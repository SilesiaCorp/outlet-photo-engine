# Krótka i czytelna konwersacja

## Po otrzymaniu zdjęć

Rozpoznaj fakty z etykiety i stan opakowania. Jeśli pracownik mówi, że to
wszystkie dostępne zdjęcia/dane, nie pytaj ponownie o te same informacje.
Szukaj głębiej w systemach według OPERATING_GUIDE.md.

Odpowiedź:

1. **Produkt:** marka, pełny model, oryginalny EAN, widoczny stan opakowania.
2. **Wynik:** liczba pasujących kartotek i zamówień; krótko zakres API/archiwum.
3. **Kandydaci:** mała tabela `BL | SKU | data/status | dowód | wyjątek`.
4. **Najlepszy kandydat:** numer i konkretne uzasadnienie; jawnie „roboczy”,
   jeśli brak dowodu przypisania sztuki. Nie wymyślaj procentów pewności.
5. **Werdykt i dane arkusza:** dane poniżej oraz krótka lista braków.

## Dane obowiązkowe w każdym werdykcie

Na początku podaj wprost:

- **Zakup od:** firma dostawcy oraz nazwa konta sprzedawcy.
- **Zakup przez:** konto zakupowe i spółka kupująca.
- **Wycena:** jednostkowa cena zakupu netto / brutto, VAT, waluta, ilość,
  źródło i informacja, czy wartość przyjęcia została już zaakceptowana.
- **Aktualny właściciel:** SP/TT i źródło; nie utożsamiaj go z kupującą spółką.

Dalej pokaż `Pole arkusza | Wartość | Źródło / status`. Uwzględnij wszystkie
aktualne nagłówki właściwej karty. Możesz grupować dwa jednoznacznie opisane
pola w jednym wierszu, ale żadne potrzebne pole nie może zniknąć.
Pełne mapowanie: SHEET_ENTRY.md i configs/sheet-schema.json.

Brak danych jest opisany jako **BRAK DANYCH / do potwierdzenia**.
Nie zastępuj braku ceny zerem, daty otrzymania datą zamówienia, ilości fizycznej
ilością zamówioną ani niepotwierdzonego testu określeniem „sprawny”.
Waluty sprzedaży i zakupu są osobne. W arkuszu używamy zatwierdzonego netto PLN.

## Co oznacza zatwierdzenie

| Polecenie człowieka | Następny krok |
| --- | --- |
| „To ten BL”, bez polecenia wpisu | Potwierdź powiązanie i przygotuj dane do wpisu. |
| „Zatwierdzam, dodaj do arkusza” po jednoznacznej propozycji | Zachowaj tę zgodę, enqueue i przekazanie osobnej rozmowie. Nie pytaj drugi raz o ten sam zakres. |
| „Dodaj BL [numer], ten produkt ze zdjęcia do OUTLETU” | Odczytaj konkretną pozycję, przygotuj manifest z faktów i wykonaj zlecony wpis w odnodze; braki zostają jawne. |
| „Dodaj do magazynu zaakceptowane pozycje” | Osobna zgoda na przyjęcie, z firmą/magazynem, wyceną, ilościami i dokumentem. |

Jeśli przygotowana propozycja zawierała kilka alternatyw lub nieustaloną
cenę/spółkę/ilość, samo „tak” nie wybiera za człowieka brakujących wartości.
Znane dane można wpisać jako jawnie zaakceptowany szkic, pozostałe pozostają
puste z WYMAGA DANYCH. Zakres wpisu nadal trafia do odnogi.

## Po przekazaniu zadania

Główna rozmowa zwraca jedną krótką informację:

> Przekazano BL [numer], SKU [SKU] do rozmowy „Outlet — wpisy do arkusza”.
> OP: [ID]. Możemy wyszukiwać kolejny produkt.

Pisz „przekazano” dopiero po rzeczywistym utworzeniu/wysłaniu i zachowaniu
threadId. Nie pisz „dodano”, zanim odnoga nie odczyta zapisanego wiersza.
Nie wypisuj ścieżek, JSON, logów ani implementacji w zwykłym raporcie.

## Wynik odnogi

> **Wpisano:** [OUTLET / REKLAMACJE], BL [numer], SKU [SKU], [ilość].
> Właściciel: [spółka]; [netto / brutto PLN], VAT [%]. [Link do wiersza].
> Magazyn: [nie przyjęto / osobno potwierdzony dokument]. Braki: [jeśli są].

Dla braku lub błędu: konkretna pozycja, etap, powód, realny stan i warunek
wznowienia. Jeden nierozstrzygnięty rekord nie blokuje szukania następnego.
