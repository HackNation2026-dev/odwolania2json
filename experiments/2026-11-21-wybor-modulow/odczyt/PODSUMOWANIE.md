# Podsumowanie grupy A: odczyt (E01–E05, zestaw skanów, F1 na skanach)

Wszystkie liczby: zbiór rozwojowy (49 spraw, 147 dok.), podzbiory 12 spraw dla OCR; syntetyczne skany z jednego generatora; nic nie jest oficjalnym F1. **Wszystkie czasy zebrano pod obciążeniem (load avg 20–57) i są niewiążące**; czasy do decyzji (E02b) czekają na ciche okno.

| E | Wynik | Decyzja | Pewność | Otwarte |
|---|---|---|---|---|
| zestaw | 342 wpisy (147 skanów w 4 profilach wg 3 skanów negatywnych i szablonu, 49 mieszanych, 49 S2, 49 S5, 36 obrotów, 12 skosów), blokada przecieku, 9 testów zielonych; [ZESTAW.md](ZESTAW.md) | używać przez `load_zestaw` (grupy B–D) | wysoka co do pochodzenia, średnia co do realizmu | skany fizyczne ~10 spraw; prześwit, perspektywa, pieczęcie |
| E01 | pdfium: 1454/1454 wartości (1,000), IoU po `/Rotate` ≥ 0,977 (śr. ≥ 0,999), tusz 98,8–99,4%; pypdf, pdfminer, PyMuPDF też 1,000; kolejność czytania przelewów: pdfminer 92/98, reszta 98/98 | **zostaje pypdfium2** (kryterium ≥ 0,99 spełnione; PyMuPDF AGPL, pdfminer wolniejszy i gorsza kolejność) | wysoka dla PDF z generatora, średnia poza nim | natywny `/Rotate`, nietypowy MediaBox, układy bez etykiety przed wartością |
| E02 | OCR: 96,7–97,8% wartości (exact) przy 100–300 dpi A4, różnice w granicach szumu (359 wartości); `max_side_len` 2000 czyni 200 i 300 dpi identycznymi; limit 4000: 95,0% i droższy; RSS proces 0,7–1,1 GB (< 4 GB) | 100–150 dpi A4, limit ≈ 2000 px; konfiguracja w pikselach, nie dpi | średnia | **E02b (p50/p95, zimny/ciepły, szablon, 3 skany negatywne) niewykonane**: czeka na ciche okno; skrypt gotowy |
| E03 | obrót 90°: +0,46 [0,37–0,56], 180°: +0,30 [0,23–0,37] z wykrywaczem; 270° rapidocr radzi sobie sam; deskew −0,011 [−0,024…0,001]; Otsu −0,033 [−0,058…−0,013] | wykrywanie obrotu **tak, tanio** (obecne ≈ 2× OCR przekracza regułę kosztu); deskew i Otsu **nie** | średnia-wysoka | wyzwalacz obrotu z pewności OCR, skosy > 3°, zdjęcia |
| E04 | 0 z 843 stron skanopodobnych oznaczonych jako tekst (górna granica 0,36%); 1 z 514 stron tekstowych niepotrzebnie do OCR (0,19%); 49/240 stron mieszanych bez OCR | v1 + sygnał niewidocznego tekstu; kryterium spełnione | wysoka (zbiór), średnia (poza generatorem) | progi wokół pokrycia 0,5; częściowa warstwa OCR |
| E05 | PDF: 0 błędnych/zgadniętych, 86,0% zakotwiczonych (14% niejednoznacznych: duplikaty wartości); OCR: 87% zakotwiczonych, 73% przypadków z poprawnym bbox; `/Rotate` 180/270: 100%, 90: 94,6% (IoU ≥ 0,998) | resolver bezpieczny, ale **kryterium ≥ 0,95 niespełnione** dla samej wartości; cytat z kontekstem + zawężenie obrysu; OCR wymaga słów drobniejszych niż linia | wysoka (PDF), niska (OCR) | prawdziwe cytaty LLM, granularność słów OCR |
| F1 skany | skan − oryginał: −0,083 [−0,129…−0,042] (36 dok., ekstraktor regułowy); mieszany bez straty (0,173 vs 0,172); S2 0,265 vs 0,286; **S5: 0,000 (0 TP, 20 FP) przy `complete`** | **warstwa tekstu stron skanowych nie może wchodzić do wyniku** (BLOKERY pkt 6) | wysoka co do S5, średnia co do reszty | powtórzyć na ekstraktorze LLM |

## Najważniejsze ustalenia

1. **S5 to cichy błąd danych**: `read_document` dokleja słowa OCR do niewidocznej, błędnej warstwy; wartości z warstwy wygrywają. Diagnoza stron (E04) wysyła stronę do OCR, ale tego nie wystarcza.
2. „dpi” w konfiguracji OCR nie jest miarą: zależy od MediaBox (skan szablonu deklaruje 96 dpi przy 200 dpi obrazu) i od `max_side_len`; do ADR: konfigurować piksele dłuższego boku.
3. Wartość jako cytat kotwiczy się niejednoznacznie w 14% (PDF): to wymaganie na prompt i na moduł kotwiczenia.

## Pliki

[E01](E01/README.md) · [E02](E02/README.md) · [E03](E03/README.md) · [E04](E04/README.md) · [E05](E05/README.md) · [F1](F1/README.md) · [BLOKERY](BLOKERY.md) · [ZESTAW](ZESTAW.md). Surowe liczby w `*.json`; skrypty powtarzalne jednym poleceniem (w README każdego).
