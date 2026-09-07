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
| **Version** | **v1 — THE DRAFT.** Written from the shipped code, not from a hypothesis: the two ingest paths that record a failure instead of raising it (`ingest.py`'s retry `except Exception` and its unparseable early return), the library's `diagnostics=None` default, the two CLI `Memory(...)` constructions that attach no reporter while the MCP entry point does, and the MCP result's strip of the degradation counters. ONE reader: its author. Research is the first reader (PROCESS §3a). |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | — (dev only; this text has had ONE reader) |
| **External review** | REQUIRED — changes what two shipped entry points do on error, and what the diagnostics log contains |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0025** — the ingest report's counter inventory (`invalid`, `retried`, `recovered`, `residual`, `redispositioned`), present on every return path, and its rule that a provider failure during the ONE retry is recorded as `retried > 0, recovered = 0` and NEVER re-raised (§4b(1)). This spec keeps that contract unchanged: it adds a second carrier for the same fact, it does not turn a degrade into a raise.
- **0031 §4d** — the operator-only counters are STRIPPED from the MCP tool result because a model that learns how often its attempts are refused learns to probe. This spec keeps that strip unchanged and does not add a principal-facing field (§10 Q1 asks whether one is wanted; it is not decided here).
- **0007 §4c** — the busy-timeout discipline is the precedent for "a failure has defined behaviour and a named form"; this spec applies the same discipline to the degrade paths' record.

---

## 1. Problem — measured, not hypothesised

**Veracium degrades in two places instead of failing, and by design.** Both are correct
contracts (0025 §4b; the BYO-provider clause). Neither leaves a record an operator will
see.

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

**1b. The unparseable extraction.** A provider answering in prose, refusing, or returning
a wrong-typed `instructions` field (0038 §2c row 2) takes the early return: a content-free
placeholder episode, `unparseable: True`, every counter present at zero. No exception.

**1c. Where a record could have gone, and did not.** The library has a diagnostics
reporter (`diagnostics.Reporter`): a local, user-owned rotating log
(`$XDG_STATE_HOME/veracium/veracium.log`, default `~/.local/state/veracium/`; 1 MB, two
backups) that records genuine errors with the operation name, a hashed user id and the
full traceback, and re-raises. Three facts about it, each a line in the tree:

| fact | where |
|---|---|
| `Memory(...)` takes `diagnostics=None` by default; the library core never creates a reporter implicitly | `__init__.py`, the constructor's signature and `diagnostics.load_reporter`'s docstring |
| the MCP entry point DOES attach one: `build_memory()` passes `diagnostics=diagnostics.load_reporter()`, a `Reporter` whenever `log_enabled` (the default) | `mcp_server.py`, `build_memory` |
| the CLI's two `Memory(...)` constructions attach NONE | `cli.py`, both construction sites |

And the error hook is called from five operations (`remember`, `recall`, `answer`,
`maintain`, `introspect`) — only when an exception PROPAGATES. The two degrade paths
never call it, so even the MCP server's attached reporter records nothing when a
provider fails during the retry or answers unparseably.

**1d. What the MCP host sees.** The tool result strips `retried`, `recovered`,
`residual`, `invalid` and `redispositioned` (0031 §4d, by design); `unparseable`
survives the strip. So a host embedding the MCP server has exactly one degradation
signal — `unparseable: True` — and none for the retry failure.

**The consequence the owner named:** during ordinary use, a run of provider failures
shows up only as counters in return values nobody reads, in a log that the CLI never
opens and that the degrade paths never write to.

## 2. Behaviour

**2a. A degrade is RECORDED through the diagnostics reporter — never raised.** At the two
degrade sites, when a reporter is attached, one record is written per occurrence:

```
op=remember degrade=retry_failed   exc=<ExceptionType> user_hash=<12 hex> residual=<n>
op=remember degrade=unparseable    reason=<not-json | wrong-type-instructions | …> user_hash=<12 hex>
```

The record carries the exception's TYPE and a capped, redacted message; it carries NO
event text, NO model output, NO prompt. The degrade paths' return values are unchanged:
`retried/recovered/residual` and `unparseable` mean exactly what 0025 says. The hook
that writes the record is best-effort (0025's rule that logging never masks or delays the
real outcome applies to a degrade as it applies to an error).

**2b. The CLI attaches a reporter as the MCP entry point does.** Both CLI `Memory(...)`
constructions pass `diagnostics=diagnostics.load_reporter()` — a `Reporter` iff
`log_enabled`, the same rule `build_memory()` uses. The library core's default stays
`None` (embedding hosts pass their own or none — the existing contract).

**2c. What changes, stated exactly.** `ingest.py`: the two degrade sites gain a call to
a `on_degrade` callback the store passes through (or the report gains a private,
non-public `_degrade` field consumed by `Memory.remember` before it returns — the
choice is §10 Q2 and the reviewer's). `__init__.py`: `remember` hands each degrade to a
new `Memory._on_degrade(where, kind, exc_or_reason, user_id)` beside `_on_error`, which
calls `Reporter.record_degrade`. `diagnostics.py`: `Reporter.record_degrade` writes the
record at WARNING level in the same log. `cli.py`: two constructions gain the
`diagnostics=` argument. **The MCP tool result is unchanged** (§10 Q1). **No stored byte
changes; no schema, no export, no migration.**

## 2c-i. Untrusted inputs — REQUIRED, blocking

The untrusted input is the BYO provider's exception and output. Every row states an
observable outcome and the invariant that enforces it.

| # | case | observable outcome | enforced by |
|---|---|---|---|
| 1 | the retry raises (network, provider, SDK) | ONE WARNING record: `degrade=retry_failed`, the exception's type, a message capped at 200 chars and redacted (emails, number shapes — `diagnostics.redact`); the return dict as 0025 specifies | V-DEGRADE-RECORDED, V-NO-CONTENT-IN-LOG |
| 2 | the retry returns malformed JSON | as row 1 with `exc=ValueError` from `extract_json`; NEVER the raw output in the log | V-NO-CONTENT-IN-LOG |
| 3 | the first extraction is unparseable (prose, refusal) | ONE record: `degrade=unparseable reason=not-json`; the placeholder episode as today | V-DEGRADE-RECORDED |
| 4 | `instructions` of the wrong type (0038 §2c row 2) | as row 3 with `reason=wrong-type-instructions` | V-DEGRADE-RECORDED |
| 5 | no reporter attached (an embedding host passing `None`) | no record, no exception, no change in behaviour — the degrade paths return exactly as today | V-NEVER-RAISED-BY-RECORDING |
| 6 | the reporter itself fails (disk full, path unwritable) | swallowed inside the reporter (its existing contract: "nothing here re-raises"); the operation's outcome is unchanged | V-NEVER-RAISED-BY-RECORDING |
| 7 | the exception message carries content (a provider echoing the prompt into an error) | the message is capped and redacted before the write; the record is rejected entirely if, after redaction, it still exceeds the cap | V-NO-CONTENT-IN-LOG |
| 8 | a degrade loop (every call fails) | one record per occurrence, bounded by the log's rotation (1 MB × 3); no auto-send unless the operator pre-authorized it, throttled by `report_min_interval_s` (existing) | the reporter's existing bounds |

## 3. Trust-class matrix — REQUIRED, blocking

Unchanged. No record's trust class, disclosure or assertability moves. The degrade
record is operator telemetry about the extractor, not a memory record.

## 3b. Authorization — REQUIRED

No authorization decision keys on any of this. The record carries a hashed user id (the
existing `_on_error` convention) and no content; it crosses no scope boundary that the
error log does not already cross. `_disclosure_for` is untouched.

## 4. The field-consumer table — REQUIRED (guarded surfaces)

`ingest.py` and `__init__.py` are guarded (`check_spec_reference.py`'s `GUARDED`), so this
section is required.

| field / surface | who writes it | who READS it | reachability |
|---|---|---|---|
| the degrade record (log line) | `Reporter.record_degrade`, called by `Memory._on_degrade` | the operator, by reading the log; `veracium diagnostics report`'s tail (existing, consented, redacted) | a log line; never persisted in the store; never returned |
| the degrade signal from ingest to `Memory` | `ingest_event`, at the two sites | `Memory.remember` only, which forwards to the reporter and strips it before returning (if the private-field design is chosen) | not a public counter; the report's public key set is unchanged and `PUBLIC_COUNTERS`' exact-set test (0025 §4c) proves it |
| `diagnostics=` on the CLI's `Memory(...)` | `cli.py` | `Memory`'s existing attribute | the same object the MCP entry point already attaches |

**Reachability evidence.** The two degrade sites are the ONLY places ingest continues after
a provider failure (an AST census of `except Exception` in `ingest.py` is the matrix's
node); every other exception propagates to `_on_error`.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| provider healthy, schema followed | no degrade record; unchanged |
| provider fails during the retry | today: counters only; after: counters AND one WARNING record naming the exception type |
| provider answers unparseably | today: `unparseable: True`; after: the same AND one record naming the reason |
| CLI use | today: no log at all (no reporter); after: the same log the MCP server writes |
| embedding host passing `diagnostics=None` | unchanged: no log, no record — the host owns its own error handling |
| MCP host | unchanged tool result; the operator's log gains the degrade records |

## 6. Invariants and executable checks — REQUIRED, blocking

| id | invariant | check | node |
|---|---|---|---|
| **V-DEGRADE-RECORDED** | with a reporter attached, each of the two degrade paths writes exactly ONE record per occurrence, naming the path (`retry_failed` / `unparseable`) and the exception type or reason | a scripted provider that raises on the retry; one that returns prose; one that returns a wrong-typed `instructions`; the log read back | OWED at implementation: `tests/test_0039_degradation_visibility.py::test_retry_failure_writes_one_record`, `::test_unparseable_writes_one_record_with_its_reason` |
| **V-NO-CONTENT-IN-LOG** | no degrade record contains event text, model output or prompt text; the exception message is capped and redacted | a provider whose exception message echoes the event text and an email address; the record carries neither | OWED: `::test_the_record_carries_no_content` |
| **V-NEVER-RAISED-BY-RECORDING** | recording never changes the operation's outcome: no reporter → identical return; a failing reporter → identical return | the same scripted providers with `diagnostics=None` and with a reporter whose log path is unwritable; the return dicts equal the recorded ones | OWED: `::test_recording_never_changes_the_outcome` |
| **V-CLI-ATTACHES** | both CLI `Memory(...)` constructions pass `diagnostics=load_reporter()` | an AST census of `Memory(` calls in `cli.py`: every one carries the argument | OWED: `::test_every_cli_memory_construction_attaches_a_reporter` |
| **V-PUBLIC-COUNTERS-UNCHANGED** | the ingest report's public key set is exactly 0025 §4c's plus 0038's; the degrade signal is not a public counter | INHERITED from `tests/test_0025_enforcement.py`'s exact-set test (X12) | CHECKED today (the existing node) |
| **V-MCP-RESULT-UNCHANGED** | the MCP tool result gains no field | INHERITED from `tests/test_0031_phase_a.py`'s strip test and the result's existing shape tests | CHECKED today |

**Mutants the matrix must kill:** recording via `print`/stderr instead of the reporter (the
CLI-without-reporter regime would still see nothing persistent); logging the raw exception
string uncapped (row 7); a degrade that raises when the reporter fails (row 6); the CLI
attaching a reporter in one construction and not the other (V-CLI-ATTACHES's census).

### 6a. Acceptance measurement — REQUIRED, FINITE

Every invariant above is either CHECKED today by an existing node or OWED at a named
node; the table's last column says which, row by row, and no count is stated in prose.
Acceptance is the OWED nodes existing and passing, plus a manual run: the CLI against a
scripted provider that fails the retry, then `cat` of the log, showing one record.

## 7. Failure modes and reversibility

- **Reversible.** Removing the two hook calls and the CLI arguments restores today's
  behaviour byte-for-byte; no stored state is touched.
- **The log can grow.** Bounded by the reporter's existing rotation; a degrade loop
  writes at most 3 MB before the oldest lines are lost.
- **The log can be sent.** Only under the existing consent flow, redacted, capped; this
  spec adds records to that log and therefore to what a consented send may carry — §2c-i
  row 7 is why the record is content-free by construction, not by redaction alone.

## 8. Claims and limits

**This spec does not make a degrade an error.** 0025's contract stands: a provider
failure during the retry is a no-op with counters. What changes is that the fact is also
written where an operator looks.

**This spec does not tell the MCP host more.** The tool result is unchanged (§10 Q1).

**A host that passes `diagnostics=None` learns nothing new.** That is the existing
library contract and the right default for an embedding host with its own logging.

## 9. Brief for the external reviewer

Attack, in order: **§2c-i row 7**, because a log that can carry content is the one thing
the diagnostics module was built to avoid, and "capped and redacted" is a claim about a
regex; **the seam between ingest and Memory** (§10 Q2), because a private report field
that escapes into a public dict is 0025's X12 mutant, and a callback threaded through
`ingest_event`'s signature touches a guarded function; and **V-NEVER-RAISED-BY-RECORDING
under a failing reporter**, because the reporter's "nothing here re-raises" is a docstring
until a test makes the disk fail.

## 10. Open questions

1. **Should the MCP tool result carry a single `degraded: bool`?** 0031 §4d strips the
   counters because refusal counts teach a model to probe; a boolean that says only "this
   write was degraded" is a smaller signal than `unparseable: True`, which is already
   exposed. Not decided here; the default is NO new field.
2. **How does the degrade signal travel from `ingest_event` to `Memory.remember`?** (a) a
   private `_degrade` list in the report dict, stripped by `remember` before return — no
   signature change, but a field that must never escape (X12 guards it); (b) an
   `on_degrade` callable parameter on `ingest_event` — a guarded signature change, no
   dict field. The reviewer's call; (a) is the smaller diff.
3. **Should `residual > 0` alone be recorded?** A residual can arise with a healthy
   provider (a triple no relation fits). This spec records only the FAILED retry (an
   exception or malformed output), not a residual the provider legitimately produced.

## Reviewer checklist

- [ ] every claim in §1 is a line in the tree at the pinned commit
- [ ] the two degrade paths' RETURN values are unchanged (0025 §4c's exact-set test still passes)
- [ ] the MCP tool result is unchanged (0031 §4d's strip test still passes)
- [ ] no degrade record can carry event text, model output or prompt text (row 7's mutant)
- [ ] recording never changes an outcome, with or without a reporter, with a failing reporter
- [ ] the CLI attaches a reporter at every `Memory(...)` construction
