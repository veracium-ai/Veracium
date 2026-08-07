"""specs/0008 — the confirmation metadata surface (§6b/§6c): closed enums and a
validated `correlation_id`, so the audit record cannot become a content store."""

import pytest

from veracium.schema import (Confirmation, ConfirmationActor, ConfirmationCallPath,
                             CONFIRMATION_RULE_VERSION, validate_correlation_id)
from datetime import datetime, timezone


def test_call_path_and_actor_are_closed_enums():
    assert [c.value for c in ConfirmationCallPath] == ["host_api"]
    assert set(a.value for a in ConfirmationActor) == {"user", "host"}
    with pytest.raises(ValueError):
        ConfirmationCallPath("free text")
    with pytest.raises(ValueError):
        ConfirmationActor("a whole sentence smuggled as an actor label")


@pytest.mark.parametrize("ok", ["abc", "a.b_c:d-e", "x" * 64, "01234567"])
def test_correlation_id_accepts_opaque_keys(ok):
    assert validate_correlation_id(ok) == ok


@pytest.mark.parametrize("bad", ["", "x" * 65, "has space", "emoji😀",
                                 "new\nline", "slash/y"])
def test_correlation_id_rejects_content(bad):
    with pytest.raises(ValueError):
        validate_correlation_id(bad)


def test_rule_version_is_stable_and_stringy():
    assert isinstance(CONFIRMATION_RULE_VERSION, str) and CONFIRMATION_RULE_VERSION


def test_confirmation_record_types_are_enforced():
    rec = Confirmation(id="c1", user_id="u", edge_id="e",
                       confirmed_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                       actor=ConfirmationActor.USER,
                       call_path=ConfirmationCallPath.HOST_API,
                       correlation_id="k1", request_digest="d")
    assert rec.actor is ConfirmationActor.USER
    with pytest.raises(Exception):        # free-text actor rejected by the model
        Confirmation(id="c1", user_id="u", edge_id="e",
                     confirmed_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                     actor="prose", call_path=ConfirmationCallPath.HOST_API,
                     correlation_id="k1", request_digest="d")
