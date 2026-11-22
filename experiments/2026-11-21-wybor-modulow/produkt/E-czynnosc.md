# E-czynnosc: reguły czynności, numeru BZP i imienia pełnomocnika (Z05) na zapisanych odpowiedziach LLM

**Wynik nie jest oficjalnym F1** (F1 przybliżony ewaluatora produkcyjnego: błędna wartość to tylko FP, próg 80%, miara `ratio`). Przedziały 95%: bootstrap po sprawach (`bootstrap.py`, 2000 losowań, ziarno 20261122), różnice sparowane po tych samych sprawach.

## Metoda (replay, bez nowych wywołań API)

- Zbiór: 25 spraw rozwojowych z `llm-e2e/subset_dev.json` (375 dokumentów: 125 odwołań, 125 pełnomocnictw, 125 przelewów; do 5 powtórzeń odpowiedzi na dokument). Zbioru kontrolnego nie uruchamiano, wariantów syntetycznych spraw kontrolnych nie użyto, API LLM nie wołano.
- „Przed”: zapisane odpowiedzi `llm-e2e/E10/raw/e10-text-p2.jsonl` (tekst PDF + prompt p2). Wynik zgadza się z E10: F1 0,938 [0,911; 0,960].
- „Po”: `odwolania2json.domain.czynnosc.refine_appeal` zastosowane do zapisanego wyniku odwołania z tekstem z `pola/cache/texts_pdf.json` (ten sam tekst co w E10; test w repozytorium sprawdza, że czytnik produktu daje ten sam tekst):
  - `czynnosc_powod_id`, `czynnosc_opis` (literalnie ze słownika organizatora) i `czynnosc_dzien` z reguł pierwszego zarzutu; gdy reguły nic nie znajdą, zostaje wartość modelu;
  - `numer_bzp` z bloku „dotyczy: … ODWOŁANIE”, a bez niego wartość modelu znormalizowana (`RRRR/BZPNNNNNNNN`, bez spacji) i z dowodem w tekście, inaczej `null`;
  - `pelnomocnik.imie_nazwisko` tylko osoba występująca w tekście (z listy „A; B” pierwsza z dowodem), inaczej `null`.
- Skrypt: `produkt/e_czynnosc_replay.py` (`PYTHONPATH=apps/backend:packages/contracts .venv-exp/bin/python experiments/2026-11-21-wybor-modulow/produkt/e_czynnosc_replay.py`), surowe liczby `e_czynnosc_wyniki.json`.

## Wynik

F1 całości (375 dokumentów, 25 spraw): przed **0,938 [0,911; 0,960]**, po **0,956 [0,929; 0,976]**, ΔF1 **+0,018 [+0,013; +0,024]** (sparowane po sprawach; hipoteza z zadania: +0,01…+0,02).

ΔF1 per pole (po wszystkich trzech zmianach; przedział z bootstrapu po 25 sprawach, F1 liczone na samym polu):

| Pole | F1 przed | F1 po | ΔF1 [95%] |
|---|---|---|---|
| `numer_bzp` | 0,593 | 0,956 | **+0,364 [+0,221; +0,552]** |
| `czynnosc_powod_id` | 0,843 | 0,963 | **+0,120 [+0,041; +0,225]** |
| `czynnosc_opis` | 0,832 | 0,963 | **+0,131 [+0,048; +0,238]** |
| `czynnosc_dzien` | 0,899 | 0,963 | **+0,064 [+0,017; +0,130]** |
| `pelnomocnik.imie_nazwisko` | 0,843 | 0,958 | **+0,116 [+0,059; +0,180]** |

Wkład osobno (ΔF1 całości, sparowane): tylko czynność **+0,009 [+0,003; +0,015]**, tylko `numer_bzp` **+0,006 [+0,004; +0,009]**, tylko imię pełnomocnika **+0,003 [+0,002; +0,005]**; wszystkie razem +0,018.

## Jak to działa i dlaczego tak wyszło

- `numer_bzp`: 47 FP wynikało głównie z odstępu w odpowiedzi modelu (`2026/BZP 00999063` zamiast `2026/BZP00999063`); normalizacja usuwa odstęp, a numer z bloku „dotyczy” rozstrzyga między postępowaniem bieżącym i wcześniejszym (`2025/BZP …` w tym samym piśmie).
- `pelnomocnik.imie_nazwisko`: model zwracał listę dwóch osób („A, B”) tam, gdzie referencja ma pierwszą; dowód w tekście i wybór pierwszej osoby usuwa 24 FP.
- Czynność: model brał „Zarzut nr 1” z dalszej części pisma (11 = OPZ, 4 = SWZ); reguły czytają pierwszą pozycję po „polegających na:”.

## Ograniczenia (nie zawyżać)

- Reguły i walidatory były strojone na zbiorze rozwojowym, w tym na tych samych 25 sprawach; po jednym błędzie reguł (przyklad_54: „SWZ … i wzoru umowy”, powód 4 zamiast 12) zmieniono kolejność reguł (SWZ przed słabym wzorcem „wzoru umowy”). Wynik reguł na rozwojowym (49/49 odwołań, powód, opis i dzień; numer BZP 49/49) to **górna granica**, nie prognoza na zbiór testowy.
- Jeden generator dokumentów, szablonowy układ; powód 12 nie występuje w prawdziwych dokumentach rozwojowych (8 przypadków luki g2 to edycje SYNTETYCZNE tekstu, `pola/gaps.py`; podobnie g1, brak pełnomocnika). Odwołania o innym układzie (brak bloku „dotyczy”, brak listy „polegających na:”) nie były testowane; wtedy działa wartość modelu z dowodem w tekście.
- Odpowiedzi modelu bez wyniku (błąd techniczny) nie są poprawiane regułami w replayu (brak payloadu), stąd F1 po < 1 (0,963 dla pól czynności).
- Replay nie zmienia wywołań LLM, więc nie mierzy wpływu na czas ani tokeny; powtórzenia w obrębie sprawy nie są niezależne (bootstrap po sprawach to uwzględnia).
- Test integracyjny w repozytorium: `tests/unit/test_czynnosc.py` (147 dokumentów rozwojowych, 8 + 8 luk syntetycznych); mutacje `domain/czynnosc.py`: 67/67 zabitych.
