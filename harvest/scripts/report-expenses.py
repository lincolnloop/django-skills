#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Fetch expense reports from Harvest Reports API (by client, project, category, or team)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, resolve_range, date_for_reports, now_utc, write_json, base_parser

BREAKDOWNS = ("clients", "projects", "categories", "team")


def main() -> None:
    p = base_parser(
        "Fetch expense reports from the Harvest Reports API."
        " Can be broken down by clients, projects, categories, or team."
        " Defaults to all four breakdowns."
    )
    p.add_argument(
        "--breakdown",
        choices=BREAKDOWNS,
        default=None,
        metavar="DIM",
        help="Breakdown dimension: clients, projects, categories, or team (default: all four)",
    )
    args = p.parse_args()

    client = HarvestClient()
    start_date, end_date = resolve_range(args.days, args.since, args.until)
    from_d, to_d = date_for_reports(start_date), date_for_reports(end_date)

    dimensions = [args.breakdown] if args.breakdown else list(BREAKDOWNS)

    for dim in dimensions:
        results = client.get_all(
            f"/reports/expenses/{dim}", "results", **{"from": from_d, "to": to_d}
        )
        total_amount = sum(r.get("total_amount") or 0 for r in results)
        billable_amount = sum(r.get("billable_amount") or 0 for r in results)

        output = {
            "category": f"expenses_{dim}",
            "since": f"{start_date}T00:00:00Z",
            "until": f"{end_date}T23:59:59Z",
            "range": {"start_date": start_date, "end_date": end_date},
            "generated_at": now_utc(),
            "counts": {
                f"active_{dim}": len(results),
                "total_amount": round(total_amount, 2),
                "billable_amount": round(billable_amount, 2),
            },
            dim: results,
        }

        write_json(f"{args.output_dir}/{args.prefix}report-expenses-{dim}.json", output)


if __name__ == "__main__":
    main()
