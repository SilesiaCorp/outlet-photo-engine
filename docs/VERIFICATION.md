# Weryfikacja silnika 2.0.0

Weryfikacja wykonana 12.10.2026. Repo zawiera niezależną historię samego
silnika, bez historii wcześniejszego projektu Marketplace i prywatnych przypadków.

## Sprawdzone

- **53 testy** na danych umownych: dopasowanie modelu/wariantu i EAN/SKU,
  paginacja i cache, oznaczenie zakresu archiwum, wskazany BL bez skanu statusów,
  ceny vNN netto, historyczne brutto, alokacja, VAT/waluty/spółki, brak danych,
  dowód zgody, prywatna kolejka i jeden writer.
- Plan OUTLET i REKLAMACJE, w tym rekord KLIENT bez przyjęcia własnego stanu:
  rodzime wartości, daty, percent 0.23, tekstowe identyfikatory z zerami,
  checkbox FALSE, brak fikcyjnego PZ, zachowane formuły/notatki/formaty/walidacje.
- Wykrycie zmiany preimage, błędnego wyniku, niepoprawnego konta, niespójnej
  wyceny, błędnej listy wyboru, duplikatu i wcześniejszego przyjęcia.
- Rzeczywisty odczyt Base przez samodzielny adapter tego repo; celowany wariant
  wymagał 6 żądań, zwrócił pełny werdykt 22 pól i poprawną podstawę cen zakupu.
  Raport rzeczywistego przypadku pozostaje prywatny.
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
