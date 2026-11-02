"""specs/0021 §3 — the COMBINING-SITE registry, and what each site does about
scope.

§3's operation matrix claims to be TOTAL: one row per operation that combines
records. External F4 is why that claim is not allowed to live in prose — the
matrix that preceded it rested on a reach assertion that was false about the
shipped code (it said consolidation "groups by trust class today"; consolidate
was one global pool). A hand-written inventory of merge paths is exactly what
the next merge path escapes silently, and a combining path that escapes the
matrix escapes the scope rule.

So the enumeration is MECHANICAL and lives in `specs/combining_sites.py` (it
parses the store's SQL); this module holds the VERDICTS, in the code, next to
the writers — the 0014 `CONSUMPTION_SITES` precedent.
`test_scope_operation_matrix_is_total` (W3) fails when the two disagree, and
is itself exercised against a synthetic module carrying a new unregistered
write, so the gate is known to bite rather than merely to exist.

**"Combining" is defined here, once** (§3): *any operation that writes a
record derived from, or mutates a record because of, MORE THAN ONE existing
record.* Writing one record from one record is not combining. Removing a
combination's output is not combining. Mutating N records because of ONE
operation record, with no content flowing between them, is not combining.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["OPERATIONS", "COMBINING_SITES", "SiteSpec"]


@dataclass(frozen=True)
class SiteSpec:
    """One record-mutating code path's verdict.

    `combining` False REQUIRES `why` and FORBIDS `scope_rule`; True REQUIRES
    both `operations` (drawn from `OPERATIONS`) and `scope_rule` — an omission
    must never be able to read as a decision."""

    combining: bool
    operations: tuple = ()
    scope_rule: str = ""
    why: str = ""

    @property
    def operation(self) -> str:
        return " · ".join(self.operations)


#: §3's matrix rows, and whether each is expected to OWN combining write
#: sites. `non-combining` is a falsifiable claim, not a shrug: if a site ever
#: claims one of those operations, the gate fails and the matrix row is
#: wrong.
OPERATIONS = {
    "absorption": "combining",
    "supersession": "combining",
    "consolidation": "combining",
    "wiki-compilation": "combining",
    # 0012 Design 1: a restatement is PERSISTED AS ITS OWN EDGE and transfers
    # nothing onto the prior — the prior is not read-modify-written at all.
    # One record in, one record out: no site of its own.
    "reinforcement": "non-combining",
    # per-EDGE ageing against that edge's own observed_at (0012's frozen
    # invariant). Expiry mutates a lot of records and combines none of them.
    "expiry": "non-combining",
}

_STORE = "src/veracium/store/sqlite.py"

#: (module, function) -> SiteSpec. Keyed by the ENCLOSING FUNCTION of a SQL
#: write statement, which is what `specs/combining_sites.py` enumerates.
COMBINING_SITES = {

    # -- specs/0027: the semantic derived index -----------------------------
    (_STORE, "_upsert_embedding_in_txn"): SiteSpec(
        False, why="specs/0041 §4e (tranche 5): the write now sits in the in-transaction body the lock-taking `upsert_embedding` calls — 0027 §4f: writes ONE derived-index row (a vector bound to "
        "one edge's content digest) — regenerable, trust-inert, never "
        "evidence; digest-conditional against the SINGLE live edge it "
        "derives from, so nothing is combined and no scope rule applies "
        "(visibility is enforced at read by semantic_candidates' "
        "visible-id filter, 0027 §4a Stage 1)"),

    # -- absorption + supersession: the write-time combining pair -----------
    (_STORE, "apply_supersession_plan"): SiteSpec(
        True, ("absorption", "supersession"),
        "absorption partitions by RESOLVED IDENTITY (§4c) — the candidate "
        "gate is `graph._absorption_scope_gate`, and this primitive REFUSES a "
        "cross-scope or unclosable prior independently of the planner; "
        "supersession stays scope-BLIND (§3 — truth is global, visibility is "
        "0020's job)"),
    (_STORE, "_upsert_edge_row"): SiteSpec(
        True, ("absorption", "supersession"),
        "the survivor row whose valid_from/observed_at/confidence/ungrounded "
        "were inherited from the absorbed set; same-scope by the gate above"),
    (_STORE, "_invalidate_edge_row"): SiteSpec(
        True, ("absorption", "supersession"),
        "retires a prior BECAUSE of the incoming — absorbed_duplicate only "
        "within one scope (§4c); superseded is scope-blind (§3)"),
    # ---- specs/0022 (the revocation sweep's writers, external round 21) -----
    # None of the four COMBINES: each mutates ONE record because of the
    # standing revocation state, never because of another record's content.
    # The recompute verb LOOKS combining (it folds contributor sides) but the
    # fold is computed by the sweep from the EXISTING ledger rows — this
    # writer applies precomputed values to one row and consults nothing else.
    (_STORE, "_retire_episode_row"): SiteSpec(
        False, why="0022 R18: retires ONE episode because its resolved source identity "
        "is revoked — a standing-state consequence, not a combination; the "
        "sole episode-retirement writer, mirroring _invalidate_edge_row"),
    (_STORE, "_reinstate_edge_row"): SiteSpec(
        False, why="0022's reinstate verb: reverses OUR OWN revoked_source retirement on "
        "ONE edge when the last overlapping revocation lifts; drops the wiki "
        "because the derived view changed in the restoring direction too"),
    (_STORE, "_reinstate_episode_row"): SiteSpec(
        False, why="the episode half of the reinstate verb — one record, standing-state "
        "consequence"),
    (_STORE, "_recompute_edge_row"): SiteSpec(
        False, why="0022's recompute verb: applies the sweep's PRECOMPUTED "
        "RECOMPUTED_FIELDS (valid_from, observed_at, confidence) to one edge. "
        "The fold over surviving contributor sides happens in the sweep over "
        "ledger rows; this writer consults no second record"),
    (_STORE, "_write_contribution"): SiteSpec(
        True, ("absorption",),
        "the native `absorption` row: the direct link, carrying the absorbed "
        "prior's identity digest and the typed contributor_ref. Its accepted "
        "{base, contributor} payload is NOT amended (§7b SITE MATRIX row 1)"),
    (_STORE, "_write_absorption_flattening"): SiteSpec(
        True, ("absorption",),
        "§4c WRITE-TIME FLATTENING: copies of the prior's TRANSITIVELY CLOSED "
        "row set onto the survivor at `scope-attribution`, payload "
        "{\"flattened\": true}, native per-row keys — so every post-0021 "
        "survivor's row set is its whole ancestry by construction (§7b row 2)"),
    (_STORE, "commit_outcome_import_plan"): SiteSpec(
        True, ("absorption",),
        "the import primitive writes reconstructed absorption linkage derived "
        "from the WHOLE export file (0009 §4c as amended). Attribution only, "
        "no reversal; the ledger does not travel, so imported CONSOLIDATION "
        "derivatives arrive UNRESOLVED (§2c) — the reconstruction restores "
        "absorption membership, it never mints scope evidence"),

    # -- consolidation: the maintain-time combining path --------------------
    (_STORE, "_claim_inputs"): SiteSpec(
        True, ("consolidation",),
        "claims ONE POOL's inputs. `lifecycle.partition_cold` selects the "
        "set, so a claim never spans two identities (§4b) and each pool holds "
        "its own claim, lease and crash-safety"),
    (_STORE, "write_consolidation_output_if_current"): SiteSpec(
        True, ("consolidation",),
        "the derivative, written from the whole claimed set. Its identity is "
        "CLEARED (origin=None/source_id=None — §4a/W8): store-authored means "
        "store-identified, and membership travels through the ledger, never "
        "through a copied identity"),
    (_STORE, "_write_consolidation_contributions"): SiteSpec(
        True, ("consolidation",),
        "the N×M ledger rows at the cutover — the ONLY membership evidence a "
        "cleared-identity derivative has (§4a). All inputs share one "
        "identity by the partition, so a complete row set resolves to that "
        "identity or to SHARED; anything else is UNRESOLVED (0020 §4a-iii)"),
    (_STORE, "delete_claimed_inputs_if_current"): SiteSpec(
        True, ("consolidation",),
        "deletes the N inputs because the M outputs are durable — the "
        "combination's other half, and PERMANENT (§7: there is no "
        "un-consolidate)"),

    # -- the second synthesis path ------------------------------------------
    (_STORE, "set_wiki"): SiteSpec(
        True, ("wiki-compilation",),
        "v1: the store-wide compile is UNCHANGED, and the wiki never reaches "
        "a principal-bearing response (0020 §4d excludes it). Per-scope "
        "compilation is the recorded widening (Q2), not a silent one"),

    # -- everything else: mutating, but not combining -----------------------
    (_STORE, "_evict_wiki_on_view_change"): SiteSpec(
        False, why="drops the user's cached wiki because ONE record's assertion view moved under a write "
                   "(RII-R2-01); it writes no record"),
    (_STORE, "transition_consolidation_if_current"): SiteSpec(
        False, why="the consolidation cutover drops the user's cached wiki (RII-R2-01: it hides the inputs and "
                   "reveals the outputs, 0010 X9); the drop writes no record and derives nothing"),
    (_STORE, "discard_wiki"): SiteSpec(
        False, why="deletes the one wiki row a withheld compile published, conditional on it (RII-R2-01 D2); "
                   "derives nothing from any record"),
    (_STORE, "add_episode"): SiteSpec(
        False, why="one episode from one turn; derives nothing from any "
                   "other record"),
    (_STORE, "write_policy_receipt"): SiteSpec(
        False, why="specs/0027 §4g (v14): one receipt row from one recall; "
                   "it names the ids the recall already computed and derives "
                   "nothing from any other record — an audit row, not a "
                   "synthesis"),
    (_STORE, "delete_episode"): SiteSpec(
        False, why="removes one record"),
    (_STORE, "_redact_in_txn"): SiteSpec(
        False, why="specs/0041 §4a (tranche 3; the in-transaction body since 4b, shared with the import's "
                   "notice application): rewrites ONE record's content carriers in place "
                   "from the treatment map — the marker, an empty shape, a registry value — and "
                   "the side rows keyed to it (its confirmations' digest, its ledger digests, its "
                   "refusal rows' copied relation, its embedding rows, its journal states, the wiki "
                   "cache); the attestation record it inserts names that same record. No second "
                   "record contributes and none is derived; a redaction never deletes a record or "
                   "changes a disposition (§4d, §4h(i))"),
    (_STORE, "forget_user"): SiteSpec(
        False, why="0009 erasure — drops the tenant's tables wholesale "
                   "(ledger included), which moots membership rather than "
                   "deriving it"),
    (_STORE, "confirm_edge"): SiteSpec(
        False, why="specs/0008 — clears needs_confirmation on ONE edge and "
                   "records the confirmation; no second record contributes"),
    (_STORE, "add_reply"): SiteSpec(
        False, why="specs/0047 §4a — appends ONE reply to ONE edge and its registry row; a resolve READS its "
                   "challenge to check it, derives nothing from it and writes nothing to it"),
    (_STORE, "_set_notice_state"): SiteSpec(
        False, why="specs/0041 §11.6.6 — records or moves ONE witnessed notice's pending/standing state; it treats no "
                   "record and no second record contributes"),
    (_STORE, "_apply_lifetime_transition"): SiteSpec(
        False, why="specs/0044 §4f-ii — ends ONE edge's arity-inventory membership or clears `applicable` on ITS "
                   "outcome row, from that edge's own prior and new row; no second record contributes"),
    (_STORE, "_allocate_act_seq"): SiteSpec(
        False, why="specs/0008 v7 §6f — advances the store's one act counter; a position, not content, and no "
                   "record contributes to another"),
    (_STORE, "append_outcome_if_head"): SiteSpec(
        False, why="appends one outcome record at its chain head; the head "
                   "is a POSITION, not a second source of content"),
    (_STORE, "_drop_contributions_for_survivor"): SiteSpec(
        False, why="accepted 0014 A10 — a ledger row lives exactly as long "
                   "as its survivor. Removes attribution, never derives it "
                   "(and §4c flattening is what makes that harmless)"),
    (_STORE, "_write_op"): SiteSpec(
        False, why="0010 operation bookkeeping — an operation row, not a "
                   "memory record"),
    (_STORE, "_abandon"): SiteSpec(
        False, why="0010 rollback — releases claims and drops the "
                   "provisional outputs of a combination that never "
                   "committed. Removing a combination is not one"),
    (_STORE, "_bump"): SiteSpec(
        False, why="the store_version counter — not a record at all"),
    (_STORE, "invalidate_edge"): SiteSpec(
        False, why="drops the wiki CACHE for the user (the edge row itself "
                   "is written by _invalidate_edge_row); a cache "
                   "invalidation combines nothing"),
    # specs/0048 §4D: expire()'s per-edge transition, decided from ONE edge's own current row (its writes go through
    # _invalidate_edge_row / _upsert_edge_row, registered above)
    (_STORE, "expiry_transition"): SiteSpec(
        False, why="drops the wiki CACHE for the user when a retirement "
                   "ends a refusal contention, as invalidate_edge does; "
                   "the edge is decided from its own row alone, so a "
                   "cache invalidation combines nothing"),
}
