"""Jawne błędy techniczne przetwarzania dokumentu.

Błąd techniczny ma kod maszynowy i opis bez treści dokumentu oraz bez sekretów.
Kod trafia do raportu wsadu; nigdy nie zastępujemy go zmyślonym wynikiem.
"""

from __future__ import annotations

__all__ = ["ERROR_CODES", "ProcessingError"]

ERROR_CODES = frozenset(
    {
        "not_a_pdf",
        "pdf_corrupted",
        "pdf_encrypted",
        "empty_document",
        "page_limit",
        "pixel_limit",
        "ocr_unavailable",
        "ocr_error",
        "llm_unavailable",
        "llm_authorization",
        "llm_rate_limit",
        "llm_invalid_response",
        "llm_request_rejected",
        "llm_call_limit",
        "llm_input_limit",
        "invalid_configuration",
        "internal_error",
        "write_failed",
    }
)


class ProcessingError(Exception):
    """Błąd techniczny z kodem z :data:`ERROR_CODES`.

    `retry_after_s` niesie podpowiedź serwera (`Retry-After`), gdy była w odpowiedzi.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        page: int | None = None,
        retry_after_s: float | None = None,
    ) -> None:
        if code not in ERROR_CODES:
            raise ValueError(f"nieznany kod błędu: {code}")
        super().__init__(message)
        self.code = code
        self.message = message
        self.page = page
        self.retry_after_s = retry_after_s

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
