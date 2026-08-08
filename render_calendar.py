"""
Renderuje siatkę tygodnia jako PNG, w układzie 2 rzędów (4 dni + 3 dni)
zamiast jednego rzędu 7 kolumn. Powód: przy 1 rzędzie obrazek ma
proporcje ~5:1, a Discord skaluje podgląd na czacie do maks. szerokości
~400px - przy takich proporcjach wychodzi z tego pasek wysokości
~80px, nieczytelny. Układ 2x(4+3) daje proporcje bliższe kwadratowi,
więc podgląd na czacie jest realnie czytelny bez klikania.

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

# Układ 2 rzędów: pierwszy 4 dni, drugi 3 dni.
ROW_LAYOUT = [4, 3]

# Większe komórki niż w wersji 1-rzędowej - przy mniejszej liczbie kolumn
# w rzędzie jest na to miejsce, a dzięki temu avatary i daty są czytelne
# nawet w zeskalowanym podglądzie.
CELL_WIDTH = 300
CELL_HEIGHT = 260
AVATAR_SIZE = 76
HEADER_HEIGHT = 110  # 2 linie nagłówka (STREAMY + zakres dat)
ROW_GAP = 16

# Naprzemienne odcienie komórek wg dnia tygodnia (Pon jasny, Wt ciemny, ...)
COLOR_CELL_LIGHT = (52, 55, 61, 255)
COLOR_CELL_DARK = (36, 38, 43, 255)
COLOR_CELL_TODAY_BORDER = (227, 192, 72, 255)  # akcent, gdyby "dziś" wypadło w tym tygodniu


def avatar_positions(n, cell_width, avatar_size, margin_top=16, side_margin=16):
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


def _load_font(size):
    try:
        return ImageFont.truetype(config.FONT_PATH, size)
    except OSError:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size
        )


def render_week(schedule, week_dates, output_path="calendar.png"):
    """
    schedule: dict {YYYY-MM-DD: [nazwy_streamerow]}
    week_dates: lista 7 obiektów datetime.date, poniedziałek..niedziela
    """
    max_cols = max(ROW_LAYOUT)
    n_rows = len(ROW_LAYOUT)

    width = config.MARGIN * 2 + CELL_WIDTH * max_cols
    height = (
        config.MARGIN * 2
        + HEADER_HEIGHT
        + CELL_HEIGHT * n_rows
        + ROW_GAP * (n_rows - 1)
    )

    img = Image.new("RGBA", (width, height), config.COLOR_BG)
    draw = ImageDraw.Draw(img)

    font_day = _load_font(24)
    font_date = _load_font(18)
    font_title_big = _load_font(44)   # "STREAMY"
    font_title_sub = _load_font(26)   # zakres dat

    today = dt.date.today()

    title_main = "STREAMY"
    title_sub = f"{week_dates[0].strftime('%d.%m')} - {week_dates[-1].strftime('%d.%m')}"

    bbox_main = draw.textbbox((0, 0), title_main, font=font_title_big)
    main_w = bbox_main[2] - bbox_main[0]
    draw.text(
        ((width - main_w) / 2 - bbox_main[0], 8),
        title_main, font=font_title_big, fill=config.COLOR_TEXT,
    )

    bbox_sub = draw.textbbox((0, 0), title_sub, font=font_title_sub)
    sub_w = bbox_sub[2] - bbox_sub[0]
    draw.text(
        ((width - sub_w) / 2 - bbox_sub[0], 58),
        title_sub, font=font_title_sub, fill=config.COLOR_TEXT_MUTED,
    )

    day_index = 0
    row_top = config.MARGIN + HEADER_HEIGHT

    for row_len in ROW_LAYOUT:
        for col in range(row_len):
            day = week_dates[day_index]
            day_index += 1

            x0 = config.MARGIN + col * CELL_WIDTH
            y0 = row_top
            x1 = x0 + CELL_WIDTH
            y1 = y0 + CELL_HEIGHT

            weekday_idx = day.weekday()  # 0=Pon
            cell_color = COLOR_CELL_LIGHT if weekday_idx % 2 == 0 else COLOR_CELL_DARK
            outline_color = COLOR_CELL_TODAY_BORDER if day == today else config.COLOR_GRID
            outline_width = 3 if day == today else 1
            draw.rectangle(
                [x0, y0, x1, y1], fill=cell_color,
                outline=outline_color, width=outline_width,
            )

            day_label = f"{DAY_NAMES_PL[weekday_idx]}  {day.strftime('%d.%m')}"
            draw.text((x0 + 14, y0 + 10), day_label, font=font_day, fill=config.COLOR_TEXT)

            streamers_today = schedule.get(day.isoformat(), [])

            if streamers_today:
                positions = avatar_positions(
                    len(streamers_today), CELL_WIDTH, AVATAR_SIZE, margin_top=52,
                )
                for streamer_name, (px, py) in zip(streamers_today, positions):
                    avatar_path = config.STREAMERS.get(streamer_name)
                    if not avatar_path:
                        continue
                    paste_circular_avatar(img, avatar_path, (x0 + px, y0 + py), AVATAR_SIZE)
            else:
                draw.text(
                    (x0 + 14, y0 + CELL_HEIGHT - 34),
                    "brak streamu",
                    font=font_date,
                    fill=config.COLOR_TEXT_MUTED,
                )

        row_top += CELL_HEIGHT + ROW_GAP

    img.save(output_path)
    return output_path


if __name__ == "__main__":
    # szybki test lokalny bez arkusza - przykładowe dane
    monday = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
    week = [monday + dt.timedelta(days=i) for i in range(7)]
    example_schedule = {
        week[0].isoformat(): ["Shiroe"],
        week[1].isoformat(): ["Shiroe", "ViviOnyx"],
        week[3].isoformat(): ["ViviOnyx"],
        week[5].isoformat(): ["Shiroe", "ViviOnyx"],
    }
    path = render_week(example_schedule, week, output_path="test_output.png")
    print(f"Zapisano: {path}")
