"""Opt-in bounded adaptive baseline sentinel."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
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
        self.audit_path: Optional[Path] = None
        if audit_path is not None:
            path = Path(audit_path)
            if not path.parent.exists():
                raise ValueError(f"parent directory does not exist: {path.parent}")
            self.audit_path = path
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
            observed = self._contraction_ratio()
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
        line = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
        with self._adaptive_lock:
            # O_APPEND makes each single write land at end-of-file; owner-only
            # permissions apply on creation (best effort on non-POSIX systems).
            fd = os.open(
                self.audit_path,
                os.O_WRONLY | os.O_APPEND | os.O_CREAT,
                0o600,
            )
            try:
                os.write(fd, line)
                os.fsync(fd)
            finally:
                os.close(fd)
