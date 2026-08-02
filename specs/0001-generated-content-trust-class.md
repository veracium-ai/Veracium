# Feature spec: generated-content trust class (`EvidenceAuthor.ASSISTANT`)

Spec-Status: deferred

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **deferred** — external review 2026-07-31 deferred v2; v3 written and re-reviewed, amendments outstanding (see §13 and the v3 external review)

*Fill this in **before** implementing. See `PROCESS.md`.*

> First spec through the full process. Numbering starts at `0001`; the `0007`
> in `PROCESS.md`'s examples is illustrative, not a reservation.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v3** — narrowed after external review deferred v2. §13 lists the changes. Previously v2 — (`spec-0001-research-review.md`); §11 lists the changes. *Re-read before editing; quote the version you approve.* |
| **Status** | *see `Spec-Status:` at the top — canonical.* v2 was deferred at external review; **the assertability widening is withdrawn, not re-argued.** v3 narrows to `use_only` for every subject and has its own external review outstanding. |
| **Internal reviewers** | **research — reviewed 2026-07-31, accepted with amendments** · workflow-platform *(MCP surface changes)* — pending |
| **External review** | **returned 2026-07-31 — defer / major amendment.** Response: `proposals/spec-0001-external-review-response.md` |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

An assistant turn is authored by none of the three parties we model. Today a
host must call it `SYSTEM` (→ mentionable, so **a hallucination becomes an
asserted fact**) or `THIRD_PARTY` (→ `use_only`, so **the assistant reporting
the user's own state is unusable**). Both are wrong, and we have measured the
cost of each: benchmark Arm T, which treats assistant turns as system-authored,
scored **7/8 on abstention where Arm C scored 8/8** (LongMemEval pilot, run
`20260730T174434`), and Arm C's capping produces **4 of 9 answer-misses**,
including `184da446`.

**If we do nothing:** every host embedding veracium in an assistant loop — which
is the primary deployment — makes this choice itself, silently, with no
vocabulary to describe what it chose. The `SYSTEM` branch is the dangerous one
and is also the convenient one, so it is what hosts will pick.

**Alternatives rejected.**

- **A host toggle for assistant assertability** *(dev proposed; research
  rejected — `q2-4-generated-content-answer.md`, accepted here)*. Principal–
  agent: the host sets the policy, **the user carries the risk**, and
  documenting the trade-off does not help because the party reading the docs is
  not the party paying. It would also convert an enforced guarantee into a
  configurable one, which is the exact distinction we draw against competitors.
- **A fourth `Disclosure` tier.** The tier was never the problem; the author
  was. `use_only` already means "real-looking, unverified, never asserted".
- **Reusing `SYSTEM`.** `SYSTEM` means *our own* consolidation and maintenance
  output, which we generate and can reason about. Assistant text is
  externally generated and may be adversarially influenced. Conflating them
  makes both unanalysable.
- **Letting `derived_from` express it.** Blocked by design: `derived_from` may
  only **cap** trust, never raise it (the 0.1.7 laundering defence). "The
  assistant is restating the user, therefore assertable" cannot be said with it,
  and must not be bolted on.

---

## 2. Field contracts touched

*Provenance: reinforcement silently overwrote `valid_from`, whose documented
meaning at three code sites is "when the fact became true". The renderer then
emitted `(since <that value>)` into the answer context — a false statement
injected into recall. Nobody had enumerated who reads the field.*

| field | read / written | its **documented** contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Provenance.author_of_evidence` | written by `ingest`, read by 8 modules | "Who authored the evidence. The core injection-resistance signal." | `ingest` (`_disclosure_for`, `_source_type`), `lifecycle:101` **(episode consolidation — see below)**, `introspect`, `__init__`, `cli:299` **(hardcoded `choices=`)**, `mcp_server:26` (host string→enum map), `selfcheck`, plus 16 test files, 5 docs and 2 examples | **Yes — extended, not redefined.** No existing member changes meaning. **But the value set is no longer closed**, which is the contract change that matters: every consumer branching on it must be re-read, not assumed. |
| `Episode.provenance.author_of_evidence` | written by `ingest`, **rewritten by `lifecycle.consolidate`** | same field, on episodes | `gate` (via episode authorship), `graph` (episode rendering) | **NO — see the defect found below.** |
| `Edge.subject` | written by `ingest`, read by `graph`, `compile` | the entity a fact is about; `"user"` is the reserved literal for the store owner (`graph.py:201`, `graph.py:295`) | `graph._cover`, `graph.render_edges`, `compile`, `introspect` | **Yes**, but it acquires a **second** load-bearing role: it now gates disclosure, not only rendering. Previously a wrong `subject` produced an odd sentence; now it can change assertability. Recorded as a real widening of that field's blast radius. |
| `Provenance.disclosure` | written by `ingest._disclosure_for` | mentionable / use_only / quarantined | `Edge.assertable`, `gate`, `graph`, `proactive`, `introspect` | **Yes** — no new value; only a new way to arrive at `use_only`. |
| export `version` (`portability.FORMAT_VERSION = 2`) | written on export, checked on import | "an export version newer than this library fails closed" | `portability.load` | **Changed deliberately → 3.** See §7: without the bump, an older library hits a pydantic `ValidationError` instead of our own message. |

**Consumers enumerated mechanically** (`grep -rn`, both `src/` and outside it —
the `src/`-only form used previously misses tests and docs that encode the
contract):

```
$ grep -rln "author_of_evidence\|EvidenceAuthor" src/ tests/ docs/ examples/ README.md
src/veracium/{schema,ingest,lifecycle,introspect,__init__,cli,mcp_server,selfcheck}.py
tests/ (16 files)  docs/{api,concepts,design-rationale,recipes}.md  README.md
examples/{demo.ipynb,langchain_memory.py}
```

**⚠️ I first wrote this table from memory and it was wrong in both directions,
which is the rule earning itself on the first spec that used it.** I had listed
`gate.py`, `graph.py` and `portability.py` as consumers: **they reference the
enum zero times** — they branch on the *derived* `disclosure` field, so the
author enum's blast radius is narrower than I assumed. And I had missed
`cli.py`, `lifecycle.py`, `selfcheck.py`, two examples, two docs, and four test
files. **The miss mattered more than the over-count**, because one of the files
I missed contains a defect (below).

**Two consumers need code changes that the memory-written list would have
skipped:**

- **`cli.py:299`** — `--author` carries `choices=["user","third_party","system"]`,
  a hardcoded public CLI surface that silently rejects `assistant` until updated.
- **`lifecycle.py:101` — a pre-existing trust-laundering path, and this change
  makes it more reachable.** Episode consolidation builds the new episode's
  provenance as `cold[0].provenance.model_copy(update={"author_of_evidence":
  cold[0].provenance.author_of_evidence, ...})` — it inherits the **first**
  episode's author across a whole cold set. The comment directly above says
  *"consolidation is a system-authored derivation of the cold set"*, so **the
  code and its own comment disagree**: a mixed cold set collapses to whichever
  author happens to be first. Today that can already promote a third-party
  episode to user-authored; adding a fourth class makes mixed sets more common.
  Addressed as I10 rather than left as a note, because "we noticed it" is not a
  control.

**Documentation stating the old meaning, updated in this change:**
`docs/concepts.md`, `docs/api.md`, `README.md` trust-model table, the
`EvidenceAuthor` docstring, and `mcp_server.py`'s tool description.

---

## 2c-ii. Assertions about reach

*Required since the §2c-ii amendment. Every claim below carries the command that
establishes it, not a statement that it was checked — **both prior versions of
this spec failed on unverified assertions about what was reachable.***

| assertion | command | result |
|---|---|---|
| `EvidenceAuthor` has exactly 3 members today | `grep -A6 "class EvidenceAuthor" src/veracium/schema.py` | `USER`, `THIRD_PARTY`, `SYSTEM` |
| a host can set the author via MCP | `grep -n "EvidenceAuthor" src/veracium/mcp_server.py` | `:26` maps host strings → enum |
| the CLI `--author` list is hardcoded | `grep -n "choices" src/veracium/cli.py` | `:299` `["user","third_party","system"]` |
| `import` is a shipped CLI verb with `--user` | `grep -n "add_parser" src/veracium/cli.py` | `:278` `import`, `:280` `--user` |
| which combinations reach `use_only` | `_disclosure_for` over the enum product | user+3P · 3P+any · system+3P |
| an older library cannot load an `assistant` edge | `Provenance(author_of_evidence='assistant')` | `pydantic.ValidationError` |
| no `PRAGMA user_version` guard exists | `grep -n "user_version" src/veracium/store/sqlite.py` | no match |

---

## 3. Trust-class matrix — REQUIRED, blocking

*Provenance: T1 subset-absorption merged edges without checking authorship or
disclosure, so a third-party restatement could retire a user-asserted fact out
of the assertable set and inherit its confidence. Advisory GHSA-r7j7-5jq9-3f5q.*

**Directional, because our operations are.** `apply_supersession` and T1
absorption both distinguish the **surviving/prior** edge from the
**incoming/candidate** one (`graph.py:_subsumes(pk, same)`), and the 0.4.1
defect lived exactly in that asymmetry. A single `user × assistant` cell cannot
express it, so both directions appear.

**Enumerated from code, not from memory:** `EvidenceAuthor` = `USER`,
`THIRD_PARTY`, `SYSTEM`, **`ASSISTANT`** (new); `Disclosure` = `MENTIONABLE`,
`USE_ONLY`, `QUARANTINED`.

### 3.1 Write-time disclosure — NARROWED IN v3

**v1 routed on the subject and failed. v2 tried to fail closed on a
"recognised" subject and failed differently — the predicate was unbuildable
(no entity resolution, no display name, 19,096 distinct subjects across 131,574
extracted triples, only 39.4% the literal `"user"`). v3 does not route on the
subject at all.**

| author | derived_from | disclosure |
|---|---|---|
| `ASSISTANT` | — | **`use_only`**, for **every** subject |
| `ASSISTANT` | `THIRD_PARTY` | `use_only` (existing cap; unchanged) |
| `ASSISTANT` | relation == quarantine | `quarantined` (unchanged) |

**One rule, no subject inspection, no new predicate.** Promotion remains
`confirm()` — a user act — exactly as v1 proposed and research accepted.

**What this gives up, stated plainly:** the *"the test suite passed"* case stays
`use_only`, so an assistant's first-party report of its own action is not
directly assertable. **That capability now depends on the evidence-basis axis
(research's, its own design round), which is the right home for it** — a
deployment result should be groundable because an authenticated tool returned
it, not because an assistant said so.

**What it buys:** hosts stop mislabelling assistant content as `SYSTEM`, which
is the dangerous *and* convenient default, and no new persistent assertion
channel opens. **That was always the majority of the value.**

### 3.2 Operations, both directions

| operation | prior=USER, incoming=ASSISTANT | prior=ASSISTANT, incoming=USER | ASSISTANT × ASSISTANT | involving quarantined | involving `use_only` |
|---|---|---|---|---|---|
| **supersession** (functional relation) | **blocked** — differing disclosure class (0.4.1 guard) | **allowed** — user supersedes assistant; trust rises via new user evidence, not via merge | allowed when same disclosure class | never | only within class |
| **T1 absorption** (subset) | **blocked** — same guard | **allowed**; winner is the user edge | allowed when same class | never | only within class |
| **reinforcement** (identical fact) | **blocked** | **blocked** — see below | **merge allowed; `observed_at` refresh BLOCKED** — Q1, resolved | never | only within class |
| **`confirm()`** | n/a | **this is the promotion path**: user affirmation flips an assistant `use_only` edge to assertable | n/a | never — `confirm()` has never elevated quarantined | this is what it is for |

**Q1 resolved — `ASSISTANT × ASSISTANT`: allow the merge, block the currency
refresh.** I had proposed blocking the merge outright on a
compounding-confidence hazard. Research showed the hazard is not confidence —
`confidence = max(members)` synthesises nothing, so two assistant statements
merging cannot manufacture a higher number than either held. **The exposure is
currency.** Reinforcement refreshes `provenance.observed_at`, which under C′ is
the liveness axis `lifecycle.expire()` ages against. So an assistant restating
its own hallucination would keep it fresh **indefinitely** — freshness-pinning
by self-repetition, which is the manufactured-freshness failure the T2 debate
settled, one trust class down.

**Rule: an assistant restating itself is deduplication, not evidence.**
Absorption proceeds (§5's crowd-out analysis positively wants it); reinforcement
must not advance `observed_at`. Checked by **I10a**. The consequence is that
assistant edges **age out normally**, which is correct on its own terms: a
statement about an action is point-in-time, not a persistent state.

**Reinforcement across classes is blocked in *both* directions and that is
deliberate.** A user
restating an assistant claim looks like reinforcement, but under the C′
semantics reinforcement mutates `provenance.observed_at` on the **prior** edge —
so allowing it would let user evidence refresh the currency of an
assistant-authored statement while leaving it assistant-authored. The user's
statement must create a **new user edge** that then supersedes. Slightly more
storage; no laundering.

**Answering the four required questions:**

- **Can this cause a user-asserted fact to become non-assertable?** No. Every
  operation where an assistant edge is the incoming side against a user prior is
  blocked by the same-disclosure-class guard. **§6 I3 tests this rather than
  assuming it** — that guard was written for third-party edges and its behaviour
  on a new author class is exactly the kind of thing that survives review by
  looking obviously fine.
- **Can non-user content gain user-grade authority, confidence, or currency?**
  Only through `confirm()`, which requires a user act. `derived_from` still
  cannot raise trust.
- **Can it clear `needs_confirmation`?** Only `confirm()`, unchanged. Dedup and
  maintenance still never clear it.
- **Does it merge, drop, or overwrite provenance?** No new path. Blocked merges
  leave both edges intact and dated, which is the additive-noise side of the
  asymmetry we prefer.

**Write-time or maintain-time?** **Write-time.** Disclosure is assigned when
evidence arrives. No maintenance operation may re-derive an edge's disclosure
from its subject afterwards — that would let a rename or a re-extraction change
assertability with no new evidence, which is the manufactured-freshness failure
the T2 debate settled.

---

## 3b. Authorization and scope — *full specs only*

*Trust class answers **whose claim this is and what authority it has**. It does
not answer **which user is permitted to see it**.*

- **Does this cross a user, tenant, or scope boundary?** No. Every edge is
  written under one `user_id` and every read is scoped to it; this change adds
  an author value and does not touch scoping.
- **Who may see the affected state, and does this change that set?** Unchanged
  set, **changed volume**: assistant edges about non-user subjects are now
  `mentionable`, so material that a host previously routed to `THIRD_PARTY`
  (never volunteered) may now appear in a proactive briefing with no user turn.
  That is the intended effect and it is why `proactive.py` is in §6.
- **Scope change (sharing, revocation, group join/leave)?** n/a — no sharing model.
- **Anything visible to a principal who could not see it before?** No new
  principal. The **only** visibility widening is within one user's own store,
  and only for subjects that are not that user.

---

## 4. Behaviour

`EvidenceAuthor.ASSISTANT` becomes accepted wherever an author is accepted:
`Memory.remember(..., author=EvidenceAuthor.ASSISTANT)` and the MCP `remember`
tool's `author` string (`"assistant"`).

Observable difference, given the same text:

| host says | before | after |
|---|---|---|
| `author="assistant"`, *"the deploy failed"* | not expressible; `system` → asserted, or `third_party` → `use_only` | **mentionable** — may be stated |
| `author="assistant"`, *"you prefer dark mode"* | same bad choice | **`use_only`** — rendered in the UNVERIFIED block, never asserted, promotable by `confirm()` |

**Exact rendering change:** an assistant edge with a non-user subject renders in
the normal grounded block with no new marker. An assistant edge about the user
renders in the existing unverified block; **no new sentence form is
introduced**, because rendered text becomes model context and a new phrasing is
a change to what the model reads.

### 4b. Rendering — ⚠️ ONE OPEN DECISION

Attribution must survive into the rendered context, or the class is pointless:
the whole finding from Workstream C is that a system with nowhere to *put*
provenance loses it. Research proposed keying the marker on
`author_of_evidence`:

```python
ORIGIN_MARKER = {THIRD_PARTY: " [third-party-reported; unconfirmed]",
                 ASSISTANT:   " [assistant-generated; unverified]",
                 SYSTEM:      " [system-derived; unconfirmed]"}
```

**Their four design decisions are adopted unchanged**: the default is a *marker*
not silence, so a forgotten class yields more caution; no author maps to empty;
*generated* rather than *reported*, leaving room for the evidence-basis axis;
and it dissolves the pre-existing quarantined/inference conflation.

**But keying on author alone discards `derived_from`.** Measured — the
combinations that actually reach `use_only` today:

```
author=user         derived_from=third_party  -> use_only
author=third_party  derived_from=(any/none)   -> use_only
author=system       derived_from=third_party  -> use_only
```

**`SYSTEM` reaches `use_only` ONLY via `derived_from=THIRD_PARTY`**, so
*"system-derived"* would name the relayer as the origin when a third party is.
And **`author=USER, derived_from=THIRD_PARTY` — the Workstream C landlord
shape — is not in the map at all.** The fix for one conflation would introduce
another.

**Proposed, pending research:** key on `(author, derived_from)`, checking the
capping axis first.

```python
if e.provenance.derived_from is THIRD_PARTY:  " [third-party-derived; unconfirmed]"
elif author is THIRD_PARTY:                   " [third-party-reported; unconfirmed]"
elif author is ASSISTANT:                     " [assistant-generated; unverified]"
else:                                         " [unverified origin]"   # fail closed
```

**Q5 is resolved** — `(author, derived_from)` (research, 2026-08-01). The
implementation blocker here is now this spec's `deferred` status, not Q5.

**Interfaces:** `EvidenceAuthor` gains a member (additive for callers that pass
it; **not** additive for callers that exhaustively match on it). MCP `remember`
gains `"assistant"` in its author map and tool description. **CLI changes
additively**: `cli.py:299`'s `--author` `choices` must accept `assistant`, with
help text, a parsing test and docs. *(v2 said "No CLI change" while §2 said the
opposite — the external reviewer found the contradiction in my own document; §2
was written later and I never reconciled them.)* Export
`FORMAT_VERSION` 2 → 3.

**Migration:** existing stores are untouched — no edge changes author, and no
backfill runs. Nothing is unrecoverable **going forward**; the irreversible step
is **downgrade**, see §7.

---

## 5. Regime analysis — where does this behave differently?

*Provenance: recall was query-blind on any store past `max_subgraph_edges` — no
fixture ever caught it because small stores never truncate.*

- **Scale / density.** Assistant turns are the *most numerous* event type in a
  chat deployment — plausibly the majority of all events, where third-party mail
  is a minority. So this class arrives at a volume the third-party path never
  reached, and it lands mostly in **mentionable**. The regime that matters is a
  store where assistant edges dominate the subgraph budget
  (`max_subgraph_edges`, default 40) and crowd out user facts by sheer count.
  **This is a genuinely new load pattern for the ranker, and the pilot corpus
  will not show it** — LongMemEval items average ~1,700 facts with a balanced
  mix.
- **Thresholds interacted with:** `max_subgraph_edges` (40),
  `subgraph_coverage_share` (0.0), `wiki_recompile_after_writes`.
- **Do the tests reach it?** **Not today.** A fixture-scale store cannot show
  crowd-out. **Release class: stable, so this blocks** — §6 I6 adds a
  1,000-edge assistant-dominant recall test asserting user-authored facts still
  reach the subgraph. Declaring it untested in §8 is **not** available, because
  the change ships on by default.
- **Cold vs warm / first vs thousandth call.** No difference: routing is
  per-event and stateless. The wiki recompiles on the same counter as before,
  though its *input mix* shifts toward assistant material — covered by I6.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where it runs |
|---|---|---|
| **I1** assistant + subject `"user"` → `use_only` | `test_assistant_about_user_is_use_only` | CI |
| **I2** assistant + other subject → `mentionable` | `test_assistant_about_artifact_is_mentionable` | CI |
| **I3** an assistant edge can never supersede, absorb, or reinforce a user edge | `test_assistant_cannot_touch_user_edge` (all three ops, both directions) | CI |
| **I4** `derived_from=THIRD_PARTY` still caps an assistant edge to `use_only` | `test_assistant_derived_from_third_party_is_capped` | CI |
| **I5** `confirm()` is the only promotion path; maintenance never promotes | `test_only_confirm_promotes_assistant` | CI |
| **I3b** the paths §3.2 says are **allowed** actually work: a user edge *can* supersede and absorb an assistant prior | `test_user_can_correct_an_assistant_fact` | CI |
| **I6** at 1,000 assistant edges, user-authored facts still reach the subgraph | `test_assistant_dominant_store_does_not_crowd_out_user` | CI |
| **I10** consolidation-style provenance rules hold for the new class: a mixed cold set never yields an assistant-authored summary presented as grounded | `test_mixed_batch_with_assistant_declares_influence` | CI |
| **I10a** assistant self-reinforcement dedups but **never advances `observed_at`** — no freshness-pinning by self-repetition | `test_assistant_restatement_does_not_refresh_currency` | CI |
| **I7** an export containing assistant edges is rejected by an older reader **with our message, not a pydantic traceback** | `test_downgrade_export_fails_cleanly` | CI |
| **I8** injection ladder unchanged; assistant authorship grants no new write authority | existing `bench --compare`, `engine.injection_asserts == 0` | bench gate |
| **I9** trust canaries unchanged | existing `engine.trust_canary_failures == 0` | bench gate |

Standing checks that must not regress: injection asserts 0 · cross-user leaks 0
· trust canaries 0 · supersession probes pass · malformed edges 0 · declared
read-cost and latency ceilings.

**I3b exists because I only tested prohibitions.** Research's point: I3 proves
an assistant edge cannot touch a user edge, and nothing tested the *allowed*
direction. A guard written slightly too broadly would block **user corrections**,
every prohibition test would still pass, and the symptom would be a user
correction that silently does not take — which is worse than the bug the guard
prevents and would look like the guard working.

**Reproducer retention:** `184da446` is retained as a fixture asserting the
case stays **unanswered** — it is the documented cost of this design (§8), and a
future change that "fixes" it silently would be reverting a decision rather than
improving recall.

---

## 7. Failure modes and reversibility

- **Silent failure mode.** A host that labels *every* assistant turn
  `author="assistant"` including turns that merely quote the user gets those
  facts capped at `use_only`, and the symptom is **abstention where the user
  expects an answer** — visible, but easily misread as "memory did not store
  it". First symptom is a wrong abstention on a fact the user did state, delay
  of one question. Mitigation is documentation, not code: the host should attribute
  a quoted user statement to the user.
- **Reversibility.** Forward-reversible: no existing edge changes, so reverting
  the library restores prior behaviour for **new** writes. **Backward: NOT
  reversible.** Verified — an older library loading an `assistant` edge raises
  `pydantic.ValidationError: Input should be 'user', 'third_party' or 'system'`.
  A store or export containing assistant edges **cannot be read by a pre-0.5.0
  veracium at all.** This is the first genuinely one-way schema change we have
  shipped and it is the reason `FORMAT_VERSION` goes to 3: `portability.load`
  then fails with our own "export version is newer than this library" message
  instead of a stack trace. **The SQLite store has no equivalent guard** —
  there is no `PRAGMA user_version` — so an old library opening a new `.db`
  still fails at pydantic. Adding a store version guard is **out of scope here
  and filed as §10 Q3**, because it is a portability change deserving its own
  spec rather than a rider on this one.
- **Partial failure.** No new multi-step operation; nothing to leave half-done.
  Permanent errors are not retried into a silent empty success (unchanged).
- **New attack surface?** **Yes, and it is the point of the design.** This
  admits a new class of externally-influenced content into `mentionable`.
  The containment is that it is admitted **only for non-user subjects**, where
  the assistant is the primary witness, and never for claims about the user.
  Prompt injection that induces an assistant to state *"the deploy succeeded"*
  will now be storable as mentionable. Injection inducing *"the user agreed to
  X"* remains capped.

  **v1 claimed this was "bounded by the fact that such a claim was already
  reaching the user directly in the same turn". That bound is deleted — it does
  not hold**, and research named the reason I had only suspected: **the turn is
  ephemeral; the store is persistent and re-injected.** The user reads the claim
  once, in a live context where it might look odd and be challenged. Memory
  asserts it into future contexts indefinitely, each one further from the turn
  that would have made it suspicious. Persistence is not a weaker version of
  utterance — it is a different exposure, and it is the one we build. The
  widening is stated as a limit in §8 rather than argued away here.

---

## 8. Claims and limits

- **What we will say**, exactly: *"veracium models assistant-generated content
  as its own evidence class. Assistant statements about the user are held as
  unverified until the user confirms them; assistant statements about its own
  actions may be used directly. Configuration may narrow what is assertable,
  never widen it."*
- **What this does NOT establish.**
  - It does **not** improve our LongMemEval score, and is **expected not to**:
    `184da446` and its class stay unanswered by design. Any post-change score
    movement is unattributed unless a frozen protocol says otherwise.
  - It does **not** make assistant content trustworthy. It gives a hallucination
    about a non-user subject a route to `mentionable` — a deliberate,
    bounded trade, not a safety improvement.
  - The 7/8-vs-8/8 abstention figure is **one question on an 8-item abstention
    subset from a single 44-item pilot run** (`20260730T174434`). It motivated
    the direction; it does not measure this change and cannot.
  - A passing injection ladder is *"no failures observed on the frozen suite"*,
    never "safe against prompt injection".
  - **It admits a new class of externally-influenced content into
    `mentionable`, and we have no bound on that exposure.** An assistant
    induced to state something false about a non-user subject can have it
    stored as assertable. We considered arguing this is limited because the
    claim also reached the user live, and **withdrew that argument**: the turn
    is ephemeral, the store is persistent and re-injected into contexts
    increasingly distant from the one that would have made it suspicious. The
    containment is the subject rule, not the utterance.
- **Measurements cited:** LongMemEval V1-S pilot, run `20260730T174434`, arm C,
  commit `ce66282`; Arm T comparison from the same pilot. Neither run is
  decision-eligible under the current policy (no freeze artifact) — cited as
  motivation, not as evidence for acceptance.

---

## 9. Brief for the external reviewer

- **What we are least sure of.**
  (1) **Subject-based disclosure routing.** `subject` was a rendering field and
  now gates assertability; it is extractor-produced, so a mis-extracted subject
  silently changes trust. Is that too much weight for a field we do not control?
  (2) **`ASSISTANT × ASSISTANT` merging.** They share a disclosure class, so
  today they merge. Two hallucinations reinforcing each other into higher
  confidence is a plausible failure we have not designed against.
  (3) Whether **`mentionable` is right at all** for first-party assistant
  testimony, versus a stricter default with opt-in narrowing.
- **Where we suspect we have overstated.** §7's claim that the injection
  widening is "bounded by the fact that the claim already reached the user in
  the same turn" — that is an argument, not a measurement, and it is doing a lot
  of load-bearing work.
- **What would change our minds.** Evidence that hosts cannot reliably attribute
  turns (making the whole class noise); or a construction where an assistant
  edge about a non-user subject launders into a claim about the user.
- **Added after internal review — please look hardest here.**
  **Self-corroboration.** Two assistant statements of the same fact now
  *deduplicate* but must not refresh currency (§3.2 Q1), on the reasoning that
  confidence takes `max` and so synthesises nothing, while `observed_at` would
  otherwise let a model keep its own hallucination alive forever by repeating
  it. If you have watched self-corroboration fail in another system, this is
  the part of the design most likely to be naive.
- **Reviewer-safe copy:** not required — no competitive-audit detail or
  unpublished findings here.

---

## 10. Open questions

| # | question | class | who decides | by when |
|---|---|---|---|---|
| ~~**Q5**~~ | **RULED 0001-Q5 (research, 2026-08-01 20:06): `(author, derived_from)`.** Author-only mislabels `system+third_party` and omits `user+third_party` — the two commonest `use_only` shapes after plain third-party. **Stale here for 16 hours** while the answer sat in COORDINATION; see the reconciliation check. | resolved | research | — |
| ~~**Q1**~~ | ~~Should `ASSISTANT × ASSISTANT` merges be blocked?~~ **ANSWERED 2026-07-31 (research):** do not block the merge; block the `observed_at` refresh. The hazard is currency, not confidence. See §3.2 and I10a. | ~~blocking~~ **resolved** | research | done |
| **Q2** | Does an assistant *restating* user testimony reinforce the user's edge instead of creating an assistant edge? The elegant fix; blocked by the same-disclosure-class rule; would remove most of §8's stated cost. | `deferred` | research | own design round |
| **Q3** | Store-level version guard (`PRAGMA user_version`) so an old library fails cleanly on a new `.db`, as exports now do. | `pre-release` | dev | before 0.5.0 |
| **Q4** | Does `_source_type` return `STATED` or `INFERRED` for a non-chat assistant event? Currently non-`USER` non-chat → `INFERRED`, which is probably right but is inherited rather than chosen. | `pre-release` | dev | before implementation lands |

---

## 11. Changes in v2 (after research's internal review)

1. **§3.1 failed open — fixed.** v1 routed *any* non-`user` subject to
   `mentionable`, so a mangled or invented subject from an extractor we do not
   control became assertable. Now only a **recognised** distinct entity is
   mentionable; empty, pronoun, placeholder and unresolvable subjects fail
   closed to `use_only`.
2. **Q1 answered and the reasoning replaced.** `ASSISTANT × ASSISTANT` merges
   are allowed; the **currency refresh** is blocked. My compounding-confidence
   hazard was wrong — `confidence = max` synthesises nothing. The real exposure
   is `observed_at`, i.e. freshness-pinning by self-repetition. New **I10a**.
3. **I3b added.** §6 tested only prohibitions. Nothing checked that the paths
   §3.2 calls *allowed* actually work, so a too-broad guard would silently block
   user corrections with every prohibition test still green.
4. **I10 added** for the new class against the consolidation defect this spec
   discovered (fixed separately in 0.4.4, GHSA-hcj3-8jqc-wqrp).
5. **§7's injection bound deleted**, moved to §8 as an unbounded limit. The turn
   is ephemeral; the store is persistent and re-injected. Persistence is a
   different exposure, not a weaker utterance.
6. **§9 brief extended** to ask the external reviewer specifically about
   self-corroboration.
7. **Status → accepted-with-amendments (internal).** Per `PROCESS.md` this does
   **not** authorise implementation: external review is outstanding and the
   amended version needs approval.

---

## 12. External review outcome — DEFERRED (2026-07-31)

**Accepted in full. The reviewer confirms `EvidenceAuthor.ASSISTANT` is needed
and that this spec does not establish that assistant claims about non-user
subjects belong in the ordinary grounded channel.** Full response:
`proposals/spec-0001-external-review-response.md`.

**The two findings I verified, both worse than stated:**

1. **The subject rule cannot work, and not because the alias list is short.**
   *"Quentin prefers dark mode"* bypasses it — and **veracium has no
   display-name concept at all** (`user_id` is opaque; no `display_name`
   anywhere in `src/`), so the library cannot know the store owner's name. **No
   denylist is writable.** Measured over 131,574 triples from the LongMemEval
   extraction cache: **19,096 distinct subjects, only 39.4% the literal
   `"user"`**. v2 would route **60.6% of triples** to `mentionable`, through a
   long tail of bare personal names (`mother`, `lizzie`, `rachel`). Positive
   resolution to a canonical entity id is the only sound mechanism and **we have
   not built entity resolution.**
2. **Subject identity does not establish evidence authority.** *"The deploy
   failed"* has a non-user subject and nothing shows the assistant deployed
   anything. I called it *"first-party testimony about its own action"* — that
   phrase assumes the action. I generalised from research's example rather than
   its principle. The corpus agrees: `assistant` is the **second most common
   subject** (5,436), so "the assistant did X" is frequent and would have gone
   mentionable on the strength of not being the string `user`.

**Structural correction adopted:** v2 bundled *introducing accurate provenance*
with *widening assertability*. Only the first is justified today. **v3 ships
`ASSISTANT` at `use_only` for every subject, with attribution preserved in
rendering** — which delivers the actual purpose (hosts stop mislabelling
assistant content as `SYSTEM`) without opening a new persistent assertion
channel. **Cost recorded before the fact: this is more conservative than current
Arm C, so it moves our benchmark score down or nowhere, never up.**

**Also accepted:** I2a (direct fail-closed tests); proactive eligibility assessed
separately from answer-context eligibility; the CLI contradiction (fixed in §4);
Q4 promoted to **blocking**; the `PRAGMA user_version` guard promoted to a
**hard release gate**; I10a widened to freeze *every* ranking-relevant field;
consolidation provenance to be specified in full, including whether one trusted
input may lift weaker ones; and I6 to carry a frozen acceptance rule.

**Reopened with research:** the fourth `Disclosure` tier. Research rejected it
("the tier was never the problem, the author was"), but the rendering analysis
shows a real expressive gap — we cannot say *"this may be discussed, but only as
something the assistant previously claimed."* Sequencing dissolves it: v3 does
not need the tier.

**🔴 v3 RELEASE GATE, found by research in the render path and confirmed here.**
`graph.py:305` is `tp = " [third-party-reported; unconfirmed]" if e.use_only` —
the marker keys on **`use_only`**, not on `author_of_evidence`, and its text is
**hardcoded**. Verified by construction: a `SYSTEM`-authored `use_only` edge
renders as

```
deployment uses_tool: failed (since 2026-07-31) [third-party-reported; unconfirmed]
```

Correct today, because only third-party-*derived* content reaches `use_only`.
**Under v3 it is affirmatively false** — every assistant edge would tell the
model a specific wrong origin. v3 exists so hosts stop mislabelling assistant
content as `SYSTEM`; as scoped it would swap one mislabel for a worse one,
because a wrong-but-confident provenance label is worse than a missing one.
**Blocks v3.** The gap is wider than one line: `gate.partition_parts:84` already
merges quarantined third-party *claims* with third-party `use_only` *inferences*
undifferentiated, and v3 would make that three kinds of thing in one block.

**Routed to workflow-platform:** what counts as "the assistant" in a multi-agent
deployment. Without an `author_id`, two unrelated agents mutually reinforce as
one source class, which interacts directly with §3.2's self-reinforcement rule.

---

## Reviewer checklist

- [ ] §3 has no unanswered cells
- [ ] §2 consumers were enumerated mechanically, not recalled
- [ ] Every §6 invariant has a check that actually runs
- [ ] §5 regimes are reachable by tests, or the change is experimental,
      off by default, and §8 says so
- [ ] §3b: no principal can see anything they could not see before
- [ ] §6 and §8 are filled in — `n/a — <reason>` counts, blank does not
- [ ] §10 questions each carry a class; unclassified means blocking
- [ ] §8 states what this does *not* establish
- [ ] I have said where I think the **author's conclusion is wrong**
- [ ] I re-read the current version before reviewing, and I am quoting the
      version I approve
- [ ] §9 brief is written, and external review has been sent

---

## 13. Changes in v3 (after external review deferred v2)

1. **The assertability widening is withdrawn, not re-argued.** v3 routes
   `ASSISTANT` to `use_only` for **every** subject. §3.1's subject rule is gone:
   v1 failed open, v2's "recognised subject" fix rested on a predicate the
   codebase cannot evaluate, and measurement settled it — **19,096 distinct
   subjects across 131,574 extracted triples, only 39.4% the literal `"user"`,
   and no entity resolution exists.** No subject-based rule is buildable.
2. **Speaker ≠ witness, conceded.** *"The deploy failed"* has a non-user subject
   and nothing establishes the assistant deployed anything. That capability
   moves to the **evidence-basis axis**, which is its right home — a deployment
   result should be groundable because an authenticated tool returned it.
3. **§4b added (rendering).** Research's four design decisions adopted
   unchanged; **one correction** — key on `(author, derived_from)`, because
   author alone mislabels `system+third_party` as system-derived and omits
   `user+third_party` entirely. **RULED 0001-Q5: `(author, derived_from)`.**
4. **§2c-ii added.** Every reachability claim now carries its command.
5. **Q3 (store-version guard) remains a hard release gate.**
6. **Recorded before the fact:** v3 is **more conservative than current Arm C**,
   so it moves our LongMemEval score **down or nowhere, never up.**
