# Szkic Z01 (niedokończony, poza kodem produktu)

Pliki `pdf/reader.py` (czytnik pypdfium2 z geometrią i diagnozą strony) i `ocr/rapid.py` (adapter rapidocr za
protokołem dostawcy OCR) napisał przerwany worker Z01. **Nie mają testów** i `mypy --strict` zgłasza brak typów
dla `pypdfium2` (stuby lub `# type: ignore[import-untyped]` z komentarzem). Nie są częścią `apps/` i nie były
uruchamiane przez bramki jakości.

Jak przenieść do produktu (zadanie Z01 w [zadaniach dla agentów](../../../docs/00-organizacja/zadania-dla-agentow.md)):
skopiuj do `apps/backend/odwolania2json/pdf/` i `ocr/`, napisz testy najpierw (czerwone), dodaj brakujące typy,
podłącz do silnika `process` razem z klientem LLM (`llm/`) i serializerem (`serialize.py`), które są już w `main`.
