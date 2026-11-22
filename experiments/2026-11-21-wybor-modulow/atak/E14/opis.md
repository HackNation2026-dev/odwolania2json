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
