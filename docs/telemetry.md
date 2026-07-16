# Telemetry — opt-in, anonymous, content-free

Veracium can send anonymous usage statistics to help improve the library. It is
**off by default** and sends **nothing** without an explicit opt-in.

## What it collects — and what it never collects

**Collected (aggregate counters only):**

| event | fields |
|---|---|
| ingest | facts, quarantined, episodes, (distill token/latency totals) |
| recall | wiki_used, subgraph_edges, grounded_items, unverified_items |
| answer | abstained (bool), (gate token/latency totals) |
| maintain | lapsed, decayed, flagged, consolidated_in/out |
| selfcheck | pass/fail scores on synthetic data |

Each weekly payload is these summed counters, a random **install id**, and the
period — nothing else.

**Never collected:** facts, preferences, names, entity ids, message text, queries,
answers, or any memory content. This is enforced in code, not by policy — the
collector accepts only a fixed whitelist of numeric/boolean fields and **drops
every other key and every string value** (`veracium/telemetry.py`, `EVENT_FIELDS`).
`veracium telemetry preview` shows exactly what would be sent.

Why these are useful without content: they surface the health signals that matter
— is the injection defense firing (quarantine rate)? is recall degrading
(abstention rate)? is the store growing unboundedly (lifecycle throughput)? — all
as metadata. Real-world *accuracy* can't be measured privately; the `selfcheck`
scores (below) cover correctness on synthetic data instead.

## Self-check (the `selfcheck` scores)

`veracium selfcheck` runs Veracium's load-bearing guarantees against a throwaway,
synthetic memory and scores them — it never touches real memory:

- **supersession** — a superseded functional fact yields the new value as current
  while the old value is retained as history.
- **injection** — a third-party debt claim is quarantined at ingest and never
  reaches the grounded partition, and the gate refuses to assert it (`asserts` must
  be 0).
- **abstention** — a question with no grounded support is declined, not confabulated.

It self-scores structurally (no LLM "judge"), so the numbers don't depend on a
grader's mood.

```bash
veracium selfcheck            # scorecard; exit 0 = pass
veracium selfcheck --json     # machine-readable
veracium selfcheck --push     # also record + flush the (content-free) scores, if opted in
```

Embedded hosts run it directly and fold the result into their weekly push:

```python
result = mem.self_check()   # records a content-free `selfcheck` event if telemetry is wired
```

Only the numeric counters (`total_ok`, `total_n`, `injection_asserts`, …) ever
enter telemetry; the human `detail`/`errors` in the returned dict are dropped by
the collector.

## Consent

- **Default off.** No install id is even created until you choose.
- **Anonymous.** A random install id, no user or host identity.
- **Revocable.** `veracium telemetry disable` any time.
- **No endpoint shipped.** Veracium bundles no collection URL, so even "enabled"
  sends nothing until an endpoint is configured — you decide where (if anywhere)
  data goes.

### Standalone / MCP users

```bash
veracium telemetry prompt          # the consent question
veracium telemetry enable --endpoint https://your-collector.example/ingest
veracium telemetry status
veracium telemetry preview         # exactly what would be sent
veracium telemetry disable
```

The MCP server respects this recorded choice. (Its stdio transport isn't a
terminal, so it never prompts — set your choice with the CLI.)

### Embedded in a host application (e.g. a workflow engine)

**The host is responsible for obtaining its users' consent.** Veracium ships off and
gives you the primitives:

```python
from veracium import Memory
from veracium import telemetry

# After you have asked your user and they agreed:
telemetry.set_enabled(True, endpoint="https://your-collector.example/ingest")

mem = Memory(llm=your_llm, telemetry=telemetry.load_collector_if_enabled())
# ... use mem normally; content-free counters accumulate in-process ...

mem.flush_telemetry()   # POSTs the aggregate if enabled and a week has elapsed;
                        # no-ops otherwise, never raises. Call on a timer / per request.
mem.telemetry_preview() # what a flush would send right now (or None if off)
```

`flush_telemetry()` is the "push" — call it on whatever cadence you like; it only
actually sends once `interval_days` (default 7) have passed since the last send.

## Guarantees, restated

1. Off by default; nothing sent without an explicit opt-in.
2. Content-free by construction (whitelist enforced in code; strings dropped).
3. Anonymous (random install id; no user/host identity).
4. A telemetry failure never affects memory (`flush` never raises).

## Config file

Stored at `$XDG_CONFIG_HOME/veracium/telemetry.json` (default `~/.config/veracium/`):
`{enabled, install_id, endpoint, interval_days, last_sent, schema_version}`.
Delete it to reset to the unasked state.
