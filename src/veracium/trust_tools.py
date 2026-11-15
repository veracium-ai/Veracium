"""specs/0031 §4f (amendment `0031/trust-tools-direct`): the trust tools' shared vocabulary.

The closed refusal reasons the seven agent tools serialize (§4a), and `TrustRefused`, the one exception the library
verbs raise for the scope gates of §3b. A refusal is a VALUE: the tools return it as
`{"ok": false, "refusal": <reason>, "detail": <=200 chars>}` and never raise it to the transport (INV-TT11).
"""
from __future__ import annotations

#: §4a's refusal vocabulary, closed. The order is the gate order of §4a where a gate owns the reason.
REFUSALS = (
    "attempted_elevation",     # 1. capability: anything but `direct`
    "erasure_disabled",        # 2. the erasure switch (the three forget tools)
    "principal_scoped",        # 3. the whole-user erase under any principal
    "invalid_target",          # 4. input: exactly one of edge_id / episode_id
    "reason_too_long",         # 4. input: dispute's reason over 1,024 code points
    "preview_unknown",         # 4. / §4e: a token that does not parse, or is not this issuer's
    "scope_unconfigured",      # 5. a principal with no scope policy configured
    "principal_ungroupable",   # 5. a principal with no source_id
    "source_unbound",          # 6. a writing verb under a principal whose binding has no source
    "source_out_of_scope",     # 6. a binding source the principal's view does not class OWN
    "not_found_in_scope",      # 7. CROSS_HIDDEN, UNRESOLVED, another user's id, an unknown id: one response
    "out_of_scope",            # 7. SHARED or CROSS_VISIBLE under a principal
    "correction_refused",      # 8. CorrectionRefused: a COMMITTED refusal (TT-R2-02)
    "preview_expired",         # §4e step 3
    "store_changed",           # §4e step 4
    "refused",                 # 8. any other library refusal (ValueError, TypeError, ScopeError)
)

#: the detail every `not_found_in_scope` carries, fixed so the response is identical across the four cases it
#: covers and is no existence oracle (§3b, INV-TT7, INV-TT16)
NOT_FOUND_DETAIL = "no such record in this scope"
OUT_OF_SCOPE_DETAIL = "this record is visible here but not yours to change"

_DETAILS = {
    "scope_unconfigured": "a principal was supplied but no scope policy is configured",
    "principal_ungroupable": "a principal must carry a source_id",
    "source_unbound": "this binding has no source, so a write under a principal could not be scoped",
    "source_out_of_scope": "this binding's source is not in the principal's own scope",
    "not_found_in_scope": NOT_FOUND_DETAIL,
    "out_of_scope": OUT_OF_SCOPE_DETAIL,
}


class TrustRefused(ValueError):
    """A §3b scope refusal raised by a library verb under a principal, BEFORE anything is written. `reason` is one
    of `REFUSALS`; the detail is fixed per reason, so no refusal carries record content or an existence signal."""

    def __init__(self, reason: str):
        if reason not in REFUSALS:
            raise ValueError(f"unknown trust refusal {reason!r}")
        self.reason = reason
        self.detail = _DETAILS.get(reason, reason)
        super().__init__(f"{reason}: {self.detail}")
