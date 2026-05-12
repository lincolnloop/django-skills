#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List invoices from Harvest."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, resolve_range, now_utc, write_json


def main() -> None:
    p = argparse.ArgumentParser(description="List invoices from Harvest.")
    p.add_argument("--client", metavar="CLIENT_ID", default="",
                   help="Filter to a specific client")
    p.add_argument("--project", metavar="PROJECT_ID", default="",
                   help="Filter to a specific project")
    p.add_argument("--state", choices=["draft", "open", "paid", "closed"],
                   help="Filter by invoice state")
    p.add_argument("--days", type=int, default=30, metavar="N",
                   help="Look back N days (default: 30)")
    p.add_argument("--since", metavar="DATE",
                   help="Inclusive start date YYYY-MM-DD (must be used with --until)")
    p.add_argument("--until", metavar="DATE",
                   help="Inclusive end date YYYY-MM-DD (must be used with --since)")
    p.add_argument("--output-dir", metavar="DIR", default=".",
                   help="Write output to this directory (default: .)")
    p.add_argument("--prefix", metavar="PREFIX", default="",
                   help="Output filename prefix")
    args = p.parse_args()

    client = HarvestClient()
    start_date, end_date = resolve_range(args.days, args.since, args.until)

    params: dict = {"from": start_date, "to": end_date}
    if args.client:
        params["client_id"] = args.client
    if args.project:
        params["project_id"] = args.project
    if args.state:
        params["state"] = args.state

    invoices = client.get_all("/invoices", "invoices", **params)

    total_amount = sum(i.get("amount") or 0 for i in invoices)
    due_amount = sum(i.get("due_amount") or 0 for i in invoices)

    output = {
        "category": "invoices",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        "counts": {
            "total": len(invoices),
            "total_amount": round(total_amount, 2),
            "due_amount": round(due_amount, 2),
        },
        "invoices": sorted(invoices, key=lambda x: x.get("issue_date", ""), reverse=True),
    }

    write_json(f"{args.output_dir}/{args.prefix}invoices.json", output)


if __name__ == "__main__":
    main()
