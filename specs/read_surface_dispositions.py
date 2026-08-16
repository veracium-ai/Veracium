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
    "mcp_server.maintain_impl": dict(
        returns_records=False, principal="none",
        carriers="the maintenance report",
        disposition="MAINTAIN path over MCP; policy is read-side only."),
}
