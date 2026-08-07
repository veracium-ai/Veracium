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
 ("src/veracium/compile.py", "compile_wiki", "set_wiki", "8add728df9b1"):
   (M, "none directly — **caches a trust decision**", "none",
    "➡️ **MOVED to `0004`.** Output outlives the inputs' revocation", "tracked as 0004 W1–W4 [M8-wiki]"),

 # -- the write path ---------------------------------------------------------
 ("src/veracium/graph.py", "apply_supersession", "add_edge", "3a4052969394"):
   (W, "`observed_at`, `confidence` (liveness refresh); `needs_confirmation` **NO LONGER cleared** (`specs/0008`)", "observation",
    "✅ **M3 — CLOSED by `specs/0008` (accepted 2026-08-07, implemented).** Same-author-class is not source identity; reinforcement now refreshes liveness only and `needs_confirmation` clears solely through `confirm()`",
    "`test_no_provenance_value_clears_staleness` · `test_same_author_restatement_does_not_clear_staleness` · `test_cross_author_restatement_does_not_clear`"),
 ("src/veracium/graph.py", "apply_supersession", "add_edge", "98cd90a70fb3"):
   (W, "`note` on the absorbed prior", "observation", "clean — annotates, never widens", "`test_absorbed_edges_never_render_as_history`"),
 ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", "a7a961c78cbd"):
   (W, "`active`, reason `absorbed_duplicate`", "observation", "clean — narrows", "`test_more_specific_arrival_absorbs_prior`"),
 ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", "cda8875a699c"):
   (W, "`active`, reason `superseded`", "observation",
    "➡️ **`0003`** — cross-class supersession; unfiltered today", "tracked as 0003 I1/I2 [M7-correct]"),
 ("src/veracium/graph.py", "apply_supersession", "add_edge", "1e539a527213"):
   (W, "**`valid_from = min`** on the incoming edge, `observed_at`, `confidence`", "observation",
    "🟡 **R1 — the edge is unpersisted here, so N1 holds narrowly.** Under immutable-identity this becomes construction, not mutation. §7c",
    "`test_valid_from_immutable_across_every_mutation_site`"),
 ("src/veracium/ingest.py", "ingest_event", "add_episode", "4af6ecf2af8b"):
   (W, "episode provenance (unparseable placeholder)", "observation",
    "clean — never retains raw event text", "`test_unparseable_extraction_degrades_gracefully`"),
 ("src/veracium/ingest.py", "ingest_event", "add_episode", "17d36f4cb482"):
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
 ("src/veracium/lifecycle.py", "consolidate", "delete_episode", "5bed480ae733"):
   (M, "**destroys episodes**", "none",
    "🔴 **OPEN — external review item 9.** Deletes ALL members *before* writing any replacement, so a crash between the loops is total loss. §7e",
    "➡️ **`specs/0010` X1–X6** — `test_no_crash_point_loses_data`; write-before-delete with lineage recovery [X-crash]"),
 ("src/veracium/lifecycle.py", "consolidate", "add_episode", "78d73ee79000"):
   (M, "`author_of_evidence`, `derived_from`, `confidence`, `disclosure`, `observed_at`, `source_type`, `evidence_ref`", "none",
    "**M1 — fixed 0.4.4** + advisory GHSA-hcj3-8jqc-wqrp. Whole-set minimum trust",
    "`test_consolidation_preserves_and_compresses`"),

 # -- portability ------------------------------------------------------------
 ("src/veracium/portability.py", "import_memory", "add_edge", "1b0c15265a4e"):
   (W, "**every trust field, reconstructed from a file**; a cross-user remap now mints fresh ids so it COPIES, never transfers ownership (`specs/0008` §6d)", "transfer",
    "➡️ **MOVED to `0005`.** No capping on the `user_id` remap", "tracked as 0005 P1–P4 [M6-import]"),
 ("src/veracium/portability.py", "import_memory", "add_episode", "0c90065fe4bc"):
   (W, "episode provenance from a file (id/edge_id remapped on a cross-user copy)", "transfer", "➡️ moved with M6", "tracked as 0005 P1–P4 [M6-import]"),
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
  ("src/veracium/compile.py", "compile_wiki", "set_wiki", "8add728df9b1"): "open_moved",
  ("src/veracium/graph.py", "apply_supersession", "add_edge", "3a4052969394"): "clean",
  ("src/veracium/graph.py", "apply_supersession", "add_edge", "98cd90a70fb3"): "clean",
  ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", "a7a961c78cbd"): "clean",
  ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", "cda8875a699c"): "open_moved",
  ("src/veracium/graph.py", "apply_supersession", "add_edge", "1e539a527213"): "clean",
  ("src/veracium/ingest.py", "ingest_event", "add_episode", "4af6ecf2af8b"): "clean",
  ("src/veracium/ingest.py", "ingest_event", "add_episode", "17d36f4cb482"): "clean",
  ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "52f316b93ba6"): "clean",
  ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "b832f3d50c54"): "clean",
  ("src/veracium/lifecycle.py", "expire", "add_edge", "79eaf6e63a9c"): "open",
  ("src/veracium/lifecycle.py", "expire", "add_edge", "1d9541b12c69"): "clean",
  ("src/veracium/lifecycle.py", "consolidate", "delete_episode", "5bed480ae733"): "open_moved",
  ("src/veracium/lifecycle.py", "consolidate", "add_episode", "78d73ee79000"): "fixed",
  ("src/veracium/portability.py", "import_memory", "add_edge", "1b0c15265a4e"): "open_moved",
  ("src/veracium/portability.py", "import_memory", "add_episode", "0c90065fe4bc"): "open_moved",
}
