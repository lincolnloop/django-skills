#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""
Generate an uptime report from StatusCake — JSON + Markdown.

Collects all uptime checks and writes a summary-ready JSON and a
human-readable Markdown report to the output directory.
"""
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statuscake import StatusCakeClient, check_env, now_utc, write_json, base_parser


def fetch_uptime(client: StatusCakeClient, tag: str = "", status: str = "") -> dict:
    params: dict = {}
    if tag:
        params["tags"] = tag
    if status:
        params["status"] = status

    checks = client.get_all("/uptime", **params)
    active = [c for c in checks if not c.get("paused")]
    up = [c for c in active if c.get("status") == "up"]
    down = [c for c in active if c.get("status") == "down"]
    paused = [c for c in checks if c.get("paused")]

    uptimes = [c["uptime"] for c in active if c.get("uptime") is not None]
    avg_uptime = round(sum(uptimes) / len(uptimes), 1) if uptimes else None

    def summary(c: dict) -> dict:
        return {
            "id": c.get("id"),
            "name": c.get("name"),
            "website_url": c.get("website_url"),
            "test_type": c.get("test_type"),
            "uptime": c.get("uptime"),
            "check_rate": c.get("check_rate"),
            "tags": c.get("tags", []),
        }

    return {
        "category": "uptime_checks",
        "generated_at": now_utc(),
        "filters": {"tag": tag or None, "status": status or None},
        "counts": {
            "total": len(checks),
            "up": len(up),
            "down": len(down),
            "paused": len(paused),
            "avg_uptime_pct": avg_uptime,
        },
        "checks_down": [summary(c) for c in down],
        "checks_up": sorted([summary(c) for c in up], key=lambda x: -(x.get("uptime") or 0)),
        "checks_paused": [summary(c) for c in paused],
    }


def main():
    parser = base_parser(__doc__)
    parser.add_argument("--tag", default="", help="Filter to checks matching this tag")
    parser.add_argument("--status", default="", choices=["up", "down"],
                        help="Filter by current status")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = StatusCakeClient(check_env())

    report_date = date.today().isoformat()
    if args.tag:
        slug = f"tag-{args.tag}"
    elif args.status:
        slug = f"status-{args.status}"
    else:
        slug = "statuscake-account"

    base_name = f"{args.prefix}{slug}-uptime-{report_date}"
    json_path = os.path.join(output_dir, f"{base_name}.json")
    md_path = os.path.join(output_dir, f"{base_name}.md")

    print("=== StatusCake Uptime Report ===")
    print(f"Date: {report_date}")
    print()

    uptime = fetch_uptime(client, tag=args.tag, status=args.status)

    report = {
        "schema_version": "2.0",
        "generated_at": now_utc(),
        "report_date": report_date,
        "target": {
            "slug": slug,
            "tag": args.tag or None,
            "status_filter": args.status or None,
        },
        "summary": uptime["counts"],
        "checks_down": uptime["checks_down"],
        "checks_up": uptime["checks_up"][:20],
        "checks_paused": uptime["checks_paused"],
        "uptime_checks": uptime,
    }

    write_json(json_path, report)

    counts = uptime["counts"]
    lines = [
        "# StatusCake Uptime Report",
        "",
        f"Generated: {report_date}",
        "",
        "## Overview",
        "",
        f"- **Total monitors:** {counts['total']}",
        f"- **Up:** {counts['up']}",
        f"- **Down:** {counts['down']}",
        f"- **Paused:** {counts['paused']}",
        f"- **Average uptime:** {counts['avg_uptime_pct']}%",
        "",
        "## Monitors Down",
        "",
    ]
    if uptime["checks_down"]:
        for c in uptime["checks_down"]:
            lines.append(f"- **{c['name']}** — {c['website_url']} (uptime: {c['uptime']}%)")
    else:
        lines.append("- All active monitors are up.")
    lines += ["", "## Monitors Up", ""]
    if uptime["checks_up"]:
        for c in uptime["checks_up"]:
            lines.append(f"- **{c['name']}** — {c['website_url']} ({c['uptime']}%)")
    else:
        lines.append("- No monitors currently up.")

    Path(md_path).parent.mkdir(parents=True, exist_ok=True)
    Path(md_path).write_text("\n".join(lines) + "\n")
    print(f"  Wrote: {md_path}")
    print()
    print("=== Complete ===")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")


if __name__ == "__main__":
    main()
