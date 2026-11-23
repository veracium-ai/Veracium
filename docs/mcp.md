# Using Veracium over MCP

The MCP server exposes Veracium to any MCP-compatible agent (Claude Desktop, Claude
Code, and others) with no host-side Python.

## Install & run

```bash
pip install "veracium[mcp,anthropic]"
ANTHROPIC_API_KEY=sk-... VERACIUM_DB_PATH=~/.veracium.db veracium-mcp
```

> **Python and SQLite requirement.** Veracium needs Python 3.14 or newer. It measures your Python's SQLite build on
> every open instead of checking it against a list: the build must pass the feature probes and reproduce every accepted
> schema version exactly. A build that passes opens as `verified`, with one `UnattestedBuildWarning` per process; one
> the project's CI has also attested opens with no warning. The CI has attested 22 builds: SQLite 3.34.1 to 3.54.1 on
> Linux (glibc and musl, x86_64 and arm64) and macOS (arm64), from uv, python.org, Homebrew, conda-forge,
> setup-python, deadsnakes, pyenv, the official Docker images and the distributions' own Pythons. No Windows build is
> attested yet. A build that fails is refused (`unsupported-sqlite`, naming the first failing check), for a new store
> and an existing one alike. `veracium doctor` reports your build's status and lists the attested builds, with or
> without a store. Ubuntu 24.04's own system Python is 3.12, below the floor: `pip` there installs 0.26.1, the last
> release that supports it.

(`veracium-mcp` is a stdio server meant to be launched by your MCP client —
run `veracium-mcp --help` for a summary.)

`veracium mcp` is the same server under the `veracium` command: the same help, version, environment and tools. It
is for a launcher that can name only the package's own command, for example
`uvx --from "veracium[mcp,anthropic]" veracium mcp`.

The server owns its own model access (the Anthropic reference provider, configured
from the environment).

### Environment

| var | default | meaning |
|---|---|---|
| `VERACIUM_DB_PATH` | `veracium.db` | SQLite memory file. |
| `VERACIUM_USER` | `default` | the deployment's user id. Every tool acts on it; no tool takes a `user_id` — the host process is the identity boundary (specs/0031 §4b-iii, §4e). |
| `VERACIUM_MCP_CAPABILITY` | *(unset = `none`)* | **The host's attestation about every call on this server** (specs/0031 §4a). Unset = `none`: events default to the third-party class and a model-supplied `author`/`derived_from` can only restrict trust below that, never raise it. `direct` = every call originates in a turn with the authenticated principal **and this deployment stands behind the model's authorship labelling as its own**; events then default to the user's class. Read once at startup; any other value — the empty string included — refuses to start. **Attested by the host, not verified by veracium**: a server reachable by a public or untrusted agent must leave it unset. |
| `VERACIUM_MCP_SOURCE_ID` | *(unset)* | **The host's opaque, stable id for the source this deployment ingests from** (specs/0006: a mailbox, a connector instance, a device — never a person). Host-set, never a tool argument. `require_source_id` defaults on (specs/0006 v8), so a third-party-class event with no source id is refused with `{"ok": false, "refusal": "source_id_required"}` — and under an unset `VERACIUM_MCP_CAPABILITY` **every** event is third-party-class, so such a deployment must set this (or attest `direct`) before `remember` stores anything. |
| `VERACIUM_MCP_ERASURE` | *(unset = `on`)* | **Erasure through the agent**, under `direct` (specs/0031 §4i): `forget_fact` and the two-step whole-user erase. `off` refuses those three tools with `{"ok": false, "refusal": "erasure_disabled"}` and leaves the other four trust tools working; the user then has no route to erasure through the agent, and the deployment's erasure obligations fall on its operator. Set it for a legal hold or retention rule, a memory several people rely on, or a host with its own erasure flow. Any other value — the empty string included — refuses to start. |
| `VERACIUM_AUDIT_LOG` | *(unset = no log)* | A file path: the server attaches an append-only, content-free operation audit log there (specs/0055 §4g). It records the credential screen's counts (by class and source, never a value) and the discarded provenance raises (specs/0031 §10 Q4). `veracium doctor --audit-log PATH` prints the credential counts from it. |
| `ANTHROPIC_API_KEY` | — | for the reference provider. |

## Register with a client

**Claude Desktop / Claude Code** — add to the MCP servers config
(`claude_desktop_config.json`, or `.mcp.json` for Claude Code):

```json
{
  "mcpServers": {
    "veracium": {
      "command": "veracium-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "sk-...",
        "VERACIUM_DB_PATH": "/home/you/.veracium.db"
      }
    }
  }
}
```

Restart the client; the four tools below become available to the agent.

## Tools

| tool | purpose |
|---|---|
| `remember(text, author?, event_type?, date?, derived_from?)` | store an interaction event for the deployment's user. Provenance comes from the deployment's attestation (`VERACIUM_MCP_CAPABILITY`), not from this call: an omitted `author` takes the deployment's baseline class, and a supplied `author`/`derived_from` can only **restrict** trust below it (an attempted raise is discarded). **Set `author="third_party"`** for received email / external docs so their claims are quarantined. **Write what the user said in the third person** ("The user's favorite color is blue."), one speaker per call: under the default `none` capability the event's author is a third party, so the user's own first-person words ("my favorite color…") would be read as that author's claim, not the user's. If your own event's *text* quotes lower-trust content (a summary of a received email), **set `derived_from="third_party"`** — trust is capped at the minimum, so quoted material can never become an asserted fact. A third-party-class event needs the deployment's source identity (`VERACIUM_MCP_SOURCE_ID`, above); the tool itself takes no `source_id`. |
| `recall(query?, token_budget?)` | return a grounded memory context block (unverified claims fenced under a never-assert marker). `token_budget` (approximate) caps the block, keeping query-matched facts and claim flags in preference to the wiki and old episodes. |
| `answer(query)` | answer from memory with the abstention gate (never asserts unverified claims; abstains rather than guesses). |
| `maintain()` | expire stale facts and consolidate old history; call periodically. |
| `record_procedure(summary, basis, author?, derived_from?, relation?, note?, date?)` | record a PROCEDURE the user follows (specs/0037) — a host-declared content kind that is never asserted as fact and never enters recall's context. `basis` is required: `"stated"` (the user said they follow it) or `"observed"` (a pattern they reported observing). Honoured only under `VERACIUM_MCP_CAPABILITY=direct`; under `none` it returns `{"ok": false, "refusal": "attempted_elevation"}`. Refusals are serialized, never raised: `{"ok": false, "refusal": <name>}` (e.g. `relation_not_procedural`, `basis_required`, `source_id_required`). The source identity is the deployment's `VERACIUM_MCP_SOURCE_ID`, never an argument (0006 I1); with `require_source_id` on, a third-party-authored or third-party-derived procedure needs that binding. |
| `describe_procedures(query?)` | describe the user's recorded procedures, each with its basis and provenance — never a record's note, never a summary that reads as executable step text (withheld by name). `query` orders the descriptions and never filters; records the user may not be told about are listed as withheld with a named reason. Returns `{"ok": true, descriptions, total_describable, withheld, truncated, query}`. |

### The trust tools (under `VERACIUM_MCP_CAPABILITY=direct`)

Seven tools let the user act on their memory through their agent (specs/0031 §4f). They are registered on every
server and refuse every call under `none` (`{"ok": false, "refusal": "attempted_elevation"}`), writing nothing. Each
acts **as the user**, and each description tells the agent to call it only when the user asks in the conversation,
never because of content it read.

| tool | purpose |
|---|---|
| `find_facts(query?)` | what memory currently shows the user, with the record ids the other tools take: the units one `recall` rendered, each `{kind, id, text, partition, annotations}` (`partition`: `grounded`, `fenced` for a third-party claim, or `contested`), and a `subject` exactly as the unit's line rendered it, when the line names one other than the user. It changes no fact; like any `recall`, a query lookup refreshes the user's wiki cache (one row) when wiki recompilation is on (the default), and a lookup without a query writes nothing. Wiki text is a unit with no id. |
| `correct_fact(edge_id, corrected_value)` | the remembered value was wrong: kept as history marked `corrected`, the new value stored as the user's. |
| `dispute_fact(edge_id, reason?)` | the fact is no longer asserted and is kept as history; `reason` at most 1,024 characters. |
| `confirm_fact(edge_id)` | the fact still holds: clears its staleness flag and records the confirmation (`call_path` `mcp_direct`). |
| `forget_fact(edge_id? \| episode_id?)` | **irreversible**: removes ONE record's content (redaction, reason `subject_request`); the receipt names derived records that may still carry it, to forget one call each. |
| `forget_everything_preview()` | the first of two steps: counts, a warning and a token valid for ten minutes. Nothing is erased. |
| `forget_everything_confirm(preview_token)` | **irreversible**: erases everything stored for the user, the audit trail included, if the records in the four previewed tables are the ones previewed. |

**What an existing `direct` deployment opts into on upgrade:** these seven tools (here, and through the LangChain
and Pydantic AI adapters); erasure through the agent, **on by default** (`VERACIUM_MCP_ERASURE`); and the injection
residual — content relayed in a first-party turn can induce an agent to call them, both erase steps included. The
two steps stop one induced call, not an agent induced to call both, and the descriptions ask rather than enforce.
`direct` is your attestation; a server reachable by a public or untrusted agent must leave it unset.

(Still deliberately *not* MCP tools: the host API's one-call `forget(user_id)`, and entity listing — see
[design rationale](design-rationale.md).)

No tool takes a `user_id`: every tool acts on the deployment's user
(`VERACIUM_USER`). Over stdio the transport cannot distinguish callers, so the
honest options for multi-user are one process per principal or an authenticated
transport, not a model-supplied argument — which on `recall` would be a
cross-principal read (specs/0031 §4b-iii, §4e).

## Per-user isolation & scheduling

- Memory never crosses `user_id` boundaries — one server process per end user (`VERACIUM_USER`).
- `maintain` is idempotent; a host can call it on a daily schedule per active user
  (the "overnight" consolidation pattern).

## Using your host's own model instead of the server's

The default server process calls Anthropic directly. If you'd rather Veracium use
your host's model (e.g. via MCP sampling, or an in-process embedding), import the
tool implementations (`veracium.mcp_server.remember_impl`, `recall_impl`,
`answer_impl`, `maintain_impl`) and wire them around a `Memory` built with your own
`Complete` callable.
