# E00: wyniki surowe i sposób pomiaru

E00 to test dymny samej uprzęży, nie eksperyment z planu: kilka dokumentów zbioru rozwojowego przez HTTP z odczytem pypdfium2, routerem i ekstraktorem regułowym, bez OCR. Sprawdza, że przepływ health, upload, wynik działa end-to-end i że pomiar czasu oraz RSS się zapisuje.

## Jak to działa i dlaczego

Każdy plik `<wariant>.json` to jeden przebieg `python harness/run_experiment.py <konfiguracja>`: harness startuje backend
eksperymentalny jako podproces pod limitem pamięci 14 GB, wgrywa dokumenty przez HTTP (`POST /batches`), czeka na stan
`done` i czyta wynik, dowody, raport i diagnozę. Mierzymy po stronie klienta czas ścienny, a po stronie procesu serwera
szczytowy RSS (VmHWM). Pomiar czasu biegnie pod `flock /tmp/uzp-cpu.lock`, żeby równoległe zadania nie zniekształcały wyniku.
Dlaczego HTTP: tak będzie używał backendu klient i GUI, więc mierzymy też narzut przyjęcia, kolejki i zapisu.
Plik wariantu zawiera konfigurację, wersje pakietów, ziarno, metodę limitu pamięci i surowe rekordy dokumentów;
liczby w tabeli poniżej są tylko streszczeniem (F1 liści: miara pomocnicza do porównań wariantów, nie wynik oficjalny; surowe liczniki są w `aggregates.leaf_f1`).

| plik | zbiór | dok. | wyniki | śr. s/dok. | szczyt RSS MB | F1 liści (suma) | limit pamięci |
|---|---|---|---|---|---|---|---|
| `pdfium-rules-bez-ocr.json` | cases-dev | 4 | {'complete': 4} | 0.1396 | 72.6 | 0.1967 | systemd-run |
| `szablon-skan-rapidocr.json` | template | 2 | {'foreign': 1, 'partial': 1} | 11.8466 | 991.8 | 0.0 | systemd-run |
