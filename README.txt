# Discord Stream Calendar

Bot generuje obraz kalendarza tygodnia (Pon-Niedz) z awatarami streamerów
przypisanych do danego dnia i wysyła go jako przypiętą, cyklicznie
edytowaną wiadomość na Discordzie. Źródło danych: Google Sheets.
Uruchamiany raz na dobę przez GitHub Actions.

## Krok 1 — Google Sheets

1. Stwórz nowy arkusz Google Sheets.
2. Nazwij zakładkę **Harmonogram** (albo zmień `SHEET_WORKSHEET_NAME`
   w `scripts/config.py`).
3. W pierwszym wierszu wpisz nagłówki dokładnie tak:

   | data | Bartek | Streamer2 |
   |------|--------|-----------|

   `data` w formacie `RRRR-MM-DD` (np. `2026-08-15`). Nazwy kolumn
   streamerów muszą się zgadzać 1:1 z `config.STREAMERS` (patrz Krok 4).
4. W kolejnych wierszach zaznaczaj `TRUE`/`FALSE` (albo puste = brak
   streamu) dla każdego dnia i streamera.
5. Skopiuj **ID arkusza** z URL:
   `https://docs.google.com/spreadsheets/d/TU_JEST_ID/edit` — to jest
   Twój `SHEET_ID`.

https://docs.google.com/spreadsheets/d/1pr7uRXrT_8wj3CLrOij_DdsIysk2_FnTGYSL9exiqaM/

## Krok 2 — Google Service Account (dostęp bota do arkusza)

1. Wejdź na [Google Cloud Console](https://console.cloud.google.com/).
2. Stwórz nowy projekt (albo użyj istniejącego).
3. Włącz **Google Sheets API** (menu: APIs & Services → Library).
4. Stwórz **Service Account** (APIs & Services → Credentials → Create
   Credentials → Service Account).
5. Wejdź w ten service account → zakładka **Keys** → **Add Key** →
   **JSON**. Pobierze się plik `.json` — to jest Twój
   `GOOGLE_SERVICE_ACCOUNT_JSON` (cała zawartość pliku).
6. W pliku JSON znajdź pole `client_email` (coś w stylu
   `nazwa@projekt.iam.gserviceaccount.com`).
7. Otwórz swój arkusz Google Sheets → **Udostępnij** → wklej ten
   e-mail jako edytora (wystarczy odczyt, ale edytor jest prostszy).

## Krok 3 — Discord Webhook

1. Discord → ustawienia kanału, na którym ma wisieć kalendarz →
   **Integracje** → **Webhooks** → **Nowy webhook**.
2. Skopiuj **Webhook URL** — to jest Twój `DISCORD_WEBHOOK_URL`.

https://discord.com/api/webhooks/1535612658441658532/sn8YhDkgBmvrTICCmODtcHliS2h5QS17oFTtYutrE54YrstmVKWVAvrpBfwII8waW4Ch

## Krok 4 — Avatary streamerów

1. Wrzuć pliki `.png` (najlepiej kwadratowe, min. 256×256) do
   `assets/avatars/`, np. `bartek.png`, `streamer2.png`.
2. W `scripts/config.py` zaktualizuj słownik `STREAMERS`:

   ```python
   STREAMERS = {
       "Bartek": "assets/avatars/bartek.png",
       "Streamer2": "assets/avatars/streamer2.png",
   }
   ```

   Klucze (`"Bartek"`, `"Streamer2"`) muszą być identyczne z nazwami
   kolumn w arkuszu z Kroku 1.

## Krok 5 — (opcjonalnie) własny font

Domyślnie użyty jest DejaVu Sans Bold (dołączony w
`assets/fonts/DejaVuSans-Bold.ttf`). Jeśli chcesz swój font (np.
Oswald, którego używasz na overlayach PanSzczesniaka):

1. Wrzuć plik `.ttf` do `assets/fonts/`.
2. Zmień `FONT_PATH` w `scripts/config.py` na nową ścieżkę.

## Krok 6 — Repo i sekrety GitHub

1. Wrzuć cały ten folder jako nowe repo na GitHub (może być prywatne).
2. W repo: **Settings → Secrets and variables → Actions → New
   repository secret**, dodaj trzy sekrety:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` — cała zawartość pliku JSON z Kroku 2
   - `SHEET_ID` — z Kroku 1
   - `DISCORD_WEBHOOK_URL` — z Kroku 3
3. Upewnij się, że **Settings → Actions → General → Workflow
   permissions** ma ustawione **Read and write permissions** (bot
   commituje `state/message_id.txt` z powrotem do repo).

## Krok 7 — Pierwsze uruchomienie

1. Zakładka **Actions** w repo → wybierz workflow **"Aktualizacja
   kalendarza streamów"** → **Run workflow** (uruchomienie ręczne,
   nie trzeba czekać na cron).
2. Sprawdź, czy na Discordzie pojawiła się nowa wiadomość z obrazkiem.
3. **Przypnij tę wiadomość ręcznie** (prawy klik → Przypnij
   wiadomość). Webhook nie ma uprawnień, żeby zrobić to sam — ale
   każde kolejne uruchomienie EDYTUJE tę samą wiadomość (nie tworzy
   nowej), więc pozostanie przypięta.
4. Od teraz workflow leci automatycznie codziennie o 5:00 UTC
   (7:00 PL zimą / 6:00 PL w lecie — jeśli chcesz stałą godzinę PL,
   dodaj drugi wpis `cron` przesunięty o godzinę i zostaw oba —
   niepotrzebne uruchomienie i tak tylko nadpisze ten sam obrazek).

## Testowanie lokalne (bez GitHub Actions)

```bash
pip install -r requirements.txt
export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat sciezka/do/klucza.json)"
export SHEET_ID="twoje_id_arkusza"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python scripts/main.py
```

Sam render bez wysyłki (przykładowe dane, zapisze `test_output.png`):

```bash
cd scripts && python render_calendar.py
```

## Struktura projektu

```
.github/workflows/update_calendar.yml   # cron 24h + workflow_dispatch
scripts/
  config.py            # cała konfiguracja (streamerzy, kolory, wymiary)
  fetch_sheet.py        # Google Sheets -> dane bieżącego tygodnia
  render_calendar.py    # dane -> PNG (siatka 7 dni + kółka avatarów)
  update_discord.py     # PNG -> webhook (POST pierwszy raz, potem PATCH)
  main.py               # spina powyższe w jeden przebieg
assets/
  avatars/               # pliki .png streamerów
  fonts/                 # font(y) użyte w renderze
state/
  message_id.txt         # ID edytowanej wiadomości (auto-zarządzane)
requirements.txt
```

## Znane ograniczenia

- Odświeżanie raz na dobę — zmiana w arkuszu widoczna dopiero
  następnego dnia (albo po ręcznym `workflow_dispatch`).
- Literówka w nazwie kolumny streamera w arkuszu = ten streamer
  po cichu znika z kalendarza (brak walidacji/błędu).
- Webhook nie może sam pinować wiadomości — pierwsze przypięcie
  zawsze ręczne.
