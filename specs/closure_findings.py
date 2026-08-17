"""One row per REVIEW FINDING, with the evidence that closes it.

External round 5, R5-3. `render_closure.py` generated one row per ROUND with
the verdict truncated to 300 characters, and PROCESS §4a requires one row per
FINDING with an openable command, test or commit. A round-level summary is not
a closure ledger; it is a shorter verdict.

`evidence` is a STRING A REVIEWER CAN RUN OR OPEN — a pytest node id, a
harness invocation, a `git show`, a `grep`. Not "see §4f". The rule this
project keeps relearning is that a claim with no executable behind it decays
into prose, and this field is where that is refused.

`closed_in` names the carrier(s) the fix landed in, so a reader can check the
fix is where the ledger says it is.
"""

# (spec, round_kind, round_no, finding, summary, closed_in, evidence)
CLOSURES = [
    # ---- 0022 -----------------------------------------------------------
    ("0022", "external", 1, "F2",
     "the standing state ordered by (at, seq) with a HOST-SUPPLIED `at`, so a "
     "planted far-future timestamp made a revocation permanently unliftable",
     "§4a, R1, reference_revocation.standing_revocations",
     "python3 specs/evidence/0022/vector_harness.py  "
     "# 5 clock-skew vectors: standing_a_far_future_revoke_is_still_liftable, "
     "standing_a_clock_rollback_does_not_undo_the_latest_append, "
     "standing_identical_timestamps_are_ordered_by_seq_alone, "
     "standing_row_order_in_the_list_does_not_decide, "
     "standing_the_epoch_timestamp_cannot_resurrect_a_lift"),
    ("0022", "external", 1, "F3",
     "'supersession, never edit' was true of no carrier in the product — the "
     "reference mutated in place against an abstract history list with no "
     "product analogue",
     "§4f, C3, R9, reference_revocation.apply_effects",
     "python3 specs/lint_withdrawn.py  "
     "# rules 0022-retirement-is-a-new-event and 0022-history-only-grew fail "
     "the build on any live restatement"),
    ("0022", "external", 1, "F4",
     "class (c) gated on `system_authored` was not the upper bound it "
     "advertised: a pre-0014 absorption survivor keeps the incoming record's "
     "USER authorship while carrying transferred values no ledger row names",
     "§4c, §2c, §9, R7",
     "python3 specs/evidence/0022/vector_harness.py  "
     "# sweep_a_pre_0014_user_authored_absorption_survivor_is_counted — it "
     "BITES: 1 under the old predicate, 5 under the new"),
    ("0022", "external", 2, "R3-1",
     "§4e-i printed `with conn:` and labelled it BEGIN IMMEDIATE; it begins "
     "nothing, and the harness was green on a DIFFERENT construction",
     "§4e-i, store_concurrency_harness.revocation_operation",
     "python3 specs/evidence/0022/store_concurrency_harness.py  "
     "# the operation is the one the spec prints"),
    ("0022", "external", 2, "R3-2",
     "the withdrawn class-(c) authorship condition was still normative in "
     "§2c, because the lint pattern matched the forward wording and not the "
     "reversed wording the cell used",
     "§2c, withdrawn_phrases.py rule 0022-class-c-is-system-authored",
     "python3 specs/lint_withdrawn.py"),
    ("0022", "external", 3, "R4-1",
     "`revocation_operation` was neither atomic nor actually shared: it "
     "appended the row and NEVER APPLIED THE EFFECTS, discarded `reason` and "
     "`at`, and its BUSY regression exercised a different helper",
     "store_concurrency_harness.revocation_operation, §4e-i",
     "python3 specs/evidence/0022/store_concurrency_harness.py  "
     "# EFFECTS LAND / ATOMIC (mid-effect) / ATOMIC (absent record) / METADATA"),
    ("0022", "external", 4, "R5-1",
     "the failure outcomes were not total: a failing ROLLBACK was suppressed "
     "and re-raised as the original error, and EVERY IntegrityError was "
     "converted to OrdinalCollision",
     "store_concurrency_harness: RevocationUnknownState, "
     "RevocationIntegrityError, _is_ordinal_violation, _rollback_or_poison",
     "python3 specs/evidence/0022/store_concurrency_harness.py  "
     "# 'a FAILING ROLLBACK is reported as UNKNOWN STATE' and 'a NON-ordinal "
     "integrity fault is NOT reported as a collision'"),
    ("0022", "external", 4, "R5-2",
     "two claimed regressions did not exercise their named branches: the BUSY "
     "test measured SQLite's internal wait (one BEGIN, zero caught errors) and "
     "the collision test raised OrdinalCollision by hand",
     "store_concurrency_harness: the BUSY, BUSY-DEADLINE, unreachability and "
     "classifier checks",
     "python3 specs/evidence/0022/store_concurrency_harness.py  "
     "# BUSY counts the loop's OWN attempts with busy_timeout=0; the collision "
     "branch is proven UNREACHABLE through the construction and the classifier "
     "is covered on REAL errors"),
    # ---- 0023 -----------------------------------------------------------
    ("0023", "external", 1, "F1",
     "quarantine reached ONE consumer of five; a quarantined episode still "
     "entered the gate's grounded partition and the wiki compiler's input",
     "§4a-iv, N14, N15, Episode.assertable",
     "grep -rn 'third_party_influenced' src/veracium/  "
     "# every episode-text consumer must route through Episode.assertable"),
    ("0023", "external", 2, "R3-3",
     "the lifecycle fix over-excluded and broke N12: Episode.assertable drops "
     "ordinary quarantined/use-only episodes in a store with ZERO revocations",
     "§7a lifecycle row, N12, N15",
     "grep -n 'STANDING REVOCATION' specs/0023-non-revival-under-maintenance.md"),
    ("0023", "external", 3, "R4-2",
     "§7a's header said all seven consumers call Episode.assertable while its "
     "own lifecycle row said lifecycle must not — following the header "
     "recreated the N12 regression; N12's row was malformed",
     "§7a header, §7a lifecycle row, N12",
     "awk -F'|' '/^\\| \\*\\*N12\\*\\*/{print NF-2}' "
     "specs/0023-non-revival-under-maintenance.md  # must print 2"),
    # ---- package / process ---------------------------------------------
    ("0022", "external", 3, "R4-3",
     "the closure ledgers had drifted for a third round — a count disagreeing "
     "with its own rows, a placeholder claiming it had been removed",
     "specs/render_closure.py, both closure sections",
     "python3 specs/render_closure.py --check"),
    ("0022", "external", 3, "R4-4",
     "skip_inventory.render()'s category list was hard-coded and dropped "
     "future-obligation, so four entries reached the data and never the block",
     "specs/skip_inventory.py render()/reconcile(), tests/test_spec_gate.py",
     "python3 -m pytest tests/test_spec_gate.py -k "
     "'reconcile or silently_drop or emitted_reason'"),
    ("0022", "external", 4, "R5-4",
     "reconcile() matched pytest's EMITTED reason against SOURCE-SITE tokens, "
     "so a listed skip read as unlisted on a root host only",
     "specs/skip_inventory.py EMITTED, tests/test_spec_gate.py",
     "python3 -m pytest tests/test_spec_gate.py -k emitted_reason"),
    ("0022", "external", 4, "R5-3",
     "the generated closure was one row per ROUND with a truncated verdict; "
     "PROCESS §4a requires one row per FINDING with openable evidence",
     "specs/closure_findings.py (this file), specs/render_closure.py",
     "python3 specs/render_closure.py --check"),
]
