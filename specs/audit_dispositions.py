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
YES, NO = "yes", "**no**"

DISPOSITIONS = {
 # -- explicit user verbs ----------------------------------------------------
 ("src/veracium/__init__.py", "Memory.dispute", "invalidate_edge", "54a5750e"):
   (W, "`active`, `invalidation_reason`", YES, "clean — narrows only", "`test_dispute_removes_from_assertable_but_keeps_history`"),
 ("src/veracium/__init__.py", "Memory.dispute", "add_episode", "9338b7b2"):
   (W, "episode provenance", YES, "clean", "`test_dispute_removes_from_assertable_but_keeps_history`"),
 ("src/veracium/__init__.py", "Memory.confirm", "add_edge", "c53a7a18"):
   (W, "`observed_at`, `needs_confirmation`, `confidence`", YES,
    "**M2 — fixed 0.4.5**; return-value sibling **fixed 0.4.6** (`533092c`)",
    "`test_confirm_returns_the_real_valid_from_not_the_confirmation_date`"),
 ("src/veracium/__init__.py", "Memory.confirm", "add_episode", "5a570fd8"):
   (W, "episode provenance", YES, "clean", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/__init__.py", "Memory.record_outcome", "add_episode", "9c113bc7"):
   (W, "**`author_of_evidence` (overwritten)**", YES,
    "🔴 **M4 — OPEN.** The shipped note survives exactly one upgrade; the structured field is still overwritten. Frozen behaviour specified in **`specs/0009`** §4.",
    "➡️ **`specs/0009` H1–H7** — `test_outcome_authorship_is_never_overwritten`; **none passes today**"),
 ("src/veracium/__init__.py", "Memory.record_outcome", "add_episode", "d9bfbcfe"):
   (W, "episode provenance (new outcome)", YES, "clean — new event, own provenance", "`test_record_outcome_is_edge_blind_never_supersedes`"),
 ("src/veracium/__init__.py", "Memory.record_outcome", "add_edge", "c53a7a18"):
   (W, "`outcome_counts`, `last_outcome`, `needs_confirmation`", YES,
    "clean — counters are information, never gating", "`test_record_outcome_is_edge_blind_never_supersedes`"),
 ("src/veracium/__init__.py", "Memory.correct", "invalidate_edge", "4a35ac8e"):
   (W, "`active`, `invalidation_reason=corrected`", YES,
    "➡️ **MOVED to `0003` §1b** — this is a supersession path", "tracked as 0003 I9/I10"),
 ("src/veracium/__init__.py", "Memory.correct", "add_edge", "167822d2"):
   (W, "**`author_of_evidence` hardcoded USER**, `disclosure`, `supersedes`", YES,
    "➡️ **MOVED to `0003` §1b (M7).** Resolved there: inherit the corrected edge's class", "tracked as 0003 I10"),
 ("src/veracium/__init__.py", "Memory.correct", "add_episode", "2de17d4a"):
   (W, "episode provenance", YES, "➡️ moved with M7", "tracked as 0003 I10"),
 ("src/veracium/__init__.py", "Memory.forget", "forget_user", "52dd0187"):
   (W, "**all** — irreversible erasure", YES, "clean — erasure is the contract", "`test_forget_erases_everything`"),
 ("src/veracium/cli.py", "_forget", "forget_user", "8b238d08"):
   (W, "**all**", YES, "clean — same verb through the CLI", "`test_forget_cli_requires_confirmation`"),

 # -- derived views ----------------------------------------------------------
 ("src/veracium/compile.py", "compile_wiki", "set_wiki", "fba624c6"):
   (M, "none directly — **caches a trust decision**", NO,
    "➡️ **MOVED to `0004`.** Output outlives the inputs' revocation", "tracked as 0004 W1–W4"),

 # -- the write path ---------------------------------------------------------
 ("src/veracium/graph.py", "apply_supersession", "add_edge", "783729d3"):
   (W, "**`needs_confirmation` cleared**, `observed_at`, `confidence`", YES,
    "🔴 **M3 — OPEN.** Same-author-class is not source identity; external review item 3, ruled R2. Fail-closed rule specified in §7b",
    "➡️ **`specs/0008` C1–C6** — `test_no_author_value_clears_staleness`; **none passes today**"),
 ("src/veracium/graph.py", "apply_supersession", "add_edge", "12a98f5c"):
   (W, "`note` on the absorbed prior", YES, "clean — annotates, never widens", "`test_absorbed_edges_never_render_as_history`"),
 ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", "aa33f564"):
   (W, "`active`, reason `absorbed_duplicate`", YES, "clean — narrows", "`test_more_specific_arrival_absorbs_prior`"),
 ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", "7afc65ea"):
   (W, "`active`, reason `superseded`", YES,
    "➡️ **`0003`** — cross-class supersession; unfiltered today", "tracked as 0003 I1/I2"),
 ("src/veracium/graph.py", "apply_supersession", "add_edge", "9daa6f13"):
   (W, "**`valid_from = min`** on the incoming edge, `observed_at`, `confidence`", YES,
    "🟡 **R1 — the edge is unpersisted here, so N1 holds narrowly.** Under immutable-identity this becomes construction, not mutation. §7c",
    "`test_valid_from_immutable_across_every_mutation_site`"),
 ("src/veracium/ingest.py", "ingest_event", "add_episode", "b192a5b4"):
   (W, "episode provenance (unparseable placeholder)", YES,
    "clean — never retains raw event text", "`test_unparseable_extraction_degrades_gracefully`"),
 ("src/veracium/ingest.py", "ingest_event", "add_episode", "d96093f6"):
   (W, "episode provenance", YES, "clean — the origin of trust", "`test_third_party_text_never_moves_into_the_grounded_block`"),

 # -- maintenance ------------------------------------------------------------
 ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "426f5be3"):
   (M, "`active`, reason `lapsed`", NO, "clean — narrows", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/lifecycle.py", "expire", "invalidate_edge", "e51de441"):
   (M, "`active`, reason `decayed`", NO, "clean — narrows", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/lifecycle.py", "expire", "add_edge", "ddad502b"):
   (M, "**`confidence *= decay_factor`**", NO,
    "🔴 **OPEN — external review item 8.** `MemoryConfig` is an unvalidated dataclass; `decay_factor=2.0`, `NaN`, `-1.0` are all accepted, so this site can RAISE confidence and **N4 is false as written**. §7d",
    "🔴 **`specs/0002` N4b–N4d** — `test_config_bounds_are_validated`; **none passes today**"),
 ("src/veracium/lifecycle.py", "expire", "add_edge", "41de0885"):
   (M, "`needs_confirmation = True`", NO, "clean — narrows; flags, never clears", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/lifecycle.py", "consolidate", "delete_episode", "41eb6c4d"):
   (M, "**destroys episodes**", NO,
    "🔴 **OPEN — external review item 9.** Deletes ALL members *before* writing any replacement, so a crash between the loops is total loss. §7e",
    "➡️ **`specs/0010` X1–X6** — `test_no_crash_point_loses_data`; write-before-delete with lineage recovery"),
 ("src/veracium/lifecycle.py", "consolidate", "add_episode", "346796a6"):
   (M, "`author_of_evidence`, `derived_from`, `confidence`", NO,
    "**M1 — fixed 0.4.4** + advisory GHSA-hcj3-8jqc-wqrp. Whole-set minimum trust",
    "`test_consolidation_preserves_and_compresses`"),

 # -- portability ------------------------------------------------------------
 ("src/veracium/portability.py", "import_memory", "add_edge", "55f785f8"):
   (W, "**every trust field, reconstructed from a file**", NO,
    "➡️ **MOVED to `0005`.** No capping on the `user_id` remap", "tracked as 0005 P1–P4"),
 ("src/veracium/portability.py", "import_memory", "add_episode", "bc6e49f6"):
   (W, "episode provenance from a file", NO, "➡️ moved with M6", "tracked as 0005 P1–P4"),
}
