# 0026 §6a — the acceptance measurement (dev, 2026-08-26; re-measured 2026-08-29)

**Result: the gate is CLEARED. 0.64% (439 of 68,479) under lex-9 against
a 2% bar — and that figure is an UPPER BOUND, not an estimate.**

**RE-MEASURED 2026-08-29 (external round 1, 0026-R1-1):** lex-2's
directional rule was a proximity scan and proximity is not authorship —
the reviewer executed five counterexamples (passive recipients, the
post-verbal agent, embedded clauses, ambiguous pronouns) and the rule
misclassified all five. lex-3/lex-4 are a directional grammar (lex-4 adds coordinator transparency and the coordinated-co-source rule); see
`relay_lexicon.py`'s header for the rules and the third row below for
its pass. The ambiguity class is COUNTED: exactly 0 of the 439
fires restricts via the ambiguous class alone on this corpus.

**A claim from the first version of this document is NARROWED
(0026-EVIDENCE-R1-1): "both passes ship" was true of the figures, not
of the artifacts — lex-1's implementation was never committed, so its
8.20% row below is recorded prose history, reproducible only in cause
analysis, not by rerun. lex-2 remains in git history
(`66d11a7`); lex-9 is the shipped detector. The aggregate now has a
closed validator with a cross-artifact manifest anchor and a real
`--aggregate` verify mode; whole-corpus figures are RECORDED ONLY
(they reproduce with `--cache` on the measuring host).**

§6a pre-commits that if the lexicon's false-positive rate exceeds 2% of
grounded first-person triples, the lexicon narrows before v1 ships. It did
exceed it on the first pass, the lexicon narrowed, and this records both
passes rather than only the one that passed.

## What was measured, and against what

| | |
|---|---|
| cache | `extractions.jsonl`, 52,359 entries, sha256 `654e336a…`, 6 unparseable rows counted and skipped |
| population | 68,479 **grounded first-person triples** — an in-registry relation with canonical subject `user`. This is the denominator §6a's 2% is a share *of*. |
| detector | `relay_lexicon.py`, run by `measure_false_positives.py`; counts-only aggregate in `fp_aggregate.json` |

The cache is byte-identical to the one behind 0025's published census (same
sha256), so these figures sit in the same frame as the 183,417 / 41.7% ones.

## All three passes

| | lex-1 (prose history) | lex-2 | lex-4 | lex-5 | lex-6 | lex-7/8/9 (shipped; identical figures) |
|---|---|---|---|
| fires on grounded first-person | 5,618 = **8.20%** | 415 = 0.61% | 418 = 0.61% | 849 = 1.24% | 481 = 0.70% | 439 = **0.64%** |
| …of which ambiguous-class only | n/a | n/a (class did not exist) | 1 | 2 | 2 | **0** |
| vs the 2% gate | **OVER** | **UNDER** | UNDER | UNDER | UNDER | **UNDER** |
| suppressed by the directional rule | **0** | 211 | 199 | 280 | 254 | **287** |
| lexicon coverage of `third_party_claim` notes | 539 / 3,898 = 13.8% | 138 / 3,898 = 3.5% | 135 = 3.5% | 222 = 5.7% | 217 = 5.6% | 220 / 3,898 = **5.6%** |

lex-5/lex-6 are research's red-team recall finding folded: the verb
list omitted `claimed` (the name of the relation 0024 quarantines) and
the assertion/transmission/professional-judgment classes, and NOTHING
measured recall — §6a is FP-only and every matrix inbound cell used an
in-list verb. lex-5 added them all and measured 1.24%; reading the
fires (the §6a discipline) showed the nominal homographs
(notes/added/adds/emails) were every sampled fire, so lex-6 keeps only
their unambiguous inflections; lex-7 (round 2) replaces the token scan with head construction and settles at 0.64%; lex-8 adds comitative co-speakers and the third-person self-possessive, measuring identically on this corpus; lex-9 (round 3) adds or-disjunction and the artifact-vs-entity self-possessive split, again identical — the R3-1 shapes are absent from the own-use population. Recall is now
MEASURED: held relay cells across the verb classes must fire, and
removing `claimed` alone is a red matrix.

lex-4's small movements against lex-2 are the grammar working: passives
and agent phrases that lex-2 misread as outbound now fire (inbound), a
handful lex-2 misread as inbound are now suppressed (agent = user), and
the she/he/they triples lex-2 silently called the user's are now split
between ambiguous fires (1) and genuine subjects.

## Why lex-1 failed, which is the useful part

Both causes were found by reading the fires, not by looking at the rate.

**It carried the ADVICE class.** `recommended`, `suggested` and `advised`
produced 4,445 of 5,618 fires — 79% — on constructions like *"recommended
brand"* and *"recommended time management tool"*. Recommending is a speech
act; it attributes nothing to a named source. §3a's own list is attribution:
said / told / stated / according to / confirmed by / per ⟨entity⟩. lex-2 is
that class and nothing wider.

**Its directional rule was written in the wrong grammar, and this is a
finding about the SPEC, not only about the lexicon.** §3a states its
directional cells in the first person — *"I told my doctor…" must never
match*. This extractor narrates the user in the **third person**: *"user
confirmed no dietary restrictions"*. The first-person form suppressed
**exactly 0 of 68,479 triples**, while the third-person form was read as
INBOUND — the user's own word treated as somebody else's claim, which is the
precise failure the bar exists to prevent. The rule that matters is whether
the attributing subject **is the user**, however the extractor names them.
The pronoun was never the point. §3a should say so.

A third defect never reached the corpus: lex-1 read the possessive in *"my
doctor said"* as first-person and suppressed it, which would have hidden the
commonest relay shape there is. The named cell caught it before any run.

## What the shipped upper bound is, and is not

It is the share of grounded first-person triples the detector **fires on**.
Every fire is a *candidate* false positive, so the true rate cannot exceed
it. "Genuinely own" is a property of the content, and using the detector to
decide which of its own fires are false would be the self-assertion failure
this project already has a name for — so the bound is reported instead, and
it clears the gate on its own.

A 10-fire sample was labelled by hand to characterise the residual. Roughly
3 in 10 are genuine relays (*"mechanic said brake pads are getting worn
out"*), putting the true rate near **0.4%**. The rest fall into four named
classes, none of which the gate requires fixing:

1. **verb/noun homographs** — *"park reports"*, *"creating reports"*
2. **agentless participles** — *"no diet mentioned"*
3. **passive agent after the verb** — *"project mentioned by user"* (the
   direction scan looks backward only)
4. **non-entity objects of a frame** — *"according to parse rules"*

## The M-2 coverage denominator, stated honestly

**Scope (research, pre-seal read-forward): the coverage figure is a
lexicon-reach diagnostic over the already-quarantined
`third_party_claim` note population — NOT recall over the
concrete-relation laundering population the check actually targets,
whose denominator no archive-local number measures. A
laundering-recall probe joins the evidence when a labelled corpus for
that population exists.**

The lexicon matches **220 of 3,898** `third_party_claim` triples carrying a
non-empty note — **5.6%**. §8's claim ships with that number rather than an
implied whole, which is what M-2 asked for.

One caveat the figure carries: M-2 asks for the share of **source-naming**
notes matched, and identifying that subset independently would require
labelling the whole note population. The denominator here is *all* non-empty
`third_party_claim` notes, and source-naming notes are a subset of it — so
5.6% is a **lower bound** on the quantity M-2 names. It is reported as the
computable one, not as the one asked for.

Narrowing bought this at a cost against lex-1: coverage fell 13.8% → 5.6%
while the fire rate fell 8.20% → 0.64%. That trade is the gate's whole
purpose, and the
reviewer can see both halves of it.

## Standing

Dev's half of §6a is done. Research co-verifies the run — the script, the
aggregate and the cache manifest are all here, and `--cache` reproduces
every number on the measuring host.
