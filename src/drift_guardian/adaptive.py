"""Opt-in bounded adaptive baseline sentinel."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from threading import RLock
from typing import Optional

from .core import DriftSentinel, DriftStatus


class AdaptiveDriftSentinel(DriftSentinel):
    """A sentinel that can cautiously learn its baseline when explicitly enabled."""

    def __init__(
        self,
        *args: object,
        enable_adaptive: bool = False,
        min_samples: int = 50,
        learning_rate: float = 0.01,
        max_change: float = 0.02,
        cooldown: int = 100,
        audit_path: Optional[str] = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        if min_samples < 1 or learning_rate <= 0 or max_change <= 0 or cooldown < 0:
            raise ValueError("adaptive parameters must be positive")
        self.enable_adaptive = enable_adaptive
        self.min_samples = min_samples
        self.learning_rate = learning_rate
        self.max_change = max_change
        self.cooldown = cooldown
        self.audit_path = Path(audit_path) if audit_path is not None else None
        self._total_samples = 0
        self._last_adaptation = -cooldown
        self._frozen = False
        self._adaptive_lock = RLock()

    def record_step(
        self, expansion: float, contraction: float, fingerprint: Optional[str] = None
    ) -> DriftStatus:
        with self._adaptive_lock:
            status = super().record_step(expansion, contraction, fingerprint)
            self._total_samples += 1
            self._adapt_if_due()
            return status

    def freeze_baseline(self) -> None:
        """Prevent all future adaptive baseline changes."""
        with self._adaptive_lock:
            self._frozen = True

    @property
    def baseline_frozen(self) -> bool:
        """Whether adaptation has been permanently frozen for this instance."""
        with self._adaptive_lock:
            return self._frozen

    def _adapt_if_due(self) -> None:
        if not self.enable_adaptive or self._frozen:
            return
        if self._total_samples < self.min_samples:
            return
        if self._total_samples - self._last_adaptation < self.cooldown:
            return
        with self._lock:
            total = sum(sample[0] + sample[1] for sample in self._samples)
            contractions = sum(sample[1] for sample in self._samples)
            observed = contractions / (total + self.epsilon)
            old = self.baseline
            target = old + self.learning_rate * (observed - old)
            bounded = min(0.60, max(0.15, target))
            delta = max(-self.max_change, min(self.max_change, bounded - old))
            new = min(0.60, max(0.15, old + delta))
            self.baseline = new
        self._last_adaptation = self._total_samples
        self._write_audit(old, new, observed, "bounded adaptive update")

    def _write_audit(
        self, old: float, new: float, observed: float, reason: str
    ) -> None:
        if self.audit_path is None:
            return

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_baseline": old,
            "new_baseline": new,
            "observed_ratio": observed,
            "reason": reason,
        }

        with self._adaptive_lock:
            path = self.audit_path
            if path is None:
                return
            path.parent.mkdir(parents=True, exist_ok=True)

            fd, tmp_name = tempfile.mkstemp(
                dir=str(path.parent),
                prefix=f".{path.name}.",
                suffix=".tmp",
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, sort_keys=True) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp_name, path)
            finally:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
