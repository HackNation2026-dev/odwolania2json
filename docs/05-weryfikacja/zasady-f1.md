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
