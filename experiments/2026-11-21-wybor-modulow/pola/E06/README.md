# E06: router — reguły, LLM czy hybryda

Skrypty: `../e06_router.py` (całość, ok. 40 min głównie przez API; z cache LLM powtórka ok. 1 min; `--no-llm` tylko reguły), `../e06_http_check.py` (część HTTP), `../hard_negatives.py` (negatywy zbliżone do klas).
Surowe liczby: `wyniki.json`, `http_wyniki.json`, `run.log`. LLM: MiniMax-M3.1-Flash (alias z odpowiedzi API), protokół Anthropic po HTTP, temperatura 0, **jedno wywołanie na dokument i wariant** (bez powtórzeń: wariancji nie zmierzono), 602 wywołania sieciowe + 110 z cache, 0 awarii po ponowieniach, 455 tys. tokenów wejścia / 67 tys. wyjścia. Klucz nie jest zapisywany nigdzie (sprawdzone grepem po `E06`, `cache/`).

## Hipoteza

Sygnały regułowe wystarczą do rozpoznania klasy dokumentu z nagłówkiem; LLM jest potrzebny do dokumentów bez nagłówka, ze skanu i do negatywów zbliżonych; hybryda (reguły, gdy pewne, inaczej LLM) łączy zalety.

## Metoda

- Zbiory: **dev_pdf** (147 pozytywów + 12 negatywów organizatora, tekst pdfium); **dev_headerless** (te same 147 pozytywów z usuniętymi linią tytułu i adresatem w pierwszych 12 liniach); **dev_ocr** (147, rapidocr 150 dpi, zestaw własny grupy B); **hard** (50 dokumentów szablonowych napisanych przeze mnie: 8 typów obcych po 5 sztuk: odpowiedź na odwołanie, przystąpienie, skarga na wyrok KIO, wyciąg bankowy, faktura, wezwanie do zapłaty, wezwanie KIO do wpisu, protokół rozprawy, oraz 2 typy graniczne po 5: pełnomocnictwo notarialne do innej sprawy i przelew odrzucony).
- Router widzi **wyłącznie tekst**; nazwa pliku nie jest wejściem. Część HTTP: 12 plików przez backend uprzęży (router regułowy uprzęży) pod losowymi nazwami heksadecymalnymi.
- Miara dwustronna: pozytyw odrzucony lub źle sklasyfikowany kosztuje **liczbę niepustych pól referencji** (kolumna „pola utracone”); negatyw sklasyfikowany jako klasa to FP dokumentu. `ambiguous`/`foreign` dla negatywu jest poprawne.
- Warianty: `harness_rules` (RulesRouter uprzęży, bez zmian), `rules_v2` (mój, rozszerzony o sygnały przeciwne), `llm_v1` (prompt ogólny: klasy + „foreign”), `llm_v2` (prompt z opisem klas i typów dokumentów podobnych), `hybrid_rules_first` (reguły v2, gdy decyzja „classified” bez flag przeciwnych; inaczej LLM v2), `hybrid_agree` (zgodność reguł i LLM, inaczej `ambiguous`).

## Wynik

Pozytywy poprawnie sklasyfikowane / pola utracone (negatywy organizatora: żaden nie dostał klasy; „FP” = negatyw sklasyfikowany jako klasa):

| Wariant | dev_pdf (147) | headerless (147) | OCR (147) | hard: FP na 40 obcych | LLM wołany |
|---|---|---|---|---|---|
| harness_rules | 131, utracone 135 | 35, utracone 1155 | 122, utracone 306 | **5** (wyciąg → przelew) | 0 |
| rules_v2 | 141, utracone 75 | 79, utracone 557 | 134, utracone 207 | 0 | 0 |
| llm_v1 (prompt ogólny) | 147, 0 | n/d | n/d | **23** (18 jako odwołanie, 5 jako przelew) | 159/159 |
| llm_v2 (prompt z opisem typów) | 147, 0 | 147, 0 | 147, 0 | 0 | 100% |
| hybrid_rules_first | 147, 0 | 147, 0 | 147, 0 | 0 | 18/159 (11%), 68/147 (46%), 13/147 (9%), 45/50 |
| hybrid_agree | 141, 75 | 79, 557 | 134, 207 | 0 | 100% |

Na 12 negatywach organizatora wszystkie warianty dają `foreign`/`ambiguous`; `llm_*` zwraca `ambiguous` (nie `foreign`) dla 3 decyzji/pism ministerstwa. Typy graniczne: pełnomocnictwo do innej sprawy → `power_of_attorney` we wszystkich wariantach z LLM (5/5); przelew odrzucony → `bank_transfer` (harness_rules, llm_v1), `ambiguous` (rules_v2), `foreign` (llm_v2).
HTTP: 12 plików z losowymi nazwami, wynik identyczny z odczytem lokalnym routera uprzęży (8 sklasyfikowanych poprawnie, 1 przelew `ambiguous`, 2 negatywy `foreign`, 1 negatyw-skan `technical_error/ocr_unavailable` bez OCR: z założenia); szczytowy RSS serwera 66–154 MB (pod obciążeniem maszyny, nie do decyzji).

## Jak to działa i dlaczego tak wyszło

Reguły opierają się na tytule, adresacie i słowach pól; tytuł (`ODWOŁANIE`, `PEŁNOMOCNICTWO`, `POLECENIE PRZELEWU`) niesie większość punktów, dlatego po jego usunięciu (headerless) trafność reguł spada do 54% (v2) lub 24% (uprząż). Przy `ambiguous` router nie wybiera klasy, więc dokument kosztuje wszystkie pola (miara dwustronna to pokazuje, FP negatywów tego nie widzi: router odrzucający wszystko miałby 0 FP). Ogólny prompt LLM (v1) ma **23/40 FP** na negatywach zbliżonych: odpowiedź na odwołanie i przystąpienie z nagłówkiem do KIO są dla modelu „odwołaniem”, bo zawierają te same słowa; model zawodzi tam, gdzie reguły (z tytułem) i tak by się pomyliły, tylko w innych miejscach. Prompt v2 usuwa te błędy, bo wymienia ich typy.

## Ograniczenia (ważne)

- **Zanieczyszczenie:** `hard_negatives.py`, flagi przeciwne w `rules_v2` i prompt `llm_v2` powstały po zobaczeniu tych samych typów dokumentów. Wyniki 0 FP dla `rules_v2`, `llm_v2` i hybryd na zbiorze **hard** nie są niezależnym dowodem; jedynym uczciwym wskaźnikiem odporności na nieznane typy jest `llm_v1` (23/40) i `harness_rules` (5/40). Test właściwy wymaga negatywów napisanych przez kogoś innego (np. prawdziwe odpowiedzi na odwołanie, wyroki KIO, ogłoszenia).
- Negatywy hard to szablony po 5 wariantów imion: efektywnie 10 niezależnych przypadków, nie 50. Negatywy organizatora: 12, z czego około 10 niezależnych (trzy kopie jednego OJS).
- Jedno wywołanie LLM na wariant, bez powtórzeń; zmiana aliasu modelu zmieni wynik. Prompt v2 strojony na dev.
- Dev_ocr to własny syntetyczny skan; skany organizatora (3 negatywy, szablon) bez OCR dają `technical_error`.
- Czasy LLM (suma opóźnień ok. 0,4–0,6 tys. s na 150 dokumentów, ok. 2,6–4,4 s/wywołanie) i RSS zebrano pod obciążeniem maszyny i współdzielonym kluczem (429 i ponowienia): **nie do decyzji**.

## Wniosek decyzyjny

Kryterium planu „brak fałszywych klasyfikacji negatywów” spełniają `rules_v2`, `llm_v2` i hybrydy, ale kryterium samo nie wystarcza (router „odrzuć wszystko”), a wynik jest zanieczyszczony. Wybór ostrożny: **hybryda rules_first z promptem LLM v2**, bo (a) nie traci żadnego pozytywu na tekście, bez nagłówka ani z OCR (147/147), (b) oszczędza wywołania tylko tam, gdzie reguły są pewne (89% wywołań zaoszczędzone na czystym PDF, 54% bez nagłówka, 91% na OCR), (c) ma 0 FP na negatywach organizatora i hard. Sam router regułowy jest niewystarczający dla dokumentów bez nagłówka (utrata 557 pól na 147) i dla skanów (207). Sam LLM v1 (bez opisu typów) nie nadaje się: 23/40 FP. Pewność: średnia co do kierunku, niska co do liczby FP na nieznanych typach. Otwarte: negatywy niezależne, powtórzenia LLM (wariancja), router w jednym wywołaniu z ekstrakcją (rekomendacja architektury), zachowanie `ambiguous` vs plik wyjściowy (E17).
