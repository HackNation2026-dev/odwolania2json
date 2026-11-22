# Prerejestracja (zapisana przed pomiarami; grupa C: E10, E11, E17, E18)

Data zapisu: 2026-11-22, przed pierwszym przebiegiem właściwym (pilot `E10/raw/pilot-text-p2` na 6 dokumentach istniał wcześniej i nie wchodzi do wyników).

## Dane i miara

- Zbiór rozwojowy, **podzbiór 25 z 49 spraw** (`subset_dev.json`, ziarno 20261122, warstwowo po długim odwołaniu ≥10 str.) = 75 dokumentów + 12 negatywów organizatora (tylko E10 tekst i E11 części „tekst”). Zbiór kontrolny nietknięty do ostatniego kroku.
- Miara: F1 przybliżony ewaluatora produkcyjnego (po PR #8/#9; `lib/score.py`): błędna wartość = FP, próg 80% dla pól tekstowych, miara `ratio`; rozrzut przy `token_sort_ratio` i `partial_ratio` raportowany. Przedział: bootstrap po sprawach (2000 losowań, ziarno 20261122), powtórzenia sumowane w obrębie sprawy. Nie jest to oficjalny F1.
- Sparowane porównanie: ΔF1 = wariant − baza na tych samych sprawach.

## Reguły rozstrzygające (przed zobaczeniem wyników)

1. Wariant zastępuje bazę, gdy dolna granica 95% przedziału ΔF1 > 0. Gdy przedział obejmuje 0: wygrywa tańszy (mniej tokenów, krótszy czas), potem prostszy. Brak minimalnej „istotnej” różnicy poza tą regułą; różnice < 1 pkt F1 na 25 sprawach nazywam szumem.
2. Baza E10: wejście `text` (tekst PDF), prompt `p2`, jedno wywołanie na dokument, temperatura 0, effort domyślny, model `MiniMax-M3.1-Flash-Preview`, jedno ponowienie przy odpowiedzi poza schematem.
3. E10 stabilność: 5 powtórzeń (warianty przesiewowe promptu p1/p3 i effort: 3 powtórzenia, jawnie oznaczone jako mniej wiarygodne).
4. E11: warianty A (tekst PDF + LLM), A+regex (regex nadpisuje przy rozbieżności pól o stałym formacie), B (A + OCR rapidocr 200 dpi, `if_needed`), C (same obrazy), D (tekst + obraz strony), dolna granica „sam regex” (router regułowy + ekstraktor regułowy). Ablacje jednego modułu na odtworzonych odpowiedziach LLM (replay, ta sama odpowiedź modelu). Wynik osobno dla typu wejścia: tekst, skan, mieszany, S2, S5.
5. E17: polityki liczone offline z zapisanych odpowiedzi (bez nowych wywołań), z regułą: polityka „odwrotna do architektury” zastępuje domyślną, gdy ΔF1 sparowane ma dolną granicę > 0.
6. E18: model/ustawienie zastępuje MiniMax-M3.1-Flash-Preview, gdy dolna granica ΔF1 (model − baza) > −0,02 (strata do 2 pkt F1 dopuszczalna dla mniejszego/tańszego modelu), a koszt tokenów i czas nie są większe; w przeciwnym razie zostaje baza. Modele: warianty MiniMax dostępne na tym samym kluczu (inny dostawca: patrz E18/README, tylko klucz MiniMax jest w zakresie zlecenia).
7. Wynik końcowy na zbiorze kontrolnym: jeden przebieg jednego wariantu wybranego po E11 (zapis wyboru w pliku `WYBOR.md` przed przebiegiem; licznik użyć w `KONTROLNY.md`).
