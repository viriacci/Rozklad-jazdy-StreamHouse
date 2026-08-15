"""
Renderuje tygodniowy harmonogram na bazie gotowych assetow graficznych
(zamiast rysowac wszystko proceduralnie):

  assets/bg1.png - tlo (grzybki, kaczka, ksiazki) - UZYWANE 1:1 jako baza
  assets/4.png   - warstwa "edycyjna": zawiera GOTOWE pigulki dni (PON/WT/...)
                   + brazowe kolka (TYLKO wskazniki pozycji - NIGDY nie
                   trafiaja do finalnego obrazka) + "widmowy" tytul/date
                   (tez tylko wskazniki pozycji/rozmiaru czcionki)
  assets/4x.png  - emotka "brak streamu" (lokalny plik, bez pobierania z sieci)

Pozycje pigulek i kolek zostaly ZMIERZONE programowo z 4.png (wykrywanie
plam koloru), nie odgadniete na oko - patrz stale nizej.

UKLAD (ustalony na podstawie 5.png-referencji i mockupu, POPRAWIONE wg
oznaczen 1/2 na circle-placeholderach):
  - Dwie STALE pozycje x na kazdy dzien: LEWA (x=875) i PRAWA (x=1124).
  - AVATARY: ViviOnyx zawsze w LEWYM slocie, Shiroe zawsze w PRAWYM
    slocie, niezaleznie od strony pigulki danego dnia. Jesli tylko
    jeden streamer, idzie w swoj staly slot, drugi slot zostaje pusty.
  - 0 streamerow danego dnia: tekst "BEZ STREAMKA" zawsze w LEWYM slocie,
    emotka zawsze w PRAWYM (ustalone z 5.png, niezalezne od strony pigulki).
"""
import datetime as dt

from PIL import Image, ImageDraw, ImageFont

import config

# --- Pliki assetow ---
BG_PATH = "assets/bg1.png"
EDITORIAL_LAYER_PATH = "assets/4.png"
EMOTE_PATH = "assets/4x.png"
TITLE_FONT_PATH = "assets/fonts/Anton-Regular.ttf"

CANVAS_SIZE = 2000

# --- Zmierzone wspolrzedne (ze skryptu analizujacego 4.png) ---
# Kolejnosc dni: poniedzialek .. niedziela
DAY_ROW_Y = [510, 712, 919, 1121, 1326, 1533, 1738]
COL_X_LEFT = 875
COL_X_RIGHT = 1124
CIRCLE_R = 92

# Pigulki dni: (center_y, center_x, polowa_szerokosci, polowa_wysokosci)
PILL_HALF_W = 153
PILL_HALF_H = 92
PILL_CENTERS = [
    (510, 509),    # PON
    (712, 1491),   # WT
    (919, 509),    # SR
    (1121, 1491),  # CZW
    (1326, 509),   # PT
    (1533, 1491),  # SOB
    (1738, 509),   # NIEDZ
]

# Tytul i data - zmierzone bbox "widmowego" tekstu w 4.png
DATE_Y_CENTER = 104
TITLE_Y_CENTER = 276
TITLE_MAX_WIDTH = 1450  # z marginesem wzgledem zmierzonych 1422px

# "BEZ STREAMKA" + emotka - zmierzone z 5.png (referencyjny mockup slotu)
NO_STREAM_TEXT_SIZE = (223, 90)   # w x h dwoch linii tekstu
EMOTE_SIZE = (164, 111)           # w x h

RING_COLORS = {
    "ViviOnyx": (0x84, 0x39, 0x35, 255),
    "Shiroe": (0x5C, 0x4F, 0x47, 255),
}
FALLBACK_RING = (110, 112, 118, 255)

# Stale pozycje avatarow: ViviOnyx zawsze lewo, Shiroe zawsze prawo,
# niezaleznie od strony pigulki danego dnia.
FIXED_SLOT_X = {
    "ViviOnyx": COL_X_LEFT,
    "Shiroe": COL_X_RIGHT,
}

WHITE = (255, 255, 255, 255)

_emote_cache = None


def _get_emote():
    global _emote_cache
    if _emote_cache is None:
        _emote_cache = Image.open(EMOTE_PATH).convert("RGBA")
    return _emote_cache


def _load_font(size, path=TITLE_FONT_PATH):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size
        )


def _fit_font(draw, text, max_width, start_size, min_size=20):
    size = start_size
    font = _load_font(size)
    while size > min_size:
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font, bbox
        size -= 2
        font = _load_font(size)
    return font, draw.textbbox((0, 0), text, font=font)


def _draw_centered_text(draw, text, center_x, center_y, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((center_x - w / 2 - bbox[0], center_y - h / 2 - bbox[1]), text, font=font, fill=WHITE)


def _build_pills_layer():
    """Wycina TYLKO pigulki dni z 4.png (pomija brazowe kolka i widmowy tekst)."""
    editorial = Image.open(EDITORIAL_LAYER_PATH).convert("RGBA")
    layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    for cy, cx in PILL_CENTERS:
        box = (cx - PILL_HALF_W, cy - PILL_HALF_H, cx + PILL_HALF_W, cy + PILL_HALF_H)
        crop = editorial.crop(box)
        layer.paste(crop, box[:2], crop)
    return layer


def _paste_ringed_avatar(base_img, avatar_path, center_xy, radius, ring_color):
    size = radius * 2
    avatar = Image.open(avatar_path).convert("RGBA").resize((size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)

    ring_pad = 5
    ring_size = size + ring_pad * 2
    ring = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, ring_size, ring_size), fill=ring_color)
    base_img.paste(
        ring,
        (int(center_xy[0] - ring_size / 2), int(center_xy[1] - ring_size / 2)),
        ring,
    )
    base_img.paste(
        avatar,
        (int(center_xy[0] - size / 2), int(center_xy[1] - size / 2)),
        mask,
    )


def _draw_no_stream_slot(base_img, draw, text_center, emote_center, font):
    line1, line2 = "BEZ", "STREAMKA"
    bbox1 = draw.textbbox((0, 0), line1, font=font)
    bbox2 = draw.textbbox((0, 0), line2, font=font)
    h1 = bbox1[3] - bbox1[1]
    h2 = bbox2[3] - bbox2[1]
    gap = 6
    total_h = h1 + gap + h2
    top = text_center[1] - total_h / 2
    _draw_centered_text(draw, line1, text_center[0], top + h1 / 2, font)
    _draw_centered_text(draw, line2, text_center[0], top + h1 + gap + h2 / 2, font)

    emote = _get_emote().resize(EMOTE_SIZE)
    ex = int(emote_center[0] - EMOTE_SIZE[0] / 2)
    ey = int(emote_center[1] - EMOTE_SIZE[1] / 2)
    base_img.paste(emote, (ex, ey), emote)


def render_week(schedule, week_dates, output_path="calendar.png"):
    img = Image.open(BG_PATH).convert("RGBA").resize((CANVAS_SIZE, CANVAS_SIZE))
    img.alpha_composite(_build_pills_layer())
    draw = ImageDraw.Draw(img)

    date_text = f"{week_dates[0].strftime('%d.%m.')} - {week_dates[-1].strftime('%d.%m.')}"
    date_font, _ = _fit_font(draw, date_text, 600, 40)
    _draw_centered_text(draw, date_text, CANVAS_SIZE / 2, DATE_Y_CENTER, date_font)

    title_text = "TYGODNIOWY ROZKŁAD JAZDY"
    title_font, _ = _fit_font(draw, title_text, TITLE_MAX_WIDTH, 100)
    _draw_centered_text(draw, title_text, CANVAS_SIZE / 2, TITLE_Y_CENTER, title_font)

    no_stream_font, _ = _fit_font(draw, "STREAMKA", NO_STREAM_TEXT_SIZE[0], 44)

    for i, day in enumerate(week_dates):
        y = DAY_ROW_Y[i]
        streamers_today = schedule.get(day.isoformat(), [])

        if not streamers_today:
            _draw_no_stream_slot(
                img, draw,
                text_center=(COL_X_LEFT, y),
                emote_center=(COL_X_RIGHT, y),
                font=no_stream_font,
            )
        else:
            # ViviOnyx zawsze w lewym slocie, Shiroe zawsze w prawym,
            # niezaleznie od strony pigulki danego dnia
            for name in streamers_today[:2]:
                slot_x = FIXED_SLOT_X.get(name, COL_X_LEFT)
                avatar_path = config.STREAMERS.get(name)
                ring = RING_COLORS.get(name, FALLBACK_RING)
                if avatar_path:
                    _paste_ringed_avatar(img, avatar_path, (slot_x, y), CIRCLE_R, ring)

    img.convert("RGB").save(output_path)
    return output_path


if __name__ == "__main__":
    monday = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
    week = [monday + dt.timedelta(days=i) for i in range(7)]
    example_schedule = {
        week[0].isoformat(): ["Shiroe"],
        week[1].isoformat(): [],
        week[2].isoformat(): ["Shiroe", "ViviOnyx"],
        week[4].isoformat(): [],
        week[5].isoformat(): ["ViviOnyx"],
    }
    path = render_week(example_schedule, week, output_path="test_new_design.png")
    print(f"Zapisano: {path}")
