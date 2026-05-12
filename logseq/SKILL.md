---
name: logseq
description: Read and write a local Logseq graph via its HTTP API. Use when the user wants to search their notes, fetch a page's content, create or update pages and blocks, or browse their journal entries.
---

# Logseq

Reads and writes a local [Logseq](https://logseq.com/) graph via its built-in HTTP API. Scripts are focused on individual operations — list, read, create, update, delete.

**Requires**: Logseq desktop app running with HTTP APIs enabled (Settings → Developer → HTTP APIs → Enable).

## Scripts

### Read

| Script | What it does |
|--------|-------------|
| `list-pages.py` | List all pages. Pass `--journal-only` to see only journal entries, `--no-journal` to exclude them. |
| `get-page.py <name>` | Fetch page metadata plus the full nested block tree by page name. Returns `null` if the page does not exist. |
| `get-current-page.py` | Return the page currently open in the Logseq UI with its block tree. Returns `null` if no page is focused. |
| `search-pages.py <query>` | Full-text search across all pages and blocks. Returns a unified list of matching blocks and pages with `type`, `page`, `block_uuid`, and `content`. |

### Write

| Script | What it does |
|--------|-------------|
| `create-page.py <name> [content]` | Create a new page. Optional `content` is written into the first block. |
| `insert-block.py <parent-uuid> <content> [--sibling]` | Insert a block as a child of `parent-uuid`. Pass `--sibling` to insert after it instead of inside. |
| `update-block.py <uuid> <content>` | Replace the text of a block. Returns `{"uuid": "...", "updated": true}`. |
| `delete-block.py <uuid>` | Delete a block permanently. Returns `{"uuid": "...", "deleted": true}`. |

## Output Schemas

| Schema | Describes output of |
|--------|-------------------|
| `logseq.page.schema.json` | `get-page.py`, `get-current-page.py` — page metadata + recursive block tree, or `null` |

## When to Use

- User wants to look up notes, meeting minutes, or project pages by name
- User wants to search across all notes for a term or topic
- User wants to see today's journal entry or another journal page
- User wants to create a new note or add a block to an existing one
- User asks to update or delete content from a Logseq page
- User asks what page they are currently looking at in Logseq

## Instructions for Pi

1. Check that `LOGSEQ_API_TOKEN` is set. If missing, tell the user to enable HTTP APIs in Logseq (Settings → Developer → HTTP APIs) and copy the token.
2. If `LOGSEQ_API_URL` is not set, the scripts default to `http://localhost:12315` — this is correct for the standard Logseq desktop app setup.
3. Before writing to a page, call `get-page.py` first to confirm the page exists and to get block UUIDs for any targeted updates.
4. Block UUIDs are stable identifiers — always pass them when calling `insert-block.py`, `update-block.py`, or `delete-block.py`.
5. `insert-block.py` defaults to creating a **child** of the given block. Pass `--sibling` to insert at the same level after it.
6. `get-current-page.py` can return `null` when no page is open — handle this gracefully rather than assuming a page is always focused.
7. `search-pages.py` returns both block matches and page matches in a unified list; check the `type` field (`"block"` or `"page"`) to interpret each result.
8. Journal pages are regular pages with a `journal_day` field set (integer `YYYYMMDD`). Use `list-pages.py --journal-only` to browse them.
9. Do not delete blocks unless the user explicitly asks — prefer `update-block.py` to clear content.
10. If Logseq is not running, all scripts will exit with a "cannot reach Logseq API" error — remind the user to start the desktop app.
