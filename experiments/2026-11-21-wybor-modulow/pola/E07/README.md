# E07: podmioty i role (odwołujący, zamawiający, pełnomocnik, mocodawca)

Skrypt: `../e07_e09_e20.py` (po `../run_extraction.py`; ocena ok. 20 s, z cache LLM), surowe liczby `wyniki.json`. Reguły: `../rules.py` (`extract_parties`, `extract_poa`), LLM: `../llm_extract.py` (jedno wywołanie na dokument, JSON w kluczach organizatora, tekst PDF z całego dokumentu, temperatura 0, MiniMax-M3.1-Flash, 179 wywołań wspólnych z E09/E20, 0 awarii, bez powtórzeń).
Miara: F1 ewaluatorem produkcyjnym (próg 0,8 dla nazw), pola `Odwolujacy[]`, `Zamawiajacy[]`, `mocodawca[]`, `pelnomocnicy[]`, bootstrap 95% po 49 sprawach, różnica sparowana.

## Hipoteza

Kontekst + regex przypisuje role tak samo dobrze jak LLM; błędne przypisania identyfikatorów (NIP zamawiającego jako odwołującego) są rzadkie.

## Wynik (zbiór rozwojowy, 49 spraw, 98 dokumentów odwołań i pełnomocnictw)

| Wariant | F1 pól podmiotów [95%] | odwołanie | pełnomocnictwo | FP / FN |
|---|---|---|---|---|
| reguły | 0,9865 [0,979; 0,993] | 1,000 | 0,964 | 7 / 19 |
| LLM (1 wywołanie) | **0,9969 [0,994; 0,9995]** | 1,000 | 0,992 | 4 / 2 |
| hybryda (LLM + weryfikacja identyfikatorów w tekście) | 0,9969 | 1,000 | 0,992 | 4 / 2 |

Różnica sparowana LLM − reguły: **+0,0104 [+0,003; +0,018]** (49 spraw). **Przypisanie identyfikatora złej roli: 0 na 294 wyemitowane identyfikatory** (KRS/NIP/REGON/PESEL) dla każdego wariantu. Hybryda jest identyczna z LLM, bo żaden identyfikator z LLM nie był niezgodny z tekstem (zero halucynacji cyfr).
Błędy reguł: nazwa mocodawcy w 8 układach, podpisujący (7 FP, 11 FN). Błędy LLM: imiona pełnomocników zmieniane przez model (np. „Zawadzki” → „Zawadzka”, „Jurgielewicz” → „Jurpielewicz”) oraz jeden dokument (przykład 10) z pustą listą pełnomocników.

## Jak to działa i dlaczego tak wyszło

Dokumenty organizatora mają kilka powtarzalnych układów (blok `Odwołujący:` z identyfikatorami w linii, konsorcjum z listą numerowaną, pełnomocnictwo w trzech szablonach). Reguły strojone na tych układach dochodzą do 1,000 na odwołaniach, ale każdy nowy układ pełnomocnictwa (nazwa mocodawcy w innym miejscu, podpisujący po stanowisku) wymagał osobnej poprawki: w pierwszym przebiegu nazwa mocodawcy trafiała w 12/53. LLM nie ma tego kosztu, a błędy cyfr nie wystąpiły; jego błędy to „poprawianie” fleksji nazwisk, które w danych syntetycznych jest celowo błędne gramatycznie (kobieta z nazwiskiem męskim), czyli pole, w którym dokładna kopia z tekstu bije normalizację.

## Ograniczenia

- Reguły były stroione na tym samym zbiorze rozwojowym (górna granica); LLM bez strojenia na polach (prompt jeden). Mimo to LLM wygrywa, więc regułowa przewaga nie wynika z nadmiaru strojenia po stronie LLM.
- **Brak testów niezależnych układów** (bez etykiet, etykieta po danych, zamiana płatnik/odbiorca, wiele osób), które zalecał Codex: dev ma 49 spraw z jednym odwołującym (lider konsorcjum), 3 sprawy z 2 zamawiającymi, 0 z PESEL oprócz 1. Zero błędnych ról na 294 identyfikatorach dotyczy tych szablonów.
- Jedno wywołanie LLM na dokument, bez powtórzeń; granice przedziałów dotyczą 49 spraw.

## Wniosek decyzyjny

Kryterium „błędne przypisania ≤ próg” (próg nie został zapisany przed pomiarem) trzeba zastąpić regułą porównawczą z planu 0.2: LLM zastępuje reguły, bo dolna granica różnicy F1 jest dodatnia (+0,003). Role i podmioty: **LLM, a regułowe wyodrębnienie identyfikatorów jako kontrola w tekście** (zero zmian wyniku tutaj, ale tania asekuracja przed halucynacją cyfr). Nazwisk nie normalizować. Pewność: średnia (jeden przebieg LLM, dane szablonowe, mała liczba rzadkich układów). Otwarte: układy bez etykiet i konsorcja wieloosobowe, powtórzenia LLM, pomiar na OCR (nie zrobiony dla E07).

## Uwaga o czasie

Czasy wywołań LLM i przebiegów zebrano pod obciążeniem maszyny i współdzielonym kluczem (429, ponowienia): **niewiążące**, nie do decyzji. Miary jakości od obciążenia nie zależą.
