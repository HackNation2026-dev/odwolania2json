# Ocena architektury etapami i jako całości (Fable)

Data: 2026-11-22. Tryb: tylko odczyt repozytorium, bez wywołań LLM, bez uruchamiania OCR, serwera i testów. Gałąź `kacperpaczos/backlog-from-experiments`, commit `bde8c28`.

Oznaczenia: **[F]** fakt z pliku lub pomiaru, **[W]** moje wnioskowanie. Ścieżki `E##` są względne do `experiments/2026-11-21-wybor-modulow/`. Wszystkie F1 poniżej to F1 przybliżony ewaluatorem zespołu, nie oficjalny.

## A. Werdykt zbiorczy

1. **[F]** Produkt dziś nie rozwiązuje zadania: `apps/backend/odwolania2json/engine.py` to `StubEngine`, który dla każdego PDF zapisuje `{}`. F1 pól produktu wynosi 0.
2. **[F]** Cała wiedza o skuteczności siedzi w uprzęży `harness/` (2716 linii, poza `apps/`, poza bramkami CI), mierzonej na 25 z 49 spraw rozwojowych z jednego generatora szablonów.
3. **[W]** Projekt (pdfium → diagnoza strony → OCR gdy trzeba → jedno wywołanie LLM → normalizacja → serializer) jest właściwy i wystarczający na wysoki F1. Reszta architektury (L, T2, T4, SQLite, API v1, cache, 59 kodów) nie jest potrzebna do wyniku preselekcji.
4. **[W]** Szacunek F1 na ukrytym zbiorze, **pod warunkiem** przeniesienia najlepszego wariantu uprzęży do CLI bez regresji: tekst **0,90–0,96** (pomiar: 0,938 [0,910; 0,959], M3 0,961), skan **0,75–0,95** (pomiar: B 0,902, n=71; D 0,961, n=26, jedno powtórzenie, skany syntetyczne), mieszane **0,88–0,97** (B 0,916, n=24; D 0,980, n=9).
5. **[W]** Bez tego warunku przedział dla wszystkich typów zaczyna się od 0, a dla skanów zostaje na 0 także wtedy, gdy jury zainstaluje tylko `requirements.txt` (OCR jest w osobnym `apps/backend/requirements-ocr.txt`).
6. **[W]** W niepewności dominują kolejno: (a) czy produkt powstanie i odtworzy uprząż, (b) zgodność i dostępność LLM (licencja, UE/EOG, limit klucza: w nocy limit MiniMax został wyczerpany), (c) oficjalny ewaluator, (d) realizm skanów.
7. **[F]** Pojedynczy przebieg ma rozrzut: F1 powtórzeń 0,918–0,956 (`llm-e2e/E10/wyniki.json`, `per_rep_f1`), identyczny JSON tylko w 39% dokumentów. Jury uruchomi raz.
8. **[W]** Zgodność z warunkami formalnymi jest dziś gorsza niż skuteczność: z 27 warunków w macierzy B spełnione kodem i testem są 3, a 10 to wyłącznie deklaracje.
9. **[W]** Największe pojedyncze ryzyko dyskwalifikacji niezależne od F1 to MiniMax: ADR-002 sam odnotował operatora z Singapuru i licencję „Community” (nie OSI), po czym zamknął punkt decyzją zespołu bez dowodu.
10. **Nie da się ocenić z posiadanych danych:** wyniku na zbiorze kontrolnym (licznik użyć 0), fizycznych skanów, dokumentów spoza generatora, czasu na i7/16 GB (`czas/PODSUMOWANIE.md` nie istnieje), instalacji na Windows, innego dostawcy LLM, zachowania oficjalnego ewaluatora wobec `null`, brakującego klucza i braku pliku, oraz punktów za rozmiar modelu (API nie ujawnia liczby parametrów).

## B. Macierz zgodności z warunkami zadania

Status: S = spełniony (kod + test), C = częściowo, N = niespełniony, ? = nieznany. **D** = dziś tylko deklaracja w dokumentach, bez kodu produktu i testu.

| # | Warunek (źródło) | Status | Dowód | Ryzyko |
|---|---|---|---|---|
| 1 | Python 3.13+ (README §5) | C | CI i `.venv-exp` na 3.13.18; `apps/backend/pyproject.toml` deklaruje `>=3.11` | niskie; poprawić deklarację |
| 2 | `requirements.txt`, prosta instalacja | C | plik w korzeniu istnieje, ale: `-e` na dwa pakiety, w zależnościach uruchomieniowych `pytest`, `datamodel-code-generator`, `openapi-spec-validator`; **OCR poza nim** (`requirements-ocr.txt`) | **P0**: skany = 0 po instalacji według instrukcji organizatora |
| 3 | CLI lub skrypt startowy z instrukcją (FAQ 12a) | C | `cli.py`: `process input_dir output_dir` na atrapie, `tests/unit/test_cli_process.py`; brak `start.bat`/`run.sh`; `README.md` mówi „aplikacja nie została zaimplementowana”, wersja 0.4.0 | P0 formalne |
| 4 | Foldery `input` i `output` w korzeniu | C | brak katalogów w repo; ścieżki jako argumenty, domyślne w `config.py` nieużywane przez `process` | niskie |
| 5 | Wynik nazwany jak wejście, drzewo podfolderów | S | `loader.result_name_for`, `engine.run_process`, testy CLI | `rglob("*.pdf")` pomija `.PDF` na Linuksie: brak pliku wyniku |
| 6 | JSON ściśle według formatu: klucze, kolejność, typy | C, **D** w produkcie | spike YAML: roundtrip 60/60 na klasę (`docs/05-weryfikacja/eksperyment-yaml-klasy-2026-11-21.md`); uprząż: kolejność 50/50, ale `prune` usuwa puste elementy, różnica 166 literałów `null` (`atak/E16`) | **P0**: serializera w produkcie nie ma; `prune` może łamać „ścisły format” |
| 7 | Brak zmyślania, `null` gdy brak (FAQ 2/4) | C | E20: FP na polach `null` LLM 2/240; brak pełnomocnika: LLM 4/8 FP; `numer_bzp` 47 FP na 87 zwróconych (E10) | średnie |
| 8 | Obcy dokument = `{}` pod nazwą wejścia (Discord 13:27, mentor) | C | CLI zapisuje `{}` (bo atrapa); router: 147/147 pozytywów, 0/40 FP tylko z promptem znającym typy obce, ogólny 23/40 FP (E06) | średnie: brak niezależnych negatywów |
| 9 | Skany i dokumenty mieszane (mentor) | N w produkcie, C w uprzęży | E11, tylko syntetyczne, 1 powtórzenie | **P0** |
| 10 | Tylko open source, model z możliwością instalacji lokalnej (README §5, FAQ 3/4) | ? | pypdfium2, rapidocr (Apache-2.0), onnxruntime (MIT); licencja wag OCR niepotwierdzona (`harness/ENV.md`); MiniMax Community License wg ADR-002 pkt 8 | **P0**: możliwa dyskwalifikacja |
| 11 | Bez GPU, i7, 16 GB | C | RSS OCR 0,7–1,1 GB (E02); pomiar na maszynie 8 rdzeni/30 GB pod obciążeniem | czas nieznany |
| 12 | API firmy i serwerów w UE/EOG (README l. 158) | ?, **D** | ADR-002: `platform.minimax.io` prowadzi Nanonoble Pte. Ltd., Singapur; punkt „zamknięty decyzją zespołu” | **P0** |
| 13 | Klucz API dołączony, działający w dniu testu | N, **D** | `config.py` czyta `LLM_API_KEY`; brak kanału (U-Q04), brak limitu budżetu; limit wyczerpany 22.11 do ok. 07:40; 17 z ok. 110 wywołań z 429 (`pola/BLOKERY.md`) | **P0**: wyczerpany limit = F1 0 |
| 14 | U jury tylko pip, bez Dockera (mentor) | C, **D** | `scripts/release.py` buduje koła; brak testu czystej instalacji; uprząż wymaga `systemd-run`/`flock` (Linux) | P1: Windows niezbadany |
| 15 | Publiczny endpoint, jury ma Internet | C | API zewnętrzne; sieć zawodziła seriami (40 min, `llm-e2e/PODSUMOWANIE.md`) | P1: ponowienia |
| 16 | Brak limitu czasu, ale wynik musi powstać | ? | mediana 13 s/dok. (Flash), p95 76 s, M3 4,2 s; OCR 17–35 s/stronę pod obciążeniem | nieznane |
| 17 | Nowe klasy przez pliki, bez zmiany kodu (20 pkt) | C, **D** | YAML opisuje tylko model wyniku (4. klasa bez zmian silnika); router (`harness/stages.py`, sygnały w kodzie) i prompt p2 są pisane ręcznie pod trzy klasy | P1 etap 2 |
| 18 | Transparentność ekstrakcji | C, **D** | uprząż: `evidence.json`, `report.json`; kotwice 86% (PDF), 73% poprawnych bbox (OCR) (E05) | P2 |
| 19 | GUI opcjonalne, punktowane (10 pkt) | N | `apps/` zawiera tylko `backend`; projekt UI w dokumentach | P2 |
| 20 | Rozmiar modelu (1–20 pkt, największy model) | ? | 220 albo 427 mld parametrów wg źródeł zewnętrznych (ADR-002); mniejszego modelu nie zmierzono (E18: tylko MiniMax) | P1 etap 2 |
| 21 | Niezależność dokumentów (decyzja zespołu) | C | pętla per plik w CLI; uprząż: 60/60 bajtowo identyczne przy w=1/2/4 (E15) | niskie |
| 22 | Wsad, awaria jednego nie zatrzymuje reszty | S (atrapa) | `engine.run_process`, testy CLI | niskie |
| 23 | JSON dla każdego pliku wejściowego (README §2 pkt 4) | N | `engine.py`: przy wyjątku plik nie powstaje i poprzedni jest usuwany; architektura §10 mówi `empty_json` domyślnie; `ambiguous` bez eksportu | **P0**: trzy miejsca, trzy zachowania |
| 24 | Klasyfikacja po treści, nie po nazwie | C, **D** | zasada w architekturze §2; uprząż jej przestrzega | niskie |
| 25 | Link do GitHub z działającym prototypem (README §4) | N | repo prywatne, konta jury nieustalone (U-Q09) | P0 formalne |
| 26 | Wersjonowanie | S | `VERSION` 0.6.1, `CHANGELOG.md`, `tests/unit/test_release.py` | brak |
| 27 | Opis użytego LLM, wyniki własnych testów (opcjonalne) | C | raporty w `experiments/`; brak karty modelu | P2 |

Tylko deklaracje (bez kodu produktu i testu): 6 (w produkcie), 9, 12, 13, 14, 17, 18, 19, 24 oraz self-check, cache i manifest wersji wyniku z architektury §8–§9.1.

## C. Ocena etapami

Skala 1–5. „Projekt” = jakość kontraktu wobec celu F1; „Dowody” = czy coś zmierzono i czy pomiar dotyczy produktu.

| Etap | Projekt | Dowody | Zmierzono | Nie zmierzono | Główne ryzyko dla F1 | Potrzebny? | Minimalna zmiana |
|---|---|---|---|---|---|---|---|
| E: odczyt PDF | 4 | 3 | pdfium 1454/1454 wartości, IoU ≥ 0,977 po `/Rotate` (E01) | PDF spoza generatora, kolejność czytania poza przelewami (S1) | niskie | tak | przyjąć pypdfium2 w ADR |
| E: OCR i diagnoza | 4 | 2 | 96,7–97,8% wartości (359 wartości, E02); 0/843 stron skanowych uznanych za tekst (E04); obrót +0,30…+0,46 (E03) | fizyczne skany, czas, S5 w produkcie | **S5: F1 0,000 przy `complete`**; skan obrócony | tak | na stronie zdominowanej obrazem pominąć warstwę tekstu; OCR + obraz do LLM |
| L: staging | 3 | 1 | nic (uprząż zapisuje pliki, nie mierzono korzyści) | wszystko | brak wpływu na F1; koszt budowy | **nie na ścieżce jury** | pamięć procesu + opcjonalny zrzut diagnostyczny |
| T1: router | 3 | 2 | 147/147 pozytywów; reguły same 141/147, bez nagłówka 79/147 (E06) | niezależne negatywy; modele inne niż Flash | `ambiguous` bez eksportu = same FN; fałszywe `foreign` | tak, w tym samym wywołaniu LLM | zawsze wybrać najlepszą klasę; `foreign` tylko przy jawnych sygnałach przeciwnych |
| T2: role | 2 | 3 | LLM 0,997 vs reguły 0,987, Δ +0,010 [+0,003; +0,018] (E07) | konsorcja, układy bez etykiet | niskie | **nie jako osobny etap** | usunąć z projektu v1; role w prompcie T3 |
| T3: kandydaci | 4 | 3 | tekst 0,938 [0,910; 0,959], 5 powtórzeń (E10) | zbiór kontrolny, drugi dostawca | patrz niżej: dokumenty bez wyniku i trzy słabe pola | tak | ponowienie przy złej odpowiedzi; reguły dla czynności i BZP |
| T3: kotwiczenie | 2 | 3 | 86% jednoznacznych (PDF), 73% poprawnych bbox (OCR) (E05); zerowanie bez kotwicy −0,021 tekst, −0,073 skany (E17) | docelowy algorytm | **bbox jako warunek wartości obniża F1** | tylko dla GUI | odłączyć od treści JSON; liczyć po eksporcie |
| T4: scalanie | 2 | 1 | nic | wszystko | pętla = koszt i limit API | **nie** | usunąć z planu do finału |
| T5: normalizacja i walidacja | 3 | 3 | 100% na wartościach z danych; luki E19 (`1.000,50` → 1,0; NIP z myślnikami → `None`); mutanty 83 z 216 przeżyły (`backlog.md`) | formaty ukrytego zbioru | cicha błędna kwota; blokada eksportu przy braku pola wymaganego | tak | naprawić E19; walidacja nigdy nie blokuje eksportu, tylko flaguje |
| Eksport | 3 | 2 | kolejność kluczy 50/50; `partial` bez eksportu −0,208 tekst, −0,453 skany (E17) | serializer produktu | `prune` i brak pliku | tak | serializować z szablonu klasy z jawnymi `null`; zawsze plik |
| Repozytorium danych (SQLite) | 4 | 4 | 722 linie testów kontraktowych; mutanty 21 z 63 przeżyły | użycie przez silnik (nie ma silnika) | brak wpływu na F1 | **nie dla CLI**; tak dla GUI | nie podłączać do `process` |
| API HTTP | 2 | 1 | `openapi.yaml` ma tylko `/healthz`; 51 wektorów ataku dotyczy uprzęży (E12) | produkt | brak wpływu na F1 | tylko dla GUI | po działającym CLI: 4 trasy (wgranie, stan, wynik, dowody) |
| Konfiguracja i self-check | 3 | 1 | `tests/unit/test_config.py` dla zmiennych; self-check nie istnieje | wszystko | zły klucz lub limit = F1 0 dla całego wsadu | tak, w małej formie | jedno wywołanie próbne przed wsadem + czytelny komunikat |
| CLI | 4 | 3 | drzewo, atomowość, kody wyjścia na atrapie | prawdziwy silnik | `.PDF`, brak pliku przy wyjątku | tak | podłączyć silnik; `{}` + raport przy awarii |
| GUI | 3 | 1 | nic (brak kodu) | wszystko | brak wpływu na preselekcję | po F1 | jedna strona: wgranie, JSON, obraz strony |
| CI i jakość | 4 | 4 | `scripts/ci.py` 930 linii, 564 linie testów | — | **koszt alternatywny**: próg 100% mutantów na kodzie, który nie istnieje | tak, lżej | decyzja użytkownika o zakresie mutacji do terminu (zmiana ADR-003, nie omijanie hooków) |

Szczegóły T3, które zmieniają priorytety (**[F]** `llm-e2e/E10/wyniki.json`, wariant bazowy, 435 wierszy):

- Suma: TP 3696, FP 137, FN 353. FN jest 2,6 razy więcej niż FP.
- Prawie każde pole odwołania ma FN = 10 na 125 dokumentów, przelewy 0. **[W]** Około 10 odwołań (8%) nie dało żadnego pola, co odpowiada za ok. 200 z 353 FN. Przyczyna to głównie `llm_invalid_response` (9 dokumentów) na długich odwołaniach. Ponowienie i krótsze wyjście dałyby więcej niż jakakolwiek zmiana promptu; to prawdopodobnie tłumaczy też przewagę M3 (+0,035, 706 zamiast 2566 tokenów wyjścia), więc E18 nie jest czystym porównaniem jakości modeli.
- 123 z 137 FP pochodzi z czterech pól: `numer_bzp` 47 (F1 0,593), `czynnosc_opis` 27, `czynnosc_powod_id` 25, `pelnomocnik.imie_nazwisko` 24.
- Reguły dla czynności mają 0,993 (E09), LLM w ścieżce pionowej 0,83–0,84. Raport rekomenduje „reguły główne”, ale wariant E10/E11 ich nie używa. **[W]** Zastąpienie daje do ok. +0,01.
- Gdyby usunąć obie grupy błędów, tekst doszedłby do ok. 0,97–0,98 **[W]**, na tym samym generatorze.

## D. Ocena całości

**Spójność kontraktów.** Etapy E → T3 → T5 → eksport są spójne typami. Niespójności:

1. **Awaria a plik wyniku (P0).** Architektura §10: `empty_json` domyślnie. `engine.py`: brak pliku i usunięcie poprzedniego. Uprząż: awaria LLM = brak pliku, `ambiguous` = 409 bez wyniku. README organizatora: JSON dla każdego dokumentu.
2. **Bbox jako warunek wartości (P0).** §4.5 i §10 („nie zatwierdzamy wartości bez dowodu”, `complete` wymaga geometrii) przeczą E17. Na skanach większość dokumentów miałaby `partial`.
3. **Blokada eksportu przez walidację (P0).** §2 T5: brak pola wymaganego blokuje eksport. Przy F1 liczonym per pole to zamiana jednego FN na kilkadziesiąt.
4. **Cache (P1).** §8 wymaga dokładnej rewizji modelu; API zwraca `MiniMax-M3.1-Flash` dla aliasu `-Flash-Preview` (E10), więc według własnej reguły cache nie wolno użyć. Cache nie istnieje i nie był mierzony: usunąć z zakresu.
5. **§3 a §2 (P2).** V1 to jedno wywołanie dla T1 i T3, a tabela etapów i katalog artefaktów opisują je jako osobne etapy z osobnymi wersjami.
6. **Dwa katalogi kodów (P2).** 59 kodów polskich plus mapa na angielskie; produkt nie emituje żadnego.

**Złożoność wobec terminu.** Backend ma ok. 3100 linii, z czego `db/` 1529, ewaluator 461, normalizatory 396 i zero linii odczytu PDF, OCR, LLM, routera i serializera. Do pierwszego F1 produktu potrzeba w tej kolejności: czytnik + diagnoza, OCR, klient LLM z ponowieniem, prompt p2, normalizatory, serializer z szablonu, podpięcie do `process`. Niepotrzebne do pierwszego wyniku: L, T2, T4, `DataRepository`, OpenAPI v1, cache, self-check interaktywny, mapowanie kodów, GUI.

**Pokrycie `docs/05-weryfikacja/katalog-przypadkow-brzegowych.md`.**

| Przypadek | Stan pomiaru |
|---|---|
| S2 obraz na stronie tekstowej | zmierzony: A 0,673, B 0,979 (n=24) |
| S3 cały skan | zmierzony syntetycznie: B 0,902, C 0,928, D 0,961 (n=26) |
| S4 mieszany | zmierzony: B 0,916 (n=24), D 0,980 (n=9) |
| S5 błędna warstwa | zmierzony: A 0,625, B 0,724, C 0,927, D 0,876 (n=11): **D nie wygrywa z C**, więc „tekst + obraz” nie jest lekarstwem, dopóki błędna warstwa trafia do promptu |
| S6 obrót | zmierzony dla OCR (E03); skos > 3° nie |
| S7 dane po 3. stronie | bez mocy: 2,6% pól ze strony ≥ 3 (E10) |
| S1 niewidoczna tabela, S8 wiele dokumentów | niezmierzone |
| T1, T2 etykiety | pośrednio: router bez nagłówka 79/147 regułami; ról bez etykiet nie badano |
| T3 synonimy, T4 brak informacji wprost | niezmierzone |
| T5 konsorcjum | w danych (6/60), brak osobnego wyniku |
| T6 rzadkie warianty | n = 8, edycje syntetyczne (E20) |

**ADR do zmiany po tej nocy.**

| ADR / miejsce | Zmiana | Podstawa |
|---|---|---|
| ADR-002 pkt 3 | przyjąć `pypdfium2` | E01; własnego czytnika nie ma w repo |
| ADR-002 pkt 4 i uzupełnienie „własny OCR w 3 godziny” | `rapidocr` jako dostarczany OCR; własny model tylko po pobiciu go na tym samym zestawie | E02, E03; własnego modelu nie ma w repo |
| ADR-002 pkt 8 | otworzyć ponownie: dowód UE/EOG i licencji albo drugi dostawca; nazwa modelu (Flash-Preview czy M3) | E18, README l. 158 |
| ADR-002 pkt 12, architektura §8 | cache poza zakresem do finału | brak pomiaru, brak rewizji modelu |
| Architektura §4.5, §6, §10 | bbox nie wpływa na treść JSON ani na eksport; `ambiguous` eksportuje najlepszą klasę; walidacja nie blokuje | E17 |
| Architektura §3, §5 | strona zdominowana obrazem: warstwa tekstu odrzucona lub porównana z OCR | S5 |
| ADR-003 | zakres testów mutacyjnych na czas do terminu | 83 + 8 + 21 przeżytych mutantów, zero kodu ekstrakcji |
| ADR-005 | bez zmian do odpowiedzi mentora; raportować oba warianty | wariant FP+FN obniża tekst najwyżej do ok. 0,92 **[W]** (wszystkie 137 FP liczone także jako FN) |

**Ryzyka etapu 2.** (a) Rozmiar modelu: nieznany, prawdopodobnie setki miliardów; brak pomiaru mniejszego modelu, więc brak krzywej F1 vs rozmiar. (b) Elastyczność: YAML opisuje wynik, nie ekstrakcję; dodanie klasy wymaga dziś kodu routera i promptu. Do obrony 20 pkt potrzebny jest pokaz: nowy plik YAML → działająca ekstrakcja bez zmiany kodu. (c) Wariant D na skanach wymaga modelu wizyjnego, co wiąże wybór modelu z punktacją rozmiaru.

**Realizacja mojej poprzedniej oceny** (`docs/07-decyzje/konsultacja-ocena-calosci-2026-11-21/fable-odpowiedz.txt`, §7):

| Warunek | Stan |
|---|---|
| 1. loader, ewaluator, CLI na atrapie | zrobione (kod i testy); ewaluator miał błąd unieważniający F1, naprawiony |
| 2. zastępczy odczyt i OCR zmierzone na rasteryzacji | zrobione w uprzęży na 49 sprawach, nie w produkcie |
| 3. otwarty model w Europie zmierzony na ścieżce pionowej | częściowo: zmierzono tylko MiniMax; otwartość i lokalizacja nieudowodnione; mniejszego modelu brak |
| 4. decyzje `null`, eksport, wiele dokumentów | zamknięte w dokumentach, a E17 dwie z nich podważa |
| 5. OpenAPI v1 | niezrobione |
| 6. GUI P0 | niezrobione |
| 7. sprzeczności w dokumentach | częściowo; `README.md` nadal 0.4.0 |

Nowe dane zmieniają dwie moje wcześniejsze rekomendacje: sumy kontrolnej nie wolno używać jako filtra (poprawna tylko u 64% NIP, 70% REGON, 34% IBAN, E19), a obowiązkowy bbox, który wtedy uznałem za sprawę kontraktu, okazał się kosztem F1.

## E. Następne 24 godziny

Kolejność według oczekiwanego wzrostu F1 na ukrytym zbiorze.

| # | P | Działanie | Oczekiwany skutek | Wysiłek |
|---|---|---|---|---|
| 1 | P0 | Przenieść wariant uprzęży do `process`: pdfium, diagnoza, OCR `if_needed`, jedno wywołanie LLM (prompt p2), normalizatory, serializer z szablonu klasy. Bez `DataRepository` i HTTP | z 0 do ok. 0,90 | 5–7 h |
| 2 | P0 | LLM: pisemne potwierdzenie mentora dla MiniMax albo pomiar jednego otwartego modelu u dostawcy z UE na tych samych 25 sprawach; osobny klucz dla jury z limitem ≥ 3× zużycia wsadu; dławienie i ponowienia po 429 | usuwa ryzyko 0 i dyskwalifikacji | 2–3 h |
| 3 | P0 | Instalacja: OCR w głównym `requirements.txt`, bez narzędzi deweloperskich; `start.bat` i `run.sh`; katalogi `input`/`output`; test z czystego venv na Windows i Linux; aktualny `README.md` | skany z 0 do ok. 0,90; spełnia warunki 2–4, 14 | 2 h |
| 4 | P0 | Zawsze plik wyniku: ponowienie przy złej odpowiedzi (do 3), limit tokenów wyjścia, `ambiguous` → najlepsza klasa, awaria → wynik reguł albo `{}` z raportem | +0,02–0,03 (tekst), więcej przy awariach | 2 h |
| 5 | P1 | Reguły E09 dla `czynnosc_*`, wzorzec i normalizacja `numer_bzp`, kontrola `pelnomocnik.imie_nazwisko` | +0,01–0,02 | 2 h |
| 6 | P1 | S5 i skany: odrzucić warstwę tekstu strony zdominowanej obrazem, wykrywanie obrotu, obraz do LLM tylko dla takich stron | S5 z 0,63–0,72 do ok. 0,93; skany +0,03–0,06 | 2–3 h |
| 7 | P1 | Normalizatory E19; usunąć `prune`, jawne `null` jak w referencji | chroni przed cichym FP; zgodność formatu | 1–2 h |
| 8 | P1 | Jeden przebieg produktu na zbiorze kontrolnym; 10 spraw wydrukowanych i zeskanowanych; czas całego wsadu na 4 rdzeniach | pierwszy wiarygodny wynik końcowy | 2 h + skanowanie |
| 9 | P2 | Pokaz nowej klasy z samego YAML (prompt i sygnały routera generowane z pliku); karta modelu; GUI jednostronicowe | punkty etapu 2 | 4–6 h |

Nie robiłbym przed zgłoszeniem: T2, T4, staging L, cache, OpenAPI v1 w pełnym zakresie, utwardzania HTTP poza limitem ciała żądania, mapowania kodów.

**Pięć pytań do mentora lub organizatora:**

1. Czy MiniMax przez `api.minimax.io` (podmiot, lokalizacja serwerów, licencja wag) spełnia „open source” i „firma i serwery w UE/EOG”? Jeśli nie, jakie modele i dostawcy są akceptowani?
2. Jak liczy ewaluator: agregacja (po polach czy po dokumentach lub klasach), błędna wartość jako FP czy FP i FN, brakujący klucz a `null`, pusta lista, brak pliku wyniku?
3. Jak powstały skany i dokumenty mieszane w teście (rasteryzacja generatora czy fizyczny skan, z warstwą OCR czy bez) i jaki mają udział?
4. Jak rozmiar modelu przekłada się na punkty (całkowite czy aktywne parametry w MoE, czy model OCR i model wizyjny się liczą, czy jest próg)?
5. Jak jury uruchomi rozwiązanie: system operacyjny, dokładne polecenie, liczba dokumentów w teście, kanał przekazania klucza i czy przebieg jest jednokrotny?

## F. Co mnie najbardziej niepokoi

1. **Odwrócona proporcja pracy.** Po dobie istnieją repozytorium danych z atomowym `commit_run`, runner CI z budżetami czasu i 51 wektorów ataku na serwer eksperymentalny, a polecenie, które uruchomi jury, zapisuje `{}`. Każda liczba F1 w raporcie dotyczy kodu, który nie jest zgłaszany i nie przechodzi bramek jakości obowiązujących produkt.
2. **Zamknięcie sprawy MiniMax bez dowodu.** To jedyny warunek, którego nie naprawi żadna ilość kodu w ostatniej godzinie, a wszystkie pomiary zależą od tego jednego dostawcy.
3. **Liczby wyglądają pewniej, niż są.** Jeden generator, reguły i prompt strojone na tych samych sprawach, 25 spraw, skany syntetyczne z jednym powtórzeniem, wariant D na 26 dokumentach, wiersze błędów sieci (539 + 681 + 379) wyłączone z liczb. Wyłączenie błędów sieci jest uczciwe metodologicznie, ale u jury błąd sieci jest wynikiem.
4. **Limit i niestabilność API zaobserwowane w nocy** nie mają odpowiednika w architekturze poza „ograniczonym budżetem prób”.

**Co by mnie przekonało, że się mylę:**

- wynik produktu (nie uprzęży) przez `process` z czystego venv na zbiorze kontrolnym ≥ 0,90 na tekście i ≥ 0,85 na skanach, w jednym przebiegu;
- 10 fizycznie zeskanowanych spraw z F1 w granicach 0,05 od skanów syntetycznych;
- pisemna odpowiedź mentora akceptująca MiniMax albo drugi model z porównywalnym F1;
- pełny wsad 60 spraw na Windows, 4 rdzenie, bez błędu 429 i w czasie akceptowalnym dla zespołu;
- odpowiedź organizatora o ewaluatorze zgodna z ADR-005.

## Czego nie sprawdziłem

Nie uruchamiałem testów, CI, OCR ani LLM (zakaz w zleceniu), więc stan „zielony” testów przyjmuję z obecności plików, nie z przebiegu. Nie czytałem w całości `recenzje/codex.md`, `E12`–`E15` ani surowych wierszy `raw/`. Szacunek „ok. 10 odwołań bez wyniku” wynika z rozkładu FN per pole, nie z przeliczenia wierszy.
