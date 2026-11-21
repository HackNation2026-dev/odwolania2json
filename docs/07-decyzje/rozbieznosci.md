---
wersja: 0.4.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Rozbieżności UZP i obowiązujące korekty

Źródło zmian: [Discord przekazany przez użytkownika](../01-zadanie/zrodla/UZP-Discord-doprecyzowania-2026-11-21.md). Oryginałów nie nadpisano.

| Temat | Starszy zapis | Nowsze wyjaśnienie | Stan |
|---|---|---|---|
| Finał | PDF 50/30/20 | FAQ, README i komunikat 09:38: 50/50 | przyjąć 50/50 |
| Dane | 39 zestawów / 117 PDF | 12:47: 60 zestawów | skorygowane |
| ground_truth.yaml | zapowiedziany | 12:47: usunięty jako scalone JSON-y | nie oczekiwać pliku |
| Test | opis mówi o realnych sprawach | 12:47: syntetyczne dokumenty z prawdziwych przypadków | skorygowane |
| OCR | FAQ wymaga uwzględnienia skanów | 12:47: brak skanów bez tekstu w przykładach | nie uchyla zakresu testu |
| API płatne | pytanie uczestników | 11:23: wszystkie 3 warianty dozwolone; 11:28: przekazać klucze | dozwolone |
| Sprzęt | lokalne uruchomienie bez GPU | 12:47: bez instalacji modelu, API i publiczny endpoint | klient lokalny, LLM zdalny |
| Obcy plik | 12:47: nie zwracać JSON | 13:27: pusty JSON z nazwą oryginału | 13:27 zastępuje 12:47 |
| Listy | brak reguły | 13:26: dopasowanie po treści | wyjaśnione |
| Długie teksty | ogólne 80% | 13:26: lista konkretnych pól | algorytm nadal nieznany |
| Region | FAQ UE, README UE/EOG | brak nowego doprecyzowania | wyjaśnić |

Nie utożsamiaj braku opłaty licencyjnej za model z brakiem opłaty za usługę API. Pozostałe ograniczenia licencji i lokalizacji nie zostały uchylone.

## Uzupełnienie 0.4.0 (2026-11-21)

| Temat | Źródło | Stan |
|---|---|---|
| `czynnosc_opis` w referencjach | `main` `7590db8`: 5 plików poprawiono na brzmienie słownika „Odpowiedzi/wyjaśnienia do SWZ” | wskazuje, że opis ma dosłownie odpowiadać słownikowi |
| `ground_truth.yaml` | Discord 13:27: usunięty; gałąź `dane`: 39 plików nadal istnieje | zachowane jako starszy materiał, nie referencja aktualna |
| Wzorzec `oczekiwane-json/odwolanie.json` | różne wersje w `main`, `dane` i `mateusz-readme-changes` | wszystkie wersje zachowane; aktualna w `main` |
