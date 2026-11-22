"""Schemat odpowiedzi LLM: klasa dokumentu i lista pól z cytatami.

Odpowiedź modelu jest granicą systemu, więc przechodzi przez pydantic. Schemat
jest taki jak w E10: wymagana klasa ze słownika i lista pól, gdzie każde pole ma
ścieżkę (`field`) i wartość (`value`). Cytat i strona są pomocnicze: błędny typ
tych dwóch pól nie unieważnia odpowiedzi (stają się `None`), bo nie decydują
o treści wyniku (ADR-006).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from odwolania2json.errors import ProcessingError

from .prompt import TARGET_LABELS

__all__ = ["AnswerField", "AnswerLabel", "LlmAnswer", "parse_answer"]

AnswerLabel = Literal["appeal", "power_of_attorney", "bank_transfer", "foreign", "ambiguous"]

# Kody naruszeń trafiają do raportu zamiast treści odpowiedzi modelu.
_CLASS_VIOLATION = "class_out_of_vocabulary"
_FIELDS_VIOLATION = "fields_not_list"
_ITEM_VIOLATION = "field_item_invalid"


class AnswerField(BaseModel):
    """Jedno pole z odpowiedzi: ścieżka JSON Pointer, wartość, cytat i strona."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    field: str
    # Wartość jest wymagana (także jawne `null`); typ rozstrzyga normalizacja i serializer.
    value: object
    quote: str | None = None
    page: int | None = None

    @field_validator("field", mode="before")
    @classmethod
    def _field_is_text(cls, value: object) -> object:
        if not isinstance(value, str):
            raise ValueError(_ITEM_VIOLATION)
        return value

    @field_validator("quote", mode="before")
    @classmethod
    def _quote_or_none(cls, value: object) -> str | None:
        return value if isinstance(value, str) else None

    @field_validator("page", mode="before")
    @classmethod
    def _page_or_none(cls, value: object) -> int | None:
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return value


class LlmAnswer(BaseModel):
    """Cała odpowiedź modelu dla jednego dokumentu."""

    model_config = ConfigDict(extra="ignore", frozen=True, populate_by_name=True)

    label: AnswerLabel = Field(alias="class")
    fields: tuple[AnswerField, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _fields_required_for_target_class(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        fields = data.get("fields")
        if fields is None:
            if data.get("class") in TARGET_LABELS:
                raise ValueError(_FIELDS_VIOLATION)
            # Klasy `foreign` i `ambiguous` nie mają pól; brak listy to pusta lista.
            return {**data, "fields": []}
        return data

    @field_validator("fields", mode="before")
    @classmethod
    def _fields_is_list(cls, value: object) -> object:
        if not isinstance(value, list):
            raise ValueError(_FIELDS_VIOLATION)
        return value


def _violation(error: ValidationError) -> str:
    first = error.errors()[0]
    location = first["loc"]
    if location and location[0] == "class":
        return _CLASS_VIOLATION
    if len(location) > 1:
        return _ITEM_VIOLATION
    return _FIELDS_VIOLATION


def parse_answer(data: dict[str, object]) -> LlmAnswer:
    """Odpowiedź sprawdzona względem schematu; naruszenie to `llm_invalid_response`.

    Komunikat błędu niesie tylko kod naruszenia: treść odpowiedzi modelu pochodzi
    z dokumentu i nie może trafić do raportu ani logów.
    """
    try:
        return LlmAnswer.model_validate(data)
    except ValidationError as error:
        raise ProcessingError(
            "llm_invalid_response", f"odpowiedź modelu poza schematem: {_violation(error)}"
        ) from None
