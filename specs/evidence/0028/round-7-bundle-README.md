<!-- TERMINAL RECORD — the round-7 review bundle README of spec 0028, byte-copied
UNMODIFIED from the ACCEPTED package (sha256 846db40822ae68068e92d459e76ca40983b5920d38181ba9ca332a23752b2f1e
@ 6680150e510f9c04f9439793671565e9e2a0e516, CI 34154534452) on 2026-09-07, the day the
reviewer accepted 0028 v13 and froze its invariant surface (nineteen names — every §6 row).
It is the one carrier where the round-6 dispositions and the consolidated errors ledger live
together with the path from rounds 1–6 (each earlier README rides in its successor's
prior-rounds/); the version cells carry lineage, not the reviewer's dispositions or the
process's disclosed failures. The package remains the archive; this copy is the record.
Below this comment the bytes equal the packaged README — verifiable forever against the
archived package: strip the lines above the first '# ' heading and compare. -->

# 0028 as-of / point-in-time query (feature version v2, valid-time only) — round-7 external review bundle

Assembled 2026-09-07 by dev. Seventh external round for spec 0028. Round 6
(package `415d906c9102d9b1c5531b5f4da05f44c671f381e220f0c4e4987eb8e8e3cc1d`
@ `eddcb2337d07b47c9cdfcb6cbb4834b5acf185f5`, CI 34149633519) returned for
amendment the same day: "the round-5 behavioral findings are correctly resolved,
and all tests pass. Two live contract carriers remain contradictory" — two
blocking findings, both in prose that a passing test sat beside, and two
corrections. The verdict is in `prior-rounds/` verbatim (banked by dev, the
receiving seat; the reviewer's words are the body after the marker, digest
`bd2c56b42f753ce9`). This package carries **draft revision v13**; no new
artifact was requested and none is added — the reviewer's words: "the existing
model and updated window test expose both remaining contradictions."

**Canonical artifact:** `specs/0028-as-of-query.md` at the pinned commit (see
`PIN.txt` — commit, CI run id, and the suite line as printed; repo
`github.com/veracium-ai/Veracium`, public). The copy here
(`0028-as-of-query-SPEC-v13.md`) is byte-identical to `tree/specs/` at seal;
on any doubt the repo wins.

## Disposition map — every round-6 item

| # | the finding (reviewer's words, abridged) | disposition | where |
|---|---|---|---|
| R6-1 | §4b's normative outcome definition still says `INDETERMINATE` "is never silent: every instance is disclosed with its cause", contradicting cause-free `SUCCESSOR_UNAVAILABLE`; the checklist was corrected at v12, the definition was not | §4b carries the same two classes the checklist does: an indeterminate from a condition observable within the caller's view (branching, a cycle, an unclassifiable reason) carries and discloses its cause; `SUCCESSOR_UNAVAILABLE` carries no principal-facing cause, by design, because a distinguishable cause there is the existence signal. Both failure modes are named in the text: collapsing *cannot tell* into *nothing*, and disclosing *why* across a scope boundary. The class, in the version cell: we fixed the summary and left the definition it summarises — R5-3's fix had the shape of its own finding | spec §4b; the checklist (unchanged from v12) |
| R6-2 | §4b-o, §5 and §7 describe the commit-time lock failure as SQLite's bare `database is locked` "surfacing unwrapped"; the sealed tree carries the 0029 change that wraps it, and the window test asserts the wrapped form | all three live carriers now state the wrapped refusal — an outer `OperationalError` naming the COMMIT site and `V-LOCK-REFUSAL-FORM`, SQLite's message retained as the cause — the same form as at BEGIN; the former behaviour is kept where it is history and marked as such. The pre-send miss is dev's and the version cell records it in dev's words (see the errors ledger) | spec §4b-o, §5, §7; `tree/tests/test_0028_window_transcript.py` (unchanged since round 6 — it already asserted the wrapped form) |
| corr. | §9 carried a malformed duplicated phrase ("over **the store states `EXPECTED` names … NO CARRIER STATES ONE** store states") | the round-5 "no count" replacement had fused with its neighbour's tail; the sentence reads once | spec §9 |
| corr. | the model's introduction calls itself "the design v11 specifies" while its queried-edge behaviour is the v12 amendment | "the v11 design as amended by v12" — two docstring sites (the module's and the accessor's) | `tree/specs/evidence/0028/check_successor_lookup.py` |

Round-5 items, per the verdict: R5-1 resolved, R5-2 resolved, R5-3 partially —
its remaining half is R6-1 above — and the accounting corrections substantively
resolved. Nothing from round 5 is reopened here.

## What changed in the tree between the round-6 pin and this one

Besides the spec: three lines in the successor-lookup model — the two docstring
sites of the correction above and one registry comment, so that a phrase count of
"v11 specifies" over the file is zero rather than a corrected sentence quoting the
phrase it corrects (no behaviour; the model's run is unchanged) — and
`specs/withdrawn_phrases.py` gains the
register's entries for this arc — the window-refusal wording, "except the
current-truth pointer", the old invariant name, "every instance is disclosed
with its cause" (R6-1's sentence), the bare/unwrapped lock wording (R6-2's), and
the state-count pattern from round 5. The register is what makes the next fold's
sweep mechanical: `specs/lint_withdrawn.py` runs in the suite over every spec and
test file, exempting a paragraph only when it carries the literal word
WITHDRAWN or OBSOLETE. Each paragraph in v13 that quotes one of those phrases as
history now carries the word — the marker is what lets the register and the
history coexist, and it belongs in the same edit as the retirement. No other
tracked file changed; `PIN.txt` states the product-change line from the diff.

## The evidence this package offers, each runnable offline from the archive's own bytes

| artifact | its executable check |
|---|---|
| the generated §4b table | `tests/test_0028_reason_resolution_table.py` |
| the absence proof over the shipped as-of code | `tests/test_0028_asof_absence.py` |
| the window transcript, reproduced by the reviewer in round 4 | `tests/test_0028_window_transcript.py` (asserting the wrapped commit-time refusal — the assertion §4b-o/§5/§7 now agree with) |
| the successor-lookup model | `tests/test_0028_successor_lookup.py` |

Dev's seal receipt runs all four from the extracted archive's bytes in a
throwaway; the count that run printed is the one stated in the seal announcement
and the coordination record. The two-seat seal script's ASSERT-10 runs the same
four files, set explicitly, and names them in its line. New this round: the
withdrawn-phrase lint is run over the sealed tree as a receipt WITH the count of
entries registered for this spec printed beside it — a zero-entry spec passes
that lint vacuously, and 0028 had zero entries through six rounds.

## Where the authors ask you to attack (spec §9, carried verbatim from v13)

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

## Sentences this round produced, offered as the frame for reading it

- A fix to a summary is not a fix to the definition it summarises (R6-1: the checklist was right, §4b was not).
- A package can carry both halves of a contradiction and pass every check, because no check compares prose to test (R6-2: the sealed test asserted wrapped; the sealed prose asserted bare).
- A behaviour change is described by other specs' prose too; the carrier sweep crosses specs (R6-2's cause).
- The edit that retires a sentence must quote it, so the register would flag the record of the retirement — the marker belongs in the same edit, every time.
- A sweep's false positives are the half that protects correct text: seven `bare`s, three defects, four homonyms a replace-all would have broken.

## Errors ledger

- **A first assembly of this round was DISCARDED before announcement** (dev's; sha256 `ce1bc53954e1c6a15c4e8b735e4ec2b24dbbdeefb268fce77620b0feba5fe283`, never in the outbox, disclosed in `PIN.txt` and `collected/`): this round is the first on the line where the seal check's stale sweep runs over a real identifier — the previous round's spec-copy filename — and dev's own leg FAILED it, because this README's errors ledger had written that filename out as a literal while explaining the rule. The sweep excludes only `tree/` and `prior-rounds/`, so the README is in scope, and a mention of a stale identifier is indistinguishable from a use to a sweep that has no marker convention. The sentence below now describes the identifier without spelling it; the check did exactly what it exists to do, on the seat that wrote the rule, in the carrier that explained it.
- **R6-2's cause is dev's** (stated in the version cell in dev's words): folding 0029 v11, dev swept 0029's text, `sqlite.py` and the tests — including 0028's window test, which it updated to the wrapped form — and never swept 0028's prose describing the store's behaviour; "a fix to a shared contract lands in every implementation" was read as code. The change landed inside 0028's own pin range, so the round-6 package carried the new test and the old prose together.
- **R6-1 is the round-5 fix's own carrier miss** (both seats'): the checklist was corrected and the §4b definition it summarises was not; the class is the one this arc keeps producing in both directions — a bound lost in a summary, a summary fixed without its definition.
- **The §9 sentence that fused** (research's): a scripted replacement of the "no count" wording merged with the following sentence's tail; the reviewer found it, not either seat's re-read. Second occurrence of the span class for this seat.
- **The register was empty for this arc** (both seats'): six rounds of withdrawals swept by hand and none registered, so the "withdrawn phrases at zero" receipt at every seal passed over an empty set. Found writing round 6's receipt; both seats' first proposed fixes were wrong in the same way — research proposed a strikethrough convention the lint already had as a marker word; dev's first receipt was the vacuous one. Fixed as described above; the receipt now prints the entry count.
- **A first candidate for the stale list would have failed a correct package** (both seats'): both proposed passing round 6's live identifiers as STALE; the seal script's own comment says a cited predecessor in STALE fails a correct package. The stale identifier for this line is now the previous round's spec-copy filename (the v12 copy's name, for this package) — derivable, guaranteed absent outside `prior-rounds/` and `tree/`, and it encodes this spec's recurrent defect. The seal legs' ASSERT-8 runs over one identifier this round for the first time in the line, and its first run refused this round's first assembly (the entry above).
- **The candidate needed two respins before adoption** (research's, caught by dev's gates before any copy): five paragraphs quoting registered phrases lacked the marker word (one of them this fold's own R6-1 note — the retirement quoting the sentence it retires); and §9 briefed round 6, the returned round, for the third time in three folds. Both are stated here so they read as disclosed rather than found.
- **The capture script carried a "product change: none" sentence from an earlier round** (dev's, caught before it reached round 6's carriers): now a required parameter derived from the diff at each pin.

## Contents

- `0028-as-of-query-SPEC-v13.md` — the spec, byte-identical to `tree/specs/`
- `PIN.txt` — commit, CI run id, suite line, every predecessor by identifier, the protocol
- `collected/COLLECTED.txt`, `collected/suite-run-raw.txt` — the fresh-clone capture at the pin, profile `[dev,mcp]`, raw transcript from the same run
- `prior-rounds/` — the round-6 README and verdict, the round-5, round-4, round-3 and supplemental verdicts (the sealed forms), the reproduced transcript log
- `artifacts/` — the principal-differential test design (research), byte-for-byte
- `tree/` — `git archive` at the pin (tracked files only, asserted both directions)
- `SHA256SUMS` — every file above, excluding itself
