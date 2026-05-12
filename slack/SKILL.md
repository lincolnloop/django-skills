---
name: slack
description: Send messages and structured reports to Slack, and read channel or workspace data. Use when the user wants to post a message, share a report from harvest/parallax/statuscake to a channel, update a message, list channels or users, or read recent channel messages.
---

# Slack Publisher & Reader

Sends messages and structured reports to Slack using the Slack Web API, and reads workspace data such as channels, users, and channel history.

## Scripts

### Sending messages

| Script | What it does |
|--------|-------------|
| `send-message.py` | Send a plain text or mrkdwn message to a channel. Accepts `--thread-ts` to post as a reply. |
| `post-blocks.py` | Post an arbitrary Block Kit blocks JSON file to a channel. |
| `send-report.py` | Format a structured report JSON (harvest, parallax, statuscake, github) as Block Kit blocks and post it. Auto-detects format. |
| `update-message.py` | Update an existing message by channel ID and timestamp. |

### Reading workspace data

| Script | What it collects |
|--------|-----------------|
| `list-channels.py` | All channels with ID, name, member count, topic, and purpose. |
| `list-users.py` | All workspace members with ID, name, email, and role flags. Bots excluded by default. |
| `read-channel.py` | Recent messages from a channel. Optionally fetch thread replies too. |

## Output Schemas

JSON schemas for the read-script output formats are in `schemas/`.

| Schema | Describes output of |
|--------|-------------------|
| `slack.channels.schema.json` | `list-channels.py` — channel list with IDs and metadata |
| `slack.users.schema.json` | `list-users.py` — member list with names, emails, and roles |
| `slack.channel_history.schema.json` | `read-channel.py` — message list with reactions and optional replies |

## Recommended Usage

### Post a message

```bash
uv run scripts/send-message.py --channel "#general" --text "Hello, world."
uv run scripts/send-message.py --channel "#ops" --file ./report.md
```

### Post a report from another skill

```bash
# harvest time entries
uv run scripts/send-report.py --channel "#management" --file ./output/time-entries.json

# StatusCake uptime
uv run scripts/send-report.py --channel "#ops" --file ./output/uptime-checks.json

# Parallax time summary
uv run scripts/send-report.py --channel "#engineering" --file ./output/time-entries.json

# Post as a threaded reply
uv run scripts/send-report.py \
  --channel C123ABC456 \
  --file ./output/report.json \
  --thread-ts 1503435956.000247
```

### Discover channels and users

```bash
uv run scripts/list-channels.py --output-dir ./output
uv run scripts/list-users.py    --output-dir ./output
```

### Read channel messages

```bash
uv run scripts/read-channel.py --channel "#general" --limit 20 --output-dir ./output
uv run scripts/read-channel.py --channel C123ABC456 --include-replies --output-dir ./output
```

### Update an existing message

```bash
uv run scripts/update-message.py \
  --channel C123ABC456 \
  --ts 1503435956.000247 \
  --text "Updated: deployment verified."
```

## Parameters

### Common write parameters (`send-message.py`, `post-blocks.py`, `send-report.py`)

- `--channel CHANNEL` — Target channel name (e.g. `#general`) or ID (e.g. `C123ABC456`). Required.
- `--thread-ts TS` — Post as a reply in a thread.

### `send-message.py`

- `--text TEXT` — Message body (mrkdwn supported).
- `--file FILE` — Read message text from a file instead of `--text`.
- `--no-unfurl` — Disable automatic link expansion.

### `post-blocks.py`

- `--blocks FILE` — Path to a JSON file containing a Block Kit blocks array. Required.
- `--text TEXT` — Fallback plain text shown in notifications.

### `send-report.py`

- `--file FILE` — Path to the report JSON from another skill. Required.
- `--format FORMAT` — Override auto-detection: `harvest-time`, `parallax-time`, `parallax-financials`, `statuscake-uptime`, `github`.

### `update-message.py`

- `--channel CHANNEL` — Channel ID containing the message. Required.
- `--ts TS` — Timestamp of the message to update. Required.
- `--text TEXT` — New message text.
- `--blocks FILE` — New blocks JSON file.

### `list-channels.py`

- `--types TYPES` — Comma-separated types: `public_channel`, `private_channel`, `mpim`, `im`. Default: `public_channel,private_channel`.
- `--include-archived` — Include archived channels.
- `--output-dir DIR` — Write `channels.json` here.

### `list-users.py`

- `--include-bots` — Include bot accounts.
- `--output-dir DIR` — Write `users.json` here.

### `read-channel.py`

- `--channel CHANNEL` — Channel name or ID. Required.
- `--limit N` — Number of messages to fetch (default: 50).
- `--oldest TS` — Return messages after this Unix timestamp.
- `--latest TS` — Return messages before this Unix timestamp.
- `--include-replies` — Fetch thread replies for messages that have them.
- `--output-dir DIR` — Write output here.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SLACK_BOT_TOKEN` | Bot token (`xoxb-...`) from https://api.slack.com/apps |

## When to Use

- User asks to send a message or post something to Slack
- User wants to publish a daily report, digest, or summary to a channel
- User wants to share output from harvest, parallax, statuscake, or github with their team
- User wants to post a threaded update to an existing Slack message
- User asks to notify a channel about an event, deployment, or finding
- User wants to list channels or find a channel ID
- User wants to see who is in the workspace
- User wants to read recent messages from a channel

## Instructions for Pi

1. Check that `SLACK_BOT_TOKEN` is available in the environment before running any script.
2. If the token is missing, tell the user to create a Slack app at https://api.slack.com/apps, add the required scopes, and set `SLACK_BOT_TOKEN`.
3. If the user names a channel by name, use `list-channels.py` to find its ID, or accept the name directly — scripts accept both `#channel-name` and `C...` IDs.
4. If the user has a report JSON from another skill (harvest, parallax, statuscake), use `send-report.py`. The format is auto-detected from the JSON structure.
5. For simple messages without a report file, use `send-message.py`. For custom Block Kit layouts, use `post-blocks.py`.
6. Save the `ts` from the response if the user may want to update the message or post follow-up threads.
7. If posting fails with `not_in_channel`, tell the user to invite the bot: `/invite @bot-name` in the target channel.
8. If posting fails with `channel_not_found`, run `list-channels.py` to find the correct channel ID.
9. Use `read-channel.py` when the user wants to catch up on channel activity or summarise recent discussion.
10. Use `list-users.py` when the user needs to look up a user's Slack ID or display name.
