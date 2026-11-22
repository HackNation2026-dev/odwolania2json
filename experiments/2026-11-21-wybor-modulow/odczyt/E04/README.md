# E04: diagnoza stron (tekst / skan / mieszana) i koszt po obu stronach

Polecenie (bez OCR, ok. 1 min): `../../.venv-exp/bin/python odczyt/E04/e04_diagnosis.py` z korzenia `experiments/2026-11-21-wybor-modulow` → `e04a-diagnoza.json` (agregaty), `e04a-strony.json` (1357 stron, rekord na stronę).

## Hipoteza i kryterium (plan 0.2)

Diagnoza strony (`reading.diagnose_page`: liczba słów warstwy tekstowej i pokrycie obrazami) odróżnia tekst od skanu i oszczędza OCR.
Kryterium: **zero stron skanu oznaczonych jako tekst**; koszt drugiej strony (strony tekstowe wysłane do OCR) raportowany osobno.

## Metoda

Prawda strony wynika z konstrukcji zestawu (manifest) albo z oceny materiałów organizatora (które z 3 skanów negatywnych to skan: z obrazu na całej stronie i zerowej liczby słów).
1357 stron: 339 oryginalnych stron tekstowych (147 dok. rozwojowych), 339 skanów (`skan`), 240 stron `mieszany` (strona 1 tekst, reszta skan), 200 stron skanów obróconych (3×50) i przekrzywionych (50),
49 stron `s2` (dane przelewu tylko w obrazie na stronie z tekstem), 50 stron `s5` (poprawny obraz + niewidoczna warstwa z błędnymi cyframi), 124 strony 12 negatywów organizatora, 7 stron skanu szablonu, 9 stron negatywu szablonu.
Wariant v2 = v1 + sygnał „niewidoczny tekst” (tryb renderowania 3 ≥ 50% obiektów tekstowych).

## Wynik

| Miara | v1 (harness) | v2 (+ niewidoczny tekst) |
|---|---|---|
| strony skanopodobne (skan, mieszane-skan, s2, s5, obroty, skos, szablon, skany negatywów) | 843 | 843 |
| **skan oznaczony jako tekst (musi być 0)** | **0** | **0** (górna granica 95%, reguła „3/n”: 0,36%) |
| strony tekstowe | 514 | 514 |
| strony tekstowe wysłane do OCR (koszt) | 1 (0,19%) | 1 |
| udział stron wysyłanych do OCR (ogółem) | 62,2% | 62,2% |
| oszczędność na dokumentach `mieszany` | 49 z 240 stron (strona 1) bez OCR; 191 do OCR | to samo |

Jedyny fałszywy alarm: strona 15 broszury JPK_FA (negatyw organizatora) ma 16 słów i obraz na 51% strony: kod `mixed_page`, wysłana do OCR bez potrzeby (koszt czasu, nie błędu).
Dokumenty `s2` (49 stron) i `s5` (50 stron) są wysyłane do OCR w całości (v1 oznacza je `mixed_page`/`scan`, bo obraz zajmuje ≈ 80% strony (`s2`) lub 100% (`s5`)).

## Jak to działa i dlaczego tak wyszło

Reguła v1: strona z ≥ 1 słowem i pokryciem obrazem < 50% = tekst; brak słów i pokrycie ≥ 50% = skan; słowa + pokrycie ≥ 50% = strona mieszana, **oznaczana jako wymagająca OCR**.
Skanów nie przepuszcza się, bo skan to obraz na całej stronie (pokrycie 0,998–1,0) i brak słów; fałszywe „tekst” wymagałoby warstwy tekstowej pod skanem z pokryciem < 50%.
Sygnał niewidocznego tekstu (v2) niczego nie zmienia na tym zbiorze, bo strony z niewidoczną warstwą (`s5`) mają i tak pokrycie 1,0, więc v1 już wysyła je do OCR: v2 jest zabezpieczeniem na przypadek skanu z warstwą OCR pokrywającą tylko część strony.

## Ograniczenia

- Dane syntetyczne i z jednego generatora: strony tekstowe nie mają dużych obrazów (logo, tła), więc koszt „tekst wysłany do OCR” jest niedoszacowany; jedyny fałszywy alarm pochodzi z cudzego dokumentu (broszura).
- Brak przypadku „skan z warstwą OCR pokrywającą 30% strony” i „strona z dużym tłem-obrazem i prawdziwym tekstem”: próg 0,5 pokrycia nie został zmierzony wokół wartości granicznych.
- Dla `s5` (zła warstwa) diagnoza wysyła stronę do OCR, ale **to pipeline** musi wtedy odrzucić warstwę tekstową: strona `mixed` nadal ma słowa `pdf` z błędnymi cyframi obok słów OCR; skutek zmierzono w `F1/README.md` (S5: 0 TP, 20 FP, wynik `complete`), a przyczynę opisuje BLOKERY.md pkt 6.
- Prawda dla negatywów organizatora to ocena ręczna (3 skany, reszta tekst); to nie jest etykietowanie przez dwóch recenzentów.

## Wniosek decyzyjny

Kryterium „zero stron skanu jako tekst”: **spełnione** (0 z 843, górna granica ≈ 0,4%). Diagnoza jest tania (bez OCR, ≈ 1 min na 1357 stron) i oszczędza OCR: 37,8% stron nie idzie do OCR, w tym 49 stron 1 odwołań-mieszanych.
Zostaje v1 (progi 1 słowo, pokrycie 0,5) z dopisaniem v2 (niewidoczny tekst) jako tanim zabezpieczeniem; pewność: wysoka dla zbioru syntetycznego, średnia dla dokumentów spoza generatora. Otwarte: próg wokół 0,5 pokrycia, strony z częściową warstwą OCR, polityka dla `s5`.
