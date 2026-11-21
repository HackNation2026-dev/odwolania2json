---
wersja: 0.1.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Wymagania UZP

Status wszystkich pozycji: do implementacji lub weryfikacji.

| ID | Wymaganie | Kryterium odbioru | Źródło |
|---|---|---|---|
| UZP-01 | Trzy klasy PDF i automatyczna klasyfikacja | właściwy kontrakt dla każdej klasy | FAQ 1/4, README |
| UZP-02 | PDF tekstowy oraz OCR skanów | przykłady obu typów przetworzone | FAQ 2/4 |
| UZP-03 | Wynik zgodny z kontraktem organizatora | zgodne nazwy, typy, tablice i null | oczekiwane-json |
| UZP-04 | Brak wymyślonych wartości | null tylko zgodnie z kontraktem | FAQ 2/4 |
| UZP-05 | Python 3.13+ i requirements.txt | instalacja i start na maszynie testowej | README |
| UZP-06 | CLI z instrukcją | samodzielne uruchomienie przez jury | FAQ 12a |
| UZP-07 | input/output, identyczne nazwy bazowe i podfoldery | batch zachowuje strukturę katalogów | README |
| UZP-08 | Odrzucenie obcej klasy | wynik zgodny z wyjaśnioną definicją pustego JSON | README, negatywne/readme |
| UZP-09 | Otwarte komponenty i modele do instalacji lokalnej | identyfikacja wersji i warunków licencji | FAQ 3/4 |
| UZP-10 | API i dostawca w wymaganym regionie | udokumentowana lokalizacja dostawcy i serwera | FAQ: UE; README: UE/EOG |
| UZP-11 | Laptop i7, 16 GB RAM, bez GPU | powtarzalny start i pomiar zasobów | README |
| UZP-12 | Działający klucz API do testów jury, jeśli używany | konfiguracja testowa przekazana osobnym kanałem | FAQ, README |
| UZP-13 | Nowe klasy i pola przez konfigurację | zmiana konfiguracji bez przebudowy silnika | kryterium finału |
| UZP-14 | GUI PDF/JSON obok siebie | działający import i podgląd | opcjonalne, FAQ 12b |

[Kontrakt danych](kontrakt-danych.md) opisuje pułapki schematów. [Pytania](../07-decyzje/pytania-otwarte.md) obejmują warunki nierozstrzygnięte.
