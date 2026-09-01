"""Seam model driver — research's halves (adapter + bound carrier).

RULE ZERO: every assertion has a negative control proving it CAN fail. The
controls are asserted too, so a control that stops discriminating is itself a
test failure. A check that cannot fail is worse than no check.

Payloads come from a REAL `Edge.model_dump_json()`, never hand-written, so the
schema cannot drift from the shipped model without this failing.
"""
from __future__ import annotations

import json
import pytest

from veracium.schema import (Disclosure, Edge, EvidenceAuthor, Provenance,
                             QUARANTINE_RELATION)

import sys
from pathlib import Path

SEAM = Path(__file__).resolve().parents[1] / "specs" / "evidence" / "0029-0030" / "seam_model"
sys.path.insert(0, str(SEAM))

from raw_adapter import (Adapted, adapt, control_defaulting_a_missing_field_would_grant,
                         control_flags_are_not_serialized,
                         control_one_disjunct_lets_a_claim_through,
                         derive_quarantined, derive_use_only)
from current_state_carrier import (BOUND, IDENTITY_UNBOUND, CurrentState, Envelope,
                                   RawEdgeState, View, bind,
                                   control_absence_does_not_grant,
                                   control_binding_is_load_bearing,
                                   control_binding_survives_a_corrupt_payload,
                                   control_view_leg_is_bound)


def _edge(relation="has_diet", disclosure=Disclosure.MENTIONABLE, eid="e1", uid="u"):
    return Edge(id=eid, user_id=uid, subject="user", relation=relation,
                object="avoids dairy",
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref="seam", disclosure=disclosure))


# ---------------------------------------------------------------- adapter --

def test_adapter_accepts_a_real_payload():
    e = _edge()
    a = adapt(e.model_dump_json(), expect_id="e1", expect_user="u")
    assert isinstance(a, Adapted)
    assert a.quarantined is False and a.use_only is False


def test_flags_are_derived_not_read__with_its_control():
    """F3: the flags are @property and appear in NO payload."""
    payload = json.loads(_edge().model_dump_json())
    # CONTROL: a field-reading adapter would refuse every payload.
    assert control_flags_are_not_serialized(payload), \
        "flags appear in the payload -- the derivation is no longer necessary"
    # and the derivation still produces them
    a = adapt(json.dumps(payload), expect_id="e1", expect_user="u")
    assert a.quarantined is False


def test_quarantined_has_TWO_disjuncts__with_its_control():
    """The catch this model exists for."""
    # relation disjunct alone
    assert derive_quarantined(QUARANTINE_RELATION, Disclosure.MENTIONABLE.value)
    # disclosure disjunct alone
    assert derive_quarantined("has_diet", Disclosure.QUARANTINED.value)
    assert derive_use_only(Disclosure.USE_ONLY.value)
    # CONTROL: the one-disjunct shortcut lets a third-party CLAIM through.
    assert control_one_disjunct_lets_a_claim_through(), \
        "the one-disjunct derivation no longer differs -- control is vacuous"


def test_third_party_claim_is_quarantined_end_to_end():
    e = _edge(relation=QUARANTINE_RELATION, disclosure=Disclosure.MENTIONABLE)
    a = adapt(e.model_dump_json(), expect_id="e1", expect_user="u")
    assert a.quarantined is True, "a third-party claim escaped quarantine"


def test_incomplete_provenance_refuses__with_its_control():
    m = json.loads(_edge().model_dump_json())
    del m["provenance"]["disclosure"]
    text = json.dumps(m)
    assert adapt(text, expect_id="e1", expect_user="u") is None
    # CONTROL: defaulting instead of refusing would GRANT (use_only False).
    assert control_defaulting_a_missing_field_would_grant(text), \
        "defaulting no longer grants -- control is vacuous"


def test_foreign_payload_identity_refuses():
    """C-4: the payload's id must match the row-sourced id."""
    e = _edge(eid="OTHER")
    assert adapt(e.model_dump_json(), expect_id="e1", expect_user="u") is None


def test_unparseable_text_refuses():
    assert adapt("}{ not json", expect_id="e1", expect_user="u") is None


@pytest.mark.parametrize("missing", sorted(
    {"id", "user_id", "subject", "relation", "object", "note",
     "valid_from", "invalidated_at", "invalidation_reason"}))
def test_every_required_key_is_actually_required(missing):
    """Totality: each required key, removed individually, must refuse."""
    m = json.loads(_edge().model_dump_json())
    m.pop(missing)
    assert adapt(json.dumps(m), expect_id="e1", expect_user="u") is None, \
        f"a payload missing {missing!r} was accepted"


# ----------------------------------------------------------------- carrier --

def test_five_leg_binding__with_its_control():
    env = Envelope("u", "A")
    snap = RawEdgeState("A", "u", "{}")
    cur = CurrentState("u", "A", "{}", frozenset(), 1)
    assert bind(env, snap, cur, View("u")) == BOUND
    # CONTROL: an unbound variant accepts a foreign current leg.
    assert control_binding_is_load_bearing(), \
        "binding no longer discriminates -- control is vacuous"


def test_view_leg_is_bound__with_its_control():
    assert control_view_leg_is_bound(), "the view leg is not actually bound"


def test_binding_is_parse_independent__with_its_control():
    assert control_binding_survives_a_corrupt_payload(), \
        "binding now depends on the payload -- C-2 regressed"


def test_absence_never_grants__with_its_control():
    assert control_absence_does_not_grant()


# ------------------------------------------------- the REAL ScopeView ------
# Round-3 F3 asks the adapter be exercised against the ACTUAL ScopeView,
# including incomplete provenance. These drive a real store, a real policy and
# a real principal -- no stand-ins -- because the whole finding was that a
# DESCRIPTION of the seam was wrong.

import tempfile
from pathlib import Path

from veracium import SqliteStore
from veracium.scope import Identity, validate_policy
from veracium.scope_read import ScopeView

from raw_adapter import control_defaulting_author_fabricates_a_scope_decision


@pytest.fixture
def scope_view():
    with tempfile.TemporaryDirectory() as td:
        store = SqliteStore(str(Path(td) / "seam.db"))
        try:
            policy = validate_policy({}, cross_scope_visible=False,
                                     local_origin=store.local_origin())
            yield ScopeView(store, "u", Identity(origin=None,
                                                 source_id="mailbox-a"), policy)
        finally:
            store.close()


def _edge_with_source(source_id, eid="e1"):
    e = _edge(eid=eid)
    e.provenance.source_id = source_id
    return e


def test_adapted_edge_drives_the_real_scope_view(scope_view):
    """The end-to-end the verdict asked for: payload -> adapt -> real ScopeView."""
    own = adapt(_edge_with_source("mailbox-a").model_dump_json(),
                expect_id="e1", expect_user="u")
    assert own is not None
    assert scope_view.visible(own) is True
    assert scope_view.decision(own) == (True, "own")


def test_cross_scope_edge_is_not_visible__the_discriminating_pair(scope_view):
    """CONTROL by construction: the same adapter output, different source,
    yields the OPPOSITE decision -- so `visible` is reading our fields and
    not returning a constant."""
    foreign = adapt(_edge_with_source("other-mailbox", eid="e2").model_dump_json(),
                    expect_id="e2", expect_user="u")
    assert foreign is not None
    assert scope_view.visible(foreign) is False
    assert scope_view.decision(foreign) == (False, None)


def test_incomplete_provenance_refuses_because_it_feeds_scope(scope_view):
    """Incomplete provenance is a REFUSAL, not a tolerance -- with the control
    showing a defaulting variant silently manufactures a scope decision."""
    m = json.loads(_edge_with_source("mailbox-a").model_dump_json())
    del m["provenance"]["author_of_evidence"]
    text = json.dumps(m)
    assert adapt(text, expect_id="e1", expect_user="u") is None
    assert control_defaulting_author_fabricates_a_scope_decision(text, scope_view), \
        "defaulting the author no longer produces a classifiable record -- vacuous"


@pytest.mark.parametrize("missing", sorted(
    {"author_of_evidence", "origin", "source_id", "evidence_ref", "disclosure"}))
def test_every_scope_provenance_key_is_required(missing):
    """Totality over the fields ScopeView actually reads (scope_read.py:170-176).

    Presence is required even where the VALUE may be None: dev's 0029 v9
    execution established that model_dump_json SERIALIZES Nones, so a real
    payload always carries these keys and absence means damage.
    """
    m = json.loads(_edge_with_source("mailbox-a").model_dump_json())
    m["provenance"].pop(missing)
    assert adapt(json.dumps(m), expect_id="e1", expect_user="u") is None, \
        f"a payload whose provenance lacks {missing!r} was accepted"


def test_unknown_author_is_refused_not_defaulted():
    m = json.loads(_edge_with_source("mailbox-a").model_dump_json())
    m["provenance"]["author_of_evidence"] = "impostor"
    assert adapt(json.dumps(m), expect_id="e1", expect_user="u") is None


def test_duplicate_key_would_flip_trust_under_plain_loads():
    """0026's shipped gate refused this adapter's plain `json.loads`, and the
    reason is a real trust bypass, executed here rather than asserted.

    A payload with TWO `disclosure` keys — quarantined then mentionable —
    parses to MENTIONABLE under last-wins, so a QUARANTINED third-party claim
    would be DECLASSIFIED by the adapter. The strict hook refuses it.

    The plain parse lives HERE and not in the model because the evidence tree
    is exactly where the gate forbids it: the control proving a gate necessary
    would otherwise have to violate the gate.
    """
    from raw_adapter import craft_duplicate_key_payload, strict_refuses_duplicate_keys

    e = _edge(disclosure=Disclosure.QUARANTINED)
    honest = e.model_dump_json()
    assert adapt(honest, expect_id="e1", expect_user="u").quarantined is True

    attack = craft_duplicate_key_payload(honest)
    assert attack != honest, "fixture drift — the payload shape changed, control is vacuous"
    assert attack.count('"disclosure"') == 2

    # THE VULNERABILITY, demonstrated (deliberately plain — see docstring)
    assert json.loads(attack)["provenance"]["disclosure"] == Disclosure.MENTIONABLE.value, \
        "last-wins no longer declassifies — the gate's justification is no longer demonstrable"
    # THE DEFENCE
    assert strict_refuses_duplicate_keys(attack), "the strict hook accepted a duplicate key"


# ------------------------------------------- spec ↔ model propagation ------
# Round 3's last finding: 0030 v14's §4a-iii instructed a PLAIN decoder, i.e.
# the vulnerability the model forbids -- because v14 was written BEFORE two
# episodes the model absorbed and nothing propagated them back. Any time a
# runnable artifact outruns its normative one, the divergence is SILENT.

import re as _re

import propagation_check as PC

SPEC_0030 = (Path(__file__).resolve().parents[1]
             / "specs" / "0030-time-relative-classification.md")


def _spec_text():
    if not SPEC_0030.exists():
        pytest.skip("0030 spec not reachable from this tree")
    return SPEC_0030.read_text()


def test_every_model_rule_is_propagated_to_the_spec():
    """The check itself: no divergence in either direction."""
    assert PC.check(_spec_text()) == []


def test_the_propagation_check_can_fail__its_own_control():
    """Rule zero applied to the checker.

    A propagation check that cannot fail is the exact class this round was
    spent learning, and writing one today would be a poor joke.
    """
    assert PC.control_check_can_fail(_spec_text()), \
        "the propagation check no longer detects an un-propagated rule"


def test_it_retro_detects_the_REAL_v14_defect():
    """Stronger than a synthetic control: reconstruct the historical text.

    v14 said "PARSE json → mapping" with no strict rule. The check must name
    that divergence -- if it cannot detect the defect it was built for, it is
    decorative.
    """
    v14ish = _spec_text().replace(
        "with a decoder that REFUSES DUPLICATE KEYS,", "json → mapping,")
    v14ish = _re.sub(r"NOT a plain decoder.*?mechanism\.", "", v14ish, flags=_re.S)
    found = PC.check(v14ish)
    assert any(f.startswith("strict-decoder:") for f in found), \
        f"the v14 defect went undetected: {found}"


def test_reverse_drift_is_also_caught():
    """Two-way: a rule the SPEC requires but the MODEL stops enforcing.

    Simulated by a rule whose model probe fails while its anchors are present
    -- the direction where the model quietly stops testing what the spec
    promises, which is as silent as the v14 direction.
    """
    weakened = PC.Rule("simulated", "0030 §x", lambda: False,
                       ("REFUSES DUPLICATE KEYS",), "simulated reverse drift")
    found = PC.check(_spec_text(), rules=(weakened,))
    assert found and "NOT ENFORCED by the model" in found[0]


# --------------------------------------------- round-4 F2: TYPE totality ---
# The reviewer fed `provenance.source_id=[]`: the PRESENCE-only schema check
# accepted it and the real ScopeView raised. Presence is not validity. This is
# a MUTANT CAMPAIGN over the field domain rather than the four cases I would
# think of -- the point of the finding was that my chosen cases were the gap.

WRONG_TYPES = ([], {}, 0, 1, True, 3.5, ["x"], {"a": 1})

_TOP_FIELDS = ("id", "user_id", "subject", "relation", "object", "note")
_PROV_FIELDS = ("author_of_evidence", "evidence_ref", "origin", "source_id",
                "disclosure")


def _payload(**prov_over):
    e = _edge_with_source("mailbox-a")
    m = json.loads(e.model_dump_json())
    m["provenance"].update(prov_over)
    return m


@pytest.mark.parametrize("field", _TOP_FIELDS)
@pytest.mark.parametrize("bad", WRONG_TYPES)
def test_top_level_field_wrong_type_is_refused(field, bad):
    m = _payload()
    m[field] = bad
    assert adapt(json.dumps(m), expect_id="e1", expect_user="u") is None, \
        f"{field}={bad!r} was accepted"


@pytest.mark.parametrize("field", _PROV_FIELDS)
@pytest.mark.parametrize("bad", WRONG_TYPES)
def test_provenance_field_wrong_type_is_refused(field, bad):
    m = _payload(**{field: bad})
    assert adapt(json.dumps(m), expect_id="e1", expect_user="u") is None, \
        f"provenance.{field}={bad!r} was accepted"


@pytest.mark.parametrize("field", ("origin", "source_id"))
@pytest.mark.parametrize("bad", ("", "x" * 513))
def test_identity_field_bounds_are_enforced(field, bad):
    """The SHIPPED bound: 1..IDENTITY_MAX (scope.py:96, schema.py:134-135)."""
    m = _payload(**{field: bad})
    assert adapt(json.dumps(m), expect_id="e1", expect_user="u") is None, \
        f"provenance.{field} of length {len(bad)} was accepted"


def test_the_reviewers_exact_probe(scope_view):
    """`source_id=[]` — the round-4 F2 reproduction, kept permanently."""
    m = _payload(source_id=[])
    assert adapt(json.dumps(m), expect_id="e1", expect_user="u") is None


def test_ADAPTER_NEVER_PASSES_WHAT_SCOPEVIEW_RAISES_ON(scope_view):
    """THE invariant the finding is really about, asserted directly.

    For every mutation in the campaign: if the adapter accepts, the real
    ScopeView must not raise. Any pair where adapt() succeeds and ScopeView
    raises is exactly the round-4 defect, and this test finds it for the whole
    domain rather than for the cases I happened to choose.
    """
    escaped = []
    for field in _PROV_FIELDS:
        for bad in WRONG_TYPES + ("", "x" * 513):
            m = _payload(**{field: bad})
            a = adapt(json.dumps(m), expect_id="e1", expect_user="u")
            if a is None:
                continue
            try:
                scope_view.visible(a)
            except Exception as exc:
                escaped.append((field, bad, type(exc).__name__))
    assert not escaped, f"adapter passed what ScopeView raises on: {escaped}"


def test_the_nine_surviving_carriers_are_all_clear():
    """Round-4 F3: nine carriers survived a fold that should have removed them.

    Walked as a NAMED LIST, not a sweep — "the full sweep was executed" has been
    false twice in this arc, and a list of nine can be reported honestly.
    """
    assert PC.check_carriers(_spec_text()) == []


def test_the_carrier_walk_can_fail__its_control():
    """Reintroduce one stale carrier; the walk must name it."""
    bad = _spec_text().replace("### 4a-i. `CurrentState`", "### 4a-i. `current_trust`")
    found = PC.check_carriers(bad)
    assert any(f.startswith("C5-") for f in found), \
        f"the carrier walk did not catch a reintroduced carrier: {found}"
