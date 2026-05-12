#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Fetch recent messages from a Slack channel."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slack import SlackClient, check_env, now_utc, write_json, base_parser, resolve_channel


def fetch(
    client: SlackClient,
    channel: str,
    limit: int = 50,
    oldest: str = "",
    latest: str = "",
    include_replies: bool = False,
) -> dict:
    params: dict = {"channel": channel, "limit": limit}
    if oldest:
        params["oldest"] = oldest
    if latest:
        params["latest"] = latest

    data = client.get("conversations.history", **params)
    messages = data.get("messages") or []

    items = []
    for msg in messages:
        if msg.get("subtype"):
            continue
        entry: dict = {
            "ts": msg.get("ts"),
            "user": msg.get("user"),
            "text": msg.get("text"),
            "reply_count": msg.get("reply_count", 0),
            "reactions": [
                {"name": r["name"], "count": r["count"]}
                for r in msg.get("reactions") or []
            ],
        }
        if include_replies and msg.get("reply_count", 0) > 0:
            replies_data = client.get("conversations.replies",
                                      channel=channel, ts=msg["ts"])
            entry["replies"] = [
                {"ts": r.get("ts"), "user": r.get("user"), "text": r.get("text")}
                for r in (replies_data.get("messages") or [])[1:]  # skip parent
            ]
        items.append(entry)

    return {
        "category": "channel_history",
        "channel": channel,
        "generated_at": now_utc(),
        "counts": {"total": len(items)},
        "messages": items,
    }


def main():
    parser = base_parser(__doc__)
    parser.add_argument("--channel", required=True,
                        help="Channel name (e.g. #general) or ID (e.g. C123ABC456)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Number of messages to fetch (default: 50, max: 999)")
    parser.add_argument("--oldest", default="",
                        help="Return messages after this Unix timestamp")
    parser.add_argument("--latest", default="",
                        help="Return messages before this Unix timestamp")
    parser.add_argument("--include-replies", action="store_true",
                        help="Fetch thread replies for each message with replies")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    channel = resolve_channel(args.channel)
    client = SlackClient(check_env())
    data = fetch(client, channel, limit=args.limit, oldest=args.oldest,
                 latest=args.latest, include_replies=args.include_replies)
    write_json(os.path.join(output_dir, f"{args.prefix}channel-{channel}.json"), data)
    print(f"  {data['counts']['total']} messages")


if __name__ == "__main__":
    main()
