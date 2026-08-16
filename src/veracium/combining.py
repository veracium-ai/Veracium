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
    (_STORE, "add_episode"): SiteSpec(
        False, why="one episode from one turn; derives nothing from any "
                   "other record"),
    (_STORE, "delete_episode"): SiteSpec(
        False, why="removes one record"),
    (_STORE, "forget_user"): SiteSpec(
        False, why="0009 erasure — drops the tenant's tables wholesale "
                   "(ledger included), which moots membership rather than "
                   "deriving it"),
    (_STORE, "confirm_edge"): SiteSpec(
        False, why="specs/0008 — clears needs_confirmation on ONE edge and "
                   "records the confirmation; no second record contributes"),
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
}
