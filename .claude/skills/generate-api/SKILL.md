---
name: generate-api
description: Generowanie i zmiana API (OpenAPI 3.1 + FastAPI + modele pydantic) w repozytorium odwolania2json. Użyj przy dodawaniu lub zmianie endpointów, schematów, kodów błędów albo kontraktu v1.
---

# Generowanie API w odwolania2json

Kontrakt jest źródłem prawdy: najpierw `openapi.yaml`, potem modele, na końcu kod. Nigdy odwrotnie.

## Przed pracą

1. Przeczytaj [architekturę wewnętrzną](../../../docs/04-architektura/architektura-wewnetrzna.md) §4, §6, §9, §10 i [ADR-002](../../../docs/07-decyzje/ADR-002-decyzje-po-recenzji.md). Przy konflikcie dokumentów wygrywa nowszy: ADR-002 i architektura wewnętrzna 0.6.x przed `projekt-backend-fastapi-postgres-ui.md` 0.5.0.
2. Sprawdź [pytania otwarte](../../../docs/07-decyzje/pytania-otwarte.md). Nie zamykaj ich w kontrakcie.
3. Użyj skilla `api-designer` do modelowania zasobów; poniższe reguły repo mają pierwszeństwo.

## Pliki

| Plik | Rola |
|---|---|
| `packages/contracts/odwolania2json_contracts/openapi.yaml` | jedyny ręcznie pisany kontrakt |
| `packages/contracts/odwolania2json_contracts/models.py` | generowany; nie edytuj ręcznie |
| `scripts/generate_contracts.py` | generuje modele z kontraktu |
| `scripts/validate_api.py --stage spec\|app\|all` | walidacja specyfikacji i rozjazdu z FastAPI |
| `apps/backend/odwolania2json/` | silnik, CLI, API |

## Zakres v1 (architektura §1 pkt 5, §10)

Zasoby: `system` (`GET /system`, `GET /health`), `batches`, `jobs` (stan, jawne retry), `documents` (stan, PDF, obraz i tekst strony), podzasoby `diagnosis`, `result`, `evidence`, `report`, oraz odczyt `classes` i `codes`.

Poza v1: analiza regionów, korekty, użytkowe wersje wyników, zarządzanie rolami.
Bbox dowodów jest wymagany od v1. Wersje techniczne silnika i artefaktów od początku.

## Reguły kontraktu

- Nazwy, ścieżki, `operationId`, kody i stany po angielsku, `snake_case`. Wyjątek: klucze ocenianego JSON organizatora (polskie, niezmienne) i wskazujące je JSON Pointery.
- Ścieżki to rzeczowniki w liczbie mnogiej, bez czasowników.
- Oceniany wynik (`result`) to obiekt walidowany schematem klasy, bez metadanych technicznych. Dowody, diagnoza i raport to osobne zasoby.
- Stany: `progress` ∈ `queued|running|done`; `outcome` ∈ `complete|partial|foreign|ambiguous|technical_error|null`. `done` nie oznacza sukcesu.
- Brak danych to `null` z jawnym powodem w raporcie (`missing|not_applicable|unreadable|conflicting|unprocessed`), nie `""` i nie brak klucza.
- Jeden PDF = jeden dokument = najwyżej jeden oceniany JSON.
- Błędy: `application/problem+json` (RFC 7807). `type` to stabilny URI, a `code` to kod z mapowania w architekturze §6 (np. `llm_unavailable`, `ocr_unavailable`). Opisy bez kluczy API i bez treści dokumentu.
- `Bbox` = `[x0,y0,x1,y1]`, punkty PDF, początek w lewym górnym rogu, `x0<x1`, `y0<y1`.
- Kolekcje (`batches`, `jobs`, `documents`) mają paginację kursorową. Żądania asynchroniczne zwracają `202` i zasób stanu; odczyt stanu nigdy nie uruchamia pracy ani płatnego wywołania LLM.
- Odświeżenie lub GET nie tworzy nowego wywołania AI; retry to jawne `POST` tworzące nowy `run_id`.
- Sekrety (klucz API) nie występują w żadnej odpowiedzi ani w schemacie konfiguracji zwracanej klientowi.
- Wersjonowanie: prefiks `/v1`, zmiana łamiąca = nowa wersja z okresem wycofania. Pole `info.version` rośnie przy każdej zmianie kontraktu.

## Procedura

1. Zmodeluj zasoby i stany (tabela zasób → operacje → schemat) w opisie zmiany; bez kodu przed specyfikacją.
2. Edytuj `openapi.yaml`: operacje, schematy w `components`, odpowiedzi błędów w `components/responses`, przykłady.
3. `python scripts/generate_contracts.py`, potem `python scripts/validate_api.py --stage spec`.
4. Napisz test kontraktowy (nazwa po angielsku), zobacz czerwony, dopiero potem implementuj trasę FastAPI z modelami wygenerowanymi.
5. `python scripts/validate_api.py --stage all` oraz `python -m pytest`.
6. `python3 scripts/verify_docs.py`. Zaktualizuj `CHANGELOG.md` i, przy zmianie zasady, dodaj ADR z konsekwencjami.

## Czego nie robić

- Nie edytuj `models.py` ani materiałów organizatora w `docs/02-materialy/`.
- Nie dodawaj endpointu bez wpisu w `openapi.yaml`.
- Nie rozszerzaj zakresu v1 bez decyzji w ADR.
- Nie zwracaj wyniku z cache przy awarii API (ADR-002 pkt 12).
- Nie przechowuj kluczy i tokenów w Git.
