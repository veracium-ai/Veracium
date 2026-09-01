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
from veracium.schema import (Disclosure, Edge, EvidenceAuthor, Provenance,
                             QUARANTINE_RELATION)


@dataclass(frozen=True)
class Rule:
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


def _probe_scope_field_set() -> bool:
    """EXECUTED: the scope-feeding set is the one `_record_shape` reads,
    INCLUDING `disclosure`, which a summary of that list omits."""
    return RA.SCOPE_PROVENANCE_KEYS == frozenset({
        "author_of_evidence", "origin", "source_id", "evidence_ref", "disclosure"})


def _probe_author_is_real_enum() -> bool:
    """EXECUTED: a payload whose author is a valid string yields the real ENUM
    (a string stand-in would pass hand-written tests and raise live)."""
    e = Edge(id="e1", user_id="u", subject="user", relation="has_diet",
             object="avoids dairy",
             provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                   evidence_ref="ev"))
    a = RA.adapt(e.model_dump_json(), expect_id="e1", expect_user="u")
    return isinstance(a.provenance.author_of_evidence, EvidenceAuthor)


RULES = (
    Rule("strict-decoder", "0030 §4a-iii step 1", _probe_strict_decoder,
         ("duplicate", "PER OBJECT"),
         "a plain decoder is last-wins and DECLASSIFIES a quarantined claim"),
    Rule("two-disjunct-quarantine", "0030 §4a-iii step 5",
         _probe_two_disjunct_quarantine, ("TWO disjuncts", "QUARANTINE_RELATION"),
         "one disjunct lets a third-party CLAIM through"),
    Rule("scope-field-authority", "0030 §4a-iii step 6", _probe_scope_field_set,
         ("_record_shape", "scope_read.py:170-176"),
         "the authority adds `disclosure`, which any summary of the list omits"),
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
