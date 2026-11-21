---
wersja: 0.3.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Konsultacja Fable — wynik

Status: wykonana 2026-11-21 (13:42–13:47), bezpośrednio przez CLI `claude --model fable` (Claude Code 2.1.330), bez Orca. Model odpowiedzi według metadanych CLI: `claude-fable-5-2`. CLI użył też wewnętrznie `claude-haiku-5-5` przy WebFetch/WebSearch; ten model nie jest autorem rekomendacji. Uprawnienia: odczyt plików oraz WebSearch/WebFetch. Bez poleceń powłoki, bez zapisu plików, bez sekretów. Odmów uprawnień: 0.

Zapis:

- [zlecenie](fable-2026-11-21/zlecenie.txt) z aktualnymi wymaganiami obu repo,
- [surowa odpowiedź](fable-2026-11-21/odpowiedz-surowa.txt), bez zmian,
- [metadane](fable-2026-11-21/metadane.json): model, czas, koszt, session_id.

Odpowiedź obejmuje oba zadania (UZP i COI) w jednakowym układzie. Ten sam plik jest w obu repo.

## Status rekomendacji

To **rekomendacja Fable, nie decyzja zespołu**. [ADR-001](ADR-001-stos.md) pozostaje propozycją. Decyzja wymaga akceptacji użytkownika i zapisania nowego ADR z konsekwencjami. Fable nie uruchamiał poleceń ani pomiarów. Wartości RAM i czasu są szacunkami. Licencje oznaczone w odpowiedzi jako „z pamięci” lub „niesprawdzone” wymagają weryfikacji.

## Skrót rekomendacji Fable

| Obszar | UZP — Odwołania2JSON | COI — Cyfryzacja Formularzy |
|---|---|---|
| Wariant zalecany | Czysty Python 3.13, pakiet pip; hybryda reguł/regex dla pól formalnych i małego LLM po API w UE dla pól semantycznych; klasy w YAML → Pydantic/JSON Schema | Python 3.14 + FastAPI; Apache Tika (z Tesseract) jako lokalny kontener dla 8 formatów; LLM zwraca model pośredni, a kod (kompilator) buduje JSON COI |
| Alternatywa | Samo LLM z większym modelem (szybciej, ale mniej punktów za rozmiar modelu) | Java 21 + Spring Boot z wbudowaną Tiką; Docling zamiast Tiki (brak `.doc`) |
| Rust | Rezygnacja: wymóg Pythona i pip, ryzyko kół dla systemu jury, wąskim gardłem jest sieć | Rezygnacja z Axum: poza listą preferowaną, brak zysku przy czasie zdominowanym przez model |
| Biblioteki | `pypdfium2`, `rapidocr` + `onnxruntime`, `pydantic`, `rapidfuzz`, `httpx`; bez PyMuPDF (AGPL) | Tika, Tesseract `pol`, `jsonata-python` / `jsonata` JS, llama.cpp, PDF.js; odrzucone PyMuPDF, antiword; LibreOffice (MPL) dopiero po zgodzie mentora |
| Model | Brak LLM na laptopie jury; kandydat Bielik (11B / 4.5B) u dostawcy w UE (CloudFerro Sherlock, Scaleway: niepotwierdzone); wybór najmniejszego modelu bez utraty F1 | Lokalny GGUF w llama.cpp z gramatyką; Bielik 4.5B Q4/Q5 ok. 3–4 GB RAM (szacunek), opcja 11B; tryb heurystyczny bez LLM jako zabezpieczenie |
| Docker | Tylko dodatek (GUI); główna ścieżka to pip + CLI, test czystego venv na Windows i Linux | Compose: `api`, `tika`, `llm`, `web`; przypięte tagi i digesty, `USER` bez roota, `read_only` + `tmpfs`, test bez sieci |
| GUI | Jeden ekran PDF obok JSON, na końcu; React z gotowym `dist` w repo; egui odrzucone | React/TS uzasadniony (siatka CSS, JSONata na żywo, renderer e-usługi); egui odrzucone |
| Kolejność | Ewaluator F1 → CLI input/output → klasyfikacja → przelew → pełnomocnictwo i odwołanie przez LLM → OCR → porównanie modeli → klasa z YAML → GUI | Kompilator i walidator → REST i Docker → adaptery → heurystyka → LLM → słowniki i walidatory → JSONata → GUI i renderer → test offline |

## Ważne uwagi Fable do sprawdzenia

- Wzorzec `oczekiwane-json/odwolanie.json` zawiera komentarze i brak przecinka, więc nie jest poprawnym JSON. Typy `kwota`, `przez-pelnomocnika` i `pesel` różnią się między wzorcem a przykładami.
- `przyklad_04` zawiera negatywny PDF bez JSON, więc nie ma wzorca pustego wyniku (U-Q03). Interpretacja Fable: `{}` z przełącznikiem w konfiguracji.
- ADR-001 i `pelna-aplikacja.md` w UZP mają układ przeniesiony z COI, sprzeczny z wymogiem `input`, `output` i `requirements.txt` w katalogu głównym.
