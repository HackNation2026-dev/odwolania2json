# Historia zmian

## 0.4.0 — 2026-11-21

- Odnotowano zmianę widoczności repo na publiczną przez użytkownika; skrypt publikacji prywatnej nie jest używany dla tego wydania.
- Dodano `docs/04-architektura/proponowany-stos.md` ze statusem PROPONOWANY (nie decyzja): Python 3.13, pip + CLI, hybryda reguł i LLM po API w UE, GUI PDF|JSON wcześnie.
- Addytywnie dodano późniejsze rewizje organizatora: `main` `7590db8` (poprawki `czynnosc_opis` w 5 sprawach, słownik), gałąź `dane` `26a3363` z 39 plikami `ground_truth.yaml` i gałąź `mateusz-readme-changes`. Kopia bazowa `f60ca6f` bez zmian; rejestr `uzp-aktualizacje.json`, manifest +50 plików.
- `verify_docs.py` dodatkowo sprawdza blob SHA-1 i komplet aktualizacji.
- Uzupełniono kompletność (brak prezentacji PDF i skryptu F1 potwierdzony w całej historii repo organizatora), rozbieżności, punktację GUI z cytatami i uwagę do rekomendacji Fable.
- Przywrócono jako sekcje historyczne treść nadpisaną w 0.3.0 (zlecenie i status konsultacji, status publikacji).
- Zmiany wyłącznie addytywne.

## 0.3.0 — 2026-11-21

- Opublikowano prywatne repo `HackNation2026-dev/odwolania2json` (organizację utworzył użytkownik ręcznie); potwierdzono prywatność, SHA i drzewo.
- Dodano wynik niezależnej konsultacji Fable (`claude-fable-5-2`, bezpośrednie CLI): surowa odpowiedź, zlecenie i metadane.
- Rekomendacja Fable dla UZP: czysty Python 3.13 (pip, CLI), hybryda reguł i małego LLM po API w UE, `pypdfium2` + `rapidocr`, GUI na końcu, bez Rusta. To nie jest decyzja zespołu; ADR-001 pozostaje propozycją.
- Materiały organizatora bez zmian.

## 0.2.1 — 2026-11-21

- Potwierdzono działające CLI Claude i alias modelu fable w pomocy.
- Konsultację i publikację odłożono na prośbę użytkownika do nowej sesji.
- Bezpośrednią próbę konsultacji przerwano bez uzyskania opinii.

## 0.2.0 — 2026-11-21

- Dodano źródło Discord z godzinami i autorami przekazanymi przez użytkownika.
- Uwzględniono 60 spraw, usunięcie ground_truth.yaml i syntetyczny zbiór testowy.
- Doprecyzowano darmowe/płatne/własne API, publiczny endpoint i brak instalacji modelu u jury.
- Dodano zasady F1: 80% dla wskazanych tekstów i listy dopasowywane po treści.
- Korekta 13:27: obcy dokument daje pusty JSON pod oryginalną nazwą.
- Zachowano nierozstrzygnięte szczegóły ewaluacji i oryginalne FAQ v1.0.
- Dodano wykaz kompletności i zlecenie Fable ze statusem niewykonane.
- Publikacja dopuszcza bezpieczne aktualizacje fast-forward.

## 0.1.1 — 2026-11-21

- Zmieniono organizację docelową na `HackNation2026-dev` zgodnie z poleceniem użytkownika.
- Dodano porównanie pełnej aplikacji: CLI/API, Python/Rust, React/TypeScript i egui.
- Konsultacja Fable nie została wykonana; propozycja stosu jest oceną autora.
- Publikacja nadal wymaga działającego dostępu do GitHub. Materiały organizatorów pozostają bez zmian.

## 0.1.0 — 2026-11-21

- Utworzono wersjonowaną dokumentację w podziale na osiem obszarów.
- Dodano oryginalne opisy, regulaminy i dostępne materiały organizatora.
- Rozdzielono wymagania, propozycję stosu, testy, prezentację i pytania.
- Dodano rejestr źródeł, sumy kontrolne i kontrolę odnośników.
- Nie zaimplementowano jeszcze aplikacji konkursowej.
