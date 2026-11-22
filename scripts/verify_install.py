"""Test czystej instalacji: tymczasowe venv, `pip install -r requirements.txt`, `process`.

Sprawdza to, co zobaczy jury: instalacja z PyPI bez narzędzi deweloperskich, wagi OCR
w kole (bez pobierania przy starcie), `process` na trzech małych PDF-ach z lokalną
atrapą LLM podaną przez `LLM_BASE_URL`. Kod wyjścia 0 = OK, 1 = błąd, 3 = SKIP (brak
sieci do PyPI: jawnie, nie jako sukces).

Użycie: ``python scripts/verify_install.py [--python PYTHON] [--keep] [--requirements PLIK]``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import TracebackType

ROOT = Path(__file__).resolve().parents[1]
EXIT_OK, EXIT_FAIL, EXIT_SKIP = 0, 1, 3
MIN_PYTHON = (3, 13)
SAMPLE_NAMES = ("odwolanie-a", "odwolanie-b", "odwolanie-c")


def python_is_supported(version: tuple[int, ...]) -> bool:
    """Wymóg organizatora: Python 3.13+."""
    return tuple(version[:2]) >= MIN_PYTHON


def _pdf_with_text(text: str) -> bytes:
    """Buduje minimalny poprawny PDF 1.4 z jedną stroną i tabelą xref o właściwych offsetach."""
    stream = f"BT /F1 14 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    size = len(objects) + 1
    out += f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def write_sample_pdfs(directory: Path, count: int = 3) -> list[Path]:
    """Zapisuje `count` różnych, małych PDF-ów w `directory`."""
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for index in range(count):
        name = SAMPLE_NAMES[index] if index < len(SAMPLE_NAMES) else f"odwolanie-{index}"
        path = directory / f"{name}.pdf"
        path.write_bytes(_pdf_with_text(f"Odwolanie testowe numer {index + 1}"))
        paths.append(path)
    return paths


class MockLlm:
    """Lokalna atrapa API zgodnego z OpenAI (`/chat/completions`) na wolnym porcie."""

    def __init__(self) -> None:
        self.requests = 0
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                owner.requests += 1
                body = json.dumps(
                    {
                        "id": "mock",
                        "object": "chat.completion",
                        "choices": [
                            {
                                "index": 0,
                                "finish_reason": "stop",
                                "message": {"role": "assistant", "content": "{}"},
                            }
                        ],
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                """Cisza: atrapa nie zaśmieca wyjścia."""

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port: int = self._server.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> MockLlm:
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def check_outputs(output_dir: Path, stems: list[str]) -> list[str]:
    """Zwraca listę problemów: brakujące albo niepoprawne pliki wyniku."""
    problems = []
    for stem in stems:
        path = output_dir / f"{stem}.json"
        if not path.is_file():
            problems.append(f"brak pliku wyniku {path.name}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            problems.append(f"niepoprawny JSON w {path.name}: {error}")
    return problems


def pypi_reachable(timeout: float = 5.0) -> bool:
    try:
        with urllib.request.urlopen("https://pypi.org/simple/", timeout=timeout):
            return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def _directory_size_mb(path: Path) -> float:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e6


def verify(python: str, requirements: str, keep: bool) -> int:
    """Wykonuje pełny scenariusz w katalogu tymczasowym; zwraca kod wyjścia."""
    work = Path(tempfile.mkdtemp(prefix="o2j-verify-"))
    try:
        venv = work / "venv"
        started = time.monotonic()
        _run([python, "-m", "venv", str(venv)], ROOT)
        interpreter = str(_venv_python(venv))
        _run(
            [
                interpreter,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--disable-pip-version-check",
                "-r",
                requirements,
            ],
            ROOT,
        )
        print(
            f"OK instalacja: {time.monotonic() - started:.0f} s, "
            f"venv {_directory_size_mb(venv):.0f} MB"
        )
        weights = subprocess.run(
            [
                interpreter,
                "-c",
                "import pathlib, rapidocr; "
                "print(len(list(pathlib.Path(rapidocr.__file__).parent.rglob('*.onnx'))))",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if int(weights) < 3:
            print(f"FAIL wagi OCR: w kole rapidocr tylko {weights} plików .onnx (oczekiwano ≥ 3)")
            return EXIT_FAIL
        print(f"OK wagi OCR w kole: {weights} plików .onnx (bez pobierania przy starcie)")
        input_dir, output_dir = work / "input", work / "output"
        paths = write_sample_pdfs(input_dir)
        with MockLlm() as mock:
            env = {
                "PATH": str(venv / ("Scripts" if sys.platform == "win32" else "bin")),
                "SYSTEMROOT": str(Path(sys.executable).anchor),
                "LLM_BASE_URL": mock.base_url,
                "LLM_API_KEY": "klucz-testowy",
                "LLM_MODEL": "atrapa",
                "PYTHONUTF8": "1",
            }
            result = subprocess.run(
                [interpreter, "-m", "odwolania2json", "process", str(input_dir), str(output_dir)],
                cwd=work,
                env=env,
                check=False,
            )
        if result.returncode != 0:
            print(f"FAIL process: kod wyjścia {result.returncode}")
            return EXIT_FAIL
        problems = check_outputs(output_dir, [path.stem for path in paths])
        for problem in problems:
            print(f"FAIL {problem}")
        if problems:
            return EXIT_FAIL
        print(f"OK process: {len(paths)} PDF-y → {len(paths)} plików JSON")
        return EXIT_OK
    except (subprocess.CalledProcessError, OSError) as error:
        print(f"FAIL {error}")
        return EXIT_FAIL
    finally:
        if keep:
            print(f"zachowano katalog roboczy: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default=sys.executable, help="interpreter 3.13+ do venv")
    parser.add_argument("--requirements", default="requirements.txt", help="plik zależności")
    parser.add_argument("--keep", action="store_true", help="nie usuwaj katalogu roboczego")
    arguments = parser.parse_args(argv)
    if arguments.python == sys.executable and not python_is_supported(sys.version_info[:2]):
        print(f"FAIL potrzebny Python 3.13+, a to {sys.version.split()[0]}; podaj --python")
        return EXIT_FAIL
    if not pypi_reachable():
        print("SKIP brak sieci do PyPI: czystej instalacji nie sprawdzono")
        return EXIT_SKIP
    return verify(arguments.python, arguments.requirements, arguments.keep)


if __name__ == "__main__":
    raise SystemExit(main())
