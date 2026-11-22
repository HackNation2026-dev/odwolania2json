# Blokery i defekty uprzęży (grupa D)

**Blokad eksperymentów nie było:** E12–E16 wykonano, a uprzęży (`harness/`) nie zmieniano. Poniżej defekty i niezgodności uprzęży znalezione po drodze; obejścia są w `atak/` (kopia/adapter), nie w `harness/`.

| # | Defekt uprzęży | Skutek | Obejście w `atak/` |
|---|---|---|---|
| 1 | `harness/run_experiment.py` (komentarz przy `leaf_counts` i `aggregates.leaf_f1`) twierdzi, że ewaluator produkcyjny nie zlicza `tp`; po PR #8/#9 jest to nieaktualne (`tp` jest zliczane) | mylący opis; miara liści jest zbędna do porównań | `lib.eval_counts` używa `odwolania2json.evaluator.compare_document`, miara liści zapisana obok; różnice w `E16` (DT04) |
| 2 | `GET /system` zwraca `config.work_dir` (ścieżka hosta) | ujawnienie ścieżki (E12 P04) | brak: opis w E12 |
| 3 | Trasa `/documents/{id}/artifact/{name:path}` rzuca nieobsłużony `ValueError` dla `%00` w ścieżce (500/zerwane połączenie) | E12 P01 | testy łapią wyjątek klienta |
| 4 | Normalizator kwoty zamienia 2 MB cyfr na `inf`; `result.json` zapisany z `Infinity`, `GET /result` zwraca 500 | E13 M06 | test odczytuje status zamiast zakładać JSON |
| 5 | Stan wsadów tylko w pamięci procesu (brak odtworzenia po restarcie) | E15 W03 | opis w E15 |
| 6 | `ManagedServer`/`AttackServer`: `prlimit`/`systemd-run` działają (metoda `systemd-run`); `ulimit -v` nie nadaje się do pdfium/Pythona (sam start interpretera pada przy 3 GB przestrzeni adresowej), więc izolację parsera w produkcie trzeba robić cgroupem lub `RLIMIT_AS` ≥ kilka GB z testem startowym | próba odtworzenia B08 pod `ulimit -v` bez wyniku | opis w E12 |
