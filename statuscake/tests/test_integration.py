"""Integration tests for StatusCake skill scripts.

These tests hit the live StatusCake API and verify that every script runs,
writes valid JSON output, and returns the expected top-level structure.

They are automatically skipped when STATUSCAKE_API_KEY is not set.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import requires_statuscake

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


# ── uptime ────────────────────────────────────────────────────────────────────

@requires_statuscake
def test_list_uptime(tmp_path):
    data = run_script("list-uptime.py", tmp_path=tmp_path)
    assert data["category"] == "uptime_checks"
    counts = data["counts"]
    assert "total" in counts
    assert "up" in counts
    assert "down" in counts
    assert "paused" in counts
    assert isinstance(data["checks_down"], list)
    assert isinstance(data["checks_up"], list)
    assert isinstance(data["checks_paused"], list)


@requires_statuscake
def test_list_uptime_filter_by_status(tmp_path):
    data = run_script("list-uptime.py", "--status", "up", tmp_path=tmp_path)
    assert data["category"] == "uptime_checks"
    assert data["filters"]["status"] == "up"
    assert data["counts"]["down"] == 0


# ── SSL ───────────────────────────────────────────────────────────────────────

@requires_statuscake
def test_list_ssl(tmp_path):
    data = run_script("list-ssl.py", tmp_path=tmp_path)
    assert data["category"] == "ssl_checks"
    assert isinstance(data["items"], list)
    assert "total" in data["counts"]


# ── pagespeed ─────────────────────────────────────────────────────────────────

@requires_statuscake
def test_list_pagespeed(tmp_path):
    data = run_script("list-pagespeed.py", tmp_path=tmp_path)
    assert data["category"] == "pagespeed_checks"
    assert isinstance(data["items"], list)
    assert "total" in data["counts"]


# ── heartbeat ─────────────────────────────────────────────────────────────────

@requires_statuscake
def test_list_heartbeat(tmp_path):
    data = run_script("list-heartbeat.py", tmp_path=tmp_path)
    assert data["category"] == "heartbeat_checks"
    assert isinstance(data["items"], list)
    counts = data["counts"]
    assert "total" in counts
    assert "up" in counts
    assert "down" in counts


# ── contact groups ────────────────────────────────────────────────────────────

@requires_statuscake
def test_list_contact_groups(tmp_path):
    data = run_script("list-contact-groups.py", tmp_path=tmp_path)
    assert data["category"] == "contact_groups"
    assert isinstance(data["items"], list)
    assert "total" in data["counts"]
    if data["items"]:
        g = data["items"][0]
        assert "id" in g
        assert "name" in g


# ── maintenance windows ───────────────────────────────────────────────────────

@requires_statuscake
def test_list_maintenance_windows(tmp_path):
    data = run_script("list-maintenance-windows.py", tmp_path=tmp_path)
    assert data["category"] == "maintenance_windows"
    assert isinstance(data["items"], list)
    assert "total" in data["counts"]


@requires_statuscake
def test_list_maintenance_windows_pending(tmp_path):
    data = run_script("list-maintenance-windows.py", "--state", "pending", tmp_path=tmp_path)
    assert data["category"] == "maintenance_windows"
    assert data["filters"]["state"] == "pending"


# ── locations ─────────────────────────────────────────────────────────────────

@requires_statuscake
def test_list_locations(tmp_path):
    data = run_script("list-locations.py", tmp_path=tmp_path)
    assert data["category"] == "locations"
    assert isinstance(data["uptime_locations"], list)
    assert isinstance(data["pagespeed_locations"], list)
    assert "uptime_locations" in data["counts"]
    assert "pagespeed_locations" in data["counts"]
    if data["uptime_locations"]:
        loc = data["uptime_locations"][0]
        assert "region" in loc


# ── uptime report ─────────────────────────────────────────────────────────────

@requires_statuscake
def test_uptime_report(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "uptime-report.py"),
         "--output-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"uptime-report.py failed:\n{result.stderr}")
    json_files = sorted(tmp_path.glob("*.json"))
    md_files = sorted(tmp_path.glob("*.md"))
    assert json_files, "uptime-report.py produced no JSON output"
    assert md_files, "uptime-report.py produced no Markdown output"

    data = json.loads(json_files[0].read_text())
    assert "summary" in data
    assert "checks_down" in data
    assert "schema_version" in data
