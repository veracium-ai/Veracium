"""specs/0030 — time-relative classification: `classify_as_of` over 0029's
transaction-time carrier. Pure consumers live here (the classifier, the raw
adapter, the carrier types); the store-side derivation of `CurrentState`
lives in `veracium.store.current_state` because it reads the connection.

specs/0028 v2 wires it: `resolve` is the §4a resolution over this classifier
(`Memory.facts_valid_at`, `Memory.recall(as_of=)` via `recall.recall_at`).
`Edge.assertable` is untouched (V-ADDITIVE, V-CURRENT-UNCHANGED) and the
as-of branch never consults it (0028 V-ONE-CLOCK).
"""
from .adapter import Adapted, AdaptedProvenance, adapt
from .carrier import CurrentState, Envelope, RestrictionVerdict, ScopeCell
from .classify import (EXCLUDED, FENCED_AS_OF, GROUNDED_AS_OF, IDENTITY_UNBOUND,
                       MALFORMED, NOT_VALID_AT_T, SCOPE_HIDDEN, STALE_AT_RECALL,
                       STATUSES, Result, assertable_as_of, classify_as_of)
from .resolve import (FENCED_SELF, GROUNDED_OUTCOMES, HOP_BOUND, INDETERMINATE,
                      NOT_RETURNABLE, OUTCOMES, POINTER_TO, RESOLUTION,
                      RETURN_SELF, RETURN_SELF_FLAGGED, AsOfAnswer, AsOfFact,
                      FutureAsOfRefused, Pointer, Resolution, resolve_as_of)

__all__ = [
    "Adapted", "AdaptedProvenance", "adapt",
    "CurrentState", "Envelope", "RestrictionVerdict", "ScopeCell",
    "Result", "classify_as_of", "assertable_as_of", "STATUSES", "STALE_AT_RECALL",
    "IDENTITY_UNBOUND", "SCOPE_HIDDEN", "MALFORMED", "NOT_VALID_AT_T",
    "EXCLUDED", "FENCED_AS_OF", "GROUNDED_AS_OF",
    "FutureAsOfRefused", "resolve_as_of", "AsOfAnswer", "AsOfFact", "Resolution",
    "Pointer", "RESOLUTION", "OUTCOMES", "GROUNDED_OUTCOMES", "HOP_BOUND",
    "RETURN_SELF", "RETURN_SELF_FLAGGED", "FENCED_SELF", "NOT_RETURNABLE",
    "INDETERMINATE", "POINTER_TO",
]
