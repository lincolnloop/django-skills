#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List estimates from Harvest."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, resolve_range, now_utc, write_json


def main() -> None:
    p = argparse.ArgumentParser(description="List estimates from Harvest.")
    p.add_argument("--client", metavar="CLIENT_ID", default="",
                   help="Filter to a specific client")
    p.add_argument("--state", choices=["draft", "sent", "accepted", "declined"],
                   help="Filter by estimate state")
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
    if args.state:
        params["state"] = args.state

    estimates = client.get_all("/estimates", "estimates", **params)
    total_amount = sum(e.get("amount") or 0 for e in estimates)

    output = {
        "category": "estimates",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        "counts": {
            "total": len(estimates),
            "total_amount": round(total_amount, 2),
        },
        "estimates": sorted(estimates, key=lambda x: x.get("issue_date", ""), reverse=True),
    }

    write_json(f"{args.output_dir}/{args.prefix}estimates.json", output)


if __name__ == "__main__":
    main()
