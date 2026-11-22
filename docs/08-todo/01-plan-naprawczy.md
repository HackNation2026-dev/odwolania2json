---
wersja: 0.1.0
aktualizacja: 2026-11-22
status: plan naprawczy; aktualizuj statusy po każdym zmergowanym PR
---

# Plan naprawczy

Cel: działający backend (`process`) na dokumentach tekstowych, skanowych i mieszanych, zmierzony na zbiorze organizatora, z dostawcą LLM i zapasowym. Szczegóły zadań: [zadania dla agentów](../00-organizacja/zadania-dla-agentow.md). Kontekst: [02-kontekst.md](02-kontekst.md).

## Stan startowy (2026-11-22, po PR #32)

Działa w `main`: `process` robi prawdziwą ekstrakcję **tekstu** (czytnik pdfium, prompt p2, jedno wywołanie LLM, normalizatory, serializer, polityka eksportu ADR-006), adapter OCR (rapidocr), reguły czynności i BZP, klient LLM z ponowieniami, instalacja pip (`run.sh`, `start.bat`). Fallback dostawcy (PR #33) już jest. Nie ma jeszcze w `main`: skanów w silniku, pól pełnomocnictwa, pomiaru `process` na zbiorze z prawdziwym LLM.

## Ścieżka krytyczna (kolejność)

**Najpierw (znany błąd z testu end-to-end):** utrata wiodącego zera w numerze rachunku (`z_rachunku` w `przyklad_01/potwierdzenie_przelewu.pdf`: referencja 26 cyfr, wynik 25). Szczegóły i kolejność kroków: [stan na dziś](03-stan-na-dzis.md).

| Krok | Co | Status | Bramka akceptacji |
|---|---|---|---|
| 1 | Fallback dostawcy LLM (MiniMax → GLM) + self-check obu + ślad dostawcy w raporcie | **zrobione** (PR #33, ADR-007, konfiguracja `LLM_FALLBACK_*`) | testy z atrapą HTTP, kanarek dla obu kluczy |
| 2 | Pomiar `process` na 147 dokumentach rozwojowych z prawdziwym LLM (`scripts/eval_process.py`, w `main`) | w toku: próba 10 dokumentów, potem reszta przez GLM (limit 200 wywołań) | F1 przybliżony tekstu ≥ ok. 0,90 z przedziałem; lista dokumentów bez wyniku; zapis w `experiments/.../produkt/E-produkt.md` |
| 3 | Skany w silniku (OCR, S5, obrót, adapter `PageOcr`) | w toku (Codex, gałąź `m2-skany`) | ≥ 96% wartości odnalezionych w tekście skanów rozwojowych; S5 bez wartości z błędnej warstwy |
| 4 | Pola pełnomocnictwa i podpięcie `refine_appeal`/`refine_poa` do pipeline'u | w toku (Codex, gałąź `m2-pelnomocnictwo`) | brak spadku F1 per pole; zero przeżytych mutantów w nowym module |
| 5 | Pomiar skanów end-to-end przez `process` z LLM | po krokach 1–3 | skan ≥ ok. 0,85 (referencja uprzęży: 0,90–0,96) |
| 6 | Decyzje człowieka (patrz niżej) i ADR-y po eksperymentach | równolegle | zmergowane ADR-y: zmiana ADR-002 pkt 3, 4, 8, 12; ADR-007 (dostawcy) |
| 7 | Zbiór kontrolny: jeden przebieg, wybór zapisany w `WYBOR.md` przed uruchomieniem | na końcu | raz, licznik w `KONTROLNY.md` |

Kroki 3 i 4 są niezależne od 1–2 i trwają równolegle; zbieżność w `extract/pipeline.py` (małe diffy, częsty rebase).

## Do zrobienia po ścieżce krytycznej

| Zadanie | Dlaczego | Szczegóły |
|---|---|---|
| Ponowienia semantyczne dla `llm_invalid_response` | ok. 8% odwołań (ok. 10 dokumentów) nie dało żadnego pola; odpowiada za ok. 200 z 353 FN | Z04, ocena Fable §C |
| Odporność parsera PDF (proces potomny z limitem pamięci i czasu, limit pikseli) | jeden złośliwy plik ubija proces (E12 B08) | Z12 |
| Wykrywanie ukrytego tekstu i wstrzyknięć | atrapa LLM wykonuje 5 z 6 ataków (E13) | Z12 |
| Decyzja zachowania przy braku klucza | dziś self-check kończy wsad kodem 2 **bez plików wyniku** (spójne z „zły klucz = czytelny błąd”, ale README organizatora oczekuje JSON dla każdego pliku): rozstrzygnij, czy zapisywać `{}` + raport | Z02, ADR-006 |
| Dług mutacji w `db/` | `DataRepository` nie jest na ścieżce CLI | Z13, decyzja zakresu w ADR-003 |
| Pomiar czasu w cichej maszynie, ok. 10 fizycznych skanów | czasy z nocy to górne granice; skany są syntetyczne | Z08 |
| Kotwiczenie cytatów i dowody (transparentność, GUI) | 86% jednoznacznych (PDF), 73% poprawnych bbox (OCR); bez wpływu na F1 | Z09 |
| Klasa dokumentu z samego pliku konfiguracyjnego | punkty etapu 2 (elastyczność) | Z11 |
| API HTTP v1 i GUI minimum | tylko po działającym CLI; GUI w toku w innej sesji (`apps/web`) | Z14, plan zadań GUI |

## Ryzyka (z oceny Fable i eksperymentów)

1. **Dostawca LLM:** MiniMax bywa wyczerpany (HTTP 429), a jego zgodność z wymogiem „firma i serwery w UE/EOG” i „open source” jest nieudowodniona (ADR-002 pkt 8). Zapasowy GLM (OpenCode Go) ma nieznaną lokalizację i warunki planu Go przewidują ruch agentów kodujących. Bez rozstrzygnięcia: ryzyko dyskwalifikacji niezależne od F1.
2. **Klucz dla jury:** brak kanału i limitu budżetu; wyczerpany limit = F1 0 dla całego wsadu.
3. **Jeden generator dokumentów:** wszystkie liczby mogą być zawyżone na ukrytym zbiorze; skany są syntetyczne z jednym powtórzeniem.
4. **Niestabilna sieć** (IPv6 do API zawodzi): workery i pomiary padają; ponawiaj.

## Decyzje człowieka (agent nie rozstrzyga)

1. Dostawca LLM i klucz dla jury: zgoda mentora na MiniMax albo drugi dostawca z UE; doładowanie kredytów OpenCode, jeśli ma służyć płatny endpoint.
2. Zatwierdzenie `pypdfium2` wbrew ADR-002 pkt 3.
3. Pięć pytań do mentora: czy MiniMax spełnia wymogi; jak liczy ewaluator (agregacja, błędna wartość jako FP czy FP+FN, brak klucza, brak pliku); jak powstały skany i mieszane w teście; jak rozmiar modelu przekłada się na punkty; jak jury uruchomi rozwiązanie.
4. Zakres testów mutacyjnych do terminu (ADR-003) i usunięcie `.github/workflows/docs.yml`.
5. Windows: uruchomienie `start.bat` i `scripts/verify_install.py` (agent zdalny nie ma Windows); ok. 10 fizycznych skanów.
6. Zachowanie przy braku klucza (patrz wyżej).
