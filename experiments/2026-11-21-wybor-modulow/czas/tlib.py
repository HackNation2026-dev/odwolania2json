"""Wspólne narzędzia pomiaru czasu i pamięci (grupa T): kontrola ciszy, metadane środowiska, statystyki, cgroup.

Dlaczego: poprzednie pomiary czasu powstały pod load average 20-50 na 8 rdzeniach i są niewiążące. Każdy pomiar tutaj
zaczyna się od sprawdzenia ciszy i zapisuje, ile czekano oraz jakie było obciążenie przed i po.
Bramka ciszy ma dwa poziomy (uzasadnienie w README): twarda (load avg 1 min < 1,0 i brak obcych procesów .venv-exp)
przed każdym skryptem, oraz szybka między jednostkami w obrębie skryptu (chwilowe obciążenie obcych procesów < 4% CPU
w oknie 4 s + brak obcych procesów .venv-exp), bo load avg 1 min jest zanieczyszczony własnym poprzednim pomiarem.
"""
from __future__ import annotations

import json
import os
import platform
import random
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
REPO = EXP.parent.parent
SEED = 20261122
LOAD_THRESHOLD = 4.0  # reguła koordynatora (07:15): mierz przy loadavg1 < 4; wyżej czekaj ≤ max_wait i mierz mimo to z oznaczeniem „obciążony”
VENV_PY_SUFFIX = ".venv-exp/bin/python"


def loadavg() -> list[float]:
    return [round(x, 2) for x in os.getloadavg()]


def tree_pids(root: int | None = None) -> set[int]:
    """Proces `root` (domyślnie bieżący) i wszyscy potomkowie, wg /proc."""
    root = root or os.getpid()
    kids: dict[int, list[int]] = {}
    for d in Path("/proc").iterdir():
        if d.name.isdigit():
            try:
                st = (d / "stat").read_text()
                ppid = int(st[st.rindex(")") + 2:].split()[1])
                kids.setdefault(ppid, []).append(int(d.name))
            except (OSError, ValueError):
                pass
    out, stack = set(), [root]
    while stack:
        p = stack.pop()
        if p not in out:
            out.add(p)
            stack.extend(kids.get(p, []))
    return out


def _cpu_ticks(pid: str) -> int:
    try:
        st = Path(f"/proc/{pid}/stat").read_text()
        p = st[st.rindex(")") + 2:].split()
        return int(p[11]) + int(p[12])
    except (OSError, ValueError):
        return 0


_IDLE_SEEN: dict[str, int] = {}


def foreign_venv_procs(own: set[int] | None = None, active_only: bool = True) -> list[str]:
    """Procesy `.venv-exp/bin/python` spoza drzewa tego skryptu (tylko prawdziwe interpretery, nie powłoki z tekstem w argumentach)."""
    own = own if own is not None else tree_pids(_ROOT_PID)
    res = []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit() or int(d.name) in own:
            continue
        try:
            argv = (d / "cmdline").read_bytes().split(b"\0")
            exe = os.readlink(d / "exe")
        except OSError:
            continue
        if argv and argv[0].decode(errors="replace").endswith(VENV_PY_SUFFIX) and "python" in os.path.basename(exe):
            tk = _cpu_ticks(d.name)
            prev = _IDLE_SEEN.get(d.name)
            _IDLE_SEEN[d.name] = tk
            # proces bezczynny (osierocony serwer): bez przyrostu CPU między kolejnymi sprawdzeniami; nie liczy się jako obciążenie
            if active_only and prev is not None and tk - prev <= 2:
                continue
            res.append(f"{d.name}: " + " ".join(a.decode(errors="replace") for a in argv[1:3])[:120])
    return res


_ROOT_PID = os.getpid()


def cpu_busy_fraction(window_s: float = 4.0, own: set[int] | None = None) -> float:
    """Udział zajętego CPU całej maszyny w oknie minus CPU własnego drzewa procesów (0..1, względem wszystkich rdzeni)."""
    def snap() -> tuple[float, float, float]:
        f = Path("/proc/stat").read_text().splitlines()[0].split()[1:]
        v = [int(x) for x in f]
        idle = v[3] + v[4]
        total = sum(v[:8])
        own_t = 0.0
        for p in (own if own is not None else tree_pids(_ROOT_PID)):
            try:
                s = Path(f"/proc/{p}/stat").read_text()
                parts = s[s.rindex(")") + 2:].split()
                own_t += int(parts[11]) + int(parts[12])
            except (OSError, ValueError):
                pass
        return total - idle, total, own_t
    b0, t0, o0 = snap()
    time.sleep(window_s)
    b1, t1, o1 = snap()
    return max(0.0, ((b1 - b0) - (o1 - o0)) / max(1, t1 - t0))


def wait_quiet(max_wait_s: float = 3600.0, *, strict: bool = True, poll_s: float = 10.0, label: str = "") -> dict[str, Any]:
    """Czeka na ciszę. strict: load avg 1 min < 1,0 i brak obcych .venv-exp. Szybka: obcy CPU < 4% i brak obcych .venv-exp.
    Zwraca rekord: czas oczekiwania, powód ostatniej odmowy, load przed. Przy przekroczeniu limitu: quiet=False (wynik oznacza niewiążący pomiar)."""
    t0 = time.monotonic()
    reason = ""
    n = 0
    while True:
        la = os.getloadavg()[0]
        fp = foreign_venv_procs()
        ok = not fp
        reason = f"obce procesy .venv-exp: {len(fp)}" if fp else ""
        loaded = False
        if ok and strict:
            ok = la < LOAD_THRESHOLD
            reason = reason or f"loadavg1={la:.2f}"
            if not ok and time.monotonic() - t0 > max_wait_s:
                # decyzja koordynatora: obcych repozytoriów nie zabijamy; po 2 min przyjmujemy (tło maszyny ~20% CPU: IDE, przeglądarka, kwin) obcy CPU < 30% i oznaczamy jako obciążone
                busy = cpu_busy_fraction(2.0)
                ok, loaded = True, True
        if ok and not strict:
            busy = cpu_busy_fraction(2.0)
            loaded = busy > 0.04 or la >= LOAD_THRESHOLD  # tylko znacznik; nie blokuje (reguła koordynatora 07:15)
        if ok:
            return {"quiet": True, "waited_s": round(time.monotonic() - t0, 1), "polls": n, "loadavg_before": loadavg(), "gate": "strict" if strict else "fast", "label": label, "loaded_accepted": loaded, "loadavg1_threshold": LOAD_THRESHOLD, "busy_foreign_cpu": round(busy, 3) if "busy" in dir() else None,
                    "idle_foreign_venv": foreign_venv_procs(active_only=False)[:3]}
        n += 1
        if time.monotonic() - t0 > max_wait_s:
            return {"quiet": False, "waited_s": round(time.monotonic() - t0, 1), "polls": n, "loadavg_before": loadavg(), "gate": "strict" if strict else "fast",
                    "last_reason": reason, "foreign": fp[:5], "label": label}
        time.sleep(poll_s)


class Monitor:
    """Wątek próbkujący co 2 s obce procesy .venv-exp podczas jednostki pomiaru; jednostka z obcym procesem jest nieczysta."""

    def __init__(self, period: float = 2.0) -> None:
        self.period = period
        self.violations: list[str] = []
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.wait(self.period):
            fp = foreign_venv_procs()
            if fp:
                self.violations.append(fp[0])

    def __enter__(self) -> Monitor:
        self.load0 = loadavg()
        self.violations.extend(foreign_venv_procs())
        self._t.start()
        return self

    def __exit__(self, *a: object) -> None:
        self._stop.set()
        self._t.join()
        self.load1 = loadavg()
        self.violations.extend(foreign_venv_procs())
        try:
            own = tree_pids(_ROOT_PID)
            out = subprocess.run(["ps", "-eo", "pid,pcpu,comm", "--sort=-pcpu"], capture_output=True, text=True).stdout.splitlines()[1:12]
            self.top_foreign = [l.strip() for l in out if int(l.split()[0]) not in own and float(l.split()[1]) >= 5.0][:5]
        except (OSError, ValueError):
            self.top_foreign = []

    def record(self) -> dict[str, Any]:
        return {"loadavg_start": self.load0, "loadavg_end": self.load1, "foreign_during": sorted(set(self.violations))[:5], "top_cpu_foreign_at_end": getattr(self, "top_foreign", []), "clean": not self.violations}


def pctl(xs: list[float], q: float) -> float:
    s = sorted(xs)
    if not s:
        return float("nan")
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 4)


def stats(xs: list[float]) -> dict[str, Any]:
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "p50": pctl(xs, .5), "p95": pctl(xs, .95), "mean": round(statistics.fmean(xs), 4), "min": round(min(xs), 4), "max": round(max(xs), 4)}


def block_shuffled(configs: list[Any], reps: int, seed: int = SEED) -> list[tuple[int, Any]]:
    """Kolejność jednostek: w każdym bloku (powtórzeniu) wszystkie konfiguracje w losowej kolejności (ziarno stałe)."""
    rng = random.Random(seed)
    out = []
    for r in range(reps):
        b = list(configs)
        rng.shuffle(b)
        out += [(r, c) for c in b]
    return out


def cpu_model() -> str:
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return platform.processor()


def environment(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    import importlib.metadata as md

    def v(n: str) -> str | None:
        try:
            return md.version(n)
        except md.PackageNotFoundError:
            return None
    gov = None
    try:
        gov = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor").read_text().strip()
    except OSError:
        pass
    mem = {k: int(x.split()[0]) // 1024 for k, x in (l.split(":", 1) for l in Path("/proc/meminfo").read_text().splitlines()) if k in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree")}
    env = {"cpu_model": cpu_model(), "logical_cores": os.cpu_count(), "python": sys.version.split()[0], "kernel": platform.release(),
           "versions": {n: v(n) for n in ("rapidocr", "onnxruntime", "pypdfium2", "numpy", "pillow", "httpx", "fastapi", "uvicorn")},
           "cpu_governor": gov, "mem_mb": mem, "seed": SEED, "date": time.strftime("%Y-%m-%d %H:%M:%S %z"),
           "env_threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "ORT_NUM_THREADS")}}
    env.update(extra or {})
    return env


def rss_hwm_mb(pid: int | None = None) -> float:
    for line in Path(f"/proc/{pid or 'self'}/status").read_text().splitlines():
        if line.startswith("VmHWM:"):
            return round(int(line.split()[1]) / 1024, 1)
    return 0.0


def thread_count(pid: int | None = None) -> int:
    for line in Path(f"/proc/{pid or 'self'}/status").read_text().splitlines():
        if line.startswith("Threads:"):
            return int(line.split()[1])
    return 0


def dump(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(tmp, path)


def scope_cgroup_path(unit: str) -> Path:
    return Path("/sys/fs/cgroup/user.slice/user-%d.slice/user@%d.service/app.slice/%s.scope" % (os.getuid(), os.getuid(), unit))


def cgroup_mem_peak_mb(unit: str) -> float | None:
    try:
        return round(int((scope_cgroup_path(unit) / "memory.peak").read_text()) / 1048576, 1)
    except (OSError, ValueError):
        return None


def run_in_scope(unit: str, argv: list[str], *, env: dict[str, str] | None = None, mem_max: str = "14G", **kw: Any) -> subprocess.Popen[bytes]:
    """Uruchamia polecenie w scope systemd użytkownika z limitem pamięci całej grupy procesów (cgroup)."""
    return subprocess.Popen(["systemd-run", "--user", "--scope", "--quiet", f"--unit={unit}", "-p", f"MemoryMax={mem_max}", "-p", "MemorySwapMax=0", *argv],
                            env={**os.environ, **(env or {})}, **kw)
