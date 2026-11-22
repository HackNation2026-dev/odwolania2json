# E17: polityka null i eksportu a F1

**Wynik nie jest oficjalnym F1.** Liczone offline z zapisanych odpowiedzi E10/E11 (bez nowych wywołań; `lib/analyze_e17.py`), ewaluator produkcyjny, bootstrap po sprawach (ziarno 20261122).
Czas/RSS nie dotyczą (brak pomiaru czasu).

## Hipoteza i reguła
Recenzja (Fable): zerowanie pola bez kotwicy bbox i niewyeksportowanie dokumentu wymagającego sprawdzenia to czysta strata F1, gdy wartość jest w dokumencie; bbox nie może decydować o treści ocenianego JSON.
Reguła (prerejestracja): polityka odwrotna do architektury zastępuje domyślną, gdy dolna granica ΔF1 (sparowane) > 0.

## Polityki
- `default`: jak w uprzęży: pole niezakotwiczone zostaje z wartością (kod `evidence_unanchored`, wynik `partial`), `partial` jest eksportowany, awaria LLM = brak pliku.
- `unanchored_null`: pole z cytatem bez jednoznacznej kotwicy dostaje null (architektura §4.5).
- `no_export_partial`: dokument `partial` nie jest eksportowany.
- `rules_fallback`: przy awarii LLM (`technical_error` `llm_*`) eksport wyniku z reguł zamiast braku pliku.
- `ambiguous` → brak pliku vs najlepsza klasa: patrz niżej.

## Wyniki (ΔF1 = polityka − default)
| Zbiór | Polityka | Dokumentów / zmienionych | F1 default | F1 polityka | ΔF1 [95%] |
|---|---|---|---|---|---|
| tekst, wariant A (5 powtórzeń) | unanchored_null | 435 / zmienione 100 | 0.938 [0.910; 0.959] | 0.917 [0.887; 0.940] | -0.021 [-0.029; -0.014] (base>cand) |
| tekst, wariant A (5 powtórzeń) | no_export_partial | 435 / zmienione 101 | 0.938 [0.910; 0.959] | 0.730 [0.670; 0.781] | -0.208 [-0.268; -0.155] (base>cand) |
| tekst, wariant A (5 powtórzeń) | rules_fallback | 435 / zmienione 9 | 0.938 [0.910; 0.959] | 0.940 [0.915; 0.960] | +0.002 [+0.000; +0.005] (cand>base) |
| skan+mieszany+S2+S5, wariant B (OCR+LLM) | unanchored_null | 144 / zmienione 90 | 0.893 [0.854; 0.924] | 0.819 [0.778; 0.853] | -0.073 [-0.082; -0.064] (base>cand) |
| skan+mieszany+S2+S5, wariant B (OCR+LLM) | no_export_partial | 144 / zmienione 92 | 0.893 [0.854; 0.924] | 0.439 [0.339; 0.529] | -0.453 [-0.545; -0.368] (base>cand) |
| skan+mieszany+S2+S5, wariant B (OCR+LLM) | rules_fallback | 144 / zmienione 5 | 0.893 [0.854; 0.924] | 0.895 [0.860; 0.924] | +0.002 [+0.000; +0.006] (nierozstrzygnięte) |

`ambiguous`: router LLM zwrócił `ambiguous` w 0 z 435 wierszy (wejście tekstowe, M3.1-Flash), więc polityka „najlepsza klasa” nie ma tu czego zmieniać: gdy LLM mówi `ambiguous`, nie ma pól do eksportu,
a wymuszony wybór klasy w prompcie nie był osobno testowany. Router regułowy kończy `ambiguous` dla 12 dokumentów (w tym 2 obcych); wśród 10 pozytywów
najwyżej oceniona klasa była poprawna w 10 (to trafność klasy, nie F1: ekstrakcji z wymuszoną klasą uprząż nie wykonuje).

## Jak to działa i dlaczego tak wyszło
Pole niezakotwiczone to wartość wskazana przez LLM, której cytatu nie da się jednoznacznie odnaleźć w słowach PDF/OCR (kotwiczenie na znakach, zero „zgadywania”). Wartość bywa poprawna, więc zerowanie jej obniża TP (kolumna `unanchored_null`).
Wyłączenie `partial` z eksportu usuwa duży odsetek poprawnych pól, bo `partial` to w tej uprzęży także status poprawnych dokumentów z drobną flagą (np. jedno niezakotwiczone pole).
Wynik reguł zamiast `{}` przy awarii LLM dodaje tylko pola formatowe, ale to dodatni przyrost, gdy awaria się zdarza.

## Ograniczenia
`unanchored_null` jest liczone na zapisanych kandydatach (`t3/candidates.json`); kotwiczenie w uprzęży jest prostsze niż docelowe (§4.5), więc odsetek niezakotwiczonych może być inny w produkcie.
Awarie LLM w danych to głównie `llm_invalid_response` (pusta lub niepoprawna odpowiedź 2×); polityka `rules_fallback` dotyczy tylko takich dokumentów (liczba zmienionych w tabeli): przedział jest wąski z powodu małej liczby zmian.
Brak testu `ambiguous`→klasa z wymuszeniem w prompcie. Mała próbka (25 spraw).

## Wniosek decyzyjny
- tekst, wariant A (5 powtórzeń): zerowanie pola bez kotwicy: ΔF1 -0.021 [-0.029; -0.014] → polityka pogarsza F1.
- tekst, wariant A (5 powtórzeń): brak eksportu dla `partial`: ΔF1 -0.208 [-0.268; -0.155] → polityka pogarsza F1.
- tekst, wariant A (5 powtórzeń): wynik reguł przy awarii LLM: ΔF1 +0.002 [+0.000; +0.005] → polityka zmienia wynik na lepszy.
- skan+mieszany+S2+S5, wariant B (OCR+LLM): zerowanie pola bez kotwicy: ΔF1 -0.073 [-0.082; -0.064] → polityka pogarsza F1.
- skan+mieszany+S2+S5, wariant B (OCR+LLM): brak eksportu dla `partial`: ΔF1 -0.453 [-0.545; -0.368] → polityka pogarsza F1.
- skan+mieszany+S2+S5, wariant B (OCR+LLM): wynik reguł przy awarii LLM: ΔF1 +0.002 [+0.000; +0.006] → bez rozstrzygnięcia.

Rekomendacja: bbox dowodu nie powinien decydować o treści ocenianego JSON: niezakotwiczone pole wyeksportować z wartością i oznaczyć do sprawdzenia (`review_required`), o ile liczby powyżej pokazują stratę przy zerowaniu; `partial` eksportować; przy awarii LLM rozważyć wynik reguł jako jawnie oznaczony wynik częściowy (nigdy cichą podmianę z cache; decyzja zgodna z architekturą §9.1 wymaga ADR).

## Stan końcowy (22.11.2026)
Wszystko liczone offline z zapisanych odpowiedzi (bez API); wiersze z błędem sieci/limitu nie weszły do liczb. Liczności jak w tabeli (435 dok.×powt. dla tekstu, 144 dla B na skanach; B ma 6 niepowtórzonych wierszy, patrz E11). Wynik `rules_fallback` jest równy +0.002 [+0.000; +0.005] dla tekstu: mała zmiana, bo w 9 z 435 przypadków LLM zawiódł. Test odpowiedzi `ambiguous` wymusza prompt, którego nie sprawdzono; zostaje otwarte.
