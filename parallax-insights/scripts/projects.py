#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""Fetch all projects from Parallax."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import ParallaxClient, check_api_key, now_utc, write_json

ACTIVE_STATUSES = ["PreSale", "AwaitingStart", "InProgress"]


def fetch(
    client: ParallaxClient,
    include_archived: bool = False,
    clients: list[str] | None = None,
    project_status: list[str] | None = None,
    financial_model: list[str] | None = None,
    project_tags: list[str] | None = None,
) -> dict:
    params: dict = {}
    if clients:
        params["clients[]"] = clients
    if financial_model:
        params["financial_model[]"] = financial_model
    if project_tags:
        params["project_tags[]"] = project_tags

    if project_status:
        params["project_status[]"] = project_status
    elif not include_archived:
        params["project_status[]"] = ACTIVE_STATUSES

    raw = client.get("/projects", params)
    projects_data = raw.get("data", {}).get("projects", {})

    items = []
    for project_id, p in projects_data.items():
        items.append({
            "id": project_id,
            "name": p.get("project_name"),
            "client_name": p.get("client_name"),
            "start_date": p.get("start_date"),
            "end_date": p.get("end_date"),
            "project_status": p.get("project_status"),
            "project_risk": p.get("project_risk"),
            "stage_name": p.get("stage_name"),
            "tags": p.get("tags", []),
            "target_budget": p.get("target_budget"),
            "target_margin": p.get("target_margin"),
            "crm_id": p.get("crm_id"),
            "custom_external_ids": p.get("custom_external_ids"),
            "project_owner": p.get("project_owner"),
            "sales_owner": p.get("sales_owner"),
            "offerings": p.get("offerings", {}),
        })

    return {
        "category": "projects",
        "generated_at": now_utc(),
        "counts": {
            "total": len(items),
        },
        "items": items,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-archived", action="store_true",
                        help="Include all project statuses (default: active only)")
    parser.add_argument("--client", dest="clients", action="append", default=[], metavar="NAME",
                        help="Filter by client name (repeatable)")
    parser.add_argument("--project-status", dest="project_status", action="append", default=[],
                        metavar="STATUS",
                        help="Filter by status: PreSale, AwaitingStart, InProgress, Completed, OnHold (repeatable)")
    parser.add_argument("--financial-model", dest="financial_model", action="append", default=[],
                        metavar="MODEL",
                        help="Filter by model: TimeAndMaterials, FixedBid, Retainer, Internal (repeatable)")
    parser.add_argument("--project-tag", dest="project_tags", action="append", default=[],
                        metavar="TAG", help="Filter by project tag e.g. Category::Value (repeatable)")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--prefix", default="", help="Output filename prefix")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = ParallaxClient(check_api_key())
    data = fetch(
        client,
        args.include_archived,
        clients=args.clients or None,
        project_status=args.project_status or None,
        financial_model=args.financial_model or None,
        project_tags=args.project_tags or None,
    )
    write_json(data, os.path.join(output_dir, f"{args.prefix}projects.json"))


if __name__ == "__main__":
    main()
