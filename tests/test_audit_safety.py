import json
import math
import os
import threading

import pytest

from drift_guardian import AdaptiveDriftSentinel, DriftSentinel, DriftStatus


# Promise 1: zero disk writes by default (RED on current code)
def test_default_adaptive_run_writes_nothing(tmp_path, monkeypatch):
    """Construct AdaptiveDriftSentinel without an explicit audit path and assert
    that no file is created when adaptivity is enabled.
    """
    monkeypatch.chdir(tmp_path)
    before = set(os.listdir(tmp_path))

    sentinel = AdaptiveDriftSentinel(enable_adaptive=True, min_samples=1, cooldown=0)
    for i in range(5):
        sentinel.record_step(1.0, 0.0, fingerprint=f"step-{i}")
    _ = sentinel.current_status()

    after = set(os.listdir(tmp_path))
    assert (
        before == after
    ), f"Library wrote to disk without explicit audit_path: {after - before}"


# Promise 2: atomic, complete, valid JSONL when enabled
def test_audit_lines_are_complete_and_valid_json(tmp_path):
    audit = tmp_path / "audit.jsonl"
    sentinel = AdaptiveDriftSentinel(
        enable_adaptive=True,
        min_samples=1,
        cooldown=0,
        audit_path=str(audit),
    )
    for i in range(500):
        sentinel.record_step(float(i), 0.0, fingerprint=f"f-{i}")
        sentinel.current_status()

    lines = audit.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 500, "Audit lost records"
    for line in lines:
        json.loads(line)


# Promise 3: concurrency safety — no torn lines
def test_audit_survives_concurrent_writers(tmp_path):
    audit = tmp_path / "audit_concurrent.jsonl"
    sentinel = AdaptiveDriftSentinel(
        enable_adaptive=True,
        min_samples=1,
        cooldown=0,
        audit_path=str(audit),
    )

    def worker(offset):
        for i in range(250):
            sentinel.record_step(float(offset + i), 0.0, fingerprint=f"w{offset}-{i}")

    t1 = threading.Thread(target=worker, args=(0,))
    t2 = threading.Thread(target=worker, args=(1000,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    lines = audit.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 500, "Both threads' records did not survive"
    for line in lines:
        json.loads(line)


# Invariant: loop is always detected when repeated fingerprint and zero contraction
# are present in the rolling window.
def test_loop_always_detected_after_repeated_identical_fingerprint():
    sentinel = DriftSentinel(
        window=10,
        baseline=0.30,
        warning_margin=-0.10,
        critical_margin=-0.20,
        loop_repetitions=3,
        epsilon=1e-9,
    )

    for i in range(15):
        sentinel.record_step(float(i), float(i % 3), fingerprint=f"base-{i}")

    for _ in range(20):
        status = sentinel.record_step(1.0, 0.0, fingerprint="FROZEN")
        if status == DriftStatus.LOOP:
            return
    pytest.fail(
        "Repeated identical fingerprint + zero contraction was not flagged as LOOP"
    )


# Invariant: no NaN/Inf escapes even on adversarial inputs.
def test_no_nan_or_inf_on_adversarial_inputs():
    sentinel = DriftSentinel()
    # Invalid inputs are rejected outright and must not corrupt state.
    for exp, con in [
        (-1e308, 0.0),
        (0.0, -1e308),
        (float("nan"), 0.0),
        (0.0, float("inf")),
    ]:
        with pytest.raises(ValueError):
            sentinel.record_step(exp, con)
    assert sentinel.sample_count() == 0

    # Extreme but valid finite inputs must never yield NaN/Inf margins.
    for exp, con in [(1e308, 0.0), (0.0, 1e308), (1e308, 1e308), (0.0, 0.0)]:
        sentinel.record_step(exp, con)

    assert sentinel.current_status() is not None
    assert math.isfinite(sentinel.drift_margin())


# Promise 4: a missing parent directory fails fast at construction.
def test_missing_parent_dir_fails(tmp_path):
    bad = tmp_path / "nope" / "audit.jsonl"
    with pytest.raises(ValueError, match="parent directory does not exist"):
        AdaptiveDriftSentinel(enable_adaptive=True, audit_path=str(bad))
    assert not (tmp_path / "nope").exists()


# Promise 5: audit file is owner-only on POSIX.
@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_audit_file_is_owner_only(tmp_path):
    audit = tmp_path / "audit.jsonl"
    sentinel = AdaptiveDriftSentinel(
        enable_adaptive=True, min_samples=1, cooldown=0, audit_path=str(audit)
    )
    sentinel.record_step(1.0, 0.0)
    assert (audit.stat().st_mode & 0o777) == 0o600
