# Feature spec 0053: adapter conformance suite — a framework adapter is intact when the library, as the oracle, agrees with it

Spec-Status: accepted

| | |
|---|---|
| **Author / session** | research (veracium-research, candidate v0.1 at `27484429`). Adopted by dev 2026-11-09 in the suite's first commit, byte for byte but this cell |
| **Version** | **v0.5 — 2026-11-10: the Pydantic AI row, as research measured it on dev `6bde677c` (research `260a19cd`, clean).** A change to the accepted text, ADOPTED on the owner's word, first-hand in the dev session, 2026-11-10: "Yes, adopt v0.5". It states four things and changes no check. K6's "never retried" binds a re-invocation, so a framework that offers the model another turn after a tool error retries nothing, and "never crashes the host's loop" holds within the framework's own retry budget. §8 states Pydantic AI's budget as measured, the provider renderings of the tool error, and parallel tool calls in one response. §4.5 and §6 add the Pydantic AI row and its two mutants. §10 Q8 is closed at `6bde677c`, and Q9 records its extension (research's PA-3 and PA-4). Every passage v0.5 replaces is kept verbatim in the v0.4 appendix. **Prior: ACCEPTED — 2026-11-09, on v0.4 as adopted at `4a13cade`: the owner's word, no external round (PROCESS §4a's second path)** (accepted text at `67424484`; its Version cell is quoted whole in the v0.4 appendix) |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line at the top* |
| **Internal reviewers** | research (author; stage 1 of the build, `51e036f5`) · dev (read drafts v0.2–v0.4; built v0.1 and read it against the build, D1–D9) · harness (read draft v0.2, three points; read draft v0.4's clock rule: "reads right", two additions, v0.3) |
| **External review** | none: the owner ruled acceptance on his word (PROCESS §4a's second path), recorded in `## Review closure` |
| **Decision + date** | the owner, 2026-11-09 about 12:00 UTC, first-hand in the dev session (as dev relays it): draft v0.4 meets Phase 1a item 1's condition for lighter adapter review. Confirmed by the owner first-hand in the research session (2026-11-09 16:13 UTC): v0.4 is the condition, with harness's two additions folded into the spec (v0.3). **ACCEPTED: the owner, first-hand in the dev session, 2026-11-09: "I accept 0053 after stage 2"**, given after research's stage 2 on `12636180` (research `41b082cb`, clean) and its read of the adoption commit `4a13cade` (research `12c465d3`, clean) |
| **Path** | `lightweight` — the suite adds tests, a new optional-extra package (`veracium.adapters`), extras in `pyproject.toml` and one CI job, and touches no file on the guarded list. The list was re-derived for v0.2 from `specs/check_spec_reference.py` at commit 77a1ef59, where the file is unchanged since f8de3ddc, and the build's changes under `src/` (f8de3ddc to 77a1ef59) are the three new adapter modules alone. **If the build touches a guarded file, the path becomes full** |

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
| the served registration (read through FastMCP's tool manager, `mcp>=1.0,<2`) | no tool manager: refused at construction, by name | n/a | a served tool the adapter has no binding for, or a binding for a tool not served: refused at construction, never dropped or answered by nothing | n/a | I11 |

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
- **Arguments are validated as the served tool validates them (D2).** The oracle passes each case's arguments through
  the served tool's own argument model (FastMCP's), as an MCP call is validated: an argument the schema lacks is
  ignored, and a malformed one raises. The reference for values is the `*_impl` function behind the served validation.
- **The oracle is written apart from every adapter (D8).** It imports nothing from `veracium.adapters`. The
  framework-free core (`veracium.adapters._surface`, the `*_impl` functions in the driver interface) is product code:
  it is the green control, compared with the oracle like any adapter, so a mutant of the core turns the core's row red
  against the oracle, not against itself.
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

A second user holds first-party records only, one of them from another source, so the host principal's scope (0020)
hides something there, and no never-assert text reaches K8's read cases: a label mutant stays K3's alone (D5).

**Anchors, checked before any adapter runs.** Each class must be visible in the oracle, or the suite refuses as VACUOUS:
- the reference recall contains the never-assert header and the Q line;
- the A answer matches the gate's `ABSTAINED`;
- **P has two anchors, asserted separately:** the recall anchor (P's text is absent from both blocks of the reference
  recall), and the answer anchor (in the reference run, P's summary is absent from the gate's input, read from the
  suite's scripted `Complete` prompt log). The two paths exclude P at different points, so one anchor cannot stand for
  both (B1).
- **A read writes nothing (S1-5).** Every read case's reference store (recall, answer, describe_procedures) equals the
  fixture template under the canonical comparison, so the fixture's "no policy, no sink" holds as a measurement, not
  as a docstring.

### 4.3 The surfaces, one check family each

| id | surface | the check (adapter output vs the reference, same run) |
|---|---|---|
| K1 | tool schemas | the adapter offers exactly the served surface's tools and parameters. **No `user_id`, `source_id`, `capability`, `principal` or `basis` beyond what the served MCP schema has** (0031 §4b-iii, 0006 I1: absent by schema). Parameter closed sets (`author`, `derived_from`, `relation`, `basis`) are the same sets |
| K2 | tool descriptions | each description is the served surface's description, byte for byte, with no length allowance. These are model-facing safety text. **A framework or provider path that cannot carry the full text fails K2 by name** (below). The suite holds no short form |
| K3 | recall, describe_procedures | the context **text** equals `recall_impl`'s for every case G, Q, D, S, P, R, C and T, with and without `query` and `token_budget`; `describe_procedures`'s value equals `describe_procedures_impl`'s, with and without `query` (D6). K3 never compares a store digest (store digests are K5's alone). If the adapter offers a structured form, `grounded` and `unverified` arrive as separate fields and are never merged |
| K4 | answer | the text equals `answer_impl`'s, for every case, abstention (A) and the procedural question (P) included. The adapter must not retry, fall back to its own model, reword, or answer from any other tool's output |
| K5 | remember, maintain | for each `author` / `derived_from` / `date` input, the store after the adapter's call **matches the store after the reference call under the canonical comparison below**. Each call runs in its own fresh copy of the fixture store. That covers an attempted raise discarded, third-party quarantined at birth, and the deployment baseline. The returned dict has exactly `remember_impl`'s keys: no operator counter (`_OPERATOR_ONLY`, 0031 §4d). **`maintain`** writes (expiry flags, consolidated episodes), so it is a K5 case too: its store and its returned dict, with the scripted model answering its consolidation call and its clock leaves measured in a group of their own (D6). The scripted model answers consolidation with one record dated by the pool's earliest episode, and the fixture lowers the consolidation batch so one pool consolidates; twin reference runs give an identical result and one consolidation call each. Its clock group "maintain" is measured like the others. Cases `K5-maintain` and `K8-u2-maintain`; mutant "the maintain result trimmed" → K5. Built in the adoption commit (§10 Q5) |
| K6 | refusals | each serialized refusal (`{"ok": false, "refusal": <name>, …}`: `attempted_elevation`, `SourceIdRequired`'s reason, the closed-set refusals of `record_procedure` and `describe_procedures`) reaches the model as that data, with the same name. It is never turned into a framework exception, an empty success or a retry. `basis_not_applicable` is not a case: the served schema has no `basis`, and the served validation ignores an argument the schema lacks, so only a host calling `remember_impl` directly reaches it (D3). **The raise path (B2, S1-4):** a library raise of any type (a closed-set value on `remember`, a below-floor `token_budget`, an argument the served argument model rejects) reaches the model as the framework's tool-error result, carrying the library's message verbatim. It never crashes the host's loop within the framework's own retry budget (§8), never returns as a success and is never retried: neither the adapter nor the framework calls the library again on its own. A framework that offers the model another turn after a tool error (Pydantic AI's `ModelRetry`) retries nothing; a second call is one the model makes (v0.5). The reference is the library's message, `str(exc)`; FastMCP's error result carries the same message under its own prefix (S1-6). **The witness (N3):** a raise of a type other than `ValueError`, planted in one `*_impl`, reaches the model as the tool error on every row, with its message |
| K7 | the capability gate | under `none`, `record_procedure` refuses `attempted_elevation` and the store is unchanged (K5's canonical comparison); under `direct`, it writes as the reference does, for each `author`, `derived_from` and `note` input (S1-1) |
| K8 | identity | the user and source are the host's, bound when the adapter is built. Two adapters over one store, for two users, never read or write each other's records; a model-passed `user_id` is ignored, as on MCP (D3). A host principal (0020) passed at construction reaches recall, answer and describe_procedures, and the default supplies none, as on MCP. **Every K8 case that writes (one with a clock group) compares identity only:** the other user's records are untouched, and the bound user gains the reference's row count. A write's content is K5's, so a K5 mutant does not also turn K8 red (D5). The rule is by whether the case writes, not by tool name: with `remember` alone named, the maintain mutant turned K8 red as well |

**K5's canonical comparison.** Two stores never match byte for byte, even behind a perfect adapter: ids are minted at
random (`_uid`, and the `ep-…`, `e-…` and `auto-…` ids in the package root), and times come from `utcnow`. So:
- **Fresh stores.** The reference and the adapter each run the case in a fresh copy of the same fixture store.
- **Every user table, rows in insertion order** (SQLite `rowid`).
- **Leaves, not columns (D1).** A cell holding JSON (an object or an array) is flattened to its scalar leaves by path,
  because ids live inside JSON as well as in columns (an edge's `evidence_ref` exists only inside `edges.json`). A
  *place* is (table, row, column, JSON path); a *pattern* is a place without its row, list indices written `*`. The
  declared lists are lists of patterns.
- **Generated values** at a declared id pattern are replaced by `<id:N>`, where N is the value's first appearance in a
  fixed walk: tables by name, rows by `rowid`, columns in schema order, leaves in path order. One mapping covers the
  whole store, and the value is replaced wherever it appears, as a whole leaf or inside a string leaf, so a reference to
  a row stays a reference to that row. Values computed from generated ones (a request digest over an operation's ids)
  are generated too: opaque, renamed, compared by their equality structure (D1). **A declared id that holds a timestamp
  is refused:** a clock renamed as an id loses its order.
- **Clock values** at a declared clock pattern are left out of the digest and compared as an order. The wall-clock value
  is never compared.
- **Every other leaf is compared as stored**, provenance included.

**Clocks: an order that tolerates ties.** Each clock value is located by its place in the walk (table, row by `rowid`,
column); the digest over everything else already requires both stores to hold the same rows, so places are comparable.
**K5 is red on clocks only for a strict reversal:** two places whose values are strictly ordered one way in one store and
the other way in the other. A tie on either side is tolerated, because whether two writes tie depends on the run (a coarse
clock ticks about every 15.6 ms on a Windows runner), and no tiebreak fixes it: `rowid` is per table, a store-wide walk
order can disagree with time across tables, and the adapter's run is a third run with its own ties. The order the store
relies on (S, supersession) is held by the absence of any reversal.

**Instants, not text; NULL compared as stored** (harness's two additions to draft v0.4, part of the owner's condition).
- **Each clock value is parsed to an aware instant before it is ordered.** `datetime.isoformat()` omits the fraction
  when the microseconds are 0, and a store can mix `Z` with `+00:00`, so two texts of one instant must order as one,
  and a text order that disagrees with the instants' order is no reversal. A value without an offset is read as UTC.
  **A value that does not parse is a named refusal, never an order.**
- **A NULL at a clock place is compared as stored:** NULL in both stores, or a value in both. NULL in one and a value
  in the other is a difference. Only places non-NULL in both stores enter the order, so a dropped timestamp is seen
  as a difference, and cannot hide by having no reversal to show.

**The declared lists are measured, not chosen, per clock group (D1).** For every write case the suite runs the
reference twice, in two fresh stores. **Within each clock group, the patterns whose raw values differ between the two
runs must equal that group's declared id and clock patterns, both ways.** A varying pattern left undeclared is refused;
a declared pattern that never varies is refused. The groups exist because one leaf can be an input in one call and a
clock in another: in the *dated* group the call passes `date`, so the event-time leaves (`observed_at`, `valid_from`)
are inputs, compared as stored; in the *undated* group the same leaves come from `utcnow` and are clocks. One list over
all cases would have made `observed_at` a clock and left the date-dropped mutant to an accident of cross-table order.
The two reference runs must give equal canonical forms and no clock reversal: the canonicaliser's green control.

**The serialization rule (K2 to K6).** The comparison is made at the last point the adapter controls: the value it
returns to its framework. Where the suite can call the framework's own tool-to-model conversion offline, it compares
there too. A framework that re-wraps a value (a dict to JSON text, say) is allowed a declared decoder back to the
reference value. The decoder must be lossless: the suite round-trips every fixture value through it and refuses one that
loses a byte. Anything that changes the text the model reads fails.

**Where LangChain is compared (D7).** The LangChain driver compares at the `ToolMessage` the framework's own tool-call
path produces, which is the text the model reads, downstream of the adapter's raw return. The raw return is not
compared separately, and the decoder's round trip goes through the same `ToolMessage` path.

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
  `langchain`), never a core dependency. Every adapter reads the served surface from the MCP server's registration, so
  each framework extra also installs `mcp` (D2). The core reads the registration once per binding, under the host's
  capability, so the operator's log names the capability the adapter is bound with (S1-3).
- **The driver interface** (Python; a TypeScript twin for the client) has three calls: `tools()`, the schemas and
  descriptions as the framework will present them; `call(name, args)`, the value as the adapter returns it to the
  framework; `decode(value)`, the declared decoder, the identity by default.
- **The cases** are a data file: fixture step, call, comparison. The TypeScript runner reads the same file. The oracle is
  generated per run, by the Python reference, from that file.
- **Migration:** none. No stored state changes; nothing is unrecoverable.

### 4.5 How an adapter joins, and what "lighter review" means

- **Lighter review means** that an adapter PR passing K1–K8 with its mutant row and the parameter census (§6) needs no
  spec of its own. It needs
  full review when it adds a surface: a new tool, a new parameter, a new place where text reaches the model, or a
  shortened description for a provider. The suite cannot vouch for what it does not compare.
- **Each adapter's row** records its framework and the framework's version, pinned (a framework update can change
  serialization); the decoder declared; each provider path, with its description limit and the limit's source, or "no
  limit found" with the source read; and its mutant kills.
  The LangChain row records the OpenAI function form through `convert_to_openai_tool`: no cap in the conversion, every
  served description carried in full, measured offline. The provider's own documentation was not read, and the row
  says so (D9; §8).
  The Pydantic AI row (v0.5, `6bde677c`) records `pydantic-ai-slim` 2.66.0; the tool definitions an `Agent` hands
  any model (FunctionModel's `AgentInfo.function_tools`) as its provider path, with no cap in the conversion and
  every served description carried in full, measured offline; and its decoder, which reads the tool-return part
  the agent hands the model, where a `ModelRetry` is `{"error": <message>}`. It also records the retry budget as
  the host's (§8). No provider model class was run, and the row says so.
- **Framework order:** LangChain/LangGraph first (`langchain_core` converts a tool to the provider schema offline, so the
  serialization rule can be called there); Pydantic AI second (its offline test model exercises the tool path without a
  network); CrewAI after them. The Vercel AI SDK and Mastra are TypeScript, so they come with the TS client.
- **Where it runs.** The whole suite runs on every push, in its own CI job with the adapter extras installed and the
  framework versions pinned. A framework row that job names fails when its framework is missing, never skips. **The job
  is among the needs of the required check (`pytest (py3.14)`), so a red framework row blocks a merge (S1-2)**: "every
  adapter must pass" is a gate, not a report. The core row also runs in the shard lanes, which install `[dev,mcp]`.
- **Lanes without the `mcp` extra** (the floor lane installs `.[dev]` alone): the whole file skips there by name (D2).
  The oracle validates every call with the served tool's own argument model, which needs `mcp`, and the served
  validation is part of the served surface. The floor lane therefore exercises no adapter (§8).

## 5. Regime analysis — where does this behave differently?

n/a — lightweight path. The one size regime the trust text has, truncation under `token_budget`, is fixture case T, and
K3 compares it.

## 6. Invariants and executable checks — REQUIRED, blocking

| # | invariant | executable check | where it runs |
|---|---|---|---|
| I1 | every adapter carries the library's output intact, surface by surface | K1–K8 (§4.3) against the oracle computed in the same run | the suite's CI job on every push, among the required check's needs (S1-2); the core row also in the shard lanes |
| I2 | the oracle holds something to carry for every class | the anchors (§4.2), before any adapter runs; refused as VACUOUS otherwise; an empty or unknown case refused | same |
| I3 | the green control passes | the framework-free core (`veracium.adapters._surface`, the `*_impl` functions in the driver interface) passes every check on every run, or the run is void | same |
| I4 | a declared decoder is lossless | the round-trip of every fixture value through it, compared by bytes | same |
| I5 | a provider cap below the served length is named, never absorbed | K2's limit check, naming provider, cap, source and length | same |
| I6 | K5's declared id and clock patterns are exactly the patterns that vary, per clock group | the two reference runs per write case; varying-undeclared and declared-never-varying both refused; a declared id holding a timestamp refused | same |
| I7 | the canonicaliser tells different stores apart and only those | the planted pairs below (four different, two equal) and the planted refusal (an unparseable clock), plus the green control (equal forms, no reversal across the two reference runs) | same |
| I8 | a kill is real | each mutant names its site in the adapter's source; an edit that no longer applies or leaves the file unchanged is refused; a kill counts only when a check its row names was collected, ran and failed | same |
| I9 | every served parameter is exercised | the parameter census: every served parameter takes a non-default value in at least one compared case outside K6 **whose reference outcome is not a refusal** (N1), read from the served schema and the cases file (S1-1); its negatives name `record_procedure.author` without its cases, and `record_procedure.derived_from` with only a refused case | same |
| I10 | the oracle is independent of the code under test | `checks.oracle_import_problems()` over the oracle's modules (checks, canon, fixture, planted): it refuses `import veracium.adapters[.x] [as y]`, `from veracium.adapters[.x] import …`, `from veracium import adapters`, an attribute read of `veracium.adapters`, and a string naming it passed to `import_module` or `__import__`; its anchor refuses a module that does not parse or parses to nothing, and a scan that finds no `veracium` import at all. Eight planted negatives, one per form and per anchor case (Q4) | same |
| I11 | an adapter presents exactly what it can answer | the core refuses, at construction, a served registration that differs from the tools it binds, either way | same |
| I12 | a read writes nothing | every read case's reference store equals the fixture template under the canonical comparison (S1-5); shown red by a write planted in a read, which the anchors name (N2) | same |

**Red before green.** The suite is accepted only when each check is shown red against its own mutant. Kills are counted
per check: each mutant turns red **exactly the checks its row names**, among K1–K8, and no other, so a mutant that turns
everything red is a broken fixture, not a kill. Each mutant is one logical change to the reference adapter (some need
a schema edit and a call edit, or a helper; D4), and the same row is applied to every adapter under test, so its own
seams are shown to carry each signal. A row that cannot apply to an adapter (a structured form it does not offer) is
recorded as not applicable on that row, by name, never left out.

| mutant | must turn red |
|---|---|
| the never-assert header stripped from recall's text (**the ruling's "a mutant that drops a label"**) | K3 |
| one claim line's front label removed | K3 |
| `grounded` and `unverified` merged in the structured form | K3, on a row with a structured form; recorded as not applicable on the core's and LangChain's rows, which have none (D4) |
| the adapter trims to its own budget instead of passing `token_budget` | K3 (case T) and K6 (the below-floor case no longer reaches the library's raise; D4) |
| a procedural record surfaced in recall's context | K3 (case P) |
| the abstention replaced by a fallback answer | K4 |
| the adapter answers a procedural question with P's text (from `describe_procedures` or its own render) | K4 (case P) |
| `author` forwarded as `"user"` when the model passed `"third_party"` | K5 |
| `derived_from` dropped (**checked after canonicalisation**) | K5 |
| remember's `date` (the model-supplied event date, `remember_impl`'s `date`) dropped or rewritten: an input compared as stored, never a declared clock | K5 |
| one operator counter left in remember's result | K5 |
| `record_procedure`'s `author` forwarded as `"user"` when the model passed `"third_party"` (S1-1) | K7 |
| a serialized refusal returned as `{"ok": true}` (the core's row: remember's `source_id_required`) | K6 (D4) |
| a serialized refusal raised through the framework (LangChain's row: `handle_tool_error=False`) | K6 (D4) |
| a serialized refusal raised as the framework's tool error (Pydantic AI's row: `ModelRetry` on an `ok: false` result; v0.5) | K6, and K7, whose `none` cases are refusals |
| the framework's tool-error channel dropped, so a library raise ends the run (Pydantic AI's row: no `ModelRetry`; v0.5) | K6 |
| a library raise swallowed into a success | K6 (B2) |
| the capability read from a tool argument | K1 and K7 |
| a `user_id` parameter added | K1 (and K8 when it is honoured) |
| a description shortened | K2 |
| the host principal not passed through | K8 |

**The parameter census (S1-1).** A mutant that drops or rewrites an argument is only caught by a case that passes the
argument a value other than its default, in a call the library does not refuse first. So every served parameter must
take a non-default value in at least one compared case outside K6 whose reference outcome is not a refusal (I9; N1:
`record_procedure` under `none` refuses before its arguments matter). One parameter is exempt: `record_procedure.relation`, whose non-default values the
library refuses. It is exempt only while the procedural relations hold its default alone, and only while a K6 case
carries the refusal. *Why the census exists:* at `77a1ef59` `record_procedure.author`, `.relation` and `.note` had no
such case, and a mutant forwarding `third_party` as `user` on that tool alone turned no family red, measured by research
(`51e036f5`) and reproduced by dev on an export of the same commit.

**The canonicaliser's planted pairs.** It must report as different: two stores that differ only in which row one
cross-row reference points to; two stores that differ only in the order of two clock values, a reversal; two stores that
differ only in one provenance field (`author`, `derived_from`, the source); two stores that differ only in a clock NULL
in one and set in the other (v0.3). It must report as equal: two stores that differ only in a tie, two clock values
equal in one and strictly ordered in the other; and two stores whose clocks are the same instants written as different
text (`Z` or `+00:00`, a whole second with and without its fraction; v0.3). It must refuse by name a store holding a
clock that does not parse (v0.3).

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
- **Skip read as pass.** The file skips by name on lanes without `mcp` (D2). The suite's own job installs it, a
  framework row it names fails rather than skips, and the job gates the required check (S1-2), so the full K1–K8 set
  runs, and must pass, on every push.
- **A path no case reaches.** The parameter census (I9) guards each argument; a trust path that depends on a
  combination of arguments is covered only as far as the cases reach it.
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
  - **A renamed digest** shows only its equality structure (D1). That it was computed over the right content is shown
    only by the digested fields, compared as stored.
  - **The floor lane** (`.[dev]`, without `mcp`) exercises no adapter (D2).
  - **`maintain`'s consolidation as a model would write it.** The scripted model answers it with one fixed record, so
    K5 compares how an adapter carries `maintain`'s call and result, not the quality of a consolidation (D6).
  - **Whether a raise of a type other than `ValueError` is reachable through the served arguments.** The adapters
    carry one as a tool error, shown by a planted raise (S1-4, N3); no served input is known to produce one.
  - **A framework's own retry budget (v0.5).** Pydantic AI ends a run with `UnexpectedModelBehavior` when one tool
    raises more times than its `max_retries` without a success of its own in between. Calls to other tools in
    between reset nothing, whether they raise or succeed, and at `max_retries=0` the first error ends the run
    before the model sees it. The budget is the host's: `as_tools(max_retries=)` sets every tool's, and the
    default is the agent's `retries`, 1. A serialized refusal is a success and spends none. The count does not
    carry from one run to the next. Measured on 2.66.0 with the scripted model (research `260a19cd`,
    reproducing dev's figures). So K6's "never crashes the host's loop" holds within that budget, and the
    suite pins it by `test_the_pydantic_ai_retry_budget_is_the_hosts`.
  - **How a provider renders the tool error.** The Pydantic AI row compares the form the offline model is handed,
    `{"error": <message>}`. Read in 2.66.0's code but not run: Anthropic's model class sends the bare message
    with `is_error`, Bedrock's sends `status='error'`, and Google's sends a dict holding the message. The
    message is the library's, verbatim, in each (research `260a19cd`). These renderings are the framework's,
    past the last point the adapter controls.
  - **Several tool calls in one model response.** The suite's drivers make one call per run. Pydantic AI runs the
    calls of one response concurrently, on threads. Six `remember` calls in one response, measured once, all
    succeeded, with every table's row count equal to the same calls made one at a time. Row contents were not
    compared (research `260a19cd`).
- **Measurements cited:** the description lengths and code lines in §2c-ii, at `f8de3ddc`; S1-1's survivor, at
  `77a1ef59` (research `51e036f5`, reproduced by dev); stage 2's N1 survivor, at `12636180` (research `41b082cb`); the
  Pydantic AI retry budget, the provider renderings and the parallel calls, at `6bde677c` (research `260a19cd`).

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
| Q1 | harness's read of draft v0.3's clock rule (§4.3) | **CLOSED 2026-11-09:** harness, on draft v0.4: "reads right", with two additions, folded in v0.3 | — | — |
| Q2 | the acceptance path: PROCESS §4a requires external review to reach `accepted`, or the owner's explicit acceptance word recorded in the Review-closure section | **CLOSED 2026-11-09:** the owner's word, "I accept 0053 after stage 2" (`## Review closure`) | — | — |
| Q3 | when the TypeScript client joins (its runner reads the same cases file) | dev | with the TS client | `deferred` |
| Q4 | the import scan that makes I10 executable | **CLOSED at `4a13cade`** (research's read `12c465d3`: clean) | — | — |
| Q5 | `maintain`'s K5 case (D6), with its measured clock group | **CLOSED at `4a13cade`** (research's read `12c465d3`: clean) | — | — |
| Q6 | v0.3's three planted clock cases, with the canonicaliser mutants "clocks ordered as text" and "clock NULLs skipped" | **CLOSED at `4a13cade`** (research's read `12c465d3`: clean) | — | — |
| Q7 | stage 2's N1–N3: the census counting only unrefused cases, with its negative; a planted write in a read; a planted raise of another type on every row | **CLOSED at `4a13cade`** (research's read `12c465d3`: clean) | — | — |
| Q8 | research's L1 on `4a13cade`: I10's static scan passes `import veracium as v; v.adapters`, `getattr` and a computed `import_module` string (none is in the tree). The complement: a subprocess cell importing the oracle modules alone and asserting no `veracium.adapters` module in `sys.modules` | **CLOSED at `6bde677c`** (`checks.oracle_runtime_imports`, its anchor `veracium.mcp_server`, its planted computed-string negative; research's read `260a19cd`: clean) | — | — |
| Q9 | research's PA-3 and PA-4 on `6bde677c`. Q8's wording reached only imports made when the oracle modules load: a computed import inside a function the oracle runs while computing references escapes both checks (planted, measured). The extension: the subprocess runs the oracle itself (`Oracle` on a temporary directory, all 57 references, 6.1 s) before reading `sys.modules`, with that planted import as its negative; and a cell shows the anchor red | dev, in the next 0053 commit (queued) | next 0053 commit | `deferred` |

## Review closure

**Owner-accepted: the owner's word, first-hand in the dev session, 2026-11-09: "I accept 0053 after stage 2". No external
round (PROCESS §4a's second path).** The word was given on the condition that research's stage 2 had run; it had, on
`12636180` (research `41b082cb`, clean on the six stage-1 fixes, three items added), and research's read of the adoption
commit `4a13cade` (research `12c465d3`) is clean on all of them. The reviews were internal: research's stage 1 on
`77a1ef59` (research `51e036f5`), stage 2, and the adoption read; harness read draft v0.2 and the clock rule. One row per
finding, each closed by a commit and the test that fails if it reopens. Test nodes are in
`tests/test_0053_adapter_conformance.py`; a mutant named below runs as
`test_the_mutant_row_kills_exactly_its_families[<mutant>-<row>]`.

| # | finding (source) | closed by |
|---|---|---|
| S1-1 | `record_procedure`'s author never compared with a non-default value; a mutant forwarding it as "user" passed every family (stage 1, BLOCKING; reproduced by both seats at `77a1ef59`) | `12636180`: four cases, the mutant `procedure-third-party-as-user` (both rows, K7), `test_every_served_parameter_is_exercised`, `test_the_parameter_census_names_an_unexercised_parameter` |
| S1-2 | the adapter conformance job outside the required `pytest (py3.14)` aggregate (stage 1) | `12636180`: `.github/workflows/test.yml`, the aggregate's `needs` and condition; CI `42687896114` at `4a13cade` GREEN 16/16 |
| S1-3 | every adapter build logged the default capability (stage 1) | `12636180`: the registration read under the host's capability; `test_the_registration_is_read_under_the_hosts_capability` |
| S1-4 | the LangChain wrapper converted `ValueError` alone (stage 1) | `12636180` (any `Exception`, as FastMCP); witnessed at `4a13cade` by `test_a_raise_of_another_type_reaches_the_model_as_a_tool_error` (N3) |
| S1-5 | the fixture's docstring named a check that did not exist (stage 1) | `12636180`: the anchors compare every read case's reference store with the template; shown red at `4a13cade` by `test_a_read_that_writes_is_named_by_the_anchors` (N2) |
| S1-6 | K6's raise reference worded as the served error result (stage 1, research's own) | v0.2's wording (research `d7fee05d`), §4.3's K6 row as built |
| N1 | the census counted a case whose reference refuses (stage 2) | `4a13cade`: `test_the_parameter_census_does_not_count_a_refused_case` |
| N2 | I12 never shown red (stage 2) | `4a13cade`: `test_a_read_that_writes_is_named_by_the_anchors` |
| N3 | S1-4 had no witness; its revert survived stage 2 (stage 2) | `4a13cade`: `test_a_raise_of_another_type_reaches_the_model_as_a_tool_error`, on both rows |
| §10 Q4 | I10 had no executable check (§10) | `4a13cade`: `test_the_oracle_imports_no_adapter_code`, `test_the_import_scan_refuses_each_form` |
| §10 Q5 | `maintain` compared nowhere (D6, §10) | `4a13cade`: case `K5-maintain`, the "maintain" clock group (`test_the_declared_lists_are_the_measured_ones`), the mutant `maintain-result-trimmed` (K5) |
| §10 Q6 | v0.3's three planted clock cases (§10) | `4a13cade`: `test_the_canonicaliser_judges_its_planted_pairs`; `test_the_canonicaliser_catches_each_of_its_mutants` (`clocks-ordered-as-text`, `clock-nulls-skipped`) |
| L1 | I10's static scan passes three indirect forms (the adoption read, NEXT-ROUND) | not a closure: §10 Q8, `deferred` to the next 0053 commit, a Dev-queue row in the ledger (coordination `2a09766`); none of the three forms is in the tree |

**The suite as accepted** (`4a13cade`): 57 cases; 21 mutants, 17 on both rows, 38 runs, each turning red exactly the
families its row names; 5 canonicaliser mutants; 7 planted pairs. The full suite green: 8976 collected, 8941 passed, 35
skipped. The 0044 campaign 546/546. CI `42687896114` GREEN 16/16, the adapter conformance job inside the required
aggregate.

## Appendix: prior text (v0.1, research `27484429`), as replaced

Each passage below is v0.1's text exactly as v0.2 replaced it (the Author cell is dev's and unchanged). Insertions
replaced nothing and are not listed.

**Version** (v0.1):

> | **Version** | **v0.1 — 2026-11-09: first spec text.** The body is research's draft v0.4 (research `83e3eaf9`, `proposals/ADAPTER-CONFORMANCE-SUITE-DRAFT.md`, sha256 `04187bef23babaf8…`), put into the template's sections. Read by dev at v0.2–v0.4 and by harness at v0.2 (no objection, three points, folded in v0.3). One precision from the template's §2c-ii re-run at `f8de3ddc`: the MCP library is imported inside `_server_cls()`, which `build_server` calls (v0.4 said "inside `build_server`"). **Two corrections to v0.4, from dev's build against `f8de3ddc` and confirmed in the code by research (§2c-ii):** **B1**, `answer_impl` never reports `PROCEDURAL_OUT_OF_SCOPE`. It returns the gate's text alone, and a procedural record is excluded before the gate's input. So P's answer anchor is now "P's summary is absent from the gate's input", K4 compares P's answer as text like any case, and the P mutant becomes "the adapter answers a procedural question with P's text". v0.2's anchor, which research wrote, checked a name the answer path never carries. **B2**, a closed-set refusal on `remember` (and a below-floor `token_budget` on `recall`) is a library `ValueError`, not a serialized refusal. K6 gains the raise path, and one mutant row is added. No other change of substance. Number 0053 from the registry over both trees (`specs/allocation.py --next`, peer tree CHECKED), claimed by this file |

**Path** (v0.1):

> | **Path** | `lightweight` — the suite adds tests, a new optional-extra package (`veracium.adapters`), extras in `pyproject.toml` and one CI job, and touches no file on the guarded list (`specs/check_spec_reference.py`, read at `f8de3ddc`). **If the build touches a guarded file, the path becomes full** |

**Internal reviewers** (v0.1):

> | **Internal reviewers** | research (author) · dev (read v0.2, v0.3, v0.4) · harness (read v0.2; its read of v0.3's clock rule, §4.3, is owed, §10 Q1) |

**K3** (v0.1):

> | K3 | recall | the context **text** equals `recall_impl`'s for every case G, Q, D, S, P, R, C and T, with and without `query` and `token_budget`. K3 never compares a store digest (store digests are K5's alone). If the adapter offers a structured form, `grounded` and `unverified` arrive as separate fields and are never merged |

**K5** (v0.1):

> | K5 | remember | for each `author` / `derived_from` input, the store after the adapter's call **matches the store after the reference call under the canonical comparison below**. Each call runs in its own fresh copy of the fixture store. That covers an attempted raise discarded, third-party quarantined at birth, and the deployment baseline. The returned dict has exactly `remember_impl`'s keys: no operator counter (`_OPERATOR_ONLY`, 0031 §4d) |

**K6** (v0.1):

> | K6 | refusals | each serialized refusal (`{"ok": false, "refusal": <name>, …}`: `basis_not_applicable`, `attempted_elevation`, `SourceIdRequired`'s reason, a closed-set refusal) reaches the model as that data, with the same name. It is never turned into a framework exception, an empty success or a retry. **The raise path (B2):** a library `ValueError` (a closed-set refusal on `remember`, a below-floor `token_budget`) reaches the model as the framework's tool-error result, carrying the library's message verbatim. It never crashes the host's loop, never returns as a success and is never retried. The reference is the served surface's error result for the same call |

**K7** (v0.1):

> | K7 | the capability gate | under `none`, `record_procedure` refuses `attempted_elevation` and the store is unchanged (K5's canonical comparison); under `direct`, it writes as the reference does |

**K8** (v0.1):

> | K8 | identity | the user and source are the host's, bound when the adapter is built. Two adapters over one store, for two users, never read or write each other's records. A host principal (0020) passed at construction reaches recall and answer, and the default supplies none, as on MCP |

**K5 canonical: ids** (v0.1):

> - **Generated ids** in a declared id column are replaced by `<id:N>`, where N is the value's first appearance in a fixed
>   walk: tables by name, rows by `rowid`, columns in schema order. One mapping covers the whole store, and the value is
>   replaced wherever it appears, in any column, inside JSON text too, so a reference to a row stays a reference to that
>   row.
> - **Clock values** in a declared clock column are left out of the digest and compared as an order. The wall-clock value
>   is never compared.
> - **Every other column is compared as stored**, provenance included.

**K5 measured lists** (v0.1):

> **The declared lists are measured, not chosen.** For every K5 case the suite runs the reference twice, in two fresh
> stores. **The columns whose raw values differ between the two runs, across all K5 cases, must equal the declared id and
> clock columns, both ways.** A varying column left undeclared is refused; a declared column that never varies is refused.
> The two reference runs must give equal canonical digests and no clock reversal: the canonicaliser's green control.

**4.4 package** (v0.1):

> - **`veracium.adapters`**, a new package. Each framework is an optional extra (LangChain/LangGraph first as
>   `langchain`), never a core dependency.

**4.5 lighter review** (v0.1):

> - **Lighter review means** that an adapter PR passing K1–K8 with its mutant row (§6) needs no spec of its own. It needs

**4.5 where it runs** (v0.1):

> - **Where it runs.** The whole suite runs on every push, in its own CI job with the adapter extras installed and the
>   framework versions pinned. It does not run in the shard lanes, whose dependency set stays the core plus `[dev,mcp]`.
> - **Lanes without the `mcp` extra** (the floor lane installs `.[dev]` alone): K1 and K2 compare against the served
>   surface, which needs `mcp`, so they skip there by name, as the floor lane's MCP tests already do with `importorskip`.
>   K3 to K8 do not need it (§2c-ii) and run there.

**I1** (v0.1):

> | I1 | every adapter carries the library's output intact, surface by surface | K1–K8 (§4.3) against the oracle computed in the same run | the suite's CI job, every push; K3–K8 also on the floor lane |

**I3** (v0.1):

> | I3 | the green control passes | the pass-through reference adapter (the `*_impl` functions in the driver interface) passes every check on every run, or the run is void | same |

**I6** (v0.1):

> | I6 | K5's declared id and clock columns are exactly the columns that vary | the two reference runs per K5 case; varying-undeclared and declared-never-varying both refused | same |

**red before green** (v0.1):

> everything red is a broken fixture, not a kill. Each mutant is a one-line change to the reference adapter, and the same
> row is applied to every adapter under test, so its own seams are shown to carry each signal.

**mutant merged** (v0.1):

> | `grounded` and `unverified` merged in the structured form | K3 |

**mutant trim** (v0.1):

> | the adapter trims to its own budget instead of passing `token_budget` | K3 (case T) |

**mutant serialized** (v0.1):

> | a serialized refusal raised as an exception, or returned as `{"ok": true}` | K6 |

**7 skip** (v0.1):

> - **Skip read as pass.** K1 and K2 skip by name on lanes without `mcp`, and the suite's own job installs it, so the full
>   K1–K8 set runs on every push in that job.

**8 measurements** (v0.1):

> - **Measurements cited:** the description lengths and code lines in §2c-ii, at `f8de3ddc`.

## Appendix: prior text (v0.2, research `d7fee05d`), as replaced

Each passage below is v0.2's text exactly as v0.3 replaced it. Insertions replaced nothing and are not listed.

**Version** (v0.2):

> | **Version** | **v0.2 — 2026-11-09: the suite as built and fixed.** Dev's build of v0.1 (`764b256c`, `77a1ef59`) differed from v0.1's text in nine places (D1–D9). Research's stage 1 on `77a1ef59` (research `51e036f5`) found one gap, S1-1, reproduced by both seats, and five lesser marks. v0.2 states the suite as built, with those marks fixed: §4.3's comparison at JSON-leaf level, per clock group (D1); the suite needs `mcp` (D2); K6's cases (D3, S1-4, S1-6); the mutant row (D4, S1-1); K8's write comparison (D5); `describe_procedures` and `maintain` (D6); the comparison point (D7); the oracle written apart from the adapters (D8); the provider row (D9); the parameter census (S1-1); the gating job (S1-2); the registration read under the host's capability (S1-3); and reads that write nothing (S1-5). **The S1 fixes were in dev's working tree, not yet committed, when this version was written;** research's stage 2 reads them on the fix commit, and any difference becomes v0.3, never an edit in place. Every passage v0.2 replaces is kept verbatim in the appendix. Prior: v0.1, 2026-11-09 (research `27484429`, adopted in `764b256c`), the body of research's draft v0.4 (`83e3eaf9`) with dev's B1 and B2 |

**Internal reviewers** (v0.2):

> | **Internal reviewers** | research (author; stage 1 of the build, `51e036f5`) · dev (read drafts v0.2–v0.4; built v0.1 and read it against the build, D1–D9) · harness (read draft v0.2; its read of draft v0.3's clock rule, §4.3, is owed, §10 Q1) |

**Decision** (v0.2):

> | **Decision + date** | the owner, 2026-11-09 about 12:00 UTC, first-hand in the dev session (as dev relays it): draft v0.4 meets Phase 1a item 1's condition for lighter adapter review |

**planted pairs** (v0.2):

> **The canonicaliser's planted pairs.** It must report as different: two stores that differ only in which row one
> cross-row reference points to; two stores that differ only in the order of two clock values, a reversal; two stores that
> differ only in one provenance field (`author`, `derived_from`, the source). It must report as equal: two stores that
> differ only in a tie, two clock values equal in one and strictly ordered in the other.

**I7** (v0.2):

> | I7 | the canonicaliser tells different stores apart and only those | the planted pairs below, three different and one equal, plus the green control (equal digests, no reversal across the two reference runs) | same |

**Q1** (v0.2):

> | Q1 | harness has not yet read v0.3's clock rule (§4.3), which replaced the rank harness's point 2 addressed. If harness objects, the change is a new version of this spec, never an edit in place | harness reads, dev and research fold | before acceptance | `blocking` |

## Appendix: prior text (v0.3, research `00ef5950`), as replaced

Each passage below is v0.3's text exactly as v0.4 replaced it. Insertions replaced nothing and are not listed.

**Version** (v0.3):

> | **Version** | **v0.3 — 2026-11-09: the owner's condition, and harness's two clock additions.** The owner, first-hand in the research session (2026-11-09 16:13 UTC), approves draft v0.4 as the condition, with harness's two additions folded into the spec. Harness's reply to draft v0.4 in #veracium-seats: §4.3's clock rule "reads right" (closes §10 Q1), with two additions, folded here: clocks are compared as parsed instants, never as text, and an unparseable one is a named refusal; a NULL at a clock place is compared as stored, and only non-NULL pairs enter the order. Research's probe of the built canonicaliser at `77a1ef59` finds it already behaves both ways (`proposals/evidence-0053-stage1-77a1ef59/out/canon-clocks-harness-additions.out`); no planted case holds either, so three are added to §6 (§10 Q6). Every passage v0.3 replaces is kept verbatim in the v0.2 appendix. Prior: v0.2, 2026-11-09 (research `d7fee05d`): the suite as built (D1–D9) and stage 1's fixes (S1-1 to S1-6). Before it, v0.1 (research `27484429`, adopted in `764b256c`), the body of research's draft v0.4 (`83e3eaf9`) with dev's B1 and B2 |

**K5 maintain** (v0.3):

> It is built in the commit after this version's adoption; until then `maintain`'s values are compared nowhere (§8, §10 Q5) |

**K8 writes** (v0.3):

> A write case compares identity only:** the other user's records are untouched, and the bound user gains the reference's row count. A write's content is K5's, so a K5 mutant does not also turn K8 red (D5) |

**K6 raise witness** (v0.3):

> FastMCP's error result carries the same message under its own prefix (S1-6) |

**I9** (v0.3):

> | I9 | every served parameter is exercised | the parameter census: every served parameter takes a non-default value in at least one compared case outside K6, read from the served schema and the cases file (S1-1) | same |

**I10** (v0.3):

> | I10 | the oracle is independent of the code under test | the oracle's modules import nothing from `veracium.adapters` (an import scan of the suite's oracle side; §10 Q4) | same |

**I12** (v0.3):

> | I12 | a read writes nothing | every read case's reference store equals the fixture template under the canonical comparison (S1-5) | same |

**census paragraph** (v0.3):

> argument a value other than its default. So every served parameter must take a non-default value in at least one
> compared case outside K6 (I9). One parameter is exempt:

**8 maintain** (v0.3):

>   - **`maintain`'s values,** until its K5 case is built (D6, §10 Q5).

**8 raise** (v0.3):

>   - **A raise of a type other than `ValueError` through the served arguments:** the adapters carry it as a tool error
>     (S1-4), but whether one is reachable was not measured, and no case has one.

**8 measurements** (v0.3):

>   `77a1ef59` (research `51e036f5`, reproduced by dev).

**Q4** (v0.3):

> | Q4 | the import scan that makes I10 executable (D8 was verified by research's reading at `77a1ef59`; no check holds it yet) | dev | before acceptance | `blocking` |

**Q5** (v0.3):

> | Q5 | `maintain`'s K5 case (D6): built in the commit after this version's adoption, or §8's limit stays and K5's row says so | dev | before acceptance | `blocking` |

**Q6** (v0.3):

> | Q6 | the three planted cases v0.3 adds (§6: a NULL against a value, the same instants as different text, an unparseable clock). The built canonicaliser already behaves so at `77a1ef59` (research's probe); no case holds it | dev, in the adoption commit with Q4 and Q5 | before acceptance | `blocking` |

## Appendix: prior text (v0.4 as accepted, dev `67424484`), as replaced

Each passage below is the accepted text exactly as v0.5 replaced it. Insertions replaced nothing and are not listed.

**Version** (v0.4 as accepted):

> | **Version** | **ACCEPTED — 2026-11-09, on v0.4 as adopted at `4a13cade`: the owner's word, no external round (PROCESS §4a's second path).** The acceptance fold adds `## Review closure`, records the word in the External review and Decision cells, and closes §10 Q2 and Q4–Q7; the body above §10 is v0.4's, unchanged. **v0.4 — 2026-11-09: research's stage 2 on the fix commit, and the adoption commit's build.** Stage 2 on `12636180` (research `41b082cb`) is clean on the six stage-1 fixes and adds three items: the census counts only cases that do not refuse (N1); I12 is shown red by a planted write in a read (N2); the any-type raise path has a witness, a planted raise of another type (N3). Dev's adoption commit builds Q4 (the import scan, I10), Q5 (`maintain` under K5, with its own measured clock group) and Q6 (v0.3's three planted clock cases, with two canonicaliser mutants), and K8's identity-only comparison now covers every K8 case that writes, not one tool by name; v0.4 states them as dev described them. **They were uncommitted when this version was written;** research reads them on the adoption commit, and any difference becomes v0.5. Every passage v0.4 replaces is kept verbatim in the v0.3 appendix. Prior: v0.3, 2026-11-09 (research `00ef5950`): the owner's condition (draft v0.4 with harness's two clock additions). Before it, v0.2 (`d7fee05d`) and v0.1 (`27484429`, adopted in `764b256c`) |

**K6** (v0.4 as accepted):

> | K6 | refusals | each serialized refusal (`{"ok": false, "refusal": <name>, …}`: `attempted_elevation`, `SourceIdRequired`'s reason, the closed-set refusals of `record_procedure` and `describe_procedures`) reaches the model as that data, with the same name. It is never turned into a framework exception, an empty success or a retry. `basis_not_applicable` is not a case: the served schema has no `basis`, and the served validation ignores an argument the schema lacks, so only a host calling `remember_impl` directly reaches it (D3). **The raise path (B2, S1-4):** a library raise of any type (a closed-set value on `remember`, a below-floor `token_budget`, an argument the served argument model rejects) reaches the model as the framework's tool-error result, carrying the library's message verbatim. It never crashes the host's loop, never returns as a success and is never retried. The reference is the library's message, `str(exc)`; FastMCP's error result carries the same message under its own prefix (S1-6). **The witness (N3):** a raise of a type other than `ValueError`, planted in one `*_impl`, reaches the model as the tool error on every row, with its message |

**8 measurements** (v0.4 as accepted):

> `77a1ef59` (research `51e036f5`, reproduced by dev); stage 2's N1 survivor, at `12636180` (research `41b082cb`).

**Q8** (v0.4 as accepted):

> | Q8 | research's L1 on `4a13cade`: I10's static scan passes `import veracium as v; v.adapters`, `getattr` and a computed `import_module` string (none is in the tree). The complement: a subprocess cell importing the oracle modules alone and asserting no `veracium.adapters` module in `sys.modules` | dev, in the next 0053 commit (Pydantic AI's) | with Pydantic AI | `deferred` |
