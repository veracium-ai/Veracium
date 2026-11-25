"""specs/0055 §4f: the finder, the remedy, and what the remedy cannot reach.

`scan(store)` runs the recogniser over every carrier census E lists (`SqliteStore.credential_carriers`) and reports by
CARRIER CLASS, with counts and class names. A record is named by its id when the id carries no shape, and otherwise by a
PER-REPORT ORDINAL (`record 3 of this report`), never by a value, length, offset or digest (§4g's locator rule).

`act(memory, hits)` applies the field-level remedy of §4f's matrix, in one process, keyed on the raw ids it holds
privately (never on a printed ordinal and never on a withheld text):
  - an edge's or an episode's text            -> 0041 `redact` of that record (reason `operator_policy`);
  - a journal row (`edge_event`/`episode_event`) -> 0041 `redact` of its PARENT record (the tombstone covers history);
  - a reply's text                             -> 0041 `redact` of the reply's parent EDGE;
  - the compiled wiki                          -> discarded (it is rebuilt from masked reads, §4e).
Provenance identifiers, reply targets, correlation ids and contribution-ledger payloads are RESIDUAL: 0041 keeps
identities by design (§10 Q7). The total remedy for a user's database rows is `forget_user`.

A 0041 receipt is NOT proof of removal; the second scan is (I18). And a shape scan cannot see inside a digest, so the
report always lists the opaque residual digest domains as DECLARED and UNVOUCHED, whether or not a raw token was found
(round 3's build note).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import credentials as _cred

#: the action for each removable carrier class (§4f's matrix)
REMEDY = {
    "edge.text": "0041 redact of the edge",
    "episode.text": "0041 redact of the episode",
    "edge_event.state": "0041 redact of the parent edge (the tombstone covers its history)",
    "episode_event.state": "0041 redact of the parent episode (the tombstone covers its history)",
    "reply.text": "0041 redact of the reply's parent edge",
    # census E :83: a 0041 redaction of EITHER edge rewrites the refusal's relation; the finder targets the prior edge
    "supersession_refusal.relation": "0041 redact of the refusal's prior edge (a redaction of either edge rewrites it)",
    "wiki.text": "discard the compiled wiki (rebuilt from masked reads)",
}
#: carriers no targeted remedy reaches, by name: residual, reported as such; forget_user removes them. Since round 4
#: (R4-04, research's S1) the finder FAILS CLOSED: EVERY class not in REMEDY is residual — the `<record>.other`,
#: `<kind>.unparsed`, `<journal>.reason` and `<table>.<column>` classes the store's read yields for a string no class
#: names (`SqliteStore.credential_carriers`). This tuple is the named part only; `is_residual` is the rule.
RESIDUAL = ("edge.identifier", "episode.identifier", "edge_event.identifier", "episode_event.identifier",
            "reply.identifier", "confirmation.identifier", "request_registry.identifier", "contribution_ledger.payload")


def is_residual(carrier: str) -> bool:
    """Every carrier class no targeted remedy reaches — every class not in REMEDY (fail closed)."""
    return carrier not in REMEDY

#: opaque digest domains: DECLARED and UNVOUCHED, never inferred absent because no raw token was found
DECLARED_OPAQUE = (
    ("supersession receipts", "request, logical and outcome digests over a stored prior (0055 D2 content_residual; "
                              "0041 D4): a redaction of the prior cannot vouch for them; forget_user removes them"),
    ("source_revocations.identity_digest", "D3's identity digest of a revoked or lifted credential-shaped legacy "
                                           "source: 0041 does not reach it; forget_user removes it"),
    ("migration_op.inputs_digest", "a converting import's whole-file digest: store-level, never erased; it "
                                   "SURVIVES forget_user"),
    ("host AuditLog", "D3's identity digest on a revoke_source / unrevoke_source line: the host's file, outside "
                      "the store; it SURVIVES forget_user"),
    # round 4's A1 (v0.5.5's I19-F1, D3's form): the same identity digest, as maintain()'s pool key
    ("maintain() consolidate-pool / pool_key", "a scope's source identity digest, RETURNED to maintain()'s caller "
                                               "and LOGGED on the host AuditLog's consolidate-pool line: outside "
                                               "the store; it SURVIVES forget_user"),
)
#: what lives outside the store's tables, and so outside every remedy here
OUTSIDE_REMEDY = ("the host AuditLog (user_id in plaintext, counts, D3's digests)", "exports and backups",
                  "the diagnostics log file", "freed database pages (an SQLite build without SECURE_DELETE)")


@dataclass
class Hit:
    """One carrier field holding at least one credential shape. Holds ids (the action's private key) and class
    counts; never the text."""
    user_id: str
    table: str
    carrier: str
    record_kind: str
    record_id: str
    parent_kind: str
    parent_id: str
    classes: dict = field(default_factory=dict)

    @property
    def removable(self) -> bool:
        return not is_residual(self.carrier)


def scan(store, user_id: Optional[str] = None) -> list[Hit]:
    """Every carrier field with a credential shape, merged per (user, carrier, record), in a stable order."""
    merged: dict = {}
    for uid, table, carrier, kind, rid, pkind, pid, text in store.credential_carriers(user_id):
        found = _cred.scan(text)
        if not found:
            continue
        key = (uid, carrier, kind, rid)
        h = merged.get(key)
        if h is None:
            h = merged[key] = Hit(uid, table, carrier, kind, rid, pkind, pid)
        for f in found:
            h.classes[f.cls] = h.classes.get(f.cls, 0) + 1
    return sorted(merged.values(), key=lambda h: (h.user_id, h.carrier, h.record_kind, h.record_id))


def _shaped(value) -> bool:
    return isinstance(value, str) and _cred.first_class(value) is not None


def locators(hits: list[Hit]) -> list[str]:
    """§4g: a record by its id when neither its id, its user's id nor its parent's id carries a shape; otherwise by a
    per-report ordinal with its table and carrier class."""
    out = []
    for n, h in enumerate(hits, 1):
        if _shaped(h.record_id) or _shaped(h.parent_id) or _shaped(h.user_id):
            out.append(f"record {n} of this report ({h.table}, {h.carrier})")
        else:
            out.append(f"{h.record_kind} {h.record_id} of user {h.user_id} ({h.carrier})")
    return out


def report(hits: list[Hit]) -> dict:
    """The finder's report: per carrier class, the records and the class counts; each record by its locator with its
    remedy or `residual`; the declared opaque domains and what lies outside the remedy. Content-free."""
    by_carrier: dict = {}
    for h in hits:
        slot = by_carrier.setdefault(h.carrier, {"records": 0, "classes": {}})
        slot["records"] += 1
        for c, n in h.classes.items():
            slot["classes"][c] = slot["classes"].get(c, 0) + n
    return {
        "shapes_version": _cred.CREDENTIAL_SHAPES_VERSION,
        "carriers": dict(sorted(by_carrier.items())),
        "records": [{"locator": loc, "carrier": h.carrier, "classes": dict(sorted(h.classes.items())),
                     "remedy": REMEDY.get(h.carrier, "residual: no targeted remedy; forget_user removes it")}
                    for h, loc in zip(hits, locators(hits))],
        "residual": any(not h.removable for h in hits),
        "declared_opaque": [{"domain": d, "note": n} for d, n in DECLARED_OPAQUE],
        "outside_remedy": list(OUTSIDE_REMEDY),
    }


def targets(hits: list[Hit]) -> tuple[list, list]:
    """The actions §4f's matrix assigns: ([(user, kind, id)] to redact, deduplicated, in order; [user] whose wiki to
    discard)."""
    redact, wiki = [], []
    for h in hits:
        if h.carrier == "wiki.text":
            if h.user_id not in wiki:
                wiki.append(h.user_id)
        elif h.removable:
            kind = "edge" if h.parent_kind == "edge" else "episode"
            t = (h.user_id, kind, h.parent_id)
            if t not in redact:
                redact.append(t)
    return redact, wiki


def act(memory, hits: list[Hit]) -> list[dict]:
    """Apply the remedy, one target at a time, by the raw ids held here. Returns one content-free line per target:
    its locator-safe label, the action and its outcome (`redacted`, `already redacted`, `discarded`, or the outward
    formatter's text of a refusal). Never trusted as proof: the caller re-scans (I18)."""
    redact, wiki = targets(hits)
    out = []
    for n, (uid, kind, rid) in enumerate(redact, 1):
        label = (f"target {n} ({kind})" if _shaped(rid) or _shaped(uid) else f"{kind} {rid} of user {uid}")
        try:
            kw = {"edge_id": rid} if kind == "edge" else {"episode_id": rid}
            r = memory.redact(uid, reason="operator_policy", **kw)
            repeated = bool(r.get("repeated")) if isinstance(r, dict) else bool(r.repeated)
            out.append({"target": label, "action": "redact", "outcome": "already redacted" if repeated else "redacted"})
        except Exception as exc:                                   # noqa: BLE001 - reported, content-free
            out.append({"target": label, "action": "redact", "outcome": _cred.outward_text(exc)})
    for uid in wiki:
        label = "a user's wiki" if _shaped(uid) else f"wiki of user {uid}"
        row = memory.store.get_wiki(uid)
        ok = row is not None and memory.store.discard_wiki(uid, row[0], row[1])
        out.append({"target": label, "action": "discard", "outcome": "discarded" if ok else "not present"})
    return out


def render(rep: dict, *, title: str = "credential-shaped text at rest") -> str:
    lines = [f"veracium credentials — {title} (rule set v{rep['shapes_version']})"]
    if not rep["carriers"]:
        lines.append("  no credential shape found in any scanned carrier")
    for carrier, slot in rep["carriers"].items():
        cls = ", ".join(f"{c} {n}" for c, n in sorted(slot["classes"].items()))
        lines.append(f"  {carrier:30s} {slot['records']} record(s): {cls}")
    for r in rep["records"]:
        lines.append(f"    {r['locator']}: {r['remedy']}")
    lines.append("  declared opaque digest domains (a shape scan cannot see inside a digest; unvouched, never "
                 "inferred clean):")
    for d in rep["declared_opaque"]:
        lines.append(f"    {d['domain']}: {d['note']}")
    lines.append("  outside every remedy here: " + "; ".join(rep["outside_remedy"]))
    if rep["residual"]:
        lines.append("  RESIDUAL: some matches have no targeted remedy (0041 keeps identities); `forget_user` removes "
                     "the user's database rows")
    return "\n".join(lines) + "\n"
