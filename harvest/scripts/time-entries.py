#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Fetch raw time entries from Harvest with aggregations by user, project, and task."""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest import HarvestClient, resolve_range, now_utc, write_json, base_parser


def aggregate(entries: list) -> dict:
    by_user: dict = defaultdict(lambda: {"total_hours": 0.0, "billable_hours": 0.0, "entries": 0})
    by_project: dict = defaultdict(lambda: {"total_hours": 0.0, "billable_hours": 0.0, "entries": 0})
    by_task: dict = defaultdict(lambda: {"total_hours": 0.0, "billable_hours": 0.0, "entries": 0})
    items = []

    for e in entries:
        item = {
            "id": e["id"],
            "spent_date": e["spent_date"],
            "user": e["user"]["name"],
            "user_id": e["user"]["id"],
            "client": e["client"]["name"],
            "client_id": e["client"]["id"],
            "project": e["project"]["name"],
            "project_id": e["project"]["id"],
            "task": e["task"]["name"],
            "task_id": e["task"]["id"],
            "hours": e["hours"],
            "billable": e["billable"],
            "notes": e.get("notes"),
            "created_at": e["created_at"],
            "updated_at": e["updated_at"],
        }
        items.append(item)

        uid = e["user"]["id"]
        by_user[uid].setdefault("user_id", uid)
        by_user[uid].setdefault("user", e["user"]["name"])
        by_user[uid]["total_hours"] += e["hours"]
        if e["billable"]:
            by_user[uid]["billable_hours"] += e["hours"]
        by_user[uid]["entries"] += 1

        pid = e["project"]["id"]
        by_project[pid].setdefault("project_id", pid)
        by_project[pid].setdefault("project", e["project"]["name"])
        by_project[pid].setdefault("client", e["client"]["name"])
        by_project[pid].setdefault("client_id", e["client"]["id"])
        by_project[pid]["total_hours"] += e["hours"]
        if e["billable"]:
            by_project[pid]["billable_hours"] += e["hours"]
        by_project[pid]["entries"] += 1

        tid = e["task"]["id"]
        by_task[tid].setdefault("task_id", tid)
        by_task[tid].setdefault("task", e["task"]["name"])
        by_task[tid]["total_hours"] += e["hours"]
        if e["billable"]:
            by_task[tid]["billable_hours"] += e["hours"]
        by_task[tid]["entries"] += 1

    total_hours = sum(i["hours"] for i in items)
    billable_hours = sum(i["hours"] for i in items if i["billable"])

    return {
        "counts": {
            "total_entries": len(items),
            "total_hours": round(total_hours, 4),
            "billable_hours": round(billable_hours, 4),
            "non_billable_hours": round(total_hours - billable_hours, 4),
            "active_users": len(by_user),
            "active_projects": len(by_project),
        },
        "by_user": sorted(by_user.values(), key=lambda x: -x["total_hours"]),
        "by_project": sorted(by_project.values(), key=lambda x: -x["total_hours"]),
        "by_task": sorted(by_task.values(), key=lambda x: -x["total_hours"]),
        "items": sorted(items, key=lambda x: x["spent_date"], reverse=True),
    }


def main() -> None:
    p = base_parser(
        "Fetch time entries from Harvest for a date range and produce aggregations"
        " by user, project, and task."
    )
    p.add_argument("--user", dest="user_ids", metavar="USER_ID", action="append", default=[],
                   help="Filter to a specific user (repeatable)")
    p.add_argument("--project", dest="project_ids", metavar="PROJECT_ID", action="append", default=[],
                   help="Filter to a specific project (repeatable)")
    p.add_argument("--client", metavar="CLIENT_ID", default="",
                   help="Filter to a specific client")
    args = p.parse_args()

    client = HarvestClient()
    start_date, end_date = resolve_range(args.days, args.since, args.until)

    base_params: dict = {"from": start_date, "to": end_date}
    if args.client:
        base_params["client_id"] = args.client

    all_entries: list = []
    if args.user_ids:
        for uid in args.user_ids:
            all_entries.extend(
                client.get_all("/time_entries", "time_entries", **base_params, user_id=uid)
            )
    elif args.project_ids:
        for pid in args.project_ids:
            all_entries.extend(
                client.get_all("/time_entries", "time_entries", **base_params, project_id=pid)
            )
    else:
        all_entries = client.get_all("/time_entries", "time_entries", **base_params)

    agg = aggregate(all_entries)
    output = {
        "category": "time_entries",
        "since": f"{start_date}T00:00:00Z",
        "until": f"{end_date}T23:59:59Z",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        **agg,
    }

    write_json(f"{args.output_dir}/{args.prefix}time-entries.json", output)


if __name__ == "__main__":
    main()
