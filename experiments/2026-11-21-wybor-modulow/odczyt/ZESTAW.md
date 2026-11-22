# Zestaw skanów z referencją pól (grupa A)

Cel (plan 0.2, P0 pkt 3): skany o znanej referencji pól, żeby mierzyć F1 pól i odnajdywalność wartości na wejściu bez warstwy tekstu.
**Wszystko pochodzi wyłącznie ze 49 spraw rozwojowych** (147 dokumentów z `data/podzial.json`, strona „rozwojowy”). Spraw kontrolnych nie ma.

## Gdzie i jak użyć (grupy B, C, D)

- Ścieżka: `experiments/2026-11-21-wybor-modulow/odczyt/zestaw/` (pliki w `data/`, **poza Git** wg `odczyt/.gitignore`; odtwarzalne).
- Odtworzenie (ok. 2,5 min, 3 procesy, deterministyczne): `.venv-exp/bin/python odczyt/zestaw/build_zestaw.py --jobs 3`.
- Manifest: `zestaw/manifest.json` (342 wpisy: id, wariant, profil, sprawa, `parent_split`, ziarno, SHA-256 źródła i wyniku, ścieżka PDF i referencji).
- Loader z wbudowaną blokadą przecieku:
  ```python
  sys.path.insert(0, ".../odczyt/zestaw"); from api import load_zestaw
  items = load_zestaw(["skan"])      # ScanItem: .pdf, .reference(), .profile, .document_class, .input_kind
  ```
- Referencja (`ref/<sprawa>/<dokument>.json`) = referencja organizatora z jego poprawkami (przez `harness/data.reference_for`), dziedziczona z oryginału.

## Zawartość

| Wariant | Liczba | Opis |
|---|---|---|
| `skan` | 147 | wszystkie dokumenty rozwojowe jako skan bez warstwy tekstu; profil przypisany z hasha: P1 58, P2 42, P3 30, P4 17 |
| `mieszany` | 49 | odwołania: strona 1 tekstowa, reszta skan (P2) |
| `s2` | 49 | przelewy: dolna część strony 1 (od mediany wysokości tekstu) zastąpiona obrazem, usunięty tekst pod nią; dane tylko w obrazie na stronie tekstowej |
| `s5` | 49 | pełnomocnictwa: poprawny obraz strony + niewidoczna (tryb 3 Tr) warstwa z cyframi zmienionymi (+3 mod 10) i bez diakrytyków, w pozycjach prawdziwych słów |
| `obrot90/180/270` | 3×12 | odwołania 12 spraw (co 4. sprawa): obraz obrócony fizycznie (stres E03) |
| `skos3` | 12 | te same odwołania, przekrzywione o 3° (poza profilem organizatora, stres) |

Wyprowadzenie profili: plik `zestaw/PROFIL.md` nie został utworzony — `zestaw/manifest.json` zawiera profil każdego wpisu (`profil`), a definicje profili opisują wiersze tabeli powyżej. Odwołania liczą 240 stron, pełnomocnictwa 50, przelewy 49 (339 stron na pełny przebieg `skan`).

## Test blokujący

`zestaw/test_zestaw.py` (9 testów, zielone): sprawy kontrolne (w tym `przyklad_40`) i spoza podziału rzucają `LeakError`; manifest ze sprawą kontrolną
lub złym `parent_split` jest odrzucany; `build_one` odmawia sprawy kontrolnej; zadania budowy nie zawierają spraw kontrolnych; SHA plików zgadza się z manifestem;
przebudowa jest bajt w bajt powtarzalna. Uruchomienie: `.venv-exp/bin/python -m pytest -c /dev/null --rootdir=odczyt/zestaw odczyt/zestaw/test_zestaw.py`.

## Ograniczenia

Skany są syntetyczne (rasteryzacja + szum, rozmycie, kąt, JPEG, zagięcia); nie odtwarzają rastra drukarki, prześwitu, perspektywy zdjęcia, pieczęci.
Fizyczne skany ~10 spraw (walidacja generatora) pozostają do wykonania ręcznie. Wszystkie dokumenty pochodzą z jednego generatora szablonów.
