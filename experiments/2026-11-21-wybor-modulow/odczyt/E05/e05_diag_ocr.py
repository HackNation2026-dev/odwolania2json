"""Diagnoza błędnych kotwic w OCR (E05-B): dla kotwic z IoU < 0,5 podaje geometrię (pokrycie prawdy, odległość środków, szerokość). Czyta cache OCR z E05 (bez nowego OCR).
Polecenie: python E05/e05_diag_ocr.py → E05/e05-diag-ocr.json"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent/"E02")); sys.path.insert(0, str(HERE.parent))
import e05_anchor as E
from e02_quality import CACHE
E.CACHE_DIR = CACHE
import lib, data, reading as R
from api import load_zestaw
items = data.load_items("cases-dev"); rd = R.PdfiumReader()
cases_sel = set(E.subset_cases()); rows = []
for si in [i for i in load_zestaw(["skan"]) if i.case_id in cases_sel]:
    s = [i for i in items if i.case_id == si.case_id and i.document_class == si.document_class][0]
    d0 = rd.open(s.source.read_bytes()); op_ = [rd.read_page(d0, i) for i in range(rd.page_count(d0))]
    rp = []
    for i in range(len(op_)):
        cp = E.CACHE_DIR / f"e05-dpi150/{si.id.replace('/','__')}/p{i+1}.json"
        o = json.loads(cp.read_text()); W, H = op_[i]["width_pt"], op_[i]["height_pt"]
        r = R.ocr_page_to_reading(i+1, o, o["px"][0]*72.0/W, W, H); rp.append({"number": i+1, "words": r["words"], "lines": r["lines"]})
    for c in E.make_cases(rp, si.reference()):
        res = E.RESOLVER.resolve({"pages": rp}, c["quotes"]["exact"], c["page"])
        if res["status"] != "anchored": continue
        bb = E.anchored_union(res); ws = op_[c["page"]-1]["words"]
        spans = E.spans_for(ws, c["key"], dict(lib.leaves(si.reference()))[c["path"]])
        tr = [E.union(ws[a:b+1]) for a, b in spans]
        best = max(tr, key=lambda t: E.iou(bb, t)); v = E.iou(bb, best)
        if v < 0.5:
            cx = lambda b: ((b[0]+b[2])/2, (b[1]+b[3])/2)
            (ax, ay), (tx, ty) = cx(bb), cx(best)
            inter = max(0, min(bb[2], best[2]) - max(bb[0], best[0])) * max(0, min(bb[3], best[3]) - max(bb[1], best[1]))
            rows.append({"doc": si.id, "field": c["key"], "iou": round(v, 3), "dx": round(ax-tx, 1), "dy": round(ay-ty, 1), "w_anchor": round(bb[2]-bb[0], 1), "w_truth": round(best[2]-best[0], 1),
                         "h_anchor": round(bb[3]-bb[1], 1), "h_truth": round(best[3]-best[1], 1), "truth_covered": round(inter/((best[2]-best[0])*(best[3]-best[1])), 2), "n_truth_spans": len(tr)})
a = np.array
out = {"n_wrong": len(rows), "median_abs_dy": float(np.median(np.abs(a([r['dy'] for r in rows])))), "median_abs_dx": float(np.median(np.abs(a([r['dx'] for r in rows])))),
       "median_truth_covered": float(np.median(a([r['truth_covered'] for r in rows]))), "share_center_within_one_height": float(np.mean([abs(r['dy']) < r['h_truth'] and abs(r['dx']) < max(r['w_truth'], r['w_anchor']) for r in rows])),
       "by_field": {k: sum(r['field']==k for r in rows) for k in sorted({r['field'] for r in rows})}, "multi_span": sum(r['n_truth_spans']>1 for r in rows), "rows": rows[:40]}
lib.dump(HERE / "e05-diag-ocr.json", out); print(json.dumps({k: v for k, v in out.items() if k != 'rows'}, ensure_ascii=False)); print(rows[:6])
