"""
Renderuje tygodniowy "kalendarz" w stylu bracketu turniejowego:
ciemne teksturowane tło, neonowy tytuł na górze, a pod nim 7 wierszy
(Pon..Niedz) z naprzemiennymi bannerami-strzałkami (raz z prawej, raz
z lewej) wskazującymi na centralne kółko z avatarem/avatarami danego
dnia. Dni bez streamu dostają szare kółko + etykietę "BEZ STREAMKA"
z ikonką po przeciwnej stronie niż banner.

Kolory obwódki avatara per streamer - patrz RING_COLORS niżej.
"""
import io
import datetime as dt

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import config

DAY_NAMES_PL = [
    "PONIEDZIAŁEK", "WTOREK", "ŚRODA", "CZWARTEK", "PIĄTEK", "SOBOTA", "NIEDZIELA",
]

# --- Wymiary ---
# Bazowe wymiary są policzone dla płótna ~894px (poprzednia rozdzielczość).
# TARGET_SIZE ustawia docelowy rozmiar kwadratu (np. SZABLON.png = 2000px),
# a SCALE przelicza WSZYSTKIE rozmiary (czcionki, kółka, banery, marginesy)
# proporcjonalnie - dzięki temu układ się nie psuje przy zmianie rozdzielczości.
TARGET_SIZE = 2000
_BASE_REFERENCE_SIZE = 894
SCALE = TARGET_SIZE / _BASE_REFERENCE_SIZE


def S(value):
    """Skaluje wartość pikselową wg SCALE i zaokrągla do int."""
    return round(value * SCALE)


CANVAS_W = S(780)
MARGIN = S(24)
HEADER_H = S(170)
ROW_H = S(100)
CIRCLE_R = S(36)
BANNER_H = S(48)
BANNER_W_MIN = S(170)   # minimalna szerokość banera (dla krótkich nazw jak "SOBOTA")
BANNER_PAD_X = S(18)    # margines tekstu wewnątrz banera z każdej strony
BANNER_TIP_LEN = S(24)
GAP_CIRCLE_BANNER = S(16)
EMOTE_SIZE = S(40)

# --- Kolory ---
BG_BASE = (17, 18, 21, 255)
DOT_COLOR = (255, 255, 255, 42)
TITLE_CYAN = (64, 224, 240, 255)
TITLE_GLOW = (64, 224, 240, 130)
SUBTITLE_COLOR = (230, 230, 235, 255)
BANNER_FILL = (245, 245, 245, 255)
BANNER_OUTLINE = (12, 12, 12, 255)
BANNER_TEXT = (15, 15, 15, 255)
GRAY_CIRCLE = (110, 112, 118, 255)
GRAY_CIRCLE_OUTLINE = (150, 152, 158, 255)
NO_STREAM_TEXT = (235, 235, 238, 255)

# --- Obwódki avatarów per streamer (z prośby: #843935 ViviOnyx, #5c4f47 Shiroe) ---
RING_COLORS = {
    "ViviOnyx": (0x84, 0x39, 0x35, 255),
    "Shiroe": (0x5C, 0x4F, 0x47, 255),
}

# Font tytułu "STREAMY W TYM TYGODNIU" - osobny od reszty tekstów
TITLE_FONT_PATH = "assets/fonts/Anton-Regular.ttf"
BANNER_FONT_PATH = "assets/fonts/Roboto-Regular.ttf"
NO_STREAM_EMOTE_URL = "https://cdn.7tv.app/emote/01H6RWF1YR00065QRQ3BN9TC3P/3x.webp"
_emote_cache = None


def _get_no_stream_emote():
    global _emote_cache
    if _emote_cache is not None:
        return _emote_cache
    try:
        resp = requests.get(NO_STREAM_EMOTE_URL, timeout=10)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        _emote_cache = img
    except Exception as e:
        print(f"UWAGA: nie udało się pobrać emotki 'brak streamu' ({e}) - pomijam ikonę.")
        _emote_cache = False  # False = "próbowałem, nie wyszło" (odróżnij od None = jeszcze nie próbowano)
    return _emote_cache or None


def _load_font(size, path=None):
    try:
        return ImageFont.truetype(path or config.FONT_PATH, size)
    except OSError:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size
        )


def _draw_dot_texture(width, height):
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    spacing = S(30)
    half = S(3.2)  # połowa przekątnej rombu
    for y in range(0, height, spacing):
        offset = spacing // 2 if (y // spacing) % 2 else 0
        for x in range(-offset, width, spacing):
            draw.polygon(
                [(x, y - half), (x + half, y), (x, y + half), (x - half, y)],
                fill=DOT_COLOR,
            )
    return layer


def _draw_glow_title(base_img, text, subtitle, width):
    draw = ImageDraw.Draw(base_img)

    font_sub = _load_font(S(24))
    sub_bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    sub_w = sub_bbox[2] - sub_bbox[0]
    draw.text(
        ((width - sub_w) / 2 - sub_bbox[0], S(22)),
        subtitle, font=font_sub, fill=SUBTITLE_COLOR,
    )

    max_title_w = width - MARGIN * 2
    title_size = S(46)
    font_title = _load_font(title_size, path=TITLE_FONT_PATH)
    title_bbox = draw.textbbox((0, 0), text, font=font_title)
    while (title_bbox[2] - title_bbox[0]) > max_title_w and title_size > S(24):
        title_size -= S(2)
        font_title = _load_font(title_size, path=TITLE_FONT_PATH)
        title_bbox = draw.textbbox((0, 0), text, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (width - title_w) / 2 - title_bbox[0]
    title_y = S(64)

    # poświata: tekst rysowany na osobnej warstwie, rozmyty, doklejony pod ostrym tekstem
    glow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.text((title_x, title_y), text, font=font_title, fill=TITLE_GLOW)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(S(6)))
    base_img.alpha_composite(glow_layer)

    draw = ImageDraw.Draw(base_img)
    draw.text((title_x, title_y), text, font=font_title, fill=TITLE_CYAN)


def _draw_banner(draw, tip_x, y_center, text, font, points_left):
    """
    points_left=True  -> grot strzałki skierowany w LEWO (banner rozciąga się w prawo od grota)
    points_left=False -> grot skierowany w PRAWO (banner rozciąga się w lewo od grota)
    Szerokość banera dopasowana do długości tekstu (stała szerokość
    ucinała dłuższe nazwy dni, np. "PONIEDZIAŁEK").
    """
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    banner_w = max(BANNER_W_MIN, tw + BANNER_PAD_X * 2)

    half_h = BANNER_H / 2
    if points_left:
        tip = (tip_x, y_center)
        rect_near = tip_x + BANNER_TIP_LEN
        rect_far = rect_near + banner_w
    else:
        tip = (tip_x, y_center)
        rect_near = tip_x - BANNER_TIP_LEN
        rect_far = rect_near - banner_w

    points = [
        tip,
        (rect_near, y_center - half_h),
        (rect_far, y_center - half_h),
        (rect_far, y_center + half_h),
        (rect_near, y_center + half_h),
    ]
    draw.polygon(points, fill=BANNER_FILL, outline=BANNER_OUTLINE, width=S(3))

    text_center_x = (rect_near + rect_far) / 2
    draw.text(
        (text_center_x - tw / 2 - bbox[0], y_center - th / 2 - bbox[1]),
        text, font=font, fill=BANNER_TEXT,
    )
    return banner_w


def _paste_ringed_avatar(base_img, avatar_path, center_xy, radius, ring_color):
    size = radius * 2
    avatar = Image.open(avatar_path).convert("RGBA").resize((size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)

    ring_pad = S(5)
    ring_size = size + ring_pad * 2
    ring = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
    ring_draw = ImageDraw.Draw(ring)
    ring_draw.ellipse((0, 0, ring_size, ring_size), fill=ring_color)
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


def _draw_gray_circle(draw, center_xy, radius):
    draw.ellipse(
        (
            center_xy[0] - radius, center_xy[1] - radius,
            center_xy[0] + radius, center_xy[1] + radius,
        ),
        fill=GRAY_CIRCLE, outline=GRAY_CIRCLE_OUTLINE, width=S(2),
    )


def _draw_no_stream_label(base_img, draw, center_x, y_center, font):
    emote = _get_no_stream_emote()
    y = y_center - (EMOTE_SIZE / 2 if emote else 0) - S(12)

    if emote:
        emote_resized = emote.resize((EMOTE_SIZE, EMOTE_SIZE))
        base_img.paste(
            emote_resized,
            (int(center_x - EMOTE_SIZE / 2), int(y)),
            emote_resized,
        )
        text_y = y + EMOTE_SIZE + S(4)
    else:
        text_y = y_center - S(10)

    text = "BEZ STREAMKA"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((center_x - tw / 2 - bbox[0], text_y), text, font=font, fill=NO_STREAM_TEXT)


def render_week(schedule, week_dates, output_path="calendar.png"):
    """
    schedule: dict {YYYY-MM-DD: [nazwy_streamerow]}
    week_dates: lista 7 obiektów datetime.date, poniedziałek..niedziela
    """
    height = HEADER_H + ROW_H * len(week_dates) + MARGIN
    canvas_w = height  # proporcje 1:1 - płótno poszerzone do wysokości treści

    img = Image.new("RGBA", (canvas_w, height), BG_BASE)
    img.alpha_composite(_draw_dot_texture(canvas_w, height))

    subtitle = f"{week_dates[0].strftime('%d.%m')} - {week_dates[-1].strftime('%d.%m')}"
    _draw_glow_title(img, "STREAMY W TYM TYGODNIU", subtitle, canvas_w)

    draw = ImageDraw.Draw(img)
    font_banner = _load_font(S(20), path=BANNER_FONT_PATH)
    font_label = _load_font(S(16))

    center_x = canvas_w / 2

    for i, day in enumerate(week_dates):
        y_center = HEADER_H + i * ROW_H + ROW_H / 2
        banner_on_right = (i % 2 == 0)

        streamers_today = schedule.get(day.isoformat(), [])
        circle_extent = CIRCLE_R  # promień "zajętej" strefy na środku - rośnie przy 2 avatarach

        # --- avatar(y) / szare kółko na środku ---
        if streamers_today:
            if len(streamers_today) == 1:
                avatar_path = config.STREAMERS.get(streamers_today[0])
                ring = RING_COLORS.get(streamers_today[0], GRAY_CIRCLE)
                if avatar_path:
                    _paste_ringed_avatar(img, avatar_path, (center_x, y_center), CIRCLE_R, ring)
            else:
                offset = CIRCLE_R * 0.6
                small_r = int(CIRCLE_R * 0.85)
                circle_extent = offset + small_r  # dwa kółka sięgają dalej niż jedno - banery muszą to uwzględnić
                xs = [center_x - offset, center_x + offset]
                for name, cx in zip(streamers_today[:2], xs):
                    avatar_path = config.STREAMERS.get(name)
                    ring = RING_COLORS.get(name, GRAY_CIRCLE)
                    if avatar_path:
                        _paste_ringed_avatar(img, avatar_path, (cx, y_center), small_r, ring)
        else:
            _draw_gray_circle(draw, (center_x, y_center), CIRCLE_R)
            label_center_x = center_x - (CIRCLE_R + S(70)) if banner_on_right else center_x + (CIRCLE_R + S(70))
            _draw_no_stream_label(img, draw, label_center_x, y_center, font_label)

        # --- banner z dniem/datą (na przemian prawo/lewo) ---
        day_text = f"{DAY_NAMES_PL[i]} {day.strftime('%d.%m')}"
        if banner_on_right:
            tip_x = center_x + circle_extent + GAP_CIRCLE_BANNER
            _draw_banner(draw, tip_x, y_center, day_text, font_banner, points_left=True)
        else:
            tip_x = center_x - circle_extent - GAP_CIRCLE_BANNER
            _draw_banner(draw, tip_x, y_center, day_text, font_banner, points_left=False)

    img.convert("RGB").save(output_path)
    return output_path


if __name__ == "__main__":
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
