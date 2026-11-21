---
wersja: 0.6.0
aktualizacja: 2026-11-21
status: zlecenie dla Codex — architektura wewnętrzna ELT i usunięcie sprzeczności
---

# Zlecenie A (Codex): architektura wewnętrzna ELT + sprzeczności

Repo `odwolania2json`, bieżący katalog. Po polsku. Nie piszesz kodu produktu. Nie dotykasz `docs/04-architektura/gui/` (robi to zlecenie B) ani `docs/02-materialy/organizator*`. Na końcu `python3 scripts/verify_docs.py` musi przejść.

## Przeczytaj

- `docs/07-decyzje/ADR-002-decyzje-po-recenzji.md` (cały; ostatnie uzupełnienia: shim OCR, ETL/ELT, brak „happy path”, każdy dokument niezależnie, braki jawnie).
- Oceny: `docs/07-decyzje/konsultacja-pipeline-2026-11-21/codex-odpowiedz.txt`, `docs/07-decyzje/konsultacja-ocena-calosci-2026-11-21/fable-odpowiedz.txt`, `docs/04-architektura/gui/ocena-ui-vs-kryteria.txt`.
- `docs/03-wymagania/README.md`, `docs/01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md`, `docs/05-weryfikacja/zasady-f1.md`, `docs/05-weryfikacja/przypadki-brzegowe.json`, `experiments/2026-11-21-yaml-klasy/klasy/*.yaml`, `experiments/2026-11-21-przypadki-brzegowe/format/karta.schema.json`.

## 1. Nowy dokument `docs/04-architektura/architektura-wewnetrzna.md` (wersja 0.6.0)

Opis „jak to działa w środku” jako **ELT wzbogacony o warstwę OCR i ekstraktory AI**. Musi zawierać:

1. **Zasady** (z ADR-002) w punktach i warunki Fable (sekcja 7 jego odpowiedzi) jako „warunki wejścia do implementacji”.
2. **Etapy** z wejściem, wyjściem (artefakt na dysku), odpowiedzialnością (kod / ekstraktor AI / OCR), wersją i obsługą błędu:
   - E: ekstrakcja warstwy surowej — PDF → strony, słowa z geometrią, obrazy, warstwa tekstu PDF albo OCR; diagnoza dokumentu i strony (źródło tekstu, pokrycie, obrót, pewność, sygnały).
   - L: zapis warstwy surowej do katalogu roboczego dokumentu (staging), wersjonowany.
   - T1 segmenty i router (funkcja dokumentu; progi per klasa; wyjścia: klasa / obcy `{}` / niejednoznaczny / błąd).
   - T2 grupy, podmioty, role. T3 kandydaci pól z dowodami (regex dla formatów, ekstraktor AI dla znaczenia). T4 scalanie i kontrola pokrycia (pętla do T3). T5 normalizacja, słowniki, walidacja (YAML).
   - Wyjście: oceniany JSON (ściśle wg referencji), osobno dowody, raport braków i diagnozy.
   Uzasadnij ELT zamiast ETL (przeliczanie transformacji bez ponownego OCR, wersje, pomiar).
3. **Ścieżka pionowa najpierw** (warunek Fable): które etapy są w v1 (minimalnie: E, L, T1, T3, T5 z jednym wywołaniem ekstraktora AI na dokument), które dochodzą po pomiarze (T2, T4, regiony), z kryterium włączenia („poprawia F1 na zbiorze rozwojowym”).
4. **Kontrakty** (pola i typy, przykłady JSON): warstwa odczytu (wspólna dla tekstu PDF i OCR), komponent OCR (wejście obraz strony/regionu; wyjście linie/słowa z bbox, pewność, obrót; metadane: dostępny, nazwa, wersja, liczba parametrów, licencja, lokalizacja), diagnoza, decyzja routera (kandydaci, sygnały za i przeciw), kandydat pola, dowód, raport braków (powody: brak / nie dotyczy / nieczytelne / sprzeczne / nieprzetworzone), stan wyniku, błąd techniczny.
5. **Shim OCR**: tymczasowy dostawca (propozycja: rapidocr + onnxruntime, pip, CPU) za kontraktem; dostawca „brak” (`dostepny=false`) gdy OCR wyłączony; własny model ML zespołu zastępuje shim bez zmian w reszcie. Decyzja ADR-002 pkt 4 bez zmian.
6. **Stany i kody wykonawcze**: postęp (w kolejce, w toku, zakończony) osobno od stanu wyniku (pełny, częściowy, obcy, niejednoznaczny, wiele dokumentów, błąd techniczny); lista kodów wykonawczych (np. `ocr_niedostepny`, `pdf_uszkodzony`, `pdf_zaszyfrowany`, `llm_niedostepny`, `llm_odpowiedz_niepoprawna`, `konfiguracja_niepoprawna`, `limit_czasu`) w `snake_case`, z mapowaniem na katalog przypadków.
7. **Katalog roboczy**: struktura plików per wsad i dokument (warstwa surowa, artefakty T1–T5, wynik, dowody, raport, log zdarzeń), zapis atomowy, niezależność dokumentów, kontynuacja wsadu po błędzie.
8. **Wersjonowanie i cache**: tożsamość wyniku = skrót dokumentu + wersje (silnik, konfiguracja klas, prompt, model LLM, dostawca OCR); cache tylko przy identycznym kluczu; nigdy stary wynik przy awarii API.
9. **Model wykonania**: zadania z odpytywaniem i katalog roboczy na dysku, bez bazy (rekomendacja Fable) — oznacz jako **propozycja do decyzji użytkownika**.
10. **Decyzje otwarte przed OpenAPI** (lista Fable pkt 6) z rekomendacją i stanem „do decyzji użytkownika”: polityka `null` dla pól wymaganych w YAML; brak pliku czy `{}` przy błędzie/braku OCR w trybie konkursowym (przełącznik do odpowiedzi mentora); wiele dokumentów w PDF; geometria opcjonalna w v1; język nazw w API; kanał klucza API.
11. **Pomiar**: loader 60 spraw, ewaluator TP/TN/FP/FN, CLI na atrapie silnika, ablacje etapów — jako wymagania wejścia.
12. Diagram tekstowy (mermaid) całości.

## 2. Usunięcie sprzeczności (Fable pkt 2 i 5)

- `docs/04-architektura/README.md` i `docs/04-architektura/pelna-aplikacja.md`: dopisz na górze wyraźne uzupełnienie 0.6.0, że obowiązuje ADR-002 i `architektura-wewnetrzna.md` (pip, bez Rusta i Dockera u jury, GUI obowiązkowe); nie usuwaj historii.
- `docs/03-wymagania/README.md`: w tabeli przy UZP-02, UZP-05, UZP-15 dopisz w treści wiersza odsyłacz do uzupełnienia 0.5.0 (GUI obowiązkowe, OCR wymagany, tylko pip), żeby tabela nie przeczyła uzupełnieniu.
- ADR-002: dopisz uzupełnienie wyjaśniające „Next.js” — dopuszczalny tylko jako statyczny eksport w pakiecie pip, bez serwera Node u jury.
- `docs/05-weryfikacja/przypadki-brzegowe.json`: dodaj grupę `wykonanie` z kodami wykonawczymi z pkt 1.6 (kod, nazwa, definicja, źródła, wykrywanie, testowanie); zawęź definicje `brak_etykiety_roli` i `etykieta_po_danych` do **etykiet ról podmiotów** (zamawiający, odwołujący, pełnomocnik, mocodawca, płatnik/odbiorca) — tytuł dokumentu („ODWOŁANIE”) nie jest etykietą roli. Następnie: zaktualizuj enum w `experiments/2026-11-21-przypadki-brzegowe/format/karta.schema.json`, popraw heurystyki w `narzedzia/karty.py` zgodnie z nowymi definicjami, przelicz karty (`karty.py`), wygeneruj `katalog-kodow.md` (`katalog_md.py`), uruchom testy (`pytest` w venv: `/tmp/claude-1000/-home-user-Muzyka-HackNation-2026---Zadania-dla-Uczestnik-w/73ed5933-5395-4a9d-b5b1-03252072a24b/scratchpad/venv313/bin/python -m pytest`) i zaktualizuj liczby w `docs/05-weryfikacja/karty-dokumentow-2026-11-21.md` oraz w `katalog-przypadkow-brzegowych.md` (tabela T1–T2 nie może przeczyć katalogowi kodów).
- `docs/07-decyzje/pytania-otwarte.md`: dopisz pytania do mentora: skany z tego samego generatora?; wynik dla wielu dokumentów w PDF?; pole nieczytelne = `null`?; brak pliku czy `{}` przy błędzie?; czy model OCR liczy się do „największego modelu”?
- `CHANGELOG.md` i `VERSION` → 0.6.0.

## Raport

Krótko: pliki, kluczowe decyzje w architekturze, nowe kody, wyniki testów i nowe liczby kart (kody etykiet), wynik `verify_docs.py`.
