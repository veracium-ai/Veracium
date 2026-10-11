"""Reference model for 0044 stage 1 (accumulation) — the migration, undo, doctor and portability rules of
research's ARITY-MIGRATION-TRANSITIONS-DRAFT (draft 2, research 74c51aaf, sha256 ff39bb49…), executed.

A MODEL, not product code: it imports nothing from `veracium`. Each rule of the draft is one function here, named by
its section, so a reader can hold the two side by side. Where the draft is ambiguous the model does NOT resolve it
silently: the ambiguity is a named switch (`Rules`), both settings are executed, and the run reports what each
produces. Product tests bind the same properties to the shipped code at the implementation gate (R1-10's split).

Run: `python arity_model.py` → prints a summary and writes `arity-model-results.json` beside itself; exit 0 iff every
invariant holds on the draft's rules AND every declared mutant is killed by exactly the invariant that names it.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys
from dataclasses import dataclass, field

MARKER = "\x00redacted\x00"
PLAN_RELATIONS = ("measures", "prefers", "health_state")


# ----------------------------------------------------------------------------------------------- the state
@dataclass
class Edge:
    id: str
    user: str
    relation: str
    obj: str
    source: str = "src-a"
    active: bool = True
    invalidated_at: int | None = None
    reason: str | None = None
    supersedes: str | None = None
    counters: int = 0
    basis: tuple = ()           # contribution-derived sources (0022 recompute/basis)


@dataclass
class Store:
    edges: dict = field(default_factory=dict)
    clock: int = 0
    revoked: set = field(default_factory=set)          # 0022 standing revocations
    attested_redactions: set = field(default_factory=set)
    refusals: list = field(default_factory=list)       # (prior, incoming, relation, t)
    plan: dict = field(default_factory=dict)           # relation -> {plan_id, effective_at}
    runs: dict = field(default_factory=dict)           # (plan_id, user) -> {op_id, committed_at}
    outcomes: dict = field(default_factory=dict)       # (plan_id, edge_id) -> row
    undo_ids: dict = field(default_factory=dict)       # (user, correlation_id) -> (plan_id, edge_id, digest, result)
    journal: list = field(default_factory=list)        # store-local (0029 V-INERT): never exported

    def tick(self) -> int:
        self.clock += 1
        return self.clock


@dataclass
class Rules:
    """The draft's open points (§11) and the ambiguities the model found, as executable switches. Defaults = the draft
    as written; a non-default value is an ALTERNATIVE the run also executes."""
    singleton_ambiguity: str = "inf"               # draft 2 §11.1 ruling (draft 1 open; "zero" kept as the alternative)
    empty_run_row_for_new_user: bool = True        # draft 2 §11.2 ruling
    default_import_earns_exemption: bool = False   # draft 2 §11.3 ruling: trusted restore only
    undo_id_scope: str = "user"                    # draft 2 F2: user-scoped, shared with 0008 (draft 1: "plan_edge")
    undo_without_id_duplicate: str = "replay_state"  # draft 2 F3: the recorded "already undone at T" (draft 1: "refuse")
    redaction_check_before_relation: bool = False  # F1: kept only to show the reordering is UNRECORDABLE
    time_test_on_import: bool = False              # draft 2 F5: the effective_at test applies to LOCAL rows only


# ----------------------------------------------------------------------------------------------- shipped behaviour (modelled)
def supersede_single(s: Store, prior: Edge, incoming: Edge):
    """Pre-migration, `single` arity: a differing value retires the prior (graph.py's functional branch)."""
    t = s.tick()
    prior.active, prior.invalidated_at, prior.reason = False, t, "superseded"
    if incoming.supersedes is None:              # ONE pointer, even when several priors retire (R1-04)
        incoming.supersedes = prior.id
    s.edges[incoming.id] = incoming
    s.journal.append(("invalidated", prior.id, t))


def redact(s: Store, edge_id: str):
    """0041: REPLACE relation/object with the marker, attest it."""
    e = s.edges[edge_id]
    e.relation, e.obj = MARKER, MARKER
    s.attested_redactions.add(edge_id)


def would_be_revoked(s: Store, e: Edge) -> bool:
    """§3.3 — the sweep's OWN predicate, evaluated for `e` as if active: its source or any contribution-basis source is
    in the standing set. (The product binds this to 0022's sweep, never a re-derivation; the model encodes the rule.)"""
    return e.source in s.revoked or any(b in s.revoked for b in e.basis)


# ----------------------------------------------------------------------------------------------- §2 the plan
def write_plan(s: Store, registry: dict) -> dict:
    """§2: a relation enters the plan only if the effective registry declares it canonically as the default."""
    t = s.tick()
    for rel in PLAN_RELATIONS:
        if registry.get(rel, "default") == "default":
            s.plan[rel] = {"plan_id": f"plan-{rel}", "effective_at": t}
    return s.plan


# ----------------------------------------------------------------------------------------------- §3 eligibility
def consider(s: Store, e: Edge, rules: Rules, imported: bool = False) -> str | None:
    """§3: None = not considered; else `restored` or `withheld_revoked`. `imported`: a pre-arity-format incoming row,
    for which the effective_at time test does NOT apply (F5: every such superseded row was retired under single)."""
    redacted = (MARKER in (e.relation, e.obj)) or (e.id in s.attested_redactions)
    if rules.redaction_check_before_relation and redacted and e.reason == "superseded":
        return "withheld_redacted"
    p = s.plan.get(e.relation)
    timed = (not imported) or rules.time_test_on_import
    if not (p and e.reason == "superseded" and e.invalidated_at is not None
            and (not timed or e.invalidated_at < p["effective_at"])):
        return None                                                    # (1)
    if (p["plan_id"], e.id) in s.outcomes:
        return None                                                    # (4): once per plan, ever
    if redacted:
        return None                                                    # (2) defence in depth: tombstones are never considered
    if would_be_revoked(s, e):
        return "withheld_revoked"                                      # (3)
    return "restored"


# ----------------------------------------------------------------------------------------------- §4–§5 the operation
class Crash(Exception):
    pass


def migrate_user(s: Store, user: str, rules: Rules, op_id: str, crash_at: str | None = None):
    """§5 per-user phase, one transaction: work on a COPY and swap it in only at COMMIT (so a crash before commit leaves
    nothing changed)."""
    tx = copy.deepcopy(s)
    plan_ids = {p["plan_id"] for p in tx.plan.values()}
    if all((pid, user) in tx.runs for pid in plan_ids):
        return "skipped"
    t = tx.tick()
    n = 0
    for e in sorted(tx.edges.values(), key=lambda x: x.id):
        if e.user != user:
            continue
        out = consider(tx, e, rules)
        if out is None:
            continue
        p = tx.plan[e.relation]
        succ = sorted(x.id for x in tx.edges.values() if x.supersedes == e.id)
        tx.outcomes[(p["plan_id"], e.id)] = {
            "user": user, "outcome": out, "pre_invalidated_at": e.invalidated_at, "pre_reason": e.reason,
            "successor_evidence": ("pointer", succ) if succ else ("none", []), "undone_at": None, "op_id": op_id}
        if out == "restored":
            e.active, e.invalidated_at, e.reason = True, None, None
            tx.journal.append(("reinstated", e.id, t, "arity_reclassified"))
        n += 1
        if crash_at == "mid_user" and n == 1:
            raise Crash("before commit")
    for pid in plan_ids:
        if n or rules.empty_run_row_for_new_user:
            tx.runs[(pid, user)] = {"op_id": op_id, "committed_at": t}
    s.__dict__.update(tx.__dict__)                                     # COMMIT
    if crash_at == "after_commit":
        raise Crash("after commit, before delivery")
    return "committed"


def migrate(s: Store, rules: Rules, op_id="op-1", crash_user=None, crash_at=None):
    users = sorted({e.user for e in s.edges.values()})
    for u in users:
        migrate_user(s, u, rules, op_id, crash_at if u == crash_user else None)


def receipt(s: Store, user: str) -> list:
    """§4: a VIEW over migration_outcome; object text rendered from the LIVE edge at delivery."""
    rows = []
    for (pid, eid), o in sorted(s.outcomes.items()):
        if o["user"] != user:
            continue
        kind, succ = o["successor_evidence"]
        rows.append({"edge": eid, "outcome": o["outcome"], "object": s.edges[eid].obj,
                     "replaced_by": succ if kind == "pointer" else "unknown", "undone": o["undone_at"] is not None})
    return rows


# ----------------------------------------------------------------------------------------------- §6 undo
class Refused(Exception):
    pass


def _digest(user, edge_id, plan_id) -> str:
    return hashlib.sha256(f"undo_restoration|{user}|{edge_id}|{plan_id}".encode()).hexdigest()


def undo(s: Store, user: str, edge_id: str, rules: Rules, correlation_id: str | None = None):
    e = s.edges[edge_id]
    p = s.plan.get(e.relation)
    key = next(((pid, eid) for (pid, eid) in s.outcomes if eid == edge_id), None)
    if key is None:
        raise Refused("no migration outcome for this edge")
    pid = key[0]
    digest = _digest(user, edge_id, pid)
    if correlation_id is not None:
        rec = s.undo_ids.get((user, correlation_id))
        if rec is not None:
            same_target = (rec[0], rec[1]) == (pid, edge_id)
            if rules.undo_id_scope == "user" or same_target:
                if rec[2] == digest:
                    return rec[3]                                       # replay the recorded result
                raise Refused("correlation id reused for a different request")
            # draft as written: the lookup is per (plan, edge), so a reused id on ANOTHER edge falls through
    o = s.outcomes[key]
    if o["outcome"] != "restored":
        raise Refused(f"not restored ({o['outcome']})")
    if o["undone_at"] is not None:
        if rules.undo_without_id_duplicate == "replay_state":
            return {"undone": edge_id, "already_undone_at": o["undone_at"]}
        raise Refused("already undone")
    if not e.active or e.invalidated_at is not None:
        raise Refused(f"retired since restoration ({e.reason})")
    t = s.tick()
    e.active, e.invalidated_at, e.reason = False, o["pre_invalidated_at"], o["pre_reason"]   # per field
    o["undone_at"] = t
    result = {"undone": edge_id, "already_undone_at": None}
    if correlation_id is not None:
        s.undo_ids[(user, correlation_id)] = (pid, edge_id, digest, result)
    s.journal.append(("invalidated", edge_id, t, "superseded"))
    return result


# ----------------------------------------------------------------------------------------------- §7 doctor
def doctor_refs(s: Store) -> list:
    """`refs`: an active edge whose `supersedes` predecessor is ALSO active warns, unless §7's exemption applies."""
    out = []
    for e in s.edges.values():
        pred = s.edges.get(e.supersedes) if e.supersedes else None
        if e.active and pred is not None and pred.active:
            ex = any(eid == pred.id and o["outcome"] == "restored" and o["undone_at"] is None
                     and o.get("trusted", True) for (pid, eid), o in s.outcomes.items())
            out.append(("info" if ex else "warn", e.id, pred.id))
    return out


# ----------------------------------------------------------------------------------------------- §8 portability
def export(s: Store, user: str, fmt: str = "post") -> dict:
    """Edges + migration_outcome rows (never the journal: 0029 V-INERT)."""
    edges = [copy.deepcopy(e) for e in s.edges.values() if e.user == user]
    outs = {k: copy.deepcopy(v) for k, v in s.outcomes.items() if v["user"] == user} if fmt == "post" else {}
    return {"format": fmt, "edges": edges, "outcomes": outs}


def import_file(s: Store, f: dict, mode: str, rules: Rules, op_id="op-import"):
    """§8. Returns the import receipt. Collision rule (NOT in the draft): an incoming id already held locally is SKIPPED,
    and conversion never considers it — the model makes the rule explicit so it can be checked."""
    tx = copy.deepcopy(s)
    rec = {"converted": [], "unknown_linkage": [], "refused": [], "skipped_collisions": []}
    incoming = {e.id for e in f["edges"]}
    for (pid, eid), o in f["outcomes"].items():
        if eid not in incoming:
            rec["refused"].append(eid)
    for e in f["edges"]:
        if e.id in tx.edges:
            rec["skipped_collisions"].append(e.id)
            continue
        tx.edges[e.id] = copy.deepcopy(e)
    for (pid, eid), o in f["outcomes"].items():
        if eid in incoming and eid not in rec["skipped_collisions"]:
            row = copy.deepcopy(o)
            row["trusted"] = (mode == "trusted") or rules.default_import_earns_exemption
            tx.outcomes[(pid, eid)] = row
    new = [tx.edges[e.id] for e in f["edges"] if e.id not in rec["skipped_collisions"]]
    if f["format"] == "pre":
        for e in new:                                                   # conversion: incoming rows ONLY
            out = consider(tx, e, rules, imported=True)
            if out is None:
                continue
            p = tx.plan[e.relation]
            tx.outcomes[(p["plan_id"], e.id)] = {"user": e.user, "outcome": out, "pre_invalidated_at": e.invalidated_at,
                                                 "pre_reason": e.reason, "successor_evidence": ("none", []),
                                                 "undone_at": None, "op_id": op_id, "trusted": True}
            if out == "restored":
                e.active, e.invalidated_at, e.reason = True, None, None
            rec["converted"].append((e.id, out))
    else:
        for e in new:
            p = tx.plan.get(e.relation)
            if p and e.reason == "superseded" and (p["plan_id"], e.id) not in tx.outcomes:
                rec["unknown_linkage"].append(e.id)
    s.__dict__.update(tx.__dict__)
    return rec


# ----------------------------------------------------------------------------------------------- §9 the 0003 ordering key
def order_key(group: list, o_reading: str = "other_than_top", negative: str = "as_is", slot: str = "s") -> tuple:
    """The 0003 amendment v1.3 §4a (research 7ae526f5). `group`: members as (authority, kind), kind ∈ {"R" emitted for
    the principal, "O" visible but not emitted, "U" UNRESOLVED/hidden — never used}. Key = (top1 over R DESC,
    ambiguity ASC, |R∪O| DESC, slot ASC); a group with R empty sorts LAST.

    `o_reading` — the draft's "O = the other visible members" read two ways (a finding): "other_than_top" = every
    visible member except the top-1 member; "non_emitted" = only the visible-but-not-emitted members.
    `negative` — QO4: a negative ambiguity (a visible non-emitted member above top1) as computed ("as_is", ranks first)
    or clamped to rank last within the tier ("last")."""
    R = sorted((a for a, k in group if k == "R"), reverse=True)
    V = sorted((a for a, k in group if k in ("R", "O")), reverse=True)
    if not R:
        return (1, 0, 0, 0, slot)                                       # nothing renderable: last
    top1 = R[0]
    if o_reading == "other_than_top":
        rest = list(V); rest.remove(top1)
    else:
        rest = [a for a, k in group if k == "O"]
    amb = (top1 - max(rest)) if rest else float("inf")
    if amb < 0 and negative == "last":
        amb = float("inf")
    return (0, -top1, amb, -len(V), slot)


# ----------------------------------------------------------------------------------------------- §1 retained refusals
def contested_pairs(s: Store) -> list:
    """§1 / draft 2 §11.4: a refusal recorded while the relation was `single` (t < effective_at) keeps its contested
    rendering until an existing verb retires a member; `multi` records no new refusals. No expiry."""
    out = []
    for prior, incoming, rel, t in s.refusals:
        p = s.plan.get(rel)
        if p and t >= p["effective_at"]:
            continue
        if s.edges[prior].active and s.edges[incoming].active:
            out.append((prior, incoming))
    return out
