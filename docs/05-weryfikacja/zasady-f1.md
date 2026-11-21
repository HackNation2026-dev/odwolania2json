---
wersja: 0.2.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# F1 — co potwierdził organizator

Źródło: [komunikaty UZP z Discorda](../01-zadanie/zrodla/UZP-Discord-doprecyzowania-2026-11-21.md), 11:26 i 13:26. Nie otrzymano kodu ewaluatora.

| Kategoria | Definicja z komunikatu |
|---|---|
| TP | wartość obecna i zgodna z referencją |
| TN | wartości brak w wyniku i referencji |
| FP | wartość tylko w wyniku albo obecna w obu, lecz nieprawidłowa |
| FN | wartości brak w wyniku, ale jest w referencji |

Próg zgodności długich ciągów: obecnie 80%. Dotyczy nazwy firmy pełnomocnika, tytułu przelewu, nazwy odwołującego, nazwy zamawiającego i tytułu zamówienia. Listy dopasowuje się po treści, nie pozycji.

Nie podano: algorytmu podobieństwa, normalizacji tekstu, reguł dla null/pustych wartości, agregacji wyników, łączenia wieloelementowych list ani zachowania przy zerowym mianowniku. Komunikat nie wyjaśnia, czy błędną wartość nalicza się dodatkowo jako FN; nie dopisuj tej reguły samodzielnie.

Standardowy wzór F1 to `2*TP / (2*TP + FP + FN)`. TN nie wchodzi do tego wzoru. Sam wzór nie odtwarza wszystkich decyzji oficjalnego ewaluatora. Własne pomiary oznaczaj jako przybliżenie według jawnie opisanej metody.

Do czasu uzyskania ewaluatora prowadź osobno: klasyfikację, zgodność struktury, dopasowanie pól i przypadki sporne. Brak danych referencyjnych nie daje podstaw do deklaracji wysokiej jakości.

## Uzupełnienie 0.5.0 (2026-11-21)

Mentor potwierdził (przez użytkownika), że ewaluacja liczy wszystkie cztery kategorie: TP, TN, FP i FN, jak w komunikacie 11:26. Ewaluator zespołu raportuje pełną macierz pomyłek na pole i na klasę oraz F1 według wzoru powyżej. TN raportujemy osobno, bo standardowy F1 go nie używa, a sposób jego wpływu na ocenę organizatora nie jest znany. Źródło: [odpowiedzi mentora](../01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md).

## Wniosek dla strategii ekstrakcji (2026-11-21)

Definicja z komunikatu 11:26 (potwierdzona ponownie przez użytkownika 2026-11-21) liczy błędną wartość wyłącznie jako FP. Przy F1 = 2·TP / (2·TP + FP + FN) dla pojedynczego pola:

| Referencja | Zwracamy `null` | Zwracamy wartość poprawną | Zwracamy wartość błędną |
|---|---|---|---|
| ma wartość | FN | TP | FP |
| `null` | TN (nie wpływa na F1) | — | FP |

Wnioski (interpretacja zespołu, do weryfikacji na ewaluatorze):

1. Gdy pole w dokumencie **istnieje**, zwrócenie najlepszego kandydata nigdy nie jest gorsze od `null`: błąd kosztuje tyle samo (FP zamiast FN), a trafienie daje TP.
2. Gdy pola w dokumencie **nie ma**, każda zwrócona wartość to FP, a `null` to neutralny TN.
3. Kluczowa decyzja to więc „czy pole występuje w dokumencie”, a nie „czy jestem pewien wartości”. Klasyfikator obecności pola jest ważniejszy niż próg pewności wartości.
4. Próg 80% dotyczy tylko długich tekstów (nazwy firm i pozostałe pola wskazane 13:26). Dla identyfikatorów i dat zakładamy dokładną zgodność, więc normalizacja formatu decyduje o TP.
5. Zasada „brak zmyślania” (UZP-04) pozostaje: wartość musi pochodzić z dokumentu. Wniosek 1 nie pozwala zgadywać wartości spoza tekstu.
