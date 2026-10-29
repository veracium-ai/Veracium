# Feature spec: targeted redaction — stored content removed, the record that it existed retained

Spec-Status: accepted
Folds: 0047/0041-replies

> 🧭 **THE TITLE LINE IS FIRST ON PURPOSE — v3.2.** `specs/ALLOCATION.md`
> renders a spec's FIRST LINE as its registry title, and every other spec
> opens `# Feature spec: …` (0027, 0028, 0037, 0038 — checked). This file's
> title had drifted to **line 47** under accumulated banners, so the registry
> rendered whichever banner was on top: at v3 that was
> `> # 0041 v3 — RESPUN FOR THE ROUND-1 RETURN, 2026-09-15` — a review round
> and a date, carrying raw `> #` into a table cell, going stale at every
> respin, and **displacing the 0040/0041 renumber notice from the one surface
> that notice exists to protect: the place people look up a number.**
> **Banners go BELOW the title from here. A banner that outranks the title
> renames the spec.**

> # 0041 v3 — RESPUN FOR THE ROUND-1 RETURN, 2026-09-15
>
> **All seven findings are addressed, and all seven were spec-level.** F1 §2/§2d/§2e
> (the enumeration's own model set was a hand-list — the fourth failure of one
> class in this file); F2 §4e (publication-time validation; the delayed compiler
> undoes a redaction and stamps it current); F3 §4b/4b-ii/4b-iii (the marker
> defined and validated — `TEXT NOT NULL` permits `""`; the episode record; the
> reader inventory, where a sentinel currently reads as `MALFORMED`); F4 §4f (the
> receipt selection rule and the conservative outcome); F5 §4g (the import
> contract); F6 §10.1/§8 (**ruled by the owner: outputs are separate**); F7 §11
> (**the operative contract — everything above §11 is historical discussion**).
>
> **Dev reproduced every executed claim in the verdict at the pin, and the
> enumeration reproduces byte-for-byte in their tree** (`50531999b8caf5f0` /
> `90e1d907ed58560a`, bound by a test node in `specs/evidence/0041/`).
>
> ⚠️ **READ §11 FIRST IF YOU WANT THE CONTRACT.** The four conflicts F7 named
> existed because decisions were recorded where they were taken and the passages
> they invalidated sat elsewhere, still reading true locally. **No paragraph was
> wrong when written**, which is why section-at-a-time review could not see them.

> 🔢 **THIS IS 0041, NOT 0040 — the number changed at the adoption boundary
> (dev's catch, 2026-09-15; research verified it in the registry).**
> **`0040` is SPENT.** `specs/allocation.py` records it consumed by a DIFFERENT
> proposal — *"procedural text at the choke point — the store inferring content
> kind from text shape"* — **withdrawn on Quentin's word of 2026-09-08** ("Q1
> answered NO"), its record kept at
> `proposals/0040-procedural-text-at-the-choke-point-WITHDRAWN.md`. The registry
> is explicit: *"a SPENT number that a tree file also holds is a duplicate and
> the gate refuses it"*, and `allocation.py --next` returns **0041**.
>
> **The collision was not hypothetical — it was already on disk.** Two different
> proposals have been sharing `0040` in this one directory for days: the
> withdrawal record and this candidate. Anyone looking up "0040" could have found
> the withdrawal and concluded that targeted redaction was withdrawn, which is
> precisely the confusion the SPENT list exists to prevent.
>
> **Nothing in D1–D4 changes; only the number does.** Quentin's decisions were
> worded against "0040" and stand unaltered.
>
> ⚠️ **TWO OCCURRENCES OF "0040" BELOW ARE LEFT VERBATIM ON PURPOSE, because they
> are QUOTATIONS and renumbering inside a quote would falsify it:** the header's
> *"Write the 0040 …"* (Quentin's own word) and §2b-ii-bis's quotation of the
> pre-v14.1 schema comment. The tree's own references move at adoption, in dev's
> commit.

*Research-authored candidate, 2026-09-12, on Quentin's word **"Write the 0040
candidate"**. Premises already ruled: **C0 answer 2** (the product owes a
redaction/erase surface), **"keep the split"** (ledger rows cascade, judgments
outlive their subject), **the one-month explanation horizon**, and **the
administrator-history limit** (landed `f4d607a`). The journal decision in §4c is
research's recommendation, approved in principle; the reviewer should attack it
first.*

| | |
|---|---|
| **Author / session** | research (veracium-research), the candidate's author → dev (veracium-61), each adoption at rest and re-read from the file, dated per entry: v15.6 2026-10-13 from `0041-targeted-redaction-v15.6-CANDIDATE.md` (sha16 4f4911244c54c52d; the post-acceptance notice-binding correction, 0041-PA1); v13 2026-09-16 from `0041-targeted-redaction-v4-CANDIDATE.md` (sha16 64437016dfeda101; the file kept its v4 name — the round-6 DECISION reaching the one carrier a machine consumes, held at the round-7 seal when the adopting seat found `Spec-Status` still reading `draft` after an acceptance); v12 2026-09-16 from the same file (sha16 bced72922d8b19aa — the author's own at-rest guard REFUSED the first two candidates, once for this cell having lost v11 and once for citing a fixture digest the tree did not yet hold, both caught before they reached the adopting seat); v11 2026-09-16 from the same file (sha16 ba77ed13be06ed6d — the candidate's first copy at 105d8e7e62e5d485 was HELD at adoption when this cell was found reverted to its v6 state, losing v7–v10, and the author rebased it on the tree); v10 2026-09-16 from the same file (sha16 c276b8674d8255f6); v9 2026-09-16 (fcd801bbbe9595db; landed at 7db9987 and superseded within the hour — its Version cell redded a gate in a clean checkout); v8 2026-09-15 (copied at c3595046d343b1c9 and HELD before commit when the adopting seat read it against its own attestation rule); v7 (never reached this tree); v6 2026-09-15 (41e31dc725c77cd2); v5 2026-09-15 (e7385dd63c02afd6); v3 2026-09-15 from `0041-targeted-redaction-CANDIDATE.md` (1d0c0389bef11a3f); v2.1 2026-09-15 from the same name (eecd5a4db4426058) |
| **Version** | **v16.3 — SEVEN ROWS ADDED AT 0047's IMPLEMENTATION (dev's T10a, 2026-10-19).** §2d-iii-ter's two reply rows join §2d-iii-bis where the enumeration places them: the `replies` table's model, `Reply`, is RULED a carrier (research's T10a Q18, against its write path, `SqliteStore.add_reply`), so its seven text-capable fields are rows 67–73. `Reply.text` and `Reply.request_digest` are **REPLACE**, as §2d-iii-ter rules them; the five identifiers, `target` included, are **PRESERVE** (§11.6.2). The enumeration now reports 93 identities behind 148 paths = 73 carriers + 20 non-carriers. `CorrectionAuthorisation`, which neared the new table on two shared names, is RULED a non-carrier. The rows are APPENDED, so rows 1–66 keep their numbers; §2d-iii-ter's text is kept as written. Prior: **v16.2 — TWO ROWS ADDED AT 0045's IMPLEMENTATION (dev's T9, 2026-10-18).** §2d-iii-bis gains rows 65–66, `Edge.src` and `Edge.attv`, both **PRESERVE**, carrying 0045 §4f's rulings for the grounding axis's two text-capable fields (`Edge.att` is a closed value, a non-carrier). The enumeration now reports 86 terminal identities behind 141 paths = 66 carriers + 20 non-carriers; the rows are APPENDED, so rows 1–64 keep the numbers other carriers cite. Nothing landed is reworded; counts inside round histories are records of their round. Prior: **v16.1 — SENTENCES ADDED AT THE NOTICE STATE MACHINE'S IMPLEMENTATION (dev's T4, `86baf9c`; its stage-2 fix `3e1c6bc`), 2026-10-15.** They state what v16 left unstated and the implementation had to choose, as research's shape read and stage 2 answered it and dev implemented it. Each is marked *v16.1*. Nothing landed is reworded, and `Spec-Status` stays `accepted`. (1) What an export carries: applied notices, and a standing notice only when the file does not carry its target. It carries no pending notice and no standing notice over an id since written locally, and the cost is stated (§11.6.6, §11.6.7; research's B1, a defect measured at `a2dc7b0` and in no release). (2) The table's created rows are weighed before the pending rules. A deleted target's pending notice re-arriving beside its unredacted record is refused, and beside its treated record it is applied (§11.6.6, INV-RR14; finding T4-1, main-only). (3) A pending notice keeps its stored reason until applied. (4) `pending_notices`, the read beside `confirm_notice`. (5) A standing notice's own copy in the unit takes the created rows, and a standing notice over a local write re-arrives as a held target (INV-RR12's “never completed” read as the arrival rule's). To be disclosed to the external reviewer in the R-A package. Prior: **v16 — THE REPLIES AND NOTICE-BINDING FOLD (amendment `0047/0041-replies`, v1.14, sha16 `9d953d81fa6d6d18`).** Its design was ACCEPTED at round 4 of the 0045–0047 package (verdict 2026-10-13; INV-RR1–RR12 and RR14, RR13 withdrawn), and the owner ruled “Accept now, fold next” (2026-10-14). *Annotation (research, 2026-10-15; the sentence before it is kept as written): the bytes round 4 reviewed are the amendment's **v1.13**, sha16 `225ca811fe6d5da4`. The digest this cell names, `9d953d81fa6d6d18`, is a post-verdict re-spin of them, carrying the round-4 verdict's IO-II-2 and a consolidation of the amendment's version narratives; and the label “v1.14” also names an intermediate re-spin, `52d73acfe48b7f8e`. Every normative change from the reviewed bytes to the fold's source, with its cause, and the correspondence from that source to this document, are research's fold-correspondence record (research commit `106ddbff`), which the R-A package carries.* Folded: the L220 annotation; §2d-ii's three new REPLACE carriers and their rows in a new §2d-iii-ter (they join §2d-iii-bis when `replies` exists); §2d-iv's reply write path; §3b's `confirm_notice`; a superseded-for-imported-notices note on §4g's “holds the record” row and on the v15.6 block; and the amendment's current contract as §11.6, the operative section, without its version tags. Not folded: its review briefs, open questions and version history, which stay with its research file and `specs/reviews.py`. Prior: **v15.6 — A NOTICE NEVER REMOVES CONTENT ON AN UNTRUSTED FILE'S WORD, AND A FILE THAT PAIRS A NOTICE WITH ITS RECORD UNREDACTED IS REFUSED. 2026-10-13. A post-acceptance correction (internal finding `0041-PA1`); no design-level rule outside §4g changes, and `Spec-Status` stays `accepted`.** Dev reproduced it at `1fd3e52`: §4g's first row ("holds the record: apply") applied in BOTH import modes to any held target id, so a DEFAULT-mode (untrusted) file carrying only a header and one notice redacted the user's own fact sharing its id. Research measured the class: a standing notice also refused the user's own later write of the id, listed it in `redacted_targets()`, and redacted a later arrival of that id from any store; and, once the write was admitted, a poisoned store's own export carried the notice onto the user's record. **The defect is on main from `8ea59e7` (2026-09-20) and is in no release** (`git tag --contains 8ea59e7` is empty), so no patch release; the fix lands before the next release. The owner ruled the route (2026-10-13, first-hand): fail closed, all arms, the leftover standing rows included; a file pairing a notice with its record unredacted refuses the whole import in both modes; and a standing notice completes only by attesting an arrival that already shows the redaction. **§4g's v15.6 block states the rule; the rows above it are kept as the v15.5 record.** It is a SUBSET of the round-4 0041 amendment (`0047/0041-replies`), which adds the user's confirmation of a pending notice. Prior: **v15.5 — THE IMPLEMENTATION ACCEPTED. 2026-10-06.** Research, as the specification's author, after the round-14 verdict (*"Verdict: ACCEPTED. The implementation at this pin closes both round-13 findings and the shared-carrier observation. No new blocking or nonblocking finding is raised."*), banked as `0041-round14-verdict-verbatim.md`, reviewed at pin `8a54a87d7b0f22b1e2ca2bcc5359568e4f357823` against v15.4. **No frozen decision changes, no contract sentence changes, and `Spec-Status` stays `accepted`**: this version records the acceptance and adds nothing to the contract. *"The design accepted at round 8 remains frozen on INV-1–INV-12, the 64-carrier per-candidate treatment map, and §4h’s transition rules."* The record is §"Implementation acceptance", before the review closure. **Prior cell follows.** **v15.4 — THE ROUND-13 CORRECTIONS, STATED AS CONTRACT. 2026-10-05.** Research, as the specification's author, after the round-13 verdict (*"RETURN FOR IMPLEMENTATION CORRECTION. The design accepted at round 8 remains accepted"*; the 0014 §2c rider *"is accepted. Its implementation is not yet accepted."*), banked as `0041-round13-verdict-verbatim.md`. **No frozen decision changes and `Spec-Status` stays `accepted`.** It sharpens v15.3's held-output bullet to the rider's conditions as the reviewer restated them (the notice is for the RESOLVED held output, R13-01; each named field's value IS the marker, the whole value, R13-02), and names the supersession-refusal row as a second shared side carrier (N13-01). **Prior cell follows.** **v15.3 — THE ROUND-12 CORRECTIONS, STATED AS CONTRACT. 2026-10-05.** Research, as the specification's author, after the round-12 verdict (*"RETURN FOR IMPLEMENTATION CORRECTION. The design accepted at round 8 remains accepted."*), banked as `0041-round12-verdict-verbatim.md`. **No frozen decision changes and `Spec-Status` stays `accepted`.** It states, in this specification, the rule accepted 0014 §2c now carries as a rider (approved by the owner 2026-10-05, for the 0041 reviewer's cross-spec sign-off): a redaction notice reaches a consolidation output the destination already holds (R12-01), and binds to the held output's id (N12-01). It also names a shared side carrier already at the marker as part of the covered surface (N12-02). **Prior cell follows.** **v15.2 — THE ROUND-11 CORRECTIONS, STATED AS CONTRACT. 2026-10-04.** Research, as the specification's author, after the round-11 verdict (*"RETURN FOR IMPLEMENTATION CORRECTION. The design accepted at round 8 remains accepted"*), banked as `0041-round11-verdict-verbatim.md`. **No frozen decision changes and `Spec-Status` stays `accepted`.** It annotates v15.1 where the reviewer measured the text against the implementation: (1) N11-01, the held-differs parenthesis stated a narrower rule than was ruled and built, and is aligned to the rule; (2) Q1, the arrival guarantee is the permitted treated-or-absent shape, not byte equality; (3) the R9-01 cost was measured uncontended only; (4) a notice's field domain is one definition for writer and reader, with a closed bookkeeping set (R11-01); (5) "nothing to redact" is judged over the whole covered surface (R11-02); (6) one source identity and body for native and witnessed records, and the bound-target rule (R11-03). **Prior cell follows.** **v15.1 — THE ROUND-10 CORRECTIONS, STATED AS CONTRACT. 2026-10-03.** Research, as the specification's author, after the round-10 verdict (*"RETURN FOR IMPLEMENTATION CORRECTION. The design accepted at round 8 remains accepted."*), banked as `0041-round10-verdict-verbatim.md`. **No frozen decision changes and `Spec-Status` stays `accepted`.** It annotates v15's §4g block and §11.2 where round 10 showed them incomplete: (1) the notice identity is held as STRUCTURED source fields and compared by exact equality, never as an encoded string (R10-03); (2) a completed attestation whose record is absent treats an arriving record that carries its notice, with no new event; without the notice the arrival still refuses (R10-02); (3) one held-differs rule for every record kind the importer admits, the outcome chain included (R10-01); (4) provenance is read from facts only the import path writes, and `imported_notice` is written only there: the public `redact` refuses it, ruled by the owner 2026-10-03 (R10-04); (5) v15's body list named one key too many. **Prior cell follows.** **v15 — THE ROUND-9 CORRECTIONS, STATED AS CONTRACT. 2026-10-02.** Research, as the specification's author, after the round-9 verdict (*"RETURN FOR IMPLEMENTATION CORRECTION. The design accepted at round 8 remains accepted."*), banked as `0041-round9-verdict-verbatim.md`. **No frozen decision changes and `Spec-Status` stays `accepted`.** It adds text where round 10's corrections showed the contract was silent or stale: (1) the notice identity binds the DESTINATION user and the TYPED target, and the FOREIGN BODY is immutable and compared on every repeat (§4g, R9-04); (2) the two-fact receipt: original-receipt fields are nullable and source-supplied, application fields are local (§4b-ii, R9-05); (3) the marker-kind admission and the notice field domain (§4g, R9-06/R9-08); (4) the readers and derivations round 10's sweeps found, under one rule, P-READ (§4b-iii); (5) the LIFT vocabulary, ruled by the owner 2026-10-02 (§11.2); (6) the AMENDMENT TO ACCEPTED 0022 §4a that treating stored revocation prose always required and v12 never recorded (§11.4); (7) the consequences and limits round 10 measured (§8); (8) §2d-ii's stale "NO vocabulary" clause, annotated. **"v15" is this SPECIFICATION's version; the store's schema version 15 is a different number.** **Prior cell follows.** **v14 — ACCEPTED, AND THE LEDGER THAT MAKES THE WORD MEAN SOMETHING. 2026-09-17.** 🔴 **`Spec-Status:` moves `accepted-with-amendments` → `accepted`, on the authority of the round-8 verdict** (`0041-round8-verdict-verbatim.md`): *"0041 round 8, specification v13: ACCEPTED."* **THAT VALUE IS WHAT AUTHORISES IMPLEMENTATION** — `check_spec_reference.py`'s `IMPLEMENTABLE = ("accepted",)` — and it is deliberately the LAST thing this fold did. ⚠️ **THE FLIP IS GATED ON THE CLOSURE LEDGER, NOT ON THE VERDICT.** `check_spec_reference.py` refuses an `accepted` spec with no `## Review closure` section, but only on a commit touching guarded source — which an acceptance fold never is — so the gate that should catch a missing ledger is exactly the gate this commit cannot trip. **Two accepted specs sat with the template's placeholder for two days on precisely that hole.** So the ledger went in FIRST and the flip last: **8 external rounds, 34 findings, 34 closure rows**, generated into §Review closure from `specs/reviews.py` and `specs/closure_findings.py`. ✅ **15 of the 34 rows cite a pytest node or the mutant campaign; 19 cite the fold commit**, because for those findings the fold WAS this document's text and P4 prefers an openable commit to a grep any file containing the new wording would satisfy — the packaged-tree cost of those 19 is pinned and named, not absorbed. 🔴 **ROUND 8's TWO NONBLOCKING FOLLOW-UPS ARE BOTH CLOSED HERE.** The marker check now decodes JSON before looking (it had searched raw text for a marker whose NULs JSON escapes, so it was true of every export ever written) and §11.4-bis's five stale figures are not merely corrected but **DERIVED** — a test walks the campaign's own case table and the fixture's manifest and fails if the prose disagrees, because correcting five counts by hand fixes today and guarantees nothing about the next case added. ⚠️ **ACCEPTANCE FREEZES INV-1–INV-12, THE 64-CARRIER TREATMENT MAP AND §4h'S TRANSITION RULES. IT APPROVES THE DESIGN; THE FEATURE REMAINS UNIMPLEMENTED**, and the reviewer carries three obligations into that work: reconstructed receipts where no original exists, positive controls for the EIGHT strict xfails that still lack one, and the `"redacted"` disposition. **Prior: v13 — THE DECISION RECORDED WHERE A MACHINE CAN READ IT. 2026-09-16.** 🔴 **`Spec-Status:` moves `draft` → `accepted-with-amendments`, on the authority of the round-6 verdict** (`0041-round6-verdict-verbatim.md`, body sha16 `abf9f6439dde1d0d`). **v12 folded the amendments into the TEXT and left the one line whose entire job is to say what state the spec is in** — so the canonical carrier said `draft` while the verdict in the package's own `prior-rounds/` said accepted. **PROCESS §4b: the `Spec-Status:` line *"is the CANONICAL state; the header table carries narrative only, because two sources drift."*** ✅ **And the value is load-bearing in exactly the way this round needs: `IMPLEMENTABLE = ("accepted",)` in `check_spec_reference.py`, so `accepted-with-amendments` is a recognised state that DOES NOT AUTHORISE IMPLEMENTATION.** The qualifier both seats have been carrying in prose — *accepted with amendments, not yet implementable* — is enforced by the machine-readable value, and while the line read `draft` the machine knew nothing of the decision at all. ⚠️ **A GAP IN BOTH SEATS' CHECKS, and the reason it survived: the adoption check asserts there is EXACTLY ONE `Spec-Status:` line and never reads its VALUE; `at_rest.sh` checked paths, digests and the Author cell. Presence was checked, content was not** — the same class as every other defect this round. Both checks now compare the value against the banked verdict. **Prior: v12 — ROUND 6 ACCEPTED WITH AMENDMENTS; RESEARCH'S HALF, WITH THE OWNER'S D1 RULING FOLDED. 2026-09-16.** ⚠️ **THE VERDICT DOES NOT AUTHORISE IMPLEMENTATION and says so in its first line.** **ARCHITECTURE FROZEN: INV-1..INV-12, the carrier treatment map, §4h's transition rules. Round 5's absence finding is CLOSED and D1's requirement for future source-revocation writes is RECORDED AS RESTORED.** 🔴 **FINDING 3 — THE SOURCE-REVOCATION VOCABULARY IS FINALISED, NOT PROPOSED.** Four values close the field for FUTURE writes, refusing at the write path and at every import boundary: `subject_request` (the subject asked) · `legal_obligation` (a legal order or statutory duty compelled it) · `erroneous_capture` (the source should never have been ingested) · **`policy` — the OPERATOR'S OWN standing policy required it** (retention expiry, a scope reduction, a source class withdrawn): operator-initiated, no external compulsion, no subject request. 🔴 **`policy` IS NOT A RESIDUAL "other": a revocation fitting none of the four is REFUSED, not filed under it** — §2d-iv's own rule turned on the set this spec adds. ✅ **RULED 2026-09-16: the owner RETAINED D1 and FINALISED THESE FOUR**, from three options with the reviewer's recommendation named as the reviewer's. **The vocabulary is AUTHORISED.** The four were written before the ruling and the ruling named the same four — convergence, recorded as such rather than treated as licence. **And the older summaries that implied permanent free text are MARKED HISTORICAL rather than deleted** — §2's column row now says it records what the field carried THEN, and §11.2's executed-state column says it describes what the field DOES TODAY and is superseded as a CONTRACT by the column beside it. **v10 read the absence of a vocabulary as the absence of a requirement; the fix is to date the observation, not to remove it.** **Also: §11.4-bis's frozen-record citation named `test_0041_treatment_matrix.py` and the `def` lives in `test_0041_transition_table.py:488` — corrected, verified against the tree.** **FINDINGS 1 AND 2 ARE THE SECOND SEAT'S** (transition tests that build their fixtures through ordinary writers; a fixture-checker negative control that passes against an always-succeeding stub). **CARRIED FORWARD as implementation-verification obligations, not reopening anything: reconstructed receipts where no original exists; positive AND negative controls for every strict xfail; `"redacted"` receiving the required `"drop"` disposition.** **Prior: v11 — RESPUN FOR THE ROUND-5 RETURN, 2026-09-16. FINDINGS 1 AND 2 (the spec text); FINDING 3 IS THE SECOND SEAT'S.** 🔴 **FINDING 1: ROW 49 STILL CHANGED AN ACTIVE EPISODE'S DISPOSITION — a violation of §4h, THIS SPEC'S OWN RULE, in the version that introduced §4h.** v7 fixed one direction (`NULL` un-retires) and broke the other: a two-case rule must put `None` on one side, and it put it on REPLACE, so `retired_reason=None, active=True` became `"redacted", active=False`. **Second round running that rows 30/49 are the finding.** **THE COROLLARY, now in §4h: REDACTION ACTS ON CONTENT; ABSENCE IS NOT CONTENT. Every carrier rule is THREE cases — absent · recognised value · existing prose.** Rows 30/49 and §11.2 are rewritten on it. 🔴 **AND `tests/test_0041_treatment_matrix.py:93` HAD ASSERTED THE CORRECT RULE ALL ALONG** (*"the treatment touches content, never absence"*) — **the specification and its own evidence disagreed and the EVIDENCE WAS RIGHT**; the test stayed green because it tests the product, not this document. 🔴 **FINDING 2: §11.2 AMENDED D1 WITHOUT SAYING SO.** D1 names `source_revocations.reason` as needing a closed vocabulary; v10 treated it as free text forever because it has none TODAY. **Now TWO RULES AT TWO TIMES: the field CLOSES for future writes (per D1), and prose ALREADY STORED is replaced at redaction.** Removing historical prose does not constrain future writes. **The vocabulary's members are a proposal; the alternative — an explicit owner decision changing D1 — is the owner's and is being put to him separately. This text does not assume D1 moves.** 🔴 **THE TWO FINDINGS ARE ONE MISTAKE MADE TWICE: A CURRENT STATE READ AS A PERMANENT RULE.** §11.2 was built on *"the EXECUTED state"* — the right instrument for describing what IS and the wrong one for setting what OUGHT. **A CONTRACT IS NOT A CENSUS.** 🔴 **FINDING 3 IS THE SECOND SEAT'S AND ITS RESULT CHANGES THIS DOCUMENT: §11.4-bis now states WHAT MAKES A STRICT XFAIL TRUSTWORTHY.** Three of eleven were VACUOUS — passing against a no-op `redact`, against a helper returning an empty list, and against a test that never called redaction. **Two independent sweeps (AST over all 38 nodes; all 11 xfails under `--runxfail`) returned the reviewer's three and NO FOURTH.** 🔴 **And the POSITIVE control found what no negative control can: the after-attestation test asserted a write would be refused, but that write SUCCEEDS today, so it would have xfailed through ANY implementation — it could never flip, so it could never announce the landing it existed to announce.** **Every strict xfail now owes BOTH controls: a wrong implementation it refuses AND an honest one under which it passes.** **Row 49 also gains the amplification the verdict did not name: the flip reaches `assertable`, the shared predicate text consumers call — the damage was never confined to the retirement axis.** **CLOSED by the reviewer: the round-4 INV-12 finding.** **Prior: v10 — THE VERSION CELL REDDED A GATE IT WAS DESCRIBING. 2026-09-16.** 🔴 **v9 LANDED AT `7db9987` AND CI WENT RED ON FIVE LANES WITH ONE CAUSE: this cell's own prose.** `test_no_spec_names_a_module_or_script_that_does_not_exist` reads any backticked bare Python filename as a citation, and the cell contained one **as a SAMPLE while explaining that very gate**. ⚠️ **BOTH SEATS' PRE-FLIGHT CHECKS PASSED IT, AND FOR THE SAME REASON: the gate resolves names by walking the working tree, which here contains a `.venv`.** Locally it walks **5,498** basenames; the repo tracks **309**. **The acceptance set is 18× larger than CI's** — so a local pass predicts almost nothing. Measured over every spec: of **203** bare Python-filename citations, exactly **one** resolved only through `.venv`, and it was this one. **Prior: v9 — INV-11 RE-KEYED EVERYWHERE, 2026-09-15.** 🔴 **THE SECOND SEAT READ THE ADOPTED COPY AGAINST ITS OWN ATTESTATION RULE AND FOUND THE RULE CONTRADICTED THREE SECTIONS LATER.** v7 changed INV-11 to key on ATTESTED redaction rather than on the marker bytes **and did not sweep the statements that depended on it.** The second seat found ONE; **the sweep found FOUR, and the worst was not the one reported**: 🔴 **INV-11's CANONICAL STATEMENT IN THE INVARIANT TABLE still read *"an ordinary write to a marker-holding field is refused"*** — a reviewer reading the normative table met the superseded rule as the definition. Also re-keyed: §4b-ii's `repopulation` row (the reported one), the §4b `reservation` cell's restatement, and the write-path row. **All four now key on the RECORD: an ordinary write to an ATTESTED-redacted field is refused; a write to an UNATTESTED marker SUCCEEDS** — which is what the second seat's transition table already asserts green. **Also: a cited test node wrapped across a line break inside its backticks** (§11.4-bis), which no checker can read and which is exactly what produced three false violations in research's own regex; every backticked node now sits on one line, verified by derivation rather than by eye. **Prior: v8 — THE OWNER'S LAST 0041 DECISION, FOLDED. 2026-09-15.** 🔴 **RULED: the pre-existing-marker migration report is ADVISORY, NOT BLOCKING** — the last decision this spec held for the owner, and v7 had already withdrawn the three options v6 offered him as wrong. **The §4b cell now states the consequence rather than the preference: a store can be upgraded with unattested marker rows in it and nothing stops the operator.** **Also: the cell's bare pointer to the research tree's open-items register is REMOVED.** It resolved beside the candidate in the research tree and **not from `specs/`, where the adopted copy lives** — a spec citing a file absent from its own repo is a dangling citation. ⚠️ **And the reason it had to be found by reading rather than by a gate: `test_no_spec_names_a_module_or_script_that_does_not_exist` matches Python filenames ONLY — a backticked specs-relative path ending in .py, or a bare module filename; **no gate checks a backticked .md citation at all.** 🔴 **v10: that sentence ORIGINALLY SPELLED THE PATTERN WITH A BACKTICKED SAMPLE FILENAME, AND THE GATE READ THE SAMPLE AS A CITATION** — red on five CI lanes at `7db9987`. It passed locally on both seats because a dependency inside `.venv` happens to carry that name; a clean checkout has no `.venv`. **Narrating a citation rule in the shape of a citation is the same defect this cell already records once** (the backticked pointer it removed), **and it is now recorded twice.** Verified by running the gate's own two patterns over this document: zero violations, including over the pointer now removed. **Prior: v7 — RESPUN FOR THE ROUND-4 RETURN, 2026-09-15. F1, F2 AND F3 WRITTEN; F4 IS THE SECOND SEAT'S.** 🔴 **F2: NEW §4h, THE TRANSITION POLICY — and v6's relation-only quarantine CANDIDATE IS NOW A PROVEN SAFETY REGRESSION.** Executed: `Edge(relation=QUARANTINE_RELATION, disclosure=MENTIONABLE)` is accepted by the model, stores, and reads back `quarantined=True` **held entirely by the relation clause** — `ingest.py:190` pairs them, but ingest is one producer and the model is the contract. **Redact `relation` and `quarantined` flips to False, promoting an unverified third-party claim out of `## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)` into the grounded section.** A privacy operation would have WIDENED what the model may assert. **The general rule this forces: A REDACTION MAY NOT CHANGE A DERIVED DISPOSITION — it must re-establish it through a field it does not redact, in the same transaction, or REFUSE.** Third proven instance after `Episode.kind`→H14 and `retired_reason`→`active`. **`Episode.kind`'s closure binds the WRITE and IMPORT paths, never the read path** (a closure enforced on read makes every legacy store unopenable); existing prose kinds are RETAINED at migration, and **a marker-valued `kind` validates only when ATTESTED** — the §4b rule doing a second job. **And the EVIDENCE RULE: a transition claim proved on a record built under the new model proves nothing** — the fixture has already satisfied the rule it is meant to test, exactly how the packaged INV-12 fixture missed a widened embedder. 🔴 **F3: §11.2 IS REBUILT ON THE SECOND SEAT'S EXECUTED RESULTS, and v6's central claim there was FALSE** — it said `edge_event.reason` is closed by *"nothing today"*, when `sqlite.py:247` ALREADY refuses an unregistered reason on the `invalidated` kind (executed: `invalidate_edge(reason="told me in confidence")` is REFUSED). **The rule exists and must be EXTENDED, not invented.** **FOUR reason fields, THREE contracts, each stated against what it does today**: the two that close today; `Episode.retired_reason`, which has **NO refusal at all** and whose closure is a code change this spec requires; and 🔴 **`source_revocations.reason`, which has NO VOCABULARY TO PRESERVE** — it carries the caller's sentence verbatim while the affected records get `revoked_source`, so v6's single *"PRESERVE if vocabulary"* cell was wrong for it and it is REPLACED as ordinary prose. **`revoked_source` is the EFFECT's registry value, not the revocation's reason.** **§9b's D1 is ANNOTATED, NOT EDITED** — its own conditional (*"all three close, or the next sweep finds a fourth"*) has been met, and the owner's count stays the owner's. 🔴 **F1 was right and the fault was mine: decisions reached in discussion were never written into the text.** **§4b gains THE ATTESTATION RULE — the marker is NOT self-authenticating; the redaction RECORD is the authority — and it settles THREE rows that said "owed" at once.** **pre-existing marker-holding rows: ADMITTED AS UNATTESTED MARKERS**, not refused, not quarantined; INV-11 is re-keyed on ATTESTED redaction rather than on the byte string, because keying on the bytes freezes an owner's own content and renders it as a tombstone. **legitimately empty: redaction NEVER writes `""`**, so the ambiguity does not arise and INV-8 rejects a value redaction cannot produce. **§4g's notice-less tombstone vs INV-11's import mirror: the CONFLICT IS RESOLVED** — both stand once keyed on the record; what is refused is a marker presented AS a redaction without its notice. **repeat calls with no original receipt: a RECONSTRUCTED receipt, explicit `None` for what the record cannot support, nothing inferred.** 🔴 **ROWS 30/49 NO LONGER SAY "else the marker" — they write the NEW registry value `redacted`**, because `sqlite.py:247` already refuses an unregistered reason (v6's marker would have been rejected on every legacy row) and because **`NULL` on `Episode.retired_reason` UN-RETIRES the episode** (`active` IS `retired_reason is None`) while being harmless on `Edge.invalidation_reason` (`active` keys on `invalidated_at`) — an asymmetry v6 had flat. **The extension costs FOUR coordinated sites**, including the IMPORT-TIME gate at `asof/resolve.py:113` that fails `import veracium` if the registry is extended alone. **Base: the TREE's adopted v6 at `ef46d4a` (sha16 4eaec88fde6ad1bc), RE-COPIED, not folded** — the candidate had again drifted from it by exactly one line, the Author cell dev owns. **v6 — RESPUN FOR THE ROUND-3 RETURN, 2026-09-15.** **F3** §11.2 now REFERENCES `schema.DISPOSITIONED_REASONS` instead of re-typing it — v5 listed the JOURNAL's twelve and omitted four of the registry's seven; the legacy boundary is split into retain-at-migration vs remove-at-redaction, with **hiding a value in `why` removing nothing from storage**. **F4** precedence stated: §11 governs on CONTRACT, **§2d-iii-bis governs on any per-candidate ROW** — v5's §11.1 said deletions govern for `contribution_ledger` while rows 21/23 rule CLEAR-and-keep, and the map is right. **HISTORY SPLIT: §11 now contains NO history; it is in Appendix A.** §2d-v: **WHAT READS THIS FIELD?** — seven executed results showing a treatment changing something other than content, collapsing to **two missing enforcements** (INV-11's mirror; §2d-iv's closure). Row 46 becomes **PRESERVE-if-recognised-kind / REPLACE-if-prose** after v5's flat REPLACE was shown to break H14 twice. §8 gains the consequence that **a redacted record can no longer be corrected.** **Prior: v5 — THE PER-CANDIDATE TREATMENT MAP.** §2d-iii-bis carries one row per carrier with its VALIDATED resulting shape; v4's §2d-ii named 32 of 64 individually and covered the rest with a phrase, and the second seat held adoption on it. Also corrected: the class sentence over-named `desc`/`text`/`payload`, none of which is among the 64. **Prior: v4 — RESPUN FOR THE ROUND-2 RETURN.** Folds all seven round-2 findings. **F1** §4e — the semantic-rebuild exemption is WITHDRAWN (it holds only the instance lock; a two-connection run stores the stale vector) **and research's own v3.1 wiki fix was the same bug** — `set_wiki` takes `store_version` as a parameter, so capture-then-compare is the race it diagnosed; restated as a TRANSACTION rule. **F2** §4b — the marker is NOT reserved (`sanitize_llm_body(MARKER) == MARKER`; `remember()` stores it); reservation becomes INV-11's MIRROR, a refusal at every non-redaction write and import boundary. **F3** §11.2 — reasons closed PER OPERATION; v3.2's five-value CHECK would have rejected every lifecycle write the product makes. **F4** §4g — row 9 and the notice cases RULED. **F5** §4f — the exact-coverage claim WITHDRAWN; conservative reporting is the ordinary case and durable association is a forward obligation. **F6** §2d-ii — the treatment map, ruled against the write-site sweep; `Episode.kind` is REPLACE. **F7** §11.3 — the invariant matrix CORRECTED: it had redefined INV-1 and INV-3 and omitted INV-4/5. *Re-read before editing; quote the version you approve* |
| **Prior chain** | v1 (banner-only internal read) → **v2** (internal review folded into the body) → **v2.1** (dev's §2b fold at `436e4d4`, before round 1) → **v3** (research's respin for the round-1 return) → **v3.1** (four things folded at adoption from the second seat's exchange) → **v3.2** (the title line moved to line 1 after research's second-seat read found the registry rendering a banner as the spec's name) → **v4** (the round-2 return) → **v5** (the per-candidate treatment map) → **v6** (the round-3 return) → **v7** (research's respin for the round-4 return — F1, F2 and F3 written into the text; **SUPERSEDED BY v8 BEFORE ADOPTION and never reached the tree**) → **v8** (the owner's ruling that the migration report is ADVISORY, folded; the dangling research-tree pointer removed — **adoption HELD when the second seat read it against its own attestation rule**) → **v9** (INV-11 re-keyed on the RECORD in all four places v7 left keyed on the bytes, including the invariant table's own definition; the wrapped citation un-wrapped — **ADOPTED at `7db9987` and superseded within the hour: its Version cell redded a gate in a clean checkout**) → **v10** (the sample filename un-backticked; the defect and why both seats' local checks missed it recorded in the cell — **ADOPTED at `2a227f6`, sealed as round 5 at `a3ef39a`, RETURNED with three findings**) → **v11** (findings 1 and 2: absence is not content, and a contract is not a census — **ADOPTED at `ead0bcc`, sealed and dispatched as round 6, ACCEPTED WITH AMENDMENTS**) → **v12** (the source-revocation vocabulary finalised with `policy` defined and closed by a refusal; the older free-text summaries dated rather than deleted — **ADOPTED at `e0cba0a`**) → **v13** (this — `Spec-Status: accepted-with-amendments`, the decision recorded where a machine can read it) → **v14** (ACCEPTED at round 8; sealed as round 9 at `c05b709b`, RETURNED FOR IMPLEMENTATION CORRECTION with eight findings, the design still accepted; v13's "this" above is history from here) → **v15** (this — the round-9 corrections stated as contract) → **v15.1** (the round-10 corrections; v15's "this" is history from here) → **v15.2** (the round-11 corrections) → **v15.3** (the round-12 corrections) → **v15.4** (the round-13 corrections) → **v15.5** (the implementation accepted) |
| **Internal reviewers** | dev · research |
| **External review** | **required** — touches `store/sqlite.py`, `store/edge_events.py`, `store/schema_version.py` |
| **Decision + date** | **ACCEPTED — DESIGN 2026-09-17** (external round 8; Spec-Status flipped by dev, the acceptor, at the fold `47c268d`). **IMPLEMENTATION ACCEPTED 2026-10-06** (external round 14, pin `8a54a87`; the verdict banked as `0041-round14-verdict-verbatim.md`). **v16, 2026-10-14:** the amendment `0047/0041-replies`, its design accepted at round 4 (2026-10-13), folded on the owner's ruling “Accept now, fold next”. |
| **Path** | **full** |

> ## 📥 DEV'S INTERNAL READ — RECEIVED AND FOLDED 2026-09-13. Eight items; research verified three at the tree and WIDENED the blocking one.
>
> **Status: v1 is NOT clean. Item 1 blocks §2/INV-2 and must be fixed before any
> external dispatch.** Dev checked every claim at `17d2f42`; research re-checked
> items 1, 2 and 5 independently rather than folding on the word.
>
> ### 🔴 1. BLOCKING — `edges.subject` is a duplicated column too, and so is `relation`
>
> **VERIFIED at `store/schema_version.py:123-127`.** The DDL is
> `id, user_id, subject TEXT, relation TEXT, object TEXT, active, quarantined, json TEXT`.
> §2 names **only `object`** as "the second site" and INV-2 plants a mutant for
> that one column alone. **Dev found `subject`. Research's re-derivation from
> the DDL finds THREE duplicated columns, not two: `subject`, `relation` and
> `object`.**
>
> **A redaction that tombstones `json.subject` and leaves the column is the §7
> worst outcome** — the content survives in a place nothing looks.
>
> **Fix: INV-2 becomes "every column that duplicates a json field", ENUMERATED
> FROM THE DDL at implementation, with a mutant planted PER COLUMN.** A
> hand-listed carrier set is what produced this hole in the first place —
> derive it from the schema, do not maintain it. **And say why `relation` is
> treated differently if it is** (closed vocabulary rather than user content);
> silently omitting it is how `subject` was omitted.
>
> ### 2. `why` renders event reasons, so the redaction reason reaches a surface
>
> `episodes.json` carries `retired_reason` (`schema.py:822`) and
> `edge_event.reason TEXT` already exists. **`why.py:73` renders event reasons
> (`events: [{seq, txn, kind, reason, at, changed}]`).** So **the redaction
> reason WILL reach the `why` output unless INV-6 says otherwise.** §2c's third
> row is right that this is the ConfirmationActor shape. **Open decision for the
> spec: is `why` inside INV-6's fence? It is a CLI verb — and the spec must say
> whether it is also served through MCP.**
>
> ### 3. `contribution_ledger.payload` is NOT a content carrier — record the negative
>
> The closed per-site payload schemas carry metadata only (`observed_at,
> confidence, valid_from, disclosure, derived_from, basis, author_of_evidence,
> date` — `contribution.py:44-60`). **The "evidence_ref_digest rows" row stands
> as written.** Recorded so a reviewer does not re-derive it.
>
> ### 4. §4a and the wiki row contradict each other for one carrier
>
> *"Invalidated and recompiled, never edited in place"* — **the recompile is a
> model call and cannot sit inside the single transaction §4a promises.**
> Between the transaction and the recompile the wiki `text` still carries the
> content. **"Every carrier or none" and "recompiled" cannot both be true for
> this carrier.** Either the transaction BLANKS the wiki text (invalidate =
> tombstone now, recompile later) or the spec STATES the window. Research's
> view: blank it — a stated window on a privacy operation is a window someone
> will be inside.
>
> ### 🔴 5. §8's survival claim is FALSE across export/import
>
> **VERIFIED independently: `edge_event` appears ZERO times in
> `portability.py`.** It exports edges and episodes. **So a re-import of a
> redacted store carries the tombstoned edge but NOT the `redacted` event**, and
> §8's *"the record that it existed and was redacted survives"* does not hold
> across the boundary. **Either export carries the redacted event, or §8 narrows
> its claim to the live store.**
>
> **And this is where §9's third question bites**, which dev is right to link:
> redaction is not an entitlement operation — except that on re-import **a
> redacted edge without its event is indistinguishable from an edge someone
> simply blanked.**
>
> ### 6. The tombstone gets embedded unless the rebuild skips it
>
> `semantic.py:31 content_digest(edge)` is computed from the edge's content, so
> after redaction **the next index build embeds the TOMBSTONE and writes a fresh
> `edge_embedding` row.** Harmless as an oracle — the pre-image is the public
> marker — but **INV-7's "no `content_digest` survives" is then true of the
> ORIGINAL while a tombstone row reappears.** Decide and state which.
>
> ### 7. v19 removes a carrier, and hands §6 an obligation
>
> A captured procedure's `note` is now empty; the gloss is in `object`, already
> in the table. **But `describe_procedures` renders `object` for procedural
> records**, so §6 needs INV-3's sibling — **describe degrades to "redacted" and
> never fails** — or the tombstone marker is what the host reads back as the
> user's routine.
>
> ### ✅ THE TWO OPEN DECISIONS — DEV'S ANSWERS 2026-09-13, both verified by research at the tree
>
> **(2a) `why` IS OUTSIDE INV-6's FENCE.** `why.py` is imported at exactly ONE
> site (`cli.py:272`); the six `@server.tool()` names are `remember`, `recall`,
> `answer`, `maintain`, `record_procedure`, `describe_procedures` — **no `why`,
> and `Memory` has no biography method.** So `why` is a CLI-operator surface:
> not a prompt, not recall, not export, not MCP — exactly the four names INV-6
> lists. **`why` SHOULD render the redaction reason; the operator asking "why is
> this blank" is its one legitimate reader.** Dev's proposed test is the right
> shape: assert the served tool set BY NAME against 0031's reflected inventory,
> so it fails the day a `why` tool appears rather than the day someone checks.
>
> **(2b) BLANK THE WIKI TEXT IN THE TRANSACTION** and let the next compile
> rebuild. Verified safe, and the branch it takes is worth naming in the spec:
> the recompile trigger (`compile.py:160-168`) has two — `cached is None`
> (branch 1) and a policy-digest mismatch parsed **out of the stored text**
> (branch 2). **Blanking takes BRANCH 2.** Research ran it: `_split_envelope('')`
> returns `(None, '')`, so the digest never matches and recompile fires.
> ⚠️ **Deleting the ROW would take branch 1, which is unconditional.** Dev's own
> argument — *"a blank row is the same shape the store has before its first
> compile"* — describes branch 1, but before the first compile there is **no
> row**, not an empty one. **Either works; the spec must say which branch carries
> the guarantee**, because the two have different dependencies and only one is
> visible in the sentence.
>
> ### 🔴 AND A CROSS-FINDING NEITHER ANSWER SEES ALONE: (2a) AND ITEM 5 COLLIDE
>
> **`edge_event.reason` is free TEXT** (`schema_version.py:490`). Under (2a)
> `why` renders it — so an operator who writes *"redacted: user's HIV status"*
> into the reason has put the content back into the store, **in a field §2 does
> not enumerate as a carrier.**
>
> **It is confined today by exactly two facts: `why` is not in MCP, and
> `edge_event` IS NOT EXPORTED** (item 5: zero occurrences in `portability.py`).
> **But item 5's fix is to make the redacted event exportable — which removes
> the confinement (2a) relies on.** The fix for one item dissolves the other's
> premise.
>
> **Three genuinely different resolutions, none recommended here:** constrain
> the reason to a CLOSED VOCABULARY (cheapest; makes the field a non-carrier by
> construction) · export the event **without** the reason (keeps §8's claim and
> the confinement; costs an asymmetric export shape) · narrow §8 to the live
> store and leave the reason free (costs the survival claim that motivated
> item 5).
>
> **Either way §2's enumeration MUST NAME `edge_event.reason`, even while it is
> confined.** An unenumerated carrier is exactly how `subject` was missed, and
> *"it cannot travel today"* is a property of two other decisions rather than of
> the field.
>
> ### 8. Line drift
>
> The `(true value: …)` write is at `__init__.py:1683`, not `:1681`.
>
> ### What dev did NOT find, recorded because a negative from a full sweep is worth as much as a hit
>
> **No other TEXT/BLOB column carries content** — confirmations,
> consolidation_ops, supersession_*, source_revocations, store_identity and
> store_epoch hold ids, digests and timestamps. ⚠️ **`Edge`'s json string fields
> were NOT enumerated from the model** (the DDL cannot see inside `json`), and
> **the spec must not claim that enumeration until someone has done it.**

⚠️ Amended by `0047/0041-replies`: `replies.text` (0047) carries content; it is treated with its edge (§2d-ii, REPLACE; §2d-iii-ter).

> ## ⚠️ §3'S CARRIER ENUMERATION CHANGES WHEN 0037 v19 LANDS — dev's answer, 2026-09-13T14:25Z
>
> Research asked dev, before the internal read, whether v19 adds or removes a
> content carrier — because **§3's enumeration is stale the moment it does**, and
> finding that from an external reviewer would be the worse way to learn it.
>
> **Dev's answer: v19 REMOVES one and ADDS none.** On 0.24.0 a captured
> procedure's `note` held the **verbatim span**; under v19 the span is verified
> and **discarded**, so the note is empty. The gloss stays in `object` as before;
> `procedural_refused` is a count; **no digest is stored** — dev cites this
> document's own §4 confirmation-oracle argument as the reason.
>
> **So §3 loses one row and gains nothing.** *(Do not edit the enumeration until
> v19 is actually on main — the candidate should describe what is shipped, not
> what is intended.)*

> **Implementation note, tranche 1 (2026-09-19; the owner's word "implement all 3", 0042 and 0043 complete on
> the dev side).** The two prerequisites §2d-v named and the registry value rows 30/49 require, before any
> redaction exists: **INV-11's MIRROR** — a non-redaction write may not introduce the marker — as a refusal
> at the edge upsert (every persistence path: `add_edge`, the supersession plan, correction) and at
> `add_episode`; **§4h(i)** — a quarantine relation without the QUARANTINED disclosure refused at the same
> upsert (ingest sets both; the model-and-store path never did); **§2d-iv's closure of `Episode.kind`** to the
> recognised operational kinds at the WRITE path and at the IMPORT commit (never the read path: a stored
> prose kind still loads, proved on the frozen pre-restriction store). Each is a declared 0042 census site
> (five ids; the import commit's refusal is its own id — one id, one function) with a declining execution in
> the runtime leg. The marker and the recognised-kind set live in `src/veracium/redaction.py`.
> 🔴 **The registry extension is SIX sites, not four:** `DISPOSITIONED_REASONS`, `asof/resolve.RESOLUTION`
> (`NOT_RETURNABLE`, `redacted-excluded`), the 0004 producer list and doctor as the table names — AND
> `schema.AS_OF_DISPOSITION` (0030 §2a, `EXCLUDED`) and `schema.NAMES_A_SUCCESSOR` (0028 §5.1, `False`), each
> behind a build-time gate that fails the import without it, plus the 0028 evidence checker's oracle copy. The
> 0004 producer list gains the value only when a producer passes it (tranche 3, `redact()`): its test asserts
> the literal in a producer. Seven strict xfails flipped green and their marks came off; the tests and the
> round-2/round-3 reproduction scripts that had written restricted shapes through ordinary writers now plant
> them as pre-restriction ROWS (§4h(iii)'s own rule), and the reproductions print the flipped outcome beside
> the reviewer's claim. What remains: tranche 2 (the schema bump: `episode_event`, the redaction record, the
> migration report of unattested markers), tranche 3 (`redact()` itself over the 64-carrier map), tranche 4
> (readers and the import contract), tranche 5 (delayed writers, the transition evidence, the closure rows).

> **Implementation note, tranche 2 (2026-09-19).** The store schema moves 14 → 15 (0018's obligations
> applied: additive DDL, no data step, every row byte-identical across the cross; the release record
> re-derived at the commit; the migrated-shape record carries v15; the orchestrator's mint base and
> ladder derive from the head). `episode_event` (§4b-ii: `edge_event`'s shape — seq/txn, kind, D1's
> reason, `state` as found, recorded_at) and `redactions` (§4b, the ATTESTATION record: target kind and
> id, the JSON list of fields treated, marker version, D1's reason, store version before/after, the
> journal event it wrote, recorded_at), both REQUIRED, their indexes REBUILDABLE.
> `migration.unattested_marker_report(store)` is §4b's report as ruled v7: a read over `edges` and
> `episodes` returning `{target_kind, target_id, field}` for every marker-carrying field with no attesting
> `redactions` row — it changes nothing, refuses nothing, never defaults; `test_C_the_migration_report…`
> flips green on the frozen store's two planted rows and its strict mark comes off; the campaign's report
> mutants restore the landed function and the landed report is that test's sixth positive control.
> `forget_user` erases both tables (0017's per-user erasure reaches the new carriers); the doctor's `refs`
> check names a redaction record whose target does not exist and an episode event whose episode does not
> exist. The frozen v14 fixture stays frozen: the transition tests migrate their writable COPY before
> opening it (a below-head store refuses to open; §4h(iii)'s rows are still the pre-restriction writer's).
> Nothing writes either table yet — that is tranche 3's `redact()`. The carrier enumeration's §A (the column
> census, `carrier_enumeration_OUTPUT.txt`) now lists 17 tables: `episode_event.state` holds an episode's json
> as found — the same carrier set as the `Episode` model, to be tombstoned at redaction as `edge_event.state`
> is (tranche 3) — and `redactions` is a non-carrier by construction (ids, field NAMES, D1's vocabulary,
> versions, timestamps; never content); the 84 terminal identities, 64 carriers and 20 non-carriers are
> model-derived and unchanged.

> **Implementation note, tranche 3 (2026-09-19).** `Memory.redact` → `SqliteStore.redact`: one journaled
> write transaction over §2d-iii-bis, the record's own carriers by the PURE `redaction.treat_edge` /
> `treat_episode` (validated under the model before any row is written), the side tables by the map, the
> journal tombstoned and closed by a `redacted` event (§4c; INV-4), the `episode_event` row (§4b-ii), the
> wiki dropped. **The attestation record is the receipt**: `RedactionReceipt` is the `redactions` row read
> back, so a repeat returns the original (`repeated=True`, one event); INV-11 keys on the row at
> `_upsert_edge_row` and `add_episode`; `reconstructed` is reserved for the import contract (tranche 4).
> §4h(i) executed: the frozen relation-only quarantine keeps `quarantined` through the disclosure set in the
> same transaction, and a treatment that would move `active` / `quarantined` / `needs_confirmation` /
> `ungrounded` (edges) or `active` / `quarantined` / `use_only` (episodes) refuses with nothing written. Row 3
> landed by amending `AgreementRecord`'s uniqueness validator to admit repeated REDACTION markers and nothing
> else (the before/after fixture carries the negative control). Two things the spec did not say and the
> implementation had to decide, recorded here for the review package: (1) `episode_event` allocates its own
> per-user seq/txn (its primary key is its own; sharing `edge_event`'s allocator would let an edge event and
> an episode event collide on seq); (2) the ledger digests are cleared on rows the target SURVIVES **or
> CONTRIBUTES to**, and the survivors of the latter are the F6 "surviving derived records" the receipt names
> — INV-7's "for redacted content" reaches both directions of the absorption. Seven declared 0042 sites.
> What remains: tranche 4 (readers — `edge_state_at`'s REDACTED state, `recall`, `describe_procedures`; export
> and the import contract), tranche 5 (delayed writers, the transition evidence rows, the closure ledger).

> **Implementation note, tranche 4a (2026-09-19) — the readers.** By the ATTESTATION RECORD everywhere (the
> store's `redacted_targets(user_id, kind)`; an unattested marker row is in no reader's excluded set): `recall`
> drops attested-redacted edges from the retrieved subgraph (and its semantic metadata), attested-redacted
> episodes from the episode list, and both from the contested groups — after retrieval, inside the visible
> set (a slot a redacted record won is a recall-quality cost, not a disclosure); the wiki compile's input
> excludes them (the cache dropped at redaction would otherwise be recompiled over the marker);
> `describe_procedures` reports a redacted procedure as `withheld: redacted` — after the stamp conjunct
> (a PRESERVE row, so it still classifies) and before the relation (the marker) — and a hidden one stays
> hidden; the as-of classifier returns `REDACTED` for any T (above). `why` landed with tranche 3. What remains:
> tranche 4b (export carries the redaction record, D2; the §4g import contract), tranche 5.

> **Implementation note, tranche 4b (2026-09-20) — D2 and the §4g import contract.** The export carries one
> `redaction` line per attestation record (format 13, stamped only when one exists — the refuse-don't-drop
> era rule; the record itself travels redacted); the line carries the SOURCE identity (origin, source user,
> source event ref), which a witnessed row keeps in its own id so a re-export names the original source. ⚠️ *v15: the id now ALSO binds the destination user and the typed target (§4g, v15 block).* On
> import the notices are validated before any record is admitted (an invalid one refuses the whole import —
> the unit — with nothing written; two under one identity with different bodies refuse as a corrupted
> source; a file declaring a version below 13 that carries notices refuses), deduplicated by identity, and
> applied INSIDE the atomic import commit through the same in-transaction body `redact` uses: held → applied
> (the destination's journal closes the record with its own `redacted` event; a record arriving already
> marked is journaled all the same — V-APPEND's updater and V-KIND's kind, with the attestation naming the
> source's carriers too); absent → a STANDING notice (a `redactions` row with no event; INV-11 refuses an
> ordinary write of that id; the doctor reports it as information — §11.4's refs exemption, met at the
> redactions table rather than the journal, since a standing notice writes no event) and the record is
> redacted on arrival *(⚠️ v15.6: never — a standing notice now only ATTESTS an arrival this import inserts that already shows the redaction, from the notice's own origin on a default import; any other arrival refuses the import. §4g's v15.6 block)* in the same commit that delivers it (the standing row completed in place — one row
> per identity, the two orders reaching one state); a held DIFFERENT version is redacted anyway and flagged
> `inconsistent_notices`; a marker-carrying record with no notice is admitted as an UNATTESTED marker and
> listed. INV-11 binds the import boundary: a record this store has redacted (a COMPLETED attestation) is
> not repopulated by a file carrying no notice for it — a standing notice is exactly the arrival case and
> admits. A `user_id=` remap moves the notice's target with the record's minted id; a notice whose record
> is not in the file keeps the source's id under a remap (no record can arrive under it — it stands as the
> witness). The witnessed receipt is `reconstructed=True`, reason `imported_notice`. What remains: tranche 5
> (§4e's delayed writers, the transition evidence rows, the closure ledger).

> **Implementation note, tranche 5 (2026-09-20) — §4e's delayed writers, and the last strict xfail.** Both
> paths §4e names, in the two shapes it admits: the embedding upsert takes `BEGIN IMMEDIATE` BEFORE its read
> (the read and the insert one transaction under the DATABASE lock; a writer that cannot take the lock within
> the busy timeout refuses in the 0007 §4c form — `store.embedding.txn-locked`, a declared site — never a
> silent skip; an already-open transaction is joined), and the wiki publish is ONE conditional statement —
> `INSERT … SELECT … WHERE the write counter still equals the version the compile read BEFORE its inputs`
> — so the check and the write are indivisible and a compile that read content before a redaction can never
> publish it (`set_wiki` returns whether it wrote; a stale compile publishes nothing and the next read
> recompiles). Round-2 F1a's two-connection reproduction now REFUSES inside A's window (B's write cannot take
> the lock, the refusal propagates through A's hook, A rolls back, nothing is stored, A's connection is
> reusable) and round-1 F2's wiki race is refused by the statement; both reproductions print the flipped
> outcome beside the reviewer's claim. The eleventh strict xfail flips green; the campaign's derived
> coverage reads no strict xfail awaiting a control. INV-9's wording, deferred to dev's reproduction, is the
> §4e rule as landed. What remains of 0041 on the dev side: nothing but the implementation-review package,
> on the owner's word.

---

## 1. Problem and motivation

**Three independent routes reached the same missing capability**, which is why
this is a spec rather than a backlog item:

1. **C0 (ruled).** The one real deployment holds third-party content — 7,023 of
   7,023 note-bearing edges are third-party in origin. A correspondent asking for
   their content removed has **no targeted path**: `delete_episode` is a silent
   no-op for confirmation episodes' siblings, `source_id` is NULL on all 7,154
   edges so 0022 revocation cannot fire, and `forget_user` removes everything.
2. **T12.** `delete_episode` **refuses** outcome-chain links (0009 H14), so
   deleting supporting content does not delete the judgment built on it.
   Append-only history and privacy deletion contradict each other today.
3. **The embedded value.** `__init__.py:1681` writes
   `f" (true value: {corrected_value})"` into a judgment's summary, **so a
   `CORRECTED` judgment carries user-supplied content inside a chain nothing can
   remove short of `forget_user`.**

**All three need CONTENT gone, not RECORDS gone.** That distinction is the
spec's spine: the existing refusals (0009 H14, 0010 X21) are deliberate fences
against *"the unfenced-door class"*, and **a deletion operation that relaxed them
would be the exact failure they were built to prevent.**

## 2. Field contracts touched

> **🔧 DERIVED, NOT HAND-MAINTAINED — v3.** This table is produced by
> `0041-carrier-enumeration.py`, which reads the DDL **and** the pydantic models,
> because neither sees what the other does: SQL cannot look inside `edges.json`,
> and the models cannot see that three columns duplicate what the blob holds.
> **v1 hand-listed one duplicated column and INV-2 planted one mutant. There are
> three.** Re-run the script rather than editing this table.
>
> ### 🔴 v3, 2026-09-13 — AND THE DERIVED ENUMERATION ITSELF SWEPT ONE TABLE OF FOURTEEN
>
> **The script read `SCHEMA_V1` and looped over `edges`.** The live schema is
> `SCHEMA_V13`. Eleven tables were outside its corpus — **including
> `edge_event`, `edge_embedding` and `contribution_ledger`, which the table
> below already names**, so the enumeration had never confirmed the very rows it
> was cited as deriving. It looked correct because its `edges` output was
> correct. **A derivation is only as wide as its corpus; "derived" is a claim
> about the corpus, not about the method.** The script now resolves the newest
> `SCHEMA_Vn` by version number, so the receipt's v14 table enters the sweep
> with nobody remembering to add it. **The widened sweep's findings are §2b.**

> ### 🔴 v3, 2026-09-15 — THE ENUMERATION'S OWN MODEL SET WAS A HAND-LIST. FOURTH FAILURE, SAME CLASS.
>
> The round-1 reviewer found this section missing `Edge.original_relation`,
> `Episode.retired_reason`, and `agreement.markers` under a foreign lexicon
> version. **They were missing together, and the reason they were missing
> together is the finding.** Section B of the enumeration read
> `text_fields(Edge)` and `text_fields(Provenance)` — **two model names written
> literally.** `Episode` was never walked, and nesting was never recursed at
> all. So the banner directly above, which corrected this script for reading
> `SCHEMA_V1` when the live schema was `SCHEMA_V13`, **fixed the corpus at the
> DDL source and left the identical defect standing one source lower.**
>
> **That is the fourth failure of one class in one script** — a line-anchored
> DDL regex, `SCHEMA_V1`, the fifteenth table, and now the model set. Each time
> the script looked correct because what it *did* enumerate was enumerated
> correctly. **"Derived" is a claim about the corpus, and this project has now
> paid for that sentence four times in the same file.**
>
> It now discovers every `BaseModel` in `veracium.schema` and recurses through
> nested models, cutting cycles on a visited set rather than a depth limit.
> **11 text-capable fields across 2 hand-named models → 125 across 18
> discovered.** All three fields the reviewer named appear, including
> `agreement.markers` at two levels of nesting.
>
> ### THE 125 ARE NOT 125 CARRIERS, AND THE RAW LIST MUST NOT LAND IN THIS TABLE
>
> 125 is a count of **paths**, not of fields. `ContestedGroup.exposed.note` and
> `SupersessionPlan.incoming_edge.note` are both `Edge.note` reached through a
> container; redacting the field redacts every path to it. **Pasted wholesale,
> this table would inventory `Edge.note` three times and the repetition would
> read as coverage.** Section C of the script collapses every path to its
> terminal `(model, field)` and classifies it:
>
> **84 terminal identities behind 135 paths = 64 carriers + 20 non-carriers + 0
> unresolved.** The bucket sum is asserted, so a field dropped in triage fails
> the run rather than vanishing from this table.
>
> **Two defects in the triage's first pass, both caught by its own controls and
> both pointing the expensive way** — recorded because the same two shapes will
> recur in the implementation:
>
> 1. **A FALSE CLEAN.** Persistence was first derived from `model_validate_json`
>    in `store/`, which sees JSON blobs and nothing else. `SupersessionRefusal`,
>    `Confirmation` and `ContributionRecord` are `INSERT`ed column by column, so
>    all three were reported *"never stored"* — **non-carriers, while being
>    written to disk.** Persistence is now derived from **both** storage
>    disciplines: the JSON round-trip, and the model *being* the row.
> 2. **A DEAD BRANCH THAT READ AS A PASSING CHECK.** The value-space test could
>    not fire: **`pattern=` appears nowhere in `veracium.schema`**, and `Literal`
>    fields never enter the walk. Every non-carrier was one for a reason that
>    check never supplied. It is kept with its emptiness **asserted**, so a field
>    that gains a pattern fails loudly instead of being quietly reclassified.
>
> An intermediate overlap test over-matched the other way, reporting
> `ContestedGroup` stored in `edges` on two shared field names. **Subset — the
> model IS the row — is the property that actually means "this is stored".**
>
> ### ⚠️ THE SENTENCE THIS SECTION MUST CARRY: THE NEGATIVES ARE STORAGE, NOT SHAPE
>
> **Every one of the 20 non-carriers is a non-carrier because it never reaches
> disk — NOT because its content is constrained.** Nothing in `veracium.schema`
> bounds a text value. `CorrectionAuthorisation.principal`,
> `OutcomeJudgmentDraft.summary` and `Relation.desc` hold whatever a caller puts
> in them; they are clear only while nothing persists them. **If any of these
> gains a storage site, all twenty become carriers at once**, and this table
> will be wrong without a single line of it changing.
>
> They are therefore recorded below as **excluded-by-storage**, never as
> excluded-by-shape, and the enumeration must be re-run at any change to what is
> persisted — not only at a schema change.
>
> ### The three the reviewer named, with their treatment
>
> | field | why it was missed | treatment |
> |---|---|---|
> | `Edge.original_relation` | `Edge` *was* walked; v1 classified this field as *"identifiers/vocabulary, not user content"* — see the row below, now **corrected**. Dev's reproduction confirms an unrecognised extractor relation lands here **verbatim** (`relation` becomes `unclassified`, the prose is kept) and **exports** | **content replaced by the tombstone.** It is extractor-supplied prose, not vocabulary |
> | `Episode.retired_reason` | `Episode` was never in the corpus — no model but `Edge` and `Provenance` was walked | **D1 applies.** It is the shape *"host-supplied reason string"*, the fourth known instance after `edge_event.reason`, `Edge.invalidation_reason` and `source_revocations.reason`. Dev's reproduction confirms prose through the sole retirement writer (`_retire_episode_row`), persisted and exported |
> | `agreement.markers` | nested two levels down; the walk did not recurse | **content replaced.** Under a **foreign lexicon version** the record is validated as opaque closed shapes only (0026-R7-1), so marker text is **not** vocabulary-constrained and carries prose — reproduced by dev, persists and exports |
>
> **`Edge.original_relation` is the one that matters most here**, because this
> table already named it and named it *wrong*: it sat in the "stated so the
> negative is recorded" row. **A recorded negative is load-bearing — a later
> reader trusts it instead of checking — and this one was false.**

| carrier | field | change |
|---|---|---|
| `edges` | `json.subject`, `json.relation`, `json.object`, `json.note` | content replaced by the tombstone |
| `edges` | 🔴 **`subject`, `relation` AND `object` COLUMNS** | **same values, second site — THREE columns, not one.** INV-2 plants a mutant **per column**, enumerated from the DDL at implementation |
| `edges` | 🔴 **`json.invalidation_reason`** | **free text, newly enumerated.** Nobody had named it; it is the same shape as `edge_event.reason` below |
| `edges` | 🔴 **`json.original_relation`** | **CORRECTED v3 — this row previously read *"identifiers/vocabulary, not user content"*, and that recorded negative is FALSE.** An extractor relation the registry does not recognise is kept **verbatim** here while `relation` becomes `unclassified`; it persists and exports (reproduced by dev at the round-1 pin). **Content replaced by the tombstone** |
| `edges` | `json.supersedes` | identifier, not user content — **stated so the negative is recorded**, and re-derived at v3 rather than inherited from the row it used to share with `original_relation` |
| `episodes` | 🔴 **`json.retired_reason`** | **free text, newly enumerated at v3 — `Episode` had never been in the enumeration's corpus.** **D1 applies**: the shape *"host-supplied reason string"*, fourth known instance. Prose reaches it through `_retire_episode_row`, persists and exports |
| `edges` | 🔴 **`json.agreement.markers`** | **newly enumerated at v3** (nested two levels; the walk did not recurse). Under a **foreign lexicon version** the record is validated as opaque closed shapes only (0026-R7-1), so markers are **not** vocabulary-bound and carry prose. **Content replaced** |
| `edges` | `json.evidence_ref`, `json.source_id`, `json.origin` | host-supplied identifiers — §8's limit applies, not redacted here |
| `episodes` | `json.summary` | content replaced; **includes the embedded `(true value: …)`** |
| `wiki` | **the ROW** | 🔴 **DELETE THE ROW in the transaction** (v2, dev's answer as amended). v1 said *"invalidated and recompiled"* — **the recompile is a model call and cannot sit inside the transaction**, so the content stayed in the row for the whole window and *"every carrier or none"* was false for this one. **Deleting takes `compile.py:161`'s `cached is None` branch, which is unconditional**; blanking the text takes the digest-mismatch branch, which works only because `_split_envelope('')` returns a non-matching digest — verified, but a guarantee resting on a parser's behaviour on empty input |
| `edge_embedding` | `vector` | **dropped** |
| `edge_embedding` | `content_digest` | **dropped** — see §2c |
| `contribution_ledger` | `evidence_ref_digest` rows | **dropped** for the redacted survivor |
| `edge_event` | `state` | **tombstoned**, plus a new `redacted` event — §4c |
| `edge_event` | 🔴 **`reason`** | **free TEXT, and A CARRIER — enumerated here even though it cannot travel today.** `why.py:73` renders event reasons and `why` is a CLI-operator surface (verified: imported once at `cli.py:272`; not among the six MCP tools). **Its confinement is a property of TWO OTHER DECISIONS — that `why` stays out of MCP, and that `edge_event` stays unexported — and §8's fix proposes changing the second.** See the decisions below |

**Nothing structural changes IN THE RECORD TABLES.** No `edges` or `episodes`
row is deleted, no `seq` shifts, no reference is orphaned. That is why this is
redaction and not deletion.

> 🔴 **CORRECTED v3 (F7).** This paragraph read *"No row is deleted"* flatly,
> while the table directly above it **deletes the `wiki` row**, drops
> `edge_embedding` rows and drops `contribution_ledger` rows. **Three deletions
> named in the table and denied in the sentence under it.** The distinction that
> was meant is between **records** — never deleted, which is the whole claim —
> and **derived rows**, which are rebuildable and carry no history. Stated that
> way it is true and it is the property that matters; stated flatly it was
> simply false, and it is the kind of false a reader accepts because it sounds
> like a summary of what they just read.

## 2b. The other eight tables — swept 2026-09-13, three carriers found

*The table above names six tables. `SCHEMA_V13` has fourteen. **The eight never
examined are enumerated here with a verdict each, because an unexamined table
and a cleared one are indistinguishable in a document that simply omits both.***

### Carriers — must be added to §2's treatment

| carrier | field | why it carries | status |
|---|---|---|---|
| `source_revocations` | 🔴 **`reason`** | **free TEXT, host-supplied** (`revocation.py:122`), written verbatim. **The same shape as `edge_event.reason`, which §2 already classes a carrier** — and §2c's third row exists precisely because a free-form reason "lets a host smuggle prose past the constraints on the other fields." One reason field was found and confined; its twin was not. | **NEW — §2 must treat it as it treats `edge_event.reason`** ⚠️ **HISTORICAL as at §2's writing (round 1) and SUPERSEDED BY §11.2 (v12): this row records that the field carried free text THEN. It is not a statement that it may do so permanently — D1 requires a closed vocabulary for future writes, and §11.2 now names the four values.** |
| `supersession_refusals` | 🔴 **`relation`** | the **edge's own `relation` value**, copied at `graph.py:549`. §2's headline finding was *"three columns duplicate the json — not one."* **This is a fourth site, in a different table**, and it survives a redaction that rewrites all three. | **NEW — tombstone with the others** |
| `supersession_operations` | 🔴 **`request_digest`, `logical_request_digest`** | **SHA-256 over `raw_request_snapshot` — "the COMPLETE Edge model dump… EVERY field"** (`contribution.py:213`), which includes `subject`, `relation`, `object`, `note`. **This is the confirmation-oracle class §2c-ii names: it cannot reconstruct the text, but given a candidate it verifies it — and that is exactly why §2 orders `edge_embedding.content_digest` DROPPED.** The oracle 0041 closes in one table stands open in another. | **NEW — and it needs a ruling, D4 below** |

> **🔴 D4 — DECISION REQUIRED. The receipt digest cannot simply be dropped the
> way `content_digest` can, and the difference must be stated rather than
> assumed away.**
>
> **Two honest asymmetries, both against a straight drop:**
> 1. **It is a weaker oracle than `content_digest`.** `content_digest` digests
>    the content alone; this digests the whole edge dump, so confirming a guess
>    requires already holding `id`, `user_id`, every timestamp and every
>    confidence. The guess space is enormously larger. **Weaker is not closed** —
>    an adversary holding a pre-redaction export holds exactly that.
> 2. **It is load-bearing.** It is the replay identity that separates a true
>    retry from a collision (`sqlite.py:1127` refuses at write via
>    `validate_receipt_state`). **Dropping it does not degrade a receipt; it
>    breaks idempotency for that operation.**
>
> **Research recommends: tombstone the receipt's digest columns to a sentinel
> and record the redaction on the operation, accepting that a replay of a
> redacted supersession can no longer be distinguished from a collision and must
> therefore REFUSE rather than silently re-apply.** A refusal after redaction is
> correct degradation, on the same reasoning §4g already accepted for a receipt
> naming a redacted record — **it becomes unreadable, and unreadable is the
> right answer.** But this trades an availability property for a privacy one and
> **is the owner's call, not research's.**

### Cleared — the negatives, recorded so the sweep is auditable

| table | what it holds | verdict |
|---|---|---|
| `contribution_ledger` | `payload` is a **CLOSED field set** — `observed_at, confidence, valid_from, disclosure` + optional `derived_from, basis` (`contribution.py:48-52`), validated on write. **`basis` is a closed vocabulary** (0037 §4b, `V-BASIS-CLOSED`), not prose. | **not a carrier.** §2's existing row (drop `evidence_ref_digest`) is unchanged and now checked rather than assumed |
| `supersession_operations` | `response` is `effect_payload(result)` — **three integers** (`inserted_incoming`, `invalidated`, `refused`), `sqlite.py:1120` | **not a carrier** (the digests on the same row ARE — above) |
| `confirmations` | `actor`/`call_path` closed enums; `correlation_id` and `request_digest` **host-supplied identity** — §8's limit applies, as it does to `evidence_ref` | **not redacted here; §8's limit, stated** |
| `consolidation_ops` | `operation_id, fence, state, owner, lease_*, claimed_ids` (`sqlite.py:1820`) — lease bookkeeping and identifiers | **not a carrier** |
| `store_epoch` | `started_at` | **not a carrier** |
| `store_identity` | `origin` | **not a carrier** |
| `write_counter` | `user_id` | **not a carrier** |

### 2b-ii-bis. 🔴 THE TABLE SHIPPED, AND NEITHER THE DDL NOR THE CONSTRAINT IS WHAT §2b-ii WAS WRITTEN AGAINST

*Research, 2026-09-14T23:38Z — re-derived at the moment of adoption, because
0027 v14 landed `policy_receipt` after §2b-ii was written and the frozen-candidate
rule makes this the last moment to respin. **The carrier enumeration found it
without being told**: it resolves the newest `SCHEMA_Vn` by version number, so
`SCHEMA_V14`'s fifteenth table appeared on the next run. That widening was made
for exactly this.*

**Three ways the shipped table differs from the one §2b-ii classified.**

**1. The DDL is not three constrained columns — it is a JSON BLOB.** As shipped:

```sql
CREATE TABLE policy_receipt (
  user_id TEXT, recall_id TEXT, policy_id TEXT, policy_version TEXT,
  recorded_at TEXT, receipt TEXT NOT NULL, PRIMARY KEY (user_id, recall_id))
```

`tags_matched` is **not a column**. It lives inside `receipt`, which holds the
receipt's JSON verbatim. **So `policy_receipt.receipt` is a SECOND blob carrier
of the same kind as `edges.json`** — a TEXT column whose interior the schema
cannot describe and a column-level sweep cannot reach. §2 handles `edges.json`
as a special case; **it must now handle two, and the enumeration's section B
warning ("the DDL is blind to these") applies to this column as well.**

**2. The constraint §2b-ii endorsed was never implemented.** Dev's 2026-09-13
reply said the three fields "will constrain them at the model to identifier
shape (letters, digits, `._:-`, ≤64 chars each), refused otherwise, so that the
table carries no free TEXT column". **Measured at v14, all three accept
arbitrary prose:**

| field | value accepted at v14 | lands in |
|---|---|---|
| `policy_id` | `'a whole sentence, with spaces and punctuation.'` | its own TEXT column |
| `policy_version` | `'diagnosis: hiv-positive, disclosed here'` | its own TEXT column |
| `tags_matched` | a 400-character string; a full prose sentence | inside `receipt` |

`PolicyLane.__post_init__` checks `policy_id` and `policy_version` are non-empty
strings and `ranks` is a dict. **`tags_matched` is not validated at all.**

**3. The schema's own comment asserts a property the code does not hold.**
`schema_version.py:510` says `receipt` is *"ids only, never content
(V-RECEIPT-IDS-ONLY), so the table is a new carrier of nothing 0040's
enumeration does not already reach."* **Verified false as shipped:** a recall
with `tags_matched=('diagnosis:hiv-positive', 'a whole sentence about the
patient, with spaces and punctuation.')` stores both strings verbatim in
`policy_receipt.receipt`.

> ✅ **RE-READ AGAINST THE COMMITTED TEXT AND AT REST — research, 2026-09-15T00:03Z.**
> Verified against `181199d` (not the working tree the first pass measured, which
> is the point of the re-read): all **nine** boundary rows and all **eight**
> residual examples reproduce exactly; the schema comment now scopes
> `V-RECEIPT-IDS-ONLY` to the RANKING fields — where it is true — and names the
> identity fields *"bounded, not content-free"* with `receipt` as *"a second blob
> carrier beside `edges.json`"*; `V-POLICY-IDENTIFIERS-BOUNDED` stands at
> `specs/0027-semantic-hybrid-recall.md:838`; the guidance *"a policy tag names a
> policy, not a subject"* is in the spec and the CHANGELOG; and
> `test_an_identifier_shaped_disclosure_is_accepted_and_persisted_the_stated_limit`
> **asserts the limit rather than hiding it.** Nothing in §2b-ii-bis is left
> unverified. **From adoption the frozen-candidate rule binds research too:
> corrections queue as the next version.**

### ⚖️ RESOLVED at v14.1 — dev implemented the constraint AND corrected the comment

*Dev's decision, 2026-09-14, after reproducing the above by execution: constrain
at construction and state the limit honestly rather than choose one. **Verified
here as built**, every boundary:*

| | |
|---|---|
| `policy_id`, `policy_version`, each tag | must match `^[A-Za-z0-9._:-]{1,64}$` |
| refused | a sentence · a 400-char tag · a 65-char id · a `bool` · an empty tag · a tag containing a space · a 65th tag |
| accepted | a 64-char id · 64 tags |

**So the three fields take the bounded-identifier class** — research's row
holding `evidence_ref`, `source_id`, `origin` and
`confirmations.correlation_id` — and **`policy_receipt.receipt` is a second blob
carrier beside `edges.json` whose INTERIOR IS NOW SHAPED**: record ids, numbers,
booleans, ISO timestamps, and identifier-shaped host strings. **That shaping is
a gift to §2's sweep**: unlike `edges.json`, whose interior holds free prose, a
sweep over this blob can be TYPED — it knows what each position may contain, so
a value that is not one of those shapes is itself a finding.

### 🔴 The residual, stated at its true width — the charset forbids PROSE and permits RECORDS

Dev kept the honest half (`diagnosis:hiv-positive` passes and persists). **The
limit is sharper than that example, and a host needs the sharper version.**
Every one of these is accepted at v14.1 and persisted verbatim:

| accepted tag | what it is |
|---|---|
| `ssn:123-45-6789` | a US social security number |
| `dob:1974-03-02` | a date of birth |
| `dx:C50.9` | an ICD-10 diagnosis code |
| `phone:555-123-4567` | a phone number |
| `acct:GB29-NWBK-6016-1331-9268-19` | an IBAN |
| `salary:184000` | a salary |
| `addr:10-downing-st.london` | a street address |
| `diagnosis:hiv-positive`, `hiv`, `is-pregnant` | the original example and its short forms |

> **`[A-Za-z0-9._:-]` is precisely the alphabet of structured identifiers, which
> is precisely the alphabet of most structured PII.** The constraint eliminates
> free-text leakage, which is a real improvement — **and its residual is
> arguably the more dangerous category, because an SSN identifies a person more
> completely than a sentence about them does.** 64 characters is room for an
> IBAN and change.
>
> **The guidance this implies, which belongs in the host documentation rather
> than in a validator: a policy tag names a POLICY, not a SUBJECT.** No rule
> over an alphabet can enforce that distinction — it is a distinction about
> reference, not shape — so it must be said to the host in words and enforced by
> 0041's redaction reach, not pretended away by a charset.

> **§2b-ii's CONCLUSION IS UNCHANGED AND NOW BETTER SUPPORTED.** It disputed
> "closed by construction" on the ground that identifier-SHAPED is not closed —
> *"`diagnosis:hiv-positive` is twenty-one characters, uses only letters and
> `:-`, passes every rule proposed, and is a disclosure."* **That example now
> runs: it is accepted and persisted.** The classification research argued for —
> the class holding `evidence_ref`, `source_id`, `origin` and
> `confirmations.correlation_id` — is the correct row for all three fields, and
> `policy_receipt.receipt` joins `edges.json` as a blob §2 must reach into.

**This is also a PRODUCT finding, not only a spec one**, and 0027 v14 is
unreleased, so it can be fixed before it ships: either implement the constraint
the comment assumes, or correct the comment — but **V-RECEIPT-IDS-ONLY as
written is not true of the code beneath it**, and an invariant name that a
reader trusts is worse than no name.

### 2b-ii. The fourteenth table, classified BEFORE its DDL freezes

*Dev's reply to the sweep, 2026-09-13: commit 2's receipt table carries
`policy_id`, `policy_version` and `tags_matched` — **host-supplied strings** —
and will constrain them at the model to identifier shape (letters, digits,
`._:-`, ≤64 chars each), refused otherwise, so that "the table carries no free
TEXT column and lands in your enumeration as closed by construction."*

**Research endorses the constraint and disputes the classification.** The
tightening is worth shipping: it eliminates sentences, whitespace and
multi-clause prose, and it is strictly better than commit 1's non-empty check.
**But identifier-SHAPED is not closed, and §2c already draws exactly this
distinction.**

> **`ConfirmationActor` is closed because the permitted VALUE SET is finite and
> OURS. These three have an unbounded value set and only a constrained
> ALPHABET.** `diagnosis:hiv-positive` is twenty-one characters, uses only
> letters and `:-`, passes every rule proposed, and is a disclosure. **A charset
> forbids the shape of prose, not the content of a label** — and a label is how
> you say something about a person in few characters.

**So the correct §2b row for these three is the one §2 already has** — the class
holding `evidence_ref`, `source_id`, `origin` and `confirmations.correlation_id`:

| carrier | field | change |
|---|---|---|
| *v14 receipt table* | `policy_id`, `policy_version`, `tags_matched` | **host-supplied identifiers — §8's limit applies, not redacted here.** Identifier-shaped and length-capped by construction (commit 2), which is a real narrowing and not a closure |

**And `tags_matched` should be separated from the other two.** A `policy_id`
names an object the host owns and versions. **A matched tag is an assertion that
FIRED ON THIS RECALL** — the docstring's own words are *"which host tags fired
it"* — so it is a host-chosen label co-located with one user's retrieval.
Whether a given tag describes the policy's trigger, the query, or the user **is
the host's choice and not ours**, which under §2c's untrusted-input discipline
means it must be classified by its worst admissible value, not its intended one.

> **This does not block commit 2 and is not a design objection.** Ship the
> constraint. What changes is one line of documentation: the column set is
> **narrowed**, not closed, and §8's limit is the honest place for it to rest.
> **The risk of recording it as "closed by construction" is that the next sweep
> reads the word "closed" and skips the table** — which is precisely how eleven
> tables went eleven versions unexamined.

> ✅ **SETTLED 2026-09-13, same day.** Dev accepted both halves: commit 2 ships
> the constraint and records the row as **narrowed** — the class holding
> `evidence_ref`, `source_id`, `origin`, `correlation_id`, §8's limit applies,
> not redacted here — **and `tags_matched` is split out and named on its own**,
> classified by its worst admissible value under §2c. **The same words go into
> 0027's v14 amendment and the CHANGELOG line, so a host reads one
> classification in both places rather than two.** Recorded here because the
> disagreement was over a single word and the resolution is the reason the
> table stays inside the swept set.

> **What this sweep cost and what it bought.** It was run only because dev
> announced that receipt commit 2 adds a **fourteenth table**, and the obvious
> question — *can my enumeration see it?* — turned out to have the answer *no,
> and it could not see ten of the existing thirteen either.* **Three carriers in
> tables nobody had looked at, one of them an oracle this very spec orders closed
> elsewhere.** The rule that generalises: **a tool that exists to replace a
> hand-list inherits the hand-list's failure the moment its corpus is pinned to a
> literal.**

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| **target id** (host-supplied) | refuse, `ValueError` | refuse | **refuse — never a silent no-op** | an id for another `user_id` → refuse | **INV-5** |
| **`user_id`** | refuse | refuse | refuse | cross-user target → refuse | **INV-5** |
| **reason string** (host-supplied, stored) | permitted, stored empty | 🔴 **CLOSED VOCABULARY — v3.** This cell read *"length-capped"*, which **D1 superseded**: a length cap on free prose is exactly the hole D1 closed, since the content that matters is short. The value MUST be one of §11's allowed reasons | n/a | **prose smuggled into a content-bearing field** → the reason is stored on the `redacted` EVENT, never rendered into a prompt | **INV-6** |
| **data written by an older version** | a pre-0041 store has no `redacted` kind | a `state` that does not parse | baseline events carrying full json | **the whole existing corpus is in this class** | **INV-4** |

> **The third row is the one to read twice.** `ConfirmationActor` was closed as an
> enum precisely because a free-form string *"let a host smuggle prose past the
> constraints on the other fields"* (0008 §6b, finding 7). **A redaction reason is
> the same shape**, and this spec must not reintroduce the hole it is removing.

### 2c-ii. Assertions about reach

- **Consumers of `edge_event.state`: exactly one.** `why.py` parses it and diffs
  consecutive states. **`doctor.py` reads `edge_event` for reference integrity
  only and never touches `state`.**

  *Verified 2026-09-12 by READING the occurrences, not by counting them:
  `doctor.py` contains three matches for "state" and all three are prose — "the
  stated version", "the state the standing set requires", a comment. **A grep
  count alone would have read as a contradiction of this assertion.** Recorded
  because §2c-ii exists for claims that turn out wrong on checking, and this one
  looked wrong until it was read.*
- **Producers of `edge_event`: one choke point**, `_journal_edge_write`, plus
  `journal_baselines` at migration.
- **`content_digest` is not a vector and not reversible — it is a CONFIRMATION
  ORACLE.** It cannot reconstruct the text; given a candidate it verifies it.
  **Dropping the vector and keeping the digest would leave the oracle standing.**

## 2d. The derived inventory — 93 terminal identities, 73 carriers (v16.3; 86 and 66 before 0047's `Reply`, 84 and 64 before 0045's two fields)

*Generated by `0041-carrier-enumeration.py` §C. **Do not edit these lists** — re-run the script. Fields are TERMINAL identities: redacting `Edge.note` covers every container path that reaches it.*

### Carriers — where each one reaches disk

| model | storage discipline | text-capable fields |
|---|---|---|
| `AgreementRecord` | nested in `Edge` (inside a `json` blob) | 3 — `direction`, `lexicon`, `markers` |
| `Confirmation` | **ruled** (see §2e): `confirmations` | 5 — `correlation_id`, `edge_id`, `id`, `request_digest`, `user_id` |
| `ConsolidationOp` | is the row: `consolidation_ops` | 5 — `claimed_ids`, `lease_expires_at`, `operation_id`, `owner`, `user_id` |
| `ContributionDraft` | **ruled** (see §2e): `contribution_ledger` | 5 — `contributor_id`, `contributor_type`, `site`, `survivor_id`, `survivor_type` |
| `ContributionRecord` | is the row: `contribution_ledger` | 10 — `contributor_ref`, `contributor_type`, `evidence_ref_digest`, `id`, `identity_digest`, `op_key`, `site`, `survivor_id`, `survivor_type`, `user_id` |
| `Edge` | inside a `json` blob | 10 — `id`, `invalidation_reason`, `note`, `object`, `original_relation`, `outcome_counts`, `relation`, `subject`, `supersedes`, `user_id` |
| `Episode` | inside a `json` blob | 14 — `claimed_by`, `context_ref`, `date`, `date_end`, `date_start`, `edge_id`, `id`, `kind`, `lineage`, `operation_id`, `retired_reason`, `summary`, `supersedes_episode`, `user_id` |
| `Provenance` | nested in `Edge` (inside a `json` blob) | 3 — `evidence_ref`, `origin`, `source_id` |
| `SupersessionRefusal` | is the row: `supersession_refusals` | 6 — `incoming_edge_id`, `prior_edge_id`, `refusal_id`, `relation`, `rule_version`, `user_id` |
| `SupersessionRefusalDraft` | is the row: `supersession_refusals` | 3 — `incoming_edge_id`, `prior_edge_id`, `relation` |

### Excluded BY STORAGE, not by shape — 20 fields

> **Not one of these is constrained.** Each is clear only while nothing
> persists it. A storage site added to any of them makes it a carrier
> with no change to its declaration — so this list expires at any change
> to what is written, not only at a schema change.

| model | why | fields |
|---|---|---|
| `ConsolidationOutputDraft` | never written to disk | `date_end`, `date_start`, `summary` |
| `ContestedGroup` | a **view** assembled from rows, never written (§2e) | `prior_edge_ids`, `relation`, `subject` |
| `ContestedLinkage` | never written to disk | `edge_id`, `partition` |
| `CorrectionAuthorisation` | never written to disk | `kind`, `origin`, `principal`, `prior_edge_id`, `replacement_digest` |
| `OutcomeJudgmentDraft` | never written to disk | `context_ref`, `event_timestamp`, `summary` |
| `Relation` | never written to disk | `desc`, `name` |
| `SupersessionPlan` | never written to disk | `expected_state`, `operation_id` |

### ⚠️ "Carrier" here means CAN HOLD TEXT AND REACHES DISK — not "gets tombstoned"

**The 64 are the candidate set, not the treatment set.** Many are identifiers
(`id`, `user_id`, `request_digest`, `op_key`): they are text-capable and stored,
so the enumeration must return them, but §2's table is where each gets a
*treatment* — replaced, dropped, or **recorded as an explicit negative**.

**The enumeration's job is that nothing is missed; §2's job is that nothing is
mistreated.** Collapsing the two is how `Edge.original_relation` came to sit in
a negative row for two versions: it was classified *by its name* rather than by
what reaches it. **A field is a negative only when something checked what writes
to it** — which is what dev's round-1 reproduction does for the three above.

## 2d-ii. 🔴 THE TREATMENT MAP — what is REMOVED, as distinct from what CAN hold text

> **Round-2 F6 and F7 together.** §2d enumerates the **64 candidates**; this map
> is the **removal surface**. v3.2 conflated them, which is what made §11.3's
> INV-1 read as a content invariant. Ruled against dev's skeleton
> `cf814d849825ca0e` and the write-site sweep `200553ca29066610`.

| treatment | fields | basis |
|---|---|---|
| **REPLACE** with the marker | the content leaves **as the per-candidate table names them**; **`markers` per entry, arity preserved**; 🔴 **`Episode.kind`** | extractor- or host-supplied content. 🔴 **v5: this cell previously named `desc`, `text` and `payload` — NONE of the three is among the 64.** `Relation` is configuration and never persisted; `wiki.text` and the ledger `payload` are **DDL-level carriers under §2b**, not model fields. **The class sentence over-named and the TABLE IS THE AUTHORITY** |
| **CLEAR the keys** | `outcome_counts` | keys persist and export **verbatim**; the `Outcome` enum constrains `record_outcome` but **not the model and not import** |
| **DELETE the row** | the three digest / vector carriers | INV-7. Never copied into a receipt |
| 🔴 **v7: PER FIELD — §11.2 is the authority, and there is no single rule** | 🔴 **FOUR reason fields, three different contracts.** `Edge.invalidation_reason` and `Episode.retired_reason`: **PRESERVE if in the registry · else the new `redacted`** (rows 30/49; never the marker, and never `NULL` on the episode). `edge_event.reason`: the journal's existing closure, **EXTENDED** to the `redacted` kind. 🔴 **`source_revocations.reason`: REPLACED with the marker like any other prose — it has NO vocabulary** ⚠️ **v15 ANNOTATION — "it has NO vocabulary" is HISTORICAL as at v7, SUPERSEDED by §11.2 (v12, and v15's lift row).** The treatment that governs is §11.2's: stored prose is REPLACED WITH THE MARKER (not `redacted`, which is a `DISPOSITIONED_REASONS` value for rows 30/49 and none of D1's four), a vocabulary value is PRESERVED, and absence does not arise — the column is `reason TEXT NOT NULL`. **This carrier has no number in §2d-iii-bis**, whose rows 1–64 are model fields; it is a §2b side-table carrier. Cite it as *§11.2, `source_revocations.reason`*., and v6's single *"preserve if vocabulary"* cell was wrong for it | §11.2, built on the second seat's executed results |
| **PRESERVE** — identifiers, timestamps, traced-internal fields | each with its reason recorded, never a bare negative | §2d-iii |

**v16 (amendment `0047/0041-replies`):** three carriers join REPLACE, beside the existing `confirmations.request_digest`: `replies.text`, `replies.request_digest`, and `request_registry.request_digest` for every verb's registry row whose `target_edge_id` is the edge (0008 §6g). A `resolve` reply's NULL `text` stays NULL, the permitted treated-or-absent shape. Their per-candidate rows are §2d-iii-ter.

### 2d-iii. Why each PRESERVE is preserved — the reasons, not a bare list

**A recorded negative with no reason is how `json.original_relation` sat wrong
for two versions.** Every PRESERVE names what makes it safe:

| field(s) | the line that makes it safe |
|---|---|
| `AgreementRecord.direction` | ✅ `_direction_closed` **refuses** anything outside `("inbound","ambiguous","user_source")` |
| `site` ×2 | ✅ `contribution.validate_payload` **refuses** a site outside `SITES` |
| `contributor_type` ×2 · `survivor_type` ×2 | the literal `"edge"` at **every** write site, **including import's reconstruction** (`graph.py:514-515`, `portability.py:638`, `scope_linkage.py:354`) |
| `edge_event.kind` | five literals at the journal writers; **no import path today** |
| `rule_version` | the module constant `RULE_VERSION` at the single insert |
| `ConsolidationOp.owner` | product-generated `consolidate:<hex>` (`lifecycle.py:216`). ⚠️ the `Store` methods take `owner` as a **PARAMETER**, so a host driving the `Store` directly can pass anything; `consolidation_ops` neither exports nor imports, so it cannot travel |
| `ConsolidationOp.claimed_ids` | **episode IDs**, not content — *"every `claimed_id` belongs to `user_id`"*. Replacing them **destroys the lease's record of what it claimed**; `forget_user()` already erases them |
| `AgreementRecord.lexicon` | ⚠️ `_lexicon_pattern` bounds a **CHARSET** and not a value space. Preserved because redacting it breaks the version binding 0026-R7-1 rests on; **the limit is §8's** |
| `provenance.evidence_ref` · `source_id` · `origin` | host-supplied pointers; **§8's limit applies** |
| ids, digests, timestamps, `user_id` | identifiers and bookkeeping |

### 2d-iii-bis. 🔴 THE PER-CANDIDATE MAP — one row per carrier, with its resulting shape

> **Round-2 F6 asks for "one complete mapping from EACH candidate … with valid
> resulting shapes".** v4's §2d-ii was a five-row table BY CLASS: it named 32 of
> 64 individually and covered the rest with the phrase *"ids, digests,
> timestamps, `user_id`"* — **in the section whose own rule is that a recorded
> negative must name its reason.** The second seat held adoption on it and was
> right. **The table below is the authority; the class rows above are rationale.**
>
> **Every resulting shape here was VALIDATED UNDER THE MODEL, not asserted** —
> including the two that do NOT validate, which are recorded as results rather
> than as footnotes.

> **Completeness, asserted at generation:** 64 rows below (66 since v16.2: rows 65–66 APPENDED for 0045's `Edge.src` and `Edge.attv`; 73 since v16.3: rows 67–73 APPENDED for 0047's `Reply`, and the block now declares 73; EQUAL), derived from `carrier_enumeration_OUTPUT.txt`'s CARRIERS block at generation time; the block declares **64**; EQUAL. Rulings from research's `0041-treatment-matrix-RULINGS.md` (4d9e21a4893fc8cd) over dev's skeleton (cf814d849825ca0e) and traces (200553ca29066610); resulting shapes as research ruled them, each checked to VALIDATE under the model except where marked.

| # | candidate | where it reaches disk | ruling | resulting shape | the line that makes a PRESERVE safe / the basis |
|---|---|---|---|---|---|
| 1 | `AgreementRecord.direction` | nested in Edge (json blob) | **PRESERVE** | the value unchanged, byte for byte | `_direction_closed` REFUSES anything outside `(inbound, ambiguous, user_source)` |
| 2 | `AgreementRecord.lexicon` | nested in Edge (json blob) | **PRESERVE** | the value unchanged, byte for byte | the version binding 0026-R7-1 rests on; the charset pattern bounds a charset, not a value space — §8's limit |
| 3 | `AgreementRecord.markers` | nested in Edge (json blob) | **REPLACE (per entry)** | a list of N marker entries, arity preserved — 🔴 **INVALID until the uniqueness validator admits repeated markers**: `AgreementRecord(markers=[M, M])` is REFUSED today ("markers[1] duplicates …"); the validator change is BLOCKING for this row, not a footnote | content; `AgreementRecord` validator amendment (a CODE change) |
| 4 | `Confirmation.correlation_id` | RULED carrier -> confirmations | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 5 | `Confirmation.edge_id` | RULED carrier -> confirmations | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 6 | `Confirmation.id` | RULED carrier -> confirmations | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 7 | `Confirmation.request_digest` | RULED carrier -> confirmations | **REPLACE** | the marker, alone, as the whole value (validates: `Confirmation(..., request_digest=MARKER)`) | CLEAR has NO VALID SHAPE here: a required bare `str` — `None` is refused by the model and `""` by INV-8's CHECK at the database layer; REPLACE removes the oracle (INV-7), keeps the confirmation judgment (*"keep the split"*), validates today, and is self-describing (the marker says *redacted*; an emptied field says *nothing was here*). `content_digest`/`vec` are `edge_embedding` COLUMNS (§2b, DDL level, not among the 64): that row IS deleted |
| 8 | `Confirmation.user_id` | RULED carrier -> confirmations | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 9 | `ConsolidationOp.claimed_ids` | IS the row -> consolidation_ops | **PRESERVE** | the value unchanged, byte for byte | episode ids, not content — *"every `claimed_id` belongs to `user_id`"*; replacing them destroys the lease's record; `forget_user()` erases them (research 1b) |
| 10 | `ConsolidationOp.lease_expires_at` | IS the row -> consolidation_ops | **PRESERVE** | the value unchanged, byte for byte | a timestamp |
| 11 | `ConsolidationOp.operation_id` | IS the row -> consolidation_ops | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 12 | `ConsolidationOp.owner` | IS the row -> consolidation_ops | **PRESERVE** | the value unchanged, byte for byte | product-generated `consolidate:<hex>` (`lifecycle.py:216`); the `Store` methods take it as a parameter — a host driving the `Store` directly is outside the product API |
| 13 | `ConsolidationOp.user_id` | IS the row -> consolidation_ops | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 14 | `ContributionDraft.contributor_id` | RULED carrier -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 15 | `ContributionDraft.contributor_type` | RULED carrier -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | the literal `"edge"` at every writer incl. import's reconstruction (`graph.py:515`, `scope_linkage.py:354`) |
| 16 | `ContributionDraft.site` | RULED carrier -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | `contribution.validate_payload` REFUSES a site outside `SITES` (0014 §4a) |
| 17 | `ContributionDraft.survivor_id` | RULED carrier -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 18 | `ContributionDraft.survivor_type` | RULED carrier -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | the literal `"edge"` at every writer incl. import's reconstruction (`graph.py:514`, `portability.py:638`) |
| 19 | `ContributionRecord.contributor_ref` | IS the row -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 20 | `ContributionRecord.contributor_type` | IS the row -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | the literal `"edge"` at every writer incl. import's reconstruction (`graph.py:515`, `scope_linkage.py:354`) |
| 21 | `ContributionRecord.evidence_ref_digest` | IS the row -> contribution_ledger | **CLEAR** | the row KEPT, the field `None` (validates: `Optional[str]`) | the oracle, not the record — INV-7 disposes of the digest, *"keep the split"* keeps the ledger's absorption record; ruled by research over dev's DELETE-the-row (both wrong once, corrected against §2's *"nothing structural changes in the record tables"*) |
| 22 | `ContributionRecord.id` | IS the row -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 23 | `ContributionRecord.identity_digest` | IS the row -> contribution_ledger | **CLEAR** | the row KEPT, the field `None` (validates: `Optional[str]`) | the oracle, not the record — INV-7 disposes of the digest, *"keep the split"* keeps the ledger's absorption record; ruled by research over dev's DELETE-the-row (both wrong once, corrected against §2's *"nothing structural changes in the record tables"*) |
| 24 | `ContributionRecord.op_key` | IS the row -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 25 | `ContributionRecord.site` | IS the row -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | `contribution.validate_payload` REFUSES a site outside `SITES` (0014 §4a) |
| 26 | `ContributionRecord.survivor_id` | IS the row -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 27 | `ContributionRecord.survivor_type` | IS the row -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | the literal `"edge"` at every writer incl. import's reconstruction (`graph.py:514`, `portability.py:638`) |
| 28 | `ContributionRecord.user_id` | IS the row -> contribution_ledger | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 29 | `Edge.id` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 30 | `Edge.invalidation_reason` | json blob | 🔴 **v11: PRESERVE `None` · PRESERVE a registered reason · REPLACE EXISTING PROSE with `redacted`** — **three cases, because ABSENCE IS NOT CONTENT** | `None` stays `None`; a registered reason unchanged; existing prose becomes `"redacted"` — **never the marker** | 🔴 **v11 (round-5 finding 1): v7 said *"else the new registry value"*, which turns an ABSENT reason into a present one.** The marker is separately refused by a guard that ships — `sqlite.py:247` refuses any reason outside `DISPOSITIONED_REASONS`. **Redaction removes content; a field holding `None` has no content to remove, so the treatment does not reach it**
| 31 | `Edge.note` | json blob | **REPLACE** | the marker, alone, as the whole value (validates today: no pattern or length constraint on any of these — checked by construction) | content; the duplicated `edges.subject/relation/object` columns follow the json field (INV-2) |
| 32 | `Edge.object` | json blob | **REPLACE** | the marker, alone, as the whole value (validates today: no pattern or length constraint on any of these — checked by construction) | content; the duplicated `edges.subject/relation/object` columns follow the json field (INV-2) |
| 33 | `Edge.original_relation` | json blob | **REPLACE** | the marker, alone, as the whole value (validates today: no pattern or length constraint on any of these — checked by construction) | content; the duplicated `edges.subject/relation/object` columns follow the json field (INV-2) |
| 34 | `Edge.outcome_counts` | json blob | **CLEAR** | `{}` — an empty dict (validates) | round-2 F6: keys persist and export verbatim; the `Outcome` enum bounds `record_outcome` only |
| 35 | `Edge.relation` | json blob | **REPLACE** | the marker, alone, as the whole value (validates today: no pattern or length constraint on any of these — checked by construction) | content; the duplicated `edges.subject/relation/object` columns follow the json field (INV-2) |
| 36 | `Edge.subject` | json blob | **REPLACE** | the marker, alone, as the whole value (validates today: no pattern or length constraint on any of these — checked by construction) | content; the duplicated `edges.subject/relation/object` columns follow the json field (INV-2) |
| 37 | `Edge.supersedes` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 38 | `Edge.user_id` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 39 | `Episode.claimed_by` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 40 | `Episode.context_ref` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 41 | `Episode.date` | json blob | **PRESERVE** | the value unchanged, byte for byte | a timestamp |
| 42 | `Episode.date_end` | json blob | **PRESERVE** | the value unchanged, byte for byte | a timestamp |
| 43 | `Episode.date_start` | json blob | **PRESERVE** | the value unchanged, byte for byte | a timestamp |
| 44 | `Episode.edge_id` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 45 | `Episode.id` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 46 | `Episode.kind` | json blob | 🔴 **v6: PRESERVE if a RECOGNISED OPERATIONAL KIND · REPLACE if prose** | the kind unchanged when recognised; the marker when prose | 🔴 **v5's flat REPLACE BROKE H14, executed twice.** `sqlite.py:1592` refuses `delete_episode` on `kind == "outcome"`; replace the value and the refusal stops matching — **the chain head disappears, the next `record_outcome` writes `seq 1`, and targeted deletion is PERMITTED.** `sqlite.py:1512` is the same fence on `add_episode` and is lost the same way. **Recognised = the set the product's own writers produce (`interaction`, `outcome`, `corrected`), and it MUST BE CLOSED BY A REFUSAL at the model AND at import** — §2d-iv, and the 0006/portability amendment named at round 2 and not written |
| 47 | `Episode.lineage` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 48 | `Episode.operation_id` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 49 | `Episode.retired_reason` | json blob | 🔴 **v11: PRESERVE `None` · PRESERVE a registered reason · REPLACE EXISTING PROSE with `redacted`** — **three cases, because ABSENCE IS NOT CONTENT** | `None` stays `None` **and the episode stays ACTIVE**; a registered reason unchanged; existing prose becomes `"redacted"` — **never the marker** | 🔴 **v11 — v7's *"never NULL"* FIXED ONE DIRECTION AND BROKE THE OTHER, and it violated §4h, this spec's own rule.** `schema.py:872`: `Episode.active` **IS** `retired_reason is None`. Clearing an existing reason UN-retires (v7's concern, still correct); **writing `"redacted"` over an ABSENT one RETIRES AN ACTIVE EPISODE** — `None`/active=True → `"redacted"`/active=False, reproduced by the reviewer on the packaged model. 🔴 **AND `tests/test_0041_treatment_matrix.py:93` HAS ASSERTED THE CORRECT RULE ALL ALONG** (`after.retired_reason is None and after.active == before.active`, comment: *"the treatment touches content, never absence"*) — **the evidence was right and the spec text drifted away from it.** The verdict's sentence to design against: *forbidding the clearing of an existing retirement reason does not justify forbidding an already-absent one* 🔴 **AND THE FLIP REACHES `assertable`, NOT JUST THE RETIREMENT AXIS** (second seat's reproduction, beyond what the verdict named): `active` feeds `assertable`, **the shared predicate the text consumers call**, so a redaction that retired an active episode also removed it from what the product may assert. **The damage was never confined to one field's value** |
| 50 | `Episode.summary` | json blob | **REPLACE** | the marker, alone, as the whole value (validates today: no pattern or length constraint on any of these — checked by construction) | content; the duplicated `edges.subject/relation/object` columns follow the json field (INV-2) |
| 51 | `Episode.supersedes_episode` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 52 | `Episode.user_id` | json blob | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 53 | `Provenance.evidence_ref` | nested in Edge (json blob) | **PRESERVE** | the value unchanged, byte for byte | §2 excludes it; §8 states the limit (the content is one dereference away on the host's side) |
| 54 | `Provenance.origin` | nested in Edge (json blob) | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 55 | `Provenance.source_id` | nested in Edge (json blob) | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 56 | `SupersessionRefusal.incoming_edge_id` | IS the row -> supersession_refusals | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 57 | `SupersessionRefusal.prior_edge_id` | IS the row -> supersession_refusals | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 58 | `SupersessionRefusal.refusal_id` | IS the row -> supersession_refusals | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 59 | `SupersessionRefusal.relation` | IS the row -> supersession_refusals | **REPLACE** | the marker, alone, as the whole value (validates today: no pattern or length constraint on any of these — checked by construction) | content; the duplicated `edges.subject/relation/object` columns follow the json field (INV-2) |
| 60 | `SupersessionRefusal.rule_version` | IS the row -> supersession_refusals | **PRESERVE** | the value unchanged, byte for byte | one of the authority module's constants, `RULE_VERSION` or `WITHIN_EPISODE_RULE_VERSION`, chosen by the rule that refused (0003 §4c-iv); never content |
| 61 | `SupersessionRefusal.user_id` | IS the row -> supersession_refusals | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 62 | `SupersessionRefusalDraft.incoming_edge_id` | IS the row -> supersession_refusals | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 63 | `SupersessionRefusalDraft.prior_edge_id` | IS the row -> supersession_refusals | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 64 | `SupersessionRefusalDraft.relation` | IS the row -> supersession_refusals | **REPLACE** | the marker, alone, as the whole value (validates today: no pattern or length constraint on any of these — checked by construction) | content; the duplicated `edges.subject/relation/object` columns follow the json field (INV-2) |
| 65 | `Edge.src` | json blob | **PRESERVE** | the value unchanged, byte for byte | an episode id; it must survive so that 0045 §4d's guard can see the SOURCE's redaction (0045 §4f, v16.2) |
| 66 | `Edge.attv` | json blob | **PRESERVE** | the value unchanged, byte for byte | a producer identifier from 0045 §2c's closed grammar, no content (0045 §4f, v16.2) |
| 67 | `Reply.correlation_id` | RULED carrier -> replies | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 68 | `Reply.edge_id` | RULED carrier -> replies | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 69 | `Reply.id` | RULED carrier -> replies | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |
| 70 | `Reply.request_digest` | RULED carrier -> replies | **REPLACE** | the marker, alone, as the whole value | §2d-iii-ter: a reply's request digest binds its free text, so a surviving copy would still verify it (`0047/0041-replies`, v16.3) |
| 71 | `Reply.target` | RULED carrier -> replies | **PRESERVE** | the value unchanged, byte for byte | a resolve's challenge id (NULL for every other kind): structure, not content (§11.6.2: `target` PRESERVE, v16.3) |
| 72 | `Reply.text` | RULED carrier -> replies | **REPLACE** | the marker, alone, as the whole value; a resolve's NULL text stays NULL | §2d-iii-ter: the subject's own words about the edge, the first FREE-TEXT side column (`0047/0041-replies`, v16.3) |
| 73 | `Reply.user_id` | RULED carrier -> replies | **PRESERVE** | the value unchanged, byte for byte | an identifier (an id, a reference to an id, or a version/state token the product writes) |

> 🔴 **THREE ROWS ARE NOT INDEPENDENT.** `SupersessionRefusal.relation` and
> `SupersessionRefusalDraft.relation` **COPY the edge's relation**, so they
> follow `Edge.relation`'s ruling and must move with it. `Edge.relation` is
> **REPLACE** because it is not closed: **the model accepts
> `relation="told me in confidence: hiv-positive"`** — verified. Ingest closes
> it (refiling the unrecognised as `unclassified` + `original_relation`), but
> **`store.add_edge` and import do not**, and §2d-iv's test is whether something
> REFUSES, not whether some path is careful.

### 2d-iii-ter. The reply carriers (v16, amendment `0047/0041-replies`)

> These rows govern as §2d-iii-bis's do. They are kept apart because §2d-iii-bis is checked row for row against the carrier enumeration, and the `replies` table does not exist until 0047 is implemented. At implementation they join §2d-iii-bis, and the census output moves by exactly these carriers.

| candidate | where it reaches disk | ruling | resulting shape |
|---|---|---|---|
| `replies.text` | the `replies` table (0047) | **REPLACE** | the marker; a NULL `text` (a `resolve` row) stays NULL. The first side-table column in the map that holds FREE TEXT |
| `replies.request_digest` | the `replies` table | **REPLACE** | the marker. A reply's request digest binds its free text, so a surviving copy would still verify it |
| `request_registry.request_digest` | the request registry (0008 §6c, §6g), every verb's row whose `target_edge_id` is the edge | **REPLACE** | the marker |
| the backfilled registry copy of `confirmations.request_digest` | the request registry | **REPLACE** | the marker (the registry step backfills an already-redacted confirmation's row with the marker) |

*The amendment's own statement of these rows:* v1.3: three more rows, `replies.request_digest`, `request_registry.request_digest` and the backfilled registry copy of `confirmations.request_digest`, each REPLACE, shape “the marker”; and one row: `replies.text`, REPLACE, resulting shape “the marker”; **the first side-table column in the map that holds FREE TEXT** (every other side row holds a digest, a closed value or an id), said plainly

> **Annotation (research, 2026-10-14, at 0008 v7's implementation, dev's `f20840f`; re-derived at `a2dc7b0`). The sentence above is kept as written. For the two registry rows it holds in this form:** they are implemented as ONE path, `request_registry.request_digest` (the backfilled copy lands in the same column), and they did NOT join §2d-iii-bis as numbered rows. No model describes a registry row, so the carrier enumeration, which places every §2d-iii-bis row, cannot place this one. The row joins the DDL-ONLY treated side paths instead, beside §11.2's `source_revocations.reason`: it is in `SIDE_TABLE_TREATMENTS` (`src/veracium/redaction.py`), and the redaction finds it by `target_edge_id`. The census output moved in section A only, from 17 to 19 tables: the registry's seven columns, and `confirmations`' five act TEXT columns (0008 §2a). The 84 model identities and the 64 + 20 split did not move. The two reply rows still wait for 0047's implementation, and where they join is measured then. Evidence: research's `proposals/evidence-0008-t3/` (the section-A diff, `e987e5c` to `a2dc7b0`).

### 🔴 2d-v. WHAT READS THIS FIELD? — the question the map did not ask, and the two lines that answer it

**Round-3 F1/F2 and four executed simulations. Every one is the same shape: a
field that LOOKS like content and is LOAD-BEARING, so a treatment on it changes
something other than content.**

| # | the field | what reads it | executed result |
|---|---|---|---|
| **1** | `Episode.kind` | **a REFUSAL** — H14's `delete_episode` fence at `sqlite.py:1592` | 🔴 **chain head gone · next append `seq 1` · targeted deletion PERMITTED** |
| **2** | `Episode.kind` | the same fence on `add_episode`, `sqlite.py:1512` | 🔴 **refuses `kind="outcome"`, ACCEPTS the marker** |
| **3** | `Episode.retired_reason` | **a DERIVED PROPERTY** — `active` *is* `retired_reason is None`, and `active` feeds `assertable` | 🔴 **redacting a `None` reason RETIRES the episode** |
| **4** | `Edge.subject` / `relation` | the supersession guard at `graph.py:333` | 🔴 **a redacted record can NO LONGER BE CORRECTED** — a live replacement is refused for not sharing the prior's `(user, subject, relation)` |
| **5** | `Edge.subject` / `relation` | the same guard, both sides redacted | 🔴 **a MARKER-CARRYING replacement is ADMITTED** — the guard compares equal |
| **6** | `Edge.object` | the correction digest at `sqlite.py:1052` | ✅ mostly safe — the digest binds the **replacement**, not the prior. But an authorisation minted **for the marker** admits |
| **7** | `Edge.relation` | **a SAFETY disposition** — `quarantined` is `relation == QUARANTINE_RELATION or disclosure == QUARANTINED` | ◐ **ingest sets BOTH, so ingest-quarantined edges survive.** 🔴 **But a relation-only quarantine is constructible via `add_edge` with no refusal, and redacting it PROMOTES the edge out of quarantine** — from `UNVERIFIED THIRD-PARTY CLAIMS` into `RELEVANT DETAIL` |

### The seven collapse to TWO missing enforcements

> **1. INV-11's MIRROR — no non-redaction write may INTRODUCE the marker.**
> Rows 5 and 6 are admitted *only* because nothing refuses a marker-valued
> write. **The mirror was named in v4's §4b and has never been written**, and it
> is the single line that closes both.
>
> **2. §2d-iv's CLOSURE — the discriminator must be closed by a refusal.**
> Rows 1, 2 and 7 are all *"a comment named the set and nothing enforces it"*.
> **Without closure, no treatment can tell an operational value from prose**, so
> every guard keyed on the field is downstream of a comment.

**Neither is a redaction feature. Both are prerequisites that redaction made
visible**, and §11.4 carries them as named amendments rather than as notes.

### 🔴 AND ONE CONSEQUENCE THE SPEC MUST STATE TO THE CALLER (row 4)

**A redacted record can no longer be corrected.** The supersession path requires
a replacement to share the prior's `(user, subject, relation)`, and after
redaction the prior's are markers. **§8 must say so: redaction is not only
removal, it is the END OF THE RECORD'S CORRECTABLE LIFE** — and a caller who
redacts to fix a mistake needs to know that the fix can no longer be filed
against the record.

### 🔴 2d-iv. A SET IS CLOSED WHEN SOMETHING REFUSES A VALUE OUTSIDE IT

**`Episode.kind` is REPLACE because its closure is a comment:**

```
kind: str = "interaction"        # "interaction" | "outcome"
```

The model **accepts and round-trips** `kind = "told me in confidence:
hiv-positive"`, and `import_memory` **accepts such a record from a file and
stores it verbatim** — both executed. It becomes PRESERVE **only once import AND
the model close it**, which is a **named amendment to 0006/portability**.

> **FIFTH instance of one shape in this spec's lineage:** `TEXT NOT NULL`
> forbidding `""` · a leading NUL making the marker unproducible ·
> `Episode.retired_reason` · `outcome_counts` · `Episode.kind`. **Each is a
> description of an intention mistaken for an enforcement, and in each the
> description is why nobody wrote the refusal.**
>
> **The rule this spec now carries: a comment, a docstring, a type alias and a
> naming convention are not closures. Only a refusal is. Every "closed set" here
> names the line that refuses, or it is not called closed.**

**v16 (amendment `0047/0041-replies`):** the reply writer (0047) is a WRITE PATH that must refuse: a `kind` outside the closed set; and INV-11's mirror, an ordinary reply whose text carries the marker (a non-redaction write may not introduce it).

## 2e. The residual rulings — decided against the WRITE PATH, not the field names

Thirteen fields shared a table's column names without being a row. **They were
held in an UNRESOLVED tier rather than defaulted**: guessing non-carrier loses a
real carrier, and that is the direction that costs something. Each is ruled with
its evidence, and a ruling that outlives its question fails the run.

| model | ruling | evidence |
|---|---|---|
| `Confirmation` | **carrier** | subset failed on `replayed` **alone**, which `schema.py:149` comments *"runtime only: True when returned for a replay"* — not a column. The model **is** the `confirmations` row; `INSERT` at `sqlite.py:588` |
| `ContributionDraft` | **carrier** | subset failed on `contributor_id` **alone**, which is `INSERT`ed into the column `contributor_ref` — `sqlite.py:1236` documents its own rename. The draft's content reaches disk under a different name |
| `ContestedGroup` | **not a storage site** | `exposed`, `linkage` and `prior_edge_ids` are not columns of anything: it is a **view assembled from rows**, never written. Its text is `Edge`'s, already carried. `ContestedLinkage` sits inside it and therefore inherits nothing — **an unresolved container cannot confer persistence on what it holds** |

> **`ContestedGroup.partition` greps clean in `store/` for a reason worth
> recording: every hit is `str.partition()`.** Our own vocabulary, someone
> else's sense — the false-positive shape that grows with the size of the moat.


## 3. Trust-class matrix — REQUIRED, blocking

**Enumerate from `EvidenceAuthor` and `Disclosure` at implementation time, not
from this table.** The operation is uniform across classes by design:

| author class of the target | redaction permitted? | rationale |
|---|---|---|
| `USER` | **yes** | the subject's own content is the primary case |
| `SYSTEM` | **yes** | derived content can carry the same text |
| `ASSISTANT` | **yes** | same |
| `THIRD_PARTY` | **yes — the motivating case** | C0's correspondents |

> **Redaction does NOT consult the authority ladder, and that is deliberate.**
> `permitted()` governs who may RETIRE a record — a claim about truth. Redaction
> makes no claim about truth; it removes content. **Gating redaction on authority
> would mean a low-authority party could not have their own content removed**,
> which inverts the purpose. **Authorisation is §3b's subject, not the ladder's.**

## 3b. Authorization and scope

Under C1's ruled model — embedded, operator and policy controller the same party
— **redaction is a host-invoked operation**, like `forget_user`. The library does
not decide who may request it; the host does, and the spec says so rather than
implying a model the deployment does not have.

**Out of scope for v1:** a self-service path for a data subject who is not the
operator. **C0 named that party and C2 ruled they are not separately modelled in
v1**; when C2 changes, this section is the one that reopens.

**v16 (amendment `0047/0041-replies`): one new host surface, `confirm_notice(user_id, notice_id)` (§11.6),** scoped to that user's notices. It is the only path by which a notice from a default-mode file changes held content, and it applies the notice as a redaction by this store. Its exposure on other surfaces (MCP, CLI) is not decided by this amendment.

## 4. Behaviour

### 4a. The operation

`redact(user_id, *, edge_id | episode_id, reason) -> RedactionReceipt`

Single transaction. Every carrier in §2 or none.

### 4b. The tombstone — 🔴 v4: THE MARKER IS NOT RESERVED, AND SAYING SO DID NOT MAKE IT SO

> 🔴 **ROUND-2 F2, EXECUTED.** v3.1 claimed *"a leading NUL makes it unproducible
> by the extractor, by an LLM body, and by any host string that survives
> `sanitize_llm_body`."* **All three are false.** Verified: `sanitize_llm_body(MARKER)
> == MARKER` — it rewrites only the wiki-compile marker prefix — and `remember()`
> with an extractor emitting `object == MARKER` **stores an edge whose object is
> the marker, with no redaction anywhere.**
>
> **This is the SECOND time in this spec that a property was asserted of a
> mechanism that does not hold it** — after `TEXT NOT NULL` was claimed to forbid
> `""`. Both times the sentence was the reason nobody wrote the enforcement.

**Reservation is not a property of the bytes. It is a REFUSAL AT EVERY WRITE.**

#### 🔴 v7 — THE ATTESTATION RULE, and it settles three things that were "owed"

> **THE MARKER IS NOT SELF-AUTHENTICATING. THE REDACTION RECORD IS THE
> AUTHORITY.** A field is REDACTED if and only if a redaction record (§4b-ii)
> names that record and that field. A field holding the marker byte-string with
> **no** such record is an **UNATTESTED MARKER**: bytes that carry no user
> content and confer no redacted status.

**Why the spec could not settle the three rows below without it.** Each of them
asked *"what does the marker mean here?"* and the marker cannot answer — it is a
byte string anyone could have stored, and `sanitize_llm_body(MARKER) == MARKER`
proved at round 2 that the product never stopped them. **Keying the guarantees
on the RECORD instead of the bytes makes all three answerable at once, and it
changes INV-11: the write-refusal keys on ATTESTED redaction, not on the byte
string.** Without that change a pre-existing marker-holding row becomes
permanently unwritable and reads to every consumer as a tombstone the owner
never asked for.

| | |
|---|---|
| **representation** | unchanged: the exact byte string `\x00veracium:redacted\x00` |
| **reservation** | 🔴 **INV-11's MIRROR: a NON-REDACTION write MAY NOT INTRODUCE THE MARKER.** Enforced at every ordinary write path and at **every import boundary**, refusing loudly. INV-11 forbids an ordinary write to a field whose redaction is *attested*; this forbids an ordinary write *introducing* the marker. **Neither implies the other and v3.1 had only one** |
| **pre-existing rows** | 🔴 **RULED v7 — ADMITTED AS UNATTESTED MARKERS; the migration neither refuses nor quarantines.** Rows already holding the marker byte-string at migration carry no redaction record, so by the attestation rule they are **not redacted**: they stay writable, they are not tombstones, and INV-11 does not fence them. The migration **enumerates them into its report** so an operator can see what the store holds. **The three options v6 offered the owner are all withdrawn as wrong**: refusing the migration bricks a store over a byte string the product never forbade; quarantining silently reclassifies the owner's own content; and *accept-and-flag* alone still leaves INV-11 keyed on the bytes, which freezes the row and renders it as redacted. 🔴 **v8 — RULED BY THE OWNER 2026-09-15: THE REPORT IS ADVISORY, NOT BLOCKING.** *"Make the migration report advisory, not blocking."* **The upgrade proceeds; the report enumerates the rows and an operator reads it.** **Stated plainly rather than left as a preference: this means a store CAN BE UPGRADED WITH UNATTESTED MARKER ROWS IN IT and nothing stops the operator — and the attestation rule is why that is right.** Those rows are not redacted, are not tombstones, and stay writable, so the report tells an operator about **content they already own**, not about damage. **A blocking report would have made the product refuse an upgrade over a byte string it never forbade anyone from storing** |
| **nested shapes** | 🔴 **two `agreement.markers` entries replaced by one marker FAIL the uniqueness validator.** Replacement must preserve arity, or redaction of a list field is refused by a validator the spec never mentions |
| **legitimately empty** | 🔴 **RULED v7 — REDACTION NEVER WRITES `""`, so the ambiguity does not arise.** Every REPLACE writes the marker; every CLEAR writes `NULL` where the column admits it. `""` is therefore **never a redaction outcome**, which is precisely what INV-8's CHECK enforces and what `TEXT NOT NULL` never provided. A legitimately empty field keeps whatever its own column rule allows and redaction does not touch it. **Confirmed against a second enforcement**: `revocation_sweep.py:637` already refuses a `retired_reason` that is not *"a non-empty str"*, so `""` is independently unreachable on that field today |

#### 🔴 v7 — THE REGISTRY EXTENSION rows 30/49 REQUIRE, and the FOUR sites that must move together

Rows 30 and 49 write `"redacted"` into fields whose vocabulary is
`schema.DISPOSITIONED_REASONS`. **That value does not exist today, and adding it
to one place breaks the product at import.**

| site | what it does today | what the extension owes it |
|---|---|---|
| `schema.py:570` `DISPOSITIONED_REASONS` | a **dict** of 7 reasons → `"drop"` / `"retain"` | add `"redacted": "drop"`. **A redacted record's wiki must not be retained** — the wiki may carry a derivation of the very content being removed, and `WIKI_RETAINING_REASONS` is the mechanism |
| 🔴 `asof/resolve.py:113` | an **IMPORT-TIME** gate: `if set(RESOLUTION) != set(DISPOSITIONED_REASONS): raise ImportError` | add `"redacted"` to `RESOLUTION` **in the same change**. Its own comment states the rule: *"an eighth reason fails BOTH this gate and the registry's own totality test … a new reason must be dispositioned TWICE (V-TOTAL)"*. **Extending the registry alone makes `import veracium` fail** |
| `asof/resolve.py` outcome | — | **`(NOT_RETURNABLE, TAG_REDACTED_EXCLUDED)`**, following `revoked_source`'s precedent: both are rights-driven removals, and an as-of read must not serve a tombstone as a historical answer |
| `tests/test_0004_wiki_revocation.py:101` `producer_reachable` | enumerates the producers | **redaction becomes a producer**; add `"redacted"` or `test_invalidation_reason_registry_is_total` fails |
| `doctor.py:263` | flags a retired edge whose reason is outside the registry | **no change needed** — it goes quiet once the value is registered. Named here because it is the check that would otherwise report every redacted record as damage |

> **This is the §2d-iv rule paying out in the other direction.** The rule said a
> set is closed only when something REFUSES a value outside it. `DISPOSITIONED_
> REASONS` **is** properly closed — by `sqlite.py:247`, by the import-time gate
> and by the totality test — **and that is exactly why this spec cannot write a
> new value into those fields without amending the registry.** A closed set
> costs something to extend, and the cost is the evidence that it was closed.

### 4b-ii. The episode redaction record (F3)

**The API accepts an edge or an episode; §4c defines only an edge journal
event.** `edge_event` is keyed by `edge_id` and cannot carry an episode, so an
episode redaction today would be durable in the record and **invisible in the
journal** — the asymmetry the reviewer named.

| | |
|---|---|
| **durable record** | an `episode_event` row of the same shape as `edge_event` (`episode_id`, `kind`, `reason`, `state`, `recorded_at`), written in the redaction transaction. **`reason` is D1's shape and takes D1's closed vocabulary** — this is the fourth instance (§9b/D1) |
| **receipt fields** | `redacted_kind` (`edge`/`episode`), the target id, the carrier fields cleared, the marker version, the store version **before and after**, and the surviving derived records F6 requires the caller be told about |
| **repeat calls** | **idempotent by content, not by attempt.** A second redaction of an already-redacted target writes **no** new event and returns the original receipt with `repeated=True`. Redaction is not an append-only log of intentions; a log of repeats is itself a signal about the target. 🔴 **v7 — AND WHEN THERE IS NO ORIGINAL RECEIPT TO RETURN.** A record redacted before receipts existed, or an attested redaction whose receipt was never stored, has none. **The call returns a RECONSTRUCTED receipt — `repeated=True` AND `reconstructed=True`** — carrying only what the redaction record itself supports (`redacted_kind`, the target id, the fields the record names, the event's `recorded_at`) and **explicit `None` for every field it cannot support** (the store version before and after, the marker version in force at the time). **Nothing is inferred and nothing is fabricated**: a receipt that guesses the store version is worse than one that says it does not know. An **unattested** marker is not an already-redacted target at all — the call proceeds as a first redaction |
| **repopulation** | 🔴 **v9 — KEYED ON THE RECORD, NOT THE BYTES.** An ordinary write to a field whose redaction is **ATTESTED by a redaction record** is **refused**, not merged; **a write to an UNATTESTED marker SUCCEEDS** (§4b's attestation rule). Without the refusal the tombstone is advisory: `remember()` on the same subject/relation would supersede an attested redaction back into content. **v8 still read *"whose target field currently holds the marker"* — the pre-attestation rule, stated as current three sections after the rule that replaced it** |

> 🔴 **v15 — A WITNESSED RECEIPT CARRIES TWO FACTS, AND NEITHER STANDS IN FOR THE OTHER (round-9 R9-05).**
> A redaction applied here from an imported notice has an ORIGINAL (the source's redaction) and an APPLICATION (this
> store's). Round 9 measured the original's fields filled with the destination's counters: a source redaction at
> store versions 1→2 reported as 3→4, with the import's reason and time. Those were genuine local values in the
> wrong fields.
> - **Original-receipt fields** — reason, `recorded_at`, the marker version, the store version before and after, the
>   event reference — are **source-supplied and NULLABLE.** Each is the value the foreign body holds, or `None`
>   where the body does not support one. A supported marker version is retained. Nothing is inferred from local
>   state (the v7 rule above, applied to the imported case).
> - **Application fields** — when, at which local store versions, and under which local event this store applied
>   it — are **local**, and are reported under their OWN names, never in the original's fields.
> - The receipt's JSON shape changes accordingly: an unsupported original field serializes as `null`. The
>   CHANGELOG states the shape change.
> - **Local application facts stay local.** They are in the receipt and the store, and are NOT exported: §4g's
>   requirement is that the FOREIGN notice travel consistently, and a destination's application history has no
>   consumer downstream.

> ⚠️ **The repopulation rule is the one with teeth, and it is a constraint on
> the WRITE path, not on redaction.** Redaction that does not change what
> subsequent writes may do is a delete with extra steps.

### 4b-iii. Readers — the inventory was incomplete (F3)

**Journal snapshots feed the 0030 classifier through `edge_state_at()`, and a
plain sentinel currently becomes `MALFORMED`.** A redacted historical read would
therefore not report *redacted*; it would report *corrupt*, which is a different
claim about the store and an alarming one.

| reader | redacted outcome |
|---|---|
| `edge_state_at()` / 0030 classifier | a **`REDACTED` state**, distinct from `MALFORMED`. The classifier must be taught the marker; a sentinel it does not recognise is indistinguishable from damage |
| `recall` | the record is **not returned**. Its absence is not concealment — §4d's existence fact is preserved in the journal, which is where it was already disclosed |
| `describe_procedures` | reports the procedure as redacted rather than omitting it, **subject to the existing visibility restrictions, which are unchanged** — redaction must not become a way to see that a record exists that the caller could not otherwise see |
| `why` | renders the event with D1's vocabulary reason; no free prose |
| `export` | D2 governs; F5 defines the import contract |

**The existing visibility restrictions are preserved in every row above.** A new
state that is visible where the record was not is a disclosure channel, and it
would be introduced by the feature whose purpose is removing disclosure.

> 🔴 **v15 — THE TABLE ABOVE NAMES READERS; THE RULE BINDS EVERY READ (round 10's sweeps, P-READ).** The rows
> above were read as a list, and round 10 measured paths the list does not name returning or re-deriving redacted
> records. **The contract is one rule: every reader and every derivation of stored content excludes ATTESTED
> targets AT ITS READ, by the attestation record (`redacted_targets`), and says so by name.** A closure that holds
> only because the marker happens to break a scope, date or identity match is INCIDENTAL, and is made explicit.
> The instances round 10 measured, each now bound by a cell:
> - **`recall` without a query (proactive)** — the `recall` row above already covers it. It returned redacted edges
>   and episodes as marker lines in three of its four sections; the fourth (dated commitments) dropped them only
>   because the marker removed the date it selects on.
> - **consolidation** — cold selection excludes attested episodes, and the claim re-checks under the write
>   transaction (§8, v15).
> - **expiry in `maintain`** — skips attested targets. Without this, one redacted durable edge stopped expiry for
>   its user on every run.
> - **`compile_wiki`'s RETURN** — a body drawn from a target attested during the compile is never returned (§4e's
>   publish rule, extended to the value handed back).
> - **semantic backfill** — D3, at the read.
> - **derived WRITES** (dispute, `record_outcome`, `correct`) — refuse an attested target, decided under the
>   transaction that writes.
> - **`describe_procedures`** — measured, and holds (the row above).

### 4c. The journal — the decision this spec exists to make

**`edge_event.state` holds the edge's FULL JSON as found** (0029 V-BASELINE:
*"the bytes, not a re-serialization"*), and every write journals through the same
choke point. **So redacting the live row alone is cosmetic: every prior version
remains in the journal, in the same file.**

**RULED APPROACH: tombstone `state` on every event for the redacted edge, and
append a new `redacted` event recording the redaction.**

`created` → `mutated` → **`redacted`**, with its own `seq`, `txn`,
`recorded_at`, and the reason.

**Why this is not a hole:** the journal exists to record the sequence of writes,
and **a redaction is a write.** Removing content while leaving no record of the
removal would be the hole; recording the removal preserves the property the
journal is for. **It composes with the administrator ruling already landed
(`f4d607a`): the journal was never tamper-evidence against the operator, so
nothing that was being claimed is lost.**

**Cost, stated:** `veracium why` can no longer show WHAT a redacted edge said,
only that fields moved and when. **`why` must render "redacted" and must not
fail** — see INV-3.

### 4d. What redaction does NOT do

- **It does not delete rows.** Chains, seqs and references are untouched.
- **It does not retire, quarantine or supersede.** Those are entitlement
  operations; redaction is not one, and conflating them would put a
  content-removal request on the trust surface.
- **It is not reversible.** A reversible redaction is not a redaction.
- **A redacted edge remains recallable** — structurally present, content absent.
  Otherwise redaction becomes deletion by another name and reopens every fence.

### 4e. Delayed writers — 🔴 v4: THE EXEMPTION IS WITHDRAWN AND MY OWN FIX WAS THE SAME BUG

> 🔴 **ROUND-2 F1a, EXECUTED at the pin by the second seat. Both halves of v3.1's
> §4e are wrong.**
>
> **(1) The semantic-rebuild exemption does NOT hold.** v3.1 called it *"exempt
> by construction"* because `upsert_embedding` re-reads the live row and refuses
> on a digest mismatch. **It holds only the INSTANCE lock, and its `SELECT`
> opens no transaction** — verified: `with self._lock:` then `SELECT`, then
> `INSERT`, with no `BEGIN IMMEDIATE`. Two `Memory` instances on one file, with
> B committing a tombstone and deleting the embedding between A's `SELECT` and
> A's `INSERT`: **A reports success and the stale vector is STORED, under the
> ORIGINAL content digest, while the live edge is the tombstone.** `V-FRESH`
> excludes it at read — *"excluded but stored"*, which is not what an exemption
> claimed.
>
> **(2) MY FIX FOR THE WIKI WAS THE SAME BUG.** v3.1 prescribed *"capture
> `v_begin` before `_grounded_inputs`, refuse to publish if it moved."*
> **`set_wiki` takes `store_version` as a PARAMETER** — read outside, passed in,
> written under the instance lock in a single statement. So "captured then
> compared" is itself a **compare-then-act race**: the store can move between
> the comparison and the commit. **I diagnosed a comparison bug and prescribed a
> comparison.**

**The rule, restated so it is about TRANSACTIONS and not about comparisons.**

> **A read-compute-publish path must make its READ and its PUBLISH one
> transaction under the DATABASE lock. An instance lock does not serialise
> across connections, and a captured value compared later is not a guard.**

**Two shapes the code admits, named by the second seat from what is there:**

| shape | |
|---|---|
| **`BEGIN IMMEDIATE` before the read** | the read and the write execute in one transaction under the database lock |
| **one statement** | `INSERT … SELECT … WHERE` the live digest still matches — the check and the write are indivisible because they are the same statement |

**Both paths owe this: the embedding upsert AND `compile_wiki`'s publish.**
Neither is exempt, and **§4e no longer lists an exemption at all.**

> ⚠️ **The generalisation stands and is now better evidenced.** *Read state → do
> slow work outside the transaction → write a result stamped current.* v3.1
> named the shape and then granted an exemption to the one path it examined,
> **on a guard that a second connection defeats.** An exemption is a claim about
> concurrency and cannot be read off a single-connection reading of the code.

### 4f. Locating affected receipts — 🔴 v4: THE EXACT-COVERAGE CLAIM IS WITHDRAWN

> 🔴 **ROUND-2 F5, EXECUTED on a real absorption** (prior *"Acme"*, incoming
> *"Acme Corp"*). v3.1 said step 1 was *"exact for current-domain receipts"*.
> **It is not exact for ANY domain, and the reasons are structural:**
>
> | step | what the reproduction found |
> |---|---|
> | **1. recompute the digest** | the logical digest covers **the whole plan** — incoming, upserts, invalidations, refusals — and **is not recoverable from the target alone** |
> | **2. scan `response` for the target id** | the current domain `veracium.supersession-request.v2` records a response of **COUNTS ONLY** (`inserted_incoming`, `invalidated`, `refused` → integers). **There are no ids in it to find** |
> | **3. follow the ledger and refusals** | **neither `contribution_ledger` nor `supersession_refusals` carries an `operation_id` column.** The join reaches the SURVIVOR and never the RECEIPT |

**So the selection rule has no exact tier, and v3.1's table implied one.**

| | |
|---|---|
| **today** | 🔴 **every unlinked receipt gets the CONSERVATIVE outcome.** `receipts_complete=False`, the domains named, and the caller told which class may retain a digest over redacted content. **This is now the ordinary case, not the edge case v3.1 presented** |
| **forward obligation** | durable association must be BUILT: an `operation_id` on the ledger row, **or** an `ids` field in the response. **Until one exists, no version of this spec can promise receipt coverage** |
| **the receipt itself** | 🔴 **must NOT carry the removed content digest.** A receipt that names what was removed by its digest is an oracle for the removed content |

> **What this costs the spec, stated plainly:** §8's success claim narrows again.
> Redaction removes content from the named carriers; **receipts containing a
> digest derived from that content may survive, and the caller is told so.**
> That is weaker than v3.1 and it is what the code supports.

### 4g. The import contract for redaction events (F5)

**D2 settles what TRAVELS. It does not settle how a destination ACCEPTS it**,
and an export shape without an import contract is a format change presented as a
guarantee. **A format-version bump alone establishes none of the properties
below** — it announces that the bytes differ, not what a receiver must do.

**Binding.** A redaction event names a record. The destination may hold that
record, hold a different version of it, or not hold it at all.

| destination state | outcome |
|---|---|
| holds the record | apply the redaction **in the same transaction as the record's import**. Records and their redaction state **commit together or not at all** — a window in which the record exists un-redacted is the exact harm this spec exists to prevent ⚠️ *v16: for an IMPORTED notice this row is superseded by §11.6's table: over a held target, a default import records the notice PENDING; it is applied only in a trusted restore whose file shows the redaction, or by `confirm_notice`.* |
| holds a **different version** | redact it anyway when the event's target id matches, and record an **inconsistent-notice** flag on the imported event. Content-derived divergence is not grounds to keep content the source says was redacted |
| **does not hold** the record | import the event as a **standing notice**, not a no-op. If the record arrives later it is redacted on arrival. **Dropping the event makes redaction order-dependent**, and import order is not something either side controls 🔴 **v3.1 — EXECUTED, and the row is REPRESENTABLE BUT NOT YET HONEST.** The store accepts a journal event whose `edge_id` names no row (`edge_event` declares no foreign key, `PRAGMA foreign_keys` is 0) and `edge_events(user, edge_id)` returns it — so a standing notice can be written and read today. **But `doctor` reports it as an ERROR** (check `refs`: *"journaled edge id(s) with no row"*), which is correct for every case that existed before this spec and wrong for this one. **As written, row 3 makes a healthy store permanently fail its own health check**, and an operator's rational response to a permanent error is to stop reading the errors. §11.4 amends 0029's `refs` check so a `pending` notice of kind `redacted` is EXPECTED rather than an orphan — a standing notice is the journal outliving its subject **on purpose**, which is the one case 0029's wording was not written against. |

> 🔴 **v15.6 — A NOTICE NEVER REMOVES CONTENT ON AN UNTRUSTED FILE'S WORD, AND A FILE THAT PAIRS A NOTICE WITH ITS
> RECORD UNREDACTED IS REFUSED (internal finding `0041-PA1`, 2026-10-13; the owner's rulings: fail closed, all arms).**
> The three rows above bound a notice to a bare target id. At v15.5 they applied in both import modes, so a
> default-mode file carrying one notice redacted the user's own fact; a standing notice refused the user's own later
> write of the id, listed it in `redacted_targets()`, and redacted any store's later arrival of it. The defect is on
> main from `8ea59e7` and is in no release. **The rows now read as follows.**
> - **A file that carries a notice's target record UNREDACTED refuses the WHOLE import wherever the record would be
>   admitted under the notice: in a trusted restore, and in a default import that inserts it** (site
>   `store.import.notice-record-unredacted`). A default import over a HELD target does not reach this test: the notice
>   is reported `held-target` and the held copy is kept (next bullet). **The one exception: a notice this store already
>   holds as applied** (its own redaction, or the same witnessed notice applied before, counted `existing`): the arrival
>   is then written in its attestation's treated shape (the v15.1 R10-02 rule, below). A DIFFERENT notice over a
>   record with a completed attestation is refused like any other. Unredacted means treating the file's copy under the notice's fields
>   would change one of its record carriers (`redaction.shows_redaction`; the bookkeeping paths `journal.state` and
>   `provenance.disclosure` are not record carriers). An export writes a redacted record as stored, in its treated
>   shape, so a legitimate same-file notice passes. Admitting such a record would land content its source says it
>   redacted; redacting it would destroy the user's fact when the pairing comes from a poisoned store's own export
>   (a leftover notice beside the user's later record), restored to a fresh machine included. The owner chose
>   refusal over both.
> - **Default import (untrusted, 0005): a notice is applied only to a record THIS import inserts.** A notice whose
>   target was held before the import is NOT applied (row 1, and the held-different-version row: the held copy is
>   kept unchanged and the arriving copy is not written). A notice whose target is absent writes NO standing row (row 3).
> - **Trusted restore (own history, 0005):** rows 1 to 3 stand, under the first bullet. A notice whose target has no
>   copy in the file applies to a held record only if that record already shows the redaction: it then attests and
>   removes nothing, so a split restore reaches the same state in either order. Otherwise it is not applied.
> - **A notice not applied writes nothing** and is reported in the import's `notices_not_applied`, as
>   `[kind, id, reason]` with the reason `held-target`, `absent-target` or `record-not-in-file`. The CLI import line
>   prints their count. `inconsistent_notices` keeps its meaning: targets a notice WAS applied to.
> - **A standing notice names no record this store holds.** It is excluded from `redacted_targets()` and from the two
>   ordinary-write refusals (`add_edge`'s upsert and `add_episode`), so it neither hides nor blocks the user's own
>   record of that id. It still counts at the import's own sites (the reason waiver and the marker-kind admission).
> - **A standing notice completes only on a record THIS import inserts, and only by attesting it.** On a default
>   import, the record's resolved origin (0006 `source_identity.resolve_origin`, over the row as written) must equal
>   the notice's origin byte for byte, or the WHOLE import is refused, naming the standing notice
>   (`store.import.standing-notice-origin-mismatch`). That comparison only ever refuses: it is a restriction, the reading
>   0022 C1 already gives 0006 ("identity groups, never grants"), and 0006 I5's text is not amended. In both modes, the
>   arrival must already show the redaction, or the WHOLE import is refused. A standing notice therefore never removes
>   content.
>
> **What this costs, stated.** (1) On a default import, a source's redaction no longer reaches a record this store
> already holds. (2) A standing notice no longer removes content from a later arrival, in either mode: it attests an
> arrival that already shows the redaction, or the import is refused. (3) A standing notice made by store B over a
> record B holds FROM store A carries origin B while the record keeps origin A, so a later default arrival of that
> record is refused. (4) A file pairing a notice with an older, unredacted copy of its record is refused whole: a
> poisoned store's export pairing a leftover notice with the user's later record (the user removes the notice line to
> import it), and a genuine combination of an old record with its later notice (the remedy is an export taken after
> the redaction). Rows 1 and 3's harm statement (a window in which the record exists un-redacted) is accepted for
> untrusted input, because the alternative was untrusted input destroying data. The round-4 0041 amendment restores
> (1) through the user's confirmation of a PENDING notice.
>
> **Checks:** `tests/test_0041_notice_binding_hotfix.py` (the three arms; the leftover standing rows; the poisoned
> export into a second store, a fresh restore and the same store; the fixed-point, restore and arrival cells), with
> the closure mutants in `specs/evidence/0041/mutation-table.json`.

> **v16 (the fold of `0047/0041-replies`):** §11.6's rules supersede this block's at implementation. Until the pending and standing notice machinery and its tests land together, the product keeps this block's behaviour, its default-path origin check included: the round-4 verdict says not to remove it before its replacement.

#### 🔴 Row 9 and the notice cases — RULED v4 (round-2 F4)

**v3.1's row 9 admitted the record UN-REDACTED when its notice was invalid,
which inverts the whole point.** Ruled, on the second seat's proposed semantics:

| case | ruling |
|---|---|
| **an invalid notice accompanying a record** | 🔴 **the record-and-notice UNIT is REFUSED, with an explicit failure result.** Never the record admitted un-redacted. **A malformed notice must not be a route to importing the content it was meant to remove** |
| **a tombstone arriving with NO notice** | 🔴 **v7 — ADMITTED AS AN UNATTESTED MARKER (§4b), recorded as such, and FLAGGED.** v6 said *"accepted as content — it holds none"*, and that phrasing is what **CONFLICTED with INV-11's mirror**, which refuses the marker *"at every import boundary"*. **Both rules stand once the attestation rule keys them on the RECORD**: the mirror refuses a marker the import cannot account for, and the import's own flag IS the accounting — so the record is admitted, is **not** treated as redacted, and stays writable. **What is still refused at the boundary is a marker presented AS a redaction without its notice** — a forged tombstone — which is the harm the mirror exists to stop |
| **two notices sharing `(origin, target_id, event_id)` with different bodies** | **an integrity refusal.** One identity with two bodies is a corrupted source, not a conflict to resolve ⚠️ **v15: the bodies are compared on the SOURCE identity, across every destination user and remapped copy, and the refusal holds ACROSS imports, not only within one file (below)** |
| **`event_id`** | **the source's `(user_id, seq)` pair, carried as attributes** — never as the destination's own position, per §4g's `seq`/`txn` rule |

> **The standing notice is representable and still not honest** until 0029's
> `refs` check exempts a `pending` notice of kind `redacted` (§11.4). **Until
> that lands, row 3 makes a healthy store fail its own integrity check**, and
> this spec should not ship a row that does.

| holds it and the event is **missing** from a later export | **nothing is inferred.** Absence is not un-redaction; there is no path by which an import restores redacted content |

**Repeat imports** are idempotent on `(origin, target_id, event_id)` *(⚠️ v15: on the BOUND identity below)* — the same
event twice is one redaction and one notice, per §4b-ii's content-idempotence.

**User remapping.** An import that remaps `user_id` **must remap the event's
subject with the record's**, in the same mapping. A redaction event that keeps
the source's `user_id` after its record was remapped is **a redaction that no
longer points at anything** — the record survives un-redacted and the store
believes it handled the event.

> 🔴 **v15 — WHAT A NOTICE'S IDENTITY BINDS, AND WHAT TRAVELS WITH IT (round-9 R9-04, R9-06, R9-08; sweep C).**
> - **The identity binds the destination.** A notice is identified by its SOURCE identity (origin, source user,
>   source event reference) AND the DESTINATION user AND the TYPED target (kind, id) after any remap. Round 9 imported
>   one redacted export for two users of one store: the second import reported the notice as existing, applied
>   nothing, and left that user's copy unattested. Sweep C enumerated every identity import mints or carries; the
>   notice identity was the only one that failed to bind the destination.
>   ⚠️ **v15.1 — AND IT IS HELD STRUCTURED, NEVER ENCODED (round-10 R10-03).** The three source components are stored as three fields and compared by exact equality; the row's own id is a digest over the six components, each length-framed, so no two distinct identities share one. v15's implementation joined unrestricted strings with a separator and compared by prefix: an origin containing the separator collided with another identity, a source user containing it was relabelled as local on relay, and an embedded NUL defeated the cross-import comparison. **An identity this store cannot decode is never relabelled as locally witnessed history.** The store schema carrying these fields is unreleased (15); a store created from an unreleased checkout of the repository is not supported across this change.
> - **The foreign body is IMMUTABLE.** The canonical body (fields, marker version, reason, `recorded_at`, the source's
>   store versions, the source event reference) is kept beside the local application facts *(⚠️ v15.1: the source event reference belongs to the IDENTITY above, not the body; the body is the fields, marker version, reason, `recorded_at` and the two store versions — one source event has one body by construction)*, and is exported
>   UNCHANGED: a relay re-exports the source's reason and time, never `imported_notice` and its own import time. So
>   an original and its honest relay, imported together, are one notice.
> - **Repetition is compared, not assumed — on the SOURCE identity, not the bound one.** One source event has one
>   body, whichever copy or destination user it lands on. The same bound identity with an EQUAL body is idempotent.
>   Any held notice of the same SOURCE identity (origin, source user, source event reference) whose body DIFFERS —
>   under any destination user, any remapped target — refuses the WHOLE import atomically, across calls as well as
>   within one file. (Round 10 stage 2: a comparison keyed on the bound id never ran for a user-remapping import,
>   because each such import mints a new target id, and a contradictory body was accepted onto a second copy.)
> - **A marker-valued `kind` is admitted ONLY when the same atomic unit attests `kind` for that episode** — a notice in
>   the import naming it, or a notice already held for it, a standing one included. A prose kind, and a marker kind
>   nothing accounts for, keep §4h's refusal. (Round 9: the implementation refused its own valid export of the
>   treated historical episode.)
> - **A notice's `fields` are the declared kind's CARRIER PATHS**, derived from the treatment tables, side-table
>   paths included — not free strings. A prose entry, a wrong-kind path, a repeated or an empty list refuses before
>   any write, at the parser and at the commit. (Round 9 stored prose as a "field name".)
> - 🔴 **v15.1 — ONE HELD-DIFFERS RULE, FOR EVERY RECORD KIND THE IMPORTER ADMITS (round-10 R10-01).** A held record
>   that differs from the arriving one is redacted and flagged when a valid notice accounts for the difference (the
>   difference lies in the notice's fields), and refused otherwise. *(⚠️ **v15.2 — ALIGNED, round-11 N11-01.** The parenthesis states a narrower rule than the one ruled at round 10 and built: no implementation computes "the difference lies in the notice's fields". The rule is: when a valid notice for the held record is present, the held record is treated as the notice names, its other fields are KEPT, and the arrival is flagged `inconsistent_notices`, whatever else differs; a difference in an outcome chain's STRUCTURAL fields refuses, notice or not; with no notice, a content difference refuses. The parenthesis was drafted before that ruling and not revised after it. Nothing arriving overwrites a held field.)* The OUTCOME CHAIN takes the same rule as edges and
>   interaction episodes; v15's implementation refused there unconditionally, so a full export carrying a newly
>   redacted outcome could not treat the destination's held copy. The chain's structural fields and integrity checks
>   are untouched: a structural (topology) difference still refuses, notice or not. This does not authorise
>   overwriting outcome history.
> - 🔴 **v15.1 — A COMPLETED ATTESTATION WHOSE RECORD IS ABSENT (round-10 R10-02).** A record this store redacted and
>   then deleted is not an empty slot. When it ARRIVES again in a unit carrying its notice, it is written in its
>   TREATED shape *(⚠️ v15.2, round-11 Q1: the PERMITTED treated-or-absent shape, not byte equality with what the original redaction wrote: an arriving empty carrier stays empty, content becomes the marker, a marker stays the marker)* in the same commit, with no new REDACTION event and no new attestation (an edge's ordinary
>   import journal row, carrying the treated record, is an import write, not a redaction); the next receipt is `repeated=True`
>   and returns the original. The arrival is REFUSED, fail-closed, when
>   the treatment the record would need reaches a field the original attestation does not name (the attestation is
>   the authority, and it does not cover that field); an honest backup, taken before or after the redaction, needs
>   no field outside it. Without the notice the arrival REFUSES, unchanged (the absent-target twin of a present
>   attested target meeting a no-notice file), and an ordinary write to that id stays refused. Refusing the
>   notice-bearing arrival instead was weighed and rejected: import is atomic per file, so one deletion would make
>   every later file carrying the record, the store's own backups included, unrestorable. **The doctor grades this
>   state as INFORMATION**, beside the standing notice: a completed attestation naming an absent EPISODE, and that
>   episode's own journal events, are what a supported deletion leaves. An absent EDGE under a completed attestation stays an ERROR (no single-edge remover
>   exists), and every other missing target stays an error. The doctor cannot tell a deleted episode from one that
>   never existed; a hand-planted attestation for the latter also reads as information, and planting it needs a
>   write outside every public path.
> - 🔴 **v15.1 — PROVENANCE IS A RECORD FACT, NOT A REASON (round-10 R10-04).** Whether a redaction record is local or
>   witnessed is read from facts only the import path writes (the source fields and the foreign body), never from its
>   reason. A hand-built import file cannot make a witnessed record read as local.
> - 🔴 **v15.1 — WHAT AN ATTESTATION NAMES, AND WHEN THERE IS NOTHING TO REDACT (found in the R10-04 sweep).** A
>   redaction attests every carrier that holds its TREATED value after the call: the ones this call changed, the ones
>   that already held the marker, and a registered `redacted` reason by the same rule. So redacting an UNATTESTED
>   marker (§4b-ii: the call proceeds as a first redaction) attests it, and the record is protected from then on;
>   v15's implementation attested nothing there, left the record writable, and exported a notice naming no field,
>   which import refused. Only when that set is EMPTY, a record holding neither content nor marker in any carrier,
>   does the call REFUSE, before any write: "nothing to redact" — ruled by the owner 2026-10-03. An attestation that
>   names nothing attests nothing, and its export would be unusable.
> - 🔴 **v15.2 — WHAT A NOTICE'S `fields` MAY NAME: ONE DOMAIN FOR THE WRITER AND THE READER (round-11 R11-01).**
>   The domain is the kind's carrier paths (the treatment map's own, unchanged) plus a CLOSED, NAMED set of
>   BOOKKEEPING paths: for an edge, `provenance.disclosure` (the §4h disposition a redaction may have to move) and
>   `journal.state` (the §4c journal, which is its own class outside the 64 carriers; the path names the journal, not
>   its table, so 0029's V-INERT gate on the event table's name stays as accepted). Each bookkeeping path is
>   listed ONLY when this treatment changed it: the disclosure when it moved, the journal when a prior event's state
>   held content. The redaction writer, the import parser and the commit primitive read ONE definition. v15.1's
>   implementation wrote `provenance.disclosure` into a quarantine edge's notice, even when the disclosure was
>   already quarantined, and its own importer refused that path, so the destination kept the content. No other
>   provenance path is admitted. A destination's attestation is the notice's fields together with its OWN
>   treatment: a destination whose disclosure needs moving moves and attests it whether or not the notice named it,
>   and a notice that predates the journal path still treats the destination's journal.
> - 🔴 **v15.2 — "NOTHING TO REDACT" IS JUDGED OVER THE WHOLE COVERED SURFACE (round-11 R11-02).** The owner's ruling
>   (refuse when there is nothing to redact) is unchanged; what it is judged over is now stated. A record whose live
>   carriers are empty can still hold its content in its journal or a side table (a confirmation's request digest, the
>   ledger's digests). The decision is made AFTER the treatment has examined every covered carrier, inside the
>   transaction; a refusal rolls the whole operation back, so nothing is written. A record that holds content only in
>   its history is redacted, and its attestation names those paths, so it is non-empty and its notice imports.
>   ⚠️ **v15.3 (round-12 N12-02):** the covered surface includes a SHARED side carrier linked to the record's source that ALREADY holds the marker, whoever's redaction put it there (a historical source-revocation reason is shared by every record of that source). Such a carrier is attested for this record too *(v15.4, round-13 N13-01: and so is a SUPERSESSION-REFUSAL row, which links the prior AND the incoming edge; a shared row is recognised by EVERY column that links it to a record, never by one key. The contribution ledger is shared too (a row links its survivor and its contributor), but its digests are a CLEAR carrier and the native writers leave identity_digest NULL when a record has no source id, and evidence_ref_digest NULL when its evidence reference is empty, so a cleared ledger digest is not distinguished from one never written: an already-cleared ledger row is not attested for the second record, the round-11 reading of CLEAR values)*, so a record whose only covered carrier is an already-treated shared row is redacted, not refused "nothing to redact". A record with no linked source and no content anywhere still refuses.
> - 🔴 **v15.2 — ONE SOURCE IDENTITY AND BODY FOR A NATIVE AND A WITNESSED RECORD (round-11 R11-03).** A redaction this
>   store ORIGINATED has a source identity and body too: this store's origin, the user, its own event reference, and
>   its own facts, exactly as its export states them. Every comparison reads that same projection for native and
>   witnessed records alike. So, for an arriving notice whose source identity is one this store holds:
>   - an EQUAL body naming the SAME target (destination user, kind, id) is existing: nothing is written;
>   - an EQUAL body naming a DIFFERENT target (a copy, for instance this store's own export imported under another
>     user) is applied to that target. That application is WITNESSED: the new record carries the native identity as its
>     source and the projected body as its foreign body; the native record is never altered;
>   - a DIFFERENT body is refused, whole-import, whether the held record is native or witnessed.
>
>   v15.1's implementation compared only witnessed records. A contradiction of the store's own event was accepted, and
>   its next export held two bodies under one identity; an honest relay of its own event wrote a second record for one
>   target. Foreign provenance is never written onto a native record to make a comparison match.
>   A witnessed record with no stored foreign body can exist only in a store from an unreleased checkout (written before
>   the body was kept; already unsupported, above); such a record never contradicts, so a contradiction against it is
>   not detected.
> - 🔴 **v15.3 — A CONSOLIDATION OUTPUT THE DESTINATION ALREADY HOLDS (round-12 R12-01, N12-01).** An indexed
>   consolidation output carries an identity accepted 0014 §2c protects: an arriving output whose `(destination user,
>   resolved origin, operation_id, index)` the destination already holds must match the held one exactly, or the
>   import refuses. A redaction of that output is the ONE difference admitted, by the rider 0014 §2c now carries
>   (approved by the owner 2026-10-05; the two texts state one rule): a valid notice for that output is in the import
>   or already held, every differing field is named in it and is an episode carrier path, and each such field holds
>   the marker on the held or the incoming side. Then the arriving output is NOT installed at the identity check; the
>   notice binds to the HELD output's id and is applied to it by the notice step, as to any held target (the body
>   comparison runs on it as on any notice); the arrival is flagged. That is the outcome the held-differs rule above
>   gives a held record under a notice, reached through the notice step, not through that rule. Any other difference
>   refuses as 0014 always required, lineage included, notice or not (the operation and index cannot differ at a
>   collision: they ARE its key, so a difference there is a different output). v15.2's implementation refused at the identity check before any notice was
>   read, so a held output never received its redaction; and a repeated remapped import wrote a standing notice for an
>   id it had discarded.
>   ⚠️ **v15.4 (round-13 R13-01, R13-02), the conditions read exactly:** "a valid notice for that output" means a notice whose target, AFTER every arriving id in the unit is resolved, is this RESOLVED held output. A raw id spelling never stands for both an arriving record and an unrelated held one, so when ids are relabelled, a notice for one output can never authorize another's difference. A notice names a SOURCE record: when an arriving record carries the notice's target id, the notice is for THAT arrival's subject, and it authorizes this exception only when that arrival IS the colliding output; a notice whose target names no arriving record is for the held or standing record of that id directly. An ordinary record arriving under a held output's id does not lend its notice to that output's own arrival under another id: the import refuses. "Holds the marker" means the field's WHOLE value IS the marker; text that merely contains it is an ordinary difference and refuses. The broad "contains the marker" test keeps its own jobs (reserving the marker against ordinary writes; reporting unattested markers) and is not this decision.


**`seq` / `txn` — the reviewer's sharpest point.** Exporting **only** redaction
events **creates gaps in the source's sequence**, and the destination **may
already be using those numbers**. Therefore:

| | |
|---|---|
| **never reuse source numbers locally** | imported events are allocated **destination-local** `seq`/`txn` at import, from the destination's own allocator |
| **preserve source metadata** | the source `origin`, source `seq`/`txn` and source timestamp are retained **as attributes of the imported event**, never as its local position |
| **gaps are expected, not repaired** | a gap in the source sequence carries no meaning at the destination and **must not be treated as missing data**, because a partial export is the normal case |
| 🔴 **witness distinction** | an imported notice **must not present as a locally witnessed action.** The local journal says *"this store was told that the source redacted X"*, never *"this store redacted X"*. Collapsing the two makes the destination's journal claim an act it did not perform, and `why` would render it as local history |

> **The witness distinction is the one that matters beyond this spec.** The
> journal's value is that it records what THIS store did. An import that writes
> foreign acts as local acts corrupts that property for every reader, and
> redaction events would be the first records to do it.

### 4h. 🔴 v7 — THE TRANSITION POLICY FOR EXISTING RECORDS (round-4 F2)

**Every restriction in this spec is a rule about WRITES. None of them reaches a
record already in the store**, and the reviewer's F2 is that the spec had
written the restrictions and not the transition.

#### (i) The relation-only quarantine is REAL, and redacting it is a SAFETY REGRESSION — EXECUTED

v6 carried this as a *candidate* needing simulation. **Simulated, at the pin:**

```
BEFORE redaction: relation='third_party_claim'    quarantined=True
AFTER  redaction: relation=<marker>               quarantined=False
```

The pair is **constructible through the public model, stores, and reads back**:
`Edge(relation=QUARANTINE_RELATION, provenance.disclosure=MENTIONABLE)` is
accepted, persisted, and returns `quarantined == True` — **held entirely by the
first clause of `Edge.quarantined`.** `ingest.py:190` does set both together,
which is why this has never been seen; **ingest is one producer and the model is
the contract.**

> 🔴 **So redacting `relation` on such an edge PROMOTES AN UNVERIFIED
> THIRD-PARTY CLAIM out of `## UNVERIFIED THIRD-PARTY CLAIMS (never assert as
> fact)` and into the grounded `## RELEVANT DETAIL` section** — the render split
> at `__init__.py:1167/1168` reads `quarantined`. **A privacy operation would
> have widened what the model may assert.**

**THE RULE THIS FORCES, and it is general:**

> **A REDACTION MAY NOT CHANGE A DERIVED DISPOSITION. Where the treatment would,
> the redaction MUST RE-ESTABLISH that disposition through a field it does not
> redact — in the same transaction — or REFUSE.**

#### 🔴 v11 — THE COROLLARY THIS SPEC THEN BROKE ITSELF ON (round-5 finding 1)

> **REDACTION ACTS ON CONTENT. ABSENCE IS NOT CONTENT.** A field holding `None`
> has nothing to remove, so no treatment reaches it. **Every carrier rule is
> therefore THREE cases, not two: ABSENT · a RECOGNISED VALUE · EXISTING PROSE.**

**v7 wrote rows 30/49 as two cases — preserve-if-registered, else replace — and a
two-case rule must put `None` on one side or the other.** It put it on the
replace side, so `retired_reason=None, active=True` became
`"redacted", active=False`: **a redaction that RETIRES AN ACTIVE EPISODE**, which
is exactly what the rule immediately above forbids. Reproduced by the reviewer on
the packaged model.

🔴 **AND THE TEST HAD IT RIGHT THE WHOLE TIME.**
`tests/test_0041_treatment_matrix.py:93` asserts
`after.retired_reason is None and after.active == before.active`, under the
comment *"the treatment touches content, never absence"*. **The evidence encoded
the correct rule and the SPEC TEXT drifted away from it** — the test stayed green
because it tests the product, not this document. *The specification and its own
evidence disagreed, and the evidence was right.*

> 🔴 **FINDINGS 1 AND 2 ARE ONE MISTAKE MADE TWICE: A CURRENT STATE READ AS A
> PERMANENT RULE.** `retired_reason` is `None` today, so absence was treated as
> something to overwrite; `source_revocations.reason` has no vocabulary today, so
> it was treated as free text forever. **§11.2 was built on "the EXECUTED state"
> — the right instrument for describing what IS, and the wrong one for setting
> what OUGHT. A CONTRACT IS NOT A CENSUS.**

**The verdict's sentence to design against:** *forbidding the clearing of an
existing retirement reason does not justify forbidding an already-absent one.*


For this case: redacting `relation` on a quarantined edge **sets
`provenance.disclosure = QUARANTINED`**, so the second clause carries what the
first one held. **This is §2d-v's question (*what READS this field?*) turned
into an obligation rather than a warning**, and it is the third proven instance
after `Episode.kind` → H14 and `retired_reason` → `active`.

#### (ii) `Episode.kind`: existing prose kinds, and how a marker-valued record validates

Row 46 closes `kind` to the recognised operational set. **Existing stores hold
prose kinds that nothing ever refused**, so the closure cannot be applied
retroactively without refusing records the product itself wrote.

| | |
|---|---|
| **at MIGRATION** | existing prose kinds are **RETAINED** — the same boundary §11.2 draws for legacy reasons, and for the same reason: a migration that rewrites history destroys the record it exists to preserve |
| **enforcement point** | the closure binds **the WRITE path and the IMPORT boundary**, never the read path. A closure enforced on read turns every legacy store into an unopenable one |
| 🔴 **how the marker-valued record validates** | **by the ATTESTATION RULE (§4b).** The closed set is the recognised kinds **plus the marker when, and only when, a redaction record names this record and this field.** An unattested marker in `kind` is not a valid kind and is refused — which is what stops the closure from becoming a route to writing arbitrary bytes into a field five guards read |

#### (iii) 🔴 THE EVIDENCE RULE — a transition claim proved on a NEW record proves nothing

**Every claim in this section must be demonstrated on a record written by the
PRE-RESTRICTION writer**, loaded from a store created before the change — never
on a record constructed under the new model in the same test. A fixture built
by the new code has already satisfied the new rule, so it cannot show what
happens to one that never did.

> **This is the reviewer's F2 in its sharpest form, and it is a rule about
> FIXTURES rather than about redaction.** The spec has been wrong this way once
> already: the packaged INV-12 fixture left fields unset and **missed a widened
> embedder that a populated fixture caught.** A fixture that cannot fail the
> test is not evidence that the test passes.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| pre-0041 store, no `redacted` kind | migration adds the kind; **existing baseline events carry full json and are redactable by the same operation** |
| semantic lane enabled | vector and digest dropped; **next recall simply has no semantic entry for that edge** |
| semantic lane disabled | no embedding rows to drop; the rest is identical |
| consolidation in flight | the fenced primitives own claimed ids — **redaction of a claimed input must refuse and say why**, not proceed (0010 X21's shape) |
| `forget_user` afterwards | unaffected; wholesale erasure still removes everything |

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **INV-1 structure preserved** — after redaction, chain lengths, `seq` contiguity and reference integrity are unchanged | redact mid-chain; assert chain length, every `seq`, and `doctor` clean | CI |
| **INV-2 no partial carrier** — the duplicated `edges.object` column and the json agree after redaction | planted mutant that redacts json only; the check must fail | CI |
| **INV-3 `why` degrades, never fails** | `why` on a redacted edge returns a biography whose mutation diff is "redacted" | CI |
| **INV-4 journal carries no residue** — no event for a redacted edge yields the original content | sweep every `edge_event.state` for that edge id; assert tombstone | CI |
| **INV-5 scope** — cross-user or unknown target refuses loudly | `pytest.raises` on each; **never a silent no-op** (the `delete_episode` defect's shape) | CI |
| **INV-6 reason is not a content channel** — the reason never reaches a prompt, recall, export or MCP surface | the 0022 §7a seam sweep pattern, extended to the reason | CI |
| **INV-7 oracle disposal** — no `content_digest` or `evidence_ref_digest` survives for redacted content | assert both row sets empty | CI |

**INV-2 and INV-7 are the two a reasonable implementation gets wrong**, which is
why both carry planted mutants rather than positive assertions alone.

## 7. Failure modes and reversibility

| failure | consequence | mitigation |
|---|---|---|
| partial redaction (one carrier missed) | **content survives while the record says redacted — the worst outcome available** | INV-2, INV-7, and the single transaction |
| redaction of the wrong id | irreversible content loss | INV-5; refuse on anything unrecognised |
| `why` crashes on a tombstone | a DX verb broken by a privacy feature | INV-3 |
| reason used as a content channel | reintroduces the hole 0008 closed | INV-6 |

**Reversibility: none, by design.** The mitigation is refusal on doubt, not undo.

## 8. Claims and limits

> 🔴 **v6 — A CONSEQUENCE THE CALLER MUST BE TOLD, EXECUTED (round-3 G1).**
> **After redaction the record can NO LONGER BE CORRECTED.** The supersession
> path requires a replacement to share the prior's `(user, subject, relation)`;
> after redaction the prior's are markers, so a live replacement is **REFUSED**.
> **Redaction is not only removal — it ends the record's correctable life**, and
> a caller redacting in order to fix a mistake must know the fix can no longer be
> filed against that record.

**Claimed:** after redaction, the named content is absent from **every carrier
this spec enumerates AND NAMES IN THE RECEIPT**, and the record that it existed
and was redacted survives **in the live store**.

> ⚖️ **NARROWED v3 by the owner's F6 ruling — *"outputs are separate."*
> Redacting an input does NOT reach consolidated outputs, or other records
> containing its content.** The claim is bounded to the named carriers, and the
> receipt **names the surviving derived records so the caller can redact them
> too**. See §10.1.
>
> **This is a narrowing of the CLAIM, not of the operation** — the operation
> already did only this. What changes is that a caller is now told what remains
> after a success, which is the thing the reviewer said a caller needs to know.
> **A success claim wider than what was done is the failure mode this spec has
> to avoid**, and it is the same failure as §2's false negative on
> `original_relation`, one level up.

> 🔴 **v1 CLAIMED THAT SURVIVAL WITHOUT THE QUALIFIER, AND IT WAS FALSE ACROSS
> EXPORT/IMPORT.** Verified independently by both seats: **`edge_event` appears
> ZERO times in `portability.py`**, which exports edges and episodes. So a
> re-import carries the tombstoned edge and **not** the `redacted` event — and a
> redacted edge without its event **is indistinguishable from an edge someone
> simply blanked**, which is §9's entitlement question arriving by the back door.
> **The claim is narrowed to the live store until the decision below is taken.**
>
> 🔴 **v3.1 — AND THE NARROWING IS NOT LIFTED BY D2 ALONE.** `export` carries no
> events of any kind today (verified: the record kinds are `edge` and `episode`,
> anything else raises). **The claim stays bounded to the live store until a
> carrier is BUILT**, not until the decision is taken. D2 chose the cargo;
> nothing yet carries it.

**NOT claimed:**
- **that the content is unrecoverable from a copy of the file taken earlier.**
  Redaction is not retroactive across backups, and no embedded product can make
  it so.
- **that redaction is detectable as complete by the redacting party alone** — the
  administrator-history limit applies here as everywhere (`f4d607a`).
- **that `evidence_ref` names resolved by the host are redacted** — Veracium does
  not hold them. **The host's own copy is the host's obligation**, and C0's
  `source_id` requirement is the handle for it.

> 🔴 **v15 — CONSEQUENCES AND LIMITS MEASURED IN ROUND 10, stated so they are not found later:**
> - **A store holding legacy prose in a closed field cannot restore its own export until those records are
>   redacted.** The D1 closures bind import, `restore=True` included, so a stored prose `retired_reason`,
>   `invalidation_reason`, episode `kind` or revocation reason is refused on the way back in; redacting the record
>   writes the vocabulary value or the marker over the prose. This is D1's consequence, not an oversight; admitting
>   legacy prose on restore alone would change D1, and is the owner's decision.
> - **An attested episode is never a consolidation input.** It stays as its marker. A redaction that lands between
>   the pool's listing and its claim makes the claim refuse under the write transaction; the pool reports 0021's
>   existing `contended` / `claim-contention`, which 0021 does not tie to one cause, and the next run excludes the
>   attested input at selection. **The pool result does not distinguish "redacted since the listing" from "claimed
>   since the listing"**; the redaction's own record does.
> - **An invalidation made through `add_edge` is journaled as `mutated` with a NULL reason, never as
>   `invalidated`.** The reason field itself is closed (§11.2); the journal's shape for that path is a NAMED RESIDUAL,
>   not fixed here.
> - **The ledger's `plan_row_id` binds the destination by reading, not by execution.** It hashes the user and the
>   survivor type, and its validator refuses the synthetic row an execution would need. Sweep C reports it as held
>   by reading.
> - **Two check-then-write gaps on the episode write path are closed together** (R9-01 and the reserved-id check
>   beside it): both decisions run inside the write's own `BEGIN IMMEDIATE`, each with a two-connection cell. The
>   cost is a longer write-lock interval on `add_episode`, measured with the fix. *(⚠️ v15.2: measured UNCONTENDED only, at round 10, on one connection (ratio 0.998); the wait a second writer incurs under contention is not quantified.)*
> - **Records that may still carry the content are named at three link strengths** (§11.5(3) as widened at v15;
>   ruled by the owner 2026-10-02). Redaction treats the record, not records related to it (§4d; *"outputs are
>   separate"*), and round 10 measured the receipt naming none of them, on the primary path: `remember()` stores an
>   edge AND the episode its summary came from, and redacting the edge left that episode carrying the value verbatim.
>   1. **EXACT, by identifier join:** outcome episodes whose `Episode.edge_id` is the target; for an edge target, the
>      SOURCE episodes of the same user sharing its `provenance.evidence_ref` (row 53, PRESERVE, so the join holds
>      after treatment); for an episode target, the edges of the same user sharing its `evidence_ref`. Each named
>      record carries the link it was found by. A record that is itself attested-redacted is not named: it no
>      longer carries the content. Where a caller supplied its own `evidence_ref`, the join can name records that
>      do not carry the content; that is the conservative direction, never a false assurance.
>   2. **A DOMAIN with no exact list:** "episodes quoting this record" written by `dispute` and `correct`, which are
>      linked to the edge only by an evidence-reference CONVENTION this store does not treat as an identity. It is
>      reported when the target was disputed or corrected (its reason or a journal event), or supersedes a corrected
>      prior (the replacement edge carries neither reason). `receipts_complete` stays `False`, as §4f already
>      requires.
>   3. **Forward obligation:** a structural link from dispute and correction episodes to the record they quote, as its
>      own specification; until it exists, that domain has no exact tier.

## 9. Brief for the external reviewer

**Attack §4c first.** The journal decision is the one that is a judgement rather
than a derivation: tombstoning `state` removes content from the product's only
history artifact, and the argument that this is acceptable rests on the
administrator ruling landed the same day. **If that argument is wrong, the spec
is wrong at its centre.**

**Second: §2's carrier list is the whole safety claim.** It was enumerated from
the schema, not from a design discussion — the duplicated `object` column, the
`content_digest` oracle and the journal are the three a design discussion would
miss. **A carrier this list omits is a silent partial redaction, which §7 names
as the worst outcome available.**

**Third: is §3's refusal to consult the authority ladder right?** Research argues
redaction makes no claim about truth and gating it on authority would prevent a
low-authority party removing their own content. A reviewer may see an entitlement
effect research does not.

## 9b. ⚖️ FOUR DECISIONS — ALL RULED BY THE OWNER 2026-09-14

> **⚖️ RULED, research session 2026-09-14:**
>
> | | ruling |
> |---|---|
> | **D1** | **the CLOSED VOCABULARY.** And it binds the SHAPE, not one field — the enumeration has found **three** host-supplied reason fields (`edge_event.reason`, `Edge.invalidation_reason`, `source_revocations.reason`); all three close, or the next sweep finds a fourth |
> | **D2** | **RULED IN THE OWNER'S OWN WORDS: *"carry it — but carry only the redacted events, not the journal."*** The constraint is his instruction, **not research's gloss on a one-word yes** |
> | **D3** | **SKIP redacted edges in the semantic rebuild** |
> | **D4** | **TOMBSTONE the receipt's request digest**, and a replay of a redacted supersession REFUSES rather than silently re-applying |
>
> 🔴 **v7 ANNOTATION — D1's OWN CONDITIONAL HAS BEEN MET, and the ruling is left exactly as the owner wrote it.** D1 says *"all three close, or the next sweep finds a fourth"*. **The sweep found the fourth (`Episode.retired_reason`), and then found that a fifth surface has a different character entirely**: §11.2 now carries FOUR reason fields with THREE contracts, because the EXECUTED state differs per field — two close today, `Episode.retired_reason` has **no refusal at all**, and `source_revocations.reason` **has no vocabulary to close**, so D1's shape-binding rule reaches it as a content carrier rather than as a vocabulary. **The count in the ruling above is the owner's and is NOT edited**; this note records what the condition it names has since produced.
>
> **D2's reasoning, recorded because the question was put to research rather than
> answered by the document — and then RULED back in the owner's own words,
> constraint included, so the narrowing is not research's to soften or widen.** D1(a) removes the only objection: a vocabulary
> reason carries no content, so the event exports safely. The harm of NOT
> carrying it is sharper than a lost claim — **a re-imported tombstone is
> indistinguishable from a record someone simply blanked**, so a lawful redaction
> and arbitrary tampering read identically after a round-trip, which is §9's
> entitlement question arriving by the back door.
>
> 🔴 **But "carry the event" must not become "export the journal." Verified:
> `edge_event` appears ZERO times in `portability.py` — it has never been
> exported at all.** The journal holds every state transition for every edge;
> newly exporting it is a large disclosure surface unrelated to redaction and
> would need its own review. **So: `edge_event` rows of kind `redacted` ONLY.**
> **Consequence: `FORMAT_VERSION` bumps under 0025/0026 §3d** (a new exported
> field bumps the format so an old reader refuses rather than sheds it) — 12→13,
> after the producer field's 11→12.



**Each is a real fork with a cost on both sides. Research states a preference and
does not pick.**

### D1 — the `edge_event.reason` field

It is free TEXT and `why` renders it. An operator who writes *"redacted: the
user's HIV status"* into the reason has put the content back into the store.

| option | buys | costs |
|---|---|---|
| **(a) closed vocabulary** *(dev's recommendation; research concurs)* | **makes the field a non-carrier BY CONSTRUCTION**; 0008's `ConfirmationActor` precedent for the same hole; lets the redacted event export freely | the operator loses free prose — **which they should not be writing into a store they are redacting** |
| (b) export the event WITHOUT the reason | keeps §8's survival claim and the confinement | an asymmetric export shape someone must remember |
| (c) narrow §8 to the live store, leave the reason free | nothing changes | **costs the survival claim that motivated raising it** |

> ⚠️ **And D1 now reaches further than the event: the derived enumeration found
> `Edge.invalidation_reason`, free text on the edge itself.** Whatever is decided
> for one reason field should be decided for both, or the next enumeration finds
> the other one.
>
> 🔴 **It did. The widened sweep (§2b) found a THIRD free-text reason —
> `source_revocations.reason` — in a table this spec had never examined.** The
> sentence above was written as a warning and came true within the day.
> **So D1 is not a decision about one field: it is a decision about the SHAPE
> "host-supplied reason string", and it must be applied to every instance the
> enumeration returns, now and at each future sweep.** Three are known:
> `edge_event.reason`, `Edge.invalidation_reason`, `source_revocations.reason`.
>
> 🔴 **AND IT HAPPENED A THIRD TIME — v3, 2026-09-15: `Episode.retired_reason`
> is a FOURTH instance**, found once the enumeration stopped hand-naming the
> models it walked (§2). The warning above has now come true twice, on the two
> occasions the corpus was widened, which is the whole of the evidence about
> what widening it again will find.
>
> **D1's four instances: `edge_event.reason`, `Edge.invalidation_reason`,
> `source_revocations.reason`, `Episode.retired_reason`.** Dev's round-1
> reproduction confirms prose reaches the fourth through its sole writer
> (`_retire_episode_row`, the revocation path's `reason`), persists and exports
> — so option (a)'s closed vocabulary must cover it, or the field is the hole
> the other three were closed to prevent.
>
> ⚠️ **AND THE COUNT IS A FLOOR, NOT A TALLY.** Three of the four were found by
> widening the enumeration, each time after this document asserted the set was
> complete. **D1 should therefore be written as a rule over the shape, applied
> by the enumeration at each run, and not as a list of four field names** — a
> list is the artifact that has failed here four times.

### D2 — does `export` carry the `redacted` event?

**Coupled to D1 and that is the point.** Carrying the event restores §8's
survival claim across re-import; it also carries whatever the reason holds.
**Under D1(a) the coupling dissolves** and the event can export safely.

### D3 — does the semantic rebuild skip redacted edges?

If not, the tombstone is embedded and a fresh `edge_embedding` row appears.
**Harmless as an oracle** — the pre-image is the public marker — **but INV-7 must
then say it is true of the ORIGINAL digest and not of the row.** Research's
preference: **skip redacted edges**, because an invariant needing a footnote
about which row it means is one nobody will hold.


### D4 — the supersession receipt's request digest

**Stated in full at §2b, where the evidence is.** In one line: the receipt
carries a SHA-256 over the complete edge dump, which is the confirmation-oracle
class §2 orders dropped for `edge_embedding.content_digest` — but here the
digest is the replay identity, so dropping it converts a privacy hole into an
idempotency hole. **Research recommends tombstoning it and letting a replay of a
redacted supersession REFUSE; that is a trade of availability for privacy and is
the owner's to make.**

## 10. Open questions

1. ~~**Does redaction propagate to consolidated outputs** whose `lineage` names a
   redacted input?~~ ⚖️ **RULED BY THE OWNER 2026-09-15 (F6): NO — *"outputs are
   separate."*** Redacting an input does **not** reach consolidated outputs, or
   any other record containing its content. Research's view above was the
   recommendation and it was taken; **what was missing was not the answer but
   its consequence**, which the reviewer supplied:

   | | |
   |---|---|
   | **the operation** | unchanged — it redacts the named carriers of the named record |
   | **the receipt** | 🔴 **MUST NAME THE SURVIVING DERIVED RECORDS**, so the caller can redact them too. An output whose `lineage` names the target is identifiable at redaction time; **leaving the caller to discover it is what made "separate" sound like "absent"** |
   | **the claim** | §8 is bounded to the named carriers |
   | **repeat** | redacting an output is an ordinary redaction of that record; nothing about it is special | ⚠️ *v15.3: and it TRAVELS: a destination already holding that output applies the notice to it (§4g, v15.3; 0014 §2c's rider) rather than refusing the output's identity.*

   **§10.1 is CLOSED for v3.** The remaining lineage questions are 0010's, not
   this spec's, and they are about consolidation, not redaction.
2. ~~**Should a redacted edge's `content_digest` removal invalidate the semantic
   index's freshness bookkeeping**, or is absence sufficient?~~ **ANSWERED
   2026-09-13 (dev, against the tree):** `semantic.py:31 content_digest(edge)` is
   computed from the edge's content, so after redaction **the tombstone has its
   own digest and the next index build EMBEDS THE TOMBSTONE**, writing a fresh
   `edge_embedding` row. Harmless as an oracle — the pre-image is the public
   marker — **but INV-7's *"no `content_digest` survives"* is then true of the
   ORIGINAL while a tombstone row reappears.** Absence is sufficient **only if
   the rebuild skips redacted edges**; the spec must say which it wants.
3. ~~**Does `export` carry tombstones or omit redacted records?**~~ **NO LONGER
   OPEN — it is now a DECISION, see below.** Export carries the tombstoned edge
   and **not** the `redacted` event, because `edge_event` is not exported at all.

---

# 11. THE OPERATIVE CONTRACT

> 🔴 **v6 (round-3, "historical discussion moved OUT of the consolidated
> contract"): §11 IS THE CONTRACT AND CONTAINS NO HISTORY.** Everything about how
> a clause came to be worded — the conflicts that were resolved, what an earlier
> version said, which round corrected it — now lives in **Appendix A**. A reader
> who needs the contract reads §11 and §2d-iii-bis and nothing else.
>
> **Precedence, stated once:** §11 governs on **CONTRACT**; **§2d-iii-bis governs
> on any per-candidate ROW.** Where they differ on a row, the map wins — that is
> F4's resolution and it is the only place the two can conflict.

> **Everything above this line is HISTORICAL DISCUSSION.** Where it conflicts
> with this section, **this section governs.** The reviewer found four live
> conflicts between the owner's decisions and passages that were never swept
> when those decisions landed — *"withdraw a claim, sweep its dependents"*,
> which this project has now paid for in both directions.
>
> **Why the conflicts existed, since it is the reusable part.** Each decision was
> recorded **where it was taken** — D1 in §9b, D2 in §9b, the column finding in
> §2 — and the passages those decisions invalidated sat elsewhere and still read
> as true locally. **No individual paragraph was wrong when written.** A spec
> that records decisions in place and never consolidates them accumulates exactly
> this, and it is invisible to any review that reads sections one at a time.

## 11.2 Reason values

🔴 **v7 — FOUR reason fields, not three, and the PER-FIELD contract is built on
what each one DOES TODAY, executed at the pin by the second seat.** v6 said
`edge_event.reason` is closed by *"nothing today"*. **That is FALSE**, and the
correction changes what this section owes: the rule exists and must be
EXTENDED, not invented.

| field | 🔴 **EXECUTED state today** | contract after this spec | enforced by |
|---|---|---|---|
| **`edge_event.reason`** (the journal) | 🔴 **ALREADY CLOSED on the `invalidated` kind** — `sqlite.py:247` refuses a reason outside `DISPOSITIONED_REASONS` (*"the write is refused, 0029 V-KIND"*); **`None` for every other kind.** Executed: `invalidate_edge(reason="told me in confidence")` is REFUSED; with `superseded` the journal reads `[(created, None), (invalidated, superseded)]` | **EXTEND the existing rule to the new kind**: a `redacted` event carries the redaction vocabulary below; **every other kind stays `None`** | the writer that already refuses — one branch added, no new mechanism |
| **`Edge.invalidation_reason`** | **closed by the same writer** | `DISPOSITIONED_REASONS` **+ the new `redacted`**, and the treatment is 🔴 **THREE-CASE (v11): `None` stays `None` · a registered reason is preserved · existing prose becomes `"redacted"`** (row 30) | `test_invalidation_reason_registry_is_total` |
| **`Episode.retired_reason`** | 🔴 **a bare `str` with NO refusal** (round-1 F1b, reconfirmed) — prose reaches it through the sole retirement writer, persists and exports | 🔴 **v11 — THREE CASES, and v10's two-case rule violated §4h.** `None` stays `None` **and the episode stays ACTIVE**; a registered reason is preserved; existing prose becomes `"redacted"`. **Closing the field means `DISPOSITIONED_REASONS` + `redacted` FOR A VALUE THAT IS PRESENT — it does not mean the field must hold one.** v10 said *"never NULL"*, which correctly stopped an existing reason being cleared and then wrongly forced a value onto an absent one: `None`/active=True → `"redacted"`/active=False | 🔴 **OWED — this refusal DOES NOT EXIST and is a code change this spec requires.** The other two close today; this one does not. **And the closure must admit `None`**, or it re-creates finding 1 in the enforcement |
| 🔴 **`source_revocations.reason`** | 🔴 **AS AT v11 (a statement of the EXECUTED state, NOT of the contract)**: a bare `str` carrying THE CALLER'S PROSE, with no vocabulary enforced. Executed: `revoke_source(..., "<the caller's sentence>", ...)` stores that sentence **verbatim** while the affected edge and episode get `revoked_source`. ⚠️ **This row describes what the field DOES TODAY and is superseded as a contract by the column beside it** — v10 read the absence of a vocabulary as the absence of a requirement, which is the mistake round 5 finding 2 named | 🔴 **v12 — FINALISED, no longer proposed (round-6 finding 3; the reviewer RECOMMENDS RETAINING D1 and this text does).** **FUTURE WRITES close to exactly four values**, enforced at the `revoke_source` write path and at every import boundary, refusing loudly: **`subject_request`** — the data subject asked; **`legal_obligation`** — a legal order or statutory duty compelled it; **`erroneous_capture`** — the source should never have been ingested; **`policy`** — 🔴 **the OPERATOR'S OWN standing policy required it** (retention expiry, a scope reduction, a source class withdrawn): operator-initiated, **no external compulsion and no subject request**. 🔴 **`policy` IS NOT A RESIDUAL "other". A revocation that fits none of the four is REFUSED, not filed under `policy`** — §2d-iv's rule, that a set is closed only when something refuses a value outside it, applied to the set this spec is adding. **PROSE ALREADY STORED is replaced at redaction**, three cases as everywhere else. ✅ 🔴 **RULED BY THE OWNER 2026-09-16: RETAIN D1, FINALISE THESE FOUR.** Three options were put to him — keep D1 with these values, keep D1 with different values, or record a decision changing D1 — with the reviewer's recommendation named as the reviewer's. **He took the first. The vocabulary is AUTHORISED, not proposed** | D1 (§9b), which names this field; §2's column table, which classed it a carrier |
| 🔴 **v15 — `source_revocations.reason` on a LIFT row** | the row above was ruled for revocations: its four values are reasons to REVOKE, and the column also holds every LIFT (`action IN ('revoke','lift')`). This specification never mentioned a lift, and the lift's reason stayed unruled through round 9 | ✅ 🔴 **RULED BY THE OWNER 2026-10-02: a lift has ITS OWN closed list, a revocation keeps D1's four, and anything else is REFUSED** (asked in the research session, confirmed in the dev session). The values, chosen by `action` at `revoke_source` and at every import boundary: **`revoked_in_error`** — the revocation itself was a mistake (the wrong source, the wrong digest); **`subject_request`** — the data subject asked that it be restored; **`legal_obligation`** — the order that compelled the revocation ended, or an order compels restoration; **`policy`** — the operator's own standing policy changed, and, as for a revocation, NOT a residual "other". Stored lift prose is a carrier on the same three-case treatment as revocation prose | D1 (§9b), which binds the SHAPE; the lift is the same shape in the same column |
| 🔴 **v15 — the disposition `redacted` itself** | rows 30/49 added `redacted` to `DISPOSITIONED_REASONS` as the value a redaction writes; as registered, every writer that admits a registered reason ADMITTED it, so an ordinary write could set `redacted` on a record nobody redacted (executed in round 10: `add_edge` and `add_episode` both admitted it). `why` and export would then report a redaction that never happened | 🔴 **`redacted` is WRITTEN ONLY BY A REDACTION.** Every other writer REFUSES it as an `invalidation_reason` or a `retired_reason`; import admits it only when the same atomic unit attests that record (a notice in the import, or one held, a standing one included — the R9-06 rule). The other registered reasons are unaffected | the attestation rule (§4b), applied to the registry value; the mirror of INV-11 one field over |
| **redaction's own reasons** | — | `subject_request` · `operator_policy` · `erroneous_capture` · `legal_obligation` · `imported_notice` | ⚠️ **v15.1: `imported_notice` is written ONLY by the import path's notice application. The public `redact` REFUSES it before any write — ruled by the owner 2026-10-03 ("Refuse it"): a caller claiming the witness label for a local act would make a false provenance claim that export carries to another store. The other four are the caller's vocabulary.** | this spec, at the redaction write path — a column CHECK cannot distinguish operations |

> 🔴 **`revoked_source` IS THE EFFECT'S REGISTRY VALUE, NOT THE REVOCATION'S
> REASON.** They are different fields with opposite characters: the affected
> records get a closed vocabulary value; the revocation row keeps the human
> sentence that explains it. **A treatment that reads "the reason field" and
> applies one rule gets one of them wrong**, and v6's single
> *"PRESERVE if vocabulary"* cell did exactly that.

**Other reason-writing operations, named rather than implied:** supersession,
correction, quarantine, lapse/decay, consolidation, dispute, **and SOURCE
REVOCATION** (`revoked_source`) — which v5 did not name at all.

### The legacy boundary

**Two different acts, and v5 blurred them:**

| | |
|---|---|
| **at MIGRATION** | legacy free-form reasons are **RETAINED.** A migration that rewrites historical reasons destroys the record it exists to preserve |
| **at REDACTION** | a legacy prose reason is **REMOVED** like any other content carrier — it is prose, and this is the operation whose purpose is removing prose |
| 🔴 **and the one that must be said plainly** | **hiding a value in `why` REMOVES NOTHING FROM STORAGE.** `legacy_freeform` rendering is a READ-path courtesy, not a redaction. **A spec that offers it as though it were removal would be claiming an erasure it has not performed** |

## 11.3 The invariant matrix

### The canonical invariants — §6 governs their meaning

| inv | statement (§6 governs the meaning) |
|---|---|
| **INV-1** | **structure preserved** — chain lengths, `seq` contiguity and reference integrity unchanged after redaction |
| **INV-2** | **no partial carrier** — every column duplicating a `json` field agrees with the blob after redaction. 🔴 **v3 widening stands: a mutant is planted in EVERY such column, enumerated from the DDL at run time — three, not one** |
| **INV-3** | **`why` degrades, never fails** |
| **INV-4** | **journal carries no residue** — no event for a redacted edge yields the original content |
| **INV-5** | **scope** — a cross-user or unknown target refuses loudly; **never a silent no-op** |
| **INV-6** | **reason is not a content channel.** 🔴 **AMENDED, not redefined:** D2 carries vocabulary reasons on export, so the fence is on **free-form** reasons. After §11.2 there is no free text to fence |
| **INV-7** | **oracle disposal** — no `content_digest` or `evidence_ref_digest` survives for redacted content. **Conditional on D3**: §10's item 2 shows a rebuild re-embeds the tombstone, so this is true of the ORIGINAL either way |

### Additional invariants, numbered from INV-8

| inv | statement | why |
|---|---|---|
| **INV-8** | `""` is **REJECTED** by the tombstone CHECK | F3 round 1. `TEXT NOT NULL` permits `""`; **the test must be seen to FAIL before the CHECK exists.** 🔴 **v7 — the "legitimately empty vs redacted-to-empty" ambiguity this invariant was carrying is RESOLVED in §4b: redaction NEVER writes `""`** (REPLACE writes the marker, CLEAR writes `NULL`), so INV-8 rejects a value redaction cannot produce, and a legitimately empty field is never mistaken for a redacted one |
| **INV-9** | no read-compute-publish path republishes content across a redaction — **as landed (tranche 5, 2026-09-20): the read and the publish are one transaction under the database lock (the embedding upsert) or one conditional statement on the version read before the inputs (the wiki publish)** | F2 round 1 — and round 2's F1 says the check must be ATOMIC, not instance-local; `tests/test_0041_delayed_writers.py` and the flipped two-connection test bind it |
| **INV-10** | an imported redaction notice never presents as locally witnessed | F5 round 1 |
| **INV-11** | 🔴 **v9:** an ordinary write to a field whose redaction is **ATTESTED** is **refused** — *not* keyed on the marker bytes; an unattested marker stays writable (§4b) | F3 round 1; re-keyed by v7's attestation rule |
| **INV-12** | `embedded_text`'s field set ⊆ `content_digest`'s | 🔴 **round-2 F1: the test PASSES when `embedded_text` is widened with `original_relation`, because the fixture leaves optional fields unset. A check that cannot fail. Fixture correction owed with dev's reproduction** |

> ⚠️ **§11.3 no longer claims all 64 enumerated carriers are the removal
> surface** (round-2 F7). **§2d's 64 is the set that CAN hold text; §2 and §6's
> treatment map is the set that is REMOVED.** Conflating an enumeration with a
> removal surface is what made INV-1 read as a content invariant in the first
> place. The treatment map itself is round-2 F6 and is owed.

## 11.4 Amendments to existing contracts

> 🔴 **v15 — the amendment treating stored revocation prose makes to accepted 0022 (round 10), recorded on V-APPEND's
> precedent.** 0022 §4a: *"There is no `active` column and no UPDATE statement anywhere near this table"*, pinned
> mechanically by `test_the_table_is_append_only_by_construction` and by R19's writer gate. §11.2 (v12) ruled that
> prose already stored in `source_revocations.reason` is REPLACED at redaction, which is an in-place UPDATE. **v12 did
> not record that as an amendment to 0022; this paragraph does.** The append-only rule admits EXACTLY ONE updater,
> the redaction treatment:
> - it rewrites `reason` ONLY — never `seq`, `action`, `identity_digest` or `at` — so the standing state, which 0022
>   derives from the latest row by `seq` alone, cannot change;
> - it rewrites ONLY a reason outside that row's vocabulary (§11.2: D1's four on a revoke row, the lift list on a
>   lift row), and writes the marker;
> - it runs ONLY inside the redaction's own serialised write transaction, allocates no ordinal, and appends nothing.
>
> Both gates bind the one updater by name AND by property (its statement's SET clause names only `reason`), each
> with a negative control (an UPDATE of another column, an INSERT, a call outside a transaction). A cell shows the
> standing state identical before and after the treatment across revoke → lift → revoke. **What 0022 loses:** the
> audit sentence a host wrote, which 0022 kept as the point of the trail. That is D1's ruling — a free-form reason is
> a content carrier — applied to the history 0022 was keeping.

> **Tranche 3 (2026-09-19), the two amendments §4c makes to accepted 0029:** (1) **V-KIND** — the kind vocabulary
> is derived from the mutator surface, and `redact()` is a mutator, so `EVENT_KINDS` gains `redacted`, the one
> kind beside `invalidated` whose `reason` is non-NULL (redaction's own vocabulary, §11.2/D1; prose refused at
> the choke point). (2) **V-APPEND** — *no code path updates or deletes an event except erasure* admits exactly
> one updater: `_redact_in_txn` (the body `redact` and, since tranche 4b, the import's notice application share) tombstones `state` on the redacted edge's prior events (§4c's ruled approach) and touches
> no other column; `tests/test_0029_carrier.py` binds both — the updater's name, its statement's shape, and the
> six kinds.

> **Tranche 4a (2026-09-19), the amendment §4b-iii makes to accepted 0030:** the as-of classifier's closed
> status set gains **`REDACTED`**, the eighth status — a leg after visibility and before parse, keyed on the
> ATTESTATION RECORD carried in `CurrentState.redacted` from the read window (0030's carrier gains the field;
> never the event's kind/reason column, which V-COLUMN-NOT-INPUT forbids, never marker bytes); the
> resolver maps it to `NOT_RETURNABLE` / `redacted-excluded` (the tag tranche 1 registered). 0030's pseudocode
> carries the same leg; `tests/test_0041_readers.py` binds the status, the hidden-stays-hidden order and the
> unattested-marker control.

> **Tranche 4b (2026-09-20), §11.4's refs exemption as landed:** a standing redaction notice writes no journal
> event (it is a `redactions` row with no event), so 0029's `refs` check over the journal never sees it; the
> exemption lands where the notice lives — the doctor's redaction-target check reports a standing notice
> as information, never as a missing-target error. The export format moves 12 → 13 (0014's format rules:
> conditional stamp, older readers refuse).


### 11.4-bis. The two prerequisites, in executable form

**Round-3's seven results collapse to two missing enforcements (§2d-v). Each is
already written as a STRICT XFAIL that flips the day its amendment lands** —
cited here rather than restated, so **the test is the statement of the property
and this section cannot drift from it**:

| prerequisite | the test that is red until it lands |
|---|---|
| **§2d-iv's CLOSURE** — the recognised-kind set closed by a refusal | `tests/test_0041_treatment_matrix.py::test_row46_the_recognised_kind_set_is_closed_by_a_refusal` |
| **§2d-iv's CLOSURE** — quarantine closed to the disclosure | `…::test_a_relation_only_quarantine_is_refused_at_the_write_path` |
| **INV-11's MIRROR** — no non-redaction write may INTRODUCE the marker | `…::test_a_non_redaction_write_may_not_introduce_the_marker` |
| 🔴 **v7 — THE REGISTRY EXTENSION** rows 30/49 require (§4b) | `…::test_the_redacted_reason_is_dispositioned_twice` — asserting **BOTH** `"redacted" in schema.DISPOSITIONED_REASONS` **AND** `RESOLUTION["redacted"] == (NOT_RETURNABLE, TAG_REDACTED_EXCLUDED)`. **One assertion would not be enough**: `asof/resolve.py:113`'s set-equality gate raises `ImportError` on a lone extension, so a test that checked only the registry would pass in a tree that cannot be imported |

> 🔴 **v7 — THE REGISTRY EXTENSION IS AN AMENDMENT TO 0028/0030 AS WELL AS TO
> THIS SPEC**, because `RESOLUTION` is 0028's table and the gate that couples
> them is executed at import. **It is named here so its landing cannot be
> mistaken for a local change to `schema.py`.**

> 🔴 **v7 — THE QUARANTINE ROW ABOVE DOES NOT COVER THE RECORDS ALREADY STORED,
> and §4h is why that matters.**
> `test_a_relation_only_quarantine_is_refused_at_the_write_path`
> closes the pair **going forward**. It cannot reach an edge
> already holding `relation=QUARANTINE_RELATION` with a non-quarantined
> disclosure — **and those exist** (§4h(i), executed). **The write-path refusal
> and §4h's re-establish-or-refuse rule are two halves of one property**, and
> a spec carrying only the first would ship a redaction that promotes a stored
> unverified claim while its own prerequisite test reads green.

#### 🔴 v11 — WHAT MAKES A STRICT XFAIL TRUSTWORTHY, and it is not the strictness (round-5 finding 3)

**The reviewer mutation-tested these and found THREE VACUOUS** — passing against
a no-op `Memory.redact`, against a helper that always returns an empty list, and
against a test that never called redaction at all. **Existence checks wearing
behaviour names.** The second seat then swept every one of the 38 nodes by AST,
asking whether each assertion depends on a VALUE the product computed or merely
on a NAME existing, and re-ran all 11 xfails under `--runxfail` to compare why
each ACTUALLY fails against what its reason CLAIMS. **Both sweeps returned the
reviewer's three and no fourth.**

> 🔴 **AND THE POSITIVE CONTROL FOUND WHAT NO NEGATIVE CONTROL CAN.** The
> after-attestation test asserted a write would be REFUSED — but that write
> SUCCEEDS today as an ordinary upsert, so the test would have gone on xfailing
> **through any implementation whatsoever.** It could never have flipped, so it
> could never have announced the landing it was written to announce.
> **A test that cannot be made green ON PURPOSE is a check in one direction
> only, and mutants that must FAIL will never reveal it.**

**So the rule this section now carries: every strict xfail owes BOTH controls —
a wrong implementation it refuses, AND an honest implementation under which it
PASSES.** `specs/evidence/0041/xfail_mutant_campaign.py` runs 18: the reviewer's 5,
5 more of ours, and **8 positive controls (the fifth added 2026-09-19 at 0041 tranche 1: the landed kind closure is the import-boundary test's positive control, and the reviewer's import-rule mutant now switches that closure off to stay a mutant; the sixth added the same day at tranche 2: the landed `migration.unattested_marker_report` is the migration-report test's positive control beside the in-process honest report, and every report mutant now restores the landed function instead of deleting it); the seventh and eighth added the same day at tranche 3: the landed `Memory.redact` is the positive control of the repeat test and of the after-attestation test, and every redact mutant restores the landed method that install a correct implementation
and require green**. 18 of 18 behave. 🔴 **Only 3 of those 4 cover a STRICT
xfail — the fourth covers an ordinary test — so EIGHT of the eleven strict
xfails still await one, and that remainder is owed at implementation rather
than claimed as done.** ⚠️ **v15 — REFRESHED AT eee8688 (the round-9 verdict: "the former strict xfails now run as ordinary tests").** All ELEVEN have flipped: NO `xfail` marker remains on any test in `tests/test_0041_*.py` (counted by AST over the decorators, 0), and each former one carries a dated `(strict xfail until 0041 tranche N, …)` comment beside it (11). A flipped test passing against the landed implementation IS the honest-implementation control this paragraph asked for, so the eight-of-eleven remainder above is discharged by the flip, not by the campaign. The text above is kept as adopted; the campaign's own figures, which a test derives, are unchanged. ⚠️ **Every figure in this paragraph is DERIVED from the
campaign's own case table by
`tests/test_0041_evidence.py::test_the_11_4_bis_evidence_figures_are_derived_from_the_artifacts_they_cite`,
because round 8 found five counts in this section stale at once. A count
maintained beside the thing it counts is a count that drifts; this one cannot
drift without going red.**

**Evidence rows this section relies on:**

| | |
|---|---|
| the §4h corollary, executable | `tests/test_0041_transition_table.py::test_rows30_49_on_a_frozen_record_absence_survives_and_prose_does_not` — absent stays absent with `active` AND `assertable` unchanged; registered stays registered; only prose becomes the registry value |
| the frozen pre-restriction fixture | `specs/evidence/0041/pre_restriction.sqlite`, sha256 **`741d9417…`**, recorded in full in `pre_restriction_manifest.json` beside the store schema version (14) and the HEAD it was frozen at (`6b8d7575`). 🔴 **10 shapes written through today's write paths** — including the active-episode-with-no-reason case the reviewer reproduced, the historical source-revocation row carrying prose that round 6 required, and the SOURCE-LINKED EDGE that round 7 required so the affected-records assertion has a record to be about. ⚠️ **THE BYTE SIZE IS DELIBERATELY NOT PINNED HERE, and the reason is a trap the artifact has now demonstrated TWICE: this file is 188,416 bytes and has been through TWO SEPARATE REGENERATIONS of its contents — 3 shapes at the first and a tenth at the second — with the digest moving both times and the size never once (bab160a5… → 047f0d11… → 741d9417…, 6 → 9 → 10 shapes, 188,416 bytes throughout).** SQLite allocates by page (4,096 × 46), so **a size pin does not merely go stale silently — IT CAN STAY TRUE WHILE THE ARTIFACT IT DESCRIBES IS ENTIRELY DIFFERENT.** The digest is the fingerprint; the size is an allocation detail. **The count beside this note was itself stale until round 8** — it read "three shapes were added" under a cell that by then said ten, so a reader would take three as the delta that produced ten when it is neither the delta from six nor from nine. Found by the second seat re-deriving the landed text. A test asserts the bytes against the manifest, **so a silent regeneration after the closure lands shows up as a digest change** — which is what makes the evidence rule of §4h(iii) enforceable rather than advisory |
| the campaign | `specs/evidence/0041/xfail_mutant_campaign.py` |

> **A strict xfail is the right form and not a formality.** It is **red-first by
> construction**, it **fails loudly if the property starts holding without the
> amendment**, and **the amendment's landing is what flips it** — so the spec
> cannot claim the prerequisite is met while the code says otherwise. **This
> document has twice asserted a property of a mechanism that did not hold it
> (`TEXT NOT NULL` forbidding `""`; a leading NUL making the marker
> unproducible). A cited strict xfail is what makes the third time impossible.**

**This spec changes contracts other specs own. Each is listed so the owning spec
is swept rather than discovering it later.**

| contract | amendment |
|---|---|
| **journal** (0029) | a new `redacted` event kind; a new `episode_event` table; imported events carry source metadata and destination-local `seq`/`txn` |
| **doctor / integrity** (0029) | 🔴 **the `refs` check must EXEMPT a standing redaction notice.** Today it flags any journaled `edge_id` with no row; a notice imported before its record is exactly that, by design. **Exempt the `redacted` kind in `pending` state and NOTHING else** — the check's value is that an orphan is normally a real defect, and widening it further would spend that |
| **reader** (0030) | `edge_state_at()` gains a **`REDACTED`** state. 🔴 **Today a plain sentinel classifies as `MALFORMED`** — a redacted read must not report as damage |
| **compiler** (0012) | publication is conditional on the store version the inputs were read at (§4e) |
| **export/import** (0006/portability) | 🔴 **`export` carries NO events at all today — verified, and this is larger than a format change.** The record kinds are `edge` and `episode`; anything else raises *"unknown record kind"*. So D2's travelling redaction event **has no existing carrier**, and §8's survival claim depends on building one. §4g is the acceptance contract for a transport that does not yet exist |
| **write path** | writes to an **ATTESTED-redacted** field are refused (INV-11, re-keyed v9); redaction calls `_bump` (§4e) |
| **`why`** (CLI) | renders vocabulary reasons and `legacy_freeform` tokens only |

## 11.5 What a caller is guaranteed after a successful redaction

1. the named content is **absent from every carrier named in the receipt**;
2. the fact that a record existed and was redacted **survives in the live
   store**, and travels on export as a notice (D2);
3. **derived records that may still carry the content are NAMED in the receipt**
   (F6) — they are *not* redacted, and the caller can redact them; 🔴 **v15 — WIDENED, ruled by the owner 2026-10-02: "records that may still carry the content, found by an identifier join in either direction (derived from the target, or its source)".** "Derived" above is v14's word, kept as adopted; a source episode is not derived from the edge extracted from it, and round 10 measured it unnamed on the `remember()` path. The operation is unchanged; §8 (v15) states the three link strengths.
4. **receipt-table completeness is reported, not assumed** (F4): if a digest
   domain could not be recomputed, `receipts_complete=False` says so.

> **Points 3 and 4 are limits stated as guarantees, and that is deliberate.** A
> caller can act on a named limit. The failure this spec keeps circling — the
> false negative on `original_relation`, the `TEXT NOT NULL` claim, the flat
> *"no row is deleted"* — is never that something was incomplete. **It is that
> the prose claimed more than what was done**, and a reader has no way to see
> the gap from inside the document.

## 11.6 Replies, and the notice binding (v16, amendment `0047/0041-replies`)

> The amendment's current contract, folded at v16. It governs as the rest of §11 does; §2d-iii-ter governs its per-candidate rows.

### 11.6.1 Why

0047 adds a `replies` table whose `text` holds the subject's own words ABOUT an edge, and those words routinely
restate it (*“I never took sertraline”*). Redact the edge, and a surviving reply re-publishes what was redacted. So
whatever carries a reply must be treated in the redaction's transaction — 0041's job (0047 §1c: no carrier avoids
this).
0041's sweep recorded (L221): *“No other TEXT/BLOB column carries content.”* The census test reproduces the carrier
enumeration byte for byte and goes red when a new content column exists. **That is the claim working as designed;
this amendment is its answer.**

### 11.6.2 Sites changed

| site in 0041 / the code | change |
|---|---|
| **the sweep record at L221** (a dated record of dev's 2026-09-13 sweep, in a blockquote; L220 before the fold) | **NOT rewritten** — it is a record. An annotation line is APPENDED after the blockquote: *“⚠️ Amended by `0047/0041-replies`: `replies.text` (0047) carries content; it is treated with its edge (§2d-ii, REPLACE).”* |
| **§2d-ii, the treatment map** | gains: **`replies.text` → REPLACE** with the marker. The ROW is KEPT (append-only survives), `kind`, `target`, ids, `actor` and timestamps are **PRESERVE** — the map stays TOTAL over the table. A NULL `text` (a `resolve` row carries none) stays NULL: the permitted treated-or-absent shape |
| **§2d-ii, the treatment map: every new DIGEST carrier** | **`replies.request_digest` → REPLACE** and **`request_registry.request_digest` → REPLACE** (for every verb's row whose `target_edge_id` is the edge; 0008 §6g), beside 0041's existing `confirmations.request_digest` → REPLACE. A reply's request digest binds its free text, so a surviving copy would still validate guesses of that text. *The census of new carriers is complete: the three digest columns above, `replies.text`, and the act rows' portable fields (`act_uid`, position, origin), which hold no content. An imported or exported act's digest is one of these columns and is treated by the same rows.* |
| **§2d-iii-bis, the per-candidate map** | three more rows, `replies.request_digest`, `request_registry.request_digest` and the backfilled registry copy of `confirmations.request_digest`, each REPLACE, shape “the marker”; and one row: `replies.text`, REPLACE, resulting shape “the marker”; **the first side-table column in the map that holds FREE TEXT** (every other side row holds a digest, a closed value or an id), said plainly |
| **`SIDE_TABLE_TREATMENTS["edge"]`** (`redaction.py` L99) | gains `("replies.text", REPLACE)`, `("replies.request_digest", REPLACE)` and `("request_registry.request_digest", REPLACE)`. `carrier_paths("edge")` (L108) DERIVES it, so a notice's `fields` may name it with no second list |
| **§2d-iv** | the reply writer is a WRITE PATH that must refuse: a `kind` outside the closed set; and **INV-11's mirror** — an ordinary reply whose text carries the marker (a non-redaction write may not introduce it) |
| **§4g, the import contract** | the rows in §4 below |
| **the receipt / the attestation record** | the redaction's record names `replies.text` in `fields` when the edge had a reply |
| **the census's committed output** | moves by exactly the `replies` table's carriers |
| **`doctor`** | one more `refs` row: a reply whose edge is absent (0047 INV-R5); every PENDING notice is listed, with its source identity, as awaiting the user's confirmation; a STANDING notice's row no longer reads “not damage” |
| **§4g, the notice binding** | the rows of §11.6.6's table replace 0041's “holds the record: apply the redaction”: a unit carrying a notice's record unredacted refuses the whole import wherever the record would be admitted under the notice (a trusted restore; a default import that creates it), and over a HELD target in a default import the notice is PENDING with the held copy kept; a held target's notice in a default import is recorded PENDING, never applied; a standing notice refuses an inserted arrival that does not show the redaction, and is PENDING (default) or applied (restore) on one that does. No rule compares a notice's origin |
| **a new host verb** | `confirm_notice(user_id, notice_id)` applies a PENDING notice as a redaction by this store (§11.6.6). The only path by which a default-mode notice changes held content. *v16.1 (T4):* a read-only host call, `pending_notices(user_id)`, lists the user's pending notices, oldest first: the notice id `confirm_notice` takes, the target, the reason, the claimed and unauthenticated source, and the time recorded. It reads one user's rows only. It is an operator surface by decision, with no CLI verb |
| **`redacted_targets()` and the two local-writer refusals** (`add_edge`'s upsert, `add_episode`) | count APPLIED attestations only: a pending or standing notice is not a redaction of anything this store holds |

### 11.6.3 Untrusted inputs

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| an ordinary reply's text (0047's writer) | 0047 refuses | — | — | carries the marker → **refused at write** (INV-11's mirror) | **INV-RR1** |
| an imported reply row | — | the existing import refusals | — | text = the marker WITHOUT a notice in the unit attesting `replies.text` for its edge → **the unit refused** (a fabricated tombstone) | **INV-RR3** |
| an imported notice naming `replies.text` | — | a field that is not a carrier path of `edge` → refused (§4g's carrier-path rule, L1467, unchanged) | — | a notice whose body differs from a held one of the same source identity → the whole import refused (0041, unchanged) | 0041 |
| an imported notice's TARGET, in a default-mode file | — | — | — | names a record this store already HOLDS (a local fact, or a genuine copy of another store's record) → **recorded PENDING, never applied**; held bytes unchanged | **INV-RR10** |
| an imported notice's `origin`, in a default-mode file | refused (0041, unchanged) | refused (unchanged) | — | ** decides nothing**: recorded as the notice's source identity, compared by no rule. Whatever origin it claims, the notice only attests what its file shows, refuses a unit carrying its record unredacted, or waits PENDING | **INV-RR10**, **INV-RR12**, **INV-RR14** |

### 11.6.4 Assertions about reach

Commands run from the repository root at `af1e564` (research, 2026-10-14), except that rows 2 and 3 read THIS document's own lines as folded at v16. The amendment's rows 5–11 recorded the code at `1fd3e52`, before the notice-binding hotfix (v15.6), and are not carried; its rows 1–4, 12 and 13 are, re-derived here.

| # | assertion | command | result |
|---|---|---|---|
| 1 | the side-table treatments, and the derivation a notice's fields use | `grep -n -e "^SIDE_TABLE_TREATMENTS = {" -e "^def carrier_paths" src/veracium/redaction.py` | READ: L99, L108 |
| 2 | 0041's content-column record, and the census that enforces it | `grep -n "No other TEXT/BLOB column carries content" specs/0041-targeted-redaction.md; grep -n "def test_the_carrier_enumeration_reproduces_its_committed_output_byte_for_byte" tests/test_0041_evidence.py` | READ: L221 (this document) · L75 |
| 3 | a notice's fields are derived carrier paths; an arrival under its notice is written treated | `grep -n -e "A notice's \`fields\` are the declared kind's CARRIER PATHS" -e "When it ARRIVES again in a unit carrying its notice" specs/0041-targeted-redaction.md` | READ: L1467, L1478 (this document) |
| 4 | no reply table exists today | `grep -rn --include="*.py" -e "CREATE TABLE replies" src/; echo "exit $?"` | EXECUTED: `exit 1` (no match) |
| 12 | 0009 compares the CAPPED incoming form, and a held record whose unit carries a notice for it is skipped by 0041 §4g's held-differs rule before 0009 can refuse | `grep -n -e "^def held_differs_verdict" -e "existing records differ from the capped incoming form" src/veracium/portability.py; grep -n -F '_v = held_differs_verdict(store._completed_attestation(target_uid, "edge", edge.id)' src/veracium/portability.py` | READ: L120, L289 · L1235. EXECUTED by research (`839ddafa`): with e-a held from a restore, a default import of its plain copy is refused (0009, the capped form differs); with the redacted export (treated copy and notice) or the notice alone, it is admitted and the notice reported `held-target`, the held bytes unchanged. With e-a held from a default import, each of the three is admitted. |
| 13 | with no notice in the unit, an arrival under this store's completed attestation meets INV-11: a differing held record through the held-differs verdict `attested-redaction`, a created one at the commit | `grep -n -e "if attested_complete and not noticed:" -e "^def held_differs_verdict" src/veracium/portability.py; grep -n -F 'if self._completed_attestation(user_id, "edge", edge.id) and ("edge", edge.id) not in notice_targets:' src/veracium/store/sqlite.py` | READ: L289, L303 · L2089. EXECUTED by research (`91b87bde`, reproducing dev's probe): a store redacts its own e-1, exports, strips the notice and re-imports into itself. Default: REFUSED, “is redacted here (a redaction record attests it) and the file carries no notice for it”. Restore of the equal copy: admitted, skipped 1, unchanged. Restore of a content-changed copy: REFUSED, the same message. |

### 11.6.5 Trust classes

n/a beyond 0041's own: the treatment is by the redacted EDGE, whatever its class; a reply carries no trust class of
its own (0047 §3).

### 11.6.6 Behaviour

**At redaction (in its transaction):** every `replies` row of the edge has its `text` AND its `request_digest`
REPLACED with the marker; every request-registry row whose `target_edge_id` is the edge has its `request_digest`
REPLACED (R2-05); rows, kinds, targets and ids kept; the attestation names every treated path. **After it, a retry
under any of those ids returns the terminal `request_redacted`, whatever its payload** (0008 §6g): it
neither replays the original, because the verifier is gone, nor admits a new act, because the id stays held. *That
resolves the tension the verdict named: keeping the verifier would defeat the redaction, and replacing it ends
ordinary request equality, so the outcome is terminal by design.* **Migration:** the registry step backfills an
already-redacted confirmation's registry row with the marker, never with the live digest. **A new reply to a redacted edge is REFUSED** (0047; the
reviewer agreed: a content reply attached to a tombstone).

**At import — the reply rows in 0041 §4g's terms** (the whole file preflighted against destination ∪ incoming, after
user/id remapping, then ONE transaction — 0047 R1-07):

**What COVERS means for a reply row.** A redaction notice for the reply's target, held or arriving, covers
the row iff its `fields` attest EVERY non-NULL content carrier of that row: `replies.text` and
`replies.request_digest` (a `resolve` row's NULL `text` needs no attestation). A notice that attests only one of them
does NOT cover the row (0008 §6e: coverage is all or nothing per row). Its foreign body is never
enlarged to make it cover. ** Coverage counts every notice for the target, whatever its state (applied,
pending, standing or arriving)**, and **this store's own attestations**: a redaction by this store (local, a
confirmed notice, or a trusted restore's application) covers exactly the paths it attests, every carrier path of the
target after a total treatment. Coverage counts all of these because coverage decides only what an arriving row may be ADMITTED as and how a
replay compares. It never writes held content. Only an APPLIED notice writes held content (the binding table below).

| arriving reply row | its target's state (a notice in the file, or one held) | outcome |
|---|---|---|
| ordinary text | **not attested redacted** | admitted (0047's other checks apply) |
| ordinary text | attested redacted by a notice that **covers** the row | **written in its TREATED shape**: the marker in `text` AND in `request_digest` (§4g's principle at L1478, for a record, extended to reply rows by this amendment) |
| ordinary text | 🔴 attested redacted by a notice that attests **neither** of the row's content carriers (a notice from before this feature, or one made when the edge had no reply) | **the unit is REFUSED** (R2-06): content is never attached to a held redacted target through an uncovered cell, and a foreign notice's immutable body is never rewritten to extend it. *0041's `_treated_on_arrival` already refuses record carriers an old completed attestation does not cover; this keeps that boundary for side rows* |
| the marker | attested redacted, **covering** the row | **admitted as a redacted reply** — the round trip R1-07 found refused |
| any | attested redacted by a notice that attests SOME of the row's content carriers but not all (**partial coverage**) | **the unit is REFUSED**: a carrier the notice does not attest is never treated in its name |
| the marker, its `act_uid` held as an ORDINARY reply (record first: the reply was imported, then redacted at its source) | the arriving notice covers the row | **trusted restore:** **the authorized transition** (0008 §6e): the held row's `text` and `request_digest` become the marker, written by the notice's redaction in the import's transaction. **Default import:** an exact replay under the coverage (a no-op); the held row is unchanged, and the notice is recorded PENDING (the binding table). Either way, every structural field must be equal, else the unit is refused |
| the marker | not attested, or **not covered** | **the unit refused** (INV-11's mirror at import: a fabricated tombstone) |
| any, edge absent from destination ∪ file | — | **the whole file refused before any write** (0047 INV-R11) |

**A notice never lands content and never removes it on an untrusted file's word; it is applied, refused, or left
PENDING for the user (the owner's rulings of 2026-10-13: refuse where content would land, pending only to attest,
no origin binding).** An arriving notice's effect depends on its target's state at this import, on the file's copy of
the target's record, and on the mode. The file's copy **shows** the redaction when treating it under the notice's
fields would change none of its record carriers (the bookkeeping paths `journal.state` and `provenance.disclosure` are
not record carriers). An export writes a redacted record as stored, in its treated shape, so every honest same-file
pair shows it. *v16.1 (T4, research's B1):* an export carries a notice only where the pair it makes shows the redaction. It carries every APPLIED notice, whose record it writes treated, and a STANDING notice only when the file does not carry that notice's target. It carries no PENDING notice, and no standing notice whose id the user has since written locally. Either would sit beside an untreated record of its id, which the table below refuses, so the store's own export would not restore (measured at `a2dc7b0`: refused on a restore into a fresh store, a default import into a fresh store, and a restore into the store itself). The cost: a restore does not reproduce those notices, and re-importing the source file records them again.

| the notice's target | default import | trusted restore (own history, 0005) |
|---|---|---|
| the unit carries the target's record **UNREDACTED** (it does not show the redaction) | where the import would create the record: **the whole import REFUSED**, naming the notice: admitting the record would land content its source says it redacted, and redacting it would destroy the user's fact when the pair comes from a poisoned store's own export (the poisoned-export case of internal finding 0041-PA1). Over a HELD target: the held-target row below (PENDING, the held copy kept) | **the whole import REFUSED**, whether the record is created or held |
| *the exception to the row above*: the notice is one this store already holds as **APPLIED** (its own redaction, or the same witnessed notice applied before) | `existing`: the arrival is written in its attestation's treated shape (0041's R10-02 rule), and nothing lands or is removed. A DIFFERENT notice over a record with a completed attestation takes the row above. The exception needs a notice for the target IN THE UNIT. With none, an arrival under this store's completed attestation meets accepted 0041 INV-11 (§4b-ii), unchanged: a held record whose arriving form differs from it is refused by INV-11, through 0041 §4g's held-differs rule (verdict `attested-redaction`; in a default import the capped form differs from a store's own record, so its own redacted export re-imported without the notice is refused there); an equal arriving form is an exact no-op (a trusted restore of the store's own export); a created arrival is refused at the commit (§11.6.4 row 13) | same |
| **created by this import**, its record showing the redaction | **applied** in the import's transaction: it attests what arrived treated, the fresh propagation 0041 §4g exists for | same |
| **held before this import** (a local fact, or a copy of another store's record) | **never applied.** Recorded **PENDING**: its source identity and body kept immutable (0041's discipline), listed in `notices_not_applied` with reason `held-target`, and by `doctor`. Every held byte is unchanged | the unit carries the record showing the redaction: **applied**, as a redaction BY THIS STORE (below). No copy in the unit: **applied** only if the held record already shows the redaction, otherwise **PENDING**, reported `record-not-in-file`. Applied here is still the total treatment by this store: the record's carriers change nothing, because it already shows the redaction, and held acts still carrying content are treated |
| **absent, and not in the unit** | **STANDING** (below) | same |

- **A PENDING notice is not an attestation.** It is not listed in `redacted_targets()`, refuses no local write, and
  writes no held content. A repeat DEFAULT import of it is `existing`; in a trusted restore the table weighs it
  like any arriving notice, and where the table applies it, the pending row becomes applied, its body unchanged. **`confirm_notice(user_id, notice_id)`** applies it as a
  redaction BY THIS STORE: total over the target's carriers under this store's own treatment map, exactly as a local
  redaction is. Every held carrier of the target is treated, held acts that are not in any unit included, **even when
  the notice is older or partial and does not attest them**. This store attests what it treated; the foreign notice's
  body is unchanged. *That total treatment is kept for a trusted restore and for the confirmation: 0041's
  binding rule says content-derived divergence “is not grounds to keep content the source says was redacted”, and a
  held reply restating a redacted edge is that content (0047 §1c). It is no longer applied on an untrusted file's
  word.* A pending notice whose target is later deleted is inert. A pending notice is weighed only when it
  arrives: an import that re-creates its target leaves it PENDING. It was recorded beside the user's content, and a
  re-created record is that same state. Only `confirm_notice` or its own re-arrival in a trusted restore applies it. Confirming one whose target this store has since
  redacted adds its attestation and treats nothing new. There is no dismiss verb in this amendment: an unconfirmed
  notice stays pending, listed. *v16.1 (T4 stage 2, T4-1):* the table's CREATED rows are weighed before this paragraph's rules. A pending notice whose target was deleted, re-arriving IN a unit that creates the target's record, takes the created rows in both modes. It is refused whole if the record does not show the redaction: row 1, whose exception names only a notice held as APPLIED. It is applied if the record shows it: the unit attests itself, nothing held changes, and the outcome is a fresh store's. “An import that re-creates its target leaves it PENDING” governs a unit that does NOT carry the notice. A pending notice keeps its stored reason through every import that leaves it pending, default or restore (IO-II-1); only its application moves it.
- **A STANDING notice names no record this store holds.** It is not listed in `redacted_targets()`, and it never
  refuses a local write: a local write of its id is admitted, and the standing notice never completes on that record,
  because the record was not created by an import. **On a later arrival THIS import creates:** an arrival that does
  not show the redaction **refuses the whole import** (content would land under a notice), in both modes; an arrival
  that shows it is **PENDING** on it in a default import, for the user's `confirm_notice` (an attestation of data this
  store then holds, on an untrusted file's word), listed in `notices_not_applied` with reason `standing-arrival`
 , and is **applied** in a trusted restore (the total treatment; the record is new and already shows the
  redaction, so nothing held changes). A standing notice therefore never removes held content. *v16.1 (T4):* this arrival rule weighs a standing notice that is NOT in the unit, a notice and a record from different files. When the unit carries the standing notice's own copy beside the record it creates, the table's created rows decide, as for a store that never held it: refused unshown, applied shown. A standing notice over an id since written locally is weighed, when it re-arrives, as a HELD target (research's B3): PENDING `held-target` in a default import, and the held-target restore row in a trusted restore.
- **Origin decides nothing (the owner's ruling).** A notice's origin is recorded as its source identity (0041's
  discipline) and is compared by no rule here. With the rules above, a notice changes content only through the user's confirmation or a trusted restore
  whose file shows the redaction, whatever the origins, so the binding decided only whether a treated arrival was
  attested automatically, and it misfired on a legitimate case: a store B that redacts a record it holds from store A
  issues a notice with origin B over a record with origin A. Origin is also unauthenticated (0006 Q4): a store's
  origin is in every one of its exports and every relay of its records (I2b). 0006 I5 is unamended.

**Older notices and confirmations.** The coverage rule is the same for a confirmation, whose one content
carrier is `confirmations.request_digest`. A confirmation arriving onto a target redacted under a notice that does
not attest that path refuses the unit: R2-06's rule, applied to the confirmation's carrier. *Intended: confirmations
were not exportable before 0008 v6, so no import that was admitted before is refused now.*

**0009 before the table (measured: §11.6.4 row 12).** 0009's same-id comparison runs on the CAPPED incoming
form a default import would store. Where that form differs from the held record and the unit carries no notice for
it, the whole import is refused before any notice is weighed. Where the unit carries a notice for it, 0041 §4g's
held-differs rule runs first: the arriving copy is skipped (never written), and the notice is weighed by the table.
So the held-target row is reached in a default import whether the held copy came from a restore or a default import,
and whether the unit carries a copy or none.

**Notice-first, record-first, same file:** order inside a file is immaterial (one preflight, one transaction, over
the staged union). Across files, a STANDING notice completes on a later arrival only under the binding above.
**Repeat import:** 0008's precedence (§6e). Equality is decided on the CANONICAL TREATED
PROJECTION under the staged union's coverage: a covered content carrier compares as the marker on both sides. So a
reply written treated on its first import is an exact replay of the same untreated file imported again (a no-op),
not a conflict. A difference in any structural field refuses the whole unit. **This matrix composes with 0047's
target refusal:** a default import of a NEW reply over a held target is refused by 0047 first, whatever its text.

### 11.6.7 Regimes

| regime | behaviour |
|---|---|
| no replies | the reply rows change nothing, and the census output moves only when the table exists. **0041's import behaviour still changes**: §4's notice table governs every import (a held target's notice PENDING in a default import, standing notices inert to local writes and readers, refusal where content would land), whether or not any reply exists |
| edge with replies redacted | texts replaced, rows kept, attested |
| redacted export → fresh store | admitted via the notice path (the round trip) |
| a file with a marker reply and no notice | refused |
| a default file whose notice names a held local fact | the fact unchanged; the notice PENDING, listed; the user's `confirm_notice` applies it |
| a default file whose notice names an absent id, then the user writes that id | the write admitted; the standing notice never completes on it |
| a standing notice, then a default arrival of its id that shows the redaction | admitted; the notice PENDING on it, whatever the origins |
| a standing notice, then an arrival of its id carrying content | the import refused |
| *v16.1:* a store holding a pending notice, or a standing notice over an id since written locally, restores its own export | admitted in every mode: the export carries neither notice (§11.6.6), so neither is reproduced |
| a store's own export carrying a notice beside an untreated record of its id | refused wherever the record would be admitted under the notice (a trusted restore; a default import that creates it); over a held target in a default import, the notice PENDING and the held copy kept |
| a default file whose notice claims this store's origin | treated as any other notice: origin decides nothing |

### 11.6.8 Invariants

| | invariant | mutant that must fail |
|---|---|---|
| **INV-RR1** | an ordinary reply write carrying the marker is refused | accept it |
| **INV-RR2** | redacting an edge REPLACEs every reply's text in the same transaction; rows, kinds, targets kept; the attestation names `replies.text` | delete the rows (append-only broken); keep the text (0041's claim broken); omit the field from the attestation |
| **INV-RR3** | a marker reply is admitted on import iff its unit attests `replies.text` for its edge; an ordinary reply under such a notice is written treated | refuse every marker reply (the valid round trip fails); admit a marker reply with no notice |
| **INV-RR4** | `replies.text`, `replies.request_digest` and `request_registry.request_digest` are in `carrier_paths("edge")` by derivation | list one a second time by hand |
| **INV-RR5** | after an edge's redaction no request digest on it survives in `confirmations`, `replies` or the registry, and a retry under such an id returns `request_redacted` for the same AND for a different payload (R2-05) | treat `replies.text` only (the verdict's countermodel); replay "same payload" by comparing against a treated digest |
| **INV-RR6** | an ordinary reply arriving onto a target attested redacted by a notice that does not cover `replies.text` refuses the unit (R2-06); this store's own attestation covers what it attests | treat an absent field as permission (the verdict's held-notice probe keeps the content); rewrite the foreign notice to add the field; count only foreign notices as coverage (the coverage check misreads this store's own redaction) |
| **INV-RR7** | the registry step backfills an already-redacted confirmation's registry row with the marker | copy the live digest |
| **INV-RR8** | an ordinary reply restored onto its held redacted target under a covering notice is written with BOTH `text` and `request_digest` treated, and the same file imported again is a no-op | treat `text` and keep the digest (the round-3 witness's first admission); compare the untreated arrival with the treated held row (its second import refuses) |
| **INV-RR10** | a default import never changes a held record's or held act's bytes through a notice: a notice whose target was held before the import is recorded PENDING, listed in `notices_not_applied` with reason `held-target`, and every held row (the record's whole json, every carrier table row) is byte-equal before and after; so whether the held copy came from a restore or a default import (0041 §4g's held-differs rule skips the noticed copy before 0009 compares) | apply it (the defect at `1fd3e52`, on main and in no release); apply the authorized transition in default mode; list it in `notices_not_applied` and apply it anyway; refuse by 0009 a noticed held record whose capped copy differs (the held-target path unreachable for a restore-held record) |
| **INV-RR11** | a pending notice is not an attestation (absent from `redacted_targets()`, refuses no local write), and `confirm_notice` applies it as this store's total treatment, the foreign body unchanged; every application by this store is that total treatment, a restore's where the held record already shows the redaction included; a pending notice re-arriving is `existing` in a default import and weighed by the table in a trusted restore; an import that re-creates its target leaves it pending | count a pending notice in `redacted_targets()`; refuse a local write under it; confirm with the notice's fields only (a held reply survives); attest only in a restore whose held record already shows the redaction (a held reply keeps its content); count a restore re-arrival `existing` (the restore never applies it); re-weigh a held pending notice when an import re-creates its target |
| **INV-RR12** | a standing notice refuses no local write and is absent from `redacted_targets()`; on an arrival this import created, it refuses the whole import if the arrival does not show the redaction (both modes), and is PENDING (default, reason `standing-arrival`) or applied (restore) if it does; a locally written id is never completed by a later import; no rule reads the notice's origin. *v16.1:* “never completed” is the arrival rule's: the arrival loop never completes it. A re-arrival of the notice itself is weighed by the table as a held target (§11.6.6) | complete it on every present target (the arrival loop before the v15.6 hotfix); complete it on an untreated arrival (content removed); admit an untreated arrival (content lands under the notice); attest a treated arrival automatically in a default import; refuse the local write (the pin); compare origins (origin binding: a legitimate B-over-A notice misfires); leave a pending standing arrival out of `notices_not_applied`; *v16.1:* leave a re-arriving standing notice over a local write standing; pend a standing notice whose own copy arrives with the record its unit creates, showing it |
| **INV-RR14** | a unit that carries a notice's target record unredacted refuses the whole import wherever the record would be admitted under the notice (a trusted restore; a default import that creates it), unless the notice is already held as applied (`existing`, the R10-02 rule, which needs a notice for the target in the unit: with none, 0041 INV-11 refuses a differing or created arrival, and an equal arriving form is a no-op); *v16.1:* a notice held PENDING (its target since deleted) or STANDING is not excepted (T4-1); a default import over a held target records it PENDING with the held copy byte-equal; a same-file notice whose record shows the redaction is applied to a created record | apply it to the created record regardless (hotfix candidate 1: the poisoned export redacts the user's record in a second store); admit the record and skip the notice (content its source redacted lands, as in the hotfix's candidate 1.5); admit the record and pend the notice (content its source redacted lands, as in an earlier draft of this rule); apply it in a restore to a held record whose file copy is unredacted (the same-store restore); test only the edge's own fields and skip an episode; write treated an arrival under a completed attestation whose unit carries no notice for it (0041 INV-11 refuses it); let a default import skip a store's own redacted record that arrives without its notice (INV-11 refuses it, by the reason `attested-redaction`); *v16.1:* weigh the pending shortcut before the created row (T4-1: a deleted target's pending notice admits its unredacted re-creation) |
| **INV-RR13** | **Withdrawn; not a current invariant.** The number is kept so later numbers do not move; the Version history records what it said | — |
| **INV-RR9** | a notice attesting only some of a row's content carriers refuses the unit; a held ordinary reply receives the treatment from an arriving treated copy and its notice, and nothing else changes | admit under partial coverage; refuse the treated arrival over the held untreated copy (the round-3 witness 2 keeps the content); let the transition change a structural field |

**Closure evidence (R1-07, the reviewer's list):** fresh ordinary round trip; fresh REDACTED round trip; idempotent
replay; user remap; held-target import; negative controls for an orphan, a fabricated notice, a marker-containing
ordinary reply. **R2-05, R2-06:** an edge with both a local confirmation and a text reply, redacted, then every
act table and the registry inspected, with same- and different-payload retries and the redacted export/import path;
a pre-feature notice, a post-feature notice made when no reply existed, complete and partial coverage, held targets,
same-file arrival and notice-first order, with an unredacted-target positive control and a valid redacted-reply round
trip. *Model: dev's model II carries the import matrix (its G10), the redacted requests and the backfill for INV-RR5 and RR7 (its G18), and notice coverage for INV-RR6 (its G19). INV-RR8 and RR9 are notice coverage too (its G19), with 0008's INV-I4/I5 (v6). Product tests at the implementation gate. **Model scope:** model II's episodes carry one content carrier, so RR14's episode mutant tests the KIND (the refusal is not edge-only). The fixed point over every episode carrier path is PRODUCT: `redaction.shows_redaction` over `carrier_paths("episode")`, tested at the implementation gate.*

**Controls (the round-3 verdict's lists):** ordinary replay; treated replay; notice-first and record-first
arrival; a valid redaction update; a second hop; negative controls for a structural change under a held `act_uid`,
incomplete (partial) coverage, and a new untrusted act over a held target.

### 11.6.9 Failure modes, claims and limits

Redaction of a reply's text is irreversible by design (0041). A refused import writes nothing.

**Claimed:** a reply never outlives its edge's redaction as content, **and no request digest on the edge survives as a
verifier of that content**; a redacted reply round-trips as a tombstone and only as one, and never arrives with
content onto a target redacted under a notice that does not cover it. ** Claimed:** no notice lands content or removes it on an untrusted file's word: a
unit pairing a notice with its record unredacted is refused wherever the record would be admitted under it, and held data changes through a notice only by a
trusted restore whose file shows the redaction, or by the user's confirmation. **NOT claimed:** that a reply which RESTATES a different, unredacted edge is treated (a reply is treated
with the edge it targets, only). **NOT claimed:** (1) that a source's redaction reaches a record this
store ALREADY holds without the user's confirmation; in a default import it waits, pending, which is the cost of not
trusting a file's word. (2) That a notice is genuine: origin is unauthenticated and decides nothing. **In a default import** a forged
notice can at most leave a PENDING notice; it removes no held content. **In a trusted restore** (own history, 0005),
a notice is applied as this store's TOTAL treatment wherever §11.6.6's table applies it, so it can treat held side rows
(replies, confirmations, registry digests) that still carry content; that is the restore's trust, not the file's. (3) That a pending notice is genuine: the confirmation surface shows its claimed source as
testimony, unauthenticated. (4) That a file pairing a notice with an older, unredacted copy of its record imports: it
is refused whole wherever the record would be admitted under the notice (over a held target in a default import, the
notice is PENDING and the held copy kept), including a genuine combination of an old record with its later notice (the remedy is an export
taken after the redaction).

---

## Implementation acceptance — round 14 (v15.5)

**The implementation is ACCEPTED**, at pin `8a54a87d7b0f22b1e2ca2bcc5359568e4f357823`, package sha256
`99a4985c83758331a3d78a89e2e79e24e46e7c2a6d104a5a3e65b1560ab2f617`, against v15.4, by the external reviewer's
round-14 verdict (`0041-round14-verdict-verbatim.md`): the sixth implementation review (rounds 9 to 14) after the
design was accepted at round 8. *"Verdict: ACCEPTED. The implementation at this pin closes both round-13 findings and the shared-carrier observation. No new blocking or nonblocking finding is raised."*

**What the acceptance covers is bounded, in the verdict's own words:**

> Acceptance remains bounded to the documented operation and receipt, including the existing limits: other records containing the content require separate redaction; exact source/outcome joins and unlinked correction/dispute domains have different link strengths; unlinked supersession receipt digests may survive with conservative incompleteness reporting; contention cost is not quantified; legacy prose cannot be restored until treated; unsupported unreleased schemas and bodyless witnesses are not supported migration inputs. Earlier backups, host-held pointers and identifier-shaped disclosures remain outside the removal guarantee. This review does not convert these named limits into stronger claims or certify every unrelated accepted specification.

This specification does not restate those limits as anything stronger. *"Store schema 15 and export format 13 remain unchanged."*

**The 0014 §2c rider.** *"Separate 0014 §2c rider sign-off: the contract accepted at round 13 is unchanged."* Its implementation is accepted on three conjunctive conditions, recorded beside the
rider in `specs/0014-maintenance-attribution.md`:
1. *"A valid notice accounts for this resolved held output, in the same unit or already held; another arrival’s notice cannot authorize it."*
2. *"Every projected difference is both named by the notice and in the episode carrier domain; structural lineage/operation/index changes retain their refusal."*
3. *"Each differing field’s held or incoming whole value equals the marker."*

**Two nonblocking requests, queued with dev; neither is a condition of this acceptance:** a small machine-readable
table per permutation (raw id → arriving subject → resolved held id → rebound notice target), and, when a historical
reproduction runs at a corrected pin, its pre-fix FOUND expectations labelled as such or paired with expected outcomes.

---

## Review closure

**PROCESS §4a: a spec at `accepted` carries one row per review finding, with
evidence a reader can RUN or OPEN.** Everything between the markers below is
GENERATED from `specs/reviews.py` and `specs/closure_findings.py` — the round
index from the first, the per-finding ledger from the second, validated against
each other on `(spec, kind, round, id)` exactly. **Do not edit it here.** A
ledger maintained beside the thing it summarises is the defect this project has
paid for most often, and the whole point of generating it is that a round
appearing in one and not the other is impossible rather than unnoticed.

**Two conventions a reader needs, and no count of them is written here.** A
round has TWO rows — the **SENT** dispatch record and the returning **verdict**
— labelled so the two are never summed; the totals are in the generated block
below, which derives them. And **some rows cite a FOLD COMMIT rather than a
test**, because for those findings the fold WAS this document's text: the line
had no implementation to point at, and P4's rule prefers an openable commit to a
grep that any file containing the new wording would satisfy. **Those rows are
enumerated in
`tests/test_spec_gate.py::test_new_closure_evidence_is_behavioral`, which is
where the list is maintained and where adding one is a visible diff**, and their
cost is pinned rather than absorbed: **a reviewer holding only the sealed archive
has no `.git` and cannot run them**, and
`::test_the_count_of_closure_evidence_unrunnable_in_a_package_is_pinned` fails
the day that number moves without a reason beside it. Every other row cites a
pytest node or the mutant campaign and runs anywhere.

> ⚠️ **This paragraph deliberately states no total.** The first draft of it said
> "eight external rounds, sixteen rows" and "19 of the 34" — hand-carried counts
> in the one section of this document whose entire subject is that a summary
> maintained beside the thing it summarises drifts. **Implementation review will
> add rounds and rows to this ledger**, at which point both figures would have
> been quietly wrong, in a paragraph introducing a generated block that has them
> right.

<!-- GENERATED:review-closure -->

**1 internal round(s) and 14 external round(s) with a returned VERDICT are recorded for `0041`; 14 package(s) were dispatched** — counted from `specs/reviews.py`, which is the source this block is generated from. A round appearing here and not there, or the reverse, is impossible by construction. **SENT rows are dispatch records, not outcomes**, and are labelled below so the two are never summed.

| round | date | findings raised (from `raised=`) | verdict (compressed) |
|---|---|---|---|
| internal 0 (verdict) | 2026-10-13 | 1 | POST-ACCEPTANCE DEFECT, SELF-FOUND AND FIXED — THE NOTICE-BINDING HOTFIX (dev and research; the owner's rulings, first-hand: fail closed, all three arms; the fixed point in both modes; a file pairing a notice with its record unredacted refuses whole). Found while encoding the 0045-0047 round-4 refer… |
| external 1 (SENT) | 2026-09-15 | — | SENT (round-1 package 2e82485ea6e75bbb6054429c0b480b1f2ff1d9567ccbf82ed8f347f658a57c9a @ pin 436e4d4b0bc70afe998560b2512715267113b3dd, CI 34920124502; 0041 v2.1; fresh-clone capture at the pin: 3237 passed, 11 skipped, 2 warnings in 1678.76s (0:27:58)). 0041 v2.1 — the line's FIRST seal and first di… |
| external 1 (verdict) | 2026-09-15 | 7 | RETURN for amendment — "The feature is worth building." Seven findings, all specification-level. F1 the content-carrier inventory is incomplete (`Edge.original_relation` classified non-content while ingestion preserves an unrecognised extractor relation there verbatim — confirmed to persist AND expo… |
| external 2 (SENT) | 2026-09-15 | — | SENT (round-2 package 1a0dc8c9171e35891ea48c3506f1225d6d6fcdd5eb87bcb5a07faa95ada0306b @ pin dc695b9913f7f68d8b77798fcfb8702798ea1a93, CI 34993768185; 0041 v3.2; fresh-clone capture at the pin: 3242 passed, 11 skipped, 2 warnings in 703.13s (0:11:43)). 0041 v3.2 — round 1's seven findings folded at … |
| external 2 (verdict) | 2026-09-15 | 7 | RETURN for amendment — ROUND-1 F6 EXPLICITLY CLOSED on the owner's ruling. Seven implementation-contract findings: F1 the semantic-rebuild exemption does not hold ACROSS DATABASE CONNECTIONS (`upsert_embedding()` checks under an instance-local lock without a transaction; reproduced with two connecti… |
| external 3 (SENT) | 2026-09-15 | — | SENT (round-3 package 6bbd7384eb41e75932697fab05e934786053e64aba13371a09d0ce8038d4ab59 @ pin 0fb4a3299b7b62b49f029b3919c0db426321f757, CI 35012023075; 0041 v5; fresh-clone capture at the pin: 3245 passed, 11 skipped, 1 xfailed, 2 warnings in 780.22s (0:13:00)). 0041 v5 — round 2's seven findings fol… |
| external 3 (verdict) | 2026-09-15 | 5 | RETURN for amendment — the atomic publication requirement, the rejection of invalid record-and-notice units and conservative receipt reporting all accepted as improvements. Five findings: F1 REPLACING `Episode.kind` BREAKS OUTCOME-HISTORY PROTECTION — simulated on a real outcome record, the model va… |
| external 4 (SENT) | 2026-09-15 | — | SENT (round-4 package 9d80cd7274a7dd552effb51bc0313d50136ace2801d510f957c1f20791c669fd @ pin ef46d4a4cb80e5c86f672a0f76b162d46eea0d63, CI 35026765939; 0041 v6; fresh-clone capture at the pin: 3260 passed, 11 skipped, 4 xfailed, 2 warnings in 706.81s (0:11:46)). 0041 v6 — round 3's five findings fold… |
| external 4 (verdict) | 2026-09-15 | 4 | RETURN for amendment — the outcome-chain treatment improved, the fixtures now perform full validation, and the ledger-row precedence conflict is RESOLVED. Four findings: (1) the marker decisions the README reports as completed are still missing — §4b labels pre-existing marker values "OWED AND NOT Y… |
| external 5 (SENT) | 2026-09-16 | — | SENT (round-5 package b5746cc2fddaebc241433da5d08675897dcac49fb49c9b2b70369c656f1d9b77 @ pin a3ef39af276b63823d13d721ff47149f356c8ded, CI 35045533574; 0041 v10; fresh-clone capture at the pin: 3272 passed, 11 skipped, 11 xfailed, 2 warnings in 1821.24s (0:30:21)). 0041 v10 — round 4's four findings … |
| external 5 (verdict) | 2026-09-16 | 3 | RETURN for amendment — THE ROUND-4 INV-12 FINDING IS CLOSED (the revised check detects the widening). The attestation rule, advisory migration report, reconstructed receipts and preservation of existing quarantine all accepted. Two contract corrections and one evidence finding: (1) row 49 STILL CHAN… |
| external 6 (SENT) | 2026-09-16 | — | SENT (round-6 package 1b2ff04a8513dae7593c329c786a63d715c5c513ac08f52f15b80b9edf766d9e @ pin ead0bcc93301b42f7e2ae19f684c49bae8e9882e, CI 35066008494; 0041 v11; fresh-clone capture at the pin: 3276 passed, 11 skipped, 11 xfailed, 2 warnings in 678.08s (0:11:18)). 0041 v11 — round 5's two contract fi… |
| external 6 (verdict) | 2026-09-16 | 3 | ACCEPTED WITH AMENDMENTS — "Under your process, this does not yet authorize implementation." THE ARCHITECTURE IS FROZEN around INV-1–INV-12, the carrier treatment map and §4h's transition rules. Round 5's absence-handling finding CLOSED (rows 30/49 preserve absent reasons, preserve registered reason… |
| external 7 (SENT) | 2026-09-16 | — | SENT (round-7 package 1a9767feeff299400e63af8d99fc22e4609cab85195376ac0080b3dbe22d4991 @ pin 6b8d757530865194c5ad4ffc50783994b7eb8f0c, CI 35120067776; 0041 v13; fresh-clone capture at the pin: 3277 passed, 11 skipped, 11 xfailed, 2 warnings in 678.31s (0:11:18)). 0041 v13 — round 6 ACCEPTED WITH AME… |
| external 7 (verdict) | 2026-09-16 | 3 | REMAINS ACCEPTED WITH AMENDMENTS — "Implementation is not yet authorized." The design freeze holds. Amendment 2 CLOSED (altered bytes are actually checked; both always-accept and always-reject controls are detected) and amendment 3 CLOSED (the owner's decision, the four values and the definition of … |
| external 8 (SENT) | 2026-09-16 | — | SENT (round-8 package c59a4c761b8efa86c43c70452bafa5854b28a8c1e9b28f1eab9dd7a861cb694b @ pin b0f9c54fd2e0dfc931a560b7e3cbc4c460cf40bd, CI 35151936119; 0041 v13; fresh-clone capture at the pin: 3277 passed, 11 skipped, 11 xfailed, 2 warnings in 798.12s (0:13:18)). 0041 v13 UNCHANGED — the specificati… |
| external 8 (verdict) | 2026-09-17 | 2 | ACCEPTED. "The remaining amendment is closed. The two amendments closed in round 7 remain closed." All three round-7 corrections verified independently: the ordinary-write test loads its historical record from the frozen fixture and attempts only `ep-new` through the writer; the export contains exac… |
| external 9 (SENT) | 2026-10-01 | — | SENT (round-9 package 9c315ab6f60cc69e76e4f0c83acac6a7e9d0033a6879bec16660e8173430e63d @ pin c05b709b80a6e817b4d45d5a265aa4d24e09594c, CI 36905663405; 0041 v14; fresh-clone capture at the pin: 4722 passed, 12 skipped, 8 warnings in 2202.25s (0:36:42)). The line's first implementation package (round … |
| external 9 (verdict) | 2026-10-02 | 8 | RETURN FOR IMPLEMENTATION CORRECTION — "The design accepted at round 8 remains accepted." The first implementation review: eight findings, four P1 and four P2. 0041-R9-01 an ordinary episode write can restore attested-redacted content; 0041-R9-02 two D1 reason closures and historical source-reason r… |
| external 10 (SENT) | 2026-10-03 | — | SENT (round-10 package d38f5e016113b7b2989b719c8dca2bceb1a7288c97923e7086b8972712f8e13f @ pin de9f9659855069118fcdaa74650e5bbb030c463a, CI 37070746917; 0041 v15; fresh-clone capture at the pin: 4888 passed, 12 skipped, 8 warnings in 2149.99s (0:35:49)). Answers round 9's eight findings; first seal; … |
| external 10 (verdict) | 2026-10-03 | 4 | RETURN FOR IMPLEMENTATION CORRECTION — "Four implementation findings prevent acceptance of this submission." The design accepted at round 8 remains accepted. 0041-R10-01 (P1) a full export carrying a newly redacted outcome cannot apply its notice to a destination holding the earlier outcome; 0041-R1… |
| external 11 (SENT) | 2026-10-04 | — | SENT (round-11 package 0d78617487a5927543fa8dd87c5836cb9339a69b4d95db9fc5a42a04e5fc6149 @ pin 04581ec4c9dc65bf09cfa53a796d48d9ec307fc9, CI 37157423523; 0041 v15.1; fresh-clone capture at the pin: 4989 passed, 12 skipped, 8 warnings in 2310.49s (0:38:30)). Answers round 10's four findings; its first … |
| external 11 (verdict) | 2026-10-04 | 4 | RETURN FOR IMPLEMENTATION CORRECTION — "The four named round-10 reproductions are corrected. Three additional implementation findings prevent acceptance of this submission." 0041-R11-01 (P1) redacting an edge with the quarantine relation emits a notice the importer rejects; 0041-R11-02 (P2) the noth… |
| external 12 (SENT) | 2026-10-04 | — | SENT (round-12 package eb5eba1c722c00686d9141ee40cb07db170a354eb9dbfcde884c9fa9c9ae02a7 @ pin 7fbcd5dc226551d89bbb15dc81e819085a801b38, CI 37226813006; 0041 v15.2; fresh-clone capture at the pin: 5055 passed, 12 skipped, 8 warnings in 2360.35s (0:39:20)). Answers round 11's three findings and N11-01… |
| external 12 (verdict) | 2026-10-05 | 3 | RETURN FOR IMPLEMENTATION CORRECTION — "The three named round-11 defects are corrected on their reproduced paths." 0041-R12-01 (P2) a genuine notice cannot redact a consolidation output the destination already holds: the output identity gate rejects the unit before the notice applies. Nonblocking: 0… |
| external 13 (SENT) | 2026-10-05 | — | SENT (round-13 package 7b2616ddecfc008fa6d0302aebb9c6dec22bebdd6ecdc9203000560fee3d7f98 @ pin 79c9bf182e198b119a9ac7f7c5434a82d64f0cb6, CI 37272901357; 0041 v15.3; fresh-clone capture at the pin: 5147 passed, 12 skipped, 8 warnings in 2419.22s (0:40:19)). Answers R12-01, N12-01 and N12-02, and carri… |
| external 13 (verdict) | 2026-10-05 | 3 | RETURN FOR IMPLEMENTATION CORRECTION — "The named round-12 reproductions now pass." 0041-R13-01 (P2) the collision check matched a notice's raw target against the arriving OR the held id before resolution, so one output's notice authorised another's difference; 0041-R13-02 (P2) the rider's marker co… |
| external 14 (SENT) | 2026-10-06 | — | SENT (round-14 package 99a4985c83758331a3d78a89e2e79e24e46e7c2a6d104a5a3e65b1560ab2f617 @ pin 8a54a87d7b0f22b1e2ca2bcc5359568e4f357823, CI 37392629406; 0041 v15.4; fresh-clone capture at the pin: 5175 passed, 12 skipped, 8 warnings in 2620.92s (0:43:40)). Answers R13-01, R13-02, N13-01 and the 0014 … |
| external 14 (verdict) | 2026-10-06 | 0 | 🏁 ACCEPTED — THE IMPLEMENTATION: "The implementation at this pin closes both round-13 findings and the shared-carrier observation. No new blocking or nonblocking finding is raised." The 0014 §2c rider's implementation accepted on its three conjunctive conditions; INV-1–INV-12, the 64-carrier map and… |

**Per-finding closure ledger — PROCESS §4a.** **57 finding(s) for `0041`** — every number here is DERIVED from the rows below (external round 7, R7-1: the manifest claimed 26 while the ledgers held 31, and 0023 said 9/9 above a 10-row table); the total across the tracked specs is derived once, in `specs/STATUS.md`. Generated from `specs/closure_findings.py` and validated against `specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — extras, duplicates, wrong rounds and empty evidence all fail the build.

| finding | round | what it was | closed in | evidence (runnable) |
|---|---|---|---|---|
| **0041-R1-1** | external 1 | the content-carrier inventory was incomplete: `Edge.original_relation` was classified non-content while ingestion preserves an unrecognised extractor relation there verbatim, and the reviewer confirmed it persists AND exports; two further omitted carriers did the same | the inventory re-derived by a script that WALKS THE MODEL rather than a hand list, with its classification output committed beside it and reproduced byte-for-byte from the tree; v3.1 §2/§2d | `$PY -m pytest tests/test_0041_evidence.py::test_the_carrier_enumeration_reproduces_its_committed_output_byte_for_byte tests/test_0041_evidence.py::test_f1a_an_unrecognised_extractor_relation_is_kept_verbatim_in_original_relation -q -p no:randomly` |
| **0041-R1-2** | external 1 | clearing the wiki inside the redaction transaction does not prevent its later restoration — a compilation that BEGAN before the redaction republishes the original content, stamped with the current store version | §4e: publication is conditional on the store version its inputs were read at, and redaction bumps that version; the delayed-writer treatment defined | `git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §4e — the version-conditional publication rule` |
| **0041-R1-3** | external 1 | redacted state and episode handling were underspecified, and the supporting claim was FALSE: `TEXT NOT NULL` permits the empty string, so it reserves nothing. §4c described only an edge journal event while §4a accepts an episode | §4b defines the marker's representation and validation, §4c gains the durable episode record, and the reader inventory names `edge_state_at()`'s new REDACTED state instead of leaving a sentinel to classify as MALFORMED | `git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §4b/§4c/§6 — representation, the episode record, the reader state` |
| **0041-R1-4** | external 1 | D4 did not explain how affected supersession receipts are LOCATED: `supersession_operations` stores digests and an operation id with no complete reverse mapping to affected records | §4f defines durable associations for future operations and CONSERVATIVE completeness reporting for existing unlinked receipts — the limit is stated as a guarantee (`receipts_complete=False`) rather than claimed away | `git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §4f — durable association and conservative reporting` |
| **0041-R1-5** | external 1 | exporting redaction events needed a complete IMPORT contract: record/event binding, missing or inconsistent notices, repeat imports, user remapping, destination conflicts, and the treatment of source `seq`/`txn` | §4g, the acceptance contract for a transport that does not yet exist — export carries no events at all today, which the spec now states rather than assumes | `git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §4g — the import contract and its failure cases` |
| **0041-R1-6** | external 1 | the scope of dependent content was an open PRODUCT question: §10.1 left consolidated outputs unresolved, so a caller could not know what remained after a successful redaction | THE OWNER'S RULING — outputs are separate; §10.1 and §8 state it, and §11.5 limits the success claim accordingly, naming surviving copies in the receipt | `git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §10.1/§8 — the owner's ruling, outputs are separate` |
| **0041-R1-7** | external 1 | the owner's four decisions had not reached the operative contract consistently — four live passages still contradicted them (D1 against §2c's length-capped prose; D2 against INV-6 and §10; §2's three duplicated columns against INV-2; 'no row is deleted' against deleting wiki, embedding and ledger rows) | §11, one consolidated current contract that GOVERNS where anything above it conflicts, with the historical discussion moved out | `git show 6831bcf3e22521fff9f5fbb95a87f826bca68380 # v3.1 §11 — the operative contract and its precedence rule` |
| **0041-R2-1** | external 2 | the semantic-rebuild exemption did not hold ACROSS DATABASE CONNECTIONS: `upsert_embedding()` read and checked the live edge under an instance-local lock with no transaction, so a second connection's redaction was overwritten. Separately the INV-12 test still passed when `embedded_text()` was widened onto an optional field its fixture left UNSET | §4e requires validation and publication to be atomic against other CONNECTIONS, and the exemption is withdrawn; the INV-12 fixture populates every string leaf and each optional leaf carries a control proving a widening onto it is caught | `$PY -m pytest tests/test_0041_evidence.py::test_two_connection_publication_the_embedding_upsert_refuses_a_vector_for_content_another_connection_replaced tests/test_0041_evidence.py::test_inv12_each_optional_leaf_is_load_bearing_a_widening_onto_it_is_missed_when_it_is_unset -q -p no:randomly` |
| **0041-R2-2** | external 2 | the tombstone was not reserved by the stated mechanism — the marker survives `sanitize_llm_body()`, ordinary ingestion and storage, so the claim that a leading NUL makes it unproducible was false; nested replacement shapes were undefined and broke an existing uniqueness validator | §4b: the marker is NOT reserved by a column constraint, reservation is INV-11's mirror at the write and import boundaries, and the nested shapes carry valid post-redaction representations | `git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §4b — reservation as a rule, not a claim about a column` |
| **0041-R2-3** | external 2 | the five-value reason vocabulary conflicted with existing lifecycle behaviour: all seven of the store's disposition reasons were excluded, so enforcing it would reject normal writes, and calling them `legacy_freeform` would discard distinctions historical classification and cache handling use | §11.2 scopes permitted reasons BY OPERATION and preserves existing lifecycle meanings, separating migration-time retention from redaction-time removal | `git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §11.2 — reasons per operation` |
| **0041-R2-4** | external 2 | import failure row 9 rejected an event with an invalid reason but imported its record UN-REDACTED — the content arrived without the instruction to remove it | §4g rules the dependent record-and-notice unit as ONE: it is rejected together or the import fails explicitly; the adjacent cases (notice-less tombstone, inconsistent notices, the idempotency key's `event_id`) are completed | `git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §4g — the record and its notice commit together` |
| **0041-R2-5** | external 2 | receipt selection was incomplete for CURRENT-format operations too: a reproduced `prior_upserts` update left no contribution or refusal row linking the target to the operation, and step 2 could not locate an id in the current `response` | the exact-coverage claim is WITHDRAWN; §4f reports completeness conservatively and the receipt no longer copies a removed content digest into itself | `git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §4f — the withdrawn coverage claim` |
| **0041-R2-6** | external 2 | the expanded inventory still lacked a complete treatment map — 64 candidates discovered, none of them told what happens to it; a prose `outcome_counts` KEY was confirmed to persist and export, and §2 and the example disagreed about `provenance.evidence_ref` | §2d-iii-bis, the 64-row per-candidate map built by both seats: replace, clear, delete, preserve or explicitly exclude, each with its resulting shape | `git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §2d-iii-bis — the 64-row treatment map` |
| **0041-R2-7** | external 2 | §11 did not provide a consistent invariant contract: it re-pointed EXISTING identities (INV-1 from structure preservation to content absence, INV-3 from `why` behaviour to atomicity), dropped INV-4 and INV-5, and described all 64 candidates as the removal surface while §2d said they are not all targets | §11.3 restores §6's meanings, new properties take NEW identifiers, and the matrix is one complete current table with its checks | `git show 0fb4a3299b7b62b49f029b3919c0db426321f757 # v5 §11.3 — stable invariant identities` |
| **0041-R3-1** | external 3 | replacing `Episode.kind` broke outcome-history protection: simulated on a real outcome record the model still VALIDATED, but the chain head disappeared, the next append restarted at sequence 1, and targeted deletion of the original was no longer refused — five guards read that discriminator | row 46 becomes two branches — PRESERVE a recognised operational kind, REPLACE prose — with the recognised set closed by a refusal rather than by convention | `$PY -m pytest tests/test_0041_treatment_matrix.py::test_row46_the_two_branch_kind_treatment_keeps_the_outcome_chain_and_its_guards tests/test_0041_treatment_matrix.py::test_row46_the_replace_branch_applies_to_prose_only -q -p no:randomly` |
| **0041-R3-2** | external 3 | marker, migration and absence handling were still incomplete: §4b left pre-existing marker values 'not yet ruled', §4b and §4g contradicted each other over a notice-less tombstone, and `None`, a legitimate empty value, ordinary text and a redacted value were not distinguished | §2d-v's absence rules — None stays None, empty stays empty — and §4b's ruling on pre-existing markers as unattested rather than forbidden | `git show ef46d4a4cb80e5c86f672a0f76b162d46eea0d63 # v6 §2d-v/§4b — the absence rules and the migration ruling` |
| **0041-R3-3** | external 3 | the corrected reason contract named the WRONG existing vocabulary: a twelve-value list against the journal writer's seven-value `DISPOSITIONED_REASONS`, omitting `disputed`, `revoked_source` and others | §11.2 REFERENCES `schema.DISPOSITIONED_REASONS` instead of re-typing it — a list copied into prose is a list that drifts — and defines the other reason-writing operations separately, splitting retain-at-migration from remove-at-redaction | `git show ef46d4a4cb80e5c86f672a0f76b162d46eea0d63 # v6 §11.2 — the registry referenced, not retyped` |
| **0041-R3-4** | external 3 | the supposedly authoritative sections still disagreed about treatment: rows 21 and 23 retained contribution-ledger rows and cleared their digests while §11.1 said deletion governs, and the example receipt cleared a field the map preserves | one current contract with EXPLICIT PRECEDENCE — §11 governs on contract, §2d-iii-bis on per-carrier treatment — and the example corrected to the map | `git show ef46d4a4cb80e5c86f672a0f76b162d46eea0d63 # v6 §11.1/§2d-iii-bis — precedence stated` |
| **0041-R3-5** | external 3 | the evidence OVERSTATED its validation and field coverage: fixtures labelled VALID used `model_copy(update=...)`, which skips validation of the updates, and the revised INV-12 fixture still passed a widening onto an unset `invalidation_reason` | every fixture is validated through the applicable model AND the operation's own checks, with the two refusals printed as results; INV-12 is generated from the model's field walk with a per-leaf control | `$PY -m pytest tests/test_0041_evidence.py::test_the_before_after_fixtures_validate_as_the_treatment_map_rules_them tests/test_0041_evidence.py::test_inv12_catches_a_widened_embedder_the_packaged_fixture_missed -q -p no:randomly` |
| **0041-R4-1** | external 4 | the marker decisions the README reported as completed were still missing: §4b labelled pre-existing marker values 'OWED AND NOT YET RULED' and legitimate empty values 'still owed', §4g accepted a marker-only record without a notice while §4b prohibited marker introduction, and repeat handling promised an original receipt a record may never have had | v9's ATTESTATION RULE, which answers all four at once: a field is redacted iff a redaction record names that record and that field — so a pre-existing marker is an unattested marker, writable and reported, and a repeat returns the original OR a reconstructed receipt | `git show 7db9987b980505d8a7f57bbdf05499f41c690c31 # v9 §4b — the attestation rule` |
| **0041-R4-2** | external 4 | the new restrictions did not settle compatibility with records ALREADY STORED: a stored relation-only quarantine loses its quarantine under the treatment map, and existing prose-valued kinds had no transition policy | §4h's re-establish-or-refuse rule, and an EXECUTABLE transition table over records written before the restrictions — the write-path refusal and the transition rule are two halves of one property | `$PY -m pytest tests/test_0041_transition_table.py::test_A_existing_relation_only_quarantine_keeps_its_quarantine_under_the_ruled_treatment tests/test_0041_transition_table.py::test_A_control_the_naive_treatment_promotes_the_claim -q -p no:randomly` |
| **0041-R4-3** | external 4 | §11.2 still described the reason fields incorrectly: the journal already enforces `DISPOSITIONED_REASONS` for invalidation events, so its closure is not 'nothing today', and `revoked_source` does not define the vocabulary of `source_revocations.reason` — the revocation row retained the caller's sentence | §11.2 states the allowed values and enforcement PER D1 REASON FIELD, including `source_revocations.reason` and `Episode.retired_reason`, and extends the existing journal rule to redaction events | `git show 7db9987b980505d8a7f57bbdf05499f41c690c31 # v9 §11.2 — per-field reason contract` |
| **0041-R4-4** | external 4 | INV-12 still missed DICTIONARY KEYS: `_inv12_sets` changed values and not keys, so with `embedded_text` widened onto `outcome_counts` keys all seven fixture/control cases passed although the embedding text changed and the content digest did not | the generator mutates keys as well as values and asserts directly against the production projections, keeping the optional-field controls | `$PY -m pytest tests/test_0041_evidence.py::test_inv12_catches_a_widened_embedder_onto_dictionary_keys tests/test_0041_evidence.py::test_inv12_the_embedder_sees_no_field_the_content_digest_does_not_cover -q -p no:randomly` |
| **0041-R5-1** | external 5 | row 49 still changed an ACTIVE episode's disposition: preserve-registered, else `"redacted"`, never NULL turned `retired_reason=None, active=True` into `"redacted", active=False` — a redaction RETIRING an active episode, which §4h forbids and which the previous round's own fix introduced | §4h's corollary — REDACTION ACTS ON CONTENT; ABSENCE IS NOT CONTENT — so every carrier rule is three cases: absent stays absent, registered stays registered, only prose becomes the registry value | `$PY -m pytest tests/test_0041_transition_table.py::test_rows30_49_on_a_frozen_record_absence_survives_and_prose_does_not tests/test_0041_treatment_matrix.py::test_rows30_49_absence_stays_absence_a_none_reason_is_not_replaced -q -p no:randomly` |
| **0041-R5-2** | external 5 | the source-revocation rule changed D1 without recording a replacement decision: D1 puts `source_revocations.reason` under a closed vocabulary and §11.2 treated it as continuing free text. Removing historical prose does not constrain what future writes may store — two separate questions | §11.2 separates the restriction on FUTURE writes from the treatment of historical prose, and the field closes for future writes without amending D1 | `git show ead0bcc93301b42f7e2ae19f684c49bae8e9882e # v11 §11.2 — future writes and historical prose separated` |
| **0041-R5-3** | external 5 | three strict xfails did not exercise the behaviour their names promised — the repeated-call test passed against a no-op `Memory.redact`, the migration-report test against a helper that always returned `[]`, and the after-attestation test never called redaction at all. Existence checks wearing behaviour names | the three rewritten to bind VALUES the product computes, the class exhausted by our own mutant campaign, and POSITIVE CONTROLS added — the after-attestation test could never have been made green by any implementation, which no negative control can reveal | `$PY specs/evidence/0041/xfail_mutant_campaign.py` |
| **0041-R6-1** | external 6 | several transition tests still created their historical records through ORDINARY WRITERS, so three of them fail at SETUP once the proposed restrictions land; the fixture lacked a historical source-revocation row with a prose reason, and the row-46 test still expected the `Episode` CONSTRUCTOR to reject a prose kind, contradicting §4h's requirement that existing records stay readable | a FROZEN pre-restriction store, written before the closure and checked against its manifest, which the transition tests copy instead of writing rows a landed closure would refuse; the refusal moved from the constructor to the write path | `$PY -m pytest tests/test_0041_transition_table.py::test_the_frozen_store_carries_every_pre_restriction_shape_the_table_needs tests/test_0041_transition_table.py::test_B_existing_prose_kind_is_retained_at_migration_and_readable -q -p no:randomly` |
| **0041-R6-2** | external 6 | the fixture-checker's test invoked the checker only on the ORIGINAL bytes and compared sha256 digests for the altered copy — a property of sha256, not of the checker. Replacing the subprocess result with unconditional success left the test passing: an unfailable check guarding the artifact whose whole value is that it has not changed | the checker is RUN on the altered bytes in a throwaway copy of its own directory, and the rejection is read from ITS exit code and ITS message; the README's both-directions claim corrected | `$PY -m pytest tests/test_0041_transition_table.py::test_the_frozen_pre_restriction_store_matches_its_manifest -q -p no:randomly` |
| **0041-R6-3** | external 6 | the source-revocation vocabulary was still marked PROPOSED — `policy`, `subject_request`, `erroneous_capture` and `legal_obligation` — with older summaries still implying the field stays permanently free text | THE OWNER'S RULING, folded as authorised rather than proposed: the four values are final, `policy` is defined, and the superseded summaries are DATED as historical rather than erased | `git show e0cba0aac04ff48adc8a28befc96648a65e47a60 # v12 §11.2 — the vocabulary authorised, not proposed` |
| **0041-R7-1** | external 7 | historical-data setup still used restricted writers: the prose-kind test wrote `ep-old` through the ordinary writer and would fail at setup under the proposed restriction, never reaching its assertion; the source-reason test created a new prose reason; and the frozen revocation had no linked record for the test's affected-records assertion | both tests read frozen records, and the fixture gains a source-linked edge so the affected-records assertion has something to be about | `$PY -m pytest tests/test_0041_transition_table.py::test_B_an_ordinary_write_of_a_new_prose_kind_is_refused_while_the_stored_one_stays tests/test_0041_transition_table.py::test_D_a_source_revocation_reason_holding_the_callers_sentence_is_replaced -q -p no:randomly` |
| **0041-R7-2** | external 7 | the revised import test could pass FOR THE WRONG REASON: it exported the entire mixed fixture including marker-bearing rows, so an import rule that rejected markers and performed no kind validation at all made it pass | the prose-kind case is exported in ISOLATION, so no other restriction can satisfy its expected rejection — and a control asserts the isolated export carries no marker to reject | `$PY -m pytest tests/test_0041_transition_table.py::test_B_an_import_carrying_a_prose_kind_is_refused tests/test_0041_transition_table.py::test_the_isolation_control_detects_a_marker_bearing_export -q -p no:randomly` |
| **0041-R7-3** | external 7 | the redaction adapter disagreed with §4a: it passed `kind`, `target_id` and `fields` where §4a specifies a user, an edge-OR-episode target and a reason, so a callable with the documented signature failed the repeat test immediately | the adapter takes `user_id`, exactly one of `edge_id | episode_id` — asserted, never both and never neither — and `reason`, matching §4a | `$PY -m pytest tests/test_0041_transition_table.py::test_F_a_repeated_call_returns_the_original_or_a_reconstructed_receipt -q -p no:randomly` |
| **0041-R8-1** | external 8 | NONBLOCKING FOLLOW-UP. The isolation control searched the export's RAW TEXT for a marker whose NUL bytes JSON escapes to `\u0000`, so the assertion was true of every JSON export ever written — a file full of markers passed it. The campaign's import mutant had the same defect, so it simulated a rule that does nothing | the check DECODES and walks every string value and dictionary key, returns the list so a failure names what it found, and reads record lines only because the export's metadata header carries a kind of its own; demonstrated rather than claimed, on a marker-bearing export | `$PY -m pytest tests/test_0041_transition_table.py::test_the_isolation_control_detects_a_marker_bearing_export -q -p no:randomly` |
| **0041-R8-2** | external 8 | NONBLOCKING FOLLOW-UP. §11.4-bis's evidence references were stale in five figures: ten campaign cases where the file holds 14, a nine-shape fixture where the manifest holds 10, and a superseded digest and creation pin | the five figures corrected AND bound — a test DERIVES each one from the artifact it describes (the campaign's `check()` calls by AST, the manifest's rows, the store's sha256, the recorded HEAD) and fails if the section disagrees, so the class cannot recur silently | `$PY -m pytest tests/test_0041_evidence.py::test_the_11_4_bis_evidence_figures_are_derived_from_the_artifacts_they_cite -q -p no:randomly` |
| **0041-R9-01** | external 9 | an ordinary episode write could restore attested-redacted content: the attestation and reservation checks ran outside the writer's own transaction | round 10 (6f419ff): the attestation and reservation checks run inside add_episode's own BEGIN IMMEDIATE | `$PY -m pytest tests/test_0041_round10_txn.py::test_R9_01_blocked_the_redaction_waits_for_the_write_then_treats_what_it_wrote tests/test_0041_round10_txn.py::test_R9_01_sequential_a_redaction_committed_before_the_write_begins_is_seen_and_refuses tests/test_0041_round10_txn.py::test_R9_01_control_ordinary_episode_writes_still_work -q -p no:randomly` |
| **0041-R9-02** | external 9 | two D1 reason closures were absent (revoke_source and Episode.retired_reason accepted prose; the sweep added Edge.invalidation_reason), and historical source-revocation reason prose survived a real redaction | round 10 (19066f4, 90bbe5c, eabd89d): the owner's revocation and lift reason lists checked in preview and commit; a present retired or invalidation reason must be registered; redact treats source_revocations.reason through the one admitted updater (a 0022 amendment); the named tests invoke the operation they test | `$PY -m pytest tests/test_0041_round10_reasons.py::test_a_revoke_with_prose_refuses_in_preview_and_in_commit_and_writes_nothing tests/test_0041_round10_reasons.py::test_a_a_lift_outside_the_lift_list_refuses_in_preview_and_commit_and_writes_nothing tests/test_0041_round10_reasons.py::test_a_revoked_in_error_is_a_lift_reason_and_not_a_revoke_reason tests/test_0041_round10_reasons.py::test_b_a_present_retired_reason_must_be_registered_none_stays_valid tests/test_0041_round10_reasons.py::test_the_closure_binds_the_import_boundary tests/test_0041_round10_reasons.py::test_c_the_re_upsert_to_invalidated_with_prose_refuses_and_the_stored_row_is_unchanged tests/test_0041_round10_reasons.py::test_d_the_frozen_stores_prose_revocation_is_treated_by_the_real_redaction tests/test_0041_transition_table.py::test_D_a_source_revocation_reason_holding_the_callers_sentence_is_replaced tests/test_0041_round10_reasons.py::test_a_revoke_with_each_of_the_owners_four_reasons_commits tests/test_0041_round10_reasons.py::test_a_a_lift_with_each_lift_reason_commits tests/test_0041_round10_reasons.py::test_stored_legacy_prose_still_loads_the_closure_never_binds_the_read_path tests/test_0041_round10_reasons.py::test_c_every_registered_reason_is_accepted_the_closure_is_the_registry_not_a_list tests/test_0041_round10_reasons.py::test_d_the_standing_state_is_identical_before_and_after_the_treatment_across_revoke_lift_revoke -q -p no:randomly` |
| **0041-R9-03** | external 9 | the contribution-ledger treatment omitted episodes and matched ids without their target kind | round 10 (ba6f88f): the ledger digests cleared in both target branches, joined by user, kind and id, in both absorption directions | `$PY -m pytest tests/test_0041_round10_matrix.py::test_the_real_redaction_treats_the_carrier_as_the_map_rules tests/test_0041_round10_matrix.py::test_the_mirror_redacting_an_edge_leaves_a_same_id_episode_ledger_intact -q -p no:randomly` |
| **0041-R9-04** | external 9 | durable notice deduplication lost the destination scope and the body's integrity: a repeat with a different body was accepted as existing | round 10 (81c68d4, 6af44ee): notice_id binds origin, source user, source event, destination user and typed target; the canonical foreign body is persisted and compared on every repeat, across remaps; a contradiction refuses the whole import | `$PY -m pytest tests/test_0041_round10_notices.py::test_R9_04_one_notice_imported_for_two_destination_users_attests_each_users_own_record tests/test_0041_round10_notices.py::test_R9_04_a_later_contradictory_body_under_the_same_identity_refuses_atomically tests/test_0041_round10_notices.py::test_S2_1_a_remapping_import_with_a_contradictory_body_is_refused_atomically tests/test_0041_round10_notices.py::test_S2_1_the_same_contradiction_across_two_destination_users_is_refused tests/test_0041_round10_notices.py::test_R9_04_an_honest_repeat_is_idempotent_and_writes_nothing tests/test_0041_round10_notices.py::test_S2_1_control_remapping_twice_with_an_equal_body_is_not_refused -q -p no:randomly` |
| **0041-R9-05** | external 9 | witnessed receipts and relayed notices did not retain the source's provenance: the destination's application facts overwrote the source's | round 10 (81c68d4): the two-fact receipt — the source's reason, times, versions and event reference, None where the notice does not carry them, beside this store's applied_* facts; a re-export passes the source body on unchanged | `$PY -m pytest tests/test_0041_round10_notices.py::test_R9_05_a_witnessed_receipt_reports_the_sources_facts_and_this_stores_application_beside_them tests/test_0041_round10_notices.py::test_R9_05_the_original_and_its_honest_relay_are_one_notice_together_or_in_sequence tests/test_0041_round10_notices.py::test_R9_05_facts_the_notice_does_not_carry_are_None_and_serialise_as_null tests/test_0041_round10_notices.py::test_R9_05_a_relay_that_alters_the_body_is_refused -q -p no:randomly` |
| **0041-R9-06** | external 9 | an attested marker-valued episode kind could not round-trip through export and import | round 10 (81c68d4): the kind closure admits the marker when the same import unit attests kind, including by a standing notice; raw prose and unaccounted markers still refused | `$PY -m pytest tests/test_0041_round10_notices.py::test_R9_06_the_treated_historical_prose_kind_episode_round_trips_with_its_notice tests/test_0041_round10_notices.py::test_R9_06_a_standing_notice_admits_the_marker_kind_when_the_record_arrives_later tests/test_0041_round10_notices.py::test_R9_06_the_closure_still_refuses_what_no_attestation_accounts_for -q -p no:randomly` |
| **0041-R9-07** | external 9 | semantic backfill recreated embeddings for attested-redacted edges | round 10 (aa7472f): backfill excludes redacted targets at its read, and the upsert's digest guard refuses a vector for content replaced during the embed call | `$PY -m pytest tests/test_0041_round10_readers.py::test_R9_07_an_attested_edge_is_skipped_and_its_tombstone_never_reaches_the_embedder tests/test_0041_round10_readers.py::test_R9_07_a_redaction_during_the_embed_call_is_refused_by_the_digest_guard_at_the_upsert tests/test_0041_round10_readers.py::test_R9_07_an_unattested_marker_row_follows_its_own_contract_and_is_embedded -q -p no:randomly` |
| **0041-R9-08** | external 9 | a notice's field names admitted arbitrary prose rather than the kind's carrier paths | round 10 (81c68d4): the field domain is the declared kind's carrier paths, derived from the treatment tables, checked at the parser and at the commit primitive | `$PY -m pytest tests/test_0041_round10_notices.py::test_R9_08_notice_field_names_are_the_kinds_carrier_paths tests/test_0041_round10_notices.py::test_R9_08_the_commit_primitive_refuses_prose_field_names_on_its_own tests/test_0041_round10_notices.py::test_R9_08_the_allowed_set_is_derived_from_the_treatment_tables -q -p no:randomly` |
| **0041-R10-01** | external 10 | a full export carrying a newly redacted outcome could not apply its notice to a destination holding the earlier outcome | round 11 (9f37287): one held-differs rule for edges, episodes and outcome links (portability.held_differs_verdict); an outcome's structural difference refuses, notice or not | `$PY -m pytest tests/test_0041_round11_outcome.py::test_R10_01_full_export_applies_notice_to_held_outcome tests/test_0041_round11_outcome.py::test_A2_an_already_treated_held_outcome_meeting_its_old_record_ends_existing_with_no_new_event tests/test_0041_round11_outcome.py::test_outcome_and_interaction_give_the_same_result_for_the_same_difference tests/test_0041_round11_outcome.py::test_the_treated_held_outcome_keeps_its_chain tests/test_0041_round11_outcome.py::test_control_a_changed_outcome_with_no_notice_still_refuses tests/test_0041_round11_outcome.py::test_control_a_topology_conflict_refuses_notice_or_not -q -p no:randomly` |
| **0041-R10-02** | external 10 | after a treated interaction episode was deleted, import could restore its content and skip treatment because its notice was already applied | round 11 (d812059): treat on arrival — a record arriving under a completed attestation with its notice is written as the pure treatment, no new event or attestation; without a notice it refuses | `$PY -m pytest tests/test_0041_round11_arrival.py::test_R10_02_public_import_cannot_repopulate_a_deleted_attested_episode tests/test_0041_round11_arrival.py::test_a_backup_taken_after_the_redaction_restores_after_a_delete tests/test_0041_round11_arrival.py::test_an_honest_full_backup_of_several_redacted_episodes_restores_after_one_is_deleted tests/test_0041_round11_arrival.py::test_an_arrival_needing_treatment_in_a_carrier_the_attestation_never_named_is_refused tests/test_0041_round11_arrival.py::test_control_re_arrival_without_a_notice_still_refuses tests/test_0041_round11_arrival.py::test_control_an_ordinary_write_of_the_deleted_attested_episode_is_refused tests/test_0041_round11_arrival.py::test_notice_only_after_the_delete_inserts_nothing -q -p no:randomly` |
| **0041-R10-03** | external 10 | the notice identity was not injective over the admitted identifier domain: control characters in source identifiers broke identity separation, relay provenance and the body comparison | round 11 (9b0d0a4): the source identity is three structured columns compared exactly; the row id is a length-framed sha256 over the six components; an empty or non-string component refused at both boundaries | `$PY -m pytest tests/test_0041_round11_identity.py::test_R10_03_a_two_source_triples_that_encoded_equal_are_two_standing_notices tests/test_0041_round11_identity.py::test_R10_03_b_a_relay_preserves_the_native_source_triple tests/test_0041_round11_identity.py::test_R10_03_c_a_changed_body_under_the_same_source_identity_refuses tests/test_0041_round11_identity.py::test_R10_03_c_the_comparison_crosses_a_destination_remap_for_a_NUL_identity tests/test_0041_round11_identity.py::test_the_row_id_is_injective_over_each_component tests/test_0041_round11_identity.py::test_control_an_equal_body_remapped_twice_is_not_a_contradiction -q -p no:randomly` |
| **0041-R10-04** | external 10 | a successful public redaction with the reason imported_notice produced an export the importer rejected: the reason text decided provenance | round 11 (132193b): provenance is a record fact; on the owner's ruling Memory.redact refuses imported_notice and a notice's own reason must be an originating one | `$PY -m pytest tests/test_0041_round11_provenance.py::test_R10_04_memory_redact_refuses_imported_notice_before_any_write tests/test_0041_round11_provenance.py::test_R10_04_a_LOCAL_row_holding_the_witness_label_still_reads_local tests/test_0041_round11_provenance.py::test_R10_04_a_notice_whose_own_reason_is_the_witness_label_is_refused tests/test_0041_round11_provenance.py::test_R10_04_every_admitted_local_reason_round_trips tests/test_0041_round11_provenance.py::test_control_a_genuine_imported_notice_keeps_the_sources_facts -q -p no:randomly` |
| **0041-R11-01** | external 11 | redacting an edge with the quarantine relation emitted a notice the importer rejected, so a destination holding the earlier edge kept its content | round 12 (1b8d875): one domain for a notice's fields, read by the writer, the parser and the commit primitive — the kind's carrier paths plus a closed, named set of bookkeeping paths | `$PY -m pytest tests/test_0041_round12_quarantine.py::test_R11_01_quarantine_redaction_export_applies_to_held_target tests/test_0041_round12_quarantine.py::test_a_destination_holding_the_relation_only_shape_moves_and_attests_its_own_disclosure tests/test_0041_round12_quarantine.py::test_the_notice_domain_stays_closed -q -p no:randomly` |
| **0041-R11-02** | external 11 | the nothing-to-redact check refused an empty live edge whose journal and confirmation row still held carriers requiring treatment | round 12 (7fae0f8): the nothing-to-redact decision moved to the end of the treatment, over the record, its side tables, its journal and the linked revocation prose, inside the caller's transaction | `$PY -m pytest tests/test_0041_round12_surface.py::test_R11_02_empty_live_record_with_retained_carriers_can_be_redacted tests/test_0041_round12_surface.py::test_R11_02_the_confirmation_digest_of_an_emptied_edge_is_treated tests/test_0041_round12_surface.py::test_the_ledger_digests_of_an_emptied_survivor_are_treated tests/test_0041_round12_surface.py::test_a_history_only_redaction_exports_a_notice_another_store_applies tests/test_0041_round12_surface.py::test_a_record_with_nothing_anywhere_is_still_refused_with_nothing_written tests/test_0041_round12_surface.py::test_control_a_populated_edge_treats_its_journal_and_its_digest tests/test_0041_round12_surface.py::test_a_notice_WITHOUT_the_journal_path_still_treats_the_destinations_journal -q -p no:randomly` |
| **0041-R11-03** | external 11 | the source-body comparison omitted redactions originated by the destination itself, so a contradictory notice was accepted | round 12 (bbd71d1): one canonical source projection for every redaction row, witnessed or native, used by both the export and the body comparison | `$PY -m pytest tests/test_0041_round12_native.py::test_R11_03_contradiction_with_native_source_event_refuses_atomically tests/test_0041_round12_native.py::test_the_stores_own_event_relayed_back_honestly_is_existing_not_a_second_row tests/test_0041_round12_native.py::test_two_native_events_of_one_user_are_compared_each_against_its_own tests/test_0041_round12_native.py::test_the_export_and_the_comparison_share_one_projection tests/test_0041_round12_native.py::test_control_the_stores_own_export_re_imported_is_existing tests/test_0041_round12_native.py::test_control_a_witnessed_contradiction_still_refuses tests/test_0041_round12_native.py::test_a_self_import_under_a_remap_attests_the_copy_as_a_witnessed_row tests/test_0041_round12_native.py::test_a_foreign_origin_never_compares_against_a_native_row -q -p no:randomly` |
| **0041-N11-01** | external 11 | NONBLOCKING wording correction: v15.1 §4g's held-differs parenthesis stated a narrower predicate (the difference lies in the notice's fields) than the rule ruled at round 10 and built | v15.2 (7fbcd5d): the parenthesis aligned to the rule as ruled and built — a valid notice for the held record treats it as named, keeps its other fields and flags the arrival; a structural outcome difference refuses, notice or not; credited by the round-12 verdict | `$PY -m pytest tests/test_0041_import_contract.py::test_a_held_different_version_is_redacted_anyway_and_flagged tests/test_0041_round11_outcome.py::test_R10_01_full_export_applies_notice_to_held_outcome tests/test_0041_round11_outcome.py::test_the_treated_held_outcome_keeps_its_chain tests/test_0041_round11_outcome.py::test_control_a_changed_outcome_with_no_notice_still_refuses tests/test_0041_round11_outcome.py::test_control_a_topology_conflict_refuses_notice_or_not -q -p no:randomly` |
| **0041-R12-01** | external 12 | a genuine notice could not redact a consolidation output the destination already held: the output identity gate rejected the unit before the notice applied | round 13 (e4c1573): the owner-approved 0014 §2c rider admits exactly one difference on a colliding indexed output, a redaction of the held output; the arrival is discarded, the notice binds to the held id and the notice step treats it; the arrival is flagged | `$PY -m pytest tests/test_0041_round13_outputs.py::test_R12_01_indexed_output_redaction_reaches_held_output tests/test_0041_round13_outputs.py::test_the_held_output_keeps_every_field_the_notice_does_not_name tests/test_0014_portability.py::test_rider_a_named_field_at_the_marker_WITH_the_notice_resolves_and_treats_the_held_output tests/test_0014_portability.py::test_rider_a_treated_held_output_meeting_its_untreated_arrival_with_the_notice_is_existing tests/test_0014_portability.py::test_rider_the_same_difference_WITHOUT_the_notice_rejects tests/test_0014_portability.py::test_rider_a_field_the_notice_does_NOT_name_rejects tests/test_0014_portability.py::test_rider_a_named_field_at_a_NON_marker_value_rejects tests/test_0014_portability.py::test_rider_a_lineage_difference_rejects_notice_or_not tests/test_0041_round13_outputs.py::test_control_the_unchanged_first_export_still_reimports_idempotently tests/test_0041_round13_outputs.py::test_control_the_redacted_export_without_its_notice_still_refuses -q -p no:randomly` |
| **0041-N12-01** | external 12 | NONBLOCKING: a repeated remapped import bound the notice to an output id the collision check had discarded | round 13 (e4c1573): every notice for an arrival the collision check resolves is rebound to the held output's id before the commit, so the repeat ends existing | `$PY -m pytest tests/test_0041_round13_outputs.py::test_N12_01_a_repeated_remapped_import_binds_the_notice_to_the_existing_copy tests/test_0041_round13_outputs.py::test_every_redaction_row_names_a_record_after_held_earlier_and_repeat tests/test_0041_round13_outputs.py::test_a_contradictory_body_on_the_rebound_notice_still_refuses_whole_import -q -p no:randomly` |
| **0041-N12-02** | external 12 | NONBLOCKING: an empty episode linked to an already-marked shared revocation row received an inaccurate nothing-to-redact refusal | round 13 (0333ad1): revocation.revocation_reason_marked, a read, lets a shared revocation row already at the marker enter this record's attestation union | `$PY -m pytest tests/test_0041_round13_side.py::test_N12_02_an_empty_episode_of_a_source_whose_revocation_row_is_marked_is_redacted tests/test_0041_round13_side.py::test_control_an_empty_episode_with_no_linked_source_is_still_nothing_to_redact tests/test_0041_round13_side.py::test_control_the_record_that_changes_the_revocation_row_attests_it -q -p no:randomly` |
| **0041-R13-01** | external 13 | the collision check matched a notice's raw target against the arriving OR the held id before resolution, so with ids permuted one output's notice authorised another output's difference | round 14 (b24f5ae; controls strengthened in 8a54a87): every arrival resolved before any notice is read for a collision; a raw id names one subject; a notice authorises the exception only for its own resolved subject; an ordinary arrival reusing a held id does not lend its notice | `$PY -m pytest tests/test_0041_round14_resolution.py::test_R13_01_permuted_ids_with_ONE_notice_refuse_the_whole_import tests/test_0041_round14_resolution.py::test_R13_01_an_ordinary_arrival_reusing_a_held_id_does_not_lend_its_notice tests/test_0041_round14_resolution.py::test_control_permuted_ids_with_BOTH_notices_treat_both_held_outputs tests/test_0041_round14_resolution.py::test_control_a_notice_naming_a_held_target_with_no_arrival_applies_to_it tests/test_0041_round14_resolution.py::test_control_a_repeated_user_remap_binds_both_notices_to_the_surviving_copies tests/test_0041_round13_outputs.py::test_a_contradictory_body_on_the_rebound_notice_still_refuses_whole_import tests/test_0041_round13_outputs.py::test_N12_01_a_repeated_remapped_import_binds_the_notice_to_the_existing_copy -q -p no:randomly` |
| **0041-R13-02** | external 13 | the 0014 §2c rider's marker condition was a substring test, admitting a value that merely contained the marker | round 14 (2662970; controls strengthened in 8a54a87): held_output_redaction compares each differing field exactly, held or incoming == MARKER; the substring helpers keep their reservation and diagnostic jobs | `$PY -m pytest tests/test_0041_round14_marker.py::test_R13_02_a_value_that_merely_CONTAINS_the_marker_refuses_whole_import tests/test_0041_round14_marker.py::test_control_the_exact_marker_with_the_notices_is_admitted_and_treats_both tests/test_0041_round14_marker.py::test_control_ordinary_text_in_a_named_field_refuses tests/test_0014_portability.py::test_rider_a_field_the_notice_does_NOT_name_rejects tests/test_0041_round13_outputs.py::test_control_the_unchanged_first_export_still_reimports_idempotently -q -p no:randomly` |
| **0041-N13-01** | external 13 | NONBLOCKING: a supersession-refusal row shared by two edges was omitted from the second edge's redaction receipt | round 14 (a24a47d): a supersession-refusal row linked to the edge at either end and already at the marker is attested; the one update unchanged | `$PY -m pytest tests/test_0041_round14_shared.py::test_N13_01_the_second_edge_attests_the_shared_row_already_at_the_marker tests/test_0041_round14_shared.py::test_control_a_never_treated_shared_row_is_treated_and_attested_by_this_call tests/test_0041_round14_shared.py::test_control_an_edge_with_no_refusal_row_does_not_name_the_path -q -p no:randomly` |
| **0041-PA1** | internal 0 | An imported redaction notice bound to its target by id alone: an untrusted file carrying only a notice redacted the user's own held fact, left a standing notice that refused the user's own later write and hid the id, and redacted a later arrival; the store's own export then paired a hostile notice with the user's unredacted fact | 98327c2: on the default path a notice applies only to a record the import inserts; in both modes only where a record shows the redaction (redaction.shows_redaction): the file's copy, or, on a restore with no copy, the held record (attest only); a file carrying a notice's record unredacted refuses whole wherever that record would be admitted under it (store.import.notice-record-unredacted), unless this store already holds that notice as applied; a standing notice refuses no local write and is not in redacted_targets(), completing only on an inserted record that shows it and, on the default path, of its own origin (store.import.standing-notice-origin-mismatch); the result names notices_not_applied. SUPERSEDED at T4 (2026-10-14; 0041 v16 §11.6.6, the notice state machine; the cells re-pointed, the mutation table re-anchored): a default import over a held target records the notice PENDING (held bytes unchanged), an absent target's is STANDING and inert, a later arrival must show the redaction in both modes (PENDING on a default import, applied on a restore), the origin check is REMOVED (origin decides nothing, INV-RR12), and an export carries no non-applied notice beside its record, so a store's own export no longer pairs a hostile notice with the user's fact (research's B1) | `$PY -m pytest tests/test_0041_notice_binding_hotfix.py::test_an_untrusted_notice_never_redacts_the_users_own_held_fact tests/test_0041_notice_binding_hotfix.py::test_an_untrusted_notice_never_redacts_a_held_episode tests/test_0041_notice_binding_hotfix.py::test_the_victims_exact_record_in_the_file_does_not_unlock_the_notice tests/test_0041_notice_binding_hotfix.py::test_a_held_different_version_under_an_untrusted_notice_is_kept_and_reported tests/test_0041_notice_binding_hotfix.py::test_an_untrusted_notice_for_an_absent_id_leaves_an_inert_standing_row tests/test_0041_notice_binding_hotfix.py::test_a_later_unredacted_record_of_that_id_is_refused_whole_and_nothing_is_redacted tests/test_0041_notice_binding_hotfix.py::test_i_a_legacy_standing_notice_never_refuses_the_users_own_write tests/test_0041_notice_binding_hotfix.py::test_i_a_legacy_standing_notice_never_refuses_the_users_own_episode_write tests/test_0041_notice_binding_hotfix.py::test_ii_an_unredacted_default_arrival_under_a_standing_notice_is_refused_whole tests/test_0041_notice_binding_hotfix.py::test_ii_a_default_REDACTED_arrival_from_another_origin_is_pending_origin_decides_nothing tests/test_0041_notice_binding_hotfix.py::test_ii_an_unredacted_arrival_under_a_standing_notice_refuses_even_on_restore tests/test_0041_notice_binding_hotfix.py::test_7a_a_poisoned_export_default_imported_refuses_and_redacts_nothing tests/test_0041_notice_binding_hotfix.py::test_7b_a_poisoned_export_restored_into_a_fresh_store_refuses_and_redacts_nothing tests/test_0041_notice_binding_hotfix.py::test_7c_a_poisoned_store_restoring_its_own_export_refuses_and_keeps_the_fact tests/test_0041_notice_binding_hotfix.py::test_7_the_default_path_reports_a_held_target_before_it_would_refuse tests/test_0041_notice_binding_hotfix.py::test_a_notice_only_restore_onto_a_held_record_is_not_applied tests/test_0041_notice_binding_hotfix.py::test_a_repeat_untrusted_import_stays_inert tests/test_0041_notice_binding_hotfix.py::test_the_cli_prints_the_notices_it_did_not_apply tests/test_0041_notice_binding_hotfix.py::test_the_attest_only_branch_is_restore_only_on_a_default_import tests/test_0041_notice_binding_hotfix.py::test_the_primitive_defaults_to_the_narrow_scope tests/test_0041_notice_state.py::test_a_default_import_never_changes_a_held_record_through_a_notice tests/test_0041_notice_state.py::test_a_standing_notice_over_a_local_write_is_weighed_as_a_held_target tests/test_0041_notice_state.py::test_origin_decides_nothing tests/test_0041_notice_state.py::test_a_stores_own_export_round_trips_whatever_its_notices_hold -q -p no:randomly` |

<!-- /GENERATED:review-closure -->

# Appendix A — how the contract got here (HISTORY, not contract)

> **Moved out of §11 at v6 on the round-3 ask.** Nothing here governs. It is
> kept because a correction with its reason deleted is a claim nobody can
> check, and this document has withdrawn enough claims to owe that.

## A.1 The four conflicts resolved at v3 (F7)

| # | conflict | resolution |
|---|---|---|
| 1 | **D1** selects a closed reason vocabulary; **§2c** still permitted length-capped prose | **D1 governs.** §2c's cell is corrected in place. A length cap is not a defence — the content that matters is short |
| 2 | **D2** carries redaction events and vocabulary reasons; **INV-6** prohibited reasons from export and **§10** still said the event is omitted | **D2 governs.** INV-6 is amended below to fence *free* reasons, not vocabulary ones; §10's item 3 is superseded |
| 3 | **§2** requires all three duplicated edge columns; **INV-2** checked only `object` | **§2 governs.** INV-2 is restated to enumerate from the DDL |
| 4 | 🔴 **v6 (F4): PRECEDENCE STATED, AND v5 CONTRADICTED ITS OWN TABLE.** §11.1 said *"the deletions govern"* for `contribution_ledger`, while §2d-iii-bis rows 21 and 23 rule **CLEAR the field, KEEP the row** — and §11 claims to govern, so the contract contradicted the map it points at. **THE MAP IS RIGHT AND §11 IS CORRECTED:** rows DELETED are **`wiki` and `edge_embedding` ONLY** (derived, rebuildable, no history). **`contribution_ledger` rows are KEPT with their digest fields cleared** — the absorption record is a judgement and INV-7 disposes of the ORACLE, not the record. **Where §11 and §2d-iii-bis differ on a ROW, the per-candidate map governs; §11 governs on CONTRACT.** |

## A.2 — why §11.2 references the registry (round-3 F3)

> 🔴 **ROUND-3 F3. v5 listed TWELVE values and called them the vocabulary. Those
> twelve are the JOURNAL's (`edge_event.reason`), and they are not the registry.**
> Verified: `veracium.schema.DISPOSITIONED_REASONS` holds **SEVEN** —
> `absorbed_duplicate` · `corrected` · `decayed` · `disputed` · `lapsed` ·
> `revoked_source` · `superseded`. **My list omitted four of them.**
>
> **And the product already has the closure discipline I re-enumerated wrongly.**
> `schema.py:558`, in its own words: *"DISPOSITIONED_REASONS is the process
> record W5's registry test diffs against: every reason any producer can pass,
> each explicitly dispositioned. A producer growing a new reason fails
> `test_invalidation_reason_registry_is_total` until the spec that adds it
> dispositions it here."*
>
> **A spec that RE-TYPES a registry drifts from it the moment either moves. This
> section now POINTS at it** — the same rule this document applies to carriers,
> applied to itself.

## A.3 — why §11.3's numbering was restored (round-2 F7)

> 🔴 **F7, and this is the worst defect in the spec because of WHERE it sits.**
> §11 declares itself the operative contract — *"where anything above conflicts
> with this section, this section governs."* **Its invariant matrix then
> silently changed what two invariants MEAN and omitted two others entirely:**
>
> | | §6, the real invariant | §11.3 at v3.2, what I wrote |
> |---|---|---|
> | **INV-1** | **structure preserved** — chain lengths, `seq` contiguity, reference integrity unchanged | *"no carrier holds the content"* |
> | **INV-3** | **`why` degrades, never fails** | *"record and redaction state commit in one transaction"* |
> | **INV-4** | journal carries no residue | **absent** |
> | **INV-5** | scope — cross-user or unknown target refuses loudly, never a silent no-op | **absent** |
>
> **A reader trusting §11 as governing would have believed INV-1 means content
> removal and would never have checked structure preservation at all** — and
> INV-5, the one that forbids a silent no-op, is exactly the invariant whose
> absence is hardest to notice.
>
> **The section written to make the spec say one thing said a different thing
> with more authority.** §6's numbering is restored below and is canonical;
> everything research added is numbered from **INV-8 upward**, where it cannot
> collide with a meaning that already exists.
