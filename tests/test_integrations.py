import pytest


def test_langchain_integration_imports_without_required_extra() -> None:
    module = pytest.importorskip("drift_guardian.integrations.langchain_cb")
    assert hasattr(module, "DriftGuardCallbackHandler")


def test_crewai_wrapper_is_framework_neutral() -> None:
    from drift_guardian import DriftSentinel
    from drift_guardian.integrations.crewai_wrapper import monitor_agent

    sentinel = DriftSentinel()

    @monitor_agent(sentinel, fingerprint="crew")
    def kickoff() -> str:
        return "done"

    assert kickoff() == "done"
    assert sentinel.sample_count() == 1
