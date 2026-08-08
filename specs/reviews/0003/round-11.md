# specs/0003 — external review round 11 (2026-08-08)

**Verdict: architecture APPROVED — "end broad architecture review here." Canonical `accepted`
deferred on two contract/process-only corrections only; no architecture round requested.**

The five round-10 items are confirmed closed (contention-resolution invalidation is symmetric;
the wiki cache binds a `compiler_policy_digest` over the host registry/policy; the fenced
challenger's structured reach is removed; §7a lists the `Recall` API; the ledger is materially
improved). The reviewer explicitly did NOT reopen: the authority ladder, `min(author,
derived_from)` capping, refuse-and-preserve, broad permutation inside functional contention
groups, refusal-scoped wiki/preservation, finite budget, CAS-linearized plans, durable receipts,
the v3→v4 schema direction, or entitlement/history deferral to `0011`.

## Two remaining corrections (bookkeeping/contract only → v14, then `accepted`)

**C1 — same-partition contention is ambiguous between I6 and `Recall.contested`.**
I6 promises every distinct **same-partition grounded** value renders (higher authority first),
even one ordinary relevance retrieval did not select. But the round-10 carrier rule exposes a
full `Edge` only for the preserved higher-authority prior + members retrieval already selected.
A lower-authority **grounded same-partition** challenger is in neither category → it renders in
`Recall.context` (I6) but would be content-free in `Recall.contested`/`Recall.edges` — exactly the
structured/rendered drift the carrier exists to prevent. This is NOT the fenced-challenger reach
issue (the SYSTEM value here is already on the grounded side). Required: state that every value the
deterministic I6 surface exposes is a full exposed member; the no-query-independent-reach rule is
scoped to an UNSEEN FENCED CROSS-partition challenger. Add prospective tests distinguishing the two.

**L — §11a does not literally satisfy PROCESS §4a's one-row-per-finding rule.** Rounds 3 (5),
4 (5) and 5 (7) are collapsed to one row each; several early closures give only a normative
section or "→ 0011" prose, not a command/test/commit ("prose is not a closure"). Required:
expand round 5 into its seven rows; reconstruct rounds 3/4 from the artifacts if they exist, else
make an explicit evidence-loss ruling rather than pretending the verdict-only files contain five
findings; give every closure row real evidence; for scope-move findings cite the commit that
performed the narrowing.

## Disposition

Fix those two without reopening the architecture, then set `Spec-Status: accepted` and move
further verification into implementation of I1–I9.

## Implementation-watch (not a blocker)

§7a says v4 introduces exactly two new tables and no existing table/field changes. If
implementation needs a physical `compiler_policy_digest` carrier (a wiki column or a third schema
object) rather than an internal cache envelope / cache-disable strategy, that is a spec/schema
amendment, not an invisible implementation choice. Closed at the current design boundary.
