#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""
Generate a Parallax executive-summary report covering time entries,
people, and projects for a date range. Pass --with-allocations
to add a logged vs allocated (utilisation) comparison.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import ParallaxClient, check_api_key, resolve_range, now_utc, slugify, write_json
import time_entries as te_mod
import people as people_mod
import projects as projects_mod
import allocations as alloc_mod


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def _h(level: int, text: str) -> str:
    return f"{'#' * level} {text}"


def _bullet(text: str) -> str:
    return f"- {text}"


def _bold(text: str) -> str:
    return f"**{text}**"


def build_markdown(report: dict, with_allocations: bool) -> str:
    lines = []
    r = report

    lines += [_h(1, "Parallax Executive Summary"), ""]
    lines += [f"Period: {r['range']['start_date']} to {r['range']['end_date']}", ""]

    # Top line
    c = r["summary"]["counts"]
    lines += [_h(2, "Top Line"), ""]
    lines += [_bullet(f"{_bold('Total hours:')} {c['total_hours']}h")]
    lines += [_bullet(f"{_bold('Billable:')} {c['billable_hours']}h ({c['billable_pct']}%)")]
    lines += [_bullet(f"{_bold('Non-billable:')} {c['non_billable_hours']}h")]
    if with_allocations and c.get("allocated_hours") is not None:
        lines += [_bullet(f"{_bold('Allocated:')} {c['allocated_hours']}h")]
    lines += [_bullet(f"{_bold('Active people:')} {c['active_people']}")]
    lines += [_bullet(f"{_bold('Total entries:')} {c['total_entries']}")]
    lines.append("")

    # By person
    lines += [_h(2, "By Person"), ""]
    top_people = r["summary"]["top_people"]
    if not top_people:
        lines += [_bullet("No time logged.")]
    else:
        for p in top_people:
            name = _bold(p["name"])
            if with_allocations and p.get("allocated_hours") is not None:
                pct = p.get("pct_logged", 0)
                line = f"{name}: {p['logged_hours']}h logged / {p['allocated_hours']}h allocated ({pct}%)"
                line += f" — {p['billable_hours']}h billable, {p['entries']} entries"
            else:
                hours = p.get("logged_hours") or p.get("total_hours", 0)
                line = f"{name}: {hours}h ({p['billable_hours']}h billable, {p['entries']} entries)"
            lines += [_bullet(line)]
    lines.append("")

    # Recent entries
    lines += [_h(2, "Recent Entries"), ""]
    entries = r["time_entries"]["items"][:20]
    if not entries:
        lines += [_bullet("No entries in this period.")]
    else:
        for e in entries:
            name = e.get("person_name", e["person_id"])
            nb = "" if e["billable"] else " [non-billable]"
            lines += [_bullet(f"{e['recorded_date']} — {name}: {e['hours']}h{nb}")]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--person", dest="person_ids", action="append", default=[], metavar="UUID",
                        help="Scope to a specific person UUID (repeatable)")
    parser.add_argument("--days", type=int, default=7, help="Look back N days (default: 7)")
    parser.add_argument("--since", default="", help="Start date YYYY-MM-DD (use with --until)")
    parser.add_argument("--until", default="", help="End date YYYY-MM-DD (use with --since)")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory (default: ../output or BASIL_OUTPUT_DIR)")
    parser.add_argument("--with-allocations", action="store_true",
                        help="Collect planned hours and include logged vs allocated comparison (slower)")
    args = parser.parse_args()
    output_dir = (
        args.output_dir
        or os.environ.get("BASIL_OUTPUT_DIR")
        or os.path.join(os.path.dirname(__file__), "..", "output")
    )

    client = ParallaxClient(check_api_key())
    start_date, end_date, since_iso, until_iso = resolve_range(args.days, args.since, args.until)

    # Determine output slug
    if len(args.person_ids) == 1:
        slug, mode = f"person-{args.person_ids[0]}", "person"
    elif len(args.person_ids) > 1:
        slug, mode = "selected-people", "people"
    else:
        slug, mode = "parallax-account", "account"

    base_name = f"{slug}-{start_date}_to_{end_date}"
    os.makedirs(output_dir, exist_ok=True)
    final_json = os.path.join(output_dir, f"{base_name}.json")
    final_md = os.path.join(output_dir, f"{base_name}.md")

    print(f"=== Parallax Executive Summary ===")
    print(f"Period: {start_date} to {end_date}")
    print(f"Output: {final_json}")
    print()

    print("--- Collecting time entries ---")
    te_data = te_mod.fetch(client, start_date, end_date, args.person_ids or None)
    print()

    print("--- Collecting people ---")
    people_data = people_mod.fetch(client)
    print()

    print("--- Collecting projects ---")
    projects_data = projects_mod.fetch(client)
    print()

    alloc_data = None
    if args.with_allocations:
        print("--- Collecting allocations ---")
        alloc_data = alloc_mod.fetch(
            client,
            start_date,
            end_date,
            person_ids=args.person_ids or None,
        )
        print()

    # Build lookup map for name enrichment
    people_map = {p["id"]: p for p in people_data["items"]}

    total_hours = te_data["counts"]["total_hours"]
    billable_hours = te_data["counts"]["billable_hours"]
    non_billable_hours = te_data["counts"]["non_billable_hours"]
    billable_pct = round(billable_hours / total_hours * 100) if total_hours > 0 else 0

    # Enrich by_person with names (and allocation data if available)
    alloc_by_person = {r["person_id"]: r for r in (alloc_data["by_person"] if alloc_data else [])}
    top_people = []
    for p in te_data["by_person"][:10]:
        alloc = alloc_by_person.get(p["person_id"])
        entry = {
            "person_id": p["person_id"],
            "name": people_map.get(p["person_id"], {}).get("name") or p["person_id"],
            "logged_hours": p["total_hours"],
            "billable_hours": p["billable_hours"],
            "entries": p["entries"],
        }
        if alloc_data:
            alloc_hours = alloc["total_hours"] if alloc else None
            entry["allocated_hours"] = alloc_hours
            entry["pct_logged"] = (
                round(p["total_hours"] / alloc_hours * 100) if alloc_hours else None
            )
        top_people.append(entry)

    report = {
        "schema_version": "1.0",
        "generated_at": now_utc(),
        "range": {
            "start_date": start_date,
            "end_date": end_date,
            "since": since_iso,
            "until": until_iso,
        },
        "target": {
            "mode": mode,
            "slug": slug,
            "person_ids": args.person_ids,
        },
        "summary": {
            "counts": {
                "total_hours": total_hours,
                "billable_hours": billable_hours,
                "non_billable_hours": non_billable_hours,
                "billable_pct": billable_pct,
                "allocated_hours": alloc_data["counts"]["total_hours"] if alloc_data else None,
                "total_entries": te_data["counts"]["total_entries"],
                "active_people": te_data["counts"]["active_people"],
            },
            "top_people": top_people,
        },
        "time_entries": te_data,
        "allocations": alloc_data,
        "people": people_data,
        "projects": projects_data,
    }

    write_json(report, final_json)

    md = build_markdown(report, args.with_allocations)
    with open(final_md, "w") as f:
        f.write(md)
    print(f"  Wrote: {final_md}")

    print()
    print("=== Complete ===")
    print(f"JSON: {final_json}")
    print(f"Markdown: {final_md}")


if __name__ == "__main__":
    main()
