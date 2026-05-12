# Slack Skill

A collection of Python scripts for interacting with the [Slack Web API](https://api.slack.com/), designed to be used by AI agents and humans alike. Covers sending messages, posting Block Kit reports, reading channels, and listing workspace members.

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
npx skills add lincoln-loop/agent-skills --skill slack
```

Or install globally so it's available in every project:

```bash
npx skills add lincoln-loop/agent-skills --skill slack --global
```

Interactive mode — choose which agents to target and whether to symlink or copy:

```bash
npx skills add lincoln-loop/agent-skills
```

Non-interactive (CI / scripted):

```bash
npx skills add lincoln-loop/agent-skills --skill slack -a claude-code -y
```

Once installed, Claude Code picks up the skill automatically when you ask about sending messages or reports to Slack.

### Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
- [uv](https://docs.astral.sh/uv/) (for running the scripts — handles Python and dependencies automatically)

---

## Configuration

All scripts read credentials from the environment variable below.

| Variable | Where to find it |
|---|---|
| `SLACK_BOT_TOKEN` | [api.slack.com/apps](https://api.slack.com/apps) → your app → OAuth & Permissions |

Export it in your shell:

```bash
export SLACK_BOT_TOKEN=xoxb-your-token-here
```

### Required OAuth scopes

| Scope | Required by |
|---|---|
| `chat:write` | `send-message.py`, `post-blocks.py`, `send-report.py`, `update-message.py` |
| `channels:read` | `list-channels.py` (public channels) |
| `groups:read` | `list-channels.py` (private channels) |
| `im:read`, `mpim:read` | `list-channels.py` (DMs, when `--types im,mpim`) |
| `users:read`, `users:read.email` | `list-users.py` |
| `channels:history` | `read-channel.py` (public channels) |
| `groups:history` | `read-channel.py` (private channels) |

---

## Scripts reference

All scripts live in `scripts/`. Run any script with `--help` for full usage.

### Sending messages

| Script | Description |
|---|---|
| `send-message.py` | Send a plain text or mrkdwn message to a channel. Accepts `--channel`, `--text` (or `--file`), `--thread-ts`, `--no-unfurl`. |
| `post-blocks.py` | Post a Block Kit message from a JSON blocks file. Accepts `--channel`, `--blocks`, `--text` (fallback), `--thread-ts`. |
| `send-report.py` | Format a report JSON as Block Kit blocks and post it. Auto-detects format from JSON structure. Accepts `--channel`, `--file`, `--format`, `--thread-ts`. |
| `update-message.py` | Update an existing message in place. Requires `--channel` (ID) and `--ts`. Accepts `--text` and/or `--blocks`. |

### Reading workspace data

| Script | Output file | Description |
|---|---|---|
| `list-channels.py` | `channels.json` | All channels in the workspace. Accepts `--types`, `--include-archived`. |
| `list-users.py` | `users.json` | All workspace members. Bots excluded by default; use `--include-bots`. |
| `read-channel.py` | `channel-{id}.json` | Recent messages from a channel. Requires `--channel`. Accepts `--limit`, `--oldest`, `--latest`, `--include-replies`. |

### Supported report formats for `send-report.py`

| Format key | Detected from | Source skill |
|---|---|---|
| `harvest-time` | `category: time_entries` + `by_user` key | harvest |
| `parallax-time` | `category: time_entries` + `by_person` key | parallax-insights |
| `parallax-financials` | `category: people_financials` | parallax-insights |
| `statuscake-uptime` | `category: uptime_checks` | statuscake |
| `github` | `commits` + `summary` keys | github |

Pass `--format <key>` to override auto-detection.

---

## Usage examples

### Send a message

```bash
uv run scripts/send-message.py \
  --channel "#general" \
  --text "Deployment complete. *All systems go.*"
```

### Post a report to a channel

```bash
# From harvest
uv run scripts/send-report.py \
  --channel "#management" \
  --file ./output/time-entries.json

# From StatusCake
uv run scripts/send-report.py \
  --channel "#ops" \
  --file ./output/uptime-checks.json

# From Parallax
uv run scripts/send-report.py \
  --channel "#engineering" \
  --file ./output/time-entries.json
```

### Post as a thread reply

```bash
uv run scripts/send-report.py \
  --channel C123ABC456 \
  --file ./output/report.json \
  --thread-ts 1503435956.000247
```

### Update an existing message

```bash
uv run scripts/update-message.py \
  --channel C123ABC456 \
  --ts 1503435956.000247 \
  --text "Updated: all clear."
```

### Discover channels and users

```bash
uv run scripts/list-channels.py --output-dir ./output
uv run scripts/list-users.py    --output-dir ./output
```

### Read recent channel messages

```bash
uv run scripts/read-channel.py \
  --channel "#general" \
  --limit 20 \
  --output-dir ./output
```

---

## Running tests

### Unit tests (no credentials needed)

```bash
uv run --with pytest --with requests pytest tests/test_lib.py -v
```

### Integration tests (live API — read-only)

```bash
export SLACK_BOT_TOKEN=...
uv run --with pytest --with requests pytest tests/ -v
```

Integration tests only cover read operations (`list-channels.py`, `list-users.py`) and are automatically skipped when credentials are absent.

---

## Output format

Read scripts (`list-channels.py`, `list-users.py`, `read-channel.py`) write JSON with a consistent envelope:

```json
{
  "category": "channels",
  "generated_at": "2026-05-12T09:00:00Z",
  "counts": { "total": 42 },
  "channels": [ ... ]
}
```

Write scripts (`send-message.py`, `post-blocks.py`, `send-report.py`) print to stdout on success:

```
Sent: channel=C123ABC456 ts=1503435956.000247
```

The `ts` value can be passed to `--thread-ts` to post replies, or to `update-message.py --ts` to edit the message.
