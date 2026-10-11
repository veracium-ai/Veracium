"""Reference model for package II (0045 grounding × 0047 replies × confirmations): research's
GROUNDING-REPLY-TRANSITIONS-DRAFT (draft 2, research 93b0d285, sha256 d9ec36f4…), executed.

A MODEL, not product code: no `veracium` import. One function per rule section. Ambiguities are named switches
(`Rules`); the run executes both settings and reports, never resolving them silently.
"""
from __future__ import annotations

import copy
import hashlib
import hmac
from dataclasses import dataclass, field

MARKER = "\x00redacted\x00"
GROUNDING_VERSION = 16        # the schema version at which the grounding predicate became the write gate (§2)


@dataclass
class Edge:
    id: str
    user: str
    relation: str
    obj: str
    ungrounded: bool
    version: int                       # the schema version it was written at (§2's version evidence)
    flag_by: str = "predicate"         # who set `ungrounded`: "predicate" | "absorption_or" (0019/0014's OR rule)
    active: bool = True
    author: str = "user"               # effective author: user | assistant | third_party
    disclosure: str = "mentionable"
    origin: str = "local"              # local | imported (default import) | restored (trusted)


@dataclass
class Reply:
    id: str
    edge: str
    kind: str                          # challenge | context | withdrawn-consent | resolve
    text: str
    t: int
    target: str | None = None          # resolve -> challenge id
    origin: str = "local"


@dataclass
class Confirmation:
    id: str
    edge: str
    t: int
    actor: str
    correlation_id: str
    digest: str
    origin: str = "local"


@dataclass
class Store:
    edges: dict = field(default_factory=dict)
    replies: list = field(default_factory=list)
    confirmations: list = field(default_factory=list)
    clock: int = 100
    key: bytes = b"store-key-1"
    redacted_episodes: set = field(default_factory=set)
    revoked_sources: set = field(default_factory=set)
    forgotten_users: set = field(default_factory=set)
    corr: dict = field(default_factory=dict)       # (user, correlation_id) -> (digest, result)
    counts: dict = field(default_factory=lambda: {"unattested_refused": 0, "unattested_proposed": 0,
                                                  "unattested_unproposable": 0})

    def tick(self):
        self.clock += 1
        return self.clock


@dataclass
class Rules:
    unknown_with_challenge: str = "assertable_with_unit"   # §10.2: alt "not_assertable"
    unknown_renders_marker_if_flagged: bool = True          # draft 2: the axis and the flag are orthogonal (G3)
    absorption_or_post_version: bool = False                # draft 2 (G2, option (a)): post-version survivor keeps the INCOMING's flag
    legacy_flag_precedence: str = "flag_first"              # draft 2 (G1): the STORED FLAG decides first; draft 1: "unknown"


# ----------------------------------------------------------------------------------------------- §2 grounding
def grounding(s: Store, e: Edge, rules: Rules, at: int | None = None) -> str:
    confirmed = any(c.edge == e.id and (at is None or c.t <= at) for c in s.confirmations)
    if rules.legacy_flag_precedence == "flag_first":
        if e.ungrounded:
            return "confirmed" if confirmed else "inferred"            # whatever the version (G1)
        return "unknown" if e.version < GROUNDING_VERSION else "attested"
    # draft 1's precedence, kept executable as the mutant/alternative
    if e.version < GROUNDING_VERSION:
        if e.ungrounded and confirmed and rules.legacy_flag_precedence == "confirmed":
            return "confirmed"
        return "unknown"
    if not e.ungrounded:
        return "attested"
    return "confirmed" if confirmed else "inferred"


# ----------------------------------------------------------------------------------------------- §4 challenges
def active_challenges(s: Store, e: Edge, at: int | None = None) -> list:
    rs = [r for r in s.replies if r.edge == e.id and (at is None or r.t <= at)]
    resolved = {r.target for r in rs if r.kind == "resolve"}
    return sorted((r for r in rs if r.kind == "challenge" and r.id not in resolved), key=lambda r: (r.t, r.id))


class Refused(Exception):
    pass


def add_reply(s: Store, e: Edge, kind: str, text: str, target: str | None = None) -> Reply:
    if kind not in ("challenge", "context", "withdrawn-consent", "resolve"):
        raise Refused("kind outside the closed set")
    if MARKER in text:
        raise Refused("a marker in an ordinary reply")
    if MARKER in (e.relation, e.obj):
        raise Refused("reply to a redacted edge")                     # R1 (owner/reviewer): refuse
    if kind == "resolve":
        c = next((r for r in s.replies if r.id == target), None)
        if c is None or c.edge != e.id or c.kind != "challenge":
            raise Refused("resolve must name a challenge of the same edge")
        if any(r.kind == "resolve" and r.target == target for r in s.replies):
            raise Refused("challenge already resolved")
    r = Reply(id=f"r{len(s.replies) + 1}", edge=e.id, kind=kind, text=text, t=s.tick(), target=target)
    s.replies.append(r)
    return r


# ----------------------------------------------------------------------------------------------- §5 the gate
def gate(s: Store, e: Edge, rules: Rules, existing_ok: bool = True, at: int | None = None) -> str:
    """'assertable' | 'assertable_with_unit' | 'inference_with_marker' | 'not_assertable' (additional restriction)."""
    if not existing_ok:
        return "not_assertable"                                       # never promotes an ineligible edge
    g = grounding(s, e, rules, at)
    ch = bool(active_challenges(s, e, at))
    if g == "attested":
        return "assertable_with_unit" if ch else "assertable"
    if g in ("confirmed", "inferred"):
        return "not_assertable" if ch else "inference_with_marker"
    # unknown
    if ch:
        return "assertable_with_unit" if rules.unknown_with_challenge == "assertable_with_unit" else "not_assertable"
    return "assertable"


def render(s: Store, e: Edge, rules: Rules, budget: int, at: int | None = None) -> str | None:
    """§6: the mandatory unit, or withheld. The count is computed BEFORE budget selection."""
    gt = gate(s, e, rules, at=at)
    if gt == "not_assertable":
        return None
    g = grounding(s, e, rules, at)
    marker = ""
    if g in ("inferred", "confirmed") or (e.ungrounded and (g != "unknown" or rules.unknown_renders_marker_if_flagged)):
        marker = " [possible extraction error]"
    line = f"{e.relation}: {e.obj}{marker}"
    ch = active_challenges(s, e, at)
    if ch:
        line += f" [challenged by the subject: {len(ch)} open; latest: {ch[-1].text[:20]}]"
    return line if len(line) <= budget else None                     # never rendered without its unit


# ----------------------------------------------------------------------------------------------- §3 proposals
def canonical(p: dict) -> bytes:
    fields = ("user", "relation", "obj", "episode", "source", "minted_at")
    return b"veracium.proposal.v1\0" + "\0".join(str(p[k]) for k in fields).encode()


def mint(s: Store, user: str, relation: str, obj: str, episode: str | None, source: str, author: str = "user"):
    """§3: only from a USER-effective event WITH an episode carrier; otherwise refused and counted."""
    if author != "user":
        s.counts["unattested_refused"] += 1
        return None
    if not episode:
        s.counts["unattested_unproposable"] += 1
        return None
    p = {"user": user, "relation": relation, "obj": obj, "episode": episode, "source": source, "minted_at": s.tick()}
    p["token"] = hmac.new(s.key, canonical(p), hashlib.sha256).hexdigest()
    s.counts["unattested_proposed"] += 1
    return p


def confirm_inference(s: Store, p: dict, *, actor: str, call_path: str, correlation_id: str):
    """§3/§3a: replay first; then the lifetime checks INSIDE the write transaction; then the fresh edge + row."""
    digest = hashlib.sha256(b"confirm_inference|" + canonical(p) + f"|{actor}|{call_path}".encode()).hexdigest()
    rec = s.corr.get((p["user"], correlation_id))
    if rec is not None:
        if rec[0] == digest:
            return rec[1]
        raise Refused("integrity conflict: same id, different request")
    tx = copy.deepcopy(s)                                            # BEGIN IMMEDIATE
    if not hmac.compare_digest(p.get("token", ""), hmac.new(tx.key, canonical(p), hashlib.sha256).hexdigest()):
        raise Refused("token")
    if p["episode"] in tx.redacted_episodes:
        raise Refused("source redacted")
    if p["source"] in tx.revoked_sources:
        raise Refused("source revoked")
    if p["user"] in tx.forgotten_users:
        raise Refused("forgotten")
    eid = f"c-{p['episode']}-{p['obj']}"
    e = Edge(id=eid, user=p["user"], relation=p["relation"], obj=p["obj"], ungrounded=True, version=GROUNDING_VERSION)
    tx.edges[eid] = e
    tx.confirmations.append(Confirmation(id=f"k{len(tx.confirmations) + 1}", edge=eid, t=tx.tick(), actor=actor,
                                         correlation_id=correlation_id, digest=digest))
    result = {"edge": eid}
    tx.corr[(p["user"], correlation_id)] = (digest, result)
    s.__dict__.update(tx.__dict__)                                    # COMMIT
    return result


def confirm(s: Store, e: Edge, *, actor="host", correlation_id="x"):
    """0008's confirm(), with the renamed refusal site: an edge with an open challenge is refused."""
    if active_challenges(s, e):
        raise Refused("store.confirm.active-challenge")
    s.confirmations.append(Confirmation(id=f"k{len(s.confirmations) + 1}", edge=e.id, t=s.tick(), actor=actor,
                                        correlation_id=correlation_id, digest="d"))


# ----------------------------------------------------------------------------------------------- §7 identity transitions
def absorb(s: Store, prior: Edge, incoming: Edge, rules: Rules) -> str:
    """§7: absorption is REFUSED when the prior carries a confirmation or reply; otherwise today's behaviour, where the
    survivor's flag is the OR of the incoming and absorbed flags (0019/0014)."""
    acts = any(c.edge == prior.id for c in s.confirmations) or any(r.edge == prior.id for r in s.replies)
    s.edges[incoming.id] = incoming
    if acts:
        return "not_absorbed"
    prior.active = False
    if (rules.absorption_or_post_version or incoming.version < GROUNDING_VERSION) and prior.ungrounded and not incoming.ungrounded:
        incoming.ungrounded, incoming.flag_by = True, "absorption_or"
    return "absorbed"


# ----------------------------------------------------------------------------------------------- §8 import
def import_rows(s: Store, edges: list, confirmations: list, replies: list, mode: str):
    """§8: preflight against destination ∪ incoming; default import refuses acts aimed at PRE-EXISTING local edges."""
    local = set(s.edges)
    incoming = {e.id for e in edges}
    for row in confirmations + replies:
        tgt = row.edge
        if tgt not in local | incoming:
            raise Refused(f"orphan act {row.id}")
        if tgt in local and mode == "default":
            raise Refused(f"an untrusted file acting on a local edge ({row.id})")
    tx = copy.deepcopy(s)
    for e in edges:
        e2 = copy.deepcopy(e)
        if mode == "default":
            e2.author, e2.disclosure, e2.origin = "third_party", "use_only", "imported"
        tx.edges[e2.id] = e2
    for row in confirmations + replies:
        r2 = copy.deepcopy(row); r2.origin = "imported" if mode == "default" else "restored"
        (tx.confirmations if isinstance(r2, Confirmation) else tx.replies).append(r2)
    s.__dict__.update(tx.__dict__)
