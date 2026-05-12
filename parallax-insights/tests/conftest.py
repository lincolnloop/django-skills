"""Pytest configuration and shared fixtures for Parallax Insights skill tests."""
import os
import pytest

PARALLAX_CREDENTIALS_AVAILABLE = bool(os.environ.get("PARALLAX_API_KEY"))

requires_parallax = pytest.mark.skipif(
    not PARALLAX_CREDENTIALS_AVAILABLE,
    reason="PARALLAX_API_KEY must be set for integration tests",
)
