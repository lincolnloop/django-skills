#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Fetch time-by-project report from Harvest Reports API."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, resolve_range, date_for_reports, now_utc, write_json, base_parser


def main() -> None:
    p = base_parser(
        "Fetch time by project from the Harvest Reports API."
        " Requires Administrator or Manager access."
    )
    p.add_argument("--client", metavar="CLIENT_ID", default="",
                   help="Filter to a specific client")
    args = p.parse_args()

    client = HarvestClient()
    start_date, end_date = resolve_range(args.days, args.since, args.until)
    from_d, to_d = date_for_reports(start_date), date_for_reports(end_date)

    params: dict = {"from": from_d, "to": to_d}
    if args.client:
        params["client_id"] = args.client

    results = client.get_all("/reports/time/projects", "results", **params)

    total_hours = sum(r.get("total_hours") or 0 for r in results)
    billable_hours = sum(r.get("billable_hours") or 0 for r in results)

    output = {
        "category": "projects",
        "since": f"{start_date}T00:00:00Z",
        "until": f"{end_date}T23:59:59Z",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        "counts": {
            "active_projects": len(results),
            "total_hours": round(total_hours, 4),
            "billable_hours": round(billable_hours, 4),
        },
        "projects": sorted(
            [
                {
                    "project_id": r.get("project_id"),
                    "project_name": r.get("project_name"),
                    "client_id": r.get("client_id"),
                    "client_name": r.get("client_name"),
                    "total_hours": r.get("total_hours"),
                    "billable_hours": r.get("billable_hours"),
                    "billable_amount": r.get("billable_amount"),
                    "currency": r.get("currency"),
                }
                for r in results
            ],
            key=lambda x: -(x["total_hours"] or 0),
        ),
    }

    write_json(f"{args.output_dir}/{args.prefix}projects.json", output)


if __name__ == "__main__":
    main()
