# Feature spec 0053: adapter conformance suite — a framework adapter is intact when the library, as the oracle, agrees with it

Spec-Status: draft

| | |
|---|---|
| **Author / session** | research (veracium-research, candidate v0.1 at `27484429`). Adopted by dev 2026-11-09 in the suite's first commit, byte for byte but this cell |
| **Version** | **v0.1 — 2026-11-09: first spec text.** The body is research's draft v0.4 (research `83e3eaf9`, `proposals/ADAPTER-CONFORMANCE-SUITE-DRAFT.md`, sha256 `04187bef23babaf8…`), put into the template's sections. Read by dev at v0.2–v0.4 and by harness at v0.2 (no objection, three points, folded in v0.3). One precision from the template's §2c-ii re-run at `f8de3ddc`: the MCP library is imported inside `_server_cls()`, which `build_server` calls (v0.4 said "inside `build_server`"). **Two corrections to v0.4, from dev's build against `f8de3ddc` and confirmed in the code by research (§2c-ii):** **B1**, `answer_impl` never reports `PROCEDURAL_OUT_OF_SCOPE`. It returns the gate's text alone, and a procedural record is excluded before the gate's input. So P's answer anchor is now "P's summary is absent from the gate's input", K4 compares P's answer as text like any case, and the P mutant becomes "the adapter answers a procedural question with P's text". v0.2's anchor, which research wrote, checked a name the answer path never carries. **B2**, a closed-set refusal on `remember` (and a below-floor `token_budget` on `recall`) is a library `ValueError`, not a serialized refusal. K6 gains the raise path, and one mutant row is added. No other change of substance. Number 0053 from the registry over both trees (`specs/allocation.py --next`, peer tree CHECKED), claimed by this file |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line at the top* |
| **Internal reviewers** | research (author) · dev (read v0.2, v0.3, v0.4) · harness (read v0.2; its read of v0.3's clock rule, §4.3, is owed, §10 Q1) |
| **External review** | not required by path (lightweight). Acceptance still takes external review or the owner's explicit acceptance word (PROCESS §4a), §10 Q2 |
| **Decision + date** | the owner, 2026-11-09 about 12:00 UTC, first-hand in the dev session (as dev relays it): draft v0.4 meets Phase 1a item 1's condition for lighter adapter review |
| **Path** | `lightweight` — the suite adds tests, a new optional-extra package (`veracium.adapters`), extras in `pyproject.toml` and one CI job, and touches no file on the guarded list (`specs/check_spec_reference.py`, read at `f8de3ddc`). **If the build touches a guarded file, the path becomes full** |

**Spec-Requires:** 0031 (the served MCP surface: §4b-iii's pinned schemas, §4d's named carriers, §6a's live
measurement), 0006 (I1: `source_id` host-supplied only), 0020 (the host principal), 0037 (the procedural record and the
gate's out-of-scope outcome), 0003 (§4c-ii, contention as rendered).

## 1. Problem and motivation

**Phase 1a item 1** (ruled 2026-11-08, coordination `76a1818`) gives adapters and SDK glue lighter review **on the
condition of a shared conformance suite every adapter and client must pass. It must show that quarantine, the answer
gate's refusal and the trust labels arrive intact, and a mutant that drops a label must turn it red.** This spec is that
suite.

An adapter (`as_tools()` for a function-calling framework, or the TypeScript client over the Python server) adds no trust
logic. It only carries the library's. Each framework re-wraps tool schemas, descriptions and results in its own way, so
each adapter is a new place where a label, a refusal or a quarantine can be lost **without any library test going red**.

**If we do nothing,** every adapter takes full review, or adapters ship with lighter review and nothing showing that the
trust signals arrive.

**Alternatives rejected:**
- *Full review per adapter.* It is what the condition replaces, and it repeats one question (does the adapter carry the
  library's output?) by hand for each framework.
- *Hand-written golden strings.* They go stale the moment the library's trust text changes. Two implementations of one
  rule drift, so the library's is the one kept (§4.1).
- *A deterministic id source and clock injected into both runs* (option (b) for K5). It adds test-only seams to `src/`.
  The canonical comparison (§4.3, option (a)) needs no product hook.

## 2. Field contracts touched

n/a — lightweight path. The suite reads the store and writes only throwaway fixture stores. It changes no field's
meaning.

## 2c. Untrusted inputs — REQUIRED, blocking

The suite consumes no user content. Its uncontrolled inputs are the thing under test and its environment.

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| the adapter under test (its tool list, schemas, returned values) | no tools: K1 red (the served surface's tools are missing) | a value the declared decoder cannot read: the check fails, never skips | an extra tool or parameter: K1 red | an adapter that passes by carrying nothing: the anchors refuse an oracle with nothing to carry (VACUOUS) | I1, I2, I3 (§6) |
| the adapter's declared decoder | the identity by default | a lossy decoder: refused by the round-trip over every fixture value | n/a | a decoder that rewrites text to match: refused by the same round-trip, which compares bytes | I4 |
| the framework and its version | n/a | n/a | a framework update that changes serialization: the pinned version in the adapter's row, and K2–K6 compare after the framework's own conversion where it can be called offline | n/a | I4; the row's pin (§4.5) |
| a provider's tool-description limit | "no limit found" with the source read | n/a | a limit not in the documentation: not tested, stated in §8 | a cap below the served length: K2 fails by name | I5 |
| the wall clock (`utcnow`) | n/a | n/a | ties that vary between runs: tolerated (§4.3) | a clock stepping backwards inside one run: reported as a clock reversal, by name, never as a provenance defect | I6, I7 |
| the cases data file | no cases: refused (VACUOUS) | a case naming an unknown call: refused | n/a | n/a | I2 |
| a mutant's edit to the adapter under test | an edit that leaves the file unchanged: refused | an edit that no longer applies (a moved site): refused | n/a | a renamed witness that ran nothing: no kill counts unless a named check was collected, ran and failed | I8 |

### 2c-ii. Assertions about reach — REQUIRED

All commands run in a `git archive f8de3ddc` export, from its root.

| assertion | command that establishes it | result |
|---|---|---|
| the served surface has six tools | `grep -n -A1 '@server.tool()' src/veracium/mcp_server.py` | remember, recall, answer, maintain, record_procedure, describe_procedures (lines 406–501) |
| each tool has an `*_impl` reference over `Memory` | `grep -n -E 'def [a-z_]+_impl\(' src/veracium/mcp_server.py` | remember 229, record_procedure 299, describe_procedures 313, recall 326, answer 340, maintain 344 |
| the MCP library is imported only inside `_server_cls()`, so the `*_impl` functions import without it | `grep -n -E '^\s*(import mcp\|from mcp)' src/veracium/mcp_server.py; grep -n 'def _server_cls' src/veracium/mcp_server.py` | imports at 371 and 374, inside `_server_cls()` at 368 |
| the floor lane installs `.[dev]` without `mcp` | `grep -n 'pip install -e' .github/workflows/test.yml` | line 106 `".[dev]"`; lines 44 and 146 `".[dev,mcp]"` |
| no adapter package exists today | `ls src/veracium/adapters` | No such file or directory |
| the operator counters the served `remember` strips | `grep -n '_OPERATOR_ONLY' src/veracium/mcp_server.py` | defined at 201, applied at 248 |
| the gate's procedural outcome is a name in code, never in answer's result | `grep -rn --include='*.py' 'PROCEDURAL_OUT_OF_SCOPE' src; grep -n -A1 'def answer_impl' src/veracium/mcp_server.py` | the constant at `src/veracium/gate.py:33` and four comments or docstrings; `answer_impl` returns `mem.answer(...)` alone |
| a closed-set `author` on `remember` raises, not serialized | `grep -n -E '_closed_set\("author"\|except SourceIdRequired' src/veracium/mcp_server.py` | `_closed_set` called at 168 and 281; `remember_impl` catches `SourceIdRequired` alone |
| ids are minted at random | `grep -n -A1 'def _uid' src/veracium/ingest.py` | line 57, `uuid.uuid4().hex[:12]` |
| the two existing scripted completers | `grep -n -E '^class _?FakeComplete' tests/test_smoke.py tests/test_0006_source_identity.py` | `tests/test_smoke.py:14`, `tests/test_0006_source_identity.py:152` |
| the cleaned descriptions' lengths | `python3 -c 'import ast,inspect;t=ast.parse(open("src/veracium/mcp_server.py").read());print({f.name:(len(inspect.cleandoc(ast.get_docstring(f,clean=False))),len(ast.get_docstring(f,clean=False))) for f in ast.walk(t) if isinstance(f,ast.FunctionDef) and any(ast.unparse(d)=="server.tool()" for d in f.decorator_list)})'` | (cleaned, raw): remember (1407, 1575), recall (710, 790), record_procedure (607, 679), describe_procedures (389, 437), answer (212, 228), maintain (154, 170) |

## 3. Trust-class matrix — REQUIRED, blocking

n/a — lightweight path, and the suite performs no operation on a real store. It **observes** every trust class: the
fixture (§4.2) holds each one, and K3–K8 compare how it arrives. The classes are listed there, not here, so this table
cannot drift from the fixture.

## 3b. Authorization and scope — *full specs only*

n/a — lightweight path. K8 checks that an adapter crosses no user boundary (§4.4).

## 4. Behaviour

### 4.1 What "intact" means: the library is the oracle

> **For every case, what the adapter hands to its framework (or, for a client, what it surfaces to its caller) equals
> what the reference path gives for the same store, user and inputs, computed in the same run.** The reference is split:
> **the served MCP surface** (`build_server`'s registered tools, as FastMCP lists them) for schemas and descriptions (K1,
> K2), and **the `*_impl` functions** over the same `Memory` for values (K3 to K8).

- **Expected values are never written by hand.** The suite computes each one from the library during the run, so a trust
  change in the library moves the oracle and the adapter together.
- **Equality is byte-equality** of the text the model will read, after the framework's own serialization (§4.4). The one
  exception is K5's store comparison, which is canonical by declared and measured rules (§4.3).

### 4.2 The fixture: one store holding every trust class, with anchors

A deterministic fixture is built once per run in a throwaway store. A scripted `Complete` handles extraction and the gate,
so the gate's text is reproducible.
- **The suite owns one scripted `Complete`,** in its own support module. It imports neither existing copy
  (`tests/test_smoke.py:14`, `tests/test_0006_source_identity.py:152`) and adds no third inline.
- **The fixture configures no policy, no telemetry sink and no audit sink.** With a policy, `recall` writes a durable
  `PolicyReceipt` before it returns, so a reference call and an adapter call would change the store between them.
  `Memory._record` writes to the telemetry and audit sinks when they are configured. A later case that adds a policy runs
  the reference and the adapter on separate copies of the store, and K3 still compares text alone.

| class | what it is | what must arrive |
|---|---|---|
| G | a grounded first-party fact | stated plainly in recall |
| Q | a third-party claim (`author="third_party"`), including an injection-shaped payload | under `## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)`, each claim line labelled at the front |
| D | user text quoting third-party content (`derived_from="third_party"`) | capped, on the never-assert side |
| S | a superseded functional fact | the new value current, the old one as history |
| P | a procedural record (0037) | **in recall:** in neither block of the context. **In answer:** P's summary never reaches the gate's input (recall's selection skips a procedural record before visibility; `src/veracium/graph.py`, the outcome named `gate.PROCEDURAL_OUT_OF_SCOPE` in code only), and the answer text is compared as for any case (B1) |
| R | a revoked source's record | out of the read seam |
| C | a live contention (0003 §4c-ii) | as the library renders it |
| A | a question with no grounded support | the gate's abstention text, verbatim |
| T | a store whose `token_budget` truncates, at or above the recall surface's floor (`validate_budget` raises below it) | the library's truncated block, never the adapter's own trimming |

**Anchors, checked before any adapter runs.** Each class must be visible in the oracle, or the suite refuses as VACUOUS:
- the reference recall contains the never-assert header and the Q line;
- the A answer matches the gate's `ABSTAINED`;
- **P has two anchors, asserted separately:** the recall anchor (P's text is absent from both blocks of the reference
  recall), and the answer anchor (in the reference run, P's summary is absent from the gate's input, read from the
  suite's scripted `Complete` prompt log). The two paths exclude P at different points, so one anchor cannot stand for
  both (B1).

### 4.3 The surfaces, one check family each

| id | surface | the check (adapter output vs the reference, same run) |
|---|---|---|
| K1 | tool schemas | the adapter offers exactly the served surface's tools and parameters. **No `user_id`, `source_id`, `capability`, `principal` or `basis` beyond what the served MCP schema has** (0031 §4b-iii, 0006 I1: absent by schema). Parameter closed sets (`author`, `derived_from`, `relation`, `basis`) are the same sets |
| K2 | tool descriptions | each description is the served surface's description, byte for byte, with no length allowance. These are model-facing safety text. **A framework or provider path that cannot carry the full text fails K2 by name** (below). The suite holds no short form |
| K3 | recall | the context **text** equals `recall_impl`'s for every case G, Q, D, S, P, R, C and T, with and without `query` and `token_budget`. K3 never compares a store digest (store digests are K5's alone). If the adapter offers a structured form, `grounded` and `unverified` arrive as separate fields and are never merged |
| K4 | answer | the text equals `answer_impl`'s, for every case, abstention (A) and the procedural question (P) included. The adapter must not retry, fall back to its own model, reword, or answer from any other tool's output |
| K5 | remember | for each `author` / `derived_from` input, the store after the adapter's call **matches the store after the reference call under the canonical comparison below**. Each call runs in its own fresh copy of the fixture store. That covers an attempted raise discarded, third-party quarantined at birth, and the deployment baseline. The returned dict has exactly `remember_impl`'s keys: no operator counter (`_OPERATOR_ONLY`, 0031 §4d) |
| K6 | refusals | each serialized refusal (`{"ok": false, "refusal": <name>, …}`: `basis_not_applicable`, `attempted_elevation`, `SourceIdRequired`'s reason, a closed-set refusal) reaches the model as that data, with the same name. It is never turned into a framework exception, an empty success or a retry. **The raise path (B2):** a library `ValueError` (a closed-set refusal on `remember`, a below-floor `token_budget`) reaches the model as the framework's tool-error result, carrying the library's message verbatim. It never crashes the host's loop, never returns as a success and is never retried. The reference is the served surface's error result for the same call |
| K7 | the capability gate | under `none`, `record_procedure` refuses `attempted_elevation` and the store is unchanged (K5's canonical comparison); under `direct`, it writes as the reference does |
| K8 | identity | the user and source are the host's, bound when the adapter is built. Two adapters over one store, for two users, never read or write each other's records. A host principal (0020) passed at construction reaches recall and answer, and the default supplies none, as on MCP |

**K5's canonical comparison.** Two stores never match byte for byte, even behind a perfect adapter: ids are minted at
random (`_uid`, and the `ep-…`, `e-…` and `auto-…` ids in the package root), and times come from `utcnow`. So:
- **Fresh stores.** The reference and the adapter each run the case in a fresh copy of the same fixture store.
- **Every user table, rows in insertion order** (SQLite `rowid`).
- **Generated ids** in a declared id column are replaced by `<id:N>`, where N is the value's first appearance in a fixed
  walk: tables by name, rows by `rowid`, columns in schema order. One mapping covers the whole store, and the value is
  replaced wherever it appears, in any column, inside JSON text too, so a reference to a row stays a reference to that
  row.
- **Clock values** in a declared clock column are left out of the digest and compared as an order. The wall-clock value
  is never compared.
- **Every other column is compared as stored**, provenance included.

**Clocks: an order that tolerates ties.** Each clock value is located by its place in the walk (table, row by `rowid`,
column); the digest over everything else already requires both stores to hold the same rows, so places are comparable.
**K5 is red on clocks only for a strict reversal:** two places whose values are strictly ordered one way in one store and
the other way in the other. A tie on either side is tolerated, because whether two writes tie depends on the run (a coarse
clock ticks about every 15.6 ms on a Windows runner), and no tiebreak fixes it: `rowid` is per table, a store-wide walk
order can disagree with time across tables, and the adapter's run is a third run with its own ties. The order the store
relies on (S, supersession) is held by the absence of any reversal.

**The declared lists are measured, not chosen.** For every K5 case the suite runs the reference twice, in two fresh
stores. **The columns whose raw values differ between the two runs, across all K5 cases, must equal the declared id and
clock columns, both ways.** A varying column left undeclared is refused; a declared column that never varies is refused.
The two reference runs must give equal canonical digests and no clock reversal: the canonicaliser's green control.

**The serialization rule (K2 to K6).** The comparison is made at the last point the adapter controls: the value it
returns to its framework. Where the suite can call the framework's own tool-to-model conversion offline, it compares
there too. A framework that re-wraps a value (a dict to JSON text, say) is allowed a declared decoder back to the
reference value. The decoder must be lossless: the suite round-trips every fixture value through it and refuses one that
loses a byte. Anything that changes the text the model reads fails.

**K2 at a provider's limit: fail by name.** The served descriptions are long, and remember's is the longest (§2c-ii).
K2's reference is the served listing, not either form of the docstring.
- **Where a framework's provider path caps a tool description below the served length, K2 fails, naming the provider,
  the cap, its source and the length.** The source is the provider's documentation or a measurement through the
  framework's offline conversion. The suite never assumes one number for all providers.
- **The remedy is outside the suite.** A shortened description for one provider is a new place where text reaches the
  model, so it takes full review, read as safety text (§4.5). The long form stays the reference.

**The TypeScript client** runs against the Python server, so its reference is the Python MCP server over the same
transport. A Python reference client records each case's server response, and the TypeScript runner must surface the
same values to its caller. The cases are shared as data (§4.5), not rewritten per language.

### 4.4 Interfaces

- **`veracium.adapters`**, a new package. Each framework is an optional extra (LangChain/LangGraph first as
  `langchain`), never a core dependency.
- **The driver interface** (Python; a TypeScript twin for the client) has three calls: `tools()`, the schemas and
  descriptions as the framework will present them; `call(name, args)`, the value as the adapter returns it to the
  framework; `decode(value)`, the declared decoder, the identity by default.
- **The cases** are a data file: fixture step, call, comparison. The TypeScript runner reads the same file. The oracle is
  generated per run, by the Python reference, from that file.
- **Migration:** none. No stored state changes; nothing is unrecoverable.

### 4.5 How an adapter joins, and what "lighter review" means

- **Lighter review means** that an adapter PR passing K1–K8 with its mutant row (§6) needs no spec of its own. It needs
  full review when it adds a surface: a new tool, a new parameter, a new place where text reaches the model, or a
  shortened description for a provider. The suite cannot vouch for what it does not compare.
- **Each adapter's row** records its framework and the framework's version, pinned (a framework update can change
  serialization); the decoder declared; each provider path, with its description limit and the limit's source, or "no
  limit found" with the source read; and its mutant kills.
- **Framework order:** LangChain/LangGraph first (`langchain_core` converts a tool to the provider schema offline, so the
  serialization rule can be called there); Pydantic AI second (its offline test model exercises the tool path without a
  network); CrewAI after them. The Vercel AI SDK and Mastra are TypeScript, so they come with the TS client.
- **Where it runs.** The whole suite runs on every push, in its own CI job with the adapter extras installed and the
  framework versions pinned. It does not run in the shard lanes, whose dependency set stays the core plus `[dev,mcp]`.
- **Lanes without the `mcp` extra** (the floor lane installs `.[dev]` alone): K1 and K2 compare against the served
  surface, which needs `mcp`, so they skip there by name, as the floor lane's MCP tests already do with `importorskip`.
  K3 to K8 do not need it (§2c-ii) and run there.

## 5. Regime analysis — where does this behave differently?

n/a — lightweight path. The one size regime the trust text has, truncation under `token_budget`, is fixture case T, and
K3 compares it.

## 6. Invariants and executable checks — REQUIRED, blocking

| # | invariant | executable check | where it runs |
|---|---|---|---|
| I1 | every adapter carries the library's output intact, surface by surface | K1–K8 (§4.3) against the oracle computed in the same run | the suite's CI job, every push; K3–K8 also on the floor lane |
| I2 | the oracle holds something to carry for every class | the anchors (§4.2), before any adapter runs; refused as VACUOUS otherwise; an empty or unknown case refused | same |
| I3 | the green control passes | the pass-through reference adapter (the `*_impl` functions in the driver interface) passes every check on every run, or the run is void | same |
| I4 | a declared decoder is lossless | the round-trip of every fixture value through it, compared by bytes | same |
| I5 | a provider cap below the served length is named, never absorbed | K2's limit check, naming provider, cap, source and length | same |
| I6 | K5's declared id and clock columns are exactly the columns that vary | the two reference runs per K5 case; varying-undeclared and declared-never-varying both refused | same |
| I7 | the canonicaliser tells different stores apart and only those | the planted pairs below, three different and one equal, plus the green control (equal digests, no reversal across the two reference runs) | same |
| I8 | a kill is real | each mutant names its site in the adapter's source; an edit that no longer applies or leaves the file unchanged is refused; a kill counts only when a check its row names was collected, ran and failed | same |

**Red before green.** The suite is accepted only when each check is shown red against its own mutant. Kills are counted
per check: each mutant turns red **exactly the checks its row names**, among K1–K8, and no other, so a mutant that turns
everything red is a broken fixture, not a kill. Each mutant is a one-line change to the reference adapter, and the same
row is applied to every adapter under test, so its own seams are shown to carry each signal.

| mutant | must turn red |
|---|---|
| the never-assert header stripped from recall's text (**the ruling's "a mutant that drops a label"**) | K3 |
| one claim line's front label removed | K3 |
| `grounded` and `unverified` merged in the structured form | K3 |
| the adapter trims to its own budget instead of passing `token_budget` | K3 (case T) |
| a procedural record surfaced in recall's context | K3 (case P) |
| the abstention replaced by a fallback answer | K4 |
| the adapter answers a procedural question with P's text (from `describe_procedures` or its own render) | K4 (case P) |
| `author` forwarded as `"user"` when the model passed `"third_party"` | K5 |
| `derived_from` dropped (**checked after canonicalisation**) | K5 |
| remember's `date` (the model-supplied event date, `remember_impl`'s `date`) dropped or rewritten: an input compared as stored, never a declared clock | K5 |
| one operator counter left in remember's result | K5 |
| a serialized refusal raised as an exception, or returned as `{"ok": true}` | K6 |
| a library raise swallowed into a success | K6 (B2) |
| the capability read from a tool argument | K1 and K7 |
| a `user_id` parameter added | K1 (and K8 when it is honoured) |
| a description shortened | K2 |
| the host principal not passed through | K8 |

**The canonicaliser's planted pairs.** It must report as different: two stores that differ only in which row one
cross-row reference points to; two stores that differ only in the order of two clock values, a reversal; two stores that
differ only in one provenance field (`author`, `derived_from`, the source). It must report as equal: two stores that
differ only in a tie, two clock values equal in one and strictly ordered in the other.

**The canonicaliser's mutants**, each caught by a planted pair or the measured-list check: renaming ids per table or per
column instead of one store-wide map; dropping clock columns instead of comparing their order; reading a tie as a
difference; one provenance column added to the declared id list.

**Standing checks:** unchanged. The suite adds checks and alters none of the standing ones.

## 7. Failure modes and reversibility

- **Silent pass.** The failure this project keeps finding is a check that cannot fire, which reads exactly like one that
  passed. The anchors (I2), the green control (I3), the per-check kill count and the real-kill rule (I8) are each there
  for one way of passing while carrying nothing. First visible symptom if one of them were missing: none until an
  adapter dropped a label in production, so the mutant row is acceptance, not a later chore.
- **False red.** The wall clock's ties are tolerated by rule (§4.3). A clock stepping backwards inside one run shows as a
  clock reversal, by name. A framework update can change serialization; the pinned version makes that a deliberate bump
  with K2–K6 re-run, not drift.
- **Skip read as pass.** K1 and K2 skip by name on lanes without `mcp`, and the suite's own job installs it, so the full
  K1–K8 set runs on every push in that job.
- **Reversible:** entirely. The suite writes only throwaway stores, and the adapters are optional extras.
- **New attack surface:** an adapter is one, which is why it must pass the suite. The suite itself reads no
  untrusted content and has no network path except the TypeScript client's local stdio server.

## 8. Claims and limits

- **What we will say:** "Every Veracium framework adapter passes a shared conformance suite on every push. The suite
  computes its expected values from the library itself, and shows each check red against a mutant that drops the signal
  it checks." Scoped to the adapters that have a row.
- **What this does NOT establish:**
  - **What a model does with intact labels.** An agent can still assert a never-assert claim. That is the injection
    residual, measured by the test harness's live cases (0031 §6a), not by this suite.
  - **Framework prompt templates outside the adapter**, such as an agent framework's own system prompt that summarizes
    tool output. The suite compares what the adapter hands over, plus the framework's tool-to-model conversion where it
    can be called offline. It does not cover whole agent loops.
  - **Live transports.** The TypeScript client's run uses a real stdio server, but network failure modes are the
    client's own tests.
  - **A provider's limit enforced only at request time,** past what the framework's offline conversion shows. The row's
    stated limit and its source are what the suite holds. A limit the documentation does not state is not tested.
  - **A lost equality between two clock values** (two writes sharing one `now`). That equality is set inside the
    library, not by anything an adapter forwards, so K5 does not see it.
- **Measurements cited:** the description lengths and code lines in §2c-ii, at `f8de3ddc`.

## 9. Brief for the external reviewer

- **What we are least sure of:** (1) K5's clock rule. A strict reversal is the only red on clocks, so a lost tie is a
  stated limit. Is any trust property carried by an equality of clock values that an adapter could break? (2) Whether
  byte-equality after the framework's offline conversion is the right last point: a framework can transform text again at
  request time, past anything the suite can call.
- **Where we suspect we have overstated:** "the library is the oracle" holds only for what the cases exercise. A trust
  path no case reaches is not compared, and the anchors only show the classes listed in §4.2 are present.
- **What would change our minds:** a framework whose offline conversion cannot be called at all. The comparison would
  then stop at the adapter's return value, and lighter review for that framework would rest on less.
- **Generalised for a reviewer-safe copy:** nothing so far.

## 10. Open questions

| # | question | who decides | by when | class |
|---|---|---|---|---|
| Q1 | harness has not yet read v0.3's clock rule (§4.3), which replaced the rank harness's point 2 addressed. If harness objects, the change is a new version of this spec, never an edit in place | harness reads, dev and research fold | before acceptance | `blocking` |
| Q2 | the acceptance path: PROCESS §4a requires external review to reach `accepted`, or the owner's explicit acceptance word recorded in the Review-closure section | the owner | before acceptance | `blocking` |
| Q3 | when the TypeScript client joins (its runner reads the same cases file) | dev | with the TS client | `deferred` |
