# Feature spec: subject-scoped entitlement

Spec-Status: accepted
Spec-Requires: 0003, 0005, 0006, 0008, 0012, 0014, 0015, 0016, 0020, 0023, 0024, 0025

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **accepted** (2026-08-29, external round 19: NO findings of any class;
> the reviewer authorized the flip in the verdict). Split out of `0003` on
> 2026-08-02 after two external reviews showed the entitlement model is a
> larger design than the defect that motivated it; `0003` narrowed to the
> reported attack and shipped, this owned the breadth. Nineteen external
> rounds: finite design acceptance on the frozen S1–S7 surface at round 4,
> and every later return an evidence-machinery finding, closed at its
> mechanism.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v23 (ACCEPTED)** — external round 19 (2026-08-29): 🏁 ACCEPTED, the exact package `0011-v19` and candidate v22, NO blocking/major/minor/policy/trust-model findings; finite design acceptance in force on the frozen S1–S7 surface; the reviewer authorized the status flip after recording the verdict and generating the review-closure carriers (§Review closure is the GENERATED per-round ledger). The reviewer's OPTIONAL ask is recorded, not silent: a digest-bound focused R18 transcript (pristine pass + replacement-mutant identity failure) — DISCHARGED 2026-08-30 (`check_r18_transcript.py` + `r18_transcript.json`, runner-observed, digest-bound; reproduced in-suite). Implementation (E2–E6) is now authorized. *Prior:* **v22** — the ROUND-18 FOLD (2026-08-29; §28 maps the finding; production cleanup confirmed correct, no production change needed; no policy or trust-model defect). PROCESS-R18-1: 'the original exception propagates' was bound by TYPE and MESSAGE — an inner handler swapping each copy exception for a fresh lookalike passed both R17 regressions and the whole suite. Closed by IDENTITY: one sentinel exception object per copy2/copytree case, asserted with `caught.value is sentinel`; the same-type/same-message replacement mutant stands as a biting regression that only the identity probe kills; cleanup assertions and the cleanup-deletion mutant retained. *Prior:* **v21** — the ROUND-17 FOLD (2026-08-29; §27 maps the finding; R16-1's pre-refusal behavior and production cleanup confirmed correct; no policy or trust-model defect). PROCESS-R17-1: the copy-exception CLEANUP was not regression-bound — deleting the except-block rmtree passed the whole suite while a planted copytree failure leaked a snapshot dir; the test asserted the exception (outcome), never the allocated dir's fate (mechanism). Closed to the reviewer's five requirements: independent copy2/copytree fault injection post-allocation, the exact recorded directory required gone, the original exception propagated, the cleanup-deletion mutant standing with the leak OBSERVED, no broad globs. §27 also names the concurrent-reader class as recurring (three bites) with its invariant: private copies or recorded-path-scoped touches, never pattern-matched sweeps. *Prior:* **v20** — the ROUND-16 FOLD (2026-08-29; §26 maps the finding; R15-1's production fix confirmed correct; no policy or trust-model defect). PROCESS-R16-1: 'refuse before access' was NOT REGRESSION-BOUND — a mutant copying every root into a leaked temp dir BEFORE running the guards refused normally and passed all regressions (three leaked snapshots with the external sentinel), and the config-carrier check ran after mkdtemp so its refusal stranded a temp dir. Closed both halves: _snapshot is two-phase (ALL guards read-only first; allocate+copy second with guaranteed cleanup), and the regressions OBSERVE the mechanism — instrumented copytree/copy2/mkdtemp/walk must record zero pre-refusal activity, with the reviewer's copy-before-refuse mutant as a standing adversarial check that must trip the detector. *Prior:* **v19** — the ROUND-15 FOLD (2026-08-29; §25 maps the finding; R14-1 confirmed closed on its requested surface; no policy or trust-model defect). PROCESS-R15-1: the snapshot pre-scan missed SYMLINKED COPY ROOTS — is_dir() follows links, os.walk() walks a symlinked top, copytree dereferences it wholesale (top-level tests → external dir: sentinel copied in), and a symlinked conftest.py was SILENTLY OMITTED rather than refused. The recursion-base case of the round-14 property: each copy root is is_symlink-checked BEFORE is_dir/walk, config carriers (linked or broken-linked) refuse with the error posture, and the standing regression drives all three roots plus both carrier shapes with an external sentinel proving nothing is copied. *Prior:* **v18** — the ROUND-14 FOLD (2026-08-28; §24 maps the finding; R13-1 confirmed substantively closed incl. the reviewer's stronger constant-cardinality replacement; no policy or trust-model defect). PROCESS-R14-1: identity READ UNTRUSTED PATHS before validating them — a record hunk naming /etc/passwd validated clean (the record carrier had no path validation; the R8-1(3) absolute-join footgun back through the new path) and /bin/sh crashed both carriers with an uncaught decode error. Closed with ONE shared guard (allowlist membership as a pure string check FIRST — no filesystem access for an out-of-set path — containment and regular-file as depth) run in BOTH carriers before identity touches the filesystem, plus a defensive identity that cannot read outside the tree or crash on binary bytes. The standing regression drives /etc/passwd, traversal and /bin/sh through both carriers at the real entry point — /bin/sh IS the no-read witness (reading it raises; a named refusal without a traceback proves no read), with a latency bound proving no campaign ran. *Prior:* **v17** — the ROUND-13 FOLD (2026-08-28; §23 maps the finding; R12-1's exact-duplicate and window attacks confirmed closed; no policy or trust-model defect). PROCESS-R13-1: hunk PARTITIONING defeated mutation uniqueness — C2's two edits merged into one wider hunk yielded byte-identical mutated artifacts under a distinct identity, and a constant-cardinality replacement hid one mutant behind a double-counted other. FACE FOUR of one finding; the terminal identity is the RESULTING TRANSFORMATION — per artifact, the sha256 of the bytes the complete bundle produces from pristine — with no description left to slide. Merged-C2 and constant-cardinality attacks are standing regressions at the real on-disk boundaries; the ws-folded screen refuses the cheapest semantic-equivalent; the undecidable boundary stays named and visible as data. *Prior:* **v16** — the ROUND-12 FOLD (2026-08-28; §22 maps the finding; PROCESS-R11-1 confirmed substantively closed; no policy or trust-model defect). PROCESS-R12-1, two faces closed same-day: mutation IDENTITY is the sorted bundle of MINIMAL-DIFF hunk identities (common prefix/suffix stripped, whitespace folded, pinned to the edit's absolute position) — never the id (a fresh id relabeled R5A and inflated the totals while every observation stayed genuine) and never the full old/new text (research's pre-seal pass slid the context window: three exactly-once in-span old-texts of the same single edit made three 'distinct' bundles). Duplicates refuse on both carriers (entries validator and record grammar) whatever the id, finder, node, hunk order or window; run_check fails fast on entry problems so the refusal lands at the real --check boundary before any campaign run; --write refuses without writing; the DUPR5A regression drives both boundaries on disk. Subset inflation was already refused by leave-one-out; the undecidable semantic-variant boundary is named, and visible as data. *Prior:* **v15** — the ROUND-11 FOLD (2026-08-28; §21 maps the finding; the finite acceptance stands, no policy or trust-model defect found). PROCESS-R11-1: the kill-claim protocol is REMOVED, not hardened — schema 4 carries each mutation as TEXT HUNKS the runner applies itself, and a kill is runner-OBSERVED: the node passes on the clean tree and fails (exit 1, failures ≥ 1) with the entry's hunks applied, old text required exactly once, artifacts restored byte-identically verified. Leave-one-out runs prove each hunk of a multi-hunk entry individually load-bearing, so the hunk count is a MEASURED witness of defense depth (M3 takes four simultaneous neuters). A swapped registry is an observed SURVIVAL refused in both modes; a judge-targeting hunk (test files, the registry itself) and optioned node ids refuse at validation; a collection/usage error or empty run is a campaign ERROR, never a kill (the round-11 fail-open, standing at the REAL root); the campaign runs in a PRIVATE SNAPSHOT of the tree — the live tree is read-only to it by construction (in-place patching froze mutations into the fold checker twice in one afternoon: an interleaved concurrent campaign, then a killed one); the ABSENCE of any claim channel is itself a standing test; and research's pre-dispatch red-team pass is folded — every entry names the defense it mutates and hunks outside that ast-located span refuse (proxy-kills), the clean gate refuses skip/xfail laundering, the subprocess env is scrubbed, and every run gets a private bytecode namespace (a live mtime+size pyc collision made R5A report a false survival). *Prior:* **v14** — the ROUND-10 FOLD (2026-08-28; §20 maps the blocking finding and the maintenance item; the finite acceptance stands, no policy/authorization/contention/trust-model defect found). PROCESS-R10-1: attribution is RUNNER-OWNED — each node runs in an isolated pytest invocation and every reported kill is joined to the node the runner itself invoked; the reporter leaves the artifact entirely (a 4-line id-only writer in the test files), so an in-artifact reporter has nothing left to self-assert; the coordinated on-disk swap is the standing regression, driven through the REAL execution. EVIDENCE-M10-1: the check operand is PINNED to the shipped record (the environment selector is gone; corrupt operands exercise an internal helper on copies) and the check order is genuinely grammar-first — parse, closed schema, canonical-form of the bytes themselves, all BEFORE the campaign runs. *Prior:* **v13** — the ROUND-9 FOLD (2026-08-28; §19 maps both findings; the finite acceptance stands, no design or trust-model defect found). PROCESS-R9-1: the node join is bound BEHAVIORALLY — an integration regression sends a node-swapped registry through the REAL execution and requires failure, so a reporter rewritten to self-assert from the registry fails the test rather than the binding; the runner also refuses any reported node it did not invoke. EVIDENCE-R9-1: the record has a CLOSED CANONICAL GRAMMAR — duplicate JSON keys refuse at parse, a recursive exactly-typed schema governs every level (found_by is the two-value partition, totals keys are closed, bool never passes as int), the shipped RAW BYTES must equal the canonical writer's output, the schema is bumped to 3 for the killed-shape change, and every corrupt record is refused BY MAIN ITSELF in standing subprocess regressions. *Prior:* **v12** — the ROUND-8 FOLD (2026-08-28; §18 maps the finding; the finite acceptance stands, no policy/authorization/contention/trust-model defect found). PROCESS-R8-1: the ledger binds kills PER NODE — (node, id) pairs with the node taken from pytest's own PYTEST_CURRENT_TEST, exact pair-set equality; the record check compares CANONICAL SERIALIZED BYTES after pinning exact int types (False == 0 no longer passes as a match); and artifact paths must be relative, contained beneath the package root, and regular files (pathlib's absolute-join discard closed). All three attacks are standing regressions. *Prior:* **v11** — the ROUND-7 FOLD (2026-08-28; §17 maps the finding; the finite acceptance stands and the enum correction is confirmed sound). PROCESS-R7-1: the mutant ledger is INDEPENDENTLY CHECKABLE — every standing test reports the id(s) it kills, the runner requires reported kills to equal the declared ids exactly, artifact paths are validated, the default invocation is a non-mutating --check that recomputes the whole record and requires equality with the shipped one, and the bogus-entry / ghost-artifact / phantom-kill / double-kill / corrupted-record attacks are standing regressions. *Prior:* **v10** — the ROUND-6 FOLD (2026-08-28; §16 maps both findings; the finite acceptance stands, no policy/authorization/contention/telemetry/trust-model defect found). EVIDENCE-R6-1: the enum axes are pinned TO THE ENUM — AUTHORS must equal EvidenceAuthor and DERIVED must equal (None, *EvidenceAuthor), with expected keys built from the enum rather than the mutable constants; the narrowed-DERIVED mutant is standing. PROCESS-R6-1: the campaign is EXECUTABLE now — mutant_registry.py binds every id to its artifact, mutation and pytest node, runs them all, and derives the totals into a generated record (21 entries: 6 reviewer-found, 15 dev-found); the nine previously-untested mutants have standing in-memory tests; every fold check is sentinel-proven REACHED; and subject_census.py enters P1 via an explicit artifact registry. *Prior:* **v9** — the ROUND-5 FOLD (2026-08-27; §15 maps both findings; the finite acceptance stands, no architectural defect found). EVIDENCE-R5-1: a COUNT does not prove COVERAGE — the oracle now constructs the exact expected Cartesian key set and requires the emitted keys to equal it, with duplicates rejected separately, so a duplicate can no longer hide a missing cell at constant cardinality; the attack is a standing test. CARRIER-R5-1: §3c's live contract row still promised the withdrawn rider — swept, and the withdrawal is now BOUND TO THAT ROW in the checker, since a deferral stated in §4b does not un-promise a different row. *Prior:* **v8** — the ROUND-4 FOLD (2026-08-27; §14 maps every finding). **Round 4's verdict is FINITE DESIGN ACCEPTANCE for the v7 core construction — the authority-chain design is not to be reopened; this revision closes the three mechanical items the acceptance named as the gate to the status flip.** EVIDENCE-R4-1: the oracle is FULL-EDGE now — source and origin are real decision inputs on real Edge objects, every check consumes the ONE emitted stream (1,440 cells), the import-flattened cell runs through production `portability.import_memory` in both modes, and both of the reviewer's attacks (emitted-cell variance; helper shadowing) are standing mutation tests. CARRIER-R4-1: five more carriers swept to the broadened rule and the withdrawn-rider disposition. PACKAGE-R4-1: the static first-package paragraph is DELETED from every template and the seal now REFUSES static lineage claims — the defect the header's own C5-1 note already recorded, reintroduced seven lines below it. *Prior:* **v7** — the ROUND-3 FOLD (2026-08-27; §13 maps every finding). R3-1: the predicate is defined over the AUTHORITY CHAIN via production `effective()`, so a marker carrying no authority cannot move the decision — the executable 240-cell policy matrix asserts the CLASS (equal authority decides equally), not the two named instances. R3-2: the measurement rider is WITHDRAWN — 0015 defers refusal counters to a consent discussion this spec cannot hold, so v1 ships with the constituency unmeasured and says so. CARRIER-R3-1: five more contradictions swept and the checker bound to the predicate's TRANSITIVE DEPENDENCIES, closing the helper-in-another-fence bypass. EVIDENCE-R3-1: `schema == 1` required, the predicate cross-checked against 0025 on the shared subset, and every figure labelled by what backs it — including the two that are RECORDED ONLY. *Prior:* **v6** — the ROUND-2 FOLD (2026-08-27; §12 maps every finding). R2-1: **`source_id` is no longer read by the entitlement decision at all** — `0006` says it may GROUP, never GRANT, and v5 made it a capability in both directions (omission stripped protection, a caller-supplied value bought retirement). The `sourced` term is GONE, the rule refuses on subject class + self-assertion alone, the narrowing is deferred to `0016`'s frozen carrier, and a source-identity INVARIANCE matrix is owed. R2-2: `would_refuse_broad` DELETED as constant-true; the rider adds no stored state, so §7's claim holds again. R2-3: contention is `0003`'s REFUSAL-scoped notion — the shipped one — not a second contract. CARRIER-R2-1: seven contradictory authoritative statements swept, and the checker rebuilt to bind each assertion to its NAMED ROW, with S6 compared count-to-count. EVIDENCE-R2-1: the census aggregate has a closed typed schema and is cross-checked against 0025's independently-derived artifact. *Prior:* **v5** — the ROUND-1 FOLD (2026-08-26; §11 maps every finding). R1-1: the entitlement rule is REPRESENTABLE — `sourced` and `self_assertion` defined as closed predicates over state that exists today, a TOTAL policy function replacing v4's condition (which omitted the sourced term and contradicted §3c), the over-inclusion named in the refusing direction, the withdrawn 'confirmation is a higher rung' phrase retired against 0008, the basis-aware form deferred to 0016 rather than unfreezing it, and the measurement rider made MEASURABLE (it could not have measured anything: the deciding population produces no refusal row). R1-2: E5 is an INTEGRITY BINDING, not authentication — the claim is withdrawn, `correct()` is a protected host API with the host's obligations stated. R1-3: contention requires ≥2 DISTINCT `_value_key` values (v4's rule was false against accepted 0012, executed). R1-4: one outcome for a malformed `from_class` — RAISES, no write — with the complete grammar. R1-5: a first-match precedence table, total and exclusive, and E6 re-motivated after its premise was measured false. PACKAGE-R1-1: the census is GENERATED and digest-bound; two unreproducible figures retired. *Prior:* **v4** — the pre-send audit (2026-08-24, dev; nothing from a reviewer — these are the findings this spec would otherwise have paid a round for): **`Spec-Requires` declared for the first time** (0003, 0014, 0020, 0023, 0024, 0025 — the F1 class 0024 paid a round-1 finding for: a spec that consumes another's mechanism must say so); §3a-ii **Assertions about reach** and §3c **Trust-class matrix** written, both REQUIRED by TEMPLATE and both absent; the §3a `0024` Q3 currency line corrected (it said the pinned tests were absent post-revert — true when research wrote it, stale within the day when 0024 landed as amended); the §9 brief addressed to the EXTERNAL reviewer with the internal rounds recorded; section order fixed to 3a → 3a-ii → 3b → 3c (internal M-1b). Every command in §3a-ii was RUN and its real output recorded. *Prior:* **v3** — internal round 1 folded (research, 2026-08-23, PASS WITH AMENDMENTS): **M-2/E-Q4 RULED YES** — the acting principal (`0020`) joins the E5 tuple as the fifth element, verified in-transaction (E5 authenticates CORRECTORS, not just corrections; S4 gains the replay-across-principals cell); **M-3** §4b keeps the NARROW refusal cell for v1 with a measurement RIDER (count refusal rows by cell post-ship; broad revisits on an operator's numbers — the E-Q1 pattern); **M-1** currency + references (0024 cited at its SPEC surface with the predicate-not-disposition statement for the A1 divergence; the S7 pointer fixed; sections renumbered §3a/§3b); minors m-4 (historical motivation marked), m-5 (symbol not line), m-6 (`derived(from_class)` closed domain, unknown fails to the THIRD_PARTY floor). Ratified untouched: E-Q2, E-Q3, the conservation argument, absence-as-positive-capability, S1–S7's shape, and research's purpose-scoping non-foreclosure lens (passes by construction). *Prior:* **v2** — the design (2026-08-22, authorized by Quentin's "Proceed with 0011"): E-Q2 and E-Q3 RULED (both dev-owned; derived-at-read and explicit threading — the accepted stack's own disciplines), E-Q1 dispatched to research with a decision frame and a provisional floor, the six inherited findings turned into §4's constructions and §6's invariants, and the open `M7-correct` finding adopted as this spec's motivating live defect. *Prior:* v1, the scope-holder from the `0003` split |
| **Status** | *see `Spec-Status:` — canonical.* Holds `0003`'s deferred scope. **Nothing here blocks `0003`.** |
| **Internal reviewers** | research — round 1 PASS WITH AMENDMENTS 2026-08-23 (3 moderates + 3 minors, both §9 questions answered, E-Q4 ruled), folded in v3; **round 2 PASS 2026-08-23 (diff-verified 83d84c9..36eb177, zero stale refs, no new findings) — READY FOR EXTERNAL, send at Quentin's discretion** |
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

**At the time of the split (2026-08-02) the reported defect was unfixed
after two review rounds** — third-party content could still retire a user
fact (then `graph.py:139`). **So `0003` narrowed to that, and the breadth
landed here** rather than holding a guard hostage to an entitlement model.
(`0003` has since shipped, v0.6.0 — the sentence above is the historical
motivation, not a live defect; internal round 1, m-4.)

---

## 2. Scope inherited from `0003`'s reviews

| # | inherited finding | why it needs this spec |
|---|---|---|
| **E1** | subject class cannot come from the relation | needs `subject_class(user_id, subject, relation)`, canonical identity, alias handling, and an explicit default |
| **E2** | the authority matrix must be subject-aware | once subject class is load-bearing, the 400-row product stops being the decision procedure; the generated policy must take a subject dimension |
| **E3** | external-world contention has no current-value semantics | *"both stay active"* leaves a functional relation with no unique value; needs a **`CONTESTED`** relation state every reader handles |
| **E4** | trusted ingress must be a capability | `derived_from=None` is safe only if absence was **positively established**; a persistence-site manifest cannot authenticate origin |
| **E5** | `correct()` and absorption under one authorised replacement | needs a TAMPER-EVIDENT authorisation bound to *(store, prior, replacement, kind, principal)* and checked inside the atomic operation. NOT unforgeable and NOT authentication — see §4e: the principal is host-supplied and `correct()` mints the authorisation, so this binds INTEGRITY and ATTRIBUTION, and authenticating the corrector is the host's obligation (R1-2) |
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

## 3a. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the extractor's `subject` string | falsy → dropped by the shipped completeness check (`ingest.py`); whitespace → survives, strips to an empty claimant (the cell `0024` Q3 RULED conservative, and its pinned tests are ON MAIN as of 2026-08-24, when 0024's mechanism landed as amended by A1 — the internal-round-1 note said they were absent post-revert, true when written and stale within the day; re-derived at packaging) | truthy non-str → str()-converted by the shipped path | an entity ref this store has never seen → class **OTHER** (the default IS the conservative class) | text engineered to make the extractor emit `subject="user"` so a third-party fact rides the SELF class | **E1**: the classifier is TOTAL with OTHER as default; and SELF grants nothing to the *content* — it gates only which ENTITLEMENT rules apply to retirement, never disclosure (`0024` owns disclosure; **S7** states the non-interaction). **This spec consumes `0024`'s PREDICATE (§4a canonical subject), never its DISPOSITION** — amendment A1 (ACCEPTED 2026-08-24, round 24) sets the disposition to uniform USE_ONLY and nothing here moves with it (M-1: stated so the divergence cannot read as drift; currency updated at A1's acceptance) |
| the caller's `actor` on `correct()` | absent → the shipped default `"user"` — **the M7 defect's second face: a string DEFAULT is not an authorisation** | any string passes today | — | a tool-driven caller invoking `correct()` with `actor="user"` | **E5**: the authorisation capability is TAMPER-EVIDENT (NOT unforgeable — R1-2/§4e: `correct()` mints it from caller-controlled values, so the host authenticates the principal) and bound to *(store origin, prior id, replacement value, kind, **acting principal** — the `0020` element, internal round 1 M-2/E-Q4)* — a string names nobody, and without the principal ANY caller reaching `correct()` minted a valid capability: the binding closed forge/replay of a DIFFERENT correction, not an unauthorised caller minting a fresh one |
| the host's ingress declaration (`derived_from=None`) | absence is the TRUSTED claim today — safe only if positively established | — | — | a persistence-site caller replaying content with `derived_from` omitted | **E4**: absence must be a POSITIVE capability, not a missing argument |
| a second active value on a functional relation | — | — | — | an attacker holding one side of a contention to keep a stale value live | **E3**: `CONTESTED` is DERIVED at read (E-Q2 ruling) — no writer can pin it, no reader can miss it |

### 3a-ii. Assertions about reach — REQUIRED

**Every command was RUN in this repository on 2026-08-24 and the result
column records its real output.**

| assertion | command | result (RUN 2026-08-24) |
|---|---|---|
| **`Memory.correct` bypasses the ladder entirely and its `actor` is an unauthenticated string** — the motivating defect (`findings.py M7-correct`), in the source | `python -c "import inspect, veracium; print(inspect.getsource(veracium.Memory.correct))"` | signature carries `actor: str = "user"`; the body's store calls are exactly `['add_edge', 'invalidate_edge']` — **no `apply_supersession`, no receipt** |
| **the `0003` ladder this spec extends is a GENERATED policy with a version id** (so §4b's subject dimension is a regeneration + bump, not a new table) | `python -c "from veracium import authority; print(authority.RULE_VERSION)"` | `supersession-authority-v1` |
| **the refusal carrier §4b lands rows in already exists** — no new table | `select name from sqlite_master where type='table'` on a fresh store | `supersession_refusals` PRESENT |
| **`subject_class` does not exist today** — E1 is a construction, not a rename | `python -c "import veracium.graph as g; print(hasattr(g,'subject_class'))"` | `False` |
| **`CONTESTED` has no stored carrier today** — E-Q2's derived-at-read ruling is not undoing an existing field | `python -c "from veracium.schema import Edge; print([f for f in Edge.model_fields if 'contest' in f])"` | `[]` |
| **the `0024` canonical-subject predicate this spec's SELF floor consumes is SHIPPED** (as amended by A1, landed 2026-08-24) | `grep 'casefold() == "user"' src/veracium/ingest.py` | present at the coherence test; the same `str → strip` canonical subject the write path stores |
| **`0020`'s principal — E5's fifth element — is a real binding target** on the read path this spec must compose with | `grep -rln principal src/veracium/*.py` | eight modules, `scope_read.py` being "the ONE place a read path asks 'may this principal…'" |

*(The first row is why this spec exists and why E5 is not a rename: a
correction today reaches storage through two direct store calls, so
there is no plan, no receipt, no refusal record and no authorisation to
verify — the subject-entitlement rule of §4b would have nothing to
attach to.)*

## 3b. The rulings (E-Q2, E-Q3) and the provisional floor (E-Q1)

- **E-Q2 — RULED (dev, 2026-08-22): `CONTESTED` is DERIVED at read, never
  stored.** A functional relation with two or more ACTIVE same-disclosure-
  class edges on one `(user_id, subject, relation)` IS contested; the state
  is a read-time property in the same family as `Edge.active`,
  `quarantined` and `assertable` — every one of which is derived precisely
  so no second writer can drift from the fact it restates (`0023` N2's
  single-writer sweep exists because stored duplicates of derivable facts
  rot). A stored member would need a writer at every mutation site that
  can create or resolve contention — an enumeration this repo has watched
  drift through twelve external rounds elsewhere.
- **E-Q3 — RULED (dev, 2026-08-22): `EvidenceContext` is an EXPLICIT
  constructor argument threaded through ingest.** Invasive and checkable
  beats ambient and neither: an explicit parameter is enumerable by the
  X7-style AST sweep (`0025`'s "no unvalidated path" form), while ambient
  context is invisible to exactly the structural checks this repo's gates
  are built from.
- **E-Q1 — RESOLVED for v1 (research's ruling + the measured count,
  2026-08-22): (c), the predicate floor — and the count says the floor may
  be the ceiling.** v1 SELF is the `0024` canonical-subject predicate —
  `str(subject).strip().casefold() == "user"` — one predicate, shared
  verbatim with an accepted consumer. **An identity RELATION is REJECTED
  blocking-grade** (research): it would make the entitlement gate's input
  writable by the machinery the gate governs — supersession could rewrite
  who "the user" is, and a poisoned extraction could assert identity to
  acquire entitlement. Identity that gates anything must be
  HOST-ATTESTED; content-derived identity is the injection surface the
  ingest ladder closed. The named extension point, if a real operator
  ever needs it, is (a)-shaped: a host-declared alias set,
  boundary-validated, frozen per event — the registry pattern — arriving
  through its own review round, never a config flag. **The deciding count, GENERATED (PACKAGE-R1-1):**
  `specs/evidence/0011/subject_census.py` over the cache pinned by
  sha256 `654e336a…`, with the counts-only aggregate and the
  distinct-string candidate table shipped beside it, so every figure
  below re-derives WITHOUT the corpus (`--aggregate` reproduces the run
  exactly).

  | | |
  |---|---|
  | triples | 183,417 — the same corpus and sha as 0025's census |
  | predicate passes | **72,253 = 39.4%** (`subject.strip().casefold() == "user"`) |
  | candidate rows | **337 = 0.184%**, over **94 distinct strings** |
  | classified SELF | **31 = 0.017%**, over 4 distinct strings (`me`, `I`, `[User]`, `the user`) |
  | classified OTHER | 306 — possessives ("user's mom", "user's sister"), work topics ("User interviews", "end user"), roles |

  **Round 1 retired two figures that could not be reproduced.** v4 said
  305 candidates = 0.166% and ≈30 self-denoting ≈0.016%. The
  load-bearing one — 72,253 / 39.4% — reproduces EXACTLY. The other two
  came from a regex family that was never recorded, so its exact set
  cannot be reconstructed; the script's candidate regex IS recorded and
  deliberately over-inclusive (its job is to bound what a human must
  read, not to decide anything), and it finds 337 rows over 94 strings.
  The conclusion is unchanged and marginally stronger: 0.017% rather
  than 0.016%.

  **WHAT THE ARCHIVE CAN CHECK, AND WHAT IT CANNOT (external round 3,
  EVIDENCE-R3-1).** Round 2 added a closed schema and manifest
  cross-checks, and the reviewer showed the DECIDING figures were still
  self-asserted: keeping the peer manifest and triple total but setting
  `schema = 999`, `predicate_passes = 0` and a one-row candidate table
  produced no findings. `schema` was typed and never valued. The
  validator now requires `schema == 1`, and each figure is labelled by
  what actually backs it:

  | figure | backing |
  |---|---|
  | cache manifest, entries, unparseable, 183,417 triples | **cross-checked** against 0025's aggregate — same cache, different script |
  | the PREDICATE itself, on the `third_party_claim` subset: 1,606 of 3,945 | **cross-checked** against 0025's independently-derived `subject_user`. It does not bind the whole-corpus count, but it proves this predicate IS 0025's, on 1,600+ real rows |
  | candidate rows (337), classified SELF (31) | **derived** from the shipped table — recomputable from the archive alone |
  | `predicate_passes` over the whole corpus (**72,253**), and the candidate table's COMPLETENESS | **RECORDED ONLY.** 0025 carries no whole-corpus subject data, so these reproduce with `--cache` on the measuring host and NOT from the archive alone |

  That last row is a limitation of this package, stated rather than
  papered over: a reader without the corpus is trusting dev for 72,253
  and for the claim that no candidate was omitted. The narrowing is the
  honest option the round offered, and the alternative — shipping a
  whole-corpus subject-frequency table — would put 12,000+ corpus
  strings in a public archive to bind one number.

  The classification stays a HUMAN judgement and is now auditable as
  one: `SELF_DENOTING` in the script lists the strings judged
  self-denoting, the candidate table ships every row that judgement was
  made over, and a reader who disagrees edits the set and watches the
  number move. A regex cannot make this call — it finds subjects
  MENTIONING the user, and most of those ("user's mom") correctly denote
  somebody else. Given names in the table are masked (`user's friend
  <name>`); the classification never depends on them.

  The floor costs nothing real, and the alias set has no measured
  constituency yet.

## 3c. Trust-class matrix — REQUIRED, blocking

**Scope:** the rows state what a RETIREMENT attempt is entitled to do;
disclosure is untouched throughout (**S7**), so no cell here moves a
trust class. `SELF`/`OTHER` are §4a's classifier output for the PRIOR
edge's subject; "sole authority is self-assertion" is §4b's narrow cell
as ruled at internal round 1.

| incoming author | prior subject class | prior evidence | today | after | why |
|---|---|---|---|---|---|
| USER (self-assertion) | **SELF** | any | retires by the ladder | **unchanged** | a user's own facts about themselves are exactly what the `0003` ladder is for |
| USER (sole authority: self-assertion) | **OTHER** | sourced third-party evidence | retires by the ladder | **REFUSED**, `supersession_refusals` row | the reviewed attack: a user statement erasing sourced evidence about someone else — the motivating case of a rule that is now BROADER (any OTHER-subject prior, R2-1). §4b's cell, narrow by ruling; the measurement rider is WITHDRAWN (R3-2), so the narrow/broad question ships unmeasured and stated as such |
| USER (with other authority — **NOT confirmation: `0008` grants it none, R1-1**) | OTHER | any | retires | **unchanged** | the refusal is scoped to SOLE self-assertion authority; other authority is the ladder's business |
| THIRD_PARTY / SYSTEM | any | any | per the ladder | **unchanged** | this spec adds no authority to anyone; it only refuses |
| any | OTHER | **no** sourced evidence (an unsourced OTHER-subject edge) | per the ladder | **REFUSED when the incoming edge is a bare user self-assertion — CHANGED at R2-1** | v5 keyed the refusal on displacing SOURCED evidence; `0006` forbids `source_id` from granting anything, so the distinction has no trustworthy carrier and the rule refuses on subject class + self-assertion alone. Deferred to `0016`'s frozen `evidence_basis` |
| any | any (functional relation, ≥2 active same-class **with ≥2 distinct `_value_key` values**) | silent both-active | **`CONTESTED` at every reader** (derived) | E3/E-Q2: visible, never resolved by this spec. Same-VALUE restatements are agreement, not contention — `0012` persists them deliberately (R1-3) |
| `correct()` caller | any | any | direct invalidate+add, unauthenticated | **through the plan machinery with a bound `CorrectionAuthorisation`** — the correction becomes TAMPER-EVIDENT and ATTRIBUTED, and a caller who names a principal they are not is STILL NOT STOPPED here (R1-2: `correct()` mints from caller-controlled values; authenticating the corrector is the host's obligation, §4e) | E5; the subject rule above applies to corrections exactly as to extractor-driven supersession |

**Nothing in this table grants a retirement that is refused today.**
Every changed cell is a refusal that does not exist yet, a derived label
over facts already stored, or a route through machinery that already
records what it does — which is the conservation argument §3 makes and
the reason this composes with `0003` without unwinding it.

## 4. Behaviour — the constructions

### 4a. The classifier (E1)

`subject_class(user_id, subject) -> SELF | OTHER` — TOTAL, with **OTHER
the default**: SELF iff the canonical subject equals the user under the
`0024` predicate (§3b's floor; research's E-Q1 answer widens it behind the
same interface). The classifier consumes the STORED subject — the
str()-converted, stripped slot with a stated contract — never the note,
never the relation (§1: a relation cannot tell you whose fact it is).

### 4b. The subject-aware entitlement rule (E2)

The `0003` ladder (`authority.py`, `supersession-authority-v1`) remains
the AUTHOR axis; this spec adds the SUBJECT axis as a REFUSAL widening
only (§3's conservation argument): a retirement permitted by the author
ladder is additionally refused when the POLICY FUNCTION below returns
`REFUSE` — a user statement on their own authority cannot retire ANY
OTHER-subject prior, sourced or not (R2-1 removed the sourced qualifier:
`0006` forbids the distinction's only carrier from granting, so the rule
is broader than the attack that motivated it, and says so).

**v4's condition was `subject_class(prior) == OTHER` AND "sole
authority", and it OMITTED the sourced predicate — contradicting §3c's
own unchanged row, which says the refusal keys on displacing SOURCED
evidence and not on subject class alone (external round 1, R1-1). Worse,
neither "sourced" nor "self-assertion" had a runtime predicate at all.
`self_assertion` is defined here over the AUTHORITY CHAIN; `sourced` was REMOVED at R2-1 and is not a term of this decision.**

```
self_assertion(e) := effective(author_of_evidence, derived_from)
                    == effective(USER, None)
                    # "the chain carries nothing but the user's own
                    #  authority", computed by 0003's own effective()

policy(incoming, prior) :=
    REFUSE   if  subject_class(prior) == OTHER
             and self_assertion(incoming)
    ALLOW    otherwise            # total by construction

# THE RULE READS NO source_id. That is the point, not an omission.
```

**THE PREDICATE IS DEFINED OVER THE AUTHORITY CHAIN, NOT OVER A MARKER'S
PRESENCE (external round 3, R3-1).** v6 said `derived_from is None`, and
`EvidenceContext.derived(USER)` is valid and reachable, so:

| incoming provenance | effective authority | v6 |
|---|---|---|
| `USER`, `derived_from=None` | 3 | REFUSE |
| `USER`, `derived_from=USER` | **3 — identical** | **ALLOW** |

A marker supplying no independent authority bought permission to retire an
OTHER-subject fact. That is the SAME DEFECT as R2-1 one field over, and
both were mine: each round replaced one unauthenticated marker with
another and inherited the class. **The common defect is keying on the
presence or absence of a marker instead of on authority**, so the
predicate now asks production `effective()` — 0003's own function —
whether the chain carries anything but the user. Enumerated against it,
exactly two chains qualify, and R3-1's cell is inside the refusal set BY
CONSTRUCTION rather than by patch.

**§6 acceptance surface — `specs/evidence/0011/policy_matrix.py`, 240
cells, executable.** It enumerates author × derived_from × subject class ×
source presence × origin and asserts: totality; the named R3-1 cell; the
GENERAL property that equal effective authority decides equally (which is
the class, not the instance); invariance under source identity and origin
(0006's GROUP-never-GRANT, proved rather than asserted); that
`derived_from` never RAISES authority; and that a SELF-subject prior is
never refused. Both defects that actually shipped were planted against it
and both are caught.

**The decision table, GENERATED from that matrix:**

| author | derived_from | effective | subject OTHER | subject SELF |
|---|---|---|---|---|
| `user` | `None` | 3 | **REFUSE** | ALLOW |
| `user` | `user` | 3 | **REFUSE** | ALLOW |
| `user` | `third_party` | 0 | **ALLOW** | ALLOW |
| `user` | `system` | 2 | **ALLOW** | ALLOW |
| `user` | `assistant` | 1 | **ALLOW** | ALLOW |
| `third_party` | `None` | 0 | **ALLOW** | ALLOW |
| `third_party` | `user` | 0 | **ALLOW** | ALLOW |
| `third_party` | `third_party` | 0 | **ALLOW** | ALLOW |
| `third_party` | `system` | 0 | **ALLOW** | ALLOW |
| `third_party` | `assistant` | 0 | **ALLOW** | ALLOW |
| `system` | `None` | 2 | **ALLOW** | ALLOW |
| `system` | `user` | 2 | **ALLOW** | ALLOW |
| `system` | `third_party` | 0 | **ALLOW** | ALLOW |
| `system` | `system` | 2 | **ALLOW** | ALLOW |
| `system` | `assistant` | 1 | **ALLOW** | ALLOW |
| `assistant` | `None` | 1 | **ALLOW** | ALLOW |
| `assistant` | `user` | 1 | **ALLOW** | ALLOW |
| `assistant` | `third_party` | 0 | **ALLOW** | ALLOW |
| `assistant` | `system` | 1 | **ALLOW** | ALLOW |
| `assistant` | `assistant` | 1 | **ALLOW** | ALLOW |

**The laundering cells, decided rather than defaulted (R3-1 asked).**
`derived_from` CAPS authority — it is a `min`, never a raise — so
`SYSTEM`/`ASSISTANT` evidence marked `derived_from=USER` keeps its own
class and is not the user's self-assertion. The matrix asserts both
halves: those cells are not self-assertions, and the marker does not
raise their authority. A lower class cannot launder upward through a
derivation marker, which is why they ALLOW here and the ladder decides.

**`sourced` IS GONE, AND `source_id` IS NOT READ ANYWHERE IN THIS
DECISION (external round 2, R2-1).** v5 defined both predicates from
`source_id` presence, and the reviewer executed what that bought:

| mutation | v5 outcome |
|---|---|
| sourced OTHER prior + plain USER assertion | REFUSE |
| omit the prior's `source_id` | **ALLOW** — omission removed the protection |
| add any `source_id` to the USER assertion | **ALLOW** — caller-supplied metadata granted permission |

Accepted `0006` says in four places that **`source_id` may GROUP, never
GRANT**: it is optional, host-supplied and DIAGNOSTIC, and its absence
must not relax a decision. v5 made it an entitlement capability in both
directions — omission stripped protection, and supplying a value bought
retirement permission. `0006` was not even declared as a prerequisite
while its carrier was being consumed to decide authority. That is the
whole finding, and the fix is not to read the field more carefully; it
is to STOP READING IT.

**What this costs, stated plainly.** The `sourced` qualifier was v5's
narrowness — the refusal keyed on displacing SOURCED evidence, so a
user correcting their own unsourced entries about another subject was
untouched. Without a trustworthy carrier for that distinction the
narrowing cannot be expressed, so the rule REFUSES MORE: any bare user
self-assertion retiring an OTHER-subject prior is refused, sourced or
not. A refusal is a recorded row and a confirmable path, never data
loss — but it is friction on a real workflow, and v1 CANNOT measure how
much: the rider that would have counted it is WITHDRAWN (R3-2 — `0015`
defers refusal counters to a consent discussion this spec cannot hold),
so the cost is stated as unquantified rather than promised a number.

**When the distinction returns.** `0016`'s `evidence_basis` is the
authenticated carrier this rule wants and it is FROZEN; v1 does not
unfreeze it. The narrowing is deferred to that carrier's own round, and
the deferral is the reason the rule is broad rather than an oversight.

**The invariance this spec now owes `0006`, as a matrix:** the decision
must be UNCHANGED under every manipulation of source identity, which is
a stronger claim than "we don't use it" and is testable —

| mutation of the incoming or prior edge | required |
|---|---|
| `source_id` present → absent, either side | decision unchanged |
| `source_id` absent → present, either side | decision unchanged |
| `source_id` set to an arbitrary caller-chosen value | decision unchanged |
| `origin` local → foreign, either side | decision unchanged |
| the prior arrives by IMPORT (0005 cap applied, author flattened) | decision follows the FLATTENED author, and still reads no `source_id` |

**Every term, including absence:**

| term | absent case | why this reading |
|---|---|---|
| ~~`source_id`~~ | **NOT A TERM (R2-1)** | removed from the decision entirely: `0006` says it may GROUP, never GRANT. Kept in this table as a struck row so a reader who remembers it finds its removal rather than its absence |
| `derived_from` | `None` → not relayed | **and this is the known soft spot, named rather than hidden.** Today `None` means both "genuinely first-party" and "the host said nothing" — which is precisely the ambiguity §4d's `EvidenceContext` exists to remove. Until a host supplies one, `self_assertion` is over-inclusive: it will be TRUE for user edges whose provenance was merely unstated. |
| `author_of_evidence` | never absent | a required field on `Provenance` |

**The over-inclusion is in the REFUSING direction, and that is the
choice.** A user edge whose derivation was never declared is treated as
self-assertion, so the rule refuses more often than a perfectly-informed
rule would. A refusal is a recorded row and a confirmable path, not data
loss; the opposite error silently erases sourced evidence about a third
party. Once `EvidenceContext` ships, `self_assertion` tightens to
`context.direct`, and it tightens WITHOUT changing this rule's shape.

**What is NOT expressible today, and is therefore not claimed.** v4 also
spoke of "confirmation, a higher rung". `0008` grants confirmation NO
authority, so there is no rung to read, and the phrase is withdrawn
rather than reinterpreted. A basis-aware rule — one that distinguishes
first-hand from relayed evidence properly — needs `0016`'s frozen
`evidence_basis`, and 0016 is a FROZEN surface. **v1 does not unfreeze
it.** The basis-aware form is recorded as the successor and named as
blocked on 0016's own round. The generated policy gains the subject dimension; the 400-row
author product stops being the whole decision procedure, and the refusal
lands as a `supersession_refusals` row exactly like the ladder's own
(same carrier, `rule_version` bumped — no new table).

**The narrowness is v1's, held with a MEASUREMENT RIDER (internal round
1, M-3 ruling):** "sole authority is self-assertion" closes the reviewed
attack without pushing routine user corrections of their own third-party
entries into authorisation friction — and the broad form ("ANY
user-authored retirement of an OTHER-subject sourced fact refuses
pending confirmation") has no measured constituency. **The rider as v4 wrote it could not have measured anything, and the
reviewer showed why (R1-1).** Refusal rows carry edge ids, relation,
effective authorities and `rule_version` — no cell code, so refusals
could not be attributed to a cell. And the decisive population is the
one that produces NO ROW AT ALL: an event the narrow rule ALLOWS and the
broad rule would refuse never reaches the refusal carrier, so counting
refusals could never find the broad form's constituency. It would have
returned zero for the wrong reason, and zero is what "no measured
constituency" already claims — the rider would have confirmed itself.

**THE RIDER IS DEFERRED. IT CANNOT BE BUILT ON ANOTHER SPEC'S DEFERRED
CONSENT SURFACE (external round 3, R3-2).**

Round 2 rewrote the rider as counters on `0015`'s existing carrier,
incremented at decision time under the existing consent posture. Accepted
`0015` says the opposite of every clause of that:

| `0015` says | v6 assumed |
|---|---|
| refusal counters are **explicitly deferred to a new consent discussion** | they can be added now |
| new payload fields require **consent-version gating and updated consent text** | the existing posture covers them |
| counters derive **only from a fresh commit** | increment at decision time |
| replays, stale attempts and refusal-only outcomes **do not count** | every decision counts |

Decision-time increments would also overcount aborted and `PLAN_STALE`
attempts, and the rider named no field names, cell taxonomy, consent
version, visibility rules or multi-prior cardinality. **This is the third
round in which I asserted a rule over another spec's contract without
checking that contract's domain** — after `0006` at R2-1 and `0012` at
R1-3 — and it is the same error each time.

So the rider is WITHDRAWN from v1 rather than specified around:

* **v1 ships with the broad rule's constituency UNMEASURED, and says so.**
  The narrow/broad question is not resolved by this spec and cannot be
  resolved by it, because the only honest way to count the deciding
  population is a telemetry surface whose consent question `0015` has
  deferred.
* Revisiting the broad form therefore waits on **`0015`'s consent
  discussion**, and on a complete telemetry construction — field names, a
  closed cell taxonomy, consent version and text, host/MCP visibility, and
  fresh-commit semantics that exclude replays and stale attempts. That is
  `0015`'s round to hold, not this spec's to pre-empt.
* What v1 keeps is the NARROWNESS ITSELF as a stated, deliberate choice
  with its cost named (§4b: the rule refuses more than a
  perfectly-informed rule would), rather than a promise to measure that it
  has no mechanism to keep.

`0015` remains in `Spec-Requires` — this spec still depends on its
supersession counters existing — but nothing here adds to its payload.

### 4c. `CONTESTED` at every reader (E3, per the E-Q2 ruling)

**CONTENTION IS `0003`'s REFUSAL-SCOPED NOTION. This spec does not
define a second one (external round 2, R2-3).**

`contested` is what the shipped surface already means: a LIVE REFUSAL
CONTENTION — a refusal record exists, both referenced edges are still
active and distinct, and the relation is functional. `compile.py` says
so in terms ("the derived-view treatment is REFUSAL-scoped (Option B),
not every contention") and `Recall.contested` carries one entry per live
refusal.

v5 defined it instead from ANY active same-class pair with ≥2 distinct
values, and the reviewer executed the divergence: two active, same-class,
distinct-value edges inserted directly into a real store are **contested
under v5's predicate and NOT contested under the shipped
`Recall.contested`** — 0 groups, 0 exposed members. The draft was
carrying two contracts at once and calling both `contested`, which is
how a reader gets a label that no reader produces.

So E3 governs the RENDERING of the refusal-scoped set — what a reader
does when it meets one — and derives nothing new:

| surface | E3's obligation |
|---|---|
| `Recall.contested` | already the carrier; E3 adds no members and removes none |
| gate | a contested functional value is non-assertable-as-current — assert the CONTENTION, never one side |
| maintain | resolution verbs (consolidate, absorb across the pair) are suppressed; **`0012`'s per-edge expiry is NOT** |
| import | a refusal record is store-local state; an imported pair carries no refusal and is therefore not contested on arrival |
| direct-store insertion | **not contested** — no refusal, no contention. This is the reviewer's executed cell, and the shipped answer is the right one |

The distinct-value requirement folded at R1-3 is not lost: it is part of
the shipped predicate already ("still distinct"), which is why adopting
that predicate keeps R1-3 closed rather than reopening it.

**The distinct-value clause is not a refinement; without it the rule was
FALSE against accepted `0012` (external round 1, R1-3, executed).** v4
defined contention as two active same-class edges and stopped there.
`0012` deliberately PERSISTS a same-value restatement as a separate
active edge and says in terms that such a pair is not contested — the
reviewer ran
`tests/test_0012_currency_renewal.py::test_a_same_value_restatement_produces_no_contention_artifacts`
(**1 passed**) on a MENTIONABLE USER/SYSTEM pair that is active,
same-class, and produces no contention artifact. v4's rule would have
labelled every renewal in the store as a contradiction. Two records of
the same value are agreement; contention needs disagreement, and
disagreement means distinct values.

**Composition with the specs this rule reaches into**, which v4 left
unstated:

* **`0003`** already scopes contention to REFUSAL — a refused
  supersession leaves both sides active and records why. This rule is
  derived and additive: it names the resulting state at read time and
  changes no refusal semantics. Where `0003` has already recorded a
  refusal, `contested` is the read-side view of that same fact, not a
  second one.
* **`0012`** owns same-value persistence, the render-time collapse of
  strict redundancy, and **per-edge expiry**. The clause above adopts
  `0012`'s own `_value_key` normalisation rather than inventing a
  second notion of "same value", so the two cannot drift apart.
* **`maintain` neither resolves nor consolidates across a contested
  pair** — and that is a NARROWER claim than v4 made. It does NOT
  suspend `0012`'s per-edge expiry: a contested edge still expires on
  its own schedule, because holding a stale value alive because it is
  disputed is the opposite of the guarantee. Contention suppresses
  RESOLUTION verbs (consolidate, absorb across the pair), never
  lifecycle.
* Structured reach, budgeting, scoping, proactive no-new-reach and
  cache semantics are UNCHANGED by this rule. It adds a label at read
  time; a reader that never asks for the label sees exactly today's
  behaviour.

Readers handle it the way they handle `needs_confirmation` — recall
labels the value set as contested rather than choosing one; the gate
treats a contested functional value as non-assertable-as-current
(assert the CONTENTION, never one side). Resolution happens only
through the entitled paths: supersession by an entitled author,
`correct()` under E5, or `confirm()`.

**Prerequisite consequence:** `0012` joins `Spec-Requires` as a direct
dependency, and `src/veracium/lifecycle.py` joins §7a's consumer list —
the expiry interaction above is a claim about that module and v4 did
not name it.

### 4d. Trusted ingress as a capability (E4)

`derived_from=None` stops being trusted-by-omission: `ingest_event`
gains an explicit `EvidenceContext` (E-Q3: a constructor argument)
carrying the host's POSITIVE declaration — `direct` (the host attests
first-party capture) or `derived(from_class)`. **`from_class` is a CLOSED domain,
validated at construction (internal round 1, m-6): an unknown or
malformed value RAISES and NOTHING IS WRITTEN.**

*(External round 1, R1-4: v4 said both "the constructor refuses
unknowns" AND "fails closed to the `derived(THIRD_PARTY)` floor". Those
are different observable outcomes for one input, and a spec that names
two cannot be conformed to. REFUSAL is chosen: flooring a malformed
value silently accepts a host bug and writes a record whose declared
provenance nobody meant, which is the failure this capability exists to
prevent. Refusing is loud, has no write, and leaves the host's bug
where the host can see it.)*

**ABSENCE IS A DIFFERENT INPUT AND KEEPS THE FLOOR.** No context at all
is the conservative cell: treated as `derived(THIRD_PARTY)`, never as
direct. That is not a contradiction of the refusal above — a host that
supplies nothing has declared nothing and gets today's worst case; a
host that supplies GARBAGE has declared something untrue, and the
difference is worth an exception.

**The complete grammar, with every cell reachable and named:**

| input | outcome |
|---|---|
| context absent (`None`) | `derived(THIRD_PARTY)` — the floor |
| `direct` | host attests first-party capture |
| `derived(USER)` / `derived(SYSTEM)` / `derived(ASSISTANT)` / `derived(THIRD_PARTY)` | as declared |
| `derived(<unknown member>)` | **RAISES**, no write |
| `derived(None)` | **RAISES**, no write — `derived` with nothing derived from is not the same as absence |
| `derived(<non-enum type>)` — str, int, dict, list | **RAISES**, no write; no coercion, no `str()` |
| a bare string `"direct"` where a context is expected | **RAISES** — the value object cannot be minted from a caller string |

**Adversarial matrix (V-names to be assigned at implementation):** each
RAISES row above is a test, plus the two that make the closed domain
mean something — an enum member added later with no cell must fail the
totality test rather than inherit a default, and the absence row must
be proven distinct from `derived(THIRD_PARTY)` supplied explicitly, so
the two paths cannot be collapsed by a future refactor. The context is a value object the persistence site cannot mint
implicitly; hosts that never construct one get exactly today's
worst-case flooring, so the change is refusal-conservative.

### 4e. `correct()` through the ladder, authorised (E5 — closes `M7-correct`)

The live defect (`findings.py M7-correct`, at the symbol `Memory.correct` — cited by name, not line; internal round 1, m-5):
`correct()` calls `invalidate_edge` + `add_edge` directly — no ladder, no
receipt, no refusal record, and `actor` is an unauthenticated string
defaulting to `"user"`. The construction: `correct()` builds a
replacement edge and submits it through `apply_supersession`'s atomic
plan machinery with a **`CorrectionAuthorisation`** bound to
*(store origin, prior edge id, replacement value digest, kind, **acting
principal**)* — the fifth element is `0020`'s principal (internal round
1, M-2/E-Q4).

**WHAT THIS IS: AN INTEGRITY BINDING. IT IS NOT AUTHENTICATION, AND v4
CLAIMED OTHERWISE (external round 1, R1-2).** v4 said binding the
principal made the authorisation "unforgeable" and that it
"authenticates CORRECTORS". It does neither, and the reviewer executed
the reason: `0020` states plainly that `principal` is HOST-SUPPLIED,
FORGEABLE and NOT AUTHENTICATED, while `Memory.correct()` MINTS the
authorisation itself from caller-controlled values. A caller may name
any principal, request a fresh authorisation for it, and pass the
in-transaction equality check. The cross-principal replay test blocks
REUSE under a different name; it never blocked fresh impersonation, and
a five-tuple cannot authenticate a value its own caller chose.

So the claim is withdrawn and replaced by the one the mechanism
supports:

* **What the binding DOES establish.** A correction, once authorised,
  cannot be altered, replayed against a different prior, rebound to a
  different replacement value, or reused under a different principal —
  every element is verified INSIDE the transaction (the `0014`
  snapshot-verification shape). The receipt records WHICH principal the
  caller declared, so an operator can attribute and scope after the
  fact. That is integrity and attribution, and it is worth having.
* **What it does NOT establish.** That the declared principal is who
  they say they are. Nothing in this spec authenticates a corrector.

**`correct()` is therefore a PROTECTED HOST API, on 0008's model, and
the obligations are the host's** — stated here rather than assumed:

| the host must | because |
|---|---|
| authenticate the principal before calling | the store cannot; `principal` arrives as a caller-supplied string |
| establish the user's INTENT to correct | a correction retires a prior fact; an unintended one is a silent loss |
| not expose `correct()` on a surface a model can reach with a caller-chosen principal | that is self-elevation with extra steps — the same rule that keeps `system` off the MCP surface |

A future spec may specify an externally issued opaque capability that
`Memory.correct()` cannot mint from caller-controlled values, which
WOULD authenticate. That is a real API-surface change, it is out of
scope for v1, and it is named here so the gap is a known one rather
than a silent one.

With the binding so scoped: the subject-entitlement rule of §4b applies
to corrections exactly as to extractor-driven supersession. `record_outcome` stays
fact-untouching.

### 4f. The history partition (E6)

**v4's three labels were neither TOTAL nor EXCLUSIVE, and their stated
motivation was FALSE. External round 1, R1-5, executed all three.**

Applying v4's definitions literally: an active, quarantined, grounded,
uncontested edge matched **zero** labels; an active, mentionable,
grounded, contested edge matched **both** `GROUNDED_CURRENT` and
`UNVERIFIED_CURRENT`. And the premise — that `compile` and `introspect`
interleave history with present fact — does not hold: `compile.py`
reads `active_only=True`, `introspect.py` already separates retired
counts and renders categories from the active set, and `gate.partition_parts`
drops inactive edges from both blocks. **No shipped reader interleaves
history with present fact.** The defect E6 was written to fix is not
there.

**So E6 is re-motivated to what it actually earns, and it is smaller.**
Two states this spec introduces — `CONTESTED` (§4c) and the quarantined
cell — have no defined rendering, and every reader that meets them will
otherwise invent one. E6 supplies ONE vocabulary so they cannot diverge,
and states the precedence exactly. It is a naming and totality
guarantee, not a repair of a live interleaving bug, and v4 claimed the
latter.

**The precedence table — FIRST MATCH WINS, which is what makes it both
total and exclusive:**

| # | condition | label |
|---|---|---|
| 1 | `not e.active` | `RETIRED_HISTORY` |
| 2 | `e.quarantined` | `QUARANTINED_CLAIM` |
| 3 | `contested(user_id, subject, relation)` (§4c) | `CONTESTED_CURRENT` |
| 4 | `e.ungrounded or e.use_only` | `UNVERIFIED_CURRENT` |
| 5 | otherwise | `GROUNDED_CURRENT` |

Row 5 is a catch-all, so TOTALITY holds by construction rather than by
enumeration; first-match makes EXCLUSIVITY hold for the same reason.
`QUARANTINED_CLAIM` and `CONTESTED_CURRENT` are new since v4 — v4 had no
cell for either, which is exactly why an edge could match none or two.
Precedence order is a claim in itself: quarantine outranks contention
because a quarantined edge's dispute is moot until it leaves quarantine,
and contention outranks ungroundedness because a contested value must
not be rendered as merely unverified-but-current.

**The invariant, and its adversarial matrix:** for every edge, exactly
one label — asserted over the CROSS-PRODUCT of (active × quarantined ×
ungrounded × use_only × contested), not over sampled cells. The two
cells R1-5 executed (quarantined-grounded-uncontested → row 2;
mentionable-grounded-contested → row 3) are named cells in it, since
they are the ones v4 got wrong.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| a store with only user-self facts | byte-identical decisions — SELF-on-SELF entitlement is today's ladder |
| third-party/org facts, no contention | unchanged until a USER self-assertion attempts to retire ANY OTHER-subject fact — sourced or not (R2-1 removed the sourced qualifier, so this widened) — then a NEW refusal row |
| a functional relation in genuine contention | today: silent both-active; after: derived `CONTESTED` at every reader, gate asserts the contention |
| existing `correct()` callers | same signature; the authorisation is minted by `Memory.correct` itself for the interactive path — the CHANGE is that tool-driven and replayed invocations can no longer TAMPER WITH or REPLAY (they can still name a principal they are not — R1-2) it |
| hosts that never construct `EvidenceContext` | floored at `derived(THIRD_PARTY)` — strictly more conservative than today |

## 6. Invariants and executable checks — REQUIRED, blocking

| # | invariant | check |
|---|---|---|
| **S1** | `subject_class` is TOTAL with OTHER as default — every subject string classifies, and only the canonical-predicate cell is SELF | `test_subject_class_is_total` — property test over adversarial strings, the `0024` predicate cells included |
| **S2** | a USER self-assertion never retires ANY OTHER-subject prior — sourced or not (the R2-1 broadening; sourced was the motivating case, not the rule) | `test_self_assertion_cannot_retire_other_subject` — the E2 cell over BOTH source states, plus the refusal-row assertion |
| **S3** | `CONTESTED` is derived — NO stored carrier exists, and every reader (recall, gate, maintain) handles the contested cell | `test_contested_is_derived_and_total_over_readers` — an AST sweep for stored writes plus per-reader behaviour cells |
| **S4** | `correct()` reaches storage ONLY through the atomic plan machinery with a verified `CorrectionAuthorisation`; a forged, replayed, unbound, or **cross-principal** authorisation aborts inside the transaction (M-2: a capability minted under one principal replayed under another is the named new cell) | `test_correct_requires_bound_authorisation` — the M7 regression, forge/replay/rebind cells **+ the replay-across-principals cell** |
| **S5** | absent `EvidenceContext` floors at `derived(THIRD_PARTY)` — absence is never the trusted cell — **and an unknown or malformed `from_class` RAISES with no write — a DIFFERENT outcome, settled at R1-4 (absence declares nothing; garbage declares something untrue)** — the domain is closed and validators refuse the unknown, not just cover the known (m-6) | `test_absent_context_floors_conservative` — plus the unknown-value cell |
| **S6** | the partition labels are derived and total — every edge lands in exactly one of `labels=5` — the labels of §4f's first-match precedence table (R1-5/CARRIER-R2-1: v5 said three, which was neither total nor exclusive, and said it in a row a phrase-search did not reach) | `test_history_partition_is_total` — enumeration over the field product |
| **S7** | disclosure is never WRITTEN here — the `0024`/`0025` pipeline owns it. **§4f's partition READS it** (`quarantined`, `use_only`) to place a label, which v5 denied (R2-1/CARRIER-R2-1); reading to render is not writing to decide, and the distinction is the invariant | `test_no_disclosure_interaction` — the N2-style single-writer sweep extended, not duplicated |

## 7. Failure modes and reversibility

- **Too-narrow SELF** (the literal predicate misses aliased self-facts):
  the OTHER default refuses more retirements than intended — costs
  convenience, never integrity. Research's E-Q1 widening recovers it.
- **Too-broad SELF** would be the dangerous direction; S1's property test
  and the single-predicate discipline (shared with `0024`) bound it.
- **Reversibility:** every rule is a refusal-widening or a derived read
  label; reverting restores today's behaviour with no stored state to
  unwind. The `CorrectionAuthorisation` and receipt rows are additive.

## 7a. Surfaces touched

| carrier | change |
|---|---|
| `src/veracium/authority.py` | the subject dimension in the generated policy; `rule_version` bump |
| `src/veracium/graph.py` | the §4b refusal cell in plan building; contested derivation |
| `src/veracium/__init__.py` (`correct`) | routed through the plan machinery with the bound authorisation |
| `src/veracium/ingest.py` | the explicit `EvidenceContext` parameter (E-Q3) |
| `src/veracium/compile.py` / `gate.py` / `introspect.py` | contested handling + the §4f partition labels |
| `src/veracium/lifecycle.py` | **added at R1-3.** §4c claims contention does NOT suspend `0012`'s per-edge expiry; that is a claim about this module and v4 named neither |
| `src/veracium/portability.py` | **retained, on NARROWER grounds (R3-1).** R1-1 listed this because source identity participated in the predicate; it no longer does. What remains is real: the `0005` import cap FLATTENS an imported record's author, and the decision is a function of author and derivation — so the import boundary decides which authority chain the predicate sees. The matrix asserts the import-flattened cell |
| tests | the §6 table's named tests — §6 is the ONE authoritative list |

## 8. Claims and limits

This spec decides who may retire what about whom, and nothing else. It
does not touch disclosure (`0024`/`0025` own the trust pipeline), does
not resolve contention (it makes contention VISIBLE and gates its
resolution paths), and grants no new authority to anyone — every rule is
a refusal that does not exist today or a label over facts already
stored.

## 9. Brief for the external reviewer

*(Internal review is complete: research ran two rounds — round 1 PASS
WITH AMENDMENTS with all three questions ruled, round 2 PASS with no new
findings, both folded. The questions below are what we most want you to
attack.)*

1. **The E-Q2 ruling** — derived-at-read rests on the single-writer
   discipline; if you think a stored member with enumerated writers is
   safer, that reverses three accepted precedents and is the finding we
   would rather have now than after implementation.
2. **The E5 binding** — RULED at internal round 1 (M-2/E-Q4): the
   acting principal IS the fifth element. Kept here for the external
   reviewer: attack the in-transaction verification and the
   cross-principal replay cell.
3. **The §4b refusal cell** — RULED at internal round 1 (M-3): narrow
   for v1. The measurement rider is WITHDRAWN (R3-2): `0015` defers
   refusal counters to a consent discussion this spec cannot hold, so
   the narrow/broad question ships UNMEASURED and stated as such. For
   the external reviewer: attack the deferral instead — is anything in
   v1 quietly depending on a number this spec has no mechanism to
   produce?

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **E-Q1** | How is the user's own subject identity canonicalised? | **RESOLVED for v1 (2026-08-22)** — the predicate floor ships; the identity-relation option rejected blocking-grade; the alias-set extension point named and priced at ≈0.017% — the GENERATED census (31 rows over 94 distinct candidate strings). The figure v4 carried here is superseded and is not restated in this row; PACKAGE-R1-1 and §3b record what it was and why it went measured constituency (§3b) | research + dev, jointly | — |
| **E-Q4** | should the E5 authorisation tuple carry the acting principal (`0020`) as a fifth element? | **RESOLVED (internal round 1, 2026-08-23): YES** — E5 as drafted bound the arguments, not the actor; under `0020` the principal IS what distinguishes callers. Fifth element, verified in-transaction, receipt records WHO, S4 gains the cross-principal replay cell (§4e) | dev + internal review | — |

## 11. Changes in v5 — the round-1 fold (2026-08-26)

Round 1 returned draft v4 for major amendment: five spec findings and one
package finding. All six are folded here. Two of them found claims that
were not merely incomplete but **false against shipped, accepted
behaviour**, and the reviewer executed both.

**0011-R1-1 — the central cell was not representable.** v4's rule spoke
of `sourced`, `self-assertion` and "confirmation, a higher rung", and
none had a runtime predicate; §4b's formal condition tested subject class
and sole authority while OMITTING the sourced term, contradicting §3c's
own unchanged row. Folded: `sourced` and `self_assertion` are closed
predicates over state that exists today, the policy function is TOTAL and
replaces the condition, and every term's absence case is stated. The
`derived_from is None` ambiguity is named as the known soft spot rather
than hidden, with the over-inclusion pointed in the REFUSING direction
and the reason given. "Confirmation is a higher rung" is WITHDRAWN —
`0008` grants confirmation no authority, so there was no rung to read.
The basis-aware successor needs `0016`'s frozen `evidence_basis`; **v1
does not unfreeze it**, and the successor is recorded as blocked on
0016's own round. `0008`, `0012` and `0016` join `Spec-Requires`.

**The rider could not have measured anything.** Refusal rows carry no
cell code, and the deciding population — allowed by the narrow rule,
refused by the broad one — produces NO REFUSAL ROW AT ALL. Counting
refusals would have returned zero for the wrong reason and confirmed the
claim it was meant to test. Folded at round 1 as a cell code and a flag
on the existing carrier plus a counts-only counter — and
ROUND 2 deleted the flag as constant-true and the columns with it; see
§12.

**0011-R1-2 — E5 binds an asserted identity; it does not authenticate.**
v4 called the authorisation "unforgeable" and said it "authenticates
CORRECTORS". `0020` states that `principal` is host-supplied, forgeable
and unauthenticated, and `Memory.correct()` mints the authorisation from
caller-controlled values — so a caller may name any principal, obtain a
fresh authorisation and pass the in-transaction check. The
cross-principal replay test blocks REUSE, never fresh impersonation.
Folded: the claim is withdrawn; the binding is INTEGRITY and
ATTRIBUTION, stated as such in all three carriers that made the claim;
`correct()` is a protected host API on 0008's model with the host's
authentication and intent obligations written down; the externally
issued capability that WOULD authenticate is named as out of scope for
v1 rather than implied.

**0011-R1-3 — E3 misclassified same-value restatements.** v4 defined
contention as ≥2 active same-class edges. Accepted `0012` deliberately
persists a same-value restatement as a separate active edge and says
such a pair is not contested; the reviewer ran
`test_a_same_value_restatement_produces_no_contention_artifacts`
(1 passed) on exactly that shape. v4's rule would have labelled every
renewal in the store a contradiction. Folded: ≥2 DISTINCT normalised
`_value_key` values, using `0012`'s own normalisation so the two cannot
drift; composition with `0003`, `0012`, budgeting, scoping, proactive
reach and cache semantics stated; **"maintain neither resolves" narrowed
so it does not suspend `0012`'s per-edge expiry** — contention suppresses
resolution verbs, never lifecycle; `lifecycle.py` added to §7a.

**0011-R1-4 — the invalid-input contract contradicted itself.** §4d said
a malformed `from_class` is both refused by the constructor and floored
to `derived(THIRD_PARTY)`. Those are different observable outcomes and a
spec naming two cannot be conformed to. Folded: it RAISES and nothing is
written. ABSENCE is a different input and keeps the floor — a host that
supplies nothing has declared nothing; one that supplies garbage has
declared something untrue. The complete `direct`/`derived` grammar is
enumerated with every cell reachable, and the adversarial matrix named.

**0011-R1-5 — S6's labels were neither total nor exclusive, and their
premise was false.** Executed: an active, quarantined, grounded,
uncontested edge matched ZERO labels; an active, mentionable, grounded,
contested edge matched TWO. And `compile.py` reads `active_only=True`,
`introspect.py` already separates retired, `gate.partition_parts` drops
inactive — **no shipped reader interleaves history with present fact**,
so the defect E6 claimed to fix was not there. Folded: a five-row
first-match precedence table, total by catch-all and exclusive by
ordering, with `QUARANTINED_CLAIM` and `CONTESTED_CURRENT` added
(v4 had no cell for either, which is why an edge could match none or
two); the invariant asserted over the cross-product rather than sampled
cells; and E6 re-motivated to what it earns — one vocabulary for states
this spec introduces — with the false premise retracted in place.

**PACKAGE-R1-1 — the deciding measurement was not reproducible.** No
`specs/evidence/0011/` existed; the archive could not re-derive any
reported figure. Folded: `subject_census.py`, a counts-only aggregate
digest-bound to the same cache sha as 0025's census, and the
distinct-string candidate table the hand classification was made over,
with given names masked. `--aggregate` reproduces every figure without
the corpus. **The load-bearing figure reproduces exactly — 183,417
triples, 72,253 predicate passes, 39.4%. Two prose figures did not and
are RETIRED**: v4's 305 candidates = 0.166% and ≈30 self-denoting
≈0.016% came from a regex family that was never recorded; the recorded
one finds 337 over 94 distinct strings, of which 31 = 0.017%. The
conclusion is unchanged and marginally stronger. This is the 0001 R11-1
lesson — packaged figures are GENERATED and BOUND — reaching a second
line, which it should have done before this package was sealed.

## 12. Changes in v6 — the round-2 fold (2026-08-27)

Round 2 returned v5 for major amendment. **Four of the five findings were
defects in round 1's own fixes**, which is what the found-in-fix checklist
exists to prevent and I did not run on that fold.

**0011-R2-1 — `source_id` had become an entitlement capability.** Round 1
defined both `sourced` and `self_assertion` from `source_id` presence,
because it was state that existed. The reviewer executed what that bought:
omitting the prior's `source_id` ALLOWED the retirement, and adding any
`source_id` to the incoming assertion ALLOWED it too. Accepted `0006` says
in four places that `source_id` **may GROUP, never GRANT** — optional,
host-supplied, diagnostic, and its absence must not relax a decision — and
`0006` was not even a declared prerequisite while its carrier decided
authority. The fix is not to read the field more carefully but to STOP
READING IT: `sourced` is gone, and the rule refuses on subject class plus
self-assertion alone. That refuses MORE — the narrowness is lost with the
distinction — and the cost is stated rather than absorbed. `0016`'s frozen
`evidence_basis` is the carrier that would restore it; v1 does not unfreeze
it. A source-identity invariance matrix is now owed: the decision must be
unchanged under presence, absence, forgery, foreign origin and import.

**0011-R2-2 — a field that could not vary.** `would_refuse_broad` was
CONSTANT TRUE, because the broad predicate is a strict superset of the
narrow one. It is deleted. Round 1 also proposed two new columns while §7a
named no schema, migration, erasure or telemetry surface and §7 claimed
there was no stored state to unwind — three statements, two false if the
columns shipped. The rider now adds NO stored state: counters on `0015`'s
existing carrier, no column, no migration, nothing to erase. §7 is true
again, and `0013` is not a prerequisite because there is no schema change.

**0011-R2-3 — two contracts called `contested`.** The checker validated a
standalone value-list function — a reimplementation, not the rule any
reader sees. The reviewer inserted two active, same-class, distinct-value
edges into a real store: v5's predicate said contested, the shipped
`Recall.contested` said 0 groups and 0 exposed members. `compile.py`
states the shipped contract outright — REFUSAL-scoped, not every
contention — so this spec adopts it and defines nothing new; E3 governs
the RENDERING of that set across `Recall.contested`, gate, maintain,
import and direct-store insertion. The checker now drives a real store and
asserts both the reviewer's cell (direct pair → NOT contested) and a
positive control (a live refusal → contested), so it cannot pass by never
firing.

**CARRIER-R2-1 — contradictory text passed a green checker.** Seven
authoritative statements survived round 1: §3a's UNFORGEABLE, §3c's
"confirmation, a higher rung", §5's "can no longer forge", S5's doubled
malformed-input outcome, S6's three labels, S7's denial that any rule
reads disclosure, and E-Q1's retired figure. The checker searched narrow
phrases across the whole file, so a withdrawal written in §4e satisfied it
while §3a still asserted the opposite. All seven are swept, and each
assertion is now bound to its NAMED ROW — a withdrawal written elsewhere
cannot satisfy it. **S6 is checked count-to-count**: the row carries
`labels=5` as a token and the checker compares it to the actual number of
rows in §4f's table. That last change came from this fix's own failure —
the first attempt searched for "three labels", and the row says "one of
the three", so the guard looked for wording the spec never used and the
contradiction survived a second time.

**EVIDENCE-R2-1 — the census verified nothing in aggregate mode.** A
one-entry aggregate with an all-zero digest printed the claimed
measurement and exited 0. The aggregate now passes a CLOSED typed schema
(missing and unknown keys both refused) and every figure it asserts about
the cache is cross-checked against `0025`'s aggregate — derived from the
same cache by a different script, shipped in the same archive — including
a triple total independently derived by summing 0025's relation counts. A
fabricated manifest must now agree with an artifact its author does not
control. Seven fabrications tested, all refused; the real aggregate still
verifies. This is `0001`'s R12-1 arriving in a second place, again after
the fact rather than before.

## 13. Changes in v7 — the round-3 fold (2026-08-27)

Round 3 returned v6 for major amendment. Three of the four findings were
again defects in the previous round's fixes, and the shape had become a
pattern worth naming rather than folding past.

**0011-R3-1 — `derived(USER)` bypassed the rule, exactly as `source_id`
had.** `EvidenceContext.derived(USER)` is valid and reachable, and
`USER/derived_from=USER` carries effective authority **3 — identical to
`USER/None`** — yet v6 refused one and allowed the other. A marker
supplying no independent authority bought permission to retire an
OTHER-subject fact.

That is R2-1 one field over. R1 defined the rule over `source_id`; R2
found `source_id` grants and it moved to `derived_from is None`; R3 found
`derived_from` grants. **Each round replaced one unauthenticated marker
with another and inherited the class**: the defect was never the field,
it was keying on a marker's PRESENCE rather than on AUTHORITY.

The predicate is now `effective(author, derived_from) == effective(USER,
None)` — the chain carries nothing but the user's own authority, computed
by `0003`'s own function. Enumerated against production authority exactly
two chains qualify, so R3-1's cell sits in the refusal set BY
CONSTRUCTION. `specs/evidence/0011/policy_matrix.py` is the §6 acceptance
surface: 240 cells over author × derived_from × subject class × source
presence × origin, asserting totality, the named cell, **the general
property that equal effective authority decides equally**, invariance
under source identity and origin, that `derived_from` never raises
authority, and that a SELF-subject prior is never refused. Both defects
that actually shipped were planted against it and both are caught — the
absence-based one by the generalised check, which is the property that
would have ended this at round 2. §4b's decision table is GENERATED from
the matrix and bound to it.

**0011-R3-2 — the rider assumed another spec's deferred consent
surface.** `0015` defers refusal counters to a new consent discussion,
requires consent-version gating for new payload fields, and counts only
from a fresh commit — excluding replays and stale attempts. v6's rider
contradicted all of it and would have overcounted aborted and
`PLAN_STALE` attempts. **This was the third round in which I asserted a
rule over another spec's contract without checking that contract's
domain**, after `0006` and `0012`. The rider is WITHDRAWN: v1 ships with
the broad rule's constituency unmeasured, states that plainly, and leaves
both the consent question and the telemetry construction to `0015`'s own
round.

**CARRIER-R3-1 — the sweep was still incomplete and the check was
syntactic.** Five more contradictions survived: S5's doubled
malformed-input outcome, §4b claiming `sourced` is defined here after its
removal, the term table still listing `source_id`, the regime row scoped
to sourced priors when unsourced ones now refuse too, and §7a justifying
portability on a participation that no longer exists. All five swept. And
the reviewer defeated the no-`source_id` check by moving the read behind a
helper defined in a SEPARATE FENCE — every check still passed. The check
now follows the predicate's TRANSITIVE DEPENDENCIES across fences: both
the reviewer's bypass and a deeper two-hop version are closed.

**EVIDENCE-R3-1 — the deciding figures were still self-asserted.**
`schema` was typed and never valued, so `schema = 999` with
`predicate_passes = 0` produced no findings. `schema == 1` is required
now. More usefully, `0025` turns out to carry subject data for one
subpopulation — `subject_user` over `third_party_claim` — so **the
predicate itself is cross-checked: 1,606 of 3,945, two scripts, same
answer**. That does not bind the whole-corpus count, and the package no
longer implies it does: every figure is labelled by what backs it, and
`predicate_passes` (72,253) plus the candidate table's completeness are
marked **RECORDED ONLY**, reproducible with `--cache` on the measuring
host and not from the archive alone. A reader without the corpus is
trusting dev for those two, which is stated rather than papered over.

## 14. Changes in v8 — the round-4 fold (2026-08-27)

**Round 4 granted FINITE DESIGN ACCEPTANCE for v7's core construction:
the authority-chain design need not be reopened.** Three mechanical
findings gate the status flip; all three are closed here.

**EVIDENCE-R4-1 — the 240-cell oracle had decorative dimensions.** Source
and origin were enumerated in `cells()` and never passed to `policy()`,
and the invariance check re-called the function instead of comparing the
EMITTED cells — the reviewer flipped one emitted cell to a
source-conditional ALLOW and the oracle exited 0 while printing that
source identity was invariant. An oracle that does not consume its own
output certifies its inputs, not its subject. The oracle is FULL-EDGE
now: the decision's inputs are two real `Edge` objects whose provenances
carry independent source and origin values (1,440 cells), every check
derives from the one emitted stream, and the import-flattened cell runs
through production `portability.import_memory` in both modes — the
default cap flattens the author and the decision follows it; restore
preserves the author and the refusal returns. Separately, the fold
checker's dependency closure kept only the LAST definition of a helper
name, so a dangerous `sourced()` shadowed by a benign redefinition
passed; the closure now carries EVERY definition of a name, and a read in
any copy is a read. Both attacks are standing mutation tests in
`tests/test_0011_policy_matrix.py`, replayed exactly as the reviewer ran
them.

**CARRIER-R4-1 — the round-3 sweep was still incomplete.** Five carriers
swept: §4's claim and S2 now state the BROADENED rule (any OTHER-subject
prior, sourced or not — R2-1 removed the qualifier's only carrier); §4b's
pointer at "the rider below" and §9's reviewer ask both now state the
rider is WITHDRAWN, and §9 redirects the reviewer at the deferral itself;
S5's unclosed editing fragment is repaired. Historical sections keep the
old wording as history.

**PACKAGE-R4-1 — the built header contradicted the package's own
lineage.** The line's templates carried a hand-written "THE FIRST SEALED
PACKAGE ON THIS LINE" paragraph from the line's creation, so v4's header
asserted first-package and "sealed rounds 1–4" in the same file, beside a
CHANGED_FROM_PREVIOUS inventorying the v3 delta — and every header check
passed. The sharpest part: the template's own C5-1 note, SEVEN LINES
ABOVE the paragraph, already records this exact defect from the 0022
line ("static prose here once claimed first sealed package on the line's
third sealed round"). The paragraph — and a second static claim, the
round-count sentence — are deleted from every template on both lines, and
`seal_package.WITHDRAWN_CLAIMS` now REFUSES both shapes at seal time, in
wording the sealer's own derived NO_PRIOR text deliberately does not use.
`test_no_template_hand_asserts_lineage` proves the ban bites and that the
derived wording never trips it. Lineage facts now have exactly one
source: the governed record.

## 15. Changes in v9 — the round-5 fold (2026-08-27)

Round 5 returned exact v5 for two mechanical amendments; the finite
acceptance remains in force and no architectural defect was found.

**EVIDENCE-R5-1 — cell count does not prove domain coverage.** The oracle
required 1,440 emitted rows; the reviewer replaced one cell with a
duplicate of another and the count held while a source/origin combination
silently vanished — cardinality-preserving omission, and `problems()`
returned nothing. The oracle now constructs the EXACT expected Cartesian
key set independently of the emitter and requires the emitted keys to
equal it — set equality names a missing key and an alien key, and
duplicates are rejected separately so the replacement itself is named
rather than hiding behind the missing-key report it causes. The
reviewer's replay and an alien-key variant are standing tests beside the
round-4 attacks.

**CARRIER-R5-1 — §3c still carried the withdrawn rider, in a LIVE
contract row.** The row described the OTHER-subject refusal as "narrow by
ruling, with the measurement rider", and the fold checker exited 0
because it found "THE RIDER IS DEFERRED" elsewhere in the file — a
file-wide search satisfied by a different section's deferral text. The
row is swept (the rider is withdrawn, the narrow/broad question ships
unmeasured and stated as such), and the withdrawal is now BOUND TO THE
ROW: the checker anchors on §3c's row and refuses the promise there
specifically, with the planted-back promise verified biting. A deferral
stated in §4b does not un-promise a different row.

## 16. Changes in v10 — the round-6 fold (2026-08-28)

Round 6 returned exact v6 for two mechanical evidence amendments; the
finite acceptance stands and the status flip is blocked only by evidence
machinery.

**EVIDENCE-R6-1 — an enum-derived dimension still self-narrowed.** The
round-5 fix pinned the hand-picked dimensions and deliberately left the
enum-derived ones unpinned as "growing legitimately with the enum" — half
the truth, since they also SHRINK silently: removing `THIRD_PARTY` from
`DERIVED` changed the claimed domain from 1,440 to 1,152 cells with exit
0, both the emitter and the expected key set reading the same constants.
The enum axes are pinned to the enum itself now (`AUTHORS ==
tuple(EvidenceAuthor)`, `DERIVED == (None, *tuple(EvidenceAuthor))`), the
expected keys are built directly from the enum, and the narrowed-`DERIVED`
mutant — plus a narrowed-`AUTHORS` sibling — is a standing test.

**PROCESS-R6-1 — the campaign record was prose, and false in two ways.**
It claimed every fix carried a standing test while nine mutants (F1–F4,
C1–C4, the row-unbound withdrawal) had none — verified by shell plants
that died with the session — so neutering the entire census-figure binding
left every test green. And its totals were hand arithmetic that did not
add up (4+9+6=19, the record said 15). Folded: the campaign is EXECUTABLE
— `mutant_registry.py` binds each id to its artifact, mutation and pytest
node, executes all of them in one invocation, and writes
`mutant_results.json` with totals DERIVED from what ran (currently 21
entries: 6 reviewer-found, 15 dev-found, over 18 nodes). The nine
untested mutants now plant their attacks in memory as standing tests;
every fold check is sentinel-proven REACHED by `main()` so a dropped
check is loud; the census-figure binding takes an injectable aggregate so
fabrications are testable without touching disk; and `subject_census.py`
— a validator outside the `check_*`/`verify_*`/`validate_*` filename
convention that had already produced findings in three consecutive rounds
— enters P1's domain through an explicit artifact registry, with the full
registry-not-convention escalation named if that list grows. The prose
record now states that the GENERATED record is authoritative and that a
narrative about tests is not tests.

## 17. Changes in v11 — the round-7 fold (2026-08-28)

Round 7 returned exact v7 for one mechanical evidence amendment; the
finite acceptance stands and the enum correction was confirmed sound.

**PROCESS-R7-1 — registry entries were not bound to executed mutants.**
The runner derived success from the distinct pytest nodes: a fictitious
entry with a nonexistent artifact, no real mutation and an already-listed
passing node made 22 entries over the same 18 nodes with exit 0. Nothing
validated artifact paths. And `mutant_results.json` was WRITE-ONLY —
overwritten by every run, read by nothing, so a stale or corrupted
shipped record would be silently replaced during review.

The binding now comes from the EXECUTED side. Each standing test, after
its assertions succeed, reports the mutant id(s) it just killed into a
kill log the runner owns (`record_kill()`; a no-op outside the runner).
The runner requires the reported kills to equal the declared ids
EXACTLY — an entry nothing kills, a kill nothing declares, and a double
report are all named. Artifact paths must exist; duplicate ids are
refused. The default invocation is a non-mutating **check**: it re-runs
the campaign, rebuilds the record, and requires it to equal the shipped
`mutant_results.json` on the whole record — `--write` is reserved for
seal time. The reviewer's bogus-entry attack, plus ghost-artifact,
phantom-kill, double-kill and corrupted-record variants, are standing
regressions calling the runner's pure functions.

## 18. Changes in v12 — the round-8 fold (2026-08-28)

Round 8 returned exact v8 for one mechanical registry amendment; the
finite acceptance stands and no policy, authorization, contention or
trust-model defect was found.

**PROCESS-R8-1 — the ledger validated projections, not complete
bindings.** Three adjacent gaps, each executed by the reviewer and each
reproduced here before fixing:

1. **Kills were bound globally.** The kill log was a bag of ids, so
   swapping the nodes of two entries changed nothing — every id still
   appeared "somewhere". Kills are **(node, id) pairs** now, with the
   node taken from pytest's own `PYTEST_CURRENT_TEST` rather than
   supplied by the caller, and the runner requires exact pair-set
   equality: an id reported by a different node is a misbound entry.
2. **"Byte-for-byte" was dict equality, which coerces.** `executed.exit`
   changed from `0` to `False` claimed an exact match, since `False ==
   0` in Python. The check now pins exact int types (`type(x) is int` —
   bool is an int subclass) and compares **canonical serialized bytes**,
   where `"false"` is not `"0"`.
3. **Artifact validation accepted `/etc/passwd`.** `ROOT / "/etc/passwd"`
   IS `/etc/passwd` — pathlib discards the left operand when the right is
   absolute. Paths must now be plain relative, contain no `..`, resolve
   inside the package root, and be regular files; absolute, traversal and
   directory variants are all refused.

All three attacks are standing regressions at the real checker boundary
(`tests/test_0011_mutant_registry.py`), and the shipped record was
regenerated under the new schema and verified by the non-mutating check.

## 19. Changes in v13 — the round-9 fold (2026-08-28)

Round 9 returned exact v9 for two mechanical evidence amendments; the
finite acceptance stands, the three v8 attacks were confirmed closed, and
no design or trust-model defect was found.

**PROCESS-R9-1 — per-node provenance was not behaviorally bound.** The v8
regressions fed `binding_problems()` honest hand-built kills, so a
reporter rewritten to look up each id's node FROM THE REGISTRY ITSELF
reproduced whatever mapping the registry declared — a node-swapped
registry passed `--write`, `--check` and the whole focused suite. Folded:
an integration regression sends the swapped registry through the REAL
execution (a live pytest run, attribution taken from pytest's own
environment) and requires binding failure — if `record_kill` ever
self-asserts, that test fails; and the runner independently refuses any
reported node it did not itself invoke.

**EVIDENCE-R9-1 — the record lacked a closed canonical grammar.** Four
holes, each executed: duplicate JSON keys vanished in parsing (a
prepended `"schema": false` was discarded by `json.loads`, which keeps
the last value); `found_by` was an open vocabulary, so `banana`
regenerated cleanly and the totals grew an ungoverned partition; the
refusal branches could be deleted with every test still green, because
the checks were exercised as functions and never as the behavior
`main()` runs; and the schema stayed 2 across the killed-shape change.
Folded: duplicates refuse AT PARSE (`object_pairs_hook`); a recursive,
exactly-typed, closed schema governs every level — `found_by ∈
{reviewer, dev}`, closed totals keys, `type(x) is int` so bool never
passes; the check compares the shipped file's RAW BYTES to the canonical
writer's exact output, so a parse-normalise round trip blesses nothing;
the schema is 3; and the corrupt-record family — duplicate key, alien
partition, bool-for-int, the old killed shape, an ungoverned totals key,
non-canonical whitespace — is refused BY MAIN ITSELF in standing
subprocess regressions, with the shipped record as the passing control.

## 20. Changes in v14 — the round-10 fold (2026-08-28)

Round 10 returned exact v10 for one blocking process amendment plus one
nonblocking maintenance item; the finite acceptance stands and no design
defect was found.

**PROCESS-R10-1 — per-node provenance remained self-assertable.** The
round-9 integration regression swapped a LOCAL copy of the entries and
passed it to `execute()`, but the child pytest process imports the
ON-DISK registry — so the coordinated attack (swap R4A/F1 on disk AND
rewrite the in-artifact reporter to look up nodes from `ENTRIES`) passed
`--write`, `--check` and all 31 focused tests: the test's local swap
reversed the on-disk one while the child self-reported from the mutated
module. Reproduced exactly before fixing.

The fix removes the thing the attack needs: **the artifact no longer
performs attribution at all.** The reporter is a 4-line id-only writer
living in the TEST files; the runner executes each distinct node in its
own isolated pytest invocation and joins every reported id to the node
IT invoked. A self-asserting reporter has nothing left to assert — it
cannot name a node, and an id emitted from the wrong test lands joined
to that test's node and mismatches the declaration. The coordinated
on-disk mutation is the standing regression: the swapped registry is
written to disk as a real module and driven through its own real
execution, where it must fail.

**EVIDENCE-M10-1 (nonblocking, fixed) — the shipped-record operand was
environment-selectable, and "grammar FIRST" was not.** The
`VERACIUM_MUTANT_RECORD` selector — introduced solely for testing — let
the checker be pointed at a pristine alternate file while the real
record sat corrupted; and the check ran the full campaign BEFORE
parsing. The entry point is pinned to the shipped record with no
selector of any kind (a standing test asserts the variable's absence
from the source); corrupt operands are exercised through an internal
helper on copies; and the order is now parse → closed schema →
canonical-form-of-the-bytes-themselves → only then the campaign, so a
corrupt record refuses in milliseconds and non-canonical serialisation
is detected without a recomputation at all.

## 21. Changes in v15 — the round-11 fold (2026-08-28)

Round 11 returned exact v11 for one mechanical process amendment; the
finite acceptance stands and no policy or trust-model defect was found.

**PROCESS-R11-1 — the kill-claim protocol itself was the attack surface,
so it is gone.** Two halves, both reproduced before fixing:

1. *The round-10 regression was fail-open.* Its copied registry module
   derived `ROOT` from its temporary location, pytest exited **4** with
   nothing collected, and the empty kill list produced exactly the
   binding mismatch the test expected — it passed while executing
   nothing. Reachability of the failure is not the right CAUSE of the
   failure: an outcome asserted without asserting the mechanism ran is
   the K2 lesson, landed this time on the regression itself.
2. *The id half of every kill was still a claim.* The runner owned the
   node label, but a reporter rewritten to ignore its arguments and
   derive ids from the registry via pytest's current-test variable —
   coordinated with a swapped on-disk registry — passed `--write`, the
   default check, and the full focused suite.

Rounds 7–10 each hardened WHO could claim a kill; round 11 shows any
claim protocol is one coordinated rewrite away from circular. Schema 4
removes the protocol: **each registry entry now carries its mutation as
text hunks, and the runner applies them itself and OBSERVES the outcome.**
A kill is `node passes on the clean tree AND fails (exit 1, failures ≥ 1)
with the entry's hunks applied` — both facts observed by the runner from
exit codes and summary counts, with every hunk's old text required
exactly once at application and every artifact restored byte-identically,
verified. A collection error, usage error, or empty run is a campaign
ERROR, never a kill. There is no reporter, no kill log, and no id anybody
reports: a swapped registry now applies one artifact's mutation and runs
the other entry's node, which passes — an observed SURVIVAL, refused in
both modes (replayed against the shipped file before this fold was
committed: check exit 1 naming both survivals, `--write` refuses).

Where the historical scenario-mutants were redundantly defended, the
entry carries the **minimal hunk set** that defeats every layer, and the
runner verifies minimality by leave-one-out: each dropped hunk must leave
the node PASSING, proving that layer individually load-bearing. The hunk
count is thereby a measured witness of defense depth (M3's
narrowed-SUBJECTS attack takes four simultaneous neuters; C2's gutted
candidate table takes two). 21 entries, 25 hunks, 6 minimality witnesses,
all runner-observed.

Hardening the new machinery before reseal (dev's own campaign, plus the
found-in-fix checklist item 9): a hunk aimed at a TEST file or at the
registry itself is refused at validation (mutating the judge manufactures
the verdict); node ids are pinned to a plain-`tests/` grammar so pytest
options cannot be smuggled; a syntax-breaking hunk lands as ERROR, not
kill (verified); a dead subprocess at either phase is a named refusal
with no baseline (the round-11 fail-open, now a standing test at the
REAL root); and **the campaign never mutates the live tree** — found
the hard way when two interleaved campaigns froze R4B's
last-definition-wins hunk into the fold checker on this tree. A lock was
the first answer; the snapshot design below superseded it, removing the
class instead of serializing it. The absence of any claim channel is
itself a standing test (no reporter function, no kill-log variable, no
pytest-side attribution — needles assembled so the test's own source
cannot satisfy them).

Research's pre-dispatch red-team pass (the C5 batch discipline) triaged
six false-PASS classes before this seal. Three were closed by design and
are now stated as such: there is NO tolerated-survival category (any
survival is exit-nonzero in both modes, so a kill-to-survival conversion
is loud); a crash-frozen mutation refuses pre-campaign, because
`validate_entries` re-checks every hunk's exactly-once text before any
run; and the record is parse-validate-recompute-compare, never an input
to a verdict. F-E was then generalized past its own fix: the campaign
now runs in a **private snapshot** of the tree (src, tests, specs minus
archives), so the live tree is read-only to it by construction — the
crash window, the concurrent-campaign hazard, and the
closure-evidence gate's concurrent ledger commands (which read the
artifacts while a sibling command runs the campaign) all vanish rather
than being individually guarded. Two campaigns running concurrently
while the live artifact stays byte-identical is the standing test.
Research's executable pass against the pushed fold (`cf06440`) then
confirmed every planted attack refuses — shadow-copy, comment
relocation, dead code, path escapes, symlink-through-the-snapshot (the
copy DEREFERENCES, so a hunk writes to the snapshot regular file, never
through a link) — and returned one residual, closed before seal: the
mutable-artifact set was a DENY-list ("not tests/, not the registry"),
the polarity this arc exists to refuse — it silently admitted a future
conftest.py and off-path src functions (a genuine kill of an unrelated
defense would inflate the depth metric). The set is now
inclusion-defined: `MUTABLE_ARTIFACTS` is the closed four-file
allowlist the campaign is entitled to mutate, membership is checked
FIRST, and widening it is a reviewed edit pinned by a standing test. Three were built: **F-B, the proxy-kill** — an observed
failure proves the test NOTICED the hunk, not that the hunk touched the
defense, so every entry now names the top-level function or constant it
`defends` and validation locates that span by ast and refuses any hunk
whose old text falls outside it (a fixture/helper/constant hunk can only
buy a proxy-kill; refused mechanically, standing test); **F-C,
skip-laundering** — the clean gate requires passed ≥ 1 AND zero
skipped/xfailed/deselected, so a marker cannot make exit 0 mean nothing;
**F-D, environment injection** — the runner scrubs PYTEST_ADDOPTS and
PYTEST_PLUGINS and disables plugin autoload, so nothing outside the tree
joins the verdict.

Two incidents during the work, both kept: a killed campaign left a
frozen hunk in the live tree — `validate_entries` refused loudly at the
next invocation, and the snapshot design then removed the whole class
(a crash now costs a temp dir). And a **stale-bytecode hazard found
live**: pyc invalidation is mtime+size, the hunks are often
length-preserving, and patch→run→restore cycles fit inside one mtime
second — a run can execute another run's cached semantics and report a
false survival or a false kill (R5A surfaced it as a nondeterministic
survival). Every campaign subprocess gets a fresh private
PYTHONPYCACHEPREFIX, bypassing adjacent caches entirely.

Closed from v14: EVIDENCE-M10-1 confirmed closed by the reviewer (pinned
operand, genuine grammar-first ordering).

## 22. Changes in v16 — the round-12 fold (2026-08-28)

Round 12 returned exact v12 for one mechanical process amendment;
PROCESS-R11-1 is confirmed substantively closed (reporter protocol gone,
baselines require collection and passes, exit-4 and empty runs refused,
the R4A/F1 swap yields two SURVIVED and exit 1, snapshots isolate, the
selector remains absent) and no policy or trust-model defect was found.

**PROCESS-R12-1 — duplicate mutations inflate the observed ledger.**
R5A duplicated under a fresh `DUPR5A` id passed everything: unique-ids
held, `--write` produced 22 entries / 26 hunks, `--check` exited 0, the
focused suite stayed green — and the totals reported a dev mutant that
was a second label for a reviewer's. Reproduced exactly before fixing.
The diagnosis is carrier-completeness (checklist item 5): schema 4 moved
the mutant's IDENTITY from the id string to the hunk bundle, and
uniqueness stayed enforced on the old carrier. Every observation was
genuine; only the record's totals lied — R7-1's fictitious entry, reborn
in the observed protocol. Neither dev's own campaign nor research's
red-team pass had asked the question this finding answers: what makes
the RECORD lie while every run is honest?

The fix, in two faces because research's pre-seal pass broke the first
form the same day: the canonical identity of a mutation is the sorted
bundle of its hunks' **minimal-diff identities** — common prefix and
suffix stripped between old and new (whitespace folded), pinned to the
edit's absolute POSITION in the artifact. The first form — the full
(artifact, old, new) text — was CONTEXT-WINDOW SLIDABLE: research
planted "emitted_keys.count(k) > 1", "keys.count(k) > 1" and
"count(k) > 1" as three exactly-once, in-span old-texts of the same
single edit, three "distinct" bundles, one defense probed three ways.
The minimal diff is window-invariant; the position keeps the same edit
text on a different line a genuinely different mutant. Duplicates
refuse whatever their id, finder, node, description, hunk order or
window, on BOTH carriers (the entries validator and the record
grammar). `run_check` now fails fast on
entry problems before spending ~45 subprocess runs on a ledger already
known to lie, which also puts the refusal at the real `--check`
boundary; `--write` refuses without writing. The standing regression
drives the reviewer's exact DUPR5A registry through both real
boundaries on disk, with a latency assertion proving the refusal
precedes the campaign.

The class, enumerated past the named cell (item 2): a hunk-order
permutation and a whitespace variant fold into the same identity
(refused); a cross-node or cross-finder duplicate is still one mutant
(refused — a mutant killed by two tests is one mutant); a SUBSET bundle
riding a killer hunk was already refused by leave-one-out minimality
(the extra hunk is not load-bearing). The honest boundary: a
semantically-equivalent but textually-distinct duplicate is not
decidable and remains possible in principle — and remains VISIBLE,
because the hunks ship in the record as data a reader can diff.

## 23. Changes in v17 — the round-13 fold (2026-08-28)

Round 13 returned exact v13 for one mechanical process amendment;
PROCESS-R12-1's exact-duplicate and context-window attacks are confirmed
closed, and no policy or trust-model defect was found.

**PROCESS-R13-1 — hunk partitioning defeats mutation uniqueness.** The
identity was still a function of the hunk DECOMPOSITION: C2's two edits
encoded as one wider hunk spanning both sites produce byte-identical
mutated artifacts under a distinct identity — `--write` accepted 22
entries, `--check` exited 0, and the cardinality-preserving variant
(C1 removed, the merged duplicate kept) held 21 entries and unchanged
finder totals while one historical mutant vanished and another counted
twice. Reproduced exactly before fixing.

This is **face four of one finding**, and the ladder's shape is now
explicit: id string (face 1, a fresh label), full old/new text (face 2,
the window slides), minimal diff plus position (face 3, closed the
window), hunk partitioning (face 4 — the decomposition slides). Each
fix normalized a richer *description* of the mutation; the terminal
form has no description left to vary: **the canonical identity is the
resulting artifact transformation** — per artifact, the sha256 of the
bytes produced by applying the entry's complete bundle to the pristine
file. Any decomposition that produces the same mutated bytes is the
same mutation; any that produces different bytes is a different one.
Duplicates refuse on both carriers, `run_check` still fails fast before
any campaign subprocess, `--write` still refuses without writing, and
both of the reviewer's attacks — the merged-C2 duplicate and the
constant-cardinality replacement — ride as standing regressions at the
real on-disk boundaries (with the copied module pinned to the real
root: the round-11 fail-open lesson, applied to the new test itself).

Research's pre-seal pass then named the one seam left in "the bytes":
for ORDER-DEPENDENT hunk bundles (one hunk's new text creating or
destroying another's old text), the resulting bytes depend on the apply
path — and the identity was a *second implementation* of the apply
algorithm that merely happened to agree with the campaign's. Today's
bundles are pairwise disjoint, so the seam was unreachable; it is
closed by construction rather than by luck: **identity and campaign
share one apply function** (`_apply_hunks_to_text`, per artifact, in
entry order), so digested bytes and executed bytes are the same
computation and cannot disagree. Order-dependence is thereby
well-defined rather than forbidden; an unappliable order degrades
loudly instead of digesting bytes that would never run. The standing
test proves it behaviorally on a genuinely dependent bundle: the
identity's digest equals the sha256 of the file the campaign's own
applier leaves behind, and the reversed bundle refuses.

The named boundary moves with the identity, honestly: whitespace
variants of the *inserted* text now produce distinct resulting bytes,
so they sit with the semantically-equivalent-program class. A second,
whitespace-folded digest screen refuses the cheapest of those for
human review; the deeper equivalence remains undecidable, named, and
visible as record data.

## 24. Changes in v18 — the round-14 fold (2026-08-28)

Round 14 returned exact v14 for one mechanical process amendment;
PROCESS-R13-1 is confirmed substantively closed (the merged-C2
duplicate, the original constant-cardinality substitution, and the
reviewer's stronger 21-entry/25-hunk/17-node/15-6-split replacement all
refuse at both real boundaries before any campaign run), and no policy
or trust-model defect was found.

**PROCESS-R14-1 — identity reads untrusted paths before validating
them.** The round-12 restructure put the duplicate-identity check ahead
of the per-hunk path checks (deliberately, for root-independence), so
`_identity` would read whatever path a hunk named; and the record
carrier had no path validation at all. Executed counterexamples,
reproduced before fixing: a record hunk naming `/etc/passwd` validated
CLEAN (the R8-1(3) pathlib footgun — `ROOT / "/etc/passwd"` IS
`/etc/passwd` — reachable through the new code path); `/bin/sh` was
read and crashed both carriers with an uncaught UnicodeDecodeError.
The classification is order-of-operations plus carrier-completeness:
the entries carrier had the guard in the wrong ORDER, and the record
carrier (item 5) never received it.

The fix: **one shared guard** (`artifact_problems`) — allowlist
membership as a pure string check FIRST (an out-of-set path refuses
with no filesystem access at all), containment and regular-file status
as depth behind it — run in BOTH carriers before identity touches the
filesystem; entries failing the guard are excluded from identity
dedup and refused loudly. `_identity` is additionally defensive in its
own right: it will not read an absolute, escaping, or missing path and
degrades on unreadable bytes instead of crashing — validation refuses
such entries; identity merely guarantees no read happens on the way
there. The standing regression drives `/etc/passwd`, traversal, and
`/bin/sh` through BOTH carriers at the real entry point, with the
no-read witness built in: reading `/bin/sh` raises, so a clean named
refusal without a traceback proves the read never happened (plus a
latency bound proving no campaign ran). One test-side consequence
kept honestly: the round-12 DUPR5A regression's copied module claimed
root-independence the guard deliberately removed — it is now pinned to
the real root, the R11 lesson applied a second time.

Research's pre-seal pass then answered the question this fold asked
("is there a path shape that still touches outside the tree?") in the
affirmative, one layer down: **the snapshot itself** — `copytree` with
`symlinks=False` DEREFERENCES, so a committed symlink anywhere under
the copied dirs is a read of its target (escaping if the target does),
and the artifact guard never sees it because the snapshot copies the
whole tree, not the four guarded artifacts. Not a false-PASS vector
(it reads into a throwaway temp dir; a broken target fails closed;
planting it requires committing a symlink — a visible act outside the
entry-driven threat model), but "the guard runs before anything
touches the filesystem" was not fully true while the snapshot
dereferenced the unguarded remainder. Closed in the same round, per
the round's own theme: a pre-scan without following links refuses on
the FIRST symlink, before any copy — a symlink in this tree is
anomalous, so the posture is error, not skip. The standing test plants
a link to `/bin/sh` and requires the named refusal with no snapshot
produced.

## 25. Changes in v19 — the round-15 fold (2026-08-29)

Round 15 returned exact v15 for one mechanical process amendment;
PROCESS-R14-1 is confirmed closed on its requested surface (named
refusals with no traceback and no campaign for /etc/passwd, traversal
and /bin/sh, on both carriers; the defensive identity degrades without
reading), and no policy or trust-model defect was found.

**PROCESS-R15-1 — the snapshot pre-scan misses symlinked copy roots.**
The round-14 scan proved "no symlinks" for every node BENEATH `src`,
`tests` and `specs` — and not for those directories themselves. The
recursion-base miss (checklist item 1: recurse the property, *including
its base case*): `is_dir()` follows symlinks, `os.walk()` walks a
symlinked top even with `followlinks=False`, and `copytree` then
dereferences it wholesale. The reviewer's executed counterexample
replaced top-level `tests` with a symlink to an external directory:
not refused, external sentinel copied in. A second, quieter defect in
the same fix: a symlinked `conftest.py` was *silently omitted* by the
`is_file() and not is_symlink()` skip — omission that would quietly
change what the campaign's pytest runs under, and a broken-symlink
carrier vanished the same way.

The fix: each copy root is `is_symlink()`-checked BEFORE `is_dir()` or
any walk, and a symlinked or broken-symlink configuration carrier
REFUSES (error posture, consistent with round 14) rather than being
dropped. The standing regression drives all three top-level roots as
links to an external sentinel directory — refusal before snapshot
creation, sentinel never copied — plus linked and broken-linked
config carriers.

Research's pre-seal pass confirmed the node-class enumeration COMPLETE
for the entry-driven, git-carriable threat model, checking the two
surfaces outside the scan's node-set rather than only the ones inside:
pytest's own conftest/rootdir discovery for the campaign subprocess
(a planted parent-directory conftest did NOT execute — pytest's
default resolution bounds discovery at the snapshot; now pinned
by-construction with explicit `--rootdir`/`--confcutdir` per the
arc's own standard against agreement-by-coincidence, since a parent
conftest would be code execution), and hard links (git cannot carry
one — committing it commits the content). Scoped out as environmental
rather than entry-reachable: a symlinked ROOT itself (the caller names
root) and FIFOs/devices/sockets in the tree (git-uncarriable; a FIFO
would hang the copy — a denial, not a read or a false pass).

## 26. Changes in v20 — the round-16 fold (2026-08-29)

Round 16 returned exact v16 for one mechanical process amendment;
PROCESS-R15-1's production fix is confirmed correct, and no policy or
trust-model defect was found.

**PROCESS-R16-1 — "refuse before access" was not regression-bound.**
The round-15 regressions asserted the refusal OUTCOME: the reviewer
planted a mutant that copies every root wholesale into a leaked temp
dir and *then* runs the guards — normal refusal message, all
regressions green, three leaked snapshots holding the external
sentinel. The K2 lesson (reachability of the failure is not the right
mechanism of the failure) landing on the round-15 test itself. The
same ordering also had a real leak in production: the config-carrier
check ran after `mkdtemp`, so its refusal stranded a
`veracium-mutant-tree-*` directory — reproduced, one dir per refusal.

The fix, in the required two halves. Production: `_snapshot` is now
two phases — phase 1 is EVERY guard (config carriers and copy roots
and the walk scan), touching the filesystem read-only; phase 2
allocates and copies, with cleanup guaranteed on any exception. A
refusal therefore allocates nothing and copies nothing, by structure.
Regression: the mechanism is OBSERVED, not inferred — recording
wrappers over `copytree`, `copy2`, `mkdtemp` and `os.walk` require the
refusal to arrive with zero allocations, zero copies, and no walk
under the link, for both the symlinked-root and the symlinked-carrier
(leak) cases. And the reviewer's copy-before-refuse mutant rides as a
standing adversarial check: the planted leak is driven through the
instrumentation and the detector MUST fire — if the instrumentation
ever goes blind, that test fails, not just the campaign.

## 27. Changes in v21 — the round-17 fold (2026-08-29)

Round 17 returned exact v17 for one mechanical process amendment;
PROCESS-R16-1's pre-refusal behavior and production cleanup are
confirmed correct, and no policy or trust-model defect was found.

**PROCESS-R17-1 — the copy-exception cleanup was not regression-bound.**
Round 16 bound one half of its own fix (refusal before allocation,
instrumented) and left the other half a claim: deleting the except-
block's `rmtree` passed both new R16 tests and the entire registry
suite while a planted `copytree` failure leaked a real snapshot
directory. The reviewer's move is this arc's recurring one — the test
asserted the exception propagates (the OUTCOME) and never observed the
allocated directory's fate (the MECHANISM). Reproduced, then closed to
the reviewer's five requirements: failures injected independently into
`copy2` and `copytree` after allocation; the exact allocated directory
recorded via the mkdtemp wrapper's RETURN paths and required to not
exist after the exception; the original exception required to
propagate; the cleanup-deletion mutant standing, with the leak
required to be OBSERVED (if the detector goes blind, the mutant test
fails); and no broad temp-directory globs anywhere in cleanup.

**The concurrent-reader class, named as recurring** (research's flag,
owed from round 16): three times in this arc, code that was correct in
isolation destroyed or corrupted state a CONCURRENT reader depended on
— (1) two in-place campaigns interleaving apply/restore froze a
mutation into the live tree (round 11's fold; closed by the snapshot);
(2) the closure-evidence gate's concurrent ledger commands read
artifacts mid-mutation (same closure); (3) the round-16 mutant test's
cleanup globbed `veracium-mutant-tree-*` and deleted a LIVE concurrent
campaign's snapshot out from under its subprocess. The class invariant
now stated once: **shared mutable state is either never touched (work
in a private copy) or touched only through paths scoped to what THIS
actor created (recorded return paths, never pattern-matched sweeps)** —
and any future broom, lock, or restore step gets measured against it.

## 28. Changes in v22 — the round-18 fold (2026-08-29)

Round 18 returned exact v18 for one mechanical process amendment;
production cleanup is confirmed correct (no production change was
needed — the bare re-raise was already right), and no policy or
trust-model defect was found.

**PROCESS-R18-1 — original-exception propagation was not
regression-bound.** The round-17 tests asserted the exception's TYPE
and MESSAGE (`pytest.raises(OSError, match=...)`); the reviewer
planted an inner handler replacing each copy exception with a fresh
lookalike carrying the same type and message — both R17 regressions
passed, the full registry suite passed, and the caught exception was a
different object than the one raised, contradicting the package's
repeated "the original exception propagates" claim. Reproduced (the
replacement passes type-and-message, fails identity), then closed to
the reviewer's requirements: one sentinel exception OBJECT per
copy2/copytree case, raised as that exact object and asserted by
IDENTITY (`caught.value is sentinel`); the cleanup-path assertions and
the cleanup-deletion mutant retained; and the same-type/same-message
replacement mutant standing as a biting regression — it preserves
cleanup, type, and message (the old assertions bless it) and the
identity probe alone kills it.

## 29. Changes in v23 — ACCEPTANCE (2026-08-29)

External round 19 returned 🏁 **ACCEPTED** — the exact package
`0011-v19-20260829T1119Z.tar.gz` (sha `71fae9d6…`) and candidate draft
v22, with no blocking, major, minor, policy, or trust-model findings.
Finite design acceptance remains in force on the frozen S1–S7 invariant
surface. Round 18's closure was confirmed sound, with the reviewer
independently replanting the replacement handler and watching the
regression fail exactly at the identity probe.

This revision performs exactly what the verdict authorizes: records the
verdict, generates the review-closure carriers (the `## Review closure`
section below is the generated per-round ledger), and sets
`Spec-Status: accepted`. The reviewer's optional ask is recorded as an
open follow-up rather than carried silently: a digest-bound focused R18
transcript (pristine pass plus replacement-mutant identity failure)
would save future reviewers from replanting the mutant. Implementation
of the E2–E6 obligations is now authorized.

*Discharged 2026-08-30:* `specs/evidence/0011/check_r18_transcript.py`
re-executes both invocations in a private snapshot — the pristine R18
regression passing, then the replacement mutant applied and killed AT
the identity probe (the probe's own `E` line is required and recorded)
— and binds `specs/evidence/0011/r18_transcript.json` by digest to the
artifact's bytes and the probe function's source. Verify:
`$PY specs/evidence/0011/check_r18_transcript.py`; the suite reproduces
it at `test_r18_transcript_reproduces_runner_observed`, and the
checker's own adversarial matrix (P1) is
`test_r18_transcript_checker_matrix`.

## Review closure

*(PROCESS §4a — one row per review finding, with evidence that is
openable or executable. The round-by-round ledger below is GENERATED
from `specs/reviews.py`. Regenerate with `python3
specs/render_closure.py --write`; `--check` fails the build when it
drifts.)*

<!-- GENERATED:review-closure -->

**2 internal round(s) and 19 external round(s) with a returned VERDICT are recorded for `0011`; 19 package(s) were dispatched** — counted from `specs/reviews.py`, which is the source this block is generated from. A round appearing here and not there, or the reverse, is impossible by construction. **SENT rows are dispatch records, not outcomes**, and are labelled below so the two are never summed.

| round | date | findings raised (from `raised=`) | verdict (compressed) |
|---|---|---|---|
| internal 1 (verdict) | 2026-08-23 | 6 | PASS WITH AMENDMENTS (research) — the design is right; three moderates, three minors, both §9 questions answered and E-Q4 ruled. Method was a full read plus code verification on main @ 83d84c9: the M7-correct defect confirmed live, the ingest completeness check and the canonical-subject helper both … |
| internal 2 (verdict) | 2026-08-24 | 0 | PASS (research) — diff-verified fold of round 1, no new findings. External-ready |
| external 1 (SENT) | 2026-08-26 | — | SENT (package `0011-v1`, candidate draft v4 — the LINE'S FIRST SEALED PACKAGE; no predecessor, so the sealer's NO_PRIOR path applies and the what-changed diff is skipped and SAID to be skipped). Subject-scoped entitlement: a user's authority over their OWN subject does not extend to retiring sourced… |
| external 1 (verdict) | 2026-08-26 | 6 | RETURN DRAFT v4 FOR MAJOR AMENDMENT (package `0011-v1`, sha 05c23952 verified; archive safety, package identity, all declared prerequisites, header/collected/reconciliation/closure/operation/review-lessons/transcript all PASSED; harnesses 60/60 and 18/18; spec gate 95 passed; extracted-tree suite 18… |
| external 2 (SENT) | 2026-08-26 | — | SENT (package `0011-v2`, candidate draft v5 — the round-1 fold; §11 maps every finding). All five spec findings and the package finding closed. R1-1: `sourced` and `self_assertion` are closed predicates over state that EXISTS, the policy function is TOTAL and replaces v4's condition (which omitted t… |
| external 2 (verdict) | 2026-08-27 | 5 | RETURN v2 / DRAFT v5 FOR MAJOR AMENDMENT (package `0011-v2`, sha cb5cdb3f verified; archive structure and v1 lineage valid; extracted suite 1835 passed/22 skipped reconciling through 14 declared transitions; collected-header 21 passed; spec gate 88 passed. R1-3's same-value defect confirmed CLOSED).… |
| external 3 (SENT) | 2026-08-27 | — | SENT (package `0011-v3`, candidate draft v6 — the round-2 fold; §12 maps every finding). R2-1: the decision READS NO source_id — `sourced` is deleted, the rule refuses on subject class plus self-assertion alone, 0005/0006/0015 join Spec-Requires, and the cost is stated rather than absorbed: without … |
| external 3 (verdict) | 2026-08-27 | 4 | RETURN v3 / DRAFT v6 FOR MAJOR AMENDMENT (package `0011-v3`, sha 6261af6d verified; v2 lineage valid; extracted suite 1835 passed/22 skipped; collected-header 21; spec gate 88). CLOSED from round 2: source_id presence no longer changes the policy, 0005/0006/0015 declared, would_refuse_broad and the … |
| external 4 (SENT) | 2026-08-27 | — | SENT (package `0011-v4`, candidate draft v7 — the round-3 fold; §13 maps every finding). R3-1: the predicate is defined over the AUTHORITY CHAIN — `effective(author, derived_from) == effective(USER, None)`, computed by 0003's own function — so a marker carrying no authority cannot move a decision th… |
| external 4 (verdict) | 2026-08-27 | 3 | 🏁 FINITE DESIGN ACCEPTANCE FOR DRAFT v7'S CORE CONSTRUCTION — the authority-chain design need not be reopened — with THIS EXACT v4 PACKAGE RETURNED for mechanical amendments before the status flip (package `0011-v4`, sha 73e3a6d8 verified; extracted suite 1835/22; 1,857 collected reconcile with the … |
| external 5 (SENT) | 2026-08-27 | — | SENT (package `0011-v5`, candidate draft v8 — the round-4 fold; §14 maps every finding; the FINITE ACCEPTANCE stands and the core construction is untouched). EVIDENCE-R4-1: the oracle is FULL-EDGE — two real Edge objects with independent source and origin values on each side (1,440 cells), every che… |
| external 5 (verdict) | 2026-08-27 | 2 | RETURN EXACT v5 FOR TWO MECHANICAL AMENDMENTS before the status flip — FINITE DESIGN ACCEPTANCE REMAINS IN FORCE, no architectural defect found (package `0011-v5`, sha 48982518 verified; 499 members; policy mutation suite 5 passed; extracted suite 1841/22; 1,863 collected reconcile with the sealed 1… |
| external 6 (SENT) | 2026-08-27 | — | SENT (package `0011-v6`, candidate draft v9 — the round-5 fold; §15 maps both findings; the finite acceptance stands). EVIDENCE-R5-1: the oracle constructs the EXACT expected Cartesian key set independently of the emitter and requires emitted keys to EQUAL it — missing and alien keys are named by th… |
| external 6 (verdict) | 2026-08-28 | 2 | RETURN EXACT v6 FOR TWO MECHANICAL EVIDENCE AMENDMENTS — finite design acceptance remains in force; the status flip is blocked only by evidence machinery (package `0011-v6`, sha b5476dbe verified; 501 members; policy/campaign suite 10 passed; extracted suite 1846/22; 1,868 reconcile with the sealed … |
| external 7 (SENT) | 2026-08-28 | — | SENT (package `0011-v7`, candidate draft v10 — the round-6 fold; §16 maps both findings; the finite acceptance stands). EVIDENCE-R6-1: the enum axes are pinned TO THE ENUM (AUTHORS == tuple(EvidenceAuthor); DERIVED == (None, *EvidenceAuthor)) and the expected key set is built from the enum rather th… |
| external 7 (verdict) | 2026-08-28 | 1 | RETURN EXACT v7 FOR ONE MECHANICAL EVIDENCE AMENDMENT — finite design acceptance stands; the enum correction is sound; the remaining defect is confined to the new mutant registry (package `0011-v7`, sha 4c32346b verified; focused 21 passed; collected-header 22; spec gate 88; extracted suite 1857/22;… |
| external 8 (SENT) | 2026-08-28 | — | SENT (package `0011-v8`, candidate draft v11 — the round-7 fold; §17 maps the finding; the finite acceptance stands). PROCESS-R7-1 closed exactly as prescribed: the binding comes from the EXECUTED side — every standing test reports the id(s) it kills into a kill log the runner owns, and the runner r… |
| external 8 (verdict) | 2026-08-28 | 1 | RETURN EXACT v8 FOR ONE MECHANICAL REGISTRY AMENDMENT — finite design acceptance stands; no policy, authorization, contention or trust-model defect (package `0011-v8`, sha 4aaaf6fb verified; the exact v7 attacks confirmed closed; the default check confirmed non-mutating; focused 25 passed; extracted… |
| external 9 (SENT) | 2026-08-28 | — | SENT (package `0011-v9`, candidate draft v12 — the round-8 fold; §18 maps the finding; the finite acceptance stands). PROCESS-R8-1 closed as prescribed: kills are (node, id) PAIRS with the node taken from pytest's own PYTEST_CURRENT_TEST — the caller cannot misdeclare it — and the runner requires ex… |
| external 9 (verdict) | 2026-08-28 | 2 | RETURN EXACT v9 FOR TWO MECHANICAL EVIDENCE AMENDMENTS — finite design acceptance stands; the three v8 attacks closed in the pristine implementation; no design or trust-model defect (package `0011-v9`, sha 3063cd70 verified; focused 28 passed; extracted suite 1864/22; 1,886 reconcile with the sealed… |
| external 10 (SENT) | 2026-08-28 | — | SENT (package `0011-v10`, candidate draft v13 — the round-9 fold; §19 maps both findings; the finite acceptance stands). PROCESS-R9-1: the join is bound at the EXECUTION — an integration regression sends the node-swapped registry through the real pytest run and requires binding failure, which a self… |
| external 10 (verdict) | 2026-08-28 | 2 | RETURN EXACT v10 FOR ONE BLOCKING PROCESS AMENDMENT (plus one nonblocking maintenance item) — finite design acceptance stands; no policy, authorization, contention or trust-model defect (package `0011-v10`, sha 1ee6af69 verified; focused 31 passed; extracted suite 1867/22; 1,889 reconcile with the s… |
| external 11 (SENT) | 2026-08-28 | — | SENT (package `0011-v11`, candidate draft v14 — the round-10 fold; §20 maps both items; the finite acceptance stands). PROCESS-R10-1 closed by REMOVING what the attack needs: the artifact no longer performs attribution at all — the reporter is a 4-line id-only writer in the TEST files, the runner ex… |
| external 11 (verdict) | 2026-08-28 | 1 | RETURN EXACT v11 FOR ONE MECHANICAL PROCESS AMENDMENT — finite design acceptance stands; no policy or trust-model defect (package `0011-v11`, sha 76ea68a8 verified; focused 32 passed; collected-header 22; spec gate 88/5; selfcheck 8; extracted suite 1868/22, its 1,890 reconciling exactly with the se… |
| external 12 (SENT) | 2026-08-28 | — | SENT (package `0011-v12`, candidate draft v15 — the round-11 fold; §21 maps the finding; the finite acceptance stands). PROCESS-R11-1 closed by REMOVING the kill-claim protocol: schema-4 entries carry their mutations as text hunks, the runner applies them and OBSERVES kills (clean pass + mutated exi… |
| external 12 (verdict) | 2026-08-28 | 1 | RETURN EXACT v12 FOR ONE MECHANICAL PROCESS AMENDMENT — finite design acceptance stands; PROCESS-R11-1 confirmed substantively closed (reporter protocol gone, baselines require collection and passes, exit-4/empty runs refused, the R4A/F1 swap yields two SURVIVED and exit 1, snapshots isolate, the se… |
| external 13 (SENT) | 2026-08-28 | — | SENT (package `0011-v13`, candidate draft v16 — the round-12 fold; §22 maps the finding). PROCESS-R12-1 closed at the identity carrier, twice in one day: mutation_identity is the sorted bundle of MINIMAL-DIFF hunk identities — common prefix/suffix stripped between old and new, whitespace folded, pin… |
| external 13 (verdict) | 2026-08-28 | 1 | RETURN EXACT v13 FOR ONE MECHANICAL PROCESS AMENDMENT — finite design acceptance stands; R12-1's exact-duplicate and context-window attacks confirmed closed; no policy or trust-model defect (package `0011-v13`, sha 897edcb7 verified; focused 37; collected-header 22; spec gate 88/5; selfcheck 8; extr… |
| external 14 (SENT) | 2026-08-28 | — | SENT (package `0011-v14`, candidate draft v17 — the round-13 fold; §23 maps the finding). PROCESS-R13-1 closed at the terminal rung of the four-face identity ladder (id → full text → minimal diff+position → partitioning): the canonical identity is the RESULTING TRANSFORMATION — per artifact, the sha… |
| external 14 (verdict) | 2026-08-28 | 1 | RETURN EXACT v14 FOR ONE MECHANICAL PROCESS AMENDMENT — finite design acceptance stands; PROCESS-R13-1 confirmed substantively closed (merged-C2, the original constant-cardinality substitution, AND a stronger replacement preserving 21 entries / 25 hunks / 17 nodes / the 15-6 finder split all refuse … |
| external 15 (SENT) | 2026-08-28 | — | SENT (package `0011-v15`, candidate draft v18 — the round-14 fold; §24 maps the finding). PROCESS-R14-1 closed with ONE shared guard (artifact_problems: allowlist membership as a pure string check FIRST, so an out-of-set path refuses with no filesystem access; containment and regular-file as depth) … |
| external 15 (verdict) | 2026-08-29 | 1 | RETURN EXACT v15 FOR ONE MECHANICAL PROCESS AMENDMENT — finite design acceptance stands; PROCESS-R14-1 confirmed closed on its requested surface (named refusals, no traceback, no campaign, both carriers; _identity degrades without reading; both amendment tests pass); no policy or trust-model defect … |
| external 16 (SENT) | 2026-08-29 | — | SENT (package `0011-v16`, candidate draft v19 — the round-15 fold; §25 maps the finding). PROCESS-R15-1 closed as the recursion-base case of the round-14 property: each copy root is is_symlink-checked BEFORE is_dir or any walk, and a symlinked or broken-symlink configuration carrier REFUSES (error p… |
| external 16 (verdict) | 2026-08-29 | 1 | RETURN EXACT v16 FOR ONE MECHANICAL PROCESS AMENDMENT — finite design acceptance stands; PROCESS-R15-1's production fix confirmed correct; no policy or trust-model defect (package `0011-v16`, sha ddbb674d verified; archive safety 514 members; focused 42; collected-header 22; spec gate 88/5; selfchec… |
| external 17 (SENT) | 2026-08-29 | — | SENT (package `0011-v17`, candidate draft v20 — the round-16 fold; §26 maps the finding). PROCESS-R16-1 closed in both required halves: _snapshot is TWO-PHASE (phase 1 is every guard — carriers, roots, walk scan — filesystem read-only; phase 2 allocates and copies with cleanup guaranteed on any exce… |
| external 17 (verdict) | 2026-08-29 | 1 | RETURN EXACT v17 FOR ONE MECHANICAL PROCESS AMENDMENT — finite design acceptance stands; PROCESS-R16-1's pre-refusal behavior and production cleanup confirmed correct; no policy or trust-model defect (package `0011-v17`, sha f7e1b62c verified; archive safety 515 members; focused 44; collected-header… |
| external 18 (SENT) | 2026-08-29 | — | SENT (package `0011-v18`, candidate draft v21 — the round-17 fold; §27 maps the finding). PROCESS-R17-1 closed to the reviewer's five requirements: failures injected independently into copy2 and copytree after allocation; the exact allocated directory recorded via the mkdtemp wrapper's RETURN paths … |
| external 18 (verdict) | 2026-08-29 | 1 | RETURN EXACT v18 FOR ONE MECHANICAL PROCESS AMENDMENT — finite design acceptance stands; production cleanup confirmed correct; no policy or trust-model defect (package `0011-v18`, sha 1013e36a verified; archive safety 516 members; focused 46; collected-header 22; spec gate 88/5; selfcheck 8; extract… |
| external 19 (SENT) | 2026-08-29 | — | SENT (package `0011-v19`, candidate draft v22 — the round-18 fold; §28 maps the finding). PROCESS-R18-1 closed by IDENTITY: one sentinel exception OBJECT per copy2/copytree case, raised as that exact object and asserted with caught.value IS sentinel; the cleanup-path assertions and the cleanup-delet… |
| external 19 (verdict) | 2026-08-29 | 0 | 🏁 ACCEPTED — the exact package `0011-v19` (sha 71fae9d6 verified by the reviewer) and candidate draft v22; NO blocking, major, minor, policy or trust-model findings; finite design acceptance remains in force on the frozen S1-S7 invariant surface, and dev is authorized to advance the spec to accepted… |

**Per-finding closure ledger — PROCESS §4a.** **42 finding(s) for `0011`; 277 across the 7 tracked specs** — every number here is DERIVED from the rows below (external round 7, R7-1: the manifest claimed 26 while the ledgers held 31, and 0023 said 9/9 above a 10-row table). Generated from `specs/closure_findings.py` and validated against `specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — extras, duplicates, wrong rounds and empty evidence all fail the build.

| finding | round | what it was | closed in | evidence (runnable) |
|---|---|---|---|---|
| **0011-I1-M1** | internal 1 | §2c cited 0024 Q3 cells that are NOT on main post-revert, and pointed at a §3b the spec did not have (its sections ran §1, §2, §3, §2c, §3c) | the citation names the ACCEPTED surface as amended by A1 rather than shipped tests, and the section ordering is repaired so §3b exists and the reference resolves | `grep -n 'as amended by A1, landed' specs/0011-subject-scoped-entitlement.md && grep -nE '^## 3b\.' specs/0011-subject-scoped-entitlement.md` |
| **0011-I1-M2** | internal 1 | E5 bound the correction's ARGUMENTS but not the ACTOR, so any caller reaching correct() obtained a valid capability and §2c's adversarial cell was closed only against forge/replay of a DIFFERENT correction | E-Q4 ruled YES: the acting principal is the fifth tuple element, verified inside the transaction like the rest | `grep -n "E5's fifth element" specs/0011-subject-scoped-entitlement.md` |
| **0011-I1-M3** | internal 1 | §9.3's broad form (any user-authored retirement of other-subject sourced fact refuses pending confirmation) had no measured constituency | keep the NARROW cell for v1 and add a measurement rider to §4b, so counting the refusal rows post-release is a design obligation rather than a hope | `grep -n 'MEASUREMENT RIDER' specs/0011-subject-scoped-entitlement.md` |
| **0011-I1-m4** | internal 1 | §1 quoted the 2026-08-02 split-date defect state in the present tense, though 0003 shipped in v0.6.0 — a cold reader would file a live defect | marked as the historical motivation, at the time of the split | `grep -n 'At the time of the split' specs/0011-subject-scoped-entitlement.md` |
| **0011-I1-m5** | internal 1 | the M7 site was cited by line number, which had already moved | cited by SYMBOL instead, which does not drift | `grep -n 'at the symbol .Memory.correct' specs/0011-subject-scoped-entitlement.md && ! sed '/<!-- GENERATED:review-closure -->/,$d' specs/0011-subject-scoped-entitlement.md \| grep -n '__init__.py:1362'` |
| **0011-I1-m6** | internal 1 | §4d's derived(from_class) had an OPEN domain — an unknown or malformed value had no defined behaviour (the week's validator lesson: refuse the unknown, do not merely cover the known) | the domain is CLOSED and validated at construction, failing closed to the derived(THIRD_PARTY) floor, with S5 carrying the unknown-value cell | `$PY specs/evidence/0011/check_round1_fold.py  # m-6 asked for a CLOSED domain validated at construction; external R1-4 then found that §4d named TWO outcomes for a malformed value and rewrote the passage, which broke this row's original grep. The property is unchanged and is now checked structurally — one outcome, absence kept distinct, every invalid cell enumerated — rather than by a sentence a later fold can reword` |
| **0011-R1-1** | external 1 | the central entitlement cell was not representable — `sourced`, `self-assertion` and 'confirmation, a higher rung' had no runtime predicate; §4b's condition omitted the sourced term, contradicting §3c; and the measurement rider could not measure the broad rule's constituency, which produces no refusal row at all | closed predicates over state that exists today, a TOTAL policy function, every absence case stated, the over-inclusion pointed in the refusing direction, the 0008 phrase withdrawn, the basis-aware form deferred rather than unfreezing 0016, and the rider made measurable with a counts-only counter for the allowed-but-broad-refusing cell | `$PY specs/evidence/0011/check_round1_fold.py  # checks the policy block is TOTAL and carries the sourced term v4 omitted, both predicates are DEFINED not merely used, and the rider has the allowed-cell counter that makes it measurable` |
| **0011-R1-2** | external 1 | E5 was claimed to be unforgeable and to authenticate CORRECTORS; 0020 states the principal is host-supplied, forgeable and unauthenticated, and correct() mints the authorisation from caller-controlled values, so a fresh impersonation passes the in-transaction check | the claim is WITHDRAWN in every carrier that made it; the binding is integrity and attribution; correct() is a protected host API with the host's authentication and intent obligations stated | `$PY specs/evidence/0011/check_round1_fold.py  # checks the unforgeable/authentication claim is gone from EVERY carrier that made it and the host-obligation table exists — the finding was a claim in three places, not one sentence` |
| **0011-R1-3** | external 1 | E3 defined contention as two active same-class edges, which is FALSE against accepted 0012 — it persists same-value restatements as separate active edges and calls them uncontested; the reviewer executed the test that proves it | contention requires >=2 DISTINCT normalised _value_key values, using 0012's own normalisation; composition with 0003/0012 stated; the maintain claim narrowed so per-edge expiry is not suspended; 0012 added to Spec-Requires and lifecycle.py to the consumer list | `$PY specs/evidence/0011/check_contention_rule.py  # the fold checked against 0012's OWN _value_key, runnable under the reviewer's bare offline interpreter; the shipped behaviour it must not contradict is tests/test_0012_currency_renewal.py::test_a_same_value_restatement_produces_no_contention_artifacts` |
| **0011-R1-4** | external 1 | §4d named TWO different observable outcomes for one input — a malformed from_class both refused by the constructor and floored to derived(THIRD_PARTY) | one outcome: it RAISES and nothing is written; ABSENCE is a distinct input that keeps the floor; the complete direct/derived grammar enumerated with every cell reachable | `$PY specs/evidence/0011/check_round1_fold.py  # checks ONE outcome for malformed input, the contradictory flooring sentence absent, absence kept distinct, and all four RAISES cells enumerated` |
| **0011-R1-5** | external 1 | S6's three labels were neither total (a quarantined, grounded, uncontested edge matched ZERO) nor exclusive (a mentionable, grounded, contested edge matched TWO), and the premise was false: no shipped reader interleaves history with present fact | a five-row FIRST-MATCH precedence table — total by catch-all, exclusive by ordering — with QUARANTINED_CLAIM and CONTESTED_CURRENT added; the invariant asserted over the cross-product; E6 re-motivated and the false premise retracted in place | `$PY specs/evidence/0011/check_round1_fold.py  # checks a 5-row first-match table ending in a catch-all and carrying QUARANTINED_CLAIM and CONTESTED_CURRENT — the two labels whose absence made an edge match zero` |
| **0011-PACKAGE-R1-1** | external 1 | the deciding SELF-floor measurement had NO evidence artifact — the archive could not re-derive 72,253 passes, 305 candidates, ~30 self-denoting rows or the 0.016% conclusion; 0025's aggregate supports corpus size, not subject classification | subject_census.py plus a counts-only aggregate digest-bound to the same cache sha as 0025's census, and the masked distinct-string candidate table the classification was made over; the load-bearing figure reproduces exactly and the two that did not are RETIRED | `$PY specs/evidence/0011/subject_census.py --aggregate specs/evidence/0011/subject_aggregate.json` |
| **0011-R2-1** | external 2 | the round-1 predicates made `source_id` an ENTITLEMENT CAPABILITY in both directions — omitting the prior's source_id ALLOWED the retirement, adding any source_id to the incoming assertion ALLOWED it too — against accepted 0006, which says it may GROUP never GRANT and was not even declared as a prerequisite | `sourced` is DELETED and the decision reads no source_id at all; the rule refuses on subject class plus self-assertion; 0005/0006/0015 join Spec-Requires; the lost narrowness is stated as a cost and deferred to 0016's frozen carrier; an invariance matrix is specified | `$PY specs/evidence/0011/check_round1_fold.py  # asserts the policy block CONTAINS NO source_id (comments stripped, so the sentence denying the read cannot satisfy it), that 0006's constraint is quoted as the reason, and that the invariance matrix exists` |
| **0011-R2-2** | external 2 | `would_refuse_broad` is CONSTANT TRUE — broad is a strict superset of narrow, so a narrow refusal is always a broad one; and the rider proposed store columns while §7a named no schema/migration/erasure/telemetry surface and §7 claimed no stored state | the flag is DELETED; the rider adds no stored state at all — counters on 0015's existing carrier, no column, no migration, nothing to erase — so §7 is true again and 0013 is not a prerequisite | `$PY specs/evidence/0011/check_round1_fold.py  # asserts the rider names the allowed-but-broad-refusing counter rather than the vacuous flag; the checker previously REQUIRED that flag, pinning the defect in place` |
| **0011-R2-3** | external 2 | the checker validated a standalone value-list function, and the shipped surface disagreed with it: two active same-class distinct-value edges in a real store are contested under the draft and NOT contested under Recall.contested (0 groups, 0 exposed) | contention IS 0003's refusal-scoped notion, adopted rather than redefined; E3 governs its rendering across the named surfaces; the checker drives a REAL store | `$PY specs/evidence/0011/check_contention_rule.py  # the reviewer's own cell (direct distinct-value pair -> NOT contested) beside a positive control (a live refusal -> contested), both on a real store, so the check cannot pass by never firing` |
| **0011-CARRIER-R2-1** | external 2 | SEVEN contradictory authoritative statements passed the pristine fold checker, which searched narrow phrases across the whole file — so a withdrawal written in §4e satisfied it while §3a still asserted the opposite | all seven swept; each assertion BOUND TO ITS NAMED ROW so a withdrawal elsewhere cannot satisfy it; S6 compared COUNT-TO-COUNT against §4f's table via a `labels=5` token | `$PY specs/evidence/0011/check_round1_fold.py  # row-scoped contradiction checks plus the count comparison; the count check exists because the first fix searched for 'three labels' while the row said 'one of the three', so the contradiction survived twice` |
| **0011-EVIDENCE-R2-1** | external 2 | the census aggregate mode TRUSTED its input — a fabricated one-entry aggregate with an all-zero digest printed the claimed measurement and exited 0 | a CLOSED typed schema (missing and unknown keys both refused) plus cross-checks against 0025's independently-derived aggregate, including a triple total summed from its relation counts, so a fabricated manifest must agree with an artifact its author does not control | `$PY specs/evidence/0011/subject_census.py --aggregate specs/evidence/0011/subject_aggregate.json` |
| **0011-R3-1** | external 3 | an EQUIVALENT authority bypass through `derived_from`: EvidenceContext.derived(USER) is valid and reachable, and USER/derived_from=USER carries the SAME effective authority (3) as USER/None, yet v6 refused one and allowed the other — a marker supplying no independent authority bought permission | the predicate is defined over the AUTHORITY CHAIN via production effective(), so exactly two chains qualify and the bypass cell is in the refusal set by construction; the 240-cell executable matrix asserts the CLASS (equal authority decides equally), not the instances | `$PY specs/evidence/0011/policy_matrix.py  # both defects that shipped were planted against it and both are caught; the absence-based one trips the GENERALISED equal-authority check as well as its named cell` |
| **0011-R3-2** | external 3 | the telemetry rider contradicted accepted 0015, which DEFERS refusal counters to a new consent discussion, requires consent-version gating for new payload fields, and counts only from a fresh commit — decision-time increments would overcount aborted and PLAN_STALE attempts | the rider is WITHDRAWN: v1 ships with the broad rule's constituency unmeasured and says so, leaving the consent question and the telemetry construction to 0015's own round | `$PY specs/evidence/0011/check_round1_fold.py  # asserts the deferral and that the spec states the constituency is unmeasured; this check previously REQUIRED the counter, pinning in place what the next round removed` |
| **0011-CARRIER-R3-1** | external 3 | five more contradictions survived the claimed sweep, and the no-source_id check was SYNTACTIC — the reviewer moved the read behind a helper defined in a separate fence and every fold check passed | all five swept, and the check follows the predicate's TRANSITIVE DEPENDENCIES across fences, so a read one or two indirections away is still a read | `$PY specs/evidence/0011/check_round1_fold.py  # the reviewer's exact bypass and a deeper two-hop version were both replayed against it and both are refused` |
| **0011-EVIDENCE-R3-1** | external 3 | the census's deciding figures remained forgeable: `schema` was typed but never valued, so schema=999 with predicate_passes=0 and a one-row candidate table returned no findings | schema == 1 required; the PREDICATE ITSELF cross-checked against 0025's independently-derived subject_user on the shared subset; and every figure labelled by what backs it, with the whole-corpus count and the table's completeness marked RECORDED ONLY rather than implied to be verifiable | `$PY specs/evidence/0011/subject_census.py --aggregate specs/evidence/0011/subject_aggregate.json` |
| **0011-EVIDENCE-R4-1** | external 4 | the 240-cell oracle had DECORATIVE dimensions: source and origin were enumerated but never passed to policy(), the invariance check re-called the function instead of comparing the EMITTED cells (a planted source-conditional ALLOW exited 0), the import-flattened cell never invoked portability, and the fold checker's definition map was last-definition-wins so a shadowed dangerous helper passed | the oracle is FULL-EDGE (1,440 cells over two real Edge provenances with independent source/origin), every check consumes the one emitted stream, the import cell runs production portability.import_memory in both modes, and the dependency closure carries EVERY definition of a name; both reviewer attacks are standing mutation tests | `$PY -m pytest tests/test_0011_policy_matrix.py::test_a_variance_planted_in_the_emission_is_caught tests/test_0011_policy_matrix.py::test_the_fold_checker_refuses_a_shadowed_helper tests/test_0011_policy_matrix.py::test_the_import_cell_runs_the_production_adapter -q -p no:randomly` |
| **0011-CARRIER-R4-1** | external 4 | five current carriers still stated the NARROW rule or the LIVE rider: §4's claim, S2, §4b's pointer at the rider, §9's ask to attack the rider's taxonomy, and S5's unclosed editing fragment | all five swept to the broadened rule and the withdrawn-rider disposition; §9 redirects the reviewer at the deferral itself; obsolete wording survives only as marked history | `$PY specs/evidence/0011/check_round1_fold.py  # the row-scoped and closure-based checks over the swept carriers, with the shadowing attack now refused` |
| **0011-PACKAGE-R4-1** | external 4 | the generated header asserted 'sealed rounds 1-4' and 'THE FIRST SEALED PACKAGE ON THIS LINE' in the same file, beside a CHANGED_FROM_PREVIOUS inventorying the v3 delta, and every header check passed — a hand-written template paragraph reintroduced the exact defect the header's own C5-1 note records, seven lines below it | the static paragraph and the static round-count sentence are DELETED from every template on both lines; seal_package.WITHDRAWN_CLAIMS refuses both shapes at seal time in wording the derived NO_PRIOR text deliberately does not use; lineage facts have exactly one source, the governed record | `$PY -m pytest tests/test_collected_header.py::test_no_template_hand_asserts_lineage -q -p no:randomly` |
| **0011-EVIDENCE-R5-1** | external 5 | cell COUNT did not prove domain COVERAGE: replacing one emitted cell with a duplicate of another kept 1,440 rows while a source/origin combination silently vanished — cardinality-preserving omission, invisible to the count check and to the truncated-stream test | the oracle constructs the EXACT expected Cartesian key set independently of the emitter and requires emitted keys to equal it; duplicates are rejected separately so the replacement is named rather than hiding behind the missing-key report it causes | `$PY -m pytest tests/test_0011_policy_matrix.py::test_a_duplicate_hiding_a_missing_cell_is_caught tests/test_0011_policy_matrix.py::test_an_alien_cell_key_is_caught -q -p no:randomly` |
| **0011-CARRIER-R5-1** | external 5 | §3c's LIVE contract row still described the OTHER-subject refusal as 'with the measurement rider' after R3-2 withdrew it; the fold checker exited 0 by finding the deferral text elsewhere in the file | the row is swept and the withdrawal is BOUND TO THE ROW: the checker anchors on §3c's row and refuses the promise there specifically — a deferral stated in §4b does not un-promise a different row | `$PY specs/evidence/0011/check_round1_fold.py  # the row-bound rider check, planted-back promise verified biting` |
| **0011-EVIDENCE-R6-1** | external 6 | an enum-derived dimension still self-narrowed: removing THIRD_PARTY from DERIVED changed the oracle's claimed domain from 1,440 to 1,152 cells with exit 0 — the emitter and the expected key set read the same constants, and the round-5 pins covered only the hand-picked dimensions | the enum axes are pinned TO THE ENUM and the expected key set is built from the enum rather than the mutable constants; the narrowed-DERIVED mutant and a narrowed-AUTHORS sibling are standing | `$PY -m pytest tests/test_0011_mutant_registry.py::test_narrowed_enum_dimension_is_refused -q -p no:randomly` |
| **0011-PROCESS-R6-1** | external 6 | the campaign record was PROSE and false twice over: nine mutants had no planted tests (their verification died with the session), neutering the whole census-figure binding left 10/10 green, subject_census.py sat outside P1's filename convention, and the hand-typed totals did not add up | the campaign is EXECUTABLE: mutant_registry.py binds every id to its artifact, mutation and node, runs them in one pytest invocation, and derives the totals into a generated record; the nine untested mutants are standing in-memory tests; every fold check is sentinel-proven reached; subject_census.py enters P1 via an explicit artifact registry | `$PY specs/evidence/0011/mutant_registry.py` |
| **0011-PROCESS-R7-1** | external 7 | registry entries were not bound to executed mutants: success derived from the distinct pytest nodes, so a fictitious entry riding an already-listed passing node inflated the total with exit 0; artifact paths were unvalidated; and the result record was WRITE-ONLY — overwritten by every run, read by nothing | the binding comes from the executed side: each standing test reports the id(s) it kills, and the runner requires reported kills to equal the declared ids exactly; artifacts validated, duplicates refused; the default invocation is a non-mutating check requiring whole-record equality with the shipped record; --write is seal-time only | `$PY specs/evidence/0011/mutant_registry.py  # CHECK mode: re-runs the campaign, verifies the one-to-one kill binding, and requires the shipped record to equal the recomputation; the attack regressions are tests/test_0011_mutant_registry.py::test_missing_observations_fail_coverage and ::test_the_shipped_record_recomputes_and_diverges_on_tamper` |
| **0011-PROCESS-R8-1** | external 8 | three adjacent registry gaps: kill ids bound globally (a node swap between two entries changed nothing), record checking by dict equality which coerces (False == 0 claimed an exact match), and artifact validation accepting /etc/passwd via pathlib's absolute-join discard | kills are (node, id) pairs with the node taken from pytest's own PYTEST_CURRENT_TEST and exact pair-set equality enforced; the record check pins exact int types and compares canonical serialized bytes; artifact paths must be relative, contained and regular files — all three attacks standing at the real checker boundary | `$PY -m pytest tests/test_0011_mutant_registry.py::test_a_swapped_on_disk_registry_survives_and_is_refused tests/test_0011_mutant_registry.py::test_type_coerced_kill_exit_is_refused tests/test_0011_mutant_registry.py::test_artifact_outside_the_package_is_refused -q -p no:randomly` |
| **0011-PROCESS-R9-1** | external 9 | per-node provenance was not behaviorally bound: a reporter looking up each id's node from the registry itself, plus a node swap, passed --write, --check and the whole focused suite — the regressions fed binding_problems() hand-built kills, never the production join | an integration regression sends the node-swapped registry through the REAL execution and requires binding failure (a self-asserting reporter makes the swapped registry pass, failing the test); the runner refuses any reported node it did not invoke | `$PY -m pytest tests/test_0011_mutant_registry.py::test_a_swapped_on_disk_registry_survives_and_is_refused -q -p no:randomly` |
| **0011-EVIDENCE-R9-1** | external 9 | the record lacked a closed canonical grammar: duplicate JSON keys vanished at parse, found_by was an open vocabulary whose alien value regenerated cleanly, deleting the refusal branches left every test green, and the schema stayed 2 across the killed-shape change | duplicates refuse AT PARSE; a recursive exactly-typed closed schema governs every level; shipped RAW BYTES must equal the canonical writer's output; schema 3; and each corrupt record is refused BY MAIN ITSELF in standing subprocess regressions | `$PY -m pytest tests/test_0011_mutant_registry.py::test_corrupt_records_are_refused_by_main_itself tests/test_0011_mutant_registry.py::test_non_canonical_bytes_are_refused_by_main -q -p no:randomly` |
| **0011-PROCESS-R10-1** | external 10 | per-node provenance remained self-assertable: the round-9 regression swapped a LOCAL entries copy while the child imported the ON-DISK registry, so the coordinated attack — on-disk node swap plus an in-artifact reporter reading ENTRIES — passed --write, --check and all 31 focused tests | the artifact performs no attribution: the reporter is an id-only writer in the TEST files, and the runner executes each node in an isolated invocation, joining every reported id to the node IT invoked; the coordinated on-disk mutation is the standing regression, driven through the real execution | `$PY -m pytest tests/test_0011_mutant_registry.py::test_a_swapped_on_disk_registry_survives_and_is_refused -q -p no:randomly` |
| **0011-EVIDENCE-M10-1** | external 10 | the shipped-record operand was environment-selectable via a testing-only variable, and the check ran the full campaign before parsing despite claiming grammar first | the entry point is pinned to the shipped record with no selector (a standing test asserts the variable's absence from the source); corrupt operands exercise an internal helper on copies; the order is parse -> closed schema -> canonical-form-of-the-bytes -> campaign | `$PY -m pytest tests/test_0011_mutant_registry.py::test_non_canonical_bytes_are_refused_by_main tests/test_0011_mutant_registry.py::test_corrupt_records_are_refused_by_main_itself -q -p no:randomly` |
| **0011-PROCESS-R11-1** | external 11 | the round-10 regression was fail-open (its copied module derived ROOT from /tmp, pytest exited 4, and the empty kill list produced the expected mismatch — it passed while executing nothing), and the id half of every kill was still a test-side claim: a reporter deriving ids from the registry, coordinated with a swapped on-disk registry, passed --write, --check and the focused suite | schema 4 removes the claim protocol: entries carry their mutations as text hunks, the runner applies them and OBSERVES the kill (clean pass + mutated exit-1 failure, counts parsed, artifacts restored byte-identically verified), leave-one-out proves each hunk of a multi-hunk entry load-bearing, a dead subprocess is a named ERROR at the real root, judge-targeting hunks refuse at validation, concurrent campaigns refuse on an exclusive lock, and no reporter, kill log or pytest-side attribution exists (standing absence test) | `$PY -m pytest tests/test_0011_mutant_registry.py::test_a_dead_subprocess_is_an_error_not_a_defense tests/test_0011_mutant_registry.py::test_a_swapped_on_disk_registry_survives_and_is_refused tests/test_0011_mutant_registry.py::test_no_kill_claim_protocol_remains -q -p no:randomly` |
| **0011-PROCESS-R12-1** | external 12 | duplicate mutations inflate the observed ledger: R5A duplicated under a fresh id passed validation, --write, --check and the focused suite — schema 4 moved the mutant's identity to the hunk bundle and uniqueness stayed on the id string, so every observation was genuine and only the totals lied | mutation_identity — the sorted bundle of minimal-diff hunk identities (common prefix/suffix stripped, whitespace folded, pinned to the edit's absolute position; the full-text form was context-window slidable, research pre-seal) — is canonical; duplicates refuse on both carriers regardless of id, finder, node, hunk order or window; run_check fails fast on entry problems so the refusal precedes any campaign run; --write refuses without writing; the DUPR5A case is driven through both real boundaries on disk | `$PY -m pytest tests/test_0011_mutant_registry.py::test_a_duplicate_mutation_is_refused_at_the_real_boundary tests/test_0011_mutant_registry.py::test_mutation_identity_is_the_resulting_transformation -q -p no:randomly` |
| **0011-PROCESS-R13-1** | external 13 | hunk partitioning defeated mutation uniqueness: C2's two edits merged into one wider hunk produced byte-identical mutated artifacts under a distinct identity, and a constant-cardinality replacement hid a vanished mutant behind a double-counted one — face four of the identity ladder (id, full text, minimal diff, partitioning), each fix normalizing a richer description while identity stayed a function of the description | the canonical identity is the resulting artifact transformation (per-artifact sha256 of the bytes the complete bundle produces from pristine), so no representation remains to vary; duplicates refuse on both carriers pre-campaign; both reviewer attacks are standing regressions at the real on-disk boundaries with the copied module pinned to the real root | `$PY -m pytest tests/test_0011_mutant_registry.py::test_partitioned_duplicates_are_refused_at_the_real_boundary tests/test_0011_mutant_registry.py::test_mutation_identity_is_the_resulting_transformation -q -p no:randomly` |
| **0011-PROCESS-R14-1** | external 14 | both carriers computed mutation identity before validating hunk paths: a record hunk naming /etc/passwd validated CLEAN (the record carrier had no path validation at all), and /bin/sh was READ and crashed the checker with an uncaught decode error — the R8-1(3) absolute-join footgun reachable through the round-12 identity restructure | one shared guard (artifact_problems) runs in BOTH carriers before identity touches the filesystem — membership is a pure string check, so an out-of-set path refuses with no read; _identity is additionally defensive (no absolute/escaping/missing reads, degrades on binary bytes); /bin/sh is the built-in no-read witness in the standing regression at the real entry point | `$PY -m pytest tests/test_0011_mutant_registry.py::test_out_of_tree_paths_refuse_before_any_read -q -p no:randomly` |
| **0011-PROCESS-R15-1** | external 15 | the snapshot pre-scan proved no-symlinks for every node BENEATH the copied roots and not for src/tests/specs themselves — is_dir() follows links, os.walk walks a symlinked top, copytree dereferences it wholesale (executed: top-level tests as a link to an external dir, sentinel copied in); a symlinked conftest.py was silently omitted rather than refused | each copy root is is_symlink-checked BEFORE is_dir or any walk; symlinked and broken-symlink configuration carriers refuse with the error posture; the standing regression drives all three top-level roots plus both carrier shapes with an external sentinel proving nothing is copied | `$PY -m pytest tests/test_0011_mutant_registry.py::test_a_symlinked_copy_root_or_config_carrier_refuses -q -p no:randomly` |
| **0011-PROCESS-R16-1** | external 16 | 'refuse before access' was asserted nowhere: the round-15 regressions checked the refusal message only, so a mutant that copied every root into a leaked temp dir BEFORE running the guards passed the whole registry suite; and config-carrier validation ran after mkdtemp, stranding a temp dir per refusal | _snapshot is two-phase (all guards read-only first, allocate+copy second with guaranteed cleanup) and the regression OBSERVES the mechanism: instrumented copytree/copy2/mkdtemp/walk must record zero pre-refusal activity, and the reviewer's copy-before-refuse mutant stands as an adversarial check that must trip the detector | `$PY -m pytest tests/test_0011_mutant_registry.py::test_refusal_precedes_every_access_and_allocation tests/test_0011_mutant_registry.py::test_the_copy_before_refuse_mutant_is_caught -q -p no:randomly` |
| **0011-PROCESS-R17-1** | external 17 | the copy-exception cleanup was a claim: deleting the except-block rmtree passed both R16 tests and the whole registry suite while a planted copytree failure leaked a real snapshot directory — the test asserted the exception propagates and never observed the allocated directory's fate | failures injected independently into copy2 and copytree after allocation; the exact allocated directory (the mkdtemp wrapper's recorded return path, never a glob) required to not exist after the exception; the original exception propagated; the cleanup-deletion mutant stands with the leak required OBSERVED | `$PY -m pytest tests/test_0011_mutant_registry.py::test_copy_exception_cleanup_is_regression_bound tests/test_0011_mutant_registry.py::test_the_cleanup_deletion_mutant_is_caught -q -p no:randomly` |
| **0011-PROCESS-R18-1** | external 18 | original-exception propagation was asserted by type and message only — an inner handler swapping each copy exception for a fresh lookalike passed both R17 regressions and the whole registry suite while the caught exception was a different object than the one raised | one sentinel exception object per copy2/copytree case, raised as that exact object and asserted by identity (caught.value is sentinel); the replacement mutant stands as a biting regression that only the identity probe kills; cleanup assertions and the cleanup-deletion mutant retained | `$PY -m pytest tests/test_0011_mutant_registry.py::test_copy_exception_cleanup_is_regression_bound tests/test_0011_mutant_registry.py::test_the_exception_replacement_mutant_is_caught -q -p no:randomly` |

<!-- /GENERATED:review-closure -->
