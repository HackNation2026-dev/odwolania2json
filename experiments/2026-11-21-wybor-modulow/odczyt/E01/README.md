# E01: czytnik warstwy tekstowej PDF i geometria

Polecenia (powtarzalne; `.venv-exp`, z katalogu `odczyt/`; drugi czytnik instalowany izolowanie: `uv pip install --target vendor pdfminer.six pymupdf`):

```sh
../../.venv-exp/bin/python odczyt/E01/e01_readers.py     # E01a, pod flock, ok. 3 min   → e01a-czytniki.json
../../.venv-exp/bin/python odczyt/E01/e01_geometry.py    # E01b                         → e01b-geometria.json
```

## Hipoteza i kryterium (plan 0.2)

Warstwa tekstowa (pypdfium2) wystarcza dla dokumentów elektronicznych: odnajdywalność wartości referencyjnych po normalizacji ≥ 0,99; bbox poprawne po `/Rotate`.
Miara nie jest CER ani „pokryciem słów” (brak referencji słów): to odsetek niepustych liści referencji, których wartość daje się znaleźć w tekście odczytu
(NIP/KRS/REGON/rachunek: same cyfry; kwota: formy `200,00`/`200.00`/`200`; data: `dd.mm.rrrr`, ISO, „20 marca 2026”; `numer_ted`: części liczbowe, bo tekst ma format `2026/S086-999073`; tekst: po zdjęciu diakrytyków i znaków nie-alfanumerycznych; „fuzzy” = podobieństwo ≥ 0,8 dla długich tekstów).
Pominięte jako nielteralne: kody (`czynnosc_powod_id`, `przez-pelnomocnika`, `typ`) i `czynnosc_opis` (opis interpretacyjny, nie występuje dosłownie, 3/49 trafień literalnych; to zadanie E09).

## Wynik E01a: czytniki (147 dokumentów rozwojowych, 1454 wartości; 5 powtórzeń; zimny start = pierwszy odczyt w nowym procesie)

| Czytnik | Odnajdywalność (exact) | s/dok. p50 | p95 | zimny 1. dok. | szczyt RSS MB | Licencja |
|---|---|---|---|---|---|---|
| pypdfium2 (czytnik uprzęży: słowa z bbox, pętla Pythona po znakach) | 1454/1454 = 1,000 | 0,0049 | 0,076 | 0,017 s | 51 | BSD/Apache |
| pypdf 7.1.1 (sam tekst) | 1,000 | 0,0108 | 0,058 | 0,144 s | 69 | BSD-3 |
| pdfminer.six 20260107 (sam tekst) | 1,000 | 0,0213 | 0,227 | 0,268 s | 65 | MIT |
| PyMuPDF 2.1 (sam tekst) | 1,000 | 0,0016 | 0,016 | 0,624 s | 183 | **AGPL-3.0**/komercyjna |

Pełen przebieg 147 dokumentów (mediana na dokument, suma): pdfium 1,9 s, pypdf 2,5 s, pdfminer 6,7 s, PyMuPDF 0,44 s. Wątki: czytniki jednowątkowe. Czas pdfium obejmuje obliczanie bbox słów (inne czytniki zwracają tylko tekst), więc porównanie czasu jest zaniżone na korzyść pozostałych. RSS = `ru_maxrss` procesu pomiarowego (przy 147 dok., nie drzewa procesów); pomiar uruchamiany obok innych zadań grup, choć pod `flock` (inne grupy mogły obciążać CPU).

## Wynik E01b: geometria (12 losowych dokumentów, 2 strony, obrót wymuszony przez `set_rotation`, ziarno 20261122)

| `/Rotate` | słów porównanych | IoU min | IoU średnie | udział IoU ≥ 0,95 | test obiegowy tuszu (próba 1138 słów) | wymiary strony |
|---|---|---|---|---|---|---|
| 0 | 4370 | 1,000 | 1,000 | 1,000 | 99,2% | zgodne |
| 90 | 4370 | 0,998 | 1,000 | 1,000 | 99,0% | zgodne |
| 180 | 4367 (3 bez pary tekstowej) | 0,977 | 0,999 | 1,000 | 99,4% | zgodne |
| 270 | 4370 | 0,979 | 1,000 | 1,000 | 98,8% | zgodne |

IoU liczone wobec ręcznie wyprowadzonej transformacji narożników (CW 90/180/270) słów z strony nieobróconej; test obiegowy: render pdfium (skala 2), ≥ 3% ciemnych pikseli w bbox i ≥ 70% tuszu z paska wokół bbox leży w bbox
(to nie jest OCR wyciętego bboxa: ślad tuszu). Uwaga o pomyłce w trakcie: pierwsza wersja testu dawała 45% dla 90°/270° z powodu paska liczonego od wysokości słowa (słowa pionowe); to był błąd testu, nie czytnika.

Kolejność czytania na przelewach (98 par numer rachunku → najbliższa poprzedzająca etykieta nadawca/odbiorca; 3 układy: ramki w dwóch kolumnach 14, jedna kolumna 72, lista kropkowana 12):
pdfium, pypdf, PyMuPDF: 98/98 poprawnie; pdfminer.six: 92/98 (6 odwróconych w układach jedno- i dwukolumnowych).

## Jak to działa i dlaczego tak wyszło

pdfium daje tekst i `get_charbox` na znak; uprząż skleja znaki w słowa i przelicza bbox na układ po `/Rotate` (macierz `display_mapping`), więc obrót nie psuje geometrii: wynik pokrywa się z niezależną transformacją i ze śladem tuszu.
Wszystkie czytniki mają 100% odnajdywalności, bo zbiór to czysty tekst z jednego generatora szablonów: test nie rozróżnia czytników po treści, tylko po czasie, pamięci, licencji i kolejności czytania. Jedyny rozróżniający sygnał jakości to kolejność czytania pdfminer.

## Ograniczenia

- Czasy z E01a zebrane pod flock, ale przy obciążeniu maszyny innymi grupami (load avg 20–40): niewiążące do decyzji; rząd wielkości i kolejność czytników (PyMuPDF < pypdf < pdfium < pdfminer) są wiarygodne, wartości bezwzględne nie.

- Dokumenty elektroniczne z jednego generatora: 100% nie dowodzi odporności na PDF-y z innych źródeł (kolumny, tabele, czcionki bez ToUnicode). Nie ma w zbiorze rozwojowym PDF-ów z uszkodzonym mapowaniem znaków.
- Układy przelewów: we wszystkich etykieta poprzedza wartość, więc test kolejności jest łatwy; układ wartość-przed-etykietą nie występuje w danych.
- `/Rotate` to rotacja wymuszona sztucznie na dokumentach bez własnego `/Rotate`; strona z natywnym obrotem i niestandardowym MediaBox (np. początek ≠ 0,0) nie jest pokryta.
- Czas pdfium zawyżony względem „samego tekstu” (liczy bbox). Pomiar czasu mógł być zaburzony pracą innych grup mimo `flock`.
- Nie jest to oficjalne F1.

## Wniosek decyzyjny

Kryterium ≥ 0,99: spełnione (1,000, 1454/1454) dla pypdfium2 i bez rozróżnienia względem trzech innych czytników. **Zostaje pypdfium2**: ten sam silnik daje tekst, bbox i render, geometria po `/Rotate` zweryfikowana, licencja liberalna, 51 MB RSS, 0,005 s/dokument.
PyMuPDF jest najszybszy, ale AGPL-3.0 wyklucza go bez zgody na licencję komercyjną; pdfminer.six odpada (wolniejszy 4×, gorsza kolejność czytania). Pewność: wysoka dla czystych PDF-ów z tego generatora, średnia dla PDF-ów spoza niego (niezmierzone). Otwarte: PDF-y z natywnym `/Rotate` i nietypowym MediaBox, tabele wielokolumnowe.
