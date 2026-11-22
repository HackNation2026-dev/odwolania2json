---
wersja: 0.2.0
aktualizacja: 2026-11-22
status: plan weryfikacji i sprawdzenie etapu 1
---

# Plan weryfikacji UZP

Stan etapu 1 (2026-11-22). Czysta instalacja `pip install -r requirements.txt` na macOS arm64 z Pythonem 3.13 przeszła. Zainstalowany `process` zakończył wsad 196 PDF-ów organizatora kodem `0` z lokalną atrapą LLM. Powstało 196 plików JSON z zachowaniem nazw i podkatalogów oraz 196 wpisów w `report.jsonl`. Osobna próba potwierdziła zapis pola przelewu poza katalogiem repozytorium.

Pierwszy przebieg sprawdzał dostarczenie, odczyt i zapis. Atrapa dla pełnego wsadu zwracała klasę obcą. W drugim przebiegu, z odpowiedziami LLM wypełnionymi z referencji, wszystkie 196 plików przeszło walidację schematów. Wyniki odtworzyły wartości referencyjne dla 180 dokumentów ocenianych, a 16 negatywnych dało `{}`. Cztery pliki ujemne są kopiami tych z katalogu `negatywne` i liczą się jako osobne ścieżki w próbie uruchomienia.

Próbne rozwiązanie zależności pip zakończyło się powodzeniem dla Pythona 3.13 na Linux i Windows x86-64. Rzeczywiste uruchomienie wykonano na macOS arm64. Pomiar F1 aktualnego produktu z MiniMaxem pozostaje do wykonania. Instrukcja jest w [README](../../README.md#próba-pomiaru-minimax).

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

## Uzupełnienie organizatora

[Zasady F1](zasady-f1.md) zapisują próg 80%, pola długiego tekstu i dopasowanie list po treści. Dane referencyjne to JSON-y 60 spraw; ground_truth.yaml usunięto. Testy są syntetyczne. Brak skanów w przykładach nie rozstrzyga ukrytego testu. Testuj publiczny endpoint z innej sieci; nie zakładaj lokalnej instalacji modelu u jury.

## Uzupełnienie 0.5.0 (2026-11-21)

- [Eksperyment: czy YAML wystarcza do opisu klasy](eksperyment-yaml-klasy-2026-11-21.md) — 60/60 spraw, 4528/4528 mutantów zabitych, granice podejścia.
- [Eksperyment: typy plików i przypadki brzegowe](eksperyment-przypadki-brzegowe-2026-11-21.md) — inwentarz 206 PDF-ów, syntetyczne skany, Codex/Claude/MiniMax, przeglądarka egui.
- [Katalog przypadków brzegowych](katalog-przypadkow-brzegowych.md) — wiedza zespołu, mentor, konsultacje, dane; co trzeba wygenerować.
