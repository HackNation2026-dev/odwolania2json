---
wersja: 0.5.0
aktualizacja: 2026-11-21
status: wynik eksperymentu (spike, kod jednorazowy)
---

# Eksperyment: czy YAML wystarcza do opisu klasy dokumentu

Zgoda użytkownika: 2026-11-21 (decyzja ad 8 w [ADR-002](../07-decyzje/ADR-002-decyzje-po-recenzji.md)). Kod: [`experiments/2026-11-21-yaml-klasy/`](../../experiments/2026-11-21-yaml-klasy/). Uruchomienie: Python 3.13.18, pydantic 2.14.4, PyYAML 6.0.4, `python eksperyment.py`. Surowe wyniki: `wyniki.json` obok skryptu.

## Pytanie

Czy proponowany format YAML (jeden plik na klasę) opisuje wynikowy JSON wszystkich trzech klas tak, żeby silnik budował z niego ścisły model danych, serializację, schemat dla LLM i pola pochodne bez kodu specyficznego dla klasy? I czy czwartą klasę da się dodać samym YAML-em?

## Metoda

1. Trzy pliki YAML ([`klasy/`](../../experiments/2026-11-21-yaml-klasy/klasy/)) przepisane ręcznie ze wzorców `oczekiwane-json` i danych 60 spraw. Wzorce mają komentarze i brakujący przecinek, więc nie da się ich wczytać automatycznie.
2. Silnik ([`silnik.py`](../../experiments/2026-11-21-yaml-klasy/silnik.py)) buduje z YAML dynamiczny model pydantic w trybie ścisłym (`strict`, `extra=forbid`), alias dla kluczy niebędących identyfikatorami (`przez-pelnomocnika`), wzorce formatów, zakresy, enumy, listy i zagnieżdżenia.
3. Referencje: 60 spraw z migawki `f60ca6f` z nałożonymi poprawkami `main-7590db8` (5 plików odwołań).
4. Sprawdzenia na każdej referencji:
   - **walidacja**: referencja przechodzi przez model;
   - **roundtrip**: serializacja modelu daje JSON identyczny z referencją, łącznie z kolejnością kluczy;
   - **formaty**: każda niepusta wartość spełnia `format` z YAML;
   - **pochodne**: pola wyliczane funkcjami z rejestru są równe referencji;
   - **mutanty**: dla każdego liścia usunięcie klucza, zmiana typu (tekst↔liczba) oraz dodatkowy klucz; walidator musi odrzucić każdego mutanta.
5. Czwarta, hipotetyczna klasa ([`klasy_nowe/`](../../experiments/2026-11-21-yaml-klasy/klasy_nowe/)) z elementami, których nie ma w trzech klasach: lista tekstów, enum z `null`, liczba z zakresem. Plus YAML z nieistniejącym normalizatorem.

## Wyniki

| Klasa | Walidacja | Roundtrip identyczny | Naruszenia formatu | Pola pochodne zgodne | Mutanty zabite |
|---|---|---|---|---|---|
| odwołanie | 60/60 | 60/60 | 0 | 183/183 | 2609/2609 |
| pełnomocnictwo | 60/60 | 60/60 | 0 | brak pochodnych | 1139/1139 |
| przelew | 60/60 | 60/60 | 0 | brak pochodnych | 780/780 |

Nowa klasa: model zbudowany bez zmian w silniku, poprawna próbka przechodzi, enum spoza listy i liczba spoza zakresu są odrzucane. YAML z nieznanym normalizatorem jest odrzucany przy wczytaniu (`zla.x: brak normalizatora 'nieistniejacy' w rejestrze`).

**Kontrola czułości:** ta sama reguła pochodna `czynnosc_opis = słownik[czynnosc_powod_id]` uruchomiona na referencjach bazowych **sprzed** poprawki organizatora wykrywa dokładnie 5 niezgodności (przyklad_19, 23, 25, 44, 55: „Odpowiedzi i wyjaśnienia do SWZ” zamiast „Odpowiedzi/wyjaśnienia do SWZ”). To te same pliki, które organizator poprawił w `7590db8`. Test nie jest więc pusty: wykrywa realny błąd danych.

## Ustalenia o danych (ważne dla serializacji)

- `pelnomocnicy[].pesel`: wzorzec pokazuje liczbę (`85120133547`), a **wszystkie** referencje mają tekst albo `null` (97× `null`, 1× tekst). YAML przyjmuje tekst. Do potwierdzenia u organizatora: który typ oceni ewaluator.
- `przelew_bankowy.numer_transakcji`: wzorzec ma `null`, referencje mają tekst w 60/60 przypadków.
- `Odwolujacy[].przez-pelnomocnika`: zawsze 1 i zawsze zgodne z obecnością pełnomocnika.
- `Zamawiajacy[].prowadzacy_postepowanie`: `null` dokładnie wtedy, gdy zamawiający jest jeden (57 spraw); przy dwóch zamawiających 0/1 (3 sprawy). Reguła z komentarza wzorca potwierdzona na danych.
- Kolejność kluczy jest jednolita we wszystkich 180 referencjach.
- `kwota` jest liczbą zmiennoprzecinkową; zapis `10000.00` we wzorcu i `10000.0` po serializacji są równe po wczytaniu JSON, ale nie tekstowo. Do sprawdzenia, czy ewaluator porównuje wartości, czy tekst.

## Odpowiedź

**Tak, dla opisu wyniku YAML wystarcza.** Struktura, typy, nullowalność, kolejność kluczy, formaty, enumy, zakresy, aliasy kluczy i pola pochodne trzech klas są w pełni wyrażalne, a czwartą klasę dodano bez zmian w kodzie.

**Granica:** „bez kodu” działa tylko wtedy, gdy nowa klasa korzysta z istniejących normalizatorów i funkcji pochodnych z rejestru. Nowy rodzaj reguły (np. inny słownik, inna zależność między polami) to nowa funkcja w kodzie, dodawana raz i potem używana z YAML. Dla odwołania wystarczyły trzy funkcje: `ze_slownika`, `obecnosc`, `null_gdy_lista_jednoelementowa`.

**Czego eksperyment NIE sprawdzał i czego YAML v0 nie opisuje:**

1. **Semantyka ekstrakcji.** Zakres („nagłówek pierwszej strony”), reguła „wyłącznie pierwszy zarzut” i przypisanie roli („ten NIP należy do zamawiającego”) są w YAML tylko opisem tekstowym (`zakres`, `rola`, `opis`). Silnik ich nie wykonuje. To zależy od decyzji 3, 4 i 5 (odczyt PDF, OCR, klasyfikacja), które są otwarte.
2. **Łączenie wyników reguł i LLM w obrębie jednego elementu listy.** Schemat dla LLM zawiera tylko pola `metoda: llm` (np. `Odwolujacy[].nazwa`), a pola regułowe tego samego elementu (`nip`, `krs`) trzeba do niego przypiąć. YAML v0 nie definiuje, jak. To uwaga Codexa nr 7.
3. **Jakość ekstrakcji.** Eksperyment sprawdza kontrakt wyniku, nie to, czy dane da się wyciągnąć z PDF.
4. Ograniczenia `min`/`max` nie trafiają jeszcze do schematu dla LLM (drobne, do dodania).

## Wniosek dla architektury

YAML zostaje formatem opisu klasy. Do rozstrzygnięcia przy projektowaniu ekstrakcji (po decyzjach 3–5): kontrakt kandydata wartości (wartość, rola, fragment źródła, normalizator, pewność) i reguły scalania, wyrażane w YAML przez odwołanie do nazwanych strategii z rejestru. Mutanty z tego eksperymentu warto przenieść do testów walidatora docelowej aplikacji.

## Uzupełnienie (2026-11-21, po odpowiedziach mentora)

Typ `pesel` rozstrzygnięty: tekst albo `null`, jak przyjęto w YAML. Ta sama zasada obejmuje rachunki i `numer_transakcji`. `kwota` pozostaje liczbą JSON, tak jak w referencjach. Źródło: [odpowiedzi mentora](../01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md).
