"""The CITATION DEBT of the accepted specs — GENERATED 2026-09-08, a RATCHET with
a REASON per entry.

Every backticked `test_*` name an ACCEPTED spec cites should resolve to a `def`
in tests/ or specs/evidence/. 0025 v14 cited four nodes that did not exist, in the
fold that closed a finding about a cited artifact that did not exist (research,
the same day): "a spec is not verified until its citations are resolved against
the thing built". The names below did NOT resolve at generation.

THE GATE (`tests/test_spec_gate.py::test_accepted_specs_cite_only_test_nodes_that_exist_or_recorded_debt`)
derives the unresolved set from the tree and requires it to EQUAL this table's
keys — a NEW unresolved citation fails the build (fix the spec, or declare it
here WITH a reason), and a citation that starts resolving must be REMOVED (the
list only shrinks). Drafts are exempt: a draft may cite the nodes it owes;
acceptance is where a planned node becomes a claim.

THE REASON is a closed vocabulary, because "unresolved" is three things wanting
OPPOSITE actions (research, 2026-09-08; measured: of the 174 at generation, 36
have a real test within 0.85 similarity — almost certainly renames; 138 have no
near match — the real debt): `renamed` (the test exists under another name — a
one-line spec fix; carry the resolving name after a colon), `never_written` (work
owed), `owed_at_implementation` (a forward reference to a node an OWED invariant
names), `stale_version` (the spec cites a version that moved), and
`unclassified_at_generation` — permitted ONLY for the pairs frozen in
GENERATION_SET below, so every entry added after this file was generated must
carry a real reason. Classifying a frozen entry replaces its reason; nothing
about the ratchet loosens.

SUGGEST, NEVER REWRITE: `python3 specs/citation_debt.py --suggest` prints, per
unresolved name, the closest real test name at >= 0.85 similarity. A similarity
is a strong hint and a bad authority — a wrong auto-rename would point a spec at
a test asserting something else — so the tool never edits a spec or this table.

Regenerate rather than edit the KEYS: `python3 specs/citation_debt.py --write`
(keeps every reason already recorded; new keys arrive as
`unclassified_at_generation` only if they are in GENERATION_SET, else the write
REFUSES and names them).

THE RATCHET STOPS THE DEBT GROWING; IT DOES NOT WORK IT DOWN. The frozen reason
is a GRANDFATHER CLAUSE, not progress: nothing forces a frozen entry to be
classified, and every gate stays green while the 174 sit unclassified. So "the
citation gate is green" and "the citation debt is being paid" are different
claims, and the second has its own number — `UNCLASSIFIED_REMAINING` below,
DERIVED at import from the table (never typed), which starts at 174 and can
only fall. Watch that number, not the gate.
"""
GENERATED_AT = "2026-09-08"
REASONS = ("renamed", "never_written", "owed_at_implementation", "stale_version",
           "unclassified_at_generation")

# spec -> {cited test name that did not resolve: reason}
CITATION_DEBT: dict = {
    "0001": {
        "test_affirmation_grounds_and_confirm_edge_refuses": "unclassified_at_generation",
        "test_assistant_cannot_touch_user_edge": "unclassified_at_generation",
        "test_assistant_derived_from_third_party_is_capped": "unclassified_at_generation",
        "test_assistant_dominant_store_does_not_crowd_out_user": "unclassified_at_generation",
        "test_assistant_never_yields_mentionable": "unclassified_at_generation",
        "test_assistant_restatement_does_not_refresh_currency": "unclassified_at_generation",
        "test_ladder_diagnostics_generate_from_the_registry": "unclassified_at_generation",
        "test_mixed_batch_with_assistant_declares_influence": "unclassified_at_generation",
        "test_old_reader_refuses_v11_at_open": "unclassified_at_generation",
        "test_release_migration_derives_from_the_bumped_head": "unclassified_at_generation",
        "test_the_measure_producer_derives_the_record_from_real_commands": "unclassified_at_generation",
        "test_the_production_measure_delegates_to_the_implementation": "unclassified_at_generation",
        "test_the_sealer_enforces_the_candidate_replay": "unclassified_at_generation",
        "test_user_can_correct_an_assistant_fact": "unclassified_at_generation",
        "test_v10_to_v11_migration_is_stamp_only": "unclassified_at_generation"
    },
    "0003": {
        "test_a_failed_plan_leaves_no_partial_state_and_does_not_touch_sibling_triples": "unclassified_at_generation",
        "test_contention_matrix": "unclassified_at_generation",
        "test_cross_partition_contention_keeps_the_fenced_member_unverified": "unclassified_at_generation",
        "test_legacy_null_receipt_with_conflicting_plan_conflicts": "unclassified_at_generation",
        "test_n_way_contention_renders_every_distinct_value": "unclassified_at_generation",
        "test_new_snapshot_less_receipt_verifies_at_v2": "stale_version: reshaped by 0016 D2 at a5c6d82 into test_new_snapshot_less_receipt_verifies_at_v4 (receipt version 2 -> 4); the I9 row cites the R9-2/R10-2 shape as it stood at acceptance",
        "test_public_retry_against_a_legacy_null_receipt_reaches_phase_2": "stale_version: reshaped by 0016 D2 at a5c6d82 into test_public_retry_against_a_legacy_null_receipt_refuses_on_sight \u2014 the continuation branch it named was CLOSED for pre-D2 receipts; repointing would make the I9 row claim a different behaviour",
        "test_refusal_does_not_evict_the_prior": "unclassified_at_generation",
        "test_replaying_an_operation_id_is_a_no_op": "unclassified_at_generation",
        "test_resolving_a_refusal_contention_invalidates_the_wiki_immediately": "unclassified_at_generation",
        "test_the_challenger_gains_no_query_independent_reach_on_context_edges_or_contested": "unclassified_at_generation",
        "test_v3_to_v4_migration_invalidates_pre_v8_wikis": "unclassified_at_generation"
    },
    "0005": {
        "test_capped_projection_identity_matrix": "unclassified_at_generation"
    },
    "0006": {
        "test_local_caller_cannot_supply_origin": "unclassified_at_generation",
        "test_local_source_survives_a_round_trip": "unclassified_at_generation",
        "test_missing_source_id_keeps_the_flag": "unclassified_at_generation",
        "test_source_id_in_a_pre_v4_envelope_is_ignored": "unclassified_at_generation",
        "test_source_id_is_not_reachable_from_the_extractor": "unclassified_at_generation",
        "test_staleness_clearing_matrix": "unclassified_at_generation",
        "test_two_honest_origins_do_not_collide": "unclassified_at_generation",
        "test_v4_export_roundtrip": "unclassified_at_generation",
        "test_v4_file_into_v3_build_is_rejected": "unclassified_at_generation"
    },
    "0007": {
        "test_a_hostile_table_name_is_passed_as_a_value": "unclassified_at_generation",
        "test_a_non_identical_schema_is_refused": "unclassified_at_generation",
        "test_adoption_audit_sink_failure_aborts": "unclassified_at_generation",
        "test_adoption_event_payload_is_typed": "unclassified_at_generation",
        "test_committed_sink_failure_leaves_the_store_adopted": "unclassified_at_generation",
        "test_concurrent_first_open_across_processes": "unclassified_at_generation",
        "test_creation_validates_before_stamping": "unclassified_at_generation",
        "test_drifted_acceleration_index_is_rebuilt": "unclassified_at_generation",
        "test_every_statement_names_its_columns": "unclassified_at_generation",
        "test_first_open_locks_before_reading": "unclassified_at_generation",
        "test_in_memory_store_is_versioned": "unclassified_at_generation",
        "test_legacy_store_is_adopted_losslessly": "stale_version: 0013 \u00a75b replaced adoption-on-open with refuse-then-offline-migrate; the live node is test_s6_a_legacy_store_is_migrated_losslessly, and the S6 row's 'adopted' wording is the superseded contract",
        "test_new_store_is_stamped": "unclassified_at_generation",
        "test_repair_revalidates_before_stamping": "unclassified_at_generation"
    },
    "0008": {
        "test_add_edge_transition_guard": "unclassified_at_generation",
        "test_no_direct_writer_outside_confirm_edge": "unclassified_at_generation",
        "test_no_maintenance_op_clears_staleness": "unclassified_at_generation",
        "test_older_build_cannot_open_a_confirmations_store": "unclassified_at_generation"
    },
    "0009": {
        "test_source_type_derived_user_stated_system_inferred": "unclassified_at_generation"
    },
    "0012": {
        "test_reinforcement_plan_inserts_no_duplicate": "unclassified_at_generation",
        "test_reinforcement_still_advances_observed_at": "renamed: a HISTORY mention \u2014 the \u00a77b row records that this test was inverted AND renamed at implementation to test_reinforcement_no_longer_advances_observed_at; the old name is the row's subject, not a live claim"
    },
    "0014": {
        "test_0010_consolidation_primitives": "unclassified_at_generation",
        "test_0010_visibility_reservation": "unclassified_at_generation",
        "test_a_corrupt_derivation_seam_aborts_the_op": "unclassified_at_generation",
        "test_a_plain_episode_round_trips_with_no_index": "unclassified_at_generation",
        "test_a_v4_import_then_v5_export_reimports_cleanly": "unclassified_at_generation",
        "test_concurrent_consumptions_each_write_one_row": "unclassified_at_generation",
        "test_every_consumed_contributor_is_enumerable": "unclassified_at_generation",
        "test_export_excludes_the_contribution_ledger": "unclassified_at_generation",
        "test_forget_user_erases_the_contribution_ledger": "unclassified_at_generation",
        "test_ledger_rows_are_append_only": "unclassified_at_generation",
        "test_the_consumption_manifest_matches_the_code": "unclassified_at_generation",
        "test_the_severance_capability_gate_binds": "unclassified_at_generation",
        "test_v5_export_round_trips_output_indexes": "unclassified_at_generation"
    },
    "0015": {
        "test_absent_or_invalid_epoch_aba_discards": "unclassified_at_generation",
        "test_legacy_enabled_config_epoch_is_normalized_before_collection": "unclassified_at_generation",
        "test_same_epoch_repair_never_sends_post_erasure_records": "never_written: the I17 list cites it beside the existing test_same_epoch_recreation_never_sends_post_erasure_records as a distinct planned case (a repair path); never written",
        "test_tombstone_after_malformed_drops_records_pre_and_post_post": "never_written: the I17 list cites it beside the existing test_tombstone_after_deletion_drops_records_pre_and_post_post as a distinct planned case (a malformed tombstone); never written",
        "test_windows_death_releases_lock_across_processes": "never_written: the spec marks it '(platform-gated, future)'; only the POSIX twin exists",
        "test_windows_live_holder_exclusion_across_processes": "never_written: the spec marks it '(platform-gated, future)'; only the POSIX twin exists"
    },
    "0016": {
        "test_below_v6_base_refuses_with_the_ladder_message": "stale_version: the head moved past v7 after acceptance; the live node is test_below_v7_base_refuses_with_the_ladder_message over bases 1\u20136, and the row's 'below-v6 (bases 1\u20135)' is the number at acceptance",
        "test_below_v6_open_unchanged": "stale_version: the head moved past v7 after acceptance; the live node is test_below_v7_open_unchanged",
        "test_deletion_is_decision_invisible": "never_written: the I1 projection-compare test was never written under any name (the near match test_metering_is_decision_invisible is 0017's, a different subject)",
        "test_dir_surfaces_include_sourcetype": "stale_version: the I2 row is the D1 deprecation surface (dir INCLUDES SourceType); the same spec's D2 deleted the class and the test became test_dir_surfaces_exclude_sourcetype at a5c6d82 \u2014 the row describes the superseded D1 era",
        "test_field_access_warns_at_pinned_floor": "unclassified_at_generation",
        "test_format_6_refused_by_version_gate": "unclassified_at_generation",
        "test_idempotency_discrimination_post_collapse": "unclassified_at_generation",
        "test_no_receipt_straddles_the_v7_boundary": "unclassified_at_generation",
        "test_old_export_source_type_is_dropped": "unclassified_at_generation",
        "test_pickle_roundtrip_emits_exactly_two_warnings": "unclassified_at_generation",
        "test_sourcetype_import_warns_at_d1": "unclassified_at_generation",
        "test_star_import_namespace_is_byte_identical": "unclassified_at_generation",
        "test_v3_receipts_follow_the_ordinary_contract": "stale_version: receipt version 3 was itself superseded (the live node is test_v4_receipts_follow_the_ordinary_contract); the row's 'version-3 receipt follows the ordinary contract' is the closed set at acceptance",
        "test_v7_step_changes_no_objects": "unclassified_at_generation",
        "test_v7_step_declaration_matches_pin": "unclassified_at_generation"
    },
    "0017": {
        "test_consent_text_does_not_promise_token_totals": "unclassified_at_generation",
        "test_v2_consent_strips_token_fields": "owed_at_implementation: the I4 row itself says 'stage-5 obligation \u2014 none of the three exists yet'; the near match test_v1_consent_strips_new_fields is 0015's v1 test, not this",
        "test_v2_to_v3_transition_through_a_live_memory_carrier": "owed_at_implementation: the I4 row itself says 'stage-5 obligation \u2014 none of the three exists yet'; the near match is 0015's v1->v2 test, not this"
    },
    "0018": {
        "test_base_6_proceeds_through_the_audited_operation": "stale_version: the head moved past v7 after acceptance; the live node is test_base_7_proceeds_through_the_audited_operation",
        "test_below_v6_base_refuses_with_the_ladder_message": "stale_version: the head moved past v7 after acceptance; the live node is test_below_v7_base_refuses_with_the_ladder_message over bases 1\u20136",
        "test_below_v6_open_unchanged": "stale_version: the head moved past v7 after acceptance; the live node is test_below_v7_open_unchanged"
    },
    "0019": {
        "test_below_v6_base_refuses_with_the_ladder_message": "stale_version: quoted from 0018's final-form amendment; the head moved past v7 after acceptance (live node test_below_v7_base_refuses_with_the_ladder_message)",
        "test_below_v6_open_unchanged": "stale_version: quoted from 0018's final-form amendment; the head moved past v7 after acceptance (live node test_below_v7_open_unchanged)"
    },
    "0020": {
        "test_import_reconstruction_precommit": "unclassified_at_generation"
    },
    "0021": {
        "test_import_contribution_primitive": "unclassified_at_generation"
    },
    "0022": {
        "test_busy_is_retryable_and_collision_is_not": "unclassified_at_generation",
        "test_closure_is_transitive_and_recursive": "unclassified_at_generation",
        "test_completeness_statement_is_honest": "unclassified_at_generation",
        "test_dry_run_equals_the_commit": "unclassified_at_generation",
        "test_effect_verbs_are_closed": "unclassified_at_generation",
        "test_lift_is_desired_state_not_undo": "unclassified_at_generation",
        "test_no_update_writer_against_source_revocations": "unclassified_at_generation",
        "test_recompute_is_exact_and_restrict_only": "unclassified_at_generation",
        "test_retired_synthesized_counted_separately": "unclassified_at_generation",
        "test_revocation_does_not_cross_the_user_boundary": "unclassified_at_generation",
        "test_revocation_drops_the_wiki": "unclassified_at_generation",
        "test_revocation_grants_nothing": "unclassified_at_generation",
        "test_revocation_is_not_exposed_on_the_agent_surfaces": "unclassified_at_generation",
        "test_revocation_never_clears_the_ungrounded_flag": "unclassified_at_generation",
        "test_revocation_reference_vectors": "unclassified_at_generation",
        "test_revocation_retains_every_record": "unclassified_at_generation",
        "test_revocation_state_is_derived_not_stored": "unclassified_at_generation",
        "test_revoked_source_retires_direct_records": "unclassified_at_generation",
        "test_second_revoke_is_a_no_op": "unclassified_at_generation",
        "test_sole_basis_requires_a_different_identity": "unclassified_at_generation",
        "test_source_revocations_is_append_only": "unclassified_at_generation",
        "test_the_evidence_transcript_validates_against_the_ledger": "unclassified_at_generation",
        "test_the_sweep_retires_through_the_sole_writer": "unclassified_at_generation",
        "test_two_hosts_cannot_allocate_one_ordinal": "unclassified_at_generation",
        "test_unknown_source_is_not_revocable": "unclassified_at_generation",
        "test_user_authored_unattributed_is_counted": "unclassified_at_generation"
    },
    "0023": {
        "test_cold_pool_unchanged_without_revocations": "unclassified_at_generation",
        "test_reinforcement_transfers_nothing_unchanged": "unclassified_at_generation"
    },
    "0025": {
        "test_portability_version_gate": "unclassified_at_generation",
        "test_prompt_bytes_exact": "unclassified_at_generation",
        "test_receipt_era_semantic_equivalence": "unclassified_at_generation"
    },
    "0029": {
        "test_a_failed_commit_discards_the_import_counts": "unclassified_at_generation",
        "test_the_duplicate_race_raises_at_the_insert_not_the_commit": "unclassified_at_generation"
    },
    "0030": {
        "test_five_leg_binding": "unclassified_at_generation",
        "test_legs_are_identity_bound_before_anything": "unclassified_at_generation"
    },
    "0031": {
        "test_apply_proposal_is_one_transaction": "unclassified_at_generation",
        "test_every_nullable_check_states_its_null_case": "unclassified_at_generation",
        "test_forget_user_erases_proposals": "unclassified_at_generation",
        "test_no_mcp_path_to_trust_mutation": "unclassified_at_generation",
        "test_no_undifferentiated_acceptance": "unclassified_at_generation",
        "test_p3_3_records_the_elevation_as_a_finding": "unclassified_at_generation",
        "test_proposal_ddl_refuses_and_accepts": "unclassified_at_generation",
        "test_proposal_is_not_a_fact": "unclassified_at_generation",
        "test_proposal_kinds_closed": "unclassified_at_generation",
        "test_proposal_mutates_nothing": "unclassified_at_generation",
        "test_proposal_queue_refuses_not_evicts": "unclassified_at_generation",
        "test_resolution_fk_is_enforced_not_declared": "unclassified_at_generation",
        "test_schedules_are_serializable": "unclassified_at_generation",
        "test_undo_is_forward_only": "unclassified_at_generation",
        "test_undo_is_scoped_to_its_txn": "unclassified_at_generation",
        "test_undo_refuses_on_intervening_state": "unclassified_at_generation"
    },
    "0038": {
        "test_every_frozen_text_yields_exactly_one_episode": "unclassified_at_generation",
        "test_no_bare_instruction_is_stored_as_a_completed_action": "unclassified_at_generation",
        "test_silent_coercion_residual_is_reported": "unclassified_at_generation",
        "test_third_party_claim_receipt_is_exempt": "unclassified_at_generation",
        "test_user_disposition_on_a_third_party_event_is_refused": "unclassified_at_generation"
    }
}

#: the (spec, name) pairs present when this file was GENERATED — the only ones
#: allowed to carry `unclassified_at_generation`
GENERATION_SET: frozenset = frozenset(
    (spec, name) for spec, names in CITATION_DEBT.items() for name in names
    if names[name] == "unclassified_at_generation")

#: the entries STILL carrying the grandfather reason — derived at import, the
#: one number that says whether the debt is being paid (174 at generation; it
#: can only fall)
def unclassified_remaining(table=None) -> int:
    """The grandfather count over `table` (default: the live CITATION_DEBT). A
    FUNCTION, not only a constant, so a test can re-derive it after planting an
    entry: GENERATION_SET is derived from the table at import, which makes the
    "reserved for the frozen set" check in problems() unfalsifiable against an
    entry EDITED INTO THE FILE — that loophole is closed by the ceiling
    tests/test_spec_gate.py pins over this number (an ocr review of the v0.21.0
    range found the tautology, 2026-09-11)."""
    names_by_spec = CITATION_DEBT if table is None else table
    return sum(1 for names in names_by_spec.values() for r in names.values()
               if r == "unclassified_at_generation")


UNCLASSIFIED_REMAINING: int = unclassified_remaining()


def test_defs(root):
    import pathlib, re
    root = pathlib.Path(root); defs = set()
    for pat in ("tests/**/*.py", "specs/evidence/**/*.py"):
        for p in root.glob(pat):
            defs |= set(re.findall(r"^def (test_[A-Za-z0-9_]+)\(", p.read_text(), re.M))
    return defs


def unresolved_by_spec(root):
    """The DERIVATION the gate compares against CITATION_DEBT's keys."""
    import pathlib, re
    root = pathlib.Path(root); defs = test_defs(root)
    out = {}
    for spec in sorted((root / "specs").glob("[0-9]*.md")):
        text = spec.read_text()
        m = re.search(r"^Spec-Status:\s*(\S+)", text, re.M)
        if not m or m.group(1) != "accepted":
            continue
        names = sorted(set(re.findall(r"`(?:[\w/.:-]*::)?(test_[A-Za-z0-9_]+)`", text)) - defs)
        if names:
            out[spec.name[:4]] = names
    return out


def problems(root) -> list:
    """Everything the gate refuses, as sentences: new unresolved citations, debt
    entries that now resolve, reasons outside the vocabulary, and
    `unclassified_at_generation` on a pair that was not frozen."""
    live = unresolved_by_spec(root)
    out = []
    for spec, names in live.items():
        for n in names:
            if n not in CITATION_DEBT.get(spec, {}):
                out.append(f"{spec} {n}: NEW unresolved citation — fix the spec, or declare it with a reason")
    for spec, entries in CITATION_DEBT.items():
        for n, reason in entries.items():
            if n not in live.get(spec, []):
                out.append(f"{spec} {n}: now resolves (or is no longer cited) — remove it; the ratchet only shrinks")
            if reason.split(":", 1)[0] not in REASONS:
                out.append(f"{spec} {n}: reason {reason!r} outside {REASONS}")
            if reason == "unclassified_at_generation" and (spec, n) not in GENERATION_SET:
                out.append(f"{spec} {n}: unclassified_at_generation is reserved for the frozen generation set")
    return out


def suggestions(root, cutoff=0.85):
    import difflib
    defs = sorted(test_defs(root)); out = []
    for spec, names in unresolved_by_spec(root).items():
        for n in names:
            near = difflib.get_close_matches(n, defs, n=1, cutoff=cutoff)
            if near:
                out.append((spec, n, near[0]))
    return out


if __name__ == "__main__":
    import json as _json, pathlib as _pl, sys as _sys
    _root = _pl.Path(__file__).resolve().parent.parent
    if "--suggest" in _sys.argv:
        for spec, n, near in suggestions(_root):
            print(f"{spec}  {n}\n      ~ {near}")
        print(f"{len(suggestions(_root))} near-match suggestion(s) — hints, never applied")
    elif "--write" in _sys.argv:
        live = unresolved_by_spec(_root); new = {}
        for spec, names in live.items():
            for n in names:
                if n not in CITATION_DEBT.get(spec, {}):
                    new.setdefault(spec, []).append(n)
        if new:
            print("REFUSED: new unresolved citations need a declared reason (edit the table by hand):", _json.dumps(new))
            _sys.exit(2)
        kept = {spec: {n: CITATION_DEBT[spec][n] for n in names} for spec, names in live.items()}
        src = _pl.Path(__file__).read_text()
        head, _, _tail = src.partition("CITATION_DEBT: dict = ")
        rest = src[src.index("\n\n#: the (spec, name) pairs present"):]
        _pl.Path(__file__).write_text(head + "CITATION_DEBT: dict = " + _json.dumps(kept, indent=4, sort_keys=True) + rest)
        print("citation debt regenerated:", sum(len(v) for v in kept.values()), "over", len(kept), "accepted specs")
    else:
        for p in problems(_root):
            print(p)
        print(f"{len(problems(_root))} problem(s)")
