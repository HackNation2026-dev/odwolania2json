#!/usr/bin/env python3
"""Kontrola dokumentacji i kopii źródeł, bez testowania aplikacji."""

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

root = Path(__file__).resolve().parents[1]
errors = []
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
manifest = json.loads((root / "docs/02-materialy/manifest.json").read_text(encoding="utf-8"))
listed = set()
for row in manifest["files"]:
    p = root / row["path"]
    listed.add(row["path"])
    if not p.is_file():
        errors.append(f"Brak materiału: {row['path']}")
        continue
    if (
        p.stat().st_size != row["bytes"]
        or hashlib.sha256(p.read_bytes()).hexdigest() != row["sha256"]
    ):
        errors.append(f"Zmieniony materiał: {row['path']}")
folders = [root / "docs/01-zadanie/zrodla"] + [
    p for p in (root / "docs/02-materialy").glob("organizator*") if p.is_dir()
]
actual = {p.relative_to(root).as_posix() for f in folders for p in f.rglob("*") if p.is_file()}
for p in sorted(actual - listed):
    errors.append(f"Materiał poza manifestem: {p}")
lock = root / "docs/02-materialy/uzp-revision.json"
if lock.exists():
    data = json.loads(lock.read_text(encoding="utf-8"))
    base = root / "docs/02-materialy/organizator-uzp"
    expected = {r["path"] for r in data["files"]}
    found = {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()}
    if expected != found:
        errors.append(
            f"Niezgodny zestaw UZP: brak {sorted(expected - found)}, "
            f"nadmiar {sorted(found - expected)}"
        )
    for row in data["files"]:
        p = base / row["path"]
        if not p.exists():
            continue
        b = p.read_bytes()
        sha = hashlib.sha1(
            b"blob " + str(len(b)).encode() + b"\0" + b, usedforsecurity=False
        ).hexdigest()
        if sha != row["git_blob_sha1"] or len(b) != row["size"]:
            errors.append(f"Niezgodny blob UZP: {row['path']}")
upd = root / "docs/02-materialy/uzp-aktualizacje.json"
if upd.exists():
    # Uzupełnienie addytywne: późniejsze rewizje i gałęzie organizatora UZP.
    data = json.loads(upd.read_text(encoding="utf-8"))
    ubase = root / "docs/02-materialy/organizator-uzp-aktualizacje"
    stored = set()
    for snap in data["snapshots"]:
        for row in snap["files"]:
            if not row["stored"]:
                q = root / "docs/02-materialy/organizator-uzp" / row["path"]
                if not q.exists():
                    errors.append(f"Brak pliku bazowego UZP: {row['path']}")
                    continue
            else:
                q = ubase / snap["dir"] / row["path"]
                stored.add(q.relative_to(ubase).as_posix())
                if not q.exists():
                    errors.append(f"Brak aktualizacji UZP: {snap['dir']}/{row['path']}")
                    continue
            b = q.read_bytes()
            if (
                hashlib.sha1(
                    b"blob " + str(len(b)).encode() + b"\0" + b, usedforsecurity=False
                ).hexdigest()
                != row["git_blob_sha1"]
            ):
                errors.append(f"Niezgodny blob aktualizacji UZP: {snap['dir']}/{row['path']}")
    found = {p.relative_to(ubase).as_posix() for p in ubase.rglob("*") if p.is_file()}
    if found != stored:
        errors.append(
            f"Niezgodny zestaw aktualizacji UZP: brak {sorted(stored - found)}, "
            f"nadmiar {sorted(found - stored)}"
        )
# Kontrola tylko dokumentacji zespołu; odnośniki w oryginałach nie są przez nas naprawiane.
count = 0
for p in root.rglob("*.md"):
    rel = p.relative_to(root)
    if (
        ".git" in rel.parts
        or ".ci" in rel.parts
        or ".superpowers" in rel.parts
        or ".venv" in rel.parts
        or "zrodla" in rel.parts
        or any(s.startswith("organizator") for s in rel.parts)
    ):
        continue
    count += 1
    s = p.read_text(encoding="utf-8")
    for link in re.findall(r"(?<!!)\[[^\]]*\]\((<[^>]+>|[^)\n]+)\)", s):
        link = link.strip().split(' "')[0].strip("<>")
        link = unquote(link.split("#", 1)[0])
        if not link or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", link):
            continue
        if not (p.parent / link).exists():
            errors.append(f"Nieistniejący link: {rel} -> {link}")
    if rel.parts[0] == "docs" and "wersja:" not in s:
        errors.append(f"Brak wersji dokumentu: {rel}")
for f in ["README.md", "VERSION", "CHANGELOG.md", "docs/README.md", "docs/02-materialy/rejestr.md"]:
    if not (root / f).exists():
        errors.append(f"Brak pliku: {f}")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(listed)} materiałów, {count} dokumentów, odnośniki lokalne i integralność źródeł.")
