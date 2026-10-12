import pytest

from drift_guardian import DriftSentinel, DriftStatus


def test_exact_formula_and_thresholds() -> None:
    sentinel = DriftSentinel(window=10, baseline=0.30)
    assert sentinel.record_step(8, 2) is DriftStatus.OK
    assert sentinel.record_step(8, 0) is DriftStatus.OK
    assert sentinel.record_step(8, 0) is DriftStatus.CRITICAL
    expected = 2 / (26 + 1e-9) - 0.30
    assert sentinel.drift_margin() == pytest.approx(expected)

    warning = DriftSentinel(window=10, baseline=0.30)
    for _ in range(3):
        warning.record_step(8, 1)
    assert warning.current_status() is DriftStatus.WARNING


def test_epsilon_prevents_zero_division() -> None:
    sentinel = DriftSentinel()
    for _ in range(3):
        sentinel.record_step(0, 0)
    assert sentinel.drift_margin() == pytest.approx(0.0 - 0.30)


def test_warmup_returns_ok_until_three_samples() -> None:
    sentinel = DriftSentinel()
    assert sentinel.record_step(100, 0) is DriftStatus.OK
    assert sentinel.record_step(100, 0) is DriftStatus.OK


def test_cycle_detection_is_immediate() -> None:
    sentinel = DriftSentinel()
    assert sentinel.record_step(1, 0, "same") is DriftStatus.OK
    assert sentinel.record_step(1, 0, "same") is DriftStatus.OK
    assert sentinel.record_step(1, 0, "same") is DriftStatus.LOOP


def test_invalid_values_are_rejected() -> None:
    with pytest.raises(ValueError):
        DriftSentinel(window=2)
    sentinel = DriftSentinel()
    with pytest.raises(ValueError):
        sentinel.record_step(-1, 0)
