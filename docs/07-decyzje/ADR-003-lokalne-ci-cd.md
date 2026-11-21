---
wersja: 0.6.1
aktualizacja: 2026-11-21
status: przyjęta decyzja użytkownika
---

# ADR-003: lokalne CI/CD

## Kontekst i decyzja

Na polecenie użytkownika kontrole oraz budowanie wydań wykonujemy na maszynie dewelopera. Zastępuje to wcześniejszą zasadę bramki w chmurze w AGENTS.md. [ADR-002](ADR-002-decyzje-po-recenzji.md) nadal wymaga pip u jury oraz mutacji normalizatorów, regex i walidatora. Nie zmieniamy materiałów organizatora ani historycznego workflow docs.

Standardowa biblioteka Pythona 3.13 wystarcza dla runnera `scripts/ci.py` i `scripts/release.py`. Narzędzia wywołujemy przez ten sam interpreter. Pre-commit wykonuje szybkie kontrole, pre-push pełne all z mutacjami: koszt czasu jest świadomą konsekwencją obowiązkowej bramki przed push. Przed merge deweloper również musi uzyskać zielone all.

## Narzędzia i licencje

| Narzędzie | Wersja | Licencja | Podstawa zgodności Python 3.13 |
|---|---|---|---|
| [ruff](https://pypi.org/project/ruff/0.14.6/) | 0.14.6 | MIT | klasyfikator Python 3.13, Requires-Python >=3.7 |
| [mypy](https://pypi.org/project/mypy/1.18.2/) | 1.18.2 | MIT | klasyfikator Python 3.13, Requires-Python >=3.9 |
| [mutmut](https://pypi.org/project/mutmut/3.3.1/) | 3.3.1 | BSD | [historia projektu](https://github.com/boxed/mutmut/blob/main/HISTORY.rst) potwierdza wsparcie 3.13 od 3.3.0 |
| [build](https://pypi.org/project/build/1.3.0/) | 1.3.0 | MIT | Requires-Python >=3.9, uniwersalny wheel |

Metadane i licencje sprawdzono w źródłach projektów/PyPI. Nie potwierdzają kompletnego rozwiązania zależności w tym środowisku. Próby pip index versions oraz pip install --dry-run nie uzyskały dystrybucji; pobranie interpretera przez uv zawiodło na DNS. Przypięte wersje wymagają jeszcze weryfikacji instalacji na Pythonie 3.13 z dostępem do PyPI. Nie dodajemy ich do zależności produkcyjnych.

Mutmut wymaga fork (Windows przez WSL). Wersja 3 mutuje funkcje, dlatego runner dodatkowo mutuje deklaracje stałych regex i typów pól modeli pydantic w izolowanej kopii. Generowane modele w repo pozostają nienaruszone. Zakres znajduje się w pyproject.toml; po dodaniu osobnego walidatora lub wzorców należy go rozszerzyć. Próg dla całego zakresu: **100% zabitych**, zero przeżytych, timeoutów, pominiętych i niesprawdzonych. Pusty zbiór nie jest sukcesem. Dla metadanych mutmut za zabicie uznajemy wyłącznie kod testów 1, a nie błąd wewnętrzny pytest.

## Konsekwencje

- Brak niezależnej bramki chmurowej: hooki są lokalne, wymagają instalacji i można je ominąć. Autor push/merge odpowiada za wynik pełnego przebiegu.
- Maszyna dewelopera musi mieć zgodne narzędzia i zależności aplikacji. Istniejące błędy typów, formatowania i dokumentacji mogą blokować kontrolę; skrypty nie naprawiają ich automatycznie.
- Artefakty CI są ograniczone do `.ci/`, a CD dodatkowo zapisuje pakiety w `dist/`. Mutacje i build pracują na kopiach. Pełna izolacja dowolnego kodu testów wymagałaby osobnego sandboxa; runner ustawia lokalne cache, katalog tymczasowy i wyłącza bytecode.
- Wydanie wymaga czystego Git, zgodności VERSION/CHANGELOG/wersji artefaktów i pełnego CI. Domyślny dry-run buduje pakiety i sumy, lecz nie tworzy tagu. Flaga --tag tworzy wyłącznie tag lokalny. Brak automatycznej publikacji, push i serwera wdrożeniowego.
- Repo ma obecnie dwie definicje pakietów pip, dlatego budujemy obie bez zmiany ich pyproject.toml. Ujednolicenie dostarczenia do jednego pakietu z ADR-002 pozostaje osobnym zadaniem; ten mechanizm nie dowodzi gotowości produktu u jury.

Instrukcja operacyjna: [lokalne CI/CD](../00-organizacja/lokalne-ci-cd.md).
