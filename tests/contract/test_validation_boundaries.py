"""Przykłady graniczne walidatora pochodzą z kontraktu, nie z kodu modeli."""

import json
from pathlib import Path

import pytest
import yaml
from odwolania2json_contracts import models
from pydantic import ValidationError

SPEC = yaml.safe_load((Path(models.__file__).parent / "openapi.yaml").read_text(encoding="utf-8"))[
    "components"
]["schemas"]


def example(schema):
    if "$ref" in schema:
        return example(SPEC[schema["$ref"].split("/")[-1]])
    if "anyOf" in schema:
        return example(next(part for part in schema["anyOf"] if part.get("type") != "null"))
    kind = schema.get("type")
    if isinstance(kind, list):
        kind = next(value for value in kind if value != "null")
    if kind == "object":
        return {key: example(value) for key, value in schema.get("properties", {}).items()}
    if kind == "array":
        return [example(schema["items"])]
    if "enum" in schema:
        return schema["enum"][0]
    if kind == "string":
        return "2026-11-21" if "pattern" in schema else "0000012345"
    if kind in {"number", "integer"}:
        return schema.get("minimum", 1)
    return None


@pytest.mark.parametrize("name", sorted(SPEC))
def test_each_result_object_keeps_string_values_and_rejects_extra_fields(name):
    schema = SPEC[name]
    model = getattr(models, name, None)
    if model is None:
        pytest.fail(f"Brak modelu kontraktu: {name}")
    data = example(schema)
    if not isinstance(data, dict):
        pytest.fail(f"Oczekiwano schematu obiektu: {name}")
    validated = model.model_validate(data)
    assert validated.model_dump(by_alias=True) == data
    with pytest.raises(ValidationError):
        model.model_validate({**data, "unknown_field": "unexpected"})


def test_result_reason_range_and_all_labels():
    schema = SPEC["OdwolanieKIO"]
    data = example(schema)
    for reason in (0, 13):
        with pytest.raises(ValidationError):
            models.OdwolanieKIO.model_validate({**data, "czynnosc_powod_id": reason})
    for label in schema["properties"]["czynnosc_opis"]["enum"]:
        assert (
            models.OdwolanieKIO.model_validate({**data, "czynnosc_opis": label}).czynnosc_opis
            == label
        )


def test_zero_representative_flag_and_text_pesel_roundtrip():
    representative = example(SPEC["Odwolujacy"])
    representative["przez-pelnomocnika"] = 0
    assert models.Odwolujacy.model_validate(representative).przez_pelnomocnika == 0
    person = example(SPEC["PelnomocnikPelnomocnictwa"])
    person["pesel"] = "00012345678"
    assert (
        json.loads(models.PelnomocnikPelnomocnictwa.model_validate(person).model_dump_json())[
            "pesel"
        ]
        == "00012345678"
    )
