"""Optional framework-neutral wrapper for CrewAI kickoff methods."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

from ..core import DriftSentinel, DriftStatus

F = TypeVar("F", bound=Callable[..., Any])


def monitor_agent(
    sentinel: DriftSentinel, fingerprint: Optional[str] = None
) -> Callable[[F], F]:
    """Decorate a CrewAI or Crew kickoff callable with bounded drift accounting.

    CrewAI's current lifecycle guidance also supports ``@before_kickoff`` and
    ``@after_kickoff`` hooks. This decorator is useful when a direct callable
    boundary is more convenient than a ``CrewBase`` class.
    """

    def decorator(function: F) -> F:
        @wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            result = function(*args, **kwargs)
            sentinel.record_step(1.0, 1.0, fingerprint)
            return result

        return cast(F, wrapped)

    return decorator


drift_guard = monitor_agent


def status_after_kickoff(sentinel: DriftSentinel) -> DriftStatus:
    """Return the status after a monitored CrewAI kickoff."""
    return sentinel.current_status()
