"""Testy zestawu skanów: blokada przecieku, spójność manifestu, determinizm."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_zestaw as b  # noqa: E402
from guard import LeakError, assert_dev_case, assert_manifest_clean  # noqa: E402
from odwolania2json.dataset import load_split  # noqa: E402

MANIFEST = Path(__file__).resolve().parent / "manifest.json"


def test_control_case_is_blocked():
    for c in load_split().kontrolny:
        with pytest.raises(LeakError):
            assert_dev_case(c)


def test_unknown_case_is_blocked():
    with pytest.raises(LeakError):
        assert_dev_case("przyklad_999")


def test_przyklad_40_blocked():
    with pytest.raises(LeakError):
        assert_dev_case("przyklad_40")


def test_manifest_with_control_parent_rejected():
    bad = {"entries": [{"id": "x", "case_id": "przyklad_40", "parent_split": "rozwojowy"}]}
    with pytest.raises(LeakError):
        assert_manifest_clean(bad)


def test_manifest_with_wrong_split_label_rejected():
    c = sorted(load_split().rozwojowy)[0]
    with pytest.raises(LeakError):
        assert_manifest_clean({"entries": [{"id": "x", "case_id": c, "parent_split": "kontrolny"}]})


def test_build_one_refuses_control_case():
    job = dict(case_id="przyklad_40", input_name="odwolanie.pdf", document_class="odwolanie", reference_name=None,
               source="x", variant="skan", fn="scan", profile="P1-szablon", input_kind="scan")
    with pytest.raises(LeakError):
        b.build_one(job)


def test_jobs_only_dev_cases():
    ctl = set(load_split().kontrolny)
    jobs = b.make_jobs()
    assert jobs and not ({j["case_id"] for j in jobs} & ctl)


@pytest.mark.skipif(not MANIFEST.exists(), reason="zestaw niezbudowany")
def test_manifest_clean_files_and_counts():
    from common import sha256_file
    m = json.loads(MANIFEST.read_text())
    assert_manifest_clean(m)
    root = MANIFEST.parent
    for e in m["entries"]:
        assert sha256_file(root / e["pdf"]) == e["pdf_sha256"]
        assert (root / e["ref"]).is_file()
    main = [e for e in m["entries"] if e["variant"] == "skan"]
    assert len(main) == 147 and len({e["case_id"] for e in main}) == 49


def test_deterministic_rebuild(tmp_path, monkeypatch):
    items = [i for i in b.hdata.load_items("cases-dev") if i.document_class == "przelew"][:1]
    it = items[0]
    o1, o2 = tmp_path / "a.pdf", tmp_path / "b.pdf"
    b.v_scan(it.source, o1, "P2-ksero-szare", 7)
    b.v_scan(it.source, o2, "P2-ksero-szare", 7)
    assert o1.read_bytes() == o2.read_bytes()
