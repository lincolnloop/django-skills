#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""Fetch all clients from Parallax."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import ParallaxClient, check_api_key, now_utc, write_json
from projects import ACTIVE_STATUSES


def fetch(
    client: ParallaxClient,
    include_archived: bool = False,
    project_status: list[str] | None = None,
) -> dict:
    params: dict = {}
    if project_status:
        params["project_status[]"] = project_status
    elif not include_archived:
        params["project_status[]"] = ACTIVE_STATUSES

    raw = client.get("/projects", params)
    projects_data = raw.get("data", {}).get("projects", {})

    clients_map: dict[str, dict] = {}
    for project_id, project in projects_data.items():
        client_name = project.get("client_name", "")
        if client_name and client_name not in clients_map:
            clients_map[client_name] = {
                "name": client_name,
                "projects_count": 0,
            }
        if client_name:
            clients_map[client_name]["projects_count"] += 1

    items = sorted(clients_map.values(), key=lambda x: x["name"])

    return {
        "category": "clients",
        "generated_at": now_utc(),
        "counts": {
            "total": len(items),
        },
        "items": items,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-archived", action="store_true",
                        help="Include clients from all project statuses (default: active projects only)")
    parser.add_argument("--project-status", dest="project_status", action="append", default=[],
                        metavar="STATUS",
                        help="Filter by project status: PreSale, AwaitingStart, InProgress, Completed, OnHold (repeatable)")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--prefix", default="", help="Output filename prefix")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = ParallaxClient(check_api_key())
    data = fetch(
        client,
        args.include_archived,
        project_status=args.project_status or None,
    )
    write_json(data, os.path.join(output_dir, f"{args.prefix}clients.json"))


if __name__ == "__main__":
    main()
