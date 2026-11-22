"""Składa E10/E11/E17/E18 README.md z wyniki.json (liczby tylko z danych; narracja i wnioski dopisane w szablonach poniżej).

Uruchomienie po analizach: analyze_e10.py, analyze_e11.py, analyze_e17.py, analyze_e18.py, potem ten skrypt.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import analyze as A

L = A.LLM_E2E
LOAD = "pod obciążeniem maszyny (load avg ok. 20–35 na 8 rdzeniach, kilka grup liczy naraz): czasy i RSS ORIENTACYJNE, nie do decyzji"


def J(path: str) -> Any:
    p = L / path
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def ci(v: dict[str, Any]) -> str:
    c = v.get("ci95")
    return f"{v['f1']:.3f} [{c[0]:.3f}; {c[1]:.3f}]" if c else f"{v['f1']:.3f}"


def pr(p: dict[str, Any] | None) -> str:
    if not p:
        return "—"
    return f"{p['delta']:+.3f} [{p['ci95'][0]:+.3f}; {p['ci95'][1]:+.3f}] ({p['decision']})"


def progress(exp: str, name: str, planned_docs: int, planned_reps: int) -> str:
    recs = A.raw(exp, name)
    reps = max((r["rep"] for r in recs), default=0)
    done = len(recs)
    pend = A.transient_pending(exp, name)
    return f"{done}/{planned_docs * planned_reps} wierszy (dok.×powt.), powt. ≤{reps} z {planned_reps}" + (f", {pend} wierszy czeka na ponowienie po błędzie sieci" if pend else "")


def e10() -> str:
    d = J("E10/wyniki.json")
    plan = {"e10-text-p2": (87, 5), "e10-textimg-p2": (87, 3), "e10-image-p2": (87, 3), "e10-text-p1": (36, 3), "e10-text-p3": (36, 3), "e10-effort-low": (36, 3), "e10-effort-high": (36, 3)}
    rows = []
    for n, v in d["variants"].items():
        if "summary" not in v:
            rows.append(f"| {n} | brak wyniku | | | | | | |")
            continue
        s, ll = v["summary"], v["summary"]["llm"]
        rows.append(f"| {n} | {ci(s)} | {pr(v.get('paired_vs_base'))} | {s['docs']} wierszy / {s['cases']} spraw (z negatywami); {progress('E10', n, *plan[n])} | {s['rep_f1_sd']} | "
                    f"{ll['schema_first_bad_rate']:.3f} / {ll['schema_final_bad']} | {ll['input_tokens_per_doc']} / {ll['output_tokens_per_doc']} | {ll['latency_median_s']} s (p95 dok.: {ll['doc_wall_p95_s']} s) |")
    lg = d.get("long_document")
    lgtxt = "brak wyniku"
    if lg:
        lgtxt = (f"{lg['docs']} długich odwołań (10–11 str.), {lg['reps']} powt.: pełny tekst F1 {ci(lg['full'])}, tylko 2 pierwsze strony {ci(lg['first_2_pages'])}, "
                 f"ΔF1 (2 str. − pełny) {pr(lg['paired'])}; pola tracące ≥0,2 F1: {lg['fields_lost_ge_0.2_f1'] or 'brak'}; tylko {lg['share_of_returned_fields_from_page_ge_3']*100:.1f}% "
                 f"zwróconych pól ({lg['returned_fields']}) pochodzi ze strony ≥3.")
    base = d["variants"]["e10-text-p2"]["summary"]
    return f"""# E10: wariant LLM (wejście, prompt, effort), stabilność, odpowiedzi poza schematem

**Wynik nie jest oficjalnym F1.** Miara: F1 przybliżony ewaluatora produkcyjnego (PR #8/#9: TP poprawnie, błędna wartość tylko FP, próg 80%, miara `ratio`),
przedział 95% z bootstrapu po sprawach (2000 losowań, ziarno 20261122), powtórzenia sumowane w obrębie sprawy.
Czas i RSS: {LOAD}.

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
{chr(10).join(rows)}

Baza `e10-text-p2`: F1 {ci(base)}; per klasa: {', '.join(f"{k} {v['f1']}" for k, v in base['per_class'].items() if v['f1'] or k != 'obcy')}; zgodność JSON między 5 powtórzeniami: identyczny JSON w {base['stability']['identical_json_rate']*100:.0f}% dokumentów,
średnia zgodność liści {base['stability']['mean_leaf_agreement']}; rewizja modelu zwrócona przez API: {base['llm']['models_returned']}. Rozrzut przy innych miarach podobieństwa: {base['by_similarity']}.
Dla porównania `leaf_f1` uprzęży (multizbiór liści, bez progu 80%): {base['legacy_leaf_f1']} (ewaluator produkcyjny: {base['f1']}); różnica wynika z progu 80% dla nazw/tytułów i dopasowania list element do elementu.

**Test długiego dokumentu:** {lgtxt}

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
{conclusion_e10(d)}
"""


def conclusion_e10(d: dict[str, Any]) -> str:
    v = d["variants"]
    out = []
    for n in ("e10-textimg-p2", "e10-image-p2", "e10-text-p3", "e10-text-p1", "e10-effort-low", "e10-effort-high"):
        p = (v.get(n) or {}).get("paired_vs_base")
        if p:
            out.append(f"- `{n}`: {p['decision']} (ΔF1 {p['delta']:+.3f}, 95% [{p['ci95'][0]:+.3f}; {p['ci95'][1]:+.3f}]).")
    return ("Zgodnie z regułą z prerejestracji: baza = tekst + prompt p2, jedno wywołanie na dokument; wariant zastępuje ją tylko przy dodatniej dolnej granicy ΔF1.\n" + "\n".join(out)
            + "\nWybór wejścia dla skanów rozstrzyga E11, wybór modelu E18.")


def e11() -> str:
    d = J("E11/wyniki.json")

    def c(v: dict[str, Any]) -> str:
        return v["status"] if "status" in v else f"{ci(v)} (n={v['docs']}; tech. błędów {sum(v['technical_errors'].values())}; {v['input_tokens_per_doc']}/{v['output_tokens_per_doc']} tok.)"

    names = {"skan": "skan (cały dokument jako obraz)", "mieszany": "mieszany (str. 1 tekst, reszta skan)", "s2": "S2 (dane tylko w obrazie na str. tekstowej)", "s5": "S5 (poprawny obraz, błędna niewidoczna warstwa)"}
    t = d["text"]
    trows = [f"| {n} | {c(v['rep1'])} | {c(v['all_reps']) if v['all_reps'] else '—'} |" for n, v in t.items()]
    srows = []
    for k, label in names.items():
        for n, v in d["scan"][k].items():
            srows.append(f"| {label} | {n} | {c(v)} |")
    agg = [f"| {n} | {c(v)} |" for n, v in d["scan_all_nontext"].items()]
    prow = [f"| {k} | {pr(v)} | {v['docs'] if v else '—'} |" for k, v in d["paired"].items()]
    prog = "; ".join(f"{n}: {progress('E11', n, *pl)}" for n, pl in (("e11-scan-B", (150, 1)), ("e11-scan-C", (150, 1)), ("e11-scan-D", (150, 1)), ("e11-scan-Balways", (75, 1)), ("e11-DM3-text", (87, 1)), ("e11-DM3-scan", (150, 1))))
    dm = J("E11/wyniki_dm3.json")
    return f"""# E11: ścieżka pionowa end-to-end przez HTTP: warianty A, B, C, D, dolna granica „sam regex”, ablacje

**Wynik nie jest oficjalnym F1.** F1 przybliżony ewaluatora produkcyjnego (po PR #8/#9), przedział 95% z bootstrapu po sprawach (ziarno 20261122); porównania sparowane po sprawach.
Czas i RSS: {LOAD}. Zbiór kontrolny nietknięty w tym eksperymencie.

## Hipoteza i kryterium
H: LLM na tekście PDF (A) wystarcza dla dokumentów elektronicznych; skany wymagają OCR (B) albo obrazu (C, D); „sam regex” jest tylko dolną granicą.
Reguła (prerejestracja): wariant zastępuje inny, gdy dolna granica przedziału ΔF1 (sparowane) > 0; przy nierozstrzygnięciu tańszy, potem prostszy. Wynik osobno dla każdego typu wejścia, nie jedna liczba.

## Warianty
- **rules**: router regułowy + ekstraktor regułowy (bez LLM); `rules+OCR` na skanach (rapidocr, 200 dpi). Dolna granica.
- **A**: tekst warstwy PDF (pdfium) → LLM (1 wywołanie). Na skanie bez warstwy tekstu: jawny `technical_error/ocr_unavailable`.
- **B**: A + OCR rapidocr 200 dpi stron bez tekstu (`if_needed`); `B_ocr_always`: OCR każdej strony (tylko mieszany/S2/S5).
- **C**: tylko obrazy stron (JPEG 100 dpi, do 12) → LLM; bez OCR, więc cytaty nie mają kotwic (`partial`).
- **D**: tekst (PDF lub OCR) + obrazy stron → LLM.
- **Ablacje na odtworzonych odpowiedziach LLM** (replay, bez wywołań): `A+regex_override` (regex nadpisuje przy rozbieżności pól o stałym formacie), `A+regex_fill` (regex tylko uzupełnia brak), `A_replay` (kontrola: powtórka bez regexu = A, rep. 1).
- Model: MiniMax-M3.1-Flash-Preview (baza z E10), prompt p2, 1 powtórzenie dla skanów (5 dla A na tekście z E10).

## Zakres wykonania
Skany: 25 spraw z podzbioru (75 skanów, 25 mieszanych, 25 S2, 25 S5; zestaw grupy A, tylko sprawy rozwojowe). {prog}. Wiersze z błędem sieci czekają na ponowienie i nie liczą się jako wynik.

## Wyniki: wejście tekstowe (oryginały PDF; 25 spraw + 12 negatywów)
| Wariant | F1, powt. 1 | F1, wszystkie powt. |
|---|---|---|
{chr(10).join(trows)}

## Wyniki: wejścia nietekstowe (jedno powtórzenie)
| Typ wejścia | Wariant | F1 [95%] (n dok.; błędy tech.; tokeny wej./wyj.) |
|---|---|---|
{chr(10).join(srows)}

Razem skan+mieszany+S2+S5:

| Wariant | F1 [95%] |
|---|---|
{chr(10).join(agg)}

## Porównania sparowane (ΔF1 = drugi − pierwszy, bootstrap po sprawach)
| Para | ΔF1 [95%] | dok. |
|---|---|---|
{chr(10).join(prow)}

## Jak to działa i dlaczego tak wyszło
{narrative_e11(d)}

## Ograniczenia
Mała próbka: 25 spraw, 1 powtórzenie na wariant skanowy; skany są syntetyczne (zestaw grupy A: rasteryzacja + szum/rozmycie/kąt/JPEG, ten sam generator szablonów), bez fizycznych skanów, pieczęci, zdjęć.
S2/S5 powstały algorytmicznie; S5 ma przesunięte cyfry w niewidocznej warstwie (+3 mod 10). Wszystkie warianty używają jednego modelu (M3.1-Flash-Preview); model M3 z E18 sprawdzono tylko w D (patrz niżej).
Ewaluator: miara przybliżona, próg 80% (miara `ratio`), bez oficjalnej definicji (U-Q01). Sieć niedostępna ok. 40 min (05:00–05:12) i seriami wcześniej; dotknięte wiersze ponowione, nie zapisane jako wyniki.
Czas/RSS pod obciążeniem (nie do decyzji); szczytowy RSS serwera zapisany w `E11/raw/*.meta.json` (`peak_rss_mb`, limit 14 GB: `systemd-run`).

## Wniosek decyzyjny
{conclusion_e11(d)}
"""


def _p(d: dict[str, Any], k: str) -> str:
    v = d["paired"].get(k)
    return f"{k}: {pr(v)}" if v else f"{k}: brak"


def narrative_e11(d: dict[str, Any]) -> str:
    return ("Warstwa tekstowa PDF jest wystarczająca dla dokumentów elektronicznych, a regexy same dają tylko ok. jedną czwartą F1 (pola formatowe: NIP, KRS, numery; role, nazwy, czynność wymagają LLM). "
            "Na skanach bez OCR wariant A kończy jawnym `ocr_unavailable` (F1 0 przez brak pliku, nie przez zmyślone dane). S5 pokazuje ryzyko ufania warstwie tekstowej: A i B (OCR tylko dla stron bez tekstu) "
            "czytają błędne cyfry, a warianty z obrazem (C, D) je omijają; `B_ocr_always` sprawdza, czy OCR każdej strony to naprawia. "
            "Wariant D łączy kotwice z tekstu/OCR (statusy `complete`) z obrazem (odporność na błędy odczytu), kosztem ok. 3× tokenów wejściowych.")


def conclusion_e11(d: dict[str, Any]) -> str:
    lines = [f"- {_p(d, k)}" for k in d["paired"] if d["paired"][k]]
    dm = J("E11/wyniki_dm3.json")
    extra = ""
    if dm:
        extra = "\n\nKandydat końcowy D + MiniMax-M3: " + json.dumps(dm, ensure_ascii=False)
    return "Decyzje wynikają z dolnych granic przedziałów ΔF1 w tabeli sparowanej (zob. wyżej), osobno dla typu wejścia:\n" + "\n".join(lines) + extra


def e17() -> str:
    d = J("E17/wyniki.json")
    rows = []
    for label, v in d.items():
        if label == "ambiguous":
            continue
        for pol in ("unanchored_null", "no_export_partial", "rules_fallback"):
            x = v[pol]
            rows.append(f"| {label} | {pol} | {x['docs']} / zmienione {x['docs_changed']} | {ci(x['default'])} | {ci(x['variant'])} | {pr(x['paired'])} |")
    am = d.get("ambiguous", {})
    return f"""# E17: polityka null i eksportu a F1

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
{chr(10).join(rows)}

`ambiguous`: router LLM zwrócił `ambiguous` w {am.get('llm_router_ambiguous_docs_text_p2')} z {am.get('llm_router_docs')} wierszy (wejście tekstowe, M3.1-Flash), więc polityka „najlepsza klasa” nie ma tu czego zmieniać: gdy LLM mówi `ambiguous`, nie ma pól do eksportu,
a wymuszony wybór klasy w prompcie nie był osobno testowany. Router regułowy kończy `ambiguous` dla {am.get('rules_router_ambiguous_docs')} dokumentów (w tym {am.get('of_which_expected_foreign')} obcych); wśród {am.get('rules_ambiguous_positives')} pozytywów
najwyżej oceniona klasa była poprawna w {am.get('rules_top_class_correct_among_ambiguous_positives')} (to trafność klasy, nie F1: ekstrakcji z wymuszoną klasą uprząż nie wykonuje).

## Jak to działa i dlaczego tak wyszło
Pole niezakotwiczone to wartość wskazana przez LLM, której cytatu nie da się jednoznacznie odnaleźć w słowach PDF/OCR (kotwiczenie na znakach, zero „zgadywania”). Wartość bywa poprawna, więc zerowanie jej obniża TP (kolumna `unanchored_null`).
Wyłączenie `partial` z eksportu usuwa duży odsetek poprawnych pól, bo `partial` to w tej uprzęży także status poprawnych dokumentów z drobną flagą (np. jedno niezakotwiczone pole).
Wynik reguł zamiast `{{}}` przy awarii LLM dodaje tylko pola formatowe, ale to dodatni przyrost, gdy awaria się zdarza.

## Ograniczenia
`unanchored_null` jest liczone na zapisanych kandydatach (`t3/candidates.json`); kotwiczenie w uprzęży jest prostsze niż docelowe (§4.5), więc odsetek niezakotwiczonych może być inny w produkcie.
Awarie LLM w danych to głównie `llm_invalid_response` (pusta lub niepoprawna odpowiedź 2×); polityka `rules_fallback` dotyczy tylko takich dokumentów (liczba zmienionych w tabeli): przedział jest wąski z powodu małej liczby zmian.
Brak testu `ambiguous`→klasa z wymuszeniem w prompcie. Mała próbka (25 spraw).

## Wniosek decyzyjny
{conclusion_e17(d)}
"""


def conclusion_e17(d: dict[str, Any]) -> str:
    out = []
    for label, v in d.items():
        if label == "ambiguous":
            continue
        for pol, name in (("unanchored_null", "zerowanie pola bez kotwicy"), ("no_export_partial", "brak eksportu dla `partial`"), ("rules_fallback", "wynik reguł przy awarii LLM")):
            p = v[pol]["paired"]
            verdict = ("polityka zmienia wynik na lepszy" if p["ci95"][0] > 0 else "polityka pogarsza F1" if p["ci95"][1] < 0 else "bez rozstrzygnięcia")
            out.append(f"- {label}: {name}: ΔF1 {p['delta']:+.3f} [{p['ci95'][0]:+.3f}; {p['ci95'][1]:+.3f}] → {verdict}.")
    return ("\n".join(out) + "\n\nRekomendacja: bbox dowodu nie powinien decydować o treści ocenianego JSON: niezakotwiczone pole wyeksportować z wartością i oznaczyć do sprawdzenia (`review_required`), o ile liczby powyżej pokazują stratę przy zerowaniu; "
            "`partial` eksportować; przy awarii LLM rozważyć wynik reguł jako jawnie oznaczony wynik częściowy (nigdy cichą podmianę z cache; decyzja zgodna z architekturą §9.1 wymaga ADR).")


def e18() -> str:
    d = J("E18/wyniki.json")
    rows = []
    for g in ("models", "effort"):
        for k, v in d[g].items():
            if "status" in v:
                rows.append(f"| {k} | brak wyniku | | | | | |")
                continue
            rows.append(f"| {k} | {ci(v)} | {pr(v['paired_vs_base'])} | {v['docs']} wierszy, powt. {v['reps_used']} | {v['tokens_in_per_doc']} / {v['tokens_out_per_doc']} (baza {v['base_tokens_out_per_doc']}) | "
                        f"{v['latency_median_s_UNDER_LOAD']} s (baza {v['base_latency_median_s_UNDER_LOAD']} s) | {'TAK' if v['rule_replaces_base'] else 'nie'} |")
    return f"""# E18: wybór modelu LLM (i ustawienia effort)

**Wynik nie jest oficjalnym F1.** Ten sam prompt p2, to samo wejście (tekst PDF), te same sprawy; ewaluator produkcyjny; bootstrap po sprawach (ziarno 20261122).
Czas: {LOAD}. Model „bazowy” to `MiniMax-M3.1-Flash-Preview` (API zwraca `MiniMax-M3.1-Flash`).

## Zakres: inny dostawca
Zlecenie dopuszcza tylko klucz MiniMax (`MINIMAX_KEY_FILE`). W katalogu domowym są pliki z kluczami innych usług, ale NIE zostały użyte: spoza zakresu zlecenia, a zgodność dostawcy z wymogiem UE/EOG rozstrzyga ADR-002. Dlatego E18 porównuje modele MiniMax dostępne na jednym kluczu
(`MiniMax-M3`, `M2.7`, `M2.5`; `MiniMax-M3.1` dało HTTP 400, `M2.1` i `M2` HTTP 404) oraz ustawienia `effort` bazowego modelu. Porównania z innymi rodzinami (mniejszy otwarty model z UE) pozostają otwarte.

## Hipoteza i reguła (prerejestracja pkt 6)
Mniejszy lub tańszy model zastępuje bazę, gdy dolna granica ΔF1 (model − baza) > −0,02 oraz tokeny wyjściowe na dokument i mediana czasu wywołania nie są większe od bazy. Rozmiar parametrów nie jest ujawniony przez API; „tańszy” = mniej tokenów i krótszy czas (cennika nie znamy).

## Metoda
Modele: 25 spraw rozwojowych (75 dokumentów pozytywnych; negatywów nie uruchamiano), 2 powtórzenia, tekst + p2, temperatura 0. Baza do porównania: `e10-text-p2` na tych samych dokumentach i powtórzeniach 1–2. Effort: `low`/`high` na 12 sprawach (36 dok.), 3 powtórzenia (z E10).
API przyjmuje `output_config.effort`, ale nie weryfikowaliśmy, czy model je uwzględnia (sprawdzić po różnicy tokenów).

## Wyniki
| Model / ustawienie | F1 [95%] | ΔF1 vs baza (sparowane) | Zakres | Tokeny wej./wyj. na dok. | Czas wywołania (mediana) | Reguła: zastępuje bazę |
|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## Jak to działa i dlaczego tak wyszło
{narrative_e18(d)}

## Ograniczenia
Jeden dostawca; 25 spraw (przesiew effortu na 12); 2 powtórzenia modeli; negatywów nie uruchamiano, więc nie mierzymy fałszywych pozytywów routera dla modeli; aliasy MiniMax mogą zmienić rewizję (zapisane nazwy zwrócone przez API: patrz `E18/wyniki.json`).
Czas pod obciążeniem (nie do decyzji); tokeny są wiążące. Brak ceny, więc „koszt” = tokeny.

## Wniosek decyzyjny
{conclusion_e18(d)}
"""


def narrative_e18(d: dict[str, Any]) -> str:
    m3 = d["models"].get("M3", {})
    if "status" in m3:
        return "Brak wyniku dla M3."
    return (f"M3 zwraca ok. {m3['tokens_out_per_doc']} tokenów wyjściowych na dokument wobec {m3['base_tokens_out_per_doc']} u bazy: nie generuje długiego rozumowania, więc jest szybszy i tańszy w tokenach, "
            "a F1 na tych sprawach nie jest gorszy. Czas wywołania wyznaczają tokeny wyjściowe (rozumowanie), nie wejściowe.")


def conclusion_e18(d: dict[str, Any]) -> str:
    win = [k for g in ("models", "effort") for k, v in d[g].items() if "status" not in v and v["rule_replaces_base"]]
    return (f"Reguła z prerejestracji wskazuje: {', '.join(win) if win else 'zostaje baza (żaden wariant nie spełnia reguły)'}. "
            "Pewność umiarkowana: jeden dostawca, 25 spraw, 2 powtórzenia; przed ADR sprawdzić M3 w wariancie końcowym E11 (D) i potwierdzić licencję/lokalizację modelu w ADR-002.")


def podsumowanie() -> str:
    e10d, e11d, e17d, e18d = J("E10/wyniki.json"), J("E11/wyniki.json"), J("E17/wyniki.json"), J("E18/wyniki.json")
    v = e10d["variants"]
    base = v["e10-text-p2"]["summary"]

    def vr(n: str) -> str:
        x = v.get(n, {})
        return "brak" if "summary" not in x else f"{x['summary']['f1']:.3f}, Δ {pr(x.get('paired_vs_base'))}"

    def sc(k: str, n: str) -> str:
        c = e11d["scan"][k][n]
        return "brak" if "status" in c else f"{c['f1']:.3f} (n={c['docs']})"

    m3 = e18d["models"].get("M3", {})
    m27 = e18d["models"].get("M2.7", {})
    m25 = e18d["models"].get("M2.5", {})
    un = e17d["tekst, wariant A (5 powtórzeń)"]
    dm = J("E11/wyniki_dm3.json")
    ctrl = (L / "KONTROLNY.md").read_text(encoding="utf-8") if (L / "KONTROLNY.md").is_file() else "Zbiór kontrolny: NIE wykonano (patrz WYBOR.md/KONTROLNY.md, jeśli istnieją)."
    return f"""# Podsumowanie grupy C (E10, E11, E17, E18)

Wszystkie liczby: F1 przybliżony (ewaluator produkcyjny po PR #8/#9, próg 80%), przedział 95% z bootstrapu po sprawach, **nie oficjalny F1**. Próbka: 25 z 49 spraw rozwojowych (przesiew 12). Czasy i RSS zebrane pod
obciążeniem maszyny (load avg 20–35), **niewiążące**; do decyzji o czasie służy osobne ciche okno. Klucz API: tylko MiniMax; nie zapisany w wynikach (kontrola grepem: `WYCIEK.md`). Szczegóły i tabele w `E##/README.md`; pełne
specyfikacje w `specs/`, surowe wiersze w `E##/raw/`. Sieć zawodziła seriami (w tym ok. 40 min 05:00–05:12); wiersze z błędem sieci ponawiane, nie zapisywane jako wyniki.

| E | Wynik | Decyzja | Pewność | Co otwarte |
|---|---|---|---|---|
| E10 | tekst p2: {ci(base)} (5 powt., SD między powt. {base['rep_f1_sd']}); tekst+obraz {vr('e10-textimg-p2')}; sam obraz {vr('e10-image-p2')}; prompt p1 {vr('e10-text-p1')}; p3 {vr('e10-text-p3')}; effort low {vr('e10-effort-low')}; high {vr('e10-effort-high')}; poza schematem 1. próba {base['llm']['schema_first_bad_rate']:.3f}; identyczny JSON w {base['stability']['identical_json_rate']*100:.0f}% dok. | wejście: tekst PDF, prompt p2, 1 wywołanie/dok.; obraz tylko jako dodatek tam, gdzie brak tekstu (E11) | średnia (25 spraw; p1/p3/effort tylko 12) | test faktu osadzonego na str. 3 (dane go nie zawierają); weryfikacja effortu; kontrola 9 stałych niepowodzeń odpowiedzi |
| E11 | tekst: rules {e11d['text']['rules']['rep1']['f1']:.3f}, A {e11d['text']['A']['rep1']['f1']:.3f}, C {e11d['text']['C']['rep1']['f1']:.3f}, D {e11d['text']['D']['rep1']['f1']:.3f}; skan: A {sc('skan','A')}, B {sc('skan','B')}, C {sc('skan','C')}, D {sc('skan','D')}, rules+OCR {sc('skan','rules+OCR')}; S5: A {sc('s5','A')}, B {sc('s5','B')}, C {sc('s5','C')}, D {sc('s5','D')}; S2: B {sc('s2','B')}, D {sc('s2','D')} | patrz E11/README (sparowane ΔF1 per typ); warstwa tekstowa nie jest wiarygodna (S5) bez obrazu lub kontroli | średnia/niska na skanach (syntetyczne, 1 powt.) | fizyczne skany; D z pełnym zakresem; kontrolny jeden przebieg |
| E17 | zerowanie pola bez kotwicy: ΔF1 {pr(un['unanchored_null']['paired'])} (tekst); brak eksportu `partial`: {pr(un['no_export_partial']['paired'])}; wynik reguł przy awarii LLM: {pr(un['rules_fallback']['paired'])}; `ambiguous` LLM: 0 z 435 | nie zerować pól z braku kotwicy; eksportować `partial` z flagą; bbox nie decyduje o treści JSON | wysoka dla kierunku (duże ΔF1), niska dla wielkości (uprząż ≠ produkt) | `ambiguous`→wymuszona klasa; kotwiczenie docelowe |
| E18 | M3: {('%.3f' % m3['f1']) + ' Δ ' + pr(m3['paired_vs_base']) if m3 and 'status' not in m3 else 'brak'} (tok. wyj. {m3.get('tokens_out_per_doc')} vs {m3.get('base_tokens_out_per_doc')}); M2.7: {('%.3f' % m27['f1']) + ' Δ ' + pr(m27['paired_vs_base']) if m27 and 'status' not in m27 else 'brak'}; M2.5: {('%.3f' % m25['f1']) + ' Δ ' + pr(m25['paired_vs_base']) if m25 and 'status' not in m25 else 'brak'} | reguła z prerejestracji: patrz E18/README (M3 spełnia, jeśli tabela mówi TAK) | niska/średnia (jeden dostawca, 2 powt.) | inny dostawca (klucz poza zakresem), M3 w pełnym wariancie D, negatywy, licencja i lokalizacja (ADR-002) |

D + MiniMax-M3 (kandydat końcowy): {json.dumps(dm, ensure_ascii=False) if dm else 'brak wyniku w chwili zapisu'}.

{ctrl}
"""


if __name__ == "__main__":
    (L / "E10" / "README.md").write_text(e10(), encoding="utf-8")
    (L / "E11" / "README.md").write_text(e11(), encoding="utf-8")
    (L / "E17" / "README.md").write_text(e17(), encoding="utf-8")
    (L / "E18" / "README.md").write_text(e18(), encoding="utf-8")
    (L / "PODSUMOWANIE.md").write_text(podsumowanie(), encoding="utf-8")
    print("README zapisane")
