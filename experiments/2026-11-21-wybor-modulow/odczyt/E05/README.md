# E05: kotwiczenie cytatów do słów i bbox

Polecenie (z korzenia `experiments/2026-11-21-wybor-modulow`, ok. 30 min pod obciążeniem): `../../.venv-exp/bin/python odczyt/E05/e05_anchor.py` → `e05-wyniki.json`; diagnoza błędnych kotwic OCR: `odczyt/E05/e05_diag_ocr.py` → `e05-diag-ocr.json`.
Moduł testowany: `stages.WordAnchorResolver` uprzęży (dopasowanie na znakach po NFKC+casefold, białe znaki zwinięte, zero trafień = `unanchored`, więcej niż jedno = `ambiguous`).

## Hipoteza i kryterium (plan 0.2)

Cytat wartości (z LLM) daje się zakotwiczyć w słowach PDF i OCR z poprawnym bbox: **≥ 0,95 zakotwiczonych jednoznacznie i zero „zgadniętych”**. Zamiast „IoU z wzorcem”: test obiegowy (wytnij bbox, odczytaj, porównaj z cytatem), narożniki po `/Rotate`.

## Metoda

**Cytaty są syntetyczne, nie odpowiedzi LLM** (E05 nie woła LLM): wartość referencyjna → przedział słów, w którym leży w tekście (kwota i data: słowo = forma; identyfikatory: cyfry; tekst: `squash`), cytat = tekst tych słów. Cztery postaci: `exact`, `upper` (wielkie litery), `nbsp` (spacje nierozdzielające), `context` (z jednym słowem kontekstu po obu stronach); każda z numerem strony i bez.
A) warstwa tekstowa: 147 dokumentów rozwojowych, 1277 przypadków (pole × dokument). B) OCR: 36 skanów (12 spraw, jak E02), 150 dpi A4, 311 przypadków, w których wartość występuje w słowach OCR; „prawda” = bbox tych samych słów w warstwie tekstowej oryginału (ten sam układ strony, przeliczenie pikseli na punkty jak w harnessie `ocr_page_to_reading`).
C) obieg: render → wycięcie bbox → OCR wycinka → porównanie z cytatem (CER po squash ≤ 0,2). D) obrót: 12 dokumentów, `/Rotate` 90/180/270 wymuszony, prawda = narożniki strony nieobróconej po transformacji.

## Wynik

| Ścieżka / cytat | n | zakotwiczone | niejednoznaczne (duplikaty) | niezakotwiczone | bbox błędny (IoU < 0,5 z prawdą) |
|---|---|---|---|---|---|
| A. PDF, `exact`, ze stroną | 1277 | **1098 (86,0%)** | 179 (14,0%) | 0 | **0** (IoU średnie 1,000) |
| A. PDF, `exact`, bez strony | 1277 | 1039 (81,4%) | 238 (18,6%) | 0 | 0 |
| A. PDF, `upper` / `nbsp` | 1277 | jak `exact` | jak `exact` | 0 | 0 |
| A. PDF, `context` | 1277 | 1277 (100%) | 0 | 0 | (patrz niżej: obrys obejmuje kontekst, IoU względem samej wartości 0,35) |
| B. OCR, `exact`, ze stroną | 311 | 271 (87,1%) | 40 (12,9%) | 0 | **44 z 271 (16%)**; poprawnie 227 (73% przypadków) |
| B. OCR, `exact`, bez strony | 311 | 254 | 57 | 0 | 43 z 254 |
| B. OCR, `context` | 311 | 311 | 0 | 0 | 290 (obrys większy niż wartość, patrz niżej) |

Niezależna kontrola A: wyszukiwanie tekstu w pdfium (`textpage.search`, bez moich słów) zgadza się z bbox kotwicy w 695 z 695 sprawdzonych przypadków (IoU ≥ 0,5).
C. Obieg bbox → OCR → cytat (CER ≤ 0,2): warstwa PDF 103 z 124 (83,1%), skany 189 z 200 (94,5%).
D. Obrót: `/Rotate` 90: 87 z 92 zakotwiczonych (94,6%), 180: 92/92, 270: 92/92; wśród zakotwiczonych IoU z transformacją narożników min. 0,998, średnie ≥ 0,9997 (zgodnie z E01b).

## Jak to działa i dlaczego tak wyszło

- **Zero zgadywania spełnione** w obu ścieżkach: nie ma przypadku `unanchored`, a kotwica jest przyznawana tylko przy dokładnie jednym trafieniu. Niejednoznaczność (14% PDF) to duplikaty wartości: NIP/KRS/nazwa powtarzają się na stronie (nagłówek, treść, podpis). `Ambiguous` kończy się `review_required`, więc **kryterium ≥ 0,95 zakotwiczonych nie jest spełnione dla samej wartości jako cytatu** (86,0%; 81,4% bez strony).
  Cytat z kontekstem rozstrzyga duplikaty w 100% przypadków, ale obrys obejmuje wtedy słowa kontekstu (metryka „błędny bbox” dla `context` oznacza „za szeroki”, a nie „w złym miejscu”; zawieranie wartości nie było mierzone osobno, więc nie podaję go jako wyniku). Wniosek: prompt LLM musi wymagać cytatu z minimalnym kontekstem **i** kod musi zawężać obrys do wartości w obrębie kontekstu.
- OCR: bbox poprawny w 73% przypadków (84% zakotwiczonych). Diagnoza 40 pierwszych błędnych kotwic (`e05-diag-ocr.json`): 18 z 40 obejmuje wartość w ≥ 90% (obrys „słowa” OCR jest szerszy od wartości: rapidocr zwraca fragmenty linii, np. `KRS 0000…` w jednym polu, szer. 180 vs 57 pt), 17 z 40 nie zachodzi na prawdę (głównie `imie_nazwisko`, `nip`, `krs`, `nazwa`: inne wystąpienie tej samej wartości na stronie niż to, które wskazałem jako prawdę, albo sąsiednia linia). Pierwszej grupy nie traktuję jako „zgadniętej”, drugiej nie umiem odróżnić od błędu prawdy bez ręcznego przeglądu; kryterium dla OCR **nie jest wykazane**.
- Obrót 90°: 5 z 92 cytatów gubi się, bo pdfium po obrocie strony inaczej dzieli znaki na słowa (zgodnie z E01b); wynik jest jawny (`unanchored`), nie błędny.
- Test obiegowy jest słabszy niż ślad tuszu z E01b (99%): nieudane obiegi to puste OCR bardzo krótkich wycinków (`17.06.2026`) i wielowierszowe cytaty, których obrys sumuje linie; to ograniczenie testu, nie dowód błędnego bbox.

## Ograniczenia

- Cytaty syntetyczne: prawdziwy LLM zmienia kolejność, skraca, łączy pola i halucynuje; ten test nie mierzy jego zachowania (to zadanie grup LLM). Dokumenty z jednego generatora.
- Prawda w B pochodzi z tekstu oryginału; wartości obecne wielokrotnie mają kilka prawdziwych miejsc, wybierałem najlepsze IoU (łagodne dla kotwicy).
- Obrót tylko na pdfium (`/Rotate`), nie na skanach obróconych fizycznie (tu E03). Brak testu kolejności czytania przelewów poza E01.
- Próbka OCR 36 dok.; liczby procentowe mają przedział rzędu ±4 pp. Nie jest to oficjalne F1.

## Wniosek decyzyjny

`WordAnchorResolver` jest bezpieczny (0 zgadnięć, 0 błędnych bbox na PDF, 1098/1098 poprawnych) i **odmawia zamiast zgadywać**, ale 14% cytatów-wartości to duplikaty, więc kryterium 0,95 wymaga zmiany sposobu cytowania (kontekst + zawężenie obrysu) i ponownego pomiaru na prawdziwych cytatach LLM. Ścieżka OCR wymaga dopracowania granularności słów (obrys całej linii zamiast wartości). Pewność: wysoka dla PDF, niska dla OCR. Czasy: nie mierzone (niewiążące).
