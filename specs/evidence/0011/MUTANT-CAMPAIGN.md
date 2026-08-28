# 0011 evidence artifacts — dev's own mutant campaign (2026-08-28, extended the same day)

**Run before dispatching round 6, at Quentin's direction, because rounds 4–5
were the reviewer mutation-testing these artifacts at one class per round —
the same ladder that cost the A1 line seven consecutive seal cycles. The
standing rule this applies (checklist item 10): when a round's findings are
all in the evidence layer, exhaust the class yourself before resealing.
Applied late rather than never.**

## Honest headline

Nine mutants were designed against the oracle and the fold checker. On the
first run, **six of nine were MISSED** — and one of the three catches (M1)
was luck: a standing test happens to hardcode a source string, not a check
that understands the domain. Every miss was fixed, every fix carries a
standing test, and the campaign was re-run to 9/9 before anything shipped.

## The mutants

| id | attack | first run | after fixes | fix |
|---|---|---|---|---|
| M1 | narrow `SOURCES` — emitter and expected key set share the constants, so both shrink together | caught (by luck) | CAUGHT | hand-picked dimensions pinned as literals with required members, independent of the constants |
| M2 | narrow `ORIGINS` — same class | **MISSED** | CAUGHT | same pins |
| M3 | drop the OTHER subject — every refusal cell vanishes | caught | CAUGHT | subject-class coverage pinned via the shipped predicate |
| M4 | expected key set built FROM the emitted keys (tautology) | caught | CAUGHT | the standing truncation/duplication tests judge injected streams |
| M5 | fabricate the import cells inside `problems()` — the adapter never runs, the value checks pass on values nobody measured | **MISSED** | CAUGHT | the R14-1 sentinel: a standing test replaces `import_flattened_cells` and requires `problems()` to REACH it |
| F1 | helper definition INDENTED in a fence — the `^`-anchored regex never collects it | **MISSED** | CAUGHT | definitions may be indented |
| F2 | PARENLESS binding (`srcflag := …`) read as a bare name — neither collected nor followed | **MISSED** | CAUGHT | parenless definitions collected; any known name referenced as a word is followed |
| F3 | helper hidden in an INFO-STRING fence (```` ```text ````) — the fence regex required a bare newline | **MISSED** | CAUGHT | any info string matches. This is the A1 ladder's info-string rung, reintroduced by dev and found by dev |
| F4 | an EXTRA contradicting row beside the generated table — presence-of-every-generated-row is not equality | **MISSED** | CAUGHT | the spec's table block is extracted and must EQUAL the generated rows as a multiset |

The four reviewer attacks from rounds 4–5 (emitted-cell variance, shadowed
helper, duplicate-for-missing, row-unbound withdrawal) were already standing
tests before this campaign and remained green throughout.

## What this bought, stated plainly

Six defects that would otherwise have been six more review rounds — rounds
4 and 5 ran at one evidence-class per round, so the projection is not
hypothetical. The pattern across all six misses is the one the reviewer has
been teaching since round 4: **a check that shares structure with its
subject (constants, regexes, call sites) certifies the shared structure,
not the subject.** Every fix breaks the sharing: literal pins, a sentinel
that must be reached, grammar the attacker does not control, equality
instead of containment.

Reproduce: the mutants are scripted plants over the shipped artifacts; each
fix's standing test is in `tests/test_0011_policy_matrix.py` and the fold
checker's own row-scoped checks.


## The extension (same day): the two artifacts the first pass did not cover

The first campaign was scoped to the oracle and the fold checker. The
census — **the most-hit artifact on the line** (EVIDENCE-R2-1 and
EVIDENCE-R3-1 were both census findings, each a defect in the previous
round's census fix) — and the contention checker went un-campaigned. The
extension ran six more mutants. **Zero of six were caught**, and both
evidence-directory checkers turned out to sit entirely OUTSIDE P1's glob,
so no mutation matrix had ever been demanded of them: the gate covered the
artifacts nobody was attacking and missed the ones under attack.

| id | attack | first run | after fixes | fix |
|---|---|---|---|---|
| C1 | inflate the recorded-only whole-corpus count in the aggregate | **MISSED** | CAUGHT | §3b's figure table is bound DATA-TO-DATA to the shipped aggregate in the fold checker — a fabricated aggregate now disagrees with the spec beside it |
| C2 | gut the candidate table, keeping the SELF total | **MISSED** | CAUGHT | same binding: candidate rows and distinct-string count are bound figures |
| C3 | an UNMASKED name-shaped key accepted into the aggregate | **MISSED** | CAUGHT | the emit-time mask pattern also REFUSES at validate |
| C4 | drift a §3b figure in the SPEC (72,253 → 72,254) | **MISSED** | CAUGHT | the same binding, from the other side — the PAIR-R4-1 drift class, now mechanical |
| K1 | delete the contention checker's positive-control cell | **MISSED** | CAUGHT | the cells are a REGISTRY; run_cells() returns what ran, and a missing cell is a mismatch |
| K2 | neuter a cell's assertion with `if False and …` — the cell runs, reachability checks pass | **MISSED**, twice: it survived the registry restructure too | CAUGHT | reachability is not FAILABILITY: the standing test feeds each cell a world in which it must complain, by lying to it through the shipped surface it reads |

K2 deserves its own line: it was missed, fixed with a registry + sentinel,
and **missed again** — the sentinel proves a cell is reached, not that its
assertion is alive. The second fix is the general one: every cell is
proven able to FAIL.

## Process consequence

P1's domain is now RECURSIVE (`rglob`) over `specs/`, with the three
pre-rule artifacts of accepted lines grandfathered by name. Both 0011
checkers carry `# Mutation-Matrix:` pointers at the tests that attack
them.

Final state: **15 mutants, 15 caught** (4 reviewer attacks standing + 9
first-pass + 6 extension, with K2 counted once); pristine artifacts clean.


## Round-6 correction: this record was prose, and its own claims failed audit

PROCESS-R6-1 found this document claiming "every fix carries a standing
test" while F1–F4, C1–C4 and the row-unbound withdrawal had NO planted
tests — they were verified by ad-hoc shell plants that died with the
session. Neutering the entire `check_census_figures()` binding left every
test green. And the totals were hand arithmetic that did not add up: 4
reviewer + 9 first-pass + 6 extension is 19, and the record said 15.

The record is superseded on both counts by the EXECUTABLE registry:

* **`mutant_registry.py`** binds every campaign id to its artifact, its
  mutation, and the pytest node that plants it, EXECUTES all of them in
  one pytest invocation, and writes **`mutant_results.json`** with the
  totals DERIVED from what ran. No hand counting remains in the loop.
* Standing tests now exist for every id — the previously-untested nine
  live in `tests/test_0011_mutant_registry.py`, planting their attacks in
  memory (attacked spec text, fabricated aggregates, patched constants).
* The current derived totals: **21 entries — 6 reviewer-found, 15
  dev-found** — over 18 distinct nodes. The generated record, not this
  sentence, is authoritative; if they ever disagree, this sentence is the
  one that is wrong.

This is the same lesson as every other finding in this file, applied to
the file itself: a narrative ABOUT tests is not tests, and totals typed by
hand drift exactly like any other hand-carried figure.


## Round-7 correction: the ledger itself was not independently checkable

PROCESS-R7-1: the first registry derived success from the DISTINCT PYTEST
NODES, not from the mutants — a fictitious entry riding an already-listed
node inflated the total with exit 0, artifact paths were never validated,
and `mutant_results.json` was write-only: overwritten by every run, read
by nothing. Corrected:

* every standing test, after its assertions succeed, REPORTS the id(s) it
  killed via `record_kill()`; the runner requires reported kills to equal
  the declared ids exactly — one-to-one, unknowns and doubles refused;
* artifact paths are validated to exist and duplicate ids refused;
* the default invocation is a non-mutating **`--check`** that recomputes
  the whole record and requires equality with the shipped one; `--write`
  is seal-time only;
* the bogus-entry, ghost-artifact, phantom-kill, double-kill and
  corrupted-record attacks are standing regressions.
