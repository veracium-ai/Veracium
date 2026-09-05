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
- **9 retained v2 scenarios.**
- **The four pass criteria, pre-committed** — copied from the spec, not
  invented here.

## Freeze

`MANIFEST.json` sha256 **`c844523962fecdf8ea369312e86a9756a505001f674bc017e8bf2363a1c6da8b`**
(amendment 1; supersedes `820cabee48112d8e674bfbff1917a0eca22d58d6b8bfebd7a101ff2a147f6f81`,
the digest dev recorded in both `## Review closure` sections — that record
stands, and this one is the amended artifact)

Recorded before dev's first product commit of the choke point or migration, per
0030 §6a's "digest recorded in `## Review closure` before implementation".

## What this corpus does NOT do

It does not build or run anything. **Dev owns the portable builder/runner**
placed beside this manifest; research owns the expectations. That separation is
the point: if one seat authored both, the corpus would only prove the
implementation agrees with itself.
