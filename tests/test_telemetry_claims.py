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


def test_consent_text_does_not_promise_token_totals():
    """The specific regression: we asked users to consent to sending token
    totals we never collected."""
    assert "token" not in CONSENT_TEXT.lower(), (
        "CONSENT_TEXT mentions tokens. Only claim this once token fields are "
        "in EVENT_FIELDS *and* populated — see veracium.llm.metered.")


def test_no_token_fields_are_whitelisted_yet():
    """Guards the pairing: the consent text and the whitelist must move
    together, in that order."""
    whitelisted = {f for fs in EVENT_FIELDS.values() for f in fs}
    leaked = {f for f in whitelisted if "tok" in f}
    assert not leaked, (
        f"{sorted(leaked)} whitelisted without a populating call site. Re-add "
        f"token fields only alongside the code that fills them.")


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
