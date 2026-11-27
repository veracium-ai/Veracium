#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0055_implementation_mutants.py::test_the_table_check_refuses_each_tampered_table
"""0055's invariants demonstrated red against the IMPLEMENTATION (the build's owed item "RED demonstrations for the
integration checks, by mutation"): every row is the RED its invariant's row in the spec names, made as a code edit to
the product and run by the shared protocol (specs/evidence/mutation_protocol.py) on a copy of the tracked tree, killed
by assertion in EVERY one of its named cells, with an HONEST probe from the same test files that still passes under it.
Beside them, per mutated file, a NO-OP control whose cells must all pass, and one classifier negative control.

The named cells are MEASURED, not chosen: the cells of the three 0055 test files (the invariants, the recogniser, and
the I19 sweep) that fail under the edit by a qualifying kind (specs/evidence/mutation_kinds.py). A cell that fails
under the edit by a crash instead is not named (it would make the row unclassifiable), and the row's `what` says how
many there were. Measured 2026-11-23 at the build's test files; two rows survived the first measurement and each
exposed a gap closed in the same change: I7's no-query briefing never rendered its legacy record (a durable fact; the
briefing renders transient ones), and nothing held D3's reason check before the identity digest (now
test_d3_the_reason_is_checked_before_the_identity_digest); I20's only failing cell failed by a KeyError and now
compares with `.get`.

The recogniser's own mutants (research's reference model: `evidence/out/mutants.out`, the table's) and I9's quadratic
mutant (in tests/test_0055_recogniser.py) are not repeated here; the product rows I2/I3 below are the implementation's.

    $PY specs/evidence/0055/implementation_mutants.py --check     # fast: definitions, anchors, digests
    TMPDIR=/dev/shm $PY specs/evidence/0055/implementation_mutants.py --write
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

TABLE = HERE / "implementation" / "mutation-table.json"
SELF = "specs/evidence/0055/implementation_mutants.py"
SUBJECT = "implementation"
CELL_FILES = ("tests/test_0055_invariants.py", "tests/test_0055_recogniser.py", "tests/test_0055_i19_digest_sweep.py",
              "tests/test_0055_r4_closure.py", "tests/test_0055_r5_closure.py")
MUTATED = ("src/veracium/credentials.py", "src/veracium/__init__.py", "src/veracium/ingest.py",
           "src/veracium/portability.py", "src/veracium/proactive.py", "src/veracium/store/sqlite.py",
           "src/veracium/mcp_server.py", "src/veracium/graph.py", "src/veracium/cli.py", "src/veracium/semantic.py",
           # round 4's fixes (R4-02 compile, R4-03 the receipt, R4-06 diagnostics, A1 the finder)
           "src/veracium/compile.py", "src/veracium/trust_tools.py", "src/veracium/diagnostics.py",
           "src/veracium/credential_finder.py",
           # round 5 (the carrier-to-boundary table's findings: why's --find hit)
           "src/veracium/why.py",
           # round 5's RETURN (dev's library audit: introspect's report)
           "src/veracium/introspect.py")
DIGESTED = MUTATED + CELL_FILES + ("tests/support_0055_i19.py", "specs/evidence/0055/digests.json",
                                   "specs/evidence/0055/vectors.py", "specs/evidence/mutation_protocol.py",
                                   _protocol.KINDS, SELF)

# (id, kind, file, [(anchor, replacement)], named cells, honest nodes, reason, what)
MUTANTS = [
    ('I3-single-pass-mask', 'product', 'src/veracium/credentials.py',
     [('    out, held, passes = text, [], 0\n    found = scan(out)\n    while found:\n        if passes >= MAX_PASSES:', '    out, held, passes = text, [], 0\n    found = scan(out)\n    if found:\n        if passes >= MAX_PASSES:')],
     ['tests/test_0055_invariants.py::test_i8_every_sink_holds_only_field_names_class_names_and_exact_counts', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[C16]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[C5]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[C6]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[D3]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[D4]', 'tests/test_0055_recogniser.py::test_mask_scans_at_most_five_times', 'tests/test_0055_recogniser.py::test_the_completed_output_is_inert_and_text_idempotent', 'tests/test_0055_recogniser.py::test_the_fallback_is_reached_and_withholds_the_whole_value', 'tests/test_0055_recogniser.py::test_the_product_equals_the_reference_on_a_seeded_fuzz'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'mask() makes one pass and returns, inert or not (I3: a single-pass mask, C5/C6) [measured: 2 more cell(s) fail by a crash, not named]'),
    ('I3-fallback-keeps-the-text', 'product', 'src/veracium/credentials.py',
     [('        return PLACEHOLDER.format(cls=FALLBACK_CLASS), {FALLBACK_CLASS: 1}\n    rep: dict', '        return out, {FALLBACK_CLASS: 1}\n    rep: dict')],
     ['tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[D4]', 'tests/test_0055_recogniser.py::test_the_completed_output_is_inert_and_text_idempotent', 'tests/test_0055_recogniser.py::test_the_fallback_is_reached_and_withholds_the_whole_value', 'tests/test_0055_recogniser.py::test_the_product_equals_the_reference_on_a_seeded_fuzz'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     "the bound's fallback returns the partly masked text instead of withholding the value (I3, D4) [measured: 2 more cell(s) fail by a crash, not named]"),
    ('I2-no-stop-list', 'product', 'src/veracium/credentials.py',
     [('    if not w or w in STOP or _MASKED_VALUE', '    if not w or _MASKED_VALUE')],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[K39]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[K43]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[K6]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[X6]', 'tests/test_0055_recogniser.py::test_the_product_equals_the_reference_on_a_seeded_fuzz'],
     ['tests/test_0055_invariants.py::test_i20_record_procedure_keeps_its_str_and_the_twin_reports'], None,
     "the labelled rule's stop list removed, so a stop word after a label is withheld (I2, K6)"),
    ('I4-identifier-not-refused', 'product', 'src/veracium/__init__.py',
     [('                if cls is not None:\n                    raise self._cred_refused(user_id, op, field_name, cls)\n        out: list = []', '                if cls is not None:\n                    continue\n        out: list = []')],
     ['tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r11:c[-identity_digest-]--copied-from-a-closed-ledger-row--s:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].provenance.source_id-[remember--procedur:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r34:record.provenance.origin--.source_id-of-a-held-record--_:extra-34-same-scope]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r35:e.provenance.origin--e.provenance.source_id-for-EVERY-ed:extra-35-chain-src]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r5:target--resolve-only--a-reply-id:reply-resolve]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r6:contributor.provenance.source_id:run]', 'tests/test_0055_invariants.py::test_i20_record_procedure_keeps_its_str_and_the_twin_reports', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[confirm.correlation_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[confirm.source_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[correct.actor]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[correct.corrected_value]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[correct.evidence_ref]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[correct.source_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[dispute.actor]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[dispute.source_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[record_outcome.context_ref]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[record_outcome.evidence_ref]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[record_procedure.evidence_ref]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[record_procedure.source_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[remember.event_type]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[remember.evidence_ref]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[remember.source_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[reply.correlation_id]', 'tests/test_0055_r4_closure.py::test_r4_01_reviewer_identifiers_are_rejected_before_conversion[str-event_type]', 'tests/test_0055_r4_closure.py::test_r4_01_reviewer_identifiers_are_rejected_before_conversion[str-evidence_ref]'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'an identifier argument with a shape passes the ingress screen instead of refusing the call (I4) [measured: 2 more cell(s) fail by a crash, not named]'),
    ('I5-model-output-screen-removed', 'product', 'src/veracium/ingest.py',
     [('        _shaped = _model_triple_class(t)\n        if _shaped is not None:', '        _shaped = None\n        if _shaped is not None:')],
     ['tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].object-[remember--procedure--absorption:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].relation-[remember--procedure--absorptio:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].subject-[remember--procedure--absorption:run]'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     "the extractor's triples are written without the model-output screen (I5) [measured: 1 more cell(s) fail by a crash, not named]"),
    ('I6-restore-masks-without-the-flag', 'product', 'src/veracium/portability.py',
     [('    if restore and withheld and not withhold:', '    if False:')],
     ['tests/test_0055_invariants.py::test_i6_plain_import_withholds_and_restore_refuses_unless_flagged'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'a restore whose free text carries shapes masks it without withhold_credentials=True (I6)'),
    ('I7-proactive-path-unmasked', 'product', 'src/veracium/proactive.py',
     [('    _edges = [_cred.masked_edge(e) for e in store.edges(user_id) if e.id not in _redacted_edges]', '    _edges = [e for e in store.edges(user_id) if e.id not in _redacted_edges]')],
     ['tests/test_0055_invariants.py::test_i7_no_legacy_credential_reaches_a_model_or_a_tool_result'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'the no-query (proactive) read path left unmasked (I7: one read path left unmasked)'),
    ('I8-formatter-echoes-the-message', 'product', 'src/veracium/credentials.py',
     [('    name = type(exc).__name__\n    field = exc.field if isinstance(exc, ArgumentRefused) else None', '    return str(exc)\n    name = type(exc).__name__\n    field = exc.field if isinstance(exc, ArgumentRefused) else None')],
     ['tests/test_0055_invariants.py::test_i17_served_and_cli_errors_never_echo_the_argument'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     "the one outward formatter returns the exception's own message, which may echo the input (I8, I17)"),
    ('I12-diagnostic-digest-over-raw-text', 'product', 'src/veracium/ingest.py',
     [('    b = _cred.mask(text)[0].encode("utf-8")', '    b = text.encode("utf-8")')],
     ['tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[rP:the-provider-s-answer--its-retry-answer--and-the-provide:provider-answer]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[rP:the-provider-s-answer--its-retry-answer--and-the-provide:provider-error]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[rP:the-provider-s-answer--its-retry-answer--and-the-provide:provider-retry]', 'tests/test_0055_invariants.py::test_i19_the_diagnostics_digest_is_over_masked_provider_text'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'answer_len/answer_sha16 (and the provider-error digest) over the raw provider text (I12, I19 row P)'),
    ('I13-guard-on-present', 'product', 'src/veracium/store/sqlite.py',
     [('                hit = _cred_introduced(edge.model_dump(mode="json"),\n                                       json.loads(prior[1]) if prior is not None else None)', '                hit = _cred_introduced(edge.model_dump(mode="json"), None)')],
     ['tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r10:contributor_ref---an-id-in-the-absorbed-prior-s-transiti:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_invalidations[].edge_id-[remember--procedure]:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].agreement.markers-[remember--procedure:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].id-[remember--procedure--absorption-only:extra-1-upserts-procedure-id]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].id-[remember--procedure--absorption-only:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].original_relation-[remember--procedure:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].provenance.evidence_ref-[remember--proce:extra-1-upserts-procedure-evidence_ref]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].provenance.evidence_ref-[remember--proce:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].provenance.origin-[remember--procedure:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].src-[remember--procedure--absorption-onl:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].supersedes-[remember--procedure--absorpt:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r2:contribution_drafts[].contributor_id:extra-2-procedure-contributor_id]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r2:contribution_drafts[].contributor_id:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r3:e.id-of-each-scoped-edge:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r6:resolve_origin-contributor.provenance.origin--local:extra-6-origin-sourceless]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r7:contributor.provenance.evidence_ref:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r7:resolve_origin-contributor.provenance.origin--local:run]'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'the store guard screens every PRESENT string, not the introduced ones (I13: dispute of a legacy row fails) [measured: 2 more cell(s) fail by a crash, not named]'),
    ('I15-discarded-count-not-recorded', 'product', 'src/veracium/mcp_server.py',
     [('    _record_discarded(mem, user_id, "remember", r)', '    pass')],
     ['tests/test_0055_invariants.py::test_i15_the_discarded_raise_count_reaches_the_audit_log'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'remember_impl strips provenance_raises_discarded without recording it to the AuditLog (I15)'),
    ('I16-absorption-note-unmasked', 'product', 'src/veracium/graph.py',
     [('            noted.note = _cred.mask((f"{noted.note}; " if noted.note else "")\n                                    + f"absorbed_by:{incoming.id} (restated as {incoming.object!r})")[0]', '            noted.note = ((f"{noted.note}; " if noted.note else "")\n                          + f"absorbed_by:{incoming.id} (restated as {incoming.object!r})")')],
     ['tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].note-[remember--procedure--absorption-on:run]'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     "the absorption's rewritten note (composed from the stored note) written unmasked (I16 rule 1)"),
    ('I17-served-formatter-bypassed', 'product', 'src/veracium/mcp_server.py',
     [('                raise ValueError(_cred.outward_text(exc)) from exc', '                raise')],
     ['tests/test_0055_invariants.py::test_i17_served_and_cli_errors_never_echo_the_argument'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'an exception escaping a served MCP tool reaches the SDK with its own message (I17 E1)'),
    ('I17-hide-input-unset', 'product', 'src/veracium/mcp_server.py',
     [('    model_config = ConfigDict(hide_input_in_errors=True)', '    model_config = ConfigDict(hide_input_in_errors=False)')],
     ['tests/test_0055_invariants.py::test_i17_served_and_cli_errors_never_echo_the_argument'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'the served argument models echo input_value= in validation errors (I17 E2)'),
    ('I18-second-scan-trusted', 'product', 'src/veracium/cli.py',
     [('        after = cf.scan(store, args.user)', '        after = []')],
     ['tests/test_0055_invariants.py::test_i18_redact_removes_what_0041_can_and_reports_the_residual'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     '`veracium credentials redact` trusts the 0041 receipt instead of re-scanning (I18)'),
    ('I19-content-digest-unmasked', 'product', 'src/veracium/semantic.py',
     [('    # legacy text; on text with no credential shape the mask is the identity, so every existing digest is unchanged\n    edge = _cred.masked_edge(edge)', '    # legacy text; on text with no credential shape the mask is the identity, so every existing digest is unchanged\n    pass')],
     ['tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r28:edge.note:backfill-note]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r28:edge.object:backfill-object]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r28:edge.relation:backfill-relation]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r28:edge.subject:backfill-subject]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r29:live.note:backfill-note]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r29:live.object:backfill-object]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r29:live.relation:backfill-relation]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r29:live.subject:backfill-subject]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r30:live.note:recall-note]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r30:live.object:recall-object]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r30:live.relation:recall-relation]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r30:live.subject:recall-subject]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r31:cur.note:asof-cur-note]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r31:cur.object:asof-cur-object]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r31:cur.relation:asof-cur-relation]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r31:cur.subject:asof-cur-subject]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r31:snap.note:asof-snap-note]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r31:snap.object:asof-snap-object]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r31:snap.relation:asof-snap-relation]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r31:snap.subject:asof-snap-subject]', 'tests/test_0055_invariants.py::test_i19_the_embedding_digest_and_input_are_masked'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'content_digest over raw legacy text (I19, census F row 13 / map rows 28-31; W4)'),
    ('I7-embedder-sees-raw-text', 'product', 'src/veracium/semantic.py',
     [('    is a provider, so a legacy credential never reaches it)."""\n    edge = _cred.masked_edge(edge)', '    is a provider, so a legacy credential never reaches it)."""\n    pass')],
     ['tests/test_0055_invariants.py::test_i19_the_embedding_digest_and_input_are_masked', 'tests/test_0055_invariants.py::test_i7_no_legacy_credential_reaches_a_model_or_a_tool_result'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     "embedded_text, the embedder's input, over raw legacy text (I7, the embedder egress)"),
    ('I19-correct-hashes-the-raw-note', 'product', 'src/veracium/__init__.py',
     [('                copied_note, nrep = _cred.mask(edge.note) if edge.note else (edge.note, {})', '                copied_note, nrep = (edge.note, {})')],
     ['tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:incoming_edge.agreement.markers-[correct]:correct_markers]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:incoming_edge.note-[correct]:run]'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     "correct copies the prior's note into the plan unmasked, so plan_correction hashes it (I19, W5) [measured: 2 more cell(s) fail by a crash, not named]"),
    ('I19-reason-after-the-digest', 'product', 'src/veracium/__init__.py',
     [('        _rv.check_reason(action, reason)        # specs/0055 D3: the reason, too, before the digest\n        digest = digest_of(origin, source_id, self.store.local_origin())', '        digest = digest_of(origin, source_id, self.store.local_origin())\n        _rv.check_reason(action, reason)')],
     ['tests/test_0055_i19_digest_sweep.py::test_d3_the_reason_is_checked_before_the_identity_digest'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     "revoke_source's reason check moved after the identity digest (I19, D3's order)"),
    ('I19-unknown-shape-digested', 'product', 'src/veracium/__init__.py',
     [('        field_name, cls = shaped[0]\n        raise self._cred_refused(user_id, op, field_name, cls)', '        return origin, source_id')],
     ['tests/test_0055_invariants.py::test_i19_revoke_source_refuses_an_unknown_shape_before_any_digest'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'D3 accepts an unknown credential-shaped source and digests it (I19: an unknown shape refuses first)'),
    ('I20-twin-omitted-on-the-served-surface', 'product', 'src/veracium/mcp_server.py',
     [('    out = {"ok": True, "edge_id": rep["edge_id"]}\n    if rep.get("credentials_withheld"):\n        out["credentials_withheld"] = rep["credentials_withheld"]', '    out = {"ok": True, "edge_id": rep["edge_id"]}')],
     ['tests/test_0055_invariants.py::test_i20_record_procedure_keeps_its_str_and_the_twin_reports'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'the served record_procedure drops the report the twin returns (I20)'),
    ('I19-F6-stored-reason-quoted', 'product', 'src/veracium/store/sqlite.py',
     [('{_cred.mask_text(edge.invalidation_reason)!r}, which is not "', '{edge.invalidation_reason!r}, which is not "')],
     ['tests/test_0055_invariants.py::test_i19_f6_a_store_refusal_masks_the_value_it_quotes[edge-reupsert]'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     "the store's upsert refusal quotes a stored invalidation reason unmasked (I19-F6, fixed at v0.5.5; "
     "measured: exactly this cell fails, by assertion)"),
    ('I1-v056-word-boundary', 'product', 'src/veracium/credentials.py',
     [['    ("aws_access_key_id",      r"(?<![A-Za-z0-9])(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}(?![A-Za-z0-9])"),\n', '    ("aws_access_key_id",      r"\\b(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\\b"),\n'], ['    ("github_token",           r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{36,255}(?![A-Za-z0-9])"),\n', '    ("github_token",           r"\\bgh[pousr]_[A-Za-z0-9]{36,255}\\b"),\n'], ['    ("github_token",           r"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{22,255}(?![A-Za-z0-9])"),\n', '    ("github_token",           r"\\bgithub_pat_[A-Za-z0-9_]{22,255}\\b"),\n'], ['    ("gitlab_token",           r"(?<![A-Za-z0-9])glpat-[A-Za-z0-9_\\-]{20,}"),\n', '    ("gitlab_token",           r"\\bglpat-[A-Za-z0-9_\\-]{20,}"),\n'], ['    ("slack_token",            r"(?<![A-Za-z0-9])xox[abposr]-[A-Za-z0-9-]{10,}"),\n', '    ("slack_token",            r"\\bxox[abposr]-[A-Za-z0-9-]{10,}"),\n'], ['    ("stripe_key",             r"(?<![A-Za-z0-9])(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}"),\n', '    ("stripe_key",             r"\\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}"),\n'], ['    ("anthropic_key",          r"(?<![A-Za-z0-9])sk-ant-[A-Za-z0-9_\\-]{20,}"),\n', '    ("anthropic_key",          r"\\bsk-ant-[A-Za-z0-9_\\-]{20,}"),\n'], ['    ("openai_key",             r"(?<![A-Za-z0-9])sk-(?!ant-)(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\\-]{20,}"),\n', '    ("openai_key",             r"\\bsk-(?!ant-)(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\\-]{20,}"),\n'], ['    ("google_api_key",         r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_\\-]{35}"),\n', '    ("google_api_key",         r"\\bAIza[0-9A-Za-z_\\-]{35}"),\n'], ['    ("google_oauth_secret",    r"(?<![A-Za-z0-9])GOCSPX-[A-Za-z0-9_\\-]{28}"),\n', '    ("google_oauth_secret",    r"\\bGOCSPX-[A-Za-z0-9_\\-]{28}"),\n'], ['    ("huggingface_token",      r"(?<![A-Za-z0-9])hf_[A-Za-z0-9]{34,}"),\n', '    ("huggingface_token",      r"\\bhf_[A-Za-z0-9]{34,}"),\n'], ['    ("npm_token",              r"(?<![A-Za-z0-9])npm_[A-Za-z0-9]{36}(?![A-Za-z0-9])"),\n', '    ("npm_token",              r"\\bnpm_[A-Za-z0-9]{36}\\b"),\n'], ['    ("pypi_token",             r"(?<![A-Za-z0-9])pypi-AgEIcHlwaS5vcmc[A-Za-z0-9_\\-]{50,}"),\n', '    ("pypi_token",             r"\\bpypi-AgEIcHlwaS5vcmc[A-Za-z0-9_\\-]{50,}"),\n'], ['    ("sendgrid_key",           r"(?<![A-Za-z0-9])SG\\.[A-Za-z0-9_\\-]{22}\\.[A-Za-z0-9_\\-]{43}"),\n', '    ("sendgrid_key",           r"\\bSG\\.[A-Za-z0-9_\\-]{22}\\.[A-Za-z0-9_\\-]{43}"),\n'], ['    ("digitalocean_token",     r"(?<![A-Za-z0-9])do[por]_v1_[a-f0-9]{64}(?![A-Za-z0-9])"),\n', '    ("digitalocean_token",     r"\\bdo[por]_v1_[a-f0-9]{64}\\b"),\n'], ['    ("jwt",                    r"(?<![A-Za-z0-9])eyJ[A-Za-z0-9_\\-]{8,}\\.eyJ[A-Za-z0-9_\\-]{8,}\\.[A-Za-z0-9_\\-]{8,}"),\n', '    ("jwt",                    r"\\beyJ[A-Za-z0-9_\\-]{8,}\\.eyJ[A-Za-z0-9_\\-]{8,}\\.[A-Za-z0-9_\\-]{8,}"),\n'], ['    ("url_userinfo_password",  r"(?<![A-Za-z0-9])[a-zA-Z][a-zA-Z0-9+.\\-]{0,31}://[^\\s:/@]{1,256}:[^\\s@/]{1,256}@[^\\s/]+"),\n', '    ("url_userinfo_password",  r"\\b[a-zA-Z][a-zA-Z0-9+.\\-]{0,31}://[^\\s:/@]{1,256}:[^\\s@/]{1,256}@[^\\s/]+"),\n'], ['    ("auth_header",            r"(?i)(?<![A-Za-z0-9])authorization\\s*:\\s*(?:basic|bearer|token)\\s+[A-Za-z0-9._~+/\\-]{16,}=*"),\n', '    ("auth_header",            r"(?i)\\bauthorization\\s*:\\s*(?:basic|bearer|token)\\s+[A-Za-z0-9._~+/\\-]{16,}=*"),\n'], ['    ("bearer_token",           r"(?i)(?<![A-Za-z0-9])bearer\\s+[A-Za-z0-9._~+/\\-]{20,}=*"),\n', '    ("bearer_token",           r"(?i)\\bbearer\\s+[A-Za-z0-9._~+/\\-]{20,}=*"),\n'], ['    ("veracium_preview_token", r"(?<![A-Za-z0-9])tt1\\.eyJ[A-Za-z0-9_\\-]{8,}\\.[A-Za-z0-9_\\-]{20,}"),\n', '    ("veracium_preview_token", r"\\btt1\\.eyJ[A-Za-z0-9_\\-]{8,}\\.[A-Za-z0-9_\\-]{20,}"),\n']],
     ['tests/test_0055_invariants.py::test_i1_no_secret_byte_survives_any_free_text_field[remember]', 'tests/test_0055_invariants.py::test_i1_no_secret_byte_survives_any_free_text_field[record_procedure.summary]', 'tests/test_0055_invariants.py::test_i1_no_secret_byte_survives_any_free_text_field[record_procedure.note]', 'tests/test_0055_invariants.py::test_i1_no_secret_byte_survives_any_free_text_field[dispute.reason]', 'tests/test_0055_invariants.py::test_i1_no_secret_byte_survives_any_free_text_field[reply.text]', 'tests/test_0055_invariants.py::test_i1_no_secret_byte_survives_any_free_text_field[record_outcome.corrected_value]', 'tests/test_0055_invariants.py::test_i12_neither_the_provider_nor_the_degrade_callback_sees_a_value_or_its_sha16', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G1]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G2]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G3]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G4]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G5]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G6]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G7]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G8]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G9]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G10]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G11]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G12]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G13]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G14]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G15]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G16]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G17]', 'tests/test_0055_recogniser.py::test_every_row_matches_the_reference_and_its_exact_report[G18]', 'tests/test_0055_recogniser.py::test_the_product_equals_the_reference_on_a_seeded_fuzz'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     "v0.5.6's structural patterns, the superseded implementation: a regular-expression word boundary, so a token glued by `_` or written against CJK text is stored (I1, §4a's token boundary, G1-G18) [measured: 1 more cell(s) fail by a crash, not named]"),
]

# ---- round 4's RETURN (coordination a421b28): one mutant per fix, each the fix reverted (research's addition 2) ----
_R4 = "tests/test_0055_r4_closure.py::"
MUTANTS += [
    ('R4-01-no-type-gate', 'product', 'src/veracium/__init__.py',
     [('        for field_name, value in (*ids, *free):\n            if value is not None and not isinstance(value, str):',
       '        for field_name, value in ():\n            if value is not None and not isinstance(value, str):')],
     ['tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[confirm.correlation_id]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[confirm.source_id]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[correct.actor]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[correct.corrected_value]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[correct.evidence_ref]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[correct.source_id]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[dispute.actor]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[dispute.reason]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[dispute.source_id]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_outcome.context_ref]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_outcome.corrected_value]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_outcome.evidence_ref]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_procedure.evidence_ref]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_procedure.note]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_procedure.source_id]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_procedure.summary]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_procedure_report.evidence_ref]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_procedure_report.note]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_procedure_report.source_id]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[record_procedure_report.summary]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[remember.event_text]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[remember.event_type]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[remember.evidence_ref]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[remember.source_id]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[reply.correlation_id]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[reply.target]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[reply.text]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[undo_restoration.correlation_id]', 'tests/test_0055_r4_closure.py::test_r4_01_reviewer_identifiers_are_rejected_before_conversion[bytes-event_type]', 'tests/test_0055_r4_closure.py::test_r4_01_reviewer_identifiers_are_rejected_before_conversion[bytes-evidence_ref]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "_cred_ingress admits a non-str identifier or free text again (round 4's R4-01: the isinstance(str) gate)"),
    ('R4-02-cache-unmasked', 'product', 'src/veracium/compile.py',
     [('    return _cred.mask_text(_split_envelope(row[0])[1])', '    return _split_envelope(row[0])[1]')],
     ['tests/test_0055_r4_closure.py::test_r4_02_a_fresh_cached_body_is_masked_on_every_served_read[library-legacy-shaped]', 'tests/test_0055_r4_closure.py::test_r4_02_the_provider_free_reader_of_a_fresh_cache_is_masked[legacy-shaped]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "ensure_wiki returns a FRESH cached body unmasked again (round 4's R4-02) [re-measured at round 5's RETURN: the served cells also pass under served_result's projection, a second layer over the same leak; the library cells name the row]"),
    ('R4-03-receipt-raw-id', 'product', 'src/veracium/trust_tools.py',
     [('None if record is None else self._locator(record.id), "text": text,',
       'None if record is None else record.id, "text": text,')],
     ['tests/test_0055_r4_closure.py::test_r4_03_render_receipts_use_the_locator_on_every_exit'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "RenderReceipt.admit carries the stored id raw again (round 4's R4-03 and S2: find_facts, recall, proactive) [re-measured at round 5's RETURN: the served cells also pass under served_result's projection, a second layer over the same leak; the library cells name the row]"),
    ('R4-03-import-refusal-raw-id', 'product', 'src/veracium/portability.py',
     [('"procedural_refusals": _procedural_locators(procedural_refusals, credential_report),',
       '"procedural_refusals": procedural_refusals,')],
     ['tests/test_0055_r4_closure.py::test_r4_03_early_import_refusals_use_the_locator[duplicate-import-shaped]', 'tests/test_0055_r4_closure.py::test_r4_03_early_import_refusals_use_the_locator[procedural-import-shaped]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "import's procedural refusals carry their raw ids again (round 4's R4-03, the pass before the screen)"),
    ('R4-03-served-receipt-raw-id', 'product', 'src/veracium/mcp_server.py',
     [('        return _ok(_locate_receipt(r if isinstance(r, dict) else r.model_dump(mode="json")))',
       '        return _ok(r if isinstance(r, dict) else r.model_dump(mode="json"))')],
     ['tests/test_0055_r4_closure.py::test_r4_03_no_served_tool_names_a_shaped_record_id[direct]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the served forget_fact receipt names surviving records by raw id again (dev's sweep, R4-03's class)"),
    ('R4-04-old-text-lists', 'product', 'src/veracium/store/sqlite.py',
     [('        edge_own = (_redaction.EDGE_REPLACE + _redaction.EDGE_CLEAR + _redaction.EDGE_REASON_THREE_CASE\n'
       '                    + _redaction.EDGE_MARKERS_PER_ENTRY)\n'
       '        episode_own = (_redaction.EPISODE_REPLACE + _redaction.EPISODE_KIND_TWO_BRANCH\n'
       '                       + _redaction.EPISODE_REASON_THREE_CASE)',
       '        edge_own = ("subject", "relation", "object", "note", "original_relation")\n'
       '        episode_own = ("summary",)')],
     ['tests/test_0055_r4_closure.py::test_r4_04_a_shape_in_any_field_of_a_record_or_its_journal_is_found[current-edge]', 'tests/test_0055_r4_closure.py::test_r4_04_a_shape_in_any_field_of_a_record_or_its_journal_is_found[current-episode]', 'tests/test_0055_r4_closure.py::test_r4_04_a_shape_in_any_field_of_a_record_or_its_journal_is_found[journal-edge]', 'tests/test_0055_r4_closure.py::test_r4_04_a_shape_in_any_field_of_a_record_or_its_journal_is_found[journal-episode]', 'tests/test_0055_r4_closure.py::test_r4_04_credentials_redact_removes_a_legacy_invalidation_reason_end_to_end'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the finder's removable text is the superseded fixed lists (round 4's R4-04: invalidation_reason, kind and "
     "retired_reason read as residual, so the remedy never targets them)"),
    ('R4-04-unclassified-dropped', 'product', 'src/veracium/store/sqlite.py',
     [('                else:\n                    cls = f"{carrier}.other"\n',
       '                else:\n                    continue\n')],
     ['tests/test_0055_r4_closure.py::test_r4_04_a_shape_in_any_field_of_a_record_or_its_journal_is_found[current-edge]', 'tests/test_0055_r4_closure.py::test_r4_04_a_shape_in_any_field_of_a_record_or_its_journal_is_found[current-episode]', 'tests/test_0055_r4_closure.py::test_r4_04_a_shape_in_any_field_of_a_record_or_its_journal_is_found[journal-edge]', 'tests/test_0055_r4_closure.py::test_r4_04_a_shape_in_any_field_of_a_record_or_its_journal_is_found[journal-episode]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "a record field no class names is dropped again, not reported (round 4's R4-04: fail closed)"),
    ('S1-unparsed-record-skipped', 'product', 'src/veracium/store/sqlite.py',
     [('                        out.append((uid, f"{kind}s", f"{kind}.unparsed", kind, rid, kind, rid, js))',
       '                        pass')],
     ['tests/test_0055_r4_closure.py::test_r4_04_an_unparseable_current_record_is_reported_not_skipped[edge]', 'tests/test_0055_r4_closure.py::test_r4_04_an_unparseable_current_record_is_reported_not_skipped[episode]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "a current record whose JSON does not parse is skipped again (research's S1)"),
    ('S1-named-side-tables-only', 'product', 'src/veracium/store/sqlite.py',
     [('            for table, cols in self._credential_side_tables():',
       '            for table, cols in [x for x in self._credential_side_tables()\n'
       '                                if x[0] in ("replies", "confirmations", "request_registry", "wiki",\n'
       '                                            "contribution_ledger")]:')],
     ['tests/test_0055_r4_closure.py::test_r4_04_a_shape_in_any_column_of_any_per_user_side_table_is_found'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the finder reads only the round-3 side tables again (research's S1: supersession_refusals.relation, "
     "source_revocations.reason and every other per-user column unread)"),
    ('R4-05-args-rewrite-only', 'product', 'src/veracium/credentials.py',
     [('        if _formats_as(exc, msg):\n            return exc\n', '        return exc\n')],
     ['tests/test_0055_r4_closure.py::test_r4_05_a_real_invalid_import_leaves_the_cli_without_its_input', 'tests/test_0055_r4_closure.py::test_r4_05_an_exception_with_its_own_formatter_is_replaced_and_a_plain_one_raised_as_itself'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "a defect with its own formatter is re-raised as itself after the args rewrite (round 4's R4-05)"),
    ('S3-dict-key-echoed', 'product', 'src/veracium/credentials.py',
     [('    return "[key]"', '    return str(seg)')],
     ['tests/test_0055_r4_closure.py::test_r4_05_a_caller_dict_key_in_a_validation_location_is_not_echoed'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "a validation location prints a caller's dict key again (research's S3)"),
    ('R4-06-cut-before-screen', 'product', 'src/veracium/diagnostics.py',
     [('            text = _cred.mask_text(data.decode("utf-8", "replace"))',
       '            data = data[-cap:]\n            text = _cred.mask_text(data.decode("utf-8", "replace"))')],
     ['tests/test_0055_r4_closure.py::test_r4_06_a_cut_never_sends_the_unscreened_rest_of_a_value[labelled-value]', 'tests/test_0055_r4_closure.py::test_r4_06_a_cut_never_sends_the_unscreened_rest_of_a_value[structural-body]', 'tests/test_0055_r4_closure.py::test_r4_06_a_cut_never_sends_the_unscreened_rest_of_a_value[structural-prefix]', 'tests/test_0055_r4_closure.py::test_r4_06_reviewer_a_twenty_byte_tail_holds_no_part_of_the_token'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the log tail is cut to the cap BEFORE it is screened again (round 4's R4-06)"),
    ('A1-pool-key-undeclared', 'product', 'src/veracium/credential_finder.py',
     [('    ("maintain() consolidate-pool / pool_key",', '    ("maintain() consolidate-pool",')],
     ['tests/test_0055_r4_closure.py::test_a1_the_finder_report_declares_the_pool_key'], [_R4 + 'test_r4_03_render_receipts_use_the_locator_on_every_exit'], None,
     "the finder's report no longer names maintain()'s pool_key destination (round 4's A1)"),
    # round 5: D3's type gate (research's (c)) and the carrier-to-boundary table's findings
    ('R5-D3-str-only-gate', 'product', 'src/veracium/__init__.py',
     [('        for field_name, value in (("origin", origin), ("source_id", source_id)):\n            if value is not None and not isinstance(value, str):\n                raise _cred.ArgumentTypeRefused(f"{op}: {field_name} must be a str, not {type(value).__name__}",\n                                                field=field_name, reason="not_a_string")\n', '')],
     ['tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[revoke_source.origin]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[revoke_source.source_id]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[unrevoke_source.origin]', 'tests/test_0055_r4_closure.py::test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str[unrevoke_source.source_id]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "D3's screen reads only a str again: a bytes origin or source_id passes it to `_bounded`, whose message quotes it (round 5: R4-01's class one call down, found by the A5 census's exception-text cell)"),
    ('R5-recall-episode-date-unmasked', 'product', 'src/veracium/__init__.py',
     [('        ep_lines = [(e, clamp_item(f"[{_cred.mask_text(e.date)}]', '        ep_lines = [(e, clamp_item(f"[{e.date}]'), ('        tp_ep_lines = [(e, clamp_item(f"[{_cred.mask_text(e.date)}]', '        tp_ep_lines = [(e, clamp_item(f"[{e.date}]')],
     ['tests/test_0055_r4_closure.py::test_r5_a_legacy_episode_date_reaches_no_model_and_no_result[answer-bare]', 'tests/test_0055_r4_closure.py::test_r5_a_legacy_episode_date_reaches_no_model_and_no_result[answer-dated]', 'tests/test_0055_r4_closure.py::test_r5_a_legacy_episode_date_reaches_no_model_and_no_result[recall-bare]', 'tests/test_0055_r4_closure.py::test_r5_a_legacy_episode_date_reaches_no_model_and_no_result[recall-dated]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "recall's episode lines print the stored date unmasked again (round 5, the carrier table's `record:episode:current:date`) [re-measured at round 5's RETURN: the served cells also pass under served_result's projection, a second layer over the same leak; the library cells name the row]"),
    ('R5-compile-episode-date-unmasked', 'product', 'src/veracium/compile.py',
     [('clamp_item(f"[{_cred.mask_text(e.date)}] {_cred.mask_text(e.summary)}", item_cap)', 'clamp_item(f"[{e.date}] {_cred.mask_text(e.summary)}", item_cap)')],
     ['tests/test_0055_r4_closure.py::test_r5_a_legacy_episode_date_reaches_no_model_and_no_result[answer-dated]', 'tests/test_0055_r4_closure.py::test_r5_a_legacy_episode_date_reaches_no_model_and_no_result[find_facts-dated]', 'tests/test_0055_r4_closure.py::test_r5_a_legacy_episode_date_reaches_no_model_and_no_result[mcp-recall-dated]', 'tests/test_0055_r4_closure.py::test_r5_a_legacy_episode_date_reaches_no_model_and_no_result[recall-dated]', 'tests/test_0055_r4_closure.py::test_r5_a_legacy_episode_date_reaches_no_model_and_no_result[wiki-compile-dated]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the wiki compile's episode line prints the stored date unmasked again (round 5; reached by the DATED form only: a bare token sorts as a future date and the episode is not assertable)"),
    ('R5-mask-deep-keys-kept', 'product', 'src/veracium/credentials.py',
     [('            nk = mask_text(k) if isinstance(k, str) else k\n', '            nk = k\n')],
     ['tests/test_0055_r4_closure.py::test_r5_mask_deep_masks_str_keys_and_keeps_two_alike_as_two', 'tests/test_0055_r4_closure.py::test_r5_why_prints_no_legacy_dict_key_and_no_unmasked_find_field[why-json]', 'tests/test_0055_r4_closure.py::test_r5_why_prints_no_legacy_dict_key_and_no_unmasked_find_field[why]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     'mask_deep leaves dict keys as they are again (round 5: `veracium why` printed a legacy `outcome_counts` key)'),
    ('R5-why-find-two-fields', 'product', 'src/veracium/why.py',
     [('            out.append(_cred.mask_deep({"id": d.get("id"), "fact": _summary(d),', '            out.append(dict({"id": _cred.mask_text(d.get("id")), "fact": _cred.mask_text(_summary(d)),')],
     ['tests/test_0055_r4_closure.py::test_r5_why_prints_no_legacy_dict_key_and_no_unmasked_find_field[find-json]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     'why.find masks only its id and fact again (round 5: `why --find --json` printed `invalidation_reason`)'),
    ('R5-journal-after-redaction-removable', 'product', 'src/veracium/store/sqlite.py',
     [('                done = (uid, rid) in redacted\n', '                done = False\n')],
     ['tests/test_0055_r4_closure.py::test_r4_04_a_shape_in_any_field_of_a_record_or_its_journal_is_found[journal-episode]', 'tests/test_0055_r4_closure.py::test_r5_text_in_the_journal_of_an_already_redacted_record_is_residual[edge]', 'tests/test_0055_r4_closure.py::test_r5_text_in_the_journal_of_an_already_redacted_record_is_residual[episode]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     'journal text of an already-redacted record is reported removable again (round 5: `act` redacted nothing and the token stayed)'),
    # round 5's RETURN (coordination 0d13921): one mutant per corrected boundary, measured (tests/test_0055_r5_closure.py)
    ('R5-06-no-canonical-form', 'product', 'src/veracium/__init__.py',
     [('        ids = tuple((f, _cred.exact(v)) for f, v in ids)\n        free = tuple((f, _cred.exact(v)) for f, v in free)\n', '')],
     ['tests/test_0055_r5_closure.py::test_r5_06_an_accepted_str_subclass_reaches_what_its_data_reaches[remember.event_text]', 'tests/test_0055_r5_closure.py::test_r5_06_remember_fallback_summary_uses_the_screened_event_type'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "_cred_ingress screens a str subclass by its data but hands the object on again (round 5's R5-06)"),
    ('R5-06-remember-keeps-the-object', 'product', 'src/veracium/__init__.py',
     [('        (event_text,), caller_report, (source_id, evidence_ref, event_type) = self._cred_ingress(', '        (event_text,), caller_report, _ids = self._cred_ingress(')],
     ['tests/test_0055_r5_closure.py::test_r5_06_remember_fallback_summary_uses_the_screened_event_type'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "remember passes the unconverted event_type to ingest again, whose fallback summary formats it (R5-06's branch)"),
    ('R5-06-d3-keeps-the-object', 'product', 'src/veracium/__init__.py',
     [('        origin, source_id = _cred.exact(origin), _cred.exact(source_id)\n', '')],
     ['tests/test_0055_r5_closure.py::test_r5_06_d3_returns_exact_strs'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "D3's callee screen returns origin and source_id unconverted again (R5-06, the callee's step)"),
    ('R5-01-import-keys-unread', 'product', 'src/veracium/portability.py',
     [('                if isinstance(k, str) and k:\n                    yield (f"{path}.[key]" if path else "[key]"), k\n', '')],
     ['tests/test_0055_r5_closure.py::test_r5_01_a_shaped_key_in_every_dict_field_is_refused_at_import[plain-Edge-outcome_counts]', 'tests/test_0055_r5_closure.py::test_r5_01_a_shaped_key_in_every_dict_field_is_refused_at_import[restore-Edge-outcome_counts]', 'tests/test_0055_r5_closure.py::test_r5_01_a_shaped_key_in_every_dict_field_is_refused_at_import[restore_withhold-Edge-outcome_counts]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the import screen reads mapping VALUES only again: a shaped key passes admission (round 5's R5-01)"),
    ('R5-01-guard-keys-unread', 'product', 'src/veracium/store/sqlite.py',
     [('            if isinstance(k, str) and k and k not in prior_keys:\n                cls = _cred.first_class(k)\n                if cls is not None:\n                    return (f"{path}.[key]" if path else "[key]", cls)\n', '')],
     ['tests/test_0055_r5_closure.py::test_r5_01_the_store_guard_reads_new_keys_and_passes_unchanged_ones', 'tests/test_0055_r5_closure.py::test_r5_02_a_label_prints_a_declared_name_or_key[ghp_kgPoYqnCDoYzBKbftfOoXTZhQ8stzhe6SVI3]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the store guard reads mapping VALUES only again: a new shaped key passes it (round 5's R5-01)"),
    ('R5-02-import-label-raw', 'product', 'src/veracium/portability.py',
     [('                seg = _cred.path_segment(k)\n                yield from leaves(v, f"{path}.{seg}" if path else seg)', '                yield from leaves(v, f"{path}.{k}" if path else str(k))')],
     ['tests/test_0055_r5_closure.py::test_r5_02_an_ordinary_unknown_key_is_labelled_key_too'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the import screen's label prints a caller's key again (round 5's R5-02)"),
    ('R5-02-guard-label-raw', 'product', 'src/veracium/store/sqlite.py',
     [('            seg = _cred.path_segment(k)\n            hit = _cred_introduced(', '            seg = str(k)\n            hit = _cred_introduced(')],
     ['tests/test_0055_r5_closure.py::test_r5_02_a_label_prints_a_declared_name_or_key[not_a_declared_name]', 'tests/test_0055_r5_closure.py::test_r5_02_a_label_prints_a_declared_name_or_key[relation]', 'tests/test_0055_r5_closure.py::test_r5_02_a_label_prints_a_declared_name_or_key[xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the store guard's refusal label prints a stored key again (R5-02 in the recursive guard)"),
    ('R5-03-record-id-raw', 'product', 'src/veracium/mcp_server.py',
     [('                n += 1\n                return f"record {n} of this report ({key})"\n', '                return v\n')],
     ['tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[confirmed]', 'tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[corrected]', 'tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[disputed]', 'tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[edge_id]', 'tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[id]', 'tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[superseded_by]', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[confirm_fact-binding-shaped_id]', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[confirm_fact-mcp-shaped_id]', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[dispute_fact-binding-shaped_id]', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[dispute_fact-mcp-shaped_id]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "a served result keeps a shaped record id raw again (round 5's R5-03)"),
    ('R5-03-stored-text-raw', 'product', 'src/veracium/mcp_server.py',
     [('            return _cred.mask_text(v)\n        if isinstance(v, dict):\n            out: dict = {}', '            return v\n        if isinstance(v, dict):\n            out: dict = {}')],
     ['tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[confirmed]', 'tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[corrected]', 'tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[disputed]', 'tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[edge_id]', 'tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[id]', 'tests/test_0055_r5_closure.py::test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked[superseded_by]', 'tests/test_0055_r5_closure.py::test_r5_03_the_minted_preview_token_is_kept'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "a served result keeps shaped stored text raw again (R5-03: dispute's relation)"),
    ('R5-04-no-chain-context', 'product', 'src/veracium/diagnostics.py',
     [('                send_at = len(prefix) + len(head_text) + _cred.chain_safe_offset(rest_text)', '                send_at = len(prefix) + len(head_text)')],
     ['tests/test_0055_r5_closure.py::test_r5_04_a_label_before_a_window_long_blank_run_still_withholds_its_value[label]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     'the log window sends from its first full line again: a white-space-joined match is cut from its label (R5-04)'),
    ('R5-04-no-pem-state', 'product', 'src/veracium/diagnostics.py',
     [('                prefix = _cred.PEM_REOPEN if pem_open else ""', '                prefix = ""')],
     ['tests/test_0055_r5_closure.py::test_r5_04_a_pem_block_with_no_end_longer_than_the_window_is_withheld'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the log window ignores a PEM block open at its start again (round 5's R5-04)"),
    ('R5-04-crossing-span-kept', 'product', 'src/veracium/credentials.py',
     [('        for f in found:\n            if f.start < cur < f.end:\n                cur = f.end\n', '')],
     ['tests/test_0055_r5_closure.py::test_r5_04_mask_from_omits_a_span_that_crosses_the_cut'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     'mask_from keeps the cursor inside a span that crosses the send point again (R5-04)'),
    ('R5-05-replacement-unsettled', 'product', 'src/veracium/credentials.py',
     [('    try:\n        del exc.__notes__\n    except AttributeError:\n        pass\n    exc.__cause__ = None\n    return exc', '    return exc')],
     ['tests/test_0055_r4_closure.py::test_r4_05_an_exception_with_its_own_formatter_is_replaced_and_a_plain_one_raised_as_itself', 'tests/test_0055_r5_closure.py::test_r5_05_the_replacement_is_checked_after_construction[_CauseInCtor]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the replacement exception keeps the notes and cause its constructor added again (round 5's R5-05)"),
    ('R5-03-introspect-unmasked', 'product', 'src/veracium/introspect.py',
     [('    return {"user_id": uid, **_cred.mask_deep(out)}', '    return {"user_id": uid, **out}')],
     ['tests/test_0055_r5_closure.py::test_r5_03_introspect_carries_no_stored_shape_in_its_report_or_on_the_cli[categories]', 'tests/test_0055_r5_closure.py::test_r5_03_introspect_carries_no_stored_shape_in_its_report_or_on_the_cli[summary]', 'tests/test_0055_r5_closure.py::test_a_none_return_carries_no_stored_shape[introspect-relation]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "introspect's report carries stored relations and reasons raw again (dev's library audit: the CLI printed them)"),
    ('R5-03-library-dispute-relation-raw', 'product', 'src/veracium/__init__.py',
     [('"relation": _cred.mask_text(edge.relation)}', '"relation": edge.relation}')],
     ['tests/test_0055_r5_closure.py::test_r5_03_library_dispute_masks_the_stored_relation'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the library dispute result carries the stored relation raw again (research's addition 2)"),
    ('R5-03-trust-impls-undecorated', 'product', 'src/veracium/mcp_server.py',
     [('@_projected\ndef confirm_fact_impl(', 'def confirm_fact_impl('), ('@_projected\ndef dispute_fact_impl(', 'def dispute_fact_impl(')],
     ['tests/test_0055_r5_closure.py::test_r5_03_every_impl_is_served_through_the_projection', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[confirm_fact-binding-shaped_id]', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[confirm_fact-mcp-shaped_id]', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[dispute_fact-binding-shaped_id]', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[dispute_fact-mcp-shaped_id]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     'confirm_fact_impl and dispute_fact_impl return unprojected again (R5-03, the decorator)'),
    ('R5-03-minted-token-masked', 'product', 'src/veracium/mcp_server.py',
     [('@_projected(keep=_MINTED_PREVIEW_TOKEN)\ndef forget_everything_preview_impl(', '@_projected\ndef forget_everything_preview_impl(')],
     ['tests/test_0055_invariants.py::test_i14_preview_then_confirm_completes_and_a_pasted_token_is_withheld', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[forget_everything_confirm-binding-shaped_id]', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[forget_everything_confirm-binding-shaped_relation]', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[forget_everything_confirm-mcp-shaped_id]', 'tests/test_0055_r5_closure.py::test_r5_03_every_served_success_result_carries_no_shape[forget_everything_confirm-mcp-shaped_relation]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "forget_everything_preview's minted token is masked like a stored shape (the declared exception lost)"),
    ('R5-06-confirm-edge-id-unconverted', 'product', 'src/veracium/__init__.py',
     [('("source_id", source_id)))\n        edge_id = _cred.exact(edge_id)      # R5-06: an unscreened id is looked up AND written; one representation\n        actor = ConfirmationActor(actor)', '("source_id", source_id)))\n        actor = ConfirmationActor(actor)')],
     ['tests/test_0055_r5_closure.py::test_r5_06_an_accepted_str_subclass_reaches_what_its_data_reaches[confirm.edge_id]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "confirm writes an unscreened str-subclass edge_id's name into the record again (R5-06's unscreened sibling)"),
    ('R5-06-dispute-edge-id-unconverted', 'product', 'src/veracium/__init__.py',
     [('free=(("reason", reason),))\n        edge_id = _cred.exact(edge_id)      # R5-06: an unscreened id is looked up AND written; one representation\n', 'free=(("reason", reason),))\n')],
     ['tests/test_0055_r5_closure.py::test_r5_06_an_accepted_str_subclass_reaches_what_its_data_reaches[dispute.edge_id]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "dispute writes an unscreened str-subclass edge_id's name into the record again (R5-06's unscreened sibling)"),
    ('R5-06-correct-edge-id-unconverted', 'product', 'src/veracium/__init__.py',
     [('        edge_id = _cred.exact(edge_id)      # R5-06: the derived evidence_ref is built from it; one representation\n', '')],
     ['tests/test_0055_r5_closure.py::test_r5_06_an_accepted_str_subclass_reaches_what_its_data_reaches[correct.edge_id]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "correct derives evidence_ref from a str-subclass edge_id's name again (R5-06's unscreened sibling)"),
    ('R5-06-answer-query-unconverted', 'product', 'src/veracium/__init__.py',
     [("        query = _cred.exact(query)          # R5-06: the gate's prompt formats it; one representation\n", '')],
     ['tests/test_0055_r5_closure.py::test_r5_06_an_accepted_str_subclass_reaches_what_its_data_reaches[answer.query]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "answer puts a str-subclass query's name in the gate's prompt again (R5-06's unscreened sibling)"),
    ('R5-05-notes-unjudged', 'product', 'src/veracium/credentials.py',
     [('    try:\n        if exc.__notes__:\n            return False\n    except AttributeError:\n        pass\n', '')],
     ['tests/test_0055_r5_closure.py::test_r5_05_notes_that_cannot_be_deleted_refuse_the_object'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     '_formats_as no longer refuses an exception that still carries notes (R5-05: an undeletable __notes__)'),
    # research's ruling on the host-only library results (2026-11-27): the RETURN census's three boundaries
    ('R5-census-cli-recall-prints-records', 'product', 'src/veracium/cli.py',
     [('            print(r.context)\n', '            print(r.context)\n            print(*(e.id for e in r.edges))\n')],
     ['tests/test_0055_r5_closure.py::test_the_cli_recall_verb_prints_no_planted_shape[id]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the CLI's recall verb prints the host-record Recall's raw record ids (the census's outward check, CLI half)"),
    ('R5-census-unscreened-caller', 'product', 'src/veracium/cli.py',
     [('            print(r.context)\n', '            print(r.context)\n            mem.edges_since(args.user, "2000-01-01T00:00:00+00:00")\n')],
     ['tests/test_0055_r5_closure.py::test_a_host_record_method_reaches_no_outward_surface_but_through_a_screened_caller'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "a host-record method gains a caller outside Memory that no projection or masked print screens (the surface half)"),
    ('R5-census-host-record-empty', 'product', 'src/veracium/__init__.py',
     [('                    out.append(e)\n        return out\n\n    # -- user feedback verbs', '                    out.append(e)\n        return []\n\n    # -- user feedback verbs')],
     ['tests/test_0055_r5_closure.py::test_a_host_record_return_carries_the_raw_id_and_no_log_line_does[edges_since]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "edges_since returns nothing: the census's positive control (the host's own read carries the record) reaches no record"),
    # research's stage 2 of round 5 (2026-11-27, research 1eded2d3): S2-1's fix, and the two survivors S2-2/S2-3 pin
    ('S2-1-pem-judged-at-the-cut', 'product', 'src/veracium/diagnostics.py',
     [('_cred.pem_open_before(read_back, start + nl + 1)', '_cred.pem_open_before(read_back, start)')],
     ['tests/test_0055_r5_closure.py::test_s2_1_a_window_starting_anywhere_in_a_begin_line_withholds_the_body[1]', 'tests/test_0055_r5_closure.py::test_s2_1_a_window_starting_anywhere_in_an_end_line_sends_what_follows[1]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the log window's PEM state is judged at its cut again, inside a line (S2-1; the line-start refusal then sends nothing)"),
    ('S2-1-pem-cut-unrefused', 'product', 'src/veracium/credentials.py',
     [('    if pos < 0 or (pos > 0 and read_back(pos - 1, pos) != b"\\n"):\n        raise ValueError("pem_open_before: pos must be a line start")\n', '')],
     ['tests/test_0055_r5_closure.py::test_s2_1_pem_state_is_judged_only_at_a_line_start'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "pem_open_before answers at a position inside a line, where a marker can be cut in two (S2-1's mechanism)"),
    ('S2-1-chunk-edge-fixed-overlap', 'product', 'src/veracium/credentials.py',
     [('        carry = raw if nl < 0 else raw[:nl]', '        carry = (raw if nl < 0 else raw[:nl])[:4096]')],
     ['tests/test_0055_r5_closure.py::test_s2_1_a_marker_longer_than_any_overlap_is_read_whole_across_chunk_edges[64]', 'tests/test_0055_r5_closure.py::test_s2_1_a_long_begin_marker_cut_by_the_read_back_chunk_edge_withholds_the_body'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the read-back carries a fixed 4096-byte overlap across a chunk edge again (round 5's form): a longer marker is cut"),
    ('S2-2-chain-blank-lines-count', 'product', 'src/veracium/credentials.py',
     [('        if _normalise(text[pos:end])[0].strip():\n            seen += 1', '        if True:\n            seen += 1')],
     ['tests/test_0055_r5_closure.py::test_s2_2_a_many_line_run_between_a_label_and_its_value_counts_no_chain_line[blank-lines]', 'tests/test_0055_r5_closure.py::test_s2_2_chain_safe_offset_counts_only_visible_lines[blank]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the chain bound counts blank lines (research's chain-blank-lines-count: a many-line run ends the context early)"),
    ('S2-2-chain-invisible-lines-count', 'product', 'src/veracium/credentials.py',
     [('if _normalise(text[pos:end])[0].strip():', 'if text[pos:end].strip():')],
     ['tests/test_0055_r5_closure.py::test_s2_2_a_many_line_run_between_a_label_and_its_value_counts_no_chain_line[invisible-only-lines]', 'tests/test_0055_r5_closure.py::test_s2_2_chain_safe_offset_counts_only_visible_lines[invisible-only]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "the chain bound judges a line raw, so an invisible-only line counts (research's chain-invisible-lines-count)"),
    ('S2-3-exact-only-enum', 'product', 'src/veracium/credentials.py',
     [('return str.__str__(value) if isinstance(value, str) and type(value) is not str else value', "return str.__str__(value) if isinstance(value, str) and isinstance(value, __import__('enum').Enum) else value")],
     ['tests/test_0055_r5_closure.py::test_r5_06_remember_fallback_summary_uses_the_screened_event_type', 'tests/test_0055_r5_closure.py::test_r5_06_an_accepted_str_subclass_reaches_what_its_data_reaches[remember.event_text]'], [_R4 + 'test_a1_the_finder_report_declares_the_pool_key'], None,
     "exact converts Enum members only; a plain str subclass that formats as the token passes (research's exact-only-enum)"),
]


def _noop(rel, anchor, cells):
    return (f"NOOP-{pathlib.Path(rel).stem}", rel, [(anchor, "# no-op control: a comment, no behaviour\n" + anchor)],
            sorted(set(cells)), f"a comment edit in {rel}: its mutants' cells must all pass", "SURVIVED")


def _cells_of(rel):
    return [c for m in MUTANTS if m[2] == rel for c in m[4]]


_NOOP_ANCHORS = {
    "src/veracium/credentials.py": "def outward_text(",
    "src/veracium/__init__.py": "    def _cred_withheld(self, user_id: str, op: str, report: dict, *, source: str) -> None:",
    "src/veracium/ingest.py": "def _len_sha16(",
    "src/veracium/portability.py": "def _credential_screen(",
    "src/veracium/proactive.py": "def assemble(",
    "src/veracium/store/sqlite.py": "    def erase_preview_snapshot(self, user_id) -> dict:",
    "src/veracium/mcp_server.py": "def _served(",
    "src/veracium/graph.py": "def _absorption_scope_gate(",
    "src/veracium/cli.py": "def main(",
    "src/veracium/semantic.py": "def content_digest(",
    "src/veracium/compile.py": "def ensure_wiki(",
    "src/veracium/trust_tools.py": "class RenderReceipt:",
    "src/veracium/diagnostics.py": "class Reporter",
    "src/veracium/credential_finder.py": "def is_residual(",
    "src/veracium/why.py": "def find(",
    "src/veracium/introspect.py": "def report(",
}

# (id, file, [(anchor, replacement)], named cells, what, the outcome the classifier must give)
CONTROLS = [_noop(rel, _NOOP_ANCHORS[rel], _cells_of(rel)) for rel in MUTATED] + [
    ("CTRL-unrelated-TypeError", "src/veracium/__init__.py",
     [("    def _cred_withheld(self, user_id: str, op: str, report: dict, *, source: str) -> None:\n",
       "    def _cred_withheld(self, user_id: str, op: str, report: dict, *, source: str) -> None:\n"
       "        raise TypeError(\"an unrelated execution failure (classifier negative control)\")\n")],
     ["tests/test_0055_invariants.py::test_i20_record_procedure_keeps_its_str_and_the_twin_reports"],
     "an UNRELATED TypeError in Memory._cred_withheld: its cell fails for no reason a row names", "UNCLASSIFIED"),
]

SUBJECT_P = _protocol.Subject(
    spec="0055", finding=SUBJECT, table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium", "veracium.credentials", "veracium.ingest", "veracium.portability",
                    "veracium.proactive", "veracium.store.sqlite", "veracium.mcp_server", "veracium.graph",
                    "veracium.cli", "veracium.semantic", "veracium.compile", "veracium.trust_tools",
                    "veracium.diagnostics", "veracium.credential_finder", "veracium.why",
                    "veracium.introspect"),
    import_specs=(), cells_files=CELL_FILES, kinds=("product",))

definition_sha = _protocol.definition_sha
canonical = _protocol.canonical
render = _protocol.render
_digests = SUBJECT_P.digests


def problems(path: pathlib.Path = TABLE, root: pathlib.Path = ROOT) -> list:
    return SUBJECT_P.problems(path, root)


def main() -> int:
    if "--check" in sys.argv or len(sys.argv) == 1:
        probs = problems()
        for b in probs:
            print(f"STALE: {b}")
        return 1 if probs else 0
    return SUBJECT_P.main(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
