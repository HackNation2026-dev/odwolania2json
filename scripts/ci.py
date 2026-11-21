#!/usr/bin/env python3
"""Lokalne kontrole jakości z poziomami hooków; artefakty trafiają wyłącznie do .ci/.

Poziomy (--profile): commit (budżet ~10 s, tylko zmienione pliki), push (budżet ~2 min,
pełne testy, API i mutacje przyrostowe względem merge-base z main). Pełne mutacje:
`--stage mutation`, ręcznie lub z crona.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import inspect
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

STAGES = ("docs", "lint", "types", "api", "test", "mutation", "audit")
# Budżety czasu w sekundach: informacyjne, przekroczenie jest raportowane, nie blokuje.
BUDGETS = {"commit": 10.0, "push": 120.0}
PUSH_BASE = "main"
ENGINE_VERSION = "3"
CACHE_PATH = ".ci/mutation-cache.json"
SCOPE_ROOTS = ("apps", "packages")
SHADOW_DATA_ROOTS = ("data", "docs/02-materialy")
MODEL_TESTS = ("tests/contract", "tests/unit/test_base.py")
DOCS_TRIGGERS = (
    "docs/",
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "VERSION",
    "scripts/verify_docs",
)
TOOL_FILES = ("pyproject.toml", "pytest.ini", "requirements-dev.txt", "requirements.txt")


@dataclass(frozen=True)
class Options:
    """Parametry pojedynczego etapu; domyślne wartości oznaczają pełny zakres."""

    fast: bool = False
    changed: bool = False
    since: str | None = None
    files: tuple[str, ...] | None = None
    jobs: int = 1
    timeout: float | None = None
    use_cache: bool = True
    coverage: bool = True
    partial: bool = False  # mutacje tylko linii zmienionych w indeksie
    max_survivors: int | None = None  # przerwij po tylu niezabitych (szybka informacja)


def environment(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(root / "apps/backend"), str(root / "packages/contracts"), env.get("PYTHONPATH", "")]
    )
    env["TMPDIR"] = str(root / ".ci/tmp")
    env["XDG_CACHE_HOME"] = str(root / ".ci/cache")
    return env


def execute(command: list[str], root: Path) -> bool:
    try:
        result = subprocess.run(command, cwd=root, env=environment(root), check=False)
    except OSError as error:
        print(f"FAIL uruchomienie: {error}")
        return False
    return result.returncode == 0


def require(module: str) -> bool:
    if importlib.util.find_spec(module) is not None:
        return True
    print(
        f"FAIL brak {module}; instalacja: python -m pip install -r requirements-dev.txt "
        "-r apps/backend/requirements.txt (albo ustaw CI_PYTHON na interpreter z narzędziami)"
    )
    return False


def reexec_in_project_python(root: Path) -> None:
    """Hooki wołają python3 z PATH; narzędzia leżą w CI_PYTHON lub .venv projektu."""
    if os.environ.get("CI_PYTHON_ACTIVE"):
        return
    candidates = [os.environ.get("CI_PYTHON"), str(root / ".venv/bin/python")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            os.environ["CI_PYTHON_ACTIVE"] = "1"
            os.execv(candidate, [candidate, *sys.argv])  # noqa: S606 - ten sam skrypt


def git_names(root: Path, *args: str) -> set[str]:
    result = subprocess.run(["git", *args, "-z"], cwd=root, check=True, capture_output=True)
    return {os.fsdecode(path) for path in result.stdout.split(b"\0") if path}


def changed_paths(root: Path) -> set[str]:
    """Nazwy po rename pochodzą wyłącznie z indeksu Git, także ze spacjami."""
    return git_names(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")


def since_paths(root: Path, ref: str) -> set[str] | None:
    """Pliki zmienione od merge-base z ref (także niezacommitowane i nowe); None = brak bazy."""
    result = subprocess.run(
        ["git", "merge-base", ref, "HEAD"], cwd=root, check=False, capture_output=True, text=True
    )
    base = result.stdout.strip()
    if result.returncode != 0 or not base:
        return None
    return git_names(root, "diff", "--name-only", "--diff-filter=ACMR", base) | git_names(
        root, "ls-files", "--others", "--exclude-standard"
    )


def is_ignored_part(path: Path) -> bool:
    return any(
        part in {"build", "__pycache__"} or part.endswith(".egg-info") for part in path.parts
    )


def mutation_paths(root: Path) -> list[str]:
    """Normalizatory, walidatory i moduły regex; nowe moduły wchodzą automatycznie."""
    paths: list[str] = []
    for directory in SCOPE_ROOTS:
        for path in sorted((root / directory).rglob("*.py")):
            relative = path.relative_to(root).as_posix()
            if is_ignored_part(path):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            regex = any(
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "re"
                for node in ast.walk(tree)
            )
            if (
                regex
                or any(word in path.stem for word in ("normaliz", "validat"))
                or (relative == "packages/contracts/odwolania2json_contracts/models.py")
            ):
                paths.append(relative)
    return paths


def declarative_mutants(source: str) -> Iterator[tuple[int, str]]:
    """Jednopunktowe mutacje cyfr, etykiet, formatów oraz typów wyniku.

    AST gwarantuje poprawną składnię, a każdy kandydat jest wykonywany osobno.
    Nie zmieniamy docstringów, opisów pól ani importów (to nie zachowanie).
    """
    tree = ast.parse(source)
    seen: set[str] = set()
    originals = ast.unparse(tree)
    patterns: set[int] = set()
    labels: set[int] = set()
    excluded: set[int] = set()
    model_fields: set[int] = set()
    for item in ast.walk(tree):
        if isinstance(item, ast.ClassDef):
            if any(isinstance(base, ast.Name) and base.id == "Protocol" for base in item.bases):
                excluded.update(id(child) for child in ast.walk(item))
            if any(isinstance(base, ast.Name) and base.id == "BaseModel" for base in item.bases):
                model_fields.update(
                    id(child) for child in item.body if isinstance(child, ast.AnnAssign)
                )
        # Przełączniki bibliotek (np. zip strict) często nie zmieniają zachowania.
        # Operator wartości logicznych obejmuje kod logiki, nie opcje wywołań.
        if (
            isinstance(item, ast.keyword)
            and isinstance(item.value, ast.Constant)
            and isinstance(item.value.value, bool)
        ):
            excluded.add(id(item.value))
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        if (
            isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "re"
            and call.args
        ):
            patterns.add(id(call.args[0]))
        for keyword in call.keywords:
            if keyword.arg == "pattern":
                patterns.add(id(keyword.value))
            if keyword.arg in {"alias", "extra"}:
                labels.add(id(keyword.value))
    for literal in ast.walk(tree):
        if (
            isinstance(literal, ast.Subscript)
            and isinstance(literal.value, ast.Name)
            and literal.value.id == "Literal"
        ):
            labels.update(id(node) for node in ast.walk(literal.slice))
    for node in ast.walk(tree):
        if id(node) in excluded:
            continue
        replacements: list[int | bool | str] = []
        if isinstance(node, ast.Constant):
            value = node.value
            if type(value) is int:
                replacements = [value + 1]
            elif type(value) is bool:
                replacements = [not value]
            elif isinstance(value, str) and value and id(node) in patterns:
                # Nie mutujemy składni regex ani zakresów liter: wiele takich
                # zmian jest równoważnych; cyfry i separatory badają format.
                for index, char in enumerate(value):
                    changed = (
                        str((int(char) + 1) % 10)
                        if char.isascii() and char.isdigit()
                        else "X"
                        if char.isalpha() and index == 0
                        else ";"
                        if char in ":.,/-"
                        else ""
                    )
                    if changed and changed != char:
                        candidate = value[:index] + changed + value[index + 1 :]
                        try:
                            re.compile(candidate)
                        except re.error:
                            continue
                        replacements.append(candidate)
            elif isinstance(value, str) and id(node) in labels:
                replacements = ["allow" if value == "forbid" else value + "X"]
            original = node.value
            for replacement in replacements:
                node.value = replacement
                rendered = ast.unparse(tree)
                node.value = original
                if rendered not in seen and rendered != originals:
                    seen.add(rendered)
                    yield node.lineno, rendered
        # Anotacje modeli są wykonywalnym walidatorem pydantic.
        if isinstance(node, ast.AnnAssign) and id(node) in model_fields:
            for name in ast.walk(node.annotation):
                if isinstance(name, ast.Name) and name.id in {"str", "int", "float", "bool"}:
                    original_name = name.id
                    name.id = "int" if original_name == "str" else "str"
                    rendered = ast.unparse(tree)
                    name.id = original_name
                    if rendered not in seen:
                        seen.add(rendered)
                        yield node.lineno, rendered


def declarative_variants(source: str) -> Iterator[str]:
    """Same mutanty bez numerów linii."""
    return (text for _, text in declarative_mutants(source))


def changed_lines(root: Path, paths: set[str]) -> dict[str, set[int]]:
    """Numery linii dodanych lub zmienionych w indeksie względem HEAD (git diff -U0)."""
    result: dict[str, set[int]] = {}
    for relative in sorted(paths):
        diff = subprocess.run(
            ["git", "diff", "--cached", "-U0", "--no-color", "--", relative],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        lines: set[int] = set()
        for match in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff, re.MULTILINE):
            start, count = int(match.group(1)), int(match.group(2) or 1)
            lines.update(range(start, start + count))
        result[relative] = lines
    return result


def module_tests(root: Path, relative: str) -> list[str]:
    """Testy obejmujące moduł: pliki testowe importujące go; brak = cały zestaw."""
    if relative.endswith("/models.py"):
        return list(MODEL_TESTS)
    name = re.escape(Path(relative).stem)
    # Tylko importy modułu; samo słowo w danych testowych (np. "nip") nie wybiera testu.
    pattern = re.compile(
        rf"^\s*(?:from\s+[\w.]*\b{name}\s+import\b|import\s+[\w.]*\b{name}\b"
        rf"|from\s+[\w.]+\s+import\s+[^\n]*\b{name}\b|.*import_module\(['\"]{name}['\"]\))",
        re.MULTILINE,
    )
    found = [
        path.relative_to(root).as_posix()
        for path in sorted((root / "tests").rglob("test_*.py"))
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    return found or ["tests"]


def select_tests(root: Path, files: tuple[str, ...]) -> list[str] | None:
    """Testy dla zmienionych plików; None = cały zestaw, [] = nic do uruchomienia."""
    selected: list[str] = []
    for relative in sorted(files):
        path = Path(relative)
        if relative in TOOL_FILES or path.name == "conftest.py":
            return None
        if path.suffix != ".py":
            continue
        if path.parts[0] == "tests":
            if path.name.startswith("test_") and (root / relative).exists():
                selected.append(relative)
        elif path.parts[0] in (*SCOPE_ROOTS, "scripts"):
            mapped = module_tests(root, relative)
            if mapped == ["tests"]:
                return None
            selected.extend(mapped)
    return list(dict.fromkeys(selected))


def engine_fingerprint() -> str:
    """Zmiana operatorów mutacji unieważnia cache."""
    digest = hashlib.sha256(ENGINE_VERSION.encode())
    digest.update(inspect.getsource(declarative_variants).encode())
    digest.update(f"{sys.version_info[0]}.{sys.version_info[1]}".encode())
    return digest.hexdigest()


def cache_key(root: Path, relative: str, tests: list[str]) -> str:
    """Skrót kodu modułu, wybranych testów, conftest i konfiguracji pytest."""
    digest = hashlib.sha256(engine_fingerprint().encode())
    files = {root / relative, root / "pytest.ini"}
    for test in tests:
        path = root / test
        files.update(path.rglob("*.py") if path.is_dir() else [path])
    files.update((root / "tests").rglob("conftest.py"))
    for path in sorted(files):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def load_cache(root: Path) -> dict[str, dict[str, object]]:
    try:
        data = json.loads((root / CACHE_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    entries = data.get("entries") if isinstance(data, dict) else None
    return entries if isinstance(entries, dict) else {}


def save_cache(root: Path, entries: dict[str, dict[str, object]]) -> None:
    """Zapis atomowy: plik tymczasowy, fsync, zamiana."""
    target = root / CACHE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=target.parent, prefix=".mutation-cache-")
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump({"version": 1, "entries": entries}, handle, indent=1, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, target)


def make_shadow(root: Path, shadow: Path, paths: list[str]) -> None:
    """Kopia źródeł, w której podmieniamy mutanta; repozytorium i testy pozostają nietknięte."""
    ignore = shutil.ignore_patterns("__pycache__", "*.egg-info", "build")
    # Moduły domyślnie czytają dane spoza SCOPE_ROOTS (loader, dataset), więc ich
    # bazowe testy w kopii muszą widzieć te same dane, inaczej mutacje się nie uruchomią.
    for top in (*SCOPE_ROOTS, *SHADOW_DATA_ROOTS):
        if (root / top).is_dir():
            shutil.copytree(root / top, shadow / top, ignore=ignore)
    for relative in paths:
        if not (shadow / relative).exists():
            (shadow / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / relative, shadow / relative)
    (shadow / "_tmp").mkdir(parents=True, exist_ok=True)


def shadow_environment(root: Path, shadow: Path) -> dict[str, str]:
    env = environment(root)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(shadow / "apps/backend"), str(shadow / "packages/contracts"), str(shadow)]
    )
    env["TMPDIR"] = str(shadow / "_tmp")
    # Wtyczki z entry pointów kosztują ~1/3 czasu startu pytest, a testy ich nie używają.
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return env


def verify_shadow_loading(root: Path, shadow: Path, relative: str) -> bool:
    """Mutant ma być faktycznie importowany z kopii, a nie z instalacji edytowalnej."""
    for prefix in ("apps/backend/", "packages/contracts/"):
        if relative.startswith(prefix):
            module = relative.removeprefix(prefix).removesuffix(".py").replace("/", ".")
            break
    else:
        return True
    code = f"import importlib.util as u; s = u.find_spec({module!r}); print(s.origin if s else '')"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        env=shadow_environment(root, shadow),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip().startswith(str(shadow))


def run_pytest(
    root: Path, shadow: Path, tests: list[str], extra: list[str], timeout: float
) -> tuple[int, float, str]:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-x",
        "-q",
        "-m",
        "not eval",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        str(shadow / "_pytest"),
        *tests,
        *extra,
    ]
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=root,
            env=shadow_environment(root, shadow),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return -1, time.monotonic() - started, ""
    return result.returncode, time.monotonic() - started, result.stdout or ""


@dataclass
class ModuleResult:
    relative: str
    status: str = "OK"
    detail: str = ""
    total: int = 0
    seconds: float = 0.0
    survivors: list[int] = field(default_factory=list)
    partial: bool = False
    not_run: int = 0


def check_mutants(
    root: Path,
    paths: list[str],
    *,
    jobs: int = 1,
    timeout: float | None = None,
    use_cache: bool = True,
    ci_root: Path | None = None,
    lines: dict[str, set[int]] | None = None,
    max_survivors: int | None = None,
) -> bool:
    """Kod 1 pytest zabija mutanta; przeżycie, błąd i timeout blokują. SKIP tylko z cache.

    root: drzewo z testami (kopia indeksu lub repozytorium); ci_root: gdzie cache i raport.
    lines: tylko mutanty w tych liniach (wynik częściowy, nie trafia do cache);
    max_survivors: po tylu niezabitych reszta mutantów nie jest uruchamiana.
    """
    ci_root = ci_root or root
    (ci_root / ".ci").mkdir(exist_ok=True)
    cache = load_cache(ci_root) if use_cache else {}
    results = {relative: ModuleResult(relative) for relative in paths}
    pending: list[str] = []
    keys: dict[str, str] = {}
    tests_for: dict[str, list[str]] = {}
    for relative in paths:
        tests_for[relative] = module_tests(root, relative)
        keys[relative] = cache_key(root, relative, tests_for[relative])
        entry = cache.get(relative)
        if use_cache and entry and entry.get("key") == keys[relative]:
            results[relative].status = "SKIP"
            results[relative].total = int(str(entry.get("mutants", 0)))
            results[relative].detail = "cache: niezmieniony kod i testy, poprzedni przebieg zielony"
        else:
            pending.append(relative)
    jobs = max(1, min(jobs, 64)) if pending else 1
    work = Path(tempfile.mkdtemp(dir=ci_root / ".ci", prefix="mutation-"))
    sources = {relative: (root / relative).read_text(encoding="utf-8") for relative in pending}
    failures: list[tuple[str, int, str]] = []
    try:
        shadows: queue.Queue[Path] = queue.Queue()
        for number in range(jobs):
            shadow = work / f"w{number}"
            make_shadow(root, shadow, pending)
            shadows.put(shadow)
        if pending and not verify_shadow_loading(root, work / "w0", pending[0]):
            print("FAIL mutacje: mutant nie jest ładowany z kopii (instalacja ma pierwszeństwo)")
            return False

        def with_shadow[T](job: Callable[[Path], T]) -> T:
            shadow = shadows.get()
            try:
                return job(shadow)
            finally:
                shadows.put(shadow)

        def baseline(relative: str) -> tuple[str, int, float, str]:
            code, seconds, output = with_shadow(
                lambda shadow: run_pytest(root, shadow, tests_for[relative], [], 600.0)
            )
            return relative, code, seconds, output

        durations: dict[str, float] = {}
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            ready: list[str] = []
            for relative, code, seconds, output in pool.map(baseline, pending):
                if code == 0:
                    ready.append(relative)
                    durations[relative] = seconds
                    continue
                failed = [
                    line for line in output.splitlines() if line.startswith(("FAILED", "ERROR"))
                ] or output.splitlines()[-3:]
                results[relative].status = "FAIL"
                results[relative].detail = "testy bazowe nie przechodzą" + "".join(
                    f"\n    {line}" for line in failed[:5]
                )
            tasks: list[tuple[str, int, str]] = []
            for relative in ready:
                every = list(declarative_mutants(sources[relative]))
                variants = [text for _, text in every]
                if lines is not None:
                    results[relative].partial = True
                    wanted = lines.get(relative, set())
                    variants = [text for number, text in every if number in wanted]
                results[relative].total = len(variants)
                tasks.extend((relative, index, text) for index, text in enumerate(variants, 1))
                if not variants and lines is not None:
                    results[relative].status = "SKIP"
                    results[relative].detail = "brak mutantów w zmienionych liniach"
                elif not variants:
                    results[relative].status = "FAIL"
                    results[relative].detail = "brak mutantów: operatory niczego nie zmieniają"

            lock = threading.Lock()
            survived = [0]

            def mutant(task: tuple[str, int, str]) -> tuple[str, int, int | None, float]:
                relative, index, text = task
                if max_survivors is not None and survived[0] >= max_survivors:
                    return relative, index, None, 0.0
                limit = timeout or min(120.0, max(10.0, durations[relative] * 5))
                extra = (
                    ["-k", "not test_generated_models_match_committed_file"]
                    if relative.endswith("/models.py")
                    else []
                )

                def attempt(shadow: Path) -> tuple[int, float, str]:
                    target = shadow / relative
                    target.write_text(text, encoding="utf-8")
                    try:
                        return run_pytest(root, shadow, tests_for[relative], extra, limit)
                    finally:
                        target.write_text(sources[relative], encoding="utf-8")

                code, seconds, _ = with_shadow(attempt)
                if code != 1:
                    with lock:
                        survived[0] += 1
                return relative, index, code, seconds

            texts = {(r, i): t for r, i, t in tasks}
            report: list[str] = []
            for relative, index, outcome, spent in pool.map(mutant, tasks):
                if outcome is None:
                    results[relative].not_run += 1
                    report.append(f"{relative}:{index} not-run")
                    continue
                status = "killed" if outcome == 1 else "survived" if outcome == 0 else "error"
                report.append(f"{relative}:{index} {status} exit={outcome} {spent:.2f}s")
                results[relative].seconds += spent
                if outcome != 1:
                    results[relative].status = "FAIL"
                    results[relative].survivors.append(index)
                    failures.append((relative, index, texts[relative, index]))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return finish_mutation(
        ci_root, results, cache, keys, failures, [*report, *report_lines(results)]
    )


def report_lines(results: dict[str, ModuleResult]) -> list[str]:
    return [
        f"{item.status:4} {item.relative} mutanty={item.total} "
        f"nieudane={len(item.survivors)} {item.seconds:.1f}s {item.detail}".rstrip()
        for item in results.values()
    ]


def finish_mutation(
    ci_root: Path,
    results: dict[str, ModuleResult],
    cache: dict[str, dict[str, object]],
    keys: dict[str, str],
    failures: list[tuple[str, int, str]],
    lines: list[str],
) -> bool:
    destination = ci_root / ".ci/mutation-failures"
    shutil.rmtree(destination, ignore_errors=True)
    for relative, index, text in failures:
        target = destination / f"{Path(relative).stem}-{index}.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    (ci_root / ".ci/mutation-report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for item in results.values():
        killed = item.total - len(item.survivors) - item.not_run
        print(
            f"{item.status:4} mutation {item.relative}: mutanty {item.total}, zabite {killed}, "
            f"przeżyte lub błędne {len(item.survivors)}, {item.seconds:.1f} s"
            + (f", nieuruchomione po przerwaniu {item.not_run}" if item.not_run else "")
            + (" (tylko zmienione linie)" if item.partial else "")
            + (f" — {item.detail}" if item.detail else ""),
            flush=True,
        )
        if item.status == "OK" and not item.partial:
            cache[item.relative] = {"key": keys[item.relative], "mutants": item.total}
        elif item.status == "FAIL":
            cache.pop(item.relative, None)
    save_cache(ci_root, cache)
    return bool(results) and all(item.status != "FAIL" for item in results.values())


def mutation(root: Path, opts: Options) -> bool | None:
    """Zakres: --changed (kopia indeksu), --since (od merge-base) albo wszystko."""
    scope: set[str] | None = None
    if opts.changed:
        scope = changed_paths(root)
        if not scope:
            print("SKIP mutation — brak staged plików w zakresie")
            return None
    elif opts.since:
        scope = since_paths(root, opts.since)
        if scope is None:
            print(f"UWAGA: brak merge-base z {opts.since}; zakres mutacji pełny")
    (root / ".ci").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root / ".ci", prefix="snapshot-") as temporary:
        work = root
        if opts.changed:
            work = Path(temporary)
            subprocess.run(
                ["git", "checkout-index", "--all", f"--prefix={work}/"],
                cwd=root,
                check=True,
                capture_output=True,
            )
        paths = mutation_paths(work)
        if scope is not None:
            paths = [
                path
                for path in paths
                if path in scope or any(test in scope for test in module_tests(work, path))
            ]
            if not paths:
                print("SKIP mutation — brak zmian w zakresie mutacji")
                return None
        lines = changed_lines(root, set(paths)) if opts.partial and opts.changed else None
        return check_mutants(
            work,
            paths,
            jobs=opts.jobs,
            timeout=opts.timeout,
            use_cache=opts.use_cache,
            ci_root=root,
            lines=lines,
            max_survivors=opts.max_survivors,
        )


def audit(root: Path) -> bool | None:
    """Brak sieci to jawny SKIP; błędy narzędzia i podatności to FAIL."""
    if not require("pip_audit"):
        return False
    try:
        with urllib.request.urlopen("https://pypi.org/simple/", timeout=5):
            pass
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"SKIP audit — brak sieci do PyPI: {error}")
        return None
    return execute(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "--disable-pip",
            "--no-deps",
            "-r",
            "apps/backend/requirements.txt",
        ],
        root,
    )


def lint(root: Path, opts: Options) -> bool | None:
    if not require("ruff"):
        return False
    targets = ["."]
    if opts.files is not None:
        targets = [f for f in opts.files if f.endswith(".py") and (root / f).exists()]
        if not targets:
            print("SKIP lint — brak zmienionych plików Pythona")
            return None
    base = [sys.executable, "-m", "ruff"]
    flags = ["--cache-dir", ".ci/ruff", "--force-exclude"]
    return execute([*base, "check", *flags, *targets], root) and execute(
        [*base, "format", "--check", *flags, *targets], root
    )


def test(root: Path, opts: Options) -> bool | None:
    if not require("pytest"):
        return False
    command = [sys.executable, "-m", "pytest", "-m", "not eval", "-o", "cache_dir=.ci/pytest"]
    command += ["--basetemp", str(root / ".ci/pytest-tmp")]
    if opts.files is not None:
        selected = select_tests(root, opts.files)
        if selected == []:
            print("SKIP test — zmiany nie dotyczą kodu ani testów")
            return None
        # Szybka ścieżka commita: zmienione moduły, bez pokrycia (pokrycie sprawdza pre-push).
        command += ["-o", "addopts=", "-q", "-x", *(selected or [])]
        return execute(command, root)
    if not require("pytest_cov"):
        return False
    return execute(
        [
            *command,
            "-p",
            "pytest_cov",
            "--cov=odwolania2json",
            "--cov=odwolania2json_contracts",
            "--cov-report=term-missing",
        ],
        root,
    )


def run_stage(stage: str, root: Path, opts: Options) -> bool | None:
    python = sys.executable
    if stage == "docs":
        return execute([python, "scripts/verify_docs.py"], root)
    if stage == "lint":
        return lint(root, opts)
    if stage == "types":
        return require("mypy") and execute(
            [
                python,
                "-m",
                "mypy",
                "--strict",
                "--cache-dir",
                ".ci/mypy",
                "apps/",
                "packages/",
                "scripts/ci.py",
            ],
            root,
        )
    if stage == "api":
        return all(
            require(name) for name in ("yaml", "openapi_spec_validator", "datamodel_code_generator")
        ) and execute(
            [python, "scripts/validate_api.py", "--stage", "spec" if opts.fast else "all"], root
        )
    if stage == "test":
        return test(root, opts)
    if stage == "audit":
        return audit(root)
    return mutation(root, opts)


def commit_plan(staged: set[str]) -> dict[str, Options]:
    """Etapy pre-commit zależne od zmienionych plików; reszta jest jawnie pomijana."""
    python = sorted(path for path in staged if path.endswith(".py"))
    source = [p for p in python if p.startswith(SCOPE_ROOTS)]
    tools = [p for p in staged if p in TOOL_FILES]
    files = tuple(sorted(staged))
    plan: dict[str, Options] = {}
    if any(p.startswith(DOCS_TRIGGERS) for p in staged):
        plan["docs"] = Options()
    if python or tools:
        plan["lint"] = Options(files=tuple(python) if not tools else None)
        plan["test"] = Options(files=files)
    if source or tools:
        plan["types"] = Options()
    if any(
        p.startswith(("packages/contracts/", "scripts/validate_api", "scripts/generate_con"))
        for p in staged
    ):
        plan["api"] = Options(fast=True)
    if source or any(p.startswith("tests/") for p in python):
        plan["mutation"] = Options(changed=True, jobs=default_jobs(), partial=True, max_survivors=3)
    return plan


def default_jobs() -> int:
    return max(1, min(os.cpu_count() or 1, 8))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=(*STAGES, "all"), default="all")
    parser.add_argument("--profile", choices=tuple(BUDGETS), help="poziom hooka: commit lub push")
    parser.add_argument("--fast", action="store_true", help="docs, lint, types, api spec")
    parser.add_argument("--keep-going", action="store_true", help="kontynuuj po błędzie")
    parser.add_argument("--changed", action="store_true", help="mutacje kopii indeksu git")
    parser.add_argument("--since", metavar="REF", help="mutacje od merge-base z REF")
    parser.add_argument("--files", nargs="+", metavar="PLIK", help="lint i testy tylko dla plików")
    parser.add_argument("--spec", action="store_true", help="etap api: tylko specyfikacja")
    parser.add_argument("--jobs", type=int, default=default_jobs(), help="równoległe mutanty")
    parser.add_argument("--mutant-timeout", type=float, help="limit sekund na mutanta")
    parser.add_argument("--no-cache", action="store_true", help="ignoruj cache mutacji")
    return parser


def validate(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.profile and (
        args.stage != "all" or args.fast or args.changed or args.since or args.files or args.spec
    ):
        parser.error("--profile nie łączy się z --stage, --fast, --changed, --since, --files")
    if args.changed and args.since:
        parser.error("--changed i --since wykluczają się")
    if (args.changed or args.since) and (args.stage != "mutation" or args.fast):
        parser.error("--changed i --since wymagają --stage mutation")
    if args.files and args.stage not in {"lint", "test"}:
        parser.error("--files wymaga --stage lint lub test")
    if args.spec and args.stage != "api":
        parser.error("--spec wymaga --stage api")
    if args.fast and args.stage != "all":
        parser.error("--fast wymaga --stage all (domyślny)")
    if args.jobs < 1:
        parser.error("--jobs musi być dodatnie")


def build_plan(args: argparse.Namespace, root: Path) -> dict[str, Options]:
    jobs = args.jobs
    if args.profile == "commit":
        return commit_plan(changed_paths(root))
    if args.profile == "push":
        shared = Options(jobs=jobs, since=PUSH_BASE, max_survivors=10)
        return dict.fromkeys(STAGES[:6], shared)
    selected = STAGES[:4] if args.fast else STAGES if args.stage == "all" else (args.stage,)
    options = Options(
        fast=args.fast or args.spec,
        changed=args.changed,
        since=args.since,
        files=tuple(args.files) if args.files else None,
        jobs=jobs,
        timeout=args.mutant_timeout,
        use_cache=not args.no_cache,
    )
    return dict.fromkeys(selected, options)


def main(argv: list[str] | None = None, *, root: Path | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate(parser, args)
    root = root or Path(__file__).resolve().parents[1]
    (root / ".ci/tmp").mkdir(parents=True, exist_ok=True)
    plan = build_plan(args, root)
    reason = "poza zakresem zmian" if args.profile else "niewybrany lub zatrzymany po błędzie"
    failed = False
    began = time.monotonic()
    for stage in STAGES:
        if stage not in plan or (failed and not args.keep_going):
            print(f"SKIP {stage:8} 0.00 s — {reason}", flush=True)
            continue
        started = time.monotonic()
        try:
            ok = run_stage(stage, root, plan[stage])
        except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
            print(f"FAIL {error}")
            ok = False
        elapsed = time.monotonic() - started
        label = "SKIP" if ok is None else "OK" if ok else "FAIL"
        print(f"{label:4} {stage:8} {elapsed:.2f} s", flush=True)
        failed = failed or ok is False
    if args.profile:
        total = time.monotonic() - began
        budget = BUDGETS[args.profile]
        verdict = "w budżecie" if total <= budget else "BUDŻET PRZEKROCZONY"
        label = "FAIL" if failed else "OK"
        print(f"{label:4} razem    {total:.2f} s (budżet {budget:.0f} s: {verdict})")
    return int(failed)


if __name__ == "__main__":
    reexec_in_project_python(Path(__file__).resolve().parents[1])
    raise SystemExit(main())
