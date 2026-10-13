# Zmiany silnika

## 2.2.0 — 13.10.2026

- Numery zwrotów/RMA są pomocnicze: nie mają pierwszeństwa, nie blokują
  dopasowania rozpoznanego produktu i nie podnoszą samodzielnie rankingu.
- Pierwsza odpowiedź zaczyna się od najlepszego kandydata znalezionego dotąd;
  mocniejszy późniejszy wynik pojawia się jako krótka aktualizacja.
- Domyślny przebieg kontynuuje porównanie Base po pierwszej propozycji;
  rozmowa następnie sprawdza archiwum. Zakres API i archiwum pozostają jawne.
- Równoległy odczyt rejestru zwrotów i tanich kart zamówień, ponowne użycie
  pierwszej strony i bez odczytu dokumentów finansowych każdej alternatywy.
- Zachowany ostatni pokazany kandydat i checkpoint częściowy. Przerwanie
  dalszego szukania/przejście właściciela do kolejnego produktu potwierdza
  ostatnie jednoznacznie wskazane dopasowanie; awaria techniczna tego nie robi.
- Zachowane wcześniejsze zgody na dokładny wpis oraz bramki danych arkusza.

## 2.1.0 — 12.10.2026

- Domyślny tryb kończy wyszukiwanie na pierwszym świeżym, wiarygodnym kandydacie.
- Pierwszeństwo numeru zwrotu/RMA, przesyłki, BL i transakcji ze zdjęć.
- Numery zwrotów wyszukiwane także w notatkach i polach dodatkowych zamówień Base.
- Prywatny indeks oznaczeń i wykorzystanie dotychczasowego cache bez czekania
  na ponowną budowę całego indeksu.
- Podgląd `--preview-only`, wczesne zdarzenie JSONL, pomiar czasu do pierwszego
  kandydata oraz pomijanie odrzuconego BL.
- Powiązany BL można zaproponować z rejestru RMA przed odczytem pełnej karty;
  oryginalne ceny, daty i ilości pozostają do weryfikacji.
- Równoległe uzupełnienie faktur/przesyłek tylko wybranego kandydata.
- Budżet 100 żądań/min bez stałego opóźniania każdej krótkiej próby.
- Oddzielny pełny przegląd, pogłębiona ścieżka konkretnego oznaczenia i
  obsługa archiwum, konfliktów wariantu oraz niezgodnych etykiet.
- Procedura rozwoju silnika z komputera autora i aktualizacji magazynu;
  skrypt fast-forward zachowujący prywatną kolejkę i lokalne zmiany.

## 2.0.0 — 12.10.2026

- Samodzielne publiczne repo silnika, pełne instrukcje źródłowe i konfiguracja.
- Wyszukiwanie Base, werdykt z zakupem/netto/brutto/VAT i komplet pól arkusza.
- Zatwierdzone wpisy w osobnej rozmowie, prywatna kolejka i exact readback.
- Odrębna zgoda na przyjęcie magazynowe, bez automatycznego PZ przy wpisie do arkusza.
