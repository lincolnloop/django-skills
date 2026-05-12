# StatusCake Skill

A collection of Python scripts covering the [StatusCake API v1](https://developers.statuscake.com/api/), designed to be used by AI agents and humans alike. Each script focuses on a single monitoring dimension — combine them to build whatever report you need.

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
npx skills add lincoln-loop/agent-skills --skill statuscake
```

Or install globally so it's available in every project:

```bash
npx skills add lincoln-loop/agent-skills --skill statuscake --global
```

Interactive mode — choose which agents to target and whether to symlink or copy:

```bash
npx skills add lincoln-loop/agent-skills
```

Non-interactive (CI / scripted):

```bash
npx skills add lincoln-loop/agent-skills --skill statuscake -a claude-code -y
```

Once installed, Claude Code picks up the skill automatically when you ask about uptime, SSL, pagespeed, or heartbeat monitoring.

### Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
- [uv](https://docs.astral.sh/uv/) (for running the scripts — handles Python and dependencies automatically)

---

## Configuration

All scripts read credentials from the environment variable below.

| Variable | Where to find it |
|---|---|
| `STATUSCAKE_API_KEY` | [app.statuscake.com/User](https://app.statuscake.com/User) → API Keys |

Export it in your shell:

```bash
export STATUSCAKE_API_KEY=your_api_key_here
```

Or add it to a `.env` file and load with `direnv` / `dotenv`.

---

## Scripts reference

All scripts live in `scripts/`. Run any script with `--help` for full usage.

### Shared parameters

All scripts accept:

| Flag | Description |
|---|---|
| `--output-dir DIR` | Directory for output files (default: `.`) |
| `--prefix PREFIX` | Prepended to every output filename |

### Uptime monitoring

| Script | Output file | Description |
|---|---|---|
| `list-uptime.py` | `uptime-checks.json` | All uptime checks with up/down/paused counts and average uptime %. Accepts `--tag`, `--status up\|down`. |
| `uptime-history.py` | `uptime-history-{id}.json` | Historical check results for a specific monitor. Requires `--test-id`. Accepts `--before`, `--after` (Unix timestamps). |
| `uptime-periods.py` | `uptime-periods-{id}.json` | Downtime periods for a specific monitor. Requires `--test-id`. |
| `uptime-alerts.py` | `uptime-alerts-{id}.json` | Alert history for a specific monitor. Requires `--test-id`. |

### SSL certificate monitoring

| Script | Output file | Description |
|---|---|---|
| `list-ssl.py` | `ssl-checks.json` | All SSL checks with valid/invalid/paused counts. |

### Pagespeed monitoring

| Script | Output file | Description |
|---|---|---|
| `list-pagespeed.py` | `pagespeed-checks.json` | All pagespeed checks with active/paused counts. |
| `pagespeed-history.py` | `pagespeed-history-{id}.json` | Historical results for a specific pagespeed check. Requires `--test-id`. Accepts `--before`, `--after`. |

### Heartbeat monitoring

| Script | Output file | Description |
|---|---|---|
| `list-heartbeat.py` | `heartbeat-checks.json` | All heartbeat checks with up/down/paused counts. Accepts `--status up\|down`. |

### Account configuration

| Script | Output file | Description |
|---|---|---|
| `list-contact-groups.py` | `contact-groups.json` | All alert contact groups with email addresses, integrations, and webhook URLs. |
| `list-maintenance-windows.py` | `maintenance-windows.json` | All maintenance windows. Accepts `--state active\|paused\|pending`. |
| `list-locations.py` | `locations.json` | Probe server locations for both uptime and pagespeed checks. |

### Executive summary

| Script | Output files | Description |
|---|---|---|
| `uptime-report.py` | `{slug}-uptime-{date}.json` + `.md` | Full uptime report — JSON + human-readable Markdown. Accepts `--tag`, `--status`. |

---

## Usage examples

### Full account uptime report

```bash
uv run scripts/uptime-report.py --output-dir ./output
```

### Report filtered to a specific tag

```bash
uv run scripts/uptime-report.py --tag production --output-dir ./output
```

### All monitoring snapshots

```bash
uv run scripts/list-uptime.py        --output-dir ./output
uv run scripts/list-ssl.py           --output-dir ./output
uv run scripts/list-pagespeed.py     --output-dir ./output
uv run scripts/list-heartbeat.py     --output-dir ./output
```

### Drill into a specific monitor

```bash
uv run scripts/uptime-history.py  --test-id 12345 --output-dir ./output
uv run scripts/uptime-periods.py  --test-id 12345 --output-dir ./output
uv run scripts/uptime-alerts.py   --test-id 12345 --output-dir ./output
```

### Account configuration

```bash
uv run scripts/list-contact-groups.py      --output-dir ./output
uv run scripts/list-maintenance-windows.py --output-dir ./output
uv run scripts/list-locations.py           --output-dir ./output
```

---

## Running tests

### Unit tests (no credentials needed)

```bash
uv run --with pytest --with requests pytest tests/test_lib.py -v
```

### Integration tests (live API)

```bash
export STATUSCAKE_API_KEY=...
uv run --with pytest --with requests pytest tests/ -v
```

Integration tests are automatically skipped when credentials are absent — safe to include in CI pipelines.

---

## Output format

Every script writes JSON with a consistent envelope:

```json
{
  "category": "uptime_checks",
  "generated_at": "2026-05-12T09:00:00Z",
  "counts": { "total": 42, "up": 40, "down": 1, "paused": 1, "avg_uptime_pct": 99.8 },
  "checks_down": [ ... ],
  "checks_up": [ ... ],
  "checks_paused": [ ... ]
}
```

`uptime-report.py` additionally writes a Markdown file at the same base path with a `.md` extension.
