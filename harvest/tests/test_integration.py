"""Integration tests for Harvest skill scripts.

These tests hit the live Harvest API and verify that every script runs, writes
valid JSON output, and returns the expected top-level structure.

They are automatically skipped when HARVEST_ACCESS_TOKEN and
HARVEST_ACCOUNT_ID are not set in the environment.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import requires_harvest

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


# ── account data ──────────────────────────────────────────────────────────────

@requires_harvest
def test_company(tmp_path):
    data = run_script("company.py", tmp_path=tmp_path)
    assert data["category"] == "company"
    assert "company" in data
    assert "name" in data["company"]


@requires_harvest
def test_list_users(tmp_path):
    data = run_script("list-users.py", "--is-active", tmp_path=tmp_path)
    assert data["category"] == "users"
    assert isinstance(data["users"], list)
    assert data["counts"]["total"] >= 0
    if data["users"]:
        u = data["users"][0]
        assert "id" in u
        assert "email" in u


@requires_harvest
def test_list_clients(tmp_path):
    data = run_script("list-clients.py", tmp_path=tmp_path)
    assert data["category"] == "clients"
    assert isinstance(data["clients"], list)
    assert "total" in data["counts"]


@requires_harvest
def test_list_projects(tmp_path):
    data = run_script("list-projects.py", tmp_path=tmp_path)
    assert data["category"] == "projects"
    assert isinstance(data["projects"], list)


@requires_harvest
def test_list_tasks(tmp_path):
    data = run_script("list-tasks.py", tmp_path=tmp_path)
    assert data["category"] == "tasks"
    assert isinstance(data["tasks"], list)


@requires_harvest
def test_list_roles(tmp_path):
    data = run_script("list-roles.py", tmp_path=tmp_path)
    assert data["category"] == "roles"
    assert isinstance(data["roles"], list)
    assert "total" in data["counts"]


@requires_harvest
def test_list_invoices(tmp_path):
    data = run_script("list-invoices.py", "--days", "90", tmp_path=tmp_path)
    assert data["category"] == "invoices"
    assert isinstance(data["invoices"], list)
    assert "total_amount" in data["counts"]


@requires_harvest
def test_list_estimates(tmp_path):
    data = run_script("list-estimates.py", "--days", "90", tmp_path=tmp_path)
    assert data["category"] == "estimates"
    assert isinstance(data["estimates"], list)


@requires_harvest
def test_list_expenses(tmp_path):
    data = run_script("list-expenses.py", "--days", "30", tmp_path=tmp_path)
    assert data["category"] == "expenses"
    assert isinstance(data["expenses"], list)
    assert "total_cost" in data["counts"]


# ── time entry reports ────────────────────────────────────────────────────────

@requires_harvest
def test_time_entries(tmp_path):
    data = run_script("time-entries.py", "--days", "7", tmp_path=tmp_path)
    assert data["category"] == "time_entries"
    assert "counts" in data
    for key in ("total_hours", "billable_hours", "non_billable_hours",
                "active_users", "active_projects", "total_entries"):
        assert key in data["counts"], f"missing key: {key}"
    assert isinstance(data["by_user"], list)
    assert isinstance(data["by_project"], list)
    assert isinstance(data["by_task"], list)
    assert isinstance(data["items"], list)
    assert data["counts"]["total_hours"] >= 0


@requires_harvest
def test_time_entries_date_range(tmp_path):
    data = run_script(
        "time-entries.py", "--since", "2026-01-01", "--until", "2026-01-07",
        tmp_path=tmp_path,
    )
    assert data["range"]["start_date"] == "2026-01-01"
    assert data["range"]["end_date"] == "2026-01-07"


@requires_harvest
def test_report_team(tmp_path):
    data = run_script("report-team.py", "--days", "7", tmp_path=tmp_path)
    assert data["category"] == "team"
    assert isinstance(data["members"], list)
    assert data["counts"]["total_hours"] >= 0
    if data["members"]:
        m = data["members"][0]
        assert "user_id" in m
        assert "total_hours" in m


@requires_harvest
def test_report_projects(tmp_path):
    data = run_script("report-projects.py", "--days", "7", tmp_path=tmp_path)
    assert data["category"] == "projects"
    assert isinstance(data["projects"], list)
    assert "active_projects" in data["counts"]


@requires_harvest
def test_report_clients(tmp_path):
    data = run_script("report-clients.py", "--days", "7", tmp_path=tmp_path)
    assert data["category"] == "clients"
    assert isinstance(data["clients"], list)
    assert "active_clients" in data["counts"]


@requires_harvest
def test_report_tasks(tmp_path):
    data = run_script("report-tasks.py", "--days", "7", tmp_path=tmp_path)
    assert data["category"] == "tasks"
    assert isinstance(data["tasks"], list)
    assert "active_tasks" in data["counts"]


# ── financial and budget reports ──────────────────────────────────────────────

@requires_harvest
def test_report_expenses_single_breakdown(tmp_path):
    data = run_script(
        "report-expenses.py", "--breakdown", "clients", "--days", "30",
        tmp_path=tmp_path,
    )
    assert data["category"] == "expenses_clients"
    assert "clients" in data
    assert isinstance(data["clients"], list)


@requires_harvest
def test_report_expenses_all_breakdowns(tmp_path):
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "report-expenses.py"),
        "--days", "30", "--output-dir", str(tmp_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    json_files = list(tmp_path.glob("*.json"))
    assert len(json_files) == 4, f"Expected 4 files, got {len(json_files)}"


@requires_harvest
def test_report_budget(tmp_path):
    data = run_script("report-budget.py", tmp_path=tmp_path)
    assert data["category"] == "project_budget"
    assert isinstance(data["projects"], list)
    assert "total_projects" in data["counts"]


@requires_harvest
def test_report_uninvoiced(tmp_path):
    data = run_script("report-uninvoiced.py", "--days", "30", tmp_path=tmp_path)
    assert data["category"] == "uninvoiced"
    assert isinstance(data["projects"], list)
    assert "total_uninvoiced_amount" in data["counts"]
