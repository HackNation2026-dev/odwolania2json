# E10: wariant LLM (wejście, prompt, effort), stabilność, odpowiedzi poza schematem

**Wynik nie jest oficjalnym F1.** Miara: F1 przybliżony ewaluatora produkcyjnego (PR #8/#9: TP poprawnie, błędna wartość tylko FP, próg 80%, miara `ratio`),
przedział 95% z bootstrapu po sprawach (2000 losowań, ziarno 20261122), powtórzenia sumowane w obrębie sprawy.
Czas i RSS: pod obciążeniem maszyny (load avg ok. 20–35 na 8 rdzeniach, kilka grup liczy naraz): czasy i RSS ORIENTACYJNE, nie do decyzji.

## Hipoteza i kryterium (z plan + PREREJESTRACJA.md)
H: tekst PDF wystarcza jako wejście LLM; obraz (sam lub dodany) nie poprawia F1 na tyle, by uzasadniać koszt. Wariant zastępuje bazę (tekst, prompt p2), gdy dolna granica
przedziału ΔF1 (sparowane po sprawach) > 0; przy nierozstrzygnięciu wygrywa tańszy, potem prostszy. Różnice < 1 pkt F1 na 25 sprawach to szum.

## Metoda
Zbiór: 25 z 49 spraw rozwojowych (75 dokumentów + 12 negatywów organizatora), wybór warstwowy (ziarno 20261122, `subset_dev.json`); przesiew promptów i effortu na 12 z tych spraw
(`subset_screen.json`, 36 dokumentów). Wszystko przez HTTP do backendu uprzęży (`runner.py` → `POST /batches`, `GET /documents/..`), jedno wywołanie LLM na dokument
(klasa + pola + cytaty), temperatura 0, MiniMax `MiniMax-M3.1-Flash-Preview` (API zwraca `MiniMax-M3.1-Flash`), jedno ponowienie przy odpowiedzi poza schematem.
Błędy sieci/429/timeout (przejściowe) są ponawiane i NIE liczą się jako wynik wariantu (zapis w `*.errors.jsonl`); stałe niepowodzenia (np. 2× pusta/niepoprawna odpowiedź) liczą się jako dokument bez pól.
Skrypt: `lib/runner.py specs/<nazwa>.json`, analiza `lib/analyze_e10.py`. Surowe wiersze: `E10/raw/*.jsonl`, liczby: `E10/wyniki.json`.

## Wyniki
| Wariant | F1 [95% bootstrap po sprawach] | ΔF1 vs baza (sparowane, wspólne powt.) | Zakres | SD F1 między powt. | Poza schematem: 1. próba / po ponowieniu | Tokeny wej./wyj. na dok. | Czas wywołania (mediana) |
|---|---|---|---|---|---|---|---|
| e10-text-p2 | 0.938 [0.910; 0.959] | — | 435 wierszy / 26 spraw (z negatywami); 435/435 wierszy (dok.×powt.), powt. ≤5 z 5 | 0.0129 | 0.011 / 0 | 1286 / 2203 | 13.1 s (p95 dok.: 76.02 s) |
| e10-textimg-p2 | 0.944 [0.919; 0.964] | +0.015 [-0.010; +0.042] (nierozstrzygnięte) | 261 wierszy / 26 spraw (z negatywami); 261/261 wierszy (dok.×powt.), powt. ≤3 z 3 | 0.0252 | 0.042 / 0 | 3866 / 2273 | 13.38 s (p95 dok.: 89.12 s) |
| e10-image-p2 | 0.890 [0.855; 0.920] | -0.039 [-0.076; -0.005] (base>cand) | 245 wierszy / 26 spraw (z negatywami); 245/261 wierszy (dok.×powt.), powt. ≤3 z 3, 16 wierszy czeka na ponowienie po błędzie sieci | 0.0164 | 0.057 / 0 | 1823 / 2793 | 15.26 s (p95 dok.: 92.48 s) |
| e10-text-p1 | 0.751 [0.662; 0.847] | -0.157 [-0.257; -0.038] (base>cand) | 43 wierszy / 12 spraw (z negatywami); 43/108 wierszy (dok.×powt.), powt. ≤2 z 3, 65 wierszy czeka na ponowienie po błędzie sieci | 0.0087 | 0.070 / 0 | 738 / 2023 | 12.73 s (p95 dok.: 107.53 s) |
| e10-text-p3 | 0.921 [0.881; 0.951] | +0.014 [-0.027; +0.066] (nierozstrzygnięte) | 108 wierszy / 12 spraw (z negatywami); 108/108 wierszy (dok.×powt.), powt. ≤3 z 3 | 0.0214 | 0.018 / 0 | 1341 / 2474 | 15.81 s (p95 dok.: 65.07 s) |
| e10-effort-low | 0.942 [0.931; 0.954] | +0.036 [-0.004; +0.095] (nierozstrzygnięte) | 108 wierszy / 12 spraw (z negatywami); 108/108 wierszy (dok.×powt.), powt. ≤3 z 3 | 0.005 | 0.000 / 0 | 1195 / 915 | 16.28 s (p95 dok.: 40.52 s) |
| e10-effort-high | 0.940 [0.910; 0.963] | +0.033 [-0.006; +0.080] (nierozstrzygnięte) | 108 wierszy / 12 spraw (z negatywami); 108/108 wierszy (dok.×powt.), powt. ≤3 z 3 | 0.0043 | 0.000 / 0 | 1121 / 1535 | 8.64 s (p95 dok.: 92.33 s) |

Baza `e10-text-p2`: F1 0.938 [0.910; 0.959]; per klasa: odwolanie 0.927, pelnomocnictwo 0.921, przelew 0.9919; zgodność JSON między 5 powtórzeniami: identyczny JSON w 39% dokumentów,
średnia zgodność liści 0.768; rewizja modelu zwrócona przez API: {'MiniMax-M3.1-Flash': 411}. Rozrzut przy innych miarach podobieństwa: {'ratio': 0.9378, 'token_sort_ratio': 0.9378, 'partial_ratio': 0.9378}.
Dla porównania `leaf_f1` uprzęży (multizbiór liści, bez progu 80%): 0.9147 (ewaluator produkcyjny: 0.9378); różnica wynika z progu 80% dla nazw/tytułów i dopasowania list element do elementu.

**Test długiego dokumentu:** 10 długich odwołań (10–11 str.), 3 powt.: pełny tekst F1 0.962 [0.936; 0.978], tylko 2 pierwsze strony 0.973 [0.956; 0.985], ΔF1 (2 str. − pełny) +0.011 [-0.016; +0.047] (nierozstrzygnięte); pola tracące ≥0,2 F1: brak; tylko 2.6% zwróconych pól (583) pochodzi ze strony ≥3.

## Jak to działa i dlaczego tak wyszło
Wejście `text` to tekst PDF ze znacznikami stron; `image` to JPEG 100 dpi kolejnych stron (do 12), `text_image` oba naraz. Obraz sam traci przede wszystkim na polach cyfrowych (porównanie na 3 wspólnych powtórzeniach: numer_bzp −0,27, z_rachunku −0,22, numer_ted −0,18, na_rachunek −0,10 F1; 100 dpi to mało dla długich ciągów cyfr) i rzadko daje `complete` (16 z 245 wierszy), bo cytat modelu z obrazu ma mniej jednoznaczne kotwice w słowach PDF (kotwiczenie działa na tekście PDF/OCR, więc status `partial` i kod `evidence_unanchored`).
Dodanie obrazu do tekstu kosztuje ok. 3× więcej tokenów wejściowych przy różnicy F1 w granicach szumu. Prompt p1 (krótki, bez wzorów organizatora) jest wyraźnie gorszy, p3 (dodatkowe reguły) nie poprawia.
Wyjście modelu to głównie rozumowanie (ok. 2 tys. tokenów na dokument) — to ono, nie wejście, wyznacza czas wywołania.

## Ograniczenia
Mała próbka (25 spraw, w tym 10 z długim odwołaniem; przesiew 12 spraw); powtórzenia w obrębie jednej sprawy nie są niezależne (bootstrap po sprawach to uwzględnia).
Test „fakt po stronie 3” nie ma tu mocy: w tych danych prawie wszystkie pola leżą na stronach 1–2, więc obcięcie do 2 stron niczego nie traci; syntetyczny test faktu osadzonego późno nie został wykonany.
Sieć była niedostępna ok. 40 min (05:00–05:12) i wcześniej seriami (ConnectError); dotknięte wiersze zostały ponowione, nie zapisane jako wyniki.
Wszystkie wywołania biegły pod obciążeniem; czasy nie nadają się do decyzji.

## Wniosek decyzyjny
Zgodnie z regułą z prerejestracji: baza = tekst + prompt p2, jedno wywołanie na dokument; wariant zastępuje ją tylko przy dodatniej dolnej granicy ΔF1.
- `e10-textimg-p2`: nierozstrzygnięte (ΔF1 +0.015, 95% [-0.010; +0.042]).
- `e10-image-p2`: base>cand (ΔF1 -0.039, 95% [-0.076; -0.005]).
- `e10-text-p3`: nierozstrzygnięte (ΔF1 +0.014, 95% [-0.027; +0.066]).
- `e10-text-p1`: base>cand (ΔF1 -0.157, 95% [-0.257; -0.038]).
- `e10-effort-low`: nierozstrzygnięte (ΔF1 +0.036, 95% [-0.004; +0.095]).
- `e10-effort-high`: nierozstrzygnięte (ΔF1 +0.033, 95% [-0.006; +0.080]).
Wybór wejścia dla skanów rozstrzyga E11, wybór modelu E18.

## Stan końcowy (finalizacja z replayu, bez wywołań API; 22.11.2026)
- Limit MiniMax wyczerpany; po ostatnim przebiegu nie wołano API. Liczby wyżej to wyłącznie zapisane odpowiedzi.
- Wiersze z błędem sieci/limitu (`llm_unavailable`, `llm_rate_limit`) NIE weszły do liczb: 539 wierszy w `E10/raw/*.errors.jsonl` (odrzucone przy ponowieniu) oraz 81 wierszy wciąż niepowtórzonych w `*.jsonl` (image-p2 16, text-p1 65), odfiltrowanych przez `analyze.py::_transient`.
- **Niepełne:** `e10-image-p2` ma 245 z 261 wierszy (16 brakuje); `e10-text-p1` tylko 43 z 108 (12 spraw × 3 powt. planowane); wynik p1 (0.751) opiera się na tej mniejszej, niepełnej próbce, więc jest wiarygodny słabiej niż reszta.
- **effort low/high:** wykonane, 12 spraw (36 dok.) × 3 powt. = 108 wierszy każdy: low 0.942, high 0.940 wobec bazy z tych samych spraw; ΔF1 +0.036 [-0.004; +0.095] i +0.033 [-0.006; +0.080], nierozstrzygnięte. Uwaga: nie weryfikowano, że model stosuje `effort` (tokeny wyjściowe: low 915, high 1535, baza 2528 na dok., czyli oba warianty mają mniej niż baza; kierunek nie jest monotoniczny low<high, więc ustawienie nie wygląda na kontrolę długości rozumowania).
- Powyższa tabela jest regenerowana z `lib/make_readmes.py`; tekst „brak wyniku” w starszych wersjach dotyczył stanu sprzed ukończenia tych przebiegów.
