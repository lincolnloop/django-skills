"""Shared library for Slack Web API scripts."""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


class SlackClient:
    BASE_URL = "https://slack.com/api"

    def __init__(self, token: str):
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "slack (ll-agent-skills)",
        })

    def post(self, method: str, **payload: Any) -> dict:
        resp = self._session.post(f"{self.BASE_URL}/{method}", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error on {method}: {data.get('error', 'unknown')}")
        return data

    def get(self, method: str, **params: Any) -> dict:
        resp = self._session.get(
            f"{self.BASE_URL}/{method}",
            params={k: v for k, v in params.items() if v is not None},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error on {method}: {data.get('error', 'unknown')}")
        return data

    def get_all(self, method: str, key: str, **params: Any) -> list:
        """Fetch all pages via cursor pagination and return a flat list."""
        items: list = []
        cursor: str = ""
        while True:
            if cursor:
                params["cursor"] = cursor
            data = self.get(method, **params)
            items.extend(data.get(key) or [])
            cursor = data.get("response_metadata", {}).get("next_cursor", "")
            if not cursor:
                break
        return items


def check_env() -> str:
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    if not token:
        print("Error: SLACK_BOT_TOKEN is not set.", file=sys.stderr)
        print("       Create a Slack app and install it to get a bot token (xoxb-...).", file=sys.stderr)
        sys.exit(1)
    return token


def resolve_channel(channel: str) -> str:
    """Pass through bare IDs; strip leading # from names."""
    return channel.lstrip("#")


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
