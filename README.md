# Veracium Memory

<!-- mcp-name: io.github.veracium-ai/veracium -->

[![tests](https://github.com/veracium-ai/Veracium/actions/workflows/test.yml/badge.svg)](https://github.com/veracium-ai/Veracium/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/veracium)](https://pypi.org/project/veracium/)
[![Python](https://img.shields.io/pypi/pyversions/veracium)](https://pypi.org/project/veracium/)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Provenance-aware memory for AI agents: it records who said what, so a claim your agent only read never silently
becomes a fact about your user.

**Veracium Memory is a provenance-aware memory plug-in for agentic systems** —
it gives any agent durable, per-user memory that keeps what the agent read apart
from what it was told. Provenance means every fact tracks *who said it*: a claim
from an email your agent merely read is stored as that sender's claim, not as a
fact about your user. It remembers what the user said, past interactions, and what worked —
and it remembers where each of those came from.

Veracium is the production distillation of an evaluation-driven research project
(`agent-memory`): every design choice below traces to a measured finding, and the
research's synthetic-corpus harness is reused as the regression suite.

**Research:** the evaluation instrument behind those findings — a longitudinal
benchmark for agent memory — is described in Q. Spencer, *"Ground Truth First:
A Longitudinal Evaluation Instrument for Agent Memory, and the Tenure Crossover
in Memory-Architecture Rankings"* ([arXiv:2607.21962](https://arxiv.org/abs/2607.21962), 2026).

## Why it's shaped this way

- **Typed graph + dated episodes are the store of record.** Entity facts live as
  relational edges (with unforgeable provenance); interaction history lives as
  dated episodes. A curated "wiki" view is compiled from them and cached — never
  the source of truth. *(The layered design won on both short and 9-week horizons;
  flat stores each failed one regime.)*
- **Supersession, never erasure.** Single-valued facts (employer, location,
  deadline) keep one current value with the prior value retained as history —
  "what did X used to be?" stays answerable. Facts that can hold several values
  at once (preferences, measurements, health states) accumulate instead. A user can hold several deadlines:
  each dated obligation is stored under its own name with an ISO date, and a rescheduled one shows once, marked
  contested, with both dates kept. `correct()` does not reschedule such a date (the subject is the
  obligation, not the user) and `confirm()` retires neither date; the user resolves it by disputing the stale date
  (`dispute()`, or the agent's `dispute_fact` tool under `direct`), which keeps it as history.
- **Representation is a security control.** Third-party claims (received email,
  external docs) are quarantined *structurally* — stored as `third_party_claim`
  edges with the claimant as subject, never as user facts. Content-type quarantine
  catches obligation/debt/renewal claims regardless of how plausible they look.
  *(Held against a full plausibility ladder incl. contact-impersonation.)*
  **What this is, and is not:** the store governs retention, retrieval,
  description and recommendation — what it will *say* and how it labels it.
  It does not instantiate, authorize or execute anything; those belong to the
  host's harness. Without an exclusive harness path that consumes the labels,
  Veracium's trust classes are **advisory labelling, not enforcement**.
- **Bring your own model.** Veracium never owns your API keys or model choice; it
  calls a `Complete` callable you supply. A reference Anthropic provider ships in
  the box.
- **Embedded by default.** Zero external services: one SQLite file. Swap in
  Neo4j/Postgres later via the `Store` interface.

## Install

```bash
pip install "veracium[anthropic]"       # core + the reference LLM provider
pip install "veracium[mcp,anthropic]"   # the same, plus the MCP server
```

> **Package name.** Install `veracium` for now. From 0.34.0, which is not released yet, the package is
> `veracium-memory`; until then `veracium-memory` on PyPI is only a placeholder with no code. `import veracium` and
> the `veracium` commands stay the same.

> **Python and SQLite requirement.** Veracium needs Python 3.14 or newer; that is the only thing to check before you
> start. The rest of this note is detail. Veracium measures your Python's SQLite build on
> every open instead of checking it against a list: the build must pass the feature probes and reproduce every accepted
> schema version exactly. A build that passes opens as `verified`, with one `UnattestedBuildWarning` per process; one
> the project's CI has also attested opens with no warning. The CI has attested 22 builds: SQLite 3.34.1 to 3.54.1 on
> Linux (glibc and musl, x86_64 and arm64) and macOS (arm64), from uv, python.org, Homebrew, conda-forge,
> setup-python, deadsnakes, pyenv, the official Docker images and the distributions' own Pythons. No Windows build is
> attested yet. A build that fails is refused (`unsupported-sqlite`, naming the first failing check), for a new store
> and an existing one alike. `veracium doctor` reports your build's status and lists the attested builds, with or
> without a store. Ubuntu 24.04's own system Python is 3.12, below the floor: `pip` there installs 0.26.1, the last
> release that supports it. Without Python 3.14, use the container image (next section).

Extras: `[mcp]` adds the MCP server, `[dev]` adds pytest. The core alone depends
only on `pydantic`. To work from source instead:

```bash
git clone https://github.com/veracium-ai/Veracium.git && cd Veracium
pip install -e ".[anthropic,dev]"
```

Links: [docs](https://veracium-ai.github.io/Veracium/) · [veracium.ai](https://veracium.ai) · [PyPI](https://pypi.org/project/veracium/)

### The container image (no Python 3.14 needed)

`ghcr.io/veracium-ai/veracium:<version>` (from 0.32.0) runs the MCP server over stdio from that release's own wheel, on
Python 3.14 and an attested SQLite build, for linux/amd64 and linux/arm64 (specs/0054). The store lives on a volume at
`/data`. The image sets no trust value of its own: the host supplies them at run time. An MCP client configuration:

```json
{"mcpServers": {"veracium": {
  "command": "docker",
  "args": ["run", "-i", "--rm", "-v", "veracium-data:/data",
           "-e", "ANTHROPIC_API_KEY", "-e", "VERACIUM_MCP_SOURCE_ID",
           "ghcr.io/veracium-ai/veracium:0.33.0"],
  "env": {"ANTHROPIC_API_KEY": "<key>", "VERACIUM_MCP_SOURCE_ID": "<your source id>"}}}}
```

The `env` block is required: an MCP client starts the server with a minimal environment, and `-e NAME` forwards only
what is there. What each configuration stores:

| configuration | `remember` | what `recall` shows |
|---|---|---|
| neither variable | refused: `source_id_required` | nothing stored |
| `VERACIUM_MCP_SOURCE_ID` only, as above | stored as a **third-party** claim | under "UNVERIFIED THIRD-PARTY CLAIMS", never asserted as fact |
| `VERACIUM_MCP_CAPABILITY=direct`, where you stand behind it | the user's own statements are the user's | verified facts |

`direct` is the deployment's own attestation that every call comes from the authenticated user, for example a
single-user desktop where you are that user (see `veracium-mcp --help`). Name a version tag, never `:latest`: a newer
image whose store schema is higher refuses to open the volume's store and names the `veracium migrate` command to run
first. `/data` holds the store and its SQLite sidecars, plus `config/` and `state/` (the telemetry and diagnostics
choices, off by default, and the local diagnostics log). On Docker Desktop for macOS or Windows, use a named volume, not
a bind mount.


### Upgrading an existing store

`veracium migrate` upgrades a store written by any earlier release, one audited schema version at a time
(since 0.31.0). Take a backup first and stop every other process using the store:

```bash
veracium migrate --db path/to/veracium.db --i-have-quiesced --backup <your-backup-ref>
```

Each step is its own audited operation, so a walk across several versions does several transactions;
`migrate_store(path)` in the library stays the one-transaction route. If a walk stops part-way, its last lines say
why and whether running `migrate` again is safe. A part-walked store is usable only by migrating it with 0.31.0 or a
newer release, or by restoring the backup you took before the walk. `veracium doctor` names the route for your store.

## Use (library)

The example calls Anthropic's API, so set `ANTHROPIC_API_KEY` first (no key: see the paragraph after the example). It
creates `veracium.db` in the current folder. Delete that file to start over: running the example again records the
same events a second time.

```python
from veracium import Memory, EvidenceAuthor, EvidenceContext
from veracium.llm.anthropic import AnthropicComplete

mem = Memory(llm=AnthropicComplete())   # or pass your own Complete callable

# Something the user told your agent. `context` is you, the host, saying how you
# captured the text: here, first-hand. Leave it out and Veracium vouches for
# nothing: even the user's own words are stored as an unverified claim.
mem.remember("alice", "USER: I'm vegetarian and have a dog named Ollie.",
             context=EvidenceContext.direct())

# An email your agent read. You captured it first-hand too, but its AUTHOR is a
# third party, so what it says is stored as that party's claim, never as a fact.
mem.remember("alice", "From billing@scam: you owe $900.",
             author=EvidenceAuthor.THIRD_PARTY, event_type="email",
             source_id="billing-mailbox",   # third-party content needs a source id
             context=EvidenceContext.direct())

# Recall labelled context to put in a prompt.
ctx = mem.recall("alice", "suggest a lunch spot")
print(ctx.context)
```

The output is text for your prompt. The vegetarian fact appears as a fact, in up to three sections (the user model,
the notable events and the detail relevant to this query). The $900 appears
only under `UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)`. A line such as
`[[veracium-wiki-compile:v1]] +0 facts / +0 episodes not compiled` is always present: it counts the facts and
episodes the compiled summary had to leave out to stay within its input budget (here, none). You may also see an `UnattestedBuildWarning`, possibly
printed twice: Veracium checked your SQLite build itself when it opened the store, and the build passed; `veracium
doctor` says more.

No Anthropic API key? `AnthropicComplete` is just a convenience — Veracium calls any
`Complete` callable you supply. To run without SDK/key setup, wrap a client you
already have; `examples/claude_cli_provider.py` wraps the `claude` CLI as a
drop-in provider (`from claude_cli_provider import ClaudeCLIComplete`), and
`examples/openai_provider.py` wraps any OpenAI-compatible chat-completions API
(OpenAI itself, vLLM, Ollama's `/v1` endpoint) via `OpenAIComplete` — point it
at a local server with `OpenAIComplete(base_url=...)` and override `models` with
whatever model name your server serves.

### Revoking a source (library, `SqliteStore`)

A host can revoke a source it no longer trusts, for one user, with one call (since 0.30.0). Every record that came
from it is retired, or recomputed from the evidence that survives it; nothing is deleted, and `unrevoke_source` reverses
it by the same computation:

```python
report = mem.revoke_source("alice", None, "billing-mailbox", "erroneous_capture", dry_run=True)
# dry_run=True returns the identical completeness statement and writes nothing; drop it to apply.
mem.revoke_source("alice", None, "billing-mailbox", "erroneous_capture")
mem.source_revocations("alice")   # the standing revocations and their append-only history
```

`origin=None` means this store's own records; pass a foreign origin as it is stored on an imported record. `reason` is
one of `subject_request`, `legal_obligation`, `erroneous_capture` or `policy`. These are library methods only: there is
no CLI verb and no MCP tool, because a revocation is a trust decision and a surface a model can reach is one it can be
talked into. They need `SqliteStore`; any other store raises `NotImplementedError`.

## Use (MCP)

`veracium-mcp` (or `veracium mcp`, the same server) exposes `remember` / `recall` / `answer` / `maintain`, plus
`record_procedure` and `describe_procedures`, to any MCP-compatible agent (Claude
Desktop/Code, others) with no host-side Python.

To try it, install `veracium[mcp,anthropic]`, run `which veracium-mcp` (or `where veracium-mcp` on Windows), and add
this to your client's MCP configuration (`claude_desktop_config.json`, or `.mcp.json` for Claude Code) with that full
path as the command, then restart the client. A desktop client does not see your shell's `PATH` or an activated
virtual environment, so a bare `veracium-mcp` fails to start there, and the client may say only that the server
disconnected.

```json
{"mcpServers": {"veracium": {
  "command": "/full/path/to/veracium-mcp",
  "env": {"ANTHROPIC_API_KEY": "<key>",
          "VERACIUM_DB_PATH": "/home/you/.veracium.db",
          "VERACIUM_MCP_SOURCE_ID": "my-desktop"}}}}
```

The server needs one of two settings before `remember` stores anything; with neither, it refuses with
`source_id_required`:

- `VERACIUM_MCP_SOURCE_ID`, as above, names where the memories come from. Everything the agent remembers, your own
  words included, is then stored as an unverified claim from that source and recalled under "UNVERIFIED THIRD-PARTY
  CLAIMS". That is the safe choice for an agent that reads content from other people.
- `VERACIUM_MCP_CAPABILITY=direct` is your statement that every call comes from the authenticated user, for example a
  single-user desktop where you are that user. Your statements are then stored as yours and recalled as facts.

The container section's table above shows the same choices.

The server also registers seven trust tools, which act only under
`VERACIUM_MCP_CAPABILITY=direct`: through them the user can look up, correct, dispute, confirm and erase their memory
(under any other setting every call refuses and writes nothing). Erasure removes the user's records from the store,
not from exports or backups you've taken. Under `direct`, erasure through the agent is on by
default (`VERACIUM_MCP_ERASURE=off` refuses the three forget tools), and content relayed in a first-party turn can
induce an agent to call these tools, both erase steps included: the two steps stop one induced call, not an agent
induced to call both. A deployment already on `direct` opts into all of this on upgrade; read
[docs/mcp.md](docs/mcp.md) (the config JSON and tool reference) before setting it.

## Documentation

Hosted docs: **[veracium-ai.github.io/Veracium](https://veracium-ai.github.io/Veracium/)**

- **[examples/demo.ipynb](examples/demo.ipynb)** — the scam-email injection demo,
  runnable end to end ([open in Colab](https://colab.research.google.com/github/veracium-ai/Veracium/blob/main/examples/demo.ipynb)).
- **[examples/langchain_memory.py](examples/langchain_memory.py)** — Veracium as
  the long-term memory layer of a LangChain chat app (session-keyed hybrid:
  LangChain buffers recent turns, Veracium holds durable facts with provenance
  and quarantine; your existing LangChain model powers both sides).
- **[docs/concepts.md](docs/concepts.md)** — the mental model: edges vs episodes
  vs the compiled wiki, provenance & authorship, quarantine, the abstention gate,
  lifecycle.
- **[docs/recipes.md](docs/recipes.md)** — short copy-paste examples, one per
  capability (quarantine, mixed provenance, budgeted recall, portability,
  feedback verbs, audit, local models).
- **[docs/api.md](docs/api.md)** — the public API: `Memory`, `MemoryConfig`,
  `EvidenceAuthor`, providing your own LLM callable or store.
- **[docs/mcp.md](docs/mcp.md)** — running and registering the MCP server.
- **[docs/design-rationale.md](docs/design-rationale.md)** — why there's no
  `update()`/`delete()`, no LLM-free extraction, no TTL purging — and what's
  genuinely on the roadmap.
- **[docs/telemetry.md](docs/telemetry.md)** — the opt-in, anonymous, content-free usage statistics (off by default).
- **[docs/diagnostics.md](docs/diagnostics.md)** — opt-in error reporting: local-first error log, consented + redacted send.
- **[ROADMAP.md](ROADMAP.md)** · **[CHANGELOG.md](CHANGELOG.md)**

## Recent changes

- **0.33.0** — a user can look up, correct, dispute, confirm and erase their memory through their agent (seven trust
  tools under `VERACIUM_MCP_CAPABILITY=direct`, over MCP and the LangChain and Pydantic AI adapters); `veracium mcp`
  starts the MCP server; `edges_since` returns what the store learned since a time. See the
  [CHANGELOG](CHANGELOG.md#0330--2026-11-18). Do not open a store the trust tools have written in place with an older
  Veracium: an older build drops an agent's call path when it rewrites an episode, which then reads as the host's act.
- **0.32.1** — a recall no longer states that the view is empty above a fact written during it; the MCP server reports
  its own version; the container image `ghcr.io/veracium-ai/veracium` (first published for 0.32.0). See the
  [CHANGELOG](CHANGELOG.md#0321--2026-11-14).
- **0.32.0** — `veracium.adapters` serves the same tools as the MCP server to LangChain and Pydantic AI, held to the
  adapter conformance suite. See the [CHANGELOG](CHANGELOG.md#0320--2026-11-12).
- **0.31.0** — `veracium migrate` upgrades a store written by any earlier release, one audited schema version at a
  time ([Upgrading an existing store](#upgrading-an-existing-store)).
- **0.30.0** — a host on `SqliteStore` can revoke a source it no longer trusts
  ([Revoking a source](#revoking-a-source-library-sqlitestore)), and maintenance can no longer raise a fact's
  confidence. A host with its own `Store` must add `expiry_transition`, or `maintain()` raises `NotImplementedError`.
- **0.29.0** — a user can hold more than one deadline. BREAKING for code that filters commitments by subject `user`
  or parses the briefing's DATED COMMITMENTS text.

The full record, with every upgrade note, is the [CHANGELOG](CHANGELOG.md).

## Status

The validated layered design is implemented, tested (about 9,000 offline tests, plus
opt-in live tiers: the acceptance eval and a real-corpus robustness harness),
and passes its own research-claim bar (5/5, 0 injection asserts). Roadmap
v0.1–v0.7 complete, plus opt-in telemetry, a self-check, consented error
reporting, and an operation audit log. See [ROADMAP.md](ROADMAP.md).

## License

MIT
