# Konfiguracja na innym komputerze

## Repo i Python

Pobierz zwykły publiczny adres z README. Klon zawiera wszystkie instrukcje,
kod i testy. Nie trzeba dostępu do wcześniejszego projektu Marketplace,
prywatnego checkpointu ani wiadomości z poprzedniego komputera.

Użyj Python 3.11+. Gdy `python` otwiera Microsoft Store, sprawdź `py -3`
albo narzędzie Codexa `load_workspace_dependencies` i użyj zwróconej ścieżki.
Nie utrwalaj ścieżki konkretnego użytkownika. Daty zamówień używają
`Europe/Warsaw`; środowisko musi mieć bazę IANA. Bundled Python Codexa ją
obsługuje. Jeżeli jej brak, użyj tego runtime albo uzgodnionego pakietu tzdata;
nie zastępuj strefy po cichu UTC. Nie ma automatycznej instalacji zależności.

## Base

Narzędzie czyta `BASELINKER_TOKEN` ze środowiska. Sprawdź obecność konfiguracji,
bez drukowania wartości. Token ustaw lokalnie przez istniejący mechanizm
sekretów na danym PC. Do odczytu wystarczy uprawniony token właściwego Base.
Nie wyciągaj tokenu z cookies, pamięci przeglądarki lub niepowiązanego profilu.

Pilot połączenia: `getInventories` i `getInventoryWarehouses`, potwierdź
`Projekt BELLA / 17463`. Przed jakimkolwiek ruchem ponownie sprawdź katalogi
i magazyny SP/TT z configs/outlet-intake.json. Numery są różnymi typami ID.
Dołączony adapter pozwala wyłącznie na odczyty.

Przy UI Base odczytaj istniejącą autoryzację właściciela na tym komputerze:
`%CODEX_HOME%/base-browser-owner-authorization.json`. Używaj istniejącej sesji
i dozwolonych narzędzi; instrukcja silnika nie zastępuje zgody ani logowania.

## Google i arkusz

1. Wykryj dostępne narzędzia Google Drive/Sheets.
2. `get_profile` musi potwierdzić firmowy adres `dsi.silesiaprotech@gmail.com`.
   `link_id` pochodzi z aktualnej listy połączeń, nie z repo.
3. Ustal arkusz przez lokalny `OUTLET_SPREADSHEET_ID` lub dokładne wyszukanie
   tytułu **SYSTEM REKLAMACJI I OUTLETU — SP / TT** na tym koncie.
   Przy kilku wynikach sprawdź metadane/źródło, nie wybieraj przypadkowej kopii.
4. Zapisz ID lokalnie poza repo. Odczytaj metadane: nazwy zakładek, sheetId,
   siatkę, locale i timeZone. Obecny układ: OUTLET, REKLAMACJE,
   INSTRUKCJA MAGAZYNU, STATYSTYKI, STANOWE DODAJ DO SM.
5. Odczytaj całą kartę instrukcji, małymi zakresami do ostatniej sekcji.
   Obserwacja 12.10.2026: 136 niepustych wierszy, sekcje 01–12.
   Kopia procedur w repo jest materiałem startowym; zmianę żywego źródła rozlicz.
6. Odczytaj aktualne nagłówki, rodzime komórki i reguły przed zapisem.
   Dawny arkusz OUTLETY 06.26 służy kontroli duplikatów, jeżeli nadal jest źródłem
   historii; jego ID ustaw lokalnie w `OUTLET_LEGACY_SPREADSHEET_ID`.

Brak firmowego Google zatrzymuje tylko krok zależny od arkusza. Wyszukiwanie
w Base może działać dalej. Nie inicjuj nowego logowania lub rozszerzenia
uprawnień samodzielnie. Zapisz zakres, hash, powód i warunek wznowienia w
lokalnym account-gated-backlog.md, bez sekretów.

## Odnoga Codexa i dane lokalne

Potrzebne narzędzia desktop: `create_thread`, `list_projects`,
`send_message_to_thread`, `read_thread`, `wait_threads`. Używaj ich aktualnych
schematów. Dostępność zależy od środowiska; nie imituj ich przez zmianę bazy
Codexa, plików sesji lub automatyczne kupowanie API.

Domyślna kolejka: `%LOCALAPPDATA%/Codex/outlet-photo-engine/jobs.sqlite3`
na Windows; odpowiedni lokalny katalog danych użytkownika na innym systemie.
Manifesty, zdjęcia, snapshoty i receipt przechowuj w sąsiednim prywatnym
katalogu przypadków. Obydwie rozmowy mają korzystać z tej samej lokalizacji
na tym samym hoście. Nie przesyłaj danych przez publiczny Git.

Po restarcie odczytaj kolejkę, właściciela i checkpoint. Nie zakładaj,
że nowy proces oznacza brak poprzedniego wpisu. Blokada lokalna nie jest
blokadą innych PC; jeden właściciel arkusza obowiązuje również organizacyjnie.

## Weryfikacja startu

```powershell
py -3 -m unittest discover -s tests -v
py -3 scripts/find_outlet_candidates.py --help
py -3 scripts/prepare_sheet_entry.py --help
py -3 scripts/outlet_queue.py --help
```

Następnie jeden celowany, read-only odczyt rzeczywistego produktu/zamówienia.
Pierwszy rzeczywisty wpis jest pilotem tylko po konkretnej zgodzie pracownika;
nie dodawaj wiersza testowego do produkcji, aby sprawdzić instalację.

## Aktualizacje na magazynie

Silnik rozwijamy w kanonicznym repo. Na tym PC pobieraj nową wersję z tego
samego adresu i ponownie odczytaj zmienione reguły w aktywnej rozmowie.
Pełna procedura Git/ZIP i skrypt: [UPDATING.md](UPDATING.md).
