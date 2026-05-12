---
name: statuscake
description: Fetch monitoring data from StatusCake. Use when the user wants a summary of website uptime, SSL certificate status, pagespeed results, heartbeat checks, or which monitors are currently down.
---

# StatusCake Monitor Reporter

Collects monitoring data from the StatusCake API v1 into structured JSON using Python scripts. Each script is focused on a single monitoring dimension — combine them to build whatever summary you need.

## Scripts

### Uptime Monitoring

| Script | What it does |
|--------|-------------|
| `list-uptime.py` | All uptime checks with up/down/paused counts and average uptime %. Accepts `--tag`, `--status up\|down`. |
| `uptime-history.py` | Historical check results for a specific monitor. Requires `--test-id`. |
| `uptime-periods.py` | Downtime periods for a specific monitor. Requires `--test-id`. |
| `uptime-alerts.py` | Alert history for a specific monitor. Requires `--test-id`. |

### SSL Certificate Monitoring

| Script | What it does |
|--------|-------------|
| `list-ssl.py` | All SSL checks with valid/invalid/paused counts and expiry info. |

### Pagespeed Monitoring

| Script | What it does |
|--------|-------------|
| `list-pagespeed.py` | All pagespeed checks with active/paused counts. |
| `pagespeed-history.py` | Historical results for a specific pagespeed check. Requires `--test-id`. |

### Heartbeat Monitoring

| Script | What it does |
|--------|-------------|
| `list-heartbeat.py` | All heartbeat checks with up/down/paused counts. Accepts `--status up\|down`. |

### Account Configuration

| Script | What it does |
|--------|-------------|
| `list-contact-groups.py` | All alert contact groups with emails, integrations, and webhook URLs. |
| `list-maintenance-windows.py` | All maintenance windows. Accepts `--state active\|paused\|pending`. |
| `list-locations.py` | Probe server locations for both uptime and pagespeed checks. |

### Reports

| Script | What it does |
|--------|-------------|
| `uptime-report.py` | Full uptime report — collects all uptime checks and writes JSON + Markdown. Accepts `--tag`, `--status`. |

## Output Schemas

JSON schemas for the script output formats are in `schemas/`.

| Schema | Describes output of |
|--------|-------------------|
| `statuscake.uptime_checks.schema.json` | `list-uptime.py` — checks split by status with counts and avg uptime |
| `statuscake.ssl_checks.schema.json` | `list-ssl.py` — SSL checks with validity status and expiry info |
| `statuscake.pagespeed_checks.schema.json` | `list-pagespeed.py` — pagespeed checks with region and alert thresholds |
| `statuscake.heartbeat_checks.schema.json` | `list-heartbeat.py` — heartbeat checks with period and status |
| `statuscake.maintenance_windows.schema.json` | `list-maintenance-windows.py` — maintenance windows with schedule and affected checks |
| `statuscake.locations.schema.json` | `list-locations.py` — uptime and pagespeed probe locations |

## Recommended Usage

### Full uptime report

```bash
uv run scripts/uptime-report.py --output-dir ./output
uv run scripts/uptime-report.py --tag production --output-dir ./output
```

### All monitor types

```bash
uv run scripts/list-uptime.py        --output-dir ./output
uv run scripts/list-ssl.py           --output-dir ./output
uv run scripts/list-pagespeed.py     --output-dir ./output
uv run scripts/list-heartbeat.py     --output-dir ./output
```

### Drill into a specific monitor

```bash
uv run scripts/uptime-history.py --test-id 12345 --output-dir ./output
uv run scripts/uptime-periods.py --test-id 12345 --output-dir ./output
uv run scripts/uptime-alerts.py  --test-id 12345 --output-dir ./output
```

### Account configuration

```bash
uv run scripts/list-contact-groups.py
uv run scripts/list-maintenance-windows.py --state pending
uv run scripts/list-locations.py
```

## Parameters

All scripts accept:

- `--output-dir DIR` — Write output to this directory.
- `--prefix PREFIX` — Prepend to output filenames.

`list-uptime.py` and `uptime-report.py` additionally accept:

- `--tag TAG` — Filter to monitors with this tag.
- `--status up|down` — Filter by current status.

`list-heartbeat.py` additionally accepts:

- `--status up|down` — Filter by current status.

`list-maintenance-windows.py` additionally accepts:

- `--state active|paused|pending` — Filter by window state.

`uptime-history.py`, `uptime-periods.py`, `uptime-alerts.py`, `pagespeed-history.py` require:

- `--test-id ID` — The monitor ID to fetch detail for.
- `--before TIMESTAMP` — Return results before this Unix timestamp (optional).
- `--after TIMESTAMP` — Return results after this Unix timestamp (optional).

## Environment Variables

| Variable | Description |
|----------|-------------|
| `STATUSCAKE_API_KEY` | API key from https://app.statuscake.com/User |

## When to Use

- User asks for an uptime report or availability summary from StatusCake
- User wants to know which websites are currently down
- User wants to see overall uptime percentages across monitored sites
- User asks for a status check on a group of sites (filtered by tag)
- User wants to know how many monitors are paused
- User asks about SSL certificate expiry or validity
- User wants to see pagespeed check results
- User asks about heartbeat monitor status
- User wants to review contact groups or maintenance windows
- User wants to drill into history or downtime periods for a specific monitor

## Instructions for Pi

1. Check that `STATUSCAKE_API_KEY` is available in the environment before running any script.
2. If the key is missing, tell the user to generate an API key at https://app.statuscake.com/User and set the `STATUSCAKE_API_KEY` environment variable.
3. For a general uptime overview, run `scripts/uptime-report.py`. It writes both JSON and a human-readable Markdown report.
4. If the user names a specific group of sites, use `--tag` to filter by that group's tag.
5. Read the generated Markdown report and write a concise uptime summary.
6. Always highlight monitors that are currently down — these are the most actionable items.
7. Note the average uptime percentage and call out if it is below 99%.
8. Mention the count of paused monitors so the user is aware of gaps in coverage.
9. For SSL checks, call out any certificates with status other than VALID, especially those expiring soon.
10. For heartbeat checks, treat "down" the same as a failed uptime check — something stopped sending pings.
11. When the user asks about a specific monitor's history or downtime, use `uptime-history.py` or `uptime-periods.py` with the monitor's ID.
12. Use `list-maintenance-windows.py --state active` to check if a current outage is expected (inside a maintenance window).
