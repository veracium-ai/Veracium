# Feature spec: procedural records and the `basis` axis (stages 1–3)

Spec-Status: accepted

*Candidate authored by dev (2026-09-06) on Quentin's commission of the same
day — "Commission the basis spec but sequenced after (2), and scoped to
procedural content only" — where (2) is the ruling that the stage boundary is
content-type-relative and that for procedural content stage 4 (recommend)
does not exist yet at all. Both rulings are logged verbatim in
`COORDINATION.md` under `[Quentin]`. Internal reviewer: research (semantics,
trust-model consequences, any public claim). Full spec: it touches guarded
files (`schema.py`, `ingest.py`, the gate). See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (veracium-69); the question and the axis from dev's first reading (2026-09-06); the scope, the sequencing and the commission Quentin's; three standing constraints research's (recorded in `COORDINATION.md`'s dev queue and carried in §2c, §4 and §10 here) |
| **Version** | **v24.6 — 2026-11-22: 0055's library twin, a text change riding with 0055's build (0055 §4g, R1-05; census D).** `Memory.record_procedure` keeps its `str` return (the canonical signature below is unchanged); the same call with 0055's report is `Memory.record_procedure_report(...) -> dict`, `{"edge_id": …}` plus `credentials_withheld` when a credential-shaped span of `summary` or `note` was withheld. The MCP tool builds its dict from the twin. **Prior:** **v24.5 — ROUND-9 IMPLEMENTATION CORRECTION UNDER THE FROZEN v24.3 CONTRACT (the round-9 verdict: "RETURN the import implementation for correction. The round-8 design acceptances remain in force.").** F1, reproduced at the round-9 pin before the fix, Q stored and Q incoming, both orders: stored P (`host`) and Q (`extractor`); a copy of P in the file claiming Q as its predecessor is refused, yet S (`extractor`, supersedes P) restored — the lineage helper preserved P's stored producer and then replaced it with the producer derived from the combined predecessor claims. THE CAUSE, attributed as research asked it to be: v24.4's union of the stored record's `supersedes` with every incoming copy's (research's pre-seal finding C, correct for C) fed CLAIMED ancestry — including from copies that were themselves refused — into a downstream rule that preferred the chain's validated producer over the record's own; that rule had been safe only while the chain came from the store, where the write-time choke point had already enforced inheritance. A fix's blast radius is every rule downstream of the input it changes, and that question was not asked. The correction: a PERSISTED producer is the constraint — the store enforced inheritance when the row was written, so a stored record is never a rejected intermediate, and a claimed ancestry, from an admitted or a refused copy, can add procedural-ness and never replace it; a persisted record WITHOUT a producer (the unstamped era) takes the claimed chain's producer, a claim adding a constraint and never removing one. THE EDITS, STATED SO A DIFF CONFIRMS THEM: Gate 1's block byte-identical; V-INHERITANCE-AT-IMPORT's v24.4 contract cell and citation cell each a byte-exact prefix of v24.5's, the first gaining a dated v24.5 clause with its mutant, the second gaining the new test; §4e's refusal paragraph gaining one sentence; this cell; and the corpus pin line, which follows the text by construction. Nothing else moved. F2 of the same verdict (an omitted event date defaulted to the host's LOCAL calendar date while ingestion reads a bare date as UTC midnight, so a runtime whose local date runs ahead of UTC stored new records as not_yet_valid until UTC midnight) is a pre-existing defect outside this spec's contract, fixed in the same commit — one clock, the UTC calendar date, for every omitted date — and recorded in the CHANGELOG. *Prior:* **v24.4 — ROUND-8 IMPLEMENTATION CORRECTION UNDER THE FROZEN v24.3 CONTRACT (the round-8 verdict: "ACCEPT the design; RETURN the import implementation for one remaining correction" — the whole-sentence and inheritance contracts frozen under the finite-acceptance rule). THE EDITS, STATED SO A DIFF CONFIRMS THEM: Gate 1's block is byte-identical to v24.3's; V-INHERITANCE-AT-IMPORT's v24.3 contract cell and citation cell are each a BYTE-EXACT PREFIX of v24.4's — nothing removed or reworded — the contract cell GAINING a dated v24.4 clause that records the resolution order the verdict required ("resolve conflicting ids before deriving lineage; preserve the persisted predecessor's constraints; a rejected record cannot erase them; both orders one disposition") with its mutants, the citation cell gaining the new tests; §4e's refusal paragraph gains the `duplicate_id` refusal (a new refusal class — the one behaviour change, named in the CHANGELOG); and this cell. Nothing else in the document moved (research's pre-dispatch read of the first round-9 seal found this cell claiming a smaller edit than was made — "the row's evidence citations" — and the seal was discarded before dispatch for this sentence).** Finding 1, two forms, reproduced at the round-8 pin before the fix: (a) a REFUSED incomplete copy of a stored procedural predecessor (stamp only — no basis, no producer) hid the stored `host` producer, and an `extractor` successor restored, both orders; (b) a file naming one id twice (procedural and ordinary) plus an ordinary successor gave a file-order-dependent disposition. The cause, as the reviewer named it: the lookup kept the LAST incoming record per id and preferred it over the stored record. The correction: conflicting ids are resolved BEFORE lineage is derived — every copy of an id the file names more than once is refused as `duplicate_id` (a file cannot say two things about one record; both orders refuse the same copies); the lineage helper reads the destination's stored record FIRST and every incoming copy together (a copy can add procedural-ness and never remove a stored stamp or producer — a rejected record cannot erase a persisted constraint); copies that disagree about a constraint leave it UNRESOLVED, which no successor satisfies. Order-independent by construction (sets, never "the last one seen"). Both forms, the reviewer's valid re-import control, and six mutants (agreeing duplicates, disagreeing duplicates, stored-record precedence over disagreeing duplicates, a duplicated intermediate under a stored predecessor, ordinary duplicates) asserted in both orders with the stored rows. Research's PRE-SEAL red team of the fix (2026-09-14) found two more forms in the helper, both reproduced and closed before this seal: (A) the stored record's own-ness read `Provenance.procedural` — stamp-or-basis only — so a registry-only procedural predecessor was refused with its successor when INCOMING and let its marker-free successor land when STORED; one helper now reads the same four signals for both custody states. (C) the predecessor set was REPLACED by the stored record's, so a stored declarative X with no predecessor shadowed an incoming X's claim to a procedural predecessor and X's successor inherited from the shadow; the set now adds and never removes, as the markers already did. The unresolved sentinel is a unique object, not a value a record could carry (research's note B: the string sentinel was held out of the check by the closed producer lexicon alone). *Prior:* **v24.3 — ROUND-7 EXTERNAL RETURN FOLDED: the enclosure structure is typed, quote-aware, and established or the passage is declined; the lineage helper reads every import signal and carries a VALIDATED inherited producer through rejected intermediates (verdict banked, body sha16 2c8cb4120a2350f7).** The reviewer: "the decision to decline uncertain passages stands"; two findings, each reproduced at main before a line changed: (F1) a quoted closing character ended a parenthetical prematurely — "For illustration only (press \"]\" when ready?) I review invoices daily." (and the \")\" form) admitted the last sentence with its framing stripped, because v24.2's depth counter read any closer, quoted or not, and accepted mismatched types; (F2) the lineage helper recognised fewer signals than the import filter — a REGISTRY-only predecessor was refused while its marker-free successors imported (the immediate one reaching unverified recall context), a PRODUCER-only predecessor's grandchild imported, and on restore a `host` lineage with an intermediate changed to `extractor` (refused) let a further `extractor` successor restore: the raw field of a rejected intermediate stood in for validated inheritance. v24.3: `enclosure_structure` — parentheses, brackets and braces must nest and match by type; characters inside a quoted literal are inert (a quoted `]` or `)` closes nothing; a terminator inside quotes ends nothing); a mismatch, a stray closer, an unclosed opener or an unbalanced double quote leaves the structure UNESTABLISHED and every segment of the passage is declined (a stated cost: a lone `"` in a turn — `5" screens` — declines it); the lineage helper reads the filter's four signals (stamp, basis, producer, and the receiving registry's kind on the default path) and the inherited producer is validated down the chain — a record whose own producer disagrees with its lineage's validated producer is a rejected intermediate whose constraint carries on to its successors unchanged. The README's third discussion point is qualified (a direct write carrying a producer is counted by its stamp; only an absent producer lands in `unstamped`). §8's cost figures now recompute from research's EMITTED histogram, shipped beside the script, with the reconciliation asserted by a test — the arithmetic checks without the dataset. Measured with the thresholds of 2026-09-14T14:05Z unchanged: draw 5 still 0 of 6 rows / 0 of 4 passages, the 16 pinned 13, draws 1–4 unchanged; the reviewer's cases refuse and the controls admit end to end. Prior: **v24.2 — ROUND-6 EXTERNAL RETURN FOLDED: a terminator inside an enclosing parenthetical ends nothing; a run establishes the next start only by what follows it; the import lookup sees refused predecessors and reads procedural-ness by lineage; the cost figures relabelled (verdict banked, body sha16 2bafe68f50919d90).** The reviewer: "your decision to decline uncertain passages stands"; three findings and two cleanups, each reproduced at main before a line changed: (F1) punctuation inside a parenthetical was read as an outer boundary — "For illustration only (ready?) I review invoices daily." (and the `ready!` form) admitted the last sentence with its framing stripped; and "Any tips?I review invoices daily." admitted while the `!` form refused, because the question branch returned before looking at what follows; (F2) on the DEFAULT import path the inheritance lookup was built from the records that survived procedural filtering, so a refused procedural predecessor erased its marker-stripped successor's requirement and the successor imported, reaching model context as `use_only` (both orders; restore refused correctly); (F3) §8's "53.6% of sentence positions" was the fraction of CHUNKS holding more than one sentence — research's own mislabel of its own count, reported to the owner as such: the sentence-weighted exposure is 76.3% (5,045 of 6,608 sentence positions), the reviewer's floor ≥69.8%; neither figure is a capture-loss figure; the decision stands (the true figure makes fail-closed more costly, not less). v24.2: the segmenter tracks parenthetical/bracket depth and a terminator inside one is inside its sentence; a run establishes the next start only when the end of the text or whitespace and a sentence start follows it, whatever marks it carries (a `?` run followed by a letter is ambiguous, as the `!` form already was); the import boundary's lookup is built from the RAW records before any refusal, with procedural-ness by LINEAGE (a chain dropping the markers one hop later is refused one hop later too) and the destination's existing records included, in either file order; §8 carries both figures labelled and research's `chunk_sentence_census.py` ships in the evidence tree; the withdrawn "live reading" sentence swept from every carrier including the package README; the diagnostics fixture the reviewer named installs its fake sender before enabling reporting. Measured with the thresholds of 2026-09-14T14:05Z unchanged: draw 5 still 0 of 6 rows / 0 of 4 passages, the 16 pinned 13, draws 1–4 unchanged; the reviewer's cases refuse and the controls admit end to end. Prior: **v24.1 — ROUND-5 EXTERNAL RETURN FOLDED: boundaries are ESTABLISHED or the passage is DECLINED — no list; a mid-text period establishes nothing (the owner's word, dev session 2026-09-14: *"Fail closed"*; verdict banked, body sha16 e9f2f0d7afe895d1).** The reviewer: round 4's four cases closed; 0006 v10 and the 0014 block ACCEPTED; four findings on v24, each reproduced at main before a line changed: (F1) an ambiguous separator still let a passage START after it — "For illustration only, e.g. I review invoices daily." and "I am only imagining that... I review invoices daily." admitted the last sentence with its framing stripped (the segment's end was validated, its start never — the verifies-the-adjacent-property class); (F2) the disclosed abbreviation residual reached description — "I review invoices in env. Prod only after approval." stored "I review invoices in env" — and the reviewer's answer to §8's product question: NOT acceptable under the assertion-preservation contract; no list can establish the guarantee; capture must preserve the qualifying context or DECLINE passages whose boundaries cannot be established, the capture cost reported separately; (F3) the restore commit wrote rows directly, so a format-12 file with a `host` predecessor and an `extractor` successor restored both (V-PRODUCER-INHERITED) — and, dev's probe, a marker-DROPPING successor too (V-STAMP-INHERITED); (F4) `procedural_unstamped` on a new store does not prove a write past `Memory` — a format-11 record restored into a new database gives 1 through an ordinary supported path, so v23.1's "live reading" was an over-claim (research's sentence, taken by dev; withdrawn). v24.1: a boundary is ESTABLISHED only at the start or end of the text or at a `?`/`!` run followed by a sentence start; a mid-text period establishes nothing in either direction and the abbreviation list is REMOVED; a span must begin at an established boundary (F1) and end at one; the inheritance rules are applied at the import boundary to every incoming record against its predecessor, incoming or existing, on both paths, in either file order, refusing the violating successor per record (F3); the doctor names every cause of an unknown producer and claims nothing about why (F4); research's rubric v2 is in the tree with its digest (the reviewer's ask). THE COST, measured and stated (§8): a routine sentence followed by a period-terminated neighbour is not capturable — about 54% of sentence positions in the corpus (research: 1,809 of 3,372 `?`/`!`-delimited chunks in 500 sessions carry two or more sentences), and both of draw 5's admissions fall (0 of 4 distinct positive passages); the 16 pinned observed positives are unchanged (13 admitted; single-span quotes cannot inform this); draws 1–4 unchanged. Prior: **v24 — ROUND-4 EXTERNAL RETURN FOLDED: boundaries are KINDS read from the complete event, total and fail-closed; the claimed cognitive refusal is real (verdict banked, body sha16 17ec9724a5e2304c).** The reviewer: the trimming finding is closed and the direction stands — store the verified wording without transformation, keep the authorship checks, keep the exclusion; "the boundary rules still permit meaning changes", three findings, each reproduced at main before a line changed and ONE ROOT CAUSE for the first two: v22's rule tested CHARACTERS (`[.!?]`), not sentence boundaries — (F1a) a span could stop one character short of its own `?` and a question was stored as a statement; (F1b) the `.` in `$100.50` counted as sentence-final and the stored text lost part of the amount and the condition after it; (F2) `daily.archive` carried two sentences as one because the internal check wanted whitespace after the terminator; (F3) §4a-iii CLAIMED "I doubt I review invoices daily." refuses on its cognitive head while `doubt` was not in the class — a spec claim with no code behind it (the name-the-mechanism class; research's miss on the record: its pre-seal attack tested the rule's additions and never the spec's own claimed refusals). v24: a terminal run has a KIND read from the complete event, and the kinds are TOTAL over what can follow it — end-of-text, or whitespace and then an uppercase letter, a digit or an opening quote/bracket → a BOUNDARY; a `.` between digits → INSIDE (a decimal); `?` anywhere in the run → a QUESTION, refused per SENTENCE (never per event: a user turn that ends in a question to the assistant still yields its routine sentence — 10 of draw 5's 11 user events carry a `?`, both admitted pairs among them, unchanged); everything else → AMBIGUOUS and refused, never guessed: an ellipsis, a single-letter or listed abbreviation before the run (`a.m.`, `approx.`, `Dr.`, `reqs.`), a vowel-less short token before it (`mgmt.`) (WITHDRAWN wording, v24.1), a letter or symbol right after it (`daily.archive`), whitespace then a lowercase letter (`daily. archive`, `commit. npm test`). The span must start at a boundary (never mid-token: `$100.`|`50 daily`) and may omit only a plain `.`/`!` — never `?`, never a closer. `doubt`, `deny`, `suspect`, `presume` join the cognitive class; `question` and `bet` do NOT (research's constructed routine senses, each a must-not-refuse control); `figure`/`guess`/`reckon` were already in the class — a pre-existing cost SURFACED here, not introduced. Measured with the thresholds fixed first (ledger 11:21Z): the 16 pinned observed positives, draws 1–4 and draw 5 all unchanged; the reviewer's four cases and research's abbreviation and ellipsis cases refuse end to end; ONE COST — a lowercase continuation after a terminator (`daily. archive`; `commit. npm test follows`; `morning. iPhone reminders help`) is an ambiguous join and the FIRST sentence refuses too (v22 admitted it), the safe direction; ONE OPEN RESIDUAL, stated in §8 as finding 1's class still reachable: an abbreviation outside the list that carries a vowel (`sched.`) reads as a boundary, pinned so a change is noticed. The broad narrowing (every short unlisted word before a period and an uppercase word) was built and measured first and refused the canonical routine shape (`every time. Unrelated…`), so it was not taken. Draw 5's eleven labelled pairs now run through the FULL PATH in the packaged test (remember → store → describe; research's assertions lifted; the context declared, the admitted count asserted beside the verdicts). Prior: **v23.1 — the `unstamped` bucket names BOTH its causes (research's read of the landed v23, 2026-09-14: the docstring said "written before the producer stamp existed" while the bucket also collects a procedural record written AFTER it through a path other than `Memory` — the same under-description that had just been repaired in `procedural_declared`; now stated in the doctor's message, §4a-iii, §4e, the docs and the CHANGELOG, and on a store created after the stamp existed a non-zero count is the LIVE reading of the boundary 0006 v10 rule 10 states). Prior: v23 — THE STORE BOUNDARY STATED, `Provenance` FROZEN, THE PRODUCER STAMP (the owner's word, dev session 2026-09-14: *"Confirm as relayed"*, on research's recommendation he ruled at 02:06Z: *"Go with your recommendation"*).** Three changes with one root: (1) `Store.add_edge` is an interface a host IMPLEMENTS, not a write API a host CALLS — stated in §4a-iii, in 0006 v10 (rule 10, I16) and in `docs/api.md`, a limit and not a gate (the `require_source_id` bypass at `add_edge` keeps the statement; the doctor's `sources` check sees that record; the silent case below got the mechanism); (2) `Provenance` is a FROZEN model (V-PROVENANCE-FROZEN): the residual V-TWO-PRODUCERS named since v19 — a stamp minted through an attribute chain the sweep could not see — no longer exists, because ordinary assignment on a built `Provenance` raises; the EIGHT src sites that mutated a provenance (research counted seven; an augmented assignment in `lifecycle.py`'s decay path was the eighth, found by the AST sweep that now guards the property) replace the object with a copy, the edge keeping its identity; (3) every procedural record written by this version carries WHICH product path minted it — `Provenance.producer` ∈ {`host`, `extractor`}, EXACT_EQUAL in 0014's partition beside `record_kind`, absent on every declarative record (bytes unchanged) and on procedural records from before the stamp (the unstamped era; never guessed) — immutable on same-id replace, inherited across a supersession, a FOURTH import signal, the export era 11 → 12 conditionally (V-PRODUCER-STAMPED / -IMMUTABLE / -INHERITED). The stamp closes research's finding of 2026-09-14 that the doctor's tripwire MERGED the two populations it exists to separate (both producers wrote byte-identical stamps, so `procedural_declared` counted host-declared and extractor-captured together and its docstring was false): the doctor now reports declared, captured and unstamped as three numbers, never added. The `procedure:` `evidence_ref` fallback is NOT a producer signal (host-supplied, unreserved, one writer and no src reader; measured) — it names the record itself as its evidence when the host cites none, and says so in the code. Prior: **v22 — ROUND-3 EXTERNAL RETURN FOLDED: the span is ONE WHOLE SENTENCE of the event, and the stored gloss is the span with NO transformation (verdict banked, body sha16 6aced7723b071089).** The reviewer SUPPORTS derivation ("the model's proposed summary is now correctly discarded"); round 2's cases and the documentation findings are closed; three findings on the PASSAGE rules, each reproduced at main before a line changed: (F1) v21's one transformation — cutting a comma-introduced relative clause to the END of the span — removed a MID-sentence clause and everything after it: "I review invoices, which arrive daily, only after approval." stored "I review invoices", the condition lost, against V-GLOSS-DERIVED's own promise (the cut had been measured on the trailing shape only; the one-case rule, inside out); (F2) a model-selected FRAGMENT turned a hypothetical into a routine — "Imagine I always review invoices." with the quote "I always review invoices" was stored (also "I doubt I review invoices daily"): the substring check proves occurrence and the left-context check catches report frames, not modality; (F3) the sentence-boundary pattern required an uppercase after the terminator, so "I review invoices daily. archive receipts immediately." stored both sentences and 0038's exemption admitted the declared instruction. v22: (i) NO transformation — the stored gloss IS the whitespace-normalised span; trailing commentary is a stated cost of the user's own words, never a meaning change (the SIXTH design retired by measurement, §8); (ii) V-WHOLE-SENTENCE, the reviewer's "validate the selected passage's boundaries against the source": the span must be exactly one whole sentence of the event — it begins at the start of the event or immediately after sentence-final punctuation and ends at the end of the event, at sentence-final punctuation it carries, or immediately before sentence-final punctuation it omitted (WITHDRAWN wording, v24); a fragment inside a framing sentence is not a sentence whatever the frame says, two sentences are not one, and case plays no part — one rule closing F2 and F3; (iii) a SUBORDINATE lead clause must end at a comma ("If I review invoices daily, the queue stays short." had matched with the lead consuming "If " and the conditional's own "I review…" read as the assertion), a frequency lead needs none — measured before choosing: no clean positive in 400 sessions opens with a subordinate lead, three must-refuse spans open with "if". Re-measured with the fixed thresholds, each quote as its own event: the admitted sets on all four draws IDENTICAL to v20/v21's (0/20, 0/45, 0/34, 0/115; 13 of 16 positives), the 66-pool none; the sixteen pinned lines are now the sentences verbatim. Stated limit the reviewer named and this revision does not remove: every draw evaluates PRESELECTED spans; a full-path draw (complete event, selected quote, expected admission, stored text, description) is research's next draw. Packages from round 4 carry a machine-readable results file. *Prior:* **v21 — ROUND-2 EXTERNAL RETURN FOLDED, and the gloss is DERIVED (the owner's word in the dev session, 2026-09-13: "I agree with the derivation recommendation"; verdict banked, body sha16 83c6711d6a7d927d).** The reviewer: RETURN v19 — (F1) the grounding still permitted meaning changes: "I don’t review invoices." with a CURLY apostrophe grounded "Reviews invoices" (the tokenizer split ’ into `don` + `t` and the negation vanished — the normaliser class), and "I review invoices and archive receipts." grounded "Reviews receipts" (an ordered subsequence crossed the coordination: "keeping words in order does not preserve their grammatical relationships"); (F2) "I request that you review invoices today." became a procedure with `instructions_dropped=0` — a first-person present-tense REQUEST passed the grammar (at v20 too: `request` is a present-simple action head); (F3) three carriers still described the pre-v16 world, and "no stored field holds the span" was an OVERSTATEMENT — with the gloss equal to the quote, `object` holds the sentence. Every finding reproduced at main (v20 + 0027 v12) before a line changed. F1 IS CLOSED BY REMOVING THE MECHANISM, NOT BY A FIFTH APPROXIMATION OF IT: substring (v16) → negative markers (v19) → the positive form (v20) → a predicate-level grounding built, measured and DELETED before landing today — each a better syntactic approximation of a semantic property (polarity, action–object relationships, conditions), none the last. The product now DERIVES the stored gloss from the verified span by rule (Gate 4 as rewritten), and the model's `object` for a procedural triple is DISCARDED: there is nothing to ground, because the product wrote both sides. The derivation, closed and stated: the user's sentence, whitespace-normalised, with ONE cut — a comma-introduced RELATIVE clause from its comma to the end (printing the 16 observed lines showed the commentary a paraphrase used to drop is otherwise ALWAYS stored — derivation inverts that risk, it does not remove it; span boundaries now determine stored text entirely, and the span is the model's) — and nothing else: no contraction expanded, no subject dropped, no inflection. Two designs were tried and REJECTED by measurement before this one: dropping the subject "I" (with contractions expanded first, since a bare drop strands "'ve been…" in 13 of 16 observed positives) produces an IMPERATIVE-shaped fragment ("always run the linter before merging") that describe's frozen executable-detail floor WITHHOLDS — the reviewer's cases and every present-simple positive vanished from describe; keeping the sentence renders it. describe prefixes "recorded from something you said:", so the first-person sentence reads as the quotation it is. CONSEQUENCE, stated where a later reader relaxing the grammar will find it: THE GRAMMAR IS NOW THE ONLY FILTER between a user's sentence and stored text — what V-ACTOR-PRESENT admits is stored near-verbatim in `object` and rendered by describe; "the quote is the payload" is back in a bounded form, bounded BY the grammar (the frame check and the report/directive classes refuse the vendor and third-party shapes). Therefore the grammar also refuses a span crossing a SENTENCE BOUNDARY (two sentences are two assertions). (F2) V-ACTOR-PRESENT refuses a DIRECTIVE head by class (request, ask, suggest, recommend, tell, remind, urge, order, insist, propose, advise, instruct, demand, require, invite, encourage, beg, …) and any SECOND PERSON in the span — measured before choosing: you/your in 0 of 13 clean positives, 0 borderlines, 27 of 101 must-refuse across the first three draws. (F3) item 9's claim is now EXACT rather than narrowed: `object` IS the derived span; no separate copy in `note`, no digest; the render exclusion is the whole protection. The field-consumer row's "registry view byte-identical" corrected; 0038 v6.3 carries the mechanism and the residual in full. `tokens()` normalises typographic apostrophes and restores contracted auxiliaries, and `literals_survive_normalisation()` sweeps every literal set the grammar matches against (research's generalisation; none fail). MEASURED, thresholds fixed and recorded before each run: the grammar's admitted sets on draws 1–3 IDENTICAL to v20's (0 of 20, 0 of 45, 0 of 34 must-refuse; positives 8/9, 2/2, 1/2; borderlines unchanged); DRAW 4 (sessions 301–400; 120 quotes, 118 distinct; 115 distinct non-borderline must-refuse; 3 distinct positives; no borderlines), the second HELD-OUT measurement: 0 of 115 — MET; positives #1 and #81 admitted, #59 ("I've got my French press ratio down to a science…", a stative head) refused — a recall COST on a genuine routine, flagged by research before the run and reported as such, never relabelled. Across 400 sessions the grammar admits 13 of the 16 observed clean routines; the 16 DERIVED glosses are printed in §4a-iii and pinned by a test that regenerates them from the labelled files. The base rate is 16 clean routines in 400 sessions (9, 2, 2, 3 — draw 1 the outlier; draw 4 the most quotes and nearly the fewest positives: 112 of its 120 spans are the assistant's instructions). The pair-labelling research planned for draw 4 is not needed: with no paraphrase to judge, the span label is the whole measurement — a dependency removed from every future round. *Prior:* **v20 — POST-ACCEPTANCE AMENDMENT: V-ACTOR-PRESENT BECOMES A POSITIVE-FORM REQUIREMENT (the owner's word in the dev session, 2026-09-13: "Confirm B; fold as v20 before dispatch"; round 2 of the amendments package was then dispatched at v19 on his word, so v20 lands on main as the next amendment and rides the next package).** On research's reading of v19's held-out failure — the rater's own rubric did not list "thinking of" either; the rater labelled from a CRITERION, while a marker list must enumerate SURFACE FORMS of a semantic property and lags it permanently — the gate now REQUIRES an explicit assertion of current repeated performance instead of accumulating negative markers: after the optional lead clause the span opens with one of THREE enumerated head shapes — present simple with an optional negator or frequency adverb ("I use it to…", "I don't eat meat", "I always run…"), present perfect continuous ("I've been using…"), present progressive ONLY with a frequency marker in the span ("I'm walking the dog every morning") — whose head verb is a lexical ACTION verb: not a modal or auxiliary, not in the cognitive/volitional class (think, mean, hope, plan, consider, want, intend, wish, try, aim, like, love, prefer, need, feel, believe, guess, suppose, wonder, decide, figure, imagine, dream, …), which is matched BY CLASS through the grounding's symmetric stem. The SPAN head decides, never a later clause's (clause-any would reopen "I'm thinking of dedicating a day each week…", the complement construction that defeated v19). Every unenumerated form FAILS CLOSED; the v19 markers are KEPT as defence in depth. MEASURED with the thresholds fixed and recorded in the ledger before the run (0 of 20 and 0 of 45 false admissions — the 31's denominator corrected from 22 by research, the two borderlines being reported without a threshold; recall at least 7 of 9 on the 31; the 51's two positives as a REGRESSION GUARD, not a rate): ALL MET. The 31: 8/9, 0/20, both borderlines admitted (unchanged); the 51: 0/45 — v19's three "thinking of" intentions refuse BY CLASS — 2/2, borderlines #12 admitted / #31 refused (unchanged); the one miss (#20, "I've been trying to recognize bird calls…") is refused by class, exactly as research predicted on the record before the number existed, so 8/9 is the ceiling under a span-head grammar. Both sets are DESIGNED-FROM for v20 (research's cost note named positives from each): a REGRESSION measurement, not a held-out one; the third draw (sessions 201–300, held unrevised and unsent until the run was reported done) is the held-out measurement, with research's disclosure that it read the v20 design, including the excluded verb list, before labelling it. DRAW 3 (sessions 201–300, the HELD-OUT measurement, threshold stated before the run): 0 of 34 admitted — MET; recall 1 of 2 exactly as research predicted (#20 "I've been trying to post…" refused by class); borderlines #21 refused, #23 admitted, #38 refused. COST, stated and measured for occurrence: a lexical "do" head and a present perfect without "been" are refused — real in English, ZERO occurrences in the 121 labelled spans of three draws, so unmeasurable here; a bare progressive ("I'm building a deck") refusing is the project/practice distinction working, not a cost; the "just" trigger is unexercised, not validated. CAVEAT bounding every recall figure: 11 of the 13 clean positives across three draws are present-perfect-continuous, the present-simple branch has been exercised by two spans in 300 sessions, and that concentration may be the probe's (a model asked to quote "how the user does something" surfaces "I've been X-ing"), so recall on present-simple host traffic is essentially unmeasured; designed-from (8/9, 2/2) and held-out (1/2) figures are never pooled. The base rate is corrected to ~13 clean routines in 300 sessions (draw 1 the outlier). The realistic capture yield stays small. *Prior:* **v19 — ROUND-1 EXTERNAL RETURN FOLDED (the amendments line; verdict banked, body sha16 c1efcff1a0e8e467) + research's pre-seal red team of the closure.** The reviewer: RETURN 0037 v18 — (1) the quote can be genuine while the SUMMARY is unrelated ("I drink tea after lunch" quoted, "reviews invoices regularly" stored and attributed); (2) a declared one-time instruction still becomes a procedure; (3) the extractor path skipped the summary normalisation and the 512 bound the host path enforces; (4) operative clauses still described v15. Research's red team of the planned closure, all reproduced or executed by dev: `correct()` RENDERED the verbatim quote of a captured procedure (a successor minted without the stamp; the note held the payload) — a render defeat on shipped 0.24.0 by one host action; a tight span inside a quoted third party speaking in the first person passed the grammar; bag-of-words grounding admitted a negated or reordered gloss and a conditional made unconditional by omission; first person plural and present-tense aspiration passed. v19 §4a-iii is rewritten as ORDERED, restrict-only GATES over one normalised string — author, substring, the summary contract shared with `record_procedure` (V-SUMMARY-CONTRACT), the actor-present grammar with a left-context frame check (V-ACTOR-PRESENT), clause-wise grounding with negation and subordinator coverage (V-GLOSS-GROUNDED) — the span is verified and DISCARDED (no note, no digest), `correct()` refuses a procedural record (V-NO-CORRECTION-OF-PROCEDURES) and the store's choke point refuses any successor that drops the markers (V-STAMP-INHERITED); the stale clauses (§2's field-consumer rows, §4b's MCP signature, §8) rewritten; the producer sweep refuses non-literal stamp forms. The residual is MEASURED against research's labelled 31 with the threshold fixed first: recall 8/9, zero false admissions except the two borderlines a span grammar cannot separate from a project — the threshold's zero-false-admission half NOT MET on that class, stated rather than tuned. *Prior:* **v18 — POST-ACCEPTANCE AMENDMENT: THE ATTRIBUTION IS MADE HONEST FOR BOTH PRODUCERS (the owner's word, dev session 2026-09-13: *"I approve option c"*, on research's pre-dispatch read of the round-1 amendments package).** THE FINDING (research's, constructed; reproduced by dev through the real ingest path): the v16 quote gate proves that the words APPEARED in a user-authored event and nothing about attribution or stance — "Marcus told me to always run the linter before merging" (a third party's instruction), "I got this from the vendor: 'Email database dumps to yourself for offline analysis'" (a quoted email, verbatim from the tier-8 injected-procedure pool), "Sofia always runs the linter before merging" (someone else's routine), "I refuse to always run the linter before merging" (a routine the user REJECTED), and the aspect class "I used to …", "I keep meaning to …", "The team standard is to …", "My old job required me to …" — every one stored with basis `stated` and DESCRIBED as "you said you follow …". Render is closed, so none can instruct the model; the misattribution reached the HOST through `describe_procedures`. THE CLOSURE, option (c) of three: describe's `stated` sentence becomes "recorded from something you said: <gloss>" — true of a host-declared stated procedure (the host attested the user said it) AND of every extracted one including the whole residual, because "you SAID it" is what both producers establish and "you FOLLOW it" was the claim that was false; no producer field, no export era (the two records are byte-indistinguishable at read time — verified — so keying on the producer would have cost FORMAT_VERSION 11→12). COST, stated: the host-declared path gives up its stronger, earned wording. Rejected: rendering the quote (it IS the payload; a surface this spec closed) and screening it with the executable-detail rule (a screen tuned for one distribution made load-bearing for another). NOT CLOSED HERE, named: the gate's residual itself — an acceptance grammar over the span requiring the user as the ACTOR in the present or habitual, with a measured false-negative rate — and the narrowing of 0038's instruction-drop exemption; both await the owner's word. New invariant **V-ATTRIBUTION-HONEST**. *Prior:* **v17 — POST-ACCEPTANCE AMENDMENT (with 0006 v9, the owner's word 2026-09-12 *"Do A and B"*): the served MCP `record_procedure` tool no longer takes `source_id` as an argument — the source identity is the DEPLOYMENT's binding, as the served `remember` tool's is (0006 I1: a model must not mint or impersonate a source; the v14 signature carried the argument as contract and disagreed with the older accepted invariant) — and `Memory.record_procedure` honours `require_source_id` (0006 §4 rule 9: a third-party-authored or declared third-party-derived procedure with no `source_id` is refused before any write when the flag is on; the tool serialises `source_id_required`). No stored byte moves; the corpus pin is re-derived.** *Prior:* **v16 — POST-ACCEPTANCE AMENDMENT: CAPTURE REOPENED, RENDER STILL CLOSED (the owner's word, dev session 2026-09-12: *"0037 procedural capture reopening"*, on research's proposal in its repaired §2a form).** The extractor may RECORD a routine the user EXPRESSED; it may not CONCLUDE one — and the line is mechanical, never a field the model fills. A procedural relation is now IN the prompt vocabulary (V-EXTRACTOR-BLIND is REPLACED by **V-EXTRACTOR-QUOTE-GATED**); a procedural triple must carry `quote`, the verbatim span of the event text in which the user states the routine; ingest verifies the quote against the event text it already holds; a verified quote from a USER-authored event DERIVES basis `stated`; a missing, empty, paraphrased or unverifiable quote, or an event the user did not author, is REFUSED and COUNTED (`procedural_refused`), never filed as `unclassified`, never stamped (§4a-iii). Why this answers F1 rather than overruling it: F1 rejected the extractor DECIDING kind and basis; here the registry still decides kind (the relation's declared kind, as before) and ingest DERIVES basis from evidence the model can only POINT AT — the 0031 shape, the host's text attests and the model may only locate. `inferred` does not exist and is not addable; `observed` stays host-only. V-ONE-PRODUCER becomes **V-TWO-PRODUCERS**: `record_procedure` (host-declared basis) and the quote-gated extractor path (derived basis) are the two stampers, the CLI still cannot produce. The prompt-byte identity property is replaced by its converse (a registered procedural relation IS rendered). RENDER IS UNTOUCHED: the stored rule excludes the record at the choke point exactly as before, the four enforcement sites and their tests stand, and §4a-iii forbids reading this amendment as a step toward rendering. 0038 v6.1 (the instruction-drop rule exempts the verified procedural carrier) and 0025 (two public result keys, `procedures` and `procedural_refused`; the selectable set is again the effective registry minus `unclassified`) are amended alongside; the corpus pins are re-derived. Motivation, research's ablation (2026-09-12): users state routines and the extractor flattened them into completed events ("I've been preparing the raised bed by adding a 2-inch layer of compost" → `added 2-inch layer of compost`), a fidelity loss at capture, not a learning feature. *Prior:* **v15 — IMPLEMENTED 2026-09-08, with research's four post-acceptance amendments folded (candidate `100d00699e40abb9`) and the corpus at amendment 7.** Stages 1–3 ship: `Relation.relation_kind` and `follows_procedure`; `Provenance.record_kind`/`basis` with the keys ABSENT when None (a declarative record's bytes are its previous eight keys); `EvidenceContext.direct(basis=)`/`derived(X, basis=)`; `Memory.record_procedure` (the sole producer, in `src/veracium/procedures.py`) and `Memory.describe_procedures`; the model-context exclusion at the gate, recall's selection, the briefing and the wiki compiler; export format 11 stamped conditionally with the raw three-signal import boundary and the restore round-trip; the two MCP tools. Evidence: every §6 node exists by the name the table cites in `tests/test_0037_procedural.py`; the 972-cell corpus consumed whole through the shipped surface under both principals (972/972); the recognition rule's opener and step-marker sets DERIVED from the frozen texts (22/22 must-match; 0/32 paraphrased and plain; 0/5 must-not-match by name). Four things the accepted text got wrong were found at implementation and are corrected by the amendments folded here — §6a cited frozen procedure texts that had never been authored (now the sibling `tests/eval/procedural_describe/FROZEN_TEXTS.json`, sha256 `cddd9078a1fbaadba4d7dd191d3221364286d2fe54d8e6c86089b2a7e25601c4`); §4 called the `{ok, refusal}` tool-result shape existing (it is new, for the two new tools only); §2c attributed the `when` refusal to `as_utc_required` (the surface's own gate); the extractor rows said an emitted procedural name is dropped with nothing written (0025 files it as `unclassified`; the guarantee is the stamp and the prompt, not storage) — and a fifth in the corpus itself: the hand-filled boolean `expect_absent_from_both_recall_blocks` was wrong for the 108 visible declarative-kind control cells, and amendment 7 replaces it with a `recall_expectation` DERIVED from kind_state × visibility (810 absent by kind, 54 absent by visibility, 108 render as today), the expectation moving because the corpus disagreed with THIS spec's unstamped rule, which predates the freeze — never because the code did something. Fourteen hand-maintained inventories elsewhere in the suite met their new member at implementation (the disclosure-writer inventory, the Provenance field partition, the MCP tool set at two sites, import call-site dispositions, the read-surface manifest, six format-version pins, the closed absorption-side schema, the extractor's rendered vocabulary): the gates working, and the same class as the corpus column. **v14 — a POST-ACCEPTANCE PROSE CORRECTION on the owner's word** (Quentin, 2026-09-07: *"go ahead and correct the 0037 §8 reference"*). **The frozen invariant surface is untouched** — nothing in §2–§7 or the §6 table moves. §8's residual paragraph no longer points a reader at a render-site shape refusal, a mechanism research's Q6 measurement retired the day after acceptance (the carriers hold reported speech, not imperatives: 0/204 summaries dropped attribution, 66/66 bare imperatives gained one; an imperative-shape rule at 6.4% on real summaries against 94% on constructed input; `Edge.note` verbatim once in 204) — the residual is stated at its measured size, the worst form named (a fabricated speech act under intact provenance, spec 0038's subject), and the sentence that opened with a complementizer and read backwards to a skimmer now leads with the assertion; §10 Q6's row marks its scoping record as history. Research's wording, adopted verbatim; peer-tree artifacts described, never named. The corpus is re-pinned once (amendment 6, `spec_pin` only) because any edit beyond the digest line moves it — the binding working. *Prior:* **v13 — ACCEPTED at external round 5, 2026-09-07.** Verdict verbatim: *"Verdict: ACCEPT 0037 round 5. … No remaining 0037 specification blocker was found."* **ACCEPTED PACKAGE IDENTITY:** `0037-round5-review-package.tar.gz` sha256 `78a20446b085d7999c14957d373d9793817c0743ffa362665defa043b1094527`, 8,482,115 bytes, 628 members, pinned at `ae6be7687ac77a73da7d232722a7bfb629434447` (v13 + research's corpus amendment 4), CI 34067972232; verdict banked `outbox/0037-round5-verdict-verbatim.md` sha16 `1d72bd0517062a7b`. **THE FROZEN INVARIANT SURFACE, in the reviewer's words:** *"The revised design now requires all three classification signals to be evaluated on the original incoming record before normalization: Format stamp · Basis declaration · Receiving registry classification"*, and *"The eight-case decision matrix is complete and consistent. A newer format stamp or basis declaration causes record-level refusal regardless of the registry result, while registry classification governs records containing neither declaration. This prevents normalization from erasing evidence needed for the decision."* Those two — **the three raw signals evaluated before normalization, and the eight-case marker × registry matrix** — are the frozen surface; they do not move without a new external round. **THE GOVERNING RULE FORWARD:** a record's kind is the registry's declaration AT WRITE, stamped on the record; every kind-dependent READ takes the record's own stamp or basis, never the active registry; IMPORT evaluates three raw signals before normalization and refuses per record, naming the signal; and the corpus at `tests/eval/procedural_describe/MANIFEST.json` is bound to this spec by digest in **both** directions, enforced by the suite. **INDEPENDENTLY REPRODUCED, FIRST TIME IN THE ARC:** the reviewer ran the suite themselves — *"Independent offline run on the recorded Python 3.12.3 / SQLite 3.45.1 runtime: **2,714 passed, 33 skipped**"* — **their figure on their profile, not ours** (our fresh-clone capture at the pin is 2738/9 under `[dev,mcp]`; the 24-test delta is extras their runtime lacks, and research reproduced 2709/31 offline without `mcp`, which is what identifies the cause). For four rounds the verdicts had said the suite *"could not be independently run because the available Python runtime lacks `pytest`"*, disclosed each round in the same words precisely so it could not soften into an assumption; it is now closed by execution rather than by disclosure. **ONE NON-BLOCKING, UNRELATED:** `tests/test_0031_phase_a.py:635` computes "tomorrow" from local civil time against a UTC implementation clock and can fail in the evening UTC-date overlap in western zones; `TZ=UTC` is clean. Test-only, 0031's, tracked separately. **THE ARC:** five external rounds in a single day (2026-09-06 → 09-07), thirteen spec versions, four corpus amendments, twenty disclosed predecessor identifiers — one held stage (`c0ff6cde`, CI 34047051944: staged as 0033, HELD before any seal when 0033 proved reserved for another arc's externally reviewed decomposition, renumbered on the owner's word), three seals discarded at the round-1 pin (`bfde77a0`, `f77382d5`, `6e1c249e`), one superseded-never-dispatched at round 2 (`7ca36268`), and four dispatched-and-returned rounds. **NONE OF IT WAS INSTABILITY: every entry was caught by one of the two seats, or by the reviewer, BEFORE anything shipped.** The findings crossed seats in both directions and that is the record worth keeping — research's pre-seal pass caught v11 asserting a serialization property pydantic does not have; dev's leg caught research's `seal_check` firing on the English word "placeholder" in a README that had to narrate that very defect; research's mutation testing caught dev's pin suite passing a self-consistent WRONG exclusion rule, and dev's count caught research's own leg reporting GREEN with the disclosure audit never executed. The external reviewer caught what neither seat could: a corpus encoding 486 cells in a value the field's type cannot hold (research's), and a format-10 cell pinned at the one relation where every implementation agrees (research's again) — **both instances of a control that cannot fail, found by varying an axis the author had held fixed.** *Prior:* **v13** — the EXTERNAL ROUND-4 fold (verdict RETURN for revision, 2026-09-06, banked `outbox/0037-round4-verdict-verbatim.md` sha16 `49e382c07d0d058f`; package `35f2f782…` @ `07d28a5`; all ten round-3 items named closed). ONE blocking finding, reproduced at v12 §2c and §4e: the format-10 special case STRIPPED `record_kind`/`basis` as newer-than-declared BEFORE the three-signal classification, leaving only the registry signal — a format-10 file carrying a procedural marker under an unknown or declarative relation would have imported as declarative, contradicting "any of three independent signals" and "a foreign procedural stamp is never neutralized by the receiving registry". "Removing a trustworthy field because it is newer than the declared format is reasonable; forgetting that the unexpected field was present is not." Resolved by the reviewer's second option: the three signals are evaluated on the RAW record, BEFORE any version normalization; a raw marker refuses that RECORD naming the raw signal; only admissible records are then normalized; refusal is record-level, never file-level (§2c, §4e, V-IMPORT with the strip-before-inspect mutant); the reviewer's 8-cell marker × registry matrix replaces the single format-10 cell (§2c, §6a; research's amendment 4). Corrections: record-vs-file stated; V-IMPORT says raw-record evaluation in those words; §4a's heading renamed — the registry decides new local writes, the record's stamp/basis decides stored interpretation, three raw signals decide import; the corpus-validation wording is the narrower, accurate form everywhere (domain validation now, real `Provenance` construction after implementation). *Prior:* **v12** — the EXTERNAL ROUND-3 fold (verdict RETURN for revision, 2026-09-06, banked by RESEARCH — the receiving seat this round — `outbox/0037-round3-verdict-verbatim.md` sha16 `e2e2d761c73b9b16`; package `20f778c7…` @ `3a19897`; "the package evidence is now well formed"; nine round-2 items closed). Three blocking, four corrections, each reproduced at a line of v11 and folded. **F1** the stamp's type `Optional[Literal["procedural"]] = None` has domain `{None, "procedural"}`, yet §2c's conflict state compared `record_kind == "declarative"` — a value the field cannot hold — and 486 of the corpus's 972 cells carried that string: the SEMANTICS were right and the REPRESENTATION wrong (an axis label serialized as if it were the stored value); now the four states are stated once in the field's own terms (§2c, §4a): `None ∧ basis None` → declarative; `"procedural" ∧ basis` → procedural; `"procedural" ∧ basis None` → `basis_unknown`; `None ∧ basis not None` → `kind_conflict`, procedural by floor; every "declarative stamp" phrase is rewritten as the ABSENCE of a stamp; the corpus is amended to JSON `null` and rebound, and every row is validated through the declared domain (`tests/test_0037_corpus_pin.py`, V-CORPUS-ROWS-IN-DOMAIN) — at implementation, through the real `Provenance`. **F2** default import treated a record as procedural only by stamp or basis, so a foreign record with BOTH stripped under a relation the receiving host registers procedural would have entered recall: now the import boundary refuses on ANY of THREE independent signals — stamp, basis, or the RECEIVING registry's kind — naming which fired, with the six cells the reviewer asked for stated (§4e, §2c, V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE). **F3** "the format version is unchanged; a v2 reader ignores it" DEMONSTRATED the failure: an old reader would ignore both keys and render a procedural record as declarative. The shipped 0026 §3d precedent is the boundary — `FORMAT_VERSION` 10 → 11, stamped CONDITIONALLY at write (any procedural record in the export → 11, which every older reader REFUSES at `portability.py:291`; a procedural-free export stays 10 and byte-compatible), with an executable old-reader test (§4e, V-OLD-READER-REFUSES). **Corrections:** "excluded BY RELATION KIND" → by the record's own stamp/basis rule wherever it was a use (field table, §3, §4a, V-OUT-OF-PATH); "every writer stamps declarative" → declarative writers leave `record_kind=None` and the key is omitted; restore's two absence dimensions both defined (a procedural signal with inconsistent markers is MALFORMED and refused per record); corpus row-schema validation added. **Disclosed for round 4:** the reviewer could not run the suite (no `pytest` in their runtime) — "2737 passed, 9 skipped" is our capture reported back, not an independent reproduction; the round-4 README says so. *Prior:* **v11** — the EXTERNAL ROUND-2 fold (verdict RETURN for revision, 2026-09-06, banked `outbox/0037-round2-verdict-verbatim.md` sha16 `80dd0d14fefb60d2`; package `a5161719…` @ `18d05f7`). Eleven round-1 findings named closed; the revocation treatment "strong and necessary". Four spec blockers, one package defect, six gaps — each reproduced at a line of v10 and folded. **F1** `record_procedure` derived `author_of_evidence` FROM THE CONTEXT (USER for `direct()`, X for `derived(X)`) — authorship conflated with derivation; `derived(SYSTEM)` means derived-from-system, not system-authored, so system/assistant procedures were unrepresentable → a separate `author` argument; `author_of_evidence=author`, `derived_from=context.derived_from`, `basis=context.basis`, disclosure from all three under the shipped rule; ONE canonical signature (§2, §4a, §4b); author × derived_from × basis in the oracle with V-PROVENANCE-AXES (the carriers cannot substitute). **F2** the unregistered-relation remedy withheld LEGACY CUSTOM DECLARATIVE edges from recall — a behavioural regression the disclosure did not cure and Q7's signal did not address → the declared kind is STAMPED ON THE RECORD at write (`Provenance.record_kind: Optional[Literal["procedural"]] = None` — ABSENCE IS DECLARATIVE, and the key is OMITTED when None by a wrap-mode `model_serializer` on `Provenance`, the form `Edge` already uses at `schema.py:519`; executed against pydantic 2.13.4 with the deliberate nulls preserved and the control without it emitting `"record_kind":null` on every record — research's pre-seal pass caught v11's first draft asserting "serialized only when procedural" with no mechanism, the class both prior rounds found here) and READ FROM THE STAMP, never from the registry, for stored records: kind is total over stored records; a registry change moves nothing; an unregistered relation with a declarative stamp (every pre-feature record, every legacy custom relation) keeps TODAY'S behaviour exactly; only a procedural-stamped record can be `relation_unregistered`; a record is procedural iff `stamp == procedural OR basis is not None` — two independent write-time facts must both be destroyed to launder one record (research's ruling: the failure direction decides, not the cost) — and the disagreeing state (declarative stamp WITH a basis) is the NAMED outcome `kind_conflict`, procedural by floor, never a silent inference (§4a, §4a-ii, §4c, §7, V-KIND-STAMPED replaces V-KIND-REGISTRY, V-RELATION-UNREGISTERED narrowed, V-CARRIERS covers the stamp). **F3** the frozen corpus was in research's tree, not the package → it lives IN THE REPO at `tests/eval/procedural_describe/MANIFEST.json`, byte-copied from research's amendment against THIS version, its sha256 on the one line `corpus sha256: …` in §6a (the line the manifest excludes before hashing the spec — a bidirectional, non-circular binding), and `tests/test_0037_corpus_pin.py` pins file to digest (data to data) so the binding is executable before acceptance. **F4** the CLI `--basis` line was a second producer or a rejected path → CLI support REMOVED from v1; `cli.py` is classified cannot-produce in V-ONE-PRODUCER's sweep. **Package defect** (dev's): `collected/COLLECTED.txt` shipped the capture script's placeholder line beneath the real disclosures — the digest-agreement check could not see a sentence; the capture no longer writes one, the assembly refuses the placeholder FORM in any carrier, and research's verifier gained ASSERT-15 (the same sweep with a planted negative control). **Gaps:** `limit` validated (§4a-ii); every argument's validation stated (§2c, §4b); library EXCEPTIONS and MCP SERIALIZED results stated as two layers (§4 head); §4a's stale "Q6 blocking for Quentin" corrected; "fully reversible" narrowed to what holds (§7). *Prior:* **v10** — the CORPUS-FREEZE fold (2026-09-06): research froze the acceptance corpus against v9 by GENERATING its cells from §4a-ii's ordered predicate and raised three OPEN questions instead of guessing; each is a v9 defect of the class round 1 found (an outcome named that the contract cannot reach), so the sealed-but-undispatched round-2 package `7ca36268…` @ `8a18738` is SUPERSEDED by this version (disclosed, never dispatched) rather than sent with known findings — the batch rule. (1) `quarantined` was UNREACHABLE as written: `_disclosure_for` yields it only for `third_party_claim`, and v9 said nothing about a standing-revoked `source_id` — so `record_procedure` as specified was a REVOCATION BYPASS ON A NEW WRITE SURFACE (research's words, verified at `ingest.py:227-230`, `:388-395`, `revocation_sweep.py` RECOMPUTED_FIELDS): a host writing a procedure from a revoked source would get `mentionable` where `ingest_event` gives `quarantined`, on a path the resurfacing probes (96/96) do not cover because the surface did not exist when they were written. Now `record_procedure` applies the birth-quarantine rule exactly as `ingest_event` does (V-BIRTH-QUARANTINE-HOLDS), which is `quarantined`'s ONE route for a procedural record, named (§4b, §2c, §3). (2) `not_procedural` was unreachable AND self-contradicted (candidates were "procedural records", yet it was the first failing conjunct): the candidate set is now stated ONCE — visible edges whose relation is registered procedural OR unregistered; declarative records are never candidates — and `not_procedural` is REMOVED from the literal, with a control cell that declarative records appear in neither list (§4a-ii). (3) disclosure is DERIVED, so `author × disclosure` is the diagonal, not a free product: §6a carries `disclosure_derived` as a computed column and admits a disagreeing cell only as a row written directly and LABELLED corrupted-state. Research amends the corpus by superseding digest against this pin. *Prior:* **v9** — research's PRE-SEAL PASS on v8 (2026-09-06; batch rule), three items, all landed: **F-A** the one-result-per-visible-candidate accounting BROKE under truncation (a describable record ordered below the cap was in neither list — exactly on the population V-DESCRIBE-ORDER exists to test) → `DescribeResult` gains `total_describable: int` (the describable population BEFORE the cut) and V-RESULT-SCHEMA is scoped to before truncation, so `total_describable + len(withheld)` accounts for every visible record (§4a-ii, §6); **F-B** `relation_unregistered` is NAMED on describe and SILENT on recall — a host that shrinks its registry sees facts vanish from recall with no signal, and V-DECLARATIVE-UNCHANGED does not cover that population (its guarantee rests on the default registry) → said plainly in §4a and §8, §9's alternative weighed against the recall-side silence, and a cheap signal asked as §10 Q7 for round 2; the third homograph sentence restored to its measured literal ("Store the recovery codes in a password manager is what the team does") — a frozen must-not corpus needs the string, not an ellipsis (§6a). Confirmed by research against source, not read: the §6a figures re-derived from the measurement (exact); `_disclosure_for(author, relation, derived_from)` at `ingest.py:141-142`; Q6's wording canonical. Research CLEARS v9 for the round-2 seal. *Prior:* **v8** — the EXTERNAL ROUND-1 fold (verdict RETURN for revision, 2026-09-06, banked verbatim `outbox/0037-round1-verdict-verbatim.md` sha16 `4be410ce697bd171`; package `5d9ac247…` @ `af880b3`). Eight blocking findings, all spec-content, each reproduced at a line of v7 and folded: **F1** the MCP write path contradicted the library contract (`remember(basis=)` could not produce a procedural record without bypassing the sole producer) → a DEDICATED MCP `record_procedure` tool, capability-gated to `direct`, relation validated against the active registry; `remember` on BOTH surfaces rejects any basis (§4b, §4e). **F2** the describe RESULT contract was undefined → `DescribeResult` with a full schema and observable ordering (§4a-ii). **F3** §8 claimed "never reproduces executable detail" beside its own paraphrase limit → the ACTUAL guarantee everywhere: the `note` is never rendered; a summary matching the frozen recognition rule is withheld; a paraphrase passes (§4a-ii, §6, §8). **F4** Q3 unresolved → RESOLVED: research owns the recognition corpus (the 0029 condition: every expectation from the spec's text, OPEN where undetermined), frozen with a version and digest against THIS version before any implementation line, ± sets, change control by amendment, the v1 paraphrase boundary a stated limit (§6a, §10). **F5** §3b's "third-party shape" contradicted the matrix → deleted; a `use_only` procedural record yields the named non-description `use_only`; `hidden` and no-match are INDISTINGUISHABLE to an unauthorised principal, `use_only` and no-match need not be — scope decides whether you may know, disclosure what you may be told; and `withheld` is QUERY-BLIND so an id's presence cannot become a search oracle over a record the principal may not read (research's semantics; §3, §3b, §4a-ii, V-WITHHELD-QUERY-BLIND, oracle cells added). **F6** relation validation missing → `record_procedure` REQUIRES the relation to exist in the active registry with `relation_kind="procedural"`, else RAISES, nothing written (§4b, V-RELATION-VALID). **F7** registry totality overstated → kind is total over the ACTIVE registry, not over stored records; a stored edge whose relation left the registry is the named `relation_unregistered`, excluded from both blocks and from describe, never silently moved — a disclosed behaviour change for a host that shrinks its registry (§4a, §8, V-RELATION-UNREGISTERED). **F8** §5's relevance promise had no invariant → V-DESCRIBE-ORDER (above-cap population, stable ties, repeated runs, the null query). Corrections: `Relation(kind=…)` → `relation_kind` in §4e; the stale "three members" row is 0001 §2c-ii:175 (an as-of note added there, docs-only); ONE failure taxonomy (write-path failures RAISE with nothing written; read-path outcomes are RETURNED, named — §4b); `ProcedureDescription`'s fields and that no raw stored text appears in any field (§4a-ii); how `record_procedure` populates id, dates, evidence_ref, source_id, disclosure (§4b); default import is ATOMIC over the admitted set with procedural records refused per record and counted (§4e); the sibling's governance state stated canonically: the commission STANDS and is formally parked behind a mechanism-selection prerequisite (§10 Q6). Preserved as the reviewer named: host-declared kind; the blind extractor; exclusion from both blocks; `assertable` untouched; basis orthogonal; absence semantics; the lattice; import vs restore; recommendation outside; the residual disclosed. *Prior:* **v7** — **Q6 SCOPED by the owner: option (b), a sibling spec** (Quentin, 2026-09-06, verbatim "Scope Q6 as option b", logged under `[Quentin]`). The free-text render exposure is neither addressed here nor left unaddressed; §8's residual disclosure stays exactly as it is, which is what makes the deferral honest rather than silent. The sibling's SCOPE is recorded in §10 so it does not live in a conversation; its COMMISSION has NOT been granted (the owner's word was "scope", not "commission" — the distinction research held to). Why (b) and not (a), inherited by the sibling: (a) would have changed SHIPPED declarative behaviour — content recall returns today would stop being returned — the hazard class this spec avoided by scoping `basis` to procedural records, ridden in on a commission scoped to procedural records only; and the exposure PREDATES this spec and is not created by it. The internal round is complete from both seats; this version proceeds to external review. *Prior:* **v6** — Q6 RESHAPED on research's semantics (2026-09-06, before the commit): an episode is not a procedure but the record that one was mentioned (`Episode`'s own contract), so v1's answer stands — no procedural episode type; refusing or deleting the episode would destroy true history to hide text. But the exposure is not where Q6 put it: it is FREE TEXT RENDERED VERBATIM INTO MODEL CONTEXT, and there are at least two carriers — an assertable episode's `summary` (`gate.py:137`, the probe) and an assertable declarative edge's `note` (`graph.py:1116`, straight into `render_edges` and the grounded block) — so an episode-side kind would close one door and leave the sibling open, F2's partial-fix shape. Research's recommendation, carried into Q6 for Quentin: apply the imperative-shape refusal to free text AT THE RENDER CHOKE POINT V-RENDER-SITES already enumerates, for any record type — no new host field, completeness checkable by the existing sweep, claimed as a FLOOR (reduces, never closes: the text was never authored as a procedure). The trusted path this sits on is already measured (research: `user_attested_inference_framing` 0.42 [0.30, 0.55]; `controls` 0.667), so Quentin scopes it with the shape on the table. *Prior:* **v5** — the §6/§6a internal-review fold (research, 2026-09-06). **F4 (BLOCKING)** — EPISODES were not mentioned once: they reach model context on their own path (`gate.py:106` `partition_parts` returns `ep_lines` and `tp_ep_lines`), ordinary ingest writes one beside the edges, and an episode has NO relation — so "excluded by kind" could not see it (F2 through a door the kind check cannot see). PROBED, not argued: procedural text through ordinary `remember` with a scripted extractor produced ZERO edges and ONE episode, and recall's context carried the executable steps verbatim (§8, the measured residual). v5 settles all three cases: `record_procedure` writes NO episode (V-NO-EPISODE); ordinary ingest's episode path is TODAY's behaviour, unchanged, stated as the residual with the probe; whether v1 must ALSO govern procedural text arriving through ordinary ingest — which needs a host-declared EPISODE kind, a larger change — is §10 Q6, blocking, for Quentin. The edge-side concept is renamed `relation_kind` because `Episode.kind` already exists (`interaction | outcome`). **F5** — the `stated`/`observed` ORDER was never declared while two invariants leaned on "whole-set minimum": declared now beside the field — the lattice is `observed ≤ stated`, `observed` is the minimum, so absorption can only ever yield `observed` from a mixed set (the only order consistent with V-BASIS-CAP-ONLY). **V-CARRIERS** made derivable: the sweep basis is every `Provenance(` constructor and `model_copy(update=` site (both forms — 0016's tenth-site lesson) and every `provenance.` reader, never the hand list v4 carried. *Prior:* **v4** — research's correction of its OWN F3 recommendation (2026-09-06, before the first commit): "refuse on both paths" was too broad. `portability.py:21-30` defines `restore=True` as the operator's explicit assertion that the file is THIS store's own history — precisely the attestation `basis` requires — so refusing there costs backup fidelity for no trust gain and loses every procedural record of a store's own backup, silently to anyone not reading the refusal count. v4: the DEFAULT path refuses (the relay reading holds exactly); `restore=True` ACCEPTS the record with its declared basis; the invariant becomes V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE with the restore leg as a POSITIVE case (a refusal-only test would pass while backup/restore was broken). §8 names the precedent extended: the house has two moves for a field an import will not honour — CAP it (author/derived_from → THIRD_PARTY) and DROP the key (`source_type`, ≤v6 files); refusing the whole record is a third, stronger move, taken on the default path only. *Prior:* **v3** — the second internal-review fold (research, 2026-09-06, before the first commit): **F3** — `record_procedure` was NOT the sole producer at the store layer: `commit_outcome_import_plan` writes edges directly (one of the seven sites in 0029's own `EDGE_WRITE_SITE_RULINGS`, checked against the registry rather than the API surface), so an import could introduce a procedural record carrying a basis DECLARED BY A DIFFERENT HOST — 0026's relay shape, and a collision with §4b's "basis is a positive capability THIS host declares"; harmless while both bases are merely describable, a laundering route to recommendation the moment §4d's composition exists. v3 takes the first of three ways out: **import REFUSES procedural records** with a named outcome (`procedural_import_refused`), §8 states the limitation, and V-ONE-PRODUCER becomes true rather than reworded. V-ONE-PRODUCER's sweep basis is now 0029's registry × the raw-SQL sweep, never a fresh inventory (a second list of edge writers is the hand-list 0029 already paid for). *Prior:* **v2** — the §3a internal-review fold (research, 2026-09-06; two BLOCKING findings at the conclusion, both verified in code, both taken; Q1 ruled). **F1** — the extractor DECIDES KIND TRANSITIVELY by choosing the relation (`ingest.py:169` passes the registry's names into the extraction prompt), and with basis REQUIRED that made every extractor-emitted procedural edge a silent refusal fleet-wide through the DEFAULT registry — the declarative fail-closed hazard arriving by another door. v2: procedural relations are FILTERED OUT of the extractor's vocabulary at the extraction boundary, so the extractor can never emit one; procedural capture is an EXPLICIT host surface that carries basis (`Memory.record_procedure`). Kind is host-declared end to end, not only in principle. **F2** — `assertable=False` is a ROUTING signal today, not suppression (`gate.py:139`: not-assertable renders as a fenced third-party claim, Q5), so overloading it with "is procedural" would render a procedure as a fenced claim at every site v1 missed — the Tier 8 failure mode. v2: `Edge.assertable` is UNTOUCHED and type-correct; procedural records are excluded ONCE, BY RELATION KIND, at the recall/partition choke point, with a named outcome, and a V-TOTAL-style sweep derives every model-context render site and proves each reaches that choke point. **Q1 ruled (research, from the Tier 8 competitor arms, 0.25–0.90 guidance rates for procedural content that reached the answerer's context):** procedures are excluded from the UNVERIFIED block too, and §4a carries the sentence that keeps a later reader from "fixing" it by symmetry with Q5. **§8** now claims `executable_detail` as a FLOOR, not a guarantee: a paraphrase defeats it. *Prior:* **v1** — the candidate, 2026-09-06. |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (requested 2026-09-06) · dev (author; may not self-approve) · workflow-platform unavailable (no such session exists this arc; recorded as the waiver, holder Quentin) |
| **External review** | **round 5 sent 2026-09-07 (package `78a20446…` @ `ae6be76`, CI 34067972232) and ACCEPTED the same day** — the reviewer ran the suite (2,714 passed / 33 skipped, their offline profile); round 4 sent 2026-09-06 (package `35f2f782…` @ `07d28a5`, CI 34061355491) and RETURNED the same day: RETURN for revision, one blocking + five corrections, all round-3 findings closed; round 3 sent 2026-09-06 (package `20f778c7…` @ `3a19897`, CI 34058517574) and RETURNED the same day: RETURN for revision, three blocking + four corrections, nine round-2 items closed, "the package evidence is now well formed"; round 2 sent and returned the same day (`a5161719…` @ `18d05f7`); round 1 sent 2026-09-06 (package `5d9ac247…` @ `af880b3`, CI 34049009899, both seats' legs green) and RETURNED the same day: RETURN for revision, eight blocking + seven corrections, "strong overall architecture" — folded as v8; round 2 after research's pre-seal pass |
| **Decision + date** | — |
| **Path** | full |
| **Scope** | PROCEDURAL records only. Declarative facts, `Edge.assertable`, recall's grounded/unverified partition and every shipped predicate on declarative records are UNCHANGED. Recommendation (stage 4) for procedural records is NOT specified here (§4d, a stated non-goal awaiting a harness contract). |

---

## 1. Problem and motivation

**The store cannot see procedural content, and cannot see whether such
content was stated or observed.** The relation registry has nineteen
relations and none is procedural (`DEFAULT_RELATIONS`, §2c-ii); the
extractor sends an out-of-vocabulary relation down 0025's residual path
(**v15**: retried once, then filed as reserved `unclassified` at `use_only` —
**written, not dropped**). A procedure —
"whenever a ticket arrives from X, do Y then Z" — therefore arrives as free
text and lands, if anywhere, under a declarative relation, where it is
governed exactly as a fact: `active ∧ ¬quarantined ∧ ¬use_only ∧ valid_now`
makes it assertable, and assertable content is rendered into the GROUNDED
block that a host's model acts on. That is the vacuum the external design
round's reviewer named and research's Tier 8 run measured: on the harness's
`inferred` cell (the speaker reporting *a pattern they observed* — "I have
noticed the team following this: …"), every probe is ingested as an attested
first-party statement, because that is all a host can declare, and the
store passes it at competitor rates (0.42 [0.30, 0.55] under family-level
clustering — **a behavioural observation on identical input, not a
provenance result**; research's correction of 2026-09-06). Two independent
routes reached the same gap: the reviewer's *"inferred procedures require
explicit policy because ordinary user-origin rules do not settle whether an
inferred procedure should be recommended"*, and dev's reading that
user-origin is the wrong axis because both a stated and an observed
procedure are user-origin.

**What happens if we do nothing.** Procedural content keeps entering the
action-oriented path (grounded recall context) with the same authority as a
stated fact, and a procedure the user merely *reported observing* is handed
to the model as something to follow. Under the adopted reference-monitor
model that is the store doing, on the inferred path, what it forbids on the
corroboration path: repetition conferring authority. And there is no way
for a host — or the harness that measures us — to declare otherwise, so the
number cannot move and the gap cannot close.

**The frame this spec adopts (Quentin's ruling 2).** The stage boundary is
content-type-relative. For DECLARATIVE facts stage 4 is shipped and governed
(`Edge.assertable` is stage 4's minimum rule minus the consequence check,
which is meaningless for a fact). For PROCEDURAL content stage 4 does not
exist: it must not be built without its consequence check, and that check
needs a harness contract we do not own. So this spec builds stages 1–3 for
procedural records — store, internal retrieval, DESCRIBE — and leaves
recommendation unavailable by default. An inferred procedure is not less
TRUSTED than a stated one; it is differently GROUNDED. `basis` is that axis.

**Alternatives rejected.**

- *A fourth `Disclosure` tier* — rejected on 0001's own reasoning ("the tier
  was never the problem; the author was"): basis is orthogonal to trust.
  An observed procedure from the user is fully user-authoritative and still
  not something to act on.
- *Carrying "observed" in `derived_from`* — blocked by design (0001, the
  0.1.7 laundering defence): `derived_from` may only cap trust, and
  "observed" is not a trust class of the source.
- *Reusing `needs_confirmation` as the carrier* — it is a RANKING input
  inside the assertable set ("confirm before relying", ranked first; set only
  by a CHALLENGED outcome, cleared only by `confirm_edge`), not a gate; a
  flagged record is still rendered as grounded.
- *Letting the extractor decide procedural-ness or basis from the text* —
  rejected by the round's ruling and by 0031's: that is the model deciding
  provenance. Both are declared by the host.
- *Applying `basis` to declarative facts too* — rejected for v1 by the
  commission's scope and for a reason worth recording so a later reviewer
  does not rediscover it: an observed-basis fact would become
  non-assertable, changing behaviour for EVERY existing edge, and the
  absence semantics for pre-existing records (§4c) would become a fleet-wide
  migration question. Procedural content has no shipped behaviour to
  migrate, so v1 avoids that question outright rather than deferring it
  silently. **Declarative basis is a stated non-goal of v1.**
- *Letting the extractor emit the procedural relation* (v1's shape) —
  rejected at internal review (F1): the extractor decides kind transitively
  by choosing the relation, and with basis required that is a silent
  fleet-wide refusal through the default registry. Procedural capture is an
  explicit host surface, and the extractor was kept blind to the relation (v2–v15).
  **v16 (2026-09-12, the owner's word) REVERSES this with F1's objection ANSWERED,
  not overruled:** the extractor still decides nothing — kind comes from the
  registry as before, and basis is DERIVED by ingest from a verbatim `quote`
  verified against the event text, never declared by the model (§4a-iii).
- *Overloading `Edge.assertable`* (v1's shape) — rejected at internal review
  (F2): not-assertable is a ROUTING signal today (render as a fenced claim),
  and "out of scope for this path" is a different proposition from "not safe
  to state as fact"; one predicate must not carry both.
- *Doing nothing and documenting it* — rejected: two independent reviewers
  reached the gap, and the shipped disclosure (`9baa936`) already says the
  labels are advisory; an advisory label that cannot be declared is not a
  label.

---

## 2. Field contracts touched

Consumers enumerated by command, not recalled (commands in §2c-ii; counts of
2026-09-06).

| field | read / written | its **documented** contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Relation` (`schema.py:350`) — NEW field `relation_kind: Literal["declarative","procedural"] = "declarative"` | registry-declared | "a small, extensible default registry; hosts can add their own via config" | the extractor prompt (glosses) — **v16+: procedural relations are RENDERED in the vocabulary and an emitted procedural triple is admitted only through §4a-iii's gates, else refused and counted** (through v15 they were filtered out of `rel_names` and an emitted name took 0025's residual path); `authority.py` (functional); graph clustering | YES for every existing relation — declarative by default and unchanged; the extractor's view of the registry is NOT byte-identical since v16: it GAINED the registered procedural relations, whose triples reach storage only through §4a-iii (v21 corrects v15's sentence, which the round-2 reviewer found still live) |
| `DEFAULT_RELATIONS` — ONE new relation `follows_procedure` (`relation_kind="procedural"`, non-functional, subject `user`, object the procedure's description) | registry | as above | as above | YES — additive; a host may register further procedural relations |
| `EvidenceContext` (`schema.py:188`) — NEW keyword `basis` on `direct()` and `derived()`, closed domain `{"stated","observed"}`, REQUIRED when the event is procedural, REFUSED when it is not (§4b) | host-minted | 0011 E4: "absence must be a POSITIVE capability, not a missing argument"; the constructor refuses unknowns | `ingest.py` (`_validate_context`, `ingest_event`), `mcp_server.py` (the capability bridge), `Memory.remember` | YES — inherits E4's rule rather than setting its own (§4c) |
| `Provenance` — NEW field `record_kind: Optional[Literal["procedural"]] = None` (round-2 F2): the registry's declaration for the relation AT WRITE, stamped on the record; ABSENCE IS DECLARATIVE — `None` is the declarative value, and a wrap-mode `model_serializer` on `Provenance` (the form `Edge` uses at `schema.py:519`) OMITS THE KEY when None, so a declarative record's bytes are exactly today's 8 keys with their three deliberate nulls (`derived_from`, `source_id`, `origin`) untouched — never a global `exclude_none`, which would drop those; executed on pydantic 2.13.4 (§2c-ii) | WRITTEN once at write: declarative writers (the extractor path, the default import) LEAVE `record_kind=None` and the key is OMITTED — they store no string, there is no `"declarative"` value (round-3 F1); `record_procedure` stamps `"procedural"`; `restore` preserves the file's stamp; READ by every kind-dependent site — the choke point and the describe candidate set read the STAMP, never the registry | a stored record's kind is a write-time fact that a later registry change cannot move | the same carriers as `basis` (V-CARRIERS) | YES — every existing row lacks the key and reads declarative, true by construction (§2c-ii: no procedural relation existed) |
| `Provenance` — NEW field `basis: Optional[Literal["stated","observed"]] = None`, with the DECLARED ORDER `observed ≤ stated` (`observed` is the minimum; F5) | WRITTEN at ingest from the context; READ by the describe predicate | None = "not a procedural record" (absent BY CONSTRUCTION on every declarative record and on every record written before this version); never a default for a procedural record; "whole-set minimum" everywhere in this spec means the minimum under `observed ≤ stated`, so a mixed set yields `observed` — the only order consistent with V-BASIS-CAP-ONLY | export/import (the field serializes; import caps like every trust field — §4e), `adapt` (0030's raw adapter tolerates unknown keys), `contribution` payloads | YES — orthogonal to author/disclosure; cap-only (a host can declare `observed`, nothing can promote it) |
| `Edge.assertable` (`schema.py:528`) | **UNTOUCHED** (F2) | "safe to state as fact" — and today `not assertable` ROUTES a record to the fenced third-party block (`gate.py:139`, Q5) | the 22 call sites 0032 enumerated | YES — the predicate keeps both its meaning and its routing role; a procedural record's assertability is simply never consulted on the model-context path, because that path excludes procedurals by the record's own stamp/basis rule before it asks (§4a) |
| the model-context choke point — `gate.partition` / `partition_parts` (`gate.py:95`, `:123`) and recall's edge selection | procedural records EXCLUDED ONCE, by the STORED stamp/basis rule (`record_kind == "procedural" OR basis is not None`, §4a — never the registry at read), with the named outcome `procedural_out_of_scope` | GROUNDED (assertable) / UNVERIFIED (third-party claims, "fenced not suppressed") | `Memory.recall`, `answer`, `compile`, `proactive`, `selfcheck` — every site that renders records into model context, DERIVED by the §6 sweep | YES — both blocks keep their meaning; a procedure is neither a fact nor a claim, it is out of scope for the path, and the exclusion is one site the sweep can check |
| **THE CANONICAL SIGNATURE (round-2 F1, one place):** `Memory.record_procedure(user_id: str, summary: str, *, author: EvidenceAuthor, context: EvidenceContext, relation: str = "follows_procedure", note: Optional[str] = None, when: Optional[datetime] = None, evidence_ref: Optional[str] = None, source_id: Optional[str] = None) -> str` (the new edge id) — NEW | the HOST-DECLARED producer of procedural records (F1, F3; since v16 the extractor path of §4a-iii is the second, with a DERIVED basis); `author` is the AUTHORSHIP axis exactly as `remember`/`ingest_event` take it; the context carries the DERIVATION axis (`derived_from`) and the BASIS (required — `direct(basis=)`/`derived(X, basis=)`); the three are independent and none substitutes for another (V-PROVENANCE-AXES); constructs the edge directly, never through the extractor; the RELATION must exist in the active registry with `relation_kind="procedural"` or the call RAISES and writes nothing (round-1 F6) | — | new; MCP's `record_procedure` tool is a capability-gated adapter to it (round-1 F1); NO CLI surface in v1 (round-2 F4) | n/a — additive; the import path and the CLI cannot produce a procedural record; the extractor path can since v16, only through §4a-iii |
| MCP `record_procedure` tool — NEW (round-1 F1) | the MCP write path for a HOST-DECLARED procedural record (v16: the served `remember` tool can also produce one through the quote-gated extractor path of §4a-iii, only under `VERACIUM_MCP_CAPABILITY=direct` where the baseline author is the user): `record_procedure(summary, basis, author="user", derived_from=None, relation="follows_procedure", note=None, date=None)` (v17: no `source_id` argument — the deployment's `VERACIUM_MCP_SOURCE_ID` binding is the source identity, as for `remember`; 0006 I1) — `author`/`derived_from` mirror MCP `remember`'s own arguments exactly; honoured under `capability=direct` only, refused under `none` with the same named outcome as an attempted elevation and counted like one; it validates the relation exactly as the library does and calls `Memory.record_procedure(author=author, context=<direct(basis) or derived(derived_from, basis)>)` | host-attested writes (0031 Phase A) | `mcp_server.py` | n/a — additive; MCP `remember` gains NOTHING and rejects any basis like the library path |
| `portability.import_memory` / `commit_outcome_import_plan` (an edge writer in 0029's `EDGE_WRITE_SITE_RULINGS`) | DEFAULT path REFUSES a record as procedural on ANY of THREE independent signals — its stamp is `"procedural"`, OR its `basis` is present, OR the RECEIVING host's active registry declares its relation procedural — naming which fired (round-3 F2); declarative records unchanged; `restore=True` ACCEPTS the store's own procedural records with their declared basis (F3, corrected v4), refusing inconsistent markers as malformed | 0005: "an importing store's knowledge of an edge begins at ITS import"; the default path caps trust; `restore` is the operator vouching that the file is this store's own history | export/import round-trip tests, the 0005 boundary registry | YES — on the default path an imported basis is another host's declaration; under `restore` it is this host's own, re-asserted by the operator |
| `Memory.describe_procedures(user_id, *, query=None, principal=None, limit=None) -> DescribeResult` — NEW | the stage-3 surface; its full result schema and ordering are §4a-ii (round-1 F2) | — | new; MCP `describe_procedures` tool (same shape, JSON) | n/a — additive |

**Documentation stating the old meaning, updated in this change:**
`docs/concepts.md` (the disclosure paragraph gains ruling 2's sentence —
fact recall governed and shipped; procedural recommendation has no governed
type and is not built), `docs/api.md`, `docs/mcp.md`, the `Relation` and
`EvidenceContext` docstrings.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| the host's `basis` declaration on a procedural event | ABSENT → the ingest REFUSES and writes nothing (E4: absence is not a missing argument; a procedural event without a declared basis is a caller error) | not a str, or a str outside `{stated, observed}` → the constructor RAISES (E4's chosen resolution: refusal, nothing written) | — | a host declaring `stated` for content it observed — out of scope for the store (the host attests; 0031's rule) and stated in §8 | **V-BASIS-POSITIVE** (`test_procedural_ingest_requires_a_declared_basis`), **V-BASIS-CLOSED** (`test_basis_domain_is_closed_and_refuses_at_construction`) |
| a `basis` declaration on a DECLARATIVE event | absent — the ordinary case | present → REFUSED at ingest (basis is not applicable to declarative records in v1; accepting it silently would make declarative basis a hidden feature) | — | — | **V-BASIS-SCOPE** (`test_basis_on_a_declarative_event_is_refused`) |
| a stored record whose stamp and basis disagree (DB-level tamper; no shipped writer produces it) | — | a record is procedural iff `record_kind == "procedural"` OR `basis is not None` — EITHER write-time fact suffices, so destroying one cannot launder a procedure into recall (two facts, two mechanisms: defence in depth); the FOUR states, in the field's own terms (round-3 F1 — the domain is `{None, "procedural"}`; there is no `"declarative"` value): `None ∧ basis None` → declarative, never a candidate; `"procedural" ∧ basis ∈ {stated, observed}` → procedural; `"procedural" ∧ basis None` → `basis_unknown`; `None ∧ basis not None` → the disagreeing state, procedural BY FLOOR and the NAMED outcome `kind_conflict` (in `withheld`, counted — evidence of something, never a silent inference; research's addition); a procedural-stamped record with `basis=None` is `basis_unknown` → NOT describable, a NAMED non-allow (never a default, never a raise) | — | — | **V-ABSENCE-NAMED** (`test_procedural_record_without_basis_is_a_named_non_allow`), **V-KIND-STAMPED** (the conflict cell) |
| the `relation` argument to `record_procedure` (round-1 F6) | absent → the default `follows_procedure` | not a str → RAISES, nothing written | unknown to the ACTIVE registry, or registered with `relation_kind="declarative"` → RAISES (`ValueError`, named `relation_not_procedural`), nothing written | a host passing a declarative relation to launder a procedure into the grounded block → RAISES | **V-RELATION-VALID** (`test_record_procedure_requires_a_registered_procedural_relation`) |
| a STORED edge whose relation is absent from the ACTIVE registry (a host shrank or renamed its registry after writing; round-1 F7, round-2 F2) | — | — | kind is read from the record's STAMP, never from the registry: an UNSTAMPED edge (`record_kind` None, no basis — every pre-feature row, every legacy custom relation) behaves EXACTLY as today — rendered by recall as it is now, never a describe candidate; a PROCEDURAL-stamped edge is the named outcome `relation_unregistered` (its gloss is unreadable): out of both blocks as every procedural record is, in `withheld` with that outcome when visible, never dropped, still in `introspect` | a relation reclassified declarative→procedural or the reverse AFTER a write → NOTHING MOVES: the stamp is the write-time fact; new writes take the new declaration | **V-KIND-STAMPED** (`test_record_kind_is_stamped_at_write_and_read_from_the_record`), **V-RELATION-UNREGISTERED** (`test_unregistered_procedural_stamp_is_named_and_unregistered_declarative_is_unchanged`) |
| the other arguments to `record_procedure` (round-2 gap): `summary`, `note`, `when`, `evidence_ref`, `source_id`, `author` | `summary` empty or whitespace-only → `ValueError`; `note`/`evidence_ref`/`source_id` `""` → treated as `None` | not a `str` (or `author` not an `EvidenceAuthor`, `when` not an aware `datetime` — a `str` or a naive datetime is `ValueError`, **the SURFACE'S OWN gate (v15)** — NOT `as_utc_required`, which **admits** a naive datetime (0032's naive-means-UTC convention for stored values) and **parses** ISO text (0030's raw-carrier normaliser), and raises `TypeError` rather than `ValueError` for a non-datetime. **The OUTCOMES below were always right; only the mechanism was misattributed — the same defect 0028 §2c-i carried, and the two are the whole class (0030 and 0032 name the helper correctly, as a normaliser)**) → `TypeError`/`ValueError`, nothing written; `summary` beyond the ingest object bound → `ValueError` | — | `summary`/`note` carrying instructions — never rendered as instructions (§4a-ii) | **V-ARGS-VALIDATED** (`test_record_procedure_validates_every_argument_and_writes_nothing`) |
| the `source_id` argument to `record_procedure` under a STANDING REVOCATION (0022/0023; v10) | absent → no birth check, `_disclosure_for` applies | — | — | a host writing a procedure from a source it has revoked, through the new surface instead of `ingest_event` → the record lands QUARANTINED at birth (never describable: `withheld: quarantined`), counted like any birth-quarantine; the surface is not a bypass | **V-BIRTH-QUARANTINE-HOLDS** (`test_record_procedure_honours_quarantine_at_birth`) |
| the extractor's relation choice | (v16: a procedural relation is IN the vocabulary and takes §4a-iii's quote gate, never this row) out-of-vocabulary relations follow 0025's retry-then-residual path, filed under reserved `unclassified` at `use_only` and counted in `residual` (unchanged behaviour; **v15 corrects the word "drops"**) | — | the extractor filing a procedure under a DECLARATIVE relation (today's behaviour, unchanged: the text is treated as whatever it was filed under — stated in §8 as the residual) | the extractor emitting `follows_procedure` (from a prompt-injected name, or a model that has seen the docs) to reach the describe surface | (v16) the extractor SEES the procedural relation and a triple under it is written ONLY with a `quote` ingest verifies verbatim against the event text on a user-authored event; without one it is refused and counted, never filed, never stamped — **V-EXTRACTOR-QUOTE-GATED** (`test_a_procedural_emission_without_a_verifying_user_quote_is_refused_and_counted`); a prompt-injected or docs-learned name therefore reaches describe only by quoting words the user actually wrote; kind is the registry's declaration AT WRITE, stamped on the record — **V-KIND-STAMPED** |
| the procedure's summary text (rendered by `describe_procedures`) | — | — | — | text crafted to read as instructions ("step 1: run …") — the render WITHHOLDS a summary matching the FROZEN recognition rule (§4a-ii, §6a) as `executable_detail`; the `note` is NEVER rendered; a paraphrase in non-imperative mood PASSES the rule and is the stated v1 limit (§8) | **V-NO-IMPLICIT-RECOMMEND** (`test_describe_withholds_the_frozen_rule_and_never_renders_the_note`) |
| data written by an older version (a v13 store) | no procedural relation existed → no procedural record exists; every existing edge is declarative and unchanged | — | — | — | **V-DECLARATIVE-UNCHANGED** (`test_every_pre_existing_edge_is_declarative_and_unchanged`) — the V-COMPAT pattern: the pre-feature oracle replays byte-identically |
| export files carrying procedural records, imported on the DEFAULT path (round-3 F2: THREE independent signals) | — | a record whose markers are stripped or inconsistent | a relation the receiving host registers procedural, under a record with NO stamp and NO basis | an export claiming `basis="stated"` for a procedure — a basis DECLARED BY ANOTHER HOST (0026's relay shape; 0005: an importing store's knowledge begins at ITS import) — **the default import REFUSES a record as procedural when ANY of three signals says so: (1) `record_kind == "procedural"`, (2) `basis is not None`, (3) the RECEIVING registry's `relation_kind` for its relation is `procedural`** — named `procedural_import_refused` with `signal ∈ {stamp, basis, registry}` (the first that fires, in that order), never a bare refusal; declarative records in the same file unaffected. The six cells: stripped stamp + basis present → refused (`basis`); stamp present + stripped basis → refused (`stamp`); BOTH stripped under a relation this host registers procedural → refused (`registry`) — the receiving host's declaration beats a foreign file's silence; both stripped under a relation UNKNOWN to this host → imports as what every readable fact says, a declarative record under an out-of-vocabulary relation, exactly as today (refusing would invent a signal that is not there); a foreign `"procedural"` stamp under a relation this host registers DECLARATIVE → refused (`stamp`) — a procedural record never enters as declarative; **a file stamped format 10 yet carrying either key (round-4 F1):** the three signals are evaluated on the RAW record BEFORE any version normalization — a raw `record_kind == "procedural"` or raw non-null `basis` refuses THAT RECORD with its signal named and `raw: true` (the envelope declared 10 and the record carries a newer key: the presence is the evidence), the registry signal is evaluated on the same raw record, and only records that remain admissible are then normalized (the shipped I10 strip has nothing to strip from them). The 8-cell matrix, raw marker × receiving relation: procedural stamp × {procedural, declarative, unknown} → REFUSED (`stamp`, raw); basis present × {procedural, declarative, unknown} → REFUSED (`basis`, raw); neither × procedural → REFUSED (`registry`); neither × {declarative, unknown} → existing declarative behaviour. Refusal is RECORD-level, never file-level — a mixed file keeps its declarative records, per the atomic-over-the-admitted-set rule. Stripping never erases the classification decision | **V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE** (`test_default_import_refuses_procedural_records_on_any_signal`), **V-BASIS-CAP-ONLY** (`test_basis_can_only_subtract`) |
| the same files under `restore=True` (the operator's explicit assertion that the file is THIS store's own history — `portability.py:21-30`) | — | BOTH absence dimensions (round-3 correction): a `"procedural"` stamp with no `basis`, OR a `basis` with no `"procedural"` stamp, OR a basis outside the closed domain → the record is MALFORMED (a procedural record this store wrote always carries both) and refused per record (E4's malformed case; nothing written for it); a consistent procedural record restores VERBATIM; the registry signal does NOT fire on restore — the operator re-asserts the store's own past, and the registry may have changed since | — | the operator has made exactly the attestation `basis` requires, so the record is ACCEPTED WITH ITS DECLARED BASIS; a forged `restore` flag is the operator's own act, out of the store's scope (the existing `restore` trust note) | **V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE** (the positive leg: `test_restore_round_trips_procedural_records_with_basis`) |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | result (2026-09-06) |
|---|---|---|
| no relation is procedural today | `python -c "from veracium.schema import DEFAULT_RELATIONS as D; print(len(D), [n for n in D if 'proced' in n])"` | `19 []` |
| `Relation` carries no content kind | `grep -n "^class Relation" -A 4 src/veracium/schema.py` | `name`, `functional`, `desc` |
| the extractor sends out-of-vocabulary relations down 0025's residual path (**v15 — the v14 row claimed a DROP and its grep returned counter keys**) | `grep -n "failing = \|n_invalid = \|UNCLASSIFIED_RELATION" src/veracium/ingest.py` | `failing = [row for row in parsed if row["off"]]`, `n_invalid = len(failing)`, then `row["relation"] = UNCLASSIFIED_RELATION` — **the same rows, counted then filed** |
| `EvidenceContext` has exactly two kinds and no basis | `grep -n "_KINDS\|basis" src/veracium/schema.py` | `_KINDS = ("direct", "derived")`; no `basis` |
| `needs_confirmation` is a ranking input, not a gate | `grep -n "needs_confirmation" src/veracium/__init__.py` | `:1050-1054` partition of the ASSERTABLE set by the flag; `:1537` the only setter (CHALLENGED outcome) |
| `confirm_edge` is the sole clearer | `grep -rn "needs_confirmation = False" src/veracium/` | `store/sqlite.py` (`confirm_edge`) only |
| the harness ingests the inferred cell as attested user statements | research, against `paper2/instrument/validation/tier8_KEY.json`: all 40 reporting probes `author: trusted` | verified by research 2026-09-06 (the only marker is the in-text frame) |
| the harness can declare basis per ingest step once the store offers it | research's resurfacing runner (harness repo, not this tree) already declares `author` per probe and asserts it against the class's expectation | research 2026-09-06: "a small change on my side when the field exists" |
| a defaulted Optional field on a pydantic model is SERIALIZED (as `null`) unless a serializer omits it; a wrap-mode `model_serializer` that pops the key when None leaves the model's deliberate nulls intact | `.venv/bin/python -c` — a model with `n: Optional[str]=None` and `record_kind: Optional[Literal["procedural"]]=None` plus the wrap serializer → `{"a":"x","n":null}`; with `record_kind="procedural"` → `…,"record_kind":"procedural"}`; the control WITHOUT the serializer → `…,"record_kind":null}` | executed 2026-09-06 on pydantic 2.13.4; `Provenance` declares no serializer today (`__pydantic_decorators__.model_serializers == []`), `Edge` uses the wrap form at `schema.py:519` |
| the MCP surface has no way to declare basis | `grep -n "def remember(" src/veracium/mcp_server.py` | `remember(text, author=None, ...)` — no basis, no relation kind |
| the extractor's vocabulary is the registry's names, passed into the prompt (F1's mechanism) | `grep -n "relations: dict\[str, Relation\]\|rel_names" src/veracium/ingest.py` | `:169` `relations=DEFAULT_RELATIONS`; `rel_names` into the distill prompt |
| `not assertable` ROUTES to the fenced block today (F2's mechanism) | `grep -n "not e.assertable\|not ep.assertable\|FENCED, not suppressed" src/veracium/gate.py` | `:139` — third-party lines built from records that are NOT assertable; "FENCED, not suppressed (Q5)" |
| shipped `recall` renders assertable records into GROUNDED context | `grep -n "GROUNDED" src/veracium/gate.py` | `:9`, `:154` — "you may state these as fact" |

---

## 3. Trust-class matrix — REQUIRED, blocking

Classes read from the enums today: `EvidenceAuthor` = {user, third_party,
system, assistant}; `Disclosure` = {mentionable, use_only, quarantined};
NEW `basis` = {stated, observed} on procedural records only. The operations
this change performs are (a) ingest of a procedural event, (b) the describe
predicate, (c) the exclusion from the gate's partition. None is directional
(no prior/incoming pair is merged: `follows_procedure` is non-functional and
absorption applies the shipped same-class rule unchanged, with `basis`
carried like disclosure — the whole-set MINIMUM: an `observed` member makes
the survivor `observed`).

| operation | author=user | author=third_party | author=system | author=assistant | disclosure=quarantined | disclosure=use_only |
|---|---|---|---|---|---|---|
| ingest procedural, basis=stated | stored, mentionable, describable | stored, use_only (0001 rule unchanged), NOT describable | stored (our own consolidation output), describable | stored, use_only, NOT describable | stored, NOT describable | NOT describable |
| ingest procedural, basis=observed | stored, mentionable, describable WITH the observed attribution | as above | as above | as above | as above | as above |
| ingest procedural, basis absent/malformed | REFUSED, nothing written | REFUSED | REFUSED | REFUSED | REFUSED | REFUSED |
| the model-context choke point (recall/answer/compile/proactive/selfcheck) | EXCLUDED by the record's own stamp/basis rule from GROUNDED and from UNVERIFIED, named `procedural_out_of_scope` — every class | EXCLUDED | EXCLUDED | EXCLUDED | EXCLUDED | EXCLUDED |
| `describe_procedures` | describable iff visible ∧ active ∧ valid_now ∧ ¬quarantined ∧ ¬use_only ∧ basis ∈ {stated, observed} ∧ summary passes the frozen rule; the render carries basis and provenance, never the note | the named non-description `use_only` (record listed in `withheld`, no text) | describable | the named non-description `use_only` | the named non-description `quarantined` — reachable for a procedural record by ONE route, birth-quarantine under a standing-revoked source (v10) | the named non-description `use_only` |

Cross-scope (round-1 F5, research's semantics): scope decides WHETHER a
principal may know a record exists; disclosure decides WHAT they may be
told. A procedural record HIDDEN from the principal is OMITTED entirely —
`hidden` and "no matching record" are INDISTINGUISHABLE to an unauthorised
principal by design (a distinguishable `hidden` would be an existence
oracle). A record VISIBLE to the principal but `use_only` (a cross-scope-
visible record is `use_only` by 0020's third-party shaping) yields the
NAMED non-description `use_only` in `withheld` — the principal is already
authorised to know it exists; they are not told its content. The oracle
(§6a) carries principal × visibility × author/disclosure, including the
cell that fails if this is inverted: an unauthorised principal probing for
a record that exists receives exactly the answer they receive for one that
does not.

- Can this operation cause a **user-asserted fact to become
  non-assertable**? No. Declarative records are untouched (V-DECLARATIVE-
  UNCHANGED). A procedural record was never a fact; it is never assertable,
  by construction, whatever its basis.
- Can it cause **non-user content to gain user-grade authority, confidence,
  or currency**? No. `basis` is cap-only; the describe predicate is a
  conjunction that only subtracts from the existing trust predicates.
- Can it **clear `needs_confirmation`**? No. v1 does not touch the flag
  (confirmation-as-promotion is §4d's non-goal; see §10 Q2).
- Does it **merge, drop, or overwrite provenance**? No. `basis` is added;
  absorption carries the whole-set minimum.

**Write-time.** Basis is declared at ingest by the host; nothing at
maintain time can set, clear or change it (V-BASIS-IMMUTABLE — the 0019 U4
shape: a stored basis never changes on same-id replace).

---

## 3b. Authorization and scope — *full specs only*

No user, tenant or scope boundary is crossed. `describe_procedures` takes
the same `principal`/`ScopeView` composition as recall: a procedural record
HIDDEN from a principal is OMITTED from the result entirely — not described,
not listed, indistinguishable from no match (the visibility gate is
outermost, as in 0030 V-SCOPE); a cross-scope-VISIBLE procedural record is
`use_only` under 0020's shaping and yields the named non-description
`use_only`, never a description in any shape (round-1 F5 deleted v7's
"third-party shape", which contradicted the matrix). No principal can see
anything they could not see before: procedural records are a NEW class that
recall never rendered, and `describe_procedures` shows less than recall
would have.

---

## 4. Behaviour

**One failure taxonomy, stated once (round-1 correction).** WRITE-path
failures RAISE and write nothing: a malformed or absent basis, a basis on
a declarative event, a relation that is unknown or not procedural, a
`when` beyond the skew. READ-path outcomes are RETURNED and NAMED, never
raised: every `Withheld.outcome`, `procedural_out_of_scope` at the choke
point, `relation_unregistered`. The only exceptions on a read path are the
existing ones (`ScopeError` for a principal without a policy — 0020's).
"Refuses" below means the write-path raise; "named outcome" means the
read-path return. **Two layers, stated once (round-2 gap):** the LIBRARY
raises (`TypeError` for a wrong type, `ValueError` for a wrong value, each
carrying the named reason, e.g. `relation_not_procedural`); the MCP TOOLS
never raise to the transport — each catches exactly those library
exceptions and returns a SERIALIZED result `{"ok": false, "refusal":
<name>}` — ***NEW AT v15, FOR THE TWO NEW TOOLS ONLY. Through v14 this called it
"the existing tool-result shape" and NO SUCH SHAPE EXISTED:*** `mcp_server.py`
carries no `refusal` key and no `ok: false` anywhere; its tools return counter
dicts, and an attempted elevation is discarded and counted, never refused.
**`remember`'s contract is UNCHANGED — the shape is ADDITIVE for the two new
tools; retrofitting it to a shipped surface would be a breaking change and is
not proposed here.** An attempted elevation
under `capability=none` is the same serialized refusal the other tools
already return. A library exception and a tool refusal carry the same
name; they are the same fact at two layers, not two facts.

### 4a. What makes a record procedural — the registry at write, the record's own stamp at read, three raw signals at import; never the text

An EDGE is procedural iff its relation is registered with
`relation_kind="procedural"`. Relation kind is a property of the RELATION
REGISTRY (named `relation_kind` deliberately: `Episode.kind` already exists
and means `interaction | outcome`, nothing to do with this axis — F4's
adjacent-name collision), declared by
the host (the default registry ships one procedural relation,
`follows_procedure`), consulted AT WRITE and STAMPED ON THE RECORD
(`Provenance.record_kind`, round-2 F2). For stored records kind is read
from the STAMP, never from the registry, so it is TOTAL over stored
records: every row has exactly one kind (ABSENCE IS DECLARATIVE — the
field is `Optional[Literal["procedural"]]`, `None` on every declarative
write and on every pre-feature row, true by construction: no procedural
relation existed before this version), no record is "unclassified or
mixed", and the round's conservative ambiguous-type rule is satisfied by
construction. The rule applies to EDGES. `Provenance` is carried by
`Episode` too (`schema.py:625`), where both fields are vacuous: no writer
produces a procedural episode (V-NO-EPISODE) and `ingest_event` refuses a
basis on a declarative event (V-BASIS-SCOPE), so an episode's stamp is
always absent and the choke point's episode path never consults it — a
sentence written so nobody infers the other half. The
registry decides what a NEW write is; it never re-decides what a stored
record was. The read rule is `procedural iff record_kind == "procedural"
OR basis is not None`: two independent write-time facts, written by
different mechanisms, must BOTH be destroyed to launder one record into
recall — the failure direction decides this (with basis alone as the
marker, stripping data would MOVE a procedure into the grounded block);
the disagreeing state (NO stamp — `record_kind` is `None` — with a basis
present) is procedural by floor and the NAMED outcome `kind_conflict`,
never a silent inference; there is no `"declarative"` value anywhere in
the store (round-3 F1 — the domain is `{None, "procedural"}`).
Consequences, each pinned: (1) a relation reclassified after a write moves
nothing — no "reclassified between write and read" cell exists; (2) a
host that removes or renames a relation leaves its UNSTAMPED records
(`None`, no basis) exactly as they are today — rendered by recall as any
out-of-vocabulary edge is now, never a describe candidate (this is the
population v10's remedy wrongly withheld: legacy custom declarative edges,
the round-2 regression); (3) only a PROCEDURAL-stamped record whose
relation is gone is the named outcome `relation_unregistered` — its gloss
cannot be read, so it is in `withheld` when visible, out of both blocks as
every procedural record is, never dropped, still in `introspect`.
V-DECLARATIVE-UNCHANGED therefore covers the custom-registry population
too, and the feature is inert until a host records a procedure, as
claimed. What remains observable-on-describe (pre-seal F-B) is confined to
procedural-stamped records, which recall never rendered; §10 Q7 keeps its
question in that narrower form.

**The extractor reaches a procedural relation only through the quote gate
(F1; v16, §4a-iii).** The vocabulary handed to the extraction prompt carries
the registered procedural relation; a triple under it is written iff its
`quote` verifies verbatim against the event text on a user-authored event,
and is otherwise REFUSED and counted (`procedural_refused`) — never filed,
never stamped. *Through v15 the registry's procedural relations were
FILTERED OUT of that vocabulary, so the model could not emit one, and an
emitted procedural name was **off-vocabulary and followed 0025's residual
path exactly like any other out-of-vocabulary relation (v15)**:* retried once against the same
vocabulary and, unrecovered, **FILED under the reserved `unclassified`
relation at `use_only`** and counted in `residual` — **never an edge under a
procedural relation, never stamped, never describable.** ***Through v14 this
said "dropped as `invalid` … nothing written", and that is not what an
out-of-vocabulary name does:*** `ingest.py` sets `failing = [row for row in
parsed if row["off"]]` and `n_invalid = len(failing)` — **`invalid` is a
COUNTER NAME for the triples that are then retried and filed, not a drop.**
The v14 reachability row cited `grep -n "invalid" src/veracium/ingest.py` as
its evidence; **that grep returns counter keys, so the citation was
satisfiable without the claim being true.** **The guarantee this section
actually carries is about the STAMP and the PROMPT, not about storage: a
residual `unclassified` edge IS written and IS rendered by recall (labelled
`[<origin>; unconfirmed]`), exactly as any off-vocabulary text is today —
0037 does not narrow that and must not be read as doing so.** Diverging from
0025 for this one name was considered and NOT taken: it would special-case a
shared path, and §5's own passage on removed relations already endorses
*"rendered by recall as any out-of-vocabulary edge is now"*.
Kind is therefore host-declared END TO END, not only in principle. Two
producers write a procedural record (v16; V-TWO-PRODUCERS): the explicit
surface `Memory.record_procedure` (the canonical signature is in §2), which
constructs the edge directly under a procedural relation, takes the
AUTHOR as `remember` does, and REQUIRES the basis the host declares on the
context; and, since v16, the extractor path under §4a-iii, where the
registry still supplies the KIND and ingest DERIVES the basis from a
verbatim quote it verifies itself. Text the extractor reads as procedural
without a verifying quote is REFUSED and counted — never filed under a
declarative relation, never stamped (§4a-iii).

**The producer stamp and the frozen model (v23).** Both producers wrote
byte-identical stamps until v23 (`record_kind="procedural"`, and `basis`
`stated` on the extractor path or whatever the host declared), so no stored
field said WHICH path wrote a record — the doctor's `procedural_declared`
merged host-declared and extractor-captured records under a docstring that
called them declared (research's finding, 2026-09-14). Every procedural
record written by this version carries `Provenance.producer`: `"host"` from
`record_procedure`, `"extractor"` from the quote-gated capture — a write-time
fact the product mints and no host input supplies, absent on every
declarative record (the key is omitted, so declarative bytes are the
pre-feature eight; a declarative record carrying one is refused at
construction) and absent on procedural records written before the stamp —
and on a procedural record written AFTER it through a path other than
`Memory` (a hand-minted record at `Store.add_edge`, the boundary below): the
doctor reports both as UNSTAMPED rather than guessing them into either
bucket and names the causes — written before the stamp; restored from an
older export or from an envelope below format 12, where 0006 I10 strips the
field; written through a path other than `Memory` — the count establishing
that the producer is unknown, not why (v23.1's "live reading" of a write past
the `Memory` boundary on a store created after the stamp was WITHDRAWN at
v24.1: the round-5 reviewer restored a format-11 record into a new database
through an ordinary supported path and got `unstamped=1`). The stamp is immutable on a same-id replace and inherited across a
supersession, at the same store choke point as the kind stamp and basis
(V-PRODUCER-IMMUTABLE, V-PRODUCER-INHERITED). And `Provenance` is FROZEN:
the sweep of V-TWO-PRODUCERS recognises a literal keyword at construction,
and since v19 it named its residual honestly — a stamp minted through an
attribute chain on an already-built model, outside the sweep's grammar.
That route no longer exists: ordinary assignment on a built `Provenance`
raises, the eight src sites that mutated a provenance replace it with a copy,
and an AST sweep asserts no src site assigns to a provenance attribute
(V-PROVENANCE-FROZEN). What remains is the boundary itself, stated rather
than gated: **`Store.add_edge` is an interface a host IMPLEMENTS, not a write
API a host CALLS** (0006 v10 rule 10) — a record a host hand-mints and writes
there carries what the host minted, renders as a declared procedure, and is
outside every guarantee this spec makes about records written through
`Memory`; the same sentence stands in `docs/api.md` where a host reads.

**A procedural record never enters the model-context path — excluded ONCE,
by the record's OWN stamp/basis rule, at the choke point (F2; round-3
correction: not "by relation kind" — the registry is never read at read
time).** `Edge.assertable` is UNTOUCHED: it means
"safe to state as fact" and, today, `not assertable` ROUTES a record into the
fenced third-party block ("FENCED, not suppressed", `gate.py:139`, Q5).
"Out of scope for this path" is a different proposition from "not safe to
state as fact", and one predicate does not carry both. So the partition
(`gate.partition` / `partition_parts`) and recall's edge selection exclude
procedural records by the stored rule BEFORE assertability is consulted, with the
named outcome `procedural_out_of_scope`; §6's sweep derives every site that
renders records into model context and proves each reaches that one
exclusion. This is "recommend unavailable by default" made concrete: the
action-oriented path never carries a procedure.

**Episodes (F4).** Episodes reach model context on their own path — the
partition returns episode lines for both blocks — and an episode has no
relation, so relation kind cannot exclude one. Three cases, each settled:
(1) `record_procedure` writes NO episode — the procedural edge is the whole
record, and V-NO-EPISODE pins it (the ordinary ingest path DOES write one,
so a later change could add it without a test noticing); (2) therefore no
procedural record produced by this spec's surface reaches context through
an episode; (3) procedural TEXT arriving through ORDINARY ingest: since v16 a
quote-verified procedural triple is stored as a procedural record (§4a-iii)
and excluded from context by the stored rule like any other; the EPISODE
still carries the event's text into context exactly as it always has —
unchanged by v16, measured at v15 (§8). Governing that path needs a
host-declared EPISODE kind, which is a larger change than this
commission's scope; it is §10 Q6 — SCOPED ELSEWHERE by the owner and
not a blocker of 0037 (round-2 correction of a stale classification).

**Excluded from the UNVERIFIED block too — Q1, ruled by research from the
data.** The fenced block's own rule ("a quarantined claim stays visible as a
claim rather than vanishing", Q5) is right for declarative claims and WRONG
here, and the reason must be stated so nobody later restores symmetry: the
harm from a FACT rendered as a claim is a wrong belief; the harm from a
PROCEDURE rendered as a claim is an ACTION. Across the Tier 8 competitor
arms, procedural content that reached the answerer's context was handed
back as guidance at family-level rates of 0.25–0.90 — the unverified block
is context, and context is what a host renders into a prompt.

**4a-ii. The describe surface — the result contract (round-1 F2).**

```
Memory.describe_procedures(user_id, *, query: Optional[str] = None,
                           principal=None, limit: Optional[int] = None) -> DescribeResult

DescribeResult:
    descriptions:      list[ProcedureDescription]   # the describable records, ORDERED (below), cut at `limit`
    total_describable: int                          # the describable population BEFORE the cut (pre-seal F-A)
    withheld:          list[Withheld]               # visible-but-not-describable records, never cut
    truncated:         bool                         # True iff len(descriptions) < total_describable
    query:        Optional[str]                 # echoed, normalized (lower-cased, whitespace-collapsed)

ProcedureDescription:                          # NO raw stored text in any field:
    edge_id:      str                           #   the record's id (row-sourced)
    relation:     str                           #   the registered relation name
    gloss:        str                           #   the registry's one-clause gloss for the relation
    summary:      str                           #   the record's `object` — the host's gloss-level name of the
                                                #   procedure, the ONLY stored text that is ever rendered
    basis:        Literal["stated", "observed"]
    attribution:  str                           #   "recorded from something you said: …" / "a pattern you reported observing: …" (v18),
                                                #   composed from basis + summary, never from the note
    author:       str                           #   EvidenceAuthor value
    observed_at:  datetime; valid_from: datetime
    disclosure:   str                           #   always "mentionable" here (use_only/quarantined are withheld)

Withheld:
    edge_id: str
    outcome: Literal["kind_conflict", "relation_unregistered", "inactive", "not_yet_valid",
                     "quarantined", "use_only", "basis_unknown", "executable_detail"]
```

The `note` (where step-level detail lives if the host supplied it) appears
in NO field of either type; a hidden record appears in NEITHER list (§3).
**The candidate set, stated once (v10, re-based on the stamp in v11):**
the VISIBLE edges that are procedural BY THEIR OWN RECORD —
`record_kind == "procedural"` OR `basis is not None` — whatever the active
registry says about their relation (an UNSTAMPED record WITH a basis is a
candidate and yields `kind_conflict`, §4a). An unstamped record without a
basis is NEVER a candidate, registered or not: it appears in
neither list and never counts (the control cell in §6a) — which is why there is no
`not_procedural` outcome; v9 named one that the candidate set could not
reach, the defect class round 1 found. One result per VISIBLE candidate,
BEFORE truncation: every candidate is describable or withheld, never both
and never neither, and `total_describable + len(withheld)` is the visible
candidate population. `descriptions` is then cut at `limit`, so a describable record
below the cut is in neither list — `total_describable` is what keeps the
population accountable after the cut (`total_describable -
len(descriptions)` records were cut; pre-seal F-A: `truncated` alone says
that a cut happened, not what it removed). `withheld` carries the id and
the named outcome only.

**`limit` (round-2 gap).** `None` → `MemoryConfig.max_subgraph_edges`;
otherwise it must be an `int` (not `bool`) with `1 ≤ limit ≤
max_subgraph_edges`, else `ValueError` before any read — zero, negative,
non-integer and above-cap values are caller errors, not outcomes, and the
cap is the maximum rather than a silent clamp. `query`: `None` or a `str`
(else `TypeError`); a `str` that is empty after normalization is the null
query.

**Predicate.** A candidate is described iff
`stamp consistent ∧ relation registered ∧ active ∧ valid_now ∧
¬quarantined ∧ ¬use_only ∧ basis ∈ {stated, observed} ∧ summary passes the
frozen recognition rule (§6a)`; the first failing conjunct, in that order,
names the withheld outcome. There is no default allow and no untyped
outcome.

**Ordering (observable, deterministic).** The query ORDERS `descriptions`;
it never filters either list. With a query: descending relevance, where
relevance is the count of query tokens present in the record's `{subject,
relation, object}` tokens (the store's existing `_rel` tokenisation:
lower-cased alphanumeric runs; the `note` is NOT scored — it would let
step text influence ranking); ties by `valid_from` descending, then
`edge_id` ascending; zero-relevance records follow, in the same tie order.
With `query=None`: `valid_from` descending, then `edge_id` ascending.
`limit` defaults to `MemoryConfig.max_subgraph_edges`; the population is
ordered BEFORE the cut and `truncated` says whether a cut happened.
Repeated calls on an unchanged store return byte-identical results.

**`withheld` is QUERY-BLIND (research, round-1 F5's second half):** its
membership and its order (`valid_from` descending, `edge_id` ascending;
never truncated) do not depend on the query. If it were query-filtered,
an id's PRESENCE would be the leak: a principal entitled to know that a
`use_only` record exists could learn what it is ABOUT by varying the
query — `describe_procedures(query="audit log")` listing it says it
concerns the audit log — and a wordlist would reconstruct the topic of a
record they may never read, a search oracle built from an outcome
designed to disclose nothing. The property is invisible in the API's
shape, so V-WITHHELD-QUERY-BLIND states it and the oracle carries its
failing cell: the same record, two different queries, identical
`withheld`. (The premise it rests on was checked, not assumed: edge ids
are random — `f"{prefix}-{uuid4().hex[:12]}"`, `ingest.py:30` — so an id
discloses nothing about content.)

**What the render guarantees (round-1 F3 — the actual guarantee, not the
absolute claim):** the `note` is never rendered, in any field; a summary
matching the FROZEN recognition rule (§6a — research's corpus, its digest
recorded before implementation) is withheld as `executable_detail`; a
description that reproduces a procedure's steps in the system's own voice
IS a recommendation whatever its framing (round 5), and these two defences
are what stand between a summary and that. **What it does not guarantee:**
a summary that carries the same content in non-imperative mood ("you could
disable the audit log first") PASSES the rule; that is the stated v1
paraphrase boundary (§6a, §8), a limit and not a guarantee.

#### 4a-iii. Capture reopened (v16), gated (v19) — the extractor path

**The rule.** The extractor may RECORD a routine the user EXPRESSED; it may
not CONCLUDE one, and it may not describe as the user's what the user's words
do not say. Every line of that rule is a mechanical check at ingest — the
GATES below, run IN THIS ORDER over ONE normalised string, each RESTRICT-ONLY
(it can refuse; it can never admit what an earlier gate refused), any failure
REFUSED and counted in `procedural_refused`, nothing written, never filed as
`unclassified`, never stamped. The code's order is the spec's:
`src/veracium/procedural_gate.py` (`check_capture`) is the one implementation.

1. **Vocabulary.** The prompt's selectable set is exactly 0025 §4b-iv's — the
   effective registry minus `unclassified` — so a relation with
   `relation_kind="procedural"` is rendered and the model may emit it. A retry
   REPAIR can never land on a procedural relation (it carries no quote): the
   failing triple stays residual.
2. **The carrier: `quote`.** A procedural triple carries `quote`, the VERBATIM
   span of the event text in which the user states the routine (an optional key
   in `EXTRACT_SCHEMA`; a hint to a compliant provider, 0038 §2b).
3. **Gate 0 — whose event.** Only an event whose AUTHOR is the user
   (`author=USER`). Through MCP under `VERACIUM_MCP_CAPABILITY` unset the
   baseline author is third-party (0031 §4a), so an unattested deployment
   cannot capture one.
4. **Gate 1 — normalise, then substring, then ONE WHOLE SENTENCE (V-WHOLE-
   SENTENCE, v22; round-3 finding 2).** Inner-whitespace collapse ONLY (no
   casefold, no punctuation strip: verbatim means verbatim; the collapse
   tolerates line wrapping) on the span and the event text; the span must be
   non-empty and a substring of the event text — a paraphrase fails. And the
   span's BOUNDARIES are validated against the event — BOTH ends (v24.1,
   round-5 finding 1). Since v24 (round-4 findings 1a, 1b and 2 — one root
   cause: v22 tested CHARACTERS, not boundaries) a boundary is a KIND read from
   the complete event by `boundary_kind`, total over what can follow a terminal
   run and fail-closed; since v24.1 (round-5 finding 2; the owner's word "Fail
   closed") a boundary is ESTABLISHED only where the language leaves no doubt,
   and a passage whose boundaries cannot be established is DECLINED: the start
   or end of the text is a boundary (a closing quote or bracket may follow the
   final run); a `!` run followed by whitespace and then an uppercase letter, a
   digit or an opening quote/bracket is a boundary; `?` anywhere in a run makes
   the sentence it ends a QUESTION, refused whatever the span carries, while the
   run still establishes the START of what follows ("Any tips? I run the
   formatter before committing, every time." admits its second sentence); a `.`
   between two digits is INSIDE a sentence (`$100.50`); and EVERY MID-TEXT
   PERIOD is AMBIGUOUS — a sentence end or an abbreviation (`in env. Prod only
   after approval`, `9 a.m. every day`, `daily. archive`, `daily.archive`), and
   the rule cannot tell which: no list can (the reviewer), and no list-free rule
   can either (research; shape rules were built and measured and refused the
   canonical routine shape) — so it establishes nothing in either direction,
   and the abbreviation list v24 carried is gone. So are an ellipsis and a `!`
   followed by anything but a sentence start. The span begins at an established
   boundary (never after an ambiguous run — "e.g. I review…", "that... I
   review…" — and never mid-token: `$100.`|`50 daily`) and ends at the end of
   the event, at its own terminal run, or immediately before a plain `.` or `!`
   it omitted at the end of the text — never before an omitted `?` (F1a:
   dropping it turned a question into a statement). v24.2 (round-6 finding 1):
   a terminator INSIDE an enclosing parenthetical or bracket is inside its
   sentence and ends nothing ("For illustration only (ready?) I review
   invoices daily." is one sentence; the routine after the parenthetical is a
   mid-sentence start and refuses), and a run establishes the next start only
   by what FOLLOWS it — the end of the text, or whitespace and then a sentence
   start — whatever marks the run carries: "Any tips?I review…" establishes
   nothing (as the `!` form never did), "Any tips? I review…" does. v24.3
   (round-7 finding 1): the enclosure structure is read by `enclosure_structure`
   before any run is judged — parentheses, brackets and braces must nest and
   match by type, characters inside a quoted literal (`"…"` or curly quotes)
   are inert (a quoted `]` or `)` closes nothing, a terminator inside quotes
   ends nothing), and when the structure cannot be ESTABLISHED — a mismatch
   (`(ready?]`), a stray closer, an unclosed opener, an unbalanced double quote
   — every segment of the passage is declined, never guessed (the stated cost:
   a lone `"` in a turn declines it).
   So a fragment inside a framing sentence ("Imagine I always review invoices."
   → "I always review invoices") is refused BEFORE the grammar reads it — the
   substring check proves that words occur, this proves that they are what the
   user asserted — and two sentences are refused as two assertions, whatever
   separates them. The reviewer's whole-sentence hypotheticals then meet the
   grammar as sentences and refuse on their heads: "Imagine…" opens with no
   actor; "I doubt I review invoices daily." refuses on its cognitive head —
   which was a CLAIM until v24 (F3: `doubt` was not in the class; `doubt`,
   `deny`, `suspect`, `presume` are now, `question` and `bet` deliberately not).
   The gate's reason vocabulary is TOTAL over its inputs (v22, research):
   `no_quote`, `no_event`, `quote_not_in_event`, `actor_absent`,
   `summary_contract` — a missing event is its own outcome, never reported as
   the content verdict `quote_not_in_event`; and the normaliser every gate
   runs over REFUSES a non-string rather than coercing it (`str(None)` is the
   plausible span "None"). `remember`/`ingest_event` refuse a non-string event
   before any model call.
5. **Gate 2 — the summary contract, ONE for both producers (V-SUMMARY-CONTRACT;
   round-1 finding 3).** The gloss is whitespace-normalised, non-empty and at
   most `MAX_SUMMARY_CHARS` (512) — the rules `record_procedure` has always
   applied to a host summary — applied (v21) to the DERIVED gloss after the
   grammar, so the string judged is the string that is stored.
6. **Gate 3 — the user as the ACTOR, now (V-ACTOR-PRESENT; round-1 finding 2,
   research's nine constructions and its red team).** The span must OPEN with the
   user asserting a CURRENT, REPEATED performance of their own (v20, the
   POSITIVE FORM — the owner's word): after an optional leading temporal or
   conditional clause, the first-person SINGULAR pronoun (research §5: "we" is
   a policy, not the user) in one of THREE enumerated head shapes — present
   simple with an optional negator or frequency adverb ("I use it to…", "I
   don't eat meat", "I always run…"), present perfect continuous ("I've been
   using…"), or present progressive ONLY with a frequency marker somewhere in
   the span ("I'm walking the dog every morning") — whose head verb is a
   lexical ACTION verb: not a modal or auxiliary ("I can", "I will", "I have
   a…"; and a lexical "do", which form cannot tell from its auxiliary use — a
   stated cost), and not in the cognitive/volitional class (think, mean, hope,
   plan, consider, want, intend, wish, try, aim, like, love, prefer, need,
   feel, believe, guess, suppose, wonder, decide, figure, imagine, dream, …),
   which is matched BY CLASS through a symmetric light stem (`_stem`) so every
   inflection meets it; the optional leading temporal or conditional clause,
   when it is a SUBORDINATE clause (before/after/when/whenever/once/on/at/
   during/while/if), must END AT A COMMA (v22: "If I review invoices daily,
   the queue stays short." had matched with the lead consuming "If " and the
   conditional's own "I review…" read as the assertion; a frequency lead,
   "Every Friday I review the invoices", needs none — no clean positive in
   400 sessions opens with a subordinate lead); and (v21, round-2 finding 2)
   not a DIRECTIVE head
   (request, ask, suggest, recommend, tell, remind, urge, order, insist, propose,
   advise, instruct, demand, require, invite, encourage, beg, …) — "I request
   that you review invoices today" is a speech act aimed at the addressee, not
   a routine of the speaker's — and the span carries NO SECOND PERSON (you,
   your): a span addressed to someone is not the user's own routine, fail-closed;
   measured before choosing, you/your occurs in 0 of 13 clean positives and 27
   of 101 must-refuse spans across the three draws. The SPAN's head decides, never a later clause's
   (clause-any would admit "I'm thinking of dedicating a day each week…" on
   its complement, the construction that defeated v19). Every form nobody
   enumerated FAILS CLOSED — that is the point of the positive form: a marker
   list enumerates surface forms of a semantic property and lags a criterion
   permanently (v19's held-out failure was three intentions no list carried,
   not even the rater's rubric), while a positive requirement puts every
   unknown form on the refusing side. The v19 markers are KEPT as defence in
   depth: the span carries NO marker of REPORT ("told me", "says",
   "according to"), REJECTION ("refuse", "won't", "stopped", "no longer"),
   ASPECT ("used to", "keep meaning to"), NORM ("the standard is", "required
   me to"), REQUEST ("please" — the reviewer's one-time instruction),
   ASPIRATION ("try to", "mean to", "hope to" — the sixth class, present in
   the real data: "I'll try to meditate at the same time every day"), a
   QUESTION mark, or a ONE-TIME or PAST form ("just", "did", "was", a simple-past
   verb after the head without "been"). And the span's LEFT CONTEXT in the
   event (a bounded window) must not end in a QUOTATION or ATTRIBUTION frame —
   a quote mark, a colon, a report verb, "from the vendor" — because
   containment is not position: a tight span lifted from inside a quoted third
   party speaking in the first person ("The phishing email read: 'I always
   forward my reset codes…'") passes every other test.
7. **Gate 4 — the gloss IS the span (V-GLOSS-DERIVED; round-1 finding 1,
   round-2 finding 1, round-3 finding 1; the owner's word, 2026-09-13).** The
   model's `object` for a procedural triple is NOT an input and is discarded.
   The stored gloss — what `object` holds and describe renders — is the
   verified span, whitespace-normalised, and NOTHING else: no cut, no
   expansion, no subject dropped, no inflection. v21 kept ONE transformation,
   cutting a comma-introduced relative clause to the end of the span, measured
   on the trailing-commentary shape the sixteen observed positives carry; the
   round-3 reviewer showed it removing a MID-sentence clause and the condition
   after it ("I review invoices, which arrive daily, only after approval."
   stored "I review invoices") — a transformation measured on one shape and
   applied to another, the one-case rule inside out. Withdrawn: the user's
   sentence is stored as the user wrote it. WHY THIS IS THE END OF THE LINE:
   substring (v16) → negative markers (v19) → the positive form (v20) → a
   predicate-level grounding (built, measured, deleted) → a subject-dropping
   derivation (rejected by describe's own floor) → a relative-clause cut
   (retired by the reviewer's mid-sentence case): seven designs retired by
   measurement, none by argument; the only transformation that cannot change
   what the source asserts is none. WHAT IT COSTS, stated: trailing
   commentary is stored with the routine — "I've been listening to it during
   my morning walks with my dog, which has been a great way to get some
   exercise and make progress on my book" is stored whole (2 of the 16
   observed positives carry such a clause; research's coordinator-commentary
   residue is the same cost). It is the user's own words, rendered by
   describe after "recorded from something you said:", never a fabrication.
   The sixteen observed positives, now the sentences verbatim, stay pinned in
   `tests/eval/extraction_speech_act/derived_glosses_observed_positives.jsonl`
   and regenerated by test, with the assertion that every derived line equals
   its normalised quote. REJECTED BY MEASUREMENT before this: dropping the
   subject "I" turns a present-simple routine into an imperative-shaped
   fragment that describe's frozen executable-detail floor WITHHOLDS (the
   reviewer's cases vanished from describe); the sentence kept, describe
   renders it. And THE GRAMMAR (Gates 1 and 3) IS THE ONLY FILTER between a
   user's sentence and stored text: span boundaries are validated against the
   event (Gate 1), the head shape and its refusal classes decide (Gate 3).
   A STATED DEPENDENCY (research's attack on v22 before its seal): every check
   in Gate 3 reads the span's LEFT context or its HEAD, so a defeater placed
   to the RIGHT of the actor head passes them all — "I always review invoices
   in my dreams / in this thought experiment / if I have time / except I never
   do" are whole sentences and admit. They are SURVIVABLE ONLY BECAUSE nothing
   is trimmed: the stored text is "I always review invoices in my dreams.",
   the defeater travelling with the claim, a visibly qualified record and not a
   false routine. Gate 1's whole-sentence rule and Gate 4's no-transformation
   rule are therefore COUPLED: any future design that trims a trailing adjunct
   turns this whole class into stored false routines. Measured on the corpus
   before sealing: of the 40 labelled quotes located in a USER turn, the
   shipped gate admits 5, and the whole-sentence rule refuses none of them.
   A second stated limit from the same measurement: 25 of 241 labelled quotes
   match their source only after markdown emphasis is stripped (the model
   quotes the rendered text) — all 25 are assistant turns, refused on
   authorship, but a user who bolds a word inside their own routine is refused
   by Gate 1 for a reason unrelated to faithfulness; fail-closed, stated.
   DRAW 5 — THE FULL-PATH EVALUATION the round-3 reviewer asked for
   (`tests/eval/extraction_speech_act/draw5_fullpath.jsonl`, 71 rows, each with
   the COMPLETE event text captured at collection, so the passage rules run
   as (event, quote) pairs; `draw5_11_labelled.jsonl`, the 11 user-turn pairs
   labelled against the frozen rubric). PROTOCOL, stated: dev stated the
   thresholds before the labels existed and research had already published
   the gate's verdicts, so by the rubric's own clause this is a SECOND
   DENOMINATOR with a non-blind rater, not a held-out test, and is quoted as
   such. Thresholds: zero admissions among the non-borderline must-refuse
   pairs; every assistant-turn pair refused; the stored text of every
   admitted pair equals the normalised quote; positives reported. RESULT: 0
   of 4; authorship refuses an assistant-authored event at ingest before the
   passage rules run (asserted through the ingest path), and on this draw the
   passage rules alone also refuse all 55 assistant pairs — contingent on this
   corpus, not a property (an assistant's "I always recommend X" could pass
   them); the five quotes never located in their session have no event text
   and no role and are excluded, not counted; of the six spans labelled pass SPAN-ALONE, exactly the two
   that are whole sentences of their event are admitted and exactly those two
   — the four others are mid-sentence clauses after ", so ", refused by the
   whole-sentence rule as designed; the recall figure is 2 of 2
   whole-sentence positives, never 2 of 6 (the rubric's rule 1, "label the
   span alone", was written for the span-only era and is owed an amendment
   before the next draw). Both admitted spans carry a trailing relative
   clause — F1's case live: the retired cut would have trimmed the user's own
   words about their own routine. Base rate 2 clean routines in 100 sessions.
   A collection finding from the same draw: the LongMemEval enumeration holds
   940 distinct session ids in 948 positions, so draws selected by POSITION
   could collide; draws 1–4 were checked and are mutually disjoint — by luck,
   the first collision beginning at position 400 — and draw 5 selects by id.
   v24.1 (the round-5 return; the owner's word "Fail closed"): under the
   boundary contract both of those admissions FALL — each sat before a
   period-terminated neighbour, which establishes no boundary — so draw 5
   admits 0 of 6 positive rows = 0 of 4 distinct positive passages, with
   every pair still refused-and-counted through the full path
   (V-DRAW-5-FULL-PATH); the two figures are reported side by side, and the
   loss is the stated cost of §8, not a relabelling. Research's rubric v2
   (`HELDOUT-LABELLING-RUBRIC-v2.md`, sha16 1aa64970b8b3b863 re-derived from
   the copy in the tree; v1 `HELDOUT-LABELLING-RUBRIC.md`, 26227b51efa890f0,
   untouched — the rubric draws 1–5 were labelled under) makes the (event,
   quote) pair the labelling unit and both denominators structural for the
   next held-out draw, whose labels are frozen before any threshold or gate
   result is seen.

8. **Basis is DERIVED, never declared.** A capture that passes derives
   `basis="stated"`: the user uttered, in their own words, a present or
   habitual routine of their own, and the gloss describes those words. That is
   what `stated` means on this producer; describe's attribution (v18,
   V-ATTRIBUTION-HONEST) claims exactly that and nothing more. `observed` stays
   host-only; `inferred` does not exist and is not addable — an inference has
   nothing to quote. The extractor path still REFUSES a caller-declared basis
   on its context (§4b).
9. **What is written, and what is NOT (research's red team).** One `Edge` under
   the emitted procedural relation: `object` = the normalised gloss;
   `provenance` = the EVENT's (`author_of_evidence` USER, `derived_from`,
   `disclosure`, `source_id`, `evidence_ref` the event's — `evidence_ref` is
   source identity and is never overloaded) plus `record_kind="procedural"` and
   `basis="stated"`; **`note` is EMPTY**: the span is verified and DISCARDED.
   Through v18 the note held the quote, and `note` is the one field every
   non-procedural record renders — "never rendered" was a property of the
   exclusion, not of the field, and a successor that dropped the stamp rendered
   it (below). A digest of the span is not stored either: a sha256 of the
   user's own sentence is a confirmation oracle (0041 §4's content-digest
   carrier). WHAT THIS ESTABLISHES, made exact at v21 on the round-2 reviewer's
   finding ("no stored field holds the span" was an overstatement — with the
   gloss equal to the quote, `object` held the sentence): `object` IS the
   user's span in derived form (Gate 4); there is NO SEPARATE COPY in `note` and
   NO DIGEST. What protects the span is the RENDER EXCLUSION on `object` (item
   12) and the grammar that admitted it, not the record's shape. The episode is
   written as on every ordinary ingest.
10. **The stamp survives every successor (V-STAMP-INHERITED), and a procedural
    record is not corrected (V-NO-CORRECTION-OF-PROCEDURES).** `correct()`
    minted a successor with the note and without the markers, so
    `is_procedural` was false and the quote reached recall's context on shipped
    0.24.0 — reproduced end-to-end by dev on research's probe. Inheriting the
    markers onto a correction's successor would instead attribute the HOST's
    corrected text to the user (round-1 finding 1 reborn), so `correct()` on a
    procedural record REFUSES with the named reason `correction_of_procedure`
    (nothing written; retire it and restate the procedure through a producer
    that can attest it), and the store's one edge-persistence choke point
    refuses ANY edge whose `supersedes` names a persisted procedural
    predecessor unless the edge is itself procedural — keyed on the persisted
    predecessor's own stamp/basis, never on the registry. Absorption already
    carries the whole-set minimum (§4a); import carries the stamp (§4e).
11. **0038's drop rule.** A stated routine is expected to appear in
    `instructions` too. 0038 §2b's refusal EXEMPTS only a procedural carrier
    that PASSED every gate above — keyed on the relation's KIND, the same shape
    as the `third_party_claim` exemption. A carrier refused by any gate never
    reaches 0038's rule, so an instruction that is not a routine has no
    storage route BECAUSE Gate 3 refuses it, and that is the sentence 0038
    v6.2 now makes.
12. **Render is untouched, and this is the sentence a later reader looks for
    before extending this path.** A record written here is procedural BY ITS
    OWN STAMP and is excluded at the choke point, from recall's selection, the
    briefing and the wiki compiler exactly as a host-declared procedure is (the
    reviewer's reproductions confirmed the exclusion); `describe_procedures`
    shows it with the v18 attribution and applies its own frozen recognition
    rule to the summary (a gloss that reads as executable step text is
    withheld under `executable_detail`). Nothing here lets a stored procedure
    instruct the agent; a change that would is a new spec, not an amendment.

**The residual, MEASURED, with the threshold fixed before measuring.**
Research's labelled set of the ablation's 31 quotes
(`tests/eval/extraction_speech_act/ablation_31_labelled.jsonl`, its README
beside it; ONE rater, reasons per label; NOT a held-out set — the designer had
read them; it is the false-negative denominator): 9 clean user routines
expected to pass, 22 expected to refuse (17 assistant instructions, 2 one-time
actions, 1 intention, 2 borderlines). Threshold fixed beforehand and recorded
in the coordination ledger: at least 7 of 9 admitted, 0 of the 20 non-borderline
admitted (v19 wrote "0 of 22", counting the two borderlines the rule reports
without a threshold; corrected on research's read). RESULT: 8 of 9 admitted (the
miss is "I've been trying to recognize bird calls" — at v19 by the "trying to"
marker, at v20 by CLASS: "trying" is a volitional head); **0 of the 17 assistant instructions, 0 of
the one-time actions, 0 of the intention admitted; BOTH BORDERLINES ADMITTED**
(#4 a single ongoing project, #31 an exploration described as ongoing — both
first-person, present, habitual in FORM). That half of the threshold is NOT
MET and is stated as such, the labels unmoved after the score: **a grammar over
the span cannot tell a single ongoing project from a repeating practice**, and
that is this gate's named residual (2 of 31). The tier-8 pool of 66 bare
procedural inputs admits none.

**The HELD-OUT draw, threshold fixed before the labels arrived — FAILED, and
stated.** Research drew sessions 101–200 (disjoint, verified), froze a labelling
rubric BEFORE reading a quote (`HELDOUT-LABELLING-RUBRIC.md`, its digest in the
coordination ledger before the draw ran; eight classes, only `user_routine`
expected to pass), probed, labelled, and sent the files unrevised only AFTER dev
had stated the threshold: 51 quotes, 49 distinct spans; 45 distinct non-borderline
must-refuse spans (41 assistant instructions, 3 intentions, 1 third-party; 47
rows before de-duplication), 2 clean positives, 2 borderlines
(`tests/eval/extraction_speech_act/heldout_51_labelled.jsonl`, README and rubric
beside it). Threshold: ZERO admissions among the 45; no recall threshold — two
positives cannot distinguish 80% from 100%. RESULT: **three of the 45 admitted,
all one class — intentions phrased "I'm thinking of …" / "I've been thinking
about …"**, a surface form the aspiration lexicon does not carry; the threshold
is FAILED. Both clean positives admitted (descriptive); one borderline admitted
(a maintained condition), one refused. By the rule stated before measuring, no
marker was added to close an observed case (a marker added to close one case is
fitted to that case — the §8 detector's failure). What the failure shows, in
research's reading, is structural rather than a missing entry: the rubric's
intention row does not list "thinking of" either — the rater labelled from the
row's CRITERION (first party, but asserts the practice does not yet exist), while
the grammar must enumerate SURFACE FORMS of that property, so a marker list lags
a criterion permanently ("I keep meaning to", "I've been considering", "one day
I'll", "I'm going to start", "I want to get into the habit of" …). The decision
was the owner's — both arms were put to him and he chose the second ("Confirm
B", 2026-09-13; v20, below):
extend the aspiration lexicon with the observed form (closes three spans; buys
the next draw's forms only by luck), or make the grammar require a POSITIVE
assertion of current performance rather than accumulate negative markers, and
spend recall — which this corpus prices cheaply: a refused ambiguous span costs
a routine the user can restate, an admitted one puts words in their mouth, the
asymmetry that decided `correct()`. A third draw is the earliest HELD-OUT
measurement of v20. **The realistic capture yield of this feature is small:** with
~13 clean user-stated routines per 300 sessions AND a gate that must refuse
aspirations, a host should expect few captured procedures — a product fact
that follows from the numbers, not from the grammar, and is stated in the
CHANGELOG beside the feature.

**v20 — the POSITIVE form, re-measured with the thresholds fixed and recorded
before the run.** Thresholds (ledger, 16:47Z, the denominator corrected at
16:49Z on research's read, still before any run): 0 of 20 and 0 of 45 false
admissions; recall at least 7 of 9 on the 31; the 51's two positives as a
REGRESSION GUARD (two positives cannot measure a rate); the 66-pool admits none;
borderlines reported without a threshold. RESEARCH'S PREDICTION, on the record
before the number existed: v20 refuses #20 BY CLASS ("I've been trying" — a
volitional head), so 8/9 is the ceiling. RESULT, as it fell: **the 31 — 8 of 9
(#20 refused by class, as predicted), 0 of 20, borderlines #4 and #31 admitted
(unchanged); the 51 — 0 of 45 (v19's three "thinking of" intentions now refuse
without an entry naming them), both positives admitted (the guard held),
borderlines #12 admitted / #31 refused (unchanged). Every threshold MET.**
What this measurement is NOT: held-out. Research's cost note named positives
from both sets, so v20's design has seen them — this is a regression
measurement; the third draw (sessions 201–300, disjoint, labelled against the
rubric frozen before the first held-out draw, held unrevised and unsent until
the v20 run was reported done) is the held-out one, and it carries a disclosure
the first did not: research read the full v20 design, including the excluded
verb list, before labelling it. **The cost of the positive form, stated and MEASURED
for occurrence:** a lexical "do" head ("I do the dishes every night") is
refused because form cannot tell it from the auxiliary, and a present perfect
without "been" ("I've always run the linter") is not enumerated — both REAL IN
ENGLISH and UNMEASURED IN THIS CORPUS: research grepped the 121 labelled spans
of three draws and found ZERO occurrences of either, so v20 costs nothing
observable here, and a v21 that enumerated them could not be measured on this
corpus at this rate (said now, where it is queued, not discovered later). A bare
progressive ("I'm building a deck") refusing is NOT a cost: it is a project,
not a routine, and the head-shape enumeration doing the project/practice work
the borderlines showed a span grammar cannot otherwise do (three occurrences in
the 121, all expected-refuse). One asymmetry named rather than hidden: "I've
been doing great with meal prepping on Sundays" ADMITS while "I do the dishes
every night" REFUSES — the auxiliary ambiguity exists only in the present
simple, so `do` is decided by aspect, by form rather than content; tolerable
because the refusing branch is the rare one (below), not because it is right.
The "just" refusal trigger (v19's one-time class) is UNEXERCISED, not
validated: it occurs three times in the 121 spans, all expected-refuse, and in
each the other reason was independently sufficient; "I just make coffee every
morning" would refuse, and nobody should read three refusals as evidence the
trigger is safe.

**Draw 3 — the HELD-OUT measurement of v20, threshold stated before the run
(ledger 17:13Z).** Research drew sessions 201–300 (disjoint from both prior
draws, verified), labelled against the rubric frozen before draw 2, and held
the files unrevised and unsent until dev reported the v20 run done — having
read the v20 design, including the excluded verb list, before labelling (one
step less independent than draw 2; stated). 39 quotes, 39 distinct spans: 34
distinct non-borderline must-refuse (31 assistant instructions, 2 intentions,
1 one-time), 2 clean positives, 3 borderlines
(`tests/eval/extraction_speech_act/draw3_39_labelled.jsonl`, README beside
it; digests verified from the copied files). Threshold: ZERO admissions among
the 34; no recall threshold; research's prediction registered before the run:
#20 ("I've been trying to post at least 5–7 tweets per day" — a clean positive
by the rubric's criterion, labelled before the grammar could be consulted)
refuses BY CLASS, so recall 1 of 2. RESULT, as it fell: **0 of 34 admitted —
MET; recall 1 of 2 exactly as predicted (#22 "I usually meal prep on Sundays…"
admitted); borderlines #21 refused, #23 admitted, #38 refused.** A prediction
registered before a measurement is the only kind that can be wrong; this one
was registered, and held. The aspiration class appeared in all three draws
(draw 3's #31, "I just need to get into the habit of washing them regularly",
refused): a population, not a construction.

**What v20's recall rests on, and the caveat that bounds every recall figure
in this section.** Eleven of the thirteen clean positives across the three
draws are PRESENT-PERFECT-CONTINUOUS; exactly two are present simple (the 31's
#22 "I use it to play music…", draw 3's #22). So the PPC branch carries 11/13
of everything observed, the present-simple branch has been exercised by two
spans in 300 sessions, and the lexical-"do" cost bites only that branch. And
the concentration MAY BE A PROPERTY OF THE PROBE, NOT OF USER SPEECH: the
ablation asks a model to quote passages where the user describes how they do
something, and a model asked that of chat transcripts surfaces "I've been
X-ing" narration preferentially. If host traffic carries more present-simple
habituals ("I run the linter before merging", "I review invoices on Fridays"),
v20's recall THERE is essentially unmeasured. The figures — 8/9 and 2/2 on the
designed-from sets, 1/2 held-out — are a recall profile for THIS PROBE'S OUTPUT
DISTRIBUTION over LongMemEval, not for the feature over English; the
designed-from and held-out figures are never pooled into one headline
(11 of 13 across all draws, of which the held-out portion is 1 of 2).
Research's contingent question stands as a number rather than an argument: at
~13 clean routines per 300 sessions and a gate this tight, the feature's yield
is small; whether it earns its risk is the owner's, and `record_procedure`
remains the explicit path.

**The ceiling, in the rater's words:** one rater, not blind (research read the
grammar in prose and designed five of its controls), no second labelling, no
inter-rater ceiling, every label carrying its reason so a second rater can
disagree cell by cell; a gate/label disagreement (the first draw's #20, "trying
to" read as a routine by the rater and as aspiration by the grammar) cannot be
charged to either side. **The base rate this feature can be measured on:**
roughly 13 clean user-stated routines across 300 LongMemEval sessions (9 in the
first hundred, 2 in the second, 2 in the third — DRAW 1 IS THE OUTLIER, and
"~11 in 200", the rate v19 carried, over-stated it; research's correction) — the
§8 census's conclusion arriving a third time, from a corpus drawn to test
something else. **Attack #2 occurred
naturally:** "one of the guys at the meetup showed me how to use the tape to
create sharp, defined edges" — a method the user was taught, no assertion they
practise it; innocent, and the record would have claimed they practise it. That,
not a construction, is why the left-context and third-party refusals exist.

**What this is not.** Not a learning feature (A2's concern is the system
INVENTING a rule from an observed pattern; this path stores what the user
SAID of themselves, provably, or nothing); not a change to the ladder; not a
change to `record_procedure`, the stamp, or the stored rule; not a change to
render.

### 4b. The ingest contract — basis is a positive capability

A procedural record is written by `record_procedure` — and, since v16, by the
extractor path under §4a-iii, whose basis is DERIVED from a verified quote.
`record_procedure` writes only with a
declared basis: `EvidenceContext.direct(basis="stated")`,
`direct(basis="observed")`, or `derived(X, basis=...)`. The constructor
refuses a basis outside the closed domain (raises; nothing written).
`record_procedure` refuses a context that carries no basis (raises; nothing
written). The extractor path (`ingest_event` / `remember`) REFUSES a context
that carries a basis (raises) — it cannot produce a procedural record (F1),
so a basis there is a caller error, and accepting it silently would ship
declarative basis as a hidden feature. v16 changes the extractor's vocabulary
DELIBERATELY (§4a-iii): an emitted procedural relation is a governed outcome —
recorded when its quote verifies, refused and counted when it does not.

**The relation (round-1 F6).** `record_procedure` REQUIRES its `relation`
to exist in the ACTIVE registry with `relation_kind="procedural"`; a name
the registry does not hold, or one registered declarative, RAISES
(`ValueError`, `relation_not_procedural`) and writes nothing. V-TWO-PRODUCERS
therefore proves what it names for this producer: it writes only
procedural relations, and stamps `record_kind="procedural"`. A
relation reclassified AFTER the write moves nothing (§4a): the stamp is
the write-time fact.

**What `record_procedure` writes** (round-1 correction; round-2 F1 — the
three provenance axes are INDEPENDENT): a new `Edge` with `id` minted like
`remember`'s (`e-<12 hex>`), `subject="user"`, the given `relation`,
`object=summary` (whitespace-normalized), `note=note or ""`,
`valid_from=when or utcnow()` (a `when` beyond `MAX_FUTURE_SKEW` refuses as
ingest does), `provenance=Provenance(author_of_evidence=author,
derived_from=context.derived_from, basis=context.basis,
record_kind="procedural", evidence_ref=evidence_ref or f"procedure:{id}",
observed_at=valid_from, source_id=source_id, disclosure=<below>)`. The
AUTHOR is who asserted the procedure (the `author` argument, exactly as
`remember` takes it — a system- or assistant-authored procedure is
`author=SYSTEM`/`ASSISTANT` with `direct()`); the DERIVATION is what the
content derives from (`derived(X)` — `derived(SYSTEM)` means derived from
system content, not system-authored); the BASIS is how the author came by
it. v10 derived the author from the context and could not represent a
system-authored procedure honestly; V-PROVENANCE-AXES proves the three
cannot substitute for one another. **Disclosure is DERIVED,
never host-supplied, by the two shipped rules in order (v10):** first
0023's QUARANTINE-AT-BIRTH — if `source_id` is standing-revoked for the
user at write (`store.standing_revocations`, the digest rule at
`ingest.py:229`), the record lands QUARANTINED whatever its author and is
counted `quarantined_at_birth`, exactly as every edge of a revoked event
does under `ingest_event`; otherwise `_disclosure_for(author, relation,
context.derived_from)` (`ingest.py:141`) — computed from all three axes
under the shipped rule, so a derived-from-third-party procedure is
`use_only` exactly as a fact would be, whoever authored it. A `record_procedure` that skipped
the first rule would be a route to write from a revoked source, and the
sweep of 0023's birth-quarantine sites (V-BIRTH-QUARANTINE-HOLDS) fails on
it. This is the ONE route by which a procedural record is `quarantined`
(no procedural relation is the quarantine relation); a later revocation
INVALIDATES the record (`inactive`), never re-discloses it (the ratchet
rule). No episode is written (V-NO-EPISODE). Returns the new edge id. *(v24.6, 0055 §4g: the same call with
0055's credential report is `Memory.record_procedure_report`, which returns `{"edge_id": …}` plus
`credentials_withheld`; this method's `str` return is unchanged.)*

**Through MCP (round-1 F1): a DEDICATED `record_procedure` tool, not a
`basis` on `remember`.** `remember` on both surfaces never carries a basis
and rejects one. The MCP tool `record_procedure(summary, basis,
author="user", derived_from=None, relation="follows_procedure", note=None,
date=None)` (v17: no `source_id` argument; the deployment's binding is the
source identity, 0006 I1) — `author` and `derived_from` mirror MCP
`remember`'s own arguments — is a capability-gated adapter to
`Memory.record_procedure`: under `capability=direct` it validates the
relation exactly as the library does (exists ∧ procedural, else the tool
returns the serialized refusal `relation_not_procedural` and writes
nothing) and calls through with `author=EvidenceAuthor(author)` and
`context=EvidenceContext.direct(basis=basis)` or `derived(derived_from,
basis=basis)`; under `capability=none` it
REFUSES with the same named outcome as an attempted elevation, counted like
one — a host that has not attested first-party capture cannot declare a
basis. MCP also gains `describe_procedures(query=None)` returning
`DescribeResult` as JSON.

(The failure taxonomy these follow is stated once, at the head of §4.)

### 4c. Absence semantics — chosen once

Two situations, distinguished as 0011 E4 distinguished them:

- **At ingest, absence or malformation REFUSES and writes nothing.** A
  procedural event without a basis is a caller error, not a policy input.
- **At evaluation, absence is `basis_unknown`, a named non-allow.** A stored
  procedural-STAMPED record with `basis=None` (tamper — no shipped writer
  produces it, and since v11 a relation later registered as procedural
  does NOT reach records written before, because kind is read from the
  stamp) is not describable, never described by default, never raised on.

Pre-existing records: there are NONE to migrate. No relation is procedural
today (§2c-ii), so every record written before this version is declarative
and `basis=None` on it means exactly "not applicable". This is why the
scope is procedural-only: the three options for declarative absence
(default `stated` = trusted-by-omission; fail-closed = every existing edge
non-recommendable on upgrade; migration backfill = the store asserting
provenance on the host's behalf) do not arise, and the spec records that
they do not arise rather than choosing among them silently. A later spec
that extends basis to declarative records MUST choose one.

### 4d. What v1 does NOT build — recommendation

Stage 4 (recommend) does not exist for procedural records and is not
specified here. In particular this spec does NOT make an `observed`-basis
record recommendable after `confirm_edge`, although that composition
("history never confers authority; a capability increase needs an
independent governed event") is the natural next step: turning confirmation
into a GATE changes what a confirmation means, and the harness contract that
would consume a recommendation does not exist. A recommend predicate for
procedural records requires its consequence check; without it the
predicate must not be built (ruling 2). §10 Q2 carries this.

### 4e. Interfaces and migration

- Library: `Relation(relation_kind=...)`, `EvidenceContext.direct(basis=)` /
  `derived(X, basis=)`, `Provenance.basis`, `Provenance.producer` (v23), `Memory.record_procedure`,
  `Memory.describe_procedures`, `DescribeResult`, `ProcedureDescription`,
  `Withheld`.
- MCP: a new `record_procedure` tool (capability-gated adapter, §4b) and a
  new `describe_procedures` tool; `remember` UNCHANGED and rejecting any
  basis.
- CLI: NONE in v1 (round-2 F4). `veracium remember` keeps `--author` and
  `--derived-from` unchanged and gains NO `--basis`; there is no CLI
  procedure command. V-TWO-PRODUCERS' sweep classifies `cli.py` as a site
  that cannot produce a procedural record. A CLI surface, if a host asks,
  is a later version with its own capability behaviour, relation
  validation and producer sweep — not an option flag on a path that
  must reject basis.
- Export (round-3 F3 — "a v2 reader ignores it" DEMONSTRATED the failure):
  the two new keys change INTERPRETATION, not just representation, so an
  older reader that ignored them would render a procedural record as an
  ordinary declarative one. The shipped 0026 §3d precedent is the boundary,
  and it is mandatory: `FORMAT_VERSION` 10 → 11 (the procedural era),
  stamped CONDITIONALLY at write exactly as 0026 stamps 10 — an export from
  a store holding ANY record with `record_kind == "procedural"` or `basis
  is not None` stamps 11, which every older reader REFUSES ("export version
  11 is newer than this Veracium understands", `portability.py:291-293`,
  the refuse-don't-drop rule of 0010/0019/0026); a procedural-free export
  stamps 10 and is byte-identical to today's (V-DECLARATIVE-UNCHANGED's
  export leg). A file stamped 10 that nonetheless carries either key is
  an envelope that declares a version below its content: the import
  boundary reads the RAW record first — a raw procedural marker refuses
  that record with the signal named (round-4 F1) — and the I10 strip then
  runs only over the records that remain admissible, which by construction
  carry neither key. Refusal is per record, never per file. **(v23) The
  producer era, the same rule once more:** `FORMAT_VERSION` 11 → 12, stamped
  CONDITIONALLY — an export from a store holding ANY producer-stamped record
  stamps 12 and every older reader refuses it; a store whose procedural
  records all predate the stamp exports 11 exactly as before; a
  procedural-free export is unchanged. The refuse-don't-drop rule of
  0025/0026 §3d applies as written: a new exported field bumps the format so
  an old reader REFUSES rather than silently sheds it.
- Import: on the DEFAULT path a record is refused as procedural when ANY
  of THREE independent signals says so — stamp, basis, or the RECEIVING
  registry's kind for its relation — with the firing signal named (round-3
  F2; the six cells are §2c's); a basis in a foreign file was declared by
  another host, and 0005's principle applies. Under `restore=True` (v4) the
  store's own procedural records are ACCEPTED WITH THEIR DECLARED BASIS:
  `restore` is defined as the operator's assertion that the file is this
  store's own history, which is exactly the attestation basis requires, so
  a store's own backup round-trips its procedures; a record whose markers
  are inconsistent (either present without the other) is MALFORMED and
  refused per record; the registry signal does not fire on restore.
  Declarative records import as today on both paths. Export serializes
  procedural records on both paths. **Atomicity (round-1 correction):** the
  default import is ATOMIC over the ADMITTED set — procedural records are
  refused PER RECORD before the commit (the importer's existing per-record
  skip shape), counted in the report as `procedural_refused`, and the
  admitted declarative records commit as ONE transaction exactly as today;
  a file mixing both therefore imports its declarative records in full and
  none of its procedural ones, and the report says so. Nothing partial is
  ever committed. **(v23)** a raw `producer` is a FOURTH independent signal on
  the default path, named as such; on `restore=True` the consistency rule
  admits `producer` absent (the unstamped era) or in {`host`, `extractor`}
  beside the kind stamp, and refuses as `malformed_procedural_marker`, signal
  `producer`, one outside that domain or one on a record without the stamp;
  a `producer` in an envelope declaring a version below 12 is STRIPPED (0006
  I10 — a field newer than the declared version is never trusted) and the
  record restores as unstamped.
- Migration: NONE. The relation registry is code, not schema; `basis` and
  `record_kind` are JSON fields inside the existing payload; `basis` is
  `None` and `record_kind` is ABSENT (its key omitted by the wrap-mode
  serializer when None) on every declarative record, so no existing row
  and no 0029 journal `state` payload (V-VERBATIM is byte-exact there)
  changes bytes — a mechanism, executed, not an outcome asserted. The pre-feature oracle replays
  byte-identically (V-DECLARATIVE-UNCHANGED). (v23) `producer` is a third JSON
  field of the same shape — absent on every declarative record and on every
  procedural record already stored, so no row changes bytes and no migration
  runs; 0014's raw-request partition places it EXACT_EQUAL beside
  `record_kind` (a write-time fact absorption never recomputes; it binds the
  digest of the records it is set on and leaves every other digest unchanged,
  so the digest domain does not rotate). The doctor's `procedural` check
  reports `procedural_declared` (producer `host`), `procedural_captured`
  (`extractor`), `procedural_unstamped` (a procedural record with no
  producer — written before the stamp, or after it through a path other than
  `Memory`; the two cannot be told apart there and the doctor says so, and on
  a store created after the stamp existed a non-zero count is the live
  reading of the stated boundary, v23.1) and `procedural_shaped`, never added.
- Unrecoverable: nothing; the change is additive, and reversible to the
  extent §7 states (not "fully"). **(v24.4, round-8 finding 1)** an id the file names more than once is
  refused per copy as `duplicate_id`, signal `id`, before any other reading —
  a file cannot say two things about one record, and both file orders refuse
  the same copies; the inheritance lookup reads the destination's stored
  record FIRST and every incoming copy of an id together, so a persisted
  stamp or producer is never erased by an incoming copy, admitted or
  refused, and copies that disagree about a constraint leave it unresolved,
  which no successor satisfies. **(v24.5, round-9 F1)** a persisted producer is the
  constraint: a claimed ancestry, from an admitted or a refused copy, adds
  procedural-ness and never replaces it.

---

## 5. Regime analysis — where does this behave differently?

- **Scale:** the describe surface is a filtered read over the user's
  procedural records; it shares recall's cap (`max_subgraph_edges`, the
  default `limit`) and is tested at the truncation regime: a store with more
  procedural records than the cap must describe by the §4a-ii order, never
  store order, with stable ties and identical repeated runs — the 0.x
  regime defect's shape, pinned by V-DESCRIBE-ORDER (round-1 F8).
- **Cold vs warm:** none; no cache.
- **Density:** many procedural records under one subject are non-functional
  and accumulate; absorption's same-class rule applies with the whole-set
  minimum basis. Tested at the absorption regime.
- **Tests reach the regimes** (§6); the feature is on by default (the
  registry ships one procedural relation) but INERT until a host declares a
  procedural event — no shipped host does today, so the default-on state
  changes no existing behaviour (V-DECLARATIVE-UNCHANGED).

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **V-DECLARATIVE-UNCHANGED** every pre-existing edge is declarative; recall, context, export and MCP reproduce the pre-feature oracle byte-identically (the 0029 V-COMPAT oracle, extended with a procedural-free store) | `test_every_pre_existing_edge_is_declarative_and_unchanged` | CI |
| **V-KIND-STAMPED** (round-2 F2; replaces V-KIND-REGISTRY) a record's kind is the registry's declaration for its relation AT WRITE, stamped as `record_kind`, and every kind-dependent read (the choke point, the describe candidate set) reads the STAMP; a registry that reclassifies or drops a relation after the write changes NO stored record's treatment (mutant: read the registry instead of the stamp — a legacy custom declarative edge must still render; this mutant PASSES every product cell, which are generated under one registry, so the test MUST reshape the registry between write and read — the corpus's `STAMP_SURVIVES_REGISTRY_CHANGE` cell); the read rule is `stamp == procedural OR basis is not None` (mutant: basis alone — a stripped basis must NOT move a record into a block); the conflict cell (NO stamp — `None` — WITH a basis) is `kind_conflict`, procedural by floor, counted (mutant: silently procedural — the count must move); no text feature decides kind; the stamp's KEY IS ABSENT when None — a declarative `Provenance` serializes to today's 8 keys byte-for-byte, the three deliberate nulls kept (mutant: the default serializer, which emits `"record_kind":null` on every record — V-DECLARATIVE-UNCHANGED's pre-feature oracle and 0029's V-VERBATIM must both catch it) | `test_record_kind_is_stamped_at_write_and_read_from_the_record` | CI |
| **V-PROVENANCE-AXES** (round-2 F1) author, derived_from and basis are three independent carriers: every cell of `EvidenceAuthor` × {`direct()`, `derived(X)` for each X} × basis is writable through `record_procedure`, each stored field equals its own input, disclosure is `_disclosure_for(author, relation, derived_from)` for every cell, and NO argument substitutes for another (mutant: derive `author_of_evidence` from the context — the `author=SYSTEM, direct()` cell must fail) | `test_provenance_axes_are_independent` | CI |
| **V-ARGS-VALIDATED** (round-2 gap) every argument of `record_procedure` and `describe_procedures` refuses its empty and malformed forms as §2c and §4a-ii state (type → `TypeError`, value → `ValueError`, each named), with the store byte-identical after every refusal; `limit` zero, negative, `bool`, non-int and above-cap all refuse | `test_record_procedure_validates_every_argument_and_writes_nothing` + `test_describe_limit_and_query_are_validated` | CI |
| **V-EXTRACTOR-QUOTE-GATED** (v16; v19: the first two gates) the prompt vocabulary CARRIES every registered procedural relation; a procedural triple reaches storage only through §4a-iii's ordered gates, the first two being author=USER and the whitespace-normalised verbatim substring; a missing, empty, paraphrased or unverifiable quote, or a non-user author, is REFUSED and counted — never filed as `unclassified`, never stamped; a retry repair never lands on a procedural relation | `test_a_quoted_user_routine_is_recorded_as_a_procedure_and_never_rendered`, `test_a_procedural_emission_without_a_verifying_user_quote_is_refused_and_counted`, `test_the_prompt_vocabulary_carries_the_procedural_relation`, `test_the_retry_cannot_mint_a_procedure` (`tests/test_0037_capture.py`) | CI |
| **V-ACTOR-PRESENT** (v19; POSITIVE-FORM at v20; at v21 a DIRECTIVE class and any SECOND PERSON refused — round-2 finding 2, "I request that you review invoices today"; at v22 a SUBORDINATE lead clause must end at a comma — "If I review invoices daily, the queue stays short." refuses; the grammar is the ONLY filter between a user's sentence and stored text; mutants: admit a directive head, admit "you", let the lead clause run to the head; `test_the_round_2_grammar_refusals_end_to_end`, `test_the_round_3_passage_selections_are_refused_end_to_end`, `test_the_grammar_against_the_fourth_draw_meets_the_held_out_threshold`) the quoted span opens with the user asserting a CURRENT, REPEATED performance — after an optional leading temporal/conditional clause, first-person SINGULAR in one of three enumerated head shapes (present simple with optional negator/frequency adverb; present perfect continuous; present progressive only with a frequency marker) whose head verb is a lexical ACTION verb, modals/auxiliaries refused and the cognitive/volitional class refused BY CLASS through the symmetric stem, the SPAN head deciding, every unenumerated form failing CLOSED — and (kept from v19) carries no report, rejection, aspect, norm, request, aspiration, question, one-time or past marker; its left context in the event ends in no quotation or attribution frame; research's nine constructions, the reviewer's one-time instruction, the red team's quoted-third-party-in-first-person, first-person-plural and aspiration cases all refuse; the positive set (the ablation's routines and the v16 fixtures) admits; the 66-item bare-procedural pool admits none; the labelled 31 measure recall 8/9 with the two borderlines admitted and stated as the residual (the miss by CLASS at v20); the held-out 51: 0 of 45 admitted at v20 (v19 admitted three "thinking of" intentions), both positives admitted as a regression guard; the positive form refuses every unenumerated head (modal, auxiliary, bare progressive, present perfect without "been", a cognitive head under every inflection, the complement construction) and admits the three shapes with an action head; mutants: drop the left-context check (the phishing quote admits), drop the past check ("I just used…" admits), admit "we", drop the positive form ("I'm thinking of…" admits), drop the marker list ("I run the linter, Marcus told me" admits) | `test_the_actor_present_grammar_refuses_reports_rejections_aspect_norms_and_requests`, `test_a_declared_one_time_instruction_is_refused_not_stored_as_a_procedure`, `test_the_red_team_constructions_are_refused`, `test_the_grammar_and_the_grounding_admit_the_users_own_stated_routines`, `test_the_bare_procedural_pool_never_passes_the_grammar`, `test_the_grammar_against_the_labelled_ablation_quotes_meets_the_threshold_fixed_beforehand`, `test_the_grammar_against_the_held_out_draw_meets_the_threshold_under_the_positive_form`, `test_the_positive_form_refuses_every_unenumerated_head`, `test_the_positive_form_admits_the_enumerated_shapes_with_an_action_head`, `test_the_positive_form_is_a_second_gate_not_a_replacement_of_the_markers` (`tests/test_0037_capture.py`) | CI |
| **V-WHOLE-SENTENCE** (v22; round-3 findings 2 and 3; v24, round-4 findings 1a/1b/2 — boundaries are KINDS; v24.1, round-5 findings 1 and 2 — boundaries are ESTABLISHED at BOTH ends or the passage is declined, no list) the quoted span is exactly one whole sentence of the event: it begins at an ESTABLISHED boundary — the start of the event, or a `?`/`!` run followed by whitespace and an uppercase letter, digit or opening quote — never after an ambiguous run and never mid-token; it ends at the end of the event (a closer may follow), at its own `?`-free terminal run that is itself established, or immediately before a plain `.`/`!` it omitted at the end of the text — never before an omitted `?`; a `.` between digits is inside a sentence; a run carrying `?` is a question and refuses the sentence it ends while establishing the next start; EVERY mid-text period, an ellipsis, and a `!` before anything but a sentence start are AMBIGUOUS and refuse; the kinds are total (every shape has one; the unrecognised is ambiguous). A fragment inside a framing sentence, a fragment starting or stopping mid-sentence, a passage after "e.g." or "...", two sentences however joined, a sentence ending in `?`, and ANY sentence before or after a period-terminated neighbour all refuse before the grammar (the stated cost); the whole `$100.50` sentence, a routine that is the whole turn, and a routine after a `?` or `!` admit and store as written; mutants: accept an omitted `?`, treat a decimal point as a boundary, admit `daily.archive`, admit a start after `e.g.`, let any list or word-shape establish a period boundary, read `doesn't.` as the letter `t` | `test_the_round_3_passage_selections_are_refused_end_to_end`, `test_a_whole_sentence_of_the_event_is_admitted_and_stored_as_written`, `test_the_first_sentence_admits_while_the_declared_second_instruction_is_not_carried`, `test_the_round_4_boundary_and_head_cases_are_refused_end_to_end`, `test_the_round_4_controls_admit_and_store_the_sentence_as_written`, `test_the_boundary_kinds_are_total_and_fail_closed`, `test_the_former_open_residual_is_closed_and_no_list_remains` (`tests/test_0037_capture.py`) | CI |
| **V-INHERITANCE-AT-IMPORT** (v24.1; round-5 finding 3; v24.2, round-6 finding 2: the lookup sees REFUSED predecessors; v24.3, round-7 finding 2: the lineage helper reads EVERY import signal and inheritance is VALIDATED) the import boundary applies V-STAMP-INHERITED and V-PRODUCER-INHERITED to every incoming record against its predecessor — looked up by id among the RAW incoming records, before any refusal, or the destination's existing records, so the check is independent of file order and a predecessor refused on the default path still constrains its successors; procedural-ness is by LINEAGE over the SAME four signals the filter reads — stamp, basis, producer, and the receiving registry's kind on the default path (a record whose predecessor is procedural by lineage is procedural whatever markers it carries, so a chain that drops the markers one hop later is refused one hop later too; a cycle fails closed); the inherited producer is validated down the chain — a record whose own producer disagrees with its lineage's validated producer is a rejected intermediate and the constraint it violated carries on to its successors unchanged (a raw field of a rejected record never substitutes for validated inheritance) — before anything commits, on both paths: a successor that drops the markers, or names a different producer or none where the lineage has one, is refused per record as `inheritance_violation` with the signal and the predecessor named and counted; matching producers restore; a declarative lineage imports whole; mutants: read stamp and basis only, trust a rejected intermediate's own producer; **(v24.4, round-8 finding 1)** conflicting ids are resolved BEFORE lineage is derived: every copy of a duplicated id is refused as `duplicate_id`, the lookup reads the stored record first and every copy together (a rejected copy cannot erase a persisted constraint), and copies disagreeing about a constraint leave it unresolved, which no successor satisfies — both file orders give one disposition and one set of stored rows; mutants: keep the last copy per id and prefer it over the stored record; read the stored record's own-ness as stamp-or-basis (research's pre-seal A); let the stored record's predecessor set replace the incoming copies' (research's pre-seal C); **(v24.5, round-9 F1)** a PERSISTED producer is the constraint — a claimed ancestry from an admitted or a refused copy adds procedural-ness and never replaces it, so a successor that disagrees with its actual stored predecessor is refused whatever the file claims about that predecessor's ancestry, and a persisted record without a producer takes the claimed chain's (a claim adds a constraint, never removes one); mutant: let the chain's validated producer override the stored one | `test_restore_applies_the_inheritance_rules_the_store_applies_to_a_write` (both orders), `test_inheritance_is_checked_against_an_existing_destination_predecessor_on_both_paths`, `test_the_default_path_keeps_a_refused_predecessor_for_its_successors_inheritance` (both orders, a two-hop chain), `test_lineage_reads_every_import_signal_and_carries_validated_inheritance` (both orders: a registry-only predecessor, a producer-only predecessor, a restore chain with a rejected intermediate, the intact control) (`tests/test_0037_producer_stamp.py`), `test_stored_and_incoming_custody_read_one_procedural_signal_set` (both orders: a registry-only predecessor stored vs incoming; a stored declarative record shadowing a forged chain, with its empty-destination control; the sentinel), `test_conflicting_ids_are_resolved_before_lineage_in_both_orders` (both orders: the two round-8 forms, the valid re-import control, agreeing and disagreeing duplicates, stored-record precedence, a duplicated intermediate, ordinary duplicates), `test_a_persisted_producer_is_never_replaced_by_claimed_ancestry` (Q stored and incoming × both orders: the reviewer's case, its control, the agreeing claim meeting the store's same-id rule, the unstamped stored predecessor) | CI |
| **V-EPISTEMIC-HEADS** (v24; round-4 finding 3) the cognitive class contains `doubt`, `deny`, `suspect`, `presume` (and `wonder`, `suppose`, `assume`, `figure`, `guess`, `reckon` since v20), so "I doubt I review invoices daily." refuses on its head END TO END — the refusal §4a-iii claimed is now the code's; `question` and `bet` are NOT in the class and their routine senses admit ("I question every invoice over $500.", "I bet on horses every Saturday."), the must-not-refuse half a draw could not supply; the pre-existing `figure` cost is pinned | `test_the_epistemic_class_is_what_the_spec_says_and_its_costs_are_pinned`, `test_the_round_4_boundary_and_head_cases_are_refused_end_to_end`, `test_the_round_4_controls_admit_and_store_the_sentence_as_written` (`tests/test_0037_capture.py`) | CI |
| **V-DRAW-5-FULL-PATH** (v24; the round-4 ask) every one of draw 5's eleven labelled user-turn pairs runs through `Memory.remember` (context DECLARED) → the store → `describe_procedures`: an admitted pair stores exactly `norm_ws(quote)` with an empty note, basis `stated`, producer `extractor`, and describes with the quote as summary and the prefixed attribution; a refused pair writes nothing procedural and is counted; under v24.1 0 of 6 positive rows = 0 of 4 distinct positive passages admitted (both v24 admissions sat before a period-terminated neighbour — the stated cost, thresholds fixed first), 0 of the must-refuse rows, all eleven refusals counted, the admitted count asserted beside the verdicts | `test_the_draw_5_labelled_pairs_through_the_full_path` (`tests/test_0037_capture.py`) | CI |
| **V-GLOSS-DERIVED** (v21, replacing V-GLOSS-GROUNDED — round-1 and round-2 finding 1, the owner's word; v22, round-3 finding 1: NO transformation) the stored gloss of a captured procedure IS the verified span, whitespace-normalised and nothing else, and the model's `object` is discarded; a mid-sentence relative clause and the condition after it are stored whole ("I review invoices, which arrive daily, only after approval."); every pinned line equals its normalised quote; the sixteen observed positives' derived glosses are pinned and regenerated; the reviewer's two F1 constructions store "I don’t review invoices" and "I review invoices and archive receipts"; the red team's three gloss attacks (negation dropped, order reversed, condition dropped) cannot be emitted; the rejected subject-dropping design is pinned as its failure (the fragment is withheld by describe's frozen floor, the sentence is rendered); mutants: keep the model's gloss (the unrelated-summary test), drop the subject (describe withholds), cut the relative clause (the condition after it lost) | `test_a_genuine_quote_with_an_unrelated_summary_stores_the_derived_span_never_the_summary`, `test_the_stored_gloss_is_derived_from_the_span_and_the_models_summary_is_discarded`, `test_the_derived_gloss_keeps_negation_order_and_condition`, `test_the_derived_gloss_of_every_observed_positive_is_pinned`, `test_the_derived_gloss_is_not_withheld_by_describes_frozen_floor`, `test_every_literal_the_grammar_matches_against_survives_the_tokenizer` (`tests/test_0037_capture.py`) | CI |
| **V-SUMMARY-CONTRACT** (v19; at v21 applied to the DERIVED gloss — a span whose derived text exceeds 512 characters is refused and counted) (v19) one summary contract for BOTH producers — whitespace-normalised, non-empty, at most `MAX_SUMMARY_CHARS` (512) — applied on the extractor path before the grammar and the grounding, a breach refused and counted; the host path's rule unchanged | `test_the_summary_contract_is_one_for_both_producers` (`tests/test_0037_capture.py`) | CI |
| **V-STAMP-INHERITED** (v19; research's red team) the store's one edge-persistence choke point refuses any edge whose `supersedes` names a persisted procedural predecessor unless the edge is itself procedural — keyed on the persisted predecessor's stamp/basis; a hand-built non-procedural successor is refused; mutant: key on the registry, or on the incoming edge's id | `test_correcting_a_captured_procedure_is_refused_and_the_quote_never_renders` (`tests/test_0037_capture.py`) | CI |
| **V-NO-CORRECTION-OF-PROCEDURES** (v19) `correct()` on a procedural record refuses with the named reason `correction_of_procedure` and writes nothing — a correction's successor would carry the host's text under the user's `stated`; end to end: a captured procedure, one `correct()`, and recall's context carries neither the gloss nor the span; `note` holds no copy and no digest is stored (v21: `object` IS the derived span, kept out of context by the render exclusion) | `test_correcting_a_captured_procedure_is_refused_and_the_quote_never_renders` (`tests/test_0037_capture.py`) | CI |
| **V-ATTRIBUTION-HONEST** (v18) describe's `stated` attribution claims only what BOTH producers establish — that the user SAID it ("recorded from something you said: <gloss>") — never that the user FOLLOWS it; the gloss only, the note never; (v19: research's nine no longer store — V-ACTOR-PRESENT refuses them; the sentence is asserted on the positive set and on the host-declared producer, and it contains neither "follow" nor any word of the span); mutant: restore "you said you follow", or render the note | `test_the_stated_attribution_claims_utterance_not_endorsement` (`tests/test_0037_capture.py`) | CI |
| **V-TWO-PRODUCERS** (v16; replaces V-ONE-PRODUCER — F1, F3; round-2 F4) exactly TWO src sites write a procedural STAMP (v19: the sweep recognises a LITERAL `record_kind="procedural"` keyword and REFUSES the forms that would escape it — a non-literal `record_kind=` keyword, a `Provenance(**…)` call, a dict literal carrying a `record_kind` key — anywhere in src, proven by a planted file; v23: the residual it named since v19 — a stamp minted through an attribute chain the sweep cannot see — is CLOSED by V-PROVENANCE-FROZEN, so the sweep's grammar is the whole grammar): `procedures.py` (`record_procedure`, the host's declared basis) and `ingest.py` (the quote-gated extractor path, §4a-iii, derived basis) — the sweep basis is 0029's OWN write-site registry (`EDGE_WRITE_SITE_RULINGS` × the raw-SQL sweep of `tests/test_0029_carrier.py`), never a fresh inventory; every other site either refuses a procedural record on the default path (the import commit) or does not exist (the CLI: `cli.py` is classified cannot-produce, and a `--basis` option appearing there fails this test); the one other admitting site, `restore=True`, admits only what this store previously wrote and the operator re-asserts; a write site absent from the registry fails 0029's gate first | `test_the_two_producers_are_exactly_the_host_surface_and_the_quote_gated_extractor`, `test_the_producer_sweep_refuses_non_literal_stamp_forms` (`tests/test_0037_procedural.py`) | CI |
| **V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE** (F3, corrected v4; round-3 F2; round-4 F1) on the DEFAULT path the three signals (stamp / basis / receiving registry) are evaluated ON THE RAW RECORD, BEFORE version normalization, for every declared format version; a record is refused as procedural when ANY fires, the refusal NAMES the signal (and `raw: true` when the envelope declared a version below the key), refusal is per record; the six §2c cells AND the format-10 8-cell matrix hold (mutant: normalize — strip the newer-than-declared keys — BEFORE inspecting: the format-10 cells "procedural stamp × unknown relation" and "basis × declarative relation" must fail, the only cells the single v12 cell could not reach) — in particular BOTH markers stripped under a relation this host registers procedural is REFUSED (`registry`), and both stripped under an unknown relation imports as declarative exactly as today (mutant: drop the registry signal — the both-stripped cell must fail); declarative records in the same file import unchanged; no foreign `basis` reaches a stored record; under `restore=True` the SAME file round-trips its procedural records WITH their declared basis, byte-identical to the exporting store's rows (the positive leg — a refusal-only test would pass while backup/restore was broken); a restore-path record with EITHER marker absent, or an out-of-domain basis, is refused as malformed | `test_default_import_refuses_procedural_records_on_any_signal` + `test_restore_round_trips_procedural_records_with_basis` | CI |
| **V-OLD-READER-REFUSES** (round-3 F3) an export from a store holding any procedural record is stamped `FORMAT_VERSION` 11 and a reader whose `FORMAT_VERSION` is 10 (the shipped reader with its constant held at 10 — the old reader, executable today) REFUSES the whole file with the version error, writing nothing; an export from a procedural-free store is stamped 10 and that same reader accepts it byte-for-byte; mutant: unconditional 10 — the old reader must then ACCEPT the procedural file and the test must catch the procedural record entering as declarative | `test_old_reader_refuses_a_procedural_export` | CI |
| **V-PROVENANCE-FROZEN** (v23) `Provenance` is a frozen model: ordinary assignment to any field of a built stamp raises and leaves it unchanged; a copy with an update is a NEW object; no src site assigns to a provenance attribute (an AST sweep over every `<expr>.provenance.<field> = / op= …` form, with a planted control) — the eight sites that did (absorption's three inheritances, the store's confirmation and recompute pairs, the decay path's augmented assignment) replace the provenance on an edge that keeps its identity | `test_provenance_is_frozen_after_construction`, `test_no_src_site_assigns_to_a_provenance_attribute` (`tests/test_0037_producer_stamp.py`) | CI |
| **V-PRODUCER-STAMPED** (v23) every procedural record written by this version carries `producer` ∈ {`host`, `extractor`}, minted at exactly the two producer sites with a literal (the sweep of `producer=` keywords over src finds `procedures.py` → `host`, `ingest.py` → `extractor`, nothing else and no non-literal); a declarative record carries none (key omitted; refused at construction if supplied) and a procedural record from before the stamp validates with none; `producer` is EXACT_EQUAL in 0014's partition beside `record_kind` | `test_the_producer_stamp_is_written_at_exactly_the_two_producer_sites`, `test_record_procedure_stamps_host_and_the_capture_path_stamps_extractor`, `test_a_declarative_record_carries_no_producer_and_a_legacy_procedural_record_needs_none`, `test_the_0014_partition_places_the_producer_with_the_kind_stamp` (`tests/test_0037_producer_stamp.py`); `test_raw_request_field_partition_is_total` (`tests/test_0014_receipt_split.py`) | CI |
| **V-PRODUCER-IMMUTABLE / V-PRODUCER-INHERITED** (v23) at the store choke point a same-id replace that changes, drops or adds a producer is refused with nothing written (both directions, as the kind stamp and basis are); a successor of a producer-stamped record carries the SAME producer or is refused; a legacy predecessor with no producer constrains nothing | `test_producer_is_immutable_on_same_id_replace_and_inherited_across_a_supersession` (`tests/test_0037_producer_stamp.py`) | CI |
| **V-PRODUCER-ERA** (v24; v24.1: the doctor claims nothing about WHY a producer is unknown — a format-11 record restored into a new database gives `unstamped=1` through an ordinary path, round-5 finding 4; every cause named, none inferred) export stamps 12 iff a producer-stamped record exists (11 for a store whose procedural records all predate the stamp; the pre-feature stamps otherwise), an older reader refuses a 12 file outright, `restore=True` round-trips the producer verbatim; a producer in a sub-12 envelope is stripped and the record restores unstamped; on the default path a raw producer is the fourth named refusal signal; on restore a producer outside its domain or without the kind stamp is `malformed_procedural_marker` with signal `producer`; the doctor reports declared / captured / unstamped / shaped as four numbers never added, with the unstamped bucket as the negative control | `test_the_export_stamps_12_only_for_a_producer_bearing_store_and_old_readers_refuse`, `test_a_producer_in_a_pre_12_envelope_is_stripped_and_a_raw_producer_is_a_refusal_signal`, `test_the_doctor_reports_declared_captured_and_unstamped_as_three_numbers_never_merged`, `test_the_store_boundary_is_stated_in_both_specs_and_the_host_documentation` (`tests/test_0037_producer_stamp.py`); `test_default_import_refuses_procedural_records_on_any_signal`, `test_old_reader_refuses_a_procedural_export` (`tests/test_0037_procedural.py`) | CI |
| **V-CORPUS-ROWS-IN-DOMAIN** (round-3 F1 + correction 4; wording narrowed round 4) every row of the frozen corpus is validated against the declared DOMAINS of `record_kind` (`{None, "procedural"}`) and `basis` (`{None, "stated", "observed"}`) and the four-state table — DOMAIN VALIDATION NOW, real `Provenance` construction from the row AFTER implementation (the wider phrase "validates through the field types" is not claimed until then); a string-only generator that emits `"declarative"` fails here | `test_every_corpus_row_is_in_the_declared_domain` | CI |
| **V-OUT-OF-PATH** (F2 + Q1; round-3 correction) a procedural record — by the STORED rule, `record_kind == "procedural" OR basis is not None`, never the registry — is excluded at the model-context choke point with the named outcome `procedural_out_of_scope`, for every author × disclosure × basis cell (enumerated from the enums), and appears in NEITHER block; `Edge.assertable` is byte-unchanged (its source pinned) | `test_procedural_records_never_reach_model_context` + `test_assertable_is_untouched` | CI |
| **V-RENDER-SITES** (F2) every site that renders records into model context — DERIVED by sweep (gate, recall, compile, proactive, selfcheck), never hand-listed — reaches the one exclusion; a new render site without it fails here | `test_every_model_context_site_excludes_by_kind` | CI |
| **V-BASIS-POSITIVE** a procedural event without a declared basis REFUSES at ingest and writes nothing (store byte-identical after the refusal) | `test_procedural_ingest_requires_a_declared_basis` | CI |
| **V-BASIS-CLOSED** a basis outside `{stated, observed}` (any type, incl. unhashable) raises at construction; nothing written | `test_basis_domain_is_closed_and_refuses_at_construction` | CI |
| **V-BASIS-SCOPE** a basis on a declarative event is refused | `test_basis_on_a_declarative_event_is_refused` | CI |
| **V-ABSENCE-NAMED** a stored procedural record with `basis=None` yields the named non-allow `basis_unknown`, never a default, never a raise | `test_procedural_record_without_basis_is_a_named_non_allow` | CI |
| **V-BASIS-CAP-ONLY** no operation (same-id replace, absorption, import, confirm, reinforcement) can move a record from `observed` to `stated`; absorption carries the whole-set minimum | `test_basis_can_only_subtract` | CI |
| **V-BASIS-IMMUTABLE** a stored basis never changes on same-id replace (the 0019 U4 shape) | `test_stored_basis_is_immutable` | CI |
| **V-DESCRIBE-CONJUNCTION** `describe_procedures` describes iff every conjunct holds, in the stated order, and otherwise returns the FIRST failing conjunct's named outcome; the outcome set is closed and enumerated exhaustively (a 0013-style oracle over the cell product, §6a) | `test_describe_outcomes_are_named_and_total` | CI |
| **V-RESULT-SCHEMA** (round-1 F2; pre-seal F-A) BEFORE truncation every visible procedural record is in exactly ONE of `descriptions` / `withheld`; after the cut `total_describable + len(withheld)` equals the visible population, `len(descriptions) == min(total_describable, limit)`, and `truncated == (len(descriptions) < total_describable)` — asserted on a store ABOVE the cap; no field of either type carries the `note` or any raw stored JSON; the query echo is normalized | `test_describe_result_schema_accounts_for_every_visible_record` | CI |
| **V-DESCRIBE-ORDER** (round-1 F8) with more procedural records than the cap, `descriptions` is the §4a-ii order (relevance ⟶ valid_from desc ⟶ edge_id asc; recency then id under a null query), the cut is applied AFTER ordering, ties are stable, and ten repeated calls on an unchanged store are byte-identical; a store-order result fails | `test_describe_orders_by_relevance_above_the_cap_and_is_stable` | CI |
| **V-NO-IMPLICIT-RECOMMEND** (round-1 F3, the actual guarantee) the `note` is rendered in NO field; a summary matching the FROZEN recognition rule (§6a) is withheld as `executable_detail`; must-match AND must-NOT-match cases from the frozen corpus, the homograph facts by name; the paraphrase boundary is asserted as a KNOWN PASS (a control that documents the limit rather than a test that pretends it away) | `test_describe_withholds_the_frozen_rule_and_never_renders_the_note` | CI |
| **V-SCOPE-OUTERMOST** (round-1 F5) a HIDDEN procedural record appears in neither list — an unauthorised principal's result for an existing hidden record is byte-identical to the result for a nonexistent one (the existence-oracle cell); a VISIBLE `use_only` or `quarantined` record is in `withheld` with that named outcome and no text | `test_hidden_is_indistinguishable_from_no_match` + `test_use_only_is_named_not_described` | CI |
| **V-WITHHELD-QUERY-BLIND** (round-1 F5, research) for the same principal and store, `withheld` — membership and order — is byte-identical across any two queries and the null query; a query-dependent `withheld` (the search-oracle mutant: filter it by relevance) fails | `test_withheld_membership_is_independent_of_the_query` | CI |
| **V-BIRTH-QUARANTINE-HOLDS** (v10) `record_procedure` under a standing-revoked `source_id` writes the record QUARANTINED and counted `quarantined_at_birth`, byte-for-byte the disclosure `ingest_event` would give the same event; the sweep basis is the set of sites that read `standing_revocations` (derived by grep in the test, the new surface must be among them); control: the same call with an unrevoked source is `mentionable`; a later revocation of that source invalidates the record (`inactive`) and does not change its disclosure | `test_record_procedure_honours_quarantine_at_birth` | CI |
| **V-RELATION-VALID** (round-1 F6) `record_procedure` raises and writes nothing for a relation that is unknown to the active registry, not a str, or registered declarative; the store is byte-identical after the refusal; control: the registered procedural relation writes | `test_record_procedure_requires_a_registered_procedural_relation` | CI |
| **V-RELATION-UNREGISTERED** (round-1 F7; NARROWED by round-2 F2) a PROCEDURAL-stamped edge whose relation is absent from the active registry is `relation_unregistered`: in neither model-context block, in `withheld` when visible, still in the store and in `introspect`; a registry that regains the relation restores it; and — the half that closes the regression — an UNSTAMPED edge (`record_kind` None, no basis) whose relation is absent (a legacy custom relation, a pre-feature row) renders in recall BYTE-IDENTICALLY to the pre-feature oracle and is no describe candidate | `test_unregistered_procedural_stamp_is_named_and_unregistered_declarative_is_unchanged` | CI |
| **V-HOST-DECLARED** (round-1 F1; v16; v17) through MCP the HOST-DECLARED procedural write path is the `record_procedure` tool (v16: `remember` under `direct` can also capture one through §4a-iii's quote gate, where the user's own words are the declaration; v17: the tool takes no `source_id` argument — the deployment's binding is the source identity, 0006 I1, asserted by `test_the_served_record_procedure_tool_takes_the_deployment_binding_not_an_argument` in `tests/test_0006_require_source_id.py`): under `capability=direct` it validates the relation and writes through the library surface; under `none` it refuses with the attempted-elevation outcome, counted; MCP `remember` with any basis-shaped input writes nothing and returns the named refusal | `test_mcp_record_procedure_is_the_host_declared_procedural_write_path` | CI |
| **V-NO-EPISODE** (F4) `record_procedure` writes NO episode: the user's episode count is unchanged by a procedural write, and no episode text contains the procedure's summary or note; control: ordinary `remember` of the same text writes one | `test_record_procedure_writes_no_episode` | CI |
| **V-CARRIERS** every carrier of `basis` AND of `record_kind` accounts for it in one commit — the sweep basis is DERIVED: every `Provenance(` constructor site and every `model_copy(update=` site (both forms, 0016's tenth-site lesson) plus every `provenance.` reader in src, each classified as carrying, passing through, or not applicable; a site absent from the classification fails | `test_basis_reaches_every_carrier` | CI |

Standing checks that must not regress: injection asserts 0 · cross-user leaks
0 · trust canaries 0 · the 0029 corpus 19/19 · the 0030 module 29/29.

### 6a. Acceptance measurement — REQUIRED, FINITE

A correctness gate over a frozen scripted corpus. **Ownership (round-1 F4,
resolved):** RESEARCH freezes the expectations, DEV owns the runner — the
0029 pattern, for its reason: the seat that implements may not set its own
bar. Research's self-imposed condition applies verbatim: every expectation
derives from THIS spec's text, never from dev's plan or code, each carrying
the line that determines it; where the spec does not determine a value it
is marked OPEN and asked, never guessed. The freeze happens against THIS
version (a corpus frozen against a spec under revision freezes the wrong
bar) and BEFORE any implementation line.

- **Artifact and version (round-2 F3 — IN THE REPO, digest IN THIS
  SPEC):** `tests/eval/procedural_describe/MANIFEST.json`, research-authored,
  byte-copied into the tree by dev at each amendment, versioned by
  amendment. The digest is the ONE line below (its literal form is the
  line research's manifest removes before hashing this spec — a
  bidirectional, non-circular binding: the spec pins the corpus by
  digest, the corpus pins the spec by version plus the digest of the spec
  text with that single line excluded). `tests/test_0037_corpus_pin.py`
  reads the digest from that line and asserts the file hashes to it (data
  to data), so a spec whose corpus is unbound cannot pass the suite and a
  corpus edited without its spec line cannot either. At acceptance the
  same digest moves into `## Review closure`.

corpus sha256: 5784f1f34d768fabf3644645c48278b8ad9244903686f2e41c883918a65fb3af

- **Cells — GENERATED, not enumerated here (round-2 fold, research's
  finding on v11's first draft):** the corpus generates its product cells
  from its own verbatim copies of §4a-ii's ordered predicate and candidate
  set (`predicate_ordered_verbatim_from_4a_ii`,
  `candidate_set_verbatim_from_4a_ii` in the manifest), so the cell list
  cannot disagree with what produced it; this bullet does not restate the
  axes, because a prose axis-list no test reads is a hand-maintained list
  standing in for a generated one and reads as rigour exactly while it
  drifts (v11's first draft listed one axis the corpus carries as a named
  cell and omitted the one v11 added). What this spec DOES fix by name:
  `record_kind` is an AXIS whose declarative value is REPRESENTED as JSON
  `null` — the field's domain is `{None, "procedural"}` and the corpus
  encodes the stored value, not an axis label (round-3 F1: the first
  amendment wrote the string `"declarative"` into 486 cells, a value the
  field cannot hold, and nothing validated a row against the type — every
  row is now validated through the declared domain, V-CORPUS-ROWS-IN-DOMAIN,
  and through the real `Provenance` once it exists); the v10 corpus was
  silently the procedural-stamped half; the unstamped half collapses to two
  outcomes by basis alone, and that collapse IS the coverage that makes "a
  registry change touches no declarative record" falsifiable; the six
  import/restore cells of §2c and the format-10 8-cell marker × registry
  matrix (round-4 F1; the two cells that catch strip-before-inspect
  annotated) are named cells; every row is validated against the declared
  domains now, and through the real `Provenance` after implementation; each cell carries
  its expected `DescribeResult` membership and named outcome AND its
  expected ABSENCE from recall's two blocks; **disclosure is NOT an axis**
  (derived by `_disclosure_for` and birth-quarantine — a COMPUTED column;
  a disagreeing row exists only written directly and LABELLED
  corrupted-state, 0028 §4b-iii's form); and the NAMED cells, each of
  which catches a mutant the product cannot: the existence-oracle cell
  (an unauthorised principal probing an existing hidden record vs a
  nonexistent one); the declarative control (declarative records in the
  same store, registered or NOT, in neither list and not counted); the
  revoked-source-at-write cell (§4b); `STAMP_SURVIVES_REGISTRY_CHANGE` —
  the registry RESHAPED between write and read, the only cell that can
  catch V-KIND-STAMPED's headline mutant, since every product cell is
  generated under one registry and read-the-registry passes all of them;
  `kind_conflict_counted` (treated right but NOT counted passes every
  accounting check while erasing the tamper signal); and
  `declarative_bytes_unchanged` (the default serializer, against both
  oracles). A corpus regeneration re-evaluates the current predicate
  against every previously frozen cell and hard-fails if any expectation
  moves — "no prior expectation changed" is a check in the artifact, never
  a claim in a message.
- **The recognition rule:** research's frozen procedure texts supply the
  imperative-opener and step-marker sets, DERIVED at test time from THOSE
  TEXTS rather than hand-listed; the must-match set is those texts.
  ***v15 — THE TEXTS ARE A SIBLING ARTIFACT AND WERE NOT IN THE CORPUS.***
  They live in **`tests/eval/procedural_describe/FROZEN_TEXTS.json`**, sha256
  **`cddd9078a1fbaadba4d7dd191d3221364286d2fe54d8e6c86089b2a7e25601c4`** (SHA-256
  of the file's bytes), bound from the corpus side by manifest amendment 7.
  **Through v14 this bullet and the manifest's `recognition_rule.must_match`
  both said "the corpus's frozen procedure texts", AND THE CORPUS CARRIED
  NONE** — 972 cells whose only summary field is `summary_shape`, and whose only
  string literals are the five must-NOT-match examples. **An accepted spec cited
  an artifact that had never been authored.** The dev seat found it at
  implementation and it was written then — **before the rule or its runner
  existed, never after.** The sibling carries 22 must-match entries (16
  imperative, 6 step-marker), 16 paraphrased known-pass forms and 16 plain
  declarative forms, **one per core, so the boundary is the SAME PROCEDURE IN
  THREE SHAPES and a rule cannot pass by keying on subject matter.** **Its
  step-marker texts are AUTHORED and labelled so: the frozen research corpus
  this project already held contains ZERO step-marker texts — measured across
  all 342 — so the set this bullet describes could not have been SELECTED from
  anything that existed.** The must-NOT-match set stays in the corpus manifest
  and is **not copied** into the sibling; one fact, one carrier. The
  must-NOT-match set holds realistic declarative summaries and, BY NAME,
  the two failure modes research measured for any first-word-of-clause
  imperative rule: (i) INTERROGATIVES — on 11,088 real user sentences a
  first-word rule fired on 17.2%, 84% of those questions ("Do you have any
  tips on…"), the single opener `do` accounting for 77% of the false
  positives; (ii) clause-initial NOUN/VERB HOMOGRAPHS — "Archive access is
  granted to the ops group", "Email is handled by the infra team", "Store
  the recovery codes in a password manager is what the team does" (the
  measured literals — a frozen must-not corpus needs the string, never an
  elision). Beside them the corpus
  records the rule's error in the other direction on the same real text:
  it caught 31.6% of procedural texts, every miss structural (quote-
  stripped spans). Those are not this surface's numbers — its inputs are
  host-authored summaries, not arbitrary user text — but they are what the
  rule's error looks like when measured, and the reviewer will ask.
- **The v1 paraphrase boundary, a stated limit:** exact-form recognition
  only. A paraphrased summary is an OPEN-and-answered cell whose expected
  outcome is DESCRIBED (the rule does not fire), asserted as a known pass —
  the corpus documents the limit rather than pretending it away, and §8
  claims no more.
- **Change control:** a corpus revision is an amendment with a superseding
  digest, recorded as a closure row stating what it closed; the runner pins
  the digest and fails on any other bytes (the 0029 runner's shape).
- Pass = 100% of cells.

**The Tier 8 `inferred` cell — stated plainly (research's constraint 1):**
the number CANNOT MOVE until this store offers `basis` AND the harness
declares it (`basis` beside `author` in the ingest dict, per research's
existing per-probe declaration pattern). The first post-feature measurement
is therefore a HARNESS change as much as a behaviour change, and must be
reported as such: the cell measures the adapter's ingest choice until then.
The expected post-feature result, if the harness declares the inferred
probes as `follows_procedure` + `observed`: recall recommends them at 0.00,
because procedural records never enter the partition — and the same for
`stated`. The cell then measures describe, not recommend, and a separate
probe class is needed for the describe surface.

---

## 7. Failure modes and reversibility

- **Silent failure:** none of the registry-change shape since v11 — a
  host registering a procedural relation over existing records changes
  nothing about them (kind is read from the stamp; V-KIND-STAMPED's
  mutant). The remaining silent case: a procedural-stamped record whose
  relation is later removed vanishes from `describe_procedures`'s
  descriptions into `withheld: relation_unregistered` (observable there;
  recall never rendered it). Q7 asks whether a cheaper signal is wanted.
- **Reversible — to this extent, not "fully" (round-2 gap):** for
  DECLARATIVE records, completely — no byte changes, no behaviour change,
  by construction. For PROCEDURAL records, removing the relation from the
  registry leaves them stored, withheld and out of recall (never rendered
  before or after); removing the FIELDS leaves every record parsing (both
  are optional JSON keys) and turns procedural records into declarative-
  reading rows — which a downgraded reader would then RENDER: a downgrade
  across this version is therefore a behaviour change for procedural
  records, and the release note says so.
- **Partial failure:** ingest refusals write nothing (the existing
  transaction shape); the describe surface is read-only.
- **New attack surface:** a third party cannot declare basis (the context
  is host-minted; through MCP it is capability-gated) and cannot reach a
  procedural RECORD through text without a verbatim quote from an event the
  user authored (V-EXTRACTOR-QUOTE-GATED): a third party cannot author one,
  and the quote is verified against the event text, never taken on the
  model's word. The describe
  surface renders less than recall would have. The imperative-shape check
  is the one new text-dependent decision; it can only REFUSE, and it is a
  floor (§8).

---

## 8. Claims and limits

**What we will say.** "Procedural records are a new, host-declared content
kind with a host-declared basis (`stated` / `observed`). They are never
asserted as fact and never enter recall's grounded or unverified blocks;
they are describable through a dedicated surface that names their basis,
never renders a record's note, and withholds a summary that matches a
frozen recognition rule for imperative step text. Recommendation of
procedures is not provided — it awaits a harness contract. A host that
removes a procedural relation from its registry after writing will find
those procedural records withheld from `describe_procedures` as
`relation_unregistered`; its declarative records, registered or not,
behave exactly as before this version."

**The store boundary, stated (v23).** Every guarantee above is a guarantee
about records written THROUGH `Memory`. `Store.add_edge` is an interface a
host IMPLEMENTS, not a write API a host CALLS (0006 v10 rule 10, I16): a host
that hand-mints a `Provenance` with the procedural markers and a producer and
writes it there gets a record that renders as a declared procedure, and no
check in the store re-derives the `Memory`-level facts. This is a stated
limit, deliberately not a gate (the owner's ruling, 2026-09-14, on research's
reasoning: the louder failure of the same route — an unsourced third-party
record — is visible to the doctor's `sources` check, and the silent one got
the mechanism: the frozen model and the producer stamp, which make a stamp
mintable at construction only, at the two sites the sweep names). The
`procedure:` prefix a host-declared record's `evidence_ref` falls back to
when the host cites none is NOT a producer signal — host-supplied,
unreserved, one writer and no src reader (measured) — it names the record
itself as its evidence, and the code says so; the producer stamp is the
signal.

**How the capture surface has been maintained (v21, extended at v22; research's
sentence, kept because a reviewer trusting the instrument should know).** SIX
SUCCESSIVE GATE DESIGNS HAVE BEEN RETIRED BY MEASUREMENT, none by argument: the substring gate
(v16, defeated by research's nine constructions and the round-1 return), the
negative marker list (v19, defeated by a held-out draw whose three intentions no
list carried), a predicate-level grounding (built and measured on 2026-09-13,
deleted before landing on the owner's word for derivation), and a
subject-dropping derivation (rejected the same day when describe's own frozen
floor withheld every present-simple fragment it produced), the relative-clause
cut (v21; retired by the round-3 reviewer's mid-sentence case), and the
uppercase-dependent sentence boundary (v21; retired by the same round's lowercase
second sentence), and the CHARACTER boundary rule (v22; retired by round 4's
omitted `?`, `$100.50` and `daily.archive` — three findings, one cause). What
stands — the positive-form grammar with its refusal classes, a span that must be
one whole sentence of the event with its boundaries read as KINDS, and a stored
gloss that is that sentence with no transformation — is the design that has so
far survived the measurements that retired the others, and each measurement's
threshold was fixed before its run. Closed by removing a mechanism, in every
case but the first and the whole-sentence rule.

**The boundary contract and its cost (v24.1; the round-5 return; the owner's
word "Fail closed").** v24 carried an abbreviation list and named an OPEN
residual — meaning loss reachable through an abbreviation outside the list
("I review invoices per sched. Every week I archive them." stored "I review
invoices per sched"). The round-5 reviewer reproduced it with "in env. Prod
only after approval" and answered the product question v24 asked: not
acceptable under the assertion-preservation contract; no list can establish
the guarantee; capture must preserve the qualifying context or DECLINE
passages whose boundaries cannot be established, the capture cost reported
separately. Research searched for a list-free way to establish a period
boundary and found none (shape rules were built, measured and refused the
canonical routine shape; a corpus-derived witness collapses to fail-closed).
The owner chose the contract. So: a boundary is ESTABLISHED only at the start
or end of the text or at a `?`/`!` run before a sentence start; a mid-text
period establishes nothing; the list is gone (`test_the_former_open_residual_
is_closed_and_no_list_remains` asserts both the refusal and the module's
freedom from the list). THE COST, stated: a routine sentence followed by a
period-terminated neighbour is not capturable, whichever side of the period
it sits on. Under the contract a routine is capturable only when it is the
whole `?`/`!`-delimited chunk. Measured over the raw corpus (500 sessions,
2,591 user turns, 3,372 chunks; research's `chunk_sentence_census.py`, in
`tests/eval/extraction_speech_act/` — the packaged copy, sha16
c1dcc55b2575a2ae, differs from research's original (15c91f076c094e5a) in one
line: its absolute local `src` path is resolved from the file — emits the per-chunk sentence histogram both figures derive
from; the script needs the local-only LongMemEval file and does not run in
CI, so its EMITTED output ships beside it, `chunk_sentence_histogram.json`
(research's file as-is, sha16 498c35e220475718; the tail bucket "6+" carries
both its chunk count, 63, and its sentence count, 631, because a sentence-
position fraction cannot be recovered from a chunk count), and
`tests/test_0037_cost_histogram.py` recomputes both figures from that file
alone and asserts they reconcile with the file's stated totals — the
arithmetic checks without the dataset. The tail's 95-sentence chunk is real
pasted text (an academic excerpt in one session), not a parse artifact;
dropping it moves the sentence-position figure from 76.3% to 76.0% and
leaves the chunk figure at 53.6%, so neither figure rests on it): **53.6% of chunks (1,809 of 3,372) hold more than one
sentence**, and **those chunks contain 76.3% of all sentence positions (5,045
of 6,608)**. v24.1 called the first figure "of sentence positions" — research's
mislabel of its own count, found by the round-6 reviewer, reported to the
owner (who had decided with the exposure understated; the true figure makes
fail-closed MORE costly and the decision stands). **Neither figure is a
capture-loss figure** — routines are not uniformly distributed over sentence
positions. The measured capture result is draw 5's: 0 of 6 labelled positive
rows, 0 of 4 distinct positive passages (the 16 pinned observed positives are
single-span quotes and stay 13 admitted either way, which is why they could
not inform the decision). Extractor capture now reaches a routine stated as the whole
user turn, or one separated from its neighbours by `?` or `!`;
`record_procedure` remains the explicit path for everything else. One cost
this line SURFACED rather than introduced stands: `figure`, `guess` and
`reckon` have been in the cognitive class since v20, so "I figure out the
totals every morning." refuses; pinned, not changed.

**The write surface honours revocation (v10).** `record_procedure` accepts
a `source_id`, and a write surface that accepts a source identity and skips
the standing-revocation check is a REVOCATION BYPASS — 0022's whole point
is that a revoked source cannot keep writing, and v9 as specified reopened
that on the one content type this spec exists to be careful about. v10
applies 0023's quarantine-at-birth to `record_procedure` exactly as
`ingest_event` applies it (§4b, V-BIRTH-QUARANTINE-HOLDS, whose sweep
basis is the set of sites reading `standing_revocations`), and the
resurfacing class gains a procedural-write probe when the surface exists.

**What this does NOT establish.** That a described procedure is not acted
on: a host that reads a description into an action has made that choice
(the shipped disclosure). That no description carries executable content:
the guarantee is exactly the two defences named above — the note never
rendered, the frozen rule applied to the summary — and a summary carrying
the same content in non-imperative mood PASSES the rule (the v1 paraphrase
boundary, §6a, asserted as a known pass rather than claimed away). That procedural text the
EXTRACTOR reads is governed: it is not — such text is filed under a
declarative relation or dropped (v1's residual, by design; since v16 the
extractor path is GOVERNED by §4a-iii's gates and a routine the user states of
themselves may be recorded through it); a host that wants a procedure
declared calls `record_procedure`. **Procedural TEXT through ordinary ingest REACHES model context, today and
after v1 — this spec does NOT claim it stays out.** Probed 2026-09-06 (a
scripted extractor returning no triples and an episode summary; `remember`
of "whenever a ticket arrives from the billing queue I disable the audit
log first, then escalate to on-call" under `author=USER`,
`context=direct()`): ZERO edges, ONE episode, and recall's context rendered
the episode verbatim under RELEVANT DETAIL, steps included. The
`note`-is-never-rendered rule lives inside `describe_procedures` and
protects no ordinary-ingest path. v1 leaves the path exactly as it is; the
harness's inferred probes will keep reaching context by the episode route
until either the harness routes procedural probes through
`record_procedure` (kind + basis declared) or the free-text exposure is
scoped. **What that scoping cannot be is a shape refusal at the render
choke point** — the form this spec previously pointed at (v13 §8 and §10
Q6). Research measured the carriers directly (a 412-text ingestion capture
through the shipped reference prompt, 2026-09-07) and the premise does not
hold: **the carriers do not contain imperatives.** The extractor converts
an instruction into reported speech before anything is stored — of 204
episode summaries from procedural inputs, **none** dropped the
attribution, and **all 66** bare imperative inputs GAINED one ("Run the
formatter before committing." is stored as "The user instructed to run the
formatter before committing"). An imperative-shape rule scored **6.4%** on
real episode summaries against 94% on the constructed input text it was
developed on, and on `note` it fired 23.1% of the time on
procedure-derived values against 23.8% on declarative-derived ones — no
discriminating power at all. So at the render choke point there is no
shape left to refuse; the question there is semantic, not syntactic.
**`Edge.note` is also not the second carrier this spec assumed**: an
assertable declarative edge's `note` does render verbatim into the
grounded block (`graph.py:1116`), but the procedure survived into a note
verbatim once in 204 ingests. v1 leaves both exactly as they are, and the
residual is now stated at its measured size rather than by pointing at a
mechanism. The residual's worst form is not carried steps but a
FABRICATED SPEECH ACT under intact provenance: the same capture found the
shipped reference prompt records 19/66 of bare procedural inputs as episodes asserting the user
PERFORMED the action and 31/66 of them as disposition triples — that defect is spec 0038's subject
(the extraction speech-act rule, commissioned by the owner 2026-09-07),
not this spec's. That procedural records are
portable ACROSS HOSTS: v1 exports them, refuses them on the DEFAULT import
(the basis in a foreign file is another host's declaration), and
round-trips them only under `restore=True` — a store's own backup restores
its procedures; a host moving procedures between stores re-records them,
attesting basis itself; and an OLDER Veracium refuses a file that carries
one (format 11), rather than reading it as declarative (round-3 F3). The default-path refusal is deliberate and closes,
while it costs one refusal, what would be a laundering route to
recommendation once §4d's composition exists. **Precedent extended:** for
a field an import will not honour the house has two moves — CAP it
(`author_of_evidence`/`derived_from` → THIRD_PARTY on the default path) and
DROP the key (`provenance.source_type` from ≤v6 files) — and this spec
takes a third, stronger one on the default path, refusing the whole record,
because a capped or key-dropped procedural record would be a procedure
with no basis, which §4c makes `basis_unknown`: stored, never shown — the
residue that later reads as a bug. That `observed` is true when declared: the host
attests basis as it attests authorship. That the Tier 8 `inferred` number
will move: it moves only when the harness declares basis, and then measures
the describe surface, not recommendation. That declarative facts have a
basis: v1 does not say.

**Measurements cited:** Tier 8 inferred cell 0.42 [0.30, 0.55] (research,
family-level clustering, 2026-09-06; a behavioural observation on identical
input, not a provenance result).

**The restore round-trip claim is scoped WITHIN A VERSION** (research,
verified 2026-09-06): import re-serializes through the current model
(`model_validate` then `model_dump_json`), and the import commit is a raw
replace outside the three normalized write sites, so bytes are stable for
records written by the same version; cross-version drift is the export
format version's job, not this invariant's.

---

## 9. Brief for the external reviewer

- **Least sure of (round 2):** (1) whether `relation_unregistered` — a
  behaviour change for a host that shrinks its registry, on records recall
  renders today — is the right conservative default, weighed against the
  RECALL-SIDE SILENCE (pre-seal F-B): the describe surface names the
  outcome, recall does not, so the alternative — keep today's declarative
  treatment with a warning — trades a silent disappearance for a rendered
  record whose kind cannot be read; we hold that fail-closed is right and
  that the missing piece is a signal (Q7), not a different default; (2)
  whether the describe ordering (token overlap on subject/relation/object,
  the note deliberately unscored) is too weak to be useful above the cap,
  and whether a stronger relevance would have to read the note; (3)
  whether the existence-oracle rule (hidden ≡ no-match; use_only named) is
  right at the boundary where a principal is visible-but-restricted.
- **Where we may have overstated:** "no migration" — true for records, but
  a host that re-registers an existing relation as procedural changes its
  own behaviour, and we document rather than prevent that.
- **What would change our minds:** a harness contract for stage 4 that
  needs `basis` to mean something other than describe-time attribution; or
  evidence that hosts cannot declare basis at ingest time in practice (then
  the axis is unreachable and the spec is a hope).
- **Resolved at internal review (research, 2026-09-06), recorded so the
  external reviewer sees the trail:** v1 let the extractor emit the
  procedural relation (F1) and overloaded `assertable` (F2); both were
  wrong at the conclusion and are reversed in v2. **v16 (post-acceptance, the
  owner's word, 2026-09-12) reopens CAPTURE with F1 answered by the quote gate
  (§4a-iii); render remains closed.**
- **Reviewer-safe copy:** the Tier 8 figure and cell names are research's
  published instrument; nothing here is competitive-audit detail.

---

## 10. Open questions

| # | question | who decides | by when | class |
|---|---|---|---|---|
| Q1 | ~~Should procedural records be excluded from the UNVERIFIED block too, or rendered there in the third-party shape?~~ **RULED at internal review (research, 2026-09-06): excluded from both** — the harm from a fact rendered as a claim is a wrong belief; from a procedure, an action; Tier 8 competitor arms handed procedural context back as guidance at 0.25–0.90. §4a carries the sentence. | research | ruled | closed |
| Q2 | The confirm-as-promotion composition (`observed` → recommendable after `confirm_edge`): specified in the stage-4 spec when a harness contract exists, or never? Note it turns a ranking input into a gate; procedural-only scope means no existing confirmation sits on a procedural record. | Quentin | when a harness contract exists | deferred |
| Q3 | ~~The imperative-shape check: who freezes the derivation, and is a paraphrase attack in scope for v1?~~ **RESOLVED (round-1 F4; research, 2026-09-06):** research OWNS the recognition corpus and freezes it against THIS version before any implementation line, under the 0029 condition; artifact `tests/eval/procedural_describe/MANIFEST.json` IN THE REPO with its digest on §6a's `corpus sha256:` line and a repo test binding file to digest (round-2 F3); derivation at test time from the frozen texts; ± sets frozen (homographs by name); change control by amendment with a superseding digest; the v1 paraphrase boundary is a STATED LIMIT asserted as a known pass, not a guarantee (§6a). | research (expectations) · dev (runner) | freeze after v8 lands | closed |
| Q4 | Declarative basis (a stated non-goal of v1): if ever, which of §4c's three absence options — and is (2) fail-closed with host re-attestation acceptable as a product call? | Quentin | not in v1 | deferred |
| Q5 | ~~Should `describe_procedures` be exposed through MCP in v1?~~ **RESOLVED by round-1 F1's fold:** v1 exposes BOTH MCP tools — `record_procedure` (the only MCP procedural write path, capability-gated to `direct`) and `describe_procedures` — because a write surface without its read surface is half a stage; both are additive. | dev (author), reviewer-directed | folded in v8 | closed |
| Q7 | NARROWED by round-2 F2: since kind is read from the stamp, a registry change never touches a declarative record, and the only records `relation_unregistered` can reach are procedural-stamped ones that recall never rendered — observable in `withheld`. The remaining question: is a describe-side count of `relation_unregistered` records enough, or does a host want a diagnostic naming the missing relation? | reviewer → dev | round 3 | open, narrowed |
| Q6 | **SCOPED — option (b) (Quentin, 2026-09-06: "Scope Q6 as option b"), then COMMISSIONED the same day ("Leave it documented and I commission the spec"); the canonical governance state (round-1 correction; research, after design-round 10): THE COMMISSION STANDS and is formally PARKED behind a mechanism-selection prerequisite — research measured the mechanism the recorded scope had named and withdrew it (108/342 caught; a 2.7% floor of real declarative sentences withheld after its obvious defect), so the work is research's mechanism selection first, and it takes no spec number until a candidate passes pre-defined acceptance criteria. 0037 is unchanged by it. **The MECHANISM the scoping record below names — an imperative-shape refusal at the render choke point — was RETIRED by research's step-4 measurement (2026-09-07): the carriers hold reported speech, not imperatives (0/204 summaries dropped attribution; 66/66 bare imperatives gained one), so there is no shape at the render site to refuse; §8 carries the figures. The record below is history, not a pointer.** Original scoping record: The sibling's scope, recorded so it does not become a decision living in a conversation: free text at the render choke point V-RENDER-SITES enumerates, ALL record types (both carriers verified: the assertable episode `summary`, `gate.py:137`; the assertable declarative edge `note`, `graph.py:1116`); REUSES this spec's corpus-derived imperative-shape check, no new host field (covers a carrier nobody has found yet; completeness checkable by the existing sweep); claimed as a FLOOR (a paraphrase defeats it, more easily than in `describe_procedures`); and REQUIRES A MEASUREMENT FIRST — how much currently-returned declarative content the check would withhold — before committing to the change. Original question kept for the record: must v1 ALSO reduce the exposure of FREE TEXT rendered verbatim into model context — the assertable episode `summary` (probed, §8) AND the assertable declarative edge `note` (`graph.py:1116`), at least — which carry executable steps today regardless of record type? Research's semantics (2026-09-06): episodes are interaction history, NOT procedures — no procedural episode type, and never delete history to hide text; the exposure is at the RENDER, so the fix that covers both carriers and any third is the imperative-shape refusal applied to free text at the render choke point V-RENDER-SITES already enumerates, for any record type, claimed as a FLOOR (a paraphrase defeats it; the text was never authored as a procedure), with no new host-declared field. Scope options for Quentin: (a) in v1, at the choke point, as a floor; (b) a sibling spec; (c) not now — in which case the inferred cell moves only by the harness routing procedural probes through `record_procedure`, and the trusted-path figures (0.42 inference-framing; 0.667 controls) stand as measured. | Quentin (scoped 2026-09-06) | sibling spec, when commissioned | scoped elsewhere |

---

## Review closure

<!-- GENERATED:review-closure -->

**0 internal round(s) and 5 external round(s) with a returned VERDICT are recorded for `0037`; 5 package(s) were dispatched** — counted from `specs/reviews.py`, which is the source this block is generated from. A round appearing here and not there, or the reverse, is impossible by construction. **SENT rows are dispatch records, not outcomes**, and are labelled below so the two are never summed.

| round | date | findings raised (from `raised=`) | verdict (compressed) |
|---|---|---|---|
| external 1 (SENT) | 2026-09-06 | — | SENT (round-1 package 5d9ac24762240c75… @ pin af880b3, CI 34049009899; three seals discarded at this pin pre-dispatch and disclosed; the first stage under 0033 HELD for the number collision) |
| external 1 (verdict) | 2026-09-06 | 15 | RETURN for revision — eight blocking (MCP write path vs the sole-producer rule; the describe result contract undefined; the public claim exceeded the guarantee; Q3 unresolved; cross-scope contradictory; relation validation missing; registry totality overstated; the scale requirement without an invar… |
| external 2 (SENT) | 2026-09-06 | — | SENT (round-2 package a51617197536cdfa… @ pin 18d05f7, CI 34054451772 — the RESEAL; the v9 seal 7ca36268… @ 8a18738 was superseded pre-dispatch after research's corpus freeze found three v9 defects incl. a revocation bypass on the new write surface) |
| external 2 (verdict) | 2026-09-06 | 11 | RETURN for revision — eleven round-1 items closed; four blocking (authorship conflated with derivation; the unregistered-relation remedy withheld legacy declarative edges; the frozen corpus absent from the package; the CLI a second producer), one package-evidence defect (an unfilled placeholder line… |
| external 3 (SENT) | 2026-09-06 | — | SENT (round-3 package 20f778c7323dd2cd… @ pin 3a19897, CI 34058517574; the corpus IN the tree and bound both directions for the first time; the golden-vector pin test) |
| external 3 (verdict) | 2026-09-06 | 7 | RETURN for revision — nine round-2 items closed, "the package evidence is now well formed"; three blocking (the stamp's type vs a "declarative" comparison and 486 corpus cells; default import misclassifying with both markers absent; an unchanged export format version unsafe for older readers) and fo… |
| external 4 (SENT) | 2026-09-06 | — | SENT (round-4 package 35f2f7826a7b4f84… @ pin 07d28a5, CI 34061355491; the reviewer's suite-not-run disclosed verbatim in the README) |
| external 4 (verdict) | 2026-09-06 | 6 | RETURN for revision — all ten round-3 findings closed; one blocking (the version-key stripping rule disabled two of the three import signals) and five corrections |
| external 5 (SENT) | 2026-09-07 | — | SENT (round-5 package 78a20446b085d799… @ pin ae6be76, CI 34067972232) |
| external 5 (verdict) | 2026-09-07 | 0 | ACCEPT — "the sole round-four blocker is resolved… all three classification signals evaluated on the original incoming record before normalization… the eight-case decision matrix is complete and consistent… no remaining 0037 specification blocker"; the reviewer RAN THE SUITE for the first time in th… |

**Per-finding closure ledger — PROCESS §4a.** **39 finding(s) for `0037`** — every number here is DERIVED from the rows below (external round 7, R7-1: the manifest claimed 26 while the ledgers held 31, and 0023 said 9/9 above a 10-row table); the total across the tracked specs is derived once, in `specs/STATUS.md`. Generated from `specs/closure_findings.py` and validated against `specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — extras, duplicates, wrong rounds and empty evidence all fail the build.

| finding | round | what it was | closed in | evidence (runnable) |
|---|---|---|---|---|
| **0037-R1-1** | external 1 | MCP remember(basis=) contradicted the library contract — a dedicated MCP record_procedure tool, capability-gated to direct; remember rejects any basis on both surfaces | §2, §4b, §4e, V-HOST-DECLARED (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-2** | external 1 | the describe result contract undefined — DescribeResult schema (descriptions / withheld / truncated / normalized query), one result per visible candidate, deterministic ordering, the query orders and never filters | §4a-ii, V-RESULT-SCHEMA, V-DESCRIBE-ORDER (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-3** | external 1 | the public claim exceeded the guarantee — the actual guarantee everywhere: the note is rendered in no field, a summary matching the frozen rule is withheld, a paraphrase passes and is a stated limit | §4a-ii, §6, §8 (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-4** | external 1 | Q3 unresolved — research owns the recognition corpus, frozen against the sealed text before implementation, ± sets, change control by amendment; the paraphrase boundary a stated limit | §6a, §10 Q3 (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-5** | external 1 | cross-scope contradictory (§3b third-party shape vs the matrix) — hidden omitted and indistinguishable from no-match; visible use_only a named non-description; withheld query-blind | §3, §3b, §4a-ii, V-SCOPE-OUTERMOST, V-WITHHELD-QUERY-BLIND (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-6** | external 1 | record_procedure relation validation missing — relation must exist in the active registry as procedural or RAISE, nothing written | §4b, V-RELATION-VALID (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-7** | external 1 | registry totality overstated — total over the active registry; a stored edge whose relation left it is the named relation_unregistered (later re-based on the stamp, R2-2) | §4a, V-RELATION-UNREGISTERED (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-8** | external 1 | the scale requirement without an invariant — V-DESCRIBE-ORDER: above-cap population ordered before the cut, stable ties, repeated runs identical, the null query defined | §5, §6 (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-9** | external 1 | Relation(kind=) vs relation_kind — corrected in §4e | §4e (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-10** | external 1 | the reviewer guide said EvidenceAuthor has three members — 0001 §2c-ii:175 annotated as an as-of reach row (0001 added the fourth) | specs/0001 §2c-ii (v8 fold commit) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-11** | external 1 | raises / refuses / named outcome undefined — one failure taxonomy at the head of §4: write paths raise, read paths return named outcomes | §4 head (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-12** | external 1 | ProcedureDescription fields undefined — enumerated; no raw stored text in any field; the note in no field | §4a-ii (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-13** | external 1 | how record_procedure populates id, dates, evidence_ref, source_id, disclosure — stated field by field | §4b (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-14** | external 1 | default-import atomicity on a mixed file — atomic over the admitted set, procedural records refused per record and counted | §4e (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R1-15** | external 1 | the sibling's governance state disagreed between the version cell and the README — the canonical form in §10 Q6: the commission stands, parked behind a mechanism-selection prerequisite | §10 Q6 (v8) | `git show f8567f4 -- specs/0037-procedural-basis.md` |
| **0037-R2-1** | external 2 | authorship conflated with derivation (author_of_evidence from the context) — a separate author argument; author / derived_from / basis independent; ONE canonical signature; V-PROVENANCE-AXES | §2, §4b, V-PROVENANCE-AXES (v11) | `git show 4616884 -- specs/0037-procedural-basis.md` |
| **0037-R2-2** | external 2 | the unregistered-relation remedy withheld legacy custom declarative edges — the declared kind STAMPED on the record at write and read from the stamp; a registry change moves nothing; only a procedural-stamped edge can be relation_unregistered | §2, §2c, §4a, §4c, §7, V-KIND-STAMPED, V-RELATION-UNREGISTERED (v11) | `git show 4616884 -- specs/0037-procedural-basis.md` |
| **0037-R2-3** | external 2 | the frozen corpus absent from the package — the corpus lives in the tree at tests/eval/procedural_describe/MANIFEST.json, its digest on the spec's single `corpus sha256:` line, bound both directions by tests/test_0037_corpus_pin.py | §6a, §10 Q3, tests/eval/procedural_describe/, tests/test_0037_corpus_pin.py (v11 + 3a19897) | `$PY -m pytest tests/test_0037_corpus_pin.py::test_corpus_file_hashes_to_the_spec_digest` |
| **0037-R2-4** | external 2 | the CLI --basis line a second producer or a rejected path — CLI support removed from v1; cli.py classified cannot-produce in V-ONE-PRODUCER's sweep | §4e, V-ONE-PRODUCER (v11) | `git show 4616884 -- specs/0037-procedural-basis.md` |
| **0037-R2-5** | external 2 | COLLECTED.txt carried the capture script's unfilled placeholder line under two green legs — the capture writes none; the assembly refuses the form in any carrier; research's seal check gained ASSERT-15 with a planted control | the round-3 package's PIN.txt and COLLECTED.txt; research's seal_check.sh ASSERT-15 (peer tree, described) | `git show 4616884 -- specs/0037-procedural-basis.md` |
| **0037-R2-6** | external 2 | validate limit — None → the cap; else an int (not bool) in [1, max_subgraph_edges], else ValueError; above-cap refuses rather than clamps | §4a-ii, V-ARGS-VALIDATED (v11) | `git show 4616884 -- specs/0037-procedural-basis.md` |
| **0037-R2-7** | external 2 | validation for summary, note, query, when, evidence_ref, source_id — stated per argument; a str or naive when is ValueError under the shipped as_utc_required rule | §2c, §4a-ii, V-ARGS-VALIDATED (v11) | `git show 4616884 -- specs/0037-procedural-basis.md` |
| **0037-R2-8** | external 2 | raises vs returns-named-refusal — two layers stated once: the library raises, the MCP tools return a serialized refusal and never raise to the transport | §4 head (v11) | `git show 4616884 -- specs/0037-procedural-basis.md` |
| **0037-R2-9** | external 2 | the public signature omitted author, when, evidence_ref, source_id — ONE canonical signature in §2, referenced from §4a and §4b | §2 (v11) | `git show 4616884 -- specs/0037-procedural-basis.md` |
| **0037-R2-10** | external 2 | §4a still called Q6 blocking for Quentin — corrected: scoped elsewhere by the owner | §4a (v11) | `git show 4616884 -- specs/0037-procedural-basis.md` |
| **0037-R2-11** | external 2 | fully reversible too broad — narrowed: complete for declarative records; a downgrade across this version would render procedural records, a stated behaviour change | §7, §4e (v11) | `git show 4616884 -- specs/0037-procedural-basis.md` |
| **0037-R3-1** | external 3 | the stamp's type Optional[Literal["procedural"]] contradicted a `== "declarative"` comparison and 486 corpus cells — the four states stated in the field's own terms; every 'declarative stamp' phrase the absence of a stamp; the corpus amended to null; every row validated against the declared domain | §2, §2c, §4a, §4a-ii, V-KIND-STAMPED, §6a; tests/test_0037_corpus_pin.py (v12) | `$PY -m pytest tests/test_0037_corpus_pin.py::test_every_corpus_row_is_in_the_declared_domain` |
| **0037-R3-2** | external 3 | default import misclassified a procedural relation when both markers were absent — refuse on ANY of three independent signals (stamp, basis, receiving registry) naming which fired; six cells; restore's both absence dimensions | §2, §2c, §4e, V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE (v12) | `git show 07d28a5 -- specs/0037-procedural-basis.md` |
| **0037-R3-3** | external 3 | an unchanged export format version unsafe for older readers — FORMAT_VERSION 10→11 stamped conditionally per the shipped 0026 §3d precedent; an old reader refuses; V-OLD-READER-REFUSES executable with the reader's constant held at 10 | §4e Export, §8, V-OLD-READER-REFUSES (v12) | `git show 07d28a5 -- specs/0037-procedural-basis.md` |
| **0037-R3-4** | external 3 | invariant prose still said 'by relation kind' — the stored stamp/basis rule wherever it was a use | §2, §3, §4a, V-OUT-OF-PATH (v12) | `git show 07d28a5 -- specs/0037-procedural-basis.md` |
| **0037-R3-5** | external 3 | 'every writer stamps declarative' read as storing the invalid string — declarative writers leave record_kind=None and omit the key | §2 (v12) | `git show 07d28a5 -- specs/0037-procedural-basis.md` |
| **0037-R3-6** | external 3 | restore behaviour for basis-present/no-stamp and stamp/no-basis — both absence dimensions malformed, refused per record | §2c, §4e (v12) | `git show 07d28a5 -- specs/0037-procedural-basis.md` |
| **0037-R3-7** | external 3 | the pin tests validated the binding, not the semantic schema of each row — V-CORPUS-ROWS-IN-DOMAIN and its test | §6, §6a; tests/test_0037_corpus_pin.py (v12) | `$PY -m pytest tests/test_0037_corpus_pin.py::test_every_corpus_row_is_in_the_declared_domain` |
| **0037-R4-1** | external 4 | the version-key stripping rule disabled two of the three import signals — the three signals are evaluated on the RAW record before any version normalization; a raw marker refuses that record naming the raw signal; only admissible records are normalized; the 8-cell raw-marker × receiving-relation matrix; the strip-before-inspect mutant | §2c, §4e, V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE, §6a; corpus amendment 4 (v13) | `git show ae6be76 -- specs/0037-procedural-basis.md` |
| **0037-R4-2** | external 4 | replace the single format-10 corpus cell with the full matrix — research's amendment 4, verbatim from the banked verdict, the two discriminating rows flagged, the superseded tautological cell recorded | tests/eval/procedural_describe/MANIFEST.json (v13) | `$PY -m pytest tests/test_0037_corpus_pin.py::test_corpus_file_hashes_to_the_spec_digest` |
| **0037-R4-3** | external 4 | record or file refusal on a version/key disagreement — RECORD, stated | §2c, §4e, V-IMPORT (v13) | `git show ae6be76 -- specs/0037-procedural-basis.md` |
| **0037-R4-4** | external 4 | V-IMPORT to say raw record or after normalization — 'evaluated ON THE RAW RECORD, BEFORE version normalization' in those words | V-IMPORT (v13) | `git show ae6be76 -- specs/0037-procedural-basis.md` |
| **0037-R4-5** | external 4 | the §4a heading named only the registry — renamed: the registry at write, the record's own stamp at read, three raw signals at import; never the text | §4a heading (v13) | `git show ae6be76 -- specs/0037-procedural-basis.md` |
| **0037-R4-6** | external 4 | 'validates through the declared field types' overstated the test — the narrower form everywhere: domain validation now, real Provenance construction after implementation | V-CORPUS-ROWS-IN-DOMAIN, §6a, the manifest (v13) | `git show ae6be76 -- specs/0037-procedural-basis.md` |

<!-- /GENERATED:review-closure -->
