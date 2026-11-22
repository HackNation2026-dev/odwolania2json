# Profile skanów wyznaczone z materiałów organizatora

Pomiar: 3 skany negatywne z obrazem (`dane/negatywne`) i skan szablonu (`szablon-aplikacja/input/case1/przyklad odwolanie.pdf`), strony 1 i ostatnia.
Skrypt pomiarowy był jednorazowy (pypdf + numpy); wartości poniżej to surowe liczby.

| Źródło | Piksele | Kolor | Filtr, tablica kwantyzacji q0[0..3] | Szum tła (σ, strona z tekstem / pusta) | Kąt | Deklarowane |
|---|---|---|---|---|---|---|
| szablon (7 str.) | 1654×2339 (200 dpi) | RGB | DCT, 3 2 2 3 (≈ jakość 92) | 1,48 / 0,51 | −0,1° | MediaBox 1240,5×1754 pt (96 dpi!) |
| bizhub 223 (4 str.) | 1653×2338 | szary | DCT, 5 5 6 8 | 2,14 / 0,34 | 0,2–0,6° | 595×842 pt |
| Decyzja Min. Sportu (1 str.) | 1654×2337 | RGB | DCT, 8 6 5 8 | 2,74 | 0,1° | tło 251, bez metadanych |
| pismo Min. Sprawiedliwości (2 str.) | 3507×2480 (300 dpi, poziomo) | szary | DCT, 26 18 16 26 (≈ jakość 31) | 2,68–2,84 | −0,7°/0° | /Rotate 270 |

Wniosek: kanał to 200 dpi (jeden 300 dpi), JPEG w jednym przejściu, jakość od ok. 30 do 92, kąt do 0,7°, szum tła σ 0,3–2,8 (przy braku binaryzacji). Szablon deklaruje 96 dpi
mimo 200 dpi obrazu (strona 1240 pt zamiast 595 pt): to odtwarza P1 i jest pułapką dla geometrii (pt vs px).

Profile generatora (`build_zestaw.py: PROFILES`): P1-szablon, P2-ksero-szare, P3-ksero-rgb (z zagięciami), P4-300-szare.
Zmierzony w wyniku (te same obliczenia na stronie 1, maska jasnych pikseli): σ 2,9–3,8, czyli nieco powyżej organizatora (ta miara wlicza krawędzie tekstu; porównanie przybliżone).
Kąt (±0,3 do ±0,7°) i tablice kwantyzacji zgadzają się z pomiarem (P1: 3 2 2 3; P2: 5 3 3 5; P3: 7 5 5 7; P4: 26 18 16 26). Nie ma odtworzenia /Rotate 270 w profilu
głównym (jest wariant `obrot*` z obrazem obróconym fizycznie, oraz osobny test E01 narożników po `/Rotate`).
