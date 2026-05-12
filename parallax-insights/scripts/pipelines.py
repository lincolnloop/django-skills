#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""Fetch sales pipeline stages from Parallax."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import ParallaxClient, check_api_key, now_utc, write_json


def fetch(
    client: ParallaxClient,
    clients: list[str] | None = None,
    project_status: list[str] | None = None,
    financial_model: list[str] | None = None,
    project_tags: list[str] | None = None,
) -> dict:
    params: dict = {}
    if clients:
        params["clients[]"] = clients
    if project_status:
        params["project_status[]"] = project_status
    if financial_model:
        params["financial_model[]"] = financial_model
    if project_tags:
        params["project_tags[]"] = project_tags

    raw = client.get("/projects", params)
    projects_data = raw.get("data", {}).get("projects", {})

    stages_map: dict[str, dict] = {}
    for project_id, project in projects_data.items():
        stage_name = project.get("stage_name", "")
        if stage_name:
            if stage_name not in stages_map:
                stages_map[stage_name] = {
                    "name": stage_name,
                    "projects_count": 0,
                    "projects": [],
                }
            stages_map[stage_name]["projects_count"] += 1
            stages_map[stage_name]["projects"].append({
                "id": project_id,
                "name": project.get("project_name"),
                "client_name": project.get("client_name"),
                "status": project.get("project_status"),
            })

    items = sorted(stages_map.values(), key=lambda x: x["name"])

    return {
        "category": "pipelines",
        "generated_at": now_utc(),
        "counts": {
            "total": len(items),
        },
        "note": "Pipeline stages extracted from project data in Insights API",
        "items": items,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", dest="clients", action="append", default=[], metavar="NAME",
                        help="Filter by client name (repeatable)")
    parser.add_argument("--project-status", dest="project_status", action="append", default=[],
                        metavar="STATUS",
                        help="Filter by status: PreSale, AwaitingStart, InProgress, Completed, OnHold (repeatable)")
    parser.add_argument("--financial-model", dest="financial_model", action="append", default=[],
                        metavar="MODEL",
                        help="Filter by model: TimeAndMaterials, FixedBid, Retainer, Internal (repeatable)")
    parser.add_argument("--project-tag", dest="project_tags", action="append", default=[],
                        metavar="TAG", help="Filter by project tag (repeatable)")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--prefix", default="", help="Output filename prefix")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = ParallaxClient(check_api_key())
    data = fetch(
        client,
        clients=args.clients or None,
        project_status=args.project_status or None,
        financial_model=args.financial_model or None,
        project_tags=args.project_tags or None,
    )
    write_json(data, os.path.join(output_dir, f"{args.prefix}pipelines.json"))


if __name__ == "__main__":
    main()
