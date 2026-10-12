# Najszybsza droga do pierwszego wiarygodnego kandydata

Cel: **pokaż pierwszego prawdopodobnego kandydata natychmiast**, gdy świeży
dowód łączy oznaczenie/produkt z zamówieniem. Pełna lista i globalny ranking
nie są warunkiem pierwszej odpowiedzi. Dopiero potem uzupełniamy wybraną
pozycję i przechodzimy do jej zatwierdzenia.

## 1. Najpierw oczywiste rzeczy ze zdjęcia

Odczytaj w jednym przebiegu wszystkie widoczne etykiety. Kolejność prób:

| Oznaczenie | Najkrótsza droga |
| --- | --- |
| Numer zwrotu / RMA | Prywatny indeks oznaczeń → świeży rekord zwrotu lub notatka zamówienia → powiązany numer BL. |
| Wewnętrzny ID zwrotu Base | getOrderReturns(return_id), porównanie produktu, od razu propozycja powiązanego BL. |
| Pełny numer przesyłki | Indeks przesyłek → świeża przesyłka zamówienia; przy braku indeksu dokładny filtr panelu. |
| Numer BL | Jeden getOrders(order_id), bez skanu statusów i całego katalogu. |
| Numer transakcji marketplace | getOrders(filter_external_order_id), porównanie produktu. |
| SKU / pełny model / oryginalny EAN | Lokalny indeks → świeży kandydat; następnie pierwsze odpowiednie strony statusów i celowany katalog tylko w razie potrzeby. |

Nie pomijaj numeru zwrotu dlatego, że rozpoznano model. Zachowaj pełny
prefiks i zera. Telefon automatu DPD, numer punktu odbioru, EAN, kod partii
i numer seryjny są różnymi identyfikatorami. Nie wysyłaj telefonu jako
return_id lub numeru przesyłki. Przy kilku etykietach określ, które są
aktualne i czego dotyczą; nie utożsamiaj automatycznie etykiety zakupu ze zwrotną.

## 2. Numery zwrotów wpisane w samych zamówieniach

Firma wprowadza numery zwrotów również w rekordach zamówień. Dlatego
wyszukiwanie sprawdza **Notatki**, `extra_field_2`, `admin_comments` i
nazwane pola dodatkowe, a nie tylko osobny rejestr zwrotów.

- `getOrders(include_custom_extra_fields=true)` udostępnia wartości tych pól.
- `getOrderExtraFields` rozpoznaje ich aktualne nazwy. W sprawdzonym układzie
  standardowe pole `2` ma nazwę **Notatki**. Nie zakładaj stałego ID przyszłego
  dedykowanego pola RMA; rozpoznaj je z metadanych.
- Obsługujemy m.in. „Numer zwrotu”, „Nr zwrotu”, „ID zwrotu”, „Kod zwrotu”,
  „RMA”, „Return number” oraz nazwę z dopiskiem marketplace.
- Pusty getOrderReturns nie wyklucza numeru w notatce lub przesyłki zwrotnej.
- RMA w rejestrze zwrotów ma własne `return_id`, `reference_number`,
  `external_order_id` i powiązane `order_id` / `order_product_id`.
  `external_order_id` w tym rejestrze jest kodem zwrotu, nie automatycznie
  numerem zamówienia sprzedaży.

Base nie dokumentuje filtra getOrders po dowolnej notatce, numerze przesyłki
lub numerze RMA zapisanym w dodatkowym polu. Nie wysyłaj wymyślonych
`filter_return_number`, `filter_notes` albo `filter_delivery_package_nr`.
Ignorowany parametr mógłby zwrócić niepowiązane zamówienia.

Jeśli dokładnego oznaczenia nie ma jeszcze w indeksie i rejestrze,
użyj **dokładnego wyszukiwania w panelu Base** po notatce/polu dodatkowym
lub przesyłce, na bieżącym stanie interfejsu. Ustaw właściwy zakres oraz
wyczyść poprzednie filtry. Dla starego towaru sprawdź archiwum. Gdy UI jest
niedostępne albo nie rozstrzyga, `--deep` skanuje oznaczenie w bieżących
zamówieniach wszystkich statusów, strona po stronie, i kończy na trafieniu.
Nie odczytuj każdego zamówienia osobnym żądaniem tylko po to, aby zbudować indeks.

## 3. Pierwsza odpowiedź przed pełnym przeglądem

Dla pierwszej propozycji uruchom szybki podgląd:

```powershell
py -3 scripts/find_outlet_candidates.py --model "MODEL_Z_ETYKIETY" --return-number "PELNY_NUMER_ZWROTU" --preview-only --format json
py -3 scripts/find_outlet_candidates.py --return-id ID_ZWROTU_BASE --sku "SKU_Z_ETYKIETY" --preview-only --format json
py -3 scripts/find_outlet_candidates.py --model "MODEL_Z_ETYKIETY" --tracking-number "PELNY_NUMER_PRZESYLKI" --preview-only --format json
py -3 scripts/find_outlet_candidates.py --model "MODEL_Z_ETYKIETY" --preview-only --format json
```

Pokaż od razu:

> **Pierwszy wiarygodny kandydat: BL [numer], [model / SKU].**
> Dowód: [numer zwrotu zgodny z notatką / RMA wskazuje zamówienie / przesyłka /
> dopasowany produkt i status]. Sztuka do potwierdzenia.

Nie opóźniaj tej informacji pobieraniem wszystkich kartotek, faktur innych
zamówień, pełnego arkusza lub globalnego rankingu. Następnie odczytaj dane
**wyłącznie tego kandydata**, bez `--preview-only`, i podaj pełny werdykt
z firmą zakupu, netto/brutto/VAT, własnością oraz wszystkimi polami arkusza.
Jeśli faktów nie ma, pokaż ich brak; nie zastępuj ceny zakupu kwotą zwrotu.

Drugi odczyt przypnij do numeru znalezionego BL, aby nie proponować innej
pozycji podczas uzupełniania. Zachowaj znane oznaczenia jako kontrolę zgodności:

```powershell
py -3 scripts/find_outlet_candidates.py --order-id ZNALEZIONY_BL --model "MODEL_Z_ETYKIETY" --format json
```

Bez `--preview-only` skrypt nadal kończy wyszukiwanie na pierwszym kandydacie,
ale uzupełnia jego faktury i przesyłki. `--format jsonl` emituje
`candidate_found` **przed** tym uzupełnieniem, a następnie `result`.
Obsłuż pierwsze zdarzenie od razu. Sam JSON bez JSONL jest jednym końcowym
obiektem; nie parsuj go jako strumienia częściowego.

## 4. Powiązanie RMA jest wcześniejsze niż odczyt całego zamówienia

Jeśli rejestr zwrotów podaje oryginalny numer BL i jeden zgodny produkt,
proponujemy to zamówienie już po odczycie zwrotu. Nie czekamy, aż API odczyta
całą kartę sprzedaży. Ma to znaczenie również przy archiwum.

W podglądzie RMA pola zakupu, daty zamówienia i ilość fizyczna pozostają
nieustalone. Ilość rejestru zwrotu pokazujemy osobno. Nie kopiujemy kwoty
refundacji do kosztu ani daty zgłoszenia zwrotu do daty sprzedaży/otrzymania.
`order_readback_complete=false` wymaga odczytu oryginalnej karty przed wpisem.
Gdy getOrders zwraca pustą listę, powiązanie z RMA nadal jest kandydaturą;
odczytaj panel/archiwum, bez przywracania zamówienia do obiegu.

## 5. Cache, prędkość i kolejne próby

- Cache jest prywatny, poza repo, osobny dla konfiguracji Base. SQLite
  przechowuje oznaczenia → BL, minimalne pozycje i metadane. Całe notatki,
  dane klienta i bankowe zwrotu nie są indeksowane.
- Stary indeks wersji 2.0 jest importowany jako wskazówka; zawsze robimy
  świeży odczyt wybranego zamówienia/zwrotu. Stary status nie jest dowodem.
- Pierwsze strony API są przetwarzane na bieżąco. Pełna strona 100 rekordów
  nie wymusza pobrania kolejnej, jeśli jest już wiarygodny kandydat.
- Zapisy cache wykonujemy partią, a nie osobnym dyskowym commitem na rekord.
  Wczesna propozycja pojawia się przed dalszym uzupełnianiem.
- Usunięto stałe 0.7 s między żądaniami w szybkim trybie. Lokalny budżet
  respektuje 100 żądań/minutę; kolejne tanie odczyty nie czekają, gdy budżet
  jest wolny. Faktyczny retry HTTP również zużywa budżet. Inne komputery
  i aplikacje trzeba uwzględniać przy wspólnym limicie konta.
- Faktury i przesyłki jednego kandydata są odczytywane równolegle.
- Czas do pierwszego kandydata i liczbę żądań zapisujemy w receipt.
  To pomiar konkretnej próby, nie gwarancja czasu przy każdym API/archiwum.

Po odrzuceniu kandydata nie powtarzaj jego propozycji:

```powershell
py -3 scripts/find_outlet_candidates.py --model "MODEL_Z_ETYKIETY" --exclude-order-id ODRZUCONY_BL --preview-only
```

Pełne porównanie jest opcją, gdy człowiek go potrzebuje:

```powershell
py -3 scripts/find_outlet_candidates.py --model "MODEL_Z_ETYKIETY" --full-scan
```

Znany numer zwrotu/przesyłki, który nie pasuje do zamówienia, nie może zostać
zastąpiony samym podobnym modelem. Konflikt wariantu także blokuje tę
kandydaturę. Do wpisu nadal obowiązują zgoda, fizyczna ilość/stan, wycena,
własność, duplikaty i odczyt wyniku opisane w SHEET_ENTRY.md.

Źródła techniczne: [getOrders](https://api.baselinker.com/index.php?method=getOrders),
[getOrderReturns](https://api.baselinker.com/index.php?method=getOrderReturns),
[getOrderExtraFields](https://api.baselinker.com/index.php?method=getOrderExtraFields),
[limit API](https://api.baselinker.com/).
