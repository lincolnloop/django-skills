#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Usage: update-block.py <uuid> <content>

Replaces the content of an existing block.

Environment:
  LOGSEQ_API_TOKEN  required
  LOGSEQ_API_URL    optional, defaults to http://localhost:12315
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from logseq import LogseqClient, check_env

if len(sys.argv) < 3:
    print(__doc__.strip())
    sys.exit(1)

uuid = sys.argv[1]
content = sys.argv[2]

token, api_url = check_env()
client = LogseqClient(token, api_url)

client.call("logseq.Editor.updateBlock", [uuid, content])
print(json.dumps({"uuid": uuid, "updated": True}))
