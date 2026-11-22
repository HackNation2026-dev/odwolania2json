# E03: preprocessing skanów (wykrycie obrotu 0/90/180/270, deskew, binaryzacja Otsu)

Polecenie (z korzenia `experiments/2026-11-21-wybor-modulow`; 97 odwołań, ok. 2 h pod obciążeniem, 2 wątki onnxruntime): `../../.venv-exp/bin/python odczyt/E03/e03_preproc.py --threads 2` → `e03-wyniki.json`. (`e03.log` bywa uszkodzony: dwa przebiegi pisały do jednego pliku; liczą się tylko JSON.)

## Hipoteza, kryterium i reguła (ustalona przed pomiarem)

Preprocessing poprawia OCR na tyle, by był wart kosztu. Plan: przyrost ≥ 10% wart kosztu czasu. Reguła zapisana w skrypcie: krok przyjęty, gdy **dolna granica 95% przedziału bootstrapu po sprawach** różnicy odnajdywalności (metoda − brak) jest > 0 i dodatkowy czas ≤ 1× czas OCR strony.

## Metoda

Odwołania, strona 1, 150 dpi A4, `max_side_len` 2000. Zbiory: `skan` (49 spraw), `obrot90/180/270` (12 spraw, obraz obrócony fizycznie), `skos3` (12 spraw, kąt 3°). Metody: brak, `rot` (wykrywacz obrotu), `deskew`, `rot+deskew`, `rot+deskew+otsu`, `otsu`.
Miara: odnajdywalność wartości, które istnieją w warstwie tekstu strony 1 oryginału (stały mianownik). Wykrywacz obrotu: detektor na miniaturze 1000 px (kierunek wierszy), potem OCR dwóch kandydatów orientacji i wybór wyższej sumy pewność × liczba znaków. Deskew: profil rzutu poziomego, krok 0,1°.

## Wynik (średnia odnajdywalność [95% bootstrap po sprawach]; Δ względem „brak”)

| Zbiór | brak | `rot` | Δ `rot` | `deskew` Δ | `otsu` Δ | `rot+deskew+otsu` Δ |
|---|---|---|---|---|---|---|
| skan (49) | 0,977 [0,964–0,989] | 0,977 | 0,000 [0,000–0,000] | −0,011 [−0,024…0,001] | −0,033 [−0,058…−0,013] | −0,054 [−0,079…−0,031] |
| obrót 90 (12) | 0,509 [0,423–0,597] | 0,970 | **+0,461 [0,371–0,556]** | +0,165 | +0,137 | +0,417 |
| obrót 180 (12) | 0,678 [0,612–0,744] | 0,975 | **+0,297 [0,231–0,368]** | +0,030 [−0,017…0,081] | −0,054 | +0,257 |
| obrót 270 (12) | 0,940 [0,910–0,966] | 0,962 | +0,021 [−0,021…0,059] | −0,015 | −0,041 | −0,025 |
| skos 3° (12) | 0,964 [0,938–0,990] | 0,964 | 0,000 | −0,005 [−0,044…0,032] | +0,011 [−0,025…0,042] | −0,033 |

Wykrywanie obrotu: 49/49 poprawnie na skanach prostych (brak fałszywych obrotów), 12/12 dla 180° i 3°; dla 90°/270° wybór jest odwrotny do etykiety zbioru (zwraca 270 dla `obrot90` i 90 dla `obrot270`), bo `PIL.rotate` obraca przeciwnie do ruchu wskazówek, a zbiór obracano zgodnie z nimi; **to różnica konwencji, nie błąd**: po zastosowaniu zwróconego kąta odnajdywalność rośnie do 0,97 (tabela). Kąt skosu: estymata ±0,7° dla skanów prostych (zgodnie z profilem organizatora) i −3,0° dla skosu 3° (poprawne).
Koszt (niewiążący: load avg 20–40, 2 wątki): OCR strony 5–7 s (skan prosty), wykrywacz obrotu 14,7 s/stronę (≈ 2× czas OCR: miniatura + dwa OCR-y kandydatów), estymacja skosu 0,06 s, deskew 0,1–0,45 s, Otsu 0,01 s. Szczyt RSS procesu 816 MB.

## Jak to działa i dlaczego tak wyszło

- Obrót 90° i 180° niszczy OCR (51% i 68% odnajdywalności), więc wykrywacz daje gigantyczny zysk tam, gdzie jest potrzebny. **Obrót 270° (zgodny z ruchem wskazówek) rapidocr znosi sam** (94%): klasyfikator linii obraca pionowe pola tekstu w jednym kierunku, w drugim nie; stąd asymetria 90 vs 270.
- Na prostych skanach wykrywacz niczego nie zmienia (brak fałszywych alarmów), ale kosztuje ok. 2× OCR: **nie spełnia reguły czasu (≤ 1× OCR strony) w obecnej postaci**, choć spełnia regułę przyrostu tam, gdzie są obrócone strony.
- Deskew nie pomaga: rapidocr toleruje skos do 3° i szum z profili (0,7°); estymata jest poprawna, ale korekta interpolacją pogarsza ostrość (Δ −0,011, granica górna 0,001).
- Binaryzacja Otsu **szkodzi** na skanach (−0,033, przedział poniżej zera): przy szumie i JPEG ucina cienkie znaki i cyfry; model OCR radzi sobie lepiej ze skalą szarości.

## Ograniczenia

12 spraw na zbiór obrotów (przedziały szerokie), jedna strona na dokument, jeden generator; obrót jest idealny (±90/180°), brak obrotów o kąty pośrednie ani zdjęć. Reguły deskew nie sprawdzono dla skosu > 3° (tu nie ma danych). Czasy niewiążące. Tańszy wyzwalacz wykrywania (np. uruchamiaj tylko, gdy pierwszy OCR ma niską pewność lub mało słów) nie był testowany. Nie jest to oficjalne F1.

## Wniosek decyzyjny

1. **Wykrywanie obrotu: przyjąć, ale tanio** (wyzwalane, nie dla każdej strony; w obecnej postaci 2× OCR przekracza regułę kosztu). Zysk +0,30…+0,46 na stronach obróconych jest oczywisty (granica dolna > 0,23), a skany proste nie tracą.
2. **Deskew: odrzucić** (brak zysku, przedział Δ obejmuje 0 lub jest ujemny). 3. **Binaryzacja Otsu: odrzucić** (−3,3 pp, szkodliwa). Pewność: średnia-wysoka (12 spraw na obrót, wyraźne efekty); otwarte: koszt tańszego wyzwalacza obrotu, skosy > 3°, zdjęcia z perspektywą.
