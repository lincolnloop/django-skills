#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Usage: get-current-page.py

Returns the page currently open in Logseq, including its block tree.
Returns {"page": {...}, "blocks": [...]} or null if no page is open.

Environment:
  LOGSEQ_API_TOKEN  required
  LOGSEQ_API_URL    optional, defaults to http://localhost:12315
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from logseq import LogseqClient, check_env

token, api_url = check_env()
client = LogseqClient(token, api_url)

page = client.call("logseq.App.getCurrentPage", [])
if page is None:
    print("null")
else:
    name = page.get("name") or page.get("originalName")
    blocks = client.call("logseq.Editor.getPageBlocksTree", [name]) if name else []
    print(json.dumps({"page": page, "blocks": blocks}, indent=2))
