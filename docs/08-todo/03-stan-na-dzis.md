---
wersja: 0.1.0
aktualizacja: 2026-11-22
status: rzetelny opis stanu na koniec etapu (2026-11-22, ok. 10:00); odróżnia to, co sprawdziłem osobiście, od raportów agentów
---

# Stan na koniec etapu: co mamy, gdzie jesteśmy, co dalej

## Jedno zdanie

Backend (`python -m odwolania2json process input output`) **robi prawdziwą ekstrakcję dla dokumentów tekstowych i działa z fallbackiem dostawcy LLM**, ale nie ma jeszcze skanów w silniku, pól pełnomocnictwa ani pomiaru skuteczności produktu na całym zbiorze rozwojowym z prawdziwym LLM; zbiór kontrolny nietknięty.

## Sprawdzone osobiście (uruchomienie, 2026-11-22)

| Co | Wynik |
|---|---|
| `process` na starym `main` (rano) | zapisywał `{}` dla każdego PDF (atrapa); to już nieaktualne |
| `process` bez klucza LLM (aktualny `main`) | czytelny błąd `llm_authorization`, kod wyjścia 2, wsad nieprzetworzony, brak plików wyniku (świadoma decyzja self-checku, do rozstrzygnięcia: patrz plan) |
| `process` na `potwierdzenie_przelewu.pdf` ze sprawy `przyklad_01`, MiniMax zwrócił 429, odpowiedział GLM (`glm-5.3-flash`) | **kod wyjścia 0**, poprawny JSON, klucze i kolejność zgodne z referencją; 5 z 6 pól identycznych z referencją (`data_operacji`, `kwota`, `na_rachunek`, `numer_transakcji`, `tytul`); **`z_rachunku` różni się: referencja `05470680287581539721455024` (26 cyfr), wynik `5470680287581539721455024` (25 cyfr, utracone wiodące zero)**; `report.jsonl` zawiera `provider: fallback`, `switch_reason: llm_rate_limit` i flagę `unnormalized:/przelew_bankowy/z_rachunku` |
| MiniMax | HTTP 429 „Token Plan usage limit reached” (limit okresowy) |
| GLM na OpenCode Go | HTTP 200, ok. 0,8 s, wymaga własnego `User-Agent` i `x-opencode-session` |

To jest **jeden dokument, jedno wywołanie**: dowód, że ścieżka działa, nie miara skuteczności.

## Z raportów agentów i testów w repozytorium (nie powtarzałem)

- W `main` (PR #27–#33): czytnik pdfium z diagnozą strony, adapter OCR (rapidocr), prompt p2 i pipeline, normalizatory po naprawie luk E19 (mutacje 291/291), reguły czynności i BZP, serializer, klient LLM z ponowieniami, polityka eksportu (ADR-006), łańcuch dostawców (ADR-007), instalacja pip. Raportowane: 580+ testów zielonych, pokrycie ok. 97–98%.
- F1 przybliżony na 25 sprawach rozwojowych, **replay zapisanych odpowiedzi LLM** (bez nowych wywołań): tekst 0,938 [0,911; 0,960] → 0,956 [0,929; 0,976] po regułach czynności i BZP (ΔF1 +0,018 [+0,013; +0,024]). To nie jest pomiar `process` z prawdziwym LLM.
- Wyniki uprzęży (poza produktem), jeden generator dokumentów, skany syntetyczne: skan B 0,902, C 0,928, D 0,961 (n=26); S5 sama warstwa tekstu 0,625, obraz 0,927. Szczegóły: [raport](../../experiments/2026-11-21-wybor-modulow/RAPORT.md).

## W toku w chwili zapisu (nie jest w `main`, status niepotwierdzony)

| Praca | Kto | Gdzie |
|---|---|---|
| Pomiar `process` na 147 dokumentach rozwojowych przez GLM (próba 10, limit 200 wywołań), rozbudowa `scripts/eval_process.py` | worker rdzenia | worktree `m1core`; wynik trafi do `experiments/2026-11-21-wybor-modulow/produkt/E-produkt.md` |
| Skany w silniku (`extract/scan.py`, adapter `PageOcr`), pomiar odnajdywania wartości w tekście skanów | Codex | worktree `scan`, gałąź `m2-skany`; niezacommitowane |
| Pola pełnomocnictwa i podpięcie reguł do pipeline'u, test replay na zbiorze rozwojowym | Codex | worktree `poa`, gałąź `m2-pelnomocnictwo`; niezacommitowane |

Jeśli te prace nie zostały zmergowane, nie ma ich w `main`; sprawdź `gh pr list` i `git log origin/main`.

## Czego nie mamy (jawnie)

- **Pomiaru produktu na zbiorze organizatora z prawdziwym LLM.** Mamy jeden dokument i replay. Liczby F1 produktu na 147 dokumentach nie istnieją, dopóki worker rdzenia nie zapisze `E-produkt.md`.
- **Skanów i dokumentów mieszanych w produkcie.** OCR istnieje jako moduł, ale nie jest wpięty w `process`; skan bez warstwy tekstu daje dziś błąd `ocr_unavailable` lub pustą stronę według ADR-006.
- **Pól pełnomocnictwa z regułami** (`extract_poa`); dla pełnomocnictwa działa tylko odpowiedź LLM z normalizatorami.
- **Zbioru kontrolnego** (licznik 0), pomiaru czasu w ciszy (czasy z nocy to górne granice), fizycznych skanów, uruchomienia na Windows.
- **Rozstrzygnięcia dostawcy LLM:** zgodność MiniMax i GLM z wymogiem „firma i serwery w UE/EOG” oraz „open source” nieudowodniona; plan Go jest dla agentów kodujących (ADR-007, ryzyko po stronie użytkownika).
- **Znany błąd:** utrata wiodącego zera w numerze rachunku (`z_rachunku`), patrz wyżej; najpewniej normalizator lub odpowiedź LLM (do zbadania: czy zero znika w odpowiedzi modelu, czy w normalizacji).

## Co zrobić (kolejność)

1. **Naprawić utratę wiodącego zera w numerach rachunków** (reprodukcja: `przyklad_01/potwierdzenie_przelewu.pdf`, pole `z_rachunku`; test czerwony, potem poprawka w `domain/normalize.py`/pipeline; sprawdzić też `na_rachunek` i NIP/REGON/KRS/PESEL z wiodącym zerem).
2. **Dokończyć pomiar `process` na 147 dokumentach rozwojowych** (tekst), zapisać `E-produkt.md` z F1 per klasa i pole z przedziałem, listą dokumentów bez wyniku i zużyciem wywołań.
3. **Zmergować skany w silniku** (Codex `m2-skany`) i zmierzyć skany przez `process` (cel ok. 0,85; uprząż 0,90–0,96).
4. **Zmergować pola pełnomocnictwa** (Codex `m2-pelnomocnictwo`).
5. **Rozstrzygnąć decyzje człowieka** ([plan](01-plan-naprawczy.md)): dostawca LLM i klucz dla jury, `pypdfium2` wbrew ADR-002 pkt 3, pytania do mentora, zachowanie przy braku klucza (dziś brak plików wyniku), zakres mutacji, Windows, fizyczne skany.
6. **Jednorazowy przebieg na zbiorze kontrolnym** po zamrożeniu konfiguracji (`WYBOR.md` przed uruchomieniem, licznik `KONTROLNY.md`).

Szczegółowe instrukcje do każdego zadania: [zadania dla agentów](../00-organizacja/zadania-dla-agentow.md). Kontekst, środowisko i pułapki: [02-kontekst.md](02-kontekst.md).
