---
wersja: 0.6.0
aktualizacja: 2026-11-21
status: zlecenie dla Codex — naniesienie decyzji przed OpenAPI
---

# Zlecenie C (Codex): decyzje przed OpenAPI w architekturze

Repo `odwolania2json`. Po polsku. Zmieniasz **wyłącznie** `docs/04-architektura/architektura-wewnetrzna.md` (wersja → 0.6.1) i dopisujesz wpis w `CHANGELOG.md` (pod 0.6.0, sekcja „0.6.1”) oraz `VERSION` → 0.6.1. Nie ruszaj `docs/04-architektura/gui/` (równolegle trwa inne zlecenie). Na końcu `python3 scripts/verify_docs.py` musi przejść.

Przeczytaj ostatnie uzupełnienie `docs/07-decyzje/ADR-002-decyzje-po-recenzji.md` („decyzje przed OpenAPI”) i nanieś je w całym dokumencie architektury (nie tylko w §9–§10), usuwając sprzeczności:

1. **Trwałość:** zaprojektuj interfejs repozytorium danych (zadania, dokumenty, artefakty, wyniki) z implementacją v1 na katalogu roboczym (opcjonalnie SQLite z biblioteki standardowej) i opcjonalną implementacją PostgreSQL dla wersji serwerowej. Oznacz wybór PostgreSQL jako „do potwierdzenia przez użytkownika”; tryb jury bez serwera bazy (tylko pip).
2. Polityka braków i błędów: obecne ustalenia potwierdzone; obcy → `{}` pod nazwą pliku. Zamknij te punkty w §10.
3. **Jeden PDF = jeden dokument**, dowolna liczba stron: usuń wynik „wiele dokumentów” jako osobny wynik eksportu; segmentacja może zostać jako diagnoza (kod/ostrzeżenie), ale nie dzieli wyniku. Bez limitu stron w kontrakcie (limity tylko zasobowe, z kodem `limit_kontekstu`/`limit_czasu`).
4. **Geometria obowiązkowa:** każdy dowód ma bbox na stronie; opisz, skąd pochodzi (słowa warstwy tekstu PDF lub OCR), jak dowód z cytatu AI jest kotwiczony w warstwie odczytu, co gdy nie da się zakotwiczyć (pole „do sprawdzenia” + kod, bez zgadywania bbox). Zaktualizuj kontrakty §4 (bbox wymagany).
5. **Język:** kod, API, nazwy plików, artefaktów i identyfikatory po angielsku — przemianuj w dokumencie nazwy artefaktów katalogu roboczego, pól kontraktów i stanów na angielskie (np. `raw/`, `diagnosis.json`, `candidates.json`, `result.json`, `evidence.json`, `report.json`; stany `queued/running/done`, wyniki `complete/partial/foreign/ambiguous/technical_error`), z tabelą odpowiedników polskich nazw używanych wcześniej. Oceniany JSON zachowuje klucze organizatora. Kody z katalogu przypadków (polskie) — zaproponuj mapowanie na angielskie kody techniczne w API (tabela), bez zmiany katalogu w tym zleceniu.
6. **Konfiguracja i klucz API:** sekcja „Konfiguracja i samosprawdzenie”: źródła konfiguracji (zmienne środowiskowe, plik konfiguracyjny użytkownika poza Git), przy braku klucza w trybie interaktywnym program prosi o klucz, wykonuje self-check (połączenie, autoryzacja, model, region, gotowość OCR) i dopiero wtedy kontynuuje; zapis do pliku tylko za zgodą; w trybie nieinteraktywnym jawny błąd `llm_autoryzacja`/`konfiguracja_niepoprawna`; komenda `selfcheck` w CLI i endpoint stanu w API.
7. Zaktualizuj diagram (§12) i listę decyzji otwartych (zostają: PostgreSQL, dostawca i model LLM, biblioteka UI, pytania do mentora).

Raport: krótko — co zmieniono, nowe nazwy angielskie (tabela skrócona), pozostałe decyzje, wynik `verify_docs.py`.
