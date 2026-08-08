import datetime as dt

import config
from fetch_sheet import fetch_week_schedule, _current_week_range
from render_calendar import render_week
from update_discord import post_or_edit_calendar


def main():
    week_dates = _current_week_range()
    schedule = fetch_week_schedule()
    image_path = render_week(schedule, week_dates, output_path="calendar.png")
    post_or_edit_calendar(image_path)


if __name__ == "__main__":
    main()
