# Historia zmian

## Nieopublikowane — 0.8.0

- **`process` wykonuje prawdziwą ekstrakcję dokumentów tekstowych** (Z01, M1): czytnik PDF na pdfium z diagnozą strony (`pdf/reader.py`), prompt p2 bajtowo zgodny z E10 (`extract/prompt.py`), schemat odpowiedzi LLM (`extract/answer.py`), pipeline z normalizatorami i uzgadnianiem pary powodu (`extract/pipeline.py`), silnik `Engine` z opcjonalnym dostawcą OCR (`PageOcr`). Na zapisanych odpowiedziach E10 pipeline produktu daje F1 przybliżony 0,938 [0,910; 0,960]; pomiar z prawdziwym LLM nie został wykonany (MiniMax: HTTP 429), stan w [E-produkt](experiments/2026-11-21-wybor-modulow/produkt/E-produkt.md). Skany czekają na podpięcie OCR.
- Polityka eksportu ([ADR-006](docs/07-decyzje/ADR-006-polityka-eksportu.md), Z02): plik wyniku dla każdego wejścia (także `.PDF`), błąd techniczny to `{}` + wpis w `report.jsonl` + kod wyjścia 1, poprzedni wynik nie jest usuwany, przełącznik `ERROR_EXPORT`; adnotacje w architekturze §4.5 i §10.
- Konfiguracja i self-check LLM (Z04): `LLM_API_KEY_FILE`, `LLM_PROTOCOL`, `LLM_ALLOWED_HOSTS`, limity; próba połączenia przed wsadem (401/403/429 → kod 2 bez przetwarzania); `process` bez argumentów używa `input`/`output`.
- Łańcuch dostawców LLM z zapasowym ([ADR-007](docs/07-decyzje/ADR-007-zapasowy-dostawca-llm.md)): `LLM_FALLBACK_*`, wspólny budżet wywołań i tokenów, ślad dostawcy w raporcie, ostrzeżenie `llm_primary_unauthorized`; zgodność dostawcy zapasowego z wymogiem UE/EOG jest nieznana.
- `scripts/eval_process.py`: pomiar `process` na sprawach rozwojowych (wznawianie, budżet wywołań, F1 per klasa i pole z bootstrapem po sprawach).
- Reguły czynności i pól słabych (Z05) w `domain/czynnosc.py` (powód, opis ze słownika, dzień, numer BZP z dowodem w tekście, imię pełnomocnika z dowodem, `refine_appeal`); replay 25 spraw: ΔF1 +0,018 [+0,013; +0,024]; mutacje 67/67.
- Normalizatory (Z07): NIP/REGON/KRS z grupami cyfr, kwoty z separatorem tysięcy (niejednoznaczny zapis daje `None`), daty (rok dwucyfrowy, miesiąc rzymski, `RRRR/MM/DD`, dzień słowny), TED ze spacjami, `rank_by_checksum`; mutacje `normalize.py` 291/291 zabitych.
- Dopisano do ADR-002 podział etapów (pip na etapie 1, GUI na prezentacji), punktację GUI i otwarte decyzje: biblioteka komponentów, podgląd PDF, model pól wg kontraktu.
- Dodano [przepływ urzędnika](docs/04-architektura/gui/user-flow-urzednik.md): pełny przebieg operatora, widoczne etapy przetwarzania, naprawa błędów, korekty i wersjonowanie po MVP, eksport wariantu A oraz osobne dowody.
- Udokumentowano obowiązkowy klucz MiniMax, brak logowania w zakresie i wyłącznie syntetyczne demo; dodano tablicę zgodności, mapę ramek/trasa/kod i pytania otwarte. Dokument rozróżnia plan, makiety i demonstracyjną implementację; VERSION pozostaje bez zmian.
- Dodano aplikację GUI `apps/web` (Next 16, React 19.3, TypeScript, Tailwind 4, TanStack Query) działającą na mocku zgodnym z kontraktem: pulpit, klucz i kontrola, dodawanie, lista i galeria, przegląd dokumentu z prawdziwym podglądem PDF i obrysem dowodu, eksport wariantu A, klasy (`/klasy/[id]`), partie i eksport częściowy, ustawienia, dziennik, użytkownicy, dostępność, gotowość.
- Dodano system design (23 atomy, 28 molekuł, 12 organizmów, 4 szablony, Storybook 10, test axe po historiach w obu motywach) i 36 makiet uzupełniających FigCraft (71 PNG w `apps/web/design`).
- Dodano plan zadań GUI dla agentów: [zadania-gui.md](docs/00-organizacja/zadania-gui.md) (G01–G13). GUI działa wyłącznie na danych syntetycznych; silnik w `main` pozostaje atrapą.
- `zadania-dla-agentow.md` i `backlog.md` wskazują plan zadań GUI; Z14 (GUI minimum) oznaczono jako wyprzedzone przez `apps/web`.

## 0.7.0 — 2026-11-21

- Dodano przepływy użytkownika ([user-flow.md](docs/04-architektura/gui/user-flow.md)) oraz pliki FigCraft z ekranami (38 ramek) i ośmioma grafami przepływów.
- Nowe ekrany: logowanie na później, brak klucza API i kontrola połączenia, pulpit (jasny i ciemny), panel dodawania i przeglądania dokumentów, galeria kafelków z filtrami, sortowaniem i pustym wynikiem.
- ADR-002, uzupełnienie 0.7.0: wariant A eksportu (ścisła walidacja, bez zastępczego `{}`) zastępuje domyślne `empty_json` z 0.6.1; zatwierdzona paleta UI; ciemny motyw jako propozycja. Architektura §10 do synchronizacji.
- Otwarte: pole klucza w GUI (sprzeczne z projekt-ui §3.1.1), próg galerii, nazwa produktu. Projekt UI (projekt-ui.md) bez zmian w tym wpisie. To dokumentacja projektowa, nie potwierdzenie implementacji.

## 0.6.0 — 2026-11-21

- Dodano architekturę wewnętrzną ELT: kontrakty odczytu/OCR, diagnozy, routera, kandydatów, dowodów, braków i stanów; staging, wersje, cache i ścieżkę pionową E/L/T1/T3/T5. Rozszerzenia po pomiarze F1.
- Zachowano własny model OCR; opisano wymienny shim i dostawcę „brak”. Otwarte polityki eksportu, null, wielu dokumentów i wykonania oznaczono jako propozycje do decyzji użytkownika.
- Uzupełniono historyczne opisy architektury i tabelę wymagań: pip, bez Rusta i Dockera u jury, GUI obowiązkowe. Next.js wyłącznie jako statyczny eksport pakietu pip.
- Dodano 14 kodów wykonawczych (katalog 59 kodów), zawężono kody etykiet do ról podmiotów, poprawiono heurystyki i przeliczono 180 kart oraz dokumentację liczebności.
- Po przeliczeniu: `brak_etykiety_roli` 18/180 (0/15/3 O/P/R), `etykieta_po_danych` 62/180 (0/55/7), `etykieta_synonim` 94/180 (60/34/0), spójne grupy 452/622; lokalizacja referencji nadal 1784/1784. Weryfikacja: 74 testy pytest, `verify_docs.py` OK (440 materiałów, 48 dokumentów).
- Dodano pięć pytań do mentora. Materiały organizatora i katalog projektu GUI bez zmian w tym zleceniu.

## 0.6.1 — 2026-11-21

- Etap 2: framework pre-commit zastąpił .githooks/ dla obu hooków; commit wymaga testów, pokrycia 90% i mutacji staged (--changed). Pełne mutacje AST wymagają 100% zabitych; dodano lokalny audit i rozszerzony zestaw reguł Ruff. Zakaz --no-verify opisano w AGENTS.md i ADR-003.
- CI lokalne w poziomach z budżetem czasu: pre-commit `ci.py --profile commit` (~10 s: zmienione pliki, mutacje zmienionych linii), pre-push `--profile push` (~2 min: pełne testy, mutacje od merge-base z `main`), pełne mutacje ręcznie `--stage mutation`. Mutacje: równolegle, na kopii źródeł, tylko testy modułu, cache wyniku zielonego pod skrótem kodu i testów, jawny raport OK/FAIL/SKIP; błąd testów bazowych nie jest już maskowany.
- ADR-004: SQLAlchemy 2.x + SQLite za DataRepository; usunięto pg8000, konfigurację i SQL specyficzny dla PostgreSQL. Migracje i testy działają bez serwera bazy; test importów oraz Ruff pilnują granicy sterownika. Historyczne plany PostgreSQL są odłożone.

- Dodano lokalne CI/CD: runner etapów, hooki Git, kontrole mutacji, budowanie pakietów pip z SHA-256 i opcjonalnym lokalnym tagiem; konfigurację i konsekwencje opisuje ADR-003. Bez push i publikacji.

- Trwałość zamknięta: SQLite w wersji demo, PostgreSQL przy skalowanym wdrożeniu (ADR-002, architektura §10).

- MiniMax hostowany w Europie potwierdzony przez użytkownika; punkt 8 zamknięty (ADR-002, architektura §10).

- Uzupełnienia po zleceniu C: domyślny `error_export=empty_json` (potwierdzona rekomendacja użytkownika), decyzje ADR-002 pkt 8 (MiniMax, ryzyko zgodności) i pkt 10 (stos GUI) w §10 architektury; nazwa projektu Arkadiana i decyzje o repozytorium w ADR-002.

- Naniesiono decyzje ADR-002 przed OpenAPI w całej architekturze wewnętrznej: jeden PDF = jeden dokument bez limitu stron w kontrakcie, pięć wyników, zamknięte polityki braków, błędów i `{}` dla obcego.
- Dodano interfejs repozytorium danych i wariant jury na dysku (opcjonalnie SQLite); PostgreSQL dla serwera pozostaje do potwierdzenia przez użytkownika.
- Wymagane bbox dowodów powiązano ze słowami PDF/OCR; opisano kotwiczenie cytatów AI i pole do sprawdzenia przy braku kotwicy.
- Ujednolicono angielskie nazwy kontraktów, artefaktów i stanów; zaproponowano mapowanie polskich kodów katalogu bez zmiany katalogu i ocenianego JSON.
- Opisano konfigurację, pobranie klucza, zgodę na zapis, CLI `selfcheck` i stan API; zaktualizowano diagram i pozostałe decyzje. Projekt GUI bez zmian w tym zleceniu.

- Ewaluator F1 v2 (ADR-005): błędna obecna wartość to wyłącznie FP (wariant FP+FN konfigurowalny do porównania); próg podobieństwa 0,8 dla pięciu pól tekstowych z wymiennym algorytmem (`ratio` domyślnie, `token_sort_ratio`, `partial_ratio`) i raportem rozrzutu F1; listy parowane element do elementu po najlepszym przypisaniu, pola oceniane osobno.
- Dodano bootstrap po sprawach (przedział F1) i porównanie sparowane ΔF1 z jawnym ziarnem (`bootstrap.py`) oraz testy: referencja kontra referencja daje F1 = 1,0 na 180 plikach.

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

- Dodano skill projektowy `.claude/skills/generate-api` (generowanie API z kontraktu OpenAPI zgodnie z architekturą 0.6.1 i ADR-002).

- Dodano backlog (`docs/00-organizacja/backlog.md`) z kolejką prac, znanymi długami i definicją ukończenia oraz `CLAUDE.md` odsyłający do `AGENTS.md`.

- Naprawa ewaluatora: wartość obecna i zgodna z referencją liczy się jako TP (wcześniej TN, więc F1 pól wynosiło 0). Wykryte w recenzji planu eksperymentów.

- Eksperymenty wyboru modułów (E00-E20, uprząż HTTP, raport, ocena architektury Fable) oraz lista zadań dla agentów ze szczegółowymi instrukcjami (`docs/00-organizacja/zadania-dla-agentow.md`). Wniosek: produkt dziś zapisuje `{}` (F1 pól = 0); wyniki pochodzą z uprzęży w `experiments/`.

## Niewydane

- Z03, dostarczenie: `requirements.txt` w korzeniu zawiera tylko zależności uruchomieniowe z OCR (rapidocr + onnxruntime CPU, wagi ONNX w kole `rapidocr`) i pakiety lokalne bez `-e`; narzędzia deweloperskie przeniesiono do `requirements-dev.txt`, usunięto `apps/backend/requirements-ocr.txt`. `requires-python >= 3.13`.
- Dodano `run.sh`, `start.bat`, katalogi `input/` i `output/` (`.gitkeep`, zawartość ignorowana), `scripts/verify_install.py` z lokalną atrapą LLM i testy dostarczenia; README opisuje instalację, klucz API, kody wyjścia i stan implementacji (`process` nadal na atrapie do czasu Z01).

- Klient LLM (ponowienia, kody błędów, walidacja `base_url`) i serializer z szablonu klasy w `apps/backend`; szkic czytnika PDF i adaptera OCR w `experiments/.../produkt-szkic/`. `process` nadal na atrapie (Z01 do dokończenia).

- Materiały TODO (`docs/08-todo/`): plan naprawczy, kontekst dla agentów i rzetelny opis stanu na koniec etapu 2026-11-22 (co sprawdzone osobiście, co z raportów, co w toku, czego nie mamy).
