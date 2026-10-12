# Pełna instrukcja dodawania do arkusza i przyjęć

Wiedza źródłowa: karta **INSTRUKCJA MAGAZYNU**, odczyt całej treści 12.10.2026.
136 niepustych wierszy; sekcje 01–12. Poniżej zachowano wszystkie procedury
i reguły tej karty. Adresy prywatnych arkuszy zastąpiono lokalnym źródłem.
To materiał operacyjny, a nie zgoda na zapis. Polecenie człowieka wyznacza zakres.
Przed wykonaniem odczytaj żywą instrukcję i rozlicz jej zmiany.

Hash znormalizowanego odczytu źródła: `251bb6a14172f3f3c85a3e7335b55296ab02352af49866c3725595a29df8b9d7`.

Wersję rozdzielenia rozmów i zakresów zgód określają DELEGATION.md oraz SHEET_ENTRY.md.
Wpis do arkusza wykonywany jest w odnodze; PZ wymaga zakresu przyjęcia magazynowego.

## INSTRUKCJA MAGAZYNU  |  REKLAMACJE I OUTLET

## Wersja 1.0 • 02.10.2026 • SP / TT • procedura dla pracownika i jego Codexa

## Etap 1: instrukcja pracy. Sam wpis w arkuszu ani zaznaczenie checkboxa nie tworzy dokumentu w Base. Przyjęcie wykonuje Codex po wyraźnym poleceniu pracownika i sprawdzeniu danych.

## 01  SZYBKI START — OD ZAMÓWIENIA DO NUMERU PZ

### 1 • Pracownik

Wskaż kartę OUTLET albo REKLAMACJE i podaj numer zamówienia BL, produkt oraz faktycznie otrzymaną liczbę sztuk. Dopisz datę przyjęcia, stan, braki i dostępne zdjęcia lub oznaczenia. Checkbox „Dodane do systemu magazynowego” zostaw odznaczony.

### 2 • Codex

Przeczytaj całą tę instrukcję. Odczytaj zamówienie i kartotekę Base, dopasuj produkt, uzupełnij dane w arkuszu i pokaż pracownikowi propozycję: firma, magazyn, dokument, elementy, ilości, ceny i opis. Braki wyjaśnij z pracownikiem.

### 3 • Pracownik

Sprawdź zgodność z fizycznym towarem i zaakceptuj konkretną propozycję. Dopiero polecenie „Dodaj zaakceptowane pozycje do magazynu” upoważnia do przyjęcia. Zmiana firmy, magazynu, ceny lub zakresu wymaga ponownego uzgodnienia.

### 4 • Codex

Sprawdź duplikaty i aktualną własność, wykonaj przyjęcie, odczytaj potwierdzenie w Base, wpisz pełny numer PZ w odpowiednich wierszach i dopiero wtedy zaznacz checkbox. Zwróć krótkie podsumowanie i pozycje wymagające pomocy.

## 02  GOTOWE POLECENIA DLA PRACOWNIKA

### Przygotowanie — skopiuj

Otwórz [arkusz ustawiony lokalnie przez OUTLET_SPREADSHEET_ID] i przeczytaj kartę INSTRUKCJA MAGAZYNU. Przygotuj wpis w [OUTLET / REKLAMACJE] dla zamówienia BL [NUMER], produkt [NAZWA / SKU], otrzymano [ILOŚĆ], stan i braki [OPIS]. Uzupełnij dane ze źródeł, zapytaj o braki i przedstaw gotową propozycję przyjęcia. Na tym etapie tylko przygotuj dane.

### Dodanie — po sprawdzeniu

Akceptuję propozycję dla [ID OPERACJI / POZYCJE]: firma [SP / TT], magazyn [PEŁNA NAZWA], dokument [TYP], cena jednostkowa [KWOTA NETTO + WALUTA], ilości [LISTA], opis [ZAAKCEPTOWANY OPIS]. Dodaj dokładnie te pozycje, sprawdź potwierdzenie w Base, zapisz pełny numer PZ w arkuszu i zaznacz wyłącznie przyjęte pozycje. Dla zestawu przyjmij każdy zaakceptowany element osobno.

### Oczekiwany wynik

Raport: ID operacji, firma i magazyn, pełny numer dokumentu, dokument_id, przyjęte produkty i ilości, jednostkowe ceny oraz suma. Dodatkowo: co pozostało nieprzyjęte, dlaczego i jaki jest następny krok.

## 03  DANE PRODUKTU — CO UZUPEŁNIA CODEX, CO POTWIERDZA PRACOWNIK

### Numer zamówienia

„Zamówienie BL” oznacza wewnętrzny numer Base. Numer z Allegro lub sklepu jest numerem zewnętrznym — najpierw odnajdź odpowiadające mu zamówienie BL. Jeśli jest kilka pasujących wyników, poproś o doprecyzowanie. Nie dopisuj wszystkich produktów z zamówienia automatycznie.

### Identyfikacja produktu

Potwierdź model, EAN, SKU, wariant i product_id Base. Porównaj etykietę towaru z pozycją zamówienia oraz kartoteką. Wyszukuj po EAN/SKU/modelu; sam podobny tytuł nie wystarcza. Zachowuj oryginalny EAN z opakowania i jego zera początkowe.

### Cena, ilość, VAT

Uzupełniaj ze wskazanego zamówienia lub dokumentu, zapisując źródło. Rozróżnij cenę sprzedaży, cenę zakupu i wartość dokumentu przyjęcia. Pracownik potwierdza faktycznie otrzymaną ilość; liczba w zamówieniu może być większa. Brak ceny lub stawki VAT oznacza pytanie, a nie zero lub zgadywanie.

### Stan i opis

Pracownik potwierdza stan, kompletność, uszkodzenia, wynik sprawdzenia, opakowanie i ewentualny numer seryjny. Codex układa rzeczowy opis: model → stan → braki → uszkodzenia → test. Nie dopisuj „sprawny”, „kompletny” ani innych niepotwierdzonych cech.

### Daty

Data zamówienia i data fizycznego przyjęcia to różne informacje. OUTLET: używaj „Data przyjęcia”; REKLAMACJE: „Data otrzymania”. Nie kopiuj daty zamówienia do daty otrzymania. Datę wykonania dokumentu uzgodnij przed zatwierdzeniem.

### Zapis do arkusza

Rozpoznawaj kolumny po aktualnych nagłówkach, ponieważ ich kolejność może się zmieniać. Zmieniaj tylko komórki obsługiwanych pozycji. Zachowaj formuły cen, checkboxy, formatowanie i dotychczasowe notatki. Nie nadpisuj całych wierszy ani kart.

## 04  FIRMA, WŁASNOŚĆ I WŁAŚCIWY MAGAZYN

### OUTLET • SP

SILESIA PROTECH → M2 SP - Outlet • warehouse_id 25816.

### OUTLET • TT

TRACER TEAM → M2 TT - Outlet • warehouse_id 25820.

### REKLAMACJE • SP

Towar firmowy (MY), firma Silesia Protech → M3 SP - Reklamacje • warehouse_id 25817.

### REKLAMACJE • TT

Towar firmowy (MY), firma Tracer Team → M3 TT - Reklamacje • warehouse_id 25821.

### KLIENT = BLOKADA

REKLAMACJE: „Właściciel towaru” = KLIENT → zakaz przyjęcia jako własny stan firmy i zakaz oznaczenia checkboxa. Nie zmieniaj właściciela po to, aby ominąć blokadę. Towar klienta pozostaje w ewidencji reklamacji.

### Własność nieustalona

Puste lub niejednoznaczne pole własności → WYMAGA DANYCH. „MY” potwierdza własność firmy, ale nie wybiera SP/TT. Sprawdź firmę z zamówienia, faktycznej sprzedaży/wydania i udokumentowanych transferów; przy sprzeczności poproś pracownika o wyjaśnienie.

### Źródło firmy

Potwierdzone zwroty po sprzedaży TT pozostają TT. Kaufland: TT; eBay: SP. Dla Allegro sprawdź konkretne konto sprzedawcy. Samo anulowane zamówienie nie dowodzi przekazania własności. Firma kupująca SP jest punktem wyjścia wyłącznie przy potwierdzonym zakupie i braku dowodu transferu do TT.

### Kontrola bieżąca

Nazwy i ID powyżej sprawdzono w Base 02.10.2026. Przed operacją odczytaj aktualne magazyny oraz katalog, do którego należą. Nie wybieraj magazynu Domyślny, M0, M1 lub MF na podstawie podobieństwa nazwy.

## 05  DOKUMENT PRZYJĘCIA I WYCENA

### Typ dokumentu

Docelowo zapisujemy numer PZ z Base. Dla zaakceptowanego przyjęcia z zewnątrz wybierz PZ właściwego magazynu i firmy. Najpierw sprawdź, czy towar nie został już przyjęty przez obsługę zwrotu, dostawę lub inny dokument.

### Towar już w magazynie

Jeśli towar ma już własny stan w Base, ustal potrzebny ruch zamiast ponownego przyjęcia. Przesunięcie między magazynami tej samej firmy może wymagać MM; przekazanie między SP i TT wymaga osobnej uzgodnionej procedury. Pokaż typ dokumentu pracownikowi przed wykonaniem.

### PW / BO i historia

W arkuszu istnieje kolumna „Cena do PW/BO — TT +3%”, a w historii Base są także PW i BO. Nazwa kolumny nie jest poleceniem utworzenia takiego dokumentu. Nie powtarzaj bilansu otwarcia ani historycznego przyjęcia. Dla uzgodnionego PW/MM zapisz rzeczywisty numer i typ, bez nazywania go PZ.

### OUTLET • reguła ceny

POTWIERDZONE 02.10.2026: cena dokumentu przyjęcia = aktualna „Cena Netto” w OUTLECIE, bez dodatkowego narzutu. Wartości dawnej kolumny „Cena dokument” przeniesiono do „Cena Netto” i usunięto tamtą kolumnę. Używaj zatwierdzonej kwoty z tego pola; nie przeliczaj jej ponownie.

### REKLAMACJE • reguła ceny

POTWIERDZONE 02.10.2026: cena dokumentu przyjęcia = aktualna „Cena netto” w REKLAMACJACH, bez dodatkowego narzutu. Przy braku kwoty lub sprzeczności ze źródłem najpierw uzgodnij ją z pracownikiem; nie zastępuj samodzielnie ceną sprzedaży ani ceną innego produktu.

### Bez dodatkowego +3%

Nie doliczaj +3% do ceny netto przy tworzeniu dokumentu, także dla TT. Kolumna „Cena do PW/BO — TT +3%” pozostaje materiałem historycznym i nie jest podstawą nowych przyjęć. Część przeniesionych dawnych kwot zawierała wcześniejszy narzut — zachowano je zgodnie z poleceniem, bez ponownego naliczania.

### Jednostki i suma

Podaj cenę jednostkową, walutę oraz informację netto/brutto. Sprawdź zgodność z polem ceny dokumentu w Base. Wartość pozycji = ilość × zaakceptowana cena jednostkowa; policz sumę dokumentu i sprawdź zaokrąglenia. Ceny sprzedaży w grupach cenowych są odrębną zmianą.

## 06  PROCEDURA DODANIA — KOLEJNOŚĆ JEST ISTOTNA

### 1 • Odczyt i duplikaty

Ponownie odczytaj wybrane wiersze, własność, checkbox i „Nr PZ system magazynowy”. Sprawdź Base po dotychczasowym numerze/ID dokumentu, zamówieniu oraz identyfikatorze operacji. Jeśli przyjęcie istnieje, odtwórz zapis w arkuszu zamiast tworzyć następne.

### 2 • Identyfikator operacji

Nadaj trwałe ID (np. UUID) jednemu fizycznemu przyjęciu. Zapisz je przed wysłaniem w notatce pozycji oraz uwagach dokumentu Base. REKLAMACJE: powiąż z istniejącym „ID”; OUTLET: z zamówieniem i SKU/EAN. Numer wiersza służy nawigacji, nie identyfikacji po sortowaniu.

### 3 • Jeden wykonawca

W notatce ustaw „MAG: W TOKU · OP: [ID]”. Jedną operację prowadzi jeden Codex/pracownik; inny wykonawca najpierw sprawdza jej stan. Jeśli nie można ustalić, kto wykonuje przyjęcie, zatrzymaj zapis — sam tekst statusu nie stanowi blokady technicznej.

### 4 • Propozycja i zgoda

Pokaż kartę/ID pozycji, firmę, nazwę i ID magazynu, typ dokumentu, product_id/SKU, ilości, jednostkowe ceny, sumę i opis. Dla zestawu pokaż wszystkie elementy. Wykonaj dokładnie zakres zaakceptowany przez pracownika.

### 5 • Szkic dokumentu

Utwórz jeden szkic dla jednej firmy, magazynu i zaakceptowanego zakresu. Zapisz document_id natychmiast w notatce komórki. Dodaj tylko zatwierdzone pozycje, ilości, ceny i uwagi. Szkic oraz samo utworzenie kartoteki nie oznaczają przyjęcia.

### 6 • Kontrola szkicu

Odczytaj pozycje szkicu i porównaj je z zaakceptowaną listą: product_id, komplet elementów, ilości, ceny, suma, magazyn i firma. Nie zatwierdzaj dokumentu z brakującymi lub zdublowanymi pozycjami.

### 7 • Zatwierdzenie w Base

Zatwierdź poprawny dokument. Następnie odczytaj jego status „Zatwierdzony”, pełny numer i wszystkie pozycje. Zweryfikuj skutki na właściwym magazynie; inne równoległe ruchy mogą zmieniać saldo, dlatego dowodem tej operacji są również pozycje potwierdzonego dokumentu.

### 8 • Numer PZ w arkuszu

Do „Nr PZ system magazynowy” wpisz dokładny pełny numer z Base (np. format M2/SP/…/PZ), aby dało się go wyszukać. Nie wpisuj wymyślonego numeru, samego document_id ani numeru zamówienia. document_id i zweryfikowany link przechowuj dodatkowo w notatce komórki.

### 9 • Checkbox na końcu

„Dodane do systemu magazynowego” = TRUE dopiero po potwierdzeniu własności firmowej oraz przyjęcia danej pozycji. Odczytaj zapisany numer i checkbox po zmianie. Nie zaznaczaj wierszy pominiętych, błędnych, szkiców ani towaru KLIENT.

### 10 • Raport i zapis awaryjny

Ustaw „MAG: DODANE · OP: [ID]” i podaj wynik pracownikowi. Jeśli dokument potwierdzono, ale zapis do Sheets się nie udał, zachowaj numer/ID i zgłoś „WERYFIKACJA: zapis arkusza”. Ponów wyłącznie zapis w arkuszu po odczycie Base.

## 07  ZESTAWY — KAŻDY ELEMENT ODDZIELNIE

### Skład i stan

Sprawdź skład zestawu w zamówieniu/kartotece, a pracownik potwierdza rzeczywiście otrzymane elementy i ich stan. Dla każdego ustal własny product_id/SKU/EAN, ilość, cenę, opis i ID elementu, np. [OP]/01. Brak identyfikatora lub potwierdzonego składu wymaga wyjaśnienia.

### Wiersze w arkuszu

Rozpisz elementy na osobne wiersze powiązane tym samym ID operacji i zamówieniem. Przy rozpisywaniu istniejącego wiersza zachowaj jego dane w notatce/audycie i rozdziel ilości oraz wartości. Nie pozostawiaj jednocześnie pełnej wartości zestawu i tych samych wartości na elementach — statystyki policzyłyby je dwa razy.

### Ilości elementów

Ilość elementu = liczba faktycznie przyjętych zestawów × liczba tego elementu w zestawie, skorygowana o potwierdzone braki. Dodatkowe sztuki i niekompletne zestawy rozpisz jawnie. Nie utożsamiaj 1 zestawu z 1 sztuką każdego elementu.

### Wycena elementów

Użyj kosztów elementów ze źródła. Gdy istnieje tylko cena całego zestawu, przedstaw podział do akceptacji; nie wpisuj pełnej ceny zestawu na każdym elemencie i nie dziel dowolnie. Suma wartości elementów musi równać się zaakceptowanej wartości przyjęcia. Różnicę zaokrągleń przypisz jawnie do jednego elementu.

### Bez podwójnego ruchu

Przyjmuj komponenty jako pozycje dokumentu. Sprawdź zachowanie zestawów w tym katalogu Base, aby system nie rozbił ich drugi raz. Nie przyjmuj równolegle produktu nadrzędnego i jego komponentów. Nie twórz zbędnych kopii istniejących kartotek.

### Wspólny lub różne PZ

Jeśli wszystkie elementy są na jednym zatwierdzonym PZ, każdy ich wiersz otrzymuje ten sam pełny numer oraz własny item_id/pozycję w notatce. Jeżeli przyjęto je różnymi dokumentami, każdy wiersz otrzymuje swój numer; notatka grupy zawiera zestawienie wszystkich dokumentów.

### Przyjęcie częściowe

Dla każdego elementu zapisz osobny wynik. Grupa ma status CZĘŚCIOWO, dopóki są nieprzyjęte elementy. Po przerwaniu odczytaj potwierdzone dokumenty i szkice; kontynuuj tylko brakujące elementy. Potwierdzonych pozycji nie przyjmuj ponownie. Brakujące fizycznie części pozostają brakami.

### Przykład — dane umowne

2 zestawy, każdy: urządzenie 1 × 100 zł netto, akcesorium 2 × 20 zł netto, ładowarka 1 × 10 zł netto. Przyjęcie: urządzenia 2 szt., akcesoria 4 szt., ładowarki 2 szt.; razem 300 zł netto. Trzy osobne pozycje i trzy wiersze; cena jednostkowa nie jest ceną całego zestawu.

## 08  STATUSY I BŁĘDY — CZYTELNIE, BEZ ZALANIA TABELI

### GOTOWE / W TOKU

GOTOWE: komplet danych i zaakceptowana propozycja, checkbox FALSE. W TOKU: operacja wykonywana, checkbox FALSE aż do potwierdzenia. Zachowaj ID operacji przy każdym przejściu.

### DODANE / CZĘŚCIOWO

DODANE: potwierdzone przyjęcie pozycji, pełny numer PZ, checkbox TRUE. CZĘŚCIOWO: tylko część grupy przyjęta; checkboxy TRUE wyłącznie przy potwierdzonych elementach. Raportuj brakujące elementy i ich przyczyny.

### WYMAGA DANYCH / BLOKADA

WYMAGA DANYCH: brak firmy, własności, ceny, ilości, dopasowania lub składu zestawu. BLOKADA KLIENT: własność klienta. Krótko wskaż, co pracownik ma wyjaśnić. Checkbox FALSE, bez nowego ruchu magazynowego.

### BŁĄD / WERYFIKACJA

BŁĄD: potwierdzona odmowa wykonania, np. brak uprawnień lub błędny product_id. WERYFIKACJA: timeout, utrata połączenia lub nieznany wynik; najpierw sprawdź Base. Brak odpowiedzi nie dowodzi braku przyjęcia. Nie ponawiaj zapisu w ciemno.

### Miejsce komunikatów

OUTLET: krótki wiersz „MAG: [STATUS] · OP: [ID]” w „Notatka AI”. REKLAMACJE: w „Notatka”. Zachowaj wcześniejsze notatki. Szczegóły, kod błędu, datę, etap, dokument_id/item_id i następny krok umieść w notatce komórki (Wstaw → Notatka); nie wklejaj stosu błędów do widocznej tabeli.

### Spokojne oznaczenia

Status ma być krótki i filtrowalny. Jeśli dodawane jest formatowanie statusów: DODANE — delikatna zieleń; WYMAGA DANYCH/CZĘŚCIOWO/WERYFIKACJA — jasny bursztyn; BLOKADA/BŁĄD — subtelny róż tylko w komórce statusu. Nie nadpisuj kolorów wieku przyjęcia ani nie barw całych wierszy na czerwono.

### Ponowienie i spójność

Numer PZ bez checkboxa → sprawdź dokument i odtwórz wynik. Checkbox bez numeru → ustal wcześniejsze przyjęcie; nie twórz nowego tylko z powodu braku numeru. Po poprawieniu danych ponów wyłącznie niepotwierdzony etap, po odczycie wcześniejszego wyniku.

## 09  DLA CODEXA — WYKONANIE TECHNICZNE

### Dostęp i aktualna wersja

Przed każdą sesją przeczytaj tę kartę i aktualne dane obsługiwanych pozycji. Potrzebujesz dostępu do tego arkusza i właściwego konta Base z uprawnieniami do magazynu. Arkusz nie nadaje dostępu ani nie powoduje trwałego „nauczenia” innego Codexa. Nie wpisuj tokenów, haseł ani sekretów do komórek, notatek lub rozmowy.

### Kontrola KLIENT w każdej drodze

Istniejąca blokada onEdit odznacza checkbox dla KLIENT przy ręcznej edycji. Zapisy przez API/skrypt nie wywołują onEdit. Codex musi sam sprawdzać aktualną własność przed dokumentem i przed końcowym checkboxem, także przy imporcie, zestawie i wznowieniu.

### Odczyt zamówienia / produktu

API: getOrders z order_id dla numeru BL; filter_external_order_id dla numeru marketplace. Następnie odczytaj getInventories, getInventoryWarehouses, getInventoryProductsList oraz getInventoryProductsData i potwierdź product_id w odpowiednim katalogu. Korzystając z panelu, wykonaj te same kontrole na widocznych danych.

### Kartoteka a przyjęcie

Użyj istniejącego produktu lub wariantu. Nową kartotekę twórz dopiero po sprawdzeniu braku odpowiednika i uzgodnieniu z pracownikiem. Opis stanu konkretnego zwrotu zapisuj w uwagach pozycji/dokumentu; nie nadpisuj globalnego opisu wspólnej kartoteki. Bezpośrednia zmiana stanu omija dokument i nie zastępuje przyjęcia.

### API • szkic

addInventoryDocument: warehouse_id, document_type, uzgodnione daty oraz notes z ID operacji i odniesieniem do arkusza/zamówienia. Typy API: 0 = PZ, 1 = PW, 4 = MM, 5 = BO. W wyniku sprawdź status i zapisz document_id; dokument jest na tym etapie szkicem.

### API • pozycje

addInventoryDocumentItems: document_id oraz items z product_id, quantity i zatwierdzoną jednostkową price; comments dla stanu/braków, opcjonalnie serial_no/location_name. Uwagi pozycji mają limit 255 znaków, dokumentu 500 znaków — pełny opis zachowaj w notatce arkusza. Odczytaj i sprawdź pozycje przed zatwierdzeniem.

### API • zatwierdzenie i odczyt

setInventoryDocumentStatusConfirmed(document_id) wykonuje ruch magazynowy. Po nim getInventoryDocuments(filter_document_id) musi wskazywać document_status = 1 i pełny full_number. getInventoryDocumentItems musi potwierdzać właściwe product_id, quantity, price, item_id i sumy. Odczytaj wszystkie strony wyników.

### API • wyniki i wznowienie

Sprawdź status SUCCESS/ERROR każdej odpowiedzi, a potem rezultat biznesowy. Po nieznanym wyniku szukaj dokumentu/pozycji po zachowanym ID i ID operacji w uwagach; odczytuj istniejący szkic przed dodaniem pozycji. Nie zakładaj, że ponowne addInventoryDocument albo addInventoryDocumentItems jest bezpieczne i nie tworzy duplikatów.

### Zapis i równoległe zmiany

Tuż przed zapisem porównaj bieżącą firmę, własność, produkt, ilość i cenę z zaakceptowaną propozycją. Zmiana wymaga wyjaśnienia. Dopisz wynik po trwałym ID, zachowaj walidację checkboxa i zapisz rzeczywiste TRUE/FALSE. Nie usuwaj potwierdzonego dokumentu ani nie koryguj stanu automatycznie po błędzie arkusza.

## 10  ŹRÓDŁA I CHECKLISTA PRZED PIERWSZYM PRZYJĘCIEM

### Base • magazyny i wyszukiwanie

Sprawdzono nazwy/ID oraz istniejący zatwierdzony PZ Outlet SP: 02.10.2026. Wyszukiwanie numeru: Produkty → Kontrola magazynu → Dokumenty magazynowe → Filtrowanie dokumentów; użyj numeru, magazynu, typu, miesiąca i roku. Panel: https://panel.baselinker.com/inventory_documents

### Base • zasady dokumentów

https://base.com/pl-PL/pomoc/wiedza/dokumenty-magazynowe/

### Base • zamówienia / katalog

https://api.baselinker.com/?method=getOrders • https://api.baselinker.com/?method=getInventoryProductsData

### Base • utworzenie dokumentu

https://api.baselinker.com/?method=addInventoryDocument

### Base • pozycje dokumentu

https://api.baselinker.com/?method=addInventoryDocumentItems • https://api.baselinker.com/?method=getInventoryDocumentItems

### Base • potwierdzenie / numer

https://api.baselinker.com/?method=setInventoryDocumentStatusConfirmed • https://api.baselinker.com/?method=getInventoryDocuments

### Google • ograniczenia onEdit

https://developers.google.com/apps-script/guides/triggers#restrictions

### Kontrola przed wykonaniem

Dostęp ✓ • właściwy produkt/elementy ✓ • fizyczna ilość i stan ✓ • własność firmy i SP/TT ✓ • aktualny magazyn/katalog ✓ • brak wcześniejszego przyjęcia ✓ • uzgodniony typ i wycena ✓ • akceptacja pracownika ✓. Nierozwiązane pozycje zostają w arkuszu z krótkim statusem.

### Stan wdrożenia

Ta karta jest instrukcją wykonywania operacji przez Codexa; nie uruchamia automatycznej integracji ani automatycznej obsługi błędów. Działa osobna blokada checkboxa dla towaru KLIENT. Potwierdzona wycena: aktualna cena netto bez dodatkowego narzutu. Pierwsze przyjęcie wymaga odczytu danych, propozycji i polecenia pracownika.

## 11  DODAJ DO SM → IMPORT Z ARKUSZA DO WAREPILOT

### Cel karty

Pracownik lub Codex przygotowuje produkty w DODAJ DO SM. Dane trafiają do strony add_product_to_catalog.html przez kopiowanie i wklejanie. Sam wpis w arkuszu nie wykonuje operacji w BL. Po uzupełnieniu pracownik wydaje polecenie przetworzenia uzgodnionych pozycji.

### Blok importu A–K

Dokładna kolejność: sku | akcja | firma | typ_produktu | cena_netto | ilosc | zamowienie | magazyn_zrodlowy | magazyn_docelowy | opis | dokument. Nagłówki są w wierszu 1, produkty od wiersza 2. Nie zmieniaj nazw ani kolejności.

### Pomocnicze L–Q

L = własność MY/KLIENT; M = automatyczna kontrola; N = pełny numer PZ; O = źródło i trwałe ID produktu; P = krótki błąd/uwagi; Q = rzeczywiste ID operacji HTML. Te kolumny pozostają tylko w arkuszu — NIE kopiuj ich do HTML.

### Przygotowanie danych

Codex odczytuje zamówienie i katalog, a pracownik potwierdza fizyczny produkt, ilość, stan, własność, spółkę oraz wycenę. Uzupełnij A–K, L=MY i jednoznaczne źródło w O. Nie kopiuj pozycji bez potwierdzonej własności firmy. M nie zastępuje kontroli źródła ani walidacji strony.

### sku

Dokładne źródłowe SKU, jako tekst. Nie zastępuj go EAN ani nazwą. Zera na początku muszą pozostać. Produkt niestanowy jest wyszukiwany w katalogu bazowym; stanowy w M1 właściwej spółki.

### akcja

W tym szablonie przyjęć wybierz zwrot, reklamacja albo zwrot_allegro. Wydanie, przesunięcie oraz kopiowanie kartoteki obsługuj w pełnym formularzu HTML po osobnym uzgodnieniu; mają inne reguły źródła, wyceny i dokumentów.

### firma

sp = Silesia Protech; tt = Tracer Team. Wybór musi wynikać z potwierdzonej własności i dokumentów, nie wyłącznie z miejsca zakupu ani domyślnej wartości. KLIENT nie może być dodawany do magazynu firmy.

### typ_produktu

niestanowy = źródłowa kartoteka w katalogu bazowym; stanowy = źródło w M1 danej spółki. To określenie źródła w systemie, nie opis sprawności. Zwrot Allegro wymaga niestanowy. Sprawdź rzeczywistą kartotekę.

### cena_netto

Cena JEDNEJ sztuki w PLN, z aktualnej Cena netto w OUTLECIE/REKLAMACJACH lub uzgodnionego dokumentu źródłowego. Nie dodawaj +3%. Wpisz liczbę nieujemną, np. 49,90, bez zł i separatorów tysięcy. Zero jest poprawne. Nie wpisuj wartości całego zestawu przy każdym elemencie.

### ilosc

Jawnie wpisz ilość większą od zera. Więcej sztuk tego samego produktu w tej samej operacji wpisz w jednym wierszu z właściwą ilością. Strona dopuszcza części dziesiętne; używaj ich tylko dla właściwej jednostki produktu.

### zamowienie

Numer zamówienia jako tekst; obowiązkowy dla zwrot_allegro, opcjonalny dla zwykłego zwrotu i reklamacji. Reklamacja z numerem domyślnie otrzymuje SKU:ZAMOWIENIE; Allegro SKU:ZAMOWIENIE-ZA. Przy zwykłym przyjęciu do M1 SKU pozostaje źródłowe.

### magazyn_zrodlowy

Dla wszystkich trzech akcji przyjęcia pozostaw H puste. Źródło wynika z typ_produktu. Wypełnienie H dla zwrotu/reklamacji jest błędem w parserze HTML.

### magazyn_docelowy

W I wpisz kod, nie ID: M2 = outlet; M3 = reklamacje; M1 = stanowe; M0 = główny. Spółkę określa firma. Szablon wymaga jawnego celu; puste pole HTML może skierować zwrot stanowy do M1, a reklamację do M3. Potwierdź magazyn przed wykonaniem.

### opis i stan

Dla reklamacji opis jest obowiązkowy. Zapisz konkretny stan, uszkodzenia i braki. Import 11-kolumnowy stosuje domyślnie zwrot=nowy i reklamacja=oczekuje. Jeśli produkt jest powystawowy lub ma status outlet, po dodaniu do sesji ustaw odpowiedni stan w pozycji formularza i ponownie sprawdź magazyn oraz opis.

### dokument

Wpisz jawnie nowy albo szkic. nowy tworzy i potwierdza PZ; szkic pozostawia go niepotwierdzonym. brak jest dopuszczalne technicznie, wymaga osobnego uzgodnienia i nie wyłącza wszystkich skutków akcji. Puste pole w HTML oznacza nowy, także dla M2 i M3.

### Własność i kontrola

Własność sprawdź w źródłowej reklamacji bezpośrednio przed importem i wykonaniem. KLIENT = BLOKADA, bez dodawania do sesji. HTML nie zawiera pola własności. M pokazuje gotowość tylko przy podstawowo kompletnych danych. Wiersze z błędem, nieustaloną własnością, wynikiem lub ID istniejącej sesji wymagają sprawdzenia zamiast ponownego importu.

### Kopiowanie z nagłówkami

Skopiuj tylko gotowe wiersze w kolumnach A–K wraz z A1:K1. Przykład dla 10 kolejnych produktów: A1:K11. Nie wybieraj całego arkusza ani L–Q. Pozostaw puste pola wewnątrz zakresu na swoich miejscach; nie przesuwaj danych w lewo.

### Wklejenie i podgląd

W HTML wybierz Importuj → Wklej z arkusza. Wklej do pola Dane z arkusza, pozostaw opcję „Wklejam same wartości, bez nagłówków” WYŁĄCZONĄ i kliknij Pokaż podgląd. Przy kopiowaniu wyłącznie A2:K… zaznacz tę opcję; wtedy konieczna jest dokładna kolejność 11 kolumn.

### Dodaj do sesji

Sprawdź każdy wiersz podglądu: SKU, spółkę, źródło, cel, ilość, jednostkową cenę i plan PZ. Błąd dowolnej pozycji blokuje dodanie całej partii; popraw arkusz i wygeneruj nowy podgląd. Dodaj do sesji dopisuje kolejkę i nie wykonuje jeszcze ruchu magazynowego. Zapisz wygenerowane ID operacji w Q.

### Przetworzenie

Po ewentualnym ustawieniu stanu powystawowy/outlet i kontroli kartotek pracownik wydaje polecenie wykonania konkretnych pozycji. Codex używa Przetwórz sesję i standardowego potwierdzenia strony. Potwierdzenie dokumentu wykonuje ruch; nie uznawaj podglądu ani dodania do sesji za przyjęcie.

### Zestawy

Rozpisz każdy faktycznie przyjęty element na osobny wiersz: jego SKU, ilość, jednostkowa cena, stan i magazyn. W opisie i źródle O podaj wspólny identyfikator zestawu i wskazanie elementu. Nie dodawaj równocześnie całego zestawu i jego części, jeżeli spowodowałoby to podwójny zapas.

### Wartość elementów

Ceny wynikają z dokumentu źródłowego lub uzgodnionego podziału. Suma ilość × cena netto dla przyjmowanych elementów musi odpowiadać uzgodnionej wartości. Nie rozdzielaj ceny arbitralnie i nie przypisuj pełnej ceny zestawu do każdego elementu. Różnice zaokrągleń uzgodnij przed dokumentem.

### Dokument dla zestawu

Domyślnie nowy/szkic tworzy osobny PZ dla każdego wiersza, także elementu zestawu. Jeśli pracownik chce wspólny PZ, skonfiguruj w HTML istniejący, niepotwierdzony PZ z jego rzeczywistym liczbowym ID: wcześniejsze elementy jako istniejacy_szkic, ostatni jako istniejacy. Ten rozszerzony tryb wymaga formularza; nie dopisuj id_dokumentu do standardowego bloku A–K.

### Zapis PZ i operacji

Po odczycie rzeczywistego wyniku wpisz w N pełny numer PZ widoczny w BL, a w Q ID operacji strony. Zachowaj identyfikator dokumentu i produktów w uwagach źródłowej pozycji. Przenieś pełny PZ również do kolumny Nr PZ system magazynowy w odpowiednim wierszu OUTLETU/REKLAMACJI. Dla zestawu zachowaj mapowanie element → PZ, także gdy numery są różne.

### Szkic i brak dokumentu

Szkic nie potwierdza przyjęcia. Dopisz SZKIC w P i pozostaw główny checkbox Dodane do systemu magazynowego odznaczony. Przy świadomym brak nie wymyślaj numeru PZ; zachowaj opis rzeczywistego wyniku i uzgodniony powód. Wpisanie numeru w N oznacza tylko zapis wyniku, nie automatyczną weryfikację statusu BL.

### Błąd podglądu

Popraw wskazany fizyczny wiersz i pole. Używaj list wyboru, pojedynczej ceny bez waluty i tekstowego SKU. Tekst zawierający tabulatory, nowe linie lub cudzysłowy musi być prawidłowo cytowany przy kopiowaniu z arkusza; najwygodniejszy jest opis w jednym wierszu. Błędy zapisuj krótko w P, bez pełnych logów w tabeli.

### Błąd wykonania

Nie zmieniaj samowolnie produktu, własności ani ceny. Zapisz krótki błąd i następny krok w P, zachowaj Q oraz znane dane dokumentu. Najpierw sprawdź, które elementy zestawu już się udały; wznawiaj wyłącznie brakujące operacje po ustaleniu ich stanu.

### Niepewny wynik

Po timeout lub zerwaniu połączenia wpisz WYNIK NIEPEWNY w P. Sprawdź zachowaną sesję/ID operacji i istniejący PZ w BL przed próbą wznowienia. Nie importuj pozycji jako nowej i nie zmieniaj ID w celu ominięcia blokady duplikatu. Potwierdzony dokument nie może być tworzony drugi raz.

### Wynik a arkusz

Checkbox w głównej karcie zaznacz dopiero po odczycie potwierdzonego PZ oraz sprawdzeniu spółki, magazynu, elementów, ilości, cen i sum. Błąd zapisu do arkusza napraw przez dopisanie istniejącego wyniku. Sam zapis produktu w DODAJ DO SM nie powiększa wartości OUTLETU/REKLAMACJI w statystykach.

### Daty i pola rozszerzone

HTML domyślnie przyjmuje dzień importu jako datę przyjęcia i ostatniej akcji. Dla historycznego towaru ustaw prawdziwe daty w formularzu sesji przed wykonaniem. Stan, docelowe SKU, istniejący PZ, wydruk i inne pola rozszerzone ustawiaj tam; standardowe A–K pozostaje zgodne z trybem bez nagłówków.

### Limit i powtórzenia

Maksymalnie 500 niepustych pozycji i 2 MB na import; przygotowane wiersze 2–501. Większe partie podziel. Identyczne operacje są sprawdzane w pliku, bieżącej sesji i historii backendu. Kilka sztuk tego samego produktu w jednej operacji wpisuj przez ilosc, zamiast powielać wiersz.

### Sprawdzenie SKU

Parser weryfikuje format i reguły formularza. Istnienie produktu, dostępny zapas oraz stan dokumentu sprawdza zaplecze podczas operacji. Przed wykonaniem rozwiń pozycję sesji i użyj Wyszukaj, jeśli trzeba potwierdzić produkt. Do obsługi potrzebna jest aktualna strona i jej skonfigurowane zaplecze WarePilot.

### Potwierdzony format

Format odczytano z add_product_to_catalog.html oraz IMPORT_PRODUKTOW_CSV.md z katalogu Silesia_WarePilot, 02.10.2026. Po zmianie importu w stronie ponownie porównaj jej wzór z A1:K1. Przygotowanie arkusza nie uruchamia automatycznego przetwarzania ani zapisu PZ — wykonuje je Codex na polecenie pracownika.

## 12. PANEL MAGAZYNOWY — BEZ KOPIOWANIA

### Otwieranie

W arkuszu: Magazyn → Otwórz panel przyjęć. Osobny adres WWW wymaga wdrożenia Apps Script jako użytkownik korzystający z aplikacji.

### Pierwsza konfiguracja

Każdy pracownik ze zgodą na dostęp do arkusza autoryzuje Apps Script i zapisuje swój klucz WarePilot w panelu. Klucza nie zapisujemy w komórkach ani HTML.

### Źródło w kolumnie O

REKLAMACJE|ID, OUTLET|SKU|zamówienie lub NOWY|numer przyjęcia. Reklamacja zawsze musi wskazywać istniejącą REKLAMACJĘ. OUTLET wymaga jednoznacznego SKU i zamówienia.

### Twarda kontrola własności

L musi być MY. Serwer ponownie odczytuje aktualną własność, spółkę, SKU, zamówienie, cenę i ilość ze źródła przed zapisem. KLIENT i nieustalona własność blokują wykonanie.

### Cena i data

Cena netto jest ceną jednostkową dokumentu bez dodatku. Dla istniejącego produktu cena i ilość muszą zgadzać się ze źródłem. AA: historyczna data przyjęcia; pusta jest pobierana ze źródła. Dla NOWY wpisz datę.

### Stan produktu

AB: zwrot nowy/powystawowy; reklamacja oczekuje/outlet; zwrot_allegro pozostaje pusty. Produkt powystawowy i reklamacja wymagają opisu.

### Przebieg przyjęcia

Uzupełnij arkusz, odśwież panel, sprawdź podgląd SKU, spółki, magazynu, ilości, ceny, opisu i daty. Dopiero na jednoznaczną prośbę pracownika potwierdź przyjęcie. Samo uzupełnienie wiersza nie tworzy PZ.

### Wynik

R: status; S: czas; T: ID produktu; U: rzeczywiste ID PZ. N: numer PZ zwrócony przez Base. Jeśli pełny numer nie został zwrócony, N pokazuje jawnie ID PZ i uwagę — bez wymyślania numeracji.

### Szkic i brak dokumentu

DODANO wymaga confirmation_verified=true i document_status=1. SZKIC i KARTA BEZ STANU są osobnymi wynikami. Checkbox w źródle pozostaje odznaczony dla szkicu i karty bez dokumentu.

### Zestaw

Podgląd wykrywa zestaw. Rozbij w arkuszu tworzy wszystkie składniki z ilością przemnożoną przez liczbę zestawów i pustymi cenami. Wyceń każdy składnik; ich suma musi równać się wartości zestawu. Rodzica nie wysyłamy.

### Zestaw — potwierdzenie

Checkbox i numery PZ w źródle zestawu zapisujemy dopiero po potwierdzonym przyjęciu wszystkich składników. Po przerwanym rozbiciu Sprawdź składniki odtwarza brakujące wiersze bez nadpisania istniejącej wyceny.

### Przerwane połączenie

Nie kasuj Q ani ukrytych kolumn V–Z. Najpierw Sprawdź wynik. Zachowane ID i dokładne żądanie pozwalają odczytać wcześniejszy wynik, również gdy PZ powstał przed awarią zapisu do arkusza.

### Ponowienie

Ponów zapis najpierw wykonuje GET. POST dopuszczony wyłącznie dla failed albo potwierdzonego NOT_FOUND, z niezmienionymi danymi i tym samym ID. processing, needs_review i konflikt wymagają wyjaśnienia.

### Wcześniejszy duplikat

Backend może odtworzyć dawny PZ pod kanonicznym ID. Jego blokada duplikatów nie obejmuje ceny. Panel oznacza taki obcy wynik do sprawdzenia, zamiast uznawać go za korektę bieżącej ceny.

### Praca na liście

Pozycje są wysyłane kolejno po zatwierdzeniu podglądu listy. Po błędzie lista zatrzymuje się. Zamknięcie panelu wstrzyma kolejne pozycje; bieżąca operacja może zakończyć się w WarePilot. Po powrocie odczytaj jej wynik.

### Nowy produkt i statystyki

NOWY zapisuje wynik przyjęcia w kolejce. Kolejka nie jest uwzględniona w statystykach OUTLETU i REKLAMACJI. Uzupełnij właściwą kartę źródłową, gdy rejestrujesz nowy produkt dla tych statystyk.

### Format A–K

Pierwsze 11 kolumn zachowuje format wskazanego HTML. R–AB obsługują panel; V–Z są ukryte i automatyczne. Stary import z sekcji 11 pozostaje ścieżką ręczną. M jest kontrolą starego importu; dla panelu rozstrzyga status R.
