---
wersja: 0.6.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Pytania UZP — stan po komunikatach Discord

## Wyjaśnione w przekazanych komunikatach

- 60 zestawów; liczba 39 z prezentacji jest nieaktualna.
- ground_truth.yaml usunięto; używać referencyjnych JSON-ów.
- Testy syntetyczne na podstawie prawdziwych przypadków.
- JSON ściśle według formatu; listy dopasowywane po treści.
- API darmowe, płatne i własny model po API są dopuszczone.
- Jury ma Internet; endpoint publiczny; model nie jest instalowany na laptopie jury.
- Brak ogłoszonego limitu czasu.
- Obcy dokument: pusty JSON z nazwą oryginału; komunikat 13:27 zastępuje 12:47.
- Finał 50/50; słownik kodów przyczyn jest dostępny.

## Nadal otwarte

| ID | Pytanie | Wpływ |
|---|---|---|
| U-Q01 | Jaką miarą wylicza się 80% i jak normalizuje wartości? | F1 |
| U-Q02 | Jak agregowane są pola/dokumenty i dopasowywane wieloelementowe listy? | F1 |
| U-Q03 | Czy pusty JSON to dokładnie `{}`? Jak traktować null i brak klucza? | wynik |
| U-Q04 | Jaki bezpieczny kanał klucza, budżet i okres dostępu API dla jury? | uruchomienie |
| U-Q05 | FAQ UE a README UE/EOG — jaki zakres geograficzny obowiązuje? | dostawca |
| U-Q06 | Czy jakikolwiek pomocniczy moduł Rust jest dozwolony przy języku Python 3.13+? | stos |
| U-Q07 | Jak przeliczyć rozmiar modelu na punkty, zwłaszcza dla MoE? | finał |
| U-Q08 | Czy ukryty test może zawierać skany bez warstwy tekstowej? | OCR |
| U-Q09 | Które konta jury dodać do prywatnego repo? | zgłoszenie |
| U-Q10 | Która dokładnie rewizja kontraktów będzie użyta przez ewaluator? | zgodność |

Brak skanów w przykładach nie jest potwierdzeniem ich braku w teście. Brak limitu czasu nie oznacza, że awaria lub niedostępny endpoint jest akceptowany.

## Odpowiedzi 2026-11-21 (przekazane przez użytkownika)

Źródło: [odpowiedzi mentora](../01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md). Kanał: rozmowa użytkownika z mentorem UZP, przekazana asystentowi.

| ID | Stan | Odpowiedź |
|---|---|---|
| U-Q01, U-Q02 | częściowo | Liczone TP, TN, FP, FN (Discord 11:26). Miara podobieństwa 80%, normalizacja i agregacja nadal nieznane; przyjęta robocza interpretacja w [ADR-005](ADR-005-interpretacja-f1.md). |
| U-Q03 | częściowo | Obcy dokument: `{}` pod nazwą pliku — potwierdzone. `null` a brak klucza: nie pytano. |
| U-Q05 | zamknięte | Hosting w Europie; modele i inne komponenty mogą być po API, jeśli spełniają wymogi. |
| U-Q06 | nieaktualne | Dostarczenie wyłącznie przez pip; Docker tylko deweloperski. |
| U-Q07 | częściowo | Liczy się największy model, także w systemie wieloagentowym. Przelicznik na punkty nieznany. |
| U-Q08 | zamknięte | Tak: pliki tekstowe, skany i dokumenty mieszane. |
| U-Q10 | zamknięte | Obowiązuje najnowszy kod repozytorium organizatora. |
| nowe | zamknięte (zespół) | PESEL, rachunki i numer transakcji: tekst albo `null`, zgodnie z referencjami. |

Nadal otwarte: U-Q04 (kanał i budżet klucza), U-Q09 (konta jury), lokalny model instalowany przez pip (ani potwierdzony, ani wykluczony).

## Uzupełnienie 0.6.0 — pytania do mentora przed OpenAPI

Pytania poniżej są otwarte; nie stanowią potwierdzeń organizatora.

| ID | Pytanie | Wpływ |
|---|---|---|
| U-Q11 | Czy skany i dokumenty mieszane w ukrytym teście pochodzą z tego samego generatora co przykłady tekstowe? | reprezentatywność rasteryzacji i fizycznych skanów |
| U-Q12 | Jaki dokładnie wynik jest oczekiwany, gdy jeden PDF zawiera wiele odrębnych dokumentów? | segmentacja i kontrakt eksportu |
| U-Q13 | Czy nieczytelne pole ma mieć `null`, także gdy pole jest wymagane i referencyjny schemat nie dopuszcza `null`? | polityka braków i walidacja YAML |
| U-Q14 | Przy błędzie technicznym lub niedostępnym OCR: brak pliku wynikowego czy `{}` pod nazwą wejścia? Jak ewaluator liczy brak pliku? | przełącznik eksportu konkursowego; błąd pozostaje osobnym stanem |
| U-Q15 | Czy model OCR liczy się do „największego modelu”; jak traktować klasyczny OCR i model wizyjno-językowy? | metadane i punktacja rozmiaru modelu |

Do odpowiedzi polityki opisuje [architektura wewnętrzna](../04-architektura/architektura-wewnetrzna.md#10-decyzje-otwarte-przed-openapi) jako rekomendacje do decyzji użytkownika.
