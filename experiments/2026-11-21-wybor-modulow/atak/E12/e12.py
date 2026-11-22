"""E12: złośliwe i uszkodzone wejścia (upload, ścieżki, zasoby, bomby PDF, SSRF z PDF, ReDoS, nagłówki/CSRF, XSS).

Uruchomienie (jedno polecenie, z korzenia repozytorium):
    .venv-exp/bin/python experiments/2026-11-21-wybor-modulow/atak/E12/e12.py [--only grupa,grupa] [--skip grupa]
Wynik: atak/E12/wyniki.json (surowe liczby i werdykty wektorów). Wynik opisuje UPRZĄŻ, nie produkt.
Klucz LLM nie jest tu używany (router/ekstraktor regułowy).
"""

from __future__ import annotations

import argparse
import http.server
import io
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import *  # noqa: F401,F403,E402
import lib  # noqa: E402

EXPN = "E12"
WORKDIR = SANDBOX / EXPN


def srv_dir(g: str) -> Path:
    return WORKDIR / g


def snap_roots(work: Path) -> list[Path]:
    """Gdzie szukamy plików powstałych poza obszarem pracy serwera: katalog nadrzędny sandboxa i katalog uprzęży."""
    return [work.parent, HARNESS]


def outside_new(before: dict, after: dict, work_data: Path) -> list[str]:
    d = snap_diff(before, after)
    wd = str(work_data)
    ignore = ("server.log", ".config.json", "wyniki")
    return [p for p in d["added"] + d["changed"] if not p.startswith(wd) and not any(i in p for i in ignore)
            and "__pycache__" not in p]


# ===================================================================== G1: nazwy plików w uploadzie
def g_names() -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    pdf = dev_pdf("przelew", 0)
    with running("names", srv_dir("names")) as (srv, c):
        work_data: Path = srv.work  # type: ignore[attr-defined]
        long_name = "a" * 300 + ".pdf"
        cases: list[tuple[str, str, bytes | str]] = [
            ("N01", "traversal ../../x.json", "../../x.json"),
            ("N02", "ścieżka bezwzględna /etc/cron.d/x", "/etc/cron.d/x.pdf"),
            ("N03", "separator Windows ..\\..\\x.pdf", "..\\..\\evil.pdf"),
            ("N04", "kodowanie %2e%2e%2f", "%2e%2e%2f%2e%2e%2fevil.pdf"),
            ("N05", "NUL w nazwie", b"ok\x00.pdf"),
            ("N06", "zarezerwowane CON/NUL", "CON.pdf"),
            ("N07", "300 znaków", long_name),
            ("N08", "Unicode NFD", "záżół́c.pdf"),
            ("N09", "podfolder a/../../b", "a/../../b.pdf"),
            ("N10", "pusta nazwa", ""),
            ("N11", "nazwa z CRLF i znacznikami HTML", "x\r\nSet-Cookie: a=b<img src=x onerror=alert(1)>.pdf"),
            ("N12", "nazwa zaczynająca się od kropki (ukryty plik)", ".htaccess"),
        ]
        for vid, name, fn in cases:
            before = snapshot(snap_roots(work_data))
            body, ctype = raw_multipart([{"name": "files", "filename": fn, "data": pdf, "ctype": "application/pdf"}])
            r = c.http.post("/batches", content=body, headers={"Content-Type": ctype}, timeout=60)
            info: dict[str, Any] = {"http": r.status_code}
            ok_state = None
            if r.status_code == 201:
                j = r.json()
                info["stored_filename"] = j["documents"][0]["filename"]
                st = doc_state(c, j["document_id"], 60)
                ok_state = st.get("outcome")
                info["outcome"] = ok_state
                disk = sorted(p.name for p in (work_data / j["batch_id"] / "documents" / j["document_id"]).iterdir())
                info["on_disk"] = disk
            after = snapshot(snap_roots(work_data))
            leaked = outside_new(before, after, work_data)
            info["outside_new_files"] = leaked
            silent_fix = r.status_code == 201 and info.get("stored_filename") != (fn if isinstance(fn, str) else None)
            gap = "tak" if leaked else ("częściowo" if silent_fix else "nie")
            actual = (f"HTTP {r.status_code}; zapisana nazwa={info.get('stored_filename')!r}; pliki na dysku={info.get('on_disk')}; "
                      f"poza obszarem pracy: {len(leaked)}")
            recs.append(vec(vid, "upload-nazwa", name, "brak zapisu poza obszarem pracy; nazwa odrzucona jawnie (architektura §7), nie naprawiona po cichu",
                            actual + ("; nazwa naprawiana po cichu (ścieżka zawsze input.pdf)" if silent_fix else ""), gap,
                            fix="Odrzucić nazwę z separatorem/NUL/kontrolnymi (422 `invalid_filename`) zamiast czyścić; ścieżkę dysku budować wyłącznie z ID (jak teraz).",
                            port_test="test_upload_filename_variants_never_write_outside_workdir (parametryzowany listą N01–N12)", data=info))
        # duplikaty i wielkość liter
        names = [("A.pdf", "a.pdf"), ("dup.pdf", "dup.pdf"), ("sub1/same.pdf", "sub2/same.pdf")]
        for vid, (n1, n2) in zip(("N13", "N14", "N15"), names, strict=True):
            r = c.http.post("/batches", files=[("files", (n1, pdf, "application/pdf")), ("files", (n2, pdf, "application/pdf"))])
            j = r.json()
            ids = j["document_ids"]
            sts = [doc_state(c, i, 60).get("outcome") for i in ids]
            fns = [d["filename"] for d in j["documents"]]
            recs.append(vec(vid, "upload-nazwa", f"duplikat/wielkość liter: {n1} + {n2}", "dwa osobne dokumenty, brak nadpisania, mapowanie wejście→wynik zachowane",
                            f"ids={ids} unikalne={len(set(ids)) == 2}; nazwy={fns}; wyniki={sts}", "nie" if len(set(ids)) == 2 and all(sts) else "tak",
                            fix="Zachować oryginalną nazwę w metadanych (UTF-8) obok ID; porównywać wielkość liter przy raportowaniu duplikatów.",
                            port_test="test_same_basename_two_documents_get_distinct_ids_and_results"))
        # przerwany upload (połączenie zamknięte w połowie)
        time.sleep(1.5)
        before = snapshot(snap_roots(work_data))
        body, ctype = raw_multipart([{"name": "files", "filename": "przerwany.pdf", "data": pdf, "ctype": "application/pdf"}])
        s = socket.create_connection(("127.0.0.1", srv.port))
        s.sendall((f"POST /batches HTTP/1.1\r\nHost: x\r\nContent-Type: {ctype}\r\nContent-Length: {len(body)}\r\n\r\n").encode() + body[: len(body) // 2])
        s.close()
        time.sleep(2)
        after = snapshot(snap_roots(work_data))
        partial_docs = [p for p in snap_diff(before, after)["added"] if p.endswith("input.pdf") or p.endswith("input.pdf.part")]
        recs.append(vec("N16", "upload-nazwa", "przerwany upload (zamknięcie połączenia w połowie ciała)", "brak częściowego dokumentu przetwarzanego jako wynik",
                        f"pliki input* po przerwaniu: {[Path(p).name for p in partial_docs]}; /health={c.http.get('/health').status_code}",
                        "nie" if not partial_docs else "tak",
                        fix="Wsad zapisywać w katalogu tymczasowym i przenosić atomowo po pełnym przyjęciu; sprzątać `.part` przy starcie.",
                        port_test="test_aborted_upload_leaves_no_batch_or_part_files"))
        recs.append({"_probe": probe_ok(c)})
    return recs


# ===================================================================== G2: typ pliku / magia / poliglot
def g_types() -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    pdf = dev_pdf("przelew", 0)
    from PIL import Image
    png = io.BytesIO()
    Image.new("RGB", (40, 40), "white").save(png, "PNG")
    zip_ = io.BytesIO()
    import zipfile
    with zipfile.ZipFile(zip_, "w") as z:
        z.writestr("a.txt", "x" * 100)
    empty_pages = pdf_from_objects([b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [] /Count 0 >>"])
    cases: list[tuple[str, str, bytes, str, str]] = [
        ("T01", "plik 0 bajtów", b"", "x.pdf", "not_a_pdf|empty_document"),
        ("T02", "sam nagłówek %PDF-1.7", b"%PDF-1.7\n", "x.pdf", "pdf_corrupted"),
        ("T03", "PNG z Content-Type application/pdf i nazwą .pdf", png.getvalue(), "x.pdf", "not_a_pdf"),
        ("T04", "nagłówek HTML + treść", b"<html><script>alert(1)</script></html>", "x.pdf", "not_a_pdf"),
        ("T05", "%PDF po 1 MB śmieci (poza oknem 1024 B)", b"\0" * (1 << 20) + pdf, "x.pdf", "not_a_pdf"),
        ("T06", "poliglot PDF + ZIP doklejony na końcu", pdf + zip_.getvalue(), "x.zip", "complete|partial"),
        ("T07", "śmieci przed %PDF w oknie 1024 B", b"JUNK" * 100 + pdf, "x.pdf", "complete|partial"),
        ("T08", "obcięty PDF (połowa bajtów)", pdf[: len(pdf) // 2], "x.pdf", "pdf_corrupted"),
        ("T09", "PDF z 0 stron (Count 0)", empty_pages, "x.pdf", "empty_document"),
        ("T10", "dobry PDF z rozszerzeniem .exe i MIME text/plain", pdf, "x.exe", "complete|partial"),
        ("T11", "zaszyfrowany PDF (słownik /Encrypt, hasło użytkownika)", encrypted_stub(), "x.pdf", "pdf_encrypted"),
    ]
    with running("types", srv_dir("types")) as (srv, c):
        for vid, name, data, fname, expect in cases:
            r = c.http.post("/batches", files=[("files", (fname, data, "text/plain" if fname.endswith(".exe") else "application/pdf"))])
            if r.status_code != 201:
                recs.append(vec(vid, "typ-pliku", name, expect, f"HTTP {r.status_code} {r.text[:80]}", "nie"))
                continue
            st = doc_state(c, r.json()["document_id"], 60)
            got = st.get("outcome") if st.get("outcome") in ("complete", "partial") else (st.get("codes") or [st.get("outcome")])[0]
            ok = got in expect.split("|") or (got == "technical_error")
            recs.append(vec(vid, "typ-pliku", name, f"kod: {expect}", f"outcome={st.get('outcome')} kody={st.get('codes')}",
                            "nie" if (st.get("outcome") == "technical_error" or got in expect.split("|")) else "tak",
                            fix="Walidować magię i strukturę niezależnie od rozszerzenia i MIME; kod błędu stabilny.",
                            port_test=f"test_input_type_matrix[{vid}]", data={"expected": expect, "got": got, "state_ok": ok}))
        recs.append({"_probe": probe_ok(c)})
    return recs


def encrypted_stub() -> bytes:
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>"]
    o = "<" + "ab" * 32 + ">"
    u = "<" + "cd" * 32 + ">"
    enc = f"<< /Filter /Standard /V 1 /R 2 /O {o} /U {u} /P -4 >>".encode()
    objs.append(enc)
    return pdf_from_objects(objs, trailer_extra=b"/Encrypt 4 0 R /ID [<0123456789abcdef0123456789abcdef><0123456789abcdef0123456789abcdef>]")


# ===================================================================== G3: ścieżki, IDOR, nagłówki, XSS
def g_paths() -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    pdf = dev_pdf("przelew", 0)
    pdf2 = dev_pdf("przelew", 1)
    canary_dir = WORKDIR / "outside"
    canary_dir.mkdir(parents=True, exist_ok=True)
    canary = "CANARY-" + secrets.token_hex(8)
    (canary_dir / "tajne.json").write_text(json.dumps({"k": canary}))
    with running("paths", srv_dir("paths")) as (srv, c):
        work: Path = srv.work  # type: ignore[attr-defined]
        r = c.http.post("/batches", files=[("files", ("a.pdf", pdf, "application/pdf"))])
        j = r.json()
        did, bid = j["document_id"], j["batch_id"]
        doc_state(c, did, 60)
        r2 = c.http.post("/batches", files=[("files", ("b.pdf", pdf2, "application/pdf"))])
        j2 = r2.json()
        doc_state(c, j2["document_id"], 60)
        # P01: ../ w ścieżce artefaktu
        payloads = ["../../../../../../etc/passwd", "..%2f..%2f..%2fetc%2fpasswd", "%2e%2e/%2e%2e/x.json", "/etc/passwd",
                    "raw/../../../../outside/tajne.json", "....//....//x.json", "raw/reading.json%00.png", "..\\..\\x.json"]
        res = []
        for p in payloads:
            try:
                rr = c.http.get(f"/documents/{did}/artifact/{p}")
                res.append({"payload": p, "http": rr.status_code, "leak": canary in rr.text or "root:" in rr.text})
            except httpx.HTTPError as e:  # np. serwer zrywa połączenie po nieobsłużonym wyjątku (NUL w ścieżce → ValueError)
                res.append({"payload": p, "http": f"błąd:{type(e).__name__}", "leak": False})
        recs.append(vec("P01", "odczyt-ścieżek", "traversal w /documents/{id}/artifact/{name:path} (8 kodowań)", "404, brak odczytu plików spoza katalogu przebiegu",
                        f"statusy={[x['http'] for x in res]}; wycieki={sum(x['leak'] for x in res)}; nieobsłużony wyjątek (500/zerwane połączenie) dla {sum(1 for x in res if not isinstance(x['http'], int) or x['http'] >= 500)} z {len(res)} ładunków", "tak" if any(x["leak"] for x in res) else ("częściowo" if any(not isinstance(x['http'], int) or x['http'] >= 500 for x in res) else "nie"),
                        fix="Trasa surowych artefaktów nie powinna istnieć w produkcie; jeśli tak, lista dozwolonych nazw zamiast ścieżki.",
                        port_test="test_artifact_route_rejects_traversal_encodings", data={"cases": res}))
        # P02: symlink do kanarka poza workspace, w katalogu przebiegu
        run_dir = work / bid / "documents" / did / "runs" / "r1"
        link = run_dir / "raw" / "link.json"
        link.symlink_to(canary_dir / "tajne.json")
        rr = c.http.get(f"/documents/{did}/artifact/raw/link.json")
        # symlink do pliku w innym dokumencie (poza r1 tego dokumentu)
        link2 = run_dir / "raw" / "cudzy.json"
        link2.symlink_to(work / j2["batch_id"] / "documents" / j2["document_id"] / "runs" / "r1" / "raw" / "reading.json")
        rr2 = c.http.get(f"/documents/{did}/artifact/raw/cudzy.json")
        # symlink do katalogu
        (run_dir / "raw" / "dirlink").symlink_to(canary_dir)
        rr3 = c.http.get(f"/documents/{did}/artifact/raw/dirlink/tajne.json")
        recs.append(vec("P02", "odczyt-ścieżek", "symlink w katalogu przebiegu: do pliku-kanarka poza workspace, do cudzego dokumentu, do katalogu", "żaden nie jest odczytany",
                        f"plik poza: HTTP {rr.status_code} wyciek={canary in rr.text}; cudzy dokument: HTTP {rr2.status_code} wyciek={'pages' in rr2.text}; katalog: HTTP {rr3.status_code} wyciek={canary in rr3.text}",
                        "tak" if (canary in rr.text or 'pages' in rr2.text or canary in rr3.text) else "nie",
                        fix="resolve() + sprawdzenie prefiksu (jest) oraz odmowa gdy któryś element ścieżki jest symlinkiem (lstat) lub open z O_NOFOLLOW.",
                        port_test="test_symlink_inside_run_dir_is_not_followed",
                        data={"outside": rr.status_code, "foreign_doc": rr2.status_code, "dir": rr3.status_code}))
        # P03: ID jako ścieżka / enumeracja / IDOR
        idp = [f"..%2f{did}", "../batches", f"{did}/../{did}", "%2e%2e%2f", did + "%00", "b000000000000-d001"]
        stat = [c.http.get(f"/documents/{p}").status_code for p in idp]
        # IDOR: dokument innego wsadu dostępny bez żadnej tożsamości
        cross = c.http.get(f"/documents/{j2['document_id']}/result").status_code
        recs.append(vec("P03", "IDOR", "identyfikatory jako ścieżka i dostęp do cudzego wsadu", "ID = nieprzewidywalny losowy token; brak traktowania ID jako ścieżki",
                        f"ID-ścieżki → {stat}; wynik cudzego wsadu bez tożsamości: HTTP {cross}; batch_id={bid} ({len(bid)-1} hex = {4*(len(bid)-1)} bit entropii), document_id=batch_id+'-d00N' (sekwencyjny sufiks)",
                        "częściowo" if cross == 200 else "nie",
                        fix="MVP bez logowania: ID ≥128 bit (secrets.token_urlsafe(16)); zapis w ADR, że brak izolacji użytkowników jest świadomy; przy dodaniu użytkowników sprawdzać właściciela wsadu.",
                        port_test="test_ids_have_128_bit_entropy_and_unknown_id_is_404"))
        # P04: wyciek ścieżek hosta
        sysj = c.http.get("/system").json()
        bad = c.http.get("/documents/nieistnieje").text
        pv = c.http.post("/batches", content=b"x", headers={"Content-Type": "multipart/form-data; boundary=zzz"}).text
        host_path_hits = {"/system": str(srv.work.parent) in json.dumps(sysj) or "/tmp/" in json.dumps(sysj), "404": "/tmp/" in bad, "422": "/tmp/" in pv}
        recs.append(vec("P04", "odczyt-ścieżek", "ujawnienie ścieżek hosta w /system i w błędach", "brak ścieżek hosta w odpowiedziach",
                        f"ścieżka w odpowiedzi: {host_path_hits}", "tak" if any(host_path_hits.values()) else "nie",
                        fix="W /system podawać wersje i gotowość, bez `work_dir` i ścieżki pliku klucza.", port_test="test_system_and_errors_do_not_expose_host_paths"))
        # P05: nagłówki, CSRF, Host, CORS
        hdr = {"Host": "evil.example", "Origin": "http://evil.example"}
        r_h = c.http.get("/health", headers=hdr)
        body, ctype = raw_multipart([{"name": "files", "filename": "csrf.pdf", "data": pdf, "ctype": "application/pdf"}])
        r_csrf = c.http.post("/batches", content=body, headers={"Content-Type": ctype, "Origin": "http://evil.example", "Referer": "http://evil.example/form.html", "Host": "evil.example"})
        r_opt = c.http.options("/batches", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
        acao = r_csrf.headers.get("access-control-allow-origin")
        recs.append(vec("P05", "wiązanie/CSRF", "Host: evil.example, Origin obcy, formularz bez preflight", "odrzucenie żądania z obcym Host/Origin; brak wsadu z formularza obcej strony",
                        f"Host evil → HTTP {r_h.status_code}; POST multipart z obcym Origin → HTTP {r_csrf.status_code} (wsad utworzony); OPTIONS → {r_opt.status_code}; ACAO={acao}",
                        "tak" if r_csrf.status_code == 201 else "nie",
                        fix="Middleware: dopuszczać tylko Host ∈ {127.0.0.1:PORT, localhost:PORT}; odrzucać Origin spoza listy; wymagać nagłówka niestandardowego (np. X-Requested-With) lub tokenu sesji dla POST.",
                        port_test="test_post_with_foreign_origin_or_host_is_rejected"))
        # P06: XSS / typ treści
        xss_pdf = text_pdf(["Potwierdzenie przelewu", "<script>alert(1)</script> <img src=x onerror=alert(2)>"])
        up = c.http.post("/batches", files=[("files", ("<img src=x onerror=alert(1)>.pdf", xss_pdf, "application/pdf"))])
        jj = up.json()
        doc_state(c, jj["document_id"], 60)
        ev = c.http.get(f"/documents/{jj['document_id']}/artifact/raw/reading.json")
        hdrs = {k.lower(): v for k, v in ev.headers.items()}
        recs.append(vec("P06", "XSS", "HTML/JS w nazwie pliku i treści PDF: czy wraca nieescapowane w JSON i jaki Content-Type", "Content-Type: application/json + nosniff; nazwa oczyszczona; ucieczka w GUI",
                        f"nazwa zapisana={jj['documents'][0]['filename']!r}; treść z <script> w odpowiedzi surowa={('<script>' in ev.text)}; content-type={hdrs.get('content-type')}; nosniff={hdrs.get('x-content-type-options')}",
                        "częściowo",
                        fix="Dodać `X-Content-Type-Options: nosniff` i `Content-Security-Policy: default-src 'none'` do odpowiedzi API; GUI renderuje tekst dokumentu wyłącznie jako tekst (textContent), nie innerHTML; test w GUI.",
                        port_test="test_api_responses_have_nosniff_and_json_content_type; GUI: test_document_text_rendered_as_text_not_html",
                        data={"headers": {k: hdrs.get(k) for k in ("content-type", "x-content-type-options", "content-security-policy", "content-disposition")}}))
        recs.append({"_probe": probe_ok(c)})
    return recs


def text_pdf(lines: list[str], size: int = 10) -> bytes:
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    ops = ["BT", f"/F1 {size} Tf", f"{size + 2} TL", "40 800 Td"]
    for ln in lines:
        ops.append(f"({esc(ln)}) Tj T*")
    ops.append("ET")
    return simple_page_pdf("\n".join(ops).encode("latin-1", "replace"))


# ===================================================================== G4: wyczerpanie zasobów przy przyjmowaniu
def _chunked_stream(total: int, boundary: str, filename: str):
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{filename}\"\r\nContent-Type: application/pdf\r\n\r\n").encode()
    yield head
    left = total
    chunk = b"%PDF-1.7\n" + b"A" * ((1 << 20) - 9)
    while left > 0:
        k = min(left, len(chunk))
        yield chunk[:k]
        chunk = b"A" * (1 << 20)
        left -= k
    yield f"\r\n--{boundary}--\r\n".encode()


def g_flood() -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    with running("flood", srv_dir("flood")) as (srv, c):
        work: Path = srv.work  # type: ignore[attr-defined]
        du0 = disk_used("/tmp")
        # F01: strumień bez Content-Length (chunked), 1 GiB
        total = 1 << 30
        b = "----flood"
        t0 = time.monotonic()
        peak_tmp = 0
        stop = threading.Event()

        def watch() -> None:
            nonlocal peak_tmp
            while not stop.is_set():
                peak_tmp = max(peak_tmp, disk_used("/tmp") - du0)
                time.sleep(0.25)
        th = threading.Thread(target=watch, daemon=True)
        th.start()
        try:
            r = c.http.post("/batches", content=_chunked_stream(total, b, "ogromny.pdf"), headers={"Content-Type": f"multipart/form-data; boundary={b}"}, timeout=600)
            code, body = r.status_code, r.text
        except httpx.HTTPError as e:
            code, body = None, type(e).__name__
        wall = time.monotonic() - t0
        stop.set()
        th.join()
        j = json.loads(body) if code == 201 else {}
        outcome = None
        if code == 201:
            st = doc_state(c, j["document_ids"][0], 60)
            outcome = (st.get("outcome"), st.get("codes"))
        recs.append(vec("F01", "zasoby-upload", "1 GiB strumieniowo bez Content-Length (chunked), limit uprzęży 30 MiB", "413 przed wczytaniem całości; RSS i dysk bez wzrostu proporcjonalnego do rozmiaru",
                        f"HTTP {code}; po {wall:.1f} s; stan dokumentu={outcome}; szczyt zajętego /tmp (tmpfs=RAM) ≈ {peak_tmp / 1048576:.0f} MiB; RSS drzewa serwera {srv.usage()['peak_rss_tree_mb']} MiB",
                        "tak" if wall > 5 or peak_tmp > 200 * 1048576 else "częściowo",
                        fix="Limit na poziomie ciała (reverse proxy/middleware ASGI: przerwać po przekroczeniu `max_upload_bytes`, nie czytać reszty); `Content-Length` > limit → 413 natychmiast; spool poza tmpfs.",
                        port_test="test_oversized_chunked_upload_aborted_with_413_without_reading_all",
                        data={"http": code, "wall_s": round(wall, 2), "peak_tmp_mib": round(peak_tmp / 1048576), "total_sent_mib": total >> 20, **srv.usage()}))
        recs.append({"_probe": probe_ok(c)})
        # F02: 1001 małych części
        parts = [{"name": "files", "filename": f"{i}.pdf", "data": b"%PDF-1.4 x", "ctype": "application/pdf"} for i in range(1001)]
        r = post_raw(c, parts)
        recs.append(vec("F02", "zasoby-upload", "1001 małych części multipart (starlette: max_files=1000)", "odmowa (400/413) bez przetwarzania części",
                        f"HTTP {r.status_code} {r.text[:100]}", "nie" if r.status_code in (400, 413, 422) else "tak",
                        fix="Jawny limit liczby plików z kodem `upload_too_large` (jest `max_batch_documents`=500, ale middleware starlette odrzuca wcześniej z 400 bez kodu API).",
                        port_test="test_too_many_parts_returns_documented_error_code"))
        # F03: duże pole formularza (nie plik): 100 MB
        big = b"x" * (100 << 20)
        parts = [{"name": "komentarz", "filename": None, "data": big}]
        t0 = time.monotonic()
        r = post_raw(c, parts)
        recs.append(vec("F03", "zasoby-upload", "pole formularza 100 MB (nie plik)", "413/400 bez wczytania całości",
                        f"HTTP {r.status_code} {r.text[:90]} po {time.monotonic() - t0:.1f} s; RSS {srv.usage()['peak_rss_tree_mb']} MiB", "nie" if r.status_code in (400, 413, 422) else "tak",
                        fix="Odrzucać nieznane pola formularza; limit rozmiaru pola.", port_test="test_unknown_large_form_field_rejected"))
        # F04: wolni klienci: 50 połączeń, 1 bajt/s przez 25 s
        socks = []
        for _ in range(50):
            s = socket.create_connection(("127.0.0.1", srv.port))
            s.sendall(b"POST /batches HTTP/1.1\r\nHost: x\r\nContent-Type: multipart/form-data; boundary=zz\r\nContent-Length: 100000000\r\n\r\n--zz\r\n")
            socks.append(s)
        t_end = time.monotonic() + 25
        lat = []
        while time.monotonic() < t_end:
            for s in socks:
                try:
                    s.send(b"x")
                except OSError:
                    pass
            t0 = time.monotonic()
            try:
                lat.append(round(c.http.get("/health", timeout=10).elapsed.total_seconds(), 4))
            except httpx.HTTPError:
                lat.append(None)
            time.sleep(1)
        pr = probe_ok(c)
        for s in socks:
            s.close()
        recs.append(vec("F04", "zasoby-upload", "50 wolnych połączeń (1 B/s, Content-Length 100 MB) przez 25 s", "serwer obsługuje poprawne żądania; połączenia odcięte po limicie bezczynności",
                        f"/health: max {max([x for x in lat if x] or [0])} s, błędy {sum(1 for x in lat if x is None)}; kontrola poprawnego dokumentu={pr}; połączenia nie zostały odcięte przez serwer w 25 s",
                        "częściowo" if pr["alive"] else "tak",
                        fix="uvicorn `--timeout-keep-alive` nie obejmuje ciała; dodać limit czasu odczytu ciała (reverse proxy) i limit równoległych połączeń na upload.",
                        port_test="test_slow_upload_connections_do_not_block_valid_requests", data={"health_latencies_s": lat, "probe": pr}))
        recs.append({"_usage": srv.usage()})
    return recs


def disk_used(path: str) -> int:
    st = os.statvfs(path)
    return (st.f_blocks - st.f_bfree) * st.f_frsize


# ===================================================================== G5: bomby PDF (każda na osobnym serwerze, limit 6 GB)
def bomb_pdfs() -> list[tuple[str, str, str, Any]]:
    """(id, nazwa, oczekiwanie, funkcja budująca PDF) — budowa leniwa (duże pliki)."""
    def flate_content(n: int):
        def f() -> bytes:
            data = zeros_flate(n)
            objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R >>",
                    f"<< /Length {len(data)} /Filter /FlateDecode >>\nstream\n".encode() + data + b"\nendstream"]
            return pdf_from_objects(objs)
        return f

    def huge_page() -> bytes:
        img = b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceGray /BitsPerComponent 8 /Length 1 >>\nstream\n\xff\nendstream"
        cont = stream_obj("", b"q 14400 0 0 14400 0 0 cm /Im0 Do Q")
        return pdf_from_objects([b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                                 b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 14400 14400] /Contents 4 0 R /Resources << /XObject << /Im0 5 0 R >> >> >>", cont, img])

    def big_flate_image(side: int):
        def f() -> bytes:
            data = zeros_flate(side * side)
            img = f"<< /Type /XObject /Subtype /Image /Width {side} /Height {side} /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode /Length {len(data)} >>\nstream\n".encode() + data + b"\nendstream"
            cont = stream_obj("", b"q 595 0 0 842 0 0 cm /Im0 Do Q")
            return pdf_from_objects([b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                                     b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /XObject << /Im0 5 0 R >> >> >>", cont, img])
        return f

    def big_jpeg(side: int):
        def f() -> bytes:
            from PIL import Image
            im = Image.new("L", (side, side), 255)
            b = io.BytesIO()
            im.save(b, "JPEG", quality=30)
            del im
            data = b.getvalue()
            img = f"<< /Type /XObject /Subtype /Image /Width {side} /Height {side} /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /DCTDecode /Length {len(data)} >>\nstream\n".encode() + data + b"\nendstream"
            cont = stream_obj("", b"q 595 0 0 842 0 0 cm /Im0 Do Q")
            return pdf_from_objects([b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                                     b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /XObject << /Im0 5 0 R >> >> >>", cont, img])
        return f

    def many_pages(n: int):
        def f() -> bytes:
            kids = " ".join(f"{i + 3} 0 R" for i in range(n))
            objs = [b"<< /Type /Catalog /Pages 2 0 R >>", f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode()]
            objs += [b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 10 10] >>"] * n
            return pdf_from_objects(objs)
        return f

    def cyclic_kids() -> bytes:
        return pdf_from_objects([b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [2 0 R 3 0 R] /Count 2 /Parent 2 0 R >>",
                                 b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>"])

    def nested_forms() -> bytes:
        objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Contents 4 0 R /Resources << /XObject << /Fm 5 0 R >> >> >>",
                stream_obj("", b"/Fm Do"),
                stream_obj("/Type /XObject /Subtype /Form /BBox [0 0 100 100] /Resources << /XObject << /Fm 5 0 R >> >>", b"/Fm Do /Fm Do")]
        return pdf_from_objects(objs)

    def deep_nesting() -> bytes:
        d = 200000
        body = b"[" * d + b"]" * d
        return pdf_from_objects([b"<< /Type /Catalog /Pages 2 0 R /X 5 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                                 b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>", b"<< >>", body])

    def many_objects() -> bytes:
        n = 400000
        objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>", b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>"]
        objs += [b"<< /A 1 >>"] * n
        return pdf_from_objects(objs)

    def many_ops() -> bytes:
        ops = (b"q 1 0 0 1 0 0 cm Q " * 4000000)  # ~76 MB treści strony: poniżej limitu uploadu? sprawdzane przez serwer
        return simple_page_pdf(ops[: 25 * 1024 * 1024], flate_content=True)

    return [
        ("B01", "strumień Flate 1 MB → ~1 GiB treści strony", "technical_error w limicie, bez OOM", flate_content(1 << 30)),
        ("B02", "strumień Flate → 4 GiB treści strony", "technical_error w limicie, bez OOM", flate_content(4 << 30)),
        ("B03", "strona 14400×14400 pt (200 dpi ⇒ 40 000² px) jako skan", "odrzucenie przed renderem lub limit pikseli", huge_page),
        ("B04", "obraz Flate deklarujący 60 000² (3,6 GB po dekompresji)", "limit pikseli obrazu", big_flate_image(60000)),
        ("B05", "obraz JPEG (DCT) 30 000² (0,9 Gpx)", "limit pikseli obrazu", big_jpeg(30000)),
        ("B06", "50 000 pustych stron", "page_limit natychmiast", many_pages(50000)),
        ("B07", "cykliczne /Kids", "pdf_corrupted bez zawieszenia", cyclic_kids),
        ("B08", "samoodwołujący się XObject Form (/Fm Do)", "brak zawieszenia, limit głębokości", nested_forms),
        ("B09", "obiekt zagnieżdżony na 200 000 poziomów", "pdf_corrupted bez przepełnienia stosu", deep_nesting),
        ("B10", "400 000 małych obiektów", "limit czasu/pamięci, bez zawieszenia", many_objects),
        ("B11", "25 MB (po kompresji) operatorów graficznych", "limit czasu, bez zawieszenia", many_ops),
    ]


def run_bomb(item: tuple[str, str, str, Any], mem: str = "6G", wait_s: float = 120.0) -> dict[str, Any]:
    vid, name, expect, builder = item
    t_build = time.monotonic()
    data = builder()
    build_s = time.monotonic() - t_build
    rec: dict[str, Any] = {"pdf_bytes": len(data), "build_s": round(build_s, 1), "memory_max": mem}
    with flock_cpu_optional():
        with running(f"bomb-{vid}", srv_dir(f"bomb-{vid}"), memory_max=mem) as (srv, c):
            t0 = time.monotonic()
            r = None
            try:
                r = c.http.post("/batches", files=[("files", ("bomba.pdf", data, "application/pdf"))], timeout=120)
            except httpx.HTTPError as e:
                rec["upload_error"] = type(e).__name__
            outcome, codes, hung = None, None, False
            if r is not None and r.status_code == 201:
                did = r.json()["document_id"]
                t_wait = time.monotonic()
                while time.monotonic() - t_wait < wait_s:
                    if not srv.alive():
                        break
                    try:
                        st = c.http.get(f"/documents/{did}", timeout=5).json()
                    except httpx.HTTPError:
                        time.sleep(0.3)
                        continue
                    if st["progress"] == "done":
                        outcome, codes = st["outcome"], st["codes"]
                        break
                    time.sleep(0.2)
                else:
                    hung = True
            elif r is not None:
                outcome, codes = f"HTTP {r.status_code}", [r.text[:80]]
            wall = time.monotonic() - t0
            died = not srv.alive()
            rec.update({"wall_s": round(wall, 2), "outcome": outcome, "codes": codes, "hung_over_wait": hung, "server_died": died,
                        "returncode": srv.proc.poll() if srv.proc else None, **srv.usage()})
            if not died:
                srv_peak_after = srv.cgroup_peak_mb()
                if hung:
                    rec["probe_after"] = {"note": "serwer ma 1 wątek roboczy zablokowany; kontrola poprawnego dokumentu ma limit 30 s"}
                    pr = quick_probe(c, 30)
                else:
                    pr = quick_probe(c, 60)
                rec["probe_after"] = pr
                rec["cgroup_peak_mb"] = srv_peak_after
            else:
                rec["probe_after"] = {"alive": False}
    return rec


def flock_cpu_optional():
    return contextlib.nullcontext()


def quick_probe(c: HarnessClient, timeout: float) -> dict[str, Any]:
    try:
        h = c.http.get("/health", timeout=5).status_code
    except httpx.HTTPError as e:
        return {"health": type(e).__name__, "alive": False}
    st = upload_and_wait(c, dev_pdf("przelew", 0), "kontrola.pdf", timeout=timeout)
    return {"health": h, "clean_doc": st.get("outcome") or st.get("progress"), "alive": st.get("outcome") in ("complete", "partial")}


def g_bombs(only: set[str] | None = None) -> list[dict[str, Any]]:
    recs = []
    for item in bomb_pdfs():
        if only and item[0] not in only:
            continue
        print(f"  bomba {item[0]} {item[1]}", flush=True)
        try:
            rec = run_bomb(item)
        except Exception as e:  # noqa: BLE001 — błąd budowy/uruchomienia to wynik, nie cichy brak
            rec = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
        ok = rec.get("outcome") == "technical_error" and not rec.get("server_died") and not rec.get("hung_over_wait") and rec.get("probe_after", {}).get("alive")
        died_or_hung = rec.get("server_died") or rec.get("hung_over_wait") or not rec.get("probe_after", {}).get("alive", False)
        peak = rec.get("cgroup_memory_peak_mb") or 0
        near_limit = peak > 0.5 * 6144  # szczyt > 50% limitu 6 GB: serwer przeżył tylko dzięki rozmiarowi bomby
        gap = "tak" if died_or_hung else ("nie" if ok and not near_limit else "częściowo")
        actual = (f"outcome={rec.get('outcome')} kody={rec.get('codes')}; {rec.get('wall_s')} s; serwer_zabity={rec.get('server_died')}; zawieszenie={rec.get('hung_over_wait')}; "
                  f"szczyt RSS drzewa {rec.get('peak_rss_tree_mb')} MiB, cgroup peak {rec.get('cgroup_memory_peak_mb')} MiB (limit {rec.get('memory_max')}); kontrola po ataku: {rec.get('probe_after')}")
        if "error" in rec:
            actual = f"nie wykonano: {rec['error']}"
            gap = "nie wykonano"
        recs.append(vec(item[0], "bomba-PDF", item[1], item[2], actual, gap,
                        fix="Parsowanie/renderowanie w procesie potomnym z RLIMIT_AS/cgroup i twardym czasem (kill po timeout); limity: bajty po dekompresji, piksele strony i obrazu, liczba obiektów/stron odczytana przed renderem; pamięć drzewa procesów.",
                        port_test=f"test_pdf_bomb_{item[0].lower()}_yields_technical_error_and_server_survives (z limitem RLIMIT_AS procesu potomnego)", data=rec))
    return recs


# ===================================================================== G6: SSRF z PDF
class Listener:
    def __init__(self) -> None:
        self.hits: list[str] = []
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a: Any) -> None:
                pass

            def do_GET(self) -> None:  # noqa: N802
                outer.hits.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"x")
            do_POST = do_HEAD = do_GET

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def ssrf_pdf(port: int, file_canary: Path, image_page: bool) -> bytes:
    u = f"http://127.0.0.1:{port}"
    fu = f"file://{file_canary}"
    xfa = f'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "{u}/xxe">]><xdp>&e;</xdp>'
    contents = b"BT /F1 12 Tf 40 780 Td (Potwierdzenie przelewu) Tj ET"
    res = "/Font << /F1 7 0 R >>"
    if image_page:
        contents = b"q 595 0 0 842 0 0 cm /Im0 Do Q"
        res = "/XObject << /Im0 8 0 R >>"
    objs = [
        f"<< /Type /Catalog /Pages 2 0 R /OpenAction 9 0 R /AcroForm << /XFA 10 0 R /Fields [] >> /Names << /EmbeddedFiles << /Names [(a.txt) 11 0 R] >> >> >>".encode(),
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << {res} >> /Annots [5 0 R 6 0 R 12 0 R 13 0 R] >>".encode(),
        stream_obj("", contents),
        f"<< /Type /Annot /Subtype /Link /Rect [0 0 595 842] /A << /S /URI /URI ({u}/uri) >> >>".encode(),
        f"<< /Type /Annot /Subtype /Link /Rect [0 0 595 842] /A << /S /GoToR /F ({u}/gotor) /D [0 /Fit] >> >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        # strumień z zewnętrznym plikiem (F/FFilter): pdfium nie powinien go otwierać
        f"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceGray /BitsPerComponent 8 /F << /FS /URL /F ({u}/extstream) >> /FFilter /FlateDecode /Length 1 >>\nstream\n\xff\nendstream".encode(),
        f"<< /S /JavaScript /JS (app.launchURL\\(\"{u}/js\", true\\); this.submitForm\\(\"{u}/submit\"\\);) >>".encode(),
        stream_obj("", xfa.encode()),
        f"<< /Type /Filespec /F (a.txt) /UF (a.txt) /EF << /F 14 0 R >> >>".encode(),
        f"<< /Type /Annot /Subtype /Link /Rect [0 0 100 100] /A << /S /Launch /F ({fu}) /Win << /F ({u}/launch) >> >> >>".encode(),
        f"<< /Type /Annot /Subtype /Link /Rect [100 0 200 100] /A << /S /URI /URI ({fu}) >> >>".encode(),
        stream_obj("/Type /EmbeddedFile", b"embedded"),
    ]
    return pdf_from_objects(objs)


def g_ssrf() -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    canary_dir = WORKDIR / "ssrf-outside"
    canary_dir.mkdir(parents=True, exist_ok=True)
    canary = "CANARY-" + secrets.token_hex(8)
    cf = canary_dir / "kanarek.txt"
    cf.write_text(canary)
    for variant, image_page in (("tekst", False), ("skan (render)", True)):
        lst = Listener()
        try:
            with running(f"ssrf-{int(image_page)}", srv_dir(f"ssrf-{int(image_page)}")) as (srv, c):
                pdf = ssrf_pdf(lst.port, cf, image_page)
                st = upload_and_wait(c, pdf, "ssrf.pdf", 60)
                did = st.get("_document_id")
                text_blob = ""
                for name in ("artifact/raw/reading.json", "evidence", "report", "diagnosis"):
                    rr = c.http.get(f"/documents/{did}/{name}")
                    text_blob += rr.text
                time.sleep(1.5)
                hits = list(lst.hits)
                recs.append(vec(f"S0{1 + image_page}", "SSRF-z-PDF", f"PDF z akcjami URI/GoToR/Launch/JS/XFA(XXE)/F+FFilter/EmbeddedFile + file:// — wariant: {variant}",
                                "zero połączeń do nasłuchu, zero treści z file:// w wyniku, zero wykonania akcji",
                                f"outcome={st.get('outcome')} kody={st.get('codes')}; połączenia do nasłuchu 127.0.0.1: {len(hits)} {hits}; treść kanarka z file:// w artefaktach: {canary in text_blob}",
                                "tak" if hits or canary in text_blob else "nie",
                                fix="Zachować pdfium bez V8/XFA i bez FORM ENV (stan obecny); w produkcie dodać test z nasłuchem i uruchamiać parser w procesie bez dostępu do sieci (np. `unshare -n`) — obrona w głąb.",
                                port_test="test_pdf_with_external_actions_makes_no_network_requests (nasłuch loopback)", data={"hits": hits}))
                recs.append({"_probe": probe_ok(c)})
        finally:
            lst.close()
    return recs


# ===================================================================== G7: ReDoS
def g_redos() -> list[dict[str, Any]]:
    """Czasy wzorców regex (uprząż + produkcyjne normalizatory) na wejściach 1k..50k znaków, każdy przypadek w podprocesie z limitem 20 s."""
    import subprocess
    probes = r'''
import re, sys, time, json
sys.path.insert(0, %(harness)r); sys.path.insert(0, %(backend)r)
import common
from odwolania2json.domain import normalize as nz
import stages
n = int(sys.argv[1]); kind = sys.argv[2]
inputs = {
 "digits": "1" * n,
 "digits_spaces": "1 " * (n // 2),
 "spaced_letters": "a " * (n // 2),
 "nip_like": "NIP: " + "123-45 " * (n // 7),
 "account_like": "PL" + "61 1090 1014 0000 " * (n // 19),
 "amount_like": "1 234,5 " * (n // 8),
 "date_like": "12 stycznia " * (n // 12) + "2026",
 "dots": "1." * (n // 2),
 "ted_like": "2024/S 123-" * (n // 11),
 "zl_spaces": "1" + " " * n + "zł",
}
txt = inputs[kind]
t0 = time.perf_counter()
res = {}
fns = {"nip": nz.normalize_nip, "regon": nz.normalize_regon, "krs": nz.normalize_krs, "pesel": nz.normalize_pesel, "account": nz.normalize_account,
       "amount": nz.normalize_amount, "date": nz.normalize_date, "ted": nz.normalize_ted}
for k, f in fns.items():
    t = time.perf_counter()
    try:
        f(txt)
    except Exception as e:
        pass
    res[k] = round(time.perf_counter() - t, 4)
t = time.perf_counter()
try:
    stages.fold(txt)
    for rx in (r"odwolujac\w*\s*:", r"wnosz\w+ odwolanie|wnosim odwolanie|odwoluje sie|wnosze odwolanie", r"udzielam|ustanawiam|umocowan|upowazniam|upowaznia"):
        re.search(rx, stages.fold(txt))
    src = open(%(stages)r, encoding="utf-8").read()
    import inspect
    for name, obj in vars(stages).items():
        if name.startswith("_join") or name.startswith("_merge") or name.startswith("_spaced"):
            obj(txt)
except Exception as e:
    res["stages_error"] = type(e).__name__
res["harness_regex"] = round(time.perf_counter() - t, 4)
print(json.dumps(res))
''' % {"harness": str(HARNESS), "backend": str(BACKEND_DIR), "stages": str(HARNESS / "stages.py")}
    pf = WORKDIR / "redos_probe.py"
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(probes)
    kinds = ["digits", "digits_spaces", "spaced_letters", "nip_like", "account_like", "amount_like", "date_like", "dots", "ted_like", "zl_spaces"]
    table: dict[str, dict[str, Any]] = {}
    worst = (0.0, "", 0, "")
    for kind in kinds:
        table[kind] = {}
        for n in (1000, 10000, 50000):
            try:
                p = subprocess.run([str(VENV_PY), "-I", str(pf), str(n), kind], capture_output=True, text=True, timeout=20)
                if p.returncode == 0:
                    r = json.loads(p.stdout.strip().splitlines()[-1])
                else:
                    r = {"error": p.stderr[-200:]}
            except subprocess.TimeoutExpired:
                r = {"timeout_20s": True}
            table[kind][str(n)] = r
            for k, v in r.items():
                if isinstance(v, (int, float)) and v > worst[0]:
                    worst = (v, kind, n, k)
                if k == "timeout_20s":
                    worst = (20.0, kind, n, "timeout")
    # HTTP: dokument z adversarialnym tekstem
    lines = ["Potwierdzenie przelewu", "Kwota: " + "1 " * 2000, "Rachunek: " + "61 1090 " * 1500, "NIP: " + "1" * 20000, "Data: " + "12 stycznia " * 800]
    pdf = text_pdf(lines, size=5)
    with running("redos", srv_dir("redos")) as (srv, c):
        t0 = time.monotonic()
        st = upload_and_wait(c, pdf, "redos.pdf", 120)
        http_s = round(time.monotonic() - t0, 2)
        pr = probe_ok(c)
    slow = worst[0] > 1.0
    return [vec("R01", "ReDoS", "wzorce normalizatorów produkcyjnych (apps) i regułowe uprzęży na ciągach do 50 000 znaków (10 rodzin wejść × 3 rozmiary)",
                "czas ≤ ~1 s dla 50 000 znaków; brak wzrostu wykładniczego i kwadratowego rzutującego na limit czasu",
                f"najgorszy czas {worst[0]:.2f} s ({worst[1]}, n={worst[2]}, funkcja {worst[3]}); dokument HTTP z długimi liniami: outcome={st.get('outcome')} w {http_s} s; kontrola={pr}",
                "tak" if slow else "nie",
                fix="Ograniczyć długość kandydata przed regex (np. ≤200 znaków dla NIP/rachunku/kwoty), użyć regex z limitem czasu (`regex` z timeout) lub wzorców bez zagnieżdżonych kwantyfikatorów; test z wejściem 50 000 znaków.",
                port_test="test_normalizers_linear_time_on_50k_char_inputs (limit 1 s)", data={"table": table, "worst": {"s": worst[0], "kind": worst[1], "n": worst[2], "fn": worst[3]}, "http_s": http_s})]


# ===================================================================== main
GROUPS = {"names": g_names, "types": g_types, "paths": g_paths, "flood": g_flood, "ssrf": g_ssrf, "redos": g_redos}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--skip", default="")
    ap.add_argument("--bombs", default="all", help="all | none | B01,B02,...")
    ns = ap.parse_args()
    only = {x for x in ns.only.split(",") if x}
    skip = {x for x in ns.skip.split(",") if x}
    out_path = ATAK / EXPN / "wyniki.json"
    out = json.loads(out_path.read_text()) if out_path.exists() and only else {"experiment": EXPN, "versions": versions(), "memory_limit": "14G (bomby: 6G, patrz uwagi)",
                                                                              "note": "Wynik opisuje uprząż harness/server.py, nie produkt.", "vectors": [], "probes": {}}
    out["generated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    seen = {v["id"] for v in out["vectors"]}
    todo = [g for g in [*GROUPS, "bombs"] if (not only or g in only) and g not in skip]
    for g in todo:
        t0 = time.monotonic()
        print(f"== {g}", flush=True)
        if g == "bombs":
            if ns.bombs == "none":
                continue
            recs = g_bombs(None if ns.bombs == "all" else set(ns.bombs.split(",")))
        else:
            recs = GROUPS[g]()
        for r in recs:
            if "_probe" in r:
                out["probes"][g] = r["_probe"]
            elif "_usage" in r:
                out["probes"][g + "_usage"] = r["_usage"]
            else:
                out["vectors"] = [v for v in out["vectors"] if v["id"] != r["id"]] + [r]
        out["vectors"].sort(key=lambda v: v["id"])
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"   {g}: {len(recs)} rekordów w {time.monotonic() - t0:.1f} s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
