# F1 pól na skanach (przez HTTP, ewaluator produkcyjny po naprawie)

Polecenie (z korzenia `experiments/2026-11-21-wybor-modulow`, `OMP_NUM_THREADS=2`): `../../.venv-exp/bin/python odczyt/F1/f1_scans.py --ocr-dpi 72` → `f1-72.json`, `f1-72-dokumenty.json` (ok. 17 min pod obciążeniem).

## Hipoteza i metoda

Hipoteza: po rasteryzacji do skanu F1 pól spada nieznacznie wobec dokumentu z warstwą tekstu, a warianty S2 (dane przelewu tylko w obrazie na stronie tekstowej) i S5 (obraz poprawny, niewidoczna warstwa tekstu z błędnymi cyframi) są obsługiwane poprawnie.
Metoda: backend uprzęży (`harness/server.py`, podproces pod limitem 14 GB), wgranie przez HTTP, `pdfium` + `rapidocr` (`ocr_dpi` = 72 w parametrze uprzęży = skala 1,0 względem MediaBox skanów 1240×1754 pt, czyli ≈ 150 dpi A4), router regułowy, ekstraktor regułowy; podzbiór 12 spraw (jak E02; 36 dok. oryginałów, 36 skanów, 12 `mieszany`, 12 `s2`, 12 `s5`).
Miara: `evaluate_document` i `bootstrap_f1` z `apps/backend/odwolania2json` (po PR #8/#9: TP poprawnie, błędna wartość tylko FP, próg 80%); przedział 95% bootstrapem po sprawach, 2000 prób, ziarno 20261122. Różnica wobec `leaf_f1` uprzęży: tamta liczy multizbiór niepustych liści (bez progu 80% i bez dopasowania ścieżek), ewaluator liczy po ścieżkach pól z wartościami TN dla pustych pól; tu raportowany jest tylko ewaluator produkcyjny. Nie jest to oficjalne F1.

## Wynik (ekstraktor regułowy = wąska linia bazowa, więc liczy się różnica, nie poziom)

| Wariant | dok. | F1 pól | przedział 95% (po sprawach) | TP / FP / FN | F1 per klasa (odw. / pełn. / przel.) | wyniki |
|---|---|---|---|---|---|---|
| oryginał (warstwa tekstu) | 36 | 0,236 | 0,208–0,259 | 55 / 3 / 353 | 0,172 / 0,348 / 0,286 | 29 complete, 3 partial, 4 ambiguous |
| skan (profile P1–P4, OCR 150 dpi A4) | 36 | 0,153 | 0,107–0,197 | 34 / 4 / 372 | 0,079 / 0,273 / 0,222 | 28 complete, 2 partial, 6 ambiguous |
| mieszany (odwołania: str. 1 tekst, reszta skan) | 12 | 0,173 | 0,135–0,206 | 23 / 2 / 218 | odw. 0,173 | 11 complete, 1 ambiguous |
| S2 (przelew, dane w obrazie) | 12 | 0,265 | 0,200–0,326 | 11 / 0 / 61 | przel. 0,265 | 3 complete, 7 partial, 2 ambiguous |
| **S5 (pełnomocnictwa, zła warstwa)** | 12 | **0,000** | 0,000 | **0 / 20 / 75** | pełn. 0,000 | 10 complete, 1 partial, 1 ambiguous |

Różnica skan − oryginał (para po tych samych 36 dokumentach i 12 sprawach): **−0,083 (przedział −0,129 … −0,042)**: spadek istotny co do znaku, ale liczony na ekstraktorze, który i tak wydobywa tylko 13% pól z tekstu.
Delty zapisane w JSON dla `mieszany`, `s2`, `s5` **są nieprawidłowe**: baza oryginału obejmuje 3 klasy na sprawę, a wariant tylko jedną; do porównania służy kolumna „per klasa” (oryginał tej samej klasy): mieszany 0,173 vs 0,172 (bez straty), S2 0,265 vs 0,286 (strata mała, w granicach próbki 12 dok.), S5 0,000 vs 0,348.
Czas i RSS (niewiążące, load avg ≈ 40): 14,8 s/dok. dla skanu (3,9–4,0 s dla jednostronicowych S2/S5), szczyt RSS serwera 686 MB, brak błędów technicznych w żadnym dokumencie.

## Jak to działa i dlaczego tak wyszło

- Spadek na skanach pochodzi z OCR: chybione identyfikatory (patrz E02) i nazwy podzielone na linie; oryginał ma pola w jednym tokenie. Klasyfikacja dokumentu (router regułowy) pogarsza się słabo (F1 klasyfikacji 0,89 → 0,83; 4 → 6 dokumentów `ambiguous`).
- **S5: 20 FP przy 0 TP:** strona z niewidoczną warstwą jest wysyłana do OCR (E04), ale ekstraktor regułowy czyta słowa z warstwy PDF (`pdf`) razem ze słowami OCR i wartości z warstwy (cyfry +3) wygrywają. Wynik to `complete` z błędnymi NIP/KRS, czyli **cichy błąd danych**, najgorszy możliwy: żaden kod nie sygnalizuje problemu. To wynik uprzęży, nie wada OCR: moduł odczytu musi przy stronie ocenionej jako skan/mieszana **odrzucać** warstwę tekstową (albo uzgadniać ją z OCR i zgłaszać niezgodność).
- S2: dane w obrazie na stronie tekstowej są odczytywane przez OCR (strona oznaczona `mixed_page`), 7 z 12 kończy `partial` (brak części pól), ale bez błędnych wartości (FP 0).

## Ograniczenia

12 spraw (36 dok.): przedziały szerokie, różnice < 5 pp nierozstrzygalne; jeden generator; ekstraktor regułowy nie reprezentuje LLM, więc poziom bezwzględny nie ma znaczenia dla decyzji o ekstraktorze. S5 sprawdzony tylko na 12 pełnomocnictwach, mechanizm wyjaśniony z kodu `diagnose_page` i czytnika (nie z osobnego testu jednostkowego).

## Wniosek decyzyjny

Skan kosztuje ok. 8 pp F1 pól (−0,083, 95%: −0,13…−0,04) przy tym ekstraktorze: do powtórzenia na ekstraktorze LLM (grupy B–D). **S5 wymaga decyzji projektowej: warstwa tekstowa strony skanowej nie może wchodzić do wyniku** (kryterium „zero stron skanu jako tekst” z E04 jest spełnione, ale nie wystarcza). Pewność: wysoka co do S5 (0 TP, 20 FP), średnia co do wielkości spadku na skanach.
