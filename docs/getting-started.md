# Getting started

DriftGuard measures whether a process is reclaiming work as quickly as it is
creating work. It is useful at the boundary of an AI agent, task runner,
retrieval pipeline, or any loop where resource creation can outpace progress.

## 1. Install

The core library is zero-dependency:

```bash
pip install drift-guardian
```

For optional framework integrations, install only what you use:

```bash
pip install "drift-guardian[langchain]"
pip install "drift-guardian[crewai]"
```

## 2. Understand expansion and contraction

- **Expansion (`E`)** is new work or resource consumption: generated tokens,
  API calls, queued tasks, memory allocated, or URLs fetched.
- **Contraction (`C`)** is reclaimed work or useful progress: completed tasks,
  unique insights, memory freed, or successfully processed records.

For the current rolling window, DriftGuard calculates:

$$
\\text{Drift Margin} = \\frac{\\sum C_i}{\\sum(E_i + C_i) + \\varepsilon} - R_{baseline}
$$

The default window is ten samples, `R_baseline` is `0.30`, and `epsilon` is
`1e-9`. A negative margin means the process is reclaiming less than its expected
baseline.

## 3. Record steps and evaluate status

This example is intentionally short enough to place around an agent loop:

```python
from drift_guardian import DriftSentinel, DriftStatus

sentinel = DriftSentinel()
status = sentinel.record_step(20, 8, fingerprint="research:page-1")
if status is DriftStatus.LOOP:
    stop_agent()
elif status is DriftStatus.CRITICAL:
    switch_to_fallback()
elif status is DriftStatus.WARNING:
    log_warning()
```

The first two samples are warm-up. DriftGuard returns `OK` until a third sample
is available, then applies the warning and critical thresholds.

## 4. Detect repeated states

Pass a stable fingerprint for the meaningful state of each step. If the same
fingerprint appears for three consecutive steps while contraction remains zero,
`record_step()` returns `DriftStatus.LOOP` immediately. A fingerprint can be a
hash of a URL, task parameters, tool input, or normalized plan state. Do not put
secrets into fingerprints.

## 5. Reset and inspect

```python
status = sentinel.current_status()
margin = sentinel.drift_margin()
sentinel.reset()
```

`reset()` clears the rolling window and returns the status to `OK`. For adaptive
operation, see [API reference](api-reference.md) and use
`freeze_baseline()` when a learned baseline must no longer change.
