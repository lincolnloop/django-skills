"""Unit tests for common.py shared library — no live API calls."""
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ── date utilities ────────────────────────────────────────────────────────────

def test_resolve_range_days():
    from common import resolve_range
    start, end, since_iso, until_iso = resolve_range(7)
    today = date.today()
    assert start == (today - timedelta(days=7)).isoformat()
    assert end == today.isoformat()
    assert since_iso.endswith("T00:00:00Z")
    assert until_iso.endswith("T23:59:59Z")


def test_resolve_range_zero_days():
    from common import resolve_range
    start, end, _, _ = resolve_range(0)
    today = date.today().isoformat()
    assert start == today
    assert end == today


def test_resolve_range_explicit_dates():
    from common import resolve_range
    start, end, since_iso, until_iso = resolve_range(7, "2026-01-01", "2026-01-31")
    assert start == "2026-01-01"
    assert end == "2026-01-31"
    assert since_iso == "2026-01-01T00:00:00Z"
    assert until_iso == "2026-01-31T23:59:59Z"


def test_resolve_range_passthrough_iso_datetime():
    from common import resolve_range
    start, end, since_iso, until_iso = resolve_range(
        7, "2026-01-01T08:00:00Z", "2026-01-31T17:00:00Z"
    )
    assert start == "2026-01-01"
    assert end == "2026-01-31"
    assert since_iso == "2026-01-01T08:00:00Z"
    assert until_iso == "2026-01-31T17:00:00Z"


def test_resolve_range_since_without_until_exits():
    from common import resolve_range
    with pytest.raises(SystemExit):
        resolve_range(7, "2026-01-01", "")


def test_resolve_range_until_without_since_exits():
    from common import resolve_range
    with pytest.raises(SystemExit):
        resolve_range(7, "", "2026-01-31")


def test_now_utc_format():
    from common import now_utc
    ts = now_utc()
    assert ts.endswith("Z")
    assert "T" in ts
    assert len(ts) == 20  # YYYY-MM-DDTHH:MM:SSZ


# ── slugify ───────────────────────────────────────────────────────────────────

def test_slugify_basic():
    from common import slugify
    assert slugify("Hello World") == "hello-world"


def test_slugify_slash_becomes_dash():
    from common import slugify
    assert slugify("by-offering/role") == "by-offering-role"


def test_slugify_strips_special_chars():
    from common import slugify
    assert slugify("foo & bar!") == "foo-bar"


def test_slugify_collapses_dashes():
    from common import slugify
    result = slugify("foo   bar")
    assert "--" not in result
    assert result.startswith("foo")
    assert result.endswith("bar")


def test_slugify_strips_leading_trailing_dashes():
    from common import slugify
    result = slugify("  hello  ")
    assert not result.startswith("-")
    assert not result.endswith("-")


# ── person_name ───────────────────────────────────────────────────────────────

def test_person_name_uses_name_field():
    from common import person_name
    assert person_name({"name": "Alice Smith", "given_name": "Alice", "family_name": "Smith"}) == "Alice Smith"


def test_person_name_assembles_from_parts():
    from common import person_name
    assert person_name({"first_name": "Bob", "last_name": "Jones"}) == "Bob Jones"


def test_person_name_given_only():
    from common import person_name
    assert person_name({"first_name": "Charlie"}) == "Charlie"


def test_person_name_falls_back_to_id():
    from common import person_name
    assert person_name({"id": "abc-123"}) == "abc-123"


def test_person_name_empty_dict():
    from common import person_name
    assert person_name({}) == "unknown"


# ── write_json ────────────────────────────────────────────────────────────────

def test_write_json_roundtrip(tmp_path):
    from common import write_json
    data = {"key": "value", "count": 42, "nested": {"x": [1, 2, 3]}}
    out_path = str(tmp_path / "test.json")
    write_json(data, out_path)
    loaded = json.loads(Path(out_path).read_text())
    assert loaded == data


def test_write_json_creates_parent_directories(tmp_path):
    from common import write_json
    out_path = str(tmp_path / "a" / "b" / "c" / "test.json")
    write_json({"x": 1}, out_path)
    assert Path(out_path).exists()


# ── check_api_key ─────────────────────────────────────────────────────────────

def test_check_api_key_missing_exits(monkeypatch):
    monkeypatch.delenv("PARALLAX_API_KEY", raising=False)
    import common
    with pytest.raises(SystemExit):
        common.check_api_key()


def test_check_api_key_present(monkeypatch):
    monkeypatch.setenv("PARALLAX_API_KEY", "test-key-123")
    import common
    key = common.check_api_key()
    assert key == "test-key-123"


# ── ParallaxClient ────────────────────────────────────────────────────────────

def test_parallax_client_injects_api_key():
    from common import ParallaxClient
    client = ParallaxClient("my-api-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"data": {}}
    client.session.get = MagicMock(return_value=mock_resp)

    client.get("/people/utilization", {"start_date": "2026-01-01"})

    call_kwargs = client.session.get.call_args
    params = call_kwargs[1]["params"] if call_kwargs[1] else call_kwargs[0][1]
    assert params.get("apikey") == "my-api-key"


def test_parallax_client_successful_get():
    from common import ParallaxClient
    client = ParallaxClient("key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"data": {"people": {}}}
    client.session.get = MagicMock(return_value=mock_resp)

    result = client.get("/people/utilization")
    assert result == {"data": {"people": {}}}


def test_parallax_client_retries_on_429():
    from common import ParallaxClient
    client = ParallaxClient("key")

    rate_limited = MagicMock()
    rate_limited.status_code = 429
    rate_limited.headers = {"Retry-After": "0"}

    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.raise_for_status = MagicMock()
    ok_resp.json.return_value = {"data": {}}

    client.session.get = MagicMock(side_effect=[rate_limited, ok_resp])

    import unittest.mock
    with unittest.mock.patch("time.sleep"):
        result = client.get("/people/utilization")

    assert result == {"data": {}}
    assert client.session.get.call_count == 2


def test_parallax_client_raises_after_max_retries():
    import requests
    from common import ParallaxClient
    client = ParallaxClient("key")

    rate_limited = MagicMock()
    rate_limited.status_code = 429
    rate_limited.headers = {"Retry-After": "0"}

    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.raise_for_status = MagicMock()
    ok_resp.json.return_value = {"data": {}}

    error_resp = MagicMock()
    error_resp.status_code = 500
    error_resp.raise_for_status = MagicMock(side_effect=requests.HTTPError("500"))

    client.session.get = MagicMock(side_effect=[error_resp, error_resp, error_resp])

    import unittest.mock
    with unittest.mock.patch("time.sleep"):
        with pytest.raises(requests.HTTPError):
            client.get("/people/utilization")
