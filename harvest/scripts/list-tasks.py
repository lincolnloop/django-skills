#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List all tasks in Harvest."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, now_utc, write_json


def main() -> None:
    p = argparse.ArgumentParser(description="List all tasks in Harvest.")
    p.add_argument("--is-active", action=argparse.BooleanOptionalAction, default=None,
                   help="Filter to active or inactive tasks")
    p.add_argument("--output-dir", metavar="DIR", default=".",
                   help="Write output to this directory (default: .)")
    p.add_argument("--prefix", metavar="PREFIX", default="",
                   help="Output filename prefix")
    args = p.parse_args()

    client = HarvestClient()
    params: dict = {}
    if args.is_active is not None:
        params["is_active"] = str(args.is_active).lower()

    tasks = client.get_all("/tasks", "tasks", **params)

    output = {
        "category": "tasks",
        "generated_at": now_utc(),
        "counts": {
            "total": len(tasks),
            "active": sum(1 for t in tasks if t.get("is_active")),
        },
        "tasks": sorted(tasks, key=lambda x: x.get("name", "")),
    }

    write_json(f"{args.output_dir}/{args.prefix}tasks.json", output)


if __name__ == "__main__":
    main()
