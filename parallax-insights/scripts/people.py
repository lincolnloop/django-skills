#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""Fetch all people (team members) from Parallax."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import ParallaxClient, check_api_key, now_utc, write_json


def fetch(
    client: ParallaxClient,
    people_tags: list[str] | None = None,
    departments: list[str] | None = None,
    roles: list[str] | None = None,
    worker_type: list[str] | None = None,
) -> dict:
    params: dict = {}
    if people_tags:
        params["people_tags[]"] = people_tags
    if departments:
        params["departments[]"] = departments
    if roles:
        params["roles[]"] = roles
    if worker_type:
        params["worker_type[]"] = worker_type

    raw = client.get("/people/utilization", params)
    people_data = raw.get("data", {}).get("people", {})

    items = [
        {
            "id": person_id,
            "name": f"{p.get('given_name', '')} {p.get('family_name', '')}".strip(),
            "first_name": p.get("given_name"),
            "last_name": p.get("family_name"),
            "email": p.get("email_address"),
            "worker_type": p.get("worker_type"),
            "primary_dept": p.get("primary_dept"),
            "primary_role": p.get("primary_role"),
            "cost_rate": p.get("cost_rate"),
            "location": p.get("location"),
            "billable_capacity": p.get("billable_capacity"),
            "target_utilization": p.get("target_utilization"),
            "tags": p.get("tags", []),
        }
        for person_id, p in people_data.items()
    ]

    return {
        "category": "people",
        "generated_at": now_utc(),
        "counts": {
            "total": len(items),
        },
        "items": items,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--people-tag", dest="people_tags", action="append", default=[],
                        metavar="TAG", help="Filter by people tag e.g. Location::MN (repeatable)")
    parser.add_argument("--department", dest="departments", action="append", default=[],
                        metavar="NAME", help="Filter by department name (repeatable)")
    parser.add_argument("--role", dest="roles", action="append", default=[],
                        metavar="NAME", help="Filter by role name (repeatable)")
    parser.add_argument("--worker-type", dest="worker_type", action="append", default=[],
                        metavar="TYPE",
                        help="Filter by worker type: FullTime, Contractor, Placeholder (repeatable)")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--prefix", default="", help="Output filename prefix")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = ParallaxClient(check_api_key())
    data = fetch(
        client,
        people_tags=args.people_tags or None,
        departments=args.departments or None,
        roles=args.roles or None,
        worker_type=args.worker_type or None,
    )
    write_json(data, os.path.join(output_dir, f"{args.prefix}people.json"))


if __name__ == "__main__":
    main()
