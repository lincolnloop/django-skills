#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Usage: get-page.py <name>

Fetches page metadata and block tree from Logseq.
Returns {"page": {...}, "blocks": [...]} or null if the page does not exist.

Environment:
  LOGSEQ_API_TOKEN  required
  LOGSEQ_API_URL    optional, defaults to http://localhost:12315
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from logseq import LogseqClient, check_env

if len(sys.argv) < 2:
    print(__doc__.strip())
    sys.exit(1)

name = sys.argv[1]
token, api_url = check_env()
client = LogseqClient(token, api_url)

page = client.call("logseq.Editor.getPage", [name])
if page is None:
    print("null")
else:
    blocks = client.call("logseq.Editor.getPageBlocksTree", [name])
    print(json.dumps({"page": page, "blocks": blocks}, indent=2))
