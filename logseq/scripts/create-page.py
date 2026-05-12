#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Usage: create-page.py <name> [<content>]

Creates a Logseq page. If content is provided it is written into the first block.

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
content = sys.argv[2] if len(sys.argv) > 2 else None

token, api_url = check_env()
client = LogseqClient(token, api_url)

page = client.call("logseq.Editor.createPage", [name, {}, {"createFirstBlock": bool(content)}])
if content and page:
    blocks = client.call("logseq.Editor.getPageBlocksTree", [name])
    if blocks:
        client.call("logseq.Editor.updateBlock", [blocks[0]["uuid"], content])

print(json.dumps(page, indent=2))
