#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Fetch historical check results for a specific uptime monitor."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statuscake import StatusCakeClient, check_env, now_utc, write_json, base_parser


def fetch(
    client: StatusCakeClient,
    test_id: str,
    before: int | None = None,
    after: int | None = None,
) -> dict:
    params: dict = {}
    if before:
        params["before"] = before
    if after:
        params["after"] = after

    items = client.get_all(f"/uptime/{test_id}/history", **params)
    return {
        "category": "uptime_history",
        "test_id": test_id,
        "generated_at": now_utc(),
        "counts": {"total": len(items)},
        "items": items,
    }


def main():
    parser = base_parser(__doc__)
    parser.add_argument("--test-id", required=True, help="Uptime check ID")
    parser.add_argument("--before", type=int, default=None,
                        help="Return results before this Unix timestamp")
    parser.add_argument("--after", type=int, default=None,
                        help="Return results after this Unix timestamp")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = StatusCakeClient(check_env())
    data = fetch(client, args.test_id, before=args.before, after=args.after)
    write_json(os.path.join(output_dir, f"{args.prefix}uptime-history-{args.test_id}.json"), data)


if __name__ == "__main__":
    main()
