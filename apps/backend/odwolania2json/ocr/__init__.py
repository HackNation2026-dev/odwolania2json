"""OCR stron skanowych za wymiennym protokołem `OcrProvider`."""

from odwolania2json.ocr.rapid import (
    OcrLine,
    OcrProvider,
    OcrResult,
    OcrWord,
    RapidOcr,
    UnavailableOcr,
)

__all__ = ["OcrLine", "OcrProvider", "OcrResult", "OcrWord", "RapidOcr", "UnavailableOcr"]
