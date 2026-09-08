<!-- TERMINAL RECORD — the round-4 review bundle README of spec 0038, byte-copied
UNMODIFIED from the ACCEPTED package (sha256 eccfada2950b3ec33dcc137fa3c0751f323556fc359f41a70ee54ae071edd8e9
@ 8588e558ede0ce1989aec2ab421274187c690914, CI 34173288704) on 2026-09-08, the day the
reviewer accepted 0038 v5.9 — round 4's second assembly; the first (18ad6b69…) was discarded
before dispatch and is disclosed inside. It is the one carrier where the round-3 dispositions,
the retracted round-2 item and the consolidated errors ledger live together with the path from
rounds 1–3 (each earlier README rides in its successor's prior-rounds/); the version cells
carry lineage, not the reviewer's dispositions or the process's disclosed failures. The
package remains the archive; this copy is the record. Below this comment the bytes equal the
packaged README — verifiable forever against the archived package: strip the lines above the
first '# ' heading and compare. -->

# 0038 the extraction's speech-act discipline — round-4 external review bundle

Assembled 2026-09-07 by dev. Fourth external round for spec 0038. Round 3
(package `ac8cf169936cc6f50e58c62c570317d5e64e945aac3458a0319541638fe19369`
@ `a03d25d5f415fb0d8a77f2af9f7e402f64e5c9aa`, CI 34168036384) returned for
amendment the same day — "the product implementation remains sound, and round 3
correctly retracts the invalid validation-gate claim in the specification.
However, that retraction was not propagated through the complete bound evidence
set" — one blocking finding and two required corrections; the round-2 editorial
finding was retracted by the reviewer. The verdict is in `prior-rounds/`
verbatim as banked by research, the receiving seat, before any fold (the
reviewer's words are the body after the marker, digest `1515c689645d6fb9`). This
package carries **draft revision v5.9** (v5.8 was the discarded first assembly's label; two assemblies must not share a version cell); the enforcement as shipped is unchanged
since round 2.

**Canonical artifact:** `specs/0038-extraction-speech-act.md` at the pinned
commit (see `PIN.txt` — commit, CI run id, and the suite line as printed; repo
`github.com/veracium-ai/Veracium`, public). The copy here
(`0038-extraction-speech-act-SPEC-v5.9.md`) is byte-identical to `tree/specs/`
at seal; on any doubt the repo wins.

## Disposition map — every round-3 item

| # | the finding (reviewer's words, abridged) | disposition | where |
|---|---|---|---|
| R3-1 | current evidence artifacts still assert the withdrawn conclusion — the model-leg write-up says "THE §8 GATE — PASSES", "two independent raters", "Nothing to pass"; the human-result write-up says "applied independently"; both are in the manifest as evidence supporting the current specification, so a reader following the evidence reaches the conclusion the spec withdrew | THE ROUND'S FINDING, stated as we read it: a document and the artifacts it binds are two carriers, and this programme had a sweep discipline for the first and none for the second. Research's sweep of all sixteen files found FOUR carriers, not the two named — the two write-ups, the rubric, and the registry's own changelog comment. Now bound and current: `SUPERSEDED-CONCLUSIONS.md`, the set's disposition — where any file disagrees with it, it is current and the file is a historical record of a run ("a record amended to agree with a later conclusion is no longer a record") — carrying the check's data as JSON (the withdrawn phrases, the markers as a pointer to the house lint's, the files that must carry a marker, the two records a declared header governs, the exemptions with their reasons — no "owned elsewhere" category: an exemption checked somewhere else was checked nowhere, and that is where the first assembly's stale row lived), the marker convention being the withdrawn-phrase lint's applied to a directory rather than a document. The two write-ups carry supersession headers. `RUBRIC.md` is deliberately NOT amended: it is the instrument the rater was shown, and amending it would make the record of the run false — it is evidence FOR the circularity the spec now states, and leaving it unaltered is what makes that checkable. The registry's changelog comment is marked WITHDRAWN by dev (comments only; the rulings tuple is unchanged, proved by both seats; the file's digest moved and §6b cites the new one, the old declared foreign). Every entry in the disposition is phrased as a STATE, not a to-do — a to-do goes stale the moment it is done and nothing can tell — and `tests/test_oracle_set_disposition.py` reads the disposition's JSON and holds the marker-or-exemption rule over every file in the set, at paragraph granularity with the house normaliser, its markers imported from the house lint rather than retyped; its negative controls include this round's own discarded first assembly's entry and a planted silent carrier. Stated as what it is: over the present set every phrase-bearing paragraph is either declared exempt or governed by a declared header, so the paragraph rule has no live input today — it guards the next edit and is exercised by its negative controls, not by the set. The house lint itself still reads none of the set's files; what changed is reach, through a test inside its selection | `tree/tests/eval/extraction_speech_act/oracle/SUPERSEDED-CONCLUSIONS.md`; the two write-ups' headers; `verb_registry.py`'s changelog; `tree/tests/test_oracle_set_disposition.py`; spec §6b |
| R3-2 | the planted-digest test does not invoke the production membership check — it reconstructs part of the allowed-set logic, so the production scanner could stop inspecting paragraphs while the control kept passing; extract the validator into a shared helper and assert the planted document fails that same helper; the module's opening description still describes the older token rule | one function, `token_membership_violations`, serves the real check and the negative control; the control mutates the real spec body, plants a fabricated digest into the paragraph that names the registry, and asserts the validator reports exactly that token — and nothing on the unmutated body. The module docstring describes the membership rule. A selftest must call the real function, never re-implement it: the rule was already in the runbook and dev broke it in the correction for a claim wider than its implementation | `tree/tests/test_0038_oracle_pin.py` |
| R3-3 | the pseudonymised gate copy records the original's checksum and describes a single substitution, but the original bytes are absent, so a reviewer cannot prove the copy differs only by the stated substitution | the claim is NARROWED rather than the evidence grown (the reviewer's third option): the package carries a bound derived copy and cannot independently establish its byte-level fidelity to an original it does not carry. Both alternatives fail for stated reasons — shipping the original into the reviewer package would publish the name the owner ruled out; an attestation is a promise, not a proof | spec §6b |
| R2-4 | (round 2) the §4 heading appears twice | RETRACTED by the reviewer: the heading occurs exactly once; the earlier observation was a display or extraction artifact. Round 3 answered it with counts rather than a change | — |

## The evidence this package offers, each runnable offline from the archive's own bytes

| artifact | its executable check |
|---|---|
| the corpus and its baselines, bound to the spec | `tests/test_0038_corpus_pin.py` |
| the oracle set, bound to the spec by one pin, pseudonymised, with the digest-token membership check and its production-validator control | `tests/test_0038_oracle_pin.py` |
| the ingest enforcement, its matrix and its mutants | `tests/test_0038_instruction_enforcement.py` |

Dev's seal receipt runs the three from the extracted archive's bytes in a
throwaway; the count that run printed is the one stated in the seal announcement.
The two-seat seal script's ASSERT-10 runs the same three files, set explicitly.
The withdrawn-phrase lint runs over the sealed tree with the count of entries
registered for this spec printed beside it.

## Where the authors ask you to attack (spec §9, carried verbatim from v5.9)

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

## Errors ledger

- **A first seal of this round was DISCARDED before dispatch** (both seats'; sha256 `18ad6b69ebc0e4d9ddbb5a13399f0d57fb94463c48d82c95dccfad8183882df4`, both legs green on it, disclosed in `PIN.txt` and `collected/`): the bound disposition artifact `SUPERSEDED-CONCLUSIONS.md` still said the registry's changelog "needs the same treatment" while the registry beside it in the same set already carried the marker — the artifact whose job is to be current contradicting the set it dispositions, in the package that answers a finding about exactly that. Both legs were green because nothing reads that sentence against the registry; dev found it checking a leg note against the sealed bytes. The entry is corrected, the set re-pinned, and the package resealed. R3-1 one level down: the disposition of the evidence is itself evidence, and it needs the same sweep.
- **A suite was launched against a tree whose adoption had not been confirmed** (dev's, during this reseal): the adopt script had refused v5.9 at its version gate, and the chain launched the full suite anyway — a run that could not name what it ran against; its green would have been a true statement about bytes nobody could identify afterwards. Caught inside a minute, stopped by PID including the evidence runner that had reparented to init, relaunched only on a green adoption, and the launch is now gated on the adoption's exit. The same shape as the round: the spec current and the evidence stale (round 3); the evidence current and its disposition stale (this round's first seal); the tree changing under a check already in flight (this). A result is only as good as the thing it can name as its input, and of the three only this one is now mechanical.
- **The retraction stopped at the document** (research's text; the class is the programme's): every sweep discipline here reads the spec, and none read the artifacts the spec's manifest binds. The reviewer read the evidence rather than the claim. The disposition artifact and its JSON-declared check are the first mechanism for the second carrier.
- **The negative control re-implemented the validator** (dev's): the rule "a selftest calls the real function" was already in the runbook; the control written to answer R2-2 broke it. One function now.
- **A restored section nearly reinstated a renamed key, and a superseded pin's commit subject overstated its body** (rounds 2–3, disclosed there and carried here as the lineage's history): v5.6's §9 fragment and d07043d's subject are in round 3's README; nothing new this round on either.
- **R2-3's fidelity claim was wider than the package could support** (both seats'): the derived gate copy's header records a checksum the reviewer cannot check without bytes we chose not to ship. Narrowed.
- **The registry's own changelog carried the withdrawn claim in a bound, pinned file** (dev's, found by research's sweep): marked, not rewritten; the rulings did not move and both seats proved it before the digest was re-cited.

## Contents

- `0038-extraction-speech-act-SPEC-v5.9.md` — the spec, byte-identical to `tree/specs/`
- `PIN.txt` — commit, CI run id, suite line, the corpus digest, the product change, every predecessor by identifier, the protocol
- `collected/COLLECTED.txt`, `collected/suite-run-raw.txt` — the fresh-clone capture at the pin, profile `[dev,mcp]`, raw transcript from the same run
- `prior-rounds/` — the round-3 README; the round-1, round-2 and round-3 verdicts (as banked)
- `tree/` — `git archive` at the pin (tracked files only, asserted both directions), including the seventeen-file oracle set with `SUPERSEDED-CONCLUSIONS.md`, and the three 0038 test files
- `SHA256SUMS` — every file above, excluding itself
