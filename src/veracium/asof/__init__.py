"""specs/0030 — time-relative classification: `classify_as_of` over 0029's
transaction-time carrier. Pure consumers live here (the classifier, the raw
adapter, the carrier types); the store-side derivation of `CurrentState`
lives in `veracium.store.current_state` because it reads the connection.

Not wired into recall: 0028 v2 owns `as_of=` on the recall API; this package
is the primitive it will call. `Edge.assertable` is untouched (V-ADDITIVE,
V-CURRENT-UNCHANGED).
"""
from .adapter import Adapted, AdaptedProvenance, adapt
from .carrier import CurrentState, Envelope, RestrictionVerdict, ScopeCell
from .classify import (EXCLUDED, FENCED_AS_OF, GROUNDED_AS_OF, IDENTITY_UNBOUND,
                       MALFORMED, NOT_VALID_AT_T, SCOPE_HIDDEN, STALE_AT_RECALL,
                       STATUSES, Result, assertable_as_of, classify_as_of)

__all__ = [
    "Adapted", "AdaptedProvenance", "adapt",
    "CurrentState", "Envelope", "RestrictionVerdict", "ScopeCell",
    "Result", "classify_as_of", "assertable_as_of", "STATUSES", "STALE_AT_RECALL",
    "IDENTITY_UNBOUND", "SCOPE_HIDDEN", "MALFORMED", "NOT_VALID_AT_T",
    "EXCLUDED", "FENCED_AS_OF", "GROUNDED_AS_OF",
]
