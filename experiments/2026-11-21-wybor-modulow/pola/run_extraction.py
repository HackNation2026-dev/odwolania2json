"""Uruchamia ekstrakcję LLM dla zbioru rozwojowego (147 dokumentów) i luk (gaps.py); zapisuje cache/extraction_llm.json."""
from __future__ import annotations

import json
import sys

import gaps
import lib
import llm_calls
import llm_extract

repeat = int(sys.argv[1]) if len(sys.argv) > 1 else 0
t = lib.read_text_cache()
items = [(it.key, lib.CLASS_OF[it.document_class], lib.doc_text(t[it.key])) for it in lib.dev_items() if it.document_class != "obcy"]
g = gaps.build()
items += [(x["key"], lib.CLASS_OF[{"odwolanie": "odwolanie", "przelew": "przelew"}[x["class"]]], "[[strona 1]]\n" + x["text"]) for x in g]
res = llm_extract.extract(items, workers=2, repeat=repeat)
out = {k: {kk: v for kk, v in r.items() if kk != "cached"} for k, r in res.items()}
(lib.CACHE / f"extraction_llm_r{repeat}.json").write_text(json.dumps(out, ensure_ascii=False))
print(len(out), "ok:", sum(1 for r in out.values() if r["ok"]), llm_calls.STATS)
