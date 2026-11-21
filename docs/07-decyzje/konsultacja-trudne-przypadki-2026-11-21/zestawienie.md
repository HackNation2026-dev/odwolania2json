---
wersja: 0.5.0
aktualizacja: 2026-11-21
status: zestawienie konsultacji — rekomendacje, nie decyzje
---

# Trudne przypadki testowe: zestawienie konsultacji Fable i Codex

Zlecenie: [zlecenie.txt](zlecenie.txt). Odpowiedzi: [Fable](fable-odpowiedz.txt) (`claude-fable-5-2`), [Codex](codex-odpowiedz.txt). Metadane: [metadane.json](metadane.json). Oba modele pracowały niezależnie, tylko z odczytem repo.

## Zgodne wnioski

1. **Trudny zbiór budować ze wszystkich 60 spraw jako pary: oryginał + wariant z tą samą referencją.** Referencja zostaje bez zmian przy przekształceniach niedestrukcyjnych: rasteryzacja, szarość/1-bit, JPEG, obrót (obrazem i flagą `/Rotate`), przekrzywienie bez obcinania, strony mieszane, pusta strona, błędna niewidoczna warstwa OCR przy poprawnym obrazie.
2. **Przekształcenia destrukcyjne** (obcięcie, zaczernienie, usunięcie strony, pieczątka na polu) wymagają nowej referencji. Pole może występować w dokumencie kilka razy, więc zasłonięcie jednego miejsca nie oznacza automatycznie `null`. Przypadki niejednoznaczne trzymać poza głównym F1.
3. **Największe ryzyka:** skan bez tekstu; dokument mieszany (decyzja „tekst czy OCR” musi zapadać na stronę, nie na dokument); skan z błędną lub niepełną warstwą OCR (cichy błąd); obrót, także flagą `/Rotate`; dane dalej niż na 3. stronie (odwołania mają 10–11 stron); trudne negatywy.
4. **Podział po sprawach** na rozwój i zamrożony test (Fable 40/20, Codex 30/10/20). Wszystkie warianty jednej sprawy w tej samej części.
5. **Realizm generatora:** render 300 dpi → rozmycie/tusz/papier → skan 150–300 dpi → kompresja; wariant 1-bit; ksero wielokrotne; perspektywa telefonu (OpenCV); niewidoczna warstwa tekstu (ReportLab, tryb renderowania 3). Augraphy (MIT) ma realistyczne efekty, ale zgodność z Pythonem 3.13 trzeba sprawdzić. Narzędzia tylko do generowania testów, nie do produktu.
6. **Wady obecnego `syntetyczne.py`:** obrót z `expand=False` obcina rogi; `x11` usuwa strony; `x07` ma arbitralną klasę; `x12` nie testuje danych istniejących tylko w obrazie; szum Gaussa jest nierealistyczny; 12 plików z 3 spraw to demonstracja, nie pomiar.
7. **Prawdziwy wydruk i skan (oraz zdjęcia telefonem) ~10 znanych spraw** to najcenniejszy podzbiór — referencje już istnieją.
8. **Ręczna referencja skanu szablonu** (`szablon-aplikacja/input/case1/przyklad odwolanie.pdf`, plik wynikowy organizatora ma 0 bajtów), opisana niezależnie przez dwie osoby.
9. **Eksperyment z przypadkami brzegowymi nie mierzył F1 ekstrakcji** — tylko klasę, wykrycie problemów i początek transkrypcji z ≤3 stron.

## Luki treściowe w 60 sprawach (zweryfikowane w danych)

| Wariant | Pokrycie |
|---|---|
| Odwołanie bez pełnomocnika | 0/60 |
| Powód czynności 12 | 0/60 |
| Brak obu numerów BZP i TED | 0/60 |
| Przelew będący wpisem od odwołania | 0/60 (wszystkie: opłata skarbowa, kwoty 17/34/50/100/200) |
| PESEL pełnomocnika | 1 wartość na 98 osób (przyklad_43) |
| Mocodawca osoba fizyczna | 4 (44, 47, 51, 52) |
| Dwóch zamawiających | 3 (42, 51, 59) |
| Konsorcjum odwołujących | 6 (41, 46, 48, 49, 50, 60) — referencja zawiera lidera |

Rozbieżność: Fable podał konsorcja 0/60 na podstawie samych JSON-ów; Codex 6/60 na podstawie tekstu PDF. Sprawdzone `pdftotext` (2026-11-21): w przyklad_41 „Lider Konsorcjum”, „Partner Konsorcjum” — **rację ma Codex**.

## Różnice w planie

- Fable: najpierw grupa A (przekształcenia niedestrukcyjne) na wszystkich sprawach i fizyczny skan w 5–6 h; nowe treści (grupa C) w 12–16 h.
- Codex: minimalny start 12 spraw × 3 klasy × 2 warianty = 72 PDF-y, dobrane pod rzadkie treści; błędna warstwa OCR jako osobny krok; ręczna referencja szablonu wcześnie (9–12 h).

## Pytania do mentora (z obu konsultacji)

1. Czy skany w teście pochodzą z tego samego generatora co przykłady?
2. Jaki wynik dla pliku z kilkoma dokumentami?
3. Czy pole nieczytelne lub zasłonięte ma w referencji `null`?
