#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List all pagespeed checks from StatusCake."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statuscake import StatusCakeClient, check_env, now_utc, write_json, base_parser


def fetch(client: StatusCakeClient) -> dict:
    checks = client.get_all("/pagespeed")
    active = [c for c in checks if not c.get("paused")]
    paused = [c for c in checks if c.get("paused")]

    return {
        "category": "pagespeed_checks",
        "generated_at": now_utc(),
        "counts": {
            "total": len(checks),
            "active": len(active),
            "paused": len(paused),
        },
        "items": sorted(checks, key=lambda c: c.get("name") or ""),
    }


def main():
    parser = base_parser(__doc__)
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = StatusCakeClient(check_env())
    data = fetch(client)
    write_json(os.path.join(output_dir, f"{args.prefix}pagespeed-checks.json"), data)


if __name__ == "__main__":
    main()
