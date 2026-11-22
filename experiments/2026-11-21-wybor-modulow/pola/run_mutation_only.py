"""Samo uruchomienie mutacji E08 (po zmianach sond) i zapis do E08/mutacje.json."""
import json, lib, mutate
pdf = lib.read_text_cache(); ocr = json.loads((lib.CACHE / "texts_ocr150.json").read_text())
keys = [k for k, v in pdf.items() if v["class"] != "obcy"]
r = mutate.run({k: lib.doc_text(pdf[k]) for k in keys}, {k: lib.doc_text(ocr[k]) for k in keys if k in ocr}, keys)
(lib.HERE / "E08" / "mutacje.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))
print({k: v for k, v in r.items() if k not in ("by_pattern", "survivors")})
import collections
c = collections.defaultdict(list)
for s in r["survivors"]: c[s["pattern"]].append(s["operator"])
for k, v in c.items(): print(k, len(v), v[:8])
