"""Unit tests for statuscake.py shared library — no live API calls."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ── now_utc ───────────────────────────────────────────────────────────────────

def test_now_utc_format():
    from statuscake import now_utc
    ts = now_utc()
    assert ts.endswith("Z")
    assert "T" in ts
    assert len(ts) == 20  # YYYY-MM-DDTHH:MM:SSZ


# ── write_json ────────────────────────────────────────────────────────────────

def test_write_json_roundtrip(tmp_path):
    from statuscake import write_json
    data = {"key": "value", "count": 42, "nested": {"x": [1, 2, 3]}}
    out_path = str(tmp_path / "test.json")
    write_json(out_path, data)
    loaded = json.loads(Path(out_path).read_text())
    assert loaded == data


def test_write_json_creates_parent_directories(tmp_path):
    from statuscake import write_json
    out_path = str(tmp_path / "a" / "b" / "c" / "test.json")
    write_json(out_path, {"x": 1})
    assert Path(out_path).exists()


# ── check_env ─────────────────────────────────────────────────────────────────

def test_check_env_missing_exits(monkeypatch):
    monkeypatch.delenv("STATUSCAKE_API_KEY", raising=False)
    import statuscake
    with pytest.raises(SystemExit):
        statuscake.check_env()


def test_check_env_present(monkeypatch):
    monkeypatch.setenv("STATUSCAKE_API_KEY", "test-key-abc")
    import statuscake
    key = statuscake.check_env()
    assert key == "test-key-abc"


# ── base_parser ───────────────────────────────────────────────────────────────

def test_base_parser_defaults():
    from statuscake import base_parser
    parser = base_parser("Test description")
    args = parser.parse_args([])
    assert args.output_dir is None
    assert args.prefix == ""


def test_base_parser_accepts_output_dir():
    from statuscake import base_parser
    parser = base_parser("Test")
    args = parser.parse_args(["--output-dir", "/tmp/out", "--prefix", "test-"])
    assert args.output_dir == "/tmp/out"
    assert args.prefix == "test-"


# ── StatusCakeClient ──────────────────────────────────────────────────────────

def test_client_sets_auth_header():
    from statuscake import StatusCakeClient
    c = StatusCakeClient("my-api-key")
    assert "Bearer my-api-key" in c._session.headers["Authorization"]


def test_client_get_success():
    from statuscake import StatusCakeClient
    c = StatusCakeClient("key")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"data": [{"id": 1}], "metadata": {"page_count": 1}}
    c._session.get = MagicMock(return_value=mock_resp)

    result = c.get("/uptime")
    assert result["data"][0]["id"] == 1


def test_client_get_passes_params():
    from statuscake import StatusCakeClient
    c = StatusCakeClient("key")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"data": [], "metadata": {"page_count": 1}}
    c._session.get = MagicMock(return_value=mock_resp)

    c.get("/uptime", status="up", tags="prod")
    call_kwargs = c._session.get.call_args
    params = call_kwargs[1]["params"]
    assert params["status"] == "up"
    assert params["tags"] == "prod"


def test_client_get_omits_none_params():
    from statuscake import StatusCakeClient
    c = StatusCakeClient("key")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"data": [], "metadata": {"page_count": 1}}
    c._session.get = MagicMock(return_value=mock_resp)

    c.get("/uptime", status=None, tags="prod")
    call_kwargs = c._session.get.call_args
    params = call_kwargs[1]["params"]
    assert "status" not in params
    assert params["tags"] == "prod"


def test_client_get_all_single_page():
    from statuscake import StatusCakeClient
    c = StatusCakeClient("key")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "data": [{"id": 1}, {"id": 2}],
        "metadata": {"page_count": 1, "page": 1},
    }
    c._session.get = MagicMock(return_value=mock_resp)

    result = c.get_all("/uptime")
    assert result == [{"id": 1}, {"id": 2}]
    assert c._session.get.call_count == 1


def test_client_get_all_follows_pagination():
    from statuscake import StatusCakeClient
    c = StatusCakeClient("key")

    page1 = {"data": [{"id": 1}], "metadata": {"page_count": 2, "page": 1}}
    page2 = {"data": [{"id": 2}, {"id": 3}], "metadata": {"page_count": 2, "page": 2}}

    call_idx = 0
    responses = [page1, page2]

    def fake_get(url, params=None):
        nonlocal call_idx
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = responses[call_idx]
        call_idx += 1
        return resp

    c._session.get = fake_get
    result = c.get_all("/uptime")
    assert len(result) == 3
    assert result[0]["id"] == 1
    assert result[2]["id"] == 3


def test_client_get_all_empty_response():
    from statuscake import StatusCakeClient
    c = StatusCakeClient("key")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"data": [], "metadata": {"page_count": 1}}
    c._session.get = MagicMock(return_value=mock_resp)

    result = c.get_all("/uptime")
    assert result == []


def test_client_get_all_missing_data_key():
    from statuscake import StatusCakeClient
    c = StatusCakeClient("key")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"metadata": {"page_count": 1}}
    c._session.get = MagicMock(return_value=mock_resp)

    result = c.get_all("/uptime")
    assert result == []


def test_client_get_raises_on_http_error():
    import requests
    from statuscake import StatusCakeClient
    c = StatusCakeClient("key")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock(side_effect=requests.HTTPError("403"))
    c._session.get = MagicMock(return_value=mock_resp)

    with pytest.raises(requests.HTTPError):
        c.get("/uptime")
