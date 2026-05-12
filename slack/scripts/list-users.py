#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""List all users (members) in the Slack workspace."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slack import SlackClient, check_env, now_utc, write_json, base_parser


def fetch(client: SlackClient, include_bots: bool = False) -> dict:
    members = client.get_all("users.list", "members", limit=200)

    items = []
    for m in members:
        if m.get("deleted"):
            continue
        if not include_bots and (m.get("is_bot") or m.get("id") == "USLACKBOT"):
            continue
        profile = m.get("profile") or {}
        items.append({
            "id": m.get("id"),
            "name": m.get("name"),
            "real_name": m.get("real_name") or profile.get("real_name"),
            "display_name": profile.get("display_name"),
            "email": profile.get("email"),
            "is_admin": m.get("is_admin", False),
            "is_owner": m.get("is_owner", False),
            "is_bot": m.get("is_bot", False),
            "tz": m.get("tz"),
        })

    items.sort(key=lambda u: (u.get("real_name") or u.get("name") or "").lower())

    return {
        "category": "users",
        "generated_at": now_utc(),
        "counts": {"total": len(items)},
        "users": items,
    }


def main():
    parser = base_parser(__doc__)
    parser.add_argument("--include-bots", action="store_true",
                        help="Include bot accounts (excluded by default)")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = SlackClient(check_env())
    data = fetch(client, include_bots=args.include_bots)
    write_json(os.path.join(output_dir, f"{args.prefix}users.json"), data)
    print(f"  {data['counts']['total']} users")


if __name__ == "__main__":
    main()
