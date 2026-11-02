# Feature spec: speaker turns inside a user event — the assistant's first person is not the user's

Spec-Status: accepted

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

| | |
|---|---|
| **Author / session** | dev (veracium dev seat), 2026-10-19, on Quentin's word "Do the 1 and 2 fix" (2 = this spec) |
| **Version** | **v0.5 — 2026-11-02: §4b judges a `deadline`'s date by 0045's resolution** (0003 v18.2 §4c-v.6d; the 0.29.0 hold's B1: research's read of the 0.29.0 notes, `1eb722a9`, and stage 1 on `2088d08`, `8b0de7d2`). No change for any other triple. **Prior: v0.4 (drafted by research 2026-10-21; ADOPTED by dev 2026-10-22 from research 4f0724b0, candidate sha256 471ef4cec44ba7e3…) — R-II round 2's RII-02: ATTEST-6 (`attest_turns.py`, sha256 `ccabb664…`), ATTEST-5 with one rule changed (a counted `h`/`q` is a USER label for the weak-name test, as the class table already said); measured on the fresh holdout H5 (research 76e34b3f; §6). Rows written under ATTEST-5 keep their `attv` (INV-G7).** v0.3.1 — 2026-10-20: research's v0.3 read (READ-0051-v0.3.md, research 3bb09e35, sha16 1cab911e4c73d7d5) reads clean; its two edits in: E1 (H4's order, §6), E2 (INV-S8).** v0.3 (sha16 54599485d40c2687): **research's v0.2 re-read and both holdouts folded** (READ-0051-v0.2.md, research d498d9af, sha16 74a20b947ccedeb8; H3 scored, research 3a933ebf; H4 scored, research b3242a94). B3 (a heading inside an assistant reply ended its turn: 24.5% of LongMemEval's assistant turns) → the one-pass hand-off rule, **ATTEST-5** (`attest_turns.py`, sha256 `0bb7779f…`); C1–C4; S1, S2; the backstop moved OUT of the frozen file into product code (`speaker_backstop.py`) with its normalisation fixed (H4's two lost user facts). Prior: v0.2 (sha16 b20d79ac8fac606e; ATTEST-4 `ba09a2a1`, never shipped), v0.1 (c12075491ad7bde7) |
| **Status** | *see `Spec-Status:` at the top — canonical.* |
| **Internal reviewers** | research (stage 1 read v0.1; H3 built and scored by research) · dev (author) |
| **External review** | **owed** — a full spec (it touches `ingest.py`, a guarded file, and amends 0045 §3's input rule and its assertability answer, a frozen surface). Acceptance path RULED by Quentin 2026-10-19: his word after research's read, the R-II package carrying the code; research's condition, that the shipped version is measured on a fresh holdout before R-II seals, is met by §6's H4 row (ATTEST-5) |
| **Decision + date** | **v0.4 ACCEPTED 2026-10-22 on the owner's word** ("accept 0051 v0.4"; the acceptance path v0.3.1 took: research's reads first — its stage-1 read a94fe187, H5 scored once (76e34b3f), the firing5 re-run re-derived — dev's adoption (c34d686, from research 4f0724b0), then the owner's word); R-II round 2 carries it to the external reviewer, as R-II carried v0.3.1. **v0.3.1 ACCEPTED 2026-10-20 on the owner's word** ("Accept 0051"; the second path of PROCESS §4a, on the acceptance path the owner ruled 2026-10-19: research's reads first, the R-II package carrying the code to the external reviewer). The accepted text is v0.3.1 (sha16 66adb4ebb87247c2 as read by research); the adoption's declared deltas are this line, the status line, the Review closure section, the reviewer checklist copied from TEMPLATE.md, and the rewrite of off-tree script names to plain text (research's landing read L2, 2026-10-20) |
| **Path** | full |

---

## 1. Problem and motivation

`remember()` takes ONE author per event, and ingest does not separate speakers inside an event. A host that passes a
whole conversation, the user's turns and an assistant's, as one event under `author=USER` hands the extractor and
ATTEST a text in which the assistant's first person reads as the user's. Measured 2026-10-19 (ledger `0d8bec9`;
evidence `.claude/skills/pre-seal/impl-review/0044/mixed-transcript-2026-10-19/`, local) on 12 hand-written
two-speaker transcripts at `3914f73`. Passed whole, an assistant-only value was asserted as the user's on a fact line
or the wiki in **4/12** transcripts (6/18 planted values). **Two of the six carry `att=attested`**, because ATTEST-3
reads the raw text and "I'm based in Toronto" / "I prefer ThinkPads" is a first-person sentence in it. By label format:
unlabelled 3/4, `Human:`/`AI:` 1/3, `User:`/`Assistant:` 0/3, named speakers 0/2. Passed turn by turn (the assistant's
turns under `ASSISTANT`), 0/18. One run per arm, fixtures written by dev: a demonstration, not a rate.

The docs half shipped as `94c46d7`: one speaker per event, in `remember()`, the MCP tool description and
`docs/api.md`. This spec is the product half, for the case the product CAN see: **a turn the event itself labels for
a non-user speaker**. Doing nothing leaves an `attested` label on a fact the user never stated, and an assertable user
fact whose only source in the event is the assistant's turn.

**Alternatives rejected.**
- *Floor the whole event to `derived(ASSISTANT)` when a non-user label is found*, so nothing from it is assertable.
  Robust and simple, but it demotes the user's own facts from that event: 10/10 user values reached a fact line in
  every arm. The user's turns are the user's. v0.1's grammar did this by accident (B1); v0.2's does not.
- *Split the event into per-speaker events at ingest.* The structural answer, but it changes the event and episode
  identity (one `evidence_ref`, one episode) that 0006, 0029 and 0041 key on. The docs half already tells hosts to
  split, which is where the split belongs.
- *Prompt rule alone.* It relies on the model: the measurement's one labelled leak (`Human:`/`AI:`, c11) happened
  under a prompt that already names one author. The prompt rule is kept as the first line, with a deterministic
  backstop (§4b).
- *Attempting unlabelled transcripts.* Nothing in the text marks the speaker change, so any heuristic would refuse the
  user's own sentences. Out of scope; §8 states it, and the docs carry it.

## 2. Field contracts touched

| field / carrier | change |
|---|---|
| `Edge.att` | unchanged domain. For a USER-effective event with a non-user turn, `attested` now requires ATTEST-3 over the event's USER TEXT as well as over the raw text (§4a). Restriction only |
| `Edge.attv` | `ATTEST-6@ccabb664` on every predicate-judged edge written from now (§4a). `ATTEST-3@b1329a81` and `ATTEST-5@0bb7779f` rows keep theirs (immutable, INV-G7; versions coexist, INV-G13). `_ATTV` already admits the form. T11b's import must admit it too |
| `Provenance.disclosure` | a declarative triple whose non-`user` side(s) occur ONLY in non-user turns is written `use_only` (§4b). Restriction only |
| **0045 §3, amended** | its "Can it make a user-asserted fact non-assertable? **No**" becomes "**only §4b's restriction**: a fact whose value the event shows only in a non-user turn". The input rule "ATTEST over the RAW event text" becomes "ATTEST-3 over the raw text AND over the user text" |
| `EXTRACT_PROMPT` | one rule added (§4c). `run_longmemeval.py`'s `extract_prompt_sha` moves with it, so the next LongMemEval run re-extracts (>$10 needs Quentin's word) |
| `remember()` return | a new counter, `speaker_restricted`: the triples §4a or §4b restricted. It is present on every path (0025 §4c's rule; the `subject_refused` precedent) and is the host's signal to split |

## 2c. Untrusted inputs — REQUIRED, blocking

The event text is host-supplied and, in the mixed case, partly model-authored. The label grammar (§4) is matched on
it. A hostile text can:
- (i) **omit** labels. This spec then does nothing, which is the pre-spec behaviour (§8 limit 1).
- (ii) **forge a user label** in front of an assistant sentence. This spec then does nothing for the turn it opens:
  the same reach as today, since the author line already claims USER.
- (iii) **forge a non-user label** in front of the user's own text. This is the only new reach. It restricts that
  whole turn, **up to the next label that ends a non-user turn** (a listed label, or an unlisted name that is
  established or hands off, §4), and it can only RESTRICT: those sentences stop counting for `attested` and for
  assertability.

No input can make an edge `attested` or `mentionable` that is not so today (INV-S4).

### 2c-ii. Assertions about reach — REQUIRED

ATTEST-3 is still the only predicate (INV-G1 unchanged); ATTEST-6, like ATTEST-5 before it, is ATTEST-3 run twice and conjoined. The extractor
still cannot claim grounding. The new reads are of the event text the write path already holds; nothing new reaches
the store except the counter.

## 3. Trust-class matrix — REQUIRED, blocking

| effective author / content | before | after |
|---|---|---|
| USER, direct, no non-user turn | ATTEST-3(raw) | ATTEST-6(raw) = ATTEST-3(raw) (INV-S3) |
| USER, direct, ≥1 non-user turn | ATTEST-3(raw) | ATTEST-3(raw) AND ATTEST-3(user text); a triple whose non-`user` side(s) occur only in non-user turns → `use_only` |
| any other | `not_attested` / `non-user-effective`, no predicate | unchanged |

## 3b. Authorization and scope

n/a — no principal, scope or entitlement is read or written.

## 4. Behaviour

**The turn grammar** is the frozen file `src/veracium/attest_turns.py` (sha256
`ccabb664bbf1567a6d45bae6c64c7dbf08ff0c3a319f69bf83d9642700b1cba7`, ATTEST-6). Its docstring is the normative text; in short:
- **Labels.** A LABEL sits at the start of the event or of a line, after optional spaces, `>` quote markers and a
  markdown heading, inside optional `**`/`__`. It has one of three shapes: `NAME [ (parenthetical) ] :`,
  `NAME said:`, or a heading that is only NAME.
- **Names.** NAME is one to three words of letters (and `'` `.` `-`), at most 32 characters, none of them `said`. A
  colon followed by `//` is not a label.
- **Turns, one left-to-right pass** (B1, B3; C3). A USER or NON-USER label always ends the turn before it. OUTSIDE a
  non-user turn, an unlisted label opens a USER turn, and its name becomes ESTABLISHED iff its NEXT label is
  NON-USER. INSIDE a non-user turn, an unlisted label ends that turn iff its name is already established or its NEXT
  label is NON-USER (the hand-off, which also establishes it); otherwise it is the turn's own text — a heading, a key,
  a list title ("Pros:", "Note:", "Ingredients:"). No whole-event alternation rule applies to unlisted names: a later
  recurrence never reaches back.
- **Classes:**
  - USER: `user · human · me · customer`, and `you` in the `said:` form;
  - NON-USER: `assistant · ai · chatbot · claude · chatgpt · gpt · gemini · copilot`;
  - WEAK: `system · model · agent · bot · *bot`. These are NON-USER only in a two-speaker shape: a USER label is
    present (a counted `h`/`q` among them: RII-02), or the same weak name labels two turns with another label between
    them (B1);
  - LETTERS: `h`/`q` (user) and `a` (non-user), only as a pair;
  - **UNLISTED**: any other name, an uncounted weak name or letter — governed by the pass above.
- **User text.** Text before the first label is USER text. The USER TEXT is every user turn, labels removed; it exists
  only when at least one NON-USER turn does.

**4a. Attestation (ATTEST-6).** For a USER-effective event (0019 v7): `att = attested` iff ATTEST-3 answers ATTESTED
over the raw text AND, when the event has a non-user turn, over its user text. `attv = ATTEST-6@ccabb664` for every
predicate-judged edge, whatever the event. The literal is bound by a test to `attest_turns.py`'s digest AND to
`attest_v3.py`'s (`b1329a81`), since ATTEST-6's verdict is a function of both (F3). Neither file is edited after
freezing: an edit is a new version, measured on a fresh holdout before it ships (0045 §4a, Versioning).

**ATTEST-5 → ATTEST-6 (R-II round 2, RII-02).** ATTEST-5's weak-name test ("the event carries a USER label") left out
a counted `h`/`q`, which its own class table makes USER. So in "Q: / Bot: / A:" the weak `Bot:` read UNLISTED, its line
joined the user text, and a bot's first person could be stored attested and mentionable. ATTEST-6 computes the letter
pair first and counts it in that test; nothing else in the file changes. ATTEST-5's bytes stay retrievable
(`specs/evidence/0051/holdout-h4/attest_turns_ATTEST-5_0bb7779f.py`, digest-bound), so every `ATTEST-5@0bb7779f` row
names bytes that still exist.

**4b. The backstop** — PRODUCT code, `src/veracium/speaker_backstop.py`, NOT the frozen predicate (research's v0.2
read, on H4): a triple it restricts has its value in no user text, so ATTEST-6 over the user text cannot attest it;
its only independent effect is disclosure, and its normalisation may be fixed without a new attestation version
(the frozen file's own `only_in_non_user_turns` — ATTEST-4's matcher, carried in ATTEST-5's and ATTEST-6's bytes — is unused). For a USER-effective
event with a non-user turn, a declarative triple is written `use_only` (the class ASSISTANT authorship would have
given it) when EVERY non-`user` side of it occurs in some non-user turn and in no user text:
- the sides checked are the object when the subject is `user`; the subject when the object is `user`; both otherwise
  (F2: "Anna works at Acme", stated only by the assistant, is covered);
- **a `deadline` whose subject is `user` or an obligation** (v0.5; `schema.is_obligation`: relation `deadline` and a subject that, as `str(subject).strip().casefold()`, is not `user` and carries no `kind:` prefix (`^[a-z][a-z_]*:`); 0003 §4c-v.6d) is judged
  on its DATE alone, by 0045's resolution rather than by tokens: it is restricted when the event's non-user
  text grounds the object and its user text does not (`grounding.ungrounded` False over the one, True over
  the other, at the session date; each text is the bodies the frozen grammar's `turns` gives, joined by
  speaker: `speaker_backstop._date_restricts`; the branch is taken when the caller passes the relation and
  the session date, as ingest does, `schema.OBLIGATION_RELATION` being `deadline`). Why: the obligation's name is a side the user says, so the every-side rule never fired on a date
  only another speaker gave; and the extractor writes an obligation's date as ISO, which a date said in words
  never matches as tokens. An entity's deadline (`person:alice`) is judged as above, on every side. INV-S8
  holds for the rule: ATTEST-3's triggers name no `deadline`, so ATTEST-6 attests none;
- a side is matched as a TOKEN SEQUENCE on word boundaries ("Go" is not in "going"), after its `kind:` prefix
  (`person:`, `org:`) is dropped, `_` and `-` are read as spaces, and ATTEST-3's own normalisation is applied (F2);
  tokens are runs of letters and digits, so an apostrophe splits ("my husband Daniel's 40th" holds "daniel": H4
  h4-073); and each token is compared by a plural stem ("window seats" ~ "window seat": h4-083; "boxes" ~ "box";
  never "glass" ~ "glas"). Both H4 rows restricted a USER fact under ATTEST-4's matcher;
- a value found in no turn (a paraphrase) is unchanged: §4c is then the only defence (§8 limit 2).

**4c. The extraction rule.** One rule in `EXTRACT_PROMPT`'s RULES: "If the event is a transcript whose turns are
labelled by speaker, only the user's turns state facts about the user. A statement in a turn labelled for another
speaker (an assistant, AI, bot or agent) is never a fact about the user: omit it from `triples`, and in the episode
attribute it to that speaker."

## 5. Regime analysis

Measured on LongMemEval s_cleaned (distinct turns; synthetic, so bounds, not rates), with the frozen file, by
firing5.py (local evidence, not in this tree) (dev, sha256 `7b0d2d73…`). These counts were measured under ATTEST-5.
ATTEST-6 differs only on an event that carries a counted letter pair AND a weak name, so the rows can move only
there. **Re-run under ATTEST-6 (dev, 2026-10-22; research re-derived it, research `evidence-0051/firing5-attest6/`):
byte-identical output; no row moves.** 28 of the measured events carry a letter pair (`h` or `q` with `a`): 3 user
turns, 12 placeholder events, 13 session pairs. None changes class or turns between ATTEST-5 and ATTEST-6.

| regime | behaviour |
|---|---|
| no label at all (the common chat event; H1 and H2) | identical to today, `attv` aside (INV-S3). The grammar fires on 0/120 of H1 and 0/120 of H2 (research) |
| a user's notes with `Name:` lines ("Model: Corolla", "Agent: Jane Doe", "Note: …") | unchanged: outside a non-user turn an unlisted name or a lone weak name opens a USER turn (B1). Of 93,931 user turns the grammar finds a non-user turn in 20: 17 are `assistant:` segments genuinely mixed into the user turn (correct), 3 are pasted `Q:`/`A:` FAQ or flashcard text (a restriction of pasted content) |
| an assistant reply with headings, keys, list titles ("Pros:", "Ingredients:", "Note:", "location:") | they stay in the assistant's turn (B3). Behind "User: hi\nAssistant: ", 46 of 95,591 assistant turns reopen a user turn (0.05%; 27,922 of 163.8M characters, 0.02%; ATTEST-4's every-label rule: 24.5% and 27.3%). 25 of the 46 are C1's shape (§8 limit 7) |
| real session pairs, "User: <u>\nAssistant: <a>" (C2) | 110 of 94,694 assistant turns lose text to a user turn (0.12%; 101,174 of 161.8M characters, 0.06%). The two shapes (research): a heading in the user's own turn right before the assistant label establishes that word, so the assistant's same heading reopens a user turn; and a heading at the end of one non-user turn directly before another non-user label hands off (§8 limit 8) |
| labelled two-speaker transcript | §4a–§4c apply |
| named speakers, two or more exchanges ("Quentin: …" / "Claude: …" / "Quentin: …") | the user's name is established (or hands off), so its turns are USER turns and the user's own lines are not restricted |
| named speakers, ONE exchange after the assistant ("Claude: Where do you live?" / "Quentin: I live in Porto.") | **restricted**: "Quentin" is unlisted, unestablished, and hands off to nobody, so it stays in Claude's turn (§8 limit 6; counted by `speaker_restricted`) |
| labels mid-line ("User: hi Assistant: hello") | not recognised (§8 limit 3) |
| **existing, stated (F4):** a retraction word ANYWHERE in the raw text ("not true", "kidding") already kills every attestation in the event, including one in the ASSISTANT's turn. The AND cannot recover it, correctly so (restriction only) | unchanged |
| **existing, stated (F4):** a user sentence that starts on a label line ("User: I live in Porto.") is not attested by ATTEST-3 ("user:" is no closed filler), so in labelled transcripts only a turn's later sentences attest. This bounds §4a's effect | unchanged |

## 6. Invariants and executable checks — REQUIRED, blocking

| id | invariant | mutant it must kill |
|---|---|---|
| INV-S1 | ATTEST-6 never answers `attested` for a sentence found only in a non-user turn | drop the conjunction → c11's `located_at Toronto` reads `attested` |
| INV-S2 | no `mentionable` triple whose non-`user` sides occur only in non-user turns, in any orientation; and a user fact whose value the user text holds in any normalised form is never restricted | drop §4b; one-sided prefix drop (`user partner_of person:Anna`); substring match ("Go" in "going"); keep the apostrophe in tokens (h4-073); drop the plural stem (h4-083) |
| INV-S3 | an event with no non-user turn gets ATTEST-3's answer | a grammar that classes an unlisted name or a lone weak name as non-user → research's five B1 note rows move |
| INV-S4 | restriction only: every edge's `att` and disclosure is ≤ the pre-spec answer for the same event and triple | AND replaced by OR in §4a → a promotion found |
| INV-S5 | `attv` is `ATTEST-6@ccabb664` on every predicate-judged edge, and the binding test pins both files' digests; ATTEST-5's kept bytes are bound to `0bb7779f` | keep `ATTEST-5@0bb7779f`; edit either file without a new version |
| INV-S6 | the grammar's domain: every shape × class × position (n = 0, 1, 2, 3 labels; `**`/`__`; `>`; headings; parentheticals; `said:`; the weak two-speaker rule both ways; the letter pair; a URL line; a label word inside a sentence), and C3's pass: a heading inside a reply stays; a hand-off ends the turn; an established name ends it; a later recurrence never reaches back; the one-exchange row restricted and counted; **and every sequence of one to four labels over the class alphabet, its classes checked against an oracle written from the docstring, not from `_classify` (RII-02 needs three labels: a letter pair and a weak name, so no one- or two-label cell can see it)** | ATTEST-5's weak-name test (counted letters left out: fails at 07df8f8, 864 of 22,620 sequences); each class member dropped in turn; ATTEST-4's every-label rule; establishment without the hand-off condition; a whole-event alternation rule for unlisted names |
| INV-S7 | `speaker_restricted` counts exactly the triples §4a or §4b restricted, on every path | the counter omitted on a path; counting §4b only |
| INV-S8 | **no triple is both restricted by the backstop and attested by ATTEST-6** — the premise of §4b's argument that the backstop's normalisation may change without a new `attv` (research's v0.3 read, E2). Measured: 0 of H5's 130 items under ATTEST-6 (research diagnose_h5.py); ATTEST-6's turns equal ATTEST-5's on every H3 and H4 item (score_h5.py), so their 0 of 260 carries over. Under ATTEST-5: 0 of H3 ∪ H4's 260 items (dev inv_s8.py (local evidence, not in this tree); research's check_backstop.py likewise) | a backstop normalisation STRICTER than ATTEST-3's (drop the leading-article strip) → "User: Hi. I prefer Beatles.\nAssistant: I prefer the Beatles too." with `prefers the Beatles` reads both ATTESTED and restricted (dev s8_mutant.py (local evidence, not in this tree), run: unmutated restricted=False, mutant True) |
| INV-S9 (v0.5) | a `deadline` whose subject is `user` or an obligation is restricted exactly when the non-user text grounds its date and the user text does not; any other triple keeps the every-side rule | 0003 §4c-v.8's INV-OB11: `B1-token-rule-kept`, `B1-whole-event-grounding`, `B1-user-condition-alone`, `B1-subject-user-form-excluded`, `B1-caller-drops-the-relation`, `B1-caller-drops-the-date` (`specs/evidence/0003/obligations_mutants.py`) |

**ATTEST-6's holdout, H5 (RII-02; 0045 §4a, Versioning).** Scored ONCE by research (`76e34b3f`), with a
pre-registered scorer (`b170840a`) and all three files' digests asserted. 130 items in two strata, each from its own
blind author (0 tool uses; the briefs committed verbatim before either author was launched, `90d25056`; written after
ATTEST-6 was frozen and its digest verified; never shown 0051 or ATTEST): **H5-G** (65, H4's brief: the no-regression
measure) and **H5-T** (65, letter-labelled transcripts with a weak-named automated participant: the change's own
measure). This was needed because **H3 ∪ H4 hold no counted-letter event**: ATTEST-6 changes none of their 260 items.
A second blind labelling agrees 130/130. Dev stated before the score that it had not read H5 and would not.

| H5 | ATTEST-3 | ATTEST-5@0bb7779f | **ATTEST-6@ccabb664** |
|---|---|---|---|
| H5-G false attestations (one-sided 95% upper bound) | 0/38 (7.6%) | 0/38 (7.6%) | **0/38 (7.6%)** |
| H5-G recall | 2/27 | 2/27 | 2/27 |
| H5-T false attestations | 0/33 (8.7%) | 0/33 (8.7%) | **0/33 (8.7%)** |
| H5-T recall | 2/32 | 2/32 | **1/32** |
| H3, H4 | — | as below | identical to ATTEST-5, item for item |

- **H5 does not measure a false-attestation reduction.** ATTEST-3 attests 2 of H5-T's 65 items, so no false
  attestation was available to remove. H5-T does exercise the change: 64 of its 65 items carry counted letters, and in
  exactly those 64 the classes and the turns change.
- **The one recall loss (h5-112) is H4's echo case again:** ATTEST-5 attested `located_at Leeds` on the BOT's "I'm
  based in Leeds.", which the defect had placed in the user text; the user's own "I'm in Leeds too" is outside
  ATTEST-3's construction. The fact stays stored and assertable.
- **§4b under ATTEST-6 on H5:** of the 28 gold-false values only another speaker gave, 26 are restricted (21 under
  ATTEST-5). **One user fact is restricted (h5-048, §8 limit 11)**, and none under ATTEST-5, which hid it.

**The measured holdouts for ATTEST-5 (0045 §4a, Versioning; B2, C4).** Scored ONCE by research, with pre-registered scripts and all
three files' digests asserted. **H4 is ATTEST-5's holdout** (130 items, 58 true / 72 false; a blind author with 0 tool
uses, briefed from §1's problem and real assistant formats, never shown 0051 or ATTEST; **written by the blind author
before ATTEST-5's bytes existed, and committed (`375089fb`) after ATTEST-5 was frozen; the author saw neither the rule
nor the file, and dev did not open H4 before research's score** (research's v0.3 read, E1); a second blind labelling,
130/130 agreement; research b3242a94). **H3 is its regression set** (scored
before ATTEST-5 existed, then opened; research 3a933ebf).

| set | ATTEST-3 | ATTEST-4@ba09a2a1 | **ATTEST-5@0bb7779f** |
|---|---|---|---|
| H4 false attestations (one-sided 95% upper bound) | 7/72 (17.5%) | 4/72 (12.3%) | **3/72 (10.4%)** |
| H4 recall | 12/58 | 11/58 | 9/58 |
| H3 false attestations | 0/72 | 0/72 | 0/72 |
| H3 recall | 1/58 | 1/58 | 1/58 |

- The 3 recall losses on H4 (h4-014, h4-083, h4-103) are labels that rested on the assistant's draft repeating the
  user's fact: ATTEST-3 over the user's own text does not attest them. Removing them is the spec's purpose, and the
  facts stay assertable.
- **H3 does not exercise the conjunction (S1):** ATTEST-3 attests 1 of its 130 items, so its 0/72 holds for ATTEST-4
  and ATTEST-5 only because their attested sets are subsets of ATTEST-3's.
- ATTEST-5's 3 remaining false attestations are format limits (§8 limit 3): API role brackets (h4-008), a terminal
  agent (h4-056), a named persona (h4-106).

**§4b (product code) on both sets:** H4 restricts 12 of the 32 values only from another speaker, and loses 0 user
facts. ATTEST-4's matcher lost 2, h4-073 and h4-083, which are now INV-S2's literal cells. H3 restricts 5 of 27 and
loses 0. *The backstop's normalisation was fixed after reading those two H4 items, so H4 is the backstop's
regression set, not its holdout.*

Plus:
- the 12-transcript probe re-run on the implementation (expected: labelled formats leak 0/8; unlabelled reported as
  measured, not expected to move);
- an absorption cell: a `use_only` arrival meeting a `mentionable` same-value prior (research: unchecked).

## 7. Failure modes and reversibility

A grammar bug can only restrict (INV-S4): the failure is a user fact stored `use_only` or `not_attested`, visible in
`why()` and counted in `speaker_restricted`. Reversal is a code revert. Rows written under ATTEST-5 keep their
`attv`, which names what produced them. **RII-02 shows the other direction too, within a frozen version:** ATTEST-5
failed OPEN on one composition (a counted letter pair plus a weak name), and rows it wrote from such events keep
`attested`, `mentionable` and `speaker_restricted = 0` (INV-G7: `attv` and `att` are immutable). Re-judging them is the
owner's call, not a fix; `attv = ATTEST-5@0bb7779f` identifies them.

## 8. Claims and limits

Claim: **a statement in a turn the event labels for a non-user speaker — by a listed label, or by an unlisted name
that behaves as a speaker (§4) — is not attested as the user's, and a fact whose value appears only in such turns is
not asserted.** Limits:
1. **Unlabelled transcripts are unchanged**: the measurement's 3/4. The docs half is the only remedy.
2. A paraphrased value found in no turn relies on the prompt rule.
3. **Formats the grammar does not recognise** (H4's 20 unrestricted misses, and H3's):
   - named AI personas with an unlisted user label (Character.ai's "You:" plus a character name), 10;
   - API role brackets (`[system]`/`[user]`/`[assistant]`), 3;
   - support bots with no USER label ("Agent (Priya):", "Bright (virtual assistant):"), 2;
   - Gemini's bare-name lines ("You" / "Gemini" alone), 2 on H4, 5 across H3 and H4;
   - a terminal agent ("> " user lines, "●" agent lines), 1;
   - a Slack bot with no colon, 1;
   - a paraphrase, 1;
   - and labels mid-line.
4. **The episode's wording relies on the prompt rule.** An episode can still say "User is based in Toronto", and
   episodes render on recall: this is the residual leak path after this spec, and the CHANGELOG says so.
5. A forged non-user label restricts the user's text up to the next label that ends a non-user turn (§2c (iii)).
6. **The one-exchange named transcript** ("Claude: …" then the user's name once) restricts the user's line: the safe
   direction, counted by `speaker_restricted`, the host's signal to split.
7. **Sample dialogue or an FAQ INSIDE an assistant reply** ("Customer: …", "User: …", "Q: … A: …") reopens a USER turn
   by a listed label, so those assistant-authored lines read as user text and fail open: 25 of 95,591 LongMemEval
   assistant turns (C1).
8. **Two heading shapes fail open (C2):** a heading in the user's own turn just before the assistant label establishes
   that word for the assistant's own headings; a heading closing one non-user turn right before another non-user label
   hands off. Both are inside C2's 0.12% of real session pairs.
9. **Other people's words (S2):** a value stated only by ANOTHER HUMAN — a group chat, "Mom:", Slack, Zoom, email,
   "Agent Lin:" — is user text by design (unlisted names open USER turns): 17 of H3's 26 negatives whose value comes
   from another speaker. Outside this spec's scope (it concerns assistants), and the larger class.
10. The 12-transcript measurement is dev-written, one run each: not a rate. H4 is ATTEST-5's measured holdout and H5
    is ATTEST-6's.
11. **The backstop's token sequence can split on the user's own wording (H5 h5-048).** The user's "my thesis is on coral
    bleaching" does not hold the value "thesis on coral bleaching" as a sequence, while the bot's line does, so the
    user's fact is written `use_only` (stored, not asserted). This is product code (§4b), changeable without a new
    `attv`; ATTEST-5 hid it by reading the bot's line as the user's.

## 9. Brief for the external reviewer

To be written for R-II, which carries the code (Quentin's ruling).

## 10. Open questions

- **Q1 (Quentin): RULED 2026-10-19:** his acceptance word after research's read; R-II carries the code.
  Research's condition (a fresh holdout before R-II seals) is met by H4 (§6).
- **Q2: ANSWERED (research):** a new predicate version, on two conditions: B2 (the holdout) and F3 (the frozen file,
  both digests bound). The version that ships is ATTEST-6 (v0.4): ATTEST-5 shipped with v0.3.1 and was superseded by
  RII-02; ATTEST-4 was measured and superseded (B3).
- **Q3: ANSWERED (research):** a counter (`speaker_restricted`), not a 0039 degrade event. Nothing degraded, and
  0039's accepted census is closed.
- **Q4: ANSWERED (research):** research could not write the holdout blind after its stage-1 read, so it commissioned
  H3 and H4 (§6).

## Review closure

Internal reads by research (stage 1 `READ-0051-stage1.md` e8ebe9ef; the v0.2 re-read `READ-0051-v0.2.md` 74a20b94;
the v0.3 read `READ-0051-v0.3.md` 1cab911e at research 3bb09e35, and with its addendum 0ec1391f at df3ed744: no objection), and the owner's acceptance word
(ledger `af376b9`). External review: the R-II package carries the code. T = tests/test_0051_speaker_turns.py.

| # | finding | closed by |
|---|---|---|
| B1 | v0.1's "a turn runs to the next listed label" put a user's own `Name:` notes inside non-user turns | §4's one-pass rule; `T::test_inv_s3_a_users_notes_have_no_non_user_turn` (research's five B1 rows) |
| B2 | 0045 §4a: a new version ships only after a FRESH holdout | §6's H4 table (research b3242a94: H4 committed `375089fb`, labels `7c79f29c`, score_h4.py (research repo, 9d1130c8) pre-registered `9d1130c8`) |
| B3 | ATTEST-4's every-label rule: a heading inside an assistant reply ended its turn (24.5% of LongMemEval assistant turns) | ATTEST-5's hand-off rule; `T::test_inv_s6_a_heading_inside_a_reply_stays_in_the_reply`; `T::test_inv_s1_s6_an_assistant_first_person_never_attests_and_is_restricted[B3 note heading]` and `[B3 key line]`; §5's re-measured 0.02% |
| F1 | the `said:`, heading, quote, parenthetical and letter formats were not recognised | `T::test_inv_s1_s6_an_assistant_first_person_never_attests_and_is_restricted` (said-form, heading, quote, parenthetical, letters, emphasis) |
| F2 | substring matching; a one-sided prefix drop; neither side `user` uncovered | `T::test_inv_s2_the_backstop_reads_each_side_through_its_normalisations` (Go, person:Anna, anna_smith, Anna/Acme both ways) |
| F3 | the version must name frozen bytes, both files | `T::test_inv_s5_the_version_names_both_frozen_files`; `tests/test_0045_t9_write.py::test_d6_the_vendored_predicate_is_the_frozen_file_byte_for_byte` |
| F4 | the reach statements understated (§2c (iii); two existing interactions) | §2c (iii); §5's two "existing, stated" rows |
| C1 | sample dialogue inside a reply reopens a user turn | §8 limit 7 (25 of 95,591); `T::test_c1_sample_dialogue_inside_a_reply_is_a_stated_limit` |
| C2 | real session pairs; two heading shapes | §5's real-pairs row (0.12%); §8 limit 8 |
| C3 | the rule stated exactly | the frozen file's docstring; `T::test_inv_s6_c3_the_one_pass_hand_off_rule` (hand-off, established, the one-exchange limit, no reach-back) |
| C4 | H3 is ATTEST-5's regression set, H4 its holdout | §6 |
| S1 | H3 does not exercise the conjunction | §6's sentence |
| S2 | another human's words are user text | §8 limit 9 (17 of 26 on H3) |
| H4-backstop | ATTEST-4's matcher restricted two USER facts (h4-073, h4-083) | the backstop moved to `speaker_backstop.py` with its normalisation fixed; `T::test_inv_s2_the_backstop_reads_each_side_through_its_normalisations[...H4_073...]` and `[...H4_083...]` (the items verbatim) |
| E1 | H4's order stated wrongly | §6's clause, research's wording |
| E2 | the backstop/attestation agreement is a premise | INV-S8; `T::test_inv_s4_s8_restriction_only_and_never_both_restricted_and_attested` |
| RII-02 (external, R-II round 2) | ATTEST-5's weak-name test left out counted `h`/`q` | ATTEST-6 (`ccabb664`); INV-S6's generated 1–4-label gate against the docstring oracle, shown failing on ATTEST-5's bytes (cells: dev to name at adoption); H5 (§6, research 76e34b3f) |
| — | the write path, the counter on every path, an absorption against a mentionable prior | `T::test_the_write_path_restricts_the_assistants_value_and_keeps_the_users`; `T::test_s7_a_label_only_restriction_is_counted_once`; `T::test_s7_the_counter_is_present_and_zero_on_every_other_path`; `T::test_a_restricted_arrival_never_demotes_a_mentionable_prior` |

## Reviewer checklist

- [ ] §3 has no unanswered cells, and is **directional** where the operation is
- [ ] §3's classes were read from the enums, not copied from the template
- [ ] Prohibitions AND the corresponding **permissions** are both tested — a
      guard drawn too broadly passes every prohibition test
- [ ] Every default fails **closed**: an unresolvable input costs assertability
      rather than granting it
- [ ] §2c has a row per uncontrolled input, and **no empty invariant cell** —
      "fails closed" on a predicate the code cannot evaluate is not a control
- [ ] §2c-ii: every claim about what is reachable / exposed / licensed /
      available carries **the command**, not a statement that it was checked
- [ ] §2 consumers were enumerated by grep, not recall
- [ ] Every §6 invariant has a check that actually runs
- [ ] §5 regimes are reachable by tests, or the change is experimental,
      off by default, and §8 says so
- [ ] §3b: no principal can see anything they could not see before (full specs)
- [ ] §6 and §8 are filled in — `n/a — <reason>` counts, blank does not
- [ ] §10 questions each carry a class; unclassified means blocking
- [ ] §8 states what this does *not* establish
- [ ] I have said where I think the **author's conclusion is wrong**, not
      only where the text is wrong
- [ ] I re-read the current version before reviewing, and I am quoting the
      version I approve
- [ ] §9 brief is written, and external review has been sent (or the
      security-hotfix carve-out is recorded)
