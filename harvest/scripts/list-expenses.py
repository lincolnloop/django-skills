#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List raw expense entries from Harvest."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, resolve_range, now_utc, write_json, base_parser


def main() -> None:
    p = base_parser("List expense entries from Harvest.")
    p.add_argument("--user", metavar="USER_ID", default="",
                   help="Filter to a specific user")
    p.add_argument("--client", metavar="CLIENT_ID", default="",
                   help="Filter to a specific client")
    p.add_argument("--project", metavar="PROJECT_ID", default="",
                   help="Filter to a specific project")
    p.add_argument("--is-billed", action=argparse.BooleanOptionalAction, default=None,
                   help="Filter to billed or unbilled expenses")
    args = p.parse_args()

    client = HarvestClient()
    start_date, end_date = resolve_range(args.days, args.since, args.until)

    params: dict = {"from": start_date, "to": end_date}
    if args.user:
        params["user_id"] = args.user
    if args.client:
        params["client_id"] = args.client
    if args.project:
        params["project_id"] = args.project
    if args.is_billed is not None:
        params["is_billed"] = str(args.is_billed).lower()

    expenses = client.get_all("/expenses", "expenses", **params)
    total_cost = sum(e.get("total_cost") or 0 for e in expenses)

    output = {
        "category": "expenses",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        "counts": {
            "total": len(expenses),
            "total_cost": round(total_cost, 2),
        },
        "expenses": sorted(expenses, key=lambda x: x.get("spent_date", ""), reverse=True),
    }

    write_json(f"{args.output_dir}/{args.prefix}expenses.json", output)


if __name__ == "__main__":
    main()
