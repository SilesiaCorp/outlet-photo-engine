# Krótka i czytelna konwersacja

## Po otrzymaniu zdjęć

Rozpoznaj fakty z etykiety i stan opakowania. Jeśli pracownik mówi, że to
wszystkie dostępne zdjęcia/dane, nie pytaj ponownie o te same informacje.
Szukaj głębiej w systemach według OPERATING_GUIDE.md.

Stosuj FAST_SEARCH.md: niezależne tropy sprawdzane możliwie równolegle,
numery zwrotów pomocniczo. Pokaż najlepszego kandydata dotąd bez czekania
na pełny przegląd, a następnie pracuj dalej w Base i archiwum. Uzupełnienie
finansów i pól wykonuj dla proponowanej pozycji.

Odpowiedź:

1. **Najlepszy kandydat dotąd: BL [numer], [model / SKU].** Jedno zdanie
   uzasadnienia i oznaczenie „wstępny”, dopóki powiązanie sztuki nie jest potwierdzone.
   Ta informacja zawsze jest na początku odpowiedzi z wynikiem.
2. **Produkt i wynik:** marka, pełny model, EAN, stan opakowania;
   liczba pasujących kartotek i zamówień w sprawdzonym dotąd zakresie;
   krótko zakres API/archiwum. Nie sugeruj kompletnego przeglądu po pierwszym trafieniu.
3. **Kandydaci:** mała tabela `BL | SKU | data/status | dowód | wyjątek`.
4. **Dalsza weryfikacja:** sprawdzam pozostałe zamówienia Base i archiwum.
   Przy mocniejszym trafieniu pokaż: „Aktualizacja: lepszy kandydat BL ... — [powód]”.
   Nie wymyślaj procentów pewności i nie raportuj niezmienionego stanu.
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
| Właściciel przerywa dalsze poszukiwania lub przechodzi do kolejnego produktu | Potwierdź ostatnio jednoznacznie pokazane dopasowanie, zapisz źródło tego zdarzenia, zakończ szukanie poprzedniej sztuki i obsłuż nową. |
| „Zatwierdzam, dodaj do arkusza” po jednoznacznej propozycji | Zachowaj tę zgodę, enqueue i przekazanie osobnej rozmowie. Nie pytaj drugi raz o ten sam zakres. |
| „Dodaj BL [numer], ten produkt ze zdjęcia do OUTLETU” | Odczytaj konkretną pozycję, przygotuj manifest z faktów i wykonaj zlecony wpis w odnodze; braki zostają jawne. |
| „Dodaj do magazynu zaakceptowane pozycje” | Osobna zgoda na przyjęcie, z firmą/magazynem, wyceną, ilościami i dokumentem. |

Jeśli przygotowana propozycja zawierała kilka alternatyw lub nieustaloną
cenę/spółkę/ilość, samo „tak” nie wybiera za człowieka brakujących wartości.
Znane dane można wpisać jako jawnie zaakceptowany szkic, pozostałe pozostają
puste z WYMAGA DANYCH. Zakres wpisu nadal trafia do odnogi.

Reguła przejścia została wybrana przez właściciela: nie pytaj ponownie,
czy ostatnio pokazany kandydat był właściwy. Zapisz prywatnie numer BL,
pozycję/SKU, ostatni pokazany wynik, rzeczywistą wiadomość lub zdarzenie
właściciela i czas jako `accepted_after_user_transition`. Decyduje kandydat
pokazany pracownikowi, nie nowszy wynik obliczony, lecz jeszcze niewyświetlony.
Jawne odrzucenie lub korekta człowieka ma pierwszeństwo przed tą regułą.
Techniczna awaria, timeout, utrata połączenia, samo zakończenie skryptu i cisza
nie potwierdzają dopasowania. Jeśli nie wskazano jednego najlepszego kandydata,
zachowaj nierozstrzygnięcie zamiast wybierać dowolny numer z tabeli.

Potwierdzenie dopasowania wykorzystaj przy przygotowaniu wpisu. Jeśli
istnieje już zgoda na pokazany wpis, przeprowadź go w odnodze zgodnie z jej
zakresem. Nie uzupełniaj nieznanej ceny, ilości lub stanu z samego przejścia
do nowego produktu. Dokładny manifest wpisu nadal przechodzi bramki SHEET_ENTRY.md.

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
