"""Pomiar produktu: `process` na podzbiorze spraw rozwojowych i ocena ewaluatorem zespołu.

Skrypt kopiuje PDF-y wybranych spraw (oraz negatywy organizatora) do katalogu
roboczego, uruchamia `python -m odwolania2json process` z prawdziwym LLM i liczy
F1 przybliżony z przedziałem z bootstrapu po sprawach. Wynik NIE jest oficjalnym F1.

Zasady:
- tylko sprawy rozwojowe z `data/podzial.json`; sprawa kontrolna przerywa skrypt;
- klucz czytany jest przez produkt z pliku (`LLM_API_KEY_FILE`); skrypt nie otwiera
  pliku z kluczem, nie wypisuje go i nie zapisuje w wynikach;
- limit wywołań LLM na przebieg (`--max-calls`) chroni budżet konta;
- przy HTTP 429 wynik jest oznaczony jako niepełny: nie uzupełniamy liczb.

Przykład:
    python scripts/eval_process.py --out .ci/eval-process/wynik.json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT / "apps" / "backend", ROOT / "packages" / "contracts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from odwolania2json.bootstrap import bootstrap_f1, case_totals  # noqa: E402
from odwolania2json.dataset import load_split  # noqa: E402
from odwolania2json.evaluator import ClassTotals, DocumentMetrics, compare_document  # noqa: E402
from odwolania2json.loader import (  # noqa: E402
    MATERIALS_DIR,
    CaseReference,
    load_case_references,
    load_reference_json,
    result_name_for,
)

DEFAULT_SUBSET = ROOT / "experiments/2026-11-21-wybor-modulow/llm-e2e/subset_dev.json"
DEFAULT_WORK = ROOT / ".ci" / "eval-process"
DEFAULT_BASE_URL = "https://api.minimax.io/anthropic/v1/messages"
DEFAULT_MODEL = "MiniMax-M3.1-Flash-Preview"
DEFAULT_KEY_FILE = "~/kluczMiniMaxKacper"
NEGATIVE_CASE = "negatywne"
SEED = 20261122
RESAMPLES = 2000
# Kody, przy których liczby nie opisują produktu, tylko stan konta lub sieci.
TRANSIENT_CODES = frozenset({"llm_rate_limit", "llm_unavailable", "llm_call_limit"})
EXIT_OK, EXIT_FAIL, EXIT_INCOMPLETE = 0, 1, 3


def select_references(cases: list[str], negatives: bool) -> list[CaseReference]:
    """Dokumenty wybranych spraw; sprawa spoza zbioru rozwojowego to błąd."""
    split = load_split()
    forbidden = sorted(set(cases) - split.rozwojowy)
    if forbidden:
        raise SystemExit(f"błąd: sprawy spoza zbioru rozwojowego: {', '.join(forbidden)}")
    wanted = set(cases) | ({NEGATIVE_CASE} if negatives else set())
    return [ref for ref in load_case_references() if ref.case_id in wanted]


def prepare_input(references: list[CaseReference], input_dir: Path) -> None:
    """Kopiuje PDF-y do świeżego katalogu wejścia w układzie `sprawa/plik.pdf`."""
    if input_dir.exists():
        shutil.rmtree(input_dir)
    for ref in references:
        target = input_dir / ref.case_id / ref.input_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(MATERIALS_DIR / "dane" / ref.case_id / ref.input_name, target)


def run_process(input_dir: Path, output_dir: Path, args: argparse.Namespace) -> tuple[int, float]:
    """Uruchamia produkt w osobnym procesie; zwraca kod wyjścia i czas ścienny."""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    key_file = Path(args.key_file).expanduser()
    if not key_file.is_file():
        raise SystemExit(f"błąd: brak pliku z kluczem: {key_file}")
    env = {
        **{name: value for name, value in os.environ.items() if not name.startswith("LLM_")},
        "PYTHONPATH": os.pathsep.join(
            [str(ROOT / "apps" / "backend"), str(ROOT / "packages" / "contracts")]
        ),
        "LLM_API_KEY_FILE": str(key_file),
        "LLM_BASE_URL": args.base_url,
        "LLM_MODEL": args.model,
        "LLM_PROTOCOL": args.protocol,
        "LLM_MAX_CALLS": str(args.max_calls),
        "PYTHONUTF8": "1",
    }
    started = time.monotonic()
    result = subprocess.run(
        [sys.executable, "-m", "odwolania2json", "process", str(input_dir), str(output_dir)],
        cwd=ROOT,
        env=env,
        check=False,
    )
    return result.returncode, time.monotonic() - started


def read_report(output_dir: Path) -> dict[str, dict[str, object]]:
    path = output_dir / "report.jsonl"
    if not path.is_file():
        return {}
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return {str(record["input"]): record for record in records}


def _f1_block(metrics: list[DocumentMetrics]) -> dict[str, object]:
    counts: Counter[str] = Counter()
    for item in metrics:
        counts.update(outcome.verdict for outcome in item.outcomes)
    totals = ClassTotals(tp=counts["tp"], tn=counts["tn"], fp=counts["fp"], fn=counts["fn"])
    block: dict[str, object] = {
        "documents": len(metrics),
        "cases": len({item.case_id for item in metrics}),
        "tp": totals.tp,
        "fp": totals.fp,
        "fn": totals.fn,
        "f1": round(totals.f1, 4),
        "ci95": None,
    }
    if totals.tp + totals.fp + totals.fn:
        interval = bootstrap_f1(case_totals(metrics), seed=SEED, resamples=RESAMPLES)
        block["ci95"] = [round(interval.low, 4), round(interval.high, 4)]
    return block


def evaluate(references: list[CaseReference], output_dir: Path) -> dict[str, object]:
    """Porównuje pliki wyniku z referencjami; brak pliku liczy się jak `{}`."""
    report = read_report(output_dir)
    metrics: list[DocumentMetrics] = []
    statuses: Counter[str] = Counter()
    codes: Counter[str] = Counter()
    missing = 0
    for ref in references:
        relative = f"{ref.case_id}/{ref.input_name}"
        result_path = output_dir / ref.case_id / result_name_for(ref.input_name)
        predicted: dict[str, object] = {}
        if result_path.is_file():
            predicted = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            missing += 1
        record = report.get(relative, {})
        statuses[str(record.get("status", "brak_w_raporcie"))] += 1
        errors = record.get("errors")
        for error in errors if isinstance(errors, list) else []:
            codes[str(error["code"])] += 1
        predicted_class = record.get("document_class") or "obcy"
        metrics.append(
            DocumentMetrics(
                case_id=ref.case_id,
                input_name=ref.input_name,
                document_class=ref.document_class,
                outcomes=compare_document(predicted, load_reference_json(ref)),
                classification="tp" if predicted_class == ref.document_class else "fn",
            )
        )
    per_class = {
        name: _f1_block([item for item in metrics if item.document_class == name])
        for name in ("odwolanie", "pelnomocnictwo", "przelew", "obcy")
        if any(item.document_class == name for item in metrics)
    }
    transient = sum(count for code, count in codes.items() if code in TRANSIENT_CODES)
    return {
        "all": _f1_block(metrics),
        "per_class": per_class,
        "classification_accuracy": round(
            sum(item.classification == "tp" for item in metrics) / max(1, len(metrics)), 4
        ),
        "statuses": dict(sorted(statuses.items())),
        "error_codes": dict(sorted(codes.items())),
        "missing_result_files": missing,
        "documents_with_transient_llm_error": transient,
        "complete": transient == 0 and missing == 0,
        "seed": SEED,
        "resamples": RESAMPLES,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", maxsplit=1)[0])
    parser.add_argument("--subset", type=Path, default=DEFAULT_SUBSET, help="plik JSON z `cases`")
    parser.add_argument("--no-negatives", action="store_true", help="bez negatywów organizatora")
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK, help="katalog roboczy")
    parser.add_argument("--out", type=Path, default=None, help="plik JSON z podsumowaniem")
    parser.add_argument(
        "--key-file",
        default=os.environ.get("MINIMAX_KEY_FILE", DEFAULT_KEY_FILE),
        help="plik z kluczem LLM poza Git (domyślnie MINIMAX_KEY_FILE)",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--protocol", default="anthropic", choices=("anthropic", "openai"))
    parser.add_argument("--max-calls", type=int, default=150, help="limit wywołań LLM na przebieg")
    parser.add_argument(
        "--skip-run", action="store_true", help="tylko ocena istniejącego katalogu wyjścia"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cases = json.loads(args.subset.read_text(encoding="utf-8"))["cases"]
    references = select_references(cases, negatives=not args.no_negatives)
    input_dir, output_dir = args.work / "input", args.work / "output"
    summary: dict[str, object] = {
        "subset": str(
            args.subset.relative_to(ROOT) if args.subset.is_relative_to(ROOT) else args.subset
        ),
        "cases": len(cases),
        "negatives": not args.no_negatives,
        "model": args.model,
        "base_url": args.base_url,
        "max_calls": args.max_calls,
    }
    if not args.skip_run:
        prepare_input(references, input_dir)
        exit_code, wall_s = run_process(input_dir, output_dir, args)
        summary |= {"process_exit_code": exit_code, "process_wall_s": round(wall_s, 1)}
        if exit_code == 2:
            print("błąd: self-check LLM nie przeszedł; wsad nie został przetworzony")
            return EXIT_FAIL
    summary |= evaluate(references, output_dir)
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    print(text)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    if not summary["complete"]:
        print("UWAGA: wynik niepełny (błąd przejściowy LLM albo brak pliku); nie cytuj jako F1")
        return EXIT_INCOMPLETE
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
