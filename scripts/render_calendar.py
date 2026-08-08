"""
Renderuje siatkę tygodnia (7 kolumn) jako PNG.
Dla każdego dnia rysuje kółka z avatarami streamerów, którzy tego dnia
streamują:
  - 1 osoba  -> na środku góry komórki
  - 2 osoby  -> w górnych rogach komórki
  - 3 osoby  -> równomiernie na całej górnej krawędzi
"""
import datetime as dt
from PIL import Image, ImageDraw, ImageFont

import config

DAY_NAMES_PL = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Niedz"]


def avatar_positions(n, cell_width, avatar_size, margin_top=14, side_margin=14):
    """Zwraca listę (x, y) - środków kółek - względem lewego górnego rogu komórki."""
    r = avatar_size / 2
    y = margin_top + r
    if n == 0:
        return []
    if n == 1:
        return [(cell_width / 2, y)]
    if n == 2:
        return [
            (side_margin + r, y),
            (cell_width - side_margin - r, y),
        ]
    # n >= 3: równomiernie na całej górnej krawędzi
    usable = cell_width - 2 * side_margin - avatar_size
    if n == 1:
        step = 0
    else:
        step = usable / (n - 1)
    return [(side_margin + r + i * step, y) for i in range(n)]


def paste_circular_avatar(base_img, avatar_path, center_xy, size):
    """Wkleja avatar przycięty do koła, wyśrodkowany na center_xy."""
    avatar = Image.open(avatar_path).convert("RGBA").resize((size, size))
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=255)

    # cienka obwódka dla czytelności na ciemnym tle
    ring = Image.new("RGBA", (size + 6, size + 6), (0, 0, 0, 0))
    ring_draw = ImageDraw.Draw(ring)
    ring_draw.ellipse((0, 0, size + 6, size + 6), fill=(255, 255, 255, 60))
    base_img.paste(
        ring,
        (int(center_xy[0] - size / 2 - 3), int(center_xy[1] - size / 2 - 3)),
        ring,
    )

    x, y = int(center_xy[0] - size / 2), int(center_xy[1] - size / 2)
    base_img.paste(avatar, (x, y), mask)


def _load_font(size, bold=False):
    try:
        return ImageFont.truetype(config.FONT_PATH, size)
    except OSError:
        # fallback gdyby brakowało własnego fontu w repo
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size
        )


def render_week(schedule, week_dates, output_path="calendar.png"):
    """
    schedule: dict {YYYY-MM-DD: [nazwy_streamerow]}
    week_dates: lista 7 obiektów datetime.date, poniedziałek..niedziela
    """
    n_days = len(week_dates)
    width = config.MARGIN * 2 + config.CELL_WIDTH * n_days
    height = config.MARGIN * 2 + config.HEADER_HEIGHT + config.CELL_HEIGHT

    img = Image.new("RGBA", (width, height), config.COLOR_BG)
    draw = ImageDraw.Draw(img)

    font_day = _load_font(22)
    font_date = _load_font(16)
    font_title = _load_font(26)

    today = dt.date.today()

    title = f"Streamy: {week_dates[0].strftime('%d.%m')} - {week_dates[-1].strftime('%d.%m.%Y')}"
    draw.text((config.MARGIN, 4), title, font=font_title, fill=config.COLOR_TEXT)

    top = config.MARGIN + config.HEADER_HEIGHT

    for i, day in enumerate(week_dates):
        x0 = config.MARGIN + i * config.CELL_WIDTH
        y0 = top
        x1 = x0 + config.CELL_WIDTH
        y1 = y0 + config.CELL_HEIGHT

        cell_color = config.COLOR_CELL_TODAY if day == today else config.COLOR_CELL
        draw.rectangle([x0, y0, x1, y1], fill=cell_color, outline=config.COLOR_GRID)

        day_label = f"{DAY_NAMES_PL[i]}  {day.strftime('%d.%m')}"
        draw.text((x0 + 12, y0 + 8), day_label, font=font_day, fill=config.COLOR_TEXT)

        streamers_today = schedule.get(day.isoformat(), [])

        if streamers_today:
            positions = avatar_positions(
                len(streamers_today), config.CELL_WIDTH, config.AVATAR_SIZE,
                margin_top=44,
            )
            for streamer_name, (px, py) in zip(streamers_today, positions):
                avatar_path = config.STREAMERS.get(streamer_name)
                if not avatar_path:
                    continue
                paste_circular_avatar(img, avatar_path, (x0 + px, y0 + py), config.AVATAR_SIZE)
        else:
            draw.text(
                (x0 + 12, y0 + config.CELL_HEIGHT - 30),
                "brak streamu",
                font=font_date,
                fill=config.COLOR_TEXT_MUTED,
            )

    img.save(output_path)
    return output_path


if __name__ == "__main__":
    # szybki test lokalny bez arkusza - przykładowe dane
    monday = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
    week = [monday + dt.timedelta(days=i) for i in range(7)]
    example_schedule = {
        week[0].isoformat(): ["Bartek"],
        week[1].isoformat(): ["Bartek", "Streamer2"],
        week[3].isoformat(): ["Streamer2"],
        week[5].isoformat(): ["Bartek", "Streamer2"],
    }
    path = render_week(example_schedule, week, output_path="test_output.png")
    print(f"Zapisano: {path}")
