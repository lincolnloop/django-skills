#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List all uptime checks from StatusCake with status aggregations."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statuscake import StatusCakeClient, check_env, now_utc, write_json, base_parser


def fetch(
    client: StatusCakeClient,
    tag: str = "",
    status: str = "",
) -> dict:
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
        "filters": {
            "tag": tag or None,
            "status": status or None,
        },
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
    data = fetch(client, tag=args.tag, status=args.status)
    write_json(os.path.join(output_dir, f"{args.prefix}uptime-checks.json"), data)


if __name__ == "__main__":
    main()
