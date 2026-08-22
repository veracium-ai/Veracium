"""The effective relation registry — specs/0025 §4b-ii, accepted v13.

The host's registry dict is validated AS SUPPLIED at the `ingest_event`
boundary, the reserved members are injected, and the result is EXTRACTED
into an immutable per-event snapshot of frozen `(name, functional, desc)`
records — all prompt- and classification-bearing fields (X11). This ONE
snapshot feeds prompt rendering, retry validation, membership, and
supersession; there is no second registry read anywhere in the event.

Construction order (each step's position is load-bearing — §4b-ii):
  1. shape (every value a Relation, every key == its value's name)
  2. empty AS SUPPLIED (before injection can mask it — X5)
  3. conflicting-shadow refusal (the COMPLETE canonical form, desc
     included; an empty gloss is drift too — rounds 2/3/4 each narrowed
     this rule and the shipped DEFAULT_RELATIONS passes verbatim)
  4. injection of both reserved members (X8)
  5. the frozen snapshot (X11)

Differentially tested against specs/evidence/0025/reference_enforcement.py.
"""
from types import MappingProxyType
from typing import NamedTuple

from .schema import QUARANTINE_RELATION, RESERVED_RELATIONS, UNCLASSIFIED_RELATION


class FrozenRel(NamedTuple):
    """The snapshot's OWN record — never the host's mutable model."""
    name: str
    functional: bool
    desc: str


class RegistryError(ValueError):
    """A host registry the boundary refuses (X5/X9)."""


def effective_registry(host: dict) -> MappingProxyType:
    # 1. shape
    for k, v in host.items():
        if not hasattr(v, "name") or not hasattr(v, "functional"):
            raise RegistryError(f"value for {k!r} is not a Relation")
        if k != v.name:
            raise RegistryError(f"key {k!r} != Relation.name {v.name!r} — "
                                f"membership and lookup would disagree")
    # 2. empty — AS SUPPLIED (X5)
    if not host:
        raise RegistryError("empty registry refused — every relation would "
                            "be off-vocabulary, silently")
    # 3. conflicting shadows only; the canonical form is COMPLETE (desc
    #    included, empty is drift)
    for name, canon in RESERVED_RELATIONS.items():
        if name in host:
            v = host[name]
            if (bool(v.functional) != canon.functional
                    or getattr(v, "desc", "") != canon.desc):
                raise RegistryError(
                    f"reserved name conflictingly shadowed: {name!r} — the "
                    f"canonical form is (functional={canon.functional}, "
                    f"desc={canon.desc!r})")
    # 4. injection — any reserved member not already (canonically) present
    eff = {k: FrozenRel(v.name, bool(v.functional), getattr(v, "desc", ""))
           for k, v in host.items()}
    for name, canon in RESERVED_RELATIONS.items():
        eff.setdefault(name, FrozenRel(canon.name, canon.functional,
                                       canon.desc))
    # 5. the snapshot
    return MappingProxyType(eff)


def render_prompt_relations(reg) -> str:
    """§4b-iv: the extractor-SELECTABLE set — the effective registry minus
    `unclassified` — rendered in the registry's INSERTION order (round 4,
    R4-2: sorting changed prompt bytes), in the exact line format the
    prompt has always used. `third_party_claim` stays selectable: the
    trust convention requires the extractor to emit it for hearsay."""
    return "\n".join(
        f"- {name}: {r.desc}" if r.desc else f"- {name}"
        for name, r in reg.items() if name != UNCLASSIFIED_RELATION)
