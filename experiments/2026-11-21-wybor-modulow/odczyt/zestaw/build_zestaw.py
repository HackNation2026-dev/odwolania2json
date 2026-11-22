"""Buduje zestaw skanów z referencją pól z 49 spraw rozwojowych (147 dokumentów).

Uruchomienie: ../../../.venv-exp/bin/python zestaw/build_zestaw.py [--jobs 3]
Wynik: zestaw/data/{pdf,ref}/..., zestaw/manifest.json. Deterministyczne dla ziarna.
Profile wyznaczono z 3 skanów negatywnych i szablonu organizatora (patrz PROFIL.md).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import time
import unicodedata
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guard import assert_dev_case, assert_manifest_clean  # noqa: E402

import data as hdata  # noqa: E402  (harness)
from common import sha256_file, write_json_atomic  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data"
SEED = 20261122
FIXED = time.gmtime(1767225600)

# Profile z pomiarów: DPI prawdziwe, JPEG (jakość PIL dobrana do tablicy kwantyzacji), tło, szum, kąt, deklarowane dpi.
PROFILES = {
    "P1-szablon": dict(dpi=200, gray=False, quality=92, bg=255, noise=1.5, blur=0.5, skew=0.3, declared=96, fold=False,
                       src="szablon: 1654x2339 RGB, q0[0]=3, szum tła 0,5-1,5, deklarowane 96 dpi (MediaBox 1240x1754 pt)"),
    "P2-ksero-szare": dict(dpi=200, gray=True, quality=85, bg=255, noise=2.1, blur=0.6, skew=0.7, declared=200, fold=False,
                           src="bizhub 223: 1653x2338 szary, q0[0]=5, szum 2,1, kąt do 0,6°"),
    "P3-ksero-rgb": dict(dpi=200, gray=False, quality=77, bg=251, noise=2.7, blur=0.6, skew=0.3, declared=200, fold=True,
                         src="Decyzja Min. Sportu: 1654x2337 RGB, q0[0]=8, tło 251, szum 2,7"),
    "P4-300-szare": dict(dpi=300, gray=True, quality=31, bg=255, noise=2.7, blur=0.7, skew=0.7, declared=300, fold=False,
                         src="pismo Min. Sprawiedliwości: 3507x2480 szary, q0[0]=26 (jakość ok. 31), szum 2,7"),
}
WEIGHTS = [("P1-szablon", 40), ("P2-ksero-szare", 25), ("P3-ksero-rgb", 25), ("P4-300-szare", 10)]


def doc_seed(variant: str, key: str) -> int:
    return int(hashlib.sha256(f"{SEED}/{variant}/{key}".encode()).hexdigest()[:8], 16)


def assign_profile(key: str) -> str:
    v = int(hashlib.sha256(f"profil/{key}".encode()).hexdigest()[:6], 16) % 100
    acc = 0
    for name, w in WEIGHTS:
        acc += w
        if v < acc:
            return name
    return WEIGHTS[-1][0]


def degrade(img: Image.Image, p: dict, rng: np.random.Generator, skew: float | None = None) -> Image.Image:
    ang = skew if skew is not None else float(rng.uniform(-p["skew"], p["skew"]))
    if p["gray"]:
        img = img.convert("L")
    bgv = p["bg"]
    if ang:
        img = img.rotate(ang, resample=Image.BICUBIC, fillcolor=255 if p["gray"] else (255, 255, 255))
    if p["blur"]:
        img = img.filter(ImageFilter.GaussianBlur(p["blur"]))
    a = np.asarray(img).astype(np.float32)
    if bgv < 255:
        a = a * (bgv / 255.0)
    if p.get("fold"):  # zagięcia: słabe poziome pasma w 1/3 i 2/3 wysokości
        h = a.shape[0]
        for f in (h // 3, 2 * h // 3):
            a[f - 2:f + 2] *= 0.94
    a += rng.normal(0, p["noise"], a.shape).astype(np.float32)
    specks = rng.random(a.shape[:2]) < 0.0004
    a[specks] = 40
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def render(doc: pdfium.PdfDocument, i: int, dpi: int) -> Image.Image:
    return doc[i].render(scale=dpi / 72.0).to_pil().convert("RGB")


def save_pdf(images: list[Image.Image], out: Path, declared: int, quality: int) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    images[0].save(buf, "PDF", resolution=declared, save_all=True, append_images=images[1:], quality=quality,
                   creationDate=FIXED, modDate=FIXED)
    out.write_bytes(buf.getvalue())


def v_scan(src: Path, out: Path, profile: str, seed: int, **kw) -> dict:
    p = PROFILES[profile]
    rng = np.random.default_rng(seed)
    d = pdfium.PdfDocument(str(src))
    imgs = []
    for i in range(len(d)):
        im = render(d, i, p["dpi"])
        im = degrade(im, p, rng, kw.get("skew"))
        rot = kw.get("rotate")
        if rot:
            im = im.rotate(rot, expand=True)
        imgs.append(im)
    save_pdf(imgs, out, p["declared"], p["quality"])
    return {"pages": len(imgs)}


def v_mixed(src: Path, out: Path, profile: str, seed: int, **kw) -> dict:
    """Strona 1 zostaje tekstowa, pozostałe jako skan (profil z deklarowanym prawdziwym dpi)."""
    p = dict(PROFILES[profile])
    p["declared"] = p["dpi"]
    rng = np.random.default_rng(seed)
    d = pdfium.PdfDocument(str(src))
    n = len(d)
    idx = list(range(1, n)) or [0]
    imgs = [degrade(render(d, i, p["dpi"]), p, rng) for i in idx]
    tmp = io.BytesIO()
    imgs[0].save(tmp, "PDF", resolution=p["declared"], save_all=True, append_images=imgs[1:], quality=p["quality"],
                 creationDate=FIXED, modDate=FIXED)
    new = pdfium.PdfDocument.new()
    new.import_pages(pdfium.PdfDocument(str(src)), [0])
    new.import_pages(pdfium.PdfDocument(tmp.getvalue()))
    bio = io.BytesIO()
    new.save(bio)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bio.getvalue())
    return {"pages": n, "text_pages": [1], "scan_pages": [i + 1 for i in idx] if n > 1 else []}


def v_s2(src: Path, out: Path, profile: str, seed: int, **kw) -> dict:
    """S2: dolna połowa strony 1 zastąpiona obrazem (dane tylko w obrazie na stronie tekstowej)."""
    p = dict(PROFILES[profile])
    rng = np.random.default_rng(seed)
    doc = pdfium.PdfDocument(str(src))
    page = doc[0]
    W, H = page.get_size()
    cs = sorted((o.get_bounds()[1] + o.get_bounds()[3]) / 2 for o in page.get_objects(filter=[pdfium.raw.FPDF_PAGEOBJ_TEXT]))
    cut = cs[len(cs) // 2] if cs else H * 0.5  # mediana środków tekstu: ok. połowy tekstu trafia do obrazu
    full = render(doc, 0, p["dpi"])
    lower = full.crop((0, int(round((H - cut) / H * full.height)), full.width, full.height))
    lower = degrade(lower, dict(p, skew=0), rng, 0.0).convert("RGB")
    removed = 0
    for obj in list(page.get_objects(filter=[pdfium.raw.FPDF_PAGEOBJ_TEXT])):
        l, b, r, t = obj.get_bounds()
        if (b + t) / 2 < cut:
            page.remove_obj(obj)
            removed += 1
    img = pdfium.PdfImage.new(doc)
    img.set_bitmap(pdfium.PdfBitmap.from_pil(lower))
    img.set_matrix(pdfium.PdfMatrix().scale(W, cut))
    page.insert_obj(img)
    page.gen_content()
    bio = io.BytesIO()
    doc.save(bio)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bio.getvalue())
    return {"pages": len(doc), "image_region_page1_cut_pt": round(cut, 1), "removed_text_objects": removed}


def _fold(s: str) -> str:
    s = s.replace("ł", "l").replace("Ł", "L")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def v_s5(src: Path, out: Path, profile: str, seed: int, **kw) -> dict:
    """S5: poprawny obraz strony (skan) + niewidoczna (tryb 3 Tr) warstwa z błędnymi cyframi."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject
    from reading import PdfiumReader
    p = dict(PROFILES[profile])
    p["declared"] = p["dpi"]
    rng = np.random.default_rng(seed)
    doc = pdfium.PdfDocument(str(src))
    n = len(doc)
    imgs = [degrade(render(doc, i, p["dpi"]), p, rng) for i in range(n)]
    tmp = io.BytesIO()
    imgs[0].save(tmp, "PDF", resolution=p["declared"], save_all=True, append_images=imgs[1:], quality=p["quality"],
                 creationDate=FIXED, modDate=FIXED)
    rd = PdfiumReader()
    wrong_digits = 0
    wr = PdfWriter(clone_from=PdfReader(io.BytesIO(tmp.getvalue())))
    for i in range(n):
        pg = rd.read_page(doc, i)
        H = pg["height_pt"]
        ops = ["BT", "3 Tr"]
        for w in pg["words"]:
            x0, y0, x1, y1 = w["bbox"]
            fs = max(4.0, (y1 - y0) * 0.8)
            t = _fold(w["text"])
            t2 = re.sub(r"\d", lambda m: str((int(m.group()) + 3) % 10), t)
            wrong_digits += sum(a != b for a, b in zip(t, t2))
            t2 = t2.replace("\\", "").replace("(", "").replace(")", "")
            ops.append(f"/F1 {fs:.1f} Tf 1 0 0 1 {x0:.2f} {H - y1 + fs * 0.2:.2f} Tm ({t2}) Tj")
        ops.append("ET")
        page = wr.pages[i]
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
                                 NameObject("/BaseFont"): NameObject("/Helvetica"),
                                 NameObject("/Encoding"): NameObject("/WinAnsiEncoding")})
        res = page["/Resources"]
        res[NameObject("/Font")] = DictionaryObject({NameObject("/F1"): wr._add_object(font)})
        st = DecodedStreamObject()
        st.set_data("\n".join(ops).encode("latin-1", "replace"))
        old = page.raw_get("/Contents")
        page[NameObject("/Contents")] = ArrayObject([old, wr._add_object(st)])
    bio = io.BytesIO()
    wr.write(bio)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bio.getvalue())
    return {"pages": n, "invisible_layer": "wrong_digits(+3 mod 10), ascii-folded", "wrong_digit_count": wrong_digits}


def build_one(job: dict) -> dict:
    assert_dev_case(job["case_id"])
    src = Path(job["source"])
    out = OUT / "pdf" / job["variant"] / job["case_id"] / job["input_name"]
    seed = doc_seed(job["variant"], f"{job['case_id']}/{job['input_name']}")
    fn = {"scan": v_scan, "mixed": v_mixed, "s2": v_s2, "s5": v_s5}[job["fn"]]
    extra = fn(src, out, job["profile"], seed, **job.get("kw", {}))
    ref = hdata.reference_for(hdata.DocItem(job["case_id"], job["input_name"], job["document_class"], "dev", src, job["reference_name"]))
    rp = OUT / "ref" / job["case_id"] / (Path(job["input_name"]).stem + ".json")
    write_json_atomic(rp, ref)
    return {"id": f"{job['variant']}/{job['case_id']}/{Path(job['input_name']).stem}", "variant": job["variant"], "profile": job["profile"],
            "case_id": job["case_id"], "input_name": job["input_name"], "document_class": job["document_class"],
            "parent_split": "rozwojowy", "seed": seed, "kw": job.get("kw", {}),
            "source": str(src.relative_to(hdata.REPO)), "source_sha256": sha256_file(src),
            "pdf": str(out.relative_to(ROOT)), "pdf_sha256": sha256_file(out), "ref": str(rp.relative_to(ROOT)),
            "input_kind": job["input_kind"], **extra}


def make_jobs() -> list[dict]:
    items = sorted(hdata.load_items("cases-dev"), key=lambda i: i.key)
    for it in items:
        assert_dev_case(it.case_id)
    mk = lambda it, variant, fn, profile, kind, kw=None: dict(  # noqa: E731
        case_id=it.case_id, input_name=it.input_name, document_class=it.document_class, reference_name=it.reference_name,
        source=str(it.source), variant=variant, fn=fn, profile=profile, input_kind=kind, kw=kw or {})
    jobs = []
    cases = sorted({i.case_id for i in items})
    by = lambda c: {i.document_class: i for i in items if i.case_id == c}  # noqa: E731
    for it in items:  # glowny zestaw: 147 skanow, profil z hasha
        jobs.append(mk(it, "skan", "scan", assign_profile(it.key), "scan"))
    sub12 = cases[::4][:12]
    for c in sub12:  # stres: obrót fizyczny i skos 3° (dokumenty: odwołanie)
        it = by(c)["odwolanie"]
        for r in (90, 180, 270):
            jobs.append(mk(it, f"obrot{r}", "scan", "P2-ksero-szare", "scan", {"rotate": r}))
        jobs.append(mk(it, "skos3", "scan", "P2-ksero-szare", "scan", {"skew": 3.0}))
    for c in cases:
        jobs.append(mk(by(c)["odwolanie"], "mieszany", "mixed", "P2-ksero-szare", "mixed"))
        jobs.append(mk(by(c)["przelew"], "s2", "s2", "P2-ksero-szare", "s2"))
        jobs.append(mk(by(c)["pelnomocnictwo"], "s5", "s5", "P2-ksero-szare", "s5_wrong_layer"))
    return jobs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=3)
    ns = ap.parse_args()
    jobs = make_jobs()
    t0 = time.time()
    with ProcessPoolExecutor(ns.jobs) as ex:
        entries = list(ex.map(build_one, jobs, chunksize=4))
    entries.sort(key=lambda e: e["id"])
    manifest = {"seed": SEED, "profiles": PROFILES, "n_entries": len(entries), "entries": entries,
                "wall_s": round(time.time() - t0, 1)}
    assert_manifest_clean(manifest)
    write_json_atomic(ROOT / "manifest.json", manifest)
    print(len(entries), "wpisów,", manifest["wall_s"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
