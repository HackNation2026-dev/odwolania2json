---
wersja: 0.2.0
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
