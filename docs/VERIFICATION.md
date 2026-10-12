# Weryfikacja silnika 2.1.0

Weryfikacja wykonana 12.10.2026. Repo zawiera niezależną historię samego
silnika, bez historii wcześniejszego projektu Marketplace i prywatnych przypadków.

## Sprawdzone

- **84 testy** na danych umownych: dopasowanie modelu/wariantu i EAN/SKU,
  paginacja i cache, oznaczenie zakresu archiwum, wskazany BL bez skanu statusów,
  ceny vNN netto, historyczne brutto, alokacja, VAT/waluty/spółki, brak danych,
  dowód zgody, prywatna kolejka i jeden writer.
- Szybki tryb: pierwszy wynik bez kolejnej strony/statusu, cache z aktualnym
  odczytem, RMA w Notatkach i nazwanych polach, zachowane zera, powiązana pozycja
  zwrotu, konflikty oznaczeń, pominięcie odrzuconego BL, zdarzenie przed
  uzupełnieniem finansów i zachowanie kandydatury przy błędzie tego odczytu.
- Wspólny lokalny budżet API, bez stałego opóźnienia przy wolnym limicie;
  aktualizator dopuszcza kanoniczny origin i blokuje aktywny/niepewny wpis.
- Plan OUTLET i REKLAMACJE, w tym rekord KLIENT bez przyjęcia własnego stanu:
  rodzime wartości, daty, percent 0.23, tekstowe identyfikatory z zerami,
  checkbox FALSE, brak fikcyjnego PZ, zachowane formuły/notatki/formaty/walidacje.
- Wykrycie zmiany preimage, błędnego wyniku, niepoprawnego konta, niespójnej
  wyceny, błędnej listy wyboru, duplikatu i wcześniejszego przyjęcia.
- Rzeczywisty odczyt Base przez samodzielny adapter tego repo; celowany wariant
  w wersji 2.1 wymagał **3 żądań**, zwrócił pełny werdykt 22 pól, poprawną
  podstawę cen zakupu i właściciela z dokumentu. Zdarzenie pierwszego kandydata
  pojawiło się po **0.20 s**, przed odczytem faktur/przesyłek; całość po 0.44 s.
  Raport rzeczywistego przypadku pozostaje prywatny.
- Rzeczywisty podgląd po modelu z istniejącym cache: **0.59 s / 2 żądania**.
  Podgląd powiązania RMA: **0.23 s / 1 żądanie**, z jawnym brakiem odczytu
  oryginalnej karty i ceny. Są to pomiary konkretnych prób, nie gwarancja czasu.
- Rzeczywiste metadane Base potwierdziły standardowe pole **2 — Notatki**.
  Dopasowanie numeru wpisanego w notatkę/pole jest sprawdzone testami umownymi;
  nie deklarujemy produkcyjnego trafienia po notatce na podstawie samego odczytu
  definicji pól. Rejestr RMA i jego powiązanie odczytano w rzeczywistym API.
- Rzeczywiste metadane i rodzime komórki firmowego arkusza: parser odpowiedzi
  konektora rozpoznał 22 kolumny OUTLET, format VAT i walidacje. Odczytano
  wszystkie 136 wierszy instrukcji, sekcje 01–12 i kolejkę A–AB.
- Narzędzie Base blokuje mutacje przed wywołaniem sieci; token curl jest
  podawany wyłącznie przez stdin, bez argumentów procesu i pliku w repo.

## Granice tych dowodów

Test zapisu jest testem rzeczywistych kształtów żądań i odczytu na modelu
rodzimych komórek. W tej wersji nie dodano pozycji testowej do produkcji,
nie utworzono PZ ani odnogi z niezleconym wpisem. Pierwszy rzeczywisty wpis
i dispatch do odnogi wykonywane są po konkretnej zgodzie pracownika,
z obowiązkowym exact readbackiem. Dostęp do firmowych systemów i narzędzi
rozmów musi istnieć także na nowym PC.

Publiczny dostęp do repo i pobranie całego pakietu weryfikujemy przy dostarczeniu
linku. Produkcyjne receipt, SHA zdalnego commitu i potwierdzenie dostarczenia
maila są zapisane w prywatnym checkpointcie, poza publicznym Git.

## Powtórzenie testów

```powershell
py -3 -m unittest discover -s tests -v
```

Po zmianie źródła, schematu, kontraktu lub reguły powtórz właściwy test
i reprezentatywny pilot. Nie traktuj tagu wersji lub historycznego testu
jako dowodu bieżących danych konkretnego towaru.
