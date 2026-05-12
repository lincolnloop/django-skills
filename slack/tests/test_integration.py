"""Integration tests for Slack skill scripts.

These tests hit the live Slack API and verify read operations work correctly.
Write operations (send-message, post-blocks, send-report, update-message) are
not tested here to avoid posting to real channels during CI runs.

They are automatically skipped when SLACK_BOT_TOKEN is not set.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import requires_slack

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


def run_script(script: str, *args: str, tmp_path: Path) -> dict:
    """Run a script, return the first JSON file it writes."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script), "--output-dir", str(tmp_path), *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.fail(f"{script} failed:\n{result.stderr}")
    json_files = sorted(tmp_path.glob("*.json"))
    assert json_files, f"{script} produced no JSON output.\nstdout: {result.stdout}"
    return json.loads(json_files[0].read_text())


@requires_slack
def test_list_channels(tmp_path):
    data = run_script("list-channels.py", tmp_path=tmp_path)
    assert data["category"] == "channels"
    assert isinstance(data["channels"], list)
    assert "total" in data["counts"]
    if data["channels"]:
        ch = data["channels"][0]
        assert "id" in ch
        assert "name" in ch
        assert "is_private" in ch


@requires_slack
def test_list_channels_public_only(tmp_path):
    data = run_script("list-channels.py", "--types", "public_channel", tmp_path=tmp_path)
    assert data["category"] == "channels"
    for ch in data["channels"]:
        assert not ch.get("is_private")


@requires_slack
def test_list_users(tmp_path):
    data = run_script("list-users.py", tmp_path=tmp_path)
    assert data["category"] == "users"
    assert isinstance(data["users"], list)
    assert "total" in data["counts"]
    if data["users"]:
        u = data["users"][0]
        assert "id" in u
        assert "name" in u
        assert u.get("is_bot") is False


@requires_slack
def test_list_users_include_bots(tmp_path):
    data = run_script("list-users.py", "--include-bots", tmp_path=tmp_path)
    assert data["category"] == "users"
    assert isinstance(data["users"], list)
