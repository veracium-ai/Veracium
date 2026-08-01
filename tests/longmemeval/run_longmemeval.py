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
from freeze import FreezeError, config_conflicts, verify as verify_freeze
from manifest import (CompletionAttestation, EffectiveConfig, RunManifest,
                      check_manifest_self_consistency, decision_eligibility,
                      environment_state, explain_ineligibility, git_state,
                      sha256_file)
from providers import LEDGER, QuotaExhausted, UnclassifiedProviderError
from strictness import StrictExtraction

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
        max_edges: int | None = None, bar: str = "none",
        coverage: float | None = None, experiment: str = "unnamed",
        arm_name: str = "baseline", freeze_id: str | None = None,
        parent_run_id: str | None = None, data_path: Path | None = None,
        freeze_path: str | None = None) -> dict:
    """Runs the requested control arms over `items`. Returns the run record;
    writes one hypothesis file per arm, plus an immutable run manifest and, at
    termination, a completion attestation (benchmark policy G14-G17)."""
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
    raw_cache = CachedComplete(provider, path=cache_path or (CACHE_DIR / "extractions.jsonl"),
                               identity=identity, enabled=cache_enabled)
    # the extraction bar filters CACHED output, so strictness is testable as a
    # replay rather than a re-extraction; identity is unchanged on purpose —
    # the provider call is identical, only what we keep from it differs.
    # `raw_cache` stays bound separately: the wrapper has its own stats, and
    # reading hit/miss counters off whichever object happens to be outermost is
    # how this broke the first time.
    cache = (StrictExtraction(raw_cache, bar=bar, relations=MemoryConfig().relations)
             if bar != "none" else raw_cache)

    # ---- effective configuration (G15) ---------------------------------
    # One construction path, used by both the read-back and the run. A probe
    # that rebuilt the config itself would only prove the probe correct, which
    # is how the retrieval-breadth ablation recorded 200 while running at 40.
    def _build_config(db_path: str) -> MemoryConfig:
        cfg = MemoryConfig(db_path=db_path, wiki_recompile_after_writes=0)
        if coverage is not None:
            # 0.0 = pure relevance (the pre-coverage selector), so the
            # write-path change can be isolated from the selection change
            cfg.subgraph_coverage_share = coverage
        if max_edges:
            # how much of memory one query may see. At LongMemEval scale
            # (~1.7k facts/item) the default 40 is ~2% of the store.
            cfg.max_subgraph_edges = max_edges
        return cfg

    # `context` is rebound as a local inside one_item, so the flag has to be
    # captured here under a name that is not shadowed
    _ctx_flag = bool(context)
    _defaults = MemoryConfig()
    effective = EffectiveConfig(
        max_subgraph_edges=max_edges or _defaults.max_subgraph_edges,
        subgraph_coverage_share=(coverage if coverage is not None
                                 else _defaults.subgraph_coverage_share),
        trust_arm=arm, extraction_bar=bar, context_serialization=_ctx_flag,
        cache_enabled=bool(cache_enabled), workers=workers,
    )
    _probe = _build_config(f"{tempfile.mkdtemp(prefix='veracium-probe-')}/probe.db")
    effective.resolve(max_subgraph_edges=_probe.max_subgraph_edges,
                      subgraph_coverage_share=_probe.subgraph_coverage_share)
    effective.assert_consistent(stage="config construction")
    _observed_once = threading.Lock()
    _observed = [False]

    # ---- immutable run manifest, written before the first provider call ----
    manifest = RunManifest(
        experiment_name=experiment, arm_name=arm_name, trust_arm=arm,
        freeze_artifact_id=freeze_id, parent_run_id=parent_run_id,
        source=git_state(), environment=environment_state(),
        dataset={"path": str(data_path) if data_path else str(S_FILE),
                 "sha256": sha256_file(data_path or S_FILE)
                 if Path(data_path or S_FILE).exists() else None},
        adapter={"serializer_version": SERIALIZER_VERSION,
                 "answer_template_version": ANSWER_TEMPLATE_VERSION,
                 "context_policy": CONTEXT_POLICY if context else None,
                 "module_sha256": sha256_file(Path(__file__).parent / "adapter.py")},
        extraction_identity=identity,
        effective_config=effective.as_dict(),
        expected_item_ids=[i.question_id for i in items],
        expected_output_count=len(items),
        note=note,
    )
    # ---- freeze verification (proposals/freeze-artifact-spec.md) ---------
    # Runs BEFORE the manifest is written and before the first paid call. A bad
    # --freeze-id aborts (the operator believes something false); everything
    # else only downgrades the run to exploratory — the runner never refuses to
    # RUN, it refuses to call the result confirmatory.
    from datetime import datetime as _dt, timezone as _tz
    _started = _dt.now(_tz.utc)
    freeze = verify_freeze(freeze_path, freeze_id=freeze_id,
                           run_started_at=_started,
                           item_ids=[i.question_id for i in items])
    print(f"[longmemeval] freeze: {freeze.explain()}", file=sys.stderr)

    # Freeze (INTENDED) vs effective config (ACTUAL) — the cross-check that
    # makes "we ran what we said we would" checkable rather than assertable.
    # G15 gave the manifest requested/resolved/observed; the freeze declares
    # intent; until now the two records never met.
    #
    # This ABORTS rather than downgrading, unlike the other freeze failures,
    # and the distinction is deliberate: a run that both claims a protocol AND
    # contradicts it means the operator believes something false about what is
    # executing — the same condition as a wrong --freeze-id. It is detectable
    # here, before the first paid call, and the alternative is ~180 item-runs
    # of the wrong configuration.
    if freeze.confirmatory and freeze.arm_config:
        declared = (freeze.arm_config.get(arm_name)
                    or freeze.arm_config.get("treatment")
                    or {})
        conflicts = config_conflicts(
            declared,
            {k: v["requested"] for k, v in effective.as_dict().items()},
            arm=arm_name)
        if conflicts:
            raise FreezeError(
                "run contradicts its own freeze:\n  "
                + "\n  ".join(conflicts)
                + f"\n  Aborting before the first paid call. Either run the "
                  f"configuration the freeze declares, or run without "
                  f"--freeze (exploratory).")

    manifest.freeze_artifact_id = freeze.freeze_id if freeze.confirmatory else None

    manifest_hash = manifest.write(out_dir)
    validation = check_manifest_self_consistency(
        manifest, out_dir,
        referenced_files=[p for p in (data_path or S_FILE,) if Path(p).exists()])
    print(f"[longmemeval] manifest {manifest.run_id} ({manifest_hash[:12]}) "
          f"experiment={experiment} arm={arm_name} "
          f"freeze={freeze_id or 'NONE (exploratory)'}", file=sys.stderr)

    record = {"stamp": stamp, "note": note, "arm": arm, "context": context,
              "freeze": freeze.as_dict(),
              "workers": workers,
              # the three-value form; the old single "max_subgraph_edges" key
              # is gone on purpose because it asserted the REQUESTED value and
              # was wrong for hours
              "effective_config": effective.as_dict(),
              "extraction_bar": bar,
              "run_id": manifest.run_id, "experiment": experiment,
              "arm_name": arm_name, "manifest_hash": manifest_hash,
              "freeze_artifact_id": freeze_id,
              "throughput": getattr(provider, "throughput", {}),
              "identity": identity, "answer_template_version": ANSWER_TEMPLATE_VERSION,
              "items": len(items), "results": {}, "cache": None}

    def one_item(control, item) -> dict:
        """One item, one isolated store. Turn ORDER matters within an item
        (supersession/T1 depend on it) so a single worker owns an item start to
        finish; parallelism is across items, which are independent by
        construction (fresh user_id + fresh store)."""
        d = tempfile.mkdtemp(prefix="veracium-lme-")
        cfg = _build_config(f"{d}/lme.db")
        mem = Memory(llm=cache if control == "veracium" else provider, config=cfg)
        # Post-condition, from the FIRST item actually processed (G15). The
        # config being constructed correctly does not prove it propagated into
        # the object the run uses; only reading it off that object does.
        with _observed_once:
            first = not _observed[0]
            _observed[0] = True
        if first:
            effective.observe(
                max_subgraph_edges=mem.config.max_subgraph_edges,
                subgraph_coverage_share=mem.config.subgraph_coverage_share,
                trust_arm=arm, extraction_bar=bar,
                context_serialization=_ctx_flag,
                cache_enabled=bool(cache_enabled), workers=workers)
            effective.assert_consistent(stage="first processed item")
        try:
            ing = {"turns": 0, "facts": 0}
            context, n_edges, n_episodes, edge_sig = "", 0, 0, []
            recalled_refs = []
            if control == "veracium":
                ing = ingest_item(mem, item, arm=arm, serializer=serializer,
                                  cache=cache if cache_enabled else None)
                r = mem.recall(item.question_id, question_with_date(item),
                               token_budget=budget)
                hyp = mem.answer(item.question_id, question_with_date(item))
                ctx_tokens = r.tokens_estimated
                # the failure taxonomy needs the rendered context, and the
                # variance protocol needs a comparable extraction signature
                context = r.context
                n_edges, n_episodes = len(r.edges), len(r.episodes)
                # The frozen primary metric is answer-turn hit rate, computed
                # from recalled evidence_refs against turns marked has_answer.
                # Counts and a signature hash cannot produce it: without this
                # the run yields no computable primary measurement.
                # Safe for R2 — zero of the 30 items carry repeated session
                # ids, so Session.ref never diverges from the oracle's
                # session_id (verified before the run).
                recalled_refs = sorted(
                    {e.provenance.evidence_ref for e in r.edges
                     if e.provenance.evidence_ref}
                    | {ep.provenance.evidence_ref for ep in r.episodes
                       if ep.provenance.evidence_ref})
                edge_sig = sorted(
                    _sha16(f"{e.subject}|{e.relation}|{e.object}".lower())[:8]
                    for e in mem.store.edges(item.question_id, active_only=False,
                                             include_quarantined=True))
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
                    "edge_sig": edge_sig, "recalled_refs": recalled_refs,
                    "context": context,
                    "cache_frozen": bool(cache_enabled and control == "veracium")}
        finally:
            mem.close()

    per_item: dict = {}
    try:
      for control in arms:
        rows, t0 = [], time.monotonic()
        done = [0]
        progress = threading.Lock()

        def _run(item, control=control):
            try:
                row = one_item(control, item)
            except (QuotaExhausted, UnclassifiedProviderError):
                raise            # terminal: abort rather than fill in blanks
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
                      f"hits={raw_cache.stats['hits']} misses={raw_cache.stats['misses']})",
                      file=sys.stderr)
            return row

        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_run, it) for it in items]
                try:
                    for f in as_completed(futures):
                        rows.append(f.result())
                except (QuotaExhausted, UnclassifiedProviderError) as e:
                    for f in futures:
                        f.cancel()
                    print(f"\n[longmemeval] ABORTING: {e}\n"
                          f"  extractions already cached are preserved; re-run "
                          f"after the cause is resolved and they replay for free.",
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
        for r in rows:
            per_item[f"{control}:{r['question_id']}"] = (
                "failed" if r.get("error") else "succeeded")
        record["results"][control] = {"hypotheses": str(hyp_path), "n": len(rows),
                                      "errors": len(errors),
                                      "error_examples": [e["error"] for e in errors[:5]],
                                      "seconds": round(time.monotonic() - t0, 1)}
        print(f"  [{control}] -> {hyp_path}", file=sys.stderr)
    except Exception as e:
        # G16: a run that dies must be visibly incomplete. Without this, an
        # aborted run leaves hypothesis files and no record at all, which reads
        # as "nothing happened" rather than "this is partial".
        CompletionAttestation(
            run_id=manifest.run_id, manifest_hash=manifest_hash,
            execution_status="partial" if per_item else "failed",
            validity_status="invalidated",
            invalidation_reason=f"aborted: {type(e).__name__}: {e}"[:400],
            items_expected=len(items) * len(arms),
            items_succeeded=sum(v == "succeeded" for v in per_item.values()),
            items_failed=sum(v == "failed" for v in per_item.values()),
            per_item_status=per_item,
            retries=getattr(provider, "retries", 0),
            failures=getattr(provider, "failures", 0),
            validation={"error_classes": getattr(provider, "error_classes", {})},
        ).write(out_dir)
        print(f"[longmemeval] attestation written: run {manifest.run_id} "
              f"is NOT decision-eligible ({type(e).__name__})", file=sys.stderr)
        raise

    if isinstance(cache, StrictExtraction):
        record["strictness"] = dict(cache.stats)
    record["cache"] = {**raw_cache.stats, "unique_keys": raw_cache.unique_keys,
                       "enabled": cache_enabled}
    if hasattr(provider, "cost_usd"):
        record["cost"] = {"actual": provider.cost_usd(),
                          "retries": getattr(provider, "retries", 0),
                          "failures": getattr(provider, "failures", 0)}

    # ---- completion attestation (G16) -----------------------------------
    # Separate file, referencing the manifest by hash, so the immutable record
    # stays immutable. Output hashes are taken here rather than at read time:
    # a hypothesis file edited after the run should stop matching.
    n_failed = sum(v == "failed" for v in per_item.values())
    n_ok = sum(v == "succeeded" for v in per_item.values())
    expected = len(items) * len(arms)
    execution = ("completed" if n_ok == expected
                 else "partial" if n_ok else "failed")
    attestation = CompletionAttestation(
        run_id=manifest.run_id, manifest_hash=manifest_hash,
        execution_status=execution,
        # validity is a LATER analytical determination — the no-op ablation
        # executed perfectly and was invalidated hours afterwards. The runner
        # is not entitled to declare its own output valid.
        validity_status="unreviewed",
        items_expected=expected, items_succeeded=n_ok, items_failed=n_failed,
        per_item_status=per_item,
        effective_config=effective.as_dict(),
        output_hashes={r["hypotheses"]: sha256_file(r["hypotheses"])
                       for r in record["results"].values()
                       if Path(r["hypotheses"]).exists()},
        cost_ledger_hash=(sha256_file(LEDGER)[:16] if LEDGER.exists() else None),
        retries=getattr(provider, "retries", 0),
        failures=getattr(provider, "failures", 0),
        validation={**validation,
                    "error_classes": getattr(provider, "error_classes", {}),
                    "effective_config_disagreements": effective.disagreements()},
    )
    attestation.write(out_dir)
    # refresh: the copy taken at manifest time predates every `observed` value
    record["effective_config"] = effective.as_dict()
    record["attestation"] = f"attestation_{manifest.run_id}.json"
    eligible, detail = decision_eligibility(manifest, attestation, out_dir=out_dir)
    record["decision_eligible"] = eligible
    record["decision_detail"] = detail
    print(f"[longmemeval] {explain_ineligibility(detail)}", file=sys.stderr)

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
    ap.add_argument("--coverage", type=float, default=None,
                    help="subgraph_coverage_share override; 0.0 = pure relevance")
    ap.add_argument("--bar", choices=["none", "registry", "registry+len"],
                    default="none", help="extraction strictness bar (over-extraction test)")
    ap.add_argument("--max-edges", type=int, default=None,
                    help="override max_subgraph_edges (retrieval-breadth ablation)")
    ap.add_argument("--note", default="")
    ap.add_argument("--experiment", default="unnamed",
                    help="frozen experiment name (G11) — free-text notes are "
                         "what produced the E-number collision")
    ap.add_argument("--arm-name", default="baseline",
                    help="arm within the experiment: baseline | treatment | ...")
    ap.add_argument("--freeze-id", default=None,
                    help="sha256 of the frozen protocol artifact. Without one "
                         "the run is recorded as exploratory and is NOT "
                         "decision-eligible (G3/G19)")
    ap.add_argument("--freeze", dest="freeze_path", default=None,
                    help="path to the committed freeze artifact that --freeze-id "
                         "names. Verified locally: hash, required fields, "
                         "approved_at strictly before run start, item-set hash")
    ap.add_argument("--parent-run-id", default=None,
                    help="resume lineage: this run continues that one")
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
                  budget=args.budget, note=args.note, max_edges=args.max_edges,
                  bar=args.bar, coverage=args.coverage,
                  experiment=args.experiment, arm_name=args.arm_name,
                  freeze_id=args.freeze_id, freeze_path=args.freeze_path,
                  parent_run_id=args.parent_run_id,
                  data_path=Path(args.data))
    print(json.dumps({k: rec[k] for k in ("stamp", "run_id", "experiment", "arm",
                                          "items", "cache", "results",
                                          "decision_eligible")},
                     indent=2))
    print("\nNext: run the OFFICIAL judge, e.g.\n"
          f"  python3 evaluate_qa.py gpt-4o {rec['results'][list(rec['results'])[0]]['hypotheses']} "
          f"{args.data}")
