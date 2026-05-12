# Parallax Insights Skill

A collection of Python scripts that cover the [Parallax Insights API](https://www.getparallax.com/), designed to be used by AI agents and humans alike. Each script is focused on a single data dimension — combine them to build whatever summary you need.

## Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Scripts reference](#scripts-reference)
- [Usage examples](#usage-examples)
- [Running tests](#running-tests)
- [Output format](#output-format)

---

## Installation

### Via vercel-labs/skills (recommended)

Install into your project's Claude Code skill directory with a single command:

```bash
npx skills add lincoln-loop/agent-skills --skill parallax-insights
```

Or install globally so it's available in every project:

```bash
npx skills add lincoln-loop/agent-skills --skill parallax-insights --global
```

Interactive mode — choose which agents to target and whether to symlink or copy:

```bash
npx skills add lincoln-loop/agent-skills
```

Non-interactive (CI / scripted):

```bash
npx skills add lincoln-loop/agent-skills --skill parallax-insights -a claude-code -y
```

Once installed, Claude Code picks up the skill automatically when you ask about Parallax time entries, allocations, financials, or project data.

### Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
- [uv](https://docs.astral.sh/uv/) (for running the scripts — handles Python and dependencies automatically)

---

## Configuration

All scripts read credentials from the environment variable below.

| Variable | Where to find it |
|---|---|
| `PARALLAX_API_KEY` | [app.getparallax.com/settings/api](https://app.getparallax.com/settings/api) |

Export it in your shell:

```bash
export PARALLAX_API_KEY=your_api_key_here
```

Or add it to a `.env` file and load with `direnv` / `dotenv`.

---

## Scripts reference

All scripts live in `scripts/`. Run any script with `--help` for full usage.

### Shared parameters

Scripts that accept a date range support:

| Flag | Description |
|---|---|
| `--days N` | Look back N days from today (default: 7; max: 90) |
| `--since DATE` | Start date `YYYY-MM-DD` (must pair with `--until`) |
| `--until DATE` | End date `YYYY-MM-DD` (must pair with `--since`) |
| `--output-dir DIR` | Directory for output files (default: `.`) |
| `--prefix PREFIX` | Prepended to every output filename |

### Time and allocation reports

| Script | Output file | Description |
|---|---|---|
| `time_entries.py` | `time-entries.json` | Actual hours logged per person per period, with billable and non-billable breakdown. Accepts `--person` (repeatable), `--level days\|weeks\|months`. |
| `allocations.py` | `allocations.json` | Planned (allocated) hours per person for a date window, with billable and internal breakdown. Accepts `--person` (repeatable), `--level`. |

### People reports

| Script | Output file | Description |
|---|---|---|
| `people.py` | `people.json` | Team member roster with capacity, utilisation targets, department, role, and tags. No date range. |
| `people_financials.py` | `people-financials.json` | Planned, projected, actual, and forecast revenue/cost/margin per person per date period. Comparable to the Parallax Margin Overview report. Accepts `--level`. |

### Project reports

| Script | Output file | Description |
|---|---|---|
| `projects.py` | `projects.json` | All active (or all) projects with financial totals and offerings. No date range. Defaults to active statuses; use `--include-archived` for all. |
| `project_financials.py` | `project-financials-by-{mode}.json` | Project financials broken down by offering (default) or by role per date period. Use `--mode offering\|role`. |
| `clients.py` | `clients.json` | Unique client names with project counts, derived from the projects endpoint. |
| `pipelines.py` | `pipelines.json` | Pipeline stages with associated projects, derived from the projects endpoint. |

### Executive summary

| Script | Output files | Description |
|---|---|---|
| `executive_summary.py` | `parallax-account-{range}.json` + `.md` | Runs time entries, people, and projects in one pass; writes a summary-ready JSON and human-readable Markdown report. Add `--with-allocations` for a logged vs planned comparison. |

### People-side filters

Accepted by `time_entries.py`, `allocations.py`, `people.py`, `people_financials.py`:

```
--people-tag TAG       tag formatted as Category::Value (repeatable)
--department NAME      department name (repeatable)
--role NAME            role name (repeatable)
--worker-type TYPE     FullTime, Contractor, or Placeholder (repeatable)
```

### Project-side filters

Accepted by `projects.py`, `project_financials.py`, `people_financials.py`, `clients.py`, `pipelines.py`:

```
--client NAME          client name (repeatable)
--project-status STATUS  PreSale, AwaitingStart, InProgress, Completed, OnHold (repeatable)
--financial-model MODEL  TimeAndMaterials, FixedBid, Retainer, Internal (repeatable)
--project-tag TAG      project tag (repeatable)
```

---

## Usage examples

### Weekly time summary

```bash
uv run scripts/time_entries.py --days 7 --output-dir ./output
uv run scripts/allocations.py  --days 7 --output-dir ./output
```

### Date range with logged vs allocated comparison

```bash
uv run scripts/executive_summary.py \
  --since 2026-05-01 --until 2026-05-07 \
  --with-allocations \
  --output-dir ./output
```

### People and project financials

```bash
uv run scripts/people_financials.py  --since 2026-05-01 --until 2026-05-31 --output-dir ./output
uv run scripts/project_financials.py --since 2026-05-01 --until 2026-05-31 --output-dir ./output
uv run scripts/project_financials.py --since 2026-05-01 --until 2026-05-31 --mode role --output-dir ./output
```

### Roster and pipeline snapshot

```bash
uv run scripts/people.py    --output-dir ./output
uv run scripts/projects.py  --output-dir ./output
uv run scripts/clients.py   --output-dir ./output
uv run scripts/pipelines.py --output-dir ./output
```

### Scoped to one client

```bash
uv run scripts/project_financials.py \
  --since 2026-05-01 --until 2026-05-31 \
  --client "Acme Corp" \
  --output-dir ./output
```

---

## Running tests

### Unit tests (no credentials needed)

```bash
uv run --with pytest --with requests pytest tests/test_lib.py -v
```

### Integration tests (live API)

```bash
export PARALLAX_API_KEY=...
uv run --with pytest --with requests pytest tests/ -v
```

Integration tests are automatically skipped when credentials are absent — safe to include in CI pipelines.

---

## Output format

Every script writes JSON with a consistent envelope:

```json
{
  "category": "time_entries",
  "range": { "start_date": "2026-05-05", "end_date": "2026-05-11" },
  "generated_at": "2026-05-12T09:00:00Z",
  "counts": { "total_hours": 42.5, "billable_hours": 38.0, ... },
  "items": [ ... ]
}
```

`executive_summary.py` additionally writes a Markdown file at the same path with a `.md` extension.

## API Limits

- Max **10 requests per minute**. The client automatically retries on HTTP 429 with back-off.
- Max **90 days** of data per request (`--days` must be ≤ 90).
- The `/api/projects` endpoint does not accept date parameters — it always returns all-time totals.
