"""Core rolling-window drift detection primitives."""

from __future__ import annotations

import math
from collections import deque
from enum import Enum
from threading import RLock
from typing import Deque, Optional, Tuple


class DriftStatus(str, Enum):
    """The current safety status of a sentinel."""

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    LOOP = "loop"


Sample = Tuple[float, float, Optional[str]]


class DriftSentinel:
    """Detect reclamation drift and repeated no-progress cycles.

    The drift margin is calculated as::

        sum(C_i) / (sum(E_i + C_i) + epsilon) - baseline

    where the sums cover the current rolling window.
    """

    def __init__(
        self,
        window: int = 10,
        baseline: float = 0.30,
        warning_margin: float = -0.10,
        critical_margin: float = -0.20,
        loop_repetitions: int = 3,
        epsilon: float = 1e-9,
    ) -> None:
        if window < 3:
            raise ValueError("window must be at least 3")
        if not 0.0 <= baseline <= 1.0:
            raise ValueError("baseline must be between 0 and 1")
        if loop_repetitions < 2:
            raise ValueError("loop_repetitions must be at least 2")
        self.window = window
        self.baseline = baseline
        self.warning_margin = warning_margin
        self.critical_margin = critical_margin
        self.loop_repetitions = loop_repetitions
        self.epsilon = epsilon
        self._samples: Deque[Sample] = deque(maxlen=window)
        self._status = DriftStatus.OK
        self._lock = RLock()

    def record_step(
        self, expansion: float, contraction: float, fingerprint: Optional[str] = None
    ) -> DriftStatus:
        """Record one step and return the resulting status."""
        if not math.isfinite(expansion) or not math.isfinite(contraction):
            raise ValueError("expansion and contraction must be finite")
        if expansion < 0 or contraction < 0:
            raise ValueError("expansion and contraction must be non-negative")
        with self._lock:
            self._samples.append((expansion, contraction, fingerprint))
            if self._has_loop():
                self._status = DriftStatus.LOOP
                return self._status
            if len(self._samples) < 3:
                self._status = DriftStatus.OK
                return self._status
            margin = self.drift_margin()
            if margin <= self.critical_margin:
                self._status = DriftStatus.CRITICAL
            elif margin <= self.warning_margin:
                self._status = DriftStatus.WARNING
            else:
                self._status = DriftStatus.OK
            return self._status

    def drift_margin(self) -> float:
        """Return the exact rolling-window Drift Margin."""
        with self._lock:
            return self._contraction_ratio() - self.baseline

    def _contraction_ratio(self) -> float:
        """Return ``sum(C) / (sum(E + C) + epsilon)`` for the current window."""
        with self._lock:
            contraction = sum(sample[1] for sample in self._samples)
            total = sum(sample[0] + sample[1] for sample in self._samples)
            epsilon = self.epsilon
            if not (math.isfinite(contraction) and math.isfinite(total)):
                # Valid finite samples can overflow when summed. Rescale so the
                # ratio stays finite instead of collapsing to inf/inf = NaN.
                scale = max(max(sample[0], sample[1]) for sample in self._samples)
                contraction = sum(sample[1] / scale for sample in self._samples)
                total = sum(
                    sample[0] / scale + sample[1] / scale for sample in self._samples
                )
                epsilon = epsilon / scale
            return contraction / (total + epsilon)

    def reset(self) -> None:
        """Clear all samples and return to ``OK``."""
        with self._lock:
            self._samples.clear()
            self._status = DriftStatus.OK

    def current_status(self) -> DriftStatus:
        """Return the last status without changing state."""
        with self._lock:
            return self._status

    def sample_count(self) -> int:
        """Return the number of samples currently in the rolling window."""
        with self._lock:
            return len(self._samples)

    def _has_loop(self) -> bool:
        if len(self._samples) < self.loop_repetitions:
            return False
        recent = list(self._samples)[-self.loop_repetitions :]
        fingerprints = [sample[2] for sample in recent]
        return (
            fingerprints[0] is not None
            and len(set(fingerprints)) == 1
            and all(sample[1] == 0 for sample in recent)
        )
