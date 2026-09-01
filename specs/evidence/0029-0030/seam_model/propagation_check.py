"""Seam-model ↔ spec PROPAGATION CHECK.

Round 3 ended with a defect neither seat expected: 0030 v14's §4a-iii said
"PARSE json → mapping", which followed faithfully yields a PLAIN decoder --
the exact duplicate-key declassification the runnable model forbids. The spec
was INSTRUCTING the vulnerability the model refuses.

The mechanism was ORDERING, not carelessness: v14 was written before two
episodes the model then absorbed, and nothing propagated them back. **Any time
a runnable artifact outruns its normative one, the divergence is silent by
default.** This check makes it loud.

DESIGN, per the 0029 seat's note: check the RULE, not the PROSE. Each rule
carries a MODEL PROBE that is EXECUTED (not read) and a SPEC ANCHOR set of
mechanism names. Anchoring on mechanism rather than sentences means ordinary
wording churn does not fail the check -- otherwise every micro-fold pays a
brittleness tax and the check gets disabled, which is how such checks die.

RULE ZERO applies to this file too: `control_check_can_fail` proves the check
detects an un-propagated rule, using a fixture spec with one rule removed. A
propagation check that cannot fail would be exactly the joke this round earned.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable, Sequence

import raw_adapter as RA
from raw_adapter import _strict_pairs   # the checker USES the discipline it ENFORCES
from veracium.schema import (Disclosure, Edge, EvidenceAuthor, Provenance,
                             QUARANTINE_RELATION)


@dataclass(frozen=True)
class Rule:
    # ANCHOR DISCIPLINE, learned twice on this file's own runs: anchors name a
    # MECHANISM and nothing more. "PER OBJECT" failed on a line wrap; "1..512"
    # failed because the spec wrote `1..IDENTITY_MAX`. Both were over-specified
    # -- they encoded FORMATTING, and formatting churns. Each false positive
    # tempts the next person to disable the check, which is how it dies. If an
    # anchor needs more than a symbol name to be unambiguous, the rule is
    # probably not crisp enough to check mechanically.
    id: str
    section: str                       # the normative carrier's section
    model_probe: Callable[[], bool]    # EXECUTED against the model
    spec_anchors: Sequence[str]        # mechanism names, not sentences
    why: str


def _dup_key_payload() -> str:
    e = Edge(id="e1", user_id="u", subject="user", relation="has_diet",
             object="avoids dairy",
             provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                   evidence_ref="ev",
                                   disclosure=Disclosure.QUARANTINED))
    return RA.craft_duplicate_key_payload(e.model_dump_json())


def _probe_strict_decoder() -> bool:
    """EXECUTED: the adapter refuses a duplicate-key payload."""
    return RA.adapt(_dup_key_payload(), expect_id="e1", expect_user="u") is None


def _probe_two_disjunct_quarantine() -> bool:
    """EXECUTED: relation alone quarantines, disclosure alone quarantines."""
    return (RA.derive_quarantined(QUARANTINE_RELATION, Disclosure.MENTIONABLE.value)
            and RA.derive_quarantined("has_diet", Disclosure.QUARANTINED.value))


def scope_shape_keys_from_production() -> frozenset:
    """INTROSPECT the production function -- do not restate it.

    Round-4 F3's diagnosis of why this check was blind to its own author's
    error: the probe compared a HARDCODED SET to a HARDCODED SET, so it could
    only confirm that two of our own restatements agreed. It could not see
    that BOTH were wrong. A check that never reads the production code is a
    mirror, not a check.

    This calls the real `MembershipResolver._record_shape` on a real `Edge`
    and returns the keys it ACTUALLY reads, so the authority is the function.
    """
    from veracium.scope_read import MembershipResolver
    e = Edge(id="p", user_id="u", subject="s", relation="has_diet", object="o",
             provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                   evidence_ref="ev"))
    shape = MembershipResolver._record_shape(MembershipResolver.__new__(
        MembershipResolver), e)
    return frozenset(shape)


def _probe_scope_field_set() -> bool:
    """EXECUTED against production: the adapter must carry every field the
    shape path reads, and must not CLAIM a field it does not read.

    `lineage` is read via `getattr(record, "lineage", None)` and `Edge` has no
    such field, so the adapter does not carry it; `disclosure` is needed by the
    adapter's FLAG DERIVATION but is NOT a shape-path field -- conflating those
    two questions is exactly the round-4 error.
    """
    # VOCABULARY CAVEAT, found by this very probe on its first hardened run:
    # `_record_shape` returns {"author": p.author_of_evidence.value, ...} --
    # the dict KEY is "author" while the PROVENANCE FIELD read is
    # "author_of_evidence". Introspecting the OUTPUT therefore yields the
    # shape's vocabulary, not the field names a carrier must supply. The map
    # below is the translation, and it is the only restatement left; everything
    # else comes from production. Stated because a silent rename here would
    # reintroduce exactly the mirror this hardening removed.
    SHAPE_KEY_TO_PROV_FIELD = {"author": "author_of_evidence",
                               "evidence_ref": "evidence_ref",
                               "origin": "origin", "source_id": "source_id"}
    production_keys = scope_shape_keys_from_production() - {"lineage"}
    if set(SHAPE_KEY_TO_PROV_FIELD) != production_keys:
        return False        # production grew or renamed a key: refuse, loudly
    needed = frozenset(SHAPE_KEY_TO_PROV_FIELD[k] for k in production_keys)
    carried = RA.SCOPE_PROVENANCE_KEYS - {"disclosure"}
    return carried == needed


def _probe_type_before_membership() -> bool:
    """EXECUTED: an unhashable value REFUSES rather than raising.

    0030's V-NORMALIZE states this for the classifier; round-4 found the
    adapter violating it. A spec rule is not confined to the field that
    motivated it, so the check now covers the rule wherever it applies.
    """
    e = Edge(id="e1", user_id="u", subject="user", relation="has_diet",
             object="o", provenance=Provenance(
                 author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev"))
    m = json.loads(e.model_dump_json(), object_pairs_hook=_strict_pairs)
    m["provenance"]["disclosure"] = []            # unhashable
    try:
        return RA.adapt(json.dumps(m), expect_id="e1", expect_user="u") is None
    except TypeError:
        return False                              # raised instead of refusing


def _probe_identity_bounds() -> bool:
    """EXECUTED: an out-of-bound identity field refuses (round-4 F2)."""
    e = Edge(id="e1", user_id="u", subject="user", relation="has_diet",
             object="o", provenance=Provenance(
                 author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev"))
    m = json.loads(e.model_dump_json(), object_pairs_hook=_strict_pairs)
    m["provenance"]["source_id"] = []
    return RA.adapt(json.dumps(m), expect_id="e1", expect_user="u") is None


def _probe_author_is_real_enum() -> bool:
    """EXECUTED: a payload whose author is a valid string yields the real ENUM
    (a string stand-in would pass hand-written tests and raise live)."""
    e = Edge(id="e1", user_id="u", subject="user", relation="has_diet",
             object="avoids dairy",
             provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                   evidence_ref="ev"))
    a = RA.adapt(e.model_dump_json(), expect_id="e1", expect_user="u")
    # DEFENSIVE: a probe that RAISES cannot report "not enforced" -- it
    # explodes and takes the whole check with it. Found by mutating the model
    # to refuse everything: this probe assumed success. Probes return False.
    return a is not None and isinstance(a.provenance.author_of_evidence,
                                        EvidenceAuthor)


RULES = (
    Rule("strict-decoder", "0030 §4a-iii step 1", _probe_strict_decoder,
         ("duplicate", "PER OBJECT"),
         "a plain decoder is last-wins and DECLASSIFIES a quarantined claim"),
    Rule("two-disjunct-quarantine", "0030 §4a-iii step 5",
         _probe_two_disjunct_quarantine, ("TWO disjuncts", "QUARANTINE_RELATION"),
         "one disjunct lets a third-party CLAIM through"),
    Rule("scope-field-authority", "0030 §4a-iii step 6", _probe_scope_field_set,
         ("_record_shape", "scope_read.py:170-176"),
         "the shape-path field set must be INTROSPECTED from production, never restated"),
    Rule("type-before-membership", "0030 V-NORMALIZE", _probe_type_before_membership,
         ("unhashable", "membership"),
         "an unhashable value reaching `in`/`dict.get` RAISES instead of refusing"),
    Rule("identity-bounds", "0030 §4a-iii step 6", _probe_identity_bounds,
         ("IDENTITY_MAX",),   # mechanism name only -- see ANCHOR DISCIPLINE
         "presence is not validity; the consumer raises on out-of-bound identity fields"),
    Rule("author-real-enum", "0030 §4a-iii step 6", _probe_author_is_real_enum,
         ("EvidenceAuthor", ".value"),
         "a string stand-in passes hand-written tests and raises live"),
)


def _normalise(text: str) -> str:
    """Collapse whitespace before anchor matching.

    Learned immediately, on this check's FIRST run: the anchor "PER OBJECT"
    missed because the spec wraps it as "PER\n                OBJECT". A
    multi-word anchor is brittle to line wrapping, which is precisely the
    brittleness tax the 0029 seat warned would get such checks disabled. The
    anchor still names a MECHANISM; normalising only removes the typography.
    """
    return re.sub(r"\s+", " ", text)


#: The NINE surviving carriers named in the round-4 verdict, as a REGRESSION
#: LIST rather than a sweep. Each is a (id, forbidden-pattern, why) triple: the
#: pattern is text that must NOT reappear, because each one is a stale carrier
#: that survived the fold which should have removed it.
#:
#: A LIST, deliberately, not a "full sweep". The claim "the full sweep was
#: executed" has been FALSE TWICE in this arc; a named list of nine can be
#: checked and reported honestly, where a sweep invites the claim that killed
#: us. Widened is not exhausted.
CARRIER_REGRESSIONS = (
    ("C1-signature", "classify_as_of(snapshot, current, T, now",
     "§1/§2 published the pre-carrier signature"),
    ("C3-caps-from-row", "from the CURRENT row",
     "§3 said current caps come from the row; they come from standing state"),
    ("C4-three-inputs", "needs three distinct inputs",
     "§4a introduced the pre-carrier input count"),
    ("C5-current-trust-heading", "### 4a-i. `current_trust`",
     "§4a-i kept the pre-carrier name"),
    ("C6-cache-and-multisweep", "cacheable per",
     "a v9 cost/cache sentence contradicted the one-sweep/no-cache rules ABOVE it"),
    ("C8-empty-interval-incoherent", 'unknown "eighth" reason, empty interval',
     "§6a called coherent states incoherent, contradicting V-MALFORMED"),
)

#: Carriers whose fix is a PRESENCE requirement rather than an absence.
CARRIER_PRESENCE = (
    ("C2-2c-carrier-inputs", "the **carrier inputs**", "§2c must inventory them"),
    ("C7-vbind-carrier", "carrier model updated round-4 C7", "V-BIND/V-ADDITIVE"),
    ("C9-requires-0029", "consumed DIRECTLY", "Spec-Requires must name 0029"),
)


def check_carriers(spec_text: str) -> list[str]:
    """The nine, walked as a list. Reported individually, never as a sweep."""
    flat = _normalise(spec_text)
    out = []
    for cid, pat, why in CARRIER_REGRESSIONS:
        if _normalise(pat) in flat:
            out.append(f"{cid}: STALE CARRIER RETURNED — {why}")
    for cid, pat, why in CARRIER_PRESENCE:
        if _normalise(pat) not in flat:
            out.append(f"{cid}: FIX MISSING — {why}")
    return out


def check(spec_text: str, rules: Sequence[Rule] = RULES) -> list[str]:
    """Return a list of divergence descriptions; empty means propagated.

    TWO-WAY by construction: a rule the MODEL enforces must be REQUIRED by the
    spec (the v14 failure -- the model outran its spec), and a rule the spec
    states must be ENFORCED by the model (the reverse drift). Both directions
    are silent by default, so both are checked.
    """
    out: list[str] = []
    flat = _normalise(spec_text)
    for r in rules:
        in_model = r.model_probe()
        in_spec = all(_normalise(a) in flat for a in r.spec_anchors)
        if in_model and not in_spec:
            out.append(f"{r.id}: ENFORCED by the model, NOT REQUIRED by "
                       f"{r.section} — the spec would instruct the defect "
                       f"({r.why})")
        elif in_spec and not in_model:
            out.append(f"{r.id}: REQUIRED by {r.section}, NOT ENFORCED by the "
                       f"model — the model does not test what the spec promises")
    return out


# --------------------------------------------------------------------------
# NEGATIVE CONTROL
# --------------------------------------------------------------------------

def control_check_can_fail(spec_text: str) -> bool:
    """Remove one rule's anchors from a COPY of the spec; the check must fire.

    True means the check detects an un-propagated rule. If this ever returns
    False the propagation check has become unfailable -- the exact class it
    exists to prevent, and the one this round was spent learning.
    """
    clean = check(spec_text)
    if clean:
        return False                    # can't run the control on a dirty spec
    mutilated = spec_text.replace("duplicate", "XXXX").replace("PER OBJECT", "XXXX")
    found = check(mutilated)
    return any(f.startswith("strict-decoder:") for f in found)
