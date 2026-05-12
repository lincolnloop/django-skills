#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Fetch time-by-task report from Harvest Reports API."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, resolve_range, date_for_reports, now_utc, write_json, base_parser


def main() -> None:
    p = base_parser("Fetch time by task from the Harvest Reports API.")
    args = p.parse_args()

    client = HarvestClient()
    start_date, end_date = resolve_range(args.days, args.since, args.until)
    from_d, to_d = date_for_reports(start_date), date_for_reports(end_date)

    results = client.get_all("/reports/time/tasks", "results",
                             **{"from": from_d, "to": to_d})

    total_hours = sum(r.get("total_hours") or 0 for r in results)
    billable_hours = sum(r.get("billable_hours") or 0 for r in results)

    output = {
        "category": "tasks",
        "since": f"{start_date}T00:00:00Z",
        "until": f"{end_date}T23:59:59Z",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        "counts": {
            "active_tasks": len(results),
            "total_hours": round(total_hours, 4),
            "billable_hours": round(billable_hours, 4),
        },
        "tasks": sorted(
            [
                {
                    "task_id": r.get("task_id"),
                    "task_name": r.get("task_name"),
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

    write_json(f"{args.output_dir}/{args.prefix}report-tasks.json", output)


if __name__ == "__main__":
    main()
