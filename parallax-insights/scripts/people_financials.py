#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""
Fetch people financials from Parallax — planned, projected, actual, and forecast
revenue/cost/margin per person per date period.

Comparable to the Margin Overview report in Parallax.
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
    level: str = "weeks",
    departments: list[str] | None = None,
    roles: list[str] | None = None,
    worker_type: list[str] | None = None,
    clients: list[str] | None = None,
    project_status: list[str] | None = None,
    financial_model: list[str] | None = None,
    people_tags: list[str] | None = None,
    project_tags: list[str] | None = None,
) -> dict:
    params: dict = {"start_date": start_date, "end_date": end_date, "level": level}
    if departments:
        params["departments[]"] = departments
    if roles:
        params["roles[]"] = roles
    if worker_type:
        params["worker_type[]"] = worker_type
    if clients:
        params["clients[]"] = clients
    if project_status:
        params["project_status[]"] = project_status
    if financial_model:
        params["financial_model[]"] = financial_model
    if people_tags:
        params["people_tags[]"] = people_tags
    if project_tags:
        params["project_tags[]"] = project_tags

    raw = client.get("/people/financials", params)
    people_data = raw.get("data", {}).get("people", {})

    items = []
    total_actual_hours = 0.0
    total_actual_revenue = 0.0
    total_planned_hours = 0.0
    total_planned_revenue = 0.0

    for person_id, person in people_data.items():
        periods = person.get("periods", {})
        period_totals: dict = {}
        t: dict[str, float] = {k: 0.0 for k in (
            "actual_hours", "actual_revenue", "actual_margin", "actual_cost",
            "planned_hours", "planned_revenue", "planned_margin", "planned_cost",
            "projected_hours", "projected_revenue", "projected_margin", "projected_cost",
            "forecast_hours", "forecast_revenue", "forecast_margin", "forecast_cost",
        )}

        for date, period in sorted(periods.items()):
            period_totals[date] = period
            for key in t:
                t[key] += period.get(key, 0) or 0

        items.append({
            "person_id": person_id,
            "name": f"{person.get('given_name', '')} {person.get('family_name', '')}".strip(),
            "given_name": person.get("given_name"),
            "family_name": person.get("family_name"),
            "email": person.get("email_address"),
            "worker_type": person.get("worker_type"),
            "primary_dept": person.get("primary_dept"),
            "primary_role": person.get("primary_role"),
            "location": person.get("location"),
            "tags": person.get("tags", []),
            "totals": {k: round(v, 2) for k, v in t.items()},
            "periods": period_totals,
        })

        total_actual_hours += t["actual_hours"]
        total_actual_revenue += t["actual_revenue"]
        total_planned_hours += t["planned_hours"]
        total_planned_revenue += t["planned_revenue"]

    items.sort(key=lambda x: -(x["totals"]["actual_hours"] or 0))

    return {
        "category": "people_financials",
        "since": f"{start_date}T00:00:00Z",
        "until": f"{end_date}T23:59:59Z",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        "counts": {
            "total_people": len(items),
            "total_actual_hours": round(total_actual_hours, 2),
            "total_actual_revenue": round(total_actual_revenue, 2),
            "total_planned_hours": round(total_planned_hours, 2),
            "total_planned_revenue": round(total_planned_revenue, 2),
        },
        "items": items,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", default="weeks", choices=["days", "weeks", "months"],
                        help="Aggregation level (default: weeks)")
    parser.add_argument("--department", dest="departments", action="append", default=[],
                        metavar="NAME", help="Filter by department name (repeatable)")
    parser.add_argument("--role", dest="roles", action="append", default=[],
                        metavar="NAME", help="Filter by role name (repeatable)")
    parser.add_argument("--worker-type", dest="worker_type", action="append", default=[],
                        metavar="TYPE",
                        help="Filter by worker type: FullTime, Contractor, Placeholder (repeatable)")
    parser.add_argument("--client", dest="clients", action="append", default=[], metavar="NAME",
                        help="Filter by client name (repeatable)")
    parser.add_argument("--project-status", dest="project_status", action="append", default=[],
                        metavar="STATUS",
                        help="Filter by project status: PreSale, AwaitingStart, InProgress, Completed, OnHold (repeatable)")
    parser.add_argument("--financial-model", dest="financial_model", action="append", default=[],
                        metavar="MODEL",
                        help="Filter by financial model: TimeAndMaterials, FixedBid, Retainer, Internal (repeatable)")
    parser.add_argument("--people-tag", dest="people_tags", action="append", default=[],
                        metavar="TAG", help="Filter by people tag e.g. Location::MN (repeatable)")
    parser.add_argument("--project-tag", dest="project_tags", action="append", default=[],
                        metavar="TAG", help="Filter by project tag (repeatable)")
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
        level=args.level,
        departments=args.departments or None,
        roles=args.roles or None,
        worker_type=args.worker_type or None,
        clients=args.clients or None,
        project_status=args.project_status or None,
        financial_model=args.financial_model or None,
        people_tags=args.people_tags or None,
        project_tags=args.project_tags or None,
    )
    write_json(data, os.path.join(output_dir, f"{args.prefix}people-financials.json"))


if __name__ == "__main__":
    main()
