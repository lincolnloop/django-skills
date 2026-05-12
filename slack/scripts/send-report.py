#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""
Format a structured report JSON as Slack Block Kit blocks and post it to a channel.

Accepts JSON output from the harvest, parallax-insights, statuscake, and github skills.
The format is auto-detected from the JSON structure when --format is omitted.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from slack import SlackClient, check_env, resolve_channel


# ── format detection ──────────────────────────────────────────────────────────

def detect_format(data: dict) -> str:
    category = data.get("category", "")

    if category in ("time_entries", "report_team", "report_projects",
                    "report_clients", "report_tasks"):
        if "by_user" in data or "by_project" in data or "by_task" in data:
            return "harvest-time"
        if "by_person" in data:
            return "parallax-time"

    if category == "uptime_checks":
        return "statuscake-uptime"

    if category == "people_financials":
        return "parallax-financials"

    if category == "project_financials_by_offering" or category == "project_financials_by_role":
        return "parallax-project-financials"

    # Legacy github executive-summary detection
    if "commits" in data and "summary" in data:
        return "github"

    # Legacy harvest executive-summary
    if "time_entries" in data and "summary" in data:
        return "harvest-legacy"

    raise ValueError(
        f"Cannot auto-detect format from category={category!r}. "
        "Use --format to specify."
    )


# ── block builders ────────────────────────────────────────────────────────────

def _header(text: str) -> dict:
    return {"type": "header", "text": {"type": "plain_text", "text": text, "emoji": False}}


def _context(*texts: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": t} for t in texts]}


def _section(text: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def _divider() -> dict:
    return {"type": "divider"}


def build_harvest_time_blocks(data: dict) -> tuple[list, str]:
    counts = data.get("counts", {})
    total = counts.get("total_hours", 0)
    billable = counts.get("billable_hours", 0)
    non_billable = counts.get("non_billable_hours", 0)
    pct = round(billable / total * 100, 1) if total else 0
    r = data.get("range", {})
    date_range = f"{r.get('start_date', '')} to {r.get('end_date', '')}"

    by_user = sorted(data.get("by_user", []), key=lambda x: -x.get("total_hours", 0))[:10]
    user_lines = "\n".join(
        f"• *{u.get('user', u.get('name', 'unknown'))}:* {u.get('total_hours', 0):.1f}h"
        for u in by_user
    )

    blocks = [
        _header("Harvest Timesheet Summary"),
        _context(date_range),
        _divider(),
        _section(
            f"*{total:.1f}h total*   ·   {billable:.1f}h billable ({pct}%)   ·   "
            f"{non_billable:.1f}h non-billable\n"
            f"{counts.get('active_users', counts.get('active_people', '?'))} users   ·   "
            f"{counts.get('total_entries', '?')} entries"
        ),
    ]
    if user_lines:
        blocks.append(_section(f"*By User*\n{user_lines}"))
    blocks += [_divider(), _context(f"_Generated {data.get('generated_at', '')}_")]

    fallback = f"Harvest Timesheet: {date_range}: {total:.1f}h total ({billable:.1f}h billable, {pct}%)"
    return blocks, fallback


def build_parallax_time_blocks(data: dict) -> tuple[list, str]:
    counts = data.get("counts", {})
    total = counts.get("total_hours", 0)
    billable = counts.get("billable_hours", 0)
    non_billable = counts.get("non_billable_hours", 0)
    pct = round(billable / total * 100, 1) if total else 0
    r = data.get("range", {})
    date_range = f"{r.get('start_date', '')} to {r.get('end_date', '')}"

    by_person = sorted(data.get("by_person", []), key=lambda x: -x.get("total_hours", 0))[:10]
    person_lines = "\n".join(
        f"• *{p.get('name', p.get('person_id', 'unknown'))}:* {p.get('total_hours', 0):.1f}h"
        for p in by_person
    )

    blocks = [
        _header("Parallax Time Summary"),
        _context(date_range),
        _divider(),
        _section(
            f"*{total:.1f}h total*   ·   {billable:.1f}h billable ({pct}%)   ·   "
            f"{non_billable:.1f}h non-billable\n"
            f"{counts.get('active_people', '?')} people"
        ),
    ]
    if person_lines:
        blocks.append(_section(f"*By Person*\n{person_lines}"))
    blocks += [_divider(), _context(f"_Generated {data.get('generated_at', '')}_")]

    fallback = f"Parallax Time Summary: {date_range}: {total:.1f}h total ({billable:.1f}h billable, {pct}%)"
    return blocks, fallback


def build_statuscake_uptime_blocks(data: dict) -> tuple[list, str]:
    counts = data.get("counts", {})
    total = counts.get("total", 0)
    up = counts.get("up", 0)
    down = counts.get("down", 0)
    paused = counts.get("paused", 0)
    avg = counts.get("avg_uptime_pct")

    overview = (
        f"*{total} monitors*   ·   {up} up   ·   {down} down   ·   {paused} paused"
        + (f"   ·   avg *{avg}%*" if avg is not None else "")
    )

    blocks: list = [
        _header("StatusCake Uptime Report"),
        _divider(),
        _section(overview),
    ]

    checks_down = data.get("checks_down", [])
    if checks_down:
        down_lines = "\n".join(
            f"• *{c.get('name', '?')}* — {c.get('website_url', '')} (uptime: {c.get('uptime', '?')}%)"
            for c in checks_down
        )
        blocks.append(_section(f":red_circle: *Monitors Down*\n{down_lines}"))
    else:
        blocks.append(_section(":white_check_mark: All active monitors are up."))

    blocks += [_divider(), _context(f"_Generated {data.get('generated_at', '')}_")]

    status = "all up" if down == 0 else f"{down} down"
    fallback = f"StatusCake: {total} monitors, avg uptime {avg}%, {status}"
    return blocks, fallback


def build_parallax_financials_blocks(data: dict) -> tuple[list, str]:
    counts = data.get("counts", {})
    r = data.get("range", {})
    date_range = f"{r.get('start_date', '')} to {r.get('end_date', '')}"

    total_hours = counts.get("total_actual_hours", 0)
    total_revenue = counts.get("total_actual_revenue", 0)

    top_people = sorted(
        data.get("items", []),
        key=lambda x: -(x.get("totals", {}).get("actual_hours") or 0),
    )[:10]
    person_lines = "\n".join(
        f"• *{p.get('name', '?')}:* {p.get('totals', {}).get('actual_hours', 0):.1f}h  "
        f"${p.get('totals', {}).get('actual_revenue', 0):,.0f}"
        for p in top_people
    )

    blocks = [
        _header("Parallax People Financials"),
        _context(date_range),
        _divider(),
        _section(f"*{total_hours:.1f}h actual*   ·   *${total_revenue:,.0f} revenue*"),
    ]
    if person_lines:
        blocks.append(_section(f"*By Person*\n{person_lines}"))
    blocks += [_divider(), _context(f"_Generated {data.get('generated_at', '')}_")]

    fallback = f"Parallax Financials: {date_range}: {total_hours:.1f}h actual, ${total_revenue:,.0f} revenue"
    return blocks, fallback


def build_github_blocks(data: dict) -> tuple[list, str]:
    summary = data.get("summary", {})
    counts = summary.get("counts", data.get("counts", {}))
    r = data.get("range", {})
    date_range = f"{r.get('start_date', '')} to {r.get('end_date', '')}"
    repos = data.get("target", {}).get("repos", [])

    overview = (
        f"*{counts.get('commits', 0)} commits*   ·   "
        f"{counts.get('prs_opened', 0)} PRs opened   ·   "
        f"{counts.get('prs_merged', 0)} merged   ·   "
        f"{counts.get('issues_opened', 0)} issues"
    )

    blocks: list[Any] = [
        _header("GitHub Activity Summary"),
        _context("  ·  ".join(repos) + "   |   " + date_range if repos else date_range),
        _divider(),
        _section(overview),
    ]

    for repo in summary.get("repos", [])[:8]:
        c = repo.get("counts", {})
        if (c.get("commits", 0) + c.get("prs_opened", 0) + c.get("issues_opened", 0)) == 0:
            continue
        text = f"*{repo.get('repo', '?')}*\n"
        if c.get("commits", 0):
            text += f"• *Commits:* {c['commits']}\n"
        if c.get("prs_opened", 0) + c.get("prs_merged", 0):
            text += f"• *PRs:* {c.get('prs_opened', 0)} opened · {c.get('prs_merged', 0)} merged\n"
        if c.get("issues_opened", 0):
            text += f"• *Issues:* {c.get('issues_opened', 0)} opened\n"
        blocks.append(_section(text.rstrip()))

    blocks += [_divider(), _context(f"_Generated {data.get('generated_at', '')}_")]

    fallback = (
        f"GitHub Activity: {', '.join(repos)} — {date_range}: "
        f"{counts.get('commits', 0)} commits, {counts.get('prs_opened', 0)} PRs"
    )
    return blocks, fallback


def build_harvest_legacy_blocks(data: dict) -> tuple[list, str]:
    """Handle old harvest executive-summary.sh JSON format."""
    summary = data.get("summary", {})
    counts = summary.get("counts", {})
    r = data.get("range", {})
    date_range = f"{r.get('start_date', '')} to {r.get('end_date', '')}"
    total = counts.get("total_hours", 0)
    billable = counts.get("billable_hours", 0)
    pct = counts.get("billable_pct", round(billable / total * 100, 1) if total else 0)

    top_users = summary.get("top_users", [])
    user_lines = "   ·   ".join(
        f"*{u.get('user', '?')}:* {u.get('total_hours', 0)}h"
        for u in top_users
    )

    blocks = [
        _header("Harvest Timesheet Summary"),
        _context(date_range),
        _divider(),
        _section(
            f"*{total}h total*   ·   {billable}h billable ({pct}%)   ·   "
            f"{counts.get('non_billable_hours', 0)}h non-billable"
        ),
    ]
    if user_lines:
        blocks.append(_section(f"*By User*\n{user_lines}"))
    blocks += [_divider(), _context(f"_Generated {data.get('generated_at', '')}_")]

    fallback = f"Harvest Timesheet: {date_range}: {total}h total ({billable}h billable, {pct}%)"
    return blocks, fallback


FORMAT_BUILDERS = {
    "harvest-time": build_harvest_time_blocks,
    "harvest-legacy": build_harvest_legacy_blocks,
    "parallax-time": build_parallax_time_blocks,
    "parallax-financials": build_parallax_financials_blocks,
    "statuscake-uptime": build_statuscake_uptime_blocks,
    "github": build_github_blocks,
}

SUPPORTED_FORMATS = ", ".join(sorted(FORMAT_BUILDERS))


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", required=True,
                        help="Target channel name (e.g. #reports) or ID (e.g. C123ABC456)")
    parser.add_argument("--file", required=True, dest="report_file",
                        help="Path to the report JSON file")
    parser.add_argument(
        "--format", default="", dest="fmt",
        help=f"Report format (auto-detected if omitted). Supported: {SUPPORTED_FORMATS}",
    )
    parser.add_argument("--thread-ts", default="", help="Post as a threaded reply")
    args = parser.parse_args()

    report_path = Path(args.report_file)
    if not report_path.exists():
        print(f"Error: report file not found: {args.report_file}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(report_path.read_text())

    fmt = args.fmt
    if not fmt:
        try:
            fmt = detect_format(data)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    builder = FORMAT_BUILDERS.get(fmt)
    if not builder:
        print(f"Error: unknown format '{fmt}'. Supported: {SUPPORTED_FORMATS}", file=sys.stderr)
        sys.exit(1)

    blocks, fallback = builder(data)

    client = SlackClient(check_env())
    payload: dict = {
        "channel": resolve_channel(args.channel),
        "text": fallback,
        "blocks": blocks,
    }
    if args.thread_ts:
        payload["thread_ts"] = args.thread_ts

    result = client.post("chat.postMessage", **payload)
    print(f"Sent: channel={result['channel']} ts={result['ts']}")


if __name__ == "__main__":
    main()
