import json

from drift_guardian import AdaptiveDriftSentinel


def test_adaptation_waits_for_minimum_samples(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    sentinel = AdaptiveDriftSentinel(
        enable_adaptive=True, min_samples=50, cooldown=100, audit_path=str(path)
    )
    original = sentinel.baseline
    for _ in range(49):
        sentinel.record_step(10, 0)
    assert sentinel.baseline == original
    assert not path.exists()
    sentinel.record_step(10, 0)
    assert sentinel.baseline != original
    assert path.exists()


def test_adaptation_is_clamped_and_audited(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    sentinel = AdaptiveDriftSentinel(
        baseline=0.60,
        enable_adaptive=True,
        min_samples=1,
        cooldown=0,
        audit_path=str(path),
    )
    sentinel.record_step(0, 10)
    assert 0.15 <= sentinel.baseline <= 0.60
    record = json.loads(path.read_text().splitlines()[0])
    assert set(record) == {
        "timestamp",
        "old_baseline",
        "new_baseline",
        "observed_ratio",
        "reason",
    }


def test_freeze_prevents_future_adaptation(tmp_path) -> None:
    sentinel = AdaptiveDriftSentinel(
        enable_adaptive=True,
        min_samples=1,
        cooldown=0,
        audit_path=str(tmp_path / "audit.jsonl"),
    )
    sentinel.freeze_baseline()
    original = sentinel.baseline
    sentinel.record_step(0, 10)
    assert sentinel.baseline == original
    assert sentinel.baseline_frozen
