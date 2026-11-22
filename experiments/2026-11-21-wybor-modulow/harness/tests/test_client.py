"""Testy klienta: faktyczny podproces serwera, metoda limitu pamięci, pomiar RSS i czasu."""

import json
import time

import pytest

from client import HarnessClient, ManagedServer, descendants, detect_limit_method, proc_status_kb
from pdfs import image_pdf, text_pdf


def test_command_wraps_with_limit():
    s = ManagedServer(port=1, limit_method="systemd-run")
    assert s.command()[:5] == ["systemd-run", "--user", "--scope", "--quiet", "-p"] and "MemoryMax=14G" in s.command()
    s = ManagedServer(port=1, limit_method="prlimit")
    assert s.command()[0] == "prlimit" and s.command()[1] == f"--as={14 * 1024**3}"
    assert ManagedServer(port=1, limit_method="none").command()[1].endswith("server.py")


def test_detect_limit_method_returns_known_value():
    assert detect_limit_method() in ("systemd-run", "prlimit", "none")


def test_proc_helpers_on_self():
    import os
    assert proc_status_kb(os.getpid(), "VmHWM") > 1000
    assert isinstance(descendants(os.getpid()), list)


@pytest.mark.slow
def test_managed_server_roundtrip_with_rss_and_timing(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"name": "test", "work_dir": str(tmp_path / "work")}))
    pdf = tmp_path / "t.pdf"
    pdf.write_bytes(text_pdf(["Hello World"]))
    with ManagedServer(cfg, log_path=tmp_path / "srv.log") as srv, HarnessClient(srv.url, server=srv) as c:
        assert c.health()["status"] == "ok"
        run = c.run_document(pdf)
        assert run["state"]["progress"] == "done"
        assert run["artifacts"]["diagnosis"]["http"] == 200
        assert 20 < run["peak_rss_mb"] < 4000 and run["timing"]["wall_s"] > 0
        assert run["limit_method"] == srv.limit_method


@pytest.mark.slow
def test_server_survives_garbage_and_reports_kill9(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"work_dir": str(tmp_path / "work")}))
    srv = ManagedServer(cfg, log_path=tmp_path / "srv.log").start()
    try:
        with HarnessClient(srv.url, server=srv) as c:
            up = c.upload([("zly.pdf", b"nie pdf"), ("skan.pdf", image_pdf())])
            for d in up["document_ids"]:
                assert c.wait_done(d)["outcome"] == "technical_error"
            assert c.health()["status"] == "ok"
    finally:
        srv.kill9()
    assert srv.proc is None and (srv.peak_rss_kb or 0) > 0
