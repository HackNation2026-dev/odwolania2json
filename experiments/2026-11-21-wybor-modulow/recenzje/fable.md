# Recenzja planu eksperymentów wyboru modułów (Fable)

Data: 2026-11-22. Zakres: plan 0.1.0 (`docs/05-weryfikacja/plan-eksperymentow-wyboru-modulow-2026-11-21.md`) na tle README organizatora, architektury 0.6.1, ADR-002, eksperymentu przypadków brzegowych, katalogu i zasad F1. Tylko odczyt repozytorium; jedyne uruchomienie to `compare_document` na czterech polach (pkt 0.1).

Werdykt: **plan nie nadaje się do wykonania w obecnej postaci.** Miernik, na którym opiera się E07–E11, jest dziś niepoprawny, a decyzja o OCR opiera się na próbce bez referencji pól. Kolejność E01→E16 odwraca też priorytet: najpierw trzeba naprawić pomiar i zbudować zestaw skanów z referencją.

## 0. Ustalenia blokujące (P0, sprawdzone w kodzie)

0.1. **Ewaluator nie zwraca żadnego TP dla pól.** `apps/backend/odwolania2json/evaluator.py`, `_compare_value`: zgodna wartość dostaje werdykt `tn` (l. 189–190), dopasowany element listy też `tn` (l. 207). `tp` powstaje wyłącznie dla klasyfikacji. Sprawdzone: `compare_document({'a':'x'},{'a':'x'})` → `tn`. Skutek: F1 pól = 0,0 dla każdego wariantu, więc E10/E11 nie rozróżnią niczego.

0.2. **Ewaluator jest sprzeczny z `zasady-f1.md`.** Błędna wartość liczona jest jako FP **i** FN (l. 192–193); zasady i architektura §11 mówią: tylko FP. Zmienia to ranking strategii „zwróć kandydata vs `null`”.

0.3. **Brak progu 80% i dopasowania częściowego list.** Porównanie to `==`; lista dopasowuje całe elementy (`element in unmatched`). Jedna litera różnicy w nazwie firmy daje FN+FP za cały podmiot, zamiast oceny pole po polu. `rapidfuzz` jest w zależnościach, ale ewaluator go nie używa. Pola OCR (nazwy, tytuły) będą systematycznie zaniżane, co przesunie decyzję na korzyść wariantu C (LLM na obrazach) lub przeciw OCR z powodów czysto pomiarowych.

0.4. **Przeciek do zbioru kontrolnego już nastąpił.** Eksperyment przypadków brzegowych podaje, że 12 syntetyków powstało ze spraw `przyklad_01`, `02` i **`40`**; `przyklad_40` jest w `kontrolny` (`data/podzial.json`). Plan używa tych 12 plików w E02 i „Danych” do strojenia progów. Dodatkowo `narzedzia/syntetyczne.py` wybiera sprawy przez `next(...)` po cechach (liczba stron), bez sprawdzania podziału.

0.5. **Plan testuje moduły odrzucone w ADR-002.** E01 nazywa `pypdfium2`, E02 `rapidocr`; ADR-002 pkt 3 i 4 odrzuca oba jako docelowe, a plan nie ma ani jednego konkurenta ani własnego modelu OCR zespołu. Eksperyment z jednym kandydatem nie jest wyborem modułu.

0.6. **Backend, który ma być atakowany, nie istnieje w kontrakcie.** `openapi.yaml` ma jedną trasę (`/healthz`). Plan dopuszcza „cienką warstwę eksperymentalną w `experiments/`” — wtedy E12–E16 mierzą odporność harnessu, nie produktu. Wyniki części D nie przenoszą się na kod, który zostanie zgłoszony.

## 1. Luki

### 1.1. Brakujące eksperymenty

| P | Brak | Dlaczego blokuje wybór |
|---|---|---|
| P0 | **E00: walidacja ewaluatora** — referencja vs referencja musi dać F1 = 1,0; referencja z jedną zepsutą wartością, z dodanym polem, z usuniętym polem, z permutacją listy, z nazwą różną o 1 znak | bez tego żaden F1 z planu nie jest liczbą |
| P0 | **Skany z referencją pól**: rasteryzacja wszystkich 49 spraw rozwojowych × 3 dokumenty (grupa A z architektury §11) + osobno 11 kontrolnych | E02 mierzy CER, a ocena to F1 pól; CER nie przewiduje trafienia NIP-u ani rachunku |
| P0 | **F1 w rozbiciu na typ wejścia** (tekst / skan / mieszany) dla każdego wariantu E11 | ukryty zbiór ma wszystkie trzy; średnia po 180 dokumentach tekstowych ukryje porażkę na skanach |
| P0 | **Wybór dostawcy i modelu LLM**: co najmniej 2–3 modele o różnej wielkości, w tym mniejszy | E10 porównuje warianty wywołania jednego modelu; etap 2 karze rozmiar (1–20 pkt), a ADR-002 podaje 220–427 mld parametrów dla MiniMax |
| P0 | **Klasyfikator obecności pola** (`null` vs wartość) | `zasady-f1.md` wniosek 3 nazywa to kluczową decyzją; plan nie ma eksperymentu ani miary (FP na polach z referencją `null`) |
| P0 | **Polityka przy awarii i niepewności a F1**: `{}` vs częściowy wynik vs najlepszy kandydat, `ambiguous` bez eksportu | architektura §10 dopuszcza brak pliku przy `ambiguous`; na ukrytym zbiorze to same FN |
| P1 | **Kolejność czytania i niewidoczne tabele (S1)**, tekst w kolumnach | katalog wymienia to jako wymóg odczytu; E01 mierzy tylko pokrycie słów |
| P1 | **Błędna warstwa OCR w PDF (S5) i obraz na stronie tekstowej (S2)** | E04 ma trzy klasy stron; S5 wygląda jak „tekst” i przejdzie diagnozę |
| P1 | **Normalizatory formatów względem referencji** (daty, kwoty, NIP z kreskami, rachunek ze spacjami, wielkość liter) | dla identyfikatorów zgodność jest dokładna; to tanie punkty F1 niezależne od modułów |
| P1 | **Luki danych T6**: brak pełnomocnika, powód 12, brak BZP/TED, przelew-wpis, konsorcjum (lider) | 0/60 w danych; E09 mierzy „dokładność id” na rozkładzie bez klasy 12 |
| P1 | **Długie odwołania (10–11 stron) a limit kontekstu i czas** | E10 „jedno wywołanie na dokument” bez pomiaru ucinania |
| P1 | **Czas całego ukrytego zbioru na 4 rdzeniach** z OCR i limitem 429 | brak budżetu czasu u jury; E15 mierzy tylko 60 dokumentów tekstowych |
| P2 | **Instalacja z czystego `pip install -r requirements.txt` na 3.13**, bez sieci poza LLM, z wagami OCR w kole | model OCR pobierany przy pierwszym uruchomieniu = awaria u jury |
| P2 | **Windows** (`start.bat` w README organizatora): ścieżki, `fsync`, blokady SQLite | laptop biurowy; plan zakłada `systemd-run` i `flock`, czyli tylko Linux |

### 1.2. Mierniki złe lub niemierzalne

1. E01 „pokrycie słów względem referencji” — **referencji słów nie ma**. Jedyna dostępna prawda to JSON pól. Zamiennik: odsetek wartości referencyjnych odnajdywalnych w tekście odczytu po normalizacji (karty 180 dokumentów już to lokalizują).
2. E01/E05 „IoU z wzorcem” — **wzorca bbox nie ma**; plan nie przewiduje jego adnotacji. Mierzalne bez adnotacji: test obiegowy (wyrenderuj stronę, wytnij bbox, OCR/porównaj z cytatem) oraz narożniki po `/Rotate`.
3. E02 CER/WER — dla 3 skanów negatywnych i szablonu **nie ma transkrypcji**. Mierzalne tylko na rasteryzacji dokumentów z warstwą tekstu.
4. E03 „przyrost CER ≥ 10%” — nieokreślone, czy względny, czy w punktach; sformułowane odwrotnie (chodzi o spadek).
5. E04 „zero stron skanów oznaczonych jako tekst” — przy kilkunastu stronach skanów zero błędów nie daje żadnej gwarancji (reguła trzech: 0/15 ⇒ górna granica 95% ≈ 18%). Brak symetrycznej miary kosztu (strony tekstowe wysłane do OCR).
6. E05 „zero zgadniętych” — niefalsyfikowalne bez definicji operacyjnej; właściwa miara: odsetek kotwic, gdzie tekst słów pod bbox ≠ cytat.
7. E06 „brak fałszywych klasyfikacji negatywów” — 12 negatywów, w tym trzy kopie jednego ogłoszenia OJS; realnie ~10 niezależnych. Brak miary odwrotnej: pozytyw odrzucony jako obcy kosztuje wszystkie pola dokumentu (FN), a fałszywy pozytyw tylko FP.
8. E07 „≤ ustalony próg”, E08 „ustalona tolerancja”, E02 „próg ustalony po pomiarze” — progi po obejrzeniu wyniku to dopasowanie kryterium do danych.
9. E13 „wynik niezmieniony lub oznaczony do sprawdzenia” — drugi człon czyni test niefalsyfikowalnym (wszystko można oznaczyć).
10. E16 „zero różnic poza polami LLM z jawną wariancją” — w v1 wszystkie pola znaczeniowe pochodzą z LLM, więc wyjątek obejmuje prawie cały wynik.

### 1.3. Kryteria arbitralne

- E01 próg 0,99, E05 próg 0,95, E02 „RSS < 4 GB”: bez uzasadnienia i bez związku z F1. Limit 14 GB dla procesu przy 16 GB u jury nie uwzględnia systemu, przeglądarki GUI i antywirusa; realny budżet to raczej 8–10 GB — do ustalenia pomiarem na docelowej klasie maszyny.
- E09 „reguły tylko jeśli ≥ LLM” i E10 „najlepszy F1”: bez przedziału ufności i bez progu minimalnej różnicy. Na 11 sprawach kontrolnych różnica 1–2 pkt F1 to szum.
- Żadne kryterium nie waży kosztu rozmiaru modelu (etap 2), choć to 20 z 50 punktów „elastyczności”.

## 2. Ryzyka metodologiczne

2.1. **Przecieki (P0).** (a) `przyklad_40` w syntetykach — pkt 0.4. (b) Wszystkie 180 dokumentów pochodzi z jednego generatora („LAPFormalDoc”), więc zbiór kontrolny nie jest niezależny od rozwojowego: mierzy powtarzalność na tym samym szablonie, nie uogólnienie. (c) Kontrolny wybrano systematycznie (co piąta sprawa), nie losowo. (d) Przykłady few-shot i słowniki etykiet w promptach muszą pochodzić wyłącznie z rozwojowego — plan tego nie zapisuje. (e) „Kontrolny raz” jest nieegzekwowalne przy 16 eksperymentach i kilku agentach; potrzebny licznik użyć w repozytorium. (f) Prompty z eksperymentu przypadków brzegowych stroiły się na 41 dokumentach obejmujących sprawy z obu stron podziału.

2.2. **Próbka skanów (P0).** Jedyny pozytywny skan (szablon, 7 stron) nie ma referencji pól, a 3 skany negatywne testują wyłącznie router. Decyzja o OCR opierałaby się na 12 syntetykach z 3 spraw. Minimum: rasteryzacja 49 spraw rozwojowych (147 dokumentów) w 3–4 profilach degradacji + **fizyczny wydruk i skan ok. 10 spraw** (architektura §11 już to przewiduje; plan to pominął).

2.3. **Nierealistyczne syntetyki (P1).** Rasteryzacja czystego PDF + szum Gaussa + JPEG nie odtwarza: rastra drukarki, prześwitu drugiej strony, cienia grzbietu, perspektywy ze zdjęcia telefonem, pieczęci i podpisów na danych, dziurkacza, faksu 1-bit, skalowania przez sterownik skanera. Skany negatywne organizatora („z kserokopiarki”) i szablon 1240×1754 pt to jedyna próbka prawdziwego kanału. Trzeba wyznaczyć z nich profil (rozdzielczość, kompresja, szum, kąt) i dopasować do niego generator, a fizyczne skany traktować jako walidację generatora: jeśli F1 na fizycznych jest wyraźnie niższy niż na syntetycznych tych samych spraw, wyniki syntetyczne nie są podstawą decyzji.

2.4. **Pomiar czasu (P1).** `flock` szereguje nasze zadania, ale nie chroni przed: dławieniem termicznym laptopa, trybem oszczędzania, innymi agentami na maszynie, pierwszym uruchomieniem (ładowanie modelu ONNX, zimny cache dysku). Liczba wątków onnxruntime domyślnie = liczba rdzeni; przy współbieżności 4 daje to nadsubskrypcję i czas gorszy niż przy 1. Raportować: medianę i p95 z ≥5 powtórzeń, osobno zimny i ciepły start, ustawione jawnie `intra_op_num_threads`, model CPU i liczbę rdzeni. Czas LLM mierzyć osobno od CPU — zależy od sieci jury i limitu konta, nie od laptopa. RSS mierzyć dla całego drzewa procesów (cgroup `memory.peak`), nie dla procesu głównego; `prlimit` ogranicza przestrzeń adresową, nie RSS, i potrafi wywrócić onnxruntime z innego powodu niż brak pamięci.

2.5. **Wariancja LLM (P1).** Trzy powtórzenia nie wystarczą do oszacowania wariancji; `effort: medium` z niewyłączalnym „myśleniem” (eksperyment brzegowy) oznacza, że temperatura 0 nie daje determinizmu. Model ma w nazwie „Preview” — alias może zmienić się między pomiarem a oceną. Wymagane: ≥5 przebiegów na wariant, bootstrap po sprawach (nie po polach — pola jednej sprawy są skorelowane) dla przedziału F1, test sparowany między wariantami na tych samych dokumentach, zapis identyfikatora rewizji modelu z odpowiedzi API. Zmierzyć też odsetek odpowiedzi poza schematem (w eksperymencie 2/41 ≈ 5%) i jego koszt w F1 przy polityce ponowień.

2.6. **Wielokrotne porównania (P2).** E10 × E11 × progi routera × preprocessing to dziesiątki wariantów ocenianych na 49 sprawach; najlepszy wariant jest zawyżony przez sam wybór. Ograniczyć liczbę wariantów z góry i zgłaszać wynik kontrolny wyłącznie dla jednego, wcześniej zapisanego wyboru.

2.7. **Rozkład danych ≠ rozkład testu (P1).** W danych: 0 skanów pozytywnych, 0 spraw bez pełnomocnika, 0 powodów 12, przelewy głównie opłaty skarbowej. Wynik kontrolny będzie optymistyczny; raport musi podawać F1 osobno dla każdej luki z grupy C, z jawną liczebnością.

## 3. Wektory ataku na backend HTTP nieobjęte planem

Uwaga wstępna: testy mają sens dopiero na trasach z kontraktu (pkt 0.6). Do każdego testu: kryterium to jawny kod błędu, żywy `/healthz` po ataku, brak wzrostu RSS po zwolnieniu żądania, brak nowych plików poza `work/`.

| P | Wektor | Jak przetestować |
|---|---|---|
| P0 | **Wyciek klucza LLM** w odpowiedziach, logach, artefaktach i śladach wyjątków | ustawić klucz-kanarek (unikalny ciąg); wymusić 401, 429, timeout, błąd TLS, błąd walidacji; następnie `grep -r` kanarka po `work/`, logach, `events.jsonl`, `ai-response.json`, wszystkich odpowiedziach HTTP (w tym `/system`, 422, 500) i `/openapi.json`. Sprawdzić też nagłówek `Authorization`/`x-api-key` w logach debug `httpx` i w komunikatach wyjątków z URL-em |
| P0 | **Ścieżki plików w uploadzie**: `filename="../../x.json"`, ścieżka bezwzględna, `..\\` (Windows), NUL, nazwy `CON`/`NUL`, 300 znaków, Unicode NFC/NFD, dwie nazwy różne tylko wielkością liter, dwa pliki o tej samej nazwie w jednym wsadzie, podfolder `a/../../b` | multipart z `httpx` ustawiający surowe `filename`; po każdym żądaniu porównać listę plików poza katalogiem wsadu i wyjścia (migawka `find` przed/po). Architektura §7 wymaga odrzucenia przed pracą — sprawdzić, że odrzuca, a nie „naprawia” po cichu |
| P0 | **Wyczerpanie zasobów przy przyjmowaniu**: brak limitu rozmiaru ciała, części multipart, liczby plików | wysłać strumieniowo 2 GB bez `Content-Length`; 10 000 małych części; pole formularza 100 MB; powolne wysyłanie (1 bajt/s) na 50 połączeniach. Mierzyć RSS i miejsce w katalogu tymczasowym; oczekiwane 413 przed wczytaniem całości |
| P0 | **Bomby PDF**: strumień Flate 1 MB → 4 GB; strona 14 400 × 14 400 pt renderowana w 300 dpi (≈ 3,6 mld pikseli); obraz JBIG2/JPX o deklarowanych wymiarach 60 000²; 50 000 pustych stron; cykliczne `/Kids`, głęboko zagnieżdżone XObject; czcionka z milionem glifów | wygenerować pliki skryptem (pikepdf/qpdf jako narzędzie testowe); uruchamiać pod limitem pamięci cgroup; kryterium: `technical_error` z kodem w zadanym czasie, proces serwera nie zabity przez OOM. **Wymaga izolacji parsowania w procesie potomnym z limitem pamięci i czasu** — bez niej jeden plik zabija cały wsad |
| P0 | **Prompt injection — szerzej niż E13** | warianty: (a) instrukcja udająca komunikat systemowy lub zamknięcie bloku danych; (b) tekst niewidoczny: biały, 1 pt, poza MediaBox, pod obrazem, tryb renderowania 3 (niewidoczna warstwa OCR); (c) podmiana wartości zamiast „zwróć {}” — fałszywy NIP/rachunek w ukrytej warstwie, **wykrywalna tylko porównaniem warstwy tekstu z OCR renderu**; (d) instrukcja w skanie (dociera przez OCR); (e) polecenie ujawnienia promptu lub klucza w polu tekstowym wyniku; (f) wstrzyknięcie zmieniające klasę na `foreign` (wynik `{}` = utrata wszystkich pól). Miara: liczba pól zmienionych względem czystego dokumentu, osobno „zmiana na `null`” i „zmiana na wartość atakującego” |
| P1 | **SSRF i zasoby zewnętrzne z PDF**: `/URI`, `/GoToR`, `/Launch`, strumienie z `/F` i `/FFilter` (plik zewnętrzny), XFA/XXE, JavaScript `app.launchURL`, zdalne czcionki, załączniki | PDF wskazujący na `http://127.0.0.1:<port>/kanarek` i na `file:///etc/passwd`; lokalny serwer nasłuchujący rejestruje połączenia; dodatkowo uruchomić backend w przestrzeni sieciowej bez wyjścia poza endpoint LLM i sprawdzić, że nic się nie psuje. pdfium nie pobiera zasobów sam z siebie — test ma to potwierdzić dla faktycznie użytego czytnika i renderera, a nie zakładać |
| P1 | **SSRF przez konfigurację**: `ODWOLANIA2JSON_ENDPOINT` lub parametr API wskazujący endpoint/model | jeśli jakakolwiek trasa przyjmuje URL, endpoint lub ścieżkę (np. `input_path`, retry z innym modelem), podać `http://169.254.169.254/`, `file://`, `gopher://`; oczekiwane odrzucenie. Sprawdzić, czy klucz nie jest wysyłany do endpointu podanego przez klienta HTTP |
| P1 | **Brak uwierzytelnienia i wiązanie adresu**: serwer na `0.0.0.0`, CORS `*`, brak ochrony przed żądaniami z przeglądarki (DNS rebinding, formularz z obcej strony na `127.0.0.1`) | sprawdzić adres nasłuchu; wysłać żądanie z nagłówkiem `Host: evil.example` i `Origin: http://evil.example`; multipart z prostego formularza HTML (bez preflight) nie może utworzyć wsadu i zużyć klucza LLM |
| P1 | **IDOR i wyliczanie identyfikatorów**: odczyt PDF, tekstu strony i dowodów cudzego wsadu | sprawdzić, czy `batch_id`/`document_id` są losowe; pobrać `/documents/{id}` z identyfikatorem z innego wsadu; podać `run_id` z innego dokumentu; identyfikator w postaci `../` i zakodowany `%2e%2e%2f` |
| P1 | **Wyścigi we wsadzie** | równolegle: 20× retry tego samego zadania (oczekiwany jeden `run_id` aktywny, reszta konflikt rewizji); dwa wsady z tą samą nazwą wyjścia; odczyt `result` w trakcie `commit_run` (nigdy częściowy JSON); `kill -9` między zapisem artefaktu a manifestem, potem restart (stan `technical_error`, brak osieroconego `running`); dwa procesy serwera na tym samym `work/` (blokady SQLite: `database is locked` nie może dać 500 bez kodu) |
| P1 | **Zatrucie cache**: ten sam SHA-256, inna konfiguracja/prompt; wynik po awarii API | wgrać dokument, zmienić prompt lub model, wgrać ponownie — wynik musi być przeliczony; wymusić awarię API przy drugim wgraniu — nie może wrócić stary wynik (ADR-002 pkt 12). Dodatkowo: dwa różne PDF-y o tej samej nazwie w dwóch wsadach nie mogą dzielić wyniku |
| P1 | **Wyczerpanie budżetu LLM** (klucz zespołu u jury) | wsad 1000 dokumentów, pętla retry, dokument 500 stron tekstu; sprawdzić twardy limit wywołań i tokenów na dokument i wsad oraz zachowanie przy 429 z `Retry-After: 3600` (nie może wisieć godzinę) |
| P2 | **Treść dokumentu w odpowiedziach błędów i logach** (dane osobowe: PESEL, rachunki) | wgrać dokument z kanarkiem w treści, wymusić błąd na każdym etapie, `grep` kanarka w logach i w ciałach 4xx/5xx; pydantic domyślnie zwraca `input` w 422 |
| P2 | **XSS w GUI przez treść PDF**: tekst `<img onerror>` w nazwie pliku, metadanych, cytacie dowodu | sprawdzić typ treści odpowiedzi i ucieczkę w GUI; nazwa pliku w `Content-Disposition` bez wstrzyknięcia CRLF |
| P2 | **Wstrzyknięcie przez YAML klas**: jeśli API pozwala wgrać lub wskazać konfigurację klasy | `yaml.load` vs `safe_load`, wzorce regex o wykładniczym czasie (ReDoS) w konfiguracji i na wejściu: ciąg 50 000 cyfr i spacji przeciw wzorcom NIP/rachunku |
| P2 | **Polyglot i typ pliku**: `%PDF` po 1 MB śmieci, PDF+ZIP, PDF z nagłówkiem HTML, plik 0 bajtów, sam nagłówek, `Content-Type: application/pdf` dla PNG | macierz kombinacji rozszerzenie × typ MIME × magia; oczekiwany spójny kod, nie zależny od rozszerzenia |

E12 wymienia „ogromne obrazy” i „zagnieżdżone obiekty”, ale bez kryterium pamięci drzewa procesów i bez izolacji parsera — to dwie rzeczy, które decydują, czy atak jednym plikiem kończy cały wsad.

## 4. Proponowane zmiany planu (wg wpływu na F1 na ukrytym zbiorze)

**P0 — przed jakimkolwiek pomiarem**

1. **Dodaj E00: napraw i zwaliduj ewaluator** (pkt 0.1–0.3): zgodna wartość = TP; błędna = tylko FP; próg 80% dla pięciu wskazanych pól (zmierzyć dwa–trzy warianty podobieństwa i raportować rozrzut, bo algorytmu nie podano); listy dopasowywane element do elementu po najlepszym przypisaniu, z oceną pól wewnątrz elementu. Test: referencja vs referencja = 1,0. Naprawa z testem, który dziś zawodzi (AGENTS.md).
2. **Dodaj zestaw „skany z referencją”**: rasteryzacja 147 dokumentów rozwojowych w profilach dopasowanych do skanów organizatora + dokumenty mieszane; osobno 33 kontrolne, generowane z osobnego ziarna i nietykane. Usuń z użycia syntetyki pochodzące z `przyklad_40` albo przenieś je do kontrolnego. Dodaj test blokujący: żaden plik eksperymentu rozwojowego nie pochodzi ze sprawy kontrolnej.
3. **Zmień miarę E02/E03/E04 na F1 pól end-to-end per typ wejścia**; CER zostaje jako miara pomocnicza. Decyzja OCR = różnica F1 skan vs tekst na tych samych sprawach (para), z przedziałem z bootstrapu po sprawach.
4. **Zmień E11**: dodaj wariant D (tekst PDF/OCR + **obraz strony** do LLM jednocześnie) i wariant bazowy „sam regex + router regułowy, bez LLM” jako dolną granicę. Raport per typ wejścia i per pole, nie jedna liczba.
5. **Dodaj E17: polityka `null`/eksportu a F1** — porównaj: `ambiguous` → brak pliku vs najlepsza klasa; pole niezakotwiczone → `null` vs wartość; awaria LLM → `{}` vs wynik z samych regexów. Architektura §4.5 zeruje pole bez kotwicy; przy definicji F1 z `zasady-f1.md` to czysta strata, gdy wartość jest w dokumencie. **Bbox dowodu nie może decydować o treści ocenianego JSON** — zmierzyć koszt tej reguły i ją odwrócić, jeśli kosztuje.
6. **Dodaj E18: wybór modelu LLM** — ten sam prompt i dane na 2–3 modelach różnej wielkości dostępnych z UE; kryterium zapisane z góry (np. mniejszy model wygrywa, jeśli traci mniej niż ustalona liczba punktów F1).

**P1 — po działającym pomiarze**

7. **Dodaj fizyczne skany ~10 spraw rozwojowych** (wydruk, skaner biurowy, zdjęcie telefonem) jako walidację generatora syntetycznego.
8. **Dodaj E19: normalizatory vs referencje** — dla każdego pola formatowego odsetek zgodności po normalizacji na rozwojowym; to mierzalne dziś, bez LLM i OCR.
9. **Dodaj E20: obecność pola** — FP na polach z referencją `null` per wariant; plus grupa C (brak pełnomocnika, powód 12, brak BZP/TED, wpis).
10. **Zmień E06**: miara dwustronna (pozytyw → obcy liczony w utraconych polach); dołóż negatywy zbliżone do klas (pełnomocnictwo do innej sprawy, wyciąg bankowy, polecenie przelewu niezrealizowane, odpowiedź na odwołanie, sprzeciw, skarga na orzeczenie KIO). 12 negatywów organizatora nie wystarczy.
11. **Zmień E10**: ≥5 powtórzeń, bootstrap po sprawach, zapis rewizji modelu, pomiar odsetka odpowiedzi poza schematem i skuteczności jednego ponowienia; usuń „temperatura 0” jako gwarancję stabilności.
12. **Zmień E01/E05**: zastąp „pokrycie słów” i „IoU z wzorcem” miarami bez adnotacji (pkt 1.2); dodaj kolejność czytania na przelewach o dwóch układach bankowych.
13. **Zapisz progi przed pomiarem** (E02, E07, E08) albo zamień je na reguły porównawcze („wariant X zastępuje Y, jeśli dolna granica przedziału różnicy F1 > 0”).
14. **Rozszerz część D** o tabelę z pkt 3 i uruchamiaj ją wyłącznie na trasach z `openapi.yaml`; do tego czasu oznacz E12–E16 jako niewykonalne zamiast mierzyć warstwę z `experiments/`.

**P2**

15. **Zmień pomiar zasobów**: budżet pamięci drzewa procesów z cgroup, jawna liczba wątków, zimny/ciepły start, p95; dodaj przebieg na Windows.
16. **Dodaj test instalacji** z czystego środowiska 3.13 bez sieci po `pip install`.
17. **Usuń** kryterium E16 w obecnym brzmieniu; zastąp: identyczność bajtowa JSON przy tych samych odpowiedziach LLM odtworzonych z zapisu (determinizm kodu oddzielony od wariancji modelu).
18. **Usuń** z E02 skany negatywne i szablon jako źródło CER (brak transkrypcji); zostają do testu routera i jako wzorzec profilu skanu.

Kolejność wykonania: E00 → zestaw skanów → E19/E01 → E11 (bazowy i A) → E02–E04 w mierze F1 → E18/E10 → E17/E20 → E06/E07/E09 → część D na prawdziwych trasach.

## 5. Zalecany zestaw modułów dla CPU + 16 GB

To hipoteza wyjściowa do obalenia pomiarem, nie wynik. Wersji i kół dla 3.13 nie weryfikowałem poza tym, co jest w `apps/backend/requirements.txt`.

| Moduł | Zalecenie | Uzasadnienie | Co zmieniłoby zdanie |
|---|---|---|---|
| Czytnik PDF i renderer | **pypdfium2** (już przypięty w zależnościach, licencja liberalna, jeden komponent do tekstu z geometrią i do rasteryzacji) | ten sam silnik daje słowa i obraz, więc układ współrzędnych tekstu i renderu jest spójny — warunek kotwiczenia i diagnozy strony; brak zależności systemowych przy pip | odnajdywalność wartości referencyjnych w tekście < ~99% na rozwojowym, błędna kolejność czytania na przelewach (S1), błędy `/Rotate`; albo własny czytnik zespołu z lepszym wynikiem na tym samym zestawie. ADR-002 pkt 3 odrzuca pypdfium2 jako docelowy — bez konkurenta zmierzonego w E01 ta decyzja nie ma podstawy pomiarowej w żadną stronę |
| OCR | **Lokalny OCR ONNX na CPU (rapidocr + onnxruntime) jako bazowy**, render 200 dpi (do potwierdzenia: 150 vs 200 vs 300), z jawną liczbą wątków; własny model zespołu za tym samym kontraktem, gdy wygra | lokalnie = brak kosztu i limitu API, dane osobowe nie opuszczają maszyny, deterministyczny; daje bbox słów potrzebne do dowodów | F1 pól na skanach wyraźnie niższy niż w wariancie „obraz do LLM”; polskie znaki diakrytyczne psujące nazwy poniżej progu 80%; czas na stronę przekraczający budżet wsadu; brak koła na 3.13 lub wagi pobierane z sieci przy starcie. Tesseract jako drugi kandydat odpada przy dostawie wyłącznie przez pip (binarka systemowa) |
| Diagnoza strony | reguły: liczba słów warstwy tekstu, pokrycie strony obrazem, zgodność warstwy tekstu z szybkim OCR próbki (wykrycie S5) | tanie, deterministyczne; błąd kosztuje asymetrycznie, więc próg ustawić na „raczej OCR” | fałszywe OCR stron tekstowych pogarszające F1 lub czas |
| Router | **hybryda w jednym wywołaniu**: sygnały regułowe tylko do taniego odrzucenia oczywistych przypadków i jako kontrola; klasa z tego samego wywołania LLM co pola (architektura §3) | osobne wywołanie klasyfikatora podwaja koszt i czas; w eksperymencie brzegowym modele miały trafność klasy 0,976–1,0 na 41 dokumentach — mało, ale kierunek jasny; przy niepewności **preferować klasę nad `foreign`**, bo fałszywe `{}` traci wszystkie pola | jeśli negatywy zbliżone do klas (pkt 4.10) dają dużo fałszywych pozytywów z dużą liczbą FP pól — wtedy osobny, tani krok routera |
| Pola formatowe | regex + normalizatory + sumy kontrolne (NIP, REGON, rachunek) na tekście PDF i OCR; suma kontrolna jako filtr błędów OCR (O/0, l/1) | dokładna zgodność wymagana przez ewaluację; walidacja sumą kontrolną odrzuca błędy OCR bez LLM | referencje organizatora zawierające identyfikatory z błędną sumą kontrolną — wtedy suma tylko jako sygnał, nie filtr (sprawdzić na 180 dokumentach przed włączeniem) |
| Role, podmioty, czynność | LLM; regex dostarcza kandydatów, LLM przypisuje rolę | katalog T1–T4: etykiety ról nie są wiarygodne (brak etykiety w 18/180, etykieta po danych w 62/180) | reguły ≥ LLM w E07/E09 z rozłącznym przedziałem |
| Wywołanie LLM | **jedno wywołanie na dokument, wejście: tekst z układem (linie, identyfikatory słów) + dla stron z OCR lub niskiej jakości także obraz strony**; wymuszony schemat (tool use / structured output), walidacja pydantic, jedno ponowienie przy błędzie schematu, twardy limit czasu i tokenów; współbieżność 2–4 ograniczona limitem konta | tekst jest tańszy i daje kotwice; obraz ratuje błędy OCR i układ; schemat ogranicza 5% odpowiedzi poza formatem zaobserwowane w eksperymencie | „sam obraz” (wariant C) ≥ tekst+OCR na skanach przy akceptowalnym koszcie → OCR zostaje tylko do dowodów; albo dwa wywołania (klasa, potem pola) wygrywają o więcej niż szum |
| Model | **najmniejszy model, który trzyma F1**; MiniMax Flash do rozwoju, ale decyzja po E18 | etap 2: do 20 pkt za mały model; etap 1 to 100% F1, więc najpierw nie stracić preselekcji — duży model jest uzasadniony tylko mierzalną przewagą F1 | wynik E18; potwierdzenie mentora co do licencji (ADR-002 odnotowuje licencję społecznościową, nie OSI) i hostingu — użytkownik zamknął kwestię hostingu, kwestia licencji „open source” pozostaje nierozstrzygnięta w dokumentach |

Budżet pamięci, który trzeba potwierdzić: serwer + SQLite + pdfium, render jednej strony A4 w 200 dpi (~12 MB RGB), sesja ONNX OCR i GUI w przeglądarce powinny zmieścić się z dużym zapasem w 16 GB; ryzykiem nie jest średnie zużycie, tylko pojedynczy złośliwy lub nietypowy plik (strona 1240×1754 pt renderowana w 300 dpi, bomby z pkt 3) — stąd limit pikseli na stronę i izolacja parsera są częścią zestawu, nie dodatkiem.

## 6. Czego nie sprawdziłem

- Nie uruchamiałem backendu, OCR ani LLM; nie mierzyłem czasu ani pamięci.
- Nie weryfikowałem dostępności kół rapidocr/onnxruntime dla Pythona 3.13 ani ich licencji.
- Twierdzenie o pochodzeniu syntetyków z `przyklad_40` pochodzi z dokumentu eksperymentu; skrypt wybiera sprawy dynamicznie, a pliku `syntetyczne.json` nie ma w Git.
- Zachowanie ewaluatora sprawdziłem jednym wywołaniem `compare_document`; pełnego zestawu testów nie uruchamiałem.
