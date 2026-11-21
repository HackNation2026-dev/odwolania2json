---
wersja: 0.5.0
aktualizacja: 2026-11-21
status: zlecenie dla Codex — aktualizacja projektu UI do wersji 0.2.0
---

# Zlecenie: aktualizacja projektu UI (Codex)

Pracujesz w repo `odwolania2json`. Piszesz po polsku. Zmieniasz **wyłącznie** `docs/04-architektura/gui/projekt-ui.md` (do wersji 0.2.0) i możesz dodać plik `docs/04-architektura/gui/zmiany-ui-0.2.0.md` z listą zmian. Nie piszesz kodu. Na końcu `python3 scripts/verify_docs.py` musi przechodzić.

## Przeczytaj

1. Obecny projekt: `docs/04-architektura/gui/projekt-ui.md` (v0.1.0) i brief `brief-projektu-ui.md`.
2. Recenzja projektu: `docs/04-architektura/gui/recenzja-codex-2026-11-21.md` — **nanieś wszystkie uwagi** (KRYTYCZNE i WAŻNE obowiązkowo, DROBNE gdzie sensowne).
3. Decyzje: `docs/07-decyzje/ADR-002-decyzje-po-recenzji.md`, szczególnie uzupełnienia na końcu (zasady przypadków brzegowych, brak „happy path”, decyzje GUI).
4. Pipeline i jego ocena: `docs/07-decyzje/konsultacja-pipeline-2026-11-21/zlecenie.txt` i `codex-odpowiedz.txt`.
5. Przypadki brzegowe i karty: `docs/05-weryfikacja/katalog-przypadkow-brzegowych.md`, `przypadki-brzegowe.json`, `katalog-kodow.md`, `karty-dokumentow-2026-11-21.md`, schemat `experiments/2026-11-21-przypadki-brzegowe/format/karta.schema.json`.
6. Odpowiedzi mentora: `docs/01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md`.

## Decyzje użytkownika (obowiązujące)

- React + TypeScript; gotowa biblioteka komponentów — tak, nazwę wskaże użytkownik (projekt neutralny wobec biblioteki).
- Logowanie i role **projektujemy w UI**, ale **MVP działa bez logowania** (tryb demonstracyjny, dane syntetyczne — zgodnie z recenzją).
- **Bez OpenUI** teraz: usuń elementy generatywne z MVP i pełnej wersji; zostaw jedną krótką sekcję „punkt rozszerzenia (poza zakresem)”.
- Dostarczenie: na teście tylko `pip`; frontend jako gotowe pliki statyczne w pakiecie Pythona, bez Node u jury.

## Nowe ustalenia do uwzględnienia (projekt ma umożliwić ich wprowadzenie)

1. **Grupy z wieloma obrysami**: grupa (podmiot) może mieć kilka obszarów, także na różnych stronach, połączonych kolorem i identyfikatorem; przy kolizji z inną grupą przejście na oznaczenie pól. Karty dają 446/622 spójnych grup — UI nie może zakładać jednej ramki.
2. **Diagnoza dokumentu, strony i regionu** (wewnętrzna klasyfikacja niezależna od klasy biznesowej): źródło tekstu (tekst cyfrowy / OCR ukryty / obraz z tekstem / obraz dekoracyjny / tekst jako krzywe / pusty), typ strony, orientacja, jakość, pewność, sygnały decyzji, kody odstępstw z katalogu. Pokaż, gdzie operator to widzi.
3. **Stany wyniku dokumentu**: pełny, częściowy (z listą braków), obcy (`{}`), wiele dokumentów, niejednoznaczny (do przeglądu), błąd techniczny — każdy z innym wyglądem i tekstem; awaria nigdy jako `{}`.
4. **Braki jawnie**: rozróżnienie wewnętrzne „brak / nie dotyczy / nieczytelne / sprzeczne / nieprzetworzone” w UI, przy `null` w ocenianym JSON.
5. **Kody przypadków brzegowych** z katalogu widoczne przy dokumencie i polu; filtr listy po kodach.
6. **Każdy dokument niezależnie** — UI nie sugeruje przenoszenia danych między dokumentami sprawy.
7. **Dowód pola**: strona, cytat, obrysy, źródło (tekst PDF / OCR), dla wartości wyliczonej reguła i przesłanki; brak geometrii = komunikat o przybliżonej lokalizacji.

## Wymagania do wyniku

- Zachowaj strukturę 10 sekcji i oznaczenia źródeł; dopisz źródła nowych elementów (ADR-002, konsultacja pipeline, karty).
- Uzupełnij brakujące ramki z recenzji (S04, S11, S13, S14, niezapisane zmiany, błąd zapisu, odmowa odsłonięcia danych, aktywacja YAML), dodaj ramki dla nowych stanów (diagnoza, wiele obrysów, niejednoznaczny, wiele dokumentów), macierz widok × stan × szerokość × motyw × język z reprezentatywnymi ramkami, jeden widok EN, kontrolę reflow 320 px; oddziel rozmiar viewportu od wysokości treści.
- Popraw kontrast `evidence-border` w motywie ciemnym i tabelę obliczeń (policz wzorem WCAG).
- MVP realne na dobę: wgranie PDF → lista statusów → PDF/dane/JSON z dowodem (strona + fragment) → pobranie wyniku; reszta jako etapy po MVP.
- Na końcu sekcja „Otwarte pytania” zaktualizowana (usuń rozstrzygnięte).

## Raport końcowy

Krótko: co zmieniono (lista według uwag recenzji i nowych ustaleń), liczba stron i ramek, zakres MVP, pozostałe pytania, wynik `verify_docs.py`.
