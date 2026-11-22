# E20: obecność pola i luki grupy C

Skrypt: `../e07_e09_e20.py` (po `../run_extraction.py`), luki: `../gaps.py`, surowe liczby `wyniki.json`.
Miara: (1) FP na polach z referencją `null` na 147 dokumentach rozwojowych; (2) cztery rodzaje luk jako edycje tekstu prawdziwych dokumentów rozwojowych (po 8 dokumentów, **małe próby**), referencja wyprowadzona z oryginału.

## Hipoteza

Zwracanie wartości tam, gdzie pola nie ma, jest rzadkie, a luki (brak pełnomocnika, powód 12, brak BZP/TED, wpis zamiast opłaty skarbowej) nie psują wyniku.

## Wynik

FP na polach z referencją `null` (dev: 240–243 pola o referencji `null`):

| Wariant | FP na `null` | gdzie |
|---|---|---|
| reguły | 7 | `mocodawca[].podpisujacy[].imie_nazwisko` (dodatkowi „podpisujący” względem referencji; przyczyny nie rozbijano na przypadki) |
| LLM | 2 | `pelnomocnicy[].imie_nazwisko` (dodatkowy element) |

Luki (n = 8 dokumentów każda; F1 na polach dotkniętych luką; „tn” = poprawnie `null`):

| Luka | reguły | LLM |
|---|---|---|
| g1 brak pełnomocnika (usunięty blok reprezentacji, podpis i załącznik) | 8 TP, 24 TN, 0 FP | **4 FP** na 8 dokumentach: flaga `przez-pelnomocnika` = 1 mimo braku; imię i firma `null` poprawnie |
| g2 powód 12 (zdanie o projektowanych postanowieniach umowy) | 8/8 id 12 | v1: 4/8, v2: 8/8 |
| g3 brak BZP i TED (wartości usunięte, etykiety zostają) | 16 TN, 0 FP | 16 TN, 0 FP |
| g4 wpis 15 000,00 zł zamiast 200,00 | 8/8 | 8/8 |

## Jak to działa i dlaczego tak wyszło

Referencja `null` jest rzadka w danych (wartościowe pola 1654, `null` 243), ale to tam leży kluczowa decyzja z `zasady-f1.md`: wartość tam to FP. Reguły są konserwatywne dla pól opartych na etykiecie (nie ma etykiety → `null`), a mylą się przy polach listowych bez etykiety (podpisujący). LLM nie wymyśla wartości w g3 (etykieta bez wartości daje `null`), ale ustawia flagę logiczną „przez pełnomocnika” na podstawie ogólnych sygnałów (osoba podpisująca, „w imieniu”), nie obecności bloku reprezentacji.

## Ograniczenia

- Luki to **syntetyczne edycje 8 dokumentów każda** (`gaps.py`), bez kontroli niezależnej; g1 po poprawce usuwa także podpis i załącznik, ale nadal może pozostawiać inne ślady reprezentacji. Wynik g1 jest podatny na sposób edycji.
- 0 prawdziwych dokumentów z lukami w dev (0/60 w danych organizatora wg recenzji).
- Nie zbadano przelewu typu wpis z innym tytułem (tytuł nie jest oceniany regułami), osoby fizycznej bez KRS ani PESEL (dev: 1 PESEL).

## Wniosek decyzyjny

Pola z możliwym `null` (flagi logiczne, pełnomocnik, BZP, TED) wymagają **decyzji obecności opartej na dowodzie w tekście** (np. istnienie bloku „reprezentowana przez” lub cytatu), a nie na samej odpowiedzi LLM: tutaj reguła strukturalna ma 0 FP w g1, a LLM 4/8. Przy zwracaniu wartości dla pól z referencją niepustą należy preferować kandydata (FP = FN), ale dla pól logicznych i opcjonalnych zostawić `null` bez cytatu. Pewność: niska co do liczby (n = 8), średnia co do kierunku. Otwarte: prawdziwe dokumenty z lukami, E17 (polityka `null`/eksportu).

## Uwaga o czasie

Czasy wywołań LLM i przebiegów zebrano pod obciążeniem maszyny i współdzielonym kluczem (429, ponowienia): **niewiążące**, nie do decyzji. Miary jakości od obciążenia nie zależą.
