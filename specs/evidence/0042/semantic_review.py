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
    "store/near_misses.py": "internal-invariant",  # 0007 §4g.6 4b (I3): head_variant refuses a near-miss whose anchor moved; runtime_status() reads that escape as `refused`, so it is not an enforcement point of its own
}
OVERRIDE = {  # (module, line) -> reason class, where the module default is not the truth for that line
    ("__init__.py", 403): "control-flow", ("__init__.py", 484): "control-flow", ("__init__.py", 621): "control-flow",
    ("__init__.py", 948): "control-flow", ("__init__.py", 1588): "control-flow", ("__init__.py", 1729): "control-flow",
    ("__init__.py", 1751): "control-flow", ("__init__.py", 1800): "control-flow", ("__init__.py", 1807): "control-flow",
    ("__init__.py", 1818): "control-flow", ("__init__.py", 1825): "control-flow", ("__init__.py", 1854): "control-flow",
    ("__init__.py", 1880): "control-flow", ("__init__.py", 2264): "internal-invariant", ("__init__.py", 2352): "control-flow",
    ("__init__.py", 305): "internal-invariant", ("__init__.py", 312): "internal-invariant",
    ("__init__.py", 1028): "internal-invariant", ("__init__.py", 1032): "internal-invariant", ("__init__.py", 1036): "internal-invariant",
    ("__init__.py", 1043): "internal-invariant", ("__init__.py", 1045): "internal-invariant",
    ("agreement.py", 219): "predicate-helper", ("agreement.py", 267): "control-flow", ("agreement.py", 487): "control-flow",
    ("asof/adapter.py", 54): "internal-invariant", ("asof/resolve.py", 117): "internal-invariant", ("asof/resolve.py", 122): "internal-invariant",
    ("asof/resolve.py", 181): "control-flow", ("asof/resolve.py", 206): "predicate-helper",
    ("compile.py", 208): "predicate-helper", ("diagnostics.py", 216): "predicate-helper", ("diagnostics.py", 249): "predicate-helper",
    ("doctor.py", 484): "predicate-helper", ("dryrun.py", 68): "predicate-helper",
    ("graph.py", 60): "predicate-helper", ("graph.py", 75): "predicate-helper", ("graph.py", 241): "internal-invariant",
    ("graph.py", 920): "argument-check", ("grounding.py", 154): "control-flow",
    ("ingest.py", 183): "control-flow", ("ingest.py", 135): "argument-check",
    ("lifecycle.py", 208): "control-flow", ("lifecycle.py", 354): "control-flow",
    ("portability.py", 1017): "control-flow",
    ("procedural_gate.py", 49): "argument-check", ("procedures.py", 104): "control-flow", ("procedures.py", 369): "control-flow",
    ("scope.py", 189): "predicate-helper", ("scope.py", 229): "internal-invariant", ("scope.py", 232): "internal-invariant",
    ("scope.py", 234): "internal-invariant", ("scope.py", 387): "predicate-helper", ("scope.py", 596): "control-flow", ("scope.py", 690): "control-flow",
    ("scope_linkage.py", 115): "control-flow", ("scope_linkage.py", 126): "control-flow", ("scope_linkage.py", 510): "predicate-helper",
    ("scope_linkage.py", 511): "predicate-helper", ("scope_linkage.py", 532): "control-flow",
    ("schema.py", 64): "control-flow", ("schema.py", 280): "predicate-helper", ("schema.py", 287): "predicate-helper",
    ("schema.py", 369): "predicate-helper", ("schema.py", 597): "predicate-helper", ("schema.py", 723): "internal-invariant",
    ("schema.py", 728): "internal-invariant", ("schema.py", 751): "internal-invariant", ("schema.py", 756): "internal-invariant",
    ("schema.py", 797): "predicate-helper", ("schema.py", 906): "predicate-helper", ("schema.py", 356): "internal-invariant", ("schema.py", 792): "internal-invariant",
    ("store/sqlite.py", 282): "control-flow", ("store/sqlite.py", 359): "control-flow", ("store/sqlite.py", 439): "control-flow",
    ("store/sqlite.py", 535): "control-flow", ("store/sqlite.py", 618): "control-flow", ("store/sqlite.py", 1003): "control-flow",
    ("store/sqlite.py", 1333): "control-flow", ("store/sqlite.py", 1378): "control-flow", ("store/sqlite.py", 1449): "control-flow",
    ("store/sqlite.py", 1465): "predicate-helper", ("store/sqlite.py", 1620): "control-flow", ("store/sqlite.py", 3027): "control-flow",
    ("store/sqlite.py", 3058): "control-flow", ("store/sqlite.py", 3067): "predicate-helper", ("store/sqlite.py", 264): "argument-check",
    ("store/sqlite.py", 514): "argument-check", ("store/sqlite.py", 3143): "argument-check", ("store/sqlite.py", 4025): "argument-check",
    ("store/sqlite.py", 4040): "argument-check", ("store/sqlite.py", 509): "control-flow", ("store/sqlite.py", 1326): "control-flow",
    ("store/sqlite.py", 1918): "control-flow", ("store/sqlite.py", 2194): "control-flow", ("store/sqlite.py", 2208): "control-flow",
    ("store/sqlite.py", 2223): "control-flow", ("store/sqlite.py", 3376): "control-flow", ("store/sqlite.py", 3398): "control-flow",
    ("store/sqlite.py", 4043): "control-flow", ("store/sqlite.py", 3116): "argument-check",
    ("store/revocation.py", 56): "predicate-helper", ("store/revocation.py", 110): "control-flow", ("store/revocation.py", 145): "control-flow",
    ("store/revocation_sweep.py", 172): "control-flow", ("store/revocation_sweep.py", 192): "control-flow",
    ("store/schema_version.py", 1972): "argument-check", ("store/schema_version.py", 2146): "control-flow",
    ("telemetry.py", 466): "control-flow", ("telemetry.py", 487): "control-flow", ("telemetry.py", 514): "control-flow",
    ("mcp_server.py", 578): "cli-usage", ("mcp_server.py", 584): "cli-usage", ("mcp_server.py", 588): "cli-usage", ("mcp_server.py", 600): "cli-usage",
    ("source_identity.py", 59): "argument-check", ("_json.py", 43): "control-flow", ("introspect.py", 54): "argument-check",
    ("compile.py", 412): "predicate-helper",   # carried: compile.py:_unbound_by:RETURN_NONE:1
    ("schema.py", 659): "predicate-helper",   # carried: schema.py:wiki_drops_on:BOOL_RETURN:1
    ("schema.py", 686): "predicate-helper",   # RII-R2-01: schema.py:assertion_view:RETURN_NONE:1
    ("schema.py", 1451): "internal-invariant",   # RII-R2-01: schema.py:_check_assertion_view_partition:RAISE:1
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
e("compile.py", 422, "compile.bind.unbound", "0047", "§4d INV-R18 (R-II round 2's RII-01: recall serves no wiki body its own snapshot does not admit)", "withhold")
e("compile.py", 142, "compile.fence.disputed", "0047", "§4d INV-R18 (the in-flight fence withholds a body drawn on a fact challenged since)", "withhold")
e("compile.py", 194, "compile.grounded-inputs", "0004", "§4", "withhold")
e("diagnostics.py", 276, "diagnostics.send.not-consented", "0015", "§4", "withhold")
e("gate.py", 54, "gate.exclude-procedural", "0037", "V-EXTRACTOR-QUOTE-GATED", "withhold")
e("gate.py", 178, "gate.partition-parts", "0001", "§4", "withhold")
e("gate.py", 125, "gate.scoped-assertable.entitlement", "0011", "§4c", "withhold")
e("gate.py", 119, "gate.scoped-assertable.invisible", "0020", "§4a", "withhold")
e("gate.py", 122, "gate.scoped-assertable.third-party-shaped", "0020", "§4a", "withhold")
e("graph.py", 300, "graph.absorption.cross-scope", "0020", "§4a-iii", "withhold")
e("graph.py", 302, "graph.absorption.no-flattening-plan", "0021", "§4a", "withhold")
e("graph.py", 297, "graph.absorption.scope-unresolved", "0020", "§4a-iii", "withhold")
e("graph.py", 1388, "graph.collapse-for-render", "0012", "§4c", "withhold")
e("graph.py", 1313, "graph.collapse.acted", "0047", "§4e (collapse never hides a member carrying an act, nor one behind a withheld survivor)", "withhold")
e("graph.py", 368, "graph.correction.identity-mismatch", "0011", "§4b", "refuse")
e("graph.py", 380, "graph.correction.prior-not-active", "0011", "§4b", "refuse")
e("graph.py", 859, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 865, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 867, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 869, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 871, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 873, "graph.semantic-duplicate.keep", "0012", "§4c", "withhold")
e("graph.py", 439, "graph.src-revoked", "0022", "§4a", "withhold")
e("graph.py", 443, "graph.src-revoked", "0022", "§4a", "withhold")
e("graph.py", 1231, "graph.strictly-redundant", "0012", "§4c", "withhold")
e("graph.py", 194, "graph.supersession.receipt-boundary", "0014", "R10", "refuse")
e("graph.py", 220, "graph.supersession.replay-mismatch", "0014", "§4b", "refuse")
e("grounding.py", 243, "grounding.ungrounded", "0019", "§4", "downgrade")
e("ingest.py", 317, "ingest.basis-via-remember", "0037", "§4b", "refuse")
e("ingest.py", 378, "ingest.instructions-not-a-list", "0039", "§2a", "downgrade")
e("ingest.py", 306, "ingest.source-id-required", "0006", "§4 rule 9", "refuse")
e("mcp_server.py", 113, "mcp.closed-set.author", "0011", "§4d", "refuse")
e("mcp_server.py", 122, "mcp.closed-set.trust-field", "0011", "§4d", "refuse")
e("__init__.py", 1982, "memory.confirm.unknown-target", "0008", "§6c INV-Q2", "refuse")
e("__init__.py", 2215, "memory.correct.inactive-edge", "0011", "§4b", "refuse")
e("__init__.py", 2235, "memory.correct.procedural", "0037", "§4a-iii", "refuse")
e("__init__.py", 2281, "memory.correct.refused", "0011", "§4b", "refuse")
e("__init__.py", 1919, "memory.dispute.inactive-edge", "0003", "§4b", "refuse")
e("__init__.py", 1900, "memory.edge.unknown-target", "0041", "INV-5", "refuse")
e("__init__.py", 1891, "memory.feedback.attested-target", "0041", "§4b-ii INV-11 (derived episodes)", "refuse")
e("__init__.py", 932, "memory.recall.as-of-on-proactive", "0028", "§2c", "refuse")
e("__init__.py", 1053, "memory.recall.policy-with-as-of", "0027", "v13 §4c", "refuse")
e("__init__.py", 2091, "memory.record-outcome.actor-vocabulary", "0008", "§4", "refuse")
e("__init__.py", 2094, "memory.record-outcome.human-judgment", "0008", "§4", "refuse")
e("__init__.py", 2097, "memory.record-outcome.system-judgment", "0008", "§4", "refuse")
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
e("proactive.py", 160, "proactive.eligible", "0012", "§4", "withhold")
e("proactive.py", 88, "proactive.variant", "0012", "I8j", "withhold")
e("proactive.py", 92, "proactive.variant", "0012", "I8j", "withhold")
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
e("schema.py", 976, "schema.edge.assertable", "0001", "§4", "withhold")
e("schema.py", 922, "schema.edge.quarantined", "0001", "§4", "quarantine")
e("schema.py", 934, "schema.edge.use-only", "0001", "§4", "withhold")
e("schema.py", 958, "schema.edge.valid-now", "0028", "S2", "withhold")
e("schema.py", 1057, "schema.episode.active", "0022", "§4b-ii", "withhold")
e("schema.py", 1076, "schema.episode.assertable", "0001", "§4", "withhold")
e("schema.py", 1039, "schema.episode.quarantined", "0001", "§4", "quarantine")
e("schema.py", 1050, "schema.episode.use-only", "0001", "§4", "withhold")
e("schema.py", 1084, "schema.episode.valid-now", "0028", "S2", "withhold")
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
e("store/sqlite.py", 885, "store.act-counter.allocate", "0008", "§6f (v7: the never-reset act counter)", "refuse")
e("store/sqlite.py", 2263, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2275, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2283, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2290, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2326, "store.add-episode", "0009/0010", "X21", "refuse")
e("store/sqlite.py", 2307, "store.add-episode.owner", "0004", "v3.5 §2c (i): the persisted owner never changes (0008 §6d's guard)", "refuse")
e("store/sqlite.py", 3584, "store.confirm-notice.standing", "0041", "§11.6.6 (confirm_notice: a standing row is not pending)", "refuse")
e("store/sqlite.py", 3591, "store.confirm-notice.target-absent", "0041", "§11.6.6 (confirm_notice: a pending notice whose target is gone is inert)", "refuse")
e("store/sqlite.py", 3576, "store.confirm-notice.unknown", "0041", "§11.6.6 (confirm_notice: an unknown or another user's id, one refusal)", "refuse")
e("store/sqlite.py", 920, "store.confirm.active-challenge", "0047", "§4c INV-R13", "refuse")
e("store/sqlite.py", 995, "store.confirm.correlation", "0008", "C9", "refuse")
e("store/sqlite.py", 911, "store.confirm.not-assertable", "0008", "§6d", "refuse")
e("store/sqlite.py", 863, "store.confirm.request-digest", "0008", "C9", "refuse")
e("store/sqlite.py", 934, "store.confirm.source-redacted", "0045", "§4d INV-G10", "refuse")
e("store/sqlite.py", 906, "store.confirm.unknown-edge", "0008", "§6d", "refuse")
e("store/sqlite.py", 2111, "store.consolidation-contribution", "0014", "§2c", "refuse")
e("store/sqlite.py", 2119, "store.consolidation-contribution", "0014", "§2c", "refuse")
e("store/sqlite.py", 2152, "store.consolidation-contribution", "0014", "§2c", "refuse")
e("store/sqlite.py", 3369, "store.consolidation.abandon-live-lease", "0010", "X7", "refuse")
e("store/sqlite.py", 3174, "store.consolidation.contended", "0010", "X7/X11", "refuse")
e("store/sqlite.py", 3351, "store.consolidation.delete-not-current", "0010", "X21", "refuse")
e("store/sqlite.py", 3158, "store.consolidation.input-redacted", "0041", "§4b-ii INV-11", "refuse")
e("store/sqlite.py", 3205, "store.consolidation.renew-refused", "0010", "X7", "refuse")
e("store/sqlite.py", 3300, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3305, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3310, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3316, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3331, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3338, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3341, "store.consolidation.transition", "0010", "§4b", "refuse")
e("store/sqlite.py", 3219, "store.consolidation.write-not-current", "0010", "X23", "refuse")
e("store/sqlite.py", 1934, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 1938, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 1944, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 1949, "store.contribution", "0014", "§4b", "refuse")
e("store/sqlite.py", 1746, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1753, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1757, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1761, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1765, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1771, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1776, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/sqlite.py", 1780, "store.correction.authorisation", "0011", "§4b", "refuse")
e("store/data_migration.py", 409, "store.data-migration.inventory-integrity", "0044", "§4f / 0018 §4i D1", "refuse")
e("store/data_migration.py", 313, "store.data-migration.op-id-conflict", "0018", "§4i I32", "refuse")
e("store/data_migration.py", 505, "store.data-migration.read-refused", "0018", "§4i §4d", "refuse")
e("store/data_migration.py", 450, "store.data-migration.redacted-not-considered", "0044", "§4f.1 INV-A7", "withhold")
e("store/data_migration.py", 333, "store.data-migration.registry-changed", "0018", "§4i I25", "refuse")
e("store/data_migration.py", 458, "store.data-migration.withheld-revoked", "0044", "§4f.2 INV-A11", "withhold")
e("store/sqlite.py", 2387, "store.delete-episode.outcome", "0009", "§4c", "refuse")
e("store/sqlite.py", 2395, "store.delete-episode.reserved", "0010", "X21", "refuse")
e("store/sqlite.py", 1498, "store.edges.read-fence", "0001", "§4", "withhold")
e("store/sqlite.py", 4091, "store.embedding.delayed-writer", "0027", "§4f", "refuse")
e("store/sqlite.py", 4098, "store.embedding.stale-content", "0027", "§4f", "refuse")
e("store/sqlite.py", 4069, "store.embedding.txn-locked", "0041", "§4e (0007 §4c form)", "refuse")
e("store/sqlite.py", 2318, "store.episode.attested-redaction", "0041", "§4b-ii INV-11", "refuse")
e("store/sqlite.py", 2254, "store.episode.kind-not-recognised", "0041", "§2d-iv/§4h(ii) write path", "refuse")
e("store/sqlite.py", 2241, "store.episode.marker-introduced", "0041", "§4b INV-11's mirror", "refuse")
e("store/sqlite.py", 2249, "store.episode.retired-reason-not-registered", "0041", "§11.2 D1 (write path)", "refuse")
e("store/sqlite.py", 3387, "store.export.non-quiescent", "0010", "X-quiesce", "refuse")
e("store/sqlite.py", 2029, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2038, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2047, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2052, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2075, "store.flattening", "0021", "§4a", "refuse")
e("store/sqlite.py", 2504, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2509, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2513, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2519, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2526, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2533, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2554, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2559, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2563, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2571, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2575, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2579, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2585, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2604, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2616, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2646, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2843, "store.import-plan", "0009", "§4c", "refuse")
e("store/sqlite.py", 2721, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2728, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2751, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2787, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2796, "store.import.attested-redaction", "0041", "§4b-ii INV-11 at the import boundary (§4g)", "refuse")
e("store/sqlite.py", 2781, "store.import.episode-kind-not-recognised", "0041", "§2d-iv/§4h(ii) import boundary", "refuse")
e("store/sqlite.py", 2914, "store.import.notice-body-conflict", "0041", "§4g", "refuse")
e("store/sqlite.py", 2956, "store.import.notice-record-unredacted", "0041", "§11.6.6 (INV-RR12/RR14: a record an import creates, or a restore's held record, beside its notice must show it)", "refuse")
e("store/sqlite.py", 2977, "store.import.notice-record-unredacted", "0041", "§11.6.6 (INV-RR12/RR14: a record an import creates, or a restore's held record, beside its notice must show it)", "refuse")
e("store/sqlite.py", 3007, "store.import.notice-record-unredacted", "0041", "§11.6.6 (INV-RR12/RR14: a record an import creates, or a restore's held record, beside its notice must show it)", "refuse")
e("store/sqlite.py", 2711, "store.import.reason-not-registered", "0041", "§11.2 D1 (import boundary)", "refuse")
e("store/sqlite.py", 2765, "store.import.reason-not-registered", "0041", "§11.2 D1 (import boundary)", "refuse")
e("store/sqlite.py", 2757, "store.import.reserved-id", "0010", "X21 at the import, any owner (0004 v3.5 §2c (ii))", "refuse")
e("store/sqlite.py", 527, "store.journal.pre-epoch", "0029", "§4a", "refuse")
e("store/sqlite.py", 445, "store.journal.reason-not-dispositioned", "0030", "V-TOTAL", "refuse")
e("store/sqlite.py", 453, "store.journal.redaction-reason", "0041", "§4c/§11.2 D1", "refuse")
e("store/sqlite.py", 462, "store.journal.reinstatement-reason", "0029", "§4b-i (v12, INV-J1)", "refuse")
e("store/migration.py", 228, "store.migration.duplicate-outcome-chain", "0009", "§4c", "refuse")
e("store/migration.py", 86, "store.migration.postcondition", "0013", "§4f (v33, 0013-PA1: each step checked at the step)", "refuse")
e("store/migration.py", 322, "store.migration.version", "0013", "§4", "refuse")
e("store/migration.py", 386, "store.migration.version", "0013", "§4", "refuse")
e("store/migration.py", 414, "store.migration.version", "0013", "§4", "refuse")
e("store/migration.py", 440, "store.migration.version", "0013", "§4", "refuse")
e("store/migration.py", 496, "store.migration.version", "0013", "§4", "refuse")
e("store/migration.py", 529, "store.migration.version", "0013", "§4", "refuse")
e("store/sqlite.py", 3533, "store.notice.state-domain", "0041", "§11.6.6 (T4: the notice state's one writer)", "refuse")
e("store/schema_version.py", 2005, "store.open.invalid-version", "0007", "§4a", "refuse")
e("store/schema_version.py", 2077, "store.open.legacy", "0007", "§4h", "refuse")
e("store/schema_version.py", 2087, "store.open.legacy", "0007", "§4h", "refuse")
e("store/schema_version.py", 2103, "store.open.legacy", "0007", "§4h", "refuse")
e("store/schema_version.py", 2113, "store.open.legacy", "0007", "§4h", "refuse")
e("store/schema_version.py", 1992, "store.open.locked", "0007", "§4a", "refuse")
e("store/schema_version.py", 2009, "store.open.newer", "0007", "§4a", "refuse")
e("store/schema_version.py", 1979, "store.open.runtime-unsupported", "0007", "§4a-viii", "refuse")
e("store/schema_version.py", 1891, "store.open.unaccepted-shape", "0007", "§4a-v", "refuse")
e("store/schema_version.py", 1898, "store.open.unaccepted-shape", "0007", "§4a-v", "refuse")
e("store/schema_version.py", 1906, "store.open.unaccepted-shape", "0007", "§4a-v", "refuse")
e("store/sqlite.py", 2446, "store.outcome.context-ref", "0009", "§4c", "refuse")
e("store/sqlite.py", 2374, "store.read.input-claimed", "0010", "§4b", "withhold")
e("store/sqlite.py", 2371, "store.read.output-not-visible", "0010", "§4b", "withhold")
e("store/sqlite.py", 3733, "store.redact.both-or-neither", "0041", "§4a/INV-5", "refuse")
e("store/sqlite.py", 3806, "store.redact.disposition-changed", "0041", "§4h(i)", "refuse")
e("store/sqlite.py", 3778, "store.redact.input-claimed", "0041/0010", "X21", "refuse")
e("store/sqlite.py", 3927, "store.redact.nothing-to-redact", "0041", "§4b-ii (round 11: the owner's ruling, nothing to redact)", "refuse")
e("store/sqlite.py", 3739, "store.redact.reason-not-registered", "0041", "§11.2", "refuse")
e("store/sqlite.py", 3752, "store.redact.target", "0041", "§4a/INV-5", "refuse")
e("store/sqlite.py", 652, "store.redacted-reason.not-a-redaction", "0041", "§11.2 (only a redaction writes `redacted`)", "refuse")
e("store/sqlite.py", 841, "store.registry.request-redacted", "0008", "§6g (v7: the terminal rule, INV-Q7)", "refuse")
e("store/sqlite.py", 870, "store.registry.result-missing", "0008", "§6c (v7: replay reconstructs from result_ref; a dangling ref is an integrity conflict)", "refuse")
e("store/sqlite.py", 844, "store.registry.verb-held", "0008", "§6c (v7: the registry first; a held id names its verb)", "refuse")
e("store/sqlite.py", 1074, "store.reply.actor", "0047", "§2c who wrote it (a closed label until 0050)", "refuse")
e("store/sqlite.py", 1070, "store.reply.kind", "0047", "§2c INV-R8", "refuse")
e("store/sqlite.py", 1083, "store.reply.marker", "0047/0041", "§2c INV-R7 / 0041 INV-RR1", "refuse")
e("store/sqlite.py", 1104, "store.reply.procedural-edge", "0047", "§4d ruling INV-R19", "refuse")
e("store/sqlite.py", 1099, "store.reply.redacted-edge", "0047", "§0 INV-R9", "refuse")
e("store/sqlite.py", 1037, "store.reply.request-digest", "0047/0008", "§4b INV-R15/R24 (0008 §6c)", "refuse")
e("store/sqlite.py", 1116, "store.reply.resolve-repeat", "0047", "§4b INV-R14", "refuse")
e("store/sqlite.py", 1144, "store.reply.resolve-repeat", "0047", "§4b INV-R14", "refuse")
e("store/sqlite.py", 1112, "store.reply.resolve-target", "0047", "§4b INV-R14", "refuse")
e("store/sqlite.py", 1044, "store.reply.result-missing", "0008/0047", "§6c (reply: replay reconstructs from result_ref; a dangling ref is an integrity conflict)", "refuse")
e("store/sqlite.py", 1080, "store.reply.shape", "0047", "§4b the closed request (research's T10a F1)", "refuse")
e("store/sqlite.py", 1094, "store.reply.unknown-edge", "0047", "§2c INV-R9", "refuse")
e("store/revocation.py", 140, "store.revocation.integrity", "0022", "§4c", "refuse")
e("store/revocation.py", 139, "store.revocation.ordinal-collision", "0022", "§4c", "refuse")
e("store/revocation.py", 345, "store.revocation.revoke-reason-not-registered", "0041", "§11.2 D1 (revoke)", "refuse")
e("store/revocation_sweep.py", 360, "store.revocation.self-linkage", "0022", "§4c", "refuse")
e("store/revocation_sweep.py", 232, "store.revocation.source-not-revocable", "0022", "I13", "refuse")
e("store/revocation.py", 73, "store.revocation.unknown-state", "0022", "R5-1", "refuse")
e("store/schema_version.py", 1599, "store.runtime-refused", "0007", "§4g.6 4a (attested / verified / refused, by measurement; both gates' one decision)", "refuse")
e("store/sqlite.py", 1303, "store.supersession.absorb-acted", "0047", "§4e INV-R17 (a plan absorbing an acted prior is stale)", "refuse")
e("store/sqlite.py", 1674, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1692, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1708, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1713, "store.supersession.integrity", "0014", "§4b", "refuse")
e("store/sqlite.py", 1797, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 1819, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 1827, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 1846, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 1851, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 1856, "store.supersession.plan", "0014/0019", "§4b", "refuse")
e("store/sqlite.py", 350, "store.txn.locked", "0013", "§5b", "refuse")
e("store/sqlite.py", 375, "store.txn.locked-retry", "0013", "§5b", "refuse")
e("store/data_migration.py", 578, "store.undo.ambiguous-outcome", "0044", "§4i (research's T7 annotation: no undo lookup chooses between two)", "refuse")
e("store/data_migration.py", 634, "store.undo.correlation", "0008", "C9 (the C8 fallback)", "refuse")
e("store/data_migration.py", 611, "store.undo.edge-unavailable", "0044", "§4i.2", "refuse")
e("store/data_migration.py", 588, "store.undo.no-outcome", "0044", "§4i.2 INV-A12", "refuse")
e("store/data_migration.py", 605, "store.undo.not-applicable", "0044", "§4i.2 INV-A12", "refuse")
e("store/data_migration.py", 593, "store.undo.not-restored", "0044", "§4i.2 INV-A12", "refuse")
e("store/data_migration.py", 649, "store.undo.request-digest", "0008", "C9", "refuse")
e("store/data_migration.py", 656, "store.undo.result-missing", "0008", "§6c (v7: replay reconstructs from result_ref; a dangling ref is an integrity conflict)", "refuse")
e("store/data_migration.py", 600, "store.undo.testimony", "0044", "§4i.2 R2-05 INV-A17", "refuse")
e("store/sqlite.py", 678, "store.upsert.attested-redaction", "0041", "§4b-ii INV-11", "refuse")
e("store/sqlite.py", 710, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 716, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 726, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 739, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 745, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 754, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 765, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 780, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 790, "store.upsert.immutable", "0008/0019/0037/0045", "§6d/V-IMMUTABLE/INV-G13", "refuse")
e("store/sqlite.py", 692, "store.upsert.invalidation-reason-not-registered", "0041", "§11.2 D1 (write path)", "refuse")
e("store/sqlite.py", 669, "store.upsert.marker-introduced", "0041", "§4b INV-11's mirror", "refuse")
e("store/sqlite.py", 697, "store.upsert.relation-only-quarantine", "0041", "§4h(i)", "refuse")
e("telemetry.py", 545, "telemetry.collector.not-enabled", "0015", "§4", "withhold")
e("telemetry.py", 374, "telemetry.flush.invalid-consent", "0015", "§4", "withhold")
e("telemetry.py", 380, "telemetry.flush.not-enabled", "0015", "§4", "withhold")
e("telemetry.py", 345, "telemetry.preview.invalid-consent", "0015", "§4", "withhold")
e("telemetry.py", 350, "telemetry.preview.not-enabled", "0015", "§4", "withhold")
