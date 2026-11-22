# E16: determinizm i regresja

> **Zakres.** Wynik opisuje **uprząż** (kod regułowy i kod na nagranych odpowiedziach LLM), nie produkt i nie wariancję modelu. Dane: 60 dokumentów rozwojowych. Miary F1 w DT04 **nie są oficjalnym wynikiem**.
> **Czas.** Czasy przebiegów (1,1–1,6 s) zmierzono pod obciążeniem maszyny (load avg ok. 22–35); niewiążące, nie służą do decyzji.

## Hipoteza i kryterium (plan E16)

Ten sam wsad dwa razy daje identyczny JSON (kolejność kluczy, `null`, wersje); różnice mogą wystąpić tylko w polach LLM z jawną wariancją. Kryterium: *zero różnic poza polami LLM z jawną wariancją*. Plan (korekta 0.2) każe rozdzielić determinizm kodu od wariancji modelu: robimy to nagrywaniem odpowiedzi.

## Metoda

Skrypt: `.venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/E16/e16.py` (jedno polecenie). Wynik: `wyniki.json`.

- **DT01**: wsad 60 dokumentów na świeżych serwerach: w=1, ponownie w=1, w=4. Porównanie **bajtów** `result.json`, `evidence.json`, `report.json`, `diagnosis.json`, `state.json` oraz `versions.json` (bez `work_dir`, który zależy od katalogu).
- **DT02**: kolejność kluczy wyniku względem referencji organizatora (wynik ma być podciągiem kolejności referencji, bo `prune` usuwa puste elementy list) i liczba literałów `null`.
- **DT03**: ekstraktor LLM z deterministyczną atrapą (odpowiedź zależna od treści promptu), 10 przelewów, dwa przebiegi na osobnych serwerach: porównanie `result`, `evidence`, `report`, `ai-response.json`, `candidates.json`.
- **DT04**: ewaluator produkcyjny (`compare_document`, po PR #8/#9: poprawna wartość = TP, błędna = tylko FP, próg podobieństwa 80%) vs miara liści uprzęży (`run_experiment.leaf_counts`, multizbiór par ścieżka bez indeksów + wartość JSON) na wyniku regułowym 60 dokumentów.

## Jak to działa i dlaczego tak wyszło

- **Kod regułowy jest bajtowo deterministyczny**: 0 różnic między dwoma przebiegami i między w=1 a w=4; `versions.json` identyczny w 60/60. Deterministyczność wynika z braku losowości i zegara w artefaktach (czasy są tylko w `metrics.json`, który z założenia pomijamy) oraz z `json.dumps` z zachowaną kolejnością wstawiania.
- **Kolejność kluczy i `null`**: wynik powstaje z szablonu pierwszej referencji klasy, więc kolejność kluczy zgadza się z referencją (50/50 dokumentów z wynikiem; 10 dokumentów ma `ambiguous` bez `result.json`). Literały `null` różnią się od referencji (suma bezwzględna różnic 166), bo `prune` usuwa puste elementy list; kontrakt v1 musi rozstrzygnąć, czy puste elementy list i `null` w opcjonalnych polach mają być jawne.
- **Kod na nagranych odpowiedziach LLM jest deterministyczny** (DT03: 0 różnic, w tym `ai-response.json`; 7 z 10 przelewów trafiło do LLM, resztę router uznał za `ambiguous`). To pokazuje, że wariancja całego potoku z modelem wynika z modelu (patrz E13: szum bazowy MiniMax na polach `imie_nazwisko`, `tytul`), nie z kodu.
- **Ewaluator vs miara liści**: po naprawie ewaluatora produkcyjnego obie miary dają niemal te same F1 na wyniku regułowym (odwołania 0,205 vs 0,204; pełnomocnictwa 0,442 vs 0,442; przelewy 0,323 vs 0,323). Różnica 0,0005 dla odwołań prawdopodobnie wynika z dopasowania rozmytego (próg 80%) i dopasowania list w ewaluatorze produkcyjnym, których miara liści nie ma (porównuje wartości dokładnie, listy jako multizbiór); nie sprawdzano tego na poziomie pojedynczych pól. Stara uwaga w uprzęży („ewaluator produkcyjny nie zlicza tp”) jest nieaktualna: `tp` jest zliczane (np. odwołania tp 46); miara liści nie jest już potrzebna do porównań. F1 regułowe są niskie (to wariant bazowy bez OCR i bez LLM, nie wynik produktu).

## Ograniczenia

Kod regułowy i atrapa to wariant uproszczony: determinizm potoku z OCR (rapidocr/onnxruntime) i wielowątkowym wnioskowaniem nie był sprawdzany (kolejność sumowania w CPU może dawać różnice w ostatnich cyfrach confidence). Porównanie dotyczy jednej maszyny i jednej wersji pdfium. Wariancja modelu: zmierzona w E13 tylko na 2 dokumentach × 8 przebiegów.

## Wyniki wektorów

### Zestawienie wektorów

Wektorów: 4; luka: nie 3, nie dotyczy 1.

| ID | Rodzina | Wektor | Luka |
|---|---|---|---|
| DT01 | determinizm | ten sam wsad 60 dokumentów dwa razy (świeże serwery, w=1) i raz z w=4: bajty result/evidence/report/diagnosis/state | **nie** |
| DT02 | determinizm | kolejność kluczy wyniku względem referencji organizatora i obecność `null` | **nie** |
| DT03 | determinizm | kod na stałych odpowiedziach LLM (atrapa deterministyczna z treści): 10 przelewów dwa razy | **nie** |
| DT04 | regresja-miary | ewaluator produkcyjny (compare_document, domyślnie: błędna wartość = FP, próg 80%) vs miara liści uprzęży na 60 dokumentach regułowych | **nie dotyczy** |

### Szczegóły: oczekiwane, faktyczne, poprawka, test do produktu

**DT01 — ten sam wsad 60 dokumentów dwa razy (świeże serwery, w=1) i raz z w=4: bajty result/evidence/report/diagnosis/state** (luka: nie)

- Oczekiwane: zero różnic (kod regułowy jest deterministyczny)
- Faktyczne: w=1 vs w=1: zero różnic; w=1 vs w=4: zero różnic; versions.json (bez work_dir) identyczne w 60/60; czasy 1.64/1.55/1.14 s
- Proponowana poprawka: Utrzymać test powtarzalności bajtowej w CI (dwa przebiegi na stałych danych).
- Test do przeniesienia do produktu: `test_two_runs_same_batch_are_byte_identical_for_rules_pipeline`

**DT02 — kolejność kluczy wyniku względem referencji organizatora i obecność `null`** (luka: nie)

- Oczekiwane: kolejność kluczy zgodna z szablonem, `null` jawne dla pustych pól
- Faktyczne: kolejność kluczy wyniku jest podciągiem kolejności referencji (puste elementy list usunięte): 50/50 dokumentów z wynikiem (reszta: ambiguous bez result.json); różnica liczby literałów null między wynikiem a referencją (suma bezwzględna): 166 (wynik po `prune` usuwa puste elementy list, więc null-e w listach się różnią)
- Proponowana poprawka: Serializować wynik z kolejnością klas szablonu (Pydantic z zachowaniem kolejności pól); test porównania kolejności z `example` OpenAPI.
- Test do przeniesienia do produktu: `test_result_key_order_matches_template_and_nulls_explicit`

**DT03 — kod na stałych odpowiedziach LLM (atrapa deterministyczna z treści): 10 przelewów dwa razy** (luka: nie)

- Oczekiwane: identyczne bajty artefaktów; różnice tylko z wariancji modelu (tu jej brak)
- Faktyczne: różnice: zero różnic; wywołań atrapy 7/7
- Proponowana poprawka: Zapisywać odpowiedź modelu (jest: ai-response.json) i testować kod na nagranych odpowiedziach osobno od wariancji modelu.
- Test do przeniesienia do produktu: `test_replay_recorded_llm_responses_is_byte_identical`

**DT04 — ewaluator produkcyjny (compare_document, domyślnie: błędna wartość = FP, próg 80%) vs miara liści uprzęży na 60 dokumentach regułowych** (luka: nie dotyczy)

- Oczekiwane: wartości zbliżone; różnice wyjaśnione definicją
- Faktyczne: odwolanie: ewaluator F1=0.2049 (tp 46, tn 37, fp 1, fn 356), liście F1=0.2044; pelnomocnictwo: ewaluator F1=0.4416 (tp 34, tn 44, fp 0, fn 86), liście F1=0.4416; przelew: ewaluator F1=0.3226 (tp 15, tn 0, fp 0, fn 63), liście F1=0.3226
- Proponowana poprawka: Do porównań wariantów używać ewaluatora produkcyjnego; miara liści zostaje tylko jako kontrola.
- Test do przeniesienia do produktu: `(brak: dotyczy pomiaru, nie produktu)`

## Wniosek decyzyjny wobec kryterium z planu

Kryterium *„zero różnic poza polami LLM z jawną wariancją”* jest **spełnione dla kodu uprzęży** (0 różnic bajtowych w 3 przebiegach po 60 dokumentów i w 2 przebiegach z nagraną odpowiedzią LLM) i dla kolejności kluczy (50/50). Wariancja modelu jest osobnym, zmierzonym źródłem różnic (E13), więc testy regresji w produkcie powinny: (1) porównywać bajty wyniku na nagranych odpowiedziach LLM, (2) trzymać wersję promptu i modelu w `versions.json`, (3) rozstrzygnąć jawność `null` i pustych elementów list w kontrakcie v1. **Pewność:** wysoka dla kodu bez OCR; średnia dla potoku z OCR (nie badany). **Otwarte:** determinizm z rapidocr, wielowątkowy odczyt, obsługa `null` w kontrakcie.
