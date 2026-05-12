"""Shared Harvest API v2 client and utilities for agent-skill scripts."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

HARVEST_API_BASE = "https://api.harvestapp.com/v2"


def check_env() -> tuple[str, str]:
    token = os.environ.get("HARVEST_ACCESS_TOKEN", "")
    account_id = os.environ.get("HARVEST_ACCOUNT_ID", "")
    if not token:
        sys.exit(
            "Error: HARVEST_ACCESS_TOKEN is not set.\n"
            "       Generate a personal access token at https://id.getharvest.com/developers"
        )
    if not account_id:
        sys.exit(
            "Error: HARVEST_ACCOUNT_ID is not set.\n"
            "       Find your Account ID at https://id.getharvest.com/developers"
        )
    return token, account_id


class HarvestClient:
    """Thin authenticated wrapper around the Harvest API v2."""

    def __init__(self) -> None:
        token, account_id = check_env()
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Harvest-Account-Id": account_id,
                "User-Agent": "harvest (ll-agent-skill)",
            }
        )

    def get(self, path: str, **params: Any) -> dict:
        resp = self._session.get(f"{HARVEST_API_BASE}{path}", params=params or None)
        resp.raise_for_status()
        return resp.json()

    def get_all(self, path: str, key: str, **params: Any) -> list:
        """Fetch all pages for a paginated endpoint and return a flat list."""
        params.setdefault("per_page", 2000)
        url = f"{HARVEST_API_BASE}{path}"
        current_params: dict | None = dict(params)
        items: list = []
        while url:
            resp = self._session.get(url, params=current_params)
            resp.raise_for_status()
            data = resp.json()
            items.extend(data.get(key, []))
            url = (data.get("links") or {}).get("next") or ""
            current_params = None  # subsequent pages: full URL from links.next already has params
        return items


def resolve_range(days: int, since: str | None, until: str | None) -> tuple[str, str]:
    """Return (start_date, end_date) as YYYY-MM-DD strings."""
    if since or until:
        if not (since and until):
            sys.exit("Error: --since and --until must be provided together.")
        return since[:10], until[:10]
    end = date.today()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def date_for_reports(d: str) -> str:
    """Convert YYYY-MM-DD → YYYYMMDD (required by the Harvest reports API)."""
    return d.replace("-", "")


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: str, data: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    print(f"  Wrote: {path}")


def base_parser(description: str, *, default_days: int = 7) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--days", type=int, default=default_days, metavar="N",
                   help=f"Look back N days (default: {default_days})")
    p.add_argument("--since", metavar="DATE",
                   help="Inclusive start date YYYY-MM-DD (must be used with --until)")
    p.add_argument("--until", metavar="DATE",
                   help="Inclusive end date YYYY-MM-DD (must be used with --since)")
    p.add_argument("--output-dir", metavar="DIR", default=".",
                   help="Write output to this directory (default: .)")
    p.add_argument("--prefix", metavar="PREFIX", default="",
                   help="Output filename prefix")
    return p
