<!-- TERMINAL RECORD — the round-16 review bundle README of spec 0031, byte-copied
UNMODIFIED from the ACCEPTED package (sha256 1aabb39e517ceef15f0bbaa8f0617aab2ae321098d8ec6c3619ffe5f955eebd3
@ c0affa03fd1d5371256816fd688d0c7a428b0fbe, CI 33826218063) on 2026-09-04, the day the
reviewer accepted 0031 v21 and froze its invariant surface. It is the one carrier where the
sixteen per-round dispositions and the consolidated errors ledgers live together; the version
cells carry lineage, not the reviewer's dispositions or the process's disclosed failures. The
package remains the archive; this copy is the record. Below this comment the bytes equal the
packaged README — verifiable forever against the archived package. -->

# 0031 the agent-facing trust surface — round-16 external review bundle

Assembled 2026-09-04 by dev; authored by research with dev's mechanism
designs. ONE round-15 finding — **the fifteenth rung, your attack point
#3 taken for the third consecutive round** — folded; round-14's closure
credited in all seven points on your side, the table's consumption
invariant "reasonable for its listed entries".

**Canonical artifact:** `specs/0031-agent-facing-trust-surface.md` at the
pinned commit (`PIN.txt` beside this README — full values, written after
each existed). Outer `.sha256` sidecar beside this archive.

## The finding — disposition

| finding | disposition |
|---|---|
| **1** the dotted-access boundary is syntactic rather than enforceable | Measured before anything was designed: **4,885 dotted attribute accesses in `src/veracium`** — a per-site allowance table for dotted access would be hygiene theatre, not evidence. So the closure takes your second and fourth options TOGETHER. **ONE shared classifier decides both forms** (`_classify_attribute`, five classes): `refused` — a `FRAME_ATTRS` name on any receiver; `module-protected` — the receiver is `sqlite3`/`_sqlite3`/an alias, the positive-surface rules govern (a `getattr` on a protected module refuses: a string-named lookup is never the blessed direct call); `module-machinery` — `sys`/`importlib`/a machinery module, the registry rules govern; `module-plain` — an UNPROTECTED module-valued name (every import tracked, propagated through assignments), an ordinary attribute of an ordinary module, allowed under both forms; **`dataflow` — the receiver cannot be established as module-valued: OBJECT DATAFLOW, outside the completeness claim for BOTH forms**, stated in your words — the census does not know the receiver's runtime type under either syntax, and dotted syntax proves nothing about it. **The one mechanically justified difference, and only it**: a `getattr` name can be NON-LITERAL, which dotted syntax cannot express — non-literal refuses (round 13); a permanent test asserts this is the sole asymmetry. **The one dunder rule for both forms is `FRAME_ATTRS` MEMBERSHIP, never shape**: our first cut refused every dunder by shape and the src sweep exposed 96 dotted dunders that are ordinary data (`__name__` ×69, `__cause__`, `__init__`, `__new__`, …); `FRAME_ATTRS` gains the three LOOKUP dunders (`__getattribute__`, `__getattr__`, `__import__`), and `__getitem__` on a mapping is already an escape from a keyed lookup. **`GETATTR_ALLOWANCES` survives as what it honestly was — the INVENTORY of declared-uncertainty sites with their consumption, hygiene swept both directions — not a classification**: the census no longer refuses an untabled literal `getattr` (that refusal was the syntactic asymmetry — its dotted twin never refused), the sweep fails an untabled site with "inventory it", and the round-14 declared-uncertainty sentence is WITHDRAWN. **Your paired tests, exactly**: ten (receiver, attribute) pairs through both forms across all five classes — including a hostile call receiver (both dataflow) and a module rebound through assignment (both module-plain) — receive identical classes. **Your feedback executable — the shared semantic inventory**: `attribute_census` classifies every access in a source under both forms, and the src sweep reports the counts — **dotted dataflow 4,583 (the 96 ordinary-data dunders INSIDE it; there is no sixth bucket), dotted module-plain 248, dotted module-machinery 19, dotted module-protected 35, `getattr` dataflow 21 (the table's total, exactly); zero refused under either form; every one of the 4,906 accesses in exactly one class** — and the partition is now asserted by EQUALITY against one constants row (`SRC_ATTRIBUTE_PARTITION`) the spec quotes, with a second test binding the spec's figures to that row. Live plant of `getattr(host, "connection")` beside `host.connection` under `src/veracium`: the census is CLEAN by the one rule (both dataflow) and the inventory sweep fails on the untabled probe — the hygiene gate doing precisely its job. Matrix 165 → 178 |

## The claim, narrowed in your words

The completeness claim is now as wide as the module-governed classes
and no wider: attribute access on a receiver the census cannot
establish as module-valued is object dataflow, outside the census under
BOTH syntactic forms. The census never says that dotted syntax proves a
known type. The shared inventory NAMES the size of what is excluded —
4,583 dotted and 21 `getattr` accesses in the shipped source — so the
boundary is measured, not gestured at, and asserted by equality. This is the round where the
ladder's honest-limit precondition (round 9: a stated limit must be
consistent with the claim) is satisfied by narrowing the claim rather
than by closing the limit — the door you opened yourself.

## Rungs thirteen through fifteen, one motion

Round 13 took the name off the RECEIVER; round 14 took it off the
ATTRIBUTE; **round 15 took the SYNTAX off the rule.** What is left is
one classifier and an honest boundary around what static analysis of a
single file cannot see. All three rungs came from the same attack
point, offered three times and taken three times — which is the
offering posture working exactly as designed, and why this round's
third attack point offers the boundary itself.

## Errors made and caught at staging (this round's ledger)

**A FIRST SEAL OF THIS PACKAGE WAS DISCARDED, refused pre-dispatch by
research's probe re-run from its sealed bytes.** Two defects: (1) the
sealed spec still carried round 14's blanket sentence — a literal
`getattr` on a module-valued receiver "refuses regardless of the
inventory, even for an unprotected module" — while the sealed census
classified exactly that access `module-plain` and allowed it (the
census was right: refusing the `getattr` form alone was round 15's own
syntactic asymmetry; the spec sentence had survived the classifier that
superseded it). (2) The measured figure was STALE: 4,487 was taken
before the membership rule moved the 96 data-dunders INTO dataflow; the
true figure is 4,583, and it rode in the spec, this README, and the
version cell while the test certified only "> 1000" — an ordinary
program, not the claim we print. Both corrected: the spec's escape
rule is rewritten as provenance-routes-to-class with the supersession
stated; the partition is now GENERATED from the measurement into one
constants row, asserted by EQUALITY in the sweep, and a second test
binds every figure the spec quotes to that row. The discarded seal
never left the outbox's staging. The read-then-write class, on a
measurement: a narrated number nobody asserts goes stale silently.

Two more, both ours, from the fold itself. (1) The first cut of the shared classifier refused every
dunder by SHAPE; the source-wide inventory sweep — written to prove the
one rule — refused 96 ordinary-data dunders in src on its first run and
so caught its own author: the rule became membership in the enumerated
set, the enumeration gained the lookup dunders, and the shape rule is
gone from both forms. (2) Research's round-15 harness matcher (disclosed
last round, harness-side only): a `startswith` on path-prefixed keys
read five refusals as clean; caught by probe-defect-before-absence,
fixed, and the harness now runs a guaranteed-positive MATCHER CONTROL
before any negative is trusted — the rule is in our pre-seal runbook.

## Contents

| path | what it is |
|---|---|
| `0031-agent-facing-trust-surface-SPEC-v21.md` | the spec — **START HERE** (the five-class rule; the narrowed claim; the inventory re-described) |
| `PIN.txt` | commit + CI run id + suite line, full values |
| `tree/` | the COMPLETE source/test tree at the pin — `tests/test_0031_proposal_ddl.py` at 178 cells + `specs/evidence/0031/connection_census.py` with `attribute_census`, runnable offline |
| `corpus/` | the acceptance corpus, unchanged from round 9 |
| `collected/` | the suite run at the pin, standing discipline |
| `prior-rounds/` | all fifteen verdicts VERBATIM + all prior bundle READMEs + the N/A receipt |
| `SHA256SUMS` | binds every file above, both directions counted (nested corpus manifest included) |

## Where the authors ask you to attack

1. **The sixteenth rung, standing invitation**: a capability-discovery
   route the thirteen-form enumeration misses — or adjudicate the
   inventory closed with the conservative floor as its terminal answer.
2. **The five classes**: find an attribute access that belongs to none
   of them, or one that the classifier places wrongly under either
   form — or certify the partition.
3. **The narrowed claim itself**: object dataflow is outside the census
   under both forms, its size named. Say whether a static census of one
   file can honestly claim anything narrower than this about receivers
   it cannot type — or whether this boundary is the terminal shape of
   the honest-limit precondition you minted at round 9.
