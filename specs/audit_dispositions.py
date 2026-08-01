"""Per-call-site verdicts for the specs/0002 audit manifest.

Keyed on (file, enclosing def, mutator, nth) so a verdict survives unrelated
edits above it. `audit_manifest.py --check` fails when a site here has no
counterpart in the code, or a site in the code has no entry here.

Columns: operation class | trust fields touched | evidence-bearing? | verdict | test
"""

W, M = "write-time", "maintain-time"
YES, NO = "yes", "**no**"

DISPOSITIONS = {
 # -- explicit user verbs ----------------------------------------------------
 ("src/veracium/__init__.py", "dispute", "invalidate_edge", 1):
   (W, "`active`, `invalidation_reason`", YES, "clean — narrows only", "`test_dispute_retires`"),
 ("src/veracium/__init__.py", "dispute", "add_episode", 1):
   (W, "episode provenance", YES, "clean", "`test_dispute_records_episode`"),
 ("src/veracium/__init__.py", "confirm", "add_edge", 1):
   (W, "`observed_at`, `needs_confirmation`, `confidence`", YES,
    "**M2 — fixed 0.4.5**; return-value sibling **fixed 0.4.6** (`533092c`)",
    "`test_confirm_returns_the_real_valid_from_not_the_confirmation_date`"),
 ("src/veracium/__init__.py", "confirm", "add_episode", 1):
   (W, "episode provenance", YES, "clean", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/__init__.py", "record_outcome", "add_episode", 1):
   (W, "**`author_of_evidence` (overwritten)**", YES,
    "🔴 **M4 — OPEN.** The shipped note survives exactly one upgrade; the structured field is still overwritten. Frozen behaviour specified in §7a.",
    "⚠️ **none passes today** — `test_m4_authorship_history_is_structural` is the amendment's deliverable"),
 ("src/veracium/__init__.py", "record_outcome", "add_episode", 2):
   (W, "episode provenance (new outcome)", YES, "clean — new event, own provenance", "`test_record_outcome_new_episode`"),
 ("src/veracium/__init__.py", "record_outcome", "add_edge", 1):
   (W, "`outcome_counts`, `last_outcome`, `needs_confirmation`", YES,
    "clean — counters are information, never gating", "`test_outcome_counters_do_not_gate`"),
 ("src/veracium/__init__.py", "correct", "invalidate_edge", 1):
   (W, "`active`, `invalidation_reason=corrected`", YES,
    "➡️ **MOVED to `0003` §1b** — this is a supersession path", "tracked as 0003 I9/I10"),
 ("src/veracium/__init__.py", "correct", "add_edge", 1):
   (W, "**`author_of_evidence` hardcoded USER**, `disclosure`, `supersedes`", YES,
    "➡️ **MOVED to `0003` §1b (M7).** Resolved there: inherit the corrected edge's class", "tracked as 0003 I10"),
 ("src/veracium/__init__.py", "correct", "add_episode", 1):
   (W, "episode provenance", YES, "➡️ moved with M7", "tracked as 0003 I10"),
 ("src/veracium/__init__.py", "forget", "forget_user", 1):
   (W, "**all** — irreversible erasure", YES, "clean — erasure is the contract", "`test_forget_erases_everything`"),
 ("src/veracium/cli.py", "_forget", "forget_user", 1):
   (W, "**all**", YES, "clean — same verb through the CLI", "`test_cli_forget`"),

 # -- derived views ----------------------------------------------------------
 ("src/veracium/compile.py", "compile_wiki", "set_wiki", 1):
   (M, "none directly — **caches a trust decision**", NO,
    "➡️ **MOVED to `0004`.** Output outlives the inputs' revocation", "tracked as 0004 W1–W4"),

 # -- the write path ---------------------------------------------------------
 ("src/veracium/graph.py", "apply_supersession", "add_edge", 1):
   (W, "**`needs_confirmation` cleared**, `observed_at`, `confidence`", YES,
    "🔴 **M3 — OPEN.** Same-author-class is not source identity; external review item 3, ruled R2. Fail-closed rule specified in §7b",
    "⚠️ **amendment deliverable** — `test_system_repetition_cannot_clear_staleness`"),
 ("src/veracium/graph.py", "apply_supersession", "add_edge", 2):
   (W, "`note` on the absorbed prior", YES, "clean — annotates, never widens", "`test_absorption_notes_prior`"),
 ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", 1):
   (W, "`active`, reason `absorbed_duplicate`", YES, "clean — narrows", "`test_absorption_retires_prior`"),
 ("src/veracium/graph.py", "apply_supersession", "invalidate_edge", 2):
   (W, "`active`, reason `superseded`", YES,
    "➡️ **`0003`** — cross-class supersession; unfiltered today", "tracked as 0003 I1/I2"),
 ("src/veracium/graph.py", "apply_supersession", "add_edge", 3):
   (W, "**`valid_from = min`** on the incoming edge, `observed_at`, `confidence`", YES,
    "🟡 **R1 — the edge is unpersisted here, so N1 holds narrowly.** Under immutable-identity this becomes construction, not mutation. §7c",
    "`test_valid_from_immutable_across_every_mutation_site`"),
 ("src/veracium/ingest.py", "ingest_event", "add_episode", 1):
   (W, "episode provenance (unparseable placeholder)", YES,
    "clean — never retains raw event text", "`test_unparseable_event_keeps_no_content`"),
 ("src/veracium/ingest.py", "ingest_event", "add_episode", 2):
   (W, "episode provenance", YES, "clean — the origin of trust", "`test_ingest_sets_provenance`"),

 # -- maintenance ------------------------------------------------------------
 ("src/veracium/lifecycle.py", "expire", "invalidate_edge", 1):
   (M, "`active`, reason `lapsed`", NO, "clean — narrows", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/lifecycle.py", "expire", "invalidate_edge", 2):
   (M, "`active`, reason `decayed`", NO, "clean — narrows", "`test_expiry_lapse_confirm_and_reinforcement`"),
 ("src/veracium/lifecycle.py", "expire", "add_edge", 1):
   (M, "**`confidence *= decay_factor`**", NO,
    "🔴 **OPEN — external review item 8.** `MemoryConfig` is an unvalidated dataclass; `decay_factor=2.0`, `NaN`, `-1.0` are all accepted, so this site can RAISE confidence and **N4 is false as written**. §7d",
    "⚠️ **amendment deliverable** — `test_decay_factor_bounds_are_validated`"),
 ("src/veracium/lifecycle.py", "expire", "add_edge", 2):
   (M, "`needs_confirmation = True`", NO, "clean — narrows; flags, never clears", "`test_confirm_behavior_flags_stale`"),
 ("src/veracium/lifecycle.py", "consolidate", "delete_episode", 1):
   (M, "**destroys episodes**", NO,
    "🔴 **OPEN — external review item 9.** Deletes ALL members *before* writing any replacement, so a crash between the loops is total loss. §7e",
    "⚠️ **amendment deliverable** — `test_consolidation_is_crash_safe`"),
 ("src/veracium/lifecycle.py", "consolidate", "add_episode", 1):
   (M, "`author_of_evidence`, `derived_from`, `confidence`", NO,
    "**M1 — fixed 0.4.4** + advisory GHSA-hcj3-8jqc-wqrp. Whole-set minimum trust",
    "`test_consolidation_uses_whole_set_min_trust`"),

 # -- portability ------------------------------------------------------------
 ("src/veracium/portability.py", "import_memory", "add_edge", 1):
   (W, "**every trust field, reconstructed from a file**", NO,
    "➡️ **MOVED to `0005`.** No capping on the `user_id` remap", "tracked as 0005 P1–P4"),
 ("src/veracium/portability.py", "import_memory", "add_episode", 1):
   (W, "episode provenance from a file", NO, "➡️ moved with M6", "tracked as 0005 P1–P4"),
}
