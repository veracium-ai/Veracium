# Claude Code hooks integration — memory without tool-schema tokens

An alternative (and complement) to the MCP server: wire Veracium into
[Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) so
memory flows through the session lifecycle instead of tool calls.

Why you might prefer this over MCP:

- **Zero schema tokens** — MCP tool definitions cost context on every request;
  hooks cost nothing until they fire.
- **Memory on every session, not on model discretion** — the session-start
  briefing is *injected*; the model doesn't have to decide to call a recall
  tool.
- **Survives context compaction** — `SessionStart` fires on `resume`/`compact`
  too, so the briefing comes back after a compaction dropped it.

MCP stays the right choice when the *model* should decide what to recall
mid-conversation and for non-Claude-Code clients. The two compose: hooks for
ambient briefing + write-back, MCP for on-demand recall.

## Setup

1. Install and configure the provider (extraction runs on write-back):

   ```bash
   pip install 'veracium[anthropic]'
   export ANTHROPIC_API_KEY=sk-...
   ```

2. Copy the two scripts somewhere stable (e.g. `~/.claude/veracium/`) and make
   them executable. Pick a store path and user id — the scripts default to
   `~/.veracium/claude-code.db` and `$USER`, overridable via `VERACIUM_DB` /
   `VERACIUM_USER`.

3. Merge `settings.example.json` into `~/.claude/settings.json` (user-wide) or
   `.claude/settings.json` (per project).

## What each hook does

- **`SessionStart` → `briefing.sh`** — runs `veracium recall --user $VERACIUM_USER`
  (no query = the proactive briefing: dated commitments due, facts to confirm,
  current context, recent history) and prints it, which Claude Code injects as
  session context. Store-only and LLM-free: adds no latency beyond a SQLite
  read and never bills a token.

- **`UserPromptSubmit` → `capture.sh`** — reads the hook's JSON from stdin,
  extracts the prompt, and pipes it to `veracium remember --user ... -` **in a
  detached background process**, so the ~seconds of LLM extraction never block
  the conversation. The hook itself returns immediately.

Provenance note: `capture.sh` records what *the user typed*, so
`--author user` is correct. If you capture anything else (file contents, tool
output, web pages), pass `--author third_party` or
`--derived-from third_party` — that is the entire point of Veracium: content
the user didn't author must never become an asserted fact.

## Try it

```bash
./briefing.sh                 # empty at first
echo "The dentist appointment is on 2026-08-14" | \
  veracium remember --user "$USER" --db ~/.veracium/claude-code.db -
./briefing.sh                 # now shows the dated commitment
veracium introspect --user "$USER" --db ~/.veracium/claude-code.db
```
