"""Pytest configuration and shared fixtures for Slack skill tests."""
import os
import pytest

SLACK_CREDENTIALS_AVAILABLE = bool(os.environ.get("SLACK_BOT_TOKEN"))

requires_slack = pytest.mark.skipif(
    not SLACK_CREDENTIALS_AVAILABLE,
    reason="SLACK_BOT_TOKEN must be set for integration tests",
)
