---
wersja: 0.1.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Plan weryfikacji UZP

Stan: aplikacja nie istnieje; wyników F1 jeszcze nie zmierzono.

1. Rozdziel dane według całych spraw, nie stron. Zachowaj grupowanie dokumentów.
2. Oddziel dane do rozwoju od nieużywanego wcześniej zbioru kontrolnego.
3. Sprawdź każdą klasę, skany i dokumenty negatywne.
4. Mierz klasyfikację, jakość pól, poprawność struktury, czas, koszt i pamięć.
5. Sprawdź batch input/output, nazwy i podfoldery oraz start bez GPU.
6. Dodaj klasę przez konfigurację i pokaż zakres potrzebnych zmian.
7. Odtwórz uruchomienie z czystej kopii bez pomocy autora.

Własne wyniki F1 opisuj z dokładną metodą normalizacji i zliczania. Nie nazywaj ich wynikiem oficjalnego ewaluatora, dopóki ten nie jest dostępny.

FAQ dopuszcza wgląd w materiały testowe na stoisku. Oznacz każdy obejrzany przypadek jako znany; nie używaj go do niezależnej oceny uogólniania.

Kontrola dokumentacji: `python3 scripts/verify_docs.py`. Jej wynik nie potwierdza jakości ekstrakcji.
