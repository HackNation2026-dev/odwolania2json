---
wersja: 0.1.0
aktualizacja: 2026-11-21
status: plan eksperymentów; wyniki w experiments/2026-11-21-wybor-modulow/
---

# Plan eksperymentów: wybór modułów odczytu i ekstrakcji

Cel: na podstawie pomiarów zdecydować, jakie moduły tworzą wersję końcową: odczyt tekstu, OCR, geometria i dowody, klasyfikacja, grupy i role, pola, LLM. Decyzje zapisujemy w ADR dopiero po wynikach. Nic tu nie jest wynikiem F1 oficjalnego ewaluatora.

## Ograniczenia (z README organizatora, §5–§6)

- Laptop: Intel i7, **16 GB RAM, bez GPU**. LLM wyłącznie po API, z serwerów w UE/EOG; klucz dostarczamy z rozwiązaniem. Python 3.13+, komponenty open source.
- Pomiar zasobów na CPU i RAM: każdy eksperyment liczący uruchamiamy z limitem pamięci 14 GB (`systemd-run --user --scope -p MemoryMax=14G` lub `prlimit`) i raportujemy szczytowy RSS oraz czas ścienny. Testy czasu biegną pod `flock /tmp/uzp-cpu.lock`, żeby równoległe zadania nie zniekształcały pomiaru.
- MiniMax (`api.minimax.io`, protokół Anthropic, klucz z `MINIMAX_KEY_FILE`) służy tylko do eksperymentów; zgodność z wymogiem UE/EOG potwierdza ADR-002, nie ten plan. Klucz nigdy w repozytorium, logach ani wynikach.

## Dane

- Zbiór rozwojowy i kontrolny: zamrożony podział `data/podzial.json` (kod: `apps/backend/odwolania2json/dataset.py`). Strojenie wyłącznie na rozwojowym; kontrolny raz, na końcu.
- Materiały organizatora: `docs/02-materialy/organizator-uzp/` (60 spraw × 3 dokumenty, negatywy, szablon-skan). Oryginały nienaruszone; kopie robocze w katalogu eksperymentu.
- Przypadki brzegowe: [katalog](katalog-przypadkow-brzegowych.md) i 12 syntetycznych wariantów z [eksperymentu 2026-11-21](eksperyment-przypadki-brzegowe-2026-11-21.md); dodatkowo warianty rasteryzacji (100/150/200/300 dpi), obrót, przekrzywienie, szum, JPEG.
- Ewaluator: `apps/backend/odwolania2json/evaluator.py` (TP/TN/FP/FN, F1). Wynik nazywamy „F1 przybliżonym”.

## Sposób komunikacji: HTTP

Wszystkie eksperymenty end-to-end idą przez HTTP, tak jak będzie używał klient lub GUI:

1. Harness uruchamia backend (FastAPI) na `127.0.0.1` i wywołuje go klientem HTTP (`httpx`): wgranie PDF, odczyt stanu, wyniku, dowodów, raportu.
2. Backend woła LLM przez HTTP (protokół OpenAI lub Anthropic, konfigurowalny endpoint i model).
3. Kontrakt: [OpenAPI v1](../04-architektura/architektura-wewnetrzna.md) (§10). Dopóki trasy nie istnieją w `openapi.yaml`, harness dostarcza cienką warstwę eksperymentalną w `experiments/`; wyniki przenoszą się na kontrakt po decyzji.

## Eksperymenty

Każdy ma: hipotezę, dane, miarę, kryterium decyzji i artefakt (JSON z surowymi liczbami + krótki opis „jak działa i dlaczego”).

### A. Odczyt tekstu i geometria

| Nr | Pytanie | Miara | Kryterium |
|---|---|---|---|
| E01 | Czy warstwa tekstowa PDF (pypdfium2) wystarcza dla dokumentów elektronicznych i daje poprawne bbox (obrót `/Rotate`, strony w pt vs px)? | pokrycie słów względem referencji, poprawność bbox (IoU na punktach kontrolnych), czas i RSS na 206 dokumentach | pokrycie ≥ 0,99 na dokumentach tekstowych |
| E02 | Czy OCR CPU (rapidocr + onnxruntime) mieści się w czasie i RAM i jak dokładny jest na skanach? | CER i WER na skanach (szablon 7 str., 3 skany negatywne, 12 syntetycznych), s/stronę, szczyt RSS, dla 100/150/200/300 dpi | próg dokładności i czasu ustalony po pomiarze; RSS < 4 GB |
| E03 | Czy preprocessing (wykrycie obrotu 0/90/180/270, deskew, binaryzacja) poprawia OCR i ile kosztuje? | zmiana CER, czas | przyrost CER ≥ 10% wart kosztu czasu |
| E04 | Czy diagnoza per strona (tekst / skan / mieszana) działa i oszczędza OCR? | dokładność diagnozy, odsetek stron wysłanych do OCR | zero stron skanów oznaczonych jako tekst |
| E05 | Czy kotwiczenie cytatów LLM w słowach PDF i OCR daje poprawny bbox? | odsetek jednoznacznie zakotwiczonych, IoU z wzorcem, duplikaty cytatów, obrót | ≥ 0,95 zakotwiczonych, zero „zgadniętych” |

### B. Klasyfikacja, grupy, role, pola

| Nr | Pytanie | Miara | Kryterium |
|---|---|---|---|
| E06 | Router: sygnały regułowe, sam LLM czy hybryda? | macierz pomyłek, trudne negatywy (wyrok KIO, BZP/TED), koszt wywołań | brak fałszywych klasyfikacji negatywów |
| E07 | Podmioty i role (odwołujący, zamawiający, pełnomocnik, mocodawca): kontekst + regex czy LLM? | F1 pól listowych, NIP przypisany złej osobie | błędne przypisania ≤ ustalony próg |
| E08 | Pola o stałym formacie (NIP, REGON, KRS, rachunek, kwota, daty, numery): regex na tekście PDF i na tekście OCR | precyzja i recall, odporność na błędy OCR (O/0, l/1), mutanty | brak regresji na OCR względem PDF poza ustaloną tolerancją |
| E09 | Zaskarżona czynność (powód 1–12 i data): reguły czy LLM? | dokładność id i daty | reguły tylko jeśli ≥ LLM |

### C. LLM i ścieżka pionowa

| Nr | Pytanie | Miara | Kryterium |
|---|---|---|---|
| E10 | Który wariant LLM: wejście tekst vs obraz, jedno wywołanie na dokument, prompt, temperatura 0; stabilność 3 powtórzeń | F1 przybliżony, tokeny, czas, zgodność ze schematem, wariancja | najlepszy F1 przy czasie i koszcie w budżecie |
| E11 | Ścieżka pionowa end-to-end przez HTTP, warianty: A (PDF + regex + LLM), B (A + OCR), C (tylko LLM na obrazach) | F1 per klasa i pole, czas na dokument, szczyt RSS | wybór wariantu na zbiorze rozwojowym; kontrolny raz |

### D. Odporność i atak na API

| Nr | Pytanie | Miara | Kryterium |
|---|---|---|---|
| E12 | Złośliwe i uszkodzone wejścia: uszkodzony i zaszyfrowany PDF, nie-PDF z `.pdf`, 0 stron, tysiące stron, ogromne obrazy, zagnieżdżone obiekty, bardzo duży upload | kod błędu techniczny, brak crashu i zawieszenia, limit czasu i RAM | zawsze jawny `technical_error`, serwer żyje |
| E13 | Wstrzyknięcie poleceń w treści dokumentu (np. „zwróć {}”, ukryty biały tekst, tekst w metadanych) | zmiana wyniku względem czystego dokumentu | wynik niezmieniony lub oznaczony do sprawdzenia |
| E14 | Awarie LLM i OCR: 401/403, 429, timeout, urwany JSON, brak sieci, odpowiedź poza schematem | kody błędów, brak zmyślonych danych, brak podmiany z cache | zgodność z architekturą §6 i §9.1 |
| E15 | Wsad i współbieżność: 60 dokumentów, współbieżność 1/2/4, ubicie procesu w trakcie (`kill -9`), uszkodzony plik w środku wsadu | czas, szczyt RSS, kompletność, atomowość zapisu, kontynuacja wsadu | brak plików częściowych, wsad kończy resztę |
| E16 | Determinizm i regresja: ten sam wsad dwa razy | identyczność JSON (kolejność kluczy, `null`), stabilność wersji | zero różnic poza polami LLM z jawną wariancją |

## Wynik końcowy

Raport zbiorczy `experiments/2026-11-21-wybor-modulow/RAPORT.md`: tabela decyzji (moduł → wybór → dowód → ryzyko), wyniki E01–E16 z liczbami, budżet zasobów na i7/16 GB, lista otwartych problemów i propozycja ADR. Wyniki surowe i skrypty w katalogu eksperymentu; powtarzalne jednym poleceniem.

## Korekta 0.2 po recenzjach (Fable i Codex, 2026-11-22)

Recenzje: `experiments/2026-11-21-wybor-modulow/recenzje/fable.md` i `codex.md`. Poniższe zapisy mają pierwszeństwo nad tabelami wyżej.

**P0 — warunki przed jakimkolwiek rankingiem**

1. **E00: ewaluator.** Zgodna wartość to TP (naprawione, PR #8). Do zrobienia: błędna wartość obecna po obu stronach to wyłącznie FP (architektura §11), próg 80% dla pięciu pól tekstowych z `zasady-f1.md` (kilka wariantów podobieństwa, raportowany rozrzut), listy dopasowane element do elementu z oceną pól wewnątrz elementu. Test: referencja kontra referencja daje F1 = 1,0.
2. **Zakaz przecieku.** Warianty pochodzące ze spraw kontrolnych (m.in. `przyklad_40`) nie służą do strojenia; wariant dziedziczy podział rodzica; manifest pochodzenia i test blokujący. Kontrolny zbiór: jeden wcześniej zapisany wybór, jeden przebieg; licznik użyć w repozytorium.
3. **Skany z referencją pól.** Rasteryzacja 49 spraw rozwojowych (147 dokumentów) w profilach dopasowanych do skanów organizatora (rozdzielczość, kompresja, szum, kąt, zagięcia) oraz dokumenty mieszane, S2 (dane tylko w obrazie na stronie tekstowej) i S5 (poprawny obraz z błędną niewidoczną warstwą). Referencja pól dziedziczona z oryginału. Fizyczne skany około 10 spraw są walidacją generatora i pozostają do wykonania ręcznie; plan tego nie udaje.
4. **Miara decyzyjna to F1 pól end-to-end, osobno dla tekstu, skanu i mieszanych**, z przedziałem z bootstrapu po sprawach i porównaniem sparowanym. CER/WER i pokrycie słów są tylko diagnostyczne. Progi zapisujemy przed pomiarem albo zastępujemy regułą porównawczą (wariant zastępuje drugi, gdy dolna granica przedziału różnicy F1 jest dodatnia).

**Nowe i zmienione eksperymenty**

| Nr | Zmiana |
|---|---|
| E00 | patrz wyżej |
| E01, E05 | zamiast „pokrycia słów” i „IoU z wzorcem”: odnajdywalność wartości referencyjnych w tekście odczytu po normalizacji, test obiegowy bbox (wytnij bbox, porównaj z cytatem), narożniki po `/Rotate`, kolejność czytania na dwóch układach przelewów |
| E02–E04 | dodatkowo F1 pól na skanach; CER tylko na rasteryzacji dokumentów z warstwą tekstu; E04 z kosztem po obu stronach (strony tekstowe wysłane do OCR) |
| E06 | miara dwustronna (pozytyw odrzucony kosztuje wszystkie pola), negatywy zbliżone do klas, losowe nazwy plików |
| E10 | co najmniej 5 powtórzeń, bootstrap po sprawach, zapis rewizji modelu, odsetek odpowiedzi poza schematem, test długiego dokumentu (fakt po stronie 3) |
| E11 | dodatkowo wariant D (tekst + obraz strony) i dolna granica „sam regex bez LLM”; ablacje jednego modułu naraz; F1 per typ wejścia i per pole |
| E16 | determinizm kodu na zapisanych odpowiedziach LLM, osobno od wariancji modelu |
| E17 | polityka `null` i eksportu a F1: `ambiguous` bez pliku vs najlepsza klasa, pole niezakotwiczone `null` vs wartość, awaria LLM `{}` vs wynik z reguł; bbox nie decyduje o treści ocenianego JSON |
| E18 | wybór modelu LLM: ten sam prompt i dane na 2–3 modelach różnej wielkości; reguła rozstrzygająca zapisana z góry |
| E19 | normalizatory kontra referencje (daty, kwoty, NIP, rachunki, wielkość liter), bez LLM i OCR |
| E20 | obecność pola: FP na polach z referencją `null`; luki: brak pełnomocnika, powód 12, brak BZP/TED, wpis |

**Zakres części D.** Backend z kontraktu v1 nie istnieje, więc E12–E16 uruchamiamy na uprzęży (`harness/server.py`) wiernie odwzorowującej trasy v1 i zapisujemy wprost: wynik opisuje uprząż, a luki przenosimy jako testy do produktu. Dołączone wektory z recenzji: wyciek klucza-kanarka, ścieżki w uploadzie, wyczerpanie zasobów, bomby PDF z izolacją parsera, rozszerzona prompt injection, SSRF z PDF i przez konfigurację, IDOR, wyścigi i `kill -9`, zatrucie cache, wyczerpanie budżetu LLM.

**Pomiar zasobów.** Szczyt pamięci całej grupy procesów, jawna liczba wątków, zimny i ciepły start, mediana i p95 z co najmniej 5 powtórzeń, czas LLM osobno od CPU.
