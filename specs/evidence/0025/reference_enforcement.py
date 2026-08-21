"""Executable reference for the 0024/0025 v3 constructions — pre-implementation.

External round 1 package feedback: *"a pre-implementation reference harness
would help"* — and all three of 0025's blocking findings (F1 disclosure
ordering, F2 the retry, F3 the registry construction) were constructions the
spec described without making runnable. This file IS those constructions,
verbatim from the v3 text, with vectors that bite: each vector states the
wrong behaviour the amended text forbids, and several run the WRONG order on
purpose to show what it produces.

Run:  $PY specs/evidence/0025/reference_enforcement.py
      (any Python >= 3.10; no dependencies, no product imports — this is the
       reference the implementation will be differentially tested against,
       the 0022 vector-harness discipline)

Covers 0024 §4a (the coherence predicate) and 0025 §4b(1) (the retry),
§4b-ii (the effective registry), §3/X10 (disclosure from the ORIGINAL
relation), X11 (snapshot immutability), X4 (count reconciliation).
"""
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

QUARANTINE_RELATION = "third_party_claim"
UNCLASSIFIED = "unclassified"
RESERVED = (UNCLASSIFIED, QUARANTINE_RELATION)


@dataclass(frozen=True)
class Relation:
    name: str
    functional: bool = False


class Author(Enum):
    USER = "user"
    SYSTEM = "system"
    THIRD_PARTY = "third_party"


class Disclosure(Enum):
    MENTIONABLE = "mentionable"
    USE_ONLY = "use_only"
    QUARANTINED = "quarantined"


class RegistryError(ValueError):
    pass


# ---- 0024 §4a: the coherence predicate, mechanical -------------------------

def canonical_subject(subject) -> str:
    """The SAME conversion the shipped write path applies (ingest.py:225)."""
    return str(subject).strip()


def incoherent(relation: str, subject) -> bool:
    """Whole-string casefold equality. No substring, no synonyms, no note."""
    return (relation == QUARANTINE_RELATION
            and canonical_subject(subject).casefold() == "user")


# ---- 0025 §4b-ii: the effective registry, five ordered steps ---------------

def effective_registry(host: dict) -> MappingProxyType:
    # 1. shape — every value a Relation, every key == its value's name
    for k, v in host.items():
        if not isinstance(v, Relation):
            raise RegistryError(f"value for {k!r} is not a Relation")
        if k != v.name:
            raise RegistryError(f"key {k!r} != Relation.name {v.name!r}")
    # 2. empty — tested AS SUPPLIED, before injection can mask it (X5)
    if not host:
        raise RegistryError("empty registry refused")
    # 3. shadowing — refused BEFORE injection, both reserved names (X9)
    for name in RESERVED:
        if name in host:
            raise RegistryError(f"reserved name shadowed: {name}")
    # 4. injection — both reserved members, non-functional (X8)
    eff = {k: Relation(v.name, v.functional) for k, v in host.items()}
    for name in RESERVED:
        eff[name] = Relation(name, False)
    # 5. snapshot — the copies above ARE the deep copy (Relation is frozen);
    #    the proxy refuses later key mutation (X11)
    return MappingProxyType(eff)


# ---- disclosure, the shipped decision (ingest.py:96) -----------------------

def disclosure_for(author: Author, relation: str, derived_from) -> Disclosure:
    if relation == QUARANTINE_RELATION:
        return Disclosure.QUARANTINED
    if author is Author.THIRD_PARTY or derived_from is Author.THIRD_PARTY:
        return Disclosure.USE_ONLY
    return Disclosure.MENTIONABLE


# ---- the whole ingest decision for one event -------------------------------

def enforce(triples, host_registry, author, derived_from, retry=None):
    """0025 §4b(1)+(2) with 0024 §4a composed in the ruled order.

    `triples` — list of dicts with subject/relation/object (post the shipped
    completeness check: falsy-free, str()-converted).
    `retry` — a callable(failing_triples) -> list of triples or None, standing
    in for the ONE provider call; None means "host without a provider".
    Returns (stored, counts) where each stored row carries the decided
    relation, disclosure, and original_relation.
    """
    reg = effective_registry(host_registry)
    calls = 0
    stored, failing = [], []

    def decide(t, relation, original):
        # X10: disclosure from the ORIGINAL relation, computed before any
        # rewrite and retained — the rewrite never feeds disclosure_for.
        disc = disclosure_for(author, original, derived_from)
        rel, orig_field = relation, None
        if incoherent(original, t["subject"]):
            # 0024 §4b: re-disposition — relation to the reserved member,
            # disclosure by the author rules ALONE, original in the typed field
            rel, orig_field = UNCLASSIFIED, original
            disc = disclosure_for(author, "", derived_from)
        elif relation != original:
            orig_field = original      # 0025 rewrite: the typed carrier (F6)
        return dict(t, relation=rel, disclosure=disc,
                    original_relation=orig_field)

    for t in triples:
        r = str(t["relation"]).strip()
        if r in reg:
            stored.append(decide(t, r, r))
        else:
            failing.append(t)

    retried = len(failing)
    recovered = 0
    if failing and retry is not None:
        calls += 1                     # exactly ONE call per event (F2)
        try:
            replacements = retry(list(failing)) or []
        except Exception:
            replacements = []          # malformed retry output is a no-op
        def key(t):
            return (canonical_subject(t["subject"]).casefold(),
                    str(t["object"]).strip().casefold())
        by_key = {}
        for rep in replacements:
            if not isinstance(rep, dict):
                continue
            rrel = str(rep.get("relation", "")).strip()
            if rrel in reg:            # the replacement must be a member
                by_key.setdefault(key(rep), rrel)
        still = []
        for t in failing:
            rrel = by_key.get(key(t))  # match on the content pair only
            if rrel is not None:
                recovered += 1
                stored.append(decide(t, rrel, str(t["relation"]).strip()))
            else:
                still.append(t)
        failing = still
    for t in failing:                  # the residual → the reserved member
        stored.append(decide(t, UNCLASSIFIED, str(t["relation"]).strip()))

    counts = dict(retried=retried, recovered=recovered,
                  residual=retried - recovered, retry_calls=calls)
    assert counts["retried"] == counts["recovered"] + counts["residual"]
    return stored, counts


# ============================ vectors ========================================

def _refuses(fn, needle):
    try:
        fn()
    except RegistryError as e:
        assert needle in str(e), (needle, str(e))
        return
    raise AssertionError(f"not refused: {needle}")


HOST = {"works_as": Relation("works_as", True),
        "works_on": Relation("works_on", False)}


def vector_construction_refuses_empty_as_supplied():
    _refuses(lambda: effective_registry({}), "empty")


def vector_construction_refuses_mismatched_key():
    _refuses(lambda: effective_registry({"jobs": Relation("works_as", True)}),
             "!= Relation.name")


def vector_construction_refuses_both_reserved_shadows():
    for name in RESERVED:
        for fn in (True, False):       # functional AND non-functional shadows
            _refuses(lambda n=name, f=fn: effective_registry(
                dict(HOST, **{n: Relation(n, f)})), "shadowed")


def vector_construction_injects_both_reserved_members():
    reg = effective_registry(HOST)
    for name in RESERVED:
        assert name in reg and reg[name].functional is False


def vector_snapshot_survives_host_mutation():
    host = dict(HOST)
    reg = effective_registry(host)
    host.clear()                       # the host mutates its dict afterwards
    assert "works_as" in reg and reg["works_as"].functional is True
    try:
        reg["injected"] = Relation("injected", True)
        raise AssertionError("snapshot accepted a write")
    except TypeError:
        pass


def vector_disclosure_is_computed_from_the_original_relation():
    """THE LAUNDERING CELL (0025 F1). Host registry omits third_party_claim;
    the extractor relays genuine hearsay. The WRONG order — rewrite first,
    disclosure from the rewritten relation — asserts it. The reference, with
    injection + X10, quarantines it."""
    t = {"subject": "the landlord", "relation": QUARANTINE_RELATION,
         "object": "user owes $500"}
    # the wrong order, run on purpose:
    laundered = disclosure_for(Author.USER, UNCLASSIFIED, None)
    assert laundered is Disclosure.MENTIONABLE      # the bite
    stored, _ = enforce([t], HOST, Author.USER, None)
    assert stored[0]["disclosure"] is Disclosure.QUARANTINED
    assert stored[0]["relation"] == QUARANTINE_RELATION  # injected resident


def vector_literal_user_subject_redispositions():
    """0024 §4b: the coherence cell — relation says hearsay, claimant is the
    user themself. Re-dispositioned, disclosure by author alone, original in
    the TYPED field."""
    t = {"subject": " User ", "relation": QUARANTINE_RELATION,
         "object": "opening act was Whiskey Wanderers"}
    stored, _ = enforce([t], HOST, Author.USER, None)
    row = stored[0]
    assert row["relation"] == UNCLASSIFIED
    assert row["disclosure"] is Disclosure.MENTIONABLE
    assert row["original_relation"] == QUARANTINE_RELATION


def vector_odd_subject_types_fail_closed():
    """0024 F2: a truthy non-string subject survives the shipped completeness
    check str()-converted; the predicate misses it and quarantine holds."""
    for subject in (["user"], {"name": "user"}, 1):
        t = {"subject": str(subject).strip(),
             "relation": QUARANTINE_RELATION, "object": "x"}
        stored, _ = enforce([t], HOST, Author.USER, None)
        assert stored[0]["disclosure"] is Disclosure.QUARANTINED, subject


def vector_author_floor_holds_through_redisposition():
    """0024 U2: a THIRD_PARTY-authored incoherent triple lands USE_ONLY,
    never MENTIONABLE — the floor is the author, not the rewrite."""
    t = {"subject": "user", "relation": QUARANTINE_RELATION, "object": "x"}
    stored, _ = enforce([t], HOST, Author.THIRD_PARTY, None)
    assert stored[0]["disclosure"] is Disclosure.USE_ONLY


def vector_retry_is_one_call_and_matches_on_the_content_pair():
    ts = [{"subject": "user", "relation": "job", "object": "carpenter"},
          {"subject": "user", "relation": "hobby", "object": "chess"}]
    def retry(failing):
        assert len(failing) == 2       # ONE call carries ALL failing triples
        return [{"subject": "User", "relation": "works_as",
                 "object": "carpenter "},          # repairs by content pair
                {"subject": "user", "relation": "invented", "object": "new"}]
    stored, counts = enforce(ts, HOST, Author.USER, None, retry=retry)
    assert counts == dict(retried=2, recovered=1, residual=1, retry_calls=1)
    by_obj = {r["object"]: r for r in stored}
    assert by_obj["carpenter"]["relation"] == "works_as"
    assert by_obj["carpenter"]["original_relation"] == "job"
    assert by_obj["chess"]["relation"] == UNCLASSIFIED   # unmatched → residual
    assert all(r["object"] != "new" for r in stored)     # discards, never adds


def vector_retry_replacement_must_be_a_member():
    ts = [{"subject": "user", "relation": "job", "object": "carpenter"}]
    stored, counts = enforce(ts, HOST, Author.USER, None,
                             retry=lambda f: [{"subject": "user",
                                               "relation": "occupation",
                                               "object": "carpenter"}])
    assert counts["recovered"] == 0
    assert stored[0]["relation"] == UNCLASSIFIED


def vector_malformed_retry_output_is_a_noop():
    ts = [{"subject": "user", "relation": "job", "object": "carpenter"}]
    for bad in (lambda f: (_ for _ in ()).throw(ValueError("bad json")),
                lambda f: "not a list at all",
                lambda f: None):
        stored, counts = enforce(ts, HOST, Author.USER, None, retry=bad)
        assert counts == dict(retried=1, recovered=0, residual=1,
                              retry_calls=1), bad
        assert stored[0]["relation"] == UNCLASSIFIED


def vector_in_vocabulary_event_is_untouched():
    """X6's shape: nothing off-vocabulary, nothing incoherent → no rewrite,
    no retry call, zeros PRESENT (an absent key is not a zero)."""
    ts = [{"subject": "user", "relation": "works_as", "object": "carpenter"}]
    calls = []
    stored, counts = enforce(ts, HOST, Author.USER, None,
                             retry=lambda f: calls.append(1))
    assert counts == dict(retried=0, recovered=0, residual=0, retry_calls=0)
    assert not calls
    assert stored[0]["relation"] == "works_as"
    assert stored[0]["original_relation"] is None


def main() -> int:
    vectors = [v for n, v in sorted(globals().items())
               if n.startswith("vector_")]
    for v in vectors:
        v()
        print(f"ok  {v.__name__}")
    print(f"{len(vectors)} vectors, all biting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
