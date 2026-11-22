# E02: OCR na CPU (rapidocr + onnxruntime): dokładność, dpi, czas, pamięć

Polecenia (`.venv-exp`, z korzenia `experiments/2026-11-21-wybor-modulow`):

```sh
../../.venv-exp/bin/python odczyt/E02/e02_quality.py --config dpi100_cap2000 --config dpi150_cap2000 ...   # E02a, jakość → e02a-<config>.json (cache OCR poza Git)
../../.venv-exp/bin/python odczyt/E02/e02_timing.py                                                       # E02b, czas: p50/p95, ≥5 powtórzeń, zimny/ciepły, pod flock → e02b-czas.json
```

**Stan: E02a wykonane; E02b (czas do decyzji) NIE wykonane**: skrypt jest gotowy, ale na polecenie koordynatora pomiar czasu czeka na ciche okno (maszyna miała load avg 27–57 na 8 rdzeniach).

## Hipoteza i kryterium (plan 0.2)

OCR CPU mieści się w czasie i RAM (RSS < 4 GB) i jest dostatecznie dokładny; próg dokładności i czasu ustalany po pomiarze.

## Metoda E02a

Podzbiór: 12 spraw rozwojowych (ziarno 20261122) × 3 dokumenty = 36 skanów z zestawu (profile P1–P4), 92 strony. Strona renderowana do „dpi A4” (dłuższy bok = dpi × 11,69 cala; BLOKERY.md pkt 1),
`intra_op_num_threads` = 3, `inter_op` = 1, `Global.max_side_len` = 2000 (domyślny harnessu) albo 4000. Miara: odnajdywalność 359 niepustych, literalnych wartości referencyjnych w tekście OCR po normalizacji (exact; „fuzzy” = podobieństwo ≥ 0,8 dla tekstów ≥ 8 znaków).
Dodatkowo „CER” = odległość Levenshteina po `squash` między OCR czystej rasteryzacji pierwszej strony odwołań/przelewów (24 dok.) a warstwą tekstu. Nie jest to oficjalne F1.

## Wynik E02a (359 wartości; przedział Wilsona 95% dla ~0,97 ≈ ±0,018)

| Konfiguracja | exact | exact+fuzzy | CER mediana | szczyt RSS MB (proces) | s/stronę p50 / p95 (**pod obciążeniem, niewiążące**) |
|---|---|---|---|---|---|
| 100 dpi, cap 2000 | 348 (0,969) | 0,981 | 0,108 | 716 | 3,4 / 4,8 |
| 150 dpi, cap 2000 | 351 (0,978) | 0,986 | 0,089 | 773 | 13,7 / 24,5 |
| 200 dpi, cap 2000 | 347 (0,967) | 0,978 | 0,127 | 836 | 10,1 / 17,9 |
| 300 dpi, cap 2000 | 347 (0,967) | 0,983 | 0,107 | 905 | 4,7 / 7,2 |
| 200 dpi, cap 4000 | 341 (0,950) | 0,967 | 0,109 | 1069 | 16,6 / 32,4 |

Podział wg klasy: pełnomocnictwa ≈ 1,0, odwołania 0,976–0,981, przelewy 0,958–1,0. Chybienia (1–3 na 359 w konfiguracji) to identyfikatory (`numer_bzp`, `numer_ted`, `numer_postepowania`, rachunek, NIP) i długie tytuły; dokument `przyklad_12/odwolanie` chybia te same trzy pola przy 150 i 300 dpi (cecha obrazu, nie rozdzielczości).
Wyniki jakości do porównania dpi: **różnice 100–300 dpi mieszczą się w szumie próbki** (≤ 3 wartości z 359).

## Jak to działa i dlaczego tak wyszło

1. `max_side_len=2000` skaluje obraz tak, by dłuższy bok ≤ 2000 px (≈ 171 dpi A4). Dlatego 200 i 300 dpi z limitem 2000 to **ten sam obraz** wejściowy do detektora (różnice to szum/odtwarzalność i rozmiar renderu), a 150 dpi (1754 px) i 100 dpi (1169 px) nie są skalowane. „300 dpi” w konfiguracji bez zmiany limitu niczego nie daje; trzeba mówić o pikselach.
2. Konfiguracja z limitem 4000 (prawdziwe 200 dpi bez zmniejszania, 2339 px) jest **nie lepsza, a wolniejsza i droższa w pamięci** (1,07 GB, wynik 0,950): detektor działa najlepiej dla tekstu ok. 1200–2000 px, wyższa rozdzielczość daje rozbicie linii i dodatkowe fałszywe wykrycia. To jedna próbka (341 vs 347–351 z 359, w granicach szumu), więc nie jest dowodem szkodliwości.
3. Skany z szumem i JPEG ≈ jakość 30–92 nie psują odczytu cyfr: 96,7–97,8% wartości odnajduje się dokładnie. „CER” 0,09–0,13 jest zawyżony artefaktem: porównuje cały tekst strony z warstwą tekstu w innej kolejności czytania (kolumny, etykiety), więc nie jest czystą miarą błędu znaków; na poziom błędu znaków wskazuje raczej odnajdywalność.

## Czas i pamięć (niewiążące)

Czasy w tabeli zebrane pod obciążeniem (inne grupy; load avg 27–57; E02a bez flock, 3 wątki, 2–3 moje procesy równolegle): rozrzut 3,4–16,6 s/stronę nie odzwierciedla kosztu algorytmu (100 dpi 3,4 s vs 150 dpi 13,7 s odzwierciedla chwilowe obciążenie).
RSS: proces OCR 0,7–1,1 GB (jeden proces, `ru_maxrss`), czyli **mieści się w progu 4 GB** z zapasem ~4× (w tym ten pomiar jest wiążący co do rzędu wielkości, bo zależy od rozmiaru obrazu, a nie od obciążenia). Serwer uprzęży z OCR mierzy E00.
**Brak p50/p95 z ≥ 5 powtórzeń pod flock, zimnego/ciepłego startu i skanów organizatora (szablon 7 str., 3 skany negatywne):** E02b nie zostało uruchomione (powód wyżej). `e02_timing.py` (4 poziomy dpi, 5 powtórzeń, podproces na dpi, flock, szablon z referencją organizatora) czeka na ciche okno.

## Ograniczenia

- 36 dokumentów syntetycznych z jednego generatora (szum, JPEG, rozmycie); brak fizycznych skanów (poza wymienionymi w E02b); mała próbka: różnice < 1 pp to szum.
- Limit `max_side_len` i dpi są splątane (pkt 1): nie zmierzono dpi przy większym limicie poza jednym punktem (200/4000).
- Brak F1 na skanach w tym eksperymencie: patrz `F1/` (ekstraktor regułowy).
- Nie jest to oficjalne F1.

## Wniosek decyzyjny

Dokładność nie zależy mierzalnie od dpi w zakresie 100–300 dpi A4 (≥ 96,7% exact na wartościach literalnych; różnice w granicach próbki 359). **Rekomendacja robocza: 100–150 dpi A4 (dłuższy bok 1170–1750 px), `max_side_len` ≈ 2000, bez 300 dpi**; pewność średnia (mała próbka, jeden generator, czas niewiążący).
RSS < 4 GB: spełnione (≈ 0,7–1,1 GB na proces). Próg czasu: **otwarty do ciszy** (E02b). Otwarte: fizyczne skany, limit pikseli zamiast dpi w konfiguracji produktu, dwa/więcej procesów OCR równolegle (suma RSS).
