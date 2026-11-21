---
wersja: 0.5.0
aktualizacja: 2026-11-21
status: wynik eksperymentu, przed przeglądem przez człowieka
---

# Eksperyment: typy plików i przypadki brzegowe UZP

Zlecenie użytkownika: przejrzeć pliki UZP (tekst, skany, przypadki brzegowe) i sprawdzić, czy MiniMax (flash), Codex i Claude już teraz wykrywają przypadki brzegowe. Wyniki w plikach dla przeglądarki egui, w której człowiek opisuje problemy. Kod i dane: [`experiments/2026-11-21-przypadki-brzegowe/`](../../experiments/2026-11-21-przypadki-brzegowe/). Format plików: `format/FORMAT.md` i schematy JSON. Przeglądarka: `przegladarka/README.md`.

## 1. Inwentarz plików (bez modeli, poppler)

206 dokumentów, 586 stron (`wyniki/2026-11-21-v1/manifest.json`).

| Grupa | Dokumentów | Typ | Uwagi |
|---|---|---|---|
| Pozytywne (60 spraw × 3) | 180 | wszystkie tekstowe | jeden generator „LAPFormalDoc”; odwołania 2, 3, 10 lub 11 stron; pełnomocnictwa 1 (jedno 2) strony; przelewy 1 strona; co najmniej dwa układy bankowe przelewów |
| Negatywne | 12 | 8 tekst, 3 skany, 1 mieszany | trudne negatywy: wyrok KIO, ogłoszenia BZP/TED; skany z kserokopiarki |
| Szablon organizatora | 2 | `przyklad odwolanie.pdf` to 7-stronicowy skan | jedyny skan dokumentu pozytywnego |
| Syntetyczne (nasze) | 12 | skany i mieszane | patrz pkt 2 |

**Ustalenia:**

- Żaden z 180 przykładów pozytywnych nie jest skanem ani dokumentem mieszanym, a test je zawiera (mentor). Do testowania OCR potrzebujemy własnych syntetycznych skanów i dokumentów mieszanych.
- Przelewy dotyczą w większości **opłaty skarbowej od pełnomocnictwa** (kwoty 17–200 zł), nie tylko wpisu od odwołania.
- Przypadki wykryte automatycznie: skan z szablonu ma stronę 1240×1754 pt (piksele zapisane jako punkty, ok. 2× A4); pismo Ministra Sprawiedliwości ma obrót `/Rotate 270` w samym PDF; negatywy z prezentacji są poziome; ogłoszenie OJS występuje trzy razy (w tym jako „negatywny przykład” w szablonie).

## 2. Syntetyczne przypadki brzegowe

12 plików z dokumentów pozytywnych spraw przyklad_01, 02 i 40 (`narzedzia/syntetyczne.py`, znane problemy w `syntetyczne/syntetyczne.json`): obrót 90° i 180°, przekrzywienie 3°, 72 dpi z rozmyciem i JPEG q25, „ksero” (szare tło, szum, −1,5°), dokument mieszany (strona tekstowa + skan), dwa dokumenty w jednym pliku, pieczątka i podpis na treści, ucięty prawy margines, wstawiona pusta strona, strona mieszana (tekst + wklejony obraz), dokument mieszany z obróconym skanem.

## 3. Modele

Próbka: 41 dokumentów (wszystkie negatywy, szablon, syntetyczne, 5 spraw pozytywnych × 3). Każdy model dostał te same obrazy pierwszych ≤3 stron (100 dpi JPEG), to samo polecenie i ten sam schemat wyniku (`format/wynik_modelu.schema.json`).

| Model | Wywołanie |
|---|---|
| Codex | `codex exec`, gpt-6.1-sol, `--output-schema`, tryb tylko do odczytu |
| Claude | `claude -p`, model domyślny CLI, `--json-schema`, obrazy przez narzędzie Read |
| MiniMax | `MiniMax-M3.1-Flash-Preview`, API zgodne z Anthropic, `effort: medium` (myślenia nie da się wyłączyć; przy domyślnym `max` pierwsze wywołanie trwało 288 s i nie zwróciło JSON) |

MiniMax działa z serwerów `api.minimax.io` — tylko na potrzeby eksperymentu; nie spełnia wymogu hostingu w Europie bez weryfikacji dostawcy.

**Błąd w pierwszym poleceniu:** klasę „przelew” zdefiniowałem jako „wpis od odwołania”. Codex trzymał się tej definicji i odrzucał przelewy opłaty skarbowej. Wyniki z tym poleceniem są w `_surowe_polecenie1/`; poniżej wyniki po poprawce (polecenie v2: „potwierdzenie przelewu bankowego związanego ze sprawą”).

| Miara (polecenie v2) | Codex | Claude | MiniMax |
|---|---|---|---|
| Odpowiedzi zgodne ze schematem | 41/41 | 41/41 | 39/41 |
| Średni czas na dokument [s] | 16,4 | 16,4 | 12,4 |
| Trafność klasy | 0,976 | 0,976 | 1,0 |
| Średnie podobieństwo transkrypcji początku strony | 0,971 | 0,973 | 0,966 |
| Wykryte wstrzyknięte problemy | 23/23 | 23/23 | 19/22 (x10 bez poprawnej odpowiedzi) |

- Codex i Claude jedyną „pomyłkę” klasy mają przy dwóch dokumentach w jednym pliku: odpowiedzieli „niepewne” i opisali oba dokumenty. To zachowanie pożądane, nie błąd.
- MiniMax nie rozpoznał skanu i przekrzywienia w dwóch syntetycznych skanach (x02, x03) i w 2/41 przypadków dopisał nieistniejące pola (`uzasadnij`, `uzasadnieniu_klasy`); w pierwszym przebiegu dwa razy odesłał sam schemat zamiast odpowiedzi. Bez wymuszonego schematu jego wyniki wymagają walidacji i ponowienia.
- Wszystkie trzy modele rozpoznały obroty, pieczątki, ucięty tekst, stronę mieszaną i dwa dokumenty w jednym pliku.

**Ograniczenia oceny:** próbka syntetyczna jest mała (12 plików, 23 problemy); dopasowanie wykrycia jest liberalne (np. „skan” uznany, gdy model określił typ strony jako skan); podobieństwo transkrypcji to `partial_ratio` pierwszych ~200 znaków; problemy zgłoszone przez modele w dokumentach prawdziwych nie mają jeszcze wzorca — ocenia je człowiek w przeglądarce. Wyniki dotyczą modeli dostępnych w eksperymencie, nie docelowego modelu hostowanego w Europie.

## 4. Dalsze kroki

1. Przegląd w przeglądarce egui: adnotacje w `wyniki/2026-11-21-v1/adnotacje/`, eksport `adnotacje_zbiorcze.csv`.
2. Na podstawie adnotacji: lista przypadków brzegowych do obsługi w odczycie PDF/OCR (decyzje ad 3 i 4) i w klasyfikacji (ad 5).
3. Syntetyczne skany włączyć do ewaluatora F1 jako zestaw „skany i mieszane”.

## Odtworzenie

```
cd experiments/2026-11-21-przypadki-brzegowe/narzedzia
python syntetyczne.py && python inwentarz.py        # PDF-y syntetyczne, obrazy stron, manifest
python modele.py codex|claude|minimax               # surowe wyniki w wyniki/<przebieg>/_surowe/
python scal.py                                       # scalenie + podsumowanie.md
```

Wymaga Python 3.13 z `pypdf pillow numpy rapidfuzz jsonschema`, poppler-utils, CLI `codex` i `claude`, klucza MiniMax w pliku (`MINIMAX_KEY_FILE`). Obrazy stron i PDF-y syntetyczne nie są w Git (`.gitignore`), bo skrypty je odtwarzają.
