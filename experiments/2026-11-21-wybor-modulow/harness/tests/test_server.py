"""Testy serwera przez HTTP (TestClient): trasy, stany, limity, błędy jawne, brak crashu."""

import json
import time

import pytest
from fastapi.testclient import TestClient

from config import HarnessConfig
from llm import MockLlm
from pdfs import image_pdf, text_pdf
from pipeline import Modules
from server import create_app

PRZELEW = ("POLECENIE PRZELEWU Potwierdzenie realizacji polecenia przelewu Rachunek odbiorcy "
           "PL68438223049992295262834736 Kwota operacji 200,00 PLN Data transakcji 2026-03-21")


def make_client(tmp_path, **over):
    cfg = HarnessConfig(work_dir=str(tmp_path / "work"))
    for k, v in over.items():
        if k in ("max_upload_bytes", "max_pages", "document_timeout_s", "max_workers"):
            setattr(cfg.limits, k, v)
        else:
            setattr(cfg, k, v)
    return TestClient(create_app(cfg, mods=over.pop("mods", None))), cfg


def wait(c, doc_id, timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = c.get(f"/documents/{doc_id}").json()
        if r["progress"] == "done":
            return r
        time.sleep(0.05)
    raise AssertionError("timeout")


def upload(c, *pdfs, names=None):
    files = [("files", ((names or [f"d{i}.pdf" for i in range(len(pdfs))])[i], p, "application/pdf")) for i, p in enumerate(pdfs)]
    r = c.post("/batches", files=files)
    assert r.status_code == 201, r.text
    return r.json()


def test_health_and_system(tmp_path):
    c, _ = make_client(tmp_path)
    assert c.get("/health").json()["status"] == "ok"
    s = c.get("/system").json()
    assert s["ocr"]["ready"] is False and s["ocr"]["provider"]["name"] == "none" and s["paid_call_performed"] is False
    assert s["llm"]["provider"] is None and "key_file" not in json.dumps(s)


def test_text_pdf_end_to_end(tmp_path):
    c, _ = make_client(tmp_path)
    up = upload(c, text_pdf([PRZELEW[:90]], size=(600, 800)))
    st = wait(c, up["document_id"])
    assert up["batch_id"] in c.get(f"/batches/{up['batch_id']}").json()["batch_id"]
    assert st["progress"] == "done" and st["outcome"] in ("complete", "partial", "foreign", "ambiguous")
    for name in ("evidence", "report", "diagnosis", "metrics"):
        assert c.get(f"/documents/{up['document_id']}/{name}").status_code == 200


def test_bank_transfer_extracted_with_evidence(tmp_path):
    c, _ = make_client(tmp_path)
    # kilka wierszy, żeby etykiety i wartości były w osobnych liniach jak w PDF-ie organizatora
    from pdfs import text_pdf as tp
    lines = ["POLECENIE PRZELEWU", "Potwierdzenie realizacji polecenia przelewu", "Rachunek odbiorcy",
             "PL68438223049992295262834736", "Kwota operacji", "200,00 PLN", "Data transakcji", "2026-03-21"]
    pdf = _multiline(lines)
    up = upload(c, pdf)
    st = wait(c, up["document_id"])
    assert st["class_id"] == "bank_transfer", st
    res = c.get(f"/documents/{up['document_id']}/result").json()
    assert res["przelew_bankowy"]["kwota"] == 200.0 and res["przelew_bankowy"]["na_rachunek"] == "68438223049992295262834736"
    ev = c.get(f"/documents/{up['document_id']}/evidence").json()
    assert ev and all(e["bbox"] and e["words"] and e["page"] >= 1 and e["quote"] for e in ev)


def _multiline(lines):
    import io
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"]
    body = "BT /F1 14 Tf 40 760 Td 20 TL " + " ".join(f"({ln}) Tj T*" for ln in lines) + " ET"
    objs.append(f"<< /Length {len(body)} >>\nstream\n{body}\nendstream")
    objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = io.BytesIO(); out.write(b"%PDF-1.4\n"); offs = []
    for i, o in enumerate(objs, 1):
        offs.append(out.tell()); out.write(f"{i} 0 obj\n{o}\nendobj\n".encode())
    x = out.tell(); out.write(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
    for o in offs:
        out.write(f"{o:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n".encode())
    return out.getvalue()


def test_scan_without_ocr_is_technical_error_with_code(tmp_path):
    c, _ = make_client(tmp_path)
    up = upload(c, image_pdf())
    st = wait(c, up["document_id"])
    assert st["outcome"] == "technical_error" and "ocr_unavailable" in st["codes"] and st["errors"][0]["code"] == "ocr_unavailable"
    r = c.get(f"/documents/{up['document_id']}/result")
    assert r.status_code == 409 and r.json()["code"] == "result_unavailable"
    assert c.get(f"/documents/{up['document_id']}/diagnosis").json()["requires_ocr"] is True


@pytest.mark.parametrize("blob,code", [(b"to nie jest pdf", "not_a_pdf"), (b"%PDF-1.4\nuciety w polowie", "pdf_corrupted"),
                                       (b"", "not_a_pdf")])
def test_bad_inputs_are_explicit_and_server_survives(tmp_path, blob, code):
    c, _ = make_client(tmp_path)
    up = upload(c, blob)
    st = wait(c, up["document_id"])
    assert st["outcome"] == "technical_error" and st["codes"] == [code]
    assert c.get("/health").status_code == 200


def test_upload_too_large_marks_only_that_document(tmp_path):
    c, _ = make_client(tmp_path, max_upload_bytes=1000)
    big = text_pdf(["x"]) + b"0" * 5000
    up = upload(c, big, text_pdf(["Hello World"]))
    d0, d1 = up["document_ids"]
    assert wait(c, d0)["codes"] == ["upload_too_large"]
    assert wait(c, d1)["outcome"] != "technical_error" or wait(c, d1)["codes"] != ["upload_too_large"]


def test_page_limit(tmp_path):
    c, _ = make_client(tmp_path, max_pages=2)
    up = upload(c, text_pdf(["a b c"] * 3))
    assert wait(c, up["document_id"])["codes"] == ["page_limit"]


def test_unknown_ids_and_not_ready(tmp_path):
    c, _ = make_client(tmp_path)
    assert c.get("/documents/nie-ma").status_code == 404
    assert c.get("/batches/nie-ma").json()["code"] == "not_found"
    assert c.get("/documents/nie-ma/result").status_code == 404
    assert c.post("/batches").status_code == 422


def test_artifact_path_traversal_blocked(tmp_path):
    c, _ = make_client(tmp_path)
    up = upload(c, text_pdf(["Hello World"]))
    wait(c, up["document_id"])
    assert c.get(f"/documents/{up['document_id']}/artifact/../../../batch.json").status_code == 404
    assert c.get(f"/documents/{up['document_id']}/artifact/raw/reading.json").status_code == 200


def test_atomic_write_leaves_no_temp_files(tmp_path):
    c, cfg = make_client(tmp_path)
    up = upload(c, text_pdf(["Hello World"]))
    wait(c, up["document_id"])
    leftovers = [p for p in (tmp_path / "work").rglob("*") if p.suffix in (".tmp", ".part")]
    assert leftovers == []


def test_foreign_document_exports_empty_object(tmp_path):
    c, _ = make_client(tmp_path)
    up = upload(c, _multiline(["Ogloszenie o zamowieniu", "Dostawa krzesel dla biura"]))
    st = wait(c, up["document_id"])
    assert st["outcome"] == "foreign" and c.get(f"/documents/{up['document_id']}/result").json() == {}


def test_llm_router_failure_is_technical_error_not_fabricated(tmp_path):
    cfg = HarnessConfig(work_dir=str(tmp_path / "w"), router="llm")
    cfg.llm.protocol = "mock"
    cfg.llm.retries = 0
    from llm import LlmClient
    llm = LlmClient(cfg.llm, transport=MockLlm(default=("status", 429)).transport())
    c = TestClient(create_app(cfg, mods=Modules(cfg, llm=llm)))
    up = upload(c, _multiline(["PELNOMOCNICTWO", "Udzielam pelnomocnictwa"]))
    st = wait(c, up["document_id"])
    assert st["outcome"] == "technical_error" and st["codes"] == ["llm_rate_limit"] and st["class_id"] is None


def test_llm_extractor_anchors_quote_and_flags_unanchored(tmp_path):
    cfg = HarnessConfig(work_dir=str(tmp_path / "w"), router="rules", extractor="llm")
    cfg.llm.protocol = "mock"
    answer = json.dumps({"fields": [
        {"field": "/przelew_bankowy/kwota", "value": 200.0, "quote": "200,00 PLN", "page": 1},
        {"field": "/przelew_bankowy/tytul", "value": "zmyślony", "quote": "tego nie ma w dokumencie", "page": 1}]})
    from llm import LlmClient
    llm = LlmClient(cfg.llm, transport=MockLlm(default=("ok", answer)).transport())
    c = TestClient(create_app(cfg, mods=Modules(cfg, llm=llm)))
    up = upload(c, _multiline(["POLECENIE PRZELEWU", "Potwierdzenie przelewu", "Rachunek odbiorcy", "Kwota operacji", "200,00 PLN"]))
    st = wait(c, up["document_id"])
    assert st["outcome"] == "partial"  # niezakotwiczony cytat blokuje `complete`
    rep = c.get(f"/documents/{up['document_id']}/report").json()
    assert any(g["codes"] == ["evidence_unanchored"] and g["field"].endswith("tytul") for g in rep["gaps"])
    ev = c.get(f"/documents/{up['document_id']}/evidence").json()
    assert [e["field"] for e in ev] == ["/przelew_bankowy/kwota"] and ev[0]["bbox"]
    assert c.get(f"/documents/{up['document_id']}/artifact/t3/ai-response.json").status_code == 200


def test_concurrent_batch_all_documents_finish(tmp_path):
    c, _ = make_client(tmp_path, max_workers=3)
    up = upload(c, *[text_pdf([f"Hello World {i}"]) for i in range(6)])
    for d in up["document_ids"]:
        assert wait(c, d)["progress"] == "done"
    assert c.get(f"/batches/{up['batch_id']}").json()["done"] is True
