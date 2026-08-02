# Feature spec: subject-scoped entitlement

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — split out of `0003` on 2026-08-02, **after two external reviews
> showed the entitlement model is a larger design than the defect that motivated
> it.** `0003` narrows to the reported attack and ships; this owns the breadth.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
| **Status** | *see `Spec-Status:` — canonical.* Holds `0003`'s deferred scope. **Nothing here blocks `0003`.** |
| **Internal reviewers** | — |
| **External review** | required |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Why this is separate

**`0003` proposed a global author ladder. Two reviews established that the
ladder is right for user-self facts and overbroad for the graph** — a user
assertion should not erase sourced third-party evidence about another person or
an organisation.

**The fix `0003` v2 proposed does not work.** It derived subject class from the
relation registry, and **a relation cannot tell you whose fact it is**:
`Quentin works_as Acme` and `Alice works_as Acme` share a relation and belong to
different classes. Making it work needs subject identity, alias canonicalisation
and a total classifier — **a design, not an amendment.**

**Meanwhile the reported defect is unfixed after two review rounds.** Third-party
content can still retire a user fact at `graph.py:139`. **So `0003` narrows to
that, and the breadth lands here** rather than holding a guard hostage to an
entitlement model.

---

## 2. Scope inherited from `0003`'s reviews

| # | inherited finding | why it needs this spec |
|---|---|---|
| **E1** | subject class cannot come from the relation | needs `subject_class(user_id, subject, relation)`, canonical identity, alias handling, and an explicit default |
| **E2** | the authority matrix must be subject-aware | once subject class is load-bearing, the 400-row product stops being the decision procedure; the generated policy must take a subject dimension |
| **E3** | external-world contention has no current-value semantics | *"both stay active"* leaves a functional relation with no unique value; needs a **`CONTESTED`** relation state every reader handles |
| **E4** | trusted ingress must be a capability | `derived_from=None` is safe only if absence was **positively established**; a persistence-site manifest cannot authenticate origin |
| **E5** | `correct()` and absorption under one authorised replacement | needs an unforgeable authorisation bound to *(store, prior, replacement, kind)* and checked inside the atomic operation |
| **E6** | a distinct history partition | `GROUNDED_CURRENT` / `UNVERIFIED_CURRENT` / `RETIRED_HISTORY`, so an inactive edge is never in a block whose meaning is *present grounded fact* |

**`0003` explicitly does not claim any of these.** Its §8 says so.

---

## 3. Why the narrow version does not make this harder

**Blocking is strictly conservative.** `0003` only ever **refuses** a retirement
it currently permits; it grants nothing and hides nothing. So every rule here
can be added later as a **further restriction or a widening of an existing
refusal**, without unwinding `0003`.

**The one thing `0003` fixes that this spec would otherwise inherit** is the
attack: after `0003`, no lower-authority edge retires a higher-authority one
through functional supersession. **This spec then decides who is entitled to
retire *what about whom*** — a different question, and one that is safe to leave
open while the deletion primitive is closed.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **E-Q1** | How is the user's own subject identity canonicalised — `user_id`, a declared alias set, or an identity relation? | **blocking** | research | before design |
| **E-Q2** | Does `CONTESTED` belong in the schema, or is it derived at read time from multiple active edges on a functional relation? | **blocking** | dev | before design |
| **E-Q3** | Is `EvidenceContext` a constructor argument threaded through ingest, or an ambient context object? The first is invasive and checkable; the second is neither. | `pre-release` | dev | before design |
