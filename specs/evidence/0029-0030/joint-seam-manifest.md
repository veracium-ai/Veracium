<!-- TERMINAL RECORD — the ACCEPTED revision of the joint seam manifest, byte-copied
from the round-18 package (sha256 9930334127f782a24a4b35b1f19c01db8006c3d4bbec0d82d494f1c47e8e4669
@ dc244f001cce8c937228a06c6b1e8f43780d624f, CI 33804235511) on 2026-09-03, the day
the reviewer accepted 0029 v9, 0030 v29 and the joint seam and FROZE the invariant
surface. Its home was the review packages until acceptance froze it; a terminal
record living only in outbox archives is one rm from archaeology. Below this comment
the bytes equal the packaged manifest — verifiable forever against the archived package. -->

# 0029 ↔ 0030 — the joint seam manifest (round 18)

*Every seam where the two specifications meet (or deliberately do not),
each with its owner, its contract, and where the round-2 AND round-3
findings landed on it. The boundary sentence the pair is built on:*
**0030 classifies, 0029 carries transaction time, a future 0028 v2
resolves.** *New at round 4: the seams are no longer prose-only — the
RUNNABLE SEAM MODEL (`specs/evidence/0029-0030/seam_model/`, in the
bundled tree, 41 tests in the ordinary suite) executes S2, S3, S4 and S6,
and the PROPAGATION CHECK binds each model rule to its normative section
in BOTH directions, so a model that outruns its spec (the round-3 v14
episode) or a spec that outruns its model fails a test rather than
waiting for a reviewer.*

## S1 — EdgeStateAt(K): 0029 produces, 0030 consumes — MOVED (F5, C-1)

- **Contract (round-3 form):** `Store.edge_state_at(user_id, edge_id,
  until_txn) -> RawEdgeState | None` (0029 §4b-ii). The carrier is
  `RawEdgeState(edge_id, user_id, state: str, txn, seq, kind,
  recorded_at)`: `state` is the journal payload as VERBATIM TEXT —
  0029 promises byte fidelity (V-VERBATIM) and nothing about parseability
  or validity; **the consumer owns the parse** (0030 V-PARSE) and ALL
  validation. Why the round-2 verdict forced this: the shipped Pydantic
  deserializer REJECTS malformed reasons/timestamps at load, so a typed
  `Edge` return made "journal malformed state, then classify it"
  unimplementable — and an append-only journal can outlive the model that
  wrote it, which applies to the text as much as the values.
- **Naming, deliberately split:** 0029 mints V-VERBATIM (read-surface
  half), 0030 mints V-RAW (consumption half). Two specs defining one
  symbol differently would be its own finding; this manifest is what ties
  the pair, not a shared name.
- **Second consumer:** 0031 Phase B's reversal (§4c-iii) reads the same
  journal — V-RECON now has TWO consumers, so this contract freezes here,
  not per-consumer (0031 v3's own text says so; recorded at this fold).
- **Round-1 landing:** F1 (the pair could not reconstruct) — closed by
  the owner's ruling: full-serialization payloads. **Round-2 landing:**
  F1's second half (migrated stores) — closed by the epoch BASELINE batch
  (0029 §4e): every pre-existing edge journaled AS FOUND, so a migrated
  edge reconstructs from the epoch txn onward and `None` honestly means
  "held no such edge at any txn ≤ K".
- **Reconstruction oracle (unchanged in spirit, sharper in type):** the
  scripted harness snapshots the live row (`SELECT json`) after every
  committed transaction keyed by allocated `txn`; the oracle asserts
  `edge_state_at(user, edge, txn_i).state` BYTE-EQUALS the snapshot at
  `txn_i` — now literally a text comparison, no deserialization in the
  oracle either.

## S2 — held-at-K vs assertable-now: the two-state split — MOVED (F2)

- **Contract:** unchanged in structure — 0029 reconstructs *belief held
  at K* and asserts nothing; 0030's `Result{status, held_at_K}` carries
  both truths; current caps SUBTRACT ONLY.
- **Round-2 landing — the current-trust input (F2):** the current
  source-restriction cap reads a DEDICATED store-derived input, NEVER
  `current.invalidation_reason` — the shipped sweep retires only ACTIVE
  rows (`revocation_sweep.py:734`), so an already-inactive `superseded`
  edge carries no trace of a standing restriction in its row, and as-of
  queries are BY DEFINITION about inactive edges. **Derivation (0030
  §4b-iii — corrected once at the round-2 cross-check and once by the
  round-3 verdict, both misses EXECUTED away):** a THIRD caller of the
  sweep's ONE COMPUTATION, membership **`("edge", edge_id) in
  statement["retire"]`** — the retire population is the transitively
  closed DESIRED STATE under the whole standing set AND it is
  HETEROGENEOUS ACROSS RECORD TYPES (executed: an episode key sits beside
  the edge keys), so a bare id fails open always and a cast could match
  an episode. NOT `affected` (target-scoped; executed empty on the
  simplest direct case) and NOT the effect list (active-filtered). ONE
  sweep call; the no-standing case is a defined outcome with zero calls;
  a LIFT flips the answer with no row rewritten (V-TRUST-INPUT).
- **Round-15 landing (one finding — the claims ladder's LAST rung):**
  the runtime registry keyed on WRITABLE metadata, and a metadata-copied
  impostor satisfied the real control's entry while it never ran (the
  round-15 attack point #1, taken exactly). The registry now holds
  FUNCTION OBJECTS — the one in-process thing nothing can counterfeit,
  only replace — and the gate re-resolves discovered callables fresh at
  gate time, closing the replacement half. ROUND 16 SHARPENED THE RUNG:
  holding the right objects is not enough if MEMBERSHIP compares by
  equality — a set consults __hash__/__eq__, which arbitrary callables
  define, and the reviewer's two distinct equal-comparing instances
  satisfied each other's entry. The registry is now an id-keyed IDENTITY
  registry (references retained, so an id can never be reused), a
  control is BY DEFINITION an ordinary function (types.FunctionType,
  enforced at the door and at discovery — the type is not subclassable,
  so the check is exact), and membership everywhere is an id() lookup
  with no path through user-definable equality. The ladder: mention →
  invocation → identity-by-name → execution-and-assertion → execution by
  object → EXECUTION BY IDENTITY-COMPARED OBJECT; within one process
  there is nowhere softer left to stand, and the remaining softness
  BETWEEN processes sits behind the fail-closed floor (xdist detected
  and failed explicitly; skip-when-empty labels itself a selection
  convenience, never evidence). The four-part metadata-impostor
  discriminator and the equal-comparing-twin discriminator are both
  permanent, via the reusable impostor_of probe and the reviewer's
  round-16 construction verbatim. ROUND 17 MOVED THE OBLIGATION TO
  SESSION START: re-resolution alone let a control replaced with a
  non-callable, a foreign function, or nothing at all fall out of the
  discovery FILTERS before validation — success over a reduced set. The
  session-start inventory (captured at import, before any test runs)
  now defines what must remain present, and the gate validates four
  clauses per obligation before any filter — present, an ordinary
  function, of its own module, the PRESENT identity executed — so a
  change fails explicitly and never removes an obligation; additions
  join the obligation under the same clauses, and a control planted
  before capture becomes an obligation, never an exemption (pollution
  can only make the gate stricter). The reviewer's four cases are
  permanent, run against the real gate over a controlled inventory.
- **Round-14 landing (one finding — the census's FINAL static gap):**
  `if False: rd.control_x()` credited as "actually called"; AST call
  identity is stronger than mention and still not runtime evidence. The
  census-claims ladder ends at its only honest carrier: mention →
  invocation → identity → EXECUTION-AND-ASSERTION. Controls are invoked
  through `assert_control` (records the callable identity ONLY after
  the result assert passes); the RUNTIME GATE compares discovered
  controls against the registry, anchored last post-shuffle; the
  reviewer's dead-branch probe is the permanent DISCRIMINATING PAIR
  (static credits it — its stated ceiling; runtime lacks it — why the
  claim moved); the static census RESCOPED to source hygiene. All 21
  call sites converted across both drivers; cross-machine green with
  every control recorded. Staging confessions recorded: two vacuous
  validations of the new gate (flat throwaway; spec-less tree) minting
  the repo-shaped-with-spec staging rule, and the shared-control mutant
  masked by the other registrar.
- **Round-13 landing (one finding — the inventory's own confessed
  misclassification):** TypeAlias was EXCLUDED as "binds a TYPE name" —
  a reason conceding the defect (`type rd = int` shadows exactly like an
  assignment; both reviewer probes proved it on 3.12). The reviewer's
  sentence kept whole: deferred-to-when-a-driver-uses-it REVERSES the
  inventory's purpose. TypeAlias HANDLED where the interpreter has it
  (availability = a parser fact, never a semantic exclusion — and the
  fix's own first commit went CI-red because the ROUND-12 coverage test
  still REQUIRED availability: the new rule applied to one of two
  coverage tests, caught by the 3.10/3.11 lanes where a 3.12-only local
  green could not see it). Coverage is now CAUSAL: every violation
  brackets its construct's AST class; per-construct probes must NAME
  the construct as the shadowing source (appears-somewhere dead; the
  reviewer took the round-13 README's own attack point #1). The
  exclusion-table audit ran across all three maintained tables; every
  surviving reason states why the construct CANNOT BIND or where its
  binding is owned.
- **Round-12 landing (one finding — the binding family's remainder):**
  the round-11 shadow census missed Lambda parameters and structural-
  pattern captures (`lambda rd:` and `case rd:` both rebind the name;
  the reviewer's probes credited the original while runtime invoked a
  replacement). Closed with the remainder learned (Lambda; MatchAs/
  MatchStar/MatchMapping-rest, nested patterns via the walk) and THE
  BINDING INVENTORY: an explicit handled/excluded table over Python's
  name-introducing constructs, exclusions carrying reasons, a coverage
  test asserting every handled entry has a battery probe and every
  ast.Match* class is inventoried — "every binding construct" is a
  table plus two assertions, not a sentence, and the coverage assertion
  PULLED six probes into existence. The census itself PROMOTED to the
  reusable evidence module `seam_model/binding_census.py` (reviewer
  feedback, taken); the structured collected-record feedback queued
  with reason for this round's assembly.
- **Round-11 landing (two findings, both the reviewer taking the round's
  own offered attack points):** INSTANTS, NOT STRINGS — the round-10
  datetime check validated parseability and the fold compared strings
  lexicographically, so an offset-form contributor folded to the
  chronologically WRONG maximum with product and reference AGREEING on
  the wrong value (attack point #2: refusal agreement is not value
  agreement). Production compares datetime objects (graph.py:463-464),
  so the string fold was always an approximation of the semantics it
  claimed; _side now validates the EXACT canonical writer form and the
  fold + clamp compare parsed UTC instants, in product AND reference in
  one commit, with the accepted-value discriminator vector (canonical
  mixed precision, lexical vs chronological disagreement) and a
  VALUE-AGREEMENT runner over every accepted vector. And the census's
  FIFTH rung: shadowing — the round-10 census never applied later name
  binding (a def-shadow or reassigned module alias credited the
  original while runtime invoked a replacement); the constrained
  grammar now refuses EVERY shadow of a protected binding (def/class,
  all assignment forms, walrus, loop/with/except targets, parameters,
  conflicting re-imports), twelve permanent negatives with the
  reviewer's probes verbatim first.
- **Round-10 landing (four findings; the sidecar met its check on first
  contact):** DOMAINS, one recursion past round 9's types — the sweep's
  reader validates every fold output against the SHIPPED MODEL'S domain
  (confidence finite in [0,1]; datetimes parseable canonical form),
  because the reviewer's confidence 2.0 survived a revoke+LIFT into a
  committed edge that failed its own Edge.model_validate; revoke
  refuses with rollback, a refused lift does not half-lift. THE
  REFERENCE TWIN: the round-9 _side fix had reached the product and not
  the 0022 reference oracle — divergence the shared vectors could not
  see; the reference now carries the full current _side, vectors.json
  gains the 12-cell invalid-shape matrix (proven failing against the
  OLD reference first), and a both-implementations test refuses the
  whole matrix through reference AND product. THE CENSUS'S FOURTH RUNG:
  identity, not names — calls resolve through each driver's imports to
  (module, function); rebinding a control is a census violation
  outright; same-name-foreign-call and both rebind shapes are permanent
  negatives. And the PAIR RULE'S PROSE CARRIER: the spec pseudocode had
  round 9's rule in the model only — both principals now guarded BEFORE
  the dereference in the pseudocode, V-BIND reads presence-AND-equality,
  and the propagation check gains a deref-safety rule proven against
  the synthesized v21 divergence it had missed (spec pseudocode was
  PROSE to every prior rule — the reference-twin class, in prose).
- **Round-9 landing (three findings; V-WINDOW explicitly closed) —
  the F1/F3 halves SHARPENED by round 10 above:**
  PRESENCE PRECEDES EQUALITY — "one principal when present" said ONE and
  round 8 checked EQUAL, so a present pair with both principals None
  bound while naming no principal (the only hole; half-None was already
  mismatch). Rule 0 refuses a None principal on either side of a present
  pair BEFORE comparing; enforcement at bind() ONLY, constructors
  deliberately wide so the negative controls can build the illegal
  shapes; cost verified at production (ScopeView raises on a
  non-groupable principal, scope_read.py:307). Persisted-value totality
  went ONE LAYER DEEPER into SHIPPED code: the wrapper was validated and
  the fields _fold consumes were not — {"base":{},"contributor":{}}
  escaped as KeyError, and with the tamper before the revocation it
  crashed revoke_source itself; the sweep's reader now validates its own
  consumption (three fields, presence AND writer-emitted types — a
  mistyped field would escape as TypeError one mutant over, preempted)
  raising its declared RevocationError: refusal + R19 rollback on the
  write path, UNDETERMINABLE on the read path; reviewer's payload + a
  12-cell matrix permanent. And the every-control census's third rung:
  round 7 scanned two modules, round 8 discovered modules but grepped
  TEXT (mention passed for assertion — the reviewer built the synthetic
  control our own attack point offered), round 9 requires INVOCATION
  (AST call census, both drivers; the mentioned-never-invoked decoy is
  the permanent negative).
- **Round-8 landing (all four findings):** THE PAIR RULE — the scope
  cell and the view are present together, absent together, one principal
  when present; ANY violation refuses at rule 0 as `IDENTITY_UNBOUND`.
  Round 7 had refused only the principal-BEARING cell; a principal-less
  one still carries the `visible`/`shape` steps 2/10 consume — the same
  influence channel MINUS attribution, strictly worse — and the producer
  emits no cell without a principal (two `ScopeCell(` sites, one guard),
  so the refusal costs no legitimate path anything. The store driver
  replays the producer's REAL cell viewless, principal stripped, and
  asserts refusal — the exact shape that slipped round 7's rule. The
  interpretation boundary is REGION-TOTAL (any `Exception` inside
  `project_store` → `ProjectionUnreadable`; the reviewer's 10k-nesting
  RecursionError probe and the BLOB-digest/mixed-ordering TypeError are
  permanent cells, both proven escaping first) — the narrowness control
  moved to the region's edge (RuntimeError injected at the sweep
  propagates). The read window is mode-neutral in BOTH remaining
  carriers (§4a headline + signature comment; V-WINDOW cites the
  both-journal-modes test). The every-control sweep is EXHAUSTIVE:
  modules discovered from the seam_model directory, both drivers as the
  assertion corpus, a permanent synthetic-module negative, and the
  plant-in-a-formerly-omitted-module proof run on both machines.
- **Round-7 landing (all four findings; the F1 half FINISHED by round
  8's pair rule above):** the X-C ruling REVERSED — a
  viewless principal-bearing cell is REFUSED at rule 0 (the round-6
  adjudication settled a two-way disagreement while the NORMATIVE
  carrier held the answer: the classifier consumes the cell at steps 2
  and 10 guarded on the CELL's presence, not the view's, so a viewless
  cell decides visibility and shaping — "surplus and unconsumed" was
  false; the wrong-property control is INVERTED and its principal-less
  narrowing split out; the lesson: a control can be executed, green,
  and still assert the wrong property). The persisted-data family
  WIDENED to a STATEMENT (any failure to interpret persisted data →
  UNDETERMINABLE): UnicodeDecodeError from json's encoding detection
  and RevocationError from the sweep's own validation both proven, the
  boundary moved to the sweep call, enumerations named as under-counting.
  The read window stated mode-neutrally in the SPEC (matching the model:
  rollback → exclusion, WAL → snapshot, one invariant — ONE READ
  WINDOW). And the unwired-control CLASS is closed mechanically:
  `test_every_control_in_the_seam_model_is_asserted` enumerates every
  control in both model modules and fails naming any the driver does
  not reference (found a third unwired control on its first run).
- **Round-6 landing (all four findings):** the carried decision is
  DECOMPOSED ONCE at the fill site — `ScopeView.decision()` already
  returns `(visible, shape)` and the round-5 fill had stored the whole
  pair into `.shape`, double-wrapping so a cross-visible probe GROUNDED
  off the carried cell where the direct decision refused; carried ==
  direct is now asserted per reachable decision row with the double-wrap
  kept as a discriminating control. Leg 6 (the cell's principal) is REAL
  in two independently-mutation-detectable halves: view present ⇒ the
  cell is REQUIRED (with the live calls gone, a bound view-without-cell
  either dereferences None or fails open) then its principal must match;
  view absent ⇒ the cell is surplus *(SUPERSEDED: round 7 refused the
  principal-bearing viewless cell; round 8's pair rule refuses ANY
  viewless cell — see the round-8 landing)*. The
  derivation boundary catches `ProjectionUnreadable` ONLY — at this
  round a wrapper over exactly the three decode families (edge, episode,
  ledger) *(SUPERSEDED twice: round 7 widened the family list; round 8
  made the region total — enumerations under-count)* — so a
  malformed LEDGER payload yields UNDETERMINABLE while a non-decode
  failure still propagates. The checker reads EVERY fenced block with
  comments RETAINED, discriminating by position (`: frozenset` fires;
  prose mentioning the word does not) — proven both ways on both
  machines against synthetic round-5 residue.
- **Round-5 landing (F1, F2, F3):** the scope decision is CARRIED, not
  called — `ScopeCell(visible, shape, fail_closed, principal)` computed
  in-transaction; the classifier consumes the cell and the live
  `view.visible`/`view.decision` calls are gone from the pseudocode; rule
  0 binds the cell's PRINCIPAL against the view's in both directions (the
  authority-moves law, third instance: relocating the decision orphaned
  the principal until it was bound). The restriction verdict is
  THREE-VALUED — `clear`/`restricted`/`undeterminable` — because
  `project_store` validates every row (revocation.py:217), so over a
  store containing one malformed row the sweep cannot run and both
  booleans would be fabrications; `undeterminable` is RETURNED never
  raised and maps to FENCED_AS_OF, NEVER EXCLUDED (an uncomputed
  EXCLUDED asserts a revocation never established); the collapse happens
  at the classifier, the carrier keeps all three. The consistency
  mechanism is stated MODE-NEUTRALLY: ONE WORLD PER WINDOW (rollback
  excludes writers; WAL admits them while the reader keeps its snapshot
  — both executed, each mode's mechanism asserted). The 12-cell
  end-to-end matrix (principal × standing × three malformation
  placements) runs through `current_state` with NO raise in any cell.
- **Round-4 landing (F1, F4):** the one-consistent-read runs inside an
  explicit read transaction under the store lock *(this landing
  originally said "BY EXCLUSION … NOT an MVCC snapshot" — SUPERSEDED by
  rounds 7–8: the mechanism is MODE-DEPENDENT — rollback-journal
  excludes writers, WAL snapshots past them — and the only mode-neutral
  invariant is ONE READ WINDOW, ONE WORLD; naming either mechanism as
  THE mechanism is wrong in the other mode, which round 8 found still
  asserted here)*. The ScopeView decision is computed IN-transaction (option
  (a)), so its lazy contribution-ledger reads land inside the window —
  PROVEN by forced interleaving at the reviewer's required point, with
  the discriminating pair (the refused write succeeds the moment the
  window closes) and the autocommit straddle kept as a permanent
  control. And `source_restricted` is a BOOLEAN — the collective sweep
  proves a verdict, not per-digest attribution; `frozenset(standing)`
  was false attribution, named rather than quietly corrected.
- **Round-3 landing — CurrentState (F2):** the bound carrier REPLACES the
  separate current parameter: row, standing set, sweep and read token
  from ONE transaction on ONE connection, so scope/caps/restriction are
  one world BY CONSTRUCTION — there is no second current read to be
  stale against. No caching is specified, and the once-proposed
  `(user, standing-set)` key is named DEAD (the contribution graph moves
  under an unchanged standing set). EXECUTABLE: the derivation, the
  bare-id and affected-membership mistakes (kept as permanent negative
  controls), the lift flip, and the token-moves control all run in
  `restriction_derivation.py`.
- **Round-2 landing — the subtractive projection (F3):** the current leg
  also subtracts on VALID-TIME (current interval must contain T — the
  Jan/Feb/Mar counterexample) and SEMANTIC IDENTITY (same-id content
  change fences the old snapshot; `note` stays in the digest basis
  deliberately — 0026's relay floor scans the note). V-SUBTRACT.

## S3 — the transaction cursor: 0029 owns, consumers obey — MOVED (F6, round-3 F4)

- **Contract:** `txn` is the ONLY cutoff token — non-negative integers,
  one domain; no read surface accepts a datetime cutoff. The epoch is a
  TXN VALUE per user (`epoch_txn(user)` = the baseline batch's txn; 0 for
  fully-journaled users, making the pre-epoch test `until_txn < 0`
  unsatisfiable — no spurious refusals). Allocation is serialized at the
  DATABASE level (max+1 inside the writing transaction under the DB's
  single-writer lock; the instance-local Python lock is named
  insufficient across two `SqliteStore` instances; the `(user_id, seq)`
  PK refuses any residual race). `recorded_at` is minted ONCE per batch.
  Reads include or exclude a committed batch WHOLE (V-BATCH).
- **Round-3 landing — the LOCKING SCHEDULE (F4):** "inside the write
  transaction" was not enough — the reviewer executed two DEFERRED
  transactions reading the same maxima. The schedule is now exact:
  **`BEGIN IMMEDIATE` before ANY allocation read** (the shipped house
  pattern: 0022 R3-1 at revocation.py:6; schema_version.py:1501), txn,
  seq and the batch timestamp minted AFTER the lock, whole-transaction
  retry-or-loud-refusal under `busy_timeout` (0007 §4c), the PK demoted
  to backstop-only. EXECUTABLE: `allocation_schedule.py` runs BOTH
  schedules — IMMEDIATE positive, DEFERRED as the negative control
  keeping the reviewer's reproduction failing forever.

## S4 — the malformed axis crosses the seam — MOVED (F5, C-1, X-2)

- **The division, now three layers, all consumer-owned:** 0029 is a
  RECORDER — it journals whatever state the store held and returns it
  verbatim. 0030 owns (1) the PARSE (unparseable text → MALFORMED
  visible / SCOPE_HIDDEN with a view — V-PARSE, V-FAILHIDDEN), (2) FIELD
  validation (types before membership, required/optional normalizers —
  V-NORMALIZE, V-NORM-TOTAL), and (3) DEFENSIVE EXTRACTION of every field
  the rules read — content fields and trust flags included; a MISSING
  field is MALFORMED, never a default, because a defaulted flag GRANTS
  (V-EXTRACT).
- **How malformed state exists at all (stated so "real load path" is not
  misread):** the store serializes only valid edges — the honest origins
  are a journal OUTLIVING the model that wrote it, or DB-level tamper.
  The fixture must use one of those and say which.
- **Round-5 landing — the adapter contract is DERIVED, not restated
  (F4):** the adapter had drifted STRICTER than production on six fields
  (refusing empty strings the shipped model accepts — failing on
  ordinary data nobody crafted, the inverse and worse half of
  too-permissive); its rules are now introspected from the shipped
  model's own field metadata, and the two-sided invariant — ACCEPT
  everything production emits, REFUSE everything the consumer raises on
  — was verified satisfiable (the identity bounds agree at 1..512).
  Restated contracts drift in both directions; the cure for both is to
  stop restating.
- **Round-3 landing — the adapter is an EXECUTABLE construction (F3):**
  `quarantined`/`use_only` are `@property`, NOT serialized (executed: 18
  keys, neither present) — so the round-2 missing⇒MALFORMED rule would
  have refused every payload, and the flags are DERIVED (two disjuncts on
  `quarantined`, schema.py:482). The parse REFUSES DUPLICATE KEYS (the
  0026 evidence-boundary rule caught the model's own plain parse on its
  first suite run; the executed bypass: a duplicate-`disclosure` payload
  declassifies QUARANTINED→MENTIONABLE under last-wins). The
  scope-feeding field authority is `MembershipResolver._record_shape`
  (scope_read.py:170-176), whose five keys are — EXECUTED, round 5,
  retracting this manifest's own round-4 claim that `disclosure` belonged
  among them — `{author, evidence_ref, lineage, origin, source_id}`.
  `disclosure` is what the ADAPTER's flag derivation needs, not what the
  shape path reads; conflating the two was verification-with-the-wrong-
  question (an executed output misread by its author). VOCABULARY NOTE:
  the shape's KEY is `author` while the FIELD read is
  `author_of_evidence` — output-introspection gives the shape's
  vocabulary, not the carrier's, which is why one explicit translation
  map survives in the propagation check and fails loudly on drift.
  `author_of_evidence` must be the REAL enum (`.value` is accessed). EXECUTABLE:
  `raw_adapter.py`, driving the REAL ScopeView end-to-end with the
  own-vs-foreign discriminating pair, real-payload fixtures, and seven
  proven mutations (three cross-machine).
- Visibility remains the OUTERMOST principal-facing gate; identity
  binding (S6) precedes it because a binding failure reveals only what
  the caller supplied.

## S6 — carrier identity: row authoritative, payload unverified — NEW (C-2, C-4, F4)

- **Contract:** `RawEdgeState.edge_id`/`.user_id` come from the event ROW
  columns and are authoritative (0029 V-VERBATIM's identity clause);
  binding of snapshot/current/envelope — and the VIEW's owner (X-3) — is
  therefore PARSE-INDEPENDENT (0030 rule 0, V-BIND). The payload EMBEDS
  its own identity copy and 0029 NEVER reconciles the halves: the
  consumer MUST verify payload-vs-row agreement (V-CARRIER-AGREES) —
  current-leg disagreement fails HIDDEN so a foreign payload's scope
  fields never reach a visibility decision; snapshot-leg → MALFORMED.
- **Why it is a seam:** C-2's row-sourcing fix CREATED the unreconciled
  duplicate C-4 closes — both were invisible to single-spec review and
  surfaced only in the both-directions cross-check.

## S7 — the event `reason` column is NOT a classifier input — NEW (C-3)

- The column records the EVENT's reason (non-NULL iff kind=`invalidated`);
  the state's own `invalidation_reason` lives INSIDE the payload. With
  baselines this is systematic, not occasional: a migrated INACTIVE
  edge's `baseline` event carries column NULL while its payload carries
  the found reason — a column-wired classifier would silently read the
  entire pre-upgrade inactive population as active-with-no-reason.
  0029 §4b states the rule; 0030 pins V-COLUMN-NOT-INPUT.

## S5 — what is deliberately NOT in the pair (kept LAST as the closing scope statement; numbered before S6/S7 existed — not new)

- **Resolution** (corrected→corrector, absorbed→absorber, gap semantics):
  0028 v2's table, on both substrates, when that arc resumes.
- **Rendering** of `held_at_K` truths: 0028 v2's labeled channel.
- **Scope-policy versioning:** out of scope for both (S2's reasoning).
- **Episode/wiki state journaling:** 0029 §10, deliberately v1-excluded.
- **The future-`valid_from` current-classifier cell:** ruled for SEPARATE
  closure (owner, 2026-08-31) — see the README's S2-ruling note; 0030's
  scope statement ("a 0019 question left untouched") remains true.

## The propagation discipline — NEW (round 4)

- **The episode:** the seam model learned two rules AFTER 0030's round-3
  fold (the strict decoder; the `_record_shape` authority), and nothing
  propagated them back — so v14's §4a-iii INSTRUCTED the exact
  duplicate-key declassification the model forbids. A normative carrier
  that instructs a bypass is worse than one that omits the rule, because
  it is followed confidently. The mechanism is ORDERING: whenever a
  runnable artifact outruns its normative one, the divergence is silent
  by default.
- **Round-4 hardening:** the check now INTROSPECTS `_record_shape` by
  calling it (its round-3 form compared two hardcoded sets — it could
  confirm our restatements agreed, never that both were wrong, which is
  exactly how the false disclosure claim survived it); the verdict's
  NINE surviving carriers are a NAMED regression list walked and
  reported individually, not a sweep ("the full sweep was executed" has
  been false twice in this arc); anchors name mechanisms, never
  formatting (two live false positives documented); probes return
  False, never raise. MUTATIONS 8+7 prove the 0026 gate and this model
  catch DISJOINT halves in BOTH directions (plain-loads revert: model
  fully green, only the gate fires; name-blessed dupe-accepting hook:
  gate green, only the model fires) — proven cross-machine, and the
  no-belt-and-braces ruling is recorded: the pair's value is
  independence, and correlated instruments fail together.
- **The mechanical answer:** `propagation_check.py` binds each model rule
  to an EXECUTED probe and mechanism-name spec anchors
  (whitespace-normalised — it caught ITSELF on a wrapped anchor first
  run), in BOTH directions: model-enforced-but-not-spec-required (the
  v14 failure) and spec-required-but-not-model-enforced (the reverse
  drift). Rule zero applies to it too (an asserted mutilation control +
  a retro-detection reconstructing the v14-shaped spec), and its one
  conditional skip is INVENTORIED (specs/skip_inventory.py — the 0014
  R13-3 gate refused it until it was, which is the gate catching the
  blind spot in the tool built to catch blind spots).

## The joint scenarios — ownership (8 from round 1, 7 added by round 2)

| # | scenario | 0029 asserts | 0030 asserts |
|---|---|---|---|
| 1 | backdated correction, K both sides of the recording | the invalidation's `txn`, not its valid-time; reconstruction at both cutoffs | matrix row `corrected` × before/after-K |
| 2 | revocation → reinstatement, K between | the erased `invalidated_at`/`reason` recovered from the journal | `revoked_source` current-cap: EXCLUDED while standing; the cap LIFTS on reinstatement while `held_at_K` stays stable |
| 3 | `valid_from` moved by recompute after K | the fourth-site event + reconstruction of the pre-recompute interval | classification at T against the SNAPSHOT's interval |
| 4 | same-text replace changing disclosure/scope provenance | full-state trigger fires (digest-invisible class) | content-trust/scope read from the right leg |
| 5 | multi-edge supersession, cutoff at the boundary | whole-batch: both sides observe A-and-B or neither | consumes only batch-resolved snapshots |
| 6 | two transactions, one `recorded_at` | `txn` distinguishes; `seq` orders | n/a (cursor discipline upstream) |
| 7 | later correction/dispute/revocation on an earlier snapshot | the snapshot is reconstructable unchanged | the F2 split: `held_at_K=True`, status capped |
| 8 | malformed edge hidden from the principal | journaled as held (recorder, not validator); traverses the raw carrier | SCOPE_HIDDEN only; visible incoherence on either leg → MALFORMED |
| 9 | migrated pre-existing edge at the epoch + around first mutation (round 2) | baseline payload at the epoch txn; pre-mutation state never `None`/lost; pre-epoch refuses; `epoch_txn=0` contrast cell literal | consumes the baseline snapshot like any other |
| 10 | superseded edge, source later restricted (round 2) | the row's reason honestly still `superseded` (history never rewrites) | EXCLUDED via the standing-state input; MUST FAIL if the row is read instead |
| 11 | snapshot open at K, later superseded, T after current interval (round 2) | both events journaled, whole batches | `FENCED_AS_OF`, `held_at_K=True` (V-SUBTRACT time half) |
| 12 | same-ID semantic replacement after K (round 2) | `mutated` event under the full-state trigger | `FENCED_AS_OF`, current still ACTIVE (V-SUBTRACT identity half) |
| 13 | mismatched snapshot/current identities (round 2) | row-sourced carrier identity makes the probe expressible | `IDENTITY_UNBOUND` before visibility; three fixtures incl. the view leg |
| 14 | malformed state through the REAL load path, hidden + visible (round 2) | the raw carrier lets it traverse; origins stated (drift/tamper) | parse/extraction cells; `SCOPE_HIDDEN` when hidden, `MALFORMED` visible, NO raise anywhere |
| 15 | concurrent txn allocation, two store connections (round 2) | distinct whole batches, unique txns, PK backstop unfired under the serialized schedule | n/a (cursor discipline upstream) |
