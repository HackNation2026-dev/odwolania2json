# Historia zmian

## Nieopublikowane — 0.8.0

- Dopisano do ADR-002 podział etapów (pip na etapie 1, GUI na prezentacji), punktację GUI i otwarte decyzje: biblioteka komponentów, podgląd PDF, model pól wg kontraktu.
- Dodano [przepływ urzędnika](docs/04-architektura/gui/user-flow-urzednik.md): pełny przebieg operatora, widoczne etapy przetwarzania, naprawa błędów, korekty i wersjonowanie po MVP, eksport wariantu A oraz osobne dowody.
- Udokumentowano obowiązkowy klucz MiniMax, brak logowania w zakresie i wyłącznie syntetyczne demo; dodano tablicę zgodności, mapę ramek/trasa/kod i pytania otwarte. Dokument rozróżnia plan, makiety i demonstracyjną implementację; VERSION pozostaje bez zmian.

## 0.6.0 — 2026-11-21

- Dodano architekturę wewnętrzną ELT: kontrakty odczytu/OCR, diagnozy, routera, kandydatów, dowodów, braków i stanów; staging, wersje, cache i ścieżkę pionową E/L/T1/T3/T5. Rozszerzenia po pomiarze F1.
- Zachowano własny model OCR; opisano wymienny shim i dostawcę „brak”. Otwarte polityki eksportu, null, wielu dokumentów i wykonania oznaczono jako propozycje do decyzji użytkownika.
- Uzupełniono historyczne opisy architektury i tabelę wymagań: pip, bez Rusta i Dockera u jury, GUI obowiązkowe. Next.js wyłącznie jako statyczny eksport pakietu pip.
- Dodano 14 kodów wykonawczych (katalog 59 kodów), zawężono kody etykiet do ról podmiotów, poprawiono heurystyki i przeliczono 180 kart oraz dokumentację liczebności.
- Po przeliczeniu: `brak_etykiety_roli` 18/180 (0/15/3 O/P/R), `etykieta_po_danych` 62/180 (0/55/7), `etykieta_synonim` 94/180 (60/34/0), spójne grupy 452/622; lokalizacja referencji nadal 1784/1784. Weryfikacja: 74 testy pytest, `verify_docs.py` OK (440 materiałów, 48 dokumentów).
- Dodano pięć pytań do mentora. Materiały organizatora i katalog projektu GUI bez zmian w tym zleceniu.

## 0.6.1 — 2026-11-21

- Trwałość zamknięta: SQLite w wersji demo, PostgreSQL przy skalowanym wdrożeniu (ADR-002, architektura §10).

- MiniMax hostowany w Europie potwierdzony przez użytkownika; punkt 8 zamknięty (ADR-002, architektura §10).

- Uzupełnienia po zleceniu C: domyślny `error_export=empty_json` (potwierdzona rekomendacja użytkownika), decyzje ADR-002 pkt 8 (MiniMax, ryzyko zgodności) i pkt 10 (stos GUI) w §10 architektury; nazwa projektu Arkadiana i decyzje o repozytorium w ADR-002.

- Naniesiono decyzje ADR-002 przed OpenAPI w całej architekturze wewnętrznej: jeden PDF = jeden dokument bez limitu stron w kontrakcie, pięć wyników, zamknięte polityki braków, błędów i `{}` dla obcego.
- Dodano interfejs repozytorium danych i wariant jury na dysku (opcjonalnie SQLite); PostgreSQL dla serwera pozostaje do potwierdzenia przez użytkownika.
- Wymagane bbox dowodów powiązano ze słowami PDF/OCR; opisano kotwiczenie cytatów AI i pole do sprawdzenia przy braku kotwicy.
- Ujednolicono angielskie nazwy kontraktów, artefaktów i stanów; zaproponowano mapowanie polskich kodów katalogu bez zmiany katalogu i ocenianego JSON.
- Opisano konfigurację, pobranie klucza, zgodę na zapis, CLI `selfcheck` i stan API; zaktualizowano diagram i pozostałe decyzje. Projekt GUI bez zmian w tym zleceniu.

## 0.5.0 — 2026-11-21

- Dodano ADR-002 z decyzjami użytkownika po recenzji architektury przez Codex: odrzucone `pypdfium2` i `rapidocr` (będzie własne rozwiązanie), klasyfikacja i LLM otwarte, regex tylko z eksperymentami i testami mutacyjnymi, zgodność API (MiniMax: Claude; DeepSeek, GLM, OpenAI: OpenAI), zakaz zwracania starego wyniku z cache przy awarii API, GUI React/TS (prawdopodobnie Next.js).
- Dodano eksperyment `experiments/2026-11-21-yaml-klasy/` i jego wynik w `docs/05-weryfikacja/`: YAML opisuje wszystkie trzy klasy (60/60 spraw, roundtrip identyczny, 4528/4528 mutantów zabitych), nowa klasa bez zmian w kodzie; granica: semantyka ekstrakcji i scalanie reguł z LLM.
- Odnotowano rozbieżność typu `pesel` (wzorzec: liczba, referencje: tekst) i `numer_transakcji`.
- Dodano odpowiedzi mentora UZP przekazane przez użytkownika (`docs/01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md`): pełna macierz TP/TN/FP/FN, najnowsza rewizja kontraktu, skany i dokumenty mieszane w teście, tylko pip, hosting w Europie, liczy się największy model, `{}` dla obcego dokumentu, numery jako tekst. GUI obowiązkowe z decyzji zespołu. Zaktualizowano pytania otwarte, wymagania, zasady F1 i ADR-002.
- Dodano eksperyment przypadków brzegowych (`experiments/2026-11-21-przypadki-brzegowe/`, wynik w `docs/05-weryfikacja/`): inwentarz 206 PDF-ów (pozytywne wyłącznie tekstowe), 12 syntetycznych skanów i dokumentów mieszanych, porównanie Codex, Claude i MiniMax-M3.1-Flash na 41 dokumentach, format plików ze schematami JSON i przeglądarka egui do adnotacji.
- Dodano brief projektu interfejsu (`docs/04-architektura/gui/brief-projektu-ui.md`).
- Zmiany addytywne; materiały organizatora bez zmian.

## 0.4.0 — 2026-11-21

- Odnotowano zmianę widoczności repo na publiczną przez użytkownika; skrypt publikacji prywatnej nie jest używany dla tego wydania.
- Dodano `docs/04-architektura/proponowany-stos.md` ze statusem PROPONOWANY (nie decyzja): Python 3.13, pip + CLI, hybryda reguł i LLM po API w UE, GUI PDF|JSON wcześnie.
- Addytywnie dodano późniejsze rewizje organizatora: `main` `7590db8` (poprawki `czynnosc_opis` w 5 sprawach, słownik), gałąź `dane` `26a3363` z 39 plikami `ground_truth.yaml` i gałąź `mateusz-readme-changes`. Kopia bazowa `f60ca6f` bez zmian; rejestr `uzp-aktualizacje.json`, manifest +50 plików.
- `verify_docs.py` dodatkowo sprawdza blob SHA-1 i komplet aktualizacji.
- Uzupełniono kompletność (brak prezentacji PDF i skryptu F1 potwierdzony w całej historii repo organizatora), rozbieżności, punktację GUI z cytatami i uwagę do rekomendacji Fable.
- Przywrócono jako sekcje historyczne treść nadpisaną w 0.3.0 (zlecenie i status konsultacji, status publikacji).
- Zmiany wyłącznie addytywne.

## 0.3.0 — 2026-11-21

- Opublikowano prywatne repo `HackNation2026-dev/odwolania2json` (organizację utworzył użytkownik ręcznie); potwierdzono prywatność, SHA i drzewo.
- Dodano wynik niezależnej konsultacji Fable (`claude-fable-5-2`, bezpośrednie CLI): surowa odpowiedź, zlecenie i metadane.
- Rekomendacja Fable dla UZP: czysty Python 3.13 (pip, CLI), hybryda reguł i małego LLM po API w UE, `pypdfium2` + `rapidocr`, GUI na końcu, bez Rusta. To nie jest decyzja zespołu; ADR-001 pozostaje propozycją.
- Materiały organizatora bez zmian.

## 0.2.1 — 2026-11-21

- Potwierdzono działające CLI Claude i alias modelu fable w pomocy.
- Konsultację i publikację odłożono na prośbę użytkownika do nowej sesji.
- Bezpośrednią próbę konsultacji przerwano bez uzyskania opinii.

## 0.2.0 — 2026-11-21

- Dodano źródło Discord z godzinami i autorami przekazanymi przez użytkownika.
- Uwzględniono 60 spraw, usunięcie ground_truth.yaml i syntetyczny zbiór testowy.
- Doprecyzowano darmowe/płatne/własne API, publiczny endpoint i brak instalacji modelu u jury.
- Dodano zasady F1: 80% dla wskazanych tekstów i listy dopasowywane po treści.
- Korekta 13:27: obcy dokument daje pusty JSON pod oryginalną nazwą.
- Zachowano nierozstrzygnięte szczegóły ewaluacji i oryginalne FAQ v1.0.
- Dodano wykaz kompletności i zlecenie Fable ze statusem niewykonane.
- Publikacja dopuszcza bezpieczne aktualizacje fast-forward.

## 0.1.1 — 2026-11-21

- Zmieniono organizację docelową na `HackNation2026-dev` zgodnie z poleceniem użytkownika.
- Dodano porównanie pełnej aplikacji: CLI/API, Python/Rust, React/TypeScript i egui.
- Konsultacja Fable nie została wykonana; propozycja stosu jest oceną autora.
- Publikacja nadal wymaga działającego dostępu do GitHub. Materiały organizatorów pozostają bez zmian.

## 0.1.0 — 2026-11-21

- Utworzono wersjonowaną dokumentację w podziale na osiem obszarów.
- Dodano oryginalne opisy, regulaminy i dostępne materiały organizatora.
- Rozdzielono wymagania, propozycję stosu, testy, prezentację i pytania.
- Dodano rejestr źródeł, sumy kontrolne i kontrolę odnośników.
- Nie zaimplementowano jeszcze aplikacji konkursowej.

## 0.7.0 — 2026-11-21

- Dodano przepływy użytkownika ([user-flow.md](docs/04-architektura/gui/user-flow.md)) oraz pliki FigCraft z ekranami (38 ramek) i ośmioma grafami przepływów.
- Nowe ekrany: logowanie na później, brak klucza API i kontrola połączenia, pulpit (jasny i ciemny), panel dodawania i przeglądania dokumentów, galeria kafelków z filtrami, sortowaniem i pustym wynikiem.
- ADR-002, uzupełnienie 0.7.0: wariant A eksportu (ścisła walidacja, bez zastępczego `{}`) zastępuje domyślne `empty_json` z 0.6.1; zatwierdzona paleta UI; ciemny motyw jako propozycja. Architektura §10 do synchronizacji.
- Otwarte: pole klucza w GUI (sprzeczne z projekt-ui §3.1.1), próg galerii, nazwa produktu. Projekt UI (projekt-ui.md) bez zmian w tym wpisie. To dokumentacja projektowa, nie potwierdzenie implementacji.
