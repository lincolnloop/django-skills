"""Pytest configuration for Logseq skill tests."""
import os
import pytest
import requests

LOGSEQ_API_URL = os.environ.get("LOGSEQ_API_URL", "http://localhost:12315")


def _logseq_reachable() -> bool:
    if not os.environ.get("LOGSEQ_API_TOKEN"):
        return False
    try:
        requests.get(LOGSEQ_API_URL, timeout=2)
        return True
    except Exception:
        return False


LOGSEQ_AVAILABLE = _logseq_reachable()

requires_logseq = pytest.mark.skipif(
    not LOGSEQ_AVAILABLE,
    reason="LOGSEQ_API_TOKEN must be set and Logseq must be running for integration tests",
)
