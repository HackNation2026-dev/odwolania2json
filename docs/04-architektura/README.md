---
wersja: 0.1.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Architektura UZP — propozycja

Stan: propozycja, nie opis gotowej aplikacji.

```text
CLI (Python) -> odczyt PDF / OCR -> klasyfikacja
             -> ekstrakcja według konfiguracji -> walidacja -> output
GUI (TypeScript, opcjonalne) -> ten sam silnik -> widok PDF | JSON
LLM: otwarty model przez zatwierdzone API w UE
```

| Warstwa | Propozycja | Uzasadnienie |
|---|---|---|
| Silnik i CLI | Python 3.13+ | wymóg README |
| Kontrakty | ścisłe typy i reguły normalizacji | zgodność wyniku |
| GUI | TypeScript | podgląd źródła i danych |
| Rust | istniejący moduł pomocniczy, po potwierdzeniu zgodności | nie zastępuje wymaganego rdzenia Python |
| Dostarczenie | Docker; requirements.txt pozostaje wymagany | powtarzalność |

Model, endpoint i klucz mają być konfigurowalne. Dokumentuj rozmiar modelu, licencję i miejsce przetwarzania. Preferencja małego modelu nie zastępuje pomiaru jakości.

Klucz dla jury: osobny plik lokalny lub zmienna środowiska, poza Git. Awaria API ma dawać błąd techniczny, nie zmyślone dane. Limity i ponowienia muszą być ograniczone.

Zobacz [ADR-001](../07-decyzje/ADR-001-stos.md).
