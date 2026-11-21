---
wersja: 0.5.0
aktualizacja: 2026-11-21
status: źródło — odpowiedzi przekazane przez użytkownika
---

# Odpowiedzi na pytania do mentora UZP (2026-11-21)

Źródło: odpowiedzi przekazane przez użytkownika w rozmowie z asystentem, 2026-11-21, na listę pytań do mentora UZP. Użytkownik nie rozróżnił w każdym punkcie, co jest słowami mentora, a co jego ustaleniem. Punkty oznaczone „decyzja zespołu” to ustalenia użytkownika, nie organizatora. Treść poniżej oddaje sens wypowiedzi; nie jest dosłownym zapisem rozmowy z mentorem.

| Pytanie | Odpowiedź | Charakter |
|---|---|---|
| Ewaluator F1 | Liczone są TP, TN, FP i FN („pełna F1”), zgodnie z opisem na Discordzie (komunikat 11:26, zob. [Discord](UZP-Discord-doprecyzowania-2026-11-21.md), l. 42–45). Ewaluator zespołu musi zliczać wszystkie cztery kategorie. | odpowiedź, źródło Discord |
| Rewizja kontraktu (U-Q10) | Obowiązuje **najnowszy kod** repozytorium organizatora. | odpowiedź |
| Skany w teście (U-Q08) | **Tak.** Raz jest plik tekstowy, raz skan, raz jedno i drugie (dokument mieszany). | odpowiedź |
| Sposób dostarczenia | **Wyłącznie pip.** Na teście aplikacja musi się uruchomić u jury tylko przez pip. Docker tylko do pracy deweloperskiej. | odpowiedź |
| Model lokalny / API (pyt. 1, U-Q05) | Modele i inne komponenty **mogą być po API**, jeśli spełniają wymogi i są **hostowane w Europie**. Lokalny model instalowany przez pip nie został wprost ani potwierdzony, ani wykluczony. | odpowiedź |
| Rozmiar modelu (U-Q07) | Liczy się **największy model**, także w systemie wieloagentowym. | odpowiedź |
| GUI | **Musi być** (decyzja zespołu). Absolutne minimum: UI do wrzucenia pliku. Pełna wersja: aplikacja dla urzędu z wersjonowaniem dokumentów, przeglądaniem dokumentów lub całych paczek (spraw), użytkownikami i uprawnieniami. Zakres pełnej wersji do przemyślenia. | decyzja zespołu |
| Pusty JSON (U-Q03) | **Potwierdzone:** obcy dokument daje `{}` pod nazwą pliku wejściowego. O `null` i brak klucza nie pytano. | odpowiedź |
| Typy (pesel, numer_transakcji) | **PESEL to tekst.** Typowanie wzorujemy na modelowaniu danych w Excelu, standardzie urzędowym: numery (PESEL, NRB/IBAN, numer transakcji) to tekst albo `null`. Przy sprzeczności wzorca z referencjami decydują referencje. | decyzja zespołu |

## Uzasadnienie typów przekazane przez użytkownika (streszczenie)

Użytkownik wkleił uzasadnienie (bez wskazania autora; nie jest to wypowiedź organizatora):

- 26-cyfrowy numer rachunku przekracza bezpieczny zakres liczb całkowitych (JavaScript: 16 cyfr) i traci zera wiodące, więc musi być tekstem. To samo dotyczy numeru transakcji i PESEL.
- Ewaluator porównuje wynik z referencjami, nie z plikiem wzorcowym; przy ścisłym porównaniu typów liczba zamiast tekstu zeruje pole.
- `10000.00` i `10000.0` jako liczby JSON są po wczytaniu równe; jako tekst — różne.

Weryfikacja na danych (eksperyment YAML, 2026-11-21): `kwota` jest w 60/60 referencjach liczbą JSON (bez cudzysłowu), więc liczba miejsc po przecinku nie ma znaczenia przy porównaniu po wczytaniu JSON. `pesel`, rachunki i `numer_transakcji` są w referencjach tekstem lub `null`.
