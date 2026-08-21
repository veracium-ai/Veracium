# Veracium — External Reviewer's Guide

*A guide for reviewing Veracium's code, tests, and specifications. Read Parts 1–3 for
orientation, Parts 4–7 for the review method, Part 8 for what past reviews taught us, and
Part 9 for the distilled checklist.*

---

## Part 1 — What Veracium is

**Veracium is a memory layer for AI agents.** It turns a stream of interaction events (chat
turns, sent/received email, tool and document output) into a typed, **provenance-tracked**
knowledge graph, and serves **grounded recall** back to a model — answers backed only by
memory the system is willing to assert.

The product's distinguishing thesis, and the thing a reviewer is really auditing, is a
**trust position**:

- **Memory is a trust surface.** Not all remembered content is equal. Content the *user*
  authored, content the *system* authored, and content a *third party* authored (an email, a
  scraped document, a tool result) carry different authority. Veracium tracks *who authored
  the evidence* for every fact and *what lower-trust material that evidence embeds*, and it
  refuses to let low-trust content be asserted as fact.
- **Maintenance is an attack surface.** The subtle bugs are not in the write path — they are
  in the *maintenance* operations that run later (expiry, consolidation, supersession,
  deduplication, import). Two shipped security advisories were the same shape: a maintenance
  operation crossing a trust boundary the write path guards correctly. Much of the spec corpus
  exists to close that class.
- **Provenance-first.** Every stored fact records how it is known (first-known vs
  last-observed dates, author, disclosure class, source type, and — newest — which *source*
  produced it). The system's job is to never make a claim its provenance doesn't support.

**Threat model.** Third-party-authored content is treated as adversarial input. The canonical
attacks are: (a) **laundering** — getting third-party content extracted and then asserted as
if the user said it; (b) **maintenance-path bypass** — using expiry/consolidation/import to
move low-trust content across a boundary the write path blocks; (c) **impersonation** — a
model or host naming a trust-bearing field (author, source) to inflate its own authority.

**Delivery.** A Python library (`Memory` API), an MCP server, and a CLI. It is **bring-your-
own-LLM** (a `Complete` callable) — Veracium never owns credentials or model choice, which is
why it deliberately cannot meter tokens the host doesn't surface.

---

## Part 2 — The parts (architecture)

Data flows **write → store → read**, with **lifecycle** maintenance and **portability**
crossing the store. Trust classes thread through all of it.

### The trust model (`schema.py`, `authority.py`) — read this first
- **`EvidenceAuthor`** — exactly `USER`, `SYSTEM`, `THIRD_PARTY`. Who authored the evidence. *(Corrected external round 3: this guide previously listed an `ASSISTANT` member the shipped enum does not have — assistant-generated content is a deferred trust class, 0001 in the status table below.)*
- **`Disclosure`** — `MENTIONABLE` (assertable) → `USE_ONLY` (may inform, never asserted) →
  `QUARANTINED` (structurally isolated). The gate keys on this.
- **`SourceType`**, **`Provenance`** — `observed_at` (last recorded) vs `valid_from` (first
  known), `evidence_ref`, `confidence`, `derived_from` (the lower-trust material the evidence
  embeds; trust is capped at `min(author, derived_from)` — this closes "system-event
  laundering"), and now `(origin, source_id)` (source identity, `specs/0006`).
- **The authority ladder** (`authority.py`, `specs/0003`): `effective = min(AUTH[author],
  AUTH[derived_from])`; a differing value supersedes a prior only when its effective authority
  ≥ the prior's, else the retirement is **refused** and both values stay live.

### Write path
- **`ingest.py`** — one event → typed edges + a dated episode. The host declares `author`;
  `ingest` sets disclosure by structural rule (a third-party *claim* is quarantined; a
  third-party *inference* is use-only). This is where laundering is stopped at write time.
- **`graph.py`** — supersession (functional relations hold one current value), absorption
  (T1 dedup), and recall subgraph selection.

### Store
- **`store/sqlite.py`** — edges/episodes serialised as JSON blobs in a versioned SQLite
  schema. `edges(active_only=True)` is a load-bearing default (it keeps absorption from
  re-touching an invalidated prior).
- **`store/schema_version.py`** (`specs/0007`) — the on-disk schema is **declared, versioned,
  and shape-verified**, not inferred. Opening a store runs a decision table (refuse-unknown /
  adopt-v1 / migrate / create) under a write lock; a store's *shape* (a manifest digest of
  `sqlite_master`) is checked against shipped **evidence**, so a zeroed `user_version` or a
  foreign file is refused rather than silently "fixed."
- **`store/migration.py`** (`specs/0013`) — offline, additive, forward migrations
  (`migrate_store()`), one step per version, each revalidated against the head schema before
  commit. `SCHEMA_VERSION` is not restated here — read it from `src/veracium/store/schema_version.py` (`SCHEMA_VERSION`); a number frozen in this guide goes stale (round-2 bin-(b), 0015).

### Read path
- **`graph.subgraph_for_query`** → **`gate.py`** (abstention: what may be asserted; the gate
  asserts only grounded, mentionable memory) → **`compile.py` + the wiki** (a curated one-
  value-per-fact view, cached and invalidated on trust-reducing changes) → **`proactive.py`**
  (unsolicited recall — dangerous because it injects text into model context with *no user
  turn*, so a regression there volunteers `use_only` material nobody asked for).

### Lifecycle (the "overnight" job)
- **`lifecycle.py`** — `expire()` (volatility-driven lapse/decay/confirm) and `consolidate()`
  (crash-safe compaction of cold episodes, `specs/0010`). This is the maintenance surface the
  advisories came from.

### Portability & source identity
- **`portability.py`** — export/import across a trust boundary. An export is *data*, not
  authority; import treats the file as untrusted. `FORMAT_VERSION` is not restated here — read it from `src/veracium/portability.py`; a number frozen in this guide goes stale (round-2 bin-(b), 0015).
- **`source_identity.py`** (`specs/0006`) — the canonical `source_identity_digest` primitive
  and `resolve_origin` chokepoint; the durable per-store `store_identity` origin.

### Surfaces
- **`__init__.py`** (`Memory` API — `remember`/`recall`/`answer`/`maintain`, plus `confirm()`
  and `correct()`), **`mcp_server.py`**, **`cli.py`**, **`introspect.py`** (per-user
  inspection), **`telemetry.py`**/**`audit.py`** (consented, content-free), **`selfcheck.py`**.

---

## Part 3 — The governance model (READ BEFORE REVIEWING ANYTHING)

Veracium is **spec-driven**. Behaviour on the trust surface is not changed by a PR alone; it
is changed by a **specification** that has passed review. The rules live in `specs/PROCESS.md`.

### The spec lifecycle
`Spec-Status: draft → in review → accepted`. **Only `accepted` authorises implementation.** An
accepted spec MUST carry a `## Review closure` section (the per-round acceptance ledger). A spec
cannot be accepted while a `Spec-Requires:` prerequisite is unresolved.

### The guarded surface + the `Spec:` trailer gate
A commit that touches the **trust surface** must cite the spec that authorises it, or a typed
exception. The guarded files (`check_spec_reference.py`):

`schema.py` · `graph.py` · `ingest.py` · `lifecycle.py` · `gate.py` · `portability.py` ·
`__init__.py` · `store/sqlite.py` · `proactive.py` · `introspect.py` · `mcp_server.py`
(and the schema/migration modules in practice).

A guarded commit carries either `Spec: specs/NNNN-….md` (an accepted spec, deps accepted) or
`Spec-Exception: <docs-only|test-only|revert|behavior-preserving-refactor|security-hotfix>` +
`Spec-Exception-Reason:`. CI fails the build otherwise. (`compile.py` is deliberately excluded —
a derived view whose inputs are already guarded.)

### The spec corpus (your map)
| Spec | Subject | Status |
|---|---|---|
| 0001 | generated-content trust class (`ASSISTANT`) | deferred |
| 0002 | the maintenance provenance invariant (the retrospective parent) | deferred |
| 0003 | supersession authority (the ladder) | **accepted, shipped 0.6.0** |
| 0004 | derived views must not outlive a revoked trust decision | draft |
| 0005 | import has no trust boundary | draft |
| 0006 | source identity — `(origin, source_id)` | **accepted, shipped 0.7.0** |
| 0007 | on-disk store schema versioning | **accepted, shipped 0.5.0** |
| 0008 | what may clear `needs_confirmation` | **accepted, shipped 0.5.0** |
| 0009 | outcome authorship is append-only history | **accepted, shipped 0.5.0** |
| 0010 | crash-safe consolidation | **accepted, shipped 0.5.0** |
| 0011 | subject-scoped entitlement | draft (2 blocking Qs) |
| 0012 | who may renew a fact's currency | **accepted, implemented** |
| 0013 | on-disk store migrations | **accepted, shipped 0.5.0** |
| 0014 | maintenance attribution (a consumed contributor must leave a record) | **accepted, implemented** |
| 0015+ | (see `specs/STATUS.md` — the generated index is the live authority; this table is a snapshot and `STATUS.md` wins on any disagreement) | — |

### The mechanical gates (`tests/test_spec_gate.py`, ~59 tests)
The process is enforced by tests, not vigilance. The ones a reviewer should know:
- **Guarded-file gate** — a trust-surface commit must cite an *accepted* spec or a typed
  exception; renaming out of a guarded path, deleting a guarded file, a prose line masquerading
  as a trailer, an unresolvable range — all caught.
- **`test_an_accepted_spec_must_carry_a_review_closure`** / **`…_authorises_implementation`** /
  **`…while_its_prerequisite_is_unresolved`** — the acceptance contract.
- **`test_every_store_mutation_site_carries_a_verdict`** — every store mutator call site is
  enumerated in a generated manifest with an operation class, the trust fields it touches, and a
  verdict backed by a real test (the 0002 audit manifest). Coverage is an *artifact*, not a claim.
- **`test_status_prose_is_generated_from_the_structured_records`**, **`…authority_tables_are_
  generated_from_the_ladder`**, **`test_review_archives_are_named_and_indexed`** — every human-
  readable summary is *derived*; drift fails the build.
- **`test_no_spec_cites_an_invariant_it_does_not_define`**, **`…names_a_module_that_does_not_
  exist`**, **`test_no_withdrawn_rule_is_stated_as_live_spec_text`** — spec-text integrity.

---

## Part 4 — How to review the CODE

**Start at the trust surface** (the guarded files), not the entry points. Ask of each change:
*what caller-supplied value does this decide the permission of, and can a lower-trust party
influence it?*

### The recurring failure classes to hunt
1. **Laundering** — third-party content reaching an assertable (`MENTIONABLE`) edge or the
   grounded recall block. Check `ingest` disclosure routing, `derived_from` capping, the gate,
   `proactive`, and consolidation provenance.
2. **Maintenance-path bypass** — a boundary the write path guards being crossed by
   `expire`/`consolidate`/supersession/absorption/import. Both advisories were here.
3. **Absence-at-a-boundary** — a field that is optional (`source_id`, `origin`, `derived_from`)
   whose *absent* case is under-specified at some boundary (compare, digest, import, export).
   In `0006`, **all three** defects reviewers/authors found were absence cases.
4. **Unattributed transfer** — a maintenance op consuming a contributor (reinforcement,
   absorption, consolidation) without leaving a record of what it consumed (`0014`).
5. **Impersonation** — a model- or host-supplied field standing in for authenticated authority.
   The rule: *an act through a dedicated entry point is evidence; a field asserting who acted is
   not.* (`source_id` is host-supplied but **never** authenticated — verify the spec never
   claims otherwise.)

### The found-in-fix checklist (this is the highest-leverage lens)
Repeatedly, a review round's finding was a **shallow spot in the previous round's own fix**.
Apply this to every change that closes a finding:
1. **Recurse the property.** A fix that establishes *immutable / total / validated / canonical /
   closed / fail-closed* is almost always **recursive** — prove it at every nested layer (an
   "immutable" container of mutable dicts is not immutable).
2. **Enumerate the matrix, not the named cell.** If the fix adds a case, confirm every cell of
   states × inputs is reachable and honest — not only the one the reviewer named.
3. **Every escape and branch, not just the happy path** — named escapes and error paths get the
   same terminal record / closed outcome / rollback.
4. **Audit new cross-module trust** — a fix relying on another module's return/callback/cleanup
   must have that behaviour guaranteed *under failure*, not just on the sunny path.
5. **Carrier-completeness** — if the fix changes a value/field/state/case, update **every**
   representation of it (the record *and* the exception that stands in for it; the enum *and* the
   mapping that branches on it; the schema *and* the docstring; the writer *and* the validator).
   Grep the new name across the module; every hit is a carrier to check.
6. **Write the adversarial regression, not the conformance test** (Part 5).
7. **Diff-scan as an adversary** — re-read *only the diff* and ask "what does this newly assume
   or newly expose?"
8. **The fix's name is a claim** — assert the property the name promises, at the site it names
   (a handler *named* "classify by phase" that actually tested "commit facts exist" read true and
   behaved wrong).

---

## Part 5 — How to review the TESTS

### The executable-check convention
Every spec invariant (`I1`, `A4`, …) names a **concrete, existing test**. The gate
`test_a_spec_claiming_a_test_is_measured_today_must_have_it` enforces that a spec cannot claim a
passing test that doesn't exist. When reviewing, map the invariant surface to the tests and
confirm each invariant is *actually* exercised, not just named.

### Adversarial regression, not conformance
A test that only exercises the happy path passes while the attack path stays open. The standard
is: for each property, **inject the failure the reviewer would** — mutate the frozen thing, feed
nested garbage, force the escape, make cleanup raise, exercise the *other* carrier. Example: for
"consult-and-discard records even an empty payload," the test drives a consumption where *no
value moves* and asserts a record still exists.

### What "green" means, precisely
- **`COLLECTED.txt` is the authoritative expectation** — this guide carries NO frozen counts
  (R11-4/0014: a hardcoded count triple here drifted three releases behind the suite and
  contradicted the package it shipped in; counts live where they are measured). Each package's
  `COLLECTED.txt` records the exact command, environment, and pass/skip/xfail line.
- **Where it is measured — ONE canonical protocol, corrected at external round 10
  (R10-1):** in the AUTHOR'S COMMITTED GIT CHECKOUT, at the commit both carriers name,
  with `specs/seal_package.py` running the suite before it builds `COLLECTED.txt`. This
  paragraph previously described a separate extracted copy with no `.git`, and claimed
  the measured line therefore already reflected the reviewer's shape. **It does not, and
  it never did** — the sealer measures `ROOT`. The observable consequence is the
  git-dependent tests: they EXECUTE in the sealed line and SKIP in your extraction, which
  is the largest single term in the delta between the two numbers.
  **Your run will differ from the sealed line, by design, and the skip inventory in
  `COLLECTED.txt` is what makes the difference reconcile.** Anyone comparing the two
  numbers should expect them to differ and check the decomposition, not the total.
- **Reconciling your own run:** `COLLECTED.txt` records the measured line AND the
  environment-conditional skip inventory — the named tests that skip or run depending on
  the host (git checkout present, coordination files present, qualified SQLite runtime,
  recorded runtime identity, root euid). Reconcile any delta between your run and the
  measured line against that named inventory; a delta NOT explained by a named
  conditional test is a finding. (R12-4: no frozen delta — the "+N" itself drifts.)
- **xfails are unbuilt-by-design** — regressions pinning not-yet-implemented behaviour of the
  spec under review. Their count varies by round; `COLLECTED.txt`'s line is the truth.
- `test_spec_gate.py` (~59 tests) is the process gate; it must be green before any package ships.

### Mechanical pre-send gates
Some invariants are checked **exhaustively/systematically**, not by example — because
enumeration has no cell to overlook. E.g. `test_terminal_facts_matches_the_independent_oracle`
enumerates a whole domain against a separately-written oracle; the 0002 audit manifest enumerates
every store mutator. When a change adds a validator with a small domain or a new failure seam,
the right move is to **extend the exhaustive gate**, not add one example test.

---

## Part 6 — How to review the SPECIFICATIONS

### Anatomy of a spec
A full spec carries: **§1 problem/motivation**, **§2 field contracts**, **§2c untrusted-input
matrix** (empty / malformed / unrecognised / adversarial per input, each with the invariant that
governs it), **§3 the finding at its sites**, **§3b authorization & scope**, **§4 behaviour (the
mechanical contract)**, **§5 regime analysis** (where does it behave differently — growth,
concurrency, cold/warm), **§6 invariants + executable checks** (the acceptance surface), **§7
failure modes & reversibility**, **§7a surfaces touched**, **§8 claims & limits**, **§10 open
questions**, **§11 Review closure** (once accepted).

### What makes a spec acceptable
- The **mechanical contract is complete** — a construction, not a description. ("Digest the pair"
  is not a spec; "domain-separated, length-framed SHA-256 over the resolved pair, one shared
  primitive" is.)
- Every **invariant is executable** and every **untrusted-input cell** is both reachable and
  honest.
- **Claims match limits.** The spec must not over-state (see below).
- **Cross-spec citations resolve** (`§4.6`, not a stale `§4.5`), and dependencies are accepted.

### The spec anti-patterns the process has caught — look for these
- **Superlatives surviving a narrowing ruling.** A claim like *"unforgeable"* or *"structurally
  incapable"* left in one section after another section (or a ruling) narrowed it. The failure
  is **semantic** (a claim contradicting the limits section), not lexical — a word-grep would
  fire loudest on the *corrected* documents. The house rule: **strike falsified text with a
  WITHDRAWN/OBSOLETE marker** (`lint_withdrawn.py`), never silently leave it.
- **Absence under-specified.** For every optional field, ask what happens when it is *absent* at
  every boundary it crosses. "Unknown is a distinct state and the floor, never a synonym for any
  attested value" is the principle that catches these.
- **Carrier-completeness in the spec** — a value changed in one representation (the §3 table) but
  not another (the §4a schema enum, the §5 regime, the §7a surfaces). Grep the value across the
  document.
- **Status prose contradicting itself** — a header asserting completion beside a ledger showing
  unimplemented work. Veracium's answer: **derive all summaries** from structured records
  (`findings.py`, `reviews.py`) so drift fails a test.

### The interface-freeze protocol (co-owned interfaces)
When two specs share a frozen interface (e.g. `0006`↔`0014`), a change to any frozen point needs
**both spec owners plus the reviewer**. A reviewer confirming such a freeze is asked to confirm
the **enumerated frozen points**, not to re-review two whole documents. The freeze sign-off is
**separate from** either spec's own acceptance.

---

## Part 7 — The review workflow

- **Packages.** Each review round ships a `git archive` tarball (`specs src tests pyproject.toml`)
  plus `COLLECTED.txt` (source commit, pytest version, node count, pass/skip/xfail, exit code) and
  a `sha256`. The tarballs are gitignored; a committed `specs/archives/INDEX.md` records each
  package's hash. **Verify the archived spec is byte-identical to what you were sent**, and re-run
  the suite in the extracted tree.
- **Rounds & dispositions.** A round returns *for amendment* (with numbered findings) or *accepts*
  (design frozen on a named invariant surface). Every round is recorded in `specs/reviews.py` — the
  single source of truth for review counts — and cross-checked against the archives on disk.
- **Findings.** Number them, tie each to the invariant or contract it breaks, and give a concrete
  failure (inputs → wrong output). The strongest findings reproduce against the code first.
- **Finite acceptance.** Review is *bounded*: when rounds stop finding architectural problems and
  start finding seams in the prior round's own fixes, the design is accepted on a **frozen
  invariant surface**, and further edges become implementation obligations, not new design rounds.
- **Coupled specs review as ONE package.** When specs carry mutual or directional
  `Spec-Requires` and one spec's central claim is CONDITIONAL on another (e.g. 0020/0021, where
  the read-time boundary's claim fails at the first maintenance run without the write-time
  companion), the round ships BOTH specs in one package with per-spec verdicts. The seam
  BETWEEN them is review surface — the strongest findings there are cross-spec attacks neither
  spec exposes alone. A spec that is *separable by design* (its own threat model, deferrable —
  e.g. an authentication upgrade to an isolation spec) is deliberately NOT bundled; bundling it
  would invite scope creep of the round.

### A standing request TO the reviewer (please answer in every round)

The package format above is ours, not gospel. In each round's response, please tell us:

1. **What additional artifacts would have made this review more robust?** Anything you wanted
   and didn't have — execution traces, a runnable repro harness for the spec's claims, a
   dependency-graph rendering of `Spec-Requires`, prior rounds' full texts, generated-artifact
   provenance, more of the tree than `specs src tests` — name it and we will supply it in the
   next round or explain why we cannot.
2. **What would you change about the archive itself?** Layout, naming, the `COLLECTED.txt`
   fields, hash coverage, anything that made verification slower or trust harder than it
   needed to be. Package-format findings are findings: we treat them with the same discipline
   as design findings, and past reviewer pushback has already reshaped this process
   (per-finding ledgers, byte-identity checks, the pre-seal SENT convention all originated as
   reviewer complaints).

---

## Part 8 — History of past reviews & lessons learned

Veracium has run **14 specs through the full process** (≈86 external review rounds). The concrete
stories are the best guide to where the bodies are buried.

- **0002 — the maintenance provenance invariant (8 external rounds, deferred).** The retrospective
  parent. Every one of the first several rounds found a **status claim contradicting another
  status claim in the same document** — a header asserting every maintenance finding was closed
  beside a ledger showing several still unimplemented; a review-count in the prose that disagreed
  with the number of rounds the document actually contained. Each was hand-corrected and the next
  appeared. **Lesson: never hand-maintain a summary** — the prose is now *derived*
  from `findings.py`/`reviews.py`, and a phrase-lint alone was proven insufficient (it passed
  while the header lied).

- **0003 — supersession authority (12 external rounds, accepted, shipped 0.6.0).** The **found-in-
  fix** saga: rounds 11–12 kept raising findings that were not pre-existing bugs but **shallow
  spots in the previous round's own fix** — an "immutable" `AuditState` that was an immutable
  container of *mutable* dicts; validators made "total" only one layer deep; a new field added to
  the terminal record but not to the exception that carries it. Round 12 traced four of five
  findings to a single prior commit. **Lesson: the found-in-fix checklist (Part 4) + two
  *mechanical* pre-send gates** (an exhaustive terminal-facts oracle; a fault-injection at every
  seam) that must be green before a candidate goes out.

- **0007 / 0013 — schema versioning & migrations (14 / 29 rounds, accepted).** The deepest
  machinery. A store's `user_version` reads 0 for a genuine legacy store, a truncated copy, *and*
  a foreign SQLite file — so adoption must **verify the shape**, not trust the counter. Repeated
  rounds hardened the manifest/digest/evidence system, the open-time decision table (taken under a
  write lock, committed exactly once, with infallible commit/rollback sinks so a post-commit
  cleanup failure can't hide a committed migration). **Lesson: fail closed; verify shape not
  counters; never let a cleanup path discard a proven fact.**

- **0009 / 0010 — append-only outcomes & crash-safe consolidation (5 / 7 rounds, accepted).**
  These introduced **finite acceptance boundaries**: review value dropped as later rounds
  increasingly found seams in the prior round's fix while the architecture was affirmed every
  round. They were accepted on a frozen `H1–H14` / `X1–X23` invariant surface, with further edges
  reclassified as implementation obligations. **Lesson: bound the review; a design can be "done"
  on a frozen surface even when infinite polish remains.**

- **0006 — source identity (5 external rounds, accepted, implemented).** Three lessons in one.
  (a) **The absence-at-a-boundary pattern**: every defect found — the interface-lock (absent
  `origin` locally), **F1** (absent `source_id` at digest time), **F3** (absent `origin` on
  import) — was the *same shape*: the present-value semantics were ruled and the absent case was
  under-specified at one boundary. The principle that would have caught all three ("unknown is the
  floor, handled explicitly at every boundary") already existed and wasn't applied. (b) **A
  surviving superlative**: "unforgeable" persisted in §1 after R7 established the identity is *not*
  authenticated — and the right fix is the WITHDRAWN-marker discipline, not a word-grep (which
  fires on the corrected text). (c) **The interface-freeze protocol** worked: the `0006`↔`0014`
  seven-point interface was frozen by both owners + reviewer, *independently* of either spec's own
  acceptance. **Lesson: enumerate absence at every boundary before calling a ruling done; a freeze
  is only as strong as the thing frozen is *specified*.**

- **Process/CI lessons (cheap to hit, cheap to avoid).** Git trailers must sit in the **last
  contiguous paragraph** of the commit message — a blank line before `Co-Authored-By` orphaned a
  `Spec-Exception` and failed the guarded-file gate. The **audit manifest re-hashes** when an edit
  line-shifts a store-mutation site, so it must be regenerated after touching a manifested module
  (a docstring edit is enough). After a **schema-version bump**, the shipped **evidence must be
  regenerated** (`schema_evidence.py --runtime --write` + the registry-derived policy/version
  artifacts) or the store fails closed on open.

---

## Part 9 — The reviewer's checklist (distilled)

**Orientation**
- [ ] Read `PROCESS.md` and the spec being reviewed end-to-end; note its `Spec-Status`,
      `Spec-Requires`, and whether prerequisites are accepted.
- [ ] Verify the package: archived spec is **byte-identical** to what you were sent; re-run the
      suite in the extracted tree and reconcile with `COLLECTED.txt`'s measured line via its
      environment-conditional skip inventory (see "What green means").

**Specification**
- [ ] Is §4 a **construction**, not a description? Every invariant executable, every §2c cell
      reachable and honest?
- [ ] Do **claims match limits**? Any **superlative** that a later ruling narrowed but left
      standing? Any withdrawn rule stated as live (should be WITHDRAWN-marked)?
- [ ] For every **optional field**, is the **absent** case specified at every boundary (compare,
      digest, store, import, export)?
- [ ] **Carrier-completeness**: is a changed value updated in *every* representation (table,
      schema, regime, surfaces, invariant)?
- [ ] Do cross-spec citations resolve exactly?

**Code**
- [ ] Start at the guarded surface. For each change: whose trust does this decide, and can a
      lower-trust party influence it?
- [ ] Hunt the five failure classes: laundering, maintenance-path bypass, absence-at-a-boundary,
      unattributed transfer, impersonation.
- [ ] Apply the **found-in-fix checklist** to every change that closes a finding — especially
      recurse-the-property and carrier-completeness.
- [ ] Diff-scan as an adversary: what does this newly assume or newly expose?

**Tests**
- [ ] Every invariant maps to a real, **adversarial** test (inject the failure, don't confirm the
      happy path).
- [ ] New validators / failure seams **extend an exhaustive gate**, not just add an example.
- [ ] The mutation-site manifest and all `test_spec_gate.py` gates are green.

**Disposition**
- [ ] Number findings, tie each to the invariant/contract it breaks, give a concrete failure, and
      reproduce against the code where you can.
- [ ] If accepting, name the **frozen invariant surface**; if it's an interface freeze, confirm
      the **enumerated points**, and keep that sign-off separate from spec acceptance.
