# Feature spec: what may clear `needs_confirmation`

Spec-Status: accepted
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **accepted 2026-08-02 19:27 UTC** — under `PROCESS.md` §4a, after four external rounds in
> which **the clearing rule was approved every time**. Every finding is closed
> in *Review closure* with openable evidence. **`Spec-Requires: 0007` still
> blocks implementation**, which is the intended outcome: the rule is settled,
> the prerequisite is not.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v5** — *re-read before editing; quote the version you approve.* **The clearing rule has been approved in every round; the deferrals are the contract around it.** |
| **Status** | *see `Spec-Status:` — canonical.* Split from `0002` §M3/§7b. **`0002` is a retrospective and must be closeable; this is a proposal and is not.** |
| **Internal reviewers** | research — **R2** (fail-closed rule) and **R3** (strict; not temporary) |
| **External review** | required — **counts are generated into `specs/STATUS.md` from `specs/reviews.py`; this row states none.** It said *"two rounds complete"* while `reviews.py` recorded three, in a project that built the generation to stop exactly that. |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

**A staleness flag addressed to the user can be cleared by something that is not
the user.**

`needs_confirmation` renders as `[possibly stale — confirm before relying on
it]` (`graph.py:358`). It is **a question addressed to whoever is entitled to reaffirm the fact** —
v1 said *"the party who stated it"*, and §6a establishes the mechanism cannot
prove the original speaker acted, only that an authorised principal did.

```python
if (prior.provenance.author_of_evidence
        == edge.provenance.author_of_evidence):
    prior.needs_confirmation = False
```

**Author class is not source identity and not evidence basis.** Two unrelated
`SYSTEM` processes are both `SYSTEM`; two unrelated third parties are both
`THIRD_PARTY`; and a system may restate a derived claim having observed nothing
new. **Same class ≠ same source · same speaker ≠ fresh evidence · repetition ≠
renewed observation.**

**This shipped in 0.4.5 as the fix for M3**, described as *"a staleness flag can
no longer be cleared by a different author"*. That is true and insufficient: it
closed cross-*class* clearing and left same-class clearing wide open, which is
the case that matters because **the host chooses the class**.

**The deeper defect, found by the second external review of `0002`.** The rule
that replaced it in `0002` §7b permitted *"a new user-authored observation"* to
clear the flag — while **§2c of the same document lists host-supplied `author`
as an uncontrolled input** whose adversarial case is *"host may claim
`system`"*. **The rule tested the very field we model as adversarial.** Both
sections were written by us, days apart, and neither was cross-read against the
other.

**Alternatives rejected.**

- **Same-class equality** (shipped). Closes the wrong half; see above.
- **Same `source_id`**, once `0006` lands. **Rejected by R3, and this is the
  subtle one:** *never model-supplied ≠ authenticated*. A host can give two
  unrelated statements one `source_id`, and same-source reinforcement would then
  clear staleness on evidence with **no common source**. It grants exactly what
  the strict rule withholds.
- **A `confirmed_by` parameter on `remember()`.** Rejected on the governing
  principle below — it is another field, and fields are what failed.

---

## 2. Field contracts touched

| field | read / written | contract | preserved? |
|---|---|---|---|
| `Edge.needs_confirmation` | set by `expire()`; **cleared by `confirm()` only, after this change** | "an **authorised principal** must explicitly reaffirm this edge through `confirm()`" — v1 said *"the party who stated this should re-affirm it"*, which the mechanism does not establish (§6a) | **restored** — currently cleared by parties that did not state it |
| `Provenance.author_of_evidence` | read by the rule being **removed** | authorship of evidence | **unchanged** — this spec stops *relying* on it for authority, it does not alter it |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **host/model `author`** on `remember` | enum-rejected | enum-rejected | enum-rejected | **`author="user"` on model-authored text** — and `remember` is `@server.tool()`, so **the model reaches this directly** | **C1** — no value of `author` clears the flag |
| **`source_id`** (future, `0006`) | — | — | — | host reuses one id across unrelated sources | **C1** — no field clears the flag, whatever it is |
| **`actor`** on `confirm()` | defaults `user` | — | — | mislabelled | **C2** — `actor` is recorded, never load-bearing; the **call** is the evidence |
| **call frequency** | — | — | — | repeated `confirm()` to hold a fact fresh forever | **audited, not limited** (§6b). A host with API access can do this by design; the record makes it **visible**, which is the part veracium can provide. Rate limiting is host policy |

> **Template rule this spec is the first to follow** *(research, 2026-08-01;
> proposed as a `Process-Change`)*: **a rule that relies on an input listed in
> §2c must name that row and say why it is safe to rely on it here.** This spec
> relies on **none of them** — which is the whole design.

## 2c-ii. Assertions about reach

| assertion | command | result |
|---|---|---|
| the shipped rule compares class only | `sed -n '119,121p' src/veracium/graph.py` | `==` on `author_of_evidence` |
| `author` is model-reachable | `grep -n "@server.tool" src/veracium/mcp_server.py` | `remember` · `recall` · `answer` · `maintain` |
| **`confirm()` is not** | same command; `grep -n "add_parser" src/veracium/cli.py` | absent from both — **host API only** |
| the flag reaches the model | `grep -n "possibly stale" src/veracium/graph.py` | `:358` |

---

## 3. Trust-class matrix — REQUIRED, blocking

**Two effects, not one.** v1 wrote a single **BLOCK** column, which was
ambiguous: a restatement blocked from *clearing* the flag still advanced
liveness, and that decides whether the flag is ever **set** (§3d).

| candidate | clears the flag? | advances liveness? |
|---|---|---|
| **`confirm()`** — host API, not model-reachable | **yes** | yes |
| `remember(author="user")`, same value | **no** | **unchanged — `0012`** |
| `remember(author="system")`, same value | **no** | **unchanged — `0012`** |
| third-party restatement | **no** | **unchanged — `0012`** |
| cross-class restatement | no *(0.4.5)* | **unchanged — `0012`** |
| `expire()` · consolidation · dedup · wiki | **no** | no — maintenance never refreshes |
| same `source_id` *(future, `0006`)* | **no** | **unchanged — `0012`** |

**The liveness column says `unchanged` rather than a rule**, because this spec
does not have one. v2 filled it from the supersession ladder and the result
contradicted this very table in two rows — `third_party → third_party` and
`third_party → user` both renew under authority and are denied here.

> **The governing principle:** *an act through a dedicated entry point is
> evidence; a field asserting who acted is not.* **Add an entry point, not a
> parameter.**

**And a distinction integrators mistake:** a user who agrees with a third-party
claim has produced **new user evidence**, which belongs in `remember()`.
`confirm()` is not a mechanism for adopting untrusted content — it reaffirms
what is already there, at the trust it already has.


## 3d. Clearing is not the only way to defeat the flag — and that is `0012`

**Measured.** `expire()` ages against `observed_at` and reinforcement advances
`observed_at` unconditionally, so repeated restatement keeps a fact permanently
fresh and the flag never fires:

```
SLOW relation, lifetime 120 days, edge 200 days old
control, no restatement       -> needs_confirmation = True
4 THIRD_PARTY restatements    -> needs_confirmation = False
```

**A party that cannot clear the flag can prevent it appearing**, and the
restatements are the class §1 treats as adversarial.

**v2 tried to fix this here, with recorded effective authority, and the second
external review rejected it. Correctly.** Authority answers *how strongly may
this evidence affect trust decisions*; it does not answer *did this source
observe the fact again*. **That is this spec's own error one level up** — §1
rejects same-author-class because unrelated sources share a class, and unrelated
sources share an authority rung too. It also contradicted the matrix below and
depended on `0003`, which is not accepted.

> **Moved to `specs/0012`.** `0008` closes the clearing path and **claims
> nothing about liveness.** §8 says so.

**Why it cannot be a smaller fix here:** reinforcement **discards** the incoming
edge today, so *"store the incoming observation as its own evidence"* is a new
representation, not a narrower version of this change.

---


## 4. Behaviour

Delete the conditional at `graph.py:119-121`. Reinforcement continues to refresh
**liveness** (`observed_at`) **unchanged — that behaviour is `0012`'s subject,
neither endorsed nor altered here** — and to retain confidence per `0002` M5 T1;
it stops
touching `needs_confirmation`.

**`confirm()` is unchanged** and already carries the correct guard — only
assertable facts may be confirmed, because *"if the user affirms a claim, that
affirmation is new user-authored evidence and belongs in `remember()`"*.

**This is a restriction, and it is not temporary.** R3: `source_id` does not
lift it. What would is **provenance of the call, not of the claim** — recording
which entry point was used and requiring hosts to gate the privileged ones.
**That belongs in evidence-basis and is on no roadmap**; this spec should not
imply a relaxation it cannot deliver.

**Cost, stated plainly:** a genuine same-source restatement no longer clears the
flag, so a fact stays marked `[possibly stale]` until someone calls `confirm()`.
**The failure is additive and visible** — a caveat that should have gone away —
against **silent removal of a caveat that should have stayed**, which is what
ships today.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **C1** only `Store.confirm_edge()` may transition an **existing stored edge** from `needs_confirmation` `True → False` | **three checks.** `test_no_provenance_value_clears_staleness` — behavioural, over every provenance input · `test_add_edge_refuses_the_transition` — **runtime**: generic `add_edge()` rejects it, with **no context parameter that could authorise it** · `test_no_direct_writer_outside_confirm_edge` — AST inventory as *defence in depth*; it cannot see `model_copy(update=…)`, `setattr`, a reconstructed edge or deserialisation, which is why it is not the guard | CI |
| **C2** `confirm()` clears it | `test_confirm_clears_staleness` | CI |
| **C2a** `actor` is audit metadata and grants nothing | `test_actor_metadata_does_not_grant_confirmation_authority` — authority comes from the protected call path; v1's name (*"clears regardless of actor label"*) read as normalising arbitrary labels | CI |
| **C3** *(temporary — owned for replacement by `0012`)* reinforcement still refreshes liveness, **unchanged by this spec** | `test_reinforcement_still_advances_observed_at` — **the permission, not the prohibition.** A deletion drawn too broadly would remove liveness refresh along with the flag clearing, and no other test distinguishes them. **Whether this behaviour is right at all is `0012`. Marked temporary so an accepted `0008` does not later read as prohibiting the correction `0012` exists to make.** |
| **C4** maintenance never clears | `test_no_maintenance_op_clears_staleness` — property-based over random op sequences, asserting its registry against the **maintenance entry points reachable from `maintain()`/`lifecycle`**, *not* the `@store_mutator` surface. **Those sets are not equal**: the manifest's 28 sites include `ingest_event`, `correct`, `forget` and `import_memory`. **After implementation** it must also contain `confirm_edge` — which is *allowed* to clear — and must **no longer** contain `confirm()`'s independent `add_edge` and `add_episode` sites. **The count will change; it is regenerated and verified then, not asserted now.** The two inventories cross-check ownership and are never equated | CI |
| **C5** the flag reaches the model when set | `test_stale_marker_renders` | CI |
| **C6** the 0.4.5 reproducer stays fixed | `test_cross_author_restatement_does_not_clear` — regression, cross-class was the half 0.4.5 got right | CI |
| **C7** confirmation is **all-or-nothing** | `test_confirmation_is_atomic` — a store wrapper that fails the record write; **every edge field unchanged**, no episode | CI |
| **C8** replay and collision | `test_replay_returns_the_original_success` · `test_same_id_different_request_conflicts` · `test_concurrent_duplicates_commit_once` — one mutation, one episode, one record | CI |
| **C9** audit metadata is validated **before** any mutation | `test_invalid_call_path_or_correlation_id_rejects_before_mutation` — closed enums, length and charset | CI |
| **C10** **every** `Store` backend refuses the transition through `add_edge()` | `test_add_edge_transition_guard` — a **backend conformance test** run against each implementation, not a SQLite detail | CI |
| **C11** retention, erasure and export | `test_forget_user_deletes_and_counts_confirmations` · `test_export_excludes_confirmations` · `test_invalidated_edge_keeps_its_confirmations` | CI |
| **C12** schema-version compatibility gate | `test_older_build_cannot_open_a_confirmations_store` — **`0007`**; without it an older build ignores the table and clears unaudited | CI |

**C3 is the one to write first.** The change is a deletion, and a deletion that
over-reaches would remove liveness refresh along with the flag clearing — which
no test currently distinguishes.

---

## 6a. What `confirm()` proves, and what the host must supply

**Finding 4: `confirm()` is a call path, not proof that a user affirmed
anything.** v1 argued it is safe because it is absent from the bundled MCP tool
list and the CLI. **That is true and it is not the same claim.** A host service,
a background job, or a custom model-facing tool the host writes can all call the
same API.

> **The contract, stated conditionally because that is what is true:**
> **veracium treats a call to `confirm()` as confirmation.** The host must
> expose that operation **only** through an authenticated, intent-bound action
> by the principal whose edge is being changed.

**Host obligations — the integrator's half, and it is not optional:**

| obligation | why |
|---|---|
| authenticate the principal | veracium cannot; it sees a function call |
| authorise for **that store and that edge** | a principal may be authenticated and still not own the edge |
| bind to explicit intent | a background job is not a reaffirmation |
| replay protection | a re-sent request is not a second confirmation |
| **never expose it to model control** | the whole boundary; a model-callable `confirm()` returns us to 0.4.5 |

**`actor` remains audit metadata and grants nothing** (C2a). It is retained
rather than removed because `record_outcome` beside it validates actor↔outcome
pairing and a silent removal would break callers — **but a caller could
reasonably read it as authorisation, so the spec says plainly that it is not.**

**Finding 5 — the field's own meaning was overstated.** §2 defined
`needs_confirmation` as *"the party who stated this should re-affirm it"* —
**WITHDRAWN wording.** The mechanism proves no such thing: not that the original
speaker acted, not that a human did.

> **Narrowed:** *an authorised principal must explicitly reaffirm this edge
> through `confirm()`.*

**That matters for system-authored, third-party-derived, imported, and
non-human-principal edges**, where "the party who stated this" may not exist as
a caller at all.

---

## 6b. The confirmation audit record

**Finding 7: `confirm()` becomes the only clearing path, and v1 left its
auditability `pre-release`.** Making a transition the entire trust boundary and
leaving it unobservable is not a defensible pairing.

> **One primitive, and it is the only way the transition happens:**
> ```
> @store_mutator
> Store.confirm_edge(user_id, edge_id, confirmed_at, actor,
>                    call_path, correlation_id) -> Confirmation
> ```
> The **store** loads the edge, verifies ownership and current state, enforces
> the assertability rule, applies **every** confirmation mutation, and persists
> the record — **in one commit.**

**v3 defined two mechanisms and they were incompatible.** C1 named
`clear_needs_confirmation(edge, confirmation_context)`; §6b named
`confirm_edge(...)`. **A caller-constructible `confirmation_context` is another
field claiming authorisation** — exactly what §6a rejects — so it is gone.
**`add_edge()` refuses a `True → False` transition on an existing edge**, with no
context parameter that would let it through.

**Every trust-bearing mutation is inside the transaction**, not just the flag.
v3's operation covered the flag and the audit; `Memory.confirm()` also advances
`observed_at`, raises `confidence`, and writes an episode
(`__init__.py:507-517`), so a partial outcome was possible:

| inside the transaction | why |
|---|---|
| `needs_confirmation = False` | the transition being authorised |
| `observed_at = max(old, confirmed_at)` | confirmation *is* an observation; splitting it lets the flag clear while currency does not move |
| `confidence = max(old, 0.9)` | same |
| the **confirmation record** | mandatory; **if it cannot commit, the confirmation fails and the flag stays set** |
| the confirmation **episode** | part of confirmation behaviour today; dropping it silently would be a behaviour change nobody asked for |

**`actor` is in the request because the episode needs it.** Today's summary is
`f"({actor}) confirmed …"` (`__init__.py:513`), so a store handed only
`(user_id, edge_id, confirmed_at, call_path, correlation_id)` **cannot reproduce
existing behaviour** — v4 froze a signature that could not do its own job.

**And that exposed a hole I had left open.** `actor` was called audit metadata,
kept out of the mandatory record, and **embedded unconstrained in a
content-bearing episode** — so a host could put prose, or a memory, in `actor`
and bypass every constraint §6c places on `call_path` and `correlation_id`.
**`ConfirmationActor` is now a closed enum**, like `call_path`.

**`Memory.confirm()` is not "unchanged", and v3 said it was.** Its persistence
mechanism moves from four independent store calls to one operation.

**The existing optional `AuditLog` does not satisfy this.** It is best-effort and
swallows failures (`_record`), which is right for telemetry and wrong for the
sole clearing transition. **The `confirmations` table is separate and
mandatory.**

**C-Q1 is resolved by this**, not deferred.

---

## 6c. The public contract, frozen

**Finding 3: v3 changed the persistence mechanism and never said what callers
see.**

```python
Memory.confirm(
    user_id: str,
    edge_id: str,
    *,
    date: str | None = None,
    actor: str = "user",                       # audit metadata; grants nothing
    call_path: ConfirmationCallPath = ConfirmationCallPath.HOST_API,
    correlation_id: str | None = None,
) -> ConfirmationResult
```

**Backward compatible.** Existing callers keep working: both new parameters have
defaults. **`principal` is `user_id`** — the store is tenant-scoped, so a
separate principal would be a second identity with no source of truth.

**`correlation_id` is optional, and the cost of omitting it is stated rather
than hidden:** supplied, it gives replay protection across an unknown commit
outcome; absent, the library generates one and **there is none.** A host that
retries a request whose result it never saw needs to supply it.

### Idempotency — the request identity, frozen

**v4 said "same payload" without saying what the payload is**, and the gap has a
concrete failure: with `date` omitted, the server picks the time, so a retry
picks a *different* time. If the normalised instant is part of the identity the
retry conflicts; if only `(user_id, edge_id)` is, then a changed `call_path` or
`actor` is silently accepted as the same request.

> **The canonical request is:**
> ```
> user_id · edge_id · call_path · actor · rule_version
> caller_date  — the CALLER's string, or the sentinel OMITTED
> ```
> **The caller's input, never the derived instant.** `OMITTED` is a value, so
> two date-less retries are identical requests.

**The correlation id is checked before a timestamp is generated.** On replay the
**stored** `confirmed_at` is returned, not a fresh one. A digest of the canonical
request is persisted so a true replay is distinguishable from a collision.

| case | result |
|---|---|
| same id, same canonical request | **the original success**, `replayed=True` |
| same id, different canonical request | **integrity conflict** |
| concurrent duplicates | **exactly one** mutation, one episode, one record |

**Scope: `UNIQUE(user_id, correlation_id)`, not global.** v4 made it global, and
with a `≤64 char` format that permits ordinary short strings **one tenant can
consume identifiers another needs** — a cross-tenant denial path, and the
differing conflict behaviour leaks that an id exists elsewhere. **The request is
already principal-scoped and a cross-principal retry is never the same request.**

### The return shape (finding 4)

**`confirm()` returns a dict today** (`__init__.py:525`), and callers subscript
it, `json.dumps` it, and type-check it. **v4 replaced it with an undefined
`ConfirmationResult` and called that backward compatible.** It is not.

> **The contract stays a mapping:**
> ```python
> {"confirmed": str, "valid_from": str, "confirmed_at": str,
>  "correlation_id": str, "replayed": bool}
> ```
> Three existing keys keep their meaning; two are added. **On replay every value
> is reconstructed from the stored record**, not from an edge that may have
> changed since — otherwise "the original success" is not what is returned.

### Audit metadata is constrained, not merely discouraged (finding 4)

**v3 called the record content-free while two of its fields were free-form host
strings.** A host could put a whole sentence — or a memory — in `call_path`, and
the table would quietly become a content store.

| field | constraint | rejection |
|---|---|---|
| `call_path` | **closed enum** `ConfirmationCallPath` — no free text | unknown value raises |
| `correlation_id` | opaque, **≤ 64 chars**, `[A-Za-z0-9._:-]` | anything else raises |
| `user_id` · `edge_id` | opaque identifiers, unchanged | — |
| `confirmed_at` | **the normalised UTC instant**, not the caller's string — following the 0.4.7/0.4.8 date fixes | — |

**A policy that hosts should not put content in strings is not a constraint.**
This is the same free-form-metadata problem `actor` already demonstrated.

---

## 6d. The store contract, and what it costs every backend

**Finding 6: `Store` is a replaceable interface**, so this is not a SQLite
change.

> **Two obligations, and v4 only stated the first:**
>
> 1. **`confirm_edge` joins the interface as `@store_mutator`.** A backend that
>    cannot write the edge and the confirmation atomically **must raise**, not
>    degrade.
> 2. **`add_edge()` must compare the persisted prior state and reject
>    `needs_confirmation: True → False`** when replacing an edge of the same id.
>    It must also **reject a change of `user_id`** — ownership is not
>    transferable through the upsert path.

**Both are backend conformance tests (C10), not SQLite implementation details.**
A custom store could implement an atomic `confirm_edge()` and still accept a
reconstructed edge with the flag cleared through `add_edge()` — satisfying the
new signature while **violating the headline invariant.**

**SQLite:** a `confirmations` table, **`UNIQUE(user_id, correlation_id)`**,
indexed on `edge_id`, created by the `0013` v1→v2 migration. *(Corrected
2026-08-03: this line said `UNIQUE(correlation_id)` — global — while §6c's
round-4 ruling is explicitly tenant-scoped, and said `CREATE TABLE IF NOT
EXISTS` — the model `0007` replaced. Found by `0013`'s first external review;
§6c was always the ruling, this line had drifted from it.)*

| question | answer |
|---|---|
| edge invalidated | records **retained** — the confirmation happened |
| edge physically removed | records removed with it |
| `forget_user()` | deletes them **and counts them** in its result |
| export / import | **excluded** — a confirmation is a fact about this store, not about the memory |
| audit inspection | `confirmations_for(user_id, edge_id)` — read-only |

> **Implementation prerequisite: `specs/0007` must be accepted, and ship first
> or atomically with this.** Declared as `Spec-Requires: 0007` at the top, and
> **the gate enforces it** — a commit citing an `accepted` `0008` fails while
> `0007` is unresolved.

**⚠️ This is load-bearing, not administrative.** `CREATE TABLE IF NOT EXISTS` is
not a migration story: an older build opens the newer store, **ignores the table, and clears the flag
unaudited through the old reinforcement path** — defeating both of this spec's
guarantees at once. **Accepting `0008` alone would authorise that cut.**
**Fifth spec to need `0007`, which has never been reviewed.**

---

## 7. Failure modes and reversibility

**Failure mode is a caveat that outstays its welcome** — a fact stays marked
`[possibly stale]` until someone calls `confirm()`. Additive and visible,
against silent removal of a caveat that should have stayed.

**Reversibility, corrected.** v1 said *"no data is written or destroyed;
existing values stay exactly as they are"* and that was wrong in a way that
matters:

> **A new `confirmations` table and a new `Store` method** (§6b, §6d).
> `Memory.confirm()` gains two defaulted parameters — **additive, existing
> callers unaffected.** No existing table or field changes and no stored edge or
> episode is migrated. **The implementation is rollbackable, but behaviour
> during deployment changes persisted edge state**,
> and reverting does not reconstruct the counterfactual the old rule would have
> produced.

Before, reinforcement wrote `needs_confirmation=False`; after, it leaves `True`
persisted. **After a rollback we cannot tell which flags the old behaviour would
have cleared during the intervening period** — the safer flags simply remain set
until a later `confirm()` clears them — **reinforcement no longer changes the
flag at all.** **That is the
right direction to fail, and it is still not "no data changes".**


## 8. Claims and limits

**Claim, and it is one sentence on purpose:** *only `Store.confirm_edge()` may
transition an **existing stored edge** from `needs_confirmation = True` to
`False`.*

**"Transition on an existing edge" is precise on purpose.** New edges are
created with `False`, and import and deserialisation load `False` values — those
are not clearing events, and v3's wording implied every `False` should have a
confirmation record behind it.

**Liveness is explicitly out of claim.** §3d measures a second way to defeat the
warning — repeated restatement prevents the flag being set at all — and **this
spec does not fix it.** `specs/0012` owns it. **A reader must not take this
spec as closing the staleness boundary; it closes one of its two doors.**

**v2 claimed both doors and the second external review rejected the mechanism**
— it used supersession authority as a proxy for renewed observation, which is
this spec's own error one level up.

**What this does NOT establish:**

- **Not that a user confirmed anything.** veracium sees a call, not a person.
  **The guarantee is conditional on the host obligations in §6a** — and if the
  host exposes `confirm()` to a model, this spec buys nothing.
- **Not per-author staleness.** `needs_confirmation` is one boolean for the
  whole edge; `0002` Q4 would dissolve this structurally rather than fence it.
- **Not why the flag was set.** `expire()`'s CONFIRM behaviour is untouched.
- **Not anything about liveness.** §3d's bypass is open and owned by `0012`.
  **v2 claimed this and the mechanism was rejected**; nothing replaced it here.


## Review closure

**Set `accepted` 2026-08-02 19:27 UTC by dev, under `PROCESS.md` §4a: external review is
required and dev sets the status once the review's comments are satisfied.**

**Four external rounds. The clearing rule was approved in all four**; every
deferral was about the contract around it. Every finding raised is closed below
with something openable — a section, an invariant, a test, or a commit.

**What `accepted` does and does not mean here.** It authorises implementation of
**this spec's rule**. It does **not** mean the code can land: `Spec-Requires:
0007` is enforced by the gate, and `0007` is `draft`, so a commit citing this
spec still fails. **That is the intended outcome** — the invariant is settled,
the prerequisite is not.

### Round 1 — 7 findings

| # | finding | closed by |
|---|---|---|
| 1 | reinforcement can prevent the flag being set | §3d, **measured**; owner `specs/0012` |
| 2 | matrix conflates clearing with liveness | §3 — two columns |
| 3 | C1 tested only `EvidenceAuthor` | C1 — behavioural + runtime + AST |
| 4 | `confirm()` is a call path, not proof | §6a host obligations |
| 5 | field contract overstated the reaffirming party | §2 row, narrowed |
| 6 | reversibility claim incorrect | §7 |
| 7 | audit/rate policy unresolved | §6b; C-Q1 resolved |

### Round 2 — 11 findings

| # | finding | closed by |
|---|---|---|
| 1–3, 7 | authority is not entitlement to renew; contradicts the matrix; `0003` not accepted | **rule withdrawn**; `specs/0012` §2 |
| 4–6 | incoming-evidence representation · §4 contradiction · the withdrawn rule's test coverage | `specs/0012` §3 — the invariant those findings attached to no longer exists here |
| 8 | AST writer check bypassable | C1 — runtime guard, AST demoted |
| 9–10 | audit atomicity and schema | §6b, §6d |
| 11 | `call_path` undefined | §6c — closed enum |

### Round 3 — 8 findings

| # | finding | closed by |
|---|---|---|
| 1 | two incompatible mechanisms | `Store.confirm_edge()` sole primitive; context parameter removed |
| 2 | transaction omitted other effects | §6b table — flag, `observed_at`, `confidence`, episode, record |
| 3 | public API undefined | §6c |
| 4 | "content-free" fields were free-form | §6c constraints |
| 5 | replay under unknown commit | §6c idempotency |
| 6 | store contract incomplete | §6d |
| 7 | C4's boundary wrong | C4 — maintenance entry points, not the mutator surface |
| 8 | claim not transition-specific | §8 |

### Round 4 — 9 findings

| # | finding | closed by |
|---|---|---|
| 1 | signature could not write the episode | `actor` in the request; `ConfirmationActor` closed enum |
| 2 | idempotency identity undefined | §6c — canonical request, `OMITTED` sentinel |
| 3 | global correlation ids unsafe | `UNIQUE(user_id, correlation_id)` |
| 4 | return not backward compatible | §6c — mapping contract retained |
| 5 | storage contract untested | **C7–C12** |
| 6 | `add_edge()` guard not formalised | §6d — backend conformance, C10 |
| 7 | `0007` prerequisite | `Spec-Requires: 0007`, **gate-enforced** (`feb81ff`) |
| 8 | manifest claimed a future state | C4 — future tense |
| 9 | review metadata drifted | header row states no counts |

### What remains open, and is not claimed

- **The §3d liveness bypass** — measured, unfixed, `specs/0012`.
- **Nothing is implemented.** C1–C12 are unwritten; the source still clears on
  same-author reinforcement and the historical reproducer is `xfail`.
- **The guarantee is conditional** on the §6a host obligations.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~**C-Q1**~~ | **RESOLVED in §6b, not deferred.** Every `confirm()` writes a content-free audit record; repeated confirmation is allowed without limit, because veracium cannot distinguish a legitimate re-affirmation from an automated one and **a guessed limit would substitute our judgement for the host's while still not detecting misuse.** The record makes misuse visible, which is the part we can provide. | resolved | dev | — |
| ~~C-Q2~~ | **RULED 2026-08-01 (Quentin): no release-note correction.** The 0.4.5 note is accurate as written — cross-author clearing *was* closed. The residual same-class case is this spec's subject and ships as its own fix. **Not blocking.** | resolved | Quentin | — |
