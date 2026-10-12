from drift_guardian import DriftSentinel, DriftStatus

sentinel = DriftSentinel()
status = sentinel.record_step(expansion=12, contraction=4, fingerprint="step-1")
print(status)
assert status in (DriftStatus.OK, DriftStatus.WARNING, DriftStatus.CRITICAL)
