#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Usage: search-pages.py <query>

Full-text search across all pages and blocks in Logseq.
Returns {"query": "...", "count": N, "results": [{"page": "...", "block": "..."}, ...]}.

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

query = sys.argv[1]

token, api_url = check_env()
client = LogseqClient(token, api_url)

raw = client.call("logseq.App.search", [query]) or {}

blocks = raw.get("blocks", [])
pages = raw.get("pages", [])

results = []
for b in blocks:
    results.append({
        "type": "block",
        "page": b.get("page", {}).get("originalName") or b.get("page", {}).get("name"),
        "block_uuid": b.get("uuid") or b.get("block/uuid"),
        "content": b.get("content") or b.get("block/content"),
    })
for p in pages:
    results.append({
        "type": "page",
        "page": p if isinstance(p, str) else (p.get("originalName") or p.get("name")),
        "block_uuid": None,
        "content": None,
    })

print(json.dumps({"query": query, "count": len(results), "results": results}, indent=2))
