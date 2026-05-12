"""Unit tests for harvest.py shared library — no live API calls."""
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ── date utilities ────────────────────────────────────────────────────────────

def test_resolve_range_days():
    from harvest import resolve_range
    start, end = resolve_range(7, None, None)
    today = date.today()
    assert start == (today - timedelta(days=7)).isoformat()
    assert end == today.isoformat()


def test_resolve_range_zero_days():
    from harvest import resolve_range
    start, end = resolve_range(0, None, None)
    today = date.today().isoformat()
    assert start == today
    assert end == today


def test_resolve_range_explicit_dates():
    from harvest import resolve_range
    start, end = resolve_range(7, "2026-01-01", "2026-01-31")
    assert start == "2026-01-01"
    assert end == "2026-01-31"


def test_resolve_range_truncates_datetime_to_date():
    from harvest import resolve_range
    start, end = resolve_range(7, "2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z")
    assert start == "2026-01-01"
    assert end == "2026-01-31"


def test_resolve_range_since_without_until_exits():
    from harvest import resolve_range
    with pytest.raises(SystemExit):
        resolve_range(7, "2026-01-01", None)


def test_resolve_range_until_without_since_exits():
    from harvest import resolve_range
    with pytest.raises(SystemExit):
        resolve_range(7, None, "2026-01-31")


def test_date_for_reports_converts_dashes():
    from harvest import date_for_reports
    assert date_for_reports("2026-04-14") == "20260414"
    assert date_for_reports("2026-01-01") == "20260101"
    assert date_for_reports("2026-12-31") == "20261231"


def test_now_utc_format():
    from harvest import now_utc
    ts = now_utc()
    assert ts.endswith("Z")
    assert "T" in ts
    assert len(ts) == 20  # YYYY-MM-DDTHH:MM:SSZ


# ── write_json ────────────────────────────────────────────────────────────────

def test_write_json_roundtrip(tmp_path):
    from harvest import write_json
    data = {"key": "value", "count": 42, "nested": {"x": [1, 2, 3]}}
    out_path = str(tmp_path / "test.json")
    write_json(out_path, data)
    loaded = json.loads(Path(out_path).read_text())
    assert loaded == data


def test_write_json_creates_parent_directories(tmp_path):
    from harvest import write_json
    out_path = str(tmp_path / "a" / "b" / "c" / "test.json")
    write_json(out_path, {"x": 1})
    assert Path(out_path).exists()


# ── environment checks ────────────────────────────────────────────────────────

def test_check_env_missing_token(monkeypatch):
    monkeypatch.delenv("HARVEST_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("HARVEST_ACCOUNT_ID", "123456")
    import harvest
    with pytest.raises(SystemExit) as exc_info:
        harvest.check_env()
    assert "HARVEST_ACCESS_TOKEN" in str(exc_info.value)


def test_check_env_missing_account_id(monkeypatch):
    monkeypatch.setenv("HARVEST_ACCESS_TOKEN", "fake-token")
    monkeypatch.delenv("HARVEST_ACCOUNT_ID", raising=False)
    import harvest
    with pytest.raises(SystemExit) as exc_info:
        harvest.check_env()
    assert "HARVEST_ACCOUNT_ID" in str(exc_info.value)


def test_check_env_both_present(monkeypatch):
    monkeypatch.setenv("HARVEST_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("HARVEST_ACCOUNT_ID", "123")
    import harvest
    token, account_id = harvest.check_env()
    assert token == "tok"
    assert account_id == "123"


# ── HarvestClient ─────────────────────────────────────────────────────────────

def test_harvest_client_sets_auth_headers(monkeypatch):
    monkeypatch.setenv("HARVEST_ACCESS_TOKEN", "mytoken")
    monkeypatch.setenv("HARVEST_ACCOUNT_ID", "99999")
    import harvest
    c = harvest.HarvestClient()
    assert "Bearer mytoken" in c._session.headers["Authorization"]
    assert c._session.headers["Harvest-Account-Id"] == "99999"


def test_harvest_client_get_all_single_page(monkeypatch):
    monkeypatch.setenv("HARVEST_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("HARVEST_ACCOUNT_ID", "123")
    import harvest

    page = {"items": [{"id": 1}, {"id": 2}], "links": {"next": None}}

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = page

    c = harvest.HarvestClient()
    c._session.get = MagicMock(return_value=mock_resp)

    result = c.get_all("/items", "items")
    assert result == [{"id": 1}, {"id": 2}]
    assert c._session.get.call_count == 1


def test_harvest_client_get_all_follows_pagination(monkeypatch):
    monkeypatch.setenv("HARVEST_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("HARVEST_ACCOUNT_ID", "123")
    import harvest

    page1 = {"items": [{"id": 1}], "links": {"next": "https://api.harvestapp.com/v2/items?page=2"}}
    page2 = {"items": [{"id": 2}, {"id": 3}], "links": {"next": None}}

    responses = [page1, page2]
    call_idx = 0

    def fake_get(url, params=None):
        nonlocal call_idx
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = responses[call_idx]
        call_idx += 1
        return resp

    c = harvest.HarvestClient()
    c._session.get = fake_get

    result = c.get_all("/items", "items")
    assert len(result) == 3
    assert result[0]["id"] == 1
    assert result[2]["id"] == 3


def test_harvest_client_get_all_empty_response(monkeypatch):
    monkeypatch.setenv("HARVEST_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("HARVEST_ACCOUNT_ID", "123")
    import harvest

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"items": [], "links": {"next": None}}

    c = harvest.HarvestClient()
    c._session.get = MagicMock(return_value=mock_resp)

    result = c.get_all("/items", "items")
    assert result == []


def test_harvest_client_get_all_missing_key_returns_empty(monkeypatch):
    monkeypatch.setenv("HARVEST_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("HARVEST_ACCOUNT_ID", "123")
    import harvest

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"other_key": [], "links": {}}

    c = harvest.HarvestClient()
    c._session.get = MagicMock(return_value=mock_resp)

    result = c.get_all("/items", "items")
    assert result == []
