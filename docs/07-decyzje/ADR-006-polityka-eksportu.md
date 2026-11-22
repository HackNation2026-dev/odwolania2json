---
wersja: 0.1.0
aktualizacja: 2026-11-22
status: przyjęta; ma pierwszeństwo przed architekturą wewnętrzną §4.5 i §10 w zakresie eksportu
---

# ADR-006: polityka eksportu wyniku i awarii w `process`

## Kontekst

README organizatora (§2 pkt 4) wymaga pliku JSON dla każdego pliku wejściowego. Trzy miejsca opisywały to różnie: [architektura §10](../04-architektura/architektura-wewnetrzna.md) (`error_export`, domyślnie `empty_json`; brak kotwicy bbox blokuje wartość; `ambiguous` bez eksportu), `engine.py` (brak pliku przy błędzie i usunięcie poprzedniego wyniku) oraz uprząż eksperymentów (brak pliku przy awarii LLM, błąd przy `ambiguous`).

Dane z eksperymentów (F1 przybliżony ewaluatora zespołu, bootstrap po sprawach; [E17](../../experiments/2026-11-21-wybor-modulow/llm-e2e/E17/README.md), [E16](../../experiments/2026-11-21-wybor-modulow/atak/E16/README.md)):

- zerowanie pola bez kotwicy bbox: ΔF1 −0,021 [−0,029; −0,014] na tekście i −0,073 [−0,082; −0,064] na skanach;
- brak eksportu dokumentu `partial`: ΔF1 −0,208 [−0,268; −0,155] na tekście i −0,453 [−0,545; −0,368] na skanach;
- usuwanie elementów list z samymi `null` (`prune`) zmienia strukturę względem wzorców organizatora (różnica 166 `null`).

## Decyzja

1. **Plik wyniku powstaje dla każdego PDF-a wejściowego**, pod nazwą bazową wejścia z rozszerzeniem `.json`, z zachowaniem podkatalogów. Rozszerzenie wejścia jest rozpoznawane bez rozróżniania wielkości liter (`.pdf`, `.PDF`).
2. **Dokument obcy** (`foreign`) → dokładnie `{}`.
3. **Błąd techniczny** dokumentu (PDF uszkodzony lub zaszyfrowany, brak tekstu, brak OCR dla wszystkich stron, LLM po wyczerpaniu ponowień, limit, nieoczekiwany wyjątek) → `{}` jako wynik **oraz** wpis w raporcie `report.jsonl` w katalogu wyjścia i **kod wyjścia wsadu 1**. Nigdy dane zmyślone ani wynik z poprzedniego przebiegu. Przełącznik `ERROR_EXPORT` (`empty_json` domyślnie, `no_file`) zostaje do czasu odpowiedzi mentora, jak ewaluator liczy brak pliku.
4. **Strona wymagająca OCR bez dostępnego OCR** → wpis `ocr_unavailable` ze stroną i lista `unprocessed` w raporcie; wynik powstaje z pozostałych stron (stan `partial`, kod wyjścia 1). Warstwa tekstu takiej strony nie trafia do modelu.
5. **Dokument niejednoznaczny** (`ambiguous`) → najlepsza klasa: jedno dodatkowe wywołanie LLM z poleceniem wyboru klasy. Jeśli model znów nie wybierze, wynik to `{}` ze stanem `ambiguous` i flagą `class_ambiguous` w raporcie (kod wyjścia 0, bo to nie awaria techniczna).
6. **Cytat, strona i kotwica bbox nie decydują o treści wyniku.** Wartość bez kotwicy zostaje w JSON. Dowody (Z09) są osobnym artefaktem poza ocenianym wynikiem.
7. **Walidacja nie blokuje eksportu.** Wartość, której nie da się znormalizować, zostaje i dostaje flagę `unnormalized:<ścieżka>`; wartość o typie niezgodnym z szablonem staje się `null` z flagą `type_mismatch:<ścieżka>`; ścieżka spoza szablonu jest odrzucana z flagą `unknown_field:<ścieżka>`. Para `czynnosc_powod_id` ↔ `czynnosc_opis` jest uzgadniana kodem ze słownikiem organizatora (`reason_text_replaced`, `reason_pair_invalid`).
8. **Serializer z szablonu klasy**: klucze i kolejność jak we wzorcach organizatora, jawne `null`, bez `prune`; pusta lista ma jeden element szkieletowy.
9. **Poprzedni plik wyniku nie jest usuwany.** Przy `empty_json` błąd zastępuje go przez `{}` (stary wynik nie może uchodzić za nowy). Przy `no_file` i przy nieudanym zapisie (`write_failed`) plik zostaje nietknięty, a raport i kod wyjścia wskazują awarię. Zapis jest atomowy.
10. **Błąd konfiguracji lub self-check LLM przed wsadem** (brak klucza w trybie nieinteraktywnym, 401/403, 429, zły adres) → komunikat i **kod wyjścia 2, bez przetwarzania wsadu** i bez plików wyniku. Odrzucenie klucza albo wyczerpanie limitu wywołań w trakcie wsadu kończy wywołania LLM: pozostałe dokumenty dostają `{}` i ten sam kod w raporcie.

### Raport `report.jsonl`

Jeden wiersz JSON na plik wejściowy, zapisywany atomowo po każdym dokumencie: `input`, `output` (lub `null`), `status` (`ok`, `foreign`, `ambiguous`, `unclassified`, `partial`, `technical_error`), `document_class`, `pages`, `unprocessed`, `errors` (`code`, `message`, `page`), `flags`, `llm` (dostawca, model, powód przełączenia, ostrzeżenia; [ADR-007](ADR-007-zapasowy-dostawca-llm.md)). Raport nie zawiera treści dokumentów, odpowiedzi modelu ani sekretów: opisy składa program, a nieoczekiwany wyjątek zostawia tylko nazwę swojej klasy.

### Kody wyjścia `process`

`0` wszystkie dokumenty bez błędu; `1` co najmniej jeden dokument ze stanem `technical_error` albo `partial`; `2` błąd użycia, konfiguracji albo self-check LLM (wsad nieprzetworzony).

## Konsekwencje

- Zmienia założenia architektury §4.5 i §10 (bbox jako warunek wartości, blokada eksportu, `ambiguous` bez eksportu): oba miejsca mają adnotację o pierwszeństwie tego ADR. Historii nie przepisujemy.
- Plik `{}` po błędzie technicznym wygląda w katalogu wyjścia jak dokument obcy. Rozróżnienie daje wyłącznie `report.jsonl` i kod wyjścia; kto ocenia wynik, musi czytać raport. Dla dokumentu trzech klas `{}` oznacza utratę wszystkich pól (FN), a nie fałszywe wartości (FP).
- `report.jsonl` leży w katalogu wyjścia obok wyników. Jeśli ewaluator organizatora liczy każdy plik `*.json`, raport go nie dotyczy (rozszerzenie `.jsonl`); pytanie o ocenę braku pliku pozostaje otwarte ([pytania otwarte](pytania-otwarte.md)).
- Dodatkowe wywołanie dla `ambiguous` nie było mierzone: w E10 model nie zwrócił `ambiguous` ani razu na 435 wierszy, więc koszt i wpływ na F1 są w praktyce zerowe, ale wymuszony wybór klasy dla dokumentu obcego może dać fałszywe pola.
- Wartości bez kotwicy i bez normalizacji trafiają do wyniku: zysk F1 z E17 kosztem tego, że wynik może zawierać wartość do sprawdzenia. Flagi w raporcie są jedynym śladem.
- Kod wyjścia 1 dla `partial` oznacza, że wsad ze skanami bez OCR kończy się błędem, mimo że pliki powstały.
