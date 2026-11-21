"""Test kontraktu OpenAPI i generowanych modeli pydantic.

Kontraktem jest ``packages/contracts/odwolania2json_contracts/openapi.yaml``
(jedyna kopia, wewnątrz pakietu); modele w ``models.py`` są z niego generowane
skryptem ``scripts/generate_contracts.py``.
"""

from __future__ import annotations

import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

import odwolania2json_contracts
import yaml
from odwolania2json_contracts import models
from odwolania2json_contracts.models import Odwolanie, Pelnomocnictwo, Przelew, PustyWynik
from openapi_spec_validator import validate

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "packages" / "contracts" / "odwolania2json_contracts"
SPEC_PATH = PACKAGE_DIR / "openapi.yaml"
MODELS_PATH = PACKAGE_DIR / "models.py"
GENERATE_SCRIPT = REPO_ROOT / "scripts" / "generate_contracts.py"
PATTERN_DIR = REPO_ROOT / "docs" / "02-materialy" / "organizator-uzp" / "oczekiwane-json"
EXAMPLES_DIR = REPO_ROOT / "docs" / "02-materialy" / "organizator-uzp" / "dane"

EXPECTED_MODEL_NAMES = {
    "Odwolanie",
    "OdwolanieKIO",
    "Odwolujacy",
    "PelnomocnikOdwolania",
    "Zamawiajacy",
    "ZamowieniePubliczne",
    "Pelnomocnictwo",
    "Mocodawca",
    "MocodawcaDane",
    "Podpisujacy",
    "PelnomocnikPelnomocnictwa",
    "Przelew",
    "PrzelewBankowy",
    "PustyWynik",
}

DOCUMENT_MODELS = {
    "odwolanie.json": Odwolanie,
    "pelnomocnictwo.json": Pelnomocnictwo,
    "przelew.json": Przelew,
}


def _load_spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def _strip_json_comments(text: str) -> str:
    """Usuwa komentarze ``//`` spoza ciągów znaków (wzorce organizatora nie są JSON-em)."""
    out: list[str] = []
    in_string = False
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
            out.append(char)
        elif char == "/" and text.startswith("//", index):
            while index < len(text) and text[index] != "\n":
                index += 1
            continue
        else:
            out.append(char)
        index += 1
    return "".join(out)


def _organizer_pattern(name: str) -> dict:
    """Wzorzec organizatora: JSON z komentarzami i miejscami brakującym przecinkiem."""
    text = _strip_json_comments((PATTERN_DIR / name).read_text(encoding="utf-8"))
    text = re.sub(r'("(?:[^"\\]|\\.)*")(\s*\n\s*")', r"\1,\2", text)
    return json.loads(text)


def _key_shape(value):
    """Kolejność kluczy dokumentu jako lista par (klucz, kształt wartości)."""
    if isinstance(value, dict):
        return [(key, _key_shape(item)) for key, item in value.items()]
    if isinstance(value, list):
        return [_key_shape(item) for item in value[:1]]
    return None


def _key_order_matches(actual, expected) -> bool:
    """Czy dokumenty mają identyczne klucze w tej samej kolejności."""
    return _key_shape(actual) == _key_shape(expected)


def _reference_examples() -> list[tuple[Path, type]]:
    examples: list[tuple[Path, type]] = []
    for path in sorted(EXAMPLES_DIR.rglob("*.json")):
        model = DOCUMENT_MODELS.get(path.name)
        if model is not None:
            examples.append((path, model))
    return examples


# Dane referencyjne organizatora używają dla powodu 6 wariantu opisu z „i” zamiast „/”,
# a kanonicznym źródłem pozostaje słownik main-7590db8.
ORGANIZER_OPIS_VARIANTS = {
    "Odpowiedzi i wyjaśnienia do SWZ": "Odpowiedzi/wyjaśnienia do SWZ",
}


def _organizer_deviations(source: dict) -> list[tuple[str, str]]:
    """Różnice opisu czynności między danymi referencyjnymi a słownikiem przyczyn."""
    naglowek = source.get("OdwolanieKIO") or {}
    opis = naglowek.get("czynnosc_opis")
    if opis in ORGANIZER_OPIS_VARIANTS:
        return [(opis, ORGANIZER_OPIS_VARIANTS[opis])]
    return []


def _normalize_organizer_variant(source: dict) -> dict:
    naglowek = source.get("OdwolanieKIO") or {}
    opis = naglowek.get("czynnosc_opis")
    if opis not in ORGANIZER_OPIS_VARIANTS:
        return source
    return {**source, "OdwolanieKIO": {**naglowek, "czynnosc_opis": ORGANIZER_OPIS_VARIANTS[opis]}}


def test_spec_is_valid_openapi():
    validate(_load_spec())


def test_spec_declares_three_document_schemas():
    schemas = _load_spec()["components"]["schemas"]
    for name in ("Odwolanie", "Pelnomocnictwo", "Przelew", "PustyWynik"):
        assert name in schemas


def test_spec_has_single_copy_inside_the_package():
    assert SPEC_PATH == PACKAGE_DIR / "openapi.yaml"
    assert not (REPO_ROOT / "packages" / "contracts" / "openapi.yaml").exists()


def test_generated_models_match_committed_file(tmp_path):
    regenerated = tmp_path / "models.py"
    result = subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT), "--output", str(regenerated)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert regenerated.read_bytes() == MODELS_PATH.read_bytes()


def test_generated_models_expose_expected_classes():
    names = {
        name
        for name, value in inspect.getmembers(models, inspect.isclass)
        if value.__module__ == models.__name__
    }
    assert names == EXPECTED_MODEL_NAMES


def test_package_exposes_result_union():
    assert set(odwolania2json_contracts.Wynik.__args__) == {
        Odwolanie,
        Pelnomocnictwo,
        Przelew,
        PustyWynik,
    }


def test_models_keep_organizer_key_order():
    pattern = _organizer_pattern("odwolanie.json")
    document = Odwolanie.model_validate(
        {
            "OdwolanieKIO": {
                "data": "2025-10-13",
                "czynnosc_dzien": "2025-10-01",
                "czynnosc_powod_id": 4,
                "czynnosc_opis": "Publikacja specyfikacji warunków zamówienia (SWZ)",
                "miejscowosc": "Pruszków",
            },
            "Odwolujacy": [
                {
                    "krs": "0000054588",
                    "nazwa": "STRABAG Sp. z o.o.",
                    "nip": None,
                    "regon": None,
                    "przez-pelnomocnika": 1,
                    "pelnomocnik": {
                        "imie_nazwisko": "Marcel Kielce",
                        "nazwa": "Kancelaria Radców Prawnych",
                        "mail": "info@prawnik.xy",
                    },
                }
            ],
            "Zamawiajacy": [
                {
                    "krs": None,
                    "nazwa": "Filharmonia Pomorska",
                    "nip": "5540240549",
                    "regon": "000279077",
                    "prowadzacy_postepowanie": None,
                }
            ],
            "ZamowieniePubliczne": {
                "numer_bzp": None,
                "numer_postepowania": None,
                "numer_ted": "641651-2025",
                "tytul": "Wykonanie robót budowlanych",
            },
        }
    )
    assert _key_order_matches(document.model_dump(by_alias=True), pattern)


def test_key_order_comparison_is_order_sensitive():
    """Porównanie musi uwzględniać kolejność kluczy, a nie tylko ich zbiór."""
    pattern = _organizer_pattern("odwolanie.json")
    reversed_pattern = dict(reversed(list(pattern.items())))
    assert _key_order_matches(pattern, pattern)
    assert not _key_order_matches(pattern, reversed_pattern)


def test_empty_result_serializes_as_empty_object():
    assert PustyWynik().model_dump() == {}
    assert PustyWynik.model_validate({}).model_dump(by_alias=True) == {}


def test_organizer_pattern_validates_against_models():
    """Wzorce organizatora muszą przechodzić walidację modelami (pesel jako liczba)."""
    for name, model in DOCUMENT_MODELS.items():
        pattern = _organizer_pattern(name)
        document = model.model_validate(pattern)
        assert _key_order_matches(document.model_dump(by_alias=True), pattern), name


def test_reference_examples_validate_against_models():
    examples = _reference_examples()
    assert len(examples) == 180
    deviations: set[tuple[str, str]] = set()
    for path, model in examples:
        source = json.loads(path.read_text(encoding="utf-8"))
        normalized = _normalize_organizer_variant(source)
        deviations.update(_organizer_deviations(source))
        document = model.model_validate(normalized)
        assert _key_order_matches(document.model_dump(by_alias=True), source), path
    assert deviations == {("Odpowiedzi i wyjaśnienia do SWZ", "Odpowiedzi/wyjaśnienia do SWZ")}
