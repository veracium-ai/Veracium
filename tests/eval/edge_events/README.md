# 0029/0030 shared acceptance corpus — FROZEN

*Frozen by research, 2026-09-05, before any implementation of the behaviour it
scores. Destination: `tests/eval/edge_events/` in the product repo — **dev
places it; research does not write to that tree.***

## Why research froze it

The spec requires the corpus "frozen model-free **before the first run**"
(0029 §6a; 0030 §6a says the same over the same corpus). Dev proposed, and
research accepted, that **the seat that implements may not set its own bar** —
the same principle as PROCESS §3a's "the author may not silently self-approve",
one layer down.

## The self-imposed condition, and why it matters

**Every expectation is derived from the SPEC's text, never from dev's plan or
code**, and each scenario carries the spec line that determines it. Where the
spec does not determine a value, the manifest marks it **OPEN** and asks rather
than guesses — because a bar set by my reading of an ambiguous line is not a
bar, it is an opinion with a digest on it.

Two such questions were recorded, and **both are now closed** by dev's
implementation answers (amendment 1, below). They are kept in
`OPEN_QUESTIONS_CLOSED` rather than deleted, so the amendment shows what it
closed:

1. **Scenario 6** needed two transactions with an equal `recorded_at`. §4c
   mints it once per batch from a real clock read; the spec does not say how a
   builder forces equality. **Answer: the store's injectable clock**
   (`SqliteStore(path, clock=…)`, the 0010 §4b-ii lease clock), held frozen
   across both transactions. Accepted — a mechanism the spec already provides
   rather than one invented for the test, which is what the question was
   asking. The requirement is untouched.
2. **Scenario 10(b)** — the spec says the second connection fails `database is
   locked`; whether that surfaces verbatim or wrapped by the 0007 busy-timeout
   discipline is an implementation fact. **Answer: verbatim and immediate on
   the seam-model runner at `busy_timeout 0`; embedded in the re-raised message
   on the product path; asserted as the substring `locked`, which holds on
   both.** Accepted — substring rather than equality is not a weakening here.
   An exact-string assertion would bind the corpus to one of the two paths and
   break on the other: the brittle-matcher defect this programme keeps
   re-finding.

## Amendments

**1 — 2026-09-05.** Both OPEN questions closed with dev's answers, folded into
the scenarios they govern (S06 setup + mechanism, S10 failure surface).
**No expectation changed.** The amendment records *mechanisms*, which were
dev's to declare — not *bars*, which were mine to set. Supersedes
`820cabee48112d8e674bfbff1917a0eca22d58d6b8bfebd7a101ff2a147f6f81`.

## What is in it

- **10 named scenarios** with exact expected event sequences AND
  `edge_state_at` reconstructions, including scenario 9's literal
  `epoch_txn = 0` contrast cell and scenario 10's two allocation schedules
  (the DEFERRED one retained as the negative control that proves the
  requirement is load-bearing rather than stylistic).
- **5 classification cells** named here and *specified in 0030 §6a* — one
  shared surface, each half owned where its behaviour lives.
- **9 retained v2 scenarios, WITH expectations** (amendment 2 — they shipped
  as bare names, which was a bar with no value in it; see below).
- **The four pass criteria, pre-committed** — copied from the spec, not
  invented here.

## Freeze

`MANIFEST.json` sha256 **`9974601d85cdcc7f3d459ae6d1a9c3e47206c23e79aa3c485019b9f7bd834867`**
(amendment 3; supersedes `c4197b598cecf04f…` and `c844523962fecdf8…`, which superseded
`820cabee48112d8e674bfbff1917a0eca22d58d6b8bfebd7a101ff2a147f6f81` — the
digest dev recorded in both `## Review closure` sections. That record stands:
it is the pre-implementation one, and it is what §6a asked for.)

Recorded before dev's first product commit of the choke point or migration, per
0030 §6a's "digest recorded in `## Review closure` before implementation".

## What this corpus does NOT do

It does not build or run anything. **Dev owns the portable builder/runner**
placed beside this manifest; research owns the expectations. That separation is
the point: if one seat authored both, the corpus would only prove the
implementation agrees with itself.

**2 — 2026-09-05. The nine retained v2 scenarios gain their expectations.**

They shipped as nine bare **names** — a bar with no value in it. That is my
omission, not dev's: dev found it, **refused to guess**, and raised it, which
is the same discipline the freeze asks of me.

They **are** scored. Pass criterion (1) says "every scenario", and the v2 text
those names are retained *from* (commit `4698a1c`) required "each scenario
naming its exact expected event sequence (kind, reason, digest-transitions, seq
order)". The digest-transitions clause is dead by v3 F5 — full snapshots
dissolved the old/new-digest question — so the retained shape is **kind,
reason, seq order**, resolved against §4a's per-write kind rule and §4b's
site→kind table. Criterion **(5)** is added so a runner cannot satisfy the gate
while skipping them.

**Four of the nine expand into cells rather than one expectation**, because the
spec names more than one path and picking would be my choice rather than the
spec's: `confirm` (byte-delta present / absent — §4a's third branch is what
proves the trigger basis is the full-state delta and not the call), `absorb`
(survivor restated / created), `expiry` (`lapsed` / `decayed`), `import`
(created / mutated / **no event** — v4 F-A's named reachable instance of the
per-write rule).

**Two are asserted as sets within a batch, not as ordered sequences.** The spec
makes `seq` monotone "per the append order the database serialized" and does
not determine which of a supersession's two events is appended first. The
atomic unit it *does* pin is the batch, so that is what is asserted — pinning
an intra-batch order would be a bar set by my reading of a line that does not
set one.

`erase` is the one scenario whose pass condition is an **absence**, and it is
stated as a **count of zero rows** plus an untouched second user — "no `erased`
kind appears" would pass a store that left the events under a different kind,
and a single-user check cannot distinguish scoped erasure from a table wipe.

**3 — 2026-09-05. `absorb` (V05) corrected; the bar gets SMALLER.**

Amendment 2 had it wrong, and the error was mine reading the spec — not a gap
in the spec. §4b's `mutated` row says "absorption restate" and its `created`
row says "insert_incoming, **absorption survivor**". Those name two *different
edges*, and I read them as two fates of one. The restate is the **absorbed
prior** (re-upserted with its note extended by `absorbed_by:<survivor>`); the
survivor **is** the incoming edge and is new by construction
(`graph.py:426` — "The survivor IS the incoming (a NEW row)").

So there is **one** shape, not two cells: three events in one txn — absorbed
`mutated`, absorbed `invalidated`/`absorbed_duplicate`, survivor `created`.
Amendment 2's cell (a) named a path that does not exist, and its cell (b)
omitted the absorbed edge's restate entirely.

The correction **reduces** the bar, which is the part worth recording: an
"exhaust the class" instinct manufactured a second cell for a path there was no
evidence for. That is the same over-broad error in a bar that it would be in a
claim, and it is harder to see, because a bar that is too wide looks like rigour.

Ordering within the batch is still not asserted. Instead the **payloads** are
pinned — §4a makes each event's `state` the edge's full serialization *after*
that mutation, so the absorbed edge's `mutated` state must carry the extended
note and its `invalidated` state must carry that note plus the invalidation
fields. That constrains the sequence using what the spec *does* determine,
rather than asserting an order it leaves to "the append order the database
serialized."

Dev's `import` mechanism is recorded on V08: cells (b) and (c) reach the
presence-admitting replace through `Store.commit_outcome_import_plan` — the
site §4b names — because `portability.import_memory` skips an existing id
before the commit, so through the public importer both cells would emit no
event for the **short-circuit** reason rather than the **delta** reason and
cell (c) would pass while measuring nothing. That was the confound research
flagged; dev found and closed it before it reached the gate.

## Known cosmetic debt — rides the next amendment, deliberately not a digest move

`V02` (supersede) keys its per-event edge role as **`edge`**; `V05` (absorb),
added later, keys it as **`role`**. Dev's runner reads either, so nothing fails
today. It is recorded here rather than fixed because **the fix is worth less
than the churn**: a digest move obliges dev to re-pin an artifact whose gate is
green, to change a key no consumer misreads. It is written down so it is
carried rather than rediscovered — the next amendment that moves the digest for
a substantive reason unifies the key to `role`.

*(The README is not hashed — only `MANIFEST.json` is — so recording this here
costs no re-pin.)*
