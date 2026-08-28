# 0011 evidence artifacts — dev's own mutant campaign (2026-08-28)

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
