#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List all projects in Harvest."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, now_utc, write_json


def main() -> None:
    p = argparse.ArgumentParser(description="List all projects in Harvest.")
    p.add_argument("--is-active", action=argparse.BooleanOptionalAction, default=None,
                   help="Filter to active or inactive projects")
    p.add_argument("--client", metavar="CLIENT_ID", default="",
                   help="Filter to a specific client")
    p.add_argument("--output-dir", metavar="DIR", default=".",
                   help="Write output to this directory (default: .)")
    p.add_argument("--prefix", metavar="PREFIX", default="",
                   help="Output filename prefix")
    args = p.parse_args()

    client = HarvestClient()
    params: dict = {}
    if args.is_active is not None:
        params["is_active"] = str(args.is_active).lower()
    if args.client:
        params["client_id"] = args.client

    projects = client.get_all("/projects", "projects", **params)

    output = {
        "category": "projects",
        "generated_at": now_utc(),
        "counts": {
            "total": len(projects),
            "active": sum(1 for p in projects if p.get("is_active")),
        },
        "projects": sorted(projects, key=lambda x: x.get("name", "")),
    }

    write_json(f"{args.output_dir}/{args.prefix}projects-list.json", output)


if __name__ == "__main__":
    main()
