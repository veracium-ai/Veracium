# 0018 adjacent rungs: round 6, the implementation review

**Canonical artifact:** this package, bound by `PIN.txt` (pin `91838da576b567ce35c93ab6cee875230e093b12`, tree `7095d244ca37caf587a1066671fe1291c97461b5`, CI run `42451632282`) and
`SHA256SUMS`. `tree/` is `git archive` of the pin, witnessed by `collected/tree_hash_witness.sh`.

## 1. What this round asks

Round 5 returned the implementation for correction, the accepted design staying accepted: R5-01 and R5-02 blocking, C5-01 and C5-02 to
resolve in the package, R4-02 and R4-03 closed, E4-01 retained as disclosed (`prior-rounds/0018-adjacent-rungs-round5-verdict-verbatim.md`).
This package is the bounded resubmission at `91838da576b567ce35c93ab6cee875230e093b12`: the two corrections with their controls, refreshed mutation and obligation evidence,
the full offline run, and the two reconciliations. The review surface is unchanged: I13′, I15′, I19′ and I33–I39, retaining I14, I16–I18
and I20–I23.

**C5-01 is folded: the spec is v9.1.** `0018-release-migration-orchestrator-SPEC-v9.1.md` rides at the package root, `Spec-Status:
accepted`, byte-identical to `tree/specs/`. Against round 5's v9 it changes two lines: the Version cell, and §4j.9.7c's E1 row, whose input
now states `audit_committed` as `False`, `True` or `None`, each with its condition, and whose sentence is the one `audit_committed` selects.
The disclosure id, the action classification, the restriction, the operation id and the counting are unchanged. The owner approved the text.
Its two lines alone are `collected/spec-diffs/0018-release-migration-orchestrator.v9-to-v9.1.diff`; the since-fold diff carries them with the
earlier annotations. Please read it as the reconciliation round 5
asked for, not as a design change.

## 2. What round 5 asked, and what changed

`collected/0018-adjacent-rungs-implementation-commits.txt` lists every commit from the fold, derived by `Spec:` trailer; this round's are the
last 10. The 4 other commits in the span touch neither `src/`, `tests/` nor the 0018 spec: `e6fc5bc3` CI lane split: each long lane runs as five single-process shards, measured on a branch first; `9c741a99` CI lane split: a `pytest (py3.14)` job carries main's required check; `15ea40f0` 0044 campaign: each group's wall time is recorded in its shard result; `6d683e67` 0042: the INV-7 run re-made on a282215c after 0018 round 6. `collected/0018-adjacent-rungs-since-round5.patch` is the
concise patch from round 5's pin, beside the cumulative one. The closures' cells are `tests/test_0018_r5_closures.py`, at rungs 1→2, 13→14
and 15→16, every one through the real rung or the real walk.

- **R5-01, absence is proven only where control flow proves it.** The writers are split into load, append-once, stage (build the entry,
  write and fsync the tmp file) and publish. A failure in the stage window raises `_NotPublished`: the trail was read, append-once found no
  record of this kind for this id, and `os.replace` was never called. That type alone maps to N1 at the attempted sink and to
  `audit_committed=False` at the terminal sink. Every other failure is unresolved. At the attempted sink it is N2, with the id printed; a
  raising `os.replace` is still narrowed to N1 by a successful read-back with no attempted entry for the id, as round 4 accepted. At the
  terminal sink one recovery `read_terminal` decides: `True` for a valid record equal to the facts, `False` for a successful read with no
  record (never after append-once), `None` otherwise. The cells cross existing attempted and matching or different terminal records with
  readable, transiently unreadable and persistently unreadable loads, with genuine-absence controls and failures inside the window.
- **Where the trail is there and stays unreadable, the walk ends at E2.** The attempted sink still selects N2. The walk's own terminal
  readback then cannot read the trail either, and §4f routes a malformed readback to `MigrationAuditReadError` under every outcome, the
  frozen rule that keeps audit failures loud (I17). So the walk prints the read error, the operation id, `inspect-audit-trail` and no rerun.
  We kept §4f rather than add a routing exception. A trail that becomes readable again, or is truly absent, gives N2 at the walk.
- **Absence is an lstat ENOENT, at all four sites 0018 owns.** `os.path.exists` answers False for any stat error, so a record inside a
  directory the process cannot search read as nothing there (research's read, measured). `_absent` now decides at the two trail readers, the
  mint and preflight. A store in such a directory is `store-unopenable` and fix-access (U6), never `migration-source-missing` and fix-the-path
  (U2). The cells use an injected EACCES, which runs on any euid, and a real `chmod 000`, which skips as root. A census of the exists family
  in `src/` at round 5's pin finds 18 sites: these four, and fourteen outside 0018 (`audit.py:56`, `doctor.py:175`, `dryrun.py:94` and `:114`,
  `diagnostics.py` ×4, `telemetry.py` ×4, `schema_version.py:1409` and `:1692`). None licenses a weaker outcome here, and they are queued.
- **R5-02, the observer's universe is not the plan.** `_Trace` in `tests/test_0018_rungs_t5.py` observes every step any plan can name, at
  any depth. It records every call the dispatcher makes to a `migration.py` function off its own list (the run's state object, the plan and
  the clock, keyed by code object and measured on every clean route). It keeps every statement outside an entry's extent, and it refuses any
  thread started during a rung, recorded by CPython's own audit event for a thread start, whatever name reached it. Your off-plan read is a
  row. So are the same read nested in a planned check, a non-step read helper at dispatch level, the read in a `threading.Thread` and in a
  low-level `_thread.start_joinable_thread`, and a no-op thread started before the first entry and after the last.
- **C5-02, the backward control is generated.** The stage runs the pin's closure file, and its twin on a shared seam, against round 5's
  `src/` from the pin's own tree, asserting the import origin inside each run. `collected/backward-control.txt` names the files by git blob
  and round 5's `src/` by git tree, and lists every result by test function and kind. `collected/backward-control-results.xml` and
  `collected/backward-twin-results.xml` are the raw junit: 69 cells: 21 pass, 45 fail by assertion, 3 cannot run at round 5's src (they use `veracium.store.release_migration._stage_audit`, which round 6 added); their twin on a shared seam, `tests/test_0018_r4_closures.py::test_a_failed_terminal_write_reports_what_it_established[*-fsync-before-rename]`, 3 of 3 pass at round 5's src. A failure that is neither an assertion nor a name round 6 added
  refuses the stage, checked by importing the module under each `src/`. The count cannot drift from the file it describes.
- **E4-01** is unchanged, as the verdict allowed.

## 3. The obligations and the artifacts you asked for

`collected/obligation-map.md` is generated by `collected/mk_map18.py`: 10 invariants, 18 closure checks, 84 of the table's 84 rows placed, no defect. `collected/obligation-map.json` beside it carries the
same map machine-readably, every invariant's and closure check's full text untruncated. The map's first section gives each invariant's text
from the spec, with code, cells and mutation rows. Its second gives each closure check from the verdicts in the verdict's words, with cells.
Those cells are named by reading the check against them; the mutation rows are what has been executed.

- **Declared plan descriptors and preimages.** `tree/specs/evidence/0018/rungs/digest_vectors.json`, unchanged: no plan or preimage moved.
- **Release-authored populated fixtures.** `tree/specs/evidence/0018/rungs/fixtures.tar.xz`, 141 stores, with `manifest.json` and a README.
- **The target-aware SA10 campaign.** `tree/specs/evidence/0013/sa10/mutation-table.json`, 74 of 74 rows killed.
- **The original-preservation checks.** `tests/test_0018_rungs_t3.py`, unchanged.

**The implementation mutation table** (`tree/specs/evidence/0018/rungs/implementation/mutation-table.json`, rendered at
`collected/mutation-table-0018.md`): 84 rows, 84 KILLED (by assertion or a missing expected refusal), every honest probe passing, 6 controls good. Eleven rows are new this round: four for R5-01 (an unresolved write read as absence, the load
inside the proving window, an unresolved terminal write reported unpublished, absence by `os.path.exists`) and seven for R5-02. Two of round
4's rows are re-anchored on the new code with the same meaning.

**The cells:** `collected/cell-results.md`, from the capture's junit: 856 cells, 856 passed, 0 skipped, none failed, every collected cell present.

## 4. Found while building this

- **A second route to the same false proof.** Research found that `os.path.exists` reads a permission error as absence, at the trail and,
  as the census then showed, at the store path in the mint and in preflight.
- **Threads, twice.** The first thread check compared the threads alive before and after a rung, so one that started and ended inside it was
  unseen. The second patched two names, and a direct call of `_thread.start_joinable_thread`, the function `threading` itself starts through,
  reached neither. The audit event closes the class. Both are rows.
- **The backward count we shipped last round was stale.** It was measured before an assertion was added to the file it described, and
  neither seat re-ran it after. It is generated now.

## 5. Limits

- The attestation is the host's assertion, and a same-version, same-shape swap between the mint and the transaction is not seen.
- A walk does `n` transactions where the library call does one.
- `src/veracium/store/release_migration.py` holds no enforcement entries in the 0042 declaration, as at every release, so a rung's refusals take
  that module's default class.
- The closure-check cells in the map's second section were matched by reading. Only the rows in its first section were executed as
  mutants.
- N1 after a raising rename rests on one read-back of the sidecar, made at once: a rename that takes effect after that read is not modelled.
- The dispatcher's own list was derived from clean traces, so it admits what the clean code does at dispatch level: the state object, the plan
  and the clock, each pure except the clock, whose second read is its own act and a row.
- E4-01: a fault restoring connection state after a real commit still reports `internal-error` with unknown facts and no committed rung. The
  classifier asks for inspection and offers no rerun.
- An intermediate rung's refusal in rows 3 and 6 prints `this build=` with the rung's target, not the build's head. It is queued.
- `direct` pins `plan(b, SCHEMA_VERSION)`, so the next head moves it. Separating it from the frozen rungs is queued before that head.

## 6. Contents

- `0018-release-migration-orchestrator-SPEC-v9.1.md`
- `PIN.txt`
- `README-0018-adjacent-rungs-round6-bundle.md`
- `collected/0018-adjacent-rungs-implementation-commits.txt`
- `collected/0018-adjacent-rungs-implementation.patch`
- `collected/0018-adjacent-rungs-path-commits.patch`
- `collected/0018-adjacent-rungs-path-commits.txt`
- `collected/0018-adjacent-rungs-since-round5.patch`
- `collected/COLLECTED.txt`
- `collected/backward-control-results.xml`
- `collected/backward-control-run-raw.txt`
- `collected/backward-control.txt`
- `collected/backward-twin-results.xml`
- `collected/backward-twin-run-raw.txt`
- `collected/cell-results.md`
- `collected/cell_results.py`
- `collected/check_verdict_tarball.py`
- `collected/digest-vectors-check.txt`
- `collected/mk_map18.py`
- `collected/mutation-table-0013-sa10_mutants-check.txt`
- `collected/mutation-table-0018-rungs-implementation_mutants-check.txt`
- `collected/mutation-table-0018.md`
- `collected/obligation-map.json`
- `collected/obligation-map.md`
- `collected/offline-results.xml`
- `collected/offline-run-raw.txt`
- `collected/offline-skips.txt`
- `collected/requirements-resolved.txt`
- `collected/spec-diffs/0007-store-schema-versioning.since-fold.diff`
- `collected/spec-diffs/0013-store-migrations.since-fold.diff`
- `collected/spec-diffs/0018-release-migration-orchestrator.fold.diff`
- `collected/spec-diffs/0018-release-migration-orchestrator.since-fold.diff`
- `collected/spec-diffs/0018-release-migration-orchestrator.v9-to-v9.1.diff`
- `collected/suite-results.xml`
- `collected/suite-run-raw.txt`
- `collected/tree_hash_witness.sh`
- `prior-rounds/0018-adjacent-rungs-round1-review-package.tar.gz.sha256`
- `prior-rounds/0018-adjacent-rungs-round1-verdict-verbatim.md`
- `prior-rounds/0018-adjacent-rungs-round2-review-package.tar.gz.sha256`
- `prior-rounds/0018-adjacent-rungs-round2-verdict-verbatim.md`
- `prior-rounds/0018-adjacent-rungs-round3-review-package.tar.gz.sha256`
- `prior-rounds/0018-adjacent-rungs-round3-verdict-verbatim.md`
- `prior-rounds/0018-adjacent-rungs-round4-implementation-review-package.tar.gz.sha256`
- `prior-rounds/0018-adjacent-rungs-round4-verdict-verbatim.md`
- `prior-rounds/0018-adjacent-rungs-round5-implementation-review-package.tar.gz.sha256`
- `prior-rounds/0018-adjacent-rungs-round5-verdict-verbatim.md`
- `tree/` — the repository at the pin (`git archive`), witnessed by `collected/tree_hash_witness.sh`
- `SHA256SUMS` — every other member's digest
