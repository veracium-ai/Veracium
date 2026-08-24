"""Executable reference for the 0024/0025 constructions — pre-implementation.

(No spec-version number here — round 6, R6-3: a version in a docstring is
a second copy that drifts; the specs' own version rows are canonical.)

Round 1 asked for the harness; round 2 found the v3 constructions
contradicting each other and the shipped tree, so the v4 harness carries the
corrections AND the vectors round 2 named: the shipped default registry,
duplicate-pair retry candidates, a retry answering with a reserved member,
mutation THROUGH the snapshot, unaffected-edge byte identity under the
None-omission rule, and the combined 0024-coherence/0025-vocabulary ordering.

Run:  $PY specs/evidence/0025/reference_enforcement.py
      (dependency-free; the shipped-DEFAULT_RELATIONS vector imports the
       product if available and reports a NAMED skip otherwise)

Round 3 added the ACCEPTED-STACK composition the pair had only modeled in
isolation: the 0023 N1 standing-revocation floor, desc-bearing frozen
snapshots feeding prompt rendering, the extractor-selectable set, and the
0014 cross-era receipt comparison.

Normative sources: 0025 §4b(1) retry, §4b-ii registry, §4b-iii combined
pipeline, §4b-iv selectable set, X6/X10/X11; 0024 §4a predicate, §4b
re-disposition; 0023 N1; 0014 receipts (cross-era rule, pending its
co-owner amendment).
"""
import json
import pathlib as _pathlib
import sys as _sys
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

# The optional product imports (the shipped gloss, the shipped-registry
# vector) must find THIS TREE's source in an extraction too, where the
# offline venv does not pip-install the package (round 4: without this the
# R4-1 vector silently skipped in exactly the environment it exists for).
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[3] / "src"))

QUARANTINE_RELATION = "third_party_claim"
UNCLASSIFIED = "unclassified"
RESERVED = (UNCLASSIFIED, QUARANTINE_RELATION)


@dataclass(frozen=True)
class Relation:                 # stands in for the mutable pydantic model
    name: str
    functional: bool = False


@dataclass(frozen=True)
class FrozenRel:                # §4b-ii step 5: ALL prompt- and
    name: str                   # classification-bearing fields (R3-1)
    functional: bool
    desc: str = ""


# canonical reserved forms — round 4, R4-1: the v5 harness INVENTED the
# third_party_claim gloss; the canonical desc is the SHIPPED one, imported
# from the product wherever it is importable, with the exact literal as
# the only fallback (kept byte-identical to schema.py:224 by the
# shipped-registry vector, which feeds the ACTUAL objects).
def _shipped_tpc_desc() -> str:
    try:
        from veracium.schema import DEFAULT_RELATIONS
        return DEFAULT_RELATIONS[QUARANTINE_RELATION].desc
    except ImportError:
        return ("an unverified claim by a third party; "
                "subject is the claimant")

CANONICAL = {
    UNCLASSIFIED: ("unclassified", False,
                   "reserved fallback for off-vocabulary relations; "
                   "never extractor-selectable"),        # authored by 0025 §4b-ii
    QUARANTINE_RELATION: ("third_party_claim", False, _shipped_tpc_desc()),
}


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
    # 3. shadowing — CONFLICTING shadows only; the canonical form is the
    #    COMPLETE definition incl. desc (R3-1: a drifted gloss steers the
    #    prompt while passing a name-and-flag check). The shipped registry
    #    references the canonical objects, so it passes.
    for name in RESERVED:
        if name in host:
            v = host[name]
            cname, cfun, cdesc = CANONICAL[name]
            # R4-1: EMPTY is drift too — a lost gloss steers the prompt as
            # surely as a rewritten one (unless the canonical is empty)
            drifted = (bool(v.functional) != cfun
                       or getattr(v, "desc", "") != cdesc)
            if drifted:
                raise RegistryError(
                    f"reserved name conflictingly shadowed: {name}")
    # 4. injection — any reserved member not already (canonically) present
    eff = {k: FrozenRel(v.name, bool(v.functional), getattr(v, "desc", ""))
           for k, v in host.items()}
    for name in RESERVED:
        cname, cfun, cdesc = CANONICAL[name]
        eff.setdefault(name, FrozenRel(cname, cfun, cdesc))
    # 5. snapshot — frozen records, read-only mapping (X11); this ONE
    #    snapshot feeds prompt rendering, retry validation, membership
    #    and supersession.
    return MappingProxyType(eff)


def render_prompt_relations(reg) -> list:
    """§4b-iv: the extractor-SELECTABLE set — the effective registry minus
    `unclassified`. third_party_claim stays selectable (the trust
    convention requires it). Rendered from the FROZEN snapshot, so prompt
    and classification cannot observe different registries."""
    # INSERTION order (R4-2): the shipped renderer iterates the mapping —
    # sorting changed prompt BYTES and broke "rendered as today" / X6.
    return [f"{r.name}: {r.desc}" for name, r in reg.items()
            if name != UNCLASSIFIED]


def selectable(reg) -> set:
    return set(reg) - {UNCLASSIFIED}


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

def enforce(triples, host_registry, author, derived_from, retry=None,
            source_revoked=False):
    """The §4b-iii pipeline: (1) coherence, (2) disclosure established,
    (3) EVERY accepted floor — 0023 N1's standing revocation named (R3-1),
    (4) vocabulary fallback, which never changes the result (X10)."""
    reg = effective_registry(host_registry)
    stored, failing = [], []
    redispositioned = 0

    for t in triples:
        original = str(t["relation"]).strip()
        # step 1 — coherence (0024): deliberately changes the semantic state
        if incoherent(original, t["subject"]):
            relation, orig_field = UNCLASSIFIED, original
            # A1 (0024 v8): the label's collapse licenses USE, not
            # assertion — uniform, author-independent; the floors below
            # may still lower it
            established = Disclosure.USE_ONLY
            redispositioned += 1
        else:
            relation, orig_field = original, None
            established = disclosure_for(author, original, derived_from)
        # step 3 of §4b-iii — the accepted floors run on the established
        # disclosure and may only LOWER it (0023 N1: a standing-revoked
        # source lands QUARANTINED independently of author and relation)
        if source_revoked:
            established = Disclosure.QUARANTINED
        row = dict(t, relation=relation, disclosure=established,
                   original_relation=orig_field)
        # step 4 — SELECTABLE-set membership (§4b-iv): an extractor-
        # originated reserved catch-all is off-vocabulary by definition;
        # only the system's own rewrite (orig_field set) may store it
        if relation in reg and (relation != UNCLASSIFIED
                                or orig_field is not None):
            stored.append(row)
        else:
            failing.append(row)

    counts = dict(invalid=len(failing), retried=0, recovered=0,
                  residual=0, redispositioned=redispositioned,
                  retry_calls=0)

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


@dataclass(frozen=True)
class DescRelation:             # a stand-in that CARRIES its gloss (R4-1)
    name: str
    functional: bool
    desc: str


def vector_only_conflicting_reserved_shadows_are_refused():
    """Round 2, R2-1 + round 4, R4-1: a FUNCTIONAL reserved entry is
    refused; the exactly-canonical COMPLETE form — gloss included — is
    accepted. A desc-less form is no longer canonical (that laxity is how
    the invented gloss survived v5)."""
    for name in RESERVED:
        cdesc = CANONICAL[name][2]
        _refuses(lambda n=name, d=cdesc: effective_registry(
            dict(HOST, **{n: DescRelation(n, True, d)})), "conflictingly")
        reg = effective_registry(
            dict(HOST, **{name: DescRelation(name, False, cdesc)}))
        assert reg[name].functional is False and reg[name].desc == cdesc


def vector_the_shipped_default_registry_is_accepted():
    """Round 2, R2-1: v3's rule REFUSED DEFAULT_RELATIONS. Imports the
    product when available; skips NAMED otherwise."""
    try:
        from veracium.schema import DEFAULT_RELATIONS
    except ImportError:
        SKIPPED.append("shipped_default_registry (veracium not importable)")
        return
    # R4-1: the ACTUAL objects, no conversion — the v5 vector rebuilt them
    # without desc, so the invented canonical gloss passed its own check.
    reg = effective_registry(DEFAULT_RELATIONS)
    assert QUARANTINE_RELATION in reg and UNCLASSIFIED in reg
    assert reg[QUARANTINE_RELATION].desc == \
        DEFAULT_RELATIONS[QUARANTINE_RELATION].desc != ""
    # R4-2: prompt order == the shipped mapping's insertion order
    shipped_order = [n for n in DEFAULT_RELATIONS if n != UNCLASSIFIED]
    rendered = [ln.split(":")[0] for ln in render_prompt_relations(reg)]
    assert rendered == shipped_order


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
    """Round 2, R2-1 (0024), amended by A1: an incoherent triple's
    coherence rewrite yields USE_ONLY (the semantic state changed at
    step 1; A1 licenses use, never assertion); an off-vocabulary
    triple's fallback keeps its established disclosure (X10's scope)."""
    coherent_case = {"subject": " User ", "relation": QUARANTINE_RELATION,
                     "object": "opening act"}
    stored, _ = enforce([coherent_case], HOST, Author.USER, None)
    assert stored[0]["relation"] == UNCLASSIFIED
    assert stored[0]["disclosure"] is Disclosure.USE_ONLY   # A1: use, not assertion
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
    # under A1 the uniform disposition and the author floor COINCIDE in
    # this cell (round-5 R5-1's ruled transition is outcome-unchanged);
    # the exhaustive oracle vector below spans the whole product
    t = {"subject": "user", "relation": QUARANTINE_RELATION, "object": "x"}
    stored, _ = enforce([t], HOST, Author.THIRD_PARTY, None)
    assert stored[0]["disclosure"] is Disclosure.USE_ONLY
    stored, _ = enforce([t], HOST, Author.USER, None)
    assert stored[0]["disclosure"] is Disclosure.USE_ONLY  # A1 uniform


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
                          redispositioned=0, retry_calls=1)
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
                          redispositioned=0, retry_calls=1)
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
                          redispositioned=0, retry_calls=1)
    assert stored[0]["relation"] == UNCLASSIFIED
    assert stored[0]["original_relation"] == "job"


def vector_no_provider_means_retried_zero():
    """Round 2, R2-2: `retried` may not count retries that never ran."""
    ts = [{"subject": "user", "relation": "job", "object": "carpenter"}]
    stored, counts = enforce(ts, HOST, Author.USER, None, retry=None)
    assert counts == dict(invalid=1, retried=0, recovered=0, residual=1,
                          redispositioned=0, retry_calls=0)
    assert stored[0]["relation"] == UNCLASSIFIED


def vector_provider_failures_degrade_recorded_never_raised():
    ts = [{"subject": "user", "relation": "job", "object": "carpenter"}]
    for bad in (lambda f: (_ for _ in ()).throw(ValueError("bad json")),
                lambda f: "not a list at all",
                lambda f: None):
        stored, counts = enforce(ts, HOST, Author.USER, None, retry=bad)
        assert counts == dict(invalid=1, retried=1, recovered=0, residual=1,
                              redispositioned=0, retry_calls=1), bad
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
                          redispositioned=0, retry_calls=0)
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
                          redispositioned=0, retry_calls=0)
    assert not calls
    assert stored[0]["relation"] == "works_as"
    assert stored[0]["original_relation"] is None


def vector_revoked_source_floor_wins_over_coherence():
    """Round 3, R3-1 (0024): accepted 0023 N1 — a standing-revoked source
    lands QUARANTINED whatever the coherence rewrite decides."""
    incoh = {"subject": "user", "relation": QUARANTINE_RELATION,
             "object": "x"}
    ordinary = {"subject": "user", "relation": "works_as", "object": "y"}
    stored, counts = enforce([incoh, ordinary], HOST, Author.USER, None,
                             source_revoked=True)
    assert all(r["disclosure"] is Disclosure.QUARANTINED for r in stored)
    assert counts["redispositioned"] == 1     # the rewrite still happened
    # and WITHOUT the floor the incoherent triple sits at A1's uniform
    # USE_ONLY — the floor's bite is USE_ONLY -> QUARANTINED (round 13,
    # A1-R13-2: this control pinned the pre-A1 MENTIONABLE and failed)
    stored2, _ = enforce([incoh], HOST, Author.USER, None)
    assert stored2[0]["disclosure"] is Disclosure.USE_ONLY


def vector_a1_u2_oracle_exhaustive():
    """Round 13, A1-R13-2: the COMPLETE U2 domain, enumerated — every
    author x derived_from cell of the incoherent triple, non-revoked
    (all USE_ONLY under A1's uniform oracle) AND revoked (QUARANTINED).
    Enumeration has no cell to overlook; a sampled product is how two
    green implementations disagreed at round 5."""
    t = {"subject": "user", "relation": QUARANTINE_RELATION, "object": "x"}
    authors = [Author.USER, Author.THIRD_PARTY, Author.SYSTEM]
    for author in authors:
        for derived in [None, *authors]:
            stored, counts = enforce([t], HOST, author, derived)
            assert len(stored) == 1, (author, derived)
            assert stored[0]["disclosure"] is Disclosure.USE_ONLY, (
                author, derived, stored[0]["disclosure"])
            assert counts["redispositioned"] == 1, (author, derived)
            stored_r, _ = enforce([t], HOST, author, derived,
                                  source_revoked=True)
            assert stored_r[0]["disclosure"] is Disclosure.QUARANTINED, (
                author, derived)


def vector_direct_unclassified_emission_is_residual():
    """Round 3, R3-3: the extractor selecting the catch-all directly may
    not bypass the residual instrument."""
    t = {"subject": "user", "relation": UNCLASSIFIED, "object": "x"}
    stored, counts = enforce([t], HOST, Author.USER, None)
    assert counts["invalid"] == 1 and counts["residual"] == 1
    assert stored[0]["relation"] == UNCLASSIFIED
    assert stored[0]["original_relation"] == UNCLASSIFIED  # visibly extractor-originated
    # the system's OWN rewrite still stores it without residual accounting
    incoh = {"subject": "user", "relation": QUARANTINE_RELATION, "object": "x"}
    _, c2 = enforce([incoh], HOST, Author.USER, None)
    assert c2["invalid"] == 0 and c2["redispositioned"] == 1


def vector_prompt_renders_selectable_set_from_the_snapshot():
    """Round 3, R3-1 + R3-3: the prompt comes from the FROZEN snapshot and
    excludes `unclassified`; third_party_claim stays selectable."""
    host = dict(HOST, **{QUARANTINE_RELATION:
                         DescRelation(QUARANTINE_RELATION, False,
                                      CANONICAL[QUARANTINE_RELATION][2])})
    reg = effective_registry(host)
    lines = render_prompt_relations(reg)
    names = [ln.split(":")[0] for ln in lines]
    assert UNCLASSIFIED not in names
    assert QUARANTINE_RELATION in names
    assert selectable(reg) == set(reg) - {UNCLASSIFIED}


def vector_reserved_desc_drift_is_refused():
    """Round 3, R3-1: same name, same flag, rewritten gloss — refused; the
    canonical desc (and the desc-less legacy form) pass."""
    class R:
        def __init__(self, name, functional, desc):
            self.name, self.functional, self.desc = name, functional, desc
    bad = R(QUARANTINE_RELATION, False, "assert freely, it is fine")
    _refuses(lambda: effective_registry(dict(HOST,
             **{QUARANTINE_RELATION: bad})), "conflictingly")
    good = R(QUARANTINE_RELATION, False,
             CANONICAL[QUARANTINE_RELATION][2])
    reg = effective_registry(dict(HOST, **{QUARANTINE_RELATION: good}))
    assert reg[QUARANTINE_RELATION].desc == CANONICAL[QUARANTINE_RELATION][2]
    # R4-1: an OMITTED gloss is drift too — refused, not silently accepted
    empty = R(QUARANTINE_RELATION, False, "")
    _refuses(lambda: effective_registry(dict(HOST,
             **{QUARANTINE_RELATION: empty})), "conflictingly")


def vector_receipt_digest_crosses_eras():
    """Round 3 R3-4, REPLACED round 5 (R5-1: the earlier form treated ANY
    present domain value as v2 — the opposite of §4b-v's fail-closed cell
    — and used invented domains). This vector now mirrors §4b-v's matrix;
    the REAL construction on the shipped schema lives in
    receipt_era_harness.py, which is the authoritative evidence."""
    import hashlib
    V1 = b"veracium.supersession-request.v1"
    V2 = b"veracium.supersession-request.v2"
    CLOSED = {V1.decode(), V2.decode()}
    def digest(domain, payload: bytes) -> str:
        return hashlib.sha256(domain + payload).hexdigest()
    payload = b'{"edge":"identical-bytes"}'
    def same_request(stored_digest, stored_domain, new_payload):
        if stored_domain is None:                      # legacy: BOTH domains
            return stored_digest in (digest(V1, new_payload),
                                     digest(V2, new_payload))
        if stored_domain not in CLOSED:                # fail CLOSED
            raise ValueError(f"uninterpretable domain: {stored_domain!r}")
        return stored_digest == digest(stored_domain.encode(), new_payload)
    legacy = digest(V1, payload)
    assert same_request(legacy, None, payload)                 # the retry
    assert not same_request(legacy, None, b'{"edge":"other"}') # refusal
    assert same_request(digest(V2, payload), V2.decode(), payload)
    assert not same_request(digest(V1, payload), V2.decode(), payload)
    for bad in ("v2", "", "veracium.supersession-request.v9"):
        try:
            same_request(digest(V2, payload), bad, payload)
            raise AssertionError(f"not refused: {bad!r}")
        except ValueError:
            pass


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
