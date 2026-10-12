"""Optional LangChain callback integration.

Compatible with the current BaseCallbackHandler callback forms:
``on_llm_end(response, **kwargs)`` and ``on_chain_end(outputs, **kwargs)``.
"""

from __future__ import annotations

from typing import Any, Optional

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:  # pragma: no cover - exercised only without the extra
    class BaseCallbackHandler:  # type: ignore[no-redef]
        """Fallback that keeps the core package importable without LangChain."""


from ..core import DriftSentinel, DriftStatus


class DriftGuardCallbackHandler(BaseCallbackHandler):
    """Record completed LLM and chain callbacks as reclaimed progress."""

    def __init__(self, sentinel: DriftSentinel) -> None:
        super().__init__()
        self.sentinel = sentinel

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Record an LLM completion, using token usage when available."""
        usage = getattr(response, "llm_output", None) or {}
        tokens = usage.get("token_usage", {}).get("total_tokens", 1)
        fingerprint = kwargs.get("run_id")
        self.sentinel.record_step(
            float(tokens), 1.0, str(fingerprint) if fingerprint else None
        )

    def on_chain_end(self, outputs: Any, **kwargs: Any) -> None:
        """Record a completed chain as one unit of contraction."""
        fingerprint: Optional[str] = (
            str(kwargs["run_id"]) if kwargs.get("run_id") else None
        )
        self.sentinel.record_step(1.0, 1.0, fingerprint)

    def current_status(self) -> DriftStatus:
        """Expose the monitored sentinel status."""
        return self.sentinel.current_status()
