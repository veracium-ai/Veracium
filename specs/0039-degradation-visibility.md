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
| **Version** | **v4 — DEV'S §3a CODE-REALITY READ FOLDED (2026-09-09, on Quentin's word "let's do spec 0039 for an internal read").** Every §1 claim re-verified at HEAD `b3c67d2` after 0037, 0025 v14 and 0038 landed on `ingest.py`: the census still returns four handlers (L114 re-raises; L294, L443, L503 continue); `Memory(diagnostics=None)`; `_on_error` at five sites, the CALLER re-raising; `load_reporter` in `build_memory` only; two CLI constructions, neither attaching; `RotatingFileHandler(maxBytes=1_000_000, backupCount=2)`; `redact` measured. ONE SUBSTANTIVE FINDING (D1): the retry site reaches `reps = []` FOUR ways and only two of them are exceptions — a well-formed answer whose `triples` is not a list is a shape branch that raises nothing, so a record emitted from the `except` would miss it; and the retry path lacks the bare-array wrap the first extraction has, so a bare JSON array answer is `AttributeError`, not recovery (§10 Q4, not changed here). §2a/§2c/§2c-i rows 2–3 restated for it; the retry record is emitted ONCE after the block on a failure flag, never on a legitimately empty recovery. Eight smaller corrections: a present `null` volatility is a drift (row 5); a wrong-typed first-extraction `triples` is an ERROR, not a degrade (row 3); the extractor's own message embeds `text[:200]` of provider output (row 7's measured instance); `redact`'s four patterns named; `user_hash` is sha256's first 12 hex; only the CLI's `remember` construction can emit a degrade record; V-RESULT-UNCHANGED phrased as the set X12 pins at HEAD. *(was v3 — RESEARCH'S v2 READ FOLDED (2026-09-07, same day).)** Read against the shipped paths at the v2 commit, not against v2's prose: the volatility handler sits inside the per-triple loop (so §2b's per-call count is derivable); `_on_error` exists with three call sites; X12's test says PRECISELY; `cli.py` has exactly two `Memory(...)` constructions. ONE finding, taken whole: **§2a's field table was CLOSED IN ONE DIRECTION ONLY.** "Nothing else may be added" and a mutant list that killed additions — and NOTHING forbade an OMISSION: a `volatility_defaulted` record with no `count`, a `retry_failed` record with no `exc_type`, satisfied every §6 invariant, because V-DEGRADE-RECORDED asserts existence and cardinality, V-NO-CONTENT-IN-LOG asserts absence, and none asserted the field SET. 0025 §4c had already named why it matters — *an absent key is not a zero* — for counters; a degrade record is where it applies next. **V-RECORD-FIELDS-TOTAL** (§6): for each `degrade` value the record carries EXACTLY its declared field set, asserted as exact set equality per degrade type, never a subset check; mutants: a record missing `count`; one missing `exc_type`; one carrying another type's field. The fourth invariant of the day found constraining one direction only (V-NEVER-HEAD over results; V-NO-EXISTENCE-SIGNAL by hiding everything; the withdrawn register catching uses not mentions; this) — the tell is a rule that names what must NOT happen without naming what MUST. Also §7: the window stated with its FILE COUNT beside the size — **3 MB (1 MB × 3 files: the active file and `backupCount=2`)** — because "backupCount=2 means three files" is the off-by-one that produced a wrong headline in the read that got the retention arithmetic right; and §7 now says the derived retention figure (records per window; events to evict a traceback) is the number to quote, since the retention claim is the section's subject and does not depend on getting a unit right. Credits: research (veracium-research-32), second read. *v2 — RESEARCH'S FIRST READ FOLDED (2026-09-07, same day as v1).* Four changes, each from a check EXECUTED against the shipped code rather than read from v1's description of it. **(1) A THIRD degrade path.** v1 said the two named sites were "the ONLY places ingest continues after a provider failure" and proposed an except-clause census as the proof; the census, run by both seats independently and converging, found FOUR handlers of which THREE continue: the two v1 named and `except ValueError: vol = Volatility.DURABLE` — a model-emitted volatility value outside the enum is silently coerced to DURABLE, per triple, with no counter, no record and no warning. v1's sentence survived on a strict reading ("provider *failure*") and failed the spec's purpose; §1 is widened from provider failure to **provider-originated degradation** and the volatility coercion is ranked WORST of the three, because the other two degrade into a visible absence and this one produces a record that looks correct, on an axis the paper names as a contribution. **(2) The record carries NO message text.** v1's "capped and redacted" was measured: `diagnostics.redact` on a provider error echoing a prompt removes the email and the phone number and keeps "Alice moved to Berlin" — it strips PII-SHAPED TOKENS and preserves the SEMANTIC PAYLOAD, which for a memory product is backwards (the fact IS the payload). The record is now the exception TYPE, the message LENGTH and a digest — never the text (§2a, §2c-i row 7, V-NO-CONTENT-IN-LOG). **(3) The seam is a callback, decided by 0025 X12.** v1 left open whether the degrade fact travels as a private field on the ingest result or as a callback on `ingest_event`'s signature; X12 asserts the result's counter keys are PRECISELY §4c's public set, so a private field survives only by exempting the invariant that makes the set closed. Callback (§2c; old Q2 closed). **(4) §7 answered the wrong question.** "Bounded by rotation" is a SIZE bound; the operator's question is RETENTION — after 0039 how long a real traceback survives depends on DEGRADE volume, and a per-triple record on the volatility path would evict the errors the log exists for. The volatility path is aggregated to ONE record per `ingest_event` call with a count (V-ONE-RECORD-PER-CALL); §7 states the retention consequence with the window re-derived from the handler's parameters. Also added to §8 as the spec's strongest argument, previously implicit: the CLI attaches NO reporter today (`load_reporter`: zero occurrences in `cli.py`, one in `mcp_server.py`), so every degrade — the volatility coercion included, for as long as it has existed — is invisible to a CLI user until this ships. Credits: research (veracium-research-32), first reader under PROCESS §3a: the census run, the redaction inversion framing, the X12 ruling, the retention arithmetic, the §8 limit. *v1 (2026-09-07) — THE DRAFT, written from the shipped code: the two ingest paths that record a failure instead of raising it, the library's `diagnostics=None` default, the two CLI `Memory(...)` constructions that attach no reporter while the MCP entry point does, and the MCP result's strip of the degradation counters. ONE reader: its author.* |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (veracium-research-32) — first read folded at v2, second at v3; dev (veracium-90) — §3a code-reality read folded at v4 |
| **External review** | REQUIRED — changes what two shipped entry points do on error, and what the diagnostics log contains |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0025** — the ingest report's counter inventory (`invalid`, `retried`, `recovered`, `residual`, `redispositioned`), present on every return path, and its rule that a provider failure during the ONE retry is recorded as `retried > 0, recovered = 0` and NEVER re-raised (§4b(1)). This spec keeps that contract unchanged: it adds a second carrier for the same fact, it does not turn a degrade into a raise. **X12** (the result carries PRECISELY the §4c public counter keys) decides §2c: the degrade fact does not travel on the result.
- **0031 §4d** — the operator-only counters are STRIPPED from the MCP tool result because a model that learns how often its attempts are refused learns to probe. This spec keeps that strip unchanged and does not add a principal-facing field (§10 Q1 asks whether one is wanted; it is not decided here).
- **0007 §4c** — the busy-timeout discipline is the precedent for "a failure has defined behaviour and a named form"; this spec applies the same discipline to the degrade paths' record.

---

## 1. Problem — measured, not hypothesised

**Veracium degrades in three places instead of failing, and by design.** Each is a
correct contract (0025 §4b; the BYO-provider clause; the extraction schema's tolerance).
None leaves a record an operator will see. The three are the ONLY exception handlers in
`ingest.py` that continue after catching; a fourth (the event-date parser) re-raises. The
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

**Four ways to the same empty list (v4, read at HEAD).** `reps = []` is reached by (i) the
provider call raising; (ii) `extract_json` raising `ValueError` — no JSON in the answer;
(iii) a well-formed answer whose `triples` is NOT a list — the line
`if not isinstance(reps, list): reps = []` just above the handler, which raises NOTHING;
and (iv) a bare JSON array — `extract_json` returns the list as a fallback and `.get`
raises `AttributeError` inside the `try`. The first extraction wraps a bare array into
`{"triples": [...]}`; the retry path does not, so the same provider answer is a
recovery attempt on the first call and a failure on the second (§10 Q4 — named, not
changed here). Path (iii) matters for this spec's shape: a record emitted from inside the
`except` would miss it. A legitimately empty recovery — `{"triples": []}` — is none of
the four and is NOT a degrade.

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
`maintain`, `introspect`) — only when an exception PROPAGATES. None of the three degrade
paths calls it, so even the MCP server's attached reporter records nothing when a
provider fails during the retry, answers unparseably, or emits a volatility class the
enum does not know.

**1e. What the MCP host sees.** The tool result strips `retried`, `recovered`,
`residual`, `invalid` and `redispositioned` (0031 §4d, by design); `unparseable`
survives the strip. So a host embedding the MCP server has exactly one degradation
signal — `unparseable: True` — and none for the retry failure or the coercion.

**The consequence the owner named:** during ordinary use, a run of provider failures
shows up only as counters in return values nobody reads, in a log that the CLI never
opens and that no degrade path writes to; and a provider whose volatility vocabulary has
drifted shows up nowhere at all.

## 2. Behaviour

**2a. A degrade is RECORDED through the diagnostics reporter — never raised.** When a
reporter is attached, each degrade path produces a record. The record's fields are
CLOSED IN BOTH DIRECTIONS — nothing may be added without reopening this table, and
nothing declared for a degrade type may be omitted from its record (an absent key is not
a zero, 0025 §4c; V-RECORD-FIELDS-TOTAL asserts the exact set per type):

| field | value | never |
|---|---|---|
| `op` | the operation (`remember`) | — |
| `degrade` | one of `retry_failed`, `unparseable`, `volatility_defaulted` — a closed vocabulary | any other string |
| `user_hash` | the hashed user id — the existing `_on_error` convention: the first 12 hex digits of the user id's SHA-256 | the user id |
| `exc_type` | the exception's class name (`retry_failed`, `unparseable`); for `retry_failed` reached by the shape branch (§1a path iii, no exception raised) the fixed token `shape` | any other token; the exception's message |
| `msg_len`, `msg_sha16` | the exception message's length and the first sixteen hex digits of its SHA-256 | **the message text, in any form, at any length, redacted or not** |
| `count` | for `volatility_defaulted`: how many triples in this `ingest_event` call were coerced | the offending value's text (it is model output) |

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

**2c. The seam: a callback, not a field.** `ingest_event` gains a keyword-only parameter
`on_degrade: Optional[Callable[[str, dict], None]] = None`; the three sites call it.
The retry site calls it ONCE, after the `try`/`except` block, on a failure flag set by
any of §1a's four paths — the `except` sets the flag with the exception, the shape
branch sets it with `shape` — and never when the recovery was legitimately empty
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

**2e. What changes, stated exactly.** `ingest.py`: the `on_degrade` parameter and three
call sites; no other line. `__init__.py`: `Memory._on_degrade`, passed from `remember`.
`diagnostics.py`: `Reporter.record_degrade` writing the §2a record at WARNING level in
the same log, best-effort. `cli.py`: two constructions gain the `diagnostics=` argument.
**The MCP tool result is unchanged** (§10 Q1). **No stored byte changes; no schema, no
export, no migration.**

## 2c-i. Untrusted inputs — REQUIRED, blocking

The untrusted input is the BYO provider's exception and output. Every row states an
observable outcome and the invariant that enforces it.

| # | case | observable outcome | enforced by |
|---|---|---|---|
| 1 | the retry raises (network, provider, SDK) | ONE record `degrade=retry_failed` with the exception's type, message length and digest; the return dict as 0025 specifies | V-DEGRADE-RECORDED, V-NO-CONTENT-IN-LOG |
| 2 | the retry returns no JSON (prose, a refusal) | as row 1 with `exc_type=ValueError` from the extractor; NEVER the raw output — the extractor's own message embeds the first 200 characters of the answer, which is why the record carries length and digest only | V-NO-CONTENT-IN-LOG |
| 2b | the retry returns well-formed JSON whose `triples` is not a list | ONE record `degrade=retry_failed exc_type=shape` from the shape branch (§1a path iii — no exception is raised there); `retried > 0, recovered = 0` as today | V-DEGRADE-RECORDED |
| 2c | the retry returns a bare JSON array | today: `AttributeError` inside the `try`, `reps = []`; ONE record with `exc_type=AttributeError` — the record makes the first-call/second-call asymmetry visible; the asymmetry itself is §10 Q4 | V-DEGRADE-RECORDED |
| 2d | the retry legitimately recovers nothing (`{"triples": []}`) | NO record — an empty list is an answer, not a failure; `recovered = 0` as today | V-DEGRADE-RECORDED's negative arm |
| 3 | the first extraction is unparseable (prose, refusal) | ONE record `degrade=unparseable`; the placeholder episode as today. NOT this row: a well-formed object whose `triples` is not a list — iterating it raises `AttributeError` outside the handler, which PROPAGATES to `_on_error` and is re-raised: an ERROR, not a degrade (the census's "every other handler re-raises") | V-DEGRADE-RECORDED, V-CENSUS |
| 4 | `instructions` of the wrong type (0038 §2c row 2) | as row 3 — the extractor's `ValueError` is the same exception class; the record does not say which shape failed, by design (the message would) | V-DEGRADE-RECORDED, V-NO-CONTENT-IN-LOG |
| 5 | a triple carries a volatility value outside the enum — a PRESENT `null` included (`str(None)` is `"none"`, outside the enum) | coerced to DURABLE as today; ONE record `degrade=volatility_defaulted count=n` per `ingest_event` call; the VALUE's text appears nowhere | V-DEGRADE-RECORDED, V-ONE-RECORD-PER-CALL, V-NO-CONTENT-IN-LOG |
| 6 | a triple carries NO volatility key | the declared default; NO record — this is not a degrade (absence; row 5's `null` is presence) | V-DEGRADE-RECORDED's negative arm |
| 7 | the exception message carries content (a provider echoing the prompt into an error) | the record carries the message's length and digest and NOTHING of its text — redaction is not consulted, because it preserves the semantic payload (measured: "Alice moved to Berlin" survives `redact`) | V-NO-CONTENT-IN-LOG |
| 8 | no reporter attached (an embedding host passing `None`; the CLI today) | no record, no exception, no change in behaviour — `on_degrade` is `None` and the sites do not call it | V-NEVER-RAISED-BY-RECORDING |
| 9 | the reporter itself fails (disk full, path unwritable) | swallowed inside the reporter (its existing contract: "nothing here re-raises"); the operation's outcome is unchanged | V-NEVER-RAISED-BY-RECORDING |
| 10 | a degrade storm (every call fails; every triple drifted) | one record per call per path, bounded by the log's rotation (§7); no auto-send unless the operator pre-authorized it, throttled by `report_min_interval_s` (existing) | V-ONE-RECORD-PER-CALL; the reporter's existing bounds |

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

**Reachability evidence.** The three degrade sites are the ONLY exception handlers in
`ingest.py` that continue after catching (the census, V-CENSUS: four handlers; three
continue; one re-raises). Every other exception propagates to `_on_error`.

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
| **V-CENSUS** | `ingest.py` has exactly the three continuing exception handlers §1 names (the retry, the unparseable return, the volatility coercion) and every other handler re-raises; a NEW continuing handler fails this node until the spec names it | an AST walk over every `ExceptHandler`: classify by whether its body (transitively) raises; assert the continuing set equals the named three by enclosing function and caught type | OWED at implementation: `tests/test_0039_degradation_visibility.py::test_the_census_names_every_continuing_handler` |
| **V-DEGRADE-RECORDED** | with a reporter attached, each of the three paths writes exactly ONE record per occurrence (per call for the volatility path), naming the path in §2a's closed vocabulary; an absent volatility key writes NONE | scripted providers: one raising on the retry; one returning prose; one returning a wrong-typed `instructions`; one emitting `"banana"` for every triple; one omitting the key — the log read back | OWED: `::test_retry_failure_writes_one_record`, `::test_unparseable_writes_one_record`, `::test_drifted_volatility_writes_one_record_with_the_count`, `::test_an_absent_volatility_key_writes_nothing` |
| **V-NO-CONTENT-IN-LOG** | no record contains ANY substring of the event text, of the model's output, or of the provider's exception message beyond its length and digest | a provider whose exception message and whose triple values echo the event text and a sentinel; assert no sentinel, no event-text token and no message substring longer than three characters appears in the log | OWED: `::test_the_record_carries_no_content` |
| **V-ONE-RECORD-PER-CALL** | the volatility path writes one record per `ingest_event` call regardless of triple count | a ten-triple event, every triple drifted: one record, `count` equal to the number coerced | OWED: `::test_volatility_records_aggregate_per_call` |
| **V-RECORD-FIELDS-TOTAL** | for each `degrade` value, the record carries EXACTLY its declared field set (§2a): `retry_failed` and `unparseable` → `op, degrade, user_hash, exc_type, msg_len, msg_sha16`; `volatility_defaulted` → `op, degrade, user_hash, count`; asserted as exact set equality per type, never a subset check | each scripted provider's record read back; the key set compared for equality against the declared set for its type | OWED: `::test_each_record_carries_exactly_its_declared_fields` |
| **V-NEVER-RAISED-BY-RECORDING** | recording never changes the operation's outcome: no reporter → identical return; a failing reporter → identical return | the same scripted providers with `diagnostics=None` and with a reporter whose log path is unwritable; the return dicts equal the recorded ones | OWED: `::test_recording_never_changes_the_outcome` |
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
`exc_type`, a record carrying another type's field (V-RECORD-FIELDS-TOTAL — the
omission direction, which no other row constrains).

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
- **The log can be sent.** Only under the existing consent flow, redacted, capped; this
  spec adds records to that log and therefore to what a consented send may carry — §2a
  is why the record is content-free by CONSTRUCTION (no message text at all), not by
  redaction: redaction was measured and preserves the payload.

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

**What the record cannot tell the operator:** WHICH shape failed (row 4), or WHAT the
drifted value was (row 5). Both would require carrying model output; both are recoverable
from the provider's own logs by the digest and the timestamp.

## 9. Brief for the external reviewer

Attack, in order: **V-NO-CONTENT-IN-LOG's test**, because "no substring of the event
text" is a claim about a test's sentinel and the reviewer will look for the token the
sentinel did not cover (the exception's `repr`, the `args` tuple, a `__notes__`); **the
callback under a failing provider**, because `on_degrade` runs inside `ingest_event`'s
own exception paths and a callback that raises there would change a degrade into an
error (row 9 says the reporter swallows — prove the CALLBACK does, not only the reporter);
and **V-CENSUS's classifier**, because "the handler's body transitively raises" is a
static property and a handler that continues on one branch and raises on another is
neither cell. §1c's ranking — the coercion is worse than the two absences — is an
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

4. **(v4, D1) Should the retry path wrap a bare JSON array as the first extraction
   does?** Today the same provider answer is a recovery attempt on the first call and an
   `AttributeError`-shaped failure on the retry (§1a path iv). Wrapping it is a one-line
   change to a guarded file under accepted 0025's retry clause, so it is an amendment to
   0025, not a line of this spec; this spec records the asymmetry (row 2c) and leaves the
   behaviour as shipped.

*Closed at v2: the seam (callback, by 0025 X12 — §2c).*

## Reviewer checklist

- [ ] every claim in §1 is a line in the tree at the pinned commit; the census (V-CENSUS) is RUN and names three continuing handlers and one re-raising
- [ ] the three degrade paths' RETURN values are unchanged (0025 X12's exact-set test still passes; the callback adds no key)
- [ ] the MCP tool result is unchanged (0031 §4d's strip test still passes)
- [ ] no degrade record can carry event text, model output or the exception message's text (row 7's mutant — the redaction inversion is measured, not argued)
- [ ] the volatility path writes one record per call, and none for an absent key
- [ ] each record carries EXACTLY its type's declared field set — the omission mutants (no `count`; no `exc_type`) fail, not only the addition mutant
- [ ] recording never changes an outcome, with or without a reporter, with a failing reporter, with a failing CALLBACK
- [ ] the CLI attaches a reporter at every `Memory(...)` construction
