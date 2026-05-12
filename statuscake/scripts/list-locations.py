#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List StatusCake probe server locations (uptime and pagespeed)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statuscake import StatusCakeClient, check_env, now_utc, write_json, base_parser


def fetch(client: StatusCakeClient) -> dict:
    uptime_data = client.get("/uptime-locations")
    pagespeed_data = client.get("/pagespeed-locations")

    uptime_locs = uptime_data.get("data") or []
    pagespeed_locs = pagespeed_data.get("data") or []

    return {
        "category": "locations",
        "generated_at": now_utc(),
        "counts": {
            "uptime_locations": len(uptime_locs),
            "pagespeed_locations": len(pagespeed_locs),
        },
        "uptime_locations": sorted(uptime_locs, key=lambda l: l.get("region") or ""),
        "pagespeed_locations": sorted(pagespeed_locs, key=lambda l: l.get("region") or ""),
    }


def main():
    parser = base_parser(__doc__)
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = StatusCakeClient(check_env())
    data = fetch(client)
    write_json(os.path.join(output_dir, f"{args.prefix}locations.json"), data)


if __name__ == "__main__":
    main()
