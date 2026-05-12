#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Usage: insert-block.py <parent-uuid> <content> [--sibling]

Inserts a new block as a child of parent-uuid (default) or as a sibling after
it (with --sibling).

Environment:
  LOGSEQ_API_TOKEN  required
  LOGSEQ_API_URL    optional, defaults to http://localhost:12315
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from logseq import LogseqClient, check_env

args = sys.argv[1:]
if len(args) < 2:
    print(__doc__.strip())
    sys.exit(1)

parent_uuid = args[0]
sibling = "--sibling" in args
content = next(a for a in args[1:] if not a.startswith("--"))

token, api_url = check_env()
client = LogseqClient(token, api_url)

result = client.call("logseq.Editor.insertBlock", [parent_uuid, content, {"sibling": sibling}])
print(json.dumps(result, indent=2))
