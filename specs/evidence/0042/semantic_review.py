"""specs/0042 Part A-0-bis — THE SEMANTIC REVIEW: one decision for every DISCOVERED candidate, AUTHORED
by dev on 2026-09-19 from specs/evidence/0042/decision_site_inventory_OUTPUT.json read site by site.

`E` maps a candidate (module, line) to (site_id, governing spec, invariant/section, decision label) for
every candidate that IS an enforcement point: a site that can return a decision other than the
caller's request (refuse, quarantine, withhold, abstain, downgrade) enforcing a spec's stated
guarantee at a product boundary. Everything else takes a NOT decision with a reason class — the
module DEFAULT, or a per-line OVERRIDE where the default is not the truth for that line:
  argument-check      the caller's input is malformed (type, shape, range, closed parameter vocabulary)
  internal-invariant  a validator of the product's own contracts (carriers, ledgers, registries, package)
  predicate-helper    a Boolean/None helper whose CONSUMER makes the decision
  control-flow        lookups returning None for absent rows, early returns, re-raise after logging,
                      filters by non-policy criteria, budget/shape plumbing
  cli-usage           usage/exit handling of the command line

THE KEYS ARE DERIVED, NOT MAINTAINED (2026-09-19): the enforcement keys of every instrumented id are
rebuilt from the source by specs/evidence/0042/derive_keys.py (every `fire()`-wrapped candidate binds its
statement to its id), and the OVERRIDE keys are re-keyed by (module, qualname, kind, ordinal) in ONE hop
from the plan-time literal (override_at_plan.py) — after a sequential re-key had drifted two keys onto
neighbouring statements while every test stayed green. reviewed_points.json and declaration.py are
GENERATED from this module and the inventory; a change of judgement is made HERE.

Review corrections recorded: `_src_revoked` and `_is_variant` each bind ONE id — their `return False`
exits are the non-declining branch of one decision (`declines=True`), not enforcement points of their
own (found by touching, tranche 3); research's structural sweep over the whole review then found no
further instance (seven functions with more than one id on non-raising exits, each a set of distinct
declining reasons — the frozen allow-list lives in tests/test_0042_reconciliation.py).
"""

E = {}
def e(module, line, site_id, spec, inv, label): E[(module, line)] = (site_id, spec, inv, label)

# ---- __init__.py (Memory: the public surface) ----
# ---- asof/ ----
# ---- authority / grounding / compile / gate / schema ----
# ---- graph.py ----
# ---- ingest.py ----
# ---- mcp_server.py / procedures.py / procedural_gate.py / proactive.py / registry.py ----
# ---- portability.py (the import/export boundary) ----
# ---- scope.py / scope_linkage.py / scope_read.py ----
# ---- store/ ----
# ---- telemetry / diagnostics (0015 consent) ----


# ---- NOT decisions: module defaults + per-line overrides ----
DEFAULT = {
    "__init__.py": "argument-check", "_json.py": "control-flow", "agreement.py": "internal-invariant",
    "asof/adapter.py": "predicate-helper", "asof/classify.py": "predicate-helper", "asof/recall.py": "predicate-helper",
    "asof/resolve.py": "argument-check", "authority.py": "predicate-helper", "budgets.py": "argument-check",
    "cli.py": "cli-usage", "compile.py": "control-flow", "config.py": "argument-check", "contribution.py": "internal-invariant",
    "diagnostics.py": "control-flow", "doctor.py": "control-flow", "dryrun.py": "control-flow", "gate.py": "predicate-helper",
    "graph.py": "control-flow", "grounding.py": "predicate-helper", "ingest.py": "argument-check", "introspect.py": "argument-check",
    "lifecycle.py": "argument-check", "llm/anthropic.py": "internal-invariant", "llm/metered.py": "predicate-helper",
    "mcp_server.py": "cli-usage", "portability.py": "control-flow", "proactive.py": "argument-check",
    "procedural_gate.py": "predicate-helper", "procedures.py": "argument-check", "registry.py": "argument-check",
    "redaction.py": "predicate-helper",      # 0041 tranche 1: carries_marker / marker_fields — consumed by the upsert and add_episode sites
    "contention.py": "predicate-helper",     # 0044 §4d (T5): is_live_refusal — consumed by recall's contested groups and the compiler's grounded-inputs site
    "attest_v3.py": "predicate-helper",      # 0045 §4a (T9): ATTEST-3, vendored byte-identical — its returns are the predicate's own verdict, consumed by attestation.attestation
    "attestation.py": "predicate-helper",    # 0045 §2/§4c (T9): the (att, attv) derivation, the attv grammar and g(e) — consumed by ingest's write, the Edge validator and confirm's guard
    "attest_turns.py": "predicate-helper",   # 0051 §4/§4a: ATTEST-6 (ATTEST-5 until R-II round 2), frozen — the turn grammar and the conjunction; its returns are the predicate's own verdict, consumed by attestation.attestation and speaker_backstop
    "speaker_backstop.py": "predicate-helper",   # 0051 §4b: the speaker-turn backstop's test — consumed by ingest's write (the triple's disclosure)
    "store/lifetime.py": "predicate-helper",  # 0044 §4f-ii (T5): the lifetime transition — consumed by the choke point's effects and the v16 step
    "store/data_migration.py": "internal-invariant",  # 0018 §4i (T6): run_data_migration's refusals are rows of its closed result carrier, release_migration's precedent
    "schema.py": "argument-check", "scope.py": "argument-check", "scope_linkage.py": "internal-invariant",
    "scope_read.py": "control-flow", "semantic.py": "internal-invariant", "source_identity.py": "control-flow",
    "store/base.py": "internal-invariant", "store/current_state.py": "internal-invariant", "store/migration.py": "internal-invariant",
    "store/release_migration.py": "internal-invariant", "store/revocation.py": "internal-invariant",
    "store/revocation_sweep.py": "internal-invariant", "store/schema_version.py": "internal-invariant",
    "store/sqlite.py": "internal-invariant", "telemetry.py": "control-flow", "census.py": "internal-invariant",
    # specs/0053: the framework adapters carry the library's decisions and make none. A binding's refusal is the caller's
    # malformed input (a user id, a tool name); langchain.py's raises are an optional extra's import and the re-raise of
    # a library error as the framework's tool error, and its one list return builds the tools, filtering nothing
    "adapters/_surface.py": "argument-check", "adapters/langchain.py": "control-flow",
    "adapters/pydantic_ai.py": "control-flow",   # the same two raises (the extra's import, the tool-error re-raise) and list return
    "store/near_misses.py": "internal-invariant",  # 0007 §4g.6 4b (I3): head_variant refuses a near-miss whose anchor moved; runtime_status() reads that escape as `refused`, so it is not an enforcement point of its own
}
OVERRIDE = {  # (module, line) -> reason class, where the module default is not the truth for that line
    ("__init__.py", 403): "control-flow", ("__init__.py", 484): "control-flow", ("__init__.py", 621): "control-flow",
    ("__init__.py", 948): "control-flow", ("__init__.py", 1603): "control-flow", ("__init__.py", 1744): "control-flow",
    ("__init__.py", 1766): "control-flow", ("__init__.py", 1815): "control-flow", ("__init__.py", 1822): "control-flow",
    ("__init__.py", 1833): "control-flow", ("__init__.py", 1840): "control-flow", ("__init__.py", 1869): "control-flow",
    ("__init__.py", 1895): "control-flow", ("__init__.py", 2279): "internal-invariant", ("__init__.py", 2432): "control-flow",
    ("__init__.py", 305): "internal-invariant", ("__init__.py", 312): "internal-invariant",
    ("__init__.py", 1032): "internal-invariant", ("__init__.py", 1036): "internal-invariant", ("__init__.py", 1040): "internal-invariant",
    ("__init__.py", 1047): "internal-invariant", ("__init__.py", 1049): "internal-invariant",
    ("agreement.py", 219): "predicate-helper", ("agreement.py", 267): "control-flow", ("agreement.py", 487): "control-flow",
    ("asof/adapter.py", 54): "internal-invariant", ("asof/resolve.py", 117): "internal-invariant", ("asof/resolve.py", 122): "internal-invariant",
    ("asof/resolve.py", 181): "control-flow", ("asof/resolve.py", 206): "predicate-helper",
    ("compile.py", 228): "predicate-helper", ("diagnostics.py", 216): "predicate-helper", ("diagnostics.py", 249): "predicate-helper",
    ("doctor.py", 502): "predicate-helper", ("dryrun.py", 68): "predicate-helper",
    ("graph.py", 60): "predicate-helper", ("graph.py", 75): "predicate-helper", ("graph.py", 241): "internal-invariant",
    ("graph.py", 922): "argument-check", ("grounding.py", 154): "control-flow",
    ("ingest.py", 183): "control-flow", ("ingest.py", 135): "argument-check",
    ("lifecycle.py", 196): "control-flow", ("lifecycle.py", 342): "control-flow",
    ("portability.py", 1017): "control-flow",
    ("procedural_gate.py", 49): "argument-check", ("procedures.py", 104): "control-flow", ("procedures.py", 369): "control-flow",
    ("scope.py", 189): "predicate-helper", ("scope.py", 229): "internal-invariant", ("scope.py", 232): "internal-invariant",
    ("scope.py", 234): "internal-invariant", ("scope.py", 387): "predicate-helper", ("scope.py", 596): "control-flow", ("scope.py", 690): "control-flow",
    ("scope_linkage.py", 115): "control-flow", ("scope_linkage.py", 126): "control-flow", ("scope_linkage.py", 510): "predicate-helper",
    ("scope_linkage.py", 511): "predicate-helper", ("scope_linkage.py", 532): "control-flow",
    ("schema.py", 65): "control-flow", ("schema.py", 281): "predicate-helper", ("schema.py", 288): "predicate-helper",
    ("schema.py", 370): "predicate-helper", ("schema.py", 598): "predicate-helper", ("schema.py", 743): "internal-invariant",
    ("schema.py", 748): "internal-invariant", ("schema.py", 771): "internal-invariant", ("schema.py", 776): "internal-invariant",
    ("schema.py", 817): "predicate-helper", ("schema.py", 926): "predicate-helper", ("schema.py", 357): "internal-invariant", ("schema.py", 812): "internal-invariant",
    ("store/sqlite.py", 359): "control-flow", ("store/sqlite.py", 436): "control-flow", ("store/sqlite.py", 539): "control-flow",
    ("store/sqlite.py", 635): "control-flow", ("store/sqlite.py", 718): "control-flow", ("store/sqlite.py", 1099): "control-flow",
    ("store/sqlite.py", 1429): "control-flow", ("store/sqlite.py", 1471): "control-flow", ("store/sqlite.py", 1540): "control-flow",
    ("store/sqlite.py", 1554): "predicate-helper", ("store/sqlite.py", 1760): "control-flow", ("store/sqlite.py", 3165): "control-flow",
    ("store/sqlite.py", 3196): "control-flow", ("store/sqlite.py", 3205): "predicate-helper", ("store/sqlite.py", 341): "argument-check",
    ("store/sqlite.py", 614): "argument-check", ("store/sqlite.py", 3281): "argument-check", ("store/sqlite.py", 4165): "argument-check",
    ("store/sqlite.py", 4180): "argument-check", ("store/sqlite.py", 609): "control-flow", ("store/sqlite.py", 1422): "control-flow",
    ("store/sqlite.py", 2058): "control-flow", ("store/sqlite.py", 2334): "control-flow", ("store/sqlite.py", 2348): "control-flow",
    ("store/sqlite.py", 2363): "control-flow", ("store/sqlite.py", 3514): "control-flow", ("store/sqlite.py", 3536): "control-flow",
    ("store/sqlite.py", 4183): "control-flow", ("store/sqlite.py", 3254): "argument-check",
    ("store/revocation.py", 56): "predicate-helper", ("store/revocation.py", 110): "control-flow", ("store/revocation.py", 145): "control-flow",
    ("store/revocation_sweep.py", 172): "control-flow", ("store/revocation_sweep.py", 192): "control-flow",
    ("store/schema_version.py", 1987): "argument-check", ("store/schema_version.py", 2179): "control-flow",
    ("telemetry.py", 466): "control-flow", ("telemetry.py", 487): "control-flow", ("telemetry.py", 514): "control-flow",
    ("mcp_server.py", 578): "cli-usage", ("mcp_server.py", 584): "cli-usage", ("mcp_server.py", 588): "cli-usage", ("mcp_server.py", 600): "cli-usage",
    ("source_identity.py", 59): "argument-check", ("_json.py", 43): "control-flow", ("introspect.py", 54): "argument-check",
    ("__init__.py", 2351): "internal-invariant",   # carried: __init__.py:Memory.source_revocations:RAISE:1
    ("__init__.py", 2361): "internal-invariant",   # specs/0022 §4g: a store without revocation support refuses, the Store base's refusing-default class
    ("adapters/_surface.py", 41): "internal-invariant",   # specs/0053: _registered:RAISE:1, the MCP server exposes no tool manager
    ("adapters/_surface.py", 45): "internal-invariant",   # specs/0053: _registered:RAISE:2, the served tools differ from the ones bound
    ("adapters/pydantic_ai.py", 62): "argument-check",   # specs/0053: as_tools:RAISE:1, a max_retries that is not a non-negative int
    ("compile.py", 241): "predicate-helper",   # SR2-01: the cached code-owned empty body test, consumed by needs_recompile
    ("compile.py", 459): "predicate-helper",   # carried: compile.py:_unbound_by:RETURN_NONE:1
    ("lifecycle.py", 63): "internal-invariant",   # specs/0048 §4D, the owner's "Refuse, name it": a store without the transition refuses (the Store base's refusing-default class)
    ("proactive.py", 242): "control-flow",   # 0003/obligations N1–N4 (NEW 1): proactive.py:assemble._commit_line:RETURN_NONE:1, a line that cannot fit its cap is dropped (budget plumbing)
    ("proactive.py", 291): "control-flow",   # 0003/obligations N1–N4 (N1): proactive.py:assemble._contested_line:RETURN_NONE:1, a group line that cannot hold one slot is dropped (budget plumbing)
    ("schema.py", 625): "predicate-helper",   # 0.29.0 B1+B2: schema.py:is_obligation:BOOL_RETURN:1 (consumed by the backstop and _lexical_scored)
    ("schema.py", 679): "predicate-helper",   # carried: schema.py:wiki_drops_on:BOOL_RETURN:1
    ("schema.py", 706): "predicate-helper",   # RII-R2-01: schema.py:assertion_view:RETURN_NONE:1
    ("schema.py", 1471): "internal-invariant",   # RII-R2-01: schema.py:_check_assertion_view_partition:RAISE:1
    ("store/migration.py", 825): "control-flow",   # carried: store/migration.py:preimage_fields:FILTER_RETURN:1
    ("store/release_migration.py", 936): "predicate-helper",   # carried: store/release_migration.py:_mintable_base:RETURN_NONE:1
    ("store/release_migration.py", 1571): "argument-check",   # carried: store/release_migration.py:_record_row:RAISE:1
    ("store/release_migration.py", 1578): "predicate-helper",   # carried: store/release_migration.py:_readback_is_bound:BOOL_RETURN:1
    ("store/release_migration.py", 1621): "argument-check",   # carried: store/release_migration.py:classify_recovery:RAISE:1
    ("store/release_migration.py", 1711): "control-flow",   # carried: store/release_migration.py:run_release_rung:RAISE:3
    ("store/schema_version.py", 1989): "argument-check",   # carried: store/schema_version.py:open_versioned:RAISE:2
    ("store/schema_version.py", 1991): "argument-check",   # carried: store/schema_version.py:open_versioned:RAISE:3
    ("store/schema_version.py", 1993): "argument-check",   # carried: store/schema_version.py:open_versioned:RAISE:4
    ("store/schema_version.py", 2000): "argument-check",   # carried: store/schema_version.py:open_versioned:RAISE:5
}
REASON_TEXT = {
    "argument-check": "not an enforcement point: the caller's input is malformed (type, shape, range or closed parameter vocabulary); the request is refused as ill-formed, not declined on trust or policy",
    "internal-invariant": "not an enforcement point: a validator of the product's own contract (a carrier, ledger, registry, audit record or package consistency), never a decision about a caller's request",
    "predicate-helper": "not an enforcement point: a Boolean/None helper whose consumer takes the decision",
    "control-flow": "not an enforcement point: a lookup returning None for an absent row, an early return, a re-raise after logging, a filter by a non-policy criterion or budget/shape plumbing",
    "cli-usage": "not an enforcement point: command-line usage and exit handling",
}


# THE PREDICATE-HELPER REASON'S SUBJECT (research's second read of the NOT half, 2026-09-19): the generator
# derives each helper's consumers from the source and names them in the reason. For a helper NO product
# function references, the review states the consumer by hand here; a helper with neither REFUSES generation.
CONSUMED_OUTSIDE = {
    "llm/metered.py:Metered.totals": "a public read of the meter (the host and tests); the product never branches on it",
    "schema.py:EvidenceContext.__eq__": "the language's == operator (record equality); no product decision consumes it",
    "schema.py:SuccessorLookup.__eq__": "the language's == operator (record equality); no product decision consumes it",
    "scope.py:same_identity": "exported in scope's __all__ for the 0020 vector harness and tests; no product function calls it",
    "attest_turns.py:only_in_non_user_turns": "ATTEST-4's backstop matcher, carried in ATTEST-5's and ATTEST-6's FROZEN bytes and unused by design (0051 §4b: the product backstop is speaker_backstop.py); read only by research's H3/H4 scoring and the 0051 tests",
}

# specs/0041 tranche 1 (2026-09-19): INV-11's mirror, the relation-only quarantine, the kind closure

# specs/0041 tranche 3 (2026-09-19): the operation's refusals and INV-11 at the two whole-record writers

# T7 (0044 §4i undo; research's T7 stage-1 classification f8ec28ed: every one an enforcement point that refuses)

# ---- DERIVED from the instrumented source (derive_keys.py): every fire()-wrapped candidate ----
e("asof/adapter.py", 160, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 162, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 165, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 168, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 173, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 179, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 182, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 184, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 187, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 189, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 193, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 196, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 198, "asof.adapter.adapt.refuse", "0030", "V-EXTRACT", "refuse")
e("asof/adapter.py", 100, "asof.adapter.derive-quarantined", "0030", "V-CARRIER-AGREES", "quarantine")
e("asof/adapter.py", 108, "asof.adapter.derive-use-only", "0030", "V-CARRIER-AGREES", "withhold")
e("asof/classify.py", 181, "asof.classify.assertable-as-of", "0028", "§4b", "withhold")
e("asof/recall.py", 48, "asof.recall.claim", "0028", "§4b", "withhold")
e("asof/recall.py", 43, "asof.recall.grounded", "0028", "§4b", "withhold")
e("asof/resolve.py", 328, "asof.resolve.edge-hidden-or-invalid", "0028", "§4b", "withhold")
e("asof/resolve.py", 320, "asof.resolve.edge-unclassified", "0028", "§4b", "withhold")
e("asof/resolve.py", 272, "asof.resolve.future-T", "0028", "§2c-i", "refuse")
e("asof/resolve.py", 245, "asof.resolve.held-at", "0028", "§2c-i", "withhold")
e("authority.py", 76, "authority.permitted", "0003", "§4a", "refuse")
e("authority.py", 89, "authority.self-assertion", "0003", "§4a", "withhold")
e("compile.py", 469, "compile.bind.unbound", "0047", "§4d INV-R18 (R-II round 2's RII-01: recall serves no wiki body its own snapshot does not admit)", "withhold")
e("compile.py", 155, "compile.fence.disputed", "0047", "§4d INV-R18 (the in-flight fence withholds a body drawn on a fact challenged since)", "withhold")
e("compile.py", 207, "compile.grounded-inputs", "0004", "§4", "withhold")
e("diagnostics.py", 276, "diagnostics.send.not-consented", "0015", "§4", "withhold")
e("gate.py", 54, "gate.exclude-procedural", "0037", "V-EXTRACTOR-QUOTE-GATED", "withhold")
e("gate.py", 178, "gate.partition-parts", "0001", "§4", "withhold")
e("gate.py", 125, "gate.scoped-assertable.entitlement", "0011", "§4c", "withhold")
e("gate.py", 119, "gate.scoped-assertable.invisible", "0020", "§4a", "withhold")
e("gate.py", 122, "gate.scoped-assertable.third-party-shaped", "0020", "§4a", "withhold")
e("graph.py", 300, "graph.absorption.cross-scope", "0020", "§4a-iii", "withhold")
e("graph.py", 302, "graph.absorption.no-flattening-plan", "0021", "§4a", "withhold")
e("graph.py", 297, "graph.absorption.scope-unresolved", "0020", "§4a-iii", "withhold")
e("graph.py", 1390, "graph.collapse-for-render", "0012", "§4c", "withhold")
e("graph.py", 1315, "graph.collapse.acted", "0047", "§4e (collapse never hides a member carrying an act, nor one behind a withheld survivor)", "withhold")
e("graph.py", 368, "graph.correction.identity-mismatch", "0011", "§4b", "refuse")
e("graph.py", 380, "graph.correction.prior-not-active", "0011", "§4b", "refuse")
e("graph.py", 861, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 867, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 869, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 871, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 873, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 875, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 439, "graph.src-revoked", "0022", "§4a", "withhold")
e("graph.py", 443, "graph.src-revoked", "0022", "§4a", "withhold")
e("graph.py", 1233, "graph.strictly-redundant", "0012", "§4c", "withhold")
e("graph.py", 194, "graph.supersession.receipt-boundary", "0014", "R10", "refuse")
e("graph.py", 220, "graph.supersession.replay-mismatch", "0014", "§4b", "refuse")
e("grounding.py", 243, "grounding.ungrounded", "0019", "§4", "downgrade")
e("ingest.py", 317, "ingest.basis-via-remember", "0037", "§4b", "refuse")
e("ingest.py", 378, "ingest.instructions-not-a-list", "0039", "§2a", "downgrade")
e("ingest.py", 306, "ingest.source-id-required", "0006", "§4 rule 9", "refuse")
e("mcp_server.py", 113, "mcp.closed-set.author", "0011", "§4d", "refuse")
e("mcp_server.py", 122, "mcp.closed-set.trust-field", "0011", "§4d", "refuse")
e("__init__.py", 1997, "memory.confirm.unknown-target", "0008", "§6c INV-Q2", "refuse")
e("__init__.py", 2230, "memory.correct.inactive-edge", "0011", "§4b", "refuse")
e("__init__.py", 2250, "memory.correct.procedural", "0037", "§4a-iii", "refuse")
e("__init__.py", 2296, "memory.correct.refused", "0011", "§4b", "refuse")
e("__init__.py", 1934, "memory.dispute.inactive-edge", "0003", "§4b", "refuse")
e("__init__.py", 1915, "memory.edge.unknown-target", "0041", "INV-5", "refuse")
e("__init__.py", 1906, "memory.feedback.attested-target", "0041", "§4b-ii INV-11 (derived episodes)", "refuse")
e("__init__.py", 932, "memory.recall.as-of-on-proactive", "0028", "§2c", "refuse")
e("__init__.py", 1057, "memory.recall.policy-with-as-of", "0027", "v13 §4c", "refuse")
e("__init__.py", 2106, "memory.record-outcome.actor-vocabulary", "0008", "§4", "refuse")
e("__init__.py", 2109, "memory.record-outcome.human-judgment", "0008", "§4", "refuse")
e("__init__.py", 2112, "memory.record-outcome.system-judgment", "0008", "§4", "refuse")
e("__init__.py", 408, "memory.scope.local-origin-missing", "0006", "I9", "refuse")
e("portability.py", 494, "portability.export.non-quiescent", "0010", "X-quiesce", "refuse")
e("portability.py", 1810, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1815, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1821, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1826, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1832, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1860, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1866, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1895, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1909, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1921, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1925, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1938, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1943, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 328, "portability.import.act-records", "0008", "§6e", "refuse")
e("portability.py", 357, "portability.import.act-records", "0008", "§6e", "refuse")
e("portability.py", 369, "portability.import.act-records", "0008", "§6e", "refuse")
e("portability.py", 1310, "portability.import.agreement-invalid", "0025", "§4c", "refuse")
e("portability.py", 1720, "portability.import.arity-preflight", "0044", "§4l", "refuse")
e("portability.py", 1727, "portability.import.arity-preflight", "0044", "§4l", "refuse")
e("portability.py", 1741, "portability.import.arity-preflight", "0044", "§4l", "refuse")
e("portability.py", 183, "portability.import.arity-records", "0044", "§4l", "refuse")
e("portability.py", 188, "portability.import.arity-records", "0044", "§4l", "refuse")
e("portability.py", 213, "portability.import.arity-records", "0044", "§4l", "refuse")
e("portability.py", 220, "portability.import.arity-records", "0044", "§4l", "refuse")
e("portability.py", 255, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 263, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 267, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 273, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 279, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 283, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 422, "portability.import.axis", "0045", "§2c", "refuse")
e("portability.py", 735, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 739, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 748, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 752, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 756, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 761, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 768, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 773, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 824, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 827, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 830, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 859, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 873, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 884, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 896, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 903, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 911, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 1400, "portability.import.origin-missing", "0006", "§4", "refuse")
e("portability.py", 2002, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2006, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2017, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2032, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2036, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2059, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2068, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2072, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2080, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2099, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 1655, "portability.import.race-exhausted", "0009", "§4c", "refuse")
e("portability.py", 1456, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1467, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1474, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1483, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1500, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1506, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1510, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1518, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1547, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1599, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 809, "portability.import.restore-not-bool", "0005", "P13", "refuse")
e("portability.py", 814, "portability.import.restore-with-user", "0005", "P5", "refuse")
e("proactive.py", 183, "proactive.eligible", "0012", "§4", "withhold")
e("proactive.py", 111, "proactive.variant", "0012", "I8j", "withhold")
e("proactive.py", 115, "proactive.variant", "0012", "I8j", "withhold")
e("procedural_gate.py", 203, "procedural-gate.actor-present", "0037", "Gate 3", "refuse")
e("procedural_gate.py", 205, "procedural-gate.actor-present", "0037", "Gate 3", "refuse")
e("procedural_gate.py", 207, "procedural-gate.actor-present", "0037", "Gate 3", "refuse")
e("procedural_gate.py", 212, "procedural-gate.actor-present", "0037", "Gate 3", "refuse")
e("procedural_gate.py", 214, "procedural-gate.actor-present", "0037", "Gate 3", "refuse")
e("procedural_gate.py", 217, "procedural-gate.actor-present", "0037", "Gate 3", "refuse")
e("procedural_gate.py", 185, "procedural-gate.positive-form", "0037", "Gate 3", "refuse")
e("procedural_gate.py", 188, "procedural-gate.positive-form", "0037", "Gate 3", "refuse")
e("procedural_gate.py", 190, "procedural-gate.positive-form", "0037", "Gate 3", "refuse")
e("procedural_gate.py", 192, "procedural-gate.positive-form", "0037", "Gate 3", "refuse")
e("procedural_gate.py", 193, "procedural-gate.positive-form", "0037", "Gate 3", "refuse")
e("procedures.py", 165, "procedures.source-id-required", "0006", "§4 rule 9", "refuse")
e("challenge.py", 85, "read.challenge.twin", "0047", "§4c INV-R3, the owner's F7 ruling (a same-value twin of a challenged record is withheld)", "withhold")
e("challenge.py", 87, "read.challenge.twin", "0047", "§4c INV-R3, the owner's F7 ruling (a same-value twin of a challenged record is withheld)", "withhold")
e("challenge.py", 108, "read.challenge.withheld", "0047", "§4c–§4d INV-R3, R12 (a challenged fact reaches no assertion surface)", "withhold")
e("registry.py", 78, "registry.arity-refused", "0044", "§2c INV-A3/A10", "refuse")
e("registry.py", 82, "registry.arity-refused", "0044", "§2c INV-A3/A10", "refuse")
e("registry.py", 85, "registry.arity-refused", "0044", "§2c INV-A3/A10", "refuse")
e("registry.py", 91, "registry.empty-refused", "0025", "§4b-iv X5", "refuse")
e("registry.py", 101, "registry.reserved-shadowed", "0025", "§4b-iv", "refuse")
e("schema.py", 996, "schema.edge.assertable", "0001", "§4", "withhold")
e("schema.py", 942, "schema.edge.quarantined", "0001", "§4", "quarantine")
e("schema.py", 954, "schema.edge.use-only", "0001", "§4", "withhold")
e("schema.py", 978, "schema.edge.valid-now", "0028", "S2", "withhold")
e("schema.py", 1077, "schema.episode.active", "0022", "§4b-ii", "withhold")
e("schema.py", 1096, "schema.episode.assertable", "0001", "§4", "withhold")
e("schema.py", 1059, "schema.episode.quarantined", "0001", "§4", "quarantine")
e("schema.py", 1070, "schema.episode.use-only", "0001", "§4", "withhold")
e("schema.py", 1104, "schema.episode.valid-now", "0028", "S2", "withhold")
e("scope_linkage.py", 535, "scope-linkage.export.ambiguous-absorber", "0020", "§4a-iii", "refuse")
e("scope_linkage.py", 458, "scope-linkage.import.rows", "0020", "R6-2", "refuse")
e("scope_linkage.py", 478, "scope-linkage.import.rows", "0020", "R6-2", "refuse")
e("scope_linkage.py", 389, "scope-linkage.import.winner", "0020", "R6-1", "refuse")
e("scope_linkage.py", 397, "scope-linkage.import.winner", "0020", "R6-1", "refuse")
e("scope_linkage.py", 409, "scope-linkage.import.winner", "0020", "R6-1", "refuse")
e("scope_linkage.py", 413, "scope-linkage.import.winner", "0020", "R6-1", "refuse")
e("scope_read.py", 451, "scope-read.narrow-edges", "0020", "§4e", "withhold")
e("scope_read.py", 417, "scope-read.scoped", "0020", "§4a", "withhold")
e("scope_read.py", 313, "scope-read.view.no-policy", "0006", "§4", "refuse")
e("scope_read.py", 305, "scope-read.view.principal-not-identity", "0006", "§4", "refuse")
e("scope_read.py", 320, "scope-read.view.principal-ungroupable", "0006", "I13", "refuse")
e("scope.py", 719, "scope.classify.evidence-not-digest", "0006", "§4", "refuse")
e("scope.py", 705, "scope.classify.no-policy", "0006", "§4", "refuse")
e("scope.py", 711, "scope.classify.principal-ungroupable", "0006", "I13", "refuse")
e("scope.py", 447, "scope.closure.walk", "0020", "§4a-iii", "refuse")
e("scope.py", 468, "scope.closure.walk", "0020", "§4a-iii", "refuse")
e("scope.py", 480, "scope.closure.walk", "0020", "§4a-iii", "refuse")
e("scope.py", 484, "scope.closure.walk", "0020", "§4a-iii", "refuse")
e("scope.py", 486, "scope.closure.walk", "0020", "§4a-iii", "refuse")
e("scope.py", 492, "scope.closure.walk", "0020", "§4a-iii", "refuse")
e("scope.py", 494, "scope.closure.walk", "0020", "§4a-iii", "refuse")
e("scope.py", 497, "scope.closure.walk", "0020", "§4a-iii", "refuse")
e("scope.py", 500, "scope.closure.walk", "0020", "§4a-iii", "refuse")
e("scope.py", 502, "scope.closure.walk", "0020", "§4a-iii", "refuse")
e("scope.py", 767, "scope.filters.apply", "0020", "§4e", "withhold")
e("scope.py", 754, "scope.filters.bad-value", "0020", "§4e", "refuse")
e("scope.py", 746, "scope.filters.not-mapping", "0020", "§4e", "refuse")
e("scope.py", 750, "scope.filters.unknown-field", "0020", "§4e", "refuse")
e("scope.py", 163, "scope.identity.groupable", "0006", "I13", "withhold")
e("scope.py", 644, "scope.membership.abandoned", "0021", "§4a", "refuse")
e("scope.py", 640, "scope.membership.unknown-state", "0021", "§4a", "refuse")
e("scope.py", 307, "scope.policy.digest-overlap", "0006", "§4", "refuse")
e("scope.py", 301, "scope.policy.non-groupable-member", "0006", "I13", "refuse")
e("scope.py", 564, "scope.prune.cycle", "0021", "§4a", "refuse")
e("scope.py", 352, "scope.revalidate", "0006", "§7 tamper-evidence", "refuse")
e("scope.py", 355, "scope.revalidate", "0006", "§7 tamper-evidence", "refuse")
e("scope.py", 360, "scope.revalidate", "0006", "§7 tamper-evidence", "refuse")
e("scope.py", 365, "scope.revalidate", "0006", "§7 tamper-evidence", "refuse")
e("scope.py", 375, "scope.revalidate", "0006", "§7 tamper-evidence", "refuse")
e("store/sqlite.py", 983, "store.act-counter.allocate", "0008", "§6f (v7: the never-reset act counter)", "refuse")
e("store/sqlite.py", 2403, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2415, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2423, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2430, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2466, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2447, "store.add-episode.owner", "0004", "v3.5 §2c (i): the persisted owner never changes (0008 §6d's guard)", "refuse")
e("store/sqlite.py", 3722, "store.confirm-notice.standing", "0041", "§11.6.6 (confirm_notice: a standing row is not pending)", "refuse")
e("store/sqlite.py", 3729, "store.confirm-notice.target-absent", "0041", "§11.6.6 (confirm_notice: a pending notice whose target is gone is inert)", "refuse")
e("store/sqlite.py", 3714, "store.confirm-notice.unknown", "0041", "§11.6.6 (confirm_notice: an unknown or another user's id, one refusal)", "refuse")
e("store/sqlite.py", 1018, "store.confirm.active-challenge", "0047", "§4c INV-R13", "refuse")
e("store/sqlite.py", 1091, "store.confirm.correlation", "0008", "C9", "refuse")
e("store/sqlite.py", 1009, "store.confirm.not-assertable", "0008", "§6d", "refuse")
e("store/sqlite.py", 961, "store.confirm.request-digest", "0008", "C9", "refuse")
e("store/sqlite.py", 1032, "store.confirm.source-redacted", "0045", "§4d INV-G10", "refuse")
e("store/sqlite.py", 1004, "store.confirm.unknown-edge", "0008", "§6d", "refuse")
e("store/sqlite.py", 2251, "store.consolidation-contribution", "0014", "§2c", "refuse")
e("store/sqlite.py", 2259, "store.consolidation-contribution", "0014", "§2c", "refuse")
e("store/sqlite.py", 2292, "store.consolidation-contribution", "0014", "§2c", "refuse")
e("store/sqlite.py", 3507, "store.consolidation.abandon-live-lease", "0010", "X7", "refuse")
e("store/sqlite.py", 3312, "store.consolidation.contended", "0010", "X7/X11", "refuse")
e("store/sqlite.py", 3489, "store.consolidation.delete-not-current", "0010", "X21", "refuse")
e("store/sqlite.py", 3296, "store.consolidation.input-redacted", "0041", "§4b-ii INV-11", "refuse")
e("store/sqlite.py", 3343, "store.consolidation.renew-refused", "0010", "X7", "refuse")
e("store/sqlite.py", 3438, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3443, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3448, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3454, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3469, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3476, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3479, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3357, "store.consolidation.write-not-current", "0010", "X23", "refuse")
e("store/sqlite.py", 2074, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 2078, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 2084, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 2089, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 1886, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1893, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1897, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1901, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1905, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1911, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1916, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1920, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/data_migration.py", 409, "store.data-migration.inventory-integrity", "0044", "§4f / 0018 §4i D1", "refuse")
e("store/data_migration.py", 313, "store.data-migration.op-id-conflict", "0018", "§4i I32", "refuse")
e("store/data_migration.py", 505, "store.data-migration.read-refused", "0018", "§4i §4d", "refuse")
e("store/data_migration.py", 450, "store.data-migration.redacted-not-considered", "0044", "§4f.1 INV-A7", "withhold")
e("store/data_migration.py", 333, "store.data-migration.registry-changed", "0018", "§4i I25", "refuse")
e("store/data_migration.py", 458, "store.data-migration.withheld-revoked", "0044", "§4f.2 INV-A11", "withhold")
e("store/sqlite.py", 2527, "store.delete-episode.outcome", "0009", "§4c", "refuse")
e("store/sqlite.py", 2535, "store.delete-episode.reserved", "0010", "X21", "refuse")
e("store/sqlite.py", 1638, "store.edges.read-fence", "0001", "§4", "withhold")
e("store/sqlite.py", 4231, "store.embedding.delayed-writer", "0027", "§4f", "refuse")
e("store/sqlite.py", 4238, "store.embedding.stale-content", "0027", "§4f", "refuse")
e("store/sqlite.py", 4209, "store.embedding.txn-locked", "0041", "§4e (0007 §4c form)", "refuse")
e("store/sqlite.py", 2458, "store.episode.attested-redaction", "0041", "§4b-ii INV-11", "refuse")
e("store/sqlite.py", 2394, "store.episode.kind-not-recognised", "0041", "§2d-iv/§4h(ii) write path", "refuse")
e("store/sqlite.py", 2381, "store.episode.marker-introduced", "0041", "§4b INV-11's mirror", "refuse")
e("store/sqlite.py", 2389, "store.episode.retired-reason-not-registered", "0041", "§11.2 D1 (write path)", "refuse")
e("store/sqlite.py", 3525, "store.export.non-quiescent", "0010", "X-quiesce", "refuse")
e("store/sqlite.py", 2169, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2178, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2187, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2192, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2215, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2644, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2649, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2653, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2659, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2666, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2673, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2694, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2699, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2703, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2711, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2715, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2719, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2725, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2744, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2756, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2786, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2981, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2861, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2868, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2889, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2925, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2934, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2919, "store.import.episode-kind-not-recognised", "0041", "§2d-iv/§4h(ii) import boundary", "refuse")
e("store/sqlite.py", 3052, "store.import.notice-body-conflict", "0041", "§4g", "refuse")
e("store/sqlite.py", 3094, "store.import.notice-record-unredacted", "0041", "§11.6.6 (INV-RR12/RR14: a record an import creates, or a restore's held record, beside its notice must show it)", "refuse")
e("store/sqlite.py", 3115, "store.import.notice-record-unredacted", "0041", "§11.6.6 (INV-RR12/RR14: a record an import creates, or a restore's held record, beside its notice must show it)", "refuse")
e("store/sqlite.py", 3145, "store.import.notice-record-unredacted", "0041", "§11.6.6 (INV-RR12/RR14: a record an import creates, or a restore's held record, beside its notice must show it)", "refuse")
e("store/sqlite.py", 2851, "store.import.reason-not-registered", "0041", "§11.2 D1 (import boundary)", "refuse")
e("store/sqlite.py", 2903, "store.import.reason-not-registered", "0041", "§11.2 D1 (import boundary)", "refuse")
e("store/sqlite.py", 2895, "store.import.reserved-id", "0010", "X21 at the import, any owner (0004 v3.5 §2c (ii))", "refuse")
e("store/sqlite.py", 627, "store.journal.pre-epoch", "0029", "§4a", "refuse")
e("store/sqlite.py", 545, "store.journal.reason-not-dispositioned", "0030", "V-TOTAL", "refuse")
e("store/sqlite.py", 553, "store.journal.redaction-reason", "0041", "§4c/§11.2 D1", "refuse")
e("store/sqlite.py", 562, "store.journal.reinstatement-reason", "0029", "§4b-i (v12, INV-J1)", "refuse")
e("store/migration.py", 229, "store.migration.duplicate-outcome-chain", "0009", "§4c", "refuse")
e("store/migration.py", 87, "store.migration.postcondition", "0013", "§4f (v33, 0013-PA1: each step checked at the step)", "refuse")
e("store/migration.py", 848, "store.migration.version", "0013", "§4", "refuse")
e("store/migration.py", 871, "store.migration.version", "0013", "§4", "refuse")
e("store/sqlite.py", 3671, "store.notice.state-domain", "0041", "§11.6.6 (T4: the notice state's one writer)", "refuse")
e("store/schema_version.py", 2033, "store.open.invalid-version", "0007", "§4a", "refuse")
e("store/schema_version.py", 2110, "store.open.legacy", "0007", "§4h", "refuse")
e("store/schema_version.py", 2120, "store.open.legacy", "0007", "§4h", "refuse")
e("store/schema_version.py", 2136, "store.open.legacy", "0007", "§4h", "refuse")
e("store/schema_version.py", 2146, "store.open.legacy", "0007", "§4h", "refuse")
e("store/schema_version.py", 2020, "store.open.locked", "0007", "§4a", "refuse")
e("store/schema_version.py", 2037, "store.open.newer", "0007", "§4a", "refuse")
e("store/schema_version.py", 2007, "store.open.runtime-unsupported", "0007", "§4a-viii", "refuse")
e("store/schema_version.py", 1905, "store.open.unaccepted-shape", "0007", "§4a-v", "refuse")
e("store/schema_version.py", 1912, "store.open.unaccepted-shape", "0007", "§4a-v", "refuse")
e("store/schema_version.py", 1920, "store.open.unaccepted-shape", "0007", "§4a-v", "refuse")
e("store/sqlite.py", 2586, "store.outcome.context-ref", "0009", "§4c", "refuse")
e("store/sqlite.py", 2514, "store.read.input-claimed", "0010", "§4b", "withhold")
e("store/sqlite.py", 2511, "store.read.output-not-visible", "0010", "§4b", "withhold")
e("store/sqlite.py", 3871, "store.redact.both-or-neither", "0041", "§4a/INV-5", "refuse")
e("store/sqlite.py", 3944, "store.redact.disposition-changed", "0041", "§4h(i)", "refuse")
e("store/sqlite.py", 3916, "store.redact.input-claimed", "0041/0010", "X21", "refuse")
e("store/sqlite.py", 4067, "store.redact.nothing-to-redact", "0041", "§4b-ii (round 11: the owner's ruling, nothing to redact)", "refuse")
e("store/sqlite.py", 3877, "store.redact.reason-not-registered", "0041", "§11.2", "refuse")
e("store/sqlite.py", 3890, "store.redact.target", "0041", "§4a/INV-5", "refuse")
e("store/sqlite.py", 752, "store.redacted-reason.not-a-redaction", "0041", "§11.2 (only a redaction writes `redacted`)", "refuse")
e("store/sqlite.py", 939, "store.registry.request-redacted", "0008", "§6g (v7: the terminal rule, INV-Q7)", "refuse")
e("store/sqlite.py", 968, "store.registry.result-missing", "0008", "§6c (v7: replay reconstructs from result_ref; a dangling ref is an integrity conflict)", "refuse")
e("store/sqlite.py", 942, "store.registry.verb-held", "0008", "§6c (v7: the registry first; a held id names its verb)", "refuse")
e("store/sqlite.py", 1170, "store.reply.actor", "0047", "§2c who wrote it (a closed label until 0050)", "refuse")
e("store/sqlite.py", 1166, "store.reply.kind", "0047", "§2c INV-R8", "refuse")
e("store/sqlite.py", 1179, "store.reply.marker", "0047/0041", "§2c INV-R7 / 0041 INV-RR1", "refuse")
e("store/sqlite.py", 1200, "store.reply.procedural-edge", "0047", "§4d ruling INV-R19", "refuse")
e("store/sqlite.py", 1195, "store.reply.redacted-edge", "0047", "§0 INV-R9", "refuse")
e("store/sqlite.py", 1133, "store.reply.request-digest", "0047/0008", "§4b INV-R15/R24 (0008 §6c)", "refuse")
e("store/sqlite.py", 1212, "store.reply.resolve-repeat", "0047", "§4b INV-R14", "refuse")
e("store/sqlite.py", 1240, "store.reply.resolve-repeat", "0047", "§4b INV-R14", "refuse")
e("store/sqlite.py", 1208, "store.reply.resolve-target", "0047", "§4b INV-R14", "refuse")
e("store/sqlite.py", 1140, "store.reply.result-missing", "0008/0047", "§6c (reply: replay reconstructs from result_ref; a dangling ref is an integrity conflict)", "refuse")
e("store/sqlite.py", 1176, "store.reply.shape", "0047", "§4b the closed request (research's T10a F1)", "refuse")
e("store/sqlite.py", 1190, "store.reply.unknown-edge", "0047", "§2c INV-R9", "refuse")
e("store/revocation.py", 140, "store.revocation.integrity", "0022", "§4c", "refuse")
e("store/revocation.py", 139, "store.revocation.ordinal-collision", "0022", "§4c", "refuse")
e("store/revocation.py", 355, "store.revocation.revoke-reason-not-registered", "0041", "§11.2 D1 (revoke)", "refuse")
e("store/revocation_sweep.py", 360, "store.revocation.self-linkage", "0022", "§4c", "refuse")
e("store/revocation_sweep.py", 232, "store.revocation.source-not-revocable", "0022", "I13", "refuse")
e("store/revocation.py", 73, "store.revocation.unknown-state", "0022", "R5-1", "refuse")
e("store/schema_version.py", 1612, "store.runtime-refused", "0007", "§4g.6 4a (attested / verified / refused, by measurement; both gates' one decision)", "refuse")
e("store/sqlite.py", 1399, "store.supersession.absorb-acted", "0047", "§4e INV-R17 (a plan absorbing an acted prior is stale)", "refuse")
e("store/sqlite.py", 1814, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1832, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1848, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1853, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1937, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 1959, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 1967, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 1986, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 1991, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 1996, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 427, "store.txn.locked", "0013", "§5b", "refuse")
e("store/sqlite.py", 452, "store.txn.locked-retry", "0013", "§5b", "refuse")
e("store/data_migration.py", 578, "store.undo.ambiguous-outcome", "0044", "§4i (research's T7 annotation: no undo lookup chooses between two)", "refuse")
e("store/data_migration.py", 634, "store.undo.correlation", "0008", "C9 (the C8 fallback)", "refuse")
e("store/data_migration.py", 611, "store.undo.edge-unavailable", "0044", "§4i.2", "refuse")
e("store/data_migration.py", 588, "store.undo.no-outcome", "0044", "§4i.2 INV-A12", "refuse")
e("store/data_migration.py", 605, "store.undo.not-applicable", "0044", "§4i.2 INV-A12", "refuse")
e("store/data_migration.py", 593, "store.undo.not-restored", "0044", "§4i.2 INV-A12", "refuse")
e("store/data_migration.py", 649, "store.undo.request-digest", "0008", "C9", "refuse")
e("store/data_migration.py", 656, "store.undo.result-missing", "0008", "§6c (v7: replay reconstructs from result_ref; a dangling ref is an integrity conflict)", "refuse")
e("store/data_migration.py", 600, "store.undo.testimony", "0044", "§4i.2 R2-05 INV-A17", "refuse")
e("store/sqlite.py", 778, "store.upsert.attested-redaction", "0041", "§4b-ii INV-11", "refuse")
e("store/sqlite.py", 810, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 816, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 826, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 839, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 845, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 854, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 865, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 880, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 890, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 792, "store.upsert.invalidation-reason-not-registered", "0041", "§11.2 D1 (write path)", "refuse")
e("store/sqlite.py", 769, "store.upsert.marker-introduced", "0041", "§4b INV-11's mirror", "refuse")
e("store/sqlite.py", 797, "store.upsert.relation-only-quarantine", "0041", "§4h(i)", "refuse")
e("telemetry.py", 545, "telemetry.collector.not-enabled", "0015", "§4", "withhold")
e("telemetry.py", 374, "telemetry.flush.invalid-consent", "0015", "§4", "withhold")
e("telemetry.py", 380, "telemetry.flush.not-enabled", "0015", "§4", "withhold")
e("telemetry.py", 345, "telemetry.preview.invalid-consent", "0015", "§4", "withhold")
e("telemetry.py", 350, "telemetry.preview.not-enabled", "0015", "§4", "withhold")
