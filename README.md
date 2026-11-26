# Rozkład Jazdy StreamHouse

Google Sheets → PNG → Discord. GitHub Actions sprawdza harmonogram codziennie o 16:00 czasu polskiego. W niedzielę wybiera następny tydzień, w pozostałe dni aktualny. Bez zmian nie wysyła wiadomości. Przy zmianie publikuje nowy rozkład z pingiem obu skonfigurowanych ról, zapisuje ID i usuwa poprzednią wiadomość (bez przypinania).

## Konfiguracja
- Arkusz `Harmonogram`: kolumna A w formacie DD.MM.RRRR, kolejne kolumny to nazwy streamerów z `scripts/config.py`. Co najmniej jeden wiersz dla danego tygodnia jest wymagany; jawnie puste dni można zapisać jako samą datę.
- Secrets Actions: `GOOGLE_SERVICE_ACCOUNT_JSON`, `SHEET_ID`, `DISCORD_WEBHOOK_URL`.
- Konto usługi Google potrzebuje dostępu tylko do odczytu. Webhook musi należeć do kanału publikacji, mieć możliwość wspominania wskazanych ról i być tym samym webhookiem, który wysłał poprzednią wiadomość.
- Stan jest zapisywany w `state/publication.json`; pierwszy przebieg korzysta z dotychczasowego `state/message_id.txt`.
- Ręczny workflow: wybierz tydzień i wyłącz dry-run tylko przy faktycznej publikacji. Podgląd jest dostępny jako artefakt.
- Testy: `python -m unittest discover -s tests`. Lokalny podgląd: `python scripts/main.py --dry-run`.

Licencja MIT.
