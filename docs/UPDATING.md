# Aktualizacje z komputera autora na komputer magazynowy

Repo kanoniczne: **https://github.com/SilesiaCorp/outlet-photo-engine**.
Ten zwykły adres pozostaje ten sam przy kolejnych wydaniach. Komputer
magazynowy pobiera jego domyślną gałąź; nie potrzebuje dostępu do większego
projektu Marketplace ani prywatnych repozytoriów.

## Na komputerze autora — rozwój silnika

1. Sprawdź Git, gałąź, origin, lokalne zmiany i aktualny remote. Zachowaj
   cudze zmiany. Nie uruchamiaj drugiego writera tego samego kodu.
2. Zlecone nowe informacje wpisz raz do właściwego dokumentu domenowego,
   parsera lub konfiguracji. Potwierdź regułę u źródła. Przykłady i testy
   mają dane umowne; prawdziwy przypadek pozostaje w prywatnym checkpointcie.
3. Zmień najmniejszy potrzebny zakres, dodaj adekwatny test regresji.
   Przy zmianie wyszukiwania zmierz czas do pierwszego kandydata i żądania API.
4. Uzupełnij CHANGELOG.md i wersję w pyproject.toml / src/outlet_engine/__init__.py.
   Testuj to, co się zmieniło, potem sprawdź zgodność całego małego silnika:

   ```powershell
   py -3 -m unittest discover -s tests -v
   git diff --check
   ```

5. Przed publikacją sprawdź zakres plików, odnośniki, JSON i brak sekretów,
   danych zamówień, zdjęć oraz produkcyjnych manifestów/receipt.
6. Commit/push wykonaj w zakresie zleconej aktualizacji na `work/<osoba>/<temat>`.
   Domyślna gałąź wydania jest już gałęzią work. Jeżeli rozwijasz osobną
   gałąź, gotowa zmiana musi trafić do domyślnej gałęzi, zanim ogłosisz
   dostępność dla magazynu. Nie zmieniaj domyślnej gałęzi przy każdej poprawce.
7. Potwierdź dokładny zdalny SHA, publiczny README i pobranie plików bez
   logowania. Sam lokalny commit nie jest gotową aktualizacją na drugim PC.
8. Jeśli właściciel zlecił powiadomienie, wyślij krótki mail: numer wersji,
   co się zmieniło, zwykły link do repo i proste polecenie aktualizacji.
   Odbiorca i potwierdzenie maila pozostają w prywatnym checkpointcie.
   Nie wysyłaj skomplikowanych linków do konkretnego SHA lub zamówienia.

## Na magazynie — pierwsza aktualizacja z wersji 2.0

Po zakończeniu bieżącego wpisu/operacji otwórz folder sklonowanego repo.
Sprawdź `git status --short`; lokalne zmiany rozlicz bez kasowania lub
automatycznego resetu. Dla czystej kopii na domyślnej gałęzi:

```powershell
git pull --ff-only
```

Następnie polecenie w dotychczasowej głównej rozmowie:

> Zaktualizowałem repo silnika. Odczytaj bieżące AGENTS.md,
> docs/FAST_SEARCH.md, docs/CONVERSATION_FORMAT.md i CHANGELOG.md.
> Od następnego produktu działaj według nowej wersji, z pierwszeństwem
> numeru zwrotu/przesyłki i natychmiastowym pierwszym kandydatem.
> Zachowaj istniejącą odnogę, kolejkę i nierozliczone OP.

Nie trzeba tworzyć nowej rozmowy ani nowej odnogi do każdego wydania.
Aktualizacja plików wymaga ponownego odczytania zmienionych reguł przez
aktywną rozmowę. Nie kopiuj do niej całej historii starych przypadków.

## Kolejne aktualizacje — skrypt

Od wersji 2.1 możesz sprawdzić dostępność:

```powershell
py -3 scripts/update_engine.py
```

I zastosować aktualizację:

```powershell
py -3 scripts/update_engine.py --apply
```

Skrypt potwierdza origin, domyślną gałąź, czyste drzewo, brak aktywnego lub
niepewnego wpisu w prywatnej kolejce oraz zgodny SHA po fast-forward.
Nie robi force reset, stash, zmiany uprawnień ani nadpisania lokalnej pracy.
Jeśli używasz kolejki w innym miejscu, wskaż ją przez `--queue-db`.

Prywatne tokeny, cache, zdjęcia i kolejka znajdują się poza repo, więc zwykła
aktualizacja ich nie przenosi i nie zastępuje. Nie usuwaj private queue
dlatego, że kod ma nową wersję. Po aktualizacji obsłuż nowe zadania nowym
kodem, a niepewną wcześniejszą operację rozlicz po jej zachowanym OP.

## Gdy pobrano ZIP

Pobierz nowy **Code → Download ZIP** z tego samego zwykłego adresu.
Rozpakuj do nowego folderu, otwórz go w Codexie i odczytaj zmienione instrukcje.
Zachowaj dotychczasowe prywatne dane i ścieżkę kolejki. Nie rozpakowuj ZIP
na trwającą operację i nie kasuj poprzedniego folderu przed sprawdzeniem nowego.
Do przyszłych prostych aktualizacji zalecany jest klon Git.

## Zakres publikacji

Aktualizacja repo udostępnia silnik i instrukcje. Nie aktualizuje zdalnie
firmowego PC bez działania na tym PC, nie daje nowych uprawnień Google/Base
i nie wykonuje wpisu magazynowego. Gotowość wydania oraz zastosowanie go
na magazynie to dwa oddzielnie potwierdzane wyniki.
