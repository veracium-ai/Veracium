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

## Client recipes

Copy-paste configs for common MCP clients. Each recipe sets the launch
command, wires a per-user id (`VERACIUM_USER` — one process per principal;
see [Per-user isolation](#per-user-isolation--scheduling)), and includes a
remember → answer round-trip you can run once the tools appear.

Personal Claude / editor hosts that capture the authenticated user's own
turns should attest `VERACIUM_MCP_CAPABILITY=direct` so `remember` stores
user-class events. Leave it unset (or omit it) for any deployment reachable
by an untrusted agent — then set `VERACIUM_MCP_SOURCE_ID` before third-party
events can be stored (see [Environment](#environment)).

Install once on the machine that will run the server:

```bash
pip install "veracium[mcp,anthropic]"
```

### Claude Code (`.mcp.json`)

Project-local: put this at the repo root as `.mcp.json`. User-wide: merge
the same `mcpServers` block into `~/.claude.json` (Claude Code's global
MCP config).

```json
{
  "mcpServers": {
    "veracium": {
      "command": "veracium-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "sk-...",
        "VERACIUM_DB_PATH": "/home/you/.veracium/claude-code.db",
        "VERACIUM_USER": "you",
        "VERACIUM_MCP_CAPABILITY": "direct"
      }
    }
  }
}
```

Restart Claude Code (or reload MCP). Confirm with this round-trip in chat:

1. Ask the agent to call `remember` with text
   `USER: I'm vegetarian and have a dog named Ollie.`
2. Ask it to call `answer` with query `Do I have dietary constraints?`
3. Expect an answer grounded in the vegetarian fact (not a guess).

### Claude Desktop

Edit the Desktop MCP config and add the same server block:

| OS | config path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "veracium": {
      "command": "veracium-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "sk-...",
        "VERACIUM_DB_PATH": "/home/you/.veracium/claude-desktop.db",
        "VERACIUM_USER": "you",
        "VERACIUM_MCP_CAPABILITY": "direct"
      }
    }
  }
}
```

Fully quit and reopen Claude Desktop so it relaunches the stdio server.
Then run the same remember → answer round-trip as above (Desktop exposes
the tools to the model the same way).

If `veracium-mcp` is not on Desktop's `PATH`, set `"command"` to the
absolute path from `which veracium-mcp`.

### Editor-agnostic (any stdio MCP client)

Any client that launches an MCP server over stdio with a `command` + `env`
block can use the same shape — Cursor (`.cursor/mcp.json` or the MCP
settings UI), Zed, Continue, and others. Example:

```json
{
  "mcpServers": {
    "veracium": {
      "command": "veracium-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "sk-...",
        "VERACIUM_DB_PATH": "/home/you/.veracium/editor.db",
        "VERACIUM_USER": "you",
        "VERACIUM_MCP_CAPABILITY": "direct"
      }
    }
  }
}
```

Equivalent shell launch (what the client runs):

```bash
ANTHROPIC_API_KEY=sk-... \
VERACIUM_DB_PATH=~/.veracium/editor.db \
VERACIUM_USER=you \
VERACIUM_MCP_CAPABILITY=direct \
veracium-mcp
```

After the client lists the Veracium tools, run the remember → answer
round-trip once to confirm the store path and user id are the ones you
intended (`VERACIUM_DB_PATH` / `VERACIUM_USER` above).


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
