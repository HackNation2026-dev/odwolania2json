# Raport: wybór modułów odczytu i ekstrakcji (CPU, 16 GB)

Data: 2026-11-22. Plan: [plan z korektą 0.2](../../docs/05-weryfikacja/plan-eksperymentow-wyboru-modulow-2026-11-21.md). Recenzje planu: [Fable](recenzje/fable.md), [Codex](recenzje/codex.md).

**Co to jest i czym nie jest.** Wszystkie liczby to F1 przybliżony ewaluatorem zespołu (po naprawie, PR #8 i #9), zbiór rozwojowy (49 spraw, 147 dokumentów), przedziały 95% z bootstrapu po sprawach. To nie jest oficjalny F1 organizatora. Zbiór kontrolny **nie został użyty** (licznik 0). Dane pochodzą z jednego generatora dokumentów, więc wyniki regułowe są górną granicą. Skany są syntetyczne; fizycznych skanów nie było. Komunikacja end-to-end szła przez HTTP z uprzężą `harness/server.py`, nie z produktem (trasy v1 nie istnieją w `openapi.yaml`).

## 1. Decyzje (hipotezy do zatwierdzenia w ADR, nie fakty)

| Warstwa | Wybór | Dowód | Pewność | Ryzyko |
|---|---|---|---|---|
| Czytnik PDF | `pypdfium2` | E01: 1454/1454 wartości, bbox po `/Rotate` IoU ≥ 0,977; konkurenci też 1,000 | wysoka dla PDF z generatora | ADR-002 odrzucił go jako docelowy; wymaga decyzji użytkownika |
| OCR | `rapidocr` + `onnxruntime` CPU, render do ok. 2000 px dłuższego boku, wykrywanie obrotu, bez deskew i binaryzacji | E02: ok. 97% wartości, RSS 0,7–1,1 GB; E03: obrót +0,30…+0,46, deskew −0,011, Otsu −0,033 | średnia | skany syntetyczne; czas niezmierzony wiążąco |
| Diagnoza stron | reguły (słowa, pokrycie obrazem, sygnał niewidocznego tekstu) | E04: 0 z 843 skanopodobnych stron uznanych za tekst; 1 z 514 tekstowych niepotrzebnie do OCR | wysoka (zbiór), średnia (poza nim) | S5, patrz niżej |
| Wejście do LLM | tekst PDF + prompt p2, jedno wywołanie na dokument; **na skanach i S5 także obraz strony** | E10: tekst 0,938 [0,910; 0,959]; E11 skany: A (sama warstwa tekstu) 0,000, B (OCR) 0,902, C (obraz) 0,928, D (tekst+obraz) 0,961 (n=26) | średnia na skanach (próbka mała, 1 powtórzenie) | D przebadane częściowo: 57 z 150 dokumentów |
| Router | reguły najpierw, LLM tylko gdy niepewne, z opisem typów obcych | E06: 147/147 pozytywów; LLM z promptem ogólnym 23/40 FP na negatywach zbliżonych | niska co do FP (opis typów znany autorowi) | brak niezależnych negatywów |
| Role i podmioty | LLM | E07: 0,997 vs reguły 0,987, Δ +0,010 [+0,003; +0,018], 0 błędnych ról na 294 | średnia | układy bez etykiet, konsorcja |
| Pola stałe | regex jako generator kandydatów i kontrola na PDF; na skanach przez LLM z weryfikacją regułą | E08: F1 0,998 (PDF), 0,948 (OCR 150 dpi) | średnia | mutacje 77% zabitych, próg 100% niespełniony |
| Zaskarżona czynność | reguły główne, LLM z promptem wskazującym źródło jako kontrola | E09: reguły 0,993; LLM ogólny 0,749, LLM v2 0,972 | średnia | brak klasy 12 w danych prawdziwych |
| Polityka braków | **nie zerować pola z braku kotwicy; eksportować `partial` z flagą** | E17: zerowanie −0,021 [−0,029; −0,014]; brak eksportu `partial` −0,208 [−0,268; −0,155] | wysoka co do kierunku | uprząż ≠ produkt |
| Model LLM | MiniMax-M3 lub M2.5 zamiast Flash-Preview do rozstrzygnięcia | E18: M3 0,961 (+0,035 [+0,002; +0,076], 706 vs 2566 tokenów wyjścia), M2.5 0,959 (+0,033 [+0,007; +0,067]) | niska-średnia (jeden dostawca, 2 powtórzenia) | licencja i lokalizacja (ADR-002); inny dostawca niesprawdzony |

## 2. Najważniejsze ustalenia

1. **Warstwa tekstu stron skanowych nie może wchodzić do wyniku (S5).** Poprawny obraz z błędną niewidoczną warstwą daje F1 0,000 (0 TP, 20 FP) przy statusie `complete`: cichy błąd danych. `read_document` dokleja słowa OCR do tej warstwy i wartości z warstwy wygrywają. Obraz strony do LLM podnosi wynik S5 z 0,625 (A) do 0,927 (C). To najcięższy błąd jakości w całym zestawie.
2. **Skan kosztuje 0,083 F1** względem oryginału (ekstraktor regułowy, [−0,129; −0,042]). Mieszane strony bez straty. Wariant tekst+obraz zmniejsza lukę.
3. **Kotwiczenie cytatów jest jednoznaczne tylko w 86% (PDF) i 73% poprawnych bbox (OCR)**, kryterium ≥ 95% niespełnione. Powód: duplikaty wartości na stronie. Wymaga cytatu z kontekstem i słów OCR drobniejszych niż linia.
4. **„dpi” w konfiguracji OCR nie jest miarą:** skan szablonu deklaruje 96 dpi przy obrazie 200 dpi, a `max_side_len` 2000 czyni 200 i 300 dpi identycznymi. Konfigurować piksele dłuższego boku.
5. **Normalizatory mają luki** (E19): NIP/REGON/KRS ze spacjami i myślnikami dają `None`, kwota `1.000,50` daje 1,0 (cicha wartość błędna), daty skrócone, rzymskie miesiące. Sumy kontrolne w referencjach są poprawne tylko u 64% NIP, 70% REGON, 34% IBAN, więc **nie wolno ich używać jako twardego filtra**.
6. **Ewaluator miał błąd**, który unieważniał każdy ranking: zgodna wartość była TN, więc F1 pól wynosił 0 (naprawione). Wariant „błędna wartość = FP i FN” zamiast „tylko FP” jest konfigurowalny; wybór wymaga potwierdzenia mentora (ADR-005, U-Q01/U-Q02).

## 3. Odporność i atak na HTTP (E12–E16, uprząż)

51 wektorów: luka tak 4, częściowo 16, nie 31. Wynik opisuje uprząż; luki to testy do przeniesienia do produktu.

| Priorytet | Luka | Dowód |
|---|---|---|
| 1 | PDF z samoodwołującym się XObject ubija serwer (brak pamięci przy limicie 6 GB po ok. 24 s); inne bomby przeżyły przy 4,6–5,2 GB | E12 B08, B02, B03: wymagany parser w procesie potomnym z limitem pamięci i czasu |
| 2 | Obcy `Origin` tworzy wsad; 1 GiB bez `Content-Length` czytany w całości; `/system` ujawnia ścieżkę hosta | E12 P05, F01 |
| 3 | Posłuszny LLM wykonuje 5 z 6 ataków wstrzyknięcia (zwróć `{}`, ukryty tekst, router `foreign`); MiniMax: 0 wartości atakującego w 27 przebiegach (próbka mała) | E13; detektor ukrytego tekstu 5/5 i 49/49 S5, 5/159 fałszywych alarmów |
| 4 | Klucz LLM trafia w 2 nagłówkach do dowolnego hosta z konfiguracji; brak limitu budżetu (60 wywołań na żądanie 0,98 MB) | E14 C02, L02, L03; wycieku kanarka: 0 |
| 5 | Po `kill -9` stan wsadu ginie (404), do 52 z 60 dokumentów osieroconych; kolejka bez limitu | E15; wyniki bajtowo identyczne 60/60 przy w=1/2/4, 0 uszkodzonych plików |
| — | Traversal, symlinki, SSRF z PDF, ReDoS (0,15 s): bez luki | E12 |

Determinizm kodu (E16): 0 różnic bajtowych w 3 przebiegach i na nagranych odpowiedziach LLM; kolejność kluczy 50/50.

## 4. Czas i pamięć

**Nie ma jeszcze wiążących liczb.** Wszystkie czasy z grup A–D zebrano przy load average 20–57 na 8 rdzeniach i są niewiążące (OCR 17–35 s na stronę zamiast ok. 1–3 s). Pomiar w cichym oknie prowadzi worker T (katalog `czas/` nie istnieje do odwołania). Sekcja zostanie uzupełniona po jego zakończeniu; jeśli `czas/PODSUMOWANIE.md` nie istnieje, pomiar nie został ukończony.

## 5. Czego nie zrobiono

- **Zbiór kontrolny:** nietknięty (limit API MiniMax do ok. 07:40 i termin). Brak jakiegokolwiek wyniku końcowego.
- **Niepełne:** D na skanach 57/150 dokumentów, D+M3 skany 39/150, `B_ocr_always` 0/75, prompt p1 43/108; effort low/high tylko na 12 sprawach. Wiersze błędów sieci i limitu (E10 539+81, E11 681+20, E18 379+12) nie weszły do liczb.
- **Poza zasięgiem zdalnym:** fizyczne skany ok. 10 spraw, test na produktowym backendzie, prawdziwe cytaty LLM w E05, JBIG2/JPX i awarie prawdziwego OCR w E12.
- **Inny dostawca LLM** (porównanie rozmiarów między dostawcami): niesprawdzony; użyto wyłącznie klucza MiniMax.
- **Test faktu osadzonego na stronie 3** (długi dokument): dane go nie zawierają.
- **Apache Tika:** nie sprawdzona w dokumentacji (sieć niedostępna); wstępna ocena bez weryfikacji: raczej nie.

## 6. Proponowane decyzje do ADR i kolejność prac

1. Odczyt: `pypdfium2` jako adapter za kontraktem `Reading`; decyzja użytkownika wobec ADR-002 pkt 3.
2. Nigdy nie ufać warstwie tekstu strony, która ma obraz zdominowany treścią (S5): obraz do LLM lub kontrola zgodności warstwy z OCR próbki.
3. Polityka: `partial` z flagą zamiast zerowania i zamiast braku pliku; bbox nie decyduje o treści ocenianego JSON.
4. OCR konfigurowany w pikselach; wykrywanie obrotu tak, deskew i binaryzacja nie.
5. Backend produktowy: parser PDF w procesie potomnym z limitem, walidacja Host/Origin, limit ciała, trwały stan wsadu, jeden nagłówek klucza i walidacja `base_url`.
6. Naprawić normalizatory (E19) i dopisać testy do 100% zabitych mutantów w zakresie.
7. Ponowić eksperymenty C i T po powrocie limitu API i w cichej maszynie; dodać fizyczne skany ok. 10 spraw przed wyborem OCR.

## 7. Powtarzalność

Każdy eksperyment jednym poleceniem (patrz `E##/README.md`); środowisko `.venv-exp` (Python 3.13, opis w `harness/ENV.md`). Surowe liczby w `E##/wyniki.json`; surowe odpowiedzi LLM w `llm-e2e/E##/raw/` (bez klucza, kontrola w `llm-e2e/WYCIEK.md`).

Podsumowania grup: [odczyt](odczyt/PODSUMOWANIE.md) · [pola](pola/PODSUMOWANIE.md) · [llm-e2e](llm-e2e/PODSUMOWANIE.md) · [atak](atak/PODSUMOWANIE.md).
