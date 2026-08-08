# specs/0003 — second external review, 2026-08-02

*Moved out of the spec when v3 narrowed scope.*


**Twelve findings, all verified. The direction is approved twice; what fails now
is the design of the mechanisms, not the rule.**

### The three worth reading first

**1 — the subject classifier does not work.** §3a says subject class is *"derived
from the relation registry, not guessed per edge"*. **A relation cannot tell you
whose fact it is.** `Quentin works_as Acme` and `Alice works_as Acme` share a
relation and are user-self and external-world respectively. The same holds for
`lives_in`, `prefers`, `owns`. **Relation metadata can say a relation *may*
describe user-self state; it cannot establish that a given edge's subject is the
user.** Entitlement needs `subject_class(user_id, subject, relation)` with
canonicalised identity and aliases, defaulting to **external-world** when
ownership is unclear.

**10 — I replaced a bad rationale with a false one.** v1 justified no advisory
partly by deployment count; the first review told me to lead with
automatic-versus-invoked instead, and I wrote *"exploitation requires third-party
ingestion plus a functional collision — it is not automatic."* **That is wrong
for the primary defect.** Once third-party content reaches extraction, the
retirement happens **inside `apply_supersession`, automatically** — no second
privileged call. The automatic/invoked distinction holds for `correct()` and not
for ingest, and the two must be dispositioned separately.

**4 and 5 — the centralised guard is not centralised.** The store refuses
retirement for `reason="superseded" | "absorbed_duplicate"`, enumerated as
strings, while **this spec's own routing table lists `corrected` as a
replacement-caused retirement.** So `correct()` can retire under a reason the
guard does not protect. And the "authorisation result" has **no type, no
constructor, no binding and no lifetime** — a plain boolean or public dataclass
would be another caller-controlled field, not a capability. It must bind
*(store, prior id, replacement, subject class, kind, authority inputs)* and be
checked **inside the atomic operation**, or it is forgeable and replayable.

| # | finding | verified |
|---|---|---|
| 1 | subject class cannot come from the relation | **yes** — `:361` |
| 2 | the 400-row matrix no longer covers the policy | **yes** — `specs/ladder.py` has no subject dimension, so the generated table stopped being the decision procedure the moment §3a landed |
| 3 | `derived_from=None` is still an escalation | **yes** — `min(AUTH[a], AUTH[d or a])` treats absence as "direct from this author", which is safe **only if absence was positively established** |
| 4 | `corrected` bypasses the guard | **yes** — `:435` |
| 5 | the authorisation result is unspecified | **yes** |
| 6 | "grounded history" conflates history with assertability | **yes** — an inactive edge in the grounded block asks the model to infer a semantic exception inside the trusted partition |
| 7 | the `use_only` row assumes provenance from disclosure | **yes — and it is this spec's own error, restated.** §3 argues disclosure is not a proxy for authority, then labels all `use_only` history "third-party origin" |
| 8 | external-world contention has no current-value semantics | **yes** — §1 rejected "never supersede" partly because it leaves no current value; v2 adopts it for external-world facts without supplying the semantics |
| 9 | "migration: none" is false | **yes** — `:421`. v2 removes `actor`, adds `SourceType.CORRECTED`, adds relation metadata, changes a store signature and adds a retrieval budget |
| 10 | the no-advisory rationale is unsound | **yes** — above |
| 11 | stale status and decision text | **yes** — §10 still marks **Q4 `pre-release`** while §4c resolves it |
| 12 | I9's description contradicts the new design | **yes** — `:429` says a set-equality test is not enough; `:541` says it is deliberately a set-equality test. Plus a duplicated reversibility fragment |

### The method failure, named plainly

**Findings 11 and 12 are 0002's failure mode, reproduced in one cycle.** I
appended §3a, §4a–§4c and a disposition, and did not replace §5, §9, §10 or the
I9 prose they contradict. **Seven rounds of 0002 taught me that appending a
correction leaves the old rule live, and I did it again on the next spec the
same day.** v3 replaces those sections rather than answering them elsewhere, and
§12 becomes a changelog.

---
