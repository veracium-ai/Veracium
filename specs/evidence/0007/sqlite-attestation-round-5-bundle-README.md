<!-- TERMINAL RECORD — the round-5 review bundle README of the SQLite attestation amendment (0013/0007-sqlite-attestation,
folded into 0007, 0013 and 0018), byte-copied UNMODIFIED from the ACCEPTED package (sha256 658b6c2dcc5152aa4b3661206085523070862f4fbe299c33fc8ead518b483a03
@ f5d1524fe43b48962ee7d6b8b3ceb39fa9e5c403, CI 41128447687) on 2026-11-01, at the acceptance fold of the reviewer's
2026-10-31 verdict accepting the implementation (round 2's frozen obligations I1–I7 satisfied). It is the one carrier
holding round 4's closure dispositions, the red/green record and the errors ledger together; the version cells carry
lineage, not the reviewer's dispositions. The package remains the archive; this copy is the record. THE BYTES AFTER
THE BLANK LINE FOLLOWING THIS COMMENT equal the packaged README:
sha256 7ad8e00992a0ed655472ded7fd95d182f6c289401edb4249a0947ecf4f21e753, 38936 bytes — verifiable forever against the archived package.
On the tarball: tar xzf <pkg> -O 0007-sqlite-attestation-round5-implementation-review-package/README-0007-sqlite-attestation-round5-bundle.md | sha256sum
Here: sed '1,/^-->$/d' <this file> | tail -n +2 | sha256sum   (the comment closes on its own line)
-->

# SQLite attestation — round 5: the closure of round 4's findings

**Canonical artifact:** this package, bound by `PIN.txt` (pin `f5d1524fe43b48962ee7d6b8b3ceb39fa9e5c403`, tree `24d2208e662312d605f6b7570215587cb09e299f`, CI run `41128447687`) and
`SHA256SUMS`. `tree/` is `git archive` of the pin, witnessed by `collected/tree_hash_witness.sh`.

## 1. What this round asks

Round 4 withheld implementation acceptance on two findings within round 2's frozen obligations, each an incomplete
round-3 closure: SA-R4-01 (I5, INV-SA6: the exact bootstrap failure masked an additional session-finish failure) and
SA-R4-02 (I4, INV-SA6: a fresh replacement erased a same-key current record the production validator rejects). It
closed SA-R3-01, SA-R3-02 and C1, and gave a finite closure checklist
(`prior-rounds/0007-sqlite-attestation-round4-implementation-obligations-verbatim.md`, "Finite closure checklist",
items 1–3). The round 2 design acceptance stands. This round asks whether each item of that checklist is met at the
pin. Nothing here asks for another design round.

**Scope.** The three amended specs ride at the package root, each `Spec-Status: accepted` and byte-identical to
`tree/specs/` at the pin: `0007-store-schema-versioning-SPEC-v23.2.1.md`, `0013-store-migrations-SPEC-v38.1.md`,
`0018-release-migration-orchestrator-SPEC-v8.md`. 0007 v23.2 states the two closures as rules and v23.2.1 adds their
mutants to INV-SA6's column (§5); 0013 and 0018 are unchanged since round 4. The commits since round 4's pin `d087f6e`
are in §7.

## 2. Round 4's checklist, item by item

`collected/obligation-map.md` maps each item to its code (`path:symbol`), its cells and the mutation-table rows that
demonstrate it, and keeps the I1–I7 map of rounds 3 and 4, every row of the three tables placed in it. Every citation
in it is checked against `tree/` by the stage. In summary:

| checklist item | at the pin |
|---|---|
| **1. SA-R4-01** the exact bootstrap failure plus an exception after the JUnit refuses, no record; the bootstrap-only control and the exit-status controls kept | the suite process now carries a POSITIVE completion signal written at the process boundary: the child (`specs/attestation_job.py:_CHILD`) runs `pytest.main` and writes a completion record only if `pytest.main` RETURNED, so a failure pytest does not catch (an exception escaping `pytest_sessionfinish` after the JUnit, a raising `pytest_unconfigure`, a process that exits from inside pytest) leaves none, whatever hook priority raised it. `specs/attestation_job.py:completion_problem` requires the record to exist, hold exactly `returned`, `exit_status` and `nonce`, carry THIS run's nonce (minted by `decide`, so another run's record cannot stand in) and the exit status the process exited with; it runs before every outcome that yields a record, so the exempt bootstrap failure explains exit 1 only if the process otherwise completed. Your five rows run through a REAL pytest process (`tests/test_0007_attestation_jobs.py::test_r4_01_the_reviewers_five_rows`): `bootstrap+session-raise` is `failed-tests` with no record; `bootstrap-alone` stays `bootstrap-pending`; the other three are unchanged. A sessionfinish hookwrapper would not do (a conftest's tryfirst wrapper runs outside a `-p` plugin's own), and is kept as a mutant |
| **2. SA-R4-02** malformed original evidence of the incoming key refused before a fresh replacement drops it, bytes unchanged; bootstrap, superseded, future-revision and ancestry controls kept | `specs/attestation_writer.py:write_records`: in fresh mode the PRODUCTION validator (`sv.attestation_record_problems`) runs over every ORIGINAL current record before the dry run and before anything is dropped, so a same-key current record with a bad digest, a missing confinement field, a false confinement probe or an extra field refuses with the bytes unchanged. Superseded records are outside "malformed" by design (S74: they attest nothing in either mode, and fresh mode drops them), stated with a control. Your rows run in both modes on a real two-commit repository (`tests/test_0007_attestation_writer.py::test_r4_02_the_reviewers_rows_in_both_modes`); the controls are `test_real_a_fresh_write_drops_bootstrap_records_and_refuses_a_non_bootstrap_one`, `test_r4_02_a_superseded_record_with_a_bad_digest_is_dropped_by_design`, `test_real_a_fresh_write_keeps_v19s_order` and the future-revision cases of `test_real_a_fresh_write_erases_no_future_or_malformed_record_of_any_key`. Your secondary observation, a conflicting duplicate in the original, now refuses a fresh write (`test_r4_02_a_conflicting_duplicate_in_the_original_refuses_a_fresh_write`) |
| **3.** the new checks red on round 4's pin and green after; the campaigns and clean controls kept; the full suite on this pin, environmental differences named | the round-4 cells, every parametrisation, run against round 4's implementation of the three files the fixes changed (put back from `d087f6e` into a git-archive export of this pin) and against this pin's, each node's role DECLARED by its cell and parameter id before the runs and its RED result required to match it, each node's kind named (`collected/red-then-green.txt`, made by `collected/rtg.py`): `RTG nodes=33 regression=16 (6 assertion, 5 error:AttributeError, 5 expected-refusal-missing) controls=17 green_here=33 roles_match=33 flip_control=refused ok=yes`. The five AttributeErrors are red by ABSENCE (the cell reaches a name round 4's code does not have), and are counted apart from the eleven red by the cell's own verdict. INV-SA10 65 of 65, A-matrix 22 of 22, INV-SA 44 of 44, each killed and good, each re-run IN FULL on a git-archive export of the pin, its rows equal to the committed table's (timing excluded; `collected/mutation-tables-rerun-at-pin.txt`); the job's and the writer's in-test matrices, 52 and 43 mutants (the aggregate's 13), every one killed with its controls green first and last; the 0044 consolidated campaign 546 of 546. The full suite: §8 |

The round-4 cells (every declared regression case red on round 4's implementation, every control, such as `[passing-control]` and the valid-bootstrap rows, green on both, and all green here; one regression row, `[other-key-bad-digest-fresh]`, is red by its reason only: round 4 refused it too, by another rule, and the cell requires the original-record validation's reason): `tests/test_0007_attestation_jobs.py::test_r4_01_the_reviewers_five_rows`,
`::test_r4_01_a_failure_pytest_does_not_catch_is_refused_whatever_its_priority`,
`::test_r4_01_the_completion_record_must_be_this_runs_and_agree`; `tests/test_0007_attestation_writer.py::test_r4_02_the_reviewers_rows_in_both_modes`,
`::test_r4_02_a_conflicting_duplicate_in_the_original_refuses_a_fresh_write`. The job's and the writer's in-test
mutation matrices gain a mutant per new check, the superseded implementation and the hookwrapper design included.

**What the second seat's two stage-2 passes found in the fix, and what this pin does about it** (each found before
this package, each closed here, each named in the map):
- **F1.** The completion child runs under `python -c`, which puts `''` at `sys.path[0]` where `python -m pytest` put
  the absolute cwd. The child's first two lines restore the absolute cwd only where `-c` left `''` (under safe-path the
  stdlib entry is kept); cells compare the prelude with a bare `-c` launch and run a chdir-then-lazy-import through a
  real pytest process.
- **F2.** Two completion-record guards (`returned is not True`; `exit_status` an int, since `True == 1`) had no killing
  cell; each now has one, and a matrix row.
- **F3, and its class.** The child's three outputs (the JUnit, the collection record, the completion record) were read
  without a closed refusal on malformed input: a truncated write, a directory or a FIFO at the path, invalid UTF-8,
  nesting deep enough to recurse, a classname naming no test module. Each is now a named refusal, so `decide` returns
  and `--out` is written. A collection record that is not a list of node ids refuses: a mapping of the right ids
  compared equal. The JUnit is refused when it is not a regular file, before it is opened (a FIFO there blocked the
  parse).
- **F4.** The outcomes that carry a record are ONE constant, `specs/attestation_aggregate.py:RECORD_OUTCOMES`, which
  the aggregator branches on; a cell drives `decide` to every outcome of its closed set and compares the outcomes
  returned with a record against it.
- **G2's own gap.** Each guard's refusal is told apart from the parse catch's by its reason, and a FIFO is released by
  a non-blocking writer poll that records whether `decide` ever opened it. That observation was shown failing by a
  scratch mutant that opens the path but keeps the guard's reason (research's and dev's runs agree); it is a
  demonstration outside the matrix, recipe in the map.

## 3. The real and constructed routes (I6, 0007 §6's Gate)

Unchanged since round 3. `specs/evidence/0007/routes/` holds four transcripts of `specs/evidence/0007/routes/route_probe.py`,
nothing patched:

| route | kind | status |
|---|---|---|
| the runner build CI attests (actions/python-versions 3.14.7, the system SQLite 3.45.1) | real | `attested` |
| uv's python-build-standalone 3.14.7 (SQLite 3.53.1, statically linked) | real | `verified`: its key differs from the attested uv 3.53.1 records only in `compile_options_digest` |
| sqlite.org's 3.45.1 amalgamation, as is | constructed | `verified` |
| the same with `SQLITE_OMIT_GENERATED_COLUMNS` | constructed | `refused`: "feature probe xinfo_exposes_generated is False" (§4b step 1) |

The constructed builds come from `specs/evidence/0007/routes/build_route_libs.sh`, which checks the zip's sha256; they
are labelled as such and are not CI matrix rows. Of the 29 jobs attestation run 8 ran, none failed verification.

## 4. The attestation matrix (I5): run 8, by the job this round fixes

The shipped records were made by the job at this round's fixes. `collected/attestation-ci/` carries CI attestation
runs 1–4 and 6–8 (40514117945, 40527873219, 40550040663, 40808367207, 40999790335, 41029898264, 41048681015): each run's job outcomes (`run.json`), every per-job result (`results/`) and its aggregate. Run 8 ran
the job at `03ccdff`; its 22 records are the shipped artifact, written by the production writer in ordinary mode
(each replaced run 4's record of the same key). **22 builds are attested** at the pin: Linux x86_64 and aarch64,
glibc and musl, macOS aarch64, SQLite 3.34.1 to 3.54.1. At stage:
- run 8's aggregate is **re-derived** from its per-job results by the pin's aggregator and equals CI's byte for byte
  (`collected/attestation-ci/run-41048681015-rederive.txt`);
- the 22 records in `tree/src/veracium/store/evidence/sqlite_runtimes.json` **are** that aggregate's records, in order;
- the matrix is reconciled row by row against `tree/specs/evidence/attestation/rows.json`
  (`collected/attestation-ci/run-41048681015-matrix.txt`): 30 rows = 26 evidence + 3 failed-tests (Windows) +
  1 unavailable (python.org on Windows: its installer exits 67).
Group A (SQLite 3.34–3.40) is attested through 0013 v37's attribution of the pre-3.41 `declare_vtab` sequence (§5f.1).

**The runs between round 4 and run 8, disclosed.** Run 5 (40978817628) was cancelled when F1 changed the job. Run 6
(40999790335 at `7d58985`) ran the job before G1–G3; its records were committed and then withdrawn unshipped
(`d714344` reverts `df62e1f`). Run 7 (41029898264 at `d714344`) failed the attestation suite on 19 of its 29 jobs, at
three nodes of this round's own: the two deep-nesting cells and the job matrix, whose first control runs that form (§9);
no record of it was written.

## 5. The specs since round 4

Each version landed byte-identical to research's candidate, on the owner's word:

| version | landed in | what |
|---|---|---|
| 0007 v23.2, v23.2.1 | c0a1ace | round 4's findings as rules: the suite process's completion record and the per-run nonce (0007 §4d, I5); the fresh write runs the production validator over the original current records (§4d, I4); v23.2.1 adds the two closures' mutants to INV-SA6's column |

Each spec's diffs are in `collected/spec-diffs/`: the fold diff (`81c6512`), the since-fold diff, and every
non-insertion token change since the fold (`*.rewordings.txt`):
- 0007: 25 non-insertion token changes (unchanged since round 4: v23.2's one deletion, "(the bootstrap, below)", is in
  text added after the fold);
- 0013: 8 non-insertion token changes;
- 0018: 0 non-insertion token changes.
`collected/spec-diffs/fold-check/` is research's check that the fold is faithful (`bash reproduce.sh`, offline), as in
rounds 3 and 4.

## 6. Known, and queued (not in the reviewed text)

- **Windows:** the attestation suite does not pass on Windows (381 failures in run 8, 378 in run 4: POSIX paths,
  locking, shell tools; the three FIFO cells, `os.mkfifo` being POSIX-only, are among run 8's named failures; each per-job result
  names 20 of its 381), so no Windows build is attested.
- **The compiler in the key:** a python-build-standalone release that changes only `COMPILER=` is a new key and reads
  `verified`; whether the compiler belongs in the identity is queued for 0007 v24.
- **0013 v37, two items that fail closed:** condition (1) relies on an unstated ordering, and condition (2)'s
  first-use test is a text pattern; each is a false refusal, never an admitted write.
- **The collection record's residual (0007 v23.1):** an item a conftest never creates (`pytest_pycollect_makeitem`)
  is invisible to any collection record; the module check still sees a module that yields nothing.
- **The completion record's reach (0007 v23.2):** it proves `pytest.main` returned against HONEST process failures;
  code inside the suite could forge it, which is outside the stated adversary (§4d "The limit, stated").
- **"Superseded" in the fresh write** also covers revision values no format ever had (for example `schema_version`
  `-1`): such records attest nothing in either mode, so fresh mode drops them as it drops any superseded record.
- **Four timed negative witnesses** can only pass vacuously when the second party is late, never fail.
- **"Carry A1–A15 into 0008 when its artifact lands":** deferred by the obligation itself.

## 7. The commit record

The implementation commits are derived from git (`collected/0007-implementation-commits.txt`,
`collected/0013-implementation-commits.txt`, `collected/0018-implementation-commits.txt`, each with its author-free
patch), over the range from the fold `81c6512` (exclusive) to the pin, through the record `27b117fdd669f9c0b6fd654f1612ead6e2492142` of round 3's 25
commits whose `Spec:` lines git does not parse (round 3 §7). The 29 commits since round 4's pin `d087f6e`, by the spec their `Spec:` trailer names:
- inside this review (0007, 0013): `c877648` (the 0013 model measures the build under the draft lock: a race the held
  release's suite found); `c0a1ace` (SA-R4-01 and SA-R4-02, with 0007 v23.2.1); `cff2c7c` (F1–F4); `1d77456` (G1–G3);
  `4dd7f6f` (the deep-nesting cells, exact on every build); `47d2d1e`, `9fea8ef`, `ff6a71f`, `cacea43`, `5518ded` (the
  INV-SA table regenerated after each); `df62e1f` and its revert `d714344` (run 6's records, withdrawn); `e253c12` (run 8's records);
- OUTSIDE this review, in `tree/`: the held minor release's batch (`2f3899b`, `e1c393b`, `9e61997`, `5c15964`, `2934bb8`,
  `d5338b7`, `ad459de`: 0003, 0008, 0012, 0022, 0025, 0031, 0041, 0042, 0044, 0047), the CI floor lane's optional-SDK
  skip (`7542330`, 0014), the 0003 within-episode no-op cell's git-checkout skip (`996df90`, 0003: §9), the 0044
  consolidated campaign re-runs, which pin `tests/` (`8f01da6`, `c2e48c6`, `7d58985`, `47c3420`, `03ccdff`, and the pin
  itself, re-run at `5518ded`), and the src-pinned transcripts re-made on `e253c12` (`8738f56`, 0042 and 0039).
`collected/trailer-sweep.txt` is the history-wide sweep, as in rounds 3 and 4: 75 commits name a spec in a `Spec:` line
git does not parse, the 25 recorded and 50 outside this review; none since round 3. `collected/removed-tests.txt` answers
I7's "do not remove tests", from the reviewed pin `58dd7f6` to this pin.

## 8. The suites

- fresh-clone capture at the pin, `[dev,mcp]`: `7481 passed, 12 skipped, 15 warnings in 4287.14s (1:11:27)` (`collected/COLLECTED.txt`, `collected/suite-run-raw.txt`,
  `collected/suite-results.xml`, `collected/requirements-resolved.txt`)
- the offline launcher on a git-less export of the pin: `7436 passed, 57 skipped, 14 warnings in 4363.25s (1:12:43)` (`collected/offline-run-raw.txt`,
  `collected/offline-skips.txt`, every skip named)
- CI at the pin: run `41128447687`, every job green
- environmental differences, named: the capture runs as a non-root user, on CPython 3.14.7 (the build CI attests), in
  UTC; your round-4 run was UID 0, which the explicit synthetic job state of every `job.decide` cell (C1) makes
  immaterial, and production's root guard still refuses a real root job. The offline launcher runs on a git-less
  export, its skips named in `collected/offline-skips.txt`. Two date-boundary cells of
  `tests/test_omitted_date_defaults_to_utc.py` (the Etc/GMT-14 zone) run or skip depending on the UTC hour of the run.

## 9. Errors ledger

- **The fix's own gaps, found before this package by the second seat (§2):** F1–F4 in the round-4 fix, then G1–G3 in
  F3's own closure (a FIFO hung the JUnit parse; two new guards had no cell that failed with either alone removed).
- **A cell of this round's that held on one build only:** G2 made each malformed-input form assert ITS reason, and the
  deep-nesting form's reason is a fact of the reading thread's stack, not of the input (CPython 3.14 checks C
  recursion against the measured stack). On the local build the 100,000-level nest raises `RecursionError`; on 19 of
  attestation run 7's jobs it parses and is refused for its shape. The refusal was correct everywhere; the asserted
  reason was verified on one build. The cell now measures its reading on the thread `decide` reads from and asserts
  that arm's reason, and a seam reaches the `RecursionError` catch on every build (`4dd7f6f`); both stack regimes
  pass locally.
- **Shipped records that predated the job, twice:** run 4's records predated SA-R4-01's fix, and run 6's predated G1;
  run 6's were withdrawn unshipped, and run 8's are shipped (§4).
- **Round 4's dispatched map carried three defects, each a figure or citation copied forward unchecked** (found by
  dev and research deriving this round's map): its 0007 line citations did not point at their quoted text even at
  round 4's pin; its 0013 citation of line 1266 had moved to line 1308 when 0013 v38 and v38.1 inserted text; and
  its count of the INV-SA carrier map (77 entries) was round 3's, where round 4's pin had 90. Round 4's stage checked
  only that a cited path exists. This round every citation and the count are re-derived at the pin, and the stage now
  checks each line citation's quoted text in the cited line or range (shown red on round 4's map first) and derives the
  carrier counts from `specs/evidence/0007/sa_mutants.py:CARRIERS`.
- **A git-dependent cell from the held minor release:** `tests/test_0003_within_episode_mutants.py`'s no-op control
  cell snapshots the tracked tree through `git ls-files`, and came with the held release's batch after round 4's green
  offline leg; the offline leg at an earlier candidate pin (`8738f56`) failed on it, 1 of 7493. It now skips in a
  git-less copy by the other mutation campaigns' convention (`996df90`: `not _is_checkout()`, a git-checkout inventory
  entry), runs and passes in any checkout, CI's included, and is outside the attestation suite, so run 8's records
  stand: the suite rule's module set is identical at `03ccdff` and here (59 modules).
- Discarded seals this round: none.

## 10. Where to push

1. **The completion signal.** It is written after `pytest.main` returns and bound to this run's nonce and exit status;
   try an honest process failure that still leaves a record.
2. **The child's outputs.** Every form tried is a named refusal; try another path state or content that makes
   `decide` raise, hang, or admit.
3. **The fresh write's originals.** Every original current record is validated before anything is dropped; try a
   fresh write that erases evidence the production validator rejects, or that the ordinary merge would keep.

## Contents

- `0007-store-schema-versioning-SPEC-v23.2.1.md`
- `0013-store-migrations-SPEC-v38.1.md`
- `0018-release-migration-orchestrator-SPEC-v8.md`
- `PIN.txt`
- `README-0007-sqlite-attestation-round5-bundle.md`
- `collected/0007-implementation-commits.txt`
- `collected/0007-implementation.patch`
- `collected/0013-implementation-commits.txt`
- `collected/0013-implementation.patch`
- `collected/0018-implementation-commits.txt`
- `collected/0018-implementation.patch`
- `collected/COLLECTED.txt`
- `collected/attestation-ci/run-40514117945/aggregate.json`
- `collected/attestation-ci/run-40514117945/results/result-0.json`
- `collected/attestation-ci/run-40514117945/results/result-1.json`
- `collected/attestation-ci/run-40514117945/results/result-10.json`
- `collected/attestation-ci/run-40514117945/results/result-11.json`
- `collected/attestation-ci/run-40514117945/results/result-12.json`
- `collected/attestation-ci/run-40514117945/results/result-13.json`
- `collected/attestation-ci/run-40514117945/results/result-14.json`
- `collected/attestation-ci/run-40514117945/results/result-15.json`
- `collected/attestation-ci/run-40514117945/results/result-16.json`
- `collected/attestation-ci/run-40514117945/results/result-17.json`
- `collected/attestation-ci/run-40514117945/results/result-18.json`
- `collected/attestation-ci/run-40514117945/results/result-19.json`
- `collected/attestation-ci/run-40514117945/results/result-2.json`
- `collected/attestation-ci/run-40514117945/results/result-20.json`
- `collected/attestation-ci/run-40514117945/results/result-21.json`
- `collected/attestation-ci/run-40514117945/results/result-22.json`
- `collected/attestation-ci/run-40514117945/results/result-23.json`
- `collected/attestation-ci/run-40514117945/results/result-24.json`
- `collected/attestation-ci/run-40514117945/results/result-25.json`
- `collected/attestation-ci/run-40514117945/results/result-26.json`
- `collected/attestation-ci/run-40514117945/results/result-27.json`
- `collected/attestation-ci/run-40514117945/results/result-28.json`
- `collected/attestation-ci/run-40514117945/results/result-29.json`
- `collected/attestation-ci/run-40514117945/results/result-3.json`
- `collected/attestation-ci/run-40514117945/results/result-4.json`
- `collected/attestation-ci/run-40514117945/results/result-5.json`
- `collected/attestation-ci/run-40514117945/results/result-6.json`
- `collected/attestation-ci/run-40514117945/results/result-7.json`
- `collected/attestation-ci/run-40514117945/results/result-9.json`
- `collected/attestation-ci/run-40514117945/run.json`
- `collected/attestation-ci/run-40527873219/aggregate.json`
- `collected/attestation-ci/run-40527873219/results/result-0.json`
- `collected/attestation-ci/run-40527873219/results/result-1.json`
- `collected/attestation-ci/run-40527873219/results/result-10.json`
- `collected/attestation-ci/run-40527873219/results/result-11.json`
- `collected/attestation-ci/run-40527873219/results/result-12.json`
- `collected/attestation-ci/run-40527873219/results/result-13.json`
- `collected/attestation-ci/run-40527873219/results/result-14.json`
- `collected/attestation-ci/run-40527873219/results/result-15.json`
- `collected/attestation-ci/run-40527873219/results/result-16.json`
- `collected/attestation-ci/run-40527873219/results/result-17.json`
- `collected/attestation-ci/run-40527873219/results/result-18.json`
- `collected/attestation-ci/run-40527873219/results/result-19.json`
- `collected/attestation-ci/run-40527873219/results/result-2.json`
- `collected/attestation-ci/run-40527873219/results/result-20.json`
- `collected/attestation-ci/run-40527873219/results/result-21.json`
- `collected/attestation-ci/run-40527873219/results/result-22.json`
- `collected/attestation-ci/run-40527873219/results/result-23.json`
- `collected/attestation-ci/run-40527873219/results/result-24.json`
- `collected/attestation-ci/run-40527873219/results/result-25.json`
- `collected/attestation-ci/run-40527873219/results/result-26.json`
- `collected/attestation-ci/run-40527873219/results/result-27.json`
- `collected/attestation-ci/run-40527873219/results/result-28.json`
- `collected/attestation-ci/run-40527873219/results/result-29.json`
- `collected/attestation-ci/run-40527873219/results/result-3.json`
- `collected/attestation-ci/run-40527873219/results/result-4.json`
- `collected/attestation-ci/run-40527873219/results/result-5.json`
- `collected/attestation-ci/run-40527873219/results/result-6.json`
- `collected/attestation-ci/run-40527873219/results/result-7.json`
- `collected/attestation-ci/run-40527873219/results/result-9.json`
- `collected/attestation-ci/run-40527873219/run.json`
- `collected/attestation-ci/run-40550040663/aggregate.json`
- `collected/attestation-ci/run-40550040663/results/result-0.json`
- `collected/attestation-ci/run-40550040663/results/result-1.json`
- `collected/attestation-ci/run-40550040663/results/result-10.json`
- `collected/attestation-ci/run-40550040663/results/result-11.json`
- `collected/attestation-ci/run-40550040663/results/result-12.json`
- `collected/attestation-ci/run-40550040663/results/result-13.json`
- `collected/attestation-ci/run-40550040663/results/result-14.json`
- `collected/attestation-ci/run-40550040663/results/result-15.json`
- `collected/attestation-ci/run-40550040663/results/result-16.json`
- `collected/attestation-ci/run-40550040663/results/result-17.json`
- `collected/attestation-ci/run-40550040663/results/result-18.json`
- `collected/attestation-ci/run-40550040663/results/result-19.json`
- `collected/attestation-ci/run-40550040663/results/result-2.json`
- `collected/attestation-ci/run-40550040663/results/result-20.json`
- `collected/attestation-ci/run-40550040663/results/result-21.json`
- `collected/attestation-ci/run-40550040663/results/result-22.json`
- `collected/attestation-ci/run-40550040663/results/result-23.json`
- `collected/attestation-ci/run-40550040663/results/result-24.json`
- `collected/attestation-ci/run-40550040663/results/result-25.json`
- `collected/attestation-ci/run-40550040663/results/result-26.json`
- `collected/attestation-ci/run-40550040663/results/result-27.json`
- `collected/attestation-ci/run-40550040663/results/result-28.json`
- `collected/attestation-ci/run-40550040663/results/result-29.json`
- `collected/attestation-ci/run-40550040663/results/result-3.json`
- `collected/attestation-ci/run-40550040663/results/result-4.json`
- `collected/attestation-ci/run-40550040663/results/result-5.json`
- `collected/attestation-ci/run-40550040663/results/result-6.json`
- `collected/attestation-ci/run-40550040663/results/result-7.json`
- `collected/attestation-ci/run-40550040663/results/result-9.json`
- `collected/attestation-ci/run-40550040663/run.json`
- `collected/attestation-ci/run-40808367207/aggregate.json`
- `collected/attestation-ci/run-40808367207/results/result-0.json`
- `collected/attestation-ci/run-40808367207/results/result-1.json`
- `collected/attestation-ci/run-40808367207/results/result-10.json`
- `collected/attestation-ci/run-40808367207/results/result-11.json`
- `collected/attestation-ci/run-40808367207/results/result-12.json`
- `collected/attestation-ci/run-40808367207/results/result-13.json`
- `collected/attestation-ci/run-40808367207/results/result-14.json`
- `collected/attestation-ci/run-40808367207/results/result-15.json`
- `collected/attestation-ci/run-40808367207/results/result-16.json`
- `collected/attestation-ci/run-40808367207/results/result-17.json`
- `collected/attestation-ci/run-40808367207/results/result-18.json`
- `collected/attestation-ci/run-40808367207/results/result-19.json`
- `collected/attestation-ci/run-40808367207/results/result-2.json`
- `collected/attestation-ci/run-40808367207/results/result-20.json`
- `collected/attestation-ci/run-40808367207/results/result-21.json`
- `collected/attestation-ci/run-40808367207/results/result-22.json`
- `collected/attestation-ci/run-40808367207/results/result-23.json`
- `collected/attestation-ci/run-40808367207/results/result-24.json`
- `collected/attestation-ci/run-40808367207/results/result-25.json`
- `collected/attestation-ci/run-40808367207/results/result-26.json`
- `collected/attestation-ci/run-40808367207/results/result-27.json`
- `collected/attestation-ci/run-40808367207/results/result-28.json`
- `collected/attestation-ci/run-40808367207/results/result-29.json`
- `collected/attestation-ci/run-40808367207/results/result-3.json`
- `collected/attestation-ci/run-40808367207/results/result-4.json`
- `collected/attestation-ci/run-40808367207/results/result-5.json`
- `collected/attestation-ci/run-40808367207/results/result-6.json`
- `collected/attestation-ci/run-40808367207/results/result-7.json`
- `collected/attestation-ci/run-40808367207/results/result-9.json`
- `collected/attestation-ci/run-40808367207/run.json`
- `collected/attestation-ci/run-40999790335/aggregate.json`
- `collected/attestation-ci/run-40999790335/results/result-0.json`
- `collected/attestation-ci/run-40999790335/results/result-1.json`
- `collected/attestation-ci/run-40999790335/results/result-10.json`
- `collected/attestation-ci/run-40999790335/results/result-11.json`
- `collected/attestation-ci/run-40999790335/results/result-12.json`
- `collected/attestation-ci/run-40999790335/results/result-13.json`
- `collected/attestation-ci/run-40999790335/results/result-14.json`
- `collected/attestation-ci/run-40999790335/results/result-15.json`
- `collected/attestation-ci/run-40999790335/results/result-16.json`
- `collected/attestation-ci/run-40999790335/results/result-17.json`
- `collected/attestation-ci/run-40999790335/results/result-18.json`
- `collected/attestation-ci/run-40999790335/results/result-19.json`
- `collected/attestation-ci/run-40999790335/results/result-2.json`
- `collected/attestation-ci/run-40999790335/results/result-20.json`
- `collected/attestation-ci/run-40999790335/results/result-21.json`
- `collected/attestation-ci/run-40999790335/results/result-22.json`
- `collected/attestation-ci/run-40999790335/results/result-23.json`
- `collected/attestation-ci/run-40999790335/results/result-24.json`
- `collected/attestation-ci/run-40999790335/results/result-25.json`
- `collected/attestation-ci/run-40999790335/results/result-26.json`
- `collected/attestation-ci/run-40999790335/results/result-27.json`
- `collected/attestation-ci/run-40999790335/results/result-28.json`
- `collected/attestation-ci/run-40999790335/results/result-29.json`
- `collected/attestation-ci/run-40999790335/results/result-3.json`
- `collected/attestation-ci/run-40999790335/results/result-4.json`
- `collected/attestation-ci/run-40999790335/results/result-5.json`
- `collected/attestation-ci/run-40999790335/results/result-6.json`
- `collected/attestation-ci/run-40999790335/results/result-7.json`
- `collected/attestation-ci/run-40999790335/results/result-9.json`
- `collected/attestation-ci/run-40999790335/run.json`
- `collected/attestation-ci/run-41029898264/aggregate.json`
- `collected/attestation-ci/run-41029898264/results/result-0.json`
- `collected/attestation-ci/run-41029898264/results/result-1.json`
- `collected/attestation-ci/run-41029898264/results/result-10.json`
- `collected/attestation-ci/run-41029898264/results/result-11.json`
- `collected/attestation-ci/run-41029898264/results/result-12.json`
- `collected/attestation-ci/run-41029898264/results/result-13.json`
- `collected/attestation-ci/run-41029898264/results/result-14.json`
- `collected/attestation-ci/run-41029898264/results/result-15.json`
- `collected/attestation-ci/run-41029898264/results/result-16.json`
- `collected/attestation-ci/run-41029898264/results/result-17.json`
- `collected/attestation-ci/run-41029898264/results/result-18.json`
- `collected/attestation-ci/run-41029898264/results/result-19.json`
- `collected/attestation-ci/run-41029898264/results/result-2.json`
- `collected/attestation-ci/run-41029898264/results/result-20.json`
- `collected/attestation-ci/run-41029898264/results/result-21.json`
- `collected/attestation-ci/run-41029898264/results/result-22.json`
- `collected/attestation-ci/run-41029898264/results/result-23.json`
- `collected/attestation-ci/run-41029898264/results/result-24.json`
- `collected/attestation-ci/run-41029898264/results/result-25.json`
- `collected/attestation-ci/run-41029898264/results/result-26.json`
- `collected/attestation-ci/run-41029898264/results/result-27.json`
- `collected/attestation-ci/run-41029898264/results/result-28.json`
- `collected/attestation-ci/run-41029898264/results/result-29.json`
- `collected/attestation-ci/run-41029898264/results/result-3.json`
- `collected/attestation-ci/run-41029898264/results/result-4.json`
- `collected/attestation-ci/run-41029898264/results/result-5.json`
- `collected/attestation-ci/run-41029898264/results/result-6.json`
- `collected/attestation-ci/run-41029898264/results/result-7.json`
- `collected/attestation-ci/run-41029898264/results/result-9.json`
- `collected/attestation-ci/run-41029898264/run.json`
- `collected/attestation-ci/run-41048681015-matrix.txt`
- `collected/attestation-ci/run-41048681015-rederive.txt`
- `collected/attestation-ci/run-41048681015/aggregate.json`
- `collected/attestation-ci/run-41048681015/results/result-0.json`
- `collected/attestation-ci/run-41048681015/results/result-1.json`
- `collected/attestation-ci/run-41048681015/results/result-10.json`
- `collected/attestation-ci/run-41048681015/results/result-11.json`
- `collected/attestation-ci/run-41048681015/results/result-12.json`
- `collected/attestation-ci/run-41048681015/results/result-13.json`
- `collected/attestation-ci/run-41048681015/results/result-14.json`
- `collected/attestation-ci/run-41048681015/results/result-15.json`
- `collected/attestation-ci/run-41048681015/results/result-16.json`
- `collected/attestation-ci/run-41048681015/results/result-17.json`
- `collected/attestation-ci/run-41048681015/results/result-18.json`
- `collected/attestation-ci/run-41048681015/results/result-19.json`
- `collected/attestation-ci/run-41048681015/results/result-2.json`
- `collected/attestation-ci/run-41048681015/results/result-20.json`
- `collected/attestation-ci/run-41048681015/results/result-21.json`
- `collected/attestation-ci/run-41048681015/results/result-22.json`
- `collected/attestation-ci/run-41048681015/results/result-23.json`
- `collected/attestation-ci/run-41048681015/results/result-24.json`
- `collected/attestation-ci/run-41048681015/results/result-25.json`
- `collected/attestation-ci/run-41048681015/results/result-26.json`
- `collected/attestation-ci/run-41048681015/results/result-27.json`
- `collected/attestation-ci/run-41048681015/results/result-28.json`
- `collected/attestation-ci/run-41048681015/results/result-29.json`
- `collected/attestation-ci/run-41048681015/results/result-3.json`
- `collected/attestation-ci/run-41048681015/results/result-4.json`
- `collected/attestation-ci/run-41048681015/results/result-5.json`
- `collected/attestation-ci/run-41048681015/results/result-6.json`
- `collected/attestation-ci/run-41048681015/results/result-7.json`
- `collected/attestation-ci/run-41048681015/results/result-9.json`
- `collected/attestation-ci/run-41048681015/run.json`
- `collected/check-verdict-tarball.txt`
- `collected/check_verdict_tarball.py`
- `collected/mutation-table-a-matrix-check.txt`
- `collected/mutation-table-pa1-check.txt`
- `collected/mutation-table-sa-check.txt`
- `collected/mutation-table-sa10-check.txt`
- `collected/obligation-map.md`
- `collected/offline-run-raw.txt`
- `collected/offline-skips.txt`
- `collected/removed-tests.txt`
- `collected/requirements-resolved.txt`
- `collected/rewordings.py`
- `collected/spec-diffs/0007-store-schema-versioning.fold.diff`
- `collected/spec-diffs/0007-store-schema-versioning.rewordings.txt`
- `collected/spec-diffs/0007-store-schema-versioning.since-fold.diff`
- `collected/spec-diffs/0013-store-migrations.fold.diff`
- `collected/spec-diffs/0013-store-migrations.rewordings.txt`
- `collected/spec-diffs/0013-store-migrations.since-fold.diff`
- `collected/spec-diffs/0018-release-migration-orchestrator.fold.diff`
- `collected/spec-diffs/0018-release-migration-orchestrator.rewordings.txt`
- `collected/spec-diffs/0018-release-migration-orchestrator.since-fold.diff`
- `collected/spec-diffs/fold-check-reproduce.txt`
- `collected/spec-diffs/fold-check/README.md`
- `collected/spec-diffs/fold-check/check.out`
- `collected/spec-diffs/fold-check/check_offline.py`
- `collected/spec-diffs/fold-check/controls.out`
- `collected/spec-diffs/fold-check/inputs/MANIFEST.tsv`
- `collected/spec-diffs/fold-check/inputs/amendment-v0.12.1-134243c63b05845a.md`
- `collected/spec-diffs/fold-check/inputs/base-0007-ccf97c874e9ede88.md`
- `collected/spec-diffs/fold-check/inputs/base-0013-d315ed0394c29437.md`
- `collected/spec-diffs/fold-check/inputs/base-0018-fa815cf3cf97342a.md`
- `collected/spec-diffs/fold-check/inputs/check.py-d10a97d39e59caa0.py`
- `collected/spec-diffs/fold-check/inputs/controls.py-199f06df6ffbf200.py`
- `collected/spec-diffs/fold-check/inputs/landed-0007-2508a477e1ebf82e.md`
- `collected/spec-diffs/fold-check/inputs/landed-0013-a215a6960cf325d8.md`
- `collected/spec-diffs/fold-check/inputs/landed-0018-2308c45d2d269ff0.md`
- `collected/spec-diffs/fold-check/reproduce.sh`
- `collected/suite-results.xml`
- `collected/suite-run-raw.txt`
- `collected/trailer-sweep.txt`
- `collected/tree_hash_witness.sh`
- `prior-rounds/0007-sqlite-attestation-round1-verdict-verbatim.md`
- `prior-rounds/0007-sqlite-attestation-round2-implementation-obligations-verbatim.md`
- `prior-rounds/0007-sqlite-attestation-round2-verdict-verbatim.md`
- `prior-rounds/0007-sqlite-attestation-round3-implementation-obligations-verbatim.md`
- `prior-rounds/0007-sqlite-attestation-round3-validation-verbatim.md`
- `prior-rounds/0007-sqlite-attestation-round3-verdict-verbatim.md`
- `prior-rounds/0007-sqlite-attestation-round4-implementation-obligations-verbatim.md`
- `prior-rounds/0007-sqlite-attestation-round4-validation-verbatim.md`
- `prior-rounds/0007-sqlite-attestation-round4-verdict-verbatim.md`
- `prior-rounds/README-0007-sqlite-attestation-round2-bundle.md`
- `prior-rounds/README-0007-sqlite-attestation-round3-bundle.md`
- `prior-rounds/README-0007-sqlite-attestation-round4-bundle.md`
- `tree/` — the repository at the pin (`git archive`), witnessed by `collected/tree_hash_witness.sh`
- `SHA256SUMS` — every other member's digest
