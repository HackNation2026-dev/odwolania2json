---
wersja: 0.6.1
aktualizacja: 2026-11-22
status: przyjęta interpretacja zespołu, do potwierdzenia z mentorem (U-Q01, U-Q02)
---

# ADR-005: interpretacja F1 w ewaluatorze zespołu

## Kontekst

Organizator podał definicję TP/TN/FP/FN, próg 80% dla pięciu pól tekstowych i zasadę dopasowania list po treści ([zasady F1](../05-weryfikacja/zasady-f1.md)). Nie podał algorytmu podobieństwa, normalizacji, agregacji ani łączenia elementów list ([pytania otwarte](pytania-otwarte.md), U-Q01 i U-Q02). Ewaluator zespołu jest więc przybliżeniem, a nie kopią oficjalnego.

## Decyzja

1. **Błędna obecna wartość to wyłącznie FP**, bez dodatkowego FN (komunikat 11:26; [architektura §11](../04-architektura/architektura-wewnetrzna.md)). Wariant „FP + FN” zostaje w kodzie jako `EvalConfig(wrong_value="fp_fn")`, tylko do porównania wyników; nie jest domyślny.
2. **Próg podobieństwa 0,8, włącznie** (`podobieństwo ≥ 0,8` to zgodność, TP) dotyczy pięciu pól rozpoznawanych po kluczach referencyjnych JSON, z `[]` w miejscu indeksu listy: `Odwolujacy[].pelnomocnik.nazwa`, `przelew_bankowy.tytul`, `Odwolujacy[].nazwa`, `Zamawiajacy[].nazwa`, `ZamowieniePubliczne.tytul`. Lista jest w jednym miejscu: `SIMILARITY_FIELD_PATHS` w `similarity.py`. Pozostałe pola (daty, identyfikatory, `mocodawca[].data.nazwa` itd.) wymagają dokładnej równości, bez normalizacji, bo zasady jej nie opisują.
3. **Algorytm podobieństwa jest wymienny** (rapidfuzz): `ratio` (domyślny), `token_sort_ratio`, `partial_ratio`. `evaluate_variants` liczy raport dla każdego wariantu, aby pokazać rozrzut F1 wynikający z tej niewiadomej.
4. **Listy**: element do elementu po przypisaniu o maksymalnej sumie wag (algorytm węgierski). Waga pary to `2·TP − FP − FN` pól pary plus liczba niepustych liści obu elementów (tyle kosztowałoby pozostawienie ich bez pary). Pola w sparowanym elemencie są oceniane osobno, z progiem tam, gdzie dotyczy. Kolejność nie ma znaczenia. Element tylko w wyniku to FP wszystkich niepustych pól, tylko w referencji to FN. Remisy: premia za bliskość indeksów, potem kolejność algorytmu; wynik jest deterministyczny. W ścieżce indeks to pozycja w referencji, a elementy nadmiarowe wyniku dostają kolejne indeksy za jej końcem.
5. **Zmiana typu lub struktury** (np. obiekt zamiast tekstu, liczba zamiast `bool`) to jedna błędna wartość: FP na ścieżce.

## Konsekwencje

- Sparowany element z samymi błędnymi wartościami daje tylko FP (bez FN), zgodnie z pkt 1. Przy wariancie `fp_fn` ta sama sytuacja daje FP i FN. Pełne przypisanie zakłada, że para zawsze wygrywa z pozostawieniem obu elementów bez pary; różnicę zobaczy raport wariantów.
- Wynik zależy od niezależnych niewiadomych: wariantu podobieństwa i reguły błędnej wartości. Raportując F1, podajemy obie. Przy ocenie decyzji (eksperymenty E10/E11) liczymy przedział bootstrapem po sprawach, nie po polach (`bootstrap.py`), oraz ΔF1 sparowane.
- Gdy mentor poda algorytm lub regułę, zmieniamy domyślne wartości `EvalConfig` i ten ADR; interfejs się nie zmienia.
