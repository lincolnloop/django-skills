#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List all heartbeat checks from StatusCake."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statuscake import StatusCakeClient, check_env, now_utc, write_json, base_parser


def fetch(client: StatusCakeClient, status: str = "") -> dict:
    params: dict = {}
    if status:
        params["status"] = status

    checks = client.get_all("/heartbeat", **params)
    active = [c for c in checks if not c.get("paused")]
    up = [c for c in active if c.get("status") == "up"]
    down = [c for c in active if c.get("status") == "down"]
    paused = [c for c in checks if c.get("paused")]

    return {
        "category": "heartbeat_checks",
        "generated_at": now_utc(),
        "filters": {"status": status or None},
        "counts": {
            "total": len(checks),
            "up": len(up),
            "down": len(down),
            "paused": len(paused),
        },
        "items": checks,
    }


def main():
    parser = base_parser(__doc__)
    parser.add_argument("--status", default="", choices=["up", "down"],
                        help="Filter by current status")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = StatusCakeClient(check_env())
    data = fetch(client, status=args.status)
    write_json(os.path.join(output_dir, f"{args.prefix}heartbeat-checks.json"), data)


if __name__ == "__main__":
    main()
