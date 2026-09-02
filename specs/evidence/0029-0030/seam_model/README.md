# The runnable joint seam model (0029 ↔ 0030)

Built at the round-3 fold, on the reviewer's request and on the round's own
lesson: three of six round-3 findings were places the specs DERIVED from
reading code what only EXECUTION shows (the tuple-keyed retire population;
the @property trust flags no payload carries; the deferred-transaction
allocation race). This model executes those constructions so the next such
defect fails a test before it reaches a reviewer.

## Rule zero (both seats, non-negotiable)

**Every assertion ships with a negative control that makes it fail, in the
same file — and the controls are themselves asserted**, so a control that
stops discriminating is a test failure, not a silent green. A check that
cannot fail is worse than no check: it manufactures confidence. (Earned
three times in one day: an assertion over an empty list, an exclusion probe
on an absent string, and a clean scan with no seeded positive.)

## Layout

| file | seat | executes |
|---|---|---|
| `allocation_schedule.py` | dev | F4: `BEGIN IMMEDIATE` before any allocation read (positive) + the DEFERRED reproduction (negative control, the reviewer's own failure kept failing forever) |
| `restriction_derivation.py` | dev | F1/X-1: `("edge", edge_id) in retire` against the REAL `sweep` through the REAL `project_store` (share-the-projection, executable); the bare-id and affected-membership mistakes kept as controls; the CurrentState one-consistent-read shape + token-moves control |
| `raw_adapter.py` | research | F3 IN FULL: text → validated + DERIVED trust flags (two-disjunct `quarantined` per schema.py:482, executed not recalled); payloads from a REAL `Edge.model_dump_json()`, never hand-written; and the adapter DRIVES THE REAL `ScopeView` end-to-end (real store, real policy, real `Identity`) — the scope-feeding fields per `MembershipResolver._record_shape` (scope_read.py:170-176, the authority; the verdict's field list was missing `disclosure`), `author_of_evidence` as the REAL enum (`.value` is accessed — a string stand-in passes fake tests and fails live), incomplete provenance a REFUSAL because those fields FEED THE SCOPE DECISION (the defaulting variant silently manufactures a scope decision from an author that was never there — the fabricated-authority control) |
| `current_state_carrier.py` | research | F2/F4/C-2/C-4: six-leg parse-independent binding (round-8 F1: the view and the scope cell are a PAIR — present together, absent together, one principal when present); absence-never-grants. This row said "five-leg" for two rounds after leg six landed — the round-8 verdict's stale-carrier list caught it |
| `tests/test_seam_model_0029_0030.py` | research (dev-adopted) | driver for the research halves |
| `tests/test_seam_model_0029_0030_store.py` | dev | driver for the dev halves, against a real `SqliteStore` |

Adoption discipline: research's halves were mutation-tested on their machine
(FIVE deliberate breaks across two increments, failures observed, restored)
and the two trust-defect mutations — 1 (one-disjunct `quarantined`) and 5
(unknown author defaulted to USER, the fabricated-authority path) — were
re-flipped and re-proven on the dev machine at adoption, each restored
byte-identical (`cmp`) and re-greened.

## The strict-decoder episode (first full-suite run)

The shipped 0026 relay-lexicon gate refused the adapter's plain
`json.loads` on the model's first full-suite run — correctly: research
executed the bypass (a duplicate-`disclosure` payload declassifies a
QUARANTINED claim to MENTIONABLE under last-wins parsing) before fixing.
The adapter now parses with the duplicate-refusing `_strict_pairs` hook
at every site. Two structural lessons, recorded because they recur:

- **A control proving a gate necessary must itself violate the gate.**
  The last-wins demonstration cannot live in the evidence tree the gate
  protects; it lives in the DRIVER (`tests/`, outside the gate's scope),
  with the reason stated in its docstring. The gate protects evidence;
  the demonstration of the unprotected behaviour is justification, not
  evidence. (Gate-owner ruling, dev.)
- **Name-scanning and behavioural control cover different halves.**
  Mutation 7 — a hook that keeps the blessed NAME but accepts duplicates
  (`dict(pairs)`) — passes the gate's AST scan and is caught only by the
  model's behavioural control. Proven on both machines.

## Scope notes, stated rather than discovered

- The TRANSITIVE restriction case (an edge in `reach`) is accepted 0022
  ground, exercised by the shipped 54 sweep vectors; this model proves the
  MEMBERSHIP TEST's shape over the heterogeneous retire population.
- The ScopeView gap flagged at first adoption is CLOSED: the adapter now
  drives the real `ScopeView` end-to-end, with the discriminating pair
  (same adapter output, own vs foreign `source_id` → `(True, "own")` vs
  `(False, None)`) proving `visible` reads our fields rather than
  returning a constant — the cross-scope case and its own control in one.
