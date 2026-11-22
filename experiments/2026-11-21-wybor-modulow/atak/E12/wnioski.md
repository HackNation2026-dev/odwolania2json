## Wniosek decyzyjny wobec kryterium z planu

Kryterium *„zawsze jawny `technical_error`, serwer żyje”* jest **niespełnione dla uprzęży**: 1 z 11 bomb PDF (B08, samoodwołujący się XObject) zabija proces serwera i cały wsad, dwie kolejne (B02: 5,2 GB; B03: 4,6 GB przy limicie 6 GB) przeżywają tylko dzięki rozmiarowi ładunku. Pozostałe wejścia (nazwy, typ, uszkodzone, zaszyfrowane, 0 stron, cykliczne, 50 000 stron) kończą się kodem i serwer żyje.

Decyzje przenoszone do produktu (od najważniejszej):

1. **Izolacja parsowania w procesie potomnym** z limitem pamięci (`RLIMIT_AS` lub cgroup) i twardym czasem z `kill` (B02, B03, B08). To jedyna obrona przed bombą, której nie przewidziano limitem; limity bajtów po dekompresji i pikseli to uzupełnienie.
2. **Limit ciała żądania na wejściu** (przerwanie po przekroczeniu, `Content-Length` > limit → 413) zamiast czytania do końca (F01).
3. **Walidacja Host/Origin** i nagłówek niestandardowy dla POST (P05; formularz z obcej strony tworzy wsad).
4. **Obsługa NUL i innych wyjątków** w trasach bez globalnego handlera 500 z kodem API (P01), nazwy plików odrzucane jawnie (N01–N11), `/system` bez ścieżek hosta (P04).

**Pewność:** wysoka dla wyników jakościowych (powtarzalne, deterministyczne PDF-y); średnia dla wielkości pamięci (zależne od wersji pdfium). **Otwarte:** mechanizm B08 w pdfium; zachowanie przy limicie 14 GB (przewidywane: to samo, wolniej); JBIG2/JPX; DNS-owy monitor SSRF; testy uruchomione na produktowym backendzie, gdy powstanie.
