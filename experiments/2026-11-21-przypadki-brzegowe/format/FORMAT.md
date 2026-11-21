# Format plików przeglądu przypadków brzegowych (wersja 1)

Jeden przebieg = jeden katalog `wyniki/<przebieg>/`. Wszystkie ścieżki w plikach są **względne wobec katalogu przebiegu**, z `/` jako separatorem. Kodowanie UTF-8. Schematy JSON (draft 2020-12) leżą obok tego pliku.

```
wyniki/<przebieg>/
  manifest.json                 # manifest.schema.json   (pisze narzędzie)
  dokumenty/<id>.json           # dokument.schema.json   (pisze narzędzie)
  strony/<id>/p001.jpg ...      # obrazy stron, 100 dpi, JPEG (pisze narzędzie)
  adnotacje/<id>.json           # adnotacja.schema.json  (pisze WYŁĄCZNIE przeglądarka egui)
```

Zasady:

- Narzędzia nigdy nie nadpisują `adnotacje/`. Przeglądarka nigdy nie zmienia `manifest.json`, `dokumenty/` ani `strony/`.
- Brak pliku adnotacji = dokument nieprzejrzany.
- Przeglądarka zapisuje adnotację atomowo (plik tymczasowy + rename).
- `id` dokumentu: tylko `[a-z0-9_-]`, unikalne w przebiegu.
- Pola opcjonalne mogą mieć wartość `null`; nieznane pola należy ignorować (zgodność w przód).
- Kody problemów pochodzą z `manifest.taksonomia`. Kod spoza taksonomii wyświetlać jako tekst, nie odrzucać.
- Numery stron są liczone od 1.
- `modele.<id>.wynik` ma kształt `wynik_modelu.schema.json` (ten sam schemat dostają modele jako wymagany format odpowiedzi).

## Karty dokumentów

`karty/<id>.json` odpowiada schematowi `karta.schema.json` (draft 2020-12).
`karty/podsumowanie.json` agreguje wyłącznie 180 kart pozytywnych PDF-ów.
Kody pochodzą z `docs/05-weryfikacja/przypadki-brzegowe.json`; nieznany kod
powoduje błąd generowania i walidacji. Po zmianie kanonicznej listy należy
zaktualizować enum schematu (test wykrywa rozbieżność).

Ścieżki PDF i referencji są względne wobec repo. Strony od 1, bbox w punktach
PDF z początkiem w lewym górnym rogu. `pola` jest mapą ścieżek referencji.
`grupy[].obszary` zawiera ramki na stronach; `spojna` oznacza brak kolizji
z polami innych grup i co najmniej jeden obszar. Kompletność podano osobno.
Karta nie korzysta z innych dokumentów tej samej sprawy. Opis ograniczeń
i odtworzenia: `docs/05-weryfikacja/karty-dokumentow-2026-11-21.md`.
