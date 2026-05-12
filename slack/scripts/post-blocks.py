#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Post a Block Kit message to a Slack channel from a JSON blocks file."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slack import SlackClient, check_env, resolve_channel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", required=True,
                        help="Target channel name or ID")
    parser.add_argument("--blocks", required=True, dest="blocks_file",
                        help="Path to a JSON file containing a Block Kit blocks array")
    parser.add_argument("--text", default="Message from Pi",
                        help="Fallback plain text shown in notifications")
    parser.add_argument("--thread-ts", default="", help="Post as a threaded reply")
    args = parser.parse_args()

    blocks_path = Path(args.blocks_file)
    if not blocks_path.exists():
        print(f"Error: blocks file not found: {args.blocks_file}", file=sys.stderr)
        sys.exit(1)

    blocks = json.loads(blocks_path.read_text())
    client = SlackClient(check_env())
    payload: dict = {
        "channel": resolve_channel(args.channel),
        "text": args.text,
        "blocks": blocks,
    }
    if args.thread_ts:
        payload["thread_ts"] = args.thread_ts

    data = client.post("chat.postMessage", **payload)
    print(f"Sent: channel={data['channel']} ts={data['ts']}")


if __name__ == "__main__":
    main()
