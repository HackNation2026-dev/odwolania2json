"""Wspólne narzędzia grupy D (atak na uprząż HTTP): serwer pod limitem pamięci, surowy multipart,
PDF-y testowe, atrapa HTTP dla LLM, wykrywanie wycieków, pomiar zasobów.

WAŻNE: wynik opisuje UPRZĄŻ (`harness/server.py`), nie produkt. Klucz LLM nigdy nie jest tu czytany ani zapisywany:
testy wycieku używają fikcyjnego klucza-kanarka z pliku tymczasowego, a E13 podaje tylko ŚCIEŻKĘ do prawdziwego klucza
(`MINIMAX_KEY_FILE`) procesowi serwera.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import http.server
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import zlib
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

ATAK = Path(__file__).resolve().parent
EXP = ATAK.parent
HARNESS = EXP / "harness"
REPO = EXP.parents[1]
for p in (HARNESS, HARNESS / "tests"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import httpx  # noqa: E402

import client as hclient  # noqa: E402
from client import HarnessClient, ManagedServer, descendants, proc_status_kb  # noqa: E402
from common import BACKEND_DIR  # noqa: E402,F401  (ustawia sys.path backendu)

SANDBOX = Path(os.environ.get("ATAK_WORK", "/tmp/uzp-atak"))
VENV_PY = REPO / ".venv-exp" / "bin" / "python"


# ---------------------------------------------------------------- zapis wyników
def save_json(exp: str, name: str, obj: Any) -> Path:
    out = ATAK / exp / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return out


def versions() -> dict[str, Any]:
    import importlib.metadata as md
    import platform
    v = {"python": sys.version.split()[0], "platform": platform.platform(), "cpu_count": os.cpu_count()}
    for pkg in ("fastapi", "starlette", "uvicorn", "httpx", "pypdfium2", "pypdf", "pydantic", "python-multipart", "rapidocr", "onnxruntime"):
        with contextlib.suppress(Exception):
            v[pkg] = md.version(pkg)
    with contextlib.suppress(Exception):
        v["git_head"] = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    return v


# ---------------------------------------------------------------- konfiguracja i serwer
def write_config(path: Path, work_dir: Path, **over: Any) -> Path:
    """Plik JSON wariantu; `over` może zawierać zagnieżdżone `llm` i `limits` (słowniki)."""
    cfg: dict[str, Any] = {"work_dir": str(work_dir), "ocr": "none", "router": "rules", "extractor": "rules"}
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k] |= v
        else:
            cfg[k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return path


def cgroup_dir(pid: int) -> Path | None:
    try:
        line = Path(f"/proc/{pid}/cgroup").read_text().strip().splitlines()[0]
        rel = line.split("::", 1)[1]
        p = Path("/sys/fs/cgroup") / rel.lstrip("/")
        return p if p.is_dir() else None
    except (OSError, IndexError):
        return None


class AttackServer(ManagedServer):
    """ManagedServer z konfigurowalnym limitem pamięci (domyślnie 14 GB zgodnie z planem), próbnikiem RSS drzewa
    procesów i odczytem `memory.peak` cgroup (cała grupa procesów, także dzieci)."""

    def __init__(self, config_path: Path, *, memory_max: str = "14G", env: dict[str, str] | None = None,
                 log_path: Path | None = None, port: int | None = None, extra_env_clean: Iterable[str] = ()) -> None:
        super().__init__(config_path, env=env, port=port, log_path=log_path)
        self.memory_max = memory_max
        self.rss_peak_kb = 0
        self._stop_sampler = threading.Event()
        self._sampler: threading.Thread | None = None
        self.cgroup: Path | None = None
        self.pid: int | None = None

    def command(self) -> list[str]:
        base = [self.python, str(HARNESS / "server.py"), "--port", str(self.port), "--config", str(self.config_path)]
        if self.limit_method == "systemd-run":
            return ["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={self.memory_max}", "-p", "MemorySwapMax=0", *base]
        return base

    def start(self) -> AttackServer:
        super().start()
        assert self.proc is not None
        self.pid = self.proc.pid
        self.cgroup = cgroup_dir(self.proc.pid)
        self._stop_sampler.clear()
        self._sampler = threading.Thread(target=self._sample_loop, daemon=True)
        self._sampler.start()
        return self

    def _sample_loop(self) -> None:
        while not self._stop_sampler.is_set():
            self.rss_now_kb()
            time.sleep(0.15)

    def rss_now_kb(self) -> int:
        if self.proc is None or self.proc.poll() is not None:
            return 0
        pids = [self.proc.pid, *descendants(self.proc.pid)]
        tot = sum(proc_status_kb(p, "VmRSS") or 0 for p in pids)
        self.rss_peak_kb = max(self.rss_peak_kb, tot)
        return tot

    def cgroup_peak_mb(self) -> float | None:
        if self.cgroup is None:
            return None
        try:
            return round(int((self.cgroup / "memory.peak").read_text()) / 1048576, 1)
        except (OSError, ValueError):
            return None

    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def stop(self) -> None:
        self._stop_sampler.set()
        super().stop()

    def usage(self) -> dict[str, Any]:
        return {"peak_rss_tree_mb": round(self.rss_peak_kb / 1024, 1), "cgroup_memory_peak_mb": self.cgroup_peak_mb(),
                "limit_method": self.limit_method, "memory_max": self.memory_max if self.limit_method == "systemd-run" else None}


@contextlib.contextmanager
def running(name: str, work: Path, *, memory_max: str = "14G", env: dict[str, str] | None = None, **cfg: Any):
    """Serwer + klient na świeżym katalogu roboczym `work`; log serwera w `work/../<name>.log`."""
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    cp = write_config(work.parent / f"{name}.config.json", work / "data", **cfg)
    srv = AttackServer(cp, memory_max=memory_max, env=env, log_path=work.parent / f"{name}.server.log")
    srv.work = work / "data"  # type: ignore[attr-defined]
    srv.log = work.parent / f"{name}.server.log"  # type: ignore[attr-defined]
    srv.start()
    c = HarnessClient(srv.url, server=srv, timeout=120.0)
    try:
        yield srv, c
    finally:
        c.close()
        srv.stop()


def wait_alive(url: str, tries: int = 50, delay: float = 0.2) -> bool:
    for _ in range(tries):
        try:
            if httpx.get(url + "/health", timeout=2).status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(delay)
    return False


# ---------------------------------------------------------------- HTTP: surowy multipart
def raw_multipart(parts: list[dict[str, Any]], boundary: str | None = None) -> tuple[bytes, str]:
    """parts: {"name": "files", "filename": <str|bytes|None>, "data": bytes, "ctype": str}. Nazwa pliku wstawiana surowo."""
    b = boundary or "----atak" + secrets.token_hex(8)
    out = bytearray()
    for p in parts:
        out += f"--{b}\r\n".encode()
        disp = f'Content-Disposition: form-data; name="{p.get("name", "files")}"'.encode()
        fn = p.get("filename", "x.pdf")
        if fn is not None:
            disp += b'; filename="' + (fn if isinstance(fn, bytes) else fn.encode("utf-8", "surrogateescape")) + b'"'
        out += disp + b"\r\n"
        if p.get("ctype"):
            out += f"Content-Type: {p['ctype']}\r\n".encode()
        out += b"\r\n" + p["data"] + b"\r\n"
    out += f"--{b}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={b}"


def post_raw(client: HarnessClient, parts: list[dict[str, Any]], timeout: float = 120.0) -> httpx.Response:
    body, ctype = raw_multipart(parts)
    return client.http.post("/batches", content=body, headers={"Content-Type": ctype}, timeout=timeout)


def wait_batch(client: HarnessClient, batch_id: str, timeout: float = 300.0, poll: float = 0.2) -> dict[str, Any]:
    t0 = time.monotonic()
    while True:
        r = client.http.get(f"/batches/{batch_id}")
        if r.status_code != 200:
            return {"http": r.status_code, "body": r.text[:300]}
        j = r.json()
        if j["done"]:
            return j
        if time.monotonic() - t0 > timeout:
            j["timeout"] = True
            return j
        time.sleep(poll)


# ---------------------------------------------------------------- PDF-y
def pdf_from_objects(objs: list[bytes], root: int = 1, *, trailer_extra: bytes = b"") -> bytes:
    out = bytearray(b"%PDF-1.7\n")
    offs = []
    for i, body in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for o in offs:
        out += f"{o:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root {root} 0 R {trailer_extra.decode()} >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def stream_obj(dict_body: str, data: bytes, *, flate: bool = False) -> bytes:
    if flate:
        data = zlib.compress(data, 9)
        dict_body += " /Filter /FlateDecode"
    return f"<< {dict_body} /Length {len(data)} >>\nstream\n".encode() + data + b"\nendstream"


def simple_page_pdf(content: bytes, *, mediabox: str = "0 0 595 842", extra_page: str = "", extra_objs: list[bytes] | None = None,
                    catalog_extra: str = "", flate_content: bool = False) -> bytes:
    objs = [f"<< /Type /Catalog /Pages 2 0 R {catalog_extra} >>".encode(),
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            f"<< /Type /Page /Parent 2 0 R /MediaBox [{mediabox}] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> {extra_page} >>".encode(),
            stream_obj("", content, flate=flate_content),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    return pdf_from_objects(objs + (extra_objs or []))


def zeros_flate(n_bytes: int) -> bytes:
    """Skompresowany strumień n zer (współczynnik ~1000:1), budowany kawałkami bez trzymania całości w pamięci."""
    c = zlib.compressobj(9)
    chunk = b"\0" * (1 << 20)
    out = bytearray()
    left = n_bytes
    while left > 0:
        k = min(left, len(chunk))
        out += c.compress(chunk[:k])
        left -= k
    out += c.flush()
    return bytes(out)


# ---------------------------------------------------------------- atrapa HTTP dla LLM
class MockServer:
    """Prawdziwy serwer HTTP (wątek) udający endpoint LLM w formacie Anthropic. `handler(req) -> action`.

    Zapisuje tylko metadane żądań: ścieżka, długość ciała, czy nagłówki auth są obecne i czy równe kanarkowi
    (wartość klucza NIE jest zapisywana w wynikach).
    """

    def __init__(self, behavior: Callable[["MockReq"], None], canary_key: str | None = None) -> None:
        self.behavior = behavior
        self.canary_key = canary_key
        self.log: list[dict[str, Any]] = []
        self.lock = threading.Lock()
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a: Any) -> None:  # cisza
                pass

            def _go(self) -> None:
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(n) if n else b""
                auth = self.headers.get("Authorization", "")
                xkey = self.headers.get("x-api-key", "")
                req = MockReq(self, body)
                with outer.lock:
                    outer.log.append({"path": self.path, "method": self.command, "body_len": len(body), "t": time.monotonic(),
                                      "has_auth": bool(auth), "has_x_api_key": bool(xkey),
                                      "auth_is_canary": bool(outer.canary_key and outer.canary_key in auth),
                                      "xkey_is_canary": bool(outer.canary_key and xkey == outer.canary_key)})
                    req.index = len(outer.log)
                try:
                    outer.behavior(req)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            do_POST = do_GET = _go

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self) -> MockServer:
        self.thread.start()
        return self

    def __exit__(self, *a: object) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


class MockReq:
    def __init__(self, h: http.server.BaseHTTPRequestHandler, body: bytes) -> None:
        self.h, self.body, self.path, self.index = h, body, h.path, 0
        self.headers = h.headers

    def json(self) -> Any:
        return json.loads(self.body or b"{}")

    def send(self, status: int, body: bytes, headers: dict[str, str] | None = None, ctype: str = "application/json") -> None:
        h = self.h
        h.send_response(status)
        h.send_header("Content-Type", ctype)
        h.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            h.send_header(k, v)
        h.end_headers()
        h.wfile.write(body)

    def anthropic_ok(self, text: str) -> None:
        self.send(200, json.dumps({"id": "m", "model": "mock", "stop_reason": "end_turn", "content": [{"type": "text", "text": text}],
                                   "usage": {"input_tokens": 10, "output_tokens": 5}}).encode())


def make_key_file(directory: Path, canary: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    p = directory / "key.canary"
    p.write_text(canary + "\n", encoding="utf-8")
    p.chmod(0o600)
    return p


# ---------------------------------------------------------------- wycieki i migawki
def grep_tree(root: Path, needles: list[str]) -> list[dict[str, Any]]:
    hits = []
    if not root.exists():
        return hits
    for p in root.rglob("*"):
        if p.is_file() and not p.is_symlink():
            try:
                data = p.read_bytes()
            except OSError:
                continue
            for n in needles:
                if n.encode() in data:
                    hits.append({"file": str(p.relative_to(root)), "needle_prefix": n[:6] + "…"})
    return hits


def snapshot(roots: list[Path], skip: list[Path] | None = None) -> dict[str, tuple[int, int]]:
    skip = skip or []
    snap: dict[str, tuple[int, int]] = {}
    for r in roots:
        if not r.exists():
            continue
        for dp, dns, fns in os.walk(r):
            dpp = Path(dp)
            if any(s == dpp or s in dpp.parents for s in skip) or "__pycache__" in dpp.parts:
                dns[:] = []
                continue
            for fn in fns:
                f = dpp / fn
                with contextlib.suppress(OSError):
                    st = f.lstat()
                    snap[str(f)] = (st.st_size, int(st.st_mtime_ns))
    return snap


def snap_diff(before: dict[str, tuple[int, int]], after: dict[str, tuple[int, int]]) -> dict[str, list[str]]:
    return {"added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after)),
            "changed": sorted(k for k in before.keys() & after.keys() if before[k] != after[k])}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------- rekordy wektorów
def vec(vid: str, family: str, name: str, expected: str, actual: str, gap: str, *, fix: str = "", port_test: str = "",
        data: dict[str, Any] | None = None) -> dict[str, Any]:
    """gap: 'tak' | 'nie' | 'częściowo' | 'nie dotyczy' (uprząż nie ma tej funkcji) | 'nie wykonano'."""
    return {"id": vid, "family": family, "name": name, "expected": expected, "actual": actual, "gap": gap,
            "fix": fix, "port_test": port_test, "data": data or {}}


def doc_state(c: HarnessClient, doc_id: str, timeout: float = 120.0) -> dict[str, Any]:
    try:
        return c.wait_done(doc_id, timeout=timeout)
    except TimeoutError:
        return {"progress": "timeout", "outcome": None, "codes": []}


def upload_and_wait(c: HarnessClient, data: bytes, name: str = "x.pdf", timeout: float = 120.0) -> dict[str, Any]:
    r = c.http.post("/batches", files=[("files", (name, data, "application/pdf"))])
    if r.status_code != 201:
        return {"http": r.status_code, "body": r.text[:200]}
    j = r.json()
    st = doc_state(c, j["document_id"], timeout)
    st["_http"] = 201
    st["_document_id"] = j["document_id"]
    return st


# ---------------------------------------------------------------- dane rozwojowe (tylko dev)
def dev_item(document_class: str, index: int = 0):
    """Dokument ze zbioru rozwojowego (nigdy kontrolnego); `load_items('dev')` nie zwraca spraw kontrolnych."""
    from data import load_items
    return [i for i in load_items("dev") if i.document_class == document_class][index]


def dev_pdf(document_class: str, index: int = 0) -> bytes:
    return dev_item(document_class, index).source.read_bytes()


def probe_ok(c: HarnessClient, pdf: bytes | None = None) -> dict[str, Any]:
    """Kontrola po ataku: /health żyje i poprawny dokument kończy się wynikiem (complete/partial)."""
    out: dict[str, Any] = {}
    try:
        out["health"] = c.http.get("/health", timeout=10).status_code
    except httpx.HTTPError as e:
        return {"health": f"błąd:{type(e).__name__}", "clean_doc": None, "alive": False}
    st = upload_and_wait(c, pdf or dev_pdf("przelew", 0), "kontrola.pdf", timeout=120)
    out["clean_doc"] = st.get("outcome")
    out["alive"] = out["health"] == 200 and st.get("outcome") in ("complete", "partial")
    return out


# ---------------------------------------------------------------- wstrzykiwanie tekstu do istniejącego PDF (pdfium)
def inject_text(pdf: bytes, items: list[dict[str, Any]], page_index: int = 0) -> bytes:
    """Dodaje obiekty tekstowe do strony istniejącego PDF-a (pypdfium2 raw). Pozycja `x,y` w punktach PDF (początek: lewy dół).

    items: {"text", "x", "y", "size"=10, "rgb"=(0,0,0), "mode"=None (3 = niewidoczny)}; polskie znaki wymagają czcionki
    z kodowaniem Unicode, dlatego teksty wstrzyknięć są ASCII (to nie zmienia istoty ataku)."""
    import ctypes

    import pypdfium2 as pdfium
    import pypdfium2.raw as raw
    doc = pdfium.PdfDocument(pdf)
    page = doc[page_index]
    for it in items:
        font = raw.FPDFText_LoadStandardFont(doc.raw, b"Helvetica")
        obj = raw.FPDFPageObj_CreateTextObj(doc.raw, font, float(it.get("size", 10)))
        buf = it["text"].encode("utf-16-le") + b"\0\0"
        arr = (ctypes.c_ushort * (len(buf) // 2)).from_buffer_copy(buf)
        raw.FPDFText_SetText(obj, arr)
        r, g, b = it.get("rgb", (0, 0, 0))
        raw.FPDFPageObj_SetFillColor(obj, r, g, b, 255)
        if it.get("mode") is not None:
            raw.FPDFTextObj_SetTextRenderMode(obj, it["mode"])
        raw.FPDFPageObj_Transform(obj, 1, 0, 0, 1, float(it["x"]), float(it["y"]))
        raw.FPDFPage_InsertObject(page.raw, obj)
    raw.FPDFPage_GenerateContent(page.raw)
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


# ---------------------------------------------------------------- ocena: ewaluator produkcyjny (po PR #8/#9) i miara uprzęży
def eval_counts(result: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    """Liczniki TP/TN/FP/FN z `odwolania2json.evaluator.compare_document` (domyślna konfiguracja: błędna wartość = FP,
    próg 80%). Dodatkowo `leaf` z `run_experiment.leaf_counts` (własna miara uprzęży) do opisu różnic."""
    from odwolania2json.evaluator import ClassTotals, compare_document
    outs = compare_document(result, reference)
    c = {v: sum(1 for o in outs if o.verdict == v) for v in ("tp", "tn", "fp", "fn")}
    tot = ClassTotals(**c)
    from run_experiment import leaf_counts, leaf_f1
    lc = leaf_counts(result, reference)
    return {**c, "f1": round(tot.f1, 4), "leaf": lc, "leaf_f1": round(leaf_f1(lc), 4)}


def flat_leaves(x: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(x, dict):
        for k, v in x.items():
            out |= flat_leaves(v, f"{prefix}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            out |= flat_leaves(v, f"{prefix}/{i}")
    else:
        out[prefix] = x
    return out


def read_key_for_leak_check() -> str | None:
    """Klucz LLM wczytany WYŁĄCZNIE do sprawdzenia wycieku (grep po wynikach); nigdy nie wypisywany ani zapisywany."""
    p = Path(os.environ.get("MINIMAX_KEY_FILE") or Path.home() / "kluczMiniMaxKacper").expanduser()
    try:
        k = p.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return k or None


# ---------------------------------------------------------------- PDF z tekstem (do ataków)
def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def text_pdf_lines(lines: list[str], size: int = 10) -> bytes:
    ops = ["BT", f"/F1 {size} Tf", f"{size + 2} TL", "40 800 Td"] + [f"({_esc(ln)}) Tj T*" for ln in lines] + ["ET"]
    return simple_page_pdf("\n".join(ops).encode("latin-1", "replace"))


def dense_pdf(pages: int, chars_per_page: int, head: list[str] | None = None) -> bytes:
    """Wielostronicowy PDF z gęstym tekstem (słowa po 6 liter, linie ~100 znaków)."""
    words = ["alfa", "bravo", "kod123", "nip", "kwota", "umowa"]
    n_base = 3  # 1 katalog, 2 drzewo, 3 czcionka
    page_ids = [n_base + 1 + 2 * p for p in range(pages)]
    out = [b"<< /Type /Catalog /Pages 2 0 R >>", f"<< /Type /Pages /Kids [{' '.join(f'{i} 0 R' for i in page_ids)}] /Count {pages} >>".encode(),
           b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    for p in range(pages):
        cur, lines, i = "", [], 0
        total = 0
        while total < chars_per_page:
            w = words[(p + i) % len(words)] + str(i % 97)
            i += 1
            if len(cur) + len(w) > 100:
                lines.append(cur)
                total += len(cur)
                cur = ""
            cur += w + " "
        if p == 0 and head:
            lines = list(head) + lines
        ops = "BT /F1 4 Tf 5 TL 10 830 Td " + " ".join(f"({_esc(ln)}) Tj T*" for ln in lines) + " ET"
        pid = n_base + 1 + 2 * p
        out.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {pid + 1} 0 R /Resources << /Font << /F1 3 0 R >> >> >>".encode())
        out.append(stream_obj("", ops.encode("latin-1", "replace")))
    return pdf_from_objects(out)


def encrypted_stub() -> bytes:
    """PDF ze słownikiem /Encrypt (hasło użytkownika nieznane): pdfium zgłasza błąd hasła."""
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>",
            f"<< /Filter /Standard /V 1 /R 2 /O <{'ab' * 32}> /U <{'cd' * 32}> /P -4 >>".encode()]
    return pdf_from_objects(objs, trailer_extra=b"/Encrypt 4 0 R /ID [<0123456789abcdef0123456789abcdef><0123456789abcdef0123456789abcdef>]")
