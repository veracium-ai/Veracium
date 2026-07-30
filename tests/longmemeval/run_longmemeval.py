"""LongMemEval V1-S runner — ingest per turn, answer, emit the official
hypothesis file.

    # pilot (stratified, both control arms, Arm C trust mapping)
    PYTHONPATH=src python tests/longmemeval/run_longmemeval.py --pilot
    # one arm only, no cache (variance work)
    PYTHONPATH=src python tests/longmemeval/run_longmemeval.py --pilot --no-cache --arm T

Judging is NOT run here: we emit `hypotheses_<run>.jsonl` in the official
format and the operator runs the benchmark's own
`evaluate_qa.py gpt-4o <hyp> <data>` unmodified (spec §6).

Conventions verified against the official repo (2026-07-29):
  - the answer prompt carries the question date verbatim ("Current Date: ...")
  - sessions are date-sorted (adapter.load does this)
  - turns render as "<role>: <content>"
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adapter import ORACLE_FILE, S_FILE, load, stratified_pilot
from cache import CACHE_DIR, CacheLock, CachedComplete
from providers import QuotaExhausted

from veracium import Memory, MemoryConfig
from veracium.prompts import EXTRACT_PROMPT, EXTRACT_SCHEMA, EXTRACT_SYSTEM
from veracium.schema import EvidenceAuthor

OUT_DIR = Path.home() / "Datasets" / "longmemeval" / "runs"


def _sha16(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()[:16]

# Ingestion serialization (versioned: part of the cache identity) ------------
# Per-turn ingestion keeps authorship exact, but an isolated turn ("the second
# one") can be uninterpretable — so the event text carries a bounded window of
# prior turns marked as context-only. Only the CURRENT turn is evidence, and
# only its author is passed to remember().
CONTEXT_POLICY = {"version": 2, "window_turns": 4}
SERIALIZER_VERSION = 2

_CONTEXT_HEADER = ("[CONTEXT — earlier turns in this conversation, provided ONLY so the "
                   "current turn can be understood. Do NOT extract facts from these.]")
_CURRENT_HEADER = ("[CURRENT TURN — this is the only content to extract facts from. "
                   "Attribute every fact to this speaker.]")


def serialize(session, turn_index: int, *, window: int) -> str:
    """The event text for one turn: bounded prior context + the current turn."""
    cur = session.turns[turn_index]
    lines = []
    if window > 0 and turn_index > 0:
        prior = session.turns[max(0, turn_index - window):turn_index]
        lines.append(_CONTEXT_HEADER)
        lines += [f"{t.role}: {t.content.strip()}" for t in prior]
        lines.append("")
    lines.append(_CURRENT_HEADER)
    lines.append(f"{cur.role}: {cur.content.strip()}")
    return "\n".join(lines)


def isolated(session, turn_index: int, *, window: int = 0) -> str:
    """Ablation arm: no context at all (spec §3 ablation (a))."""
    cur = session.turns[turn_index]
    return f"{cur.role}: {cur.content.strip()}"


# Trust arms for assistant turns (spec §3a) ---------------------------------
#   T = trusted:  author=SYSTEM            -> mentionable/assertable
#   C = capped:   + derived_from=THIRD_PARTY -> use_only, never asserted
def author_for(role: str, arm: str):
    if role == "user":
        return EvidenceAuthor.USER, None, "chat"
    if arm == "T":
        return EvidenceAuthor.SYSTEM, None, "assistant_chat"
    return EvidenceAuthor.SYSTEM, EvidenceAuthor.THIRD_PARTY, "assistant_chat"


# Answer prompt (official convention) ---------------------------------------
ANSWER_TEMPLATE_VERSION = 1


def question_with_date(item) -> str:
    return f"Current Date: {item.question_date}\nQuestion: {item.question}"


def ingest_item(mem, item, *, arm: str, serializer, cache=None) -> dict:
    n_turns = n_facts = 0
    for session in item.sessions:
        for i, turn in enumerate(session.turns):
            text = serializer(session, i, window=CONTEXT_POLICY["window_turns"])
            author, derived, etype = author_for(turn.role, arm)
            if cache is not None:
                # key on the date string that actually reaches the provider
                kw = dict(author=author.value, event_type=etype, date=session.iso_day)
                cache.bind(cache.key_for(text, **kw), cache.parts_for(text, **kw))
            r = mem.remember(item.question_id, text, author=author,
                             derived_from=derived, event_type=etype,
                             date=session.iso_day,
                             evidence_ref=f"{session.ref}#{turn.index}")
            n_turns += 1
            n_facts += r.get("facts", 0) + r.get("quarantined", 0)
    return {"turns": n_turns, "facts": n_facts}


def run(items, *, provider, arm: str = "C", arms=("veracium",), cache_enabled=True,
        context: bool = True, budget=None, note: str = "", workers: int = 1,
        out_dir: Path = OUT_DIR, cache_path: Path | None = None,
        max_edges: int | None = None) -> dict:
    """Runs the requested control arms over `items`. Returns the run record;
    writes one hypothesis file per arm."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    serializer = serialize if context else isolated

    identity = {
        "extractor_model": getattr(provider, "model", type(provider).__name__),
        "decoding": getattr(provider, "decoding", "provider-default"),
        # hash the ACTUAL prompt + schema content, not a hand-kept label:
        # a forgotten version bump cannot then poison replay
        "extract_prompt_sha": _sha16(EXTRACT_SYSTEM + EXTRACT_PROMPT),
        "extract_schema_sha": _sha16(json.dumps(EXTRACT_SCHEMA, sort_keys=True)),
        "serializer_version": SERIALIZER_VERSION,
        "context_policy": CONTEXT_POLICY if context else {"version": 0, "window_turns": 0},
        "truncation": "none",
        "parser_version": 1,          # veracium._json.extract_json contract
        "schema": "triples-v1",
        # NOTE: the trust arm is deliberately NOT part of the extraction
        # identity — arms T and C differ only in write-time disclosure routing
        # (derived_from), which never reaches the extractor. Keying on it would
        # re-pay for byte-identical extractions. Recorded below instead.
    }
    cache = CachedComplete(provider, path=cache_path or (CACHE_DIR / "extractions.jsonl"),
                           identity=identity, enabled=cache_enabled)

    record = {"stamp": stamp, "note": note, "arm": arm, "context": context,
              "workers": workers, "max_subgraph_edges": max_edges or "default(40)",
              "throughput": getattr(provider, "throughput", {}),
              "identity": identity, "answer_template_version": ANSWER_TEMPLATE_VERSION,
              "items": len(items), "results": {}, "cache": None}

    def one_item(control, item) -> dict:
        """One item, one isolated store. Turn ORDER matters within an item
        (supersession/T1 depend on it) so a single worker owns an item start to
        finish; parallelism is across items, which are independent by
        construction (fresh user_id + fresh store)."""
        d = tempfile.mkdtemp(prefix="veracium-lme-")
        mem = Memory(llm=cache if control == "veracium" else provider,
                     config=MemoryConfig(db_path=f"{d}/lme.db",
                                         wiki_recompile_after_writes=0))
        try:
            ing = {"turns": 0, "facts": 0}
            context, n_edges, n_episodes, edge_sig = "", 0, 0, []
            if control == "veracium":
                ing = ingest_item(mem, item, arm=arm, serializer=serializer,
                                  cache=cache if cache_enabled else None)
                r = mem.recall(item.question_id, question_with_date(item),
                               token_budget=budget)
                hyp = mem.answer(item.question_id, question_with_date(item))
                ctx_tokens = r.tokens_estimated
            elif control == "no-memory":
                # identical answer path, empty memory: measures the gate floor
                hyp = mem.answer(item.question_id, question_with_date(item))
                ctx_tokens = 0
            else:  # bare-model: no veracium path at all — reveals priors
                hyp = provider(question_with_date(item), role="gate")
                ctx_tokens = 0
            return {"question_id": item.question_id, "hypothesis": hyp,
                    "control_arm": control, "context_tokens_estimated": ctx_tokens,
                    "ingested": ing, "recalled": {"edges": n_edges,
                                                  "episodes": n_episodes},
                    "edge_sig": edge_sig,
                    "context": context,
                    "cache_frozen": bool(cache_enabled and control == "veracium")}
        finally:
            mem.close()

    for control in arms:
        rows, t0 = [], time.monotonic()
        done = [0]
        progress = threading.Lock()

        def _run(item, control=control):
            try:
                row = one_item(control, item)
            except QuotaExhausted:
                raise                                   # terminal: abort the run
            except Exception as e:                      # keep the run alive
                row = {"question_id": item.question_id, "hypothesis": "",
                       "control_arm": control, "context_tokens_estimated": 0,
                       "ingested": {"turns": 0, "facts": 0}, "cache_frozen": False,
                       "error": f"{type(e).__name__}: {e}"[:400]}
                print(f"  [{control}] ERROR on {item.question_id}: {row['error']}",
                      file=sys.stderr)
            with progress:
                done[0] += 1
                n = done[0]
            if n % 5 == 0 or n == len(items):
                rate = (time.monotonic() - t0) / n
                eta = rate * (len(items) - n) / 60
                print(f"  [{control}] {n}/{len(items)} items "
                      f"({rate:.0f}s/item, ETA {eta:.0f} min; cache "
                      f"hits={cache.stats['hits']} misses={cache.stats['misses']})",
                      file=sys.stderr)
            return row

        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_run, it) for it in items]
                try:
                    for f in as_completed(futures):
                        rows.append(f.result())
                except QuotaExhausted as e:
                    for f in futures:
                        f.cancel()
                    print(f"\n[longmemeval] ABORTING: {e}\n"
                          f"  extractions already cached are preserved; re-run "
                          f"after billing is restored and they replay for free.",
                          file=sys.stderr)
                    raise
            rows.sort(key=lambda r: [i.question_id for i in items].index(r["question_id"]))
        else:
            rows = [_run(it) for it in items]

        hyp_path = out_dir / f"hypotheses_{stamp}_{control}_{arm}.jsonl"
        with hyp_path.open("w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        errors = [r for r in rows if r.get("error")]
        record["results"][control] = {"hypotheses": str(hyp_path), "n": len(rows),
                                      "errors": len(errors),
                                      "error_examples": [e["error"] for e in errors[:5]],
                                      "seconds": round(time.monotonic() - t0, 1)}
        print(f"  [{control}] -> {hyp_path}", file=sys.stderr)

    record["cache"] = {**cache.stats, "unique_keys": cache.unique_keys,
                       "enabled": cache_enabled}
    if hasattr(provider, "cost_usd"):
        record["cost"] = {"actual": provider.cost_usd(),
                          "retries": getattr(provider, "retries", 0),
                          "failures": getattr(provider, "failures", 0)}
    (out_dir / f"record_{stamp}.json").write_text(json.dumps(record, indent=2))
    return record


def _provider(kind: str):
    if kind == "openai":
        from providers import MeteredOpenAI
        return MeteredOpenAI()
    sys.path.insert(0, str(Path(__file__).parents[2] / "examples"))
    from claude_cli_provider import ClaudeCLIComplete
    return ClaudeCLIComplete()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", default=str(S_FILE))
    ap.add_argument("--pilot", action="store_true", help="stratified pilot subset")
    ap.add_argument("--limit", type=int, default=None, help="first N items (wiring smoke)")
    ap.add_argument("--arm", choices=["T", "C"], default="C",
                    help="assistant-turn trust arm (spec 3a)")
    ap.add_argument("--controls", default="veracium",
                    help="comma list: veracium,no-memory,bare-model")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--no-context", action="store_true",
                    help="ablation: isolated per-turn ingestion")
    ap.add_argument("--budget", type=int, default=None)
    ap.add_argument("--max-edges", type=int, default=None,
                    help="override max_subgraph_edges (retrieval-breadth ablation)")
    ap.add_argument("--note", default="")
    ap.add_argument("--provider", choices=["openai", "claude-cli"], default="openai",
                    help="openai = pinned API models with token metering")
    ap.add_argument("--workers", type=int, default=1,
                    help="items processed in parallel (order is preserved within an item)")
    ap.add_argument("--strict", action="store_true",
                    help="abort on any loader rejection (canonical runs)")
    args = ap.parse_args()

    items, evals, manifest = load(args.data, strict=args.strict)
    print(json.dumps(manifest, indent=2)[:1200], file=sys.stderr)
    if args.pilot:
        items = stratified_pilot(items, evals)
    if args.limit:
        items = items[:args.limit]
    print(f"[longmemeval] {len(items)} items, arm={args.arm}, "
          f"context={'on' if not args.no_context else 'OFF'}, "
          f"cache={'off' if args.no_cache else 'on'}", file=sys.stderr)

    with CacheLock(CACHE_DIR / "lock"):
        rec = run(items, provider=_provider(args.provider), arm=args.arm,
                  workers=args.workers,
                  arms=tuple(a.strip() for a in args.controls.split(",") if a.strip()),
                  cache_enabled=not args.no_cache, context=not args.no_context,
                  budget=args.budget, note=args.note, max_edges=args.max_edges)
    print(json.dumps({k: rec[k] for k in ("stamp", "arm", "items", "cache", "results")},
                     indent=2))
    print("\nNext: run the OFFICIAL judge, e.g.\n"
          f"  python3 evaluate_qa.py gpt-4o {rec['results'][list(rec['results'])[0]]['hypotheses']} "
          f"{args.data}")
