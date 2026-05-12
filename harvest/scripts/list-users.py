#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List all users in Harvest."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, now_utc, write_json


def main() -> None:
    p = argparse.ArgumentParser(description="List all users in Harvest.")
    p.add_argument("--is-active", action=argparse.BooleanOptionalAction, default=None,
                   help="Filter to active or inactive users")
    p.add_argument("--output-dir", metavar="DIR", default=".",
                   help="Write output to this directory (default: .)")
    p.add_argument("--prefix", metavar="PREFIX", default="",
                   help="Output filename prefix")
    args = p.parse_args()

    client = HarvestClient()
    params: dict = {}
    if args.is_active is not None:
        params["is_active"] = str(args.is_active).lower()

    users = client.get_all("/users", "users", **params)

    output = {
        "category": "users",
        "generated_at": now_utc(),
        "counts": {
            "total": len(users),
            "active": sum(1 for u in users if u.get("is_active")),
            "contractors": sum(1 for u in users if u.get("is_contractor")),
        },
        "users": sorted(
            [
                {
                    "id": u["id"],
                    "first_name": u.get("first_name"),
                    "last_name": u.get("last_name"),
                    "email": u.get("email"),
                    "is_active": u.get("is_active"),
                    "is_contractor": u.get("is_contractor"),
                    "timezone": u.get("timezone"),
                    "weekly_capacity": u.get("weekly_capacity"),
                    "default_hourly_rate": u.get("default_hourly_rate"),
                    "roles": u.get("roles", []),
                    "created_at": u.get("created_at"),
                    "updated_at": u.get("updated_at"),
                }
                for u in users
            ],
            key=lambda x: (x.get("last_name") or "", x.get("first_name") or ""),
        ),
    }

    write_json(f"{args.output_dir}/{args.prefix}users.json", output)


if __name__ == "__main__":
    main()
