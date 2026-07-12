"""Robustness tier — stream real, messy conversations through the write path and
hold veracium's guarantees as invariants (no ground truth, no accuracy scoring;
see proposal: unlabeled corpora are fuzzing input, the guarantees are the oracle).

Run standalone against the committed fixture corpus (needs the `claude` CLI):

    PYTHONPATH=src python tests/robustness/run_robustness.py
    PYTHONPATH=src python tests/robustness/run_robustness.py --path lmsys.jsonl --n 200

or wire any provider via `run(mem_factory, path, ...)`. The pytest wrapper
(tests/test_robustness.py) is opt-in via VERACIUM_ROBUSTNESS=1.

Notes vs the proposal:
- answer()/maintain() run on a seeded sample of conversations (answer_frac) —
  they dominate cost, and per-conversation coverage buys nothing extra here.
- H1 crashes are attributed provider-vs-internal (see invariants.py); only
  internal ones gate. The harness records its own redacted tracebacks rather
  than attaching a diagnostics.Reporter — fuzz noise doesn't belong in the
  user's local diagnostics log.
"""

from __future__ import annotations

import inspect
import json
import random
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adapter import FIXTURES, iter_conversations
from invariants import Accumulators

from veracium import Memory, MemoryConfig


def _edge_ids(store, uid) -> set:
    return {e.id for e in store.edges(uid, active_only=False, include_quarantined=True)}


def _provider_files(llm) -> tuple:
    try:
        return (inspect.getsourcefile(type(llm)),)
    except TypeError:
        return ()


def run(mem_factory, path=FIXTURES, *, n: int = 200, seed: int = 0,
        inject_frac: float = 0.15, truncate_chars: int = 16000,
        answer_frac: float = 0.15, verbose: bool = False) -> dict:
    """mem_factory() -> a fresh Memory on an isolated temp store, with a cheap
    llm. Returns the scorecard dict (invariants.Accumulators.scorecard)."""
    mem = mem_factory()
    acc = Accumulators(provider_files=_provider_files(mem.llm))
    convos, manifest = iter_conversations(path, n=n, seed=seed,
                                          inject_frac=inject_frac,
                                          truncate_chars=truncate_chars)
    manifest["answer_frac"] = answer_frac
    manifest["provider"] = type(mem.llm).__name__
    rng = random.Random(seed + 1)  # decoupled from the adapter's sampling stream

    for ci, (uid, turns) in enumerate(convos):
        for turn in turns:
            before = _edge_ids(mem.store, uid)
            t0 = time.monotonic()
            try:
                r = mem.remember(uid, turn["text"], author=turn["author"],
                                 event_type=turn["event_type"])
            except Exception as e:                                      # H1
                acc.crash("remember", e, turn["text"])
                continue
            acc.latency["remember"].append((time.monotonic() - t0) * 1000)  # S3
            acc.yield_stat(turn, r)                                     # S1
            new = [e for e in mem.store.edges(uid, active_only=False,
                                              include_quarantined=True)
                   if e.id not in before]
            acc.check_edges(new, turn)                                  # H3/H4/S2

        if rng.random() < answer_frac:
            for op, fn in (("answer", lambda: mem.answer(uid, "what do you know about me?")),
                           ("maintain", lambda: mem.maintain(uid))):
                t0 = time.monotonic()
                try:
                    fn()                                                # H1
                    acc.latency[op].append((time.monotonic() - t0) * 1000)
                except Exception as e:
                    acc.crash(op, e, uid)
        if verbose and (ci + 1) % 10 == 0:
            print(f"  …{ci + 1}/{len(convos)} conversations", file=sys.stderr)

    acc.check_isolation(mem.store, [uid for uid, _ in convos[:20]])     # H2
    mem.close()
    return acc.scorecard(manifest)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--path", default=FIXTURES, help="corpus jsonl (default: committed fixtures)")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--inject-frac", type=float, default=0.15)
    ap.add_argument("--truncate-chars", type=int, default=16000)
    ap.add_argument("--answer-frac", type=float, default=0.15)
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).parents[2] / "examples"))
    from claude_cli_provider import ClaudeCLIComplete

    def factory():
        d = tempfile.mkdtemp(prefix="veracium-robust-")
        return Memory(llm=ClaudeCLIComplete(),
                      config=MemoryConfig(db_path=f"{d}/robust.db",
                                          wiki_recompile_after_writes=0))

    card = run(factory, args.path, n=args.n, seed=args.seed,
               inject_frac=args.inject_frac, truncate_chars=args.truncate_chars,
               answer_frac=args.answer_frac, verbose=True)
    print(json.dumps(card, indent=2, default=str))
    print("\nPASSED" if card["passed"] else "\nFAILED", "—", card["hard"])
    raise SystemExit(0 if card["passed"] else 1)
