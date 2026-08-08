"""
Pobiera harmonogram z Google Sheets i zwraca dane dla NASTĘPNEGO
tygodnia (poniedziałek-niedziela) względem dnia uruchomienia.
Skrypt jest odpalany raz w tygodniu, w niedzielę po południu (patrz
.github/workflows/update_calendar.yml), więc "następny tydzień" =
tydzień, który zaczyna się jutro.

Format arkusza (BEZ wiersza nagłówka - dane od wiersza 1):

    A            B          C
    10.08.2026   Shiroe
    11.08.2026   ViviOnyx
    24.08.2026   ViviOnyx   Shiroe

Kolumna A: data w formacie DD.MM.RRRR.
Kolumny B, C, D...: nazwy streamerów, którzy tego dnia streamują
(dowolna liczba kolumn, puste komórki pomijane). Nazwy muszą się
DOKŁADNIE zgadzać z kluczami w config.STREAMERS.
"""
import json
import datetime as dt

import gspread
from google.oauth2.service_account import Credentials

import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

DATE_FORMAT = "%d.%m.%Y"  # np. 10.08.2026


def _get_client():
    creds_dict = json.loads(config.GOOGLE_SERVICE_ACCOUNT_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def _current_week_range(today=None):
    """
    Zwraca listę 7 dat (poniedziałek..niedziela) NASTĘPNEGO tygodnia
    względem `today` (domyślnie dzisiaj). Nazwa funkcji zostaje
    (_current_week_range) żeby nie trzeba było zmieniać main.py -
    zwraca po prostu inny tydzień niż poprzednio.
    """
    today = today or dt.date.today()
    this_monday = today - dt.timedelta(days=today.weekday())
    next_monday = this_monday + dt.timedelta(days=7)
    return [next_monday + dt.timedelta(days=i) for i in range(7)]


def _parse_date(raw_value):
    """Parsuje DD.MM.RRRR -> date. Zwraca None jeśli nie da się sparsować."""
    raw_value = str(raw_value).strip()
    if not raw_value:
        return None
    try:
        return dt.datetime.strptime(raw_value, DATE_FORMAT).date()
    except ValueError:
        return None


def _verify_sheet_access(client):
    """
    Wykonuje prosty request do arkusza i - jeśli coś jest nie tak - wypisuje
    CZYTELNY powód zamiast pozwolić gspread wybuchnąć na próbie
    zdekodowania pustej/nie-JSON-owej odpowiedzi jako JSON.
    """
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{config.SHEET_ID}?fields=properties.title"
    resp = client.session.get(url)
    if resp.status_code != 200:
        print("=" * 60)
        print(f"BŁĄD dostępu do arkusza: HTTP {resp.status_code}")
        print(f"Treść odpowiedzi: {resp.text[:500]!r}")
        print(f"SHEET_ID użyty w requeście: {config.SHEET_ID!r}")
        print("Sprawdź w tej kolejności:")
        print("  1) SHEET_ID - czy to sam ID, nie cały URL i bez spacji/newline?")
        print("  2) Czy Google Sheets API jest włączone w projekcie Cloud?")
        print("  3) Czy arkusz jest udostępniony e-mailowi service account")
        print("     (client_email z pliku JSON) jako Edytujący?")
        print("=" * 60)
        resp.raise_for_status()


def fetch_week_schedule():
    """
    Zwraca dict: {data (str YYYY-MM-DD): [lista_streamerow_ktorzy_streamuja]}
    dla każdego z 7 dni następnego tygodnia (nawet jeśli pusty).
    """
    week_dates = _current_week_range()
    week_dates_set = set(week_dates)
    result = {d.isoformat(): [] for d in week_dates}

    known_streamers = set(config.STREAMERS.keys())

    client = _get_client()
    _verify_sheet_access(client)
    sheet = client.open_by_key(config.SHEET_ID).worksheet(config.SHEET_WORKSHEET_NAME)
    rows = sheet.get_all_values()  # surowe wiersze, bez zakładania nagłówka

    for row in rows:
        if not row:
            continue
        day = _parse_date(row[0])
        if day is None or day not in week_dates_set:
            continue  # zły format daty albo spoza bieżącego tygodnia

        for cell in row[1:]:
            name = str(cell).strip()
            if not name:
                continue
            if name not in known_streamers:
                print(
                    f"UWAGA: '{name}' w wierszu z datą {row[0]} nie występuje "
                    f"w config.STREAMERS - pomijam. Sprawdź literówkę."
                )
                continue
            result[day.isoformat()].append(name)

    return result


if __name__ == "__main__":
    data = fetch_week_schedule()
    print(json.dumps(data, indent=2, ensure_ascii=False))
