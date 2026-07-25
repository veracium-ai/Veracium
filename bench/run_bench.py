"""Internal benchmark suite — measure the contract, catch regressions.

Not a marketing artifact: this measures the functionality Veracium actually
promises (trust routing, supersession, abstention, duplication drift) plus the
engine's own overhead and cost profile, and records one comparable JSON line
per run so releases can be diffed against a baseline.

Tiers (run what you can afford; the record marks what ran):

  engine      free, deterministic-input: a scripted zero-latency fake LLM
              isolates VERACIUM'S code from model latency. Micro-benchmarks
              remember/recall/budgeted-recall/outcome ops; asserts budget
              adherence. Timing varies by machine — compare on one machine.
  eval        live (needs a provider): the acceptance eval (tests/eval) —
              correctness of the guarantees against the research-claim bar.
  robustness  live: the robustness tier on the seeded lmsys sample if present
              (else the committed fixtures) with --s4-samples 50 — this IS the
              value-equivalence T0 measurement (duplicate shapes classified).

Usage:
    PYTHONPATH=src python bench/run_bench.py                  # engine tier only
    PYTHONPATH=src python bench/run_bench.py --live           # + eval + robustness
    PYTHONPATH=src python bench/run_bench.py --compare        # diff last 2 records
Results append to bench/results.jsonl (committed; aggregates only, content-free).

Release checklist: run `--live`, then `--compare` — hard metrics must not
regress (thresholds below); soft regressions need a written justification in
the release notes.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "robustness"))
sys.path.insert(0, str(ROOT / "examples"))

RESULTS = Path(__file__).with_name("results.jsonl")

# -- regression thresholds (compare) ------------------------------------------
HARD = {  # any violation fails compare outright
    "eval.injection_asserts": ("==", 0),
    "robustness.internal_crashes": ("==", 0),
    "robustness.cross_user_leaks": ("==", 0),
    "robustness.injection_leaks": ("==", 0),
}
SOFT = {  # (max relative increase, or absolute drop) vs previous record
    "engine.remember_ms_p50": 1.5,      # >1.5x slower = flag
    "engine.recall_ms_p50": 1.5,
    "engine.recall_budgeted_ms_p50": 1.5,
    "engine.record_outcome_ms_p50": 1.5,
    "eval.correct_ratio": -0.05,        # >5pt drop = flag
    "robustness.dup_rate": 2.0,         # duplicates per reingest, >2x = flag
    "robustness.empty_rate": 1.5,
}


# -- engine tier ---------------------------------------------------------------

def _fake_llm():
    """Deterministic, zero-latency: cycles scripted extractions so remember()
    exercises new-fact, reinforcement, and supersession paths."""
    scripts = [
        {"triples": [{"subject": "user", "relation": "has_diet",
                      "object": "vegetarian", "volatility": "permanent"}],
         "episode": "User said they are vegetarian."},
        {"triples": [{"subject": "user", "relation": "works_as",
                      "object": "designer at Acme", "volatility": "durable"}],
         "episode": "User works at Acme."},
        {"triples": [{"subject": "user", "relation": "works_as",
                      "object": "engineer at Globex", "volatility": "durable"}],
         "episode": "User moved to Globex."},          # supersession
        {"triples": [{"subject": "user", "relation": "has_diet",
                      "object": "vegetarian", "volatility": "permanent"}],
         "episode": "User reaffirmed being vegetarian."},   # reinforcement
    ]
    state = {"i": 0}

    def llm(prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            out = scripts[state["i"] % len(scripts)]
            state["i"] += 1
            return json.dumps(out)
        return "## USER MODEL\n- benchmark wiki"
    return llm


def _median_ms(fn, n):
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    return round(statistics.median(times), 3)


def engine_tier(n_ops: int = 100) -> dict:
    from veracium import Memory, MemoryConfig
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=_fake_llm(),
                     config=MemoryConfig(db_path=f"{d}/bench.db",
                                         wiki_recompile_after_writes=0))
        counter = {"i": 0}

        def one_remember():
            counter["i"] += 1
            mem.remember(f"user{counter['i'] % 10}", f"benchmark turn {counter['i']}",
                         date="2026-01-01")
        remember_ms = _median_ms(one_remember, n_ops)

        recall_ms = _median_ms(lambda: mem.recall("user1", "acme designer diet"),
                               n_ops // 2)

        budgets_ok = {"n": 0, "over": 0}

        def one_budgeted():
            r = mem.recall("user1", "acme designer diet", token_budget=120)
            budgets_ok["n"] += 1
            if r.tokens_estimated > 120 * 1.25:   # documented approx tolerance
                budgets_ok["over"] += 1
        budgeted_ms = _median_ms(one_budgeted, n_ops // 2)

        edge = mem.store.edges("user1")[0]
        oc = {"i": 0}

        def one_outcome():
            oc["i"] += 1
            mem.record_outcome("user1", edge.id, outcome="unreviewed",
                               evidence_ref=f"run-{oc['i']}")
        outcome_ms = _median_ms(one_outcome, n_ops // 2)

        n_edges = sum(e["edges"] for e in mem.list_entities())
        mem.close()
        return {"remember_ms_p50": remember_ms, "recall_ms_p50": recall_ms,
                "recall_budgeted_ms_p50": budgeted_ms,
                "record_outcome_ms_p50": outcome_ms,
                "budget_overruns": budgets_ok["over"], "ops": n_ops,
                "edges_after": n_edges}


# -- live tiers ----------------------------------------------------------------

def eval_tier(provider) -> dict:
    sys.path.insert(0, str(ROOT))
    from tests.eval.run_eval import run
    r = run(provider)
    return {"correct": r["correct"], "total": r["total"],
            "correct_ratio": round(r["correct"] / r["total"], 4),
            "injection_asserts": r["injection_asserts"]}


def robustness_tier(mem_factory, s4_samples: int = 50) -> dict:
    from run_robustness import run
    from adapter import FIXTURES
    lmsys = Path.home() / "Datasets/lmsys-chat-1m/sample-20k.jsonl"
    corpus = lmsys if lmsys.exists() else FIXTURES
    card = run(mem_factory, corpus, n=200, seed=0, s4_samples=s4_samples)
    s4 = card["soft"]["reinforcement"]
    return {"corpus": Path(corpus).name, **card["hard"],
            "empty_rate": card["soft"]["yield"]["empty_rate_substantive"],
            "dup_rate": round(s4["duplicated"] / max(1, s4["reingested"]), 4),
            "dup_shapes": s4.get("shapes", {}),
            "superseded_churn": s4["superseded_churn"],
            "s4_samples": s4["reingested"]}


# -- ledger + compare ----------------------------------------------------------

def _flatten(rec: dict, prefix="") -> dict:
    out = {}
    for k, v in rec.items():
        if isinstance(v, dict):
            out.update(_flatten(v, f"{prefix}{k}."))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[f"{prefix}{k}"] = v
    return out


def compare(records: list[dict]) -> int:
    if len(records) < 2:
        print("compare: need at least 2 records")
        return 0
    prev, cur = _flatten(records[-2]["tiers"]), _flatten(records[-1]["tiers"])
    failures, flags = [], []
    for key, (op, want) in HARD.items():
        if key in cur and not (cur[key] == want):
            failures.append(f"HARD {key} = {cur[key]} (must be {want})")
    for key, limit in SOFT.items():
        if key not in cur or key not in prev:
            continue
        if limit < 0:   # absolute drop allowed
            if cur[key] < prev[key] + limit:
                flags.append(f"{key}: {prev[key]} -> {cur[key]} (drop > {-limit})")
        else:           # relative increase allowed
            if prev[key] > 0 and cur[key] / prev[key] > limit:
                flags.append(f"{key}: {prev[key]} -> {cur[key]} (> {limit}x)")
    for line in failures + flags:
        print(("FAIL " if line.startswith("HARD") else "flag ") + line)
    if not failures and not flags:
        print(f"compare: no regressions "
              f"({records[-2]['version']} -> {records[-1]['version']})")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="also run eval + robustness")
    ap.add_argument("--compare", action="store_true", help="diff last two records")
    ap.add_argument("--note", default="", help="free-text label for this record")
    args = ap.parse_args()

    records = [json.loads(l) for l in RESULTS.read_text().splitlines() if l.strip()] \
        if RESULTS.exists() else []
    if args.compare:
        return compare(records)

    from importlib.metadata import version as _v
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    rec = {"schema": 1, "version": _v("veracium"), "commit": commit,
           "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "note": args.note, "tiers": {"engine": engine_tier()}}

    if args.live:
        from claude_cli_provider import ClaudeCLIComplete
        from veracium import Memory, MemoryConfig
        rec["tiers"]["eval"] = eval_tier(ClaudeCLIComplete())

        def factory():
            d = tempfile.mkdtemp(prefix="veracium-bench-")
            return Memory(llm=ClaudeCLIComplete(),
                          config=MemoryConfig(db_path=f"{d}/robust.db",
                                              wiki_recompile_after_writes=0))
        rec["tiers"]["robustness"] = robustness_tier(factory)

    with RESULTS.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec, indent=2))
    print(f"\nrecorded -> {RESULTS.name} "
          f"({'engine+eval+robustness' if args.live else 'engine tier only'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
