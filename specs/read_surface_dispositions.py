"""specs/0020 §4f — THE READ-SURFACE DISPOSITIONS.

The verdicts behind `specs/generated/0020-read-surfaces.md`. The
ENUMERATION is mechanical (`specs/read_surfaces.py` parses the AST of the
public surface); the DISPOSITION of each surface is a recorded decision and
lives here, the `specs/audit_dispositions.py` precedent.

A public surface that returns RECORDS and carries no disposition fails
`test_read_surface_manifest_is_total` (0020 V12). That is the point: the
§4f inventory was written by hand once, and a hand-written inventory is
exactly what an added read path silently escapes.

Fields, per surface:

- `returns_records` — does this surface hand a caller record objects, or
  text/derived material assembled from them? A `True` here is what obliges
  a principal disposition.
- `principal` — `"threaded"` (the surface takes a `principal=` and routes
  it into the visibility relation) or `"none"`. **The value is CHECKED
  against the parsed signature**, in both directions: a `"threaded"`
  surface with no `principal` parameter fails, and so does a `"none"`
  surface that has one. A row cannot claim what the code does not do.
- `carriers` — the §4f carrier column: what actually leaves the surface.
- `disposition` — the recorded ruling, in words.
"""

# --------------------------------------------------------------------------- #
# Memory — the library's public read/write surface.
# --------------------------------------------------------------------------- #

DISPOSITIONS: dict[str, dict] = {

    # ---- the scoped read surfaces (§4f rows 1-4) --------------------------
    "Memory.recall": dict(
        returns_records=True, principal="threaded",
        carriers="rendered `context` + `Recall.edges` / `.episodes` / "
                 "`.contested` (and each group's `.exposed`)",
        disposition="SCOPED. The visibility relation is applied to the EDGE "
                    "and EPISODE sets before rendering, and every structured "
                    "carrier is built from its output; the §4e filters run "
                    "after scope, within the visible set. Queryless (the "
                    "proactive briefing) takes the same lens on the same code "
                    "path, before assembly. The compiled wiki is EXCLUDED "
                    "from a principal-bearing response (§4d)."),

    "Memory.embed_backfill": dict(
        returns_records=False, principal="none",
        carriers="an int (vectors written); rows land in the edge_embedding "
                 "derived index, never in a caller-visible record",
        disposition="OPERATOR SURFACE by decision (0027 §4c): a host-invoked "
                    "index-maintenance verb, the export/forget row's shape. "
                    "It reads the user's own edges to embed them and returns "
                    "a count only; no record leaves the surface. Visibility "
                    "is enforced where records DO leave — "
                    "semantic_candidates filters to the lens's visible-id "
                    "set at recall (§4a Stage 1)."),

    "Memory.facts_valid_at": dict(
        returns_records=True, principal="threaded",
        carriers="`list[AsOfFact]` — the (scope-shaped) edge and its "
                 "`Resolution` per returned record",
        disposition="SCOPED, on recall's own relation (specs/0028 §4c, "
                    "V-SCOPE-DIFFERENTIAL, R3-3). The direct as-of lookup "
                    "carries `principal`/`policy` keyword-only because it "
                    "promises recall's decision: the §4a resolution builds the "
                    "same `ScopeView` and applies visibility BEFORE historical "
                    "eligibility (§3b), so the candidate set is the principal's "
                    "visible set at every T and T is never a capability; "
                    "returned edges are shaped through `ScopeView.shape`. "
                    "Unscoped (no principal) exactly as `recall` is. "
                    "Read-only: one clock read, one read window, no write."),

    "Memory.record_procedure": dict(
        returns_records=False, principal="none",
        carriers="the new edge id",
        disposition="WRITE path (specs/0037 §4b) — the sole producer of a "
                    "procedural record; returns an id, renders nothing. "
                    "Disclosure is derived (quarantine-at-birth, then the "
                    "three-axis rule), never host-supplied."),

    "Memory.describe_procedures": dict(
        returns_records=True, principal="threaded",
        carriers="`DescribeResult` — `descriptions` (summary, basis, "
                 "attribution, author, dates) and `withheld` (id + named "
                 "outcome); never the note",
        disposition="SCOPED on recall's own relation (specs/0037 §3b, "
                    "V-SCOPE-OUTERMOST): the same `ScopeView` composition as "
                    "recall — a record HIDDEN from the principal is in "
                    "NEITHER list, indistinguishable from no match; a "
                    "cross-scope-VISIBLE record is `use_only` under 0020's "
                    "shaping and yields the named non-description `use_only`, "
                    "never a description. Shows less than recall would have."),

    "Memory.answer": dict(
        returns_records=False, principal="threaded",
        carriers="the answer string, built from an internal `recall`",
        disposition="SCOPED by threading. `answer` never calls `recall` "
                    "unscoped when it was given a principal — an answer path "
                    "that dropped it would be a public bypass of the whole "
                    "boundary (external F3, V11)."),

    # ---- the operator surfaces (§2's row, §4f row 6) ----------------------
    "Memory.introspect": dict(
        returns_records=False, principal="none",
        carriers="counts by relation / author / disclosure, lifecycle state, "
                 "the wiki compile record (mode=\"categories\" adds rendered "
                 "facts)",
        disposition="UNSCOPED IN v1 BY DECISION, not by omission. This is the "
                    "OPERATOR's (and the data subject's) right-to-know "
                    "surface, not a principal surface: it answers \"what do "
                    "you know about me\", which a per-principal view would "
                    "answer falsely. Per-principal introspection is a "
                    "RECORDED WIDENING (§4f), and `test_operator_surfaces_"
                    "take_no_principal` fails if a `principal` parameter "
                    "appears here without that widening."),

    "Memory.export_memory": dict(
        returns_records=False, principal="none",
        carriers="the portable JSONL file (full provenance/history)",
        disposition="UNSCOPED IN v1 BY DECISION. Portability is an operator "
                    "right; a scope-filtered export would silently produce a "
                    "LOSSY file that reads as complete. (0021 owns what "
                    "travels; the ledger does not.)"),

    "Memory.forget": dict(
        returns_records=False, principal="none",
        carriers="`{edges, episodes}` counts; the erasure itself",
        disposition="UNSCOPED IN v1 BY DECISION. Erasure is the data "
                    "subject's right and must be TOTAL — a scoped forget "
                    "would leave residue the caller believes is gone, the "
                    "worst possible failure on this surface."),

    "Memory.redact": dict(
        returns_records=False, principal="none",
        carriers="a `RedactionReceipt`: the target's kind and id, the carrier NAMES treated, the "
                 "vocabulary reason, the marker and store versions, the journal event ref, the "
                 "ids of derived records that may still carry the content (F6), the receipt "
                 "domains it cannot vouch for — never content and never a content digest",
        disposition="AN OPERATOR SURFACE BY DECISION (specs/0041 §3b), scoped to `user_id` by "
                    "INV-5 (a cross-user or unknown target refuses with the same words, so the "
                    "existence of another user's record is not disclosed). It is a WRITE that "
                    "returns a receipt, the `forget` shape: the data subject's request must "
                    "reach every carrier the map names or none, so no principal narrows it."),

    "Memory.confirm_notice": dict(
        returns_records=False, principal="none",
        carriers="a `RedactionReceipt`, exactly `redact`'s — carrier NAMES, the reason, the marker and store "
                 "versions, the journal event ref, the derived ids (F6); never content and never a content digest",
        disposition="AN OPERATOR SURFACE BY DECISION, `redact`'s class (specs/0041 §11.6.6, T4): the user's "
                    "confirmation of a PENDING notice, applied as this store's total treatment. A WRITE that "
                    "returns a receipt; scoped to `user_id` with ONE refusal for an unknown id and another "
                    "user's (the existence of another user's notice is not disclosed). Host API only, never MCP."),

    "Memory.revoke_source": dict(
        returns_records=False, principal="none",
        carriers="the completeness statement (specs/0022 §4c): the target digest, the standing flag, the affected "
                 "record IDS with their completeness class and kind, the retire/recompute/reinstate effects (ids "
                 "and recomputed trust-field values), the class counts, `complete`, and the ledger row the commit "
                 "appends (digest, action, reason, at); never record content",
        disposition="AN OPERATOR SURFACE BY DECISION (specs/0022 §3b, R14): a trust decision about a source, for "
                    "ONE user, made by the host through the library only — no CLI verb, no MCP tool. A WRITE that "
                    "returns a statement, `redact`'s shape; the statement names record ids for the caller's own "
                    "user, which the operator can already enumerate through `introspect` and `export_memory` "
                    "(§3b: nothing becomes visible to anyone new). No principal narrows it: a revocation is "
                    "store-state for every principal, and under 0020 a scoped principal sees strictly less after "
                    "it."),
    "Memory.unrevoke_source": dict(
        returns_records=False, principal="none",
        carriers="the completeness statement, exactly `revoke_source`'s",
        disposition="AN OPERATOR SURFACE BY DECISION, `revoke_source`'s class (specs/0022 §4f): the lift, the same "
                    "computation over the new standing set. Host API only, never MCP."),
    "Memory.source_revocations": dict(
        returns_records=False, principal="none",
        carriers="one user's standing identity digests and the append-only revoke/lift history (seq, digest, "
                 "action, at, reason); digests and closed values, never record content or record ids",
        disposition="AN OPERATOR SURFACE BY DECISION (specs/0022 §4g): the operator's audit view of its own "
                    "revocations, in `policy_receipts`' class. Reads one user's rows. Host API only, never MCP."),

    "Memory.pending_notices": dict(
        returns_records=False, principal="none",
        carriers="per pending notice: its id, the target's kind and id, the pending reason, the CLAIMED "
                 "source origin and user, the time recorded — ids and closed values, never content",
        disposition="AN OPERATOR SURFACE BY DECISION (specs/0041 §11.6.6, T4): the host's list of notices "
                    "awaiting the user's `confirm_notice`, the `doctor` listing as a call. Reads one user's "
                    "rows; the claimed source is UNAUTHENTICATED testimony (0006 Q4), so it is shown, never "
                    "trusted. Carries no record content. Host API only, never MCP."),

    "Memory.edges_since": dict(
        returns_records=True, principal="none",
        carriers="`list[Edge]` — full record objects",
        disposition="UNSCOPED IN v1 BY DECISION, and NAMED here because it is "
                    "the §4f inventory's blind spot: it returns full `Edge` "
                    "objects. It is the host's CHANGE-DETECTION surface "
                    "(superseded and quarantined edges included, deliberately "
                    "so), i.e. operator/sync material in the same class as "
                    "`export_memory`, and it is not exposed over MCP. "
                    "Scoping it is a recorded widening; a host that needs a "
                    "scoped delta uses `recall(principal=…)`."),

    "Memory.list_entities": dict(
        returns_records=False, principal="none",
        carriers="per-user id + edge/episode counts",
        disposition="UNSCOPED operator/admin surface, cross-USER by nature and "
                    "deliberately not an MCP tool. Carries no record content "
                    "and no per-record identity."),

    "Memory.policy_receipts": dict(
        returns_records=False, principal="none",
        carriers="`list[PolicyReceipt]` — ids only (baseline/adjusted orders, "
                 "displaced/admitted, per-id deltas, reserved ids), the policy's "
                 "identity and tags, the minted recall_id; never content",
        disposition="UNSCOPED IN v1 BY DECISION (specs/0027 §4g, v14). This is "
                    "the HOST's audit surface over its own policy lane — it "
                    "reads every receipt the user's recalls wrote, including "
                    "recalls made under other principals' views (each receipt's "
                    "ids were themselves computed under that call's scoped scan, "
                    "Stage 0-1), so the list is cross-principal by nature: "
                    "operator material in `edges_since`'s class, carrying "
                    "per-record IDENTITY and no content, deliberately not an "
                    "MCP tool and never a principal response carrier. A "
                    "per-principal receipt view is a recorded widening; a host "
                    "that serves principals keeps receipts on its side of the "
                    "boundary."),
    "Memory.policy_receipt": dict(
        returns_records=False, principal="none",
        carriers="one `PolicyReceipt` by recall_id, or None — the same ids-only "
                 "shape",
        disposition="UNSCOPED IN v1 BY DECISION — the single-row form of "
                    "`policy_receipts`, same class, same reasoning; the "
                    "recall_id is a minted opaque key the host already holds "
                    "from the recall it audits."),

    # ---- surfaces that return no records ----------------------------------
    "Memory.remember": dict(
        returns_records=False, principal="none",
        carriers="ingest counters",
        disposition="WRITE path. 0020 changes no write, no lifecycle "
                    "transition (§3); identity partitioning at write/maintain "
                    "is 0021's."),
    "Memory.maintain": dict(
        returns_records=False, principal="none",
        carriers="the maintenance report",
        disposition="MAINTAIN path. Policy is READ-SIDE ONLY (§2, external "
                    "F5): no host policy can widen or narrow what the store "
                    "merges. 0021 rules maintenance."),
    "Memory.dispute": dict(
        returns_records=False, principal="none",
        carriers="`{disputed, relation}`",
        disposition="WRITE path (user feedback verb); no record set leaves."),
    "Memory.confirm": dict(
        returns_records=False, principal="none",
        carriers="`{confirmed, valid_from, confirmed_at, correlation_id, "
                 "replayed}`",
        disposition="WRITE path; no record set leaves."),
    "Memory.undo_restoration": dict(
        returns_records=False, principal="none",
        carriers="`{undone, undone_at, correlation_id, replayed, "
                 "already_undone}`",
        disposition="WRITE path (host-only, never MCP; specs/0044 §4i): "
                    "retires one restored value again; ids and a time "
                    "leave, no record content."),
    "Memory.reply": dict(
        returns_records=False, principal="none",
        carriers="`{reply_id, edge_id, kind, target, written_at, "
                 "correlation_id, replayed}`",
        disposition="WRITE path (host-only, never MCP; specs/0047 §4a): "
                    "appends one reply; ids, a closed kind and a time leave, "
                    "never the reply's text or the fact's content."),
    "Memory.correct": dict(
        returns_records=False, principal="none",
        carriers="`{corrected, replacement}`",
        disposition="WRITE path; no record set leaves."),
    "Memory.record_outcome": dict(
        returns_records=False, principal="none",
        carriers="`{edge_id, outcome, upgraded, times_used}`",
        disposition="WRITE path (engine-written, never MCP); no record set "
                    "leaves."),
    "Memory.import_memory": dict(
        returns_records=False, principal="none",
        carriers="`{edges, episodes, skipped, user_id, capped}`",
        disposition="WRITE path (the 0005 trust boundary); no record set "
                    "leaves."),
    "Memory.self_check": dict(
        returns_records=False, principal="none",
        carriers="content-free pass/fail counters",
        disposition="Runs against a THROWAWAY store; touches neither this "
                    "store nor any principal."),
    "Memory.flush_telemetry": dict(
        returns_records=False, principal="none",
        carriers="bool",
        disposition="Content-free aggregate. §7a: withholding rates are "
                    "DEFERRED to a future consent version — telemetry carries "
                    "no scope field in v1."),
    "Memory.telemetry_preview": dict(
        returns_records=False, principal="none",
        carriers="the aggregate a flush would send",
        disposition="Content-free; no records."),
    "Memory.report_error": dict(
        returns_records=False, principal="none",
        carriers="bool",
        disposition="Diagnostics channel, consent-gated; no record set."),
    "Memory.diagnostics_preview": dict(
        returns_records=False, principal="none",
        carriers="the captured local error log",
        disposition="Operator diagnostics; not a memory read surface."),
    "Memory.close": dict(
        returns_records=False, principal="none",
        carriers="—",
        disposition="Lifecycle."),

    # ---- MCP (§4f row 5) ---------------------------------------------------
    "mcp_server.recall_impl": dict(
        returns_records=False, principal="threaded",
        carriers="`Recall.context` (the rendered block) over MCP",
        disposition="PASSES THE HOST'S PRINCIPAL THROUGH — and adds NO MCP "
                    "tool field (§4f). The registered `recall` tool calls this "
                    "with `principal=None`, which is §5's adoption-path "
                    "honesty row: the default MCP stream supplies no "
                    "identities, so NO isolation exists on it. Docs and the "
                    "marketing rail say exactly that."),
    "mcp_server.answer_impl": dict(
        returns_records=False, principal="threaded",
        carriers="the answer string over MCP",
        disposition="Passes the host's principal through to `Memory.answer`; "
                    "no new MCP field (as above)."),
    "mcp_server.remember_impl": dict(
        returns_records=False, principal="none",
        carriers="ingest counters",
        disposition="WRITE path over MCP."),
    "mcp_server.record_procedure_impl": dict(
        returns_records=False, principal="none",
        carriers="`{ok, edge_id}` or the serialized refusal `{ok: false, refusal}`",
        disposition="WRITE path over MCP (specs/0037 §4b): the capability-gated "
                    "adapter to `Memory.record_procedure`; refuses under "
                    "`none` as an attempted elevation; renders nothing."),
    "mcp_server.describe_procedures_impl": dict(
        returns_records=True, principal="threaded",
        carriers="`DescribeResult` as JSON",
        disposition="Passes `principal` through to `Memory.describe_procedures` "
                    "(the served tool binds the deployment's user and no "
                    "principal, as `recall` does); no new MCP field."),
    "mcp_server.maintain_impl": dict(
        returns_records=False, principal="none",
        carriers="the maintenance report",
        disposition="MAINTAIN path over MCP; policy is read-side only."),
}
