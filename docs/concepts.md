# Concepts — how to think about veracium

Veracium gives an agent durable, per-user memory. This page is the mental model;
`api.md` is the reference and `mcp.md` is the MCP setup.

## The three things memory is for

Veracium distinguishes three recall targets, because each fails differently:

| target | example | how veracium stores it |
|---|---|---|
| **User model** | "vegetarian", "employer is Acme" | typed graph **edges** |
| **Interaction history** | "on Tuesday the export failed" | dated **episodes** |
| **Work knowledge** | "the CLI export worked; svg-batchpack didn't" | typed graph **edges** |

## Store of record: edges + episodes

The source of truth is two things:

- **Edges** — typed relational facts: `(subject, relation, object)` with a note,
  e.g. `user —has_pet→ "dog named Ollie"`. Entity-centric, queryable, and each
  carries **provenance**.
- **Episodes** — dated one-sentence summaries of what happened in an interaction.
  Episodes supply narrative the graph can't ("what did we work on Tuesday?").

A curated **wiki** (a compact Markdown view) is *compiled* from edges + episodes
and cached — but it is never the source of truth. If you delete the wiki cache,
nothing is lost; it recompiles.

Why this shape: in the research behind veracium, a typed graph won on provenance and
entity recall, dated episodes supplied the narrative it lacked, and an LLM curator
compiling the working view beat every flat store on both short and long histories.

## Provenance and authorship — the security backbone

Every edge and episode records **who authored the evidence** it came from:

- `user` — the user's own messages and *sent* mail. Trusted.
- `third_party` — *received* mail, external documents, tool output about the user.
  Untrusted: anyone in the world can put text here.
- `system` — veracium's own derivations (e.g. consolidation).

This one field is the most important input you give veracium. A received email that
says "per our agreement you owe $2,400" is a **claim**, not a fact — and because
you marked it `third_party`, veracium stores it as a `third_party_claim` edge with
the *claimant* as subject, never as a fact about the user. Recall renders it under
an explicit never-assert flag, and the answer gate refuses to state it as true.

Content-type quarantine backs this up: obligation/debt/renewal claims from third
parties are quarantined regardless of how plausible they look — the attack that
gets past naive memory is the *routine-looking* invoice, not the absurd one.

### Mixed provenance: `derived_from`

**Authorship is per-event — but your event's *text* may embed content someone
else influenced.** A system-authored triage verdict that quotes a received
email's subject, a summary derived from a third-party document: the event is
honestly yours, yet an attacker wrote parts of what it says. Declare that with
`derived_from`:

```python
mem.remember(user, f"Triage classified the mail (subject: {subject!r}) as spam.",
             author=EvidenceAuthor.SYSTEM, derived_from=EvidenceAuthor.THIRD_PARTY,
             event_type="triage")
```

Trust is capped at the **minimum** of `author` and `derived_from`: nothing
extracted from such an event — no edge, and not the episode either — can reach
an assertable surface (the gate's GROUNDED block or the compiled wiki). The
classification history still shapes behavior through recall's unverified
channel; it just can't be asserted as fact. Provenance records both fields, so
the graph stays honest: *authored by system, derived from third-party*.

The rule of thumb: **if any span of the event text was influenced by a party
you wouldn't mark as the author, declare the lower-trust source.** Without the
declaration, veracium trusts your voice — quoted attacker text and all.

## Supersession — one current value, history retained

For **functional** facts (preference, employer, location, deadline) a new value
supersedes the old one: at most one is "current", but the prior value is retained
(soft-invalidated), so both "what does the user prefer *now*?" and "what did they
prefer *before*?" are answerable. Re-stating a fact **reinforces** it (refreshes
its validity) instead of duplicating.

Non-functional facts (pets, relatives, tools used) accumulate.

## Volatility and lifecycle

Each fact has a **volatility** class — how long it's expected to hold:

`permanent` → `durable` (years) → `slow` (months) → `transient` (days) → `ephemeral`

`mem.maintain(user_id)` — the "overnight" job — uses it:

- transient/ephemeral facts past their lifetime **lapse** silently (nobody asks
  about a flu from three months ago);
- durable/slow facts past their lifetime are **flagged possibly-stale** (surfaced
  in recall, never silently dropped — "still at Acme?");
- cold episodes are **consolidated** into denser records, preserving first
  occurrences of failures, fixes, illnesses, and dated commitments.

## A note on dates

Relative dates in ingested text ("due Friday", "next week") are resolved to
absolute dates *during extraction*. veracium injects a weekday→date calendar
anchored to the event's `date` so the model **copies** dates rather than computing
them — far more reliable than freehand, and the prompt tells it to keep the
original wording when a date is neither stated nor on the calendar. But it is
still an LLM step: treat an absolute date stored in memory as an inference from
the source — high-confidence when the source stated an explicit date, lower when
it was relative. Always pass an accurate `date=` per event (the date it actually
occurred) so the calendar anchors correctly; the default is "today", which is
wrong for backfilled or dated content.

## Recall and the abstention gate

`mem.recall(user_id, query)` assembles the curated wiki + a per-query subgraph and
partitions memory into **grounded** (verified, assertable) and **unverified**
(third-party claims/reports). `mem.answer(user_id, query)` adds the gate:

- answer only from grounded memory;
- never assert unverified claims as fact;
- say "I don't know" rather than guess.

The gate is why veracium doesn't confabulate on a miss and doesn't get injected: a
fact from the user's own sent email is answered; the same-shaped claim from a
received email is refused. Provenance-by-authorship, doing its job.

## What veracium does *not* do

- It doesn't own your API keys or pick your model — you pass a `Complete` callable.
- It doesn't answer the user for you unless you call `answer()`; `recall()` just
  hands you grounded context to drop into your own prompt.
- It isn't multi-user-leaky: memory is scoped by `user_id`; one user's memory can
  never reach another's.
