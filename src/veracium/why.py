"""`veracium why <edge>` — a fact's biography, rendered from data the store already
holds. Pure READ: this module opens one read window, asks the store's public
accessors, and renders. It writes nothing and decides nothing.

    veracium why --user ida e-3f9a1c2b7d6e            # the biography of one edge
    veracium why --user ida e-3f9a1c2b7d6e --json     # the same, machine-readable
    veracium why --user ida --find "prefers"          # edges whose subject/relation/
                                                      # object contain the text, with ids

Why it exists (the developer-tools backlog, item 3, endorsed 2026-08-30 and
started on Quentin's word 2026-09-11): every decision the system makes about a
fact is silent — superseded by what, absorbed into what, why it is not
assertable, who cleared its confirmation, whether its source was revoked. All of
it is recorded (0009 outcome history, 0029's transaction-time journal, 0028's
reason-carrying supersession, 0014's contribution ledger, 0008's confirmations,
0022's revocation standing) and none of it was readable from a terminal.

What the biography carries, and where each part comes from (every accessor is
a public one that takes the edge id; nothing here reads a private surface):

  the fact        `edges(active_only=False)` filtered by id — the row VERBATIM,
                  with its provenance, volatility, validity bounds, counters
  standing        `current_state`: the three-valued source-restriction verdict
                  (0030 §4a-i) — CLEAR / RESTRICTED / UNDETERMINABLE
  journal         `edge_events(edge_id=)`: created / mutated / invalidated /
                  reinstated (0029), with the event's reason and, for a
                  mutation, WHICH fields moved (diffed here, from the states)
  confirmations   `confirmations_for`: who cleared `needs_confirmation`, when,
                  by which call path (0008)
  outcomes        `episodes(include_retired=True)` of kind "outcome" naming the
                  edge (0009: append-only judgment history)
  lineage         the edge's own `supersedes` (predecessor) and
                  `edges_superseding` (successors), each with the reason the
                  invalidated side carries (0028 §5.1)
  absorption      `contributions(user, "edge", id)` — what was consumed INTO
                  this edge; `contributions_naming(user, id)` — what this edge
                  was consumed into (0014 / 0021 §7b)
  refusals        `refusals`: supersessions refused with this edge on either
                  side (0003 — content-free, both ids)
  receipt         `supersession_receipt(user, "sup-<id>")`: the operation that
                  installed this edge as a successor, if one did (0014 §4b)

What it does NOT do: it never re-derives a verdict the store did not compute
(the restriction verdict is read, not recomputed) and it never prints another
user's data (every read is keyed by the user id given).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

# --- the field names a mutation diff reports, in a stable order --------------
_TRACKED = ("subject", "relation", "object", "note", "volatility", "valid_from",
            "invalidated_at", "invalidation_reason", "supersedes",
            "original_relation", "needs_confirmation", "agreement", "ungrounded",
            "times_used", "outcome_counts", "last_outcome", "last_outcome_at")
_PROV_TRACKED = ("author_of_evidence", "evidence_ref", "observed_at", "disclosure",
                 "confidence", "derived_from", "source_id", "origin", "record_kind",
                 "basis")


@dataclass
class Biography:
    """Everything `why` gathered, as plain data. `render()` and `to_json()` are
    the only two consumers; both are total over this shape."""
    user_id: str
    edge_id: str
    found: bool
    edge: Optional[dict] = None                 # the row, as the store serialises it
    verdict: Optional[str] = None               # RestrictionVerdict value
    revoked_source: Optional[bool] = None       # standing revocation covers its source?
    events: list = field(default_factory=list)  # [{seq, txn, kind, reason, at, changed}]
    confirmations: list = field(default_factory=list)
    outcomes: list = field(default_factory=list)
    predecessor: Optional[dict] = None          # {id, subject, relation, object, reason}
    succession: Optional[str] = None            # SuccessorDisposition value (0028 §5.1)
    successors: list = field(default_factory=list)
    absorbed: list = field(default_factory=list)      # consumed INTO this edge
    absorbed_into: list = field(default_factory=list) # this edge consumed into
    refusals: list = field(default_factory=list)
    receipt: Optional[dict] = None
    notes: list = field(default_factory=list)   # what could not be read, and why


# ----------------------------------------------------------------- gathering --
def _edge_dict(e) -> dict:
    return e.model_dump(mode="json") if hasattr(e, "model_dump") else dict(e)


def _summary(e: dict) -> str:
    return f"{e.get('subject')} {e.get('relation')} {e.get('object')}"


def _diff(prev: Optional[dict], cur: dict) -> list:
    """Which tracked fields moved between two journal states, as
    `[(name, before, after)]` — the biography's own reading of the states."""
    if prev is None:
        return []
    out = []
    for k in _TRACKED:
        if prev.get(k) != cur.get(k):
            out.append((k, prev.get(k), cur.get(k)))
    pp, cp = prev.get("provenance") or {}, cur.get("provenance") or {}
    for k in _PROV_TRACKED:
        if pp.get(k) != cp.get(k):
            out.append((f"provenance.{k}", pp.get(k), cp.get(k)))
    return out


def gather(store, user_id: str, edge_id: str) -> Biography:
    """Read everything about one edge. The window-joining accessors run inside ONE
    read window (specs/0028 §4b-o), so the row, journal, lineage, ledger, refusals
    and receipt are one snapshot. Three accessors take the store's plain (non-
    reentrant) instance lock themselves — `current_state`, `episodes` and
    `standing_revocations` —
    and the window HOLDS that lock on the owner thread, so they are read after the
    window closes: the outcome list and the revocation flag may be one write
    newer than the rest. Stated here rather than hidden; a biography is a report,
    not a transaction."""
    bio = Biography(user_id=user_id, edge_id=edge_id, found=False)
    with store.read_window(user_id):
        rows = {e.id: e for e in store.edges(user_id, active_only=False,
                                             include_quarantined=True)}
        edge = rows.get(edge_id)
        if edge is None:
            return bio
        bio.found = True
        bio.edge = _edge_dict(edge)

        # journal, with the mutation diff computed from consecutive states
        prev = None
        for ev in store.edge_events(user_id, edge_id=edge_id):
            try:
                state = json.loads(ev.state)
            except (TypeError, ValueError):
                state, note = {}, "state not JSON"
            else:
                note = None
            bio.events.append({"seq": ev.seq, "txn": ev.txn, "kind": ev.kind,
                               "reason": ev.reason, "at": ev.recorded_at,
                               "changed": _diff(prev, state) if ev.kind == "mutated" else [],
                               **({"note": note} if note else {})})
            prev = state

        for c in store.confirmations_for(user_id, edge_id):
            bio.confirmations.append({
                "at": str(c.confirmed_at), "actor": c.actor.value,
                "call_path": c.call_path.value,
                "correlation_id": c.correlation_id})

        # lineage, both directions, reasons from the invalidated side
        pred_id = bio.edge.get("supersedes")
        if pred_id:
            p = rows.get(pred_id)
            bio.predecessor = ({"id": pred_id, "fact": _summary(_edge_dict(p)),
                                "reason": _edge_dict(p).get("invalidation_reason")}
                               if p is not None else {"id": pred_id, "fact": None,
                                                      "reason": None,
                                                      "note": "predecessor row not found"})
        try:
            # specs/0028 §5.1: a SuccessorLookup — a disposition (head / superseded /
            # successor_unavailable) and the successors, oldest first
            lookup = store.edges_superseding(user_id, edge_id)
            bio.succession = lookup.disposition.value
            for s in lookup.successors:
                sd = _edge_dict(s)
                bio.successors.append({"id": sd.get("id"), "fact": _summary(sd),
                                       "reason": bio.edge.get("invalidation_reason")})
        except Exception as ex:                                   # noqa: BLE001
            bio.notes.append(f"successors unreadable: {type(ex).__name__}")

        for r in store.contributions(user_id, "edge", edge_id):
            rd = r.model_dump(mode="json") if hasattr(r, "model_dump") else dict(r)
            bio.absorbed.append({"site": rd.get("site"), "at": str(rd.get("created_at")),
                                 "contributor_type": rd.get("contributor_type"),
                                 "contributor_ref": rd.get("contributor_ref")})
        for r in store.contributions_naming(user_id, edge_id):
            bio.absorbed_into.append({"survivor_type": r.get("survivor_type"),
                                      "survivor_id": r.get("survivor_id"),
                                      "site": r.get("site")})

        for r in store.refusals(user_id):
            rd = r.model_dump(mode="json") if hasattr(r, "model_dump") else dict(r)
            if edge_id in (rd.get("prior_edge_id"), rd.get("incoming_edge_id")):
                bio.refusals.append({
                    "role": "prior" if rd.get("prior_edge_id") == edge_id else "incoming",
                    "other": rd.get("incoming_edge_id") if rd.get("prior_edge_id") == edge_id
                             else rd.get("prior_edge_id"),
                    "at": str(rd.get("created_at")), "rule_version": rd.get("rule_version")})

        bio.receipt = store.supersession_receipt(user_id, f"sup-{edge_id}")

    # outside the window: `current_state` opens and closes its OWN window and
    # consults the revocation standing under the lock, so it runs here too
    try:
        cs = store.current_state(user_id, edge_id)
        bio.verdict = cs.source_restricted.value
    except Exception as ex:                                       # noqa: BLE001
        bio.notes.append(f"restriction verdict unreadable: {type(ex).__name__}")
    try:
        from .source_identity import resolve_origin, source_identity_digest
        prov = bio.edge.get("provenance") or {}
        # 0006 §4 rule 6: a locally stored record has no `origin` on the row; it
        # resolves to THIS store's minted identity before any digest
        d = source_identity_digest(resolve_origin(prov.get("origin"), store.local_origin()),
                                   prov.get("source_id"))
        bio.revoked_source = (d in store.standing_revocations(user_id)) if d else None
    except Exception as ex:                                       # noqa: BLE001
        bio.notes.append(f"revocation standing unreadable: {type(ex).__name__}")
    for ep in store.episodes(user_id, include_retired=True):
        if ep.kind == "outcome" and ep.edge_id == edge_id:
            bio.outcomes.append({
                "date": ep.date, "outcome": ep.outcome.value if ep.outcome is not None else None,
                "evidence_ref": ep.provenance.evidence_ref,
                "actor": ep.provenance.author_of_evidence.value,
                "retired_reason": ep.retired_reason})
    bio.outcomes.sort(key=lambda o: (o["date"] or ""))
    return bio


def find(store, user_id: str, text: str) -> list:
    """Edges whose subject, relation or object contains `text` (case-insensitive),
    with ids — the lookup a terminal user needs, since no other verb prints ids."""
    needle = text.casefold()
    out = []
    for e in store.edges(user_id, active_only=False, include_quarantined=True):
        d = _edge_dict(e)
        if any(needle in str(d.get(k) or "").casefold() for k in ("subject", "relation", "object")):
            out.append({"id": d.get("id"), "fact": _summary(d), "active": bool(e.active),
                        "quarantined": bool(e.quarantined),
                        "invalidation_reason": d.get("invalidation_reason")})
    return out


# ----------------------------------------------------------------- rendering --
def _fmt(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (dict, list)):
        return json.dumps(v, sort_keys=True)
    return str(v)


def render(bio: Biography) -> str:
    if not bio.found:
        return (f"no edge {bio.edge_id!r} for user {bio.user_id!r} "
                f"(try: veracium why --user {bio.user_id} --find <text>)")
    e = bio.edge or {}
    prov = e.get("provenance") or {}
    out = [f"{_summary(e)}", f"  id            {e.get('id')}"]
    state = "active" if e.get("invalidated_at") is None else (
        f"retired ({e.get('invalidation_reason') or 'no reason recorded'} at {e.get('invalidated_at')})")
    out += [
        f"  state         {state}",
        f"  volatility    {_fmt(e.get('volatility'))}   valid_from {_fmt(e.get('valid_from'))}",
        f"  evidence      author={_fmt(prov.get('author_of_evidence'))} disclosure={_fmt(prov.get('disclosure'))} "
        f"confidence={_fmt(prov.get('confidence'))} observed_at={_fmt(prov.get('observed_at'))}",
        f"  evidence_ref  {_fmt(prov.get('evidence_ref'))}"
        + (f"   derived_from={prov.get('derived_from')}" if prov.get("derived_from") else "")
        + (f"   {prov.get('record_kind')}/{prov.get('basis')}" if prov.get("record_kind") else ""),
        f"  source        origin={_fmt(prov.get('origin'))} source_id={_fmt(prov.get('source_id'))} "
        f"revoked={_fmt(bio.revoked_source)}   restriction verdict: {_fmt(bio.verdict)}",
        f"  flags         needs_confirmation={_fmt(e.get('needs_confirmation'))} "
        f"ungrounded={_fmt(e.get('ungrounded'))} agreement={_fmt(e.get('agreement'))}",
        f"  use           times_used={_fmt(e.get('times_used'))} last_outcome={_fmt(e.get('last_outcome'))} "
        f"outcome_counts={_fmt(e.get('outcome_counts'))}",
    ]
    if bio.predecessor:
        p = bio.predecessor
        out.append(f"  supersedes    {p['id']}  {_fmt(p.get('fact'))}"
                   f"  (that edge retired: {_fmt(p.get('reason'))}){'  ' + p['note'] if p.get('note') else ''}")
    for s in bio.successors:
        out.append(f"  superseded by {s['id']}  {_fmt(s.get('fact'))}  (this edge retired: {_fmt(s.get('reason'))})")
    if bio.succession == "successor_unavailable":
        out.append("  superseded by (a successor this reader cannot see — 0028 §5.1 successor_unavailable)")
    if bio.receipt:
        # specs/0014 §4b: every edge the ingest installs has a receipt keyed
        # `sup-<id>` (the supersession pass runs whether or not a predecessor
        # existed), so this is the WRITE receipt, not evidence of a supersession
        out.append(f"  write receipt sup-{e.get('id')} status={bio.receipt.get('status')} (specs/0014 §4b)")
    for a in bio.absorbed:
        out.append(f"  absorbed      {a['contributor_type'] or '?'} {a['contributor_ref'] or '(untyped, pre-v8)'} "
                   f"at site {a['site']} ({a['at']})")
    for a in bio.absorbed_into:
        out.append(f"  absorbed into {a['survivor_type']} {a['survivor_id']} at site {a['site']}")
    for r in bio.refusals:
        out.append(f"  refusal       as {r['role']} vs {r['other']} at {r['at']} (rule {r['rule_version']})")

    out.append("")
    out.append("timeline")
    if not bio.events:
        out.append("  (no journal events — the store predates the 0029 journal for this edge, "
                   "or the edge was never journaled)")
    for ev in bio.events:
        line = f"  {ev['at']}  txn {ev['txn']}  {ev['kind']}"
        if ev.get("reason"):
            line += f" ({ev['reason']})"
        out.append(line)
        for name, before, after in ev.get("changed", []):
            out.append(f"      {name}: {_fmt(before)} -> {_fmt(after)}")
        if ev.get("note"):
            out.append(f"      {ev['note']}")
    for c in bio.confirmations:
        out.append(f"  {c['at']}  confirmed by {c['actor']} via {c['call_path']} (correlation {c['correlation_id']})")
    for o in bio.outcomes:
        retired = f"  [retired: {o['retired_reason']}]" if o.get("retired_reason") else ""
        out.append(f"  {o['date']}  outcome {o['outcome']} by {o['actor']} (evidence {o['evidence_ref']}){retired}")
    for n in bio.notes:
        out.append(f"  note: {n}")
    return "\n".join(out) + "\n"


def to_json(bio: Biography) -> dict:
    # `dataclasses.asdict`, never a dunder or a variable-named getattr: the 0031
    # attribute census refuses both forms anywhere in src/ (a literal getattr
    # would need a tabled allowance; this module uses none)
    d = asdict(bio)
    # tuples from the diff become lists so the document round-trips
    for ev in d["events"]:
        ev["changed"] = [list(c) for c in ev.get("changed", [])]
    return d


def render_find(user_id: str, text: str, hits: list) -> str:
    if not hits:
        return f"no edge for user {user_id!r} mentions {text!r}\n"
    out = []
    for h in hits:
        tag = "active" if h["active"] else f"retired:{h['invalidation_reason'] or '?'}"
        if h["quarantined"]:
            tag += ",quarantined"
        out.append(f"  {h['id']}  {h['fact']}  [{tag}]")
    return "\n".join(out) + "\n"
