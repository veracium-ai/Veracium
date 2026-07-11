# Using veracium over MCP

The MCP server exposes veracium to any MCP-compatible agent (Claude Desktop, Claude
Code, and others) with no host-side Python.

## Install & run

```bash
# from source (not yet on PyPI):
git clone https://github.com/veracium-ai/Veracium.git && cd Veracium && pip install -e ".[mcp,anthropic]"
ANTHROPIC_API_KEY=sk-... VERACIUM_DB_PATH=~/.veracium.db veracium-mcp
```

The server owns its own model access (the Anthropic reference provider, configured
from the environment).

### Environment

| var | default | meaning |
|---|---|---|
| `VERACIUM_DB_PATH` | `veracium.db` | SQLite memory file. |
| `VERACIUM_USER` | `default` | user id used when a tool call omits `user_id`. |
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
| `remember(text, user_id?, author?, event_type?, date?)` | store an interaction event. **Set `author="third_party"`** for received email / external docs so their claims are quarantined. |
| `recall(query, user_id?)` | return a grounded memory context block (unverified claims fenced under a never-assert marker). |
| `answer(query, user_id?)` | answer from memory with the abstention gate (never asserts unverified claims; abstains rather than guesses). |
| `maintain(user_id?)` | expire stale facts and consolidate old history; call periodically. |

`user_id` defaults to `VERACIUM_USER`. For a single-user assistant, leave it unset;
for a multi-user host, pass the id of the user being served (memory is isolated
per id).

## Per-user isolation & scheduling

- Memory never crosses `user_id` boundaries — pass a stable id per end user.
- `maintain` is idempotent; a host can call it on a daily schedule per active user
  (the "overnight" consolidation pattern).

## Using your host's own model instead of the server's

The default server process calls Anthropic directly. If you'd rather veracium use
your host's model (e.g. via MCP sampling, or an in-process embedding), import the
tool implementations (`veracium.mcp_server.remember_impl`, `recall_impl`,
`answer_impl`, `maintain_impl`) and wire them around a `Memory` built with your own
`Complete` callable.
