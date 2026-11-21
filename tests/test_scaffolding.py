"""Test szkieletu repozytorium: importowalne pakiety i działające CLI."""

import runpy
import sys

import odwolania2json_contracts
import pytest
from odwolania2json.__main__ import main


def test_cli_help_runs(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "Odwołania2JSON" in capsys.readouterr().out


def test_contracts_package_is_importable():
    assert odwolania2json_contracts.__version__


def test_module_run_prints_help_without_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["odwolania2json"])
    # Usunięcie z sys.modules, żeby runpy nie zgłosił ostrzeżenia o ponownym imporcie.
    sys.modules.pop("odwolania2json.__main__", None)
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("odwolania2json", run_name="__main__")
    assert exc.value.code == 0
    assert "Odwołania2JSON" in capsys.readouterr().out
