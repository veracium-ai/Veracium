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
     # specs/0044 (T5): `prefers` is now `multi`, so the flag this command grepped for is gone. The finding was a
     # DISAGREEMENT between the §3 matrix and the code, so the command checks the agreement: 0025's annotation names
     # 0044's flip AND the shipped declaration is `multi` — it fails if either side drifts (research's R6). The text is
     # read ABOVE the closure ledger only: this row carries the command's own literals, so a search of the whole file
     # matched itself and could never fail (research's T5 stage-2 N2, measured open at T12's stage-1 read)
     "PYTHONPATH=src $PY -c \"import pathlib, sys; from veracium.schema import DEFAULT_RELATIONS as D; "
     "from veracium.registry import declared_arity; "
     "t = pathlib.Path('specs/0025-relation-vocabulary-enforcement.md').read_text().split('**Per-finding closure "
     "ledger')[0]; "
     "sys.exit(0 if declared_arity(D['prefers']) == 'multi' and 'from 0044' in t and 'arity=\\\"multi\\\"' in t "
     "else 1)\"  # the matrix row, its 0044 annotation and the shipped declaration agree"),
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
     "! grep -n '183,416' specs/0026-label-value-agreement.md "
     "| grep -v 'v1 carried' | grep -v '0026-I1-'"),

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
     "the seed basis is the NONCE-FREE PROJECTION (schema 5, completed "
     "at research's round-5 pre-seal pass — the interim archive-sidecar "
     "form rested on an unguaranteed non-precomputable first seal): "
     "derived from exactly the cross-anchored and decision-read fields "
     "(fire_digests + fires + manifest), each byte enumerated and "
     "justified; shopping the draw requires moving the measurement or "
     "tripping the anchor, so precomputability is harmless; "
     "nonce-invariance and population-sensitivity cells stand; the "
     "shipped corpus is a census and needs no seed at all "
     "[SUPERSEDED at round 6: EVIDENCE-R6-1 showed fire_digests itself "
     "is a host-produced identifier — sampling ENDED entirely; every "
     "adjudication is a census, schema 6]",
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
    ("0026", "external", 6, "0026-EVIDENCE-R6-1",
     "fire_digests remained a host-controlled seed nonce: digests are "
     "shape-checked, never recomputed from or bound to the cache, so "
     "varying ONE digest while holding the semantic population and "
     "labels fixed swung 159/500 FP accepted vs 234/500 refused — "
     "'decision-read' does not make a host-produced identifier "
     "non-choosable (face EIGHT of the selection class)",
     "sampling ENDS: every adjudication is a CENSUS (schema 6 — sample "
     "carries size only; manifest must label exactly the population; "
     "decision is the exact labelled share; draw/seed/size/Wilson all "
     "REMOVED — eight faces proved no sampling construction over a "
     "host-produced population survives); boundary cells stand incl. "
     "the exact-share bar from both sides; the digest-to-cache "
     "derivation is recorded protocol, reproducible with --cache",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
    ("0026", "external", 6, "0026-R6-1",
     "the restore-mode foreign-version cell was UNSPECIFIED: a "
     "well-typed record with current-valid markers and a foreign "
     "lexicon version under restore=True was unrecognised but not "
     "malformed — no stated outcome, and §2c's unrecognised cell "
     "stated only the default mode",
     "RULED verbatim: the version field exists to mark provenance, "
     "recomputation stays diagnostic-only, and refusing would break "
     "restore round-trips of old exports; the cell joins MATRIX (the "
     "one carrier) and both generated projections carry it",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_renderers_agree_with_independent_oracles -q -p no:randomly"),
    ("0026", "external", 6, "0026-PACKAGE-R6-1",
     "the half-swept-carrier class AGAIN: the Version row described "
     "the discarded archive-sidecar seed, the round-6 SENT row said "
     "v0 witness/schema 4 while the archive shipped schema 5 with the "
     "projection seed, and the example README claimed a generator the "
     "package did not ship",
     "closed STRUCTURALLY per the reviewer's fix: ADJUDICATION_SCHEMA "
     "is the one generated carrier of the CURRENT revision (validator, "
     "shipped generator, §6a claim block and tests all read it; "
     "current-summary prose derives or omits the number — HISTORICAL "
     "prose names the schema of its own round, a constraint round 7 "
     "made explicit); generate_example.py ships and the standing test "
     "requires byte-identical regeneration; the Version row and SENT "
     "row carry visible corrections",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_worked_adjudication_example_validates_from_disk "
     "-q -p no:randomly"),
    ("0026", "external", 6, "0026-EVIDENCE-R6-2",
     "the round-5 denominator fix divided unguarded: doc_problems on "
     "a zero-denominator aggregate raised ZeroDivisionError while "
     "render_spec_claim guarded the same derivation",
     "the doc needle uses the renderer's guarded derivation; the "
     "zero-denominator cell refuses structurally and stands",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
    ("0026", "internal", 8, "0026-I8-1",
     "the next half-swept carrier after the one-schema fix is PROSE "
     "THAT RESTATES MECHANISMS: _validate_adjudication's docstring "
     "still said 'Schema 3' and 'Wilson' two revisions after both were "
     "deleted — natural-language prose is the one carrier the "
     "generated-schema pattern cannot bind",
     "the docstring names the mechanism's carriers (the code below it, "
     "ADJUDICATION_SCHEMA, the spec's per-round history) instead of "
     "restating rules; the live-prose sweep ran with history sections "
     "standing as history; the drift is named IN the docstring as its "
     "own cautionary case",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_live_prose_names_carriers_not_mechanisms -q -p no:randomly"),
    ("0026", "external", 7, "0026-EVIDENCE-R7-1",
     "the live over-gate census could not be CREATED: measurement "
     "validated before emitting, and an over-2% result demanded the "
     "adjudication that the emitted aggregate and worklist exist to "
     "enable — a bootstrap deadlock (executed: fresh over-gate cache, "
     "exit 1, nothing emitted); the synthetic example never exercised "
     "the path because its generator hand-builds every artifact",
     "measurement validates in BOOTSTRAP mode: structural problems "
     "refuse, an over-gate rate is a distinct reported STATE (exit 3, "
     "aggregate + worklist emitted, acceptance never claimed); the "
     "verify entry keeps refusing; the adjudication is looked for "
     "beside the aggregate under verification; the shipped synthetic "
     "e2e_fixture drives every stage through the real main() as a "
     "standing regression",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_over_gate_pipeline_end_to_end -q -p no:randomly"),
    ("0026", "external", 7, "0026-EVIDENCE-R7-2",
     "independent label co-verification was neither judgeable nor "
     "bound: --sample truncated note/object so distinct fires "
     "displayed identically, the manifest is hashes-only so content "
     "cannot be recovered, and a host-only all-tp census returned [] "
     "with no co-verifier evidence required",
     "schema 7 BINDS both censuses (host + independent co-verifier, "
     "one shared reader); the decision runs on the fail-closed "
     "fp-UNION with disagreements counted; a missing co-verification "
     "refuses (host-only labels are not an adjudication); --worklist "
     "emits the full-content LOCAL-ONLY worklist keyed by fire digest",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_the_gate_and_the_doc_are_bound -q -p no:randomly"),
    ("0026", "external", 7, "0026-R7-1",
     "foreign-version MARKER validity was undefined: "
     "markers=['future_marker'] under lexicon=0026-lex-999/restore is "
     "well-typed, but the reader cannot know that lexicon's "
     "vocabulary — the foreign row said verbatim while the malformed "
     "row said out-of-grammar raises",
     "grammar membership is VERSION-SCOPED, mechanically: foreign-"
     "version markers validate as OPAQUE closed shapes (nonempty "
     "bounded strings, bounded count, closed types), never for "
     "membership; the malformed row's out-of-grammar rule applies "
     "only under the CURRENT version; the reviewer's exact case is "
     "named in the matrix cell and both projections carry the rule",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_renderers_agree_with_independent_oracles -q -p no:randomly"),
    ("0026", "external", 7, "0026-PACKAGE-R7-1",
     "the half-swept-carrier class persisted in OPERATIONAL prose: "
     "--sample help said 'draw N fires' (census flag), test comments "
     "said projection-seed and v0-witness, and summary prose "
     "hard-coded 'schema 6' while claiming prose never numbers "
     "revisions",
     "operational prose swept; the one-carrier claim CONSTRAINED "
     "precisely: current-summary carriers derive from "
     "ADJUDICATION_SCHEMA or omit the number, historical prose names "
     "the schema of its own round",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_live_prose_names_carriers_not_mechanisms -q -p no:randomly"),
    ("0026", "external", 8, "0026-EVIDENCE-R8-1",
     "census records were not unambiguous: json.loads keeps the LAST "
     "duplicate member, so 'label:fp,label:tp' passed as tp — hash "
     "binding authenticated ambiguous bytes without resolving meaning, "
     "and both censuses shared the reader so the fp-union could be "
     "reduced (the 0011 EVIDENCE-R9-1 class refound in new code)",
     "duplicate JSON members REFUSE at parse via _strict_json (an "
     "object-pairs hook) at every evidence boundary — both manifests "
     "and the adjudication record — with duplicate-label and "
     "duplicate-fire regressions standing",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_census_manifests_refuse_ambiguous_records -q -p no:randomly"),
    ("0026", "external", 8, "0026-R8-2",
     "the foreign-version shape lacked an EXECUTABLE definition — "
     "'nonempty bounded strings' and 'bounded count' with no bounds "
     "let conforming implementations accept different inputs",
     "AGREEMENT_SHAPE is data with the running reference validator "
     "agreement_shape_problems (closed keys; a bounded marker array; "
     "duplicates refuse; the closed direction enum; a bounded lexicon "
     "version under a closed pattern — the EXACT numbers live only in "
     "the generated §3d shape block and moved with the I10-1 "
     "measurement; this row is version-neutral per PACKAGE-R10-1, "
     "which caught it restating the pre-measurement bound), rendered "
     "byte-bound into §3d; every bound driven at the limit and one "
     "beyond by a standing test",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_agreement_shape_bounds_at_the_limit_and_beyond "
     "-q -p no:randomly"),
    ("0026", "external", 8, "0026-EVIDENCE-R8-3",
     "bootstrap output paths could overwrite one another or the input: "
     "--emit-aggregate X --worklist X destroyed the aggregate, either "
     "output could name --cache, and exit 3 was reachable without both "
     "artifacts retained",
     "every path resolves and cross-checks BEFORE any write; aliases "
     "(relative or absolute) and output-names-input refuse with the "
     "source proven preserved; the good path retains both artifacts",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_bootstrap_paths_cannot_alias_and_worklists_stay_local "
     "-q -p no:randomly"),
    ("0026", "external", 8, "0026-PRIVACY-R8-4",
     "LOCAL-ONLY was documentation: --worklist accepted any path with "
     "ordinary permissions, and .gitignore covered fp_worklist* while "
     "the packaged test wrote worklist.jsonl",
     "mechanically enforced: a worklist path inside the package tree "
     "refuses before any write, the file is written mode 0600, and a "
     "standing package sweep refuses ANY .jsonl under specs/ carrying "
     "the worklist line shape — rename-proof",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_no_full_content_worklist_ships_in_the_package "
     "-q -p no:randomly"),
    ("0026", "internal", 10, "0026-I10-1",
     "the ninth face: the R8-1 fold routed the manifests through the "
     "strict decoder but left plain json.loads at THREE evidence "
     "boundaries — aggregate verify, peer cross-anchor, and the CACHE "
     "read whose raw-vs-parsed split (raw-sha anchor vs last-wins "
     "enumeration) was genuinely exploitable; vigilance failed twice "
     "(11-day class recurrence + three missed sites in the closing "
     "fold). Secondary: the alias guard missed hardlinks; "
     "markers_max_count was taste not measurement",
     "every evidence-boundary read routes through _strict_json (a "
     "duplicate-key cache row counts unparseable, never last-wins); "
     "the structural gate makes the unsafe form UNREACHABLE — a "
     "standing test refuses plain json.load(s) under specs/evidence/ "
     "outside a reasoned allowlist (legacy lines capped at their "
     "current counts, new files at zero); the alias guard compares "
     "(st_dev, st_ino) so hardlinks refuse; the shape bounds carry "
     "their MEASURED basis (max distinct markers per record = 2 over "
     "the full cache -> count bound 8 = measured x4; longest member "
     "16 chars -> length bound 64 = x4)",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_no_plain_json_load_at_evidence_boundaries -q -p no:randomly"),
    ("0026", "internal", 11, "0026-I11-1",
     "the gate's own allowlist defeated it for the file it protects: "
     "0026's cap was 3 while the matched count was 0 (regex miscount — "
     "the impl line skipped, the docstrings never matched), leaving "
     "three slots of headroom for reintroduced plain json.loads",
     "the gate is EXACT-MATCH (a count above OR below its pin trips — "
     "self-catching, no headroom anywhere) and AST-BASED (calls "
     "resolved through import aliases incl. bare `from json import "
     "loads`; safety judged per-call by the object_pairs_hook keyword, "
     "not per-line) — the AST recount immediately corrected one legacy "
     "pin the regex had undercounted, proving the rebuild on its first "
     "run; 0026's own pin is 0; the co-verify's tenth-face hardening "
     "taken same-day — only KNOWN-STRICT hooks by name count as safe "
     "(object_pairs_hook=dict counts as plain)",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_no_plain_json_load_at_evidence_boundaries -q -p no:randomly"),
    ("0026", "external", 9, "0026-R9-1",
     "the AgreementRecord carriers DISAGREED in the machinery built to "
     "prevent it: §3d's stored direction enum is "
     "inbound|ambiguous|user_source while AGREEMENT_SHAPE said "
     "inbound|outbound|ambiguous (the lexicon's internal reading "
     "names); markers=[] was accepted against V2's no-markers-no-record "
     "rule; and §18 plus the round-9 SENT row restated 16 markers "
     "beside the executable 8",
     "ONE canonical enum: the shape matches §3d exactly (user_source "
     "legal — it IS §3c's demotion-direction record; 'outbound' "
     "refuses as a stored value with the lexicon-mapping stated; "
     "markers minimum 1); the three named inputs are independent "
     "standing cells; both restatements carry visible corrections and "
     "live prose no longer carries the numbers",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_agreement_shape_bounds_at_the_limit_and_beyond "
     "-q -p no:randomly"),
    ("0026", "external", 9, "0026-PRIVACY-R9-2",
     "the local-only closure covered only FRESH files: O_TRUNC applies "
     "0600 only on create, so a pre-existing 0644 worklist kept 0644 "
     "while the program reported 0600; and the package sweep read only "
     "the first line of *.jsonl, contradicting the rename-proof claim",
     "fchmod is explicit before any content lands (pre-existing-file "
     "regression standing); the sweep reads EVERY line of every "
     "decodable file under specs/ whatever the suffix or size, with "
     "undecodable worklist-shaped bytes flagged at the byte level "
     "(the round-10 size-cap exclusion removed)",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_bootstrap_paths_cannot_alias_and_worklists_stay_local "
     "tests/test_0026_relay_lexicon.py::"
     "test_no_full_content_worklist_ships_in_the_package "
     "-q -p no:randomly"),
    ("0026", "external", 9, "0026-EVIDENCE-R9-3",
     "the duplicate-cache regression was NON-PROBATIVE: it passed on "
     "returncode != 0, which the peer mismatch it introduced already "
     "guaranteed — nothing proved the row was counted unparseable",
     "the regression builds a MATCHING peer for the modified cache, "
     "requires the bootstrap state (exit 3), and asserts the exact "
     "'1 unparseable' count — proving the row was COUNTED, not that "
     "something failed",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_duplicate_key_cache_rows_count_unparseable -q -p no:randomly"),
    ("0026", "external", 10, "0026-PACKAGE-R10-1",
     "numeric carrier cleanup was incomplete: the R8-2 closure row "
     "still recorded 'at most 16 markers' (never re-swept after the "
     "I10-1 measurement moved the bound to 8) and the boundary test's "
     "diagnostic literal said '17 markers must refuse' beside a "
     "derived case — contradicting v13's no-restatement claim",
     "the closure row is version-neutral (exact numbers live only in "
     "the generated §3d block, and the row says so) and the "
     "diagnostic derives from markers_max_count",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_agreement_shape_bounds_at_the_limit_and_beyond "
     "-q -p no:randomly"),
    ("0026", "external", 10, "0026-PRIVACY-R10-2",
     "the broadened sweep silently skipped files over 8,000,000 bytes "
     "— an undocumented exclusion a large worklist-shaped file "
     "evades; and the R9-2 closure command invoked only the file-mode "
     "regression, not the package-sweep half",
     "the size cap is REMOVED — total scope at bounded memory (text "
     "streamed line by line; undecodable files byte-scanned in 1MB "
     "chunks with an overlap window); the R9-2 closure evidence runs "
     "both halves",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_no_full_content_worklist_ships_in_the_package "
     "-q -p no:randomly"),
    ("0026", "internal", 13, "0026-I13-1",
     "the §6 V-invariant check column was not S-list-honest: six of "
     "seven named tests did not exist — V4's name had drifted from "
     "the real test, and V2/V3/V5/V6/V6a/V7 are implementation-time "
     "obligations (0026 is a draft; no agreement mechanism exists in "
     "src/) presented as standing checks; the S-list completeness "
     "check is exactly what the acceptance reviewer runs",
     "every §6 row is marked CURRENT vs IMPLEMENTATION-TIME "
     "(graduates with src/), V4's name corrected to the real test, "
     "and the standing guard binds both halves: every test name cited "
     "in the spec's live zone must resolve to a real function (marked "
     "obligations exempt), and the shape-bound digits may appear in "
     "marker/character context only inside generated blocks — the "
     "restatement class's five bitten carriers under one guard",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_current_v_table_tests_resolve_and_no_live_restatement "
     "-q -p no:randomly"),
    ("0026", "external", 11, "0026-R11-1",
     "six §6 invariants (V2/V3/V5/V6/V6a/V7) still lacked EXECUTABLE "
     "checks: accurately labeled implementation-time, but the "
     "resolution guard exempted those rows, so the suite passed with "
     "none of the six named tests existing — PROCESS.md makes an "
     "invariant without an executable check a hard gate",
     "the six named tests EXIST as standing ABSENCE-AWARE checks: in "
     "the draft state each mechanically proves its invariant vacuous "
     "(no agreement machinery in src/ — the sweep flips when "
     "implementation begins) and the behavioral cells against the "
     "spec'd API activate automatically at graduation (V6a fails "
     "loudly then until the matrix drive is written, by design); the "
     "exemption is removed — every cited name resolves",
     "$PY -m pytest tests/test_0026_relay_lexicon.py::"
     "test_absence_is_no_evidence "
     "tests/test_0026_relay_lexicon.py::"
     "test_no_markers_is_byte_identical "
     "tests/test_0026_relay_lexicon.py::"
     "test_current_v_table_tests_resolve_and_no_live_restatement "
     "-q -p no:randomly"),
    # ---- 0031 external rounds 1-15 (2026-08-31 → 2026-09-04) — one row per finding; evidence = the permanent test that pins the closure, or the fold commit for text-only closures ----
    ("0031", "external", 1, '0031-R1-1',
     'V-NO-RAISE was stated on the whole trust model and checked on one coordinate',
     'v6 §2c/§2c-i: the four consumers enumerated, the lattice statement (later four obligations, v8)',
     'git show b006c3e -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 1, '0031-R1-2',
     '`direct` restored model-controlled authorship as an elevation route (author defaulted to the top of the ladder)',
     "v6 §4a F2: author loses its default, takes the capability's baseline, restrict-only; direct attests the authorship axis (§3a)",
     'git show b006c3e -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 1, '0031-R1-3',
     'the central capability was not actually pinned to a carrier',
     'v6 §4a: build_server(capability=) keyword-only, VERACIUM_MCP_CAPABILITY env mapping, tool-schema exclusion by construction',
     'git show b006c3e -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 1, '0031-R1-4',
     'the proposal DDL did not enforce its stated contract or support reversal',
     "v6 §4b-ii DDL pinned + §4c-iii reversal; the reviewer's six rows R1-R6 executed from the spec's own CREATE TABLE blocks",
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_proposal_cell tests/test_0031_proposal_ddl.py::test_resolution_cell -q -p no:randomly'),
    ("0031", "external", 1, '0031-R1-5',
     'the resolution API contradicted the required correction friction and lacked an atomic schedule',
     'v6 §4c: Store.apply_proposal as the transaction-owning primitive; the three in-transaction constructions',
     'git show b006c3e -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 1, '0031-R1-6',
     'proposal attribution and review evidence were not yet buildable',
     'v6 §6a + the shipped acceptance corpus; the DDL executed at test time from the spec',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_proposal_cell -q -p no:randomly'),
    ("0031", "external", 2, '0031-R2-1',
     'the four-coordinate lattice proof was overstated (scope_fingerprint is an equality digest, not ordered)',
     'v8 §2c-i: four separate obligations — descend-only disclosure/authority, restrict-only shaping, preserve-or-invalidate fingerprint',
     'git show 01268cd -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 2, '0031-R2-2',
     'the `direct` bridge conflicted with the one-declaration contract (_resolve_context refuses context+derived_from)',
     'v8 §3a: the mapping pinned — direct+absent -> direct(); direct+supplied -> derived(X); never both',
     'git show 01268cd -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 2, '0031-R2-3',
     'the process-level identity boundary was asserted but not enforced',
     'v8: user_id off the Phase A/B tool schemas (absence-by-schema); the propose signature pinned; Q2 reconciled with the dropped turn',
     'git show 01268cd -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 2, '0031-R2-4',
     'the atomic acceptance schedule lacked a composable store primitive (Memory.correct commits twice)',
     'v8 §4c: Store.apply_proposal owns the transaction; the additive in-transaction variant of apply_supersession_plan',
     'git show 01268cd -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 2, '0031-R2-5',
     'resolution history was not attributable or relationally bound',
     'v8 §4b-ii: resolver column, the FK with the PRAGMA foreign_keys=ON obligation, the hex digest CHECK; N3/N4 cells',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_resolution_cell tests/test_0031_proposal_ddl.py::test_fk_is_inert_without_the_pragma__control -q -p no:randomly'),
    ("0031", "external", 2, '0031-R2-6',
     'the requested review evidence was still absent',
     'v8 §6a: the corpus ships in the package; DDL evidence executed from the spec',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_proposal_cell -q -p no:randomly'),
    ("0031", "external", 3, '0031-R3-1',
     'the four-obligation correction was incomplete (one carrier reached, the matrix and V-NO-RAISE row missed)',
     'v9: all residual descent language removed; V-NO-RAISE replaced by four per-obligation invariants',
     'git show fc8b39a -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 3, '0031-R3-2',
     "the unavailable-turn contradiction remained in Q2's row",
     'v9: Q2 names exactly what the resolver sees — stored content, kind, claim, proposer, unresolved evidence_ref',
     'git show fc8b39a -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 3, '0031-R3-3',
     'proposal creation did not define how its target digest is minted',
     'v9 §4b: the STORE-MINTED digest under the writer lock; target_state_digest never a tool argument',
     'git show fc8b39a -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 3, '0031-R3-4',
     'the atomic mutation remained underspecified',
     'v9 §4c: Store.apply_proposal signature + input contract; the three constructions name their plan machinery',
     'git show fc8b39a -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 3, '0031-R3-5',
     'resolution history was not fully bound (applied_txn divergence, seq allocation)',
     'v9: applied_txn equality from one local in one commit; seq domain in DDL, MAX(seq)+1 under the lock; the gate strengthened',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_resolution_cell -q -p no:randomly'),
    ("0031", "external", 3, '0031-R3-6',
     'the DDL and foreign-key evidence overstated enforcement (BLOB-blind CHECKs; FK proven on the wrong path)',
     'v9: the type-affinity rule (typeof on every length/GLOB/BETWEEN predicate; N5/N8 BLOB cells); FK evidence against the pinned store opening sequence',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_proposal_cell tests/test_0031_proposal_ddl.py::test_fk_holds_under_the_pinned_store_opening_sequence tests/test_0031_proposal_ddl.py::test_todays_store_lacks_the_pragma__the_obligation_is_real -q -p no:randomly'),
    ("0031", "external", 3, '0031-R3-7',
     'the evidence corpus was not self-contained',
     'v9 §6a: full sha256 citations, corpus/ with the harness package, rerun.sh as the one archive-local command',
     'git show fc8b39a -- specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 4, '0031-R4-1',
     'the correction carrier was still undefined',
     'v10 §4b: the TYPED payload (object/note/effective_date), duplicate-refusing decoder, parse authority at both sites, json_valid in DDL',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_proposal_cell -q -p no:randomly'),
    ("0031", "external", 4, '0031-R4-2',
     'the resolution-history gate did not exist (a phantom citation in the ownership table)',
     'v10 §6a: V-RESOLUTION-LEDGER as fenced SQL, extracted at test time; the seven-history battery',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_resolution_ledger_gate -q -p no:randomly'),
    ("0031", "external", 4, '0031-R4-3',
     'the SQLite type rule did not cover affinity coercion',
     'v10: DDL owns stored-representation domains (claims narrowed to non-coercible); the binding preamble owns types; honest-limit cells',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_coercible_text_txn_is_ddl_invisible__honest_limit tests/test_0031_proposal_ddl.py::test_numeric_resolver_coerces_to_text__honest_limit tests/test_0031_proposal_ddl.py::test_ddl_accepts_what_the_store_parse_must_refuse__honest_limit -q -p no:randomly'),
    ("0031", "external", 4, '0031-R4-4',
     'the foreign-key sentinel could not detect partial enablement',
     'v10 §4b-ii: the connection-path INVENTORY with its classifier criterion; the central connection factory rider; the inventory-completeness sweep',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_connection_path_inventory_is_complete -q -p no:randomly'),
    ("0031", "external", 4, '0031-R4-5',
     'the retired umbrella invariant (V-NO-RAISE) remained live at §2c-ii',
     'v10: the symbol retirement swept by name, uses vs mentions classified; registered in specs/withdrawn_phrases.py',
     'git show 97783d3 -- specs/withdrawn_phrases.py specs/0031-agent-facing-trust-surface.md'),
    ("0031", "external", 4, '0031-R4-6',
     'the corpus was source-contained, not execution-contained',
     'v10 §6a + corpus/rerun.sh: the claim narrowed to source-contained, receipt versions pinned, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
     'git show 97783d3 -- specs/0031-agent-facing-trust-surface.md  # the narrowed claim; the corpus itself ships in every review package (corpus/rerun.sh asserts import-origin inside it), not in this tree'),
    ("0031", "external", 5, '0031-R5-1',
     'the resolution-ledger gate was six true negatives whose conjunction was not totality (accept+refuse fired none)',
     'v11 §6a: clause 7 audits the complete state/action grammar; the NULL trap COALESCEd throughout',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_resolution_ledger_gate -q -p no:randomly'),
    ("0031", "external", 5, '0031-R5-2',
     'the connection-path inventory still missed the original `__import__` mutant said to have hardened it',
     'v11: dynamic loading of sqlite3 prohibited (literal or unresolvable arg); the original mutant permanent',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_dynamic_sqlite_acquisition_is_refused__controls -q -p no:randomly'),
    ("0031", "external", 5, '0031-R5-3',
     'the binding-type preamble accepted strings SQLite cannot bind (a lone surrogate)',
     'v11: the text domain DEFINED (valid UTF-8) and validated in the preamble; Phase-B ownership split stated',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_surrogate_text_raises_through_the_driver__mechanism -q -p no:randomly'),
    ("0031", "external", 6, '0031-R6-1',
     'a captured `opener = sqlite3.connect` evaded the census (the sixth rung)',
     'v12: refusal by parenthood — an uncalled sqlite3.connect attribute refuses; a bare sqlite3 name refuses',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_captured_connect_reference_is_refused__controls -q -p no:randomly'),
    ("0031", "external", 7, '0031-R7-1',
     '`sqlite3.Connection(path)` and `sqlite3.dbapi2.connect` bypassed the census (the seventh rung)',
     'v13: the POSITIVE SURFACE — one blessed opener, Connection annotation-only, ALLOWED_ATTRS-or-refuse, submodules refused, the runtime opener matrix',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_connection_constructors_and_submodules_refuse__controls tests/test_0031_proposal_ddl.py::test_every_runtime_opener_spelling_is_refused__matrix -q -p no:randomly'),
    ("0031", "external", 8, '0031-R8-1',
     "an evaluated annotation `sqlite3.Connection(':memory:')` acquired at def time (the eighth rung)",
     'v14: calls processed before any exemption; the exemption admits only non-executing type-reference structure',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_evaluated_annotation_acquisition_is_refused__controls -q -p no:randomly'),
    ("0031", "external", 9, '0031-R9-1',
     'string annotations bypassed the inventory (the ninth rung)',
     'v15: strings in annotation position parsed and the surface applied recursively; unparseable/assembled fail closed',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_string_annotations_apply_the_surface_recursively__controls -q -p no:randomly'),
    ("0031", "external", 10, '0031-R10-1',
     'the string-annotation check was gated by spelling, not acquisition capability (`_sqlite3`; the tenth rung)',
     'v16: PROTECTED_MODULES, provenance-tracked aliases, entry unconditional, the widened fail-closed floor; TypeAlias positions (red-team)',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_acquisition_is_classified_by_provenance_not_spelling__controls tests/test_0031_proposal_ddl.py::test_type_alias_values_are_annotation_positions__controls -q -p no:randomly'),
    ("0031", "external", 11, '0031-R11-1',
     'a standard alternate module-access form (sys.modules) acquired uncounted (the eleventh rung)',
     'v17: the enumerated, mechanically checked forms inventory with a conservative floor; the claim rescoped to the enumeration',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_capability_discovery_form tests/test_0031_proposal_ddl.py::test_capability_discovery_inventory_is_mechanically_checked -q -p no:randomly'),
    ("0031", "external", 12, '0031-R12-1',
     'namespace mappings (globals/locals/vars) were absent from the inventory (the twelfth rung)',
     'v18: CAPABILITY_DISCOVERY_FORMS (thirteen forms incl. namespace-mappings, frame-introspection, captured-primitive, accessor-constructors); both-directions probes per form',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_capability_discovery_form tests/test_0031_proposal_ddl.py::test_capability_discovery_inventory_is_mechanically_checked -q -p no:randomly'),
    ("0031", "external", 13, '0031-R13-1',
     'the `self`/`cls` exemption assumed a runtime type Python does not guarantee (the thirteenth rung)',
     'v19: the exemption deleted, the one project site rewritten to literal access; cls refused separately; vars(x) refused; sibling exemptions pinned by executed properties',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_receiver_names_do_not_determine_runtime_type__control tests/test_0031_proposal_ddl.py::test_the_legitimate_project_site_is_literal_and_clean__control tests/test_0031_proposal_ddl.py::test_sibling_exemptions_rest_on_documented_semantics__controls -q -p no:randomly'),
    ("0031", "external", 14, '0031-R14-1',
     'a literal attribute name did not establish a safe receiver (the fourteenth rung)',
     'v20: GETATTR_ALLOWANCES by (file, receiver, attr) with category, consumption, count; the escape rules; swept both directions',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_identical_literal_names_differ_by_receiver__control tests/test_0031_proposal_ddl.py::test_getattr_allowances_sweep_both_directions -q -p no:randomly'),
    ("0031", "external", 15, '0031-R15-1',
     'the dotted-access boundary was syntactic rather than enforceable (the fifteenth rung)',
     'v21 (respun at the round-16 pre-dispatch refusal): one classifier over both forms, five classes, object dataflow outside the claim for both, the partition asserted by equality and bound to the spec',
     '$PY -m pytest tests/test_0031_proposal_ddl.py::test_both_attribute_forms_share_one_classification tests/test_0031_proposal_ddl.py::test_the_one_justified_difference_is_the_non_literal_name__control tests/test_0031_proposal_ddl.py::test_shared_attribute_inventory_over_src tests/test_0031_proposal_ddl.py::test_spec_quotes_the_measured_partition_exactly -q -p no:randomly'),

    # ---- 0030 — the joint arc's ONE ledger (0029 + 0030 + the seam), 57 findings over
    # rounds 1-17; round 18 accepted. Target per finding in TARGETS below. Summaries quote
    # the verbatim verdicts; `closed in` names the fold commit; evidence is a whole pytest
    # node where a mechanism exists, `git show <fold> -- <spec>` where the closure is text
    # (13 rows, enumerated per finding in the P4 gate). Written 2026-09-04.
    ("0030", "external", 1, '0030-R1-1',
     '[F1] The pair cannot reconstruct `EdgeStateAt(known_as_of)` — same-ID mutations overwrite the only edge row; a digest cannot recover prior values',
     'Owner ruled option (a) RECONSTRUCTABLE STATE: every 0029 event carries the edge\'s FULL canonical serialization so EdgeStateAt(K) is a single lookup (0029 v3 §4a/§4b-ii, V-RECON; manifest S1); the change-detection narrowing was refused. — fold 9ad7fba',
     'git show 9ad7fba -- specs/0029-transaction-time-carrier.md specs/0030-time-relative-classification.md'),
    ("0030", "external", 1, '0030-R1-2',
     '[F2] Current trust and historical knowledge require two separate states — a single `Edge` parameter cannot represent state-at-K + current cap + current visibility',
     '0030 v6/v7 introduced the two-state classifier classify_as_of(snapshot, current, T, now, view) -> Result{status, held_at_K, flags} with the reason×cutoff matrix (§4a-ii, V-TWO-STATE; current caps subtract only, current scope always governs); 9ad7fba states the seam from the 0029 side (0029 reconstructs belief held at K; revocation/scope are consumer-applied outer caps). — fold e0b3a2d',
     'git show e0b3a2d -- specs/0029-transaction-time-carrier.md specs/0030-time-relative-classification.md'),
    ("0030", "external", 1, '0030-R1-3',
     '[F3] 0029\'s event cuts can split an atomic mutation — a cutoff between event rows selects a state that never existed; shared `recorded_at` has no sequence component',
     '0029 v3 §4a: per-user `txn` batch id allocated per event-emitting write transaction, `seq` the ordering authority, whole-batch reads, `recorded_at` demoted to telemetry (V-BATCH). — fold 9ad7fba',
     'git show 9ad7fba -- specs/0029-transaction-time-carrier.md'),
    ("0030", "external", 1, '0030-R1-4',
     '[F4] V-TOTAL misses a shipped classification-relevant mutation — four raw `UPDATE edges` sites not three; recompute changes `valid_from` invisibly to the 0027 digest',
     '0029 v3 §4b: the trigger basis re-based from the 0027 semantic-text digest to the FULL-STATE serialization and the fourth site `_recompute_edge_row` named (later cited at its UPDATE statement sqlite.py:334 in v4, 2a54fb4) (V-TOTAL). — fold 9ad7fba',
     'git show 9ad7fba -- specs/0029-transaction-time-carrier.md'),
    ("0030", "external", 1, '0030-R1-5',
     '[F5] 0029\'s event schema remains unresolved — one `content_digest` column vs old/new digests; header still v1, §4b/§10 still defer the choice',
     '0029 v3 §4a: the DDL pinned exactly with no deferred choices — full-state snapshots dissolve the old/new-digest question. — fold 9ad7fba',
     'git show 9ad7fba -- specs/0029-transaction-time-carrier.md'),
    ("0030", "external", 1, '0030-R1-6',
     '[F6] 0030\'s exact classifier still does not implement its input contract — unhashable reason raises; UTC normalization absent; unknown string MALFORMED vs FENCED',
     '0030 v6: type and UTC normalization placed before every membership/comparison operation and the unknown string reason ruled FENCED with the default lookup genuinely reachable (V-NORMALIZE, V-MALFORMED, V-FAILCLOSED); the dev both-check B-1/B-2 in v7 extended the same discipline to the `current` leg. — fold e0b3a2d',
     'git show e0b3a2d -- specs/0030-time-relative-classification.md'),
    ("0030", "external", 1, '0030-R1-7',
     '[F7] 0030 evaluates hidden records before applying visibility — a hidden malformed record returns MALFORMED, not SCOPE_HIDDEN',
     '0030 v6: visibility made the OUTERMOST gate — a hidden record returns SCOPE_HIDDEN only, held_at_K withheld too (V-SCOPE; §6a hidden+malformed fixture = joint scenario 8). — fold e0b3a2d',
     'git show e0b3a2d -- specs/0030-time-relative-classification.md'),
    ("0030", "external", 1, '0030-R1-8',
     '[F8] 0030\'s prior fixes were not swept through every carrier — six remnants (§3 shape(), §9, §4b absorbed_duplicate, §7 \'only narrow\', v4/v5 header, §4c)',
     '0030 v6: all six carrier remnants swept; 9ad7fba applied the same version-header discipline to 0029 (its closure table lists this as \'F8 (0029 half)\'), and 5d76b77 closed a same-class recurrence in 0029 v4\'s Version cell. — fold e0b3a2d',
     'git show e0b3a2d -- specs/0030-time-relative-classification.md'),
    ("0030", "external", 2, '0030-R2-1',
     '[F1] migrated edges still lack reconstructable epoch state (no baseline event at migration; pre-first-mutation state permanently unavailable)',
     '0029 v5 §4e: EPOCH BASELINE snapshots — the migration journals every pre-existing edge AS FOUND in one `baseline` batch per user (the user\'s epoch txn); baselines + epoch row + schema stamp commit in ONE transaction (V-BASELINE; §6a scenario 9). — fold eaefd8b',
     'git show eaefd8b -- specs/0029-transaction-time-carrier.md'),
    ("0030", "external", 2, '0030-R2-2',
     '[F2] `current: Edge` is not a complete current restriction cap (an already-inactive `superseded` edge gets no retirement rewrite; reason reads groundable)',
     '0030 v8/v9/v11: the current source-restriction cap reads a DEDICATED standing-state input derived from the sweep\'s ONE computation (`statement["retire"]`, corrected from `affected` by cross-check X-1), never `current.invalidation_reason` (§4b-iii, V-TRUST-INPUT; §6a restrict→lift cell). — fold 7b929b5',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_typed_membership_restricts__bare_id_is_the_control -q -p no:randomly'),
    ("0030", "external", 2, '0030-R2-3',
     '[F3] current valid-time and semantic changes do not subtract (snapshot [Jan,∞) superseded Feb, T in Mar grounds; same-ID content change still grounds)',
     '0030 v8: the current leg SUBTRACTS on valid-time (current interval must contain T) and semantic identity (same-id digest change fences the old snapshot), with `note` kept in the digest basis by X-5 (V-SUBTRACT; §6a scenarios 11–12). — fold 7b929b5',
     'git show 7b929b5 -- specs/0030-time-relative-classification.md'),
    ("0030", "external", 2, '0030-R2-4',
     '[F4] `snapshot` and `current` are not identity-bound (a snapshot for A paired with visible unrestricted current B borrows B\'s scope and cap)',
     '0030 v8 rule 0: identity binding of snapshot/current/envelope (and the view leg, X-3) BEFORE visibility, placed ahead of the privacy gate because a binding failure reveals only what the caller supplied (V-BIND; §6a scenario 13, three fixtures); 0029 v6 (b05a58c, C-2) made the carrier identity ROW-sourced so binding is parse-independent. — fold 7b929b5',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_six_leg_binding__with_its_control -q -p no:randomly'),
    ("0030", "external", 2, '0030-R2-5',
     '[F5] malformed states cannot traverse the 0029→0030 interface (0029 returns `Edge | None`; Pydantic rejects the values 0030 promises to classify)',
     '0029 v5 §4b-ii: `edge_state_at` returns a RAW carrier (`RawEdgeState`, payload verbatim TEXT, V-VERBATIM) and 0030 v8/v12 (7b929b5) owns parse AND validation (V-RAW, V-PARSE; C-1 parse ownership folded in b05a58c) — seam S4. — fold eaefd8b',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_unparseable_text_refuses -q -p no:randomly'),
    ("0030", "external", 2, '0030-R2-6',
     '[F6] the epoch and transaction cursor domains remain incomplete (integer `until_txn` vs instant epoch; instance-local lock insufficient across two stores)',
     '0029 v5 §4e/§2c: the epoch became a TXN value (`until_txn < epoch_txn(user)`, one integer domain, 0 for fully-journaled users); txn/seq allocation moved to DATABASE-level serialization with `recorded_at` minted once per batch (V-EPOCH, V-TXN-ALLOC; §6a scenario 15) — the locking schedule itself was left open and closed at round 3 (F4). — fold eaefd8b',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_immediate_schedule_serializes__deferred_is_the_control -q -p no:randomly'),
    ("0030", "external", 2, '0030-R2-7',
     '[F7] datetime normalization is not total (`as_utc(None) -> None` lets T=None, now=None, current.valid_from=None reach comparisons)',
     '0030 v8: required/optional normalizer split — T, now and both valid_from use `as_utc_required`; only `invalidated_at` uses `as_utc_optional` (V-NORM-TOTAL). — fold 7b929b5',
     'git show 7b929b5 -- specs/0030-time-relative-classification.md'),
    ("0030", "external", 2, '0030-R2-8',
     '[F8] 0029 \'digest-only\'/\'one digest\'/data-handling residue; 0030 unknown-string reason called incoherent; V-STALE \'iff\' false early',
     'Split by the folds into F8a (0029 v5: journal stated CONTENT-BEARING in §3/§5, retention and data-handling in §4f) and F8b (0030 v8 in 7b929b5: unknown string reason removed from the incoherent family; V-STALE\'s \'iff\' scoped to grounded results). — fold eaefd8b',
     'git show eaefd8b -- specs/0029-transaction-time-carrier.md specs/0030-time-relative-classification.md'),
    ("0030", "external", 3, '0030-R3-1',
     '[F1] 0030 — the restriction derivation uses the wrong key type (`edge_id in statement["retire"]`; the sweep\'s keys are `(record_type, record_id)`)',
     '0030 v14 §4b-iii: membership is `("edge", edge_id) in statement["retire"]` with the executed heterogeneous retire output in-spec, the explicit no-standing case (zero sweep calls) and ONE sweep; executable in the seam model built the same fold (16ba4c8, restriction_derivation.py). — fold c591422',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_typed_membership_restricts__bare_id_is_the_control -q -p no:randomly'),
    ("0030", "external", 3, '0030-R3-2',
     '[F2] 0030/joint seam — `current_trust` is neither identity-bound nor freshness-bound (loose boolean; `(user, standing-set)` cache key insufficient)',
     '0030 v14 §4a-i: `CurrentState` REPLACES the current carrier — row, standing set, sweep and read token from ONE transaction on ONE connection; rule 0 binds five legs; no caching, the `(user, standing-set)` key named dead; executable shape + token-moves control in restriction_derivation.py (16ba4c8). Reviewer disposition at round 4: \'Still open\' (one-consistent-read not actually implemented → round-4 F1). — fold c591422',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_current_state_is_bound_and_token_moves -q -p no:randomly'),
    ("0030", "external", 3, '0030-R3-3',
     '[F3] 0030 — the raw-to-scope projection is not an executable construction (`try_parse_and_project` has no schema; `quarantined`/`use_only` are derived, not flags)',
     '0030 v14/v15 §4a-iii: the adapter as an executable construction — 18 serialized keys enumerated, flags DERIVED (two-disjunct `quarantined`, schema.py:482), duplicate-refusing decoder required, `MembershipResolver._record_shape` named as the field authority; executed end-to-end against the real ScopeView in raw_adapter.py (16ba4c8). Reviewer disposition at round 4: \'Partially closed; type-totality remains open\' (→ round-4 F2). — fold c591422',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_flags_are_derived_not_read__with_its_control -q -p no:randomly'),
    ("0030", "external", 3, '0030-R3-4',
     '[F4] 0029 — concurrent allocation still lacks the locking schedule required by V-TXN-ALLOC (two DEFERRED txns read the same maxima; second dies `database is locked`)',
     '0029 v8 §4a (commit f5fb7dd, NOT in the provided fold list — \'round-3 F4\' in its subject): `BEGIN IMMEDIATE` before ANY allocation read, txn/seq/batch recorded_at minted after the lock, whole-transaction retry under busy_timeout, PK demoted to backstop-only; §6a scenario 10 carries the DEFERRED schedule as the negative control; executable in allocation_schedule.py (16ba4c8).',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_immediate_schedule_serializes__deferred_is_the_control -q -p no:randomly'),
    ("0030", "external", 3, '0030-R3-5',
     '[F5] 0030 — the reason×cutoff matrix contradicts rule 8 and V-SUBTRACT (post-K supersession GROUNDED in the matrix, FENCED_AS_OF in the algorithm)',
     '0030 v14 §4a-ii: every post-K GROUNDED matrix cell conditioned on rule 8 (current interval contains T, semantic identity matches, all current caps allow); reviewer disposition at round 4: \'Closed\'. — fold c591422',
     'git show c591422 -- specs/0030-time-relative-classification.md'),
    ("0030", "external", 3, '0030-R3-6',
     '[F6] 0030 — the amendments did not propagate through all normative carriers (§1/§2 old signature; §2c; §3; §6a; one vs many sweeps; V-ADDITIVE; Spec-Requires)',
     '0030 v14 killed the one-sweep ambiguity and v15 added two propagation sentences; the propagation check was born the same day (d8f1b70) — but the reviewer\'s round-4 disposition was \'Still open\' (→ round-4 F3, which lists a superset of these carriers), so this round\'s fold closed only part of the list. — fold c591422',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_the_nine_surviving_carriers_are_all_clear -q -p no:randomly'),
    ("0030", "external", 4, '0030-R4-1',
     '[F1] `CurrentState` does not implement its one-consistent-read promise (consecutive queries, no BEGIN, no store lock; ScopeView\'s lazy ledger reads land later)',
     '0030 v16 §4a-i states the mechanism as EXCLUSION (SHARED lock for the window) with the scope decision computed in-transaction per option (a); the model half (8a57b99, NOT in the provided list) runs everything inside an explicit read transaction under the store lock, proven by forced interleaving with the autocommit straddle kept as a permanent negative control. (The \'exclusion, not snapshot\' wording was itself refuted in WAL mode at round 5 F3.) — fold f56604d',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_autocommit_straddle_is_real__the_round4_control -q -p no:randomly'),
    ("0030", "external", 4, '0030-R4-2',
     '[F2] The raw adapter is not total over malformed field types (`provenance.source_id=[]` accepted; the real `ScopeView` raised `ScopeError`)',
     '0030 v16 §4a-iii: presence is not validity — per-field types plus the shipped identity bounds (1..IDENTITY_MAX), the invariant that the adapter never passes what its consumer raises on, and TYPE-BEFORE-MEMBERSHIP promoted to a propagation rule; the model half (f83d8f3, NOT in the provided list) ran a mutant campaign over the whole field domain and the ScopeView cross-check. — fold f56604d',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_the_reviewers_exact_probe -q -p no:randomly'),
    ("0030", "external", 4, '0030-R4-3',
     '[F3] The propagation check is green while normative carriers still disagree (nine surviving carriers; hard-coded sets; `_record_shape` does not read `disclosure`)',
     '0030 v16: the `disclosure` claim RETRACTED (executed: `_record_shape` returns exactly {author, evidence_ref, lineage, origin, source_id}) and the nine surviving carriers walked as a NAMED LIST; the checker (f83d8f3) now INTROSPECTS `_record_shape` by calling it and carries the nine carriers as a regression list with its own control. Reviewer\'s round-5 view: propagation evidence \'remain false-green\' (→ round-5 F4). — fold f56604d',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_the_nine_surviving_carriers_are_all_clear -q -p no:randomly'),
    ("0030", "external", 4, '0030-R4-4',
     '[F4] `source_restricted`\'s type overstates what was computed (returns the entire standing set; one collective sweep establishes only a boolean)',
     '0030 v16: `source_restricted` is a BOOLEAN, `frozenset(standing)` named as false attribution; model half in 8a57b99 (restriction_derivation) and f83d8f3 (current_state_carrier), NOT in the provided list. Superseded at round 5 by the three-valued `RestrictionVerdict`; textual `frozenset` residue persisted to rounds 5–6 (round-5 F4, round-6 F4). — fold f56604d',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_typed_membership_restricts__bare_id_is_the_control -q -p no:randomly'),
    ("0030", "external", 5, '0030-R5-1',
     '[F1] The precomputed scope result is not part of the normative classifier contract (`CurrentState` omits `scope_cell`; pseudocode still calls the live view)',
     '0030 v17 §4a-i: the scope decision is computed in-transaction and CARRIED as `scope_cell`; the classifier consumes it, the live view calls are gone from the pseudocode, and rule 0 binds the cell\'s principal against `view.principal` (the authority-moves law); the seam model (952bf25) unified the carrier definition (restriction_derivation imports from current_state_carrier) and populates the cell through the adapter. — fold 5450907',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_pseudocode_and_carrier_types_agree_with_the_spec -q -p no:randomly'),
    ("0030", "external", 5, '0030-R5-2',
     '[F2] Malformed current records can still raise before the classifier (`Edge.model_validate_json` in scope precomputation; `source_id=[]` raises ValidationError)',
     '0030 v17: the restriction verdict is THREE-VALUED (`clear`/`restricted`/`undeterminable`, undeterminable → FENCED_AS_OF never EXCLUDED, collapse at the classifier); the model (952bf25) catches ValidationError at exactly the projection boundary, routes the scope cell through the adapter (fail-closed HIDDEN cell), and runs the 12-cell principal × standing × malformation matrix with no raise. — fold 5450907',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_end_to_end_matrix_never_raises -q -p no:randomly'),
    ("0030", "external", 5, '0030-R5-3',
     '[F3] The stated SQLite mechanism is false in WAL mode (the foreign write succeeded; consistency held by read-snapshot semantics, not writer exclusion)',
     'Seam model: the mode-neutral ONE-WORLD-PER-WINDOW property executed in BOTH journal modes (rollback excludes, WAL snapshots — the reviewer\'s WAL refutation reproduced and kept). The spec-side wording was NOT corrected in 5450907 (round-6 F4 names the surviving rollback-only \'writers excluded\' text; closed at rounds 7–8 per 0030 v19/v20 history, outside this ledger\'s range). — fold 952bf25',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_transactional_read_is_one_world__both_journal_modes -q -p no:randomly'),
    ("0030", "external", 5, '0030-R5-4',
     '[F4] The propagation and adapter evidence remain false-green (`frozenset[str]` residue; checker misses scope cell/live view calls; adapter rejects `evidence_ref=""`)',
     '0030 v17: the adapter\'s contract DERIVED from the shipped model via field introspection (it had been stricter than production on six fields) with a named field × case-class coverage matrix; the model (952bf25) adds `check_pseudocode` (extracts the classifier block, bans live view calls, introspects carrier types) and the two-sided accept-everything-production-emits campaign. Residue closure was INCOMPLETE — round-6 F4 found `frozenset` still in the spec and the checker still blind to it. — fold 5450907',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_provenance_empty_and_overbound__expectation_DERIVED -q -p no:randomly'),
    ("0030", "external", 6, '0030-R6-1',
     '[F1] The carried scope decision is encoded incorrectly (`decision()` returns `(visible, shape)`; `current_state()` stores the whole pair in `ScopeCell.shape`)',
     'Dev half: the carried decision is decomposed ONCE at the fill site in restriction_derivation.current_state; carried == direct asserted per reachable decision-table row with the double-wrap kept as a discriminating control. — fold 4aec843',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_carried_decision_equals_direct__every_reachable_row -q -p no:randomly'),
    ("0030", "external", 6, '0030-R6-2',
     '[F2] The new principal binding is described but not executed (`bind()` ignores `scope_cell.principal`; a cell for a different principal still returns BOUND)',
     'Research half (0030 v18 + current_state_carrier.py): `View` gains `principal`, `bind()` gains a SIXTH leg (view present ⇒ cell required and principal must match; absence refused as firmly as mismatch) with two discriminating controls (mismatched cell, absent principal); the driver\'s `test_five_leg_binding` became `test_six_leg_binding__with_its_control`. — fold 4aec843',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_cell_principal_mismatch_is_refused__with_its_control -q -p no:randomly'),
    ("0030", "external", 6, '0030-R6-3',
     '[F3] The three-valued derivation still permits an exception (`project_store` also parses ledger payloads; a malformed one produced an uncaught `JSONDecodeError`)',
     'Dev half: `ProjectionUnreadable` wraps exactly the three decode families (edge, episode, ledger — json.loads at revocation.py:232) and is caught ALONE at the derivation boundary → UNDETERMINABLE, with a narrowness control proving non-decode failures propagate. (Rounds 7–8 later widened the family to the whole region — outside this range.) — fold 4aec843',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_malformed_ledger_payload_yields_undeterminable -q -p no:randomly'),
    ("0030", "external", 6, '0030-R6-4',
     '[F4] The normative text and checker remain inconsistent (`frozenset` residue, rollback-only wording, `_legacy_bool_removed`; adapter\'s `is_required()` never called)',
     '0030 v18: all three frozenset/_legacy_bool_removed residues corrected in spec AND driver; the checker reads EVERY fenced block with comments retained, discriminating by position; F4b retracts the `is_required` claim (the string-annotation test kept with an executable ForwardRef control). The rollback-only wording was NOT closed here — round-7 F3 / round-8 F3 (v19/v20) made it mode-neutral. — fold 4aec843',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_pseudocode_and_carrier_types_agree_with_the_spec -q -p no:randomly'),
    ("0030", "external", 7, '0030-R7-1',
     '[1.] Principal-binding rules disagree. Model/guide return BOUND for a carried cell with no view; 0030 v18 returns IDENTITY_UNBOUND; rule 0 still says \'five legs\'.',
     'The model\'s bind() was aligned TO the spec (the viewless principal-bearing cell refused; control_no_view_does_not_require_a_cell INVERTED into control_no_view_refuses_a_principal_bearing_cell, its principal-less narrowing split into control_no_view_allows_a_principal_less_cell) in df31c62; the spec\'s rule-0 comment corrected from FIVE legs to SIX in 0226dd1 (spec :249-259 hunk). The \'five legs\' README row and the principal-less narrowing were both re-raised in round 8 F1.',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_no_view_refuses_a_principal_bearing_cell__with_its_control -q -p no:randomly'),
    ("0030", "external", 7, '0030-R7-2',
     '[2.] The three-valued derivation is still incomplete. Invalid UTF-8 -> uncaught UnicodeDecodeError; invalid ledger fields -> uncaught RevocationError; §4a-i boolean.',
     'seam half closed at df31c62 (the three-valued derivation total over invalid UTF-8 and every other malformation, refusing not raising). The SPEC half — §4a-i assigns a boolean to `restricted` where the carrier types `source_restricted: RestrictionVerdict` three-valued, and never shows the unreadable-data transition — is UNCHANGED from v15 through v30 ACCEPTED: the v19 cell claims it corrected, 0226dd1\'s three hunks do not touch §4a-i, and the reviewer never re-raised it. This row does NOT cite 0226dd1 for it (both seats, 2026-09-04).',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_invalid_utf8_ledger_payload_yields_undeterminable -q -p no:randomly'),
    ("0030", "external", 7, '0030-R7-3',
     '[3.] The read-window wording remains contradictory. §4a-i says the mechanism is exclusion, writers refused, then describes a SQLite snapshot. Not mode-neutral.',
     'Spec §4a \'ONE CONSISTENT READ\' paragraph rewritten mode-neutrally (rollback-journal -> exclusion; WAL -> snapshot; the one assertable invariant \'one read window, every read within it describes one world\'), and the \'one SQLite snapshot\' phrase in the transaction paragraph replaced (0226dd1, hunk :529-560). Two stragglers (the §4a headline and the signature comment) were re-raised as round-8 F3.',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_transactional_read_is_one_world__both_journal_modes -q -p no:randomly'),
    ("0030", "external", 7, '0030-R7-4',
     '[4.] The requiredness evidence is overstated and unwired. control_presence_derivation_agrees() never referenced; 12 fields vs 28 claimed; last_outcome retained.',
     'df31c62 wired the control (test_presence_derivation_agrees__with_its_control) and closed the CLASS with test_every_control_in_the_seam_model_is_asserted (which found a third unwired control on its first run); 0226dd1 removed the retracted last_outcome explanation from the version cell (v19 cell text). The 12-vs-28 field claim lived in the package\'s review guide, not a repo carrier tracked by these folds. The checker itself was re-raised as round-8 F4.',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_presence_derivation_agrees__with_its_control -q -p no:randomly'),
    ("0030", "external", 8, '0030-R8-1',
     '[1.] The viewless-cell contract is still incomplete and inconsistently propagated. Rule 0 accepts a principal-less cell. Require cell is None whenever view is None.',
     'THE PAIR RULE: spec rule 0 changed from `elif cell is not None and cell.principal is not None` to `elif cell is not None` — ANY viewless cell refuses IDENTITY_UNBOUND (c2ead33, spec :304 comment); the superseded \'surplus\' prose swept; V-BIND row rewritten to name the cell/view PAIR and its phantom test citation replaced with real tests (c2ead33). Seam half in 5ae0385: control_viewless_cell_is_refused replaces the round-7 narrowing control (asserting both halves), README \'five-leg\' row corrected to six-leg, propagation_check C7 re-anchored on the V-BIND row head, and the store driver replays the producer\'s REAL cell viewless with its principal stripped. The joint manifest was a package artifact (first repo commit 627aea2, round 18).',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_viewless_cell_is_refused__with_its_control -q -p no:randomly'),
    ("0030", "external", 8, '0030-R8-2',
     '[2.] The persisted-data totality claim is false. A stored payload of 10,000 nested JSON arrays raises RecursionError from source_restricted, not UNDETERMINABLE.',
     'The interpretation boundary made REGION-TOTAL in restriction_derivation.py: any Exception inside project_store wraps as ProjectionUnreadable, the standing-set read + ordering gained their own boundary (a BLOB digest row\'s TypeError from min() — the class exhausted past the named finding), and the narrowness control moved to the honest edge (a RuntimeError injected at the sweep, outside the region, propagates). — fold 5ae0385',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_deeply_nested_payload_yields_undeterminable -q -p no:randomly'),
    ("0030", "external", 8, '0030-R8-3',
     '[3.] The read-window wording remains contradictory. §4a opens \'EXCLUSION, not a snapshot\'; pseudocode says \'one SQLite snapshot\'; add a V-WINDOW entry.',
     'The two round-7 stragglers fixed: the §4a headline now reads \'one read window, one world — the mechanism is MODE-DEPENDENT (round-8 F3 …)\' (spec :549) and the CurrentState signature comment\'s \'one SQLite snapshot\' replaced with \'one read WINDOW, one world (mode-neutral …)\' (spec :239); a V-WINDOW row added to the invariant table citing test_transactional_read_is_one_world__both_journal_modes (spec :845). The manifest\'s unconditional exclusion claim was a package artifact. Explicitly declared closed by the round-9 verdict. — fold c2ead33',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_transactional_read_is_one_world__both_journal_modes -q -p no:randomly'),
    ("0030", "external", 8, '0030-R8-4',
     '[4.] The \'every control is asserted\' checker is not exhaustive. Scans only current_state_carrier and raw_adapter; a control planted in restriction_derivation passed.',
     'The every-control sweep rewritten in the STORE driver as EXHAUSTIVE: seam_model modules DISCOVERED from the directory (_seam_modules), BOTH drivers as the assertion corpus, a permanent synthetic-module negative control with a runtime-assembled name (test_the_control_sweep_can_fail__control), the plant proof run in restriction_derivation (planted -> sweep failed naming it -> removed, sha16 58e7748bd80837ea); the round-7 checker deleted from the main driver with a tombstone. — fold 5ae0385',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_every_control_in_the_seam_model_is_asserted -q -p no:randomly'),
    ("0030", "external", 9, '0030-R9-1',
     '[1.] Persisted-value totality is still false. A valid stored {"base":{},"contributor":{}} reaches _fold() -> KeyError(\'valid_from\'), escaping source_restricted().',
     'A SHIPPED-CODE fix: src/veracium/store/revocation_sweep.py::_side now validates the three RECOMPUTED_FIELDS per side (present and typed as the writer emits) before _fold, raising RevocationError — order A refuses inside revoke_source with R19 rollback, order B returns UNDETERMINABLE through source_restricted; a 12-cell side × field × {absent, wrong-type} matrix added; CHANGELOG Unreleased entry records crash -> typed refusal. The reviewer\'s exact payload also became a shared 0022 vector in round 10 (recompute_empty_sides_refuse). — fold efab441',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_reviewers_empty_sides_payload_yields_undeterminable -q -p no:randomly'),
    ("0030", "external", 9, '0030-R9-2',
     '[2.] The control census proves textual mention, not execution. _unasserted_controls() checks only whether each name occurs in driver text; a comment satisfies it.',
     'The census rewritten as an AST CALL census over both drivers — a control must be the callee of a real Call node; all 19 real controls confirmed genuinely called; the permanent negative is the reviewer\'s construction (a decoy comment mentions control_mentioned_never_invoked and test_the_control_sweep_can_fail__control asserts the census flags it). Re-raised as round-10 F3 (terminal names, not identity). — fold efab441',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_every_control_in_the_seam_model_is_asserted -q -p no:randomly'),
    ("0030", "external", 9, '0030-R9-3',
     '[3.] The executable pair rule still admits a present pair with no principal. Both None; equality succeeds and bind() returns BOUND vs \'one principal when present\'.',
     'PRESENCE PRECEDES EQUALITY: the carrier\'s bind() refuses a None principal on a present pair before comparing (control_principal_less_pair_is_refused, efab441) and the spec\'s rule-0 pseudocode gained `if cell.principal is None: return IDENTITY_UNBOUND` with the round-9 F3 comment (4d90e69, spec :288); constructors stay deliberately wide (enforcement at bind() only), justified by production ScopeView raising at scope_read.py:307. The spec half guarded only cell.principal and was re-raised as round-10 F4.',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_principal_less_pair_is_refused__with_its_control -q -p no:randomly'),
    ("0030", "external", 10, '0030-R10-1',
     '[1.] Persisted confidence validation is not domain-total. _side() accepts any non-boolean number; confidence 2.0 survived revoke+lift; NaN and infinities admitted.',
     'Shipped revocation_sweep.py::_side now validates every fold output against the shipped model\'s DOMAIN — confidence finite in [0.0, 1.0] (NaN/inf refused explicitly), valid_from/observed_at parseable canonical json_datetime (the same laundering one field over closed as a class); real-store regressions prove revoke refuses with rollback and a rotted ledger under a standing revocation makes the lift refuse without half-lifting; the seam matrix widened to 24 cells. — fold ed4ab40',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_out_of_domain_confidence_refuses_revoke_and_lift -q -p no:randomly'),
    ("0030", "external", 10, '0030-R10-2',
     '[2.] The accepted 0022 oracle does not carry the shipped fix. reference_revocation.py::_side() validates only the wrapper; shared vectors carry no invalid shapes.',
     'The CURRENT _side (fields + types + domains) ported to specs/evidence/0022/reference_revocation.py with the confession in its docstring; specs/evidence/0022/vectors.json gained 12 invalid-shape recompute vectors (proven failing against the OLD reference first); a new both-implementations test refuses the whole matrix through reference AND product. Carrier is the 0022 evidence tree (not the seam model directory). — fold ed4ab40',
     '$PY -m pytest tests/test_0022_sweep_vectors.py::test_reference_and_product_refuse_the_same_invalid_shapes -q -p no:randomly'),
    ("0030", "external", 10, '0030-R10-3',
     '[3.] The invocation census identifies terminal names, not callables. _invoked_names() records only Name.id/Attribute.attr; alias or dispatch invocation invisible.',
     'The census\'s FOURTH rung: identity resolved through each driver\'s imports (from-import bindings incl. aliases; module-attribute calls), crediting (module, function) pairs, and the grammar CONSTRAINED where identity cannot be traced — rebinding an imported control to another name is a census violation outright; permanent negatives for the same-name-foreign-call and both rebind shapes (store driver, later promoted into seam_model/binding_census.py::census_source). Re-raised as round-11 F2 (shadowing). — fold ed4ab40',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_same_name_foreign_call_does_not_credit__control -q -p no:randomly'),
    ("0030", "external", 10, '0030-R10-4',
     '[4.] The principal rule still disagrees across normative carriers. v21 pseudocode guards only cell.principal then derefs view.principal.origin; V-BIND says \'equal\'.',
     'Spec rule 0 now reads `if cell.principal is None or view.principal is None: return IDENTITY_UNBOUND` before the dereference (a7163bb, spec :288-289), V-BIND reads \'principals PRESENT on both sides AND equal — the guard before the dereference\' (spec :844); propagation_check.py gained the deref-safety rule (_deref_safety + control_deref_safety_can_fail) with a negative control firing on a synthesized deref-before-guard shape AND on the v21 text (ed4ab40, research\'s half adopted byte-identical). Declared closed by the round-11 verdict.',
     '$PY -m pytest tests/test_seam_model_0029_0030.py::test_deref_safety_rule__with_its_control -q -p no:randomly'),
    ("0030", "external", 11, '0030-R11-1',
     '[1.] Datetime validation accepts values for which the fold is semantically wrong. _side() checks parseability only; _fold() compares strings; offsets reverse order.',
     'Both implementations fixed in one commit: revocation_sweep.py::_side and reference_revocation.py::_side validate the EXACT canonical writer form (aware, utcoffset zero, json_datetime round-trip == value — refusing offset/naive/date-only/spelled-+00:00/padded-precision), and _fold + the clamp compare PARSED UTC instants (production compares datetime objects, graph.py:463-464); vectors.json gained five refused datetime-domain vectors (the reviewer\'s offset pair first) plus the accepted-value discriminator recompute_chronological_not_lexical_max; the differential harness now compares accepted values across both implementations; seam matrix widened to 40 cells. Credited closed in the round-12 verdict. — fold e425065',
     '$PY -m pytest tests/test_0022_sweep_vectors.py::test_reference_and_product_agree_on_accepted_values -q -p no:randomly'),
    ("0030", "external", 11, '0030-R11-2',
     '[2.] The callable-identity census does not account for shadowing. _census_source() ignores later name binding; def-shadow and module reassignment credit original.',
     'The census\'s FIFTH rung: a PROTECTED set (imported control names + seam-module aliases, derived from the directory) and every shadowing construct refuses — def/class, plain/annotated/augmented/unpacked assignment, walrus, for/comprehension targets, with-as, except-as, parameters, conflicting re-imports (same-module local re-import stays legal with its own control); twelve permanent negatives, the reviewer\'s two probes verbatim first; first-binding-wins fixed a pre-ship deprotection hole. Re-raised as round-12 F1 (lambda parameters and pattern captures). — fold e425065',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_shadowing_is_a_census_violation__controls -q -p no:randomly'),
    ("0030", "external", 12, '0030-R12-1',
     '[1.] The protected-binding census still misses Python binding constructs. Covers function parameters but not lambda parameters (`lambda rd:`) or `case rd:` captures.',
     'The census learned the family\'s remainder (ast.Lambda with the same parameter treatment as a def; MatchAs / MatchStar / MatchMapping-rest with nested sequence/class/or patterns reached by the walk) and, per the mechanical-reviewability ask, gained BINDING_CONSTRUCTS — an explicit handled/excluded inventory of name-introducing constructs with a coverage test asserting every handled entry appears in a battery probe and every ast.Match* class is inventoried; the census PROMOTED into specs/evidence/0029-0030/seam_model/binding_census.py; battery at 23 with the reviewer\'s two probes verbatim first. (test_the_binding_inventory_is_covered_causally is round-13, not this fold.) — fold efa8ec0',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_shadowing_is_a_census_violation__controls -q -p no:randomly'),
    ("0030", "external", 13, '0030-R13-1',
     '[1] `TypeAlias` is incorrectly excluded from the binding census',
     'binding_census.py::census_source now HANDLES ast.TypeAlias where the interpreter has it (node.name.id passed to _shadow, violation tagged \'[TypeAlias]\'), BINDING_CONSTRUCTS moves TypeAlias from excluded to handled (availability below 3.12 is a parser fact, skip-with-reason, never a semantic exclusion), the reviewer\'s two probes are permanent version-gated negatives in SHADOW_PROBES, and — the verdict\'s sub-ask — coverage is made CAUSAL: every violation brackets the shadowing AST class and test_the_binding_inventory_is_covered_causally requires per handled construct a probe whose violation NAMES it (a dedicated \'conflicting-refrom-import\' probe closes the ImportFrom appears-somewhere hole); recorded in the 0030 v25 Version cell. — fold 878151e',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_shadowing_is_a_census_violation__controls -q -p no:randomly'),
    ("0030", "external", 14, '0030-R14-1',
     '[1] The census still proves a syntactic call, not runtime execution',
     'The execution claim moves off the static census onto a RUNTIME registry: binding_census.py::assert_control invokes a control, asserts its result and records its identity only after the assert passes; tests/test_seam_model_0029_0030_store.py::test_every_control_was_executed_and_asserted compares the discovered control set against the registry, anchored LAST by a trylast conftest hook (after pytest-randomly), fails by design on a partial surface, and skips with a registered \'selection-conditional\' reason when nothing was recorded; the reviewer\'s `if False:` construction is the permanent discriminating pair (static credits / runtime lacks); the static census is rescoped to source hygiene; all 21 control call sites across both drivers converted to the runner; recorded in the 0030 v26 Version cell. — fold 2cbaaf4',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_dead_branch_credits_static_but_not_runtime__control -q -p no:randomly'),
    ("0030", "external", 15, '0030-R15-1',
     '[1] The runtime registry does not record exact callable identity',
     'The registry key moves from writable metadata `(control.__module__, control.__name__)` to the FUNCTION OBJECT itself (EXECUTED becomes a set of objects), the gate re-resolves discovered callables fresh at gate time (the reviewer\'s also-consider), the reviewer\'s four-part discriminating test is permanent via the new reusable binding_census.py::impostor_of probe with the round-14 key-satisfied contrast asserted; the topology adjudication is implemented too — the gate DETECTS xdist (PYTEST_XDIST_WORKER) and fails explicitly, the single-process topology is stated in assert_control\'s docstring, and the skip-when-empty reason labels itself \'a selection convenience, NEVER positive evidence\'; recorded in the 0030 v27 Version cell. — fold 9a04dea',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_metadata_impostor_cannot_satisfy_the_registry__control -q -p no:randomly'),
    ("0030", "external", 16, '0030-R16-1',
     '[Finding 1] Set membership is equality-based, not identity-based',
     'Both halves the verdict offered are taken: THE DOOR — a control IS an ordinary Python function, binding_census.py::assert_control enforces isinstance(control, types.FunctionType) (not subclassable, so the check is exact) and the gate enforces the same at discovery (a callable instance named control_* fails loudly, never silently narrowed out); THE COMPARISON — EXECUTED becomes an id()-keyed dict with references retained, membership everywhere an id lookup with no path through user-definable equality; the reviewer\'s permanent two-equal-instances test asserts the door refusal, the bypass (instance placed directly into the registry) leaving the twin unexecuted, and the set-membership contrast; the definitional statement is ruled to docstrings + the round-17 README; recorded in the 0030 v28 Version cell. — fold 3354946',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_equal_comparing_callables_cannot_satisfy_each_other__control -q -p no:randomly'),
    ("0030", "external", 17, '0030-R17-1',
     '[Finding] Final discovery can silently omit a changed control',
     'The reviewer\'s session-start-inventory feedback taken as the primary design: tests/test_seam_model_0029_0030_store.py::_EXPECTED_CONTROLS is captured at import before any test executes, and the gate validates ALL FOUR CLAUSES per obligation before any filter, in the reviewer\'s order — present (else \'attribute REMOVED\'), an ordinary function (else \'replaced with a non-function\'), of its own module (else \'replaced with a function from module ...\'), and the PRESENT identity executed (a same-module replacement passes only if the replacement itself ran); additions join the obligation under the same clauses; the reviewer\'s four permanent cases run against the real gate end-to-end over a controlled one-module inventory; the in-process trust boundary is stated in the gate docstring; found-in-fix disclosed — the skip-if-empty guard was moved AFTER clauses 1-3 and the additions door after an order-dependent skip surfaced under pytest-randomly; recorded in the 0030 v29 Version cell. — fold dc244f0',
     '$PY -m pytest tests/test_seam_model_0029_0030_store.py::test_changed_controls_fail_explicitly_not_silently__controls -q -p no:randomly'),

    # ---- 0037 external rounds 1-4 (2026-09-06) — the closure ledger written at acceptance (round 5, 2026-09-07). Text-only closures cite the fold commit; the corpus closures cite the pin tests ----
    ("0037", "external", 1, '0037-R1-1',
     'MCP remember(basis=) contradicted the library contract — a dedicated MCP record_procedure tool, capability-gated to direct; remember rejects any basis on both surfaces',
     '§2, §4b, §4e, V-HOST-DECLARED (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-2',
     'the describe result contract undefined — DescribeResult schema (descriptions / withheld / truncated / normalized query), one result per visible candidate, deterministic ordering, the query orders and never filters',
     '§4a-ii, V-RESULT-SCHEMA, V-DESCRIBE-ORDER (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-3',
     'the public claim exceeded the guarantee — the actual guarantee everywhere: the note is rendered in no field, a summary matching the frozen rule is withheld, a paraphrase passes and is a stated limit',
     '§4a-ii, §6, §8 (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-4',
     'Q3 unresolved — research owns the recognition corpus, frozen against the sealed text before implementation, ± sets, change control by amendment; the paraphrase boundary a stated limit',
     '§6a, §10 Q3 (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-5',
     'cross-scope contradictory (§3b third-party shape vs the matrix) — hidden omitted and indistinguishable from no-match; visible use_only a named non-description; withheld query-blind',
     '§3, §3b, §4a-ii, V-SCOPE-OUTERMOST, V-WITHHELD-QUERY-BLIND (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-6',
     'record_procedure relation validation missing — relation must exist in the active registry as procedural or RAISE, nothing written',
     '§4b, V-RELATION-VALID (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-7',
     'registry totality overstated — total over the active registry; a stored edge whose relation left it is the named relation_unregistered (later re-based on the stamp, R2-2)',
     '§4a, V-RELATION-UNREGISTERED (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-8',
     'the scale requirement without an invariant — V-DESCRIBE-ORDER: above-cap population ordered before the cut, stable ties, repeated runs identical, the null query defined',
     '§5, §6 (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-9',
     'Relation(kind=) vs relation_kind — corrected in §4e',
     '§4e (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-10',
     'the reviewer guide said EvidenceAuthor has three members — 0001 §2c-ii:175 annotated as an as-of reach row (0001 added the fourth)',
     'specs/0001 §2c-ii (v8 fold commit)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-11',
     'raises / refuses / named outcome undefined — one failure taxonomy at the head of §4: write paths raise, read paths return named outcomes',
     '§4 head (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-12',
     'ProcedureDescription fields undefined — enumerated; no raw stored text in any field; the note in no field',
     '§4a-ii (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-13',
     'how record_procedure populates id, dates, evidence_ref, source_id, disclosure — stated field by field',
     '§4b (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-14',
     'default-import atomicity on a mixed file — atomic over the admitted set, procedural records refused per record and counted',
     '§4e (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 1, '0037-R1-15',
     "the sibling's governance state disagreed between the version cell and the README — the canonical form in §10 Q6: the commission stands, parked behind a mechanism-selection prerequisite",
     '§10 Q6 (v8)',
     'git show f8567f4 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 2, '0037-R2-1',
     'authorship conflated with derivation (author_of_evidence from the context) — a separate author argument; author / derived_from / basis independent; ONE canonical signature; V-PROVENANCE-AXES',
     '§2, §4b, V-PROVENANCE-AXES (v11)',
     'git show 4616884 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 2, '0037-R2-2',
     'the unregistered-relation remedy withheld legacy custom declarative edges — the declared kind STAMPED on the record at write and read from the stamp; a registry change moves nothing; only a procedural-stamped edge can be relation_unregistered',
     '§2, §2c, §4a, §4c, §7, V-KIND-STAMPED, V-RELATION-UNREGISTERED (v11)',
     'git show 4616884 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 2, '0037-R2-3',
     "the frozen corpus absent from the package — the corpus lives in the tree at tests/eval/procedural_describe/MANIFEST.json, its digest on the spec's single `corpus sha256:` line, bound both directions by tests/test_0037_corpus_pin.py",
     '§6a, §10 Q3, tests/eval/procedural_describe/, tests/test_0037_corpus_pin.py (v11 + 3a19897)',
     '$PY -m pytest tests/test_0037_corpus_pin.py::test_corpus_file_hashes_to_the_spec_digest'),
    ("0037", "external", 2, '0037-R2-4',
     "the CLI --basis line a second producer or a rejected path — CLI support removed from v1; cli.py classified cannot-produce in V-ONE-PRODUCER's sweep",
     '§4e, V-ONE-PRODUCER (v11)',
     'git show 4616884 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 2, '0037-R2-5',
     "COLLECTED.txt carried the capture script's unfilled placeholder line under two green legs — the capture writes none; the assembly refuses the form in any carrier; research's seal check gained ASSERT-15 with a planted control",
     "the round-3 package's PIN.txt and COLLECTED.txt; research's seal_check.sh ASSERT-15 (peer tree, described)",
     'git show 4616884 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 2, '0037-R2-6',
     'validate limit — None → the cap; else an int (not bool) in [1, max_subgraph_edges], else ValueError; above-cap refuses rather than clamps',
     '§4a-ii, V-ARGS-VALIDATED (v11)',
     'git show 4616884 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 2, '0037-R2-7',
     'validation for summary, note, query, when, evidence_ref, source_id — stated per argument; a str or naive when is ValueError under the shipped as_utc_required rule',
     '§2c, §4a-ii, V-ARGS-VALIDATED (v11)',
     'git show 4616884 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 2, '0037-R2-8',
     'raises vs returns-named-refusal — two layers stated once: the library raises, the MCP tools return a serialized refusal and never raise to the transport',
     '§4 head (v11)',
     'git show 4616884 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 2, '0037-R2-9',
     'the public signature omitted author, when, evidence_ref, source_id — ONE canonical signature in §2, referenced from §4a and §4b',
     '§2 (v11)',
     'git show 4616884 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 2, '0037-R2-10',
     '§4a still called Q6 blocking for Quentin — corrected: scoped elsewhere by the owner',
     '§4a (v11)',
     'git show 4616884 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 2, '0037-R2-11',
     'fully reversible too broad — narrowed: complete for declarative records; a downgrade across this version would render procedural records, a stated behaviour change',
     '§7, §4e (v11)',
     'git show 4616884 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 3, '0037-R3-1',
     'the stamp\'s type Optional[Literal["procedural"]] contradicted a `== "declarative"` comparison and 486 corpus cells — the four states stated in the field\'s own terms; every \'declarative stamp\' phrase the absence of a stamp; the corpus amended to null; every row validated against the declared domain',
     '§2, §2c, §4a, §4a-ii, V-KIND-STAMPED, §6a; tests/test_0037_corpus_pin.py (v12)',
     '$PY -m pytest tests/test_0037_corpus_pin.py::test_every_corpus_row_is_in_the_declared_domain'),
    ("0037", "external", 3, '0037-R3-2',
     "default import misclassified a procedural relation when both markers were absent — refuse on ANY of three independent signals (stamp, basis, receiving registry) naming which fired; six cells; restore's both absence dimensions",
     '§2, §2c, §4e, V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE (v12)',
     'git show 07d28a5 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 3, '0037-R3-3',
     "an unchanged export format version unsafe for older readers — FORMAT_VERSION 10→11 stamped conditionally per the shipped 0026 §3d precedent; an old reader refuses; V-OLD-READER-REFUSES executable with the reader's constant held at 10",
     '§4e Export, §8, V-OLD-READER-REFUSES (v12)',
     'git show 07d28a5 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 3, '0037-R3-4',
     "invariant prose still said 'by relation kind' — the stored stamp/basis rule wherever it was a use",
     '§2, §3, §4a, V-OUT-OF-PATH (v12)',
     'git show 07d28a5 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 3, '0037-R3-5',
     "'every writer stamps declarative' read as storing the invalid string — declarative writers leave record_kind=None and omit the key",
     '§2 (v12)',
     'git show 07d28a5 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 3, '0037-R3-6',
     'restore behaviour for basis-present/no-stamp and stamp/no-basis — both absence dimensions malformed, refused per record',
     '§2c, §4e (v12)',
     'git show 07d28a5 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 3, '0037-R3-7',
     'the pin tests validated the binding, not the semantic schema of each row — V-CORPUS-ROWS-IN-DOMAIN and its test',
     '§6, §6a; tests/test_0037_corpus_pin.py (v12)',
     '$PY -m pytest tests/test_0037_corpus_pin.py::test_every_corpus_row_is_in_the_declared_domain'),
    ("0037", "external", 4, '0037-R4-1',
     'the version-key stripping rule disabled two of the three import signals — the three signals are evaluated on the RAW record before any version normalization; a raw marker refuses that record naming the raw signal; only admissible records are normalized; the 8-cell raw-marker × receiving-relation matrix; the strip-before-inspect mutant',
     '§2c, §4e, V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE, §6a; corpus amendment 4 (v13)',
     'git show ae6be76 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 4, '0037-R4-2',
     "replace the single format-10 corpus cell with the full matrix — research's amendment 4, verbatim from the banked verdict, the two discriminating rows flagged, the superseded tautological cell recorded",
     'tests/eval/procedural_describe/MANIFEST.json (v13)',
     '$PY -m pytest tests/test_0037_corpus_pin.py::test_corpus_file_hashes_to_the_spec_digest'),
    ("0037", "external", 4, '0037-R4-3',
     'record or file refusal on a version/key disagreement — RECORD, stated',
     '§2c, §4e, V-IMPORT (v13)',
     'git show ae6be76 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 4, '0037-R4-4',
     "V-IMPORT to say raw record or after normalization — 'evaluated ON THE RAW RECORD, BEFORE version normalization' in those words",
     'V-IMPORT (v13)',
     'git show ae6be76 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 4, '0037-R4-5',
     "the §4a heading named only the registry — renamed: the registry at write, the record's own stamp at read, three raw signals at import; never the text",
     '§4a heading (v13)',
     'git show ae6be76 -- specs/0037-procedural-basis.md'),
    ("0037", "external", 4, '0037-R4-6',
     "'validates through the declared field types' overstated the test — the narrower form everywhere: domain validation now, real Provenance construction after implementation",
     'V-CORPUS-ROWS-IN-DOMAIN, §6a, the manifest (v13)',
     'git show ae6be76 -- specs/0037-procedural-basis.md'),

    # ---- 0029 post-acceptance revision v11 (2026-09-07) — the lock-refusal form; owner-placed, no external round ----
    ("0029", "internal", 0, '0029-PA1',
     'The COMMIT-time `database is locked` surfaced as bare SQLite text with the write rolled back (0028 two-connection transcript, reproduced by the external reviewer); 0029 §4a had narrowed 0007 §4c to the BEGIN, and v10\'s first revision scoped its guarantee to a `_write_txn` commit that never ran — all six bodies committed themselves',
     'v11 §4a/§4a-i: `_write_txn` OWNS the commit of every transaction it opens (six in-body commits removed; two duplicate handlers folded; the C8 race raises at the INSERT — measured); the commit-time lock refused in the BEGIN-time form naming the site, batch not applied, connection reusable (V-LOCK-REFUSAL-FORM); the census node asserts zero in-body commits, its mutant the shipping code; residue censused, 0007 open in §10',
     '$PY -m pytest tests/test_0029_lock_refusal_form.py::test_commit_time_lock_refusal_has_the_begin_time_form tests/test_0029_lock_refusal_form.py::test_no_write_txn_body_issues_its_own_commit tests/test_0029_lock_refusal_form.py::test_the_store_is_unchanged_and_the_next_write_lands -q -p no:randomly'),
    # ---- 0028 external rounds 1-7 (2026-08-31 → 2026-09-07) — the closure ledger written at acceptance (round 7, 2026-09-07). Executable closures cite the permanent test nodes (the successor model, the absence proof, the window transcript, the generated table); text-only closures cite the fold commit that landed them (rounds 1-2 folded into v2–v7, landed together at 26453b6 after the owner's pause). ----
    ("0028", "external", 1, '0028-R1-1',
     'The registry holds SEVEN reasons (revoked_source, 0022\'s seat); the spec\'s "closed six" failed verification against DISPOSITIONED_REASONS',
     'v2–v7 (landed 26453b6): the §4b table is GENERATED from AS_OF_DISPOSITION in registry order with totality asserted at generation; V-CROSS compares it to the enum as data',
     '$PY -m pytest tests/test_0028_reason_resolution_table.py::test_check_passes_against_the_spec_table_as_data tests/test_0028_reason_resolution_table.py::test_mutant_eighth_reason_fails_totality -q -p no:randomly'),
    ("0028", "external", 1, '0028-R1-2',
     'known_as_of is unimplementable from the stated fields: invalidated_at is a valid-time endpoint, there is no transaction-time carrier (the backdated-correction counterexample)',
     'the arc PAUSED on the owner\'s ruling; 0029 (accepted) supplies the transaction-time carrier; v2 (landed as v7, 26453b6) is valid-time only and says so in its title',
     'git show 26453b6 -- specs/0028-as-of-query.md'),
    ("0028", "external", 1, '0028-R1-3',
     'STRUCTURAL: Edge.assertable requires active, so no historical edge can ground under the unchanged classifier',
     '0030 (accepted) supplies the time-relative classifier classify_as_of; v2 (26453b6) reads through it and never through Edge.valid_now/assertable — the absence proof',
     '$PY -m pytest tests/test_0028_asof_absence.py::test_the_behavioural_form_runs_the_shipped_asof_tests_under_the_clock tests/test_0028_asof_absence.py::test_the_static_form_reaches_the_roots_and_finds_no_predicate_access -q -p no:randomly'),
    ("0028", "external", 1, '0028-R1-4',
     'Chain/arity mechanics undefined: backward supersedes, note-carried absorption links, the absorbed-to row unreachable through §4a',
     'v2–v7 (26453b6): §4b-iii reachability stated per row; later the successor contract §5.1 (v3→v13) with the direct-successor rule',
     'git show 26453b6 -- specs/0028-as-of-query.md'),
    ("0028", "external", 1, '0028-R1-5',
     'Correction chains can cross scope (source identity, not subject; 0020 owns read visibility)',
     'v2–v7 (26453b6): scope before the historical filter; later the NON-REVEALING successor design and V-SCOPE-DIFFERENTIAL (v11–v13)',
     '$PY -m pytest tests/test_0028_successor_lookup.py::test_the_model_holds_the_observation_table_and_both_invariants -q -p no:randomly'),
    ("0028", "external", 1, '0028-R1-6',
     'The recall baseline is misstated (active_only=False history already flows) and V-DET overclaims for the composed path',
     'v2–v7 (26453b6): the baseline restated; determinism stated over the composed path with the injected clock (V-ONE-CLOCK)',
     'git show 26453b6 -- specs/0028-as-of-query.md'),
    ("0028", "external", 1, '0028-R1-7',
     'The result/gap carriers and the acceptance corpus are not finite',
     'v2–v7 (26453b6): §6a made FINITE — every invariant CHECKED by a named node or OWED at implementation, no count in prose',
     'git show 26453b6 -- specs/0028-as-of-query.md'),
    ("0028", "external", 2, '0028-R2-1',
     '§5.1 was cited four times and did not exist — the successor accessor had no contract',
     'v3 (landed 26453b6): §5.1 written — direct successors only, scope before the historical filter; redesigned at the view v11–v13 and modelled executably',
     '$PY -m pytest tests/test_0028_successor_lookup.py::test_the_model_holds_the_observation_table_and_both_invariants -q -p no:randomly'),
    ("0028", "external", 2, '0028-R2-2',
     'The verdict column used GROUNDED, a name shipping in neither vocabulary',
     'v3 (26453b6): the table generated from AS_OF_DISPOSITION; V-CROSS compares it to the enum as data',
     '$PY -m pytest tests/test_0028_reason_resolution_table.py::test_check_passes_against_the_spec_table_as_data tests/test_0028_reason_resolution_table.py::test_mutant_shuffled_rows_diverge_from_the_spec_table -q -p no:randomly'),
    ("0028", "external", 2, '0028-R2-3',
     'T > now was declared clamp OR refuse, both conforming — 0011 R1-4\'s unconformable shape',
     'v4 (26453b6): closed on the owner\'s ruling, verbatim "refuse" — the typed FutureAsOfRefused carrying T and now; clamp WITHDRAWN',
     'git show 26453b6 -- specs/0028-as-of-query.md'),
    ("0028", "external", 2, '0028-R2-4',
     'Three of §4b-iii\'s four absorbed-duplicate rows were unreachable (canonical absorption is empty-interval by construction)',
     'v3 (26453b6): the rows named as the class no shipped writer produces; the model\'s forward_missing states carry the same class',
     'git show 26453b6 -- specs/0028-as-of-query.md'),
    ("0028", "external", 2, '0028-R2-5',
     'The inventory said ten checks where §6 has thirteen',
     'v3 (26453b6): no count in prose; the CHECKED/OWED markers are the one accounting rule (re-caught at round 5)',
     'git show 26453b6 -- specs/0028-as-of-query.md'),
    ("0028", "external", 3, '0028-R3-1',
     'The old two-clock algorithm remained in §4a, the normative procedure, after two folds removed it elsewhere',
     'v9 (0410229): §4a re-derived — one injected clock captured at step 0, no step reads a clock; the absence proof over classify_as_of (static tree + recording clock)',
     '$PY -m pytest tests/test_0028_asof_absence.py::test_the_behavioural_form_runs_the_shipped_asof_tests_under_the_clock tests/test_0028_asof_absence.py::test_no_shipped_path_reaches_the_classifier_so_the_derived_set_is_the_reachable_set -q -p no:randomly'),
    ("0028", "external", 3, '0028-R3-2',
     'edges_superseding cannot return its promised omission information',
     'v9: a typed result — which R4-1 then found to be an existence signal; v11–v13: the cause-free three-value SuccessorLookup, modelled executably',
     '$PY -m pytest tests/test_0028_successor_lookup.py::test_v9_typed_result_reintroduces_the_existence_signal -q -p no:randomly'),
    ("0028", "external", 3, '0028-R3-3',
     'facts_valid_at promises scoped behaviour without carrying scope',
     'v9 (0410229): principal and policy on the read API (keyword-only), scope through the shared ScopeView',
     'git show 0410229 -- specs/0028-as-of-query.md'),
    ("0028", "external", 3, '0028-R3-4',
     'MCP exposure remained an unresolved product-interface decision',
     'v9 (0410229): Q5 closed — the as-of read is NOT exposed on the MCP surface in this version; the sentence stated once (R4-4 caught a surviving contrary carrier, fixed v11)',
     'git show 0410229 -- specs/0028-as-of-query.md'),
    ("0028", "external", 3, '0028-R3-C5',
     'The standalone generator command did not run from the extracted tree without PYTHONPATH (a fixed development-machine path)',
     'v9: the generator derives the repository root; the round-4 verdict confirmed it runs without PYTHONPATH',
     '$PY -m pytest tests/test_0028_reason_resolution_table.py::test_check_passes_against_the_spec_table_as_data -q -p no:randomly'),
    ("0028", "external", 3, '0028-R3-C6',
     'Remove the disclosed stale numeral in the v8 history rather than changing it from six to eight',
     'v9 (0410229): removed as the package recommended',
     'git show 0410229 -- specs/0028-as-of-query.md'),
    ("0028", "external", 3, '0028-R3-C7',
     'Clarify the rollback-journal concurrency wording: a writer may wait and commit after the window, or receive a busy error — "refused for the whole resolution" names an outcome that does not occur',
     'v10 (87280da) from the two-connection transcript the reviewer reproduced (the supplemental verdict); the measured rows in §5',
     '$PY -m pytest tests/test_0028_window_transcript.py::test_default_mode_writer_waits_and_commits_after_a_window_shorter_than_its_timeout tests/test_0028_window_transcript.py::test_default_mode_writer_fails_and_loses_the_write_when_the_window_outlasts_its_timeout -q -p no:randomly'),
    ("0028", "external", 4, '0028-R4-1',
     'SuccessorLookup contradicted scope indistinguishability — the typed result added to fix R3-2 was itself an existence signal across the scope boundary',
     'v11 (b4a680c): the NON-REVEALING design — a successor outside the view is not an omission; V-NO-EXISTENCE-SIGNAL with whole-object equality and its positive control; the registry NAMES_A_SUCCESSOR',
     '$PY -m pytest tests/test_0028_successor_lookup.py::test_v9_typed_result_reintroduces_the_existence_signal tests/test_0028_successor_lookup.py::test_collapsing_the_hidden_case_into_head_trades_a_leak_for_a_lie tests/test_0028_successor_lookup.py::test_the_hand_set_corrected_alone_lies_to_the_principal_on_two_reachable_states -q -p no:randomly'),
    ("0028", "external", 4, '0028-R4-2',
     'A second wall-clock exception remained ("except the current-truth pointer")',
     'v11 (b4a680c): no step reads a clock; the pointer is a current-state fact evaluated at the same captured now',
     'git show b4a680c -- specs/0028-as-of-query.md'),
    ("0028", "external", 4, '0028-R4-3',
     'The old rollback-journal rule remained in V-ONE-SNAPSHOT (a third wording of the disproved claim)',
     'v11 (b4a680c): V-ONE-SNAPSHOT restated from the measured rows; the wording registered as withdrawn (v13)',
     '$PY -m pytest tests/test_0028_window_transcript.py::test_wal_writer_commits_during_the_window_and_the_reader_keeps_its_snapshot -q -p no:randomly'),
    ("0028", "external", 4, '0028-R4-4',
     'MCP remained simultaneously closed and open',
     'v11 (b4a680c): one sentence, Q5 closed, every contrary carrier removed',
     'git show b4a680c -- specs/0028-as-of-query.md'),
    ("0028", "external", 4, '0028-R4-5',
     'Pointer-walk text still consumed the old list return',
     'v11 (b4a680c): the walk reads the SuccessorLookup result; resolved together with R4-1',
     'git show b4a680c -- specs/0028-as-of-query.md'),
    ("0028", "external", 4, '0028-R4-M1',
     'The orphaned "moot." after the corrected lane statement',
     'v11 (b4a680c)',
     'git show b4a680c -- specs/0028-as-of-query.md'),
    ("0028", "external", 4, '0028-R4-M2',
     'Several §6 rows described future checks while §6a said every invariant already carried a named check',
     'v11 (b4a680c): §6a stated by class — CHECKED today vs OWED at implementation',
     'git show b4a680c -- specs/0028-as-of-query.md'),
    ("0028", "external", 4, '0028-R4-M3',
     'The standalone table generator correction is successful (confirmation)',
     'v9/v11: runs without PYTHONPATH',
     '$PY -m pytest tests/test_0028_reason_resolution_table.py::test_check_passes_against_the_spec_table_as_data -q -p no:randomly'),
    ("0028", "external", 5, '0028-R5-1',
     'The public successor accessor could disclose a hidden queried edge — the queried edge was read from the unfiltered collection',
     'v12 (eddcb23): the queried edge\'s assertion is readable only when visible in the caller\'s view; edges_superseding is not an existence oracle; the differential on both arms',
     '$PY -m pytest tests/test_0028_successor_lookup.py::test_the_v11_lookup_that_read_the_queried_edge_unfiltered_discloses_it tests/test_0028_successor_lookup.py::test_collapse_everything_passes_the_equality_half_and_fails_the_control -q -p no:randomly'),
    ("0028", "external", 5, '0028-R5-2',
     'The malformed-reference rule was directionally inconsistent with an accessor searching supersedes == edge_id',
     'v12 (eddcb23): forward_missing and dangling_backward named apart; both in the model\'s table',
     '$PY -m pytest tests/test_0028_successor_lookup.py::test_the_model_holds_the_observation_table_and_both_invariants -q -p no:randomly'),
    ("0028", "external", 5, '0028-R5-3',
     'The reviewer checklist contradicted the cause-free result contract',
     'v12 (eddcb23): the checklist carries two classes; R6-1 then found the definition it summarises unchanged (closed v13)',
     'git show eddcb23 -- specs/0028-as-of-query.md'),
    ("0028", "external", 5, '0028-R5-C1',
     'README and §9 claimed nine states while EXPECTED executed eight',
     'v12 (eddcb23): no count in any carrier; the program prints it',
     'git show eddcb23 -- specs/0028-as-of-query.md'),
    ("0028", "external", 5, '0028-R5-C2',
     'The model header said supersession is asserted when the reason equals only corrected, contradicting the three-reason registry',
     '808d5e4: the header corrected to the registry',
     'git show 808d5e4 -- specs/evidence/0028/check_successor_lookup.py'),
    ("0028", "external", 5, '0028-R5-C3',
     'The test and model headers still described six states',
     '808d5e4 + eddcb23 (build()\'s docstring): no count in either header',
     'git show 808d5e4 -- specs/evidence/0028/check_successor_lookup.py'),
    ("0028", "external", 5, '0028-R5-C4',
     '§6a said nineteen invariants and then "no count is stated here, deliberately"',
     'v12 (eddcb23): one accounting rule — the CHECKED/OWED markers',
     'git show eddcb23 -- specs/0028-as-of-query.md'),
    ("0028", "external", 6, '0028-R6-1',
     '§4b\'s outcome definition still required a cause for every INDETERMINATE, contradicting cause-free SUCCESSOR_UNAVAILABLE (the checklist was fixed at v12, the definition it summarises was not)',
     'v13 (6680150): §4b carries the two classes — causes for conditions observable within the view; none for SUCCESSOR_UNAVAILABLE, by design',
     'git show 6680150 -- specs/0028-as-of-query.md'),
    ("0028", "external", 6, '0028-R6-2',
     '§4b-o, §5 and §7 described the commit-time lock as SQLite\'s bare message "surfacing unwrapped" while the sealed tree (0029 v11) and the window test carried the wrapped form',
     'v13 (6680150): all three carriers state the wrapped refusal naming the COMMIT site, SQLite\'s message as the cause; history marked; the wording registered as withdrawn',
     '$PY -m pytest tests/test_0028_window_transcript.py::test_default_mode_writer_fails_and_loses_the_write_when_the_window_outlasts_its_timeout -q -p no:randomly'),
    ("0028", "external", 6, '0028-R6-C1',
     '§9 carried a malformed duplicated phrase (the round-5 "no count" replacement fused with its neighbour)',
     'v13 (6680150)',
     'git show 6680150 -- specs/0028-as-of-query.md'),
    ("0028", "external", 6, '0028-R6-C2',
     'The model\'s introduction called itself "the design v11 specifies" while its queried-edge behaviour is the v12 amendment',
     '6680150: "the v11 design as amended by v12" at both docstring sites; the phrase at zero over the file',
     'git show 6680150 -- specs/evidence/0028/check_successor_lookup.py'),
    # ---- 0038 external rounds 1-4 (2026-09-07 → 2026-09-08) — the closure ledger written at acceptance (round 4, 2026-09-08). Executable closures cite the enforcement tests, the two pin tests and the disposition test by node; text-only closures cite the fold commit that landed them. ----
    ("0038", "external", 1, '0038-R1-1',
     'The claimed structural prevention is not enforced — instructions is optional and an extractor may emit it AND a disposition triple; the stored set shrinks only if the model obeys the prompt',
     'v3 (48d0dc3): enforcement AT INGEST — a triple whose object equals a declared instruction under the comparison key is refused and counted; third_party_claim exempt (v4); shipped at d59592d under the owner\'s security-hotfix exception',
     '$PY -m pytest tests/test_0038_instruction_enforcement.py::test_both_carriers_the_disposition_is_not_stored tests/test_0038_instruction_enforcement.py::test_the_match_is_equality_under_the_comparison_key_not_containment tests/test_0038_instruction_enforcement.py::test_a_third_party_claim_survives_its_own_declaration -q -p no:randomly'),
    ("0038", "external", 1, '0038-R1-2',
     'The acceptance invariants lack executable checks; "a named class" is not a bounded pass condition; a defined rule or frozen oracle for completed performance',
     'v3–v5.9: every invariant names its node; the oracle is a frozen REGISTRY bound by one pin with its disposition checked over the set (the §8 gate is NOT met; §6b-A, the weaker rule, is)',
     '$PY -m pytest tests/test_0038_oracle_pin.py::test_manifest_hashes_to_the_spec_digest tests/test_0038_oracle_pin.py::test_the_rulings_digest_matches_the_manifest_by_its_stated_method tests/test_oracle_set_disposition.py::test_the_disposition_holds_over_every_file_in_the_set -q -p no:randomly'),
    ("0038", "external", 1, '0038-R1-3',
     'The mandatory uncontrolled-input matrix is absent (§2c was prose)',
     'v3 (48d0dc3): an eight-row matrix, one row per case with its observable outcome and enforcing invariant; each row tested',
     '$PY -m pytest tests/test_0038_instruction_enforcement.py::test_row1_absent_instructions_is_processed_as_today_the_residual tests/test_0038_instruction_enforcement.py::test_row2_wrong_type_instructions_is_the_unparseable_branch tests/test_0038_instruction_enforcement.py::test_row7_mixed_event_keeps_its_declarative_facts_and_refuses_only_the_match tests/test_0038_instruction_enforcement.py::test_row8_unparseable_branch_carries_the_counter_at_zero -q -p no:randomly'),
    ("0038", "external", 1, '0038-R1-4',
     'The specification contradicts itself about reporting — §2b says the counter answers Q1, §10 says the question is deliberately unspecified',
     'v3 (48d0dc3), corrected v4: one contract — the counter on every return path of the ingest report; the MCP tool result STRIPS it with its operator-only siblings',
     '$PY -m pytest tests/test_0038_instruction_enforcement.py::test_both_carriers_the_report_counts_the_dropped_instruction tests/test_0038_instruction_enforcement.py::test_the_mcp_tool_result_strips_the_counter_with_its_siblings -q -p no:randomly'),
    ("0038", "external", 1, '0038-R1-5',
     '0037 not declared as a dependency',
     'v3 (48d0dc3): Spec-Requires 0037, with the consequence stated — §2b is correct only while V-EXTRACTOR-BLIND holds',
     'git show 48d0dc3 -- specs/0038-extraction-speech-act.md'),
    ("0038", "external", 1, '0038-R1-6',
     'The full-spec sections omitted for guarded surfaces (§4 field-consumer table, §3b authorization, §5 regime, §9 brief)',
     'v3 (48d0dc3): all four restored — prompts.py and ingest.py are GUARDED',
     'git show 48d0dc3 -- specs/0038-extraction-speech-act.md'),
    ("0038", "external", 1, '0038-P1',
     'collected_header.json promised by the reviewer guide, absent from the package',
     'f9379ab: the guide names both seal protocols and marks the header check not applicable to the two-seat hand-assembled chain; PIN.txt states the protocol',
     'git show f9379ab -- specs/REVIEWER_GUIDE.md'),
    ("0038", "external", 2, '0038-R2-1',
     'The document says the validation gate passed even though a mandatory condition (blind human labelling) was not met; naming a deviation does not make the gate pass',
     'v5.7 (a03d25d), on the owner\'s ruling "go with option 3": the §8 gate is NOT SATISFIED, its human condition UNMET, nothing substitutes; §6b-A is an explicitly weaker rule that is met; the withdrawn claim registered',
     'git show a03d25d -- specs/0038-extraction-speech-act.md'),
    ("0038", "external", 2, '0038-R2-2',
     'The claimed digest-token check is stronger than its implementation — a stale token matches nothing and is ignored',
     'v5.7 (a03d25d): a MEMBERSHIP test, described as one, with known_foreign_digests as data; R3-2 then made its control run the production validator',
     '$PY -m pytest tests/test_0038_oracle_pin.py::test_every_digest_token_beside_a_named_oracle_file_is_a_current_oracle_digest_or_declared_foreign tests/test_0038_oracle_pin.py::test_the_token_membership_check_rejects_a_planted_fabricated_token -q -p no:randomly'),
    ("0038", "external", 2, '0038-R2-3',
     'The cited validation-gate document is absent from the package',
     'v5.7 (a03d25d): VALIDATION_GATE-pseudonymised.md in the bound set — a derived copy, the original naming the owner in the rater role his ruling covers; R3-3 then narrowed its fidelity claim',
     '$PY -m pytest tests/test_0038_oracle_pin.py::test_every_listed_file_is_present_with_its_digest tests/test_0038_oracle_pin.py::test_every_present_file_is_listed -q -p no:randomly'),
    ("0038", "external", 2, '0038-R2-4',
     'Editorial duplication: the §4 heading appears twice consecutively',
     'DOES NOT REPRODUCE — the heading occurs once in the spec, the package copy and the tree copy (both seats); answered with counts in round 3 and RETRACTED by the reviewer in round 3 as a display artifact',
     'git show a03d25d -- specs/0038-extraction-speech-act.md'),
    ("0038", "external", 3, '0038-R3-1',
     'Current evidence artifacts still assert the withdrawn conclusion — the bound write-ups say the gate PASSES and the raters are independent; a reader following the evidence reaches the conclusion the spec withdrew',
     'v5.8/v5.9 (20a7103, 8588e55): supersession headers on the two write-ups; RUBRIC.md deliberately unamended (the instrument the rater was shown); the registry\'s changelog marked; SUPERSEDED-CONCLUSIONS.md bound and current, every entry a STATE; tests/test_oracle_set_disposition.py reads its JSON and holds the marker-or-exemption rule over every file (the first assembly of round 4 was discarded when the disposition itself proved stale)',
     '$PY -m pytest tests/test_oracle_set_disposition.py::test_the_disposition_holds_over_every_file_in_the_set tests/test_oracle_set_disposition.py::test_the_round_4_first_assembly_disposition_fails_this_checker -q -p no:randomly'),
    ("0038", "external", 3, '0038-R3-2',
     'The planted-digest test does not invoke the production membership check — it reconstructs the allowed-set logic, so the scanner could stop inspecting paragraphs while the control kept passing',
     'v5.8 (20a7103): one function, token_membership_violations, serves the real check and the control, which mutates the real spec body',
     '$PY -m pytest tests/test_0038_oracle_pin.py::test_the_token_membership_check_rejects_a_planted_fabricated_token tests/test_0038_oracle_pin.py::test_every_digest_token_beside_a_named_oracle_file_is_a_current_oracle_digest_or_declared_foreign -q -p no:randomly'),
    ("0038", "external", 3, '0038-R3-3',
     'Fidelity of the pseudonymised validation-gate copy to the absent original is not independently verifiable from the package',
     'v5.8 (20a7103): the claim NARROWED — the package carries a bound derived copy and cannot independently establish byte-level fidelity to an original it does not carry; shipping the original would publish the name the owner ruled out',
     'git show 20a7103 -- specs/0038-extraction-speech-act.md'),
    # ---- 0039 external rounds 1-4 (2026-09-09 → 2026-09-10) — the closure ledger written at acceptance (round 4, 2026-09-10). Executable closures cite the answer-shape transcript tests, the §6 table gate and the separated pin bindings by node; text-only closures cite the fold commit that landed the text (95fe67c the round-1 fold v8/v9, 749e122 v10, 3a470ee the round-2 fold v11, d2ef676 the round-3 fold v12).
    ("0039", "external", 1, '0039-R1-1',
     'The initial extraction path has unclassified outcomes; the specification incorrectly says a non-list triples raises AttributeError',
     'v8–v10 (95fe67c, 749e122): every primary and retry answer shape RUN through ingest_event on two independent instruments and kept as committed transcripts; ONE thirteen-row two-call-site matrix (§2c-ii) with every cell one classification and five asymmetric rows marked; two degrade kinds added; the wrong sentence replaced by the measurement (§1f)',
     '$PY -m pytest tests/test_0039_answer_shapes.py::test_the_answer_shape_transcript_is_the_scripts_output tests/test_0039_answer_shapes.py::test_researchs_independent_instrument_still_prints_its_transcript tests/test_0039_answer_shapes.py::test_a_planted_shape_changes_the_transcript'),
    ("0039", "external", 1, '0039-R1-2',
     'A failing callback can change the operation outcome; the invariant only covered a missing or unwritable reporter',
     'v8 (95fe67c): one guarded invocation helper `_emit_degrade` every site must use (Exception contained, BaseException deliberately not); V-CALLBACK-CONTAINED — a static census of direct calls and a raising callback at every one of the five sites with results and logical store contents equal to the None run (the fixture reworked at v11 after R2-2)',
     'git show 95fe67c -- specs/0039-degradation-visibility.md'),
    ("0039", "external", 1, '0039-R1-3',
     '"Never delays" conflicts with synchronous pre-authorised automatic reporting (a 15-second HTTP timeout in send)',
     'v8 (95fe67c), the first option: record_degrade writes one local line, increments the pending count and NEVER calls send(); V-NO-INLINE-SEND with record_error in the same configuration as the control',
     'git show 95fe67c -- specs/0039-degradation-visibility.md'),
    ("0039", "external", 1, '0039-R1-4',
     'The metadata disclosure contract needs tightening: length + unkeyed digest is not content-free; an exception class name is not a bounded vocabulary',
     'v8 (95fe67c): lengths are UTF-8 byte counts, digests SHA-256 over the stated bytes; the equality/guessing leakage ACKNOWLEDGED in §8 with the keyed alternative as Q5 and its reason; `cause` a closed six-value vocabulary, the class name never read; V-CAUSE-BOUNDED with a sentinel-carrying custom exception',
     'git show 95fe67c -- specs/0039-degradation-visibility.md'),
    ("0039", "external", 1, '0039-P1',
     'A retrospective gate invokes Git history, but the supplied git archive tree has no .git directory',
     'v9 (95fe67c): the live node SKIPS visibly where there is no repository, with a reason naming the third repository state and restating "a zero is not a pass"; registered in the skip inventory; the throwaway battery still runs',
     '$PY -m pytest tests/test_spec_gate.py::test_no_security_hotfix_obligation_is_past_its_date_without_a_declared_discharge_or_deferral tests/test_spec_gate.py::test_the_retrospective_derivation_owes_past_dates_closes_declared_ones_and_refuses_vacuity'),
    ("0039", "external", 2, '0039-R2-1',
     'The primary null/numeric/boolean outcome contradicts itself across §2a, §2c, row P6 and the matrix',
     'v11 (3a470ee): RECORD PLUS ERROR chosen deliberately and used everywhere; §2a defines "never raised"; the two records describe ONE call and the degrade record does not imply completion; V-RECORD-ORDER-ON-ERROR asserts count and order per row, conditional on a reporter',
     'git show 3a470ee -- specs/0039-degradation-visibility.md'),
    ("0039", "external", 2, '0039-R2-2',
     'The byte-identical callback test is not executable as written — independent ingestions generate random UUID identifiers',
     'v11 (3a470ee), reproduced first: a deterministic fixture stated in the spec (§2c-iii — a uid counter, the constructor clock= seam, fixed dates, a fresh store) and the comparison over canonical logical contents, never file bytes, with the identity-versus-equivalence distinction written in; v12 aligned the pseudocode to the shipped API',
     'git show 3a470ee -- specs/0039-degradation-visibility.md'),
    ("0039", "external", 2, '0039-R2-3',
     'Carrier-completeness drift: five passages still describe the superseded three-site / exception-type / two-battery / seven-shape design',
     'v11 (3a470ee): all five re-derived from the canonical five-site, six-cause, thirteen-row design, and two more found — the post-v9 sweep had searched for the new terms\' presence, not the old terms\' absence; the v11 sweep searched for absence',
     'git show 3a470ee -- specs/0039-degradation-visibility.md'),
    ("0039", "external", 3, '0039-R3-1',
     'The invariant table is structurally corrupted: the insertion of V-RECORD-ORDER-ON-ERROR split the V-DEGRADE-RECORDED row; add a structural gate',
     'v12 (d2ef676): the two rows restored as independent four-column rows; a §6 table-structure gate over every spec (escaped pipes and code spans respected) with a planted-split control; the gate\'s starting debt — six shorter rows in four accepted specs — recorded as a frozen set, an owner item',
     '$PY -m pytest tests/test_spec_gate.py::test_every_section_6_table_row_has_its_headers_cell_count tests/test_spec_gate.py::test_a_planted_split_row_is_caught_and_escaped_pipes_are_not'),
    ("0039", "external", 3, '0039-R3-2',
     'Archive execution skips the new transcript comparisons because the tests call the Git-history check first',
     'v12 (d2ef676): reproduction ALWAYS runs; the pin binding is its own test per transcript and skips only itself; proven in a bare git-archive copy (3 passed, 3 skipped by name)',
     '$PY -m pytest tests/test_0039_answer_shapes.py::test_the_answer_shape_transcript_is_the_scripts_output tests/test_0039_answer_shapes.py::test_devs_transcript_pin_describes_this_tree tests/test_0039_answer_shapes.py::test_researchs_transcript_pin_describes_this_tree tests/test_0039_answer_shapes.py::test_the_pin_binding_refuses_stale_foreign_and_unreachable_pins_and_names_the_two_skip_states'),
    ("0039", "external", 3, '0039-R3-3',
     'The deterministic fixture pseudocode does not match the shipped API (store.conn, "primary key", store._now)',
     'v12 (d2ef676): SqliteStore(":memory:", clock=…), the store\'s _conn seam, ORDER BY rowid declared as the current-schema rule, cursor-derived column names',
     'git show d2ef676 -- specs/0039-degradation-visibility.md'),
    ("0039", "external", 5, '0039-R5-1',
     '`unparseable` does not have the meaning claimed by X17: an all-invalid list stays indistinguishable from a legitimate empty for a default host, and the flag is set when usable triples are rejected by another top-level rule',
     "v16 (0025 v18, the owner's word 'Go with the new field'): the widening reverted; `extraction_unusable`, a bool on EVERY path, carries the outcome — no shape-valid triple, a legitimately empty list False; X12's set amended; the MCP result carries it, telemetry does not",
     '$PY -m pytest tests/test_0039_degradation_visibility.py::test_a_default_host_can_tell_a_malformed_answer_from_an_empty_one tests/test_0039_degradation_visibility.py::test_the_new_field_reaches_the_mcp_host_and_not_telemetry tests/test_0025_enforcement.py::test_public_counter_projection_is_exact'),
    ("0039", "external", 5, '0039-R5-2',
     'Aggregated records (member_skipped, volatility_defaulted) are emitted only after the storage loop and disappear when a later store operation fails',
     'v16: every degrade record is computed and emitted before the first effectful store operation — the volatility coercion as a pure pre-pass, the episode write moved below the emissions; store-failure tests at BOTH seams (edge write, episode write) for all three record kinds',
     '$PY -m pytest tests/test_0039_degradation_visibility.py::test_counted_records_are_written_before_the_first_store_write tests/test_0039_degradation_visibility.py::test_a_degrade_record_written_before_an_error_stays_before_it'),
    ("0039", "external", 6, '0039-R6-1',
     'The contract carriers contradict the implementation: the normative body of 0039, the Unreleased changelog and docs/api.md still state the superseded behaviour (non-list triples raise; a bare-array retry raises; the MCP result gained no field; no new result field)',
     "v17: every live sentence rewritten in place with the accepted text kept as marked history in the same cell; V-MCP-RESULT-UNCHANGED RETIRED and replaced by V-MCP-RESULT-CARRIES-ONE (the sixth frozen structure to move, the only one undisclosed, under a green inherited from a check of an adjacent claim); the CHANGELOG consolidated into one account; extraction_unusable in docs/api.md; three withdrawn-phrase entries registered for 0039 with a positive control, and a carrier test over the two host-facing files lint cannot read",
     '$PY -m pytest tests/test_0039_degradation_visibility.py::test_the_withdrawn_entries_for_this_spec_fire_on_a_marker_stripped_copy tests/test_0039_degradation_visibility.py::test_the_host_facing_carriers_state_the_current_contract tests/test_0039_degradation_visibility.py::test_the_new_field_reaches_the_mcp_host_and_not_telemetry'),
    ("0039", "external", 7, '0039-R7-1',
     'Live 0039 carriers still contradict the implementation in semantic variants the v17 register and carrier test did not reach (the prerequisite bullet, §2a, §4, §5, §8 twice, V-DEGRADE-RECORDED); the checks passed despite them',
     "v18: every remaining passage reconciled in place with verbatim OBSOLETE history; §2e made the ONE location for the result-surface claim and every other mention a POINTER naming location and subject, never value (the rule written in §2e); the register extended with the reviewer's variants and dev's; a spec-level binding RANKED — the closed pointer-site list asserted (each names §2e, none carries a value) as primary, a variant blocklist as backstop, incomplete by construction",
     '$PY -m pytest tests/test_0039_degradation_visibility.py::test_the_result_surface_is_stated_once_and_every_other_site_points_to_it tests/test_0039_degradation_visibility.py::test_the_withdrawn_entries_for_this_spec_fire_on_a_marker_stripped_copy'),
    ("0039", "external", 7, '0039-R7-2',
     'V-RESULT-UNCHANGED has the same defect as its retired MCP sibling: its own current text says the clean result gained a key; disclosure does not make an identifier meaning "unchanged" accurate',
     'v18: RETIRED as a struck row (still defined, OBSOLETE, the reason in its own words) and replaced by V-RESULT-SHAPE-EXACT, bound to X12\'s exact-set test — a test of the SAME claim, which the row says is the difference from the two retired ones',
     '$PY -m pytest tests/test_0025_enforcement.py::test_public_counter_projection_is_exact tests/test_spec_gate.py::test_no_spec_cites_an_invariant_it_does_not_define'),
    ("0039", "external", 8, '0039-R8-1',
     "The single-carrier rule is neither true nor fully checked: live sites outside §2e still state the value, and the test verifies eight hand-chosen anchors rather than the complete set — the verification's asserted domain is narrower than the document",
     "v19: the rule rewritten as a CRITERION — a site carries the value iff the value is what it asserts (§2e; §6 invariant rows; behaviour-table and matrix rows), every other site points; six discussions made value-free; the checker replaced by a DERIVED census over the live text with the history exclusions declared, each occurrence classified by its site's form, failing on the rest; the discussion pointers derived by subject vocabulary; the reviewer's mutation both ways",
     '$PY -m pytest tests/test_0039_degradation_visibility.py::test_the_result_surface_is_stated_once_and_every_other_site_points_to_it tests/test_0039_degradation_visibility.py::test_the_census_refuses_a_planted_restatement_and_admits_a_planted_invariant'),


    # ---- 0041 external rounds 1-8 (2026-09-15..17), the acceptance fold -----
    ("0041", "external", 1, "0041-R1-1",
     'the content-carrier inventory was incomplete: '
     '`Edge.original_relation` was classified non-content while ingestion '
     'preserves an unrecognised extractor relation there verbatim, and the '
     'reviewer confirmed it persists AND exports; two further omitted '
     'carriers did the same',
     'the inventory re-derived by a script that WALKS THE MODEL rather '
     'than a hand list, with its classification output committed beside it '
     'and reproduced byte-for-byte from the tree; v3.1 §2/§2d',
     '$PY -m pytest '
     'tests/test_0041_evidence.py::test_the_carrier_enumeration_reproduces_its_committed_output_byte_for_byte '
     'tests/test_0041_evidence.py::test_f1a_an_unrecognised_extractor_relation_is_kept_verbatim_in_original_relation '
     '-q -p no:randomly'),
    ("0041", "external", 1, "0041-R1-2",
     'clearing the wiki inside the redaction transaction does not prevent '
     'its later restoration — a compilation that BEGAN before the '
     'redaction republishes the original content, stamped with the current '
     'store version',
     '§4e: publication is conditional on the store version its inputs were '
     'read at, and redaction bumps that version; the delayed-writer '
     'treatment defined',
     'git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §4e — the '
     'version-conditional publication rule'),
    ("0041", "external", 1, "0041-R1-3",
     'redacted state and episode handling were underspecified, and the '
     'supporting claim was FALSE: `TEXT NOT NULL` permits the empty '
     'string, so it reserves nothing. §4c described only an edge journal '
     'event while §4a accepts an episode',
     "§4b defines the marker's representation and validation, §4c gains "
     'the durable episode record, and the reader inventory names '
     "`edge_state_at()`'s new REDACTED state instead of leaving a sentinel "
     'to classify as MALFORMED',
     'git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §4b/§4c/§6 '
     '— representation, the episode record, the reader state'),
    ("0041", "external", 1, "0041-R1-4",
     'D4 did not explain how affected supersession receipts are LOCATED: '
     '`supersession_operations` stores digests and an operation id with no '
     'complete reverse mapping to affected records',
     '§4f defines durable associations for future operations and '
     'CONSERVATIVE completeness reporting for existing unlinked receipts — '
     'the limit is stated as a guarantee (`receipts_complete=False`) '
     'rather than claimed away',
     'git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §4f — '
     'durable association and conservative reporting'),
    ("0041", "external", 1, "0041-R1-5",
     'exporting redaction events needed a complete IMPORT contract: '
     'record/event binding, missing or inconsistent notices, repeat '
     'imports, user remapping, destination conflicts, and the treatment of '
     'source `seq`/`txn`',
     '§4g, the acceptance contract for a transport that does not yet exist '
     '— export carries no events at all today, which the spec now states '
     'rather than assumes',
     'git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §4g — the '
     'import contract and its failure cases'),
    ("0041", "external", 1, "0041-R1-6",
     'the scope of dependent content was an open PRODUCT question: §10.1 '
     'left consolidated outputs unresolved, so a caller could not know '
     'what remained after a successful redaction',
     "THE OWNER'S RULING — outputs are separate; §10.1 and §8 state it, "
     'and §11.5 limits the success claim accordingly, naming surviving '
     'copies in the receipt',
     'git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §10.1/§8 — '
     "the owner's ruling, outputs are separate"),
    ("0041", "external", 1, "0041-R1-7",
     "the owner's four decisions had not reached the operative contract "
     'consistently — four live passages still contradicted them (D1 '
     "against §2c's length-capped prose; D2 against INV-6 and §10; §2's "
     "three duplicated columns against INV-2; 'no row is deleted' against "
     'deleting wiki, embedding and ledger rows)',
     '§11, one consolidated current contract that GOVERNS where anything '
     'above it conflicts, with the historical discussion moved out',
     'git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §11 — the '
     'operative contract and its precedence rule'),
    ("0041", "external", 2, "0041-R2-1",
     'the semantic-rebuild exemption did not hold ACROSS DATABASE '
     'CONNECTIONS: `upsert_embedding()` read and checked the live edge '
     'under an instance-local lock with no transaction, so a second '
     "connection's redaction was overwritten. Separately the INV-12 test "
     'still passed when `embedded_text()` was widened onto an optional '
     'field its fixture left UNSET',
     '§4e requires validation and publication to be atomic against other '
     'CONNECTIONS, and the exemption is withdrawn; the INV-12 fixture '
     'populates every string leaf and each optional leaf carries a control '
     'proving a widening onto it is caught',
     '$PY -m pytest '
     'tests/test_0041_evidence.py::test_two_connection_publication_the_embedding_upsert_refuses_a_vector_for_content_another_connection_replaced '
     'tests/test_0041_evidence.py::test_inv12_each_optional_leaf_is_load_bearing_a_widening_onto_it_is_missed_when_it_is_unset '
     '-q -p no:randomly'),
    ("0041", "external", 2, "0041-R2-2",
     'the tombstone was not reserved by the stated mechanism — the marker '
     'survives `sanitize_llm_body()`, ordinary ingestion and storage, so '
     'the claim that a leading NUL makes it unproducible was false; nested '
     'replacement shapes were undefined and broke an existing uniqueness '
     'validator',
     '§4b: the marker is NOT reserved by a column constraint, reservation '
     "is INV-11's mirror at the write and import boundaries, and the "
     'nested shapes carry valid post-redaction representations',
     'git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §4b — '
     'reservation as a rule, not a claim about a column'),
    ("0041", "external", 2, "0041-R2-3",
     'the five-value reason vocabulary conflicted with existing lifecycle '
     "behaviour: all seven of the store's disposition reasons were "
     'excluded, so enforcing it would reject normal writes, and calling '
     'them `legacy_freeform` would discard distinctions historical '
     'classification and cache handling use',
     '§11.2 scopes permitted reasons BY OPERATION and preserves existing '
     'lifecycle meanings, separating migration-time retention from '
     'redaction-time removal',
     'git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §11.2 — '
     'reasons per operation'),
    ("0041", "external", 2, "0041-R2-4",
     'import failure row 9 rejected an event with an invalid reason but '
     'imported its record UN-REDACTED — the content arrived without the '
     'instruction to remove it',
     '§4g rules the dependent record-and-notice unit as ONE: it is '
     'rejected together or the import fails explicitly; the adjacent cases '
     "(notice-less tombstone, inconsistent notices, the idempotency key's "
     '`event_id`) are completed',
     'git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §4g — the '
     'record and its notice commit together'),
    ("0041", "external", 2, "0041-R2-5",
     'receipt selection was incomplete for CURRENT-format operations too: '
     'a reproduced `prior_upserts` update left no contribution or refusal '
     'row linking the target to the operation, and step 2 could not locate '
     'an id in the current `response`',
     'the exact-coverage claim is WITHDRAWN; §4f reports completeness '
     'conservatively and the receipt no longer copies a removed content '
     'digest into itself',
     'git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §4f — the '
     'withdrawn coverage claim'),
    ("0041", "external", 2, "0041-R2-6",
     'the expanded inventory still lacked a complete treatment map — 64 '
     'candidates discovered, none of them told what happens to it; a prose '
     '`outcome_counts` KEY was confirmed to persist and export, and §2 and '
     'the example disagreed about `provenance.evidence_ref`',
     '§2d-iii-bis, the 64-row per-candidate map built by both seats: '
     'replace, clear, delete, preserve or explicitly exclude, each with '
     'its resulting shape',
     'git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §2d-iii-bis — '
     'the 64-row treatment map'),
    ("0041", "external", 2, "0041-R2-7",
     '§11 did not provide a consistent invariant contract: it re-pointed '
     'EXISTING identities (INV-1 from structure preservation to content '
     'absence, INV-3 from `why` behaviour to atomicity), dropped INV-4 and '
     'INV-5, and described all 64 candidates as the removal surface while '
     '§2d said they are not all targets',
     "§11.3 restores §6's meanings, new properties take NEW identifiers, "
     'and the matrix is one complete current table with its checks',
     'git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §11.3 — '
     'stable invariant identities'),
    ("0041", "external", 3, "0041-R3-1",
     'replacing `Episode.kind` broke outcome-history protection: simulated '
     'on a real outcome record the model still VALIDATED, but the chain '
     'head disappeared, the next append restarted at sequence 1, and '
     'targeted deletion of the original was no longer refused — five '
     'guards read that discriminator',
     'row 46 becomes two branches — PRESERVE a recognised operational '
     'kind, REPLACE prose — with the recognised set closed by a refusal '
     'rather than by convention',
     '$PY -m pytest '
     'tests/test_0041_treatment_matrix.py::test_row46_the_two_branch_kind_treatment_keeps_the_outcome_chain_and_its_guards '
     'tests/test_0041_treatment_matrix.py::test_row46_the_replace_branch_applies_to_prose_only '
     '-q -p no:randomly'),
    ("0041", "external", 3, "0041-R3-2",
     'marker, migration and absence handling were still incomplete: §4b '
     "left pre-existing marker values 'not yet ruled', §4b and §4g "
     'contradicted each other over a notice-less tombstone, and `None`, a '
     'legitimate empty value, ordinary text and a redacted value were not '
     'distinguished',
     "§2d-v's absence rules — None stays None, empty stays empty — and "
     "§4b's ruling on pre-existing markers as unattested rather than "
     'forbidden',
     'git show ef46d4a4cb80e5c86f672a0f76b162d46eea0d63 # v6 §2d-v/§4b — '
     'the absence rules and the migration ruling'),
    ("0041", "external", 3, "0041-R3-3",
     'the corrected reason contract named the WRONG existing vocabulary: a '
     "twelve-value list against the journal writer's seven-value "
     '`DISPOSITIONED_REASONS`, omitting `disputed`, `revoked_source` and '
     'others',
     '§11.2 REFERENCES `schema.DISPOSITIONED_REASONS` instead of re-typing '
     'it — a list copied into prose is a list that drifts — and defines '
     'the other reason-writing operations separately, splitting '
     'retain-at-migration from remove-at-redaction',
     'git show ef46d4a4cb80e5c86f672a0f76b162d46eea0d63 # v6 §11.2 — the '
     'registry referenced, not retyped'),
    ("0041", "external", 3, "0041-R3-4",
     'the supposedly authoritative sections still disagreed about '
     'treatment: rows 21 and 23 retained contribution-ledger rows and '
     'cleared their digests while §11.1 said deletion governs, and the '
     'example receipt cleared a field the map preserves',
     'one current contract with EXPLICIT PRECEDENCE — §11 governs on '
     'contract, §2d-iii-bis on per-carrier treatment — and the example '
     'corrected to the map',
     'git show ef46d4a4cb80e5c86f672a0f76b162d46eea0d63 # v6 '
     '§11.1/§2d-iii-bis — precedence stated'),
    ("0041", "external", 3, "0041-R3-5",
     'the evidence OVERSTATED its validation and field coverage: fixtures '
     'labelled VALID used `model_copy(update=...)`, which skips validation '
     'of the updates, and the revised INV-12 fixture still passed a '
     'widening onto an unset `invalidation_reason`',
     'every fixture is validated through the applicable model AND the '
     "operation's own checks, with the two refusals printed as results; "
     "INV-12 is generated from the model's field walk with a per-leaf "
     'control',
     '$PY -m pytest '
     'tests/test_0041_evidence.py::test_the_before_after_fixtures_validate_as_the_treatment_map_rules_them '
     'tests/test_0041_evidence.py::test_inv12_catches_a_widened_embedder_the_packaged_fixture_missed '
     '-q -p no:randomly'),
    ("0041", "external", 4, "0041-R4-1",
     'the marker decisions the README reported as completed were still '
     "missing: §4b labelled pre-existing marker values 'OWED AND NOT YET "
     "RULED' and legitimate empty values 'still owed', §4g accepted a "
     'marker-only record without a notice while §4b prohibited marker '
     'introduction, and repeat handling promised an original receipt a '
     'record may never have had',
     "v9's ATTESTATION RULE, which answers all four at once: a field is "
     'redacted iff a redaction record names that record and that field — '
     'so a pre-existing marker is an unattested marker, writable and '
     'reported, and a repeat returns the original OR a reconstructed '
     'receipt',
     'git show 7db9987b980505d8a7f57bbdf05499f41c690c31 # v9 §4b — the '
     'attestation rule'),
    ("0041", "external", 4, "0041-R4-2",
     'the new restrictions did not settle compatibility with records '
     'ALREADY STORED: a stored relation-only quarantine loses its '
     'quarantine under the treatment map, and existing prose-valued kinds '
     'had no transition policy',
     "§4h's re-establish-or-refuse rule, and an EXECUTABLE transition "
     'table over records written before the restrictions — the write-path '
     'refusal and the transition rule are two halves of one property',
     '$PY -m pytest '
     'tests/test_0041_transition_table.py::test_A_existing_relation_only_quarantine_keeps_its_quarantine_under_the_ruled_treatment '
     'tests/test_0041_transition_table.py::test_A_control_the_naive_treatment_promotes_the_claim '
     '-q -p no:randomly'),
    ("0041", "external", 4, "0041-R4-3",
     '§11.2 still described the reason fields incorrectly: the journal '
     'already enforces `DISPOSITIONED_REASONS` for invalidation events, so '
     "its closure is not 'nothing today', and `revoked_source` does not "
     'define the vocabulary of `source_revocations.reason` — the '
     "revocation row retained the caller's sentence",
     '§11.2 states the allowed values and enforcement PER D1 REASON FIELD, '
     'including `source_revocations.reason` and `Episode.retired_reason`, '
     'and extends the existing journal rule to redaction events',
     'git show 7db9987b980505d8a7f57bbdf05499f41c690c31 # v9 §11.2 — '
     'per-field reason contract'),
    ("0041", "external", 4, "0041-R4-4",
     'INV-12 still missed DICTIONARY KEYS: `_inv12_sets` changed values '
     'and not keys, so with `embedded_text` widened onto `outcome_counts` '
     'keys all seven fixture/control cases passed although the embedding '
     'text changed and the content digest did not',
     'the generator mutates keys as well as values and asserts directly '
     'against the production projections, keeping the optional-field '
     'controls',
     '$PY -m pytest '
     'tests/test_0041_evidence.py::test_inv12_catches_a_widened_embedder_onto_dictionary_keys '
     'tests/test_0041_evidence.py::test_inv12_the_embedder_sees_no_field_the_content_digest_does_not_cover '
     '-q -p no:randomly'),
    ("0041", "external", 5, "0041-R5-1",
     "row 49 still changed an ACTIVE episode's disposition: "
     'preserve-registered, else `"redacted"`, never NULL turned '
     '`retired_reason=None, active=True` into `"redacted", active=False` — '
     'a redaction RETIRING an active episode, which §4h forbids and which '
     "the previous round's own fix introduced",
     "§4h's corollary — REDACTION ACTS ON CONTENT; ABSENCE IS NOT CONTENT "
     '— so every carrier rule is three cases: absent stays absent, '
     'registered stays registered, only prose becomes the registry value',
     '$PY -m pytest '
     'tests/test_0041_transition_table.py::test_rows30_49_on_a_frozen_record_absence_survives_and_prose_does_not '
     'tests/test_0041_treatment_matrix.py::test_rows30_49_absence_stays_absence_a_none_reason_is_not_replaced '
     '-q -p no:randomly'),
    ("0041", "external", 5, "0041-R5-2",
     'the source-revocation rule changed D1 without recording a '
     'replacement decision: D1 puts `source_revocations.reason` under a '
     'closed vocabulary and §11.2 treated it as continuing free text. '
     'Removing historical prose does not constrain what future writes may '
     'store — two separate questions',
     '§11.2 separates the restriction on FUTURE writes from the treatment '
     'of historical prose, and the field closes for future writes without '
     'amending D1',
     'git show ead0bcc93301b42f7e2ae19f684c49bae8e9882e # v11 §11.2 — '
     'future writes and historical prose separated'),
    ("0041", "external", 5, "0041-R5-3",
     'three strict xfails did not exercise the behaviour their names '
     'promised — the repeated-call test passed against a no-op '
     '`Memory.redact`, the migration-report test against a helper that '
     'always returned `[]`, and the after-attestation test never called '
     'redaction at all. Existence checks wearing behaviour names',
     'the three rewritten to bind VALUES the product computes, the class '
     'exhausted by our own mutant campaign, and POSITIVE CONTROLS added — '
     'the after-attestation test could never have been made green by any '
     'implementation, which no negative control can reveal',
     '$PY specs/evidence/0041/xfail_mutant_campaign.py'),
    ("0041", "external", 6, "0041-R6-1",
     'several transition tests still created their historical records '
     'through ORDINARY WRITERS, so three of them fail at SETUP once the '
     'proposed restrictions land; the fixture lacked a historical '
     'source-revocation row with a prose reason, and the row-46 test still '
     'expected the `Episode` CONSTRUCTOR to reject a prose kind, '
     "contradicting §4h's requirement that existing records stay readable",
     'a FROZEN pre-restriction store, written before the closure and '
     'checked against its manifest, which the transition tests copy '
     'instead of writing rows a landed closure would refuse; the refusal '
     'moved from the constructor to the write path',
     '$PY -m pytest '
     'tests/test_0041_transition_table.py::test_the_frozen_store_carries_every_pre_restriction_shape_the_table_needs '
     'tests/test_0041_transition_table.py::test_B_existing_prose_kind_is_retained_at_migration_and_readable '
     '-q -p no:randomly'),
    ("0041", "external", 6, "0041-R6-2",
     "the fixture-checker's test invoked the checker only on the ORIGINAL "
     'bytes and compared sha256 digests for the altered copy — a property '
     'of sha256, not of the checker. Replacing the subprocess result with '
     'unconditional success left the test passing: an unfailable check '
     'guarding the artifact whose whole value is that it has not changed',
     'the checker is RUN on the altered bytes in a throwaway copy of its '
     'own directory, and the rejection is read from ITS exit code and ITS '
     "message; the README's both-directions claim corrected",
     '$PY -m pytest '
     'tests/test_0041_transition_table.py::test_the_frozen_pre_restriction_store_matches_its_manifest '
     '-q -p no:randomly'),
    ("0041", "external", 6, "0041-R6-3",
     'the source-revocation vocabulary was still marked PROPOSED — '
     '`policy`, `subject_request`, `erroneous_capture` and '
     '`legal_obligation` — with older summaries still implying the field '
     'stays permanently free text',
     "THE OWNER'S RULING, folded as authorised rather than proposed: the "
     'four values are final, `policy` is defined, and the superseded '
     'summaries are DATED as historical rather than erased',
     'git show e0cba0aac04ff48adc8a28befc96648a65e47a60 # v12 §11.2 — the '
     'vocabulary authorised, not proposed'),
    ("0041", "external", 7, "0041-R7-1",
     'historical-data setup still used restricted writers: the prose-kind '
     'test wrote `ep-old` through the ordinary writer and would fail at '
     'setup under the proposed restriction, never reaching its assertion; '
     'the source-reason test created a new prose reason; and the frozen '
     "revocation had no linked record for the test's affected-records "
     'assertion',
     'both tests read frozen records, and the fixture gains a '
     'source-linked edge so the affected-records assertion has something '
     'to be about',
     '$PY -m pytest '
     'tests/test_0041_transition_table.py::test_B_an_ordinary_write_of_a_new_prose_kind_is_refused_while_the_stored_one_stays '
     'tests/test_0041_transition_table.py::test_D_a_source_revocation_reason_holding_the_callers_sentence_is_replaced '
     '-q -p no:randomly'),
    ("0041", "external", 7, "0041-R7-2",
     'the revised import test could pass FOR THE WRONG REASON: it exported '
     'the entire mixed fixture including marker-bearing rows, so an import '
     'rule that rejected markers and performed no kind validation at all '
     'made it pass',
     'the prose-kind case is exported in ISOLATION, so no other '
     'restriction can satisfy its expected rejection — and a control '
     'asserts the isolated export carries no marker to reject',
     '$PY -m pytest '
     'tests/test_0041_transition_table.py::test_B_an_import_carrying_a_prose_kind_is_refused '
     'tests/test_0041_transition_table.py::test_the_isolation_control_detects_a_marker_bearing_export '
     '-q -p no:randomly'),
    ("0041", "external", 7, "0041-R7-3",
     'the redaction adapter disagreed with §4a: it passed `kind`, '
     '`target_id` and `fields` where §4a specifies a user, an '
     'edge-OR-episode target and a reason, so a callable with the '
     'documented signature failed the repeat test immediately',
     'the adapter takes `user_id`, exactly one of `edge_id | episode_id` — '
     'asserted, never both and never neither — and `reason`, matching §4a',
     '$PY -m pytest '
     'tests/test_0041_transition_table.py::test_F_a_repeated_call_returns_the_original_or_a_reconstructed_receipt '
     '-q -p no:randomly'),
    ("0041", "external", 8, "0041-R8-1",
     "NONBLOCKING FOLLOW-UP. The isolation control searched the export's "
     'RAW TEXT for a marker whose NUL bytes JSON escapes to `\\u0000`, so '
     'the assertion was true of every JSON export ever written — a file '
     "full of markers passed it. The campaign's import mutant had the same "
     'defect, so it simulated a rule that does nothing',
     'the check DECODES and walks every string value and dictionary key, '
     'returns the list so a failure names what it found, and reads record '
     "lines only because the export's metadata header carries a kind of "
     'its own; demonstrated rather than claimed, on a marker-bearing '
     'export',
     '$PY -m pytest '
     'tests/test_0041_transition_table.py::test_the_isolation_control_detects_a_marker_bearing_export '
     '-q -p no:randomly'),
    ("0041", "external", 8, "0041-R8-2",
     "NONBLOCKING FOLLOW-UP. §11.4-bis's evidence references were stale in "
     'five figures: ten campaign cases where the file holds 14, a '
     'nine-shape fixture where the manifest holds 10, and a superseded '
     'digest and creation pin',
     'the five figures corrected AND bound — a test DERIVES each one from '
     "the artifact it describes (the campaign's `check()` calls by AST, "
     "the manifest's rows, the store's sha256, the recorded HEAD) and "
     'fails if the section disagrees, so the class cannot recur silently',
     '$PY -m pytest '
     'tests/test_0041_evidence.py::test_the_11_4_bis_evidence_figures_are_derived_from_the_artifacts_they_cite '
     '-q -p no:randomly'),
    # ---- 0041 external rounds 9-13: THE IMPLEMENTATION REVIEW (accepted at round 14, 2026-10-06); every closure behavioural ----
    ('0041', 'external', 9, '0041-R9-01',
     "an ordinary episode write could restore attested-redacted content: the attestation and reservation checks ran outside the writer's own transaction",
     "round 10 (6f419ff): the attestation and reservation checks run inside add_episode's own BEGIN IMMEDIATE",
     "$PY -m pytest tests/test_0041_round10_txn.py::test_R9_01_blocked_the_redaction_waits_for_the_write_then_treats_what_it_wrote tests/test_0041_round10_txn.py::test_R9_01_sequential_a_redaction_committed_before_the_write_begins_is_seen_and_refuses tests/test_0041_round10_txn.py::test_R9_01_control_ordinary_episode_writes_still_work -q -p no:randomly"),
    ('0041', 'external', 9, '0041-R9-02',
     "two D1 reason closures were absent (revoke_source and Episode.retired_reason accepted prose; the sweep added Edge.invalidation_reason), and historical source-revocation reason prose survived a real redaction",
     "round 10 (19066f4, 90bbe5c, eabd89d): the owner's revocation and lift reason lists checked in preview and commit; a present retired or invalidation reason must be registered; redact treats source_revocations.reason through the one admitted updater (a 0022 amendment); the named tests invoke the operation they test",
     "$PY -m pytest tests/test_0041_round10_reasons.py::test_a_revoke_with_prose_refuses_in_preview_and_in_commit_and_writes_nothing tests/test_0041_round10_reasons.py::test_a_a_lift_outside_the_lift_list_refuses_in_preview_and_commit_and_writes_nothing tests/test_0041_round10_reasons.py::test_a_revoked_in_error_is_a_lift_reason_and_not_a_revoke_reason tests/test_0041_round10_reasons.py::test_b_a_present_retired_reason_must_be_registered_none_stays_valid tests/test_0041_round10_reasons.py::test_the_closure_binds_the_import_boundary tests/test_0041_round10_reasons.py::test_c_the_re_upsert_to_invalidated_with_prose_refuses_and_the_stored_row_is_unchanged tests/test_0041_round10_reasons.py::test_d_the_frozen_stores_prose_revocation_is_treated_by_the_real_redaction tests/test_0041_transition_table.py::test_D_a_source_revocation_reason_holding_the_callers_sentence_is_replaced tests/test_0041_round10_reasons.py::test_a_revoke_with_each_of_the_owners_four_reasons_commits tests/test_0041_round10_reasons.py::test_a_a_lift_with_each_lift_reason_commits tests/test_0041_round10_reasons.py::test_stored_legacy_prose_still_loads_the_closure_never_binds_the_read_path tests/test_0041_round10_reasons.py::test_c_every_registered_reason_is_accepted_the_closure_is_the_registry_not_a_list tests/test_0041_round10_reasons.py::test_d_the_standing_state_is_identical_before_and_after_the_treatment_across_revoke_lift_revoke -q -p no:randomly"),
    ('0041', 'external', 9, '0041-R9-03',
     "the contribution-ledger treatment omitted episodes and matched ids without their target kind",
     "round 10 (ba6f88f): the ledger digests cleared in both target branches, joined by user, kind and id, in both absorption directions",
     "$PY -m pytest tests/test_0041_round10_matrix.py::test_the_real_redaction_treats_the_carrier_as_the_map_rules tests/test_0041_round10_matrix.py::test_the_mirror_redacting_an_edge_leaves_a_same_id_episode_ledger_intact -q -p no:randomly"),
    ('0041', 'external', 9, '0041-R9-04',
     "durable notice deduplication lost the destination scope and the body's integrity: a repeat with a different body was accepted as existing",
     "round 10 (81c68d4, 6af44ee): notice_id binds origin, source user, source event, destination user and typed target; the canonical foreign body is persisted and compared on every repeat, across remaps; a contradiction refuses the whole import",
     "$PY -m pytest tests/test_0041_round10_notices.py::test_R9_04_one_notice_imported_for_two_destination_users_attests_each_users_own_record tests/test_0041_round10_notices.py::test_R9_04_a_later_contradictory_body_under_the_same_identity_refuses_atomically tests/test_0041_round10_notices.py::test_S2_1_a_remapping_import_with_a_contradictory_body_is_refused_atomically tests/test_0041_round10_notices.py::test_S2_1_the_same_contradiction_across_two_destination_users_is_refused tests/test_0041_round10_notices.py::test_R9_04_an_honest_repeat_is_idempotent_and_writes_nothing tests/test_0041_round10_notices.py::test_S2_1_control_remapping_twice_with_an_equal_body_is_not_refused -q -p no:randomly"),
    ('0041', 'external', 9, '0041-R9-05',
     "witnessed receipts and relayed notices did not retain the source's provenance: the destination's application facts overwrote the source's",
     "round 10 (81c68d4): the two-fact receipt — the source's reason, times, versions and event reference, None where the notice does not carry them, beside this store's applied_* facts; a re-export passes the source body on unchanged",
     "$PY -m pytest tests/test_0041_round10_notices.py::test_R9_05_a_witnessed_receipt_reports_the_sources_facts_and_this_stores_application_beside_them tests/test_0041_round10_notices.py::test_R9_05_the_original_and_its_honest_relay_are_one_notice_together_or_in_sequence tests/test_0041_round10_notices.py::test_R9_05_facts_the_notice_does_not_carry_are_None_and_serialise_as_null tests/test_0041_round10_notices.py::test_R9_05_a_relay_that_alters_the_body_is_refused -q -p no:randomly"),
    ('0041', 'external', 9, '0041-R9-06',
     "an attested marker-valued episode kind could not round-trip through export and import",
     "round 10 (81c68d4): the kind closure admits the marker when the same import unit attests kind, including by a standing notice; raw prose and unaccounted markers still refused",
     "$PY -m pytest tests/test_0041_round10_notices.py::test_R9_06_the_treated_historical_prose_kind_episode_round_trips_with_its_notice tests/test_0041_round10_notices.py::test_R9_06_a_standing_notice_admits_the_marker_kind_when_the_record_arrives_later tests/test_0041_round10_notices.py::test_R9_06_the_closure_still_refuses_what_no_attestation_accounts_for -q -p no:randomly"),
    ('0041', 'external', 9, '0041-R9-07',
     "semantic backfill recreated embeddings for attested-redacted edges",
     "round 10 (aa7472f): backfill excludes redacted targets at its read, and the upsert's digest guard refuses a vector for content replaced during the embed call",
     "$PY -m pytest tests/test_0041_round10_readers.py::test_R9_07_an_attested_edge_is_skipped_and_its_tombstone_never_reaches_the_embedder tests/test_0041_round10_readers.py::test_R9_07_a_redaction_during_the_embed_call_is_refused_by_the_digest_guard_at_the_upsert tests/test_0041_round10_readers.py::test_R9_07_an_unattested_marker_row_follows_its_own_contract_and_is_embedded -q -p no:randomly"),
    ('0041', 'external', 9, '0041-R9-08',
     "a notice's field names admitted arbitrary prose rather than the kind's carrier paths",
     "round 10 (81c68d4): the field domain is the declared kind's carrier paths, derived from the treatment tables, checked at the parser and at the commit primitive",
     "$PY -m pytest tests/test_0041_round10_notices.py::test_R9_08_notice_field_names_are_the_kinds_carrier_paths tests/test_0041_round10_notices.py::test_R9_08_the_commit_primitive_refuses_prose_field_names_on_its_own tests/test_0041_round10_notices.py::test_R9_08_the_allowed_set_is_derived_from_the_treatment_tables -q -p no:randomly"),
    ('0041', 'external', 10, '0041-R10-01',
     "a full export carrying a newly redacted outcome could not apply its notice to a destination holding the earlier outcome",
     "round 11 (9f37287): one held-differs rule for edges, episodes and outcome links (portability.held_differs_verdict); an outcome's structural difference refuses, notice or not",
     "$PY -m pytest tests/test_0041_round11_outcome.py::test_R10_01_full_export_applies_notice_to_held_outcome tests/test_0041_round11_outcome.py::test_A2_an_already_treated_held_outcome_meeting_its_old_record_ends_existing_with_no_new_event tests/test_0041_round11_outcome.py::test_outcome_and_interaction_give_the_same_result_for_the_same_difference tests/test_0041_round11_outcome.py::test_the_treated_held_outcome_keeps_its_chain tests/test_0041_round11_outcome.py::test_control_a_changed_outcome_with_no_notice_still_refuses tests/test_0041_round11_outcome.py::test_control_a_topology_conflict_refuses_notice_or_not -q -p no:randomly"),
    ('0041', 'external', 10, '0041-R10-02',
     "after a treated interaction episode was deleted, import could restore its content and skip treatment because its notice was already applied",
     "round 11 (d812059): treat on arrival — a record arriving under a completed attestation with its notice is written as the pure treatment, no new event or attestation; without a notice it refuses",
     "$PY -m pytest tests/test_0041_round11_arrival.py::test_R10_02_public_import_cannot_repopulate_a_deleted_attested_episode tests/test_0041_round11_arrival.py::test_a_backup_taken_after_the_redaction_restores_after_a_delete tests/test_0041_round11_arrival.py::test_an_honest_full_backup_of_several_redacted_episodes_restores_after_one_is_deleted tests/test_0041_round11_arrival.py::test_an_arrival_needing_treatment_in_a_carrier_the_attestation_never_named_is_refused tests/test_0041_round11_arrival.py::test_control_re_arrival_without_a_notice_still_refuses tests/test_0041_round11_arrival.py::test_control_an_ordinary_write_of_the_deleted_attested_episode_is_refused tests/test_0041_round11_arrival.py::test_notice_only_after_the_delete_inserts_nothing -q -p no:randomly"),
    ('0041', 'external', 10, '0041-R10-03',
     "the notice identity was not injective over the admitted identifier domain: control characters in source identifiers broke identity separation, relay provenance and the body comparison",
     "round 11 (9b0d0a4): the source identity is three structured columns compared exactly; the row id is a length-framed sha256 over the six components; an empty or non-string component refused at both boundaries",
     "$PY -m pytest tests/test_0041_round11_identity.py::test_R10_03_a_two_source_triples_that_encoded_equal_are_two_standing_notices tests/test_0041_round11_identity.py::test_R10_03_b_a_relay_preserves_the_native_source_triple tests/test_0041_round11_identity.py::test_R10_03_c_a_changed_body_under_the_same_source_identity_refuses tests/test_0041_round11_identity.py::test_R10_03_c_the_comparison_crosses_a_destination_remap_for_a_NUL_identity tests/test_0041_round11_identity.py::test_the_row_id_is_injective_over_each_component tests/test_0041_round11_identity.py::test_control_an_equal_body_remapped_twice_is_not_a_contradiction -q -p no:randomly"),
    ('0041', 'external', 10, '0041-R10-04',
     "a successful public redaction with the reason imported_notice produced an export the importer rejected: the reason text decided provenance",
     "round 11 (132193b): provenance is a record fact; on the owner's ruling Memory.redact refuses imported_notice and a notice's own reason must be an originating one",
     "$PY -m pytest tests/test_0041_round11_provenance.py::test_R10_04_memory_redact_refuses_imported_notice_before_any_write tests/test_0041_round11_provenance.py::test_R10_04_a_LOCAL_row_holding_the_witness_label_still_reads_local tests/test_0041_round11_provenance.py::test_R10_04_a_notice_whose_own_reason_is_the_witness_label_is_refused tests/test_0041_round11_provenance.py::test_R10_04_every_admitted_local_reason_round_trips tests/test_0041_round11_provenance.py::test_control_a_genuine_imported_notice_keeps_the_sources_facts -q -p no:randomly"),
    ('0041', 'external', 11, '0041-R11-01',
     "redacting an edge with the quarantine relation emitted a notice the importer rejected, so a destination holding the earlier edge kept its content",
     "round 12 (1b8d875): one domain for a notice's fields, read by the writer, the parser and the commit primitive — the kind's carrier paths plus a closed, named set of bookkeeping paths",
     "$PY -m pytest tests/test_0041_round12_quarantine.py::test_R11_01_quarantine_redaction_export_applies_to_held_target tests/test_0041_round12_quarantine.py::test_a_destination_holding_the_relation_only_shape_moves_and_attests_its_own_disclosure tests/test_0041_round12_quarantine.py::test_the_notice_domain_stays_closed -q -p no:randomly"),
    ('0041', 'external', 11, '0041-R11-02',
     "the nothing-to-redact check refused an empty live edge whose journal and confirmation row still held carriers requiring treatment",
     "round 12 (7fae0f8): the nothing-to-redact decision moved to the end of the treatment, over the record, its side tables, its journal and the linked revocation prose, inside the caller's transaction",
     "$PY -m pytest tests/test_0041_round12_surface.py::test_R11_02_empty_live_record_with_retained_carriers_can_be_redacted tests/test_0041_round12_surface.py::test_R11_02_the_confirmation_digest_of_an_emptied_edge_is_treated tests/test_0041_round12_surface.py::test_the_ledger_digests_of_an_emptied_survivor_are_treated tests/test_0041_round12_surface.py::test_a_history_only_redaction_exports_a_notice_another_store_applies tests/test_0041_round12_surface.py::test_a_record_with_nothing_anywhere_is_still_refused_with_nothing_written tests/test_0041_round12_surface.py::test_control_a_populated_edge_treats_its_journal_and_its_digest tests/test_0041_round12_surface.py::test_a_notice_WITHOUT_the_journal_path_still_treats_the_destinations_journal -q -p no:randomly"),
    ('0041', 'external', 11, '0041-R11-03',
     "the source-body comparison omitted redactions originated by the destination itself, so a contradictory notice was accepted",
     "round 12 (bbd71d1): one canonical source projection for every redaction row, witnessed or native, used by both the export and the body comparison",
     "$PY -m pytest tests/test_0041_round12_native.py::test_R11_03_contradiction_with_native_source_event_refuses_atomically tests/test_0041_round12_native.py::test_the_stores_own_event_relayed_back_honestly_is_existing_not_a_second_row tests/test_0041_round12_native.py::test_two_native_events_of_one_user_are_compared_each_against_its_own tests/test_0041_round12_native.py::test_the_export_and_the_comparison_share_one_projection tests/test_0041_round12_native.py::test_control_the_stores_own_export_re_imported_is_existing tests/test_0041_round12_native.py::test_control_a_witnessed_contradiction_still_refuses tests/test_0041_round12_native.py::test_a_self_import_under_a_remap_attests_the_copy_as_a_witnessed_row tests/test_0041_round12_native.py::test_a_foreign_origin_never_compares_against_a_native_row -q -p no:randomly"),
    ('0041', 'external', 11, '0041-N11-01',
     "NONBLOCKING wording correction: v15.1 §4g's held-differs parenthesis stated a narrower predicate (the difference lies in the notice's fields) than the rule ruled at round 10 and built",
     "v15.2 (7fbcd5d): the parenthesis aligned to the rule as ruled and built — a valid notice for the held record treats it as named, keeps its other fields and flags the arrival; a structural outcome difference refuses, notice or not; credited by the round-12 verdict",
     "$PY -m pytest tests/test_0041_import_contract.py::test_a_held_different_version_is_redacted_anyway_and_flagged tests/test_0041_round11_outcome.py::test_R10_01_full_export_applies_notice_to_held_outcome tests/test_0041_round11_outcome.py::test_the_treated_held_outcome_keeps_its_chain tests/test_0041_round11_outcome.py::test_control_a_changed_outcome_with_no_notice_still_refuses tests/test_0041_round11_outcome.py::test_control_a_topology_conflict_refuses_notice_or_not -q -p no:randomly"),
    ('0041', 'external', 12, '0041-R12-01',
     "a genuine notice could not redact a consolidation output the destination already held: the output identity gate rejected the unit before the notice applied",
     "round 13 (e4c1573): the owner-approved 0014 §2c rider admits exactly one difference on a colliding indexed output, a redaction of the held output; the arrival is discarded, the notice binds to the held id and the notice step treats it; the arrival is flagged",
     "$PY -m pytest tests/test_0041_round13_outputs.py::test_R12_01_indexed_output_redaction_reaches_held_output tests/test_0041_round13_outputs.py::test_the_held_output_keeps_every_field_the_notice_does_not_name tests/test_0014_portability.py::test_rider_a_named_field_at_the_marker_WITH_the_notice_resolves_and_treats_the_held_output tests/test_0014_portability.py::test_rider_a_treated_held_output_meeting_its_untreated_arrival_with_the_notice_is_existing tests/test_0014_portability.py::test_rider_the_same_difference_WITHOUT_the_notice_rejects tests/test_0014_portability.py::test_rider_a_field_the_notice_does_NOT_name_rejects tests/test_0014_portability.py::test_rider_a_named_field_at_a_NON_marker_value_rejects tests/test_0014_portability.py::test_rider_a_lineage_difference_rejects_notice_or_not tests/test_0041_round13_outputs.py::test_control_the_unchanged_first_export_still_reimports_idempotently tests/test_0041_round13_outputs.py::test_control_the_redacted_export_without_its_notice_still_refuses -q -p no:randomly"),
    ('0041', 'external', 12, '0041-N12-01',
     "NONBLOCKING: a repeated remapped import bound the notice to an output id the collision check had discarded",
     "round 13 (e4c1573): every notice for an arrival the collision check resolves is rebound to the held output's id before the commit, so the repeat ends existing",
     "$PY -m pytest tests/test_0041_round13_outputs.py::test_N12_01_a_repeated_remapped_import_binds_the_notice_to_the_existing_copy tests/test_0041_round13_outputs.py::test_every_redaction_row_names_a_record_after_held_earlier_and_repeat tests/test_0041_round13_outputs.py::test_a_contradictory_body_on_the_rebound_notice_still_refuses_whole_import -q -p no:randomly"),
    ('0041', 'external', 12, '0041-N12-02',
     "NONBLOCKING: an empty episode linked to an already-marked shared revocation row received an inaccurate nothing-to-redact refusal",
     "round 13 (0333ad1): revocation.revocation_reason_marked, a read, lets a shared revocation row already at the marker enter this record's attestation union",
     "$PY -m pytest tests/test_0041_round13_side.py::test_N12_02_an_empty_episode_of_a_source_whose_revocation_row_is_marked_is_redacted tests/test_0041_round13_side.py::test_control_an_empty_episode_with_no_linked_source_is_still_nothing_to_redact tests/test_0041_round13_side.py::test_control_the_record_that_changes_the_revocation_row_attests_it -q -p no:randomly"),
    ('0041', 'external', 13, '0041-R13-01',
     "the collision check matched a notice's raw target against the arriving OR the held id before resolution, so with ids permuted one output's notice authorised another output's difference",
     "round 14 (b24f5ae; controls strengthened in 8a54a87): every arrival resolved before any notice is read for a collision; a raw id names one subject; a notice authorises the exception only for its own resolved subject; an ordinary arrival reusing a held id does not lend its notice",
     "$PY -m pytest tests/test_0041_round14_resolution.py::test_R13_01_permuted_ids_with_ONE_notice_refuse_the_whole_import tests/test_0041_round14_resolution.py::test_R13_01_an_ordinary_arrival_reusing_a_held_id_does_not_lend_its_notice tests/test_0041_round14_resolution.py::test_control_permuted_ids_with_BOTH_notices_treat_both_held_outputs tests/test_0041_round14_resolution.py::test_control_a_notice_naming_a_held_target_with_no_arrival_applies_to_it tests/test_0041_round14_resolution.py::test_control_a_repeated_user_remap_binds_both_notices_to_the_surviving_copies tests/test_0041_round13_outputs.py::test_a_contradictory_body_on_the_rebound_notice_still_refuses_whole_import tests/test_0041_round13_outputs.py::test_N12_01_a_repeated_remapped_import_binds_the_notice_to_the_existing_copy -q -p no:randomly"),
    ('0041', 'external', 13, '0041-R13-02',
     "the 0014 §2c rider's marker condition was a substring test, admitting a value that merely contained the marker",
     "round 14 (2662970; controls strengthened in 8a54a87): held_output_redaction compares each differing field exactly, held or incoming == MARKER; the substring helpers keep their reservation and diagnostic jobs",
     "$PY -m pytest tests/test_0041_round14_marker.py::test_R13_02_a_value_that_merely_CONTAINS_the_marker_refuses_whole_import tests/test_0041_round14_marker.py::test_control_the_exact_marker_with_the_notices_is_admitted_and_treats_both tests/test_0041_round14_marker.py::test_control_ordinary_text_in_a_named_field_refuses tests/test_0014_portability.py::test_rider_a_field_the_notice_does_NOT_name_rejects tests/test_0041_round13_outputs.py::test_control_the_unchanged_first_export_still_reimports_idempotently -q -p no:randomly"),
    ('0041', 'external', 13, '0041-N13-01',
     "NONBLOCKING: a supersession-refusal row shared by two edges was omitted from the second edge's redaction receipt",
     "round 14 (a24a47d): a supersession-refusal row linked to the edge at either end and already at the marker is attested; the one update unchanged",
     "$PY -m pytest tests/test_0041_round14_shared.py::test_N13_01_the_second_edge_attests_the_shared_row_already_at_the_marker tests/test_0041_round14_shared.py::test_control_a_never_treated_shared_row_is_treated_and_attested_by_this_call tests/test_0041_round14_shared.py::test_control_an_edge_with_no_refusal_row_does_not_name_the_path -q -p no:randomly"),
    # ---- 0041 post-acceptance revision v15.6 (2026-10-13) — the notice-binding hotfix; owner-ruled, no external round ----
    ("0041", "internal", 0, '0041-PA1',
     'An imported redaction notice bound to its target by id alone: an untrusted file carrying only a notice redacted the user\'s own held fact, left a standing notice that refused the user\'s own later write and hid the id, and redacted a later arrival; the store\'s own export then paired a hostile notice with the user\'s unredacted fact',
     '98327c2: on the default path a notice applies only to a record the import inserts; in both modes only where a record shows the redaction (redaction.shows_redaction): the file\'s copy, or, on a restore with no copy, the held record (attest only); a file carrying a notice\'s record unredacted refuses whole wherever that record would be admitted under it (store.import.notice-record-unredacted), unless this store already holds that notice as applied; a standing notice refuses no local write and is not in redacted_targets(), completing only on an inserted record that shows it and, on the default path, of its own origin (store.import.standing-notice-origin-mismatch); the result names notices_not_applied. SUPERSEDED at T4 (2026-10-14; 0041 v16 §11.6.6, the notice state machine; the cells re-pointed, the mutation table re-anchored): a default import over a held target records the notice PENDING (held bytes unchanged), an absent target\'s is STANDING and inert, a later arrival must show the redaction in both modes (PENDING on a default import, applied on a restore), the origin check is REMOVED (origin decides nothing, INV-RR12), and an export carries no non-applied notice beside its record, so a store\'s own export no longer pairs a hostile notice with the user\'s fact (research\'s B1)',
     '$PY -m pytest tests/test_0041_notice_binding_hotfix.py::test_an_untrusted_notice_never_redacts_the_users_own_held_fact tests/test_0041_notice_binding_hotfix.py::test_an_untrusted_notice_never_redacts_a_held_episode tests/test_0041_notice_binding_hotfix.py::test_the_victims_exact_record_in_the_file_does_not_unlock_the_notice tests/test_0041_notice_binding_hotfix.py::test_a_held_different_version_under_an_untrusted_notice_is_kept_and_reported tests/test_0041_notice_binding_hotfix.py::test_an_untrusted_notice_for_an_absent_id_leaves_an_inert_standing_row tests/test_0041_notice_binding_hotfix.py::test_a_later_unredacted_record_of_that_id_is_refused_whole_and_nothing_is_redacted tests/test_0041_notice_binding_hotfix.py::test_i_a_legacy_standing_notice_never_refuses_the_users_own_write tests/test_0041_notice_binding_hotfix.py::test_i_a_legacy_standing_notice_never_refuses_the_users_own_episode_write tests/test_0041_notice_binding_hotfix.py::test_ii_an_unredacted_default_arrival_under_a_standing_notice_is_refused_whole tests/test_0041_notice_binding_hotfix.py::test_ii_a_default_REDACTED_arrival_from_another_origin_is_pending_origin_decides_nothing tests/test_0041_notice_binding_hotfix.py::test_ii_an_unredacted_arrival_under_a_standing_notice_refuses_even_on_restore tests/test_0041_notice_binding_hotfix.py::test_7a_a_poisoned_export_default_imported_refuses_and_redacts_nothing tests/test_0041_notice_binding_hotfix.py::test_7b_a_poisoned_export_restored_into_a_fresh_store_refuses_and_redacts_nothing tests/test_0041_notice_binding_hotfix.py::test_7c_a_poisoned_store_restoring_its_own_export_refuses_and_keeps_the_fact tests/test_0041_notice_binding_hotfix.py::test_7_the_default_path_reports_a_held_target_before_it_would_refuse tests/test_0041_notice_binding_hotfix.py::test_a_notice_only_restore_onto_a_held_record_is_not_applied tests/test_0041_notice_binding_hotfix.py::test_a_repeat_untrusted_import_stays_inert tests/test_0041_notice_binding_hotfix.py::test_the_cli_prints_the_notices_it_did_not_apply tests/test_0041_notice_binding_hotfix.py::test_the_attest_only_branch_is_restore_only_on_a_default_import tests/test_0041_notice_binding_hotfix.py::test_the_primitive_defaults_to_the_narrow_scope tests/test_0041_notice_state.py::test_a_default_import_never_changes_a_held_record_through_a_notice tests/test_0041_notice_state.py::test_a_standing_notice_over_a_local_write_is_weighed_as_a_held_target tests/test_0041_notice_state.py::test_origin_decides_nothing tests/test_0041_notice_state.py::test_a_stores_own_export_round_trips_whatever_its_notices_hold -q -p no:randomly'),

    ('0013', "internal", 0, '0013-PA1',
     "six migration steps' outputs were checked by nothing, on any SQLite build: the stamp, the store_identity and store_epoch mints, the v13 baseline journal, the v2->v3 outcome-chain conversion and the v3->v4 wiki drop; every perturbation of them survived a whole-ladder mutation campaign (dev's steptable.py, research's identical re-run), and a wrong stamp made migrate_store report `migrated` and commit a store the next open refused (an assurance gap, not a wrong output in any release)",
     "0a89696: 0013 v33 §4f, each step followed inside the migration's transaction by a postcondition reading the database's own bytes, a failure refusing through store.migration.postcondition (unsupported-migration, the step named, the store unchanged); the migration's ONE clock read fills a missing observed_at, stamps the baseline and starts the epoch; the v2->v3 check compares the RAW legacy row key by key as declared field types, refusing undeclared keys on either side except the retired provenance.source_type (0016 D2); the stamp read back at the post-migration end state. Closed by specs/evidence/0013/mutation-table.json: every steptable perturbation of the six steps KILLED at its own step (named, before any later step wrote, the store unchanged) and the code mutants (M121's six, M123's three, each postcondition deleted) KILLED by these cells",
     '$PY -m pytest tests/test_0013_pa1_campaign_cells.py::test_cell_a_perturbed_outcome_chain_refuses_at_its_step tests/test_0013_pa1_campaign_cells.py::test_cell_a_skipped_wiki_drop_refuses_at_its_step tests/test_0013_pa1_campaign_cells.py::test_cell_a_perturbed_store_identity_refuses_at_its_step tests/test_0013_pa1_campaign_cells.py::test_cell_a_perturbed_baseline_event_refuses_at_its_step tests/test_0013_pa1_campaign_cells.py::test_cell_a_skipped_store_epoch_refuses_at_its_step tests/test_0013_pa1_campaign_cells.py::test_cell_a_perturbed_stamp_refuses_at_the_stamp tests/test_0013_pa1_campaign_cells.py::test_cell_a_legacy_row_in_isoformat_plus0000_form_migrates tests/test_0013_pa1_campaign_cells.py::test_cell_a_present_observed_at_is_kept tests/test_0013_pa1_campaign_cells.py::test_cell_a_missing_observed_at_is_filled_from_the_one_clock_read tests/test_0013_pa1_campaign_cells.py::test_cell_an_added_key_with_a_non_default_value_refuses_at_the_chain_step tests/test_0013_pa1_campaign_cells.py::test_cell_an_undeclared_raw_key_refuses_at_the_chain_step tests/test_0013_pa1_campaign_cells.py::test_cell_two_legacy_outcome_rows_both_convert && $PY specs/evidence/0013/pa1_campaign.py --check'),

    # ---- 0042 external rounds 1-5 and 0043 external rounds 1-4 (2026-09-18), the acceptance fold -----
    ('0042', 'external', 1, '0042-R1-1',
     'the rates and their measurement windows were undefined (§§1, 4B, 5; INV-3/4): the denominator argument was overstated',
     "travelled to 0043 at the split (owner's ruling, 2026-09-18): A1's ledger form — per-(question, arm) rows, rates over RESOLVED rows with the denominator stated, the timeout as its own terminal row; 0043 v1 §4B/INV-3/INV-4",
     'git show 1bc29178014016d040e8cdb1ee92d81420970244 -- specs/0043-refusal-harness.md # v1 A1 — the ledger form'),
    ('0042', 'external', 1, '0042-R1-2',
     'the proposed examiner input violated blindness (§4B step 1; INV-6)',
     'travelled to 0043: the examiner view restricted to (subject, relation, object, since) with the flip test as the blindness proof; 0043 v1 §4B step 1, INV-6',
     'git show 1bc29178014016d040e8cdb1ee92d81420970244 -- specs/0043-refusal-harness.md # v1 A2 — the examiner view'),
    ('0042', 'external', 1, '0042-R1-3',
     'no independent outcome judge and no question-level reference labels (§§3, 4B; INV-4/6)',
     'travelled to 0043: the adjudication rubric with reference cases, later replaced by the interpretation stage (A3-ter/A3-quater); 0043 v1 §4B',
     'git show 1bc29178014016d040e8cdb1ee92d81420970244 -- specs/0043-refusal-harness.md # v1 A3 — the rubric'),
    ('0042', 'external', 1, '0042-R1-4',
     'installed instrumentation was not separated from observed traffic (§4A-0/A; INV-1/2)',
     'Part A-0 gained the three sets and Part A-1 the six-status state table (UNREACHED vs UNEXERCISED vs UNMEASURED; DISABLED as a status) — parsed from the spec by the evidence, not hand-listed',
     '$PY -m pytest tests/test_0042_evidence.py::test_a1_state_table_is_parsed_from_the_spec_and_the_code_conditions_match_it_one_to_one tests/test_0042_evidence.py::test_a1_every_tuple_maps_to_exactly_one_status_in_precedence_order'),
    ('0042', 'external', 1, '0042-R1-5',
     'the counter lifecycle and the observation-only contract were incomplete (§§4A, 5, 7, 10; INV-2/7)',
     'Part A-2: the counter lifecycle, the three-arm decision-trace diff over exactly (seq, site_id, decision) with its bound stated',
     '$PY -m pytest tests/test_0042_evidence.py::test_a2_three_arm_trace_diff_compares_only_the_named_fields_and_refuses_extra_ones'),
    ('0042', 'external', 1, '0042-R1-6',
     'the baseline treatment was unspecified (§4B step 3; INV-5)',
     'travelled to 0043: the baseline arm, replaced three times (merged prompt → examiner view → the CAPTURED model input under a stated transform, A6-ter), the history in 0043 §11',
     'git show 1bc29178014016d040e8cdb1ee92d81420970244 -- specs/0043-refusal-harness.md # v1 A6 — the first baseline definition'),
    ('0042', 'external', 2, '0042-R2-1',
     'the AST inventory could not support the completeness claim: candidate discovery, reviewed enforcement points and installed instrumentation were one undifferentiated set',
     'Part A-0-bis: DISCOVERED (derived by the inventory: RAISE, RETURN_FALSE, RETURN_NONE, BOOL_RETURN, FILTER_RETURN), REVIEWED (recorded decisions), DECLARED; the three-sets check refused on the round-2 tree because no decisions existed; since tranche 6a every candidate carries a decision and the check still bites on an emptied review',
     '$PY -m pytest tests/test_0042_evidence.py::test_a0bis_the_three_sets_check_refuses_each_wrong_pair_and_passes_the_complete_fixture tests/test_0042_evidence.py::test_a0bis_on_the_real_tree_every_discovered_candidate_has_a_decision tests/test_0042_evidence.py::test_a4_discovery_finds_the_four_symbols_round_2_named_and_states_its_unit'),
    ('0042', 'external', 2, '0042-R2-2',
     'the census schema and the comparison contract were inconsistent across prose, schema and tests (statuses 4 vs 5; invalid counts; the compared trace fields unnamed)',
     'Part A-1 is the single authority: the state table parsed from the spec with the count cross-checked against the prose; the report gate refuses every named defect; Part A-2 names the compared fields',
     '$PY -m pytest tests/test_0042_evidence.py::test_a1_parser_refuses_a_missing_table_and_a_count_that_disagrees_with_the_prose tests/test_0042_evidence.py::test_a1_report_gate_refuses_every_named_defect_and_emits_the_undeclared_row'),
    ('0042', 'external', 3, '0042-R3-1',
     'reviewed and declared does not establish installed: with every candidate reviewed, every point declared and no counters at all, the reconciliation passed',
     'Part A-0-ter derived INSTALLED from a static scan checked by the import-time registry — itself found a proxy in round 4 and replaced by A-0-quater (the binding); see 0042-R4-1',
     'git show 43c1c637cef4372dadcf315a23f06ae8e1c8100d -- specs/0042-exercised-guarantees.md # v6 Part A-0-ter'),
    ('0042', 'external', 3, '0042-R3-2',
     'A5 bounded: disabling measurement allowed an undeclared reporter to pass',
     'structural reconciliation runs BEFORE status and does not depend on `enabled`: an undeclared reporter under enabled == false is emitted DISABLED and refused',
     '$PY -m pytest tests/test_0042_evidence.py::test_a5_an_undeclared_reporter_is_refused_even_when_measurement_is_off'),
    ('0042', 'external', 3, '0042-R3-3',
     'observation-only evidence: (seq, site_id, decision) supports branch-sequence equivalence only; replay inputs and execution conditions must be frozen and the bound stated',
     'Part A-2 states the bound (branch-sequence equivalence under frozen inputs; results and state checked separately); the trace key refuses records carrying anything else',
     '$PY -m pytest tests/test_0042_evidence.py::test_a2_three_arm_trace_diff_compares_only_the_named_fields_and_refuses_extra_ones'),
    ('0042', 'external', 4, '0042-R4-1',
     'registration does not establish working instrumentation: a declare_site call is a proxy for a counter bound to the decision — both fixture decisions executed, every counter stayed at zero, the report read UNREACHED; the deletion control deleted the declaration on a fixture with no counters',
     "Part A-0-quater: the decision is expressed THROUGH the site; INSTALLED = the scan of the binding; the runtime assertion is the reviewer's own test; the controls with the naming defect fixed",
     '$PY -m pytest tests/test_0042_evidence.py::test_a0quater_the_reviewers_round4_test_executing_both_decisions_moves_both_counters_and_reads_exercised tests/test_0042_evidence.py::test_a0quater_strip_the_binding_keep_the_declaration_refuses_and_consult_without_fire_refuses tests/test_0042_evidence.py::test_a0quater_registered_but_unbound_is_refused_by_the_registry_check_as_registered_not_installed'),
    ('0042', 'external', 5, '0042-R5-1',
     'the binding scan accumulated method uses across the whole module by variable name: consult() in one function and fire() in another read as bound; an already-positive counter must not establish that a later decision was measured',
     'the binding is function-local and scope-aware (nested functions are their own scope; a shadowed name is not the site); the runtime assertion is over DELTAS around the particular decision; the split-function, nested and shadowed mutants refuse',
     '$PY -m pytest tests/test_0042_evidence.py::test_a0quater_round5_the_binding_is_function_local_and_scope_aware tests/test_0042_evidence.py::test_a0quater_the_reviewers_round4_test_executing_both_decisions_moves_both_counters_and_reads_exercised'),
    ('0042', 'external', 4, '0042-R4-2',
     'advisory: consolidating the superseded passages would help prevent old installation wording from being mistaken for current requirements',
     'acknowledged at v7 with §11 (superseded decisions out of the normative body) — and round 5 found the class still present, so the record shows the ask twice; closed at v8 (see 0042-R5-2)',
     'git show a9d3622d6252a19387b2ecb66a665f101825fb36 -- specs/0042-exercised-guarantees.md # v7 §11'),
    ('0042', 'external', 5, '0042-R5-2',
     'superseded normative wording still readable as live requirements — the class the reviewer named in round 4 and again at acceptance ("finish removing superseded normative wording")',
     "removed at v8: the diff moves the contiguous superseded blocks out of the normative body into §11 (the 'inspected subset' comparison; the A-0-ter INSTALLED definition); the history stays in §11",
     'git show c6dd4078b877088684b381add72fe08feb1354b4 -- specs/0042-exercised-guarantees.md # v8 — the superseded blocks moved to §11'),
    # ---- 0042 external rounds 6-22: THE IMPLEMENTATION REVIEW (accepted at round 23, 2026-09-26); every closure behavioural ----
    ('0042', 'external', 6, '0042-R6-1',
     'a failing trace recorder, decline classifier or single consult increment was not contained: it raised, read UNEXERCISED with errors=0, or produced fired>consulted that invalidated the whole report (INV-2/INV-7)',
     'round-7 fix: census.Site contains recorder/classifier failures, counts them in errors, records the exception type per id; the row reads UNMEASURED and census_table.insufficiency refuses it as evidence',
     '$PY -m pytest tests/test_0042_census.py::test_r6_1_a_failed_trace_recorder_is_contained_counted_and_the_decision_is_returned_as_made tests/test_0042_census.py::test_r6_1_a_failed_decline_classifier_reads_unmeasured_not_unexercised tests/test_0042_census.py::test_r6_1_a_failed_consult_increment_reads_unmeasured_the_report_stays_valid_and_is_insufficient'),
    ('0042', 'external', 6, '0042-R6-2',
     "scoped_assertable's shared bracket counted later checks as consulted after an early return, and the four hot Edge predicates left consultation at zero when evaluation raised",
     'round-7 fix: every sequential site consulted immediately before its own condition (per-check brackets / consult statements); hot Edge predicates consult before evaluating when enabled and return through one statement',
     '$PY -m pytest tests/test_0042_sites.py::test_r6_2a_a_consult_means_the_sites_own_condition_was_reached tests/test_0042_sites.py::test_a_raising_predicate_raises_identically_on_both_paths_and_is_consulted_before_it_is_evaluated'),
    ('0042', 'external', 6, '0042-R6-3',
     'a declared site whose loaded module never registered was reported UNREACHED with zero counts and validate_report accepted it; the reconciliation took its set from source scanning, not the live registry',
     'round 7: snapshot carries what registered; validate_report refuses a loaded-but-unregistered id and names out-of-reach ones — but only when site_modules was supplied; R7-1 made the incomplete validation explicit (round 8)',
     '$PY -m pytest tests/test_0042_census.py::test_r6_3_a_declared_id_whose_module_is_loaded_but_never_registered_is_refused_and_an_unloaded_one_is_named tests/test_0042_evidence.py::test_a0quater_round6_the_live_registry_reconciles_against_the_scan_and_nothing_is_out_of_reach tests/test_0042_evidence.py::test_r7_f1_the_reviewers_case_a_two_argument_validation_no_longer_reads_clean'),
    ('0042', 'external', 6, '0042-R6-4',
     'the binding scan checked local shadowing only and did not resolve enclosing scopes, so a closure over an enclosing parameter named like a site read as bound',
     'round 7: names resolved through enclosing function scopes (class bodies not scopes); the binding-form class continued as R7-2 (walrus/match, fixed round 8 by the symtable resolver) and R8-1 (nested imports, fixed round 9)',
     '$PY -m pytest tests/test_0042_evidence.py::test_a0quater_round6_a_site_name_resolves_through_enclosing_function_scopes_and_class_bodies_do_not_shadow tests/test_0042_evidence.py::test_r7_f2_the_reviewers_two_rebinding_forms_no_longer_read_as_bound tests/test_0042_scope_resolution.py::test_every_module_level_binding_form_is_refused_and_no_shadow_is'),
    ('0042', 'external', 6, '0042-R6-5',
     'inv7_harness compared encoded bytes without their symbol/label dictionaries, merged distinct sites sharing a return value, and its success status did not require arm exits or cross-checks',
     "round 7: observer records (symbol, exit-statement ordinal, label), harness decodes through each arm's dictionaries and compares canonical records, final_status requires every arm exit and cross-check; gaps continued as R7-3 (round 8) and R8-2 (round 9)",
     '$PY -m pytest tests/test_0042_inv7.py::test_r6_5_i_identical_bytes_with_different_dictionaries_are_different_traces tests/test_0042_inv7.py::test_r6_5_iii_the_harness_exit_requires_every_arm_and_every_cross_check tests/test_0042_inv7.py::test_r6_5_ii_every_declared_site_has_its_own_exit_statement_so_exit_keyed_records_separate_them'),
    ('0042', 'external', 6, '0042-R6-6',
     'the uninstrumenting transform removed an unrelated .fire call, accepted an unbound attribute chain and deleted a product side effect inside an enabled block',
     'round 7: transform rewrites only names bound by declare_site and recognised shapes, refuses the rest by line, writes twin_manifest.json that verify() re-derives; the preservation class continued through R7-4, R8-3, R9-1, R10-1/2 (closed round 11)',
     '$PY -m pytest tests/test_0042_inv7.py::test_r6_6_the_twin_transform_refuses_what_it_has_not_established_is_instrumentation_and_keeps_exits tests/test_0042_inv7.py::test_r7_f4_the_verifier_establishes_preservation'),
    ('0042', 'external', 6, '0042-R6-7',
     'the surface-driven site assertions checked only fired>=1 and consulted>=fired, so doubling every increment passed',
     "round 7: surface-driven sites assert exact deltas derived from the product's control flow (EXACT_SURFACE/EXACT_DECLINE); a doubled-increment control fails every one",
     '$PY -m pytest tests/test_0042_sites.py::test_the_surface_driven_sites_move_by_exactly_their_derived_counts tests/test_0042_sites.py::test_r6_7_a_doubled_increment_fails_every_exact_delta'),
    ('0042', 'external', 7, '0042-R7-1',
     'registry reconciliation ran only when the caller supplied site_modules, so an ordinary two-argument validate_report accepted a missing registration as UNREACHED',
     'round 8: absence of reconciliation evidence is reported in the refusal list ([] means validated completely); what a report cannot speak for moved to insufficiency, per id; the same optional-argument shape swept in insufficiency',
     '$PY -m pytest tests/test_0042_evidence.py::test_r7_f1_the_reviewers_case_a_two_argument_validation_no_longer_reads_clean tests/test_0042_census.py::test_r7_no_check_returns_clean_when_an_optional_argument_narrowed_its_scope'),
    ('0042', 'external', 7, '0042-R7-2',
     'installed_sites did not recognise every local binding form; walrus and match-capture rebinding of a site name read bound=True',
     'round 8: new scope_resolution.py over symtable shared by scan and transform (binding grammar by construction); nested-import gap continued as R8-1 (round 9)',
     '$PY -m pytest tests/test_0042_evidence.py::test_r7_f2_the_reviewers_two_rebinding_forms_no_longer_read_as_bound tests/test_0042_scope_resolution.py::test_the_resolver_answers_every_binding_form tests/test_0042_scope_resolution.py::test_the_matrix_covers_both_answers_and_the_reviewers_two_forms tests/test_0042_scope_resolution.py::test_a_module_level_rebinding_of_a_site_is_refused_including_a_walrus_in_a_comprehension'),
    ('0042', 'external', 7, '0042-R7-3',
     'inv7_harness ignored failed control runs, used an exits-per-function count that two sites sharing a return could satisfy, and serialised verdict.json before final_status added the gates',
     "round 8: every arm and control's pytest exit gated; site-to-exit association replaces the count; status computed before verdict serialisation; missing-summary gap continued as R8-2 (round 9)",
     '$PY -m pytest tests/test_0042_inv7.py::test_r7_f3a_a_control_run_that_failed_fails_the_exit tests/test_0042_inv7.py::test_r7_f3c_the_serialised_verdict_carries_the_gates_both_readmes_promise tests/test_0042_inv7.py::test_r6_5_ii_every_declared_site_has_its_own_exit_statement_so_exit_keyed_records_separate_them tests/test_0042_inv7.py::test_r6_5_ii_control_the_reviewers_fixture_collides_and_a_count_cannot_see_it'),
    ('0042', 'external', 7, '0042-R7-4',
     'verify() compared selected statement kinds only, did not check manifest hashes or the file set, was called without its source; the transform rewrote a parameter shadowing a site name',
     'round 8: verify requires source, compares the file set both ways, re-derives and diffs the AST, checks manifest hashes; transform resolves names via the shared resolver; alias-shadow gap continued as R8-3',
     '$PY -m pytest tests/test_0042_inv7.py::test_r7_f4_the_verifier_establishes_preservation tests/test_0042_inv7.py::test_r7_f4a_a_parameter_shadowing_a_site_name_keeps_its_own_call'),
    ('0042', 'external', 8, '0042-R8-1',
     "scope_resolution's nested-scope check used is_global() and is_assigned(); a nested import under 'global S' is is_imported not is_assigned, so it replaced the site undetected",
     'round 9: rule C reads STORE_GLOBAL/DELETE_GLOBAL from nested code objects (_nested_global_bindings, refuse_site_rebindings); the superseded predicate pair kept as negative control',
     '$PY -m pytest tests/test_0042_scope_resolution.py::test_every_module_level_binding_form_is_refused_and_no_shadow_is tests/test_0042_scope_resolution.py::test_the_superseded_predicate_pair_misses_exactly_the_nested_imports tests/test_0042_scope_resolution.py::test_every_refused_row_names_the_rule_that_caught_it'),
    ('0042', 'external', 8, '0042-R8-2',
     "compare() substituted the main arm's summary for an absent control summary while final_status checked only present summaries, so a missing summary dropped the control's exit check",
     'round 9: one derivation of the control set; a control directory without its own summary is named and fails the exit, never substituted',
     '$PY -m pytest tests/test_0042_inv7.py::test_r8_f2_a_control_without_its_own_summary_is_refused_not_substituted tests/test_0042_inv7.py::test_r8_f2_the_fix_changes_nothing_for_a_COMPLETE_capture'),
    ('0042', 'external', 8, '0042-R8-3',
     'visit_If recognised _census.enabled() by alias spelling alone, so a parameter or closure named _census had its branch rewritten while verify() stayed clean',
     'round 9: _is_census_alias asks the shared scope resolver; behaviour regression executes source and twin; module-scope-vs-identity gap continued as R9-1 (round 10)',
     '$PY -m pytest tests/test_0042_inv7.py::test_r8_f3_an_ordinary_shadowed_census_alias_keeps_its_behaviour tests/test_0042_inv7.py::test_r8_f3_the_census_import_is_restored_for_a_derived_alias'),
    ('0042', 'external', 9, '0042-R9-1',
     "_is_census_alias established module scope but not that the binding still denoted the census; a rebinding after import and the {'_census','census'} fallback both rewrote ordinary branches, verify clean",
     'round 10: declared_names checks import module and level; guessed-alias fallback removed; alias must be bound exactly once at module level (module_binding_count); identity asserted at runtime. Nested rebinding continued as R10-1',
     '$PY -m pytest tests/test_0042_inv7.py::test_r9_a_census_alias_whose_binding_was_replaced_is_refused_not_rewritten tests/test_0042_inv7.py::test_r9_a_module_with_no_census_import_keeps_its_own_behaviour tests/test_0042_inv7.py::test_r9_the_alias_identity_is_established_at_runtime_because_it_cannot_be_established_statically'),
    ('0042', 'external', 10, '0042-R10-1',
     'the alias check read only rule A (module code object); a nested global assignment, nested import or genexp walrus replaced _census without moving that count, and the twin diverged with verify() clean',
     'round 11: the alias asks both rule A and rule C (_nested_global_bindings made public); every census decision routed through named predicates, enforced by an AST-derived gate',
     '$PY -m pytest tests/test_0042_inv7.py::test_r11_the_four_census_identity_findings tests/test_0042_inv7.py::test_every_census_decision_routes_through_one_predicate'),
    ('0042', 'external', 10, '0042-R10-2',
     'import removal stripped any name spelled census from any import (e.g. from totally_unrelated import census), so the twin raised NameError while verify() passed',
     'round 11: removal routed through the same predicate as recognition (module and level both checked); multi-name census imports stripped per name',
     '$PY -m pytest tests/test_0042_inv7.py::test_r11_the_four_census_identity_findings tests/test_0042_inv7.py::test_every_census_decision_routes_through_one_predicate'),
    ('0042', 'external', 11, '0042-R11-1',
     'a census import was dropped whole, losing live bindings of mixed/surface imports; verify() re-derived with the same transform and read clean',
     'round 12: per-name removal with restoration of every removed binding; verify() gained checks of a different kind (compile(), lost_bindings; round 13 added lost_cross_module_references)',
     '$PY -m pytest tests/test_0042_inv7.py::test_r12_f1_every_census_import_shape_keeps_its_bindings_or_refuses tests/test_0042_inv7.py::test_r12_verify_catches_a_transform_defect_it_did_not_write'),
    ('0042', 'external', 11, '0042-R11-2',
     'the round-11 enumeration gate waived any unit calling a predicate, so an independent census decision inside such a unit passed',
     "round 12: waiver deleted; banned vocabulary derived from the predicates' own string constants, checked per unit",
     '$PY -m pytest tests/test_0042_inv7.py::test_r12_f2_the_gate_refuses_a_second_reading_wherever_it_stands tests/test_0042_inv7.py::test_every_census_decision_routes_through_one_predicate'),
    ('0042', 'external', 12, '0042-R12-1',
     "the comprehension handler walked element/key before generators (S2c-1, disclosed open), handing same-line scopes each other's symbol tables; a live census read stayed in the twin with verify clean and 0 unresolved",
     "round 13: CPython's comprehension order; a join check refusing any pairing decided by order alone; the pairing oracle as a standing gate; a census read the twin keeps is reported",
     '$PY -m pytest tests/test_0042_scope_resolution.py::test_r13_f1_every_scope_inside_a_comprehension_gets_its_own_table tests/test_0042_inv7.py::test_r13_f1_a_census_read_the_twin_keeps_is_reported_not_silent tests/test_0042_scope_resolution.py::test_r13_the_join_check_turns_the_old_orders_silent_answers_into_refusals tests/test_0042_scope_resolution.py::test_r13_the_pairing_oracle_finds_no_silent_answer_and_its_control_does'),
    ('0042', 'external', 12, '0042-R12-2',
     'the twin removed site declarations, so a sibling module importing a site failed with ImportError while verify() passed',
     'round 13: derive refused a site another module reaches plus a cross-module differential in verify; class reopened as R13-1 and closed by construction in round 14 (declarations kept, nothing removed)',
     '$PY -m pytest tests/test_0042_inv7.py::test_r14_f1_no_route_to_a_declared_site_breaks_the_twin tests/test_0042_inv7.py::test_r12_verify_catches_a_transform_defect_it_did_not_write tests/test_0042_inv7.py::test_r13_f2_a_sibling_using_only_ordinary_names_is_neither_refused_nor_reported'),
    ('0042', 'external', 13, '0042-R13-1',
     'five more routes to a removed declaration (pkgutil.resolve_name, runpy.run_module, importlib.util loading, __globals__, inspect.getmodule) derived a broken twin with verify() clean',
     'round 14: nothing removed — declarations and census imports kept verbatim, each bound to an inert stand-in (later: the reference census, rounds 15-16); every route derives, verifies clean and runs as the source (36 cells)',
     '$PY -m pytest tests/test_0042_inv7.py::test_r14_f1_no_route_to_a_declared_site_breaks_the_twin'),
    ('0042', 'external', 13, '0042-R13-2',
     "the scan-to-runtime binding check collected a property's getter only and matched functions by name, so a scanned setter binding a site could differ from the code that ran",
     "round 14: every scanned binding body must be found among the running module's code objects via its outermost def and equal the compiled source; walk covers nested classes, getter/setter/deleter, cached_property, static/class methods",
     '$PY -m pytest tests/test_0042_evidence.py::test_r14_f2_a_binding_body_that_did_not_run_is_refused tests/test_0042_evidence.py::test_r13_the_scan_describes_the_program_that_ran_and_refuses_otherwise'),
    ('0042', 'external', 14, '0042-R14-1',
     "the twin's inert stand-in class overrode object methods to count uses, so decisions asking the class (e.g. type(S).__hash__ is object.__hash__) read True in source, False in twin, verify clean, 0 uses",
     "round 15: stand-in removed; twin carries census.py verbatim so its Site class is the source's (round 16 then pinned it to the accepted commit T's census)",
     '$PY -m pytest tests/test_0042_inv7.py::test_r15_every_question_about_a_site_answers_alike_in_source_and_twin tests/test_0042_inv7.py::test_r16_the_twin_census_is_the_reference_census_and_verify_refuses_any_other'),
    ('0042', 'external', 15, '0042-R15-1',
     "the reference arm ran the census under test, so a declaration-time census defect changed decisions identically in all four arms and INV-7's trace diff could not see it",
     "round 16: reference arm's census is the census.py of an accepted commit T pinned by digest (verify refuses any other); HEAD's Site compared to T's, drift refused; INV-7 amendment proposed and accepted in round 16",
     '$PY -m pytest tests/test_0042_inv7.py::test_r16_the_reference_census_separates_a_declaration_time_defect tests/test_0042_inv7.py::test_r16_the_mutant_changes_a_decision_at_all tests/test_0042_inv7.py::test_r16_the_twin_census_is_the_reference_census_and_verify_refuses_any_other tests/test_0042_inv7.py::test_r16_a_drifted_site_is_refused_and_t_must_advance'),
    ('0042', 'external', 15, '0042-R15-2',
     "run_arm passed the inherited relative PYTHONPATH unchanged to child processes whose working directory differed, so three child-process tests failed on the reviewer's extracted tree",
     'round 16: run_arm makes every inherited PYTHONPATH entry absolute; stage smoke run as the reviewer ran it with a control reproducing the three failures at the round-15 pin',
     '$PY -m pytest tests/test_0042_inv7.py::test_r16_run_arm_hands_the_child_an_absolute_import_path'),
    ('0042', 'external', 16, '0042-R16-1',
     'the Site drift check read the class body as a member map, so a reordering and a shadowed duplicate definition read no drift while source and reference decisions differed',
     'round 17: route A compares the whole ClassDef ordered with duplicates (header by field); route B compares the realized class attribute by attribute incl. metaclass data descriptors; drift is the union',
     '$PY -m pytest tests/test_0042_inv7.py::test_r17_site_drift_reads_the_definition_and_the_realized_class tests/test_0042_inv7.py::test_r17_formatting_is_not_drift_on_either_route'),
    ('0042', 'external', 17, '0042-R17-1',
     "route B's function normaliser ignored functions' writable __name__/__qualname__/__module__, so a post-class metadata change read no drift while a decision testing it differed between source and reference",
     'round 18: one recursive rule over every data descriptor of every object (read-only included, fields derived per interpreter); __flags__ bit 19 masked; import-time realized-Site digest gated at runtime',
     '$PY -m pytest tests/test_0042_inv7.py::test_r18_function_metadata_is_compared_by_one_recursive_rule tests/test_0042_inv7.py::test_r18_route_b_sees_constants_closures_and_method_attributes tests/test_0042_inv7.py::test_r18_the_function_fields_compared_are_derived_per_interpreter'),
    ('0042', 'external', 18, '0042-R18-1',
     "the describer read a subclass named like a builtin (e.g. tuple) as that builtin, so a spoofed Site.__slots__ passed every drift check while 'site_id' in type(S).__slots__ differed",
     "round 19: a type read by name only if immutable; a mutable subclass described in full through its base's methods; each census described in a fresh python -I -B child with builtins restored",
     '$PY -m pytest tests/test_0042_inv7.py::test_r19_a_subclass_is_never_read_as_the_builtin_it_names tests/test_0042_inv7.py::test_r19_an_equal_real_builtin_is_not_drift tests/test_0042_inv7.py::test_r19_the_runtime_gate_reads_the_witness_and_the_spoof_as_different'),
    ('0042', 'external', 19, '0042-R19-1',
     'the isolated child wrote its JSON description to the stdout the census shares, so ordinary census output made derive() and verify() raise a bare JSONDecodeError and lose real drift diagnostics',
     'round 20: child writes its response to a file it owns and exits via os._exit(0); every failure named (SiteUndescribed, never drift). Non-UTF-8 output remained as R20-1, fixed round 21',
     '$PY -m pytest tests/test_0042_inv7.py::test_r20_census_output_never_reaches_the_isolated_child_s_response tests/test_0042_inv7.py::test_r20_an_undescribable_census_is_never_reported_as_drift tests/test_0042_inv7.py::test_r20_each_superseded_transport_fails_its_cell'),
    ('0042', 'external', 19, '0042-R19-2',
     'the N4 comprehension signature ignored the compiler-added __class__ on a super load, merging an inner __class__ target and raising UnresolvableScope on valid code',
     "round 20: compiler-added names derived by two routes (symtable.c and a stdlib symtable census); all comparisons in symtable's (mangled) spelling; 576-program generated corpus matches symtable 3.10-3.13",
     '$PY -m pytest tests/test_0042_scope_resolution.py::test_r20_f2_compiler_names_and_mangling_match_symtable_and_resolve tests/test_0042_scope_resolution.py::test_r20_f2_the_generated_corpus_equals_symtable_and_resolves tests/test_0042_inv7.py::test_r20_a_valid_helper_beside_a_measured_decision_derives tests/test_0042_scope_resolution.py::test_r20_f2_each_superseded_rule_fails_the_corpus'),
    ('0042', 'external', 20, '0042-R20-1',
     'the parent captured census stdout/stderr as text and decoded strictly, so non-UTF-8 census output raised UnicodeDecodeError in derive() and verify() despite a valid response',
     'round 21: bytes channel, output decoded only to name a failure; UTF-8 stated at every text boundary; sources read in their declared encoding (which introduced R21-1)',
     '$PY -m pytest tests/test_0042_inv7.py::test_r21_census_bytes_never_break_the_isolated_boundary tests/test_0042_inv7.py::test_r21_decoding_the_census_output_on_success_fails_the_byte_cells tests/test_0042_inv7.py::test_r21_derive_and_verify_hold_under_a_non_utf8_locale'),
    ('0042', 'external', 21, '0042-R21-1',
     "round 21's source reader (tokenize.detect_encoding) decoded header lines as UTF-8 before finding the cookie, refusing valid Python with latin-1/cp1252/GB18030 header comments",
     "round 22: cookie found at the byte level per PEP 263; every reading checked against the interpreter's own parse (AST equality); 560-header generated corpus with the interpreter as oracle",
     '$PY -m pytest tests/test_0042_inv7.py::test_r22_the_source_reader_agrees_with_the_interpreter_over_the_header_corpus tests/test_0042_inv7.py::test_r22_a_header_the_interpreter_accepts_derives_and_verifies tests/test_0042_inv7.py::test_r22_the_interpreter_guard_fires_on_a_wrong_reading'),
    ('0042', 'external', 22, '0042-R22-1',
     "round 22's byte-level cookie rule dropped the tokenizer's name normalisation, refusing encoding names the interpreter accepts (iso-latin-1, utf-8-unix)",
     'round 23: declared name normalised as the interpreter does (_normal_name); name corpus derived from codecs and the folded families, crossed with BOM; a refusal after the interpreter accepts is named a disagreement',
     '$PY -m pytest tests/test_0042_inv7.py::test_r23_the_source_reader_agrees_with_the_interpreter_over_every_cookie_name tests/test_0042_inv7.py::test_r23_the_normaliser_is_the_interpreters_over_the_name_domain tests/test_0042_inv7.py::test_r23_the_controls_are_sets_round_22_fails_exactly_the_folded_names_round_21_passes_them tests/test_0042_inv7.py::test_r23_a_refusal_after_the_interpreter_accepts_is_named_a_disagreement'),
    ('0043', 'external', 1, '0043-R1-1',
     'the ledger did not enforce its measurement contract: None-skips, duplicate (question, arm) pairs, negative counts, no baseline required',
     "the ledger gate's five checks; rates over RESOLVED rows; the timeout moves the rate 8/10 → 8/11; the baseline arm required by name",
     '$PY -m pytest tests/test_0043_evidence.py::test_a1_the_gate_refuses_each_of_round_2s_defects_and_no_rate_exists_for_a_refused_ledger tests/test_0043_evidence.py::test_a1_formulas_a_timeout_moves_the_rate_and_unresolved_is_out_of_both_sides tests/test_0043_evidence.py::test_a1_retries_are_attempts_not_rows_and_exclusions_are_declared_rows'),
    ('0043', 'external', 1, '0043-R1-2',
     'the projection still revealed a trust class (the relation name carried it)',
     'the examiner view is (subject, relation, object, since) with relation names in; the fixture excludes the quarantine relation; the flip test proves blindness with the rendered context as the negative control',
     '$PY -m pytest tests/test_0043_evidence.py::test_a2_flip_test_the_view_is_byte_identical_and_the_rendered_context_is_not tests/test_0043_evidence.py::test_a2_view_carries_only_the_four_fields_and_the_fixture_constraint_holds_in_the_tree tests/test_0043_evidence.py::test_a2_a_view_that_leaks_the_class_fails_the_flip_test'),
    ('0043', 'external', 1, '0043-R1-3',
     'the adjudication rules were asserted rather than specified',
     'the rubric with reference cases and the five rules (v2) — superseded in role by the interpretation stage at v3/v4 (0043-R2-1, R3-1)',
     '$PY -m pytest tests/test_0043_evidence.py::test_a3_the_judge_agrees_with_every_labelled_case_and_a_flipped_label_is_detected tests/test_0043_evidence.py::test_a3_the_five_rules_resolve_as_the_spec_states_them'),
    ('0043', 'external', 1, '0043-R1-4',
     'the baseline lacked a reproducible comparison procedure',
     'the arm contract (v2), found reconstructing rather than capturing in round 3 and replaced by A6-ter (0043-R2-2)',
     'git show f33f5bc2feab1798ba11f5cfd4ebc8e335ca451d -- specs/0043-refusal-harness.md # v2 A6-bis — the arm contract'),
    ('0043', 'external', 2, '0043-R2-1',
     'the evidence tested a classification rule, not the interpretation of answers: every reference answer replaced by lorem ipsum still calibrated 14/14',
     'A3-ter, the interpretation stage: support from the captured prompt, mention from the answer text, the class-determining fact decides, the garble control collapses calibration',
     '$PY -m pytest tests/test_0043_evidence.py::test_a3quater_calibrates_from_raw_answers_on_both_arms_and_the_garble_control_collapses_it'),
    ('0043', 'external', 2, '0043-R2-2',
     'the comparison could pass while omitting compiled context: build_arms() reconstructed the model input',
     'A6-ter: the model-input boundary is the injected Complete callable; two CAPTURED prompts compared by evidence content; compilation on; the heading-without-body control refuses',
     '$PY -m pytest tests/test_0043_evidence.py::test_a6_the_captured_prompt_carries_the_compiled_body_and_the_arms_match_on_evidence tests/test_0043_evidence.py::test_a6_the_heading_without_body_control_refuses_and_a_leaky_baseline_refuses tests/test_0043_evidence.py::test_a6_capture_sees_exactly_one_gate_call_and_compilation_is_on'),
    ('0043', 'external', 2, '0043-R2-3',
     'A1 bounded: a presented class whose cases are all UNRESOLVED became NOT PRESENTED',
     'UNDEFINED with the unresolved count for a presented class with no resolved rows; NOT PRESENTED only when no question of the class was asked',
     '$PY -m pytest tests/test_0043_evidence.py::test_a1_round3_a_presented_class_with_no_resolved_rows_reads_undefined_and_a_single_arm_is_refused'),
    ('0043', 'external', 2, '0043-R2-4',
     'A2, an acceptance WITH A LIMIT: "Accept the examiner view within its stated fixture restrictions. The disclosure-flip result does not establish blindness for relation-based classification; §8 appropriately excludes that population."',
     'stands as accepted within the limit: 0043 §8 excludes records quarantined BY RELATION from every blindness claim — no view that shows relation names can hide their class; the evidence OPENS that exclusion at the fold commit; the supplementary marker derivation (tests/test_0043_evidence.py::test_a2_supplementary_marker_derivation_still_finds_the_reviewers_quotes) is kept as checking, not proof',
     'git show f33f5bc2feab1798ba11f5cfd4ebc8e335ca451d -- specs/0043-refusal-harness.md # v2 §8 — the relation-quarantined exclusion, the limit the acceptance carries'),
    ('0043', 'external', 3, '0043-R3-1',
     "removing the baseline's annotations changed the scoring reference: support read from the prompt's sections is a property of the rendering",
     'A3-quater: presence per arm, provenance once from the adjudication record; calibration over both arms; the v3 section parser kept as the mutant the both-arm check fails on',
     '$PY -m pytest tests/test_0043_evidence.py::test_a3quater_the_reviewers_reproduction_is_a_standing_control_the_v3_parser_fails_and_the_new_reading_passes tests/test_0043_evidence.py::test_a3quater_support_is_presence_in_the_arm_and_class_from_the_record_identical_across_arms'),
    ('0043', 'external', 3, '0043-R3-2',
     'B1: a mention inside a claim frame was read as an assertion',
     'mention frames (and negations) are not assertions',
     '$PY -m pytest tests/test_0043_evidence.py::test_a3quater_round4_mention_versus_assertion_cases'),
    ('0043', 'external', 3, '0043-R3-3',
     'B2: a paraphrase asserting the fact was not recognised',
     'listed paraphrases assert',
     '$PY -m pytest tests/test_0043_evidence.py::test_a3quater_round4_mention_versus_assertion_cases'),
    ('0043', 'external', 3, '0043-R3-4',
     'B3: a recorded retrieval miss with nothing delivered read REFUSED-ABSENT; and reference row 5 declared a miss for a fact the capture showed delivered',
     'the miss rule is applied before the refusal bucket; row 5 replaced by an honest miss',
     '$PY -m pytest tests/test_0043_evidence.py::test_a3quater_round4_b3_a_recorded_miss_with_nothing_delivered_is_other_not_refused_absent_and_row5_is_honest'),
    ('0043', 'external', 3, '0043-R3-5',
     'B4: an untrusted requested fact asserted beside a clean refusal raised no anomaly',
     'the anomaly contract flags any non-class fact asserted with non-assertable support',
     '$PY -m pytest tests/test_0043_evidence.py::test_a3quater_round4_b4_an_untrusted_fact_asserted_beside_a_clean_refusal_is_an_anomaly_and_porto_still_is_not'),
    ('0043', 'external', 3, '0043-R3-7',
     'advisory: consolidating the superseded passages would help prevent old timeout wording from being mistaken for current requirements',
     "acknowledged at v4 with §11 — and round 5 named the timeout wording ('rate over COMPLETED is unchanged') still present, so the record shows the ask twice; closed at v5 (see 0043-R4-3)",
     'git show a9d3622d6252a19387b2ecb66a665f101825fb36 -- specs/0043-refusal-harness.md # v4 §11'),
    ('0043', 'external', 3, '0043-R3-6',
     'A6 residue: the final implementation must capture the baseline at its actual model invocation; the demonstration constructs it from the shipped pair',
     'CLOSED at implementation (2026-09-19, 0043 tranche 1): the baseline arm is CAPTURED at its own model invocation — gate.answer over the same selection, through the same injected Complete boundary, the stated transform applied at the product\'s rendering seam (gate.render_gate_input) — and its capture is asserted EQUAL to the oracle, baseline_transform(shipped capture); a departing invocation refuses with the first differing line, an untransformed one refuses as identical, and the ledger\'s check 6 refuses any rate while the baseline is constructed or its source undeclared',
     '$PY -m pytest tests/test_0043_evidence.py::test_a6ter_the_baseline_is_captured_at_its_own_invocation_and_equals_the_oracle tests/test_0043_evidence.py::test_a6ter_a_baseline_invocation_that_departs_from_the_stated_transform_refuses_and_so_does_no_transform tests/test_0043_evidence.py::test_a6ter_the_ledger_refuses_a_rate_over_a_constructed_or_undeclared_baseline'),
    ('0043', 'external', 4, '0043-R4-1',
     "the adjudication record joined the prompt's text to all active records on (relation, object, date) without subject or delivered ids: another subject's grounded record merged into the user's quarantined unit",
     'the record is the DELIVERED identities (the Recall the answer path used, captured at the boundary), keyed by edge id with subject and original class; text is only presence; an unaccounted unit stops scoring: UNRESOLVED with cause=capture-disagrees-with-delivered, the unit reported, counted separately from an ambiguous question',
     '$PY -m pytest tests/test_0043_evidence.py::test_a3quater_the_record_is_the_delivered_identities_with_subject_and_class_and_an_unaccounted_unit_stops_scoring_as_unresolved tests/test_0043_evidence.py::test_a3quater_round5_another_subjects_record_with_the_same_text_does_not_merge_into_the_users_fact'),
    ('0043', 'external', 4, '0043-R4-2',
     '`mixed` collapsed its constituents and read as assertable; the secondary-fact check flagged grounded+untrusted as non-assertable',
     'support keeps its constituent classes; ONE rule for every path: assertable iff a grounded constituent is present',
     '$PY -m pytest tests/test_0043_evidence.py::test_a3quater_round5_support_keeps_its_constituents_and_one_rule_decides_assertability'),
    ('0043', 'external', 4, '0043-R4-3',
     "superseded normative wording still readable as live requirements: the old prompt-derived support description and the old 'rate over COMPLETED is unchanged' instruction — the two the reviewer named",
     "removed at v5: the diff moves the contiguous superseded blocks out of the normative body into §11, INV-4's executable-check cell states the current rule alone; research's own sweep moved further blocks in the same commit (not reviewer findings, recorded in the version cell)",
     'git show c6dd4078b877088684b381add72fe08feb1354b4 -- specs/0043-refusal-harness.md # v5 — the superseded blocks moved to §11'),
    # ---- 0043 implementation rounds 5-9 (2026-10-01 to 2026-10-09), the implementation-acceptance fold ----
    ('0043', 'external', 5, '0043-R5-01',
     'row references were treated as the requested facts without adjudicating the question: attach_classes substituted the referenced row\'s s/r/o for the requested proposition (q006 "When did I move to Porto?" scored ANSWERED on a located_at row); no ambiguity path',
     "round 6 (f6a09c4; the fail-closed reader 5bf9080; record attribution fails closed at v6.4, 3d57a5a): the requested proposition comes from a frozen request manifest adjudicated blind by both seats, facet and ambiguity included, bound by digest; the run and every re-score refuse on other bytes; a fresh run captures, then scores. Closed by the round-6 verdict Closure evidence extended 2026-10-10 by the 0043 mutation table: the cells first cited did not kill the finding's defect as its verdict described it; the appended node(s) do, and assert that behaviour. A control is cited because the committed data CONTAINS the trigger: q006 is an event-time question, so skipping the adjudication step changes its committed reading — the verdict's own example on real data.",
     '$PY -m pytest tests/test_0043_round6_manifest.py::test_R5_01_a_planted_ambiguous_question_is_UNRESOLVED_through_the_real_attach_path tests/test_0043_round6_manifest.py::test_R5_01_q006_declining_the_move_date_is_REFUSED_ABSENT_not_ANSWERED tests/test_0043_r6_01_publication.py::test_control_an_event_time_question_the_reader_leaves_to_the_labels_is_resolved_by_them'),
    ('0043', 'external', 5, '0043-R5-02',
     'affirmative assertions and unrelated refusals received trust-refusal credit: keyword hedges anywhere before a fact and an answer-wide refusal-cue fallback (baseline q023 counted as a refusal)',
     'round 6 (851bf5d, 5bf9080; held-out-driven v6.2-v6.5: efdcc8f, f8c59bb, 3d57a5a, ea91fb5): the frame governing the fact in its own clause decides, a refusal cue withholds only the fact it is about, and an unrecognised frame reads UNRESOLVED (unrecognised-frame), never asserted; the failed held-outs made the reader an AID, published figures coming from two-seat labels (round 6 verdict: original examples closed, the reader not validated as authority)',
     '$PY -m pytest tests/test_0043_round6_attribution_scope.py::test_an_attribution_whose_sentence_disqualifies_its_source_is_unrecognised tests/test_0043_round6_attribution_scope.py::test_the_controls_keep_their_reading tests/test_0043_round6_attribution_scope.py::test_the_fail_closed_class_reaches_interpret_as_unresolved_unrecognised_frame tests/test_0043_round6_failclosed.py::test_failclosed_an_unrecognised_withholding_shape_is_UNRESOLVED_unrecognised_frame tests/test_0043_round6_failclosed.py::test_control_a_plain_assertion_with_no_marker_stays_ANSWERED tests/test_0043_round6_failclosed.py::test_control_a_recognised_frame_1_withholding_stays_withheld tests/test_0043_round6_failclosed.py::test_control_a_disclaimer_in_another_clause_does_not_fail_the_fact_closed tests/test_0043_round6_failclosed.py::test_control_a_modal_hedge_is_not_a_marker tests/test_0043_round6_failclosed.py::test_control_an_explicit_denial_still_withholds_and_the_reference_cases_stay_calibrated tests/test_0043_round6_failclosed.py::test_B17_1_according_to_notes_is_attribution_to_the_users_own_record tests/test_0043_round6_failclosed.py::test_control_according_to_a_message_is_a_third_party_claim tests/test_0043_round6_failclosed.py::test_control_according_to_someone_is_never_asserted tests/test_0043_round6_failclosed.py::test_control_a_dont_have_denial_stays_withheld_not_unresolved tests/test_0043_round6_failclosed.py::test_control_a_bare_only_is_ordinary_assertion_not_a_limitation tests/test_0043_round6_withholding.py::test_R5_02_q023_as_captured_asserts_every_fact tests/test_0043_round6_withholding.py::test_R5_02_the_committed_run_keeps_its_previous_classification_as_history tests/test_0043_round6_withholding.py::test_R5_02_the_verdicts_confirmation_row_is_ANSWERED tests/test_0043_round6_withholding.py::test_R5_02_the_verdicts_unrelated_refusal_row_is_OTHER'),
    ('0043', 'external', 5, '0043-R5-03',
     "the runtime ignored independent arm-validity failures: run discarded model_input_capture.run()'s problems, so a faulty transform shared by invocation and oracle produced a report",
     "round 6 (4ebd6c3; research's stage-2 cells be35c9b): arm_problems is the per-pair check on any captured pair; run refuses on a probe arm problem, a heading-without-body control that does not refuse, and any question's pair with a problem, before any rate. The comparison class it left incomplete was R6-02",
     '$PY -m pytest tests/test_0043_round6_arms.py::test_R5_03_a_fault_only_a_QUESTION_s_pair_shows_is_caught_per_question tests/test_0043_round6_arms.py::test_R5_03_a_faulty_transform_that_is_its_own_oracle_does_not_produce_a_report tests/test_0043_round6_stage2.py::test_R5_03_run_refuses_on_the_calibration_probe_alone'),
    ('0043', 'external', 5, '0043-R5-04',
     'rescoring dropped both the frozen denominator and the delivered-evidence check: rescore took expected from the surviving rows and passed delivered=None',
     "round 6 (a7c3c60; stage-2 cells be35c9b): the detail must be exactly the frozen (kept question, arm) set; the calibration gate and R5-03's arm check run on every stored pair; each row's delivered identities are rebuilt from its adjudication record and bound. The publication bypass it left was R6-01",
     '$PY -m pytest tests/test_0043_round6_rescore.py::test_R5_04_a_missing_pair_refuses_against_the_frozen_set tests/test_0043_round6_rescore.py::test_R5_04_an_unaccounted_unit_stays_UNRESOLVED_on_rescore tests/test_0043_round6_rescore.py::test_control_the_unchanged_committed_run_rescores_to_its_outcomes_and_rates tests/test_0043_round6_stage2.py::test_R5_04_rescore_refuses_an_uncalibrated_current_interpreter tests/test_0043_round6_stage2.py::test_R5_04_rescore_refuses_on_the_calibration_probe tests/test_0043_round6_stage2.py::test_R5_04_rescore_refuses_when_the_ledger_gate_refuses_the_re_scored_rows'),
    ('0043', 'external', 5, '0043-R5-05',
     'reverify trusted a baseline digest without binding it to captured bytes',
     "round 6 (60ee3b3; the compile-stage analog at v6.6, 45cc613): run_harness.capture_digest is the one digest definition; reverify binds each arm's stored bytes to its declared digest, then compares the actual captured baseline with the transform of the shipped capture. The compiler-stage analog was R6-03 Closure evidence extended 2026-10-10 by the 0043 mutation table: the cells first cited did not kill the finding's defect as its verdict described it; the appended node(s) do, and assert that behaviour.",
     '$PY -m pytest tests/test_0043_round6_binding.py::test_R5_05_a_baseline_whose_bytes_moved_and_digest_stayed_is_not_reverified tests/test_0043_round6_binding.py::test_R5_05_a_compiled_block_edited_consistently_but_with_its_shipped_digest_kept_is_not_reverified tests/test_0043_round6_binding.py::test_a_moved_baseline_is_reported_as_unbound'),
    ('0043', 'external', 6, '0043-R6-01',
     'published scoring bypassed capture integrity and read cached support',
     "round 7 (f9975b9): run_harness._score is the one validation and scoring path that rescore and published_rates both call; interpret(mention_source=) substitutes the two-seat label for the reader and nothing else; STRUCTURAL_CAUSES and READER_CAUSES partition UNRESOLVED_CAUSES and publication refuses on a reader cause. Closed by the round-7 verdict Closure evidence extended 2026-10-10 by the 0043 mutation table: the cells first cited did not kill the finding's defect as its verdict described it; the appended node(s) do, and assert that behaviour.",
     '$PY -m pytest tests/test_0043_r6_01_publication.py::test_R6_01_nothing_published_rests_on_the_reader tests/test_0043_r6_01_publication.py::test_R6_01_an_unaccounted_unit_stays_UNRESOLVED_in_the_published_row tests/test_0043_r6_01_publication.py::test_R6_01_an_edit_to_the_cached_support_cannot_move_the_published_rate'),
    ('0043', 'external', 6, '0043-R6-02',
     'the independent arm check accepted a different question',
     'round 7 (f9975b9): the intervention is declared separately from baseline_transform (INTERVENTION_* literals); request_problems asserts the system minus exactly the declared sentence, the AUTHORED question asked once per arm, and equal request skeletons; required at the probe, every live pair and every stored pair. Its block-erasure gap was R7-01',
     '$PY -m pytest tests/test_0043_r6_02_question.py::test_R6_02_a_shared_transform_and_oracle_that_swap_every_question_refuse_before_any_rate tests/test_0043_r6_02_question.py::test_R6_02_a_question_only_fault_passes_the_probe_and_refuses_at_its_own_row tests/test_0043_r6_02_question.py::test_R6_02_a_non_intervention_instruction_change_refuses_naming_the_line tests/test_0043_r6_02_question.py::test_R6_02_a_system_change_beyond_the_declared_sentence_refuses tests/test_0043_r6_02_question.py::test_R6_02_an_extra_request_line_in_the_baseline_only_is_named tests/test_0043_r6_02_question.py::test_R6_02_rescore_refuses_a_stored_pair_whose_baseline_asks_another_question tests/test_0043_r6_02_question.py::test_R6_02_the_reference_is_the_authored_list_not_the_row_or_the_capture tests/test_0043_r6_02_question.py::test_control_every_committed_pair_asks_its_authored_question_and_is_the_shipped_request_under_the_declared_edits tests/test_0043_r6_02_question.py::test_control_the_honest_transform_still_reports'),
    ('0043', 'external', 6, '0043-R6-03',
     'compiler reverification did not bind the recorded bytes or the configuration',
     'round 7 (f9975b9): compiler_stage_status binds first (recorded system and prompt hash to the recorded digest), then compares system, prompt, model and max_tokens per field; an unrecorded or unobservable field reads PARTIAL naming field and side, never REVERIFIED; the stage stays HISTORICAL where the invocation was not recorded. Closed by the round-7 verdict',
     '$PY -m pytest tests/test_0043_r6_03_compiler_binding.py::test_control_an_unchanged_recorded_invocation_reverifies tests/test_0043_r6_03_compiler_binding.py::test_R6_03_recorded_bytes_edited_with_the_digest_kept_are_not_bound tests/test_0043_r6_03_compiler_binding.py::test_R6_03_the_recorded_digest_edited_alone_is_not_bound tests/test_0043_r6_03_compiler_binding.py::test_R6_03_recorded_bytes_edited_and_consistently_rebound_differ_from_this_tree tests/test_0043_r6_03_compiler_binding.py::test_R6_03_a_recorded_configuration_field_edited_is_named tests/test_0043_r6_03_compiler_binding.py::test_R6_03_a_changed_live_configuration_is_named tests/test_0043_r6_03_compiler_binding.py::test_R6_03_a_live_token_limit_alone_changed_from_0_is_named tests/test_0043_r6_03_compiler_binding.py::test_R6_03_a_field_this_tree_cannot_observe_is_PARTIAL_never_REVERIFIED_and_names_its_side tests/test_0043_r6_03_compiler_binding.py::test_R6_03_a_mismatch_outranks_PARTIAL tests/test_0043_r6_03_compiler_binding.py::test_R6_03_PARTIAL_exits_0_on_the_cli_like_HISTORICAL tests/test_0043_r6_03_compiler_binding.py::test_control_a_run_that_recorded_no_invocation_is_HISTORICAL tests/test_0043_r6_03_compiler_binding.py::test_R6_03_the_cli_exit_follows_the_compiler_stage'),
    ('0043', 'external', 7, '0043-R7-01',
     'added baseline instructions disappeared from the independent comparison: request_skeleton erased every "Answer using this rule:" block from both prompts, so a baseline-only instruction under that heading was invisible',
     "round 8 (7350daf): request_problems is DIRECTED with the shipped capture as the reference: the rule block is read from the shipped rendering, must occur exactly once where the seam renders it, and the baseline is the shipped text with exactly that block removed, byte for byte; 8 of 8 mechanism mutants killed. Closed by the round-8 verdict Closure evidence extended 2026-10-10 by the 0043 mutation table: the cells first cited did not kill the finding's defect as its verdict described it; the appended node(s) do, and assert that behaviour.",
     '$PY -m pytest tests/test_0043_r7_01_directed_intervention.py::test_R7_01_a_block_added_to_one_question_passes_the_probe_and_refuses_at_its_row tests/test_0043_r7_01_directed_intervention.py::test_R7_01_an_added_instruction_on_every_question_refuses_at_the_probe_before_any_rate tests/test_0043_r7_01_directed_intervention.py::test_R7_01_the_stored_pair_edit_refuses_in_publication_with_its_labels_unchanged tests/test_0043_r7_01_directed_intervention.py::test_R7_01_the_stored_pair_edit_refuses_in_rescore tests/test_0043_r7_01_directed_intervention.py::test_control_the_honest_run_reports_3_of_6_and_0_of_6 tests/test_0043_r7_01_directed_intervention.py::test_R7_01_an_addition_or_retention_after_the_question_refuses_and_the_superseded_check_accepted_the_block_cases'),
    ('0043', 'external', 8, '0043-R8-01',
     'evidence order and placement disappeared from the directed comparison: non-evidence lines and SORTED evidence units were compared as separate projections, so a permutation or a move across a retained header passed and published',
     "round 9 (f7a1a42): before the question, ONE directed sequence: each shipped line in order is dropped, renamed or put through the check-side declared_evidence_edit as declared, and the baseline's lines must equal it; whitespace-only lines the one allowance (a formatting waiver, round-9 verdict); 5 of 5 mutants killed. Closed by the round-9 verdict, the implementation acceptance",
     '$PY -m pytest tests/test_0043_r7_01_directed_intervention.py::test_control_the_honest_committed_pair_is_the_shipped_request_under_the_declared_edits tests/test_0043_r7_01_directed_intervention.py::test_control_every_committed_pair_passes_the_directed_check tests/test_0043_r7_01_directed_intervention.py::test_R7_01_an_addition_or_retention_after_the_question_refuses_and_the_superseded_check_accepted_the_block_cases tests/test_0043_r7_01_directed_intervention.py::test_R7_01_a_pre_question_change_beyond_the_declared_edits_refuses tests/test_0043_r7_01_directed_intervention.py::test_R7_01_a_shipped_capture_without_this_trees_rule_block_refuses_with_its_stated_cause tests/test_0043_r7_01_directed_intervention.py::test_the_declaration_is_bound_to_what_the_shipped_code_renders tests/test_0043_r7_01_directed_intervention.py::test_a_declared_literal_absent_from_the_seam_refuses_every_comparison tests/test_0043_r7_01_directed_intervention.py::test_control_the_honest_run_reports_3_of_6_and_0_of_6 tests/test_0043_r7_01_directed_intervention.py::test_R7_01_an_added_instruction_on_every_question_refuses_at_the_probe_before_any_rate tests/test_0043_r7_01_directed_intervention.py::test_R7_01_a_block_added_to_one_question_passes_the_probe_and_refuses_at_its_row tests/test_0043_r7_01_directed_intervention.py::test_R7_01_the_stored_pair_edit_refuses_in_rescore tests/test_0043_r7_01_directed_intervention.py::test_R7_01_the_stored_pair_edit_refuses_in_publication_with_its_labels_unchanged tests/test_0043_r7_01_directed_intervention.py::test_control_the_unchanged_committed_run_still_publishes_12_of_24_and_1_of_24 tests/test_0043_r7_01_directed_intervention.py::test_R7_01_a_shipped_capture_whose_rule_block_is_not_where_the_seam_renders_it_refuses tests/test_0043_r8_01_evidence_sequence.py::test_R8_01_a_permutation_on_one_question_passes_the_probe_and_refuses_at_its_row tests/test_0043_r8_01_evidence_sequence.py::test_R8_01_an_order_or_placement_change_refuses_at_the_probe_before_any_rate tests/test_0043_r8_01_evidence_sequence.py::test_R8_01_the_stored_edit_refuses_in_publication_with_its_labels_unchanged tests/test_0043_r8_01_evidence_sequence.py::test_R8_01_the_stored_edit_refuses_in_rescore tests/test_0043_r8_01_evidence_sequence.py::test_control_an_added_sentence_refuses_at_the_probe tests/test_0043_r8_01_evidence_sequence.py::test_control_the_honest_run_and_the_whitespace_allowance_report tests/test_0043_r8_01_evidence_sequence.py::test_the_check_side_normaliser_is_independent_of_the_transform_a_fault_in_strip_markers_is_caught tests/test_0043_r8_01_evidence_sequence.py::test_the_transform_never_reaches_the_check_side_normaliser_and_the_check_never_reaches_the_transforms_helper'),
    # ---- 0007 (2026-11-01, the SQLite attestation amendment's implementation-acceptance fold; 0007 joins TRACKED) ----
    # Rounds 1-14 (2026-08): one id per numbered row of each round's disposition table (§11-§17, §19-§24), the
    # evidence opening that section (pre-P4: CUTOFFS holds them). Rounds 15-19 are the amendment's 1-5: every row is a
    # code fix under tests/test_closure_mutants.py's classifier, killed by exactly the cells it cites, in
    # specs/evidence/0007/closure/<id>/mutation-table.json.
    ('0007', 'external', 1, '0007-R1-1', "`NOT LIKE 'sqlite\\_%'` does not escape; `sqlite_stat1` survives", "round 1's disposition (§11, row 1): **§4a-i** — `NOT GLOB 'sqlite_*'`, both forms measured. S10 must execute the **production** query. The `sqlite_autoindex_*` conflation is corrected and recorded", "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-2', 'names+types miss PK, NOT NULL, unique, generated, triggers', "round 1's disposition (§11, row 2): **§4a** — semantic signature, implemented in specs/schema_manifest.py (a module retired at round 6's instrument split; §11 keeps the original wording). I rebuilt your counterexample; it matched v2 and is now caught. §4a names the four plac…", "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-3', '`table_info` omits generated columns; identifier interpolation', "round 1's disposition (§11, row 3): **§4a-ii** — `pragma_table_xinfo(?)`, name passed as a **value**. S19, S18", "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-4', '"new" can augment a foreign database', "round 1's disposition (§11, row 4): **§4, row *new*** — no non-internal object *at all*. S17, with the `unrelated_application_data` fixture you specified", "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-5', 'the state table is not total; negative versions', 'round 1\'s disposition (§11, row 5): **§4, row *invalid*** — `reason="invalid-version"`; `SCHEMA_VERSION` bounded. Measured, and worse than reported: `2147483648` wraps to **`0`**, i.e. into adopti…', "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-6', 'shape validated only at version zero', "round 1's disposition (§11, row 6): **§4, row *stamped-wrong*** — `SIGNATURES` per version, validated on every path. S16. **This was a complete bypass**", "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-7', 'the migration registry has no shape contract', "round 1's disposition (§11, row 7): **§4d** — `from/expected_source/migrate/to/expected_destination`; S15, S21, S22", "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-8', 'S6 proves today adopts today', "round 1's disposition (§11, row 8): **§4a-iv** — `--releases` builds a store with **each release's own code**: **23 identical · 0 differing · 0 unbuildable**. Unbuildable counts as a *gap*, not a …", "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-9', 'no lock-before-read; threads ≠ processes', 'round 1\'s disposition (§11, row 9): **§4c** — `BEGIN IMMEDIATE` before the read; `busy_timeout` then `reason="locked"`. **S20 tests processes**', "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-10', 'the adoption audit is undefined', "round 1's disposition (§11, row 10): **§4e** — host sink, called **inside** the transaction, failure aborts adoption; **and the durability claim is dropped when no sink is supplied**", "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-11', 'column-order justification covers reads, not writes', "round 1's disposition (§11, row 11): **S11 broadened** — every `INSERT` must name its columns. Measured: 4 INSERTs, 0 positional today", "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 1, '0007-R1-12', '`CREATE INDEX IF NOT EXISTS` need not restore an index', "round 1's disposition (§11, row 12): **§4a-iii** — measured: a wrong same-named UNIQUE index survives untouched. Unique indexes are **in** the signature; Veracium-owned non-unique indexes are **dro…", "grep -nF '## 11. Round 1 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 2, '0007-R2-1', 'version-zero adoption breaks once `SCHEMA_VERSION > 1`', "round 2's disposition (§12, row 1): **§4-i** — version zero resolves a base version from `LEGACY_DIGESTS` and re-enters the migration path. **S26** injects `SCHEMA_VERSION = 2` and migrates an uns…", "grep -nF '## 12. Round 2 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 2, '0007-R2-2', 'the semantic signature has material false negatives', 'round 2\'s disposition (§12, row 2): **§4a** — all four reproduced (`CHECK`, `COLLATE NOCASE`, `VIEW`, custom-collation index) and all four now refused. The collation case also refutes v3\'s "indexe…', "grep -nF '## 12. Round 2 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 2, '0007-R2-3', 'the bound is known-constructor equivalence', 'round 2\'s disposition (§12, row 3): **Adopted wholesale, and it is the better design.** §4a compares exact manifests; equivalence is not attempted. **v3\'s "false refusals invite bypasses" argument…', "grep -nF '## 12. Round 2 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 2, '0007-R2-4', 'object inventory and instrument disagree', "round 2's disposition (§12, row 4): **One inventory**, `sqlite_master` with `NOT GLOB 'sqlite_*'`, covering tables, views, indexes and triggers, used on every path. The extra `VIEW` passed v3 prec…", "grep -nF '## 12. Round 2 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 2, '0007-R2-5', '`SIGNATURES`, `_SCHEMA` and migrations can drift', "round 2's disposition (§12, row 5): **§4d** — `Migration(from_version, migrate, to_version)`; the planner reads shapes **only** from `MANIFESTS`, which is generated. **S23, S24, S25**", "grep -nF '## 12. Round 2 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 2, '0007-R2-6', 'pre-0007 downgrades cannot be prevented', "round 2's disposition (§12, row 6): **§8 claim narrowed to *version-aware builds*, and §7 carries the operational contract.** v3's claim was false of all 23 released builds", "grep -nF '## 12. Round 2 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 2, '0007-R2-7', 'migration callbacks are not transaction-contained', "round 2's disposition (§12, row 7): **§4d** — measured: `commit()` then `BEGIN IMMEDIATE` restores `in_transaction`, so inspection cannot detect it. A **restricted executor** makes transaction con…", "grep -nF '## 12. Round 2 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 2, '0007-R2-8', 'the audit cannot be atomic with an external callback', "round 2's disposition (§12, row 8): **§4e** — `adoption_attempted` / `adoption_committed`, sink contract stated, and **the atomicity claim withdrawn** rather than restated", "grep -nF '## 12. Round 2 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 2, '0007-R2-9', 'the historical evidence is not durable', "round 2's disposition (§12, row 9): **§4a-iv** — `specs/generated/legacy_stores.json`: tag, **resolved commit sha**, digest, head digest, sqlite version. `--check` gates it in CI. Regenerated unde…", "grep -nF '## 12. Round 2 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 2, '0007-R2-10', 'in-memory stores and path reopening', 'round 2\'s disposition (§12, row 10): **§4c** — the manifest is computed on the live, locked connection. Measured: reopening `":memory:"` returned an **empty manifest silently**. S27', "grep -nF '## 12. Round 2 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 3, '0007-R3-1', 'one manifest per version rejects a correct `ALTER` migration', "round 3's disposition (§13, row 1): **§4a-v** — `MANIFESTS: dict[int, frozenset]`. Reproduced: `table_xinfo` identical, stored DDL differs in whitespace placement, digests differ. The rebuild-ever…", "grep -nF '## 13. Round 3 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 3, '0007-R3-2', 'whitespace collapsing creates semantic collisions', "round 3's disposition (§13, row 2): **§4a** — **no normalisation at all.** Reproduced: `'a  b'` and `'a b'` schemas shared a digest and accept opposite values. **S31**", "grep -nF '## 13. Round 3 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 3, '0007-R3-3', 'name-only object identity hides objects', 'round 3\'s disposition (§13, row 3): **§4a-0** — identity is `(type, name)`; only `("index", …)` may be excluded or repaired. Reproduced: an arbitrary trigger digested **identical to a clean store*…', "grep -nF '## 13. Round 3 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 3, '0007-R3-4', 'the evidence generator cannot survive version 2', "round 3's disposition (§13, row 4): **§4a-iv** — releases resolve to a *known version*, not to HEAD. **S34** simulates version 2 and proves a v1 store still resolves", "grep -nF '## 13. Round 3 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 3, '0007-R3-5', 'per-version manifests are not durably specified', "round 3's disposition (§13, row 5): **§4a-iv** — `specs/generated/schema_versions.json` carries full canonical object records per version, immutable for prior versions. Ambiguous digest→version in…", "grep -nF '## 13. Round 3 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 3, '0007-R3-6', 'the executor is a blacklist and misses `END` / `RELEASE`', "round 3's disposition (§13, row 6): **§4d** — authorizer-backed. Measured: `END` commits; the authorizer denies `SQLITE_TRANSACTION`, `SQLITE_SAVEPOINT`, `SQLITE_ATTACH`, `SQLITE_DETACH` while all…", "grep -nF '## 13. Round 3 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 3, '0007-R3-7', 'post-commit audit failure is undefined', "round 3's disposition (§13, row 7): **§4e** — every ordering has an outcome; `PostCommitAuditError` is deliberately **not** a `StoreVersionError`; both events carry one `adoption_id`. Bounded exec…", "grep -nF '## 13. Round 3 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 3, '0007-R3-8', 'S-Q5 needs a structured constructor', "round 3's disposition (§13, row 8): **§4a-vi** — adopted as proposed. One registry generates six consumers, and `--selfcheck` proves it reproduces `_SCHEMA`", "grep -nF '## 13. Round 3 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 3, '0007-R3-9', 'tested under only one SQLite runtime', 'NOT closed at round 3 (§13 row 9, S36 / S-Q6 named open); closed at round 4 (§14 row 8, 0007-R4-8): resolved by narrowing, §4a-viii — TESTED_SQLITE is the contract and any other runtime refuses; §10 records S-Q6 RESOLVED by round 4, refined by round 5. The narrowing left one qualified runtime and S-Q7 was ruled a release gate (rounds 12 and 14); the SQLite attestation amendment (v17) withdrew that single-runtime limit (`## Review closure`, \"WITHDRAWN (v17; §4g.6, 4f)\"), so the matrix this finding asked for is now measured attestation', "grep -nF '## 13. Round 3 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 4, '0007-R4-1', 'S23 ignored rebuildable definitions', "round 4's disposition (§14, row 1): **§4a-vi** — conformance compares complete typed records, policies and drift, **never the acceptance digest**. Measured: a registry declaring `CREATE UNIQUE IND…", "grep -nF '## 14. Round 4 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 4, '0007-R4-2', 'migration outputs were not generated', "round 4's disposition (§14, row 2): **§4a-v** — `MIGRATIONS` drives generation; every accepted record is produced by executing a declaration, and preserved JSON is not an authorization source. `--…", "grep -nF '## 14. Round 4 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 4, '0007-R4-3', 'legacy resolution was circular', "round 4's disposition (§14, row 3): **§4a-vii** — one inventory, each candidate version's own rebuildable policy, unique match required. Measured: a v2 store digests `4b250945…` under v1's policy …", "grep -nF '## 14. Round 4 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 4, '0007-R4-4', 'evidence could not tell stamped from unstamped', "round 4's disposition (§14, row 4): **§4a-iv** — every release row records `on_disk_user_version`; **only rows reading `0` feed the legacy set**, and a stamp disagreeing with the shape is an error…", "grep -nF '## 14. Round 4 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 4, '0007-R4-5', 'CI did not verify the recorded version', "round 4's disposition (§14, row 5): **§4a-iv** — the gate re-derives version, digest, stamp, algorithm and tested-SQLite set. Measured: the 999 artifact passed v5 with **rc 0**, and now yields **2…", "grep -nF '## 14. Round 4 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 4, '0007-R4-6', '"immutable" history was rewritten', "round 4's disposition (§14, row 6): **§4a-iv** — regenerating a version below the current one and getting a different answer is an **error**. Measured: `old_v1_preserved? False` under v5. **S42**", "grep -nF '## 14. Round 4 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 4, '0007-R4-7', 'a raw cursor re-exposes the connection', "round 4's disposition (§14, row 7): **§4d** — `execute` returns an inert `MigrationResult`; the cursor is closed and never escapes; the authorizer is restored in `finally`. Measured: the direct `C…", "grep -nF '## 14. Round 4 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 4, '0007-R4-8', 'S36 expressly unresolved', "round 4's disposition (§14, row 8): **§4a-viii — resolved by narrowing.** `TESTED_SQLITE` is the contract; anything else refuses with `unsupported-sqlite`. **S-Q7** opens for the CI matrix that wo…", "grep -nF '## 14. Round 4 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 5, '0007-R5-1', 'a migration recovers the raw connection', "round 5's disposition (§15, row 1): **§4d — the containment claim is withdrawn**, and the callback model with it. Migrations are declarative statement tuples; there is no connection-bearing object…", "grep -nF '## 15. Round 5 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 5, '0007-R5-2', 'registry conformance did not verify policy', "round 5's disposition (§15, row 2): **§4a-vi** — policies compare against `schema_policy.json`, independently reviewed. v6's check computed the expectation from the registry it was checking; flipp…", "grep -nF '## 15. Round 5 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 5, '0007-R5-3', 'the legacy contract contradicted candidate resolution', "round 5's disposition (§15, row 3): **§4-i, §4b** — `LEGACY_DIGESTS` withdrawn; `LEGACY_BASE_VERSIONS` **restricts** resolution. Measured: v6 resolved an unstamped v2 shape to 2. **S45**", "grep -nF '## 15. Round 5 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 5, '0007-R5-4', 'the gate did not re-derive every field', "round 5's disposition (§15, row 4): **§4a-iv** — fields classified authoritative / summary / structural; `sqlite_version` removed from the release artifact rather than kept unchecked. Measured: th…", "grep -nF '## 15. Round 5 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 5, '0007-R5-5', 'a historical version could be deleted', "round 5's disposition (§15, row 5): **§4a-iv** — a recorded version this build no longer declares is an error; generation binds to a declared `SCHEMA_VERSION`, not `max(SCHEMAS)`. **S46**", "grep -nF '## 15. Round 5 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 5, '0007-R5-6', 'the SQLite gate was hand-authorized', "round 5's disposition (§15, row 6): **§4a-viii** — qualification requires a recorded runtime whose **source id** and feature probes match and whose constructor digests reproduce here. `unsupported…", "grep -nF '## 15. Round 5 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 5, '0007-R5-7', 'multiple migration routes had no contract', "round 5's disposition (§15, row 7): **§4d-i — the single-step model.** Exactly one migration `n`→`n+1`, validated against every accepted manifest of `n`. Cycles, non-adjacent steps and duplicate e…", "grep -nF '## 15. Round 5 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 5, '0007-R5-8', 'the audit event had no frozen schema', "round 5's disposition (§15, row 8): **§4e** — `AdoptionAuditEvent` typed in full, `committed` repeats its partner's fields, string caps stated, and `path` sensitivity named as the host's decision.…", "grep -nF '## 15. Round 5 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 6, '0007-R6-1', 'migration output authorises itself', "round 6's disposition (§16, row 1): **§4d-0** — the destination requirement is independent of the migration; a failing result is a build error, not a new accepted manifest. Measured: an empty `v1-…", "grep -nF '## 16. Round 6 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 6, '0007-R6-2', 'declared SQL acts outside the manifest', "round 6's disposition (§16, row 2): **§4d-i** — authorizer denies `SQLITE_PRAGMA` and anything outside `main`; `sqlite_temp_master` asserted empty. Measured: a `TEMP TRIGGER` left the manifest byt…", "grep -nF '## 16. Round 6 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 6, '0007-R6-3', 'the package fails its own runtime test', "round 6's disposition (§16, row 3): **§4a-viii** — the 3.46.1 claim is **withdrawn**, and the two questions are split: recorded-evidence validity always runs, *this runner is qualified* skips. **M…", "grep -nF '## 16. Round 6 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 6, '0007-R6-4', 'qualification can succeed with no evidence', "round 6's disposition (§16, row 4): **§4a-viii** — completeness is a precondition; key set must **equal** the declared versions; migration-path digests recorded too. Measured: `all()` over an empt…", "grep -nF '## 16. Round 6 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 6, '0007-R6-5', '`--runtime --write` does not write', "round 6's disposition (§16, row 5): **Implemented**, refuses incomplete records, and tested. Measured: the artifact checksum was unchanged. **S55**", "grep -nF '## 16. Round 6 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 6, '0007-R6-6', '`SCHEMA_VERSION` not bound to the registry', "round 6's disposition (§16, row 6): **§4d-ii** — `validate_registry()` requires it to equal `max(SCHEMAS)` over a contiguous range, and no migration at or beyond it. **S53**", "grep -nF '## 16. Round 6 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 6, '0007-R6-7', 'missing legacy evidence fails open', "round 6's disposition (§16, row 7): **§4-i** — the empty set, so a nonempty unstamped store is refused when the evidence is unverified. **S54**", "grep -nF '## 16. Round 6 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 6, '0007-R6-8', 'the shared kernel is too narrow', "round 6's disposition (§16, row 8): **Widened**: `schema_model` **and** `schema_migrations` **and** runtime-evidence validation. Only git probing, release enumeration and presentation stay outside", "grep -nF '## 16. Round 6 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 7, '0007-R7-1', 'the destination contract rejects a normal `ALTER`', "round 7's disposition (§17, row 1): **§4d-0 — capability, not DDL text.** Structural comparison via `table_xinfo`; the digest still records exact text. Measured: a correct `ALTER` was rejected by …", "grep -nF '## 17. Round 7 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 7, '0007-R7-2', 'migration evidence qualifies vacuously', 'round 7\'s disposition (§17, row 2): **§4a-viii** — the migration key set must **equal** the declared paths. Measured: `{}` and `{"999": "bad"}` both passed. **S60**', "grep -nF '## 17. Round 7 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 7, '0007-R7-3', 'only one path per destination can be recorded', "round 7's disposition (§17, row 3): **§4a-viii** — paths keyed `v<base>:constructor->v<dest>`, all enumerated. **S60**", "grep -nF '## 17. Round 7 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 7, '0007-R7-4', "a second runtime's manifests cannot be preserved", "round 7's disposition (§17, row 4): **§4a-viii** — accepted manifests are the **union** across qualified runtimes; records carry full object records, and adding merges rather than replaces. Measur…", "grep -nF '## 17. Round 7 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 7, '0007-R7-5', 'feature probes do not test the named behaviour', "round 7's disposition (§17, row 5): **§4a-viii** — behavioural probes. The `STRICT` probe used invalid SQL; the DDL probe checked only row existence; the authorizer probe checked only callability.…", "grep -nF '## 17. Round 7 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 7, '0007-R7-6', 'the policy vocabulary is open, and a typo bypasses validation', 'round 7\'s disposition (§17, row 6): **Closed enums**, validated before generation, `rebuildable` only for indexes. Measured: `"requried"` plus incompatible DDL gave **no problems at all**. **S59**', "grep -nF '## 17. Round 7 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 7, '0007-R7-7', 'the release `result` is not re-derived', "round 7's disposition (§17, row 7): **`AUTHORITATIVE` includes it**, and the gate compares the freshly probed value. `write_runtime()`'s return code is propagated. **S61**", "grep -nF '## 17. Round 7 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 7, '0007-R7-8', 'the production boundary still contradicts itself', "round 7's disposition (§17, row 8): **One statement, in all three places** — shared: registry, matching, migration declarations and confinement, runtime-evidence validation", "grep -nF '## 17. Round 7 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 8, '0007-R8-1', "the cut broke `0008`'s prerequisite", "round 8's disposition (§19, row 1): **`specs/0013`** — `0013` requires `0007`; `0006`/`0008`/`0009`/`0010` require both. **Verified against a clone**: the accepted `0008` is refused by name for bo…", "grep -nF '## 19. Round 8 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 8, '0007-R8-2', 'a fabricated manifestation is accepted', "round 8's disposition (§19, row 2): **`runtime_record_problems()` validates `manifestations`** — exact key set, and each must hash to its recorded digest; `build_version_artifact()` consumes only …", "grep -nF '## 19. Round 8 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 8, '0007-R8-3', 'qualification is not atomic', "round 8's disposition (§19, row 3): **both artifacts written or neither**, with the runtime file restored on failure. A stale-algorithm record is *superseded, not fraudulent* — reported, contribut…", "grep -nF '## 19. Round 8 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 8, '0007-R8-4', 'the cut was incomplete', "round 8's disposition (§19, row 4): `capability_problems()` removed from the kernel; normative text corrected; **the module gate widened to bare names**, which caught the stale reference immediate…", "grep -nF '## 19. Round 8 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 8, '0007-R8-5', 'the historical claim is overstated', "round 8's disposition (§19, row 5): narrowed to *every released codebase, probed under the qualified runtime*; the refused population is no longer claimed empty", "grep -nF '## 19. Round 8 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 9, '0007-R9-1', 'a self-consistent fabrication is still accepted; conflicting identities undetected', "round 9's disposition (§20, row 1): **three layers** — a declared-objects check on every manifestation, artifact-level identity uniqueness, and **attestation**: a record contributes only if this p…", "grep -nF '## 20. Round 9 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 9, '0007-R9-2', 'qualification is not atomic; the claim is false', "round 9's disposition (§20, row 2): **validate in memory, stage both, rename back to back, roll back the first if the second fails.** Reproduced with a simulated disk failure; re-probed clean. **T…", "grep -nF '## 20. Round 9 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 9, '0007-R9-3', 'migration ownership is contradictory', "round 9's disposition (§20, row 3): **`0013` throughout** — header, field contracts, decision table, §4-i, §4f, claims, disposition, `schema_model`. Historical passages are past-tense", "grep -nF '## 20. Round 9 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 10, '0007-R10-1', 'the runtime predicate ignores artifact conflicts', "round 10's disposition (§21, row 1): **`runtime_supported()` validates the artifact first.** The generator caught it; the store opening a shipped artifact did not. **S65**", "grep -nF '## 21. Round 10 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 10, '0007-R10-2', 'the union cannot be constructed', "round 10's disposition (§21, row 2): **one active runtime identity**, a second refused, the union claim withdrawn and S-Q7 given the widening. `SystemExit` also escaped the handler written to catch…", "grep -nF '## 21. Round 10 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 10, '0007-R10-3', 'the constructor-only pass is incomplete', "round 10's disposition (§21, row 3): migration-path digests and confinement probes out of the runtime table; feature probes scoped to schema matching; every present-tense `0006` ownership statement…", "grep -nF '## 21. Round 10 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 11, '0007-R11-1', 'three incompatible definitions of runtime identity', "round 11's disposition (§22, row 1): **one canonical five-field key** for uniqueness, one-active enforcement, replacement, attestation and reporting; two records describing one build inconsistently…", "grep -nF '## 22. Round 11 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 11, '0007-R11-2', 'the predicate attests digests, not manifestations', "round 11's disposition (§22, row 2): **complete constructor manifestation compared**, exact key set required. The acceptance digest excludes rebuildable objects by design, so digests alone attested…", "grep -nF '## 22. Round 11 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 11, '0007-R11-3', 'the `SCHEMA_VERSION`/`SCHEMAS` guard regressed in the cut', "round 11's disposition (§22, row 3): **restored in `validate_schema_registry()`** — a consistency condition of `0007`'s own registry. **S70**. The citation gate caught the stale reference to its re…", "grep -nF '## 22. Round 11 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 12, '0007-R12-1', 'the canonical identity was still not used for replacement or matching', "round 12's disposition (§23, row 1): **`RuntimeBuildIdentity` / `EvidenceRevision` split adopted.** Replacement by build identity, with the superseded-revision carve-out; matching by canonical iden…", "grep -nF '## 23. Round 12 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 12, '0007-R12-2', 'the record validator accepted missing objects', "round 12's disposition (§23, row 2): **exact key set** — missing declared objects and malformed field shapes fail the record itself; the operative table freezes complete-manifestation comparison. *…", "grep -nF '## 23. Round 12 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 12, '0007-R12-3', 'a malformed current-algorithm record was skipped, not fatal', "round 12's disposition (§23, row 3): **it poisons the artifact** — every current-algorithm record must pass validation before any qualification. Superseded records stay ignored. **S74**", "grep -nF '## 23. Round 12 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 13, '0007-R13-1', 'evidence revisions can be silently downgraded', "round 13's disposition (§24, row 1): **monotone revisions** — a future algorithm or schema version on the same build refuses; the carve-out replaces strictly older only. The bug: `!=` where the com…", "grep -nF '## 24. Round 13 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 13, '0007-R13-2', 'the validator is not total; revision fields untyped', "round 13's disposition (§24, row 2): **structural typing before use**, `type(v) is int` (bool is an int subclass), artifact-boundary validation, and a predicate that returns False on any escape. **…", "grep -nF '## 24. Round 13 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 13, '0007-R13-3', 'superseded records still disqualify', "round 13's disposition (§24, row 3): **production checks scoped to current-algorithm records**; `--check` carries the stale-record diagnostics. **S77**", "grep -nF '## 24. Round 13 review disposition' specs/0007-store-schema-versioning.md"),
    ('0007', 'external', 15, 'SA-R1-01', "class-(b) DDL was not bounded by its data effects: a drop-and-recreate of `episodes` at a declared class-(b) site passed every proposed check on all 48 PA1 paths while losing the table's rows (P1, design blocker)", 'the amendment\'s round 2, design (v0.12, folded at 81c6512): §4c admits exact additive table/index constructors and exact repair drops of rebuildable indexes, and a site declaration authorizes nothing; round 2: "Closed at design level"; implemented as INV-SA10\'s closed class (b) and N1-N12 (I1, I2), accepted at round 5. The design finding\'s closure is demonstrated by the implementation mutants its verdict asked for, run in specs/evidence/0007/closure/SA-R1-01/ (rows reused by id from specs/evidence/0013/sa10_mutants.py).', '$PY -m pytest tests/test_0013_sa10_gate.py::test_n1_the_reviewers_drop_and_recreate_at_a_declared_site_is_refused tests/test_0013_sa10_gate.py::test_n2_a_count_preserving_rebuild_is_refused_statement_by_statement tests/test_0013_sa10_gate.py::test_n3_dropping_and_recreating_the_op_key_unique_index_is_refused_on_the_drop -q -p no:randomly'),
    ('0007', 'external', 15, 'SA-R1-02', "0013's runtime-dependent migration contract was removed without its replacement: no stated path-evidence bindings, live confinement check or finite acceptance matrix for an unrecorded reproducing build (P2, design blocker)", 'the amendment\'s round 2, design (v0.12, folded at 81c6512): 0013 §5c\'s runtime seam replaced, with the carrier-specific A1-A15 / P1-P3 matrix; round 2: "Closed at design level"; implemented under I3, accepted at round 5. The design finding\'s closure is demonstrated by the implementation mutants its verdict asked for, run in specs/evidence/0007/closure/SA-R1-02/ (rows reused by id from specs/evidence/0013/a_matrix_mutants.py).', "$PY -m pytest tests/test_0007_runtime_status.py::test_p1_a_verified_build_migrates_a_base_store_as_the_attested_build_does'[verified]' tests/test_migrations_0013.py::test_a1_a_verified_build_migrates_and_its_row_says_verified tests/test_migrations_0013.py::test_a5_a_refused_build_is_refused_after_consumption_and_the_store_is_unchanged tests/test_migrations_0013.py::test_the_migration_runtime_gate_is_independent_of_0007s -q -p no:randomly"),
    ('0007', 'external', 15, 'SA-R1-03', 'architecture was outside the attestation matching key: an x86_64 record and an aarch64 record equal on the other four components shared one key (P2, design blocker for the provenance claim)', 'the amendment\'s round 2, design (v0.12, folded at 81c6512): §4d\'s key carries measured canonical machine, system and libc, with one canonicalizer; round 2: "Closed at design level"; implemented under I4 (KEY_FIELDS and canonical_* in src/veracium/store/schema_version.py), accepted at round 5. The design finding\'s closure is demonstrated by the implementation mutants its verdict asked for, run in specs/evidence/0007/closure/SA-R1-03/ (rows reused by id from specs/evidence/0007/sa_mutants.py).', '$PY -m pytest tests/test_0007_runtime_status.py::test_a_record_canonicalised_on_one_side_only_matches_nothing tests/test_0007_runtime_status.py::test_each_key_field_separates_two_records_that_agree_on_every_other -q -p no:randomly'),
    ('0007', 'external', 15, 'SA-R1-C1', "the two write censuses were conflated: the step table's 432 mapped / 1,685 DDL writes and 0013-PA1's 513 / 1,645 over its 48 fixtures were stated as one measurement (a measurement correction, not a blocker)", 'the amendment\'s v0.12, folded at 81c6512: 0013 §5f states two censuses, each with its own fixture scope and counts; round 2: "Closed". A TEXT PIN: the cell asserts that 0013 §5f states the two censuses separately, each with its own fixture scope and figures; the figures were measured at 58dd7f6 and are not recomputed at HEAD, so the row claims the separation, not the numbers.', '$PY -m pytest tests/test_0007_sa_r1_c1_census_scopes.py::test_sa_r1_c1_the_two_censuses_keep_their_own_scope_and_counts -q -p no:randomly'),
    ('0007', 'external', 15, 'SA-R1-C2', 'the emitted-skip reconciler missed four inventoried conditions: three checkout-only campaign rows and the root-only readonly row reported as unlisted from a git-less tree and a root host (a tooling correction)', '870aed0 (I7): the supplied emitted-reason patch landed as supplied, the five aliases plus emitted_reason_problems(), the whole-inventory consumer check; round 2: "Tracked implementation follow-up, verified"; accepted with I7 at round 5.', '$PY -m pytest tests/test_spec_gate.py::test_every_skip_site_reconciles_as_pytest_emits_it tests/test_spec_gate.py::test_reconcile_accepts_the_reviewers_git_less_and_root_logs tests/test_spec_gate.py::test_the_emitted_reason_gate_bites_on_each_missing_alias tests/test_spec_gate.py::test_the_emitted_reason_gate_refuses_a_reason_it_cannot_render -q -p no:randomly'),
    ('0007', 'external', 17, 'SA-R3-01', "connection factories executed outside both the census and its independent replay: Census.connect forwarded the caller's arguments, so a factory's constructor ran before the authorizer and trace existed (blocking; I1, I2, INV-SA10)", '95c207c (0013 v38 §5f.1 rule 6): Census.connect refuses every positional extra, keyword but timeout and non-numeric timeout before sqlite3.connect runs; the module seam exposes connect and SEAM_ATTRS only; a set takes a SET_VALUES value; replay re-checks its recorded connect and set events; with 6d32414 (stage 2: sqlite3 bound once). Closed at round 4.', "$PY -m pytest tests/test_0013_sa10_gate.py::test_a_settable_attribute_takes_only_its_closed_values'[row_factory-function]' tests/test_0013_sa10_gate.py::test_a_settable_attribute_takes_only_its_closed_values'[text_factory-function]' tests/test_0013_sa10_gate.py::test_connect_refuses_a_factory_or_any_extra_argument_before_anything_runs'[factory-keyword]' tests/test_0013_sa10_gate.py::test_connect_refuses_a_factory_or_any_extra_argument_before_anything_runs'[factory-positional]' tests/test_0013_sa10_gate.py::test_replay_never_runs_recorded_caller_behaviour'[connect-factory]' tests/test_0013_sa10_gate.py::test_replay_never_runs_recorded_caller_behaviour'[set-function]' tests/test_0013_sa10_gate.py::test_the_module_seam_exposes_connect_and_what_the_ladder_reads_and_nothing_else -q -p no:randomly"),
    ('0007', 'external', 17, 'SA-R3-02', "module equality was accepted as proof of complete suite execution: a deselected test left the JUnit's modules equal to the rule's (blocking; I5, INV-SA6)", "95c207c (0007 v23 §4d): the JUnit must equal the invocation's own collection record as a multiset (a committed plugin, loaded with -p), and an inherited PYTHONPATH, PYTHONHOME or PYTEST_* refuses as wrong-job-state; with 6d32414 (stage 2: the record precedes every collection_modifyitems). Closed at round 4.", "$PY -m pytest tests/test_0007_attestation_jobs.py::test_an_environment_that_shapes_pytest_refuses_the_job_before_anything_runs'[PYTEST_ADDOPTS--o python_functions=test_first]' tests/test_0007_attestation_jobs.py::test_an_environment_that_shapes_pytest_refuses_the_job_before_anything_runs'[PYTHONPATH-/elsewhere]' tests/test_0007_attestation_jobs.py::test_the_junit_must_equal_the_invocations_own_collection_as_a_multiset'[missing]' tests/test_0007_attestation_jobs.py::test_the_real_suite_process_is_bound_by_its_collection_and_its_exit_status'[deselect]' -q -p no:randomly"),
    ('0007', 'external', 17, 'SA-R3-03', "a failed pytest process could still produce successful attestation evidence: decide discarded run_suite's exit status (blocking; I5, INV-SA6)", "95c207c (0007 v23 §4d): decide consumes pytest's exit status beside the JUnit; 1 with no failing case is failed-tests, 0 beside a failing case and every other status suite-mismatch; _head() reads git's exit code. Its boundary carried into SA-R4-01 at round 4, closed at round 5.", "$PY -m pytest tests/test_0007_attestation_jobs.py::test_pytests_exit_status_must_agree_with_its_junit'[1-False-failed-tests-session-level failure]' tests/test_0007_attestation_jobs.py::test_the_real_suite_process_is_bound_by_its_collection_and_its_exit_status'[session-finish-raise]' -q -p no:randomly"),
    ('0007', 'external', 17, 'SA-R3-04', 'fresh bootstrap replacement bypassed the future-revision guard: a fresh write cleared records without the ordinary checks (blocking; I4, S75)', "95c207c (0007 v23 §4d): a fresh write runs every ordinary check against the ORIGINAL artifact first, refusing a future or malformed record of any key with the bytes unchanged, then a dry-run merge applies S75, v19's order and the poison check. Its boundary carried into SA-R4-02 at round 4, closed at round 5.", "$PY -m pytest tests/test_0007_attestation_writer.py::test_real_a_fresh_write_erases_no_future_or_malformed_record_of_any_key'[same-key-future]' tests/test_0007_attestation_writer.py::test_real_a_fresh_write_keeps_v19s_order -q -p no:randomly"),
    ('0007', 'external', 17, 'SA-R3-C1', "the synthetic attestation-job tests depended on the reviewer's UID: on a root host every synthetic case read as wrong-job-state (18 failures)", '95c207c: the synthetic job.decide cases pass euid=1000 explicitly; the root-job cell keeps euid=0; round 4: "Closed". The cell simulates the reviewer\'s root host (os.geteuid patched to 0).', '$PY -m pytest tests/test_0007_attestation_jobs.py::test_r3_c1_a_synthetic_case_reaches_its_outcome_on_a_root_host -q -p no:randomly'),
    ('0007', 'external', 18, 'SA-R4-01', 'the bootstrap exception also admitted a later session-finish failure: the exempt A10 failure explained exit 1 whether or not pytest.main returned (blocking; I5, INV-SA6; incomplete SA-R3-03 closure)', 'c0a1ace (0007 v23.2 §4d): the child writes a completion record after pytest.main returns, outside pytest\'s hooks; the parent checks its exact fields, `returned: true`, this run\'s nonce and an int exit status equal to the process\'s, before either record-producing outcome; round 5: "closed".', "$PY -m pytest tests/test_0007_attestation_jobs.py::test_r4_01_the_completion_record_must_be_this_runs_and_agree'[absent]' tests/test_0007_attestation_jobs.py::test_r4_01_the_completion_record_must_be_this_runs_and_agree'[stale]' tests/test_0007_attestation_jobs.py::test_r4_01_the_completion_record_must_be_this_runs_and_agree'[status]' tests/test_0007_attestation_jobs.py::test_r4_01_the_reviewers_five_rows'[bootstrap+session-raise]' -q -p no:randomly"),
    ('0007', 'external', 18, 'SA-R4-02', 'fresh replacement could erase a malformed current record of the incoming key: the same-key record was replaced before the production validator ran (blocking; I4, INV-SA6; incomplete SA-R3-04 closure)', 'c0a1ace (0007 v23.2 §4d): fresh replacement runs the production artifact validator on the ORIGINAL record list, per record and for same-key duplicates, before the dry run; round 5: "closed".', "$PY -m pytest tests/test_0007_attestation_writer.py::test_r4_02_a_conflicting_duplicate_in_the_original_refuses_a_fresh_write tests/test_0007_attestation_writer.py::test_r4_02_the_reviewers_rows_in_both_modes'[same-key-bad-digest-fresh]' tests/test_0007_attestation_writer.py::test_r4_02_the_reviewers_rows_in_both_modes'[same-key-extra-field-fresh]' tests/test_0007_attestation_writer.py::test_r4_02_the_reviewers_rows_in_both_modes'[same-key-false-probe-fresh]' tests/test_0007_attestation_writer.py::test_r4_02_the_reviewers_rows_in_both_modes'[same-key-missing-confinement-fresh]' -q -p no:randomly"),
    ('0007', 'external', 19, 'SA-R5-C1', 'the JUnit read boundary did not catch an unsupported XML encoding: CHILD_READ_ERRORS lacked LookupError, so a declaration naming no text codec escaped decide (non-blocking follow-up)', 'b718f43, after acceptance: LookupError joins CHILD_READ_ERRORS, so both of the reviewer\'s forms are a named suite-mismatch with no record (Quentin: "start SA-R5-C1").', "$PY -m pytest tests/test_0007_attestation_jobs.py::test_r5_f3_an_unreadable_junit_is_suite_mismatch'[bytes-codec]' tests/test_0007_attestation_jobs.py::test_r5_f3_an_unreadable_junit_is_suite_mismatch'[unknown-encoding]' -q -p no:randomly"),
    # ---- 0048, external rounds 1-6: its implementation-acceptance fold (verdict banked at coordination 791e0e8). The R3 and R4 closures
    # are recorded as the verdict retains them, closed as of round 6, and were not re-verified at this pin beyond its full inventory.
    ("0048", "external", 1, '0048-R1-01',
     'High. Validating the product does not validate the factor: a factor above 1 could still raise a confidence below the bound.',
     "the factor and the floor are validated at `expire()`'s entry, before any write (19a95585, §4D).",
     "$PY -m pytest tests/test_0048_decay_bounds.py::test_decay_config_refusal_writes_nothing'[0.5--0.5]' tests/test_0048_decay_bounds.py::test_decay_config_refusal_writes_nothing'[0.5-2.0]' tests/test_0048_decay_bounds.py::test_factor_is_validated_whatever_the_confidence'[2.0-0.0]' tests/test_0048_decay_bounds.py::test_factor_is_validated_whatever_the_confidence'[2.0-0.3]' -q -p no:randomly"),
    ("0048", "external", 1, '0048-R1-02',
     'High. A valid concurrent decay could overwrite a lower committed confidence: the decision came from the listing, not the row.',
     "expiry is decided from the current row, inside the store's transition (19a95585, §4B).",
     "$PY -m pytest tests/test_0048_decay_bounds.py::test_expiry_is_decided_from_the_current_row'[confirm]' tests/test_0048_decay_bounds.py::test_expiry_is_decided_from_the_current_row'[decay]' tests/test_0048_decay_bounds.py::test_expiry_is_decided_from_the_current_row'[lapse]' -q -p no:randomly"),
    ("0048", "external", 1, '0048-R1-03',
     'Medium. The refusal guarantee and the partial-failure contract disagreed.',
     'validation runs before the first write of the run, and a refusal is not swallowed (19a95585).',
     "$PY -m pytest tests/test_0048_decay_bounds.py::test_an_unrelated_write_refusal_inside_the_transition_still_raises tests/test_0048_decay_bounds.py::test_decay_config_refusal_writes_nothing'[0.5-2.0]' tests/test_0048_decay_bounds.py::test_decay_config_refusal_writes_nothing'[2.0-0.3]' -q -p no:randomly"),
    ("0048", "external", 2, '0048-R2-01',
     "Medium. The supplied model's writer gate silently accepted two unrecognized execution forms, `executemany` and an alias of `execute`.",
     "N4f fails closed on the connection's receiver, every reference a form it resolves, an execute-family attribute never held (8c71f85d). The table proves the alias half only. `executemany` is refused by more than one rule at once (`test_the_gate_refuses_each_unresolved_form[executemany]`): with it out of SQL_CALLS and the resolve-or-refuse rule off, the writer inventory and the outside-a-write-method rule still refuse the form, so removing any one survives.",
     '$PY -m pytest tests/test_0048_decay_bounds.py::test_the_gate_refuses_each_round_5_form_for_its_reason"[(b) the reviewer\'s alias of execute, with constructed SQL]" -q -p no:randomly'),
    ("0048", "external", 2, '0048-R2-02',
     'Preserve the existing decay result semantics when replacing the model.',
     'a retained decay is not counted as decayed, and below the floor the row retires without storing the decayed value (19a95585, N4i).',
     "$PY -m pytest tests/test_0048_decay_bounds.py::test_decay_keeps_the_shipped_result'[below the floor]' tests/test_0048_decay_bounds.py::test_decay_keeps_the_shipped_result'[exactly at the floor]' tests/test_0048_decay_bounds.py::test_decay_keeps_the_shipped_result'[factor 0, floor 0.3]' tests/test_0048_decay_bounds.py::test_decay_keeps_the_shipped_result'[retained]' -q -p no:randomly"),
    ("0048", "external", 3, '0048-R3-01',
     'Validate the same serialized bytes that the store binds.',
     'one capture is validated and bound: the helper returns the bytes it checked (1860fec0). Retained at round 6.',
     '$PY -m pytest tests/test_0048_decay_bounds.py::test_the_store_binds_the_bytes_it_validated -q -p no:randomly'),
    ("0048", "external", 3, '0048-R3-02',
     'N4f still accepted an existing writer that discarded the validated bytes.',
     'every edge json write goes through the one write method (1860fec0). Retained at round 6.',
     '$PY -m pytest tests/test_0048_decay_bounds.py::test_every_edge_write_goes_through_the_validating_serialiser -q -p no:randomly'),
    ("0048", "external", 3, '0048-R3-03',
     'Large integer bounds escaped the specified ValueError diagnostic.',
     'a bound is compared before float conversion, so an enormous integer names its field (1860fec0). Retained at round 6.',
     "$PY -m pytest tests/test_0048_decay_bounds.py::test_config_bounds_are_validated'[+10**400-decay_factor]' tests/test_0048_decay_bounds.py::test_config_bounds_are_validated'[-10**400-confidence_floor]' tests/test_0048_decay_bounds.py::test_config_bounds_hold_on_assignment'[+10**400-confidence_floor]' tests/test_0048_decay_bounds.py::test_decay_config_refusal_writes_nothing'[+10**400-0.3]' -q -p no:randomly"),
    ("0048", "external", 4, '0048-R4-01',
     'The closed grammar still admitted writes whose JSON source it had not resolved.',
     "the binding layout is frozen and enforced at the write method; every connection reference resolves; a failed preparation is unresolved; a non-literal entry binds what determines its value (0c7ad4aa). Retained at round 6: the verdict closes R4-01's four original witnesses at round 5.",
     '$PY -m pytest tests/test_0048_decay_bounds.py::test_every_edge_write_goes_through_the_validating_serialiser tests/test_0048_decay_bounds.py::test_the_layout_is_derived_by_execution_and_frozen_in_the_store tests/test_0048_decay_bounds.py::test_the_write_method_refuses_a_wrong_layout_before_any_sql -q -p no:randomly'),
    ("0048", "external", 4, '0048-R4-02',
     'The large-integer refusal could still lose its field diagnostic.',
     'the refused value is rendered through a bounded formatter, and the process-wide limit is never changed (0c7ad4aa). Retained at round 6.',
     "$PY -m pytest tests/test_0048_decay_bounds.py::test_a_refusal_beyond_the_rendering_limit_names_the_field_and_the_value'[-10**5000-confidence_floor]' tests/test_0048_decay_bounds.py::test_config_bounds_are_validated'[+10**5000-decay_factor]' tests/test_0048_decay_bounds.py::test_config_bounds_hold_on_assignment'[+10**5000-confidence_floor]' -q -p no:randomly"),
    ("0048", "external", 5, '0048-R5-01',
     'Medium. A receiver spelled `self` was exempted without resolving what it denotes.',
     'no receiver is read from its spelling; the one colliding method renamed, so no exemption remains (ed4d98c9). Closed at round 6.',
     "$PY -m pytest tests/test_0048_decay_bounds.py::test_each_receiver_form_has_its_stated_static_and_runtime_outcome'[P12 method-shaped, no such member]' tests/test_0048_decay_bounds.py::test_each_receiver_form_has_its_stated_static_and_runtime_outcome'[P13 method-shaped, its own _rows member]' -q -p no:randomly"),
    ("0048", "external", 5, '0048-R5-02',
     'Low. The prepare-only classifier could execute a statement on the qualified runtime.',
     'the classifier compiles `EXPLAIN QUERY PLAN <statement>`, so the statement itself never runs (ed4d98c9). Closed at round 6.',
     "$PY -m pytest tests/test_0048_decay_bounds.py::test_a_statement_that_binds_exactly_is_compiled_and_not_run tests/test_0048_decay_bounds.py::test_a_string_sqlite_refuses_bare_stays_unresolved'[QUERY PLAN SELECT 1]' -q -p no:randomly"),
    ("0048", "external", 1, '0048-R1-04',
     "Medium. The bounded-write claim exceeded C's edge-only boundary: the source holds five confidence-writing copy sites, not four.",
     'the guarantee is limited to edges, the inventory corrected to five, and the rest named as out of scope (1e80d4c7, text only).',
     '$PY -m pytest tests/test_0048_decay_bounds.py::test_declared_bounds_hold_on_every_write_path -q -p no:randomly'),
    ("0048", "external", 1, '0048-R1-05',
     'Low. A baseline control fixture used the local date against a UTC predicate, so it failed in a timezone ahead of UTC.',
     'the fixture dates its episode by the UTC calendar (6c0eab6d, a test fixture, no product change).',
     '$PY -m pytest tests/test_0041_round10_readers.py::test_E_proactive_control_all_four_sections_surface_their_records -q -p no:randomly'),
]


# The ARTIFACT each joint-arc finding targeted (research's ruling, 2026-09-04:
# one ledger housed in 0030, "each finding row naming which artifact it
# targeted"). Keyed by finding id rather than widening the 7-tuple, because
# three gates unpack the tuple positionally; `test_0030_closure_ledger.py`
# asserts this table is TOTAL over the 0030 rows and nothing else.
#   0029  — the transaction-time carrier spec
#   0030  — this spec
#   seam  — the joint seam model / binding census (specs/evidence/0029-0030/)
#   both  — a finding raised against the PAIR (one row, two folds)
#   shipped — a fix to shipped code or 0022 evidence surfaced by the seam
#             (revocation_sweep.py, reference_revocation.py, vectors.json)
TARGET_VALUES = ("0029", "0030", "seam", "both", "shipped")
TARGETS = {
    '0030-R1-1': 'both',
    '0030-R1-2': 'both',
    '0030-R1-3': '0029',
    '0030-R1-4': '0029',
    '0030-R1-5': '0029',
    '0030-R1-6': '0030',
    '0030-R1-7': '0030',
    '0030-R1-8': '0030',
    '0030-R2-1': '0029',
    '0030-R2-2': '0030',
    '0030-R2-3': '0030',
    '0030-R2-4': '0030',
    '0030-R2-5': 'both',
    '0030-R2-6': '0029',
    '0030-R2-7': '0030',
    '0030-R2-8': 'both',
    '0030-R3-1': '0030',
    '0030-R3-2': 'seam',
    '0030-R3-3': '0030',
    '0030-R3-4': '0029',
    '0030-R3-5': '0030',
    '0030-R3-6': '0030',
    '0030-R4-1': 'seam',
    '0030-R4-2': 'seam',
    '0030-R4-3': '0030',
    '0030-R4-4': 'seam',
    '0030-R5-1': '0030',
    '0030-R5-2': 'seam',
    '0030-R5-3': 'seam',
    '0030-R5-4': 'both',
    '0030-R6-1': 'seam',
    '0030-R6-2': 'seam',
    '0030-R6-3': 'seam',
    '0030-R6-4': 'both',
    '0030-R7-1': 'seam',
    '0030-R7-2': 'seam',
    '0030-R7-3': '0030',
    '0030-R7-4': 'seam',
    '0030-R8-1': '0030',
    '0030-R8-2': 'seam',
    '0030-R8-3': '0030',
    '0030-R8-4': 'seam',
    '0030-R9-1': 'shipped',
    '0030-R9-2': 'seam',
    '0030-R9-3': 'seam',
    '0030-R10-1': 'shipped',
    '0030-R10-2': 'shipped',
    '0030-R10-3': 'seam',
    '0030-R10-4': '0030',
    '0030-R11-1': 'shipped',
    '0030-R11-2': 'seam',
    '0030-R12-1': 'seam',
    '0030-R13-1': 'seam',
    '0030-R14-1': 'seam',
    '0030-R15-1': 'seam',
    '0030-R16-1': 'seam',
    '0030-R17-1': 'seam',
}
