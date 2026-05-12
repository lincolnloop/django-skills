"""Pytest configuration and shared fixtures for Harvest skill tests."""
import os
import pytest

HARVEST_CREDENTIALS_AVAILABLE = bool(
    os.environ.get("HARVEST_ACCESS_TOKEN") and os.environ.get("HARVEST_ACCOUNT_ID")
)

requires_harvest = pytest.mark.skipif(
    not HARVEST_CREDENTIALS_AVAILABLE,
    reason="HARVEST_ACCESS_TOKEN and HARVEST_ACCOUNT_ID must be set for integration tests",
)
