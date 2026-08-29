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
    # ---- 0001 external round 8 (2026-08-23) — the round-8 fold, v10 -------
    ("0001", "external", 8, "0001-R8-1",
     "the I6 vectors asserted membership, not order — a reversed selection "
     "passed all four",
     "exact ordered-ID equality in every vector, incl. the collapse-derived "
     "dedup survivor",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i6_composition_reserved_day_overlap tests/test_0001_generated_content_trust.py::test_i6_composition_distinct_reserved_days tests/test_0001_generated_content_trust.py::test_i6_composition_dedup_across_reserve_and_coverage tests/test_0001_generated_content_trust.py::test_i6_composition_underfill_backfills_by_rank_deterministically -q -p no:randomly'),
    ("0001", "external", 8, "0001-R8-2",
     "the downgrade test could not detect a version-check-after-parsing "
     "regression (its enum still knew ASSISTANT)",
     "the parse sentinel: Edge/Episode.model_validate trapped; refusal must "
     "precede any record validation",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i13_pre_assistant_reader_refuses_a_v11_store -q -p no:randomly'),
    ("0024", "external", 13, "A1-R13-1",
     "the A1 amendment was not carrier-complete while §11 claimed 'every "
     "carrier' — five passages still described the v7 assertable outcome, "
     "and the co-owned 0025 inventory named one passage of three",
     "the consequence-word sweep ('assertable', 'user's own statement') "
     "executed across BOTH specs; §7b carries THREE verbatim 0025 "
     "replacements; §11 records the lesson in place of the claim",
     "grep -q 'is a re-dispositioned record then able to SUPERSEDE' "
     "specs/0024-authorship-before-structural-quarantine.md && test "
     "\"$(grep -o 'REPLACEMENT [0-9] (' "
     "specs/0024-authorship-before-structural-quarantine.md | wc -l)\" "
     "-ge 3  # R14-1 strengthened: the live §4b-i header uses the "
     "re-dispositioned form AND the three-replacement inventory is "
     "counted per OCCURRENCE (grep -c counts lines; the three markers "
     "share the §7b table row)"),

    ("0024", "external", 13, "A1-R13-2",
     "the candidate patch did not run green (the revoked vector's control "
     "pinned pre-A1 MENTIONABLE) while §11 claimed verified-green — dev "
     "had verified with the pytest wrapper, not the reference's own runner",
     "the control pins USE_ONLY; vector_a1_u2_oracle_exhaustive covers the "
     "complete author×derived product + revoked; 23/23 under "
     "python reference_enforcement.py itself",
     "grep -n 'vector_a1_u2_oracle_exhaustive' "
     "specs/evidence/0025/reference_enforcement.py  # the patch was "
     "FOLDED into the reference at A1's acceptance (round 24); the "
     "oracle lives in the accepted file now"),

    ("0024", "external", 13, "PACKAGE-R13-1",
     "package carriers described both specs as draft candidates while the "
     "canonical statuses are in-review/accepted; the 0025 r13 ledger row "
     "overstated 'no file edit, status untouched'",
     "candidate lines DERIVE the status word from each spec's Spec-Status "
     "line, fail-closed; the ledger row states no-design-change precisely",
     "grep -n '_spec_status' specs/package_identity.py  "
     "# the derived status, refusing an unreadable Spec-Status"),

    ("0001", "external", 18, "EVIDENCE-M18-1",
     "the production/test-double divergence survived R17-1: the "
     "implementation was only ever CALLED with an injected runner, so a "
     "branch keyed on the runner's identity sent every test down the "
     "honest path and production down a read of the shipped record — "
     "and --verify agreed, because agreement is a question a record can "
     "answer about itself",
     "the seal-time enforcement perturbs the record in exactly one field "
     "and REQUIRES the replay to contradict it there and nowhere else, "
     "which no record-reading implementation can do; plus an "
     "injection-free regression running the producer with its external "
     "commands unreachable, which must FAIL rather than report. Both "
     "mutants planted — the reviewer's exact form caught by both gates, "
     "the git-guarded form by the seal-time probe",
     '$PY -m pytest tests/test_collected_header.py::test_the_terminus_note_is_an_archive_member -q -p no:randomly  # the discrimination probe and the injection-free production binding RETIRED with the candidate they guarded when 0001 was implemented; this asserts that retirement actually happened, which is the only claim about them that can still be true'),

    ("0001", "external", 18, "PACKAGE-M18-1",
     "the archive-membership test required git metadata, so it FAILED in "
     "the extracted package — the one environment where membership is a "
     "fact rather than a prediction; and the reason no gate caught it is "
     "0022 R9-1 recurring in the carrier that fix did not reach: the "
     "launcher, the only check running the whole qualified suite, ran at "
     "cwd=ROOT and measured the build tree while the header presented "
     "that number as the package's",
     "the membership test is extraction-aware (tracked-implies-member in "
     "the tree, presence-IS-membership in an extraction) and the "
     "qualified suite is now the last EXTRACTION_CHECKS entry, run "
     "inside the extracted archive, where a red run REFUSES THE SEAL",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_the_terminus_note_is_an_archive_member "
     "tests/test_spec_gate.py::"
     "test_the_extraction_check_list_matches_the_sealer_registry "
     "-q -p no:randomly"),

    ("0024", "external", 24, "EVIDENCE-M24-1",
     "the space-positive control was a tautology ('!= 0 or True') — the "
     "reviewer broke the closer grammar to [\\t]* and the complete "
     "advertised matrix still passed",
     "explicit == 0 assertions for space AND tab positives; the "
     "reviewer's [\\t]* grammar mutant planted as a self-test proving "
     "the control can fail",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_a1_carrier_checker_mutation_matrix -q -p no:randomly"),

    ("0024", "external", 24, "PROCESS-M24-1",
     "P1/P4 claimed 'no unmutated checker ships' while establishing a "
     "pointer convention and an invocation shape — a docstring-only "
     "reference and '$PY script && grep' both passed",
     "the documented claims narrowed to what the gates establish "
     "(convention + shape; the kill evidence is the matrix tests CI "
     "runs) in PROCESS.md and the gate docstrings",
     "$PY -m pytest "
     "tests/test_spec_gate.py::"
     "test_every_evidence_artifact_declares_a_mutation_matrix "
     "-q -p no:randomly"),

    ("0024", "external", 23, "A1-R23-1",
     "the fence closer used Python strip() — U+00A0 and other Unicode "
     "whitespace closed a fence CommonMark keeps open; and the oracle's "
     "vertical-tab cell then exposed str.splitlines() breaking on "
     "\\v/\\f where CommonMark does not",
     "the closer requires spaces/tabs exactly; the parser splits on "
     "true newlines only; the five-suffix whitespace oracle + tab "
     "positive control are matrix cells",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_a1_carrier_checker_mutation_matrix -q -p no:randomly"),

    ("0024", "external", 23, "PROCESS-R23-1",
     "both new gates accepted their prohibited proxies: P1 searched the "
     "whole test file for the artifact name; P4's startswith blessed "
     "$PY -c 'pass'; PROCESS.md was unchanged despite the adoption",
     "P1 binds inside the named test's AST body; P4 requires a real "
     "pytest/named-script invocation; both planted mutants are in-gate "
     "self-tests; PROCESS.md records the rules",
     "$PY -m pytest "
     "tests/test_spec_gate.py::"
     "test_every_evidence_artifact_declares_a_mutation_matrix "
     "tests/test_spec_gate.py::test_new_closure_evidence_is_behavioral "
     "-q -p no:randomly"),

    ("0024", "external", 23, "PACKAGE-R23-1",
     "the terminus proposal was claimed to accompany the package while "
     "it traveled by a side channel that never arrived — a promised "
     "companion absent from the archive and its inventory",
     "the proposal is the archive member "
     "specs/evidence/0024/A1-CHECKER-TERMINUS-PROPOSAL.md; the "
     "v23-era claims corrected in place",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_terminus_proposal_is_an_archive_member -q -p no:randomly"),

    ("0024", "external", 22, "A1-R22-1",
     "two valid Markdown contexts misclassified: a multi-word fence "
     "info string was not an opener, and a four-space-indented table "
     "(rendered as code) was classified as a table",
     "arbitrary fence-info text accepted (backtick-info-no-backticks "
     "per CommonMark); fences AND table rows bounded at three leading "
     "spaces; the reviewer's two mutants plus the self-exhausted "
     "indent-boundary cells (item 9) in the matrix",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_a1_carrier_checker_mutation_matrix -q -p no:randomly"),

    ("0024", "external", 21, "A1-R21-1",
     "the fence strip removed exactly triple-backtick fences — tilde "
     "and four-backtick fences still rendered the table as code while "
     "the checker passed",
     "fence removal is a state parser over the full grammar (backtick "
     "or tilde, length >=3, compatible same-character closer); both "
     "fence-form mutants in the matrix",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_a1_carrier_checker_mutation_matrix -q -p no:randomly"),

    ("0024", "external", 20, "A1-R20-1",
     "the round-19 parser accepted any consecutive pipe lines as a "
     "table — a malformed delimiter row and a fenced code-rendered "
     "table both exited 0",
     "a table requires a valid two-column delimiter row; fenced code "
     "regions are stripped before locating tables; both mutants in the "
     "matrix",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_a1_carrier_checker_mutation_matrix -q -p no:randomly"),

    ("0024", "external", 19, "A1-R19-1",
     "pipe-line anchoring proved neither table membership nor "
     "exclusivity — an isolated pipe-prefixed live line outside the "
     "table, and a contradictory second row, both exited 0",
     "the check PARSES the question table: exactly one table, exactly "
     "one supersession row, re-dispositioned wording, no obsolete row; "
     "both mutants in the matrix; the live row's annotation describes "
     "rather than quotes (the check's first run caught the spec's own "
     "quotation)",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_a1_carrier_checker_mutation_matrix -q -p no:randomly"),

    ("0024", "external", 18, "A1-R18-1",
     "the round-17 fix scoped the search to §4b-i but matched the "
     "fragment ANYWHERE in the section — the obsolete row restored with "
     "the live fragment in an HTML comment passed; and the carriers "
     "typed 'five mutants' while six were invoked",
     "the check anchors to an actual table row with comments STRIPPED "
     "before matching (the line-anchored-in-comment variant pre-empted); "
     "both shadow mutants join the matrix; count carriers enumerate, "
     "never type",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_a1_carrier_checker_mutation_matrix -q -p no:randomly"),

    ("0024", "external", 17, "A1-R17-1",
     "the carrier checker searched the whole file for the §4b-i header "
     "phrase, which the generated ledger quotes — the ledger-shadow "
     "mutant (obsolete header restored, ledger untouched) exited 0",
     "the check isolates §4b-i and asserts the exact table row at the "
     "site; the requested adversarial mutation matrix ships in the "
     "suite, pristine + the enumerated mutants each biting (counts "
     "never typed - round-18 editorial)",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_a1_carrier_checker_mutation_matrix -q -p no:randomly"),

    ("0024", "external", 17, "EVIDENCE-R17-1",
     "the EVIDENCE-R16-1 closure row cited the diagnostic string's "
     "lexical presence — a no-op validator containing it would satisfy "
     "the command",
     "the row runs the WORKING deleted/None regression the reviewer "
     "verified sound",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_baseline_validator_bites_on_a_planted_mutation "
     "-q -p no:randomly"),

    ("0024", "external", 16, "A1-R16-1",
     "the A1-R15-1 ledger row's own closure command was underpowered — "
     "its grep printed 1 and exited 0, establishing none of the three "
     "properties the row claimed",
     "both consequence-carrier rows run the ONE named checker; per-row "
     "inline evidence retired as a second copy of the check",
     "$PY specs/check_a1_carriers.py"),

    ("0024", "external", 16, "EVIDENCE-R16-1",
     "e.get('subject','') coerced an ABSENT canary subject into passing "
     "the no-user-subject check — the deleted-subject mutant exited zero",
     "the subject must be present, string-typed and nonempty after "
     "canonicalization before the 'user' test; deletion and None mutants "
     "are planted regressions",
     "$PY -m pytest "
     "tests/test_collected_header.py::"
     "test_baseline_validator_bites_on_a_planted_mutation "
     "-q -p no:randomly  # EVIDENCE-R17-1: the WORKING regression (the "
     "deleted/None mutants must fail the validator), not the lexical "
     "presence of its diagnostic — a no-op validator containing the "
     "string satisfied the old grep"),

    ("0024", "external", 15, "A1-R15-1",
     "the R14-1 closure evidence proved only half the finding — no "
     "command examined §9; restoring its obsolete singular summary alone "
     "passed both commands",
     "the evidence section-scopes §9 itself: three replacement targets "
     "present, the singular form rejected, the §4b-i header live",
     "$PY specs/check_a1_carriers.py  # A1-R16-1: the row's first "
     "inline grep printed 1 and exited 0, proving none of its three "
     "claims — both rows now share the one named checker"),

    ("0024", "external", 15, "PACKAGE-R15-1",
     "verify_a1_patch accepted a skipped vector — only the reference was "
     "copied, and dev's installed veracium masked the empty src/ path "
     "locally (env-leak)",
     "a complete tree is constructed, the exact zero-skip tail required, "
     "and import provenance witnessed (veracium must resolve from inside "
     "the constructed tree); the incomplete-tree refusal is a tested cell",
     "grep -n 'copy_src=False' tests/test_collected_header.py  "
     "# the refusal regression"),

    ("0024", "external", 15, "EVIDENCE-R15-1",
     "the 'whole evidentiary chain' claim was too broad — the canary "
     "subject re-run behind 'artifact-verified' was never persisted, so "
     "nothing shipped supported it",
     "fresh persisted canary_subject_records.jsonl + CANARY_SUBJECTS.md "
     "ship digest-bound; §11/PROVENANCE state shipped-records-verify vs "
     "stdout-run-is-history exactly",
     "(cd specs/evidence/0024/baseline && sha256sum --quiet -c "
     "DIGESTS.sha256 && grep -q canary_subject_records "
     "DIGESTS.sha256)  # digests verify FROM the bundle dir and the "
     "canary records are bound"),

    ("0024", "external", 14, "A1-R14-1",
     "two consequence carriers survived the round-13 sweep — §4b-i's "
     "question header still said 'corrected user statement' and §9's "
     "brief still said 'one-sentence step-2 replacement' after the "
     "inventory grew to three; the closure evidence could detect neither",
     "the §4b-i header asks about a re-dispositioned record; §9 "
     "enumerates all three 0025 replacements with the R14-1 note; the "
     "A1-R13-1 evidence strengthened to assert both",
     "$PY specs/check_a1_carriers.py  # A1-R16-1: ONE shared named "
     "checker for both consequence-carrier rows — three §9 targets, the "
     "singular form rejected, the §4b-i header live"),

    ("0001", "external", 17, "0001-R17-1",
     "the injected path was bound and the PRODUCTION path was not — an "
     "optional runner made them two paths, so a no-runner branch "
     "returning the shipped record passed every test while production "
     "--verify compared the record with itself",
     "the runner is REQUIRED on the implementation and measure() is a "
     "delegation and nothing else; a sentinel regression proves the "
     "wrapper reaches the implementation with the requested base and "
     "subprocess.run; three production-path mutants planted and failing",
     "$PY -m pytest tests/test_collected_header.py::test_the_terminus_note_is_an_archive_member -q -p no:randomly  # this finding was closed against the candidate-measurement machinery, which RETIRED when 0001 was implemented and the candidate folded into the product; the surviving checkable claim is that the retirement happened, which is what this asserts. The fix itself is recorded above and in the spec's review history."),

    ("0001", "external", 16, "0001-R16-1",
     "the PRODUCER was unbound — every consumer was tested while "
     "measure() was only ever monkeypatched, so a body of "
     "`return json.loads(RECORD.read_text())` made the verifier compare "
     "the record with itself and pass in a non-git extraction",
     "measure() takes an injectable subprocess seam; a behavioural "
     "regression proves the record is DERIVED from canned command "
     "output unlike the shipped figures, the declared base materialised "
     "and the patch applied; three collapse mutants planted and failing",
     "$PY -m pytest tests/test_collected_header.py::test_the_terminus_note_is_an_archive_member -q -p no:randomly  # this finding was closed against the candidate-measurement machinery, which RETIRED when 0001 was implemented and the candidate folded into the product; the surviving checkable claim is that the retirement happened, which is what this asserts. The fix itself is recorded above and in the spec's review history."),

    ("0001", "external", 15, "0001-R15-1",
     "the chain was tested link by link but never at the join — dropping "
     "--verify from the argv ran the helper's default measure-and-print "
     "mode, which exits 0 without comparing, with the whole gate green",
     "the exact invocation and cwd are asserted; the --verify branch is "
     "proven to discriminate on a planted difference with an identical "
     "control; the default mode's exit-0 is documented by assertion; "
     "three connection-breaking mutants planted and each failing",
     "$PY -m pytest tests/test_collected_header.py::test_the_terminus_note_is_an_archive_member -q -p no:randomly  # this finding was closed against the candidate-measurement machinery, which RETIRED when 0001 was implemented and the candidate folded into the product; the surviving checkable claim is that the retirement happened, which is what this asserts. The fix itself is recorded above and in the spec's review history."),

    ("0001", "external", 14, "0001-R14-1",
     "reachability was proved syntactically — an AST search rejecting "
     "only a literal constant-false guard, so `if a.version == 'v0'` "
     "disabled replay for every real package with the whole gate green",
     "the test EXECUTES main() and requires a sentinel to be reached, "
     "with a second sentinel naming the bypass; the call is an "
     "unconditional fail-fast precondition; three bypass shapes planted "
     "and each verified failing",
     "$PY -m pytest tests/test_collected_header.py::test_the_terminus_note_is_an_archive_member -q -p no:randomly  # this finding was closed against the candidate-measurement machinery, which RETIRED when 0001 was implemented and the candidate folded into the product; the surviving checkable claim is that the retirement happened, which is what this asserts. The fix itself is recorded above and in the spec's review history."),

    ("0001", "external", 13, "0001-R13-1",
     "the seal-time replay was sound but UNPROTECTED — a planted "
     "`if False` on its call left the named matrix and the whole spec "
     "gate green, so the only guard that catches type-valid "
     "fabrications could be removed silently",
     "the enforcement is a named injectable seam and the comparison a "
     "pure function; a sealer-boundary regression binds reachability "
     "(if-False and deletion both planted and both failing), refusal on "
     "a failing replay with a pristine control, and discrimination "
     "including failure-identity replacement",
     "$PY -m pytest tests/test_collected_header.py::test_the_terminus_note_is_an_archive_member -q -p no:randomly  # this finding was closed against the candidate-measurement machinery, which RETIRED when 0001 was implemented and the candidate folded into the product; the surviving checkable claim is that the retirement happened, which is what this asserts. The fix itself is recorded above and in the spec's review history."),

    ("0001", "external", 12, "0001-R12-1",
     "the checker bound a PROJECTION — patch hash, README count, README "
     "triple, failure LENGTH — while the record claims base commit, "
     "environment, commands, focused outcome and a sorted failure set; "
     "a forty-zero base with python 0.0.0, and a duplicated failure "
     "entry, both exited 0",
     "a closed exactly-typed schema validating every claimed field; "
     "failure_set sorted/unique/node-id/cardinality-equal; commands "
     "imported not retyped; the matrix across every field; and the base "
     "independently reproducible by a sealer-run complete-record replay",
     "$PY -m pytest tests/test_collected_header.py::test_the_terminus_note_is_an_archive_member -q -p no:randomly  # this finding was closed against the candidate-measurement machinery, which RETIRED when 0001 was implemented and the candidate folded into the product; the surviving checkable claim is that the retirement happened, which is what this asserts. The fix itself is recorded above and in the spec's review history."),

    ("0001", "external", 11, "0001-R11-1",
     "the candidate README stated a focused count of 20 while the branch "
     "ran 21 — carried from v10 and incremented by inference, inside a "
     "paragraph claiming the measurement was re-run",
     "both figures are GENERATED into candidate_results.json by running "
     "the shipped patch, and bound to the patch's bytes and the README's "
     "text by a checker in the sealer's extraction checks",
     "$PY -m pytest tests/test_spec_gate.py::test_the_extraction_check_list_matches_the_sealer_registry -q -p no:randomly  # the candidate README, its generator and its results record RETIRED when the candidate folded into the product at acceptance; the property they enforced — a package's figures are MEASURED from the artifact, never typed — is carried now by the extracted-suite gate in the sealer registry, which this binds. (P4 governs this row, so it names one test and runs under the reviewer's bare offline interpreter.)"),

    ("0001", "external", 10, "0001-R10-1",
     "the I6 reserve protected ELIGIBILITY, not relevance — every "
     "assertable in the scored set was reservable, and user-subject edges "
     "sit there at baseline score with zero query overlap; the reviewer's "
     "executed counterexample reserved an unrelated 'bananas' fact first "
     "and dropped a relevant one",
     "the relevance bit is carried FROM scoring (relevant_ids) and the "
     "reserve takes query-relevant assertables only; the exact bananas "
     "vector added and proven to fail pre-fix; the I6 cell says "
     "query-RELEVANT explicitly",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i6_no_relevant_assertable_reserves_nothing -q -p no:randomly'),

    ("0001", "external", 10, "0001-R10-2",
     "the opening block still read 'draft (v10)' with a §20 pointer "
     "beside the v11 Version row — the third version-carrier strike",
     "the opening block carries NO revision; the Version row is "
     "structurally the one carrier; the sweep greps '(v' forms",
     "! sed -n '1,20p' specs/0001-generated-content-trust-class.md "
     "| grep 'draft (v'  # the opening block carries no revision "
     "(the §22 changelog QUOTES the old defect, so the sweep is scoped "
     "to the block)"),

    ("0001", "external", 9, "0001-R9-1",
     "subgraph_for_query FILTERED the globally scored list instead of "
     "constructing reserved + remainder — a low-ranked reserved assertable "
     "record under a non-functional relation surfaced last, and every order "
     "vector used functional works_as (top-ranked reserves), masking it",
     "the output is CONSTRUCTED as reserved + remainder (both segments in "
     "scored order); the reviewer's has_pet vector asserts the complete "
     "ordered output and fails on the pre-fix filter; the dedup vector "
     "asserts full order, closing the §20 claim",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i6_reserved_low_rank_is_placed_first_nonfunctional tests/test_0001_generated_content_trust.py::test_i6_composition_dedup_across_reserve_and_coverage -q -p no:randomly'),

    ("0001", "external", 9, "0001-R9-2",
     "the candidate test module docstring still said candidate/0001-v8 — "
     "one version carrier survived the R8-3 sweep",
     "the module docstring is version-neutral; the sweep now greps the "
     "whole patch",
     "! grep -nE 'candidate/0001-v[0-9]+' tests/test_0001_generated_content_trust.py"),

    ("0001", "external", 9, "0001-R9-3",
     "the README's full-suite measurement was stale (16 failed/1797 vs the "
     "extracted branch's 16 failed/1787/21 skipped) and carried no "
     "environment",
     "the measurement is re-run at packaging time and recorded with its "
     "exact environment (python, platform, command)",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py -q -p no:randomly'),

    ("0001", "external", 8, "0001-R8-3",
     "the modified patch still identified as candidate/0001-v8 while the "
     "draft moved to v9",
     "version-neutral artifact (candidate.patch); the Version row is the "
     "one carrier",
     "! grep -nE 'candidate/0001-v[0-9]+' tests/test_0001_generated_content_trust.py"),

    # ---- 0001 external round 7 (2026-08-23) — the round-7 fold, v9 --------
    ("0001", "external", 7, "0001-R7-1",
     "the candidate patch implemented and tested the WRONG I12 label; "
     "USER/SYSTEM inherited a label",
     "the §4b decision order verbatim; the complete matrix tested",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i12_the_complete_label_matrix tests/test_render_origin.py -q -p no:randomly'),
    ("0001", "external", 7, "0001-R7-2",
     "the five-manifestation tests were proxies: routes not shapes, "
     "v11-vs-v11, count-only inheritance, a hardcoded 5, a fabricated "
     "reader",
     "shapes from the authority's own object records; digest-level "
     "inheritance; the qualified head-10 reader",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i13b_stamp_only_across_every_accepted_v10_shape tests/test_0001_generated_content_trust.py::test_i13c_v11_inherits_by_digest_not_count -q -p no:randomly'),
    ("0001", "external", 7, "0001-R7-3",
     "I7's test was a constant assertion; the spec-named downgrade test "
     "was absent",
     "test_downgrade_export_fails_cleanly, real, both import modes",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_downgrade_export_fails_cleanly -q -p no:randomly'),
    ("0001", "external", 7, "0001-R7-4",
     "the four I6 composition branches were never executed",
     "four vectors with exact-ID/order assertions, all green against the "
     "unchanged reserve implementation",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i6_composition_reserved_day_overlap tests/test_0001_generated_content_trust.py::test_i6_composition_distinct_reserved_days tests/test_0001_generated_content_trust.py::test_i6_composition_dedup_across_reserve_and_coverage tests/test_0001_generated_content_trust.py::test_i6_composition_underfill_backfills_by_rank_deterministically -q -p no:randomly'),

    # ---- 0001 external round 6 (2026-08-23) — the round-6 fold, v8 --------
    ("0001", "external", 6, "0001-R6-1",
     "I13b/c undercounted the v10 domain: five accepted manifestations, "
     "'both routes' lost three",
     "I13b/c parameterized over every accepted shape; the count derived, "
     "not typed",
     "grep -n 'EVERY accepted v10 manifestation\\|inherits_every_v10_shape' "
     "specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 6, "0001-R6-2",
     "the 0018 attestation internals were undispositioned: migration_digest "
     "from ALTERS_V7_TO_V8, ladder diagnostics hard-coding v5/v6-era bases",
     "I13d: edge-indexed step registry, empty-step-set digest, generated "
     "diagnostics, bases 1-10",
     "grep -n 'edge-indexed migration-step registry' "
     "specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 6, "0001-R6-3",
     "I5 named collapse_for_render while the design said it neither "
     "partitions nor renders",
     "I5 names gate.partition_parts + rendering; collapse retained only "
     "as the no-collapse assertion",
     "grep -n 'asserted at .gate.partition_parts' "
     "specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 6, "0001-R6-4",
     "the reserve/coverage composition was untested beyond share=0.0",
     "the composition defined; the harness measures the positive-coverage "
     "path",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i6_composition_reserved_day_overlap tests/test_0001_generated_content_trust.py::test_i6_composition_distinct_reserved_days -q -p no:randomly'),
    ("0001", "external", 6, "0001-R6-5",
     "a live cross-ref said 'the confirm() row' — the sweep grepped rule "
     "phrases, not row names",
     "fixed; cross-references join the sweep list",
     "! sed '/GENERATED:review-closure/,$d' specs/0001-generated-content-trust-class.md | grep -n 'see the .confirm(). row'"),

    # ---- 0001 external round 5 (2026-08-23) — the round-5 fold, v7 --------
    ("0001", "external", 5, "0001-R5-1",
     "three confirm() carriers survived two claimed-complete sweeps — the "
     "scripted replacements silently no-opped on wrapped text",
     "all three replaced; folds refuse needle misses; zero survivors "
     "grep-verified",
     "! sed '/GENERATED:review-closure/,$d' specs/0001-generated-content-trust-class.md | grep -n 'Only through .confirm()' && ! sed '/GENERATED:review-closure/,$d' specs/0001-generated-content-trust-class.md | grep -n 'confirm()..-class'"),
    ("0001", "external", 5, "0001-R5-2",
     "I6's post-_cover reserve was impossible — truncation precedes it; "
     "assertable_selected 0 measured at the shipped coverage_share=0.0",
     "the reserve applies to the full scored set BEFORE truncation; the "
     "fixture pins coverage_share=0.0",
     "grep -n 'BEFORE final truncation' specs/0001-generated-content-trust-class.md && PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i6_reserve_guarantees_the_user_edge -q -p no:randomly"),
    ("0001", "external", 5, "0001-R5-3",
     "I5 tested collapse_for_render, which neither partitions nor renders",
     "the harness drives gate.partition_parts and asserts grounded-only / "
     "unverified-only / origin marker / no leakage",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i5_affirmation_grounds_and_partitions_and_confirm_refuses -q -p no:randomly'),
    ("0001", "external", 5, "0001-R5-4",
     "the v10->v11 contract was prose-only in the new-reader direction",
     "I13a-d name the executable checks",
     "grep -c 'I13[abcd]' specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 5, "0001-R5-5",
     "current-version carriers disagreed: Status row, the §9 label, the "
     "harness self-id",
     "swept; version carriers join the pre-send sweep",
     '$PY -c "import re, pathlib; s = pathlib.Path(\'specs/0001-generated-content-trust-class.md\').read_text(); ver = re.search(r\'[*][*]Version[*][*] . [*][*](v\\\\d+)[*][*]\', s).group(1); assert f\'{ver} is the round-\' in s, \'Status row disagrees with Version\'; h = pathlib.Path(\'tests/test_0001_generated_content_trust.py\').read_text(); assert not re.search(r\'v\\\\d+ candidate harness\', h), \'the shipped suite carries a version literal\'; print(\'version carriers consistent, no hand-bumped literals\')"'),

    # ---- 0001 external round 4 (2026-08-23) — the round-4 fold, v6 --------
    ("0001", "external", 4, "0001-R4-1",
     "the confirm() correction was unswept across five more normative "
     "carriers — the third partial sweep this spec has recorded",
     "§3.1/§3.2/§4/§7/§9 swept with the three-way terminology",
     "! sed '/GENERATED:review-closure/,$d' specs/0001-generated-content-trust-class.md | grep -n 'Promotion remains' && sed '/GENERATED:review-closure/,$d' specs/0001-generated-content-trust-class.md | grep -c 'AFFIRMATION\\|affirmation'"),
    ("0001", "external", 4, "0001-R4-2",
     "same-value affirmation does not render-collapse: collapse groups per "
     "trust envelope, so the spec claimed a collapse 0012 forbids",
     "the separate-partitions truth stated; the harness measures the "
     "RENDERED result",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i5_affirmation_grounds_and_partitions_and_confirm_refuses -q -p no:randomly'),
    ("0001", "external", 4, "0001-R4-3",
     "I6 claimed scope runs upstream — false against shipped 0020: scope "
     "filters AFTER selection, and a principal's edge was starved at cap 1",
     "I6 scoped to unscoped recall; the scoped limitation in §8; the 0020 "
     "amendment at Q6",
     "grep -n 'scoped to UNSCOPED recall' "
     "specs/0001-generated-content-trust-class.md && "
     "grep -n 'Q6' specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 4, "0001-R4-4",
     "the v10->v11 contract was incomplete: wrong precedent, missing "
     "0013/0018 dependencies, the release orchestrator undispositioned, "
     "the refusal untyped, the Q3 carrier contradicting I13",
     "§7 completed; I13 exact; the harness asserts "
     "StoreVersionError(reason=newer)",
     "grep -n 'StoreVersionError' specs/0001-generated-content-trust-class.md && PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i13_pre_assistant_reader_refuses_a_v11_store -q -p no:randomly"),

    # ---- 0001 historical rounds (retrofitted at TRACKED-entry, 2026-08-23:
    # per-finding texts live in the spec's own §11/§12/§13 narrative) -------
    ("0001", "internal", 1, "0001-INT1",
     "research's v1->v2 amendment set, folded directly into the spec before "
     "the per-finding discipline existed",
     "§11 (changes in v2), the collective record",
     "grep -n '## 11. Review history — changes in v2' specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 1, "0001-R1-SUBJECT",
     "the subject rule cannot work: no entity resolution, no display name; "
     "19,096 distinct subjects, 39.4% the literal 'user'",
     "withdrawn in v3 — use_only for EVERY subject, no subject inspection",
     "grep -n 'One rule, no subject inspection' "
     "specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 1, "0001-R1-WITNESS",
     "subject identity does not establish evidence authority — speaker is "
     "not witness; 'the deploy failed' proves nothing about who deployed",
     "conceded in v3; groundability routed to the evidence-basis axis",
     "grep -n 'Speaker . witness, conceded' "
     "specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 2, "0001-R2-MARKER",
     "the render marker keyed on use_only with hardcoded third-party text — "
     "every assistant edge would carry an affirmatively false origin",
     "closed in shipped code 2026-08-15: author-keyed _ORIGIN_LABELS, "
     "fail-safe unverified-origin, the tripwire test",
     "PYTHONPATH=src $PY -m pytest tests/test_render_origin.py::test_every_author_reaching_use_only_has_a_deliberate_label -q -p no:randomly  # the original check asserted that USER, SYSTEM and THIRD_PARTY each had an entry in the author-keyed label map. 0001 I12 made the label PAIR-keyed and deliberately REMOVED the USER and SYSTEM entries, because inheriting another class's origin string is the very failure this finding was about — so the old assertion now demands the defect. The property it protected is unchanged and is checked over the whole author x derivation matrix against an independent oracle, including that no unlabelled class is described as a third party's or the assistant's."),

    # ---- 0001 external round 3 (2026-08-23) — the round-3 fold, v5 --------
    ("0001", "external", 3, "0001-R3-1",
     "confirm_edge (0008) refuses every non-assertable edge by contract, so "
     "the promotion v4 promised cannot exist; affirmation is NEW USER "
     "evidence — same value grounds via the user edge, differing value "
     "retires via the ladder",
     "§3.2 affirmation row, I5, §7, §8; both shapes measured",
     'PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i5_affirmation_grounds_and_partitions_and_confirm_refuses -q -p no:randomly'),
    ("0001", "external", 3, "0001-R3-2",
     "the on-disk guard was never activated: disk=10 reader=10 gives "
     "ValidationError mid-read, not a refusal — 0007 only refuses what a "
     "version bump tells it to",
     "§7 (SCHEMA 10->11 semantic bump), I13 refusal-at-open",
     "grep -n 'I13' specs/0001-generated-content-trust-class.md && PYTHONPATH=src $PY -m pytest tests/test_0001_generated_content_trust.py::test_i13a_schema_v11_is_byte_identical_to_v10 tests/test_0001_generated_content_trust.py::test_i13_pre_assistant_reader_refuses_a_v11_store -q -p no:randomly"),
    ("0001", "external", 3, "0001-R3-3",
     "two matrix cells measured false (cross-class absorption stays "
     "blocked; 0012 persists restatements untouched) and the supersession "
     "rationale named the wrong mechanism",
     "§3.2 rewritten against the ladder/0012/0.4.1 as shipped; I3b, I10a",
     'PYTHONPATH=src $PY -m pytest tests/test_absorption.py::test_third_party_restatement_never_absorbs_user_fact tests/test_0001_generated_content_trust.py::test_i1_assistant_is_use_only_for_every_subject -q -p no:randomly'),
    ("0001", "external", 3, "0001-R3-4",
     "I6 named a test with no selection rule — selected=40 user_selected=[] "
     "under the natural fixture",
     "I6: the reserve rule (min(count_relevant_assertable, ceil(budget/4))) "
     "with the exact 1,000+1 fixture",
     "grep -n 'THE SELECTION RULE' "
     "specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 3, "0001-R3-5",
     "Q4 rode ingest._source_type, deleted by 0016 — the currency pass "
     "re-ran commands but never verified cited names resolve",
     "Q4 struck as moot; the consumer row corrected",
     "! grep -rn '_source_type' src/veracium/ingest.py && "
     "grep -n 'MOOT (v5, R3-5)' specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 3, "0001-R3-6",
     "three more v2-form carriers survived the v4 sweep: the Edge.subject "
     "blast-radius cell, §3b bullet 4, §8's public claim",
     "§2/§3b/§8 rewritten; §14's completed-sweep claim corrected by §15",
     "grep -c 'v5, R3-6' specs/0001-generated-content-trust-class.md  "
     "# all three carriers annotated at the fix site"),
    ("0001", "external", 3, "0001-R3-7",
     "Spec-Requires named 0003/0005 while the design depends on "
     "0007/0008/0012/0016 and explicitly sequences after 0024",
     "the header line, complete",
     "grep -n 'Spec-Requires: 0003, 0005, 0007, 0008, 0012, 0013, 0016, 0018, 0024' "
     "specs/0001-generated-content-trust-class.md  "
     "# grown again by R4-4 (+0013 +0018); the closure tracks the CURRENT list"),

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
     # NOT `closure_evidence_command`: that is the runner, and the runner
     # executing this command spawns a child that SKIPS on the recursion
     # marker — so that half exercised nothing while exiting 0. R13-3's defect
     # wearing the marker instead of a rename, caught by the class-5 gate.
     "$PY specs/render_closure.py --check && "
     "$PY -m pytest tests/test_spec_gate.py -k closure_ledger_is_complete"),
    ("0022", "external", 7, "R7-2",
     "the reproduction carrier described the SQLite-floor launcher a round "
     "after the code changed, and repeated the previous round's launcher "
     "result against a different test set",
     "specs/package/collected_header.txt, specs/seal_package.py (the sealer "
     "runs the launcher on the final tree; since C-plus the complete "
     "stdout/stderr + exit status ship as a digested capture and the header "
     "line DERIVES from that file)",
     "grep -q '__LAUNCHER__' specs/package/collected_header.txt && "
     "grep -q 'launcher runs on the FINAL tree' specs/seal_package.py && "
     "grep -q 'derive_launcher' specs/collected_record.py"),
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
     # NOT a selector that reads the LIVE transcript, which the evidence
     # runner is rewriting as it executes this command — the self-reference
     # R12-1/R12-2 already hit, walked back into while repointing a stale
     # selector. (The test that read it, `transcript_validates`, was REMOVED at
     # round 15: pytest-randomly shuffles order, so it failed whenever the
     # shuffle put it before the runner. Its validation now happens inside the
     # runner.) THE RULE: ledger evidence must never
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
     # Only the ADVERSARIAL half. The live transcript is rewritten by the
     # evidence runner as it executes this command — the same self-reference
     # R12-1's evidence had — so nothing that reads it may be selected here.
     # The adversarial test builds its own fixtures in a temp dir and is
     # independent of the live file.
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
    # ---- self-found while writing specs/REVIEW_LESSONS.md (round 15) --------
    ("0022", "internal", 14, "R14-2",
     "SELF-FOUND, not raised: classifying fifteen rounds of findings by "
     "failure MECHANISM showed class 5 (self-reference) had no mechanical "
     "gate — the only class re-found after its first fix — and building that "
     "gate immediately caught R7-1's evidence selecting the evidence RUNNER, "
     "whose nested child skips on the recursion marker, so that half of the "
     "command exercised nothing while exiting 0",
     "specs/REVIEW_LESSONS.md (the taxonomy), tests/test_spec_gate.py (the "
     "class-5 gate), specs/closure_findings.py (R7-1's selector)",
     "$PY -m pytest tests/test_spec_gate.py -k reads_an_artifact"),
    # ---- external round 16 ------------------------------------------------
    ("0022", "external", 16, "R16-1",
     "package identity was HAND-MAINTAINED and stale: the archive was named "
     "v16 while both shipped carriers said v15 / external ROUND 15, because "
     "build_collected() received the requested version and never used it — "
     "`--version` controlled the FILENAME alone",
     "specs/package/collected_header.txt + manifest.txt (identity tokenized as "
     "__VERSION__/__ROUND__/__PACKAGE__), specs/seal_package.py (substituted, "
     "round derived from the version and CROSS-CHECKED against the SENT row in "
     "reviews.py, plus identity_problems() refusing any disagreement among the "
     "three carriers), tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k identity_carriers"),
    ("0022", "external", 16, "R16-2",
     "the lessons carrier was located with split(BEGIN, 1) and never required "
     "exactly one marker pair, so an appended second block claiming 999 "
     "findings passed --check, the gate and full archive verification — a "
     "SECOND, WEAKER COPY of the strict rule already in skip_inventory, "
     "written for 0014's identical finding",
     "specs/generated_block.py (ONE implementation: standalone-line markers, "
     "exactly one pair, no normalization, strict on the WRITE path too), "
     "specs/skip_inventory.py + specs/review_lessons.py (both delegate), "
     "specs/seal_package.py (the lessons check added to EXTRACTION_CHECKS)",
     "$PY -m pytest tests/test_spec_gate.py -k marker_mutation"),
    # ---- external round 17 ------------------------------------------------
    ("0022", "external", 17, "R17-1",
     "R16-1's fix enumerated the three identity carriers the reviewer named "
     "and there were FIVE: COLLECTED lines 6-7 state each spec's own candidate "
     "revision and were still template literals, so the v17 package shipped "
     "saying `draft v16` while its SENT rows said v18, and identity "
     "verification found nothing wrong",
     "specs/package_identity.py (the structured record: version, round, "
     "per-spec candidate revision, with exactly one SENT row required per "
     "packaged spec), specs/package/collected_header.txt (__CANDIDATES__), "
     "specs/seal_package.py (filled from the record; identity_problems() now "
     "covers the candidate carriers), tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k identity_record_governs"),
    ("0022", "external", 17, "R17-2",
     "the lessons document stated `has not moved in eight rounds` in free text "
     "OUTSIDE the generated block — wrong (nine) and ungated, since --check "
     "compares only what is between the markers; the reviewer changed it to "
     "999 rounds and every check still returned 0",
     "specs/review_lessons.py (a per-finding `scope` field, checked total, "
     "with the claim DERIVED into the block), specs/REVIEW_LESSONS.md (no "
     "quantity above the table), tests/test_spec_gate.py (the prologue gate "
     "with the reviewer's mutation, the original defect, and both controls)",
     # R18-2 replaced the natural-language prologue heuristic with byte
     # verification of the whole summary, so the test this row selected no
     # longer exists. Repointed — and the every-atom-selects-a-test gate is
     # what caught it, which is R13-3's defect refused before it shipped.
     "$PY -m pytest tests/test_spec_gate.py -k byte_verified"),
    # ---- external round 18 ------------------------------------------------
    ("0022", "external", 18, "R18-1",
     "the structured identity record was not total over its claimed domain in "
     "THREE ways: the candidate revisions restated in SENT prose were never "
     "cross-checked (a row could say `0022 at v999`), duplicate candidate lines "
     "collapsed through dict(re.findall(...)) so a carrier could disagree with "
     "itself, and FIRST_GOVERNED bounded the run without requiring continuity "
     "from it, so deleting the oldest governed row left the record valid",
     "specs/package_identity.py (contiguity of the governed run; every "
     "`NNNN at vN` claim in a matching SENT row must equal the record), "
     "specs/seal_package.py (candidate lines counted before compared), "
     "tests/test_spec_gate.py (all three mutations retained)",
     "$PY -m pytest tests/test_spec_gate.py -k identity_record_governs"),
    ("0022", "external", 18, "R18-2",
     "the prologue control lived only in the pytest file and not in "
     "review_lessons.py --check, which is what the archive verifier runs; its "
     "scrubber also dropped every four-digit number as a spec id, so `has not "
     "moved in 9999 rounds` passed both the gate and --check",
     "specs/review_lessons.py (the WHOLE summary — title, prologue, table, "
     "derived paragraphs — is generated and byte-verified by --check), "
     "specs/REVIEW_LESSONS.md, tests/test_spec_gate.py (the natural-language "
     "heuristic deleted; mutations now assert --check itself refuses)",
     "$PY -m pytest tests/test_spec_gate.py -k byte_verified"),
    # ---- self-found while making the evidence runner concurrent -----------
    ("0022", "internal", 21, "R21-1",
     "SELF-FOUND (by CI, on the first push): the byte-verification test MUTATED "
     "the shipped specs/REVIEW_LESSONS.md and restored it, which was safe only "
     "while nothing else ran at the same time — the moment the evidence runner "
     "became concurrent it raced the evidence command that reads that file, and "
     "the two commands whose evidence touches it (R15-2 and R19-2) failed in "
     "two of five CI jobs while five local runs passed",
     "tests/test_spec_gate.py (every mutation runs on a COPY in a temp dir, "
     "with rl.DOC repointed; the shipped document is asserted unmodified at the "
     "end)",
     "$PY -m pytest tests/test_spec_gate.py -k byte_verified"),
    # ---- external round 19 ------------------------------------------------
    ("0022", "external", 19, "R19-1",
     "identity_problems() extracted the four-digit spec id and the revision "
     "from each candidate line and compared only those, so renaming the PATH "
     "to specs/0022-not-the-shipped-spec.md kept both fields correct, every "
     "identity check passed, and COLLECTED could direct the reviewer at a file "
     "that does not exist",
     "specs/seal_package.py (the candidate block compared BYTE FOR BYTE against "
     "package_identity.render_candidate_lines(); nothing of that shape allowed "
     "outside it; every declared path required to be an archive MEMBER, with "
     "the member set a required argument rather than an optional one), "
     "tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k identity_record_governs"),
    ("0022", "external", 19, "R19-2",
     "the generated summary was verified BETWEEN its markers and the text "
     "before the opening marker was unconstrained, so a prepended "
     "`# What 9999 rounds actually found` became the document's title while "
     "--check, the pytest gate and full archive verification all passed",
     "specs/generated_block.py (a REQUIRED keyword-only at_start policy; the "
     "opening marker must be the first line when it is set), "
     "specs/review_lessons.py (at_start=True) and specs/skip_inventory.py "
     "(at_start=False, stated rather than defaulted), tests/test_spec_gate.py",
     "$PY -m pytest tests/test_spec_gate.py -k byte_verified"),
    # ---- external round 20 ------------------------------------------------
    ("0022", "external", 20, "R20-1",
     "the candidate block was checked for occurrence ANYWHERE in COLLECTED "
     "rather than as the reviewer-facing `specs:` field, so a package could "
     "answer `specs: none — this package has no external candidates` on the "
     "line a reviewer reads and carry the correct block lower down; the "
     "contradiction passed identity_problems() and the complete extracted "
     "verifier",
     "specs/package_identity.py (LABEL/INDENT own the field; "
     "render_candidate_field() renders it whole), "
     "specs/package/collected_header.txt (the label removed from the "
     "template), specs/seal_package.py (exactly one `specs:` field, in the "
     "header above the inventory block, byte-identical to the rendered "
     "field), tests/test_spec_gate.py (pure-function matrix AND a full-repack "
     "regression that asserts the REASON for refusal)",
     "$PY -m pytest tests/test_spec_gate.py -k relocated_candidate"),
    # ---- self-found by CI, round 15 ---------------------------------------
    ("0022", "internal", 15, "R15-3",
     "SELF-FOUND (by CI, five red runs before I looked): the transcript "
     "validator was a SEPARATE test reading the live file that the evidence "
     "runner writes, and `pytest-randomly` — a dev dependency that shuffles "
     "order every run — put the reader before the writer on some seeds, so the "
     "suite failed intermittently from the round-12 seal onward while every "
     "local run happened to shuffle the other way. Class 5 exactly: a check "
     "that reads what the run produces. The ledger already forbade EVIDENCE "
     "COMMANDS from reading that artifact and the rule was never carried across "
     "to test-to-test dependencies",
     "tests/test_spec_gate.py (the separate test REMOVED; its validation now "
     "runs inside the producer, so there is no order to get wrong), "
     "specs/closure_findings.py (both selector notes)",
     "$PY -m pytest tests/test_spec_gate.py -k reads_an_artifact"),
    # ---- external round 15 ------------------------------------------------
    ("0022", "external", 15, "R15-1",
     "the CLOSED transcript schema was closed one level down only: commands "
     "rejected undeclared fields while the object holding them did not, so "
     "`{\"undeclared_top_level\": \"accepted\"}` passed validate(), the whole "
     "archive verifier, and a repacked archive",
     "specs/evidence_transcript.py (undeclared keys refused at EVERY level "
     "with keys), tests/test_spec_gate.py (the mutation matrix is now DERIVED "
     "from the schema — every declared field of every level, plus an "
     "undeclared-key mutation per level, plus a coverage assertion that fails "
     "when a field or level has no mutation)",
     "$PY -m pytest tests/test_spec_gate.py -k counterfeit_or_missing"),
    ("0022", "external", 15, "R15-2",
     "specs/REVIEW_LESSONS.md carried two second copies of its own: it said 39 "
     "external findings collapse into six classes while the six headings summed "
     "to THIRTY (nine findings were never classified), and it restated the "
     "suite duration as ~5min beside carriers measuring 16:45, 15:06 and 1:33",
     "specs/review_lessons.py (a per-finding classification checked TOTAL "
     "against the closure ledger, with the table GENERATED from it), "
     "specs/REVIEW_LESSONS.md (counts and the duration removed from prose)",
     "$PY specs/review_lessons.py --check"),
    # ---- 0024 (L1) external round 1 -------------------------------------
    ("0024", "external", 1, "F1",
     "the spec declared independence from 0025 while its rewrite target "
     "`unclassified` is defined and protected there — without 0025 the member "
     "is not registry-resident and a functional host shadow lets the rewrite "
     "supersede",
     "Spec-Requires header, the F1 blockquote",
     "grep -n 'Spec-Requires' specs/0024-authorship-before-structural-quarantine.md  "
     "# names 0005 AND 0025, with the coupling stated in the blockquote below it"),
    ("0024", "external", 1, "F2",
     "the coherence predicate was an intent, not a computation — the shipped "
     "ingest str()-converts truthy non-strings, so subject=[\"user\"] survives "
     "the completeness check and the predicate's domain was undefined over it",
     "§4a, §2c (subject AND relation cells), U1",
     "grep -n 'casefold' specs/0024-authorship-before-structural-quarantine.md  "
     "# the canonical predicate, shared with the write site; odd types fail closed"),
    ("0024", "external", 1, "F3",
     "the invariant inventory existed in three drifted copies — §6 out of "
     "order, §7a citing a W-range, the package header hand-typing a range one "
     "past the real list",
     "§6 (the ONE list), §7a tests row, collected_header_0024_0025.txt",
     "grep -n 'ONE authoritative' specs/0024-authorship-before-structural-quarantine.md  "
     "# and the header template now points at §6 instead of restating a count"),
    ("0024", "external", 1, "F4",
     "§8 claimed provenance accuracy in general; the rule corrects the "
     "literal-user-subject cell (~40.7% of the measured mislabels), "
     "prospectively, and the claim must not exceed it",
     "§8",
     "grep -n 'cell the rule recognizes' specs/0024-authorship-before-structural-quarantine.md"),
    # ---- 0025 (L2) external round 1 -------------------------------------
    ("0025", "external", 1, "F1",
     "the rewrite could launder hearsay: a registry omitting "
     "`third_party_claim` routes the extractor's quarantine relation through "
     "the off-vocabulary path, and disclosure computed post-rewrite no longer "
     "trips the quarantine test",
     "§3 (the ordering), §4b-ii, X8/X9 widened, new X10",
     "grep -n 'X10' specs/0025-relation-vocabulary-enforcement.md  "
     "# disclosure from the ORIGINAL relation, before the rewrite, retained"),
    ("0025", "external", 1, "F2",
     "the retry was a description, not a construction — call count, prompt, "
     "matching, episode and malformed-output behaviour all undefined",
     "§4b(1)",
     "grep -n 'exactly ONE provider call per EVENT' specs/0025-relation-vocabulary-enforcement.md"),
    ("0025", "external", 1, "F3",
     "X5 and X8 contradicted with no construction order (injection-first "
     "makes the empty cell unreachable), key/name coherence was unstated, and "
     "the registry could be mutated mid-event",
     "§4b-ii, X5 restated, new X11",
     "grep -n '4b-ii' specs/0025-relation-vocabulary-enforcement.md  "
     "# five ordered steps, empty tested AS SUPPLIED, deep-copy snapshot"),
    ("0025", "external", 1, "F4",
     "the §3 matrix typed `prefers` non-functional 'by design'; shipped "
     "schema.py:203 marks it functional=True — the matrix contradicted the "
     "code it describes",
     "§3 matrix",
     "grep -n 'name=\"prefers\", functional=True' src/veracium/schema.py  "
     "# the shipped flag the corrected row now states"),
    ("0025", "external", 1, "F5",
     "§2 said one new count while §4c and X4 said three, and no caller "
     "surface (Memory/MCP/CLI/telemetry) was dispositioned",
     "§2 result-dict row, §4c, §7a",
     "grep -n 'STRIPS all five' specs/0025-relation-vocabulary-enforcement.md  "
     "# the carrier table moved into the SS4c inventory at round 3 (R3-2); the "
     "MCP-strips disposition this finding demanded is this row"),
    ("0025", "external", 1, "F6",
     "'preserved in the note' put the recovery carrier in free prose an LLM "
     "also writes — unparseable back out and spoofable by note content",
     "§4b(2), X3, §2 (`Edge.original_relation`), 0024 §4b(3)",
     "grep -n 'original_relation' specs/0025-relation-vocabulary-enforcement.md "
     "specs/0024-authorship-before-structural-quarantine.md  "
     "# one typed carrier, both specs"),
    # ---- 0024 (L1) external round 2 -------------------------------------
    ("0024", "external", 2, "R2-1",
     "two round-1 fixes contradicted when composed: X10 (disclosure from the "
     "original relation) vs §4b (author-rules disclosure after the coherence "
     "rewrite) — the reference implemented one and violated the other",
     "0025 §4b-iii (the one pipeline), 0024 §4b(2), X10 narrowed",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# vector_combined_pipeline_ordering — the cross-spec cell, both branches"),
    ("0024", "external", 2, "R2-2",
     "§8 promised relayed content is never asserted; a relay mis-emitted with "
     "subject='user' lands inside the first-person exception and U1 cannot "
     "catch it",
     "§8 (recorded-claimant property), §7 (the two doors)",
     "grep -n 'NON-USER claimant' specs/0024-authorship-before-structural-quarantine.md"),
    ("0024", "external", 2, "R2-3",
     "§3b claimed no new caller surface while U7 added three; U5's test name "
     "promised the withdrawn note carrier; telemetry had no consent "
     "disposition",
     "§3b, §7a carriers row, U5, U7 ownership pointer",
     "grep -n 'test_redisposition_carries_the_original_relation' "
     "specs/0024-authorship-before-structural-quarantine.md"),
    # ---- 0025 (L2) external round 2 -------------------------------------
    ("0025", "external", 2, "R2-1",
     "the round-1 shadow rule rejected the shipped DEFAULT_RELATIONS (it "
     "contains third_party_claim) — ordinary ingestion could not start; and "
     "the 'deep-copied immutable snapshot' wrapped mutable pydantic models",
     "§4b-ii steps 3-5, X9, X11",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# vector_the_shipped_default_registry_is_accepted + "
     "vector_snapshot_resists_mutation_through_itself"),
    ("0025", "external", 2, "R2-2",
     "retry matching was not total: duplicate pairs double-recovered, a "
     "reserved answer counted as recovery, two normalizations, retried "
     "counted with no provider, §9 said per-triple, exceptions unspecified",
     "§4b(1) rewritten, §9",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# vector_duplicate_pairs_consume_one_to_one + "
     "vector_reserved_retry_answer_is_residual_not_recovered + "
     "vector_no_provider_means_retried_zero + "
     "vector_provider_failures_degrade_recorded_never_raised"),
    ("0025", "external", 2, "R2-3",
     "Edge.original_relation broke the byte contracts: X6 false with None "
     "serialized, receipt partition and pinned digest domain broken, "
     "portability ungoverned",
     "§2 field row (None-omission + receipts + FORMAT_VERSION), X6",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# vector_unaffected_edge_is_byte_identical"),
    ("0025", "external", 2, "R2-4",
     "the §2c relation cell still claimed a truthy non-string is dropped — "
     "the same cell round 1 corrected in 0024's twin matrix",
     "§2c relation row",
     "grep -n 'R2-4' specs/0025-relation-vocabulary-enforcement.md"),
    ("0025", "external", 2, "R2-5",
     "§3b said no new caller surface while counters and CLI/telemetry "
     "changed; counter ownership was scattered across the pair",
     "§3b, §4c (the single authority), 0024 U7 pointer",
     "grep -n 'AUTHORITATIVE disposition' specs/0025-relation-vocabulary-enforcement.md"),
    # ---- 0024 (L1) external round 3 -------------------------------------
    ("0024", "external", 3, "R3-1",
     "the combined pipeline composed the pair and forgot the accepted stack "
     "— a standing-revoked source's incoherent triple came out MENTIONABLE "
     "against 0023 N1, and §5 claimed 0023 behaviour unchanged",
     "0025 §4b-iii step 3, 0024 §5 regime row",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# vector_revoked_source_floor_wins_over_coherence — shows the "
     "without-the-floor bite on purpose"),
    ("0024", "external", 3, "R3-2",
     "Edge.original_relation carried two definitions across the pair, and "
     "§5/§7a still described the pre-round-1 registry and schema shapes",
     "0025 §2 (the one definition, two writers), 0024 §4b(3), §5, §7a",
     "grep -n 'TWO writers' specs/0025-relation-vocabulary-enforcement.md"),
    # ---- 0025 (L2) external round 3 -------------------------------------
    ("0025", "external", 3, "R3-1",
     "the snapshot froze (name, functional) while the prompt renders desc — "
     "prompt and classification could observe different registries, and a "
     "desc-drifted reserved shadow passed the check",
     "§4b-ii steps 3+5 (complete canonical form, one snapshot for all reads)",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# vector_reserved_desc_drift_is_refused + "
     "vector_prompt_renders_selectable_set_from_the_snapshot"),
    ("0025", "external", 3, "R3-2",
     "counter inventories conflicted (three vs invalid vs five reference "
     "keys) and redispositioned was missing from the authority 0024 defers "
     "to",
     "§4c (THE inventory: five public counters, retry_calls reference-only)",
     "grep -n 'THE COUNTER INVENTORY' specs/0025-relation-vocabulary-enforcement.md"),
    ("0025", "external", 3, "R3-3",
     "the extractor could select unclassified directly and bypass the "
     "residual instrument — stored in-vocabulary with invalid=0",
     "§4b-iv (the selectable set)",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# vector_direct_unclassified_emission_is_residual"),
    ("0025", "external", 3, "R3-4",
     "the receipt digest-domain bump had no cross-era rule — a legitimate "
     "lost-response retry hashed under the new domain read as a different "
     "request against a legacy receipt",
     "§2 field row (cross-era rule), §7b 0014 row (amendment authorization)",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# vector_receipt_digest_crosses_eras — legacy dual-domain match, "
     "true mismatch still refused"),
    # ---- 0024 (L1) external round 4 -------------------------------------
    ("0024", "external", 4, "R4-1",
     "the §3 matrix stated unconditional finals from author and relation — "
     "false for a standing-revoked source (0023 N1) — and §4b said 'author "
     "rules ALONE'",
     "§3 (scope + the revocation row), §4b(2) base-vs-final language",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# vector_revoked_source_floor_wins_over_coherence — the revoked "
     "USER-authored third_party_claim cell the reviewer named"),
    ("0024", "external", 4, "PAIR-R4-1",
     "the published measurements did not reproduce from the shipped script",
     "§1 (script-exact figures, rule stated), §2c-ii",
     "grep -n '41.7%' specs/evidence/0025/corpus_counts.py "
     "specs/0024-authorship-before-structural-quarantine.md  "
     "# the recorded run and the spec cite ONE figure; the corpus is "
     "local-only, the script runs where it lives"),
    # ---- 0025 (L2) external round 4 -------------------------------------
    ("0025", "external", 4, "R4-1",
     "the reference invented its canonical third_party_claim gloss; the "
     "real DEFAULT_RELATIONS was REFUSED, and the lossy acceptance vector "
     "(desc dropped, empty accepted) could not catch it",
     "§4b-ii (verbatim glosses), reference CANONICAL imports the product",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# vector_the_shipped_default_registry_is_accepted — the ACTUAL "
     "objects, desc asserted non-empty and equal"),
    ("0025", "external", 4, "R4-2",
     "the reference sorted the prompt while the product renders insertion "
     "order — prompt bytes changed, X6 unestablishable, X11 stale",
     "§4b-iv insertion order, X6, X11",
     "$PY specs/evidence/0025/reference_enforcement.py  "
     "# the shipped-registry vector asserts rendered order == mapping order"),
    ("0025", "external", 4, "R4-3",
     "two three-count copies survived and retry_calls had no public "
     "disposition",
     "§4c (the only count carrier), §3b, X12",
     "grep -n 'X12' specs/0025-relation-vocabulary-enforcement.md"),
    ("0025", "external", 4, "R4-4",
     "the cross-era receipt rule was not implementable: no durable field "
     "definition, no failure matrix, no migration, dict-stored evidence "
     "under invented domains",
     "§4b-v, the completed 0014 header enumeration",
     "$PY specs/evidence/0025/receipt_era_harness.py  "
     "# real SQLite, SHIPPED digest+domain, every matrix row incl. the "
     "fail-closed unknown-domain cell"),
    ("0025", "external", 4, "PAIR-R4-1",
     "the corpus script did not compute every retained claim, and the "
     "near-synonym 2.6% rested on an unshipped semantic grouping",
     "§1 sizing table (requalified), §2c-ii (script-exact), Q2",
     "grep -n '48.1%' specs/evidence/0025/corpus_counts.py "
     "specs/0025-relation-vocabulary-enforcement.md  "
     "# the recorded run and the spec cite ONE figure; near-synonyms "
     "requalified in both carriers"),
    # ---- 0024 (L1) external round 5 -------------------------------------
    ("0024", "external", 5, "R5-1",
     "the THIRD_PARTY incoherent cell was changed by the matrix and declared "
     "unchanged by §5, with U2 flooring where the matrix specified — two "
     "green implementations could disagree",
     "§5 (the ruled transition), U2 (exact output), §3 scope sentence",
     "grep -n 'CHANGED for exactly the incoherent subset' "
     "specs/0024-authorship-before-structural-quarantine.md  "
     "# and the reference asserts USE_ONLY exactly: "
     "vector_author_floor_holds_through_redisposition"),
    # ---- 0025 (L2) external round 5 -------------------------------------
    ("0025", "external", 5, "R5-1",
     "the cross-era construction named a nonexistent receipts table, one "
     "comparison site of two, a stand-in harness table, and a frozen vector "
     "that treated any present domain as v2",
     "§4b-v (shipped topology, both sites), the corrected 0014 enumeration",
     "$PY specs/evidence/0025/receipt_era_harness.py  "
     "# schema_version.py's own DDL, both comparison shapes, fail-closed "
     "cells included"),
    ("0025", "external", 5, "R5-2",
     "X6/§5 claimed store-wide byte identity while the spec changes digests, "
     "receipts, schema and the export header; §2 claimed old readers accept "
     "the new export",
     "X6 (two exact carriers + exclusions), §5 regime row, §2 portability",
     "grep -n 'EXACTLY TWO carriers' specs/0025-relation-vocabulary-enforcement.md"),
    ("0025", "external", 5, "R5-3",
     "the §3 opening still stated the round-1 original-relation rule that "
     "round 2 withdrew — in the section that motivated the withdrawal",
     "§3 opening (post-coherence establishment + fallback retention)",
     "grep -n 'ESTABLISHED after coherence processing' "
     "specs/0025-relation-vocabulary-enforcement.md"),
    ("0025", "external", 5, "R5-4",
     "the §1 principal table kept the retired figures after the round-4 "
     "carrier sweep claimed completeness",
     "§1 (script-exact, including the derived 12,557)",
     "grep -n '64,030 — 34.9% of 183,417' "
     "specs/0025-relation-vocabulary-enforcement.md  "
     "# the principal table carries the script-exact figure"),
    # ---- 0025 (L2) external round 6 -------------------------------------
    ("0025", "external", 6, "R6-1",
     "the era harness fabricated an unreachable pre-D2 receipt and wrapped "
     "its own matrix as both 'sites' — it never invoked the product paths "
     "its REAL-construction claim named",
     "specs/evidence/0025/receipt_era_harness.py (v4 — live paths)",
     "$PY specs/evidence/0025/receipt_era_harness.py  "
     "# a product-written v4 receipt, the live phase-1 replay, the era bite "
     "raised by the shipped comparison, the snapshot-less outcome refusal"),
    ("0025", "external", 6, "R6-2",
     "the domain matrix was total over domains and not over receipt "
     "states — the legal snapshot-less receipt had no cell",
     "§4b-vi (writer invariant + the total three-axis matrix)",
     "grep -nF 'domain non-NULL iff digest non-NULL' "
     "specs/0025-relation-vocabulary-enforcement.md  "
     "# the invariant survives round 7's consolidation, scoped to new writes  "
     "# and the live vector: vector_snapshotless_receipt_takes_the_outcome_path_live"),
    ("0025", "external", 6, "R6-3",
     "four receipt carriers were stale: a phase-2 label on the phase-1 "
     "site, a phase-2-only inventory row, a pending-AND-authorized status, "
     "a versioned docstring",
     "§2 cell, §7a, §7b, reference_enforcement.py docstring",
     "grep -n 'The one status, stated once' "
     "specs/0025-relation-vocabulary-enforcement.md"),
    ("0025", "external", 6, "PACKAGE-R6-1",
     "the COLLECTED header duplicated the 41.5% measurement the specs had "
     "retired — the round-1 second-copy class in the same carrier",
     "specs/package/collected_header_0024_0025.txt (measurement removed)",
     "grep -n 'PACKAGE-R6-1' specs/package/collected_header_0024_0025.txt"),
    # ---- 0025 (L2) external round 7 -------------------------------------
    ("0025", "external", 7, "R7-1",
     "the receipt contract diverged across its own two subsections — "
     "stamping vs NULL rules, two owners for NULL, an unscoped writer "
     "invariant — and the co-owned 0014 carrier had neither matrix nor "
     "both sites",
     "the consolidated §4b-v, the rewritten 0014 header blockquote",
     "grep -nF 'NEW WRITES ONLY' specs/0025-relation-vocabulary-enforcement.md "
     "specs/0014-maintenance-attribution.md  "
     "# the scoped invariant, present in BOTH co-owned carriers"),
    ("0025", "external", 7, "R7-2",
     "the live phase-2 both-digests branch was untested, the matrix vector "
     "bypassed the rows, and the matrix had no §6 acceptance invariant",
     "receipt_era_harness.vector_live_phase2_replay_and_era_bite, the "
     "row-read matrix vector, X13",
     "$PY specs/evidence/0025/receipt_era_harness.py  "
     "# the phase-2 replay and era bite via same-plan resubmission, live"),
    ("0025", "external", 7, "R7-3",
     "the round-6 carrier sweep left four inexact claims: a phase-2 label, "
     "a stale harness description, a premature both-sites print, and a "
     "no-fabricated-receipts overclaim",
     "§4b-v evidence bullet, the harness docstring and print, the v9 "
     "version row's qualification",
     "grep -nF 'simulated by direct row edits' "
     "specs/0025-relation-vocabulary-enforcement.md  "
     "# the qualification, in the normative carrier"),
    # ---- 0025 (L2) external round 8 -------------------------------------
    ("0025", "external", 8, "R8-1",
     "the §2 receipts cell survived three consolidations still directing a "
     "write §4b-v refuses — the same document permitted and rejected "
     "(NULL, v2)",
     "§2 receipts cell (four-way summary + pointer, restating retired)",
     "grep -nF 'SUMMARIZES and never restates' "
     "specs/0025-relation-vocabulary-enforcement.md"),
    ("0025", "external", 8, "R8-2",
     "X13 demanded one test over a product its surfaces cannot express — "
     "phase 1's unconditional snapshot, write-unreachable migrated states, "
     "the snapshot-less read axis, pre-D2 never a new write",
     "§4b-v per-surface reachability table, X13 restated as five tests",
     "grep -nF 'named-unreachable' "
     "specs/0025-relation-vocabulary-enforcement.md  "
     "# the table names what each surface cannot reach"),
    ("0025", "external", 8, "R8-3",
     "0014's amendment stack was layered — the older phase-2-only summary "
     "contradicted the appended both-sites contract, leaving phase 1 on "
     "v1-only comparison for migrated receipts",
     "the single consolidated 0014 header block",
     "grep -nF 'replace, never layer' specs/0014-maintenance-attribution.md"),
    # ---- 0025 (L2) external round 9 -------------------------------------
    ("0025", "external", 9, "R9-1",
     "the phase-2 per-surface row omitted the pre-D2 precedence phase 1 "
     "carried — a v3 receipt could reach domain/digest logic and still "
     "pass the named test",
     "§4b-v phase-2 row (outcome-version axis, boundary FIRST, exploding "
     "sentinel), harness vector",
     "$PY specs/evidence/0025/receipt_era_harness.py  "
     "# vector_phase2_pre_d2_precedes_all_domain_logic — a poisoned domain "
     "loses to the boundary at both live phases"),
    ("0025", "external", 9, "R9-2",
     "0014's 'verbatim' claim went stale the day X13 split — it lacked the "
     "per-surface table and cited a singular test",
     "the 0014 block (per-surface obligations + five test names), the "
     "§4b-v pointer (verbatim phrasing retired)",
     "grep -nF 'test_receipt_migration_states' "
     "specs/0014-maintenance-attribution.md  "
     "# the five names, in the co-owned carrier"),
    ("0025", "external", 9, "R9-3",
     "lexicographic prior-archive selection breaks at v10 and same-version "
     "reseals were not excluded; the manifest's typed carrier count "
     "survived the fifth carrier",
     "seal_package._changed_from_previous (numeric key), the de-counted "
     "manifest template",
     "grep -nF \"GENERATED from the sealer's own LOOSE set\" "
     "specs/package/manifest_0024_0025.txt  "
     "# round 10 replaced the de-count note with the generated list; the "
     "de-counting this finding demanded survives one construction deeper"),
    # ---- 0025 (L2) external round 10 ------------------------------------
    ("0025", "external", 10, "R10-1",
     "the round-9 fix put the outcome-version axis on one surface of "
     "three, and the harness claimed a sentinel it never installed over "
     "a column the shipped accessor never reads",
     "§4b-v READ + PHASE 1 rows (the cross-product), the counting "
     "sentinel, the honest forward-looking scope bullet",
     "$PY specs/evidence/0025/receipt_era_harness.py  "
     "# vector_phase2_pre_d2_precedes_all_domain_logic — zero sentinel "
     "invocations asserted at both live phases"),
    ("0025", "external", 10, "R10-2",
     "the de-counted manifest still hand-enumerated four carriers; the "
     "sealer docstring said four; no regression covered the numeric "
     "selection",
     "the __LOOSE__ generation from LOOSE_CARRIERS + divergence guard, "
     "the regression test",
     "$PY -m pytest tests/test_spec_gate.py::"
     "test_changed_from_previous_orders_numerically_and_skips_same_version "
     "-q  # real tiny archives, v9/v10/v11, same-version excluded"),
    # ---- 0025 (L2) external round 11 ------------------------------------
    ("0025", "external", 11, "R11-1",
     "§7b still recorded the 0014 amendment as unconfirmed while the "
     "spec's own header announced the round-10 confirmation",
     "§7b (the confirmation recorded)",
     "grep -nF 'CONFIRMED by the external reviewer in round 10' "
     "specs/0025-relation-vocabulary-enforcement.md"),
    ("0025", "external", 11, "PACKAGE-R11-1",
     "the numeric-selector regression invoked git archive and crashed in "
     "the reviewer's extraction (no .git), taking the closure-evidence "
     "gate with it",
     "seal_package._select_prior_archive (pure), the reshaped regression",
     "$PY -m pytest tests/test_spec_gate.py::"
     "test_changed_from_previous_orders_numerically_and_skips_same_version "
     "-q  # runs on supplied paths — no git, extraction-safe"),
    ("0025", "external", 11, "PACKAGE-R11-2",
     "LOOSE and LOOSE_CARRIERS were two copies of the claimed single "
     "authority",
     "the module-level LOOSE_CARRIERS constant + the seal-time REL_PATH "
     "assertion",
     "$PY -c \"import ast, sys; tree = ast.parse(open('specs/seal_package.py').read()); "
     "names = [n.id for node in ast.walk(tree) if isinstance(node, ast.Assign) "
     "for n in node.targets if isinstance(n, ast.Name) and n.id == 'LOOSE_CARRIERS']; "
     "sys.exit(0 if len(names) == 1 else 1)\"  "
     "# the reviewer's own round-12 check, adopted: exactly ONE assignment "
     "PROVES the single authority — a grep only located its comment"),

    # ---- 0011 internal round 1 (research, 2026-08-23). The spec is NOT
    # implemented, so the artifact that carries each fold is the spec text
    # itself; the evidence reads it. Where the fold cites the finding by
    # name, the command anchors on that citation.
    ("0011", "internal", 1, "0011-I1-M1",
     "§2c cited 0024 Q3 cells that are NOT on main post-revert, and pointed "
     "at a §3b the spec did not have (its sections ran §1, §2, §3, §2c, §3c)",
     "the citation names the ACCEPTED surface as amended by A1 rather than "
     "shipped tests, and the section ordering is repaired so §3b exists and "
     "the reference resolves",
     "grep -n 'as amended by A1, landed' specs/0011-subject-scoped-entitlement.md && "
     "grep -nE '^## 3b\\.' specs/0011-subject-scoped-entitlement.md"),

    ("0011", "internal", 1, "0011-I1-M2",
     "E5 bound the correction's ARGUMENTS but not the ACTOR, so any caller "
     "reaching correct() obtained a valid capability and §2c's adversarial "
     "cell was closed only against forge/replay of a DIFFERENT correction",
     "E-Q4 ruled YES: the acting principal is the fifth tuple element, "
     "verified inside the transaction like the rest",
     "grep -n \"E5's fifth element\" specs/0011-subject-scoped-entitlement.md"),

    ("0011", "internal", 1, "0011-I1-M3",
     "§9.3's broad form (any user-authored retirement of other-subject "
     "sourced fact refuses pending confirmation) had no measured "
     "constituency",
     "keep the NARROW cell for v1 and add a measurement rider to §4b, so "
     "counting the refusal rows post-release is a design obligation rather "
     "than a hope",
     "grep -n 'MEASUREMENT RIDER' specs/0011-subject-scoped-entitlement.md"),

    ("0011", "internal", 1, "0011-I1-m4",
     "§1 quoted the 2026-08-02 split-date defect state in the present tense, "
     "though 0003 shipped in v0.6.0 — a cold reader would file a live defect",
     "marked as the historical motivation, at the time of the split",
     "grep -n 'At the time of the split' specs/0011-subject-scoped-entitlement.md"),

    ("0011", "internal", 1, "0011-I1-m5",
     "the M7 site was cited by line number, which had already moved",
     "cited by SYMBOL instead, which does not drift",
     # the negative needle is scoped to the PRE-LEDGER portion of the
     # spec: the generated Review-closure block (acceptance, 2026-08-29)
     # quotes every closure command verbatim, so an unscoped negative
     # grep would match its own quotation
     "grep -n 'at the symbol .Memory.correct' specs/0011-subject-scoped-entitlement.md && "
     "! sed '/<!-- GENERATED:review-closure -->/,$d' "
     "specs/0011-subject-scoped-entitlement.md | grep -n '__init__.py:1362'"),

    ("0011", "internal", 1, "0011-I1-m6",
     "§4d's derived(from_class) had an OPEN domain — an unknown or malformed "
     "value had no defined behaviour (the week's validator lesson: refuse the "
     "unknown, do not merely cover the known)",
     "the domain is CLOSED and validated at construction, failing closed to "
     "the derived(THIRD_PARTY) floor, with S5 carrying the unknown-value cell",
     "$PY specs/evidence/0011/check_round1_fold.py  # m-6 asked for a CLOSED domain validated at construction; external R1-4 then found that §4d named TWO outcomes for a malformed value and rewrote the passage, which broke this row's original grep. The property is unchanged and is now checked structurally — one outcome, absence kept distinct, every invalid cell enumerated — rather than by a sentence a later fold can reword"),

    # ---- 0026 internal round 1 (research, 2026-08-24).
    ("0026", "internal", 1, "0026-I1-M1",
     "§1's census figures were the PRE-correction values (183,416 / 1,637 / "
     "41.5%); the shipped script over the cache says 183,417 / 1,644 / 41.7% "
     "— a value that drifted from its source artifact and was consumed by "
     "label, which is this spec's own thesis in miniature",
     "exact script output in both carriers, with the drift itself recorded "
     "as the provenance note",
     "grep -c '183,417' specs/0026-label-value-agreement.md && grep -c '41.7' specs/0026-label-value-agreement.md"),

    ("0026", "internal", 1, "0026-I1-M2",
     "§8 promised a SEMANTIC property — a relayed claim that names its "
     "source is never asserted — delivered by a LEXICAL mechanism, so a note "
     "reading 'the vet mentioned this' falsifies the claim while every "
     "V-invariant stays green",
     "the §8 sentence is scoped to the lexicon (a mechanical surface) and "
     "§6a's run reports the coverage denominator, so the claim ships as a "
     "measured fraction of the naming population rather than an implied whole",
     "grep -n 'the promise is scoped to the LEXICON' specs/0026-label-value-agreement.md && "
     "grep -n 'coverage denominator' specs/0026-label-value-agreement.md"),

    ("0026", "internal", 1, "0026-I1-m3",
     "§3b described the floor's position two ways (after the pipeline and "
     "before the accepted floors, versus as one more accepted floor in step "
     "3), reading as two different positions",
     "monotonicity dissolves it — floors only LOWER, so order within the "
     "floor set is irrelevant; the spec says that and picks one description",
     "grep -n 'floors only LOWER' specs/0026-label-value-agreement.md"),

    ("0026", "internal", 1, "0026-I1-m4",
     "a POINTER, not a defect: when the L3 round takes the render question, "
     "research's baseline records are prior evidence — B02's answer already "
     "rendered attribution from content while the edge sat MENTIONABLE",
     "recorded against V-Q1 so the L3 round starts from the existing "
     "evidence; no spec change was required and none was made",
     "grep -n 'V-Q1' specs/0026-label-value-agreement.md"),

    ("0026", "internal", 1, "0026-I1-m5",
     "the stale 183,416 appeared once more in the demotion bullet — the M-1 "
     "sweep had to catch EVERY carrier, not the first",
     "swept; the only surviving occurrences are inside the provenance note "
     "that quotes the old figures deliberately, which this command allows "
     "for by name rather than by pretending the string is gone",
     "! grep -n '183,416' specs/0026-label-value-agreement.md | grep -v 'v1 carried'"),

    # ---- 0011 external round 1 (2026-08-26). The spec is a DRAFT: the
    # artifact carrying each fold is its own text, except PACKAGE-R1-1 whose
    # fold is a runnable script and is checked by running it.
    ("0011", "external", 1, "0011-R1-1",
     "the central entitlement cell was not representable — `sourced`, "
     "`self-assertion` and 'confirmation, a higher rung' had no runtime "
     "predicate; §4b's condition omitted the sourced term, contradicting "
     "§3c; and the measurement rider could not measure the broad rule's "
     "constituency, which produces no refusal row at all",
     "closed predicates over state that exists today, a TOTAL policy "
     "function, every absence case stated, the over-inclusion pointed in "
     "the refusing direction, the 0008 phrase withdrawn, the basis-aware "
     "form deferred rather than unfreezing 0016, and the rider made "
     "measurable with a counts-only counter for the allowed-but-broad-"
     "refusing cell",
     '$PY specs/evidence/0011/check_round1_fold.py  # checks the policy block is TOTAL and carries the sourced term v4 omitted, both predicates are DEFINED not merely used, and the rider has the allowed-cell counter that makes it measurable'),

    ("0011", "external", 1, "0011-R1-2",
     "E5 was claimed to be unforgeable and to authenticate CORRECTORS; 0020 "
     "states the principal is host-supplied, forgeable and unauthenticated, "
     "and correct() mints the authorisation from caller-controlled values, "
     "so a fresh impersonation passes the in-transaction check",
     "the claim is WITHDRAWN in every carrier that made it; the binding is "
     "integrity and attribution; correct() is a protected host API with the "
     "host's authentication and intent obligations stated",
     '$PY specs/evidence/0011/check_round1_fold.py  # checks the unforgeable/authentication claim is gone from EVERY carrier that made it and the host-obligation table exists — the finding was a claim in three places, not one sentence'),

    ("0011", "external", 1, "0011-R1-3",
     "E3 defined contention as two active same-class edges, which is FALSE "
     "against accepted 0012 — it persists same-value restatements as "
     "separate active edges and calls them uncontested; the reviewer "
     "executed the test that proves it",
     "contention requires >=2 DISTINCT normalised _value_key values, using "
     "0012's own normalisation; composition with 0003/0012 stated; the "
     "maintain claim narrowed so per-edge expiry is not suspended; 0012 "
     "added to Spec-Requires and lifecycle.py to the consumer list",
     "$PY specs/evidence/0011/check_contention_rule.py  # the fold checked against 0012's OWN _value_key, runnable under the reviewer's bare offline interpreter; the shipped behaviour it must not contradict is tests/test_0012_currency_renewal.py::test_a_same_value_restatement_produces_no_contention_artifacts"),

    ("0011", "external", 1, "0011-R1-4",
     "§4d named TWO different observable outcomes for one input — a "
     "malformed from_class both refused by the constructor and floored to "
     "derived(THIRD_PARTY)",
     "one outcome: it RAISES and nothing is written; ABSENCE is a distinct "
     "input that keeps the floor; the complete direct/derived grammar "
     "enumerated with every cell reachable",
     '$PY specs/evidence/0011/check_round1_fold.py  # checks ONE outcome for malformed input, the contradictory flooring sentence absent, absence kept distinct, and all four RAISES cells enumerated'),

    ("0011", "external", 1, "0011-R1-5",
     "S6's three labels were neither total (a quarantined, grounded, "
     "uncontested edge matched ZERO) nor exclusive (a mentionable, "
     "grounded, contested edge matched TWO), and the premise was false: no "
     "shipped reader interleaves history with present fact",
     "a five-row FIRST-MATCH precedence table — total by catch-all, "
     "exclusive by ordering — with QUARANTINED_CLAIM and CONTESTED_CURRENT "
     "added; the invariant asserted over the cross-product; E6 re-motivated "
     "and the false premise retracted in place",
     '$PY specs/evidence/0011/check_round1_fold.py  # checks a 5-row first-match table ending in a catch-all and carrying QUARANTINED_CLAIM and CONTESTED_CURRENT — the two labels whose absence made an edge match zero'),

    ("0011", "external", 1, "0011-PACKAGE-R1-1",
     "the deciding SELF-floor measurement had NO evidence artifact — the "
     "archive could not re-derive 72,253 passes, 305 candidates, ~30 "
     "self-denoting rows or the 0.016% conclusion; 0025's aggregate "
     "supports corpus size, not subject classification",
     "subject_census.py plus a counts-only aggregate digest-bound to the "
     "same cache sha as 0025's census, and the masked distinct-string "
     "candidate table the classification was made over; the load-bearing "
     "figure reproduces exactly and the two that did not are RETIRED",
     "$PY specs/evidence/0011/subject_census.py --aggregate "
     "specs/evidence/0011/subject_aggregate.json"),

    # ---- 0011 external round 2 (2026-08-27). Four of five were defects in
    # round 1's own fixes; the evidence runs, it does not grep.
    ("0011", "external", 2, "0011-R2-1",
     "the round-1 predicates made `source_id` an ENTITLEMENT CAPABILITY in "
     "both directions — omitting the prior's source_id ALLOWED the "
     "retirement, adding any source_id to the incoming assertion ALLOWED it "
     "too — against accepted 0006, which says it may GROUP never GRANT and "
     "was not even declared as a prerequisite",
     "`sourced` is DELETED and the decision reads no source_id at all; the "
     "rule refuses on subject class plus self-assertion; 0005/0006/0015 "
     "join Spec-Requires; the lost narrowness is stated as a cost and "
     "deferred to 0016's frozen carrier; an invariance matrix is specified",
     "$PY specs/evidence/0011/check_round1_fold.py"
     "  # asserts the policy block CONTAINS NO source_id (comments "
     "stripped, so the sentence denying the read cannot satisfy it), that "
     "0006's constraint is quoted as the reason, and that the invariance "
     "matrix exists"),

    ("0011", "external", 2, "0011-R2-2",
     "`would_refuse_broad` is CONSTANT TRUE — broad is a strict superset of "
     "narrow, so a narrow refusal is always a broad one; and the rider "
     "proposed store columns while §7a named no schema/migration/erasure/"
     "telemetry surface and §7 claimed no stored state",
     "the flag is DELETED; the rider adds no stored state at all — counters "
     "on 0015's existing carrier, no column, no migration, nothing to "
     "erase — so §7 is true again and 0013 is not a prerequisite",
     "$PY specs/evidence/0011/check_round1_fold.py"
     "  # asserts the rider names the allowed-but-broad-refusing "
     "counter rather than the vacuous flag; the checker previously REQUIRED "
     "that flag, pinning the defect in place"),

    ("0011", "external", 2, "0011-R2-3",
     "the checker validated a standalone value-list function, and the "
     "shipped surface disagreed with it: two active same-class "
     "distinct-value edges in a real store are contested under the draft "
     "and NOT contested under Recall.contested (0 groups, 0 exposed)",
     "contention IS 0003's refusal-scoped notion, adopted rather than "
     "redefined; E3 governs its rendering across the named surfaces; the "
     "checker drives a REAL store",
     "$PY specs/evidence/0011/check_contention_rule.py  # the reviewer's "
     "own cell (direct distinct-value pair -> NOT contested) beside a "
     "positive control (a live refusal -> contested), both on a real store, "
     "so the check cannot pass by never firing"),

    ("0011", "external", 2, "0011-CARRIER-R2-1",
     "SEVEN contradictory authoritative statements passed the pristine fold "
     "checker, which searched narrow phrases across the whole file — so a "
     "withdrawal written in §4e satisfied it while §3a still asserted the "
     "opposite",
     "all seven swept; each assertion BOUND TO ITS NAMED ROW so a "
     "withdrawal elsewhere cannot satisfy it; S6 compared COUNT-TO-COUNT "
     "against §4f's table via a `labels=5` token",
     "$PY specs/evidence/0011/check_round1_fold.py"
     "  # row-scoped contradiction checks plus the count comparison; "
     "the count check exists because the first fix searched for 'three "
     "labels' while the row said 'one of the three', so the contradiction "
     "survived twice"),

    ("0011", "external", 2, "0011-EVIDENCE-R2-1",
     "the census aggregate mode TRUSTED its input — a fabricated one-entry "
     "aggregate with an all-zero digest printed the claimed measurement and "
     "exited 0",
     "a CLOSED typed schema (missing and unknown keys both refused) plus "
     "cross-checks against 0025's independently-derived aggregate, "
     "including a triple total summed from its relation counts, so a "
     "fabricated manifest must agree with an artifact its author does not "
     "control",
     "$PY specs/evidence/0011/subject_census.py --aggregate "
     "specs/evidence/0011/subject_aggregate.json"),

    # ---- 0011 external round 3 (2026-08-27). Three of four were again
    # defects in the previous round's fixes.
    ("0011", "external", 3, "0011-R3-1",
     "an EQUIVALENT authority bypass through `derived_from`: "
     "EvidenceContext.derived(USER) is valid and reachable, and "
     "USER/derived_from=USER carries the SAME effective authority (3) as "
     "USER/None, yet v6 refused one and allowed the other — a marker "
     "supplying no independent authority bought permission",
     "the predicate is defined over the AUTHORITY CHAIN via production "
     "effective(), so exactly two chains qualify and the bypass cell is in "
     "the refusal set by construction; the 240-cell executable matrix "
     "asserts the CLASS (equal authority decides equally), not the instances",
     "$PY specs/evidence/0011/policy_matrix.py  # both defects that shipped "
     "were planted against it and both are caught; the absence-based one "
     "trips the GENERALISED equal-authority check as well as its named cell"),

    ("0011", "external", 3, "0011-R3-2",
     "the telemetry rider contradicted accepted 0015, which DEFERS refusal "
     "counters to a new consent discussion, requires consent-version gating "
     "for new payload fields, and counts only from a fresh commit — "
     "decision-time increments would overcount aborted and PLAN_STALE "
     "attempts",
     "the rider is WITHDRAWN: v1 ships with the broad rule's constituency "
     "unmeasured and says so, leaving the consent question and the telemetry "
     "construction to 0015's own round",
     "$PY specs/evidence/0011/check_round1_fold.py  # asserts the deferral "
     "and that the spec states the constituency is unmeasured; this check "
     "previously REQUIRED the counter, pinning in place what the next round "
     "removed"),

    ("0011", "external", 3, "0011-CARRIER-R3-1",
     "five more contradictions survived the claimed sweep, and the "
     "no-source_id check was SYNTACTIC — the reviewer moved the read behind "
     "a helper defined in a separate fence and every fold check passed",
     "all five swept, and the check follows the predicate's TRANSITIVE "
     "DEPENDENCIES across fences, so a read one or two indirections away is "
     "still a read",
     "$PY specs/evidence/0011/check_round1_fold.py  # the reviewer's exact "
     "bypass and a deeper two-hop version were both replayed against it and "
     "both are refused"),

    ("0011", "external", 3, "0011-EVIDENCE-R3-1",
     "the census's deciding figures remained forgeable: `schema` was typed "
     "but never valued, so schema=999 with predicate_passes=0 and a one-row "
     "candidate table returned no findings",
     "schema == 1 required; the PREDICATE ITSELF cross-checked against "
     "0025's independently-derived subject_user on the shared subset; and "
     "every figure labelled by what backs it, with the whole-corpus count "
     "and the table's completeness marked RECORDED ONLY rather than implied "
     "to be verifiable",
     "$PY specs/evidence/0011/subject_census.py --aggregate "
     "specs/evidence/0011/subject_aggregate.json"),

    # ---- 0011 external round 4 (2026-08-27) — FINITE DESIGN ACCEPTANCE for
    # the core; three mechanical items gate the status flip.
    ("0011", "external", 4, "0011-EVIDENCE-R4-1",
     "the 240-cell oracle had DECORATIVE dimensions: source and origin were "
     "enumerated but never passed to policy(), the invariance check "
     "re-called the function instead of comparing the EMITTED cells (a "
     "planted source-conditional ALLOW exited 0), the import-flattened cell "
     "never invoked portability, and the fold checker's definition map was "
     "last-definition-wins so a shadowed dangerous helper passed",
     "the oracle is FULL-EDGE (1,440 cells over two real Edge provenances "
     "with independent source/origin), every check consumes the one emitted "
     "stream, the import cell runs production portability.import_memory in "
     "both modes, and the dependency closure carries EVERY definition of a "
     "name; both reviewer attacks are standing mutation tests",
     "$PY -m pytest tests/test_0011_policy_matrix.py::"
     "test_a_variance_planted_in_the_emission_is_caught "
     "tests/test_0011_policy_matrix.py::"
     "test_the_fold_checker_refuses_a_shadowed_helper "
     "tests/test_0011_policy_matrix.py::"
     "test_the_import_cell_runs_the_production_adapter -q -p no:randomly"),

    ("0011", "external", 4, "0011-CARRIER-R4-1",
     "five current carriers still stated the NARROW rule or the LIVE rider: "
     "§4's claim, S2, §4b's pointer at the rider, §9's ask to attack the "
     "rider's taxonomy, and S5's unclosed editing fragment",
     "all five swept to the broadened rule and the withdrawn-rider "
     "disposition; §9 redirects the reviewer at the deferral itself; "
     "obsolete wording survives only as marked history",
     "$PY specs/evidence/0011/check_round1_fold.py  # the row-scoped and "
     "closure-based checks over the swept carriers, with the shadowing "
     "attack now refused"),

    ("0011", "external", 4, "0011-PACKAGE-R4-1",
     "the generated header asserted 'sealed rounds 1-4' and 'THE FIRST "
     "SEALED PACKAGE ON THIS LINE' in the same file, beside a "
     "CHANGED_FROM_PREVIOUS inventorying the v3 delta, and every header "
     "check passed — a hand-written template paragraph reintroduced the "
     "exact defect the header's own C5-1 note records, seven lines below it",
     "the static paragraph and the static round-count sentence are DELETED "
     "from every template on both lines; seal_package.WITHDRAWN_CLAIMS "
     "refuses both shapes at seal time in wording the derived NO_PRIOR text "
     "deliberately does not use; lineage facts have exactly one source, the "
     "governed record",
     "$PY -m pytest tests/test_collected_header.py::"
     "test_no_template_hand_asserts_lineage -q -p no:randomly"),

    # ---- 0011 external round 5 (2026-08-27) — two mechanical amendments
    # under the standing finite acceptance.
    ("0011", "external", 5, "0011-EVIDENCE-R5-1",
     "cell COUNT did not prove domain COVERAGE: replacing one emitted cell "
     "with a duplicate of another kept 1,440 rows while a source/origin "
     "combination silently vanished — cardinality-preserving omission, "
     "invisible to the count check and to the truncated-stream test",
     "the oracle constructs the EXACT expected Cartesian key set "
     "independently of the emitter and requires emitted keys to equal it; "
     "duplicates are rejected separately so the replacement is named rather "
     "than hiding behind the missing-key report it causes",
     "$PY -m pytest tests/test_0011_policy_matrix.py::"
     "test_a_duplicate_hiding_a_missing_cell_is_caught "
     "tests/test_0011_policy_matrix.py::"
     "test_an_alien_cell_key_is_caught -q -p no:randomly"),

    ("0011", "external", 5, "0011-CARRIER-R5-1",
     "§3c's LIVE contract row still described the OTHER-subject refusal as "
     "'with the measurement rider' after R3-2 withdrew it; the fold checker "
     "exited 0 by finding the deferral text elsewhere in the file",
     "the row is swept and the withdrawal is BOUND TO THE ROW: the checker "
     "anchors on §3c's row and refuses the promise there specifically — a "
     "deferral stated in §4b does not un-promise a different row",
     "$PY specs/evidence/0011/check_round1_fold.py  # the row-bound rider "
     "check, planted-back promise verified biting"),

    # ---- 0011 external round 6 (2026-08-28) — evidence machinery only;
    # the finite acceptance stands.
    ("0011", "external", 6, "0011-EVIDENCE-R6-1",
     "an enum-derived dimension still self-narrowed: removing THIRD_PARTY "
     "from DERIVED changed the oracle's claimed domain from 1,440 to 1,152 "
     "cells with exit 0 — the emitter and the expected key set read the "
     "same constants, and the round-5 pins covered only the hand-picked "
     "dimensions",
     "the enum axes are pinned TO THE ENUM and the expected key set is "
     "built from the enum rather than the mutable constants; the "
     "narrowed-DERIVED mutant and a narrowed-AUTHORS sibling are standing",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_narrowed_enum_dimension_is_refused -q -p no:randomly"),

    ("0011", "external", 6, "0011-PROCESS-R6-1",
     "the campaign record was PROSE and false twice over: nine mutants had "
     "no planted tests (their verification died with the session), "
     "neutering the whole census-figure binding left 10/10 green, "
     "subject_census.py sat outside P1's filename convention, and the "
     "hand-typed totals did not add up",
     "the campaign is EXECUTABLE: mutant_registry.py binds every id to its "
     "artifact, mutation and node, runs them in one pytest invocation, and "
     "derives the totals into a generated record; the nine untested "
     "mutants are standing in-memory tests; every fold check is "
     "sentinel-proven reached; subject_census.py enters P1 via an explicit "
     "artifact registry",
     "$PY specs/evidence/0011/mutant_registry.py"),

    # ---- 0011 external round 7 (2026-08-28) — the ledger itself.
    ("0011", "external", 7, "0011-PROCESS-R7-1",
     "registry entries were not bound to executed mutants: success derived "
     "from the distinct pytest nodes, so a fictitious entry riding an "
     "already-listed passing node inflated the total with exit 0; artifact "
     "paths were unvalidated; and the result record was WRITE-ONLY — "
     "overwritten by every run, read by nothing",
     "the binding comes from the executed side: each standing test reports "
     "the id(s) it kills, and the runner requires reported kills to equal "
     "the declared ids exactly; artifacts validated, duplicates refused; "
     "the default invocation is a non-mutating check requiring whole-record "
     "equality with the shipped record; --write is seal-time only",
     "$PY specs/evidence/0011/mutant_registry.py  # CHECK mode: re-runs the "
     "campaign, verifies the one-to-one kill binding, and requires the "
     "shipped record to equal the recomputation; the attack regressions are "
     "tests/test_0011_mutant_registry.py::test_missing_observations_fail_coverage "
     "and ::test_the_shipped_record_recomputes_and_diverges_on_tamper"),
     # ^ successors after the round-11 schema-4 redesign: the bogus-entry
     #   and corrupted-record regressions live on under observed-kill names

    # ---- 0011 external round 8 (2026-08-28) — the ledger's binding.
    ("0011", "external", 8, "0011-PROCESS-R8-1",
     "three adjacent registry gaps: kill ids bound globally (a node swap "
     "between two entries changed nothing), record checking by dict "
     "equality which coerces (False == 0 claimed an exact match), and "
     "artifact validation accepting /etc/passwd via pathlib's "
     "absolute-join discard",
     "kills are (node, id) pairs with the node taken from pytest's own "
     "PYTEST_CURRENT_TEST and exact pair-set equality enforced; the record "
     "check pins exact int types and compares canonical serialized bytes; "
     "artifact paths must be relative, contained and regular files — all "
     "three attacks standing at the real checker boundary",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_a_swapped_on_disk_registry_survives_and_is_refused "
     "tests/test_0011_mutant_registry.py::"
     "test_type_coerced_kill_exit_is_refused "
     "tests/test_0011_mutant_registry.py::"
     "test_artifact_outside_the_package_is_refused -q -p no:randomly"),

    # ---- 0011 external round 9 (2026-08-28) — the ledger's join and grammar.
    ("0011", "external", 9, "0011-PROCESS-R9-1",
     "per-node provenance was not behaviorally bound: a reporter looking up "
     "each id's node from the registry itself, plus a node swap, passed "
     "--write, --check and the whole focused suite — the regressions fed "
     "binding_problems() hand-built kills, never the production join",
     "an integration regression sends the node-swapped registry through the "
     "REAL execution and requires binding failure (a self-asserting "
     "reporter makes the swapped registry pass, failing the test); the "
     "runner refuses any reported node it did not invoke",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_a_swapped_on_disk_registry_survives_and_is_refused "
     "-q -p no:randomly"),

    ("0011", "external", 9, "0011-EVIDENCE-R9-1",
     "the record lacked a closed canonical grammar: duplicate JSON keys "
     "vanished at parse, found_by was an open vocabulary whose alien value "
     "regenerated cleanly, deleting the refusal branches left every test "
     "green, and the schema stayed 2 across the killed-shape change",
     "duplicates refuse AT PARSE; a recursive exactly-typed closed schema "
     "governs every level; shipped RAW BYTES must equal the canonical "
     "writer's output; schema 3; and each corrupt record is refused BY "
     "MAIN ITSELF in standing subprocess regressions",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_corrupt_records_are_refused_by_main_itself "
     "tests/test_0011_mutant_registry.py::"
     "test_non_canonical_bytes_are_refused_by_main -q -p no:randomly"),

    # ---- 0011 external round 10 (2026-08-28) — attribution leaves the artifact.
    ("0011", "external", 10, "0011-PROCESS-R10-1",
     "per-node provenance remained self-assertable: the round-9 regression "
     "swapped a LOCAL entries copy while the child imported the ON-DISK "
     "registry, so the coordinated attack — on-disk node swap plus an "
     "in-artifact reporter reading ENTRIES — passed --write, --check and "
     "all 31 focused tests",
     "the artifact performs no attribution: the reporter is an id-only "
     "writer in the TEST files, and the runner executes each node in an "
     "isolated invocation, joining every reported id to the node IT "
     "invoked; the coordinated on-disk mutation is the standing regression, "
     "driven through the real execution",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_a_swapped_on_disk_registry_survives_and_is_refused "
     "-q -p no:randomly"),   # renamed in the round-11 fold: the
                             # regression now observes SURVIVAL
                             # (schema 4), same attack, same seat

    ("0011", "external", 10, "0011-EVIDENCE-M10-1",
     "the shipped-record operand was environment-selectable via a "
     "testing-only variable, and the check ran the full campaign before "
     "parsing despite claiming grammar first",
     "the entry point is pinned to the shipped record with no selector (a "
     "standing test asserts the variable's absence from the source); "
     "corrupt operands exercise an internal helper on copies; the order is "
     "parse -> closed schema -> canonical-form-of-the-bytes -> campaign",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_non_canonical_bytes_are_refused_by_main "
     "tests/test_0011_mutant_registry.py::"
     "test_corrupt_records_are_refused_by_main_itself -q -p no:randomly"),
    # ---- 0011 external round 11 (2026-08-28) — the claim protocol removed.
    ("0011", "external", 11, "0011-PROCESS-R11-1",
     "the round-10 regression was fail-open (its copied module derived "
     "ROOT from /tmp, pytest exited 4, and the empty kill list produced "
     "the expected mismatch — it passed while executing nothing), and the "
     "id half of every kill was still a test-side claim: a reporter "
     "deriving ids from the registry, coordinated with a swapped on-disk "
     "registry, passed --write, --check and the focused suite",
     "schema 4 removes the claim protocol: entries carry their mutations "
     "as text hunks, the runner applies them and OBSERVES the kill (clean "
     "pass + mutated exit-1 failure, counts parsed, artifacts restored "
     "byte-identically verified), leave-one-out proves each hunk of a "
     "multi-hunk entry load-bearing, a dead subprocess is a named ERROR "
     "at the real root, judge-targeting hunks refuse at validation, "
     "concurrent campaigns refuse on an exclusive lock, and no reporter, "
     "kill log or pytest-side attribution exists (standing absence test)",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_a_dead_subprocess_is_an_error_not_a_defense "
     "tests/test_0011_mutant_registry.py::"
     "test_a_swapped_on_disk_registry_survives_and_is_refused "
     "tests/test_0011_mutant_registry.py::"
     "test_no_kill_claim_protocol_remains -q -p no:randomly"),
    # ---- 0011 external round 12 (2026-08-28) — identity follows the carrier.
    ("0011", "external", 12, "0011-PROCESS-R12-1",
     "duplicate mutations inflate the observed ledger: R5A duplicated "
     "under a fresh id passed validation, --write, --check and the "
     "focused suite — schema 4 moved the mutant's identity to the hunk "
     "bundle and uniqueness stayed on the id string, so every "
     "observation was genuine and only the totals lied",
     "mutation_identity — the sorted bundle of minimal-diff hunk "
     "identities (common prefix/suffix stripped, whitespace folded, "
     "pinned to the edit's absolute position; the full-text form was "
     "context-window slidable, research pre-seal) — is canonical; "
     "duplicates refuse on both carriers regardless of id, finder, "
     "node, hunk order or window; run_check fails "
     "fast on entry problems so the refusal precedes any campaign run; "
     "--write refuses without writing; the DUPR5A case is driven "
     "through both real boundaries on disk",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_a_duplicate_mutation_is_refused_at_the_real_boundary "
     "tests/test_0011_mutant_registry.py::"
     "test_mutation_identity_is_the_resulting_transformation -q -p no:randomly"),  # renamed in the round-13 fold (face four)
    # ---- 0011 external round 13 (2026-08-28) — identity with nothing left to slide.
    ("0011", "external", 13, "0011-PROCESS-R13-1",
     "hunk partitioning defeated mutation uniqueness: C2's two edits "
     "merged into one wider hunk produced byte-identical mutated "
     "artifacts under a distinct identity, and a constant-cardinality "
     "replacement hid a vanished mutant behind a double-counted one — "
     "face four of the identity ladder (id, full text, minimal diff, "
     "partitioning), each fix normalizing a richer description while "
     "identity stayed a function of the description",
     "the canonical identity is the resulting artifact transformation "
     "(per-artifact sha256 of the bytes the complete bundle produces "
     "from pristine), so no representation remains to vary; duplicates "
     "refuse on both carriers pre-campaign; both reviewer attacks are "
     "standing regressions at the real on-disk boundaries with the "
     "copied module pinned to the real root",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_partitioned_duplicates_are_refused_at_the_real_boundary "
     "tests/test_0011_mutant_registry.py::"
     "test_mutation_identity_is_the_resulting_transformation "
     "-q -p no:randomly"),
    # ---- 0011 external round 14 (2026-08-28) — the guard precedes the read.
    ("0011", "external", 14, "0011-PROCESS-R14-1",
     "both carriers computed mutation identity before validating hunk "
     "paths: a record hunk naming /etc/passwd validated CLEAN (the "
     "record carrier had no path validation at all), and /bin/sh was "
     "READ and crashed the checker with an uncaught decode error — the "
     "R8-1(3) absolute-join footgun reachable through the round-12 "
     "identity restructure",
     "one shared guard (artifact_problems) runs in BOTH carriers before "
     "identity touches the filesystem — membership is a pure string "
     "check, so an out-of-set path refuses with no read; _identity is "
     "additionally defensive (no absolute/escaping/missing reads, "
     "degrades on binary bytes); /bin/sh is the built-in no-read "
     "witness in the standing regression at the real entry point",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_out_of_tree_paths_refuse_before_any_read -q -p no:randomly"),
    # ---- 0011 external round 15 (2026-08-29) — the property's base case.
    ("0011", "external", 15, "0011-PROCESS-R15-1",
     "the snapshot pre-scan proved no-symlinks for every node BENEATH "
     "the copied roots and not for src/tests/specs themselves — "
     "is_dir() follows links, os.walk walks a symlinked top, copytree "
     "dereferences it wholesale (executed: top-level tests as a link to "
     "an external dir, sentinel copied in); a symlinked conftest.py was "
     "silently omitted rather than refused",
     "each copy root is is_symlink-checked BEFORE is_dir or any walk; "
     "symlinked and broken-symlink configuration carriers refuse with "
     "the error posture; the standing regression drives all three "
     "top-level roots plus both carrier shapes with an external "
     "sentinel proving nothing is copied",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_a_symlinked_copy_root_or_config_carrier_refuses "
     "-q -p no:randomly"),
    # ---- 0011 external round 16 (2026-08-29) — the mechanism, observed.
    ("0011", "external", 16, "0011-PROCESS-R16-1",
     "'refuse before access' was asserted nowhere: the round-15 "
     "regressions checked the refusal message only, so a mutant that "
     "copied every root into a leaked temp dir BEFORE running the "
     "guards passed the whole registry suite; and config-carrier "
     "validation ran after mkdtemp, stranding a temp dir per refusal",
     "_snapshot is two-phase (all guards read-only first, allocate+copy "
     "second with guaranteed cleanup) and the regression OBSERVES the "
     "mechanism: instrumented copytree/copy2/mkdtemp/walk must record "
     "zero pre-refusal activity, and the reviewer's copy-before-refuse "
     "mutant stands as an adversarial check that must trip the "
     "detector",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_refusal_precedes_every_access_and_allocation "
     "tests/test_0011_mutant_registry.py::"
     "test_the_copy_before_refuse_mutant_is_caught -q -p no:randomly"),
    # ---- 0011 external round 17 (2026-08-29) — both halves bound.
    ("0011", "external", 17, "0011-PROCESS-R17-1",
     "the copy-exception cleanup was a claim: deleting the except-block "
     "rmtree passed both R16 tests and the whole registry suite while a "
     "planted copytree failure leaked a real snapshot directory — the "
     "test asserted the exception propagates and never observed the "
     "allocated directory's fate",
     "failures injected independently into copy2 and copytree after "
     "allocation; the exact allocated directory (the mkdtemp wrapper's "
     "recorded return path, never a glob) required to not exist after "
     "the exception; the original exception propagated; the "
     "cleanup-deletion mutant stands with the leak required OBSERVED",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_copy_exception_cleanup_is_regression_bound "
     "tests/test_0011_mutant_registry.py::"
     "test_the_cleanup_deletion_mutant_is_caught -q -p no:randomly"),
    # ---- 0011 external round 18 (2026-08-29) — identity, not likeness.
    ("0011", "external", 18, "0011-PROCESS-R18-1",
     "original-exception propagation was asserted by type and message "
     "only — an inner handler swapping each copy exception for a fresh "
     "lookalike passed both R17 regressions and the whole registry "
     "suite while the caught exception was a different object than the "
     "one raised",
     "one sentinel exception object per copy2/copytree case, raised as "
     "that exact object and asserted by identity (caught.value is "
     "sentinel); the replacement mutant stands as a biting regression "
     "that only the identity probe kills; cleanup assertions and the "
     "cleanup-deletion mutant retained",
     "$PY -m pytest tests/test_0011_mutant_registry.py::"
     "test_copy_exception_cleanup_is_regression_bound "
     "tests/test_0011_mutant_registry.py::"
     "test_the_exception_replacement_mutant_is_caught -q -p no:randomly"),
    # ---- 0026 external round 1 (2026-08-29) — the major-amendment fold.
    ("0026", "external", 1, "0026-R1-1",
     "the directional detector confused proximity with authorship: a "
     "4-token lookback misclassified all five executed counterexamples "
     "(passive recipients as speakers, the post-verbal agent never "
     "consulted, embedded clauses inheriting the outer subject, "
     "she/he/they silently the user)",
     "the shipped lexicon is a directional grammar — agent governs, "
     "passive recipients inert, head-constructed subjects, ambiguous "
     "pronouns restrict with a counted conservative outcome; the five "
     "counterexamples ride verbatim in the hand matrix plus the "
     "generated grammar oracle; the CURRENT figures (lexicon version, "
     "cell count, rate) are DERIVED from fp_aggregate.json and "
     "validate_lexicon.py, never restated here (0026-PACKAGE-R2-1: this "
     "row once carried lex-3/32 cells/0.60% while the candidate shipped "
     "lex-6/53/0.70% — one source now)",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_reviewers_five_counterexamples_verbatim "
     "tests/test_0026_relay_lexicon.py::test_relay_lexicon_mutation_matrix "
     "-q -p no:randomly"),

    ("0026", "external", 1, "0026-R1-2",
     "the portable agreement carrier had no import-boundary contract: "
     "absent, forged, malformed, foreign-version and "
     "direction-disagreeing imported fields were all undefined, and no "
     "version or direction carrier existed despite §7's rule_version "
     "promise",
     "Edge.agreement is a structured record (markers + direction + "
     "lexicon version); §3d's import matrix is total — recomputation "
     "under the current lexicon governs every row, the incoming value "
     "is compared for a diagnostic counter and discarded, fail-closed "
     "both directions (V6a; implementation lands with acceptance like "
     "the rest of §3)",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_import_matrix_is_total_in_the_spec -q -p no:randomly"),

    ("0026", "external", 1, "0026-R1-3",
     "'consent-gated' was not a construction: 0015's consent "
     "text/schema-version/display-transition/record-gating requirements "
     "were absent, 0015 was not in Spec-Requires, and a conforming "
     "implementer could widen an already-consented payload",
     "telemetry consumption DEFERRED: the counters are local operator "
     "surface only, whitelisting is forbidden without a future "
     "0015-conformant amendment that adds 0015 to Spec-Requires and "
     "specifies the complete consent construction",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_telemetry_deferral_is_bound -q -p no:randomly"),

    ("0026", "external", 1, "0026-EVIDENCE-R1-1",
     "the acceptance measurement was self-asserted: nothing read "
     "fp_aggregate.json — fires 415 to 0, coverage to 0 and lexicon "
     "0026-lex-999 all passed header, identity, lexicon validator and "
     "the full spec gate; lex-1 did not ship despite the claim",
     "a closed validator (schema, types, internal consistency, "
     "shipped-lexicon pin) with the cache manifest cross-checked "
     "against the 0011/0025 subject aggregate; --aggregate is a real "
     "verify mode; the reviewer's three tamperings are the mutation "
     "matrix's first cells; whole-corpus figures labelled RECORDED "
     "ONLY; the lex-1 claim narrowed honestly",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_fp_aggregate_validator_matrix tests/test_0026_relay_lexicon.py::"
     "test_the_real_entry_point_verifies_and_refuses -q -p no:randomly"),

    ("0026", "external", 1, "0026-PACKAGE-R1-1",
     "candidate identity was contradictory yet verified VALID: the SENT "
     "row said v3 and v4 in one verdict; the v4 amendment postdated both "
     "internal reviews with no structured co-verification row",
     "the round-1 SENT row corrected in place with the correction "
     "visible; candidate revision is a structured SENT-row field bound "
     "to package_identity.py by the gate (disagreement refuses); the "
     "internal-first miss acknowledged, with the v5 fold queued for "
     "research's pre-seal red-team pass",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_structured_candidate_field_binds_to_the_package_record "
     "-q -p no:randomly"),
    # ---- 0026 external round 2 (2026-08-29) — every seam closed at code.
    ("0026", "external", 2, "0026-R2-1",
     "the grammar still used token proximity: a modifier's object read "
     "as the subject, a determiner-separated conjunct lost its "
     "co-source, and a curly apostrophe defeated tokenization — the "
     "hand cells stayed green because they omitted the shapes",
     "lex-7 head construction (forward clause reading, post-head "
     "modifiers inert, coordinated co-heads, Unicode normalization, "
     "relative pronouns as modifier-openers) plus the GENERATED "
     "grammar-oracle corpus with expectations derived from the "
     "constructions; §6a re-measured, bound improved",
     "$PY specs/evidence/0026/validate_lexicon.py"),
    ("0026", "external", 2, "0026-R2-2",
     "portability contradicted accepted contracts: ignore-unknown-key "
     "vs 0025's format bump, and always-recompute-and-floor vs 0005 "
     "P2's trust-field-faithful restore",
     "mode-split import boundary (restore verbatim incl. disclosure, "
     "recomputation diagnostic-only; default recomputes and floors) and "
     "a FORMAT_VERSION bump on export, with the full format x mode x "
     "field matrix in §3d",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_import_matrix_is_total_in_the_spec -q -p no:randomly"),
    ("0026", "external", 2, "0026-R2-3",
     "the telemetry deferral was not carrier-complete: §3c still said "
     "'consumed by telemetry from day one', §9 still named telemetry a "
     "consumer, and the deferral test inspected §3d alone",
     "both carriers swept with visible correction notes; the test scans "
     "EVERY carrier via a whole-file occurrence check that tolerates "
     "only quoted sweep notes",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_telemetry_deferral_is_bound -q -p no:randomly"),
    ("0026", "external", 2, "0026-EVIDENCE-R2-1",
     "the acceptance result was still not bound: fires tampered to "
     "2,000 (2.92%, over the 2% gate) verified as aggregate VALID, and "
     "the measurement doc retained stale figures beside the current "
     "result",
     "the gate is part of aggregate validity (over-gate refuses absent "
     "a separately validated adjudication artifact); the doc's shipped "
     "figures are mechanically compared to the aggregate at the verify "
     "entry point; a hand-typed 219-vs-220 coverage figure was refused "
     "by the binder during the sweep itself",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
    ("0026", "external", 2, "0026-PACKAGE-R2-1",
     "governance carriers disagreed: the closure row said lex-3/32 "
     "cells/0.60% while the candidate shipped lex-6/53/0.70%, and the "
     "v5 research pass existed only as SENT-row narration",
     "closure measurement figures derive from the aggregate and "
     "validator (one source); research's v5 pre-seal pass is recorded "
     "as structured internal rounds 3 and 4",
     "$PY specs/render_closure.py --check"),
    # ---- 0026 internal round 4 (2026-08-29) — research's pre-seal FN find.
    ("0026", "internal", 4, "0026-I4-1",
     "the verb list omitted `claimed` (the name of the relation 0024 "
     "quarantines) and high-frequency attribution verbs; §6a measures "
     "FP only and every matrix inbound cell used an in-list verb, so "
     "recall was unmeasured in two places at once",
     "the assertion/transmission/professional-judgment verb classes "
     "added with the professional-judgment ruling stated; nominal "
     "homographs narrowed by reading the fires; held recall cells and "
     "the claimed-removal mutant make completeness MEASURED; §8 scoped "
     "to the stated verb set; re-verified by research at 5ccccae",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_relay_lexicon_mutation_matrix -q -p no:randomly"),
    # ---- 0026 internal rounds 5-6 (2026-08-29) — research's round-2 pass.
    ("0026", "internal", 5, "0026-I5-1",
     "comitative quasi-coordinators (along with / together with / as "
     "well as) introduce a co-speaker the lexical coordinator set "
     "cannot see — three genuine relays silently unrestricted, the "
     "co-source class one syntactic layer up, and the generator's "
     "coordination axis could not catch what it did not generate",
     "lex-8: the closed comitative set joins the head scan as co-source "
     "introducers, the generator gains the comitative axis (measured, "
     "not patched), research's three misses ride verbatim as cells, "
     "the comitative-drop mutant stands, and the third-person "
     "self-possessive consistency fix rides",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_relay_lexicon_mutation_matrix -q -p no:randomly"),
    ("0026", "internal", 6, "0026-I6-1",
     "the new 2% gate claimed 'separately validated' and checked "
     "is_file(): an empty {} beside a 5%-fires aggregate produced "
     "'aggregate VALID' — the arc's signature defect (prose asserting "
     "more than the code) inside the fold's own binding machinery",
     "the adjudication artifact is read and validated — closed schema, "
     "labelled sample summing to size, non-blank verdict — and BOUND "
     "to the exact aggregate's lexicon version and fire count; "
     "empty-file and stale-binding refusals stand as tests and the "
     "legitimate labelled bypass is proven alive",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
    # ---- 0026 external round 3 (2026-08-29) — decisions, not narration.
    ("0026", "external", 3, "0026-R3-1",
     "the head grammar still laundered: or-disjunction was not "
     "coordination, and the self-possessive fix read 'my own doctor' — "
     "a possessed person — as the user; the oracle omitted both axes so "
     "every packaged test stayed green",
     "lex-9: `or` joins the coordinators; the self-possessive splits "
     "artifact-vs-entity over a closed artifact set in both the subject "
     "scan and the agent path; the oracle gains the disjunction axis "
     "and own-entity heads; re-measured identical",
     "$PY specs/evidence/0026/validate_lexicon.py"),
    ("0026", "external", 3, "0026-R3-2",
     "the import matrix was incomplete: AgreementRecord absent from "
     "§2c's untrusted-input table, and restore mode had no cell for a "
     "malformed new-format record — verbatim-and-typed is impossible "
     "for garbage",
     "the AgreementRecord row joins §2c; restore-malformed RAISES with "
     "nothing written (the R1-4 ruling on the restore path, validation "
     "ordered before any write); default-malformed stays "
     "treated-as-absent; the structural test binds the new cells",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_import_matrix_is_total_in_the_spec -q -p no:randomly"),
    ("0026", "external", 3, "0026-EVIDENCE-R3-1",
     "the adjudication path was decision-free: a verdict literally "
     "reading REJECT carried a 5.00% aggregate to 'aggregate VALID' — "
     "shape and blankness were checked, meaning never was, and nothing "
     "digest-bound the aggregate or sample",
     "the decision is executable: closed verdict enum, the adjudicated "
     "rate computed and required under the gate, a sample minimum, and "
     "digest binding to the exact aggregate bytes; REJECT, free-text, "
     "lying-accept, tiny-sample and wrong-digest all stand as refusals "
     "with the legitimate bypass proven alive",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
    ("0026", "external", 3, "0026-EVIDENCE-R3-2",
     "the candidate spec's §6a said 217 beside the aggregate's 220 — "
     "the binder covered the measurement doc and not the spec carrying "
     "the acceptance claim",
     "spec_problems binds the §6a headline rate and coverage figure to "
     "the aggregate at the verify entry point; the drift re-derived; "
     "the bite standing-tested",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_spec_binder_and_round_count_are_bound -q -p no:randomly"),
    ("0026", "external", 3, "0026-PACKAGE-R3-1",
     "the header and §9 said research ran two internal rounds beside a "
     "six-round structured ledger — prose frozen at the pre-external "
     "state",
     "§9 swept with the correction visible and the stated count bound "
     "to reviews.py by a standing test, so the prose cannot silently "
     "underclaim again",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_spec_binder_and_round_count_are_bound -q -p no:randomly"),
    ("0026", "external", 4, "0026-R4-1",
     "OWNERSHIP mistaken for AUTHORSHIP: lex-9's _SELF_ARTIFACTS read "
     "every owned artifact as user-authored — 'my own record reported a "
     "diagnosis of cancer' went outbound with no marker, though the "
     "record's producer can be a doctor or a bank; laundering, the FN "
     "direction, and the oracle tested only the intended senses",
     "lex-10 REMOVES the carve-out — no noun class carries an "
     "authorship inference; a possessed head restricts whoever "
     "possesses it, artifacts included ('my own notes' over-restricting "
     "is priced and reversible; laundering is not); the "
     "ownership-vs-authorship axis joins the oracle (all four reviewer "
     "cells) and the relapse is a standing behavioral mutant; "
     "re-measured 439/68,479 = 0.64% — identical, which is why the "
     "carve-out bought nothing and was pure risk",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_relay_lexicon_mutation_matrix -q -p no:randomly"),
    ("0026", "external", 4, "0026-R4-2",
     "the §2c AgreementRecord row said malformed-under-EITHER-mode "
     "raises while §3d said default-mode malformed recomputes, with the "
     "§2c columns displaced — and the matrix test checked substrings, "
     "not agreement between the carriers",
     "import_matrix.py is the ONE structured decision table now: both "
     "spec representations are GENERATED from it and byte-bound at the "
     "packaged test, so the carriers cannot diverge — there is nothing "
     "left to hand-edit into contradiction",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_spec_binder_and_round_count_are_bound -q -p no:randomly"),
    ("0026", "external", 4, "0026-EVIDENCE-R4-1",
     "the adjudication remained SELF-ASSERTED (the signature defect's "
     "sixth face, at the surface the fifth hunt cleared): "
     "true_positive=100/false_positive=-50 summed to size and passed; "
     "sample_sha256 was regex-checked, never opened or hashed; the "
     "decision used a point estimate",
     "schema 3 is RECORD-BOUND, data to data: the aggregate ships "
     "fire_digests (a content-free digest per fire), the labelled "
     "sample is an on-disk record-bound manifest (live only over-gate; "
     "a worked synthetic example ships) whose bytes are hashed against "
     "sample_sha256, membership and uniqueness are checked against the "
     "population, the counts are DERIVED by counting labels (no count "
     "carriers exist to lie), and accept requires bound x Wilson-95 "
     "UPPER confidence <= 2% — the reviewer's exact bypass and seven "
     "sibling cells are standing refusals, with the legitimate binding "
     "proven alive",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
    ("0026", "external", 4, "0026-EVIDENCE-R4-2",
     "the spec binder searched two substrings anywhere in the file — "
     "the §6a headline still said lex-8 over a lex-9 aggregate, and "
     "9,999/lex-999 mutations passed",
     "the §6a claim is a GENERATED block (render_spec_claim), byte-"
     "bound to the aggregate at the verify entry point and required to "
     "sit inside §6a — the reviewer's both mutations and an in-block "
     "figure edit are standing refusals; prose figure carriers swept "
     "into the block's custody",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_spec_binder_and_round_count_are_bound -q -p no:randomly"),
    ("0026", "external", 4, "0026-PACKAGE-R4-1",
     "round 3's verdict named the Internal-reviewers header AND §9; the "
     "fold swept only §9 — the header still listed rounds 1-2 and READY "
     "FOR EXTERNAL, and its test found 'six internal rounds' anywhere "
     "in the file",
     "the front-matter row is GENERATED from the ledger "
     "(reviews.internal_reviewers_row) and byte-bound; static readiness "
     "claims are refused outright — a generated row cannot be "
     "half-swept",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_spec_binder_and_round_count_are_bound -q -p no:randomly"),
    ("0026", "internal", 7, "0026-I7-1",
     "SAMPLE SELECTION voided the Wilson gate: the seed was recorded "
     "but never re-drawn or bound, so a host could ship any >=50 real "
     "fires, label the cleanest honestly (fp=0 -> UCB 0.071), and pass "
     "accept up to ~28% — Wilson-95 bounds a RANDOM sample; over a "
     "selected one it guarantees nothing",
     "the seed is CANONICAL (derived from the aggregate's own bytes — "
     "not choosable, closing seed-shopping too) and the validator "
     "RE-DRAWS random.Random(seed).sample over the sorted population, "
     "requiring the manifest to label EXACTLY the drawn set; --sample "
     "prints that draw; per the co-verify ADDENDUM the SIZE is "
     "canonical too (census up to the fixed 500 limit, else the limit; "
     "a census decides on the EXACT share, no Wilson needed) — "
     "size-shopping closed structurally, not just measured inert; "
     "hand-picked, non-canonical-seed, size-shopped and short-census "
     "attacks are standing refusals; the residual trust boundary is "
     "the per-fire LABELS, where it belongs",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
    ("0026", "internal", 7, "0026-I7-2",
     "byte-equality binders verified DRIFT, not renderer CORRECTNESS: "
     "an off-by-one renderer produces wrong-but-self-consistent bytes "
     "and re-render passes — the suite mutated shipped text and the "
     "aggregate, never a renderer",
     "every renderer has an INDEPENDENT oracle now: the test computes "
     "the figures straight from the artifact (never by re-invoking the "
     "renderer) and requires the rendering to carry them, both gate "
     "branches driven, the off-by-one renderer shown caught, and the "
     "cross-carrier malformed-mode facts asserted in both import-matrix "
     "renderings",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_renderers_agree_with_independent_oracles -q -p no:randomly"),
    ("0026", "external", 5, "0026-EVIDENCE-R5-1",
     "the 'canonical' seed hashed the ENTIRE host-produced aggregate, "
     "so a decision-irrelevant field was a NONCE: varying only "
     "suppressed_by_direction_only swung the draw from 167/500 FP "
     "(accepted) to 232/500 (refused) — seed-shopping survived, face "
     "seven of the selection-freedom class",
     "the seed basis LEAVES the aggregate: external and "
     "post-commitment, derived from the sealed archive's committed "
     "sha256 sidecar (schema 4: sealed_archive joins the record; name "
     "grammar checked before any path is built; the aggregate-archive "
     "pairing is the reviewer's extraction check, stated as protocol); "
     "nonce-invariance, missing-witness and traversal-name cells stand",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
    ("0026", "external", 5, "0026-R5-1",
     "render_2c_row hard-coded its text BESIDE the matrix while the "
     "spec claimed both carriers were generated from it — a mutated "
     "matrix regenerated §3d, §2c stayed contradictory, the binder "
     "returned clean (the name-vs-behavior class)",
     "every mode-dependent §2c clause is PROJECTED from the matrix "
     "rows' own operative text; the source-level mutation test drives "
     "a changed outcome through BOTH renderings and both binder halves",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_import_matrix_carriers_move_together -q -p no:randomly"),
    ("0026", "external", 5, "0026-PACKAGE-R5-1",
     "the spec and ledger said the adjudication manifest was SHIPPED "
     "and 'now EXISTS' while the archive contained neither artifact — "
     "no live adjudication can exist under-gate; the claim overstated "
     "a dormant path",
     "every carrier corrected VISIBLY (the construction ships; live "
     "artifacts materialize over-gate), and the worked clearly-"
     "synthetic end-to-end example ships in adjudication_example/ and "
     "is validated from disk by a standing test",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_worked_adjudication_example_validates_from_disk "
     "-q -p no:randomly"),
    ("0026", "external", 5, "0026-EVIDENCE-R5-2",
     "doc_problems hard-coded the 3,898 coverage denominator — a "
     "9,999 denominator (internally valid, spec block regenerated) "
     "validated clean everywhere while the doc still said 3,898",
     "the doc needle derives numerator, denominator AND percentage "
     "from the aggregate; the reviewer's denominator mutation is a "
     "standing cell",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
    ("0026", "external", 5, "0026-EVIDENCE-R5-3",
     "a correctly hash-bound manifest containing invalid UTF-8 raised "
     "an uncaught UnicodeDecodeError instead of a structured refusal",
     "both adjudication files return structured refusals on decode "
     "failure, with a standing cell for each",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
]
