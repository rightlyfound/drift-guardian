"""Property-based invariants for DriftSentinel and AdaptiveDriftSentinel."""

from __future__ import annotations

import json
import math
import os
import tempfile
from typing import List, Optional, Tuple

from hypothesis import given, settings
from hypothesis import strategies as st

from drift_guardian import AdaptiveDriftSentinel, DriftSentinel, DriftStatus

# Valid inputs: finite and non-negative, including values near float max.
amount = st.floats(
    min_value=0.0, max_value=1e308, allow_nan=False, allow_infinity=False
)
small = st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False)
fingerprint = st.one_of(st.none(), st.sampled_from(["a", "b", "c"]))
steps = st.lists(st.tuples(amount, amount, fingerprint), min_size=1, max_size=60)
small_steps = st.lists(st.tuples(small, small, fingerprint), min_size=1, max_size=60)

Step = Tuple[float, float, Optional[str]]


def _run(sentinel: DriftSentinel, data: List[Step]) -> List[DriftStatus]:
    return [sentinel.record_step(e, c, f) for e, c, f in data]


@given(steps)
def test_margin_is_always_finite_and_bounded(data: List[Step]) -> None:
    sentinel = DriftSentinel()
    for e, c, f in data:
        sentinel.record_step(e, c, f)
        margin = sentinel.drift_margin()
        assert math.isfinite(margin)
        # contraction share is in [0, 1], so margin is in [-baseline, 1 - baseline]
        assert -sentinel.baseline - 1e-9 <= margin <= 1 - sentinel.baseline + 1e-9


@given(steps, st.integers(min_value=3, max_value=20))
def test_window_never_exceeds_configured_size(data: List[Step], window: int) -> None:
    sentinel = DriftSentinel(window=window)
    for e, c, f in data:
        sentinel.record_step(e, c, f)
        assert sentinel.sample_count() <= window


@given(small_steps)
def test_status_matches_margin_thresholds(data: List[Step]) -> None:
    sentinel = DriftSentinel()
    for e, c, f in data:
        status = sentinel.record_step(e, c, f)
        if status is DriftStatus.LOOP:
            continue
        if sentinel.sample_count() < 3:
            assert status is DriftStatus.OK
            continue
        margin = sentinel.drift_margin()
        if margin <= sentinel.critical_margin:
            assert status is DriftStatus.CRITICAL
        elif margin <= sentinel.warning_margin:
            assert status is DriftStatus.WARNING
        else:
            assert status is DriftStatus.OK


@given(small_steps, st.sampled_from(["a", "b"]), st.integers(min_value=3, max_value=6))
def test_repeated_fingerprint_with_zero_contraction_is_always_loop(
    prefix: List[Step], fp: str, reps: int
) -> None:
    sentinel = DriftSentinel(loop_repetitions=3)
    _run(sentinel, prefix)
    status = None
    for _ in range(reps):
        status = sentinel.record_step(1.0, 0.0, fp)
    assert status is DriftStatus.LOOP


@given(small_steps)
def test_no_loop_without_fingerprints(data: List[Step]) -> None:
    sentinel = DriftSentinel()
    for e, c, _ in data:
        assert sentinel.record_step(e, c, None) is not DriftStatus.LOOP


@given(small_steps)
def test_reset_restores_initial_state(data: List[Step]) -> None:
    sentinel = DriftSentinel()
    _run(sentinel, data)
    sentinel.reset()
    assert sentinel.sample_count() == 0
    assert sentinel.current_status() is DriftStatus.OK


@given(small_steps)
def test_identical_input_gives_identical_statuses(data: List[Step]) -> None:
    assert _run(DriftSentinel(), data) == _run(DriftSentinel(), data)


@given(
    small_steps,
    st.floats(min_value=0.001, max_value=0.2),
    st.floats(min_value=0.001, max_value=0.2),
)
def test_adaptive_baseline_stays_bounded_and_changes_are_capped(
    data: List[Step], learning_rate: float, max_change: float
) -> None:
    sentinel = AdaptiveDriftSentinel(
        enable_adaptive=True,
        min_samples=1,
        cooldown=0,
        learning_rate=learning_rate,
        max_change=max_change,
    )
    previous = sentinel.baseline
    for e, c, f in data:
        sentinel.record_step(e, c, f)
        assert 0.15 <= sentinel.baseline <= 0.60
        assert abs(sentinel.baseline - previous) <= max_change + 1e-12
        previous = sentinel.baseline


@given(steps)
def test_adaptive_baseline_stays_finite_on_extreme_inputs(data: List[Step]) -> None:
    sentinel = AdaptiveDriftSentinel(enable_adaptive=True, min_samples=1, cooldown=0)
    for e, c, f in data:
        sentinel.record_step(e, c, f)
        assert math.isfinite(sentinel.baseline)


@given(small_steps)
def test_frozen_baseline_never_changes(data: List[Step]) -> None:
    sentinel = AdaptiveDriftSentinel(enable_adaptive=True, min_samples=1, cooldown=0)
    sentinel.freeze_baseline()
    start = sentinel.baseline
    _run(sentinel, data)
    assert sentinel.baseline == start
    assert sentinel.baseline_frozen


@given(small_steps)
def test_disabled_adaptive_never_changes_baseline(data: List[Step]) -> None:
    sentinel = AdaptiveDriftSentinel(min_samples=1, cooldown=0)
    start = sentinel.baseline
    _run(sentinel, data)
    assert sentinel.baseline == start


@settings(max_examples=40, deadline=None)
@given(steps)
def test_audit_has_one_valid_strict_json_line_per_adaptation(
    data: List[Step],
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        audit = os.path.join(tmp, "audit.jsonl")
        sentinel = AdaptiveDriftSentinel(
            enable_adaptive=True, min_samples=1, cooldown=0, audit_path=audit
        )
        _run(sentinel, data)
        with open(audit, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        assert len(lines) == len(data)
        for line in lines:
            # Reject NaN/Infinity tokens, which are not valid JSON.
            record = json.loads(line, parse_constant=_reject_constant)
            assert 0.15 <= record["new_baseline"] <= 0.60
            assert math.isfinite(record["observed_ratio"])


def _reject_constant(token: str) -> float:
    raise ValueError(f"non-standard JSON constant in audit record: {token}")
