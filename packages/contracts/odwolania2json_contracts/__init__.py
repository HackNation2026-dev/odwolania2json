"""Pakiet kontraktu danych Odwołania2JSON.

Modele pydantic są generowane z ``odwolania2json_contracts/openapi.yaml``
skryptem ``scripts/generate_contracts.py`` i używane przez backend oraz API.
"""

from . import models
from .models import Odwolanie, Pelnomocnictwo, Przelew, PustyWynik
from .powody import APPEAL_REASONS

__version__ = "0.6.1"

Wynik = Odwolanie | Pelnomocnictwo | Przelew | PustyWynik

__all__ = ["APPEAL_REASONS", "Wynik", "__version__", "models"]
