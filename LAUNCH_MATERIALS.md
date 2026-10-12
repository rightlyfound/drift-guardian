# DriftGuard launch materials

These drafts are ready for review and manual posting. Replace the placeholder
links with the final public URLs once the repository and package are published.

- GitHub: <https://github.com/rightlyfound/drift-guardian>
- PyPI: <https://pypi.org/project/drift-guardian/>

## Hacker News — Show HN

### Title

> Show HN: DriftGuard – A zero-dependency math library to stop runaway AI agents

### Body

AI agents can look productive while quietly burning API credits in retry loops:
the same URL, tool call, or plan state is expanded repeatedly without producing
new progress. Heavy LLM monitors are often too slow, expensive, or intrusive to
place on that critical path.

DriftGuard is a small Python library that turns this into a deterministic safety
signal. It tracks **Expansion** (new calls, tokens, queued work) against
**Contraction** (completed tasks, unique results, reclaimed memory) and computes
a rolling Drift Margin with five lines of standard-library math. Optional state
fingerprints detect the same no-progress state three times in a row and return
`LOOP` immediately.

The core has zero runtime dependencies. An opt-in adaptive mode is bounded,
rate-limited, auditable to JSONL, and can be frozen by an operator. There are
also optional LangChain and CrewAI integration helpers.

GitHub: https://github.com/rightlyfound/drift-guardian  
PyPI: https://pypi.org/project/drift-guardian/

I would especially value feedback from people operating agents at scale:
Which expansion and contraction signals do you measure, and where would a
mathematical stop signal fit in your stack?

## Twitter / X thread

### Tweet 1/3

AI agents get stuck in infinite loops and burn money on retries. You do not
always need another LLM to monitor them. DriftGuard stops runaway work with a
small, deterministic Drift Margin: five lines of pure math. 🧵

### Tweet 2/3

DriftGuard tracks **Expansion** (calls, tokens, queued work) versus
**Contraction** (completed tasks, unique results, freed memory). Add a state
fingerprint and it detects repeated no-progress loops before they crash your
app or exhaust your API budget.

### Tweet 3/3

Try it, inspect the audit trail, and tell us what you would measure:
https://github.com/rightlyfound/drift-guardian

Python package: https://pypi.org/project/drift-guardian/

Feedback from AI engineers and reliability teams is welcome.

## LinkedIn post

AI reliability is also cost optimization.

When an agent retries the same tool call, revisits the same URL, or expands a
plan without reclaiming useful work, the failure mode is measurable before it
becomes a large invoice. DriftGuard is an open-source Python library that
provides a deterministic signal for that condition.

It compares Expansion—new tokens, API calls, queued tasks, or allocated
memory—with Contraction—completed tasks, unique insights, processed records, or
freed memory. Its rolling Drift Margin requires no model call and no service.
Optional fingerprints detect repeated no-progress states, while an opt-in
adaptive baseline is bounded, cooldown-limited, audited, and freezable.

The first release includes optional LangChain and CrewAI wrappers, while the
core remains zero-dependency and easy to place in an existing agent loop.

This is my open-source contribution toward more observable, controllable AI
systems. If you operate agents in production, I would appreciate feedback on
which signals best represent progress in your workflows.

GitHub: https://github.com/rightlyfound/drift-guardian
PyPI: https://pypi.org/project/drift-guardian/
