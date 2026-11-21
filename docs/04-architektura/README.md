---
wersja: 0.6.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Architektura UZP — propozycja

## Uzupełnienie 0.6.0 — obowiązujące ustalenia

Pierwszeństwo mają [ADR-002](../07-decyzje/ADR-002-decyzje-po-recenzji.md) i [architektura wewnętrzna ELT](architektura-wewnetrzna.md). Jeden pakiet Python 3.13 instalowany przez pip; bez Rusta i Dockera u jury (Docker tylko deweloperski). GUI jest obowiązkowe z decyzji zespołu, React + TypeScript jako statyczne zasoby pakietu pip, bez serwera Node. CLI i GUI używają wspólnego silnika. To projekt, nie gotowa implementacja.

Poniższy opis zachowano jako historię propozycji; sprzeczne zapisy o opcjonalnym GUI, Rust i dostarczaniu przez Docker nie obowiązują.


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

Zobacz [pełną aplikację i wybór interfejsu](pelna-aplikacja.md).

## Doprecyzowanie wykonania

Według Discorda 12:47 jury nie instaluje modelu na laptopie. Aplikacja/CLI działa lokalnie, a LLM przez publicznie dostępny endpoint. Model może być na własnym serwerze albo przez darmowe lub płatne API, z zachowaniem wymagań licencji i regionu. [Źródło](../01-zadanie/zrodla/UZP-Discord-doprecyzowania-2026-11-21.md).

## Proponowany stos

[Proponowany stos](proponowany-stos.md) — status: PROPONOWANY, nie decyzja zespołu. Wersja 0.4.0.

## Przepływy użytkownika

[Przepływy użytkownika](gui/user-flow.md) (wersja 0.7.0, projekt): nawigacja, ścieżki wyjątkowe, eksport według wariantu A i luki. Ekrany i grafy: [pliki FigCraft](gui/figcraft/).
