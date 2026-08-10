"""Per-call-site verdicts for the specs/0002 audit manifest.

Keyed on (file, qualified scope, mutator, fingerprint). The fingerprint hashes
the call's normalised expression plus its enclosing branch and condition, so a
verdict follows WHAT THE CALL IS. Moving a call keeps its verdict; swapping two
different calls invalidates both -- the ordinal scheme this replaces silently
reattached verdicts on a reorder (third external review, item 4). `audit_manifest.py --check` fails when a site here has no
counterpart in the code, or a site in the code has no entry here.

Columns: operation class | trust fields touched | evidence-bearing? | verdict | test
"""

W, M = "write-time", "maintain-time"

# One POSITIVE vocabulary. There used to be two negatively-phrased columns --
# the manifest asked "evidence-bearing?" and 0002 6a asked "evidence-free?" --
# and they gave opposite answers for import_memory without either being wrong on
# its own terms. Two negations of one question is how a contradiction hides.
#
#   act          an authorised call through a dedicated entry point that is not
#                model-reachable (0008's principle: the ACT is the evidence)
#   observation  new content arriving from outside and being extracted
#   none         maintenance: no new information, only recognition of existing
#                records. N9's monotonicity applies HERE and only here.
#   transfer     records moved between stores. NOT evidence: the operator's act
#                is authorised, the records it carries are not vouched for by
#                anyone. Becomes `observation` only if 0005 ever authenticates
#                the source -- until then it takes 0005's cap and no exception.

DISPOSITIONS = {
 # -- explicit user verbs ----------------------------------------------------
 ("src/veracium/__init__.py", "Memory.dispute", "invalidate_edge", "3bbd6e160bb1"):
   (W, "`active`, `invalidation_reason`", "act", "clean — narrows only", "`test_dispute_removes_from_assertable_but_keeps_history`"),
 ("src/veracium/__init__.py", "Memory.dispute", "add_episode", "4e11253939a4"):
   (W, "episode provenance", "act", "clean", "`test_dispute_removes_from_assertable_but_keeps_history`"),
 ("src/veracium/__init__.py", "Memory.confirm", "confirm_edge", "0f81d39ca11c"):
   (W, "`needs_confirmation` (cleared), `observed_at`, `confidence`, the confirmation episode + record — ALL in one atomic store operation", "act",
    "clean — `specs/0008`: `confirm()` is the ONLY path that clears `needs_confirmation`, through the atomic `confirm_edge` (M2 first-known immutability preserved; the record is mandatory, C7)",
    "`test_confirm_clears_staleness` · `test_confirm_advances_liveness_not_first_known`"),
 ("src/veracium/__init__.py", "Memory.record_outcome", "append_outcome_if_head", "65802c446a27"):
   (W, "episode provenance / `author_of_evidence` (new chain link — NEVER overwritten)", "act",
    "clean — **`specs/0009` (ACCEPTED): M4 CLOSED.** `record_outcome` now APPENDS a new chain link via the CAS `append_outcome_if_head` (never mutates a prior judgment's author, H1); the Store assigns `seq`/id and DERIVES `source_type`; counters are derived from chain heads (H6).",
    "`test_outcome_authorship_is_never_overwritten` · `test_record_outcome_is_edge_blind_never_supersedes`"),
 ("src/veracium/__init__.py", "Memory.record_outcome", "add_edge", "5b46e2531803"):
   (W, "`outcome_counts`, `last_outcome`, `needs_confirmation`", "act",
    "clean — counters are information, never gating", "`test_record_outcome_is_edge_blind_never_supersedes`"),
 ("src/veracium/__init__.py", "Memory.correct", "invalidate_edge", "c81beaca32cb"):
   (W, "`active`, `invalidation_reason=corrected`", "act",
    "➡️ **MOVED to `0003` §1b** — this is a supersession path", "tracked as 0003 I9/I10 [M7-correct]"),
 ("src/veracium/__init__.py", "Memory.correct", "add_edge", "72b03718535b"):
   (W, "**`author_of_evidence` hardcoded USER**, `disclosure`, `supersedes`", "act",
    "➡️ **MOVED to `0003` §1b (M7).** Resolved there: inherit the corrected edge's class", "tracked as 0003 I10 [M7-correct]"),
 ("src/veracium/__init__.py", "Memory.correct", "add_episode", "23255a7f3c3f"):
   (W, "episode provenance", "act", "➡️ moved with M7", "tracked as 0003 I10 [M7-correct]"),
 ("src/veracium/__init__.py", "Memory.forget", "forget_user", "c5d9e9e2da39"):
   (W, "**all** — irreversible erasure", "act", "clean — erasure is the contract", "`test_forget_erases_everything_and_only_that_user`"),
 ("src/veracium/cli.py", "_forget", "forget_user", "269b73112fab"):
   (W, "**all**", "act", "clean — same verb through the CLI", "`test_forget_cli_requires_confirmation`"),

 # -- derived views ----------------------------------------------------------
 ("src/veracium/compile.py", "compile_wiki", "set_wiki", "888fd4a4d703"):
   (M, "none directly — **caches a trust decision** (now carries the compiler-policy digest envelope, `0003` §4c-ii)", "none",
    "➡️ **MOVED to `0004`.** Output outlives the inputs' revocation; `0003` drops the wiki on a refusal-contention transition, but the general trust-reducing-invalidation drop is 0004", "tracked as 0004 W1–W4 [M8-wiki]"),

 # -- the write path ---------------------------------------------------------
 # specs/0003 (accepted 2026-08-08) folded the whole supersession outcome into ONE
 # atomic, CAS-linearized store primitive: apply_supersession no longer calls add_edge /
 # invalidate_edge directly (reinforcement refresh, absorption note/retire, the guarded
 # retirement, the incoming insert, and the refusal inventory are all in the plan). The
 # five former direct-mutation sites here are subsumed by this one call site. The
 # authority guard closes what was tracked as 0003 I1/I2 [M7-correct].
 ("src/veracium/graph.py", "apply_supersession", "apply_supersession_plan", "e1ecd66351bd"):
   (W, "the WHOLE supersession outcome — `active` (guarded retire / absorb), reinforcement persist-only (accepted `0012` Design 1: the incoming persists untouched, the prior is not written), `valid_from=min` on the incoming edge, the incoming insert, and the content-free refusal inventory; `needs_confirmation` never cleared here", "observation",
    "✅ **`0003` (accepted 2026-08-08, implemented) — the authority guard.** A differing value retires the prior ONLY when incoming effective authority >= the prior's; otherwise the retirement is REFUSED (both edges kept, a durable content-free refusal recorded). One atomic CAS-linearized plan on a complete `expected_state`; `valid_from=min` operates on the unpersisted incoming edge (construction, not mutation of a stored row). Closes the unfiltered functional-supersession loop (0003 I1–I5). `correct()` is a separate `supersedes=` writer, out of 0003 scope (0011 E5).",
    "`test_supersession_authority_matrix` · `test_refused_supersession_keeps_both` · `test_user_authored_ingest_can_supersede_third_party` · `test_a_refused_supersession_is_counted_and_logged`"),
 ("src/veracium/ingest.py", "ingest_event", "add_episode", "5d29e2f07e03"):
   (W, "episode provenance (unparseable placeholder)", "observation",
    "clean — never retains raw event text", "`test_unparseable_extraction_degrades_gracefully`"),
 ("src/veracium/ingest.py", "ingest_event", "add_episode", "c1fb106f3b09"):
   (W, "episode provenance", "observation", "clean — the origin of trust", "`test_third_party_text_never_moves_into_the_grounded_block`"),

 # -- maintenance ------------------------------------------------------------
 ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "52f316b93ba6"):
   (M, "`active`, reason `lapsed`", "none", "clean — narrows", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "b832f3d50c54"):
   (M, "`active`, reason `decayed`", "none", "clean — narrows", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/lifecycle.py", "expire", "add_edge", "79eaf6e63a9c"):
   (M, "**`confidence *= decay_factor`**", "none",
    "🔴 **OPEN — external review item 8.** `MemoryConfig` is an unvalidated dataclass; `decay_factor=2.0`, `NaN`, `-1.0` are all accepted, so this site can RAISE confidence and **N4 is false as written**. §7d",
    "🔴 **`specs/0002` N4b–N4d** — `test_config_bounds_are_validated`; **none passes today** [N4-decay]"),
 ("src/veracium/lifecycle.py", "expire", "add_edge", "1d9541b12c69"):
   (M, "`needs_confirmation = True`", "none", "clean — narrows; flags, never clears", "`test_expiry_lapse_confirm_and_reinforcement`"),
 # specs/0010 (ACCEPTED) — consolidate() rewritten onto the crash-safe state machine:
 # write-before-delete (X1), all-or-nothing claim (X4), roll-forward recovery (X2), the
 # trust floor now DERIVED in the store (X23). The former total-loss delete-before-write
 # (review item 9) and the M1 whole-set-minimum trust are both CLOSED.
 ("src/veracium/lifecycle.py", "consolidate", "create_or_takeover_consolidation", "2cd7f2e21d07"):
   (M, "claims the whole cold batch (`claimed_by`/`operation_id` on each input)", "act",
    "clean — specs/0010 X4/X11: the batch is claimed atomically or not at all; a contended/stale set skips the pass, mutating nothing",
    "`test_concurrent_consolidation_claims_all_or_nothing` · `test_partial_claim_is_impossible`"),
 ("src/veracium/lifecycle.py", "consolidate", "write_consolidation_output_if_current", "76c4ec1e9bdf"):
   (M, "writes each provisional output; store BINDS lineage=claimed set and DERIVES the trust floor (X23)", "act",
    "clean — specs/0010 X1/X8/X12/X23: outputs are durable BEFORE any delete, carry the whole batch as lineage, and take the whole-set-minimum trust (the old M1/0.4.4 logic, moved to the fenced write)",
    "`test_output_trust_is_the_whole_set_minimum` · `test_lineage_is_the_whole_batch`"),
 ("src/veracium/lifecycle.py", "consolidate", "transition_consolidation_if_current", "00b059deffa3"):
   (M, "advances state (CLAIMED→GENERATING)", "act",
    "clean — specs/0010 §4b-ii: owner+live-lease guarded",
    "`test_every_read_sees_exactly_one_representation`"),
 ("src/veracium/lifecycle.py", "consolidate", "transition_consolidation_if_current", "d64d0ee80464"):
   (M, "the visibility cutover (GENERATING→OUTPUTS_DURABLE)", "act",
    "clean — specs/0010 X1/X14/X22: refuses with zero bound outputs, bumps store_version, and is the write-before-delete point of no return",
    "`test_visibility_cutover_bumps_store_version` · `test_cutover_refuses_with_no_bound_output`"),
 ("src/veracium/lifecycle.py", "consolidate", "delete_claimed_inputs_if_current", "8565cc3059e5"):
   (M, "deletes the claimed inputs AFTER outputs are durable", "act",
    "clean — specs/0010 X1/X2: write-before-delete; the batch delete is all-or-nothing and only reachable post-cutover",
    "`test_every_read_sees_exactly_one_representation`"),
 ("src/veracium/lifecycle.py", "consolidate", "transition_consolidation_if_current", "f6c9281664ba"):
   (M, "finalizes (OUTPUTS_DURABLE→FINALIZED)", "act",
    "clean — specs/0010 X20: refuses until every claimed input is deleted, so no terminal op strands hidden inputs",
    "`test_finalize_refuses_before_inputs_deleted`"),
 ("src/veracium/lifecycle.py", "_recover", "transition_consolidation_if_current", "6e0ea1c3cdf2"):
   (M, "recovery roll-forward finalize", "act",
    "clean — specs/0010 X2/X13: an OUTPUTS_DURABLE op recovered by idempotent re-delete + finalize, never a re-consolidation",
    "`test_recovery_finalises_after_committed_delete`"),
 ("src/veracium/lifecycle.py", "_recover", "delete_claimed_inputs_if_current", "49d3539863c9"):
   (M, "recovery idempotent re-delete", "act",
    "clean — specs/0010 X2: there is no durable 'some inputs deleted' state; the re-delete is idempotent",
    "`test_recovery_finalises_after_committed_delete`"),
 ("src/veracium/lifecycle.py", "_recover", "abandon_consolidation_if_current", "3796d339c301"):
   (M, "recovery cleanup of an expired pre-cutover op", "act",
    "clean — specs/0010 X7/X15: abandons only an EXPIRED-lease op (never a live peer), cleanup-complete before any new fence",
    "`test_takeover_of_expired_generating_cleans_first` · `test_a_live_lease_is_not_preempted`"),

 # -- portability ------------------------------------------------------------
 ("src/veracium/portability.py", "_preflight_and_commit", "commit_outcome_import_plan", "83f7d603598f"):
   (W, "**every trust field, reconstructed from a file** — edges AND whole outcome chains; a cross-user remap mints fresh ids (a COPY, never a transfer) and now remaps `supersedes_episode` too (`specs/0009` §4c Correction B)", "transfer",
    "specs/0009 (ACCEPTED) §4c CLOSED: import is now WHOLE-FILE validate-or-refuse — the entire plan is parsed, remapped, legacy-converted and topology-checked BEFORE any write, then committed through this ONE atomic primitive (no partial import, H5; no branch and linearized against append_outcome_if_head, H4; H14 fences outcome rows out of the generic mutators). **Residual: the cross-user import-cap concern (M6 — capping the `user_id` remap) remains OPEN, tracked to `0005`.**", "tracked as 0005 P1–P4 [M6-import]"),
}


# --- explicit, mutually exclusive state per call site ------------------------
# The generator used to derive these by searching RENDERED ROWS for emoji, which
# double-counted every row whose verdict said one thing and whose test column
# pointed at another spec: 28 - 4 - 10 = 14, while the true unaffected count was
# 17. The v4 package shipped both numbers, in the manifest and in its own cover
# note. Semantic state is now declared, never inferred from presentation.
#
#   clean       no defect found here
#   fixed       defect found and fixed in a released version
#   open        defect open, owned by this spec
#   moved       owned by another spec
#   open_moved  open AND owned elsewhere
STATES = {
  ("src/veracium/__init__.py", "Memory.dispute", "invalidate_edge", "3bbd6e160bb1"): "clean",
  ("src/veracium/__init__.py", "Memory.dispute", "add_episode", "4e11253939a4"): "clean",
  ("src/veracium/__init__.py", "Memory.confirm", "confirm_edge", "0f81d39ca11c"): "clean",
  ("src/veracium/__init__.py", "Memory.record_outcome", "append_outcome_if_head", "65802c446a27"): "clean",
  ("src/veracium/__init__.py", "Memory.record_outcome", "add_edge", "5b46e2531803"): "clean",
  ("src/veracium/__init__.py", "Memory.correct", "invalidate_edge", "c81beaca32cb"): "open_moved",
  ("src/veracium/__init__.py", "Memory.correct", "add_edge", "72b03718535b"): "open_moved",
  ("src/veracium/__init__.py", "Memory.correct", "add_episode", "23255a7f3c3f"): "open_moved",
  ("src/veracium/__init__.py", "Memory.forget", "forget_user", "c5d9e9e2da39"): "clean",
  ("src/veracium/cli.py", "_forget", "forget_user", "269b73112fab"): "clean",
  ("src/veracium/compile.py", "compile_wiki", "set_wiki", "888fd4a4d703"): "open_moved",
  ("src/veracium/graph.py", "apply_supersession", "apply_supersession_plan", "e1ecd66351bd"): "clean",
  ("src/veracium/ingest.py", "ingest_event", "add_episode", "5d29e2f07e03"): "clean",
  ("src/veracium/ingest.py", "ingest_event", "add_episode", "c1fb106f3b09"): "clean",
  ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "52f316b93ba6"): "clean",
  ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "b832f3d50c54"): "clean",
  ("src/veracium/lifecycle.py", "expire", "add_edge", "79eaf6e63a9c"): "open",
  ("src/veracium/lifecycle.py", "expire", "add_edge", "1d9541b12c69"): "clean",
  ("src/veracium/lifecycle.py", "consolidate", "create_or_takeover_consolidation", "2cd7f2e21d07"): "clean",
  ("src/veracium/lifecycle.py", "consolidate", "write_consolidation_output_if_current", "76c4ec1e9bdf"): "clean",
  ("src/veracium/lifecycle.py", "consolidate", "transition_consolidation_if_current", "00b059deffa3"): "clean",
  ("src/veracium/lifecycle.py", "consolidate", "transition_consolidation_if_current", "d64d0ee80464"): "clean",
  ("src/veracium/lifecycle.py", "consolidate", "delete_claimed_inputs_if_current", "8565cc3059e5"): "clean",
  ("src/veracium/lifecycle.py", "consolidate", "transition_consolidation_if_current", "f6c9281664ba"): "clean",
  ("src/veracium/lifecycle.py", "_recover", "transition_consolidation_if_current", "6e0ea1c3cdf2"): "clean",
  ("src/veracium/lifecycle.py", "_recover", "delete_claimed_inputs_if_current", "49d3539863c9"): "clean",
  ("src/veracium/lifecycle.py", "_recover", "abandon_consolidation_if_current", "3796d339c301"): "clean",
  ("src/veracium/portability.py", "_preflight_and_commit", "commit_outcome_import_plan", "83f7d603598f"): "open_moved",
}
