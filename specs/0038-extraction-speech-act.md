# Feature spec: the extraction's speech-act discipline

Spec-Status: accepted

*Candidate authored by research (veracium-research), 2026-09-07, on the owner's
word ("I approve your recommendation on all three and order you to implement all
3", 2026-09-07). **0038 — the registry's next uncontested number:** ALLOCATION
holds 0001–0032 and 0037; **0033–0036 are RESERVED** for the self-learning
decomposition arc (banked 2026-09-04, upheld by the owner 2026-09-06) and live
in COORDINATION rather than ALLOCATION, which is exactly how research collided
with them once before. Checked both, and for any claim on 0038: none.*

| | |
|---|---|
| **Author / session** | research (veracium-research) |
| **Version** | **v6.0 — ACCEPTED at external round 4, 2026-09-08.** Verdict **ACCEPTED**, banked verbatim `outbox/0038-round4-verdict-verbatim.md` — **body `4d037fb676e66445`** (the reviewer's words: everything after the first `\n---\n`, taken RAW and hashed as UTF-8 — **the rule is stated in that file because research first published a digest computed by an unstated one and dev could not reproduce it; a digest must be reproducible from a stated rule or it is a typed number**); dispatch inferred from the verdict's arrival, per the runbook. **REGISTRY RE-PINNED AT CLOSURE to `5c37d57159ffa624`** (was `5dcd1ee1e7ec2a6d`, and that value stands unaltered in this cell's *Prior:* history — **a record of what v5.8 said is not amended to agree with what came later**). The cause is a **FROZEN-at-round-4 marker** dev added at the head of the registry's CHANGELOG, quoting the reviewer's five limits and stating that editing a ruling is not a constant change but a reopening of design review on an accepted spec. **The move is COMMENTS ONLY: the diff against the accepted package's registry is seven added comment lines, and the RULINGS DIGEST IS UNCHANGED at `af7823c7ac15152f`** — the published digest tracks the FILE and the rulings digest tracks the TUPLE, which is exactly why the spec carries both with their methods stated. `5dcd1ee1…` is declared foreign as a superseded digest of a listed file, the same category as `197e0976…` and `54acc45a…`. **ACCEPTED PACKAGE, in full:** `0038-round4-review-package.tar.gz` sha256 **`eccfada2950b3ec33dcc137fa3c0751f323556fc359f41a70ee54ae071edd8e9`** @ pin **`8588e558ede0ce1989aec2ab421274187c690914`** (v5.9), CI **34173288704**, 668 members, both legs **38 PASS / 0 FAIL / 1 named N/A**, DISCLOSED 13 and every identifier confined to the disclosure carriers. **ALL FOUR FINDINGS CLOSED:** R3-1 (supersession headers on the two run records; the manifest-bound current disposition; a shared checker that rejects silent or unmarked recurrence), R3-2 (one `token_membership_violations` serving the real specification and the planted mutation), **R3-3 CLOSED BY NARROWING THE CLAIM** — *"the specification now accurately says the package cannot independently establish fidelity to the unavailable original"* — and R2-4 remains retracted, the heading occurring once. **THE FROZEN SURFACE IS THE EVIDENCE LIMITS, NOT AN INVARIANT LIST — the reviewer enumerated none, so the limits ARE the surface, and they are frozen here IN THE REVIEWER'S OWN WORDS:** *"The original validation gate is not met. The weaker §6b-A rule is met but is not a substitute. The human leg was rubric-applied and not blind. The strongest independent evidence comes from the blind model leg. A new blind human evaluation by a different person would be required to close that remaining methodological gap."* **The narrowing is what was accepted: every one of those five sentences is a limit this document volunteered, and the reviewer adopted them verbatim rather than adding a finding.** **GOVERNING FORWARD:** *"No additional artifacts or another external review round are required"* — and the reviewer's **non-blocking packaging note**, which is an obligation and not an observation: future receipts must list `tests/test_oracle_set_disposition.py` beside the three focused 0038 files, since **it now enforces a central acceptance property**. It already runs and passes inside the sealed suite, so no package is invalidated. ***The shape of that gap is a known defect and is recorded rather than quietly fixed: the focused list was assembled when the three pin tests WERE the acceptance surface and did not grow when the surface did — a hand-maintained set whose prose reads as full coverage.*** **THE CHECK'S OWN LIMIT STANDS AS ACCEPTED, UNSOFTENED:** over the present set every phrase-bearing file is declared exempt or a declared header-governed record, so **the paragraph rule has no live input today** and is exercised by its four negative controls — *"it holds over the set"* and *"it fired on the set"* are different claims and only the first is true. **THE ARC:** four external rounds — R1 six findings, R2 the §8-gate retraction (option 3: define an explicitly weaker §6b-A rather than claim a gate whose blind-human condition was unmet), R3 the finding that a retraction in this document was not a retraction in the artifacts it BINDS, R4 accepted — across **two discarded assemblies and one reseal**: round 2's first assembly (`c9b2b63d…`) and round 4's first (`18ad6b69…` @ `20a71033`, CI 34170891719), the latter discarded AFTER both legs were green, because the disposition artifact answering R3-1 carried a stale to-do about the very file it dispositioned. **Both discards are disclosed in the accepted package's lineage; neither was hidden.** **CREDITS.** *Dev seat:* the oracle pin and its exclusion-rule anti-check, the shared membership validator, `test_oracle_set_disposition.py` with its four negative controls, four seal chains, and **the catch that produced the reseal — reading an artifact against the file it describes, which is the one thing neither seal-check leg does.** *Research seat:* the spec and every fold, the corpus and the 74-item oracle pack, the blind cross-family model leg (AST-tested for blindness with three leak mutants), the two-seat second leg on every package, `SUPERSEDED-CONCLUSIONS.md`, and the four design findings that narrowed the new check before it landed. *The project's human rater:* both labelling legs, and the ruling that the record of a run is not amended to agree with a later conclusion. *Quentin:* the option-3 ruling that replaced a claimed gate with an honest weaker one, and the dispatch of every round. *Prior:* **v5.9 — THE ROUND-4 SECOND ASSEMBLY. THE DISPOSITION OF THE EVIDENCE WENT STALE WHILE THE EVIDENCE WAS CURRENT.** Round 4's first assembly (`18ad6b69…`, **discarded before dispatch**, both legs green) shipped `SUPERSEDED-CONCLUSIONS.md` saying the registry's changelog *needed* a marker it had already been given in the same package — **R3-1 recurring one level down: round 3 found the spec current and the evidence stale; this found the evidence current and the DISPOSITION of the evidence stale.** Caught by the dev seat reading the artifact against the file it describes, which **is the one thing neither seal-check leg does** — the seal-check asserts transport fidelity, never agreement between two carriers of one fact. **THE RULE: AN ENTRY PHRASED AS A TO-DO GOES STALE THE MOMENT IT IS DONE AND NOTHING CAN TELL; AN ENTRY PHRASED AS A STATE CAN BE COMPARED AGAINST THE FILE.** `owned_elsewhere` **deleted, not corrected** — it meant *true, but checked somewhere else*, and somewhere else was no one. Fix is a check, not a better sentence: `tests/test_oracle_set_disposition.py`, inside `lint_withdrawn`'s own selection, with the discarded assembly's entry as **the fixture that must fail.** Its limits are stated in §6b, not discovered later. **v5.8 — THE EXTERNAL ROUND-3 FOLD. A RETRACTION IN THIS DOCUMENT WAS NOT A RETRACTION IN THE ARTIFACTS IT BINDS.** Verdict RETURN (banked **before** the fold this round, body `1515c689645d6fb9`, correcting round 2's order deviation). **R3-1 BLOCKING, and it is the rule research wrote this morning applied one level up:** §6b withdrew the §8-gate claim and **the bound evidence set went on asserting it** — *"THE §8 GATE — PASSES"*, *"two independent raters"*, *"§8 PASSES"*, *"Nothing to pass"* — in files the manifest binds as evidence FOR this spec, **so a reader following the evidence reached the conclusion the spec had withdrawn.** Research swept the document and never swept what the document binds: **correcting the citation is not correcting the defect, at the level of an evidence SET rather than a sentence.** **THE REVIEWER NAMED TWO FILES; SWEEPING ALL SIXTEEN FOUND FOUR** — also `RUBRIC.md` and `verb_registry.py`. New bound **`SUPERSEDED-CONCLUSIONS.md`** is the set's current disposition (where a file disagrees with it, IT is current and the file is a record of a run); supersession headers on the two write-ups; and the check's data as **JSON with reasons**, in `known_foreign_digests`' shape, because **an exemption in prose is an exemption nobody can check.** ***`RUBRIC.md` is NOT amended and that is the round's sharpest point:*** it is the instrument the rater was **shown**, so amending it would make the record of the run false — **and it is evidence FOR the circularity §6b-A concedes**, since the rubric gave the rater the registry's own principle and the run was then scored against the registry. **A record amended to agree with a later conclusion is no longer a record.** **R3-3 — THE CLAIM SHRINKS INSTEAD OF THE EVIDENCE GROWING.** A checksum of an ABSENT original proves the copy has *a* digest, not that it differs *only* by the stated substitution; §6b now states that the package carries a bound derived copy and **cannot independently establish byte-level fidelity to an original it does not carry.** Shipping the original would publish the owner's name in the RATER role his ruling covers, and an attestation is a promise rather than a proof. **The registry is re-pinned to `5dcd1ee1e7ec2a6d`** — dev marked its CHANGELOG's own *"the §8 gate PASSED"* as WITHDRAWN; **comments only, and research verified the RULINGS digest is unchanged at `af7823c7ac15152f` before mirroring the file byte-for-byte** rather than re-editing it, so the set stays one artifact. `54acc45ad818fa94` becomes a superseded digest of a listed file, the `197e0976` category. **R3-2 is dev's and the reviewer stated a rule already in this programme's runbook** — *a selftest must call the real function, never re-implement it*: the planted-token control rebuilt the allowed-set logic, **so the production scanner could have stopped inspecting paragraphs while the control kept passing.** **R2-4 RETRACTED BY THE REVIEWER** — the heading occurs exactly once; reporting does-not-reproduce with counts, rather than changing correct text, was right. *Prior:* **v5.7 — A SECOND SPAN CASUALTY FROM THE SAME REWRITE: §9's OPENING SENTENCE.** Dev found it carrying §9 verbatim into the round-3 README: the section began *"every acceptance figure rests on."* — **a fragment.** R2-1's rewrite of §9's headline replaced from the paragraph's start through the gate claim and **kept the tail**, so the sentence lost its subject while reading as prose. **v5.6 recovered three sections this same rewrite deleted; this is the fourth casualty of one replacement span, found a round of respins later.** Restored from v5.4 **as a FOLD, not a copy** — the seams named there are still the right two (§2c row 1 and §6b's oracle), and the tail that follows now reads from a complete sentence into the withdrawn-gate paragraph. **d07043d is superseded as the pin; it stays on main and the next commit is the pin.** **AND THE GATE DEV IS ADDING NEEDS ITS DISCRIMINATOR, WHICH RESEARCH MEASURED RATHER THAN GUESSED:** *"a section whose first line starts lowercase"* fires **7 times on this document, 6 of them markup** — table headers, code spans, bold openings. **A gate with a 6-in-7 false positive rate is a gate that gets switched off**, which is the failure this programme has spent the day removing. **The discriminator is a BARE lowercase letter — a leading table-pipe, backtick, asterisk, hyphen or angle-bracket is markup, not a fragment — and it gives exactly ONE hit: the real one.** *Prior:* **v5.6 — RECOVERING THREE SECTIONS v5.5's OWN FOLD DESTROYED, AND THE CAUSE IS A REPLACEMENT SPAN.** Dev's adoption gates refused v5.5 before any copy: **the `oracle manifest sha256:` column-0 line had ZERO occurrences.** Investigating it found worse — **research's R2-1 rewrite replaced everything from the gate heading to `#### DISCLOSURES`, and three sections lay inside that span**: `THE EVIDENCE SET — ONE PIN` (carrying the manifest pin line and the bidirectional binding rule), `WHEN EACH RULING WAS WRITTEN` (the eight-row timeline **dev had specifically asked for**), and `THE DRIFT TEST — its exact null` (**also dev's ask**, with `2/C(19,6)` and the 1-vs-3 counter-example). **A replacement span deletes everything between its ends, and the ends were chosen for the section being rewritten, not for what lay between them.** Recovered from the landed v5.4 at `f891522` — **the artifact that still had them** — and re-inserted with the pin token restored to 64 zeros. **One thing the recovery would have silently reintroduced: the recovered text names the manifest key `spec_text_sha256_excluding_the_oracle_manifest_line`, which round 2 RENAMED** to `…_excluding_both_pin_lines` because the key said one line while its value was two; corrected on re-insertion, with `excluded_lines` named as the DATA the pin test asserts. ***Recovering old text recovers its old errors — a restore is a fold, not a copy.*** **Also: the version cell now carries WITHDRAWN**, because it quotes *"the §8 gate PASSED"* five times as history and 0038's first two register entries make that a dead claim — the same marker v13 needed on 0028 for the same reason, and the register catching the document that retired the phrase. *Prior:* **v5.5 — THE EXTERNAL ROUND-2 FOLD. WITHDRAWN CLAIMS quoted below as history: "the §8 gate PASSED" and "a named deviation, not waived" are DEAD and are named here only to record that they were made.** THE §8 GATE IS NOT MET AND THIS SPEC NO LONGER CLAIMS IT IS.** Verdict RETURN for amendment (2026-09-07); one blocking finding, three corrections. **R2-1 — THE BLOCKING ONE, AND IT LANDS ON v5.4's OWN SENTENCE.** v5.4 said the gate *"PASSED … with the human leg rubric-applied and not blind — a named deviation, not waived"*. **The reviewer: naming a deviation from a mandatory condition does not satisfy it, and "not waived" makes the claim worse rather than better. DISCLOSURE IS NOT COMPLIANCE** — the hole was documented carefully and then the claim the hole disproves was made anyway. **Research verified before folding that NO resolution exists in current data: run 1 WAS blind but its answer space was performed/reported/neither with NO `committed` class** (the category did not exist until the registry did), so the blind leg is **not merely disqualified by drift — it is UNCOMPUTABLE on this gate's classes.** And a fresh blind run is unavailable from this seat: the one human rater has labelled the corpus twice and knows which class was disputed — **blind in form, not in substance, which is the same error as the named deviation.** *(94 unseen procedural records exist, but the frozen registry classifies 0 of them, so a fresh pack would require re-freezing the thing being validated.)* **ON QUENTIN'S RULING — option 3 of the reviewer's three: stop claiming the gate passed and define an explicitly weaker criterion.** §6b now states plainly that `VALIDATION_GATE.md`'s §8 gate is **NOT SATISFIED, its human condition UNMET, and that nothing below substitutes for it**; the §6b heading and §9's brief carry the same words, found by a NOUN sweep over the whole file rather than by correcting the sentence the reviewer quoted. **NEW: §6b-A, the oracle acceptance rule for 0038, which borrows the gate's STATISTIC and none of its AUTHORITY** — one **blind** rater that is a **model** (blindness AST-tested, three leak mutants), one **rubric-applied** human with intra-rater consistency measured directly (8/8 hidden repeats, the thing run 1 lacked), per-class κ ≥ 0.60 with n ≥ 10 under the **blind** rater's classes, **plus** the ceiling cleared **on the blind leg alone** (registry v1 ↔ model 0.909 > 0.795). **§6b-A IS MET; THE §8 GATE IS NOT; THE TWO ARE NOT INTERCHANGEABLE.** And §6b now states what §6b-A **cannot** support: no human-independent validation (registry↔human 0.840 is partially circular), no claim that an unaided human reproduces the oracle, **the strongest honest claim is the blind MODEL leg's**, and closing the gap needs **a different person**. **R2-2** the token-side claim was stronger than its test — a STALE token matches no current digest and is skipped, indistinguishable from a citation of a non-public artifact, of which this document holds three; narrowed to what the tests establish, with the FILE side named as the only protection against a stale citation and its reach stated as exactly the filename list. **R2-3** `VALIDATION_GATE.md` was absent from the package and now travels — as a **DERIVED, MARKED, PSEUDONYMISED COPY**, because the frozen original names the owner in the **rater** role that his own ruling covers, and **a frozen document is not edited to suit a later publication**: the original's sha256 `a11755db…` is recorded in the copy's header with the single transformation stated, so the freeze stays intact and the copy declares itself a copy. **R2-4 DOES NOT REPRODUCE and no change is made:** `## 4. The field-consumer table` appears **once** in the repo's spec, once in the package's tree copy, the two are byte-identical, no heading in the file is duplicated and there are no hidden characters — reported to the reviewer with the evidence rather than silently ignored or 'fixed'. *Prior:* **v5.4 — THE EVIDENCE SET IS BOUND BY ONE PIN, AND THE BINDING IS BIDIRECTIONAL.** The fifteen files a reviewer needs to verify any κ ship at `tests/eval/extraction_speech_act/oracle/`; **§6b pins ONE digest — the manifest's, on a single column-0 line — and the manifest carries every file's.** Fifteen digests in prose would be fifteen things going stale independently, which this document demonstrated twice today at smaller scale. **The circularity resolves the corpus pin's way:** the spec's line is `sha256(MANIFEST.json)`; the manifest carries the spec's text digest computed with **exactly that line removed — line plus terminator, exactly one asserted** — so neither direction depends on the other's token. *(The `\s*` over-deletion trap is the corpus pin's own rule and applies unchanged: `\s` matches a newline.)* **THE BINDING IS RUN FROM BOTH SIDES**, because research's review of dev's proposed test found it one-directional: **every filename §6b names must be a manifest entry** (catches a wrong digest for a file that did not move) **and every 16-hex token here that equals a manifest file's digest must be that file's current one** (catches a citation of a file that moved). Digests naming **non-public** artifacts — registry v1 `7862ab9b`, the round-1 verdict `3f5d96e0`, the rulings digest — are untouched by either. **WHAT THE REVIEW FOUND BEFORE THE TEST WAS WRITTEN:** dev intended to bind four digests *"v5.3 already cites"*; **it cited two.** `d9a69a7a` (FREEZE_v2) and `a656970c` (the pack) were absent — **research had given the first in a MESSAGE and never put it in the spec**, the same shape as the fabricated digest in a message summary earlier the same day, one level up. **And only ONE of the fifteen public files had its digest in the spec at all**; five more were named by filename with no binding. **THE RULINGS DIGEST NOW STATES ITS METHOD** (`ast.unparse` of the parsed tuple, SHA-256, first 16) **because the manifest computes the same CLAIM by a different method and gets a different number** — `af7823c7ac15152f` here, `21289647a85b3b43` there. **A digest without its method is not reproducible, and two numbers for one claim read as a contradiction unless both say how they were made**; the claim itself — research-tree and published tuples EQUAL — was verified by direct comparison in both seats, which is stronger evidence than either digest. **Also removed before landing: a `__pycache__` directory research had left in the public set** by importing the registry in place; the pre-commit gate gains `no __pycache__/.pyc` beside the pseudonym check, and dev had made and caught the identical slip. *Prior:* **v5.3 — THE PUBLIC ORACLE SET, on Quentin's ruling (dev session, verified as his): *"Pseudonymised with aggregated timing."*** The §6b evidence must travel with the round-2 package or a reviewer cannot verify a single κ, and the repo is **public**. **Rater is `human_1` in the files and the filenames; §6b names the rater as "the project owner"; per-item timing is REDUCED to min/median/max** with the file stating that the per-item trace exists off-repo and that **no published claim rests on it** — the drift finding is derived from POSITION (exact combinatorial null), never from timing, and the medians cut both ways when it was written. **EXACTLY ONE DIGEST MOVED, and NOT for the reason the change was made:** `verb_registry.py` **197e0976272eed3d → 54acc45ad818fa94** — the registry never carried the name; it moved because the published copy must resolve the corpus in the **repo** layout as well as the research one, since a module that cannot find its corpus fails with a *path* error, which reads as a broken file rather than a moved one. **THE RULINGS DID NOT MOVE AND THAT IS CHECKABLE, NOT ASSERTED:** the `VERB_REGISTRY` tuple parsed from each copy digests to **`af7823c7ac15152f`** in both, so §6b and the freeze doc now cite **the published file digest AND the rulings digest** — a carrier pinning only a file digest cannot say whether a change touched a **ruling** or a **path**. **Every other digest §6b pins is unchanged and verified**: the corpus `a239b296d126ca78` (the repo's copy is byte-identical to the research tree's), registry v1 `7862ab9b1b9f49cb`, and the round-1 verdict `3f5d96e0cd2df90c` (re-checked against the file — intact, not stale). **ONE REFINEMENT TO THE DE-IDENTIFICATION, which research checked rather than applied blindly: the owner's name is ALREADY IN 22 OF 42 PUBLIC SPECS** as the maker of rulings, so stripping it from this spec's version cell would be inconsistent theatre while achieving nothing. **What is genuinely new exposure — and is removed — is the BEHAVIOURAL data: a named individual's per-item hesitation times and his individual annotation record.** The name stays where it attributes a **decision**; it goes where it identifies a **rater**. *Prior:* **v5.2 — F1 AND F2 SURVIVED IN §9, THE SECTION THAT SUMMARISES §6b, IN THE SAME FOLD THAT FIXED THEM.** Dev's confirming read: v5.1 corrected both at their DEFINITION site and left both at their SUMMARY site — §9's headline still read *"It IS now **independently** labelled and the §8 gate PASSED"*, carrying F2's disallowed word and quoting the result **without the bound §6b's own heading had just gained**; and §9's bullet still carried F2's original sentence verbatim while §6b's copy said "consistently". **This is R6-1 INVERTED — there the summary was fixed and the definition kept the old rule; here the definition was fixed and the summary kept it** — and it is the FOURTH time a stale claim has been found in a §9 across this programme's specs. **A NOUN sweep for `independ` over the whole file finds all of them in one command; the fix that produced them was a sweep for the SENTENCE the reviewer quoted.** **Correcting the citation is not correcting the defect.** **A THIRD site, which dev's read did not name and the same sweep caught: §6b's own HEADING read "the §8 gate PASSED" bare.** A section heading is the most-quoted summary in a document, so by F1's own rule — *the bound rides in the summary or it is lost* — the heading needed it too; it now reads **"FROZEN; the §8 gate PASSED on a NAMED DEVIATION"**. All three sites now carry: rubric-applied and not blind, a named deviation from `VALIDATION_GATE.md` §1, the blind run excluded for drift, and **only the MODEL leg independent**. *Prior:* **v5.1 — DEV'S §3a READ FOLDED (six findings, three of them load-bearing).** **F1 — THE GATE'S OWN HEADING CONTRADICTED ITS DISCLOSURE.** §6b opened *"the programme's standard: BLIND human labelling … all three were done"* — **false of the gate's data.** `VALIDATION_GATE.md` §1 requires the human labeller blind; the leg the gate scored is **run 2, rubric-applied and NOT blind**, and the blind run (run 1) never fed the gate because drift disqualified it. **The bound now rides in the sentence that states the result** — *"the §8 gate PASSED, with the human leg rubric-applied and not blind; the blind run drifted and is excluded; this is a DEVIATION from the frozen gate's §1, named and not waived"* — because a bound carried only in a disclosure is lost the first time the heading is quoted. **That is R6-1's shape on 0028, in this spec, found by dev's decorative test.** **F2 — "INDEPENDENTLY" WAS THE ONE WORD THAT COULD NOT STAND.** Run 2 was rubric-applied from the registry's own principle by a rater who knew the disputed class, so registry↔human is **partially circular**; the claim is narrowed to what it supports — that the principle, once written, is applicable **consistently**, which is why run 2 shows no drift where run 1 did. **F3 — THE CEILING ARGUMENT WAS QUOTING v2'S FIGURES, RAISED BY AN EDIT THE RATERS' OWN LABELS INFORMED.** registry v2 scores 0.932/0.863; **registry v1 — the version the gate ran against — scores 0.909/0.840**, and the paragraph now quotes v1. **The argument also now rests on the MODEL figure ALONE** (0.909 > the 0.795 ceiling), because the model leg is blind by construction and the human leg is not. `VERB_REGISTRY_FREEZE_v2.md` had already called v2's figures a circular recomputation **and the spec quoted them anyway** — the disclosure was written and then contradicted one document away. **F4** the AMBIGUOUS 0/74 now states its implication (every card took one of three labels, so **no item was excluded** and the per-class n sum to 66) instead of "recorded rather than concluded". **F5** the per-class `n` is now named as **the MODEL's labels** — one-vs-rest κ needs the class defined by a named rater, and the blind rater is the one to define it. **F6** `PERFORMED 21 · COMMITTED 22 · REPORTED 23` are **EPISODES**, said so, and the registry's 31 **entries** divide differently (performed 15, reported 12, committed 4) — two counts sitting near each other that must not be read as one. *Prior:* **v5 — THE ORACLE IS FROZEN AND THE §8 GATE PASSED; ROUND-1 R1-2 IS CLOSED.** v4 stated the completed-performance rule and said honestly it was **not validated**, naming the §8 gate as the standard and the human half as **the owner's to assign**. All three legs have now run. **THE ORACLE IS A REGISTRY, NOT A RULE:** `verb_registry.py` sha16 `197e0976272eed3d` (v2), corpus pinned `a239b296d126ca78`, **31 entries TOTAL IN BOTH DIRECTIONS with an import-time gate** — the `DISPOSITIONED_REASONS` shape. **v4's derived rule is SUPERSEDED and its own table says why**: keyed on the instruction's verb reappearing as the episode's main finite verb, it lost to the regex on `ran` (irregular past) and `copied` (`-y → -ied`) — surface matching failing exactly where surface matching fails. The registry keys on the EPISODE's verb form and disposes each explicitly, so an unseen form **fails the import** instead of being silently mis-scored. **THREE dispositions** (PERFORMED 21 / COMMITTED 22 / REPORTED 23) on Quentin's ruling that **deciding and doing are separate acts**; V-NO-FABRICATED-ACTION still fires on **PERFORMED ONLY**, so the spec does not widen — COMMITTED is measured and reported rather than folded into "fine". **THE GATE PASSED:** per-class one-vs-rest κ, human vs MODEL, **performed 0.857 / committed 0.804 / reported 0.728**, all ≥ 0.60 with n ≥ 20, and the corpus gate requires every class. Model leg `gpt-4.1-2025-04-14` temp 0, 74/74, 0 unparsed, **blind by construction with the blindness TESTED** (AST assertion, three leak mutants kill it). **THE CEILING IS THE REAL BOUND:** human↔model κ **0.795**, registry↔human 0.863, registry↔model 0.932 — **the oracle agrees with each rater more than the raters agree with each other**, so it sits above the inter-rater ceiling and no tightening of it could be validated by these raters. Stated as a bound, not a boast. **DISCLOSED RATHER THAN IMPLIED:** the registry was authored after the first labels and the key were seen (**not** a pre-registration — only the rulings' freeze-before-scoring is claimed); the second human run was **NOT blind**; **run 1 DRIFTED** (policy on `decided to` changed once mid-run, **perfect positional separation, p = 0.00007**), which is why run 2 carried **8 hidden repeats** — 8/8 consistent, model 8/8 at temp 0; and **AMBIGUOUS was chosen 0/74 by BOTH raters** despite the rubric saying it is a finding, recorded rather than concluded. **ONE RULING CARRIED AS CONTESTED:** `stated a practice ⇒ PERFORMED`, model 3/3 for, human 3/3 against — 2–1 so it stands, named in §6b and §9 as our own prior for where the registry is most likely wrong. Its counterpart moved: **`asked for` REPORTED → PERFORMED**, because registry v1 contradicted itself (`announced` PERFORMED on reasoning that made `asked for` REPORTED) — **v4's own §6b table had already called this correctly and registry v1 regressed it.** **§9 RE-AIMED:** v4's brief said the decision was *"not yet independently labelled"* — false now, and §9 is what a reviewer reads first, the same site where 0028's brief carried a stale round two rounds running; found by sweeping the NOUN `oracle` over the whole file rather than the phrase already corrected. The manifest's **19/66 remains a FROZEN BASELINE, not a validated rate** (the registry scores PERFORMED on 21/66; the instruments are not interchangeable), and 0037 §8 cites it in those terms and stays correct. *Prior:* **v4 — THE IMPLEMENTATION FOLD.** The enforcement **LANDED** 2026-09-07 at `d59592d` under the owner's security-hotfix exception (`Spec-Retrospective-Due: 2026-09-14`), CI 34120362836 green, suite 2772/8/0 — **the regression file's eight strict xfails are now eight real passes.** v4 folds what implementing it found, both from dev's adversarial diff-scan and neither from re-reading. **THE THIRD-PARTY EXEMPTION IS THE MECHANISM V-THIRD-PARTY-UNTOUCHED REQUIRED AND §2b DID NOT NAME:** v3 said "a triple whose object matches a declared instruction is refused", unqualified — so a received notice filed under `instructions` and emitted as `third_party_claim` would have had its RECEIPT refused, erasing received-claim history and changing `prompts.py:41` in behaviour. **This spec's own invariant forbade what this spec's own clause instructed.** The exemption is keyed on the RELATION, never the author, with the pair that proves it. **THE MCP CLAIM WAS FALSE:** §4's consumer table and §10 Q1 both said the counter reaches the MCP tool result; `_OPERATOR_ONLY` (`mcp_server.py:186`) strips it at `:212`, and dev strips `instructions_dropped` with its siblings on 0031 §4d's argument. **Research enumerated consumers by reading the shape of the data rather than the code that handles it — in the section written to answer R1-6's demand that they be enumerated MECHANICALLY.** The counter is `Memory.remember`'s return value and nowhere else. **THE COMPARISON KEY** is now stated: equality after casefold, whitespace collapse and surrounding-punctuation strip — **never containment**, which would decide a triple IS an instruction without the model saying so, the detection Q6 retired. **NOT in this build and stated as such:** §2a's episode rewording, which belongs with its measurement against the frozen 66. **Still NOT packageable: ONE reader, and §6b's oracle is still unfrozen — the acceptance figures rest on a rule two of research's own instruments disagree about on 12/66, and the §8 gate's human half is unassigned.** *Prior:* **v3 — THE EXTERNAL ROUND-1 FOLD** (verdict RETURN for amendment, 2026-09-07, banked `outbox/0038-round1-verdict-verbatim.md` sha16 `3f5d96e0cd2df90c`; package `4e4053f6…` @ `622bcd1c`, CI 34085071354). Four blocking, two required corrections, all folded. **R1-1 — the structural prevention was not enforced, and it was research's SECOND miss of the same class in this spec:** dev's F1 had already found §2b's drop to be a prompt instruction described as a store mechanism, research took the `instructions` field to fix it, and the reviewer showed the field made the omission OBSERVABLE without making it ENFORCED — `required` still `[triples, episode]`, and a response carrying both carriers is schema-valid. **v3's enforcement is at INGEST** (a triple whose object matches a declared instruction is refused and counted) **and the claim is BOUNDED**: no DECLARED instruction becomes a disposition fact; a provider coercing WITHOUT declaring is not reached, is today's behaviour, and is measured by the new **V-SILENT-COERCION-MEASURED** rather than asserted away — **closing that residual would require the free-text detection Q6 retired on measured evidence, and this spec does not walk back into it**. **R1-2** the invariants had no executable checks and *"a named class"* was not a bounded pass condition — every invariant now names its test node, and **§6b states the oracle's rule AND that it is NOT FROZEN**: research's derived rule and the regex behind the manifest's baseline **disagree on 12/66 and neither is right** (the derived rule misses `ran` and `copied`; the regex fires on `gave` and misses `asked`). **R1-3** §2c is now an eight-row matrix, one row per case, each with an observable outcome and an enforcing invariant; **each row states its own new-behaviour status, and no count is given here** — the v3 draft's cell said "three rows need no new behaviour" while B2 had moved row 2 to NEW BEHAVIOUR, leaving the cell one behind the body (dev read 2). *The fix is not 3→2: rows 3, 4, 5 and 7 also carry new behaviour without using the phrase, and the counter itself is new on every path, so ANY single number here is a simplification that goes stale on the next row that moves. This is the same defect as 0028 v8's "six of its occurrences" — **a count about the document's own contents, written into the document, with nothing deriving it** — and research wrote it twice in one day.* **R1-4** §10 Q1 said the disclosure question was open while §2b said the counter answered it — CLOSED, with the contract stated once and its surfaces named (the ingest report and the MCP result that serialises it; NOT logging or telemetry). **R1-5** 0037 is now Spec-Requires, with the consequence stated: §2b is correct only while V-EXTRACTOR-BLIND holds. **R1-6** §4's field-consumer table with reachability evidence, §3b authorization, §5 regime analysis and §9's reviewer brief restored, because both `prompts.py` and `ingest.py` are GUARDED. **Still NOT packageable: ONE reader, the oracle is unfrozen, and the ingest half is gated on the owner's word** (`IMPLEMENTABLE = ("accepted",)`). *Prior:* **v2 — THE FIRST-READER FOLD** (dev, PROCESS §3a, 2026-09-07, Quentin's ledger word line 782). v1 had ONE reader, its author; dev returned eight findings and **three were blocking**. **F1: §2b's "DROPPED, not coerced" was a PROMPT INSTRUCTION described as a store mechanism** — nothing in the store could tell a triple came from an instruction, `prefers` stayed legal, and the only thing producing the outcome was a RULES sentence gpt-4.1 at T=0 happened to obey 66/66. **The class 0037 was externally returned for twice, in the spec written to fix a related one.** v2 takes dev's option (b): the extraction JSON gains `instructions`, the store counts it as `instructions_dropped` and stores none of it — an invisible omission becomes an observable, countable refusal, which also answers §10 Q1. **F2: V-NO-PRACTICE-RELATION tested the wrong property and was wrong twice** — FALSE TODAY on descriptions (`has_diet`: "dietary practice or restriction") and failing the day 0037 ships `follows_procedure`, while §2b stayed correct; and research had "verified" it with **a hand-made set of practice-words — a hand-maintained list inside the check written to remove a hand-maintained list.** Now **V-NO-PROCEDURAL-IN-PROMPT-VOCAB**, asserting on `render_prompt_relations` (`ingest.py:204`) by `relation_kind`, reusing 0037's V-EXTRACTOR-BLIND — a permanent property, not the registry's current contents. **F3:** the corpus was in the peer tree and unbound (0037 round-2 B3 verbatim); it goes in the repo at `tests/eval/extraction_speech_act/`, digest on a single `corpus sha256:` line, bound both directions by a pin test in `test_0037_corpus_pin.py`'s shape INCLUDING the golden vector. **F4 was worse than found:** the frozen rows carried `n_edges` but NOT the triples, so the coercion baseline could not be DERIVED from the corpus at all — the derived-basis rule inside the corpus written to enforce it. Captured and re-frozen: **31/66 = 47%** (`prefers` 14, `works_on` 15, `uses_tool` 2), **higher than the 29% completed-action rate**, so the fact level leads §1. **F5:** the RULES rule and the episode FIELD DESCRIPTION change in ONE commit — a rule contradicting the field's own description leaves the model two instructions. **F6:** §7 added, **PROSPECTIVE ONLY** — existing stores hold fabricated records today and no migration is attempted, because a migration would have to classify stored text, the same inference that caused the defect. **F7:** V-THIRD-PARTY-UNTOUCHED names node ids. **v2 also fixed a contradiction the fold itself introduced:** §2c still said "no field, no schema version" while §2b now adds one — 0028's §5.1-vs-Q3 shape, inside the fold correcting that class. **SECOND-READ FOLD, same day: F3 WAS NEVER IN THE BODY.** The v2 cell claimed the corpus binding and §6a still pointed at the research tree's own working directory — a peer-tree path, in backticks, with no repo path, no digest line and no pin test named anywhere. (The offending path is described rather than reproduced: a spec in the repo should not carry a live-looking peer-tree reference even inside its own errata.) **0037 round-2 B3 verbatim, plus its cell-vs-carrier disagreement**, written by the seat enforcing *the file is the artifact*. Dev found it by grepping the body for what the cell claimed. Now landed: the corpus at `tests/eval/extraction_speech_act/`, one `corpus sha256:` line, `spec_version` + `spec_pin` in the manifest, `tests/test_0038_corpus_pin.py` in 0037's shape INHERITING its golden vector and exactly-one assertion. Also: **V-NO-COERCED named THREE relations where the manifest's `disposition_set` is FIVE — it would have passed while `avoids_tool` or `has_diet` was coerced into**, so it now derives the set from the artifact and cites the measured 31/66 as its baseline; and its condition is F2's rather than the premise F2 replaced. **Still NOT packageable: the new text has ONE reader.** |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | — (research only; **this text has had ONE reader**) |
| **External review** | REQUIRED — changes what the product stores from a given input. **Conducted RETROSPECTIVELY under PROCESS §3b's security-hotfix carve-out** (the enforcement shipped at `d59592d`, 2026-09-07, on the owner's authorization; four external rounds followed; accepted 2026-09-08) — **the retrospective obligation `Spec-Retrospective-Due: 2026-09-14` is DISCHARGED below (§ Retrospective, written 2026-09-08)** |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0037** — procedural records and the `basis` axis. **This spec consumes 0037 directly and v2 never said so (round-1 R1-5):** §1a's cause B rests on **V-EXTRACTOR-BLIND** keeping every `relation_kind="procedural"` relation out of the vocabulary rendered to the prompt, which is why an instruction has nowhere legal to go; `record_procedure` is the governed path this spec declines to duplicate; and §2b's drop is correct ONLY while 0037's blindness holds. **0037 is ACCEPTED** (external round 5, 2026-09-07). If V-EXTRACTOR-BLIND is ever relaxed, §2b must be re-decided — V-NO-PROCEDURAL-IN-PROMPT-VOCAB fails first and says so.

---

## 1. Problem — measured, not hypothesised

The shipped reference extraction converts a user's **instruction** into a record
asserting the user's **action** or **disposition**. Both are claims the input
does not make.

**At the episode level** — 19/66 = **29%** of bare procedural inputs:

```
in      Run migrations against production without taking a backup.
stored  On 2026-09-07, the user ran migrations against production without taking a backup.
```

**At the fact level**, which is worse because edges are assertable and render in
the grounded block:

```
in    Reuse the same password across service accounts.
fact  user | prefers | reuse the same password across service accounts
in    Grant every new hire admin access on their first day.
fact  user | prefers | grant every new hire admin access on their first day
```

Measured over a 412-text ingestion capture through the shipped prompt
(`gpt-4.1`, temperature 0). The examples are the corpus's **unsafe-practice**
cells, so the store records the user as personally holding and performing the
practices this programme exists to be careful about — carrying
`author_of_evidence=USER`, a real `evidence_ref`, and intact provenance.

**This is a fabricated claim under valid provenance.** Provenance records where
text came from; it cannot record that the speech act was invented. Every
downstream control that trusts a record because its provenance is sound trusts
this one exactly as much.

## 1a. Two causes, and they need different answers

**Cause A — the episode field's wording.** `prompts.py:29` asks for *"what
happened / was decided / was attempted, with outcomes"*. A model asked what
*happened* renders a stated practice as a thing that happened. The
receipt-not-truth discipline that would prevent it (`prompts.py:41`) is **scoped
to third-party authors**; a USER-authored instruction has no counterpart.

Demonstrated by A/B on that clause alone, same model, same temperature, fresh
store per text:

| episode clause | recorded as a completed action |
|---|---|
| shipped | 4/20 = **20%** |
| narrowed | 0/20 = **0%** |

**Cause B — the vocabulary HANDED TO THE PROMPT has nowhere to put a practice.**
The seam is `render_prompt_relations(reg)` at `ingest.py:204`: it is that
rendered vocabulary, not the registry, that the extractor may emit from. 0037's
**V-EXTRACTOR-BLIND** keeps every relation with `relation_kind="procedural"`
**out** of it, by design and permanently — `record_procedure` is the governed
path for a practice. So an instruction has nowhere legal to go, and the
extractor coerces it into the nearest available thing: `prefers`, which asserts
a disposition, or `works_on`, which asserts an activity. **Measured: 31/66 =
47%** of bare instructions are coerced (`prefers` 14, `works_on` 15,
`uses_tool` 2) — *higher* than the 29% completed-action rate, which is why the
fact level leads §1.

*Two earlier cuts of this paragraph got the property wrong, and the second is
the more instructive. The first printed all nineteen relation names in prose — a
hand-maintained list carrying the spec's whole premise. The fix replaced it with
an invariant (now **V-NO-PROCEDURAL-IN-PROMPT-VOCAB**) that first asserted "no relation in the default registry
denotes a practice"— and dev's F2 showed that invariant is **wrong twice**: it
is FALSE TODAY on descriptions (`has_diet` is "dietary practice or restriction")
and it would fail **the day 0037 ships** `follows_procedure`, while §2b remained
correct throughout. Worse, research had "verified" it using a hand-made set of
practice-words — **a hand-maintained list inside the check written to remove a
hand-maintained list.** The property was never the registry's contents; it is
0037's, and it is permanent rather than accidental.*

Cause B is **structural**, not a wording accident, and it is why a prompt edit
alone cannot close this.

## 2. Behaviour

**2a. The episode records the speech act, not an outcome.** An episode states
what was **stated, instructed, decided or observed**. It asserts that an action
was performed **only when the text asserts performance**. A stated practice or
an instruction is not a completed action.

**2b. A declared instruction is FILED and NOT STORED; a triple that carries it
is REFUSED and the REFUSAL is counted — except a `third_party_claim`, which is a
RECEIPT.** The extraction JSON gains one field:

```
"instructions": ["<the instruction, verbatim>", …]     # NEW; may be EMPTY, never ABSENT
```

`EXTRACT_SCHEMA`'s `required` becomes **`[triples, episode, instructions]`** — an
empty list is valid, an absent key is not. R1-1 named the optionality by that
word, so v3 states the change to `required` rather than implying it. *But see
§2c rows 1 and 6: the schema is a HINT handed to the provider (`json_schema=` at
`ingest.py:236`), not something ingest validates, so `required` binds a
compliant provider and nothing else — which is why row 1 exists.*
The prompt directs an instruction **there** and never into `triples`. The store reads the field, **stores none of it**, and **counts REFUSALS — never
declarations** into the ingest report as `instructions_dropped`, beside the
existing `invalid` counter (`ingest.py:261` unparseable, `:449` normal — the two
return dicts, cited by their heads everywhere in this spec).

*v3 draft said "counts the field" in three places while §2c row 4, §6 and §10 Q1
said refusals — **counting the field is counting DECLARATIONS, the first mutant
V-INSTRUCTIONS-WELL-FORMED names.** Section-vs-section, inside the fold that
fixed two of those (dev read 1, B1).* The episode still records that the instruction was given.

*v1 said "DROPPED, not coerced" and §2c-i called it structural — "removes an
emission path". Dev's F1: **nothing in the store could tell that a triple came
from an instruction.** 0037's V-EXTRACTOR-BLIND filters procedural RELATIONS
from the vocabulary; here there is nothing to filter, `prefers` stays legal, and
the only thing producing the outcome was a sentence in the RULES block that
gpt-4.1 at T=0 happened to obey. **That is an outcome asserted as if the code
provided it — the class 0037 was externally returned for twice, written into
the spec that exists to fix a related one.** The field makes it real: an
invisible omission becomes an observable, countable refusal.*

*Chosen over inventing a practice relation deliberately: a new relation is a
registry change with 0037's machinery behind it, and `record_procedure` is
already the governed path. This spec stops the fabrication; it does not open a
new storage route.*

**THE COMPARISON KEY, stated because "matches" and "carries the same content"
are two undefined phrases for one operation.** A triple is refused when its
`object` **EQUALS** a declared instruction after casefolding, whitespace
collapse and surrounding-punctuation strip. **Equality, never containment** — a
containment test would decide a triple *is* an instruction without the model
saying so, which is the free-text detection Q6 retired on measured evidence.

**THE `third_party_claim` EXEMPTION, and it is the mechanism V-THIRD-PARTY-UNTOUCHED
requires.** A received notice ("Pay the invoice by Friday") that the extractor
files under `instructions` **and** emits as `third_party_claim` with the same
wording would, under an unqualified rule, have its **receipt** refused — erasing
the received-claim history 0001/0023's gate depends on and changing
`prompts.py:41`'s behaviour, which V-THIRD-PARTY-UNTOUCHED forbids. **So the
refusal exempts the `third_party_claim` RELATION, keyed on the relation and never
on the author**: a user-disposition triple restating a declared instruction is
refused even on a third-party event, and both cases are tested.

*v3's §2b said "a triple whose object matches a declared instruction is refused",
unqualified — **this spec's own invariant forbade what this spec's own clause
instructed.** Found by dev's adversarial diff-scan while implementing, not by
either seat re-reading. Name the mechanism before the clause.*

*This also answers §10 Q1 — the drop is no longer invisible. `instructions_dropped`
is the `withheld`-with-a-count shape, at the ingest report rather than the read
surface.*

**2c. What changes, stated exactly.** The reference prompt's RULES block and its
episode field description (§2a, §2c-i); `EXTRACT_SCHEMA` gains `instructions`
(§2b); `ingest.py` reads that field, stores none of it, and counts the REFUSALS it causes. **NO
STORED BYTE CHANGES and there is no store migration** — the schema that moves
is the extraction JSON, which is transport between the host's model and the
store, not a persisted format. `Edge`, `Episode`, `Provenance` and the export
FORMAT_VERSION are untouched.

*v2 corrected this row: v1 said "no field, no schema version", which contradicted
§2b's own schema change the moment §2b became structural. A spec whose sections
disagree is the defect 0028's round-1 F1 was — §5.1 claiming "no scan" while §10
Q3 called the same thing scan-backed — and it appeared here inside the fold that
was fixing that class.*

## 2c-i. Untrusted inputs — REQUIRED, blocking

The untrusted input is **the extractor's response** — a BYO model's JSON, which
may ignore the schema entirely. Every row below states an observable outcome and
the invariant that enforces it. **`instructions_dropped` is present on every
return path**, inheriting `V-COUNTER-INVENTORY` from 0025 §4c rather than
restating it (`tests/test_0025_enforcement.py:290,312,330` — the exact-set
assertion at `:330` is what makes the hand-listed `PUBLIC_COUNTERS` safe).

| # | case | observable outcome | enforced by |
|---|---|---|---|
| 1 | `instructions` ABSENT (a provider ignoring the required list) | the response is processed as today; `instructions_dropped: 0`, **present**. **No refusal is possible — there is no declaration to relate a triple to.** This is the residual, §8 | V-COUNTER-INVENTORY; **V-SILENT-COERCION-MEASURED** (§6) reports the rate rather than forbidding it |
| 2 | `instructions` present but WRONG TYPE (string, dict, null) | **NEW BEHAVIOUR — a type check at ingest.** The response is treated as unparseable: zero edges, one placeholder episode, `unparseable: True`, every counter 0 and present. *Executed on shipped code (dev read 1, B2): a string, a dict and null all give `unparseable: None` and ONE STORED EDGE — the existing branch does not catch this, so v3 does not claim it does* | V-INSTRUCTIONS-WELL-FORMED + V-COUNTER-INVENTORY; strict xfail until the check exists |
| 3 | members that are NON-STRING or EMPTY/whitespace | those members are dropped and **not counted** — an empty string is not an instruction; remaining members process normally. `instructions_dropped` counts only what a triple was refused against | V-INSTRUCTIONS-WELL-FORMED |
| 4 | DUPLICATE members | de-duplicated before comparison; `instructions_dropped` counts REFUSALS, not declarations, so a duplicate cannot inflate it | V-INSTRUCTIONS-WELL-FORMED |
| 5 | `instructions` AND a disposition triple carrying the same content | **the triple is REFUSED and counted**; the episode still records the instruction was given. *The reviewer's own example JSON is this row* | **V-NO-COERCED-DISPOSITION** + the scripted-provider regression |
| 6 | a provider ignoring the schema wholesale (prose, bare array, extra keys) | bare array normalised (`ingest.py:241`), prose unparseable — both unchanged. **EXTRA KEYS ARE PROCESSED, NOT REJECTED**: `EXTRACT_SCHEMA` is a HINT passed as `json_schema=` (`ingest.py:236`) and ingest validates nothing against it, reading `data.get("triples")` at `:295`. *v3 draft claimed `additionalProperties: False` rejects them — an outcome the code does not provide (dev read 1, B2, executed).* v3 does not add validation: a provider that ignores the schema is the BYO contract, and row 1 already states the consequence | the existing paths; **a CONTROL asserts extra keys are processed today**, going red the day ingest validates |
| 7 | MIXED content — legitimate facts AND an instruction in one event | the facts store; only triples matching a declared instruction are refused. **A mixed event must not lose its declarative facts** | V-NO-COERCED-DISPOSITION's mixed-event case |
| 8 | the UNPARSEABLE branch | `instructions_dropped: 0`, **present in the early-return dict** (`ingest.py:261`) — on the one path that never parsed a response, an absent key is not a zero | V-COUNTER-INVENTORY (`test_0025_enforcement.py:312`) |

**ROW 1 IS THE ONE THAT BOUNDS THIS SPEC**, and it is stated here rather than
discovered at round 2. The enforcement relates a triple to a DECLARED
instruction; a provider that coerces without declaring is not reached, and that
is today's behaviour — the current prompt has no `instructions` field and 31/66
were coerced anyway. Making the rule model-independent would require deciding
that a triple's content *is* an instruction without the model saying so, which
is the free-text detection problem **Q6 retired on measured evidence** (the
carriers hold reported speech; an imperative-shape rule scores 6.4% on real
episode summaries). This spec does not walk back into it.

So the claim §2b may make is bounded, and v3 states it in these words: **no
DECLARED instruction becomes a disposition fact, and the rate at which the
extractor coerces WITHOUT declaring is measured, stated and reported.** The
stronger claim — *no instruction becomes a disposition fact* — is R1-1 again in
a new place, and research would have written it had it not been specifying row 1.

## 3. Trust-class matrix — REQUIRED, blocking

Unchanged. This spec emits **fewer** records and weaker claims; it upgrades
nothing. An episode that previously asserted an action now reports a statement —
strictly less assertive. A triple that previously asserted a disposition is now
absent.

## 6. Invariants and executable checks — REQUIRED, blocking

| id | invariant | check | test node |
|---|---|---|---|
| **V-NO-FABRICATED-ACTION** | no bare instruction is stored as an episode asserting performance | the frozen 66 through the PROPOSED prompt: **0/66**, against the manifest's `recorded_as_completed_action` baseline. **The completed-performance decision is the FROZEN ORACLE (§6b), not a regex** | `tests/test_0038_harness.py::test_no_bare_instruction_is_stored_as_a_completed_action` |
| **V-NO-COERCED-DISPOSITION** | no **DECLARED** instruction becomes a disposition fact | a response carrying both carriers: the triple is refused, `instructions_dropped` counts the REFUSAL. **Bounded by §2c row 1 — a provider that coerces WITHOUT declaring is not reached**, and V-SILENT-COERCION-MEASURED reports that rate rather than this invariant claiming it | `test_0038_instruction_enforcement.py::test_both_carriers_the_disposition_is_not_stored` + `::test_both_carriers_the_report_counts_the_dropped_instruction` |
| **V-EVENT-RETAINED** | dropping the triple does not drop the event | the scripted both-carriers case retains its episode (node 1); **across the frozen 66, every text still yields exactly one episode** (node 2, the harness) | `test_0038_instruction_enforcement.py::test_both_carriers_the_event_is_retained_as_one_episode` + `tests/test_0038_harness.py::test_every_frozen_text_yields_exactly_one_episode` |
| **V-THIRD-PARTY-UNTOUCHED** | `prompts.py:41`'s third-party rule is unchanged in behaviour, **and the refusal never eats a receipt** | the 0001 and 0023 third-party tests by NODE ID, not "the existing suite" — P4 wants ids, and "passes unchanged" over an unnamed set is a claim nobody can re-run. **Plus the pair that proves the exemption is keyed on the RELATION and not the author:** a `third_party_claim` restating a declared instruction is KEPT; a user-disposition triple restating one is REFUSED **on the same third-party event**. Mutant: key the exemption on the author — the second case wrongly survives | `tests/test_0038_instruction_enforcement.py::test_third_party_claim_receipt_is_exempt` + `::test_user_disposition_on_a_third_party_event_is_refused` |
| **V-NO-PROCEDURAL-IN-PROMPT-VOCAB** | §1a's cause B holds: the vocabulary handed to the extraction prompt carries no procedural relation | assert on `render_prompt_relations(reg)` (`ingest.py:204`) that no rendered relation has `relation_kind="procedural"` — **on the KIND, never on names or descriptions**. Reuses 0037's V-EXTRACTOR-BLIND rather than restating it. *v1 asserted "no relation in the registry denotes a practice", which is FALSE TODAY on descriptions (`has_diet`: "dietary practice or restriction") and would fail the day 0037 ships `follows_procedure` while §2b stayed correct — and research "verified" it with a hand-made set of practice-words, a hand-maintained list inside the check written to remove one.* Mutant: assert on names or on the registry rather than the rendered vocabulary | — |
| **V-INSTRUCTIONS-WELL-FORMED** (§2c rows 3-4) | a member that is non-string or empty/whitespace is DROPPED and NOT COUNTED; duplicate members are de-duplicated before comparison; `instructions_dropped` counts **REFUSALS, never DECLARATIONS** | three declarations of one instruction against one coerced triple gives the counter **1**, not 3; an empty-string member moves it by **0**. **Mutants: count declarations (the figure stops meaning "records prevented" and starts meaning "things the model said"); count malformed members (malformed input inflates the one number this spec's acceptance turns on)** | `test_0038_instruction_enforcement.py::test_row3_malformed_members_are_dropped_and_not_counted` + `::test_row4_duplicates_count_one_refusal` |
| **V-SILENT-COERCION-MEASURED** (§2c row 1) | the residual this spec does NOT close is measured, not asserted away | the 66 through the proposed prompt: count triples carrying instruction content with **no** `instructions` member. **A FIGURE, NOT A THRESHOLD** — it has no pass condition, because a pass condition would be a claim about model compliance that no mechanism here enforces. It is reported in §8 beside the enforcement's rate | `tests/test_0038_harness.py::test_silent_coercion_residual_is_reported` |
| **V-COUNTER-INVENTORY** (INHERITED from 0025 §4c — not restated) | `instructions_dropped` is present on **every** return path, including the unparseable early return | `tests/test_0025_enforcement.py:290,312,330` — the exact-set assertion at `:330` is what makes the hand-listed `PUBLIC_COUNTERS` safe; 0038 adds one key to three sites (the normal report, `ingest.py:261`'s early return, and the tuple) and two existing tests catch a missed one | `test_0038_instruction_enforcement.py::test_row8_unparseable_branch_carries_the_counter_at_zero` |
| **V-NON-REGRESSION-CHARACTERISED** | the 412-text capture's non-fabricating summaries do not silently degrade | diff before/after; the change must be a **named class**, not merely small (§6a) | — |

### 6a. Acceptance measurement — REQUIRED, FINITE

**THE CORPUS LIVES IN THE REPO AND IS BOUND BOTH WAYS.**

  `tests/eval/extraction_speech_act/MANIFEST.json`   — research-authored, byte-copied by dev
  `tests/eval/extraction_speech_act/bare_procedural_66.jsonl`     — the acceptance set
  `tests/eval/extraction_speech_act/capture_412.jsonl`            — the non-regression set

The manifest's sha256 is carried on **one** line of this spec:

```
corpus sha256: 5d0533375b0328317860840ec35fccab1d7ea88e5310de07c0daf70e6169f445
```

and the manifest carries `spec_version` and
`spec_text_sha256_excluding_the_corpus_digest_line` — the spec's text with that
single line removed. **A bidirectional, non-circular binding**: the spec pins
the corpus by digest, the corpus pins the spec by version plus the digest of
everything except the line the digest lives on, so binding one does not move the
other. `tests/test_0038_corpus_pin.py` enforces both directions, in the shape of
`tests/test_0037_corpus_pin.py` and **including its golden vector** — the
exclusion rule is the same rule, so it inherits the same mutant: a
self-consistent WRONG rule must fail, which a digest comparison alone cannot
see. It also inherits the ROW-DOMAIN check: every row constructible through the
declared types.

*v2's version cell claimed this fold and **the body did not contain it** — §6a
still pointed at the research tree's own working directory — a peer-tree path in
backticks, with no repo path, no digest line and no pin test named anywhere.
That is 0037 round 2's B3 verbatim AND the cell-vs-carrier disagreement its
round 2 found, produced by the seat that spent the day enforcing "the file is
the artifact, the message is a summary of it". Dev's second read caught it by
grepping the body for what the cell claimed — which is the check, and it is
cheap.*

**Research owns the expectations; dev owns the prompt, the runner and the
placement.** The seat that implements does not set its own bar (0029's rule).

**V-NON-REGRESSION-CHARACTERISED is the one that needs stating carefully.** A
prompt edit can reach 0/66 by making every episode terser, passing "no movement
outside the fabricating cells" while quietly degrading 400 summaries nobody was
looking at. So the non-regression set is scored on **what changed**: diff the
non-fabricating summaries before and after, and require the change to be
**characterisable as a named class**. "Small" is not a criterion; "no change
except the removal of asserted outcomes" is.

### 6b. The frozen oracle — FROZEN; the §8 gate is NOT MET; §6b-A is (v5.5)

*(v3 moved this section: it had landed after §7, so §6 cited a §6b a reader met
later — dev read 1, N3. Sections now run 1, 1a, 2, 2c-i, 3, 6, 6a, 6b, 4, 3b, 5,
9, 7, 8, 10; the guarded-surface sections restored by R1-6 keep their reviewer-
named numbers rather than being renumbered into sequence.)*

Round-1 R1-2 asks for *"a defined rule or frozen oracle for deciding whether an
episode asserts completed performance"*. **v4 stated a rule and said honestly
that it was not validated. It now is, and this section states what was run
rather than what was intended.**

#### THE ORACLE — a REGISTRY, not a rule

`proposals/0038-oracle-labelling/verb_registry.py`, **published sha16 `5c37d57159ffa624`**, rulings sha16 **`af7823c7ac15152f`** *(method: `ast.unparse` of the parsed
`VERB_REGISTRY` tuple, SHA-256, first 16 hex — **stated because the manifest
computes the same CLAIM by a different method (canonical JSON of the parsed
tuple) and gets a different number. A digest without its method is not
reproducible, and two numbers for one claim read as a contradiction unless both
say how they were made.** The claim itself — that the research-tree and
published tuples are EQUAL — was verified by direct comparison in both seats,
which is stronger than either digest.)* (v2), frozen at `VERB_REGISTRY_FREEZE_v2.md`; corpus
pinned at `a239b296d126ca78` and checked at import. **31 ordered entries,
TOTAL IN BOTH DIRECTIONS with an import-time gate** — every episode must match
a ruling and every ruling must match an episode, the shape `schema.py` uses for
`DISPOSITIONED_REASONS` / `AS_OF_DISPOSITION` / `NAMES_A_SUCCESSOR`.

**v4's "derived rule" is superseded, and the reason is the point.** That rule
keyed on the *instruction's* verb appearing as the episode's main finite verb —
and v4's own table shows it losing to the regex on `ran` (irregular past) and
`copied` (`-y → -ied`), which is surface matching failing at exactly the place
surface matching fails. **The registry keys on the EPISODE's verb form and
disposes each one explicitly**, so an unseen form fails the import instead of
being silently mis-scored.

**THE RULING PRINCIPLE, stated so a reviewer can attack it:** *the disposition
follows what the episode asserts about the user's relation to the action; a
reporting frame does not change the content it reports.* "stated a **preference**
to X" is REPORTED; "stated an **intention** to X" is COMMITTED; "stated a
**practice** of X" is PERFORMED. The same "stated" opens all three and settles
none.

**THREE dispositions, because deciding and doing are separate acts.** Over the
66 corpus **EPISODES**: `PERFORMED` 21 · `COMMITTED` 22 · `REPORTED` 23. *(The
registry's 31 ENTRIES divide differently — performed 15, reported 12,
committed 4 — because one entry can rule many episodes. The two counts sit near
each other and must not be read as one.)* **`V-NO-FABRICATED-ACTION`
fires on `PERFORMED` ONLY** — an episode reading *"the user decided to X"* over
a bare instruction still fabricates a dated decision, but it is not a fabricated
*performance*; `COMMITTED` is measured and reported, never folded into "fine".

#### THE §8 GATE IS **NOT** MET — AND THIS SPEC NO LONGER CLAIMS IT IS (R2-1)

**`paper2/freeze/VALIDATION_GATE.md` §1 requires a BLIND human labeller** —
and the frozen document itself travels with this package as
**`VALIDATION_GATE-pseudonymised.md`**, a DERIVED copy. ***Its fidelity is NOT
independently verifiable from this package, and the claim is narrowed to say so
(R3-3):*** the copy records the frozen original's sha256 and the single
substitution applied, but **the original's bytes are absent**, so a reader
cannot prove the copy differs *only* by that substitution. **The package
contains a bound derived copy and CANNOT independently establish byte-level
fidelity to an original it does not carry.** Shipping the original would
publish the owner's name in the RATER role his 2026-09-07 ruling covers, and an
attestation would be a promise rather than a proof — **so the claim shrinks
instead of the evidence growing.** —
*"intended labels stripped, items shuffled … opaque ids assigned after
shuffling"*. **No blind human leg exists in this oracle's category scheme.**

- **Run 1 WAS blind — and cannot be scored against this gate's classes.** Its
  answer space was *performed / reported / neither*; it has **no `committed`
  category**, because `COMMITTED` did not exist until the registry did. The
  gate's classes are performed/committed/reported, so run 1's labels are not
  comparable to the model's and **the blind leg is not merely disqualified by
  drift — it is uncomputable on these classes.**
- **Run 2 was RUBRIC-APPLIED AND NOT BLIND**, disclosed in those words.

> ***THE §8 GATE OF `VALIDATION_GATE.md` IS NOT SATISFIED. ITS HUMAN CONDITION
> IS UNMET, AND NOTHING BELOW SUBSTITUTES FOR IT.*** *v5.4 said the gate
> "PASSED … with a named deviation". **That was wrong: naming a deviation from
> a mandatory condition does not satisfy it, and "not waived" makes the claim
> worse rather than better. Disclosure is not compliance.** The external
> reviewer named this at round 2 (R2-1) and is correct.

#### §6b-A — THE ORACLE ACCEPTANCE RULE FOR 0038, EXPLICITLY WEAKER (v5.5)

**This is a NEW rule, local to 0038, defined because the frozen gate cannot be
met with the raters available. It borrows the gate's STATISTIC and none of its
authority.**

**Legs, named for what they are:**

1. **One BLIND rater — and it is a MODEL, not a human.** `gpt-4.1`, temperature
   0, cross-family, 74/74, 0 unparsed. **Blind by construction and the
   blindness is TESTED** (AST assertion; three leak mutants kill it).
2. **One RUBRIC-APPLIED HUMAN rater, not blind**, with **intra-rater
   consistency measured directly** — 8 hidden repeats at ≥20 cards' separation,
   **8/8 consistent**, which is what run 1 lacked and drifted for.

**Thresholds — the gate's statistic, applied to weaker legs:** per-class
one-vs-rest Cohen's κ between the two raters ≥ **0.60** with n ≥ **10**, every
class required; **plus** the oracle must exceed the inter-rater ceiling
**against the BLIND rater alone**.

**`n` is the class size under the MODEL's labels** (the blind leg; they sum to
66, the whole corpus), because one-vs-rest κ needs its class defined by a named
rater and the blind one should define it.

| class | n (model's labels) | κ (human vs model) | vs 0.60 |
|---|---|---|---|
| performed | 22 | 0.857 | met |
| committed | 24 | 0.804 | met |
| reported | 20 | 0.728 | met |

**Ceiling: registry v1 ↔ model κ 0.909 exceeds the human↔model ceiling of
0.795 — on the blind leg alone.** Met.

**§6b-A IS MET. THE §8 GATE IS NOT.** The two are not interchangeable and this
document must never again let the second borrow the first's name.

#### THE EVIDENCE SET CARRIES ITS OWN DISPOSITION (R3-1)

**A retraction in this document is not a retraction in the artifacts this
document BINDS.** Round 3 found that after §6b withdrew the gate claim, the
bound evidence still asserted it — *"THE §8 GATE — PASSES"*, *"two independent
raters"*, *"Nothing to pass"* — so **a reader following the evidence reached the
conclusion the spec had withdrawn.**

**`SUPERSEDED-CONCLUSIONS.md` is the set's CURRENT DISPOSITION**, bound by the
manifest like every other file: where any file in the set disagrees with it,
**it is current and that file is a historical record of a run.** Two write-ups
carry supersession headers; the disposition carries the withdrawn phrases, the
markers, the declared exemptions and the declared header-governs records **as
JSON**, in `known_foreign_digests`' shape — because **an exemption in prose is
an exemption nobody can check.**

**`tests/test_oracle_set_disposition.py` reads the disposition's JSON and holds
the marker-or-exemption rule over every file in the oracle set;
`lint_withdrawn.py` itself still reads none of the set's files — a test inside
its selection reaches them by reading the JSON.** The distinction is load-bearing
and is not tidied away here: **what changed is reach, not the gate's coverage.**

**The check's own limits are recorded in the disposition rather than left to be
discovered.** Every file in the set that currently carries a withdrawn phrase is
either declared exempt or a declared header-governed record, so **nothing in the
present set reaches the paragraph rule**: the central property is exercised by
the check's negative controls — the discarded assembly's own `owned_elsewhere`
block and its to-do sentence, both embedded verbatim — and not yet by the set.
***"It holds over the set" and "it fired on the set" are different claims, and
only the first is true.*** A check standing guard over a future edit is a
legitimate thing for a check to be; a check described as more than that is how
this round's defect was made in the first place.

***`RUBRIC.md` is NOT amended, deliberately.*** It is the instrument the rater
was **shown**; amending it would make the record of the run false, and a reader
could no longer establish what the rater was told. **It is evidence FOR the
circularity §6b-A concedes** — the rubric gave the rater the registry's own
principle and the run was then scored against the registry. **A record amended
to agree with a later conclusion is no longer a record.**

#### WHAT §6b-A CANNOT SUPPORT — the cost of the weaker rule, stated

- **No claim of human-independent validation.** The human leg applied the
  registry's own rubric to score the registry; registry↔human κ 0.840 is
  **partially circular** and is not offered as validation.
- **No claim that a human, unaided, reproduces the oracle.** Run 1 is the only
  evidence bearing on that and it drifted.
- **The strongest honest claim is the BLIND MODEL leg's**, and every argument
  above rests on it alone.
- **What would close the gap:** a blind human labelling by a rater who has not
  seen this corpus. **The project's one human rater has now labelled it twice
  and knows which class was disputed**, so blindness is unavailable from that
  seat — form without substance, the same error as the "named deviation".
  Closing it needs a different person, and 0038 does not claim to have one.

#### THE EVIDENCE SET — ONE PIN, THE MANIFEST CARRIES THE REST

The fifteen files a reviewer needs to verify any κ ship in the repo at
`tests/eval/extraction_speech_act/oracle/`. **This spec pins ONE digest — the
manifest's — and the manifest carries every file's.** Fifteen digests in prose
would be fifteen things going stale independently, which this document has
already demonstrated twice today at a smaller scale.

oracle manifest sha256: 33ecc3f2149d6f58031b22546e56655b8af02332c9a019cc39df2e13af344019

**The binding is bidirectional and neither direction depends on the other's
token** (the corpus pin's protocol): the line above is `sha256(MANIFEST.json)`;
`MANIFEST.json` carries `spec_text_sha256_excluding_both_pin_lines`
(renamed from `…_excluding_the_oracle_manifest_line` at round 2: **the key said
one line and its value was two**, and a name narrower than its content is how a
later editor "corrects" the computation to match the name), with the removed
prefixes carried beside it as `excluded_lines` DATA the pin test asserts —
computed over this spec's text with **BOTH column-0 pin lines removed — the
oracle manifest line AND the corpus `corpus sha256:` line, line plus terminator,
exactly one of each asserted.**

***Why BOTH, and why the order is forced.*** This document carries **two**
single-line pins, and two such pins are **mutually dependent** unless one
exclusion covers the other: the corpus pin's exclusion (0037's rule, inherited
verbatim and **left untouched**) removes only its own line, so if the oracle
line were set *after* it, the corpus manifest would already have committed to a
text that then moved. **The oracle pin therefore excludes BOTH lines and is set
FIRST; the corpus pin excludes only its own and is re-pinned SECOND** over the
final oracle line. Verified by simulation in both seats: in this order all four
bindings hold from the final text alone, and **in the reverse order the corpus
pin breaks** — which is the whole reason the order is a rule and not a habit.

A regex using `\s*` over-deletes, because `\s` matches a newline; that is the
corpus pin's own hard-won rule and it applies to both lines unchanged.

**§6b names the evidence files by FILENAME, not by digest**, deliberately —
`RUBRIC.md`, both `VERB_REGISTRY_FREEZE` docs, `model_pass_0038.py`,
`oracle_labels_human_1.json`, `verb_registry.py`. The pin test binds them from
**both** sides: every filename named here must be a manifest entry, **and**
every 16-hex token in this document that equals some manifest file's digest
must be that file's **current** one. **One direction catches a citation of a
file that moved; the other catches a wrong digest for a file that did not.**
Digests in this document that name **non-public** artifacts — registry v1
`7862ab9b1b9f49cb`, the round-1 verdict `3f5d96e0cd2df90c`, the rulings digest
above — are untouched by either direction and are not manifest entries.

#### WHEN EACH RULING WAS WRITTEN, RELATIVE TO THE RUNS IT SCORES

*(A registry that is not a pre-registration must say where in the sequence it
sits, or "frozen before scoring" is unfalsifiable. Dev's ask; the order is
checkable from the freeze docs' own timestamps.)*

| # | event | artifact / digest |
|---|---|---|
| 1 | **human run 1** — blind, 66 items, 3-way | `oracle_labels_human_1.json`; **the registry did not exist** |
| 2 | run 1 scored against the shipped regex key | κ 0.652 — later found to average two policies |
| 3 | **registry v1 RULINGS WRITTEN** — after run 1 and the key were seen | `verb_registry.py` |
| 4 | **v1 FROZEN, 2026-09-07T15:25:54Z**, sha16 `7862ab9b1b9f49cb` | `VERB_REGISTRY_FREEZE.md` — **before any agreement against it was computed** |
| 5 | **human run 2** — rubric-applied, 74 cards, 8 hidden repeats | scored against **frozen** v1 |
| 6 | **model leg** — gpt-4.1, temp 0, blind by construction | scored against **frozen** v1 |
| 7 | **the §8 gate computed and PASSED** — human vs model | does not involve the registry at all |
| 8 | **registry v2** — published `5c37d57159ffa624`, rulings `af7823c7ac15152f` | two carries, each settled by the run at step 5–6, **not** by re-reading |

**What this table concedes:** steps 3–4 sit **after** step 1, so v1's rulings
were authored by someone who had seen a set of human labels and the key. **That
is why no agreement figure against the registry is offered as a validation** —
the gate's statistic is step 7, human vs model, which the registry does not
enter. **What the table establishes is the narrower claim actually made:** the
rulings were fixed at step 4 and every number scored against them comes from
steps 5–7.

#### THE DRIFT TEST — its exact null, since p = 0.00007 is otherwise a bare number

**It is not a comparison of two distributions.** It is a single **exact
combinatorial null** over one class:

- **class:** `decided to`, n = 19 — the rater labelled **6** performed, **13**
  reported.
- **null:** the labels are **exchangeable across presentation positions** — that
  a rater applying one policy shows no relationship between label and where the
  card fell.
- **statistic:** *perfect positional separation* — every `performed` before
  every `reported`, or the reverse.
- **p:** exactly **2 / C(19,6) = 2/27132 = 0.0000737**. The `2` counts both
  directions; `C(19,6)` is every ordering of those labels.

**And the same test is what DISMISSED a second apparent separation:** the
`asked for / requested` class separated too, at **1 vs 3**, where
p = 2/C(4,1) = **0.5**. A pattern that occurs half the time by chance is not a
finding, and the p-value is what told the two apart — the raw pattern looked
identical.

#### DISCLOSURES — read before trusting any number above

- **The registry was authored after the first human leg and the key were seen.**
  It is **not** a pre-registration in `VALIDATION_GATE.md`'s sense. What is
  claimed and recorded is narrower: the rulings were frozen **before** any
  agreement was computed.
- **The second human run was NOT blind** and is recorded as not blind — the
  rater already knew which class was disputed, and `RUBRIC.md` states the
  registry's own ruling principle. **It therefore does NOT establish
  independent agreement** — the rater applied the registry's principle to score
  the registry, which is **partially circular**, and "independently" is the one
  word that cannot be used of it. What it establishes is narrower: that the
  principle, once written down, is applicable consistently — which is why run 2
  shows no drift where run 1 did.
- **Run 1 drifted and that is why run 2 exists.** The rater's policy on
  `decided to` changed once mid-run and never changed back — **perfect
  positional separation, p = 0.00007** — so run 1's κ 0.652 averaged two
  policies and was never a single measurement. Run 2 carried **8 hidden
  repeats** at ≥20 cards' separation: **8/8 consistent, no drift**, model 8/8
  likewise at temperature 0.
- **`AMBIGUOUS` was chosen 0 times in 74 by BOTH raters**, with the rubric
  stating explicitly that flagging one is a finding rather than a failure.
  **The consequence, which is why it is here: every card received one of the
  three labels, so NO item was excluded from the κ table** — the per-class n
  sum to 66, the whole corpus. A scheme that forced exclusions would make the
  κ figures cover a subset chosen by the raters.

#### THE CONTESTED RULING — carried as a disagreement, not settled

**`stated a practice of/to` ⇒ PERFORMED.** The model agreed 3/3; the human
dissented 3/3 (2 reported, 1 committed). **2–1, so it stands — and a rater
disagreeing on every instance is what a genuine boundary case looks like.** It
is named here rather than left for the reviewer to find. Its counterpart moved:
**`asked for` was REPORTED in registry v1 and is PERFORMED in v2**, because v1
contradicted itself — `announced` was PERFORMED on the reasoning that
*announcing IS the act when the instruction was to announce*, and `asked for`
was REPORTED on reasoning that would have made `announced` REPORTED too. Human
and model both said PERFORMED. **v4's own §6b table had already called this one
correctly** *("the regex's hand list lacked `asked`")*, and registry v1
regressed it.

#### WHAT THE 19/66 BASELINE IS NOW

Still a **frozen baseline, not a validated rate**, and this spec still does not
treat it as one — the registry scores `PERFORMED` on 21/66 and the two
instruments are not interchangeable. 0037 §8 cites the baseline in those terms
and stays correct.

## 4. The field-consumer table — REQUIRED (guarded surfaces)

`prompts.py` and `ingest.py` are both in `GUARDED` (`check_spec_reference.py:51-53`
— "disclosure routing at write time"), so the full-path sections are required and
v2 omitted them (round-1 R1-6).

| field / surface | who writes it | who READS it | reachability |
|---|---|---|---|
| `instructions` (extraction JSON) | the BYO extractor, per the prompt | `ingest.py` only — read, compared against triples, **never persisted** | not a stored field; no schema version, no export, no migration |
| `instructions_dropped` (report) | `ingest.py`, both return paths | **`Memory.remember`'s caller ONLY.** The MCP tool result **STRIPS it** with the other extractor counters (`_OPERATOR_ONLY`, `mcp_server.py:186`, popped at `:212`) — 0031 §4d's argument: a model that learns how often its coercions are refused learns to shape them, and a refusal count is that readout more directly than the counters it sits beside. Telemetry untouched (`remember` builds its fields explicitly). *v3's row named the MCP result as a consumer; it is not one. The row was written to answer R1-6's demand that consumers be enumerated MECHANICALLY, and research enumerated by reading the shape of the data instead of the code that handles it — the same defect, in the section written to prevent it (dev, adversarial diff-scan, 2026-09-07).* | operator-only by construction: the strip is a tuple a test pins, so surface and spec cannot drift silently |
| the refused triple | — | nobody: it is never constructed as an `Edge` | the refusal is at the pass-1 filter (`ingest.py:295`), before persistence — the same site as `n_invalid` |

**Reachability evidence.** Every path that returns an ingest report is one of the
two dicts (`ingest.py:261` unparseable, `:449` normal); `PUBLIC_COUNTERS`'
exact-set assertion (`test_0025_enforcement.py:330`) proves there is no third.

## 3b. Authorization — REQUIRED

**No authorization decision keys on any of this.** The refusal is content-shaped,
not principal-shaped: the same response from the same provider refuses
identically for every user and every principal. `instructions` is never stored,
so no disclosure class attaches to it and `_disclosure_for` is untouched. The
counter carries no content — a count, never a string — so a report crossing a
scope boundary leaks nothing the response did not already contain.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| provider follows the schema, declares and does not coerce | unchanged from today; counter 0 |
| provider declares AND coerces | the triple is refused, counter 1 — **the case the rule exists for** |
| provider coerces WITHOUT declaring | **unchanged from today** — §2c row 1; the residual, measured by V-SILENT-COERCION-MEASURED |
| provider ignores the schema | unchanged: bare array normalised, prose unparseable |
| a host running its own prompt | inherits none of this — BYO is the contract and §8 says so |

## 9. Brief for the external reviewer

**The two seams to attack hardest: §2c row 1**, because it is where this spec
stops and we would rather you tested the bound than discovered it; **and §6b's
frozen oracle**, because the completed-performance decision is the one judgement
every acceptance figure rests on. **The `VALIDATION_GATE.md` §8 gate is NOT
MET and this spec does not claim it is** — its human condition requires a blind
labeller, no blind leg exists in this oracle's classes, and **naming that as a
deviation does not satisfy it** (R2-1; the reviewer was right and v5.4 was
wrong). **What IS met is §6b-A**, an explicitly weaker rule defined in this
document: one BLIND rater that is a MODEL, one RUBRIC-APPLIED human, the gate's
statistic on weaker legs, and the ceiling cleared on the blind leg alone. So
the question has moved, and here is where we would aim you:

- **The `stated a practice ⇒ PERFORMED` ruling is CONTESTED and we say so.**
  The cross-family model agreed 3/3; the human rater dissented 3/3. It stands
  2–1 and it is not settled. **If one ruling in the registry is wrong, our
  prior is that it is this one.**
- **The second human run was NOT blind**, because the rater already knew which
  class run 1 had disputed. It shows the *principle* reproduces the registry's
  rulings when applied **consistently** — NOT independently, since the rubric
  states the registry's own principle and the rater knew the disputed class.
  Weaker than a blind pass, and stated as weaker.
- **The registry was authored after the first labels and the key were seen.**
  Not a pre-registration. What we claim is only that the rulings were frozen
  before any agreement was computed.
- **The ceiling bounds us, not only the oracle.** Human↔model κ is **0.795**;
  the oracle beats that against both raters. **No tightening of the oracle
  could be validated by these raters** — if you think it should be tighter, the
  instrument to attack is the rater pair, not the registry.

*(v5. **WITHDRAWN wording:** v4's brief said the decision was "not yet
independently labelled". It is,
and §9 is the section a reviewer reads first — the same site where 0028's brief
carried a stale round for two rounds running. Found by sweeping the NOUN
"oracle" over the whole file, not the phrase that had been corrected.)*

## 7. Failure modes and reversibility

**PROSPECTIVE ONLY — this cures nothing already stored** (dev's F6). Every store
that has run the shipped prompt holds fabricated episodes and coerced
disposition edges **today**, and a prompt change does not reach them.

- **Existing records are untouched.** No migration, and deliberately none: a
  migration would have to classify stored text to decide what to rewrite, which
  is the same inference that produced the defect.
- **A host that wants them out re-ingests**, or revokes the source under 0022 —
  both existing, governed paths.
- **Reversible.** Restoring the prior prompt restores the prior behaviour; the
  `instructions` field becomes unused rather than invalid.
- **No stored byte changes** on adopting this spec. The schema change is to the
  extraction JSON, which is transport between the host's model and the store.

## 8. Claims and limits

**The frequency in production is unknown and this spec does not estimate it.**
The corpus is adversarial and constructed — bare imperatives about unsafe
practices. 29% is the rate *on that corpus*, and must not be quoted as a
production rate.

**BYO is the contract.** A host supplies the extraction model, and this spec
governs the **reference prompt** veracium ships, not what any distiller does.
A host running its own prompt inherits its own speech-act discipline.

## 10. Open questions

1. ~~Does 2b's drop want a disclosure?~~ — **CLOSED, not open** (round-1 R1-4). §2b answers it: `instructions_dropped` is the disclosure, and v2 contradicted itself by saying so in §2b while this question still called it deliberately unspecified. **The contract, stated once and on every carrier:** the counter is present on EVERY return path including the unparseable early return (V-COUNTER-INVENTORY), it counts REFUSALS not declarations (V-INSTRUCTIONS-WELL-FORMED), and it is exposed at **`Memory.remember`'s return value and NOWHERE ELSE** — the MCP tool result **STRIPS** it with the other extractor counters (`_OPERATOR_ONLY`, `mcp_server.py:186`), on 0031 §4d's reasoning that a model learning how often its coercions are refused learns to shape them. *v3 said "wherever the ingest report already goes … and the MCP tool result": the report does not reach a tool caller intact, and this counter is operator-only.* **It is NOT added to logging or telemetry**, which have their own surfaces and their own review; a counter that appears in four places by default is four contracts nobody wrote. *(v2 named this as open while §2b called it answered — the section-vs-section class, in the spec whose previous fold fixed two of those.)*

2. **Does the episode rule generalise beyond instructions?** The capture only
   probed procedural inputs. Whether declarative inputs also gain unsupported
   speech acts is unmeasured, and the 412-set can answer it.

## Reviewer checklist

- [ ] every claim in §1 is reproducible from the frozen corpus, not from prose
- [ ] the fix is in the RULES block beside the third-party rule **AND the episode field's own description changes in the same commit** (F5 — a rule contradicting the field's description leaves the model two instructions; v1's checklist said "not in a field description" and survived the F5 fold)
- [ ] 2b DROPS rather than coerces, and no new relation is introduced
- [ ] the non-regression set is scored on **what changed**, not on what stayed
- [ ] no production frequency is claimed anywhere

## Retrospective — the security-hotfix exception, discharged

*Written by dev 2026-09-08, six days before the deadline the exception
carried. PROCESS §3b: a fix for a live user-affecting defect ships first and
the spec goes for retrospective external review, with that fact recorded in
the spec; the carve-out carries a deadline because a deadline is what keeps
it a carve-out rather than a door. This section is the record the carve-out
requires and the judgement it asks for.*

**What shipped ahead of review, and on whose word.** The ingest enforcement
— a declared instruction is filed, never stored; a triple restating it is
refused and the refusal counted — landed on main at `d59592d` (2026-09-07
12:09 UTC) under `Spec-Exception: security-hotfix` with
`Spec-Retrospective-Due: 2026-09-14`, on the owner's authorization recorded
verbatim in the ledger the same day (*"I am authorizing the 0038 ingest
enforcement under the security-hotfix exception by 09/14/2026"*). The reason
trailer named the measured defect: fabricated completed-actions at 29% and
coerced dispositions at 47% of bare procedural inputs over the 412-text
capture, carried under intact provenance into model context.

**Was the precondition met?** Yes. The carve-out is for a *live
user-affecting defect*, and this one was measured, not hypothesised (§1): a
user's instruction was being stored as a fact the user holds or an act the
user performed, rendered into model context exactly as any true record would
be. The fix was prospective and contained — three files, one new extraction
field, one refusal counter — and reversible by revoking the change.

**Was the review retrospective in fact?** Yes, and narrower than the word
implies. The round-1 package (pin `622bcd1c`, 04:58 UTC) went out SEVEN HOURS
BEFORE the enforcement landed; its R1-1 — *"the claimed structural prevention
is not enforced — `instructions` is optional and an extractor may emit it AND
a disposition triple"* — is the finding the enforcement answered. So the
hotfix was not a bypass of review; it was the fix a review in flight had just
asked for, shipped while the round was out. Rounds 2, 3 and 4 then reviewed
the SHIPPED code: between `d59592d` and the acceptance fold `1f1cf53` there is
no commit touching `ingest.py`, `prompts.py` or `mcp_server.py` — measured by
`git log d59592d..1f1cf53 -- <the three files>`, empty. Accepted at round 4
on 2026-09-08 01:37 UTC; released in 0.20.0 the same day with the
who-should-take-this-build line the release rule requires.

**What the review found, and what it did not.** Every finding after the
landing was about the EVIDENCE, not the code: R2-1 (the spec said the §8
validation gate PASSED while its mandatory leg was not met), R3-1 (the
retracted gate claim surviving in bound evidence), R3-2 and R3-3 (a
re-implemented validator; a completeness claim narrowed by the reviewer's
words). No round returned a defect in the shipped enforcement, and the code
the reviewer accepted is the code that shipped. The exception therefore cost
nothing in product behaviour that the review would have changed; it cost the
process the ordinary certainty that acceptance PRECEDES exposure, and that
cost is the point of recording it here.

**Two observations for the process, neither a finding against this spec.**
(1) The trailer is machine-checked for presence and format
(`specs/check_spec_reference.py`), but nothing checks that the retrospective
was WRITTEN by the date: the obligation discharged here was tracked in a
coordination file and a session's memory, not by a gate. A check that every
`Spec-Retrospective-Due` in history has a discharge recorded in its spec on
or before the date would close that, and is proposed rather than built here.
(2) "Shipped while the round was out" is a variant of the carve-out the
process text does not name: the review had already begun, so the exposure
window was hours, not the weeks a fresh review would take. It was the right
call for this defect; the record should say it was that variant.

**Judgement.** The carve-out was warranted, its precondition was met, the
retrospective review happened and accepted the shipped code unchanged, and
the deadline was met with six days to spare. Discharged.

## Review closure

<!-- GENERATED:review-closure -->

**0 internal round(s) and 4 external round(s) with a returned VERDICT are recorded for `0038`; 4 package(s) were dispatched** — counted from `specs/reviews.py`, which is the source this block is generated from. A round appearing here and not there, or the reverse, is impossible by construction. **SENT rows are dispatch records, not outcomes**, and are labelled below so the two are never summed.

| round | date | findings raised (from `raised=`) | verdict (compressed) |
|---|---|---|---|
| external 1 (SENT) | 2026-09-07 | — | SENT (round-1 package 4e4053f6dad537214ef95647a00ff6f48d4b2a0fc40b5d507003c195a7ff9f01 @ pin 622bcd1c9001a0022b2f65f8845ba6a31746323f, CI 34085071354; v2 — a draft, its frozen corpus and the tests that bind it; nothing implemented) |
| external 1 (verdict) | 2026-09-07 | 7 | RETURN for amendment 0038 v2 — "the proposal addresses a real, measured defect, and its corpus is well bound"; four design blockers (R1-1 the structural prevention not enforced; R1-2 no executable checks and no frozen oracle; R1-3 the uncontrolled-input matrix absent; R1-4 the spec contradicting its… |
| external 2 (SENT) | 2026-09-07 | — | SENT (round-2 package b703710454870ae6215170fa8cdd4a6db44e84918926ddaebc1cba08cde8ece0 @ pin f89152232039f2dbf9ef2517230e6291f99c0594, CI 34159469642; v5.4 — the enforcement shipped under the owner's security-hotfix exception at d59592d, the oracle frozen, the fifteen-file evidence set pseudonymised… |
| external 2 (verdict) | 2026-09-07 | 4 | RETURN for amendment 0038 v5.4 — one blocking (R2-1 the spec said the §8 validation gate PASSED while its mandatory blind-human condition was unmet; the owner ruled option 3: the gate is NOT satisfied and a weaker rule §6b-A is defined) and three required corrections (R2-2 the digest-token check str… |
| external 3 (SENT) | 2026-09-07 | — | SENT (round-3 package ac8cf169936cc6f50e58c62c570317d5e64e945aac3458a0319541638fe19369 @ pin a03d25d5f415fb0d8a77f2af9f7e402f64e5c9aa, CI 34168036384; v5.7 — a v5.6 commit d07043d preceded it and was superseded before sealing: its §9 opened on a sentence fragment left by a replacement span, and its … |
| external 3 (verdict) | 2026-09-07 | 3 | RETURN for amendment 0038 v5.7 — one blocking (R3-1 the spec retracted the gate claim but the bound evidence set still asserted it: two run write-ups, the rubric, the registry's own changelog) and two required corrections (R3-2 the planted-digest control re-implemented the validator instead of calli… |
| external 4 (SENT) | 2026-09-08 | — | SENT (round-4 package eccfada2950b3ec33dcc137fa3c0751f323556fc359f41a70ee54ae071edd8e9 @ pin 8588e558ede0ce1989aec2ab421274187c690914, CI 34173288704; v5.9 — the SECOND assembly: the first, 18ad6b69ebc0e4d9ddbb5a13399f0d57fb94463c48d82c95dccfad8183882df4 @ 20a7103325f32bcb5b80fc2b9ef2b8afb5ca5ab6 CI… |
| external 4 (verdict) | 2026-09-08 | 0 | ACCEPTED — "Round 4 closes all outstanding findings. I found no new blocking or required amendments." R3-1 closed (supersession headers; the manifest-bound current disposition; a shared checker rejecting silent or unmarked recurrence), R3-2 closed (one token_membership_violations validator for the s… |

**Per-finding closure ledger — PROCESS §4a.** **14 finding(s) for `0038`** — every number here is DERIVED from the rows below (external round 7, R7-1: the manifest claimed 26 while the ledgers held 31, and 0023 said 9/9 above a 10-row table); the total across the tracked specs is derived once, in `specs/STATUS.md`. Generated from `specs/closure_findings.py` and validated against `specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — extras, duplicates, wrong rounds and empty evidence all fail the build.

| finding | round | what it was | closed in | evidence (runnable) |
|---|---|---|---|---|
| **0038-R1-1** | external 1 | The claimed structural prevention is not enforced — instructions is optional and an extractor may emit it AND a disposition triple; the stored set shrinks only if the model obeys the prompt | v3 (48d0dc3): enforcement AT INGEST — a triple whose object equals a declared instruction under the comparison key is refused and counted; third_party_claim exempt (v4); shipped at d59592d under the owner's security-hotfix exception | `$PY -m pytest tests/test_0038_instruction_enforcement.py::test_both_carriers_the_disposition_is_not_stored tests/test_0038_instruction_enforcement.py::test_the_match_is_equality_under_the_comparison_key_not_containment tests/test_0038_instruction_enforcement.py::test_a_third_party_claim_survives_its_own_declaration -q -p no:randomly` |
| **0038-R1-2** | external 1 | The acceptance invariants lack executable checks; "a named class" is not a bounded pass condition; a defined rule or frozen oracle for completed performance | v3–v5.9: every invariant names its node; the oracle is a frozen REGISTRY bound by one pin with its disposition checked over the set (the §8 gate is NOT met; §6b-A, the weaker rule, is) | `$PY -m pytest tests/test_0038_oracle_pin.py::test_manifest_hashes_to_the_spec_digest tests/test_0038_oracle_pin.py::test_the_rulings_digest_matches_the_manifest_by_its_stated_method tests/test_oracle_set_disposition.py::test_the_disposition_holds_over_every_file_in_the_set -q -p no:randomly` |
| **0038-R1-3** | external 1 | The mandatory uncontrolled-input matrix is absent (§2c was prose) | v3 (48d0dc3): an eight-row matrix, one row per case with its observable outcome and enforcing invariant; each row tested | `$PY -m pytest tests/test_0038_instruction_enforcement.py::test_row1_absent_instructions_is_processed_as_today_the_residual tests/test_0038_instruction_enforcement.py::test_row2_wrong_type_instructions_is_the_unparseable_branch tests/test_0038_instruction_enforcement.py::test_row7_mixed_event_keeps_its_declarative_facts_and_refuses_only_the_match tests/test_0038_instruction_enforcement.py::test_row8_unparseable_branch_carries_the_counter_at_zero -q -p no:randomly` |
| **0038-R1-4** | external 1 | The specification contradicts itself about reporting — §2b says the counter answers Q1, §10 says the question is deliberately unspecified | v3 (48d0dc3), corrected v4: one contract — the counter on every return path of the ingest report; the MCP tool result STRIPS it with its operator-only siblings | `$PY -m pytest tests/test_0038_instruction_enforcement.py::test_both_carriers_the_report_counts_the_dropped_instruction tests/test_0038_instruction_enforcement.py::test_the_mcp_tool_result_strips_the_counter_with_its_siblings -q -p no:randomly` |
| **0038-R1-5** | external 1 | 0037 not declared as a dependency | v3 (48d0dc3): Spec-Requires 0037, with the consequence stated — §2b is correct only while V-EXTRACTOR-BLIND holds | `git show 48d0dc3 -- specs/0038-extraction-speech-act.md` |
| **0038-R1-6** | external 1 | The full-spec sections omitted for guarded surfaces (§4 field-consumer table, §3b authorization, §5 regime, §9 brief) | v3 (48d0dc3): all four restored — prompts.py and ingest.py are GUARDED | `git show 48d0dc3 -- specs/0038-extraction-speech-act.md` |
| **0038-P1** | external 1 | collected_header.json promised by the reviewer guide, absent from the package | f9379ab: the guide names both seal protocols and marks the header check not applicable to the two-seat hand-assembled chain; PIN.txt states the protocol | `git show f9379ab -- specs/REVIEWER_GUIDE.md` |
| **0038-R2-1** | external 2 | The document says the validation gate passed even though a mandatory condition (blind human labelling) was not met; naming a deviation does not make the gate pass | v5.7 (a03d25d), on the owner's ruling "go with option 3": the §8 gate is NOT SATISFIED, its human condition UNMET, nothing substitutes; §6b-A is an explicitly weaker rule that is met; the withdrawn claim registered | `git show a03d25d -- specs/0038-extraction-speech-act.md` |
| **0038-R2-2** | external 2 | The claimed digest-token check is stronger than its implementation — a stale token matches nothing and is ignored | v5.7 (a03d25d): a MEMBERSHIP test, described as one, with known_foreign_digests as data; R3-2 then made its control run the production validator | `$PY -m pytest tests/test_0038_oracle_pin.py::test_every_digest_token_beside_a_named_oracle_file_is_a_current_oracle_digest_or_declared_foreign tests/test_0038_oracle_pin.py::test_the_token_membership_check_rejects_a_planted_fabricated_token -q -p no:randomly` |
| **0038-R2-3** | external 2 | The cited validation-gate document is absent from the package | v5.7 (a03d25d): VALIDATION_GATE-pseudonymised.md in the bound set — a derived copy, the original naming the owner in the rater role his ruling covers; R3-3 then narrowed its fidelity claim | `$PY -m pytest tests/test_0038_oracle_pin.py::test_every_listed_file_is_present_with_its_digest tests/test_0038_oracle_pin.py::test_every_present_file_is_listed -q -p no:randomly` |
| **0038-R2-4** | external 2 | Editorial duplication: the §4 heading appears twice consecutively | DOES NOT REPRODUCE — the heading occurs once in the spec, the package copy and the tree copy (both seats); answered with counts in round 3 and RETRACTED by the reviewer in round 3 as a display artifact | `git show a03d25d -- specs/0038-extraction-speech-act.md` |
| **0038-R3-1** | external 3 | Current evidence artifacts still assert the withdrawn conclusion — the bound write-ups say the gate PASSES and the raters are independent; a reader following the evidence reaches the conclusion the spec withdrew | v5.8/v5.9 (20a7103, 8588e55): supersession headers on the two write-ups; RUBRIC.md deliberately unamended (the instrument the rater was shown); the registry's changelog marked; SUPERSEDED-CONCLUSIONS.md bound and current, every entry a STATE; tests/test_oracle_set_disposition.py reads its JSON and holds the marker-or-exemption rule over every file (the first assembly of round 4 was discarded when the disposition itself proved stale) | `$PY -m pytest tests/test_oracle_set_disposition.py::test_the_disposition_holds_over_every_file_in_the_set tests/test_oracle_set_disposition.py::test_the_round_4_first_assembly_disposition_fails_this_checker -q -p no:randomly` |
| **0038-R3-2** | external 3 | The planted-digest test does not invoke the production membership check — it reconstructs the allowed-set logic, so the scanner could stop inspecting paragraphs while the control kept passing | v5.8 (20a7103): one function, token_membership_violations, serves the real check and the control, which mutates the real spec body | `$PY -m pytest tests/test_0038_oracle_pin.py::test_the_token_membership_check_rejects_a_planted_fabricated_token tests/test_0038_oracle_pin.py::test_every_digest_token_beside_a_named_oracle_file_is_a_current_oracle_digest_or_declared_foreign -q -p no:randomly` |
| **0038-R3-3** | external 3 | Fidelity of the pseudonymised validation-gate copy to the absent original is not independently verifiable from the package | v5.8 (20a7103): the claim NARROWED — the package carries a bound derived copy and cannot independently establish byte-level fidelity to an original it does not carry; shipping the original would publish the name the owner ruled out | `git show 20a7103 -- specs/0038-extraction-speech-act.md` |

<!-- /GENERATED:review-closure -->
