"""Generuje specyfikacje przebiegów grupy C (`specs/*.json`). Uruchomienie: .venv-exp/bin/python llm-e2e/lib/make_specs.py"""
import json
from pathlib import Path

SPECS = Path(__file__).resolve().parent.parent / "specs"
LLM = {"retries": 4, "timeout_s": 150}


def spec(name, exp, docs, mode=None, prompt="p2", reps=1, conc=4, server=None, env=None):
    s = {"name": name, "experiment": exp, "docs": docs, "reps": reps, "concurrency": conc,
         "server": {"router": "llm1", "extractor": "llm1", "ocr": "none", "llm": dict(LLM)} | (server or {}),
         "env": ({"LLME2E_MODE": mode, "LLME2E_PROMPT": prompt} if mode else {}) | (env or {})}
    SPECS.mkdir(exist_ok=True)
    (SPECS / f"{name}.json").write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


SUB = {"set": "dev_sub", "negatives": True}
SCR = {"set": "dev_screen", "negatives": False}
spec("e10-text-p2", "E10", SUB, "text", reps=5)
spec("e10-textimg-p2", "E10", SUB, "text_image", reps=3)
spec("e10-image-p2", "E10", SUB, "image", reps=3)
spec("e10-text-p1", "E10", SCR, "text", "p1", reps=3)
spec("e10-text-p3", "E10", SCR, "text", "p3", reps=3)
spec("e10-effort-low", "E10", SCR, "text", reps=3, server={"llm": LLM | {"effort": "low"}})
spec("e10-effort-high", "E10", SCR, "text", reps=3, server={"llm": LLM | {"effort": "high"}})
spec("e10-long-2pages", "E10", {"set": "dev_long", "classes": ["odwolanie"]}, "text", reps=3, env={"LLME2E_TEXT_PAGES": "2"})

# E11: wejścia nietekstowe (zestaw skanów grupy A, tylko sprawy rozwojowe z podzbioru)
ZS = lambda v, extra=None: {"set": f"zestaw:{v}", "cases": "dev_sub"} | (extra or {})
ALL = "skan,mieszany,s2,s5"
OCR = {"ocr": "rapidocr", "ocr_dpi": 200, "ocr_policy": "if_needed"}
spec("e11-scan-A", "E11", ZS(ALL), "text")
spec("e11-scan-B", "E11", ZS(ALL), "text", server=OCR)
spec("e11-scan-Balways", "E11", ZS("mieszany,s2,s5"), "text", server=OCR | {"ocr_policy": "always"})
spec("e11-scan-C", "E11", ZS(ALL), "image")
spec("e11-scan-D", "E11", ZS(ALL), "text_image", server=OCR)
# dolna granica: sam regex (bez LLM)
RULES = {"router": "rules", "extractor": "rules"}
spec("e11-rules-text", "E11", SUB, server=RULES, conc=2)
spec("e11-rules-scan", "E11", ZS(ALL), server=RULES | OCR, conc=2)
for n in ("e11-rules-text", "e11-rules-scan"):
    p = SPECS / f"{n}.json"
    d = json.loads(p.read_text())
    d["env"] = {}
    p.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

# E18: modele MiniMax dostępne na jednym kluczu (tekst, prompt p2, bez negatywów, 2 powtórzenia)
POS = {"set": "dev_sub", "negatives": False}
for tag, model in (("M3", "MiniMax-M3"), ("M2.7", "MiniMax-M2.7"), ("M2.5", "MiniMax-M2.5")):
    spec(f"e18-{tag}", "E18", POS, "text", reps=2, server={"llm": LLM | {"model": model}})

# Ablacje na odtworzonych odpowiedziach LLM (replay powtórzenia 1; zero wywołań sieci)
RP = str(SPECS.parent / "E10" / "raw" / "e10-text-p2.jsonl")
for merge in ("regex_override", "regex_fill"):
    spec(f"e11-abl-{merge}", "E11", SUB, "text", conc=2, env={"LLME2E_REPLAY": RP, "LLME2E_REPLAY_REP": "1", "LLME2E_MERGE": merge})
spec("e11-abl-replay-none", "E11", SUB, "text", conc=2, env={"LLME2E_REPLAY": RP, "LLME2E_REPLAY_REP": "1"})

# Kandydat do wyboru końcowego: D (tekst + obraz, OCR if_needed) na modelu wybranym w E18 (M3); jeden powtórzenie, ta sama dev_sub
M3 = {"llm": LLM | {"model": "MiniMax-M3"}}
spec("e11-DM3-text", "E11", SUB, "text_image", server=OCR | M3)
spec("e11-DM3-scan", "E11", ZS(ALL), "text_image", conc=2, server=OCR | M3)
