"""Shared library for StatusCake API scripts."""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


class StatusCakeClient:
    BASE_URL = "https://api.statuscake.com/v1"

    def __init__(self, api_key: str):
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "statuscake (ll-agent-skills)",
        })

    def get(self, path: str, **params: Any) -> dict:
        url = f"{self.BASE_URL}{path}"
        resp = self._session.get(url, params={k: v for k, v in params.items() if v is not None})
        resp.raise_for_status()
        return resp.json()

    def get_all(self, path: str, **params: Any) -> list:
        """Fetch all pages and return a flat list of items."""
        items: list = []
        page = 1
        page_count = 1
        while page <= page_count:
            data = self.get(path, page=page, limit=100, **params)
            items.extend(data.get("data") or [])
            page_count = data.get("metadata", {}).get("page_count", 1)
            page += 1
        return items


def check_env() -> str:
    key = os.environ.get("STATUSCAKE_API_KEY", "")
    if not key:
        print("Error: STATUSCAKE_API_KEY is not set.", file=sys.stderr)
        print("       Generate an API key at https://app.statuscake.com/User", file=sys.stderr)
        sys.exit(1)
    return key


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: str, data: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Wrote: {path}")


def base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--output-dir", default=None, help="Output directory (default: .)")
    parser.add_argument("--prefix", default="", help="Output filename prefix")
    return parser
