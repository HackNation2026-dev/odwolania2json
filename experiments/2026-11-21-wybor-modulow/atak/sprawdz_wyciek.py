"""Kontrola wycieku: czy prawdziwy klucz LLM (z pliku MINIMAX_KEY_FILE) albo kanarki występują w wynikach, logach i katalogach roboczych grupy D.

Wypisuje tylko liczby i ścieżki plików, nigdy wartości kluczy. Uruchomienie: .venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/sprawdz_wyciek.py
Kanarki testowe (CANARY-KEY-*) są oczekiwane tylko w plikach klucza `key/key.canary` i w atrapach; każde inne trafienie jest raportowane.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import ATAK, SANDBOX, read_key_for_leak_check  # noqa: E402

key = read_key_for_leak_check()
roots = [ATAK, SANDBOX]
real_hits, canary_hits, scanned = [], [], 0
bearer = re.compile(rb"(?i)(authorization\"?\s*[:=]\s*\"?bearer\s+[A-Za-z0-9._\-]{8,}|x-api-key\"?\s*[:=]\s*\"?[A-Za-z0-9._\-]{16,})")
bearer_hits = []
for r in roots:
    for p in r.rglob("*"):
        if not p.is_file() or p.is_symlink() or p.stat().st_size > 400 * 1024 * 1024:
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        scanned += 1
        if key and key.encode() in data:
            real_hits.append(str(p))
        if re.search(rb"CANARY-KEY-[0-9a-f]{16,}", data) and p.name != "key.canary" and p.suffix not in (".py",):
            canary_hits.append(str(p.relative_to(r)))
        if p.suffix in (".json", ".log", ".md", ".txt") and bearer.search(data):
            bearer_hits.append(str(p))
print(json.dumps({"files_scanned": scanned, "key_available_for_check": bool(key), "real_key_hits": real_hits, "canary_hits_outside_key_files": canary_hits[:20],
                  "n_canary_hits": len(canary_hits), "auth_header_like_strings": bearer_hits[:20]}, ensure_ascii=False, indent=2))
