# E14: awarie LLM i OCR, wyciek klucza-kanarka, SSRF przez konfigurację, budżet LLM, cache

> **Zakres.** Wynik opisuje **uprząż** (`harness/server.py`, `harness/llm.py`), nie produkt. Cały eksperyment działa na atrapie HTTP (`lib.MockServer`, prawdziwy serwer w wątku) i **fikcyjnym kluczu-kanarku** (`CANARY-KEY-…` w pliku tymczasowym): zero płatnych wywołań, prawdziwy klucz MiniMax nie jest tu użyty.
> **Czas.** Czasy (backoff, timeouty) zmierzono pod obciążeniem maszyny (load avg ok. 27–35 na 8 rdzeniach); są **niewiążące**. Wiążące: kody błędów, liczba wywołań LLM, wyciek tak/nie.

## Hipoteza i kryterium (plan E14)

Awarie LLM i OCR dają jawne kody błędów zgodne z architekturą §6 i §9.1, bez zmyślonych danych i bez podmiany starym wynikiem z cache; klucz nie występuje w żadnej odpowiedzi, logu ani artefakcie. Kryterium: *zgodność z architekturą §6 i §9.1*.

## Metoda

Skrypt: `.venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/E14/e14.py` (`--only matrix,net,ssrf,budget,cache,doclog`). Wynik: `wyniki.json`. Dla każdego przypadku: nowy serwer uprzęży z ekstraktorem LLM wskazującym na atrapę, wgranie przelewu z danych rozwojowych, odczyt stanu i artefaktów, potem **przeszukanie kanarka** w: odpowiedziach HTTP (stan, `/result`, `/report`, `/evidence`, `/metrics`, `/system`, `/openapi.json`, `/docs`, błędy 404 i 422, artefakty `raw/reading.json` i `t3/ai-response.json`), w logu serwera i w całym katalogu roboczym.

Atrapa w trybach: 401, 403, 429 (z `Retry-After: 3600`), 500, 400 z echem nagłówków autoryzacji, brak odpowiedzi (timeout), urwany JSON, HTML zamiast JSON, pusta odpowiedź, brak `content`, tablica zamiast obiektu, `fields` nie-lista, element bez `value`, przekierowanie 302. We wszystkich błędach treść i nagłówki odpowiedzi atrapy **zawierają kanarka** (także jako `x-echo-key`, echo `Authorization` i `x-api-key`). Osobno: brak sieci (zamknięty port), błąd TLS (https do serwera HTTP), DNS (`.invalid`), `169.254.169.254`, `file://`, `gopher://` jako `base_url` z konfiguracji.

## Jak to działa i dlaczego tak wyszło

- **Mapowanie błędów jest odporne na wyciek**: `LlmClient.complete` zamienia każdą awarię na `HarnessError` z kodem i opisem w rodzaju `HTTP 401`, bez treści odpowiedzi; `redact_msg` dodatkowo maskuje klucz. Dlatego kanarek, choć atrapa wstawiała go do treści i nagłówków, nie trafił do żadnej odpowiedzi HTTP, logu ani pliku (0 trafień we wszystkich 14 + 6 przypadkach).
- **Kody zgodne z §6/§9.1**: 401/403 → `llm_authorization` bez ponowień (1 wywołanie), 429/5xx/timeout → ponowienia ograniczone `retries` (3 wywołania przy `retries=2`), reszta → `llm_invalid_response`. Po awarii `GET /result` zwraca 409 (eksport zablokowany): żadnych zmyślonych danych.
- **`Retry-After` jest ignorowany** (stały backoff 1 s, 2 s): to nie wisi godzinę (zaleta), ale też nie respektuje dostawcy.
- **Klucz idzie do dowolnego hosta z konfiguracji i w dwóch nagłówkach** (`x-api-key` i `Authorization: Bearer`, także po jawnym HTTP): atrapa pod `http://127.0.0.1` dostała kanarka w obu (C02). Przekierowania 302 nie są śledzone (domyślne `follow_redirects=False` w httpx), więc klucz nie trafia do drugiego hosta (C03).
- **Parametry od klienta nie zmieniają endpointu**: pola formularza, zapytanie i nagłówki (`llm_base_url`, `endpoint`, `model`, `input_path`, `key_file`, `X-LLM-Endpoint`) zostały przyjęte bez błędu i zignorowane; obcy host nie dostał żadnego połączenia (C01). Jedyna droga do SSRF to konfiguracja startowa (`base_url`): `169.254.169.254`, `file://` i `gopher://` dają `llm_unavailable`, a serwer żyje.
- **Brak limitów budżetu**: przy trwałym 500 wsad 20 dokumentów wykonał 60 wywołań (20 × 3), bez wyłącznika serii błędów (L02); dokument 60 stron × ~16 tys. znaków poszedł do LLM jako jedno żądanie ~0,98 MB (≈244 tys. tokenów szac.), bo nie ma kontroli `context_limit` (L03).
- **Cache nie istnieje**: ten sam PDF pod inną nazwą jest przeliczany (kolejne wywołanie LLM), a awaria przy trzecim wgraniu daje `technical_error` bez starego wyniku (K01). To zgodne z ADR-002 pkt 12 *trywialnie*: brak cache nie dowodzi, że przyszły cache będzie odporny.
- **Treść dokumentu** (kanarek `PESEL-CANARY-…` w tekście PDF) jest na dysku wyłącznie w `input.pdf` i `raw/reading.json` (artefakty danych), a w logu serwera, odpowiedziach błędów (w tym 422) i trasach stanu/raportu jej nie ma (D01–D04).
- **OCR:** awarie OCR sprowadzają się w uprzęży do `ocr_unavailable` (OCR wyłączony: dowody w E12 B04, B05, S02, gdzie skan kończy się tym kodem po renderze) i `ocr_error` (wyjątek silnika). Wstrzyknięcie awarii **rzeczywistego silnika rapidocr przez HTTP** nie zostało wykonane (wymaga ingerencji w proces serwera); pokrywają je testy jednostkowe uprzęży, ale nie ten eksperyment.

## Ograniczenia

Atrapa to nie MiniMax: nie odtwarza strumieniowania, kodów 529/overloaded ani błędów TLS ze strony prawdziwego dostawcy. Test wycieku sprawdza ciągi dokładne (kanarek), nie zaszyfrowane ani przekształcone formy klucza. Wsad 20 dokumentów to próbka mała; liczba wywołań jest deterministyczna (3 na dokument), więc skaluje się liniowo. Liczby czasu niewiążące (patrz wyżej).

## Wyniki wektorów

### Zestawienie wektorów

Wektorów: 31; luka: częściowo 1, nie 27, tak 3.

| ID | Rodzina | Wektor | Luka |
|---|---|---|---|
| A01 | awaria-LLM | 401 z kanarkiem w treści i nagłówku | **nie** |
| A02 | awaria-LLM | 403 z kanarkiem | **nie** |
| A03 | awaria-LLM | 429 z Retry-After: 3600 i kanarkiem | **nie** |
| A04 | awaria-LLM | 500 z kanarkiem w treści | **nie** |
| A05 | awaria-LLM | 400 z echem nagłówków autoryzacji w treści | **nie** |
| A06 | awaria-LLM | timeout (serwer milczy 8 s, limit 2 s, 1 ponowienie) | **nie** |
| A07 | awaria-LLM | urwany JSON (stop_reason max_tokens) | **nie** |
| A08 | awaria-LLM | ciało nie-JSON (HTML z kanarkiem) | **nie** |
| A09 | awaria-LLM | pusta odpowiedź modelu | **nie** |
| A10 | awaria-LLM | odpowiedź bez pola content | **nie** |
| A11 | awaria-LLM | JSON będący tablicą | **nie** |
| A12 | awaria-LLM | pole fields nie jest listą | **nie** |
| A13 | awaria-LLM | element fields[] bez value | **nie** |
| A14 | awaria-LLM | przekierowanie 302 do innego hosta | **nie** |
| C01 | SSRF-konfiguracja | URL/endpoint/model/ścieżka podane przez klienta HTTP (pola formularza, zapytanie, nagłówki) | **częściowo** |
| C02 | wyciek-klucza | klucz LLM wysyłany do endpointu z konfiguracji bez walidacji hosta (obcy host bez TLS) | **tak** |
| C03 | wyciek-klucza | odpowiedź 302 z endpointu LLM wskazująca na inny host | **nie** |
| D01 | treść-dokumentu-w-logach | błąd LLM `500`: czy treść dokumentu (PESEL-kanarek) trafia do logu serwera, odpowiedzi błędu 422 lub artefaktów | **nie** |
| D02 | treść-dokumentu-w-logach | błąd LLM `truncated`: czy treść dokumentu (PESEL-kanarek) trafia do logu serwera, odpowiedzi błędu 422 lub artefaktów | **nie** |
| D03 | treść-dokumentu-w-logach | błąd LLM `garbage`: czy treść dokumentu (PESEL-kanarek) trafia do logu serwera, odpowiedzi błędu 422 lub artefaktów | **nie** |
| D04 | treść-dokumentu-w-logach | błąd LLM `401`: czy treść dokumentu (PESEL-kanarek) trafia do logu serwera, odpowiedzi błędu 422 lub artefaktów | **nie** |
| K01 | cache | ten sam SHA-256, awaria API przy drugim wgraniu: czy wraca stary wynik (ADR-002 pkt 12) | **nie** |
| L01 | budżet-LLM | 429 z Retry-After: 3600 | **nie** |
| L02 | budżet-LLM | wsad 20 dokumentów przy trwałym błędzie 500 dostawcy | **tak** |
| L03 | budżet-LLM | dokument 60 stron gęstego tekstu (≈16 tys. znaków na stronę) (limit stron uprzęży 60): rozmiar jednego żądania do LLM | **tak** |
| N01 | awaria-sieci/SSRF-konfiguracja | brak sieci: połączenie odrzucone (zamknięty port) | **nie** |
| N02 | awaria-sieci/SSRF-konfiguracja | błąd TLS: https do serwera HTTP | **nie** |
| N03 | awaria-sieci/SSRF-konfiguracja | DNS: nieistniejąca domena (.invalid) | **nie** |
| N04 | awaria-sieci/SSRF-konfiguracja | SSRF przez konfigurację: adres metadanych 169.254.169.254 | **nie** |
| N05 | awaria-sieci/SSRF-konfiguracja | schemat file:// | **nie** |
| N06 | awaria-sieci/SSRF-konfiguracja | schemat gopher:// | **nie** |

### Szczegóły: oczekiwane, faktyczne, poprawka, test do produktu

**A01 — 401 z kanarkiem w treści i nagłówku** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_authorization, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_authorization (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.2 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['HTTP 401']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a01_maps_to_code_and_leaks_nothing`

**A02 — 403 z kanarkiem** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_authorization, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_authorization (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.2 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['HTTP 403']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a02_maps_to_code_and_leaks_nothing`

**A03 — 429 z Retry-After: 3600 i kanarkiem** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_rate_limit, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_rate_limit (zgodny=True); GET /result → 409; wywołań LLM=3; czas 3.2 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['HTTP 429']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a03_maps_to_code_and_leaks_nothing`

**A04 — 500 z kanarkiem w treści** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_unavailable, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_unavailable (zgodny=True); GET /result → 409; wywołań LLM=3; czas 3.3 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['HTTP 500']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a04_maps_to_code_and_leaks_nothing`

**A05 — 400 z echem nagłówków autoryzacji w treści** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_invalid_response, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_invalid_response (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.1 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['HTTP 400']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a05_maps_to_code_and_leaks_nothing`

**A06 — timeout (serwer milczy 8 s, limit 2 s, 1 ponowienie)** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_unavailable, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_unavailable (zgodny=True); GET /result → 409; wywołań LLM=2; czas 5.3 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['przekroczono limit czasu połączenia z LLM']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a06_maps_to_code_and_leaks_nothing`

**A07 — urwany JSON (stop_reason max_tokens)** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_invalid_response, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_invalid_response (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.2 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['odpowiedź bez obiektu JSON']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a07_maps_to_code_and_leaks_nothing`

**A08 — ciało nie-JSON (HTML z kanarkiem)** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_invalid_response, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_invalid_response (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.2 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['ciało odpowiedzi nie jest obiektem JSON']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a08_maps_to_code_and_leaks_nothing`

**A09 — pusta odpowiedź modelu** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_invalid_response, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_invalid_response (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.1 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['pusta odpowiedź modelu']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a09_maps_to_code_and_leaks_nothing`

**A10 — odpowiedź bez pola content** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_invalid_response, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_invalid_response (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.2 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['brak pola content w odpowiedzi']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a10_maps_to_code_and_leaks_nothing`

**A11 — JSON będący tablicą** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_invalid_response, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_invalid_response (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.2 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['brak listy fields w odpowiedzi LLM']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a11_maps_to_code_and_leaks_nothing`

**A12 — pole fields nie jest listą** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_invalid_response, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_invalid_response (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.3 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['brak listy fields w odpowiedzi LLM']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a12_maps_to_code_and_leaks_nothing`

**A13 — element fields[] bez value** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_invalid_response, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_invalid_response (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.1 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['pole fields[] poza schematem']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a13_maps_to_code_and_leaks_nothing`

**A14 — przekierowanie 302 do innego hosta** (luka: nie)

- Oczekiwane: outcome technical_error, kod llm_invalid_response, brak wyniku (GET /result 409), kanarek nieobecny w HTTP/logach/dysku, bez zmyślonych danych
- Faktyczne: outcome=technical_error kod=llm_invalid_response (zgodny=True); GET /result → 409; wywołań LLM=1; czas 0.3 s; kanarek w odpowiedziach HTTP/logu/dysku: -/-/-; opis błędu: ['ciało odpowiedzi nie jest obiektem JSON']
- Proponowana poprawka: Mapować błąd dostawcy tylko na kod i status HTTP (jak teraz), nigdy nie kopiować treści odpowiedzi; Retry-After uwzględniać z górnym limitem (np. 30 s); test kanarka dla każdej klasy błędu.
- Test do przeniesienia do produktu: `test_llm_failure_a14_maps_to_code_and_leaks_nothing`

**C01 — URL/endpoint/model/ścieżka podane przez klienta HTTP (pola formularza, zapytanie, nagłówki)** (luka: częściowo)

- Oczekiwane: parametry ignorowane lub odrzucone; zero połączeń do obcego hosta
- Faktyczne: HTTP 201; outcome=partial; połączenia do obcego hosta: 0; LLM użył skonfigurowanego endpointu: 1 żądań; pola nadmiarowe przyjęte bez błędu (brak jawnej odmowy)
- Proponowana poprawka: Odrzucać nieznane pola formularza kodem 422 `unknown_field`; endpoint/model/klucz wyłącznie z konfiguracji uruchomienia.
- Test do przeniesienia do produktu: `test_client_supplied_endpoint_fields_are_rejected_or_ignored_and_no_outbound_call`

**C02 — klucz LLM wysyłany do endpointu z konfiguracji bez walidacji hosta (obcy host bez TLS)** (luka: tak)

- Oczekiwane: klucz wysyłany tylko do zaufanego hosta po TLS
- Faktyczne: atrapa pod http://127.0.0.1 otrzymała nagłówki autoryzacji z kanarkiem: Authorization=True, x-api-key=True (klucz wysyłany podwójnie, w obu nagłówkach, w jawnym HTTP)
- Proponowana poprawka: Allowlista hosta i wymuszenie https; jeden nagłówek zależnie od protokołu (Anthropic: x-api-key; OpenAI: Authorization), nie oba.
- Test do przeniesienia do produktu: `test_api_key_only_sent_to_allowlisted_https_host_in_single_header`

**C03 — odpowiedź 302 z endpointu LLM wskazująca na inny host** (luka: nie)

- Oczekiwane: przekierowanie nie jest śledzone; klucz nie trafia do drugiego hosta
- Faktyczne: outcome=technical_error kod=llm_invalid_response; żądań do drugiego hosta: 0; klucz u drugiego hosta: False
- Proponowana poprawka: Utrzymać `follow_redirects=False` (domyślne w httpx) i dodać test regresji.
- Test do przeniesienia do produktu: `test_llm_client_does_not_follow_redirects`

**D01 — błąd LLM `500`: czy treść dokumentu (PESEL-kanarek) trafia do logu serwera, odpowiedzi błędu 422 lub artefaktów** (luka: nie)

- Oczekiwane: w logach i błędach brak treści dokumentu; artefakt `reading.json` i `ai-response.json` zawierają ją z konieczności (dane, nie diagnostyka)
- Faktyczne: log serwera: czysto; odpowiedzi HTTP bez tras artefaktów danych (stan, /report, /metrics, /system, błędy 404/422): czysto; 422 zawiera treść: False; na dysku w: ['input.pdf', 'reading.json']
- Proponowana poprawka: Rozróżnić artefakty danych (dozwolone, w katalogu roboczym) od logów/błędów (zakaz treści); test kanarka w CI na logach.
- Test do przeniesienia do produktu: `test_document_content_never_appears_in_logs_or_error_bodies`

**D02 — błąd LLM `truncated`: czy treść dokumentu (PESEL-kanarek) trafia do logu serwera, odpowiedzi błędu 422 lub artefaktów** (luka: nie)

- Oczekiwane: w logach i błędach brak treści dokumentu; artefakt `reading.json` i `ai-response.json` zawierają ją z konieczności (dane, nie diagnostyka)
- Faktyczne: log serwera: czysto; odpowiedzi HTTP bez tras artefaktów danych (stan, /report, /metrics, /system, błędy 404/422): czysto; 422 zawiera treść: False; na dysku w: ['input.pdf', 'reading.json']
- Proponowana poprawka: Rozróżnić artefakty danych (dozwolone, w katalogu roboczym) od logów/błędów (zakaz treści); test kanarka w CI na logach.
- Test do przeniesienia do produktu: `test_document_content_never_appears_in_logs_or_error_bodies`

**D03 — błąd LLM `garbage`: czy treść dokumentu (PESEL-kanarek) trafia do logu serwera, odpowiedzi błędu 422 lub artefaktów** (luka: nie)

- Oczekiwane: w logach i błędach brak treści dokumentu; artefakt `reading.json` i `ai-response.json` zawierają ją z konieczności (dane, nie diagnostyka)
- Faktyczne: log serwera: czysto; odpowiedzi HTTP bez tras artefaktów danych (stan, /report, /metrics, /system, błędy 404/422): czysto; 422 zawiera treść: False; na dysku w: ['input.pdf', 'reading.json']
- Proponowana poprawka: Rozróżnić artefakty danych (dozwolone, w katalogu roboczym) od logów/błędów (zakaz treści); test kanarka w CI na logach.
- Test do przeniesienia do produktu: `test_document_content_never_appears_in_logs_or_error_bodies`

**D04 — błąd LLM `401`: czy treść dokumentu (PESEL-kanarek) trafia do logu serwera, odpowiedzi błędu 422 lub artefaktów** (luka: nie)

- Oczekiwane: w logach i błędach brak treści dokumentu; artefakt `reading.json` i `ai-response.json` zawierają ją z konieczności (dane, nie diagnostyka)
- Faktyczne: log serwera: czysto; odpowiedzi HTTP bez tras artefaktów danych (stan, /report, /metrics, /system, błędy 404/422): czysto; 422 zawiera treść: False; na dysku w: ['input.pdf', 'reading.json']
- Proponowana poprawka: Rozróżnić artefakty danych (dozwolone, w katalogu roboczym) od logów/błędów (zakaz treści); test kanarka w CI na logach.
- Test do przeniesienia do produktu: `test_document_content_never_appears_in_logs_or_error_bodies`

**K01 — ten sam SHA-256, awaria API przy drugim wgraniu: czy wraca stary wynik (ADR-002 pkt 12)** (luka: nie)

- Oczekiwane: technical_error bez podmiany starym wynikiem z cache
- Faktyczne: 1. wgranie: partial (1 wywołanie LLM); to samo pod inną nazwą: przeliczone ponownie (+1 wywołanie ⇒ brak cache po SHA); 3. wgranie przy 500: outcome=technical_error, GET /result → 409; stary wynik podmieniony: False
- Proponowana poprawka: Przy dodaniu cache klucz = SHA-256 + wersja promptu + model + konfiguracja OCR; test z awarią API po trafieniu w cache; cache nigdy nie maskuje bieżącego błędu.
- Test do przeniesienia do produktu: `test_provider_failure_after_cached_success_returns_technical_error_not_stale_result`

**L01 — 429 z Retry-After: 3600** (luka: nie)

- Oczekiwane: brak godzinnego wiszenia; ograniczona liczba prób; po limicie technical_error
- Faktyczne: czas 3.1 s; żądań do LLM=3 (retries=2 ⇒ max 3); outcome=technical_error kod=llm_rate_limit; nagłówek Retry-After ignorowany (stały backoff 1 s, 2 s)
- Proponowana poprawka: Opcjonalnie respektować Retry-After do górnego limitu (np. 30 s) i przerywać wsad po serii 429 (circuit breaker).
- Test do przeniesienia do produktu: `test_retry_after_is_capped_and_attempts_are_bounded`

**L02 — wsad 20 dokumentów przy trwałym błędzie 500 dostawcy** (luka: tak)

- Oczekiwane: twardy limit wywołań na wsad / wyłącznik po serii błędów; brak setek bezcelowych wywołań
- Faktyczne: czas 15.7 s; wywołań LLM=60 (= 20 × 3 prób; bez wyłącznika serii błędów); wszystkie dokumenty technical_error=20
- Proponowana poprawka: Licznik wywołań i tokenów na wsad (twardy limit z konfiguracji) oraz circuit breaker po K kolejnych błędach dostawcy ⇒ reszta wsadu `technical_error` bez wywołań.
- Test do przeniesienia do produktu: `test_batch_stops_calling_llm_after_consecutive_provider_failures`

**L03 — dokument 60 stron gęstego tekstu (≈16 tys. znaków na stronę) (limit stron uprzęży 60): rozmiar jednego żądania do LLM** (luka: tak)

- Oczekiwane: limit kontekstu/tokenów na dokument (kod `context_limit`) przed wysłaniem
- Faktyczne: outcome=complete kod=None; wywołań=1; rozmiar żądania do LLM=0.98 MB (≈244 166 tokenów szac.) bez sprawdzenia limitu kontekstu
- Proponowana poprawka: Przed wywołaniem szacować tokeny i odrzucać/dzielić powyżej limitu (kod `context_limit`, architektura §6); osobny limit tokenów na dokument i wsad.
- Test do przeniesienia do produktu: `test_oversized_document_text_yields_context_limit_without_llm_call`

**N01 — brak sieci: połączenie odrzucone (zamknięty port)** (luka: nie)

- Oczekiwane: technical_error llm_unavailable; serwer żyje; brak klucza w odpowiedziach
- Faktyczne: outcome=technical_error kod=llm_unavailable; czas 0.3 s; serwer żyje=True; wyciek kanarka=False
- Proponowana poprawka: Walidować `base_url` przy starcie: schemat https (http tylko dla loopback w trybie deweloperskim), allowlista hostów (api.minimax.io) i odrzucenie adresów link-local/prywatnych poza loopback; test z mock.
- Test do przeniesienia do produktu: `test_llm_base_url_validation_n01`

**N02 — błąd TLS: https do serwera HTTP** (luka: nie)

- Oczekiwane: technical_error llm_unavailable; serwer żyje; brak klucza w odpowiedziach
- Faktyczne: outcome=technical_error kod=llm_unavailable; czas 0.2 s; serwer żyje=True; wyciek kanarka=False
- Proponowana poprawka: Walidować `base_url` przy starcie: schemat https (http tylko dla loopback w trybie deweloperskim), allowlista hostów (api.minimax.io) i odrzucenie adresów link-local/prywatnych poza loopback; test z mock.
- Test do przeniesienia do produktu: `test_llm_base_url_validation_n02`

**N03 — DNS: nieistniejąca domena (.invalid)** (luka: nie)

- Oczekiwane: technical_error llm_unavailable; serwer żyje; brak klucza w odpowiedziach
- Faktyczne: outcome=technical_error kod=llm_unavailable; czas 0.2 s; serwer żyje=True; wyciek kanarka=False
- Proponowana poprawka: Walidować `base_url` przy starcie: schemat https (http tylko dla loopback w trybie deweloperskim), allowlista hostów (api.minimax.io) i odrzucenie adresów link-local/prywatnych poza loopback; test z mock.
- Test do przeniesienia do produktu: `test_llm_base_url_validation_n03`

**N04 — SSRF przez konfigurację: adres metadanych 169.254.169.254** (luka: nie)

- Oczekiwane: technical_error llm_unavailable; serwer żyje; brak klucza w odpowiedziach
- Faktyczne: outcome=technical_error kod=llm_unavailable; czas 3.1 s; serwer żyje=True; wyciek kanarka=False
- Proponowana poprawka: Walidować `base_url` przy starcie: schemat https (http tylko dla loopback w trybie deweloperskim), allowlista hostów (api.minimax.io) i odrzucenie adresów link-local/prywatnych poza loopback; test z mock.
- Test do przeniesienia do produktu: `test_llm_base_url_validation_n04`

**N05 — schemat file://** (luka: nie)

- Oczekiwane: technical_error llm_unavailable; serwer żyje; brak klucza w odpowiedziach
- Faktyczne: outcome=technical_error kod=llm_unavailable; czas 0.2 s; serwer żyje=True; wyciek kanarka=False
- Proponowana poprawka: Walidować `base_url` przy starcie: schemat https (http tylko dla loopback w trybie deweloperskim), allowlista hostów (api.minimax.io) i odrzucenie adresów link-local/prywatnych poza loopback; test z mock.
- Test do przeniesienia do produktu: `test_llm_base_url_validation_n05`

**N06 — schemat gopher://** (luka: nie)

- Oczekiwane: technical_error llm_unavailable; serwer żyje; brak klucza w odpowiedziach
- Faktyczne: outcome=technical_error kod=llm_unavailable; czas 0.1 s; serwer żyje=True; wyciek kanarka=False
- Proponowana poprawka: Walidować `base_url` przy starcie: schemat https (http tylko dla loopback w trybie deweloperskim), allowlista hostów (api.minimax.io) i odrzucenie adresów link-local/prywatnych poza loopback; test z mock.
- Test do przeniesienia do produktu: `test_llm_base_url_validation_n06`

## Wniosek decyzyjny wobec kryterium z planu

Kryterium *„zgodność z architekturą §6 i §9.1”* jest **spełnione** dla klas błędów LLM i sieci w uprzęży (14 przypadków atrapy + 6 sieciowych: kody zgodne, brak zmyślonych danych, brak wycieku kanarka, brak podmiany z cache), z trzema lukami do zamknięcia w produkcie:

1. **Walidacja `base_url` i wysyłka klucza** (C02): allowlista hosta, https, jeden nagłówek zależnie od protokołu.
2. **Budżet LLM** (L02, L03): limit wywołań i tokenów na dokument i wsad, wyłącznik po serii błędów, `context_limit` przed wysłaniem.
3. **Odrzucanie nieznanych pól** formularza z kodem (C01) zamiast cichego przyjęcia.

Test kanarka (każda klasa błędu → grep po odpowiedziach, logach, dysku) jest tani i powinien wejść do CI produktu jako stały. **Pewność:** wysoka dla wniosków o kodach i wycieku w uprzęży (deterministyczne, powtarzalne); niska dla zachowania prawdziwego dostawcy. **Otwarte:** awarie prawdziwego OCR przez HTTP; cache produktu (klucz z modelem i promptem); zachowanie przy `Retry-After` w produkcie. Dodatkowa luka znaleziona w E13 (M06): wartość tekstowa z samych cyfr w polu `kwota` daje `inf` → `GET /result` zwraca 500 (patrz E13).
