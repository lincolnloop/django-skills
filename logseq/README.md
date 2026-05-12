# Logseq Skill

A collection of Python scripts that read and write a local [Logseq](https://logseq.com/) graph via its built-in HTTP API. Each script targets a single operation — list pages, fetch a page's block tree, create/update/delete blocks, or run a full-text search.

## Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Scripts reference](#scripts-reference)
- [Usage examples](#usage-examples)
- [Running tests](#running-tests)

---

## Installation

### Via vercel-labs/skills (recommended)

Install into your project's Claude Code skill directory with a single command:

```bash
npx skills add lincoln-loop/agent-skills --skill logseq
```

Or install globally so it's available in every project:

```bash
npx skills add lincoln-loop/agent-skills --skill logseq --global
```

Interactive mode — choose which agents to target and whether to symlink or copy:

```bash
npx skills add lincoln-loop/agent-skills
```

Non-interactive (CI / scripted):

```bash
npx skills add lincoln-loop/agent-skills --skill logseq -a claude-code -y
```

Once installed, Claude Code picks up the skill automatically when you ask about your Logseq notes.

### Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
- [uv](https://docs.astral.sh/uv/) (for running the scripts — handles Python and dependencies automatically)
- Logseq desktop app with HTTP APIs enabled (Settings → Developer → HTTP APIs → Enable)

---

## Configuration

Scripts read credentials from environment variables.

| Variable | Description |
|---|---|
| `LOGSEQ_API_TOKEN` | Token shown in Logseq Settings → Developer → HTTP APIs |
| `LOGSEQ_API_URL` | API base URL. Defaults to `http://localhost:12315` |

Export them in your shell:

```bash
export LOGSEQ_API_TOKEN=your_token_here
```

---

## Scripts reference

All scripts live in `scripts/`. Run any script with no arguments for usage help.

### Read operations

| Script | Description |
|---|---|
| `list-pages.py` | List all pages in the graph. Accepts `--journal-only` or `--no-journal`. |
| `get-page.py <name>` | Fetch page metadata and full block tree by page name. Returns `null` if not found. |
| `get-current-page.py` | Return the page currently open in the Logseq UI, with its block tree. Returns `null` if no page is focused. |
| `search-pages.py <query>` | Full-text search across all pages and blocks. Returns unified results list with `type`, `page`, `block_uuid`, and `content`. |

### Write operations

| Script | Description |
|---|---|
| `create-page.py <name> [content]` | Create a new page. If `content` is provided, writes it into the first block. |
| `insert-block.py <parent-uuid> <content> [--sibling]` | Insert a new block as a child of `parent-uuid`. Pass `--sibling` to insert after instead of inside. |
| `update-block.py <uuid> <content>` | Replace the text content of an existing block. |
| `delete-block.py <uuid>` | Permanently remove a block. |

---

## Usage examples

### List all regular (non-journal) pages

```bash
uv run scripts/list-pages.py --no-journal
```

### Fetch a specific page and its blocks

```bash
uv run scripts/get-page.py "My Project Notes"
```

### Search for a term across all notes

```bash
uv run scripts/search-pages.py "sprint planning"
```

### Create a new page with content

```bash
uv run scripts/create-page.py "Meeting Notes 2026-05-12" "## Agenda\n- Review sprint"
```

### Add a child block under an existing block

```bash
uv run scripts/insert-block.py "some-block-uuid" "New child item"
```

### Add a sibling block after an existing block

```bash
uv run scripts/insert-block.py "some-block-uuid" "Follow-up item" --sibling
```

### Update a block's content

```bash
uv run scripts/update-block.py "some-block-uuid" "Updated text"
```

### Delete a block

```bash
uv run scripts/delete-block.py "some-block-uuid"
```

---

## Running tests

### Unit tests (no Logseq needed)

```bash
uv run --with pytest --with requests pytest tests/test_lib.py -v
```

### Integration tests (live Logseq)

```bash
export LOGSEQ_API_TOKEN=...
uv run --with pytest --with requests pytest tests/ -v
```

Integration tests require Logseq to be running with HTTP APIs enabled. They are automatically skipped when Logseq is not reachable — safe to include in CI pipelines.
