"""Klient HTTP harnessu i uruchamianie backendu jako podprocesu pod limitem pamięci.

`ManagedServer` startuje `server.py` jako proces potomny:
1. `systemd-run --user --scope -p MemoryMax=14G` (preferowane; limit cgroup),
2. `prlimit --as=<bajty>` (limit przestrzeni adresowej; bywa ostrzejszy niż RSS),
3. brak limitu — wtedy `limit_method="none"` trafia do wyników (nie udajemy limitu).
Wybrana metoda jest zapisywana w `ManagedServer.limit_method` i w JSON-ach eksperymentów.

Szczytowy RSS = VmHWM procesu serwera (z /proc), odczytywany przed zakończeniem; to maksimum
w czasie życia procesu, nie próbkowanie. Czas ścienny mierzy `HarnessClient.run_document`.
"""

from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

from common import HARNESS_DIR

MEMORY_MAX = "14G"
MEMORY_MAX_BYTES = 14 * 1024**3


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def detect_limit_method(timeout: float = 15.0) -> str:
    """Sprawdza w praktyce, czy systemd-run --user --scope działa; inaczej prlimit, inaczej none."""
    if shutil.which("systemd-run"):
        try:
            r = subprocess.run(["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={MEMORY_MAX}", "true"],
                               capture_output=True, timeout=timeout)
            if r.returncode == 0:
                return "systemd-run"
        except (subprocess.SubprocessError, OSError):
            pass
    if shutil.which("prlimit"):
        return "prlimit"
    return "none"


def proc_status_kb(pid: int, field: str) -> int | None:
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith(field + ":"):
                return int(line.split()[1])
    except (OSError, ValueError):
        pass
    return None


def descendants(pid: int) -> list[int]:
    out, stack = [], [pid]
    while stack:
        p = stack.pop()
        try:
            kids = Path(f"/proc/{p}/task/{p}/children").read_text().split()
        except OSError:
            kids = []
        for k in kids:
            out.append(int(k))
            stack.append(int(k))
    return out


class ManagedServer:
    """Backend jako podproces pod limitem pamięci; kontekstowy menedżer."""

    def __init__(self, config_path: str | Path | None = None, *, env: dict[str, str] | None = None, port: int | None = None,
                 python: str | None = None, limit_method: str | None = None, startup_timeout: float = 60.0,
                 log_path: str | Path | None = None) -> None:
        self.port = port or free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.config_path = str(config_path) if config_path else None
        self.env = env or {}
        self.python = python or sys.executable
        self.limit_method = limit_method or detect_limit_method()
        self.startup_timeout = startup_timeout
        self.log_path = Path(log_path) if log_path else None
        self.proc: subprocess.Popen[bytes] | None = None
        self.peak_rss_kb: int | None = None
        self.start_s: float | None = None
        self._pids: set[int] = set()

    def command(self) -> list[str]:
        base = [self.python, str(HARNESS_DIR / "server.py"), "--port", str(self.port)]
        if self.config_path:
            base += ["--config", self.config_path]
        if self.limit_method == "systemd-run":
            return ["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={MEMORY_MAX}", *base]
        if self.limit_method == "prlimit":
            return ["prlimit", f"--as={MEMORY_MAX_BYTES}", *base]
        return base

    def start(self) -> ManagedServer:
        env = os.environ | self.env | {"PYTHONUNBUFFERED": "1"}
        log = self.log_path.open("ab") if self.log_path else subprocess.DEVNULL
        t0 = time.monotonic()
        self.proc = subprocess.Popen(self.command(), env=env, stdout=log, stderr=subprocess.STDOUT, cwd=str(HARNESS_DIR),
                                     start_new_session=True)
        deadline = t0 + self.startup_timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"serwer zakończył się kodem {self.proc.returncode} przy starcie (metoda limitu: {self.limit_method})")
            try:
                if httpx.get(self.url + "/health", timeout=1.0).status_code == 200:
                    self.start_s = time.monotonic() - t0
                    return self
            except httpx.HTTPError:
                time.sleep(0.1)
        self.stop()
        raise RuntimeError("serwer nie wystartował w limicie czasu")

    def sample_rss(self) -> int | None:
        """Aktualne maksimum (VmHWM) serwera i potomków; zapamiętuje największą dotąd widzianą wartość."""
        if self.proc is None:
            return self.peak_rss_kb
        pids = [self.proc.pid, *descendants(self.proc.pid)]
        self._pids.update(pids)
        total = sum(proc_status_kb(p, "VmHWM") or 0 for p in pids)
        if total:
            self.peak_rss_kb = max(self.peak_rss_kb or 0, total)
        return self.peak_rss_kb

    def stop(self) -> None:
        if self.proc is None:
            return
        self.sample_rss()
        if self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.wait(timeout=10)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                with __import__("contextlib").suppress(ProcessLookupError):
                    os.killpg(self.proc.pid, signal.SIGKILL)
        self.proc = None

    def kill9(self) -> None:
        """Ubicie bez sprzątania (E15)."""
        if self.proc is not None:
            self.sample_rss()
            with __import__("contextlib").suppress(ProcessLookupError):
                os.killpg(self.proc.pid, signal.SIGKILL)
            self.proc.wait()
            self.proc = None

    def __enter__(self) -> ManagedServer:
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.stop()


class HarnessClient:
    """Cienki klient httpx do tras backendu; `run_document` mierzy czas ścienny wgranie→wynik."""

    def __init__(self, base_url: str, *, timeout: float = 60.0, server: ManagedServer | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.http = httpx.Client(base_url=self.base_url, timeout=timeout)
        self.server = server

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> HarnessClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        r = self.http.get("/health")
        r.raise_for_status()
        return r.json()

    def system(self) -> dict[str, Any]:
        r = self.http.get("/system")
        r.raise_for_status()
        return r.json()

    def upload(self, files: list[tuple[str, bytes]]) -> dict[str, Any]:
        r = self.http.post("/batches", files=[("files", (name, data, "application/pdf")) for name, data in files])
        r.raise_for_status()
        return r.json()

    def upload_paths(self, paths: list[Path]) -> dict[str, Any]:
        return self.upload([(p.name, p.read_bytes()) for p in paths])

    def document(self, document_id: str) -> dict[str, Any]:
        r = self.http.get(f"/documents/{document_id}")
        r.raise_for_status()
        return r.json()

    def wait_done(self, document_id: str, *, timeout: float = 600.0, poll: float = 0.1) -> dict[str, Any]:
        t0 = time.monotonic()
        while True:
            st = self.document(document_id)
            if st["progress"] == "done":
                return st
            if time.monotonic() - t0 > timeout:
                raise TimeoutError(f"dokument {document_id} nie skończył w {timeout}s (progress={st['progress']})")
            time.sleep(poll)

    def artifact(self, document_id: str, name: str) -> tuple[int, Any]:
        r = self.http.get(f"/documents/{document_id}/{name}")
        return r.status_code, (r.json() if r.content else None)

    def run_document(self, path: Path | str, *, timeout: float = 600.0) -> dict[str, Any]:
        """health → upload → wait → result/evidence/report/diagnosis. Zwraca stan, artefakty, czasy i RSS."""
        path = Path(path)
        t0 = time.monotonic()
        health = self.health()
        t_health = time.monotonic()
        up = self.upload_paths([path])
        doc_id = up["document_id"]
        t_up = time.monotonic()
        state = self.wait_done(doc_id, timeout=timeout)
        t_done = time.monotonic()
        arts: dict[str, Any] = {}
        for name in ("result", "evidence", "report", "diagnosis", "metrics"):
            code, body = self.artifact(doc_id, name)
            arts[name] = {"http": code, "body": body}
        out: dict[str, Any] = {"file": path.name, "document_id": doc_id, "health": health, "state": state, "artifacts": arts,
                               "timing": {"upload_s": round(t_up - t_health, 4), "processing_s": round(t_done - t_up, 4),
                                          "wall_s": round(time.monotonic() - t0, 4), "health_s": round(t_health - t0, 4)}}
        if self.server is not None:
            out["peak_rss_mb"] = round((self.server.sample_rss() or 0) / 1024, 1)
            out["limit_method"] = self.server.limit_method
        return out
