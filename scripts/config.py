"""
Konfiguracja wczytywana ze zmiennych środowiskowych.
W GitHub Actions ustawiasz je jako Secrets (patrz README.md).
"""
import os

# --- Google Sheets ---
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
SHEET_ID = os.environ.get("SHEET_ID", "")
SHEET_WORKSHEET_NAME = os.environ.get("SHEET_WORKSHEET_NAME", "Harmonogram")

# --- Discord ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# --- Streamerzy ---
# klucz = DOKŁADNIE taka nazwa, jaka wpisywana jest w arkuszu (kolumny B, C...),
# value = ścieżka do pliku avatara w repo
STREAMERS = {
    "Shiroe": "assets/avatars/shiroe.png",
    "ViviOnyx": "assets/avatars/vivionyx.png",
}

# --- Wygląd ---
FONT_PATH = "assets/fonts/Roboto_SemiCondensed-SemiBold.ttf"  # podmień na własny (np. Oswald), patrz README
AVATAR_SIZE = 56
CELL_WIDTH = 220
CELL_HEIGHT = 220
HEADER_HEIGHT = 60
MARGIN = 12
COLOR_BG = (30, 32, 36, 255)
COLOR_CELL = (40, 43, 48, 255)
COLOR_CELL_TODAY = (54, 58, 66, 255)
COLOR_GRID = (60, 63, 70, 255)
COLOR_TEXT = (230, 230, 230, 255)
COLOR_TEXT_MUTED = (150, 150, 155, 255)

# --- Stan ---
STATE_FILE = "state/message_id.txt"

# --- Plik z danymi (fallback, patrz fetch_sheet.py) ---
LOCAL_DATA_FILE = "state/schedule_cache.json"
