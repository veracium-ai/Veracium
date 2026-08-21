"""Executable reference for the 0024/0025 v4 constructions — pre-implementation.

Round 1 asked for the harness; round 2 found the v3 constructions
contradicting each other and the shipped tree, so the v4 harness carries the
corrections AND the vectors round 2 named: the shipped default registry,
duplicate-pair retry candidates, a retry answering with a reserved member,
mutation THROUGH the snapshot, unaffected-edge byte identity under the
None-omission rule, and the combined 0024-coherence/0025-vocabulary ordering.

Run:  $PY specs/evidence/0025/reference_enforcement.py
      (dependency-free; the shipped-DEFAULT_RELATIONS vector imports the
       product if available and reports a NAMED skip otherwise)

Normative sources: 0025 §4b(1) retry, §4b-ii registry, §4b-iii combined
pipeline, X6/X10/X11; 0024 §4a predicate, §4b re-disposition.
"""
import json
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

QUARANTINE_RELATION = "third_party_claim"
UNCLASSIFIED = "unclassified"
RESERVED = (UNCLASSIFIED, QUARANTINE_RELATION)


@dataclass(frozen=True)
class Relation:                 # stands in for the mutable pydantic model
    name: str
    functional: bool = False


@dataclass(frozen=True)
class FrozenRel:                # §4b-ii step 5: the snapshot's OWN records
    name: str
    functional: bool


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


# ---- THE normalization (0025 §4b(1) — one rule, stated once) ---------------

def norm(x) -> str:
    return str(x).strip().casefold()


# ---- 0024 §4a: the coherence predicate -------------------------------------

def canonical_subject(subject) -> str:
    return str(subject).strip()          # the shipped write-path conversion


def incoherent(relation: str, subject) -> bool:
    return (relation == QUARANTINE_RELATION
            and canonical_subject(subject).casefold() == "user")


# ---- 0025 §4b-ii: the effective registry, five ordered steps ---------------

def effective_registry(host: dict) -> MappingProxyType:
    # 1. shape
    for k, v in host.items():
        if not hasattr(v, "name") or not hasattr(v, "functional"):
            raise RegistryError(f"value for {k!r} is not a Relation")
        if k != v.name:
            raise RegistryError(f"key {k!r} != Relation.name {v.name!r}")
    # 2. empty — AS SUPPLIED, before injection (X5)
    if not host:
        raise RegistryError("empty registry refused")
    # 3. shadowing — CONFLICTING shadows only (round 2, R2-1: the shipped
    #    DEFAULT_RELATIONS carries third_party_claim and must pass)
    for name in RESERVED:
        if name in host and bool(host[name].functional):
            raise RegistryError(f"reserved name conflictingly shadowed: {name}")
    # 4. injection — any reserved member not already (canonically) present
    eff = {k: FrozenRel(v.name, bool(v.functional)) for k, v in host.items()}
    for name in RESERVED:
        eff.setdefault(name, FrozenRel(name, False))
    # 5. snapshot — frozen records, read-only mapping (X11)
    return MappingProxyType(eff)


# ---- disclosure, the shipped decision (ingest.py:96) -----------------------

def disclosure_for(author: Author, relation: str, derived_from) -> Disclosure:
    if relation == QUARANTINE_RELATION:
        return Disclosure.QUARANTINED
    if author is Author.THIRD_PARTY or derived_from is Author.THIRD_PARTY:
        return Disclosure.USE_ONLY
    return Disclosure.MENTIONABLE


# ---- serialization: the None-omission rule (round 2, R2-3 / X6) ------------

def serialize_edge(row: dict) -> bytes:
    """`original_relation` is OMITTED when None — an unaffected edge is
    byte-identical to its pre-0025 shape."""
    out = {k: v for k, v in row.items()
           if not (k == "original_relation" and v is None)}
    out = {k: (v.value if isinstance(v, Enum) else v)
           for k, v in sorted(out.items())}
    return json.dumps(out, sort_keys=True).encode()


# ---- 0025 §4b-iii: the combined pipeline, in order -------------------------

def enforce(triples, host_registry, author, derived_from, retry=None):
    """Returns (stored, counts). Disclosure is ESTABLISHED at step 2 and the
    vocabulary fallback (step 3) never changes it — X10's whole scope."""
    reg = effective_registry(host_registry)
    stored, failing = [], []

    for t in triples:
        original = str(t["relation"]).strip()
        # step 1 — coherence (0024): deliberately changes the semantic state
        if incoherent(original, t["subject"]):
            relation, orig_field = UNCLASSIFIED, original
            established = disclosure_for(author, "", derived_from)
        else:
            relation, orig_field = original, None
            established = disclosure_for(author, original, derived_from)
        # step 2 — disclosure established for the post-coherence state
        row = dict(t, relation=relation, disclosure=established,
                   original_relation=orig_field)
        # step 3 — vocabulary membership; failures queue for the retry
        if relation in reg:
            stored.append(row)
        else:
            failing.append(row)

    counts = dict(invalid=len(failing), retried=0, recovered=0,
                  residual=0, retry_calls=0)

    if failing and retry is not None:
        counts["retried"] = len(failing)     # an ACTUAL retry ran (R2-2)
        counts["retry_calls"] = 1            # exactly ONE call per event
        try:
            replacements = retry([dict(f) for f in failing])
            if not isinstance(replacements, list):
                replacements = []
        except Exception:
            replacements = []                # degrade, recorded, never raised
        # one-to-one multiset consumption in occurrence order (R2-2):
        # a pool entry repairs at most one failing occurrence, and
        # `recovered` requires the FINAL stored relation to be an ORDINARY
        # member — a reserved answer is not a repair.
        pool = []
        for rep in replacements:
            if isinstance(rep, dict):
                rrel = str(rep.get("relation", "")).strip()
                if rrel in reg and rrel not in RESERVED:
                    pool.append(((norm(rep.get("subject", "")),
                                  norm(rep.get("object", ""))), rrel))
        for f in failing:
            key = (norm(f["subject"]), norm(f["object"]))
            for i, (pkey, prel) in enumerate(pool):
                if pkey == key:
                    pool.pop(i)
                    f["original_relation"] = f["relation"]
                    f["relation"] = prel
                    break

    for f in failing:                        # fallback for what remains
        if f["relation"] in reg and f["relation"] not in RESERVED:
            counts["recovered"] += 1
        else:
            counts["residual"] += 1
            f["original_relation"] = f["relation"]
            f["relation"] = UNCLASSIFIED
        stored.append(f)

    assert counts["invalid"] == counts["recovered"] + counts["residual"]
    return stored, counts


# ============================ vectors ========================================

HOST = {"works_as": Relation("works_as", True),
        "works_on": Relation("works_on", False)}
SKIPPED = []


def _refuses(fn, needle):
    try:
        fn()
    except RegistryError as e:
        assert needle in str(e), (needle, str(e))
        return
    raise AssertionError(f"not refused: {needle}")


def vector_construction_refuses_empty_as_supplied():
    _refuses(lambda: effective_registry({}), "empty")


def vector_construction_refuses_mismatched_key():
    _refuses(lambda: effective_registry({"jobs": Relation("works_as", True)}),
             "!= Relation.name")


def vector_only_conflicting_reserved_shadows_are_refused():
    """Round 2, R2-1: a FUNCTIONAL reserved entry is refused; an exactly
    canonical one is accepted (the shipped default registry's case)."""
    for name in RESERVED:
        _refuses(lambda n=name: effective_registry(
            dict(HOST, **{n: Relation(n, True)})), "conflictingly")
        reg = effective_registry(dict(HOST, **{name: Relation(name, False)}))
        assert reg[name].functional is False


def vector_the_shipped_default_registry_is_accepted():
    """Round 2, R2-1: v3's rule REFUSED DEFAULT_RELATIONS. Imports the
    product when available; skips NAMED otherwise."""
    try:
        from veracium.schema import DEFAULT_RELATIONS
    except ImportError:
        SKIPPED.append("shipped_default_registry (veracium not importable)")
        return
    host = {k: Relation(v.name, bool(v.functional))
            for k, v in DEFAULT_RELATIONS.items()}
    reg = effective_registry(host)
    assert QUARANTINE_RELATION in reg and UNCLASSIFIED in reg
    assert len(reg) >= len(host)


def vector_construction_injects_both_reserved_members():
    reg = effective_registry(HOST)
    for name in RESERVED:
        assert name in reg and reg[name].functional is False


def vector_snapshot_resists_mutation_through_itself():
    """Round 2, R2-1: X11's test mutates THROUGH the snapshot, not only the
    caller's registry."""
    host = dict(HOST)
    reg = effective_registry(host)
    host.clear()
    assert reg["works_as"].functional is True
    try:
        reg["injected"] = FrozenRel("injected", True)
        raise AssertionError("snapshot accepted a key write")
    except TypeError:
        pass
    try:
        reg["works_as"].functional = False  # type: ignore[misc]
        raise AssertionError("snapshot member accepted a field write")
    except AttributeError:
        pass  # FrozenRel refuses — the through-mutation cell (X11)


def vector_combined_pipeline_ordering():
    """Round 2, R2-1 (0024): the cross-spec vector. An incoherent triple's
    coherence rewrite yields MENTIONABLE and that is CORRECT (the semantic
    state changed at step 1); an off-vocabulary triple's fallback keeps its
    established disclosure (X10's scope)."""
    coherent_case = {"subject": " User ", "relation": QUARANTINE_RELATION,
                     "object": "opening act"}
    stored, _ = enforce([coherent_case], HOST, Author.USER, None)
    assert stored[0]["relation"] == UNCLASSIFIED
    assert stored[0]["disclosure"] is Disclosure.MENTIONABLE   # correct!
    assert stored[0]["original_relation"] == QUARANTINE_RELATION
    offvocab = {"subject": "the landlord", "relation": "ThirdPartyClaim",
                "object": "user owes $500"}
    stored, _ = enforce([offvocab], HOST, Author.THIRD_PARTY, None)
    assert stored[0]["relation"] == UNCLASSIFIED
    assert stored[0]["disclosure"] is Disclosure.USE_ONLY      # established
    assert stored[0]["original_relation"] == "ThirdPartyClaim"


def vector_genuine_hearsay_stays_quarantined():
    """The laundering cell: third_party_claim is registry-resident (injected
    or canonical), so genuine hearsay never reaches the fallback."""
    t = {"subject": "the landlord", "relation": QUARANTINE_RELATION,
         "object": "user owes $500"}
    stored, counts = enforce([t], HOST, Author.USER, None)
    assert stored[0]["disclosure"] is Disclosure.QUARANTINED
    assert counts["invalid"] == 0


def vector_odd_subject_types_fail_closed():
    for subject in (["user"], {"name": "user"}, 1):
        t = {"subject": str(subject).strip(),
             "relation": QUARANTINE_RELATION, "object": "x"}
        stored, _ = enforce([t], HOST, Author.USER, None)
        assert stored[0]["disclosure"] is Disclosure.QUARANTINED, subject


def vector_author_floor_holds_through_redisposition():
    t = {"subject": "user", "relation": QUARANTINE_RELATION, "object": "x"}
    stored, _ = enforce([t], HOST, Author.THIRD_PARTY, None)
    assert stored[0]["disclosure"] is Disclosure.USE_ONLY


def vector_retry_is_one_call_and_repairs_by_content_pair():
    ts = [{"subject": "user", "relation": "job", "object": "carpenter"},
          {"subject": "user", "relation": "hobby", "object": "chess"}]
    def retry(failing):
        assert len(failing) == 2
        return [{"subject": "User", "relation": "works_as",
                 "object": "carpenter "},
                {"subject": "user", "relation": "invented", "object": "new"}]
    stored, counts = enforce(ts, HOST, Author.USER, None, retry=retry)
    assert counts == dict(invalid=2, retried=2, recovered=1, residual=1,
                          retry_calls=1)
    by_obj = {r["object"]: r for r in stored}
    assert by_obj["carpenter"]["relation"] == "works_as"
    assert by_obj["carpenter"]["original_relation"] == "job"
    assert by_obj["chess"]["relation"] == UNCLASSIFIED
    assert all(r["object"] != "new" for r in stored)


def vector_duplicate_pairs_consume_one_to_one():
    """Round 2, R2-2: two failing occurrences of one normalized pair; ONE
    replacement repairs exactly one of them."""
    ts = [{"subject": "user", "relation": "job", "object": "carpenter"},
          {"subject": "User", "relation": "occupation", "object": "Carpenter"}]
    stored, counts = enforce(ts, HOST, Author.USER, None,
                             retry=lambda f: [{"subject": "user",
                                               "relation": "works_as",
                                               "object": "carpenter"}])
    assert counts == dict(invalid=2, retried=2, recovered=1, residual=1,
                          retry_calls=1)
    rels = sorted(r["relation"] for r in stored)
    assert rels == sorted(["works_as", UNCLASSIFIED])


def vector_reserved_retry_answer_is_residual_not_recovered():
    """Round 2, R2-2: a retry answering `unclassified` is NOT a recovery."""
    ts = [{"subject": "user", "relation": "job", "object": "carpenter"}]
    stored, counts = enforce(ts, HOST, Author.USER, None,
                             retry=lambda f: [{"subject": "user",
                                               "relation": UNCLASSIFIED,
                                               "object": "carpenter"}])
    assert counts == dict(invalid=1, retried=1, recovered=0, residual=1,
                          retry_calls=1)
    assert stored[0]["relation"] == UNCLASSIFIED
    assert stored[0]["original_relation"] == "job"


def vector_no_provider_means_retried_zero():
    """Round 2, R2-2: `retried` may not count retries that never ran."""
    ts = [{"subject": "user", "relation": "job", "object": "carpenter"}]
    stored, counts = enforce(ts, HOST, Author.USER, None, retry=None)
    assert counts == dict(invalid=1, retried=0, recovered=0, residual=1,
                          retry_calls=0)
    assert stored[0]["relation"] == UNCLASSIFIED


def vector_provider_failures_degrade_recorded_never_raised():
    ts = [{"subject": "user", "relation": "job", "object": "carpenter"}]
    for bad in (lambda f: (_ for _ in ()).throw(ValueError("bad json")),
                lambda f: "not a list at all",
                lambda f: None):
        stored, counts = enforce(ts, HOST, Author.USER, None, retry=bad)
        assert counts == dict(invalid=1, retried=1, recovered=0, residual=1,
                              retry_calls=1), bad
        assert stored[0]["relation"] == UNCLASSIFIED


def vector_unaffected_edge_is_byte_identical():
    """Round 2, R2-3 / X6: the None-omission rule makes an unaffected edge
    byte-identical to its pre-0025 shape."""
    old_shape = {"subject": "user", "relation": "works_as",
                 "object": "carpenter", "disclosure": Disclosure.MENTIONABLE}
    stored, counts = enforce([dict(subject="user", relation="works_as",
                                   object="carpenter")],
                             HOST, Author.USER, None)
    assert counts == dict(invalid=0, retried=0, recovered=0, residual=0,
                          retry_calls=0)
    assert stored[0]["original_relation"] is None
    assert serialize_edge(stored[0]) == serialize_edge(old_shape)
    # and an AFFECTED edge serializes the field
    affected = dict(stored[0], original_relation="job")
    assert b"original_relation" in serialize_edge(affected)


def vector_in_vocabulary_event_is_untouched():
    ts = [{"subject": "user", "relation": "works_as", "object": "carpenter"}]
    calls = []
    stored, counts = enforce(ts, HOST, Author.USER, None,
                             retry=lambda f: calls.append(1))
    assert counts == dict(invalid=0, retried=0, recovered=0, residual=0,
                          retry_calls=0)
    assert not calls
    assert stored[0]["relation"] == "works_as"
    assert stored[0]["original_relation"] is None


def main() -> int:
    vectors = [v for n, v in sorted(globals().items())
               if n.startswith("vector_")]
    for v in vectors:
        v()
        print(f"ok  {v.__name__}")
    for s in SKIPPED:
        print(f"SKIPPED  {s}")
    print(f"{len(vectors)} vectors run, {len(SKIPPED)} named skip(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
