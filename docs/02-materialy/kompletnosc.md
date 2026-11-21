---
wersja: 0.4.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Kompletność pakietu UZP

| Materiał | Stan |
|---|---|
| Pełny opis i regulamin PDF | zachowane oryginały |
| FAQ v1.0, cztery części | zachowane, źródło: użytkownik |
| Repo organizatora | 385 plików z przypiętej rewizji; PDF-y, JSON-y, słownik i szablon |
| Uwagi organizatorów z Discorda | zachowany wyciąg z autorami i godzinami, w tym ostatnia korekta 13:27 |
| Prezentacja ODWOLANIA2JSON_HackNation2026.pdf | brak samego załącznika; mamy opis w wiadomości |
| ground_truth.yaml | celowo usunięty przez organizatora; nie oczekujemy go |
| Oficjalny skrypt F1 | nie został dostarczony; mamy słowne zasady i pytania otwarte |

Pakiet wystarcza do rozpoczęcia implementacji. Nie oznacza potwierdzenia posiadania każdego załącznika i pełnego kodu ewaluatora.

[Rejestr](rejestr.md), [manifest](manifest.json), [pytania](../07-decyzje/pytania-otwarte.md).

## Uzupełnienie 0.4.0 — pełny przegląd repo organizatora (2026-11-21)

Sprawdzono wszystkie gałęzie i historię `Urzad-Zamowien-Publicznych/hacknation-2026` przez API GitHub. Kopia bazowa `organizator-uzp/` (rewizja `f60ca6f`) pozostaje bez zmian. Nowsze i dodatkowe pliki zapisano osobno w [organizator-uzp-aktualizacje](organizator-uzp-aktualizacje/) z rejestrem [uzp-aktualizacje.json](uzp-aktualizacje.json): ścieżka, blob SHA-1, rozmiar i informacja, czy plik jest identyczny z kopią bazową.

| Źródło | Commit | Plików | Zapisanych osobno | Zawartość różnicy |
|---|---|---|---|---|
| `main` | `7590db8` | 385 | 6 | słownik `czynnosc_powod_id_dict.md` (formatowanie); `czynnosc_opis` w sprawach 19, 23, 25, 44, 55: „Odpowiedzi i wyjaśnienia do SWZ” → „Odpowiedzi/wyjaśnienia do SWZ” |
| gałąź `dane` | `26a3363` | 280 | 42 | starszy zbiór 39 spraw; **39 plików `dane/przyklad_XX/ground_truth.yaml`**; inne wersje `README.md` i `oczekiwane-json/odwolanie.json` |
| gałąź `mateusz-readme-changes` | `b9373d6` | 4 | 2 | starsze `README.md` i `oczekiwane-json/odwolanie.json` |

Doprecyzowanie wcześniejszych wierszy tabeli:

- `ground_truth.yaml` usunięto z `main`, ale 39 plików istnieje w gałęzi `dane` i w historii od commitu `49e7c35`. Są teraz zachowane. Organizator opisał je jako scalone pliki JSON (Discord 13:27); dotyczą starszego zbioru 39 spraw.
- Prezentacji `ODWOLANIA2JSON_HackNation2026.pdf` nie ma w żadnej gałęzi ani w historii repo organizatora. Była tylko załącznikiem Discord.
- Oficjalnego skryptu F1 ani innych plików `.py` nie ma w żadnej gałęzi ani w historii.
- Wniosek: referencją aktualną jest `main` `7590db8`. Przy ewaluacji używaj poprawionych plików z `organizator-uzp-aktualizacje/main-7590db8/` w miejsce odpowiedników z kopii bazowej.
