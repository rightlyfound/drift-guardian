# Integrations

DriftGuard's core library has no runtime dependencies. Install only the
integration extra you need:

```bash
pip install "drift-guardian[langchain]"
pip install "drift-guardian[crewai]"
```

## LangChain: attach a callback handler

`DriftGuardCallbackHandler` implements the current LangChain callback boundary
for `on_llm_end(response, **kwargs)` and `on_chain_end(outputs, **kwargs)`.
Attach it to an `AgentExecutor` through the `callbacks` configuration:

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from drift_guardian import DriftSentinel, DriftStatus
from drift_guardian.integrations.langchain_cb import DriftGuardCallbackHandler

sentinel = DriftSentinel()
monitor = DriftGuardCallbackHandler(sentinel)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a careful research agent."),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])
llm = ChatOpenAI(model="gpt-4o-mini")
agent = create_tool_calling_agent(llm, tools=[], prompt=prompt)
executor = AgentExecutor(agent=agent, tools=[], callbacks=[monitor])
result = executor.invoke({"input": "Summarize the latest report."})

if sentinel.current_status() in (DriftStatus.CRITICAL, DriftStatus.LOOP):
    raise RuntimeError("Agent exceeded the configured drift budget")
```

For production systems, pass the handler through your existing callback
configuration rather than creating a second executor. The callback records
completed LLM and chain operations; your application should still use the
returned status to decide whether to stop, retry with a different strategy, or
route to a human.

## CrewAI: guard a tool or agent boundary

The local wrapper is framework-neutral, so it can decorate a custom tool
function, an agent-facing method, or a crew kickoff boundary. The canonical
name is `monitor_agent`:

```python
from drift_guardian import DriftSentinel, DriftStatus
from drift_guardian.integrations.crewai_wrapper import monitor_agent

sentinel = DriftSentinel()

@monitor_agent(sentinel, fingerprint="scrape:example.org")
def scrape_site(url: str) -> str:
    return fetch_and_parse(url)

content = scrape_site("https://example.org")
if sentinel.current_status() is DriftStatus.LOOP:
    use_cached_content()
```

If your application prefers the `@drift_guard` spelling, it is available as an
alias for the same decorator:

```python
from drift_guardian.integrations.crewai_wrapper import drift_guard

@drift_guard(sentinel, fingerprint="tool:search")
def search_tool(query: str) -> list[str]:
    return search(query)
```

CrewAI class-based crews can also place monitoring around their lifecycle with
`@before_kickoff` and `@after_kickoff`. Use the pre-hook to initialize or
normalize a fingerprint and the post-hook to record a successful completion.
The decorator is useful when a direct callable boundary is simpler.

## Operational guidance

Keep expansion and contraction units consistent within one sentinel. A window
that counts API calls for expansion should use comparable progress units for
contraction. Treat `LOOP` and `CRITICAL` as safety signals: stop or re-plan
rather than blindly increasing retry counts.
