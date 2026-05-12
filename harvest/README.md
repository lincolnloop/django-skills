# Harvest Skill

A collection of Python scripts that cover the complete [Harvest API v2](https://help.getharvest.com/api-v2/), designed to be used by AI agents and humans alike. Each script is focused on a single API dimension — combine them to build whatever summary you need.

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
npx skills add lincoln-loop/agent-skills --skill harvest
```

Or install globally so it's available in every project:

```bash
npx skills add lincoln-loop/agent-skills --skill harvest --global
```

Interactive mode — choose which agents to target and whether to symlink or copy:

```bash
npx skills add lincoln-loop/agent-skills
```

Non-interactive (CI / scripted):

```bash
npx skills add lincoln-loop/agent-skills --skill harvest -a claude-code -y
```

Once installed, Claude Code picks up the skill automatically when you ask about Harvest timesheets, hours, or reports.

### Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
- [uv](https://docs.astral.sh/uv/) (for running the scripts — handles Python and dependencies automatically)

---

## Configuration

All scripts read credentials from environment variables. Both are required.

| Variable | Where to find it |
|---|---|
| `HARVEST_ACCESS_TOKEN` | [id.getharvest.com/developers](https://id.getharvest.com/developers) → Personal Access Tokens |
| `HARVEST_ACCOUNT_ID` | Same page, shown next to each token |

Export them in your shell:

```bash
export HARVEST_ACCESS_TOKEN=your_token_here
export HARVEST_ACCOUNT_ID=your_account_id_here
```

Or add them to a `.env` file and load with `direnv` / `dotenv`.

---

## Scripts reference

All scripts live in `scripts/`. Run any script with `--help` for full usage.

### Shared parameters

Most scripts accept:

| Flag | Description |
|---|---|
| `--days N` | Look back N days from today |
| `--since DATE` | Start date `YYYY-MM-DD` (must pair with `--until`) |
| `--until DATE` | End date `YYYY-MM-DD` (must pair with `--since`) |
| `--output-dir DIR` | Directory for output files (default: `.`) |
| `--prefix PREFIX` | Prepended to every output filename |

### Time entry reports

| Script | Output file | Description |
|---|---|---|
| `time-entries.py` | `time-entries.json` | Raw time entries with aggregations by user, project, and task. Accepts `--user` (repeatable), `--project` (repeatable), `--client`. |
| `report-team.py` | `team.json` | Hours per team member from the Reports API. Includes billable amounts. Requires Manager/Administrator access. |
| `report-projects.py` | `projects.json` | Hours per project from the Reports API. Includes billable amounts. Accepts `--client`. |
| `report-clients.py` | `report-clients.json` | Hours per client from the Reports API. |
| `report-tasks.py` | `report-tasks.json` | Hours per task type from the Reports API. |

### Financial reports

| Script | Output file | Description |
|---|---|---|
| `report-expenses.py` | `report-expenses-{dim}.json` | Expense totals broken down by `clients`, `projects`, `categories`, or `team`. Pass `--breakdown <dim>` for one, or omit for all four. |
| `report-budget.py` | `report-budget.json` | Budget spent and remaining per project. No date range needed. Accepts `--is-active` / `--no-is-active`. |
| `report-uninvoiced.py` | `report-uninvoiced.json` | Billable hours and expenses not yet invoiced. Default: last 30 days. |

### Account data

| Script | Output file | Description |
|---|---|---|
| `company.py` | `company.json` | Account name, currency, week start day, and feature flags. |
| `list-clients.py` | `clients.json` | All clients. Accepts `--is-active` / `--no-is-active`. |
| `list-users.py` | `users.json` | All users with roles, capacity, and rates. Accepts `--is-active`. |
| `list-projects.py` | `projects-list.json` | All projects. Accepts `--is-active`, `--client`. |
| `list-tasks.py` | `tasks.json` | All task types. Accepts `--is-active`. |
| `list-roles.py` | `roles.json` | All roles and their member user IDs. |
| `list-invoices.py` | `invoices.json` | Invoices for a date range. Accepts `--client`, `--project`, `--state` (draft/open/paid/closed). Default: last 30 days. |
| `list-estimates.py` | `estimates.json` | Estimates for a date range. Accepts `--client`, `--state` (draft/sent/accepted/declined). Default: last 30 days. |
| `list-expenses.py` | `expenses.json` | Expense entries for a date range. Accepts `--user`, `--client`, `--project`, `--is-billed`. |

---

## Usage examples

### Time entries for a date range

```bash
uv run scripts/time-entries.py --since 2026-04-14 --until 2026-04-20 --output-dir ./output
uv run scripts/report-team.py  --since 2026-04-14 --until 2026-04-20 --output-dir ./output
uv run scripts/report-projects.py --since 2026-04-14 --until 2026-04-20 --output-dir ./output
```

### Team utilisation for last week

```bash
uv run scripts/report-team.py --days 7 --output-dir ./output
```

### All open invoices

```bash
uv run scripts/list-invoices.py --state open --days 365
```

### Unbilled expenses this month

```bash
uv run scripts/list-expenses.py \
  --no-is-billed \
  --since 2026-05-01 \
  --until 2026-05-31
```

### Budget status across all active projects

```bash
uv run scripts/report-budget.py --is-active
```

### What hasn't been invoiced yet (last 60 days)

```bash
uv run scripts/report-uninvoiced.py --days 60
```

### Full account snapshot

```bash
uv run scripts/company.py
uv run scripts/list-clients.py --is-active
uv run scripts/list-users.py --is-active
uv run scripts/list-projects.py --is-active
```

---

## Running tests

### Unit tests (no credentials needed)

```bash
uv run --with pytest --with requests pytest tests/test_lib.py -v
```

### Integration tests (live API)

```bash
export HARVEST_ACCESS_TOKEN=...
export HARVEST_ACCOUNT_ID=...
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
