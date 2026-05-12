#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List all roles in Harvest."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, now_utc, write_json


def main() -> None:
    p = argparse.ArgumentParser(
        description="List all roles in Harvest, including which users belong to each role."
    )
    p.add_argument("--output-dir", metavar="DIR", default=".",
                   help="Write output to this directory (default: .)")
    p.add_argument("--prefix", metavar="PREFIX", default="",
                   help="Output filename prefix")
    args = p.parse_args()

    client = HarvestClient()
    roles = client.get_all("/roles", "roles")

    output = {
        "category": "roles",
        "generated_at": now_utc(),
        "counts": {"total": len(roles)},
        "roles": sorted(roles, key=lambda x: x.get("name", "")),
    }

    write_json(f"{args.output_dir}/{args.prefix}roles.json", output)


if __name__ == "__main__":
    main()
