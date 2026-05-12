#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""
Fetch project financials from Parallax, broken down by offering or by role per date period.

  --mode offering  (default) — /api/projects/financials/by-offering
  --mode role                — /api/projects/financials/by-role

Comparable to the Revenue Overview and Margin Overview reports in Parallax.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import ParallaxClient, check_api_key, resolve_range, now_utc, write_json


def fetch(
    client: ParallaxClient,
    start_date: str,
    end_date: str,
    mode: str = "offering",
    level: str = "weeks",
    clients: list[str] | None = None,
    project_status: list[str] | None = None,
    financial_model: list[str] | None = None,
    project_tags: list[str] | None = None,
    project_role_tags: list[str] | None = None,
) -> dict:
    endpoint = "/projects/financials/by-offering" if mode == "offering" else "/projects/financials/by-role"

    params: dict = {"start_date": start_date, "end_date": end_date, "level": level}
    if clients:
        params["clients[]"] = clients
    if project_status:
        params["project_status[]"] = project_status
    if financial_model:
        params["financial_model[]"] = financial_model
    if project_tags:
        params["project_tags[]"] = project_tags
    if project_role_tags and mode == "role":
        params["project_role_tags[]"] = project_role_tags

    raw = client.get(endpoint, params)
    projects_data = raw.get("data", {}).get("projects", {})

    items = []
    total_actual_hours = 0.0
    total_actual_revenue = 0.0
    total_planned_hours = 0.0
    total_planned_revenue = 0.0

    for project_id, project in projects_data.items():
        offerings_raw = project.get("offerings", {})
        offerings = []

        if not isinstance(offerings_raw, dict):
            offerings_raw = {}

        for offering_id, offering in offerings_raw.items():
            offering_entry: dict = {
                "id": offering_id,
                "name": offering.get("project_offering_name"),
                "financial_model": offering.get("financial_model"),
                "crm_id": offering.get("project_offering_crm_id") or offering.get("crm_id"),
                "timesheet_id": offering.get("project_offering_timesheet_id") or offering.get("timesheet_id"),
                "totals": offering.get("totals", {}),
                "periods": offering.get("periods", {}),
            }

            if mode == "role":
                roles = []
                for role_id, role in offering.get("project_roles", {}).items():
                    roles.append({
                        "id": role_id,
                        "role": role.get("role"),
                        "department": role.get("department"),
                        "person_name": role.get("person_name"),
                        "email_address": role.get("email_address"),
                        "worker_type": role.get("worker_type"),
                        "bill_rate": role.get("bill_rate"),
                        "periods": role.get("periods", {}),
                    })
                    for period in role.get("periods", {}).values():
                        total_actual_hours += period.get("actual_hours", 0) or 0
                        total_actual_revenue += period.get("actual_revenue", 0) or 0
                        total_planned_hours += period.get("planned_hours", 0) or 0
                        total_planned_revenue += period.get("planned_revenue", 0) or 0
                offering_entry["project_roles"] = roles
            else:
                totals = offering.get("totals", {})
                total_actual_hours += totals.get("actual_hours", 0) or 0
                total_actual_revenue += totals.get("actual_revenue", 0) or 0
                total_planned_hours += totals.get("planned_hours", 0) or 0
                total_planned_revenue += totals.get("planned_revenue", 0) or 0

            offerings.append(offering_entry)

        items.append({
            "id": project_id,
            "name": project.get("project_name"),
            "client_name": project.get("client_name"),
            "start_date": project.get("start_date"),
            "end_date": project.get("end_date"),
            "project_status": project.get("project_status"),
            "project_risk": project.get("project_risk"),
            "stage_name": project.get("stage_name"),
            "tags": project.get("tags", []),
            "target_budget": project.get("target_budget"),
            "target_margin": project.get("target_margin"),
            "crm_id": project.get("crm_id"),
            "custom_external_ids": project.get("custom_external_ids"),
            "project_owner": project.get("project_owner"),
            "sales_owner": project.get("sales_owner"),
            "offerings": offerings,
        })

    return {
        "category": f"project_financials_by_{mode}",
        "mode": mode,
        "since": f"{start_date}T00:00:00Z",
        "until": f"{end_date}T23:59:59Z",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        "counts": {
            "total_projects": len(items),
            "total_actual_hours": round(total_actual_hours, 2),
            "total_actual_revenue": round(total_actual_revenue, 2),
            "total_planned_hours": round(total_planned_hours, 2),
            "total_planned_revenue": round(total_planned_revenue, 2),
        },
        "items": items,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", default="offering", choices=["offering", "role"],
                        help="Breakdown mode: offering (default) or role")
    parser.add_argument("--level", default="weeks", choices=["days", "weeks", "months"],
                        help="Aggregation level (default: weeks)")
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
    parser.add_argument("--project-role-tag", dest="project_role_tags", action="append", default=[],
                        metavar="TAG", help="Filter by project role tag, only applies with --mode role (repeatable)")
    parser.add_argument("--days", type=int, default=7, help="Look back N days (default: 7)")
    parser.add_argument("--since", default="", help="Start date YYYY-MM-DD (use with --until)")
    parser.add_argument("--until", default="", help="End date YYYY-MM-DD (use with --since)")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--prefix", default="", help="Output filename prefix")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = ParallaxClient(check_api_key())
    start_date, end_date, _, _ = resolve_range(args.days, args.since, args.until)
    data = fetch(
        client,
        start_date,
        end_date,
        mode=args.mode,
        level=args.level,
        clients=args.clients or None,
        project_status=args.project_status or None,
        financial_model=args.financial_model or None,
        project_tags=args.project_tags or None,
        project_role_tags=args.project_role_tags or None,
    )
    write_json(data, os.path.join(output_dir, f"{args.prefix}project-financials-by-{args.mode}.json"))


if __name__ == "__main__":
    main()
