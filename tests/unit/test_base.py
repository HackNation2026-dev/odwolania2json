"""Test wspólnego typu wyniku ekstrakcji (`Ekstrakcja`)."""

from __future__ import annotations

from odwolania2json.domain.base import Ekstrakcja
from odwolania2json_contracts.models import PustyWynik


def test_ekstrakcja_holds_model_and_evidence():
    ekstrakcja = Ekstrakcja(model=PustyWynik(), evidence={"przelew_bankowy.kwota": (2, 41)})

    assert ekstrakcja.model.model_dump() == {}
    assert ekstrakcja.evidence["przelew_bankowy.kwota"] == (2, 41)
