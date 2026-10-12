# DriftGuard

[![PyPI](https://img.shields.io/pypi/v/drift-guardian.svg)](https://pypi.org/project/drift-guardian/)
[![Tests](https://github.com/rightlyfound/drift-guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/rightlyfound/drift-guardian/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python versions](https://img.shields.io/pypi/pyversions/drift-guardian.svg)](https://pypi.org/project/drift-guardian/)

DriftGuard is a zero-dependency mathematical drift detector for AI agents and
data pipelines. It helps detect agent loops, pipeline bloat, and declining
reclamation before they consume unbounded resources.

## Drift Margin

For each rolling window of size `W`, DriftGuard calculates:

$$
\text{Drift Margin} = \frac{\sum C_i}{\sum(E_i + C_i) + \varepsilon} - R_{baseline}
$$

where `E` is expansion, `C` is contraction, `R_baseline` defaults to `0.30`,
and `ε = 10^-9`. Warning and critical margins default to `-0.10` and `-0.20`.

## Quick start

```bash
pip install drift-guardian
```

```python
from drift_guardian import DriftSentinel, DriftStatus

sentinel = DriftSentinel()
status = sentinel.record_step(expansion=10, contraction=3, fingerprint="plan-1")

if status is DriftStatus.LOOP or status is DriftStatus.CRITICAL:
    raise RuntimeError(f"Agent safety stop: {status.value}")
```

**Core library is zero-dependency. Integrations require optional dependencies
(e.g., `pip install drift-guardian[langchain]`).**

## Adaptive mode

`AdaptiveDriftSentinel` is opt-in and disabled by default. When enabled, it
requires a minimum sample count, clamps baseline changes, and enforces cooldown.
Use `freeze_baseline()` for a permanent per-instance freeze.

Audit logging is also opt-in. By default the library writes nothing to disk. To
record each baseline change, pass an explicit `audit_path`; the parent directory
must already exist, otherwise construction raises `ValueError`:

```python
from drift_guardian import AdaptiveDriftSentinel

sentinel = AdaptiveDriftSentinel(
    enable_adaptive=True,
    audit_path="/var/log/agent/drift_audit.jsonl",
)
```

Each adaptation appends one JSON line to that file (`O_APPEND` plus `fsync`),
so existing records are never overwritten. On POSIX systems the file is created
with owner-only (`0600`) permissions.

## License

MIT. See [LICENSE](LICENSE).
