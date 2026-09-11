<!--
specs/0039 — THE TERMINAL RECORD of the implementation review (rounds 5–9), preserved at
acceptance. The body below the marker line is the round-9 bundle README BYTE-COPIED from
the accepted package's own verified bytes:
  0039-round9-review-package.tar.gz sha256 1ac58958259d582f2ce6ff248dcfe2669e50cc06170cbf42b4c7f5385cd53944
  pin d476b3c4880e0516264ec41b4ea2925cde77bc13   CI 34609837460   both legs 56/0/2
  verdict ACCEPT (2026-09-11), banked verbatim in the outbox, body sha16 0e1b45a95e603c13
It is the one carrier holding every disposition and every errors ledger of the implementation
review, kept UNMODIFIED: `tests/test_0039_answer_shapes.py`'s sibling precedent is the round-4
record; `cmp` at preservation proved the body == the packaged bytes. Read it as what the
reviewer read; do not edit it. Everything after the next line is the record.
-->
# 0039 degradation visibility — round-9 bundle: the carrier rule as a criterion, and a census that derives its own scope

Assembled 2026-09-11 by dev. Round 8 (package `66a51c35…`, pin `d05b0bf`, 0039 v18 + 0025
v18) closed R7-2 and returned for one blocking finding: the single-carrier rule was neither
true — live sites outside §2e still stated the value — nor fully checked — the test verified
eight hand-chosen anchors and never that they were the complete set, so the verification's
asserted domain was narrower than the document, the round-7 problem repeated. The verdict
rides in `prior-rounds/` verbatim, body digest `52f6bf8450c16f04`, matched by two
computations over one stated rule. No product code moved; the reviewer found no product-code
defect.

Both specs ride here as top-level copies: `0039-degradation-visibility-SPEC-v19.md` and
`0025-relation-vocabulary-enforcement-SPEC-v18.md`, each byte-identical to `tree/specs/`
at seal.

**Canonical artifact:** the two specs at the pinned commit — see `PIN.txt` for the commit,
the CI run id and the suite line as printed; repo `github.com/veracium-ai/Veracium`, public.
On any doubt the repo wins.

**What the lineage means.** Eight verdicts ride in `prior-rounds/`: four from the 0039 spec
arc, which closed at ACCEPT, and four on its implementation. Two assemblies were discarded
across rounds 5 and 6, both by the authors before dispatch, both disclosed in `PIN.txt`. This
round has one assembly.

## The class, and the fact that it was found inside the fix for itself

Round 7's checker was "closed" by a hand-listed set of anchors. "Closed" and "enumerated by
hand" are not the same property: a hand list is complete until the next section lands, and
reads as complete after it. The second seat proposed that checker and named the conflation in
its own proposal. And the first seat's census for this round — the mechanism meant to replace
the hand list — under-counted on its first run: it excluded any LINE carrying a history
marker rather than stripping the marked SPAN, which removed exactly the sites where a live
cell sits beside a marked quote, and those were the three sites the reviewer cited. A checker
whose scope was narrower than the document, inside the census built to fix a checker whose
scope was narrower than the document.

## Disposition of round 8

| the reviewer's requirement | what changed | where it is bound |
|---|---|---|
| Either make every statement outside §2e a value-free pointer, or narrow the rule and enumerate justified exceptions | **Narrowed, as a CRITERION rather than a list of exceptions.** §2e's carrier rule now reads: a site may carry the value if and only if the value is what the site ASSERTS. Three forms assert it — §2e's statement (the contract), a §6 invariant row (a property; an invariant that says "see §2e" asserts nothing and cannot be bound, which is why the first option is refused as impossible rather than half-done), and a row of the §2c matrices (an outcome per shape). §1's behaviour table is NOT a fourth form: it is what was measured at v8, dated, and a dated statement cannot become false whatever the surface does — history; its one moved row points, and the census refuses §1 rather than admitting it by form, so an undated restatement there would be found. Every other site is a discussion and points. The allowed set is a consequence of the rule: a new invariant row is admitted by it, a new prose restatement refused by it | §2e, the rule paragraph |
| Make the test enforce the declared scope: census field-name/value occurrences with an exact allowed-location set, and a mutation showing an undeclared restatement fails | **The hand list is gone.** The checker DERIVES every occurrence of the value vocabulary from the live text, with the history exclusions DECLARED each with its reason (marked spans, struck rows, the header table, the generated closure block), CLASSIFIES each occurrence's site by its FORM under the rule, and FAILS on any occurrence outside the three asserting forms, naming it. Over the sealed text: ten allowed occurrences — §2e's statement, the two matrix rows, the two invariant rows — and zero refused. The mutation runs both ways: a value planted in a §8 prose paragraph fails; the same value planted in a new `V-…` row is admitted; the same value inside a marked span is not counted | `tree/tests/test_0039_degradation_visibility.py::test_the_result_surface_is_stated_once_and_every_other_site_points_to_it`; `::test_the_census_refuses_a_planted_restatement_and_admits_a_planted_invariant` |
| (the six sites named) | §2a's prose, §2b's clause, §8's paragraph, §9's brief and both checklist items are value-free and point; the checklist items name the invariant to check rather than restating what it asserts. The two invariant rows and the matrix rows keep the value, by the rule. Two §1 paragraphs the backstop refused now say "at v13" and point | the same census |

**The criterion survived two attempts to widen it before this seal** — the reviewer's
invitation to enumerate exceptions, and §1's behaviour table, which looked like a fourth
asserting form and turned out to be history by its date. A rule that refuses its own
authors' convenient case twice is worth more than one that was never tested; that is the
argument for it here, and the second seat's independent census over the sealed text (twelve
occurrences of the field's name, reconciling with the authors' ten by declared token set and
declared exclusions, with the one §6 hit outside an invariant row chased and found to be the
struck retired row) is the receipt.

## The ranking, reversed, and the rule underneath it

Round 7's fold ranked the positive check primary because it was over a closed set. That was
backwards, and the second seat reversed its own ranking: **the value census is PRIMARY because
it keys on an IDENTIFIER** — `extraction_unusable` has one spelling, so a token set over the
field's name is complete by construction — and **the must-point check over discussions is the
BACKSTOP because it keys on PROSE**: "names the result surface" is an English judgement no
token list closes, and a paragraph saying "what callers receive" escapes it. The rule under
rounds 6, 7 and 8 is not which half is positive; it is whether a check keys on an identifier
or on English.

**Two limits, stated where the checker lives rather than discovered next round.** The census
tests a site's FORM, which is a proxy for what it asserts: an invariant row that merely
mentions the field in passing is admitted and violates the rule, so a green census says every
occurrence sits in an asserting form, never that every one is load-bearing. And the
must-point half is open by construction, as above.

## The frozen surface, as a count with a shape

Six of the fourteen invariants round 4 froze have moved since, of which two are retired; the
table is unchanged from round 8 and the count is put to the owner as an observation. Round 8
closed R7-2, so both retirements now stand accepted.

## Where the authors ask you to attack

1. **§1 is history by date, not by marker.** Its behaviour table is excluded from the
   asserting forms because it is dated ("measured at v8"), and its one moved row now points.
   The census refuses any value there. The alternative reading is that a dated row is still an
   assertion until someone marks it; the authors chose the date as the test, in the terms
   written into §10 Q1.
2. **The value vocabulary is a regex.** It keys on the identifier and on four phrasings of
   the count ("one outcome", "carries exactly ONE field", …). The identifier half is complete
   by construction; the count half is English and is not.
3. **Six of fourteen, two retired.** See the count above.

## Errors ledger — everything that reached or nearly reached the chain

1. **The first census under-counted** (above): line-level exclusion of history markers,
   fixed to span-level before a line of the fold was written.
2. **The must-point backstop refused two §1 paragraphs** on its first run over the final
   text; both pointed before the suite. The census's first cut then admitted §1's table as a
   fourth asserting form; the second seat showed the row was dated, and history, and the
   form was withdrawn before the seal — a widening caught before it shipped.
3. **Rounds 5 and 6's discarded assemblies** stay disclosed in `PIN.txt`.

## Contents

| path | what |
|---|---|
| `0039-degradation-visibility-SPEC-v19.md` | the accepted spec plus its six post-acceptance cells, the last folding round 8 |
| `0025-relation-vocabulary-enforcement-SPEC-v18.md` | the extraction contract, unchanged since round 8 |
| `PIN.txt` | the canonical-artifact binding: commit, CI run id, suite line, predecessors, both discarded assemblies, protocol |
| `collected/COLLECTED.txt`, `collected/suite-run-raw.txt` | the fresh-clone capture at the pin and its raw transcript |
| `tree/` | the tracked repository at the pin (`git archive`) |
| `prior-rounds/` | the eight 0039 verdicts verbatim and the eight bundle READMEs |
| `SHA256SUMS` | every file above, both directions |
