# E12: złośliwe i uszkodzone wejścia (atak na uprząż HTTP)

> **Zakres.** Wynik opisuje **uprząż** `harness/server.py` (FastAPI, 127.0.0.1, bez uwierzytelniania), **nie produkt**. Backend z kontraktu v1 nie istnieje, więc każda luka poniżej jest testem do przeniesienia do produktu, a brak luki w uprzęży nie dowodzi bezpieczeństwa produktu.
> **Czas i RSS.** Liczby czasu i pamięci zebrano pod obciążeniem maszyny (load avg ok. 27–35 na 8 rdzeniach, cztery grupy liczą naraz): są **niewiążące** i nie służą do decyzji. Wiążące są wyniki jakościowe (kody błędów, przeżycie serwera, wyciek tak/nie) i rząd wielkości pamięci (zależy od rozmiaru bomby, nie od obciążenia).

## Hipoteza i kryterium (plan E12)

Każde uszkodzone lub złośliwe wejście kończy się jawnym `technical_error` z kodem, serwer żyje i obsługuje potem poprawny dokument, bez zapisu poza obszarem pracy, bez zawieszenia i bez wzrostu pamięci ponad limit. Kryterium z planu: *zawsze jawny `technical_error`, serwer żyje*.

## Metoda

Skrypt: `.venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/E12/e12.py` (wszystko jednym poleceniem; `--only grupa`, `--bombs B01,B08`). Wynik surowy: `wyniki.json` (każdy wektor: oczekiwane, faktyczne, luka, poprawka, test, dane; wersje i konfiguracja w nagłówku).

Serwer startuje jako podproces pod `systemd-run --user --scope -p MemoryMax=14G -p MemorySwapMax=0` (szczyt pamięci z `memory.peak` cgroup i próbnika RSS całego drzewa procesów). **Wyjątek:** bomby PDF (B01–B11) uruchamiano z limitem **6 GB**, a nie 14 GB, bo maszyna jest współdzielona z innymi grupami, a OOM przy 14 GB groził im; pamięć rośnie z rozmiarem bomby, więc wnioski przenoszą się na 14 GB z większym ładunkiem. Po każdej grupie wektorów: `/health` i poprawny przelew ze zbioru rozwojowego musi dać wynik (`probes` w `wyniki.json`). Klient: `httpx`; surowe multipart (nazwy plików wstawiane bajt w bajt) z `lib.raw_multipart`. Dane: tylko zbiór rozwojowy i PDF-y generowane skryptem. Klucza LLM tu nie ma (router i ekstraktor regułowe).

Grupy: **nazwy plików N01–N16** (traversal, ścieżka bezwzględna, separator Windows, `%2e`, NUL, CON, 300 znaków, NFD, podfolder, pusta, CRLF/HTML, kropka, duplikaty, wielkość liter, przerwany upload; migawka plików przed/po w sandboxie i katalogu uprzęży), **typ pliku T01–T11** (0 B, sam nagłówek, PNG jako `.pdf`, HTML, `%PDF` po 1 MB śmieci, poliglot PDF+ZIP, obcięty, 0 stron, zaszyfrowany), **ścieżki/IDOR/nagłówki/XSS P01–P06** (traversal w trasie artefaktów w 8 kodowaniach, symlinki do kanarka poza workspace, identyfikatory jako ścieżka, ścieżki hosta w `/system`, obcy `Host`/`Origin`, XSS w nazwie i treści), **wyczerpanie przy przyjmowaniu F01–F04** (1 GiB bez Content-Length, 1001 części, pole 100 MB, 50 wolnych połączeń), **bomby PDF B01–B11**, **SSRF z PDF S01–S02** (nasłuch loopback + kanarek pliku `file://`), **ReDoS R01**.

## Jak to działa i dlaczego tak wyszło

- **Nazwy plików nigdy nie trafiają na dysk.** Serwer zapisuje wsad jako `.../documents/<id>/input.pdf`; nazwa jest tylko metadaną, oczyszczaną przez `_safe_name` (basename + zamiana znaków spoza `\w.\- ` na `_`, 120 znaków). Dlatego traversal nie zapisał nic poza obszarem pracy (zero nowych plików poza `data/` w 12 wariantach), a luka to **ciche „naprawianie”** nazw (architektura §7 każe odrzucać) i **psucie legalnych nazw** (NFD z polskimi znakami → `za_z_o_ł_c.pdf`, `%2e` → `_2e`), przez co mapowanie wejście→wynik opiera się na ID, nie na nazwie.
- **Typ pliku** rozstrzyga nagłówek `%PDF-` w pierwszym 1024 B oraz pdfium; rozszerzenie i MIME są ignorowane (spójnie, bez zależności od `.pdf`). Poliglot PDF+ZIP jest przyjęty jako PDF (poprawnie dla czytnika, ale plik zawiera drugi format).
- **Trasa `/documents/{id}/artifact/{name:path}`** ma obronę `resolve()` + sprawdzenie prefiksu, więc traversal i symlinki (do kanarka, do cudzego dokumentu, do katalogu) nie czytają niczego. Ale `%00` w ścieżce daje `ValueError` przed obsługą → nieobsłużony wyjątek 500 / zerwane połączenie (P01).
- **Identyfikatory** to `b`+12 hex (48 bit) z `secrets.token_hex(6)` i sufiks `-dNNN`; brak uwierzytelniania, więc każdy, kto zna ID, czyta wynik (IDOR „z założenia MVP”, ale 48 bit to mało dla wzmianki w ADR).
- **Wyczerpanie przy przyjmowaniu.** Limit 30 MiB egzekwuje się dopiero po wczytaniu całego strumienia: serwer czyta do końca (starlette spool na dysk/tmpfs) i odrzuca nadmiar, więc 1 GiB bez Content-Length zajmuje ≈1 GiB `/tmp` (tmpfs = RAM) i kilka sekund (F01). Części multipart (>1000) i pola >1 MB odrzuca starlette z 400 bez kodu API. Wolne połączenia (50 × 1 B/s) nie blokują pętli zdarzeń (`/health` ≤ ~12 ms), ale nie są odcinane.
- **Bomby PDF.** PDFium rozpakowuje strumień treści strony do pamięci: 1 MB Flate → ~1 GiB RSS, 4 GiB treści → 5,2 GiB RSS (blisko limitu 6 GB, wynik `technical_error` tylko dlatego, że bomba mieściła się w limicie). Strona 14400×14400 pt renderowana (200 dpi) kosztuje 4,6 GB zanim pdfium odmówi. Obrazy 60 000² Flate i 30 000² JPEG nie rozpakowują się przy skali A4 (pdfium skaluje), więc nie dały wzrostu pamięci. 50 000 stron i cykliczne `/Kids` kończą się szybko (`page_limit`, `pdf_corrupted`). **Samoodwołujący się XObject Form (B08) zabił serwer:** pamięć rosła do limitu w ~24 s (OOM, proces serwera zabity razem z wsadem). Mechanizm w pdfium nie został rozstrzygnięty (nie jest to render obrazu; próba odtworzenia w osobnym procesie pod `ulimit -v` nie dała czytelnego wyniku, bo limit przestrzeni adresowej wyłącza sam start interpretera).
- **Brak izolacji parsera** jest przyczyną B08: odczyt PDFium działa w wątku procesu serwera pod `PDFIUM_LOCK`; `deadline` sprawdzany jest tylko między stronami, więc jedna strona nie jest przerywalna.
- **SSRF z PDF.** PDFium w tej konfiguracji (bez V8/XFA, bez środowiska formularzy) nie wykonuje akcji URI/GoToR/Launch/JS ani nie otwiera strumieni zewnętrznych (`/F`, `/FFilter`), XXE w XFA ani `file://`: nasłuch loopback zanotował 0 połączeń, kanarek z pliku nie pojawił się w artefaktach (ścieżka tekstowa i ścieżka renderu).
- **ReDoS.** Czas normalizatorów produkcyjnych (`odwolania2json.domain.normalize`) i wzorców regułowych uprzęży na 10 rodzinach wejść do 50 000 znaków: najgorszy 0,15 s (`date`, n=50 000) i wzrost zbliżony do liniowego; dokument z długimi liniami przeszedł HTTP w 0,7 s.

## Ograniczenia

Jedna maszyna, jedna wersja pdfium (pypdfium2 5.15.2 / Python 3.13.18); limit 6 GB dla bomb zamiast 14 GB; bomb JBIG2/JPX i czcionki z milionem glifów nie wykonano (brak generatora; najbliższy wariant: Flate i DCT o deklarowanych wymiarach); DNS nie jest monitorowany (monitor tylko loopback), więc „brak połączeń” dotyczy połączeń TCP do nasłuchu; zagnieżdżenie 200 000 poziomów trafiło w parser jako obiekt niepodpięty do strony (ścieżka odczytu nie sięga go, więc to test odporności parsera, nie ścieżki ekstrakcji). Nie zbadano slowloris z przekroczeniem limitu deskryptorów plików ani wyczerpania dysku trwałego.

## Wyniki wektorów

### Zestawienie wektorów

Wektorów: 51; luka: częściowo 16, nie 31, tak 4.

| ID | Rodzina | Wektor | Luka |
|---|---|---|---|
| B01 | bomba-PDF | strumień Flate 1 MB → ~1 GiB treści strony | **nie** |
| B02 | bomba-PDF | strumień Flate → 4 GiB treści strony | **częściowo** |
| B03 | bomba-PDF | strona 14400×14400 pt (200 dpi ⇒ 40 000² px) jako skan | **częściowo** |
| B04 | bomba-PDF | obraz Flate deklarujący 60 000² (3,6 GB po dekompresji) | **nie** |
| B05 | bomba-PDF | obraz JPEG (DCT) 30 000² (0,9 Gpx) | **nie** |
| B06 | bomba-PDF | 50 000 pustych stron | **nie** |
| B07 | bomba-PDF | cykliczne /Kids | **nie** |
| B08 | bomba-PDF | samoodwołujący się XObject Form (/Fm Do) | **tak** |
| B09 | bomba-PDF | obiekt zagnieżdżony na 200 000 poziomów | **nie** |
| B10 | bomba-PDF | 400 000 małych obiektów | **nie** |
| B11 | bomba-PDF | 25 MB (po kompresji) operatorów graficznych | **nie** |
| F01 | zasoby-upload | 1 GiB strumieniowo bez Content-Length (chunked), limit uprzęży 30 MiB | **tak** |
| F02 | zasoby-upload | 1001 małych części multipart (starlette: max_files=1000) | **nie** |
| F03 | zasoby-upload | pole formularza 100 MB (nie plik) | **nie** |
| F04 | zasoby-upload | 50 wolnych połączeń (1 B/s, Content-Length 100 MB) przez 25 s | **częściowo** |
| N01 | upload-nazwa | traversal ../../x.json | **częściowo** |
| N02 | upload-nazwa | ścieżka bezwzględna /etc/cron.d/x | **częściowo** |
| N03 | upload-nazwa | separator Windows ..\..\x.pdf | **częściowo** |
| N04 | upload-nazwa | kodowanie %2e%2e%2f | **częściowo** |
| N05 | upload-nazwa | NUL w nazwie | **częściowo** |
| N06 | upload-nazwa | zarezerwowane CON/NUL | **nie** |
| N07 | upload-nazwa | 300 znaków | **częściowo** |
| N08 | upload-nazwa | Unicode NFD | **częściowo** |
| N09 | upload-nazwa | podfolder a/../../b | **częściowo** |
| N10 | upload-nazwa | pusta nazwa | **częściowo** |
| N11 | upload-nazwa | nazwa z CRLF i znacznikami HTML | **częściowo** |
| N12 | upload-nazwa | nazwa zaczynająca się od kropki (ukryty plik) | **nie** |
| N13 | upload-nazwa | duplikat/wielkość liter: A.pdf + a.pdf | **nie** |
| N14 | upload-nazwa | duplikat/wielkość liter: dup.pdf + dup.pdf | **nie** |
| N15 | upload-nazwa | duplikat/wielkość liter: sub1/same.pdf + sub2/same.pdf | **nie** |
| N16 | upload-nazwa | przerwany upload (zamknięcie połączenia w połowie ciała) | **nie** |
| P01 | odczyt-ścieżek | traversal w /documents/{id}/artifact/{name:path} (8 kodowań) | **częściowo** |
| P02 | odczyt-ścieżek | symlink w katalogu przebiegu: do pliku-kanarka poza workspace, do cudzego dokumentu, do katalogu | **nie** |
| P03 | IDOR | identyfikatory jako ścieżka i dostęp do cudzego wsadu | **częściowo** |
| P04 | odczyt-ścieżek | ujawnienie ścieżek hosta w /system i w błędach | **tak** |
| P05 | wiązanie/CSRF | Host: evil.example, Origin obcy, formularz bez preflight | **tak** |
| P06 | XSS | HTML/JS w nazwie pliku i treści PDF: czy wraca nieescapowane w JSON i jaki Content-Type | **częściowo** |
| R01 | ReDoS | wzorce normalizatorów produkcyjnych (apps) i regułowe uprzęży na ciągach do 50 000 znaków (10 rodzin wejść × 3 rozmiary) | **nie** |
| S01 | SSRF-z-PDF | PDF z akcjami URI/GoToR/Launch/JS/XFA(XXE)/F+FFilter/EmbeddedFile + file:// — wariant: tekst | **nie** |
| S02 | SSRF-z-PDF | PDF z akcjami URI/GoToR/Launch/JS/XFA(XXE)/F+FFilter/EmbeddedFile + file:// — wariant: skan (render) | **nie** |
| T01 | typ-pliku | plik 0 bajtów | **nie** |
| T02 | typ-pliku | sam nagłówek %PDF-1.7 | **nie** |
| T03 | typ-pliku | PNG z Content-Type application/pdf i nazwą .pdf | **nie** |
| T04 | typ-pliku | nagłówek HTML + treść | **nie** |
| T05 | typ-pliku | %PDF po 1 MB śmieci (poza oknem 1024 B) | **nie** |
| T06 | typ-pliku | poliglot PDF + ZIP doklejony na końcu | **nie** |
| T07 | typ-pliku | śmieci przed %PDF w oknie 1024 B | **nie** |
| T08 | typ-pliku | obcięty PDF (połowa bajtów) | **nie** |
| T09 | typ-pliku | PDF z 0 stron (Count 0) | **nie** |
| T10 | typ-pliku | dobry PDF z rozszerzeniem .exe i MIME text/plain | **nie** |
| T11 | typ-pliku | zaszyfrowany PDF (słownik /Encrypt, hasło użytkownika) | **nie** |

### Szczegóły: oczekiwane, faktyczne, poprawka, test do produktu

**B01 — strumień Flate 1 MB → ~1 GiB treści strony** (luka: nie)

- Oczekiwane: technical_error w limicie, bez OOM
- Faktyczne: outcome=technical_error kody=['empty_document']; 4.41 s; serwer_zabity=False; zawieszenie=False; szczyt RSS drzewa 2093.3 MiB, cgroup peak 2097.9 MiB (limit 6G); kontrola po ataku: {'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b01_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**B02 — strumień Flate → 4 GiB treści strony** (luka: częściowo)

- Oczekiwane: technical_error w limicie, bez OOM
- Faktyczne: outcome=technical_error kody=['empty_document']; 10.16 s; serwer_zabity=False; zawieszenie=False; szczyt RSS drzewa 5166.7 MiB, cgroup peak 5194.8 MiB (limit 6G); kontrola po ataku: {'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b02_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**B03 — strona 14400×14400 pt (200 dpi ⇒ 40 000² px) jako skan** (luka: częściowo)

- Oczekiwane: odrzucenie przed renderem lub limit pikseli
- Faktyczne: outcome=technical_error kody=['pdf_corrupted']; 5.2 s; serwer_zabity=False; zawieszenie=False; szczyt RSS drzewa 4605.8 MiB, cgroup peak 4636.3 MiB (limit 6G); kontrola po ataku: {'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b03_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**B04 — obraz Flate deklarujący 60 000² (3,6 GB po dekompresji)** (luka: nie)

- Oczekiwane: limit pikseli obrazu
- Faktyczne: outcome=technical_error kody=['ocr_unavailable']; 5.11 s; serwer_zabity=False; zawieszenie=False; szczyt RSS drzewa 182.1 MiB, cgroup peak 161.1 MiB (limit 6G); kontrola po ataku: {'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b04_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**B05 — obraz JPEG (DCT) 30 000² (0,9 Gpx)** (luka: nie)

- Oczekiwane: limit pikseli obrazu
- Faktyczne: outcome=technical_error kody=['ocr_unavailable']; 0.97 s; serwer_zabity=False; zawieszenie=False; szczyt RSS drzewa 117.8 MiB, cgroup peak 110.0 MiB (limit 6G); kontrola po ataku: {'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b05_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**B06 — 50 000 pustych stron** (luka: nie)

- Oczekiwane: page_limit natychmiast
- Faktyczne: outcome=technical_error kody=['page_limit']; 0.28 s; serwer_zabity=False; zawieszenie=False; szczyt RSS drzewa 75.0 MiB, cgroup peak 58.6 MiB (limit 6G); kontrola po ataku: {'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b06_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**B07 — cykliczne /Kids** (luka: nie)

- Oczekiwane: pdf_corrupted bez zawieszenia
- Faktyczne: outcome=technical_error kody=['pdf_corrupted']; 0.03 s; serwer_zabity=False; zawieszenie=False; szczyt RSS drzewa 62.7 MiB, cgroup peak 39.9 MiB (limit 6G); kontrola po ataku: {'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b07_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**B08 — samoodwołujący się XObject Form (/Fm Do)** (luka: tak)

- Oczekiwane: brak zawieszenia, limit głębokości
- Faktyczne: outcome=None kody=None; 24.08 s; serwer_zabity=True; zawieszenie=False; szczyt RSS drzewa 6126.3 MiB, cgroup peak None MiB (limit 6G); kontrola po ataku: {'alive': False}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b08_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**B09 — obiekt zagnieżdżony na 200 000 poziomów** (luka: nie)

- Oczekiwane: pdf_corrupted bez przepełnienia stosu
- Faktyczne: outcome=technical_error kody=['empty_document']; 0.04 s; serwer_zabity=False; zawieszenie=False; szczyt RSS drzewa 62.7 MiB, cgroup peak 43.0 MiB (limit 6G); kontrola po ataku: {'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b09_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**B10 — 400 000 małych obiektów** (luka: nie)

- Oczekiwane: limit czasu/pamięci, bez zawieszenia
- Faktyczne: outcome=technical_error kody=['empty_document']; 0.81 s; serwer_zabity=False; zawieszenie=False; szczyt RSS drzewa 110.2 MiB, cgroup peak 115.4 MiB (limit 6G); kontrola po ataku: {'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b10_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**B11 — 25 MB (po kompresji) operatorów graficznych** (luka: nie)

- Oczekiwane: limit czasu, bez zawieszenia
- Faktyczne: outcome=technical_error kody=['empty_document']; 1.08 s; serwer_zabity=False; zawieszenie=False; szczyt RSS drzewa 99.2 MiB, cgroup peak 90.5 MiB (limit 6G); kontrola po ataku: {'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.
- Test do przeniesienia do produktu: `test_pdf_bomb_b11_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)`

**F01 — 1 GiB strumieniowo bez Content-Length (chunked), limit uprzęży 30 MiB** (luka: tak)

- Oczekiwane: 413 przed wczytaniem całości; RSS i dysk bez wzrostu proporcjonalnego do rozmiaru
- Faktyczne: HTTP 201; po 4.9 s; stan dokumentu=('technical_error', ['upload_too_large']); szczyt zajętego /tmp (tmpfs=RAM) ≈ 1054 MiB; RSS drzewa serwera 64.8 MiB
- Proponowana poprawka: Limit na poziomie ciała (reverse proxy/middleware ASGI: przerwać po przekroczeniu `max_upload_bytes`, nie czytać reszty); `Content-Length` > limit → 413 natychmiast; spool poza tmpfs.
- Test do przeniesienia do produktu: `test_oversized_chunked_upload_aborted_with_413_without_reading_all`

**F02 — 1001 małych części multipart (starlette: max_files=1000)** (luka: nie)

- Oczekiwane: odmowa (400/413) bez przetwarzania części
- Faktyczne: HTTP 400 {"detail":"Too many files. Maximum number of files is 1000."}
- Proponowana poprawka: Jawny limit liczby plików z kodem `upload_too_large` (jest `max_batch_documents`=500, ale middleware starlette odrzuca wcześniej z 400 bez kodu API).
- Test do przeniesienia do produktu: `test_too_many_parts_returns_documented_error_code`

**F03 — pole formularza 100 MB (nie plik)** (luka: nie)

- Oczekiwane: 413/400 bez wczytania całości
- Faktyczne: HTTP 400 {"detail":"Part exceeded maximum size of 1024KB."} po 1.1 s; RSS 69.2 MiB
- Proponowana poprawka: Odrzucać nieznane pola formularza; limit rozmiaru pola.
- Test do przeniesienia do produktu: `test_unknown_large_form_field_rejected`

**F04 — 50 wolnych połączeń (1 B/s, Content-Length 100 MB) przez 25 s** (luka: częściowo)

- Oczekiwane: serwer obsługuje poprawne żądania; połączenia odcięte po limicie bezczynności
- Faktyczne: /health: max 0.0119 s, błędy 0; kontrola poprawnego dokumentu={'health': 200, 'clean_doc': 'partial', 'alive': True}; połączenia nie zostały odcięte przez serwer w 25 s
- Proponowana poprawka: uvicorn `--timeout-keep-alive` nie obejmuje ciała; dodać limit czasu odczytu ciała (reverse proxy) i limit równoległych połączeń na upload.
- Test do przeniesienia do produktu: `test_slow_upload_connections_do_not_block_valid_requests`

**N01 — traversal ../../x.json** (luka: częściowo)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='x.json'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N02 — ścieżka bezwzględna /etc/cron.d/x** (luka: częściowo)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='x.pdf'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N03 — separator Windows ..\..\x.pdf** (luka: częściowo)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='evil.pdf'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N04 — kodowanie %2e%2e%2f** (luka: częściowo)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='_2e_2e_2f_2e_2e_2fevil.pdf'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N05 — NUL w nazwie** (luka: częściowo)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='ok_.pdf'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N06 — zarezerwowane CON/NUL** (luka: nie)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='CON.pdf'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N07 — 300 znaków** (luka: częściowo)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N08 — Unicode NFD** (luka: częściowo)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='za_z_o_ł_c.pdf'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N09 — podfolder a/../../b** (luka: częściowo)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='b.pdf'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N10 — pusta nazwa** (luka: częściowo)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='plik.pdf'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N11 — nazwa z CRLF i znacznikami HTML** (luka: częściowo)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='_x'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N12 — nazwa zaczynająca się od kropki (ukryty plik)** (luka: nie)

- Oczekiwane: brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu
- Faktyczne: HTTP 201; zapisana nazwa='.htaccess'; pliki na dysku=['input.pdf', 'runs']; poza obszarem pracy: 0
- Proponowana poprawka: Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).
- Test do przeniesienia do produktu: `test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)`

**N13 — duplikat/wielkość liter: A.pdf + a.pdf** (luka: nie)

- Oczekiwane: dwa osobne dokumenty, brak nadpisania, mapowanie wejście→wynik zachowane
- Faktyczne: ids=['b6150353a3021-d001', 'b6150353a3021-d002'] unikalne=True; nazwy=['A.pdf', 'a.pdf']; wyniki=['partial', 'partial']
- Proponowana poprawka: Zachować oryginalną nazwę w metadanych (UTF-8) obok ID; porównywać wielkość liter przy raportowaniu duplikatów.
- Test do przeniesienia do produktu: `test_same_basename_two_documents_get_distinct_ids_and_results`

**N14 — duplikat/wielkość liter: dup.pdf + dup.pdf** (luka: nie)

- Oczekiwane: dwa osobne dokumenty, brak nadpisania, mapowanie wejście→wynik zachowane
- Faktyczne: ids=['b7e3225441f3e-d001', 'b7e3225441f3e-d002'] unikalne=True; nazwy=['dup.pdf', 'dup.pdf']; wyniki=['partial', 'partial']
- Proponowana poprawka: Zachować oryginalną nazwę w metadanych (UTF-8) obok ID; porównywać wielkość liter przy raportowaniu duplikatów.
- Test do przeniesienia do produktu: `test_same_basename_two_documents_get_distinct_ids_and_results`

**N15 — duplikat/wielkość liter: sub1/same.pdf + sub2/same.pdf** (luka: nie)

- Oczekiwane: dwa osobne dokumenty, brak nadpisania, mapowanie wejście→wynik zachowane
- Faktyczne: ids=['b4e9712585ff7-d001', 'b4e9712585ff7-d002'] unikalne=True; nazwy=['same.pdf', 'same.pdf']; wyniki=['partial', 'partial']
- Proponowana poprawka: Zachować oryginalną nazwę w metadanych (UTF-8) obok ID; porównywać wielkość liter przy raportowaniu duplikatów.
- Test do przeniesienia do produktu: `test_same_basename_two_documents_get_distinct_ids_and_results`

**N16 — przerwany upload (zamknięcie połączenia w połowie ciała)** (luka: nie)

- Oczekiwane: brak częściowego dokumentu przetwarzanego jako wynik
- Faktyczne: pliki input* po przerwaniu: []; /health=200
- Proponowana poprawka: Wsad zapisywać w katalogu tymczasowym i przenosić atomowo po pełnym przyjęciu; sprzątać `.part` przy starcie.
- Test do przeniesienia do produktu: `test_aborted_upload_leaves_no_batch_or_part_files`

**P01 — traversal w /documents/{id}/artifact/{name:path} (8 kodowań)** (luka: częściowo)

- Oczekiwane: 404, brak odczytu plików spoza katalogu przebiegu
- Faktyczne: statusy=[404, 404, 404, 404, 404, 404, 500, 'błąd:ReadError']; wycieki=0; nieobsłużony wyjątek (500/zerwane połączenie) dla 2 z 8 ładunków
- Proponowana poprawka: Trasa surowych artefaktów nie powinna istnieć w produkcie; jeśli tak, lista dozwolonych nazw zamiast ścieżki.
- Test do przeniesienia do produktu: `test_artifact_route_rejects_traversal_encodings`

**P02 — symlink w katalogu przebiegu: do pliku-kanarka poza workspace, do cudzego dokumentu, do katalogu** (luka: nie)

- Oczekiwane: żaden nie jest odczytany
- Faktyczne: plik poza: HTTP 404 wyciek=False; cudzy dokument: HTTP 404 wyciek=False; katalog: HTTP 404 wyciek=False
- Proponowana poprawka: resolve() + sprawdzenie prefiksu (jest) oraz odmowa gdy któryś element ścieżki jest symlinkiem (lstat) lub open z O_NOFOLLOW.
- Test do przeniesienia do produktu: `test_symlink_inside_run_dir_is_not_followed`

**P03 — identyfikatory jako ścieżka i dostęp do cudzego wsadu** (luka: częściowo)

- Oczekiwane: ID = nieprzewidywalny losowy token; brak traktowania ID jako ścieżki
- Faktyczne: ID-ścieżki → [404, 405, 200, 307, 404, 404]; wynik cudzego wsadu bez tożsamości: HTTP 200; batch_id=b270f7e06d716 (12 hex = 48 bit entropii), document_id=batch_id+'-d00N' (sekwencyjny sufiks)
- Proponowana poprawka: MVP bez logowania: ID ≥128 bit (secrets.token_urlsafe(16)); zapis w ADR, że brak izolacji użytkowników jest świadomy; przy dodaniu użytkowników sprawdzać właściciela wsadu.
- Test do przeniesienia do produktu: `test_ids_have_128_bit_entropy_and_unknown_id_is_404`

**P04 — ujawnienie ścieżek hosta w /system i w błędach** (luka: tak)

- Oczekiwane: brak ścieżek hosta w odpowiedziach
- Faktyczne: ścieżka w odpowiedzi: {'/system': True, '404': False, '422': False}
- Proponowana poprawka: W /system podawać wersje i gotowość, bez `work_dir` i ścieżki pliku klucza.
- Test do przeniesienia do produktu: `test_system_and_errors_do_not_expose_host_paths`

**P05 — Host: evil.example, Origin obcy, formularz bez preflight** (luka: tak)

- Oczekiwane: odrzucenie żądania z obcym Host/Origin; brak wsadu z formularza obcej strony
- Faktyczne: Host evil → HTTP 200; POST multipart z obcym Origin → HTTP 201 (wsad utworzony); OPTIONS → 405; ACAO=None
- Proponowana poprawka: Middleware: dopuszczać tylko Host ∈ {127.0.0.1:PORT, localhost:PORT}; odrzucać Origin spoza listy; wymagać nagłówka niestandardowego (np. X-Requested-With) lub tokenu sesji dla POST.
- Test do przeniesienia do produktu: `test_post_with_foreign_origin_or_host_is_rejected`

**P06 — HTML/JS w nazwie pliku i treści PDF: czy wraca nieescapowane w JSON i jaki Content-Type** (luka: częściowo)

- Oczekiwane: Content-Type: application/json + nosniff; nazwa oczyszczona; ucieczka w GUI
- Faktyczne: nazwa zapisana='_img src_x onerror_alert_1__.pdf'; treść z <script> w odpowiedzi surowa=True; content-type=application/json; nosniff=None
- Proponowana poprawka: Dodać `X-Content-Type-Options: nosniff` i `Content-Security-Policy: default-src 'none'` do odpowiedzi API; GUI renderuje tekst dokumentu wyłącznie jako tekst (textContent), nie innerHTML; test w GUI.
- Test do przeniesienia do produktu: `test_api_responses_have_nosniff_and_json_content_type; GUI: test_document_text_rendered_as_text_not_html`

**R01 — wzorce normalizatorów produkcyjnych (apps) i regułowe uprzęży na ciągach do 50 000 znaków (10 rodzin wejść × 3 rozmiary)** (luka: nie)

- Oczekiwane: czas ≤ ~1 s dla 50 000 znaków; brak wzrostu wykładniczego i kwadratowego rzutującego na limit czasu
- Faktyczne: najgorszy czas 0.15 s (date_like, n=50000, funkcja date); dokument HTTP z długimi liniami: outcome=complete w 0.74 s; kontrola={'health': 200, 'clean_doc': 'partial', 'alive': True}
- Proponowana poprawka: Ograniczyć długość kandydata przed regex (np. ≤200 znaków dla NIP/rachunku/kwoty), użyć regex z limitem czasu (`regex` z timeout) lub wzorców bez zagnieżdżonych kwantyfikatorów; test z wejściem 50 000 znaków.
- Test do przeniesienia do produktu: `test_normalizers_linear_time_on_50k_char_inputs (limit 1 s)`

**S01 — PDF z akcjami URI/GoToR/Launch/JS/XFA(XXE)/F+FFilter/EmbeddedFile + file:// — wariant: tekst** (luka: nie)

- Oczekiwane: zero połączeń do nasłuchu, zero treści z file:// w wyniku, zero wykonania akcji
- Faktyczne: outcome=ambiguous kody=['class_ambiguous']; połączenia do nasłuchu 127.0.0.1: 0 []; treść kanarka z file:// w artefaktach: False
- Proponowana poprawka: Zachować pdfium bez V8/XFA i bez FORM ENV (stan obecny); w produkcie dodać test z nasłuchem i uruchamiać parser w procesie bez dostępu do sieci (np. `unshare -n`) — obrona w głąb.
- Test do przeniesienia do produktu: `test_pdf_with_external_actions_makes_no_network_requests (nasłuch loopback)`

**S02 — PDF z akcjami URI/GoToR/Launch/JS/XFA(XXE)/F+FFilter/EmbeddedFile + file:// — wariant: skan (render)** (luka: nie)

- Oczekiwane: zero połączeń do nasłuchu, zero treści z file:// w wyniku, zero wykonania akcji
- Faktyczne: outcome=technical_error kody=['ocr_unavailable']; połączenia do nasłuchu 127.0.0.1: 0 []; treść kanarka z file:// w artefaktach: False
- Proponowana poprawka: Zachować pdfium bez V8/XFA i bez FORM ENV (stan obecny); w produkcie dodać test z nasłuchem i uruchamiać parser w procesie bez dostępu do sieci (np. `unshare -n`) — obrona w głąb.
- Test do przeniesienia do produktu: `test_pdf_with_external_actions_makes_no_network_requests (nasłuch loopback)`

**T01 — plik 0 bajtów** (luka: nie)

- Oczekiwane: kod: not_a_pdf|empty_document
- Faktyczne: outcome=technical_error kody=['not_a_pdf']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T01]`

**T02 — sam nagłówek %PDF-1.7** (luka: nie)

- Oczekiwane: kod: pdf_corrupted
- Faktyczne: outcome=technical_error kody=['pdf_corrupted']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T02]`

**T03 — PNG z Content-Type application/pdf i nazwą .pdf** (luka: nie)

- Oczekiwane: kod: not_a_pdf
- Faktyczne: outcome=technical_error kody=['not_a_pdf']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T03]`

**T04 — nagłówek HTML + treść** (luka: nie)

- Oczekiwane: kod: not_a_pdf
- Faktyczne: outcome=technical_error kody=['not_a_pdf']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T04]`

**T05 — %PDF po 1 MB śmieci (poza oknem 1024 B)** (luka: nie)

- Oczekiwane: kod: not_a_pdf
- Faktyczne: outcome=technical_error kody=['not_a_pdf']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T05]`

**T06 — poliglot PDF + ZIP doklejony na końcu** (luka: nie)

- Oczekiwane: kod: complete|partial
- Faktyczne: outcome=partial kody=['evidence_unanchored']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T06]`

**T07 — śmieci przed %PDF w oknie 1024 B** (luka: nie)

- Oczekiwane: kod: complete|partial
- Faktyczne: outcome=partial kody=['evidence_unanchored']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T07]`

**T08 — obcięty PDF (połowa bajtów)** (luka: nie)

- Oczekiwane: kod: pdf_corrupted
- Faktyczne: outcome=technical_error kody=['pdf_corrupted']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T08]`

**T09 — PDF z 0 stron (Count 0)** (luka: nie)

- Oczekiwane: kod: empty_document
- Faktyczne: outcome=technical_error kody=['pdf_corrupted']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T09]`

**T10 — dobry PDF z rozszerzeniem .exe i MIME text/plain** (luka: nie)

- Oczekiwane: kod: complete|partial
- Faktyczne: outcome=partial kody=['evidence_unanchored']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T10]`

**T11 — zaszyfrowany PDF (słownik /Encrypt, hasło użytkownika)** (luka: nie)

- Oczekiwane: kod: pdf_encrypted
- Faktyczne: outcome=technical_error kody=['pdf_encrypted']
- Proponowana poprawka: Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.
- Test do przeniesienia do produktu: `test_input_type_matrix[T11]`

## Wniosek decyzyjny wobec kryterium z planu

Kryterium *„zawsze jawny `technical_error`, serwer żyje”* jest **niespełnione dla uprzęży**: 1 z 11 bomb PDF (B08, samoodwołujący się XObject) zabija proces serwera i cały wsad, dwie kolejne (B02: 5,2 GB; B03: 4,6 GB przy limicie 6 GB) przeżywają tylko dzięki rozmiarowi ładunku. Pozostałe wejścia (nazwy, typ, uszkodzone, zaszyfrowane, 0 stron, cykliczne, 50 000 stron) kończą się kodem i serwer żyje.

Decyzje przenoszone do produktu (od najważniejszej):

1. **Izolacja parsowania w procesie potomnym** z limitem pamięci (`RLIMIT_AS` lub cgroup) i twardym czasem z `kill` (B02, B03, B08). To jedyna obrona przed bombą, której nie przewidziano limitem; limity bajtów po dekompresji i pikseli to uzupełnienie.
2. **Limit ciała żądania na wejściu** (przerwanie po przekroczeniu, `Content-Length` > limit → 413) zamiast czytania do końca (F01).
3. **Walidacja Host/Origin** i nagłówek niestandardowy dla POST (P05; formularz z obcej strony tworzy wsad).
4. **Obsługa NUL i innych wyjątków** w trasach bez globalnego handlera 500 z kodem API (P01), nazwy plików odrzucane jawnie (N01–N11), `/system` bez ścieżek hosta (P04).

**Pewność:** wysoka dla wyników jakościowych (powtarzalne, deterministyczne PDF-y); średnia dla wielkości pamięci (zależne od wersji pdfium). **Otwarte:** mechanizm B08 w pdfium; zachowanie przy limicie 14 GB (przewidywane: to samo, wolniej); JBIG2/JPX; DNS-owy monitor SSRF; testy uruchomione na produktowym backendzie, gdy powstanie.
