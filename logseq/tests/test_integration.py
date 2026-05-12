"""Integration tests for Logseq skill scripts.

These tests hit the live Logseq HTTP API. They require:
  - LOGSEQ_API_TOKEN to be set
  - Logseq to be running with HTTP APIs enabled
    (Settings → Developer → HTTP APIs → Enable)

They are automatically skipped when Logseq is not reachable.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import requires_logseq

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"

TEST_PAGE_NAME = "__agent_skills_test_page__"


def run(script: str, *args: str) -> str:
    """Run a script and return its stdout."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script), *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.fail(f"{script} failed:\n{result.stderr}")
    return result.stdout.strip()


# ── read operations ───────────────────────────────────────────────────────────

@requires_logseq
def test_list_pages():
    output = run("list-pages.py")
    data = json.loads(output)
    assert "count" in data
    assert isinstance(data["pages"], list)
    assert data["count"] >= 0


@requires_logseq
def test_list_pages_no_journal():
    output = run("list-pages.py", "--no-journal")
    data = json.loads(output)
    for page in data["pages"]:
        assert not page.get("journal"), f"Journal page found: {page['name']}"


@requires_logseq
def test_list_pages_journal_only():
    output = run("list-pages.py", "--journal-only")
    data = json.loads(output)
    for page in data["pages"]:
        assert page.get("journal"), f"Non-journal page found: {page['name']}"


@requires_logseq
def test_get_current_page():
    output = run("get-current-page.py")
    # May be null if no page is open — both are valid
    if output != "null":
        data = json.loads(output)
        assert "page" in data
        assert "blocks" in data


@requires_logseq
def test_get_page_nonexistent_returns_null():
    output = run("get-page.py", "__definitely_does_not_exist_xyz__")
    assert output == "null"


@requires_logseq
def test_search_pages():
    output = run("search-pages.py", "the")
    data = json.loads(output)
    assert "query" in data
    assert data["query"] == "the"
    assert "count" in data
    assert isinstance(data["results"], list)


# ── write operations (create, update, delete) ─────────────────────────────────

@requires_logseq
def test_create_get_delete_page():
    # Create
    create_out = run("create-page.py", TEST_PAGE_NAME, "Integration test block")
    page_data = json.loads(create_out)
    assert page_data is not None

    # Get — should exist now
    get_out = run("get-page.py", TEST_PAGE_NAME)
    assert get_out != "null"
    data = json.loads(get_out)
    assert data["page"] is not None
    assert isinstance(data["blocks"], list)

    # Grab the first block uuid for manipulation
    blocks = data["blocks"]
    assert len(blocks) > 0
    block_uuid = blocks[0]["uuid"]

    # Update the block
    update_out = run("update-block.py", block_uuid, "Updated content")
    update_data = json.loads(update_out)
    assert update_data["updated"] is True
    assert update_data["uuid"] == block_uuid

    # Insert a child block
    insert_out = run("insert-block.py", block_uuid, "Child block")
    insert_data = json.loads(insert_out)
    assert insert_data is not None
    child_uuid = insert_data.get("uuid")
    assert child_uuid

    # Delete the child block
    delete_out = run("delete-block.py", child_uuid)
    delete_data = json.loads(delete_out)
    assert delete_data["deleted"] is True
    assert delete_data["uuid"] == child_uuid

    # Clean up — delete the test page by deleting all its blocks
    final_data = json.loads(run("get-page.py", TEST_PAGE_NAME))
    for block in final_data.get("blocks", []):
        run("delete-block.py", block["uuid"])
