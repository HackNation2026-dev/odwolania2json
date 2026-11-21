# Przeglądarka przypadków brzegowych

Desktopowa aplikacja (Rust, eframe/egui) do ręcznego przeglądu przebiegu
z eksperymentu „przypadki brzegowe” (Odwołania2JSON). Pokazuje obrazy stron,
metryki automatyczne i odpowiedzi modeli, a recenzent zapisuje w niej swoje
adnotacje. Format plików opisuje `../format/FORMAT.md`.

## Uruchomienie

```bash
cd przegladarka
cargo run --release -- ../wyniki/<przebieg>      # konkretny przebieg
cargo run --release                               # najnowszy ../wyniki/*/ z manifest.json
cargo run --release -- fixtures/przebieg-demo     # mały przebieg testowy
```

Bez argumentu aplikacja bierze podkatalog `../wyniki/*/` z najnowszym
`manifest.json`. Jeśli go nie znajdzie, pokazuje pole na ścieżkę.
Przebieg można też zmienić w trakcie pracy przyciskiem „Zmień przebieg…”.

## Układ

- **Lewy panel**: lista dokumentów z kolorowym znacznikiem statusu
  (szary: nieprzejrzany, pomarańczowy: w_toku, zielony: przejrzany,
  fioletowy: do_dyskusji, czerwony: nieczytelny plik adnotacji), klasą
  oczekiwaną, typem, liczbą stron i flagą ⚠ rozbieżności (modele wskazały
  różne klasy albo klasę inną niż oczekiwana; „inny” modelu = „obcy”).
  Filtry: źródło, status, tylko przesłane do modeli, tylko z rozbieżnością,
  szukanie po id.
- **Środek**: obraz strony, nawigacja stron, zoom (Dopasuj / 100% / − / +), przewijanie.
- **Prawy panel**, trzy zakładki:
  - **Strona**: metryki automatyczne strony i metadane dokumentu.
  - **Modele**: dla każdego modelu status, czas, klasa (✓/✗ względem oczekiwanej),
    opis bieżącej strony (typ, obrót, jakość, transkrypcja i podobieństwo do
    `probka_tekstu`) oraz problemy strony i dokumentu. Dla dokumentów
    syntetycznych tabela wstrzykniętych problemów: wykryte/pominięte przez każdy model.
  - **Adnotacja**: recenzent, status, klasa według człowieka, problemy dokumentu
    i bieżącej strony (kod z taksonomii, waga, opis), notatki, ocena modeli,
    przyciski „Przejmij problemy z modelu X”.
- **Podsumowanie** (górne menu albo F4): trafność klas i średnie podobieństwo
  transkrypcji dla każdego modelu, wykrycia wstrzykniętych problemów według
  kodu, liczba dokumentów w każdym statusie, kody nadane przez ludzi,
  przycisk „Eksport CSV”.

## Skróty klawiszowe

| Klawisz | Działanie |
|---|---|
| ← / → | poprzednia / następna strona |
| ↑ / ↓, PageUp / PageDown | poprzedni / następny dokument (w obrębie filtrów) |
| + / − | powiększ / pomniejsz |
| F1 / F2 / F3 | zakładka Strona / Modele / Adnotacja |
| F4 | przełącz Przegląd ↔ Podsumowanie |
| Ctrl+S | zapisz adnotację bieżącego dokumentu |

Strzałki i +/− nie działają, gdy kursor stoi w polu tekstowym.

## Gdzie zapisują się adnotacje

- `<katalog_przebiegu>/adnotacje/<id>.json`, zgodnie z `format/adnotacja.schema.json`.
  Zapis jest atomowy: plik tymczasowy w tym samym katalogu, potem `rename`.
- Adnotacja zapisuje się po kliknięciu „Zapisz”, po Ctrl+S, przy przejściu do
  innego dokumentu, przy zamknięciu okna i co około 30 s (autozapis eframe),
  jeśli są niezapisane zmiany. Niezapisane zmiany oznacza znak ● przy zakładce,
  na liście i w górnym pasku.
- Przy zapisie ustawiane są `zmieniono` (czas lokalny z przesunięciem),
  `wersja: 1` i `recenzent`. Puste wpisy stron są usuwane, a brakujące oceny
  modeli dostają wartość `brak_oceny`. Nieznane pola w istniejącym pliku
  zostają zachowane.
- Pierwsza edycja dokumentu „nieprzejrzany” zmienia jego status na „w_toku”.
- Jeśli pliku adnotacji nie da się odczytać, edycja tego dokumentu jest
  wyłączona i plik nie zostanie nadpisany.
- Nazwa recenzenta jest pamiętana między uruchomieniami (persystencja eframe
  w katalogu danych użytkownika, nie w przebiegu).
- „Eksport CSV” zapisuje `<katalog_przebiegu>/adnotacje_zbiorcze.csv`, jeden
  wiersz na problem: `id,strona,kod,waga,opis,recenzent,status`. Kolumna
  `strona` jest pusta dla problemów dokumentu. Przed eksportem zapisywane są
  niezapisane adnotacje.

Aplikacja nigdy nie zmienia `manifest.json`, `dokumenty/` ani `strony/`.

## Rozwój

```bash
cargo test                       # testy (wczytanie fixture, roundtrip, zapis atomowy, tolerancja pól)
cargo clippy -- -D warnings
cargo run --example generuj_fixture   # odtwarza obrazy w fixtures/przebieg-demo/strony/
```

Moduły: `model.rs` (typy serde), `dane.rs` (wczytywanie, zapis, CSV),
`podsumowanie.rs` (statystyki), `obrazy.rs` (leniwe ładowanie JPEG z małym
LRU), `ui/` (interfejs).
