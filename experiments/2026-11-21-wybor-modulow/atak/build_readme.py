"""Składa E##/README.md z ręcznie napisanych części (E##/opis.md, E##/wnioski.md) i tabel generowanych z E##/wyniki.json.

Użycie: .venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/build_readme.py E12 [E13 ...]
"""
import json
import sys
from collections import Counter
from pathlib import Path

ATAK = Path(__file__).resolve().parent


def cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def vector_tables(vectors: list[dict]) -> str:
    cnt = Counter(v["gap"] for v in vectors)
    out = ["### Zestawienie wektorów", "", f"Wektorów: {len(vectors)}; luka: " + ", ".join(f"{k} {n}" for k, n in sorted(cnt.items())) + ".", "",
           "| ID | Rodzina | Wektor | Luka |", "|---|---|---|---|"]
    for v in vectors:
        out.append(f"| {v['id']} | {cell(v['family'])} | {cell(v['name'])} | **{v['gap']}** |")
    out += ["", "### Szczegóły: oczekiwane, faktyczne, poprawka, test do produktu", ""]
    for v in vectors:
        out += [f"**{v['id']} — {v['name']}** (luka: {v['gap']})", "",
                f"- Oczekiwane: {v['expected']}", f"- Faktyczne: {v['actual']}"]
        if v.get("fix"):
            out.append(f"- Proponowana poprawka: {v['fix']}")
        if v.get("port_test"):
            out.append(f"- Test do przeniesienia do produktu: `{v['port_test']}`")
        out.append("")
    return "\n".join(out)


def main() -> None:
    for exp in sys.argv[1:]:
        d = ATAK / exp
        data = json.loads((d / "wyniki.json").read_text(encoding="utf-8"))
        head = (d / "opis.md").read_text(encoding="utf-8")
        tail = (d / "wnioski.md").read_text(encoding="utf-8") if (d / "wnioski.md").exists() else ""
        parts = [head.rstrip(), "", "## Wyniki wektorów", "", vector_tables(data["vectors"]) if data.get("vectors") else "", tail.rstrip(), ""]
        (d / "README.md").write_text("\n".join(parts), encoding="utf-8")
        print("zapisano", d / "README.md")


main()
