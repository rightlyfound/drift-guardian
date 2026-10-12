# Changelog

All notable changes to DriftGuard are documented here.

## [0.1.0] - 2026-10-13

DriftGuard 0.1.0 is the first public release: a small, deterministic safety
primitive for AI agents and data pipelines.

### Highlights

- **Zero-dependency core.** The core package uses only the Python standard
  library, so it can sit on a critical execution path without adding an LLM
  monitor, network service, or heavyweight runtime.
- **Exact Drift Margin math.** Every rolling window computes
  `sum(C_i) / (sum(E_i + C_i) + epsilon) - R_baseline`, with a default baseline
  reclamation ratio of `0.30` and `epsilon = 1e-9`.
- **Deterministic loop detection.** Optional state fingerprints identify the
  same no-progress state repeated three times with zero contraction and return
  `DriftStatus.LOOP` immediately.
- **Safe thresholds and warm-up.** The sentinel returns `OK` until three
  samples are available, then classifies observations as `OK`, `WARNING`, or
  `CRITICAL` using explicit margins.
- **Opt-in adaptive tuning.** `AdaptiveDriftSentinel` is disabled by default.
  When enabled, it requires a minimum sample count, clamps the learned baseline
  to `[0.15, 0.60]`, caps each change at `0.02`, enforces a cooldown, and
  writes timestamped JSONL audit records.
- **Auditable freeze control.** Operators can call `freeze_baseline()` to stop
  further adaptive changes for an instance.
- **Native integration wrappers.** The release includes an optional
  `DriftGuardCallbackHandler` for LangChain callbacks and a framework-neutral
  decorator for CrewAI kickoff or tool boundaries.

### Compatibility

- Python 3.9 through 3.12.
- MIT licensed.
- Core installation has no runtime dependencies; integrations are optional.
