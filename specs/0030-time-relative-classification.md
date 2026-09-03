# Feature spec: time-relative trust classification

Spec-Status: draft

*Candidate authored by research (veracium-research), 2026-08-31. The first of
two substrate specs Quentin ruled must precede a full 0028 v2 (as-of query):
0030 is the TRUST surface (this spec), 0029 the transaction-time carrier (dev-
led). 0028 r1 exposed that the shipped classifier cannot ground history at all
(`Edge.assertable` requires `active`); Quentin's ruling was to build the
time-relative trust surface CORRECTLY rather than ship a reference-only dodge.
Authored mechanically-complete from the start (0027/0028 template maturity), with
the round-1 lessons front-loaded — every totality claim is derived from the
AUTHORITATIVE registry (`DISPOSITIONED_REASONS`), never a field comment (0028
R1-1), and unknown reasons FAIL CLOSED.*

| | |
|---|---|
| **Author / session** | research (veracium-research); adopted by dev (lineage per the cells; v27 = the round-15 fold — adopted 2026-09-03, the round-16 shared baseline; frozen from adoption to seal) |
| **Version** | **v27** — the round-15 fold (version-cell delta; the gate lives in evidence and its topology contract lives in the DOCSTRINGS — deliberately not restated here, because a normative sentence naming test-infrastructure properties would mint a new carrier to lag, the census precedent applied to the gate itself). **0029 v9 ACCEPTED, ELEVENTH consecutive byte-identical round; round-14's static-vs-runtime closure credited in full.** **ONE finding, dev's own attack point #1 taken exactly: the registry keyed on `(module, __name__)` — WRITABLE metadata — and the reviewer's impostor with copied module/name/qualname satisfied the real control's key while it never ran.** Identity claimed, metadata delivered. **The fix records the only thing that IS identity in-process: the function OBJECT** — `EXECUTED` is a set of objects, and the gate compares freshly re-resolved discovered callables against the exact objects that ran (with the reviewer's also-consider: re-resolution means a later module-level reassignment cannot silently change what "discovered" means). **The TOPOLOGY BOUNDARY adjudicated and implemented:** the gate DETECTS process-splitting (xdist) and FAILS EXPLICITLY with the aggregate-or-run-single-process instruction — never skipping on a registry no single process can complete; the supported topology stated in `assert_control`'s docstring; skip-when-empty's status stated in its own reason text ("a selection convenience, NEVER positive evidence"). The four-part discriminating test permanent (real control + metadata-copied impostor via the reusable `impostor_of` probe + only-the-impostor-ran + the gate still seeing the real control unexecuted, with the round-14-key-satisfied contrast asserted). **The claims ladder gains its last rung: mention → invocation → identity-by-name → execution-and-assertion → execution BY OBJECT — each rung's softness named by the reviewer, and the final key is the one thing in a process nothing can counterfeit.** | **v26** — the round-14 fold. **0029 v9 ACCEPTED, TENTH consecutive byte-identical round; round-13's TypeAlias repair credited closed; the CI-red disclosure explicitly credited by the reviewer** ("demonstrates the availability seam is exercised rather than merely documented"). **ONE finding — the census ladder's FINAL STATIC GAP, the position-vs-capability rule taken to its logical end: `if False: rd.control_x()` credits as "actually called."** AST call identity is stronger than mention and still not runtime evidence; a static census can never carry an EXECUTION claim. **The closure moves the claim to where it can be true:** `assert_control` invokes, ASSERTS the result, and records callable identity ONLY AFTER the assert passes (a failing control never counts as covered); the RUNTIME GATE — anchored last after test shuffling — requires every discovered control executed-and-asserted in session, failing by design on partial surfaces (an unexecuted control is unexecuted; the gate refuses to guess why). The reviewer's dead-branch construction rides as the DISCRIMINATING PAIR: one probe, both verdicts — the static census credits it (its stated ceiling) while the runtime registry lacks it (why the claim moved); the static census RESCOPED to source hygiene in its own docstring. Both drivers' control sites converted to the runner (research's 17 by AST transform; dev's 4). **Research's staging note, learned by vacuous-pass:** the gate depends on repo SHAPE (module discovery) and SPEC reachability — a flat throwaway passed it vacuously and a spec-less tree failed it honestly on the never-run control — so the gate joins the spec-reading tests in the adoption-boundary class unless the validation surface is repo-shaped with the spec present; proven three-way there (282/0 clean; a mine-only reverted site fails naming exactly its control; restore green). The census-claims ladder in full: mention → invocation → identity → **execution-and-assertion** — each rung's ceiling named by the reviewer, each claim moved to the only carrier that can hold it. | **v25** — the round-13 fold (version-cell delta, evidence-side round). **0029 v9 ACCEPTED, NINTH consecutive byte-identical round; round-12's fixes credited closed in full; the collected-record DECLINE endorsed by the reviewer in their own words** ("a reduced second schema would create two carriers for the same suite claim" — the two-carriers hazard, confirmed from the other side of the table). **ONE finding, dev's, and it is the inventory's own explicitly-reasoned EXCLUSION: TypeAlias.** Excluded as "binds a TYPE name" — which IS binding a name; `type rd = int` shadows a protected alias exactly like an assignment (both reviewer probes reproduced on 3.12: credited-with-zero-violations). **The reviewer's sentence, kept whole because it corrects a whole reasoning pattern: the deferred-to-when-a-driver-uses-it reasoning REVERSES the inventory's purpose — the gate exists to reject the construct BEFORE a driver relies on it.** A protective inventory defers nothing that binds; availability is a PARSER FACT, never a semantic exclusion. Closure: TypeAlias handled where the interpreter has it; the reviewer's probes permanent and version-gated (skip-with-reason below 3.12; the CI 3.12 lane executes them); and **CAUSAL COVERAGE** — every violation now brackets the AST class of its source, and the coverage test requires per-construct a probe whose violation NAMES that construct, killing appears-somewhere coverage (an import can no longer satisfy ImportFrom while another node does the violating). Surface 321 = seam 280 + differential 41, scope beside the count per standing practice. | **v24** — the round-12 fold (version-cell delta; the census grammar lives in evidence and no spec sentence states the binding family — verified by noun sweep, not inherited). **0029 v9 ACCEPTED, EIGHTH consecutive byte-identical round; the ENTIRE round-11 datetime family CREDITED CLOSED** (canonical form, instant comparison, mixed-precision ordering, both agreement directions) plus the original shadowing battery. **ONE finding, dev's, fixed: the shadow census missed Lambda parameters and structural-pattern captures** — `lambda rd: rd.control_x()` and `case rd:` both credited the original while runtime invokes a replacement; both probes reproduced through the real census first. The fix's centerpiece is not the two handlers but THE INVENTORY: `BINDING_CONSTRUCTS`, an explicit handled/excluded table over Python's name-introducing constructs, every exclusion carrying its reason, with assertions that every handled entry appears in a probe (the coverage demand PULLED new probes into existence — async/annotated/augmented/comprehension forms), that every `ast.Match*` kind is inventoried (a future pattern kind fails LOUDLY instead of slipping the family a third time), and that nothing is double-classified. **"Every binding construct" is now a table plus two assertions, not a sentence** — the same move as clause 7's grammar, applied to the census's own coverage claim. The census is promoted to a reusable evidence module (`binding_census.py`) that probes import directly; the reviewer's structured-record feedback is QUEUED WITH REASON for round 13 (a conforming 0013-sealer record is real work worth doing right; the queue stated in the README, not silence). Battery at 23 probes, reviewer's two verbatim first; surface 317 across both drivers + differential. | **v23** — the round-11 fold, both findings dev's (evidence/shipped-code side; this cell is the spec's whole delta, plus a research NOUN SWEEP coming back clean — see below). **0029 v9 ACCEPTED, SEVENTH consecutive byte-identical round; v22's principal-presence propagation CLOSED by the reviewer.** The reviewer took dev's own attack points AGAIN — the bet keeps paying, and its price is that it pays against its author. **F1 — refusal agreement is not VALUE agreement (attack point #2, verbatim):** both `_side` implementations ACCEPTED the shape and AGREED on the chronologically wrong fold — the round-10 datetime check validated PARSEABILITY, not canonical form, and `_fold` compared STRINGS, so an offset timestamp denoting a LATER instant lost the max. The decisive fact, executed: **production compares DATETIME OBJECTS** (graph.py:463-464), so the string fold was always an approximation of the semantics it claimed. And the round-10 comment claiming canonical form "makes lexicographic min/max order-correct" was ITSELF false — canonical mixed precision lexically misorders too ('.'<'Z'). Both halves fixed: `_side` validates the EXACT canonical writer form (aware, utcoffset 0, round-trip identity); `_fold` and the clamp compare PARSED UTC INSTANTS and return the winner's canonical string; product + reference in one commit; and the vectors gain the ACCEPTED-VALUE DISCRIMINATOR (a pair where lexical and chronological order disagree) plus a VALUE-AGREEMENT runner comparing both implementations' OUTPUTS — closing the attack point in the harness, not just the finding. **F2 — the census never applied later name BINDING (attack point #3's residual, extended):** def-shadowing and module reassignment credited the original control with no violations. The constrained-grammar arm completed: a PROTECTED set (imported `control_*` names + seam-module aliases, module list from `_seam_modules()`) with EVERY shadowing construct refused — def/class, all assignment forms, walrus, loop/comprehension targets, with-as, except-as, parameters, re-imports — the reviewer's probes verbatim as permanent cells. **Research's sweep, per the symbol/noun discipline:** "lexicographic" appears NOWHERE in this spec; both "canonical" hits are unrelated (Spec-Status admin; absorption concept); no fold-ordering or string-comparison claim exists in normative text — the false claim lived in code comments and never crossed into this carrier. The v22 history cell's "datetimes parseable canonical form" stays as an accurate narration of what round 10 CLAIMED; this cell is its correction. | **v22** — the round-10 fold, research's half (F4); dev holds F1 (fold-output DOMAIN validation — types were checked, domain was not, and a committed lift laundered `confidence=2.0` into an edge that fails its own model), F2 (the round-9 `_side` fix reached ONE of its TWO implementations — the 0022 reference twin kept the old wrapper-only check while shared vectors had no invalid-shape cases, so the differential suite stayed green through real divergence), F3 (the census's FOURTH rung: name-matching → import-aware callable IDENTITY, with alias rebinding REFUSED). **0029 v9 ACCEPTED, sixth consecutive byte-identical round; the sidecar met the reviewer's check.** **F4 — research's own asymmetric fold:** round 9 wrote the both-side None refusal into the MODEL's bind() and only the cell-side guard into THIS spec's pseudocode, which then dereferenced `view.principal.origin` — a present view with `principal=None` RAISED instead of returning `IDENTITY_UNBOUND`, the one outcome this design never permits. Two carriers of one rule, updated unevenly in the same round the rule was written. Fixed: both-side guard in the pseudocode (the GUARD precedes the DEREFERENCE); V-BIND now reads "principals PRESENT on both sides AND equal" (the queued v22 phrase, reviewer-found exactly where the round-10 spot-read predicted — the queue-and-disclose posture confirming instantly); and the PROPAGATION CHECK gains a deref-safety rule with its own negative control, because the honest answer to "why didn't the checker see this" is STRUCTURAL: it verified mechanism PRESENCE (anchors, carrier types, residue) and never compared the spec's branch logic against the model's — spec pseudocode is prose to it, and two implementations of one contract can diverge invisibly beneath presence checks. The new rule pins the narrow class it can honestly pin — no `view.principal` dereference before its None-guard in the classifier block — anchored on content the block must genuinely carry, not on prose. | **v21** — the round-9 fold. **0029 v9 ACCEPTED for the FIFTH consecutive byte-identical round; V-WINDOW and the read-window wording explicitly CLOSED by the reviewer.** Three findings. **F3 (research):** "one principal when present" said ONE and the code checked EQUAL — a present pair with BOTH principals None satisfied `!=` and bound while naming no principal at all. **Presence precedes equality**: rule 0 now refuses a None principal on either side of a present pair before comparing. Production cannot construct a principal-less `ScopeView` (scope_read.py:307 raises on non-groupable), so the refusal costs no legitimate path — re-enumerated, not recalled. ENFORCEMENT LIVES IN BIND AND NOT IN THE CONSTRUCTORS, deliberately: the stand-ins must admit illegal shapes or the negative controls could not construct them; a narrowed constructor is bypassed by direct construction and blinds the controls while bind stays permissive. **F1 (dev):** persisted-value totality one layer deeper — `{"base":{},"contributor":{}}` in an absorption row crashed `revocation_sweep._side` at the field level (round 7 validated the WRAPPER; nobody validated what `_fold` consumes), and with the tamper pre-revocation the shipped `revoke_source` ITSELF crashed inside its transaction. Fixed in shipped code: the three RECOMPUTED_FIELDS validated per side, present AND typed as the writer emits (a present-but-mistyped field would escape as `TypeError` from `min()` one mutant over — the reviewer's next probe, written now); order A refuses with the declared error and rolls back, order B → UNDETERMINABLE; CHANGELOG carries the crash→refusal behavior change. **F2 (dev):** the every-control census proved MENTION, not INVOCATION — the reviewer took our own attack point #3. Third rung on one gate: round 7 scanned two modules, round 8 discovered modules but grepped text, round 9 requires a real Call node (AST census, both drivers); the permanent negative is the reviewer's own construction — a decoy textual mention that the text census passes and the call census flags. | **v20** — the round-8 fold, research's half (F1 ruling + F3 + the V-BIND phantom); dev holds F2 (region-scoped interpretation boundary) and F4 (the every-control checker's own blind spots). **0029 v9 REMAINS ACCEPTED.** **F1 — THE RULE IN ITS STABLE FORM: the scope cell and the view are a PAIR** — present together, absent together, one principal when present; any violation refuses at rule 0 as `IDENTITY_UNBOUND` (a failure of the ASSEMBLY, not the record — X-4's MALFORMED stays rule 1's answer for the record itself). Three rounds to get here, kept in the comment as lineage: round 6 bound everything ("surplus and unconsumed" — false at the consumption sites); round 7 refused only the principal-BEARING cell, reasoning a principal-less one "identifies no one" — but it still carries the `visible`/`shape` steps 2 and 10 consume, i.e. **the same influence channel minus attribution, which is strictly worse**; round 8's reviewer finished the reversal round 7 started, and the producer already conforms (`restriction_derivation` emits no cell without a view), so the refusal costs no legitimate path anything. The round-7 "narrowing" control is REPLACED by `control_viewless_cell_is_refused`, asserting BOTH halves (bare viewless record binds; any viewless cell refuses) so the rule can neither silently widen nor narrow. **The carrier's round-6 "surplus" prose had ALSO survived ten lines above the round-7 code refuting it** — one file, two contradicting comments, a round apart; swept now. **F3 — two mode-neutrality stragglers of round 7's own fix:** the §4a-i HEADLINE still said "EXCLUSION, not a snapshot" above the passage explaining why naming either mechanism is wrong (the fix replaced the paragraph and not its own headline), and the §4a signature comment still said "one SQLite snapshot"; both mode-neutral now, plus **V-WINDOW** citing the existing both-journal-modes store test. **THE V-BIND PHANTOM:** the invariant row policing binding cited `test_legs_are_identity_bound_before_anything` — a test existing NOWHERE in either driver. The grep-fails class in the invariant table itself; now cites the two real tests and covers the pair leg. | **v19** — the round-7 external fold, research's half (F1, F3, F4 + F2's spec side); the 0029 seat widened the persisted-data family. **0029 v9 REMAINS ACCEPTED, byte-identical to round six.** **F1 — THE MODEL WAS WRONG AND THIS SPEC WAS RIGHT, and the way that happened is the round's lesson.** Round-6's X-C flagged that the model bound a viewless record while the report claimed refusal; that was adjudicated as "code right, message overstated" WITHOUT ASKING THE THIRD CARRIER — this spec, whose rule 0 has refused a principal-bearing cell without a view all along. A two-way disagreement was settled while a third carrier held the answer, and the third was the NORMATIVE one. The merits confirm it: the classifier consumes the cell at step 2 (`if cell is not None and not cell.visible`) and step 10 (`scoped_assertable(True, (cell.visible, cell.shape))`), both guarded on the CELL's presence and NOT the view's — so "the cell is surplus and unconsumed" was false, asserted twice, never checked against the consumption sites. Model and driver now align to this spec; the control that asserted the wrong property is INVERTED and its narrowing (a principal-LESS cell still binds) split into its own control. Rule 0's comment said FIVE legs while describing six — corrected. **F3 — the read window is MODE-DEPENDENT and v18 was not mode-neutral:** it named EXCLUSION as *the* mechanism and then said "one SQLite snapshot" forty lines later. Now stated as rollback-journal → exclusion (SHARED lock, writers refused), WAL → snapshot (MVCC, writers unseen), with the only assertable invariant being the one identical in both: ONE READ WINDOW, every read within it describes one world. **F4 — `control_presence_derivation_agrees` was referenced by NOTHING: X-A repeating in the SAME round, in the other fix, written the same afternoon X-A was reported.** The instance was fixed and the CLASS was not. Now wired — and the class is closed by `test_every_control_in_the_seam_model_is_asserted`, which enumerates every `control_*` in the model modules and fails if any is unnamed by the driver. The `last_outcome` explanation is REMOVED from the version history here, since the adapter comment retracts it (v18 kept the retracted reasoning in the carrier a reviewer reads first). **F2's spec side:** §4a-i's boolean-to-`restricted` corrected to a `RestrictionVerdict` on `source_restricted`, with the unreadable-data transition shown. | **v18** — the round-6 fold, research's half (F2, F4); the 0029 seat holds F1/F3. **F2 — the spec claimed a bind that did not exist.** v17's cell said "rule 0 binds it" of the scope cell's principal and `ScopeCell.principal`'s own comment said "rule 0 checks it"; `bind()` did neither — five legs, none of them the principal, so a cell computed for principal A could answer for an envelope classified under B, the exact escalation the field was added to prevent. THE ROOT CAUSE IS ONE LEVEL DOWN: the model's `View` stand-in carried only `user_id`, so the field to compare against **did not exist on the view** and the check was unwritable — a stand-in narrower than production silently makes a check impossible, and the missing check then reads as a design choice. `View` gains `principal` (production's `ScopeView` has it at scope_read.py:311), `bind()` gains a SIXTH leg, and absence is refused as firmly as mismatch: an uncheckable provenance claim is not weaker than a wrong one, it is the same failure with less evidence. Two discriminating controls added — mismatched-cell, and absent-principal — because the old tests asserted the principal was STORED, not that binding ENFORCES it: **an executed test of the wrong property.** **F4 — residue, third instance on this item family.** Round-5's "residue gone" claim was false: `frozenset` survived at the §4a signature comment and in LIVE pseudocode (`source_restricted = frozenset()`), plus a `_legacy_bool_removed` pseudo-field whose comment advocated a BOOLEAN that round-5's three-valued verdict had itself superseded — stale twice over, in text an implementer copies. All three corrected. **F4b RETRACTS v17's own cell:** its claim that the adapter derives presence from "annotation + metadata + `is_required`" was false — `is_required()` was never called AND is the wrong tool (it reports whether a field has a DEFAULT; the question is whether the model accepts None). **And the obvious fix is also wrong, which is the keeper:** `typing.get_args` looks like the principled replacement for sniffing `str(annotation)`, and executed against the shipped model the two agree on every field but one — `Edge.last_outcome` is an unresolved `ForwardRef('Optional[Outcome]')` where `get_args` returns `()` and a legitimate None would be REFUSED. The reason the string test stays is now an executable control that FAILS if that ForwardRef is ever resolved, because a control outliving its own justification is a check that cannot fail. | **v17** — the round-5 fold, research's half. **F1:** the scope decision is COMPUTED IN-TRANSACTION and CARRIED as `scope_cell`; the classifier consumes it and the live `view.visible`/`view.decision` calls are GONE from the pseudocode — a live call fires lazy ledger reads AFTER the read window closed, reintroducing at the point of use the very seam the one-consistent-read design kills. **F2:** the restriction verdict is THREE-VALUED (`clear`/`restricted`/`undeterminable`) because `project_store` validates every row, so one malformed row makes the sweep RAISE and both booleans would be fabrications; `undeterminable` maps to **FENCED_AS_OF, never EXCLUDED** — EXCLUDED asserts a revocation never established, false attribution one level down from the frozenset. The collapse happens at the CLASSIFIER, never in the carrier. **F4:** the adapter's contract is now DERIVED from the shipped model (annotation + metadata + is_required) rather than restated — it was STRICTER THAN PRODUCTION on SIX fields, refusing records the model emits; restated contracts drift in BOTH directions and the cure for both is to stop restating. **NEW LAW, now predictive: WHEN AN AUTHORITY MOVES, ASK WHAT PAIR IT JUST CREATED.** C-2 moved identity to the row and left the payload's copy unbound (C-4); F1 moves the scope decision to the cell and leaves its PRINCIPAL unbound — so `ScopeCell` carries what it was computed for and rule 0 binds it, fail-closed cells included. | **v16** — the round-4 fold, research's half. **F3 RETRACTION:** v15's claim that `disclosure` belongs to `_record_shape`'s field set is FALSE — executed, it returns exactly `{author, evidence_ref, lineage, origin, source_id}`. The verdict's original list was right; the author ran the function, read its output, and wrote the opposite, having answered what the ADAPTER needs instead of what the SHAPE PATH reads. **F2:** presence is not validity — per-field types plus the SHIPPED identity bounds (1..`IDENTITY_MAX`), with the invariant that the adapter must never pass anything its consumer will raise on; and TYPE PRECEDES MEMBERSHIP everywhere, after the model was found violating this spec's own V-NORMALIZE with an unhashable `disclosure` that RAISED instead of refusing. **F4:** `source_restricted` is a BOOLEAN — `frozenset(standing)` was false attribution. **F1:** the one-consistent-read mechanism is EXCLUSION (SHARED lock for the window), NOT a snapshot, with the scope decision computed in-transaction per option (a); v15's "one world by construction" was false under autocommit. | **v15** — two sentences, no mechanism change, closing an F6-class gap the second-direction cross-check caught: v14 was folded BEFORE two episodes its own §4a-iii now embodies in the runnable model, and the SPEC is the normative carrier an implementer reads. (1) Step 1 said "PARSE json → mapping", which followed faithfully yields a PLAIN decoder — the exact duplicate-key vector executed at the model's first full-suite run, where `"disclosure":"quarantined","disclosure":"mentionable"` parses last-wins to MENTIONABLE and the adapter DECLASSIFIES a quarantined third-party claim. The step now REQUIRES a duplicate-refusing decoder, with the executed flip as its reason: the spec was instructing the vulnerability the model forbids. (2) Step 6 now names the field AUTHORITY — `MembershipResolver._record_shape` (scope_read.py:170-176), which adds `disclosure` to any summary of the scope-feeding set — and requires `author_of_evidence` as the REAL enum, since `.value` is accessed and a string stand-in passes hand-written tests while raising against the live `ScopeView`. | **v14** — the joint round-3 fold, research's half, and the round whose theme is WE DERIVED WHERE WE SHOULD HAVE EXECUTED. **F1** the restriction membership is `("edge", edge_id)` — EXECUTED against a real store: `retire = [('edge','e-083baded…'), ('episode','ep-e90471…')]`, so the population is HETEROGENEOUS ACROSS RECORD TYPES, a bare id fails OPEN always, and a cast would be wrong a second way. The same run showed `affected = []` on that case — X-1's live demonstration, now a permanent regression cell. Plus the explicit NO-STANDING case (zero sweep calls) and ONE sweep (F6's ambiguity killed in that direction). **F2** `CurrentState` REPLACES the current carrier: row, standing set and sweep in ONE transaction on ONE connection, so scope/caps/restriction are one world BY CONSTRUCTION, not by token comparison; `read_token` is audit-only and NO caching is specified (the contribution graph moves under an unchanged standing set — the dead cache named so it is not re-invented). Rule 0 now binds FIVE legs. **F3** the adapter as an EXECUTABLE construction (§4a-iii): the 18 serialized keys enumerated, and the flags DERIVED — `quarantined` has TWO disjuncts (relation OR disclosure), `use_only` one — because they are `@property` and appear in no payload, so X-2's missing⇒MALFORMED rule would have refused EVERY payload. **F5** every post-K GROUNDED matrix cell conditioned on rule 8. Adds the missing-current-row case (absence never grants; it joins the fail-closed branch). | **v13** — **C-4**, found in the re-cross-check of 0029 v6 and a direct consequence of C-2's own fix: the payload embeds `id`/`user_id` (its first two fields), C-2 made the ROW authoritative and rightly stopped deriving identity from the payload — which left the carrier's OWN two halves unbound. A corrupt payload carrying edge B's content under edge A's row would classify B under A, and on the CURRENT leg B's scope fields would decide A's visibility: F4's borrowing escalation re-entering through the carrier, under exactly the at-rest corruption the raw carrier exists to survive. The parse now verifies payload-vs-row identity on both legs, current-leg disagreement taking V-FAILHIDDEN's branch because the visibility decision must not consume it. Adds V-CARRIER-AGREES and a §6a cell. Also cites `ScopeView.user_id` precisely (scope_read.py:292/:310) rather than hedging it — a hedge would be a grep-fails citation at implementation, the `_render_class` class. | **v12** — the both-directions cross-check's SEAM findings, ruled jointly with the 0029 seat. **C-2** identity is now ROW-SOURCED from the carrier (`RawEdgeState.edge_id`/`.user_id`, from the event table's own columns, never the payload), making rule 0 PARSE-INDEPENDENT — a corrupt payload binds correctly first and is refused as MALFORMED later, rather than failing binding for the wrong reason. **C-1** `state` is TEXT and 0030 OWNS THE PARSE: rule 1 parses the current payload (unparseable text and unreadable scope fields share V-FAILHIDDEN's branch, because in both cases we cannot establish whether this principal may see the record and the reason is not their business), rule 3 parses the snapshot (→ MALFORMED). Parse failure and field-validation failure share outcomes because they share ORIGINS. **C-3** the event `reason` COLUMN is never a classifier input. Adds V-PARSE, V-COLUMN-NOT-INPUT and three §6a parse cells. Neither seat could have found C-1/C-2 alone — text-vs-mapping is invisible until one seat holds both ends. | **v11** — dev's round-2 cross-check folded (7). **X-1 BLOCKING, a both-seats miss:** the restriction population is `statement["retire"]` (`:681`, DESIRED STATE under the whole standing set), NOT `affected` (`:609-610`, scoped to THE TARGET). `affected` UNDER-restricts — `direct` (`:605-607`) tests the whole standing set, so the simplest F2 shape reaches `affected` only if a ledger row names the target, and `reach` (`:682-683`) is *defined* as retired keys not in `direct ∪ affected` — and OVER-restricts, since a corroborated survivor the sweep KEEPS is in `affected` but not `retire`. Cost drops to ONE sweep call. **X-2 BLOCKING:** the raw carrier created UNVALIDATED reads after rule 4 — new rule 3b defensively extracts content fields and flags on both legs, missing ⇒ MALFORMED/SCOPE_HIDDEN never a default (a defaulted flag GRANTS; a missing `subject` RAISES); V-RAW's fix must hold V-RAW's discipline. **X-3:** the VIEW leg is now bound in rule 0. **X-4:** V-FAILHIDDEN narrowed — no view means no principal to protect, so MALFORMED. **X-5:** `note` stays in the digest basis, stated as deliberate — 0026's relay floor SCANS the note, so narrowing would let a relay-altering edit pass as identical. **X-6:** §4a-ii footnote for the post-lift cell. **X-7:** section order repaired. Adds V-EXTRACT. | **v10** — two additions on dev's fixture-design note, no mechanism change. §6a's malformed-through-the-real-load-path cell now states HOW malformed state can exist at all — the store serializes only valid edges, so the honest origins are an append-only journal outliving the model that wrote it (0029's own justification for the verbatim carrier, i.e. the same fact from the consumer side) or DB-level tamper — closing a latent contradiction where F5 says the deserializer REJECTS malformed shapes while §6a asks to classify one. And V-RAW now names itself the CONSUMPTION half against 0029's V-VERBATIM read-surface half, tied by the seam manifest rather than a shared symbol. | **v9** — F2's DERIVATION contract wired (new §4b-iii), supplied by the 0029 seat and verified in-source before adoption: `Store.source_restricted` consumes `sweep`'s completeness STATEMENT (`affected`), never its effect list — the shipped comment at `revocation_sweep.py:611-614` already distinguishes statement / desired-state / delta and warns against conflating them, and `affected` (`:615-617`) is pure identity_digest membership with NO active filter. Classifier becomes the THIRD caller of the one computation. Adds the restrict→lift acceptance cell. No other change from v8. | **v8** — the joint round-2 fold. Six findings on 0030: **F4** identity binding of `snapshot`/`current`/envelope BEFORE everything (an unbound pair borrowed B's scope and caps) — placed ahead of visibility, which is safe for round-1 F7 because a binding failure reveals only what the CALLER supplied; **F5** the carrier becomes RAW and 0030 owns ALL validation (the shipped Pydantic deserializer rejects malformed state before any classifier could see it, so the typed carrier made joint scenario 8 unimplementable) — seam S4 confirmed at the interface; **F2** the current source-restriction cap now reads a DEDICATED standing-state input, never the row (verified in-source: `revocation_sweep.py:734` emits `retire` only for ACTIVE rows, so an inactive `superseded` edge keeps that reason while its source stands revoked — and as-of queries are by definition about inactive edges); **F3** the current leg now SUBTRACTS on valid-time and semantic identity, closing the `[Jan,∞)`-superseded-Feb-with-`T`-in-Mar counterexample and the same-id content change; **F7** required/optional normalizer split; **F8b** unknown string reason removed from the incoherent family and V-STALE's "iff" scoped to grounded results. Adds V-BIND, V-RAW, V-TRUST-INPUT, V-SUBTRACT, V-NORM-TOTAL, V-FAILHIDDEN and §6a's five new 0030 cases. | **v7** — dev v6 both-check folded: **B-1** normalization extended to the `current` leg (unhashable reason reaching `dict.get`; `current.invalidated_at` normalized outside the guard) and **B-2** structural coherence applied to `current` (the cap must never read an incoherent state). Both are the mechanical completion of the F6/F2 folds onto the second parameter F2 introduced. v6 — joint round-1 findings folded: **F2** two-state (`snapshot` vs `current`, held_at_K vs assertable-now, current caps never time-travel) + the reason×cutoff matrix (§4a-ii); **F6** type/UTC normalization before any membership or comparison, unknown reason ruled FENCED (not MALFORMED); **F7** visibility is the OUTERMOST gate (hidden never leaks MALFORMED); **F8** carrier sweep. v4 — dev v3-re-read minors folded (m-1 inverted-vs-empty interval in rule 0; m-2 `now` made load-bearing for stale-at-recall). v3 — pre-review folded (7 findings): (1) scope via time-relative verdict not `shape()`; (2) state-coherence rule 0 / MALFORMED; (3) total `AS_OF_DISPOSITION` dict not allow-set; (4) absorbed groundable, not "unreachable"; (5) `Result{status,flags}` + `now`; (6) §6a state-families not naive product; (7) baseline pinned post-0027 + UTC-aware datetimes. (v2 folded dev's D-1/D-2/d-3/d-4.) |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (author) · dev (reviewer, roles inverted from 0027) |
| **External review** | REQUIRED — new trust surface; touches classification. Entry on Quentin's word |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0019 / 0023 / 0026 / 0027** — the current trust classes and the render-time
  classifier. **The render-time classifier is `history_label` (`graph.py:270`)**
  — NOT `_render_class`, which was a spec-only fiction (finding 7): it exists in
  no code at any commit; the shipped function returning
  RETIRED_HISTORY/QUARANTINED_CLAIM/CONTESTED_CURRENT/UNVERIFIED_CURRENT/
  GROUNDED_CURRENT is `history_label`. **BASELINE PIN:** 0030 is built on top of
  ACCEPTED 0027, so its baseline is the **post-0027 implementation commit** — not
  because of any render-classifier symbol (`history_label` exists at every
  commit) but because 0030's V-CURRENT-UNCHANGED test reuses **0027's v10
  oracle** (`specs/evidence/0027/v10_oracle/`, post-0027) and 0030 composes with
  0027's accepted recall. Dev pins that commit at adoption; all §Spec-Requires/§6
  citations (`Edge.assertable schema.py:501`, `history_label graph.py:270`,
  `gate.scoped_assertable`, `ScopeView.decision`) are grep-verified against THAT
  commit (pre-dispatch caught `_render_class` failing exactly that grep).
  **UNCHANGED** by 0030: it adds a PARALLEL time-relative classifier, does not
  modify `Edge.assertable` (additive discipline, 0027).
- **0003** — reason-carrying, history-retaining supersession: the
  `invalidation_reason` this spec keys on (`schema.py:432`), and the retained
  history (`invalidated_at` set — "so history is queryable", `schema.py:421`).
- **the `DISPOSITIONED_REASONS` registry (`schema.py:407`)** — the AUTHORITATIVE
  closed reason set (seven: `disputed`, `corrected`, `superseded`,
  `revoked_source`, `lapsed`, `decayed`, `absorbed_duplicate`). 0030's
  historical-truth disposition is TOTAL over this set and derived from it, so a
  producer growing an eighth reason fails the registry-totality test until 0030
  dispositions it (mirroring W5 / `test_invalidation_reason_registry_is_total`).
- **0022 / 0023** — revocation / non-revival: `revoked_source` (0022's reserved
  seat) is withdrawn evidence and NEVER grounds at any T (V-NEVER).
- **0020** — scope (S1 principal boundary): `assertable_as_of` composes with
  `ScopeView` — a historical edge groundable-as-of-T is grounded ONLY for
  principals to whom it is assertable — composed via `gate.scoped_assertable` on
  the TIME-RELATIVE verdict, NOT `shape()` (finding 1; §4c). 0020 owns read visibility (0028 R1-5 corrected the
  0021 miscite).
- **0011** — `correct()`: the `corrected` invalidation whose retroactive-falsity
  this spec classes NEVER-groundable.

**0029** (transaction-time carrier) — `RawEdgeState` and `CurrentState` are consumed DIRECTLY (round-4 C9).


### What 0030 is NOT (scope fences — 0028 R1 lessons)
- **NOT a change to `Edge.assertable`.** The current classifier is untouched;
  0030 adds `assertable_as_of`. No recall regression (V-CURRENT-UNCHANGED).
- **NOT reason RESOLUTION.** 0030 CLASSIFIES a given edge at T (groundable /
  fenced / excluded / not-valid-at-T). It does NOT decide which edge a query
  returns — following `corrected`→corrector or `absorbed_duplicate`→absorber is
  the QUERY layer's job (0028 v2's reason→resolution table). 0030 says "a
  corrected edge is never groundable at any T"; 0028 says "when you hit one,
  resolve to the corrector."
- **NOT transaction-time.** 0030 is VALID-time classification only
  (`valid_from`/`invalidated_at`). The `observed_at` transaction axis and
  `known_as_of` are 0029 + a later 0028 phase.

---

## 1. Problem and motivation

`Edge.assertable` (`schema.py:501`) is `self.active and not self.quarantined and
not self.use_only`, and `active` is `invalidated_at is None` (`schema.py:478`).
So assertability is tied to being the **current** value: a historical edge —
even one that was validly, groundedly true throughout its interval — can NEVER
be asserted, only rendered as fenced context. 0028 round 1 named this the
"killer": "time and trust orthogonal," as written, cannot produce a historical
assertion at all, so as-of over history could only ever fence.

The current classifier **conflates two independent questions**:
1. *Is this the current value?* (`active` — `invalidated_at is None`)
2. *Is this trustworthy content?* (not `quarantined`, not `use_only`)

For a point-in-time question — "was Priya's city Boston in May?" — the honest
answer is grounded (Boston WAS her city then, validly held until it changed).
0030 **decouples** the two: it adds
`classify_as_of(envelope, snapshot_raw, current_state, T, now, view)` — "was this edge validly,
trustworthily true at T, and may it be asserted now" — returning
`Result{status, held_at_K, flags}` (§4a) and keeping every trust exclusion intact.
This is the substrate 0028 v2 needs to return an ASSERTABLE historical answer
rather than a fenced one.

**Why this is delicate (the new trust surface Quentin ruled we build, not
dodge).** Decoupling assertability from `active` means a historical edge can now
ground. Done wrong, that is a laundering path: a `corrected` error, a `disputed`
claim, or `revoked_source` content could ground at some T. The whole spec is the
discipline that this CANNOT happen — a registry-derived, fail-closed total disposition mapping
plus the time-invariant content-trust exclusions plus the scope composition.

## 2. Field contracts touched

`grep -rn` at author time (dev re-runs at implementation):

| field | read / written | contract | preserves? |
|---|---|---|---|
| `Edge.assertable` (`schema.py:501`) | READ, **UNCHANGED** | the current classifier | YES — 0030 adds a parallel predicate; current path byte-identical (V-CURRENT-UNCHANGED) |
| `Edge.invalidation_reason` / `valid_from` / `invalidated_at` (`schema.py:430-432`) | READ | the reason + valid-time interval 0030 keys on | YES — read-only |
| `DISPOSITIONED_REASONS` (`schema.py:407`) | READ + a PARALLEL disposition added | the authoritative reason registry | YES — 0030 adds `AS_OF_DISPOSITION` (total dict), key-equal to the same set, fail-closed |
| NEW `classify_as_of(envelope, snapshot_raw, current_state, T, now, view=None) -> Result{status, held_at_K, flags}` (+ boolean `assertable_as_of`) | WRITTEN | the time-relative classifier primitive | additive |
| `ScopeView` (`scope_read.py:280`) | READ | composes for "assertable-to-whom at T" | YES — reuses the shipped lens |

### 2a. The `AS_OF_DISPOSITION` total mapping (derived, fail-closed)
0030 adds a **TOTAL disposition mapping** keyed on the SAME reasons as
`DISPOSITIONED_REASONS` — NOT an allow-set (round-1 finding 3). An allow-set
records only positive dispositions, so it cannot distinguish "deliberately never
groundable" from "forgotten when a new reason was added": adding an eighth
`DISPOSITIONED_REASONS` key would silently default to fenced, safe at runtime but
never forcing the author to rule it. A total dict + exact-key-equality FAILS THE
BUILD on any undispositioned reason (the discipline `DISPOSITIONED_REASONS`
itself uses, not the `WIKI_RETAINING` allow-set):
```
AS_OF_DISPOSITION: dict[str, str] = {   # every DISPOSITIONED_REASONS key, explicitly
    "superseded":         GROUNDABLE,   # was validly true until it changed
    "lapsed":             GROUNDABLE,   # staleness is not falsity
    "decayed":            GROUNDABLE,   # low-confidence-now is not was-false
    "absorbed_duplicate": GROUNDABLE,   # was true; 0028 resolves to the absorber (finding 4)
    "corrected":          FENCED,       # retroactively false
    "disputed":           FENCED,       # trust revoked / contested at any T
    "revoked_source":     EXCLUDED,     # withdrawn — 0022 non-revival, not even fenced
}
# Build gate: assert set(AS_OF_DISPOSITION) == set(DISPOSITIONED_REASONS) exactly
# (like W5) — a new reason in either registry fails until dispositioned in BOTH.
# Runtime lookup DEFAULTS an unknown/missing key to FENCED (fail-closed), so even
# a registry drift can only fence, never ground.
GROUNDABLE / FENCED / EXCLUDED are the three closed dispositions.
```
**`AS_OF_DISPOSITION`'s GROUNDABLE set is deliberately NOT `WIKI_RETAINING`.**
They answer different questions: `WIKI_RETAINING` = {lapsed, decayed,
absorbed_duplicate} is "does the CURRENT view survive this invalidation"; the
GROUNDABLE reasons in `AS_OF_DISPOSITION` add **`superseded`** because "was it
validly TRUE at T" is a different test — a superseded fact was true until it
changed, so it must NOT survive in the current wiki (the value moved on) yet MUST
be groundable as-of a T inside its interval. That asymmetry (`superseded`:
wiki-drop but as-of-groundable) is the whole reason 0030 needs its own mapping
rather than reusing `WIKI_RETAINING`.

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| the query time `T` and eval time `now` | `None T` → caller error (the as-of layer supplies T) | non-datetime → typed refuse; **naive/aware mismatch → normalise to UTC-aware BEFORE compare** (finding 7 — "any datetime valid" was false; a naive-vs-aware `<` raises). `T`,`now`,`valid_from`,`invalidated_at` are all coerced UTC-aware | timezone crafted to skew an interval boundary | **V-INTERVAL** — UTC-aware comparison only |
| the edge's `invalidation_reason` | `None` on an INACTIVE edge → MALFORMED (finding 2); `None` on active → the well-formed active case | non-str → MALFORMED (fenced) | eighth/unknown reason → `FENCED` (default) | a producer emitting a novel reason to ground history | **V-FAILCLOSED** — `AS_OF_DISPOSITION` total dict, default `FENCED` |
| the **carrier inputs** — `envelope`, `snapshot_raw`/`current_state.current_raw` (TEXT), `current_state.source_restricted` (`clear`/`restricted`/`undeterminable`), `scope_cell` (`visible`, `shape`, `fail_closed`, `principal`), `read_token`, `view` (round-4 C2; round-5 F1/F2) | a missing current row ⇒ the fail-closed branch; absence never grants; an unprojectable store ⇒ `undeterminable`, RETURNED not raised | unparseable text, payload/row identity disagreement, out-of-bound identity fields ⇒ refuse (never raise) | an unknown payload key is ignored; an unknown reason FENCES | a foreign payload under this row; a foreign view riding along; **a scope cell computed for another principal replayed against this envelope** | **V-BIND**, **V-PARSE**, **V-CARRIER-AGREES**, **V-EXTRACT** |
| the **edge STATE** (`invalidated_at` × `invalidation_reason` × interval) | — | active+non-`None` reason; inactive+`None` reason; inverted interval (`invalidated_at < valid_from`) — all reachable via `add_edge` (schema does not couple the fields) | — | a crafted incoherent edge to reach the grounding branch | **V-MALFORMED** — state-coherence rule 0 refuses every incoherent shape BEFORE any grounding branch; never grounds |
| the principal | `None` → unscoped (self) | via 0020 | — | a principal querying another's restricted history | **V-SCOPE** — composes via the time-relative verdict through `gate.scoped_assertable`, NOT `view.shape()` (finding 1) |

### 2c-ii. Assertions about reach — REQUIRED

| claim | invariant |
|---|---|
| "0030 never makes `corrected`/`disputed`/`revoked_source`/`quarantined`/`use_only` groundable at ANY T" | **V-NEVER** |
| "an unknown/eighth reason can never ground" | **V-FAILCLOSED** (total dict, `set(AS_OF_DISPOSITION)==set(DISPOSITIONED_REASONS)`, default FENCED) |
| "0030 changes no current-recall behaviour" | **V-CURRENT-UNCHANGED** — `Edge.assertable` is not modified and the current recall path never calls `assertable_as_of`. The two predicates agree EXCEPT on two edge cells where valid-time and current-ness genuinely differ (§4e), in both of which `assertable_as_of` gives the temporally-correct answer; neither is a current-path change |
| "a historical edge grounds only for principals who may assert it" | **V-SCOPE** — 0020 composition |
| "0030 adds no field to `Edge`" | **V-ADDITIVE** |

## 3. Trust-class matrix — REQUIRED, blocking

The classifier is three independent gates ANDed — time validity, time-invariant
content trust, and the reason-keyed historical-truth disposition — then composed
with scope:

| gate | what it checks | time-varying? |
|---|---|---|
| **time validity** | `valid_from ≤ T AND (invalidated_at is None OR T < invalidated_at)` (half-open interval) | yes — the only time-varying gate |
| **content trust** | `not quarantined AND not use_only` | NO — a quarantined/use_only edge is unassertable at every T |
| **historical truth (`held_at_K`)** | from the SNAPSHOT only: coherent-active → yes; else `AS_OF_DISPOSITION[reason] == GROUNDABLE` (default FENCED) | NO — fixed by the snapshot's reason |
| **current caps (F2)** | from `CurrentState`, computed in ONE read window — the restriction verdict from the STANDING SOURCE STATE (never the row, which keeps its old reason when the sweep skips inactive rows): restricted → `EXCLUDED`; current corrected/disputed/quarantined/use_only → `FENCED_AS_OF`. Subtract-only; never grants | per-`now`, never time-travelled |
| **scope** (with principal) | CURRENT `ScopeView`: `visible()` as the OUTERMOST gate (F7), then `gate.scoped_assertable` on the TIME-RELATIVE verdict — **never the shipped `shape()`** (F8.1; it short-circuits on today's `assertable` and so never demotes history). Current scope always governs; 0029 does not version scope policy or membership (§4a) | per-principal, never time-travelled |

**Load-bearing statement:** 0030 lets an edge be assertable-as-of-T ONLY when it
was BOTH validly-held at T (time + a groundable reason) AND is trustworthy
content (not quarantined/use_only) AND assertable to the principal. It never
relaxes a trust exclusion; it only removes the *current-ness* requirement, and
only for reasons that mean "was validly true then."

## 4. Behaviour

### 4a. The classifier — exact (TWO-STATE, round-1 F2)

**A single `Edge` cannot carry the question** (F2). Answering "was this
assertable at T, given knowledge cutoff K" needs the §4a input set — envelope, `snapshot_raw`, `current_state`, `T`, `now`, `view` (round-4 C4; it was three before the carrier work) — and
conflating them is what round 1 broke:

| input | what it is | who supplies it |
|---|---|---|
| **`snapshot`** | the edge's state AT the knowledge cutoff K | 0029's full-state journal (F1) — or the live edge when no K is given |
| **`current`** | the edge's state NOW (reason, quarantine, use_only) | the live store — used ONLY to SUBTRACT (an outer cap), never to grant |
| **`view`** | CURRENT principal visibility/shaping | 0020 `ScopeView` — **current scope always governs** (see below) |

**Why current scope always governs:** 0029 versions edge state, **not** scope
policy or membership evidence — so historical scope is not reconstructable, and
inventing one would be a guess about who could see what. The only sound rule is
that *today's* boundary gates every answer, including historical ones. This is
also the safe direction: scope can only narrow what a principal sees.

**Two verdicts, not one** (the F2 ruling):
- **`held_at_K`** — *"the store held this belief at K."* A historical fact about
  our own knowledge. Computed from `snapshot` ALONE.
- **`status`** — *"may this be asserted as fact NOW."* `held_at_K` AND the
  current caps allow it.

A record corrected/disputed/revoked **after** K is therefore
`held_at_K=True, status=FENCED_AS_OF` (or `EXCLUDED`) — we honestly report that
we believed it then, and equally honestly refuse to assert it now. Current
restrictions **never time-travel away**; 0022 non-revival in particular is
absolute.

```
# INPUTS (round-3 F2 — CurrentState replaces the bare current carrier)
#   envelope        the REQUESTED (user_id, edge_id).
#   snapshot_raw    `RawEdgeState(edge_id, user_id, state: str, ...)` from 0029.
#                   Identity is ROW-SOURCED; `state` is payload TEXT.
#   current_state   `CurrentState(user_id, edge_id, current_raw: str|None,
#                   source_restricted: RestrictionVerdict, read_token: int,
#                   scope_cell: ScopeCell|None)` —
#                   row, standing set and sweep all evaluated inside ONE read
#                   transaction on ONE connection — one read WINDOW, one world
#                   (mode-neutral; round-8 F3 caught "one SQLite snapshot"
#                   surviving here after round 7 corrected the same phrase
#                   twenty lines down). It REPLACES the separate `current` parameter:
#                   there is no second current read to be stale against, and
#                   the scope projection is parsed from THIS `current_raw`, so
#                   scope and caps are the same world BY CONSTRUCTION rather
#                   than by token comparison.
#   read_token      audit + cross-read correlation only. NOT a cache key:
#                   the reviewer killed `(user, standing-set)` caching because
#                   the CONTRIBUTION GRAPH can move under an unchanged standing
#                   set. No caching is specified anywhere; every call
#                   recomputes in its own transaction. Stated so an implementer
#                   does not re-invent the dead cache.

def classify_as_of(envelope, snapshot_raw, current_state, T, now, view=None) -> Result:
    # 0. IDENTITY BINDING — SIX legs (snapshot, current_state, envelope, the
    #    view, and the scope cell's PRINCIPAL on both the view-present and
    #    view-absent branches), all row-sourced, all before anything else.
    #    Round-7 F1: this said FIVE while describing six, and the executable
    #    model disagreed with the branch below. The SPEC was right. Parse-
    #    independent (C-2), and safe ahead of visibility because a binding
    #    failure reveals only what the CALLER supplied.
    if not (snapshot_raw.edge_id == current_state.edge_id == envelope.edge_id
            and snapshot_raw.user_id == current_state.user_id == envelope.user_id):
        return Result(IDENTITY_UNBOUND, held_at_K=None)
    # `view.user_id` is a REAL exposed attribute — `ScopeView.__init__`
    # (scope_read.py:292) assigns `self.user_id = user_id` at :310. Cited, not
    # hedged: a hedge would be the grep-fails citation the `_render_class`
    # lesson is about.
    if view is not None and view.user_id != envelope.user_id:
        return Result(IDENTITY_UNBOUND, held_at_K=None)
    # ROUND-5: the SCOPE CELL is a leg too. Moving the scope decision into the
    # carrier (F1) removes the live read but recreates C-4's unbound-leg risk
    # one level down: a cell computed for principal A, passed with an envelope
    # classified for B, answers the WRONG QUESTION while looking well-formed.
    # `ScopeView.principal` is real — `self.principal = principal` at
    # scope_read.py:311 — and `Identity` is `(origin, source_id)`.
    # THE PREDICTIVE FORM, now a law of this seam rather than an observation:
    # WHEN AN AUTHORITY MOVES, ASK WHAT PAIR IT JUST CREATED. C-2 moved
    # identity to the row and left the payload's copy unbound (C-4); F1 moves
    # the scope decision to the cell and leaves its principal unbound unless
    # this line exists. The FAIL-CLOSED cell binds too: it was also computed
    # FOR someone, and an unbound hidden cell could be replayed against another
    # principal's envelope just as silently.
    cell = current_state.scope_cell
    if view is not None:
        if cell is None:
            return Result(IDENTITY_UNBOUND, held_at_K=None)   # view without a cell
        if cell.principal is None or view.principal is None:
            return Result(IDENTITY_UNBOUND, held_at_K=None)   # round-9 F3 +
            # round-10 F4: a present pair must NAME its principal ON BOTH
            # SIDES. v21 guarded only the CELL side and then dereferenced
            # `view.principal.origin` -- a present view with principal=None
            # RAISED instead of refusing, the one outcome this design never
            # permits. The model's bind() had both guards; the spec had one:
            # research's own asymmetric fold, two carriers of one rule updated
            # unevenly IN THE SAME ROUND the rule was written. Presence
            # precedes equality, and the GUARD precedes the DEREFERENCE.
            # Production cannot build a principal-less ScopeView
            # (scope_read.py:307 raises), so neither refusal costs a
            # legitimate path.
        if cell.principal != (view.principal.origin, view.principal.source_id):
            return Result(IDENTITY_UNBOUND, held_at_K=None)
    elif cell is not None:
        return Result(IDENTITY_UNBOUND, held_at_K=None)   # ANY cell without a
        # view (round-8 F1): the cell and the view are a PAIR. Round 7 refused
        # only the principal-BEARING cell; a principal-less one still carries
        # the visible/shape steps 2 and 10 consume -- the same influence
        # channel minus attribution, strictly worse -- and the producer never
        # emits a cell without a view, so this refusal costs no legitimate path.

    # 1. THE CURRENT WORLD — parse + minimal scope projection, ONE branch.
    #    A MISSING current row (`current_raw is None`) joins it: an absent row
    #    and an unreadable one are the SAME epistemic state — we cannot
    #    establish the current world — and absence must never GRANT (the
    #    subtract-only rule). Unparseable text, unreadable scope fields and a
    #    missing row therefore share this outcome.
    #    DEFENSIVE TOTALITY over a shape the type admits, BELIEVED UNREACHABLE
    #    today: `edges` rows are deleted only in `forget_user`'s table loop
    #    (sqlite.py:1753/:1776 — the one DELETE touching edges), and V-ERASE
    #    removes the user's journal in the SAME transaction, so a surviving
    #    snapshot with no current row cannot arise through any shipped path.
    #    Stated rather than omitted: if a future mutator adds a row-delete the
    #    branch is already correct, and the unreachability claim becomes the
    #    thing a V-TOTAL-style sweep re-checks.
    #    Identity is verified against the ROW-sourced id here too (C-4): a
    #    payload carrying another edge's content must not have ITS scope fields
    #    decide THIS edge's visibility.
    #    The CELL is precomputed in the read window; the classifier NEVER calls
    #    `view.visible` or `view.decision` (round-5 F1). A live call would fire
    #    lazy contribution-ledger reads AFTER the window closed — the very seam
    #    the one-consistent-read design exists to kill, reintroduced at the
    #    point of use.
    if current_state.current_raw is None:
        return Result(SCOPE_HIDDEN if view is not None else MALFORMED,
                      held_at_K=None)

    # 2. VISIBILITY — the OUTERMOST principal-facing gate (round-1 F7),
    #    now READ FROM THE CELL. `fail_closed=True` marks a cell computed from
    #    an unreadable payload: hidden, never a raise (round-5 F2).
    if cell is not None and not cell.visible:
        return Result(SCOPE_HIDDEN, held_at_K=None)

    # 3. PARSE + ADAPT BOTH PAYLOADS through §4a-iii's adapter, which owns
    #    schema validation, enum validation and the DERIVATION of the trust
    #    flags. Round-3 F3: `quarantined`/`use_only` are @property and are NOT
    #    serialized — a payload never carries them, so reading them as fields
    #    would refuse every payload.
    snap = adapt(snapshot_raw.state, expect_id=snapshot_raw.edge_id,
                 expect_user=snapshot_raw.user_id)
    cur = adapt(current_state.current_raw, expect_id=current_state.edge_id,
                expect_user=current_state.user_id)
    if cur is None:
        return Result(SCOPE_HIDDEN if view is not None else MALFORMED,
                      held_at_K=None)
    if snap is None:
        return Result(MALFORMED, held_at_K=None)

    try:
        T    = as_utc_required(T)
        now  = as_utc_required(now)
        s_vf = as_utc_required(snap.valid_from)
        c_vf = as_utc_required(cur.valid_from)
        s_ia = as_utc_optional(snap.invalidated_at)
        c_ia = as_utc_optional(cur.invalidated_at)
    except (TypeError, ValueError):
        return Result(MALFORMED, held_at_K=None)
    reason = snap.invalidation_reason

    # 4. STATE COHERENCE — structure only, both legs. An unknown-but-well-formed
    #    reason is NOT incoherent (F8b): coherent, and fenced at rule 6.
    def _coherent(ia, r, vf) -> bool:
        if ia is None:
            return r is None
        return r is not None and vf <= ia
    if not (_coherent(s_ia, reason, s_vf)
            and _coherent(c_ia, cur.invalidation_reason, c_vf)):
        return Result(MALFORMED, held_at_K=None)

    # 5. TIME VALIDITY at T over the SNAPSHOT's interval (half-open).
    if not (s_vf <= T and (s_ia is None or T < s_ia)):
        return Result(NOT_VALID_AT_T, held_at_K=False)

    # 6. HELD AT K — snapshot alone. Unknown reason DEFAULTS to FENCED.
    held = (True if s_ia is None
            else AS_OF_DISPOSITION.get(reason, FENCED) == GROUNDABLE)
    held = held and not snap.quarantined and not snap.use_only

    # 7. CURRENT SOURCE RESTRICTION — the standing-state verdict, computed in
    #    the SAME read as `current_raw` (F2). Non-empty ⇒ restricted.
    #    THREE-VALUED (round-5 F2). `project_store` validates EVERY row
    #    (revocation.py:217), so ONE malformed row anywhere makes the sweep
    #    raise — the restriction becomes IMPOSSIBLE to compute, not merely
    #    awkward, and both True and False would be fabrications.
    if current_state.source_restricted is RESTRICTED:
        return Result(EXCLUDED, held_at_K=held)    # 0022 non-revival: any K
    if current_state.source_restricted is UNDETERMINABLE:
        # FENCED, never EXCLUDED. EXCLUDED is the vocabulary for "a standing
        # revocation covers this edge"; returning it uncomputed would ASSERT a
        # revocation never established — false attribution one level down from
        # the frozenset, corrupting the very distinction the third value exists
        # to preserve. Both refuse to ground; only one claims a reason.
        return Result(FENCED_AS_OF, held_at_K=held)

    # 8. SUBTRACTIVE CURRENT PROJECTION — valid-time AND semantic identity.
    if not (c_vf <= T and (c_ia is None or T < c_ia)):
        return Result(FENCED_AS_OF, held_at_K=held)   # current interval ended
    if content_digest(snap) != content_digest(cur):
        return Result(FENCED_AS_OF, held_at_K=held)   # same-id content change

    # 9. REMAINING CURRENT CAPS — subtract only, never grant.
    current_ok = (not cur.quarantined and not cur.use_only
                  and (c_ia is None
                       or AS_OF_DISPOSITION.get(cur.invalidation_reason,
                                                FENCED) == GROUNDABLE))
    if not (held and current_ok):
        return Result(FENCED_AS_OF, held_at_K=held)

    # 10. CURRENT SCOPE SHAPING — on the time-relative verdict, not view.shape().
    if cell is not None and not gate.scoped_assertable(True, (cell.visible, cell.shape)):
        return Result(FENCED_AS_OF, held_at_K=held)   # from the CELL, no live call

    already_stale = (cur.invalidation_reason in ("lapsed", "decayed")
                     and c_ia is not None and c_ia <= now)
    return Result(GROUNDED_AS_OF, held_at_K=True,
                  flags={"stale-at-recall"} if already_stale else set())

def assertable_as_of(envelope, snapshot_raw, current_state, T, now, view=None) -> bool:
    return classify_as_of(envelope, snapshot_raw, current_state,
                          T, now, view).status == GROUNDED_AS_OF
```

### 4a-i. `CurrentState` — the derivation contract (round-2 F2; renamed round-4 C5, `current_trust` was the pre-carrier name)

The classifier CONSUMES this input; the store DERIVES it. Contract, supplied by
the 0029 seat and verified in-source here before adoption:

```
Store.current_state(user_id, edge_id, principal=None) -> CurrentState(
    user_id, edge_id,                  # identity — rule 0 binds it like every leg
    current_raw: str | None,           # the edge row's serialization VERBATIM
    source_restricted: RestrictionVerdict,   # THREE-VALUED (round-5 F2):
                                       #   clear | restricted | undeterminable
                                       # `project_store` validates EVERY row
                                       # (revocation.py:217), so ONE malformed
                                       # row makes the sweep RAISE — the
                                       # restriction is IMPOSSIBLE to compute,
                                       # and over such a store both true and
                                       # false would be fabrications. Returned,
                                       # never raised: a raise in this path is
                                       # the one indefensible outcome.
                                       # THE COLLAPSE HAPPENS AT THE CLASSIFIER,
                                       # NEVER HERE — the carrier keeps all
                                       # three so a render or audit consumer can
                                       # tell "restricted" from "could not
                                       # determine", though both refuse to
                                       # ground. Pre-collapsing would re-lose
                                       # the information one hop later.
    scope_cell: ScopeCell | None,      # round-5 F1: the scope decision computed
                                       # IN-TRANSACTION and carried, so the
                                       # classifier never calls view.visible /
                                       # view.decision — a live call fires lazy
                                       # ledger reads AFTER the read window
                                       # closed. ScopeCell(visible, shape,
                                       # fail_closed, principal); None = NO
                                       # principal supplied, which is distinct
                                       # from a computed-hidden cell.
                                       # `fail_closed=True` marks a cell built
                                       # from an unreadable payload (hidden, no
                                       # raise). `principal` is the (origin,
                                       # source_id) it was COMPUTED FOR, bound
                                       # at rule 0 — see the moved-authority law
                                       # there.
    read_token: int,                   # per-user write version AT this read
)

# the restriction derivation, inside that SAME transaction:
if not store.standing_revocations(user_id):
    source_restricted = RestrictionVerdict.CLEAR   # THE NO-STANDING CASE:
                                             # zero sweep calls, a DEFINED outcome
                                             # rather than an accidental fall-through
else:
    statement = sweep(projection, d)         # ONE call, any standing `d` —
                                             # `retire` is computed against the
                                             # WHOLE standing set (`direct` tests
                                             # `... in standing` at :605-607)
    restricted = ("edge", edge_id) in statement["retire"]
```

**ONE sweep call, and the population is `retire` — NOT `affected`.** This is a
CORRECTION of the v9 wiring, verified in-source from both seats (round-2
cross-check X-1, a both-seats miss in the same class as the round-1 four-site
count: the derivation hedged "affected-or-retired" and neither seat resolved the
hedge before it was wired):

* `affected` (`:615-617`) is **scoped to the TARGET** — the source comment at
  `:609-610` says so outright: *"it answers 'what did this source contribute
  to', which is what a completeness statement about this source means."*
* The question the cap asks is different: *is this edge restricted right now,
  under the WHOLE standing set.* That is `retire`, which `:611-614` names
  literally — *"the DESIRED STATE under the whole standing set."*
* `affected` **UNDER**-restricts: `direct` (`:605-607`) tests
  `digest_of(...) in standing` — the whole set — so the simplest F2 shape, an
  edge whose OWN source is revoked, lands in `direct` and the retire fixpoint
  but reaches `affected` only if a ledger row happens to name the target. It
  also misses the transitively-condemned class outright: `reach` (`:682-683`)
  is defined as retired keys **not in** `direct ∪ affected`.
* `affected` **OVER**-restricts too: a corroborated survivor the sweep
  deliberately KEEPS is in `affected` but not `retire`, and restricting it
  would contradict the 0022 semantics this cap exists to mirror.

Because `direct` and the fixpoint already run against the whole standing set,
**one call answers the boolean** — cost is a single sweep, not one per standing
revocation. Per-digest provenance, if wanted, comes from a per-target pass and
is optional.

**Four load-bearing properties, each EXECUTED rather than reasoned** (round-3
F1 is the reason this section now says "executed": the population question was
verified twice by reading and the KEY TYPE was wrong both times):

1. **`("edge", edge_id)` FOR CORRECTNESS, not for typing.** The `retire`
   population is **HETEROGENEOUS ACROSS RECORD TYPES**. Executed against a real
   store with a revoked source:
   `retire = [('edge', 'e-083baded…'), ('episode', 'ep-e90471…')]`. So a bare
   `edge_id in retire` is ALWAYS False — the cap fails OPEN, silently, on the
   exact cell it exists to close — and a cast to match the type would be wrong
   in a second way, because an episode could carry the same id string. The
   population spanning record types FORBIDS the cast that "use typed keys"
   would invite.
2. **`retire`, not `affected`** (round-2 X-1). The same execution showed
   `affected = []` on that case: the simplest F2 shape — an edge whose OWN
   source is revoked — lands in `direct` and never in `affected`. `retire`
   (`:681`) is the DESIRED-STATE population under the whole standing set, which
   `:611-614` names; `affected` (`:609-610`) is scoped to THE TARGET.
3. **ONE sweep call**, never one per standing revocation (F6 — the ambiguity
   came from an internal design message and is killed here in the ONE
   direction): `direct` and the fixpoint already run against the whole standing
   set, so a single call answers the boolean.
4. **SHARE THE PROJECTION** — built by the SAME builder `revoke_source` uses,
   never a re-derivation; the agreement-by-coincidence hazard applies to INPUTS
   as much as functions.

**Required cases** (all in §6a): DIRECT (own-source revoked — and the cell must
also assert `affected` MISSES it, keeping X-1 as a permanent regression);
TRANSITIVE (`reach`); INACTIVE-SUPERSEDED (the original F2 cell); LIFT (the
verdict flips with no row ever rewritten); NO-STANDING (False, with **zero**
sweep calls); and BARE-ID MEMBERSHIP asserted to MISS the restricted edge —
the negative control proving the tuple is load-bearing.

**ONE CONSISTENT READ (F2): one read window, one world — the mechanism is
MODE-DEPENDENT (round-8 F3: this heading said "EXCLUSION, not a snapshot" for
one round ABOVE the passage explaining why naming either mechanism is wrong —
the round-7 fix replaced the paragraph and not its own headline).** Everything is computed inside an explicit `BEGIN`…`COMMIT` on
one connection, and — per the reviewer's option (a) — the ScopeView decision is
computed IN-transaction and carried on the cell, so the classifier consumes a
precomputed decision and never triggers a lazy ledger read. v15's claim that a
single connection gave "one world BY CONSTRUCTION" was FALSE: single-connection
≠ single-snapshot under autocommit, and a second instance interleaved between
consecutive reads produced a mixed world. **The MECHANISM is MODE-DEPENDENT and the GUARANTEE is not (round-7 F3).** v18
named exclusion as *the* mechanism and then described a SQLite snapshot forty
lines later — a contradiction, and not mode-neutral. Stated properly:

- **rollback-journal mode:** BY EXCLUSION — a SHARED lock held for the read
  window, writers refused for its duration, NOT MVCC.
- **WAL mode:** BY SNAPSHOT — the read transaction sees a consistent MVCC view;
  writers are *not* refused, they simply are not seen.

**What the classifier depends on is identical in both and is the only thing
this spec may assert:** *one read window; every read within it describes one
world.* Naming either mechanism as THE mechanism is wrong in the other mode,
which is how v18 came to contradict itself. The executable model already
distinguishes the two; the normative text now does too. Proven by forced
interleaving immediately before the scope decision, with a discriminating pair
showing the same write succeeds once the window closes.

`CurrentState` REPLACES the separate current
carrier, so there is no second current read to be stale against: row, standing
set and sweep are evaluated in ONE transaction on ONE connection — one read
window in the mode-neutral sense above, NOT "one SQLite snapshot", which was
v18's self-contradicting phrase — and the scope projection is parsed from THAT
`current_raw`. Scope,
caps and restriction are the same world BY CONSTRUCTION rather than by token
comparison. `read_token` is audit and cross-read correlation only; **no caching
is specified anywhere**, because the reviewer killed `(user, standing-set)` as a
key — the CONTRIBUTION GRAPH can move under an unchanged standing set. Every
call recomputes in its own transaction, stated here so an implementer does not
re-invent the dead cache.

**No contribution-graph traversal is specified here**, deliberately: the sweep
already performs it internally and is transitively closed by accepted rule, so
a basis-resting-on-a-revoked-source question is answered by consuming the one
computation's classification rather than by re-implementing it.

Cost is ONE sweep evaluation per lookup, not one per standing revocation, and
**nothing is cached** (round-4 C6 — these two sentences survived from v9 and
contradicted the one-sweep/no-cache rules stated above them; a stale carrier
inside the same section is the most dangerous kind, because a reader who finds
it first never reaches the correction).

**No-K degenerate case:** with no knowledge cutoff (a pure valid-time query),
`snapshot is current` and the two-state collapses to a single-state
classification — the v4 behaviour, preserved.

### 4a-iii. The adapter — an EXECUTABLE construction (round-3 F3)

The reviewer asked for a construction, not a description, because the previous
description was wrong in a way only running it would show: **`quarantined` and
`use_only` are `@property`, NOT serialized.** Executed — `Edge.model_dump_json`
yields exactly these 18 keys:

```
id, user_id, subject, relation, object, note, provenance, valid_from,
invalidated_at, invalidation_reason, supersedes, volatility, ungrounded,
needs_confirmation, times_used, outcome_counts, last_outcome, last_outcome_at
```

`quarantined` and `use_only` appear nowhere. Round-2's X-2 rule ("a missing flag
must never default — missing ⇒ MALFORMED") would therefore have refused EVERY
payload at implementation: the fix meant to embody audit-the-fix's-own-state was
itself unexecutable. The adapter exists so that never recurs by description.

```
adapt(state_text, *, expect_id, expect_user) -> Adapted | None
  1. PARSE      json → mapping with a decoder that REFUSES DUPLICATE KEYS,
                else None                              (C-1: the consumer's step)
                NOT a plain decoder. Plain JSON parsing is LAST-WINS on
                duplicates, and here that is a trust bypass, not a curiosity:
                EXECUTED against the shipped model, a payload carrying
                `"disclosure":"quarantined","disclosure":"mentionable"` parses
                to MENTIONABLE, so a QUARANTINED third-party CLAIM is
                DECLASSIFIED by the adapter itself. This is 0026's
                evidence-boundary rule and the adapter is exactly such a
                boundary — untrusted text becoming a trust decision — so the
                shipped gate refuses a plain decoder here. The hook runs PER
                OBJECT, so nested `provenance` is covered by the same
                mechanism.
  2. IDENTITY   mapping["id"]/["user_id"] must equal expect_*  (C-4), else None
  3. SCHEMA     required keys present: id, user_id, subject, relation, object,
                note, provenance, valid_from, invalidated_at,
                invalidation_reason. Missing ⇒ None. NEVER a default.
  3b. TYPES AND BOUNDS — PRESENCE IS NOT VALIDITY (round-4 F2). Every field is
                type-checked, and the identity fields carry the SHIPPED bound:
                `origin`/`source_id` are None or a str of length
                1..`IDENTITY_MAX` (512 — scope.py:96, and
                `Provenance.…: Optional[str], min_length=1, max_length=512` at
                schema.py:134-135). The reviewer fed `source_id=[]`; a
                presence-only check accepted it and the real `ScopeView` raised
                `ScopeError`. THE INVARIANT: **the adapter must never pass
                anything its consumer will raise on.**
                TYPE PRECEDES MEMBERSHIP everywhere, not only where V-NORMALIZE
                first said it: an unhashable value reaching `in`/`dict.get`
                RAISES instead of refusing. A spec rule is not confined to the
                field that motivated it.
  4. ENUMS      invalidation_reason ∈ DISPOSITIONED_REASONS ∪ {None} is NOT
                required (an unknown STRING is coherent and fences, F8b) but the
                TYPE is: non-str ⇒ None. provenance.disclosure must be a member
                of `Disclosure`; anything else ⇒ None.
  5. DERIVE     the flags, exactly as the shipped properties do (schema.py:482,
                :491) — verified in source, not recalled:
                  quarantined = (relation == QUARANTINE_RELATION)
                                 or (provenance.disclosure == QUARANTINED)
                  use_only    = (provenance.disclosure == USE_ONLY)
                NOTE the TWO disjuncts on `quarantined`: relation OR disclosure.
                A one-disjunct derivation is the natural mistake and would let a
                third-party CLAIM through whenever its disclosure was not itself
                QUARANTINED.
  6. INCOMPLETE PROVENANCE is a real shape ⇒ None. The authority for WHICH
     provenance fields the SCOPE PATH reads is `MembershipResolver._record_shape`
     (scope_read.py:170-176), INTROSPECTED rather than restated: it reads
     {author_of_evidence, origin, source_id, evidence_ref} and `record.lineage`.
     **RETRACTION (round-4 F3):** v15 claimed `disclosure` belongs to that set.
     It does NOT — executed, `_record_shape` returns exactly
     `{author, evidence_ref, lineage, origin, source_id}`. The verdict's
     original list was right and this spec's "correction" was wrong: the author
     ran the function, read its five-key output, and still wrote the opposite,
     because they answered what the ADAPTER needs (`disclosure`, for flag
     derivation) instead of what the SHAPE PATH reads. The adapter needs BOTH
     sets; they are different sets and conflating them is the error. Note also
     that the shape's KEY vocabulary differs from the provenance FIELD names
     (`"author"` ← `author_of_evidence`), so output-introspection alone is
     insufficient and the translation is stated explicitly in the model. `author_of_evidence` must be carried as the REAL `EvidenceAuthor`
     ENUM, because `_record_shape` accesses `.value` on it: a string stand-in
     passes hand-written tests and raises against the live `ScopeView`. These
     fields FEED THE SCOPE DECISION, so defaulting a missing one does not fail
     loudly — it silently manufactures a scope decision from a field that was
     never there. The adapter is exercised against the REAL `ScopeView`,
     including this case.
```

`None` is the single failure value; the CALLER maps it to `MALFORMED` or, on the
current leg before visibility is established, to `SCOPE_HIDDEN` (V-FAILHIDDEN).

### 4a-ii. The reason × cutoff matrix (F2's required ruling)

The axis that matters is **when the invalidation was RECORDED relative to K** —
because that decides whether it is in the `snapshot` (and so shapes what we
*believed at K*) or only in `current` (and so acts purely as a cap on what we
may assert *now*). `T` must lie in the snapshot's interval throughout, else
`NOT_VALID_AT_T`.

| reason | recorded BEFORE K → in `snapshot` | recorded AFTER K → only in `current` |
|---|---|---|
| **superseded** | `held=True` → **GROUNDED** (it was the held value at T) | `held=True`; cap allows → **GROUNDED** |
| **lapsed / decayed** | `held=True` → **GROUNDED** | `held=True`; cap allows → **GROUNDED** + `stale-at-recall` if already lapsed at `now` |
| **absorbed_duplicate** | `held=True` → **GROUNDED** (0028 resolves to the absorber) | `held=True`; cap allows → **GROUNDED** |
| **corrected** | `held=False` (at K we already knew it was an error) → **FENCED_AS_OF** | **`held=True`, status=FENCED_AS_OF** — *the F2 headline case*: we honestly believed it at K, and equally honestly refuse to assert it now |
| **disputed** | `held=False` → **FENCED_AS_OF** | `held=True`, status **FENCED_AS_OF** |
| **revoked_source** | `held=False` → **EXCLUDED** | `held=True`, status **EXCLUDED** — 0022 non-revival is absolute and never time-travels away |
| **unknown / 8th** | `held=False` (default FENCED, F6) → **FENCED_AS_OF** | `held=True`; cap defaults FENCED → **FENCED_AS_OF** |

**The asymmetry is the point.** `corrected`/`disputed`/`revoked_source` recorded
*before* K mean we already knew better at K (`held=False`); recorded *after* K
they leave `held=True` but cap the present. Reporting both truthfully is exactly
what "separate the store held this belief at K from this may be asserted as fact
now" requires — and it is why one boolean could never carry it.

*(This matrix supplies joint acceptance scenarios 2 — revocation→reinstatement
with K between — and 7 — a later correction/dispute/revocation applied to an
earlier snapshot.)*
Three structural corrections from round 1:
- **State coherence is rule 0** (finding 2). `active` is derived solely from
  `invalidated_at is None`; the schema does NOT couple it to `invalidation_reason`
  (`schema.py:479` vs `:432`, no validator), so `add_edge` can persist an ACTIVE
  edge carrying `reason="corrected"`. The old active-branch shortcut (`if
  invalidated_at is None: return True`) would have grounded it. Rule 0 refuses
  every incoherent shape (active+reason, inactive+no-reason, non-STRING
  reason — an unknown STRING reason is not malformed, it fences (F6), inverted interval) as `MALFORMED` — never grounded.
- **Scope uses the TIME-RELATIVE verdict** (finding 1), fed through
  `gate.scoped_assertable(base_groundable, view.decision(edge))`. v2 called
  `view.shape()`, which first checks today's `record.assertable` — False for
  every historical edge — and returns it UNCHANGED, so a cross-scope
  `superseded` edge kept `MENTIONABLE` and grounded. The as-of verdict must go
  through the scoped relation directly (or a shaping method that accepts it), not
  the shipped `shape()`.
- **`classify_as_of` is authoritative; `assertable_as_of` is derived from it**
  (finding 2), so the two can never disagree — an active `revoked_source` edge is
  `MALFORMED` (rule 0), so both return non-grounded consistently.

**Safety is order-independent:** rules 0/3/`FENCED_AS_OF` are all non-grounding,
so `MALFORMED`/`revoked`/`disputed`/`corrected`/quarantined/use_only/restricted
never reach `GROUNDED_AS_OF` under any ordering (V-NEVER); precedence only fixes
the reported status.


**Footnote (round-2 X-6).** The BEFORE-K `revoked_source → EXCLUDED` cell
assumes the revocation STANDS at classification time. After a LIFT the code
path yields `FENCED_AS_OF`, not `EXCLUDED`: `held` is already False from the
snapshot's own reason, and rule 7's restriction input is now clear. The matrix
describes the standing case; this footnote prevents a matrix-vs-code finding.


**ROUND-3 F5 — every post-K GROUNDED cell in this matrix is CONDITIONAL.** The
matrix is a round-1 carrier and rule 8 obsoleted its unconditional readings: a
cell showing `GROUNDED_AS_OF` after K now additionally requires that the CURRENT
interval contains `T`, that snapshot and current are SEMANTICALLY IDENTICAL by
digest, and that the remaining current caps pass. Read every `GROUNDED` entry
below as "groundable, subject to rule 8's subtraction" — the matrix answers the
REASON question only, and no longer decides a verdict by itself.

### 4b. The reason → historical-truth disposition (closed, total, fail-closed)
| reason | `DISPOSITIONED_REASONS` (current) | 0030 historical-truth | rationale |
|---|---|---|---|
| **superseded** | drop | **GROUNDABLE-as-of-T** | was validly true until it changed (the headline case) |
| **lapsed** | retain | **GROUNDABLE** (flag `stale-at-recall`) | staleness is not falsity — it was our true belief then |
| **decayed** | retain | **GROUNDABLE** (flag `stale-at-recall`) | low-confidence-now is not was-false |
| **absorbed_duplicate** | retain | **GROUNDABLE** (0028 resolves to the absorber) | was a true value. CANONICAL absorption yields an empty interval (`graph.py:463,478` — `invalidated_at = min(incoming,prior) ≤ valid_from`), so those never reach the disposition (time-validity fails first). But the GENERIC invalidation/insertion paths can persist a NON-empty interval carrying `absorbed_duplicate` (finding 4), and a classifier seeing only an `Edge` cannot prove canonicity — so it must NOT rely on unreachability. It classes GROUNDABLE (the value was true at T) and lets 0028 resolve to the absorber; §6a exercises the non-empty-interval case, not an unreachable assertion (v2's D-2 over-generalized from canonical-only) |
| **corrected** | drop | **NEVER** | retroactively false — it was an error, replaced (0028 resolves to the corrector) |
| **disputed** | drop | **NEVER** (FENCED_AS_OF) | the host revoked trust; contested at any T |
| **revoked_source** | drop | **NEVER** (EXCLUDED) | withdrawn evidence — 0022 non-revival; not even fenced |
| **(any unknown 8th)** | drops | **NEVER** (fail-closed) | defaults to FENCED in the total `AS_OF_DISPOSITION` (missing key) |

### 4c. Scope composition — assertable-to-WHOM at T (0028 R1-5, finding 1)
`classify_as_of` takes `view` directly (F8.6 — v4 called it "principal-agnostic" while its own signature accepted a view). Scope composes with
0020's `ScopeView` (`scope_read.py`) — but **NOT via the shipped `view.shape()`**.
`shape()` short-circuits on today's assertability (`_asserted_today(record) =
bool(record.assertable)`, `scope_read.py:58,381`), which is False for EVERY
historical (inactive) edge, so `shape()` returns a historical edge UNCHANGED and
never demotes it. v2 relied on that demotion; it does not happen. A cross-scope
`superseded` edge would keep `MENTIONABLE` and ground — V-SCOPE false.
- **Correct composition:** feed the TIME-RELATIVE base verdict through the gate's
  scoped relation — `gate.scoped_assertable(base_groundable, view.decision(edge))`
  (§4a rule 5). The `view.decision(edge)` cell (CROSS_VISIBLE etc.) is the same
  authority `shape()` consults; passing it the AS-OF verdict instead of today's
  gives the correct per-principal answer for historical material.
- Equivalently, 0030 may add a `shape_as_of(edge, verdict)` that carries the
  restrict-only demotion onto a historical edge given its time-relative verdict —
  a small addition to 0020's surface — but calling the existing `shape()` is
  insufficient.
- `view.visible(edge)` still gates first (a cross-hidden historical edge is
  `SCOPE_HIDDEN` at every T). Scope is applied per edge, not per interval.

### 4d. Rendering channel (informative — 0028 owns the query render)
A `GROUNDED_AS_OF` historical edge is assertable, but it is HISTORY, not the
current value. 0028 v2 renders it in a labelled as-of channel carrying its
resolution provenance (`valid_from`, `invalidated_at`, `invalidation_reason`),
distinct from the current grounded block, so a reader never mistakes a
groundable-as-of historical fact for the current one. 0030 supplies the
classification; the channel is 0028's.

### 4e. Relationship to the current classifier — the two divergence cells (D-1)
`assertable_as_of(edge, now)` and `Edge.assertable` agree for the ordinary edge,
and diverge on exactly two cells where **valid-time and current-ness genuinely
differ**. Both are reachable in the shipped store, and in BOTH `assertable_as_of`
gives the temporally-correct answer. Neither changes the current recall path
(which never calls `assertable_as_of`).

| cell | `Edge.assertable` | `assertable_as_of(now)` | which is right, and why |
|---|---|---|---|
| **future `valid_from`** (`valid_from > now`, active) | True (active) | **False** | as-of is STRICTER and correct — a not-yet-valid fact is not assertable now |
| **future `invalidated_at`** (`valid_from ≤ now < invalidated_at`, groundable reason) | False (`active` is False once `invalidated_at` is set) | **True** | as-of is LESS strict and correct — the value is STILL validly held now; its successor's `valid_from` is in the future (`graph.py:362` sets `prior.invalidated_at = replacement.valid_from`, which is caller-suppliable), so the prior IS the true-now value |

The future-`invalidated_at` cell is the load-bearing one: it shows the current
classifier UNDER-asserts (fences a still-true value merely because `invalidated_at`
is set at all), and `assertable_as_of` corrects that — for the as-of path ONLY.
**Ruling (this spec):** `assertable_as_of` is authoritative on valid-time; both
divergences are intended, tested (§6a adds the future-`invalidated_at` T-position),
and confined to the as-of path. 0030 does NOT change what the current classifier
does with either cell (that is a 0019 question left untouched).

## 5. Regime analysis
- **Active edge, T = now, `valid_from ≤ now < any invalidated_at`:**
  `assertable_as_of == Edge.assertable` (V-CURRENT-UNCHANGED) — 0030 agrees on the
  present.
- **The two divergence cells** (future `valid_from`, future `invalidated_at`):
  see §4e — as-of is the correct one in both, current path unchanged.
- **Historical edge, groundable reason, T in interval:** `GROUNDED_AS_OF` — the
  new capability.
- **Historical edge, never-groundable reason, any T:** `FENCED_AS_OF` /
  `EXCLUDED` — the trust exclusion the whole spec protects.
- **T outside every interval:** `NOT_VALID_AT_T` — truthful gap (0028 handles the
  gap semantics; 0030 just reports it).

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **V-NEVER** never grounds a trust-excluded record at ANY T: for every edge whose reason ∈ {corrected, disputed, revoked_source} OR class ∈ {quarantined, use_only}, `classify_as_of` never returns `GROUNDED_AS_OF` for any sampled T (incl. inside the interval + boundaries) | `test_never_grounds_excluded_at_any_t` | CI |
| **V-MALFORMED** (finding 2, F6, **B-2**) STRUCTURE only, applied to **BOTH** `snapshot` AND `current` — the cap must never read an incoherent state (v6 checked only the snapshot, so an ACTIVE current carrying `revoked_source` EXCLUDED at rule 6 while the same shape carrying `corrected` sailed past the cap: two incoherent shapes, two outcomes, neither deliberate): an ACTIVE edge with a non-`None` reason, an INACTIVE edge with `None` reason, a **non-STRING** reason (type-checked BEFORE any membership test — an unhashable value must never reach `in`), or an INVERTED interval (`invalidated_at < valid_from`) → `MALFORMED`. An **unknown-but-string** reason is NOT malformed → `FENCED` (F6's ruling; the default lookup is reachable). An EMPTY interval (`==`) is coherent → `NOT_VALID_AT_T`. Asserted with edges built via `add_edge` (which does not couple the fields) | `test_incoherent_states_are_malformed_never_grounded` | CI |
| **V-TWO-STATE** (F2) `held_at_K` is computed from `snapshot` ALONE; `status` additionally applies CURRENT caps, which only ever SUBTRACT. The headline cell: a record corrected/disputed/revoked AFTER K returns `held_at_K=True` with `status` `FENCED_AS_OF`/`EXCLUDED` — we report that we believed it then AND refuse to assert it now. `revoked_source` current → `EXCLUDED` at every K (0022 non-revival never time-travels away). No current cap can RAISE a verdict | `test_two_state_current_caps_subtract_only` | CI |
| **V-NORMALIZE** (F6 + **B-1**) type and datetime normalization precede every membership test and comparison **on BOTH legs**: a non-string (incl. unhashable) reason on EITHER `snapshot` or `current` returns `MALFORMED` without reaching `in`/`dict.get`; every timestamp from EITHER state is UTC-coerced inside rule 2's guard — including `current.invalidated_at`, which v6 normalized on the final line, outside the guard, so garbage there raised uncaught at the end of an otherwise-green classification | `test_normalization_covers_both_states` | CI |
| **V-FAILCLOSED** (finding 3) `AS_OF_DISPOSITION` is a TOTAL dict; `set(AS_OF_DISPOSITION) == set(DISPOSITIONED_REASONS)` exactly (build fails on any undispositioned reason in EITHER); runtime defaults an unknown/missing key to `FENCED` | `test_as_of_disposition_is_total_and_failclosed` | CI |
| **V-CURRENT-UNCHANGED** (finding 7) `Edge.assertable` is not modified; the current recall path does not call the as-of classifier — proven via a caller-grep AND the current path run against the **post-0027** frozen classification oracle (the baseline is pinned to the post-0027 implementation commit, §Spec-Requires — NOT `d7bf16b`, which predates 0027's v10 oracle). `classify_as_of(...,now).status==GROUNDED_AS_OF` agrees with `edge.assertable` for the ordinary edge and diverges on EXACTLY the two §4e state cells | `test_current_path_oracle_identical_post0027` + `test_as_of_now_diverges_only_on_two_cells` | CI |
| **V-INTERVAL** groundable only within the half-open `[valid_from, invalidated_at)`; `T == invalidated_at` excluded (successor's); UTC-aware comparison only (§10) | `test_half_open_interval_boundaries` | CI |
| **V-SCOPE** (finding 1 + F2 + F7) visibility is the **OUTERMOST** gate — evaluated before normalization, coherence and time — so a hidden record returns ONLY `SCOPE_HIDDEN` (never `MALFORMED`, never `held_at_K`), leaking neither existence nor condition. Shaping then composes via `gate.scoped_assertable` on the TIME-RELATIVE verdict, NEVER `view.shape()`. **CURRENT scope governs every answer including historical ones** (0029 versions edge state, not scope policy/membership). Fixtures: (a) cross-scope-visible `superseded` grounds unscoped, `FENCED_AS_OF` for the restricted principal; (b) **hidden + malformed → `SCOPE_HIDDEN` only** (joint scenario 8) | `test_scope_outermost_hidden_never_leaks` + `test_scope_composes_via_time_relative_verdict_not_shape` | CI |
| **V-STALE** (finding 5, m-2) `classify_as_of` returns `Result{status, flags}`; **on a `GROUNDED_AS_OF` result** `stale-at-recall` is set iff reason ∈ {lapsed,decayed} AND `invalidated_at <= now` (already stale). **Round-2 F8b:** the "iff" is SCOPED to grounded results — every earlier non-grounded return omits the flag by construction, so an unscoped "iff" was false of those paths — a future-lapsing edge (invalidated_at > now) grounds WITHOUT the flag; `now` is thereby load-bearing (an external reviewer greps for the unread param) | `test_result_carries_stale_flag` | CI |
| **V-BIND** (round-2 F4; C7; round-8 F1) `snapshot_raw`, `current_state`, the envelope AND THE SCOPE-CELL/VIEW PAIR must cohere — shared `id`/`user_id`; cell present iff view present; principals PRESENT on both sides AND equal — checked BEFORE visibility, the guard before the dereference | `test_six_leg_binding__with_its_control` + `test_viewless_cell_is_refused__with_its_control` (round-8: this row cited `test_legs_are_identity_bound_before_anything`, which existed NOWHERE in either driver — a phantom citation in the row that polices binding, the grep-fails class in the invariant table itself) |
| **V-WINDOW** one read window, one world, in BOTH journal modes — exclusion under rollback-journal, snapshot under WAL; the invariant names the guarantee and neither mechanism | `test_transactional_read_is_one_world__both_journal_modes` |
| **V-CARRIER-AGREES** (round-2 C-4) the payload's embedded `id`/`user_id` must equal the carrier's ROW-sourced identity, checked AT THE PARSE on both legs. C-2 made the row authoritative and rightly stopped deriving identity from the payload — leaving the carrier's OWN two halves unbound. A payload carrying edge B's content under edge A's row would classify B under A, and on the current leg B's SCOPE FIELDS would decide A's visibility: F4's borrowing escalation re-entering through the carrier. Current-leg disagreement takes V-FAILHIDDEN's branch (the visibility decision must not consume it); snapshot-leg → `MALFORMED` | `test_payload_identity_must_match_the_row` | CI |
| **V-PARSE** (round-2 C-1) `RawEdgeState.state` is TEXT and PARSING IS THE CONSUMER'S — 0029 promises byte fidelity only (V-VERBATIM), so a parse failure is a consumer-CLASSIFIED outcome, never a 0029 read error. Unparseable CURRENT text shares V-FAILHIDDEN's branch (SCOPE_HIDDEN with a view, MALFORMED without); unparseable SNAPSHOT text → MALFORMED. Parse failure and field-validation failure share outcomes because they share ORIGINS — a payload written by a model that no longer exists fails in both ways | `test_unparseable_payloads_are_classified_not_raised` | CI |
| **V-COLUMN-NOT-INPUT** (round-2 C-3) the event `reason` COLUMN records the EVENT's reason and is NEVER a classifier input; the state's own `invalidation_reason` lives INSIDE the payload. A `baseline` event carries `reason=NULL` even when the found state was inactive — wiring the column would silently misclassify every migrated inactive edge | `test_classifier_never_reads_the_event_reason_column` | CI |
| **V-EXTRACT** (round-2 X-2) EVERY field the rules read — content {subject, relation, object, note} and flags {quarantined, use_only}, on BOTH legs — is defensively extracted before use; missing or unreadable ⇒ `MALFORMED`/`SCOPE_HIDDEN`, **never a default**. A defaulted-False flag would GRANT, failing open on exactly the fields that carry content trust; a missing `subject` would RAISE at the digest, falsifying §6a(8)'s no-raise promise. V-RAW's fix must itself hold V-RAW's discipline | `test_missing_raw_fields_never_default` | CI |
| **V-RAW** (round-2 F5) the classifier consumes RAW carriers, not `Edge` — the shipped Pydantic deserializer rejects malformed reasons/timestamps before any classifier could run, so a typed carrier made "journal malformed state, then classify it" unimplementable. 0029 records; **ALL validation is 0030's** (seam S4). **Naming, deliberately split:** this is the CONSUMPTION half; 0029 mints **V-VERBATIM** for the read-surface half. Two specs defining one name differently would be its own finding, so the pair is tied by the seam manifest rather than by a shared symbol. Asserted through the REAL load path, both hidden and visible | `test_malformed_state_traverses_the_raw_carrier` | CI |
| **V-TRUST-INPUT** (round-2 F2) the current source-restriction cap reads a DEDICATED input derived from standing source state + the contribution graph, NEVER `current.invalidation_reason`. Verified in-source: `revocation_sweep.py:734` emits `retire` only `if r["active"] and not want_active`, so an already-inactive `superseded` edge keeps that reason while its source stands revoked — and as-of queries are BY DEFINITION about inactive edges  Derivation is the THIRD caller of `sweep` (the one computation) consuming `statement["retire"]` (`:681`, the DESIRED STATE under the whole standing set), NOT `affected` (target-scoped) and NOT the effect list — testing effects reproduces the blind spot at one remove. Free cell: restrict → LIFT flips the input with no row ever rewritten | `test_restricted_source_excludes_via_standing_state_not_row` + `test_lift_flips_the_trust_input_without_touching_the_row` | CI |
| **V-SUBTRACT** (round-2 F3) the current leg subtracts on VALID-TIME and SEMANTIC IDENTITY, not only reason/disclosure: `T` must fall in the CURRENT interval too, and a same-id content change (digest) fences the old snapshot. Headline cells: snapshot `[Jan, ∞)` superseded effective Feb, `T` in Mar → `FENCED_AS_OF` not `GROUNDED`; same-id semantic replacement after K → `FENCED_AS_OF`. Neither is `EXCLUDED` — the belief WAS genuinely held at K | `test_current_projection_subtracts_on_time_and_identity` | CI |
| **V-NORM-TOTAL** (round-2 F7) normalization is TOTAL over required inputs: `T`, `now` and BOTH `valid_from` use `as_utc_required`; only `invalidated_at` uses `as_utc_optional`. `as_utc(None) -> None` previously let `T=None` reach an invalid comparison, `now=None` fail only on the stale branch, and `current.valid_from=None` pass coherence while current was active | `test_required_and_optional_normalizers_are_separate` | CI |
| **V-FAILHIDDEN** (round-2 F4/F5 composition, narrowed by X-4) when the minimal scope projection cannot be read AND a `view` is present the result is `SCOPE_HIDDEN`, NEVER `MALFORMED`; with **no view there is no principal to protect**, so the result is `MALFORMED` — we cannot prove the principal may see the record, so we must not reveal even that it is malformed; `MALFORMED` there would reintroduce v3's leak by a new route | `test_unreadable_scope_fails_closed_to_hidden` | CI |
| **V-ADDITIVE** 0030 adds no field to `Edge`; the classifier is a pure function of its carrier inputs + the registry + `(T, now, view)` (round-4 C7: the input list was pre-carrier) | `test_no_edge_field_added` | CI |

### 6a. Acceptance measurement — REQUIRED, FINITE
A **correctness gate (100%, not a quality metric)** — as 0028's §6a is. NOT a
naive Cartesian product (finding 6): a product omits well-formed active
(`reason=None`), and crossing every reason with the future-time cells makes
incoherent/non-divergent cases (the two divergence cells are STATE SHAPES, not
extra `T` positions). Instead, explicit **STATE FAMILIES**, each × a **T-position
sweep** {before, at `valid_from`, mid-interval, at `invalidated_at` (excluded),
after} × a **principal sweep** {self/unscoped, in-scope, cross-scope-visible,
cross-hidden}, with the expected `Result{status, flags}`:
1. **well-formed active** (`invalidated_at=None`, `reason=None`) — the ordinary
   present case (was omitted);
2. **well-formed inactive**, one family per reason (all seven), content classes
   {grounded, quarantined, use_only};
3. the **two future-time divergence states** — future `valid_from`, future
   `invalidated_at` — as the now-vs-current comparison (needs `now` distinct from
   `T`);
3b. **ROUND-2 REQUIRED CASES** — the reviewer's new joint set, 0030's share
   (0029 owns the epoch-baseline and concurrent-txn-allocation cells):
   * a **superseded edge whose source later becomes restricted** — the F2 cell.
     Expected `EXCLUDED`, driven from the standing-state input, and it MUST fail
     if the classifier reads `current.invalidation_reason` instead (which still
     says `superseded`);
   * a **snapshot open at `K`, later superseded, with `T` after the current
     interval** — F3(a). Expected `FENCED_AS_OF`, `held_at_K=True`; v7 returned
     `GROUNDED_AS_OF` here;
   * a **same-ID semantic replacement after `K`** — F3(b). Expected
     `FENCED_AS_OF`, `held_at_K=True`, current still ACTIVE;
   * **mismatched snapshot/current identities** — F4, three fixtures:
     mismatched id, mismatched user, mismatched view. Expected
     `IDENTITY_UNBOUND` and, critically, evaluated BEFORE visibility so the
     mismatched-view fixture cannot borrow B's scope decision;
   * **payload/row identity DISAGREEMENT** (round-2 C-4), both legs: a payload
     carrying another edge's content under this row. Current leg → the
     V-FAILHIDDEN branch (`SCOPE_HIDDEN` with a view, `MALFORMED` without);
     snapshot leg → `MALFORMED`. The current-leg cell must assert that the
     FOREIGN payload's scope fields never reached the visibility decision.
   * **unparseable payload TEXT** (round-2 C-1), three cells: unparseable
     CURRENT with a view → `SCOPE_HIDDEN`; unparseable CURRENT with no view →
     `MALFORMED`; unparseable SNAPSHOT → `MALFORMED`. All three must bind
     successfully FIRST (row-sourced identity, C-2), which is what proves the
     parse failure is classified rather than mistaken for an identity fault.
   * **malformed persisted state through the REAL load path**, hidden and
     visible — F5. The visible case expects `MALFORMED`; the hidden case
     expects `SCOPE_HIDDEN` only (V-FAILHIDDEN), and this is the case the typed
     carrier made unreachable.
     **How the malformed state gets there, stated so "real load path" is not
     misread as "the store can write garbage"** (dev's fixture-design note): the
     store serializes only VALID edges, so malformed persisted state has exactly
     two honest origins — (a) an append-only journal OUTLIVING THE MODEL THAT
     WROTE IT, i.e. a then-valid shape that a later model version no longer
     accepts, which is 0029's own structural justification for the verbatim
     carrier and therefore the SAME fact seen from the consumer side; or (b)
     DB-level tamper. The fixture must use one of those and say which. It must
     NOT be built by making the store emit an invalid edge, because it cannot,
     and a fixture that pretended otherwise would test a path that does not
     exist while appearing to test the one that does.
4. **incoherent states** (V-MALFORMED): active+reason, inactive+no-reason,
   non-string reason, inverted interval. **Round-4 C8 — WALKED AND CONFIRMED,
   not a reviewer misread:** this family previously ALSO listed the unknown
   "eighth" reason and the EMPTY interval, both of which V-MALFORMED rules the
   other way (unknown-but-string ⇒ coherent, `FENCED`; empty `ia == vf` ⇒
   coherent, `NOT_VALID_AT_T`). Both halves were genuine drift, so both are
   removed here rather than defended; they now appear in families 2 and 3 where
   their real outcomes live;
5. **scoped variants** over families 1-3 (esp. the finding-1 cross-scope
   `superseded` case: grounds unscoped, `FENCED_AS_OF` for the restricted
   principal);
6. **`lapsed`/`decayed`** asserting the `stale-at-recall` flag against `now`.
7. **JOINT acceptance scenarios (shared with 0029).** The reviewer's eight
   scenarios become the SHARED §6a corpus across both specs — dev seeds them
   0029-side, and the §4a-ii reason×cutoff matrix supplies the 0030 expectations
   for the two-state cells. 0030 owns exact outcomes for:
   - **(2)** source revocation followed by reinstatement, `K` between them —
     current `revoked_source` → `EXCLUDED` at every K; after reinstatement the
     CURRENT row no longer carries it, so the cap lifts (the snapshot at K is
     unchanged: `held_at_K` is stable while `status` moves — precisely the
     two-state split);
   - **(7)** a later correction/dispute/revocation applied to an earlier
     snapshot → `held_at_K=True`, `status` `FENCED_AS_OF`/`EXCLUDED`;
   - **(8)** a malformed edge hidden from the querying principal →
     `SCOPE_HIDDEN` ONLY (F7). **The malformed axis now has TWO states to be
     malformed in (B-1/B-2):** the family crosses {snapshot malformed, current
     malformed, both} × {unhashable reason, non-datetime, active+reason,
     inactive+no-reason, inverted interval} × {hidden, visible} — asserting
     `MALFORMED` for visible incoherence on EITHER leg, `SCOPE_HIDDEN` when
     hidden, and NO raise anywhere;
   and consumes 0029's outcomes for (1), (3), (4), (5), (6) as snapshot inputs.

Pass = **100% match**. Corpus frozen + portable builder (`--check`) + digest
recorded in `## Review closure` before implementation (0028 R1-6/R1-7 pattern).

## 7. Failure modes and reversibility
- **Fully additive / reversible:** 0030 adds a predicate; removing it restores
  today exactly (`Edge.assertable` never changed). No migration, no schema
  change, no data rewrite.
- **New-reason safety:** a producer's new reason fails the totality test until
  dispositioned; until then the runtime default fences it. **Correction (F8.4):
  the registry is NOT narrow-only** — re-dispositioning a reason to `GROUNDABLE`
  plainly widens what grounds, and v4 claimed otherwise. What IS guaranteed:
  (a) TOTALITY — the build fails on any undispositioned reason, so a widening is
  always an explicit, reviewed edit, never a silent default; and (b) the runtime
  lookup defaults UNKNOWN to `FENCED`, so drift can only fence. Widening is
  possible but never accidental.

## 8. Claims and limits
- **Claim:** 0030 lets history be asserted *when and only when* it was validly,
  trustworthily true at T — a strictly-additive trust surface that never relaxes
  a current exclusion and fails closed on the unknown. *Limit:* valid-time only;
  the transaction axis is 0029; the query/resolution/render is 0028 v2.
- **Position:** no surveyed competitor classifies historical assertability by a
  reason-carrying, fail-closed registry — the field's as-of (where it exists) is
  interval math with no trust axis (0028 design §5). This is the trust-native
  piece Quentin prioritised (0030-first) precisely because it is the part no one
  else can copy.

## 9. Brief for the external reviewer

**Two motivating facts, measured after v7 was sealed, banked for this fold.**

*The shipped classifier really does assert a not-yet-true fact.* `Edge.assertable`
(`active and not quarantined and not use_only`) consults NO time predicate, so an
edge whose `valid_from` has not arrived is assertable anyway. Measured live
(research harness Tier 7 / S2, model-free, Bedrock): written 2026-08-31 with
`date` inside `MAX_FUTURE_SKEW` (1 day), `valid_from` 2026-09-01, `assertable`
True — and the window is agent-reachable, since `date` is a parameter on the MCP
`remember` tool. This is §5's future-`valid_from` divergence cell, now MEASURED
rather than reasoned. The machinery to refuse it exists ONLY in the as-of
classifier: 0030 does not change the current recall path (V-CURRENT-UNCHANGED),
and whether it SHOULD is the 0019 question this spec deliberately leaves open.

*F6's input normalization is not defensive coding against a state that never
occurs.* The shipped revocation path puts a `str` into a `datetime` field:
`revoke_source(at: str)` assigns its ISO string to `invalidated_at`/`retired_at`,
which Pydantic tolerates with a serializer warning (`schema.py:454`) and re-reads
normalise, so nothing is corrupted — but a non-datetime `invalidated_at` reaches
a classifier on an ORDINARY path, which is exactly what `as_utc_required` /
`as_utc_optional` and the MALFORMED branch are for. Round-2 F5 sharpens the same
point from the other side: the typed carrier meant such a state could never reach
the classifier at all.

Attack hardest:
1. **The fail-closed derivation.** Is `AS_OF_DISPOSITION` (total dict + key-equality) genuinely airtight —
   can any path (a new reason, a `None` reason on an inactive edge, a race
   between `invalidated_at` and `invalidation_reason` being set) let a
   non-allow-set edge ground? The registry-totality test is the guard; break it.
2. **Decoupling assertable from active.** Does removing the `active` requirement
   open ANY laundering path for corrected/disputed/revoked/quarantined/use_only
   at some T (especially at interval boundaries, or for an edge that is both
   historical AND quarantined)?
3. **Scope composition, two-state (F2 + F7).** Visibility is now the OUTERMOST
   gate and CURRENT scope governs every answer, including historical ones
   (0029 versions edge state, not scope policy). Attack that: can a cross-scope
   historical edge ground for the wrong principal via `gate.scoped_assertable`
   on the time-relative verdict? Does anything about a hidden record leak —
   existence, malformedness, or `held_at_K`? And is "current scope governs the
   past" the right ruling, or does it mis-answer "who could see this at K?"
4. **The 0030/0028/0029 boundary.** Is "0030 classifies, 0028 resolves, 0029
   carries transaction time" a clean cut, or does classification secretly need
   resolution (e.g. does classifying an `absorbed_duplicate` groundable require
   knowing the absorber exists)?

## 10. Open questions
- **`disputed` at T — fenced vs excluded.** 0030 classes it `FENCED_AS_OF`
  (rendered, never asserted); 0028 R1-3 leaned "fence-and-return". `revoked_source`
  is stronger (`EXCLUDED`, not even fenced — 0022 non-revival). Confirm the
  fenced/excluded boundary with the gate-owner (the disputed→non-assertable
  ruling that 0028 also carries).
- **`absorbed_duplicate` — UN-RETIRED (F8.3).** v2 retired this as "unreachable
  by the empty-interval construction"; round-1 finding 4 overturned that (the
  GENERIC invalidation paths can persist a NON-empty absorbed interval, and a
  classifier seeing only an edge cannot prove canonicity). §4b now classes it
  **GROUNDABLE and exercises the non-empty case**; this entry contradicted §4b
  and is corrected rather than left as a stale retirement. The live question is
  the narrow one: 0030 grounds the absorbed edge and 0028 resolves to the
  absorber — or should only the absorber ever ground? (Leaning: as specified;
  reviewer to rule.)
- **Boundary instant `T == invalidated_at`.** Half-open interval excludes it
  (successor's). Confirm this matches 0003's supersession boundary exactly (no
  gap, no overlap).

## Review closure
*n/a — draft; the frozen §6a manifest digest + the registry-totality evidence
land here before `accepted`. Entry into external review on Quentin's word.*
