---
wersja: 0.1.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Kontrakt danych UZP

Oryginały: [oczekiwane-json](../02-materialy/organizator-uzp/oczekiwane-json/). Zachowuj ich treść; nie traktuj plików z komentarzami jak gotowego JSON Schema.

- Odwołanie: strony postępowania, zamówienie, daty i zaskarżona czynność. Dla wskazanych pól czynności decyduje pierwszy zarzut.
- Pełnomocnictwo: mocodawcy, podpisujący i pełnomocnicy. Stosuj reguły nazw osobowych ze wzorca.
- Przelew: data, kwota, rachunki, tytuł i numer transakcji zgodnie ze wzorcem.
- Rozróżniaj numer BZP, numer TED i numer wewnętrzny postępowania.
- Dodatkowy raport dowodów zapisuj poza ocenianym JSON-em, chyba że organizator potwierdzi inną zasadę.
- Nazwy plików wynikowych wynikają z nazwy wejściowej, a nie ze stałej nazwy klasy.
- Ustal dokładny wynik dla dokumentów negatywnych: plik o długości zero i `{}` to różne reprezentacje.

Do słownika przyczyn odwołania użyj pliku `czynnosc_powod_id_dict.md` z kopii materiałów, jeżeli jest obecny w przypiętej rewizji. Własna ścisła walidacja powinna być oddzielona od oryginałów.
