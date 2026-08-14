"""Telemetry must not claim to collect what it never collects.

Four token fields (`distill_in_tok`, `distill_out_tok`, `gate_in_tok`,
`gate_out_tok`) sat in `EVENT_FIELDS` from the start and were populated
**nowhere**, while `CONSENT_TEXT` promised users "token/latency totals". We
gathered less than we said — the safe direction for privacy, but still a claim
the code did not honour, and it survived because nothing checked.

A consent dialog is the one place a mismatch between claim and behaviour is
least acceptable, so the check is mechanical rather than a review habit: it
greps the source for each whitelisted field. That is the same "enumerate, do not
evaluate" discipline that `specs/TEMPLATE.md` §2c requires — a judgement call
here would be answered from the same mental model that wrote the aspirational
field in the first place.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from veracium.telemetry import CONSENT_TEXT, EVENT_FIELDS

SRC = Path(__file__).resolve().parents[1] / "src" / "veracium"

# Fields the recorder itself supplies rather than any call site.
_INTRINSIC: set[str] = set()


def _sources() -> str:
    return "\n".join(p.read_text() for p in SRC.rglob("*.py")
                     if p.name != "telemetry.py")


@pytest.mark.parametrize("event,field", sorted(
    (e, f) for e, fs in EVENT_FIELDS.items() for f in fs))
def test_every_whitelisted_field_is_actually_populated(event, field):
    """A whitelisted field that nothing writes sends nothing — it is a promise,
    not a payload."""
    if field in _INTRINSIC:
        return
    body = _sources()
    assert re.search(rf'["\']{re.escape(field)}["\']', body), (
        f'telemetry whitelists {event}.{field!r} but no call site outside '
        f'telemetry.py ever populates it. Either write it, or remove it from '
        f'EVENT_FIELDS — the whitelist describes what we send, and the consent '
        f'text is built on it.')


def test_consent_text_token_mention_matches_the_payload():
    """specs/0017 I5 — the TWO-SIDED pin (this test replaces the one-sided
    `test_consent_text_does_not_promise_token_totals`, flipped in the same
    commit that populates the fields): "token" appears in CONSENT_TEXT iff
    token fields are whitelisted AND populated. Both directions bite: drop
    the fields and the text must drop the claim; keep the fields and the
    text must state it."""
    whitelisted = {f for fs in EVENT_FIELDS.values() for f in fs}
    token_fields = {f for f in whitelisted if "tok" in f}
    mentions = "token" in CONSENT_TEXT.lower()
    if token_fields:
        body = _sources()
        for f in sorted(token_fields):
            assert re.search(rf'["\']{re.escape(f)}["\']', body), (
                f"{f!r} is whitelisted but no call site populates it — the "
                f"2767a35 regression, resurfacing")
        assert mentions, ("token fields are whitelisted and populated but "
                          "CONSENT_TEXT does not disclose them")
    else:
        assert not mentions, ("CONSENT_TEXT mentions tokens with no "
                              "whitelisted token fields")


def test_the_expected_token_fields_are_exactly_the_0017_eight():
    """specs/0017 §2: the eight fields over the four (role, event) pairs —
    no more, no fewer, at min consent version 3."""
    from veracium.telemetry import FIELD_MIN_VERSION
    token_pairs = {(e, f) for e, fs in EVENT_FIELDS.items()
                   for f in fs if "tok" in f}
    assert token_pairs == {
        ("ingest", "distill_in_tok"), ("ingest", "distill_out_tok"),
        ("answer", "gate_in_tok"), ("answer", "gate_out_tok"),
        ("recall", "compile_in_tok"), ("recall", "compile_out_tok"),
        ("maintain", "compile_in_tok"), ("maintain", "compile_out_tok")}
    for pair in token_pairs:
        assert FIELD_MIN_VERSION.get(pair) == 3, pair


def test_consent_text_claims_map_to_real_fields():
    """Every capability the consent dialog names should be locatable in the
    whitelist, so the text cannot drift ahead of the schema again."""
    whitelisted = {f for fs in EVENT_FIELDS.values() for f in fs}
    claims = {
        "facts extracted": "facts",
        "claims quarantined": "quarantined",
        "answers abstained": "abstained",
        "latency": "ms",
    }
    for phrase, field in claims.items():
        assert field in whitelisted, (
            f"consent text implies {phrase!r} but {field!r} is not whitelisted")
