"""Visual DriftGuard demo: stop a web scraper stuck retrying a 429 response."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

# Make the example runnable from a fresh checkout before editable installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from drift_guardian import DriftSentinel, DriftStatus

AUDIT_PATH = Path("drift_audit.jsonl")
URL = "https://example.com/pricing"


def audit_event(event: str, **details: object) -> None:
    """Append a human-readable safety event to the local JSONL audit trail."""
    record = {"event": event, "timestamp": time.time(), **details}
    with AUDIT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def print_status(status: DriftStatus, message: str) -> None:
    icons = {
        DriftStatus.OK: "✅",
        DriftStatus.WARNING: "⚠️",
        DriftStatus.CRITICAL: "🔥",
        DriftStatus.LOOP: "🛑",
    }
    print(f"{icons[status]} {message} [{status.value.upper()}]")


def main() -> None:
    print("=" * 72)
    print("DriftGuard Advanced Demo — AI Web Scraping Agent")
    print("Scenario: a 429 response creates a retry loop")
    print("=" * 72)

    sentinel = DriftSentinel(window=10)
    audit_event("demo_started", url=URL)

    print("\n1) Healthy tool calls")
    for page in ("home", "about"):
        status = sentinel.record_step(
            expansion=1, contraction=1, fingerprint=f"fetch:{page}"
        )
        print_status(status, f"Fetched unique page: {page}")
        audit_event("tool_call", url=page, status=status.value)

    print("\n2) The endpoint starts rate-limiting")
    print("⚠️  HTTP 429 Too Many Requests — retry policy activated")
    audit_event("http_error", code=429, url=URL)

    print("\n3) DriftGuard watches the repeated retries")
    for attempt in range(1, 5):
        status = sentinel.record_step(
            expansion=1, contraction=0, fingerprint=f"fetch:{URL}"
        )
        print(f"↻ Retry {attempt}/4: {URL}")
        audit_event(
            "retry_attempt", attempt=attempt, url=URL, status=status.value
        )
        if status is DriftStatus.LOOP:
            print_status(status, "LOOP DETECTED: Agent Halted")
            print("   Fallback: use cached content or queue the URL for later.")
            audit_event(
                "agent_halted",
                reason="identical fingerprint repeated with zero contraction",
                fallback="cache_or_deferred_queue",
            )
            break

    print("\nAudit trail written to drift_audit.jsonl")
    print("No additional API call was made after the safety stop.")


if __name__ == "__main__":
    main()
