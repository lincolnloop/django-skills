#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Fetch project budget report from Harvest Reports API."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, now_utc, write_json


def main() -> None:
    p = argparse.ArgumentParser(
        description="Fetch project budget report from the Harvest Reports API."
        " Shows budget spent and remaining per project. No date range required."
    )
    p.add_argument("--is-active", action=argparse.BooleanOptionalAction, default=None,
                   help="Filter to active (--is-active) or inactive (--no-is-active) projects")
    p.add_argument("--output-dir", metavar="DIR", default=".",
                   help="Write output to this directory (default: .)")
    p.add_argument("--prefix", metavar="PREFIX", default="",
                   help="Output filename prefix")
    args = p.parse_args()

    client = HarvestClient()

    params: dict = {}
    if args.is_active is not None:
        params["is_active"] = str(args.is_active).lower()

    results = client.get_all("/reports/project_budget", "project_budget_report_results", **params)

    output = {
        "category": "project_budget",
        "generated_at": now_utc(),
        "counts": {"total_projects": len(results)},
        "projects": results,
    }

    write_json(f"{args.output_dir}/{args.prefix}report-budget.json", output)


if __name__ == "__main__":
    main()
