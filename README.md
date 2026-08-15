# 📅 Rozkład Jazdy StreamHouse

Bot, który automatycznie generuje obrazek z tygodniowym harmonogramem streamów (w stylu kalendarza z awatarami streamerów) i wysyła go jako **przypiętą, cyklicznie aktualizowaną wiadomość na Discordzie**. Dane pobierane są z Google Sheets, a całość odpala się automatycznie przez GitHub Actions — bez konieczności trzymania własnego serwera.

---

## Jak to działa (w skrócie)

```
Google Sheets (harmonogram)
        │
        ▼
 fetch_sheet.py  ──►  render_calendar.py  ──►  update_discord.py
 (pobiera dane)       (generuje PNG)           (wysyła/edytuje wiadomość)
```

1. **`fetch_sheet.py`** łączy się z Google Sheets przez service account i pobiera z arkusza `Harmonogram` listę streamerów przypisanych do każdego dnia nadchodzącego tygodnia.
2. **`render_calendar.py`** nakłada te dane na gotowy szablon graficzny (`assets/bg1.png` + `assets/4.png`) — wstawia pigułki dni, awatary streamerów w kółkach z kolorową obwódką (albo tekst „BEZ STREAMKA” + emotkę, jeśli danego dnia nikt nie streamuje) — i zapisuje wynik jako `calendar.png`.
3. **`update_discord.py`** wysyła ten obrazek na Discorda przez webhook. Jeśli to pierwsze uruchomienie — tworzy nową wiadomość (trzeba ją **ręcznie przypiąć** raz, bo webhooki nie mają do tego uprawnień). Przy każdym kolejnym uruchomieniu skrypt **edytuje tę samą wiadomość** zamiast tworzyć nową, więc pozostaje przypięta.
4. Całość spina **`main.py`**, a **GitHub Actions** (`.github/workflows/main.yml`) odpala go automatycznie w niedzielę o 14:00 UTC (16:00 czasu polskiego latem / 15:00 zimą) — czyli wysyła harmonogram na *nadchodzący* tydzień.

---

## Struktura repozytorium

```
.
├── scripts/
│   ├── main.py              # spina cały przepływ w jedno uruchomienie
│   ├── config.py             # konfiguracja: streamerzy, sekrety ze zmiennych środowiskowych
│   ├── fetch_sheet.py        # Google Sheets -> dane tygodnia
│   ├── render_calendar.py    # dane -> gotowy obrazek PNG (aktualnie używana wersja)
│   └── update_discord.py     # PNG -> webhook Discorda (POST/PATCH)
├── render_calendar.py        # STARSZA/alternatywna wersja renderu (styl "bracket turniejowy")
├── assets/
│   ├── bg1.png, 4.png, 4x.png, ...   # tło i warstwy graficzne szablonu
│   ├── avatars/               # zdjęcia profilowe streamerów
│   └── fonts/                 # fonty użyte w renderze
├── state/
│   └── message_id.txt         # ID edytowanej wiadomości na Discordzie (zarządzane automatycznie)
├── .github/workflows/main.yml # definicja harmonogramu i kroków GitHub Actions
└── requirements.txt           # zależności Pythona
```

> ⚠️ **Uwaga:** w repo są dwa pliki `render_calendar.py` — aktywny, produkcyjny znajduje się w `scripts/render_calendar.py` i jest tym, który realnie wywołuje `main.py`. Plik `render_calendar.py` w katalogu głównym to starsza wersja wizualna (styl bannerów-strzałek) i **nie jest obecnie używana** przez workflow.

---

## Wymagania

- Konto Google z arkuszem Google Sheets zawierającym harmonogram.
- Google Cloud Service Account z dostępem do Google Sheets API.
- Webhook na kanale Discorda, gdzie ma się pojawiać kalendarz.
- Repozytorium GitHub (może być prywatne) z uprawnieniami do zapisu przez Actions.

---

## Konfiguracja krok po kroku

### 1. Arkusz Google Sheets

Stwórz arkusz i zakładkę o nazwie **`Harmonogram`** (albo zmień to w `scripts/config.py` → `SHEET_WORKSHEET_NAME`).

Format wierszy — **bez nagłówka**, dane od pierwszego wiersza:

| A (data)     | B          | C          |
|--------------|------------|------------|
| 10.08.2026   | Shiroe     |            |
| 11.08.2026   | ViviOnyx   |            |
| 24.08.2026   | ViviOnyx   | Shiroe     |

- Kolumna A: data w formacie `DD.MM.RRRR`.
- Kolumny B, C, D...: nazwy streamerów danego dnia (dowolna liczba kolumn, puste komórki są pomijane).
- Nazwy **muszą dokładnie** zgadzać się z kluczami w `config.STREAMERS` (wielkość liter też ma znaczenie) — literówka powoduje ciche pominięcie streamera z ostrzeżeniem w logach.

Skopiuj **ID arkusza** z adresu URL:
`https://docs.google.com/spreadsheets/d/TU_JEST_ID/edit`

### 2. Google Service Account

1. Wejdź na [Google Cloud Console](https://console.cloud.google.com/).
2. Stwórz projekt (lub użyj istniejącego) i włącz **Google Sheets API**.
3. Utwórz **Service Account** → zakładka **Keys** → **Add Key → JSON**. Pobrany plik to Twój `GOOGLE_SERVICE_ACCOUNT_JSON`.
4. Skopiuj z niego pole `client_email`.
5. W arkuszu Google Sheets kliknij **Udostępnij** i dodaj ten e-mail jako edytora.

### 3. Webhook Discorda

1. Ustawienia kanału Discorda → **Integracje** → **Webhooks** → **Nowy webhook**.
2. Skopiuj **Webhook URL** — to Twój `DISCORD_WEBHOOK_URL`.

### 4. Awatary i streamerzy

1. Wrzuć kwadratowe pliki `.png` (min. 256×256) do `assets/avatars/`.
2. Zaktualizuj słownik w `scripts/config.py`:

```python
STREAMERS = {
    "Shiroe": "assets/avatars/shiroe.png",
    "ViviOnyx": "assets/avatars/vivionyx.png",
}
```

Klucze muszą być identyczne z nazwami wpisywanymi w arkuszu.

Kolor obwódki awatara każdego streamera ustawia się w `scripts/render_calendar.py` w słowniku `RING_COLORS`. Domyślnie:
- `ViviOnyx` → `#843935`
- `Shiroe` → `#5C4F47`

Pozycja awatara na obrazku jest **stała per streamer** (nie zależy od tego, po której stronie jest pigułka dnia): `ViviOnyx` zawsze po lewej, `Shiroe` zawsze po prawej — patrz słownik `FIXED_SLOT_X` w `render_calendar.py`.

### 5. Sekrety w repozytorium GitHub

**Settings → Secrets and variables → Actions → New repository secret**, dodaj:

| Nazwa sekretu | Wartość |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | cała zawartość pliku JSON z kroku 2 |
| `SHEET_ID` | ID arkusza z kroku 1 |
| `DISCORD_WEBHOOK_URL` | webhook z kroku 3 |

Upewnij się też, że **Settings → Actions → General → Workflow permissions** ma ustawione **Read and write permissions** — bot commituje `state/message_id.txt` z powrotem do repo po każdym uruchomieniu.

### 6. Pierwsze uruchomienie

1. Zakładka **Actions** → workflow **„Aktualizacja kalendarza streamów”** → **Run workflow** (uruchomienie ręczne).
2. Sprawdź, czy na Discordzie pojawiła się wiadomość z obrazkiem.
3. **Przypnij ją ręcznie** (prawy klik → Przypnij wiadomość) — webhook nie ma do tego uprawnień, ale kolejne uruchomienia będą tylko edytować tę samą wiadomość, więc pozostanie przypięta.

Od teraz workflow leci automatycznie co tydzień, zgodnie z harmonogramem `cron` w `.github/workflows/main.yml`.

---

## Testowanie lokalne

```bash
pip install -r requirements.txt

export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat sciezka/do/klucza.json)"
export SHEET_ID="twoje_id_arkusza"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

python scripts/main.py
```

Sam render obrazka bez wysyłki na Discorda (na przykładowych danych, zapisuje `test_new_design.png`):

```bash
cd scripts
python render_calendar.py
```

---

## Znane ograniczenia

- Workflow odpala się raz w tygodniu (niedziela) — zmiana w arkuszu po wysyłce będzie widoczna dopiero przy kolejnym uruchomieniu, chyba że odpalisz go ręcznie (`workflow_dispatch`).
- Literówka w nazwie streamera w arkuszu = ten streamer po cichu znika z obrazka (sprawdź logi Actions — pojawi się tam ostrzeżenie).
- Webhook nie może sam przypiąć wiadomości na Discordzie — pierwsze przypięcie zawsze wymaga ręcznej akcji.
- Pozycje elementów graficznych (pigułki dni, sloty na awatary) są zaszyte na sztywno jako współrzędne w pikselach, zmierzone pod konkretne pliki w `assets/`. Podmiana tła/szablonu na inny wymaga ponownego zmierzenia i zaktualizowania stałych na górze `scripts/render_calendar.py`.

---

## Licencja

Brak zdefiniowanej licencji — repozytorium prywatne/projektowe. Jeśli chcesz je udostępnić publicznie, rozważ dodanie pliku `LICENSE`.
