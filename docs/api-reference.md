# API reference

## `DriftStatus`

The enum values are `OK`, `WARNING`, `CRITICAL`, and `LOOP`.

## `DriftSentinel`

`record_step(expansion, contraction, fingerprint=None)` records non-negative,
finite values and returns the resulting status. `current_status()` reads the
last status, `drift_margin()` returns the exact margin, and `reset()` clears state.

## `AdaptiveDriftSentinel`

Set `enable_adaptive=True` explicitly to enable bounded baseline learning. The
baseline is clamped to `[0.15, 0.60]` and each change is capped at `0.02`. Call
`freeze_baseline()` to stop adaptation.

### `audit_path`

`audit_path: Optional[str] = None`. Audit logging is opt-in: when `None` (the
default) nothing is written to disk. When set, every baseline change appends one
JSON Lines record containing `timestamp`, `old_baseline`, `new_baseline`,
`observed_ratio` and `reason`.

- The parent directory must already exist; otherwise the constructor raises
  `ValueError("parent directory does not exist: ...")`. The library never
  creates directories.
- Records are appended with `O_APPEND` and flushed with `fsync`, under the
  sentinel's lock, so concurrent recording from several threads produces
  complete, untorn lines and never overwrites earlier records. This guarantee
  covers threads in one process, not multiple processes writing one file.
- The file is created with mode `0600` on POSIX; permissions are not applied on
  Windows.
