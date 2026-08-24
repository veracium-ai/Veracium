# Feature spec: the user's own words are not third-party testimony (L1)

Spec-Status: in review
Spec-Requires: 0005, 0025

> **external round 1, F1 (blocking):** v2 declared independence while its
> §4b rewrite target — `unclassified` — is DEFINED AND PROTECTED by 0025:
> without 0025 the member is not registry-resident, and a host supplying a
> FUNCTIONAL `unclassified` would let the rewritten fact supersede, against
> §4b-i's own never-supersedes outcome. The dependency was real and the
> declaration was wrong, so the declaration moves. One-way: 0024's
> acceptance now waits on 0025's; the IMPLEMENTATION freezes remain
> separate (0024's is a measurement constraint), which the reviewer
> explicitly allows.

*Found by dev during the L1 mechanism audit research commissioned
(`veracium-research/longmemeval/L1-mechanism-audit-dev.md`, 2026-08-17),
measured at $0 over the 2026-08-01 extraction cache. Scheduled by Quentin
2026-08-17. Deliberately SEPARATE from `0025` (L2 — relation-vocabulary
enforcement); see §7b for why sharing a freeze would destroy the
measurement.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v19 — A1 round 23 folded (2026-08-24, §22)**: A1-R23-1 the fence closer accepts SPACES OR TABS ONLY (Python's strip() also removed U+00A0 etc.; the oracle's own vertical-tab cell then caught a second discrepancy — str.splitlines() breaks on \\v/\\f where CommonMark does not, so the parser now splits on true newlines only); PROCESS-R23-1 both new gates hardened against their own prohibited proxies (P1 binds the artifact reference INSIDE the named test's AST body; P4 requires an actual pytest/named-script invocation, refusing $PY -c — the reviewer's planted mutants are in-gate self-tests) and PROCESS.md records the adopted rules; PACKAGE-R23-1 the terminus proposal is an ARCHIVE MEMBER (`specs/evidence/0024/A1-CHECKER-TERMINUS-PROPOSAL.md`) instead of a claimed side-channel companion that never arrived. *Prior:* **v18 — A1 round 22 folded (2026-08-24, §21)**: A1-R22-1 the fence parser accepts arbitrary info strings (backtick-fence info may not itself hold a backtick, per CommonMark) and table rows are limited to at most three leading spaces (four-space indentation renders as code); the reviewer's two mutants PLUS the self-exhausted indent-boundary cells join the matrix (item 9: the shallow-fence failing cell and the dead-fence passing control, written before they could become rounds). PROCESS, adopted this round from the 22-round analysis: the P1 gate (no unmutated checker ships — every evidence artifact binds a named adversarial matrix) and the P4 gate (new closure evidence runs behavior, never grep) are standing; the checker-terminus proposal (produced-not-typed carrier, or accept-with-evidence-maintenance) is the ARCHIVE MEMBER `specs/evidence/0024/A1-CHECKER-TERMINUS-PROPOSAL.md` since v24 (PACKAGE-R23-1: v23 claimed it accompanied the package while it traveled by a side channel that never arrived — a promised companion is a carrier, and it now ships inside the thing that promises it). *Prior:* **v17 — A1 round 21 folded (2026-08-24, §20)**: A1-R21-1 fence removal is a STATE PARSER over the full Markdown fence grammar — backtick OR tilde openers of length ≥3, closed by a same-character marker at least as long (the round-20 regex removed exactly triple-backtick fences; tilde and four-backtick fences still rendered the table as code while passing); the reviewer's two fence-form mutants join the matrix. *Prior:* **v16 — A1 round 20 folded (2026-08-24, §19)**: A1-R20-1 the table parser validates Markdown STRUCTURE and CONTEXT — a candidate block is a table only with a valid two-column delimiter row, and fenced code regions are stripped before locating tables (consecutive pipe lines with an ordinary row where the delimiter belongs, and a fenced code-rendered table, both passed the round-19 parser); the reviewer's two mutants join the matrix. *Prior:* **v15 — A1 round 19 folded (2026-08-24, §18)**: A1-R19-1 the §4b-i check PARSES the question table — exactly one question/answer table, exactly one supersession-question row, the re-dispositioned wording, no obsolete corrected-user-statement row (phrase anchoring proved neither membership nor exclusivity: an isolated pipe line outside the table and a contradictory second row both passed); the reviewer's two mutants join the matrix, and the live row's own R14-1 annotation now DESCRIBES rather than quotes the defect phrasing (the parsed exclusivity check caught the pristine spec's own quotation — the describe-don't-quote corollary, applied by the check's first run). *Prior:* **v14 — A1 round 18 folded (2026-08-24, §17)**: A1-R18-1 the §4b-i check anchors to an ACTUAL Markdown table row with HTML comments STRIPPED before matching (the reviewer's same-section comment-shadow mutant passed the substring form; the line-anchored-inside-comment variant is pre-empted by the strip — the property recursed, not awaited); both shadow mutants join the matrix, whose cells are ENUMERATED never counted (the typed 'five' drifted the day it was written — six were invoked, eight now exist). *Prior:* **v13 — A1 round 17 folded (2026-08-24, §16)**: A1-R17-1 the carrier checker binds §4b-i AT THE SITE (the whole-file search matched the ledger's own quotation of the phrase — the reviewer's ledger-shadow mutant passed; the check now isolates §4b-i and asserts the exact table row), with the requested ADVERSARIAL MUTATION MATRIX shipped as a suite test (pristine + the enumerated mutants incl. the ledger-shadow, each biting — the typed 'five' this entry originally carried was wrong the day it was written, round-18 editorial); EVIDENCE-R17-1 the EVIDENCE-R16-1 closure row points at the WORKING pytest regression instead of the diagnostic string's lexical presence. *Prior:* **v12 — A1 round 16 folded (2026-08-24, §15)**: A1-R16-1 the two consequence-carrier closure rows share ONE named checker (`specs/check_a1_carriers.py` — the R15-1 row's inline grep printed 1 and exited 0, proving none of its claims); EVIDENCE-R16-1 the canary check refuses an absent/non-string/empty subject (the silent '' default admitted exactly what the check rejects — coercion), with the reviewer's deleted-subject and None mutants planted as regressions. Round-16 verdict: NO design issue; U2 approved; the co-owned interface remains confirmed. *Prior:* **v11 — A1 round 15 folded (2026-08-24, §14)**: A1-R15-1 the R14-1 closure evidence checks §9 ITSELF (all three replacement targets, the singular form rejected — the reviewer's restore-§9-alone attack now fails it); PACKAGE-R15-1 the patch verifier constructs a COMPLETE tree, requires the exact zero-skip result, and witnesses that veracium resolved from INSIDE the constructed tree (dev's installed venv had masked the skip — env-leak); EVIDENCE-R15-1 the canary floor is artifact-verified by fresh 2026-08-24 SHIPPED records (the earlier subject re-run persisted nothing — corroborating history, stated as such); plus the reviewer's suggested `validate_baseline.py`, recomputing the summaries and the five movements from the shipped JSONL offline, with a planted-mutation regression per research's §VII condition. Round-15 verdict: the A1 DESIGN IS READY; the co-owned three-passage interface CONFIRMED (survives the return). *Prior:* **v10 — A1 round 14 folded (2026-08-24, §13)**: R14-1 the two surviving consequence carriers fixed (§4b-i's question header asks about a RE-DISPOSITIONED RECORD, not a "corrected user statement"; §9's brief enumerates all THREE `0025` replacements instead of the stale "one-sentence" summary), and the A1-R13-1 closure evidence strengthened to assert both mechanically. Round 14 verdict: U2 semantics SUBSTANTIVELY APPROVED, no new architectural defect; the archive gains `verify_a1_patch.py` (one command: apply the candidate patch to a temp copy, run the patched file's OWN runner — in every seal's extraction checks). *Prior:* **v9 — A1 round 13 folded (2026-08-23, §12)**: A1-R13-1 the consequence-word carrier sweep completed across BOTH specs (five stale assertable/MENTIONABLE passages here; the co-owned `0025` inventory grown to THREE verbatim replacements — §4b-iii steps 1+2 and §7b's row); A1-R13-2 the candidate patch's revoked-vector control moved to A1's USE_ONLY and the EXHAUSTIVE U2 oracle vector added (full author×derived product + revoked; 23 vectors green under the reference file's OWN runner — the round-13 lesson: the pytest wrapper was the wrong verifier); PACKAGE-R13-1 carriers derive status from `Spec-Status:`. *Prior:* **v8 — AMENDMENT A1, in review (2026-08-23)**: the incoherent cell's re-disposition disclosure moves from the author rules to **uniform USE_ONLY** (the standing-revocation floor unchanged). Motivation is MEASURED, not argued: Research's post-implementation probe-paired run (2026-08-23, main @ `1b542b9`, `veracium-research/baselines/0024-conflation/RESULTS_POSTFIX.md`) sized §7's disclosed too-broad door at **4/16 relay probes DE-QUARANTINED vs 1/16 correct restoration** — B06's note literally reads "Claim made by user's boss" while the subject predicate fires, and 2 of the 4 movers carry EMPTY notes, so note-based repair cannot see half the class. The coherence test proves the LABEL self-contradictory; it does not prove the content is the user's own words, so the honest disposition for the ambiguous population is may-inform-never-assert. A1 keeps v7's core (the extractor can no longer demote user testimony below USABLE) and withholds the half the evidence does not support (assertion). U2's oracle becomes UNIFORM; §11 carries the complete delta; the v7 mechanism was implemented, measured, and REVERTED from main (`9257e85`) pending this amendment. *Prior:* **v7** — external round 5 folded (2026-08-21): **R5-1** the THIRD_PARTY-authored incoherent cell's QUARANTINED → USE_ONLY transition RULED INTENDED and stated in §5 (was "unchanged in every cell" — false), U2 upgraded to EXACT OUTPUT over the full product (a floor-only check let two implementations disagree while green), the §3 scope wording fixed (the revoked row is the stated exception). *Prior:* **v6** — external round 4 folded (2026-08-21): **R4-1** the §3 matrix scoped to non-revoked sources with the revocation dimension as its own row (N1 wins over every column) and "author rules ALONE" retired for base-vs-final disclosure language; **PAIR-R4-1** every measured figure is the shipped script's exact output (183,417; note rule 1,644 = 41.7%). *Prior:* **v5** — external round 3 folded (2026-08-21): **R3-1** the combined pipeline gains the standing-revocation floor as an explicit step (`0025` §4b-iii step 3) and §5's "unchanged under 0023" claim corrected — accepted N1 wins over the coherence rewrite, with revoked-source vectors; **R3-2** `Edge.original_relation` defined ONCE at `0025` §2 with both writers enumerated, §5's registry claim and §7a's schema row de-staled. *Prior:* **v4** — external round 2 folded (2026-08-21): **R2-1** the combined pipeline with `0025` stated once (`0025` §4b-iii) — coherence first, disclosure established for the post-coherence state, vocabulary fallback never changes it; **R2-2** §8 narrowed to the recorded-claimant property and §7 states the two doors honestly (a mis-emitted relay with subject="user" is outside every invariant here, bounded by §3b's vacuity argument); **R2-3** §3b/§7a carry the observation surface (result key, MCP strip, CLI, telemetry under the consent contract) and U5's test renamed off the withdrawn note carrier. *Prior:* **v3** — external round 1 folded (2026-08-21): **F1** `Spec-Requires: 0005, 0025` (the independence declaration was the defect); **F2** the coherence predicate made mechanical (§4a: canonical subject shared with the write site, whole-string casefold equality, odd types fail closed; §2c corrected to shipped str() behaviour; U1 restated over the complementary domain); **F3** §6 made the ONE invariant list with U7's count carriers dispositioned; **F4** §8 narrowed to the literal-user-subject cell, prospective only. Original-relation carrier moved to the typed field with `0025` F6. *Prior:* **v2** — internal round 1 folded (research, 2026-08-17). **The ruling this spec asked for is ADJUDICATED: the door OPENS, and the argument is stronger than v1's** — the steered-extractor attack is VACUOUS, not bounded (an ordinary relation already reaches MENTIONABLE), so `third_party_claim` was never a boundary against the extractor; what the fix removes is the model's power to unilaterally DEMOTE user testimony. Also folded: M1 (the §3 matrix sampled the author domain and missed the LIVE `SYSTEM`/no-`derived_from` cell), M3's pair composition, and the symmetric re-disposition count. Invariants renamed **W→U** so the prefix does not collide with `0004`'s. |
| **Status** | *see `Spec-Status:` — canonical.* Draft authorises nothing. |
| **Internal reviewers** | research — round 1 RETURN 2026-08-17 (1 adjudication + 2 moderates + minors), folded here |
| **External review** | required — changes a disclosure decision on the ingest write path |
| **Decision + date** | **ACCEPTED 2026-08-22** — external round 12, on the frozen **U1–U7** invariant surface (package `0024-0025-v12`, sha `5a91e736…`, commit `68555fe`); simultaneous with its pair partner per the round-12 verdict. The `0014` interface-freeze confirmation stands separately. **AMENDMENT A1 IN REVIEW since 2026-08-23** — implementation de-authorised until the amended revision is accepted; the v7 mechanism is reverted from main and `redispositioned` rides at 0 on every carrier |
| **Path** | full |

---

## 1. Problem and motivation

**`_disclosure_for` tests the RELATION before it tests the AUTHOR, so a
record the USER wrote can be quarantined as third-party testimony.**

```python
# src/veracium/ingest.py:96
if relation == QUARANTINE_RELATION:          # "third_party_claim"
    return Disclosure.QUARANTINED            # <-- the author is never consulted
if (author == EvidenceAuthor.THIRD_PARTY
        or derived_from == EvidenceAuthor.THIRD_PARTY):
    return Disclosure.USE_ONLY
return Disclosure.MENTIONABLE
```

The relation is chosen by the LLM extractor. When it mislabels a user's own
statement, the store quarantines content the user said in their own voice,
and every assertable surface then refuses it — *"there are some unverified
third-party claims … but these were never confirmed by you."*

**Measured, not inferred — figures are the SHIPPED script's exact output
(round 4, PAIR-R4-1; `specs/evidence/0025/corpus_counts.py`, cache sha
`654e336a…`).** Over 183,417 cached triples from the 2026-08-01
LongMemEval run:

| measure | count | share of `third_party_claim` |
|---|---|---|
| triples on `third_party_claim` | 3,945 | — |
| … whose own `note` names the USER as the source | **1,644** | **41.7%** — the script's substring rule; the earlier 1,637/41.5% used an unshipped phrase set and is retired |
| … whose `subject` is literally `"user"` | **1,606** | **40.7%** |

The extractor testifies against itself in the note field it wrote:

```
{"relation":"third_party_claim","object":"the original price of Luna's pet bed was $40",
 "note":"price stated by user"}
{"relation":"third_party_claim","object":"The opening act was Whiskey Wanderers",
 "note":"user's observation of the event lineup"}
```

**Why this is a defect and not a design position.** The position this
product holds is *never assert unconfirmed THIRD-PARTY testimony*. It has
never said *treat the user's own words as third-party*. Correcting this is
**provenance accuracy** — it makes the stored trust label match what
actually happened — and it STRENGTHENS the position rather than trading it
away for recall.

**What we do NOT claim, and the bound on the whole spec.** A user can relay
a genuine third-party claim: *"my landlord says I owe $500."* That IS
third-party testimony, the user is merely the courier, and quarantining it
is correct. **The defect is the CONFLATION of "user relays someone else's
assertion" with "user states their own observation" — and A1 concedes,
on measurement, that the §4a predicate CANNOT tell them apart (4 of the
16 relay probes fired it). So the fix's obligation is narrower and
stated honestly: a mechanism that cannot make the distinction must
never GRANT what only the distinction could license. Re-disposition
under A1 lifts the record out of quarantine into
may-inform-never-assert — it never asserts.** §4 turns the label
contradiction into a structural test rather than a matter of extractor
judgement; assertion waits for content evidence (Q5).

**What happens if we do nothing.** The store keeps mislabelling a fraction
of first-person memory as hearsay. The cost is invisible in normal use —
the content is retained, so nothing looks lost — and surfaces only as the
model declining to use things the user plainly told it.

## 2. Field contracts touched

| field | read / written | its documented contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Provenance.disclosure` | written at ONE site (`ingest.py:181`) | `_disclosure_for(author, relation, derived_from)` decides it at ingest and nothing lowers or raises it afterwards | the gate, render, `proactive`, export, `0004`'s wiki rule, `0023`'s quarantine-at-birth | the FUNCTION's decision changes for one contradictory input class; **the single write site does not move and no second writer appears.** `0023` **N2** and `0004` W-series depend on that and are preserved |
| `Edge.quarantined` | derived | `relation == QUARANTINE_RELATION or disclosure == QUARANTINED` (`schema.py:274`) | gate, render partitioning | **UNCHANGED as a formula.** Because it ORs on the relation, a re-dispositioned triple must not keep the relation — see §4's carrier note, which is the whole reason this is not a one-line change |
| `Edge.relation` | written at ingest | the extractor's classification | supersession, absorption, `0025` | a triple that fails §4's coherence test is re-dispositioned, which means its RELATION changes too. Recorded in the typed `Edge.original_relation` field (`0025` F6; one carrier for both specs), never silently discarded |
| `Provenance.author_of_evidence` / `derived_from` | READ | who authored the evidence, and whether its content embeds lower-trust material | the cap (`0005`), the gate | **read EARLIER than today** — that is the entire change |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the extractor's `relation` — **PRODUCER: the LLM, whose output is not constrained today (`0025`)** | absent → the triple is already dropped by the shipped `subject/relation/object` completeness check (`ingest.py:178`) | truthy non-str → NOT dropped: str()-converted by the shipped path (`ingest.py:203`), and the converted oddity is a string outside the registry, which `0025` refuses (same F2 correction as the subject cell: the previous "drop" claim was not what shipped code does) | a relation outside the registry → **out of scope here; `0025` owns it.** This spec changes only the `third_party_claim` cell | an extractor steered into labelling everything `third_party_claim` (a denial-of-assertion attack) | **U1** — the coherence test is structural, so mislabelling in EITHER direction is caught by the same rule |
| the extractor's `subject` on a `third_party_claim` triple | falsy → drop (shipped truthiness check, `ingest.py:201`) | truthy non-str → NOT dropped: str()-converted by the shipped write path (`ingest.py:225`), then misses the §4a predicate → stays QUARANTINED (external round 1, F2: this cell previously claimed a drop the shipped code does not perform) | a claimant name this store has never seen → **QUARANTINES, unchanged.** An unknown claimant is the ordinary case | **the apparent attack: text engineered to make the extractor emit `subject="user"` to ESCAPE quarantine** | **THE ATTACK IS VACUOUS, not merely bounded — see §3b.** A steered extractor never needed the subject: it could emit an ORDINARY relation and reach `MENTIONABLE` directly, today, with no coherence test in sight. **U2** additionally pins the author floor |
| `author_of_evidence` | absent → the model rejects it (required field) | invalid enum → rejected by validation before this code | — | a host declaring THIRD_PARTY content as USER | **out of scope, and stated so:** a host that lies about authorship is outside this spec's threat model and outside the product's (0006 C2 — identity is namespacing, not authentication) |

### 2c-ii. Assertions about reach — REQUIRED

**Every command was RUN in this repository on 2026-08-17 and the result
column records its real output.**

| assertion | command | result (RUN 2026-08-17) |
|---|---|---|
| **`_disclosure_for` tests the relation BEFORE the author** — the defect, in the source | `grep -n "def _disclosure_for" -A 14 src/veracium/ingest.py` | `ingest.py:96` `if relation == QUARANTINE_RELATION: return Disclosure.QUARANTINED`, at line 96, ahead of the author test at `:98` |
| **there is exactly ONE disclosure write site**, so the fix has one home | `grep -rn "_disclosure_for" src/veracium/ --include=*.py` | three hits: the definition (`:88`), a docstring reference (`:113`), and the single call (`:181`) |
| **`quarantined` ORs on the RELATION as well as the disclosure** — so changing the disclosure alone would not change the behaviour | `sed -n '273,280p' src/veracium/schema.py` | `return (self.relation == QUARANTINE_RELATION or self.provenance.disclosure == Disclosure.QUARANTINED)` |
| **the adapter is NOT the defect** — user turns are ingested as USER with no `derived_from` | `sed -n '88,96p'` of `longmemeval/run_longmemeval.py` (the harness in `~/Documents/veracium/proposals/`) | `if role == "user": return EvidenceAuthor.USER, None, "chat"` |
| **the steered-extractor attack is VACUOUS — an ordinary relation already reaches MENTIONABLE** (the executed basis for §3b) | `python -c "from veracium.ingest import _disclosure_for; ..."` over the whole `EvidenceAuthor` domain | `author=user relation=prefers -> mentionable` · `author=system -> mentionable` · `author=third_party -> use_only`. **The extractor could always grant; it never needed the subject slot** |
| **`EvidenceAuthor` has exactly THREE members — there is no `assistant`** (the domain **U2** must span; internal M1 named the row "ASSISTANT", which is a HOST MAPPING onto `SYSTEM`, not an enum member) | `python -c "from veracium.schema import EvidenceAuthor; print([e.value for e in EvidenceAuthor])"` | `['user', 'third_party', 'system']` |
| **the mislabelling is real and its size is known** | a $0 pass over the 2026-08-01 extraction cache | 3,945 `third_party_claim` triples; **41.7%** carry a note naming the user as source (script rule, round 4); **40.7%** have `subject == "user"` — the load-bearing cell, exact |

*(The third row is the one that changed the design: this looked like a
one-line reordering until `Edge.quarantined` turned out to OR on the
relation, which means a re-dispositioned triple has to lose the relation
too. A fix that only reordered `_disclosure_for` would have passed review
and changed nothing observable.)*

## 3. Trust-class matrix — REQUIRED, blocking

**Scope (round 4 R4-1; wording fixed round 5 R5-1): the FIRST row below
is the revoked-source result; every OTHER row states the result for a
NON-REVOKED standing source.** The rows are BASE authorship
disclosure — step 2 of `0025` §4b-iii — and the accepted floors then run on
the result; v5's rows read as unconditional finals, which was false the
moment `0023` N1 applied. The revocation dimension collapses to one row
because the floor ignores every column:

| author | `derived_from` | relation | subject | disclosure TODAY | disclosure AFTER | why |
|---|---|---|---|---|---|---|
| **any** | **any** | **any** | **any** — source standing-REVOKED | QUARANTINED | **QUARANTINED** | accepted `0023` **N1**: the standing-revocation floor is evaluated independently of relation, subject and author, and it WINS over the coherence re-disposition — `reference_enforcement.vector_revoked_source_floor_wins_over_coherence` pins the revoked USER-authored `third_party_claim` cell the reviewer named |
| USER | — | ordinary | anything | MENTIONABLE | MENTIONABLE | unchanged |
| USER | — | `third_party_claim` | **a claimant** | QUARANTINED | **QUARANTINED** | the user is the courier; the claim is still hearsay. **Unchanged, and this is the case the fix must not break** |
| USER | — | `third_party_claim` | **the user** | QUARANTINED | **USE_ONLY**, relation re-dispositioned | **the contradiction.** A third-party claim whose claimant is the user is not a third-party claim — but the collapse of the label does not prove the content is the user's own words (A1: 4 of 16 measured movers were genuine relays), so the record informs and never asserts |
| USER | THIRD_PARTY | `third_party_claim` | the user | QUARANTINED | **USE_ONLY** | the author floor still applies — the content embeds lower-trust material, so it never reaches MENTIONABLE |
| THIRD_PARTY | any | `third_party_claim` | the user | QUARANTINED | **USE_ONLY** | **the attack cell.** Steering `subject` buys `USE_ONLY`, never MENTIONABLE — exactly what an ordinary third-party inference gets |
| SYSTEM | THIRD_PARTY | `third_party_claim` | the user | QUARANTINED | **USE_ONLY** | `0005`'s three-lever cap logic, unchanged |
| **SYSTEM** | **none** | `third_party_claim` | the user | QUARANTINED | **USE_ONLY** | **the cell v1 omitted (internal M1) — and it is LIVE.** See the enumeration below; A1 makes it uniform with every other incoherent cell |
| any | any | ordinary | the user | per author | per author | unchanged |

**The full author domain, enumerated rather than sampled (internal M1).**
`EvidenceAuthor` has exactly THREE members — `user`, `third_party`,
`system` (executed, §2c-ii). **There is no `assistant` author**: an
assistant turn is a HOST MAPPING onto `SYSTEM`, with `derived_from` set or
not according to the host's trust arm. So the domain of the incoherent cell
is `author × derived_from` = 3 × 4 (three members plus absent), and under
A1 every non-revoked cell gets the SAME disposition — the oracle is
uniform, which removes entirely the two-implementations-disagree room
round 5 (R5-1) had to legislate against:

| author | `derived_from` | result after re-disposition (A1) | live in the re-run? |
|---|---|---|---|
| USER | none | USE_ONLY | yes |
| USER | THIRD_PARTY | USE_ONLY | yes |
| USER | USER / SYSTEM | USE_ONLY | rare, legal |
| **SYSTEM** | **none** | **USE_ONLY** | **YES — this is an assistant turn under a trusting host arm** |
| SYSTEM | THIRD_PARTY | USE_ONLY | yes — the capped assistant arm |
| SYSTEM | USER / SYSTEM | USE_ONLY | rare, legal |
| THIRD_PARTY | any | USE_ONLY | yes |

**The SYSTEM/none cell is not an oversight to be closed; it is the host's
declared trust arm doing what it says** — and under A1 even that trusted
arm's incoherent triple stops at USE_ONLY, because the ambiguity A1
measured is in the EXTRACTOR's slot-filling, which the host's trust
declaration says nothing about. **What v1 got wrong was not the outcome,
it was enumerating a domain by example.** **U2** now spans the whole
product with a uniform expected value.

**Nothing in this table rises above USE_ONLY (A1).** Re-disposition
grants may-inform-never-assert and nothing more: the label's collapse is
evidence the CLASSIFICATION was wrong, not evidence the content is the
user's own testimony — the measured population behind that sentence is
4 genuine relays per 1 genuine self-statement. Assertion for this cell
requires evidence about the CONTENT (Q5; the #107 agreement check),
which this spec does not have and no longer pretends to.

## 3b. Authorization and scope

- **Caller-facing surface, complete (external round 2, R2-3: v3 said "no
  new surface" while U7 added three).** No new API, flag or config; the
  rule is inside `_disclosure_for`, which no host can reach. But the
  OBSERVATION surface grows: the ingest result dict gains
  `redispositioned` (through `Memory.remember`, unchanged), the CLI prints
  it, telemetry gains the field, and the MCP surface STRIPS it. The
  telemetry field is governed by the accepted telemetry contract — added
  to the event-field whitelist with a minimum schema version, named in the
  consent text (version bumped), and covered by consent AND no-consent
  tests; absent consent the field is never emitted.
- **Per record, at write time.** Nothing existing is rewritten (§7).
- **Does anything become visible to a principal who could not see it
  before?** **Yes — a quarantined record becomes USABLE (A1: USE_ONLY —
  it may inform answers and is never asserted) — and v1 described the
  then-assertable form as a BOUNDED DOOR. It is not a door at all, and
  the stronger argument is now stated here rather than left for the
  external reviewer to find (internal round 1).**

  **The attack cell is VACUOUS.** v1 worried about an extractor steered into
  emitting `subject="user"` to escape quarantine. But the extractor chooses
  the RELATION too, and it always could: a steered extractor emits an
  ORDINARY relation — `prefers`, `works_as`, anything — and reaches
  `MENTIONABLE` directly, **today, with no coherence test involved**.
  Executed (§2c-ii): `_disclosure_for(USER, "prefers", None) → mentionable`.

  **`third_party_claim` was never a security boundary against the extractor.
  It IS the extractor's output.** A defence cannot be built out of the thing
  it is defending against.

  So compare the two powers honestly. After this change the extractor's
  power to GRANT is **exactly what it was** — total over its own labels,
  floored by the author. What changes is its power to unilaterally **DEMOTE**
  the user's own testimony, which this spec takes away.

  **That is why this is not an un-cap.** An un-cap raises a record above
  what the TRUSTED inputs license. Here the trusted inputs —
  `author_of_evidence` and `derived_from`, host-supplied, neither chosen
  by the model — would license `MENTIONABLE`, and the UNTRUSTED input
  demoted it. **A1 deliberately restores LESS than the trusted inputs
  license: USE_ONLY, because the untrusted input's slot-filling is also
  what made the population ambiguous (4 relays per 1 self-statement,
  measured) — the rule un-does the demotion's assertion-lockout without
  granting assertion.** `0005`'s C1 forbids granting past a floor; A1
  grants nothing at all above use, and **U2** pins the uniform value over
  the full author domain.
- Under `0020`, scoped principals see no more than the policy already allows.
- **Existing records are NOT re-dispositioned** (§7). This is a write-time
  rule; a retroactive sweep is `Q1`.

## 4. Behaviour

### 4a. The coherence test

A triple is **incoherent** when `relation == QUARANTINE_RELATION` and the
**canonical subject** is exactly the user. Both halves are mechanical
(external round 1, F2 — "denotes the user themself" named an intent, not a
computation):

- **Canonical subject** = `str(t["subject"]).strip()` — the SAME conversion
  the shipped write path applies (`ingest.py:225`), computed ONCE and used
  for both the test and the stored field, so the test can never disagree
  with the subject the Edge actually carries.
- **The predicate** = `canonical_subject.casefold() == "user"`. Whole-string
  equality after casefold; nothing else — no substring match, no synonym
  list, no note inspection.
- **Odd types fail closed.** The shipped completeness check (`ingest.py:201`)
  drops only FALSY subjects; a truthy non-string — `["user"]`,
  `{"name": "user"}`, `1` — survives it and is str()-converted.
  `str(["user"])` is `"['user']"`, which is not `"user"`, so every such
  triple misses the predicate and stays QUARANTINED. A subject must arrive
  as the literal string to be recognized; type games buy nothing.

The extraction prompt states the
claimant convention explicitly — *"Emit those ONLY as `{"relation":
"third_party_claim", "subject": "<claimant>", ...}"`* (`prompts.py:38`) — so
the subject slot of a third-party claim IS the claimant, and a claim whose
claimant is the user is a contradiction in the extractor's own terms.

**The test is on the SUBJECT, not on the note.** The note is free text and
was the strongest measured signal (41.7%), but it is prose an LLM wrote and
nothing constrains it. The subject is a structural slot with a stated
meaning. **We test the thing with a contract, not the thing with the
higher hit rate** — and we accept a smaller catch as the price.

### 4b. What an incoherent triple becomes

The triple is **re-dispositioned, not dropped**:

1. its `relation` becomes **`unclassified`** — the reserved, registry-resident,
   NON-FUNCTIONAL member `0025` §4b defines and injects into every effective
   registry. It is an ORDINARY relation (never `third_party_claim`, because
   `Edge.quarantined` ORs on the relation — §2c-ii row 3), and naming it here
   rather than "some fallback" is what makes the pair compose (§7b);
2. its disclosure is **USE_ONLY — may inform, never assert
   (AMENDMENT A1)** — **as the BASE disclosure: step 2 of the combined
   pipeline `0025` §4b-iii, after which the accepted floors (step 3 —
   standing revocation among them) may only LOWER it to the FINAL
   result.** v7 said "the author rules", and the paired measurement
   showed why that granted too much: the coherence test proves the label
   self-contradictory, not that the content is the user's own words —
   4 of 16 quarantined relay probes were genuine relays filed with
   `subject="user"`, and under the author rules they became assertable
   user facts. USE_ONLY keeps what the evidence supports: the extractor
   cannot demote user testimony below USABLE, and cannot be tricked (or
   merely confused) into promoting a relay to assertion. (Round 2's
   R2-1 note stands — `0025` X10 is scoped to the vocabulary fallback
   and does not constrain this step; round 4's base-vs-final language is
   unchanged, only the base VALUE moved.);
3. **the original relation is preserved in the TYPED field
   `Edge.original_relation`** — defined ONCE at `0025` §2 as the original
   relation for ANY structural re-disposition, this rewrite being one of
   its two enumerated writers (round 3, R3-2: the two specs had drifted
   into two definitions) — so the re-disposition is visible in the record
   and reversible by inspection. Nothing is silently rewritten.

**Order matters, and A1 narrows what is at stake in it:** no incoherent
path reaches `MENTIONABLE` at all — the uniform USE_ONLY disposition and
the floors below it can only lower further, so THIRD_PARTY-authored or
-derived content lands at USE_ONLY by two independent routes.

**The count is symmetric.** v1 required the original relation to survive in
the note but did not require the re-dispositions to be COUNTED — while
`0025` **X4** insists an invisible residual is how 34.9% went unnoticed.
The same principle applies to this spec's own rewrites: the ingest result
carries a re-disposition count (**U7**). A rule that silently rewrites
extractor output is the shape this project keeps finding.

#### 4b-i. What happens when BOTH specs land — the composition, chosen not inherited (internal M3)

| question | answer |
|---|---|
| is the fallback relation registry-resident? | **yes** — `unclassified` is `0025`'s reserved member, injected structurally into every registry, so this spec's rewrite cannot violate `0025` **X1** |
| which rule runs first? | **the coherence test (this spec), then vocabulary enforcement (`0025`).** `third_party_claim` is IN the registry, so enforcement would pass it through untouched; the coherence test is the only rule that can see the contradiction |
| **is a re-dispositioned record then able to SUPERSEDE?** *(R14-1: the old question header classified the content as the user's own corrected statement, which the answer itself says the mechanism cannot establish; the defect phrasing is described, not quoted, so the parsed exclusivity check can grep for it — R19-1)* | **NO — and this is a CHOSEN cell, not an accident.** `unclassified` is non-functional and A1 caps the disclosure, so a re-dispositioned triple becomes USABLE — never assertable, never superseding. **Half-restoration is the honest outcome — and A1 applies the same argument to DISCLOSURE**: the coherence test establishes that the extractor's TRUST label was self-contradictory; it establishes nothing about which RELATION the fact belonged under, and (measured) nothing about whether the content is the user's own words. Guessing a functional relation in order to complete the restoration would file a fact under semantics nobody derived, and a wrong guess retires an unrelated record — `0025` §4b refuses exactly that trade for the same reason |
| could a future spec complete it? | yes, and it would need evidence about the relation, not about the author. Recorded as **Q4** |

### 4c. What is deliberately NOT done

- **No retroactive sweep.** Existing quarantined records keep their
  disclosure. Re-dispositioning stored records means a SECOND disclosure
  writer, which breaks the single-write-site property `0004` and `0023`
  both reason from. `Q1` holds the question.
- **No prompt-only fix.** Tightening the extraction prompt is worth doing
  and is not a spec: a prompt is not enforcement, and this defect survived
  a prompt that already states the claimant convention.
- **No note-based heuristics.** See §4a.

## 5. Regime analysis — where does this behave differently?

| regime | behaviour |
|---|---|
| a store with no `third_party_claim` triples | **byte-identical.** The new branch is unreachable; **U4** pins it |
| ordinary assistant/user chat ingest | changes only for triples the extractor labels `third_party_claim` with `subject == user` |
| a THIRD_PARTY-authored event (mail, documents) | **CHANGED for exactly the incoherent subset, and INTENDED — under A1 the uniform disposition and the author floor COINCIDE in this cell, so the v7 ruling's outcome is unchanged here (external round 5, R5-1, blocking: v6 said "unchanged in every cell" while the §3 matrix and the reference both move the incoherent cell QUARANTINED → USE_ONLY — structural isolation to may-inform-never-assert).** The ruling: a third-party-authored triple whose self-contradictory label collapses gets exactly what an ordinary third-party statement gets — USE_ONLY, the author floor — no more, and §3b's vacuity bound shows the extractor could already reach that via an ordinary relation. Every COHERENT third-party cell is untouched |
| import (`0005`) | **unchanged.** The cap runs on already-written records; this is a write-time rule at ingest |
| a store under `0023` revocation | **the standing-revocation floor applies AFTER the coherence rewrite and wins (external round 3, R3-1, blocking: v4 said "unchanged" while the §4b pipeline as written let a revoked source's incoherent triple out at MENTIONABLE, against accepted N1).** A revoked source's records land QUARANTINED whatever the coherence test decides — step 3 of `0025` §4b-iii, and the revoked-source vectors pin it |
| a host supplying its own `relations` registry | unchanged in effect — and stated correctly now (round 3, R3-2): `QUARANTINE_RELATION` is a module constant AND a protected effective-registry resident under `0025` §4b-ii; a host cannot remove or conflictingly redefine it |

## 6. Invariants and executable checks — REQUIRED, blocking

| # | invariant | check |
|---|---|---|
| **U1** | a `third_party_claim` whose canonical subject (§4a: str → strip → casefold) is anything OTHER than the exact string `user` — a named claimant, a str()-converted list or dict, an empty-after-strip string — quarantines, whatever the author. The complementary domain, so no cell is left to interpretation (external round 1, F2) | `test_relayed_third_party_claim_still_quarantines` |
| **U2** | the §3 matrix is EXACT OUTPUT over the FULL `author × derived_from` product (3 × 4, internal M1) — every cell's disclosure equals the matrix's stated value, revoked and non-revoked; not merely a floor (round 5, R5-1). **A1 REVISES THIS FROZEN ROW — the one U-surface change the amendment asks for**: the oracle becomes UNIFORM — standing-revoked → QUARANTINED, every other incoherent cell → USE_ONLY — which is strictly simpler than v7's author-rules oracle and leaves no cell where two green implementations can disagree | `test_author_floor_spans_the_author_domain` — enumerates the entire product against a separately-written EXACT oracle; under A1 the oracle is the two-branch constant above |
| **U3** | a re-dispositioned triple does not keep `QUARANTINE_RELATION`, so `Edge.quarantined` reports false | `test_redispositioned_triple_is_not_quarantined_by_relation` — the check that would have failed on a fix that only reordered `_disclosure_for` |
| **U4** | a store whose extractor never emits `third_party_claim` is byte-identical before and after | `test_no_quarantine_relation_is_byte_identical` |
| **U5** | the original relation survives in the record, in the typed `Edge.original_relation` field | `test_redisposition_carries_the_original_relation` — renamed round 2 (R2-3): the old name promised the note, a carrier round 1 withdrew |
| **U6** | disclosure still has exactly ONE write site | `test_single_disclosure_write_site` — the AST sweep `0023` **N2** already specifies, extended to cover this change rather than duplicated |
| **U7** | re-dispositions are COUNTED and returned, never silent — the symmetric form of `0025` **X4** applied to this spec's own rewrites. **The COUNT'S CARRIERS, enumerated (round 1, F3):** the ingest result dict gains `redispositioned` (present on EVERY path, 0 on the unparseable and no-hit paths — an absent key is not a zero); `Memory.remember` passes the dict through unchanged; the MCP surface STRIPS it (consistent with its existing removal of the supersession/reinforcement counts — operator counts are a library surface, not a tool-call surface); telemetry gains the field beside the existing ingest counts. **Carrier ownership: `0025` §4c is the single authoritative disposition for the pair's counters; this row applies it to `redispositioned`, not restates it (round 2, R2-5)** | `test_redisposition_count_is_reported` — asserts the key on all three paths, including both zeros |

## 7. Failure modes and reversibility

- **If the coherence test is too narrow** (subject-based, ~40.7% of the
  mislabelled population): the residual stays quarantined, which is
  today's behaviour. **Failing narrow costs recall, never assertion.**
- **If it were too broad** — the case to fear, and A1's reason to
  exist: under v7 a genuine relayed claim became ASSERTABLE, and the
  paired measurement found the door is not an edge case on live
  extraction — 4/16 relay probes moved (boss/accountant/professor/
  trainer, all with extracted `subject == "user"`), against 1/16
  correctly restored. Under A1 the same door costs at most
  MAY-INFORM: the structural never-assert floor holds for the whole
  ambiguous population. Two distinct doors, stated honestly (external
  round 2, R2-2): a RULE that widened (a non-user claimant slipping the
  predicate) is what **U1** catches, and the §3 matrix is enumerated rather
  than sampled. But an EXTRACTOR that mis-emits a genuine relay with
  `subject="user"` lands inside the first-person exception and NO invariant
  here catches it — the rule reads what is recorded, not what was said.
  That residual is bounded by the same fact §3b establishes: the extractor
  could already grant assertability through an ordinary relation, so the
  exception adds no power it lacked.
- **Reversibility:** the rule is write-time, so reverting the code reverts
  the behaviour for all future writes. Records written under it keep the
  disclosure they were written with, which is the same asymmetry `0023`
  §4i declares — stated here rather than discovered.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `src/veracium/ingest.py` | `_disclosure_for` gains the coherence test; the call site and the write site do not move |
| `src/veracium/schema.py` | the FIXED re-disposition target `unclassified` (`0025`'s reserved member — never conditional, round 3 R3-2 removed the stale "if the registry has no suitable member" phrasing) and the shared `Edge.original_relation` typed field, defined once at `0025` §2 with its two writers enumerated |
| `src/veracium/prompts.py` | **optional and non-normative**: tightening the claimant convention. Explicitly NOT the fix (§4c) |
| the ingest result dict / `Memory.remember` / MCP / CLI / telemetry | `redispositioned` on every path / passthrough / STRIPPED / printed / whitelisted field under the telemetry contract with consent gating (round 2, R2-3 — these carriers were governed by U7 but absent from this inventory) |
| tests | the §6 table's named tests, U1–U7 — §6 is the ONE authoritative invariant list (external round 1, F3: this row said W1–W6, §6 listed U1–U7 out of order, and the package header hand-typed a range ending one past the real list — three versions of one surface; every other carrier now REFERENCES §6 rather than restating it) |
| docs / CHANGELOG | a behaviour-change entry: some records that were quarantined are now USABLE-NOT-ASSERTABLE (A1 — may inform answers, never asserted as fact), with the matrix |

### 7b. Cross-spec carriers

| spec | touchpoint | disposition |
|---|---|---|
| **`0025`** | the relation vocabulary | **ORTHOGONAL, AND MUST NOT SHARE A FREEZE.** `third_party_claim` is IN the 19-relation registry, so `0025`'s enforcement does not touch this mislabelling, and this spec does not reduce the off-vocabulary population. They are independent mechanisms, and — the operative reason — **a shared freeze makes the measured movement unattributable between them** |
| **`0005`** | the import cap | CONSUMED unchanged. The cap floors imported records to `USE_ONLY`/`QUARANTINED` after this rule has already run at their origin store |
| **`0004`** | the wiki drop | **nothing to add.** This spec does not invalidate; it changes what a new record may assert |
| **`0023`** | quarantine-at-birth and **N2**'s single-writer AST pin | this spec keeps the single write site, which **N2** requires. If both land, **N2**'s sweep covers this change too — one pin, not two |
| **`0020`** | scoped read | unchanged; policy decides visibility, this decides assertability |
| **`0025` co-owned text — THREE passages AMENDED BY A1, verbatim, the `0014` precedent: carried here and folded into `0025` only on acceptance (round 13, A1-R13-1 completed this inventory)** | `0025` §4b-iii step 1; §4b-iii step 2; §7b's `0024` row | REPLACEMENT 1 (§4b-iii step 1, the "becomes the user's own statement" clause): *"1. **Coherence (`0024` §4a/§4b).** An incoherent `third_party_claim` is re-dispositioned; this DELIBERATELY changes the semantic state — the record stops being RELIABLY CLASSIFIED as hearsay. The label's self-contradiction licenses use; it is NOT a finding that the content is the user's own statement (`0024` A1, measured)."* REPLACEMENT 2 (§4b-iii step 2): *"2. **Disclosure is established** for the post-coherence semantic state — **USE_ONLY for a re-dispositioned triple (`0024` §4b as amended by A1: the label's collapse licenses use, not assertion)**, the relation-then-author rules otherwise. It is computed once and RETAINED."* REPLACEMENT 3 (`0025` §7b, the `0024` row's consequence clause "A corrected user statement therefore becomes assertable but NON-SUPERSEDING"): *"A re-dispositioned record is therefore USABLE — never assertable, never superseding (`0024` A1) — which `0024` §4b-i adopts as a chosen cell rather than inheriting as an accident."* Steps 3 and 4 of §4b-iii are byte-unchanged |

## 8. Claims and limits

**What we will say:**

> **Provenance accuracy, in the cell the rule recognizes (A1 form).** A
> statement recorded with YOU as the literal claimant is no longer locked
> out of memory by an extractor mislabel — it can inform answers. It is
> NOT asserted as fact: the measured population behind that label is 4
> genuine relays per 1 genuine self-statement, so assertion waits for
> evidence about the content, not the label. A claim recorded with a
> NON-USER claimant remains an unverified third-party claim, quarantined.

*(External round 2, R2-2: the earlier sentence promised relayed content "is
never asserted as fact" — but a genuine relay the extractor mis-emits with
`subject="user"` falls INSIDE the deliberate first-person exception and,
under the v7 disposition this annotation was written against, could
become MENTIONABLE — the risk the A1 measurement then CONFIRMED at 4/16
and the reason the cell is now capped at USE_ONLY. U1 protects non-user
claimants only and cannot catch that error. The guarantee is structural, about what is RECORDED, not about
what was originally said; §7 states the residual risk honestly.)*
>
> *(External round 1, F4: the earlier absolute form — "a statement in your
> own voice is recorded as yours" — exceeded the rule. The mechanism
> corrects the literal-user-subject cell, ~40.7% of the measured mislabel
> population, PROSPECTIVELY; a user observation the extractor emits under
> another claimant string stays quarantined, and this section may not imply
> otherwise.)*

**What this does NOT establish.**

- **It is not a recall improvement, and must not be sold as one.** Any
  benchmark movement is a byproduct of storing the right trust label. If
  the labels were already right, the score would be unchanged.
- **It does not catch every mislabelling.** The subject test addresses the
  40.7% with `subject == "user"`. The remainder — mislabelled with a
  plausible claimant, or the note-only signal — stays quarantined. **The
  residual is the honest cost of testing a structural slot instead of
  prose.**
- **It is not extractor correctness.** The extractor still mislabels; this
  refuses to act on one class of self-contradictory output. `0025` and the
  prompt are different levers.
- **It does not authenticate authorship.** A host that declares
  third-party content USER-authored is outside the threat model (`0006` C2).

## 9. Brief for the external reviewer

**A1 AMENDMENT BRIEF (v8, 2026-08-23) — the narrow question this round
asks.** The frozen surface changes in exactly ONE place: U2's expected
output for the incoherent cell moves from the author rules to uniform
USE_ONLY (revoked floor unchanged). Everything else — the §4a predicate,
U1/U3–U7, the counter, the single write site, the composition with
`0025` — is byte-level or semantically unchanged, plus the co-owned
co-owned `0025` replacement inventory carried verbatim in §7b — THREE
passages: §4b-iii step 1, §4b-iii step 2, and §7b's `0024` row (R14-1:
this brief previously summarised the inventory as a single step-2
replacement after round 13 had grown it to three — a maintainer
following the brief would have re-performed the incomplete fold; the
defect phrasing is described, not quoted, so the closure sweep can
grep for it).
The motivation is a measurement, not an argument: your round-2 concern
("correction is a door… the same shape as an un-cap") was measured live
after acceptance, and the door moved 4 genuine relays per 1 genuine
self-statement (Research's probe-paired run, main @ `1b542b9`; the v7
mechanism is since reverted). A1 is the disposition that survives that
number: the extractor still cannot demote user testimony below usable,
and can no longer promote a relay to assertion — restrict-only is
restored (`0005` C1: no grant of assertability remains anywhere in the
rule). What we most want attacked: whether USE_ONLY for the USER/none
cell UNDERSHOOTS — a real first-person statement now informs rather than
asserts, and the completion path (Q5, the #107 label/value agreement
check) is deliberately out of this amendment's scope.

*(The original acceptance-round brief follows, unchanged, for the
record.)*

**The constructions are executable (round-1 package feedback):**
`specs/evidence/0025/reference_enforcement.py` is a dependency-free
reference of the v3 constructions — the §4b-ii registry order, the §4b(1)
retry with its matching and no-op rules, X10's disclosure ordering (the
laundering cell runs the WRONG order on purpose and shows the bite),
X11's snapshot, and `0024`'s §4a predicate with its fail-closed odd-type
cells, and (round 2) the shipped-default-registry, duplicate-pair,
snapshot-through-mutation, byte-identity and combined-pipeline vectors.
The vector list is the file itself — no count here to drift; the
implementation will be differentially tested
against it, the `0022` vector-harness discipline.

**What we are least sure of:**

1. **The subject test's coverage.** We chose the structural slot (40.7%)
   over the note text (41.7%) because the note has no contract. If you
   think prose with a measurably higher hit rate is the better instrument,
   argue it — we think a signal nothing constrains is not enforcement, but
   we are trading measured coverage for that principle.
2. **The one cell that RAISES a disclosure.** Everything else in this
   codebase is restrict-only, and `0005` C1 forbids grants. We argue this
   is not a grant but a CORRECTION of a mislabel, and we bound it with the
   author floor. **If you think "correction" is a door that should not be
   opened at all, that is the finding we want** — it is the same shape as
   an un-cap, and we have been suspicious of un-caps everywhere else.
3. **Where the boundary between relay and observation actually sits.**
   "My landlord says I owe $500" is a relay. "The opening act was Whiskey
   Wanderers" is an observation. Both are things the user typed about the
   external world. We claim the claimant slot separates them; attack that.

**Where we suspect we have overstated:** "provenance accuracy" is a
generous framing for a rule that catches one contradiction shape. It is
accurate for the cell it covers and silent about the rest.

## 10. Open questions

| # | question | state |
|---|---|---|
| **Q1** | should existing quarantined records be re-dispositioned retroactively? | `deferred` — it needs a SECOND disclosure writer, which breaks the single-write-site property `0004` and `0023` reason from. The same asymmetry `0023` §4i declares, for the same reason |
| **Q2** | should the note signal be used as a SECOND, weaker test — flagging rather than re-dispositioning? | **RESOLVED 2026-08-22 (Quentin): NO for v1** — a flag nobody consumes is a field, not a mechanism. The note-as-agreement-evidence idea lives on in the queued label/value agreement check (dev task #107), which is its proper generalisation |
| **Q4** | should a re-dispositioned triple ever recover a FUNCTIONAL relation, completing the restoration? | `post-v1` — it would need evidence about the RELATION, which this spec does not have and does not claim. Partial restoration (under A1: usable-not-assertable, never superseding) is §4b-i's chosen cell |
| **Q5** | should a re-dispositioned triple ever become ASSERTABLE, completing the disclosure half? | **opened by A1 (2026-08-23)** — it needs evidence about the CONTENT (is this the user's own statement, or an embedded relay?), which the subject slot cannot supply: 4 of the 16 measured movers were genuine relays and 2 of those 4 carry EMPTY notes. The #107 label/value agreement check is the candidate instrument; nothing in A1 forecloses it |
| **Q3** | should a `third_party_claim` with an EMPTY subject be treated as incoherent too? | **RESOLVED 2026-08-22 (Quentin, on the reachability check this row asked for): NO.** Measured on the live ingest: a LITERAL empty subject is dropped by the shipped completeness check (unreachable); a WHITESPACE subject survives, strips to an empty claimant, and stays QUARANTINED. An absent claimant is no evidence the user is the claimant — the conservative floor holds. Both cells pinned executable: `test_q3_empty_subject_cells_ruled_and_pinned` |

## 11. Amendment A1 (v8, 2026-08-23) — the complete delta

**One sentence:** the incoherent cell's re-disposition disclosure moves
from the author rules to **uniform USE_ONLY**; nothing else moves.

**Why a measurement forced this.** The v7 mechanism was implemented on
main (`1b542b9`, all U1–U7 green) and Research ran the frozen 48-probe
paired baseline against it same-day (`veracium-research/baselines/
0024-conflation/RESULTS_POSTFIX.md`, corrections note `f8d5a0a0` —
and since v10 the evidentiary chain ships DIGEST-BOUND in this
archive at `specs/evidence/0024/baseline/`: expectations committed
before any run (research repo `261c0b95`), both halves of the paired
records, the frozen 48-probe matrix, the harness, the 2026-08-24
canary-subject records (EVIDENCE-R15-1: the earlier subject re-run
persisted nothing and is corroborating history only — the shipped
records are the artifact verification), and `validate_baseline.py`,
which recomputes the summaries and the five movements from the shipped
JSONL offline; PROVENANCE.md states the chain, the figure-correction
`6f548f09`, and the canary chain `fd3a6170`):

- cell A (must move): moved exactly as specified — A08 restored with
  `original_relation` preserved. **1/16 of the probe set — cell A's
  entire quarantined membership (1 of 1)**;
- cell B (must not move): **4/16 genuine relays de-quarantined to
  MENTIONABLE** — boss/accountant/professor/trainer, every one a real
  relay the extractor filed with `subject == "user"` (witnessed by the
  re-disposition marker: all four carry `original_relation =
  'third_party_claim'` + `relation = 'unclassified'`, which the
  mechanism produces only when the canonical-subject predicate fired —
  the instrument did not sample subjects directly, disclosed). B06's note reads
  "Claim made by user's boss" while the subject predicate fires; 2 of
  the 4 movers carry EMPTY notes (note-based repair is half-blind);
- relay floor on the probe set: 14/16 → 10/16; blast radius assertion +
  wiki + consolidation (NOT supersession — `unclassified` never
  supersedes); canaries held by subject domain (U1), U2 unchallenged.

Quentin ruled (2026-08-23): hold v7's mechanism out of the release
(reverted, `9257e85`), amend to USE_ONLY as the destination. This
section is that amendment.

**The delta, enumerated. (Round 13, A1-R13-1: the first version of
this table said "every carrier" while five normative passages — §1's
"is not a fix", §3b's assertable/license-MENTIONABLE claims, §4b-i's
"becomes assertable", §8's historical annotation, and two further
`0025` passages — still described the v7 outcome. The claim of
completeness was itself the finding; this revision swept the
CONSEQUENCE words — "assertable", "user's own statement" — across BOTH
specs, not just the cells the disposition value lives in.)**

| carrier | change |
|---|---|
| §3 matrix + enumeration | every non-revoked incoherent cell → USE_ONLY (uniform); the revoked row unchanged |
| §4b item 2 | disposition = USE_ONLY as the step-2 BASE; floors may only lower |
| **U2 (the ONE frozen-surface change)** | exact oracle becomes the two-branch constant: revoked → QUARANTINED, else USE_ONLY |
| U1, U3–U7 | **unchanged** — the predicate, the re-dispositioned relation, the typed original, byte-identity, the single write site, the counter all stand |
| `0025` §4b-iii steps 1+2 AND §7b's `0024` row (co-owned) | THREE replacements, VERBATIM in §7b below (round 13, A1-R13-1: the first inventory carried only step 2 while step 1 still said the record "becomes the user's own statement" and `0025` §7b still said a "corrected user statement… becomes assertable" — exactly the claims the measurement rejects) |
| `specs/evidence/0025/reference_enforcement.py` | amended EXECUTABLY by the INERT candidate patch `specs/evidence/0024/a1-reference.patch` (applies clean; the vector suite runs green with it applied — verified — and the file itself is untouched until acceptance) |
| implementation (on re-acceptance) | the reverted `1b542b9` mechanism returns with one line changed: the re-dispositioned branch establishes `Disclosure.USE_ONLY` instead of calling the author rules; U6's single-establishment AST pin still holds |
| release gating | Research re-runs the paired baseline against the amended implementation before it ships (their standing same-day commitment) |

**What A1 deliberately does not do:** no retroactive sweep (Q1 stands);
no note heuristics (§4a stands); no assertion path — that is **Q5**,
opened by this amendment and pointed at the #107 label/value agreement
check, which owns the content-evidence question.

## Review closure

*(PROCESS §4a — one row per review finding, with evidence that is openable
or executable. The round-by-round ledger below is GENERATED from
`specs/reviews.py`. Regenerate with `python3 specs/render_closure.py
--write`; `--check` fails the build when it drifts.)*

<!-- GENERATED:review-closure -->

**2 internal round(s) and 23 external round(s) with a returned VERDICT are recorded for `0024`; 24 package(s) were dispatched** — counted from `specs/reviews.py`, which is the source this block is generated from. A round appearing here and not there, or the reverse, is impossible by construction. **SENT rows are dispatch records, not outcomes**, and are labelled below so the two are never summed.

| round | date | findings raised (from `raised=`) | verdict (compressed) |
|---|---|---|---|
| internal 1 (verdict) | 2026-08-17 | 0 | RETURN — light: one adjudication (the ruling the spec ASKED for), two moderates, four minors, all text-level. THE ADJUDICATION: the one disclosure-RAISING cell was put to the reviewer as 'if you think this door should not open at all, that is the finding we want'. IT OPENS — and the reviewer's argum… |
| internal 2 (verdict) | 2026-08-17 | 0 | PASS — the L1/L2 pair's internal review is COMPLETE. Verified against the diff: the vacuous-attack row EXECUTED in §2c-ii (the one-liner is the whole argument); the full 3x4 author x derived_from product with U2 against a separate oracle; the composition chosen with the half-restoration cell carryin… |
| external 1 (SENT) | 2026-08-21 | — | SENT (the coupled round-1 package `0024-0025-v1` — ONE archive, two INDEPENDENT specs (Spec-Requires 0005 and 0012 respectively, no mutual coupling), per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports n/a — first external round). 0024 at v2: L1, authorship-before… |
| external 1 (verdict) | 2026-08-21 | 4 | RETURN FOR AMENDMENT (2 blocking + 2 moderate; package sha 16024eeba284ac24 pinned). F1 BLOCKING — the spec declared independence from 0025 while its §4b rewrite target `unclassified` is DEFINED AND PROTECTED by 0025; without it the member is not registry-resident and a host supplying a FUNCTIONAL `… |
| external 2 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v2`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 at v3: all four round-1 findings folded — Spec-Requires names 0005 AND 0025 with the one-way acceptance coupling stated (F1); the coherence pr… |
| external 2 (verdict) | 2026-08-21 | 3 | RETURN FOR AMENDMENT (1 blocking + 2 moderate; sha 09f48f99 pinned). R2-1 BLOCKING — MY OWN two round-1 fixes contradict when composed: 0025 X10 said disclosure comes from the ORIGINAL relation while 0024 §4b assigns a re-dispositioned triple author-rules disclosure (USER → MENTIONABLE where the ori… |
| external 3 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v3`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 at v4: all three round-2 findings folded — the combined pipeline stated once at 0025 §4b-iii with X10 narrowed to the vocabulary fallback and … |
| external 3 (verdict) | 2026-08-21 | 2 | RETURN FOR AMENDMENT (1 blocking + 1 moderate; sha 588c761e pinned). R3-1 BLOCKING — the combined pipeline composed the PAIR and forgot the ACCEPTED STACK: a standing-revoked source's incoherent triple came out MENTIONABLE while accepted 0023 N1 requires QUARANTINED independently of author and relat… |
| external 4 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v4`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 at v5: both round-3 findings folded — the pipeline composes the ACCEPTED stack (every disclosure floor an explicit step, 0023 N1 named, revoke… |
| external 4 (verdict) | 2026-08-21 | 2 | RETURN FOR AMENDMENT (1 blocking + the shared evidence finding; sha c10b7341 pinned). R4-1 BLOCKING — §3's matrix still stated unconditional finals from author and relation alone: its USER/none/third_party_claim row said MENTIONABLE, false the moment the source is standing-revoked (accepted 0023 N1 … |
| external 5 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v5`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 at v6: both round-4 findings folded — the §3 matrix scoped to non-revoked sources with the revocation dimension its own row and base-vs-final … |
| external 5 (verdict) | 2026-08-21 | 1 | RETURN FOR AMENDMENT (1 blocking; sha b557698b pinned). R5-1 BLOCKING — the THIRD_PARTY-authored incoherent cell is simultaneously CHANGED (the matrix and reference move it QUARANTINED → USE_ONLY: relation re-dispositioned, quarantined property true → false, structural isolation → may-inform-never-a… |
| external 6 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v6`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 at v7: the round-5 finding folded — the THIRD_PARTY incoherent cell's transition RULED INTENDED and stated in §5, U2 exact-output over the ful… |
| external 6 (verdict) | 2026-08-21 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha ac0434d9 pinned): NO new 0024-scoped defect; R5-1 is CLOSED. 0024 cannot be accepted while its Spec-Requires 0025 remains unresolved. No amendment; the spec stays at v7 |
| external 7 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v7`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — the round-6 return was dependency-only (no 0024-scoped defect; R5-1 closed); it rides for the coupled verdict while 0025 res… |
| external 7 (verdict) | 2026-08-21 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha 5275d119 pinned): no new 0024-scoped defect; U1-U7 coherent; acceptance blocked by required 0025. No amendment; stays v7 |
| external 8 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v8`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — second consecutive dependency-only return; rides for the coupled verdict while 0025 resolves |
| external 8 (verdict) | 2026-08-21 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha 3f6ed6f0 pinned): no new 0024-scoped defect, third consecutive round; acceptance blocked by required 0025. No amendment; stays v7 |
| external 9 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v9`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — third consecutive dependency-only return; rides for the coupled verdict |
| external 9 (verdict) | 2026-08-21 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha a3970517 pinned): no new 0024-scoped defect, fourth consecutive round; blocked on required 0025. Stays v7 |
| external 10 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v10`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — fourth consecutive dependency-only return |
| external 10 (verdict) | 2026-08-21 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha 1e0c5104 pinned): byte-identical to the v9 copy, no new direct defect, fifth consecutive round; blocked on required 0025. Stays v7 |
| external 11 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v11`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — fifth consecutive dependency-only return |
| external 11 (verdict) | 2026-08-22 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha 9e5fd437 pinned): unchanged from v10, sixth consecutive round; 0005 noted ACCEPTED by the reviewer, so the wait is on 0025 alone. Stays v7 |
| external 12 (SENT) | 2026-08-22 | — | SENT (package `0024-0025-v12`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — sixth consecutive dependency-only return; the reviewer states both specs are final-disposition candidates after round 11's … |
| external 12 (verdict) | 2026-08-22 | 0 | 🏁 ACCEPTED on the frozen U1-U7 invariant surface (sha 5a91e7363bd5c310 verified by the reviewer; byte-identical to v11), following the SIMULTANEOUS acceptance of required 0025; prerequisite 0005 already accepted; the 0014 interface-freeze confirmation remains in force. Six final rounds dependency-on… |
| external 13 (SENT) | 2026-08-23 | — | SENT (package `0024-0025-v13` — AMENDMENT A1; 0025 rides unchanged at its accepted v13, the co-owned §4b-iii step-2 sentence carried VERBATIM in 0024 §7b per the 0014 precedent). The post-acceptance measurement round: v7's mechanism was implemented (1b542b9, U1-U7 green), Research's frozen 48-probe … |
| external 13 (verdict) | 2026-08-23 | 3 | RETURN FOR AMENDMENT (package `0024-0025-v13`, sha ec2950b8 verified; 0025 REMAINS ACCEPTED on X1-X13 — no basis found to reopen; the USE_ONLY direction well supported, no competing disposition requested; 'suitable for a narrow confirmation round' once corrected). A1-R13-1 (blocking): the amendment … |
| external 14 (SENT) | 2026-08-23 | — | SENT (package `0024-0025-v14` — the A1 narrow confirmation round; candidate v9, §12 maps the findings). A1-R13-1: the consequence-word sweep executed across BOTH specs ('assertable', 'user's own statement' — five passages rewritten here; the co-owned 0025 inventory grown to THREE verbatim replacemen… |
| external 14 (verdict) | 2026-08-24 | 1 | RETURN FOR A NARROW CARRIER AMENDMENT (package `0024-0025-v14`, sha 041693c2 verified; NO new architectural defect — A1's direction and revised U2 semantics SUBSTANTIVELY APPROVED; 0025 remains ACCEPTED). R14-1: the consequence sweep still incomplete at two carriers — §4b-i's question header said 'c… |
| external 15 (SENT) | 2026-08-24 | — | SENT (package `0024-0025-v15` — candidate v10, §13 maps the fold). R14-1: §4b-i asks about a RE-DISPOSITIONED RECORD; §9 enumerates all three 0025 replacements with the R14-1 note; the A1-R13-1 closure evidence asserts the live header form AND counts the three-replacement inventory. Standing feedbac… |
| external 15 (verdict) | 2026-08-24 | 3 | RETURN FOR A NARROW PROCESS/EVIDENCE AMENDMENT (package `0024-0025-v15`, sha 11fdccf1 verified; THE A1 DESIGN ITSELF IS READY — semantics substantively approved; 0025 remains ACCEPTED; the CO-OWNED three-passage interface CONFIRMED, surviving the return). A1-R15-1 (blocking): the R14-1 closure evide… |
| external 16 (SENT) | 2026-08-24 | — | SENT (package `0024-0025-v16` — candidate v11, §14 maps the fold). A1-R15-1: the R14-1 evidence section-scopes §9 ITSELF (three targets present, singular form rejected, §4b-i header live — the restore-§9-alone attack fails it); §9's note describes rather than quotes the defect phrasing. PACKAGE-R15-… |
| external 16 (verdict) | 2026-08-24 | 2 | RETURN FOR A NARROW PROCESS/EVIDENCE AMENDMENT (package `0024-0025-v16` reseal 0126Z, sha 8f58dd49 verified; NO design issue — A1 ready, revised U2 substantively approved, 0025 accepted, the co-owned interface confirmed). A1-R16-1 (blocking): the newly added A1-R15-1 ledger row's evidence — awk\|gre… |
| external 17 (SENT) | 2026-08-24 | — | SENT (package `0024-0025-v17` — candidate v12, §15 maps the fold). A1-R16-1: both consequence-carrier closure rows run the ONE named checker specs/check_a1_carriers.py (three §9 targets, singular form rejected, §4b-i header live — per-row inline evidence retired as a second copy of the check). EVIDE… |
| external 17 (verdict) | 2026-08-24 | 2 | RETURN FOR ONE NARROW PROCESS/EVIDENCE AMENDMENT (package `0024-0025-v17`, sha 5dc5c19f verified; NO new design defect; 0025 accepted; the co-owned interface confirmed). A1-R17-1 (blocking): check_a1_carriers searched the ENTIRE spec for the §4b-i header phrase, which the generated closure ledger al… |
| external 18 (SENT) | 2026-08-24 | — | SENT (package `0024-0025-v18` — candidate v13, §16 maps the fold). A1-R17-1: the checker isolates §4b-i and asserts the exact table row AT THE SITE (a quotation in the generated ledger no longer counts); the requested adversarial mutation matrix ships as test_a1_carrier_checker_mutation_matrix — pri… |
| external 18 (verdict) | 2026-08-24 | 1 | RETURN FOR ONE NARROW PROCESS AMENDMENT (package `0024-0025-v18`, sha 440b4e7a verified; NO design issue — revised U2 and U1-U7 remain substantively approved; 0025 accepted; the co-owned interface confirmed). A1-R18-1 (blocking): the checker now scopes to §4b-i (closing round 17's ledger shadow) but… |
| external 19 (SENT) | 2026-08-24 | — | SENT (package `0024-0025-v19` — candidate v14, §17 maps the fold). A1-R18-1: the §4b-i check anchors to the start of an ACTUAL Markdown table row with HTML comments STRIPPED before matching — the strip pre-empts the line-anchored-inside-comment variant of the same shadow (the property recursed rathe… |
| external 19 (verdict) | 2026-08-24 | 1 | RETURN FOR ONE NARROW PROCESS AMENDMENT (package `0024-0025-v19`, sha 80f86d87 verified; NO design issue — U1-U7 and revised U2 remain substantively approved; 0025 accepted; the co-owned interface confirmed). A1-R19-1 (blocking): the round-18 fix closed both shadow mutants but still proved neither t… |
| external 20 (SENT) | 2026-08-24 | — | SENT (package `0024-0025-v20` — candidate v15, §18 maps the fold). A1-R19-1: the §4b-i check PARSES the question table (comments stripped first): exactly one question/answer table, exactly one supersession-question row, the re-dispositioned wording, no obsolete corrected-user-statement row in the ta… |
| external 20 (verdict) | 2026-08-24 | 1 | RETURN FOR ONE NARROW PROCESS AMENDMENT (package `0024-0025-v20`, sha abd4388e verified; NO design issue — U1-U7 and revised U2 remain substantively approved; 0025 accepted; the co-owned interface confirmed). A1-R20-1 (blocking): the round-19 parser treats consecutive pipe-prefixed lines as a table … |
| external 21 (SENT) | 2026-08-24 | — | SENT (package `0024-0025-v21` — candidate v16, §19 maps the fold). A1-R20-1: a candidate block qualifies as the question table only with a valid two-column Markdown delimiter row as its second line, and fenced code regions are stripped before locating tables (joining the comment strip); both reviewe… |
| external 21 (verdict) | 2026-08-24 | 1 | RETURN FOR ONE NARROW PROCESS AMENDMENT (package `0024-0025-v21`, sha c5028cff verified; NO design issue — U1-U7 and revised U2 remain substantively approved; 0025 accepted; the co-owned interface confirmed). A1-R21-1 (blocking): the round-20 fix validates the delimiter and removes exactly triple-ba… |
| external 22 (SENT) | 2026-08-24 | — | SENT (package `0024-0025-v22` — candidate v17, §20 maps the fold). A1-R21-1: fence removal is a state parser over the full grammar — backtick or tilde openers of length >=3, closed by a same-character marker at least as long, alone on its line; the tilde and four-backtick mutants join the matrix. Se… |
| external 22 (verdict) | 2026-08-24 | 1 | RETURN FOR ONE NARROW PROCESS AMENDMENT (package `0024-0025-v22`, sha b07dd2c8 verified; NO design issue — U1-U7 and revised U2 remain substantively approved; 0025 accepted; the co-owned interface confirmed). A1-R22-1 (blocking): two valid Markdown contexts misclassified — a multi-word fence info st… |
| external 23 (SENT) | 2026-08-24 | — | SENT (package `0024-0025-v23` — candidate v18, §21 maps the fold; the CHECKER-TERMINUS PROPOSAL rides alongside). A1-R22-1: arbitrary fence info strings (backtick-info-no-backticks per CommonMark) and the three-leading-space bound on both fences and table rows; the reviewer's two mutants plus the SE… |
| external 23 (verdict) | 2026-08-24 | 3 | RETURN FOR A NARROW EVIDENCE/PROCESS AMENDMENT (package `0024-0025-v23`, sha 920fc792 verified; NO architectural issue; U1-U7 incl. revised U2 substantively approved — do not flip to accepted until these close; 0025 accepted; the co-owned interface confirmed). A1-R23-1 (blocking): the fence closer u… |
| external 24 (SENT) | 2026-08-24 | — | SENT (package `0024-0025-v24` — candidate v19, §22 maps the fold; the TERMINUS PROPOSAL is now an archive member). A1-R23-1: the closer requires [ 	]* exactly, and the compact whitespace oracle (five failing suffixes + the tab positive control) joined the matrix — its vertical-tab cell immediately … |

**Per-finding closure ledger — PROCESS §4a.** **31 finding(s) for `0024`; 171 across the 5 tracked specs** — every number here is DERIVED from the rows below (external round 7, R7-1: the manifest claimed 26 while the ledgers held 31, and 0023 said 9/9 above a 10-row table). Generated from `specs/closure_findings.py` and validated against `specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — extras, duplicates, wrong rounds and empty evidence all fail the build.

| finding | round | what it was | closed in | evidence (runnable) |
|---|---|---|---|---|
| **A1-R13-1** | external 13 | the A1 amendment was not carrier-complete while §11 claimed 'every carrier' — five passages still described the v7 assertable outcome, and the co-owned 0025 inventory named one passage of three | the consequence-word sweep ('assertable', 'user's own statement') executed across BOTH specs; §7b carries THREE verbatim 0025 replacements; §11 records the lesson in place of the claim | `grep -q 'is a re-dispositioned record then able to SUPERSEDE' specs/0024-authorship-before-structural-quarantine.md && test "$(grep -o 'REPLACEMENT [0-9] (' specs/0024-authorship-before-structural-quarantine.md \| wc -l)" -ge 3  # R14-1 strengthened: the live §4b-i header uses the re-dispositioned form AND the three-replacement inventory is counted per OCCURRENCE (grep -c counts lines; the three markers share the §7b table row)` |
| **A1-R13-2** | external 13 | the candidate patch did not run green (the revoked vector's control pinned pre-A1 MENTIONABLE) while §11 claimed verified-green — dev had verified with the pytest wrapper, not the reference's own runner | the control pins USE_ONLY; vector_a1_u2_oracle_exhaustive covers the complete author×derived product + revoked; 23/23 under python reference_enforcement.py itself | `grep -n 'vector_a1_u2_oracle_exhaustive' specs/evidence/0024/a1-reference.patch` |
| **PACKAGE-R13-1** | external 13 | package carriers described both specs as draft candidates while the canonical statuses are in-review/accepted; the 0025 r13 ledger row overstated 'no file edit, status untouched' | candidate lines DERIVE the status word from each spec's Spec-Status line, fail-closed; the ledger row states no-design-change precisely | `grep -n '_spec_status' specs/package_identity.py  # the derived status, refusing an unreadable Spec-Status` |
| **A1-R23-1** | external 23 | the fence closer used Python strip() — U+00A0 and other Unicode whitespace closed a fence CommonMark keeps open; and the oracle's vertical-tab cell then exposed str.splitlines() breaking on / where CommonMark does not | the closer requires spaces/tabs exactly; the parser splits on true newlines only; the five-suffix whitespace oracle + tab positive control are matrix cells | `$PY -m pytest tests/test_collected_header.py::test_a1_carrier_checker_mutation_matrix -q -p no:randomly` |
| **PROCESS-R23-1** | external 23 | both new gates accepted their prohibited proxies: P1 searched the whole test file for the artifact name; P4's startswith blessed $PY -c 'pass'; PROCESS.md was unchanged despite the adoption | P1 binds inside the named test's AST body; P4 requires a real pytest/named-script invocation; both planted mutants are in-gate self-tests; PROCESS.md records the rules | `$PY -m pytest tests/test_spec_gate.py::test_every_evidence_artifact_declares_a_mutation_matrix tests/test_spec_gate.py::test_new_closure_evidence_is_behavioral -q -p no:randomly` |
| **PACKAGE-R23-1** | external 23 | the terminus proposal was claimed to accompany the package while it traveled by a side channel that never arrived — a promised companion absent from the archive and its inventory | the proposal is the archive member specs/evidence/0024/A1-CHECKER-TERMINUS-PROPOSAL.md; the v23-era claims corrected in place | `$PY -m pytest tests/test_collected_header.py::test_terminus_proposal_is_an_archive_member -q -p no:randomly` |
| **A1-R22-1** | external 22 | two valid Markdown contexts misclassified: a multi-word fence info string was not an opener, and a four-space-indented table (rendered as code) was classified as a table | arbitrary fence-info text accepted (backtick-info-no-backticks per CommonMark); fences AND table rows bounded at three leading spaces; the reviewer's two mutants plus the self-exhausted indent-boundary cells (item 9) in the matrix | `$PY -m pytest tests/test_collected_header.py::test_a1_carrier_checker_mutation_matrix -q -p no:randomly` |
| **A1-R21-1** | external 21 | the fence strip removed exactly triple-backtick fences — tilde and four-backtick fences still rendered the table as code while the checker passed | fence removal is a state parser over the full grammar (backtick or tilde, length >=3, compatible same-character closer); both fence-form mutants in the matrix | `$PY -m pytest tests/test_collected_header.py::test_a1_carrier_checker_mutation_matrix -q -p no:randomly` |
| **A1-R20-1** | external 20 | the round-19 parser accepted any consecutive pipe lines as a table — a malformed delimiter row and a fenced code-rendered table both exited 0 | a table requires a valid two-column delimiter row; fenced code regions are stripped before locating tables; both mutants in the matrix | `$PY -m pytest tests/test_collected_header.py::test_a1_carrier_checker_mutation_matrix -q -p no:randomly` |
| **A1-R19-1** | external 19 | pipe-line anchoring proved neither table membership nor exclusivity — an isolated pipe-prefixed live line outside the table, and a contradictory second row, both exited 0 | the check PARSES the question table: exactly one table, exactly one supersession row, re-dispositioned wording, no obsolete row; both mutants in the matrix; the live row's annotation describes rather than quotes (the check's first run caught the spec's own quotation) | `$PY -m pytest tests/test_collected_header.py::test_a1_carrier_checker_mutation_matrix -q -p no:randomly` |
| **A1-R18-1** | external 18 | the round-17 fix scoped the search to §4b-i but matched the fragment ANYWHERE in the section — the obsolete row restored with the live fragment in an HTML comment passed; and the carriers typed 'five mutants' while six were invoked | the check anchors to an actual table row with comments STRIPPED before matching (the line-anchored-in-comment variant pre-empted); both shadow mutants join the matrix; count carriers enumerate, never type | `$PY -m pytest tests/test_collected_header.py::test_a1_carrier_checker_mutation_matrix -q -p no:randomly` |
| **A1-R17-1** | external 17 | the carrier checker searched the whole file for the §4b-i header phrase, which the generated ledger quotes — the ledger-shadow mutant (obsolete header restored, ledger untouched) exited 0 | the check isolates §4b-i and asserts the exact table row at the site; the requested adversarial mutation matrix ships in the suite, pristine + the enumerated mutants each biting (counts never typed - round-18 editorial) | `$PY -m pytest tests/test_collected_header.py::test_a1_carrier_checker_mutation_matrix -q -p no:randomly` |
| **EVIDENCE-R17-1** | external 17 | the EVIDENCE-R16-1 closure row cited the diagnostic string's lexical presence — a no-op validator containing it would satisfy the command | the row runs the WORKING deleted/None regression the reviewer verified sound | `$PY -m pytest tests/test_collected_header.py::test_baseline_validator_bites_on_a_planted_mutation -q -p no:randomly` |
| **A1-R16-1** | external 16 | the A1-R15-1 ledger row's own closure command was underpowered — its grep printed 1 and exited 0, establishing none of the three properties the row claimed | both consequence-carrier rows run the ONE named checker; per-row inline evidence retired as a second copy of the check | `$PY specs/check_a1_carriers.py` |
| **EVIDENCE-R16-1** | external 16 | e.get('subject','') coerced an ABSENT canary subject into passing the no-user-subject check — the deleted-subject mutant exited zero | the subject must be present, string-typed and nonempty after canonicalization before the 'user' test; deletion and None mutants are planted regressions | `$PY -m pytest tests/test_collected_header.py::test_baseline_validator_bites_on_a_planted_mutation -q -p no:randomly  # EVIDENCE-R17-1: the WORKING regression (the deleted/None mutants must fail the validator), not the lexical presence of its diagnostic — a no-op validator containing the string satisfied the old grep` |
| **A1-R15-1** | external 15 | the R14-1 closure evidence proved only half the finding — no command examined §9; restoring its obsolete singular summary alone passed both commands | the evidence section-scopes §9 itself: three replacement targets present, the singular form rejected, the §4b-i header live | `$PY specs/check_a1_carriers.py  # A1-R16-1: the row's first inline grep printed 1 and exited 0, proving none of its three claims — both rows now share the one named checker` |
| **PACKAGE-R15-1** | external 15 | verify_a1_patch accepted a skipped vector — only the reference was copied, and dev's installed veracium masked the empty src/ path locally (env-leak) | a complete tree is constructed, the exact zero-skip tail required, and import provenance witnessed (veracium must resolve from inside the constructed tree); the incomplete-tree refusal is a tested cell | `grep -n 'copy_src=False' tests/test_collected_header.py  # the refusal regression` |
| **EVIDENCE-R15-1** | external 15 | the 'whole evidentiary chain' claim was too broad — the canary subject re-run behind 'artifact-verified' was never persisted, so nothing shipped supported it | fresh persisted canary_subject_records.jsonl + CANARY_SUBJECTS.md ship digest-bound; §11/PROVENANCE state shipped-records-verify vs stdout-run-is-history exactly | `(cd specs/evidence/0024/baseline && sha256sum --quiet -c DIGESTS.sha256 && grep -q canary_subject_records DIGESTS.sha256)  # digests verify FROM the bundle dir and the canary records are bound` |
| **A1-R14-1** | external 14 | two consequence carriers survived the round-13 sweep — §4b-i's question header still said 'corrected user statement' and §9's brief still said 'one-sentence step-2 replacement' after the inventory grew to three; the closure evidence could detect neither | the §4b-i header asks about a re-dispositioned record; §9 enumerates all three 0025 replacements with the R14-1 note; the A1-R13-1 evidence strengthened to assert both | `$PY specs/check_a1_carriers.py  # A1-R16-1: ONE shared named checker for both consequence-carrier rows — three §9 targets, the singular form rejected, the §4b-i header live` |
| **F1** | external 1 | the spec declared independence from 0025 while its rewrite target `unclassified` is defined and protected there — without 0025 the member is not registry-resident and a functional host shadow lets the rewrite supersede | Spec-Requires header, the F1 blockquote | `grep -n 'Spec-Requires' specs/0024-authorship-before-structural-quarantine.md  # names 0005 AND 0025, with the coupling stated in the blockquote below it` |
| **F2** | external 1 | the coherence predicate was an intent, not a computation — the shipped ingest str()-converts truthy non-strings, so subject=["user"] survives the completeness check and the predicate's domain was undefined over it | §4a, §2c (subject AND relation cells), U1 | `grep -n 'casefold' specs/0024-authorship-before-structural-quarantine.md  # the canonical predicate, shared with the write site; odd types fail closed` |
| **F3** | external 1 | the invariant inventory existed in three drifted copies — §6 out of order, §7a citing a W-range, the package header hand-typing a range one past the real list | §6 (the ONE list), §7a tests row, collected_header_0024_0025.txt | `grep -n 'ONE authoritative' specs/0024-authorship-before-structural-quarantine.md  # and the header template now points at §6 instead of restating a count` |
| **F4** | external 1 | §8 claimed provenance accuracy in general; the rule corrects the literal-user-subject cell (~40.7% of the measured mislabels), prospectively, and the claim must not exceed it | §8 | `grep -n 'cell the rule recognizes' specs/0024-authorship-before-structural-quarantine.md` |
| **R2-1** | external 2 | two round-1 fixes contradicted when composed: X10 (disclosure from the original relation) vs §4b (author-rules disclosure after the coherence rewrite) — the reference implemented one and violated the other | 0025 §4b-iii (the one pipeline), 0024 §4b(2), X10 narrowed | `$PY specs/evidence/0025/reference_enforcement.py  # vector_combined_pipeline_ordering — the cross-spec cell, both branches` |
| **R2-2** | external 2 | §8 promised relayed content is never asserted; a relay mis-emitted with subject='user' lands inside the first-person exception and U1 cannot catch it | §8 (recorded-claimant property), §7 (the two doors) | `grep -n 'NON-USER claimant' specs/0024-authorship-before-structural-quarantine.md` |
| **R2-3** | external 2 | §3b claimed no new caller surface while U7 added three; U5's test name promised the withdrawn note carrier; telemetry had no consent disposition | §3b, §7a carriers row, U5, U7 ownership pointer | `grep -n 'test_redisposition_carries_the_original_relation' specs/0024-authorship-before-structural-quarantine.md` |
| **R3-1** | external 3 | the combined pipeline composed the pair and forgot the accepted stack — a standing-revoked source's incoherent triple came out MENTIONABLE against 0023 N1, and §5 claimed 0023 behaviour unchanged | 0025 §4b-iii step 3, 0024 §5 regime row | `$PY specs/evidence/0025/reference_enforcement.py  # vector_revoked_source_floor_wins_over_coherence — shows the without-the-floor bite on purpose` |
| **R3-2** | external 3 | Edge.original_relation carried two definitions across the pair, and §5/§7a still described the pre-round-1 registry and schema shapes | 0025 §2 (the one definition, two writers), 0024 §4b(3), §5, §7a | `grep -n 'TWO writers' specs/0025-relation-vocabulary-enforcement.md` |
| **R4-1** | external 4 | the §3 matrix stated unconditional finals from author and relation — false for a standing-revoked source (0023 N1) — and §4b said 'author rules ALONE' | §3 (scope + the revocation row), §4b(2) base-vs-final language | `$PY specs/evidence/0025/reference_enforcement.py  # vector_revoked_source_floor_wins_over_coherence — the revoked USER-authored third_party_claim cell the reviewer named` |
| **PAIR-R4-1** | external 4 | the published measurements did not reproduce from the shipped script | §1 (script-exact figures, rule stated), §2c-ii | `grep -n '41.7%' specs/evidence/0025/corpus_counts.py specs/0024-authorship-before-structural-quarantine.md  # the recorded run and the spec cite ONE figure; the corpus is local-only, the script runs where it lives` |
| **R5-1** | external 5 | the THIRD_PARTY incoherent cell was changed by the matrix and declared unchanged by §5, with U2 flooring where the matrix specified — two green implementations could disagree | §5 (the ruled transition), U2 (exact output), §3 scope sentence | `grep -n 'CHANGED for exactly the incoherent subset' specs/0024-authorship-before-structural-quarantine.md  # and the reference asserts USE_ONLY exactly: vector_author_floor_holds_through_redisposition` |

<!-- /GENERATED:review-closure -->

## 12. Changes in v9 (the A1 round-13 fold, 2026-08-23)

1. **A1-R13-1 — the amendment was not carrier-complete, and §11 claimed
   it was.** Five normative passages still described the v7 outcome
   (§1's "is not a fix", §3b's assertable + license-MENTIONABLE
   claims, §4b-i's "becomes assertable", §8's historical annotation),
   and the co-owned `0025` inventory named one passage where three
   exist (§4b-iii step 1's "becomes the user's own statement";
   §7b's "corrected user statement… becomes assertable"). All are
   rewritten around the narrower measured fact: the label is
   self-contradictory, so the record may inform — it is neither proven
   to be the user's own statement nor assertable. The sweep now greps
   the CONSEQUENCE words ("assertable", "user's own statement") across
   both specs, and §11 records the lesson in place of the false claim.
2. **A1-R13-2 — the candidate evidence did not run green, against
   §11's claim that it did.** `vector_revoked_source_floor_wins_over_
   coherence`'s non-revoked control pinned the pre-A1 MENTIONABLE;
   I had verified with the pytest wrapper (20 tests) instead of the
   reference file's OWN runner (all `vector_*`), which is the runner
   the reviewer uses. The control now pins A1's USE_ONLY, a new
   `vector_a1_u2_oracle_exhaustive` enumerates the COMPLETE U2 domain
   (author × derived_from, non-revoked all-USE_ONLY plus revoked
   QUARANTINED), and the patched suite runs 23/23 under
   `python reference_enforcement.py` itself — the verification §11 now
   cites is the one the reviewer will re-run.
3. **PACKAGE-R13-1 — package carriers now DERIVE status.** The
   candidate lines in COLLECTED/manifest read status from each spec's
   canonical `Spec-Status:` line (0024 `in review`, 0025 `accepted`)
   instead of a hardcoded "draft"; the 0025 round-13 ledger row states
   the truth precisely — no X1–X13 design change, rather than no file
   or status change (v12→v13 changed both).

## 13. Changes in v10 (the A1 round-14 fold, 2026-08-24)

1. **R14-1 — two consequence carriers survived the round-13 sweep,
   because the sweep's needle list was narrower than the consequence
   vocabulary** (the domain class: I grepped "assertable" and "user's
   own statement" and missed "corrected user statement" in §4b-i's
   QUESTION HEADER, and §9's brief was a second copy of the §7b
   inventory that rotted when round 13 grew it to three). Fixed: the
   §4b-i question asks about a re-dispositioned record; §9 enumerates
   all three `0025` replacements with the R14-1 note; the A1-R13-1
   closure evidence now asserts the live header form AND counts the
   three-replacement inventory — the old `grep -c 'becomes assertable'`
   could detect neither.
2. **Standing feedback adopted:** `specs/verify_a1_patch.py` — applies
   `a1-reference.patch` to a temporary copy and runs the patched file's
   own vector runner, one command, wired into the sealer's extraction
   checks so the round-13 wrapper-versus-own-runner mismatch is
   mechanically unrepeatable; it skips VISIBLY when no patch ships.

## 14. Changes in v11 (the A1 round-15 fold, 2026-08-24)

1. **A1-R15-1 — the R14-1 closure evidence proved only half the
   finding** (proxy: it bound the §4b-i header and §7b's markers, never
   §9 — restoring §9's obsolete summary alone passed both commands).
   The evidence now section-scopes §9 itself: all three replacement
   targets present, the singular step-2 form rejected, the §4b-i header
   still live; §9's R14-1 note describes the defect phrasing instead of
   quoting it so the sweep can grep for it.
2. **PACKAGE-R15-1 — the patch verifier accepted a skipped vector**
   (env-leak: it copied only the reference file, and dev's installed
   veracium masked the empty `src/` path that makes the
   shipped-default-registry vector skip in a clean extraction). The
   verifier now constructs a complete tree, requires the EXACT
   `0 named skip(s)` tail, and witnesses import provenance — veracium
   must resolve from inside the constructed tree; the incomplete-tree
   refusal is a tested cell.
3. **EVIDENCE-R15-1 — the "whole evidentiary chain" claim was too
   broad**, and research's answer began with a confession: the earlier
   canary-subject re-run printed to stdout and persisted nothing. The
   shipped bundle now carries a FRESH persisted measurement
   (`canary_subject_records.jsonl` + `CANARY_SUBJECTS.md`,
   `fd3a6170`) — all 8 canary subjects the claiming voice, all
   quarantined, one benign temp-0 drift disclosed — and §11/PROVENANCE
   state the boundary exactly: shipped records are the verification;
   the stdout run is corroborating history.
4. **Reviewer suggestion adopted:** `validate_baseline.py` recomputes
   both summaries and the exact five-probe movement set (A:1, B:4) and
   the 14→10 relay floor from the shipped JSONL — offline, no model;
   in the sealer's extraction checks, with a planted-mutation
   regression proving it bites (research's §VII condition on trusting
   its green).

## 15. Changes in v12 (the A1 round-16 fold, 2026-08-24)

1. **A1-R16-1 — the closure of the closure was underpowered** (proxy,
   one level up: the A1-R15-1 ledger row's inline grep printed `1` and
   exited successfully, establishing none of the three properties its
   prose claimed, while the A1-R14-1 command beside it was complete).
   Per-row inline evidence is a second copy of the check; both rows now
   run the ONE named checker `specs/check_a1_carriers.py` — three §9
   targets, the singular form rejected, the §4b-i header live — so the
   evidence cannot diverge from itself again.
2. **EVIDENCE-R16-1 — absence passed as evidence** (coercion:
   `e.get("subject", "")` defaulted a missing canary subject to `""`,
   which satisfied the no-user-subject check; the reviewer's
   deleted-subject mutant exited zero while claiming "8/8, no
   user-subject"). The validator now requires every canary edge subject
   to be PRESENT, string-typed and nonempty after canonicalization
   before testing it against 'user'; the deletion and None mutants are
   planted regressions beside the mutation-to-user one.

## 16. Changes in v13 (the A1 round-17 fold, 2026-08-24)

1. **A1-R17-1 — the carrier checker did not bind §4b-i** (proxy, again
   one level deeper: the checker searched the WHOLE file for the header
   phrase, and the generated closure ledger QUOTES that phrase — so the
   reviewer restored the obsolete header, left the ledger alone, and
   the checker reported the header live). The §4b-i check now isolates
   the §4b-i section and asserts the exact table row inside it; the
   reviewer's requested ADVERSARIAL MUTATION MATRIX ships as
   `test_a1_carrier_checker_mutation_matrix` — pristine passes, and
   each mutant bites; the cells are ENUMERATED in the test itself,
   never counted here (round-18 editorial: this line originally typed
   'five' while six were invoked — a typed count of an enumerable list
   is a second copy, and it drifted immediately).
2. **EVIDENCE-R17-1 — the closure row cited lexical presence** (proxy:
   a grep for the validator's diagnostic string, which a no-op
   validator containing the string would satisfy). The row now runs the
   WORKING regression — the pytest test whose deleted/None mutants must
   fail the validator — which the reviewer verified sound.

## 17. Changes in v14 (the A1 round-18 fold, 2026-08-24)

1. **A1-R18-1 — substring-in-section was still not the table row**
   (proxy, and the sealer's own mention-is-not-use lesson: the round-17
   fix scoped the search to §4b-i but matched the fragment ANYWHERE in
   it, so the reviewer restored the obsolete row and hid the live
   fragment in an HTML comment — the checker reported the header live).
   The check now (a) anchors to the start of an actual Markdown table
   row and (b) strips HTML comments before matching — (b) because a
   multi-line comment can put the fragment at a line start, and waiting
   for that round would be the same class again. Both mutants — the
   reviewer's comment-shadow verbatim and the line-anchored variant —
   join the matrix.
2. **The count editorial:** the carriers claimed five mutants while the
   test invoked six. Every count carrier now ENUMERATES or points at
   the test; the wrong 'five' entries are corrected in place with the
   note rather than silently rewritten.

## 18. Changes in v15 (the A1 round-19 fold, 2026-08-24)

1. **A1-R19-1 — anchoring proved neither membership nor exclusivity**
   (the same class, terminal form: a pipe-prefixed line is not the
   table, and one live row does not preclude a contradictory second).
   The check now PARSES §4b-i's question table (comments stripped
   first) and asserts the reviewer's three properties: exactly one
   question/answer table; exactly one supersession-question row; that
   row in the re-dispositioned wording; no obsolete
   corrected-user-statement row anywhere in the table. Both reviewer
   mutants — the outside-the-table stray line and the contradictory
   second row — join the matrix.
2. **The check's first run caught the spec itself:** the live row's
   R14-1 annotation QUOTED the obsolete phrase, tripping the parsed
   exclusivity check — the describe-don't-quote corollary now applies
   to the row exactly as it already did to §9, and the annotation
   describes the defect instead.

## 19. Changes in v16 (the A1 round-20 fold, 2026-08-24)

1. **A1-R20-1 — consecutive pipe lines are not a Markdown table** (the
   same class: the round-19 parser accepted any pipe block with the
   question/answer header, without the delimiter row that makes it a
   table or the context that makes it rendered — an ordinary two-cell
   row in the delimiter's place, and the whole table inside a fenced
   code block, both exited 0). The parser now requires a valid
   two-column Markdown delimiter row as the block's second line and
   strips fenced code regions before locating tables (joining the
   comment strip). Both reviewer mutants — the malformed delimiter and
   the fenced table — join the matrix.

## 20. Changes in v17 (the A1 round-21 fold, 2026-08-24)

1. **A1-R21-1 — one literal fence form was a proxy for the fence
   grammar**: the round-20 regex stripped exactly ``` fences, and a
   tilde fence or a four-backtick fence still rendered the table as
   code while the checker passed. Fence removal is now a state parser
   recognizing backtick and tilde openers of length ≥3, closed only by
   a same-character marker at least as long, alone on its line. The
   tilde and four-backtick mutants join the matrix.

## 21. Changes in v18 (the A1 round-22 fold, 2026-08-24)

1. **A1-R22-1 — two more valid Markdown contexts**: a multi-word fence
   info string is a valid opener (the regex allowed one token), and a
   four-space-indented table renders as an indented code block (the
   row classifier accepted any indentation). The fence parser now
   takes an arbitrary info string (with CommonMark's
   backtick-info-may-not-hold-backticks rule) and both fences and
   table rows are bounded at three leading spaces. Beyond the two
   reviewer mutants, the indent boundary's OTHER two cells are
   self-exhausted per checklist item 9: a 2-space-indented fence must
   still hide the table (failing cell), and a 4-space-indented marker
   is code, not a fence, so the table between such markers is real
   (passing control).
2. **Process, from the 22-round analysis (adopted by Quentin):** the
   P1 gate — every evidence artifact declares and binds a named
   adversarial mutation matrix, refused otherwise — and the P4 gate —
   closure evidence past the frozen cutoffs must run a named script or
   test, never an inline lexical command. Both standing in
   `tests/test_spec_gate.py`; the three A1-era artifacts are annotated
   and bound. The checker-terminus proposal is the archive member
   `specs/evidence/0024/A1-CHECKER-TERMINUS-PROPOSAL.md` (moved
   in-archive at round 23, PACKAGE-R23-1 — the v23 wording claimed a
   companion that traveled by a side channel and never arrived):
   produced-not-typed carrier as the structural terminus, or
   acceptance with evidence-maintenance status under P1.

## 22. Changes in v19 (the A1 round-23 fold, 2026-08-24)

1. **A1-R23-1 — the closer's whitespace class was Python's, not
   CommonMark's**: `strip()` removes U+00A0 and friends, so an
   NBSP-suffixed pseudo-closer closed the fence and the code-rendered
   table passed. The closer now requires `[ \t]*` exactly, and the new
   whitespace oracle (U+00A0, U+2000, U+3000, VT, FF failing cells; a
   tab-suffixed positive control) joined the matrix — where its
   vertical-tab cell immediately caught a SECOND same-class
   discrepancy: `str.splitlines()` treats \\v/\\f as line boundaries
   and CommonMark does not, so the parser now splits on true newlines
   only. The oracle bit before it shipped.
2. **PROCESS-R23-1 — both gates accepted their prohibited proxies**:
   P1 searched the whole test FILE for the artifact name (an
   unrelated-matrix pointer with the filename mentioned elsewhere
   passed) — it now extracts the named test's AST body and binds the
   reference there; P4's `startswith("$PY")` blessed `$PY -c "pass"` —
   it now requires an actual `$PY -m pytest tests/<f>::<t>` or
   `$PY specs/<script>.py` invocation. The reviewer's two planted
   mutants are in-gate self-tests, and `specs/PROCESS.md` records the
   adopted rules with their governed domain.
3. **PACKAGE-R23-1 — a promised companion is a carrier**: the terminus
   proposal was claimed to accompany v23 while it sat in a side
   channel that never arrived. It is now the archive member
   `specs/evidence/0024/A1-CHECKER-TERMINUS-PROPOSAL.md`, inventoried
   like everything else, and the v23-era claims are corrected in place
   with the note.
