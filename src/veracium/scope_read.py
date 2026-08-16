"""specs/0020 §4c/§4d/§4e/§4f — THE READ SURFACES' visibility relation.

Slice B. This module is the ONE place a read path asks "may this principal
see this record, and in what shape?". It CONSUMES the normative core in
`veracium.scope` (Slice A) and re-implements none of it: `membership`,
`close_absorption_rows`, `classify`, `DECISION_TABLE`, `validate_filters`
and `apply_filters` are called, never mirrored.

The three properties this module exists to hold:

- **The boundary is enforced on the STRUCTURED CARRIERS** (0020 §2, external
  F3), not on rendered bytes: `ScopeView.scoped()` filters the record
  OBJECTS, and every carrier — `Recall.edges`, `Recall.episodes`,
  `Recall.contested`, `ContestedGroup.exposed` — is built from its output.
- **Membership evidence comes from the LEDGER** (§4a-iii): the record's own
  `contributions()` rows, and for an absorption survivor the TRANSITIVELY
  CLOSED set via `scope.close_absorption_rows` over a lazily-materialised
  projection of the ledger. **A None closure IS UNRESOLVED** — fail-closed
  before `membership` ever runs.
- **Assertability is RESTRICT-ONLY** (§4b): a CROSS_VISIBLE record is
  visible but never assertable — it is re-shaped to the FENCED disclosure
  (`USE_ONLY`) so it routes through the shipped never-assert channel. The
  shaping NEVER widens: a record that is already QUARANTINED keeps its
  quarantine, and no classification ever clears `ungrounded`,
  `needs_confirmation`, or raises trust. `gate.scoped_assertable` is the
  predicate; the 0011 subject seam lives there.

`principal=None` short-circuits at construction: `view_for()` returns None
and NOTHING in this module runs — no ledger read, no extra store call, no
re-shaped record. That is the mechanical form of V1 (unscoped reads are
byte-identical to today over a fixed store state).
"""

from __future__ import annotations

import re
from typing import Optional

from . import gate as _gate
from .schema import Disclosure, Edge, Episode, EvidenceAuthor
from .scope import (DECISION_TABLE, UNRESOLVED, Identity, ScopeError,
                    apply_filters, classify, close_absorption_rows,
                    digest_of, membership)
from .scope_linkage import MEMBERSHIP_SITES

#: the LEGACY (pre-amendment) absorption link, as the shipped writer emits
#: it on the ABSORBED record: `graph.py`'s
#: `absorbed_by:{incoming.id} (restated as …)` note. §4a-iii's note-derived
#: fallback; the LAST tag governs (the earlier ones are incidental).
_ABSORBED_BY = re.compile(r"absorbed_by:(\S+)")

#: the §4e closed field set carries NO episode field, so a filter narrows
#: the EDGE set only (M-1: filters SELECT, never STRIP).
_EDGE_FILTER_FIELDS = ("subject", "relation", "author_of_evidence",
                       "source_id", "volatility")


def _asserted_today(record) -> bool:
    """TODAY's assertability verdict for one record — the input §4b's
    restrict-only relation narrows. The two record kinds are routed by the
    gate on two different fields, and this is where that asymmetry is stated
    ONCE: an `Edge` carries `assertable`; an `Episode` is grounded unless it
    is third-party-INFLUENCED (`partition_parts`' rule, not authorship)."""
    if isinstance(record, Episode):
        return not record.provenance.third_party_influenced
    return bool(record.assertable)


def _row_dict(r) -> dict:
    """A `ContributionRecord` projected to the plain mapping shape the 0020
    core consumes (`{site, identity_digest, op_key, contributor_ref,
    evidence_ref_digest, payload}`)."""
    return {"site": r.site, "identity_digest": r.identity_digest,
            "op_key": r.op_key, "contributor_ref": r.contributor_ref,
            "contributor_type": r.contributor_type,
            "evidence_ref_digest": r.evidence_ref_digest,
            "payload": r.payload}


class ScopeView:
    """One recall's principal boundary. Constructed per call (never cached
    across calls — the store moves under us); memoises only within the call.

    Every public read path routes its record sets through `scoped()` (the
    visibility relation + the restrict-only shaping) and, for edges, then
    `narrow()` (the §4e filters — AFTER scope, within the visible set,
    M-2)."""

    def __init__(self, store, user_id: str, principal: Identity,
                 policy, *, filters: Optional[dict] = None):
        if not isinstance(principal, Identity):
            raise ScopeError(
                f"principal must be a veracium.scope.Identity, got "
                f"{type(principal).__name__} (strict types, 0020 §2c)")
        # feature-disabled REFUSES a principal-bearing call (§4a-ii, R2-2) —
        # raised HERE as well as inside `classify`, so the refusal happens
        # before a single record is read rather than per-record.
        if policy is None:
            raise ScopeError(
                "a principal was supplied but no scope policy is configured — "
                "feature-disabled cannot honour a principal-bearing call "
                "(0020 §4a-ii); configure MemoryConfig.scope_groups (`{}` is "
                "the valid configured-empty state)")
        if not principal.groupable:
            raise ScopeError("a principal must carry a source_id (0006 I13)")
        self.store = store
        self.user_id = user_id
        self.principal = principal
        self.policy = policy
        self.filters = dict(filters or {})
        self.local_origin = store.local_origin()
        self._rows_cache: dict = {}
        self._evidence: dict = {}
        self._decisions: dict = {}
        self._legacy_cache = None

    # -- the ledger projection (§4a-iii) -----------------------------------
    def _rows(self, kind: str, rid: str) -> list:
        key = (kind, rid)
        if key not in self._rows_cache:
            try:
                rows = self.store.contributions(self.user_id, kind, rid)
            except NotImplementedError:
                # a Store with no ledger has no derivatives either: an
                # ordinary record resolves by its own identity, which is
                # exactly what an empty row set gives.
                rows = []
            self._rows_cache[key] = [_row_dict(r) for r in rows]
        return self._rows_cache[key]

    def _projection(self, kind: str, rid: str) -> dict:
        """`{record_id: [rows]}`, materialised TRANSITIVELY by following the
        typed `contributor_ref` — the input `close_absorption_rows` walks.
        Absence of a contributor's rows is legitimate under accepted 0014 A10
        (rows drop with their survivor) and the closure says so itself."""
        proj: dict = {}
        stack = [(kind, rid)]
        seen = set()
        while stack:
            k, i = stack.pop()
            if (k, i) in seen:
                continue
            seen.add((k, i))
            rows = self._rows(k, i)
            proj[i] = rows
            for r in rows:
                ref = r.get("contributor_ref")
                if ref is not None:
                    stack.append((r.get("contributor_type") or k, ref))
        return proj

    def _legacy(self):
        """The note-derived LEGACY fallback (`legacy_links`,
        `legacy_digests`), built once per view and only when a ref-less
        absorption row actually needs it. `absorbed_by:` sits on the ABSORBED
        record and names its absorber, so the map is inverted here; the LAST
        tag governs (§4a-iii)."""
        if self._legacy_cache is None:
            links: dict = {}
            digs: dict = {}
            for e in self.store.edges(self.user_id, active_only=False,
                                      include_quarantined=True):
                digs[e.id] = digest_of(
                    Identity(e.provenance.origin, e.provenance.source_id),
                    self.local_origin)
                tags = _ABSORBED_BY.findall(e.note or "")
                if tags:
                    links.setdefault(tags[-1], []).append(e.id)
            self._legacy_cache = ({k: tuple(v) for k, v in links.items()},
                                  digs)
        return self._legacy_cache

    # -- the membership → classification chain ------------------------------
    @staticmethod
    def _kind(record) -> str:
        return "episode" if isinstance(record, Episode) else "edge"

    def _record_shape(self, record) -> dict:
        p = record.provenance
        return {"author": p.author_of_evidence.value,
                "origin": p.origin,
                "source_id": p.source_id,
                "evidence_ref": p.evidence_ref,
                "lineage": bool(getattr(record, "lineage", None))}

    def evidence(self, record):
        """The §4a-iii membership evidence for one record: a digest, SHARED,
        or UNRESOLVED. Absorption survivors resolve over the TRANSITIVELY
        CLOSED row set; a None closure is UNRESOLVED before `membership`
        runs. Memoised per record within the call — the same record reaches
        several carriers (the subgraph, the contested surface) and must never
        get two answers."""
        key = (self._kind(record), record.id)
        if key not in self._evidence:
            self._evidence[key] = self._evidence_of(record)
        return self._evidence[key]

    def _evidence_of(self, record):
        kind = self._kind(record)
        shape = self._record_shape(record)
        rows = self._rows(kind, record.id)
        lineage = getattr(record, "lineage", None)
        expected = len(lineage) if shape["lineage"] else None
        if not shape["lineage"] and any(r["site"] in MEMBERSHIP_SITES
                                        for r in rows):
            links, digs = self._legacy()
            closed = close_absorption_rows(record.id,
                                           self._projection(kind, record.id),
                                           links, digs)
            if closed is None:
                return UNRESOLVED            # None IS UNRESOLVED (§4a-iii)
            rows = closed
        # 0010 state: a record that has REACHED a read surface is a durable
        # output — in-flight ("generating") outputs are not readable, and
        # "abandoned" has no output at all. The legacy-derivative predicate
        # inside `membership` is what catches a pre-0021 output regardless.
        return membership(shape, rows, "none", self.local_origin,
                          expected_contributors=expected)

    def decision(self, record):
        """`(visible, shape)` from the FIXED decision table, memoised per
        record within this call."""
        key = (self._kind(record), record.id)
        if key not in self._decisions:
            cls = classify(self.evidence(record), self.principal,
                           self.policy, self.local_origin)
            self._decisions[key] = DECISION_TABLE[cls]
        return self._decisions[key]

    def visible(self, record) -> bool:
        return self.decision(record)[0]

    # -- the restrict-only shaping (§4b) ------------------------------------
    def assertable(self, record) -> bool:
        """§4b: is this record assertable TO THIS PRINCIPAL? The authority is
        `gate.scoped_assertable` — the spec's relation, in the gate, where
        assertability has always lived. This method only supplies the two
        inputs: today's verdict and the decision cell."""
        return _gate.scoped_assertable(_asserted_today(record),
                                       self.decision(record))

    def shape(self, record):
        """Apply the RESTRICT-ONLY consequence of the decision to a VISIBLE
        record.

        `gate.scoped_assertable` DECIDES; this function only carries the
        decision onto the record, and only in the subtracting direction: it
        acts exactly when the gate's scoped verdict is False for a record
        that would otherwise have been assertable. CROSS_VISIBLE material is
        the cell that reaches it — visible, but pinned to the fenced
        third-party-testimony shape so it renders under the never-assert
        fence and never volunteers itself proactively.

        TWO levers, because the gate routes the two record kinds on two
        different fields and shaping only ONE of them would leave the other
        kind in the grounded block (an EDGE routes on
        `quarantined`/`use_only`, an EPISODE on
        `provenance.third_party_influenced`):

        - `disclosure` → `USE_ONLY`, and ONLY from the widest tier
          (`MENTIONABLE`); a `QUARANTINED` or `USE_ONLY` record keeps what it
          has, because moving it would be a grant;
        - `derived_from` → `THIRD_PARTY`, and only when it is unset — the
          SHIPPED trust-cap idiom (0005's import boundary sets exactly this
          pair), which caps trust at the minimum and can never raise it.

        This function can only ever NARROW. Nothing here clears `ungrounded`
        or `needs_confirmation` or raises trust —
        `test_same_scope_grants_nothing` enumerates the temptations."""
        if not self.visible(record):
            return record                     # never reaches a carrier anyway
        today = _asserted_today(record)
        if not today or self.assertable(record):
            return record                     # scope subtracted nothing
        p = record.provenance
        update = {}
        if p.disclosure == Disclosure.MENTIONABLE:
            update["disclosure"] = Disclosure.USE_ONLY
        if p.derived_from is None:
            update["derived_from"] = EvidenceAuthor.THIRD_PARTY
        if not update:
            return record                     # already narrower — never widen
        return record.model_copy(
            update={"provenance": p.model_copy(update=update)})

    # -- the two lenses every read surface uses -----------------------------
    def scoped(self, records: list) -> list:
        """THE VISIBILITY RELATION on a record set: drop every record the
        relation makes invisible (CROSS_HIDDEN and UNRESOLVED), shape what
        remains."""
        return [self.shape(r) for r in records if self.visible(r)]

    def narrow(self, edges: list) -> list:
        """§4e M-2: the filters, AFTER scope and WITHIN the visible set —
        narrow only, so a filter can never be an oracle for out-of-scope
        material."""
        return narrow_edges(edges, self.filters)

    def lens(self, records: list) -> list:
        """The one hook a read path passes down (proactive assembly): scope,
        then narrow the edges. Episodes carry no §4e filter field, so the
        closed grammar leaves them at scope."""
        out = self.scoped(records)
        if out and isinstance(out[0], Edge):
            out = self.narrow(out)
        return out


def narrow_edges(edges: list, filters: dict) -> list:
    """The §4e grammar applied to `Edge` objects: project each edge onto the
    CLOSED field set (M-4 — `source_id` reads the RESOLVED identity's
    source_id, which resolution never rewrites; a cleared derivative's field
    is None and never matches), then `scope.apply_filters`."""
    if not filters:
        return list(edges)
    projected = [({"subject": e.subject,
                   "relation": e.relation,
                   "author_of_evidence": e.provenance.author_of_evidence.value,
                   "source_id": e.provenance.source_id,
                   "volatility": e.volatility.value}, e) for e in edges]
    keep = apply_filters([p for p, _ in projected], filters)
    keep_ids = {id(p) for p in keep}
    return [e for p, e in projected if id(p) in keep_ids]


def view_for(store, user_id: str, principal, policy,
             *, filters: Optional[dict] = None) -> Optional[ScopeView]:
    """The ONE constructor every read surface calls. `principal=None` →
    None, and no scope code runs at all (V1)."""
    if principal is None:
        return None
    return ScopeView(store, user_id, principal, policy, filters=filters)


def assertable_under(view: Optional[ScopeView], record) -> bool:
    """The gate's scoped predicate for one record, for callers holding a
    view that may be None. Unscoped: today's answer, verbatim."""
    if view is None:
        return _asserted_today(record)
    return view.assertable(record)
