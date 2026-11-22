---
wersja: 0.1.0
aktualizacja: 2026-11-22
status: kontekst dla agentów: stan, fakty, środowisko, zasady, pułapki
---

# Kontekst dla agentów

## Zadanie w jednym akapicie

Aplikacja czyta PDF-y spraw odwoławczych (odwołanie do KIO, pełnomocnictwo, potwierdzenie przelewu), wyciąga dane do JSON według wzorców organizatora (`docs/02-materialy/organizator-uzp/oczekiwane-json/`), dla obcego dokumentu zapisuje `{}`. Ocena: F1 na ukrytym zbiorze (tekst, skany, mieszane). Warunki: Python 3.13+, `requirements.txt`, pip bez Dockera, bez GPU (i7, 16 GB), LLM tylko po API z serwerów UE/EOG, open source, klucz dołączony. Źródła: [README organizatora](../02-materialy/organizator-uzp/README.md), [FAQ](../01-zadanie/zrodla/FAQ-Odwolania2JSON-v1.0.md), [Discord](../01-zadanie/zrodla/UZP-Discord-doprecyzowania-2026-11-21.md), [odpowiedzi mentora](../01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md), [zasady F1](../05-weryfikacja/zasady-f1.md).

## Stan kodu (`apps/backend/odwolania2json/`)

| Moduł | Rola |
|---|---|
| `pdf/` | czytnik pypdfium2: słowa z bbox, linie, `/Rotate`, diagnoza strony, limity |
| `ocr/` | adapter rapidocr (słowa z bbox, obrót 90/180/270, limit boku 2000 px, 4 wątki), `OcrProvider` |
| `extract/` | prompt p2, schemat odpowiedzi (pydantic), pipeline, porty `PageOcr` i `JsonLlm` |
| `llm/` | klient Anthropic i OpenAI (ponowienia z `Retry-After`, kody błędów, walidacja `base_url`, klucz w jednym nagłówku), łańcuch dostawców MiniMax → GLM (`LLM_FALLBACK_*`, PR #33) |
| `domain/` | normalizatory (po naprawie luk E19, mutacje 291/291), `czynnosc.py` (reguły czynności, BZP, imię pełnomocnika) |
| `serialize.py` | serializer z szablonu klasy: jawne `null`, kolejność kluczy, bez `prune` |
| `engine.py`, `cli.py` | `process input output`: wsad, atomowy zapis, polityka eksportu ADR-006, raport wsadu, self-check |
| `evaluator.py`, `similarity.py`, `bootstrap.py`, `loader.py`, `dataset.py` | ewaluator F1 (TP/TN/FP/FN, próg 80% dla 5 pól, wersje podobieństwa), bootstrap po sprawach, loader 60 spraw, podział rozwojowy/kontrolny (`data/podzial.json`) |
| `db/` | SQLAlchemy 2 + SQLite za `DataRepository` (ADR-004); **nie na ścieżce CLI** |

Dostarczenie: `requirements.txt` (z OCR, wagi w kole), `run.sh`, `start.bat`, `scripts/verify_install.py`. Wersja i historia: `VERSION`, `CHANGELOG.md`.

## Co mówią dane (zbiór rozwojowy, 25 z 49 spraw; F1 przybliżony, nie oficjalny)

- Tekst: 0,938 [0,910; 0,959] (MiniMax Flash, 5 powtórzeń); po regułach czynności 0,956 [0,929; 0,976] (replay). Skan: B (OCR) 0,902, C (obraz) 0,928, D (tekst+obraz) 0,961 (n=26). Zła niewidoczna warstwa tekstu (S5): sama warstwa 0,625, obraz 0,927.
- Pułapki pomiarowe: jeden generator dokumentów, reguły i prompt stroiłem na tych samych sprawach (górna granica), skany syntetyczne, jedno powtórzenie, wyniki z uprzęży, nie z produktu.
- Polityka eksportu (E17): nie zerować pola bez kotwicy (−0,021), eksportować `partial` (brak eksportu −0,208 tekst); bbox nie decyduje o treści JSON.
- Pełne wyniki: [raport](../../experiments/2026-11-21-wybor-modulow/RAPORT.md), [ocena Fable](../../experiments/2026-11-21-wybor-modulow/recenzje/fable-ocena-architektury.md).

## Dostawcy LLM (fakty, bez sekretów)

| Dostawca | Stan | Szczegóły |
|---|---|---|
| MiniMax | wyczerpany limit „Token Plan” (HTTP 429, 22.11), wraca okresowo | protokół Anthropic, `https://api.minimax.io/anthropic/v1/messages`, modele `MiniMax-M3`, `MiniMax-M3.1-Flash-Preview`; klucz z pliku wskazanego w `MINIMAX_KEY_FILE` (domyślnie `~/kluczMiniMaxKacper`, poza Git); zgodność z UE/EOG i licencją nieudowodniona (ADR-002 pkt 8) |
| GLM na OpenCode Go (zapasowy) | działa (HTTP 200, ok. 0,8 s) | protokół OpenAI, `https://opencode.ai/inference/go/openai/v1/chat/completions`, model `glm-5.3-flash`, nagłówek `Authorization: Bearer`, wymagane własny `User-Agent` i stały `x-opencode-session` (UUID na proces), inaczej HTTP 400; klucz w pliku `~/kluczOpenCodeGLM` (poza Git); odpowiedź ma `reasoning_content` obok `content`: parsuj `content`. Endpoint `…/inference/openai/v1` (bez `/go`) jest płatny z kredytów (HTTP 402). Plan Go ma limity (5 godzin: 20% puli, tydzień: 50%) i jest przeznaczony dla agentów kodujących, ruch bywa monitorowany: używaj oszczędnie (współbieżność 2); lokalizacja serwerów i warunki dla naszego zastosowania nieznane |

Klucze nigdy w repozytorium, logach, wynikach ani odpowiedziach HTTP; przed commitem sprawdź grepem.

## Środowisko i narzędzia

- Dwa środowiska: `.venv` (narzędzia deweloperskie i produkt: `pip install -r requirements-dev.txt -r apps/backend/requirements.txt`) i `.venv-exp` (uprząż, OCR). W świeżym worktree ustaw: `export CI_PYTHON=<ścieżka>/.venv/bin/python PATH=<ścieżka>/.venv/bin:$PATH PYTHONPATH=apps/backend:packages/contracts`.
- Hooki: `sh scripts/install_hooks.sh` (framework pre-commit). Commit: `ci.py --profile commit` (cel < 10 s); push: `ci.py --profile push` (cel < 2 min, pełne testy z progiem pokrycia 90%, mutacje modułów zmienionych od `origin/main`). Mutacje: zero przeżytych w zakresie (normalizatory, regex, walidator). `python scripts/ci.py --stage all` przed release. **Zakaz `--no-verify`.**
- Git: gałąź od `origin/main`, atomowe commity, PR (`gh pr create --base main`), merge (`gh pr merge --merge`) po zielonych hookach. Wiele agentów pracuje równolegle: używaj własnego worktree (`git worktree add ../<nazwa> -b <gałąź> origin/main`), nie przełączaj gałęzi w cudzym katalogu, nie cofaj cudzych zmian.
- Dane: oryginały w `docs/02-materialy/` niezmienne; strojenie tylko na zbiorze rozwojowym (`data/podzial.json`); **zbiór kontrolny jeden raz**, wybór zapisany w `WYBOR.md` przed uruchomieniem, licznik w `experiments/2026-11-21-wybor-modulow/llm-e2e/KONTROLNY.md`; nie używaj wariantów syntetycznych ze spraw kontrolnych (m.in. `przyklad_40`). Dużych danych generowanych nie commituj (`odczyt/zestaw/data/`, `vendor/`, cache są w `.gitignore`).
- Jakość liczb: „F1 przybliżony” z przedziałem z bootstrapu po sprawach (`bootstrap.py`), z licznością; nie nazywaj wyniku oficjalnym.

## Pułapki, na które już wpadliśmy

- **`.gitignore` wycinał skrypty zestawu skanów:** w czystym klonie `verify_docs` padał (naprawione, PR #17). Ignorowane jest tylko `odczyt/zestaw/data/`.
- **`verify_docs.py` skanuje cały `*.md` w repo:** katalogi `.venv*`, `vendor`, `site-packages` są pominięte; nowe środowiska poza tymi nazwami zepsują etap docs.
- **Pre-push porównuje z `origin/main`** (nie z lokalnym `main`, który bywa za zdalnym).
- **`pkill -f` / `pgrep -f` z wzorcem w tej samej komendzie zabija własną powłokę;** używaj wzorca z nawiasem (`[v]env-exp`) i innego tekstu w `echo`.
- **Sieć:** IPv6 do API zawodzi (`EHOSTUNREACH`, `ECONNREFUSED`, `ENOTFOUND`); workery padają bez commitów. Pliki zostają w drzewie, ponów zadanie.
- **Cisza do pomiaru czasu nie nadchodzi** (praca w innych worktree, np. `apps/web`); mierz czas CPU i RSS, czas ścienny oznaczaj jako obciążony.
- **`rglob("*.pdf")` pomija `.PDF` na Linuksie;** test w silniku wymagany.
- **S5:** poprawny obraz z błędną niewidoczną warstwą tekstu daje F1 0,000 przy `complete`; warstwy tekstu strony zdominowanej obrazem nie wolno wprowadzać do wyniku.
- **Normalizatory:** suma kontrolna NIP/REGON/IBAN tylko jako sygnał rankingowy (poprawna u 64%/70%/34% wartości referencyjnych).

## Gdzie co leży

| Co | Gdzie |
|---|---|
| Zadania z instrukcjami | `docs/00-organizacja/zadania-dla-agentow.md` |
| Plan i kontekst | `docs/08-todo/` |
| Decyzje | `docs/07-decyzje/` (ADR-002 stos i decyzje użytkownika, ADR-003 lokalne CI/CD, ADR-004 SQLite bez Postgres, ADR-005 interpretacja F1, ADR-006 polityka eksportu, ADR-007 dostawca zapasowy i jego ryzyka) |
| Architektura (kontrakty etapów) | `docs/04-architektura/architektura-wewnetrzna.md` (część §4.5, §8, §9, §10 ma pierwszeństwo ADR-006) |
| Eksperymenty, uprząż, wyniki | `experiments/2026-11-21-wybor-modulow/` (`odczyt/`, `pola/`, `llm-e2e/`, `atak/`, `czas/`, `produkt/`, `harness/`, `recenzje/`, `RAPORT.md`) |
| Zbiór organizatora | `docs/02-materialy/organizator-uzp/` (dane, oczekiwane-json, szablon) |
| Skrypty | `scripts/` (`ci.py`, `release.py`, `verify_docs.py`, `verify_install.py`, `eval_process.py`) |
| GUI | `apps/web/` (osobna sesja, plan zadań w dokumentach GUI) |

## Pracujące równolegle agenty (stan na 2026-11-22 ok. 10:00)

Worker rdzenia (pomiar `process` na 147 dokumentach przez GLM, rozbudowa `eval_process.py`: wznawianie, F1 per pole, dostawcy), dwa Codexy (skany w silniku, pola pełnomocnictwa) oraz osobna sesja GUI. Przed rozpoczęciem pracy w tych obszarach sprawdź `git log origin/main` i `gh pr list`, żeby nie dublować.
