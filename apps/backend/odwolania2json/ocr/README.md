# Moduł OCR (`odwolania2json.ocr`)

Adapter OCR stron skanowych za protokołem `OcrProvider`. Dostawca domyślny: `RapidOcr`
(`rapidocr` + `onnxruntime`, CPU, wagi w kole pip). `UnavailableOcr` zgłasza jawny błąd
`ocr_unavailable`.

## Interfejs

```python
from odwolania2json.ocr import RapidOcr

result = RapidOcr().recognize(image)  # image: PIL.Image strony
page = result.to_page_points(width_pt, height_pt)
for line in page.lines:
    line.text, line.confidence, line.bbox  # bbox = (x0, y0, x1, y1), oś Y w dół
    for word in line.words:
        word.text, word.confidence, word.bbox
```

- `recognize(image) -> OcrResult` zwraca linie ze słowami i bbox **w pikselach obrazu wejściowego**
  (także gdy adapter obrócił obraz przed odczytem: współrzędne wracają do układu wejścia).
- `OcrResult.to_page_points(width_pt, height_pt)` przelicza piksele na punkty strony (osobna skala
  w poziomie i w pionie) i przycina do obrysu strony; słowa i linie bez dodatniego pola są pomijane.
- `OcrResult.words` to płaska lista słów; `OcrResult.rotation` to kąt (0/90/180/270, jak
  `PIL.Image.rotate`), o który obrócono obraz.
- Linia może nie mieć słów (silnik ich nie podał); wtedy `text` jest dostępny, a `words` puste.

Dopasowanie do protokołu `PageOcr` z `extract/ports.py` (jeśli się różni) to zadanie czytnika:
adapter celowo nie zna typów czytnika PDF.

## Ustalenia z eksperymentów

| Decyzja | Dowód |
|---|---|
| Limit dłuższego boku w pikselach (`max_side`, domyślnie 2000), nie w dpi | E02: 200 i 300 dpi dają ten sam wynik przy `max_side_len=2000` |
| Wykrywanie obrotu 90/180/270, bez prostowania skosu i bez binaryzacji | E03: +0,46 i +0,30 odnajdywalności na stronach obróconych; deskew −0,011, binaryzacja −0,033 |
| Jawna liczba wątków onnxruntime (`threads`, domyślnie 4) | E-T1: największy skok czasu przy 1→4 wątkach |

Drugi kandydat orientacji musi mieć wynik wyższy o co najmniej 10% niż pierwszy
(`_ROTATION_MARGIN`): klasyfikator linii w silniku czyta tekst obrócony o 180° prawie równie
dobrze, więc bez marginesu prosta strona dostawała obrót 180° z powodu szumu (wykryte testem z
prawdziwym silnikiem na obrazie wygenerowanym w teście).

## Błędy

- brak pakietu, wag albo błąd startu silnika: `ProcessingError("ocr_unavailable")`;
- błąd w trakcie rozpoznawania: `ProcessingError("ocr_error")`;
- komunikaty niosą tylko nazwę klasy wyjątku, nigdy treść dokumentu ani ścieżki.

## Testy

`tests/unit/test_ocr_rapid.py`: atrapa silnika bez wag. Testy z prawdziwym silnikiem mają znacznik
`slow_ocr` i są pomijane, gdy brak `rapidocr` (w `.venv-exp` działają:
`.venv-exp/bin/python -m pytest tests/unit/test_ocr_rapid.py -m slow_ocr`).
