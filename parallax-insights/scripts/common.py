import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import requests


class ParallaxClient:
    BASE_URL = "https://insights.getparallax.com/api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "parallax-insights (ll-agent-skills)",
        })

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        # Add API key to query parameters
        params = dict(params or {})
        params["apikey"] = self.api_key
        for attempt in range(3):
            try:
                resp = self.session.get(url, params=params, timeout=30)
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 2 ** (attempt + 1)))
                    print(f"  Rate limited, retrying in {wait}s...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.HTTPError:
                if attempt == 2:
                    raise
        return {}


def check_api_key() -> str:
    key = os.environ.get("PARALLAX_API_KEY", "")
    if not key:
        print("Error: PARALLAX_API_KEY is not set.", file=sys.stderr)
        print("       Generate an API key at https://app.getparallax.com/settings/api", file=sys.stderr)
        sys.exit(1)
    return key


def resolve_range(days: int, since: str = "", until: str = "") -> tuple[str, str, str, str]:
    """Returns (start_date, end_date, since_iso, until_iso)."""
    if since or until:
        if not (since and until):
            print("Error: --since and --until must be provided together.", file=sys.stderr)
            sys.exit(1)
        start_date = since[:10]
        end_date = until[:10]
        since_iso = _iso_start(since)
        until_iso = _iso_end(until)
    else:
        today = date.today()
        end_date = today.isoformat()
        start_date = (today - timedelta(days=days)).isoformat()
        since_iso = f"{start_date}T00:00:00Z"
        until_iso = f"{end_date}T23:59:59Z"
    return start_date, end_date, since_iso, until_iso


def _iso_start(value: str) -> str:
    return f"{value}T00:00:00Z" if re.match(r"^\d{4}-\d{2}-\d{2}$", value) else value


def _iso_end(value: str) -> str:
    return f"{value}T23:59:59Z" if re.match(r"^\d{4}-\d{2}-\d{2}$", value) else value


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(value: str) -> str:
    value = value.lower().replace("/", "-")
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


def person_name(person: dict) -> str:
    if person.get("name"):
        return person["name"]
    parts = [person.get("first_name", ""), person.get("last_name", "")]
    return " ".join(p for p in parts if p).strip() or person.get("id", "unknown")


def write_json(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Wrote: {path}")
