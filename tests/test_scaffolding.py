"""Test szkieletu repozytorium: importowalny pakiet i działające CLI."""

import pytest

from odwolania2json.__main__ import main


def test_cli_help_runs(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "Odwołania2JSON" in capsys.readouterr().out
