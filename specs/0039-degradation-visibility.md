# Feature spec: degradation visibility — what a caller and an operator learn when veracium degrades instead of failing

Spec-Status: draft

*Candidate authored by dev (veracium-69), 2026-09-07, on the owner's word ("Get a spec
number and write that up"), from the owner's question during testing: if an error occurs
during our use, do we know about it? Number 0039 taken from the registry
(`specs/allocation.py --next`). Every claim in §1 is a line in the tree at the commit this
draft was written against; the reviewer can open each one.*

| | |
|---|---|
| **Author / session** | dev (veracium-69) |
| **Version** | **v10 — RESEARCH'S DIFF OF v9 AGAINST ITS MATRIX FOLDED (2026-09-09; every measured cell agrees on both instruments — 17 primary and 9 retry shapes map onto rows 1–12 with no disagreement).** Two clauses and two measurements. **D1** row 10's title ("a list with malformed members") was wider than its cell: three kinds of member are not stored — a SHAPE-GUARD failure (silent, uncounted: the row's subject), a pipe-composed subject (`subject_refused`, already counted) and an off-vocabulary relation (`invalid`, already counted) — and `member_skipped` implemented against the title would count members two existing counters already count, the double count 0025's inventory exists to prevent; the clause: it counts SHAPE-GUARD failures only, never a member a rule refused. **D2** the merged invariant's provenance sentence read "absorbing V-ANSWER-MATRIX and V-ANSWER-MATRIX" — the v9 rename swept the one MENTION whose job was to name what was merged (a bulk replace applied to a mention as though it were a use, inside twenty-four hours of banking that rule); restored by name. **Two cells measured rather than read:** row 13 (a primary `Complete` call that raises propagates out of `ingest_event` — run: `RuntimeError` reaches the caller after one call) and row 12's retry cell (a retry answer carrying `instructions` as a string, as a list, or not at all is used for recovery unchanged — run on both instruments: `recovered: 1` in all three states; the field is not read there). *(was:* v9 — RESEARCH'S RED-TEAM OF v8 FOLDED (2026-09-09, before v8 was committed; the batch rule).** On research's OWN instrument (17 primary shapes and 9 retry shapes through the real `ingest_event`; a script sharing the author's assumptions cannot red-team the author): **H1** two batteries invite the defect they exist to catch — four shapes classify DIFFERENTLY depending on which call they arrive on, and with two tables an asymmetry is findable only by holding them side by side. v9 makes it ONE MATRIX (§2c-ii): shape down the side, the two call sites across, every cell one classification, every asymmetric row marked — so the next asymmetry is a row you read, not a discovery (the "or" row of v6, one level up). **H2** Q4 named one asymmetry; the matrix shows five, one of them 0025's design (a first-call provider failure is an error, a retry failure is a no-op) and four undesigned (`null`; a number or boolean; a bare array of dicts; a bare array of scalars) — Q4 and Q6 merge into ONE 0025 amendment question: one normalization rule shared by both callers. **H3** "bare array" is two rows with opposite outcomes on the first call (dicts recover; scalars silently yield nothing). **H4** three more silent-empty primary shapes (`[{}, {}]`; a nested `{"triples": {"triples": [...]}}`; a mixed list storing one fact and skipping three with `invalid: 0`) — all `member_skipped` or `shape`, named in the matrix. **Exhaustiveness claim, now with the matrix behind it:** no retry shape on either instrument lands outside the six `cause` values. **Measured premise for §1:** all eight non-recovering retry shapes return byte-identical counters (`invalid: 1, retried: 1, recovered: 0`) — eight provider behaviours, one observable. The retrospective gate's skip reason names the third repository state ("no repository") rather than "not a checkout", because an archive is not a shallow repo, it is no repo — and it SKIPS visibly, never passes, so the gate's own "a zero is not a pass" survives. *(was:* v8 — ROUND-1 EXTERNAL VERDICT FOLDED (RETURN for amendment, 2026-09-09; banked verbatim `outbox/0039-round1-verdict-verbatim.md`, body sha16 `a1192145c342ba4c`).** Four blocking findings, each REPRODUCED BY EXECUTION at HEAD before a line moved (§1f is the measurement). **F1** the PRIMARY extraction path had unclassified outcomes and v4's row 3 was WRONG — a wrong-typed `triples` does not raise `AttributeError`: a string or dict is iterated and every member skipped (zero facts, no flag, no error), a missing key is a silent empty result, and `null`/number/boolean raise `TypeError`; the spec's author DERIVED that row from reading the loop and did not run it, which is the rule this project already carries. → a primary-answer battery (V-ANSWER-MATRIX) with every cell classified normal / recorded degrade / propagated error, two new degrade kinds (`primary_failed`, `member_skipped`), and the retry battery re-measured (a `null` `triples` on the retry is the shape branch, not an exception). **F2** a raising `on_degrade` callback was not contained by the normative text → ONE guarded invocation helper every site must use (V-CALLBACK-CONTAINED: an AST census of direct calls plus a raising callback at every site with results and stored bytes identical to `on_degrade=None`). **F3** "never delays" conflicted with `Reporter.record_error`'s synchronous pre-authorised auto-send (a 15-second HTTP timeout) → `record_degrade` NEVER sends inline; it writes one local line and leaves the record pending (V-NO-INLINE-SEND). **F4** length + unkeyed digest is not content-free and an exception class name is not a bounded vocabulary → lengths are UTF-8 byte counts, digests are SHA-256 over the stated UTF-8 bytes, the equality/guessing leakage is ACKNOWLEDGED in §8 (a keyed digest is §10 Q5, rejected with its reason), and `cause` is a CLOSED vocabulary — the exception's class name is never recorded (V-CAUSE-BOUNDED; a sentinel-carrying custom exception is a test). PACKAGE finding: the retrospective deadline gate went red in the reviewer's `git archive` tree (no `.git`) — made archive-aware in the same commit. *(was:* v7 — RESEARCH'S DIFF READ OF v6 FOLDED (2026-09-09; all eleven changed lines read, pass).** One wording defect, present since v5 and missed on the v5 read (research's own, not one a fold created): the battery's seventh shape read "a list of dicts → recovery", which a bare JSON array of dicts satisfies literally — the same input as the third shape, `bare array → cause=AttributeError`, with a contradictory outcome — in the one row that exists so a reviewer can implement it and add an eighth shape. Fixed to `{"triples": [dicts]}`, so the four object-form shapes are parallel and "bare array" is unambiguously the top-level case. *(was:* v6 — RESEARCH'S CONFIRMING READ OF v5 FOLDED (2026-09-09; a diff against v4, 17 hunks, all inside the listed cells; no blocking findings).** ONE finding the v5 fold itself created: V-ANSWER-MATRIX's bare-array row accepted EITHER outcome — normalized after §2e's amendment, `AttributeError` before — the only row with an "or", and exactly the row the amendment changes; a test that passes on both states cannot detect the transition it exists to bracket, and a wrong wrap (members dropped; wrapped and then failing anyway) would pass because `AttributeError` stayed an accepted answer, while the log count going to zero is an observation over production, not an assertion in the suite. Fixed: the battery asserts the CURRENT state (bare array → `cause=AttributeError`), and the 0025 amendment FLIPS that one assertion in the same commit that adds the wrap — the amendment cannot land without the test changing, the test change IS its proof, and the log count becomes corroboration. *(was:* v5 — RESEARCH'S v4 READ AND ITS FOLLOW-UP FOLDED (2026-09-09, same day; never committed between).** THE FOLLOW-UP, measured at HEAD: a FIFTH way to `reps = []` that v4's enumeration did not contain — a well-formed object with NO `triples` key (`{"repairs": [...]}`, `{"note": "none found"}`) returns `[]` from `.get`, raises nothing, touches no branch, and is indistinguishable in every carrier from `{"triples": []}` — the indistinguishability §1a exists to end. Classed a degrade with its own `cause` token `no_triples_key` (a wrong schema is not a wrong type). And the widened AST census has six spellings that evade it (an IfExp or `or []`, a guard assigning an ENUM member such as the volatility default, a binding one hop further, a parser that is not `extract_json`, a helper extracted out of `ingest_event`, a member-level filter that drops bad members) — so §6 states the class the census cannot answer ("where can provider output be silently discarded" is an OUTCOME question; a static rule answers "where does this code shape appear") and adds a DYNAMIC arm, V-ANSWER-MATRIX: every answer shape at the retry site produces a distinctly labelled record or a documented non-degrade, no two shapes sharing a classification unless the spec says they do — the arm that would have caught paths iii and v without anyone thinking of them first. Two findings from the read itself, both taken whole. **F2, BLOCKING:** the shape-path record could not satisfy V-RECORD-FIELDS-TOTAL — no exception, so no message to measure, and filling `msg_len`/`msg_sha16` with 0 and sha256("") would assert a zero-length message existed ("an absent key is not a zero" turned inside out, in the spec that cites it). Resolved by research's third option: the field set is declared per (`degrade`, `cause`), and the field is RENAMED `cause` — `exc_type` means "the exception's class name", a name made false by the token `shape`; a separate `degrade` value would split the operator's count of retry failures across two rows. **F1, SUBSTANTIVE:** V-CENSUS walks `ExceptHandler` nodes, so it cannot see a degrade of the shape v4 itself found — a guarded literal-reset branch that raises nothing; it guarded only the class already known. §6 now states that limit and widens the census to the second detectable shape. **Q4 → a 0025 AMENDMENT, re-argued:** `extract_json`'s docstring returns a bare array "for the caller to normalize"; the first extraction does, the retry does not — one of two callers not honouring the documented obligation of the function it calls, a contract-conformance defect, not a symmetry preference; drafted in §2e as an amendment to 0025 §4b(1), landing with this spec's implementation; row 2c stays as the evidence, and `cause=AttributeError` going to zero becomes the amendment's test. Minor: the shape branch is INSIDE the `try`, not above the handler. *(was:* v4 — DEV'S §3a CODE-REALITY READ FOLDED (2026-09-09, on Quentin's word "let's do spec 0039 for an internal read").** Every §1 claim re-verified at HEAD `b3c67d2` after 0037, 0025 v14 and 0038 landed on `ingest.py`: the census still returns four handlers (L114 re-raises; L294, L443, L503 continue); `Memory(diagnostics=None)`; `_on_error` at five sites, the CALLER re-raising; `load_reporter` in `build_memory` only; two CLI constructions, neither attaching; `RotatingFileHandler(maxBytes=1_000_000, backupCount=2)`; `redact` measured. ONE SUBSTANTIVE FINDING (D1): the retry site reaches `reps = []` FOUR ways and only two of them are exceptions — a well-formed answer whose `triples` is not a list is a shape branch that raises nothing, so a record emitted from the `except` would miss it; and the retry path lacks the bare-array wrap the first extraction has, so a bare JSON array answer is `AttributeError`, not recovery (§10 Q4, not changed here). §2a/§2c/§2c-i rows 2–3 restated for it; the retry record is emitted ONCE after the block on a failure flag, never on a legitimately empty recovery. Eight smaller corrections: a present `null` volatility is a drift (row 5); a wrong-typed first-extraction `triples` is an ERROR, not a degrade (row 3); the extractor's own message embeds `text[:200]` of provider output (row 7's measured instance); `redact`'s four patterns named; `user_hash` is sha256's first 12 hex; only the CLI's `remember` construction can emit a degrade record; V-RESULT-UNCHANGED phrased as the set X12 pins at HEAD. *(was v3 — RESEARCH'S v2 READ FOLDED (2026-09-07, same day).)** Read against the shipped paths at the v2 commit, not against v2's prose: the volatility handler sits inside the per-triple loop (so §2b's per-call count is derivable); `_on_error` exists with three call sites; X12's test says PRECISELY; `cli.py` has exactly two `Memory(...)` constructions. ONE finding, taken whole: **§2a's field table was CLOSED IN ONE DIRECTION ONLY.** "Nothing else may be added" and a mutant list that killed additions — and NOTHING forbade an OMISSION: a `volatility_defaulted` record with no `count`, a `retry_failed` record with no `exc_type`, satisfied every §6 invariant, because V-DEGRADE-RECORDED asserts existence and cardinality, V-NO-CONTENT-IN-LOG asserts absence, and none asserted the field SET. 0025 §4c had already named why it matters — *an absent key is not a zero* — for counters; a degrade record is where it applies next. **V-RECORD-FIELDS-TOTAL** (§6): for each `degrade` value the record carries EXACTLY its declared field set, asserted as exact set equality per degrade type, never a subset check; mutants: a record missing `count`; one missing `exc_type`; one carrying another type's field. The fourth invariant of the day found constraining one direction only (V-NEVER-HEAD over results; V-NO-EXISTENCE-SIGNAL by hiding everything; the withdrawn register catching uses not mentions; this) — the tell is a rule that names what must NOT happen without naming what MUST. Also §7: the window stated with its FILE COUNT beside the size — **3 MB (1 MB × 3 files: the active file and `backupCount=2`)** — because "backupCount=2 means three files" is the off-by-one that produced a wrong headline in the read that got the retention arithmetic right; and §7 now says the derived retention figure (records per window; events to evict a traceback) is the number to quote, since the retention claim is the section's subject and does not depend on getting a unit right. Credits: research (veracium-research-32), second read. *v2 — RESEARCH'S FIRST READ FOLDED (2026-09-07, same day as v1).* Four changes, each from a check EXECUTED against the shipped code rather than read from v1's description of it. **(1) A THIRD degrade path.** v1 said the two named sites were "the ONLY places ingest continues after a provider failure" and proposed an except-clause census as the proof; the census, run by both seats independently and converging, found FOUR handlers of which THREE continue: the two v1 named and `except ValueError: vol = Volatility.DURABLE` — a model-emitted volatility value outside the enum is silently coerced to DURABLE, per triple, with no counter, no record and no warning. v1's sentence survived on a strict reading ("provider *failure*") and failed the spec's purpose; §1 is widened from provider failure to **provider-originated degradation** and the volatility coercion is ranked WORST of the three, because the other two degrade into a visible absence and this one produces a record that looks correct, on an axis the paper names as a contribution. **(2) The record carries NO message text.** v1's "capped and redacted" was measured: `diagnostics.redact` on a provider error echoing a prompt removes the email and the phone number and keeps "Alice moved to Berlin" — it strips PII-SHAPED TOKENS and preserves the SEMANTIC PAYLOAD, which for a memory product is backwards (the fact IS the payload). The record is now the exception TYPE, the message LENGTH and a digest — never the text (§2a, §2c-i row 7, V-NO-CONTENT-IN-LOG). **(3) The seam is a callback, decided by 0025 X12.** v1 left open whether the degrade fact travels as a private field on the ingest result or as a callback on `ingest_event`'s signature; X12 asserts the result's counter keys are PRECISELY §4c's public set, so a private field survives only by exempting the invariant that makes the set closed. Callback (§2c; old Q2 closed). **(4) §7 answered the wrong question.** "Bounded by rotation" is a SIZE bound; the operator's question is RETENTION — after 0039 how long a real traceback survives depends on DEGRADE volume, and a per-triple record on the volatility path would evict the errors the log exists for. The volatility path is aggregated to ONE record per `ingest_event` call with a count (V-ONE-RECORD-PER-CALL); §7 states the retention consequence with the window re-derived from the handler's parameters. Also added to §8 as the spec's strongest argument, previously implicit: the CLI attaches NO reporter today (`load_reporter`: zero occurrences in `cli.py`, one in `mcp_server.py`), so every degrade — the volatility coercion included, for as long as it has existed — is invisible to a CLI user until this ships. Credits: research (veracium-research-32), first reader under PROCESS §3a: the census run, the redaction inversion framing, the X12 ruling, the retention arithmetic, the §8 limit. *v1 (2026-09-07) — THE DRAFT, written from the shipped code: the two ingest paths that record a failure instead of raising it, the library's `diagnostics=None` default, the two CLI `Memory(...)` constructions that attach no reporter while the MCP entry point does, and the MCP result's strip of the degradation counters. ONE reader: its author.* |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (veracium-research-32/-5f) — reads folded at v2, v3 and v5; dev (veracium-90) — §3a code-reality read folded at v4 |
| **External review** | REQUIRED — changes what two shipped entry points do on error, and what the diagnostics log contains. **Round 1 (package `55c50e11…` @ `10f55a2`, v7): RETURN for amendment, 2026-09-09** — four blocking findings, folded at v8 (the Version cell); the verdict rides in round 2's package verbatim |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0025** — the ingest report's counter inventory (`invalid`, `retried`, `recovered`, `residual`, `redispositioned`), present on every return path, and its rule that a provider failure during the ONE retry is recorded as `retried > 0, recovered = 0` and NEVER re-raised (§4b(1)). This spec keeps that contract unchanged: it adds a second carrier for the same fact, it does not turn a degrade into a raise. **X12** (the result carries PRECISELY the §4c public counter keys) decides §2c: the degrade fact does not travel on the result.
- **0031 §4d** — the operator-only counters are STRIPPED from the MCP tool result because a model that learns how often its attempts are refused learns to probe. This spec keeps that strip unchanged and does not add a principal-facing field (§10 Q1 asks whether one is wanted; it is not decided here).
- **0007 §4c** — the busy-timeout discipline is the precedent for "a failure has defined behaviour and a named form"; this spec applies the same discipline to the degrade paths' record.

---

## 1. Problem — measured, not hypothesised

**Veracium degrades in three places by catching, and — measured at v8, §1f — in two more
by defaulting and filtering, instead of failing, and by design.** Each is a correct
contract (0025 §4b; the BYO-provider clause; the extraction schema's tolerance). None
leaves a record an operator will see. The three are the ONLY exception handlers in
`ingest.py` that continue after catching; a fourth (the event-date parser) re-raises; the
two silent shapes on the first answer are not handlers at all. The
census is §6's V-CENSUS node — run, not read.

**1a. The retry that fails silently.** `ingest.py` makes ONE re-extraction call for
off-vocabulary triples. If the provider raises, times out, or returns malformed output,
the `except Exception:` at the retry site sets the replacement list empty and continues:

```
except Exception:
    reps = []          # malformed output / provider failure: a no-op,
                       # visible as retried > 0, recovered = 0 — never
                       # re-raised, never a second call (§4b(1))
```

The event is stored; the report carries `retried: 1, recovered: 0, residual: N`. A
provider outage during that call is indistinguishable, in every carrier that exists
today, from a model that gave a poor second answer. The exception object — its type and
message — is discarded at that line.

**Eight provider behaviours, one observable (v9, research's instrument).** Every
non-recovering retry answer — the provider raising, prose, a bare array of dicts, a bare
array of scalars, `triples` as a string, as a dict, as `null`, and a missing key — returns
the BYTE-IDENTICAL counters `invalid: 1, retried: 1, recovered: 0`. That is this spec's
argument, measured: eight distinct things the provider did, one thing the operator can
see.

**The five KNOWN ways to the same empty list (v4 found four and called it complete; v5 found the fifth).** `reps = []` is reached by at least (i) the
provider call raising; (ii) `extract_json` raising `ValueError` — no JSON in the answer;
(iii) a well-formed answer whose `triples` is NOT a list — the line
`if not isinstance(reps, list): reps = []` INSIDE the `try`, two lines above the
`except`, which raises NOTHING;
and (iv) a bare JSON array — `extract_json` returns the list as a fallback and `.get`
raises `AttributeError` inside the `try` (recorded as `cause=bare_array`); and (v) a well-formed object with NO `triples`
key at all — `{"repairs": [...]}`, `{"note": "none found"}`, a provider answering in its
own vocabulary — for which `.get("triples", [])` returns `[]`, raising nothing and
touching no branch. The first extraction wraps a bare array into `{"triples": [...]}`;
the retry path does not, so the same provider answer is a recovery attempt on the first
call and a failure on the second (§10 Q4 — resolved at v5 as a 0025 amendment, §2e).
Paths (iii) and (v) matter for this spec's shape: a record emitted from inside the
`except` would miss both, and (v) is indistinguishable in every carrier that exists today
from a legitimately empty recovery — `{"triples": []}`, the one answer that is NOT a
degrade — which is exactly the indistinguishability this spec exists to end. (v) was
found by research on the second read, after the enumeration had been called complete
once — so this list is "the known ways", not a closed count; V-ANSWER-MATRIX
(§6) is what makes its completeness testable rather than asserted.

**1b. The unparseable extraction.** A provider answering in prose, refusing, or returning
a wrong-typed `instructions` field (0038 §2c row 2) raises `ValueError` from the JSON
extractor and takes the early return: a content-free placeholder episode,
`unparseable: True`, every counter present at zero. No exception escapes.

**1c. The volatility coercion — the worst of the three, and the one v1 missed.** For each
triple the extractor emitted, the volatility class is parsed from the model's string:

```
try:
    vol = Volatility(str(t.get("volatility", "durable")).strip().lower())
except ValueError:
    vol = Volatility.DURABLE
```

An ABSENT key takes the declared default without entering the handler — that is a
default, not a degrade. A PRESENT value outside the enum (`"banana"`, `"long-term"`, a
provider's own vocabulary) is silently coerced to DURABLE, per triple. There is no
counter for it, no report key, no log line, and the record it produces looks correct.
Volatility classes are one of the axes the paper names as a contribution; a provider
that consistently emits an unrecognised class makes every fact durable and nothing
anywhere says so. The other two degrades are visible as an ABSENCE (no facts, a
placeholder episode). This one is visible as nothing.

**1d. Where a record could have gone, and did not.** The library has a diagnostics
reporter (`diagnostics.Reporter`): a local, user-owned rotating log
(`$XDG_STATE_HOME/veracium/veracium.log`, default `~/.local/state/veracium/`; three files
of 1 MB — the current file and two backups) that records genuine errors with the
operation name, a hashed user id and the full traceback; the caller then re-raises
(`_on_error` itself never does). Three facts about
it, each a line in the tree:

| fact | where |
|---|---|
| `Memory(...)` takes `diagnostics=None` by default; the library core never creates a reporter implicitly | `__init__.py`, the constructor's signature and `diagnostics.load_reporter`'s docstring |
| the MCP entry point DOES attach one: `build_memory()` passes `diagnostics=diagnostics.load_reporter()`, a `Reporter` whenever `log_enabled` (the default) | `mcp_server.py`, `build_memory` — the one occurrence of `load_reporter` outside `diagnostics.py` |
| the CLI's two `Memory(...)` constructions attach NONE — `load_reporter` does not occur in `cli.py` | `cli.py`, both construction sites |

And the error hook is called from five operations (`remember`, `recall`, `answer`,
`maintain`, `introspect`) — only when an exception PROPAGATES. None of the degrade
paths calls it, so even the MCP server's attached reporter records nothing when a
provider fails during the retry, answers unparseably, or emits a volatility class the
enum does not know.

**1e. What the MCP host sees.** The tool result strips `retried`, `recovered`,
`residual`, `invalid` and `redispositioned` (0031 §4d, by design); `unparseable`
survives the strip. So a host embedding the MCP server has exactly one degradation
signal — `unparseable: True` — and none for the retry failure or the coercion.

**1f. The primary path, measured (v8, from round 1's F1 — run, not read).** Every shape
below was driven through `ingest_event` at HEAD with a scripted provider; the outcome is
the observable one. The first extraction's `triples` handling is `for t in
data.get("triples", []): if not (isinstance(t, dict) and t.get("subject") and
t.get("relation") and t.get("object")): continue` — a default on the missing key and a
per-member filter — and neither is an exception handler:

| primary answer | outcome at HEAD | classification |
|---|---|---|
| `{"triples": [well-formed]}` | 1 fact | normal |
| `{"triples": []}` | 0 facts, no flag | normal empty result |
| no `triples` key | 0 facts, no flag, no record | SILENT — a degrade |
| `triples` is a string | iterated as characters, every member skipped: 0 facts, no flag | SILENT — a degrade |
| `triples` is a dict | iterated as keys, every member skipped: 0 facts, no flag | SILENT — a degrade |
| `triples` is `null`, a number or a boolean | `TypeError: ... is not iterable` PROPAGATES; `remember` raises; `_on_error` records it with its traceback when a reporter is attached | propagated error (already recorded) |
| bare JSON array of well-formed dicts | wrapped into `{"triples": [...]}`: 1 fact | normal |
| a list whose members are not well-formed dicts | each member skipped: 0 facts, no flag | SILENT — a degrade, per member |
| non-object top-level JSON (a string, a number) | `extract_json` finds no object or array: `ValueError`, the unparseable placeholder | recorded as `unparseable` |
| prose; `instructions` of the wrong type | the unparseable placeholder | recorded as `unparseable` |

v4's row 3 said a wrong-typed `triples` "raises `AttributeError` outside the handler,
which propagates". It does not. The author read the loop and reasoned about it; the
reviewer ran it. Three of the ten cells were silent and one raised a different exception
than the sentence named. The rule this project carries — a load-bearing claim about
shipped behaviour is verified by execution — was not applied to the one paragraph whose
subject was shipped behaviour, and §6's batteries now exist so that it cannot be skipped
again: the batteries are the execution, kept.

**The consequence the owner named:** during ordinary use, a run of provider failures
shows up only as counters in return values nobody reads, in a log that the CLI never
opens and that no degrade path writes to; and a provider whose volatility vocabulary has
drifted shows up nowhere at all.

## 2. Behaviour

**2a. A degrade is RECORDED through the diagnostics reporter — never raised.** When a
reporter is attached, each degrade path produces a record. The record's fields are
CLOSED IN BOTH DIRECTIONS — nothing may be added without reopening this table, and
nothing declared for a record class may be omitted from its record (an absent key is not a
zero, 0025 §4c; V-RECORD-FIELDS-TOTAL asserts the exact set per CLASS, where a class is
the pair (`degrade`, `cause`) — v5, research's F2: the shape path has no exception and
therefore no message, and a field set declared per `degrade` alone would force two
fields with no defined value onto it):

| field | value | never |
|---|---|---|
| `op` | the operation (`remember`) | — |
| `degrade` | one of `retry_failed`, `primary_failed`, `unparseable`, `volatility_defaulted`, `member_skipped` — a closed vocabulary (v8 added the two the primary path needs) | any other string |
| `user_hash` | the hashed user id — the existing `_on_error` convention: the first 12 hex digits of the user id's SHA-256 | the user id |
| `cause` | a CLOSED vocabulary (v8, round-1 F4 — an exception's class name is NOT recorded, because a provider-defined class name can carry arbitrary text): `provider_error` (the provider call raised, whatever the class), `no_json` (the extractor found no JSON object or array), `instructions_type` (0038 §2c row 2), `shape` (`triples` present and not a list — a string, a dict, `null`, a number, a boolean), `no_triples_key` (a well-formed object without the key), `bare_array` (retry only, and only until §2e's 0025 amendment: the list reached `.get`). Present on `retry_failed`, `primary_failed` and `unparseable` records; absent on the two counted kinds. A wrong type and a wrong schema are different facts — ONE field with one honest meaning, so the operator's count of retry failures is one row of `degrade` (v5; was `exc_type`, a name the token `shape` made false) | any other token; the exception's message |
| `msg_len`, `msg_sha16` | ONLY when `cause` is `provider_error`: the UTF-8 BYTE length of `str(exc)`, and the first sixteen hex digits of SHA-256 over exactly those UTF-8 bytes (v8: units and bytes defined; the class name, `args`, `__notes__` and attributes are never read) | **the message text, in any form, at any length, redacted or not; the class name** |
| `answer_len`, `answer_sha16` | for every `cause` except `provider_error`: the UTF-8 byte length of the provider's raw answer exactly as the `Complete` callable returned it (before any parse), and the first sixteen hex digits of SHA-256 over those bytes — so the operator can match the provider's own log by digest. §8 states what a digest leaks | **the answer text, in any form** |
| `count` | for `volatility_defaulted`: how many triples in this `ingest_event` call were coerced; for `member_skipped`: how many list members the SHAPE GUARD dropped in this call — the `isinstance(t, dict) and t.get("subject") and t.get("relation") and t.get("object")` test on the primary answer and the `isinstance(rep, dict)` test on the retry answer — and NEVER a member refused by a rule after passing the guard (an off-vocabulary relation is `invalid`; a pipe-composed subject is `subject_refused`; both are counted already, and counting them here would be two counters for one event, v10 D1) | the offending value's text (it is model output) |

Why no message text, measured (§2c-i row 7): `diagnostics.redact` removes exactly four
shapes — an email, a US phone `ddd-ddd-dddd`, a run of seven or more digits, a dollar
amount — and preserves everything else (`555-0100` survives; so does every word). For a memory product
"everything else" IS the payload: "Alice moved to Berlin" survives redaction intact. A
redactor tuned for logs cannot protect a store whose entire content is the thing the
redactor does not recognise, so the record does not carry the message at all. An operator
who needs the provider's text has the provider's own logs and the digest to match it by.

The degrade paths' return values are unchanged: `retried/recovered/residual` and
`unparseable` mean exactly what 0025 says; the coercion still yields DURABLE. The hook
that writes the record is best-effort (0025's rule that logging never masks or delays the
real outcome applies to a degrade as it applies to an error).

**2b. The volatility path is aggregated, not per-triple.** ONE record per `ingest_event`
call, carrying `count`. A ten-triple event with a drifted provider emits one record, not
ten. §7 says why this is a retention rule and not a tidiness one.

**2c. The seam: a callback, not a field, invoked through ONE guarded helper.** `ingest_event`
gains a keyword-only parameter `on_degrade: Optional[Callable[[str, dict], None]] = None`.
No site calls it directly (v8, round-1 F2): every site calls `_emit_degrade(on_degrade,
kind, payload)`, a module-level helper that returns at once when the callback is `None`
and otherwise invokes it inside `try/except Exception: pass` — it never re-raises, never
logs, never retries, and a `BaseException` (a `KeyboardInterrupt`) is deliberately NOT
caught, which §9 hands the reviewer. The sites:
The PRIMARY site (v8) runs once the answer is a dict (a bare array having been wrapped):
`"triples" not in data` → `primary_failed`/`no_triples_key`; `not isinstance(data["triples"],
list)` → `primary_failed`/`shape` — RECORDED ONLY; the loop still runs over whatever the
value is and the outcome does not change (a string still yields zero facts; `null` still
raises `TypeError` before the record could be written, and is an error, §2c-i row P6).
The member filter's `continue` on either path increments one per-call counter, emitted
once after both loops as `member_skipped` with `count` when non-zero. The retry site
calls the helper ONCE, after the `try`/`except` block, on a failure flag set by any of
§1a's five paths — the `except` sets the flag with `provider_error`, `no_json` or
`bare_array` according to which line raised, the shape branch sets it with `shape`, the
missing key sets it with `no_triples_key` — tested as
`isinstance(data, dict) and "triples" not in data`, STRICTLY AFTER dict-ness is
established and never inferred from an empty result: on a list `in` is a MEMBERSHIP test,
not a key test (measured: a bare array of dicts tests False, a bare array containing the
string `"triples"` tests True), so a key check hoisted above the `.get` would silently
reclassify a bare array (path iv) as `no_triples_key`, make row 2c unreachable, and
pre-break §2e's amendment test — `cause=bare_array` would already be zero for an
unrelated reason — and never when the recovery
was legitimately empty
(`on_degrade("retry_failed", {...})`); the unparseable path calls it from its handler
(`on_degrade("unparseable", {...})`); and once after the triple loop
`on_degrade("volatility_defaulted", {"count": n})` when `n > 0`.
`Memory.remember` passes `self._on_degrade`, a sibling of `_on_error`, which calls
`Reporter.record_degrade`. The ingest RESULT does not change: 0025 X12 asserts its counter
keys are PRECISELY §4c's public set, and a private field on it would survive only by
exempting the invariant that makes the set closed. A degrade is an event, not a counter;
it travels on its own channel.

**2d. The CLI attaches a reporter as the MCP entry point does.** Both CLI `Memory(...)`
constructions pass `diagnostics=diagnostics.load_reporter()` — a `Reporter` iff
`log_enabled`, the same rule `build_memory()` uses. Only the `remember` construction can
emit a degrade record (the other runs with a stub provider that never extracts); it
attaches the reporter for `_on_error`, so the two constructions stay one rule. The library core's default stays
`None` (embedding hosts pass their own or none — the existing contract).

**2e. What changes, stated exactly.** `ingest.py`: the `on_degrade` parameter, the
`_emit_degrade` helper, the primary-answer check (two conditions, records only), the
per-call member counter, the retry flag, the unparseable and volatility sites — and ONE
normalization line at the retry site, which is an AMENDMENT TO 0025
§4b(1) and is stated as one (v5, from §10 Q4 re-argued): `_json.extract_json` returns a
bare JSON array "as a fallback for the caller to normalize" (its docstring); the first
extraction normalizes it into `{"triples": [...]}` and the retry caller does not, so one
of the function's two callers does not honour the documented obligation of the function
it calls — a contract-conformance defect, not a symmetry preference. The retry wraps a
bare array exactly as the first extraction does; a bare-array retry answer becomes a
recovery attempt. Row 2c stays: before the amendment lands its record is the only
evidence in production that the asymmetry occurs; the amendment's PROOF is the battery
assertion it flips in its own commit (V-ANSWER-MATRIX, v6), and the record's count
going to zero afterwards is corroboration. The commit carrying it references 0025 and this
spec. No other line. `__init__.py`: `Memory._on_degrade`, passed from `remember`.
`diagnostics.py`: `Reporter.record_degrade` writing the §2a record at WARNING level in
the same log, best-effort, incrementing the pending count and NEVER calling `send()` —
no network I/O, no prompt, no throttle check (v8, round-1 F3: `record_error` may
auto-send synchronously under advance permission with a 15-second HTTP timeout; a degrade
record is left pending for the next `send()` the host or the error path performs). `cli.py`: two constructions gain the `diagnostics=` argument.
**The MCP tool result is unchanged** (§10 Q1). **No stored byte changes; no schema, no
export, no migration.** The primary path's OUTCOMES are unchanged too: the three shapes
that raise `TypeError` today still raise it (§10 Q6 asks whether they should; that is an
ingest amendment, not this spec), and the silent shapes still yield zero facts — they
are now RECORDED, which is the whole of the change.

## 2c-i. Untrusted inputs — REQUIRED, blocking

The untrusted input is the BYO provider's exception and output. Every row states an
observable outcome and the invariant that enforces it.

| # | case | observable outcome | enforced by |
|---|---|---|---|
| 1 | the retry raises (network, provider, SDK) | ONE record `degrade=retry_failed cause=provider_error` with the message's byte length and digest — never the class name (row 7b); the return dict as 0025 specifies | V-DEGRADE-RECORDED, V-NO-CONTENT-IN-LOG, V-CAUSE-BOUNDED |
| 2 | the retry returns no JSON (prose, a refusal, a top-level scalar) | as row 1 with `cause=no_json`; NEVER the raw output — the extractor's own message embeds the first 200 characters of the answer, which is why the record carries length and digest only | V-NO-CONTENT-IN-LOG |
| 2b | the retry returns well-formed JSON whose `triples` is not a list — a string, a dict, or `null` (measured: `null` takes the shape branch, it does not raise) | ONE record `degrade=retry_failed cause=shape` (with the answer's length and digest, §2a) from the shape branch (§1a path iii — no exception is raised there); `retried > 0, recovered = 0` as today | V-DEGRADE-RECORDED |
| 2c | the retry returns a bare JSON array (of dicts or of scalars) | TODAY (asserted by the battery as the current state): `AttributeError` inside the `try`, `reps = []`, ONE record with `cause=bare_array`. AFTER §2e's 0025 amendment: normalized exactly as the first extraction does — a recovery attempt, NO record unless it then fails another way — and the battery's assertion flips in the amendment's commit; the record's count going to zero in the log is corroboration, not the proof | V-DEGRADE-RECORDED, V-ANSWER-MATRIX |
| 2d | the retry legitimately recovers nothing (`{"triples": []}`) | NO record — an empty list is an answer, not a failure; `recovered = 0` as today | V-DEGRADE-RECORDED's negative arm, V-ANSWER-MATRIX |
| 2e | the retry returns a well-formed OBJECT with NO `triples` key (its own vocabulary) | ONE record `degrade=retry_failed cause=no_triples_key` with the answer's length and digest; `retried > 0, recovered = 0` as today — today this answer is indistinguishable from row 2d. The check is `isinstance(data, dict) and "triples" not in data`, after dict-ness: a non-dict answer is row 2c, never this row | V-DEGRADE-RECORDED, V-ANSWER-MATRIX |
| 3 | the first extraction is unparseable (prose, a refusal, non-object top-level JSON such as a bare string or number) | ONE record `degrade=unparseable cause=no_json`; the placeholder episode as today | V-DEGRADE-RECORDED, V-ANSWER-MATRIX |
| P1 | the first extraction returns `{"triples": [well-formed]}` | facts; NO record | V-ANSWER-MATRIX |
| P2 | the first extraction returns `{"triples": []}` | zero facts; NO record — a normal empty result | V-ANSWER-MATRIX |
| P3 | the first extraction returns a well-formed object with NO `triples` key | zero facts as today; ONE record `degrade=primary_failed cause=no_triples_key` with the answer's length and digest — today this is silent | V-ANSWER-MATRIX, V-DEGRADE-RECORDED |
| P4 | `triples` is a string or a dict | iterated and every member skipped, zero facts as today; ONE record `degrade=primary_failed cause=shape` — today this is silent (v4 said it raised; it does not) | V-ANSWER-MATRIX |
| P5 | a list whose members are not well-formed dicts (a bare array of scalars; a triple missing `object`) | each member skipped as today; ONE record `degrade=member_skipped count=n` per call — today silent | V-ANSWER-MATRIX, V-ONE-RECORD-PER-CALL |
| P6 | `triples` is `null`, a number or a boolean | `TypeError` PROPAGATES as today — a propagated ERROR, recorded by `_on_error` with its traceback when a reporter is attached, and `remember` raises; NO degrade record (the primary check records `shape` before the loop, but the loop then raises and the operation is an error, not a degrade — the record's presence beside the error is asserted). Whether these three should stop raising is §10 Q6 | V-ANSWER-MATRIX |
| P7 | a bare JSON array of well-formed dicts | wrapped into `{"triples": [...]}` as today; facts; NO record | V-ANSWER-MATRIX |
| 4 | `instructions` of the wrong type (0038 §2c row 2) | as row 3 — the extractor's `ValueError` is the same exception class; the record does not say which shape failed, by design (the message would) | V-DEGRADE-RECORDED, V-NO-CONTENT-IN-LOG |
| 5 | a triple carries a volatility value outside the enum — a PRESENT `null` included (`str(None)` is `"none"`, outside the enum) | coerced to DURABLE as today; ONE record `degrade=volatility_defaulted count=n` per `ingest_event` call; the VALUE's text appears nowhere | V-DEGRADE-RECORDED, V-ONE-RECORD-PER-CALL, V-NO-CONTENT-IN-LOG |
| 6 | a triple carries NO volatility key | the declared default; NO record — this is not a degrade (absence; row 5's `null` is presence) | V-DEGRADE-RECORDED's negative arm |
| 7 | the exception message carries content (a provider echoing the prompt into an error) | the record carries the message's byte length and digest and NOTHING of its text — redaction is not consulted, because it preserves the semantic payload (measured: "Alice moved to Berlin" survives `redact`) | V-NO-CONTENT-IN-LOG |
| 7b | a provider-defined exception whose CLASS NAME, `args`, `__notes__` or attributes carry content (v8, round-1 F4) | `cause=provider_error` — the class name is never recorded; only `str(exc)`'s length and digest are read; nothing of the name or attributes appears anywhere in the log | V-CAUSE-BOUNDED, V-NO-CONTENT-IN-LOG |
| 7c | two records for the same message or answer | equal digests: the record REVEALS EQUALITY between records, and for a low-entropy text lets a holder of the log confirm a guess; acknowledged in §8, accepted because the log is local and user-owned, sent only under consent, and matching the provider's own log is the digest's purpose (a keyed digest, §10 Q5, would defeat it) | V-NO-CONTENT-IN-LOG (the bound is stated, not narrowed) |
| 8 | no reporter attached (an embedding host passing `None`; the CLI today) | no record, no exception, no change in behaviour — `on_degrade` is `None` and the sites do not call it | V-NEVER-RAISED-BY-RECORDING |
| 9 | the reporter itself fails (disk full, path unwritable) | swallowed inside the reporter (its existing contract: "nothing here re-raises"); the operation's outcome is unchanged | V-NEVER-RAISED-BY-RECORDING |
| 9b | the CALLBACK raises (an embedding host's `on_degrade`, or a bug in `Memory._on_degrade`) — at the retry site, the unparseable site, the volatility site, the primary site, the member site (v8, round-1 F2) | contained by `_emit_degrade`: the return dict and every stored byte identical to the same run with `on_degrade=None`; no site may call the callback except through the helper | V-CALLBACK-CONTAINED |
| 9c | a reporter with advance permission, an endpoint and the auto-send interval elapsed (v8, round-1 F3) | `record_degrade` performs NO network I/O and no prompt — the record is written locally and left pending; only `record_error`'s path and the host's `send()` may send | V-NO-INLINE-SEND |
| 10 | a degrade storm (every call fails; every triple drifted) | one record per call per path, bounded by the log's rotation (§7); no auto-send unless the operator pre-authorized it, throttled by `report_min_interval_s` (existing) | V-ONE-RECORD-PER-CALL; the reporter's existing bounds |

## 2c-ii. The answer matrix — one table, two call sites (v9)

Every provider answer shape, with its classification on the FIRST extraction and on the
RETRY, measured at HEAD on two instruments — dev's shape-driving script and research's,
written independently in the two seats' scratch areas, outside this tree; the OWED
matrix test is the execution kept. A row whose two cells differ is marked ⚠ and is either 0025's
design or an undesigned difference this spec RECORDS and §10 Q4 proposes to settle. The
column "after v8" says what this spec adds — a record, never a changed outcome. This
table is canonical; §2c-i's P-rows and the retry rows restate it.

| # | answer shape | first extraction, today | retry, today | after v8 |
|---|---|---|---|---|
| 1 | `{"triples": [well-formed]}` | facts | recovery | no record |
| 2 | `{"triples": []}` | zero facts, no flag | no recovery | no record — normal empty |
| 3 | well-formed object, NO `triples` key | silent zero facts | silent no recovery | `primary_failed`/`no_triples_key` · `retry_failed`/`no_triples_key` |
| 4 | `triples` is a string | silent zero facts (iterated as characters, each skipped) | silent (shape branch) | `primary_failed`/`shape` · `retry_failed`/`shape` |
| 5 | `triples` is a dict — a nested `{"triples": {"triples": [...]}}` included | silent zero facts (iterated as keys) | silent (shape branch) | `primary_failed`/`shape` · `retry_failed`/`shape` |
| 6 ⚠ | `triples` is `null` | `TypeError` PROPAGATES — an error | silent (shape branch) | first: the error, recorded by `_on_error`, plus the `shape` record written before the loop; retry: `retry_failed`/`shape` — an UNDESIGNED asymmetry (Q4/Q6) |
| 7 ⚠ | `triples` is a number or a boolean | `TypeError` PROPAGATES | silent (shape branch) | as row 6 |
| 8 ⚠ | bare JSON array of well-formed dicts | wrapped, facts | `AttributeError` inside the `try`, no recovery | first: no record; retry: `retry_failed`/`bare_array` — UNDESIGNED (the callee's docstring obliges both callers to wrap; one does) |
| 9 ⚠ | bare JSON array of scalars | wrapped, every member skipped, zero facts | `AttributeError`, no recovery | first: `member_skipped`; retry: `bare_array` — UNDESIGNED, and a different row from 8 (H3) |
| 10 | a list with members that FAIL THE SHAPE GUARD (`[{}, {}]`; `[valid, "junk", 7, null]` storing one fact and skipping three with `invalid: 0`, measured) — NOT members a rule refuses after passing it (an off-vocabulary relation → `invalid`; a pipe subject → `subject_refused`; both counted today) | guard failures skipped silently | guard failures skipped silently (the pool loop) | `member_skipped count=n`, one record per call over both loops, shape-guard failures only (v10 D1) |
| 11 | non-object top-level JSON (a string, a number), or prose | `unparseable` placeholder | no recovery | `unparseable`/`no_json` · `retry_failed`/`no_json` |
| 12 | `instructions` of the wrong type (0038 §2c row 2) | `unparseable` placeholder | not examined on the retry — MEASURED on both instruments (v10) over the field's WHOLE domain: a retry answer carrying `instructions` as a string, as a list, or not at all recovers unchanged, `recovered: 1` in all three states (a negative claim is only as good as the domain it was checked over) | `unparseable`/`instructions_type` · — |
| 13 ⚠ | the provider CALL raises | the exception PROPAGATES — an error (MEASURED, v10: a `RuntimeError` from the first `Complete` call reaches `ingest_event`'s caller after one call) | swallowed, no recovery (0025 §4b(1)) | first: `_on_error` records it; retry: `retry_failed`/`provider_error` — 0025's DESIGN, not a defect |

Five asymmetric rows: one designed (13), four undesigned (6, 7, 8, 9). The four share one
cause — the first extraction normalizes what it receives and the retry does not, or the
reverse — and one amendment to 0025 settles all four (§10 Q4, which absorbs Q6).

## 3. Trust-class matrix — REQUIRED, blocking

Unchanged. No record's trust class, disclosure or assertability moves. The degrade
record is operator telemetry about the extractor, not a memory record. The coerced
volatility is stored exactly as today.

## 3b. Authorization — REQUIRED

No authorization decision keys on any of this. The record carries a hashed user id (the
existing `_on_error` convention) and no content; it crosses no scope boundary that the
error log does not already cross. `_disclosure_for` is untouched.

## 4. The field-consumer table — REQUIRED (guarded surfaces)

`ingest.py` and `__init__.py` are guarded (`check_spec_reference.py`'s `GUARDED`), so this
section is required.

| field / surface | who writes it | who READS it | reachability |
|---|---|---|---|
| the degrade record (log line, §2a's closed fields) | `Reporter.record_degrade`, called by `Memory._on_degrade` | the operator, by reading the log; `veracium diagnostics report`'s tail (existing, consented, redacted) | a log line; never persisted in the store; never returned |
| `on_degrade` (the callback) | `Memory.remember` supplies it; `ingest_event` calls it at three sites | nothing else — it is not stored, not returned, not exported | the ingest result's key set is unchanged and 0025 X12's exact-set test proves it |
| `diagnostics=` on the CLI's `Memory(...)` | `cli.py` | `Memory`'s existing attribute | the same object the MCP entry point already attaches |

**Reachability evidence.** The three catching degrade sites are the ONLY exception
handlers in `ingest.py` that continue after catching (the census, V-CENSUS: four handlers;
three continue; one re-raises); the two silent primary-answer shapes are a `.get` default
and a per-member `continue`, which no handler census sees and the two batteries test by
outcome (§6). Every other exception propagates to `_on_error`.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| provider healthy, schema followed | no degrade record; unchanged |
| provider fails during the retry | today: counters only; after: counters AND one record with the exception type |
| provider answers unparseably | today: `unparseable: True`; after: the same AND one record |
| provider's volatility vocabulary has drifted | today: every fact DURABLE, nothing anywhere; after: the same facts AND one record per call with the count |
| CLI use | today: no log at all (no reporter — every degrade invisible); after: the same log the MCP server writes |
| embedding host passing `diagnostics=None` | unchanged: no log, no record — the host owns its own error handling |
| MCP host | unchanged tool result; the operator's log gains the degrade records |

## 6. Invariants and executable checks — REQUIRED, blocking

| id | invariant | check | node |
|---|---|---|---|
| **V-CENSUS** | `ingest.py` has exactly the three continuing exception handlers §1 names (the retry, the unparseable return, the volatility coercion) and every other handler re-raises; AND exactly the one guarded literal-reset branch §1a path iii names (an assignment of an empty or default literal inside a branch whose test is an `isinstance` or truthiness check over parsed provider output, within `ingest_event`'s extraction and retry blocks); a NEW site of either shape fails this node until the spec names it. **LIMIT (v5, research's F1 and follow-up; v8, round-1 F1):** the census answers "where does this code shape appear", not "where can provider output be silently discarded" — an OUTCOME question no static rule answers. The primary path's two silent discards — a `.get("triples", [])` default and a per-member `continue` — are neither handler nor literal reset, and the census did not see them; the round-1 reviewer did, by running the code. It detects these TWO shapes and no third; path v (a missing key, no branch at all) is invisible to it, as path iii was to the v3 census, and six ordinary spellings evade the second shape (an IfExp or `or []`; a guard assigning an ENUM member — the volatility default rewritten as a guard would match neither shape; a binding one hop further; a parser that is not `extract_json`; a helper extracted out of `ingest_event`; a member-level filter). The node closes the two known spellings; V-ANSWER-MATRIX below tests the outcome | an AST walk over every `ExceptHandler`: classify by whether its body (transitively) raises; assert the continuing set equals the named three; PLUS a walk over every `If` inside `ingest_event` whose test is an `isinstance(...)`/`not ...` over a name bound from `extract_json`, asserting the set of literal-reset assignments in its body equals the named one — by enclosing function and caught type | OWED at implementation: `tests/test_0039_degradation_visibility.py::test_the_census_names_every_continuing_handler` |
| **V-ANSWER-MATRIX** | (v9, absorbing the two v8 battery invariants, which were named V-PRIMARY-ANSWER-BATTERY and V-RETRY-ANSWER-BATTERY before the merge — a mention, not a use, and v9's rename swept it; restored at v10, D2) §2c-ii is asserted as ONE table: for every row, the first-extraction cell AND the retry cell hold by exact equality, and no two rows share a classification on a column unless the table says so; an asymmetric row is asserted AS asymmetric, so the 0025 amendment that removes one must flip the row in its own commit. The retry column, as it stood before the merge (all MEASURED at HEAD, v8): raising → `cause=provider_error`; prose or a top-level scalar → `no_json`; bare array of dicts or of scalars → `cause=bare_array` — the CURRENT state, asserted as such; §2e's amendment flips this one assertion to "normalized, a recovery attempt (or `member_skipped` for scalars)" in the same commit that adds the wrap, so the test change is the amendment's proof (v6 — a row that reads "or" passes on both sides of the change it brackets); `triples` a string, a dict or `null` → `shape`; no `triples` key → `no_triples_key`; `{"triples": []}` → no record; `{"triples": [dicts]}` → recovery; and the first-extraction column as §2c-ii's rows 1–13. The arm that tests the OUTCOME rather than the spelling — it would have caught paths iii and v without anyone thinking of them first, and every evasion in V-CENSUS's limit is a different spelling of the same outcome | a scripted provider per answer shape at the retry; the record (or its absence) read back and compared to this row's table by exact equality; a NEW shape the reviewer names is added to the battery, not argued | OWED: `tests/test_0039_degradation_visibility.py::test_the_answer_matrix_holds_on_both_call_sites` |
| **V-CALLBACK-CONTAINED** | (v8, round-1 F2) every degrade site invokes the callback ONLY through `_emit_degrade`, and a callback that raises changes nothing: for each of the five sites, a run with `on_degrade=lambda *_: (_ for _ in ()).throw(RuntimeError("x"))` returns a dict equal to the run with `on_degrade=None` and leaves the store's bytes identical | static: an AST census of `ingest.py` finds no `Call` whose function is the name `on_degrade` outside `_emit_degrade`'s body; dynamic: the five raising-callback runs with result-dict equality and a sha256 over the store file | OWED: `::test_a_raising_callback_changes_nothing_at_any_site` and `::test_no_site_calls_the_callback_directly` |
| **V-NO-INLINE-SEND** | (v8, round-1 F3) `Reporter.record_degrade` performs no network I/O and no prompt under any configuration: with `report_enabled`, an endpoint, and the auto-send interval elapsed, a poster injected in place of `_post` is called ZERO times across every degrade path, while the same reporter's `record_error` in the same configuration calls it once (the control) | the poster mock; both counts asserted | OWED: `::test_record_degrade_never_sends_inline` |
| **V-CAUSE-BOUNDED** | (v8, round-1 F4) every record's `cause` is a member of §2a's closed set; a provider exception whose class name, `args`, `__notes__` and attributes all contain a sentinel yields `cause=provider_error` and NO occurrence of the sentinel anywhere in the log | the sentinel exception, raised at the retry; the log read back | OWED: `::test_cause_is_a_closed_vocabulary_and_a_provider_exception_name_never_reaches_the_log` |
| **V-DEGRADE-RECORDED** | with a reporter attached, each recorded path writes exactly ONE record per occurrence (per call for the two counted kinds), naming the kind in §2a's closed vocabulary; an absent volatility key, an empty `triples` list and a well-formed answer write NONE | scripted providers: one raising on the retry; one returning prose; one returning a wrong-typed `instructions`; one emitting `"banana"` for every triple; one omitting the key — the log read back | OWED: `::test_retry_failure_writes_one_record`, `::test_unparseable_writes_one_record`, `::test_drifted_volatility_writes_one_record_with_the_count`, `::test_an_absent_volatility_key_writes_nothing` |
| **V-NO-CONTENT-IN-LOG** | no record contains ANY substring of the event text, of the model's output, or of the provider's exception message beyond its length and digest | a provider whose exception message and whose triple values echo the event text and a sentinel; assert no sentinel, no event-text token and no message substring longer than three characters appears in the log | OWED: `::test_the_record_carries_no_content` |
| **V-ONE-RECORD-PER-CALL** | the volatility path writes one record per `ingest_event` call regardless of triple count | a ten-triple event, every triple drifted: one record, `count` equal to the number coerced | OWED: `::test_volatility_records_aggregate_per_call` |
| **V-RECORD-FIELDS-TOTAL** | for each record CLASS (`degrade`, `cause`), the record carries EXACTLY its declared field set (§2a): `retry_failed`/`provider_error` → `op, degrade, user_hash, cause, msg_len, msg_sha16`; every other `retry_failed`, `primary_failed` and `unparseable` class → `op, degrade, user_hash, cause, answer_len, answer_sha16`; `volatility_defaulted` and `member_skipped` → `op, degrade, user_hash, count`; asserted as exact set equality per class, never a subset check; a `msg_*` field on a `shape` record or an `answer_*` field on an exception record fails | each scripted provider's record read back; the key set compared for equality against the declared set for its type | OWED: `::test_each_record_carries_exactly_its_declared_fields` |
| **V-NEVER-RAISED-BY-RECORDING** | recording never changes the operation's outcome: no reporter → identical return; a failing reporter → identical return; a failing CALLBACK → identical return and identical stored bytes (V-CALLBACK-CONTAINED is the direct test; this row inherits it) | the same scripted providers with `diagnostics=None` and with a reporter whose log path is unwritable; the return dicts equal the recorded ones | OWED: `::test_recording_never_changes_the_outcome` |
| **V-CLI-ATTACHES** | both CLI `Memory(...)` constructions pass `diagnostics=load_reporter()` | an AST census of `Memory(` calls in `cli.py`: every one carries the argument | OWED: `::test_every_cli_memory_construction_attaches_a_reporter` |
| **V-RESULT-UNCHANGED** | the ingest result's key set is exactly the set X12 pins at HEAD (0025 §4c's counters as amended 2026-09-08, 0038's `instructions_dropped`, 0023 Q4's two audit facts, 0026's two agreement counters); nothing of the degrade travels on it | INHERITED from `tests/test_0025_enforcement.py`'s X12 exact-set test | CHECKED today (the existing node) |
| **V-MCP-RESULT-UNCHANGED** | the MCP tool result gains no field | INHERITED from `tests/test_0031_phase_a.py`'s strip test and the result's existing shape tests | CHECKED today |

**Mutants the matrix must kill:** recording via `print`/stderr instead of the reporter
(the CLI-without-reporter regime would still see nothing persistent); a record carrying
the message text, capped or redacted (row 7 — the redaction inversion); a per-triple
volatility record (V-ONE-RECORD-PER-CALL); a record on an absent volatility key (row 6);
a degrade that raises when the reporter fails (row 9); the CLI attaching a reporter in one
construction and not the other; a fourth continuing handler added to `ingest.py` without
a spec row (V-CENSUS); the degrade fact placed on the ingest result (X12 kills it today);
a `volatility_defaulted` record with no `count`, a `retry_failed` record with no
`cause`, a `shape` record carrying `msg_len`, an exception record carrying `answer_len`,
a record carrying another class's field (V-RECORD-FIELDS-TOTAL — the omission direction,
which no other row constrains); a second guarded literal-reset branch added to the retry
block without a spec row (V-CENSUS's second shape); a wrong-key answer classified as
`shape`, or as a non-degrade, or two answer shapes sharing a `cause` the table separates
(V-ANSWER-MATRIX); the missing-key flag inferred from `reps == []` rather than
from the key test (it would mark a legitimately empty recovery as a degrade — row 2d
kills it); the key test run before dict-ness or on a non-dict (a bare array classified
`no_triples_key`, row 2c unreachable, the amendment's test pre-broken — the battery's
bare-array shape kills it).

### 6a. Acceptance measurement — REQUIRED, FINITE

Every invariant above is either CHECKED today by an existing node or OWED at a named
node; the table's last column says which, row by row, and no count is stated in prose.
Acceptance is the OWED nodes existing and passing, plus a manual run: the CLI against a
scripted provider that fails the retry and one whose volatility vocabulary has drifted,
then `cat` of the log, showing one record of each.

## 7. Failure modes and reversibility

- **Reversible.** Removing the three callback sites, the parameter and the CLI arguments
  restores today's behaviour byte-for-byte; no stored state is touched.
- **Retention, not size — the question §7 must answer.** The log window is **3 MB:
  1 MB × 3 files** — the active file and its two backups (`maxBytes=1_000_000,
  backupCount=2`; the count is stated beside the size because "backupCount=2" reads as
  two files and means three). Before 0039, how long a real traceback survives in that
  window depends on ERROR volume. After 0039 it depends on DEGRADE volume too: every
  degrade record is bytes a traceback will rotate out behind. That is why the volatility
  path is one record per call and not per triple (§2b) — at per-triple volume a drifted
  provider would evict the errors the log exists for. The figures to quote are the
  DERIVED ones — records per window, and events to evict a traceback at a stated degrade
  rate — measured at implementation from the record's actual size and stated in the
  CHANGELOG with their conditions; the window size alone answers the wrong question.
- **The log can be sent — later, never from the degrade path.** Only under the existing
  consent flow, redacted, capped, and only from `record_error`'s pre-authorised auto-send
  or the host's `send()`: `record_degrade` leaves its record pending and performs no I/O
  beyond one local log write (v8, round-1 F3). This spec adds records to that log and
  therefore to what a consented send may carry — §2a is why the record carries no text by
  CONSTRUCTION, not by redaction: redaction was measured and preserves the payload.

## 8. Claims and limits

**This spec does not make a degrade an error.** 0025's contract stands: a provider
failure during the retry is a no-op with counters; an unrecognised volatility is DURABLE.
What changes is that each fact is also written where an operator looks.

**This spec does not tell the MCP host more.** The tool result is unchanged (§10 Q1).

**A host that passes `diagnostics=None` learns nothing new.** That is the existing
library contract and the right default for an embedding host with its own logging.

**The strongest argument for this spec is a limit of the shipped product, stated
plainly:** the CLI attaches no reporter today, so EVERY degrade is invisible to a CLI
user — including the volatility coercion, which has been silently defaulting a flagship
axis, with no counter, for as long as the handler has existed. Nothing in the tree could
have told an operator. This spec is the first carrier of that fact.

**What the record cannot tell the operator:** WHICH shape failed (row 4), WHAT the
drifted value was (row 5), WHAT key the provider used instead of `triples` (row 2e), or
WHICH exception class the provider raised (row 7b — `cause=provider_error` only).

**What the digest leaks, stated (v8, round-1 F4).** `answer_sha16`/`msg_sha16` are the
first sixteen hex digits of an UNKEYED SHA-256 over the stated UTF-8 bytes, and
`answer_len`/`msg_len` are UTF-8 byte counts. Two records with the same text have the
same digest: the log reveals EQUALITY between events, and a holder of the log can confirm
a guess at a low-entropy text (a short refusal string, a fixed error message). Accepted,
not argued away: the log is local and user-owned, it is sent only under consent, and the
digest's one purpose — matching the provider's own log for the same call — needs the
unkeyed form. §10 Q5 records the keyed alternative and why v8 does not take it.

**The three shapes that raise still raise.** A `null`, numeric or boolean `triples` on
the first answer is a `TypeError` today and after this spec; it is a propagated error the
error hook already records, and making it a degrade would change an outcome, which this
spec does not do (§10 Q6). Both would require carrying model output; both are recoverable
from the provider's own logs by the digest and the timestamp.

## 9. Brief for the external reviewer

Attack, in order: **V-NO-CONTENT-IN-LOG's and V-CAUSE-BOUNDED's tests**, because "no
substring" is a claim about a test's sentinel — round 1 named the exception's `repr`,
`args`, `__notes__` and the class name, and v8 reads none of them, so look for the
carrier v8 did not name; **`_emit_degrade`'s containment boundary**, which catches
`Exception` and deliberately not `BaseException` — a callback raising `KeyboardInterrupt`
or `SystemExit` propagates, by design, and if the reviewer thinks the boundary is wrong
that is a one-word finding; **the primary battery's P6 row**, which records `shape` and
then lets the `TypeError` propagate — the record beside the error is asserted, and a
reviewer may prefer no record on an error path; **V-NO-INLINE-SEND's control**, which
relies on `record_error` sending once in the same configuration — if the throttle state
leaks between the two calls the control is not a control;
and **V-CENSUS's classifier**, because "the handler's body transitively raises" is a
static property and a handler that continues on one branch and raises on another is
neither cell — and because §6 admits the census answers a shape question, not the
outcome question; **V-ANSWER-MATRIX** is the outcome test, its seven answer
shapes are listed, and the reviewer is invited to name an eighth (two were found on
successive internal reads after the enumeration had twice been called complete). §1c's ranking — the coercion is worse than the two absences — is an
argument, not a measurement; disagree with it if the paper's axis claim does not bear
the weight.

## 10. Open questions

1. **Should the MCP tool result carry a single `degraded: bool`?** 0031 §4d strips the
   counters because refusal counts teach a model to probe; a boolean that says only "this
   write was degraded" is a smaller signal than `unparseable: True`, which is already
   exposed. Not decided here; the default is NO new field.
2. **Should `residual > 0` alone be recorded?** A residual can arise with a healthy
   provider (a triple no relation fits). This spec records only the FAILED retry (an
   exception or malformed output), not a residual the provider legitimately produced.
3. **Should the volatility record carry the drifted value's ENUM-DISTANCE or shape class**
   (a known synonym such as `long-term`, versus noise)? It would help an operator fix a
   prompt; it would also be the first byte of model output in the log. v2 says no; the
   reviewer may weigh it.

4. ~~Should the retry path wrap a bare JSON array as the first extraction does?~~ —
   **RESOLVED at v5 as a 0025 amendment, drafted in §2e; WIDENED at v9 (research, H2):**
   the matrix (§2c-ii) shows the two call sites disagree on FOUR undesigned shapes, not
   one — `null`, a number or boolean, a bare array of dicts, a bare array of scalars —
   each a defect or a deliberate difference nobody wrote down. The amendment should be
   ONE normalization rule shared by both callers (wrap a bare array; treat every non-list
   `triples` as one recorded `shape`, no exception), which settles all four and absorbs
   Q6. The original argument stands: v4 framed it as a symmetry
   question and left the behaviour as shipped; research's v4 read reframed it: the
   callee's docstring obliges the caller to normalize, and one of two callers does not —
   a contract-conformance defect, which is the kind of justification an amendment to an
   accepted spec needs. Row 2c stays as the evidence.

5. **(v8, round-1 F4) Should the digest be keyed?** An HMAC with a per-install secret
   would remove the equality/guessing leakage §8 states. v8 does not take it: the
   digest's purpose is matching the provider's own log for the same call, which a keyed
   digest defeats, and the log is local, user-owned and consent-sent. If the reviewer
   weighs the leakage above the match, the field becomes keyed and loses that purpose.
6. **(v8, round-1 F1; absorbed into Q4 at v9) Should a `null`, numeric or boolean `triples` on the first answer
   stop raising?** Today it is a `TypeError` that reaches the host while a string in the
   same position is a silent zero-fact result; the difference is iterability, not a
   property anyone chose. Making all non-list values one recorded degrade is a one-line
   change to a guarded file under accepted 0025's extraction contract — an amendment, like
   Q4 — and this spec records the inconsistency (row P6) and leaves the outcome as shipped.

*Closed at v2: the seam (callback, by 0025 X12 — §2c).*

## Reviewer checklist

- [ ] every claim in §1 is a line in the tree at the pinned commit; the census (V-CENSUS) is RUN and names three continuing handlers and one re-raising
- [ ] every degrade path's RETURN value is unchanged (0025 X12's exact-set test still passes; the callback adds no key; the primary path's three raising shapes still raise)
- [ ] the MCP tool result is unchanged (0031 §4d's strip test still passes)
- [ ] no degrade record can carry event text, model output or the exception message's text (row 7's mutant — the redaction inversion is measured, not argued)
- [ ] the volatility path writes one record per call, and none for an absent key
- [ ] each record carries EXACTLY its class's (`degrade`, `cause`) declared field set — the omission mutants (no `count`; no `cause`) and the cross-class mutants (`msg_len` on a `shape` record; `answer_len` on an exception record) fail, not only the addition mutant
- [ ] recording never changes an outcome, with or without a reporter, with a failing reporter, with a failing CALLBACK at every one of the five sites (results equal; stored bytes identical)
- [ ] every primary-answer shape in §1f/§2c-i P1–P7 has exactly its classification, and the propagated-error cells are the three named
- [ ] `record_degrade` sends nothing inline under advance permission with an endpoint and an elapsed interval; `record_error` in the same configuration is the control
- [ ] `cause` is closed; a provider exception whose class name and attributes carry the sentinel leaves nothing of it in the log; lengths are UTF-8 bytes and digests are over the stated bytes
- [ ] the CLI attaches a reporter at every `Memory(...)` construction
