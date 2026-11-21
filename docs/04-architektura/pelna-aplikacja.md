---
wersja: 0.6.0
aktualizacja: 2026-11-21
status: propozycja autora; wynik konsultacji Fable w docs/07-decyzje/konsultacja-fable.md
---

# Pełna aplikacja i wybór interfejsu

## Uzupełnienie 0.6.0 — obowiązujące ustalenia

Pierwszeństwo mają [ADR-002](../07-decyzje/ADR-002-decyzje-po-recenzji.md) i [architektura wewnętrzna ELT](architektura-wewnetrzna.md). Jeden pakiet Python 3.13 instalowany przez pip; bez Rusta i Dockera u jury (Docker tylko deweloperski). GUI jest obowiązkowe z decyzji zespołu, React + TypeScript jako statyczne zasoby pakietu pip, bez serwera Node. CLI i GUI używają wspólnego silnika. To projekt, nie gotowa implementacja.

Poniższy opis zachowano jako historię propozycji; sprzeczne zapisy o opcjonalnym GUI, Rust i dostarczaniu przez Docker nie obowiązują.


Minimum konkursowe UZP to backend przetwarzający PDF i obowiązkowe CLI w Pythonie 3.13+. GUI nie jest wymagane, lecz FAQ zapowiada dodatkową ocenę; preferuje PDF i dane obok siebie. Pełny produkt rekomenduję jako aplikację z backendem oraz cienkim interfejsem przeglądarkowym. CLI i GUI używają tej samej logiki. REST API dla GUI jest naszą propozycją, nie osobnym wymogiem UZP.

Python odpowiada za CLI, OCR, klasyfikację, ekstrakcję i konfigurację klas. Rust może wspomagać deterministyczną normalizację albo walidację, jeśli istniejący moduł daje mierzalną korzyść. Wymóg aplikacji w Pythonie nie uzasadnia zastąpienia silnika Rustem z cienką nakładką bez potwierdzenia mentora. Model otwarty musi umożliwiać lokalną instalację; dostawca i serwer API w UE. Test na komputerze bez GPU.

## React/TypeScript czy Rust/egui

Proponowany frontend: React + TypeScript. Widok dokumentu i JSON oraz formularz generowany z konfiguracji są podstawowymi scenariuszami. Interfejs korzysta z lokalnych, dołączonych zasobów; w COI nie zależy od CDN ani usług zewnętrznych. TypeScript opisuje stan i kontrakty interfejsu; walidacja backendu pozostaje obowiązkowa.

egui działa natywnie i w przeglądarce przez WebAssembly; nie jest rozwiązaniem wyłącznie desktopowym. Może być właściwe dla wewnętrznego narzędzia zespołu lub gotowej bazy aplikacji Rust. Dla tych zadań preferuję React ze względu na formularze HTML, podgląd dokumentów, kontrolę dostępności i łatwe uruchomienie przez jury. To wybór projektowy, nie wynik benchmarku. egui nie daje samo w sobie punktów konkursowych ani gwarancji spełnienia dostępności.

## Docker i podział monorepo

Docelowo: `apps/web/` dla React/TypeScript, `apps/backend/` dla API i CLI, `packages/contracts/` dla kontraktów oraz `infra/` dla konfiguracji Docker. Te katalogi są planem; implementacji jeszcze nie ma. Nie dodajemy teraz pustych serwisów ani pozornego działającego Compose. Modele i klucze pozostają poza Git. Osobna baza i kolejka dopiero po wykazaniu potrzeby.

## Decyzja i konsekwencje

Status: proponowana, rozwinięcie ADR-001. Wariant domyślny to Python + React/TypeScript + Docker. Rust dodajemy tam, gdzie istnieje sprawdzony komponent lub pomiar uzasadnia jego koszt. Dodatkowy język oznacza dodatkowe budowanie, kontrakty i testy uruchomienia. Nie przypisujemy tej rekomendacji Fable. Rekomendacja Fable (wyłącznie Python, bez Rusta) jest osobno w [konsultacji Fable](../07-decyzje/konsultacja-fable.md).

## Pytania do niezależnej konsultacji Fable

1. Czy minimum konkursowe wymaga pełnego frontendu, czy tylko backendu/CLI/API?
2. Jakie funkcje GUI wnoszą punkty, a jakie zwiększają tylko zakres?
3. Gdzie Python jest wymagany lub preferowany, a gdzie Rust ma mierzalną przewagę?
4. Czy React/TypeScript czy egui lepiej spełnia podgląd PDF/JSON, formularze i dostępność?
5. Jak zapewnić działanie na sprzęcie jury oraz wymagane miejsce przetwarzania?
6. Jakie moduły i zależności można usunąć bez utraty wymagań?

Konsultacja nie została uruchomiona: bieżący wątek poboczny nie pozwala na delegowanie do drugiego agenta. Pytania są materiałem do późniejszej konsultacji, nie otrzymaną opinią.

## Źródła

- Wymagania: [dokumentacja zadania](../03-wymagania/README.md) i oryginały organizatora.
- React: https://react.dev/learn — komponenty i obsługa interfejsu.
- egui: https://github.com/emilk/egui — web/native, eframe i dostępność; odczyt 2026-11-21.

## Warunki z komunikatów UZP

Silnik i CLI: Python 3.13+. Dopuszczalność pomocniczego Rusta nadal wymaga potwierdzenia. Jury nie instaluje modelu lokalnie; endpoint musi być publiczny. Otwarte modele przez płatne API są dozwolone, ale klucz trzeba przekazać do oceny. Zasady regionu pozostają z FAQ/README.

## Historia statusu

Status nagłówka do wersji 0.2.1: „propozycja autora; konsultacja Fable niewykonana”. Zmieniony w kolejnej wersji po wykonaniu konsultacji. Proponowany stos po konsultacji: [proponowany-stos.md](proponowany-stos.md).
