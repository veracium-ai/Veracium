"""Memory lifecycle: expiry and consolidation — the "overnight" maintenance job.

Two mechanisms, both grounded in findings:
- **Expiry (findings on volatility).** A fact past its expected lifetime is
  handled by its volatility's behavior: transient/ephemeral facts LAPSE (silently
  invalidated — "still sick?" three months later is irrelevant, not unknown);
  durable/slow facts are flagged CONFIRM (surfaced as possibly-stale, never
  silently dropped); DECAY lowers confidence until a floor. Reinforcement (a
  re-stated fact) PERSISTS the restatement as its own edge and transfers NOTHING
  onto the prior — not `observed_at`, not `confidence`, not `valid_from`
  (accepted `specs/0012` Design 1, landed 2026-08-10): the fact stays live
  through the new edge, and each edge ages against its OWN `observed_at`
  (per-edge ageing is a frozen `0012` invariant — grouping expiry to the newest
  same-value edge would reintroduce the bypass `0012` closes). Only `confirm()`
  clears `needs_confirmation` (`specs/0008` — an author-class restatement must
  not answer a question addressed to the user).
- **Consolidation (finding 11 / compaction-loss guard).** Cold episodes are
  compacted into compact summaries to bound read cost as history grows (finding
  22), but first occurrences of failures, their fixes, illnesses, and dated
  commitments are preserved verbatim — the subtle-pattern loss the research warned
  compaction causes.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from ._json import extract_json
from .llm.base import Complete
from .schema import (DEFAULT_EXPIRY, Disclosure, Episode, EvidenceAuthor, ExpiryBehavior,

                     utcnow)


def expire(store, user_id: str, config, *, now: Optional[datetime] = None) -> dict:
    """Apply volatility-driven expiry to `user_id`'s active edges. Idempotent.

    specs/0048 §4B: the policy (`decay_factor`, `confidence_floor`, `volatility_lifetime_days`) is read from `config`
    ONCE, at entry, before any edge is read, and the two bounds are validated there by the one validator
    (`config.validate_decay_bound`), and the behaviour table is read from this module's `DEFAULT_EXPIRY` — for every config object, `MemoryConfig` or duck-typed, whatever any edge's
    confidence is, and on an empty store: a malformed policy refuses with ValueError and nothing is written (N4d).
    §4D: each due candidate is then applied through the store's `expiry_transition`, which re-reads the edge and
    decides from its CURRENT row inside one write transaction (N4h); a store without it refuses here, before any
    edge is read (the owner's ruling, 2026-11-02). A later ordinary failure keeps the per-edge prefix: transitions
    already committed stay committed, and the error propagates (N4d-prefix). The counts keep the shipped meaning
    (R2-02, N4i): `decayed` counts decay-triggered invalidations only, never a retained decay."""
    from .config import validate_decay_bound
    from .store.base import Store
    decay_factor = validate_decay_bound("decay_factor", config.decay_factor)
    confidence_floor = validate_decay_bound("confidence_floor", config.confidence_floor)
    lifetimes = dict(config.volatility_lifetime_days)      # copied at entry: the config's dict is mutable (N3)
    # the behaviour table, read from THIS module's name at entry, as the shipped expire() read it: a host that edits
    # schema.DEFAULT_EXPIRY in place, and one that rebinds lifecycle.DEFAULT_EXPIRY, both reach the transition
    # (research's F2, 2026-11-02); copied, like the lifetimes
    behaviors = dict(DEFAULT_EXPIRY)
    # the method the store actually RESOLVES (a delegating wrapper's included: its __getattr__ reaches the inner
    # store's), refused when absent or when it is the Store base's refusing default — asked of the resolved method,
    # never of the wrapper's class (research, 2026-11-02: Wrapper(non-overriding subclass) escaped a class lookup).
    # Residual: a __getattr__ returning a callable with no __func__ passes here and is refused at its first call.
    impl = getattr(store, "expiry_transition", None)
    if impl is None or getattr(impl, "__func__", None) is Store.expiry_transition:
        raise NotImplementedError(
            f"{type(store).__name__} has no expiry_transition: specs/0048 §4D decides expiry from each edge's current "
            f"row inside one write transaction, and expire() runs no expiry on a store without it")
    now = now or utcnow()
    lapsed = decayed = flagged = 0
    for e in store.edges(user_id, active_only=True):
        lifetime = lifetimes.get(e.volatility)
        # the LISTING picks candidates; the transition decides on the row as committed when it runs
        if lifetime is None or (now - e.provenance.observed_at).days <= lifetime:
            continue
        outcome = store.expiry_transition(user_id, e.id, now=now, lifetimes=lifetimes, behaviors=behaviors,
                                          decay_factor=decay_factor, confidence_floor=confidence_floor)
        if outcome == "lapsed":
            lapsed += 1
        elif outcome == "decayed":
            decayed += 1
        elif outcome == "flagged":
            flagged += 1
    return {"lapsed": lapsed, "decayed": decayed, "flagged_for_confirmation": flagged}

CONSOLIDATE_SYSTEM = (
    "You compact an AI assistant's old interaction history into fewer, denser "
    "records without losing anything a future question might need."
)

CONSOLIDATE_PROMPT = """Compact these dated episodes into FEWER consolidated
records. Preserve, VERBATIM and individually dated, every first occurrence of:
a failure, the fix for a failure, an illness/injury, and any dated commitment or
deadline. Merge only routine/repetitive activity.

EPISODES (oldest first):
{episodes}

Return ONLY JSON:
{{"records": [{{"date": "<YYYY-MM-DD>", "summary": "<one sentence>"}}]}}
Fewer records than the input. Keep dates and specifics exact."""


def _recover(store, user_id: str) -> int:
    """specs/0010 X2/X13 — roll each recovery-pending op to a safe terminal state and
    return the count actually resolved this pass. `OUTPUTS_DURABLE` rolls FORWARD
    (idempotent delete-then-finalize, never a re-consolidation); an EXPIRED pre-cutover
    op is cleanly `ABANDONED`. A LIVE pre-cutover op (a peer heartbeating) is left
    pending — `abandon` refuses a live lease (X7), so it is not counted as recovered."""
    from .schema import ConsolidationState as _S
    resolved = 0
    for op in store.pending_consolidations(user_id):
        if op.state is _S.OUTPUTS_DURABLE:
            store.delete_claimed_inputs_if_current(op.operation_id, op.fence)
            if store.transition_consolidation_if_current(
                    op.operation_id, op.fence, None, _S.FINALIZED):
                resolved += 1
        elif store.abandon_consolidation_if_current(op.operation_id, op.fence):
            resolved += 1
    return resolved


#: specs/0021 §4b — the CLOSED per-pool status set
POOL_STATUSES = ("ok", "failed", "contended", "below-threshold")

#: specs/0021 §4b — the CLOSED, CONTENT-FREE error-code enum. NEVER
#: `str(exc)`: an LLM exception can echo prompt or episode text, and the
#: AuditLog's "no memory text ever" invariant forbids it (external R4-3). The
#: code is the ONLY error value that reaches either carrier — the per-pool
#: result AND the audit event — so there is one value in two carriers rather
#: than a safe one and a leaky one.
POOL_ERROR_CODES = ("llm-error", "store-error", "claim-contention",
                    "validation-error", "timeout")


def _pool_result(status: str, *, consolidated: int = 0, into: int = 0,
                 error: Optional[str] = None) -> dict:
    if status not in POOL_STATUSES:
        raise ValueError(f"pool status {status!r} outside {POOL_STATUSES}")
    if error is not None and error not in POOL_ERROR_CODES:
        raise ValueError(
            f"pool error {error!r} is not one of the closed content-free "
            f"codes {POOL_ERROR_CODES} — a free-text error would put memory "
            f"text into the audit sink (specs/0021 §4b)")
    out = {"status": status, "consolidated": consolidated, "into": into}
    if error is not None:
        out["error"] = error
    return out


def partition_cold(store, user_id: str, cold: list) -> list:
    """specs/0021 §4b step 1 — partition candidates by RESOLVED IDENTITY, and
    order the pools deterministically.

    POLICY-INDEPENDENT (§2, external F5): no `ScopePolicy` is consulted, and
    none exists at this layer. Policy is a read-side concept; no process's
    configuration may change what the store MERGES, so an identity-bearing
    store partitions whether or not any host ever configures scope groups.

    One pool per resolved identity digest; ONE pool for the host-produced
    unidentified under the reserved `pool:unidentified` key (0006 digests a
    source-less identity to None, so the shared pool needs a non-digest key
    and the colon makes collision with 64-hex impossible); UNRESOLVED
    candidates are in NO pool at all (W9 — legacy, imported and recovered
    derivatives fail closed rather than joining the pool they claim).

    Returns `[(pool_key, [episodes])]` in the order pools must run: sorted by
    identity digest, the unidentified pool LAST."""
    from .scope import SHARED, SHARED_POOL_KEY, UNRESOLVED
    from .scope_read import MembershipResolver
    if not hasattr(store, "local_origin"):
        # a backend with no 0006 store identity has no identities to partition
        # BY; every candidate is unidentified, which is the shared pool — the
        # identity-free regime of §5, reached honestly rather than by an
        # AttributeError.
        return [(SHARED_POOL_KEY, list(cold))] if cold else []
    resolver = MembershipResolver(store, user_id)
    # 0023 N6: revoked-source records enter NO pool — excluded HERE, at the
    # partition, so a pool that falls below threshold is a no-op rather than
    # a partial merge, and no downstream step needs its own copy of the rule.
    # Keyed on the standing set (empty set = the pre-0023 path, N12).
    standing = store.standing_revocations(user_id)
    pools: dict = {}
    for e in cold:
        if standing:
            from .scope_linkage import identity_digest_of
            d = identity_digest_of(e.provenance.origin, e.provenance.source_id,
                                   store.local_origin())
            if d is not None and d in standing:
                continue                          # N6: no pool for the revoked
        evidence = resolver.evidence(e)
        if evidence == UNRESOLVED:
            continue                              # W9: no pool, ever
        key = SHARED_POOL_KEY if evidence == SHARED else evidence
        pools.setdefault(key, []).append(e)
    order = sorted(k for k in pools if k != SHARED_POOL_KEY)
    if SHARED_POOL_KEY in pools:
        order.append(SHARED_POOL_KEY)
    return [(k, pools[k]) for k in order]


def _consolidate_pool(store, llm: Complete, user_id: str, config,
                      cold: list) -> dict:
    """ONE pool's consolidation: its OWN 0010 operation, claim, lease,
    crash-safety and recovery (§4b step 3). Every failure is CAUGHT and
    reported as a closed status + content-free code, so a later pool still
    runs (§4b step 4) — a pool's LLM error leaves the pools that already
    committed standing, permanently."""
    from .schema import (ConsolidationOutputDraft, ConsolidationState,
                         to_historical_id)  # noqa: F401
    import uuid
    listing = "\n".join(f"[{e.date}] {e.summary}" for e in cold)
    try:
        raw = llm(CONSOLIDATE_PROMPT.format(episodes=listing),
                  system=CONSOLIDATE_SYSTEM, role="compile")
    except TimeoutError:
        return _pool_result("failed", error="timeout")
    except Exception:
        return _pool_result("failed", error="llm-error")
    try:
        data = extract_json(raw)
        new = [r for r in data.get("records", [])
               if isinstance(r, dict) and r.get("date") and r.get("summary")]
    except Exception:
        return _pool_result("failed", error="validation-error")
    if not new or len(new) >= len(cold):
        return _pool_result("ok")                      # no compression
    # Claim the whole POOL atomically (X4). A contended set → None; a stale
    # candidate → ValueError: an input concurrently finalized out from under us,
    # OR attested-redacted since the listing above (specs/0041 round 10 — the
    # pool result does not distinguish the two; the redaction's own record does).
    # Either way, skip this pool having mutated nothing — and CONTINUE.
    owner = f"consolidate:{uuid.uuid4().hex[:12]}"
    lease = getattr(config, "consolidate_lease_seconds", 300)
    try:
        op = store.create_or_takeover_consolidation(
            user_id, [e.id for e in cold], owner, lease)
    except ValueError:
        return _pool_result("contended", error="claim-contention")
    except Exception:
        return _pool_result("failed", error="store-error")
    if op is None:
        return _pool_result("contended", error="claim-contention")
    # GENERATING → write every output (the store BINDS lineage=whole claimed set and
    # DERIVES the trust floor + date range from it, X8/X12/X23 — the whole-set-minimum
    # provenance logic now lives in the store, and CLEARS the inherited identity per
    # 0021 §4a/W8) → cutover (X1: write-before-delete) → delete inputs (X2) →
    # finalize (X20).
    try:
        store.transition_consolidation_if_current(
            op.operation_id, op.fence, owner, ConsolidationState.GENERATING)
        for r in new:
            store.write_consolidation_output_if_current(
                op.operation_id, op.fence, owner,
                ConsolidationOutputDraft(summary=str(r["summary"]),
                                         date_start=str(r["date"]),
                                         date_end=str(r["date"])))
        if not store.transition_consolidation_if_current(
                op.operation_id, op.fence, owner,
                ConsolidationState.OUTPUTS_DURABLE):
            # the lease was lost or taken over mid-flight: nothing is visible,
            # nothing is deleted, and a later pool is unaffected
            return _pool_result("contended", error="claim-contention")
        store.delete_claimed_inputs_if_current(op.operation_id, op.fence)
        store.transition_consolidation_if_current(
            op.operation_id, op.fence, owner, ConsolidationState.FINALIZED)
    except Exception:
        return _pool_result("failed", error="store-error")
    return _pool_result("ok", consolidated=len(cold), into=len(new))


def consolidate(store, llm: Complete, user_id: str, config, *,
                now: Optional[datetime] = None) -> dict:
    """Compact cold episodes (older than `consolidate_after_days`) for `user_id`,
    crash-safely (specs/0010), PER SCOPE (specs/0021 §4b).

    Runs recovery FIRST (X13, once for the user), then partitions the cold
    candidates by resolved identity and runs ONE 0010 operation PER POOL —
    each with its own claim, lease, crash-safety and recovery. Thresholds are
    PER POOL: four scope-A records plus four scope-B records with
    `consolidate_min_batch=8` is a NO-OP, because no global trigger exists.
    Pools fail INDEPENDENTLY: a pool's failure or contention leaves the pools
    that already committed standing and does not stop later pools.

    THE RESULT IS AN ADDITIVE SUPERSET of the shape this function has always
    returned. `{"consolidated", "into", "recovered"}` are PRESERVED VERBATIM
    as the rolled-up totals — so the shipped telemetry mapping, which reads
    exactly those keys, keeps working unchanged, and an identity-free store's
    VALUES are identical to before. The new keys sit beside them:
    `pools` (per pool: status, consolidated, into, and a CONTENT-FREE error
    code), `pools_ok`, `pools_failed`. The result SHAPE is new for every
    store — that is the disclosed part of §2's behaviour change, and the
    robustness checker was updated for it in the same commit."""
    now = now or utcnow()
    recovered = _recover(store, user_id)               # X13: recovery at its own start
    cutoff = (now.date() - _timedelta_days(config.consolidate_after_days))
    episodes = store.episodes(user_id)
    # Candidates exclude: outcome episodes (structured records the compactor never
    # sees), consolidation OUTPUTS (non-empty lineage — X16, never a candidate), and
    # already-claimed inputs (a concurrent op holds them — X4).
    # specs/0041 round 10 (found in sweep A/E): an ATTESTED-redacted episode is never a candidate — it stays
    # as its marker and is never a consolidation input (a consumed input would leave its attestation naming
    # an absent record). Excluded HERE, at the read, by the attestation record; the claim refuses one that
    # was redacted after this listing.
    redacted = store.redacted_targets(user_id, "episode")
    cold = [e for e in episodes if e.kind != "outcome" and not e.lineage
            and e.claimed_by is None and e.id not in redacted
            and _safe_date(e.date) and _safe_date(e.date) < cutoff]
    pools: dict = {}
    total_in = total_out = 0
    for key, members in partition_cold(store, user_id, cold):
        if len(members) < config.consolidate_min_batch:
            # the 4A + 4B / min_batch=8 cell: BOTH pools sit here and the run
            # is a no-op. There is no global trigger to fall back to.
            pools[key] = _pool_result("below-threshold")
            continue
        result = _consolidate_pool(store, llm, user_id, config, members)
        pools[key] = result
        total_in += result["consolidated"]
        total_out += result["into"]
    return {"consolidated": total_in, "into": total_out, "recovered": recovered,
            "pools": pools,
            "pools_ok": sum(1 for p in pools.values() if p["status"] == "ok"),
            "pools_failed": sum(1 for p in pools.values()
                                if p["status"] == "failed")}


# NOTE: the whole-set-minimum-trust provenance logic that used to live here (N9b /
# 0.4.4 security fix — INFERRED author, min confidence, weakest disclosure, retained
# third-party influence, currency capped at the newest input) now lives in the STORE's
# `write_consolidation_output_if_current._derive_output_metadata`, because specs/0010
# X23 requires those derived fields be computed at the fenced write boundary from the
# claimed set, not by the caller. See src/veracium/store/sqlite.py.


def _timedelta_days(n: int):
    from datetime import timedelta
    return timedelta(days=n)


def _safe_date(s: str) -> Optional[date]:
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None
