#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List all SSL certificate checks from StatusCake."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statuscake import StatusCakeClient, check_env, now_utc, write_json, base_parser


def fetch(client: StatusCakeClient) -> dict:
    checks = client.get_all("/ssl")

    valid = [c for c in checks if not c.get("paused") and c.get("status") == "VALID"]
    broken = [c for c in checks if not c.get("paused") and c.get("status") != "VALID"]
    paused = [c for c in checks if c.get("paused")]

    return {
        "category": "ssl_checks",
        "generated_at": now_utc(),
        "counts": {
            "total": len(checks),
            "valid": len(valid),
            "invalid": len(broken),
            "paused": len(paused),
        },
        "items": sorted(checks, key=lambda c: c.get("website_url") or ""),
    }


def main():
    parser = base_parser(__doc__)
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = StatusCakeClient(check_env())
    data = fetch(client)
    write_json(os.path.join(output_dir, f"{args.prefix}ssl-checks.json"), data)


if __name__ == "__main__":
    main()
