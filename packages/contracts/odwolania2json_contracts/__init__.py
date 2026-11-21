"""Pakiet kontraktu danych Odwołania2JSON.

Modele pydantic są generowane z ``packages/contracts/openapi.yaml``
skryptem ``scripts/generate_contracts.py`` i używane przez backend oraz API.
"""

from typing import Union

from . import models
from .models import Odwolanie, Pelnomocnictwo, Przelew, PustyWynik
from .powody import APPEAL_REASONS

__version__ = "0.5.0"

Wynik = Union[Odwolanie, Pelnomocnictwo, Przelew, PustyWynik]

__all__ = ["APPEAL_REASONS", "Wynik", "models", "__version__"]
