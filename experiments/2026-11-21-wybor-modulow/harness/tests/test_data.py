"""Testy zbioru i wariantów: podział, poprawki organizatora, nietykalność oryginałów, determinizm wariantów."""

import json
from collections import Counter

import pypdfium2 as pdfium
import pytest

import data
from common import MATERIALS, sha256_file
from odwolania2json.dataset import load_split


def test_split_is_frozen_and_disjoint():
    dev, ctl = data.load_items("dev"), data.load_items("control")
    assert {i.case_id for i in dev if i.split == "dev"}.isdisjoint({i.case_id for i in ctl})
    sp = load_split()
    assert {i.case_id for i in ctl} <= sp.kontrolny
    assert all(i.split == "control" for i in ctl)
    assert not any(i.case_id == "negatywne" for i in ctl)  # negatywy tylko do strojenia
    allitems = data.load_items("all")
    assert len(allitems) == len(dev) + len(ctl) and len(allitems) > 150
    assert Counter(i.document_class for i in allitems)["obcy"] >= 12


def test_template_items_are_scans():
    t = data.load_items("template")
    assert {i.input_name for i in t} == {"negatywny przyklad.pdf", "przyklad odwolanie.pdf"}
    assert data.reference_for(t[0]) == {}


def test_reference_has_organizer_corrections_and_foreign_is_empty():
    items = {i.key: i for i in data.load_items("all")}
    assert data.reference_for(next(i for i in items.values() if i.document_class == "obcy")) == {}
    # sprawa poprawiona przez organizatora: referencja czytana z katalogu aktualizacji, nie z oryginału
    from odwolania2json.loader import CORRECTIONS_DIR
    fixed = items["przyklad_19/odwolanie.pdf"]
    corrected = json.loads((CORRECTIONS_DIR / "dane" / "przyklad_19" / "odwolanie.json").read_text(encoding="utf-8"))
    assert data.reference_for(fixed) == corrected


def test_materialize_copies_and_never_touches_originals(tmp_path):
    items = data.load_items("template")
    before = {i.key: (sha256_file(i.source), i.source.stat().st_mtime_ns) for i in items}
    out = data.materialize(items, tmp_path)
    for i in items:
        assert out[i.key].parent.parent == tmp_path and sha256_file(out[i.key]) == before[i.key][0]
        assert (sha256_file(i.source), i.source.stat().st_mtime_ns) == before[i.key]


def _one_text_item():
    return next(i for i in data.load_items("cases-dev") if i.document_class == "przelew")


def test_variant_names_cover_requirements():
    names = set(data.variant_names())
    assert {"rot90", "rot180", "rot270", "skew3", "lowres72", "noise", "jpeg30", "mixed",
            "raster100", "raster150", "raster200", "raster300"} <= names


@pytest.mark.parametrize("kind", ["raster100", "rot90", "mixed", "jpeg30"])
def test_variant_is_deterministic_and_scan_has_no_text(tmp_path, kind):
    it = _one_text_item()
    src = data.materialize([it], tmp_path / "orig")[it.key]
    a = data.make_variant(src, kind, tmp_path / "a.pdf", seed=7)
    b = data.make_variant(src, kind, tmp_path / "b.pdf", seed=7)
    assert a["output_sha256"] == b["output_sha256"] or kind == "mixed"  # mixed: pdfium dodaje znacznik czasu
    doc = pdfium.PdfDocument(str(tmp_path / "a.pdf"))
    words = [len(doc[i].get_textpage().get_text_bounded().split()) for i in range(len(doc))]
    if kind == "mixed":
        assert words[0] > 0 and (len(words) == 1 or all(w == 0 for w in words[1:]))
    else:
        assert all(w == 0 for w in words)


def test_raster_dpi_changes_pixel_size(tmp_path):
    it = _one_text_item()
    src = data.materialize([it], tmp_path / "orig")[it.key]
    sizes = {}
    for d in (100, 200):
        data.make_variant(src, f"raster{d}", tmp_path / f"r{d}.pdf", seed=1)
        img = data.render_pages(tmp_path / f"r{d}.pdf", 72)[0]
        sizes[d] = img.size
    assert sizes[100] == sizes[200]  # ten sam rozmiar strony w pt; różni się rozdzielczość obrazu w pliku
    assert (tmp_path / "r200.pdf").stat().st_size > (tmp_path / "r100.pdf").stat().st_size


def test_unknown_variant_and_set_rejected(tmp_path):
    with pytest.raises(ValueError):
        data.make_variant(tmp_path / "x.pdf", "nie_ma", tmp_path / "o.pdf", seed=1)
    with pytest.raises(ValueError):
        data.load_items("zly")


def test_build_variants_records_provenance(tmp_path):
    it = _one_text_item()
    recs = data.build_variants([it], ["rot180"], tmp_path / "v", seed=3)
    assert recs[0]["source_sha256"] == sha256_file(it.source) and recs[0]["seed"] == 3
    assert json.loads((tmp_path / "v" / "variants.json").read_text())["variants"][0]["kind"] == "rot180"


def test_variant_bytes_do_not_depend_on_wall_clock(tmp_path):
    """Regresja: PIL wpisywał bieżącą datę do PDF, więc wariant z tym samym ziarnem różnił się między sekundami."""
    import time

    it = _one_text_item()
    src = data.materialize([it], tmp_path / "orig")[it.key]
    a = data.make_variant(src, "rot90", tmp_path / "a.pdf", seed=7)["output_sha256"]
    time.sleep(1.1)
    b = data.make_variant(src, "rot90", tmp_path / "b.pdf", seed=7)["output_sha256"]
    assert a == b
