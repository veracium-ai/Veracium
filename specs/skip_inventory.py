"""The canonical environment-conditional skip inventory (0014 R13-3).

Round 13 found the COLLECTED.txt inventory hand-listed and INCOMPLETE — the
optional-MCP importorskip was missing, so the reviewer's suite delta could not
fully reconcile against names. The inventory is therefore now a committed
module with a mechanical completeness gate
(tests/test_spec_gate.py::test_conditional_skip_inventory_is_complete): every
skip/skipif/importorskip site in tests/ must match an entry here, and every
entry must match a live site — a new conditional skip breaks the gate until it
is inventoried, and a stale entry breaks it until removed.

Each entry: (file, kind, condition_token, condition_class, reason).
`condition_token` must appear verbatim within the skip site's source (the
matching window spans the call line plus the following four lines, covering
multi-line messages). `condition_class` is one of:
  git-checkout        — skips when the tree is not a git checkout (always
                        skipped in the measured line and in extracted runs)
  env-flag            — opt-in live tiers, skipped unless the flag is set
  optional-dependency — skips when an optional package is absent
  host-conditional    — depends on host state (files present, runtime
                        identity, euid); the usual source of reviewer deltas
  package-artifact    — runs only inside an extracted review package (R14-1)
COLLECTED.txt's inventory section is generated from this module — one source,
and BOUND at both ends (R14-1): packaging asserts the marked COLLECTED section
equals render() before sealing, and
tests/test_spec_gate.py::test_collected_inventory_matches_the_generator makes
the same assertion inside the extracted package, so a stale or hand-edited
shipped inventory fails in the reviewer's own run.
"""

INVENTORY = [
    ("tests/test_seam_model_0029_0030_store.py", "skip",
     "no control executions recorded",
     "selection-conditional", "the RUNTIME execution gate (0029/0030 round "
                              "14): compares the discovered control set "
                              "against the assert_control registry; skips "
                              "only when a -k selection ran NO "
                              "control-invoking test at all, so there is "
                              "nothing to compare — the full suite, both "
                              "drivers, and CI always record and always "
                              "enforce", "job:runs"),
    ("tests/test_0042_sites.py", "skip",
     "selection narrowed (a deselection in this module, or a node id on the command line)",
     "selection-conditional", "the runtime leg's EXECUTION-SIDE completeness guard "
                              "(0042 round 6, 2026-09-20): compares the declared ids "
                              "against the site_id of every parametrised node pytest "
                              "COLLECTED for this module — the side the 143-for-157 "
                              "collection shortfall was visible from; it skips only "
                              "under a narrowed selection detected by its EFFECT (a "
                              "node of the module deselected — conftest's "
                              "pytest_deselected hook — or a node id on the command "
                              "line), where the collection is "
                              "narrow by request — the full suite and CI always "
                              "collect the whole module and always enforce", "job:runs"),
    ("tests/test_seam_model_0029_0030.py", "skip",
     "0030 spec not reachable from this tree",
     "host-conditional", "the seam model's propagation check reads the 0030 "
                         "spec as its normative counterpart; it skips only if "
                         "the seam-model tests are transplanted without "
                         "specs/ — a full checkout AND the extracted review "
                         "package both carry the spec, so neither skips", "job:runs"),
    ("tests/test_0031_proposal_ddl.py", "skipif", "SyntaxError below",
     "host-conditional", "the TypeAlias-position battery (0031 pre-round-11 "
                         "red-team): its probe sources use the 3.12 `type` "
                         "statement, which older parsers refuse before the "
                         "census can see it — availability is a parser fact "
                         "(the 0029/0030 round-13 lesson). 1 test; the 3.12 "
                         "CI lane executes it, 3.10/3.11 skip with this "
                         "reason", "key"),
    ("tests/test_0042_scope_resolution.py", "skipif", "sys.version_info < (3, 11)",
     "host-conditional", "specs/0042 round 13: the scope resolver's PAIRING ORACLE judges "
                         "each read against the instruction POSITIONS CPython "
                         "records from 3.11; 3.10 records none, so the gate "
                         "cannot locate a read and must not pass there. 1 test; "
                         "the 3.11/3.12/3.13 CI lanes execute it, 3.10 skips "
                         "with this reason"),
    ("tests/test_0042_inv7.py", "skip", "__firstlineno__ is stored in a class's vars() from 3.13",
     "host-conditional", "specs/0042 round 21: the mutant that drops route B's class-location "
                         "exclusion can only differ where the field exists (3.13+). 1 test; "
                         "the 3.13 CI lane executes it, 3.10/3.11/3.12 skip with this reason; "
                         "the acceptance cells run on every version"),
    ("tests/test_0042_scope_resolution.py", "skip", "tokenize returns an f-string as ONE token",
     "host-conditional", "specs/0042 round 20: the second seat's ROUTE 2 over the stdlib "
                         "counts a symbol whose name is never a NAME token as "
                         "compiler-introduced; before 3.12 tokenize returns an "
                         "f-string as one token, so names read inside one look "
                         "compiler-introduced (len, abs, repr — measured). 1 test; "
                         "the 3.12/3.13 CI lanes execute it, 3.10/3.11 skip with "
                         "this reason"),
    ("tests/test_0042_scope_resolution.py", "skip", "no comprehension is inlined before 3.12",
     "host-conditional", "specs/0042 round 20: a mutant of the compiler's implicit "
                         "__class__ (dropped, or added on a STORE of super) can "
                         "only change a signature where a comprehension is INLINED "
                         "(PEP 709, 3.12+). Those cells skip on 3.10/3.11 with this "
                         "reason and run on the 3.12/3.13 CI lanes; the mangling "
                         "cells run on every version"),
    ("tests/test_0015_lifecycle.py", "skip", "POSIX adapter test (specs/0015 I17)",
     "host-conditional", "the two 0015 lock-adapter tests run the POSIX kernel "
                         "contract via independent processes; they skip on "
                         "non-POSIX hosts (the Windows pair is a platform-gated "
                         "implementation obligation per 0015 R9-4/R10-3)"),
    ("tests/test_0015_lifecycle.py", "skip", "POSIX adapter test (specs/0015 I17)",
     "host-conditional", "the death-release half of the same POSIX pair"),
    ("tests/test_mcp.py", "importorskip", "mcp",
     "optional-dependency", "the optional MCP SDK — the importorskip is INSIDE "
                            "test_mcp_server_wiring ONLY (external 0018 B3-1: "
                            "the earlier ×5 claim mistook the file's test count "
                            "for the gate's scope); the file's other 4 tests "
                            "run without the SDK. Author line: all 5 PASS (mcp "
                            "importable in the authoring venv); an mcp-absent "
                            "environment sees 4 PASS + 1 SKIP"),
    ("tests/test_0031_phase_a.py", "importorskip", "mcp",
     "optional-dependency", "the optional MCP SDK — specs/0031 Phase A's "
                            "REFLECTED-surface tests (E2 host-only sweep, "
                            "V-NO-USER-ID-ARG, E3 inventory, A6/A7 precedence "
                            "and immutability through the built server, I3's "
                            "operator log) need the framework that reflects the "
                            "schemas; the importorskip is INSIDE those seven "
                            "tests only — the pipeline, counter, bridge and "
                            "invariant tests run without the SDK. Author line: "
                            "all PASS (mcp importable in the authoring venv); "
                            "an mcp-absent environment sees 7 SKIP"),
    ("tests/test_empty_grounded_header.py", "importorskip", "mcp",
     "optional-dependency", "the optional MCP SDK — the recall tool's served "
                            "description (the user's own words outrank a recalled "
                            "memory) is read from the built server; the importorskip "
                            "is INSIDE test_the_recall_tool_says_the_users_words_"
                            "outrank_a_memory ONLY — the file's other 3 tests run "
                            "without the SDK (found by the pydantic-floor CI lane at "
                            "c877648, run 40934117705). Author line: all 4 PASS; an "
                            "mcp-absent environment sees 3 PASS + 1 SKIP"),
    ("tests/test_0006_require_source_id.py", "importorskip", "mcp",
     "optional-dependency", "the optional MCP SDK — 0006 I15's served-tool "
                            "schema check (the built server exposes no "
                            "source_id argument, I1) needs the framework that "
                            "reflects the schemas; the importorskip is INSIDE "
                            "test_the_served_remember_tool_exposes_no_source_id "
                            "and (0006 v9) test_the_served_record_procedure_tool_"
                            "takes_the_deployment_binding_not_an_argument ONLY — "
                            "the file's other 5 tests run without the SDK (found "
                            "by the pydantic-floor CI lane at b3a405c, which "
                            "installs without the extra). Author line: all 7 "
                            "PASS; an mcp-absent environment sees 5 PASS + 2 SKIP", "job:runs"),
    # ---- FOUR ENTRIES MISSING SINCE 0021 SHIPPED (external round 3, R3-5).
    # These skip UNCONDITIONALLY on every host and were in no category, so the
    # generated inventory decomposed a measured line it could not account for
    # and `verify_collected` passed anyway — it checks the block EQUALS the
    # generator's output, which is true of an incomplete generator. The
    # reviewer's extracted run surfaced them with `-rs`; ours never printed
    # skip reasons at all. The reconciler added alongside this list is the
    # real fix; these entries are what it needs to reconcile against.
    ("tests/test_0021_maintain_scope.py", "skip",
     "W6 is the LIVE",
     "future-obligation",
     "1 test. UNCONDITIONAL on every host: it needs a real model and the "
     "benchmark harness, and a simulated leak probe measures the simulation. "
     "0021 W6 names it as research's D-extension obligation"),
    ("tests/test_0021_maintain_scope.py", "skip",
     "W16's reparenting half",
     "future-obligation",
     "1 test. UNCONDITIONAL: 0021 §7a names the primitive FUTURE and §2c-ii "
     "asserts executably that it has no shipped writer; the born-closed half "
     "IS covered by test_transitive_absorption_chains"),
    ("tests/test_0021_maintain_scope.py", "skip",
     "W17 is the shipped evidence program",
     "future-obligation",
     "1 test. UNCONDITIONAL: the check lives in "
     "specs/evidence/0020/ledger_plan_harness.py, which extracts the REAL "
     "contribution_ledger DDL from a live store; a pytest copy would be a "
     "weaker second implementation"),
    ("tests/test_0021_maintain_scope.py", "skip",
     "W18's after-a-prune half",
     "future-obligation",
     "1 test. UNCONDITIONAL, same FUTURE primitive as W16; the before half is "
     "test_native_chain_export_carries_absorbed_by_id_on_both_absorbed"),
    ("tests/test_spec_gate.py", "skip", "nested evidence run",
     "recursion-bound",
     "1 test. The closure-evidence runner executes commands that legitimately "
     "invoke `pytest tests/test_spec_gate.py`, which would re-enter the runner "
     "and nest until the timeout — measured at 10m44s and a self-inflicted "
     "failure before the bound existed. Children are marked with "
     "VERACIUM_EVIDENCE_CHILD and skip; the parent still runs every command "
     "exactly once. SKIPS ONLY inside a nested run, never at the top level"),
    ("tests/test_spec_gate.py", "skip", "COLLECTED.txt not present",
     "package-artifact",
     "binds COLLECTED's inventory to render(); 1 test. **It SKIPS in the "
     "sealed measured line** — sealing measures the committed tree BEFORE "
     "building COLLECTED, so the file it binds does not exist yet — and it "
     "EXECUTES in your extraction, which carries COLLECTED. Both statuses "
     "reconcile; your report should say which. "
     "(External round 8's R8-2 named four hand-maintained claims that had gone "
     "false; this entry was a FIFTH, still asserting the withdrawn "
     "measured-with-the-file-present story. It contradicted the sealed -rs "
     "output shipped beside it, which records this very skip. Caught by "
     "grepping the BUILT artifact rather than trusting that four carriers were "
     "all of them. NOTE: this note deliberately does NOT quote the withdrawn "
     "phrase — explanatory prose that quotes the string a mechanical check "
     "searches for defeats the check, which is its own recurring defect in "
     "this review.)"),
    ("tests/test_eval.py", "skipif", "VERACIUM_EVAL",
     "env-flag", "live acceptance-eval tier"),
    # (specs/0016 D2 removed the VERACIUM_MIN_DEP_JOB floor regression with the D1 warning surface it exercised;
    # restored at the Python 3.14 floor, 2026-09-27, as a version assertion read from pyproject.toml)
    ("tests/test_dependency_floor.py", "skipif", "VERACIUM_MIN_DEP_JOB",
     "env-flag", "runs in CI's minimum-dependency job only: asserts the installed pydantic IS the declared floor"),
    ("tests/test_robustness.py", "skipif", "VERACIUM_ROBUSTNESS",
     "env-flag", "live robustness tier"),
    # (0037 v24.5, the round-9 reviewer's F2: the omitted-date default. The
    # regression runs under a zone fourteen hours ahead of UTC and one twelve
    # behind; at any hour at least one of the two carries the local/UTC date
    # boundary, and the OTHER skips with this token when its local date
    # happens to equal the UTC date. Two tests × two zones: at most one zone
    # per test skips at any hour, never both zones of a test.)
    ("tests/test_omitted_date_defaults_to_utc.py", "skip", "local date equals the UTC date",
     "host-conditional", "the local/UTC date-boundary regression — the zone that "
                         "does not carry the boundary at this hour skips; the other "
                         "runs (at most 1 of each test's 2 zones; 2 tests, so at "
                         "most 2 skips, never a whole test)"),
    ("tests/test_spec_gate.py", "skip", "COORDINATION.md not present",
     "host-conditional", "reads a HOME-anchored local-only coordination file — "
                         "1 test, PASS in the measured line (the file exists "
                         "on the authoring HOST, outside the tree); SKIP on "
                         "any other host"),
    ("tests/test_spec_gate.py", "skip", "not a git checkout",
     "git-checkout", "STATUS.md `updated` derives from git log"),
    ("tests/test_spec_gate.py", "skip", "no archives present",
     "git-checkout", "archives are gitignored; a clone has none"),
    ("tests/test_0039_answer_shapes.py", "skip",
     "not enough history to check the transcript's pin",
     "git-checkout", "specs/0039: a SHALLOW checkout cannot answer whether the "
     "transcript's pin is an ancestor of HEAD — git's exit 128 there is a fact "
     "about the checkout, not a transcript finding; CI's pytest jobs check out "
     "with fetch-depth 0, so this skip is a last resort there"),
    ("tests/test_0039_answer_shapes.py", "skip",
     "the transcript's pin cannot be checked against history",
     "git-checkout", "specs/0039: each answer-shape transcript's header pins the "
     "commit its outcomes describe; the binding needs git history (ancestor + "
     "src/ unchanged since the pin) and cannot run in an extracted archive"),
    ("tests/test_0042_inv7.py", "skip",
     "the transcript's pin cannot be checked against history",
     "git-checkout", "specs/0042 INV-7: the four-arm transcript's header pins the "
     "commit it ran against; the binding needs git history (ancestor + src/ "
     "unchanged since the pin) and cannot run in an extracted archive"),
    ("tests/test_0042_inv7.py", "skip",
     "the pin's ancestry cannot be checked",
     "git-checkout", "specs/0042 INV-7: a SHALLOW checkout cannot answer whether the "
     "transcript's pin is an ancestor of HEAD (git exit 128 is a fact about the "
     "checkout); CI checks out with fetch-depth 0, so this is a last resort"),
    ("tests/test_0042_inv7.py", "skip",
     "the pin's harness cannot be loaded to compare against",
     "git-checkout", "specs/0042 INV-7 (round 9, F2): the equivalence proof loads the "
     "harness AS IT STOOD at the transcript's pin and runs it beside the current one, to "
     "show the control-summary fix changes nothing for a COMPLETE capture; an extracted "
     "archive has no history to load the old harness from, and comparing against a "
     "rebuilt-from-memory copy would assert a property of the reconstruction"),
    ("tests/test_0042_inv7.py", "skip",
     "is not retrievable here",
     "git-checkout", "specs/0042 INV-7 (round 9, F2): the pin is a commit here but the "
     "harness blob at it is not fetchable (a shallow or partial clone), which is a fact "
     "about the checkout and not about the harness"),
    ("tests/test_closure_mutants.py", "skip",
     "rows are subject by date, and telling a code fix needs the git history of their fix commits",
     "git-checkout", "the owner's closure-mutant rule (2026-10-10, \"Code fixes only\"): a row is subject when its FIX "
     "commits touch code, which only git history can say; a git-less copy (an sdist, the reviewer's tree/) cannot "
     "classify — CI is a checkout, where it always runs. It skips only when a row is subject by date."),
    ("tests/test_closure_mutants.py", "skip",
     "telling a code fix needs the git history of the fix commits",
     "git-checkout", "the closure-mutant rule's real-data control classifies 0043's rows by their fix commits, which "
     "needs git history; a git-less copy has none"),
    ("tests/test_0043_mutation_campaign.py", "skipif", "not _is_checkout()",
     "git-checkout", "specs/0043 round-9 follow-up: the one-row reproduction snapshots the TRACKED tree "
     "(git ls-files); a git-less copy (an sdist, the reviewer's tree/) has none, so the row cannot be "
     "re-run there — CI is a checkout, where it always runs"),
    ("tests/test_0013_pa1_campaign.py", "skipif", "not _is_checkout()",
     "git-checkout", "specs/0013 v33 0013-PA1 (the migration postconditions' mutation table): the first code mutant's "
     "reproduction snapshots the TRACKED tree (git ls-files); a git-less copy (an sdist, a reviewer's tree/) has none, "
     "so the row cannot be re-run there — CI is a checkout, where it always runs", "job:runs"),
    ("tests/test_0013_pa1_retired_keys.py", "skip",
     "no repository here (a packaged tree)",
     "git-checkout", "specs/0013 v33 §4f / M-Q6 (ruled by 0016 D2): RETIRED_EPISODE_KEYS is bound to a derivation over "
     "every release tag's schema.py, which needs the repository's tags; with no .git it skips, while a .git without "
     "tags FAILS (a tagless clone would read as nothing retired) — CI checks out with fetch-depth 0", "job:runs"),
    ("tests/test_0041_mutation_campaign.py", "skipif", "not _is_checkout()",
     "git-checkout", "specs/0041 0041-PA1 (the notice-binding hotfix's mutation table): the one-row reproduction "
     "snapshots the TRACKED tree (git ls-files); a git-less copy (an sdist, a reviewer's tree/) has none, so the row "
     "cannot be re-run there — CI is a checkout, where it always runs"),
    ("tests/test_0043_run.py", "skip",
     "the run's pin cannot be checked against history",
     "git-checkout", "specs/0043 tranche 2: the committed run report pins the commit it "
     "ran against; the binding needs git history and cannot run where there is no "
     "repository (an sdist) — named by git's own 'not a git repository'; any OTHER git "
     "failure is an error, never a skip (the vacuous-branch defect closed 2026-09-19)"),
    ("tests/test_0043_run.py", "skip",
     "not enough history to check the run's pin",
     "git-checkout", "specs/0043 tranche 2: a SHALLOW checkout cannot answer whether the "
     "run's pin is an ancestor of HEAD; CI checks out with fetch-depth 0, so this is a "
     "last resort there"),
    ("tests/test_spec_gate.py", "skip",
     "the retrospective obligation set derives from git history",
     "git-checkout", "0039 round-1 package finding: the security-hotfix "
     "retrospective deadline gate derives its obligations from `git log "
     "--all`; a `git archive` tree has no history, so the live node skips "
     "there (the throwaway battery still runs)"),
    ("tests/test_spec_gate.py", "skip",
     "the bare invocation derives the obligation set from git history",
     "git-checkout", "v0.22.0 cut, 2026-09-12: the offline launcher went red on the "
     "retrospective ROOT test (added with the ocr medium fixes), whose bare "
     "invocation of the gate derives obligations from `git log`; a `git archive` "
     "tree has none, so the node skips visibly after the one assertion that "
     "needs no git (the root is the file's) — the same class as the entry above"),
    ("tests/test_spec_gate.py", "skip",
     "the newest archive predates the identity record's domain",
     "package-artifact",
     "1 test. External round 20 asked for a FULL-REPACK regression, so the "
     "R20-1 test mutates the most recent SEALED archive and requires "
     "verify_archive to refuse. It needs an archive the identity record "
     "governs (v17 onward); on a tree whose newest archive predates that "
     "domain there is nothing to repack, and the pure-function matrix in "
     "test_the_package_identity_record_governs_every_candidate_carrier covers "
     "the same mutations without an artifact"),
    ("tests/longmemeval/test_run_wiring.py", "skipif", "not a git checkout",
     "git-checkout", "a run's manifest resolves git state by design"),
    ("tests/longmemeval/test_manifest.py", "skip", "not a git checkout",
     "git-checkout", "git_state() resolves rather than remembers"),
    ("tests/test_migrations_0013.py", "skip", "cannot hold a non-UTF-8 file name",
     "host-conditional", "macOS's APFS refuses a non-UTF-8 file name (EILSEQ), so the non-UTF-8 path cell has no file "
                         "to open there (0007 CI run 1, 2026-10-27); a function of the build's system", "key"),
    ("tests/test_migrations_0013.py", "skipif", "geteuid",
     "host-conditional", "root euid defeats the read-only-store fixture", "job:runs"),
    ("tests/test_schema_model.py", "skip", "no git checkout",
     "git-checkout", "check() returns 2 before reaching the assertion", "job:runs"),
    ("tests/test_0007_attestation_writer.py", "skip", "no git checkout",
     "git-checkout", "check() returns 2 before reaching the stale-record report (S77)", "job:runs"),
    ("tests/test_0044_t12_fixes.py", "skip", "no git checkout",
     "git-checkout", "the keep-every-value sweep reads the tracked tree (git ls-files)", "job:runs"),
    ("tests/test_printed_verification_instructions.py", "skip",
     "the tracked-file enumeration cannot run",
     "git-checkout", "the printed-instruction gate asserts that no TERMINAL RECORD "
     "carrier lives outside its subject set by enumerating the TRACKED Markdown "
     "files; a git archive has no index to enumerate, so the complement assertion "
     "is a named not-run there (the records inside the set are still executed)"),
    # R-I/R-II round 2, V1: the mechanism cells (tests/test_0044_v1_readonly_db.py)
    ("tests/test_0044_v1_readonly_db.py", "skip", "sqlite_errorname exists from Python 3.11",
     "host-conditional", "Python 3.10 has no sqlite_errorname: the message is asserted, the extended code is not", "key"),
    ("tests/test_0044_v1_readonly_db.py", "skipif", "geteuid",
     "host-conditional", "root euid writes a read-only file, so the shared-message limit cannot be shown", "job:runs"),
    ("tests/test_0044_v1_readonly_db.py", "skip", "no fcntl on this platform",
     "host-conditional", "without fcntl (Windows) no basetemp is held, and the lock cell claims nothing", "key"),
]


def render(rs_output: str = "") -> str:
    """The COLLECTED.txt inventory section, generated from INVENTORY.

    `rs_output` is the sealed `pytest -q -rs` text. Supplying it makes the
    reconciliation block OBSERVED rather than remembered (R4-4).
    """
    classes = {}
    for f, kind, token, cls, reason, *_ in INVENTORY:
        classes.setdefault(cls, []).append(f"{f} ({kind}: {reason})")
    # EXTERNAL ROUND 4, R4-4. This list was HARD-CODED and omitted
    # "future-obligation", so the four entries added at round 3 went into
    # INVENTORY and never reached the rendered block: the data was right, the
    # renderer could not see it, and `verify_collected` compared the block to
    # that same blind renderer. The order stays explicit for readability, but
    # any category present in INVENTORY and missing from it now RAISES rather
    # than being silently dropped — the renderer's domain is INVENTORY's, not
    # a list someone remembered to extend.
    order = ["git-checkout", "env-flag", "optional-dependency", "package-artifact",
             "host-conditional", "future-obligation", "recursion-bound",
             "selection-conditional"]
    unordered = sorted(set(classes) - set(order))
    if unordered:
        raise ValueError(
            f"INVENTORY carries categories this renderer would silently drop: "
            f"{unordered}. Add them to `order` and `blurb` — the failure this "
            f"guard exists for is external round 4's R4-4.")
    blurb = {
        # R8-2: this said the measured line SKIPPED them because the measuring
        # copy had no .git. The sealer measures ROOT, which IS a git checkout,
        # and the sealed reconciliation contains no git-dependent skips at all
        # — the blurb described a workflow that stopped being true.
        "git-checkout": ("git-checkout-dependent (these EXECUTE in the sealed "
                         "measured line, because sealing measures the git "
                         "checkout itself; they SKIP in your extracted run, "
                         "which has no .git — that difference is the largest "
                         "single source of the delta between the two numbers):"),
        "env-flag": "env-flag tiers (SKIPPED unless the flag is set; part of the measured line):",
        "optional-dependency": ("optional-dependency (per-entry counts and the measured "
                                "author status are in each entry):"),
        "package-artifact": ("package-artifact (status depends on whether COLLECTED.txt is "
                             "in the tree you run — see the entry):"),
        "host-conditional": ("host-conditional (may differ between the authoring host and "
                             "yours — the usual source of reviewer deltas; each entry "
                             "carries its count and measured author status):"),
        "recursion-bound": ("recursion-bound (SKIPS ONLY inside a NESTED run "
                            "and never at the top level — the closure-evidence "
                            "runner marks its children so they do not re-enter "
                            "it; at the top level this test EXECUTES):"),
        "selection-conditional": ("selection-conditional (SKIPS ONLY when a "
                                  "-k selection ran no test that could feed "
                                  "the check — the full suite, the prescribed "
                                  "offline surfaces, and CI always feed and "
                                  "always enforce; 0029/0030 round 14's "
                                  "runtime execution gate is the instance):"),
        "future-obligation": ("future-obligation (SKIPPED UNCONDITIONALLY on every host, "
                              "including yours and ours — each names a primitive or a "
                              "live-model probe a spec marks FUTURE. These four were "
                              "absent from this inventory until external round 4 because "
                              "the completeness gate's regex did not recognise "
                              "`pytest.mark.skip(`):"),
    }
    out = []
    for cls in order:
        if cls in classes:
            out.append("  " + blurb[cls])
            out += [f"    {line}" for line in classes[cls]]
    out.append(
        "  RECONCILIATION — DERIVED FROM THE MEASURED RUN, not hand-written\n"
        "  (external round 4, R4-4). The block that stood here until v5 was\n"
        "  prose: it decomposed a measured line as 'git-checkout 11 + env-flag 3\n"
        "  = 14' while the measured line said 6, cited a pydantic-floor\n"
        "  regression that no longer exists, and claimed 'the seal verifies this\n"
        "  decomposition' — which nothing did. An arithmetic claim maintained by\n"
        "  hand beside a number produced by a machine will drift, and did.\n"
        + _observed_block(rs_output))
    return "\n".join(out)


def _observed_block(rs_output) -> str:
    """The decomposition, computed from `pytest -q -rs` output.

    No argument means no measured run was supplied, and the block SAYS SO
    rather than reciting a remembered decomposition — the failure R4-4 found.
    """
    if not rs_output:
        return ("  NO MEASURED RUN WAS SUPPLIED to the renderer, so no\n"
                "  decomposition is claimed here. The seal supplies one; a\n"
                "  block without these numbers was not sealed.\n")
    import re as _re
    from collections import Counter
    cat_of = {}
    for f, _kind, token, cls, _reason, *_ in INVENTORY:
        cat_of.setdefault(f, []).append((token, cls))
    counts, unmatched, total = Counter(), [], 0
    for m in _re.finditer(r"^SKIPPED \[(\d+)\] ([^:]+):\d+: (.*)$", rs_output, _re.M):
        n, path, reason = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
        total += n
        hit = None
        for f, pairs in cat_of.items():
            tail = f.split("tests/")[-1]
            if path.endswith(tail):
                for token, cls in pairs:
                    if token.lower() in reason.lower():
                        hit = cls
                        break
            if hit:
                break
        if hit:
            counts[hit] += n
        else:
            unmatched.append(f"{path}: {reason[:60]}")
    lines = ["  OBSERVED in the sealed run, by category:"]
    for cls, n in sorted(counts.items()):
        lines.append(f"    {cls}: {n}")
    lines.append(f"    TOTAL: {total}")
    # The PASS count is deliberately NOT echoed here. It belongs in COLLECTED's
    # header, which is not byte-compared. Putting it in the generated block made
    # the block depend on the pass count, which depends on whether the block is
    # correct (the packaged-state test verifies it) — a fixed point that cannot
    # converge: build the block, the pass count changes, the block no longer
    # matches. Caught while sealing round 5, by running the suite twice and
    # diffing the two renderings. Only the SKIP arithmetic belongs to this
    # block, and it is stable across that feedback.
    summary = _re.search(r"(\d+) passed, (\d+) skipped", rs_output)
    if summary:
        lines.append(f"    summary line skips: {summary.group(2)}")
        if int(summary.group(2)) != total:
            lines.append("    *** MISMATCH: the -rs section and the summary "
                         "disagree ***")
    if unmatched:
        lines.append("    *** OBSERVED SKIPS MATCHING NO ENTRY ***")
        lines += [f"      {u}" for u in unmatched]
    lines.append("  Your environment will differ where the categories above say "
                 "it will;")
    lines.append("  reconcile() computes this same table from YOUR run.")
    return "\n".join(lines) + "\n"



if __name__ == "__main__":
    print(render())


BEGIN_MARKER = "<!-- GENERATED:skip-inventory -->"
END_MARKER = "<!-- /GENERATED:skip-inventory -->"


def verify_collected(text: str, rs_output: str = "") -> None:
    """Byte-exact carrier verification.

    `rs_output` MUST be the same sealed `pytest -rs` text the block was
    rendered with (external round 4, R4-4 made the decomposition observed
    rather than recited). Verifying with a different argument than the block
    was built with compares two different renderings and fails loudly, which
    is the correct direction: the alternative is a check that passes because
    both sides forgot the same thing.

    Original docstring follows.

    Byte-exact carrier verification (R15-1 — the first verifier split on the
    first marker pair and stripped boundary newlines, so a duplicated complete
    block and an extra blank line after the opening marker both passed).

    Rules, exactly as the reviewer required: markers count only as COMPLETE
    STANDALONE LINES; exactly one opening and one closing marker; the enclosed
    block is compared to render(rs_output) with NO normalization OF THE DECODED TEXT.
    Narrowed claim (0014 round-16 bin-(b) obligation): callers typically read
    the carrier via Path.read_text(), which normalizes CRLF — so the guarantee
    is TEXT-EXACT across line-ending conversion; the implementation may upgrade
    to raw-bytes verification per the acceptance ledger. Raises ValueError with
    a specific reason; returns None on success. Shared by the packaging step
    and tests/test_spec_gate.py — one verifier, no drift."""
    # EXTERNAL ROUND 16, R16-2. The rules below used to be implemented HERE,
    # and I later wrote a SECOND, weaker copy of them in review_lessons.py
    # (`split(BEGIN, 1)` — the first marker pair, no count), which the reviewer
    # defeated with an appended block claiming different numbers. The rule now
    # has one implementation and this function is one of its two callers;
    # `generated_block.BlockError` subclasses ValueError, so every existing
    # caller and adversarial test still sees exactly what it saw before.
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import generated_block as gb
    # COLLECTED carries a header above its block, so this one is NOT
    # anchored — stated explicitly, because R19-2 was a policy nobody had
    # to state and therefore nobody checked.
    gb.verify(text, BEGIN_MARKER, END_MARKER, render(rs_output),
              at_start=False)


# ---------------------------------------------------------------------------
# RECONCILIATION — external round 3, R3-5.
#
# `verify_collected` proves the shipped block EQUALS this generator's output.
# That is a real check and it is not the one that was needed: an INCOMPLETE
# generator satisfies it perfectly, which is exactly what happened — four
# unconditional skips were invisible to the completeness gate's regex, absent
# from this list, and `verify_collected` passed while COLLECTED's own
# decomposition could not account for its own measured line.
#
# So this reconciles against REALITY rather than against ourselves: it parses
# `pytest -q -rs` output and requires every OBSERVED skip reason to match an
# inventory entry, and the totals to agree. A skip nobody listed is a failure,
# not a rounding difference.
def reconcile(pytest_rs_output: str) -> list:
    """Return a list of problems; empty means the run reconciles.

    Feed it the FULL `pytest -q -rs` output. Two independent checks:
      1. every `SKIPPED [n] path:line: reason` line matches an entry (by file
         and by a token of the reason);
      2. the count of observed skips equals the summary line's skip count, so
         a truncated `-rs` section cannot pass by omission.
    """
    import re as _re
    problems = []
    observed = []
    for m in _re.finditer(r"^SKIPPED \[(\d+)\] ([^:]+):\d+: (.*)$",
                          pytest_rs_output, _re.M):
        n, path, reason = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
        observed.append((n, path, reason))
    for n, path, reason in observed:
        # the harness may report a path relative to a different root
        if entry_for(path, reason) is None:
            problems.append(f"OBSERVED SKIP NOT IN THE INVENTORY: {path}: {reason[:90]}")
    summary = _re.search(r"(\d+) passed, (\d+) skipped", pytest_rs_output)
    if summary:
        claimed = int(summary.group(2))
        total = sum(n for n, _, _ in observed)
        if total != claimed:
            problems.append(
                f"the -rs section lists {total} skips but the summary says "
                f"{claimed} — the report is truncated or the parse is wrong")
    elif observed:
        problems.append("no summary line found; cannot reconcile totals")
    return problems


# EXTERNAL ROUND 5, R5-4. An entry's `token` is a SOURCE-SITE token — it must
# appear near the `pytest.skip(...)` call so the completeness gate can find the
# site. pytest emits the RESOLVED reason, which is often different text: the
# euid entry's token is `geteuid` (what the source says) while pytest prints
# "root traverses any directory...". Matching emitted reasons against
# source tokens therefore reported a listed skip as unlisted on any root host —
# and only on a root host, which is why our own runs never saw it.
#
# The two vocabularies are now separate. EMITTED holds the reason text pytest
# prints, keyed by (file, source-token); reconcile matches against either.
EMITTED = {
    ("tests/test_migrations_0013.py", "geteuid"):
        ("root traverses any directory", "running as root"),
    # 0007 SQLite round 1, C2: R5-4 aliased ONE geteuid entry and not the
    # second, and the three checkout-only campaign rows never had one — a
    # git-less tree and a root host each reported a listed skip as unlisted.
    # emitted_reason_problems() below now renders every site's reason and
    # runs reconcile() on it, so a missing alias fails on any host.
    ("tests/test_0044_v1_readonly_db.py", "geteuid"):
        ("root writes a read-only file",),
    ("tests/test_0013_pa1_campaign.py", "not _is_checkout()"):
        ("a git-less copy has none",),
    ("tests/test_0041_mutation_campaign.py", "not _is_checkout()"):
        ("a git-less copy has none",),
    ("tests/test_0043_mutation_campaign.py", "not _is_checkout()"):
        ("a git-less copy has none",),
    ("tests/test_0042_scope_resolution.py", "sys.version_info < (3, 11)"):
        ("which 3.10 does not record",),
}


def _token_matches(reason: str, entry_file: str) -> bool:
    r = reason.lower()
    for f, _kind, token, _cat, _note, *_ in INVENTORY:
        if f != entry_file:
            continue
        if token.lower() in r:
            return True
        for emitted in EMITTED.get((f, token), ()):
            if emitted.lower() in r:
                return True
    return False


def _entry_matches(entry, path: str, reason: str) -> bool:
    f, token = entry[0], entry[2]
    tail = path.split("tests/")[-1]
    if not (f.endswith(tail) or tail.endswith(f.split("tests/")[-1])):
        return False
    r = reason.lower()
    return token.lower() in r or any(e.lower() in r for e in EMITTED.get((f, token), ()))


def entry_for(path: str, reason: str):
    """THE match of an observed skip to its inventory entry (0007 I5): by the file (a path relative to any root) and
    by the entry's source token or one of its EMITTED reasons. `reconcile` and the attestation job both ask this, so
    the rule lives once. None when no entry matches."""
    return next((e for e in INVENTORY if _entry_matches(e, path, reason)), None)


ATTESTATION_CLASSES = ("key", "job:runs", "rewrite")
"""0007 §4d's closed vocabulary for an entry whose file is in the attestation suite: `key` (a function of the
attestation key or the Python floor, identical across one key's jobs), `job:runs` (the attestation job fixes the
condition so the test RUNS; if it fires, the job is excluded), `rewrite` (presupposes the withdrawn single-record
rule). `rewrite` stays in the vocabulary for a future stranded skip, and the gate asserts no entry carries it."""


def attestation_class(entry):
    """The entry's sixth column: its attestation class, or None for an entry outside the suite."""
    return entry[5] if len(entry) > 5 else None


# 0007 SQLite round 1, C2 — the class, not the four. The completeness gate
# (test_conditional_skip_inventory_is_complete) matches SOURCE tokens, so it
# passed while reconcile(), which matches EMITTED reasons, refused five listed
# skips; each hand-added alias closed one host's instance. This renders the
# reason every skip site in tests/ would print and hands the lot to reconcile()
# itself — the consumer, not a second implementation of it.
_SITE_FUNCS = {"pytest.skip", "pytest.mark.skip", "pytest.mark.skipif", "pytest.importorskip"}


def _rendered(expr):
    """The text a reason expression prints, or None if it cannot be known
    statically. An f-string's fields become `X`, which can never complete a
    token, so a field cannot make a reason match."""
    import ast
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.JoinedStr):
        parts = []
        for v in expr.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            elif isinstance(v, ast.FormattedValue):
                parts.append("X")
            else:
                return None
        return "".join(parts)
    return None


def _emitted_reason(call):
    """What pytest prints for this site, or None (refused by the caller)."""
    import ast
    name = ast.unparse(call.func)
    kw = {k.arg: k.value for k in call.keywords}
    if "reason" in kw:
        return _rendered(kw["reason"])
    if name == "pytest.importorskip":
        if not (call.args and isinstance(call.args[0], ast.Constant)):
            return None
        mod = call.args[0].value
        return f"could not import {mod!r}: No module named {mod!r}"
    if name in ("pytest.skip", "pytest.mark.skip"):
        return _rendered(call.args[0]) if call.args else "unconditional skip"
    # skipif with no reason: pytest prints the condition's source
    return "condition: " + ast.unparse(call.args[0]) if call.args else None


def emitted_reason_problems(root) -> list:
    """Every skip site under `root`/tests, rendered as the `-rs` line pytest
    would print, must reconcile. Returns problems; empty means it does. A
    reason that cannot be rendered statically is itself a problem: a site this
    cannot read is not a site it has checked."""
    import ast
    import pathlib
    root = pathlib.Path(root)
    lines, problems = [], []
    for f in sorted((root / "tests").rglob("*.py")):
        rel = f.relative_to(root).as_posix()
        for node in ast.walk(ast.parse(f.read_text())):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("skip", "skipif", "importorskip")
                    and ast.unparse(node.func) in _SITE_FUNCS):
                continue
            reason = _emitted_reason(node)
            if reason is None:
                problems.append(f"{rel}:{node.lineno}: the emitted reason cannot be rendered statically "
                                f"({ast.unparse(node)[:80]})")
            else:
                lines.append(f"SKIPPED [1] {rel}:{node.lineno}: {' '.join(reason.split())}")
    n = len(lines)
    lines.append(f"0 passed, {n} skipped in 0.0s")
    return problems + reconcile("\n".join(lines))
