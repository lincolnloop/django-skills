#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List channels in the Slack workspace."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slack import SlackClient, check_env, now_utc, write_json, base_parser


def fetch(
    client: SlackClient,
    types: str = "public_channel,private_channel",
    exclude_archived: bool = True,
) -> dict:
    channels = client.get_all(
        "conversations.list",
        "channels",
        types=types,
        exclude_archived=str(exclude_archived).lower(),
        limit=200,
    )
    items = sorted(
        [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "is_private": c.get("is_private"),
                "is_archived": c.get("is_archived"),
                "num_members": c.get("num_members"),
                "topic": (c.get("topic") or {}).get("value", ""),
                "purpose": (c.get("purpose") or {}).get("value", ""),
            }
            for c in channels
        ],
        key=lambda c: c.get("name") or "",
    )
    return {
        "category": "channels",
        "generated_at": now_utc(),
        "counts": {"total": len(items)},
        "channels": items,
    }


def main():
    parser = base_parser(__doc__)
    parser.add_argument(
        "--types",
        default="public_channel,private_channel",
        help="Comma-separated channel types: public_channel, private_channel, mpim, im",
    )
    parser.add_argument(
        "--include-archived", action="store_true",
        help="Include archived channels (excluded by default)",
    )
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = SlackClient(check_env())
    data = fetch(client, types=args.types, exclude_archived=not args.include_archived)
    write_json(os.path.join(output_dir, f"{args.prefix}channels.json"), data)
    print(f"  {data['counts']['total']} channels")


if __name__ == "__main__":
    main()
