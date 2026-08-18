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

**`$PY` IS THE REVIEWER'S INTERPRETER** — the venv the offline launcher builds
at `.venv-offline/bin/python`, or any interpreter with the pinned test
dependencies. External round 7 found four evidence commands that could not run
as written because they said `python3`, and a bare `python3` has no pytest.
Evidence that does not execute in the environment the package ships is a
description, which is the defect this field exists to prevent:

    export PY=.venv-offline/bin/python     # after `bash specs/evidence/offline/run_offline.sh`
"""

# (spec, round_kind, round_no, finding, summary, closed_in, evidence)
CLOSURES = [
    # ---- 0022 -----------------------------------------------------------
    ("0022", "external", 1, "F2",
     "the standing state ordered by (at, seq) with a HOST-SUPPLIED `at`, so a "
     "planted far-future timestamp made a revocation permanently unliftable",
     "§4a, R1, reference_revocation.standing_revocations",
     "$PY specs/evidence/0022/vector_harness.py  "
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
     "$PY specs/lint_withdrawn.py  "
     "# rules 0022-retirement-is-a-new-event and 0022-history-only-grew fail "
     "the build on any live restatement"),
    ("0022", "external", 1, "F4",
     "class (c) gated on `system_authored` was not the upper bound it "
     "advertised: a pre-0014 absorption survivor keeps the incoming record's "
     "USER authorship while carrying transferred values no ledger row names",
     "§4c, §2c, §9, R7",
     "$PY specs/evidence/0022/vector_harness.py  "
     "# sweep_a_pre_0014_user_authored_absorption_survivor_is_counted — it "
     "BITES: 1 under the old predicate, 5 under the new"),
    ("0022", "external", 3, "R3-1",
     "§4e-i printed `with conn:` and labelled it BEGIN IMMEDIATE; it begins "
     "nothing, and the harness was green on a DIFFERENT construction",
     "§4e-i, store_concurrency_harness.revocation_operation",
     "$PY specs/evidence/0022/store_concurrency_harness.py  "
     "# the operation is the one the spec prints"),
    ("0022", "external", 3, "R3-2",
     "the withdrawn class-(c) authorship condition was still normative in "
     "§2c, because the lint pattern matched the forward wording and not the "
     "reversed wording the cell used",
     "§2c, withdrawn_phrases.py rule 0022-class-c-is-system-authored",
     "$PY specs/lint_withdrawn.py"),
    ("0022", "external", 4, "R4-1",
     "`revocation_operation` was neither atomic nor actually shared: it "
     "appended the row and NEVER APPLIED THE EFFECTS, discarded `reason` and "
     "`at`, and its BUSY regression exercised a different helper",
     "store_concurrency_harness.revocation_operation, §4e-i",
     "$PY specs/evidence/0022/store_concurrency_harness.py  "
     "# EFFECTS LAND / ATOMIC (mid-effect) / ATOMIC (absent record) / METADATA"),
    ("0022", "external", 5, "R5-1",
     "the failure outcomes were not total: a failing ROLLBACK was suppressed "
     "and re-raised as the original error, and EVERY IntegrityError was "
     "converted to OrdinalCollision",
     "store_concurrency_harness: RevocationUnknownState, "
     "RevocationIntegrityError, _is_ordinal_violation, _rollback_or_poison",
     "$PY specs/evidence/0022/store_concurrency_harness.py  "
     "# 'a FAILING ROLLBACK is reported as UNKNOWN STATE' and 'a NON-ordinal "
     "integrity fault is NOT reported as a collision'"),
    ("0022", "external", 5, "R5-2",
     "two claimed regressions did not exercise their named branches: the BUSY "
     "test measured SQLite's internal wait (one BEGIN, zero caught errors) and "
     "the collision test raised OrdinalCollision by hand",
     "store_concurrency_harness: the BUSY, BUSY-DEADLINE, unreachability and "
     "classifier checks",
     "$PY specs/evidence/0022/store_concurrency_harness.py  "
     "# BUSY counts the loop's OWN attempts with busy_timeout=0; the collision "
     "branch is proven UNREACHABLE through the construction and the classifier "
     "is covered on REAL errors"),
    # ---- 0023 -----------------------------------------------------------
    ("0023", "external", 1, "F1",
     "quarantine reached ONE consumer of five; a quarantined episode still "
     "entered the gate's grounded partition and the wiki compiler's input",
     "§4a-iv, N14, N15, Episode.assertable",
     # R6-3: the previous command grepped `third_party_influenced` and printed
     # the CURRENT, UNMODIFIED consumers — it demonstrated the defect, not its
     # closure. The specs are drafts, so the closure lives in the spec's own
     # inventory and its gate, and the evidence must show THAT.
     "grep -n 'SIX of the seven text consumers call' "
     "specs/0023-non-revival-under-maintenance.md && "
     "$PY specs/render_closure.py --check"),
    ("0023", "external", 3, "R3-3",
     "the lifecycle fix over-excluded and broke N12: Episode.assertable drops "
     "ordinary quarantined/use-only episodes in a store with ZERO revocations",
     "§7a lifecycle row, N12, N15",
     "grep -n 'STANDING REVOCATION' specs/0023-non-revival-under-maintenance.md"),
    ("0023", "external", 4, "R4-2",
     "§7a's header said all seven consumers call Episode.assertable while its "
     "own lifecycle row said lifecycle must not — following the header "
     "recreated the N12 regression; N12's row was malformed",
     "§7a header, §7a lifecycle row, N12",
     "awk -F'|' '/^\\| \\*\\*N12\\*\\*/{print NF-2}' "
     "specs/0023-non-revival-under-maintenance.md  # must print 2"),
    # ---- package / process ---------------------------------------------
    ("0022", "external", 4, "R4-3",
     "the closure ledgers had drifted for a third round — a count disagreeing "
     "with its own rows, a placeholder claiming it had been removed",
     "specs/render_closure.py, both closure sections",
     "$PY specs/render_closure.py --check"),
    ("0022", "external", 4, "R4-4",
     "skip_inventory.render()'s category list was hard-coded and dropped "
     "future-obligation, so four entries reached the data and never the block",
     "specs/skip_inventory.py render()/reconcile(), tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k "
     "'reconcile or silently_drop or emitted_reason'"),
    ("0022", "external", 5, "R5-4",
     "reconcile() matched pytest's EMITTED reason against SOURCE-SITE tokens, "
     "so a listed skip read as unlisted on a root host only",
     "specs/skip_inventory.py EMITTED, tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k emitted_reason"),
    ("0022", "external", 5, "R5-3",
     "the generated closure was one row per ROUND with a truncated verdict; "
     "PROCESS §4a requires one row per FINDING with openable evidence",
     "specs/closure_findings.py (this file), specs/render_closure.py",
     "$PY specs/render_closure.py --check"),
    # ---- filled at external round 6 (R6-3): every id `reviews.py` names -----
    ("0022", "internal", 1, "S1",
     "the sweep's record DOMAIN was unenumerated — 'records' meant EDGES, "
     "while episode text renders into recall context and the episodes table "
     "has no retirement column",
     "§4b-i (the enumerated record-type table), §4b-ii, R18",
     "grep -n '4b-i' specs/0022-source-revocation.md  "
     "# every stored type with its mechanism or its EXECUTED exclusion"),
    ("0022", "internal", 1, "M1",
     "Q6's rationale was false across time: 'the sweep is a pure function and "
     "can be re-run' is pure over inputs that MUTATE, so a re-run answers the "
     "present, not what the revocation reached",
     "§10 Q6",
     "grep -n 'pure over inputs that MUTATE' specs/0022-source-revocation.md"),
    ("0022", "internal", 1, "M4",
     "complete=False is the expected steady state on any consolidation-bearing "
     "store, and operators had not been told",
     "§8",
     "grep -n 'EXPECTED STEADY STATE' specs/0022-source-revocation.md"),
    ("0022", "external", 3, "R3-4",
     "the closure ledgers said THREE ROUNDS while enumerating four, claimed "
     "rows were below, and still carried 'no review rounds yet (draft)'",
     "specs/render_closure.py (the ledger is generated)",
     "$PY specs/render_closure.py --check"),
    ("0022", "external", 3, "R3-5",
     "COLLECTED did not reconcile: the decomposition implied 14 skips beside a "
     "measured line of 6, and four unconditional skips were invisible to the "
     "completeness gate's regex",
     "specs/skip_inventory.py (reconcile + the widened site regex), "
     "tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k "
     "'reconcile or conditional_skip or emitted_reason'"),
    ("0023", "internal", 1, "S1",
     "the coupled round's 0023 half — the sweep's record domain, inherited "
     "through the mutual Spec-Requires",
     "0022 §4b-i, and 0023's §7a consumer inventory",
     "$PY specs/render_closure.py --check  # both specs' ledgers"),
    ("0023", "internal", 1, "S2",
     "the lift asymmetry's justification was attackable: '_disclosure_for's "
     "inputs are not decidable from the record' is false — they are ALL on the "
     "record",
     "§4i (the two-floors argument), Q2",
     "grep -n 'TWO FLOORS' specs/0023-non-revival-under-maintenance.md"),
    ("0023", "internal", 2, "S3",
     "quarantine-at-birth wrote a field NO reader consulted: edges fenced on "
     "e.quarantined, episodes split on authorship only",
     "§4a-iv, N14",
     "grep -n '4a-iv' specs/0023-non-revival-under-maintenance.md"),
    ("0023", "external", 3, "F4",
     "N15 was not a total inventory: it swept for reads of the OLD CONDITION, "
     "so a consumer that never had one passed — and a seventh consumer "
     "(lifecycle.py:182, the consolidation prompt) was invisible",
     "N15, §7a",
     "grep -rn '\\.summary' src/veracium/ | grep -v test  "
     "# every episode-text consumer the inventory must disposition"),
    ("0023", "internal", 1, "M2",
     "renewal was the one §4 seam with no executed §2c-ii command — and "
     "running it showed there is NO renewal verb at all",
     "§4g, N7",
     "grep -rn 'renew' src/veracium/ --include=*.py  "
     "# only consolidation LEASES; 0012 deleted reinforcement's transfers"),
    ("0023", "internal", 1, "M3",
     "the wiki row's third path — the supersession-refusal cell — was covered "
     "by neither 'quarantine never enters' nor '0022 retires'",
     "§3 wiki row, §7b 0004 row",
     "grep -n 'THIRD path' specs/0023-non-revival-under-maintenance.md"),
    # ---- external round 6 -------------------------------------------------
    ("0022", "external", 6, "R6-1",
     "the rollback boundary was not total: _rollback_or_poison caught "
     "Exception while the operation caught BaseException, so a "
     "KeyboardInterrupt during ROLLBACK escaped as itself — connection open, "
     "in_transaction, uncommitted row surviving",
     "store_concurrency_harness._rollback_or_poison",
     "$PY specs/evidence/0022/store_concurrency_harness.py  "
     "# 'a BaseException during ROLLBACK is ALSO unknown state, not a leak'"),
    ("0022", "external", 6, "R6-2",
     "§4e-i's block is generated byte-for-byte from the executable and the "
     "page still carried round 5's 'verbatim is withdrawn — the executable "
     "differs materially': three carriers, two answers",
     "§4e-i (the withdrawal deleted)",
     # R7-1: the previous command grepped a string that appears in THIS
     # LEDGER ROW, so it succeeded by finding its own description. Evidence
     # must interrogate the SPEC. `grep -c` on the spec returns 0 and exits 1
     # when absent, so the absence is asserted rather than described.
     # The needle is the WITHDRAWAL ASSERTION itself, not a phrase from it.
     # My first version grepped 'differs materially', which appears in the
     # paragraph EXPLAINING the deletion and in the generated ledger row — so
     # it failed on a clean tree. Mention is not use, for the fifth time in
     # this review, and the fix is always the same: aim at the claim.
     # R7-1's tail: a grep-for-absence rendered INTO the document it searches
     # supplies its own needle, so this command failed on a clean tree. The
     # assertion moved to a test, where the ledger can point at it without
     # becoming it.
     "$PY -m pytest tests/test_spec_gate.py "
     "-k 'round5_verbatim' && $PY specs/render_operation.py"),
    ("0022", "external", 6, "R6-3",
     "the closure ledger was a HAND-MAINTAINED SECOND LIST — the thing "
     "render_closure was introduced to eliminate — at 12/17 and 3/9, with "
     "--check green because it compared the block to that same list",
     "specs/render_closure.py completeness_problems(), tests/test_spec_gate.py",
     "$PY specs/render_closure.py --check  "
     "# ids EXTRACTED from reviews.py; every one must have a row"),
    ("0022", "external", 6, "R6-4",
     "the offline launcher invented its own qualification rule and CERTIFIED "
     "an unqualified runtime: SQLite 3.53.1 accepted, 660 FAILED / 951 passed "
     "/ 31 errors, while runtime_supported() returned False",
     "specs/evidence/offline/run_offline.sh",
     "bash specs/evidence/offline/run_offline.sh  "
     "# asks runtime_supported() and exits 2 unless it is exactly True"),
    ("0023", "external", 6, "R6-3",
     "its closure ledger was 3/9 against the findings reviews.py names",
     "specs/closure_findings.py, validated by render_closure",
     "$PY specs/render_closure.py --check"),
    # ---- external round 7 -------------------------------------------------
    ("0022", "external", 7, "R7-1",
     "closure validation compared SETS OF IDS, so a wrong round, an erased "
     "evidence string, an extra row and a duplicate row all passed; the "
     "cross-spec stripper ate `0022 R99-1`; counts in prose disagreed with the "
     "rows (26 claimed, 31 present); and four evidence commands did not run",
     "specs/reviews.py (structural `raised=`), specs/render_closure.py "
     "(exact (spec, kind, round, id) validation + derived counts), "
     "specs/closure_findings.py ($PY-parameterised evidence), "
     "tests/test_spec_gate.py",
     "$PY specs/render_closure.py --check && "
     "$PY -m pytest tests/test_spec_gate.py -k "
     "'closure_ledger_is_complete or closure_evidence_command'"),
    ("0022", "external", 7, "R7-2",
     "the reproduction carrier described the SQLite-floor launcher a round "
     "after the code changed, and repeated the previous round's launcher "
     "result against a different test set",
     "specs/package/collected_header.txt, specs/seal_package.py (the sealer "
     "RUNS the launcher and substitutes what it printed)",
     "grep -q '__LAUNCHER__' specs/package/collected_header.txt && "
     "grep -q 'the sealer RUNS the launcher' specs/seal_package.py"),
    # ---- external round 8 -------------------------------------------------
    ("0022", "external", 8, "R8-1",
     "the structured closure had an ADMISSION HOLE: `raised` was read with "
     ".get(..., []), so omitting the field was indistinguishable from "
     "declaring no findings — a verdict naming R99-1 with no `raised` produced "
     "zero problems, and the displayed count came from the legacy `findings=` "
     "which disagrees with `raised` in four rows",
     "specs/render_closure.py (omission raises; the count is derived), "
     "specs/reviews.py (0023 external 7 declares raised=[]; the legacy field "
     "documented), tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k "
     "'returned_verdict_must_declare or comes_from_raised'"),
    ("0022", "external", 8, "R8-2",
     "four package claims were hand-maintained and false: harness 17/17 "
     "against an 18/18 executable, 'All 31' evidence commands against a 33-row "
     "ledger, a packaged-state claim the sealer's own order contradicts, and a "
     "git-checkout blurb describing a workflow that had stopped being true",
     "specs/seal_package.py (harnesses RUN, evidence split derived), "
     "specs/package/collected_header.txt (two-phase described), "
     "specs/skip_inventory.py (the git-checkout blurb)",
     "grep -q '__HARNESSES__' specs/package/collected_header.txt && "
     "grep -q '__EVIDENCE__' specs/package/collected_header.txt && "
     "grep -q 'TWO-PHASE' specs/package/collected_header.txt && "
     "! grep -q 'measuring copy has no .git' specs/skip_inventory.py && "
     # the fifth carrier, and the mechanical sweep that replaces hand-checking
     "! grep -q 'PACKAGED-STATE' specs/skip_inventory.py && "
     "grep -q 'WITHDRAWN_CLAIMS' specs/seal_package.py"),
    # ---- external round 9 -------------------------------------------------
    ("0022", "external", 9, "R9-1",
     "both package carriers claimed the sealer reran 'both harnesses and both "
     "verifiers from the EXTRACTED archive'; verify_archive() ran the two "
     "harnesses only, the verifiers having run before the archive existed "
     "against the build tree",
     "specs/seal_package.py EXTRACTION_CHECKS (all six run from the "
     "extraction), specs/package/collected_header.txt (__EXTRACTED__ generated "
     "from the registry), tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k extraction_check_list"),
    # ---- external round 10 ------------------------------------------------
    ("0022", "external", 10, "R10-1",
     "the reviewer guide said measurement happens in a separate extracted "
     "archive with no .git, so the measured line already reflected the "
     "reviewer's shape; the sealer measures the author's git checkout — and "
     "the guide promised command/environment/pytest-version/node-count that "
     "COLLECTED did not carry",
     "specs/REVIEWER_GUIDE.md (one canonical protocol), "
     "specs/seal_package.py (__CONTEXT__ generated; the guard reads the guide)",
     "! grep -q 'That copy has no `.git`' specs/REVIEWER_GUIDE.md && "
     "grep -q '__CONTEXT__' specs/package/collected_header.txt && "
     "grep -q 'REVIEWER_GUIDE.md' specs/seal_package.py"),
    ("0022", "external", 10, "R10-2",
     "the extraction registry bound LABELS not behaviour: swapping "
     "verify_collected's command for `python -c pass` while keeping its label "
     "was accepted, and the advertised render_operation `--check` was absent "
     "from the executed argv",
     "specs/seal_package.py (argv), specs/render_operation.py (--check is "
     "real), tests/test_spec_gate.py (argv pinning + the no-op adversary)",
     "$PY -m pytest tests/test_spec_gate.py -k "
     "'extraction_check_list or corrupting_the_packaged'"),
    ("0022", "external", 10, "R10-3",
     "git-archived members were root/root while the appended carriers carried "
     "the sealing user's uid/gid, so a plain `tar -xzf` exited 2 and "
     "--no-same-owner was needed to open the package",
     "specs/seal_package.py (normalised TarInfo + a plain-tar extraction gate)",
     "grep -q 'info.uname = info.gname = .root.' specs/seal_package.py && "
     "grep -q 'plain .tar -xzf. FAILS' specs/seal_package.py"),
    # ---- external round 11 ------------------------------------------------
    ("0022", "external", 11, "R11-1",
     "the verifier binding was textual: the regression only required the "
     "inline program to CONTAIN `verify_collected` and `COLLECTED`, so "
     "`python -c \"pass # verify_collected COLLECTED\"` was accepted with the "
     "original label",
     "specs/verify_extracted.py (named scripts), specs/seal_package.py "
     "(full argv, no inline -c), tests/test_spec_gate.py (argv pinning + a "
     "corrupt-the-carrier mutation)",
     "$PY -m pytest tests/test_spec_gate.py -k "
     "'extraction_check_list or corrupting_the_packaged'"),
    ("0022", "external", 11, "R11-2",
     "sealing inherited the whole environment, so VERACIUM_EVIDENCE_CHILD=1 "
     "turned the evidence runner into a skip while the sealer still generated "
     "the all-commands-ran claim from the ledger's length",
     "specs/seal_package.py sealed_env() + the observed evidence claim + "
     "refusing probes, tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k "
     # NOT `transcript_validates`: that test reads the LIVE transcript, which
     # the evidence runner is rewriting as it executes this command — the
     # self-reference R12-1/R12-2 already hit, walked back into while
     # repointing a stale selector. THE RULE: ledger evidence must never
     # select a test that reads an artifact the runner is producing. The
     # observed-claim half is shown by the sealer reading the transcript
     # instead of counting the ledger.
     "sealed_environment && "
     "grep -q 'evidence_transcript.validate' specs/seal_package.py"),
    # ---- external round 12 ------------------------------------------------
    ("0022", "external", 12, "R12-1",
     "the transcript shipped at the archive root while COLLECTED named "
     "specs/generated/evidence_run.json, and verify_archive() never looked at "
     "it — removing it entirely still produced a passing archive",
     "specs/seal_package.py (ships at REL_PATH; a seventh extraction check "
     "validates it), specs/evidence_transcript.py",
     # NOT `evidence_transcript.py` itself: that validates the transcript the
     # evidence runner is still WRITING as it executes this command, so it can
     # only ever see the previous run's file. The validator's proper home is
     # the EXTRACTION, where the artifact is finished and static — which is
     # where the sealer runs it, as extraction check 5 of 7. Here the closure
     # is shown by the wiring plus the adversarial cases.
     "grep -q 'evidence_transcript.REL_PATH' specs/seal_package.py && "
     "grep -q 'evidence_transcript.py' specs/seal_package.py && "
     "$PY -m pytest tests/test_spec_gate.py -k counterfeit_or_missing"),
    ("0022", "external", 12, "R12-2",
     "the observed count was self-asserted: `ran` was trusted without "
     "requiring records, so a zero-record transcript claiming 40 satisfied "
     "the sealer and the regression alike",
     "specs/evidence_transcript.py (count derived from len(commands); records "
     "matched to the ledger by (spec, finding, argv)), tests/test_spec_gate.py",
     # Only the ADVERSARIAL half: `transcript_validates` reads the live
     # transcript, which the evidence runner is rewriting as it executes this
     # command — the same self-reference R12-1's evidence had. The adversarial
     # test builds its own fixtures and is independent of the live file.
     "$PY -m pytest tests/test_spec_gate.py -k counterfeit_or_missing"),
    # ---- external round 13 ------------------------------------------------
    ("0022", "external", 13, "R13-1",
     "the transcript validator checked field PRESENCE and length, not values: "
     "`exit: false` passed because a bool is an int and False == 0, a 64-char "
     "non-hex string passed the digest check, and `cwd: null` passed presence "
     "— a fully fabricated transcript of every ledger row was accepted",
     "specs/evidence_transcript.py (typed validation), tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k counterfeit_or_missing"),
    ("0022", "external", 13, "R13-2",
     "COLLECTED listed seven extracted checks and called them 'the SAME six "
     "checks', in the sentence explaining that the list must not be "
     "maintained twice",
     "specs/package/collected_header.txt (the cardinal removed)",
     "! grep -q 'SAME six checks' specs/package/collected_header.txt"),
    ("0022", "external", 13, "R13-3",
     "a closure selector named a test that had been replaced, so the evidence "
     "command exercised half its claim and exited 0 — satisfying the "
     "every-command-runs gate while covering nothing",
     "specs/closure_findings.py (selectors repointed), "
     "tests/test_spec_gate.py (every -k atom must select a test)",
     "$PY -m pytest tests/test_spec_gate.py -k k_atom_in_the_closure"),
    # ---- external round 14 ------------------------------------------------
    ("0022", "external", 14, "R14-1",
     "the transcript schema still coerced untyped values: `ran: 45.0` passed "
     "because 45.0 == 45, a 64-digit JSON integer digest survived str() before "
     "the hex regex, and a duplicated `skipped` entry vanished into a set — "
     "all three applied at once produced an archive the verifier accepted",
     "specs/evidence_transcript.py (a CLOSED schema with exact JSON types), "
     "tests/test_spec_gate.py (six mutations + a clean-transcript control)",
     "$PY -m pytest tests/test_spec_gate.py -k counterfeit_or_missing"),
]
