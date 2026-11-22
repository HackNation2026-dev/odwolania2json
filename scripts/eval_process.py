"""Pomiar produktu: `process` na sprawach rozwojowych i ocena ewaluatorem zespołu.

Skrypt kopiuje PDF-y wybranych spraw do katalogu roboczego, uruchamia
`python -m odwolania2json process` z prawdziwym LLM i liczy F1 przybliżony
z przedziałem z bootstrapu po sprawach. Wynik NIE jest oficjalnym F1.

Zasady:
- tylko sprawy rozwojowe z `data/podzial.json`; sprawa kontrolna przerywa skrypt;
- klucze czyta produkt z plików (`LLM_API_KEY_FILE`, `LLM_FALLBACK_KEY_FILE`); skrypt
  nie otwiera plików z kluczami, nie wypisuje ich i nie zapisuje w wynikach;
- budżet wywołań LLM (`--call-budget`) obowiązuje łącznie dla wszystkich uruchomień
  w tym samym katalogu roboczym (stan w `state.json`);
- przebieg można dzielić: `--max-docs 10` robi próbę, kolejne uruchomienie bierze
  tylko dokumenty bez wyniku albo z błędem LLM (nic nie jest powtarzane);
- ponowienia sieciowe są domyślnie wyłączone, a dostawca po błędzie nie jest pytany
  ponownie w tym uruchomieniu: przy HTTP 429 lub 403 pomiar staje i jest niepełny.

Przykłady:
    python scripts/eval_process.py --max-docs 10            # próba
    python scripts/eval_process.py                          # reszta dokumentów
    python scripts/eval_process.py --skip-run               # tylko ocena
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
from odwolania2json.evaluator import (  # noqa: E402
    ClassTotals,
    DocumentMetrics,
    FieldOutcome,
    compare_document,
)
from odwolania2json.loader import (  # noqa: E402
    MATERIALS_DIR,
    CaseReference,
    load_case_references,
    load_reference_json,
    result_name_for,
)

DEFAULT_WORK = ROOT / ".ci" / "eval-process"
DEFAULT_BASE_URL = "https://api.minimax.io/anthropic/v1/messages"
DEFAULT_MODEL = "MiniMax-M3.1-Flash-Preview"
DEFAULT_KEY_FILE = "~/kluczMiniMaxKacper"
NEGATIVE_CASE = "negatywne"
SEED = 20261122
RESAMPLES = 2000
EXIT_OK, EXIT_FAIL, EXIT_INCOMPLETE = 0, 1, 3
_USAGE = re.compile(r"LLM: wywołania=(\d+) tokeny_wejścia=(\d+) tokeny_wyjścia=(\d+)")
_INDEX = re.compile(r"\[\d+\]")


def select_references(cases: list[str], negatives: bool) -> list[CaseReference]:
    """Dokumenty wybranych spraw; sprawa spoza zbioru rozwojowego to błąd."""
    split = load_split()
    forbidden = sorted(set(cases) - split.rozwojowy)
    if forbidden:
        raise SystemExit(f"błąd: sprawy spoza zbioru rozwojowego: {', '.join(forbidden)}")
    wanted = set(cases) | ({NEGATIVE_CASE} if negatives else set())
    return [ref for ref in load_case_references() if ref.case_id in wanted]


def key_of(ref: CaseReference) -> str:
    return f"{ref.case_id}/{ref.input_name}"


def needs_run(record: dict[str, object] | None) -> bool:
    """Dokument bez wpisu albo z błędem LLM czeka na (ponowne) przetworzenie."""
    if record is None:
        return True
    errors = record.get("errors")
    codes = [str(error["code"]) for error in errors] if isinstance(errors, list) else []
    return record.get("status") == "technical_error" and any(c.startswith("llm_") for c in codes)


def prepare_input(references: list[CaseReference], input_dir: Path) -> None:
    """Kopiuje PDF-y do świeżego katalogu wejścia w układzie `sprawa/plik.pdf`."""
    if input_dir.exists():
        shutil.rmtree(input_dir)
    for ref in references:
        target = input_dir / ref.case_id / ref.input_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(MATERIALS_DIR / "dane" / ref.case_id / ref.input_name, target)


def process_env(args: argparse.Namespace, max_calls: int) -> dict[str, str]:
    """Środowisko produktu: klucze tylko jako ścieżki plików, nigdy jako wartości."""
    key_file = Path(args.key_file).expanduser()
    if not key_file.is_file():
        raise SystemExit(f"błąd: brak pliku z kluczem: {key_file}")
    env = {
        **{name: value for name, value in os.environ.items() if not name.startswith("LLM_")},
        "PYTHONPATH": os.pathsep.join(
            [str(ROOT / "apps" / "backend"), str(ROOT / "packages" / "contracts")]
        ),
        "PYTHONUTF8": "1",
        "LLM_API_KEY_FILE": str(key_file),
        "LLM_BASE_URL": args.base_url,
        "LLM_MODEL": args.model,
        "LLM_PROTOCOL": args.protocol,
        "LLM_MAX_CALLS": str(max_calls),
        "LLM_MAX_RETRIES": str(args.max_retries),
        "LLM_PROVIDER_COOLDOWN_S": str(args.cooldown),
    }
    if args.fallback_base_url:
        fallback_key = Path(args.fallback_key_file).expanduser()
        if not fallback_key.is_file():
            raise SystemExit(f"błąd: brak pliku z kluczem dostawcy zapasowego: {fallback_key}")
        env |= {
            "LLM_ALLOWED_HOSTS": args.allowed_hosts,
            "LLM_FALLBACK_BASE_URL": args.fallback_base_url,
            "LLM_FALLBACK_MODEL": args.fallback_model,
            "LLM_FALLBACK_PROTOCOL": args.fallback_protocol,
            "LLM_FALLBACK_KEY_FILE": str(fallback_key),
        }
        if args.fallback_headers:
            env["LLM_FALLBACK_HEADERS"] = args.fallback_headers
    return env


def run_process(
    input_dir: Path, output_dir: Path, env: dict[str, str]
) -> tuple[int, float, tuple[int, int, int] | None]:
    """Uruchamia produkt; zwraca kod wyjścia, czas i zużycie (wywołania, tokeny wej./wyj.)."""
    started = time.monotonic()
    result = subprocess.run(
        [sys.executable, "-m", "odwolania2json", "process", str(input_dir), str(output_dir)],
        cwd=ROOT,
        env=env,
        check=False,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    match = _USAGE.search(result.stdout or "")
    usage = (int(match[1]), int(match[2]), int(match[3])) if match else None
    return result.returncode, time.monotonic() - started, usage


def read_jsonl(path: Path) -> dict[str, dict[str, object]]:
    if not path.is_file():
        return {}
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return {str(record["input"]): record for record in records}


def write_jsonl(path: Path, records: dict[str, dict[str, object]]) -> None:
    lines = [json.dumps(records[key], ensure_ascii=False) for key in sorted(records)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _totals(outcomes: list[FieldOutcome]) -> ClassTotals:
    counts = Counter(outcome.verdict for outcome in outcomes)
    return ClassTotals(tp=counts["tp"], tn=counts["tn"], fp=counts["fp"], fn=counts["fn"])


def _f1_block(metrics: list[DocumentMetrics]) -> dict[str, object]:
    totals = _totals([outcome for item in metrics for outcome in item.outcomes])
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


def _per_field(metrics: list[DocumentMetrics]) -> dict[str, dict[str, object]]:
    """F1 każdego pola (indeksy list zwinięte do `[]`) z bootstrapem po sprawach."""
    names = sorted({_INDEX.sub("[]", o.path) for item in metrics for o in item.outcomes})
    result: dict[str, dict[str, object]] = {}
    for name in names:
        narrowed = [
            item.model_copy(
                update={"outcomes": [o for o in item.outcomes if _INDEX.sub("[]", o.path) == name]}
            )
            for item in metrics
        ]
        block = _f1_block([item for item in narrowed if item.outcomes])
        result[name] = {key: block[key] for key in ("tp", "fp", "fn", "f1", "ci95")}
    return result


def evaluate(
    references: list[CaseReference], output_dir: Path, report: dict[str, dict[str, object]]
) -> dict[str, object]:
    """Porównuje pliki wyniku z referencjami; dokument bez wpisu w raporcie jest pomijany."""
    metrics: list[DocumentMetrics] = []
    statuses: Counter[str] = Counter()
    codes: Counter[str] = Counter()
    providers: Counter[str] = Counter()
    switches: Counter[str] = Counter()
    empty_for_class = missing_files = unprocessed = 0
    for ref in references:
        record = report.get(key_of(ref))
        if record is None:
            unprocessed += 1
            continue
        result_path = output_dir / ref.case_id / result_name_for(ref.input_name)
        predicted: dict[str, object] = {}
        if result_path.is_file():
            predicted = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            missing_files += 1
        if not predicted and ref.document_class != "obcy":
            empty_for_class += 1
        statuses[str(record.get("status"))] += 1
        errors = record.get("errors")
        for error in errors if isinstance(errors, list) else []:
            codes[str(error["code"])] += 1
        llm = record.get("llm")
        if isinstance(llm, dict):
            providers[f"{llm.get('provider')}:{llm.get('model')}"] += 1
            if llm.get("switch_reason"):
                switches[str(llm["switch_reason"])] += 1
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
    pending = sum(1 for ref in references if needs_run(report.get(key_of(ref))))
    return {
        "documents_planned": len(references),
        "documents_evaluated": len(metrics),
        "documents_not_processed": unprocessed,
        "documents_waiting_for_llm": pending - unprocessed,
        "documents_of_known_class_with_empty_result": empty_for_class,
        "missing_result_files": missing_files,
        "all": _f1_block(metrics),
        "per_class": per_class,
        "per_field": _per_field(metrics),
        "classification_accuracy": round(
            sum(item.classification == "tp" for item in metrics) / max(1, len(metrics)), 4
        ),
        "statuses": dict(sorted(statuses.items())),
        "error_codes": dict(sorted(codes.items())),
        "llm_answered_by": dict(sorted(providers.items())),
        "llm_switch_reasons": dict(sorted(switches.items())),
        "complete": pending == 0 and missing_files == 0,
        "seed": SEED,
        "resamples": RESAMPLES,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", maxsplit=1)[0])
    parser.add_argument(
        "--subset",
        type=Path,
        default=None,
        help="plik JSON z `cases`; domyślnie wszystkie sprawy rozwojowe z data/podzial.json",
    )
    parser.add_argument("--negatives", action="store_true", help="dołącz negatywy organizatora")
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK, help="katalog roboczy")
    parser.add_argument("--out", type=Path, default=None, help="plik JSON z podsumowaniem")
    parser.add_argument("--max-docs", type=int, default=None, help="najwyżej tyle dokumentów teraz")
    parser.add_argument(
        "--call-budget", type=int, default=200, help="limit wywołań LLM łącznie w katalogu roboczym"
    )
    parser.add_argument(
        "--key-file",
        default=os.environ.get("MINIMAX_KEY_FILE", DEFAULT_KEY_FILE),
        help="plik z kluczem dostawcy głównego poza Git (domyślnie MINIMAX_KEY_FILE)",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--protocol", default="anthropic", choices=("anthropic", "openai"))
    parser.add_argument("--fallback-base-url", default=None, help="adres dostawcy zapasowego")
    parser.add_argument("--fallback-model", default=None)
    parser.add_argument("--fallback-protocol", default="openai", choices=("anthropic", "openai"))
    parser.add_argument("--fallback-key-file", default=None, help="plik z kluczem zapasowego")
    parser.add_argument("--fallback-headers", default=None, help="obiekt JSON nagłówków zapasowego")
    parser.add_argument("--allowed-hosts", default="api.minimax.io", help="LLM_ALLOWED_HOSTS")
    parser.add_argument("--max-retries", type=int, default=0, help="ponowienia sieciowe klienta")
    parser.add_argument(
        "--cooldown", type=float, default=86400.0, help="przerwa dostawcy po błędzie (s)"
    )
    parser.add_argument(
        "--skip-run", action="store_true", help="tylko ocena dotychczasowych wyników"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.subset is not None:
        cases = list(json.loads(args.subset.read_text(encoding="utf-8"))["cases"])
    else:
        cases = sorted(load_split().rozwojowy)
    references = select_references(cases, negatives=args.negatives)
    work: Path = args.work
    work.mkdir(parents=True, exist_ok=True)
    output_dir, merged_path, state_path = (
        work / "output",
        work / "report-all.jsonl",
        work / "state.json",
    )
    report = read_jsonl(merged_path)
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    state = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "runs": [], **state}

    if not args.skip_run:
        pending = [ref for ref in references if needs_run(report.get(key_of(ref)))]
        batch = pending[: args.max_docs] if args.max_docs else pending
        remaining = args.call_budget - int(state["calls"])
        if batch and remaining <= 0:
            print(f"błąd: budżet wywołań LLM wyczerpany ({state['calls']} z {args.call_budget})")
            return EXIT_FAIL
        if batch:
            input_dir = work / "input"
            prepare_input(batch, input_dir)
            exit_code, wall_s, usage = run_process(
                input_dir, output_dir, process_env(args, remaining)
            )
            # Bez linii zużycia (np. self-check zakończył pracę) liczymy ostrożnie 2 wywołania.
            calls, tokens_in, tokens_out = usage or (2, 0, 0)
            state["calls"] += calls
            state["input_tokens"] += tokens_in
            state["output_tokens"] += tokens_out
            state["runs"].append(
                {
                    "documents": len(batch),
                    "exit_code": exit_code,
                    "wall_s": round(wall_s, 1),
                    "calls": calls,
                    "input_tokens": tokens_in,
                    "output_tokens": tokens_out,
                }
            )
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
            if exit_code == 2:
                print("błąd: self-check LLM nie przeszedł; wsad nie został przetworzony")
                return EXIT_FAIL
            report |= read_jsonl(output_dir / "report.jsonl")
            write_jsonl(merged_path, report)

    summary: dict[str, object] = {
        "cases": len(cases),
        "negatives": args.negatives,
        "primary": {"model": args.model, "base_url": args.base_url},
        "fallback": (
            {"model": args.fallback_model, "base_url": args.fallback_base_url}
            if args.fallback_base_url
            else None
        ),
        "call_budget": args.call_budget,
        "llm_usage": state,
        **evaluate(references, output_dir, report),
    }
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    print(text)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    if not summary["complete"]:
        print("UWAGA: pomiar niepełny (dokumenty bez wyniku lub z błędem LLM); nie cytuj jako F1")
        return EXIT_INCOMPLETE
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
