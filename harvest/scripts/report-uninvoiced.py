#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Fetch uninvoiced hours and expenses report from Harvest Reports API."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, resolve_range, date_for_reports, now_utc, write_json, base_parser


def main() -> None:
    p = base_parser(
        "Fetch uninvoiced hours and expenses from the Harvest Reports API."
        " Shows billable work that has not yet been invoiced.",
        default_days=30,
    )
    args = p.parse_args()

    client = HarvestClient()
    start_date, end_date = resolve_range(args.days, args.since, args.until)
    from_d, to_d = date_for_reports(start_date), date_for_reports(end_date)

    results = client.get_all("/reports/uninvoiced", "results",
                             **{"from": from_d, "to": to_d})

    total_uninvoiced = sum(r.get("uninvoiced_amount") or 0 for r in results)
    total_hours = sum(r.get("uninvoiced_hours") or 0 for r in results)

    output = {
        "category": "uninvoiced",
        "since": f"{start_date}T00:00:00Z",
        "until": f"{end_date}T23:59:59Z",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        "counts": {
            "total_projects": len(results),
            "total_uninvoiced_hours": round(total_hours, 4),
            "total_uninvoiced_amount": round(total_uninvoiced, 2),
        },
        "projects": sorted(results, key=lambda x: -(x.get("uninvoiced_amount") or 0)),
    }

    write_json(f"{args.output_dir}/{args.prefix}report-uninvoiced.json", output)


if __name__ == "__main__":
    main()
