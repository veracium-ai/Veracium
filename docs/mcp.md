# Using Veracium over MCP

The MCP server exposes Veracium to any MCP-compatible agent (Claude Desktop, Claude
Code, and others) with no host-side Python.

## Install & run

```bash
pip install "veracium[mcp,anthropic]"
ANTHROPIC_API_KEY=sk-... VERACIUM_DB_PATH=~/.veracium.db veracium-mcp
```

(`veracium-mcp` is a stdio server meant to be launched by your MCP client —
run `veracium-mcp --help` for a summary.)

The server owns its own model access (the Anthropic reference provider, configured
from the environment).

### Environment

| var | default | meaning |
|---|---|---|
| `VERACIUM_DB_PATH` | `veracium.db` | SQLite memory file. |
| `VERACIUM_USER` | `default` | the deployment's user id. Every tool acts on it; no tool takes a `user_id` — the host process is the identity boundary (specs/0031 §4b-iii, §4e). |
| `VERACIUM_MCP_CAPABILITY` | *(unset = `none`)* | **The host's attestation about every call on this server** (specs/0031 §4a). Unset = `none`: events default to the third-party class and a model-supplied `author`/`derived_from` can only restrict trust below that, never raise it. `direct` = every call originates in a turn with the authenticated principal **and this deployment stands behind the model's authorship labelling as its own**; events then default to the user's class. Read once at startup; any other value — the empty string included — refuses to start. **Attested by the host, not verified by veracium**: a server reachable by a public or untrusted agent must leave it unset. |
| `VERACIUM_MCP_SOURCE_ID` | *(unset)* | **The host's opaque, stable id for the source this deployment ingests from** (specs/0006: a mailbox, a connector instance, a device — never a person). Host-set, never a tool argument. `require_source_id` defaults on (specs/0006 v8), so a third-party-class event with no source id is refused with `{"ok": false, "refusal": "source_id_required"}` — and under an unset `VERACIUM_MCP_CAPABILITY` **every** event is third-party-class, so such a deployment must set this (or attest `direct`) before `remember` stores anything. |
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
| `remember(text, author?, event_type?, date?, derived_from?)` | store an interaction event for the deployment's user. Provenance comes from the deployment's attestation (`VERACIUM_MCP_CAPABILITY`), not from this call: an omitted `author` takes the deployment's baseline class, and a supplied `author`/`derived_from` can only **restrict** trust below it (an attempted raise is discarded). **Set `author="third_party"`** for received email / external docs so their claims are quarantined. If your own event's *text* quotes lower-trust content (a summary of a received email), **set `derived_from="third_party"`** — trust is capped at the minimum, so quoted material can never become an asserted fact. A third-party-class event needs the deployment's source identity (`VERACIUM_MCP_SOURCE_ID`, above); the tool itself takes no `source_id`. |
| `recall(query?, token_budget?)` | return a grounded memory context block (unverified claims fenced under a never-assert marker). `token_budget` (approximate) caps the block, keeping query-matched facts and claim flags in preference to the wiki and old episodes. |
| `answer(query)` | answer from memory with the abstention gate (never asserts unverified claims; abstains rather than guesses). |
| `maintain()` | expire stale facts and consolidate old history; call periodically. |
| `record_procedure(summary, basis, author?, derived_from?, relation?, note?, date?)` | record a PROCEDURE the user follows (specs/0037) — a host-declared content kind that is never asserted as fact and never enters recall's context. `basis` is required: `"stated"` (the user said they follow it) or `"observed"` (a pattern they reported observing). Honoured only under `VERACIUM_MCP_CAPABILITY=direct`; under `none` it returns `{"ok": false, "refusal": "attempted_elevation"}`. Refusals are serialized, never raised: `{"ok": false, "refusal": <name>}` (e.g. `relation_not_procedural`, `basis_required`, `source_id_required`). The source identity is the deployment's `VERACIUM_MCP_SOURCE_ID`, never an argument (0006 I1); with `require_source_id` on, a third-party-authored or third-party-derived procedure needs that binding. |
| `describe_procedures(query?)` | describe the user's recorded procedures, each with its basis and provenance — never a record's note, never a summary that reads as executable step text (withheld by name). `query` orders the descriptions and never filters; records the user may not be told about are listed as withheld with a named reason. Returns `{"ok": true, descriptions, total_describable, withheld, truncated, query}`. |

(Deliberately *not* MCP tools: `forget`, `dispute`/`confirm`, and entity
listing — suppress/wipe/enumerate verbs callable by an agent are
prompt-injection targets. They're library/CLI surface for the host; see
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
