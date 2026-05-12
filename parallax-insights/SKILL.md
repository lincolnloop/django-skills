---
name: parallax-insights
description: Aggregate activity from Parallax — a project planning and resource management platform. Use when the user wants a summary of time logged, billable vs non-billable hours, planned allocations, people financials, project financials, or sales pipeline data for a date range.
---

# Parallax Activity Aggregator

Collects time entry, allocation, people, project, financial, client, and pipeline data from the Parallax Insights API into structured JSON and Markdown reports.

## Primary Executive Summary Workflow

For executive-summary style reporting, use `scripts/executive_summary.py`.

This workflow covers:

- total hours logged (billable and non-billable)
- utilisation percentage
- breakdown by person
- optionally: logged vs allocated (planned) comparison with `--with-allocations`

With no scope filter the report covers the whole account. Use `--person` to narrow to specific people.

## Scripts

| Script | Endpoint | What it collects |
|--------|----------|-----------------|
| `executive_summary.py` | multiple | Runs time-entries, people, and projects; enriches with names; writes a summary-ready JSON + Markdown report. Add `--with-allocations` for a logged vs planned comparison. |
| `time_entries.py` | `/api/people/utilization` | Actual hours logged per person per period, with billable and non-billable breakdown. Granularity controlled by `--level`. |
| `allocations.py` | `/api/people/utilization` | Planned hours per person for a date window, with billable and internal breakdown. Granularity controlled by `--level`. |
| `people.py` | `/api/people/utilization` | Team member roster with capacity, utilisation targets, department, role, and tags. |
| `people_financials.py` | `/api/people/financials` | Planned, projected, actual, and forecast revenue/cost/margin per person per date period. Comparable to the Parallax Margin Overview report. |
| `projects.py` | `/api/projects` | All active (or all) projects with totalled financial data and offerings. No date range — returns all-time totals. |
| `project_financials.py` | `/api/projects/financials/by-offering` or `/by-role` | Project financials broken down by offering (default) or by project role per date period. Comparable to the Parallax Revenue and Margin Overview reports. |
| `clients.py` | `/api/projects` | Unique client names with project counts, derived from the projects endpoint. |
| `pipelines.py` | `/api/projects` | Pipeline stages with associated projects, derived from the projects endpoint. |

## Setup

No installation needed. Scripts use [inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/) — `uv` resolves dependencies automatically on first run. See `README.md` for auth setup.

## Recommended Usage

### Via uv (standalone)

```bash
# Weekly executive summary
uv run scripts/executive_summary.py --days 7

# Date range with logged vs allocated comparison
uv run scripts/executive_summary.py --since 2026-05-01 --until 2026-05-07 --with-allocations

# Scoped to specific people
uv run scripts/executive_summary.py --person <uuid> --person <uuid> --days 7

# People financials (revenue/margin) for a period
uv run scripts/people_financials.py --since 2026-05-01 --until 2026-05-07

# Project financials broken down by offering
uv run scripts/project_financials.py --since 2026-05-01 --until 2026-05-07

# Project financials broken down by role
uv run scripts/project_financials.py --since 2026-05-01 --until 2026-05-07 --mode role

# Raw category reports
uv run scripts/time_entries.py   --since 2026-05-01 --until 2026-05-07 --output-dir ./output
uv run scripts/allocations.py   --since 2026-05-01 --until 2026-05-07 --output-dir ./output
uv run scripts/projects.py      --output-dir ./output
uv run scripts/pipelines.py     --output-dir ./output
```

## Parameters

### Common date/range flags (all scripts except `projects.py`, `clients.py`, `pipelines.py`)

- `--days N` — Look back N days (default: 7; max: 90).
- `--since DATE` / `--until DATE` — Explicit date range `YYYY-MM-DD`. Must be used together.
- `--output-dir DIR` — Write output to this directory.

### Aggregation level (`time_entries.py`, `allocations.py`, `people_financials.py`, `project_financials.py`)

- `--level days|weeks|months` — Controls the granularity of date periods returned by the API.
  - `time_entries.py` and `allocations.py` default to `days` for maximum granularity.
  - `people_financials.py` and `project_financials.py` default to `weeks`.

### People-side filters (`time_entries.py`, `allocations.py`, `people.py`, `people_financials.py`)

- `--people-tag TAG` — Filter by people tag, e.g. `Location::MN` (repeatable).
- `--department NAME` — Filter by department name (repeatable).
- `--role NAME` — Filter by role name (repeatable).
- `--worker-type TYPE` — Filter by `FullTime`, `Contractor`, or `Placeholder` (repeatable).

### Project-side filters (`projects.py`, `project_financials.py`, `people_financials.py`, `clients.py`, `pipelines.py`)

- `--client NAME` — Filter by client name (repeatable).
- `--project-status STATUS` — Filter by `PreSale`, `AwaitingStart`, `InProgress`, `Completed`, or `OnHold` (repeatable). `projects.py` defaults to active statuses only; use `--include-archived` to get all.
- `--financial-model MODEL` — Filter by `TimeAndMaterials`, `FixedBid`, `Retainer`, or `Internal` (repeatable).
- `--project-tag TAG` — Filter by project tag (repeatable).

### `executive_summary.py` specific

- `--person UUID` — Scope to a specific person (repeatable).
- `--with-allocations` — Collect planned hours and include logged vs allocated comparison.

### `project_financials.py` specific

- `--mode offering|role` — Break down by project offering (default) or by project role.
- `--project-role-tag TAG` — Filter by project role tag when using `--mode role` (repeatable).

## Output

`executive_summary.py` writes both:

- JSON: machine-readable merged summary with enriched names
- Markdown: human-readable executive-summary draft

```text
output/
  parallax-account-2026-05-01_to_2026-05-07.json
  parallax-account-2026-05-01_to_2026-05-07.md
```

Individual scripts write a single JSON file each (e.g. `time-entries.json`, `people-financials.json`, `project-financials-by-offering.json`).

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PARALLAX_API_KEY` | API key from https://app.getparallax.com/settings/api |

## When to Use

- User asks for a time summary or utilisation report from Parallax
- User wants to know how many hours were logged in a period
- User wants billable vs non-billable breakdown
- User wants to see which projects or team members were most active
- User asks for a daily or weekly digest of time tracking activity from Parallax
- User wants an executive summary of time spent across the portfolio
- User wants to see how many hours a person is planned/allocated
- User wants a logged vs allocated comparison (utilisation against plan)
- User wants to know if someone is over- or under-allocated relative to what was planned
- User wants revenue, cost, or margin data per person or per project
- User wants to see project financial health broken down by offering or role

## Instructions for Pi

1. Check that `PARALLAX_API_KEY` is available in the environment before running any script.
2. If the token is missing, tell the user to generate an API key at https://app.getparallax.com/settings/api and set the `PARALLAX_API_KEY` environment variable.
3. Prefer `parallax-insights` for registry-managed execution. Use `uv run scripts/<name>.py` for individual sub-reports or debugging.
4. If the user gives explicit dates, prefer `--since` and `--until`. For "last week" or "yesterday", use `--days`.
5. For general time and utilisation summaries, run `scripts/executive_summary.py`.
6. For revenue, cost, or margin questions, use `scripts/people_financials.py` (per person) or `scripts/project_financials.py` (per project). Use `--mode role` on the latter when the user wants a breakdown by individual assigned team members.
7. Read the generated Markdown report and write a concise executive summary.
8. Explicitly call out when total hours or billable hours are zero.
9. Note the billable percentage as it indicates utilisation.
10. For deeper investigation into a single dimension (just projects, just pipelines, just people), use the individual category scripts.
11. When the user asks about planned, allocated, or assigned hours, use `allocations.py` or `executive_summary.py --with-allocations`.
12. When reporting logged vs allocated, highlight people where logged hours are significantly below allocated (under-utilised) or above (over-run).
13. Use `--level days` for daily granularity when the user wants to see activity day by day. The API defaults to weekly aggregation — daily is the better choice for short ranges (≤14 days).
14. Use filter flags (`--client`, `--department`, `--project-status`, etc.) to narrow scope when the user asks about a specific client, team, or project type rather than the whole account.
