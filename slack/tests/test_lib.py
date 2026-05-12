"""Unit tests for slack.py shared library — no live API calls."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import importlib.util

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def _load_send_report():
    spec = importlib.util.spec_from_file_location(
        "send_report",
        str(Path(__file__).parent.parent / "scripts" / "send-report.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ── now_utc ───────────────────────────────────────────────────────────────────

def test_now_utc_format():
    from slack import now_utc
    ts = now_utc()
    assert ts.endswith("Z")
    assert "T" in ts
    assert len(ts) == 20


# ── resolve_channel ───────────────────────────────────────────────────────────

def test_resolve_channel_strips_hash():
    from slack import resolve_channel
    assert resolve_channel("#general") == "general"


def test_resolve_channel_passes_through_id():
    from slack import resolve_channel
    assert resolve_channel("C123ABC456") == "C123ABC456"


def test_resolve_channel_passes_through_name_without_hash():
    from slack import resolve_channel
    assert resolve_channel("engineering") == "engineering"


# ── write_json ────────────────────────────────────────────────────────────────

def test_write_json_roundtrip(tmp_path):
    from slack import write_json
    data = {"key": "value", "count": 42}
    out_path = str(tmp_path / "test.json")
    write_json(out_path, data)
    loaded = json.loads(Path(out_path).read_text())
    assert loaded == data


def test_write_json_creates_parent_directories(tmp_path):
    from slack import write_json
    out_path = str(tmp_path / "a" / "b" / "test.json")
    write_json(out_path, {"x": 1})
    assert Path(out_path).exists()


# ── check_env ─────────────────────────────────────────────────────────────────

def test_check_env_missing_exits(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    import slack
    with pytest.raises(SystemExit):
        slack.check_env()


def test_check_env_present(monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
    import slack
    token = slack.check_env()
    assert token == "xoxb-test-token"


# ── base_parser ───────────────────────────────────────────────────────────────

def test_base_parser_defaults():
    from slack import base_parser
    parser = base_parser("Test")
    args = parser.parse_args([])
    assert args.output_dir is None
    assert args.prefix == ""


# ── SlackClient ───────────────────────────────────────────────────────────────

def _mock_ok_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"ok": True, **payload}
    return resp


def _mock_error_response(error: str) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"ok": False, "error": error}
    return resp


def test_client_sets_auth_header():
    from slack import SlackClient
    c = SlackClient("xoxb-my-token")
    assert "Bearer xoxb-my-token" in c._session.headers["Authorization"]


def test_client_post_success():
    from slack import SlackClient
    c = SlackClient("tok")
    c._session.post = MagicMock(return_value=_mock_ok_response({"channel": "C123", "ts": "1.0"}))

    result = c.post("chat.postMessage", channel="C123", text="hello")
    assert result["channel"] == "C123"
    assert result["ts"] == "1.0"


def test_client_post_raises_on_error():
    from slack import SlackClient
    c = SlackClient("tok")
    c._session.post = MagicMock(return_value=_mock_error_response("not_in_channel"))

    with pytest.raises(RuntimeError, match="not_in_channel"):
        c.post("chat.postMessage", channel="C123", text="hello")


def test_client_get_success():
    from slack import SlackClient
    c = SlackClient("tok")
    c._session.get = MagicMock(return_value=_mock_ok_response(
        {"channels": [{"id": "C1"}], "response_metadata": {"next_cursor": ""}}
    ))

    result = c.get("conversations.list")
    assert result["channels"][0]["id"] == "C1"


def test_client_get_raises_on_error():
    from slack import SlackClient
    c = SlackClient("tok")
    c._session.get = MagicMock(return_value=_mock_error_response("channel_not_found"))

    with pytest.raises(RuntimeError, match="channel_not_found"):
        c.get("conversations.history", channel="C999")


def test_client_get_all_single_page():
    from slack import SlackClient
    c = SlackClient("tok")
    c._session.get = MagicMock(return_value=_mock_ok_response({
        "channels": [{"id": "C1"}, {"id": "C2"}],
        "response_metadata": {"next_cursor": ""},
    }))

    result = c.get_all("conversations.list", "channels")
    assert len(result) == 2
    assert result[0]["id"] == "C1"


def test_client_get_all_follows_cursor_pagination():
    from slack import SlackClient
    c = SlackClient("tok")

    page1 = _mock_ok_response({
        "channels": [{"id": "C1"}],
        "response_metadata": {"next_cursor": "dXNlcjpVMDYx"},
    })
    page2 = _mock_ok_response({
        "channels": [{"id": "C2"}, {"id": "C3"}],
        "response_metadata": {"next_cursor": ""},
    })

    c._session.get = MagicMock(side_effect=[page1, page2])
    result = c.get_all("conversations.list", "channels")
    assert len(result) == 3
    assert result[2]["id"] == "C3"


def test_client_get_all_empty():
    from slack import SlackClient
    c = SlackClient("tok")
    c._session.get = MagicMock(return_value=_mock_ok_response({
        "channels": [],
        "response_metadata": {"next_cursor": ""},
    }))

    result = c.get_all("conversations.list", "channels")
    assert result == []


# ── send-report format detection ──────────────────────────────────────────────

def test_detect_format_harvest_time():
    detect_format = _load_send_report().detect_format
    data = {"category": "time_entries", "by_user": [], "by_project": []}
    assert detect_format(data) == "harvest-time"


def test_detect_format_parallax_time():
    detect_format = _load_send_report().detect_format
    data = {"category": "time_entries", "by_person": []}
    assert detect_format(data) == "parallax-time"


def test_detect_format_statuscake_uptime():
    detect_format = _load_send_report().detect_format
    data = {"category": "uptime_checks", "counts": {}, "checks_down": []}
    assert detect_format(data) == "statuscake-uptime"


def test_detect_format_parallax_financials():
    detect_format = _load_send_report().detect_format
    data = {"category": "people_financials"}
    assert detect_format(data) == "parallax-financials"


def test_detect_format_github():
    detect_format = _load_send_report().detect_format
    data = {"commits": [], "summary": {}}
    assert detect_format(data) == "github"


def test_detect_format_unknown_raises():
    detect_format = _load_send_report().detect_format
    with pytest.raises(ValueError, match="Cannot auto-detect"):
        detect_format({"category": "unknown_thing"})


# ── block builder smoke tests ─────────────────────────────────────────────────

def test_build_statuscake_uptime_blocks():
    build_statuscake_uptime_blocks = _load_send_report().build_statuscake_uptime_blocks
    data = {
        "category": "uptime_checks",
        "generated_at": "2026-05-12T09:00:00Z",
        "counts": {"total": 10, "up": 9, "down": 1, "paused": 0, "avg_uptime_pct": 99.2},
        "checks_down": [{"name": "Prod API", "website_url": "https://api.example.com", "uptime": 98.1}],
        "checks_up": [],
        "checks_paused": [],
    }
    blocks, fallback = build_statuscake_uptime_blocks(data)
    assert any(b["type"] == "header" for b in blocks)
    assert "down" in fallback.lower() or "up" in fallback.lower()
    assert any("Prod API" in str(b) for b in blocks)


def test_build_harvest_time_blocks():
    build_harvest_time_blocks = _load_send_report().build_harvest_time_blocks
    data = {
        "category": "time_entries",
        "generated_at": "2026-05-12T09:00:00Z",
        "range": {"start_date": "2026-05-05", "end_date": "2026-05-11"},
        "counts": {"total_hours": 80.0, "billable_hours": 64.0, "non_billable_hours": 16.0,
                   "active_users": 5, "total_entries": 40},
        "by_user": [{"user": "Alice", "total_hours": 40.0}],
        "by_project": [],
    }
    blocks, fallback = build_harvest_time_blocks(data)
    assert any(b["type"] == "header" for b in blocks)
    assert "80" in fallback


def test_build_parallax_time_blocks():
    build_parallax_time_blocks = _load_send_report().build_parallax_time_blocks
    data = {
        "category": "time_entries",
        "generated_at": "2026-05-12T09:00:00Z",
        "range": {"start_date": "2026-05-05", "end_date": "2026-05-11"},
        "counts": {"total_hours": 60.0, "billable_hours": 50.0, "non_billable_hours": 10.0, "active_people": 4},
        "by_person": [{"name": "Bob", "person_id": "abc", "total_hours": 30.0}],
        "items": [],
    }
    blocks, fallback = build_parallax_time_blocks(data)
    assert any(b["type"] == "header" for b in blocks)
    assert "Bob" in str(blocks)
