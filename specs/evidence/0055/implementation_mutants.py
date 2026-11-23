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
CELL_FILES = ("tests/test_0055_invariants.py", "tests/test_0055_recogniser.py", "tests/test_0055_i19_digest_sweep.py")
MUTATED = ("src/veracium/credentials.py", "src/veracium/__init__.py", "src/veracium/ingest.py",
           "src/veracium/portability.py", "src/veracium/proactive.py", "src/veracium/store/sqlite.py",
           "src/veracium/mcp_server.py", "src/veracium/graph.py", "src/veracium/cli.py", "src/veracium/semantic.py")
DIGESTED = MUTATED + CELL_FILES + ("tests/support_0055_i19.py", "specs/evidence/0055/digests.json",
                                   "specs/evidence/0055/vectors.py", "specs/evidence/mutation_protocol.py",
                                   _protocol.KINDS, SELF)

# (id, kind, file, [(anchor, replacement)], named cells, honest nodes, reason, what)
MUTANTS = [
    ('I3-single-pass-mask', 'product', 'src/veracium/credentials.py',
     [('    found = scan(out)\n    while found:\n        if passes >= MAX_PASSES:', '    found = scan(out)\n    if found:\n        if passes >= MAX_PASSES:')],
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
     ['tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r11:c[-identity_digest-]--copied-from-a-closed-ledger-row--s:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r1:prior_upserts[].provenance.source_id-[remember--procedur:run]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r34:record.provenance.origin--.source_id-of-a-held-record--_:extra-34-same-scope]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r35:e.provenance.origin--e.provenance.source_id-for-EVERY-ed:extra-35-chain-src]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r5:target--resolve-only--a-reply-id:reply-resolve]', 'tests/test_0055_i19_digest_sweep.py::test_each_component_follows_its_rule[r6:contributor.provenance.source_id:run]', 'tests/test_0055_invariants.py::test_i20_record_procedure_keeps_its_str_and_the_twin_reports', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[confirm.correlation_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[confirm.source_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[correct.actor]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[correct.corrected_value]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[correct.evidence_ref]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[correct.source_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[dispute.actor]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[dispute.source_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[record_outcome.context_ref]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[record_outcome.evidence_ref]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[record_procedure.evidence_ref]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[record_procedure.source_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[remember.event_type]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[remember.evidence_ref]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[remember.source_id]', 'tests/test_0055_invariants.py::test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing[reply.correlation_id]'],
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
     [('        field_name, cls = shaped[0]\n        raise self._cred_refused(user_id, op, field_name, cls)', '        return')],
     ['tests/test_0055_invariants.py::test_i19_revoke_source_refuses_an_unknown_shape_before_any_digest'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'D3 accepts an unknown credential-shaped source and digests it (I19: an unknown shape refuses first)'),
    ('I20-twin-omitted-on-the-served-surface', 'product', 'src/veracium/mcp_server.py',
     [('    out = {"ok": True, "edge_id": rep["edge_id"]}\n    if rep.get("credentials_withheld"):\n        out["credentials_withheld"] = rep["credentials_withheld"]', '    out = {"ok": True, "edge_id": rep["edge_id"]}')],
     ['tests/test_0055_invariants.py::test_i20_record_procedure_keeps_its_str_and_the_twin_reports'],
     ['tests/test_0055_invariants.py::test_i2_near_misses_are_stored_byte_for_byte'], None,
     'the served record_procedure drops the report the twin returns (I20)'),
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
                    "veracium.cli", "veracium.semantic"),
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
