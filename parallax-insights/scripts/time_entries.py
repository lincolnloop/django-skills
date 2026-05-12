#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""Fetch actual time entries from Parallax for a date range."""
import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from common import ParallaxClient, check_api_key, resolve_range, now_utc, write_json


def fetch(
    client: ParallaxClient,
    start_date: str,
    end_date: str,
    person_ids: list[str] | None = None,
    project_offering_id: str = "",
    level: str = "days",
    people_tags: list[str] | None = None,
    departments: list[str] | None = None,
    roles: list[str] | None = None,
    worker_type: list[str] | None = None,
) -> dict:
    params: dict = {"start_date": start_date, "end_date": end_date, "level": level}
    if people_tags:
        params["people_tags[]"] = people_tags
    if departments:
        params["departments[]"] = departments
    if roles:
        params["roles[]"] = roles
    if worker_type:
        params["worker_type[]"] = worker_type

    raw = client.get("/people/utilization", params)
    people_data = raw.get("data", {}).get("people", {})

    items = []
    for person_id, person in people_data.items():
        if person_ids and person_id not in person_ids:
            continue

        schedule = person.get("schedule", {})
        for date, day_data in schedule.items():
            billable_actual = day_data.get("billable_actual_hours", 0)
            internal_actual = day_data.get("internal_actual_hours", 0)

            if billable_actual > 0:
                items.append({
                    "person_id": person_id,
                    "recorded_date": date,
                    "hours": billable_actual,
                    "billable": True,
                    "person_name": f"{person.get('given_name', '')} {person.get('family_name', '')}".strip(),
                })

            if internal_actual > 0:
                items.append({
                    "person_id": person_id,
                    "recorded_date": date,
                    "hours": internal_actual,
                    "billable": False,
                    "person_name": f"{person.get('given_name', '')} {person.get('family_name', '')}".strip(),
                })

    items.sort(key=lambda x: x["recorded_date"], reverse=True)

    total_hours = sum(e["hours"] for e in items)
    billable_hours = sum(e["hours"] for e in items if e["billable"])

    by_person: dict[str, dict] = defaultdict(lambda: {"total_hours": 0.0, "billable_hours": 0.0, "entries": 0, "name": ""})
    for e in items:
        g = by_person[e["person_id"]]
        g["total_hours"] += e["hours"]
        g["name"] = e.get("person_name", "")
        if e["billable"]:
            g["billable_hours"] += e["hours"]
        g["entries"] += 1

    return {
        "category": "time_entries",
        "since": f"{start_date}T00:00:00Z",
        "until": f"{end_date}T23:59:59Z",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        "counts": {
            "total_entries": len(items),
            "total_hours": round(total_hours, 2),
            "billable_hours": round(billable_hours, 2),
            "non_billable_hours": round(total_hours - billable_hours, 2),
            "active_people": len(by_person),
        },
        "by_person": sorted(
            [{"person_id": pid, **v} for pid, v in by_person.items()],
            key=lambda x: -x["total_hours"],
        ),
        "items": items,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--person", dest="person_ids", action="append", default=[], metavar="UUID",
                        help="Filter to a specific person UUID (repeatable)")
    parser.add_argument("--level", default="days", choices=["days", "weeks", "months"],
                        help="Aggregation level (default: days)")
    parser.add_argument("--people-tag", dest="people_tags", action="append", default=[],
                        metavar="TAG", help="Filter by people tag e.g. Location::MN (repeatable)")
    parser.add_argument("--department", dest="departments", action="append", default=[],
                        metavar="NAME", help="Filter by department name (repeatable)")
    parser.add_argument("--role", dest="roles", action="append", default=[],
                        metavar="NAME", help="Filter by role name (repeatable)")
    parser.add_argument("--worker-type", dest="worker_type", action="append", default=[],
                        metavar="TYPE",
                        help="Filter by worker type: FullTime, Contractor, Placeholder (repeatable)")
    parser.add_argument("--days", type=int, default=7, help="Look back N days (default: 7)")
    parser.add_argument("--since", default="", help="Start date YYYY-MM-DD (use with --until)")
    parser.add_argument("--until", default="", help="End date YYYY-MM-DD (use with --since)")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--prefix", default="", help="Output filename prefix")
    args = parser.parse_args()
    output_dir = args.output_dir or os.environ.get("BASIL_OUTPUT_DIR", ".")

    client = ParallaxClient(check_api_key())
    start_date, end_date, _, _ = resolve_range(args.days, args.since, args.until)
    data = fetch(
        client,
        start_date,
        end_date,
        args.person_ids or None,
        level=args.level,
        people_tags=args.people_tags or None,
        departments=args.departments or None,
        roles=args.roles or None,
        worker_type=args.worker_type or None,
    )
    write_json(data, os.path.join(output_dir, f"{args.prefix}time-entries.json"))


if __name__ == "__main__":
    main()
