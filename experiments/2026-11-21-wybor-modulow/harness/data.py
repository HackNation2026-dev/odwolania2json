"""Zbiór danych eksperymentów: pary PDF ↔ referencja (z poprawkami organizatora), podział, warianty brzegowe.

- Ładowanie używa `odwolania2json.loader` i `dataset` (tylko odczyt; poprawki organizatora nakładane w pamięci).
- Podział: `data/podzial.json` (zamrożony). Strojenie wyłącznie na `dev`; `control` tylko raz, na końcu.
  Negatywy (`dane/negatywne`) nie należą do żadnej strony podziału: dołączamy je do `dev`
  (potrzebne do strojenia routera), nigdy do `control`.
- Oryginały organizatora nie są modyfikowane: `materialize` kopiuje je do `harness/work/data/`
  i weryfikuje skrót SHA-256 kopii względem źródła.
- Warianty: obrót, przekrzywienie, niska rozdzielczość, szum, JPEG, mieszane, rasteryzacja 100/150/200/300 dpi.
  Funkcje obrazowe pochodzą z `experiments/2026-11-21-przypadki-brzegowe/narzedzia/syntetyczne.py`
  (ten sam „wygląd skanu”), a renderowanie stron robi pdfium (bez `pdftoppm`).
"""

from __future__ import annotations

import importlib.util
import io
import shutil
import sys
from dataclasses import asdict, dataclass
import time
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
from PIL import Image, ImageFilter

import common
from common import MATERIALS, REPO, WORK_ROOT, sha256_file, write_json_atomic
from odwolania2json.dataset import load_split
from odwolania2json.loader import CaseReference, load_case_references, load_reference_json

DATA_WORK = WORK_ROOT / "data"
TEMPLATE_DIR = MATERIALS / "szablon-aplikacja" / "input" / "case1"
RASTER_DPIS = (100, 150, 200, 300)
_FIXED_DATE = time.gmtime(1767225600)  # 2026-01-01 UTC; PIL wymaga struct_time
SYN_TOOLS = REPO / "experiments" / "2026-11-21-przypadki-brzegowe" / "narzedzia"


@dataclass(frozen=True)
class DocItem:
    case_id: str
    input_name: str
    document_class: str            # odwolanie | pelnomocnictwo | przelew | obcy | szablon
    split: str                     # dev | control | negatives | template
    source: Path
    reference_name: str | None

    @property
    def key(self) -> str:
        return f"{self.case_id}/{self.input_name}"


def _split_of(ref: CaseReference) -> str:
    if ref.case_id == "negatywne":
        return "negatives"
    sp = load_split()
    if ref.case_id in sp.kontrolny:
        return "control"
    if ref.case_id in sp.rozwojowy:
        return "dev"
    raise ValueError(f"sprawa spoza podziału: {ref.case_id}")


def load_items(which: str = "dev") -> list[DocItem]:
    """`dev` (rozwojowy + negatywy), `control`, `all`, `negatives`, `template`, `cases-dev` (bez negatywów)."""
    if which == "template":
        return [DocItem("szablon", p.name, "szablon", "template", p, None) for p in sorted(TEMPLATE_DIR.glob("*.pdf"))]
    items = []
    for ref in load_case_references():
        sp = _split_of(ref)
        src = MATERIALS / "dane" / ref.case_id / ref.input_name if sp != "negatives" else MATERIALS / "dane" / "negatywne" / ref.input_name
        items.append(DocItem(ref.case_id, ref.input_name, ref.document_class, sp, src, ref.reference_name))
    wanted = {"dev": {"dev", "negatives"}, "cases-dev": {"dev"}, "control": {"control"}, "negatives": {"negatives"},
              "all": {"dev", "control", "negatives"}}
    if which not in wanted:
        raise ValueError(f"nieznany zbiór: {which}")
    return [i for i in items if i.split in wanted[which]]


def reference_for(item: DocItem) -> dict[str, object]:
    """Referencyjny JSON z poprawkami organizatora; `{}` dla dokumentu obcego."""
    if item.document_class in ("obcy", "szablon"):
        return {}
    ref = CaseReference(case_id=item.case_id, input_name=item.input_name, document_class=item.document_class,  # type: ignore[arg-type]
                        reference_name=item.reference_name)
    return load_reference_json(ref)


def materialize(items: list[DocItem], root: Path = DATA_WORK) -> dict[str, Path]:
    """Kopie robocze oryginałów (`root/<case>/<plik>`); weryfikuje skrót kopii i nigdy nie pisze do źródła."""
    out: dict[str, Path] = {}
    for it in items:
        dst = root / it.case_id / it.input_name
        if not dst.is_file() or sha256_file(dst) != sha256_file(it.source):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(it.source, dst)
        assert sha256_file(dst) == sha256_file(it.source), f"kopia różni się od oryginału: {it.key}"
        out[it.key] = dst
    return out


# ---------- warianty ----------

_syn: Any = None


def _syntetyczne() -> Any:
    """Ładuje syntetyczne.py z eksperymentu przypadków brzegowych (jego `wspolne` leży obok)."""
    global _syn
    if _syn is None:
        if str(SYN_TOOLS) not in sys.path:
            sys.path.insert(0, str(SYN_TOOLS))
        spec = importlib.util.spec_from_file_location("uzp_syntetyczne", SYN_TOOLS / "syntetyczne.py")
        assert spec and spec.loader
        _syn = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_syn)
    return _syn


def render_pages(pdf: Path | bytes, dpi: int, pages: list[int] | None = None) -> list[Image.Image]:
    doc = pdfium.PdfDocument(pdf if isinstance(pdf, bytes) else str(pdf))
    try:
        idx = pages if pages is not None else range(len(doc))
        return [doc[i].render(scale=dpi / 72.0).to_pil().convert("RGB") for i in idx]
    finally:
        doc.close()


def images_to_pdf(images: list[Image.Image], out: Path, dpi: int) -> None:
    buf = io.BytesIO()
    images[0].save(buf, "PDF", resolution=dpi, save_all=True, append_images=images[1:],
                   creationDate=_FIXED_DATE, modDate=_FIXED_DATE)  # stała data: wariant ma być bajt w bajt powtarzalny
    common.write_bytes_atomic(out, buf.getvalue())


def _mixed_pdf(src: Path, out: Path, dpi: int, seed: int) -> None:
    """Strona 1 zostaje tekstowa, pozostałe jako skan (pdfium importuje strony z PDF-ów)."""
    syn = _syntetyczne()
    syn.LOS.seed(seed)
    n = len(pdfium.PdfDocument(str(src)))
    scan_pages = render_pages(src, dpi, list(range(1, n))) or render_pages(src, dpi, [0])
    scans = [syn.jak_skan(im, szum=6) for im in scan_pages]
    buf = io.BytesIO()
    scans[0].save(buf, "PDF", resolution=dpi, save_all=True, append_images=scans[1:], creationDate=_FIXED_DATE, modDate=_FIXED_DATE)
    new = pdfium.PdfDocument.new()
    new.import_pages(pdfium.PdfDocument(str(src)), [0])
    new.import_pages(pdfium.PdfDocument(buf.getvalue()))
    bio = io.BytesIO()
    new.save(bio)
    common.write_bytes_atomic(out, bio.getvalue())


def _per_page(src: Path, dpi: int, fn: Any) -> list[Image.Image]:
    return [fn(im) for im in render_pages(src, dpi)]


# nazwa → (opis, funkcja(src, out, dpi, seed))
def _variant_table() -> dict[str, tuple[str, Any, int]]:
    syn = _syntetyczne()

    def raster(dpi: int):
        def f(src: Path, out: Path, seed: int) -> None:
            syn.LOS.seed(seed)
            images_to_pdf(_per_page(src, dpi, lambda im: syn.jak_skan(im, szum=4)), out, dpi)
        return f

    def rot(angle: int):
        def f(src: Path, out: Path, seed: int) -> None:
            syn.LOS.seed(seed)
            images_to_pdf(_per_page(src, 150, lambda im: syn.jak_skan(im, szum=6).rotate(angle, expand=True)), out, 150)
        return f

    def skew(src: Path, out: Path, seed: int) -> None:
        syn.LOS.seed(seed)
        images_to_pdf(_per_page(src, 150, lambda im: syn.jak_skan(im, szum=5, kat=3.0)), out, 150)

    def lowres(src: Path, out: Path, seed: int) -> None:
        syn.LOS.seed(seed)
        images_to_pdf(_per_page(src, 72, lambda im: syn.jako_jpeg(syn.jak_skan(im.filter(ImageFilter.GaussianBlur(0.9)), szum=10), 25)), out, 72)

    def noise(src: Path, out: Path, seed: int) -> None:
        syn.LOS.seed(seed)
        images_to_pdf(_per_page(src, 150, lambda im: syn.jak_skan(im, szum=24, tlo=225)), out, 150)

    def jpeg(src: Path, out: Path, seed: int) -> None:
        syn.LOS.seed(seed)
        images_to_pdf(_per_page(src, 150, lambda im: syn.jako_jpeg(im, 30)), out, 150)

    def mixed(src: Path, out: Path, seed: int) -> None:
        _mixed_pdf(src, out, 150, seed)

    t: dict[str, tuple[str, Any, int]] = {
        "rot90": ("skan obrócony o 90°", rot(90), 150), "rot180": ("skan obrócony o 180°", rot(180), 150),
        "rot270": ("skan obrócony o 270°", rot(270), 150), "skew3": ("skan przekrzywiony o 3°", skew, 150),
        "lowres72": ("72 dpi, rozmycie, JPEG q25", lowres, 72), "noise": ("szum i szare tło (ksero)", noise, 150),
        "jpeg30": ("JPEG q30, 150 dpi", jpeg, 150), "mixed": ("strona 1 tekst, reszta skan", mixed, 150)}
    for d in RASTER_DPIS:
        t[f"raster{d}"] = (f"rasteryzacja {d} dpi (skan bez warstwy tekstowej)", raster(d), d)
    return t


def variant_names() -> list[str]:
    return list(_variant_table())


def make_variant(src: Path, kind: str, out: Path, *, seed: int) -> dict[str, Any]:
    """Tworzy wariant `kind` z `src`; zwraca rekord (źródło, skróty, parametry, ziarno). Deterministyczne dla ziarna."""
    table = _variant_table()
    if kind not in table:
        raise ValueError(f"nieznany wariant {kind}; dostępne: {sorted(table)}")
    desc, fn, dpi = table[kind]
    fn(src, out, seed)
    return {"kind": kind, "description": desc, "dpi": dpi, "seed": seed, "source": str(src), "source_sha256": sha256_file(src),
            "output": str(out), "output_sha256": sha256_file(out)}


def build_variants(items: list[DocItem], kinds: list[str], out_root: Path | None = None, *, seed: int = 20261122) -> list[dict[str, Any]]:
    """Warianty dla listy dokumentów; zapisuje `variants.json` w katalogu wyjściowym. Źródła tylko do odczytu."""
    out_root = out_root or (DATA_WORK / "variants")
    originals = materialize(items)
    records = []
    for it in items:
        for kind in kinds:
            out = out_root / kind / it.case_id / it.input_name
            rec = make_variant(originals[it.key], kind, out, seed=seed)
            rec |= {"case_id": it.case_id, "input_name": it.input_name, "document_class": it.document_class,
                    "expected_reference": it.reference_name}
            records.append(rec)
    write_json_atomic(out_root / "variants.json", {"seed": seed, "variants": records})
    return records


def describe(items: list[DocItem]) -> dict[str, Any]:
    from collections import Counter
    return {"count": len(items), "by_class": dict(Counter(i.document_class for i in items)),
            "by_split": dict(Counter(i.split for i in items)), "cases": len({i.case_id for i in items})}


def to_json(items: list[DocItem]) -> list[dict[str, Any]]:
    return [asdict(i) | {"source": str(i.source)} for i in items]
