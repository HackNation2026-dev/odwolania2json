# E11: ścieżka pionowa end-to-end przez HTTP: warianty A, B, C, D, dolna granica „sam regex”, ablacje

**Wynik nie jest oficjalnym F1.** F1 przybliżony ewaluatora produkcyjnego (po PR #8/#9), przedział 95% z bootstrapu po sprawach (ziarno 20261122); porównania sparowane po sprawach.
Czas i RSS: pod obciążeniem maszyny (load avg ok. 20–35 na 8 rdzeniach, kilka grup liczy naraz): czasy i RSS ORIENTACYJNE, nie do decyzji. Zbiór kontrolny nietknięty w tym eksperymencie.

## Hipoteza i kryterium
H: LLM na tekście PDF (A) wystarcza dla dokumentów elektronicznych; skany wymagają OCR (B) albo obrazu (C, D); „sam regex” jest tylko dolną granicą.
Reguła (prerejestracja): wariant zastępuje inny, gdy dolna granica przedziału ΔF1 (sparowane) > 0; przy nierozstrzygnięciu tańszy, potem prostszy. Wynik osobno dla każdego typu wejścia, nie jedna liczba.

## Warianty
- **rules**: router regułowy + ekstraktor regułowy (bez LLM); `rules+OCR` na skanach (rapidocr, 200 dpi). Dolna granica.
- **A**: tekst warstwy PDF (pdfium) → LLM (1 wywołanie). Na skanie bez warstwy tekstu: jawny `technical_error/ocr_unavailable`.
- **B**: A + OCR rapidocr 200 dpi stron bez tekstu (`if_needed`); `B_ocr_always`: OCR każdej strony (tylko mieszany/S2/S5).
- **C**: tylko obrazy stron (JPEG 100 dpi, do 12) → LLM; bez OCR, więc cytaty nie mają kotwic (`partial`).
- **D**: tekst (PDF lub OCR) + obrazy stron → LLM.
- **Ablacje na odtworzonych odpowiedziach LLM** (replay, bez wywołań): `A+regex_override` (regex nadpisuje przy rozbieżności pól o stałym formacie), `A+regex_fill` (regex tylko uzupełnia brak), `A_replay` (kontrola: powtórka bez regexu = A, rep. 1).
- Model: MiniMax-M3.1-Flash-Preview (baza z E10), prompt p2, 1 powtórzenie dla skanów (5 dla A na tekście z E10).

## Zakres wykonania
Skany: 25 spraw z podzbioru (75 skanów, 25 mieszanych, 25 S2, 25 S5; zestaw grupy A, tylko sprawy rozwojowe). e11-scan-B: 144/150 wierszy (dok.×powt.), powt. ≤1 z 1, 6 wierszy czeka na ponowienie po błędzie sieci; e11-scan-C: 150/150 wierszy (dok.×powt.), powt. ≤1 z 1; e11-scan-D: 57/150 wierszy (dok.×powt.), powt. ≤1 z 1, 8 wierszy czeka na ponowienie po błędzie sieci; e11-scan-Balways: 0/75 wierszy (dok.×powt.), powt. ≤0 z 1; e11-DM3-text: 87/87 wierszy (dok.×powt.), powt. ≤1 z 1; e11-DM3-scan: 39/150 wierszy (dok.×powt.), powt. ≤1 z 1, 6 wierszy czeka na ponowienie po błędzie sieci. Wiersze z błędem sieci czekają na ponowienie i nie liczą się jako wynik.

## Wyniki: wejście tekstowe (oryginały PDF; 25 spraw + 12 negatywów)
| Wariant | F1, powt. 1 | F1, wszystkie powt. |
|---|---|---|
| rules | 0.242 [0.216; 0.266] (n=87; tech. błędów 3; 0/0 tok.) | — |
| A | 0.918 [0.868; 0.956] (n=87; tech. błędów 6; 1838/2207 tok.) | 0.938 [0.910; 0.959] (n=435; tech. błędów 24; 1286/2203 tok.) |
| C | 0.903 [0.849; 0.941] (n=83; tech. błędów 3; 3705/2871 tok.) | 0.890 [0.854; 0.921] (n=245; tech. błędów 10; 1823/2793 tok.) |
| D | 0.911 [0.858; 0.953] (n=87; tech. błędów 3; 6142/2288 tok.) | 0.944 [0.918; 0.964] (n=261; tech. błędów 4; 3866/2273 tok.) |
| A+regex_override | 0.922 [0.870; 0.960] (n=87; tech. błędów 6; 0/0 tok.) | — |
| A+regex_fill | 0.916 [0.866; 0.954] (n=87; tech. błędów 6; 0/0 tok.) | — |
| A_replay | 0.918 [0.868; 0.956] (n=87; tech. błędów 6; 0/0 tok.) | — |

## Wyniki: wejścia nietekstowe (jedno powtórzenie)
| Typ wejścia | Wariant | F1 [95%] (n dok.; błędy tech.; tokeny wej./wyj.) |
|---|---|---|
| skan (cały dokument jako obraz) | rules+OCR | 0.210 [0.185; 0.236] (n=75; tech. błędów 0; 0/0 tok.) |
| skan (cały dokument jako obraz) | A | 0.000 [0.000; 0.000] (n=75; tech. błędów 75; 0/0 tok.) |
| skan (cały dokument jako obraz) | B | 0.902 [0.847; 0.943] (n=71; tech. błędów 3; 2329/2794 tok.) |
| skan (cały dokument jako obraz) | B_ocr_always | brak |
| skan (cały dokument jako obraz) | C | 0.928 [0.894; 0.952] (n=75; tech. błędów 1; 7176/3244 tok.) |
| skan (cały dokument jako obraz) | D | 0.961 [0.935; 0.984] (n=26; tech. błędów 0; 7459/2508 tok.) |
| mieszany (str. 1 tekst, reszta skan) | rules+OCR | 0.187 [0.163; 0.213] (n=25; tech. błędów 0; 0/0 tok.) |
| mieszany (str. 1 tekst, reszta skan) | A | 0.944 [0.889; 0.976] (n=25; tech. błędów 1; 1874/4458 tok.) |
| mieszany (str. 1 tekst, reszta skan) | B | 0.916 [0.846; 0.967] (n=24; tech. błędów 1; 4565/4721 tok.) |
| mieszany (str. 1 tekst, reszta skan) | B_ocr_always | brak |
| mieszany (str. 1 tekst, reszta skan) | C | 0.840 [0.728; 0.924] (n=25; tech. błędów 5; 6538/5198 tok.) |
| mieszany (str. 1 tekst, reszta skan) | D | 0.980 [0.955; 1.000] (n=9; tech. błędów 0; 12418/5256 tok.) |
| S2 (dane tylko w obrazie na str. tekstowej) | rules+OCR | 0.235 [0.171; 0.305] (n=25; tech. błędów 0; 0/0 tok.) |
| S2 (dane tylko w obrazie na str. tekstowej) | A | 0.673 [0.630; 0.712] (n=25; tech. błędów 0; 616/648 tok.) |
| S2 (dane tylko w obrazie na str. tekstowej) | B | 0.979 [0.960; 0.993] (n=24; tech. błędów 0; 1880/906 tok.) |
| S2 (dane tylko w obrazie na str. tekstowej) | B_ocr_always | brak |
| S2 (dane tylko w obrazie na str. tekstowej) | C | 0.932 [0.897; 0.962] (n=25; tech. błędów 0; 2064/1586 tok.) |
| S2 (dane tylko w obrazie na str. tekstowej) | D | 0.992 [0.977; 1.000] (n=11; tech. błędów 0; 3054/993 tok.) |
| S5 (poprawny obraz, błędna niewidoczna warstwa) | rules+OCR | 0.000 [0.000; 0.000] (n=25; tech. błędów 0; 0/0 tok.) |
| S5 (poprawny obraz, błędna niewidoczna warstwa) | A | 0.625 [0.561; 0.687] (n=25; tech. błędów 0; 1180/1881 tok.) |
| S5 (poprawny obraz, błędna niewidoczna warstwa) | B | 0.724 [0.621; 0.810] (n=25; tech. błędów 2; 1192/4345 tok.) |
| S5 (poprawny obraz, błędna niewidoczna warstwa) | B_ocr_always | brak |
| S5 (poprawny obraz, błędna niewidoczna warstwa) | C | 0.927 [0.883; 0.958] (n=25; tech. błędów 0; 2115/2754 tok.) |
| S5 (poprawny obraz, błędna niewidoczna warstwa) | D | 0.876 [0.776; 0.971] (n=11; tech. błędów 0; 2796/2574 tok.) |

Razem skan+mieszany+S2+S5:

| Wariant | F1 [95%] |
|---|---|
| rules+OCR | 0.183 [0.163; 0.204] (n=150; tech. błędów 0; 0/0 tok.) |
| A | 0.530 [0.499; 0.552] (n=150; tech. błędów 76; 612/1164 tok.) |
| B | 0.893 [0.854; 0.924] (n=144; tech. błędów 6; 2429/3070 tok.) |
| B_ocr_always | brak |
| C | 0.904 [0.871; 0.932] (n=150; tech. błędów 6; 5374/3212 tok.) |
| D | 0.959 [0.933; 0.982] (n=57; tech. błędów 0; 6492/2662 tok.) |

## Porównania sparowane (ΔF1 = drugi − pierwszy, bootstrap po sprawach)
| Para | ΔF1 [95%] | dok. |
|---|---|---|
| text: A vs rules | +0.676 [+0.619; +0.723] (cand>base) | 87 |
| text: C vs A | -0.015 [-0.068; +0.040] (nierozstrzygnięte) | 87 |
| text: D vs A | -0.007 [-0.064; +0.050] (nierozstrzygnięte) | 87 |
| text: A+regex_override vs A_replay | +0.004 [-0.002; +0.009] (nierozstrzygnięte) | 87 |
| text: A+regex_fill vs A_replay | -0.002 [-0.005; +0.002] (nierozstrzygnięte) | 87 |
| skan: B vs A | +0.902 [+0.847; +0.944] (cand>base) | 71 |
| skan: C vs B | +0.024 [-0.028; +0.084] (nierozstrzygnięte) | 71 |
| skan: D vs B | +0.060 [+0.011; +0.148] (cand>base) | 26 |
| skan: D vs C | +0.051 [-0.008; +0.144] (nierozstrzygnięte) | 26 |
| skan: B vs rules+OCR | +0.693 [+0.627; +0.746] (cand>base) | 71 |
| skan: B_ocr_always vs B | — | — |
| mieszany: B vs A | -0.027 [-0.108; +0.049] (nierozstrzygnięte) | 24 |
| mieszany: C vs B | -0.082 [-0.217; +0.034] (nierozstrzygnięte) | 24 |
| mieszany: D vs B | +0.000 [-0.019; +0.017] (nierozstrzygnięte) | 9 |
| mieszany: D vs C | +0.237 [+0.041; +0.528] (cand>base) | 9 |
| mieszany: B vs rules+OCR | +0.732 [+0.657; +0.784] (cand>base) | 24 |
| mieszany: B_ocr_always vs B | — | — |
| s2: B vs A | +0.306 [+0.263; +0.351] (cand>base) | 24 |
| s2: C vs B | -0.045 [-0.082; -0.011] (base>cand) | 24 |
| s2: D vs B | +0.009 [+0.000; +0.026] (nierozstrzygnięte) | 10 |
| s2: D vs C | +0.032 [+0.008; +0.057] (cand>base) | 11 |
| s2: B vs rules+OCR | +0.746 [+0.679; +0.813] (cand>base) | 24 |
| s2: B_ocr_always vs B | — | — |
| s5: B vs A | +0.099 [-0.002; +0.208] (nierozstrzygnięte) | 25 |
| s5: C vs B | +0.203 [+0.110; +0.307] (cand>base) | 25 |
| s5: D vs B | +0.076 [-0.068; +0.220] (nierozstrzygnięte) | 11 |
| s5: D vs C | -0.069 [-0.181; +0.039] (nierozstrzygnięte) | 11 |
| s5: B vs rules+OCR | +0.724 [+0.622; +0.814] (cand>base) | 25 |
| s5: B_ocr_always vs B | — | — |

## Jak to działa i dlaczego tak wyszło
Warstwa tekstowa PDF jest wystarczająca dla dokumentów elektronicznych, a regexy same dają tylko ok. jedną czwartą F1 (pola formatowe: NIP, KRS, numery; role, nazwy, czynność wymagają LLM). Na skanach bez OCR wariant A kończy jawnym `ocr_unavailable` (F1 0 przez brak pliku, nie przez zmyślone dane). S5 pokazuje ryzyko ufania warstwie tekstowej: A i B (OCR tylko dla stron bez tekstu) czytają błędne cyfry, a warianty z obrazem (C, D) je omijają; `B_ocr_always` sprawdza, czy OCR każdej strony to naprawia. Wariant D łączy kotwice z tekstu/OCR (statusy `complete`) z obrazem (odporność na błędy odczytu), kosztem ok. 3× tokenów wejściowych.

## Ograniczenia
Mała próbka: 25 spraw, 1 powtórzenie na wariant skanowy; skany są syntetyczne (zestaw grupy A: rasteryzacja + szum/rozmycie/kąt/JPEG, ten sam generator szablonów), bez fizycznych skanów, pieczęci, zdjęć.
S2/S5 powstały algorytmicznie; S5 ma przesunięte cyfry w niewidocznej warstwie (+3 mod 10). Wszystkie warianty używają jednego modelu (M3.1-Flash-Preview); model M3 z E18 sprawdzono tylko w D (patrz niżej).
Ewaluator: miara przybliżona, próg 80% (miara `ratio`), bez oficjalnej definicji (U-Q01). Sieć niedostępna ok. 40 min (05:00–05:12) i seriami wcześniej; dotknięte wiersze ponowione, nie zapisane jako wyniki.
Czas/RSS pod obciążeniem (nie do decyzji); szczytowy RSS serwera zapisany w `E11/raw/*.meta.json` (`peak_rss_mb`, limit 14 GB: `systemd-run`).

## Wniosek decyzyjny
Decyzje wynikają z dolnych granic przedziałów ΔF1 w tabeli sparowanej (zob. wyżej), osobno dla typu wejścia:
- text: A vs rules: +0.676 [+0.619; +0.723] (cand>base)
- text: C vs A: -0.015 [-0.068; +0.040] (nierozstrzygnięte)
- text: D vs A: -0.007 [-0.064; +0.050] (nierozstrzygnięte)
- text: A+regex_override vs A_replay: +0.004 [-0.002; +0.009] (nierozstrzygnięte)
- text: A+regex_fill vs A_replay: -0.002 [-0.005; +0.002] (nierozstrzygnięte)
- skan: B vs A: +0.902 [+0.847; +0.944] (cand>base)
- skan: C vs B: +0.024 [-0.028; +0.084] (nierozstrzygnięte)
- skan: D vs B: +0.060 [+0.011; +0.148] (cand>base)
- skan: D vs C: +0.051 [-0.008; +0.144] (nierozstrzygnięte)
- skan: B vs rules+OCR: +0.693 [+0.627; +0.746] (cand>base)
- mieszany: B vs A: -0.027 [-0.108; +0.049] (nierozstrzygnięte)
- mieszany: C vs B: -0.082 [-0.217; +0.034] (nierozstrzygnięte)
- mieszany: D vs B: +0.000 [-0.019; +0.017] (nierozstrzygnięte)
- mieszany: D vs C: +0.237 [+0.041; +0.528] (cand>base)
- mieszany: B vs rules+OCR: +0.732 [+0.657; +0.784] (cand>base)
- s2: B vs A: +0.306 [+0.263; +0.351] (cand>base)
- s2: C vs B: -0.045 [-0.082; -0.011] (base>cand)
- s2: D vs B: +0.009 [+0.000; +0.026] (nierozstrzygnięte)
- s2: D vs C: +0.032 [+0.008; +0.057] (cand>base)
- s2: B vs rules+OCR: +0.746 [+0.679; +0.813] (cand>base)
- s5: B vs A: +0.099 [-0.002; +0.208] (nierozstrzygnięte)
- s5: C vs B: +0.203 [+0.110; +0.307] (cand>base)
- s5: D vs B: +0.076 [-0.068; +0.220] (nierozstrzygnięte)
- s5: D vs C: -0.069 [-0.181; +0.039] (nierozstrzygnięte)
- s5: B vs rules+OCR: +0.724 [+0.622; +0.814] (cand>base)

## Stan końcowy (finalizacja z replayu, bez wywołań API; 22.11.2026)
- Wiersze z błędem sieci/limitu nie weszły do liczb: 681 wierszy w `E11/raw/*.errors.jsonl` oraz 20 niepowtórzonych w `*.jsonl` (scan-B 6, scan-D 8, DM3-scan 6).
- **Niepełne:** D na skanach: 57 z 150 wierszy (skan 26, mieszany 9, S2 11, S5 11 dok.), więc porównania D vs B/C są na podzbiorze (liczba dok. w tabeli „dok.”), nie na pełnych 25 sprawach; `B_ocr_always`: niewykonane (0/75); B: 144/150; C: 150/150; A: 150/150.
- **DM3 (D + MiniMax-M3), `E11/wyniki-dm3.json`, skrypt `lib/analyze_dm3.py`:** tekst + obraz, 1 powt. Tekst: F1 0.933 [0.899; 0.963], n=87 (25 spraw + negatywy), ΔF1 vs A (M3.1) +0.015 [-0.038; +0.076], vs D(M3.1) +0.023 [-0.035; +0.086], nierozstrzygnięte. Skany (tylko 39 z 150 dok. gotowych: skan 19, mieszany 7, S2 6, S5 7): skan 0.944, mieszany 0.925, S2 0.986, S5 0.941; wobec B: skan +0.060 [+0.000; +0.176], S5 +0.110 [+0.013; +0.223]; wobec D(M3.1) na wspólnych dok.: S5 −0.042 [−0.075; −0.013], mieszany −0.057 [−0.151; −0.004], pozostałe nierozstrzygnięte. Próbki 6–19 dokumentów: tylko orientacyjne, nie wystarczają do wyboru modelu w wariancie D.
- Wniosek wynikający z danych: D vs A na tekście: nierozstrzygnięte, ok. 3× tokenów wejściowych, więc dla dokumentów z warstwą tekstową zostaje A (prostszy i tańszy). Na skanach: B (OCR+tekst) jest wyraźnie lepszy od A (A kończy `ocr_unavailable`); C i D z obrazem są lepsze od B tam, gdzie warstwa tekstowa jest błędna (S5: C vs B +0.203 [+0.110; +0.307]), więc obraz stron jest potrzebny jako zabezpieczenie przed zaufaniem do niewiarygodnej warstwy tekstowej; D vs C na S5 nierozstrzygnięte przy 11 dok. Wybór między C a D wymaga pełnego przebiegu D.
- Zbiór kontrolny nie został użyty (`KONTROLNY.md`).
