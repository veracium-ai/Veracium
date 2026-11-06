<!-- 0048's terminal record: the accepted package's README: every finding found before dispatch, and the named limits, byte-copied UNMODIFIED from the accepted package 51a947b3a25d1814bba1ebfacff397ff9f0b4aa68782fce61e6de48524f92f37 @ 1ba2a698bb1cfb9864db84a11632719d6da90212, member `README-0048-round6-bundle.md`, sha256 9a4ff0850e5b2c39ea72fc6b459bfea5813a1ba9f4ed26bed47523299d98db2f. Everything below this comment is those bytes. The verdict (coordination 791e0e8): "Preserve the named residuals alongside the green matrices so future readers can distinguish a governing check from a disclosed boundary." -->
# 0048 decay never raises confidence: round 6, the implementation review of the amendment of R5-01 and R5-02

**Canonical artifact:** this package, bound by `PIN.txt` (pin `1ba2a698bb1cfb9864db84a11632719d6da90212`, tree `c3da711d14b4b4b6033f3a2e952cb2640413bc9f`, CI run `42052189718`) and
`SHA256SUMS`. `tree/` is `git archive` of the pin, witnessed by `collected/tree_hash_witness.sh`.

## 1. What this round asks

Round 2 accepted the design of 0048 v3.3 (pin `c1c9ecfe302d07d7d70f69918cf11c58b4126d19`). Rounds 3, 4 and 5 reviewed the
implementation. Round 5 (`prior-rounds/0048-round5-verdict-verbatim.md`) closed R4-01's four original witnesses and
R4-02's twelve cases, retained everything earlier, and returned the implementation for R5-01 (medium: a receiver
spelled `self` was exempted without resolving what it denotes) and R5-02 (low: the prepare-only classifier could execute
a statement on the qualified runtime). This round asks whether the amendment closes both without moving anything earlier
rounds closed. The accepted design surface is unchanged, and nothing here asks for a design round.

**The spec.** `0048-decay-never-raises-confidence-SPEC-v4.2.md` rides at the package root, `Spec-Status: accepted`,
byte-identical to `tree/specs/` at the pin. It is the text round 5 bound: this round changes no spec text
(`collected/spec-diffs/` holds the fold's diff and every change since, labelled; 2 commits after the fold).

**What the text does not yet say.** The two points round 5's README named still stand: v4.2's N4f row reads "AST over
`src/veracium/store/sqlite.py`" where the check runs over all of `src/`, and §4A says the refusal names the value where
an integer too long to print is named by sign and bit length. Both stay queued as v4.3 deltas after this verdict.

**What changed since round 5's pin** (`collected/0048-implementation-commits.txt`, derived from git by the commits'
`Spec:` trailer, and `collected/0048-implementation.patch`, the same commits without author headers;
`collected/0048-path-commits.txt` and `.patch` list every commit that touches 0048's own files, derived by path, with
0 found by path only):

- **R5-01, the product change.** `src/veracium/scope_read.py`: `MembershipResolver._rows` is `_membership_rows`, its
  definition and its two calls. No behaviour changes. The exemption existed only because two unrelated functions shared
  a name, so the amendment removes the collision and not just the symptom. `_rows` now has one definition, the
  execute-family one.
- **R5-01, the gate.** In `tests/test_0048_decay_bounds.py`:
  - `_exec_callee` and the held-reference check lose their `self` exemption, with no reviewed list in its place: every
    `.<derived name>` on any receiver counts;
  - the derived names join the literal-`getattr` rule;
  - one rule across `src/` backs every other line of the gate that reads `self.X`: the only binder of `self` is the first
    parameter of a plain method directly in a class, and every read reaches one (`_self_problems`). A static or class
    method does not count, and neither does an unknown decorator;
  - the `args.backup` exception is keyed by its function and that function's digest, and the attribute is never the
    function of a call;
  - the head rule no longer exempts a bare name.
- **R5-01's class, the gate's reach.** The second seat's executable pass after the fix reached an attribute with no
  attribute node (`match conn: case object(execute=run):`) and reached code from text through a library, each past the gate
  and the census and writing on a real connection (§4). So `_import_problems` and `_own_problems` close what src/ may reach
  by name, over every module of src/:
  - `match` and a star import are refused;
  - `SRC_IMPORTS` freezes every module src/ names and every member it reads of each, because a list of import statements
    alone leaves an unlisted module one attribute away (`urllib.request.string`, `enum.bltns`, `dataclasses.inspect`);
  - a module is read only as the base of an attribute, and a name another module of src/ imported is not reached through it;
  - `SRC_DUNDERS` freezes every dunder src/ reads, so `__globals__`, `__builtins__` and `__match_args__` need no naming;
  - `__import__` and `TypeAdapter` stand only at their reviewed calls, each frozen by digest;
  - an annotation holding a call, an f-string or a binary operator other than `|` and `-`, at any depth of string, a class
    inside a function and `type` building a class are refused, because pydantic evaluates annotation text against a
    function's locals.

  `R6_IMPORT` holds these forms, static and runtime apart, each row asserted, and `collected/receiver-forms.md` renders it as a
  second table. `::test_the_closed_tables_are_exactly_what_src_uses`
  compares the tables with src/ both ways, and `::test_no_listed_member_holds_a_route_to_an_unlisted_module` audits each
  importable row on the running interpreter, one attribute level, classes and modules only.
- **R5-02.** The classifier compiles `EXPLAIN QUERY PLAN <statement>`, so the statement itself never runs, whatever the
  runtime's variable limit is (`collected/runtime-limits.json`, measured: 250000). A statement that binds exactly runs only
  the plan listing. A flag PRAGMA acts at prepare, so the scratch is thrown away after any PRAGMA outside the pin's set. Plain `EXPLAIN` was tried first: it makes the string
  `QUERY PLAN x` prepare, which SQLite refuses bare. `tree/specs/evidence/0048/contract_harness_0048.py` takes the same
  prefix, so the gate and the model state one rule.

**The named limits.**

- **A statement in a ladder table is SA10's, not N4f's.** Five `conn.execute(stmt)` sites in `_apply_forward` read a
  for-target, so N4f's binding stops there, and a statement added to a table moves no digest. N4f accepts such a plant.
  SA10 refuses it by execution on every base that runs the table, and v1 never runs it (`collected/sa10-ladder-plant.txt`,
  46 paths refused; `::test_a_ladder_table_statement_is_not_n4fs_and_sa10_refuses_it`). A static check over the
  tables is queued with the adjacent-rungs work, which rewrites these sites. Twelve other rows read a for-target; they
  are listed in `collected/receiver-forms.md`, and no governing check is claimed for them.
- **N4f reads names, not values.** It refuses `match`; a star import; any module or member src/ does not already use; a
  module held in a value; any dunder src/ does not read; `globals`, `locals`, `import_module`, `model_rebuild` and `.parser`;
  `__import__` and `TypeAdapter` outside their reviewed calls; a class inside a function; `type` building a class; and an
  annotation holding a call, an f-string or a binary operator other than `|` and `-`, at any depth of string. It does not
  follow a value: an attribute of an object a listed member returns is not read, the reviewed `TypeAdapter` call is frozen but
  the value it is handed is its caller's, an annotation computing text in any other form is not refused, and neither is a
  listed member that evaluates text in a form not named here. The census refuses by spelling, so it
  binds where it names a form and no further (`enum.bltns.getattr` and `dataclasses.inspect.getmembers` passed it).
- **The authorizer and the teardown check are test-time protections.** Neither is in src/, and a defect reaching production
  meets neither: in a shipped store nothing denies such a write. They stand behind N4f in the suite only, and a value forged
  at run time beyond what the source writes is theirs there, as the verdict allows. The unbound routes through
  `MembershipResolver` are in the matrix, all refused statically. U1 to U6 and X5 raise before any SQL; U7 to U9, which go
  round the rename, reach the authorizer at run time.
- **`os.system` and `os.popen`** are refused as spelled. A second process is not this connection. Neither was run.
- The named limits round 5's README stated (`blobopen`, `pragma_*` table functions, the two migration modules' head-rule
  scope, rebinding inside one interpreter) are unchanged.

## 2. The obligations, mapped

`collected/obligation-map.md` maps each obligation the round-5 verdict states, and each line of its closure table, to
its code, its cells and the rows of the implementation mutation table. It is generated by `collected/mk_map48r6.py`
from the banked round-5 verdict. Each sentence is pulled by an anchor that occurs once in the verdict, never retyped.
The stage checks the map against `tree/` (13 obligations, 44 of the table's 44 rows placed, no defect).

| the verdict asks | where the evidence is |
|---|---|
| **R5-01:** resolve the receiver, or restrict the exemption and refuse the rest; the same for held references | `src/veracium/scope_read.py`; `::test_each_receiver_form_has_its_stated_static_and_runtime_outcome`, `::test_the_gate_refuses_each_form_outside_the_store_for_its_reason` |
| the module-import alias and its held sibling in the permanent matrix, with the named-receiver refusal and the method and read controls | `R6_RECEIVER` (30 forms); `collected/receiver-forms.md` |
| preserve the immediate-caller authorizer and teardown protections | unchanged; `::test_the_tripwire_holds_a_write_to_the_frame_that_ran_it`, and each matrix row's runtime column |
| **R5-02:** a guaranteed mismatch or an execution-free preparation; a case with exactly `_OVERBIND` parameters; scratch unchanged; failure stays unresolved | `::test_a_statement_that_binds_exactly_is_compiled_and_not_run`, `::test_classifying_every_sql_literal_in_src_leaves_the_scratch_unchanged`, `::test_a_string_sqlite_refuses_bare_stays_unresolved`, `::test_the_superseded_preparations_are_what_these_cells_catch` |
| the verdict's class beyond its plant | `R6_IMPORT`; `::test_each_import_form_has_its_stated_static_and_runtime_outcome`; `::test_a_class_pattern_inside_the_store_is_refused`; `::test_a_star_import_is_refused` |
| a compact manifest of imported SQL wrappers, their receiver forms and governing checks | `collected/receiver-forms.md`, generated by `collected/mk_receiver48.py` |
| a machine-readable runtime-limits record | `collected/runtime-limits.json` |

**The legitimate-method control** the verdict names has no subject after the rename: `self._membership_rows` is not a
derived name, and the honest tree covers its two calls. **The read control changes outcome:** a read through a module
spelled `self` is now refused statically, which the verdict allows for an unresolved receiver. Its runtime is unchanged.
A literal read through a named module is the accepted read control.

**The implementation mutation table** (`tree/specs/evidence/0048/implementation/mutation-table.json`, run by
`tree/specs/evidence/0048/implementation_mutants.py` on the shared protocol, `specs/evidence/mutation_protocol.py`):
44 rows, 44 KILLED (by assertion or a missing expected refusal), every honest probe passing, 5 controls good. The stage ran `--check` at the pin on a git-less export (`collected/mutation-table-0048-check.txt`) and renders
the table as `collected/mutation-table-0048.md`. The gate's own forms are not table rows: they are planted on the source
text by the gate's cells. **This round's gate rules are mutated separately** (`collected/gate-mutants.txt`, by
`collected/gate_mutants_r6.py`): each rule reverted on a copy of the test file, killed by assertion in its named cells
(gate mutants: 62 cells: 85 not killed: 0).

## 3. The reviewer's witnesses, and the artifacts the verdict asked for

- **The receiver matrix:** `collected/receiver-forms.md`, 30 forms, each row asserted by the permanent cell.
  Static and runtime stay apart, and a runtime refusal is not offered as the static claim.
- **The classifier's differential:** `collected/classifier-differential.txt` compares the bare prepare with the new
  prefix over every string constant in `src/`, the three 0048 test files and the contract harness, plus planted `QUERY
  PLAN` strings (strings 8704 prepared by old 297 differences 28). Every difference is a new refusal of a comment-only, empty or `EXPLAIN`-led string, and the
  authorizer's actions and parameter counts are otherwise identical. "Identical" is a statement about this corpus.
  `collected/classifier-differential-plain-explain.txt` is its control: plain `EXPLAIN` flips the `QUERY PLAN` strings.
- **The two witnesses** (`collected/reviewer-probes/`, `RESULTS.md` first): 2 reviewer witnesses: originals reproduce the reviewer's records at round 5's pin and no longer confirm at this pin; adapted copies pass at this pin (the receiver plant refused by the complete gate, its runtime unchanged; the exact-count statement compiled and not run). Each is run four ways: the
  reviewer's ORIGINAL at round 5's pin, which must reproduce the reviewer's record; the original at this pin, which must
  no longer confirm; an ADAPTED copy at this pin; and the adaptation's diff, every change marked `# R6`.
  - The originals exit non-zero here for different reasons, stated so neither is read as a crash: the receiver probe on an
    AssertionError, because a supplied cell now refuses the plant; the classifier probe on `no such table`, because it
    reads the table it expects the classifier to have made.
  - The adaptation pins the plant's `replace` to the confidence field, with the word split as the reviewer split `json`.
    The original's `'0.8'` also matches inside a timestamp, which fails the guarded teardown on about 1% of seeds (the
    second seat measured 13 in 1,200 planted seeds, 0 in 1,200 honest).
- **The full offline JUnit**, beside its transcript: `collected/offline-results.xml`, the same run as
  `collected/offline-run-raw.txt` (8064 passed, 59 skipped, 14 warnings in 6184.18s (1:43:04)), with every skip named in `collected/offline-skips.txt`.
- **Retrieval references:** `collected/retrieval-references.txt` names every predecessor package and reviewer archive by
  sha256, and says which ones the authors keep (§5).
- **Byte stability.** The current-row traces and the R2-02 old/new table, regenerated at this pin by
  `collected/trace48.py`, are byte-identical to the ones round 5 shipped (34 runs; two runs byte-identical). The suite at the pin:
  `collected/COLLECTED.txt`, a fresh clone (8111 passed, 12 skipped, 15 warnings in 6394.93s (1:46:34)).
- **The N4 results:** `collected/n4-results.md`, generated from the capture's junit, 500 cells, 500 passed, 0 skipped, none failed, every collected cell present. The cell list is compared
  both ways with what pytest collects from the three 0048 test files at the pin.
- **The binding-layout matrix:** `collected/binding-layout.md`, regenerated from the tree, unchanged in form.

## 4. Found before dispatch, and fixed

The second seat read the plan before any fix. Each finding below changed the plan, and each is now a cell or a stated row.

- **A listed method reached unbound.** The first plan kept a closed list of `self._rows` sites. An existing method
  called unbound with a module in place of `self` passed the gate and all six of the reviewer's cells, and committed 1.8
  over a journal of 0.8. That is the verdict's own shape, so the plan changed: the collision goes, and the list with it.
  Six forms join the matrix, with the three ways round the rename the second seat tried.
- **The plain `EXPLAIN` prefix** made a new statement grammatical, as §1 says.
- **A literal `getattr` of a derived name** passed the gate, and only the tripwire inventory saw it.
- **The ladder's table statements,** declared in §1. SA10's refusal rests on dev's own run, which also corrected a base
  range: it covers v2 to v15, and v1 never runs the table.
- **Gate mutants that survived.** Reverting each new rule showed one check was redundant, so it was deleted, and two
  rules hid behind each other, so each gained a cell that isolates it.

The second seat's executable pass, after the fix commit, then found what the read could not. Its record held the seal, and the
owner ruled the scope. Each item below is now a cell, a mutant or a stated limit.

- **A class pattern** read `execute` with no attribute node. By the reviewer's own assertions the keyword form committed 1.8
  over a journal of 0.8 with no test guard. The positional forms were denied under the test-time authorizer and not run
  without it. The forms inside `sqlite.py` and from a new module passed the gate and the census and were not run. `match`
  is refused.
- **Library routes from text:** `string.Formatter`, `timeit`, `cProfile`, `xmlrpc`, `logging.config`, `typing.get_type_hints`,
  `importlib.metadata.EntryPoint`, `importlib.import_module`. Each is refused by the module or member tables.
- **The first closure was too narrow.** Measured before building it, a list of import statements left the same routes one
  attribute past a listed module, and a quoted pydantic annotation wrote too. The owner widened the ruling to members.
- **An earlier draft said a "runtime guard" stood behind the limit.** It is test-time only (§1). The second seat found this.
- **`pathlib.Path.parser` is `posixpath`**, reached through a class, where the member walk stops. Refused by name, and the audit
  cell looks for the next one.
- **A relative star import** bound names no rule saw. Found by the second seat's read of the build.
- **A string inside a quoted annotation** was left open by the second seat's read. Tested, it reached the authorizer, so
  the rule recurses.
- **The build's own defects.** `veracium/store` has no `__init__.py`, so a relative import of it bound nothing until a matrix row
  failed. The recursion then refused honest `Literal` values, which parse as subtraction; a mutant run's honest control caught that
  before commit, after a narrower run had not.
- **A memo key** in the gate omitted two tables a cell patches. The suite and CI passed in their order, and offline and the capture
  each failed one cell, in fixed order, at the first pin of this round. No sealed package carried that pin.
- **Plants that hid their rule.** Three gate mutants survived because another rule refused the plant first. The plants
  now fail only the rule they test.

**Not changed in this round, and why:**

- An edge row's denormalised columns are read from the mutable edge separately from the captured json. No verdict has
  promoted this; it stays queued.
- The redaction's episode branch writes `episodes.json`. The review's scope keeps episode persistence outside it.

## 5. Lineage

- **Five predecessors, all dispatched:** round 1 (design, returned), round 2 (design ACCEPTED), and rounds 3, 4 and 5
  (implementation, returned). `prior-rounds/` carries the five banked verdicts and the five sidecars. Rounds 1 and 2's
  verdicts arrived as files, and the stage checks each body's digest against its banking header. Rounds 3, 4 and 5's
  arrived as archives, and the shipped checker (`collected/check_verdict_tarball.py`) confirms each body against its
  archive.
- **What the authors keep** (`collected/retrieval-references.txt`, every digest read by the stage from its source):
  - rounds 3, 4 and 5's packages and the reviewer's archives for those rounds are kept and match their digests;
  - round 1's and round 2's packages, and the reviewer's round-2 evidence archive, are not. This has been disclosed
    since round 3, and the round-3 verdict records that the reviewer recovered them independently;
  - the stage repeats a search by digest over every archive under the coordination tree's inbox, outbox and pending/
    (316 archives hashed, none of the three digests).
- **No seal of this round has been discarded.**

Five commits follow round 5's pin. ed4d98c9 and 05853bde are the amendment. The other three are the regeneration runs a
`src/` or `tests/` change requires, and they are not asked about here. All five carry the trailer, so all five are in
`collected/0048-implementation-commits.txt`.

## 6. Contents

- `0048-decay-never-raises-confidence-SPEC-v4.2.md`
- `PIN.txt`
- `README-0048-round6-bundle.md`
- `collected/0048-implementation-commits.txt`
- `collected/0048-implementation.patch`
- `collected/0048-path-commits.patch`
- `collected/0048-path-commits.txt`
- `collected/COLLECTED.txt`
- `collected/binding-layout.md`
- `collected/check_verdict_tarball.py`
- `collected/classifier-differential-plain-explain.txt`
- `collected/classifier-differential.txt`
- `collected/classifier_differential.py`
- `collected/current-row-traces.md`
- `collected/gate-mutants.txt`
- `collected/gate_mutants_r6.py`
- `collected/mk_layout48.py`
- `collected/mk_limits48.py`
- `collected/mk_map48r6.py`
- `collected/mk_receiver48.py`
- `collected/mutation-table-0048-check.txt`
- `collected/mutation-table-0048.md`
- `collected/n4-results.md`
- `collected/n4_results.py`
- `collected/obligation-map.md`
- `collected/offline-results.xml`
- `collected/offline-run-raw.txt`
- `collected/offline-skips.txt`
- `collected/r2-02-old-new.md`
- `collected/receiver-forms.md`
- `collected/requirements-resolved.txt`
- `collected/retrieval-references.txt`
- `collected/reviewer-probes/RESULTS.md`
- `collected/reviewer-probes/adapted/reviewer_classifier_limit_r6.py`
- `collected/reviewer-probes/adapted/reviewer_self_receiver_r6.py`
- `collected/reviewer-probes/at-round5-pin/reviewer-classifier-limit.json`
- `collected/reviewer-probes/at-round5-pin/reviewer-self-receiver-summary.json`
- `collected/reviewer-probes/at-this-pin/originals.txt`
- `collected/reviewer-probes/at-this-pin/reviewer-classifier-limit-r6.json`
- `collected/reviewer-probes/at-this-pin/reviewer-self-receiver-r6-summary.json`
- `collected/reviewer-probes/diffs/reviewer_classifier_limit.diff`
- `collected/reviewer-probes/diffs/reviewer_self_receiver.diff`
- `collected/reviewer-probes/original/reviewer_classifier_limit.py`
- `collected/reviewer-probes/original/reviewer_self_receiver.py`
- `collected/runtime-limits.json`
- `collected/sa10-ladder-plant.txt`
- `collected/sa10_all_bases.py`
- `collected/spec-diffs/0048-decay-never-raises-confidence.fold.diff`
- `collected/spec-diffs/0048-decay-never-raises-confidence.since-fold.diff`
- `collected/suite-results.xml`
- `collected/suite-run-raw.txt`
- `collected/trace48.py`
- `collected/tree_hash_witness.sh`
- `prior-rounds/0048-round1-review-package.tar.gz.sha256`
- `prior-rounds/0048-round1-verdict-verbatim.md`
- `prior-rounds/0048-round2-review-package.tar.gz.sha256`
- `prior-rounds/0048-round2-verdict-verbatim.md`
- `prior-rounds/0048-round3-implementation-review-package.tar.gz.sha256`
- `prior-rounds/0048-round3-verdict-verbatim.md`
- `prior-rounds/0048-round4-implementation-review-package.tar.gz.sha256`
- `prior-rounds/0048-round4-verdict-verbatim.md`
- `prior-rounds/0048-round5-implementation-review-package.tar.gz.sha256`
- `prior-rounds/0048-round5-verdict-verbatim.md`
- `tree/` — the repository at the pin (`git archive`), witnessed by `collected/tree_hash_witness.sh`
- `SHA256SUMS` — every other member's digest
