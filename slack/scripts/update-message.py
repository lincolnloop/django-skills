#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Update an existing Slack message by channel ID and timestamp."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slack import SlackClient, check_env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", required=True,
                        help="Channel ID containing the message (e.g. C123ABC456)")
    parser.add_argument("--ts", required=True,
                        help="Timestamp of the message to update (e.g. 1503435956.000247)")
    parser.add_argument("--text", default="", help="New message text")
    parser.add_argument("--blocks", default="", dest="blocks_file",
                        help="Path to a JSON file containing a new blocks array")
    args = parser.parse_args()

    if not args.text and not args.blocks_file:
        print("Error: one of --text or --blocks is required.", file=sys.stderr)
        sys.exit(1)

    payload: dict = {"channel": args.channel, "ts": args.ts}
    if args.text:
        payload["text"] = args.text
    if args.blocks_file:
        blocks_path = Path(args.blocks_file)
        if not blocks_path.exists():
            print(f"Error: blocks file not found: {args.blocks_file}", file=sys.stderr)
            sys.exit(1)
        payload["blocks"] = json.loads(blocks_path.read_text())

    client = SlackClient(check_env())
    data = client.post("chat.update", **payload)
    print(f"Updated: channel={data['channel']} ts={data['ts']}")


if __name__ == "__main__":
    main()
