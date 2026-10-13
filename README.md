# Silnik Outlet — od zdjęcia do wpisu w arkuszu

Kompletny silnik pracy dla rozmów **Serwis / Reklamacje** w Codexie:
zdjęcia → identyfikacja produktu → wyszukiwanie Base i archiwum → czytelny
werdykt z zakupem i cenami → zgoda pracownika → wpis w arkuszu w osobnej rozmowie.
Główna rozmowa może w tym czasie szukać kolejnego produktu.

**Publiczny link do skopiowania:** https://github.com/SilesiaCorp/outlet-photo-engine

**Aktualizacja 2.2.0:** szybka propozycja najlepszego kandydata dotąd, potem
dalsze porównanie Base i archiwum. Numery zwrotów są pomocniczym tropem.
Przejście do kolejnego produktu potwierdza poprzednie dopasowanie.
[Szybkie wyszukiwanie](docs/FAST_SEARCH.md) · [aktualizacja na magazynie](docs/UPDATING.md).

## Start na firmowym komputerze

1. Pobierz repo: **Code → Download ZIP**, rozpakuj i otwórz folder w Codexie.
   Możesz również użyć:

   ```powershell
   git clone https://github.com/SilesiaCorp/outlet-photo-engine.git
   ```

2. Wklej poniższe polecenie do nowej rozmowy i dołącz zdjęcia:

   > Pracujesz jako Serwis / Reklamacje. Uruchom silnik z tego repo.
   > Przeczytaj AGENTS.md, docs/OPERATING_GUIDE.md, docs/CONVERSATION_FORMAT.md,
   > docs/DELEGATION.md i docs/SHEET_ENTRY.md. Rozpoznaj produkt ze zdjęć
   > i wyszukaj jego zamówienie w Base, w tym w archiwum, jeśli potrzeba.
   > Preferuj API i cache.
   > Sprawdzaj niezależne tropy równolegle; numery zwrotów są pomocnicze,
   > mogą być błędne i nie blokują dopasowania po produkcie. Na początku
   > pokaż najlepszego kandydata dotąd i kontynuuj sprawdzanie Base i archiwum.
   > Gdy przerwę poszukiwania lub przejdę do kolejnego produktu, przyjmij
   > ostatnio pokazane dopasowanie jako potwierdzone i przejdź dalej.
   > Uzupełnij dane proponowanej pozycji. Podaj siłę dowodów,
   > firmę zakupu, konto zakupowe, kupującą spółkę, cenę netto,
   > brutto, VAT i komplet pól arkusza. Po moim zatwierdzeniu konkretnego
   > wpisu utwórz osobną lokalną rozmowę do arkusza i przekazuj jej następne
   > zatwierdzone pozycje. W głównej rozmowie kontynuujemy wyszukiwanie.
   > Wpis do arkusza i utworzenie PZ traktuj jako dwa zakresy polecenia.

3. Codex sprawdza istniejący dostęp do Base i firmowego Google. Na każdym PC
   potrzebne są jego własne, już autoryzowane połączenia. Publiczne repo
   udostępnia cały silnik; dane firmowe wymagają właściwego konta.
   Szczegóły konfiguracji: [SETUP.md](docs/SETUP.md).

## Co jest w repo

| Część | Zawartość |
| --- | --- |
| [Silnik operacyjny](docs/OPERATING_GUIDE.md) | Identyfikacja po zdjęciu, API, cache, archiwum, trudne tropy, własność, wycena, zestawy i odzyskanie wyniku. |
| [Format konwersacji](docs/CONVERSATION_FORMAT.md) | Krótka lista wyników, kandydaci, najlepszy kandydat i pełne dane finansowe/pola arkusza. |
| [Szybki kandydat i dalsza weryfikacja](docs/FAST_SEARCH.md) | Niezależne tropy, pomocnicze RMA, najlepszy wynik dotąd i dalsze porównanie. |
| [Aktualizowanie silnika](docs/UPDATING.md) | Rozwój z komputera autora i pobranie nowej wersji na magazynie; bez utraty prywatnej kolejki. |
| [Odnoga do arkusza](docs/DELEGATION.md) | Kiedy utworzyć osobną rozmowę, jak przekazać zgodę i zadanie, jeden writer i powrót wyniku. |
| [Wpis do arkusza](docs/SHEET_ENTRY.md) | Mapowanie kolumn, typy API, duplikaty, notatki, formuły, zapis i dokładny odczyt wyniku. |
| [Pełna instrukcja źródłowa](docs/SHEET_INSTRUCTIONS.md) | Wszystkie sekcje 01–12 odczytane z INSTRUKCJI MAGAZYNU, również panel WarePilot i kolejka A–AB. |
| [Konfiguracja](configs/outlet-intake.json) | SP/TT, katalog i magazyny, znaczenie cen oraz reguły delegowania. Bez sekretów. |
| [Struktura arkusza](configs/sheet-schema.json) | Zweryfikowane nagłówki, rodzime formaty i walidacje. Przed zapisem ponownie czytamy żywy arkusz. |
| [Wyszukiwanie API](scripts/find_outlet_candidates.py) | Odczyty Base, prywatny indeks, pełny werdykt; nie tworzy stanu magazynowego. |
| [Plan i weryfikacja wpisu](scripts/prepare_sheet_entry.py) | Zatwierdzony manifest → precyzyjny batchUpdate → weryfikacja odczytu. |
| [Kolejka odnogi](scripts/outlet_queue.py) | Prywatny SQLite, trwałe OP, jedna rozmowa wykonawcza i kontrola duplikatów. |
| [Testy](tests/) | Dane umowne; identyfikacja, ceny, zgoda, typy arkusza, ponowienia i jeden writer. |

## Uruchomienie narzędzi

Python 3.11+, biblioteka standardowa; nie potrzeba płatnego API AI ani serwera OCR.
Zdjęcia odczytuje Codex w rozmowie. Skrypt przyjmuje rozpoznane oznaczenia.

```powershell
py -3 scripts/find_outlet_candidates.py --model "MODEL_Z_ETYKIETY" --ean "EAN_Z_ETYKIETY"
py -3 scripts/find_outlet_candidates.py --model "MODEL_Z_ETYKIETY" --return-number "NUMER_Z_PACZKI" --preview-only
py -3 scripts/find_outlet_candidates.py --model "MODEL_Z_ETYKIETY" --order-id NUMER_BL
py -3 -m unittest discover -s tests -v
```

Skrypty planowania same nie wysyłają zapisu do Sheets. Osobna rozmowa wykonuje
wygenerowane żądanie przez istniejący konektor Google i weryfikuje wynik.
Tworzenie rozmowy wymaga narzędzi Codex desktop opisanych w DELEGATION.md.
Repo nie tworzy nowych uprawnień, nie loguje automatycznie kont i nie ma tokenów.

Wersja **2.2.0**, zasady i wyszukiwanie sprawdzone **13.10.2026**;
struktura arkusza odczytana **12.10.2026**, przed zapisem sprawdzana ponownie.
Rzeczywiste zamówienia, zdjęcia magazynu, eksporty, manifesty i logi pozostają
prywatnie poza repo. Opis weryfikacji: [VERIFICATION.md](docs/VERIFICATION.md).
