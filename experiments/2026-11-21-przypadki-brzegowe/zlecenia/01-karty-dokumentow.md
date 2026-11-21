# Zlecenie dla Codex: karty dokumentów (systematyzacja 180 oryginałów)

Pracujesz w repo `odwolania2json` (bieżący katalog). Piszesz po polsku (komentarze, docstringi, dokumentacja). Python: `/tmp/claude-1000/-home-user-Muzyka-HackNation-2026---Zadania-dla-Uczestnik-w/73ed5933-5395-4a9d-b5b1-03252072a24b/scratchpad/venv313/bin/python` (3.13; są: pypdf, pillow, numpy, rapidfuzz, jsonschema, pyyaml, pydantic). Jest poppler (`pdftotext`, `pdfinfo`, `pdfimages`). Bez sieci. Najpierw przeczytaj:

- `docs/05-weryfikacja/katalog-przypadkow-brzegowych.md` i **kanoniczny katalog kodów** `docs/05-weryfikacja/przypadki-brzegowe.json`
- `docs/07-decyzje/ADR-002-decyzje-po-recenzji.md` (zwłaszcza uzupełnienia na końcu)
- `experiments/2026-11-21-przypadki-brzegowe/format/FORMAT.md` i schematy obok, `narzedzia/wspolne.py`, `narzedzia/inwentarz.py`
- dane: `docs/02-materialy/organizator-uzp/dane/przyklad_XX/{odwolanie,pelnomocnictwo,potwierdzenie_przelewu}.pdf` + `{odwolanie,pelnomocnictwo,przelew}.json`; poprawki referencji nakładaj z `docs/02-materialy/organizator-uzp-aktualizacje/main-7590db8/dane/` (5 plików odwołań); słownik `.../main-7590db8/oczekiwane-json/czynnosc_powod_id_dict.md`

**Nie zmieniaj niczego w `docs/02-materialy/`** (oryginały). Nie dotykaj `wyniki/*/adnotacje/` ani `przegladarka/`. Każdy dokument przetwarzaj niezależnie (wymóg).

## Cel

Dla każdego z 180 pozytywnych PDF-ów zbudować **kartę dokumentu**: gdzie i jak każda wartość z referencji występuje w dokumencie, jakie grupy (podmioty) tworzą te wartości i jakie kody przypadków brzegowych z katalogu dotyczą dokumentu. Plus odpowiedź na pytanie użytkownika: **czy grupowanie da się zrobić** — czy wartości jednego podmiotu (np. `Zamawiajacy[0]`: nazwa, NIP, REGON, KRS) tworzą na stronie spójny obszar, który UI obrysuje ramką z opisem.

## Do zrobienia

1. `narzedzia/wspolne.py`: `TAKSONOMIA` ma być wczytywana z `docs/05-weryfikacja/przypadki-brzegowe.json` (kod, nazwa, definicja) zamiast listy w kodzie. Zachowaj zgodność z `inwentarz.py`/`modele.py`/`scal.py`. Uruchom `inwentarz.py`, żeby manifest dostał nową taksonomię (zachowuje wyniki modeli — sprawdź).
2. `narzedzia/katalog_md.py`: generuje `docs/05-weryfikacja/katalog-kodow.md` (tabela wszystkich kodów z JSON: kod, grupa, nazwa, definicja, źródła, wykrywanie, testowanie, oraz kolumna „w danych” z liczbami z kart). Plik `.md` musi mieć nagłówek front matter jak inne dokumenty (`wersja: 0.5.0`, `aktualizacja: 2026-11-21`, `status: ...`), bo sprawdza to `scripts/verify_docs.py`. Dodaj odnośnik do niego w `docs/05-weryfikacja/katalog-przypadkow-brzegowych.md` (sekcja na końcu, bez usuwania treści).
3. `format/karta.schema.json` (draft 2020-12) i `narzedzia/karty.py` zapisujący `wyniki/2026-11-21-v1/karty/<id>.json` (id jak w manifeście, np. `p01_odwolanie`) oraz `wyniki/2026-11-21-v1/karty/podsumowanie.json`. Karta zawiera co najmniej:
   - `pola`: dla każdej ścieżki referencji (np. `Zamawiajacy[0].nip`, `OdwolanieKIO.czynnosc_dzien`, `przelew_bankowy.kwota`): wartość z referencji, `dopasowanie` ∈ {`dokladne`, `inny_zapis`, `inna_forma_gramatyczna`, `wyliczana`, `nieznaleziona`, `null_w_referencji`}, lista `wystapienia` [{strona, bbox [x0,y0,x1,y1] w punktach PDF z początkiem w lewym górnym rogu, tekst_w_dokumencie, etykieta_pola (tekst lub null), etykieta_roli {tekst, polozenie ∈ przed|po|brak, odleglosc_linii}}].
   - Dopasowanie według typu pola: identyfikatory cyfrowe (NIP, REGON, KRS, PESEL, rachunki) ignorując spacje, myślniki, prefiks PL; daty ISO ⇄ `DD.MM.RRRR`, `D miesiąca RRRR` (polskie miesiące w dopełniaczu), z „r.”; kwota ⇄ `200,00`, `200.00`, z `zł`/`PLN`; BZP ze spacją i bez; TED `NNNNNN-RRRR` ⇄ `RRRR/S NNN-NNNNNN`; teksty (nazwy, tytuł, numer postępowania, mail, numer transakcji) z normalizacją białych znaków, wielkości liter i z dopasowaniem rozmytym (rapidfuzz) dla długich tekstów i form gramatycznych — progi uzasadnij w kodzie. `czynnosc_opis`, `przez-pelnomocnika`, `prowadzacy_postepowanie`, `typ`, `czynnosc_powod_id` → `wyliczana`, chyba że wartość dosłownie występuje.
   - Pozycje słów: `pdftotext -bbox-layout` (bloki, linie, słowa z bbox). Wartość może być rozbita na kilka linii (kod `wartosc_w_kilku_liniach`).
   - `grupy`: dla każdego podmiotu/obiektu (`OdwolanieKIO`, `Odwolujacy[i]`, `Odwolujacy[i].pelnomocnik`, `Zamawiajacy[i]`, `ZamowieniePubliczne`, `mocodawca[i]`, `mocodawca[i].podpisujacy[j]`, `pelnomocnicy[i]`, `przelew_bankowy`): pola grupy, etykieta roli (jeśli znaleziona), dla każdej strony bbox będący sumą pierwszych wystąpień pól grupy (i etykiety roli), oraz ocena **spójności**: czy w bbox grupy nie ma wartości innej grupy (`spojna: true/false`, lista kolidujących pól), wysokość w liniach. To jest dowód „czy grupowanie da się zrobić”.
   - `uklad` per strona (heurystyka, oznaczona jako przybliżenie): liczba kolumn tekstu, linie z dużymi odstępami poziomymi (kandydat `niewidoczna_tabela`/`uklad_wielokolumnowy`), czy etykieta i wartość jednego wiersza trafiły do różnych bloków `pdftotext`.
   - `kody`: lista {kod z katalogu, pole lub null, dowód (krótki opis)} — tylko kody z `przypadki-brzegowe.json`; nowy kod = błąd.
   - `braki`: pola z `nieznaleziona` z hipotezą przyczyny.
4. `podsumowanie.json` + `docs/05-weryfikacja/karty-dokumentow-2026-11-21.md` (z front matter): liczba dokumentów z każdym kodem (per klasa), rozkład `dopasowanie` per pole, lista pól najczęściej `nieznaleziona`, **wynik grupowania**: odsetek grup spójnych per typ grupy i klasa, przykłady niespójnych z id dokumentu. Fakty oddziel od interpretacji.
5. Testy: `narzedzia/test_karty.py` (pytest — zainstaluj do tego venv przez `uv pip install -p <python> pytest`, jeśli brak) dla funkcji dopasowania i normalizacji, w tym przypadki negatywne i **mutacyjne** (np. zmieniona jedna cyfra NIP nie może być `dokladne`; data z innym dniem nie pasuje). Wszystkie testy muszą przechodzić.
6. Weryfikacja ręczna: wybierz losowo 5 kart (różne klasy, w tym sprawa z konsorcjum 41 i z dwoma zamawiającymi 42) i porównaj z tekstem PDF; opisz w dokumencie z pkt 4, co sprawdziłeś i jakie błędy heurystyk zostały.
7. Na koniec: `python3 scripts/verify_docs.py` musi przejść.

## Raport końcowy

Krótko po polsku: utworzone/zmienione pliki, wyniki testów (liczby), główne liczby z podsumowania (pokrycie dopasowań, kody, grupowanie), znane ograniczenia heurystyk, co sprawdziłeś ręcznie.
