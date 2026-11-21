Gotowe: **180 kart**, schemat JSON, generator katalogu kodów, podsumowanie i [raport](../../../docs/05-weryfikacja/karty-dokumentow-2026-11-21.md).

- Dodano `karty.py`, `katalog_md.py`, `test_karty.py`, `karta.schema.json`; zaktualizowano `wspolne.py`, manifest i dokumentację formatu.
- Dopasowano **1784/1784 wartości**: 1414 dokładnie, 370 w innym zapisie. Osobno: 248 wyliczanych i 284 null.
- Wykryto **16 z 45 kodów** katalogu.
- Spójne ramki: **446/622 grup (71,70%)**; zamawiający: **82,54%**.
- **55 testów przeszło**. `verify_docs.py`: OK.
- Ręcznie sprawdzono karty 41 i 42 oraz wylosowane: 34 — pełnomocnictwo, 12 — przelew, 18 — pełnomocnictwo. Poprawiono wykryte błędy REGON-u i konsorcjum.

**Grupowanie da się zrobić**, ale UI potrzebuje możliwości zaznaczania kilku obszarów. Jedna ramka może obejmować cudze dane; etykiety i kolumny pozostają heurystyczne. Pokrycie referencji nie jest miarą F1.

Oryginały, adnotacje i przeglądarka pozostały nietknięte. Wyniki modeli zachowano w 206 plikach.