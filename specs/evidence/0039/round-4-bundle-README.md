<!-- TERMINAL RECORD — the round-4 review bundle README of spec 0039, byte-copied
UNMODIFIED from the ACCEPTED package (sha256 988298782a92f0f37bb81337c226ba2afbc5c725f904b2bec72fee6fc7b3a707
@ d2ef676f470fdcfa497dc45c36bcbb50f5560863, CI 34426512022) on 2026-09-10, the day the
reviewer accepted 0039 v12. It is the one carrier where the round-3 dispositions, the
line's history stated up front (three returned verdicts, one refused assembly, the seal
blind spot, the withdrawn clearance), the clone-versus-archive reconciliation and the
consolidated errors ledger live together with the path from rounds 1–3 (each earlier
README rides in its successor's prior-rounds/); the version cells carry lineage, not the
reviewer's dispositions or the process's disclosed failures. The package remains the
archive; this copy is the record. Below this comment the bytes equal the packaged
README — verifiable forever against the archived package: strip the lines above the
first '# ' heading and compare. -->

# 0039 degradation visibility — round-4 external review bundle

Assembled 2026-09-10 by dev. Fourth external round for spec 0039 (a draft on the ordinary
path). Round 3 (package `6f050414…`, pin `3a470ee`, spec v11) returned for amendment
with all three round-2 findings closed and the core design called mature; two mechanical
defects and one minor one remained, each disposed below and each first reproduced at
the pinned code before a line of the spec moved. All three prior verdicts ride in
`prior-rounds/` verbatim.

**This line's history, stated up front rather than left to be found:** three verdicts
returned for amendment, each closing the previous round's findings in substance; one
refused package assembly (round 2's first, `72a199f3…`, refused by the second seat on a
declaration error and disclosed in round 2); a seal-protocol blind spot found after
round 1 and fixed before round 2 (both seats' seal checks had gone green over a failing
test); and, in round 3, one seat's seal leg killed repeatedly inside the whole-suite
assertion by something in its execution environment — first diagnosed as memory
contention and asked to be recorded as a protocol constraint, then MEASURED (the suite
uses about 100 MB against 11 GB free) and retracted before it reached any record; then a
clearance was declared on a probe run and withdrawn when the probe turned out to have run
a different command from the check's (without `PYTHONPATH=src`, so against the working
tree's product rather than the archive's). At this package's seal the exact command's
outcome in that session was still unknown, and its leg is recorded as it stands, not as
complete. All of
it is in `prior-rounds/` and summarized in the errors ledger; none of it is hidden by
being history.

**Canonical artifact:** `specs/0039-degradation-visibility.md` at the pinned commit (see
`PIN.txt` — commit, CI run id, and the suite line as printed; repo
`github.com/veracium-ai/Veracium`, public). The copy here
(`0039-degradation-visibility-SPEC-v12.md`) is byte-identical to `tree/specs/` at seal; on
any doubt the repo wins.

## Disposition of round 3

| # | finding (the reviewer's words, abridged) | disposition | where |
|---|---|---|---|
| R3-1 | the invariant table is structurally corrupted: the insertion of V-RECORD-ORDER-ON-ERROR split V-DEGRADE-RECORDED; add a structural gate | **Reproduced (two cells and six against a four-cell header), repaired to two independent four-column rows, and the gate built.** Every §6 table row in every spec must carry exactly its header's cell count, parsed with escaped pipes and code spans respected — a naive split flagged rows that are correct — with a control planting the exact v11 damage. The parser also found six shorter rows in four ACCEPTED specs' §6 tables; they are recorded as the gate's starting debt, a set that can only shrink, not silently edited here. The cause was a fold script anchored on a row's OPENING, which swallowed the row's tail | §6 (V-DEGRADE-RECORDED, V-RECORD-ORDER-ON-ERROR); `tree/tests/test_spec_gate.py` (two nodes) |
| R3-2 | in an extracted archive the transcript comparisons skip because the tests call the git-history check first | **Separated.** Reproduction always runs — the two transcript tests no longer touch git; the pin binding is its own test per transcript and skips only itself. Proven in a bare `git archive` copy of the tree: 3 passed (both reproductions and the planted-shape control), 3 skipped by name | `tree/tests/test_0039_answer_shapes.py` |
| R3-3 | the fixture pseudocode names `store.conn`, says "primary key" while ordering by rowid, and sets `store._now` though `clock=` exists | **Aligned to the shipped API:** `SqliteStore(":memory:", clock=lambda: FIXED_INSTANT)`; the store's `_conn` seam named as the private seam a test may use; `ORDER BY rowid` declared as the current-schema rule (every shipped table is a rowid table; a WITHOUT ROWID table must be ordered by its declared primary key and the rule updated); column names from the cursor description | §2c-iii, V-CALLBACK-CONTAINED |

## Where the authors ask you to attack

1. **The §6 gate's parser.** It treats a backtick as toggling a code span and `\|` as an
   escaped pipe. A row with an unbalanced backtick, or a pipe inside an inline HTML
   comment, is the input it does not name; the control covers only the two cases it
   lists.
2. **The gate's starting debt.** Six rows in accepted specs are recorded as known short.
   Whether any of them is real damage rather than an intentional collapsed row is a
   question this package records and does not answer.
3. **The separated transcript tests.** Reproduction now runs from archive bytes against
   whatever `veracium` the interpreter resolves; the pin binding that would say WHICH
   product is the part that skips in an archive. In an archive, therefore, a transcript
   that happened to match a different product would pass. §2c-ii's header states the
   pin; the archive cannot verify it.
4. **V-RECORD-ORDER-ON-ERROR's positional assertion, and the matrix's fourteenth row** —
   both carried from round 3, neither answered by the reviewer, both still open.

## The internal rounds between the verdict and this package (2026-09-10)

- **v12 (dev):** the three findings folded, each reproduced first; the gate built and
  measured across every spec before being made a gate; research's read of the fold.

## Errors ledger

- **Dev's v11 fold script split an invariant row** (dev's carrier). It replaced the
  opening of a row to insert a neighbour after it — the anchor-at-a-boundary rule this
  project already carries for Python files, not applied to a Markdown table. The reviewer
  found it; nothing in the tree could have, which is why the gate exists now.
- **The gate's first version had a typed debt set** (dev's): six prefixes retyped by
  hand differed from the parser's derived keys by a character; the set is now derived
  from the parser and frozen, never typed.
- **The gate's first version lacked an import** (dev's): caught by its own control before
  the suite.
- **Research diagnosed a repeated leg kill four times without measuring it once**
  (research's carrier), and asked for a protocol constraint to be recorded; the first
  measurement disproved all four diagnoses and the constraint was retracted before it
  reached any record. The measurement that followed then proved to have measured a
  different thing — a probe without `PYTHONPATH=src`, which imports the working tree's
  product rather than the archive's — and the clearance built on it was withdrawn:
  measuring is not enough if you measure a different thing. What is doing the killing in
  that session's environment is unknown; the seal check was not narrowed to accommodate
  it, and this round's legs ran dev-first with research's recorded as it stood.
- Round 3's package was dispatched by the owner while the second seat's leg was partial
  (sections 1–9 passing on three attempts) and the first seat's leg had not run; the
  banked verdict records that state.
- Earlier rounds' ledgers are carried in `prior-rounds/`.

The lineage means what it says: three predecessors, all dispatched and returned; every
entry above was caught by one of the two seats or by the reviewer, and none reached this
package's bytes unfixed.

## Two suite counts for one tree, reconciled

A reader of `collected/COLLECTED.txt` (a fresh CLONE at the pin) and of a seal check's
whole-suite run from this ARCHIVE will see two different result lines for the same
tree. On round 3's tree they were 2921 passed / 9 skipped (clone) and 2906 passed /
24 skipped (archive), both totalling 2930: the fifteen-test difference is entirely
archive-only skips — the retrospective deadline gate, the transcript pin bindings, and
the spec-gate nodes that read git history — each skipping by name with a registered
reason rather than failing, because a `git archive` tree has no history. Round 4's own
archive count is measured on the seal legs and stated in the seal event, not carried
from round 3; the arithmetic is expected to hold in the same shape.

## Claimed costs

None are claimed as measured. The derived log-window figures §7 asks for are owed at
implementation, and the spec says so.

## Contents

- `0039-degradation-visibility-SPEC-v12.md` — the spec, byte-identical to `tree/specs/`
- `PIN.txt` — commit, CI run id, suite line, and every disclosed identifier (rounds 1–3 as predecessors; round 2's refused first assembly as its discarded seal)
- `collected/COLLECTED.txt`, `collected/suite-run-raw.txt` — the fresh-clone capture at the pin, profile `[dev,mcp]`, raw transcript from the same run
- `prior-rounds/` — rounds 1–3's READMEs and verdicts, verbatim
- `tree/` — `git archive` at the pin (tracked files only, asserted both directions)
- `SHA256SUMS` — every file above, excluding itself
