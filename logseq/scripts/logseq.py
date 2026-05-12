"""Shared library for Logseq HTTP API scripts."""
import json
import os
import sys
from typing import Any

import requests


class LogseqClient:
    def __init__(self, token: str, api_url: str):
        self._url = api_url.rstrip("/") + "/api"
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

    def call(self, method: str, args: list) -> Any:
        try:
            resp = self._session.post(
                self._url,
                json={"method": method, "args": args},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.ConnectionError as e:
            sys.exit(f"error: cannot reach Logseq API at {self._url} — {e}")
        except requests.HTTPError as e:
            sys.exit(f"error: HTTP {e.response.status_code} — {e.response.text}")


def check_env() -> tuple[str, str]:
    token = os.environ.get("LOGSEQ_API_TOKEN", "")
    if not token:
        print("error: LOGSEQ_API_TOKEN is not set", file=sys.stderr)
        print("       Enable HTTP APIs in Logseq: Settings → Developer → HTTP APIs", file=sys.stderr)
        sys.exit(1)
    api_url = os.environ.get("LOGSEQ_API_URL", "http://localhost:12315")
    return token, api_url
