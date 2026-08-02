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
 ("src/veracium/__init__.py", "Memory.confirm", "add_edge", "5b46e2531803"):
   (W, "`observed_at`, `needs_confirmation`, `confidence`", "act",
    "**M2 — fixed 0.4.5**; return-value sibling **fixed 0.4.6** (`533092c`)",
    "`test_confirm_returns_the_real_valid_from_not_the_confirmation_date`"),
 ("src/veracium/__init__.py", "Memory.confirm", "add_episode", "bdd949deaa6a"):
   (W, "episode provenance", "act", "clean", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/__init__.py", "Memory.record_outcome", "add_episode", "02cff46798fc"):
   (W, "**`author_of_evidence` (overwritten)**", "act",
    "🔴 **M4 — OPEN.** The shipped note survives exactly one upgrade; the structured field is still overwritten. Frozen behaviour specified in **`specs/0009`** §4.",
    "➡️ **`specs/0009` H1–H7** — `test_outcome_authorship_is_never_overwritten`; **none passes today**"),
 ("src/veracium/__init__.py", "Memory.record_outcome", "add_episode", "1b9e2cf47dcf"):
   (W, "episode provenance (new outcome)", "act", "clean — new event, own provenance", "`test_record_outcome_is_edge_blind_never_supersedes`"),
 ("src/veracium/__init__.py", "Memory.record_outcome", "add_edge", "5b46e2531803"):
   (W, "`outcome_counts`, `last_outcome`, `needs_confirmation`", "act",
    "clean — counters are information, never gating", "`test_record_outcome_is_edge_blind_never_supersedes`"),
 ("src/veracium/__init__.py", "Memory.correct", "invalidate_edge", "c81beaca32cb"):
   (W, "`active`, `invalidation_reason=corrected`", "act",
    "➡️ **MOVED to `0003` §1b** — this is a supersession path", "tracked as 0003 I9/I10"),
 ("src/veracium/__init__.py", "Memory.correct", "add_edge", "72b03718535b"):
   (W, "**`author_of_evidence` hardcoded USER**, `disclosure`, `supersedes`", "act",
    "➡️ **MOVED to `0003` §1b (M7).** Resolved there: inherit the corrected edge's class", "tracked as 0003 I10"),
 ("src/veracium/__init__.py", "Memory.correct", "add_episode", "23255a7f3c3f"):
   (W, "episode provenance", "act", "➡️ moved with M7", "tracked as 0003 I10"),
 ("src/veracium/__init__.py", "Memory.forget", "forget_user", "c5d9e9e2da39"):
   (W, "**all** — irreversible erasure", "act", "clean — erasure is the contract", "`test_forget_erases_everything_and_only_that_user`"),
 ("src/veracium/cli.py", "_forget", "forget_user", "2acc9db31dbe"):
   (W, "**all**", "act", "clean — same verb through the CLI", "`test_forget_cli_requires_confirmation`"),

 # -- derived views ----------------------------------------------------------
 ("src/veracium/compile.py", "compile_wiki", "set_wiki", "8add728df9b1"):
   (M, "none directly — **caches a trust decision**", "none",
    "➡️ **MOVED to `0004`.** Output outlives the inputs' revocation", "tracked as 0004 W1–W4"),

 # -- the write path ---------------------------------------------------------
 ("src/veracium/graph.py", "apply_supersession", "add_edge", "b766ab223c71"):
   (W, "**`needs_confirmation` cleared**, `observed_at`, `confidence`", "observation",
    "🔴 **M3 — OPEN.** Same-author-class is not source identity; external review item 3, ruled R2. Fail-closed rule specified in §7b",
    "➡️ **`specs/0008` C1–C6** — `test_no_author_value_clears_staleness`; **none passes today**"),
 ("src/veracium/graph.py", "apply_supersession", "add_edge", "509e20030c74"):
   (W, "`note` on the absorbed prior", "observation", "clean — annotates, never widens", "`test_absorbed_edges_never_render_as_history`"),
 ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", "5d67f0861b5f"):
   (W, "`active`, reason `absorbed_duplicate`", "observation", "clean — narrows", "`test_more_specific_arrival_absorbs_prior`"),
 ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", "ddcab09b4f04"):
   (W, "`active`, reason `superseded`", "observation",
    "➡️ **`0003`** — cross-class supersession; unfiltered today", "tracked as 0003 I1/I2"),
 ("src/veracium/graph.py", "apply_supersession", "add_edge", "1e539a527213"):
   (W, "**`valid_from = min`** on the incoming edge, `observed_at`, `confidence`", "observation",
    "🟡 **R1 — the edge is unpersisted here, so N1 holds narrowly.** Under immutable-identity this becomes construction, not mutation. §7c",
    "`test_valid_from_immutable_across_every_mutation_site`"),
 ("src/veracium/ingest.py", "ingest_event", "add_episode", "aa566aea9649"):
   (W, "episode provenance (unparseable placeholder)", "observation",
    "clean — never retains raw event text", "`test_unparseable_extraction_degrades_gracefully`"),
 ("src/veracium/ingest.py", "ingest_event", "add_episode", "d4047bb84602"):
   (W, "episode provenance", "observation", "clean — the origin of trust", "`test_third_party_text_never_moves_into_the_grounded_block`"),

 # -- maintenance ------------------------------------------------------------
 ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "9b770be5d140"):
   (M, "`active`, reason `lapsed`", "none", "clean — narrows", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "a150aebdecd7"):
   (M, "`active`, reason `decayed`", "none", "clean — narrows", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/lifecycle.py", "expire", "add_edge", "2c0f01cfbcbc"):
   (M, "**`confidence *= decay_factor`**", "none",
    "🔴 **OPEN — external review item 8.** `MemoryConfig` is an unvalidated dataclass; `decay_factor=2.0`, `NaN`, `-1.0` are all accepted, so this site can RAISE confidence and **N4 is false as written**. §7d",
    "🔴 **`specs/0002` N4b–N4d** — `test_config_bounds_are_validated`; **none passes today**"),
 ("src/veracium/lifecycle.py", "expire", "add_edge", "adc9056f44a6"):
   (M, "`needs_confirmation = True`", "none", "clean — narrows; flags, never clears", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/lifecycle.py", "consolidate", "delete_episode", "d24901a8b7ea"):
   (M, "**destroys episodes**", "none",
    "🔴 **OPEN — external review item 9.** Deletes ALL members *before* writing any replacement, so a crash between the loops is total loss. §7e",
    "➡️ **`specs/0010` X1–X6** — `test_no_crash_point_loses_data`; write-before-delete with lineage recovery"),
 ("src/veracium/lifecycle.py", "consolidate", "add_episode", "83dad266cecf"):
   (M, "`author_of_evidence`, `derived_from`, `confidence`", "none",
    "**M1 — fixed 0.4.4** + advisory GHSA-hcj3-8jqc-wqrp. Whole-set minimum trust",
    "`test_consolidation_preserves_and_compresses`"),

 # -- portability ------------------------------------------------------------
 ("src/veracium/portability.py", "import_memory", "add_edge", "1cd414dfc13e"):
   (W, "**every trust field, reconstructed from a file**", "transfer",
    "➡️ **MOVED to `0005`.** No capping on the `user_id` remap", "tracked as 0005 P1–P4"),
 ("src/veracium/portability.py", "import_memory", "add_episode", "741683ddf944"):
   (W, "episode provenance from a file", "transfer", "➡️ moved with M6", "tracked as 0005 P1–P4"),
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
  ("src/veracium/__init__.py", "Memory.confirm", "add_edge", "5b46e2531803"): "fixed",
  ("src/veracium/__init__.py", "Memory.confirm", "add_episode", "bdd949deaa6a"): "clean",
  ("src/veracium/__init__.py", "Memory.record_outcome", "add_episode", "02cff46798fc"): "open_moved",
  ("src/veracium/__init__.py", "Memory.record_outcome", "add_episode", "1b9e2cf47dcf"): "clean",
  ("src/veracium/__init__.py", "Memory.record_outcome", "add_edge", "5b46e2531803"): "clean",
  ("src/veracium/__init__.py", "Memory.correct", "invalidate_edge", "c81beaca32cb"): "moved",
  ("src/veracium/__init__.py", "Memory.correct", "add_edge", "72b03718535b"): "moved",
  ("src/veracium/__init__.py", "Memory.correct", "add_episode", "23255a7f3c3f"): "moved",
  ("src/veracium/__init__.py", "Memory.forget", "forget_user", "c5d9e9e2da39"): "clean",
  ("src/veracium/cli.py", "_forget", "forget_user", "2acc9db31dbe"): "clean",
  ("src/veracium/compile.py", "compile_wiki", "set_wiki", "8add728df9b1"): "moved",
  ("src/veracium/graph.py", "apply_supersession", "add_edge", "b766ab223c71"): "open_moved",
  ("src/veracium/graph.py", "apply_supersession", "add_edge", "509e20030c74"): "clean",
  ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", "5d67f0861b5f"): "clean",
  ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", "ddcab09b4f04"): "moved",
  ("src/veracium/graph.py", "apply_supersession", "add_edge", "1e539a527213"): "clean",
  ("src/veracium/ingest.py", "ingest_event", "add_episode", "aa566aea9649"): "clean",
  ("src/veracium/ingest.py", "ingest_event", "add_episode", "d4047bb84602"): "clean",
  ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "9b770be5d140"): "clean",
  ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "a150aebdecd7"): "clean",
  ("src/veracium/lifecycle.py", "expire", "add_edge", "2c0f01cfbcbc"): "open",
  ("src/veracium/lifecycle.py", "expire", "add_edge", "adc9056f44a6"): "clean",
  ("src/veracium/lifecycle.py", "consolidate", "delete_episode", "d24901a8b7ea"): "open_moved",
  ("src/veracium/lifecycle.py", "consolidate", "add_episode", "83dad266cecf"): "fixed",
  ("src/veracium/portability.py", "import_memory", "add_edge", "1cd414dfc13e"): "moved",
  ("src/veracium/portability.py", "import_memory", "add_episode", "741683ddf944"): "moved",
}
