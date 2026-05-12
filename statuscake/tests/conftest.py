"""Pytest configuration and shared fixtures for StatusCake skill tests."""
import os
import pytest

STATUSCAKE_CREDENTIALS_AVAILABLE = bool(os.environ.get("STATUSCAKE_API_KEY"))

requires_statuscake = pytest.mark.skipif(
    not STATUSCAKE_CREDENTIALS_AVAILABLE,
    reason="STATUSCAKE_API_KEY must be set for integration tests",
)
