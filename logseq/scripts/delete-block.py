#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Usage: delete-block.py <uuid>

Removes a block from Logseq.

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

uuid = sys.argv[1]

token, api_url = check_env()
client = LogseqClient(token, api_url)

client.call("logseq.Editor.removeBlock", [uuid])
print(json.dumps({"uuid": uuid, "deleted": True}))
