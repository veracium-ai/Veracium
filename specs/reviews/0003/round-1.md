# specs/0003 — first external review, 2026-08-02

*Moved out of the spec when v3 narrowed scope. The spec keeps a changelog; carrying full dispositions inside it is the append-only pattern that caused document-integrity failures in 0002.*

## 12. First external review, 2026-08-02 — disposition

**Ladder direction approved. Eight findings, all verified against the spec and
the code.**

### Finding 1 — I inverted two of four ASSISTANT cases

**WITHDRAWN wording**, quoted so the correction is legible: §3 said
*"`assistant → user` block … `assistant → third_party` allow"*. Under
the spec's own rule — supersession permitted when **incoming effective authority
≥ prior** — with `USER 3 > SYSTEM 2 > ASSISTANT 1 > THIRD_PARTY 0`:

```
assistant -> user          incoming 3 >= prior 1   allow   (spec says block)
user      -> assistant     incoming 1 >= prior 3   BLOCK   (spec agrees)
third_party -> assistant   incoming 1 >= prior 0   allow   (spec agrees)
assistant -> third_party   incoming 0 >= prior 1   BLOCK   (spec says allow)
```

**Two of four are backwards, and `assistant → third_party: allow` is the unsafe
direction** — it lets assistant-generated content retire a third-party record.

**The source I was copying from had it right.** Research's
`proposals/cross-class-supersession.md:95` reads *"`assistant → user` allow ·
`user → assistant` block · `third_party → assistant` allow · `assistant →
third_party` block"* — correct on all four. **I inverted two while transcribing,
and the sentence I wrote around them — *"extends with no new concept"* — is what
made it read as derived rather than asserted.** §3's "measured 9/9" covers the
nine non-`ASSISTANT` pairs; **the `ASSISTANT` row was never measured, and the
prose implied it had been.**

| # | finding | verified |
|---|---|---|
| 1 | ASSISTANT cases contradict the ladder | **yes** — arithmetic above |
| 2 | the matrix tests a simpler rule than the one specified | **yes** — I1 enumerates author pairs; the rule is on `min(author, derived_from)`, so the product includes every `derived_from` **including absent**, and the cases where raw and effective authority differ are exactly the interesting ones |
| 3 | host provenance is not pinned | **yes** — I7 closes the MCP route only. Nothing establishes that third-party content always receives `derived_from=THIRD_PARTY`, and **omitting it overstates authority**, which the spec says and does not guard |
| 4 | absorption also retires edges and is not covered | **yes** — `graph.py:94` filters priors on **disclosure equality**, and this spec's own §1 argues that is inadequate because `USER` and `SYSTEM` share `MENTIONABLE`. **A `SYSTEM` edge can absorb and retire a `USER` edge.** I9 covers writers of `supersedes=`, not every path that invalidates because another edge arrived |
| 5 | `correct()` carries two conflicting fixes | **yes** — `:262` still states the **withdrawn** option (*refuse on a non-assertable edge*) as a live "Proposed fix" while `:267` and Q5 resolve it the other way. And **I10 preserves `author_of_evidence` and `disclosure` but not `derived_from`**, so a corrected edge can move from effective authority **0 → 3** |
| 6 | a global ladder ignores the subject | **yes, and it is not a corner case** — under this rule a user assertion can always retire sourced third-party evidence about another person, an organisation or a document. The user is authoritative about their own testimony, not about every subject in the graph |
| 7 | I5's visibility routing is under-specified | **yes** — it says superseded edges must reach the model and never says **which block, which disclosure classes, or which invalidation reasons**. **Making previously invisible attacker-controlled text visible is an exposure change**, and §7's "no new attack surface" is unsupported as written |
| 8 | I6 is a fixture, not a policy | **yes** — Q4 still asks whether superseded edges need a separate budget, which means the general property is unfrozen |

**Method note, since finding 1 is the second transcription error this week.**
The `_cover` docstring, the `valid_from` changelog, and now this: **a claim
restated in a second document, correct in the first.** The withdrawn-phrase lint
would not catch it — nothing was retracted. What would is deriving the matrix
from the ladder constants rather than writing it out, which is what v2 must do.

---
