# Feature spec: exercised guarantees — measuring whether what we specify is what runs

Spec-Status: accepted

| | |
|---|---|
| **Author / session** | research (veracium-research-48), the candidate's author → dev (veracium-61), each adoption at rest and re-read from the file, dated per entry: v3.1 2026-09-18 from `0042-exercised-guarantees-CANDIDATE.md` (sha16 28068200aa6f90fa); v4 2026-09-18 from the same file (sha16 0fd0af01bfb56a39); v5 2026-09-18 from `0042-exercised-guarantees-CANDIDATE.md` (sha16 f8cf6f68e0016625); v6 2026-09-18 from `0042-exercised-guarantees-CANDIDATE.md` (sha16 ba262106068d3efc); v7 2026-09-18 from `0042-exercised-guarantees-CANDIDATE.md` (sha16 ccf0715041f3148a); v8.1 2026-09-18 from `0042-exercised-guarantees-CANDIDATE.md` (sha16 b94d814d20b96d2c); v9.2 2026-09-18 from `0042-exercised-guarantees-CANDIDATE.md` (sha16 a230ae09793790be) — ACCEPTED at the design level, the flip on the owner's word |
| **Version** | **v12.17 — 2026-11-15: A NAMED LIMIT (marked amendment, research `82b37294`): a refusal returned as a value is no discovery kind; the eight sites at 9d73bdf4 are named in Part A-0-bis, and the census's coverage claim is unchanged.** Adopted on the owner's word, first-hand in the dev session: "Adopt both (Recommended)". **Prior:** **v12.16 — A FIGURE THAT DESCRIBES A MOVING SUBJECT, ANNOTATED.** A text annotation, research as the specification's author, after 0041 round 10 added eight declared sites (the declaration: 162 ids at `c05b709` → 170 at `aa2dd98`, from the generator's printed count, per dev). §6b's "95 of the 102 declared symbols" is kept as adopted and annotated with the figure at `aa2dd98`, read from the committed transcript. No contract, invariant or named limit changes, and `Spec-Status` stays `accepted`. **Prior cell follows.** **v12.15 — AN INDEX OF THE CURRENT CONTRACT PRECEDES THE HISTORY.** A text addition (the round-33 verdict's non-blocking suggestion, banked in the coordination repo at `f4ae522`, body sha16 `e55d6279aadec213`; the owner's word to take it). The verdict ACCEPTED round 33. A short, non-normative index now stands before the implementation notes. It points to the text in force, and lists every statement of this contract that is marked as history, WITHDRAWN or SUPERSEDED in the implementation notes and §4, naming §11 as the list of superseded decisions, so the long history is not read as current requirements. No other text changes, no frozen invariant's text changes, and `Spec-Status` stays `accepted`. **Prior cell follows.** **v12.14 — A SET IS DESCRIBED BY ITS WHOLE TABLE, OR REFUSED.** An implementation note (round 33; the round-32 verdict's correction R32-1, banked in the coordination repo at `cc7c1d3`, body sha16 `025b9b801b607091`, fixed within the round). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. Round 32 sorted a set's elements, so an order code observes was erased. v12.13's set-order bullet and two of its named limits are WITHDRAWN IN PLACE, their text kept with notes beside it. A round-33 paragraph after round 32's states the correction, the set reader it needed, the hash seed pinned where descriptions cross processes, the limits and the run. **Prior cell follows.** **v12.13 — EVERY OBJECT IS RECORDED, AND A SET'S ELEMENTS ENTER THE MAP IN AN ORDER THEIR DESCRIPTIONS DECIDE.** An implementation note (round 32; the round-31 verdict's correction R31-1, banked in the coordination repo at `85d7b70`, body sha16 `a70815f1162f6e7e`, fixed within the round). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. Round 31 exempted values from the reference map on the premise that their identity could not be state, and `is` shows it can. v12.12's value-set bullet is WITHDRAWN IN PLACE, its text kept with a note beside it. A round-32 paragraph after round 31's states the correction, a pre-existing set-order defect the correction would have widened, the limits and the run. **Prior cell follows.** **v12.12 — A READ CREDITS ONLY A FIELD SHOWN TO STORE IT, AND SHARING IS DESCRIBED ACROSS THE WHOLE CLASS.** An implementation note (round 31; the round-30 verdict's two corrections, banked in the coordination repo at `256c235`, body sha16 `d2c6905df8f8b9cf`, fixed within the round). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. Round 30 credited a value an accessor reports but does not store, and described each class member with its own reference map, so sharing between members read as no drift. The description FORMAT changed, so the INV-7 run is re-made again and the `Site`'s recorded digest moves, although the class did not. A round-31 paragraph after round 30's states the corrections, the limits and the run. **Prior cell follows.** **v12.11 — A DICTIONARY NO ACCESSOR REACHES IS REFUSED WHATEVER ITS NAME HOLDS, AND AN OBJECT'S OWN TYPE IS COUNTED ONCE.** An implementation note (round 30; the round-29 verdict's two corrections, banked in the coordination repo at `6cf78f9`, body sha16 `cda44d10f65b719b`, fixed within the round with the class each belongs to). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. Round 29's dictionary rule read an explicitly stored `__dict__ = None` as an absent name, and its residue rule discarded every referent identical to the object's type. A round-30 paragraph after round 29's states the corrections, a history-dependent limit, and the INV-7 run, re-made because the product's `src/` changed for the first time since round 8. **Prior cell follows.** **v12.10 — STORAGE IS READ THROUGH THE CLASS THAT OWNS IT, AND WHAT NO ACCESSOR REACHES IS REFUSED.** An implementation note (round 29; the round-28 verdict's one correction, banked in the coordination repo at `c178767`, body sha16 `8888d024c89724ac`, with two further members found by the second seat's stage 1, and a gap in the same class found while building the fix, all fixed within the round). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. Round 28 read each field through the first descriptor its NAME resolves to, so a subclass that shadows a base's slot, a C getset or the instance dictionary hid that storage, and a changed value read as no drift. A round-29 paragraph after round 28's states the correction and its limits; one of round 28's sentences is annotated in place. **Prior cell follows.** **v12.9.1 — THE RECORDED FORGE IS NOW LOUD; A SILENT ONE IS STILL EXECUTED.** A record note (round 28, found while staging): no frozen text, invariant or claim changes, and `Spec-Status` stays `accepted`. The trust-boundary record's route-B forge, executed at round 19, is now REFUSED by round 28's guard, so the record is annotated in place with what the second seat's forge probe measures at round 28's pin: the recorded forges are loud, and a forge that runs no Python frame while describing still reads no drift while the decision changes. The boundary it records is unchanged. **Prior cell follows.** **v12.9 — THE DESCRIPTION LOOKS NOTHING UP, AND WHAT IT CANNOT AVOID RUNNING IS STOPPED.** An implementation note (round 28; the round-27 verdict's two corrections, banked in the coordination repo at `d2f3730`, body sha16 `3f32ba18adf3b9a4`, with a wider class found by the second seat's stage 1 and three test gaps found by its stage 2, all fixed within the round). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. Round 27's describer still reached Python code through attribute lookup (a base's display method as a lookup default, a held object's or a metaclass's own attribute machinery), and its readers read contents but not every state channel of their types. A round-28 paragraph after round 27's states the corrections, the guard that now enforces the property, and the named limits; three of round 27's sentences are annotated in place. **Prior cell follows.** **v12.8 — THE DESCRIPTION RUNS NO DISPLAY CODE, AND STATE IT CANNOT READ IS REFUSED.** An implementation note (round 27; the round-26 verdict's one correction, banked in the coordination repo at `034ca1e`, body sha16 `daa579e450efcd14`, and two further gaps of the same class found by the second seat's stage 2 and fixed on the owner's word). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. The describer's last-resort `repr()` could run the held value's display code; objects whose state lives in C, where no field shows it, read as unchanged. A round-27 paragraph after round 26's states the corrections; two earlier sentences are annotated in place. **Prior cell follows.** **v12.7 — AN EAGER VALUE IS READ; ONLY A LAZY ONE IS LEFT UNEVALUATED.** An implementation note (round 26; the round-25 verdict's one correction, banked in the coordination repo at `619f710`, body sha16 `cbc0edc424fb6de5`). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. Round 25's rule treated every callable evaluator as lazy, so values supplied to ordinary `typing` constructors, which carry a constant evaluator, were left out of the comparison and a change to them read as no drift. A round-26 paragraph after round 25's states the correction; one of round 25's sentences is annotated in place. **Prior cell follows.** **v12.6 — LAZY VALUES ARE NEVER EVALUATED, AND A STRING ANNOTATION IS DATA.** An implementation note (round 25; the round-24 verdict's two corrections, banked in the coordination repo at `6e941ac`, body sha16 `28f0959c540666ea`). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. Round 24's rules covered one family of lazy value and one annotation regime. The describer still evaluated PEP 695's lazy type metadata, and the transform rewrote a census call inside an annotation that the future import stores as a string. A round-25 paragraph after round 24's states the corrections and the verdict's observation on the oracle; three of round 24's sentences are annotated in place. **Prior cell follows.** **v12.5 — THE EVIDENCE ON PYTHON 3.14 OR NEWER.** An implementation note for round 24, on the owner's decision of 2026-09-27 to raise the product's floor to Python 3.14 (and pydantic 2.12). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. v12.4 accepted the implementation on CPython 3.10 to 3.13 and named a later interpreter as not covered, and said running on one is a change to accepted evidence, to be reviewed as one. This is that change. Four changes in 3.14 reach the evidence layer: lazy annotations, comment bytes, new scopes, and an INV-7 run no longer carried. A round-24 paragraph after the acceptance paragraph states them, with the second seat's two stage-2 findings. Three earlier sentences are annotated in place. **Prior cell follows.** **v12.4 — THE IMPLEMENTATION IS ACCEPTED.** A record of the round-23 verdict, banked in the coordination repo at `7433bd9`, body sha16 `bc6e41b317fbafce`: "Round 23 is finished: **ACCEPTED**. The round-22 regression is fixed; no new findings." No frozen invariant's text and no code changes, and `Spec-Status` stays `accepted`. The implementation at pin `d00cd86` is accepted against this document's accepted design. A paragraph after round 23's records what was accepted and what the acceptance does not cover. The Review closure section's introduction now covers the implementation rounds, 6 to 23. **Prior cell follows.** **v12.3 — THE INTERPRETER JUDGES THE TRANSFORM'S REFUSALS AS WELL AS ITS READINGS.** An implementation note (round 23; the round-22 verdict's one correction, banked `0f8748a`, body sha16 `528ac5df80d1ad9c`). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. Round 22's byte-level rule looked a declared encoding name up as written, where the interpreter first normalises it, so it refused declarations Python accepts. Two of round 22's sentences are annotated in place: its guard judged acceptance only, and its BOM check compared names as the codecs do. The name domain is now derived and crossed with a BOM, and the transform accepts exactly when the interpreter does, in both directions. A round-23 paragraph after round 22's states it. **Prior cell follows.** **v12.2 — THE INTERPRETER IS THE ORACLE FOR EVERY SOURCE THE TRANSFORM READS.** An implementation note (round 22; the round-21 verdict's one correction, banked `e915b80`, body sha16 `f07dc190bb9f85b9`). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. 🔴 **It WITHDRAWS v12.1's sentence that a source is read "by the interpreter's own rule"**, annotated in place: the rule was the pure-Python tokenizer, which refused valid files with non-UTF-8 header comments. The encoding is now found at the byte level, and every decoded source must yield the interpreter's own syntax tree, positions included, or it is refused by name. A round-22 paragraph after round 21's states the mechanism and the cells. **Prior cell follows.** **v12.1 — EVERY TEXT BOUNDARY OF THE TRANSFORM IS STATED, NOT INHERITED.** An implementation note (round 21; the round-20 verdict's one correction, banked `3e6c072`, body sha16 `08bf83879e03eaf0`). No frozen invariant's text changes, and `Spec-Status` stays `accepted`. Route B's channel to its child is bytes both ways, with the census's output decoded only to name a failure. A Python source is read in the encoding it declares, parsed from its bytes as the interpreter parses a file, and refused BY NAME when the interpreter would refuse it. The twin declares what it is. On 3.13 a class's `__firstlineno__` is a location, not content, and no longer reads a line above `Site` as drift. A gate holds the class inside the transform. The same assumption in the other evidence modules is NAMED as a limit. A round-21 paragraph after round 20's states the mechanism and the cells. **Prior cell follows.** **v12.0 — THE ROUND-19 SCOPE OF INV-7 IS ACCEPTED AND FOLDED; ROUTE B ANSWERS ON ITS OWN CHANNEL; THE RESOLVER READS NAMES AS THE SYMBOL TABLE SPELLS THEM.** Two parts, of two kinds. (1) 🔴 **A FROZEN INVARIANT'S TEXT CHANGES BY ACCEPTANCE**, as v11.0 did for round 16: the round-19 verdict (banked `496a120`, body sha16 `7d2135a69dff4081`) ACCEPTED the scope proposed in v11.3. INV-7's row and §3b now state it. v11.3's PROPOSED block becomes the record of the acceptance, keeping the executed and inferred cases apart as the verdict asks. §11 records the unscoped text, with the verdict's own limit: the ruling "*accepts the scope now*" and approves nothing earlier. (2) **An implementation note** (round 20; the verdict's two corrections): route B's child writes its description to a response file and ends with `os._exit(0)`, and every failure to describe is named; the resolver derives the names the compiler adds by two routes, and compares every name in the symbol table's spelling. The second seat's stage-1 read found private-name mangling as a wider case of F2. `Spec-Status` stays `accepted`. **Prior cell follows.** **v11.3 — A NAME IS A CLAIM: A TYPE IS DESCRIBED BY NAME ONLY IF PYTHON CODE CANNOT HAVE MADE IT; AND THE TRUST BOUNDARY INV-7 HAS ALWAYS RESTED ON IS STATED, AND PUT TO THE REVIEWER.** Two parts, of two kinds. (1) **An implementation note** (round 19; the round-18 verdict's one correction): route B describes a type by module and qualified name only if `Py_TPFLAGS_IMMUTABLETYPE` is set, and describes every other type by its one recursive rule. Each census is executed and described in a fresh interpreter, so it cannot reach the transform. A round-19 paragraph after round 18's states the mechanism, the fourth rung of the ladder, the cells, and the INV-7 run re-made. (2) 🔴 **Not an implementation note: a PROPOSED addition to INV-7's scope, pending external design review**, on the owner's word "Disclose + state it" (2026-09-25). It sits beside the frozen text, after §6's table, and edits none of it. Census code changes behaviour; it does not attack the measurement. Three of INV-7's four readings run inside a process that executed census code, and a forge of one of them is shown silent. `Spec-Status` stays `accepted` for everything outside the proposal. **Prior cell follows.** **v11.2 — THE JOIN CHECK'S NAMED OVER-REFUSAL IS CLOSED, AND THE ORACLE NOW GENERATES ANNOTATIONS.** An implementation note (round 19); no frozen invariant's text changes, and `Spec-Status` stays `accepted`. v9.5's round-13 paragraph named two limits "recorded for the next round" and one count. All three are annotated IN PLACE:
- the over-refusal is closed on 3.12 and later;
- the oracle's generator now emits parameter, keyword-only and return annotations;
- the count of modules the join check refuses none of is dated.

A round-19 paragraph states the mechanism and the evidence. **Prior cell follows.** **v11.1 — ROUTE B IS ONE RECURSIVE RULE, AND THE REFERENCE ARM'S `Site` IS CHECKED WHERE IT RUNS.** An implementation note (round 18); no frozen invariant's text changes, and `Spec-Status` stays `accepted`. It records the round-17 verdict (banked `1aa6d68`, body sha16 `41121680bbb74898`): "*RETURNED for one implementation correction … the design amendment remains accepted*". Route B's function normaliser omitted the WRITABLE `__name__`, `__qualname__` and `__module__`. **v11.0.1's hand list of function fields is WITHDRAWN.** A round-18 paragraph states:
- the recursive rule that replaces it, with its three named exclusions;
- the attribute-cache bit that an earlier form compared by accident;
- the import-time check of the realized `Site` in every arm, which closes v11.0.1's named context limit;
- that the INV-7 run is re-made, not carried, because the observer changed.

**Prior cell follows.** **v11.0.1 — ROUTE B READS THE CLASS'S TYPE-LEVEL ATTRIBUTES TOO, AND ITS CONTEXT LIMIT IS NAMED.** A text correction to v11.0's round-17 paragraph, matching the round-17 fix; nothing else changes. Research's pre-seal read found `Site.__qualname__` reassigned after the class statement passing BOTH routes. `__qualname__` and `__name__` are slots of the TYPE object, not in `vars(Site)`, so v11.0's "the two built `Site` classes are compared" was false. Route B now also compares every data descriptor the METACLASS defines, read off each built class. The paragraph also names what route B cannot see: a post-class change CONDITIONAL on runtime context. **Prior cell follows.** **v11.0 — THE ROUND-16 AMENDMENT TO INV-7 IS ACCEPTED AND FOLDED IN: THE REFERENCE ARM IS FREE OF THE CENSUS UNDER TEST.** 🔴 **A frozen invariant's text changes in this version, BY ACCEPTANCE:** the round-16 verdict (banked `a17ebc7`, body sha16 `fb62c45af45289a7`): "*design amendment ACCEPTED; implementation RETURNED for one correction*". The changes:
- INV-7's row now defines UNINSTRUMENTED as the accepted text.
- Part A-2's third-arm reason takes the accepted wording, and its superseded sentence moves to §11.
- The PENDING block becomes an ACCEPTED record.
- The drift sentence is rewritten for round 17's correction: the check now reads the whole class definition AND the realized class. **v10.0.1's sentence "Any change to `Site`'s OWN definition is drift" is WITHDRAWN**: the reviewer showed a reordered and a duplicated docstring passing it.

`Spec-Status` stays `accepted`. **Prior cell follows.** **v10.0.1 — THE DRIFT SENTENCE NAMES WHAT DRIFT IS, NOT HOW MANY CELLS TEST IT.** A text correction to v10.0's round-16 paragraph and nothing else; the proposed INV-7 amendment is unchanged. Research's pre-seal read found `site_drift`'s own docstring claiming "any behavioural" change is drift, and three drift shapes no cell exercised. Dev added the cells, so v10.0's "Five drift cells" went stale. The sentence now names the categories (what counts as drift and what does not, including a helper elsewhere in the census) and carries no count, because a count here describes a moving subject. **Prior cell follows.** **v10.0 — A PROPOSED AMENDMENT TO A FROZEN INVARIANT, PUT TO THE REVIEWER AS A DESIGN QUESTION: THE REFERENCE ARM CARRIES THE CENSUS OF AN ACCEPTED COMMIT, NOT THE CENSUS UNDER TEST.** 🔴 **This is not an implementation note.** The round-15 verdict showed a declaration-time mutation of the census that changed a decision in all four arms while the reference observer read zero. It ruled that INV-7 requires a census-free reference, and that "retaining this construction requires an explicit design amendment". On the owner's word ("(3) Accepted census", 2026-09-24T17:34Z), this version PROPOSES that amendment. **The frozen INV-7 text is NOT edited.** The proposal sits beside it, labelled pending, so that the accepted text never states something the reviewer has not accepted. A paragraph after round 15's note records what the verdict showed and what replaces round 15's construction. `Spec-Status` stays `accepted` for everything outside the proposal. **Prior cell follows.** **v9.7 — THE STAND-IN IS GONE: THE TWIN CARRIES THE REAL CENSUS, AND "UNINSTRUMENTED" IS HELD TO A NARROWER, MEASURED WORD, WITH ITS COST NAMED.** An implementation note only (round 15): no frozen invariant's text changes, and `Spec-Status` stays `accepted`. The round-14 verdict's one finding was that the stand-in's CLASS differed from `Site`'s in its members, so a decision could ask the class and differ with nothing counted. On the owner's word ("(A) Real census in twin"), the twin now copies `census.py` verbatim. A paragraph is added after round 14's note, which stays as history. The three test citations in that note name nodes this round removes, so they are rewritten as plain references to the tests that replace them. 🔴 **This version WITHDRAWS v9.6's sentence that a residual "can observe only a stand-in's IDENTITY or its CLASS, and both are faithful".** The class's name was faithful, and its members were not. 🔴 **It also states outright that the reference arm now has the census module in it**, and names the blind spot that opens. **Prior cell follows.** **v9.6.1 — v9.6'S NOTE MISDATED THE HISTORY IT CORRECTS, IN TWO SENTENCES.** A correction to v9.6's note and to its cell, and nothing else. No frozen invariant's text changes and `Spec-Status` stays `accepted`. v9.6 said that rounds 11 to 13 removed every declaration and then refused routes to it. **The twin removed every declaration and its census imports from its FIRST derivation** (2026-09-19, `dca9f96`, the transform's first commit). **The route refusals began in ROUND 12**: `d61fd62` added the first, and it is not an ancestor of round 11's pin `1af8292`. Both sentences now say so, in place. Found by research's pre-seal read of round 14, after dev had corrected the same misdating in the round-14 README's draft. **Prior cell follows.** **v9.6 — THE TWIN STOPS REMOVING WHAT IT CANNOT FOLLOW, AND "UNINSTRUMENTED" BECOMES A MEASUREMENT WITH WHAT IT CANNOT SEE NAMED.** An implementation note only (round 14): no frozen invariant's text changes and `Spec-Status` stays `accepted`. It is added as a paragraph immediately after the tranches 3–6b note, whose "AST inverse of the instrumenter" it narrows. That note stays as history, the form v9.5 used for the paragraph it corrected. The round-13 verdict's first finding was five more routes to a REMOVED declaration, each deriving a broken twin with `verify()` clean. That ended the approach rounds 12 and 13 had taken. On the owner's word ("Keep names bound"), the twin now removes only measurements and keeps every declaration bound to an inert stand-in. 🔴 **That change meets INV-7's frozen word UNINSTRUMENTED head-on, and the note says what the word is held to and how it is checked, rather than leaving a reader to reconcile the two.** **Prior cell follows.** **v9.5 — ROUND 8'S "BY CONSTRUCTION" WAS WRONG AT BOTH OF ITS LAYERS, AND WHAT REPLACES IT IS A CHECK AND A GATE, EACH WITH WHAT IT CANNOT SEE NAMED.** An implementation note only (round 13): no frozen invariant's text changes and `Spec-Status` stays `accepted`. It is added as a paragraph immediately after the round-8 paragraph it corrects, which stays as history — the form round 9 used for the paragraph it superseded — so the document never says the old thing unmarked and never loses the record of having said it. **v9.4 — A HAND-PICKED PREDICATE PAIR WAS STANDING WHERE THE INTERPRETER'S OWN READING BELONGED, AND IT HAD INHERITED ITS NEIGHBOUR'S GUARANTEE.** 🔴 **The round-8 reviewer defeated rule C with a nested `import os as S` under `global S`** — `symtable` reports that symbol `is_imported` and NOT `is_assigned`, so the pair never fired and a declared site was replaced in silence while the scan still reported `bound=True`. *The fix is not a third predicate.* `is_namespace` would have been the next rung of exactly the ladder this evidence exists to get off, and rule C now reads what the compiler emits in a NESTED code object (`STORE_GLOBAL`/`DELETE_GLOBAL`) — the same KIND of reading rule A already was. 🔴 **THE MISS WORTH CARRYING IS THE ADJACENCY:** rule A earned *“total over syntax by construction”* by asking the compiler; **rule C sat beside it inheriting that sentence's authority and never had the property, and nothing said so.** The superseded pair is KEPT as the negative control its replacement must beat, and the two readings are measured to differ on exactly the two nested imports and to agree on every other row of a 46-case matrix, on 3.10, 3.11, 3.12 AND 3.13. *One row changes hands between the rules at 3.12 — PEP 709 inlines a list comprehension's walrus into the module, where rule A counts it, while the generator-expression spelling stays with rule C on every version — so the matrix now pins WHICH RULE caught each refused row, because a matrix that asserts only “refused” is green for a different reason on each side of that boundary.* 🔴 **RESEARCH'S DIFFERENTIAL HARNESS CAUGHT THE FIX'S OWN TRAP BEFORE IT WAS WRITTEN:** the wider opcode tuple sits four lines above the new rule, and reading it in a nested scope REFUSES `class K: S = 1` — correct code, every class whose attribute collides with a site name. *The nested set is now asserted to be a STRICT SUBSET of rule A's.* **Two further defects were found by exhausting the reviewer's classes rather than fixing the cells he named** — an import-restoration test reading a hand-written alias tuple two lines below the derived one, and a packaging gate whose regex could not see the filenames it was written to check. 🔴 **NO FROZEN INVARIANT'S TEXT CHANGED, AND THIS BUMP DOES NOT RE-OPEN THE DESIGN.** The delta from v9.3 is the round-9 implementation note — which SUPERSEDES the v9.3 note's predicate paragraph in place rather than appending beside it — and this cell. **THE ACCEPTED DESIGN REMAINS ROUND 5'S, WHICH IS v7.** **Prior cell follows.** **v9.3 — THE VERSION CELL IS AN IDENTITY, AND THREE DIFFERENT DOCUMENTS HAD SHIPPED UNDER ONE.** 🔴 **The round-6 package, the round-7 package and this tree each carry a file named `0042-exercised-guarantees-SPEC-v9.2.md`, and all three differ** — sha16 `2f36ffbdd92957c9` (925 lines), `ec8798b7cfe301e8` (950 lines) and this text. *Each round since v9.2 added an IMPLEMENTATION NOTE under the accepted version and nothing moved the identity, so a reviewer holding two copies has two files with one name and no way to tell them apart without digesting them himself.* The round-7 reviewer had already touched the symptom from the other side — `PIN.txt` *"describes round 5's accepted version as v9.2 rather than v7"* — and it surfaced here as a spec-diff filename reading `v9.2-to-v9.2` for the third round running, over a diff that is 88 lines long: **the check passed because it was checking the wrong thing.** 🔴 **NO FROZEN INVARIANT'S TEXT CHANGED, AND THIS BUMP DOES NOT RE-OPEN THE DESIGN.** The delta from v9.2 is the round-8 implementation note and this cell. *What carries acceptance is `Spec-Status: accepted` and round 5's verdict — not the version number: the version says WHICH TEXT, the status says what was decided about it.* The precedent is in this cell already: v9, v9.1 and v9.2 were all post-acceptance corrections and none was read as re-opening anything. **THE ACCEPTED DESIGN REMAINS ROUND 5'S, WHICH IS v7** — the copy in the round-5 package, not this one. *Ruled by research (the design carrier is theirs) after dev measured the three digests; the durable fix is to bind the shipped copy by CONTENT — its sha256 in `PIN.txt` beside its version — so two same-named copies are distinguishable without a reader digesting them.* **Prior cell follows.** **v9.2 — THE CITATION FIXED, AND THEN FIXED AGAIN IN THE CELL THAT ANNOUNCED IT.** 🔴 **A Part B sentence cited the gate by its MODULE name in the backticked form the citation gate reads as a TEST NODE, so the accepted spec cited a test that does not exist.** *It sat there from v6 and was invisible while the spec was a draft: **drafts are exempt from that gate, and acceptance is where a cited name stops being a note and becomes a claim.** The suite failed on the STATUS, not on any change to the text.* It now names the node that does the checking, `tests/test_spec_gate.py::test_no_spec_names_a_module_or_script_that_does_not_exist`. 🔴 **Then v9.1's own Version cell REPEATED THE OFFENDING TOKEN while explaining it, and the derivation caught that too — the failure class named in a carrier the gate scans, one level up, inside the correction.** *Both passes were derived rather than taken: every backticked `test_…` token in both candidates, extracted with the gate's own pattern, against the tree's defined test names — one hit in 0042, none in 0043, and zero after this cell.* **No other change; v9's cell follows.** **v9 — THE ACCEPTANCE FOLD.** 🏁 **ACCEPTED AT THE DESIGN LEVEL at external round 5, 2026-09-18:** *“both specifications are accepted at the design level and may proceed to implementation”* — the accepted artifact is the ROUND-5 PACKAGE — sha256 `791c1089776d9f49332483f8ff88b25794dec795ee8a7cf8eb33b441eaa1747a` @ pin `a9d3622d6252a19387b2ecb66a665f101825fb36`, CI `35382261953`, fresh-clone capture at the pin **3339 passed, 11 skipped, 11 xfailed in 750.36s** — which the reviewer holds; **no seal follows this fold.** 🔴 **FROZEN INVARIANT SURFACE, in the reviewer's words: INV-1, INV-2, INV-2b–2d, INV-7, INV-8.** 🔴 **THE RULE FORWARD: a change to a FROZEN invariant is a NEW EXTERNAL ROUND, not a version bump.** Everything else moves under the standing rule this arc paid five rounds to state — **the correction at the sentence an implementer copies, the record of what it replaced in §11.** The closure ledger under *Review closure* carries one row per finding with evidence a reader can RUN or OPEN and **derives its own counts; this cell does not restate them.** **WHAT THE FIVE ROUNDS DID TO THIS SPEC: `INSTALLED` was defined FOUR TIMES and the first three were PROXIES that passed their own checks** — the declaration plus runtime reports *(satisfied by code containing no instrumentation)*, a scan for `declare_site` calls *(both fixture decisions executed, reconciliation passed, the counters never moved)*, and the binding scanned over the MODULE *(`.consult` in one function and `.fire` in another read as bound)*. **Each was checkable; each was checkable against something other than what it claimed.** *The current definition — one lexical function body, unshadowed name, counters asserted as DELTAS across the decision — is the first that cannot be satisfied without the guarantee being measured, and the three superseded forms are kept in §11 as mutants their replacement must fail on.* **CREDITS.** The external reviewer reproduced every claim at the pin and returned the line four times; the three defects he found at acceptance had all passed our own controls. Dev (`veracium-2b`) built every evidence leg and its mutants, and caught the §9 briefs naming returned rounds — a carrier nothing re-derived. Research (`veracium-research-48`) authored the specs and the design answers and ran the second seal leg. The owner ruled the split, ruled `UNRESOLVED` a terminal outcome, and dispatched every round. *(The `Spec-Status: draft → accepted` flip is the adoption's declared delta, on the owner's word; this candidate leaves the line as it stands.)* Prior: v9.2 · v8.1 · v8 · v7 · v6 · v5 · v4 · v3.1 · v3 · v2 · v1. |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line at the top* |
| **Internal reviewers** | research (author) · dev |
| **External review** | **required** — §4's counters sit in `gate.py`, `graph.py`, `lifecycle.py`, `ingest.py`, `schema.py`, all guarded |
| **Decision + date** | |
| **Path** | **full** |
| **Number** | 0042. 🔴 **CORRECTED v4 (round-1 carrier finding C2, research's): v3.1 said “0040 is free but was VACATED”. IT IS NOT FREE — `specs/ALLOCATION.md` records it under the column `spent on`, consumed by the WITHDRAWN procedural-text proposal.** Vacated and free are different states and this cell asserted the wrong one against the registry. *(Found by the external reviewer. Research had swept 63 `0040` references across 21 files the same night and classified THIS line as correct — by asking whether the file explains the renumbering rather than whether the sentence agrees with the registry. A category check where a content check was owed.)* **0042 is this spec; the refusal harness takes its own number from `allocation.py --next` at adoption.** |

---

> **THE CURRENT CONTRACT: AN INDEX** (v12.15, research as the specification's author; added at the round-33 verdict's
> suggestion). **This index is NOT normative.** It points to the text that is. Where the index and that text differ, the
> text governs, and the index is the defect. Every statement below is a pointer, by round heading or section, to text
> that already exists.
>
> **In force:**
> - **The frozen design:** §1 to §8, with the invariants table in §6 (INV-1, INV-2, INV-2b–2d, INV-7, INV-8), accepted
>   at round 5. §11 lists the decisions superseded since then; each entry there is history.
> - **INV-7's amendment:** the reference census, accepted at round 16 (v11.0). INV-7's row in §6 carries the accepted
>   text.
> - **INV-7's scope:** the round-19 measurement scope (v12.0). Census code may change behaviour; the measurement does not
>   assume it attacks the measurement. §11 records the earlier wording it superseded.
> - **The implementation:** accepted at round 23 (the paragraph headed "ROUND 23'S VERDICT"), with its corrections
>   accepted through round 33.
> - **The INV-7 measurement as accepted at round 33:** the paragraphs headed ROUND 17 to ROUND 33, each headed by the
>   rule it adds, read together with the markers listed below.
> - **The named limits in force:** those in each "Named limits" block from round 27 on, except any marked WITHDRAWN or
>   SUPERSEDED beside it, together with the round-19 scope.
>
> **How the implementation notes below are ordered:** not strictly by round. The two tranche notes come first, then the
> paragraphs headed ROUND 14 to ROUND 33, then notes from rounds 6, 7, 8 and 13, an earlier round-19 note, and round 9's.
> Read them as a sequence of changes: where a later round's paragraph and an earlier one differ, the later one describes
> the shipped implementation, whether or not the earlier one carries a marker.
>
> **Statements that are NOT current**, each marked where it stands, with its text kept as adopted. This list covers every
> such marker in the implementation notes and §4. §11's entries are history as a set, and the Version cells above record
> each version's own history:
> - the twin's "AST inverse of the instrumenter" sentence, for declarations: history from the paragraph headed ROUND 14;
> - round 14's three stand-in paragraphs: history from ROUND 15. Also the claim that a residual "can observe only a
>   stand-in's IDENTITY or its CLASS", WITHDRAWN in the ROUND 15 paragraph;
> - round 15's construction: history from ROUND 16;
> - v10.0.1's sentence that any change to `Site`'s own definition is drift: WITHDRAWN at v11.0, in the ROUND 16 paragraph;
> - route B's hand list of what it describes: WITHDRAWN at v11.1, in the ROUND 17 paragraph, and replaced by ROUND 18's
>   recursive rule;
> - "by the interpreter's own rule", for how a source's encoding is read: WITHDRAWN at v12.2, in the ROUND 21 paragraph,
>   and replaced by ROUND 22;
> - the set of values described without identity: WITHDRAWN at round 32 (v12.13), in the ROUND 31 paragraph;
> - a set's elements ordered by their descriptions, the tie refusal, and a hash-seeded dictionary reading as drift
>   between route B's children: WITHDRAWN or SUPERSEDED at round 33 (v12.14), in the ROUND 32 paragraph;
> - the resolver's "by construction" sentence: history from the paragraph headed ROUND 13;
> - the symbol-table predicates for a binding made from a nested code object (`is_global()` chosen over
>   `is_declared_global()`): history from the paragraph headed ROUND 9, which reads the compiler's opcodes instead;
> - the count of 162 in §4 Part A-0: WITHDRAWN (round-1 amendment 4);
> - Part A-0-bis's three sets: SUPERSEDED IN PART by Part A-0-ter;
> - INV-7's earlier wording and its unstated scope: the two §11 entries.

> **Implementation note, tranche 2 (2026-09-19; the owner's word "implement all 3"; no
> frozen invariant touched — INV-1, INV-2, INV-2b–2d, INV-7, INV-8 stand as accepted).** Twenty-eight
> enforcement points in gate, schema, compile, grounding, authority and asof are now expressed
> through declared sites (28 ids; `asof.adapter.adapt.refuse` binds thirteen refusals of one
> function to one id, as §4a allows for one guarantee enforced at several branches). Two
> refinements the accepted text did not foresee, because no product site existed when it was
> written: **(i) a predicate site declares its declining value** — `declare_site(id,
> declines=False)` (or `True`, or a callable over the returned tuple) — and returns BOTH verdicts
> through `fire()`, so the return statement keeps the shape Part A-4's discovery finds and `fired`
> moves only on the decline (an exception, `None` or `False` decline by default; a filter whose loss
> is not in its return value passes `declined=` explicitly); **(ii) discovery looks through the
> wrapper** — `NAME.fire(x, …)` is the decision `x`, since `fire` returns its first argument
> unchanged — so an instrumented site keeps its kind at its statement and does not vanish from the
> inventory it was reviewed in (the inventory grew 745 → 748 by the census module's own three
> candidates, none an enforcement point). The runtime leg (`tests/test_0042_sites.py`) executes one
> declining decision at every declared id and asserts Δconsulted == 1 and Δfired == 1; the two
> as-of recall sites are inner functions driven through a recall with one candidate. Cost at the
> shipped default (census OFF), measured on the rebuilt ten-conversation store over 180 timed
> recalls: one adjacent pair read median 152.1 ms → 158.9 ms (+4.5 %) with the plain idiom at
> every site (re-measured alternating twice against the pre-tranche tree: +1.6 % and +6.1 % —
> the cost is real, both positive; its magnitude is not established at two alternations), after
> the site became its own context manager (1.00 µs → 0.20 µs per
> consult+fire disabled). Measured where it
> came from: 12,527 decisions per recall, 12,385 of them the four `Edge` predicates (`quarantined`
> 4,314, `use_only` 2,732, `assertable` 2,727, `valid_now` 2,612). **The owner's word (question
> form, 2026-09-19): a bypass at those four.** The decision is computed ONCE (`q = <expr>`), the
> census machinery runs only when the census is enabled, and both returns are discovered under
> the one id (discovery applies FILTER_RETURN's name rule to Boolean names). Re-measured
> ALTERNATING the pre-tranche tree and this one, twice, 180 timed recalls each: 149.9 / 151.1 ms
> against 150.5 / 147.6 ms — inside run-to-run noise; the figure is from the alternating run only.
> **Three things stated, not implied.** (a) The trade against §4A-2's letter: `consulted` is
> counted AFTER the decision is computed (so the predicate is written once, never twice), which
> honours the clause's purpose — counted at the site, never at a consumer — and not its letter; the
> one observable consequence is that a predicate that RAISES is invisible to the census at these
> four sites (`test_a_raising_predicate_raises_identically_on_both_paths_and_is_invisible_to_the_
> census` executes exactly that, and asserts `Site.__exit__` never swallows the raise). (b) The
> price research named: the shipped default is now a FOURTH code path at these sites, so the INV-7
> harness, when it lands, gains a fourth arm — instrumented-but-bypassed — compared with the
> healthy arm on decision OUTPUTS (a bypassed arm emits no trace), its sharpest case a predicate
> that raises; `test_the_enabled_and_bypassed_paths_agree_on_every_verdict` is that arm in
> miniature today. (c) A third option, considered and not taken: a per-recall count at the four
> would have removed the cost without a bypass but made the counter values two units across one
> report. **Tranche 3 (the same day):** forty more ids — graph (13), proactive (2), ingest (3),
> procedures (1), the procedural gate (2), the registry (2), the MCP closed set (2), the Memory
> surface (11), diagnostics (1), telemetry (5) — 68 bound in all, by a generic AST-positioned
> instrumenter: a return or raise keeps its ORIGINAL value inside `fire(...)` (the inventory stays
> at 752), `consult()` brackets the enclosing `if` for a refusal or the whole body for a predicate
> with several exits. Two review corrections: `_src_revoked` and `_is_variant` each bind ONE id —
> their `return False` exits are the non-declining branch of one decision (`declines=True`), not
> enforcement points of their own; a structural sweep of the whole review for that shape (a
> function carrying more than one id on non-raising exits) found seven functions, every one a set
> of DISTINCT declining reasons on hand-reading — no further instance. **Tranche 4:** thirty-three
> more ids in scope, scope_linkage, scope_read and portability — 101 bound; a check whose `if` sits
> inside a loop brackets the function body instead (one consult per call, not per iteration), and a
> raise inside an `elif` does the same. The review's keys are now DERIVED from the source (every
> `fire()`-wrapped candidate binds its statement to its id; the per-line NOT overrides re-keyed by
> (qualname, kind, ordinal) in one hop from the plan-time inventory) after a sequential re-key had
> drifted two keys onto neighbouring statements — the review file will be generated the same way.
> **Tranche 5:** the store's forty-six ids — 147 bound, every id the review named; each (function,
> id) bracketed once at the smallest statement containing all of its exits (an `elif` climbs to its
> chain root, an except-handler exit takes its `try`); the instrumenter's own defect found and fixed
> (`ast` columns are byte offsets — a `§` before the insertion point had put a parenthesis one
> character too far, into whitespace, in every landed case). **Tranche 6a — the reconciliation
> flip:** the REVIEWED set is `specs/evidence/0042/reviewed_points.json`, GENERATED
> (`reviewed_points_gen.py`) from the authored review (`semantic_review.py`) and the inventory —
> 752 decisions, one per DISCOVERED candidate, each carrying its stable key (module, qualname,
> kind, ordinal), its line and the statement text it decided about, the NOT decisions grouped by
> class with their reasons; the DECLARATION is `declaration.py`, generated from the same review
> (id · spec · invariant · file:symbol · label, 147 rows). `tests/test_0042_reconciliation.py`
> reconciles all four sets on the real tree with zero refusals and shows every refusal live
> (a dropped decision, an undeclared enforcement candidate, a declared id nobody bound); it also
> carries the second reader's mechanical checks — every decision's statement still at its line,
> every key resolving, exactly one decision per candidate, the collapse shape re-swept against a
> frozen hand-read set. The evidence reconciler now compares REVIEWED-as-enforcement to DECLARED by
> SITE id (a reviewed row names its site; the fixture's rows, carrying none, keep their candidate
> id) — the two coincided only in the fixture. **6a-bis (research's second read):** the 43
> `predicate-helper` decisions shared one reason whose escape clause ("where one exists") could not fail;
> the generator now derives each helper's consumers from the source and names them — the consuming site
> by id, the site-less consumers, or a hand-stated outside consumer — and refuses a helper with none.
> **6b — INV-7 as built:** the trace comes from an INDEPENDENT OBSERVER (`inv7_observer.py`), not the
> census — every declared enforcement function wrapped from outside, one content-free (symbol, decision)
> per exit; 95 of the 102 declared symbols are reachable that way *(⚠️ v12.16: at veracium `aa2dd98`, 101 of 108 — `specs/evidence/0042/inv7_transcript.txt`: "OBSERVED SYMBOLS: 101 wrapped of 108 declared"; the same seven nested functions, listed there by name. A declared id that sits on one of them is in the declaration and never in the trace, so "every declining execution is traced" is read over the 101)* and the seven nested functions are
> excluded by name in the transcript. Four arms — healthy, forced-error, disabled (the bypass path) and the
> uninstrumented twin at the commit the tranches began from — over 29 test files derived from this row's
> sentence plus a greedy cover of every id the suite reaches (`inv7_reach_table.txt`,
> `inv7_named_suites.json`), compared PER TEST after a control pair (the reference arm twice) names any
> test whose own trace is not reproducible — the first run read DIVERGENT on exactly such a test, and the
> bound ("under frozen replay inputs") is now enforced rather than assumed. `inv7_transcript.txt` is pinned
> to its commit like 0039's; `tests/test_0042_inv7.py` binds the pin, the per-test verdict grammar, the
> cross-checks, the in-process miniature over the runtime leg and the harness's mutation matrix. 0042's
> implementation is complete on the dev side; the implementation-review package follows on the owner's word.

> **Implementation note, tranches 3–6b and the INV-7 twin (2026-09-19/20).** The remaining ids landed by
> tranche (40, 33, the store's 46; 147 ids bound, then 161 with 0041's fourteen refusals), INSTALLED == DECLARED,
> the four sets reconciled on the real tree, the runtime leg exercising every id once. INV-7's four-arm
> transcript: the first twin was EXPORTED from the commit the instrumentation began at and became a
> different product the moment another spec touched src; the twin is now DERIVED from HEAD by an AST
> inverse of the instrumenter (`inv7_uninstrument.py`), the reference arm run twice and per-test units
> that differ between the two runs excluded by name. The sentence this line exists to carry, from the
> second seat, after three census-of-the-moment instances in one day: **a census is safe only when it
> refuses on change or derives on demand — every other census is a claim with a date hidden in it.**
> The pin test that asserted 'every src commit since the twin was 0042's' and the exported twin both
> encoded a date and went on asserting it; the reconciliation test's hand-read set refuses a new member
> until someone reads it; the derived twin re-derives and has no moment to decay.
>
> **ROUND 14 NARROWS WHAT "AN AST INVERSE OF THE INSTRUMENTER" REMOVES, so the sentence above is history for
> declarations** (v9.6, research as the specification's author, 2026-09-24; the round-13 verdict's first finding).
> The twin had removed every `NAME = declare_site(...)` and its census imports from its first derivation, and rounds
> 12 and 13 refused, one spelling at a time, each route by which other code could still reach the removed name: an
> import, a star, `__all__`, an attribute, `getattr`, `import_module`, `sys.modules`, `globals()`. The round-13 verdict found five more —
> `pkgutil.resolve_name`, `runpy.run_module`, `importlib.util` loading, a function's `__globals__` and `inspect.getmodule` — and each derived a
> broken twin with `verify()` clean. **The set of routes to a name is open. A name that is never unbound cannot be found
> missing, however the route is spelled.** So the twin now removes only MEASUREMENTS: every `consult` and every `fire`
> in the forms the transform recognises, with the recognised bypass kept dead as before. It keeps every declaration and
> every census import VERBATIM. The twin's STUB census has stood in place of the real one since round 7. It now answers
> `declare_site` with one INERT stand-in per declaration: a class named `Site`, answering the real `Site`'s whole surface
> as a census that is off answers, recording nothing, registering nothing, and COUNTING every use. Every route rounds 12
> and 13 refused, and the verdict's five, now derive, verify clean and run identically in twin and source, 36 cells in
> `tests/test_0042_inv7.py::test_r14_f1_no_route_to_a_declared_site_breaks_the_twin`. The refusals those cells replace
> were refusals of correct code, and they are gone. The transform's other refusals stay. Its full list is the twin
> manifest's `refused_forms`, and the scope resolver's refusals (the round-13 note below) are separate from it. Among
> those that stay are the ones the transform needs to RECOGNISE its input: a `fire` or `consult` it cannot bind to a
> declared site, a declaration made through an alias of `declare_site`, and a census name the STUB does not answer.
> The verdict's second finding was in the scan-to-runtime check, not the twin. That check had collected a property's
> getter alone and counted functions by name. Every body the scan counts as binding a site must now be FOUND among the running module's code objects
> and be equal to the compiled source, or it is refused (`tests/test_0042_evidence.py::test_r14_f2_a_binding_body_that_did_not_run_is_refused`).
>
> **Is that arm still UNINSTRUMENTED? INV-7's text is frozen and this note does not change it. The note says what the
> word is held to, and how that is checked.** Part A-2 wants an arm "without a census in it", because two arms that
> share the instrument cannot detect the instrument. Since round 7 that arm has carried a STUB census module rather than
> none. So the word has never meant "no census module is importable". It has meant that no census code can take part in
> a decision. Until round 14 that held by ABSENCE, because every declaration was removed and no stand-in existed. From
> round 14 it holds by MEASUREMENT. The stand-ins stay bound, and the observer reads their use count over the reference
> arm's whole run. The harness gate `uninstrumented:inert_stand_ins_unused` requires that count to be exactly 0, and
> never merely present, beside an empty registry. The round-14 transcript reads 0 uses and an empty registry, with
> traces identical across the four arms over 860 tests. The count covers every attribute read except `__class__`,
> every method call however reached (through the class included), and every protocol Python dispatches on the type:
> hash, `==`, the four orderings, `repr`, `bool`, `with`, size, and attribute set and delete. The gate is shown to fail
> through the real chain — twin, observer, arm, comparison and final status. A one-test suite that reads a declared
> site's attribute turns it false, and its control, which reaches the same site by identity only, reads 0 with the gate
> true (round 14's harness-gate test, replaced in round 15; see the paragraph after this note). The surface
> is pinned against the REAL class, never a list
> (round 14's surface test, removed in round 15, when the twin's class became the real one). A stand-in missing a
> member is the reviewer's own class: the twin raises where the source answers, while `verify()` stays clean.
>
> **What the count cannot see, named and pinned in both directions.** Every named residual counts 0, and its nearest
> counted neighbour counts (round 14's residual test, removed in round 15).
> The residuals are `is`, `id()`, `type()`, operators neither class defines, comparisons CPython short-circuits on
> identity (list and tuple `in`, `==`, `index` and `count` on an identity hit), and a read of `__class__`. The last is
> exempt on the owner's word ("Faithful class, exempt"). CI's pydantic-2.7.0 floor read `__class__` 126 times at import,
> through `isinstance` over module globals. So the stand-in's class is NAMED `Site`, and every `isinstance` and `type()`
> a program can reach answers as it does in the source. **Each residual can observe only a stand-in's IDENTITY or its
> CLASS, and both are faithful: one object per declaration, and the class `Site`.** One behavioural unfaithfulness is
> also named: a stand-in's counters read zero, and re-declaring an id (a reload) is not refused by it. 🔴 **A reader may
> hold that UNINSTRUMENTED means "no declaration survives". That reading would make this note a change to a frozen
> invariant, which is a new external round and not a version bump.** The owner chose to measure inertness rather than
> rewrite declarations. This paragraph is the claim that choice rests on, so it is the one a reviewer should test.
>
> **ROUND 15 REPLACES THE STAND-IN WITH THE REAL CENSUS, so round 14's three paragraphs above are history** (v9.7,
> research as the specification's author, 2026-09-24; the round-14 verdict's one finding; the owner's word "(A) Real
> census in twin"). The verdict: "*the new stand-in can still change an instrumented decision from True to False while
> verification is clean and its use counter stays at zero*". The stand-in's CLASS differed from `Site`'s in its MEMBERS.
> It defined counting overrides (`__hash__`, `__eq__`, `__bool__` and others) where the real `Site` inherits `object`'s,
> so a decision that asks the class, such as `type(S).__hash__ is object.__hash__`, answered differently in the twin,
> and a read of the class is not a use. 🔴 **The sentence above that a residual "can observe only a stand-in's IDENTITY
> or its CLASS, and both are faithful" is WITHDRAWN.** The class's NAME was faithful, and its MEMBERS were not. The claim
> came from a check of the class's name, qualname and repr, never of its members, and the surface test it leaned on
> compared names in one direction only. A stand-in that is not the real class is faithful only by a list of things
> checked. This line has now lost two such lists to a member nobody listed.
>
> **So the twin now copies `census.py` VERBATIM, and every declaration binds a real `Site`.** `verify()` requires the
> twin's census module to be byte-equal to the source's, and refuses a one-byte difference. The twin's class is the
> source's class. Re-declaring an id is refused in both, so the one unfaithfulness round 14 named is gone, and pinned
> as gone (round 15's census-identity test, replaced in round 16 by the reference-census identity test, see below).
> The verdict's eight shapes, its two controls, `type(S) is census.Site` and the repr each read alike in source and twin,
> end to end (`tests/test_0042_inv7.py::test_r15_every_question_about_a_site_answers_alike_in_source_and_twin`). Reads
> that execute no census Python code are not counted: a slot read, `is`, `id()`, `type()`, and `object`'s own methods.
> They are faithful by construction, and by one measured fact, which is pinned: with the census off, `consult` and
> `fire` leave every slot of a `Site` unchanged
> (`tests/test_0042_inv7.py::test_r15_b3_with_the_census_off_consult_and_fire_leave_every_slot_unchanged`). So the
> twin's never-called Sites are in the state the off arm's Sites are in.
>
> **What UNINSTRUMENTED is now held to, what it costs, and the question this round puts to the reviewer.** Part A-2 wants
> the reference arm "without a census in it", because two arms that share the instrument cannot detect the instrument.
> **Round 15's reference arm HAS the census module in it**: the module is imported, and its declaration code runs at
> import in every arm. So A-2's sentence is no longer true of the module. The arm is held instead to this: **no census
> code runs in it beyond the census module's own import and the product's declarations.** The observer measures that
> with a profile hook installed before the product is imported. Every entry into census code from outside the census
> module counts, except three:
> - the module's own body;
> - a call to `declare_site`, identified by its code object, from a module body in a product file;
> - the observer's own reads.
>
> A declaration made from a class body, a function body, a test module or `exec`'d text counts. The harness gate
> `uninstrumented:no_census_code_in_decisions` requires the count to be exactly 0, and never merely present. Where the
> off arm also ran, `uninstrumented:registry_equals_off` requires the reference arm's registry to equal the off arm's,
> as sets. The gate is shown to fail through the real chain: twin, observer, arm, comparison and final status. A run
> that only declares reads 0. Each of these turns the gate false:
> - a run-time census call from the product, with the census switched on;
> - a `Site` method reached through the class;
> - a declaration from a test module's body;
> - an `exec`'d declaration;
> - the hook cleared, which reads as no count at all.
>
> The test is `tests/test_0042_inv7.py::test_r15_the_reference_arm_s_census_count_fails_through_the_real_chain`.
>
> **WHAT IT CANNOT SEE, named.**
> - The hook sees Python frames only. That is total for the census module as shipped, which is pure Python, but a
>   compiled census would read 0 silently.
> - It is IN-PROCESS. Census code in a child process is outside it, just as that child's decisions are outside the
>   observer. The harness names, derived, the measured suites that start one.
> - Its liveness is checked at the END of the run. A profiler installed and removed in the middle of the run would open
>   a window the count does not see.
> - 🔴 **The new blind spot this construction opens:** a defect in the census's declaration-time code that changes a
>   later decision is shared by all four arms, so the trace diff cannot see it. Every earlier construction ran none of
>   that code in the reference arm.
>
> The round-14 verdict neither accepted nor rejected v9.6's reading of UNINSTRUMENTED; it is silent on it. 🔴 **If
> UNINSTRUMENTED means "no census code runs in the arm", this construction fails it at import. That would make it a
> change to a frozen invariant: a new external round, not an implementation fix.** The owner chose faithfulness by
> construction over that reading. This paragraph is the claim the choice rests on.
>
> **ROUND 16: THE REVIEWER TESTED THAT CLAIM AND IT FAILED, so round 15's construction is history once the amendment below is
> accepted** (v10.0, research as the specification's author, 2026-09-24; the round-15 verdict's first finding; the owner's word
> "(3) Accepted census"). The verdict: "*the new reference arm executes the census's declaration code. A reproducible
> mutation changes a decision in all four arms while the reference observer reports zero disallowed census entries. That
> leaves the accepted INV-7 requirement for a census-free reference unmet; retaining this construction requires an explicit
> design amendment.*" The blind spot named above was real, and naming it did not bound it. The reviewer's reading of the word
> is the strict one: a census-free reference.
>
> **Why no construction is both faithful and census-free while declarations bind census objects.** Faithful by construction
> needs the real census class, which is census code in the arm. Census-free needs a non-census object, which is faithful only
> by a list (round 14's finding). **What replaces round 15's construction keeps the first property, and moves the second from
> "no census" to "no census UNDER TEST".** The reference arm's twin carries the census.py of an ACCEPTED commit T, pinned by
> digest, instead of HEAD's. HEAD's census, the instrument the other three arms carry, is then not shared by the reference.
> A mutation to it, including the reviewer's class, runs in healthy, failing and off, but not in the reference, so the trace
> diff SEES it.
>
> **Measured before any code** (dev and research, 2026-09-24, on a scratch export; both seats read the raw per-arm outputs).
> - **The mutant:** a declaration-time side effect in `declare_site`. For the site `authority.permitted`, it writes through the
>   declaring module's globals into `authority._RUNGS`, a dict defined above that module's first declaration and read by the
>   declared decision `permitted()`.
> - **The suite:** `tests/test_0011_entitlement.py`, one of the 29 named, 49 tests.
> - **The cells** (T's census.py = HEAD's today, sha16 `69beb1bb2f058d97`; the mutated copy is `153e13608e3b3818`):
>   - **0, the numerator:** off arm vs mutated off arm reads DIVERGENT, and 2 tests change outcome. So the mutant alters a
>     decision.
>   - **1, round 15's construction, mutated:** IDENTICAL across all four arms, with the reference's census-entry count at 0.
>     That is the verdict, reproduced.
>   - **2, T's census in the reference and the mutated HEAD elsewhere:** DIVERGENT. The reference passes 49 while the other
>     arms fail 2, and the first differing record is an `authority.*` record.
>   - **3, T's census, unmutated:** IDENTICAL.
>   - **4, round 15's construction, unmutated:** IDENTICAL.
>
>   The separation is cells 1 and 2, and cells 0, 3 and 4 are what make it mean something. They are committed as tests,
>   through `derive`, `run_arm` with the observer, and `compare`, with every arm's imported file asserted:
>   - the numerator: `tests/test_0042_inv7.py::test_r16_the_mutant_changes_a_decision_at_all`;
>   - the four construction cells: `tests/test_0042_inv7.py::test_r16_the_reference_census_separates_a_declaration_time_defect`.
>
> **The reference census is a TRACKED file,** `specs/evidence/0042/reference_census.py`: the census.py of commit
> `5d835e1453d9265acdbb60e3f9732ad7ebeffd2b` (the round-15 pin), sha256
> `69beb1bb2f058d97de646638ec103f799c8e8e0e7c11b2abb196a3f41800683f`.
> - `derive()` refuses a reference file off that digest.
> - `verify()` refuses a twin whose census differs from the reference by a single byte, including at the same length.
> - The twin's `Site` is the reference's class, a reload is refused in both, and the registry holds the declared object.
>
> These are in `tests/test_0042_inv7.py::test_r16_the_twin_census_is_the_reference_census_and_verify_refuses_any_other`.
>
> **Drift between HEAD's `Site` and the reference's is refused as "T must advance".** It is compared member by member by
> AST, in both directions, plus the class header. v10.0.1 said here that "any change to `Site`'s OWN definition is
> drift". **That sentence is WITHDRAWN (v11.0).** The round-16 verdict showed two changes passing it: a docstring moved below
> `__slots__`, and a docstring changed with T's text re-added later. Both passed derivation and verification while source and
> reference decisions differed. The comparison modelled the class body as a MAP, which loses order and duplicates. What
> replaces it is round 17's two routes, stated in the round-17 paragraph below. The member cells of
> `tests/test_0042_inv7.py::test_r16_a_drifted_site_is_refused_and_t_must_advance` still refuse, and formatting is still not
> drift.
>
> **A change ELSEWHERE in HEAD's census is NOT drift**, for example to a helper a `Site` method calls. It is census code
> UNDER TEST, which the reference arm does not carry, so the trace diff sees any decision it changes. A `Site` method that
> runs in the reference arm is counted by the census-entry hook. *(v10.0.1 then argued that equal member ASTs build equal
> members, from a premise about T measured by research. Round 17's realized-class route makes that premise unnecessary: it
> compares the built class itself.)*
>
> **ROUND 17: THE DRIFT CHECK READS THE DEFINITION AND THE BUILT CLASS, TWO INDEPENDENT ROUTES OF ONE RULE, "`Site` IS T'S"**
> (v11.0, research as the specification's author; the round-16 verdict's one correction). `site_drift` is the UNION of:
> - **Route A, the definition:** HEAD's whole `Site` class statement equals T's, as one `ast.dump`. It is ordered, it keeps
>   duplicates, it covers the header by field and the docstring by its position, and it carries no line numbers.
> - **Route B, the realized class:** T's and HEAD's census are each executed in a fresh module namespace inside the
>   transform (never an arm), and the two built `Site` classes are compared:
>   - the method resolution order, by name;
>   - the class attributes in both directions and in order;
>   - every value normalised: functions by their compiled code without line information (nested code included), with
>     their defaults, keyword defaults, annotations, docstrings, attributes and closures; wrapped descriptors unwrapped;
>     everything else by type and representation. *(v11.1: this HAND LIST is WITHDRAWN as incomplete. The round-17 verdict
>     showed a function's writable `__name__`, `__qualname__` and `__module__` outside it. Round 18's recursive rule
>     replaces it.)*
>   - **the class's TYPE-LEVEL attributes** (v11.0.1), which are not in `vars(Site)`: every data descriptor defined along the
>     METACLASS's method resolution order, read off each built class and compared by value (class tuples by qualified
>     name). This set is derived from the metaclass, not listed: it is 17 fields on CPython 3.12 and 3.13 and 16 on 3.10
>     and 3.11 (`__type_params__` arrives in 3.12). It includes `__name__`, `__qualname__`, `__module__`, `__doc__`,
>     `__mro__` and `__bases__`. The metaclass itself is compared by qualified name. v11.0 compared the class's dict and
>     its MRO only, so a post-class `Site.__qualname__ = …` passed both routes. Research's pre-seal read executed that
>     against the round-17 staging.
>
> **Route A cannot see a change made by code OUTSIDE the class statement** (for example `Site.__doc__ = …` after it), because
> the class statement is unchanged. Research executed that counterexample at stage 1, and route B sees it. **Route B cannot
> see an order or duplicate that builds the same object**; route A sees those. A formatting-only change is drift on neither.
> The real tree reads no drift on either route.
>
> **Cells**, each naming the route that must see it:
> - the verdict's two docstring shapes;
> - a duplicate method before the original;
> - two methods swapped;
> - four modifications after the class statement: the docstring assigned, a method's defaults replaced, an attribute added
>   by `setattr`, a method rebound, and (v11.0.1) `Site.__qualname__` and `Site.__name__` assigned;
> - a module-level name read at class creation with a different value;
> - a base in T against a decorator in HEAD.
>
> These are in `tests/test_0042_inv7.py::test_r17_site_drift_reads_the_definition_and_the_realized_class`. At the round-16
> pin, each cell fails on its own verdict assertion: the defect, not a missing name. The acceptance half is
> `tests/test_0042_inv7.py::test_r17_formatting_is_not_drift_on_either_route`. *(v11.0.1 said the class header's `keywords`
> field had no cell of its own. Round 18 added one, in
> `tests/test_0042_inv7.py::test_r18_route_b_sees_constants_closures_and_method_attributes`.)*
>
> **WHAT ROUTE B CANNOT SEE, named (v11.0.1):** it builds both classes in the TRANSFORM's context (a fresh module namespace
> in the transform's process), not in an arm's runtime context. **A post-class change CONDITIONAL on runtime state** (an
> environment variable, what else is imported, `sys.modules`) is outside the class statement, so route A cannot see it, and
> it may not run in the transform's context, so route B may not either. Building HEAD's class inside a real arm and
> comparing it there would close this. It is recorded for the next round. *(v11.1: closed at runtime by round 18's
> import-time check, below.)*
>
> **ROUND 18: ROUTE B BECOMES ONE RECURSIVE RULE, AND THE REALIZED `Site` IS CHECKED INSIDE EVERY ARM** (v11.1, research as the
> specification's author; the round-17 verdict's one correction). The verdict: route B's function normaliser omitted the
> WRITABLE `__name__`, `__qualname__` and `__module__`. The reviewer's witness renamed a method after the class statement
> and then wrote `Site.__doc__ = Site.__doc__`. That line deliberately neutralised an incidental catch (next paragraph but
> one), so both routes and `verify()` read clean while `type(S).fire.__name__` differed between source and reference.
>
> **The pattern, which has now recurred three times, and the rule that ends it.**
> - Round 16: the class body as a map.
> - Round 17: the class's type-level fields.
> - Round 17's verdict: a function's own fields.
>
> Each fix derived ONE level and listed the next. Route B now normalises ANY object by ONE recursive rule: its type's
> qualified name, plus EVERY data descriptor along its type's method resolution order, read-only ones included, each
> normalised the same way.
> - Built-in scalars are compared by `repr`, containers element by element, code objects by every non-callable `co_*`
>   field, and objects with no data descriptors by an address-free `repr`.
> - An object met again is recorded as a reference to where it was first described, so cycles end.
> - Read-only fields are followed because their values can hold writable state: a `staticmethod`'s read-only `__func__`
>   is a function whose name can be changed, and closure cells are writable.
> - The functions, wrappers, properties and cells have no case of their own. The fields compared are derived per
>   interpreter, not listed.
>
> **Exclusions, only by a named property:**
> 1. **Namespace references** (`__globals__`, `__builtins__`): T's module and HEAD's legitimately differ, because they are
>    the census under test. The acceptance cell is a census helper outside `Site` changed in HEAD, which reads no drift.
> 2. **The source-location fields of code objects** (`co_filename`, `co_firstlineno`, `co_linetable`, `co_lnotab`):
>    formatting is not drift.
> 3. **`__flags__` bit 19** (`Py_TPFLAGS_VALID_VERSION_TAG`, the type's attribute cache). Measured: on 3.10 and 3.12 a
>    bare lookup, an instance created and used, or a `hasattr` of a missing name sets it, and on 3.13 none does. Comparing
>    it read a behaviour-neutral line as drift, a false "T must advance". That is loud, but it was also incidental: it
>    "caught" two changes through the cache, not through what changed. Bit 20 (`Py_TPFLAGS_IS_ABSTRACT`) is semantic and
>    stays compared.
>
> **Cells:**
> - the verdict's witness for each of `__name__`, `__qualname__` and `__module__`, each WITH `Site.__doc__ = Site.__doc__`;
> - a function's `__type_params__`;
> - a `staticmethod`'s inner function renamed through its read-only `__func__`;
> - a closure cell changed after the class.
>
> These are in `tests/test_0042_inv7.py::test_r18_function_metadata_is_compared_by_one_recursive_rule`. The derived field
> set is asserted per interpreter by `tests/test_0042_inv7.py::test_r18_the_function_fields_compared_are_derived_per_interpreter`.
> The exclusions' acceptance halves are `tests/test_0042_inv7.py::test_r18_a_census_helper_outside_site_is_not_drift` and
> `tests/test_0042_inv7.py::test_r18_a_behaviour_neutral_use_after_the_class_is_not_drift`. The abstract bit is kept by
> `tests/test_0042_inv7.py::test_r18_the_abstract_flag_is_not_masked`. At the round-17 pin, the three witness cells, the
> type-parameter cell and the `staticmethod` cell fail on their own assertion. The closure cell passes there, because
> closure contents were already compared, so it is a regression guard, not a demonstration.
>
> **The realized `Site`, checked where it runs.** v11.0.1 named what route B cannot see: a post-class change CONDITIONAL on
> runtime state. The observer now takes, in every run of every arm (controls included), a digest of route B's description
> of the `Site` class actually imported. It does so immediately after the census is imported and before the arm's own
> intervention. The harness gate `uninstrumented:site_realized_equal` requires every digest to be equal, and names the first
> difference when they are not. Three cases:
> - census code conditional on the environment runs at import, so it is captured;
> - product code that modifies `Site` runs identically in every arm, the reference included;
> - census code that changes `Site` later is census code under test, which the trace diff and the census-entry hook see.
>
> The timing is load-bearing, and it is shown. The failing arm replaces a `Site` method by construction, so a digest taken
> at session end would differ on every real run
> (`tests/test_0042_inv7.py::test_r18_the_failing_arm_changes_site_so_the_digest_is_taken_at_import`). Through the real
> chain, a HEAD census whose post-class change is conditional on a variable the arms set turns the gate FALSE while
> `site_drift` reads no drift at transform time, and an unconditional one reads TRUE
> (`tests/test_0042_inv7.py::test_r18_the_runtime_gate_sees_a_change_the_transform_cannot`).
>
> **The INV-7 run is RE-MADE, not carried**, because the observer changed: it now also counts a census entry with no Python
> caller (`tests/test_0042_inv7.py::test_r18_a_census_entry_with_no_python_caller_is_counted`) and records the realized `Site`.
> Its figures are in the transcript committed with this version, not here.
>
> **One fact a reader must not miss:** T's census.py is byte-equal to HEAD's today (unchanged since round 8). So at this
> version the reference arm's twin is byte-identical to round 15's. **The construction differs from round 15's only when
> HEAD's census changes, and its protection is prospective**: the separating test demonstrates it, not the INV-7 run at the
> pin. **The residual, named:** a declaration-time defect present in BOTH T and HEAD is shared by all four arms. It is bounded
> by T being a commit an external round accepted, and advancing T is a reviewed act, not a constant edit. The amendment below
> states both.

> **ROUND 19: A TYPE IS DESCRIBED BY NAME ONLY IF PYTHON CODE CANNOT HAVE MADE IT, AND ROUTE B RUNS OUTSIDE THE TRANSFORM**
> (v11.3, research as the specification's author; the round-18 verdict's one correction, banked `4cc6320`, body sha16
> `37d2d04ebba57959`: "*RETURNED for one implementation correction … the design remains accepted*"). The verdict's witness
> appends `class tuple(tuple)` with an overriding `__contains__`, rebinds `Site.__slots__` to an instance of it and deletes
> the name. Both routes, `derive()`, `verify()` and the runtime gate read that as the built-in `tuple`, while
> `"site_id" in type(S).__slots__` differs between source and reference. Round 18's rule chose its branches by
> `isinstance()` and described a type in `builtins` by its NAME. The spoof variant also sets `__module__ = 'builtins'` and
> `__qualname__ = 'tuple'`, and passes every name test.
>
> **The pattern, a fourth time.** Round 18's paragraph listed three levels, each a representation trusted in place of the
> thing. The fourth is **a name trusted as an identity.** `__module__` and `__qualname__` are claims: Python code can write
> both on any class it creates. The rule now rests on a property Python code cannot fake. `Py_TPFLAGS_IMMUTABLETYPE`
> (`1 << 8`, 3.10 and later) is set on every type Python code cannot create, and an immutable type's `__module__` and
> `__qualname__` cannot be written. That covers the built-ins, and C types such as `_thread.lock` and `re.Pattern`, which
> are heap types, so "heap type" would have been the wrong property. Measured on 3.10, 3.12 and 3.13 by both seats: the
> flag is set on every built-in route B meets and clear on the spoof, a plain class and a class built by a Python
> metaclass.
> - A type is described by module and qualified name **only if it is immutable.** Every other type is described by the
>   same recursive rule as any object.
> - The scalar, sequence, set, mapping and code branches are entered only for an immutable type of that name. No
>   `isinstance()` chooses a branch.
> - An instance of a MUTABLE subclass of a built-in is described by its class, in full, and by its content read through the
>   immutable base's own methods (`tuple.__iter__`, `dict.items`, `str.__repr__`), never the subclass's.
> - `__mro__`, `__bases__`, `__base__` and the metaclass use the same identity. Every non-immutable base is described in
>   its own entry. Round 18 filtered these by `__module__ != "builtins"`, which is the forgeable test.
>
> **Route B no longer runs in the transform's process.** Round 18 executed each census inside the transform. A census
> that rebinds a built-in (`import builtins; builtins.tuple = …`) therefore rebound the transform's own built-ins, and a copy
> of `__builtins__` does not isolate, because `import builtins` returns the real module (executed). Each census is now
> executed and described in a fresh `python -I`, and its description returns as data read under 0026's strict-pairs rule.
> Inside that child, the built-ins are restored after the census runs, so the describer reads with the real ones. This
> protects the TRANSFORM. It does not protect the DESCRIPTION: the describer shares the child's process with the census it
> describes. That limit is not specific to route B. It is the trust boundary proposed after §6's table. *(v12.0: ACCEPTED by the round-19 verdict, now INV-7's stated scope.)*
>
> **Cells:**
> - the verdict's witness, the spoof, and same-named subclasses of `str` (overriding `__eq__`), `int` and `dict` (overriding
>   `get`), each through round 17's drift body, verdict first:
>   `tests/test_0042_inv7.py::test_r19_a_subclass_is_never_read_as_the_builtin_it_names`;
> - the acceptance half, an equal REAL `tuple`, not drift: `tests/test_0042_inv7.py::test_r19_an_equal_real_builtin_is_not_drift`;
> - the property itself, pinned per interpreter: `tests/test_0042_inv7.py::test_r19_the_immutable_criterion_per_interpreter`;
> - the runtime gate's reading: `tests/test_0042_inv7.py::test_r19_the_runtime_gate_reads_the_witness_and_the_spoof_as_different`;
> - a census rebinding a built-in leaves the transform untouched and `derive()`/`verify()` unchanged:
>   `tests/test_0042_inv7.py::test_r19_a_census_rebinding_a_builtin_cannot_reach_the_transform`.
>
> At the round-18 pin the five subclass cells, the gate reading and the rebinding cell fail. The acceptance cell passes
> there, as an acceptance half must. The subclass cells first used differently named classes, and those passed at the
> round-18 pin, caught by the name. The verdict's class is SAME-named, so the cells are too.
>
> **The INV-7 run is RE-MADE, not carried**, because the normaliser the runtime digest calls changed. Its figures are in
> the transcript committed with this version, not here.

> **ROUND 20: ROUTE B'S CHILD ANSWERS ON A CHANNEL THE CENSUS DOES NOT WRITE, AND THE RESOLVER READS NAMES IN THE SYMBOL
> TABLE'S SPELLING** (v12.0, research as the specification's author; the round-19 verdict's two corrections, banked `496a120`,
> body sha16 `7d2135a69dff4081`). Neither finding attacks the measurement; both are defects, which the accepted scope
> leaves in the implementation review.
>
> **F1: census output reached the child's response.** Round 19's child wrote its description to the stdout the census also
> writes. One `print("census initialized")` appended to the census made route B, `site_drift()`, `derive()` and `verify()`
> raise `JSONDecodeError`. It was new in round 19: round 18 described `Site` in-process and had no transport. It is the
> found-in-fix class: the isolation was checked for what `-I` REMOVES, not for what the child SHARES with the census.
> - The child writes its description to a response file, in a temporary directory outside the tree, at an absolute path.
>   It closes the file and then calls `os._exit(0)`, so no atexit handler and no non-daemon thread the census started
>   runs after it.
> - **A complete, well-formed response is authoritative. The exit code is diagnostic only.**
> - No response, a malformed one, one of the wrong shape, or a timeout is a NAMED "could not be described" refusal, never
>   a bare exception, and **never reported as drift**: on either side it reads "*this is not drift, and T does not
>   advance*". Round 19 reported a census whose stdout was closed as "*HEAD's Site has drifted … T must advance*", and the
>   first form of this fix still wrapped the failure under that headline (the second seat's read, before the hand-over).
> - The census's stdout and stderr are captured and ignored unless the description fails. The census can read the
>   response path from argv; that is within the accepted scope.
>
> **F2: a name the compiler adds, and a name the compiler respells.** Round 19's comprehension signature decided which
> inlined names merge by the names the enclosing block "already holds", read from the AST.
> - **The compiler adds names the AST does not hold.** A `super` read adds `__class__` to the block, so the verdict's
>   witness merged an inner `__class__` target that CPython does not merge, and the resolver refused a program that runs.
> - **Every compiler-introduced name is DERIVED, by two routes, one asserted to contain the other.**
>   - Route 1 is CPython's `symtable.c` at 3.12.3 and 3.13.15. In a comprehension's own block, the only added name is
>     `__class__` on a `super` load, besides the `.0` parameter. `__classdict__` and the dotted type-parameter names go
>     to type-parameter, annotation and class blocks.
>   - Route 2 is a census of the standard library's symbol tables: every symbol that is never a NAME token, compared
>     after NFKC normalisation as the compiler reads identifiers (PEP 3131), must be in route 1's set or be a mangled
>     private name, and `__class__` must be seen. It found none outside, over the full `Lib/` of 3.12.3 and 3.13.15.
>     **A local green was not CI's:** the box's stdlib had no `Lib/test`, and CI's did, where unnormalised spellings
>     ("Unicode", "μ") read as names without a token. It cannot see `__classdict__`, which no standard-library module
>     triggers, so it does not stand alone. It skips before 3.12, where `tokenize` keeps an f-string as one token
>     (inventoried).
> - **The compiler RESPELLS private names (found by the second seat's stage-1 read, the verdict's class widened).**
>   `symtable` spells `__p` inside class `C` as `_C__p`. The comprehension signature and the join check's lambda and `def`
>   parameter comparison both used the AST's spelling, giving three loud over-refusals:
>   - a private inner target in a method (3.12, 3.13);
>   - same-line list comprehensions with a private target (3.11, not inlined);
>   - same-line lambdas with a private parameter (every version).
>   Every comparison now uses the symbol table's spelling (CPython's mangling rule, the underscore-only class name
>   included). **The binding scan's module-level reading was measured CORRECT under mangling:** `__S` in a method is read
>   as `_C__S`, never as the module's `__S`.
> - **Named, not modelled:** a PEP 695 generic class's type-parameter scope. The join check refuses there.
>
> **Cells:**
> - F1, 19 cells, each through `derive()` and `verify()`:
>   `tests/test_0042_inv7.py::test_r20_census_output_never_reaches_the_isolated_child_s_response`.
>   - 14 accept: print variants, JSON-looking text, stderr, stdout or fd 1 closed, atexit handlers, threads, chdir.
>   - 3 refuse by name.
>   - 2 are drift, with and without output.
> - A census whose import never ends: `tests/test_0042_inv7.py::test_r20_a_census_whose_import_never_ends_is_a_named_failure`.
> - An undescribable census, on HEAD's side and on the reference's, refuses by name and never as drift:
>   `tests/test_0042_inv7.py::test_r20_an_undescribable_census_is_never_reported_as_drift`.
> - Each superseded transport fails its cell: `tests/test_0042_inv7.py::test_r20_each_superseded_transport_fails_its_cell`.
> - The verdict's seven, nesting, lambdas and mangling, end to end:
>   `tests/test_0042_scope_resolution.py::test_r20_f2_compiler_names_and_mangling_match_symtable_and_resolve`.
> - A generated corpus of 576 programs, each equal to `symtable` and resolving on 3.10 to 3.13:
>   `tests/test_0042_scope_resolution.py::test_r20_f2_the_generated_corpus_equals_symtable_and_resolves`.
> - The two superseded rules fail it: `tests/test_0042_scope_resolution.py::test_r20_f2_each_superseded_rule_fails_the_corpus`.
> - The two routes: `tests/test_0042_scope_resolution.py::test_r20_f2_route_two_finds_no_implicit_name_route_one_lacks`.
> - F2 end to end through `derive()` and `verify()`, the reviewer's "*retain end-to-end derivation controls*" on their own
>   setup (a valid helper in a product module beside a measured site). Four cells, each deriving with `verify()` clean:
>   the verdict's witness and a method calling `super(C, self)` (the implicit `__class__`), a class-private inner target,
>   and same-line lambdas with a class-private parameter (mangling):
>   `tests/test_0042_inv7.py::test_r20_a_valid_helper_beside_a_measured_decision_derives`.
>
> At the round-19 pin the round-20 cells split three ways, and the red/green transcript counts each. Some FAIL ON THE DEFECT
> ITSELF: a bare `JSONDecodeError`, a bare `TimeoutExpired`, a census failure refused as "*Site has drifted … T must
> advance*", a signature unequal to `symtable`, an unresolvable scope. Some CANNOT RUN there, because they name what round
> 20 introduced (the timeout constant, the superseded-form mutants, the two routes). The rest PASS there: the cells whose
> right answer round 19 already gave, the acceptance cells and a silent real drift. A census that raises or calls
> `sys.exit(3)` during import was already refused by round 19, but under the drift headline, so those cells FAIL there
> too.

> **ROUND 21: EVERY TEXT BOUNDARY OF THE TRANSFORM IS STATED, NOT INHERITED** (v12.1, research as the specification's author;
> the round-20 verdict's one correction, banked `3e6c072`, body sha16 `08bf83879e03eaf0`: "*F1 remains: non-UTF-8
> diagnostic output raises `UnicodeDecodeError` in derivation and verification, despite a valid response*"; F2 closed).
> Round 20 moved route B's RESPONSE off the census's stdout, but the parent still captured that stdout and stderr as TEXT,
> decoded strictly on every run, so a census printing invalid UTF-8 broke `derive()` and `verify()` before the response was
> read. The class is wider than the verdict's case. **Every place the transform turns bytes into text, or text into bytes,
> assumed an encoding it had not been told.** Three were found and closed this round.
> - **Route B's channel, both ways.** It is now bytes. The census text goes in as UTF-8 and the child reads it as UTF-8;
>   the census's stdout and stderr are decoded only to NAME a failure, with escapes, and never on success. Before, the
>   channel followed two locales, the parent's and the child's. Under a non-UTF-8 locale with UTF-8 mode off, the
>   reference census failed against itself on its own em dash.
> - **A Python source is read in the encoding IT declares**, by the interpreter's own rule (a PEP 263 cookie or a BOM,
>   else UTF-8), never by the locale's and never by assumption. *(v12.2: "by the interpreter's own rule" was FALSE, and is
>   WITHDRAWN. The rule used was `tokenize.detect_encoding`, the pure-Python tokenizer, which decodes header lines as UTF-8
>   before finding a cookie; the interpreter's C tokenizer scans them as bytes. The round-21 verdict found valid files it
>   refused. What replaces it is in the round-22 paragraph below.)* The bytes are parsed first, exactly as the interpreter
>   parses a file. A source the interpreter would refuse (an unknown encoding, an undecodable byte in a literal) is a NAMED
>   refusal, "*could not be read as Python source — this is not drift, and T does not advance*". Once the bytes parse, an
>   undecodable byte can only sit in a COMMENT, which CPython 3.10 to 3.13 import and run, measured. It is decoded with
>   replacement, which changes nothing either route reads. *(v12.5: not so from the 3.14 floor. 3.14 refuses such a byte
>   in a comment too, so no source the bytes-parse accepts holds one, and the decode is now STRICT; see the round-24
>   paragraph.)* `errors="surrogateescape"` was measured and REJECTED: `compile`
>   re-encodes a text source as UTF-8 and refuses lone surrogates.
> - **The twin declares what it is.** It is written in the encoding its OWN text declares, else UTF-8. The transform drops
>   comments, the cookie among them, so writing in the original's encoding produced a module whose bytes contradicted its
>   declaration. The manifest hashes the bytes written, not a re-encoding of them.
>
> **And a location read as content, found by CI's 3.13 lane on the first commit of this round.** From 3.13, a class holds the
> line its statement starts on as `__firstlineno__`. Route B's recursive rule (round 18) reads every class-namespace entry,
> so on 3.13 ANY comment or blank line above `class Site` read as drift, in route B and in the runtime gate, from round 18
> until this round. The refusal was loud, never silent, and no cell had ever shifted the lines ABOVE the class. It is now
> excluded by the property that already excludes a code object's location fields: it records WHERE the class was written,
> not what it is. The description is unchanged on 3.10, 3.11 and 3.12, the carried INV-7 run's interpreter included.
>
> Other data files (the manifest's JSON) are UTF-8, stated. **A gate holds the class.** Inside the transform module, the
> child's code string included, no text I/O takes the locale's encoding, and no decode, encode, read or write happens
> outside the named boundary functions. The source decode must carry its error handler. *(v12.5: reversed from the 3.14 floor: the gate now requires a STRICT decode.)* The gate is shown to flag a
> UTF-8-assuming source read.
>
> **Named, not closed:** outside the transform, the evidence modules (the INV-7 harness and observer, the binding scan,
> key derivation and others) read and write text in the locale's encoding, and read sources without their declared
> encoding. Under a non-UTF-8 locale with UTF-8 mode off, or on a source that declares another encoding or holds bytes
> invalid in it, they are unmeasured. The count, by the same AST query, is in the round-21 package.
>
> **Cells:**
> - census bytes on stdout, stderr and both, valid non-ASCII, real drift with invalid bytes, and a crash after invalid
>   bytes, each through `derive()` and `verify()`:
>   `tests/test_0042_inv7.py::test_r21_census_bytes_never_break_the_isolated_boundary`;
> - under a non-UTF-8 locale, in a child that first proves its locale is not UTF-8 and FAILS if it is (never skips):
>   `tests/test_0042_inv7.py::test_r21_derive_and_verify_hold_under_a_non_utf8_locale`;
> - the round-20 decode-on-success, as a mutant:
>   `tests/test_0042_inv7.py::test_r21_decoding_the_census_output_on_success_fails_the_byte_cells`;
> - sources in the encoding they declare (a BOM, GB18030, latin-1 and cp1252 cookies, a byte in a comment, an unknown
>   encoding), census and product, the twin compiled and RUN with the source's output:
>   `tests/test_0042_inv7.py::test_r21_a_source_is_read_in_the_encoding_it_declares`;
> - each superseded source rule fails a cell, including a UTF-8-assuming decode caught only by running the twin:
>   `tests/test_0042_inv7.py::test_r21_each_superseded_source_rule_fails_a_cell`;
> - the gate: `tests/test_0042_inv7.py::test_r21_the_transform_reads_and_writes_text_only_at_its_boundaries`, and its own
>   mutant, `tests/test_0042_inv7.py::test_r21_the_boundary_gate_flags_a_utf8_assuming_source_read`;
> - a line above `Site` is not drift on any version:
>   `tests/test_0042_inv7.py::test_r21_a_line_above_site_is_not_drift_on_any_version`, and the exclusion is shown
>   load-bearing on 3.13 (it skips before 3.13, inventoried):
>   `tests/test_0042_inv7.py::test_r21_the_class_location_exclusion_is_load_bearing_on_313`.
>
> At the round-20 pin, the round-21 cells fail on the defect itself or cannot run there, with two exceptions that pass. The
> first is the acceptance halves whose right answer round 20 already gave (valid non-ASCII output, a non-ASCII census
> comment, a UTF-8 cookie line). The second is the line-above-`Site` cells on interpreters BEFORE 3.13, where the defect
> does not exist. On 3.13 those fail at the round-20 pin with "*Site.__firstlineno__ (realized): differs*", and pass here.

> **ROUND 22: THE INTERPRETER IS THE ORACLE FOR EVERY SOURCE THE TRANSFORM READS** (v12.2, research as the specification's
> author; the round-21 verdict's one correction, banked `e915b80`, body sha16 `f07dc190bb9f85b9`: "*The previous
> diagnostic-output defect is fixed. The new source reader rejects valid Python files containing certain encoded header
> comments.*"). Round 21 found a source's encoding with `tokenize.detect_encoding`, and v12.1 called that "the
> interpreter's own rule". It is not. The pure-Python tokenizer decodes each of a file's first two lines as UTF-8 BEFORE
> it looks for a coding cookie, and raises on a byte that is not UTF-8. CPython's C tokenizer, which `import` and
> `compile` use, scans those lines as bytes. So a file with a non-UTF-8 comment in its header was refused, although
> Python runs it: a latin-1 comment above its cookie, text after the cookie on the cookie's own line, an invalid-UTF-8
> comment on line 1. **It is the pattern this specification has recorded since round 16, once more: a representation of
> the thing trusted in place of the thing, here a reimplementation of the interpreter's reading trusted in place of the
> interpreter.**
> - **The encoding is found at the byte level**: PEP 263's pattern on lines 1 and 2 as BYTES, line 2 only if line 1 is
>   blank or a comment, a BOM meaning UTF-8 and refusing any other declaration. *(v12.3: the declared NAME was looked up
>   as written, and the BOM check compared it as the codecs do. The interpreter first NORMALISES the name, so this rule
>   refused declarations Python accepts, such as `iso-latin-1` and `utf-8-unix`: the round-22 verdict. See round 23.)*
> - **That rule is a reimplementation too, so it is not trusted.** Every source's decoded text is parsed, and its syntax
>   tree, positions included, must EQUAL the tree the interpreter builds from the file's BYTES. A decode that would change
>   a literal's value or a position is a NAMED refusal, "*the transform's reading of this source disagrees with the
>   interpreter's — this is not drift, and T does not advance*". A future divergence between the byte rule and the C
>   tokenizer is therefore loud, never a wrong twin. *(v12.3: this made the interpreter the judge of every reading the
>   transform ACCEPTED, but not of its REFUSALS. A source the interpreter accepts and the byte rule refused was never
>   compared with the interpreter, so this paragraph's heading, "the oracle for every source", held for acceptance only.
>   Round 23 closes the other direction.)* Comments are not in the tree, so the replacement of a comment's
>   undecodable byte (v12.1) does not disturb it; both parses measure columns on UTF-8.
> - **The twin's write** uses the same rule, and the transform no longer uses `tokenize.detect_encoding` anywhere.
>
> **Cells:**
> - a GENERATED header corpus, crossing line 1 (absent, blank, shebang, an ASCII comment, a comment in the declared
>   encoding, an invalid-UTF-8 comment, code), the cookie's form (none, emacs, vim, emacs with a mode, a cookie followed
>   by non-ASCII text), the declared encoding (UTF-8, latin-1, cp1252, GB18030), the body's actual encoding, and a BOM. The
>   ORACLE per program is the interpreter: the transform accepts iff `compile` accepts the bytes, and reads a non-ASCII
>   literal's value as `exec` does. The interpreter both accepts and refuses within it:
>   `tests/test_0042_inv7.py::test_r22_the_source_reader_agrees_with_the_interpreter_over_the_header_corpus`;
> - the verdict's shapes, census and product, through `derive()` and `verify()`, with the product twins RUN:
>   `tests/test_0042_inv7.py::test_r22_a_header_the_interpreter_accepts_derives_and_verifies`;
> - the guard shown to FIRE, on a planted wrong reading (latin-1 forced on a UTF-8 source holding "café"):
>   `tests/test_0042_inv7.py::test_r22_the_interpreter_guard_fires_on_a_wrong_reading`;
> - each superseded reading fails (round 21's `detect_encoding`, line 2 examined after code, the guard removed):
>   `tests/test_0042_inv7.py::test_r22_each_superseded_reading_fails`;
> - the gate: `tests/test_0042_inv7.py::test_r22_the_transform_never_uses_tokenize_detect_encoding`.
>
> At the round-21 pin, the round-22 cells fail ON THE DEFECT (the corpus disagrees with the interpreter; the verdict's shapes
> are refused as unreadable; the guard does not fire; the gate finds `detect_encoding`), or CANNOT RUN there (the two
> mutants whose anchors round 22 introduced). One passes: the superseded-`detect_encoding` mutant. The pin already holds that
> rule, so the mutant's corpus fails there as it must, and the red/green transcript lists it apart.

> **ROUND 23: THE INTERPRETER JUDGES THE TRANSFORM'S REFUSALS AS WELL AS ITS READINGS** (v12.3, research as the
> specification's author; the round-22 verdict's one correction, banked `0f8748a`, body sha16 `528ac5df80d1ad9c`: "*The
> previous header-comment cases are fixed. A new regression rejects valid encoding declarations such as `iso-latin-1` and
> `utf-8-unix` that round 21 accepted.*"). Round 22 replaced `tokenize.detect_encoding` with a byte-level rule, and that
> rule dropped a step the pure-Python tokenizer had right. CPython NORMALISES a declared encoding's name before looking it
> up: it takes the first twelve characters, lower-cased, with `_` read as `-`, maps `utf-8` and any `utf-8-…` to UTF-8,
> maps the `latin-1`, `iso-8859-1` and `iso-latin-1` families (each alone or followed by `-…`) to ISO-8859-1, and
> otherwise keeps the name as written. The byte rule looked the name up as written, so it refused declarations the
> interpreter accepts. **Nothing caught it, for two reasons**, both now closed:
> - **The guard judged only one direction.** A reading the transform accepted was compared with the interpreter; a
>   refusal was not. A refusal that follows the interpreter's own acceptance is now NAMED as the transform's disagreement
>   with the interpreter ("*the interpreter accepts this source and the transform cannot read it*"), never as a source
>   that is not Python. A source the interpreter itself refuses keeps "*could not be read as Python source*".
> - **The corpus enumerated the header's structure, but took the declared NAME from a hand list of four canonical
>   names.** The name is input with its own grammar, because the interpreter rewrites it. The name domain is now
>   DERIVED from two sources: every name the codecs know, spelled four ways with five tails; and the interpreter's own
>   folded families, with both separators, several tails and several casings, including case changes past the
>   twelve-character cut. Each name is crossed with a BOM and without one. The oracle stays the interpreter's `compile`,
>   and the assertion stays: the transform accepts exactly when the interpreter does, in BOTH directions.
>
> The normalisation is a mirror of the interpreter's rule, one step per line, and returns the name as written when no
> family matches. The rule's text was measured identical on 3.10 to 3.13; only the source path in its docstring moved.
> A BOM now requires the NORMAL name to be UTF-8, as the interpreter requires: a BOM with `utf8` is refused by both.
>
> **Cells:**
> - the transform accepts exactly when the interpreter does, over every derived name with and without a BOM, on every
>   interpreter, with a literal read the same:
>   `tests/test_0042_inv7.py::test_r23_the_source_reader_agrees_with_the_interpreter_over_every_cookie_name`;
> - the mirror equals the standard library's own copy of the rule over the same domain (secondary; the interpreter is
>   the judge): `tests/test_0042_inv7.py::test_r23_the_normaliser_is_the_interpreters_over_the_name_domain`;
> - controls stated as SETS: round 22's reader disagrees on exactly the derived set of names the interpreter accepts
>   and the codecs do not know as written, and round 21's reader on none of them:
>   `tests/test_0042_inv7.py::test_r23_the_controls_are_sets_round_22_fails_exactly_the_folded_names_round_21_passes_them`;
> - each step of the mirror is load-bearing: `tests/test_0042_inv7.py::test_r23_each_step_of_the_normaliser_is_load_bearing`,
>   and the twelve-character cut is shown EQUIVALENT by running it:
>   `tests/test_0042_inv7.py::test_r23_the_twelve_character_cut_is_an_equivalent_mutant`;
> - the BOM comparison, tested where it can fail. Through the reader, the interpreter's own refusal of a BOM with a
>   non-UTF-8 name comes first and masks it:
>   `tests/test_0042_inv7.py::test_r23_a_bom_is_compared_by_the_normal_name_at_its_own_site`;
> - a refusal after the interpreter's acceptance is named a disagreement:
>   `tests/test_0042_inv7.py::test_r23_a_refusal_after_the_interpreter_accepts_is_named_a_disagreement`.

> **ROUND 23'S VERDICT: THE IMPLEMENTATION IS ACCEPTED** (v12.4, research as the specification's author; the round-23
> verdict, banked in the coordination repo at `7433bd9`, body sha16 `bc6e41b317fbafce`: "Round 23 is finished:
> **ACCEPTED**. The round-22 regression is fixed; no new findings."). Rounds 6 to 22 each returned the implementation,
> and every finding they raised against it is a row in the Review closure ledger at the end of this document, with
> evidence a reader can run. The corrections to package text that rounds 6 to 9 also asked for are not findings against
> the implementation; each is recorded in its round's verdict row, with its disposition. **What was accepted:**
> - the code at pin `d00cd868d455de175d8655f275f387f799cd7ebc`, reviewed as the round-23 package (sha256
>   `462713e4a09c094ac36865e7a9e53b29169c43af926f92c9eefbf4a1fb657dbc`);
> - judged against this document's accepted design: v7's frozen scope, as amended by acceptance at round 16 (the meaning
>   of UNINSTRUMENTED) and at round 19 (INV-7's scope), with the implementation notes above;
> - on the regimes that package evidenced: CPython 3.10, 3.11, 3.12 and 3.13 in CI, and CI's pydantic 2.7.0 floor
>   lane. The reviewer's own run of the suite read 4,136 passed and 35 skipped, each skip explained, with no failures.
>
> **What the acceptance does not cover:**
> - **the limits this document names, which stay named.** INV-7 is established against census code that changes
>   behaviour, not census code written to attack the measurement (§6, the round-19 scope). And round 21's limit outside
>   the transform stands: the evidence modules still read and write text in the locale's encoding ("Named, not closed",
>   in the round-21 paragraph).
> - **an interpreter the package did not run.** The evidence layer reads interpreter internals: symbol tables, a
>   class's namespace, and the tokenizer's reading of a source. A later interpreter is therefore new ground, not
>   covered ground. Measured on CPython 3.14.7 at this pin on 2026-09-26: cells in `tests/test_0042_inv7.py` and
>   `tests/test_0042_scope_resolution.py` fail on changes in exactly those internals (a class's `__annotate__`,
>   implicit names such as `__conditional_annotations__`, the symbol table of a comprehension, and invalid bytes in a
>   comment). Running this evidence on a later interpreter is a change to accepted evidence, to be reviewed as one. *(v12.5: round 24 is that review.)*

> **ROUND 24: THE EVIDENCE ON PYTHON 3.14 OR NEWER** (v12.5, research as the specification's author; the owner's decision
> of 2026-09-27 to raise the product's floor to Python 3.14). This is the change the limit above names, for review as
> one. No frozen invariant's text changes. Four changes in 3.14 reach the evidence layer, each measured on CPython 3.14.7
> against 3.12.3:
> - **Reading annotations runs code.** On 3.14 annotations are lazy. Defining a class or a function runs none of its
>   annotation code; READING `__annotations__` calls `__annotate__`. Route B's describer read annotations, so on 3.14 it
>   entered census code in the reference arm: 7 entries, into the compiler-generated `__annotate__` functions of
>   `Site`'s methods. Under the census's `from __future__ import annotations` those functions return the declared
>   strings, so no census logic ran, but UNINSTRUMENTED counts every entry into census code. The describer now never
>   reads a class's `__annotations__` or `__annotate__`: a class's annotation content is read from its namespace, and a
>   function's `__annotate__` is described by the recursive rule and never called. *(v12.6: annotations were one family of
>   lazy value; PEP 695's type metadata was another, and was still read. See the round-25 paragraph.)* The keys that an annotation read
>   CREATES in a class namespace (a derived `__annotations_cache__`, `__annotate_func__` = None, `__annotations__` = {})
>   are normalised by value, so who read a class first is not drift. An annotation ASSIGNED to a class, which 3.14
>   stores in `__annotations_cache__` alone, is compared. **Stage-2 finding F1:** the first build dropped that cache
>   unconditionally and read an assigned change as no drift. **Named limit:** annotations that code has already
>   materialised and then mutated in place are not seen, because the cache cannot be read without the read that runs
>   the code.
> - **A comment may no longer hold a byte invalid in the declared encoding.** 3.14 refuses such a source; 3.10 to 3.13
>   accepted it. The transform already refused what the interpreter refuses. The cells now take their expectation from
>   the running interpreter, and the decode is STRICT, as the boundary gate requires, since no source the bytes-parse
>   accepts can hold such a byte. Round 21's `detect_encoding` reader agrees with 3.14 over the whole header corpus, so
>   it is retired as a mutant, on that measurement.
> - **New scopes.** 3.14 gives annotations scopes of their own. Under the floor, PEP 695's type-parameter, type-alias
>   and type-variable scopes (3.12 and later) become legal product syntax. The resolver's named boundary rested on a
>   3.10 floor and is retired. The join now accepts only the block kinds it models and refuses any other by name, so a
>   block kind a later interpreter adds cannot reach an answer. Shown RED first: with the join made total, the round-23
>   cursor refused every program in the generated corpus on 3.14 and answered none silently. A read the interpreter
>   resolves at evaluation from a class namespace, else the globals (`LOAD_FROM_DICT_OR_GLOBALS`), sees every later
>   binding in the class body and anything set on the class afterwards. It has no static answer, so it is refused as
>   dynamic, and the pairing oracle scores any other answer on such a read as wrong. *(v12.6: incomplete. The same
>   class-namespace read can fall back to an enclosing function's closure, `LOAD_FROM_DICT_OR_DEREF`, which the oracle
>   scored as silent; both opcodes count from round 25.)* **Stage-2 finding F2:** the oracle
>   first scored one direction only, so a plain answer there read as right. A census use inside any annotation or type
>   scope is refused by name. *(v12.6: in the lazy regime only. Under the future import an annotation is a string, and a
>   function-local or non-simple-target annotation is never evaluated; there the use is data and is preserved. See the
>   round-25 paragraph.)* The implicit names `.format` and `__conditional_annotations__` join route 1.
> - **The INV-7 run is RE-MADE on 3.14, not carried.** The run carried since round 19 was a CPython 3.12.3 fact. It is
>   regenerated at the pin on CPython 3.14.7, the build CI runs; its verdict, gates, census-entry count and twin digest
>   are in `specs/evidence/0042/inv7_transcript.txt`. On 3.14.7 the twin digest is the value 3.11.16 and 3.13.15 already
>   gave (3.12.3 gives another: the digest is a fact about an interpreter, and the run states which).
>
> **Cells:**
> - reading annotations:
>   - `tests/test_0042_inv7.py::test_py314_describing_a_site_runs_no_annotation_code`;
>   - `tests/test_0042_inv7.py::test_py314_describing_a_future_import_site_runs_none_of_its_code`;
>   - `tests/test_0042_inv7.py::test_py314_describing_a_site_leaves_its_vars_unchanged`;
>   - `tests/test_0042_inv7.py::test_py314_another_reader_of_the_annotations_is_not_drift`;
>   - `tests/test_0042_inv7.py::test_py314_an_assigned_class_annotation_is_drift`;
>   - `tests/test_0042_inv7.py::test_py314_a_census_dict_carrying_an_annotation_key_is_still_compared`;
>   - each rule load-bearing: `tests/test_0042_inv7.py::test_py314_each_annotation_rule_is_load_bearing`;
> - new scopes:
>   - `tests/test_0042_scope_resolution.py::test_py314_a_class_scope_read_is_answered_dynamic_never_statically`, with
>     its acceptance half `tests/test_0042_scope_resolution.py::test_py314_a_top_level_generic_class_base_is_answered_lexically`;
>   - `tests/test_0042_scope_resolution.py::test_py314_a_site_used_in_a_lazy_position_is_refused_by_name`;
>   - `tests/test_0042_inv7.py::test_py314_a_census_consult_in_a_lazy_position_is_refused_not_transformed`.

> **ROUND 25: LAZY VALUES ARE NEVER EVALUATED, AND A STRING ANNOTATION IS DATA** (v12.6, research as the specification's
> author; the round-24 verdict's two corrections, banked in the coordination repo at `6e941ac`, body sha16
> `28f0959c540666ea`). Round 24 made the evidence non-executing for one family of lazy value and one annotation regime.
> The verdict showed each rule narrower than the property it was written for. **We scoped round 24 from the tests that
> failed on 3.14, not from 3.14's changes to the language, and a feature no test yet exercised was outside that scope.**
> - **A string annotation is data (R24-1).** Under `from __future__ import annotations` every annotation is stored as a
>   string. The transform rewrote a census call inside one, so the twin's `f.__annotations__["x"]` read `123` where the
>   source's read `S.fire(123)`, a decision reading it changed, and `verify()` passed because it replayed the transform's
>   rule. Annotations are now classified by EVALUATION REGIME:
>   - under the future import, every annotation is a string, and the transform never rewrites inside it;
>   - a function-local annotation, and an annotation whose target is not a bare name (`o.a: A = v`, `d[k]: A = v`), is
>     never evaluated on 3.14, and is also preserved;
>   - every other annotation is evaluated lazily, and a census use there is refused, as in round 24.
>
>   `verify()` checks the twin's annotations against the source's, all of them, as syntax trees, without asking the
>   classifier. The binding scan counts only what runs in a function's own frame: not a data annotation, not the
>   function's own defaults or decorators, which run in the enclosing frame. It LISTS each data-annotation site call
>   instead of counting it, so an empty list says what was examined.
> - **Lazy type metadata is never evaluated (R24-2).** A PEP 695 type parameter's bound, constraints and default, and a
>   type alias's value, are lazy on 3.14. Reading `__bound__`, `__constraints__`, `__default__` or `__value__` runs its
>   evaluator. Each is paired with an `evaluate_<name>` attribute that holds the evaluator (a function, or None when the
>   value is not lazy), and reading that attribute runs nothing. The describer now reads the evaluator, describes it by
>   the recursive rule by its code, and never calls it. The pairing is derived from the attributes the type carries,
>   not from a list, so a changed lazy definition still describes differently. *(v12.7: "a function, or None when the
>   value is not lazy" is FALSE of the constructor regime. `typing.TypeVar('T', bound=X)` and the other constructors
>   hold a constant evaluator around a value that is already there. Treating every callable evaluator as lazy left
>   those values out of the comparison. See the round-26 paragraph.)*
> - **Three further corrections, found building these:**
>   - a classmethod's or staticmethod's wrapper stores annotation data in its own namespace when read, so the describer
>     no longer reads it there;
>   - an object created during a description is held until the description ends, so a later object at the same address
>     cannot read as a reference to it;
>   - the oracle's dynamic reads include the closure fallback (`LOAD_FROM_DICT_OR_DEREF`), the verdict's observation N1,
>     and its corpus now reads declared type parameters and enclosing-function closures.
> - **Named limit, not closed:** a MODULE reached by a description is not described without side effects. Reading an
>   unannotated module's `__annotate__` writes None into its namespace. The real census's `Site` reaches no module
>   (measured). *(v12.8: CLOSED. A module is now refused, and the refusal is decided from its type before anything is
>   read, so it is never touched. See the round-27 paragraph.)*
> - **The INV-7 run is CARRIED from round 24, and measured as such, not argued.** The twin derived at the round-25 commit
>   by the transcript's own recipe on CPython 3.14.7 gives the transcript's digest over the same 60 files, and route B's
>   description of the reference census's `Site` and HEAD's is unchanged by round 25's describer changes.
>
> **Cells:**
> - a string annotation is data:
>   - `tests/test_0042_inv7.py::test_r25_the_reviewers_cases_end_to_end_the_twin_reads_the_sources_annotations`;
>   - `tests/test_0042_inv7.py::test_r25_every_annotation_position_by_regime_is_preserved_or_refused_as_the_compiler_evaluates_it`;
>   - `tests/test_0042_inv7.py::test_r25_rewriting_under_the_future_import_is_caught_by_verifys_independent_check`;
>   - `tests/test_0042_evidence.py::test_r25_the_binding_scan_counts_what_runs_in_the_body_and_lists_annotation_calls`;
>   - `tests/test_0042_evidence.py::test_r25_a_nested_definitions_decorator_and_default_bind_the_enclosing_frame_not_the_nested_one`;
> - lazy type metadata:
>   - `tests/test_0042_inv7.py::test_r25_describing_lazy_type_metadata_runs_no_census_code`;
>   - `tests/test_0042_inv7.py::test_r25_a_changed_lazy_definition_still_describes_differently`;
>   - `tests/test_0042_inv7.py::test_r25_a_bare_type_parameter_is_read_eagerly_not_marked_lazy`;
> - the wrapper and the held object:
>   - `tests/test_0042_inv7.py::test_r25_describing_a_wrapper_writes_nothing_runs_nothing_and_is_stable`;
>   - `tests/test_0042_inv7.py::test_r25_every_described_object_is_held_until_the_description_ends`;
> - the closure fallback:
>   - `tests/test_0042_scope_resolution.py::test_r25_a_namespace_else_closure_read_is_refused_by_name_and_the_oracle_counts_it_right`.

> **ROUND 26: AN EAGER VALUE IS READ; ONLY A LAZY ONE IS LEFT UNEVALUATED** (v12.7, research as the specification's
> author; the round-25 verdict's one correction, banked in the coordination repo at `619f710`, body sha16
> `cbc0edc424fb6de5`). A type parameter or type alias can be made two ways on 3.14, and round 25's rule was measured on
> only one. **PEP 695 syntax** (`def f[T: X]`, `type A = X`) defers its expression: its `evaluate_<name>` holds a
> compiler-generated FUNCTION. **The ordinary constructors** (`typing.TypeVar('T', bound=X)`, a constraint or a
> default, `ParamSpec` and `TypeVarTuple` defaults, `typing.TypeAliasType('A', X)`) take a value that already exists:
> their `evaluate_<name>` holds a CONSTANT evaluator around it, which is callable but defers nothing. Round 25 treated
> every callable evaluator as lazy, so it left those values out of the comparison, and it described the constant
> evaluator by an address-free representation that names a held class but not its contents. A class held that way
> could change a decision while both routes read no drift (the verdict: 6 constructor forms, `fire` 1 → 2,
> `site_drift` empty). The evaluator now decides by its KIND, and every kind is named:
> - a Python FUNCTION: the value is lazy; the function is described by the recursive rule and never called;
> - the CONSTANT evaluator: the value is eager and is READ and described like any other field. Its type is taken from
>   the running interpreter by identity, never by name, and the evidence refuses to load if that type could be confused
>   with a function (if it is one, or carries data descriptors);
> - None: the value is read as it is;
> - anything else: a named refusal, never drift, because the value cannot be described faithfully without calling it.
>
> The real census holds no such value, so the carried INV-7 run is unaffected: the `Site` the arms import still reads
> the recorded `site_realized` digest.
>
> **Cells:**
> - a changed eager value, as a held class and as a held function, is drift in every constructor form:
>   `tests/test_0042_inv7.py::test_r26_a_changed_eager_value_behind_the_constant_evaluator_is_drift`;
> - reading an eager value runs no census code *(v12.8: this cell showed it only for held values without display code; a
>   held class with a display metaclass ran census code through the constant evaluator's `repr`. See the round-27
>   paragraph)*:
>   `tests/test_0042_inv7.py::test_r26_reading_an_eager_value_runs_no_census_code`;
> - the regime fact the rule rests on, in the test only (the evaluator returns the supplied value):
>   `tests/test_0042_inv7.py::test_r26_the_constructor_regimes_evaluator_holds_the_supplied_value`;
> - any other evaluator is refused by name:
>   `tests/test_0042_inv7.py::test_r26_any_other_evaluator_is_refused_by_name_never_read_as_lazy_or_eager`;
> - an interpreter where the kinds could be confused refuses at load:
>   `tests/test_0042_inv7.py::test_r26_the_constant_evaluator_type_refuses_an_interpreter_where_it_would_be_ambiguous`;
> - each rule is load-bearing, round 25's callable rule among the mutants:
>   `tests/test_0042_inv7.py::test_r26_each_evaluator_rule_is_load_bearing`.

> **ROUND 27: THE DESCRIPTION RUNS NO DISPLAY CODE, AND STATE IT CANNOT READ IS REFUSED** (v12.8, research as the
> specification's author; the round-26 verdict's one correction, banked in the coordination repo at `034ca1e`, body
> sha16 `daa579e450efcd14`, and two gaps of the same class found in the second seat's stage 2 and fixed within the
> round). **All three are one property, "the description neither executes nor misses a held value", carried to a path
> it had not reached.**
> - **The last-resort `repr` ran code (R26-1).** An object with no data descriptors fell to an address-free `repr()`,
>   and `repr` is code. The constant evaluator's own `repr` formats the value it holds, so a held class with a display
>   metaclass ran census code during description: in six constructor forms, through both the describer and the
>   observer, a decision changed from 0 to 1. Such an object is now described by what the garbage collector says it
>   holds (`gc.get_referents`, which visits its references in C and executes nothing):
>   - the CONSTANT evaluator is described through its one referent, the held value, so that value stays visible even
>     where no value/evaluator pair is established;
>   - a Python class with no C base besides `object` is described by its type and its referents, never its `repr`;
>   - a `repr` is trusted only where it cannot dispatch into Python: the type's own C slot, holding nothing but scalars;
>   - anything else is a named refusal.
>
>   *(v12.9: one more path formatted an object. The type-level description of a mutable base evaluated `repr` as a
>   lookup default, which ran a base's metaclass display method (the round-27 verdict's R27-1). And any attribute lookup
>   can run Python code. See the round-28 paragraph.)*
> - **State held in C was silent.** An object whose state lives in a C structure that no data descriptor, base content
>   or referent exposes read as unchanged when that state changed: a random-number generator reseeded, and six common
>   standard-library types (`array.array`, `io.StringIO`, `io.BytesIO`, `collections.deque`,
>   `collections.defaultdict`, a `hashlib` hash) holding different contents. This was measured SILENT at every pin
>   back to round 23's accepted one. The description now FAILS CLOSED: a type whose C bases add storage it does not
>   expose is refused by name, unless it is on an explicit list whose storage the description is shown to read. That
>   list comprises:
>   - the interpreter's own descriptor, function, code and type objects, whose state is fixed by the identity they show;
>   - `TypeVar`, the other type-parameter types and generic aliases, whose lazy parts round 26's rule decides;
>   - a lock and `itertools.count`, through their own C `repr`;
>   - readers, each calling the BASE type's own C method so that no override runs: `deque`'s items, `defaultdict`'s
>     items, `array`'s values, and `StringIO`'s and `BytesIO`'s contents and position. *(v12.9: contents and position
>     were not the whole state. A `StringIO`'s newline setting, and an outstanding buffer export on a `BytesIO` or an
>     `array`, read as unchanged although they change behaviour (R27-2). See the round-28 paragraph.)*
>
>   Coverage is decided from the type BEFORE anything is read, so a refused object is never touched. A MODULE is
>   refused, which closes the round-25 limit, and so is a held module-level builtin, whose `__self__` is its module.
>   Over twenty stateful standard-library types, none is now silent: seven are read and thirteen refused, loudly.
>   *(v12.9: true of those twenty as that sweep varied them, by content. Equal-content objects of the reader types
>   that differ in configuration or export state were silent: R27-2.)*
>
> **Named limits, not closed:**
> - the garbage collector's view of an object is only as complete as its type's traversal. A C type whose `repr` or
>   state uses a member its traversal does not visit is not fully seen;
> - a C type on the list is trusted to expose all its storage, and the list is not a proof;
> - annotations materialised and then mutated in place remain unseen, as before.
>
> The real census reaches none of the refused kinds, so the carried INV-7 run is unaffected: the `Site` the arms import
> still reads the recorded `site_realized` digest.
>
> **Cells:**
> - no held display code runs, in seven forms, through both callers:
>   `tests/test_0042_inv7.py::test_r27_describing_runs_no_held_display_code`;
> - an unpaired constant evaluator keeps its value visible and runs nothing:
>   `tests/test_0042_inv7.py::test_r27_an_unpaired_constant_evaluator_keeps_its_value_visible_and_runs_nothing`;
> - only a C type's own `repr` slot is trusted:
>   `tests/test_0042_inv7.py::test_r27_only_a_c_types_own_repr_slot_is_trusted_on_a_c_based_leaf`;
> - state no field exposes is refused, never read as equal:
>   `tests/test_0042_inv7.py::test_r27_state_a_c_base_holds_and_no_field_exposes_is_refused_never_read_as_equal`;
> - each reader's state change is drift, and no override is called:
>   `tests/test_0042_inv7.py::test_r27_a_reader_types_state_change_is_drift_and_no_override_is_called`;
> - a module is refused before it is touched:
>   `tests/test_0042_inv7.py::test_r27_a_module_is_refused_before_it_is_touched`;
> - the real `Site` describes with zero refusals:
>   `tests/test_0042_inv7.py::test_r27_the_real_site_describes_with_zero_refusals`;
> - each leaf rule is load-bearing: `tests/test_0042_inv7.py::test_r27_each_leaf_rule_is_load_bearing`.

> **ROUND 28: THE DESCRIPTION LOOKS NOTHING UP, AND WHAT IT CANNOT AVOID RUNNING IS STOPPED** (v12.9, research as the
> specification's author; the round-27 verdict's two corrections, banked in the coordination repo at `d2f3730`, body
> sha16 `3f32ba18adf3b9a4`, with a wider class found by the second seat's stage 1 and three test gaps found by its stage
> 2, all fixed within the round). **Round 27's property, "the description neither executes nor misses a held value",
> had been carried to formatting and to contents. Round 28 carries it to ATTRIBUTE LOOKUP and to every STATE CHANNEL
> of a reader's type.**
> - **Display code still ran through a lookup default (R27-1).** The type-level description of a mutable base read its
>   name as `getattr(base, "__qualname__", repr(base))`. Python evaluates the default first, so a base whose metaclass
>   defines a display method ran it: through both the describer and the observer, a decision changed from 0 to 1.
> - **The class is attribute lookup, not formatting (stage 1).** Reading a Python `property`, or reading any attribute
>   of an object whose type (or metaclass) defines `__getattribute__`, runs that type's Python code. Measured at round
>   27's pin through both callers, with no refusal:
>   - a held instance's property: 1 call;
>   - `Site`'s metaclass property: 1 call;
>   - a held instance's `__getattribute__`: 1 call, even when reading a C slot;
>   - `Site`'s metaclass `__getattribute__`: 23 calls;
>   - a held class's metaclass `__getattribute__`: 18 calls.
> - **The description now performs no attribute lookup on anything it describes:**
>   - a type's fields are read through `type`'s own getsets;
>   - an instance's fields are read by calling the C member or getset descriptor that defines them directly, found by
>     static lookup along the type's MRO;
>   - a PYTHON data descriptor is never called. It is recorded as such and described through its type: a property's
>     getter code is part of the type's description, and the state it would compute from is described where it lives
>     *(v12.10: not where a subclass SHADOWS the name of the descriptor that exposes that state. The name then resolves
>     to the shadow, and the storage behind it was never read (the round-28 verdict's R28-1). See the round-29
>     paragraph.)*;
>   - the checks that inspected objects (`isinstance`, the data-descriptor test, static lookup) were replaced where they
>     could dispatch;
>   - a C getter that itself looks a name up (a descriptor's `__qualname__`, through its class's metaclass) is not
>     called when that metaclass is Python-defined. The same name is formed from `type`'s own getset instead, and the
>     real census's descriptions do not move.
> - **What no list can promise is ENFORCED: the guard.** The description runs under a trace function that REFUSES the
>   first Python frame the describer did not write, at the frame's `call` event, before its first line runs. The
>   refusal is a `BaseException`, so the describer's own `except Exception` handlers cannot catch it. Garbage
>   collection is paused for the window, so an unrelated object's finalizer cannot land inside it. And the guard must
>   still be installed when the description returns: a description it did not watch to the end is refused. A census
>   `Site` that needs its own code run to be described is REFUSED, never described by running it.
> - **A reader now reads every state channel of its type (R27-2).** A `StringIO` also reads its newline setting (from
>   its pickle state). A `BytesIO` or an `array` also reads an EXPORT bit: whether an object of the exporting type
>   (`BytesIO`'s buffer object, a `memoryview`'s managed buffer, `pickle.PickleBuffer`, taken by identity at import)
>   refers to it. The second seat measured that bit tracking behaviour through release and a kept slice. A getter that
>   RAISES is a state, recorded by the exception's type: a closed `StringIO`'s `newlines` raised and crashed round 27's
>   describer, which the round-28 oracle found. Completeness is judged DATA TO DATA:
>   - over a corpus of instances per reader type, any two that the type's pickle state, its C getsets and members, or a
>     trial-resize export probe tell apart must describe differently;
>   - every channel must vary somewhere, or be a declared constant with its value asserted;
>   - the second seat's pair (a universal-newline `StringIO` after `x\n` versus `x\r\n`: equal pickle state, different
>     `newlines`) stays drift on every route. That pair is why pickle state alone is not the oracle.
>
> **Named limits, not closed:**
> - a refusal that C code swallows (a finalizer's error handling, a getter that clears errors) also unsets the trace
>   function, so frames after that point in the same window are not stopped. The description is still refused, but code
>   after the swallow ran;
> - the guard knows its own frames by their code's file name. Code compiled under the describer's file name passes it,
>   which a test uses deliberately. A census built to forge that is an attack on the measurement, outside the accepted
>   round-19 scope;
> - an export held as a raw buffer by a C extension, with no exporting object the description can see, is not seen;
> - the reader oracle is a LIST of known state channels, not a proof that a type has no other;
> - round 27's limits stand: the garbage collector's traversal, the trusted list, and annotations mutated in place.
>
> The real census reaches none of this, so the carried INV-7 run is unaffected: the `Site` the arms import still reads
> the recorded `site_realized` digest, `1826c42a…`.
>
> **Cells:**
> - an inherited base's display code does not run, through both callers, and a mutable base is still described in
>   full:
>   - `tests/test_0042_inv7.py::test_r28_describing_an_inherited_base_runs_no_display_code`;
>   - `tests/test_0042_inv7.py::test_r28_a_mutable_base_is_still_described_in_full`;
> - no attribute lookup on what is described, in every stage-1 shape, through both callers:
>   `tests/test_0042_inv7.py::test_r28_describing_performs_no_attribute_lookup_on_what_it_describes`;
> - a property is never called and is still described by its code, and an evaluator served by a property is refused:
>   - `tests/test_0042_inv7.py::test_r28_a_property_never_called_is_still_described_by_its_code`;
>   - `tests/test_0042_inv7.py::test_r28_an_evaluator_served_by_a_property_is_refused_and_never_called`;
> - equal content with different configuration or export state is drift, on all three routes:
>   `tests/test_0042_inv7.py::test_r28_equal_content_with_different_configuration_or_export_is_drift`;
> - every reader state channel is drift:
>   `tests/test_0042_inv7.py::test_r28_every_reader_state_channel_is_drift`;
> - the guard:
>   - it refuses before census code runs: `tests/test_0042_inv7.py::test_r28_a_c_getter_that_would_run_census_code_is_refused_before_it_runs`;
>   - a second entry after a refusal is stopped too: `tests/test_0042_inv7.py::test_r28_a_second_entry_after_a_refusal_is_stopped_too`;
>   - a description it did not watch to the end is refused: `tests/test_0042_inv7.py::test_r28_a_description_the_guard_did_not_watch_to_the_end_is_refused`;
>   - collection is paused inside the window: `tests/test_0042_inv7.py::test_r28_collection_is_paused_inside_the_guarded_window`;
>   - unrelated garbage does not land inside the window: `tests/test_0042_inv7.py::test_r28_unrelated_garbage_cannot_land_inside_the_guarded_window`;
> - each rule is load-bearing, each mutant failing for its NAMED reason:
>   `tests/test_0042_inv7.py::test_r28_each_rule_is_load_bearing`.

> **ROUND 29: STORAGE IS READ THROUGH THE CLASS THAT OWNS IT, AND WHAT NO ACCESSOR REACHES IS REFUSED** (v12.10,
> research as the specification's author; the round-28 verdict's one correction, banked in the coordination repo at
> `c178767`, body sha16 `8888d024c89724ac`, with two further members found by the second seat's stage 1 and a gap in the
> same class found while building the fix, all fixed within the round). **Round 28 made the description run nothing. In
> doing so it read each field only through the first descriptor that field's NAME resolves to, and whatever that name
> SHADOWS went unread.** The same state was then described identically for two different values:
> - **The verdict's three forms (R28-1):** a base's slot shadowed by a subclass property, the instance dictionary
>   shadowed by a property named `__dict__`, and a base's slot shadowed by an ordinary class attribute. The first two were
>   regressions of round 28 (round 27 had called the property and so read the state); the third was older.
> - **Two more, found by the second seat:** a slot declared again with the same name in a subclass (silent since before
>   round 27), and a reader type's C getset shadowed by a subclass property (a `StringIO` subclass hiding `newlines`, the
>   newline types it has seen).
> - **The correction:**
>   - storage is enumerated by the class that DECLARES it. For every class in the MRO, each C member and getset
>     descriptor in that class's own dictionary is read by calling that descriptor directly;
>   - where the field's name resolves to something else, an extra entry names the owning class and carries the value, so
>     an unshadowed object describes exactly as before;
>   - the instance dictionary is read through the `__dict__` descriptor (a getset, or for some interpreter types, such as a
>     module or `types.SimpleNamespace`, a member) of the class that declares one. When a type's `__dict__` NAME resolves to
>     something other than the dictionary's own accessor, and no class along its MRO owns one, the object is REFUSED by
>     name. That is the verdict's second form, in which the class that introduces the dictionary defines `__dict__` as a
>     property, so the interpreter never creates the accessor. No public C route bypasses the name lookup. (An interpreter
>     type with no `__dict__` name at all is the next bullet's case.);
>   - storage counts as covered only when it was READ, not when some base declares a descriptor for it.
> - **The same class inside the interpreter's own types (found while building the fix):** `TypeVar`, `TypeVarTuple` and
>   `ParamSpec` carry an instance dictionary that nothing exposes, so an attribute added to one (`T.extra = 1` against
>   `= 2`) read as no drift. The set is DERIVED by property (an interpreter-made type with a managed dictionary, an
>   interpreter-made MRO, and no owned accessor), never listed. The garbage collector visits that dictionary's VALUES
>   without running code, though not its keys. So:
>   - every value the collector reports must be accounted for, by identity and as a multiset, by a field the
>     description read;
>   - a value an accessor MAKES UP for an absent field (`None`, `()`) never accounts for a stored one. Which fields make
>     values up is derived per type from one canonically built object, and when that build fails every such value is
>     treated as made up (over-refusal, never silence);
>   - the dictionary's one known key, `__module__`, is described;
>   - any value left over is REFUSED: dictionary contents whose keys cannot be read faithfully.
>
> **Named limits, not closed:**
> - an instance dictionary that no accessor reaches is REFUSED, not described. On 3.14 that refusal is the only guard for
>   it: a managed dictionary lives outside `__basicsize__`, so the storage accounting cannot see it;
> - the interpreter types' dictionary rule rests on the garbage collector visiting every stored value. The made-up-value
>   rule rests on one canonical object being representative of how its type's accessors behave;
> - round 28's limits and earlier ones stand.
>
> The real census holds none of these shapes, so the carried INV-7 run is unaffected: the `Site` the arms import still
> reads the recorded `site_realized` digest, `1826c42a…`.
>
> **Cells:**
> - shadowed storage is read through its owner or refused, in the verdict's three forms and the second seat's two, through
>   all three routes: `tests/test_0042_inv7.py::test_r29_shadowed_storage_is_read_through_its_owner_or_refused`;
> - an unshadowed object describes exactly as before:
>   `tests/test_0042_inv7.py::test_r29_an_unshadowed_object_describes_exactly_as_before`;
> - an interpreter type's hidden dictionary contents are refused, and one without extra attributes is still described:
>   - `tests/test_0042_inv7.py::test_r29_a_typing_objects_hidden_dict_contents_are_refused`;
>   - `tests/test_0042_inv7.py::test_r29_a_typing_object_without_extra_attributes_is_still_described`;
> - a made-up value absorbs nothing, and `__module__` is described; a stored `None` is accounted for, not refused:
>   - `tests/test_0042_inv7.py::test_r29_a_made_up_value_absorbs_nothing_and_the_module_is_described`;
>   - `tests/test_0042_inv7.py::test_r29_a_stored_none_is_accounted_for_not_refused`;
> - each rule is load-bearing, each mutant failing for its named reason:
>   `tests/test_0042_inv7.py::test_r29_each_rule_is_load_bearing`.

> **ROUND 30: A DICTIONARY NO ACCESSOR REACHES IS REFUSED WHATEVER ITS NAME HOLDS, AND AN OBJECT'S OWN TYPE IS COUNTED
> ONCE** (v12.11, research as the specification's author; the round-29 verdict's two corrections, banked in the
> coordination repo at `6cf78f9`, body sha16 `cda44d10f65b719b`, fixed within the round). **Both were round 29's own new
> rules, each deciding from a signal wider or narrower than the fact it stood for.**
> - **An explicit `__dict__ = None` read as an absent name (R29-1).** The static lookup returned the same value for "no
>   such name" and "a name holding `None`", and round 29's dictionary rule asked the name. So a class whose body sets
>   `__dict__ = None` kept an ordinary instance dictionary that no accessor exposes, and neither read nor refused it: a
>   changed key, or a changed value beside an uncalled property, read as no drift.
>   - The rule is now decided from STORAGE alone: the type has an instance dictionary, no class along its MRO owns a
>     `__dict__` accessor (a getset, or a member), and the MRO is not wholly interpreter-made (those types take the
>     residue rule below). What the name holds, whether `None`, `0`, a property or nothing, no longer matters.
>   - The static lookup now returns a distinct ABSENT marker, and every caller was checked for which meaning it needs.
>   - The leaf fallback, which describes an object by its referents' values, refuses any object with an instance
>     dictionary, so values can never stand in for keys.
> - **Every referent identical to the object's type was discarded (R29-2).** The collector reports a type's instances as
>   referring to their type a fixed number of times, and round 29 skipped EVERY occurrence. So an attribute whose value
>   is that type, an ordinary assignment, went unaccounted.
>   - That structural count is now DERIVED per type. It is MEASURED on a canonically built instance where one can be
>     built without running Python code: 1 for `TypeVar`, `TypeVarTuple` and `ParamSpec`, and 0 for the constant
>     evaluator, a heap type whose traversal visits only its held value (measured at import). Otherwise it is READ from
>     the heap-type flag, because a heap type's traversal visits its type once. That was measured for Python classes and
>     for the C heap types `deque`, `itertools.count` and a lock.
>   - Exactly that many occurrences are consumed. Every further occurrence is accounted for like any other value.
>   - One helper does this at every place that set the type aside: the residue rule, the canonical probe, and the leaf.
>   - A field that legitimately holds the type (`TypeVar('T', bound=TypeVar)`) is still described.
>
> **Named limits, found while building the fix:**
> - the collector reports a managed dictionary either as its VALUES or, in a process whose history has MATERIALISED it,
>   as one dictionary object. The residue rule refuses the object in the second case whatever it holds, even with no
>   attribute left (a `TypeVar` given an attribute that was then deleted). Measured trigger on 3.14.7: importing
>   `pytest` or `veracium`, followed by attribute names given to these types in differing orders. The mechanism inside
>   the interpreter is not pinned. Loud, never silent. An untouched empty object was described in every history
>   measured. **Its consequence for the evidence:** a mutation check whose kill depends on values mode can pass or fail
>   with the order the tests ran. The check for made-up values went red on CI's shuffled order after an earlier test had
>   materialised the dictionary. Such a check therefore runs in a fresh interpreter and asserts values mode before it
>   judges;
> - where the structural count is read from the heap-type flag, a C heap type whose traversal does not visit its type
>   would read one attribute holding the type as structural. The constant evaluator is such a type, and is measured for
>   that reason.
>
> **The INV-7 run is RE-MADE, no longer carried.** The product's `src/` changed for the first time since round 8: the
> store's in-memory probe connections are now closed on every path (`0ceffd1`, specs/0007), a change to no census site and
> no decision. The run was made on the committed tree of `4e081c6`, on CI's own 3.14.7 build:
> - 21 of 21 gates true and harness exit 0;
> - every one of the 8 runs imported the same `Site`, `site_realized` `1826c42a…`, the digest the round-24 run recorded;
> - the twin's digest over its 60 files is now `e85dc63b…`, moved from round 24's because the source it is derived from
>   moved.
>
> **Cells:**
> - a dictionary no accessor reaches is refused whatever its name holds, and one under an inherited accessor is read:
>   - `tests/test_0042_inv7.py::test_r30_a_dictionary_no_accessor_reaches_is_refused_whatever_its_name_holds`;
>   - `tests/test_0042_inv7.py::test_r30_a_dictionary_under_an_inherited_accessor_is_read_not_refused`;
> - the leaf refuses an object with an instance dictionary:
>   `tests/test_0042_inv7.py::test_r30_the_leaf_refuses_an_object_with_an_instance_dictionary`;
> - absent is not a stored `None`: `tests/test_0042_inv7.py::test_r30_absent_is_not_a_stored_none`;
> - the object's own type, counted once:
>   - `tests/test_0042_inv7.py::test_r30_an_attribute_holding_the_objects_own_type_is_refused`;
>   - `tests/test_0042_inv7.py::test_r30_a_field_holding_the_objects_own_type_is_described_not_refused`;
>   - `tests/test_0042_inv7.py::test_r30_a_leaf_holding_its_own_type_is_described`;
>   - `tests/test_0042_inv7.py::test_r30_in_a_fresh_interpreter_both_own_type_occurrences_are_seen_and_refused`;
> - a made-up value absorbs no stored one, judged in a fresh interpreter in values mode:
>   `tests/test_0042_inv7.py::test_r30_in_a_fresh_interpreter_a_made_up_value_absorbs_no_stored_one`;
> - each rule is load-bearing, each mutant failing for its named reason:
>   `tests/test_0042_inv7.py::test_r30_each_rule_is_load_bearing`.

> **ROUND 31: A READ CREDITS ONLY A FIELD SHOWN TO STORE IT, AND SHARING IS DESCRIBED ACROSS THE WHOLE CLASS** (v12.12,
> research as the specification's author; the round-30 verdict's two corrections, banked in the coordination repo at
> `256c235`, body sha16 `d2c6905df8f8b9cf`, fixed within the round).
> - **An accessor's reported value was credited as a stored one (R30-1).** `TypeVar` and `ParamSpec` report their
>   variance as `True` or `False`, read from a C integer, not from a stored object. Round 30 still counted those Booleans
>   against the collector's referents, so a hidden attribute holding the same Boolean was absorbed and never refused.
>   - A field's read is now credited only when the field is SHOWN to store it: a build that sets that one field to a
>     FRESH sentinel must read back that very object and hold it among its referents. A plain membership test was
>     rejected because it passes by coincidence (with `default=False`, the variance flags also read `False`).
>   - Lazily bound type parameters are covered by compiling one probe declaration (`def f[T: A = B, *Ts = B, **P = B]`,
>     and a constrained form), whose evaluator functions count as the build's own objects.
>   - The builds run ONCE per import, in a child interpreter of the same executable, for the candidate types (derived by
>     the round-29 property over every loaded class, never listed). Only the field names come back. The builds therefore
>     never touch the process being described: run in-process, they had changed how later instances' dictionaries are
>     reported.
>   - A type that was not primed credits nothing, and is refused.
>   - Derived on 3.14.7: `TypeVar` {name, bound, constraints, default and their three evaluators}, `ParamSpec` {name,
>     bound, default, its evaluator}, `TypeVarTuple` {name, default, its evaluator}. The variance flags are never
>     credited, and a stored Boolean default still is.
> - **Each class member had its own reference map (R30-2).** Sharing inside one member was recorded, but sharing
>   BETWEEN members was forgotten, so two members holding one list read the same as two lists. Mutating one then changes
>   the other.
>   - There is now ONE reference map across the whole description: the members, the bases, the type-level fields and the
>     metaclass. A metaclass is reached through two of those roots (the type-level `__class__` and the metaclass entry).
>     Either one on the shared map shows the sharing, so they are a pair, and a check must break both.
>   - Identity is kept for everything EXCEPT a fixed set of values, so it is kept wherever it COULD be state. The set is:
>     scalars, an exact built-in tuple or frozenset (whatever it holds), a code object, and an immutable class. These are
>     described by value, never as a back-reference, because their identity reflects interning and constant folding
>     rather than anything the census did. The elements of a tuple or frozenset still recurse through the map, so a list
>     inside a tuple is still a back-reference. Any object outside that set is recorded, whatever its type's
>     mutability. Many immutable C instances (a compiled pattern, a `range`) are in any case refused by round 27's rule
>     before their content is read.
>     - **WITHDRAWN at round 32 (v12.13); the text above is kept as it was adopted.** Its premise was false: `pair[0] is
>       pair[1]` tells two equal runtime-built tuples, frozensets, code objects, ints or strings from one object held
>       twice, and a decision can turn on it (the round-31 verdict's R31-1). The premise was the second seat's, in its
>       round-30 stage-1 mark. Round 32 records every object; see the round-32 paragraph.
>   - Cycles still end, since every cycle passes through a mutable object.
>
> **Named limits:**
> - the probe declaration's evaluators are recognised by their code's FILE NAME: code a census compiled under that name
>   would be credited. That is the same class as the guard's file-name limit, an attack on the measurement, outside the
>   accepted round-19 scope;
> - a type first seen after import, or a field no probe build can set, is never credited. That is over-refusal, loud;
> - the priming adds a child interpreter per describer import (about 97 ms, measured, with `veracium` and `pytest`
>   loaded).
>
> **The description FORMAT changed; the class did not.** Describing immutable values by value removes the back-references
> the empty tuple `()` used to receive, so the real `Site`'s description bytes change. `src/` is unchanged since round 30.
> The INV-7 run was therefore made again, on the committed tree of `0d325a08`, on CI's own 3.14.7 build:
> - 21 of 21 gates true and harness exit 0; 860 tests compared, 0 differing;
> - every one of the 8 runs imported the same `Site`: `site_realized` `8b5c71ce…`, moved from `1826c42a…` by the format
>   change alone;
> - the twin's digest is `e85dc63b…`, unchanged, because `src/` did not change;
> - the standing list's wall-clock-sensitive test drew a variant in two of the eight runs, so the whole-trace digests are
>   not all equal. The per-test comparison is unaffected.
>
> **Cells:**
> - a synthesized Boolean read absorbs no hidden value:
>   `tests/test_0042_inv7.py::test_r31_a_synthesized_boolean_read_absorbs_no_hidden_value`;
> - a stored default, bound or constraint is described, not refused:
>   `tests/test_0042_inv7.py::test_r31_a_stored_default_bound_or_constraint_is_described_not_refused`;
> - the stored fields are derived, and primed at import:
>   `tests/test_0042_inv7.py::test_r31_backed_fields_are_derived_and_primed_at_import`;
> - the sentinel condition rejects a coincident singleton:
>   `tests/test_0042_inv7.py::test_r31_the_sentinel_condition_rejects_a_coincident_singleton`;
> - importing the describer leaves the process as it found it:
>   `tests/test_0042_inv7.py::test_r31_importing_the_describer_leaves_the_process_as_it_found_it`;
> - an unprimed type credits nothing and is refused:
>   `tests/test_0042_inv7.py::test_r31_an_unprimed_type_credits_nothing_and_is_refused`;
> - sharing between members, and between a member and a base, a closure or a metaclass, is drift, with its controls:
>   - `tests/test_0042_inv7.py::test_r31_sharing_between_members_is_drift`;
>   - `tests/test_0042_inv7.py::test_r31_sharing_controls`;
> - each rule is load-bearing, each mutant failing for its named reason:
>   `tests/test_0042_inv7.py::test_r31_each_rule_is_load_bearing`.

> **ROUND 32: EVERY OBJECT IS RECORDED, AND A SET'S ELEMENTS ENTER THE MAP IN AN ORDER THEIR DESCRIPTIONS DECIDE**
> (v12.13, research as the specification's author; the round-31 verdict's correction, banked in the coordination repo at
> `85d7b70`, body sha16 `a70815f1162f6e7e`, fixed within the round).
> - **Values were exempted from the reference map (R31-1).** Round 31 described an exact tuple, a frozenset and a code
>   object by value, never as a back-reference, and round 18 had done the same for scalars. The premise was that their
>   identity reflects interning and constant folding, not state. It is false: `is` observes the identity of ANY object,
>   and two equal objects built at runtime are not one object. A class holding two equal tuples, and the same class
>   holding one tuple twice, read the same, while `pair[0] is pair[1]` changed. The premise was the second seat's
>   (its round-30 stage-1 mark); v12.12's bullet stating it is withdrawn in place.
>   - EVERY object is now recorded: scalars, tuples, frozensets, code objects and immutable classes included. A scalar
>     still shows its value on first sight.
>   - A genuinely canonical object (`None`, a small int, `()`, an interned name) is shared in both sources by
>     construction, so its back-references cannot make a false drift.
>   - An exemption for canonical objects was considered and rejected. It would describe a canonical object like an
>     equal non-canonical one (an interned name beside an equal string built at runtime). And its test for a string
>     reads process state that changes: measured on 3.14.7, `setattr(C, s, …)` interns a runtime string in place.
>   - The same defect held for scalars built at runtime (an int, a string, bytes, a float), which were silent at the
>     round-30 and round-31 pins. No earlier pin was measured. The same rule closes them.
> - **A set's elements entered the map in iteration order (pre-existing).** A set's element descriptions were sorted,
>   but the elements were REGISTERED in iteration order. So an identical `Site`, whose set elements had only been
>   allocated in another order, described differently: loud, and present at the round-30 and round-31 pins. Recording
>   strings would have made that order follow the hash seed, and route B's `-I` children each draw their own.
>   - Each element is now first described against its OWN throwaway copy of the map, the elements are ordered by those
>     descriptions, and only then are they registered through the real map. A set subclass's content takes the same
>     path.
>   - Two elements that the description cannot tell apart are refused.
>   - **WITHDRAWN at round 33 (v12.14); the text above is kept as it was adopted.** Sorting erased an order that code
>     observes: `next(iter(s))` tells two insertion orders apart (the round-32 verdict's R32-1). The premise was the
>     second seat's, in its round-31 stage-1 mark M2, and the second seat's own probe had already shown order to be
>     the decision. The controls decided on membership and length, which cannot see order. Round 33 describes a set by
>     its whole table, or refuses it. The cells that stood for this bullet are superseded by
>     `tests/test_0042_inv7.py::test_r33_a_set_of_address_hashed_elements_is_refused`,
>     `tests/test_0042_inv7.py::test_r33_a_set_of_value_hashed_elements_is_described_by_its_table`,
>     `tests/test_0042_inv7.py::test_r33_a_set_subclass_is_described_by_its_table` and
>     `tests/test_0042_inv7.py::test_r33_a_set_of_colliding_strings_is_described_by_its_table`; see the round-33
>     paragraph.
> - Two more places rendered a value outside the map, and now go through it:
>   - a C leaf's scalar referents (the C-repr-slot branch takes the same rule, and no cell reaches it);
>   - `StringIO`'s stored newline setting (measured as a per-instance copy that neither the constructor nor `__setstate__` lets two roots
>     share).
>
> **Named limits:**
> - the tie refusal fires even when neither tied element is referenced later: loud over-refusal. The real `Site` has
>   no tie;
>   - **WITHDRAWN at round 33 (v12.14):** there is no tie refusal. A set is described by its table, or refused.
> - a dictionary whose INSERTION order came from iterating a set of strings has a hash-seeded order. That order is
>   observable behaviour and is described as it is, so route B's children can read it as drift: loud;
>   - **SUPERSEDED at round 33 (v12.14):** route B's children now run with the hash seed pinned to 0 and assert it, so
>     identical sources no longer read as drift there. The order is described as it is under seed 0.
> - the INV-7 run pins `PYTHONHASHSEED=0`, so its 8-run gate does not show hash-seed independence. A cell shows it for
>   the real `Site`, under six distinct seeds;
> - that the real `Site` describes the same when compiled from source, loaded from a cached `.pyc` or executed from
>   text is measured for that class only (the second seat), not in general.
>
> **The INV-7 run is re-made again: the describer changed, `src/` did not.** It was made on the committed tree of
> `e78b4a4d`, on CI's own 3.14.7 build:
> - 21 of 21 gates true and harness exit 0; 860 tests compared, 0 differing;
> - every one of the 8 runs imported the same `Site`: `site_realized` `41548918…`, moved from `8b5c71ce…` by the format
>   change alone;
> - the twin's digest is `e85dc63b…`, unchanged;
> - the standing list's wall-clock-sensitive test drew a variant in four of the eight runs; the per-test comparison is
>   unaffected.
>
> **Cells:**
> - sharing of an immutable object is drift, through three routes (the verdict's seven witnesses and the runtime-built
>   scalars): `tests/test_0042_inv7.py::test_r32_sharing_of_an_immutable_object_is_drift`;
> - a canonical object reads the same shared or not:
>   `tests/test_0042_inv7.py::test_r32_a_canonical_object_reads_the_same_shared_or_not`;
> - a set's elements are ordered by their descriptions, each against its own copy of the map, a set subclass included:
>   - `tests/test_0042_inv7.py::test_r32_a_sets_elements_are_registered_in_an_order_their_descriptions_decide`;
>   - `tests/test_0042_inv7.py::test_r32_each_set_element_is_ordered_against_its_own_copy_of_the_map`;
>   - `tests/test_0042_inv7.py::test_r32_a_set_subclass_is_registered_in_an_order_its_descriptions_decide`;
> - which element is shared is still drift, and elements differing only by a back-reference are described:
>   - `tests/test_0042_inv7.py::test_r32_which_set_element_is_shared_is_still_drift`;
>   - `tests/test_0042_inv7.py::test_r32_a_set_whose_elements_differ_only_by_a_back_reference_is_described`;
> - a tie is refused: `tests/test_0042_inv7.py::test_r32_a_set_whose_elements_cannot_be_told_apart_is_refused`;
> - hash-seed independence, for a set of runtime strings and for the real `Site`:
>   - `tests/test_0042_inv7.py::test_r32_a_set_of_runtime_strings_describes_the_same_under_every_hash_seed`;
>   - `tests/test_0042_inv7.py::test_r32_the_real_site_describes_the_same_under_every_hash_seed`;
> - a leaf's scalar referents go through the map:
>   `tests/test_0042_inv7.py::test_r32_a_leafs_scalar_referents_go_through_the_map`;
> - each rule is load-bearing, each mutant failing for its named reason:
>   `tests/test_0042_inv7.py::test_r32_each_rule_is_load_bearing`.

> **ROUND 33: A SET IS DESCRIBED BY ITS WHOLE TABLE, OR REFUSED** (v12.14, research as the specification's author;
> the round-32 verdict's correction, banked in the coordination repo at `cc7c1d3`, body sha16 `025b9b801b607091`, fixed
> within the round).
> - **Sorting erased an order code observes (R32-1).** Round 32 ordered a set's elements by their descriptions. Two
>   sets that differ only in insertion order read the same, while `next(iter(s))` changed the decision. The premise
>   was the second seat's (round 31, mark M2); v12.13's bullet stating it is withdrawn in place.
> - **Iteration order is not all of a set's state either.** The table is observable: the slot `pop()` resumes from; a
>   table that grew and was emptied (two adds then iterate differently from `set()`); where each element sits
>   (`frozenset([16, 14, 38])` and `frozenset([16, 38, 14])` iterate alike and sit at different slots, which
>   `set(fs)` copies); the table's size; and where deleted slots sit (sets equal in everything else, whose deleted
>   slots differ, order a later `add` differently). The second seat found the first three and the deleted slots at
>   stage 2; dev isolated the size.
> - **So a set is described by its WHOLE TABLE**, exact sets, frozensets and their subclasses alike:
>   - the table's size, its fill, its used count, and the slot `pop()` resumes from;
>   - every occupied slot by position: a deleted slot, or the element held there;
>   - elements registered in slot order, which is the order they iterate.
> - **The table is read in place**, through ctypes' C-level accessors, which run no Python frame, so the round-28
>   guard passes them. The reads use the `PySetObject` offsets of a 64-bit build without free threading or debug
>   refcounts.
>   - The layout is TRUSTED only after a check at import proves each field against an independent observable. Before
>     any slot is read: fill and used against fresh sets' lengths, and the finger against zero; the table pointer
>     against the embedded
>     small table on both sides of the first resize; and the table size against `set.__sizeof__`. Then the keys
>     against the elements' identities, fill and used against known deletions, and the finger against a known `pop()`.
>   - Any disagreement, and a free-threaded, debug or non-64-bit build, leaves the reader refusing every set.
>   - Each set is read twice, and refused if the reads differ, if its keys are not exactly the elements it iterates,
>     or if its used count or its occupied slots disagree with what it iterates and its fill.
> - **A set is REFUSED if it holds an element whose slot does not follow its value**, one element included, since its
>   slot is then its address. The elements the describer ADMITS are exactly: an int, a bool, `None`, a float that is
>   not NaN (NaN hashes by identity), a str or bytes, or an exact tuple of these. Every other element is refused,
>   including some whose hash does follow their value (a complex, a frozenset). Types are checked exactly, since a
>   subclass may define its own hash.
> - **A str's and bytes' slot also follows the hash seed.** The two comparisons that cross processes AND sources pin
>   the seed to 0 and assert it in the process that describes:
>   - route B's children, now started with `-P -s -B` and an environment without `PYTHON*` variables except
>     `PYTHONHASHSEED=0`, in place of `-I`, which ignores that variable;
>   - each INV-7 arm, since the eight runs' `site_realized` gate compares HEAD's `Site` with the twin's.
>   - Comparisons inside one process share its seed. The second seat first deferred the arms' assertion, on the
>     premise that the eight runs describe one source; that premise was false, and the enumeration it asked for found
>     the cross-source gate.
> - **A dictionary's table history is not order state** (measured): dictionaries with different histories decide
>   alike on iteration, insertion and `popitem`; the one difference measured is allocated size (`sys.getsizeof`).
> - **The real `Site` holds no sets** (two routes: a walk of its description, and a count of the set path while
>   describing it), so no set rule moves its digest.
>
> **Named limits:**
> - the set reader is a new trusted channel. It trusts the `PySetObject` offsets of a 64-bit build without free
>   threading or debug refcounts, measured on CPython 3.14.7 and checked field by field at import, and refused
>   otherwise. No version is checked. The check of the deleted slots' identity guards a change in CPython's semantics,
>   and no layout that passes the earlier checks reaches it, so no mutant covers it;
> - over-refusal: a set holding any element outside the admitted list (an instance with the default hash, NaN, `...`,
>   a hash the census defines, and value-hashed types the list omits, such as a complex or a frozenset), one element
>   included, is refused;
> - a deleted slot left by an element whose hash was its address is described where it sits, which can differ between
>   processes: loud, never silent;
> - a set of strings or bytes is described as its table stands under seed 0. Two sources whose tables agree under seed
>   0 and differ under another seed read the same (silent, bounded);
> - a census thread that changes a set between the two reads and restores it is not seen;
> - allocation is outside every description: a decision on `sys.getsizeof`, `__sizeof__`, `bytearray.__alloc__` or
>   `id()` is not held by it.
>
> **The INV-7 run is re-made again: the describer changed, `src/` did not.** It was made on the committed tree of
> `ad5df4be`, on CI's own 3.14.7 build:
> - 21 of 21 gates true and harness exit 0; 860 tests compared, 0 differing;
> - every one of the 8 runs imported the same `Site`: `site_realized` `41548918…`, unchanged (the `Site` holds no sets);
> - the twin's digest is `e85dc63b…`, unchanged;
> - the standing list's wall-clock-sensitive test drew a variant in five of the eight runs, with the research
>   seat running nothing (confirmed by `/proc`); other sessions' load was not measured. The per-test comparison is
>   unaffected.
>
> **Cells:**
> - a set's table is state, through three routes (the pop position, an emptied grown table, a frozenset's layout, the
>   table's size, deleted slots at other slots). W1, W3, W4 and W5 each isolate one field (the pop finger, the live
>   slots, the table's size, the deleted slots); W2 differs in several at once:
>   - `tests/test_0042_inv7.py::test_r33_a_sets_table_is_state`;
>   - `tests/test_0042_inv7.py::test_r33_a_frozensets_slots_are_what_differs`;
>   - `tests/test_0042_inv7.py::test_r33_a_sets_dummies_are_what_differs`;
> - described by the table: `tests/test_0042_inv7.py::test_r33_a_set_of_value_hashed_elements_is_described_by_its_table`,
>   `tests/test_0042_inv7.py::test_r33_a_set_subclass_is_described_by_its_table`,
>   `tests/test_0042_inv7.py::test_r33_an_empty_set_and_a_set_of_one_value_are_described`,
>   `tests/test_0042_inv7.py::test_r33_a_dummy_left_by_an_address_hashed_element_is_described`;
> - refused: `tests/test_0042_inv7.py::test_r33_a_set_whose_slots_are_not_its_values_is_refused`,
>   `tests/test_0042_inv7.py::test_r33_a_set_of_address_hashed_elements_is_refused`,
>   `tests/test_0042_inv7.py::test_r33_a_set_of_one_address_hashed_element_is_refused`,
>   `tests/test_0042_inv7.py::test_r33_a_set_holding_nan_is_refused`,
>   `tests/test_0042_inv7.py::test_r33_an_int_subclass_with_its_own_hash_is_refused`;
> - the reader: `tests/test_0042_inv7.py::test_r33_the_set_reader_runs_under_the_guard`,
>   `tests/test_0042_inv7.py::test_r33_the_set_reader_check_refuses_a_wrong_layout`,
>   `tests/test_0042_inv7.py::test_r33_the_set_reader_check_refuses_an_unsupported_build`,
>   `tests/test_0042_inv7.py::test_r33_an_unproven_reader_refuses_every_set`,
>   `tests/test_0042_inv7.py::test_r33_a_table_that_changes_while_read_is_refused`,
>   `tests/test_0042_inv7.py::test_r33_a_dummy_read_as_empty_is_refused`;
> - the hash seed: `tests/test_0042_inv7.py::test_r33_a_set_of_colliding_strings_is_described_by_its_table`,
>   `tests/test_0042_inv7.py::test_r33_route_b_describes_colliding_strings_in_seed_zero_order`,
>   `tests/test_0042_inv7.py::test_r33_route_b_refuses_a_child_that_is_not_isolated`,
>   `tests/test_0042_inv7.py::test_r33_an_arm_refuses_an_unpinned_seed`;
> - a dictionary's table history is not order state:
>   `tests/test_0042_inv7.py::test_r33_a_dicts_table_history_is_not_order_state`;
> - each rule is load-bearing, each mutant failing for its named reason:
>   `tests/test_0042_inv7.py::test_r33_each_rule_is_load_bearing`.

> **Implementation note, round 6 pre-seal (2026-09-20).** Building the per-site decision trace the round-5
> verdict asked for at implementation review found two defects in the runtime leg, both fixed before the seal
> (the commit is named in the package's README): the leg's parametrised ids were evaluated ABOVE its last three
> entry blocks, so fourteen declining executions (0041's tranches 3–5) had never run under the delta assertion
> while the completeness test — which compared dict keys, not the parametrised set — stayed green; and one of the
> fourteen, `store.redact.target`, bracketed TWO decision points (§4a's exactly-one-target and INV-5's
> unknown-or-cross-user) under one id and consulted twice per decline. The ids are now frozen after the last
> block and asserted equal to the dicts, a static guard refuses an entry block below the freeze, and the two
> decision points are two ids (`store.redact.both-or-neither` beside `store.redact.target`; 162 declared). The
> class is the one the note above names: a claim ("the runtime leg executes one declining decision at every
> id") carried by a test whose subject grew past it, green at every pin since 0041's tranche 3.

> **Implementation note, round 7 (2026-09-20; the seven round-6 implementation findings).** Every finding was
> reproduced at the round-6 pin before it was fixed, and every regression was run RED on that pin with only
> `tests/` replaced, then GREEN on the fixed tree (the transcript rides in the package). The product half:
> a measurement that fails is CONTAINED and counted by exception type, never a zero (R6-1); a consultation is
> recorded immediately before the site's own condition — sequential sites no longer share a bracket, and the
> four hot `Edge` predicates consult before evaluating and return through ONE statement (R6-2); the snapshot
> says what REGISTERED (R6-3). The evidence half: the loaded-module observation the registry check needs is
> the evidence layer's, because specs/0031 keeps `sys.modules` and `vars()` out of src; the binding scan
> resolves names through enclosing function scopes and refuses `nonlocal`/`global` (R6-4); the observer keys
> each record by exit STATEMENT and reads that statement from the frame's line events — CPython 3.12 attributes
> the return after a `with` block to the `with` line, so the census-enabled path of every hot predicate had
> read as an implicit exit while the census-off path read its ordinal: the class §4's Part A-0-quater names,
> an instrument reading the runtime's attribution as the program's (R6-5); the twin transform rewrites only
> names bound by `declare_site` in the same module and only recognised shapes, refuses the rest by line, keeps
> the bypass dead, and ships a manifest its `verify()` re-derives (R6-6); the surface-driven deltas are EXACT,
> derived from the product's control flow, with the superseded `>=` form kept as the mutant it could not kill
> (R6-7). The cost at the shipped default was re-measured (CHANGELOG): inside run-to-run noise. The frozen
> invariants are unchanged in text; INV-7's transcript was re-run on this tree — with a control pair for EVERY
> arm, not the reference alone (the first re-run read DIVERGENT on the healthy arm at one 0029 acceptance-corpus
> test: wall-clock noise the slowest arm sampled), and with the exclusion list STANDING and NAMED
> (`inv7_exclusions.py`, each entry with its cause; a test a control pair finds newly non-reproducible is a
> finding that fails the harness's exit, never a housekeeping exclusion — research's pre-dispatch pass, which
> also found and had fixed a propagated raise attributed to a walked return statement, a module-registry key
> test that could only turn an R6-3 refusal into a benign listing, and four transform refusals no test drove).

> **Implementation note, round 8 (2026-09-21; the four round-7 findings).** Every finding was reproduced at the
> round-7 pin before it was touched (twelve cases, two of them controls that must hold on both sides), and the
> same script run against the fix leaves only the controls. **src/ is unchanged by this round: all four findings
> were in the ACCEPTANCE CHECKS, and the reviewer said so — the shipped traces and the regenerated copy were not
> shown to be wrong.** F1: the registry reconciliation stays OPTIONAL, because the module map is an observation of
> a RUNNING interpreter and a reviewer validating the shipped report in a throwaway cannot supply one; making it
> mandatory would lock out exactly the caller who found the defect. Its ABSENCE is reported instead, in the list
> every caller already reads, so `[]` keeps meaning "validated, completely" and no caller had to change. F2 and
> F4's first case shared a root — both resolved names without the language's own scope information — and share a
> fix: one resolver over `symtable`, asked by the binding scan and the twin transform alike, which answers the
> whole binding grammar by construction rather than by an enumeration someone maintains (the reviewer found the
> two rungs the enumeration had not reached: an assignment expression and a `match` capture). F3: a control run's
> exit is gated like any other run's, the exits-per-function COUNT is replaced by the site-to-exit ASSOCIATION
> (a count of two exits for two sites is satisfied by two sites sharing one), and the gates are computed before
> the verdict is serialised — they had been absent from every shipped `verdict.json` while two READMEs said it
> carried them. F4: `verify` requires its source, compares the file set both ways, compares program structure by
> RE-DERIVING the transform and diffing the AST, and checks the manifest's before and after hashes; the harness
> passes the source, so the preservation half stops being dead code in the run.
>
> **ROUND 13 CORRECTS THE "BY CONSTRUCTION" SENTENCE ABOVE, AT BOTH OF ITS LAYERS, so that sentence is history and
> not a description of the shipped resolver** (v9.5, research as the specification's author, 2026-09-23; the
> round-12 verdict's first finding was a silent case of exactly this). The claim was that one resolver over
> `symtable` answers the whole binding grammar by construction. It fails twice. **First, `symtable` is not always
> the interpreter:** on 3.12 and later, an inlinable comprehension inside another comprehension's first iterable is
> read by `symtable` as binding a name that the compiled code reads from the module — in a function body on 3.13, in
> a class body on 3.12 and 3.13, established by executing it — so the resolver REFUSES that shape on 3.12 and later
> rather than trusting either reading. **Second, the join from AST nodes to symbol-table blocks was never by
> construction at all:** it is a walk this code maintains, pairing blocks keyed by line and kind in visiting order,
> and three orders the interpreter uses that the walk did not reproduce were each found as a SILENT wrong answer —
> definition-time positions (defaults, decorators, annotations, a class's bases and keywords) assigned to the inner
> scope (round 12, S2-1); same-line scopes in different roles of one statement's header (round 12, S2b-1, where such
> collisions are now refused); and a comprehension's element walked before its generators (round 12's S2c-1, the
> round-12 verdict's first finding). The walk now follows the order CPython's `symtable` was measured to use on
> 3.10 to 3.13: a definition's enclosing parts before its own block; inside a comprehension, each generator's target,
> iterable (all but the first, which belongs to the enclosing scope) and conditions, then a dict comprehension's
> value, then the element or key.
>
> **What replaces "by construction" is a check and a gate, and each is stated with what it cannot see.** THE JOIN
> CHECK (`_check_join` in `specs/evidence/0042/scope_resolution.py`): after the walk, every group of two or more
> same-line, same-kind blocks is either passed because every block in it has an identical symbol fingerprint — the
> resolver's answers read only a block's type and its symbols' flags, so exchanging identical blocks cannot change
> one — or each node in the group must be fitted by exactly one block, by its signature (a function's parameters; a
> comprehension's own targets and, on 3.12 and later, those of the inlinable comprehensions merged into its block),
> and that block must be the one the walk gave it; otherwise the resolver refuses. Two scopes can share a signature
> and still differ in their symbols — two parameter-less lambdas, one binding a name by an assignment expression —
> and that case is refused, not trusted. At this version it refuses none of the 74 modules under `src/veracium/` and
> `specs/evidence/0042/` (`test_r13_the_join_check_refuses_nothing_in_the_product_or_the_evidence`) *(v11.2: 74 at round 13's
> pin. The same test now reads 75, the one module added since being the round-16 reference census)*, and the round-12
> order with the check removed answers the pinned cells silently wrong while the same order with the check present
> refuses each of them (`test_r13_the_join_check_turns_the_old_orders_silent_answers_into_refusals`). WHAT IT CANNOT
> SEE, named: it over-refuses one shape — an inlinable comprehension, merged into a generator expression, that reads
> one of its own later targets in its first iterable — loudly, and that is recorded for the next round. *(v11.2: CLOSED on
> 3.12 and later by round 19, see below.)*
> THE GATE (`specs/evidence/0042/pairing_oracle.py`, driven by
> `test_r13_the_pairing_oracle_finds_no_silent_answer_and_its_control_does`): 400 generated programs at seed 13, dense
> with same-line scopes and including tied signatures, each read judged against the load instruction CPython itself
> compiles for it rather than against any model of the scoping rules. It asserts no silent wrong answer; that an
> in-process positive control — this resolver with the round-12 order restored and the join check removed — gives at
> least 10; that at least 20 programs hold a tied group, counted from the program rather than from the resolver's
> outcome, and that none of those is answered silently wrong; and that most programs are judged and few reads go
> unlocated. WHAT IT CANNOT SEE, named: it needs instruction positions and SKIPS, visibly and inventoried, on 3.10;
> and it generates no parameter annotations — the positions where the order among header roles was subtle — which is
> recorded for the next round. *(v11.2: CLOSED by round 19, see below.)*
>
> **ROUND 19: THE OVER-REFUSAL'S CAUSE, FIXED AT ITS SOURCE, AND THE ORACLE TAKES ANNOTATIONS** (v11.2, research as the
> specification's author).
> - **The cause.** CPython 3.12 inlines a comprehension into its parent in the ANALYSIS pass, after the whole block has been
>   visited. It merges an inlined comprehension's bound name into the parent only if the parent does not already hold that
>   name. A comprehension's first iterable is visited in the parent, so a target it reads there was already held, and was
>   not merged. The signature merged it anyway, so the block fitted no node, and the resolver refused correct code.
> - **The fix.** On 3.12 and later, the comprehension signature is a second implementation of that merge rule, walking the
>   block in CPython's visiting order. It is accepted DIRECTLY against the interpreter: over the pairing oracle's corpus and
>   every module under `src/veracium/` and `specs/evidence/0042/`, the signature equals the non-parameter locals `symtable`
>   reports for each block, and the SET of disagreements is empty on 3.11, 3.12 and 3.13
>   (`tests/test_0042_scope_resolution.py::test_r19_the_comprehension_signature_equals_symtable_over_the_corpus`). The
>   reproduction resolves on every version
>   (`tests/test_0042_scope_resolution.py::test_r19_n4_the_reproduction_resolves_on_every_version`). A name the block
>   ALSO reads after the inner comprehension is not merged, as measured against `symtable`, not as predicted
>   (`tests/test_0042_scope_resolution.py::test_r19_a_name_the_block_also_reads_is_not_merged`).
> - **Nothing new is accepted silently.** The gate still finds no silent wrong answer, and its positive control still
>   fires. The shape `symtable` answers differently from the interpreter (round 12's S2c-2) is still refused.
> - **What remains, named.** One untied over-refusal is refused identically on 3.11, which has no inlining, so it has
>   another cause. It is recorded, not zeroed.
> - **The oracle's generator now emits annotations,** in six roles (parameter, keyword-only and return, on a module-level
>   function and on a method). The test asserts that every role is actually JUDGED on each interpreter, so a role that never
>   reaches an instruction cannot pass silently. A control under `from __future__ import annotations`, where annotations
>   are strings and load nothing, must read "no instruction" and never "wrong". The gate's refusals rose with the new
>   roles, all through two refusals that exist by design (round 12's S2c-2 shape and header-role collisions): they are
>   loud, not lost coverage.
> - **Attributing the reads 3.13 cannot locate, read by read,** corrected an earlier attribution. They are reads FUSED into a
>   store-and-load superinstruction (a local read right after its own store), plus reads inside annotations. The earlier
>   note had attributed them to return annotations alone, before reads carried roles.
> - **The planned SM4 cell cannot exist, and the argument is recorded.** The join check requires EVERY node of a same-line
>   group to fit exactly one block, so any accepted wrong pairing is a permutation. A signature that ignores the inlined
>   merge equals each node's own targets, while the real locals are those targets plus the inlined names, and the two
>   are disjoint by the merge rule. Summing over the permutation forces every inlined set to be empty. So that mutant can
>   only over-refuse, never accept silently, and the direct tests above kill it.
>
> The OTHER "by construction" sentence in this note, below — the module-level binding count being total over syntax
> — is NOT affected: it reads the compiled code object, which is the interpreter's own reading, and none of rounds
> 12 and 13's findings touch it. It is named here so that a reader sweeping for the phrase finds the reason it stays.
>
> **The round's own class, and it is the one worth carrying forward.** Three of the four findings are one shape:
> a check whose scope depends on an argument, returning a clean result when the argument is absent. Research's
> stage-1 read then found the SAME shape had migrated into `insufficiency` — the function written to fix it — so
> the response was to sweep the layer rather than patch the cell. The rule, with both halves: **an optional
> argument is safe when its default is the COMPLETE behaviour and dangerous when its absence silently narrows what
> the check looked at; and a default that SUPPLIES AN INPUT is a substitution, whose safety condition is that the
> input is BOUND TO THE RUN rather than merely located.** Seven functions read, five safe, two reporting their own
> incompleteness, one test pinning both.
>
> **And the second class, which is the first one's mirror: a hand list standing in for what the language already
> knows, growing back ONE LAYER DOWN inside its own removal.** The F2/F4a fix deleted the enumeration from the
> NAME question and left one in the guarantee that makes the name question answerable at all — the refusal that a
> declared site is not rebound at module level, which asked an AST walk for `ast.Name` nodes in a `Store` context.
> Research's stage-2 mutants found six module-level binding spellings that are not such a node and were therefore
> all ACCEPTED: `import os as S`, `from os import path as S`, `except Exception as S`, `del S`, `def S()`,
> `class S`. Each is the walrus case in another spelling — true of the name, false of the object — and the
> refusal that exists to make those two coincide did not fire. The reading that closes it is the interpreter's
> own: the module's compiled code object binds a name by exactly four opcodes, so counting them is TOTAL over
> syntax by construction and a form nobody listed is counted like any other. A second reading covers what that
> one cannot see — a binding performed from inside a nested code object that targets module scope, which is
> `global` and a comprehension's walrus — and is asked of `is_global()` rather than `is_declared_global()`.
> **The reason first given for that choice was false and CI found it.** It said PEP 572 needs no `global`
> statement, so the narrower predicate would miss the walrus; the first half is true of the language and the
> conclusion does not follow, because `symtable` SYNTHESISES the flag — on 3.10/3.11 `is_declared_global()` is
> TRUE for a walrus in a module containing no `global` anywhere. The same false belief had reached a REFUSAL
> MESSAGE, which told a reader to look for a `global` statement that does not exist.
>
> **ROUND 9 SUPERSEDED THAT WHOLE CHOICE, so the paragraph above is history and not the shipped rule.** The
> round-8 reviewer defeated the predicate pair with a nested `import os as S` under `global S` —
> `is_imported` and NOT `is_assigned`, so it never fired. Rule C now reads what the compiler emits in a
> NESTED code object (`STORE_GLOBAL`/`DELETE_GLOBAL`), which is the same kind of reading rule A already was,
> and the predicate pair is DELETED rather than widened: a third predicate would have been the next rung of
> the ladder this evidence exists to get off. The superseded pair is kept as the negative control its
> replacement must beat, and the two readings are measured to differ on exactly the two nested imports and to
> agree on every other row, on 3.10, 3.11, 3.12 and 3.13. Verified against a 46-case matrix, 29 refusals and
> 17 acceptances; an over-strict refusal is a refusal of correct code, so the 17 are as load-bearing as the
> 29, and three drafts of this fix over-refused.
>
> **A third reading was written in the same fix and DELETED, which is the part worth carrying.** It refused
> when the two readings disagreed — the reviewer's own "put an assertion between the two readings". Its mutant
> showed it caught nothing the other two did; then running two rows the reviewer had offered as must-accept
> showed what it does catch: `if False: S = 1`, where CPython folds a dead branch the AST walk can still see,
> and `S: int`, where a bare annotation's target carries a `Store` context and binds nothing. Both are correct
> code, and both were refused. A tripwire whose only reachable firings are false is worse than none, so it went
> — and the hand-written AST walk it existed to cross-check went with it, which leaves **no enumeration
> anywhere in the refusal**. That last claim is MEASURED, not grepped: the first attempt gated it by refusing
> the strings `ast.walk` and `ast.Store` in the refusal's source, and the reviewer defeated it in one line with
> `from ast import walk as _w, Store as _St` — a narrow matcher inside the test written to prevent narrow
> matchers, the same class one level up again. It is now established by counting: every AST-walking callable is
> wrapped and `ast.Store` replaced by a counting class BEFORE the resolver is imported, so an alias bound at
> module level is counted too; the refusal must consult the AST zero times, and two mutants that reinstate a
> walk must both be caught while still returning the right verdicts.
>
> **That gate took three forms in one evening and the progression is this round in miniature** (research's
> reading, and the reason it is written down rather than just fixed): a TEXT CHECK for the names, defeated by an
> alias; SABOTAGE AFTER CONSTRUCTION, defeated by an alias bound at import time, which captures the real callable
> before any patch can reach it; then WRAPPING BEFORE IMPORT, where no spelling reaches the real callable without
> passing through the counter. The first two are both about a SPELLING — one asks whether a name appears, the
> other whether a name resolves — and only the third is about the behaviour. It is the same move as AST node
> kinds → `symtable` → the compiled code object, made one level up, in the test rather than in the instrument:
> **go to the layer at which the spelling cannot vary.** The mistake was made at four layers in one evening and
> corrected the same way each time, which is the argument for naming the move rather than the instances. The general form, because the instinct will recur: a cross-check between two
> readings is right when they are two IMPLEMENTATIONS OF ONE RULE, where a difference is by definition a
> defect, and harmful when they are two readings of DIFFERENT RULES, where a difference is an ordinary state.
>
> **One decision is recorded rather than inherited.** Counting binding operations cannot distinguish "bound
> twice in sequence" from "bound once in two mutually exclusive branches", and three real idioms count more
> than one: a `try`/`except ImportError` import fallback, a site declared in both arms of an `if`, and
> `if TYPE_CHECKING: import x as S`. All three are REFUSED, because a static reading cannot tell a dead branch
> from a live one unless the condition is a literal the compiler folds, and a site declared once and
> unconditionally is the premise of the scan. The `TYPE_CHECKING` row is the sharpest — that branch never
> executes, so the refusal is false in fact — and the trade is taken knowingly: it needs a site name to collide
> with a type-checking alias, and no module in the tree does that. `if False:` is accepted, for the compiler's
> reason, and the two rows are adjacent in the matrix so the asymmetry explains itself.

## 1. Problem and motivation

**We assert guarantees we have never measured being exercised.** Two independent
competitors found the same defect in their own systems by measuring, and neither
found it by testing:

| | |
|---|---|
| `tigerless-labs/agent-memory` | *"Across **3,744 memories** written in a 120-episode run, the supersede edge count was **ZERO** — the mechanism the whole time-travel guarantee rests on was **reachable in principle and unused in practice**."* |
| `inspeximus` | *"the field was measured at **0.0000% coverage across 111,264 records** — every store this deployment runs — which made `strict_corroboration` **unable to fire anywhere**… nothing could reach it, **this server included, and we dogfood through this server**."* |

**Both had passing tests.** The tests construct the conditions the guarantee
needs; production never presented them.

> **Coverage measures whether a TEST reached a line. This spec measures whether
> PRODUCTION reaches the GUARANTEE.** They are different questions and we have
> only ever answered the first.

**And this project has been finding the same class by hand, one instance at a
time, for a week** — a refusal that could never fire because a test above it
rewrote its input; a reconciliation bound that could not see a section added
after it was written; two controls that reported PASS without executing; a
status check that printed `ok` when its lookup broke. **Every one was found by a
person noticing. This is the systematic version.**

### What this spec claims ON ITS OWN — and what it no longer claims

🔴 **v4 REPLACES v3.1's “Why the two halves are ONE spec”, which rested on a
dependency the round-1 reviewer removed.** That section argued *“Part B cannot
produce a rate without Part A's counter”*. The reviewer ruled otherwise, and the
ruling is accepted here verbatim:

> *“A refusal rate needs a defined denominator, but a controlled question harness
> can count attempts and outcomes itself. Part A adds valuable evidence about
> internal decisions; Part B does not inherently depend on process-wide counters
> to calculate a rate.”*

**So the harness is now its own spec, and this one keeps only the census.** The
honest consequence is stated rather than absorbed: **0042's original value
proposition was partly that it supplied another spec's denominator, and it no
longer does.** What remains is narrower and stands alone:

> **Does what we specify actually RUN?** For every enforcement point this project
> declares, is it INSTALLED, is it EXERCISED in production, and can we tell those
> two apart from a deployment that never switched the census on? **No rate, no
> onward dependency, no second arm.**

**That claim needs no harness and answers the competitors' finding directly** —
`tigerless-labs` learned its supersede count was zero by counting, and this is
the counting. **The refusal harness cites this spec for evidence about internal
decisions; it does not draw its denominator from it.**

## 2. Field contracts touched

**No stored field changes.** The census adds a process-local counter keyed by a
declared enforcement-point id, and nothing else. *(v3.1 also described Part B's
surface here; Part B is now its own spec and describes its own.)*

| contract | touched how |
|---|---|
| `Memory.recall` / `gate` decision path | **observation only** — a counter increments beside the decision; the decision is unchanged |
| receipts (0027 `policy_receipt`) | **read** — the receipt already records what a lane did; Part A does not extend it in v1 (see §10 Q3) |
| 🔴 **the enforcement-point DECLARATION** | **CREATED BY THIS SPEC — it does not exist.** v2 said the expected set was *"derived from the invariant registry"*. **There is no such registry.** `INV-` appears **0 times in `src/`**, and every occurrence under `specs/` is **0041's own** — 117 in the spec, 48 across `reviews.py`, `closure_findings.py` and `specs/evidence/0041/` — **no other spec uses the prefix**; the only registries in code are 0037's relations, 0028's successors, 0020's scope policy and the active-operation table. **And it cannot be derived from the existing §6 tables either.** The id sits inside a prose cell, not a column, and the vocabulary has **TWO FAMILIES**: digit-suffixed (`M1`, `V12`, `INV-11`) and **named** (`V-CENSUS`, `V-NO-INLINE-SEND`). Counting distinct `(spec, id)` pairs: **641 — 464 digit-bearing in 35 shapes, and 177 named.** 🔴 **A grammar that requires a digit DROPS the 177 named ids (28% of the vocabulary); one that does not degenerates to counting names.** **There is no fixed grammar over an id column because there is no id column.**

> **The definition is given EXECUTABLE, not in prose, and that is deliberate.** The two seats derived this independently and disagreed across three rounds — 207, then 36, then 651 — **and the disagreement closed only when both ran the same pattern, never when we compared conclusions, which agreed from the first message.** A prose definition (*"leading bold token starting with a capital"*) admits `**The live instrument**`, a sentence-case prose cell, as an id; the second seat implemented the stated words literally and got it.
>
> ```python
> ID = re.compile(r"^\s*\*\*([A-Z][A-Za-z0-9\-]*)\*\*")   # first cell of each `|` row,
> #   between the heading "## 6." and the next "## ".  Count DISTINCT (spec, id) pairs.
> ```
>
> **Re-derived by the second seat to within one on every family** (642 / 465 / 177 / 36). *The residual is one edge row; it is not a definitional gap.* **That three rounds were needed to agree what an id IS — in a project where every spec carries a §6 table of them — is itself the argument for §4a's declaration.** So the declaration is part of the work, not a dependency of it (§4a) |

## 2c. Untrusted inputs — REQUIRED, blocking

| input | source | treatment |
|---|---|---|
| ~~**examiner questions**~~ — **MOVED to the harness spec** | a human or model that has NOT read the implementation | **data, never instructions.** Questions are asked through the ordinary public API; no question text reaches a prompt with authority |
| ~~**the fixture store's records**~~ — **MOVED to the harness spec** | includes deliberately poisoned and deliberately quarantined rows | **the material under test.** A poisoned row must be able to reach recall — excluding it in the fixture would measure the fixture |
| **enforcement-point ids** (Part A) | declared in source, read by the census | **code-supplied, not caller-supplied.** An id that is not in the derived registry is a REFUSAL, not a new row |

### 2c-ii. Assertions about reach — REQUIRED

**A census count is a statement about ONE deployment's runs, never about the
mechanism in general.** A zero from our fixture corpus says *"our corpus never
presented the condition"*, not *"this guard cannot fire"*. **The two must never
be collapsed** — the second requires a reachability argument over the code, which
this spec does not attempt.

## 3. Trust-class matrix — REQUIRED, blocking

| class | may the census count it? | *(the harness spec carries its own question-class column — MOVED)* |
|---|---|---|
| **first-party stated** | yes | yes — the ANSWERED baseline |
| **third-party / unverified** | yes | 🔴 **yes, and this is the contribution** — the question class where the answer IS present and MAY NOT be asserted |
| **quarantined** | yes | yes — must produce REFUSED-UNTRUSTED, never ANSWERED |
| **redacted / absent** | yes | yes — must produce REFUSED-ABSENT |
| **counts themselves** | **carry no record content** — an id and an integer, nothing else (§7) | n/a |

## 3b. Authorization and scope

The census is **observation-only and cannot alter a decision** (INV-7, now a
THREE-arm diff — see Part A-2). **INV-7 establishes this against census code that changes behaviour, not against
census code written to defeat the measurement** (the round-19 scope, ACCEPTED; v12.0; the record after §6's table). It has no authorization surface of its own: it
reads what the host already computes. 🔴 **It runs in PRODUCTION and is opt-in,
default OFF**; the fixture-store constraint that stood here belonged to the
harness and travelled with it.

## 4. Behaviour

### Part A-0 — what an ENFORCEMENT POINT is, and where the expected set comes from

🔴 **Both were undefined in v2 and both are load-bearing.**

**DEFINITION.** An enforcement point is **any site that can return a decision
other than the caller's request** — refuse, quarantine, withhold, abstain,
downgrade. **It is a property, not a choice.** v2 said *"each enforcement point
declares a stable id"* without saying which sites those are, which made the
census's domain "whatever someone instrumented" — **a hand list one level up, in
the spec written to kill hand lists.** 🔴 **THE 162 IS WITHDRAWN — NOT REPAIRED. (Round-1 amendment 4.)**

v3.1 offered a count of *"decision-shaped sites in the five guarded files"* and
labelled it an UPPER BOUND on candidates. **The reviewer reproduced it and showed
it is not a bound at all:** it misses ordinary `return False` decisions and
excludes relevant modules such as `scope.py`.

> **Both of its boundaries were CHOSEN, not derived.** The five files came from
> the GUARDED set — which exists to route review, a different purpose entirely —
> and the pattern came from me. **A lexical line count over a hand-picked file
> set is the same defect as a hand list of enforcement points, one level up, in
> the section written to kill hand lists.** v3.1 already said it counts comments
> and docstrings; what it did not say is that a line is not a site and that
> nothing established the file set.
>
> 🔴 **So it is not restated with a caveat. It is gone.** A quantity whose domain
> was picked by its author cannot bound anything, and carrying it with a warning
> would let a reviewer cite the number and drop the warning — which is how the
> withdrawn figures in this project's own history survived.

**THE DOMAIN IS NOW MEASURED, and it is a PREREQUISITE of this spec rather than a
premise inside it.** The inventory is an AST pass over **all of `src/veracium`**,
not a lexical pattern over a chosen subset, and it defines:

| | |
|---|---|
| **counting unit** | 🔴 **THE TOOL'S UNIT, STATED VERBATIM, because 636 is the tool's number:** one AST node of a listed kind — **`RAISE`** (every `raise` statement, no branch condition) · **`RETURN_FALSE`** (`return False`) · **`RETURN_NONE`** (`return None` or a bare `return`, *only inside a function that also returns a value somewhere*). Not a line, not a function. *(v4 first wrote a STRICTER unit — “reached on a branch that can also return the caller's request” — which the tool does not implement and nothing executes. A prose definition and a figure that disagree are two definitions of one quantity: the same defect this spec's §2 raises about ids, at the definition rather than the count. The branch condition is exactly what the INSPECTION adds; it is not in the inventory.)* |
| **site identity** | `(module, qualname, line)` — stable across formatting, and the key the declaration joins on |
| **bounded scope** | every module under `src/veracium`, stated by name in the evidence output, so a later reader can see what was NOT scanned |

**THE INVENTORY HAS NOW RUN** (`specs/evidence/0042/decision_site_inventory.py`,
against `src/` at pin `5121501`):

| | |
|---|---|
| modules scanned | **55**, every `src/veracium/**/*.py`, nothing excluded |
| modules with at least one site | **40** |
| **candidate sites** | **636** = `RAISE` **482** + `RETURN_FALSE` **82** + `RETURN_NONE` **72** |

> 🔴 **THIS IS AN INVENTORY OF CANDIDATES BY SYNTACTIC KIND. IT IS NOT A COUNT
> OF ENFORCEMENT POINTS AND IT IS NOT A VERDICT.** A `raise` may be an argument
> check; a `return False` may be a predicate. **It is where an inspector STARTS.**
> *(The superseded “inspected subset” comparison is in §11.)*

**Both seats derived it independently and disagreed, and the disagreement was
research's.** Dev reported 636; research's first pass returned **652**, with
`RAISE` agreeing exactly at 482 and only the return kinds differing. The cause
was research's: `ast.walk(fn)` descends into NESTED functions, so a `return` in a
closure was counted once for the enclosing function and again for the closure.
Re-run with a visitor that sees each `Return` once: **636, all three kinds
matching.**

> **The lesson is the one this spec exists to make.** Two counts of one quantity
> differed by 16, and comparing the COUNTS would have said only that somebody was
> wrong. **Reading the other seat's DEFINITION is what located it** — and it
> located it in the seat that went looking. *A disagreement is self-announcing;
> an agreement is not.*

**THE EXPECTED SET comes from a spec-side DECLARATION this spec creates**, one
row per point: `id · governing spec · §6 invariant it enforces · file:symbol`.
**It must be authored, not scraped** — see §2's row. **INV-1 then has TWO
independent sources**: EXPECTED from the declaration, OBSERVED from the sites.
Neither derives from the other, so **drift is a refusal in both directions**: a
declared id that never reports, and a reporting id never declared.

> **Without two sources INV-1 is vacuous.** If the expected set is collected from
> the ids at the sites, absent-from-report is impossible by construction.

### Part A — the firing census

1. Each enforcement point declares a stable id at its decision site, **and the
   same id appears in the declaration**. 🔴 **`consulted` is incremented BEFORE
   THE DECISION BRANCHES**, never where the result is consumed — otherwise a
   point consulted and short-circuited downstream reads as unconsulted.
2. When the point EXECUTES, it increments `consulted`; when it DECLINES
   (refuses, quarantines, withholds), it also increments `fired`.
3. `census()` returns, for every id **in the declaration**:
   `{id, status, consulted, fired, errors}` where **`status` is one of the SIX
   in Part A-1's state table** — `DISABLED` · `UNDECLARED` · `UNMEASURED` ·
   `UNREACHED` · `UNEXERCISED` · `EXERCISED`, in that precedence order.
   🔴 **Part A-1 is the sole authority for the enum and its conditions; this
   step does not restate them.** *v4 enumerated five here and the validator
   implemented four — three carriers of one value is how they drift, so this one
   now points instead of copying.*
   🔴 **`UNMEASURED` needs its own field, and so does the count of five.** v2 put it in
   §7 prose while the row shape was `{id, consulted, fired}`, so **a counter that
   raised before incrementing rendered as `consulted=0`** — *which under Part A-1
   now renders as `UNREACHED`; the defect is identical and the status it wore
   changed* — the
   ok-vs-na collapse this spec names at §10.1, inside its own report.
4. A declared id absent from the report is a **failure of the census**, not a
   zero (INV-1).

### Part A-0-bis — THE THREE SETS *(round-2 amendment A4)* — 🔴 **SUPERSEDED IN PART BY A-0-ter: THERE ARE FOUR**

> 🔴 **Round 3 found the fourth.** This section derived DISCOVERED and authored REVIEWED and DECLARED — and then rested **INSTALLED** on the two authored ones, which can both be true of code containing no instrumentation. **`INSTALLED` is now derived from the source by a static scan (A-0-ter).** *The sets and refusals below stand; only INSTALLED's definition moved.*

🔴 **Round 2 found a contradiction and it is real: §4 A-0 says the declaration
is compared against an “INSPECTED SUBSET” of the inventory, while INV-2d refuses
on ANY inventory site absent from the declaration. With 636 syntactic candidates
that means declaring every ordinary `raise`** — including argument checks and
predicates that are not enforcement points at all.

**The fix is that there are THREE sets, not two, and v4 named two.**

| set | what it is | who made it |
|---|---|---|
| **DISCOVERED** | the AST inventory — **636 candidates by syntactic kind** | 🔴 **nobody.** Derived from the code; its value is that no one chose its members |
| 🔴 **REVIEWED** | **one INCLUSION-OR-EXCLUSION DECISION for every discovered candidate**: `{candidate_id → decision: enforcement \| not, reason, reviewer}` | **authored, and that is the point** — *the reviewer's “record inclusion/exclusion decisions”* |
| **INSTALLED** | **the scan of the BINDING — see Part A-0-quater, which is the current definition** | **nobody** — derived from the source. *Two earlier definitions were tried and failed; both are in §11 with what each missed.* |

#### The refusals, rewritten so they compare the RIGHT pair

| condition | verdict |
|---|---|
| a **DISCOVERED** candidate with **no decision in REVIEWED** | 🔴 **REFUSE.** *This is what makes the third source bite — and it demands a DECISION, never a declaration, so an ordinary `raise` is discharged by recording “not an enforcement point, argument check”* |
| **REVIEWED-as-enforcement** but **not DECLARED** | **REFUSE** — a point we agreed enforces something and nobody declared |
| **DECLARED** but **not REVIEWED-as-enforcement** | **REFUSE** — a declaration nobody reviewed |
| **reporting** but not **DECLARED** | `UNDECLARED` (Part A-1), and the report refuses |

> **The inventory never forces a declaration. It forces a DECISION.** *That is the
> whole difference between a third source that bites and one that would require
> declaring predicates, and v4 collapsed them by comparing the declaration
> against the inventory directly.*

#### The coverage claim, stated at its real width

**DISCOVERY covers the node kinds it scans and NOTHING ELSE.** Round 2 named four
policy decisions it misses — `Edge.assertable`, `Edge.quarantined`,
`gate.partition_parts`, `gate.exclude_procedural` — **Boolean-returning properties
and collection-returning filters, which are not `raise` / `return False` /
`return None`.** The discovery kinds are widened to cover them.

> 🔴 **And the claim is narrowed in the same breath, because widening a scan can
> never establish that nothing is left:** *a generated inventory is independent
> evidence about the kinds it scans. It is NOT evidence of semantic
> completeness, and this spec does not claim it is.* **What the REVIEWED set
> establishes is that every candidate the scan found got a human decision — not
> that the scan found everything.**

**A known kind the scan does not cover (v12.17): a refusal RETURNED AS A VALUE**, a dict carrying a `refusal` key, is
no discovery kind. At `9d73bdf4` eight sites decide that way, all in the MCP server: 0037's `remember_impl`
(`basis_not_applicable`) and `record_procedure_report` (`attempted_elevation`), and 0031 §4f's `_trust_gates` (three
refusals), `_scope_configuration` (two) and `_unscoped_target_missing` (one). None is DISCOVERED, so none is REVIEWED or
DECLARED, and the census reports nothing about them. Their guarantees are held by their own specs' tests (0031 INV-TT1,
INV-TT7, INV-TT13, INV-TT16, INV-TT17; 0037 §4b), not by this census. Widening discovery to the kind is a Dev-queue
item; until it lands, this paragraph is the limit. The census that found the eight, with its criterion and its
own limit, is research's evidence for this amendment.

### Part A-0-ter — INSTALLED IS DERIVED FROM THE CODE *(round-3 blocker A4)*

🔴 **Round 3: REVIEWED + DECLARED does not establish INSTALLED.** With every
candidate reviewed, every enforcement point declared, **no counters and no
reports**, the three-set reconciliation PASSES and `report_rows()` yields valid
`UNREACHED` rows — **byte-identical for installed-but-unused and for
instrumentation that was never installed at all.** That is the exact distinction
INV-2c exists to draw, and A-0-bis could not draw it **because both of its
authored sets can be true of code that contains no instrumentation.**

> **Two authored lists agreeing proves consistency, not installation.** A-0-bis
> said that about COMPLETENESS and then rested INSTALLED on the same two lists.
> *The third set was derived; the fourth quantity was not, and nobody noticed
> because the derived one was standing next to it.*

#### INSTALLED comes from the code, by two derivations that check each other

| set | how it is derived | who authored it |
|---|---|---|
| **SCAN** | 🔴 a static AST pass for ids carrying **BOTH `declare_site(…)` AND a `.consult`/`.fire` BINDING** (A-0-quater), yielding `(id, module, qualname, line)` | **nobody** — derived from the source |
| **REGISTRY** | the **import-time record**: each `declare_site(id)` registers when its module loads | **nobody** — produced by execution |

**`INSTALLED` is defined at Part A-0-quater.** *(Two superseded definitions are in §11.)*

**The REGISTRY is the CHECK ON THE SCAN, not a second opinion about it:**

| condition | verdict |
|---|---|
| a module LOADED and a scanned site in it did **not** register | 🔴 **REFUSE** — the call is in the source and did not run: dead branch, guarded import, or a site the scan misread |
| a module **did not load** in this process | its sites are **NAMED IN THE REPORT as out of reach**, never silently absent — *a census must state what it could not observe* |
| registered but **not** in the scan | **REFUSE** — something registered that the source does not show |

#### The reconciliation, now over FOUR sets

    DISCOVERED  -> every candidate carries a DECISION in REVIEWED        else REFUSE
    REVIEWED-as-enforcement  ==  DECLARED                                else REFUSE
    DECLARED    ==  INSTALLED (the scan)                                 else REFUSE
    reporting   ⊆  DECLARED                                             else UNDECLARED + refuse

#### 🔴 The reviewer's demonstration, made the standing control

> **Delete a counter while KEEPING its decision and its declaration.** The scan
> loses it → `INSTALLED` ≠ `DECLARED` → **REFUSE.**
> **Keep the counter and send no traffic** → `INSTALLED` has it, `consulted == 0`
> → **`UNREACHED`.**
>
> **Those two must produce different verdicts, and before round 3 they produced
> the same one.** *This is the general control A6-ter states for the harness,
> applied here: for every clause saying “X is established”, delete X and require
> the check to fail.*

**Completing all 738 reviews remains implementation work** — the reviewer said so
and he is right; the refusal on our own tree is honest evidence, not a gap in the
design. **What was missing was the derivation of INSTALLED, and it is here.**

### Part A-0-quater — THE SITE BINDS THE DECISION *(round-4 blocker A4)*

🔴 **Round 4: “registration does not establish working instrumentation.”** With
both fixture decisions executed — the gate declined, ingest returned `False` —
the registry check found no refusals, the four-set reconciliation PASSED, **and
the counters never moved.** All three sites reported `UNREACHED` from empty
counters.

> **A-0-ter derived INSTALLED from a `declare_site` CALL, and a call is a PROXY
> for a counter bound to the decision.** *The scan was honest about what it
> scanned; what it scanned was the wrong thing.*

🔴 **AND OUR OWN CONTROL DEGENERATED.** It was named *“delete a counter”* and it
deleted the `declare_site` LINE, on a fixture that had no counters at all — so it
tested **missing registration** while its name promised **missing
instrumentation**. *The name asserted a property the body did not check: the
item-8 class, in the control written to prevent exactly this.*

#### The decision is expressed THROUGH the site

**So the update and the decision become ONE CALL and cannot be separated:**

```python
SITE = declare_site("gate.answer.unverified-only")
...
with SITE.consult():          # consulted += 1, at the decision
    if not assertable:
        raise SITE.fire(ValueError(...))   # fired += 1, ON the returned decision
```

| | |
|---|---|
| **`INSTALLED`** | 🔴 an id with a `declare_site` call **AND, in ONE function body, BOTH a `.consult()` use AND a `.fire(` use** on the declared name — 🔴 **the body is the LEXICAL one and the name must be UNSHADOWED: a nested function is its own scope, and a parameter or a local assignment rebinding that name is not the site** (round 5). *Not either: a body with `consult` and no `fire` takes traffic that moves `consulted` while a decline never moves `fired`, so the row reads `UNEXERCISED` for a site that FIRED — the exact confusion Part A-1 exists to prevent, reintroduced through a permissive binding rule.* |
| **declared, registered, NOT bound** | **REFUSE** — *“registered, not installed”*, which is precisely what round 4 found and A-0-ter called installed |
| 🔴 **bound in the MODULE but not in one body** | **REFUSE** — *round 5 reproduced v7's scan: `.consult()` in one function, `.fire()` in another, keyed only by variable name, reported `bound=True` and the registry check accepted it. **A scan keyed by NAME answers “does this module mention both” — a different question, true more often than the one asked.*** |

#### Two derivations, and the second is the reviewer's own test made an assertion

| | |
|---|---|
| **STATIC** | the scan above — the code binds the counter to the decision |
| 🔴 **RUNTIME** | **execute ONE declining decision and assert the counters MOVED ACROSS IT: Δ`consulted` == 1 AND Δ`fired` == 1**, measured as the difference between a snapshot before and a snapshot after that decision (Part A-2's snapshot contract). 🔴 **NOT `consulted ≥ 1` / `fired ≥ 1`, which is what v8 asserted: a LEVEL says the counter is positive, and an EARLIER decision can have made that true — “an already-positive counter must not establish that a later decision was measured” (round 5). A level assertion on a counter is the proxy defect this whole Part exists to fix, one level up.** *Exactly one, not at least one: `≥` also passes a site that double-counts.* **And one counter is not enough** — a site bound only for `consult` passes a one-counter assertion while never recording that it fired. *The scan says the binding exists; the execution says BOTH halves of it work. Round 4 is what happens when only the first is checked; round 5 is what happens when the second is checked with the wrong operator* |

#### The controls, with the naming defect fixed

| control | must |
|---|---|
| **strip the wrappers, KEEP the `declare_site` line and the `raise`** · **and separately: keep `.consult`, strip `.fire`** | **REFUSE** — *this is what “delete a counter” was always supposed to mean, and now the fixture HAS counters so the name and the body agree* |
| 🔴 **`.consult()` in one function and `.fire()` in another — same module, same name** · **and: `.fire` inside a NESTED function** · **and: both uses on a name a parameter or local assignment SHADOWS** | **REFUSE** — *the reviewer's round-5 reproduction and its two neighbours, made standing regression checks* |
| 🔴 **counters PRE-LOADED positive, then a decision that never reaches the site** | **REFUSE.** *This is the mutant for the runtime assertion: under `≥ 1` it PASSES. If the check does not fail here it is measuring the counter's HISTORY, not this decision* |
| **full binding, no traffic** | `UNREACHED` |
| **execute a decision** | the counters move **by exactly one each, asserted as a delta** |

> **The fixture must carry REAL COUNTER UPDATES.** *A control cannot delete what
> the fixture never had, and a fixture that cannot present the thing under test
> makes every control over it vacuous — the same finding as round 3's
> compilation-off fixture, one spec over.*

### Part A-1 — THE STATE TABLE *(round-2 amendment A5; the single authority)*

🔴 **This table is the ONE definition. Prose, schema and tests all derive from
it, and where any of them disagreed before, this table wins.** Round 2 found the
spec naming five statuses, the validator supporting four, and its test requiring
four — three carriers of one value, which is the defect this spec exists to
measure.

#### The two counters, defined once

| | |
|---|---|
| **`consulted`** | the site was **REACHED and EVALUATED** — control arrived, the condition was tested |
| **`fired`** | the site **RETURNED A DECISION OTHER THAN THE CALLER'S REQUEST** — refused, quarantined, withheld, abstained, downgraded |

> **`fired` ≤ `consulted` always.** A site cannot decide without being reached.

#### 🔴 SIX statuses, not five — and the sixth is the one the reviewer's question forces

**The reviewer asked for one authoritative reading of `consulted` vs `fired`.
Giving one exposes that FIVE STATUSES CANNOT CARRY IT.** `consulted = 0` and
`consulted > 0, fired = 0` are **different findings**:

- **`consulted = 0`** — the site never ran. *Nothing was asked of the guarantee.*
- **`consulted > 0, fired = 0`** — the site ran and **the guarantee never
  engaged.** *This is exactly `tigerless-labs`' finding in §1: 3,744 memories
  written, supersede edge count **ZERO** — the mechanism executed and its outcome
  never once occurred.*

**Collapsing those two into one `UNEXERCISED` destroys the distinction §1 is
built on**, and it is the `ok`-vs-`na` collapse this spec names at §10.1,
committed inside its own status enum. **So the table has six rows.**

| status | condition | precedence |
|---|---|---|
| **`DISABLED`** | `enabled == false` | **1** — wins over everything; no count is meaningful, and the counts are omitted rather than reported as zero |
| **`UNDECLARED`** | `declared == false` | **2** — see the INV-1 disposition below |
| **`UNMEASURED`** | `errors > 0` | **3** — a counter that raised cannot be read as a count |
| 🔴 **`UNREACHED`** | `consulted == 0` | **4** — *the site never ran.* **NEW at round 3** |
| **`UNEXERCISED`** | `consulted > 0 and fired == 0` | **5** — *it ran; the guarantee never engaged.* **This is the finding the spec exists for** |
| **`EXERCISED`** | `fired > 0` | **6** |

**Precedence is evaluated top to bottom and the first match wins**, so every
`(consulted, fired, errors, declared, enabled)` tuple maps to exactly one status
and no tuple maps to none. *A state table that does not say what happens when two
conditions hold at once is a table with a gap, and the gap is where the
implementations diverge.*

#### 🔴 STRUCTURAL RECONCILIATION RUNS BEFORE STATUS *(round-3 bounded obligation A5)*

**Round 3 found that disabling measurement let an UNDECLARED id through
validation.** The sentence below is dev's, verbatim, and it is the spec BECAUSE
the validator does this — not a description that happens to agree with it:

> **STRUCTURAL RECONCILIATION RUNS BEFORE STATUS AND DOES NOT DEPEND ON
> `enabled`. An id that reports but is not declared, a declared id absent from
> the report, and a duplicate id each REFUSE the report whether measurement is on
> or off. The state table orders STATUSES; it never switches reconciliation off.
> So under `enabled == false` an undeclared reporter's row is emitted with status
> `DISABLED` (precedence 1) AND the report refuses (INV-1) — the row is the
> evidence for the refusal, exactly as for `UNDECLARED` when measurement is on.**

*The precedence table orders what a row is CALLED. It was never a gate on whether
the report is checked, and v5 did not say so — which is how `enabled=false` came
to suppress a refusal that has nothing to do with measurement.*

#### The three things round 2 found unresolved, resolved

| | |
|---|---|
| **`UNEXERCISED` with `consulted=10, fired=0`** | 🔴 **VALID, and it is the central case.** The validator rejecting it was wrong and INV-2's prose was right. *A guard consulted ten times that never fired is the thing we set out to detect.* |
| **`UNDECLARED`: reported or refused?** | 🔴 **BOTH, and that is not a contradiction.** The row IS EMITTED with status `UNDECLARED`, **and the report as a whole REFUSES** (INV-1). *The row is the EVIDENCE FOR the refusal — a refusal that does not say which id caused it is an `ok`-vs-`na` collapse in the other direction.* |
| **negative counts** | **REFUSE the report.** Not a status: a negative `consulted` is not a census outcome, it is a broken counter, and §4's contract is that a broken instrument reports `UNMEASURED` **only when it knows it broke**. A negative it did not notice is worse and must stop the report. |

### Part A-2 — the counter lifecycle and the observation-only contract *(amendment 5)*

**v3.1 left activation unresolved and said nothing about concurrency, snapshot
consistency or partial failure.** Each of those turns a census into a number
nobody can interpret, and the reviewer named all four.

| | |
|---|---|
| **activation** | **opt-in, default OFF** (Quentin, 2026-09-18, *relayed to this seat through dev*). Resolved for v1 rather than deferred |
| **disabled ≠ zero** | a deployment that never enabled it reports `DISABLED` per id (INV-2b). 🔴 *A measured zero and an unmeasured one are the same bytes unless the status distinguishes them, which is this spec's own thesis applied to its own output* |
| **concurrency** | counters are process-local and monotonic; increments are atomic per id. A report names the process it read |
| 🔴 **snapshot consistency — ONE ANSWER (round-2 A5)** | **PER-ID ATOMIC; report-level WINDOW, recorded.** *v4's prose allowed a window while the schema demanded one atomic read under one lock — two answers to one question.* **Per-id is sufficient and a global lock is not**, because every status in Part A-1 is a function of ONE id's tuple: no row depends on another row's counters, so cross-id atomicity buys nothing a reader can use. **The report carries `window_start` and `window_end`**; a report whose window exceeds a deployment-stated bound says so in the header rather than being refused. ⚠️ **And a global lock is the WRONG trade here specifically**: it would serialise the very sites INV-7 must show are unaffected, so the cheap consistency guarantee would be bought by making the observation-only claim harder to hold. |
| **partial failure** | a counter that raised reports `UNMEASURED` for that id **and does not invalidate its neighbours**; the report states how many ids are `UNMEASURED`. 🔴 **An incomplete set of counters must never produce an apparently valid total** |

#### 🔴 THE COMPARED TRACE FIELDS *(round-2 amendment A5 — v4 said these were "named" and named none)*

**A decision trace is an ordered sequence of records, one per enforcement point
REACHED, carrying exactly these fields and no others:**

| field | why it is IN |
|---|---|
| `seq` | the position in the sequence. **Order is the signal**: a census that changed which site runs first has altered a decision even if every site still runs |
| `site_id` | which enforcement point was reached |
| `decision` | the branch taken — the caller's request, or the refusal/quarantine/withhold/abstain/downgrade actually returned |

| field | why it is OUT |
|---|---|
| **wall-clock / duration** | differs between arms **BY CONSTRUCTION** — the instrumented arm does more work. Including it makes INV-7 fail on every run and the failure would carry no information |
| **counter VALUES** | the census is the independent variable. Comparing it across arms compares the thing being varied |
| **record content, user ids, digests** | INV-8 forbids them in the census and they are no safer in a trace |

> **The comparison is `[(seq, site_id, decision), …]` byte-identical across all
> three arms.** *Naming the fields is the whole assertion: “the traces match” is
> unfalsifiable until someone says which bytes, and v4 asserted that someone had.*

#### The third arm *(amendment 5's sharper half)*

**v3.1's INV-7 compared healthy counters against counters forced to error.** The
reviewer's objection is one both arms share a defect:

> *“Comparing healthy counters with failing counters is useful, but both versions
> could introduce the same change to product behavior.”*

🔴 **He is right, and it is this project's own control lesson: two arms that
share the instrument cannot detect the instrument.** So INV-7 becomes a **THREE-ARM
decision-trace diff** — healthy · failing · **UNINSTRUMENTED** — and the trace
fields compared are **named in the spec** rather than left to the harness. *An
uninstrumented reference is the only arm that can show the census changed nothing,
because it is the only one that does not carry the census UNDER TEST. Its census is
an accepted commit's, so a change to the census under test, including its
declaration-time code, is visible to the trace diff.* (The round-16 amendment,
ACCEPTED, v11.0. The sentence it replaces is in §11.)

### Part B — MOVED OUT OF THIS SPEC

🔴 **The refusal harness is no longer part of 0042.** On Quentin's ruling
(2026-09-18) it becomes its own candidate:
`proposals/0043-refusal-harness-CANDIDATE.md` — **allocated 0043 at adoption `1bc2917` from
`allocation.py --next`, read from the registry rather than from a filename or a message.**
🔴 *v4 pointed at `0042B-…`, a placeholder name that was true when written and
dangling from the moment the candidate was renamed — and the gate that catches a
stale reference, `tests/test_spec_gate.py::test_no_spec_names_a_module_or_script_that_does_not_exist`,
matches backticked `.py` names ONLY, so this `.md` would have shipped silently.* *0040 is spent, 0042 is this spec; a filename is not an
allocation, and this project has already paid once for treating one as if it were.*

**It carries round-1 amendments 1, 2, 3 and 6, and invariants INV-3/4/5/6.** It is
moved rather than redrafted, so the new spec starts from the text the reviewer
actually read.

**What this spec still owes it:** nothing. The harness counts its own attempts and
outcomes. **0042 supplies evidence about internal decisions; it does not supply a
denominator** — that dependency was the round-1 reviewer's §9 ruling and its
removal is why the two are separable at all.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| ~~**fixture corpus**~~ | **MOVED with the harness** — the census runs against the PRODUCTION store, which is the point of it |
| **a store where a class never occurs** | 🔴 the census reports **`UNREACHED`** with the id named — *the site was never consulted, which is a different finding from `UNEXERCISED` (consulted, never fired) and the distinction is the point of Part A-1* — **and, if the census was never switched on, `DISABLED` instead (INV-2b), which is a different fact about a different thing** |
| **long-running host** | counters are process-local and reset on restart; a census is a statement about one process's lifetime (§8) |
| **concurrent recalls** | counts may interleave; the census claims totals, never per-request attribution |

## 6. Invariants and executable checks — REQUIRED, blocking

| id | invariant | executable check |
|---|---|---|
| **INV-1** | **CENSUS-TOTAL, FROM TWO INDEPENDENT SOURCES** — every id in the DECLARATION appears in the report, and every reporting id is declared | add a declared id with no site → report REFUSES; add a site with no declared id → report REFUSES. **Both directions, or the check is one source comparing with itself** |
| **INV-2** | **ZERO-IS-A-VERDICT, AND AN ERROR IS A THIRD ONE** — 🔴 **and “zero” is TWO verdicts, not one**: `consulted == 0` → `UNREACHED`, `consulted > 0 and fired == 0` → `UNEXERCISED`, both with the id named (Part A-1); a counter that raised → `UNMEASURED`; never omitted, never `ok` | two fixtures: a never-fired guard asserts `UNEXERCISED`; **a FORCED-RAISE counter asserts `UNMEASURED` and must NOT render `UNEXERCISED`** |
| **INV-2b** | 🔴 **DISABLED IS A STATUS, NOT A MISSING REPORT** — activation is opt-in and default OFF (Quentin, 2026-09-18, *relayed*); a deployment that never enabled the census reports **`DISABLED`** for every declared id. **Never a zero, never `UNREACHED` or `UNEXERCISED`, and never a report-level flag a per-id reader can skip.** **The enum and its precedence live in Part A-1 and nowhere else** | run the report with the census off; assert every row reads `DISABLED` and that NO row reads `UNEXERCISED` |
| **INV-2c** | 🔴 **INSTALLED IS NOT EXERCISED, AND RUNTIME CANNOT TELL THEM APART** (amendment 4) — *a correctly installed site with no traffic and a MISSING site both produce no runtime events.* So INV-1's missing-site check is settled against the **AST inventory**, never against runtime counts | 🔴 **the missing-site check compares the DECLARATION against the REVIEWED set, never against DISCOVERED (Part A-0-bis)** — four checks, each with its own fixture: **installed-but-unused** (asserts 🔴 **`UNREACHED`**, not missing — *`consulted == 0`; v4 said `UNEXERCISED` and the six-status change reached A-1 and INV-2 but not this row*) · **missing** (🔴 **REVIEWED-as-enforcement, absent from the declaration → REFUSE** — *v4 compared the raw inventory to the declaration, which would demand declaring every ordinary `raise`; Part A-0-bis*) · **undeclared** (reports an id nobody declared → REFUSE) · **duplicate id** (two sites, one id → REFUSE) |
| **INV-2d** | 🔴 **TWO AUTHORED LISTS AGREEING PROVE CONSISTENCY, NOT COMPLETENESS** (amendment 4) — the declaration and the report are both authored; their agreement cannot establish that neither omits the same point. **The third source is the AST inventory, which nobody authored** | 🔴 assert the report REFUSES when a **DISCOVERED candidate has NO DECISION in the REVIEWED set** — *not when it is absent from the DECLARATION, which round 2 showed would require declaring every ordinary `raise`. The inventory forces a DECISION, never a declaration (Part A-0-bis)* |
| **INV-7** | **OBSERVATION-ONLY** — no counter may alter a decision, **established against census code that CHANGES BEHAVIOUR, not against census code written to ATTACK THE MEASUREMENT: the observer and its evidence machinery are trusted parts of the measurement** (the round-19 scope, ACCEPTED; v12.0; the record after this table) | **a THREE-ARM DECISION-TRACE DIFF, not a green run** (amendment 5; the two-arm form is withdrawn because both arms carry the instrument): capture the trace with counters **healthy**, **forced to error**, and **UNINSTRUMENTED** — *the product with every measurement removed, whose census is the census.py of an ACCEPTED commit T, pinned by digest in this specification (the ACCEPTED record after this table), and never the census under test; no census code of the commit under review runs in the reference arm* (the round-16 amendment, ACCEPTED; v11.0) — over **the trace fields listed in Part A-2's table below**, and assert all three are **byte-identical**. Name the suites that actually reach the instrumented sites — **0027's (graph.py) and the gate/ingest/schema suites**. 🔴 **NOT 0041's**: it is accepted and UNIMPLEMENTED, its tests are frozen-record transition tests with eleven strict xfails, and none exercises a gate decision — **forcing counters to error there changes nothing they can observe, so that half would pass vacuously** |
| **INV-8** | **COUNTS CARRY NO CONTENT** — a census row is an id and integers | assert no record text, user id, or digest appears in the report |

**Each check must be demonstrated RED** against a deliberately wrong
implementation before it is accepted — an undemonstrated control is the defect
this spec exists to find.

> 🏁 **THE ROUND-16 AMENDMENT TO INV-7 — ACCEPTED** by the round-16 verdict (banked `a17ebc7`, body sha16 `fb62c45af45289a7`):
> "*design amendment ACCEPTED; implementation RETURNED for one correction*". It was proposed in v10.0 by research as the
> specification's author, on the owner's word "(3) Accepted census" (2026-09-24). Its text now lives in the INV-7 row above,
> and in Part A-2's third-arm reason.
>
> **What was accepted, as the proposal stated it:**
> 1. The reference arm contains a census, T's. "Census-free" now means "free of the census under test".
> 2. **The residual:** a declaration-time defect present in both T and HEAD is shared by all four arms. It is bounded by T
>    being externally accepted.
> 3. **Advancing T** (to a later commit whose census an external round has accepted) is a SPEC change, recorded here with its
>    digest. It is never a constant edit.
> 4. **HEAD's product may import only census names T defines,** and HEAD's `Site` must be T's `Site`. A difference is refused
>    by `derive()` as "T must advance"; how it is detected is stated under the round-16, round-17 and round-18
>    implementation notes.
>
> **T, pinned here:** commit `5d835e1453d9265acdbb60e3f9732ad7ebeffd2b`; its census.py, tracked as
> `specs/evidence/0042/reference_census.py`, has sha256 `69beb1bb2f058d97de646638ec103f799c8e8e0e7c11b2abb196a3f41800683f`.
>
> **Evidence:** the separating cells
> (`tests/test_0042_inv7.py::test_r16_the_mutant_changes_a_decision_at_all`,
> `tests/test_0042_inv7.py::test_r16_the_reference_census_separates_a_declaration_time_defect`), the pin
> (`tests/test_0042_inv7.py::test_r16_the_twin_census_is_the_reference_census_and_verify_refuses_any_other`), and the
> drift check (`tests/test_0042_inv7.py::test_r17_site_drift_reads_the_definition_and_the_realized_class`).

> 🏁 **THE ROUND-19 SCOPE OF INV-7 — ACCEPTED** by the round-19 verdict (banked `496a120`, body sha16 `7d2135a69dff4081`):
> "*the proposed INV-7 scope addition is ACCEPTED; the implementation is RETURNED for two corrections*". It was proposed in
> v11.3 by research as the specification's author, on the owner's word "Disclose + state it" (2026-09-25). Its text now
> lives in the INV-7 row above and in §3b.
>
> **What was accepted, in the verdict's words:** "*INV-7 establishes its observation-only claim against behavior-changing
> census defects, while excluding census code deliberately written to attack the measurement. The observer and its
> evidence machinery are trusted parts of this regression measurement. Resistance to hostile census code that rewrites the
> describer, recorder or evidence is not a requirement under this accepted scope.*"
>
> **What it does NOT do, also in the verdict's words:**
> - "*This ruling accepts the scope now; it does not turn an unstated assumption into an earlier explicit approval.*" The
>   acceptances of rounds 5 and 16 were of INV-7 without this clause (§11).
> - "*Ordinary defects, type collisions, incidental diagnostic output and resolver mistakes remain within the
>   implementation review.*" The scope excludes an ATTACK on the measurement, never a defect. The round-19 verdict's two
>   findings were of that kind, and round 20 answers them.
>
> **Why it cannot be a checked property.** Python has no in-process confinement. Any reading made inside a process that
> executed census code can be rewritten by that code:
>
> | reading | where it runs | inside a process that ran the census? |
> |---|---|---|
> | route A, `Site`'s definition as written | the transform, reading source | **no**, but it reads only the ClassDef, never a statement after it |
> | route B, the realized `Site` described | a fresh interpreter per census (round 19) | **yes**, the child that executed it |
> | the realized-`Site` digest (`uninstrumented:site_realized_equal`) | each arm | **yes** |
> | the decision trace itself | each arm's observer | **yes** |
>
> **EXECUTED, and re-run by the reviewer at round 19:**
> - **Route B forged, SILENT.** The round-19 spoof alone reads one drift entry. With four more lines appended, which install a
>   name-trusting predicate into the describer, it reads **none, while the decision still changes.** The same attack
>   **with no import statement** also reads none: it reaches `sys` through `object.__subclasses__()`. So an allowlist of the
>   census's imports cannot close this, even one derived from T's.
>
>   *(v12.9.1: at round 28's pin these two forges read REFUSED, not silent: the predicate they install is Python code, and
>   round 28's guard stops it before its first line. Two variants measured there by the second seat's forge probe,
>   shipped with the round-28 package:*
>   - *the describer's immutability test replaced by a C callable: REFUSED by round 27's fail-closed rule;*
>   - *the entry point replaced: the census asks the real describer for its own `Site`'s description before its spoof,
>     then binds route B's `site_description` to a C callable returning that description. It reads **none, while the
>     decision still changes**.*
>
>   *The boundary this record states therefore stands, executed: code that can rewrite the child can rewrite what it
>   reports. Such a forge is an attack on the measurement, outside the accepted round-19 scope.)*
> - **A trace erased, LOUD.** Four appended lines replace the observer's recorder in an arm: 519 records become 0, and the
>   arm's suite stays green. An empty trace reads DIVERGENT against the reference arm, so this move is detected.
>
> **INFERRED, NOT BUILT, and not promoted by the acceptance:** **a SILENT trace forge**, in which the census changes a decision
> and records the reference arm's label for it. The write access it needs is shown above. The forge is not. The verdict:
> "*This review does not promote it to measured evidence, and does not require it to be built to accept the stated
> boundary.*" **Nothing in this specification claims that this move is detected.**
>
> **Route B's fresh interpreter protects the TRANSFORM, not the DESCRIPTION** — in the verdict's words, "*it does not make
> the child's description tamper-resistant*".
>
> **Evidence:** research's probe, repository veracium-research at commit 99a110ec (probe and transcript under its
> probes directory), shipped in the round-19 package; dev's trace run, `specs/evidence/0042/trust_boundary_probe.py` with its recorded output `specs/evidence/0042/trust_boundary_probe.txt` (committed at `9932c7f`, and reproduced from a clean export by the second seat); the stated limit in the docstring of `_described_in_isolation` in
> `specs/evidence/0042/inv7_uninstrument.py`.

## 7. Failure modes and reversibility

| failure | consequence | reversal |
|---|---|---|
| a counter raises | 🔴 **must not fail the caller** — the decision is the product; the measurement is not. The row's `status` becomes **`UNMEASURED`** and `errors` increments (§4 step 3), which is a FIELD and not prose | remove the counter; no stored state |
| the registry and the call sites drift | INV-1 turns it into a refusal rather than a silent gap | — |
| the declaration omits a point the code has | **INV-2c/2d: the AST inventory is a third source neither list authored** — 🔴 and a DISCOVERED candidate carrying **no DECISION in the REVIEWED set** is a REFUSAL *(not one absent from the declaration; Part A-0-bis)* | re-run the inventory; it is derived, not maintained |
| counts leak content | INV-8; counters take an id and an integer only | — |

**Fully reversible.** No schema change, no stored field, no migration.

## 8. Claims and limits

**Claimed:** for a named deployment and a named read window, **which declared
enforcement points were INSTALLED, which were EXERCISED, which were not, and
which could not be measured** — each id carrying one of the SIX statuses in Part A-1's table. 🔴 **NO
RATE IS CLAIMED HERE.** v3.1 claimed a refusal rate beside a baseline arm; that
claim, its arms and its denominator argument all travelled to the harness spec
with the round-1 reviewer's §9 ruling.

**NOT claimed:**
- that a zero-count guard cannot fire — only that **this corpus never presented
  the condition** (§2c-ii)
- 🔴 **that the census generalises beyond THIS deployment and THIS process
  lifetime.** A census is a fact about what ran where it ran (§5)
- 🔴 **semantic completeness of discovery.** The inventory is evidence about the
  node kinds it scans; **widening a scan can never establish that nothing is
  left** (Part A-0-bis)
- 🔴 **a rate of any kind.** The census reports statuses and counts. Every rate in
  this arc belongs to the harness spec

> 🔴 **THREE HARNESS LIMITS WERE REMOVED FROM THIS LIST AT ROUND 3** — *the
> fixture generalising to a production store* (the census has no fixture and §5's
> row moved out), *comparison to another system's published refusal figures* (the
> census publishes no refusal figure), and *the answer-quality limit* whose
> sentence **had already been MOVED to 0043 §8 by a note in this file and
> survived here anyway.** **That is the reviewer's C4 — “remove obsolete harness
> claims from 0042” — and a limit that names an artifact the spec no longer has
> is not caution, it is a claim about the wrong document.**

## 9. Brief for the external reviewer — ROUND 5

🔴 **This §9 named ROUND 2 until now, and four packages sealed with it.** *The
pre-seal rule refuses a §9 naming a returned round; no stage script gated §9 for
this arc, so the brief went out four times describing questions the reviewer had
already answered. **A section that states its own round is a carrier of the round
number, and nothing was re-deriving it.*** The sealing script now refuses a
mismatch.

**Rounds 1–4 are answered and not re-asked.** The split, the six-status table, the
three sets, the derivation of `INSTALLED`, and the removal of harness claims are
settled. **A6 closed at round 4.** Round 4's A4 is answered by Part A-0-quater,
and the two questions below are what that answer leaves open.

### The questions this round asks

1. 🔴 **Is “both derivations” enough for `INSTALLED`?** A-0-quater derives it
   statically (the scan requires a `declare_site` **and both** a `.consult()` and
   a `.fire(` in one body) and dynamically (execute a declining decision; both
   counters must move). **Both run over a FIXTURE.** *Should the runtime
   assertion be required to run over the PRODUCT's real suites once `src` carries
   its first site — and if so, is a suite that never presents a declining
   condition for some site a gap the census must report, or a fact about the
   suite?*
2. **Does the four-set reconciliation now rest on anything still authored?**
   DISCOVERED and INSTALLED are derived; REVIEWED and DECLARED are authored by
   construction. *We believe the refusals are placed so that no authored pair can
   agree its way past a missing binding — we would rather be told early if a
   pair remains that can.*

> 🔴 **ANSWERED, round 5 — recorded beside the question, which is left as
> dispatched:** *“require runtime checks at real product sites once implemented,
> alongside the three-arm decision-trace comparison. **A suite that never supplies
> a declining case is a test coverage gap.** The census should continue reporting
> observed statuses: `UNREACHED` when never consulted, or `UNEXERCISED` when
> consulted without firing.”* **And on authored agreement:** *“corrected
> independent scans prevent the authored sets from agreeing past a structurally
> missing binding. Human decisions about which candidates constitute enforcement
> remain a semantic review responsibility.”* — *so A-0-bis's two-authored-lists
> hazard is answered by the scan, not by more authorship, and the residual
> judgement is named as judgement.*

### What we are NOT asking

**Whether 738 reviews are complete.** *Round 3 ruled that implementation work and
round 4 did not reopen it; the tree's red on `installed_sites` is the honest
state and the test is written to fail the day the first real site lands.*

## 10. Open questions

1. ⚖️ **RULED 2026-09-18 — INSTRUMENT PRODUCTION.** Quentin: *"if the census
   instrumenting production will give us better results then we should go that
   direction."* **It does, and the reason is stronger than "better": the replay
   variant is STRUCTURALLY INCAPABLE of answering the question.**

   `Memory.recall` writes a receipt under `if receipt_raw is not None:` — **the
   record exists only when the lane FIRED.** So a replay census over receipts:

   - **cannot observe a zero.** No receipt is written when nothing fires, so
     *"never fired"* and *"never invoked"* produce the same evidence — **exactly
     the distinction this spec exists to draw**, and the `ok`-vs-`na` failure one
     level up
   - 🔴 **cannot observe INSTALLATION, which is a second blindness and the one
     amendment 4 names.** The bullet above is about *never fired* vs *never
     invoked*; this one is about **a site that was never INSTALLED.** A missing
     site and a correctly installed site with no traffic write **the same
     nothing**, so no replay over receipts can implement INV-1's missing-site
     check. *That is why the check settles against the REVIEWED set (Part
     A-0-bis) rather than against runtime evidence.*
     *(v4 history: this bullet once cited §1's argument that Part B needs Part
     A's denominator — a claim §1 no longer makes. The round-2 rewording then
     restated the bullet above it instead of saying this; **a correction that
     duplicates its neighbour is a correction that did not land**, and dev caught
     it reading the two in sequence.)*
   - **sees one mechanism.** Supersession, correction, `forget_user`, quarantine
     promotion and the reserve write no `policy_receipt`; the candidate set is
     five and receipts cover one

   **Consequence, accepted with the ruling: `Path: full`, external review
   required** (the counters land in guarded files). **The replay variant is
   withdrawn, not deferred** — keeping it as a fallback would invite a later
   seat to take the cheap half and report zeros it cannot see.
2. ⚖️ **RULED — no longer open.** *Always-on or opt-in?* **Opt-in, default OFF,
   with `DISABLED` reported per id** (Quentin, 2026-09-18; **that ruling reached
   this seat RELAYED through dev, marked so a later reader can tell which rulings
   arrived first-hand**). Implemented at Part A-2 and INV-2b. *v4 left this open
   while two other sections recorded it ruled — a clause and its open question are
   two carriers of one value, and this project has had them disagree before.*
3. **Should `policy_receipt` carry the enforcement-point ids?** It would make the
   census durable and queryable rather than process-local — but it is a schema
   change and 0027 v14 has just shipped.
4. ~~**Who is the blind examiner?**~~ · ~~**How many questions per class?**~~
   **Both MOVED to the harness spec** — they are questions about an examiner and a
   rate, and this spec has neither.

---

## 11. Superseded decisions *(round-4: the reviewer read struck-through passages as live requirements)*

🔴 **This section exists because the practice of annotating in place was
CAUSING THE HARM IT PREVENTS.** Recording what was tried stops a later seat
re-deriving a failed answer — that is real and it is why the history is kept. But
**a superseded passage sitting inline in a normative section is read as a
requirement**, and round 4's reviewer did exactly that.

> **So the rule is refined rather than abandoned: THE HISTORY IS KEPT, AND IT
> LEAVES THE NORMATIVE BODY.** *A marker saying “this is not a requirement” is a
> PROXY for not being a requirement, and this arc has spent four rounds learning
> what proxies do. Structure asks nothing of the reader; a marker asks them to
> read more carefully than they just did.*

### The declaration compared against the raw inventory — superseded

**v4's §4 A-0 compared the declaration against an “INSPECTED SUBSET” of the
inventory while INV-2d refused on any absent site.** *Round 2: with 636 syntactic
candidates that means declaring every ordinary `raise`.* **Superseded by
A-0-bis's three sets — the inventory forces a DECISION, never a declaration.**

### `INSTALLED` — two superseded definitions

| version | definition | what it missed |
|---|---|---|
| **v5** (A-0-bis) | the declaration plus the ids that report at runtime | **Round 3: satisfied by code containing no instrumentation at all.** Both inputs were AUTHORED — and A-0-bis's own text said two authored lists agreeing proves consistency, not completeness |
| **v6** (A-0-ter) | a static scan for `declare_site(…)` calls | **Round 4: a registration is a PROXY for a counter bound to the decision.** Both fixture decisions executed, reconciliation passed, counters never moved |
| **v7** (A-0-quater) | the scan of the **BINDING** — `declare_site` **and** a `.consult`/`.fire` use, accumulated **over the MODULE and keyed by variable name** | **Round 5: “does this module mention both” is a different question.** `.consult()` in one function and `.fire()` in another reported `bound=True`; nested scopes and shadowed names were invisible to it. *The binding was right and the SCOPE it was checked over was wrong* |
| **v8** (A-0-quater) | the same binding, 🔴 **function-local, lexical and unshadowed**, with the runtime leg asserting **DELTAS across the decision** rather than positive levels | *current* |

### INV-7's "without a census in it" — superseded by the round-16 amendment *(v11.0)*

Part A-2's third-arm reason read, from amendment 5 until v11.0: "*An uninstrumented reference is the only arm that can show the
census changed nothing, because it is the only one without a census in it.*" Round 15 showed that "without a census" cannot
hold together with a reference faithful by construction, because a declaration binds a census object. Round 16's amendment,
ACCEPTED (verdict `a17ebc7`, body sha16 `fb62c45af45289a7`), replaced "without a census" with "without the census UNDER TEST",
where the reference's census is an accepted commit's, pinned by digest.

### INV-7 and §3b without a stated scope — superseded by the round-19 scope *(v12.0)*

From the round-5 acceptance until v12.0, INV-7's row read "*no counter may alter a decision*", and §3b read "*observation-only
and cannot alter a decision*", with no statement of which census code the claim was established against. Every reading
INV-7 takes inside a process that ran census code could be rewritten by that code, so the unscoped claim was an assumption
the text did not state. Round 19 disclosed it, and the round-19 verdict (`496a120`, body sha16 `7d2135a69dff4081`) ACCEPTED
the scope: "*against behavior-changing census defects, while excluding census code deliberately written to attack the
measurement*". The verdict is explicit that this "*accepts the scope now*", and "*does not turn an unstated assumption into
an earlier explicit approval*".

### The “delete a counter” control — superseded

**v6's control deleted the `declare_site` LINE on a fixture with no counters**, so
it tested missing *registration* under a name promising missing *instrumentation*.
**The name asserted a property the body did not check.** v7's fixture carries real
counter updates and the control strips the binding while keeping the declaration.

## Review closure

This spec's ledger runs from the pre-split round 1 (0042 v3.1, one document) through round 5, which accepted the design, and then through the implementation rounds 6 to 23, the last of which accepted the implementation. Rounds 2–5 were dispatched in one package with 0043, whose own ledger starts at its round 1 (= package round 2); rounds 6 to 23 were 0042's alone.

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
> "five external rounds" or "N of the M rows" — hand-carried counts
> in the one section of this document whose entire subject is that a summary
> maintained beside the thing it summarises drifts. **Implementation review then
> added rounds and rows to this ledger** (rounds 6 to 23), and both figures would
> have been quietly wrong, in a paragraph introducing a generated block that has
> them right.


<!-- GENERATED:review-closure -->

**0 internal round(s) and 23 external round(s) with a returned VERDICT are recorded for `0042`; 23 package(s) were dispatched** — counted from `specs/reviews.py`, which is the source this block is generated from. A round appearing here and not there, or the reverse, is impossible by construction. **SENT rows are dispatch records, not outcomes**, and are labelled below so the two are never summed.

| round | date | findings raised (from `raised=`) | verdict (compressed) |
|---|---|---|---|
| external 1 (SENT) | 2026-09-18 | — | SENT (round-1 package 178b0d861be8c4bce0b6e9928b025531a1b43154145c1ec4dd6cfe7b13281f2a @ pin 5121501458b8ed78469d05aff45140b9cd217225, CI 35299877700; 0042 v3.1; fresh-clone capture at the pin: 3283 passed, 11 skipped, 11 xfailed, 2 warnings in 639.03s (0:10:39)). 0042 v3.1 — the line's first dispat… |
| external 1 (verdict) | 2026-09-18 | 6 | RETURNED FOR AMENDMENT — six amendments over one document: (1) define the rates and their measurement windows; (2) the proposed examiner input violates blindness; (3) define an independent outcome judge and question-level reference labels; (4) separate installed instrumentation from observed traffic… |
| external 2 (SENT) | 2026-09-18 | — | SENT (round-2 package 5253ab921c898881ee9e066937f6edbca96fab52d2b3a4e43bb46224ca577cbc @ pin 1bc29178014016d040e8cdb1ee92d81420970244, CI 35342079472; 0042 v4; fresh-clone capture at the pin: 3299 passed, 9 skipped, 11 xfailed, 2 warnings in 641.21s (0:10:41)). 0042 v4 — the census alone after the s… |
| external 2 (verdict) | 2026-09-18 | 2 | Both specifications are returned for amendment. Census side, two of six: A4 — The AST inventory cannot yet support the completeness claim. A5 — The census schema and comparison contract remain inconsistent. Verdict banked verbatim at `0042-round2-verdict-verbatim.md`, file sha16 c6ac407ec6d172c8, bo… |
| external 3 (SENT) | 2026-09-18 | — | SENT (round-3 package 61978df8fe0cfd1170c6cd71bfb06ab6ffa51c6667702ab929f1dd738540f415 @ pin f33f5bc2feab1798ba11f5cfd4ebc8e335ca451d, CI 35364857448; 0042 v5; fresh-clone capture at the pin: 3318 passed, 11 skipped, 11 xfailed, 2 warnings in 667.77s (0:11:07)). 0042 v5 — A4 answered by the reconcil… |
| external 3 (verdict) | 2026-09-18 | 3 | Both specifications are returned for amendment, with three remaining design blockers. Census side: A4 — Reviewed and declared does not establish installed. Bounded, not design: A5 — `errors > 0` correctly takes precedence over zero consultations. And the observation-only evidence bound (branch-seque… |
| external 4 (SENT) | 2026-09-18 | — | SENT (round-4 package 51887b16bbabc8b9616268958acedd101b1e6c1be3cfe1d214d8d653ddff9058 @ pin 43c1c637cef4372dadcf315a23f06ae8e1c8100d, CI 35373684787; 0042 v6; fresh-clone capture at the pin: 3330 passed, 11 skipped, 11 xfailed, 2 warnings in 685.41s (0:11:25)). 0042 v6 — Part A-0-ter: INSTALLED der… |
| external 4 (verdict) | 2026-09-18 | 2 | Round 4 verdict: returned for amendment. Census side: A4 — Registration still does not establish working instrumentation. Advisory: Consolidating the superseded passages would also help prevent old timeout and installation wording from being mistaken for current requirements. Verdict banked verbatim… |
| external 5 (SENT) | 2026-09-18 | — | SENT (round-5 package 791c1089776d9f49332483f8ff88b25794dec795ee8a7cf8eb33b441eaa1747a @ pin a9d3622d6252a19387b2ecb66a665f101825fb36, CI 35382261953; 0042 v7; fresh-clone capture at the pin: 3339 passed, 11 skipped, 11 xfailed, 2 warnings in 750.36s (0:12:30)). 0042 v7 — Part A-0-quater: the site B… |
| external 5 (verdict) | 2026-09-18 | 2 | Round 5 verdict: both specifications are accepted at the design level and may proceed to implementation. 0042 v7: ACCEPTED — DESIGN, frozen scope INV-1, INV-2, INV-2b–2d, INV-7, INV-8. One implementation obligation carried: make the binding scan function-local and scope-aware. Document maintenance: … |
| external 6 (SENT) | 2026-09-20 | — | SENT (round-6 package f218d0dc4dca342396c9cc8179fe2728cdebf82b37cfd3ec0234a520933afa8c @ pin 4e5f44554f3e858bbec3045f23522bad4b988dc2, CI 35521603434; 0042 v9.2; fresh-clone capture at the pin: 3658 passed, 11 skipped, 2 warnings in 1004.61s (0:16:44)). The line's first implementation package, on ro… |
| external 6 (verdict) | 2026-09-20 | 7 | RETURNED FOR AMENDMENT — implementation review (the round-5 design acceptance intact); seven implementation findings. Findings: 0042-R6-1 — Measurement failures are not consistently contained or reported (failed trace recorder raises; failed classifier reads UNEXERCISED; failed consult increment giv… |
| external 7 (SENT) | 2026-09-21 | — | SENT (round-7 package bfd5147841c5d6aca6fdc607b2f178a9e17cad954675038ed72da3ce157f5517 @ pin 12d06a5ba58deb6b58f16d133c3d26aaf75cf958, CI 35548869507; 0042 v9.2; fresh-clone capture at the pin: 3677 passed, 11 skipped, 2 warnings in 1055.12s (0:17:35)). Answers the round-6 verdict; first seal. |
| external 7 (verdict) | 2026-09-21 | 4 | RETURNED for implementation corrections (R6-1, R6-2, R6-7 closed; R6-3 to R6-6 partially resolved); four findings. Findings: 0042-R7-1 — Complete report validation remains optional — INV-1 / INV-2c (two-argument validate_report returned no refusals for a removed registration); 0042-R7-2 — The bindin… |
| external 8 (SENT) | 2026-09-21 | — | SENT (round-8 package 3372664089d487bb74c49fe05e4b4f303fb3b3e1dd7a70a5e80e91de5968a277 @ pin 301981002c6f2381ff7a138c89ed4d6cd07056ec, CI 35592729466; 0042 v9.3; fresh-clone capture at the pin: 3764 passed, 9 skipped, 2 warnings in 1037.96s (0:17:17)). Answers the round-7 verdict; three discarded se… |
| external 8 (verdict) | 2026-09-21 | 3 | RETURNED for implementation corrections (R7-1 closed; R7-2 to R7-4 partially resolved); three findings. Findings: 0042-R8-1 — Nested imports can replace a declared site without detection — INV-2c (import ... as S / from ... import ... as S under global S read bound=True); 0042-R8-2 — A missing contr… |
| external 9 (SENT) | 2026-09-21 | — | SENT (round-9 package 1b4d511195789e34574772272eae19cf0829c237032df913dbf71e9049d51ef5 @ pin fe854330181ebbf2918d521cbdc19eff9cbf4cdb, CI 35624583304; 0042 v9.4; fresh-clone capture at the pin: 3767 passed, 11 skipped, 2 warnings in 1069.09s (0:17:49)). Answers the round-8 verdict; three discarded s… |
| external 9 (verdict) | 2026-09-21 | 1 | RETURNED for one implementation correction (R8-1, R8-2 closed; R8-3 partially resolved). RULING on the authors' questions: 'carrying the existing capture forward is reasonable here, supported by the reproduced manifest, digest and current-harness comparison. The disclosed limits of the static gate a… |
| external 10 (SENT) | 2026-09-21 | — | SENT (round-10 package b1e66ae592677410bd810e224c856b51ec206e54b169545921eedc00747172d4 @ pin 0f188134e67b8017b2a1ad43ddd0f3192002a19b, CI 35662875033; 0042 v9.4; fresh-clone capture at the pin: 3771 passed, 11 skipped, 2 warnings in 1065.08s (0:17:45)). Answers the round-9 verdict; first seal. |
| external 10 (verdict) | 2026-09-22 | 2 | RETURNED for two implementation corrections. Findings: 0042-R10-1 — Nested code can still replace the census alias (global assignments, nested imports, generator-expression walruses bypass the binding check; True->False, verify clean); 0042-R10-2 — Unrelated census imports are still deleted — alias … |
| external 11 (SENT) | 2026-09-22 | — | SENT (round-11 package 262970ca8a0a2fd3ce32b860af9340c9e199a0feec04e1546af6d94bce0e1982 @ pin 1af8292a936c72fec8a4c442bf9fbbec3d8b223d, CI 35721052980; 0042 v9.4; fresh-clone capture at the pin: 3773 passed, 11 skipped, 2 warnings in 1085.18s (0:18:05)). Answers the round-10 verdict; one discarded s… |
| external 11 (verdict) | 2026-09-22 | 2 | RETURNED for corrections (the round-10 reproductions fixed); two findings. Findings: 0042-R11-1 — Mixed and surface imports can lose live bindings, causing NameError while verify() reports clean; 0042-R11-2 — The enumeration gate permits independent decisions inside functions that call a predicate. … |
| external 12 (SENT) | 2026-09-23 | — | SENT (round-12 package 38e617c6c9b99ce388ecaaf5dabf05d405a8797be46a9f6151268128c583ffc2 @ pin 88d67801226af0be84838c9da710c38edda4071c, CI 35848645443; 0042 v9.4; fresh-clone capture at the pin: 3867 passed, 9 skipped, 2 warnings in 1102.68s (0:18:22)). Answers the round-11 verdict; one discarded se… |
| external 12 (verdict) | 2026-09-23 | 2 | RETURNED for two acceptance-check corrections (the round-11 import and gate findings fixed). Findings: 0042-R12-1 — The disclosed scope-order gap changes a measured decision from [True] to [False] while verify() reports clean and the manifest records zero unresolved candidates; 0042-R12-2 — Removing… |
| external 13 (SENT) | 2026-09-23 | — | SENT (round-13 package 259c01c9bf42676f1a9e81e58055335e59f3237f6f38fd49ca1c77194e8d0866 @ pin d7fbb2e59b90a818327c2bd4d317dbfbce1ad732, CI 35909763525; 0042 v9.5; fresh-clone capture at the pin: 3938 passed, 11 skipped, 2 warnings in 1110.45s (0:18:30)). Answers the round-12 verdict; first seal. |
| external 13 (verdict) | 2026-09-23 | 2 | RETURNED for two acceptance-check corrections. Findings: 0042-R13-1 — Site-reachability gaps still produce broken twins with clean verification; 0042-R13-2 — The scan-to-runtime check omits property setters, allowing false binding evidence. Verdict banked verbatim at `0042-round13-verdict-verbatim.m… |
| external 14 (SENT) | 2026-09-24 | — | SENT (round-14 package a6eb623cdb3eaf93de1760237aa1263f5ec142c269ce7e24edcecf2d4c88f8a7 @ pin 8074e6b3ab37bb98de777d1a240ff6f64a029bdd, CI 35964658381; 0042 v9.6.1; fresh-clone capture at the pin: 3956 passed, 11 skipped, 2 warnings in 1218.08s (0:20:18)). Answers the round-13 verdict; first seal. |
| external 14 (verdict) | 2026-09-24 | 1 | RETURNED for one INV-7 acceptance-check correction (both round-13 findings fixed on their reproduced cases). Findings: 0042-R14-1 — The new stand-in can still change an instrumented decision from True to False while verification is clean and its use counter stays at zero. Verdict banked verbatim at … |
| external 15 (SENT) | 2026-09-24 | — | SENT (round-15 package c95dcdf9b62788600274c4e0f4e8357744c4b7f977455407b0f66647f4d893bf @ pin 5d835e1453d9265acdbb60e3f9732ad7ebeffd2b, CI 36019828967; 0042 v9.7; fresh-clone capture at the pin: 3977 passed, 11 skipped, 2 warnings in 1210.15s (0:20:10)). Answers the round-14 verdict; first seal. |
| external 15 (verdict) | 2026-09-24 | 2 | RETURNED (the round-14 class mismatch fixed); the reference arm executes the census's declaration code, and retaining that construction requires an explicit design amendment; plus three child-process import failures in the independent suite. Findings: 0042-R15-1 — the new reference arm executes the … |
| external 16 (SENT) | 2026-09-24 | — | SENT (round-16 package 3ab5290685e2c81cbda534547e2e56c3bf4f705a11a11e010d3b9e7ce5bfa944 @ pin f5b1117f1142c01d7883343790ddb66cbef800ed, CI 36064506675; 0042 v10.0.1; fresh-clone capture at the pin: 3993 passed, 11 skipped, 2 warnings in 1129.45s (0:18:49)). Answers the round-15 verdict; first seal. |
| external 16 (verdict) | 2026-09-24 | 1 | design amendment ACCEPTED (INV-7's reference arm carries the census of an accepted commit T, pinned by digest); implementation RETURNED for one correction (the round-15 import-path failures fixed). Findings: 0042-R16-1 — The new Site drift check loses statement order and duplicate definitions. Two r… |
| external 17 (SENT) | 2026-09-25 | — | SENT (round-17 package 73dd2f6662f5bd189c820c4a6882764302681ff2eff299bb25a087be3cbf4b49 @ pin 4e477aaf7e0e1147dc8b29404b486834672ec2db, CI 36083291144; 0042 v11.0.1; fresh-clone capture at the pin: 4006 passed, 11 skipped, 2 warnings in 1137.08s (0:18:57)). Answers the round-16 verdict; first seal. |
| external 17 (verdict) | 2026-09-25 | 1 | RETURNED for one implementation correction (the round-16 finding closed; the design amendment remains accepted). Findings: 0042-R17-1 — The new function normalizer omits writable __name__, __qualname__ and __module__ metadata (Site.fire.__name__ = 'changed': drift checks and verify() return []). Ver… |
| external 18 (SENT) | 2026-09-25 | — | SENT (round-18 package c0d20d7a243a76cc06c343e80918ede0cdb2f042cce8c5490200de5180e9b5d1 @ pin 5336c0a4d096748195f2cf2c3b9fa22e715b0f4a, CI 36101025021; 0042 v11.1; fresh-clone capture at the pin: 4030 passed, 11 skipped, 2 warnings in 1182.09s (0:19:42)). Answers the round-17 verdict; first seal. |
| external 18 (verdict) | 2026-09-25 | 1 | RETURNED for one implementation correction (the round-17 finding closed). Findings: 0042-R18-1 — normalization confuses built-in types with subclasses sharing their names (class tuple(tuple) spoof in Site.__slots__ accepted by drift checks, derive, verify and the runtime gate). Verdict banked verbat… |
| external 19 (SENT) | 2026-09-25 | — | SENT (round-19 package 8d8d56689b97f28d8e5a1120b807e72959ed559869c2c72fe157c0e321eeaf79 @ pin 6a7c79658a7b06138938fab0b249ae7e2beead95, CI 36171884544; 0042 v11.3; fresh-clone capture at the pin: 4047 passed, 11 skipped, 2 warnings in 1211.06s (0:20:11)). Answers the round-18 verdict; first seal. |
| external 19 (verdict) | 2026-09-25 | 2 | the proposed INV-7 scope addition is ACCEPTED (INV-7 establishes its observation-only claim against behaviour-changing census defects, excluding census code deliberately written to attack the measurement); the implementation RETURNED for two corrections (the round-18 subclass finding closed). Findin… |
| external 20 (SENT) | 2026-09-26 | — | SENT (round-20 package 661af7d620d5823a56213d1b01859fc29fdc42cc5168a0856e4a3200699747e7 @ pin e28a17399a621461bdc30d97366a2a0b9be2977f, CI 36203759765; 0042 v12.0; fresh-clone capture at the pin: 4099 passed, 11 skipped, 2 warnings in 1254.26s (0:20:54)). Answers the round-19 verdict; first seal. |
| external 20 (verdict) | 2026-09-26 | 1 | returned for one implementation correction (F2 closed; F1 remains). Findings: 0042-R20-1 — F1 remains: non-UTF-8 diagnostic output raises UnicodeDecodeError in derivation and verification, despite a valid response. Verdict banked verbatim at `0042-round20-verdict-verbatim.md`, file sha16 fbe2e4104d2… |
| external 21 (SENT) | 2026-09-26 | — | SENT (round-21 package 62d8ffae1671e0c44a2440ea0cc2e4c52f5b68527db85a2e346a96a6d8df37e7 @ pin d4d8dfdb6d6fa9aa88893a136801cfaedc706cc2, CI 36226496556; 0042 v12.1; fresh-clone capture at the pin: 4134 passed, 12 skipped, 2 warnings in 1228.84s (0:20:28)). Answers the round-20 verdict; first seal. |
| external 21 (verdict) | 2026-09-26 | 1 | returned for one implementation correction (the previous diagnostic-output defect fixed). Findings: 0042-R21-1 — The new source reader rejects valid Python files containing certain encoded header comments. Verdict banked verbatim at `0042-round21-verdict-verbatim.md`, file sha16 5363d02433163881, bo… |
| external 22 (SENT) | 2026-09-26 | — | SENT (round-22 package a188491a1ad8db5e640de8741a664b09ad045d7383aa73996a1f1a1d2916cf89 @ pin eb55a71cdb88183a2e216ddcf5fd187343ac0eae, CI 36248945549; 0042 v12.2; fresh-clone capture at the pin: 4148 passed, 12 skipped, 2 warnings in 1260.15s (0:21:00)). Answers the round-21 verdict; first seal. |
| external 22 (verdict) | 2026-09-26 | 1 | returned for one implementation correction (the previous header-comment cases fixed). Findings: 0042-R22-1 — A new regression rejects valid encoding declarations such as iso-latin-1 and utf-8-unix that round 21 accepted. Verdict banked verbatim at `0042-round22-verdict-verbatim.md`, file sha16 45034… |
| external 23 (SENT) | 2026-09-26 | — | SENT (round-23 package 462713e4a09c094ac36865e7a9e53b29169c43af926f92c9eefbf4a1fb657dbc @ pin d00cd868d455de175d8655f275f387f799cd7ebc, CI 36261826055; 0042 v12.3; fresh-clone capture at the pin: 4159 passed, 12 skipped, 2 warnings in 1335.46s (0:22:15)). Answers the round-22 verdict; first seal. |
| external 23 (verdict) | 2026-09-26 | 0 | 🏁 ACCEPTED — THE IMPLEMENTATION: 'The round-22 regression is fixed; no new findings.' Independent suite 4,136 passed, 35 explained skips, zero failures. Closes the implementation-review arc (rounds 6-23) on round 5's design acceptance, as amended at rounds 16 and 19. Verdict banked verbatim at `0042… |

**Per-finding closure ledger — PROCESS §4a.** **49 finding(s) for `0042`** — every number here is DERIVED from the rows below (external round 7, R7-1: the manifest claimed 26 while the ledgers held 31, and 0023 said 9/9 above a 10-row table); the total across the tracked specs is derived once, in `specs/STATUS.md`. Generated from `specs/closure_findings.py` and validated against `specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — extras, duplicates, wrong rounds and empty evidence all fail the build.

| finding | round | what it was | closed in | evidence (runnable) |
|---|---|---|---|---|
| **0042-R1-1** | external 1 | the rates and their measurement windows were undefined (§§1, 4B, 5; INV-3/4): the denominator argument was overstated | travelled to 0043 at the split (owner's ruling, 2026-09-18): A1's ledger form — per-(question, arm) rows, rates over RESOLVED rows with the denominator stated, the timeout as its own terminal row; 0043 v1 §4B/INV-3/INV-4 | `git show 1bc29178014016d040e8cdb1ee92d81420970244 -- specs/0043-refusal-harness.md # v1 A1 — the ledger form` |
| **0042-R1-2** | external 1 | the proposed examiner input violated blindness (§4B step 1; INV-6) | travelled to 0043: the examiner view restricted to (subject, relation, object, since) with the flip test as the blindness proof; 0043 v1 §4B step 1, INV-6 | `git show 1bc29178014016d040e8cdb1ee92d81420970244 -- specs/0043-refusal-harness.md # v1 A2 — the examiner view` |
| **0042-R1-3** | external 1 | no independent outcome judge and no question-level reference labels (§§3, 4B; INV-4/6) | travelled to 0043: the adjudication rubric with reference cases, later replaced by the interpretation stage (A3-ter/A3-quater); 0043 v1 §4B | `git show 1bc29178014016d040e8cdb1ee92d81420970244 -- specs/0043-refusal-harness.md # v1 A3 — the rubric` |
| **0042-R1-4** | external 1 | installed instrumentation was not separated from observed traffic (§4A-0/A; INV-1/2) | Part A-0 gained the three sets and Part A-1 the six-status state table (UNREACHED vs UNEXERCISED vs UNMEASURED; DISABLED as a status) — parsed from the spec by the evidence, not hand-listed | `$PY -m pytest tests/test_0042_evidence.py::test_a1_state_table_is_parsed_from_the_spec_and_the_code_conditions_match_it_one_to_one tests/test_0042_evidence.py::test_a1_every_tuple_maps_to_exactly_one_status_in_precedence_order` |
| **0042-R1-5** | external 1 | the counter lifecycle and the observation-only contract were incomplete (§§4A, 5, 7, 10; INV-2/7) | Part A-2: the counter lifecycle, the three-arm decision-trace diff over exactly (seq, site_id, decision) with its bound stated | `$PY -m pytest tests/test_0042_evidence.py::test_a2_three_arm_trace_diff_compares_only_the_named_fields_and_refuses_extra_ones` |
| **0042-R1-6** | external 1 | the baseline treatment was unspecified (§4B step 3; INV-5) | travelled to 0043: the baseline arm, replaced three times (merged prompt → examiner view → the CAPTURED model input under a stated transform, A6-ter), the history in 0043 §11 | `git show 1bc29178014016d040e8cdb1ee92d81420970244 -- specs/0043-refusal-harness.md # v1 A6 — the first baseline definition` |
| **0042-R2-1** | external 2 | the AST inventory could not support the completeness claim: candidate discovery, reviewed enforcement points and installed instrumentation were one undifferentiated set | Part A-0-bis: DISCOVERED (derived by the inventory: RAISE, RETURN_FALSE, RETURN_NONE, BOOL_RETURN, FILTER_RETURN), REVIEWED (recorded decisions), DECLARED; the three-sets check refused on the round-2 tree because no decisions existed; since tranche 6a every candidate carries a decision and the check still bites on an emptied review | `$PY -m pytest tests/test_0042_evidence.py::test_a0bis_the_three_sets_check_refuses_each_wrong_pair_and_passes_the_complete_fixture tests/test_0042_evidence.py::test_a0bis_on_the_real_tree_every_discovered_candidate_has_a_decision tests/test_0042_evidence.py::test_a4_discovery_finds_the_four_symbols_round_2_named_and_states_its_unit` |
| **0042-R2-2** | external 2 | the census schema and the comparison contract were inconsistent across prose, schema and tests (statuses 4 vs 5; invalid counts; the compared trace fields unnamed) | Part A-1 is the single authority: the state table parsed from the spec with the count cross-checked against the prose; the report gate refuses every named defect; Part A-2 names the compared fields | `$PY -m pytest tests/test_0042_evidence.py::test_a1_parser_refuses_a_missing_table_and_a_count_that_disagrees_with_the_prose tests/test_0042_evidence.py::test_a1_report_gate_refuses_every_named_defect_and_emits_the_undeclared_row` |
| **0042-R3-1** | external 3 | reviewed and declared does not establish installed: with every candidate reviewed, every point declared and no counters at all, the reconciliation passed | Part A-0-ter derived INSTALLED from a static scan checked by the import-time registry — itself found a proxy in round 4 and replaced by A-0-quater (the binding); see 0042-R4-1 | `git show 43c1c637cef4372dadcf315a23f06ae8e1c8100d -- specs/0042-exercised-guarantees.md # v6 Part A-0-ter` |
| **0042-R3-2** | external 3 | A5 bounded: disabling measurement allowed an undeclared reporter to pass | structural reconciliation runs BEFORE status and does not depend on `enabled`: an undeclared reporter under enabled == false is emitted DISABLED and refused | `$PY -m pytest tests/test_0042_evidence.py::test_a5_an_undeclared_reporter_is_refused_even_when_measurement_is_off` |
| **0042-R3-3** | external 3 | observation-only evidence: (seq, site_id, decision) supports branch-sequence equivalence only; replay inputs and execution conditions must be frozen and the bound stated | Part A-2 states the bound (branch-sequence equivalence under frozen inputs; results and state checked separately); the trace key refuses records carrying anything else | `$PY -m pytest tests/test_0042_evidence.py::test_a2_three_arm_trace_diff_compares_only_the_named_fields_and_refuses_extra_ones` |
| **0042-R4-1** | external 4 | registration does not establish working instrumentation: a declare_site call is a proxy for a counter bound to the decision — both fixture decisions executed, every counter stayed at zero, the report read UNREACHED; the deletion control deleted the declaration on a fixture with no counters | Part A-0-quater: the decision is expressed THROUGH the site; INSTALLED = the scan of the binding; the runtime assertion is the reviewer's own test; the controls with the naming defect fixed | `$PY -m pytest tests/test_0042_evidence.py::test_a0quater_the_reviewers_round4_test_executing_both_decisions_moves_both_counters_and_reads_exercised tests/test_0042_evidence.py::test_a0quater_strip_the_binding_keep_the_declaration_refuses_and_consult_without_fire_refuses tests/test_0042_evidence.py::test_a0quater_registered_but_unbound_is_refused_by_the_registry_check_as_registered_not_installed` |
| **0042-R5-1** | external 5 | the binding scan accumulated method uses across the whole module by variable name: consult() in one function and fire() in another read as bound; an already-positive counter must not establish that a later decision was measured | the binding is function-local and scope-aware (nested functions are their own scope; a shadowed name is not the site); the runtime assertion is over DELTAS around the particular decision; the split-function, nested and shadowed mutants refuse | `$PY -m pytest tests/test_0042_evidence.py::test_a0quater_round5_the_binding_is_function_local_and_scope_aware tests/test_0042_evidence.py::test_a0quater_the_reviewers_round4_test_executing_both_decisions_moves_both_counters_and_reads_exercised` |
| **0042-R4-2** | external 4 | advisory: consolidating the superseded passages would help prevent old installation wording from being mistaken for current requirements | acknowledged at v7 with §11 (superseded decisions out of the normative body) — and round 5 found the class still present, so the record shows the ask twice; closed at v8 (see 0042-R5-2) | `git show a9d3622d6252a19387b2ecb66a665f101825fb36 -- specs/0042-exercised-guarantees.md # v7 §11` |
| **0042-R5-2** | external 5 | superseded normative wording still readable as live requirements — the class the reviewer named in round 4 and again at acceptance ("finish removing superseded normative wording") | removed at v8: the diff moves the contiguous superseded blocks out of the normative body into §11 (the 'inspected subset' comparison; the A-0-ter INSTALLED definition); the history stays in §11 | `git show c6dd4078b877088684b381add72fe08feb1354b4 -- specs/0042-exercised-guarantees.md # v8 — the superseded blocks moved to §11` |
| **0042-R6-1** | external 6 | a failing trace recorder, decline classifier or single consult increment was not contained: it raised, read UNEXERCISED with errors=0, or produced fired>consulted that invalidated the whole report (INV-2/INV-7) | round-7 fix: census.Site contains recorder/classifier failures, counts them in errors, records the exception type per id; the row reads UNMEASURED and census_table.insufficiency refuses it as evidence | `$PY -m pytest tests/test_0042_census.py::test_r6_1_a_failed_trace_recorder_is_contained_counted_and_the_decision_is_returned_as_made tests/test_0042_census.py::test_r6_1_a_failed_decline_classifier_reads_unmeasured_not_unexercised tests/test_0042_census.py::test_r6_1_a_failed_consult_increment_reads_unmeasured_the_report_stays_valid_and_is_insufficient` |
| **0042-R6-2** | external 6 | scoped_assertable's shared bracket counted later checks as consulted after an early return, and the four hot Edge predicates left consultation at zero when evaluation raised | round-7 fix: every sequential site consulted immediately before its own condition (per-check brackets / consult statements); hot Edge predicates consult before evaluating when enabled and return through one statement | `$PY -m pytest tests/test_0042_sites.py::test_r6_2a_a_consult_means_the_sites_own_condition_was_reached tests/test_0042_sites.py::test_a_raising_predicate_raises_identically_on_both_paths_and_is_consulted_before_it_is_evaluated` |
| **0042-R6-3** | external 6 | a declared site whose loaded module never registered was reported UNREACHED with zero counts and validate_report accepted it; the reconciliation took its set from source scanning, not the live registry | round 7: snapshot carries what registered; validate_report refuses a loaded-but-unregistered id and names out-of-reach ones — but only when site_modules was supplied; R7-1 made the incomplete validation explicit (round 8) | `$PY -m pytest tests/test_0042_census.py::test_r6_3_a_declared_id_whose_module_is_loaded_but_never_registered_is_refused_and_an_unloaded_one_is_named tests/test_0042_evidence.py::test_a0quater_round6_the_live_registry_reconciles_against_the_scan_and_nothing_is_out_of_reach tests/test_0042_evidence.py::test_r7_f1_the_reviewers_case_a_two_argument_validation_no_longer_reads_clean` |
| **0042-R6-4** | external 6 | the binding scan checked local shadowing only and did not resolve enclosing scopes, so a closure over an enclosing parameter named like a site read as bound | round 7: names resolved through enclosing function scopes (class bodies not scopes); the binding-form class continued as R7-2 (walrus/match, fixed round 8 by the symtable resolver) and R8-1 (nested imports, fixed round 9) | `$PY -m pytest tests/test_0042_evidence.py::test_a0quater_round6_a_site_name_resolves_through_enclosing_function_scopes_and_class_bodies_do_not_shadow tests/test_0042_evidence.py::test_r7_f2_the_reviewers_two_rebinding_forms_no_longer_read_as_bound tests/test_0042_scope_resolution.py::test_every_module_level_binding_form_is_refused_and_no_shadow_is` |
| **0042-R6-5** | external 6 | inv7_harness compared encoded bytes without their symbol/label dictionaries, merged distinct sites sharing a return value, and its success status did not require arm exits or cross-checks | round 7: observer records (symbol, exit-statement ordinal, label), harness decodes through each arm's dictionaries and compares canonical records, final_status requires every arm exit and cross-check; gaps continued as R7-3 (round 8) and R8-2 (round 9) | `$PY -m pytest tests/test_0042_inv7.py::test_r6_5_i_identical_bytes_with_different_dictionaries_are_different_traces tests/test_0042_inv7.py::test_r6_5_iii_the_harness_exit_requires_every_arm_and_every_cross_check tests/test_0042_inv7.py::test_r6_5_ii_every_declared_site_has_its_own_exit_statement_so_exit_keyed_records_separate_them` |
| **0042-R6-6** | external 6 | the uninstrumenting transform removed an unrelated .fire call, accepted an unbound attribute chain and deleted a product side effect inside an enabled block | round 7: transform rewrites only names bound by declare_site and recognised shapes, refuses the rest by line, writes twin_manifest.json that verify() re-derives; the preservation class continued through R7-4, R8-3, R9-1, R10-1/2 (closed round 11) | `$PY -m pytest tests/test_0042_inv7.py::test_r6_6_the_twin_transform_refuses_what_it_has_not_established_is_instrumentation_and_keeps_exits tests/test_0042_inv7.py::test_r7_f4_the_verifier_establishes_preservation` |
| **0042-R6-7** | external 6 | the surface-driven site assertions checked only fired>=1 and consulted>=fired, so doubling every increment passed | round 7: surface-driven sites assert exact deltas derived from the product's control flow (EXACT_SURFACE/EXACT_DECLINE); a doubled-increment control fails every one | `$PY -m pytest tests/test_0042_sites.py::test_the_surface_driven_sites_move_by_exactly_their_derived_counts tests/test_0042_sites.py::test_r6_7_a_doubled_increment_fails_every_exact_delta` |
| **0042-R7-1** | external 7 | registry reconciliation ran only when the caller supplied site_modules, so an ordinary two-argument validate_report accepted a missing registration as UNREACHED | round 8: absence of reconciliation evidence is reported in the refusal list ([] means validated completely); what a report cannot speak for moved to insufficiency, per id; the same optional-argument shape swept in insufficiency | `$PY -m pytest tests/test_0042_evidence.py::test_r7_f1_the_reviewers_case_a_two_argument_validation_no_longer_reads_clean tests/test_0042_census.py::test_r7_no_check_returns_clean_when_an_optional_argument_narrowed_its_scope` |
| **0042-R7-2** | external 7 | installed_sites did not recognise every local binding form; walrus and match-capture rebinding of a site name read bound=True | round 8: new scope_resolution.py over symtable shared by scan and transform (binding grammar by construction); nested-import gap continued as R8-1 (round 9) | `$PY -m pytest tests/test_0042_evidence.py::test_r7_f2_the_reviewers_two_rebinding_forms_no_longer_read_as_bound tests/test_0042_scope_resolution.py::test_the_resolver_answers_every_binding_form tests/test_0042_scope_resolution.py::test_the_matrix_covers_both_answers_and_the_reviewers_two_forms tests/test_0042_scope_resolution.py::test_a_module_level_rebinding_of_a_site_is_refused_including_a_walrus_in_a_comprehension` |
| **0042-R7-3** | external 7 | inv7_harness ignored failed control runs, used an exits-per-function count that two sites sharing a return could satisfy, and serialised verdict.json before final_status added the gates | round 8: every arm and control's pytest exit gated; site-to-exit association replaces the count; status computed before verdict serialisation; missing-summary gap continued as R8-2 (round 9) | `$PY -m pytest tests/test_0042_inv7.py::test_r7_f3a_a_control_run_that_failed_fails_the_exit tests/test_0042_inv7.py::test_r7_f3c_the_serialised_verdict_carries_the_gates_both_readmes_promise tests/test_0042_inv7.py::test_r6_5_ii_every_declared_site_has_its_own_exit_statement_so_exit_keyed_records_separate_them tests/test_0042_inv7.py::test_r6_5_ii_control_the_reviewers_fixture_collides_and_a_count_cannot_see_it` |
| **0042-R7-4** | external 7 | verify() compared selected statement kinds only, did not check manifest hashes or the file set, was called without its source; the transform rewrote a parameter shadowing a site name | round 8: verify requires source, compares the file set both ways, re-derives and diffs the AST, checks manifest hashes; transform resolves names via the shared resolver; alias-shadow gap continued as R8-3 | `$PY -m pytest tests/test_0042_inv7.py::test_r7_f4_the_verifier_establishes_preservation tests/test_0042_inv7.py::test_r7_f4a_a_parameter_shadowing_a_site_name_keeps_its_own_call` |
| **0042-R8-1** | external 8 | scope_resolution's nested-scope check used is_global() and is_assigned(); a nested import under 'global S' is is_imported not is_assigned, so it replaced the site undetected | round 9: rule C reads STORE_GLOBAL/DELETE_GLOBAL from nested code objects (_nested_global_bindings, refuse_site_rebindings); the superseded predicate pair kept as negative control | `$PY -m pytest tests/test_0042_scope_resolution.py::test_every_module_level_binding_form_is_refused_and_no_shadow_is tests/test_0042_scope_resolution.py::test_the_superseded_predicate_pair_misses_exactly_the_nested_imports tests/test_0042_scope_resolution.py::test_every_refused_row_names_the_rule_that_caught_it` |
| **0042-R8-2** | external 8 | compare() substituted the main arm's summary for an absent control summary while final_status checked only present summaries, so a missing summary dropped the control's exit check | round 9: one derivation of the control set; a control directory without its own summary is named and fails the exit, never substituted | `$PY -m pytest tests/test_0042_inv7.py::test_r8_f2_a_control_without_its_own_summary_is_refused_not_substituted tests/test_0042_inv7.py::test_r8_f2_the_fix_changes_nothing_for_a_COMPLETE_capture` |
| **0042-R8-3** | external 8 | visit_If recognised _census.enabled() by alias spelling alone, so a parameter or closure named _census had its branch rewritten while verify() stayed clean | round 9: _is_census_alias asks the shared scope resolver; behaviour regression executes source and twin; module-scope-vs-identity gap continued as R9-1 (round 10) | `$PY -m pytest tests/test_0042_inv7.py::test_r8_f3_an_ordinary_shadowed_census_alias_keeps_its_behaviour tests/test_0042_inv7.py::test_r8_f3_the_census_import_is_restored_for_a_derived_alias` |
| **0042-R9-1** | external 9 | _is_census_alias established module scope but not that the binding still denoted the census; a rebinding after import and the {'_census','census'} fallback both rewrote ordinary branches, verify clean | round 10: declared_names checks import module and level; guessed-alias fallback removed; alias must be bound exactly once at module level (module_binding_count); identity asserted at runtime. Nested rebinding continued as R10-1 | `$PY -m pytest tests/test_0042_inv7.py::test_r9_a_census_alias_whose_binding_was_replaced_is_refused_not_rewritten tests/test_0042_inv7.py::test_r9_a_module_with_no_census_import_keeps_its_own_behaviour tests/test_0042_inv7.py::test_r9_the_alias_identity_is_established_at_runtime_because_it_cannot_be_established_statically` |
| **0042-R10-1** | external 10 | the alias check read only rule A (module code object); a nested global assignment, nested import or genexp walrus replaced _census without moving that count, and the twin diverged with verify() clean | round 11: the alias asks both rule A and rule C (_nested_global_bindings made public); every census decision routed through named predicates, enforced by an AST-derived gate | `$PY -m pytest tests/test_0042_inv7.py::test_r11_the_four_census_identity_findings tests/test_0042_inv7.py::test_every_census_decision_routes_through_one_predicate` |
| **0042-R10-2** | external 10 | import removal stripped any name spelled census from any import (e.g. from totally_unrelated import census), so the twin raised NameError while verify() passed | round 11: removal routed through the same predicate as recognition (module and level both checked); multi-name census imports stripped per name | `$PY -m pytest tests/test_0042_inv7.py::test_r11_the_four_census_identity_findings tests/test_0042_inv7.py::test_every_census_decision_routes_through_one_predicate` |
| **0042-R11-1** | external 11 | a census import was dropped whole, losing live bindings of mixed/surface imports; verify() re-derived with the same transform and read clean | round 12: per-name removal with restoration of every removed binding; verify() gained checks of a different kind (compile(), lost_bindings; round 13 added lost_cross_module_references) | `$PY -m pytest tests/test_0042_inv7.py::test_r12_f1_every_census_import_shape_keeps_its_bindings_or_refuses tests/test_0042_inv7.py::test_r12_verify_catches_a_transform_defect_it_did_not_write` |
| **0042-R11-2** | external 11 | the round-11 enumeration gate waived any unit calling a predicate, so an independent census decision inside such a unit passed | round 12: waiver deleted; banned vocabulary derived from the predicates' own string constants, checked per unit | `$PY -m pytest tests/test_0042_inv7.py::test_r12_f2_the_gate_refuses_a_second_reading_wherever_it_stands tests/test_0042_inv7.py::test_every_census_decision_routes_through_one_predicate` |
| **0042-R12-1** | external 12 | the comprehension handler walked element/key before generators (S2c-1, disclosed open), handing same-line scopes each other's symbol tables; a live census read stayed in the twin with verify clean and 0 unresolved | round 13: CPython's comprehension order; a join check refusing any pairing decided by order alone; the pairing oracle as a standing gate; a census read the twin keeps is reported | `$PY -m pytest tests/test_0042_scope_resolution.py::test_r13_f1_every_scope_inside_a_comprehension_gets_its_own_table tests/test_0042_inv7.py::test_r13_f1_a_census_read_the_twin_keeps_is_reported_not_silent tests/test_0042_scope_resolution.py::test_r13_the_join_check_turns_the_old_orders_silent_answers_into_refusals tests/test_0042_scope_resolution.py::test_r13_the_pairing_oracle_finds_no_silent_answer_and_its_control_does` |
| **0042-R12-2** | external 12 | the twin removed site declarations, so a sibling module importing a site failed with ImportError while verify() passed | round 13: derive refused a site another module reaches plus a cross-module differential in verify; class reopened as R13-1 and closed by construction in round 14 (declarations kept, nothing removed) | `$PY -m pytest tests/test_0042_inv7.py::test_r14_f1_no_route_to_a_declared_site_breaks_the_twin tests/test_0042_inv7.py::test_r12_verify_catches_a_transform_defect_it_did_not_write tests/test_0042_inv7.py::test_r13_f2_a_sibling_using_only_ordinary_names_is_neither_refused_nor_reported` |
| **0042-R13-1** | external 13 | five more routes to a removed declaration (pkgutil.resolve_name, runpy.run_module, importlib.util loading, __globals__, inspect.getmodule) derived a broken twin with verify() clean | round 14: nothing removed — declarations and census imports kept verbatim, each bound to an inert stand-in (later: the reference census, rounds 15-16); every route derives, verifies clean and runs as the source (36 cells) | `$PY -m pytest tests/test_0042_inv7.py::test_r14_f1_no_route_to_a_declared_site_breaks_the_twin` |
| **0042-R13-2** | external 13 | the scan-to-runtime binding check collected a property's getter only and matched functions by name, so a scanned setter binding a site could differ from the code that ran | round 14: every scanned binding body must be found among the running module's code objects via its outermost def and equal the compiled source; walk covers nested classes, getter/setter/deleter, cached_property, static/class methods | `$PY -m pytest tests/test_0042_evidence.py::test_r14_f2_a_binding_body_that_did_not_run_is_refused tests/test_0042_evidence.py::test_r13_the_scan_describes_the_program_that_ran_and_refuses_otherwise` |
| **0042-R14-1** | external 14 | the twin's inert stand-in class overrode object methods to count uses, so decisions asking the class (e.g. type(S).__hash__ is object.__hash__) read True in source, False in twin, verify clean, 0 uses | round 15: stand-in removed; twin carries census.py verbatim so its Site class is the source's (round 16 then pinned it to the accepted commit T's census) | `$PY -m pytest tests/test_0042_inv7.py::test_r15_every_question_about_a_site_answers_alike_in_source_and_twin tests/test_0042_inv7.py::test_r16_the_twin_census_is_the_reference_census_and_verify_refuses_any_other` |
| **0042-R15-1** | external 15 | the reference arm ran the census under test, so a declaration-time census defect changed decisions identically in all four arms and INV-7's trace diff could not see it | round 16: reference arm's census is the census.py of an accepted commit T pinned by digest (verify refuses any other); HEAD's Site compared to T's, drift refused; INV-7 amendment proposed and accepted in round 16 | `$PY -m pytest tests/test_0042_inv7.py::test_r16_the_reference_census_separates_a_declaration_time_defect tests/test_0042_inv7.py::test_r16_the_mutant_changes_a_decision_at_all tests/test_0042_inv7.py::test_r16_the_twin_census_is_the_reference_census_and_verify_refuses_any_other tests/test_0042_inv7.py::test_r16_a_drifted_site_is_refused_and_t_must_advance` |
| **0042-R15-2** | external 15 | run_arm passed the inherited relative PYTHONPATH unchanged to child processes whose working directory differed, so three child-process tests failed on the reviewer's extracted tree | round 16: run_arm makes every inherited PYTHONPATH entry absolute; stage smoke run as the reviewer ran it with a control reproducing the three failures at the round-15 pin | `$PY -m pytest tests/test_0042_inv7.py::test_r16_run_arm_hands_the_child_an_absolute_import_path` |
| **0042-R16-1** | external 16 | the Site drift check read the class body as a member map, so a reordering and a shadowed duplicate definition read no drift while source and reference decisions differed | round 17: route A compares the whole ClassDef ordered with duplicates (header by field); route B compares the realized class attribute by attribute incl. metaclass data descriptors; drift is the union | `$PY -m pytest tests/test_0042_inv7.py::test_r17_site_drift_reads_the_definition_and_the_realized_class tests/test_0042_inv7.py::test_r17_formatting_is_not_drift_on_either_route` |
| **0042-R17-1** | external 17 | route B's function normaliser ignored functions' writable __name__/__qualname__/__module__, so a post-class metadata change read no drift while a decision testing it differed between source and reference | round 18: one recursive rule over every data descriptor of every object (read-only included, fields derived per interpreter); __flags__ bit 19 masked; import-time realized-Site digest gated at runtime | `$PY -m pytest tests/test_0042_inv7.py::test_r18_function_metadata_is_compared_by_one_recursive_rule tests/test_0042_inv7.py::test_r18_route_b_sees_constants_closures_and_method_attributes tests/test_0042_inv7.py::test_r18_the_function_fields_compared_are_derived_per_interpreter` |
| **0042-R18-1** | external 18 | the describer read a subclass named like a builtin (e.g. tuple) as that builtin, so a spoofed Site.__slots__ passed every drift check while 'site_id' in type(S).__slots__ differed | round 19: a type read by name only if immutable; a mutable subclass described in full through its base's methods; each census described in a fresh python -I -B child with builtins restored | `$PY -m pytest tests/test_0042_inv7.py::test_r19_a_subclass_is_never_read_as_the_builtin_it_names tests/test_0042_inv7.py::test_r19_an_equal_real_builtin_is_not_drift tests/test_0042_inv7.py::test_r19_the_runtime_gate_reads_the_witness_and_the_spoof_as_different` |
| **0042-R19-1** | external 19 | the isolated child wrote its JSON description to the stdout the census shares, so ordinary census output made derive() and verify() raise a bare JSONDecodeError and lose real drift diagnostics | round 20: child writes its response to a file it owns and exits via os._exit(0); every failure named (SiteUndescribed, never drift). Non-UTF-8 output remained as R20-1, fixed round 21 | `$PY -m pytest tests/test_0042_inv7.py::test_r20_census_output_never_reaches_the_isolated_child_s_response tests/test_0042_inv7.py::test_r20_an_undescribable_census_is_never_reported_as_drift tests/test_0042_inv7.py::test_r20_each_superseded_transport_fails_its_cell` |
| **0042-R19-2** | external 19 | the N4 comprehension signature ignored the compiler-added __class__ on a super load, merging an inner __class__ target and raising UnresolvableScope on valid code | round 20: compiler-added names derived by two routes (symtable.c and a stdlib symtable census); all comparisons in symtable's (mangled) spelling; 576-program generated corpus matches symtable 3.10-3.13 | `$PY -m pytest tests/test_0042_scope_resolution.py::test_r20_f2_compiler_names_and_mangling_match_symtable_and_resolve tests/test_0042_scope_resolution.py::test_r20_f2_the_generated_corpus_equals_symtable_and_resolves tests/test_0042_inv7.py::test_r20_a_valid_helper_beside_a_measured_decision_derives tests/test_0042_scope_resolution.py::test_r20_f2_each_superseded_rule_fails_the_corpus` |
| **0042-R20-1** | external 20 | the parent captured census stdout/stderr as text and decoded strictly, so non-UTF-8 census output raised UnicodeDecodeError in derive() and verify() despite a valid response | round 21: bytes channel, output decoded only to name a failure; UTF-8 stated at every text boundary; sources read in their declared encoding (which introduced R21-1) | `$PY -m pytest tests/test_0042_inv7.py::test_r21_census_bytes_never_break_the_isolated_boundary tests/test_0042_inv7.py::test_r21_decoding_the_census_output_on_success_fails_the_byte_cells tests/test_0042_inv7.py::test_r21_derive_and_verify_hold_under_a_non_utf8_locale` |
| **0042-R21-1** | external 21 | round 21's source reader (tokenize.detect_encoding) decoded header lines as UTF-8 before finding the cookie, refusing valid Python with latin-1/cp1252/GB18030 header comments | round 22: cookie found at the byte level per PEP 263; every reading checked against the interpreter's own parse (AST equality); 560-header generated corpus with the interpreter as oracle | `$PY -m pytest tests/test_0042_inv7.py::test_r22_the_source_reader_agrees_with_the_interpreter_over_the_header_corpus tests/test_0042_inv7.py::test_r22_a_header_the_interpreter_accepts_derives_and_verifies tests/test_0042_inv7.py::test_r22_the_interpreter_guard_fires_on_a_wrong_reading` |
| **0042-R22-1** | external 22 | round 22's byte-level cookie rule dropped the tokenizer's name normalisation, refusing encoding names the interpreter accepts (iso-latin-1, utf-8-unix) | round 23: declared name normalised as the interpreter does (_normal_name); name corpus derived from codecs and the folded families, crossed with BOM; a refusal after the interpreter accepts is named a disagreement | `$PY -m pytest tests/test_0042_inv7.py::test_r23_the_source_reader_agrees_with_the_interpreter_over_every_cookie_name tests/test_0042_inv7.py::test_r23_the_normaliser_is_the_interpreters_over_the_name_domain tests/test_0042_inv7.py::test_r23_the_controls_are_sets_round_22_fails_exactly_the_folded_names_round_21_passes_them tests/test_0042_inv7.py::test_r23_a_refusal_after_the_interpreter_accepts_is_named_a_disagreement` |

<!-- /GENERATED:review-closure -->
