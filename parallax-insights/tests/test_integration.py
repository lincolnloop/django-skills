"""Integration tests for Parallax Insights skill scripts.

These tests hit the live Parallax API and verify that every script runs, writes
valid JSON output, and returns the expected top-level structure.

They are automatically skipped when PARALLAX_API_KEY is not set in the
environment.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import requires_parallax

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


# ── people / roster ───────────────────────────────────────────────────────────

@requires_parallax
def test_people(tmp_path):
    data = run_script("people.py", tmp_path=tmp_path)
    assert data["category"] == "people"
    assert isinstance(data["items"], list)
    assert "total" in data["counts"]
    if data["items"]:
        p = data["items"][0]
        assert "id" in p
        assert "name" in p


# ── time entries ──────────────────────────────────────────────────────────────

@requires_parallax
def test_time_entries(tmp_path):
    data = run_script("time_entries.py", "--days", "7", tmp_path=tmp_path)
    assert data["category"] == "time_entries"
    assert isinstance(data["items"], list)
    assert isinstance(data["by_person"], list)
    counts = data["counts"]
    assert "total_entries" in counts
    assert "total_hours" in counts
    assert "billable_hours" in counts
    assert "non_billable_hours" in counts


@requires_parallax
def test_time_entries_date_range(tmp_path):
    data = run_script(
        "time_entries.py", "--since", "2026-01-01", "--until", "2026-01-31",
        tmp_path=tmp_path,
    )
    assert data["range"]["start_date"] == "2026-01-01"
    assert data["range"]["end_date"] == "2026-01-31"


# ── allocations ───────────────────────────────────────────────────────────────

@requires_parallax
def test_allocations(tmp_path):
    data = run_script("allocations.py", "--days", "7", tmp_path=tmp_path)
    assert data["category"] == "allocations"
    assert isinstance(data["by_person"], list)
    counts = data["counts"]
    assert "total_hours" in counts
    assert "billable_planned_hours" in counts
    assert "internal_planned_hours" in counts


# ── people financials ─────────────────────────────────────────────────────────

@requires_parallax
def test_people_financials(tmp_path):
    data = run_script("people_financials.py", "--days", "7", tmp_path=tmp_path)
    assert data["category"] == "people_financials"
    assert isinstance(data["items"], list)
    counts = data["counts"]
    assert "total_people" in counts
    assert "total_actual_hours" in counts
    assert "total_actual_revenue" in counts
    if data["items"]:
        p = data["items"][0]
        assert "person_id" in p
        assert "totals" in p
        assert "actual_hours" in p["totals"]


# ── projects ──────────────────────────────────────────────────────────────────

@requires_parallax
def test_projects(tmp_path):
    data = run_script("projects.py", tmp_path=tmp_path)
    assert data["category"] == "projects"
    assert isinstance(data["items"], list)
    assert "total" in data["counts"]
    if data["items"]:
        p = data["items"][0]
        assert "id" in p
        assert "name" in p


@requires_parallax
def test_projects_include_archived(tmp_path):
    data = run_script("projects.py", "--include-archived", tmp_path=tmp_path)
    assert data["category"] == "projects"
    assert isinstance(data["items"], list)


# ── project financials ────────────────────────────────────────────────────────

@requires_parallax
def test_project_financials_by_offering(tmp_path):
    data = run_script(
        "project_financials.py", "--days", "7", "--mode", "offering",
        tmp_path=tmp_path,
    )
    assert data["category"] == "project_financials_by_offering"
    assert data["mode"] == "offering"
    assert isinstance(data["items"], list)
    counts = data["counts"]
    assert "total_projects" in counts
    assert "total_actual_hours" in counts


@requires_parallax
def test_project_financials_by_role(tmp_path):
    data = run_script(
        "project_financials.py", "--days", "7", "--mode", "role",
        tmp_path=tmp_path,
    )
    assert data["category"] == "project_financials_by_role"
    assert data["mode"] == "role"
    assert isinstance(data["items"], list)


# ── clients & pipelines ───────────────────────────────────────────────────────

@requires_parallax
def test_clients(tmp_path):
    data = run_script("clients.py", tmp_path=tmp_path)
    assert data["category"] == "clients"
    assert isinstance(data["items"], list)
    assert "total" in data["counts"]
    if data["items"]:
        c = data["items"][0]
        assert "name" in c
        assert "projects_count" in c


@requires_parallax
def test_pipelines(tmp_path):
    data = run_script("pipelines.py", tmp_path=tmp_path)
    assert data["category"] == "pipelines"
    assert isinstance(data["items"], list)
    assert "total" in data["counts"]
    if data["items"]:
        stage = data["items"][0]
        assert "name" in stage
        assert "projects" in stage


# ── executive summary ─────────────────────────────────────────────────────────

@requires_parallax
def test_executive_summary(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "executive_summary.py"),
         "--days", "7", "--output-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"executive_summary.py failed:\n{result.stderr}")
    json_files = sorted(tmp_path.glob("*.json"))
    md_files = sorted(tmp_path.glob("*.md"))
    assert json_files, "executive_summary.py produced no JSON output"
    assert md_files, "executive_summary.py produced no Markdown output"

    data = json.loads(json_files[0].read_text())
    assert "time_entries" in data or "summary" in data or "counts" in data


@requires_parallax
def test_executive_summary_with_allocations(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "executive_summary.py"),
         "--days", "7", "--with-allocations", "--output-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"executive_summary.py --with-allocations failed:\n{result.stderr}")
    json_files = sorted(tmp_path.glob("*.json"))
    assert json_files, "executive_summary.py --with-allocations produced no JSON output"
