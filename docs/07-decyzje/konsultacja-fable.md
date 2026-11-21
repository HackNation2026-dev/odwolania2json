---
wersja: 0.4.0
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

## Uwaga zespołu do rekomendacji GUI (UZP)

Rekomendacja Fable „GUI na końcu, najwyżej 10 pkt” pozostaje bez zmian jako jego opinia. Źródła organizatora UZP wymieniają jednak GUI jako punktowane w trzech miejscach: README „Interfejs wykonawczy”, kryteria finału „1-10 Inne ciekawe funkcje dodane do aplikacji (np. GUI)” i FAQ 12b („Preferowany jest widok obok siebie”). Szczególnie premiowana jest też „transparentność procesu ekstrakcji danych”. Wniosek zespołu: prosty ekran PDF|JSON wcześnie, dopracowanie po osiągnięciu stabilnego F1. Zob. [proponowany stos](../04-architektura/proponowany-stos.md).

## Historia: zlecenie i status z wersji 0.2.1

Poniżej przywrócono bez zmian treść tego pliku z wersji 0.2.1 (commit `9762c12`), nadpisaną w 0.3.0.

### Konsultacja Fable — zlecenie i status

Status: konsultację odłożono na prośbę użytkownika do ponownego uruchomienia z innymi uprawnieniami. Nie uzyskano opinii drugiego modelu.

Orca nie uruchomiła runtime. Bezpośrednie CLI `claude --version` działało (2.1.330), a pomoc potwierdziła alias `fable` w `--model`. Bezpośrednią próbę konsultacji uruchomiono, a następnie przerwano na prośbę użytkownika; sesja zakończyła się kodem 130. Nie potwierdzono kanonicznego modelu odpowiedzi ani rekomendacji.

Kolejna próba powinna użyć bezpośredniego CLI z aktualną konfiguracją użytkownika. Brak runtime Orca nie jest dowodem awarii CLI Claude.

#### Zlecenie do przekazania Fable

Przeprowadź niezależną ocenę stosu dla dwóch osobnych monorepo: formularze (COI) i odwolania2json (UZP). Czytaj ich docs, oryginalne materiały oraz najnowsze komunikaty UZP z Discorda. Nie traktuj propozycji poprzedniego autora jako decyzji.

Preferencje zespołu: Rust, Python, TypeScript i Docker. Rust jest preferencją, nie warunkiem. Wybierz dojrzalsze rozwiązanie, jeżeli lepiej spełnia wymagania i skraca wykonanie.

UZP: Python 3.13+, requirements.txt i CLI. Otwarte komponenty i model możliwy do instalacji lokalnej. LLM po publicznym API; jury nie instaluje modelu na laptopie. Darmowe, płatne i własne API dozwolone, z pozostałymi ograniczeniami regionu i licencji. JSON ścisły, listy po treści, wskazane długie teksty z progiem 80%. GUI opcjonalne. Sprawdź ryzyko jakiegokolwiek komponentu Rust.

COI: REST, PDF/DOC/DOCX/ODS/XLSX/JPG/JPEG/PNG -> konfiguracja COI. Działanie bez zależności od zewnętrznych API, MCP i SaaS. Open source bez wykluczonego copyleft; brak wymaganej licencji komercyjnej. Java 21+/Python 3.14+ są preferowane. Docker, pliki użytkownika tylko tymczasowo. Uwzględnij JSON Schema, reguły i przykłady lokalne.

Odpowiedz po polsku w tej samej strukturze dla obu zadań: wariant zalecany, alternatywa, udział Rusta, dojrzałe biblioteki, licencje i zależności, budowanie Docker, ryzyka formatu DOC/OCR/JSON, model i sprzęt, plan pełnej ścieżki. Oddziel wymaganie organizatora od rekomendacji.

Porównaj React/TypeScript i egui tylko w zakresie rzeczywistych potrzeb użytkownika. Podaj źródła dokumentacji technicznej i ograniczenia sprawdzenia. Nie rekomenduj narzędzia wyłącznie na podstawie nazwy lub samej licencji wrappera.

Wynik: tabela decyzji i uzasadnienie. Podaj rzeczywistą nazwę użytego modelu. Nie twórz repo, nie publikuj, nie zmieniaj źródeł i nie odczytuj sekretów.
