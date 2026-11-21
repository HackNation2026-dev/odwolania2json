---
wersja: 0.4.0
aktualizacja: 2026-11-21
status: PROPONOWANY — nie jest decyzją zespołu
---

# Proponowany stos UZP — Odwołania2JSON

> **Status: PROPONOWANY.** To propozycja do akceptacji przez zespół, nie decyzja ani opis gotowej aplikacji. Opiera się na [konsultacji Fable](../07-decyzje/konsultacja-fable.md) (`claude-fable-5-2`) z korektą dotyczącą GUI według źródeł organizatora. Wartości RAM i czasu są szacunkami. Licencje oznaczone jako niesprawdzone wymagają weryfikacji. Decyzję zapisuje nowy ADR. [ADR-001](../07-decyzje/ADR-001-stos.md) pozostaje propozycją.

## Wymagania, które stos musi spełnić (organizator)

Python 3.13+, `requirements.txt` i instalacja przez pip, obowiązkowe CLI, foldery `input`/`output`, wyłącznie open source (także model). Uruchomienie lokalne bez GPU; LLM po publicznym API dostawcy z serwerami w UE/EOG. Ścisły JSON. Obcy dokument daje pusty JSON pod nazwą pliku wejściowego. GUI nie jest wymagane, ale jest dodatkowo punktowane. Źródła: [wymagania](../03-wymagania/README.md), [punktacja](../01-zadanie/punktacja.md).

## Proponowany stos

| Warstwa | Propozycja | Status sprawdzenia |
|---|---|---|
| Język i dostarczenie | Python 3.13, jeden pakiet, `requirements.txt`, CLI (`python -m ...` i `start.bat`) | wymóg organizatora |
| Tekst z PDF | `pypdfium2` (Apache-2.0/BSD-3; PDFium BSD) | licencja sprawdzona przez Fable |
| OCR (tylko strony bez warstwy tekstowej) | `rapidocr` + `onnxruntime` (Apache-2.0, MIT), bez binarek systemowych | jakość polskiego OCR, licencja wag PP-OCR i koła dla 3.13 do sprawdzenia |
| Klasyfikacja | reguły i słowa kluczowe z konfiguracji, model tylko przy niepewności | propozycja |
| Ekstrakcja | hybryda: regex i normalizatory dla NIP, REGON, KRS, PESEL, rachunków, dat, BZP/TED, kwot; LLM dla nazw, ról, `czynnosc_powod_id` i opisów | propozycja |
| Konfiguracja klas | YAML na klasę → dynamiczny model `pydantic` i JSON Schema; nowa klasa bez zmiany kodu | propozycja; punktowane 1–20 pkt |
| LLM | klient zgodny z OpenAI (`httpx`), `base_url`, model i klucz z env; kandydat Bielik (4.5B lub 11B) u dostawcy w UE | lokalizacja dostawcy, licencja v3 i wyjście strukturalne do potwierdzenia |
| Serializacja | wyłącznie kod (`pydantic`): stała kolejność kluczy, `null` zamiast braku klucza; `czynnosc_opis` dokładnie według słownika | wzorce organizatora po poprawce `7590db8` |
| Ewaluacja własna | ewaluator F1 z `rapidfuzz` (próg 80% dla długich pól, listy po treści) | przybliżenie; oficjalny algorytm nieznany |
| GUI | FastAPI + React/TypeScript (gotowy `dist` w repo, bez Node u jury): wgranie PDF, analiza, PDF obok JSON, wskazanie fragmentu źródłowego pola | propozycja |
| Docker | opcjonalny, tylko dla GUI: `python:3.13-slim` z przypiętym tagiem, użytkownik bez roota, bez modelu w obrazie | propozycja |
| Rust | brak w rdzeniu: wymóg Pythona i pip, ryzyko kół na systemie jury, czas zdominowany przez API | rekomendacja Fable |

## GUI — korekta względem konsultacji

Fable zalecił GUI „na końcu”, bo daje najwyżej 10 pkt. Organizator jednak wymienia GUI jako punktowane w trzech miejscach: README „Interfejs wykonawczy”, kryteria finału „1-10 … (np. GUI)” i FAQ 12b („widok obok siebie”). Dodatkowo „szczególnie premiuje” transparentność ekstrakcji. W zgłoszeniu wymaga też prototypu „umożliwiającego wgranie dokumentów i odczytanie rezultatów ekstrakcji”. Proponowana kolejność: prosty ekran PDF|JSON wcześnie, na tym samym silniku co CLI, a dopracowanie po osiągnięciu stabilnego F1.

## Proponowana kolejność

1. Loader 60 spraw i własny ewaluator F1.
2. CLI `input` → `output`, odtworzenie drzewa, pusty JSON dla obcego dokumentu.
3. Ekstrakcja tekstu i klasyfikacja regułowa, w tym zbiór negatywny.
4. Przelew samymi regułami.
5. Pierwsza wersja GUI PDF|JSON na tym samym silniku.
6. Pełnomocnictwo i odwołanie: YAML → schemat → LLM → normalizatory.
7. Zapasowy OCR.
8. Porównanie rozmiarów modeli; wybór najmniejszego bez utraty F1.
9. Demonstracja nowej klasy dodanej samym YAML-em.
10. Transparentność: fragment źródłowy dla każdego pola w GUI.
11. Test czystej instalacji na Windows i Linux, przekazanie klucza API.

## Otwarte przed decyzją

Wybór dostawcy i modelu w UE/EOG oraz ich licencji; format pustego wyniku (U-Q03); system operacyjny jury; obecność skanów w teście ukrytym.

## Uzupełnienie 0.5.0 (2026-11-21)

Status zmieniony przez [ADR-002](../07-decyzje/ADR-002-decyzje-po-recenzji.md): odczyt PDF (`pypdfium2`) i OCR (`rapidocr`) odrzucone przez użytkownika, klasyfikacja i wybór LLM otwarte, GUI: React/TS, prawdopodobnie Next.js. Tabela powyżej pozostaje jako historia propozycji.
