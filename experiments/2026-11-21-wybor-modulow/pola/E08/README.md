# E08: pola o stałym formacie (regex) na tekście PDF, OCR i z szumem

Skrypt: `../e08_fixed_fields.py` (jedno polecenie, ok. 2 min z mutacjami; `--no-mutation` ok. 10 s), mutacje osobno `../run_mutation_only.py`.
Surowe liczby: `wyniki.json` (źródła, pola, bootstrap), `mutacje.json` (mutanty, ocalałe). Wzorce: `../rules.py` (`PAT`), mutatory: `../mutate.py`.

## Hipoteza

Regex po etykiecie na warstwie tekstowej PDF daje F1 bliskie 1; na tekście z OCR spadek jest ograniczony i wynika głównie z pomyłek znaków cyfr (O/0, l/1), które da się naprawić tolerancją w tokenie po etykiecie.

## Metoda

- Pola: KRS/NIP/REGON (role z bloku nagłówka), PESEL, kwota, data operacji, oba rachunki, numer referencyjny przelewu, BZP, TED, numer postępowania, data pisma, data czynności. Pola tekstowe (nazwy, tytuły) poza zakresem (E07).
- F1: ewaluator `apps/backend/odwolania2json/evaluator.py` (po PR #8/#9), bootstrap 95% po 49 sprawach, różnice sparowane (`bootstrap.py`).
- Źródła tekstu: (1) PDF pypdfium2; (2) OCR własny zestaw grupy B: render 150 dpi + `jak_skan(szum=4)` + rapidocr 3.10.0 (CPU, 147 dokumentów; nie jest zestawem grupy A i nie ma fizycznych skanów); (3) tekst PDF z syntetycznym szumem na znakach `0/1/5/8` → `O/l/S/B` i gubieniem spacji, p = 1/2/4% na znak.
- Warianty: **strict** (tylko cyfry, bez poprawek) i **tolerant** (tokeny z `O I l S B` po etykiecie, poprawka na cyfry).
- Mutacje: 152 mutanty wzorców regex (kwantyfikatory `{n}`, litery etykiet, `?`, klasy cyfr, separatory, look-aroundy). Zabity = zmiana liczników TP/FP/FN pól stałych na tekście PDF rozwojowym, albo na 15 sondach syntetycznych.

## Wynik (F1, 95% przedział bootstrapu po sprawach)

| Źródło | strict | tolerant | tolerant − PDF | FP / FN (tolerant) |
|---|---|---|---|---|
| PDF (147 dok.) | 0,998 [0,995; 0,999] | 0,998 [0,995; 0,999] | 0 | 1 / 3 |
| OCR 150 dpi (147 dok.) | 0,947 [0,932; 0,961] | 0,948 [0,934; 0,962] | **−0,050** | 12 / 72 |
| PDF + szum 1% | 0,970 | 0,986 | −0,011 | 10 / 13 |
| PDF + szum 2% | 0,946 | 0,974 | −0,024 | 17 / 27 |
| PDF + szum 4% | 0,904 | 0,960 | −0,038 | 23 / 43 |

Różnica tolerant − strict (sparowana): PDF 0; **OCR +0,0013 [0,000; 0,003]**; szum 1% +0,017 [0,010; 0,023]; 2% +0,027 [0,020; 0,036]; 4% +0,056 [0,045; 0,067].

Najsłabsze pola na OCR (tolerant, F1): numer postępowania 0,81 (6 FP, 10 FN), BZP 0,88 (8 FN), oba rachunki 0,89 (rachunek odbiorcy/nadawcy zamienione miejscami lub pusty), czynność_dzień 0,91, TED 0,93, numer ref. 0,92.

Mutacje: **117 z 152 zabitych (77,0%)**; dev PDF sam zabija 95 (62,5%), dev+OCR 97 (63,8%), sondy dokładają 22. Ocalało 33 (głównie klasy cyfr `0-9`→`1-9`, kwantyfikatory kwoty, `?` przy separatorach, look-aroundy), szczegóły w `mutacje.json`. **Próg z AGENTS.md (100% zabitych) nie jest spełniony.**

## Jak to działa i dlaczego tak wyszło

Dokumenty organizatora są szablonowe, więc po etykiecie regex trafia niemal zawsze (PDF: 4 błędy na ok. 1600 pól). Spadek na OCR o 5 pp **nie wynika z pomyłek znaków** (tolerancja O/0, l/1 poprawia wynik realnego OCR tylko o 0,13 pp, a przy sztucznym szumie o 1,7–5,6 pp): rapidocr tu rzadko myli cyfry, za to zmienia kolejność odczytu i gubi etykiety. Typowy błąd: rachunek nadawcy i odbiorcy zamienione (wartość w kolumnie, etykieta w innej linii; rola z najbliższej etykiety przed liczbą jest wtedy odwrócona), albo wartość po etykiecie przepada, bo OCR rozbił ją na kilka linii lub zgubił kropkę w numerze postępowania. Tolerancja znaków ma więc sens jako tania asekuracja, ale to układ strony, nie alfabet cyfr, decyduje o OCR.

Mutacje: dane rozwojowe mają jeden szablon zapisu na pole, więc mutanty zmieniające obsługę rzadkich zapisów (REGON 14-cyfrowy, kwota z kropką, numer TED w starym formacie) przeżywają; wzorce z `?` i look-aroundami bronią się przed zapisami, których zbiór nie zawiera. To mierzy luki testów, nie błędy wzorców.

## Ograniczenia

- Reguły i wzorce były stroione na tym samym zbiorze rozwojowym i na tych samych szablonach: F1 PDF ≈ 1 to górna granica, nie prognoza dla zbioru testowego organizatora.
- OCR to rasteryzacja własnych PDF-ów z syntetycznym „skanem”, nie fizyczne skany; 150 dpi i jeden profil szumu. Rachunki: tylko jedna zamiana ról obserwowana ilościowo, bez analizy każdego przypadku.
- Szum syntetyczny dotyka tylko znaków cyfrowych i spacji; nie modeluje błędów układu, które w realnym OCR dominują.
- Mutanty mają własny zestaw operatorów; ocalałe nie są ręcznie sklasyfikowane jako równoważne.

## Wniosek decyzyjny

Kryterium planu: „brak regresji na OCR względem PDF poza ustaloną tolerancją”. Tolerancji nie ustalono przed pomiarem (recenzje), więc stosuję regułę porównawczą: regex+etykieta jest wystarczający jako **generator kandydatów i niezależna kontrola** dla pól stałych na PDF z warstwą tekstu (F1 0,998), ale **na OCR regres wynosi 5 pp i nie jest odzyskiwany tolerancją znaków**; dla skanów pola stałe powinny przechodzić przez LLM (z obrazem lub tekstem z układem) z weryfikacją regułą (cyfry z odpowiedzi muszą wystąpić w tekście, patrz hybryda w E07), a nie opierać się wyłącznie na regex. Pewność: średnia (jeden profil skanu, dane szablonowe). Otwarte: pomiar na fizycznych skanach, kolejność odczytu OCR (E03), uzupełnienie testów do 100% zabitych mutantów (sondy dla REGON 14, kwota z kropką, TED stary, klasy cyfr).

## Uwaga o czasie i zasobach

Czasy (`wall_s` w `wyniki.json`, ok. 2 min z mutacjami, OCR 3,5 s/dok. przy budowie zestawu) zebrano pod obciążeniem maszyny (load avg ok. 30 na 8 rdzeniach, równoległe grupy): **nie są liczbami do decyzji**. Pomiary jakości (F1, mutacje) od obciążenia nie zależą. Zestaw OCR zbudowano jednym procesem pod `nice`, bez ograniczenia wątków onnxruntime (powstał przed uwagą koordynatora).
