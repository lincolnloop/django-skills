#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Usage: list-pages.py [--journal-only] [--no-journal]

Lists all pages in the Logseq graph.
Returns {"count": N, "pages": [{"name": ..., "uuid": ..., ...}, ...]}.

Options:
  --journal-only  Include only journal pages
  --no-journal    Exclude journal pages (include only regular pages)

Environment:
  LOGSEQ_API_TOKEN  required
  LOGSEQ_API_URL    optional, defaults to http://localhost:12315
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from logseq import LogseqClient, check_env

journal_only = "--journal-only" in sys.argv
no_journal = "--no-journal" in sys.argv

token, api_url = check_env()
client = LogseqClient(token, api_url)

all_pages = client.call("logseq.Editor.getAllPages", []) or []

pages = []
for p in all_pages:
    is_journal = p.get("journalDay") is not None
    if journal_only and not is_journal:
        continue
    if no_journal and is_journal:
        continue
    pages.append({
        "name": p.get("name") or p.get("originalName"),
        "uuid": p.get("uuid"),
        "journal": is_journal,
        "journal_day": p.get("journalDay"),
        "updated_at": p.get("updatedAt"),
        "created_at": p.get("createdAt"),
    })

pages.sort(key=lambda p: p.get("name") or "")

print(json.dumps({"count": len(pages), "pages": pages}, indent=2))
