#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""
Fetch planned (allocated) hours from Parallax via the people utilization endpoint.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import ParallaxClient, check_api_key, resolve_range, now_utc, write_json


def fetch(
    client: ParallaxClient,
    start_date: str,
    end_date: str,
    person_ids: list[str] | None = None,
    level: str = "days",
    people_tags: list[str] | None = None,
    departments: list[str] | None = None,
    roles: list[str] | None = None,
    worker_type: list[str] | None = None,
) -> dict:
    person_id_set = set(person_ids or [])

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

    person_records = []

    for person_id, person in people_data.items():
        if person_id_set and person_id not in person_id_set:
            continue

        schedule = person.get("schedule", {})
        billable_planned_total = 0.0
        internal_planned_total = 0.0
        entries = []

        for date, day_data in sorted(schedule.items()):
            billable_planned = day_data.get("billable_planned_hours", 0)
            internal_planned = day_data.get("internal_planned_hours", 0)

            if billable_planned > 0 or internal_planned > 0:
                entries.append({
                    "date": date,
                    "billable_planned_hours": billable_planned,
                    "internal_planned_hours": internal_planned,
                    "total_hours": billable_planned + internal_planned,
                })
                billable_planned_total += billable_planned
                internal_planned_total += internal_planned

        total_hours = billable_planned_total + internal_planned_total
        if total_hours == 0:
            continue

        person_records.append({
            "person_id": person_id,
            "person_name": f"{person.get('given_name', '')} {person.get('family_name', '')}".strip(),
            "billable_planned_hours": round(billable_planned_total, 2),
            "internal_planned_hours": round(internal_planned_total, 2),
            "total_hours": round(total_hours, 2),
            "entries": entries,
        })

    person_records.sort(key=lambda x: -x["total_hours"])

    total_allocated = round(sum(r["total_hours"] for r in person_records), 2)
    total_billable_planned = round(sum(r["billable_planned_hours"] for r in person_records), 2)
    total_internal_planned = round(sum(r["internal_planned_hours"] for r in person_records), 2)

    return {
        "category": "allocations",
        "since": f"{start_date}T00:00:00Z",
        "until": f"{end_date}T23:59:59Z",
        "range": {"start_date": start_date, "end_date": end_date},
        "generated_at": now_utc(),
        "counts": {
            "total_hours": total_allocated,
            "billable_planned_hours": total_billable_planned,
            "internal_planned_hours": total_internal_planned,
            "active_people": len(person_records),
        },
        "by_person": person_records,
        "items": person_records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--person", dest="person_ids", action="append", default=[], metavar="UUID",
                        help="Limit to roles assigned to a specific person UUID (repeatable)")
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
    write_json(data, os.path.join(output_dir, f"{args.prefix}allocations.json"))


if __name__ == "__main__":
    main()
