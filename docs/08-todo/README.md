---
wersja: 0.1.0
aktualizacja: 2026-11-22
status: materiały TODO: plan i kontekst dla agentów; stan faktyczny ustal w kodzie i testach
---

# TODO: plan i kontekst

Zacznij tutaj. Katalog zbiera wszystko, co agent musi wiedzieć, żeby bez dopytywania kontynuować prace.

| Plik | Po co |
|---|---|
| [03-stan-na-dzis.md](03-stan-na-dzis.md) | rzetelny stan na koniec etapu: co sprawdzone osobiście, co z raportów, co w toku, czego nie mamy |
| [01-plan-naprawczy.md](01-plan-naprawczy.md) | co zrobić, w jakiej kolejności, z bramkami akceptacji i zależnościami |
| [02-kontekst.md](02-kontekst.md) | stan na dziś, ustalenia z eksperymentów, fakty o dostawcach LLM, środowisko, zasady pracy, pułapki, otwarte decyzje |
| [zadania dla agentów](../00-organizacja/zadania-dla-agentow.md) | szczegółowe instrukcje krok po kroku (Z01–Z15): cel, pliki, kroki, testy, kryteria |
| [raport eksperymentów](../../experiments/2026-11-21-wybor-modulow/RAPORT.md) | wyniki E00–E20 z liczbami |
| [ocena architektury (Fable)](../../experiments/2026-11-21-wybor-modulow/recenzje/fable-ocena-architektury.md) | macierz 27 warunków zadania, ocena etapów |
| [backlog](../00-organizacja/backlog.md) | znane długi i definicja ukończenia |

Zasada nadrzędna: **produkt (`python -m odwolania2json process input output`) ma działać na dokumentach organizatora**, a każda liczba skuteczności ma pochodzić z produktu, nie z uprzęży w `experiments/`.
