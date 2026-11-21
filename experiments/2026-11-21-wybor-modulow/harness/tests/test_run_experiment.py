"""Testy CLI eksperymentów: blokada flock, ochrona zbioru kontrolnego, zapis JSON i README, bez sekretów."""

import fcntl
import json
import threading
import time

import pytest

import run_experiment as rx

SPEC = {"experiment": "E99", "variant": "test", "description": "opis testowy", "dataset": "cases-dev", "limit": 2, "seed": 5,
        "server": {"ocr": "none", "router": "rules", "extractor": "rules"}}


def test_cpu_lock_serializes_and_reports_wait(tmp_path):
    lock = str(tmp_path / "lock")
    order = []

    def holder():
        with rx.cpu_lock(True, lock):
            order.append("a-in")
            time.sleep(0.4)
            order.append("a-out")

    t = threading.Thread(target=holder)
    t.start()
    time.sleep(0.1)
    with rx.cpu_lock(True, lock) as waited:
        order.append("b-in")
    t.join()
    assert order == ["a-in", "a-out", "b-in"] and waited >= 0.2


def test_cpu_lock_disabled_does_not_touch_file(tmp_path):
    with rx.cpu_lock(False, str(tmp_path / "nie-ma")) as waited:
        assert waited == 0.0
    assert not (tmp_path / "nie-ma").exists()


def test_cpu_lock_is_compatible_with_flock_cli(tmp_path):
    lock = tmp_path / "l"
    with rx.cpu_lock(True, str(lock)):
        with open(lock, "a+") as f:
            with pytest.raises(BlockingIOError):
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)


def test_control_set_requires_explicit_confirmation(tmp_path):
    with pytest.raises(SystemExit, match="kontrolny"):
        rx.select_documents({"dataset": "control"}, tmp_path)
    with pytest.raises(SystemExit):
        rx.select_documents({"dataset": "all"}, tmp_path)


def test_select_is_seeded_and_limited(tmp_path):
    a = rx.select_documents({"dataset": "cases-dev", "limit": 3, "seed": 1}, tmp_path)
    b = rx.select_documents({"dataset": "cases-dev", "limit": 3, "seed": 1}, tmp_path)
    c = rx.select_documents({"dataset": "cases-dev", "limit": 3, "seed": 2}, tmp_path)
    assert [d["item"].key for d in a] == [d["item"].key for d in b] and len(a) == 3
    assert [d["item"].key for d in a] != [d["item"].key for d in c]


def test_unknown_runner_and_bad_experiment_id(tmp_path):
    with pytest.raises(SystemExit):
        rx.resolve_runner("nie_ma")
    with pytest.raises(SystemExit):
        rx.run_spec({"experiment": "X1", "variant": "v"}, out_root=tmp_path)


@pytest.mark.slow
def test_run_spec_writes_json_and_readme(tmp_path):
    out = rx.run_spec(SPEC, out_root=tmp_path, no_lock=True)
    d = json.loads(out.read_text(encoding="utf-8"))
    assert d["experiment"] == "E99" and d["seed"] == 5 and d["aggregates"]["documents"] == 2
    assert d["limit_method"] in ("systemd-run", "prlimit", "none") and d["peak_rss_mb"] > 20
    assert d["versions"]["pypdfium2"] and d["harness_config"]["ocr"] == "none" and d["system"]["ocr"]["ready"] is False
    assert all("wall_s" in r["timing"] for r in d["documents"]) and d["aggregates"]["leaf_f1"]["total"]["f1"] >= 0
    assert "key_file" not in out.read_text(encoding="utf-8")
    readme = (tmp_path / "E99" / "README.md").read_text(encoding="utf-8")
    assert "opis testowy" in readme and "test.json" in readme and "flock /tmp/uzp-cpu.lock" in readme


def test_custom_runner_via_registry(tmp_path):
    rx.register_runner("noop", lambda spec, ctx: {"documents": [], "aggregates": {"documents": 0}})
    out = rx.run_spec({"experiment": "E98", "variant": "noop", "runner": "noop", "timing": False}, out_root=tmp_path)
    assert json.loads(out.read_text())["aggregates"] == {"documents": 0}
    assert (tmp_path / "E98" / "README.md").is_file()


def test_leaf_counts_order_insensitive_and_null_aware():
    ref = {"a": 1, "l": [{"n": "x"}, {"n": "y"}], "z": None}
    assert rx.leaf_counts({"a": 1, "l": [{"n": "y"}, {"n": "x"}], "z": None}, ref) == {"tp": 3, "fp": 0, "fn": 0}
    assert rx.leaf_counts({"a": 2, "l": [{"n": "x"}], "z": "zmyślone"}, ref) == {"tp": 1, "fp": 2, "fn": 2}
    assert rx.leaf_f1({"tp": 1, "fp": 2, "fn": 2}) == 0.3333 and rx.leaf_f1({"tp": 0, "fp": 0, "fn": 0}) == 0.0
    assert rx.leaf_counts({}, {}) == {"tp": 0, "fp": 0, "fn": 0}
