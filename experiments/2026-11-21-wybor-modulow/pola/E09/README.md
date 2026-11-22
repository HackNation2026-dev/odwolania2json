# E09: zaskarżona czynność (powód 1–12 i data)

Skrypty: `../e07_e09_e20.py` (ocena), `../e09_prompt_v2.py` (prompt v2, 57 wywołań), reguły `../rules.py` (`extract_act`), surowe liczby `wyniki.json`.
Miara: F1 ewaluatora na `czynnosc_powod_id`, `czynnosc_dzien`, `czynnosc_opis`, dokładność id i daty; bootstrap po 49 sprawach, różnica sparowana względem reguł.

## Hipoteza

Reguły (słowa kluczowe w pierwszej czynności) ≥ LLM; kryterium z planu: „reguły tylko jeśli ≥ LLM”.

## Wynik (49 odwołań rozwojowych)

| Wariant | F1 [95%] | id poprawne | data poprawna | id 12 (8 syntetycznych) |
|---|---|---|---|---|
| reguły | 0,993 [0,979; 1,000] | 48/49 | 49/49 | 8/8 |
| LLM v1 (prompt ogólny z pełnej ekstrakcji) | 0,749 [0,633; 0,843] | 28/49 | 34/49 | 4/8 |
| LLM v2 (prompt wskazujący źródło czynności) | 0,972 [0,950; 0,990] | 48/49 | 49/49 | 8/8 |

Różnica sparowana względem reguł: LLM v1 **−0,244 [−0,354; −0,151]**; LLM v2 **−0,021 [−0,043; 0,000]**. Błędy v1: 20 z 21 pomyłek to „11” (OPZ, 13×) lub „6” (7×), np. 8→11 (4×), 4→6 (3×). Reguły i v2 mają po jednym błędnym id (v2: 9→11; nie sprawdzano, czy to ten sam dokument co błąd reguł). Różnica F1 v2 vs reguły wynika z `czynnosc_opis` (7 FP: model nie podaje kanonicznego opisu dokładnie jak na liście).

## Jak to działa i dlaczego tak wyszło

Referencja bierze pierwszą czynność z pierwszej pozycji listy „polegających na: 1)” albo ze zdania „Zamawiający w dniu D roku …”. W części dokumentów zdanie narracyjne dotyczy innej czynności niż pierwszy zarzut (przypadki przykład 49, 58: zdanie o wyborze oferty, pierwszy zarzut o zaniechaniu unieważnienia, wzorzec 10). Prompt v1 mówił „pierwszy zarzut” i model brał „Zarzut nr 1” z dalszej części pisma, a ta treść bywa w danych ogólna (OPZ, równe traktowanie), co dało pomyłki 11/6. Prompt v2 wskazuje źródło i przywraca 48/49. Reguły robią to z definicji i dlatego są najlepsze.

## Ograniczenia

- Reguły i prompt v2 były stroione na dev, a v2 po zobaczeniu błędów v1: wynik v2 jest warunkowy; ten sam dev służył do obu. Wielkość próby 49, rozkład: id 12 nie występuje w danych (8 syntetycznych, wynikających z edycji zdania w dokumentach o krótkim układzie, nie z lekcji prawdziwych dokumentów).
- Dokumenty szablonowe: reguły łapią czasownik z krótkiego zdania lub z listy; prawdziwe odwołania z wieloma czynnościami w innej kolejności nie były testowane.
- Jedno wywołanie LLM, bez powtórzeń.

## Wniosek decyzyjny

Kryterium „reguły tylko jeśli ≥ LLM”: reguły ≥ LLM v2 (różnica LLM − reguły ≤ 0, górna granica przedziału 0,000) i ≫ LLM v1. **Dla powodu 1–12 i daty: reguły (słowa kluczowe na pierwszej czynności) jako główny wybór, LLM v2 jako kontrola i tryb awaryjny na pismach spoza układów regułowych.** Opis kanoniczny zawsze wyprowadzać z id (tabela 1–12), nie z tekstu LLM. Pewność: średnia (dane szablonowe, brak klasy 12 w danych prawdziwych). Otwarte: pierwszy zarzut w pismach o innym układzie, OCR, powtórzenia LLM.

## Uwaga o czasie

Czasy wywołań LLM i przebiegów zebrano pod obciążeniem maszyny i współdzielonym kluczem (429, ponowienia): **niewiążące**, nie do decyzji. Miary jakości od obciążenia nie zależą.
