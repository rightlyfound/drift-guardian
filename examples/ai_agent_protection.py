from drift_guardian import DriftSentinel, DriftStatus

sentinel = DriftSentinel()
for index in range(10):
    status = sentinel.record_step(expansion=5, contraction=0, fingerprint="same-plan")
    if status in (DriftStatus.CRITICAL, DriftStatus.LOOP):
        print(f"Stop or re-plan at step {index + 1}: {status.value}")
        break
