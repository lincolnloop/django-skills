---
name: harvest
description: Aggregate recent timesheet activity from Harvest using their API. Use when the user wants a summary of hours logged, billable vs non-billable time, or an activity breakdown by user, project, or task for a date range.
---

# Harvest Timesheet Aggregator

Collects data from the complete Harvest API v2 into structured JSON using Python scripts. Each script is focused on a single dimension — combine them to build whatever summary you need.

## Scripts

### Time Entry Reports

| Script | What it does |
|--------|-------------|
| `time-entries.py` | Raw time entries with aggregations by user, project, and task. Accepts `--user` (repeatable), `--project` (repeatable), `--client`. |
| `report-team.py` | Hours per team member via the Reports API. Includes billable amounts. Requires Manager/Administrator access. |
| `report-projects.py` | Hours per project via the Reports API. Includes billable amounts. Accepts `--client`. |
| `report-clients.py` | Hours per client via the Reports API. |
| `report-tasks.py` | Hours per task type via the Reports API. |

### Financial & Budget Reports

| Script | What it does |
|--------|-------------|
| `report-expenses.py` | Expense totals broken down by clients, projects, categories, or team. Pass `--breakdown` for one dimension, omit for all four. |
| `report-budget.py` | Budget spent and remaining per project. No date range needed. |
| `report-uninvoiced.py` | Billable hours and expenses not yet invoiced. Default: last 30 days. |

### Account Data

| Script | What it does |
|--------|-------------|
| `company.py` | Fetch account name, currency, week start day, and enabled feature flags. |
| `list-clients.py` | List all clients. Accepts `--is-active` / `--no-is-active`. |
| `list-users.py` | List all users with roles, capacity, and hourly rates. Accepts `--is-active`. |
| `list-projects.py` | List all projects. Accepts `--is-active`, `--client`. |
| `list-tasks.py` | List all task types. Accepts `--is-active`. |
| `list-roles.py` | List all roles and their member user IDs. |
| `list-invoices.py` | List invoices. Accepts `--client`, `--project`, `--state` (draft/open/paid/closed). Default: last 30 days. |
| `list-estimates.py` | List estimates. Accepts `--client`, `--state` (draft/sent/accepted/declined). Default: last 30 days. |
| `list-expenses.py` | List expense entries. Accepts `--user`, `--client`, `--project`, `--is-billed`. |

## Output Schemas

JSON schemas for the script output formats are in `schemas/`. Use them to understand the structure of each script's output before writing code that consumes it.

| Schema | Describes output of |
|--------|-------------------|
| `harvest.time_entries.schema.json` | `time-entries.py` — entries plus `by_user`, `by_project`, `by_task` aggregations |
| `harvest.report_team.schema.json` | `report-team.py` — hours and billable amounts per team member |
| `harvest.report_projects.schema.json` | `report-projects.py` — hours and billable amounts per project |
| `harvest.report_clients.schema.json` | `report-clients.py` — hours and billable amounts per client |
| `harvest.report_tasks.schema.json` | `report-tasks.py` — hours and billable amounts per task type |
| `harvest.report_expenses.schema.json` | `report-expenses.py` — expense totals (four `oneOf` variants: clients, projects, categories, team) |
| `harvest.report_budget.schema.json` | `report-budget.py` — budget spent and remaining per project |
| `harvest.report_uninvoiced.schema.json` | `report-uninvoiced.py` — uninvoiced hours and amounts per project |
| `harvest.users.schema.json` | `list-users.py` — team roster with roles, capacity, and rates |

## Recommended Usage

### Time entries for a date range

```bash
uv run scripts/time-entries.py --since 2026-04-14 --until 2026-04-20 --output-dir ./output
uv run scripts/report-team.py  --since 2026-04-14 --until 2026-04-20 --output-dir ./output
uv run scripts/report-projects.py --since 2026-04-14 --until 2026-04-20 --output-dir ./output
```

### Financial snapshot

```bash
uv run scripts/list-invoices.py --state open --days 365
uv run scripts/report-uninvoiced.py --days 30
uv run scripts/report-budget.py --is-active
```

### Account roster

```bash
uv run scripts/list-clients.py --is-active
uv run scripts/list-users.py --is-active
uv run scripts/list-projects.py --is-active
```

## Output

Every script writes a single JSON file with a consistent envelope:

```json
{
  "category": "time_entries",
  "range": { "start_date": "2026-04-14", "end_date": "2026-04-20" },
  "generated_at": "2026-04-21T09:00:00Z",
  "counts": { "total_hours": 42.5, "billable_hours": 38.0, ... },
  "items": [ ... ]
}
```

## Parameters

All scripts accept:

- `--days N` - Look back N days (default: 7 for time/team/project reports, 30 for invoices/estimates/expenses).
- `--since DATE` - Inclusive start date `YYYY-MM-DD`. Must be used with `--until`.
- `--until DATE` - Inclusive end date `YYYY-MM-DD`. Must be used with `--since`.
- `--output-dir DIR` - Write output to this directory.
- `--prefix PREFIX` - Prepend to output filenames.

`time-entries.py` additionally accepts:

- `--user USER_ID` - Scope to a specific Harvest user ID (repeatable).
- `--project PROJECT_ID` - Scope to a specific Harvest project ID (repeatable).
- `--client CLIENT_ID` - Scope to a specific Harvest client ID.

`report-projects.py` additionally accepts:

- `--client CLIENT_ID` - Filter the project report to a specific client.

Date-only values such as `2026-04-14` are treated as full UTC days.

## Environment Variables

Both tokens are required and must be set before running any script.

| Variable | Description |
|----------|-------------|
| `HARVEST_ACCESS_TOKEN` | Personal access token from https://id.getharvest.com/developers |
| `HARVEST_ACCOUNT_ID` | Account ID from https://id.getharvest.com/developers |

## When to Use

- User asks for a timesheet summary or time report from Harvest
- User wants to know how many hours were logged in a period
- User wants billable vs non-billable breakdown
- User wants to see which projects or team members were most active
- User asks for a daily or weekly digest of time tracking activity
- User wants to list clients, users, projects, tasks, roles, invoices, or estimates
- User asks about uninvoiced work or budget remaining on projects
- User wants expense data or expense reports

## Instructions for Pi

1. Check that `HARVEST_ACCESS_TOKEN` and `HARVEST_ACCOUNT_ID` are available in the environment before running any script.
2. If either token is missing, tell the user to generate a personal access token at https://id.getharvest.com/developers and set both environment variables.
3. If the user names specific people, projects, or clients, look up their Harvest IDs first (or ask the user to provide them) and use the appropriate filter flags.
4. If the user gives explicit dates, prefer `--since` and `--until`. For "last week" or "yesterday", use `--days`.
5. For timesheet summaries, run whichever combination of scripts covers the needed dimensions, then synthesise the results yourself.
6. Explicitly call out when total hours or billable hours are zero.
7. When summarising, note the billable percentage as it indicates utilisation.
8. For deeper investigation into a single dimension (just team, just projects, just clients), use the individual category scripts.
9. For account data (who are the active users? what clients exist?), use the `list-*.py` scripts.
10. For financial data (open invoices, uninvoiced work, budget status), use `list-invoices.py`, `report-uninvoiced.py`, or `report-budget.py`.
