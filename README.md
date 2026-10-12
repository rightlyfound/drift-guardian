# DriftGuard

[![PyPI](https://img.shields.io/pypi/v/drift-guardian.svg)](https://pypi.org/project/drift-guardian/)
[![Tests](https://github.com/rightlyfound/drift-guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/rightlyfound/drift-guardian/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python versions](https://img.shields.io/pypi/pyversions/drift-guardian.svg)](https://pypi.org/project/drift-guardian/)

DriftGuard is a zero-dependency, mathematically rigorous drift-detection and loop-prevention library for AI agents and data pipelines.

It is engineered for production infrastructure. Rather than relying on heavyweight model judges or monitoring stacks, it uses boring, deterministic math and safe defaults so it is fast, auditable, and safe by default.

## Why DriftGuard?

- Zero-dependency core: pure Python math with a tiny runtime footprint.
- O(1) memory guarantee: all fingerprints are hashed to 32-byte SHA-256 digests before storage, preventing rolling-window memory blowups.
- Time-travel immunity: logical step counters and monotonic timestamps make order stable even when the system clock jumps.
- Forensic-grade audits: opt-in append-only JSONL logs with fsync-backed writes and secure POSIX permissions. Nothing is written unless you explicitly enable it.
- Fail-fast safety: if you supply an audit path, its parent directory must exist; we refuse to silently create directories for you.

## Drift Margin

For each rolling window of size `W`, DriftGuard calculates:

```
Drift Margin = sum(C_i) / (sum(E_i + C_i) + epsilon) - baseline
```

where `E` is expansion, `C` is contraction, `baseline` defaults to `0.30`, and `epsilon = 1e-9`. Warning and critical margins default to `-0.10` and `-0.20`.

## Quick start

```bash
pip install drift-guardian
```

```python
from drift_guardian import DriftSentinel, DriftStatus

sentinel = DriftSentinel(window=25, baseline=0.30)

for step in agent_execution_loop():
    status = sentinel.record_step(
        expansion=step.tokens_out,
        contraction=step.tokens_resolved,
        fingerprint=step.current_state_json,
    )

    if status is DriftStatus.LOOP:
        agent.halt_and_replan()
    elif status is DriftStatus.CRITICAL:
        alert_oncall("Critical reclamation drift detected")
```

## Adaptive mode

`AdaptiveDriftSentinel` is opt-in and disabled by default. When enabled, it:

- requires a minimum sample count,
- clamps the adaptive baseline to a safe range,
- enforces a cooldown,
- appends audit records as JSONL,
- and freezes per-instance when `freeze_baseline()` is called.

Example:

```python
from drift_guardian import AdaptiveDriftSentinel

sentinel = AdaptiveDriftSentinel(
    enable_adaptive=True,
    min_samples=10,
    cooldown=50,
    audit_path="/var/log/agents/drift_audit.jsonl",
)
```

Every time the baseline adapts, a JSONL record is appended with:

- `monotonic_ns`: monotonic timestamp (CLOCK_TAI when available, fallback to monotonic_ns)
- `logical_step`: strictly monotonic causal step counter
- `old_baseline`, `new_baseline`, `observed_ratio`, `reason`

## Security and safe defaults

- `audit_path` defaults to `None`.
- If `audit_path` is provided, the parent directory must already exist.
- Audit writes use append-only semantics and flush to disk with `fsync`.
- On POSIX, the log file is best-effort set to `0o600` permissions.
- Nothing is written unless you explicitly enable it.

## Testing and verification

The codebase is developed with a strict TDD workflow. Focused tests cover:

- no writes by default when `audit_path` is `None`
- append-only JSONL writes to an explicit path
- parent directory validation raising a clear `ValueError`
- 32-byte hashing of fingerprints to bound memory use
- logical-step ordering for causal audit trails

Example:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]" pytest
pytest tests/test_audit_safety.py -v
```

## Operational guidance

- Keep the audit path on a dedicated filesystem or mount with retention and backup policies.
- Export JSONL to an object store (S3 / GCS) or OTLP collector for centralized analysis and retention.
- Use CI and PR review to validate exact red-to-green evidence before merging hardening or security changes.

## License

MIT. See [LICENSE](LICENSE).

