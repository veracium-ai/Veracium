# Feature spec: degradation visibility — what a caller and an operator learn when veracium degrades instead of failing

Spec-Status: accepted

*Candidate authored by dev (veracium-69), 2026-09-07, on the owner's word ("Get a spec
number and write that up"), from the owner's question during testing: if an error occurs
during our use, do we know about it? Number 0039 taken from the registry
(`specs/allocation.py --next`). Every claim in §1 is a line in the tree at the commit this
draft was written against; the reviewer can open each one.*

| | |
|---|---|
| **Author / session** | dev (veracium-69) |
| **Version** | **v16 — ROUND-5 EXTERNAL VERDICT FOLDED: RETURN for amendment, two blocking findings, both REPRODUCED by both seats at the pin before a line moved (verdict body sha16 `3e4384e0b1f0ea69`).** The reviewer's dispositions: the bare-array normalization ACCEPTABLE; the uniform non-list rule ACCEPTABLE as a disclosed behaviour change; the ordering re-instancing REASONABLE once the deferred cases are covered; the `unparseable` widening NOT acceptable until semantics and coverage agree. **R5-1** — v15's narrow fix marked the two carrier branches and called them the whole class; an all-invalid list stayed silent and the flag fired on a rejected answer whose triples were usable. FOLDED as `0025` v18 on the owner's word (*"Go with the new field"*): the outcome rides a new bool, `extraction_unusable`, present on every path; `unparseable` is narrow again. **That moves V-RESULT-UNCHANGED for the CLEAN path too** (a key added to a good result, additively) — and the round's lesson, in research's words, is that a key-set invariant staying green under the alternative would have told nobody whether hosts were affected. **R5-2** — `member_skipped` and `volatility_defaulted` were emitted AFTER the storage loop, so a store failure inside it took the promised record with it (error only): V-DEGRADE-RECORDED's one-per-occurrence was ZERO on that path, and the re-instanced V-RECORD-ORDER-ON-ERROR covered only the early-emitted retry site. FOLDED as code and tests: every degrade record is computed and emitted BEFORE the first effectful store operation — the volatility coercion as a pure pre-pass (the one continuing handler, moved, not duplicated; the census still counts three), and the episode write moved below the emissions, since it was the first write and the primary record sat after it (a variant the reviewer did not test). Tests at BOTH seams for all three kinds. **The round's other lesson, kept here so it is not lost:** dev's and research's answer-shape instruments vary ONE axis — the provider's answer — and neither perturbs the store; independent authorship did not buy independent coverage, and the reviewer varied an axis neither seat had. Axes never varied by this spec's evidence: store failure (now, at two seams), clock, concurrency. *Prior:* **v15 — POST-ACCEPTANCE AMENDMENT: A FOURTH FROZEN STRUCTURE MOVES, AND THIS ONE PAYS BACK WHAT v14's DID (Quentin's word, dev session, 2026-09-10: *"Go with the narrow fix"*).** Research read v14's wider normalization rule against **this spec's own accepted §8** and found the sentence *"A host that passes `diagnostics=None` learns nothing new"* no longer true — such a host learned nothing new AND lost the raise it had. **Measured by both seats independently: with no reporter, `{"triples": null}` returned a dict BYTE-IDENTICAL to a legitimately empty extraction**, which is §1a's founding indistinguishability reproduced on the primary path by this spec's own implementation. `0025` §4c is amended (its v17): the ingest result now carries `unparseable: True` when the primary answer yielded no usable `triples`. **What that moves here: V-RESULT-UNCHANGED**, which pins the result's key set — a fourth frozen structure, and the move is ADDITIVE (a key appears on the paths that produced nothing usable; a SUCCESSFUL ingest's key set is exactly what X12 pins, so the invariant holds where it is asserted). **§8 read against the tree today, both halves:** its *also* is true again, because nothing is subtracted any more; its *learns nothing new* is now false in the harmless direction, because such a host learns MORE — including on the string and dict shapes this spec accepted as silent, which were indistinguishable from empty before 0039 was written and are not any more. **The round owed for v14 is owed for the pair; this cell and v14's are what it should read first.** *Prior:* **v14 — POST-ACCEPTANCE AMENDMENT, AND IT MOVES THREE THINGS THE REVIEWER FROZE (Quentin's word, dev session, 2026-09-10: *"Now do the wider normalization rule for null, number and boolean"*).** `0025` §4b(1) now normalizes EVERY non-list `triples` to no triples at both call sites — the wider rule this spec's own §10 Q4/Q6 drafted and left for a ruling. **What that moved in the frozen surface, stated plainly because acceptance froze it and the next external round is owed the disclosure:** (1) **row P6** of the answer matrix — `null`, a number and a boolean no longer raise `TypeError`; they return zero facts with ONE `primary_failed`/`shape` record, exactly as the string and dict beside them always did; (2) **V-RECORD-ORDER-ON-ERROR** — those three shapes WERE its only instance, so the property is re-instanced on an error that follows a record for another reason, and its row says so rather than absorbing the change; (3) **V-CENSUS** — a second guarded literal-reset site, named here because the census's own rule is that a new site fails the node until the spec names it. Everything else in the freeze is untouched: five callback sites, the six-value cause vocabulary, record-plus-error ORDERING as a property, the local-only recording path, the equivalence fixture and the unchanged result surfaces. **Measured, both independent instruments agreeing and exactly THREE transcript rows moving in each:** `RAISES TypeError` → `RESULT facts=0`. **The cost is in §10 Q6:** a host with no reporter loses this path's one loud signal. *No external round was run for this amendment; a round is owed and this cell is what it should read first.* *Prior:* **v13 — ACCEPTED at external round 4, 2026-09-10.** Verdict **ACCEPT**, banked verbatim `outbox/0039-round4-verdict-verbatim.md` — **body `b9cb1ed156413daa`** (the reviewer's words: *"sufficiently complete, internally consistent, and finitely verifiable to proceed through acceptance and implementation."*). **THE FROZEN INVARIANT SURFACE, in the reviewer's words:** *"Acceptance freezes: V-CENSUS, V-ANSWER-MATRIX, V-CALLBACK-CONTAINED, V-NO-INLINE-SEND, V-CAUSE-BOUNDED, V-DEGRADE-RECORDED, V-RECORD-ORDER-ON-ERROR, V-NO-CONTENT-IN-LOG, V-ONE-RECORD-PER-CALL, V-RECORD-FIELDS-TOTAL, V-NEVER-RAISED-BY-RECORDING, V-CLI-ATTACHES, V-RESULT-UNCHANGED, V-MCP-RESULT-UNCHANGED. The five callback sites, six-value cause vocabulary, thirteen-row two-call-site answer matrix, record-plus-error ordering, local-only recording path, deterministic callback-equivalence fixture, and unchanged result surfaces are part of that freeze."* **THE GOVERNING RULE FORWARD:** *"The named OWED tests and manual CLI log exercise remain mandatory implementation obligations"*; implementation review wants *"the completed implementation, all OWED tests, the manual CLI transcript, derived log-retention measurements, and the normal bound suite evidence"* — and *"keep the separated transcript-reproduction and history-binding tests; that division makes extracted-package evidence materially stronger."* The six malformed §6 rows in accepted specs, recorded as the table gate's starting debt, *"do not block 0039. They should be adjudicated and retired separately; the new monotonic gate prevents additional debt"* — an owner item. **ACCEPTED PACKAGE:** `0039-round4-review-package.tar.gz` sha256 `988298782a92f0f37bb81337c226ba2afbc5c725f904b2bec72fee6fc7b3a707` @ `d2ef676f470fdcfa497dc45c36bcbb50f5560863`, CI 34426512022, spec v12; a ONE-COMPLETE-LEG seal (dev's leg green 13/15; research's partial-clean, sections 1–9, its session's whole-suite kills unexplained), dispatched on the owner's word and recorded as such. The reviewer's reconciliation: 2,897 passed / 37 skipped in the extracted tree against 2,925 / 9 in the clone, both totalling 2,934 — 28 archive-dependent executions becoming named skips. **THE ARC:** four external rounds in two days (2026-09-09 → 10), each returned verdict closing the previous round's findings in substance; twelve internal versions; the round-1 reviewer found the primary path's cells wholesale where dev's own read had reasoned instead of run — after which every input→outcome sentence was produced by execution on two independent instruments and the executions were kept as tests; three of dev's own folds introduced the defect the next read found (two batteries hiding four asymmetries; an "or" row; a split invariant row), each caught by research or the reviewer before implementation, and the last one now has a gate. Credits: research (veracium-research-32/-5f) for the seven reads, the red-team on its own instrument, the fifth path, the dict-ness order, the shallow-clone state, the seal_check amendment and its four retractions; the external reviewer for four verdicts that each named the exact sentence that was wrong. Content is FROZEN from this cell: nothing below it changed at acceptance. *(was:* v12 — ROUND-3 EXTERNAL VERDICT FOLDED (RETURN for amendment, 2026-09-10; banked verbatim `outbox/0039-round3-verdict-verbatim.md`, body sha16 `072d5e8fb7bed39b`).** All three round-2 findings CLOSED; the core design called mature. **R3-1, blocking — fold damage, dev's:** the v11 script inserted V-RECORD-ORDER-ON-ERROR by replacing the OPENING of the V-DEGRADE-RECORDED row and re-emitting the new row after it, which left V-DEGRADE-RECORDED with two cells and the new row with six (its own four plus V-DEGRADE-RECORDED's displaced check and node cells) — neither invariant mapped to a check. Repaired to two independent four-column rows, and the reviewer's structural gate built: every table row in every spec's §6 must carry exactly the header's cell count, parsed with escaped pipes and code spans respected (a naive count would have flagged rows that are correct), with a planted split row as the control; the gate also found five shorter rows in four ACCEPTED specs' §6 tables, recorded as the gate's starting debt rather than silently edited. **R3-2:** the transcript-comparison tests called the git-history binding FIRST, so an extracted archive skipped both byte-for-byte comparisons — the evidence was sound (the reviewer ran both instruments by hand) but the archive claim was stronger than the test behaviour; reproduction now ALWAYS runs and the pin binding is its own test per transcript, proven in a bare copy of the tree (3 passed, 3 skipped by name). **R3-3:** the fixture now uses the constructor's `clock=` seam, the store's `_conn` connection seam, and declares `ORDER BY rowid` as the current-schema-only rule. *(was:* v11 — ROUND-2 EXTERNAL VERDICT FOLDED (RETURN for amendment, 2026-09-10; banked verbatim `outbox/0039-round2-verdict-verbatim.md`, body sha16 `89945febffdf1524`).** Round 1's four findings CLOSED in substance (the reviewer lists seven things resolved and rules the `Exception`/`BaseException` boundary not a finding). **R2-1, blocking:** the primary `null`/number/boolean cell contradicted itself across §2a, §2c, row P6, the matrix and two invariants. CHOSEN, deliberately: RECORD PLUS ERROR — the shape check runs before the loop and emits exactly ONE `primary_failed`/`shape` record for any non-list `triples`; the loop then behaves as today, so for `null`, a number or a boolean it raises `TypeError`, which `_on_error` records and the caller receives. Two records on that path, degrade then error, asserted by count and order (V-RECORD-ORDER-ON-ERROR). Option 1 (error only) was rejected because it would make the check decide on iterability — the property nobody chose — and §2a now says what "never raised" means: recording never raises and never changes an outcome; an operation may still raise for its own reasons after a record is written. **R2-2, blocking:** V-CALLBACK-CONTAINED compared SHA-256 over the SQLite file; reproduced — two identical ingestions return equal dicts and DIFFERENT file bytes, because `_uid` mints random ids. The evidence is now a DETERMINISTIC FIXTURE stated in the spec (§2c-iii: `_uid` replaced by a counter, the store's injectable clock fixed, fixed dates, a fresh store) and the comparison is over CANONICAL LOGICAL CONTENTS (every table, ordered, rendered as JSON), never file bytes, plus a per-site invocation count of the raising callback. **R2-3:** five carriers still described the three-site / exception-type / two-battery / seven-shape design (§4 twice, §5, §7, §9) — dev's post-v9 sweep caught none of them — a sweep with a 0/5 hit rate did not miss things, it did not run correctly: it searched for the NEW terms to confirm their presence rather than for the OLD terms to prove their absence, and presence confirms nothing about what remains (research's diagnosis). All five re-derived from the canonical five-site, six-cause, thirteen-row design; the v11 sweep searched for the old terms. **Standing archive:** dev's shape-driving script and its transcript are now IN the tree (`specs/evidence/0039/`), the transcript asserted byte-for-byte by a test so the execution is kept; research's transcript rides in the round-3 package. *(was:* v10 — RESEARCH'S DIFF OF v9 AGAINST ITS MATRIX FOLDED (2026-09-09; every measured cell agrees on both instruments — 17 primary and 9 retry shapes map onto rows 1–12 with no disagreement).** Two clauses and two measurements. **D1** row 10's title ("a list with malformed members") was wider than its cell: three kinds of member are not stored — a SHAPE-GUARD failure (silent, uncounted: the row's subject), a pipe-composed subject (`subject_refused`, already counted) and an off-vocabulary relation (`invalid`, already counted) — and `member_skipped` implemented against the title would count members two existing counters already count, the double count 0025's inventory exists to prevent; the clause: it counts SHAPE-GUARD failures only, never a member a rule refused. **D2** the merged invariant's provenance sentence read "absorbing V-ANSWER-MATRIX and V-ANSWER-MATRIX" — the v9 rename swept the one MENTION whose job was to name what was merged (a bulk replace applied to a mention as though it were a use, inside twenty-four hours of banking that rule); restored by name. **Two cells measured rather than read:** row 13 (a primary `Complete` call that raises propagates out of `ingest_event` — run: `RuntimeError` reaches the caller after one call) and row 12's retry cell (a retry answer carrying `instructions` as a string, as a list, or not at all is used for recovery unchanged — run on both instruments: `recovered: 1` in all three states; the field is not read there). *(was:* v9 — RESEARCH'S RED-TEAM OF v8 FOLDED (2026-09-09, before v8 was committed; the batch rule).** On research's OWN instrument (17 primary shapes and 9 retry shapes through the real `ingest_event`; a script sharing the author's assumptions cannot red-team the author): **H1** two batteries invite the defect they exist to catch — four shapes classify DIFFERENTLY depending on which call they arrive on, and with two tables an asymmetry is findable only by holding them side by side. v9 makes it ONE MATRIX (§2c-ii): shape down the side, the two call sites across, every cell one classification, every asymmetric row marked — so the next asymmetry is a row you read, not a discovery (the "or" row of v6, one level up). **H2** Q4 named one asymmetry; the matrix shows five, one of them 0025's design (a first-call provider failure is an error, a retry failure is a no-op) and four undesigned (`null`; a number or boolean; a bare array of dicts; a bare array of scalars) — Q4 and Q6 merge into ONE 0025 amendment question: one normalization rule shared by both callers. **H3** "bare array" is two rows with opposite outcomes on the first call (dicts recover; scalars silently yield nothing). **H4** three more silent-empty primary shapes (`[{}, {}]`; a nested `{"triples": {"triples": [...]}}`; a mixed list storing one fact and skipping three with `invalid: 0`) — all `member_skipped` or `shape`, named in the matrix. **Exhaustiveness claim, now with the matrix behind it:** no retry shape on either instrument lands outside the six `cause` values. **Measured premise for §1:** all eight non-recovering retry shapes return byte-identical counters (`invalid: 1, retried: 1, recovered: 0`) — eight provider behaviours, one observable. The retrospective gate's skip reason names the third repository state ("no repository") rather than "not a checkout", because an archive is not a shallow repo, it is no repo — and it SKIPS visibly, never passes, so the gate's own "a zero is not a pass" survives. *(was:* v8 — ROUND-1 EXTERNAL VERDICT FOLDED (RETURN for amendment, 2026-09-09; banked verbatim `outbox/0039-round1-verdict-verbatim.md`, body sha16 `a1192145c342ba4c`).** Four blocking findings, each REPRODUCED BY EXECUTION at HEAD before a line moved (§1f is the measurement). **F1** the PRIMARY extraction path had unclassified outcomes and v4's row 3 was WRONG — a wrong-typed `triples` does not raise `AttributeError`: a string or dict is iterated and every member skipped (zero facts, no flag, no error), a missing key is a silent empty result, and `null`/number/boolean raise `TypeError`; the spec's author DERIVED that row from reading the loop and did not run it, which is the rule this project already carries. → a primary-answer battery (V-ANSWER-MATRIX) with every cell classified normal / recorded degrade / propagated error, two new degrade kinds (`primary_failed`, `member_skipped`), and the retry battery re-measured (a `null` `triples` on the retry is the shape branch, not an exception). **F2** a raising `on_degrade` callback was not contained by the normative text → ONE guarded invocation helper every site must use (V-CALLBACK-CONTAINED: an AST census of direct calls plus a raising callback at every site with results and stored bytes identical to `on_degrade=None` — the bytes half of which round 2 refused as non-executable; v11's §2c-iii replaces it with a deterministic fixture over logical contents). **F3** "never delays" conflicted with `Reporter.record_error`'s synchronous pre-authorised auto-send (a 15-second HTTP timeout) → `record_degrade` NEVER sends inline; it writes one local line and leaves the record pending (V-NO-INLINE-SEND). **F4** length + unkeyed digest is not content-free and an exception class name is not a bounded vocabulary → lengths are UTF-8 byte counts, digests are SHA-256 over the stated UTF-8 bytes, the equality/guessing leakage is ACKNOWLEDGED in §8 (a keyed digest is §10 Q5, rejected with its reason), and `cause` is a CLOSED vocabulary — the exception's class name is never recorded (V-CAUSE-BOUNDED; a sentinel-carrying custom exception is a test). PACKAGE finding: the retrospective deadline gate went red in the reviewer's `git archive` tree (no `.git`) — made archive-aware in the same commit. *(was:* v7 — RESEARCH'S DIFF READ OF v6 FOLDED (2026-09-09; all eleven changed lines read, pass).** One wording defect, present since v5 and missed on the v5 read (research's own, not one a fold created): the battery's seventh shape read "a list of dicts → recovery", which a bare JSON array of dicts satisfies literally — the same input as the third shape, `bare array → cause=AttributeError`, with a contradictory outcome — in the one row that exists so a reviewer can implement it and add an eighth shape. Fixed to `{"triples": [dicts]}`, so the four object-form shapes are parallel and "bare array" is unambiguously the top-level case. *(was:* v6 — RESEARCH'S CONFIRMING READ OF v5 FOLDED (2026-09-09; a diff against v4, 17 hunks, all inside the listed cells; no blocking findings).** ONE finding the v5 fold itself created: V-ANSWER-MATRIX's bare-array row accepted EITHER outcome — normalized after §2e's amendment, `AttributeError` before — the only row with an "or", and exactly the row the amendment changes; a test that passes on both states cannot detect the transition it exists to bracket, and a wrong wrap (members dropped; wrapped and then failing anyway) would pass because `AttributeError` stayed an accepted answer, while the log count going to zero is an observation over production, not an assertion in the suite. Fixed: the battery asserts the CURRENT state (bare array → `cause=AttributeError`), and the 0025 amendment FLIPS that one assertion in the same commit that adds the wrap — the amendment cannot land without the test changing, the test change IS its proof, and the log count becomes corroboration. *(was:* v5 — RESEARCH'S v4 READ AND ITS FOLLOW-UP FOLDED (2026-09-09, same day; never committed between).** THE FOLLOW-UP, measured at HEAD: a FIFTH way to `reps = []` that v4's enumeration did not contain — a well-formed object with NO `triples` key (`{"repairs": [...]}`, `{"note": "none found"}`) returns `[]` from `.get`, raises nothing, touches no branch, and is indistinguishable in every carrier from `{"triples": []}` — the indistinguishability §1a exists to end. Classed a degrade with its own `cause` token `no_triples_key` (a wrong schema is not a wrong type). And the widened AST census has six spellings that evade it (an IfExp or `or []`, a guard assigning an ENUM member such as the volatility default, a binding one hop further, a parser that is not `extract_json`, a helper extracted out of `ingest_event`, a member-level filter that drops bad members) — so §6 states the class the census cannot answer ("where can provider output be silently discarded" is an OUTCOME question; a static rule answers "where does this code shape appear") and adds a DYNAMIC arm, V-ANSWER-MATRIX: every answer shape at the retry site produces a distinctly labelled record or a documented non-degrade, no two shapes sharing a classification unless the spec says they do — the arm that would have caught paths iii and v without anyone thinking of them first. Two findings from the read itself, both taken whole. **F2, BLOCKING:** the shape-path record could not satisfy V-RECORD-FIELDS-TOTAL — no exception, so no message to measure, and filling `msg_len`/`msg_sha16` with 0 and sha256("") would assert a zero-length message existed ("an absent key is not a zero" turned inside out, in the spec that cites it). Resolved by research's third option: the field set is declared per (`degrade`, `cause`), and the field is RENAMED `cause` — `exc_type` means "the exception's class name", a name made false by the token `shape`; a separate `degrade` value would split the operator's count of retry failures across two rows. **F1, SUBSTANTIVE:** V-CENSUS walks `ExceptHandler` nodes, so it cannot see a degrade of the shape v4 itself found — a guarded literal-reset branch that raises nothing; it guarded only the class already known. §6 now states that limit and widens the census to the second detectable shape. **Q4 → a 0025 AMENDMENT, re-argued:** `extract_json`'s docstring returns a bare array "for the caller to normalize"; the first extraction does, the retry does not — one of two callers not honouring the documented obligation of the function it calls, a contract-conformance defect, not a symmetry preference; drafted in §2e as an amendment to 0025 §4b(1), landing with this spec's implementation; row 2c stays as the evidence, and `cause=AttributeError` going to zero becomes the amendment's test. Minor: the shape branch is INSIDE the `try`, not above the handler. *(was:* v4 — DEV'S §3a CODE-REALITY READ FOLDED (2026-09-09, on Quentin's word "let's do spec 0039 for an internal read").** Every §1 claim re-verified at HEAD `b3c67d2` after 0037, 0025 v14 and 0038 landed on `ingest.py`: the census still returns four handlers (L114 re-raises; L294, L443, L503 continue); `Memory(diagnostics=None)`; `_on_error` at five sites, the CALLER re-raising; `load_reporter` in `build_memory` only; two CLI constructions, neither attaching; `RotatingFileHandler(maxBytes=1_000_000, backupCount=2)`; `redact` measured. ONE SUBSTANTIVE FINDING (D1): the retry site reaches `reps = []` FOUR ways and only two of them are exceptions — a well-formed answer whose `triples` is not a list is a shape branch that raises nothing, so a record emitted from the `except` would miss it; and the retry path lacks the bare-array wrap the first extraction has, so a bare JSON array answer is `AttributeError`, not recovery (§10 Q4, not changed here). §2a/§2c/§2c-i rows 2–3 restated for it; the retry record is emitted ONCE after the block on a failure flag, never on a legitimately empty recovery. Eight smaller corrections: a present `null` volatility is a drift (row 5); a wrong-typed first-extraction `triples` is an ERROR, not a degrade (row 3); the extractor's own message embeds `text[:200]` of provider output (row 7's measured instance); `redact`'s four patterns named; `user_hash` is sha256's first 12 hex; only the CLI's `remember` construction can emit a degrade record; V-RESULT-UNCHANGED phrased as the set X12 pins at HEAD. *(was v3 — RESEARCH'S v2 READ FOLDED (2026-09-07, same day).)** Read against the shipped paths at the v2 commit, not against v2's prose: the volatility handler sits inside the per-triple loop (so §2b's per-call count is derivable); `_on_error` exists with three call sites; X12's test says PRECISELY; `cli.py` has exactly two `Memory(...)` constructions. ONE finding, taken whole: **§2a's field table was CLOSED IN ONE DIRECTION ONLY.** "Nothing else may be added" and a mutant list that killed additions — and NOTHING forbade an OMISSION: a `volatility_defaulted` record with no `count`, a `retry_failed` record with no `exc_type`, satisfied every §6 invariant, because V-DEGRADE-RECORDED asserts existence and cardinality, V-NO-CONTENT-IN-LOG asserts absence, and none asserted the field SET. 0025 §4c had already named why it matters — *an absent key is not a zero* — for counters; a degrade record is where it applies next. **V-RECORD-FIELDS-TOTAL** (§6): for each `degrade` value the record carries EXACTLY its declared field set, asserted as exact set equality per degrade type, never a subset check; mutants: a record missing `count`; one missing `exc_type`; one carrying another type's field. The fourth invariant of the day found constraining one direction only (V-NEVER-HEAD over results; V-NO-EXISTENCE-SIGNAL by hiding everything; the withdrawn register catching uses not mentions; this) — the tell is a rule that names what must NOT happen without naming what MUST. Also §7: the window stated with its FILE COUNT beside the size — **3 MB (1 MB × 3 files: the active file and `backupCount=2`)** — because "backupCount=2 means three files" is the off-by-one that produced a wrong headline in the read that got the retention arithmetic right; and §7 now says the derived retention figure (records per window; events to evict a traceback) is the number to quote, since the retention claim is the section's subject and does not depend on getting a unit right. Credits: research (veracium-research-32), second read. *v2 — RESEARCH'S FIRST READ FOLDED (2026-09-07, same day as v1).* Four changes, each from a check EXECUTED against the shipped code rather than read from v1's description of it. **(1) A THIRD degrade path.** v1 said the two named sites were "the ONLY places ingest continues after a provider failure" and proposed an except-clause census as the proof; the census, run by both seats independently and converging, found FOUR handlers of which THREE continue: the two v1 named and `except ValueError: vol = Volatility.DURABLE` — a model-emitted volatility value outside the enum is silently coerced to DURABLE, per triple, with no counter, no record and no warning. v1's sentence survived on a strict reading ("provider *failure*") and failed the spec's purpose; §1 is widened from provider failure to **provider-originated degradation** and the volatility coercion is ranked WORST of the three, because the other two degrade into a visible absence and this one produces a record that looks correct, on an axis the paper names as a contribution. **(2) The record carries NO message text.** v1's "capped and redacted" was measured: `diagnostics.redact` on a provider error echoing a prompt removes the email and the phone number and keeps "Alice moved to Berlin" — it strips PII-SHAPED TOKENS and preserves the SEMANTIC PAYLOAD, which for a memory product is backwards (the fact IS the payload). The record is now the exception TYPE, the message LENGTH and a digest — never the text (§2a, §2c-i row 7, V-NO-CONTENT-IN-LOG). **(3) The seam is a callback, decided by 0025 X12.** v1 left open whether the degrade fact travels as a private field on the ingest result or as a callback on `ingest_event`'s signature; X12 asserts the result's counter keys are PRECISELY §4c's public set, so a private field survives only by exempting the invariant that makes the set closed. Callback (§2c; old Q2 closed). **(4) §7 answered the wrong question.** "Bounded by rotation" is a SIZE bound; the operator's question is RETENTION — after 0039 how long a real traceback survives depends on DEGRADE volume, and a per-triple record on the volatility path would evict the errors the log exists for. The volatility path is aggregated to ONE record per `ingest_event` call with a count (V-ONE-RECORD-PER-CALL); §7 states the retention consequence with the window re-derived from the handler's parameters. Also added to §8 as the spec's strongest argument, previously implicit: the CLI attaches NO reporter today (`load_reporter`: zero occurrences in `cli.py`, one in `mcp_server.py`), so every degrade — the volatility coercion included, for as long as it has existed — is invisible to a CLI user until this ships. Credits: research (veracium-research-32), first reader under PROCESS §3a: the census run, the redaction inversion framing, the X12 ruling, the retention arithmetic, the §8 limit. *v1 (2026-09-07) — THE DRAFT, written from the shipped code: the two ingest paths that record a failure instead of raising it, the library's `diagnostics=None` default, the two CLI `Memory(...)` constructions that attach no reporter while the MCP entry point does, and the MCP result's strip of the degradation counters. ONE reader: its author.* |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (veracium-research-32/-5f) — reads folded at v2, v3, v5, v6, v7, v9, v10 and the reads of the v11 and v12 folds; dev (veracium-90) — §3a code-reality read folded at v4 |
| **External review** | REQUIRED — changes what two shipped entry points do on error, and what the diagnostics log contains. **Round 1 (package `55c50e11…` @ `10f55a2`, v7): RETURN for amendment, 2026-09-09** — four blocking findings, folded at v8. **Round 2 (package `6d2a9f02…` @ `749e122`, v10): RETURN for amendment, 2026-09-10** — round 1's four closed in substance; two blocking (the P6 contradiction; the non-executable byte-identity test) and five stale carriers, folded at v11; both verdicts ride in round 3's package verbatim. **Round 3 (package `6f050414…` @ `3a470ee`, v11): RETURN for amendment, 2026-09-10** — round 2's three closed, the design called mature; one blocking (a split invariant row, fold damage), one substantive (archive runs skipped the transcript comparisons), one minor (the fixture's API names), folded at v12; all three verdicts ride in round 4's package. **Round 4 (package `98829878…` @ `d2ef676`, v12): ACCEPT, 2026-09-10** — R3-1/2/3 closed; the invariant surface frozen in the reviewer's words (the Version cell) |
| **Decision + date** | **ACCEPTED — 2026-09-10** (external round 4; Spec-Status flipped by dev, the acceptor, on the reviewer's verdict; no owner-path clause needed) |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0025** — the ingest report's counter inventory (`invalid`, `retried`, `recovered`, `residual`, `redispositioned`), present on every return path, and its rule that a provider failure during the ONE retry is recorded as `retried > 0, recovered = 0` and NEVER re-raised (§4b(1)). This spec keeps that contract unchanged: it adds a second carrier for the same fact, it does not turn a degrade into a raise. **X12** (the result carries PRECISELY the §4c public counter keys) decides §2c: the degrade fact does not travel on the result.
- **0031 §4d** — the operator-only counters are STRIPPED from the MCP tool result because a model that learns how often its attempts are refused learns to probe. This spec keeps that strip unchanged and does not add a principal-facing field (§10 Q1 asks whether one is wanted; it is not decided here).
- **0007 §4c** — the busy-timeout discipline is the precedent for "a failure has defined behaviour and a named form"; this spec applies the same discipline to the degrade paths' record.

---

## 1. Problem — measured, not hypothesised

**Veracium degrades in three places by catching, and — measured at v8, §1f — in two more
by defaulting and filtering, instead of failing, and by design.** Each is a correct
contract (0025 §4b; the BYO-provider clause; the extraction schema's tolerance). None
leaves a record an operator will see. The three are the ONLY exception handlers in
`ingest.py` that continue after catching; a fourth (the event-date parser) re-raises; the
two silent shapes on the first answer are not handlers at all. The
census is §6's V-CENSUS node — run, not read.

**1a. The retry that fails silently.** `ingest.py` makes ONE re-extraction call for
off-vocabulary triples. If the provider raises, times out, or returns malformed output,
the `except Exception:` at the retry site sets the replacement list empty and continues:

```
except Exception:
    reps = []          # malformed output / provider failure: a no-op,
                       # visible as retried > 0, recovered = 0 — never
                       # re-raised, never a second call (§4b(1))
```

The event is stored; the report carries `retried: 1, recovered: 0, residual: N`. A
provider outage during that call is indistinguishable, in every carrier that exists
today, from a model that gave a poor second answer. The exception object — its type and
message — is discarded at that line.

**Eight provider behaviours, one observable (v9, research's instrument).** Every
non-recovering retry answer — the provider raising, prose, a bare array of dicts, a bare
array of scalars, `triples` as a string, as a dict, as `null`, and a missing key — returns
the BYTE-IDENTICAL counters `invalid: 1, retried: 1, recovered: 0`. That is this spec's
argument, measured: eight distinct things the provider did, one thing the operator can
see.

**The five KNOWN ways to the same empty list (v4 found four and called it complete; v5 found the fifth).** `reps = []` is reached by at least (i) the
provider call raising; (ii) `extract_json` raising `ValueError` — no JSON in the answer;
(iii) a well-formed answer whose `triples` is NOT a list — the line
`if not isinstance(reps, list): reps = []` INSIDE the `try`, two lines above the
`except`, which raises NOTHING;
and (iv) a bare JSON array — `extract_json` returns the list as a fallback and `.get`
raises `AttributeError` inside the `try` (recorded as `cause=bare_array`); and (v) a well-formed object with NO `triples`
key at all — `{"repairs": [...]}`, `{"note": "none found"}`, a provider answering in its
own vocabulary — for which `.get("triples", [])` returns `[]`, raising nothing and
touching no branch. The first extraction wraps a bare array into `{"triples": [...]}`;
the retry path does not, so the same provider answer is a recovery attempt on the first
call and a failure on the second (§10 Q4 — resolved at v5 as a 0025 amendment, §2e).
Paths (iii) and (v) matter for this spec's shape: a record emitted from inside the
`except` would miss both, and (v) is indistinguishable in every carrier that exists today
from a legitimately empty recovery — `{"triples": []}`, the one answer that is NOT a
degrade — which is exactly the indistinguishability this spec exists to end. (v) was
found by research on the second read, after the enumeration had been called complete
once — so this list is "the known ways", not a closed count; V-ANSWER-MATRIX
(§6) is what makes its completeness testable rather than asserted.

**1b. The unparseable extraction.** A provider answering in prose, refusing, or returning
a wrong-typed `instructions` field (0038 §2c row 2) raises `ValueError` from the JSON
extractor and takes the early return: a content-free placeholder episode,
`unparseable: True`, every counter present at zero. No exception escapes.

**1c. The volatility coercion — the worst of the three, and the one v1 missed.** For each
triple the extractor emitted, the volatility class is parsed from the model's string:

```
try:
    vol = Volatility(str(t.get("volatility", "durable")).strip().lower())
except ValueError:
    vol = Volatility.DURABLE
```

An ABSENT key takes the declared default without entering the handler — that is a
default, not a degrade. A PRESENT value outside the enum (`"banana"`, `"long-term"`, a
provider's own vocabulary) is silently coerced to DURABLE, per triple. There is no
counter for it, no report key, no log line, and the record it produces looks correct.
Volatility classes are one of the axes the paper names as a contribution; a provider
that consistently emits an unrecognised class makes every fact durable and nothing
anywhere says so. The other two degrades are visible as an ABSENCE (no facts, a
placeholder episode). This one is visible as nothing.

**1d. Where a record could have gone, and did not.** The library has a diagnostics
reporter (`diagnostics.Reporter`): a local, user-owned rotating log
(`$XDG_STATE_HOME/veracium/veracium.log`, default `~/.local/state/veracium/`; three files
of 1 MB — the current file and two backups) that records genuine errors with the
operation name, a hashed user id and the full traceback; the caller then re-raises
(`_on_error` itself never does). Three facts about
it, each a line in the tree:

| fact | where |
|---|---|
| `Memory(...)` takes `diagnostics=None` by default; the library core never creates a reporter implicitly | `__init__.py`, the constructor's signature and `diagnostics.load_reporter`'s docstring |
| the MCP entry point DOES attach one: `build_memory()` passes `diagnostics=diagnostics.load_reporter()`, a `Reporter` whenever `log_enabled` (the default) | `mcp_server.py`, `build_memory` — the one occurrence of `load_reporter` outside `diagnostics.py` |
| the CLI's two `Memory(...)` constructions attach NONE — `load_reporter` does not occur in `cli.py` | `cli.py`, both construction sites |

And the error hook is called from five operations (`remember`, `recall`, `answer`,
`maintain`, `introspect`) — only when an exception PROPAGATES. None of the degrade
paths calls it, so even the MCP server's attached reporter records nothing when a
provider fails during the retry, answers unparseably, or emits a volatility class the
enum does not know.

**1e. What the MCP host sees.** The tool result strips `retried`, `recovered`,
`residual`, `invalid` and `redispositioned` (0031 §4d, by design); `unparseable`
survives the strip. So a host embedding the MCP server has exactly one degradation
signal — `unparseable: True` — and none for the retry failure or the coercion.

**1f. The primary path, measured (v8, from round 1's F1 — run, not read).** Every shape
below was driven through `ingest_event` at HEAD with a scripted provider; the outcome is
the observable one. The first extraction's `triples` handling is `for t in
data.get("triples", []): if not (isinstance(t, dict) and t.get("subject") and
t.get("relation") and t.get("object")): continue` — a default on the missing key and a
per-member filter — and neither is an exception handler:

| primary answer | outcome at HEAD | classification |
|---|---|---|
| `{"triples": [well-formed]}` | 1 fact | normal |
| `{"triples": []}` | 0 facts, no flag | normal empty result |
| no `triples` key | 0 facts, no flag, no record | SILENT — a degrade |
| `triples` is a string | iterated as characters, every member skipped: 0 facts, no flag | SILENT — a degrade |
| `triples` is a dict | iterated as keys, every member skipped: 0 facts, no flag | SILENT — a degrade |
| `triples` is `null`, a number or a boolean | `TypeError: ... is not iterable` PROPAGATES; `remember` raises; `_on_error` records it with its traceback when a reporter is attached | propagated error (already recorded) |
| bare JSON array of well-formed dicts | wrapped into `{"triples": [...]}`: 1 fact | normal |
| a list whose members are not well-formed dicts | each member skipped: 0 facts, no flag | SILENT — a degrade, per member |
| non-object top-level JSON (a string, a number) | `extract_json` finds no object or array: `ValueError`, the unparseable placeholder | recorded as `unparseable` |
| prose; `instructions` of the wrong type | the unparseable placeholder | recorded as `unparseable` |

v4's row 3 said a wrong-typed `triples` "raises `AttributeError` outside the handler,
which propagates". It does not. The author read the loop and reasoned about it; the
reviewer ran it. Three of the ten cells were silent and one raised a different exception
than the sentence named. The rule this project carries — a load-bearing claim about
shipped behaviour is verified by execution — was not applied to the one paragraph whose
subject was shipped behaviour, and §6's batteries now exist so that it cannot be skipped
again: the batteries are the execution, kept.

**The consequence the owner named:** during ordinary use, a run of provider failures
shows up only as counters in return values nobody reads, in a log that the CLI never
opens and that no degrade path writes to; and a provider whose volatility vocabulary has
drifted shows up nowhere at all.

## 2. Behaviour

**2a. A degrade is RECORDED through the diagnostics reporter — never raised.** When a
reporter is attached, each degrade path produces a record. "Never raised" means exactly
this (v11, round-2 R2-1): recording never raises and never changes an outcome; an
operation may still raise for its own reasons AFTER a record is written, and on the one
path where it does — a `null`, numeric or boolean `triples` on the first answer — the
reporter's log carries the degrade record and then `_on_error`'s error record, in that
order, exactly two (V-RECORD-ORDER-ON-ERROR). Read them as ONE call: the degrade record
says the answer's `triples` was not a list, it does NOT say the operation completed, and
the error record beside it is the one that says the call failed — an operator who reads
"handled" into a degrade record beside an error has read it wrong, and this sentence is
why the matrix's rows 6–7 say "record plus error" rather than "record". The count is PER
ROW (one record for a string or dict, which complete; two for `null`, a number, a
boolean, which raise) and conditional on a reporter being attached — with
`diagnostics=None` there are zero records and the `TypeError` propagates identically. The record's fields are
CLOSED IN BOTH DIRECTIONS — nothing may be added without reopening this table, and
nothing declared for a record class may be omitted from its record (an absent key is not a
zero, 0025 §4c; V-RECORD-FIELDS-TOTAL asserts the exact set per CLASS, where a class is
the pair (`degrade`, `cause`) — v5, research's F2: the shape path has no exception and
therefore no message, and a field set declared per `degrade` alone would force two
fields with no defined value onto it):

| field | value | never |
|---|---|---|
| `op` | the operation (`remember`) | — |
| `degrade` | one of `retry_failed`, `primary_failed`, `unparseable`, `volatility_defaulted`, `member_skipped` — a closed vocabulary (v8 added the two the primary path needs) | any other string |
| `user_hash` | the hashed user id — the existing `_on_error` convention: the first 12 hex digits of the user id's SHA-256 | the user id |
| `cause` | a CLOSED vocabulary (v8, round-1 F4 — an exception's class name is NOT recorded, because a provider-defined class name can carry arbitrary text): `provider_error` (the provider call raised, whatever the class), `no_json` (the extractor found no JSON object or array), `instructions_type` (0038 §2c row 2), `shape` (`triples` present and not a list — a string, a dict, `null`, a number, a boolean), `no_triples_key` (a well-formed object without the key), `bare_array` (retry only, and only until §2e's 0025 amendment: the list reached `.get`). Present on `retry_failed`, `primary_failed` and `unparseable` records; absent on the two counted kinds. A wrong type and a wrong schema are different facts — ONE field with one honest meaning, so the operator's count of retry failures is one row of `degrade` (v5; was `exc_type`, a name the token `shape` made false) | any other token; the exception's message |
| `msg_len`, `msg_sha16` | ONLY when `cause` is `provider_error`: the UTF-8 BYTE length of `str(exc)`, and the first sixteen hex digits of SHA-256 over exactly those UTF-8 bytes (v8: units and bytes defined; the class name, `args`, `__notes__` and attributes are never read) | **the message text, in any form, at any length, redacted or not; the class name** |
| `answer_len`, `answer_sha16` | for every `cause` except `provider_error`: the UTF-8 byte length of the provider's raw answer exactly as the `Complete` callable returned it (before any parse), and the first sixteen hex digits of SHA-256 over those bytes — so the operator can match the provider's own log by digest. §8 states what a digest leaks | **the answer text, in any form** |
| `count` | for `volatility_defaulted`: how many triples in this `ingest_event` call were coerced; for `member_skipped`: how many list members the SHAPE GUARD dropped in this call — the `isinstance(t, dict) and t.get("subject") and t.get("relation") and t.get("object")` test on the primary answer and the `isinstance(rep, dict)` test on the retry answer — and NEVER a member refused by a rule after passing the guard (an off-vocabulary relation is `invalid`; a pipe-composed subject is `subject_refused`; both are counted already, and counting them here would be two counters for one event, v10 D1) | the offending value's text (it is model output) |

Why no message text, measured (§2c-i row 7): `diagnostics.redact` removes exactly four
shapes — an email, a US phone `ddd-ddd-dddd`, a run of seven or more digits, a dollar
amount — and preserves everything else (`555-0100` survives; so does every word). For a memory product
"everything else" IS the payload: "Alice moved to Berlin" survives redaction intact. A
redactor tuned for logs cannot protect a store whose entire content is the thing the
redactor does not recognise, so the record does not carry the message at all. An operator
who needs the provider's text has the provider's own logs and the digest to match it by.

The degrade paths' return values are unchanged: `retried/recovered/residual` and
`unparseable` mean exactly what 0025 says; the coercion still yields DURABLE. The hook
that writes the record is best-effort (0025's rule that logging never masks or delays the
real outcome applies to a degrade as it applies to an error).

**2b. The volatility path is aggregated, not per-triple.** ONE record per `ingest_event`
call, carrying `count`. A ten-triple event with a drifted provider emits one record, not
ten. §7 says why this is a retention rule and not a tidiness one.

**2c. The seam: a callback, not a field, invoked through ONE guarded helper.** `ingest_event`
gains a keyword-only parameter `on_degrade: Optional[Callable[[str, dict], None]] = None`.
No site calls it directly (v8, round-1 F2): every site calls `_emit_degrade(on_degrade,
kind, payload)`, a module-level helper that returns at once when the callback is `None`
and otherwise invokes it inside `try/except Exception: pass` — it never re-raises, never
logs, never retries, and a `BaseException` (a `KeyboardInterrupt`) is deliberately NOT
caught, which §9 hands the reviewer. The sites:
The PRIMARY site (v8) runs once the answer is a dict (a bare array having been wrapped):
`"triples" not in data` → `primary_failed`/`no_triples_key`; `not isinstance(data["triples"],
list)` → `primary_failed`/`shape` — RECORDED ONLY; the loop still runs over whatever the
value is and the outcome does not change (a string still yields zero facts; `null`, a number or a boolean still raise `TypeError`
in the loop AFTER the record is written — the record first, then the error, row P6).
The member filter's `continue` on either path increments one per-call counter, emitted
once after both loops as `member_skipped` with `count` when non-zero. The retry site
calls the helper ONCE, after the `try`/`except` block, on a failure flag set by any of
§1a's five paths — the `except` sets the flag with `provider_error`, `no_json` or
`bare_array` according to which line raised, the shape branch sets it with `shape`, the
missing key sets it with `no_triples_key` — tested as
`isinstance(data, dict) and "triples" not in data`, STRICTLY AFTER dict-ness is
established and never inferred from an empty result: on a list `in` is a MEMBERSHIP test,
not a key test (measured: a bare array of dicts tests False, a bare array containing the
string `"triples"` tests True), so a key check hoisted above the `.get` would silently
reclassify a bare array (path iv) as `no_triples_key`, make row 2c unreachable, and
pre-break §2e's amendment test — `cause=bare_array` would already be zero for an
unrelated reason — and never when the recovery
was legitimately empty
(`on_degrade("retry_failed", {...})`); the unparseable path calls it from its handler
(`on_degrade("unparseable", {...})`); and once after the triple loop
`on_degrade("volatility_defaulted", {"count": n})` when `n > 0`.
`Memory.remember` passes `self._on_degrade`, a sibling of `_on_error`, which calls
`Reporter.record_degrade`. The ingest RESULT does not change: 0025 X12 asserts its counter
keys are PRECISELY §4c's public set, and a private field on it would survive only by
exempting the invariant that makes the set closed. A degrade is an event, not a counter;
it travels on its own channel.

**2d. The CLI attaches a reporter as the MCP entry point does.** Both CLI `Memory(...)`
constructions pass `diagnostics=diagnostics.load_reporter()` — a `Reporter` iff
`log_enabled`, the same rule `build_memory()` uses. Only the `remember` construction can
emit a degrade record (the other runs with a stub provider that never extracts); it
attaches the reporter for `_on_error`, so the two constructions stay one rule. The library core's default stays
`None` (embedding hosts pass their own or none — the existing contract).

**2e. What changes, stated exactly.** `ingest.py`: the `on_degrade` parameter, the
`_emit_degrade` helper, the primary-answer check (two conditions, records only), the
per-call member counter, the retry flag, the unparseable and volatility sites — and ONE
normalization line at the retry site, which is an AMENDMENT TO 0025
§4b(1) and is stated as one (v5, from §10 Q4 re-argued): `_json.extract_json` returns a
bare JSON array "as a fallback for the caller to normalize" (its docstring); the first
extraction normalizes it into `{"triples": [...]}` and the retry caller does not, so one
of the function's two callers does not honour the documented obligation of the function
it calls — a contract-conformance defect, not a symmetry preference. The retry wraps a
bare array exactly as the first extraction does; a bare-array retry answer becomes a
recovery attempt. Row 2c stays: before the amendment lands its record is the only
evidence in production that the asymmetry occurs; the amendment's PROOF is the battery
assertion it flips in its own commit (V-ANSWER-MATRIX, v6), and the record's count
going to zero afterwards is corroboration. The commit carrying it references 0025 and this
spec. No other line. `__init__.py`: `Memory._on_degrade`, passed from `remember`.
`diagnostics.py`: `Reporter.record_degrade` writing the §2a record at WARNING level in
the same log, best-effort, incrementing the pending count and NEVER calling `send()` —
no network I/O, no prompt, no throttle check (v8, round-1 F3: `record_error` may
auto-send synchronously under advance permission with a 15-second HTTP timeout; a degrade
record is left pending for the next `send()` the host or the error path performs). `cli.py`: two constructions gain the `diagnostics=` argument.
**The MCP tool result is unchanged** (§10 Q1). **No stored byte changes; no schema, no
export, no migration.** The primary path's OUTCOMES are unchanged by THIS
spec: at v13 the three shapes that raised `TypeError` still raised it and the silent
shapes still yielded zero facts — they were now RECORDED, which was the whole of the
change. **SUPERSEDED for those three shapes on 2026-09-10** by `0025` §4b(1)'s wider
normalization rule — the ingest amendment §10 Q4/Q6 named and the owner ruled on — so
they now return zero facts with their record, like the string and dict beside them. Row P6
carries the new cell and the accepted one it replaced; the version cell above records
what the amendment moved in the FROZEN invariant surface, which is the disclosure the
next external round is owed.

## 2c-i. Untrusted inputs — REQUIRED, blocking

The untrusted input is the BYO provider's exception and output. Every row states an
observable outcome and the invariant that enforces it.

| # | case | observable outcome | enforced by |
|---|---|---|---|
| 1 | the retry raises (network, provider, SDK) | ONE record `degrade=retry_failed cause=provider_error` with the message's byte length and digest — never the class name (row 7b); the return dict as 0025 specifies | V-DEGRADE-RECORDED, V-NO-CONTENT-IN-LOG, V-CAUSE-BOUNDED |
| 2 | the retry returns no JSON (prose, a refusal, a top-level scalar) | as row 1 with `cause=no_json`; NEVER the raw output — the extractor's own message embeds the first 200 characters of the answer, which is why the record carries length and digest only | V-NO-CONTENT-IN-LOG |
| 2b | the retry returns well-formed JSON whose `triples` is not a list — a string, a dict, or `null` (measured: `null` takes the shape branch, it does not raise) | ONE record `degrade=retry_failed cause=shape` (with the answer's length and digest, §2a) from the shape branch (§1a path iii — no exception is raised there); `retried > 0, recovered = 0` as today | V-DEGRADE-RECORDED |
| 2c | the retry returns a bare JSON array (of dicts or of scalars) | TODAY (asserted by the battery as the current state): `AttributeError` inside the `try`, `reps = []`, ONE record with `cause=bare_array`. AFTER §2e's 0025 amendment: normalized exactly as the first extraction does — a recovery attempt, NO record unless it then fails another way — and the battery's assertion flips in the amendment's commit; the record's count going to zero in the log is corroboration, not the proof | V-DEGRADE-RECORDED, V-ANSWER-MATRIX |
| 2d | the retry legitimately recovers nothing (`{"triples": []}`) | NO record — an empty list is an answer, not a failure; `recovered = 0` as today | V-DEGRADE-RECORDED's negative arm, V-ANSWER-MATRIX |
| 2e | the retry returns a well-formed OBJECT with NO `triples` key (its own vocabulary) | ONE record `degrade=retry_failed cause=no_triples_key` with the answer's length and digest; `retried > 0, recovered = 0` as today — today this answer is indistinguishable from row 2d. The check is `isinstance(data, dict) and "triples" not in data`, after dict-ness: a non-dict answer is row 2c, never this row | V-DEGRADE-RECORDED, V-ANSWER-MATRIX |
| 3 | the first extraction is unparseable (prose, a refusal, non-object top-level JSON such as a bare string or number) | ONE record `degrade=unparseable cause=no_json`; the placeholder episode as today | V-DEGRADE-RECORDED, V-ANSWER-MATRIX |
| P1 | the first extraction returns `{"triples": [well-formed]}` | facts; NO record | V-ANSWER-MATRIX |
| P2 | the first extraction returns `{"triples": []}` | zero facts; NO record — a normal empty result | V-ANSWER-MATRIX |
| P3 | the first extraction returns a well-formed object with NO `triples` key | zero facts as today; ONE record `degrade=primary_failed cause=no_triples_key` with the answer's length and digest — today this is silent | V-ANSWER-MATRIX, V-DEGRADE-RECORDED |
| P4 | `triples` is a string or a dict | iterated and every member skipped, zero facts as today; ONE record `degrade=primary_failed cause=shape` — today this is silent (v4 said it raised; it does not) | V-ANSWER-MATRIX |
| P5 | a list whose members are not well-formed dicts (a bare array of scalars; a triple missing `object`) | each member skipped as today; ONE record `degrade=member_skipped count=n` per call — today silent | V-ANSWER-MATRIX, V-ONE-RECORD-PER-CALL |
| P6 | `triples` is `null`, a number or a boolean | **AMENDED 2026-09-10, after acceptance — see the version cell.** ONE `primary_failed`/`shape` record and ZERO facts, exactly what a string or a dict produces in P4: `0025` §4b(1)'s wider normalization rule makes every non-list `triples` the recorded shape and no iteration, at both call sites, so nothing raises. *Was, and was ACCEPTED as, v11's deliberate RECORD PLUS ERROR:* the record, then `TypeError` from the loop, `_on_error`'s traceback, and `remember` re-raising — two records and an errored operation. §10 Q4/Q6 asked whether these three should stop raising; the owner ruled that they should | V-ANSWER-MATRIX, V-RECORD-ORDER-ON-ERROR (this WAS its only instance) |
| P7 | a bare JSON array of well-formed dicts | wrapped into `{"triples": [...]}` as today; facts; NO record | V-ANSWER-MATRIX |
| 4 | `instructions` of the wrong type (0038 §2c row 2) | as row 3 — the extractor's `ValueError` is the same exception class; the record does not say which shape failed, by design (the message would) | V-DEGRADE-RECORDED, V-NO-CONTENT-IN-LOG |
| 5 | a triple carries a volatility value outside the enum — a PRESENT `null` included (`str(None)` is `"none"`, outside the enum) | coerced to DURABLE as today; ONE record `degrade=volatility_defaulted count=n` per `ingest_event` call; the VALUE's text appears nowhere | V-DEGRADE-RECORDED, V-ONE-RECORD-PER-CALL, V-NO-CONTENT-IN-LOG |
| 6 | a triple carries NO volatility key | the declared default; NO record — this is not a degrade (absence; row 5's `null` is presence) | V-DEGRADE-RECORDED's negative arm |
| 7 | the exception message carries content (a provider echoing the prompt into an error) | the record carries the message's byte length and digest and NOTHING of its text — redaction is not consulted, because it preserves the semantic payload (measured: "Alice moved to Berlin" survives `redact`) | V-NO-CONTENT-IN-LOG |
| 7b | a provider-defined exception whose CLASS NAME, `args`, `__notes__` or attributes carry content (v8, round-1 F4) | `cause=provider_error` — the class name is never recorded; only `str(exc)`'s length and digest are read; nothing of the name or attributes appears anywhere in the log | V-CAUSE-BOUNDED, V-NO-CONTENT-IN-LOG |
| 7c | two records for the same message or answer | equal digests: the record REVEALS EQUALITY between records, and for a low-entropy text lets a holder of the log confirm a guess; acknowledged in §8, accepted because the log is local and user-owned, sent only under consent, and matching the provider's own log is the digest's purpose (a keyed digest, §10 Q5, would defeat it) | V-NO-CONTENT-IN-LOG (the bound is stated, not narrowed) |
| 8 | no reporter attached (an embedding host passing `None`; the CLI today) | no record, no exception, no change in behaviour — `on_degrade` is `None` and the sites do not call it | V-NEVER-RAISED-BY-RECORDING |
| 9 | the reporter itself fails (disk full, path unwritable) | swallowed inside the reporter (its existing contract: "nothing here re-raises"); the operation's outcome is unchanged | V-NEVER-RAISED-BY-RECORDING |
| 9b | the CALLBACK raises (an embedding host's `on_degrade`, or a bug in `Memory._on_degrade`) — at the retry site, the unparseable site, the volatility site, the primary site, the member site (v8, round-1 F2) | contained by `_emit_degrade`: the return dict and every stored byte identical to the same run with `on_degrade=None`; no site may call the callback except through the helper | V-CALLBACK-CONTAINED |
| 9c | a reporter with advance permission, an endpoint and the auto-send interval elapsed (v8, round-1 F3) | `record_degrade` performs NO network I/O and no prompt — the record is written locally and left pending; only `record_error`'s path and the host's `send()` may send | V-NO-INLINE-SEND |
| 10 | a degrade storm (every call fails; every triple drifted) | one record per call per path, bounded by the log's rotation (§7); no auto-send unless the operator pre-authorized it, throttled by `report_min_interval_s` (existing) | V-ONE-RECORD-PER-CALL; the reporter's existing bounds |

## 2c-ii. The answer matrix — one table, two call sites (v9)

Every provider answer shape, with its classification on the FIRST extraction and on the
RETRY, measured at HEAD on two instruments — dev's shape-driving script and research's,
written independently in the two seats' scratch areas, outside this tree; the OWED
matrix test is the execution kept. A row whose two cells differ is marked ⚠ and is either 0025's
design or an undesigned difference this spec RECORDS and §10 Q4 proposes to settle. The
column "after v8" says what this spec adds — a record, never a changed outcome. This
table is canonical; §2c-i's P-rows and the retry rows restate it.

| # | answer shape | first extraction, today | retry, today | after v8 |
|---|---|---|---|---|
| 1 | `{"triples": [well-formed]}` | facts | recovery | no record |
| 2 | `{"triples": []}` | zero facts, no flag | no recovery | no record — normal empty |
| 3 | well-formed object, NO `triples` key | silent zero facts | silent no recovery | `primary_failed`/`no_triples_key` · `retry_failed`/`no_triples_key` |
| 4 | `triples` is a string | silent zero facts (iterated as characters, each skipped) | silent (shape branch) | `primary_failed`/`shape` · `retry_failed`/`shape` |
| 5 | `triples` is a dict — a nested `{"triples": {"triples": [...]}}` included | silent zero facts (iterated as keys) | silent (shape branch) | `primary_failed`/`shape` · `retry_failed`/`shape` |
| 6 ⚠ | `triples` is `null` | `TypeError` PROPAGATES — an error | silent (shape branch) | first: the `primary_failed`/`shape` record, THEN the error, recorded by `_on_error` — two records, that order (V-RECORD-ORDER-ON-ERROR); retry: `retry_failed`/`shape` — an UNDESIGNED asymmetry (Q4) |
| 7 ⚠ | `triples` is a number or a boolean | `TypeError` PROPAGATES | silent (shape branch) | as row 6 |
| 8 ⚠ | bare JSON array of well-formed dicts | wrapped, facts | `AttributeError` inside the `try`, no recovery | first: no record; retry: `retry_failed`/`bare_array` — UNDESIGNED (the callee's docstring obliges both callers to wrap; one does) |
| 9 ⚠ | bare JSON array of scalars | wrapped, every member skipped, zero facts | `AttributeError`, no recovery | first: `member_skipped`; retry: `bare_array` — UNDESIGNED, and a different row from 8 (H3) |
| 10 | a list with members that FAIL THE SHAPE GUARD (`[{}, {}]`; `[valid, "junk", 7, null]` storing one fact and skipping three with `invalid: 0`, measured) — NOT members a rule refuses after passing it (an off-vocabulary relation → `invalid`; a pipe subject → `subject_refused`; both counted today) | guard failures skipped silently | guard failures skipped silently (the pool loop) | `member_skipped count=n`, one record per call over both loops, shape-guard failures only (v10 D1) |
| 11 | non-object top-level JSON (a string, a number), or prose | `unparseable` placeholder | no recovery | `unparseable`/`no_json` · `retry_failed`/`no_json` |
| 12 | `instructions` of the wrong type (0038 §2c row 2) | `unparseable` placeholder | not examined on the retry — MEASURED on both instruments (v10) over the field's WHOLE domain: a retry answer carrying `instructions` as a string, as a list, or not at all recovers unchanged, `recovered: 1` in all three states (a negative claim is only as good as the domain it was checked over) | `unparseable`/`instructions_type` · — |
| 13 ⚠ | the provider CALL raises | the exception PROPAGATES — an error (MEASURED, v10: a `RuntimeError` from the first `Complete` call reaches `ingest_event`'s caller after one call) | swallowed, no recovery (0025 §4b(1)) | first: `_on_error` records it; retry: `retry_failed`/`provider_error` — 0025's DESIGN, not a defect |

Five asymmetric rows: one designed (13), four undesigned (6, 7, 8, 9). The four share one
cause — the first extraction normalizes what it receives and the retry does not, or the
reverse — and one amendment to 0025 settles all four (§10 Q4, which absorbs Q6).

## 2c-iii. The callback-equivalence fixture (v11, round-2 R2-2)

"A raising callback changes nothing" is asserted over the store's LOGICAL contents under
a deterministic fixture — never over the SQLite file's bytes. Measured at HEAD: two
identical ingestions return equal dicts and different file bytes, because `_uid` mints a
random suffix for every record and the file's page layout is not part of any contract.
The fixture, which is part of this specification and rides in the round-3 package as
pseudocode:

```
def equivalent_runs(shape, callback):
    with monkeypatch.context() as m:
        m.setattr(ingest, "_uid", counter("id"))          # ids: id-1, id-2, ... in call order
        store = SqliteStore(":memory:", clock=lambda: FIXED_INSTANT)   # the constructor's clock= seam (0010 §4b-ii)
        calls = []
        cb = None if callback is None else (lambda kind, payload: (calls.append(kind), callback(kind, payload)))
        result = ingest_event(store, scripted(shape), USER, event_text=TEXT, date=FIXED_DATE,
                              author=USER_AUTHOR, context=EvidenceContext.direct(), on_degrade=cb)
        return result, canonical(store), calls

def canonical(store):
    # every user table, every row, ORDER BY rowid — declared as the CURRENT-SCHEMA rule: every
    # table in the shipped schema is a rowid table; a WITHOUT ROWID table added later must
    # be ordered by its declared primary key and this comment updated. The seam is the
    # store's private connection, `store._conn`, named here because the fixture is a test.
    return {table: [dict(zip(cols, row)) for row in store._conn.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            for table in sorted(user_tables(store))
            for cols in [[d[0] for d in store._conn.execute(f"SELECT * FROM {table} LIMIT 0").description]]}

for shape in the matrix's rows that reach a degrade site:
    r_none, s_none, _      = equivalent_runs(shape, None)
    r_raise, s_raise, hits = equivalent_runs(shape, raising)      # raising: lambda *_: raise RuntimeError("x")
    assert r_raise == r_none
    assert s_raise == s_none
    assert hits == [kind]                                          # the raising callback WAS invoked, once, at this site
```

Because `_uid` and the clock are controlled, the two logical dumps are exactly equal, not
merely equal up to identifiers; a difference is a real difference. This does not contradict
the repo's lineage rule "digest the BYTES, never a re-serialization": that rule answers an
IDENTITY question (which artifact is this — a reparse would give a plausible digest for
bytes nobody has), while this fixture answers an EQUIVALENCE question (did two outcomes
differ — bytes carry nondeterminism that is no part of the outcome). Two questions, two
rules; neither is to be "fixed" to match the other. The dump is the
canonical form; if a future schema adds a column the dump grows with it and the
comparison stays total.

## 3. Trust-class matrix — REQUIRED, blocking

Unchanged. No record's trust class, disclosure or assertability moves. The degrade
record is operator telemetry about the extractor, not a memory record. The coerced
volatility is stored exactly as today.

## 3b. Authorization — REQUIRED

No authorization decision keys on any of this. The record carries a hashed user id (the
existing `_on_error` convention) and no content; it crosses no scope boundary that the
error log does not already cross. `_disclosure_for` is untouched.

## 4. The field-consumer table — REQUIRED (guarded surfaces)

`ingest.py` and `__init__.py` are guarded (`check_spec_reference.py`'s `GUARDED`), so this
section is required.

| field / surface | who writes it | who READS it | reachability |
|---|---|---|---|
| the degrade record (log line, §2a's closed fields) | `Reporter.record_degrade`, called by `Memory._on_degrade` | the operator, by reading the log; `veracium diagnostics report`'s tail (existing, consented, redacted) | a log line; never persisted in the store; never returned |
| `on_degrade` (the callback) | `Memory.remember` supplies it; `ingest_event` invokes it only through `_emit_degrade`, at five sites (the primary shape/key check, the member counter, the retry flag, the unparseable handler, the volatility counter) | nothing else — it is not stored, not returned, not exported | the ingest result's key set is unchanged and 0025 X12's exact-set test proves it |
| `diagnostics=` on the CLI's `Memory(...)` | `cli.py` | `Memory`'s existing attribute | the same object the MCP entry point already attaches |

**Reachability evidence.** The three catching degrade sites are the ONLY exception
handlers in `ingest.py` that continue after catching (the census, V-CENSUS: four handlers;
three continue; one re-raises); the two silent primary-answer shapes are a `.get` default
and a per-member `continue`, which no handler census sees and V-ANSWER-MATRIX tests by
outcome (§6). Every other exception propagates to `_on_error`.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| provider healthy, schema followed | no degrade record; unchanged |
| provider fails during the retry | today: counters only; after: counters AND one record with `cause=provider_error` — never the exception's type (§2a) |
| provider answers unparseably | today: `unparseable: True`; after: the same AND one record |
| provider's volatility vocabulary has drifted | today: every fact DURABLE, nothing anywhere; after: the same facts AND one record per call with the count |
| CLI use | today: no log at all (no reporter — every degrade invisible); after: the same log the MCP server writes |
| embedding host passing `diagnostics=None` | unchanged: no log, no record — the host owns its own error handling |
| MCP host | unchanged tool result; the operator's log gains the degrade records |

## 6. Invariants and executable checks — REQUIRED, blocking

| id | invariant | check | node |
|---|---|---|---|
| **V-CENSUS** | `ingest.py` has exactly the three continuing exception handlers §1 names (the retry, the unparseable return, the volatility coercion) and every other handler re-raises; AND exactly the TWO guarded literal-reset branches (**one at v13, §1a path iii's retry; the second added 2026-09-10 by `0025` §4b(1)'s wider normalization rule, its twin on the primary path — named here because the census's own rule is that a new site of the shape fails the node until the spec names it**) (an assignment of an empty or default literal inside a branch whose test is an `isinstance` or truthiness check over parsed provider output, within `ingest_event`'s extraction and retry blocks); a NEW site of either shape fails this node until the spec names it. **LIMIT (v5, research's F1 and follow-up; v8, round-1 F1):** the census answers "where does this code shape appear", not "where can provider output be silently discarded" — an OUTCOME question no static rule answers. The primary path's two silent discards — a `.get("triples", [])` default and a per-member `continue` — are neither handler nor literal reset, and the census did not see them; the round-1 reviewer did, by running the code. It detects these TWO shapes and no third; path v (a missing key, no branch at all) is invisible to it, as path iii was to the v3 census, and six ordinary spellings evade the second shape (an IfExp or `or []`; a guard assigning an ENUM member — the volatility default rewritten as a guard would match neither shape; a binding one hop further; a parser that is not `extract_json`; a helper extracted out of `ingest_event`; a member-level filter). The node closes the two known spellings; V-ANSWER-MATRIX below tests the outcome | an AST walk over every `ExceptHandler`: classify by whether its body (transitively) raises; assert the continuing set equals the named three; PLUS a walk over every `If` inside `ingest_event` whose test is an `isinstance(...)`/`not ...` over a name bound from `extract_json`, asserting the set of literal-reset assignments in its body equals the named one — by enclosing function and caught type | OWED at implementation: `tests/test_0039_degradation_visibility.py::test_the_census_names_every_continuing_handler` |
| **V-ANSWER-MATRIX** | (v9, absorbing the two v8 battery invariants, which were named V-PRIMARY-ANSWER-BATTERY and V-RETRY-ANSWER-BATTERY before the merge — a mention, not a use, and v9's rename swept it; restored at v10, D2) §2c-ii is asserted as ONE table: for every row, the first-extraction cell AND the retry cell hold by exact equality, and no two rows share a classification on a column unless the table says so; an asymmetric row is asserted AS asymmetric, so the 0025 amendment that removes one must flip the row in its own commit. The retry column, as it stood before the merge (all MEASURED at HEAD, v8): raising → `cause=provider_error`; prose or a top-level scalar → `no_json`; bare array of dicts or of scalars → `cause=bare_array` — the CURRENT state, asserted as such; §2e's amendment flips this one assertion to "normalized, a recovery attempt (or `member_skipped` for scalars)" in the same commit that adds the wrap, so the test change is the amendment's proof (v6 — a row that reads "or" passes on both sides of the change it brackets); `triples` a string, a dict or `null` → `shape`; no `triples` key → `no_triples_key`; `{"triples": []}` → no record; `{"triples": [dicts]}` → recovery; and the first-extraction column as §2c-ii's rows 1–13. The arm that tests the OUTCOME rather than the spelling — it would have caught paths iii and v without anyone thinking of them first, and every evasion in V-CENSUS's limit is a different spelling of the same outcome | a scripted provider per answer shape at the retry; the record (or its absence) read back and compared to this row's table by exact equality; a NEW shape the reviewer names is added to the battery, not argued | OWED: `tests/test_0039_degradation_visibility.py::test_the_answer_matrix_holds_on_both_call_sites` |
| **V-CALLBACK-CONTAINED** | (v8, round-1 F2) every degrade site invokes the callback ONLY through `_emit_degrade`, and a callback that raises changes nothing: for each of the five sites, a run with a raising callback returns a dict equal to the run with `on_degrade=None`, leaves the store's CANONICAL LOGICAL CONTENTS equal under §2c-iii's deterministic fixture (ids from a counter, the clock fixed, fixed dates, a fresh store — never file bytes, v11 R2-2), and the raising callback is observed to have been invoked exactly once at that site | static: an AST census of `ingest.py` finds no `Call` whose function is the name `on_degrade` outside `_emit_degrade`'s body; dynamic: §2c-iii's fixture — result-dict equality, logical-dump equality, per-site invocation count | OWED: `::test_a_raising_callback_changes_nothing_at_any_site` and `::test_no_site_calls_the_callback_directly` |
| **V-NO-INLINE-SEND** | (v8, round-1 F3) `Reporter.record_degrade` performs no network I/O and no prompt under any configuration: with `report_enabled`, an endpoint, and the auto-send interval elapsed, a poster injected in place of `_post` is called ZERO times across every degrade path, while the same reporter's `record_error` in the same configuration calls it once (the control) | the poster mock; both counts asserted | OWED: `::test_record_degrade_never_sends_inline` |
| **V-CAUSE-BOUNDED** | (v8, round-1 F4) every record's `cause` is a member of §2a's closed set; a provider exception whose class name, `args`, `__notes__` and attributes all contain a sentinel yields `cause=provider_error` and NO occurrence of the sentinel anywhere in the log | the sentinel exception, raised at the retry; the log read back | OWED: `::test_cause_is_a_closed_vocabulary_and_a_provider_exception_name_never_reaches_the_log` |
| **V-DEGRADE-RECORDED** | (**v16, round-5 R5-2: every record is written BEFORE the first effectful store operation, so an error that follows finds it already in the log — the counted kinds were emitted after the loop and a store failure inside it lost them**) with a reporter attached, each recorded path writes exactly ONE record per occurrence (per call for the two counted kinds), naming the kind in §2a's closed vocabulary — on the first answer a non-list `triples` writes its ONE `primary_failed` record whether or not the loop then raises (v11); an absent volatility key, an empty `triples` list and a well-formed answer write NONE | scripted providers: one raising on the retry; one returning prose; one returning a wrong-typed `instructions`; one emitting `"banana"` for every triple; one omitting the key — the log read back | OWED: `::test_retry_failure_writes_one_record`, `::test_unparseable_writes_one_record`, `::test_drifted_volatility_writes_one_record_with_the_count`, `::test_an_absent_volatility_key_writes_nothing` |
| **V-RECORD-ORDER-ON-ERROR** | (v11, round-2 R2-1; **RE-INSTANCED 2026-09-10, after acceptance**) a degrade record written before an error in the same call stays BEFORE it: the log carries EXACTLY two records, the degrade record then `_on_error`'s error record with its traceback, and a run with `diagnostics=None` raises identically with no log. *Its only instance WAS the three raising primary shapes, and `0025` §4b(1)'s wider normalization rule removed that raise* — no provider ANSWER now reaches this ordering, so the property is instanced on an error that follows a record for another reason (the store failing after the retry's record). The amendment is disclosed rather than absorbed: this row's subject changed | a recorded call made to fail at the store, log read back: count == 2, order asserted by position, the exception class asserted; the mutants "error record only" and "degrade record after the error" both fail; PLUS the three former shapes asserted to write ONE record and no error | `tests/test_0039_degradation_visibility.py::test_a_degrade_record_written_before_an_error_stays_before_it` |
| **V-NO-CONTENT-IN-LOG** | no record contains ANY substring of the event text, of the model's output, or of the provider's exception message beyond its length and digest | a provider whose exception message and whose triple values echo the event text and a sentinel; assert no sentinel, no event-text token and no message substring longer than three characters appears in the log | OWED: `::test_the_record_carries_no_content` |
| **V-ONE-RECORD-PER-CALL** | the volatility path writes one record per `ingest_event` call regardless of triple count | a ten-triple event, every triple drifted: one record, `count` equal to the number coerced | OWED: `::test_volatility_records_aggregate_per_call` |
| **V-RECORD-FIELDS-TOTAL** | for each record CLASS (`degrade`, `cause`), the record carries EXACTLY its declared field set (§2a): `retry_failed`/`provider_error` → `op, degrade, user_hash, cause, msg_len, msg_sha16`; every other `retry_failed`, `primary_failed` and `unparseable` class → `op, degrade, user_hash, cause, answer_len, answer_sha16`; `volatility_defaulted` and `member_skipped` → `op, degrade, user_hash, count`; asserted as exact set equality per class, never a subset check; a `msg_*` field on a `shape` record or an `answer_*` field on an exception record fails | each scripted provider's record read back; the key set compared for equality against the declared set for its type | OWED: `::test_each_record_carries_exactly_its_declared_fields` |
| **V-NEVER-RAISED-BY-RECORDING** | recording never changes the operation's outcome: no reporter → identical return; a failing reporter → identical return; a failing CALLBACK → identical return and identical canonical logical store contents under §2c-iii's fixture (V-CALLBACK-CONTAINED is the direct test; this row inherits it) | the same scripted providers with `diagnostics=None` and with a reporter whose log path is unwritable; the return dicts equal the recorded ones | OWED: `::test_recording_never_changes_the_outcome` |
| **V-CLI-ATTACHES** | both CLI `Memory(...)` constructions pass `diagnostics=load_reporter()` | an AST census of `Memory(` calls in `cli.py`: every one carries the argument | OWED: `::test_every_cli_memory_construction_attaches_a_reporter` |
| **V-RESULT-UNCHANGED** | (**AMENDED TWICE after acceptance — see the version cells. v15 widened `unparseable` on the unusable paths only; v16 REVERTED that on the round-5 verdict and added `extraction_unusable`, a bool on EVERY path, so the clean path's key set gains one key, additively: `0025` X12's exact set is amended to carry it. The result surface is otherwise as accepted; nothing of the degrade record's content travels on it.) the ingest result's key set is exactly the set X12 pins at HEAD (0025 §4c's counters as amended 2026-09-08, 0038's `instructions_dropped`, 0023 Q4's two audit facts, 0026's two agreement counters); nothing of the degrade travels on it | INHERITED from `tests/test_0025_enforcement.py`'s X12 exact-set test | CHECKED today (the existing node) |
| **V-MCP-RESULT-UNCHANGED** | the MCP tool result gains no field | INHERITED from `tests/test_0031_phase_a.py`'s strip test and the result's existing shape tests | CHECKED today |

**Mutants the matrix must kill:** recording via `print`/stderr instead of the reporter
(the CLI-without-reporter regime would still see nothing persistent); a record carrying
the message text, capped or redacted (row 7 — the redaction inversion); a per-triple
volatility record (V-ONE-RECORD-PER-CALL); a record on an absent volatility key (row 6);
a degrade that raises when the reporter fails (row 9); the CLI attaching a reporter in one
construction and not the other; a fourth continuing handler added to `ingest.py` without
a spec row (V-CENSUS); the degrade fact placed on the ingest result (X12 kills it today);
a `volatility_defaulted` record with no `count`, a `retry_failed` record with no
`cause`, a `shape` record carrying `msg_len`, an exception record carrying `answer_len`,
a record carrying another class's field (V-RECORD-FIELDS-TOTAL — the omission direction,
which no other row constrains); a second guarded literal-reset branch added to the retry
block without a spec row (V-CENSUS's second shape); a wrong-key answer classified as
`shape`, or as a non-degrade, or two answer shapes sharing a `cause` the table separates
(V-ANSWER-MATRIX); the missing-key flag inferred from `reps == []` rather than
from the key test (it would mark a legitimately empty recovery as a degrade — row 2d
kills it); the key test run before dict-ness or on a non-dict (a bare array classified
`no_triples_key`, row 2c unreachable, the amendment's test pre-broken — the battery's
bare-array shape kills it).

### 6a. Acceptance measurement — REQUIRED, FINITE

Every invariant above is either CHECKED today by an existing node or OWED at a named
node; the table's last column says which, row by row, and no count is stated in prose.
Acceptance is the OWED nodes existing and passing, plus a manual run: the CLI against a
scripted provider that fails the retry and one whose volatility vocabulary has drifted,
then `cat` of the log, showing one record of each.

## 7. Failure modes and reversibility

- **Reversible.** Removing the five callback sites, the `_emit_degrade` helper, the parameter and the CLI arguments
  restores today's behaviour byte-for-byte; no stored state is touched.
- **Retention, not size — the question §7 must answer.** The log window is **3 MB:
  1 MB × 3 files** — the active file and its two backups (`maxBytes=1_000_000,
  backupCount=2`; the count is stated beside the size because "backupCount=2" reads as
  two files and means three). Before 0039, how long a real traceback survives in that
  window depends on ERROR volume. After 0039 it depends on DEGRADE volume too: every
  degrade record is bytes a traceback will rotate out behind. That is why the volatility
  path is one record per call and not per triple (§2b) — at per-triple volume a drifted
  provider would evict the errors the log exists for. The figures to quote are the
  DERIVED ones — records per window, and events to evict a traceback at a stated degrade
  rate — measured at implementation from the record's actual size and stated in the
  CHANGELOG with their conditions; the window size alone answers the wrong question.
- **The log can be sent — later, never from the degrade path.** Only under the existing
  consent flow, redacted, capped, and only from `record_error`'s pre-authorised auto-send
  or the host's `send()`: `record_degrade` leaves its record pending and performs no I/O
  beyond one local log write (v8, round-1 F3). This spec adds records to that log and
  therefore to what a consented send may carry — §2a is why the record carries no text by
  CONSTRUCTION, not by redaction: redaction was measured and preserves the payload.

## 8. Claims and limits

**This spec does not make a degrade an error.** 0025's contract stands: a provider
failure during the retry is a no-op with counters; an unrecognised volatility is DURABLE.
What changes is that each fact is also written where an operator looks.

**This spec does not tell the MCP host more.** The tool result is unchanged (§10 Q1).

**A host that passes `diagnostics=None` learns nothing new.** That is the existing
library contract and the right default for an embedding host with its own logging.

**The strongest argument for this spec is a limit of the shipped product, stated
plainly:** the CLI attaches no reporter today, so EVERY degrade is invisible to a CLI
user — including the volatility coercion, which has been silently defaulting a flagship
axis, with no counter, for as long as the handler has existed. Nothing in the tree could
have told an operator. This spec is the first carrier of that fact.

**What the record cannot tell the operator:** WHICH shape failed (row 4), WHAT the
drifted value was (row 5), WHAT key the provider used instead of `triples` (row 2e), or
WHICH exception class the provider raised (row 7b — `cause=provider_error` only).

**What the digest leaks, stated (v8, round-1 F4).** `answer_sha16`/`msg_sha16` are the
first sixteen hex digits of an UNKEYED SHA-256 over the stated UTF-8 bytes, and
`answer_len`/`msg_len` are UTF-8 byte counts. Two records with the same text have the
same digest: the log reveals EQUALITY between events, and a holder of the log can confirm
a guess at a low-entropy text (a short refusal string, a fixed error message). Accepted,
not argued away: the log is local and user-owned, it is sent only under consent, and the
digest's one purpose — matching the provider's own log for the same call — needs the
unkeyed form. §10 Q5 records the keyed alternative and why v8 does not take it.

**The three shapes that raise still raise.** A `null`, numeric or boolean `triples` on
the first answer is a `TypeError` today and after this spec; it is a propagated error the
error hook already records, and making it a degrade would change an outcome, which this
spec does not do (§10 Q6). Both would require carrying model output; both are recoverable
from the provider's own logs by the digest and the timestamp.

## 9. Brief for the external reviewer

Attack, in order: **V-NO-CONTENT-IN-LOG's and V-CAUSE-BOUNDED's tests**, because "no
substring" is a claim about a test's sentinel — round 1 named the exception's `repr`,
`args`, `__notes__` and the class name, and v8 reads none of them, so look for the
carrier v8 did not name; **`_emit_degrade`'s containment boundary**, which catches
`Exception` and deliberately not `BaseException` — a callback raising `KeyboardInterrupt`
or `SystemExit` propagates, by design, and if the reviewer thinks the boundary is wrong
that is a one-word finding; **the primary battery's P6 row**, which records `shape` and
then lets the `TypeError` propagate — the record beside the error is asserted, and a
reviewer may prefer no record on an error path; **V-NO-INLINE-SEND's control**, which
relies on `record_error` sending once in the same configuration — if the throttle state
leaks between the two calls the control is not a control;
and **V-CENSUS's classifier**, because "the handler's body transitively raises" is a
static property and a handler that continues on one branch and raises on another is
neither cell — and because §6 admits the census answers a shape question, not the
outcome question; **V-ANSWER-MATRIX** is the outcome test, its thirteen rows
are listed with both call sites' cells, and the reviewer is invited to name a fourteenth
(shapes were found on successive internal reads after the enumeration had twice been
called complete, and the round-1 reviewer found the primary path's cells wholesale). §1c's ranking — the coercion is worse than the two absences — is an
argument, not a measurement; disagree with it if the paper's axis claim does not bear
the weight.

## 10. Open questions

1. **Should the MCP tool result carry a single `degraded: bool`?** 0031 §4d strips the
   counters because refusal counts teach a model to probe; a boolean that says only "this
   write was degraded" is a smaller signal than `unparseable: True`, which is already
   exposed. Not decided here; the default is NO new field.
2. **Should `residual > 0` alone be recorded?** A residual can arise with a healthy
   provider (a triple no relation fits). This spec records only the FAILED retry (an
   exception or malformed output), not a residual the provider legitimately produced.
3. **Should the volatility record carry the drifted value's ENUM-DISTANCE or shape class**
   (a known synonym such as `long-term`, versus noise)? It would help an operator fix a
   prompt; it would also be the first byte of model output in the log. v2 says no; the
   reviewer may weigh it.

4. ~~Should the retry path wrap a bare JSON array as the first extraction does?~~ —
   **RESOLVED at v5 as a 0025 amendment, drafted in §2e; WIDENED at v9 (research, H2);
   BOTH HALVES LANDED 2026-09-10 on the owner's word, as `0025` v15 (the bare array)
   and v16 (the wider rule), each in its own commit with its measurement.** The wider
   half moved this spec's ACCEPTED row P6 and re-instanced V-RECORD-ORDER-ON-ERROR;
   the version cell records that and the next external round is owed the disclosure:
   the matrix (§2c-ii) shows the two call sites disagree on FOUR undesigned shapes, not
   one — `null`, a number or boolean, a bare array of dicts, a bare array of scalars —
   each a defect or a deliberate difference nobody wrote down. The amendment should be
   ONE normalization rule shared by both callers (wrap a bare array; treat every non-list
   `triples` as one recorded `shape`, no exception), which settles all four and absorbs
   Q6. The original argument stands: v4 framed it as a symmetry
   question and left the behaviour as shipped; research's v4 read reframed it: the
   callee's docstring obliges the caller to normalize, and one of two callers does not —
   a contract-conformance defect, which is the kind of justification an amendment to an
   accepted spec needs. Row 2c stays as the evidence.

5. **(v8, round-1 F4) Should the digest be keyed?** An HMAC with a per-install secret
   would remove the equality/guessing leakage §8 states. v8 does not take it: the
   digest's purpose is matching the provider's own log for the same call, which a keyed
   digest defeats, and the log is local, user-owned and consent-sent. If the reviewer
   weighs the leakage above the match, the field becomes keyed and loses that purpose.
6. ~~**(v8, round-1 F1; absorbed into Q4 at v9) Should a `null`, numeric or boolean `triples` on the first answer
   stop raising?**~~ — **RESOLVED AND LANDED 2026-09-10 on the owner's word: they stop
   raising.** It was a `TypeError` reaching the host while a string in the same position
   was a silent zero-fact result; the difference is iterability, not a property anyone
   chose. All non-list values are now one recorded `shape` degrade and zero facts, the
   rule the retry already applied — one line in a guarded file under `0025`'s extraction
   contract, carried as that spec's v16 amendment. **The cost, stated:** a host that
   attaches NO diagnostics reporter loses the one loud signal this path had; for that
   host a provider answering `{"triples": null}` is now indistinguishable from a
   provider that found nothing. That is the same visibility this spec's other four
   paths always had, and the reason it exists — but it is a loss, and the CHANGELOG
   says who should attach a reporter because of it.

*Closed at v2: the seam (callback, by 0025 X12 — §2c).*

## Reviewer checklist

- [ ] every claim in §1 is a line in the tree at the pinned commit; the census (V-CENSUS) is RUN and names three continuing handlers and one re-raising
- [ ] every degrade path's RETURN value is unchanged (0025 X12's exact-set test still passes; the callback adds no key; the primary path's three raising shapes still raise)
- [ ] the MCP tool result is unchanged (0031 §4d's strip test still passes)
- [ ] no degrade record can carry event text, model output or the exception message's text (row 7's mutant — the redaction inversion is measured, not argued)
- [ ] the volatility path writes one record per call, and none for an absent key
- [ ] each record carries EXACTLY its class's (`degrade`, `cause`) declared field set — the omission mutants (no `count`; no `cause`) and the cross-class mutants (`msg_len` on a `shape` record; `answer_len` on an exception record) fail, not only the addition mutant
- [ ] recording never changes an outcome, with or without a reporter, with a failing reporter, with a failing CALLBACK at every one of the five sites (results equal; canonical logical store contents equal under §2c-iii's deterministic fixture — never file bytes; the callback observed invoked once at the site)
- [ ] every primary-answer shape in §1f/§2c-i P1–P7 has exactly its classification, and the propagated-error cells are the three named
- [ ] `record_degrade` sends nothing inline under advance permission with an endpoint and an elapsed interval; `record_error` in the same configuration is the control
- [ ] `cause` is closed; a provider exception whose class name and attributes carry the sentinel leaves nothing of it in the log; lengths are UTF-8 bytes and digests are over the stated bytes
- [ ] the CLI attaches a reporter at every `Memory(...)` construction

## Review closure

<!-- GENERATED:review-closure -->

**0 internal round(s) and 5 external round(s) with a returned VERDICT are recorded for `0039`; 5 package(s) were dispatched** — counted from `specs/reviews.py`, which is the source this block is generated from. A round appearing here and not there, or the reverse, is impossible by construction. **SENT rows are dispatch records, not outcomes**, and are labelled below so the two are never summed.

| round | date | findings raised (from `raised=`) | verdict (compressed) |
|---|---|---|---|
| external 1 (SENT) | 2026-09-09 | — | SENT (round-1 package 55c50e111faafc02dee4e0250e757e70ac6a5c72da534c4da267cba1fcd43683 @ pin 10f55a2516fbb3791e9753b34325f5930746e38d, CI 34304829265; v7 — a draft after seven internal versions, no implementation; both legs green with four N/A named) |
| external 1 (verdict) | 2026-09-09 | 5 | RETURN for amendment 0039 v7 — "the feature is worthwhile, but the current draft does not yet define or verify all behavior needed to ensure that reporting remains observational"; four blocking (R1-1 the primary extraction path has unclassified outcomes and the spec wrongly says a non-list triples r… |
| external 2 (SENT) | 2026-09-09 | — | SENT (round-2 package 6d2a9f0263703d746bc2a46c24bbe7e49440e8e3acc866f76ff3570f128af7a5 @ pin 749e122182f1c2178537a37fbefe7a7ebfa95670, CI 34411618384; v10 — the SECOND assembly: the first, 72a199f308b5a1174b272efe00193672f8318c63e4ad5e12c5d0316ef96419db at the same pin, was refused by research's leg… |
| external 2 (verdict) | 2026-09-10 | 3 | RETURN for amendment 0039 v10 — "round 2 closes the substance of all four round-1 findings, but the revised specification is not yet internally consistent enough to freeze"; two blocking (R2-1 the primary null/numeric/boolean cell contradicts itself across four carriers; R2-2 the byte-identical stor… |
| external 3 (SENT) | 2026-09-10 | — | SENT (round-3 package 6f050414ad1f6d02c553305104b4adda6f65f0784040050797c4d2a0cd59d362 @ pin 3a470eef6f1e97f68534d97b1825db8cc35bfcfa, CI 34422913677; v11 — both instruments and transcripts in the tree; dispatched while research's leg was partial (sections 1–9) and dev's had not run) |
| external 3 (verdict) | 2026-09-10 | 3 | RETURN for amendment 0039 v11 — "the core design is now mature, and all three round-2 findings are resolved in substance. Two mechanical defects still prevent freezing the invariant surface"; R3-1 blocking (the invariant table structurally corrupted — a fold split the V-DEGRADE-RECORDED row; add a s… |
| external 4 (SENT) | 2026-09-10 | — | SENT (round-4 package 988298782a92f0f37bb81337c226ba2afbc5c725f904b2bec72fee6fc7b3a707 @ pin d2ef676f470fdcfa497dc45c36bcbb50f5560863, CI 34426512022; v12 — a one-complete-leg seal: dev's leg green 13/15, research's partial-clean, sections 1–9; dispatched on the owner's word) |
| external 4 (verdict) | 2026-09-10 | 0 | ACCEPT — "sufficiently complete, internally consistent, and finitely verifiable to proceed through acceptance and implementation." R3-1/2/3 closed; the invariant surface frozen in the reviewer's words (fourteen invariants; the five callback sites, six-value cause vocabulary, thirteen-row two-call-si… |
| external 5 (SENT) | 2026-09-11 | — | SENT (round-5 package bb989e45c249716de5bea1fedc08d9593c2875fe119120fd7d9e815dc1c3c096 @ pin 371cff9f51cd343db2c64d1f4404a64110571dbe, CI 34540844625; 0039 v15 + 0025 v17 — the implementation and three post-acceptance amendments; two complete legs on the same bytes, dev 42/1/2 with the FAIL a stale … |
| external 5 (verdict) | 2026-09-11 | 2 | RETURN for amendment — "The implementation is broadly sound and the package is complete, but two blocking gaps remain." R5-1 blocking (`unparseable` does not have the meaning X17 claims: an all-invalid list stays silent, and the flag fires on a rejected answer whose triples were usable — choose one … |

**Per-finding closure ledger — PROCESS §4a.** **13 finding(s) for `0039`** — every number here is DERIVED from the rows below (external round 7, R7-1: the manifest claimed 26 while the ledgers held 31, and 0023 said 9/9 above a 10-row table); the total across the tracked specs is derived once, in `specs/STATUS.md`. Generated from `specs/closure_findings.py` and validated against `specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — extras, duplicates, wrong rounds and empty evidence all fail the build.

| finding | round | what it was | closed in | evidence (runnable) |
|---|---|---|---|---|
| **0039-R1-1** | external 1 | The initial extraction path has unclassified outcomes; the specification incorrectly says a non-list triples raises AttributeError | v8–v10 (95fe67c, 749e122): every primary and retry answer shape RUN through ingest_event on two independent instruments and kept as committed transcripts; ONE thirteen-row two-call-site matrix (§2c-ii) with every cell one classification and five asymmetric rows marked; two degrade kinds added; the wrong sentence replaced by the measurement (§1f) | `$PY -m pytest tests/test_0039_answer_shapes.py::test_the_answer_shape_transcript_is_the_scripts_output tests/test_0039_answer_shapes.py::test_researchs_independent_instrument_still_prints_its_transcript tests/test_0039_answer_shapes.py::test_a_planted_shape_changes_the_transcript` |
| **0039-R1-2** | external 1 | A failing callback can change the operation outcome; the invariant only covered a missing or unwritable reporter | v8 (95fe67c): one guarded invocation helper `_emit_degrade` every site must use (Exception contained, BaseException deliberately not); V-CALLBACK-CONTAINED — a static census of direct calls and a raising callback at every one of the five sites with results and logical store contents equal to the None run (the fixture reworked at v11 after R2-2) | `git show 95fe67c -- specs/0039-degradation-visibility.md` |
| **0039-R1-3** | external 1 | "Never delays" conflicts with synchronous pre-authorised automatic reporting (a 15-second HTTP timeout in send) | v8 (95fe67c), the first option: record_degrade writes one local line, increments the pending count and NEVER calls send(); V-NO-INLINE-SEND with record_error in the same configuration as the control | `git show 95fe67c -- specs/0039-degradation-visibility.md` |
| **0039-R1-4** | external 1 | The metadata disclosure contract needs tightening: length + unkeyed digest is not content-free; an exception class name is not a bounded vocabulary | v8 (95fe67c): lengths are UTF-8 byte counts, digests SHA-256 over the stated bytes; the equality/guessing leakage ACKNOWLEDGED in §8 with the keyed alternative as Q5 and its reason; `cause` a closed six-value vocabulary, the class name never read; V-CAUSE-BOUNDED with a sentinel-carrying custom exception | `git show 95fe67c -- specs/0039-degradation-visibility.md` |
| **0039-P1** | external 1 | A retrospective gate invokes Git history, but the supplied git archive tree has no .git directory | v9 (95fe67c): the live node SKIPS visibly where there is no repository, with a reason naming the third repository state and restating "a zero is not a pass"; registered in the skip inventory; the throwaway battery still runs | `$PY -m pytest tests/test_spec_gate.py::test_no_security_hotfix_obligation_is_past_its_date_without_a_declared_discharge_or_deferral tests/test_spec_gate.py::test_the_retrospective_derivation_owes_past_dates_closes_declared_ones_and_refuses_vacuity` |
| **0039-R2-1** | external 2 | The primary null/numeric/boolean outcome contradicts itself across §2a, §2c, row P6 and the matrix | v11 (3a470ee): RECORD PLUS ERROR chosen deliberately and used everywhere; §2a defines "never raised"; the two records describe ONE call and the degrade record does not imply completion; V-RECORD-ORDER-ON-ERROR asserts count and order per row, conditional on a reporter | `git show 3a470ee -- specs/0039-degradation-visibility.md` |
| **0039-R2-2** | external 2 | The byte-identical callback test is not executable as written — independent ingestions generate random UUID identifiers | v11 (3a470ee), reproduced first: a deterministic fixture stated in the spec (§2c-iii — a uid counter, the constructor clock= seam, fixed dates, a fresh store) and the comparison over canonical logical contents, never file bytes, with the identity-versus-equivalence distinction written in; v12 aligned the pseudocode to the shipped API | `git show 3a470ee -- specs/0039-degradation-visibility.md` |
| **0039-R2-3** | external 2 | Carrier-completeness drift: five passages still describe the superseded three-site / exception-type / two-battery / seven-shape design | v11 (3a470ee): all five re-derived from the canonical five-site, six-cause, thirteen-row design, and two more found — the post-v9 sweep had searched for the new terms' presence, not the old terms' absence; the v11 sweep searched for absence | `git show 3a470ee -- specs/0039-degradation-visibility.md` |
| **0039-R3-1** | external 3 | The invariant table is structurally corrupted: the insertion of V-RECORD-ORDER-ON-ERROR split the V-DEGRADE-RECORDED row; add a structural gate | v12 (d2ef676): the two rows restored as independent four-column rows; a §6 table-structure gate over every spec (escaped pipes and code spans respected) with a planted-split control; the gate's starting debt — six shorter rows in four accepted specs — recorded as a frozen set, an owner item | `$PY -m pytest tests/test_spec_gate.py::test_every_section_6_table_row_has_its_headers_cell_count tests/test_spec_gate.py::test_a_planted_split_row_is_caught_and_escaped_pipes_are_not` |
| **0039-R3-2** | external 3 | Archive execution skips the new transcript comparisons because the tests call the Git-history check first | v12 (d2ef676): reproduction ALWAYS runs; the pin binding is its own test per transcript and skips only itself; proven in a bare git-archive copy (3 passed, 3 skipped by name) | `$PY -m pytest tests/test_0039_answer_shapes.py::test_the_answer_shape_transcript_is_the_scripts_output tests/test_0039_answer_shapes.py::test_devs_transcript_pin_describes_this_tree tests/test_0039_answer_shapes.py::test_researchs_transcript_pin_describes_this_tree tests/test_0039_answer_shapes.py::test_the_pin_binding_refuses_stale_foreign_and_unreachable_pins_and_names_the_two_skip_states` |
| **0039-R3-3** | external 3 | The deterministic fixture pseudocode does not match the shipped API (store.conn, "primary key", store._now) | v12 (d2ef676): SqliteStore(":memory:", clock=…), the store's _conn seam, ORDER BY rowid declared as the current-schema rule, cursor-derived column names | `git show d2ef676 -- specs/0039-degradation-visibility.md` |
| **0039-R5-1** | external 5 | `unparseable` does not have the meaning claimed by X17: an all-invalid list stays indistinguishable from a legitimate empty for a default host, and the flag is set when usable triples are rejected by another top-level rule | v16 (0025 v18, the owner's word 'Go with the new field'): the widening reverted; `extraction_unusable`, a bool on EVERY path, carries the outcome — no shape-valid triple, a legitimately empty list False; X12's set amended; the MCP result carries it, telemetry does not | `$PY -m pytest tests/test_0039_degradation_visibility.py::test_a_default_host_can_tell_a_malformed_answer_from_an_empty_one tests/test_0039_degradation_visibility.py::test_the_new_field_reaches_the_mcp_host_and_not_telemetry tests/test_0025_enforcement.py::test_public_counter_projection_is_exact` |
| **0039-R5-2** | external 5 | Aggregated records (member_skipped, volatility_defaulted) are emitted only after the storage loop and disappear when a later store operation fails | v16: every degrade record is computed and emitted before the first effectful store operation — the volatility coercion as a pure pre-pass, the episode write moved below the emissions; store-failure tests at BOTH seams (edge write, episode write) for all three record kinds | `$PY -m pytest tests/test_0039_degradation_visibility.py::test_counted_records_are_written_before_the_first_store_write tests/test_0039_degradation_visibility.py::test_a_degrade_record_written_before_an_error_stays_before_it` |

<!-- /GENERATED:review-closure -->
