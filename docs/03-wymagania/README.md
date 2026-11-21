---
wersja: 0.2.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Wymagania UZP

Status implementacji: do wykonania. Doprecyzowania: [komunikaty UZP z Discorda](../01-zadanie/zrodla/UZP-Discord-doprecyzowania-2026-11-21.md). FAQ v1.0 i starsze pliki zachowano bez zmian.

| ID | Wymaganie | Kryterium odbioru | Podstawa |
|---|---|---|---|
| UZP-01 | Trzy klasy PDF i automatyczna klasyfikacja | właściwy kontrakt każdej klasy | FAQ, README |
| UZP-02 | PDF tekstowy; OCR opisane w FAQ | brak skanów bez tekstu w przykładach nie znosi automatycznie zakresu FAQ | FAQ 2/4; Discord 12:47 |
| UZP-03 | Ściśle właściwy format JSON | nazwy, typy i struktura według wzorców; dowody osobno | Discord 12:47 |
| UZP-04 | Brak zmyślonych danych | null w polach dopuszczających brak | FAQ 2/4 |
| UZP-05 | Python 3.13+ i requirements.txt | prosta instalacja, CLI i instrukcja | Discord 09:42, FAQ 12a |
| UZP-06 | input/output i zachowane nazwy bazowe oraz podfoldery | batch odtwarza drzewo | README |
| UZP-07 | Obcy dokument: pusty JSON z nazwą oryginału | nie pomijać wyniku; reprezentację pustego JSON potwierdzić | Discord 13:27, korekta 12:47 |
| UZP-08 | Otwarte komponenty i model możliwy do instalacji lokalnej | opis modelu, wersji i licencji | FAQ 3/4 |
| UZP-09 | API darmowe, płatne lub model na własnym serwerze | wariant dozwolony, pozostałe ograniczenia nadal obowiązują | Discord 11:23 |
| UZP-10 | Dostawca i serwer w wymaganym regionie | FAQ: UE; README: UE/EOG; konserwatywnie oba w UE | FAQ, README; Discord nie uchyla |
| UZP-11 | Laptop bez GPU, bez instalacji modelu na sprzęcie jury | LLM przez API; endpoint dostępny publicznie | Discord 12:47; README: i7, 16 GB |
| UZP-12 | Klucz płatnego API do oceny jury | przekazanie poza historią Git | Discord 11:28, FAQ |
| UZP-13 | Brak ogłoszonego limitu czasu testu | pomiar czasu pozostaje potrzebny; nie wprowadzać fikcyjnego limitu | Discord 12:47 |
| UZP-14 | Klasy i pola dodawane konfiguracją | rozbudowa bez przebudowy silnika | finał |
| UZP-15 | GUI opcjonalne i premiowane | PDF i JSON obok siebie | FAQ 12b, README |

Dane: 60 zestawów. `ground_truth.yaml` usunięto; referencją są pliki JSON. Testy są syntetyczne na podstawie prawdziwych przypadków. Brak skanów stwierdzono dla przykładów; nie potwierdzono ich wykluczenia z ukrytego testu.

[Kontrakt danych](kontrakt-danych.md), [zasady F1](../05-weryfikacja/zasady-f1.md), [pytania](../07-decyzje/pytania-otwarte.md).
