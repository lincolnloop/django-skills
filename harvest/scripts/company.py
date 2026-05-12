#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Fetch Harvest account/company information and feature flags."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, now_utc, write_json


def main() -> None:
    p = argparse.ArgumentParser(
        description="Fetch Harvest account information: name, currency, feature flags, and settings."
    )
    p.add_argument("--output-dir", metavar="DIR", default=".",
                   help="Write output to this directory (default: .)")
    p.add_argument("--prefix", metavar="PREFIX", default="",
                   help="Output filename prefix")
    args = p.parse_args()

    client = HarvestClient()
    data = client.get("/company")

    output = {
        "category": "company",
        "generated_at": now_utc(),
        "company": data,
    }

    write_json(f"{args.output_dir}/{args.prefix}company.json", output)


if __name__ == "__main__":
    main()
