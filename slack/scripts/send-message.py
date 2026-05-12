#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Send a plain text or mrkdwn message to a Slack channel."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slack import SlackClient, check_env, resolve_channel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", required=True,
                        help="Target channel name (e.g. #general) or ID (e.g. C123ABC456)")
    parser.add_argument("--text", default="", help="Message text (mrkdwn supported)")
    parser.add_argument("--file", default="", dest="text_file",
                        help="Read message text from a file instead of --text")
    parser.add_argument("--thread-ts", default="", help="Post as a reply to this thread timestamp")
    parser.add_argument("--no-unfurl", action="store_true", help="Disable link unfurling")
    args = parser.parse_args()

    text = args.text
    if args.text_file:
        text = Path(args.text_file).read_text()
    if not text:
        print("Error: --text or --file is required.", file=sys.stderr)
        sys.exit(1)

    client = SlackClient(check_env())
    payload: dict = {
        "channel": resolve_channel(args.channel),
        "text": text,
        "unfurl_links": not args.no_unfurl,
    }
    if args.thread_ts:
        payload["thread_ts"] = args.thread_ts

    data = client.post("chat.postMessage", **payload)
    print(f"Sent: channel={data['channel']} ts={data['ts']}")


if __name__ == "__main__":
    main()
