# AGENTS.md — instructions for AI coding agents

## Project identity
Mathematical drift detection and loop prevention for AI agents and data pipelines.
Small, zero-dependency Python library produced for setuptools with MIT license and Python >=3.9.
Core implementation lives in src/drift_guardian.

## Verified ground truth
These facts are confirmed from the repository source and must be treated as the canonical API contract until the code changes.

### Public status enum
The repository exposes `DriftStatus` as an `Enum` with the following values:
- `DriftStatus.OK`
- `DriftStatus.WARNING`
- `DriftStatus.CRITICAL`
- `DriftStatus.LOOP`

Source: `src/drift_guardian/core.py`

### DriftSentinel
Verified constructor signature:

```python
class DriftSentinel:
    def __init__(
        self,
        window: int = 10,
        baseline: float = 0.30,
        warning_margin: float = -0.10,
        critical_margin: float = -0.20,
        loop_repetitions: int = 3,
        epsilon: float = 1e-9,
    ) -> None:
```

Verified methods:

```python
def record_step(
    self, expansion: float, contraction: float, fingerprint: Optional[str] = None
) -> DriftStatus:
```

```python
def drift_margin(self) -> float:
```

```python
def reset(self) -> None:
```

```python
def current_status(self) -> DriftStatus:
```

```python
def sample_count(self) -> int:
```

### AdaptiveDriftSentinel
Verified constructor signature:

```python
class AdaptiveDriftSentinel(DriftSentinel):
    def __init__(
        self,
        *args: object,
        enable_adaptive: bool = False,
        min_samples: int = 50,
        learning_rate: float = 0.01,
        max_change: float = 0.02,
        cooldown: int = 100,
        audit_path: str = "drift_audit.jsonl",
        **kwargs: object,
    ) -> None:
```

Verified methods:

```python
def record_step(
    self, expansion: float, contraction: float, fingerprint: Optional[str] = None
) -> DriftStatus:
```

```python
def freeze_baseline(self) -> None:
```

```python
@property
def baseline_frozen(self) -> bool:
```

### Not found in source
The following names are not present in the current source tree and must not be invented or assumed:
- `DriftWarning`
- `DriftCritical`
- `warning_threshold`
- `critical_threshold`
- `baseline_window`
- `warmup`
- `record_step(value)` with a single float argument

### Loop detection contract
The verified loop rule is:
- the most recent `loop_repetitions` samples are inspected;
- all fingerprints must be identical and not `None`;
- all contraction values in that window must be exactly zero.

This is implemented in `DriftSentinel._has_loop` and is independent from the numeric margin thresholds.

### Audit file behavior (security debt)
Current real behavior in `AdaptiveDriftSentinel.__init__` and `_write_audit`:
- `audit_path` defaults to the literal string `"drift_audit.jsonl"`.
- If adaptive mode writes an audit, it opens the file in append mode and writes JSONL records.

This is a known security and operational risk: the default behavior writes to disk without express opt-in and should be hardened in a follow-up PR.

## Hard rules
1. Never invent a constructor parameter, method name, or class that is not verified in the source.
2. Keep the core package zero-dependency. Do not import third-party runtime dependencies into the core layer.
3. The library is not to be reinterpreted as a `DriftWarning`/`DriftCritical` class system. The canonical status model is `DriftStatus`.
4. For any new public API, add type annotations and a docstring in the same PR.
5. For any file I/O in tests, use `tmp_path` and never write into the repository root.
6. The audit default is not production-safe today; do not silently assume `audit_path=None` exists unless the code was changed and verified.
7. Tests must match the real public API exactly, especially `record_step(expansion, contraction, fingerprint=None)`.
8. Do not break backward compatibility of the public API within a minor version.
9. For new code, `mypy --strict` must pass and tests must remain green.

## Definition of done for a change
- Source and tests align with the verified API.
- `pytest` passes on the affected behavior.
- `ruff` passes.
- `black --check` passes.
- `mypy --strict` passes for changed code.
- Coverage remains at or above project requirements.
- Audit-related behavior is explicitly tested before it is considered safe.

## Working style for Copilot agents
When asked to modify this repository:
- first confirm the verified API using the source;
- then write tests against that API;
- then implement the smallest fix;
- then run the relevant checks.

This repository is early-stage and should be hardened incrementally, not by inventing a wider API surface than the verified code already supports.
