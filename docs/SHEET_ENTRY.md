# Pełny wpis znalezionego zamówienia do arkusza

Ta procedura jest wykonywana **w osobnej rozmowie do arkusza**, po zleceniu
z głównej rozmowy i sprawdzeniu zgody człowieka. Zakres `sheet_entry` zapisuje
ewidencję; nie tworzy stanu w Base, PZ ani oferty marketplace.

## 1. Źródło, zgoda i żywy schemat

1. Odczytaj manifest z prywatnej kolejki, jego hash i konkretną zgodę.
   `validate_manifest` odrzuca zmianę danych po akceptacji, obcy zakres,
   brak powiązania produktu z pozycją i próbę zaznaczenia przyjęcia magazynowego.
2. Zweryfikuj firmowy profil Google oraz ID arkusza. `link_id` ustal w bieżącej
   sesji. Odczytaj metadane, prawdziwe tytuły kart, sheetId, rozmiar, locale i strefę.
3. Odczytaj całą INSTRUKCJĘ MAGAZYNU i porównaj z wiedzą w repo. Zakres dziel
   na małe fragmenty, do ostatniej sekcji. Nie ograniczaj się do sekcji 01–10.
4. Odczytaj aktualne nagłówki oraz rodzime komórki przez `get_spreadsheet_cells`
   z `userEnteredValue,effectiveValue,formattedValue,dataValidation,chipRuns,userEnteredFormat,note`.
   Potrzebne są: nagłówek, docelowy wiersz i wzorzec jego struktury.
   Zwykły odczyt wartości nie potwierdza formuł i list wyboru.
5. Odczytaj żywo wybrane zamówienie i pozycję oraz odpowiedni produkt Base.
   Archiwalne zamówienie może wymagać karty w panelu. Nie przywracaj go do
   obiegu tylko w celu wpisu. Numer zewnętrzny najpierw przetłumacz na BL.

Aktualny schemat jest w configs/sheet-schema.json. Jest snapshotem **struktury**,
nie snapshotem towaru. Rozpoznawaj kolumny po nagłówkach, nie po literze.
Nieznany, brakujący albo powtórzony nagłówek rozlicz przed zapisem.

## 2. OUTLET — wszystkie 22 pola

| Pole | Co wpisujemy |
| --- | --- |
| Sprzedano | FALSE dla nowego rekordu. Istniejącej flagi nie cofamy. |
| Dodane do systemu magazynowego | FALSE do osobno potwierdzonego przyjęcia. |
| Nr PZ system magazynowy | Puste dla nowego wpisu bez PZ. Istniejący numer zachowujemy. |
| lk | Rodzimy checkbox; nowy FALSE, istniejący zachowujemy. Nie domyślaj się innego znaczenia. |
| Nazwa | Dokładny produkt/model/wariant z powiązanej pozycji. |
| EAN Oryg. | Oryginalny kod z etykiety, jako tekst z zerami. Nie podmieniaj technicznego EAN Base. |
| SKU | Źródłowe dokładne SKU jako tekst; nie zastępuj EAN-em. |
| Cena Netto | Zaakceptowana jednostkowa wycena przyjęcia PLN i jej źródło. |
| Cena brutto | Jednostkowe brutto zgodne z zaakceptowanym netto i VAT. Zachowaj istniejącą formułę. |
| VAT | Rzeczywista stawka, np. 23%; API zapisuje 0.23 w komórce procentowej. |
| Ilość | Fizycznie otrzymana, potwierdzona. Nie automatycznie ilość zamówiona. |
| Zamówienie BL | Wewnętrzny numer Base powiązanej pozycji, jako tekst. |
| Data zamówienia | Data źródłowa w Europe/Warsaw. |
| Data przyjęcia | Rzeczywista data otrzymania; nie data zamówienia/wykonania skryptu. |
| Dokument korygujący | Pełny numer potwierdzonej korekty; brak pozostaje pusty, bez fikcyjnego numeru. |
| Zamówienie zakupowe | Potwierdzony numer zakupu, jeżeli dostępny. Nie kopiuj tu BL sprzedaży. |
| Konto Allegro | Konto zakupowe; nazwa sprzedawcy zakupu trafia osobno do notatki. |
| Kupujący | Spółka kupująca towar, nie klient końcowy. |
| Własność Spółki | Aktualna potwierdzona SP/TT z dokumentów/sprzedaży/transferów. |
| Wystawione | Aktualny stan wystawienia; nowa niewystawiona pozycja NIE. Istniejącego nie resetujemy. |
| Notatka | Dostawca/sprzedawca zakupu, rzeczywisty stan, braki, uszkodzenia, test i źródła. Zachowaj wcześniejsze notatki. |
| Notatka AI | Krótki stan wpisu oraz trwałe OP. Szczegóły w notatce komórki. |

Firma dostawcy, konto sprzedawcy, konto zakupowe, kupująca spółka i aktualny
właściciel to pięć różnych informacji. Nie używaj adresu, nazwiska lub faktury
klienta do wypełnienia danych zakupowych.

## 3. REKLAMACJE — 19 pól i kontrola własności

| Pole | Co wpisujemy |
| --- | --- |
| Rozwiązane - wydano | Nowy FALSE; istniejący zachowaj. |
| Dodane do systemu magazynowego | FALSE do potwierdzonego przyjęcia własnego towaru. |
| Nr PZ system magazynowy | Tylko rzeczywisty dokument istniejącego przyjęcia; przy samym wpisie puste. |
| ID | Istniejące trwałe ID reklamacji lub nowe jednoznaczne ID rejestru, zachowane w OP. |
| Nazwa / EAN Oryginalny / SKU | Powiązany produkt i oznaczenia jako tekst. |
| Cena netto / Cena brutto / VAT | Jednostkowa wycena PLN, rzeczywista stawka, spójne netto/brutto. |
| Ilość | Faktycznie otrzymana. |
| Zamówienie BL | Wewnętrzny numer potwierdzonej pozycji. |
| Data / Data otrzymania | Odrębna data zamówienia i otrzymania. |
| Informacja | Dozwolona wartość żywej listy; szczegóły w notatce. |
| Status | Rzeczywisty stan zgodny z żywą listą wyboru. |
| Sprzedawca | Spółka sprzedaży SP/TT, nie nazwa dostawcy zakupowego. |
| Właściciel towaru | Potwierdzone MY albo KLIENT. MY nie rozstrzyga SP/TT. |
| Notatka | Stan, braki, dowody, kontekst zakupowy, OP; wcześniejsza treść pozostaje. |

KLIENT może być prawidłowym wpisem ewidencji reklamacji. **Nie może być
przyjęty na własny stan firmy ani otrzymać TRUE checkboxa magazynowego.**
Pusta/niejednoznaczna własność pozostaje WYMAGA DANYCH; nie zmieniaj jej dla
ominięcia bramki. Bieżące listy odczytaj z komórek, nie wymyślaj nowego statusu.

## 4. Cena, ilość, daty i szkic

- Base `41787`: `N: kwota vNN` = N sztuk, kwota jednostkowa NETTO PLN,
  VAT NN. Historyczna kwota bez vNN jest brutto; bez dokumentu VAT nie
  wyliczaj netto przez domyślne 1.23. Wiele pozycji/cen wymaga alokacji.
- Koszt zakupowy jest informacją i możliwą propozycją. Wpis pełny używa
  zatwierdzonej wyceny aktualnego właściciela, także po transferze SP→TT.
  Dotychczasowa zatwierdzona Cena Netto jest źródłem kolejnego PZ.
- Nie dodawaj dodatkowych 3%, nie kopiuj EUR brutto ze sprzedaży do netto PLN,
  nie zastępuj braku zerem. Kwoty liczymy Decimal, HALF_UP do 0.01 PLN.
- Ilość w zamówieniu nie dowodzi ilości otrzymanej. Potwierdzone urządzenia
  w sztukach mają liczbę całkowitą większą od zera.
- Data przyjęcia/otrzymania jest historyczną datą fizyczną. Nie używaj dnia
  importu bez dowodu. Daty API są liczbami seryjnymi z formatem DATE.
- `entry_mode=complete`: uzgodnione dane fizyczne, własność, ceny i źródła.
  „Nie testowano urządzenia” jest uczciwym opisem stanu, nie dowodem sprawności.
- `entry_mode=draft`: człowiek zlecił zapis znanych danych mimo braków.
  Nieznane pola są puste, status WYMAGA DANYCH z listą braków. Nie zatwierdzamy PZ.

## 5. Duplikaty i znalezienie wiersza

1. Przeszukaj bieżące karty i potrzebny rejestr historyczny po BL, SKU,
   oryginalnym EAN, ID reklamacji i OP. Użyj celowanych kolumn/zakresów.
   Przy row search mniej niż 50 000 skanowanych komórek; dziel duże zakresy.
2. `find_duplicate` rozpoznaje to samo OP oraz istniejące BL/SKU. Istniejące
   OP odtwarzamy, zamiast dodawać nowy wiersz. Identyczne BL/SKU może oznaczać
   kilka sztuk; osobne przyjęcie wymaga źródła, odrębnego physical_receipt_id
   i uzgodnionego rozstrzygnięcia. Nowe UUID nie rozwiązuje konfliktu.
3. Sprawdź wcześniejszy PZ/checkbox i kartotekę/stany. Jeżeli przyjęcie już
   powstało, napraw tylko brakujący zapis; nie dopisuj powtórnej wartości statystyk.
4. Dla nowego rekordu wybierz faktycznie pusty wiersz danych. Same puste
   EAN/BL nie wystarczą. Dopuszczalne są w nim nieaktywne checkboxy i rodzime
   formuły cen, bez wartości cudzej pozycji. `row_is_empty` kontroluje ten warunek.
5. Jeśli siatka nie ma miejsca, rozszerz ją w jednym uzgodnionym kroku,
   odczytaj nowy wiersz i dopiero zbuduj plan. Nie zapisuj poza rowCount.
6. Przy aktualizacji odszukaj wiersz po OP/ID i zweryfikuj SKU/BL po sortowaniu.
   Różna niepusta wartość wymaga konkretnej zaakceptowanej zmiany
   `approved_changes`: poprzednia rodzima wartość, nowa wartość i źródło zgody.

## 6. Plan natywnego zapisu API

Wiedza o typach jest w `src/outlet_engine/sheet.py`. Użyj `snapshot_from_cells`
do znormalizowania structuredContent bieżącego `get_spreadsheet_cells`.
Zapisz snapshot lokalnie poza Git. Odczyt musi obejmować **A1:ostatni nagłówek1**,
dokładny docelowy wiersz i zweryfikowany wiersz wzorcowy, w istniejącej siatce.

```powershell
py -3 scripts/prepare_sheet_entry.py plan --manifest "PRYWATNA_SCIEZKA/manifest.json" --snapshot "PRYWATNA_SCIEZKA/before.json" --output "PRYWATNA_SCIEZKA/plan.json"
```

`build_plan`:

- mapuje pola po aktualnych nagłówkach;
- zapisuje ceny/ilość przez numberValue, VAT jako 0.23 dla 23%, daty jako
  serial + format DATE, identyfikatory przez stringValue, checkboxy przez boolValue;
- zachowuje formuły cen; później sprawdza ich effectiveValue;
- dla nowego wiersza kopiuje wyłącznie FORMAT i DATA_VALIDATION z wzorca;
  nie kopiuje cudzych wartości/chipów przez PASTE_NORMAL;
- wpisuje tylko konkretne komórki, zachowuje nieobjęte zakresem wartości,
  notatki i flagi istniejących rekordów;
- zachowuje listy wyboru i formatowanie; wykrywa niesklasyfikowane chipy
  oraz walidacje niestandardowe zamiast przepisywać je na ślepo;
- dopisuje krótkie OP w Notatka AI / Notatka i audit w notatce komórki;
- pozostawia magazynowe przyjęcie FALSE oraz numer PZ pusty przy nowym wpisie.

Plan ma hash propozycji oraz preimage snapshotu. Tuż przed zapisem ponownie
odczytaj te same komórki/struktury i wykonaj:

```powershell
py -3 scripts/prepare_sheet_entry.py preflight --plan "PRYWATNA_SCIEZKA/plan.json" --snapshot "PRYWATNA_SCIEZKA/fresh.json"
```

Zmiana danych, numeru wiersza, własności, ceny lub walidacji unieważnia plan.
Odczytaj stan, wyjaśnij zmianę, zbuduj właściwy plan. Nie naprawiaj w ciemno.

Następnie ustaw `write_pending` w kolejce i zapisz checkpoint planu. Wywołaj
**jedno** `batch_update_spreadsheet` przez właściwe firmowe połączenie:

```text
link_id: bieżące połączenie firmy po get_profile
spreadsheet_id: plan.spreadsheet_id
requests: plan.requests   (tablica obiektów JSON, nie tekst)
include_spreadsheet_in_response: true
response_ranges: [plan.range]
response_include_grid_data: true
```

To aktualny kontrakt konektora; zawsze porównaj jego schema w danym środowisku.
Każde żądanie ma jedną rodzinę, zakres GridRange z indeksami od 0 i end-exclusive,
precyzyjne fields. Nie mieszaj z values.batchUpdate, nie używaj wartościowego
append do arkusza z checkboxami/formułami. Przy niepewnym wyniku nie ponawiaj POST.

## 7. Exact readback i ukończenie

Odczytaj zapisany wiersz przez get_spreadsheet_cells z tym samym maskowaniem
wartości, formuł, walidacji, formatów i notatek. Po sortowaniu odszukaj OP/ID
i zweryfikuj rzeczywisty numer wiersza. Zbuduj snapshot wyniku.

```powershell
py -3 scripts/prepare_sheet_entry.py verify --plan "PRYWATNA_SCIEZKA/plan.json" --snapshot "PRYWATNA_SCIEZKA/after.json" --output "PRYWATNA_SCIEZKA/receipt.json"
```

Porównanie obejmuje:

- właściwe konto/arkusz/kartę/OP oraz tożsamość SKU i BL;
- dokładne wartości wszystkich wpisanych pól, obliczone formuły cen;
- prawdziwe typy identyfikatorów, dat, procentów i checkboxów;
- zachowane walidacje, formaty, notatki i niezmienione pola poza zakresem;
- status wpisu, jawne braki i magazynowe FALSE przy samym wpisie.

Po poprawnej weryfikacji zapisz receipt oraz `verified` w kolejce. Wynik
w rozmowie: karta, BL/SKU, ilość, właściciel, netto/brutto/VAT, link do wiersza,
braki i prawdziwy stan magazynowy. Przy szkicu powiedz „wpisano szkic, wymaga danych”.

Odczyt rodzimego arkusza jest dowodem danych. Przy sprawdzaniu wyglądu użyj
aktualnego podglądu arkusza i oceń czytelność; nie twierdź, że wykonano kontrolę
wizualną, jeśli dostępny był tylko API. Nie przemalowuj arkusza dla jednego wpisu.

## 8. Wznowienie po przerwaniu

| Stan | Co robimy |
| --- | --- |
| Timeout po wysłaniu | Zachowaj OP/plan. Najpierw odczyt wiersza i notatki; wynik może już istnieć. |
| OP istnieje i dane są zgodne | Odtwórz receipt; nie dopisuj drugiego wiersza. |
| Wpis częściowy lub inny | needs_review, konkretna różnica; uzupełnij tylko potwierdzony brak po świeżym planie. |
| Wiersz przesunięto/sortowano | Odszukaj trwałe OP, odczytaj nowy zakres, zaktualizuj lokalizację w planie odzyskania; to nie zmienia zaakceptowanych danych. |
| Cena/spółka/ilość różni się od zgody | Wyjaśnij materialną zmianę; nie wybieraj sam nowej wartości. |
| Checkbox TRUE lub PZ już istnieje | Sprawdź Base i wcześniejszą operację; nie resetuj flag ani dokumentu. |
| Brak Google/uprawnień | Zapisz konkretny wyjątek i warunek wznowienia; główna rozmowa może nadal szukać. |

Nie kasuj notatek, Q lub ukrytych V–Z kolejki magazynowej dla ponowienia.
Nie usuwaj potwierdzonych PZ ani nie koryguj zapasu po błędzie Sheets.
Wpis nie jest transakcją compare-and-swap: jeden writer oraz świeży preflight
ograniczają konflikt, a readback go wykrywa. Status w notatce nie jest globalnym lockiem.

## 9. Przygotowanie STANOWE DODAJ DO SM oraz odrębny PZ

Jeśli zlecony zakres obejmuje przygotowanie kolejki WarePilot, zastosuj całą
SHEET_INSTRUCTIONS.md, sekcje 11–12. Zachowaj A–K w ustalonej kolejności;
L=MY dla firmowego towaru, O=`OUTLET|SKU|zamówienie` lub `REKLAMACJE|ID`,
AA=rzeczywista data, AB=uzgodniony stan. M jest formułą i nie może zostać
nadpisane. R–U są wynikiem panelu; V–Z są automatyczne i ukryte. Q zapisuje
rzeczywiste ID operacji HTML/WarePilot, nie wymyślony zamiennik sheet-entry OP.

Samo uzupełnienie kolejki nie tworzy PZ. Przed osobno zleconym przyjęciem
sprawdź żywą własność, spółkę, SKU, ilość, cenę, typ źródła i magazyn.
Zestaw rozpisz na otrzymane komponenty z uzgodnioną sumą; bez przyjęcia rodzica
i części równocześnie. Szczegółowe wywołania i odzyskanie WarePilot są w
OPERATING_GUIDE.md, sekcje 9–13. Pełny PZ i checkbox TRUE zapisujemy dopiero
po potwierdzeniu Base i wszystkich właściwych pozycji.

Podstawy techniczne: [batchUpdate i request types](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/request).
Zapisy API nie wyzwalają onEdit, więc kontrolę wykonuje worker:
[ograniczenia Apps Script](https://developers.google.com/apps-script/guides/triggers#restrictions).
