---
wersja: 0.6.0
aktualizacja: 2026-11-21
status: katalog roboczy — do uzupełniania po przeglądzie w przeglądarce egui
---

# Katalog przypadków brzegowych UZP

Źródła: **[U]** wiedza użytkownika o prawdziwych dokumentach (rozmowa 2026-11-21), **[M]** mentor ([odpowiedzi](../01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md)), **[K]** konsultacja Fable i Codex ([zestawienie](../07-decyzje/konsultacja-trudne-przypadki-2026-11-21/zestawienie.md)), **[D]** sprawdzone w danych organizatora ([eksperyment](eksperyment-przypadki-brzegowe-2026-11-21.md)).

„W danych” = czy przypadek występuje w 180 pozytywnych PDF-ach organizatora. Jeśli nie, trzeba go wygenerować (generator v2) albo zdobyć fizycznym wydrukiem i skanem.

## Treść i układ (rola podmiotu nie wynika z etykiety)

| # | Przypadek | Źródło | W danych | Dotyczy | Jak testować |
|---|---|---|---|---|---|
| T1 | Brak etykiety roli (np. „Zamawiający”, „Odwołujący”); pisane przez ludzi, bez systematyczności | [U] | Heurystyka 0.6.0: **18/180** (O/P/R: 0/15/3) — [`brak_etykiety_roli`](katalog-kodow.md) [D]; brak wykrycia nie jest dowodem nieobecności | klasyfikacja ról, LLM | nowe układy (grupa C) z usuniętymi etykietami, rola wynikająca ze zdania |
| T2 | Etykieta po danych (najpierw adres, potem etykieta, potem dane osobowe) albo w środku bloku | [U] | Heurystyka 0.6.0: **62/180** (O/P/R: 0/55/7) — [`etykieta_po_danych`](katalog-kodow.md) [D]; brak wykrycia nie jest dowodem nieobecności | kolejność czytania, przypisanie wartości do roli | nowe układy z permutacją: dane → etykieta → dane |
| T3 | Synonimy i warianty etykiet (np. „Odbierający”, „Wykonawca”, „Skarżący”, „w imieniu…”) | [U] | częściowo — „Wykonawca” w 38/60, „Strona” w 50/60 [D] | słownik etykiet, LLM | mutacje etykiet w nowych układach |
| T4 | Brak informacji „kto i co” wprost; rozstrzyga kontekst i wiedza, czego brakuje względem wzorcowego pisma | [U] | do sprawdzenia | LLM z kontekstem pojedynczego dokumentu | dokumenty z usuniętymi wprost podanymi faktami, które da się wywnioskować; osobno takie, których nie da się (→ `null`) |
| T5 | Konsorcjum: referencja zawiera tylko lidera | [K][D] | tak — 6/60 (41, 46, 48, 49, 50, 60) | wybór lidera | jest w danych; regresja |
| T6 | Rzadkie warianty: brak pełnomocnika (0/60), powód 12 (0/60), brak BZP i TED (0/60), przelew-wpis od odwołania (0/60), PESEL (1/98), osoba fizyczna (4) | [K][D] | **nie / rzadko** | ekstrakcja, walidacja | nowe dokumenty z nową referencją |

T1–T2 dotyczą wyłącznie etykiet ról podmiotów, także płatnika i odbiorcy; tytuł „ODWOŁANIE” oraz etykiety metadanych nie są rolami. W kartach to słownik i okno 8 linii, nie pełny audyt semantyczny. Historyczne stwierdzenie o etykietach w nagłówkach 60 odwołań nie rozstrzyga obecności etykiet przy wszystkich podmiotach całego zbioru. Aktualne liczby pochodzą z tego samego przeliczenia co katalog kodów.

## Struktura PDF i odczyt

| # | Przypadek | Źródło | W danych | Dotyczy | Jak testować |
|---|---|---|---|---|---|
| S1 | Tabela układu niewidoczna (białe krawędzie na białym): tekst obok siebie to jeden wiersz, a ekstrakcja tekstu go rozdziela | [U] | do sprawdzenia (przelewy i pełnomocnictwa mają ramki/kolumny wg modeli) | odczyt PDF, kolejność czytania | nowe układy z niewidoczną tabelą 2–3 kolumny; porównanie wiersz po wierszu |
| S2 | PDF ma warstwę tekstu, ale istotna treść jest wklejonym skanem (obraz na stronie tekstowej) — OCR potrzebny także dla obrazów w PDF tekstowym | [U][K] | **nie** — 0 obrazów w pozytywach [D] | decyzja OCR na poziomie regionu, nie dokumentu | strona tekstowa, na której blok z danymi (np. strony postępowania) jest obrazem; referencja bez zmian |
| S3 | Cały skan bez tekstu | [M][K] | **nie** (tylko szablon, bez referencji) | OCR | rasteryzacja wszystkich spraw (grupa A) |
| S4 | Dokument mieszany: część stron tekst, część skan | [M][K] | **nie** | decyzja OCR na stronę | grupa A |
| S5 | Skan z błędną lub niepełną warstwą OCR (cichy błąd) | [K] | **nie** | ocena wiarygodności warstwy tekstu | obraz poprawny + niewidoczny tekst z błędami |
| S6 | Obrót obrazem i flagą `/Rotate`, przekrzywienie | [K][D] | `/Rotate 270` w negatywie | orientacja | grupa A |
| S7 | Dane dalej niż na 3. stronie (odwołania do 11 stron) | [K][D] | tak | czytanie całości | regresja |
| S8 | Kilka dokumentów w jednym pliku, puste strony, załączniki | [K] | nie | klasyfikacja, kontrakt wyjścia | pytanie do mentora; test „nie wywraca się” |

## Wnioski dla architektury (do decyzji ad 3, 4, 5)

1. **Nie można polegać na etykietach.** Przypisanie roli (zamawiający, odwołujący, pełnomocnik) musi wynikać z treści i kontekstu, nie z dopasowania etykiety. Reguły i regex dotyczą tylko formatów (NIP, KRS, rachunki), nie ról — zgodnie z ADR-002 pkt 6.
2. **Odczyt musi zachować układ przestrzenny** (pozycje, wiersze), bo kolejność strumienia tekstu w PDF z niewidoczną tabelą rozrywa wiersze (S1).
3. **Docelowo OCR także na poziomie regionu** (w v1 dopuszczalny OCR całej strony, regiony po pomiarze F1): obraz na stronie tekstowej może zawierać kluczowe dane (S2), a warstwa tekstu skanu może być błędna (S5).
4. **Kontekst:** brakujące informacje wymagają rozumienia całego pisma (T4). Każdy dokument przetwarzamy niezależnie (zasada użytkownika, ADR-002), więc kontekst sprawy z innych plików nie jest dostępny. Braki wskazujemy jawnie w raporcie.

Te wnioski są wejściem dla własnego rozwiązania odczytu PDF/OCR zespołu (ADR-002 pkt 3 i 4) i klasyfikacji (pkt 5).

## Karty dokumentów i kanoniczne kody

Pełna tabela definicji i liczebności: [katalog kodów](katalog-kodow.md). Wyniki lokalizacji referencji, grupowania i kontroli ręcznej: [karty 180 dokumentów](karty-dokumentow-2026-11-21.md). Źródłem kodów pozostaje [kanoniczny JSON](przypadki-brzegowe.json).

## Uzupełnienie 0.6.0 — wykonanie

Kanoniczny katalog zawiera 59 kodów: wcześniejsze 45 przypadków oraz 14 nowych kodów grupy `wykonanie`. Ich definicje, wykrywanie i testy są w [katalogu kodów](katalog-kodow.md), a powiązania ze stanami w [architekturze wewnętrznej](../04-architektura/architektura-wewnetrzna.md#6-stany-i-kody-wykonawcze). Zera kodów wykonawczych w kartach nie potwierdzają odporności produktu — karty nie wykonują silnika.
