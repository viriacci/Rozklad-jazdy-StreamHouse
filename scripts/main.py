import argparse
import datetime as dt
import hashlib
import json
from zoneinfo import ZoneInfo

from fetch_sheet import fetch_week_schedule
from render_calendar import render_week
from update_discord import publish, load_state, clean_pending

def week_range(today, mode="auto"):
    monday = today - dt.timedelta(days=today.weekday())
    if mode == "next" or (mode == "auto" and today.weekday() == 6):
        monday += dt.timedelta(days=7)
    return [monday + dt.timedelta(days=i) for i in range(7)]

def fingerprint(schedule, dates):
    canonical = {day.isoformat(): sorted(set(schedule.get(day.isoformat(), []))) for day in dates}
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", choices=["auto", "current", "next"], default="auto")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    today = dt.datetime.now(ZoneInfo("Europe/Warsaw")).date()
    dates = week_range(today, args.week)
    state = load_state()
    if not args.dry_run:
        clean_pending(state)
    schedule = fetch_week_schedule(dates)
    digest = fingerprint(schedule, dates)
    if not args.dry_run and state.get("fingerprint") == digest:
        print("Harmonogram bez zmian.")
        return
    image = render_week(schedule, dates, output_path="calendar.png")
    if not args.dry_run:
        publish(image, digest, state)

if __name__ == "__main__":
    main()
