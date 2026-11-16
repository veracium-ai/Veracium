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
    "adapters/pydantic_ai.py": "control-flow",
    "trust_tools.py": "argument-check",   # 0031 §4f: the token's parse internals and the issuer's construction; its enforcement points are declared sites   # the same two raises (the extra's import, the tool-error re-raise) and list return
    "store/near_misses.py": "internal-invariant",  # 0007 §4g.6 4b (I3): head_variant refuses a near-miss whose anchor moved; runtime_status() reads that escape as `refused`, so it is not an enforcement point of its own
}
OVERRIDE = {  # (module, line) -> reason class, where the module default is not the truth for that line
    ("__init__.py", 437): "control-flow", ("__init__.py", 518): "control-flow", ("__init__.py", 655): "control-flow",
    ("__init__.py", 996): "control-flow", ("__init__.py", 1690): "control-flow", ("__init__.py", 1846): "control-flow",
    ("__init__.py", 1868): "control-flow", ("__init__.py", 1917): "control-flow", ("__init__.py", 1924): "control-flow",
    ("__init__.py", 1935): "control-flow", ("__init__.py", 1942): "control-flow", ("__init__.py", 1971): "control-flow",
    ("__init__.py", 2507): "internal-invariant", ("__init__.py", 2754): "control-flow",
    ("__init__.py", 339): "internal-invariant", ("__init__.py", 346): "internal-invariant",
    ("__init__.py", 1084): "internal-invariant", ("__init__.py", 1088): "internal-invariant", ("__init__.py", 1092): "internal-invariant",
    ("__init__.py", 1099): "internal-invariant", ("__init__.py", 1101): "internal-invariant",
    ("agreement.py", 219): "predicate-helper", ("agreement.py", 267): "control-flow", ("agreement.py", 487): "control-flow",
    ("asof/adapter.py", 54): "internal-invariant", ("asof/resolve.py", 117): "internal-invariant", ("asof/resolve.py", 122): "internal-invariant",
    ("asof/resolve.py", 181): "control-flow", ("asof/resolve.py", 206): "predicate-helper",
    ("compile.py", 229): "predicate-helper", ("diagnostics.py", 216): "predicate-helper", ("diagnostics.py", 249): "predicate-helper",
    ("doctor.py", 502): "predicate-helper", ("dryrun.py", 68): "predicate-helper",
    ("graph.py", 60): "predicate-helper", ("graph.py", 75): "predicate-helper", ("graph.py", 241): "internal-invariant",
    ("graph.py", 923): "argument-check", ("grounding.py", 154): "control-flow",
    ("ingest.py", 183): "control-flow", ("ingest.py", 135): "argument-check",
    ("lifecycle.py", 196): "control-flow", ("lifecycle.py", 342): "control-flow",
    ("portability.py", 1042): "control-flow",
    ("procedural_gate.py", 49): "argument-check", ("procedures.py", 104): "control-flow", ("procedures.py", 369): "control-flow",
    ("scope.py", 189): "predicate-helper", ("scope.py", 229): "internal-invariant", ("scope.py", 232): "internal-invariant",
    ("scope.py", 234): "internal-invariant", ("scope.py", 387): "predicate-helper", ("scope.py", 596): "control-flow", ("scope.py", 690): "control-flow",
    ("scope_linkage.py", 115): "control-flow", ("scope_linkage.py", 126): "control-flow", ("scope_linkage.py", 510): "predicate-helper",
    ("scope_linkage.py", 511): "predicate-helper", ("scope_linkage.py", 532): "control-flow",
    ("schema.py", 65): "control-flow", ("schema.py", 295): "predicate-helper", ("schema.py", 302): "predicate-helper",
    ("schema.py", 384): "predicate-helper", ("schema.py", 612): "predicate-helper", ("schema.py", 757): "internal-invariant",
    ("schema.py", 762): "internal-invariant", ("schema.py", 785): "internal-invariant", ("schema.py", 790): "internal-invariant",
    ("schema.py", 831): "predicate-helper", ("schema.py", 940): "predicate-helper", ("schema.py", 371): "internal-invariant", ("schema.py", 826): "internal-invariant",
    ("store/sqlite.py", 423): "control-flow", ("store/sqlite.py", 500): "control-flow", ("store/sqlite.py", 603): "control-flow",
    ("store/sqlite.py", 708): "control-flow", ("store/sqlite.py", 791): "control-flow", ("store/sqlite.py", 1177): "control-flow",
    ("store/sqlite.py", 1507): "control-flow", ("store/sqlite.py", 1549): "control-flow", ("store/sqlite.py", 1618): "control-flow",
    ("store/sqlite.py", 1632): "predicate-helper", ("store/sqlite.py", 1838): "control-flow", ("store/sqlite.py", 3243): "control-flow",
    ("store/sqlite.py", 3274): "control-flow", ("store/sqlite.py", 3283): "predicate-helper", ("store/sqlite.py", 405): "argument-check",
    ("store/sqlite.py", 687): "argument-check", ("store/sqlite.py", 3359): "argument-check", ("store/sqlite.py", 4272): "argument-check",
    ("store/sqlite.py", 4287): "argument-check", ("store/sqlite.py", 682): "control-flow", ("store/sqlite.py", 1500): "control-flow",
    ("store/sqlite.py", 2136): "control-flow", ("store/sqlite.py", 2412): "control-flow", ("store/sqlite.py", 2426): "control-flow",
    ("store/sqlite.py", 2441): "control-flow", ("store/sqlite.py", 3592): "control-flow", ("store/sqlite.py", 3614): "control-flow",
    ("store/sqlite.py", 4290): "control-flow", ("store/sqlite.py", 3332): "argument-check",
    ("store/revocation.py", 56): "predicate-helper", ("store/revocation.py", 110): "control-flow", ("store/revocation.py", 145): "control-flow",
    ("store/revocation_sweep.py", 172): "control-flow", ("store/revocation_sweep.py", 192): "control-flow",
    ("store/schema_version.py", 1987): "argument-check", ("store/schema_version.py", 2179): "control-flow",
    ("telemetry.py", 466): "control-flow", ("telemetry.py", 487): "control-flow", ("telemetry.py", 514): "control-flow",
    ("mcp_server.py", 946): "cli-usage", ("mcp_server.py", 952): "cli-usage", ("mcp_server.py", 958): "cli-usage", ("mcp_server.py", 978): "cli-usage",
    ("source_identity.py", 59): "argument-check", ("_json.py", 43): "control-flow", ("introspect.py", 54): "argument-check",
    ("__init__.py", 306): "control-flow",   # carried: __init__.py:_agent_call_path:RETURN_NONE:1
    ("__init__.py", 2068): "control-flow",   # carried: __init__.py:Memory._trust_scope_gate:RETURN_NONE:1
    ("__init__.py", 2598): "control-flow",   # carried: __init__.py:Memory.forget_everything_confirm:RAISE:2
    ("__init__.py", 2628): "internal-invariant",   # carried: __init__.py:Memory.source_revocations:RAISE:1
    ("__init__.py", 2638): "internal-invariant",   # specs/0022 §4g: a store without revocation support refuses, the Store base's refusing-default class
    ("adapters/_surface.py", 49): "internal-invariant",   # specs/0053: _registered:RAISE:1, the MCP server exposes no tool manager
    ("adapters/_surface.py", 53): "internal-invariant",   # specs/0053: _registered:RAISE:2, the served tools differ from the ones bound
    ("adapters/pydantic_ai.py", 62): "argument-check",   # specs/0053: as_tools:RAISE:1, a max_retries that is not a non-negative int
    ("budgets.py", 123): "internal-invariant",   # rendered_subject: the composer's own rendering diverged from its subject
    ("compile.py", 245): "predicate-helper",   # SR2-01: the cached code-owned empty body test, consumed by needs_recompile
    ("compile.py", 466): "predicate-helper",   # carried: compile.py:_unbound_by:RETURN_NONE:1
    ("lifecycle.py", 63): "internal-invariant",   # specs/0048 §4D, the owner's "Refuse, name it": a store without the transition refuses (the Store base's refusing-default class)
    ("mcp_server.py", 400): "control-flow",   # carried: mcp_server.py:_trust_gates:RETURN_NONE:1
    ("mcp_server.py", 406): "control-flow",   # carried: mcp_server.py:_scope_configuration:RETURN_NONE:1
    ("mcp_server.py", 412): "control-flow",   # carried: mcp_server.py:_scope_configuration:RETURN_NONE:2
    ("mcp_server.py", 419): "control-flow",   # carried: mcp_server.py:_unscoped_target_missing:RETURN_NONE:1
    ("mcp_server.py", 447): "internal-invariant",   # _trust_call: a failure after a commit in the call raises (INV-TT11's phase rule)
    ("mcp_server.py", 463): "control-flow",   # carried: mcp_server.py:find_facts_report:BOOL_RETURN:1
    ("mcp_server.py", 477): "control-flow",   # carried: mcp_server.py:correct_fact_report:BOOL_RETURN:1
    ("mcp_server.py", 487): "control-flow",   # carried: mcp_server.py:dispute_fact_report:BOOL_RETURN:1
    ("mcp_server.py", 495): "control-flow",   # carried: mcp_server.py:dispute_fact_report:BOOL_RETURN:2
    ("mcp_server.py", 505): "control-flow",   # carried: mcp_server.py:confirm_fact_report:BOOL_RETURN:1
    ("mcp_server.py", 519): "control-flow",   # carried: mcp_server.py:forget_fact_report:BOOL_RETURN:1
    ("mcp_server.py", 525): "control-flow",   # carried: mcp_server.py:forget_fact_report:BOOL_RETURN:2
    ("proactive.py", 253): "control-flow",   # 0003/obligations N1–N4 (NEW 1): proactive.py:assemble._commit_line:RETURN_NONE:1, a line that cannot fit its cap is dropped (budget plumbing)
    ("proactive.py", 303): "control-flow",   # 0003/obligations N1–N4 (N1): proactive.py:assemble._contested_line:RETURN_NONE:1, a group line that cannot hold one slot is dropped (budget plumbing)
    ("schema.py", 639): "predicate-helper",   # 0.29.0 B1+B2: schema.py:is_obligation:BOOL_RETURN:1 (consumed by the backstop and _lexical_scored)
    ("schema.py", 693): "predicate-helper",   # carried: schema.py:wiki_drops_on:BOOL_RETURN:1
    ("schema.py", 720): "predicate-helper",   # RII-R2-01: schema.py:assertion_view:RETURN_NONE:1
    ("schema.py", 1486): "internal-invariant",   # RII-R2-01: schema.py:_check_assertion_view_partition:RAISE:1
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
    ("store/sqlite.py", 4206): "control-flow",   # carried: store/sqlite.py:SqliteStore._erase_preview_keys:FILTER_RETURN:1
    ("trust_tools.py", 62): "internal-invariant",   # carried: trust_tools.py:TrustRefused.__init__:RAISE:1
    ("trust_tools.py", 101): "control-flow",   # carried: trust_tools.py:_sorted_keys:FILTER_RETURN:1
    ("trust_tools.py", 267): "internal-invariant",   # RenderReceipt.admit: a subject not at its offset in the admitted line
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

# specs/0031 §4f (the trust tools; research's 0042 stage-1 classification, 2026-11-15, 41 of dev's 50 agreed and the
# four differences taken: the confirm's bare re-raise and the reports' `return refused` are control-flow; the token's
# single malformed exit and recall's receipt-with-as_of refusal are enforcement). One id per decision, each fire
# carrying its reason as the label. INV per id: trust.scope-gate also enforces INV-TT18 (source_unbound,
# source_out_of_scope) and INV-TT7 (another user's id = an unknown id); its scope_unconfigured and principal_ungroupable
# are §4a step 5 ("configuration refusals come first"); trust.erase.store-changed is INV-TT9's one-transaction property too

# specs/0049 v2.2 (E2, E2b): edges_since's two refusals, ENFORCEMENT by research's stage 1 and the round-1
# verdict's Q5 (a reachable public decision upholding the no-substitution guarantee; a custom backend reaches both)

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
e("compile.py", 495, "compile.bind.empty-body", "0003", "§4c-ii v18.7 (C3-01: the code-owned empty body is served only when no write for the user committed since its basis)", "withhold")
e("compile.py", 476, "compile.bind.unbound", "0047", "§4d INV-R18 (R-II round 2's RII-01: recall serves no wiki body its own snapshot does not admit)", "withhold")
e("compile.py", 156, "compile.fence.disputed", "0047", "§4d INV-R18 (the in-flight fence withholds a body drawn on a fact challenged since)", "withhold")
e("compile.py", 208, "compile.grounded-inputs", "0004", "§4", "withhold")
e("diagnostics.py", 276, "diagnostics.send.not-consented", "0015", "§4", "withhold")
e("gate.py", 54, "gate.exclude-procedural", "0037", "V-EXTRACTOR-QUOTE-GATED", "withhold")
e("gate.py", 178, "gate.partition-parts", "0001", "§4", "withhold")
e("gate.py", 125, "gate.scoped-assertable.entitlement", "0011", "§4c", "withhold")
e("gate.py", 119, "gate.scoped-assertable.invisible", "0020", "§4a", "withhold")
e("gate.py", 122, "gate.scoped-assertable.third-party-shaped", "0020", "§4a", "withhold")
e("graph.py", 300, "graph.absorption.cross-scope", "0020", "§4a-iii", "withhold")
e("graph.py", 302, "graph.absorption.no-flattening-plan", "0021", "§4a", "withhold")
e("graph.py", 297, "graph.absorption.scope-unresolved", "0020", "§4a-iii", "withhold")
e("graph.py", 1391, "graph.collapse-for-render", "0012", "§4c", "withhold")
e("graph.py", 1316, "graph.collapse.acted", "0047", "§4e (collapse never hides a member carrying an act, nor one behind a withheld survivor)", "withhold")
e("graph.py", 368, "graph.correction.identity-mismatch", "0011", "§4b", "refuse")
e("graph.py", 380, "graph.correction.prior-not-active", "0011", "§4b", "refuse")
e("graph.py", 862, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 868, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 870, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 872, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 874, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 876, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 439, "graph.src-revoked", "0022", "§4a", "withhold")
e("graph.py", 443, "graph.src-revoked", "0022", "§4a", "withhold")
e("graph.py", 1234, "graph.strictly-redundant", "0012", "§4c", "withhold")
e("graph.py", 194, "graph.supersession.receipt-boundary", "0014", "R10", "refuse")
e("graph.py", 220, "graph.supersession.replay-mismatch", "0014", "§4b", "refuse")
e("grounding.py", 243, "grounding.ungrounded", "0019", "§4", "downgrade")
e("ingest.py", 317, "ingest.basis-via-remember", "0037", "§4b", "refuse")
e("ingest.py", 378, "ingest.instructions-not-a-list", "0039", "§2a", "downgrade")
e("ingest.py", 306, "ingest.source-id-required", "0006", "§4 rule 9", "refuse")
e("mcp_server.py", 120, "mcp.closed-set.author", "0011", "§4d", "refuse")
e("mcp_server.py", 129, "mcp.closed-set.trust-field", "0011", "§4d", "refuse")
e("__init__.py", 2213, "memory.confirm.unknown-target", "0008", "§6c INV-Q2", "refuse")
e("__init__.py", 2458, "memory.correct.inactive-edge", "0011", "§4b", "refuse")
e("__init__.py", 2478, "memory.correct.procedural", "0037", "§4a-iii", "refuse")
e("__init__.py", 2525, "memory.correct.refused", "0011", "§4b", "refuse")
e("__init__.py", 2130, "memory.dispute.inactive-edge", "0003", "§4b", "refuse")
e("__init__.py", 2100, "memory.edge.unknown-target", "0041", "INV-5", "refuse")
e("__init__.py", 2017, "memory.edges-since.no-journal", "0049", "E2", "refuse")
e("__init__.py", 2025, "memory.edges-since.no-journal-event", "0049", "E2b", "refuse")
e("__init__.py", 2042, "memory.feedback.attested-target", "0041", "§4b-ii INV-11 (derived episodes)", "refuse")
e("__init__.py", 972, "memory.recall.as-of-on-proactive", "0028", "§2c", "refuse")
e("__init__.py", 1109, "memory.recall.policy-with-as-of", "0027", "v13 §4c", "refuse")
e("__init__.py", 978, "memory.recall.render-receipt-with-as-of", "0031", "INV-TT3", "refuse")
e("__init__.py", 2322, "memory.record-outcome.actor-vocabulary", "0008", "§4", "refuse")
e("__init__.py", 2325, "memory.record-outcome.human-judgment", "0008", "§4", "refuse")
e("__init__.py", 2328, "memory.record-outcome.system-judgment", "0008", "§4", "refuse")
e("__init__.py", 442, "memory.scope.local-origin-missing", "0006", "I9", "refuse")
e("portability.py", 504, "portability.export.non-quiescent", "0010", "X-quiesce", "refuse")
e("portability.py", 1835, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1840, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1846, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1851, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1857, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1885, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1891, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1920, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1934, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1946, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1950, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1963, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 1968, "portability.import.act-preflight", "0008", "§6e–§6f", "refuse")
e("portability.py", 338, "portability.import.act-records", "0008", "§6e", "refuse")
e("portability.py", 367, "portability.import.act-records", "0008", "§6e", "refuse")
e("portability.py", 379, "portability.import.act-records", "0008", "§6e", "refuse")
e("portability.py", 1335, "portability.import.agreement-invalid", "0025", "§4c", "refuse")
e("portability.py", 1745, "portability.import.arity-preflight", "0044", "§4l", "refuse")
e("portability.py", 1752, "portability.import.arity-preflight", "0044", "§4l", "refuse")
e("portability.py", 1766, "portability.import.arity-preflight", "0044", "§4l", "refuse")
e("portability.py", 193, "portability.import.arity-records", "0044", "§4l", "refuse")
e("portability.py", 198, "portability.import.arity-records", "0044", "§4l", "refuse")
e("portability.py", 223, "portability.import.arity-records", "0044", "§4l", "refuse")
e("portability.py", 230, "portability.import.arity-records", "0044", "§4l", "refuse")
e("portability.py", 265, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 273, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 277, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 283, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 289, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 293, "portability.import.arity-unit", "0044", "§4l", "refuse")
e("portability.py", 432, "portability.import.axis", "0045", "§2c", "refuse")
e("portability.py", 749, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 753, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 762, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 766, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 770, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 775, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 782, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 787, "portability.import.chain", "0009", "§4c/H5", "refuse")
e("portability.py", 838, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 841, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 844, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 873, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 887, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 897, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 909, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 921, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 928, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 936, "portability.import.file", "0005", "§4", "refuse")
e("portability.py", 1425, "portability.import.origin-missing", "0006", "§4", "refuse")
e("portability.py", 2027, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2031, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2042, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2057, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2061, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2084, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2093, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2097, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2105, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 2124, "portability.import.preflight", "0009", "§4c", "refuse")
e("portability.py", 1680, "portability.import.race-exhausted", "0009", "§4c", "refuse")
e("portability.py", 1481, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1492, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1499, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1508, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1525, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1531, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1535, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1543, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1572, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 1624, "portability.import.record", "0009", "§4c/0014 §2c", "refuse")
e("portability.py", 823, "portability.import.restore-not-bool", "0005", "P13", "refuse")
e("portability.py", 828, "portability.import.restore-with-user", "0005", "P5", "refuse")
e("proactive.py", 184, "proactive.eligible", "0012", "§4", "withhold")
e("proactive.py", 112, "proactive.variant", "0012", "I8j", "withhold")
e("proactive.py", 116, "proactive.variant", "0012", "I8j", "withhold")
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
e("schema.py", 1010, "schema.edge.assertable", "0001", "§4", "withhold")
e("schema.py", 956, "schema.edge.quarantined", "0001", "§4", "quarantine")
e("schema.py", 968, "schema.edge.use-only", "0001", "§4", "withhold")
e("schema.py", 992, "schema.edge.valid-now", "0028", "S2", "withhold")
e("schema.py", 1091, "schema.episode.active", "0022", "§4b-ii", "withhold")
e("schema.py", 1110, "schema.episode.assertable", "0001", "§4", "withhold")
e("schema.py", 1073, "schema.episode.quarantined", "0001", "§4", "quarantine")
e("schema.py", 1084, "schema.episode.use-only", "0001", "§4", "withhold")
e("schema.py", 1118, "schema.episode.valid-now", "0028", "S2", "withhold")
e("scope_linkage.py", 535, "scope-linkage.export.ambiguous-absorber", "0020", "§4a-iii", "refuse")
e("scope_linkage.py", 458, "scope-linkage.import.rows", "0020", "R6-2", "refuse")
e("scope_linkage.py", 478, "scope-linkage.import.rows", "0020", "R6-2", "refuse")
e("scope_linkage.py", 389, "scope-linkage.import.winner", "0020", "R6-1", "refuse")
e("scope_linkage.py", 397, "scope-linkage.import.winner", "0020", "R6-1", "refuse")
e("scope_linkage.py", 409, "scope-linkage.import.winner", "0020", "R6-1", "refuse")
e("scope_linkage.py", 413, "scope-linkage.import.winner", "0020", "R6-1", "refuse")
e("scope_read.py", 465, "scope-read.narrow-edges", "0020", "§4e", "withhold")
e("scope_read.py", 431, "scope-read.scoped", "0020", "§4a", "withhold")
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
e("store/sqlite.py", 1056, "store.act-counter.allocate", "0008", "§6f (v7: the never-reset act counter)", "refuse")
e("store/sqlite.py", 2481, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2493, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2501, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2508, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2544, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2525, "store.add-episode.owner", "0004", "v3.5 §2c (i): the persisted owner never changes (0008 §6d's guard)", "refuse")
e("store/sqlite.py", 3800, "store.confirm-notice.standing", "0041", "§11.6.6 (confirm_notice: a standing row is not pending)", "refuse")
e("store/sqlite.py", 3807, "store.confirm-notice.target-absent", "0041", "§11.6.6 (confirm_notice: a pending notice whose target is gone is inert)", "refuse")
e("store/sqlite.py", 3792, "store.confirm-notice.unknown", "0041", "§11.6.6 (confirm_notice: an unknown or another user's id, one refusal)", "refuse")
e("store/sqlite.py", 1092, "store.confirm.active-challenge", "0047", "§4c INV-R13", "refuse")
e("store/sqlite.py", 1169, "store.confirm.correlation", "0008", "C9", "refuse")
e("store/sqlite.py", 1083, "store.confirm.not-assertable", "0008", "§6d", "refuse")
e("store/sqlite.py", 1034, "store.confirm.request-digest", "0008", "C9", "refuse")
e("store/sqlite.py", 1106, "store.confirm.source-redacted", "0045", "§4d INV-G10", "refuse")
e("store/sqlite.py", 1078, "store.confirm.unknown-edge", "0008", "§6d", "refuse")
e("store/sqlite.py", 2329, "store.consolidation-contribution", "0014", "§2c", "refuse")
e("store/sqlite.py", 2337, "store.consolidation-contribution", "0014", "§2c", "refuse")
e("store/sqlite.py", 2370, "store.consolidation-contribution", "0014", "§2c", "refuse")
e("store/sqlite.py", 3585, "store.consolidation.abandon-live-lease", "0010", "X7", "refuse")
e("store/sqlite.py", 3390, "store.consolidation.contended", "0010", "X7/X11", "refuse")
e("store/sqlite.py", 3567, "store.consolidation.delete-not-current", "0010", "X21", "refuse")
e("store/sqlite.py", 3374, "store.consolidation.input-redacted", "0041", "§4b-ii INV-11", "refuse")
e("store/sqlite.py", 3421, "store.consolidation.renew-refused", "0010", "X7", "refuse")
e("store/sqlite.py", 3516, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3521, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3526, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3532, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3547, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3554, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3557, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3435, "store.consolidation.write-not-current", "0010", "X23", "refuse")
e("store/sqlite.py", 2152, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 2156, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 2162, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 2167, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 1964, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1971, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1975, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1979, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1983, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1989, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1994, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1998, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/data_migration.py", 409, "store.data-migration.inventory-integrity", "0044", "§4f / 0018 §4i D1", "refuse")
e("store/data_migration.py", 313, "store.data-migration.op-id-conflict", "0018", "§4i I32", "refuse")
e("store/data_migration.py", 511, "store.data-migration.read-refused", "0018", "§4i §4d", "refuse")
e("store/data_migration.py", 450, "store.data-migration.redacted-not-considered", "0044", "§4f.1 INV-A7", "withhold")
e("store/data_migration.py", 333, "store.data-migration.registry-changed", "0018", "§4i I25", "refuse")
e("store/data_migration.py", 458, "store.data-migration.withheld-revoked", "0044", "§4f.2 INV-A11", "withhold")
e("store/sqlite.py", 2605, "store.delete-episode.outcome", "0009", "§4c", "refuse")
e("store/sqlite.py", 2613, "store.delete-episode.reserved", "0010", "X21", "refuse")
e("store/sqlite.py", 1716, "store.edges.read-fence", "0001", "§4", "withhold")
e("store/sqlite.py", 4338, "store.embedding.delayed-writer", "0027", "§4f", "refuse")
e("store/sqlite.py", 4345, "store.embedding.stale-content", "0027", "§4f", "refuse")
e("store/sqlite.py", 4316, "store.embedding.txn-locked", "0041", "§4e (0007 §4c form)", "refuse")
e("store/sqlite.py", 2536, "store.episode.attested-redaction", "0041", "§4b-ii INV-11", "refuse")
e("store/sqlite.py", 2472, "store.episode.kind-not-recognised", "0041", "§2d-iv/§4h(ii) write path", "refuse")
e("store/sqlite.py", 2459, "store.episode.marker-introduced", "0041", "§4b INV-11's mirror", "refuse")
e("store/sqlite.py", 2467, "store.episode.retired-reason-not-registered", "0041", "§11.2 D1 (write path)", "refuse")
e("store/sqlite.py", 3603, "store.export.non-quiescent", "0010", "X-quiesce", "refuse")
e("store/sqlite.py", 2247, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2256, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2265, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2270, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2293, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2722, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2727, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2731, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2737, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2744, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2751, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2772, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2777, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2781, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2789, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2793, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2797, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2803, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2822, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2834, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2864, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 3059, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2939, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2946, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2967, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 3003, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 3012, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2997, "store.import.episode-kind-not-recognised", "0041", "§2d-iv/§4h(ii) import boundary", "refuse")
e("store/sqlite.py", 3130, "store.import.notice-body-conflict", "0041", "§4g", "refuse")
e("store/sqlite.py", 3172, "store.import.notice-record-unredacted", "0041", "§11.6.6 (INV-RR12/RR14: a record an import creates, or a restore's held record, beside its notice must show it)", "refuse")
e("store/sqlite.py", 3193, "store.import.notice-record-unredacted", "0041", "§11.6.6 (INV-RR12/RR14: a record an import creates, or a restore's held record, beside its notice must show it)", "refuse")
e("store/sqlite.py", 3223, "store.import.notice-record-unredacted", "0041", "§11.6.6 (INV-RR12/RR14: a record an import creates, or a restore's held record, beside its notice must show it)", "refuse")
e("store/sqlite.py", 2929, "store.import.reason-not-registered", "0041", "§11.2 D1 (import boundary)", "refuse")
e("store/sqlite.py", 2981, "store.import.reason-not-registered", "0041", "§11.2 D1 (import boundary)", "refuse")
e("store/sqlite.py", 2973, "store.import.reserved-id", "0010", "X21 at the import, any owner (0004 v3.5 §2c (ii))", "refuse")
e("store/sqlite.py", 700, "store.journal.pre-epoch", "0029", "§4a", "refuse")
e("store/sqlite.py", 609, "store.journal.reason-not-dispositioned", "0030", "V-TOTAL", "refuse")
e("store/sqlite.py", 617, "store.journal.redaction-reason", "0041", "§4c/§11.2 D1", "refuse")
e("store/sqlite.py", 626, "store.journal.reinstatement-reason", "0029", "§4b-i (v12, INV-J1)", "refuse")
e("store/migration.py", 229, "store.migration.duplicate-outcome-chain", "0009", "§4c", "refuse")
e("store/migration.py", 87, "store.migration.postcondition", "0013", "§4f (v33, 0013-PA1: each step checked at the step)", "refuse")
e("store/migration.py", 848, "store.migration.version", "0013", "§4", "refuse")
e("store/migration.py", 871, "store.migration.version", "0013", "§4", "refuse")
e("store/sqlite.py", 3749, "store.notice.state-domain", "0041", "§11.6.6 (T4: the notice state's one writer)", "refuse")
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
e("store/sqlite.py", 2664, "store.outcome.context-ref", "0009", "§4c", "refuse")
e("store/sqlite.py", 2592, "store.read.input-claimed", "0010", "§4b", "withhold")
e("store/sqlite.py", 2589, "store.read.output-not-visible", "0010", "§4b", "withhold")
e("store/sqlite.py", 3949, "store.redact.both-or-neither", "0041", "§4a/INV-5", "refuse")
e("store/sqlite.py", 4022, "store.redact.disposition-changed", "0041", "§4h(i)", "refuse")
e("store/sqlite.py", 3994, "store.redact.input-claimed", "0041/0010", "X21", "refuse")
e("store/sqlite.py", 4145, "store.redact.nothing-to-redact", "0041", "§4b-ii (round 11: the owner's ruling, nothing to redact)", "refuse")
e("store/sqlite.py", 3955, "store.redact.reason-not-registered", "0041", "§11.2", "refuse")
e("store/sqlite.py", 3968, "store.redact.target", "0041", "§4a/INV-5", "refuse")
e("store/sqlite.py", 825, "store.redacted-reason.not-a-redaction", "0041", "§11.2 (only a redaction writes `redacted`)", "refuse")
e("store/sqlite.py", 1012, "store.registry.request-redacted", "0008", "§6g (v7: the terminal rule, INV-Q7)", "refuse")
e("store/sqlite.py", 1041, "store.registry.result-missing", "0008", "§6c (v7: replay reconstructs from result_ref; a dangling ref is an integrity conflict)", "refuse")
e("store/sqlite.py", 1015, "store.registry.verb-held", "0008", "§6c (v7: the registry first; a held id names its verb)", "refuse")
e("store/sqlite.py", 1248, "store.reply.actor", "0047", "§2c who wrote it (a closed label until 0050)", "refuse")
e("store/sqlite.py", 1244, "store.reply.kind", "0047", "§2c INV-R8", "refuse")
e("store/sqlite.py", 1257, "store.reply.marker", "0047/0041", "§2c INV-R7 / 0041 INV-RR1", "refuse")
e("store/sqlite.py", 1278, "store.reply.procedural-edge", "0047", "§4d ruling INV-R19", "refuse")
e("store/sqlite.py", 1273, "store.reply.redacted-edge", "0047", "§0 INV-R9", "refuse")
e("store/sqlite.py", 1211, "store.reply.request-digest", "0047/0008", "§4b INV-R15/R24 (0008 §6c)", "refuse")
e("store/sqlite.py", 1290, "store.reply.resolve-repeat", "0047", "§4b INV-R14", "refuse")
e("store/sqlite.py", 1318, "store.reply.resolve-repeat", "0047", "§4b INV-R14", "refuse")
e("store/sqlite.py", 1286, "store.reply.resolve-target", "0047", "§4b INV-R14", "refuse")
e("store/sqlite.py", 1218, "store.reply.result-missing", "0008/0047", "§6c (reply: replay reconstructs from result_ref; a dangling ref is an integrity conflict)", "refuse")
e("store/sqlite.py", 1254, "store.reply.shape", "0047", "§4b the closed request (research's T10a F1)", "refuse")
e("store/sqlite.py", 1268, "store.reply.unknown-edge", "0047", "§2c INV-R9", "refuse")
e("store/revocation.py", 140, "store.revocation.integrity", "0022", "§4c", "refuse")
e("store/revocation.py", 139, "store.revocation.ordinal-collision", "0022", "§4c", "refuse")
e("store/revocation.py", 355, "store.revocation.revoke-reason-not-registered", "0041", "§11.2 D1 (revoke)", "refuse")
e("store/revocation_sweep.py", 360, "store.revocation.self-linkage", "0022", "§4c", "refuse")
e("store/revocation_sweep.py", 232, "store.revocation.source-not-revocable", "0022", "I13", "refuse")
e("store/revocation.py", 73, "store.revocation.unknown-state", "0022", "R5-1", "refuse")
e("store/schema_version.py", 1612, "store.runtime-refused", "0007", "§4g.6 4a (attested / verified / refused, by measurement; both gates' one decision)", "refuse")
e("store/sqlite.py", 1477, "store.supersession.absorb-acted", "0047", "§4e INV-R17 (a plan absorbing an acted prior is stale)", "refuse")
e("store/sqlite.py", 1892, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1910, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1926, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1931, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 2015, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 2037, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 2045, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 2064, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 2069, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 2074, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 491, "store.txn.locked", "0013", "§5b", "refuse")
e("store/sqlite.py", 516, "store.txn.locked-retry", "0013", "§5b", "refuse")
e("store/data_migration.py", 584, "store.undo.ambiguous-outcome", "0044", "§4i (research's T7 annotation: no undo lookup chooses between two)", "refuse")
e("store/data_migration.py", 640, "store.undo.correlation", "0008", "C9 (the C8 fallback)", "refuse")
e("store/data_migration.py", 617, "store.undo.edge-unavailable", "0044", "§4i.2", "refuse")
e("store/data_migration.py", 594, "store.undo.no-outcome", "0044", "§4i.2 INV-A12", "refuse")
e("store/data_migration.py", 611, "store.undo.not-applicable", "0044", "§4i.2 INV-A12", "refuse")
e("store/data_migration.py", 599, "store.undo.not-restored", "0044", "§4i.2 INV-A12", "refuse")
e("store/data_migration.py", 655, "store.undo.request-digest", "0008", "C9", "refuse")
e("store/data_migration.py", 662, "store.undo.result-missing", "0008", "§6c (v7: replay reconstructs from result_ref; a dangling ref is an integrity conflict)", "refuse")
e("store/data_migration.py", 606, "store.undo.testimony", "0044", "§4i.2 R2-05 INV-A17", "refuse")
e("store/sqlite.py", 851, "store.upsert.attested-redaction", "0041", "§4b-ii INV-11", "refuse")
e("store/sqlite.py", 883, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 889, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 899, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 912, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 918, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 927, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 938, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 953, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 963, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 865, "store.upsert.invalidation-reason-not-registered", "0041", "§11.2 D1 (write path)", "refuse")
e("store/sqlite.py", 842, "store.upsert.marker-introduced", "0041", "§4b INV-11's mirror", "refuse")
e("store/sqlite.py", 870, "store.upsert.relation-only-quarantine", "0041", "§4h(i)", "refuse")
e("telemetry.py", 545, "telemetry.collector.not-enabled", "0015", "§4", "withhold")
e("telemetry.py", 374, "telemetry.flush.invalid-consent", "0015", "§4", "withhold")
e("telemetry.py", 380, "telemetry.flush.not-enabled", "0015", "§4", "withhold")
e("telemetry.py", 345, "telemetry.preview.invalid-consent", "0015", "§4", "withhold")
e("telemetry.py", 350, "telemetry.preview.not-enabled", "0015", "§4", "withhold")
e("__init__.py", 2593, "trust.erase.confirm.principal-scoped", "0031", "INV-TT17", "refuse")
e("__init__.py", 2573, "trust.erase.preview.issuer-context", "0031", "§4e", "refuse")
e("__init__.py", 2570, "trust.erase.preview.principal-scoped", "0031", "INV-TT17", "refuse")
e("store/sqlite.py", 4231, "trust.erase.store-changed", "0031", "INV-TT8", "refuse")
e("__init__.py", 2725, "trust.receipt.scope-filter", "0031", "INV-TT19", "withhold")
e("__init__.py", 2073, "trust.scope-gate", "0031", "INV-TT16", "refuse")
e("__init__.py", 2075, "trust.scope-gate", "0031", "INV-TT16", "refuse")
e("__init__.py", 2079, "trust.scope-gate", "0031", "INV-TT16", "refuse")
e("__init__.py", 2084, "trust.scope-gate", "0031", "INV-TT16", "refuse")
e("__init__.py", 2087, "trust.scope-gate", "0031", "INV-TT16", "refuse")
e("__init__.py", 2092, "trust.scope-gate", "0031", "INV-TT16", "refuse")
e("__init__.py", 2093, "trust.scope-gate", "0031", "INV-TT16", "refuse")
e("trust_tools.py", 165, "trust.token.parse", "0031", "INV-TT21", "refuse")
e("trust_tools.py", 214, "trust.token.verify", "0031", "INV-TT8", "refuse")
e("trust_tools.py", 216, "trust.token.verify", "0031", "INV-TT8", "refuse")
e("trust_tools.py", 219, "trust.token.verify", "0031", "INV-TT8", "refuse")
e("trust_tools.py", 221, "trust.token.verify", "0031", "INV-TT8", "refuse")
