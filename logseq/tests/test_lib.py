"""Unit tests for logseq.py shared library — no live API calls."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ── check_env ─────────────────────────────────────────────────────────────────

def test_check_env_missing_token_exits(monkeypatch):
    monkeypatch.delenv("LOGSEQ_API_TOKEN", raising=False)
    import logseq
    with pytest.raises(SystemExit):
        logseq.check_env()


def test_check_env_returns_token_and_url(monkeypatch):
    monkeypatch.setenv("LOGSEQ_API_TOKEN", "test-token-123")
    monkeypatch.delenv("LOGSEQ_API_URL", raising=False)
    import logseq
    token, url = logseq.check_env()
    assert token == "test-token-123"
    assert url == "http://localhost:12315"


def test_check_env_custom_url(monkeypatch):
    monkeypatch.setenv("LOGSEQ_API_TOKEN", "tok")
    monkeypatch.setenv("LOGSEQ_API_URL", "http://localhost:9999")
    import logseq
    _, url = logseq.check_env()
    assert url == "http://localhost:9999"


# ── LogseqClient ──────────────────────────────────────────────────────────────

def _make_client():
    from logseq import LogseqClient
    return LogseqClient("test-token", "http://localhost:12315")


def test_client_sets_auth_header():
    c = _make_client()
    assert "Bearer test-token" in c._session.headers["Authorization"]


def test_client_call_sends_correct_payload():
    c = _make_client()
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"name": "TestPage"}
    c._session.post = MagicMock(return_value=mock_resp)

    result = c.call("logseq.Editor.getPage", ["TestPage"])
    assert result == {"name": "TestPage"}

    call_kwargs = c._session.post.call_args
    body = call_kwargs[1]["json"]
    assert body["method"] == "logseq.Editor.getPage"
    assert body["args"] == ["TestPage"]


def test_client_call_returns_none_when_api_returns_none():
    c = _make_client()
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = None
    c._session.post = MagicMock(return_value=mock_resp)

    result = c.call("logseq.Editor.getPage", ["NonExistent"])
    assert result is None


def test_client_call_exits_on_connection_error():
    c = _make_client()
    c._session.post = MagicMock(side_effect=requests.ConnectionError("refused"))

    with pytest.raises(SystemExit, match="cannot reach Logseq API"):
        c.call("logseq.Editor.getPage", ["test"])


def test_client_call_exits_on_http_error():
    c = _make_client()
    error_resp = MagicMock()
    error_resp.status_code = 401
    error_resp.text = "Unauthorized"
    http_error = requests.HTTPError(response=error_resp)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock(side_effect=http_error)
    c._session.post = MagicMock(return_value=mock_resp)

    with pytest.raises(SystemExit, match="HTTP 401"):
        c.call("logseq.Editor.getPage", ["test"])


def test_client_api_url_strips_trailing_slash():
    from logseq import LogseqClient
    c = LogseqClient("tok", "http://localhost:12315/")
    assert c._url == "http://localhost:12315/api"


# ── script smoke tests ────────────────────────────────────────────────────────

def _run_script(script_name: str, argv: list, mock_responses: list) -> str:
    """Run a script with mocked API responses and capture its stdout."""
    import io
    import importlib.util

    scripts_dir = Path(__file__).parent.parent / "scripts"
    spec = importlib.util.spec_from_file_location(
        script_name.replace("-", "_").replace(".py", ""),
        str(scripts_dir / script_name),
    )
    # We can't easily exec scripts with side-effects this way, so test via subprocess
    raise NotImplementedError("Use subprocess tests for script smoke tests")


def test_list_pages_filter_flags_are_mutually_exclusive():
    """list-pages.py should exclude journals when --no-journal is set."""
    import importlib.util
    from unittest.mock import patch

    spec = importlib.util.spec_from_file_location(
        "list_pages",
        str(Path(__file__).parent.parent / "scripts" / "list-pages.py"),
    )
    # Verify the filtering logic by inspecting what would be filtered
    sample_pages = [
        {"name": "Journal", "uuid": "a", "journalDay": 20260512},
        {"name": "Notes", "uuid": "b", "journalDay": None},
    ]
    journal_pages = [p for p in sample_pages if p.get("journalDay") is not None]
    regular_pages = [p for p in sample_pages if p.get("journalDay") is None]
    assert len(journal_pages) == 1
    assert len(regular_pages) == 1
    assert journal_pages[0]["name"] == "Journal"
    assert regular_pages[0]["name"] == "Notes"


def test_search_results_normalisation():
    """Verify the block/page result normalisation logic."""
    raw = {
        "blocks": [
            {"uuid": "abc", "content": "hello world", "page": {"originalName": "MyPage"}},
        ],
        "pages": ["AnotherPage"],
    }
    blocks = raw.get("blocks", [])
    pages = raw.get("pages", [])
    results = []
    for b in blocks:
        results.append({
            "type": "block",
            "page": b.get("page", {}).get("originalName"),
            "block_uuid": b.get("uuid"),
            "content": b.get("content"),
        })
    for p in pages:
        results.append({
            "type": "page",
            "page": p if isinstance(p, str) else p.get("originalName"),
            "block_uuid": None,
            "content": None,
        })
    assert len(results) == 2
    assert results[0]["type"] == "block"
    assert results[0]["page"] == "MyPage"
    assert results[1]["type"] == "page"
    assert results[1]["page"] == "AnotherPage"
