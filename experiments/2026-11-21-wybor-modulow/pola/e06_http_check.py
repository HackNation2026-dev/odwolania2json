"""E06, część HTTP: router regułowy uprzęży przez HTTP na plikach o LOSOWYCH nazwach (heksadecymalnych); zgodność z klasą referencyjną.
Wynik: E06/http_wyniki.json (stan, klasa, RSS, limit pamięci). Jedyna rola: potwierdzić, że nazwa pliku nie wpływa na klasę.
"""
from __future__ import annotations

import json
import random
import shutil
import tempfile
from pathlib import Path

import lib
from client import HarnessClient, ManagedServer

rng = random.Random(20261122)
items = lib.dev_items()
pick = [i for c in ("odwolanie", "pelnomocnictwo", "przelew") for i in [x for x in items if x.document_class == c][:6:2]] + [i for i in items if i.document_class == "obcy"][:3]
tmp = Path(tempfile.mkdtemp(prefix="e06-"))
cfg = tmp / "cfg.json"
cfg.write_text(json.dumps({"pdf_reader": "pdfium", "ocr": "none", "router": "rules", "extractor": "none"}))
rows = []
with ManagedServer(str(cfg)) as srv, HarnessClient(srv.url, server=srv) as c:
    for it in pick:
        name = f"{rng.getrandbits(48):012x}.pdf"
        dst = tmp / name
        shutil.copyfile(it.source, dst)
        r = c.run_document(dst)
        st = r["state"]
        rows.append({"true_class": it.document_class, "random_name": name, "outcome": st.get("outcome"), "class_id": st.get("class_id"), "codes": st.get("codes"),
                     "peak_rss_mb": r.get("peak_rss_mb"), "wall_s": r["timing"]["wall_s"]})
    limit = srv.limit_method
exp = {"odwolanie": "appeal", "pelnomocnictwo": "power_of_attorney", "przelew": "bank_transfer"}
ok = sum(1 for r in rows if (r["true_class"] == "obcy" and r["outcome"] in ("foreign", "ambiguous")) or exp.get(r["true_class"]) == r["class_id"])
out = {"n": len(rows), "agree_with_reference_or_rejected_negative": ok, "limit_method": limit, "rows": rows}
(lib.HERE / "E06" / "http_wyniki.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(ok, "/", len(rows), limit, [r["outcome"] + ":" + str(r["class_id"]) for r in rows])
shutil.rmtree(tmp, ignore_errors=True)
