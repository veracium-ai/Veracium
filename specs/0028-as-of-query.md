# Feature spec: as-of / point-in-time query — FEATURE VERSION v2 (valid-time only)

Spec-Status: draft

*Candidate authored by research (veracium-research), 2026-09-05, on the owner's
ruling splitting 0028: **v2 answers VALID-TIME only; the `observed_at` /
`known_as_of` transaction axis is v3** over 0029's carrier. v1 was returned at
external round 1 and paused for its substrate; that substrate — 0029, 0030,
0032 — is now accepted, and this is the resumption.*

| | |
|---|---|
| **Author / session** | research (veracium-research) |
| **Version** | **DRAFT REVISION v13 — THE EXTERNAL ROUND-6 FOLD** (verdict RETURN for amendment, 2026-09-07, banked `outbox/0028-round6-verdict-verbatim.md` — **body `bd2c56b42f753ce9`**, the reviewer's words; working file `badbb009ff4368ea`. Package `415d906c…` @ `eddcb233`, CI 34149633519). **Round 5's behavioural findings all RESOLVED and every test passed — the reviewer's own line: *"the round-5 behavioral findings are correctly resolved, and all tests pass. Two live contract carriers remain contradictory."* R5-1 resolved (both arms and the prior unfiltered implementation tested), R5-2 resolved (three distinct executable states), R5-3 PARTIALLY — and the remaining half is R6-1.** **R6-1 — THE FIX'S OWN SUMMARY WAS CORRECTED AND THE DEFINITION IT SUMMARISES WAS NOT.** §4b's normative outcome vocabulary still read *"`INDETERMINATE` … is never silent: every instance is disclosed with its cause"* — the one-rule form, after R5-3 had corrected the reviewer CHECKLIST that summarises exactly this. **We fixed the summary and left the definition.** §4b now carries the same TWO CLASSES the checklist does: an INDETERMINATE from a condition observable WITHIN the caller's view (branching, a cycle, an unclassifiable reason) carries and discloses its cause; **`SUCCESSOR_UNAVAILABLE` carries NO principal-facing cause by design**, because a distinguishable cause there IS the existence signal. Both failures are now named: collapsing *cannot tell* into *nothing*, and disclosing WHY across a scope boundary. **R6-2 — A CROSS-SPEC SURVIVING CARRIER, AND THE PACKAGE CARRIED BOTH HALVES OF THE CONTRADICTION.** §4b-o, §5 and §7 described the commit-time lock as SQLite's **bare** `database is locked` "surfacing unwrapped" — **true when written and FALSE AT THE SEAL**, because 0029 v11 landed at `9202d3d` INSIDE this package's own pin range and `_write_txn` now owns every commit it opens. The sealed tree's window test asserts the WRAPPED form while the sealed prose asserted the bare one. All three carriers updated to the wrapped refusal naming the COMMIT site with SQLite's message retained as the CAUSE; the history is kept and marked. **The pre-send miss was dev's and is recorded as theirs: folding 0029 v11 they swept 0029's text, `sqlite.py` and the TESTS — including 0028's window test — and never swept 0028's PROSE, reading "a fix to a shared contract lands in every implementation" as meaning CODE.** **RESEARCH'S SWEEP, run by NOUN over the whole file as both seats now require: 7 occurrences of `bare`/`unwrapped`, of which only THREE were the defect.** The other four are homonyms or marked history — *the bare v2 spec* (round 2's bare-file dispatch), *the fifteen bare `—` cells* (§6a's em-dashes), the version cell, and §7's own erratum. **A phrase sweep or a replace-all would have corrupted four correct sentences**; the reviewer named three and the noun sweep confirms three, with the fourth candidate — §2c-i's *"a bare interpreter error"* about a naive datetime's `TypeError` — correctly excluded as a different bare. **§9 RESTALED A THIRD TIME, AND IS NOW GATED RATHER THAN RE-READ.** v13's brief still said *"Round 6 carries what is executable today"* — the RETURNED round, in the section a reviewer opens first, for the third consecutive fold (v11 caught at the round-5 seal, v12 at the round-6 fold, v13 here). **Three misses by two seats re-reading is the case for a check, not for more care:** dev's adopt gate now refuses `Round N carries` for the returned N and requires the next round named, so this can no longer reach a package. Round 7's brief also gains a **THIRD SEAM** on dev's suggestion, and it is the round's own lesson turned outward: **both R6 findings were claims no check could see** — R6-1's summary corrected while its definition was not, R6-2's sealed test asserting the wrapped form while the sealed prose asserted the bare one. **No gate in this repository compares prose to prose or prose to a test**, so the brief now asks the reviewer to diff §4b against the checklist and §4b-o/§5/§7 against the window test's assertions, and says plainly that we have missed this shape twice running with the executable evidence correct both times. **REGISTER MARKERS (respin, pre-adoption):** five paragraphs that QUOTE a phrase being registered as withdrawn now carry the literal word **WITHDRAWN**, so `lint_withdrawn.py` can tell a MENTION from a USE — its marker rule exempts the paragraph the word appears in. **The sharpest of the five is this fold's OWN R6-1 note:** the edit that retires a sentence must quote it, so the register would flag the record of the retirement. **The marker is what lets the register and the history coexist, and it belongs in the SAME EDIT as the retirement, every time** — dev's observation, and now this line's rule. **CORRECTIONS: 1** §9 carried a malformed duplicated span, the round-5 "no count" replacement having merged with its neighbour's tail (*"…NO CARRIER STATES ONE** store states on the shipped store"*) — the scripted-edit span class, repaired; **2** the model's module docstring still calls itself the design *"v11 specifies"* though its queried-edge behaviour is v12's amendment — dev's file, dev's fix, riding with the adoption. *Prior:* **DRAFT REVISION v12 — THE EXTERNAL ROUND-5 FOLD** (verdict RETURN for amendment, 2026-09-07, banked `outbox/0028-round5-verdict-verbatim.md` — **body `233046c641f396ae`**, the reviewer's words; working file `cc9d668542990583`. Package `a0da2aa2…` @ `b4a680c7` (v11), CI 34141038484). **All executable checks passed and the reviewer said so: *"The archive and pinning protocol are sound. The return is for the remaining accessor-contract and acceptance-text problems, not for a test regression."*** **R5-1 — THE EXISTENCE SIGNAL ONE LEVEL UP, AT THE INPUT, AND IT IS THE SAME DEFECT R4-1 CLOSED.** v11 filtered the successor ROWS through `ScopeView` but took **the queried edge itself from the unfiltered collection** to read its `invalidation_reason` — so the public accessor answered `HEAD` for a nonexistent id and `SUCCESSOR_UNAVAILABLE` for a hidden corrected one: two distinguishable answers about an edge the caller may not see. **V-NO-EXISTENCE-SIGNAL did not catch it because it tested a VISIBLE prior with a hidden successor and never a HIDDEN QUERIED EDGE — the test's coverage was the shape of the finding it was written for, which is how a fix's own test inherits the fix's blind spot.** The remedy is one clause, not a mechanism: **the queried edge's assertion is readable only when that edge is visible in the caller's view**, so an invisible queried edge asserts nothing *to this caller* exactly as a nonexistent one does and the two become the same code path. Successors are still searched among visible rows, so a visible `S` naming a hidden `M` still yields `SUPERSEDED` when `M` is queried — disclosing nothing, since `S` and its `supersedes` field were already visible. **`edges_superseding` IS NOT AN EXISTENCE ORACLE**, and the spec now says so. **R5-2 — v11's malformed-reference rule was written about the WRONG DIRECTION.** It said a `supersedes` value naming nothing yields `SUCCESSOR_UNAVAILABLE`; but the accessor searches FORWARD for rows whose `supersedes == edge_id`, so a BACKWARD dangling value on the queried edge is never read. **Two distinct states had been collapsed into one sentence** — now named and specified apart: **successor row deleted (FORWARD)**, a visible edge asserting supersession with no successor row, ⇒ `SUCCESSOR_UNAVAILABLE`; and **dangling BACKWARD pointer**, a visible `S` whose own `supersedes` names nothing, which does NOT affect `S`'s disposition and which yields `SUPERSEDED` when the named nonexistent id is queried. **RENAMED: `V-UNAVAILABLE-NEVER-HEAD` → `V-NEVER-HEAD`, and RE-PHRASED OVER THE STATES it must hold in.** v11 stated it over RESULTS while its own mutant list already assumed STATES — the mutants were right and the statement was weaker than them, which is why a dry run disagreed with both seats' predictions: phrased over results, a collapse-to-`HEAD` implementation produces no `SUCCESSOR_UNAVAILABLE` at all and the invariant passes VACUOUSLY. **The old name said `UNAVAILABLE` — a RESULT — and a name narrower than its check pulls the check down to meet it**, so it is renamed rather than annotated. Mentions of the old identifier in THIS cell's earlier entries are left standing: they record what those revisions said, and rewriting them would make the lineage false. **R5-3** the reviewer checklist demanded *"every `INDETERMINATE` carries a cause and is disclosed"* — unsatisfiable alongside §3, §4b-i, §5.1 and V-NO-EXISTENCE-SIGNAL, because a distinguishable cause there IS the existence signal; amended to **two classes**: causes for indeterminates arising from conditions observable WITHIN the view, none for `SUCCESSOR_UNAVAILABLE`. **CORRECTIONS, RESEARCH'S OWN NAMED:** §9 claimed the model covers **NINE** states; `EXPECTED` holds and executes **EIGHT**, and the program prints "8 states" on every run. **Research published dev's six-plus-three arithmetic without deriving it from the artifact that was printing the true number** — the leg-figure lesson of this same morning, committed again in a carrier this seat owns; the count is now DERIVED. And §6a **stated NINETEEN/SIX/THIRTEEN in prose immediately above the paragraph saying no count is stated here deliberately** — two accounting rules in one section. **One rule kept: the CHECKED/OWED markers carry the accounting and no number is written in prose**, because a prose count is what went stale three times already (v2's "ten" over eleven; R2-5's correction to thirteen; v4's "ten" two paragraphs below the table it miscounted). Dev's three carrier corrections — the model header's `== "corrected"` predicate the registry replaced, and two "six states" headers — land with the model's R5-1/R5-2 fixtures in dev's commit. *Prior:* **DRAFT REVISION v11 — THE EXTERNAL ROUND-4 FOLD** (verdict RETURN for amendment, 2026-09-07, banked `outbox/0028-round4-verdict-verbatim.md` — **body `343ce4ece1910312`**, the reviewer's words, identical across custody; working file `8a6e265b51a95a2c`. Package `e1b96872…` @ `87280dad` (v10), CI 34131290529). All verification passed: checksums, the pin, the generator standalone (**correction 5 CLOSED — "now runs without manually setting PYTHONPATH"**), the evidence suite 19 passed, the window cases with the SQL column, offline 2,761/33 reconciling to the sealed 2,785/9. **R4-1 — v9's TYPED RESULT WAS ITSELF THE DEFECT, AND IT WAS OURS.** `omitted > 0` with `causes == {"cross_user"}` is an EXISTENCE SIGNAL across the boundary §3b says must be indistinguishable, unconstructible from a one-user scan, and `frozenset[str]` is not a closed vocabulary. v11 removes the signal **at the VIEW, not in the RESULT**: a successor outside the principal's `ScopeView` is not in the view, so it yields no count and no cause. Closed three-value `SuccessorDisposition` (`HEAD` / `SUPERSEDED` / `SUCCESSOR_UNAVAILABLE`), a two-field result, causes demoted to **operator-only** on 0031 §4d's shipped precedent. Safe because `invalidation_reason` is on the **edge's own row** (`schema.py:503`) — the principal already holds it. **It does NOT collapse into `HEAD`: that would trade a leak for a lie.** New **V-NO-EXISTENCE-SIGNAL** (whole-object equality, so a later field fails rather than passes) and **V-UNAVAILABLE-NEVER-HEAD**. ***And the design as first sent was WRONG in the same class it fixed:*** it defined "asserts supersession" as `invalidation_reason == "corrected"` — **a hand-written set beside a registry**. `superseded` and `absorbed_duplicate` also name a successor (the latter by `AS_OF_DISPOSITION`'s own note, *"0028 resolves to the absorber"*), so an edge retired `superseded` with a cross-scope successor fell through to `HEAD` **while the principal could read `invalidation_reason == "superseded"` on the row in front of them** — not a leak but a lie the principal can catch. It survived a reading because the `corrected` case still looked right. v11 specifies **`NAMES_A_SUCCESSOR`, a third registry total over `DISPOSITIONED_REASONS`** under `AS_OF_DISPOSITION`'s build-time gate (**V-SUCCESSOR-REGISTRY-TOTAL**). **R4-2** §4a's "no step consults wall-clock now **except** the current-truth pointer" named one step that does — the two-clock design, surviving across a LINE BREAK, which is why both round-3 sweeps missed it. **R4-3** "refused for the window's duration" was a **THIRD** wording of the disproved claim (§4b-o and V-ONE-SNAPSHOT); the two prior sweeps keyed on the other two phrasings. **A hand-list of phrases cannot be total over the phrasings a document can hold — v11's sweeps are over the NOUN, every hit read.** *(Research's own first sweep for R4-2 used a `.{60}` context window and silently dropped the match at a line start: the sweep had the defect it was hunting.)* **R4-4** §2c said Q5 OPEN while §10 said CLOSED — now three consistent sentences (library only in v2; shipped MCP unchanged; the serialization rule prospective), and a future change must edit both sites. **R4-5** the walk terminated on "`edges_superseding` returns empty" and §5.1's zero row on `[]`, both consuming the withdrawn list return; termination is now `disposition is HEAD`, HEAD-only, with `SUCCESSOR_UNAVAILABLE` terminating as `INDETERMINATE`. **A survivor the verdict did not name:** §4b's verdict table still promised `INDETERMINATE` **"with one of the enumerated causes — never a bare indeterminate"**, which R4-1 makes false at the successor surface; causes are enumerated only where they arise WITHIN the view. **MINOR:** the orphaned `moot.` removed. **The model is dev's and has LANDED** (`specs/evidence/0028/check_successor_lookup.py`, `tests/test_0028_successor_lookup.py`, main `00832e4`, suite 2793/8) over **nine** states — the six requested plus `hidden_superseded`, `hidden_absorbed`, and `hidden_unretired`, the last being the contrast that **looks like the same case and is not**: an un-retired prior with a hidden successor is correctly `HEAD`, because its own row asserts nothing. *Prior:* **DRAFT REVISION v10 — THE SUPPLEMENTAL-VERDICT FOLD.** The round-3 reviewer **independently RE-RAN all four transcript cases and they matched** (supplemental verdict banked `outbox/0028-round3-supplemental-verdict-verbatim.md`, sha16 `8010f409c996839b`), resolving **correction 7 only** — the four blocking findings stay open until v9's amendments are packaged. **§5 now takes the reviewer's clearer STRUCTURE and keeps the two facts their sentence drops:** the error's actual form (SQLite's bare `database is locked` from the COMMIT) and **that the write is rolled back and must be retried**. Their wording said *"raises the store's locked-write error"* — **the store does not raise that at commit time**: `_write_txn` wraps only `BEGIN IMMEDIATE`, so adopting the sentence verbatim would have put a claim in this spec that the product does not provide, with a reviewer's authority behind it. **A reviewer's wording is a claim about the code too, and gets the same check against the tree as our own.** The parenthetical naming the unwrapped commit-time lock is true today and reads as history after the recorded product defect is fixed — the spec is not coupled to an unscheduled product change. *Prior:* **DRAFT REVISION v9 — THE EXTERNAL ROUND-3 FOLD** (verdict RETURN for amendment, 2026-09-07, banked `outbox/0028-round3-verdict-verbatim.md` sha16 `f0cbf1e6b06c9c0f`; package `c9f83b23…` @ `f9379abb`, CI 34088697413). Round 2's five findings called substantively addressed; the generated table **7 rows, registry order, totality passed**; the two-protocol disclosure **resolved the `collected_header.json` concern**. **R3-1 — THE OLD TWO-CLOCK ALGORITHM SURVIVED IN §4a, THE SECTION THAT STATES THE ALGORITHM.** v6 removed it from V-ONE-CLOCK and v7 from §4c's bullet; **§4a still said the captured `now` is used by `valid_now` inside `assertable`, and that `classify_as_of` "has no implementation today"** — contradicting this spec's own Spec-Requires section, which records it shipping at `ccaa9cc`. §4c carried a SECOND survivor 34 lines below the corrected bullet, with research's own erratum about the first fix between them. **An implementer following either would have rebuilt the exact race the fold removed.** v9 re-derived every site that describes the algorithm rather than patching two more. **R3-2** `edges_superseding -> list[Edge]` could not carry the omission counts and causes its own contract promised — an empty list was identical for a head, a dangling reference, a cross-scope omission and a malformed one, so §4b's four-way distinction was unreachable through the interface meant to feed it; now a typed **`SuccessorLookup`** with **V-OMISSION-NOT-HEAD** planting each case. **R3-3** `facts_valid_at` promised recall's `ScopeView` while carrying neither `principal` nor `policy`; both added keyword-only, with **V-SCOPE-DIFFERENTIAL** — two principals, one store, one record. **R3-4** Q5 **CLOSED: MCP is UNCHANGED in v2**, on 0031 §4d's argument applied to a time axis (a model that can ask *what did you believe at T* can reach by history what the present gate denies it) — consistent with 0038's same-day decision to strip its counter from the MCP result. **CORRECTIONS: 5** the generator's standalone block inserted a hardcoded dev-machine path — it now walks up to find `src/veracium`, **verified by IMPORT ORIGIN from a copy of the tree at a scratch location**: v9's generator imports `veracium` from the copy's own `src/`, where the HEAD generator imports it from `/home/ubuntu/Dev/veracium/src/`. **Exit code does not discriminate on a machine where the hardcoded path resolves; the origin does.** *Research's first two proofs both passed for the wrong reason — a venv with `veracium` installed never ran the derivation, and a pydantic-only scratch tree still let the old absolute path resolve. The second was announced as the corrected test. Dev's import-origin control is what separates them (2026-09-07);* **6** the stale numeral is **REMOVED, not corrected to eight**, as the reviewer endorsed from the package's own errors ledger — a count about the document's own contents goes stale on the next edit; **7** §5's concurrency rows are written **from a two-connection transcript**, and the run disproved v8 in the harder direction: *"refused for the whole resolution"* names an outcome that **does not occur** — the writer waits and succeeds, or fails with a bare `database is locked` and **LOSES THE WRITE**. That disproved claim was in THREE sites. **§9 states what this spec cannot yet evidence**: the resolution is unwritten, so its absence proof is owed at implementation and is not offered here. **Still NOT packageable: ONE reader.** *Prior:* **DRAFT REVISION v8** — **THE SECOND-READER FOLD** (dev, PROCESS §3a, 2026-09-07, on Quentin's ledger word line 782: *"I approve your recommendation on all three and order you to implement all 3"*). v5's three blocking rewrites had ONE reader, their author; dev read them and **two ran into the code at places neither seat had checked. BOTH ARE THE SAME CLASS AS THE THREE v5 FIXED — a clause asserting an outcome the code does not provide — which makes five across this spec and two more in 0038: the pattern is research's, and it is that a spec describes the behaviour wanted without checking what supplies it.** **F1** V-ONE-CLOCK said the injected clock's value is "threaded to `valid_now`" — but `Edge.valid_now` is a `@property` with NO PARAMETER (`schema.py:568`) reading `utcnow()` (`:25`), the PROCESS WALL CLOCK, unreachable from `SqliteStore(clock=)`. Nothing can be threaded to it and a recording clock counts zero calls from it, so **the check would have PASSED while the two-read sleeper race it forbids was happening** — a check that cannot see the read it forbids, written into the row that was itself the fix for an unimplementable check. v6: the as-of branch never consults `valid_now`/`assertable`; its predicate is the interval test with the threaded `now`, and the recall path's `assertable` drop is replaced on that branch by `assertable_as_of` (`asof/classify.py:161`) — 0032 untouched. **F2** §4b-o required an "outer window" and **named nothing that could open one**: `_journal_scope` and `_write_txn` are private, `epoch_txn` returns an int. v6 specifies **`SqliteStore.read_window(user_id)`**, `current_state`'s open-or-join shape extracted (`sqlite.py:312-330`), with §5 gaining the regime consequence — **stated then as "a concurrent writer is refused for the whole resolution", which round 3 corrected and a two-connection run disproved: the writer waits and succeeds, or fails and LOSES THE WRITE (v9 §5).** **MINORS:** one read + in-memory walk (§5.1 and §4b-i had disagreed, the §5.1-vs-Q3 shape again); V-CROSS now names the generator's `--check` as its evidence — **run 2026-09-07: `V-CROSS OK: 7 rows`, so F8's "inherited, not verified" row order is now VERIFIED and was already right**; the generator's loose table pattern documented as FAILING CLOSED. **SECOND-READ FOLD, same day:** dev's second read found the two carriers the first fold did not reach — **§4c still read "BEFORE the `assertable` drop"**, so an implementer following the behaviour section would have built exactly what V-ONE-CLOCK's second mutant forbids (a fix that leaves a contradicting instruction elsewhere in the same document has NOT landed); and `read_window`, a NEW PUBLIC STORE API, had no §2 field-contract row — §2 exists to enumerate precisely that, with its contract, its other consumers (`current_state` becomes a joiner) and whether it preserves them (opening no window is today's behaviour). Both folded. **THIRD-READ FOLD (dev, by the two questions, same day):** §5.1's complexity row stated TWO cost models at once — it opened with the per-hop scan form and closed with m1's one-read form, the correction appended beside the text it replaced rather than replacing it. Corrected to one model; **and re-running the same question found §10 Q3 still quoting the superseded bound**, so the §5.1/Q3 pair disagreed for a SECOND time with the error on the opposite side — the pair is one carrier and every edit to either must be checked against the other. **v8 — THE LINEAGE FOLD**, on dev's packaging finding: the arc's round numbering did not resolve. **v3–v7 labelled the SECOND round's findings `R1-*`**, which reads as round 1 — round 1 is the 2026-08-31 v1 review (seven blocking, then the owner's pause), and the 2026-09-06 v2 review is round 2 (five blocking). Twelve labels corrected; **the rename was NOT mechanical and a pattern substitution would have corrupted the document — `R1-4` is OVERLOADED, most of its occurrences being 0011's R1-4** (the unconformable-shape rule cited as the authority for the refuse decision and the one-outcome-per-surface rewrite), and four "external round 1" phrases introduce round 2's work while three others correctly name the real round 1. The numbering convention is now stated and **the Phase-0 failure is recorded in the reviews row: neither verdict was banked verbatim, and v3–v7 cite round 2 from this seat's own restatement.** That sentence bounds what every `R2-*` label in this document is worth, which is why it belongs here and not only in a package README. **Still NOT packageable: the new text has ONE reader.** *Prior:* **DRAFT REVISION v5** (of the feature-version-v2 spec; the two axes are different and v4's header confused them — the title says which FEATURE version, this cell says which DRAFT revision) — **THE INTERNAL-REVIEW FOLD (dev, PROCESS §3a, 2026-09-06, on Quentin's word "get dev to review v4", ledger line 780).** v4 had had exactly ONE reader, its author; dev returned EIGHT findings, all verified against shipped code by research before folding. **THREE BLOCKING, and all three are the same class — a clause asserting an outcome the code does not produce:** **F1** §5.1 claimed "one indexed read per hop… the accessor performs no scan" while `supersedes` is a field inside the edge JSON (`schema.py:504`) with NO column and NO index in `store/sqlite.py` (its only `supersedes` hits are `supersedes_episode`) — and §10 Q3 called the same thing "the scan-backed accessor", so the spec CONTRADICTED ITSELF; v5 states the scan-backed truth and its bound, and refuses to spec an index because that is a column, a schema version and a migration in a spec whose §7 says no stored byte differs. **F2** §4b-o required ONE SNAPSHOT with no invariant and no mechanism, though the store SHIPS one: `SqliteStore.current_state` (`sqlite.py:300-312`) opens an explicit BEGIN and **joins an already-open transaction rather than nesting** — which is exactly why the resolution must open an OUTER window every read joins; per-hop `current_state` calls without one get a snapshot PER CALL while looking correct at every call site. New **V-ONE-SNAPSHOT** asserts it in both journal modes. **F3** V-ONE-CLOCK was **unimplementable as written** — it said count `utcnow()` calls, and there is no `utcnow()` on the as-of path at all (`asof/classify.py`, `asof/adapter.py`, `store/current_state.py`: zero clock reads; `classify_as_of` takes `now` as a PARAMETER). **Research's own least-sure item resolves POSITIVELY:** the injected clock EXISTS (`SqliteStore(…, clock=None)`, `sqlite.py:91,96`, `_now()` `:1707`), so §6a's check is real and now counts invocations of the injected callable. **FIVE MORE:** **F4** the prose said "Ten invariants" two paragraphs below a table of thirteen — the miscount round 1 already corrected once — so v5 states NO count anywhere and the reviewer checklist counts the rows; **F5** the withdrawn clamp survived as a USE twice (§2c "With that clamp, the property holds"; V-ONE-CLOCK's row); **F6** §2c declared the refusal "RETURNED-or-RAISED" two sentences after invoking 0011 R1-4 against that exact shape — v5 gives ONE outcome per SURFACE (library RAISES, a tool layer SERIALIZES `{"ok": false, "refusal": "future_as_of", …}`), with the MCP tool-surface question named as **Q5 OPEN** rather than guessed; **F7** the section whose first sentence is "the untrusted input is T itself" never validated T — new **§2c-i** normalizes through `as_utc_required` BEFORE comparing to `now` (a naive T against an aware `now` is a runtime `TypeError`, neither named outcome), with `T == now` PERMITTED and new **V-NORM-FIRST** asserting the ORDER; **F8** "totality asserted at generation" named a generator **that does not exist** — `specs/evidence/` has 0001/0011/0019/0020/0022 and no 0028 — so the caption "generated" was doing the work of a generator, this seat's own derived-basis rule turned on itself; the generator is now required at `specs/evidence/0028/` for acceptance and the row order is marked INHERITED, NOT VERIFIED until it lands. **Still NOT packageable:** F1/F2/F3 changed normative text that no second seat has read, and F8's generator is not written. *Prior:* **v4** — the ROUND-1 FOLD COMPLETE. **R2-3 closed on the owner's ruling, verbatim: "refuse"** (2026-09-06). `T > now` is REFUSED with the typed `FutureAsOfRefused` carrying the requested `T` and the `now` it was compared against; the clamp alternative is WITHDRAWN, not deferred. v2 had declared clamp OR refuse, both conforming — 0011 R1-4's unconformable shape, which research caught in another seat's spec hours before shipping it in this one. Refusal is chosen because a clamp SILENTLY ANSWERS A DIFFERENT QUESTION and needs a whole envelope to disclose it (`effective_as_of`, a `clamped` flag, empty-result behaviour, cache keys, both surfaces) — and round 1 named the hole in the cheap version: a clamp "recorded in each result" discloses NOTHING when there are no results. **ONE CLOCK READ still required** — refusal relocates that seam rather than removing it. **§6a now accounts for ALL THIRTEEN checks** (v3 covered eleven): V-ONE-CLOCK needs an INJECTED clock, since a wall clock cannot make the two-read race deterministic and the read-twice mutant must FAIL; V-BOUNDARY asserts both interval ends as data INCLUDING the null upper bound, the case v2's expression got wrong and a suite over closed intervals only would never reach. **No open findings from round 1 remain; this version is packageable.** *Prior:* **v3** — the EXTERNAL ROUND-1 FOLD, **INCOMPLETE AND SAID SO**. Round 1 returned RETURN FOR REVISION (five blocking, plus corrections). Folded here: **R2-1** §5.1 was CITED FOUR TIMES AND DID NOT EXIST — the accessor contract is now written (direct successors only; scope before the historical filter; inactive and future-valid INCLUDED because the accessor answers *what points at this*, not *what is assertable*; cross-user and dangling references omitted AND COUNTED, reaching §4b as a named INDETERMINATE). **R2-2** the verdict column used `GROUNDED`, a name shipping in NEITHER vocabulary — the table is now GENERATED from `AS_OF_DISPOSITION` in registry order with its totality asserted at generation, and V-CROSS compares it to the enum as DATA. **R2-4** three of §4b-iii's four absorbed-duplicate rows were unreachable (canonical absorption is empty-interval by construction, verified in `graph.py`) — one row marked reachable, three labelled DEFENSIVE corrupted-state, with the §6a consequence that they can only be built by writing the row directly. **R2-5** the inventory said ten checks where §6 has thirteen. Plus: the interval expression was undefined for an open interval; the determinism claim named `(store state, T)` when `now`, principal scope and policy version are all inputs; §4b-o added — ONE SNAPSHOT, since V-ONE-CLOCK is necessary and not sufficient (the walk can otherwise assemble a chain from states that never coexisted); the stale 0030 substrate status marked superseded rather than rewritten. **STILL OPEN, and the reason this is not a package: R2-3 — future-time behaviour.** The spec declares that a future `T` may EITHER clamp OR refuse, both conforming: 0011 R1-4's unconformable shape, which research had caught in another seat's spec hours before shipping it here. It is a product-visible API contract and is with the owner (research recommends REFUSE: it never silently answers a different question, and a clamp needs a response envelope to disclose something a refusal states in one line). §6a's constructibility table also still accounts for eleven of the thirteen checks. **No round-2 package until both close** — sealing with a known blocking finding is the batch-rule violation this programme refuses elsewhere. *Prior:* **v2** — core section (§4b and its supports) internally reviewed by dev 2026-09-05: one BLOCKING finding, two required changes, three confirmations, then a re-read with two residuals; all folded and verified against shipped code |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | dev · research |
| **External review** | REQUIRED — touches `graph` / recall. **ROUNDS COUNT FROM THE ARC'S FIRST DISPATCH; the owner's pause did not restart them.** **Round 1** — 2026-08-31, v1, package sha256 `481db5ab650891f681648eaecf81cf815e8e01a69f2d334b3d98da1689f5b82c`: RETURN, seven blocking; the owner then ruled HOLD FOR THE BIGGER SHAPE and the arc paused while 0029/0030/0032 were specced. **Round 2** — 2026-09-06, the bare v2 spec sent as a file, sha256 `21ffcf001d8e63717c26da7885465e3d1d87745c5f419fa835c9995d8268ba40`: RETURN, five blocking, cited throughout as `R2-1`…`R2-5`. **PHASE-0 FAILURE, RECORDED HERE BECAUSE IT BOUNDS WHAT THOSE LABELS ARE WORTH: round 2's verdict text was not banked verbatim by either seat, and the folds v3–v7 cite it from the folder's own restatement.** Round 1's verdict is likewise unbanked and survives only as a ledger entry with quoted fragments. Neither can be placed in a package's `prior-rounds/` as the reviewer's words, and no reconstruction from this document may be substituted for them. *(v8 corrected the labels: v3–v7 called round 2's findings `R1-*`, which read as round 1 — a label the author knew to be false. The rename was NOT mechanical: `R1-4` is overloaded, most occurrences being 0011's R1-4, the unconformable-shape rule cited as authority for the refuse decision; those are untouched, and round 1 of 2026-08-31 keeps its name.)* |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0030** — time-relative trust classification: `assertable_as_of` and the
  per-reason verdict at T. **This spec resolves what 0030 classifies.**
  ✅ **0030 IS SHIPPED CODE as of 2026-09-06** (`ccaa9cc` on main, unreleased —
  the next cut carries schema 12→13). This was a PRECONDITION of v2 and it is
  met. Verified against the tree, not assumed:
  `classify_as_of(envelope, snapshot_raw, current_state, T, now, view=None)`
  and `assertable_as_of` at `src/veracium/asof/classify.py`; and
  **`AS_OF_DISPOSITION` as DATA** at `schema.py:471` — a dict over every
  `DISPOSITIONED_REASONS` key, with an import-time gate raising `ImportError`
  if the two key sets ever disagree. Both v2 requirements are therefore
  satisfied in the form v2 asked for: the mapping is an artifact §6's V-CROSS
  can compare against, not a paragraph; and the classifier takes `now` as a
  **parameter**, which is what V-ONE-CLOCK needs to hold.

  **v2's §4b table has now been cross-checked against the shipped mapping by
  hand** (the check V-CROSS will automate): all seven registered reasons agree
  — `superseded`/`lapsed`/`decayed`/`absorbed_duplicate` → GROUNDABLE,
  `corrected`/`disputed` → FENCED_AS_OF, `revoked_source` → EXCLUDED — and §4b is
  total over the registry plus the `None` case.

---

## 1. Problem and motivation

A memory that retains history can be asked *what did we hold to be true at T?*
Today it cannot answer: `Edge.assertable` requires `active`, so every
invalidated edge is unassertable regardless of T, and history is retained but
not groundable. That was v1's round-1 finding and the reason for the pause.

0030 closed the classification half **in design** — it specifies what an edge
*is* at T. *(An earlier cut of this sentence said "it can now say", which is
true of the spec and FALSE of the code at the time of writing: 0030 was then
accepted design and unbuilt. **Superseded history — 0030 SHIPPED 2026-09-06
(`ccaa9cc`); `classify_as_of`, `assertable_as_of` and `AS_OF_DISPOSITION` are
in `src/`.** The paragraph is retained because the lesson it records still
holds; its status claim does not.
Internal review F1; see Spec-Requires.)*
**What remains is resolution** — given a classified edge, what does the query
return to the caller? That is this spec, and 0030 hands it over explicitly:

> *"following `corrected`→corrector or `absorbed_duplicate`→absorber is the
> QUERY layer's job (0028 v2's reason→resolution table)."*

### 1a. Three corrections to v1, recorded because they are load-bearing

1. **v1's `corrected` row was WRONG, not merely underspecified.** It said
   "follow the correction to the value that replaced it and return THAT value
   for T". Dev's internal review proved that impossible: `plan_correction`
   retires the prior with `(prior.id, replacement.valid_from, "corrected")`, so
   `corrected.invalidated_at == corrector.valid_from` **by construction** and
   the intervals are adjacent, never overlapping. A corrector can never cover a
   T the prior held. See §4b-i.
2. **v1's table was total over SIX; the registry has SEVEN.**
   `revoked_source` — 0022's reserved seat — was absent. A table that claims
   totality and omits a registered reason is the failure mode this spec's own
   round-1 F1 was about, present in the spec that raised it.
3. **`known_as_of` is removed from v2's API.** v1 carried it as "the audit
   bonus"; it is now v3's whole subject.

## 2. Field contracts touched

Read-only. This spec **adds no field and mutates none**.

| field | use |
|---|---|
| `Edge.valid_from`, `Edge.invalidated_at` | the held interval `[valid_from, invalidated_at)` |
| `Edge.invalidation_reason` | the resolution key (§4b) |
| `Edge.supersedes` | backward pointer; the forward walk needs the §5.1 accessor |
| **`SqliteStore.read_window(user_id)` — NEW public API** | a read-only context manager: BEGIN under the instance lock, or JOIN an already-open transaction; ROLLBACK on error, COMMIT on exit. `current_state`'s shape (`sqlite.py:312-330`) extracted and made public. **Every other consumer:** `current_state` becomes a JOINER rather than an opener — its own open-or-join logic is unchanged in behaviour, so a caller outside a window sees exactly today's semantics. `edges(active_only=False)` and `edges_superseding` join it when called inside one. **Preserves the contract:** opening no window is today's behaviour; the only new obligation is on the as-of resolution, which must open exactly one (V-ONE-SNAPSHOT) |
| `Edge.provenance.disclosure` | 0030's classification input |

**New substrate required:** `Store.edges_superseding(user_id, edge_id)` —
contract in §5.1, queued by dev, shipping with this spec's acceptance.

## 2c. Untrusted inputs — REQUIRED, blocking

**The untrusted input is T itself.** A caller chooses the timestamp, and the
question this section must answer is: *can a caller reach content by choosing
T that they could not reach at T=now?*

**NOT WITHOUT A CLAMP — and an earlier cut of this section claimed otherwise.**
Internal review F2 found the counterexample: **0032's sleepers.**
`Edge.valid_now` withholds at now every edge whose `valid_from > now`, and it
is part of `assertable`. §4a step 1 as first written admitted any edge with
`valid_from ≤ T`, so a caller choosing a **future T** would reach a
not-yet-valid fact that the present refuses to assert — precisely the property
this section claimed was impossible. `valid_now`'s own docstring records the
measured hazard it closed: an edge "assertable a day before it became true",
and 0031 Phase A makes that window agent-reachable. **The as-of axis would
have reopened it.**

**REQUIRED, and now specified in §4a: `T > now` is REFUSED.** As-of is a
question about the **past**.

*Owner's ruling, 2026-09-06, verbatim: **"refuse"** — external round 2's R2-3.
v2 said `T > now` is clamped "or refused", declaring **two observable outcomes
for one input**, which is 0011 R1-4's unconformable shape: a spec that names two
cannot be conformed to, and REFUSAL was chosen there for the same reason it is
chosen here. Research had caught that exact defect in another seat's spec hours
before shipping it in this one.*

**Why refusal and not the clamp**, recorded so the alternative is not
reintroduced as a convenience: a clamp **silently answers a different question
than the one asked**, and disclosing it needs a whole response envelope —
`effective_as_of`, a `clamped` flag, defined behaviour when the result set is
empty, cache-key semantics, and the same treatment on both `recall` and
`facts_valid_at`. Round 1 named the hole in the cheap version: a clamp
"recorded in each result" discloses **nothing when there are no results**. A
refusal states in one line what the envelope was for.

**The refusal is typed** — `FutureAsOfRefused`, carrying the requested `T` and
the `now` it was compared against, so a caller can tell a future-T refusal from
any other failure without parsing a message. It is never silently empty: an
empty result would be indistinguishable from "nothing was held then".

**ONE OUTCOME PER SURFACE, not a choice at one surface** *(internal review F6,
2026-09-06: v4 said "RETURNED-or-RAISED per this spec's taxonomy" two sentences
after invoking 0011 R1-4 against exactly that shape — a spec naming two
observable outcomes for one input cannot be conformed to, and this seat had just
found that defect twice elsewhere)*:

- **At the library**, `FutureAsOfRefused` is **RAISED**. Not returned, not an
  empty result, not a sentinel.
- **At any tool layer that exposes an `as_of` argument**, it is **SERIALIZED**
  as a refusal result and never raised to the transport — 0037 v11's form:
  `{"ok": false, "refusal": "future_as_of", "T": …, "now": …}`. A tool boundary
  that lets a typed exception escape converts a specified refusal into an
  unspecified transport error.

These are **one outcome each at two different surfaces**, which is what a
taxonomy is for; the defect was offering two at one surface. **MCP's `recall`
tool does NOT gain `as_of` in v2** (§10 Q5, CLOSED — 0031 §4d's argument on a
time axis). So v2's as-of surface is the **library only**; the **shipped MCP
tool is unchanged**; and the serialized-refusal bullet is **prospective** — it
binds nothing today and binds the first tool layer that ever carries the
argument. *(R4-4: v10 said "OPEN" here while §10 said "CLOSED" — the same
question answered two ways in one document. The three sentences above are the
consistent statement the reviewer asked for, and any future change to Q5 must
edit this site and §10 together.)*

### 2c-i. T's own validation — the input this section is named for

*(Internal review F7, 2026-09-06: §2c's first sentence is "the untrusted input
is T itself", and v4 then treated only the FUTURE case. Malformed T is the row
this spec's own 2c template requires — empty / malformed / unrecognised /
adversarial — and the shipped answer already exists, so omitting it was a gap in
the section, not an open design question.)*

**T is normalized by `as_utc_required` (`schema.py:41`) BEFORE it is compared to
`now`, and the order is load-bearing.** A naive datetime compared against an
aware `now` raises `TypeError` at runtime in Python — a failure that is neither
of this spec's named outcomes and reaches the caller as a bare interpreter
error. Normalizing first makes the malformed case a specified `ValueError`.

| input | outcome |
|---|---|
| naive `datetime` (no tzinfo) | `ValueError` from `as_utc_required` — **distinct from `FutureAsOfRefused`** |
| a `str`, or any non-datetime | `ValueError` from `as_utc_required` (0030 V-NORM-TOTAL; the `11c476c` str-in-datetime lesson) |
| `T == now` exactly | **PERMITTED.** `now` is not the future; the boundary is `T > now`, strictly |
| `T = None` to `facts_valid_at` | `TypeError` — the argument is required there; on `recall` a `None` `as_of` means "no as-of axis", which is today's behaviour |
| aware datetime, `T > now` | `FutureAsOfRefused` (above) |

**V-NORM-FIRST** (§6) asserts the ORDER: a naive `T` in the future must raise
`ValueError`, not `FutureAsOfRefused` — the mutant that compares before
normalizing produces the wrong one of two real outcomes, which no test that
only checks "it failed" would catch.

**V-NO-FUTURE** (§6) asserts that a constructed sleeper edge is returned at no
permitted T, including T = its own `valid_from`, **and that `T > now` refuses
rather than returning anything at all.** *(This is 0032's V-SLEEPER
meeting this spec's axis; 0032 §8 explicitly did not own "the present is a
single now read", and v2 now does.)*

**With that refusal, the property holds, and it is enforced upstream.** 0030's
**V-NEVER** invariant
holds that for every edge whose reason ∈ {`corrected`, `disputed`,
`revoked_source`} or class ∈ {quarantined, use_only}, `classify_as_of` never
returns GROUNDED_AS_OF **for any T, including inside the interval and at its
boundaries**. This spec adds no path around it: every row of §4b takes 0030's
verdict as its input, and no row upgrades a verdict.

**Consequences, stated as obligations:**
- **The as-of axis must not become a revocation bypass.** `revoked_source`
  stays `NOT_RETURNABLE` at every T. 0022 non-revival "never time-travels away".
- **The current-truth pointer (§4b-i) inherits current-state classification.**
  A pointer whose head is disputed or revoked renders as a pointer to a fenced
  or excluded record, never as truth — otherwise the bypass returns by the
  other door.
- **T is not a capability.** No scope, principal or disclosure decision keys on
  T; §3b's boundary is evaluated identically at every T.

### 2c-ii. Assertions about reach — REQUIRED

- This spec reaches **only** edges already visible to the principal under 0021.
  As-of narrows a candidate set; it never widens one.
- It reaches **no** episode, wiki, or export surface.
- It cannot cause a write. Every operation is a read.

## 3. Trust-class matrix — REQUIRED, blocking

0030 owns the classification; this spec owns what the caller receives.

| 0030 verdict at T | what v2 returns | may it be asserted? |
|---|---|---|
| GROUNDED_AS_OF | the value (§4b) | yes — it was held at T |
| GROUNDABLE + `stale-at-recall` | the value, flagged | yes, flagged |
| FENCED_AS_OF | the record as a **claim about what was believed** | **no** |
| EXCLUDED | nothing | no |
| (unclassifiable) | nothing, `INDETERMINATE`. **A cause is enumerated when it arises WITHIN the principal's view** — branching, an unclassifiable reason (§4b-i, §4b-iii). **`SUCCESSOR_UNAVAILABLE` carries NO cause by design**, because a distinguishable cause there is the existence signal R4-1 removes: a hidden successor and a missing one are one outcome | no |

**No row of §4b upgrades a 0030 verdict.** That is the single structural
guarantee this spec offers, and V-NO-UPGRADE (§6) asserts it.

## 3b. Authorization and scope

Unchanged from v1 and from 0021: resolution occurs entirely within the
principal boundary, evaluated identically at every T (§2c). A cross-principal
edge is not a candidate at any T.

## 4. Behaviour

### 4a. The exact resolution (deterministic)

For a query at T over the principal's candidate edges:

0. **Refuse the future.** If `T > now`, **refuse** with the typed
   `FutureAsOfRefused` (carrying `T` and the `now` compared against). No
   clamping, no partial answer, no empty result. **As-of never answers about
   the future** — see §2c and V-NO-FUTURE.

   **ONE CLOCK READ PER RESOLUTION — required, and the seam is microseconds
   wide. Refusal does not remove this requirement, it relocates it.** The store's
   INJECTED clock (`SqliteStore(…, clock=None)`, `sqlite.py:91`, read through
   `_now()`, `:1707`) is invoked **exactly once**, at entry, and that value is
   threaded to the `T > now` test of this step and to `classify_as_of`'s `now`
   parameter. **The as-of branch consults neither `Edge.valid_now` nor
   `Edge.assertable`** — see step 2 and §4c. If step 0 read the clock and any
   later predicate read it again, a sleeper whose `valid_from` falls between the
   two reads would pass the refusal test at the first and be valid at the second,
   and the direction of that race is the unsafe one. *0032 §10 deferred
   "per-request clock snapshot" because no consumer then compared two reads;
   as-of is the first consumer that does, so v2 owns it.* (Internal review, dev,
   2026-09-05.)

   *v9 REWROTE THIS PARAGRAPH. v8 said the captured value is used by 0032's
   `valid_now` "inside `assertable`", which is the TWO-CLOCK design the v6 fold
   removed from V-ONE-CLOCK and from §4c — and left here, in the section that
   states the algorithm. `Edge.valid_now` is a `@property` with no parameter
   (`schema.py:568`) reading the process wall clock (`utcnow()`, `:25`): nothing
   can be threaded to it and a recording clock counts zero calls from it, so an
   implementer following v8's §4a would have rebuilt the exact race V-ONE-CLOCK
   forbids. External round 3, R3-1.*
1. **Time-validity.** Keep edges whose held interval contains T:
   `valid_from ≤ T AND (invalidated_at IS NULL OR T < invalidated_at)` (open interval at the upper bound —
   `invalidated_at` is the instant the successor takes over). An edge with
   `invalidated_at ≤ valid_from` has an **empty interval** and is held at no T.
2. **Classification and validity.** Ask 0030's `classify_as_of(envelope,
   snapshot_raw, current_state, T, now, view)` for the verdict at T (§3),
   passing the threaded `now`. **The branch's validity predicate is
   `assertable_as_of(…, T, now, view)` (`asof/classify.py:161`) — the recall
   path's `assertable` drop DOES NOT RUN on this branch** (§4c, V-ONE-CLOCK).
   **`classify_as_of` SHIPPED 2026-09-06 at `ccaa9cc`**, as this spec's own
   Spec-Requires section records.

   *v8 said "this call has no implementation today … v2 cannot ship before it
   exists", contradicting Spec-Requires four pages above it in the same
   document. R3-1.*
3. **Resolution.** Apply §4b, keyed by `invalidation_reason`.
4. **Render.** Attach the resolution tag and the interval to each result.

Deterministic given **`(store snapshot, requested T, captured now, principal
scope, policy version)`** — external round 2's correction. `(store state, T)`
was wrong on its face: the future-time handling and the current-head
classification both depend on `now`, and §3b applies scope BEFORE historical
eligibility, so the same store and the same T give different results to
different principals. **No step reads a clock at all.** The one injected-clock
value captured at step 0 is threaded to every predicate that needs it, **the
current-truth pointer of §4b-i included** — that pointer is a current-state
fact evaluated at *that same* `now`, never a second read. *(R4-2. **WITHDRAWN wording:** v10 said
"no step consults wall-clock now **except** the current-truth pointer", which
names one step that does — the two-clock design the fold removed everywhere
else. Both of the round-3 sweeps keyed on phrases and this survived across a
LINE BREAK; the sweep that found it swept the noun.)*

### 4b. The reason→resolution table — closed, and TOTAL over the registry

*This is the core section, internally reviewed 2026-09-05. Every row is derived
from `DISPOSITIONED_REASONS` (totality), 0030's accepted classification table
(the verdict), and the shipped store (the mechanism). No row is derived from a
field comment — round-1 F1's lesson.*

#### The verdict column is DERIVED, not transcribed (external round 2, R2-2)

v2's first version wrote verdicts by hand and used **`GROUNDED`** — a name that
ships in **neither** vocabulary. There are two, and conflating them is what the
round caught:

- **`AS_OF_DISPOSITION`** (`schema.py`) maps a *reason* → `GROUNDABLE` /
  `FENCED` / `EXCLUDED`.
- **`Result.status`** (`asof/classify.py`) is the *classification outcome* →
  `GROUNDED_AS_OF` / `FENCED_AS_OF` / …

**This table is generated from the shipped enum, in registry order, and must be
regenerated rather than edited:**

| reason | `AS_OF_DISPOSITION` | classifier status at T |
|---|---|---|
| `disputed` | `FENCED` | `FENCED_AS_OF` |
| `corrected` | `FENCED` | `FENCED_AS_OF` |
| `superseded` | `GROUNDABLE` | `GROUNDED_AS_OF` |
| `revoked_source` | `EXCLUDED` | *(not returnable)* |
| `lapsed` | `GROUNDABLE` | `GROUNDED_AS_OF` |
| `decayed` | `GROUNDABLE` | `GROUNDED_AS_OF` |
| `absorbed_duplicate` | `GROUNDABLE` | `GROUNDED_AS_OF` |

**THE GENERATOR IS AN ARTIFACT OR THIS CLAIM IS PROSE** *(internal review F8,
2026-09-06)*: v4 said "generated from the shipped enum" and "totality asserted
at generation" while **no generator existed anywhere** — `specs/evidence/`
carries 0001, 0011, 0019, 0020 and 0022, and no 0028. So "asserted at
generation" described a process only its author had run, over a table that is
prose in a research-tree candidate. That is the same finding 0037 round 2 took
on its own corpus, and this seat's own derived-basis rule turned on itself: **a
hand-maintained table standing in for a generated one fails silently and reads
as rigour precisely because it is captioned "generated".**

**WRITTEN, 2026-09-07.** `specs/evidence/0028/reason_resolution_table.py`,
for dev to place at `specs/evidence/0028/` (the shape `0031`'s
`connection_census.py` already sets — research authors, dev places). It emits
this table from `AS_OF_DISPOSITION` in registry order and asserts three things
at generation time: **totality** (`set(AS_OF_DISPOSITION) ==
set(DISPOSITIONED_REASONS)`, seven reasons — an eighth fails here and in the
registry's own test, so it must be dispositioned twice), **registry order** (it
iterates `DISPOSITIONED_REASONS` rather than sorting, so the claim is true by
construction), and **closure** (every disposition maps to exactly one classifier
status, or it refuses to render).

`--check <spec.md>` is V-CROSS: it parses the spec's table **as data** and
compares, rather than re-rendering the spec's prose into its own shape. Run
against this document it reports `V-CROSS OK: 7 rows, registry order, totality
asserted`.

*So the ROW ORDER is now **verified, not inherited**. v5 recorded it as
inherited because nothing established that these seven rows were in registry
order; the generator establishes it, and the answer is that the order was
already right. That is worth stating plainly: the claim was true and
unverifiable, which is a different defect from a claim that was false, and it
is the one this programme keeps finding.*

**V-CROSS compares this table to the enum as data** — reading the table from
the spec file and the enum from the module, so neither side is transcribed —
so a registry change fails the test rather than silently diverging from a
paragraph — the same
derived-basis rule this programme applies to every other list.

**Totality is over the seven registered reasons plus the `None` case**, not
over the six v1 listed.

| reason | 0030 verdict at T | **resolution** | tag |
|---|---|---|---|
| *(current — `invalidated_at is None` **AND `valid_from ≤ T`**)* | GROUNDED_AS_OF | `RETURN_SELF` | `current` |
| **superseded** | disposition `GROUNDABLE` → status `GROUNDED_AS_OF` | `RETURN_SELF` | `in-interval` |
| **lapsed** | GROUNDABLE + `stale-at-recall` | `RETURN_SELF_FLAGGED` | `in-interval-stale` |
| **decayed** | GROUNDABLE + `stale-at-recall` | `RETURN_SELF_FLAGGED` | `in-interval-stale` |
| **absorbed_duplicate** | GROUNDED_AS_OF | **canonical: unreachable — empty interval by construction** (§4b-ii); **legacy (the only shipped-reachable case): `INDETERMINATE`**; three defensive corrupted-state cases in §4b-iii | `absorber-indeterminate` |
| **corrected** | FENCED_AS_OF | `FENCED_SELF` + `POINTER_TO(corrector)` — a pointer, never a value at T (§4b-i) | `corrected-fenced` |
| **disputed** | FENCED_AS_OF | `FENCED_SELF`, no target | `disputed` |
| **revoked_source** | EXCLUDED | `NOT_RETURNABLE` | `revoked-excluded` |
| **reason outside the registry** | — | `NOT_RETURNABLE`, **fail closed** | `unknown-reason-excluded` |
| **`invalidation_reason is None`** on an invalidated edge | — | `NOT_RETURNABLE`, **fail closed** | `unknown-reason-excluded` |

**Outcome vocabulary (closed):** `RETURN_SELF`, `RETURN_SELF_FLAGGED`,
`POINTER_TO(x)`, `FENCED_SELF`, `NOT_RETURNABLE`, `INDETERMINATE`.
`INDETERMINATE` is **distinct from "no target exists"**, and it is never silent
about ITSELF — the outcome is always returned, never collapsed into an empty
result. **Whether it carries a CAUSE is TWO CLASSES, not one rule:**

- **an INDETERMINATE arising from a condition observable WITHIN the caller's
  view** — branching, a cycle, an unclassifiable reason — **carries its cause
  and discloses it.**
- **`SUCCESSOR_UNAVAILABLE` carries NO principal-facing cause, by design**, so
  a hidden successor and an absent one stay indistinguishable (§5.1, R4-1,
  V-NO-EXISTENCE-SIGNAL). **A distinguishable cause there IS the existence
  signal.**

Collapsing *cannot tell* into *nothing* is the failure this product line exists
to name; **disclosing WHY across a scope boundary is a different failure, and
this spec refuses both.**

*(R6-1. **WITHDRAWN wording:** v12 said "every instance is disclosed with its cause" — the normative
definition, still carrying the one-rule form after R5-3 corrected the reviewer
CHECKLIST that summarises it. **The summary was fixed and the definition it
summarises was not**, which is the bound-rides-in-the-summary class inverted.)*

#### 4b-i. A corrector NEVER covers T — construction, not a case

`plan_correction` retires the prior with
`(prior.id, replacement.valid_from, "corrected")`, applied literally by
`_invalidate_edge_row`. So the intervals are **adjacent**:

    corrected: [v, c)        corrector: [c, …)

For any T the corrected edge held, `T < c`. For `T ≥ c` the corrector is itself
the held edge and 0030 classifies it directly. A backdated `correct(date=…)`
moves `c` earlier, shortening the prior's interval; `c ≤ v` empties it.
`superseded` uses the identical construction.

**So there is no conditional and no second branch.** A corrected edge returns
`FENCED_SELF` plus a pointer labelled *"where truth became"*.

**The distinction this rests on:** *"what was held at T"* and *"where truth
lives now"* are **different questions**. The pointer is a current-state fact
offered beside a valid-time answer, and must render as such.

**The pointer walk.** At most **N hops** (N pinned here, not in code). **There
is no T inside this walk**; no termination condition may reference one.
Terminate on: the chain **HEAD** (`disposition is HEAD` — never "returns empty", which the withdrawn list return made ambiguous between a head and an unavailable successor; the head predicate is `HEAD`-ONLY and `SUCCESSOR_UNAVAILABLE` terminates the walk as `INDETERMINATE`, never as a head — R4-5, coupled to R4-1. The
accessor's unique-or-empty contract makes the head well-defined at every hop);
a terminal reason; the **bound** → `INDETERMINATE`, cause
`hop-bound-exceeded`; or a **cycle** → `INDETERMINATE`, cause `cycle`.

**N is pinned for integrity, not cost** (§5.1: the walk is in-memory over one
read). An unbounded walk over a corrupted store can cycle; and **depth is
itself a signal** — a correction of a correction is rare, a third-order one is
a smell better surfaced as `INDETERMINATE` than followed. **N = 3.**

**The head carries its own classification.** `edges_superseding` follows
`supersedes`, written by **both** corrections and ordinary supersessions, so a
chain can end at a head that is itself disputed, revoked, or
corrected-without-successor. The pointer therefore resolves to *"the head,
classified by 0030 at T=now"* — a fenced or excluded head renders as a pointer
to a fenced or excluded record, **never as truth**.

#### 4b-o. ONE SNAPSHOT, not one clock read (external round 2)

v2 required a single clock read (V-ONE-CLOCK) and that is necessary but **not
sufficient**. The interval filter, the successor walk, the current-head
classification, the ranking candidates and the render all read the store; if
they read it at different instants the walk can assemble a successor chain
**from states that never coexisted**.

**All store reads in one resolution come from ONE consistent snapshot.** The
accessor contract (§5.1) states it per call; this states it for the
resolution.

**THE MECHANISM, NAMED** *(internal review F2, 2026-09-06; the quoted v4 wording is **WITHDRAWN**: v4 said "where the
backend cannot provide a snapshot, the required behaviour is a documented
transaction/isolation level" — vague where it need not be, because the shipped
store already provides it. A spec that describes a property without naming the
mechanism that yields it is the defect class both 0037 rounds found.)*:
`SqliteStore.current_state` (`store/sqlite.py:300-312`) opens an explicit
`BEGIN` under the instance lock, derives inside it, commits, and **joins an
already-open transaction rather than nesting**. 0030's V-WINDOW asserts the
snapshot property in both journal modes. **What a concurrent WRITER sees is
measured in §5 and is not "refused"**: under the default journal mode it waits
and succeeds if the window closes within its `busy_timeout`, or **fails with the
store's WRAPPED refusal naming the COMMIT site (`V-LOCK-REFUSAL-FORM`, 0029
v11), SQLite's original `database is locked` retained as the exception cause**,
and **loses the write**; under WAL it proceeds at once and
the reader's snapshot still holds. *v8 said the SHARED lock "refuses a
concurrent writer" here and in §5 and in the version cell — three sites for one
claim, and round-3 correction 7 was right that it names neither outcome.*

That "joins rather than nests" is what makes the requirement satisfiable, and
also what makes the failure easy: **the resolution must open ONE outer window
that every read joins** — the interval filter's `edges(active_only=False)`,
each hop's `edges_superseding`, and each `current_state` call. A resolution
that simply calls the shipped `current_state` once per hop **without an outer
window gets a fresh snapshot per call**, which is exactly the failure 4b-o
exists to forbid, while looking correct at every individual call site.

**THE SURFACE, because there isn't one yet** *(internal review F2)*. v5 required
the resolution to "open ONE outer window that every read joins" and **named
nothing it could call**: `_journal_scope` (`sqlite.py:146`) and `_write_txn`
(`:161`) are private, and `epoch_txn` (`:282`) returns an int and opens
nothing. `current_state` opens-or-joins, but self-contained. So v5 required a
capability the store does not expose — **the identical defect to §5.1's indexed
read, in the section written to fix that class.**

**NEW: `SqliteStore.read_window(user_id)`** — a public read-only context
manager: BEGIN under the instance lock, or JOIN an already-open transaction;
ROLLBACK on error, COMMIT on exit. Exactly `current_state`'s shape
(`sqlite.py:312-330`), extracted. `current_state`, `edges(active_only=False)`
and `edges_superseding` all join it.

**V-ONE-SNAPSHOT** (§6) asserts it: under WAL, a write committed between two
reads of one resolution is **invisible to the second read** (mutant: no outer
window — the second read sees it); under rollback-journal, **a concurrent
writer cannot COMMIT while the window is open** — it waits and commits after
the window closes, or its commit fails and the write is rolled back (§5's
measured rows). *(R4-3. **WITHDRAWN wording:** "refused for the window's duration" was a THIRD
wording of the disproved claim, surviving two sweeps that keyed on the other
two. A hand-list of phrases cannot be total over the phrasings a document can
hold; the sweep is over the NOUN — writer, refusal — with every hit read.)*

#### 4b-ii. Reachability, stated per row

Two dispositions are **structurally unreachable**, and saying so is part of the
specification:

- **`absorbed_duplicate`, canonical path.** Absorption sets
  `incoming.valid_from = min(incoming, prior)` then invalidates the prior at
  that timestamp, so `invalidated_at ≤ valid_from` — an **empty interval**,
  never held at any T. Step 1 of §4a rejects it before the reason is consulted.
  The only `absorbed_duplicate` rows with a non-empty interval come through the
  generic invalidation paths — the legacy class *without* `contributor_ref` —
  i.e. `INDETERMINATE`.
- **A corrector covering T** (§4b-i). The pointer is live; a resolved *value at
  T* is not.

#### 4b-iii. The absorber, when asked — and WHICH of these a shipped writer can produce

**External round 1, R2-4: this table contradicted §4b-ii and the contradiction
was real.** §4b-ii establishes that a canonical absorption always yields an
**empty interval** — verified in code, not asserted: `graph.py` sets
`incoming.valid_from = min(incoming.valid_from, prior.valid_from)` and then
invalidates the prior **at that same timestamp**, so
`invalidated_at ≤ valid_from` for every canonically absorbed row. An
`absorbed_duplicate` row therefore reaches this table **only if its interval is
non-empty**, which by §4b-ii means it came through the legacy path and has **no
`contributor_ref`**.

So exactly one row below is reachable from a shipped writer, and the other
three are reachable only from a store state **no shipped writer produces** — a
hand-edited row, a foreign writer, or corruption. They are retained as
defensive handling and **labelled as such**, rather than presented as ordinary
cases a reader should expect to hit:

| store state | reachable from a shipped writer? | resolution | cause |
|---|---|---|---|
| no `contributor_ref` at all (legacy) | **YES — the only one** | `INDETERMINATE` | `absorber-unreachable-legacy` — the store CANNOT tell |
| unique canonical row, non-empty interval | **no** — canonical absorption is empty-interval by construction | `POINTER_TO(absorber)` | — |
| canonical rows exist, none match | **no**, same reason | `NOT_RETURNABLE` | `no-absorber` — the store CAN tell |
| more than one canonical row | **no**, same reason | `INDETERMINATE` | `ambiguous-absorber` — `derive_absorbed_by` raises; the query must not be more permissive than the exporter |

**Consequence for §6a:** the three defensive rows cannot be reached by
exercising the API, so their acceptance cells are **constructed by writing the
row directly** and are labelled *corrupted-state cells*. A cell that cannot be
built through a shipped path and is not labelled as synthetic reads as a
supported case, which is how defensive handling becomes an implied contract.

#### 4b-iv. `RETURN_SELF` may return more than one edge

0012 Design 1 reinforcement persists the incoming edge and retires nothing, so
one held value can exist as two active edges at T. Returning both is **correct
at this layer** — both were held. De-duplication is the render layer's
(`collapse_for_render`); this spec neither performs nor requires it.

### 4c. API

- **Recall pre-filter:** `recall(user, query, *, as_of=None)`. `as_of=None` →
  today's behaviour unchanged (V-COMPAT). `as_of=T` → the §4a resolution
  produces the candidate set, then normal recall (lexical / 0027 semantic +
  gate + budget) runs over it. **As-of is a pre-filter; ranking is unchanged.**
- **Direct lookup:** `facts_valid_at(user_id, subject, relation, T, *,
  principal=None, policy=None)` — **carries the scope inputs it needs, because
  it promises recall's decision** (round-3 R3-3). v8 declared it without
  `principal` or `policy` while stating it uses the same `ScopeView` as recall:
  it could not have reproduced a principal-dependent visibility decision, and
  the same store and T would have answered every caller identically — the
  opposite of §3b, which this spec says applies scope BEFORE historical
  eligibility. The parameters are keyword-only and default to `None`, matching
  `edges_superseding`; a caller passing neither gets the unscoped view exactly
  as `recall` does. **V-SCOPE-DIFFERENTIAL** (§6): two principals against one
  store, a record visible to only one, the same `(subject, relation, T)` —
  each sees their own answer, and the record's holder sees it at every T its
  interval covers while the other sees it at none.
- **Filter position, specified because it is load-bearing:** the as-of filter
  sits **AFTER per-record visibility** (`view.visible(e)`, which is
  record-level and keys on neither T nor `active`), and **the branch's own
  predicate is `assertable_as_of(…, T, now, view)` — the recall path's
  `assertable` drop DOES NOT RUN on the as-of branch** (V-ONE-CLOCK, F1).
  Retired edges are already scope-evaluated today, so as-of narrows an
  already-visible set and never widens one.

  *v6 corrected this bullet: it still said the filter sits "BEFORE the
  `assertable` drop", so an implementer following §4c would have built exactly
  what V-ONE-CLOCK's second mutant forbids — the carrier the F1 fold did not
  reach, found on dev's second read. A fix that leaves a contradicting
  instruction elsewhere in the same document has not landed.*
- **Provenance on every result:** `{valid_from, invalidated_at,
  invalidation_reason, resolution_tag, indeterminate_cause?}`.
- **`known_as_of` is NOT in v2.** It is v3's subject.
- **Under `as_of`, the wiki and episode sections are OMITTED** (internal review
  F4). `_recall` renders the wiki and CURRENT episodes beside the edges; a
  T-answer carrying a now-wiki and now-history would assert present truth
  inside a past answer, which is the incoherence this spec exists to avoid.
  Omission is chosen over an explicit "current, not as-of" label because a
  label relies on the reader honouring it.
- **The proactive path** `recall(query=None, as_of=T)` — the session briefing —
  **refuses `as_of`**. A briefing is a statement about now; there is no
  coherent as-of briefing, and defining one is out of scope.

**THE v1 LANE ASYMMETRY IS WITHDRAWN — it is false in the shipped code.**
*I carried it forward from v1 as "still true"; internal review F3 read the
code and it is not.* Retirement is `UPDATE edges SET active=0, json=?` and
**leaves `edge_embedding` untouched**; `semantic_candidates` joins
`edge_embedding` to `edges` with **no active condition**; and 0027's V-FRESH
compares content digests — retirement does not change content, so a retired
edge's embedding is **fresh**. Retired edges are therefore semantic candidates
today and are dropped later by `assertable`.

**The true statement:** both lanes reach retired edges — lexical via
`store.edges(user_id, active_only=False)`, semantic via the unfiltered join —
and the as-of pre-filter sits **after visibility**, with the branch's own
predicate `assertable_as_of` in place of the recall path's `assertable` drop,
which does not run here (V-ONE-CLOCK; R3-1 found this sentence still stating the
old order 34 lines below the bullet that had been corrected).

### 4d. Transaction-time — OUT OF SCOPE, v3

`observed_at` / `known_as_of` are v3 on the owner's 2026-09-05 split ruling.
0029 supplies the carrier. **v2 makes no claim about what was *known* at any
time** — only about what was *held valid*.

### 5.1 `Store.edges_superseding` — the accessor contract

**This section did not exist and was cited four times** (external round 1, R2-1).
The pointer walk depends on it, so leaving it to implementation interpretation
meant the walk had no defined behaviour. Written here rather than deferred.

```
Store.edges_superseding(user_id: str, edge_id: str, *, principal=None, policy=None)
    -> SuccessorLookup

class SuccessorDisposition(str, Enum):          # CLOSED vocabulary (R4-1)
    HEAD                  = "head"              # the edge asserts no supersession
    SUPERSEDED            = "superseded"        # >= 1 successor visible IN THIS VIEW
    SUCCESSOR_UNAVAILABLE = "successor_unavailable"
                                                # the edge asserts supersession; none visible

SuccessorLookup:                                # exactly two fields
    disposition: SuccessorDisposition
    successors:  tuple[Edge, ...]               # empty unless SUPERSEDED;
                                                # ordered valid_from asc, then id asc
```

**Precedence:** visible successors → `SUPERSEDED`; else **the queried edge's
own assertion, READ ONLY IF THAT EDGE IS ITSELF VISIBLE IN THIS VIEW** →
`SUCCESSOR_UNAVAILABLE`; else `HEAD`. **Total over every store state.**

***R5-1 — the existence signal ONE LEVEL UP, at the INPUT rather than the
output, and it is the same defect R4-1 closed.*** v11 filtered the successor
ROWS through `ScopeView` and then took the **queried edge itself from the
unfiltered collection** to read its `invalidation_reason`. So a principal
calling the public accessor with an identifier outside their view got
**`HEAD` for a nonexistent id and `SUCCESSOR_UNAVAILABLE` for a hidden
corrected one** — two distinguishable answers about an edge they may not see.
V-NO-EXISTENCE-SIGNAL did not catch it because it tested a **visible** prior
with a hidden successor and never a **hidden queried edge**: the test's
coverage was the shape of the finding it was written for.

**The fix is one clause, not a new mechanism:** the queried edge's assertion is
readable only when that edge is visible in the caller's view. An invisible
queried edge therefore asserts nothing *to this caller*, exactly as a
nonexistent one does, and the two paths become the same code. **Successors are
still searched among visible rows**, so a visible `S` naming a hidden `M`
still yields `SUPERSEDED` when `M` is queried — that discloses nothing, because
`S` and its `supersedes` field were already visible.

**`edges_superseding` IS NOT AN EXISTENCE ORACLE.** Its answers are a function
of what the caller may see, never of what the store holds.

**The holder's side of that state is a RANGE, not a value.** For a principal who
CAN see the hidden queried edge, the result is `SUPERSEDED` when its successor
is also in their view and `SUCCESSOR_UNAVAILABLE` when it is not — **never
`HEAD`**. That is what the positive control asserts, and it is stated as the
absence of `HEAD` rather than as one named disposition, because a control fixed
to a single value is over-fitted to a single state.

***R5-2 — v11's malformed-reference rule was written about the wrong
direction.*** It said *"a `supersedes` value that names nothing yields the same
`SUCCESSOR_UNAVAILABLE` as a hidden one"* — but the accessor searches
**forward**, for rows whose `supersedes == edge_id`, so a **backward** dangling
value on the queried edge is never read. **Two distinct states were collapsed
into one sentence** and the model's `missing` fixture tested only the first of
them. They are now named and specified separately in the table below.

***R4-1 — v9's typed result was itself the defect, and it was ours.*** v9 added
`omitted: int` and `causes: frozenset[str]` to close R3-2. But `omitted > 0`
with `causes == {"cross_user"}` **is an existence signal across the very
boundary §3b says must be indistinguishable**: it tells a principal that a
record they may not see *exists*. It is also unconstructible — a one-user scan
cannot produce the cross-user cause without making the cross-user observation
the scope forbids. And `frozenset[str]` is not a closed vocabulary; it admits
any string. **The fix removes the signal at the VIEW rather than masking it in
the RESULT:** a successor outside the principal's `ScopeView` is *not in the
view*, indistinguishable in kind from one that does not exist, so it produces
**no count and no cause**. Omission causes survive as **operator-only
diagnostics** on 0031 §4d's shipped precedent (extractor counters stripped from
MCP results, `mcp_server.py:186`) — a closed `_OmissionCause` enum, **never a
field of a principal-facing result**.

**Why `SUCCESSOR_UNAVAILABLE` reveals nothing:** `invalidation_reason` is a
field on **the edge's own row** (`schema.py:503`). A principal who can query
the edge can already read that it says `"corrected"`. The outcome therefore
tells them something they already hold, and adds nothing across the boundary.

**"Asserts supersession" is defined by a REGISTRY, never by a listed reason.**
v11 specifies `NAMES_A_SUCCESSOR` in `schema.py`, a **third registry total over
`DISPOSITIONED_REASONS`** under the same build-time equality gate as
`AS_OF_DISPOSITION`, refusing at import in both directions:

| reason | names a successor | why |
|---|---|---|
| `corrected` | **yes** | the host replaced the content |
| `superseded` | **yes** | W2 — the supersession path |
| `absorbed_duplicate` | **yes** | `AS_OF_DISPOSITION`'s own note: *"0028 resolves to the absorber"* |
| `lapsed` | no | staleness is not a successor |
| `decayed` | no | low confidence now is not a successor |
| `disputed` | no | trust revoked; nothing replaces it |
| `revoked_source` | no | 0022 withdrawal, non-revival |

*A hand-written set beside that registry goes stale silently. The design as
first sent named only `corrected`, and dev built it faithfully; an edge retired
`superseded` with a cross-scope successor then fell through to `HEAD` **while
the principal could read `invalidation_reason == "superseded"` on the row in
front of them** — not a leak but a lie the principal can catch, which is the
one outcome neither seat argued for. It survived a reading because the
`corrected` case still looked right. That is why the set is a gated registry
and not a list.*

**The contrast that looks like the same case and is not:** an **un-retired**
prior with only a hidden successor yields `HEAD` for the excluded principal,
and that is **correct** — the edge's own row asserts nothing, so the view is
internally consistent. The `SUCCESSOR_UNAVAILABLE` cases are exactly those
where the edge's own row makes a claim the disposition would otherwise
contradict.

*v8 declared `-> list[Edge]` while the contract below promised that dangling and
cross-user references are omitted, COUNTED, and reach §4b as distinct
`INDETERMINATE` causes. **A list cannot carry a count or a cause**, so an empty
list was observationally identical for a genuine chain head, a corrected edge
whose successor is missing, a successor in another scope, and a malformed
reference — and §4b's four-way distinction was unreachable through the very
interface that was supposed to feed it. R3-2. **The type is the mechanism — but
v9's first cut of that type leaked; see R4-1 above.** In v11 the distinction is
carried by the `disposition` alone: `HEAD` is a definite head, and
`SUCCESSOR_UNAVAILABLE` is §4b's `INDETERMINATE` — with **no cause reported**,
so a hidden successor and a missing one are one outcome.*

| clause | contract |
|---|---|
| **direction** | **DIRECT successors only** — edges whose `supersedes == edge_id`. Multi-hop is §4b's walk composing this, never the accessor recursing; a recursing accessor cannot be bounded by the caller |
| **scope** | Applies the SAME visibility decision as recall, **before** any historical filter (§3b's ordering). A record the principal may not see is **absent**, never a redacted entry — absence here is indistinguishable from non-existence **by design** |
| **inactive / future-valid** | **Included.** The accessor answers *what points at this*, not *what is assertable*; a successor that is itself invalidated or not yet valid is still the successor, and §4b decides its disposition. Excluding them here would hide a chain from the walk that must traverse it |
| **ordering** | Deterministic and total: `valid_from` ascending, then `id` ascending. Never relevance — this is a graph read, not a recall |
| **zero** | `disposition` decides, never an empty container: no visible successors **and** the edge's own `invalidation_reason` in `NAMES_A_SUCCESSOR` ⇒ `SUCCESSOR_UNAVAILABLE` (§4b's `INDETERMINATE`); no visible successors and no such assertion ⇒ `HEAD`. *(R4-5: v10's `[]` consumed the withdrawn list return, so "zero" could not distinguish the two.)* |
| **one** | the single successor |
| **multiple** | all of them, in the stated order. Multiplicity is **not** an error at this layer; §4b resolves it, and a walk that finds branching yields `INDETERMINATE` — **from the branching itself, not from a reported cause**, since the result carries none |
| **cross-user reference** | An edge whose `supersedes` names a record in another user's scope is **not in this view at all** — no count, no cause, nothing reported. It is indistinguishable from non-existence **by construction**, which is R4-1's whole point; the disposition then falls to the edge's own assertion. Following it would be a cross-user read |
| **successor row deleted (FORWARD)** | a visible edge that ASSERTS supersession (`invalidation_reason` in `NAMES_A_SUCCESSOR`) with no successor row present ⇒ `SUCCESSOR_UNAVAILABLE`, indistinguishable from a hidden successor. Constructible only by a raw `DELETE` after a real correction — §4b-iii's *"store state no shipped writer produces"* class |
| **dangling BACKWARD pointer** | a visible edge `S` whose own `supersedes` names an id that does not exist. **This does NOT affect `S`'s disposition**: the accessor searches for rows whose `supersedes == edge_id`, so `S`'s own backward value is never consulted when `S` is queried. Querying the **named nonexistent id** finds `S` and yields `SUPERSEDED` — correct, and disclosing nothing, since `S` and its `supersedes` field are already visible. **Never an exception** |
| **snapshot** | The accessor is called INSIDE `read_window` (§4b-o) and JOINS it; called outside one it opens its own, and V-ONE-SNAPSHOT's mutant fires. Every call in one resolution reads **one store snapshot** (§4b-o names the mechanism: `SqliteStore.current_state` joins an already-open transaction rather than nesting). The walk must not assemble a chain from successive states |
| **complexity** | **SCAN-BACKED in v2, and stated as such.** `supersedes` is a field inside the edge JSON (`schema.py:504`); `store/sqlite.py` has **no column and no index** for it, so it cannot be looked up — it can only be scanned for. **ONE read of the user's edges** (`edges(active_only=False)`, inside the resolution's `read_window`), **then the walk is IN-MEMORY over that one read**: the successor lookup at each hop is a `json_extract` match over the already-loaded set. **Cost: one scan of the user's edges, plus (edge count × N) in-memory comparisons**, N pinned at §4b — NOT N scans. **An index is Q3's substrate option, not this spec's claim** |

*v7 corrected this row: it opened with a PER-HOP scan model ("one hop is a scan … bounded by edge count × N hops") and then closed with the one-read model, so a single row stated two different costs — the m1 fix was appended beside the text it replaced instead of replacing it. A residual of the fix it records, and the same shape as everything else found in this spec today: the correction landed and the thing it corrected stayed.*

*v4 asserted here "one indexed read per hop… the accessor performs no scan"
— a property the store cannot provide, while §10 Q3 two pages later called the
same thing "the scan-backed accessor". Internal review F1 (2026-09-06) found
it: **a contract clause stating an outcome the code does not produce**, which
is the class both 0037 rounds found ("serialized only when procedural" with no
mechanism; an outcome the candidate set could not reach). The correction states
the truth rather than specifying an index, because an index is a column, a
schema version and a migration — and §7 of this spec says no stored byte
differs. A read-only spec does not get to require a write.*

**What it does NOT do:** it applies no as-of filter, makes no groundability
judgement, and returns no pointer structure. It is a graph accessor; §4b is the
policy.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| `as_of=None` | unchanged from today — V-COMPAT |
| `as_of` in the future | **REFUSED** — typed `FutureAsOfRefused` (owner's ruling 2026-09-06, R2-3; the clamp alternative is withdrawn, not deferred). *An earlier cut said "returns the current set" — FALSE: it would have returned the current set PLUS 0032's sleepers (F2).* |
| `as_of` before any record | empty result, not an error |
| empty-interval edges | never returned at any T (§4b-ii) |
| corrupted chain (cycle) | `INDETERMINATE`, cause `cycle` — never a hang |
| pre-v8 legacy rows | `INDETERMINATE` where the absorber is unreachable, never silence |
| **concurrent writer — DEFAULT rollback-journal mode** | **A writer cannot commit while the read window remains open.** It waits up to its configured `busy_timeout`; **if the window closes first it commits afterward** (measured: 1s window, committed after 0.74s), **otherwise the commit fails with the store's WRAPPED refusal naming the COMMIT site (`V-LOCK-REFUSAL-FORM`, 0029 v11), SQLite's `database is locked` retained as the exception CAUSE, and the write is ROLLED BACK** (measured: 7s window against the 5000ms default, raised after 5.02s, store unchanged). *(R6-2: v12 said the commit-time lock "surfaces unwrapped" and named it a recorded product defect. **WITHDRAWN — 0029 v11 landed at `9202d3d` inside this package's own pin range and `_write_txn` now OWNS every commit it opens**, so the wrapped form is what the sealed tree provides and what the window test asserts. The claim was true when written and false at the seal.)* **The store sets no `journal_mode` (`sqlite.py` sets only `busy_timeout`, `:108`), so this is what an ordinary caller gets**; `busy_timeout` is a constructor parameter (`:91`, default 5000ms), so the boundary is the caller's own configuration against the resolution's length |
| **concurrent writer — WAL (opt-in by the host)** | **The writer may commit DURING the window while the reader retains its original snapshot** — measured at both window lengths: committed after 0.01s, and the reader's second read inside the window still saw the prior state. WAL buys the writer through at no cost to the guarantee |
| **writer first, reader second (the mirror)** | **the reader is NEVER the one refused.** With the writer holding `BEGIN IMMEDIATE` and an uncommitted write, the reader's window opened immediately in both modes and read the prior state — RESERVED does not block a SHARED reader. The writer then waits (delete, committed after 1.54s) or proceeds (WAL, 0.00s). Same rule, not a second one |

## 6. Invariants and executable checks — REQUIRED, blocking

| id | invariant | check | test node |
|---|---|---|---|
| **V-COMPAT** | `as_of=None` is byte-identical to today's recall | differential test over the existing recall suite | **OWED at implementation** — no node exists today |
| **V-NO-UPGRADE** | no §4b row returns an outcome stronger than 0030's verdict allows | per-row assertion against 0030's classification | **OWED at implementation** — no node exists today |
| **V-NEVER-BYPASS** | for every edge with reason ∈ {corrected, disputed, revoked_source}, no T yields an assertable value — sampled inside the interval and at both boundaries | sampled-T test, mirrors 0030's V-NEVER | **OWED at implementation** — no node exists today |
| **V-TOTAL** | `set(RESOLUTION) == set(DISPOSITIONED_REASONS)` | registry equality test — an eighth reason fails BOTH this and the registry's own totality test, and must be dispositioned **twice** | **OWED at implementation** — no node exists today |
| **V-MUTANT** | an edge whose `invalidation_reason` is outside the registry resolves `NOT_RETURNABLE` | **planted mutant**, asserted — a fail-closed that is narrated rather than asserted is how one silently stops holding | **OWED at implementation** — no node exists today |
| **V-NONE** | `invalidation_reason is None` on an invalidated edge resolves `NOT_RETURNABLE` | typed-None test; the table is total over the TYPE, not over today's writers | **OWED at implementation** — no node exists today |
| **V-CROSS** | 0030's as-of column and §4b agree on every fenced/never row | `specs/evidence/0028/reason_resolution_table.py --check <this spec>`, which parses §4b's table AS DATA and compares it to `AS_OF_DISPOSITION` in registry order. Run 2026-09-07: `V-CROSS OK: 7 rows, registry order, totality asserted`. Mutants the accompanying test plants: an eighth reason; a shuffled row; an unmapped disposition | **CHECKED** `tests/test_0028_reason_resolution_table.py` (5 tests, the generated matrix) **and** the generator's `--check`, which reads §4b's table as data. *v10 named only the command.* |
| **V-HEAD** | the current-truth pointer resolves to the head **classified at T=now**; a fenced/excluded head never renders as truth | chain test terminating on a disputed head | **OWED at implementation** — no node exists today |
| **V-BOUND** | a chain longer than N, and a cycle, both yield `INDETERMINATE` with the stated cause | constructed-chain tests | **OWED at implementation** — no node exists today |
| **V-EMPTY** | an edge with `invalidated_at ≤ valid_from` is returned at no T | constructed empty-interval test | **OWED at implementation** — no node exists today |
| **V-NO-FUTURE** | a constructed sleeper (`valid_from` in the future) is returned at NO permitted T, including T = its own `valid_from` **and T = the query's clock snapshot instant** | sleeper test — 0032's V-SLEEPER meeting this axis (F2), with the sleeper planted at exactly the snapshot instant to catch a two-read race | **OWED at implementation** — no node exists today |
| **V-ONE-CLOCK** | the refusal test and every downstream validity predicate use ONE `now` per resolution, and **the as-of branch never consults `valid_now` or `assertable`** | **counted on a RECORDING CLOCK**: the store's INJECTED clock (`SqliteStore(…, clock=None)`, `sqlite.py:91`, read through `_now()`, `:1707`) is invoked EXACTLY ONCE per resolution, and that value is threaded to the `T > now` test and to `classify_as_of`'s `now`. The as-of branch's validity predicate is the interval test with that threaded `now`; the recall path's later `assertable` drop is REPLACED on this branch by `assertable_as_of(envelope, snapshot_raw, current_state, T, now, view)` (`asof/classify.py:161`). **Mutants: (1) a second invocation anywhere on the path; (2) ANY `valid_now`/`assertable` call on the as-of branch — grep-detectable AND behaviourally testable with a clock whose successive reads straddle a sleeper's `valid_from`.** | **CHECKED, FRACTION STATED** `specs/evidence/0028/check_asof_absence.py` — a check SCRIPT, not a pytest node. It covers `classify_as_of`, `assertable_as_of` and everything they reach; **a path through them exercised only elsewhere is outside the proof**, which the script's own header states. The resolution is unwritten, so the clock seam at the resolution level is OWED (§9). |
| **V-ONE-SNAPSHOT** | all store reads in one resolution come from ONE window (§4b-o) | under **WAL**: a write committed between two reads of one resolution is INVISIBLE to the second read — **mutant: no outer window, so the second read sees it**. Under **rollback-journal**: a concurrent writer **cannot commit while the window is open** — it waits and commits after the window closes, or its commit fails and the write is rolled back (§5's measured rows; never "refused for the duration", which names an outcome that does not occur — R4-3). Mirrors 0030's V-WINDOW, which asserts the property in both modes | **CHECKED** `tests/test_0028_window_transcript.py` (4 tests) — the snapshot measured holding in BOTH journal modes. *v10 described the shipped window's constructibility and named no runner.* |
| **V-NORM-FIRST** | `T` is normalized before it is compared to `now` (§2c-i) | a **naive** `T` in the future raises `ValueError` (from `as_utc_required`, `schema.py:41`), **NOT `FutureAsOfRefused`** — the mutant compares first and returns the wrong one of two real outcomes, which a test asserting only "it failed" cannot catch | **OWED at implementation** — no node exists today |
| **V-BOUNDARY** | at `T = c` (the corrected/corrector adjacency) exactly ONE edge returns — the corrector | boundary test; both interval ends normalised through the SAME helper (0032 `as_utc`), per 0030 V-NORM-TOTAL (F5) | **OWED at implementation** — no node exists today |
| **V-NO-EXISTENCE-SIGNAL** (R4-1; positive control added v12, its RANGE corrected the same hour) | a principal without scope cannot tell a HIDDEN successor from a MISSING one — **AND a principal WITH scope is NEVER told `HEAD` about the same state**. Both halves, or the invariant is satisfiable by hiding everything from everyone | the excluded principal's two results must be **equal as WHOLE OBJECTS**, not equal on a flag — asserted over every retired-hidden state (`corrected`, `superseded`, `absorbed_duplicate`), so a field added later reintroduces the signal by FAILING rather than passing; **and for the holder the SAME state must be NOT-`HEAD` — `SUPERSEDED` when the successor is in the holder's view, `SUCCESSOR_UNAVAILABLE` when it is not. The control is the ABSENCE OF `HEAD`, never one named value:** a control fixed to a single disposition is itself over-fitted to one state, which is the defect the control exists to catch. Asserted for the hidden QUERIED IDENTIFIER as well as the hidden successor (R5-1). **Mutants: (1) v9's `omitted`/`causes` result; (2) the hand set `{"corrected"}` alone; (3) the v11 lookup, which reads the queried edge UNFILTERED; (4) COLLAPSE-EVERYTHING — one disposition for both principals, which passes the equality half and must fail this control — **and, with NEVER-HEAD phrased over STATES, fails that too; it would have passed NEVER-HEAD vacuously under the result-phrasing v11 used, which is precisely why the phrasing was corrected** | **CHECKED** `tests/test_0028_successor_lookup.py::test_the_model_holds_the_observation_table_and_both_invariants`; `::test_v9_typed_result_reintroduces_the_existence_signal`; `::test_the_hand_set_corrected_alone_lies_to_the_principal_on_two_reachable_states` |
| **V-NEVER-HEAD** (R4-1 as the **WITHDRAWN** name `V-UNAVAILABLE-NEVER-HEAD`; RENAMED and PHRASED OVER STATES at v12) | **the forward-missing state and every retired-hidden state are NOT HEADS, for EITHER principal, at any `T`** — and `SUCCESSOR_UNAVAILABLE` therefore resolves to `INDETERMINATE`, never to current/head | the head predicate is `HEAD`-only, and the assertion ranges over the STATES, not over results that happen to be `SUCCESSOR_UNAVAILABLE`. **The difference is load-bearing: phrased over RESULTS, a collapse-to-`HEAD` implementation produces no `SUCCESSOR_UNAVAILABLE` at all and the invariant passes VACUOUSLY; phrased over STATES it trips on its own.** *(v11 stated it over results while its own mutant list assumed states — the mutants were right and the statement was weaker than them. The OLD NAME said `UNAVAILABLE`, i.e. a RESULT, and a name narrower than its check pulls the check down to meet it; renamed rather than annotated for exactly that reason.)* **Mutants: a head predicate that ignores the integrity signal; collapsing the hidden case into `HEAD`; COLLAPSE-EVERYTHING** | **CHECKED** `::test_the_model_holds_the_observation_table_and_both_invariants`; `::test_a_head_predicate_that_ignores_the_integrity_signal_is_refused`; `::test_collapsing_the_hidden_case_into_head_trades_a_leak_for_a_lie` |
| **V-SUCCESSOR-REGISTRY-TOTAL** (R4-1) | "asserts supersession" is defined by `NAMES_A_SUCCESSOR`, total over `DISPOSITIONED_REASONS` in BOTH directions, refusing at import | a reason missing from the registry, and a registry entry naming no dispositioned reason, must each fail the build — the `AS_OF_DISPOSITION` gate's shape. **Mutant: a string admitted into the disposition vocabulary** | **CHECKED** `::test_the_registry_must_be_total_over_the_dispositioned_reasons`; `::test_the_vocabulary_refuses_a_string` |
| **V-SCOPE-DIFFERENTIAL** (R3-3) | `facts_valid_at` reproduces recall's principal-dependent decision | two principals, ONE store, a record visible to only one, the same `(subject, relation, T)`: the holder sees it at every T its interval covers, the other at none. **Mutant: drop `principal`/`policy` from the signature** — both principals get one answer, which is v8's declared shape | **OWED — the node does NOT exist.** `test_two_principals_one_store_one_record` is research's DESIGN (`proposals/0028-round4-principal-differential-DESIGN.md`), executable at implementation because `facts_valid_at` is unwritten (§9). *v10 cited it in the node column, where it read as a check that runs.* |

### 6a. Acceptance measurement — REQUIRED, FINITE

**Every row of §6 carries an explicit `CHECKED` or `OWED` marker in its node column, and NO count is written in this prose.** The accounting is a property of the table: a reader counts the markers, and a row added without one is visible as a gap rather than hidden behind a number. **CHECKED** means a named runner exists — a test node, or a check script with its covered fraction stated. **OWED** means the evidence is due at implementation and says so, including where the node named is a design's rather than an existing test's. *(R4 minor, then R5's accounting correction. v10 said "every invariant carries a named executable check" — false of sixteen rows, and the fifteen bare `—` cells made the claim unfalsifiable from the table itself. **v11 then over-corrected: it stated NINETEEN/SIX/THIRTEEN in prose immediately above the paragraph that says no count is stated here deliberately — two accounting rules in one section, which R5 returned.** The markers are kept and the prose numbers are dropped: they were the thing that went stale three times before (v2's "ten" over a table of eleven; R2-5's correction to thirteen; v4's "ten" two paragraphs below the table it miscounted). Derived by checking every cited node for a `def` in `tests/`, never by reading the column. The count is of §6's table ONLY; §6a re-lists four of these, which is why a row-start sweep of the file returns 23.)*, and **no
measurement depends on model behaviour** — every check is deterministic over
constructed store state.

*No count is stated here, deliberately. v2 said "ten invariants" over a table
of eleven; external round 1 (R2-5) corrected it to thirteen; v4 still read "Ten
invariants above… not true of all ten" **two paragraphs below the table it
miscounts**, and internal review F4 (2026-09-06) found it there. v5 adds three
more, so any number written in prose is one edit from being wrong again. The
count is a property of the table, not of this sentence — the reviewer checklist
counts the rows, which is the derived-basis rule this programme applies
everywhere else: a hand-maintained figure standing in for a derivable one fails
silently and reads as rigour.*

*(v9 added the `node` column: R3-2 and R3-3's new rows carry test node ids as a
fourth cell, and under the old three-column header GitHub markdown would have
DROPPED them — the identical defect dev's B3 found in 0038 four hours earlier,
reproduced by the same author in a different spec. The existing rows carry an em
dash rather than a fabricated node.)*

**FINITE-TODAY is not true of every row, and saying so is part of the
measurement** (internal review F1/F6):

| check | constructible today? |
|---|---|
| V-BOUND, V-EMPTY, V-TOTAL, V-MUTANT, V-NONE, V-HEAD, V-NO-FUTURE | **yes** |
| V-COMPAT | **yes, if specified structurally** — assert `as_of=None` takes the pre-existing path unchanged (the filter never invoked; the parameter keyword-only, default None) plus the existing recall suite, which already IS the differential. A byte-diff harness is unnecessary |
| V-NO-UPGRADE, V-NEVER-BYPASS, V-CROSS | **YES, as of 2026-09-06.** They were unrunnable while `classify_as_of` was spec pseudocode; it now ships (`src/veracium/asof/classify.py`), and `AS_OF_DISPOSITION` ships as DATA (`schema.py:471`) with an import-time key-equality gate — so V-CROSS compares two artifacts. This row is the reason v2's external review was HELD; the hold is lifted |
| **V-ONE-CLOCK** | **YES, and the seam is VERIFIED to exist** (internal review F3, 2026-09-06). It needs an INJECTED clock, not a fast machine: with a clock whose successive reads straddle a sleeper's `valid_from`, a one-read implementation refuses (`T > now` at that reading) while a two-read one passes step 0 and then finds the edge `valid_now`. A wall-clock test cannot make that race deterministic; an injected clock makes it certain, and the store **already takes one** (`SqliteStore(…, clock=None)`, `sqlite.py:91`, read through `_now()`, `:1707`; 0029's txn allocator already takes one clock read per scope). *v4 specified the check as "`utcnow()` called once per query path" — **unimplementable as written**, because there is no `utcnow()` to count: `asof/classify.py`, `asof/adapter.py` and `store/current_state.py` read no clock at all, and `classify_as_of` takes `now` as a PARAMETER. Research flagged this as its least-sure item without verifying it; the answer is POSITIVE — the check is real, and it counts invocations of the injected callable.* **v5's row was STILL unimplementable, for a second and different reason (internal review F1): it said the value is threaded to `valid_now` — but `Edge.valid_now` is a `@property` with NO PARAMETER (`schema.py:568`) whose body reads `utcnow()` (`schema.py:25`), the PROCESS WALL CLOCK, unreachable from the store's injected clock. Nothing can be threaded to it, a recording clock counts zero calls from it, and the check would have PASSED while the two-read sleeper race it forbids was happening** — a check that cannot see the read it forbids, written into the row that was itself the fix for an unimplementable check. v6 removes the as-of branch's dependence on it entirely rather than making 0032's predicate clock-aware, which would change an accepted spec's surface. The mutants must FAIL, or the check is decorative |
| **V-ONE-SNAPSHOT** | **yes.** Both journal modes are constructible against the shipped `current_state` window (`sqlite.py:300-312`), and 0030's V-WINDOW already asserts the underlying property in both — this row asserts that the RESOLUTION opens one, not that the store can |
| **V-NORM-FIRST** | **yes**, and it is a two-outcome test rather than a failure test: a naive future `T` must produce `ValueError`, not `FutureAsOfRefused`. Asserting only "it raised" passes the mutant |
| **V-BOUNDARY** | **yes**, as data at both ends of the half-open interval: `T = valid_from` (INSIDE), `T = invalidated_at` (OUTSIDE), and `invalidated_at IS NULL` at any `T ≥ valid_from` (INSIDE). The null case is the one v2's expression got wrong — `valid_from ≤ T < invalidated_at` is undefined when the upper bound is null — and a suite over closed intervals only would never have reached it |

**Acceptance required 0030's implementation, not merely its acceptance** —
stated here rather than discovered at acceptance, and **now satisfied**
(`ccaa9cc`, 2026-09-06). All of §6 is finite.

## 7. Failure modes and reversibility

**THE OUTER WINDOW CAN COST A CONCURRENT WRITE, and v9 states it because the
window is this spec's own introduction.** Under the default journal mode a
resolution longer than a writer's `busy_timeout` makes that writer's commit fail
with the store's **WRAPPED** refusal naming the COMMIT site
(`V-LOCK-REFUSAL-FORM`) **and lose its write** (§5, measured; the bare form was
v12's and is WITHDRAWN — 0029 v11). The
snapshot guarantee §4b-o requires is therefore bought with a real, caller-visible
cost, and the honest statement is that a host running long resolutions against a
write-heavy store should either raise `busy_timeout`, enable WAL, or bound N. *v8
said only that a writer is "refused for the whole resolution" — round-3
correction 7 called that a determinism SQLite does not provide, and the run shows
it is neither outcome's name: the writer waits and succeeds, or it fails and
loses the write.*

- **Reversible.** Read-only, additive API. Removing `as_of` restores today's
  behaviour exactly; no stored byte differs.
- **The failure that matters** is a wrong *inclusion*: returning as grounded
  something 0030 fenced or excluded. V-NO-UPGRADE and V-NEVER-BYPASS are aimed
  squarely at it, and both fail closed.
- **A wrong exclusion** (an over-conservative `INDETERMINATE`) is a degraded
  answer, never an unsafe one. Where the two trade off, this spec takes
  exclusion.

## 8. Claims and limits

**Claimed:** the system can answer *what did we hold to be true at T*, with
every result carrying why it is the T-answer, and with fenced and excluded
records unreachable at every T.

**NOT claimed:** what was *known* at T (v3); that history is complete (the
store retains what it retained); that a corrected value's replacement was true
at T (§4b-i proves it cannot be); or any dedup guarantee across reinforcement
duplicates (§4b-iv).

## 9. Brief for the external reviewer

**What this spec CANNOT yet evidence.** `facts_valid_at`, `read_window` and
`edges_superseding` are specified and **unwritten** — `src/veracium` ships only
`asof/` (`classify.py`, `adapter.py`, `carrier.py`). The absence proof R3-1's
fix implies — that no as-of path reaches `Edge.valid_now` or `Edge.assertable` —
is therefore **owed at implementation, not offered here.** **Round 7 carries
what round 6 carried, unchanged — no new artifact was requested and none is
offered as if it were:** the behavioural form over `classify_as_of` as shipped
(a recording clock, zero `valid_now`/`assertable` reached from it), the
static tree from it and from the store reads §5.1 names, **with the method
stated** — what was followed and what was not — and **the successor-lookup
model** (`specs/evidence/0028/check_successor_lookup.py`,
`tests/test_0028_successor_lookup.py`), which runs the R4-1, R5-1 and R5-2 design over **the store states `EXPECTED`
names — the program prints the count on every run, and no carrier states one**,
on the shipped store through public writes. *A proof of absence over
unwritten code is exactly the claim R3-1 caught, and this spec will not make a
second one.*

**The seams to attack hardest**, in order: **§4a's algorithm**, because R3-1
found the old two-clock design surviving there after two folds had removed it
elsewhere, and one reader agreeing with it is not evidence; **the NON-REVEALING
successor design** (§5.1), because R4-1 found that v9's typed result — the type
we added to *fix* R3-2 — was itself an existence signal across the scope
boundary, so the question is whether v11's answer is total and whether it leaks
anywhere we have not looked. Four things to press: **whole-object equality** of
the hidden and the missing results (not equality on a flag — a field added later
must fail rather than pass); the **three-value space's totality** over store
states we have not built; the **registry** deciding what "asserts supersession"
means, which was a hand-written set naming one reason until it lied to a
principal on two reachable states; and the **un-retired contrast**, where `HEAD`
is correct for the excluded principal and looks like the case where it is not.
And **§5's
concurrency rows**, which are written from a two-connection run rather than from
the locking model — if the run's rule does not generalise beyond the two window
lengths measured, we would rather hear it than infer it.

**A THIRD seam, and round 6 is the reason it is named: DIFF OUR PROSE AGAINST
OUR OWN CHECKS.** Both blocking findings last round were one shape — a claim
that no check could see:

- **R6-1** — the reviewer checklist carried the corrected two-class rule while
  **§4b's normative definition still carried the old one-rule form.** We fixed
  the summary and left the definition it summarises.
- **R6-2** — the sealed window test asserted the **wrapped** commit-time
  refusal while §4b-o, §5 and §7 asserted the **bare** one. **The package
  carried both halves of the contradiction and every check passed.**

**No check in this repository compares prose to prose, or prose to a test.**
Every gate we have compares an artifact to an artifact. So the two places this
spec is most likely still wrong are the two places only a reader can look:
**diff §4b's definition against the reviewer checklist**, and **diff §4b-o, §5
and §7 against `tests/test_0028_window_transcript.py`'s assertions.** We would
rather you found a third instance than that we claimed there is none — **we
have now missed this shape twice in consecutive rounds, and both times the
executable evidence was correct and the sentence describing it was not.**

## 10. Open questions

1. ~~The 0027 lane asymmetry~~ — **WITHDRAWN as a question**: the asymmetry
   does not exist (§4c, internal review F3), so the lazy-re-embed option it
   raised is moot.
2. **N = 3.** Justified on integrity grounds (§4b-i). Is a third-order
   correction chain a smell worth surfacing, or a legitimate shape we would be
   refusing?
3. **The scan-backed accessor.** §5.1 states the scan-backed truth and its
   bound — **one scan of the user's edges, plus (edge count × N) in-memory
   comparisons** — rather than the indexed property the store cannot provide.
   *This question and §5.1 have now disagreed TWICE, in opposite directions.*
   *In v4 the clause claimed "no scan" while this question called the same
   thing "the scan-backed accessor" (internal review F1). In v6 the fix ran the
   other way: §5.1 was corrected to the one-read model and **this question kept
   quoting the superseded per-hop bound**, so the pair disagreed again with the
   error on the opposite side. **The lesson is the pair, not the sentence** — a
   clause and the open question that discusses it are one carrier, and every
   edit to either must be checked against the other. They agree in v7.* Whether
   an index is warranted is a substrate decision — a column, a schema version
   and a migration — deliberately off this read-only spec's critical path,
   since §7 says no stored byte differs.
4. **The generator's home.** §4b requires the table's generator at
   `specs/evidence/0028/` for acceptance (F8). Confirm that is where it
   belongs, versus a test fixture — the difference matters because only a tree
   artifact makes "generated" checkable by someone who is not its author.
5. ~~Does MCP's `recall` tool gain `as_of` in v2?~~ — **CLOSED: NO. MCP is
   UNCHANGED in v2, stated explicitly** (round-3 R3-4: this could not remain
   open in an implementable API spec — it decides the callable surface, the
   serialization contract, and how far `FutureAsOfRefused` reaches).
   **As-of is a library surface in v2.** The reason is 0031 §4d's, applied to a
   time axis: a model that can ask *what did you believe at T* can walk T
   backwards over content the present withholds — corrected values, disputed
   claims, retired records — and reach by history what the current gate denies
   it now. That is a **larger** model-reachable surface than the counters 0031
   strips, not a smaller one, and v2 does not open it on a spec that has had no
   external round on the question. A host wanting as-of through a tool builds
   it deliberately, against its own harness, with `FutureAsOfRefused`
   serialized per §2c's tool-layer clause — which is written and waiting.
   *Consistent with 0038's decision the same day to strip `instructions_dropped`
   from the MCP result: the tool surface is decided explicitly and narrowly,
   both times, rather than inherited from what the library happens to return.*

## Reviewer checklist

- [ ] every registry reason appears in §4b, plus the `None` and unknown cases
- [ ] no §4b row upgrades a 0030 verdict
- [ ] no termination condition inside the pointer walk references T
- [ ] every `INDETERMINATE` **arising from a condition observable WITHIN the
      caller's view** (branching; an unclassifiable reason) carries a cause and
      is disclosed — **and `SUCCESSOR_UNAVAILABLE` carries NONE, by design**
      (R5-3: v11's checklist demanded a cause for *every* indeterminate, which
      no implementation can satisfy alongside §3, §4b-i, §5.1 and
      V-NO-EXISTENCE-SIGNAL — a distinguishable cause there IS the existence
      signal. Two classes, one rule each.)
- [ ] the spec adds no field, mutates nothing, and cannot cause a write
- [ ] `known_as_of` appears nowhere as a v2 behaviour
- [ ] **COUNT THE ROWS of §6 and check every one has a check** — do not trust a
      number written in prose anywhere in this document (v2 said ten over
      eleven; round 1 corrected to thirteen; v4 still said ten; v5 has more
      again). The table is the basis; a sentence about it is not
- [ ] **every clause naming a performance or serialization property names the
      MECHANISM that yields it** — §5.1's complexity, §4b-o's snapshot,
      V-ONE-CLOCK's clock. A clause asserting an outcome the shipped code does
      not produce is this arc's recurring defect and has now been found in
      three specs
- [ ] **no withdrawn alternative survives as a USE.** Sweep `clamp`: every hit
      must be history (describing why it was withdrawn), never a mechanism the
      text relies on
- [ ] **one outcome per surface**, never two at one surface (0011 R1-4) —
      library RAISES, a tool layer SERIALIZES
- [ ] **anything captioned "generated" is generated by an artifact in the
      tree**, not by a process its author ran once
