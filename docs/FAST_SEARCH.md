# Szybki najlepszy kandydat i dalsze sprawdzanie

Cel: **na początku pokaż najlepszego kandydata znalezionego dotąd**, a potem
kontynuuj porównywanie Base i archiwum. Nie czekaj z pierwszą odpowiedzią na
pełny przegląd. Nie kończ wyszukiwania tylko dlatego, że pojawiła się propozycja.

## 1. Niezależne tropy, bez pierwszeństwa numerów zwrotu

Odczytaj w jednym przebiegu wszystkie etykiety. Wykorzystuj model/wariant,
EAN, SKU, numer BL/transakcji, pełną przesyłkę i numer zwrotu jako niezależne
tropy. Łącz tanie odczyty i wykonuj niezależne żądania równolegle, jeśli to
przyspiesza wynik. Lokalny cache jest wskazówką; wybraną pozycję czytaj świeżo.

**Numery zwrotów/RMA były wpisywane błędnie.** Nie mają pierwszeństwa ani
samodzielnego wpływu na ranking. Brak lub niezgodność takiego numeru nie
blokuje kandydata dopasowanego po produkcie. Zgodność z notatką jest tropem,
a nie potwierdzeniem fizycznej sztuki. Jawne polecenie wyszukania konkretnego
RMA można wykonać osobno, ale nie zamieniaj go automatycznie w warunek każdego
wyszukiwania po zdjęciu.

| Trop | Tani odczyt |
| --- | --- |
| Model / EAN / SKU | Najmocniejsza dostępna wskazówka produktu z cache → świeży getOrders; dalej strony odpowiednich statusów i celowany katalog. |
| BL / numer transakcji | getOrders(order_id) / getOrders(filter_external_order_id). |
| Pełny numer przesyłki | Prywatny indeks → świeże getOrderPackages lub dane zamówienia; następnie dokładny filtr panelu. |
| Numer zwrotu / RMA | Pomocniczo: indeks, notatki zamówienia, pola dodatkowe i rejestr getOrderReturns. |
| Wewnętrzny ID zwrotu Base | getOrderReturns(return_id); powiązanie produktu i oryginalnego BL nadal wymaga weryfikacji. |

Zachowuj prefiksy i zera. Telefon automatu DPD, numer punktu, EAN, partia,
numer seryjny i numer przesyłki mają różne znaczenia. Nie wysyłaj telefonu
jako return_id lub tracking. Rozróżnij etykietę zakupu i zwrotu.

## 2. Szybka odpowiedź, potem kontynuacja

Jeśli narzędzie przekazuje zdarzenia na bieżąco, uruchom domyślny przebieg:

```powershell
py -3 scripts/find_outlet_candidates.py --model "MODEL_Z_ETYKIETY" --ean "EAN_Z_ETYKIETY" --return-number "POMOCNICZY_NUMER" --format jsonl
```

`candidate_found` pojawia się przed finansowym uzupełnieniem i porównaniem
innych zamówień. Obsłuż je od razu w rozmowie. `candidate_updated` oznacza
mocniejszego kandydata; `result` podaje stan sprawdzonego zakresu API.
Zwykły JSON jest jednym końcowym obiektem, nie strumieniem.

Jeśli narzędzie oddaje stdout dopiero po zakończeniu procesu, najpierw:

```powershell
py -3 scripts/find_outlet_candidates.py --model "MODEL_Z_ETYKIETY" --ean "EAN_Z_ETYKIETY" --return-number "POMOCNICZY_NUMER" --preview-only --format json
```

Pokaż bez zwłoki:

> **Najlepszy kandydat dotąd: BL [numer], [model / SKU] — wstępny.**
> Dowód: [konkretne dopasowanie]. Sprawdzam dalej inne zamówienia Base i archiwum.

Następnie **bez czekania na odpowiedź pracownika** wywołaj ten sam zakres
bez `--preview-only`, z `--format jsonl`. Uzupełniaj firmę zakupu, netto,
brutto, VAT, właściciela i wszystkie pola arkusza proponowanej pozycji.
Nie opóźniaj pierwszej propozycji odczytem pełnego arkusza ani dokumentów
wszystkich alternatyw. Braki pozostają jawne.

Domyślnie skrypt porównuje kolejne pasujące zamówienia z cache, rodzimych
zwrotów i statusów zwrot/anulowanie/serwis. Rejestr zwrotów jest odczytywany
równolegle z tanimi odczytami innych pasujących zamówień. Paginacja kontynuuje
za pierwszą stronę bez ponownego żądania tej samej strony w jednym przebiegu.
`--deep` rozszerza porównanie na wszystkie bieżące statusy.

Gdy pokażesz mocniejsze trafienie, zaczynaj aktualizację od nowego najlepszego
BL i jednego zdania wyjaśnienia. Ranking porównuje obserwowane dowody produktu,
przesyłki, świeży odczyt i dane zwrotu; data rozstrzyga porównywalne tropy.
RMA wpisany ręcznie nie dodaje punktów. Nie wymyślaj procentów pewności.

## 3. Archiwum po wstępnej propozycji

Po szybkim wyniku sprawdź także archiwum Base. Nie traktuj zakończenia skryptu
lub `current_api_comparison_complete=true` jako końca pracy rozmowy.
`includes_archive=false` i `followup_required=["archive"]` oznaczają, że
trzeba jeszcze wykonać celowany odczyt panelu/archiwum.

W żywym panelu wybierz archiwum, wyczyść poprzednie filtry i szukaj pełnego
modelu/EAN/SKU oraz dostępnych etykiet. Odczytaj pasujące karty i porównaj
produkty, pozycje, statusy, przesyłki/zwroty i dokumenty. Numery RMA są jednym
z pomocniczych filtrów, nie jedyną drogą. Nie przywracaj zamówień z archiwum
do obiegu na potrzeby odczytu. Jeśli dostęp do archiwum jest niedostępny,
podaj ten konkretny brak; nie deklaruj wykluczenia innych zamówień.

Kontynuuj do przerwania przez właściciela, jego potwierdzenia albo rzeczywistego
sprawdzenia właściwego zakresu. Nie uruchamiaj monitora ani powtarzalnego
pollingu po wyczerpaniu dostępnych dowodów.

## 4. Co oznacza przerwanie lub kolejny produkt

Właściciel ustalił: **gdy przerywa dalsze szukanie lub przechodzi do nowego
produktu, ostatnio pokazane dopasowanie było właściwe**. Nie pytaj ponownie
o ten sam BL. Zapisz `accepted_after_user_transition` prywatnie zgodnie z
CONVERSATION_FORMAT.md, zatrzymaj proces poprzedniego wyszukiwania i obsłuż
kolejne zdjęcia. Nie kieruj nowego zdjęcia do starego OP.

Decyduje ostatni jednoznacznie wskazany najlepszy kandydat, który był widoczny
w rozmowie. `shown-candidate.json` zachowuje ostatnie zdarzenie propozycji,
`first-candidate.json` pierwsze, a `latest-result.json` stan częściowy/końcowy.
Niewyświetlona zmiana w pliku nie zastępuje decyzji pracownika. Jawne odrzucenie
lub wskazanie innego numeru ma pierwszeństwo. Timeout, awaria i samo wyjście
skryptu nie oznaczają potwierdzenia człowieka.

Potwierdzenie dopasowania i zgoda na dokładny wpis pozostają rozliczone według
CONVERSATION_FORMAT.md i DELEGATION.md. Istniejąca zgoda na wpis działa dalej
w odnodze; nie dopisuj nieznanych cen, ilości ani stanu na podstawie przerwania.

## 5. Pomocnicze RMA w zamówieniach i API

Sprawdzaj Notatki, `extra_field_2`, `admin_comments` i nazwane pola dodatkowe.
`getOrders(include_custom_extra_fields=true)` daje ich wartości;
`getOrderExtraFields` aktualne nazwy. Standardowe pole 2 to Notatki;
przyszłe dedykowane ID ustal z metadanych. Parser rozpoznaje m.in. Numer/Nr/ID
zwrotu, Kod zwrotu, RMA, Return number i nazwy z dopiskiem marketplace.

Rejestr getOrderReturns zawiera własne return_id, reference_number,
external_order_id oraz powiązane order_id/order_product_id. external_order_id
zwrotu nie jest automatycznie numerem zamówienia sprzedaży. Rejestr może
wskazać kandydaturę z archiwum przed odczytem oryginalnej karty; koszt zakupu,
daty i ilość fizyczna pozostają wtedy do weryfikacji. Kwota refundacji nie
zastępuje ceny zakupu.

Base nie dokumentuje filtrów getOrders po dowolnej notatce, tracking lub RMA.
Nie wymyślaj filter_return_number, filter_notes albo filter_delivery_package_nr.
Ignorowany parametr może zwrócić niepowiązane zamówienia. W panelu korzystaj
z rzeczywiście dostępnych filtrów, według bieżącego interfejsu.

## 6. Tryby dodatkowe i prywatność

- `--preview-only`: szybki etap; rozmowa kontynuuje kolejnym odczytem.
- `--stop-after-first` lub jawny BL/transakcja: celowane uzupełnienie wybranej
  pozycji, bez zbędnego porównania przy już ustalonym zamówieniu.
- `--strict-return-reference`: wyłącznie na jawne polecenie wyszukania
  konkretnego RMA. Domyślne rozpoznawanie produktu traktuje RMA pomocniczo.
- `--exclude-order-id`: pomiń odrzuconego kandydata dla tej sztuki.
- `--full-scan`: starszy pełny raport po modelu; nie jest warunkiem pierwszej
  propozycji ani zamiennikiem sprawdzenia archiwum.
- Cache i receipt pozostają poza repo, osobno dla konfiguracji Base. Nie
  indeksuj całych notatek ani danych klienta/bankowych zwrotu.
- Aktualny odczyt wybranego zamówienia, budżet 100 żądań/min, równoległe tanie
  żądania i zapis cache partiami nadal obowiązują. Mierz czas do pierwszej
  propozycji oddzielnie od dalszego porównania.
- Zgoda, fizyczna ilość/stan, wycena, właściciel, duplikaty i exact readback
  pozostają wymaganiami wpisu. Nowy przebieg wyszukiwania ich nie zastępuje.

Źródła API: [getOrders](https://api.baselinker.com/index.php?method=getOrders),
[getOrderReturns](https://api.baselinker.com/index.php?method=getOrderReturns),
[getOrderExtraFields](https://api.baselinker.com/index.php?method=getOrderExtraFields),
[limit API](https://api.baselinker.com/).
