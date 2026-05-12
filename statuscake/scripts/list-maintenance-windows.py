#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List maintenance windows from StatusCake."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statuscake import StatusCakeClient, check_env, now_utc, write_json, base_parser


def fetch(client: StatusCakeClient, state: str = "") -> dict:
    params: dict = {}
    if state:
        params["state"] = state

    windows = client.get_all("/maintenance-windows", **params)
    return {
        "category": "maintenance_windows",
        "generated_at": now_utc(),
        "filters": {"state": state or None},
        "counts": {"total": len(windows)},
        "items": sorted(windows, key=lambda w: w.get("start_at") or ""),
    }


def main():
    parser = base_parser(__doc__)
    parser.add_argument("--state", default="", choices=["active", "paused", "pending"],
                        help="Filter by state: active, paused, or pending")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = StatusCakeClient(check_env())
    data = fetch(client, state=args.state)
    write_json(os.path.join(output_dir, f"{args.prefix}maintenance-windows.json"), data)


if __name__ == "__main__":
    main()
