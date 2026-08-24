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
     "grep -c 'assert picked' specs/evidence/0001/candidate.patch  "
     "# ordered equality, all vectors"),
    ("0001", "external", 8, "0001-R8-2",
     "the downgrade test could not detect a version-check-after-parsing "
     "regression (its enum still knew ASSISTANT)",
     "the parse sentinel: Edge/Episode.model_validate trapped; refusal must "
     "precede any record validation",
     "grep -n 'parse sentinel\\|parses == \\[\\]' "
     "specs/evidence/0001/candidate.patch"),
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
     "specs/evidence/0024/a1-reference.patch"),

    ("0024", "external", 13, "PACKAGE-R13-1",
     "package carriers described both specs as draft candidates while the "
     "canonical statuses are in-review/accepted; the 0025 r13 ledger row "
     "overstated 'no file edit, status untouched'",
     "candidate lines DERIVE the status word from each spec's Spec-Status "
     "line, fail-closed; the ledger row states no-design-change precisely",
     "grep -n '_spec_status' specs/package_identity.py  "
     "# the derived status, refusing an unreadable Spec-Status"),

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
     "grep -n 'relevant_ids' specs/evidence/0001/candidate.patch  "
     "# the bit carried from scoring into the reserve"),

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
     "grep -n 'reserved + \\[e for _, e in scored' "
     "specs/evidence/0001/candidate.patch  # the construction, in the patch"),

    ("0001", "external", 9, "0001-R9-2",
     "the candidate test module docstring still said candidate/0001-v8 — "
     "one version carrier survived the R8-3 sweep",
     "the module docstring is version-neutral; the sweep now greps the "
     "whole patch",
     "! grep -n '0001-v8' specs/evidence/0001/candidate.patch"),

    ("0001", "external", 9, "0001-R9-3",
     "the README's full-suite measurement was stale (16 failed/1797 vs the "
     "extracted branch's 16 failed/1787/21 skipped) and carried no "
     "environment",
     "the measurement is re-run at packaging time and recorded with its "
     "exact environment (python, platform, command)",
     "grep -n 'measured 2026-08-23' specs/evidence/0001/candidate.patch  "
     "# the environment-stamped measurement block, in the shipped patch"),

    ("0001", "external", 8, "0001-R8-3",
     "the modified patch still identified as candidate/0001-v8 while the "
     "draft moved to v9",
     "version-neutral artifact (candidate.patch); the Version row is the "
     "one carrier",
     "! grep -rn 'candidate/0001-v8' specs/evidence/0001/candidate.patch "
     "|| ! ls specs/evidence/0001/candidate-v8.patch 2>/dev/null"),

    # ---- 0001 external round 7 (2026-08-23) — the round-7 fold, v9 --------
    ("0001", "external", 7, "0001-R7-1",
     "the candidate patch implemented and tested the WRONG I12 label; "
     "USER/SYSTEM inherited a label",
     "the §4b decision order verbatim; the complete matrix tested",
     "grep -n 'third-party-derived' specs/evidence/0001/candidate.patch "
     "&& grep -n 'test_i12_the_complete_label_matrix' "
     "specs/evidence/0001/candidate.patch"),
    ("0001", "external", 7, "0001-R7-2",
     "the five-manifestation tests were proxies: routes not shapes, "
     "v11-vs-v11, count-only inheritance, a hardcoded 5, a fabricated "
     "reader",
     "shapes from the authority's own object records; digest-level "
     "inheritance; the qualified head-10 reader",
     "grep -n 'test_i13b_stamp_only_across_every_accepted_v10_shape' "
     "specs/evidence/0001/candidate.patch && grep -n "
     "'test_i13c_v11_inherits_by_digest_not_count' "
     "specs/evidence/0001/candidate.patch"),
    ("0001", "external", 7, "0001-R7-3",
     "I7's test was a constant assertion; the spec-named downgrade test "
     "was absent",
     "test_downgrade_export_fails_cleanly, real, both import modes",
     "grep -n 'def test_downgrade_export_fails_cleanly' "
     "specs/evidence/0001/candidate.patch"),
    ("0001", "external", 7, "0001-R7-4",
     "the four I6 composition branches were never executed",
     "four vectors with exact-ID/order assertions, all green against the "
     "unchanged reserve implementation",
     "grep -c 'def test_i6_composition_' "
     "specs/evidence/0001/candidate.patch  # 4"),

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
     "grep -n 'coverage_share=0.25' specs/evidence/0001/candidate_harness.py"),
    ("0001", "external", 6, "0001-R6-5",
     "a live cross-ref said 'the confirm() row' — the sweep grepped rule "
     "phrases, not row names",
     "fixed; cross-references join the sweep list",
     "! grep -n 'see the .confirm(). row' "
     "specs/0001-generated-content-trust-class.md"),

    # ---- 0001 external round 5 (2026-08-23) — the round-5 fold, v7 --------
    ("0001", "external", 5, "0001-R5-1",
     "three confirm() carriers survived two claimed-complete sweeps — the "
     "scripted replacements silently no-opped on wrapped text",
     "all three replaced; folds refuse needle misses; zero survivors "
     "grep-verified",
     "! grep -n 'Only through .confirm()' "
     "specs/0001-generated-content-trust-class.md && "
     "! grep -n 'confirm()..-class' "
     "specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 5, "0001-R5-2",
     "I6's post-_cover reserve was impossible — truncation precedes it; "
     "assertable_selected 0 measured at the shipped coverage_share=0.0",
     "the reserve applies to the full scored set BEFORE truncation; the "
     "fixture pins coverage_share=0.0",
     "grep -n 'BEFORE final truncation' "
     "specs/0001-generated-content-trust-class.md && "
     "grep -n 'coverage_share=0.0' specs/evidence/0001/candidate_harness.py"),
    ("0001", "external", 5, "0001-R5-3",
     "I5 tested collapse_for_render, which neither partitions nor renders",
     "the harness drives gate.partition_parts and asserts grounded-only / "
     "unverified-only / origin marker / no leakage",
     "$PY specs/evidence/0001/candidate_harness.py  "
     "# vector_affirmation_makes_the_fact_assertable, the partition block"),
    ("0001", "external", 5, "0001-R5-4",
     "the v10->v11 contract was prose-only in the new-reader direction",
     "I13a-d name the executable checks",
     "grep -c 'I13[abcd]' specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 5, "0001-R5-5",
     "current-version carriers disagreed: Status row, the §9 label, the "
     "harness self-id",
     "swept; version carriers join the pre-send sweep",
     "$PY -c \"import re, pathlib; "
     "s = pathlib.Path('specs/0001-generated-content-trust-class.md')"
     ".read_text(); "
     "ver = re.search(r'[*][*]Version[*][*] . [*][*](v\\\\d+)[*][*]', s)"
     ".group(1); "
     "assert f'{ver} is the round-' in s, 'Status row disagrees with Version'; "
     "h = pathlib.Path('specs/evidence/0001/candidate_harness.py')"
     ".read_text(); "
     "assert not re.search(r'v\\\\d+ candidate harness', h), "
     "'harness carries a version literal'; "
     "print('version carriers consistent, no hand-bumped literals')\""),

    # ---- 0001 external round 4 (2026-08-23) — the round-4 fold, v6 --------
    ("0001", "external", 4, "0001-R4-1",
     "the confirm() correction was unswept across five more normative "
     "carriers — the third partial sweep this spec has recorded",
     "§3.1/§3.2/§4/§7/§9 swept with the three-way terminology",
     "! grep -n 'Promotion remains' "
     "specs/0001-generated-content-trust-class.md && "
     "grep -c 'AFFIRMATION\\|affirmation' "
     "specs/0001-generated-content-trust-class.md"),
    ("0001", "external", 4, "0001-R4-2",
     "same-value affirmation does not render-collapse: collapse groups per "
     "trust envelope, so the spec claimed a collapse 0012 forbids",
     "the separate-partitions truth stated; the harness measures the "
     "RENDERED result",
     "$PY specs/evidence/0001/candidate_harness.py  "
     "# vector_affirmation_makes_the_fact_assertable asserts "
     "collapse_for_render surfaced_count=2, both partitions"),
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
     "grep -n 'SCHEMA_V7 = SCHEMA_V6\\|StoreVersionError' "
     "specs/0001-generated-content-trust-class.md && "
     "$PY specs/evidence/0001/candidate_harness.py  "
     "# vector_old_reader_refuses_a_newer_store_at_open"),

    # ---- 0001 historical rounds (retrofitted at TRACKED-entry, 2026-08-23:
    # per-finding texts live in the spec's own §11/§12/§13 narrative) -------
    ("0001", "internal", 1, "0001-INT1",
     "research's v1->v2 amendment set, folded directly into the spec before "
     "the per-finding discipline existed",
     "§11 (changes in v2), the collective record",
     "grep -n '## 11. Changes in v2' "
     "specs/0001-generated-content-trust-class.md"),
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
     "$PY -c \"import sys; sys.path.insert(0,'src'); "
     "from veracium.graph import _origin_label, _ORIGIN_LABELS; "
     "from veracium.schema import EvidenceAuthor as A; "
     "assert all(a in _ORIGIN_LABELS for a in "
     "(A.USER, A.SYSTEM, A.THIRD_PARTY)); "
     "print('author-keyed, fail-safe wired')\""),

    # ---- 0001 external round 3 (2026-08-23) — the round-3 fold, v5 --------
    ("0001", "external", 3, "0001-R3-1",
     "confirm_edge (0008) refuses every non-assertable edge by contract, so "
     "the promotion v4 promised cannot exist; affirmation is NEW USER "
     "evidence — same value grounds via the user edge, differing value "
     "retires via the ladder",
     "§3.2 affirmation row, I5, §7, §8; both shapes measured",
     "$PY specs/evidence/0001/candidate_harness.py  "
     "# vector_confirm_edge_refuses_non_assertable + "
     "vector_affirmation_makes_the_fact_assertable"),
    ("0001", "external", 3, "0001-R3-2",
     "the on-disk guard was never activated: disk=10 reader=10 gives "
     "ValidationError mid-read, not a refusal — 0007 only refuses what a "
     "version bump tells it to",
     "§7 (SCHEMA 10->11 semantic bump), I13 refusal-at-open",
     "grep -n 'SCHEMA_VERSION. 10 . 11\\|I13' "
     "specs/0001-generated-content-trust-class.md && "
     "$PY specs/evidence/0001/candidate_harness.py  "
     "# vector_old_reader_refuses_a_newer_store_at_open"),
    ("0001", "external", 3, "0001-R3-3",
     "two matrix cells measured false (cross-class absorption stays "
     "blocked; 0012 persists restatements untouched) and the supersession "
     "rationale named the wrong mechanism",
     "§3.2 rewritten against the ladder/0012/0.4.1 as shipped; I3b, I10a",
     "$PY specs/evidence/0001/candidate_harness.py  "
     "# vector_cross_class_absorption_stays_blocked + "
     "vector_same_class_restatement_persists_untouched"),
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
]
