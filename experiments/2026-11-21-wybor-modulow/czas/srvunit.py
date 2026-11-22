"""Uruchomienie serwera uprzęży w scope systemd z limitem pamięci i odczyt szczytu pamięci CAŁEJ grupy procesów (cgroup memory.peak).

Używane przez T3 i T6. Serwer = `harness/server.py` (FastAPI, ten sam kod, który mierzyły grupy A-D), wywoływany wyłącznie przez HTTP.
Zapisujemy: czas startu do /health, szczyt cgroup (memory.peak, MiB), szczyt VmHWM serwera, maks. liczbę wątków, CPU serwera (utime+stime), czas każdego wsadu.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import httpx

import tlib

HARNESS = tlib.EXP / "harness"


def proc_cpu_s(pid: int) -> float:
    s = Path(f"/proc/{pid}/stat").read_text()
    p = s[s.rindex(")") + 2:].split()
    return (int(p[11]) + int(p[12])) / os.sysconf("SC_CLK_TCK")


def tree_cpu_s(pid: int) -> float:
    return sum(proc_cpu_s(p) for p in tlib.tree_pids(pid) if Path(f"/proc/{p}").exists())


class ServerUnit:
    def __init__(self, unit: str, cfg: dict[str, Any], work: Path, *, mem_max: str = "14G") -> None:
        self.unit, self.cfg, self.work, self.mem_max = unit, cfg, work, mem_max
        self.port: int = 0
        self.proc: subprocess.Popen[bytes] | None = None
        self.pid: int | None = None
        self.start_s = 0.0
        self.max_threads = 0
        self.max_rss_mb = 0.0
        self._stop = threading.Event()
        self._sampler: threading.Thread | None = None

    def __enter__(self) -> ServerUnit:
        import socket
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        self.work.mkdir(parents=True, exist_ok=True)
        cfgp = self.work / "server-config.json"
        cfgp.write_text(json.dumps(self.cfg | {"work_dir": str(self.work / "data")}), encoding="utf-8")
        t0 = time.monotonic()
        self.proc = tlib.run_in_scope(self.unit, [sys.executable, str(HARNESS / "server.py"), "--port", str(self.port), "--config", str(cfgp)],
                                      env={"PYTHONUNBUFFERED": "1"}, cwd=str(HARNESS), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        url = f"http://127.0.0.1:{self.port}"
        while time.monotonic() - t0 < 90:
            if self.proc.poll() is not None:
                raise RuntimeError("serwer zakończył się przy starcie")
            try:
                h = httpx.get(url + "/health", timeout=1.0)
                if h.status_code == 200:
                    self.pid = h.json()["pid"]
                    self.start_s = time.monotonic() - t0
                    break
            except httpx.HTTPError:
                time.sleep(0.05)
        else:
            raise RuntimeError("serwer nie wystartował")
        self.url = url
        self.client = httpx.Client(base_url=url, timeout=120.0)
        self._sampler = threading.Thread(target=self._sample, daemon=True)
        self._sampler.start()
        return self

    def _sample(self) -> None:
        while not self._stop.wait(0.25):
            try:
                self.max_threads = max(self.max_threads, tlib.thread_count(self.pid))
                self.max_rss_mb = max(self.max_rss_mb, tlib.rss_hwm_mb(self.pid))
            except (OSError, ValueError):
                pass

    def run_batch(self, files: list[tuple[str, bytes]], *, poll_s: float = 0.2, timeout: float = 3600) -> dict[str, Any]:
        cpu0 = tree_cpu_s(self.pid)
        t0 = time.monotonic()
        r = self.client.post("/batches", files=[("files", (n, d, "application/pdf")) for n, d in files], timeout=600)
        r.raise_for_status()
        t_up = time.monotonic()
        b = r.json()
        bid = b["batch_id"]
        while True:
            st = self.client.get(f"/batches/{bid}").json()
            if st.get("done"):
                break
            if time.monotonic() - t0 > timeout:
                raise TimeoutError("wsad nie skończył")
            time.sleep(poll_s)
        t_done = time.monotonic()
        cpu1 = tree_cpu_s(self.pid)
        docs = []
        for d in b["document_ids"]:
            m = self.client.get(f"/documents/{d}/metrics")
            s = self.client.get(f"/documents/{d}").json()
            docs.append({"outcome": s.get("outcome"), "codes": s.get("codes"), "metrics": m.json() if m.status_code == 200 else None})
        wall = t_done - t0
        return {"n": len(files), "wall_s": round(wall, 3), "upload_s": round(t_up - t0, 3), "docs_per_min": round(len(files) / wall * 60, 2),
                "server_cpu_s": round(cpu1 - cpu0, 2), "cpu_utilization": round((cpu1 - cpu0) / wall / (os.cpu_count() or 1), 3), "docs": docs}

    def peaks(self) -> dict[str, Any]:
        return {"cgroup_memory_peak_mb": tlib.cgroup_mem_peak_mb(self.unit), "server_vmhwm_mb": tlib.rss_hwm_mb(self.pid),
                "sampled_max_threads": self.max_threads, "start_s": round(self.start_s, 3), "mem_max": self.mem_max}

    def __exit__(self, *a: object) -> None:
        self._stop.set()
        try:
            self.client.close()
        except Exception:  # noqa: BLE001
            pass
        if self.proc and self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.wait(timeout=15)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(self.proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        shutil.rmtree(self.work, ignore_errors=True)
