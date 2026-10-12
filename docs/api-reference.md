# API reference

## `DriftStatus`

The enum values are `OK`, `WARNING`, `CRITICAL`, and `LOOP`.

## `DriftSentinel`

`record_step(expansion, contraction, fingerprint=None)` records non-negative,
finite values and returns the resulting status. `current_status()` reads the
last status, `drift_margin()` returns the exact margin, and `reset()` clears state.

## `AdaptiveDriftSentinel`

Set `enable_adaptive=True` explicitly to enable bounded baseline learning. The
baseline is clamped to `[0.15, 0.60]`, each change is capped at `0.02`, and
updates are audited to JSON Lines. Call `freeze_baseline()` to stop adaptation.
