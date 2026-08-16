"""The release-migration orchestrator — accepted `specs/0018`, in production.

Accepted 0016 rules WHAT the D2 deletion means; accepted 0018 rules HOW a
release migration EXECUTES: a total read-only preflight matrix (§4a/§4e), a
host-owned attestation (§4d), a typed mint API with the exact three-mint /
three-resolve retry (§4c), a validating result carrier over the literal §4e
table, a terminal readback with total routing (§4f), and the loud audit
escapes. The operative version numerals are the 0019 rider's: the preflight
passes ONLY resolved base **7** to minting; bases **1–6** return
`unsupported-base` with the two-release ladder diagnostic; already-current
**v8** returns `current`.

The shapes and laws here are PORTED from the reviewed 0013 instrument
(`specs/migrations_0013.py` — `TerminalFacts` ~:860, `MigrationAuthority`
~:642, `MigrationAuditWriteError` ~:375, the outcome vocabulary, the token
grammar, the outcome→states map); production never imports from `specs/`.

DOCUMENTED NARROWINGS of the instrument-level 0013 contract (honest scoping —
facts are still never inferred from labels, 0013 r8-f3):

* **The durable audit trail is a per-store JSON sidecar**
  (`<store>.migration-audit.json`) written by the orchestrator's audit sink —
  an attempted row (inside the kernel transaction, via `migrate_store`'s
  `audit_sink`) and an append-once terminal record per `operation_id` carrying
  the validated `TerminalFacts` septuple. Production has no 0013 two-table
  audit store, no durable authority-consumption table, and therefore no
  instrument-strength replay prevention: the `operation_id` keys the sidecar
  trail, and append-once immutability is what `read_terminal`'s consistency
  rests on.
* **`read_terminal(operation_id, *, audit_path)`** takes the sidecar path as a
  keyword (the instrument reads its single in-process audit store; production
  must locate the store's own trail).
* **Phase classification of kernel failures is coarser than the
  instrument's**: an exception raised inside the delegated `migrate_store`
  maps to `migration-failed` (DB errors) or `internal-error` (defects) with
  tri-state-unknown facts — production lacks the instrument's per-phase
  boundary, and honestly declines to assert the post-failure store state
  (`open_versioned` confirms no rollback to this caller).
* **The kernel lacks the 0013 `new=` seam**: if a raced-empty source is
  created-into by `migrate_store`, the orchestrator records `internal-error`
  WITH the committed facts rather than pretending it did not happen.
* **`PackageConsistencyError` routing evidence** rides as two attributes set
  on the propagating exception instance (`readback_route`,
  `recorded_facts`) — the accepted exception carries no facts of its own and
  the CLI never invents them (§4f/§4g).
* The 0013 §4h vocabulary amendment (`unsupported-base`, `mint-contention`,
  the explicit `TERMINAL_OUTCOMES` split) is realised HERE; the instrument
  file stays historical as-frozen, per its own amendment-header convention.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import NamedTuple, Optional

from . import schema_version as sv

log = logging.getLogger(__name__)

_HEAD = sv.SCHEMA_VERSION            # 8 — the destination this release migrates to
_MINT_BASE = _HEAD - 1               # 7 — the ONLY base the preflight passes to mint
_MAX_UNSUPPORTED = _HEAD - 2         # 6 — unsupported-base carries 1.._MAX_UNSUPPORTED

_BUSY_TIMEOUT_S = 5.0                # preflight/mint connect timeout (tests shrink it)

# --------------------------------------------------------------------------
# the closed outcome vocabulary (ported: instrument §5d + the 0018 §4h amendment)

MIGRATION_FAILURES = ("migration-required", "migration-evidence-missing",
                      "migration-failed", "migration-result-mismatch",
                      "migration-quiescence-required",
                      "migration-source-missing",
                      "migration-audit-unavailable",
                      "migration-audit-state-unknown")
STORE_FAILURES = ("invalid-store", "store-unopenable")
PROTOCOL_FAILURES = ("invalid-request",)
INTERNAL_FAILURES = ("internal-error",)

OUTCOMES = (frozenset({"created", "current", "adopted", "migrated"})
            | sv.REASONS | frozenset(MIGRATION_FAILURES)
            | frozenset(STORE_FAILURES) | frozenset(PROTOCOL_FAILURES)
            | frozenset(INTERNAL_FAILURES))
"""0013's returnable vocabulary (ported verbatim from the instrument)."""

RETURNABLE_OUTCOMES = OUTCOMES | frozenset({"unsupported-base",
                                            "mint-contention"})
"""The 0018 §4h amendment: +2 RETURNABLE members, produced ONLY by the
release orchestrator's preflight/retry machinery before authority minting."""

_AUDIT_ONLY_OUTCOMES = frozenset({"package-inconsistent"})

TERMINAL_OUTCOMES = ((OUTCOMES | _AUDIT_ONLY_OUTCOMES)
                     - frozenset({"unsupported-base", "mint-contention",
                                  "migration-audit-unavailable",
                                  "migration-audit-state-unknown"}))
"""The terminal domain, defined EXPLICITLY (0018 §4h, external R2-4): the
returnable set plus the audit-only `package-inconsistent`, minus the two new
never-terminal members and the two never-terminal audit outcomes (closing the
latent 0013 gap where the audit outcomes passed through the default
mapping)."""

_RESULTING_STATES = frozenset({"source", "destination", "missing",
                               "unaccepted", "unknown"})

_OUTCOME_TERMINAL_STATES = {
    # Ported verbatim from the instrument (round 13 f4; 15 f4; 20 f3; 14 f5).
    "migrated": frozenset({"destination"}),
    "current": frozenset({"destination"}),
    "migration-source-missing": frozenset({"missing", "unaccepted"}),
    "migration-failed": frozenset({"source", "unknown"}),
    "migration-result-mismatch": frozenset({"source", "unknown"}),
    "migration-evidence-missing": frozenset({"source", "unknown"}),
    "migration-quiescence-required": frozenset({"source", "unknown"}),
    "internal-error": frozenset({"destination", "source", "missing",
                                 "unaccepted", "unknown"}),
    "package-inconsistent": frozenset({"destination", "source", "unknown"}),
    "foreign-shape": frozenset({"unaccepted", "unknown"}),
    "newer": frozenset({"unaccepted", "unknown"}),
    "invalid-version": frozenset({"unaccepted", "unknown"}),
    "stamped-shape-mismatch": frozenset({"source", "unaccepted", "unknown"}),
}

_NO_RECORD_OUTCOMES = frozenset({"migration-audit-unavailable",
                                 "migration-audit-state-unknown",
                                 "migration-quiescence-required",
                                 "migration-evidence-missing"})
"""The four no-record outcomes (0018 §4e, external R2-9): a readback `absent`
under exactly these returns the fixed (False, False, unknown, None) row."""

# --------------------------------------------------------------------------
# token grammar and shared validators (ported from the instrument)

_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+:/-]{0,127}$")
_OPERATION_RE = re.compile(
    r"^op-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def backup_token_ok(value) -> bool:
    """Whether `value` is a valid 0013 backup/release token (exact `str`,
    1–128 ASCII, no whitespace) — the CLI's `--backup` gate uses this."""
    return type(value) is str and bool(_TOKEN_RE.fullmatch(value))


def _safe_repr(x) -> str:
    try:
        return repr(x)
    except Exception:
        return f"<unrepresentable {type(x).__name__}>"


def canonical_timestamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def _store_path_problems(sp) -> list:
    """Ported from the instrument (rounds 13–14 corr A/B; 21 corr A)."""
    if type(sp) is not str:
        return [f"must be a string, is {type(sp).__name__}"]
    problems = []
    if "\x00" in sp:
        problems.append("contains an embedded NUL")
    if not os.path.isabs(sp):
        problems.append("must be an absolute (canonical) path")
    try:
        encoded = os.fsencode(sp)
    except (UnicodeEncodeError, ValueError) as exc:
        problems.append(f"is not filesystem-encodable: {_safe_repr(exc)}")
    else:
        if len(encoded) > 4096:
            problems.append("exceeds 4096 bytes")
    return problems


# --------------------------------------------------------------------------
# TerminalFacts — the validated septuple (ported; instrument ~:860)

class _TerminalFactsBase(NamedTuple):
    outcome: str
    from_version: int
    to_version: int
    store_changed: object          # True | False | None (unknown)
    transaction_committed: object  # True | False | None (unknown)
    resulting_state: str
    resulting_version: object      # int | None


class TerminalFacts(_TerminalFactsBase):
    """One validated, immutable terminal-facts value (instrument rounds 13–15,
    ported with the 0018 §4h `TERMINAL_OUTCOMES` gate: the two new returnable
    members AND the two never-terminal audit outcomes REFUSE here)."""
    __slots__ = ()

    def problems(self) -> list:
        p = []
        # types FIRST — `type(x) is str`, never isinstance (hostile subclasses).
        if type(self.outcome) is not str:
            p.append(f"outcome must be a string, is {type(self.outcome).__name__}")
        elif self.outcome not in TERMINAL_OUTCOMES:
            p.append(f"outcome {self.outcome!r} is not a member of "
                     f"TERMINAL_OUTCOMES (0018 §4h: the two returnable-only "
                     f"members and the two never-terminal audit outcomes are "
                     f"excluded)")
        for f, val in (("store_changed", self.store_changed),
                       ("transaction_committed", self.transaction_committed)):
            if val is not None and val is not True and val is not False:
                p.append(f"{f} must be True, False, or None (unknown), not "
                         f"{_safe_repr(val)}")
        for f in ("from_version", "to_version"):
            if type(getattr(self, f)) is not int:
                p.append(f"{f} must be an int")
        if type(self.from_version) is int and type(self.to_version) is int \
                and not (0 <= self.from_version
                         and self.to_version == self.from_version + 1):
            p.append(f"endpoints must be adjacent: to_version "
                     f"{self.to_version} must be from_version "
                     f"{self.from_version} + 1")
        v = self.resulting_version
        if not (v is None or type(v) is int):
            p.append("resulting_version must be int | None")
        if type(self.resulting_state) is not str:
            p.append(f"resulting_state must be a string, is "
                     f"{type(self.resulting_state).__name__}")
            return p
        if self.resulting_state not in _RESULTING_STATES:
            p.append(f"resulting_state {self.resulting_state!r} is not a "
                     f"known state")
            return p
        if p:
            return p
        ch, co, st = self.store_changed, self.transaction_committed, \
            self.resulting_state
        if ch != co:
            p.append("store_changed and transaction_committed must be the same "
                     "tri-state value — a disk change is exactly a commit, and "
                     "neither is known without the other")
        elif ch is None:
            if st != "unknown":
                p.append("unknown change/commit facts require resulting_state "
                         "unknown")
            if v is not None:
                p.append("unknown facts carry a null version")
        elif ch is True:
            if st != "destination":
                p.append("a committed change leaves the store at the "
                         "destination")
            elif v != self.to_version:
                p.append(f"a committed change is at version {self.to_version}")
        else:
            if st == "destination" and v != self.to_version:
                p.append(f"resulting_state destination requires version "
                         f"{self.to_version}")
            elif st == "source" and v != self.from_version:
                p.append(f"resulting_state source requires version "
                         f"{self.from_version}")
            elif st in ("missing", "unaccepted", "unknown") and v is not None:
                p.append(f"resulting_state {st} requires a null version")
        if self.outcome == "migrated" and not (ch is True and co is True):
            p.append("a migrated operation must have changed and committed")
        allowed = _OUTCOME_TERMINAL_STATES.get(self.outcome,
                                               frozenset({"unknown"}))
        if st not in allowed:
            p.append(f"outcome {self.outcome!r} permits resulting_state "
                     f"{sorted(allowed)}, not {st!r}")
        return p


# --------------------------------------------------------------------------
# the loud escapes: audit write (ported; instrument ~:375) and audit read (0018)

class MigrationAuditWriteError(RuntimeError):
    """An audit record could not be written AFTER the operation touched or
    changed the store (0013 §5e, ported). Carries the SAME validated
    `TerminalFacts` the terminal record would have; exact-typed, base-validator
    checked (instrument round 22 f3)."""

    def __init__(self, operation_id: str, store_path: str,
                 facts: "TerminalFacts", *, audit_committed=None,
                 cause: BaseException | None = None):
        if type(facts) is not TerminalFacts:
            raise TypeError("facts must be exactly a TerminalFacts, not a "
                            f"subclass ({type(facts).__name__})")
        problems = TerminalFacts.problems(facts)
        if problems:
            raise ValueError("MigrationAuditWriteError given invalid terminal "
                             "facts: " + "; ".join(problems))
        if not (type(operation_id) is str
                and _OPERATION_RE.fullmatch(operation_id)):
            raise ValueError(f"operation_id {operation_id!r} is not op-<uuid4> "
                             f"(exact str)")
        for pr in _store_path_problems(store_path):
            raise ValueError(f"store_path invalid: {pr}")
        if not (audit_committed is None or type(audit_committed) is bool):
            raise TypeError("audit_committed must be True, False, or None "
                            f"(not {type(audit_committed).__name__})")
        self.operation_id = operation_id
        self.store_path = store_path
        self.facts = facts
        self.audit_committed = audit_committed
        self.committed = facts.transaction_committed
        self.store_changed = facts.store_changed
        self.resulting_state = facts.resulting_state
        self.resulting_version = facts.resulting_version
        vstr = (f"v{facts.resulting_version}"
                if facts.resulting_version is not None
                else facts.resulting_state)
        super().__init__(
            f"audit write failed after the operation ran "
            f"(outcome {facts.outcome!r}, store committed="
            f"{facts.transaction_committed}, audit_committed={audit_committed}, "
            f"operation {operation_id!r}, store {store_path!r}, {vstr}); the "
            f"audit is the record of an irreversible operation and its failure "
            f"is surfaced loudly, never as migration-failed")
        self.__cause__ = cause


class MigrationAuditReadError(RuntimeError):
    """The terminal readback failed to bind a record to this operation (0018
    §4f). Frozen, validated fields; `derived_resulting_state` comes from the
    frozen outcome→states map and the kernel return the orchestrator holds —
    never read from the failed record, never fabricated — and both the message
    and the CLI stderr label it `derived-from-outcome`."""

    def __init__(self, operation_id: str, failure: str, outcome: str, *,
                 cause: BaseException | None = None):
        if not (type(operation_id) is str
                and _OPERATION_RE.fullmatch(operation_id)):
            raise ValueError(f"operation_id {operation_id!r} is not op-<uuid4>")
        if failure not in ("missing", "malformed", "mismatched"):
            raise ValueError(f"failure {failure!r} is not "
                             f"missing|malformed|mismatched")
        if not (type(outcome) is str and outcome in RETURNABLE_OUTCOMES):
            raise ValueError(f"outcome {_safe_repr(outcome)} is not in the "
                             f"closed returnable vocabulary")
        allowed = _OUTCOME_TERMINAL_STATES.get(outcome, frozenset({"unknown"}))
        self.operation_id = operation_id
        self.failure = failure
        self.outcome = outcome
        self.derived_resulting_state = (next(iter(allowed))
                                        if len(allowed) == 1 else "unknown")
        super().__init__(
            f"audit readback {failure} for operation {operation_id!r} under "
            f"kernel outcome {outcome!r}; resulting_state "
            f"{self.derived_resulting_state!r} (derived-from-outcome — from "
            f"the frozen outcome-to-states map, never read from the failed "
            f"record); the audit is the record of the operation and its read "
            f"failure is surfaced loudly")
        self.__cause__ = cause


# --------------------------------------------------------------------------
# ReadbackResult — the closed readback sum carrier (0018 §4f, external R3-4)

_PROBLEM_CAP = 32
_PROBLEM_LEN_CAP = 500


def _cap_problems(entries) -> tuple:
    """Producer-side capping: ≤32 entries of ≤500 chars, an explicit
    `…truncated` final entry when the entry-count cap bites."""
    items = list(entries)
    out = []
    for e in items:
        s = e if type(e) is str else _safe_repr(e)
        if len(s) > _PROBLEM_LEN_CAP:
            s = s[:_PROBLEM_LEN_CAP - 1] + "…"
        out.append(s)
        if len(out) == _PROBLEM_CAP - 1 and len(items) > _PROBLEM_CAP - 1:
            out.append("…truncated")
            break
    return tuple(out)


class _ReadbackResultBase(NamedTuple):
    kind: str
    facts: Optional[TerminalFacts]
    problems: tuple


class ReadbackResult(_ReadbackResultBase):
    """The closed readback sum: {record | absent | malformed}, cross-field
    laws TOTAL and constructor-enforced (0018 I23): a `record` requires
    `type(facts) is TerminalFacts` (EXACT — a subclass's overridden validator
    cannot answer) AND `TerminalFacts.problems(facts)` invoked UNBOUND to be
    empty; `problems` is an exact tuple of exact strs, capped."""
    __slots__ = ()

    def __new__(cls, kind, facts, problems):
        if type(kind) is not str or kind not in ("record", "absent",
                                                 "malformed"):
            raise ValueError(f"kind {_safe_repr(kind)} is not "
                             f"record|absent|malformed")
        if type(problems) is not tuple:
            raise TypeError("problems must be an exact tuple (a list or any "
                            "mutable collection refuses)")
        if len(problems) > _PROBLEM_CAP:
            raise ValueError(f"problems capped at {_PROBLEM_CAP} entries")
        for e in problems:
            if type(e) is not str:
                raise TypeError("every problem entry must be an exact str, "
                                f"not {type(e).__name__}")
            if len(e) > _PROBLEM_LEN_CAP:
                raise ValueError(f"problem entries capped at "
                                 f"{_PROBLEM_LEN_CAP} characters")
        if kind == "record":
            if type(facts) is not TerminalFacts:
                raise TypeError("a record requires facts to be EXACTLY a "
                                f"TerminalFacts ({type(facts).__name__} "
                                f"refused)")
            if TerminalFacts.problems(facts):     # UNBOUND — the base validator
                raise ValueError("a record's facts must pass the base "
                                 "TerminalFacts validator")
            if problems != ():
                raise ValueError("a record carries no problems")
        elif kind == "absent":
            if facts is not None or problems != ():
                raise ValueError("absent requires facts=None and problems=()")
        else:                                     # malformed
            if facts is not None:
                raise ValueError("malformed carries no facts")
            if not problems:
                raise ValueError("malformed requires at least one problem "
                                 "entry")
        return super().__new__(cls, kind, facts, problems)


# --------------------------------------------------------------------------
# the durable sidecar audit trail + read_terminal (the §4h readback amendment)

_AUDIT_SUFFIX = ".migration-audit.json"

_TERMINAL_FIELDS = ("outcome", "from_version", "to_version", "store_changed",
                    "transaction_committed", "resulting_state",
                    "resulting_version")


def audit_trail_path(canonical_store_path: str) -> str:
    return canonical_store_path + _AUDIT_SUFFIX


def _load_audit(apath: str) -> dict:
    if not os.path.exists(apath):
        return {}
    with open(apath, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("audit trail is not a JSON object")
    return data


def _store_audit(apath: str, data: dict) -> None:
    tmp = apath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=True, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, apath)


def _write_attempted(apath: str, operation_id: str, event) -> None:
    """Record the kernel's `migration_attempted` event under this operation id
    (called INSIDE the kernel write transaction — a failure here aborts it)."""
    data = _load_audit(apath)
    entry = data.setdefault(operation_id, {})
    if "attempted" in entry:
        raise RuntimeError(f"append-once: operation {operation_id!r} already "
                           f"has an attempted event")
    entry["attempted"] = {
        "event": event.event, "migration_id": event.migration_id,
        "path": event.path, "from_version": event.from_version,
        "to_version": event.to_version, "occurred_at": event.occurred_at}
    _store_audit(apath, data)


def _write_committed_marker(apath: str, operation_id: str, event) -> None:
    data = _load_audit(apath)
    entry = data.setdefault(operation_id, {})
    entry["committed_event"] = {
        "event": event.event, "migration_id": event.migration_id,
        "occurred_at": event.occurred_at}
    _store_audit(apath, data)


def _write_terminal(apath: str, operation_id: str, facts: TerminalFacts) -> None:
    """Append-once terminal record per operation id — the durable carrier
    `read_terminal` reads back. Validates before writing: the producer never
    writes an impossible record (0013 r8-f3: facts are never inferred)."""
    if type(facts) is not TerminalFacts:
        raise TypeError("terminal facts must be exactly a TerminalFacts")
    problems = TerminalFacts.problems(facts)
    if problems:
        raise ValueError("refusing to write invalid terminal facts: "
                         + "; ".join(problems))
    if not (type(operation_id) is str and _OPERATION_RE.fullmatch(operation_id)):
        raise ValueError(f"operation_id {operation_id!r} is not op-<uuid4>")
    data = _load_audit(apath)
    entry = data.setdefault(operation_id, {})
    if "terminal" in entry:
        raise RuntimeError(f"append-once: operation {operation_id!r} already "
                           f"has a terminal record")
    entry["terminal"] = dict(zip(_TERMINAL_FIELDS, facts))
    entry["terminal"]["occurred_at"] = canonical_timestamp(
        datetime.now(timezone.utc))
    _store_audit(apath, data)


def read_terminal(operation_id, *, audit_path) -> ReadbackResult:
    """One read of this operation's terminal record. RAISES NOTHING (0018
    §4f, external R2-5): every read failure maps to the total `malformed` arm
    (`read-failed: <class>` bounded entries); every raise decision belongs to
    the ORCHESTRATOR. Consistency comes from the sidecar's append-once
    immutability, not connection identity."""
    try:
        if not (type(operation_id) is str
                and _OPERATION_RE.fullmatch(operation_id)):
            return ReadbackResult("malformed", None, _cap_problems(
                [f"read-failed: invalid operation_id "
                 f"{_safe_repr(operation_id)}"]))
        if type(audit_path) is not str:
            return ReadbackResult("malformed", None, _cap_problems(
                [f"read-failed: audit_path must be a str, is "
                 f"{type(audit_path).__name__}"]))
        if not os.path.exists(audit_path):
            return ReadbackResult("absent", None, ())
        try:
            data = _load_audit(audit_path)
        except Exception as exc:
            return ReadbackResult("malformed", None, _cap_problems(
                [f"read-failed: {type(exc).__name__}"]))
        entry = data.get(operation_id)
        if not isinstance(entry, dict) or "terminal" not in entry:
            return ReadbackResult("absent", None, ())
        t = entry["terminal"]
        if not isinstance(t, dict):
            return ReadbackResult("malformed", None, _cap_problems(
                ["terminal record is not a mapping"]))
        try:
            facts = TerminalFacts(*(t.get(f) for f in _TERMINAL_FIELDS))
        except Exception as exc:
            return ReadbackResult("malformed", None, _cap_problems(
                [f"read-failed: {type(exc).__name__}"]))
        problems = TerminalFacts.problems(facts)
        if problems:
            return ReadbackResult("malformed", None, _cap_problems(problems))
        return ReadbackResult("record", facts, ())
    except BaseException as exc:  # noqa: BLE001 — the raise-nothing promise is total
        try:
            return ReadbackResult("malformed", None, _cap_problems(
                [f"read-failed: {type(exc).__name__}"]))
        except BaseException:
            return ReadbackResult("malformed", None, ("read-failed: unknown",))


# --------------------------------------------------------------------------
# MigrationAttestation — the host-owned facts, exact (0018 §4d)

class _MigrationAttestationBase(NamedTuple):
    quiesced: bool
    backup_ref: str


def _attestation_scalar_problems(quiesced, backup_ref) -> list:
    p = []
    if quiesced is not True:
        p.append(f"quiesced must be the bool literal True (checked `is "
                 f"True`), not {_safe_repr(quiesced)}")
    if type(backup_ref) is not str:
        p.append(f"backup_ref must be an exact str, is "
                 f"{type(backup_ref).__name__}")
    elif not _TOKEN_RE.fullmatch(backup_ref):
        p.append(f"backup_ref {_safe_repr(backup_ref)} does not match 0013's "
                 f"token grammar (1-128 ASCII, no whitespace)")
    return p


class MigrationAttestation(_MigrationAttestationBase):
    """Immutable carrier of exactly {`quiesced is True`, `backup_ref` in
    0013's token grammar}. Admission at every consumer is EXACT-TYPE
    (`type(x) is MigrationAttestation`) — subclasses and duck-types are
    REFUSED, never copied. Passed VERBATIM into minting."""
    __slots__ = ()

    def __new__(cls, *, quiesced, backup_ref):
        problems = _attestation_scalar_problems(quiesced, backup_ref)
        if problems:
            raise ValueError("invalid MigrationAttestation: "
                             + "; ".join(problems))
        return super().__new__(cls, quiesced, backup_ref)


def _attestation_problems(att) -> list:
    """Consumer-side revalidation (a `_replace`-forged instance bypasses the
    constructor; the fields are re-checked at every admission)."""
    if type(att) is not MigrationAttestation:
        return [f"must be exactly a MigrationAttestation "
                f"({type(att).__name__} refused — subclasses can intercept "
                f"attribute access)"]
    return _attestation_scalar_problems(tuple.__getitem__(att, 0),
                                        tuple.__getitem__(att, 1))


# --------------------------------------------------------------------------
# the preflight fingerprint (0018 §4b, I22)

_FINGERPRINT_DOMAIN = "0018-preflight-fingerprint-v1"


def _fingerprint_of(user_version: int, objs: dict) -> str:
    """SHA-256 over UTF-8 length-framed segments (8-byte big-endian length
    prefix each): the domain tag, `str(user_version)`, and
    `json.dumps(identity(objs), sort_keys=True, separators=(",", ":"))` —
    `identity()` is 0007's OWN tuple-key-safe canonicalisation
    (schema_version.py:435), and the dumps parameters are byte-identical to
    0007's `digest()`."""
    payload = json.dumps(sv.identity(objs), sort_keys=True,
                         separators=(",", ":"))
    h = hashlib.sha256()
    for seg in (_FINGERPRINT_DOMAIN, str(user_version), payload):
        b = seg.encode("utf-8")
        h.update(len(b).to_bytes(8, "big"))
        h.update(b)
    return h.hexdigest()


def preflight_fingerprint(conn: sqlite3.Connection) -> str:
    """The §4b fingerprint of an open store connection."""
    found = conn.execute("PRAGMA user_version").fetchone()[0]
    return _fingerprint_of(found, sv.manifest(conn))


# --------------------------------------------------------------------------
# PreflightResolution — the evidence carrier (0018 §4b)

class _PreflightResolutionBase(NamedTuple):
    canonical_path: str
    resolved_base: int
    source_fingerprint: str


def _resolution_scalar_problems(canonical_path, resolved_base,
                                source_fingerprint) -> list:
    """EXACT-TYPE every scalar BEFORE any membership, regex, or comparison
    (0018 closure obligation 2 — recursive exactness: `True` is an int
    subclass and refuses; hostile `str` subclasses refuse before their
    methods can run)."""
    p = []
    if type(canonical_path) is not str:
        p.append(f"canonical_path must be an exact str, is "
                 f"{type(canonical_path).__name__}")
    elif not canonical_path:
        p.append("canonical_path must be non-empty")
    if type(resolved_base) is not int:
        p.append(f"resolved_base must be an exact int, is "
                 f"{type(resolved_base).__name__}")
    elif not 1 <= resolved_base <= _MINT_BASE:
        p.append(f"resolved_base {resolved_base} is outside the accepted-base "
                 f"set 1..{_MINT_BASE}")
    if type(source_fingerprint) is not str:
        p.append(f"source_fingerprint must be an exact str, is "
                 f"{type(source_fingerprint).__name__}")
    elif not _DIGEST_RE.fullmatch(source_fingerprint):
        p.append("source_fingerprint must be exactly 64 lowercase hex "
                 "characters")
    return p


class PreflightResolution(_PreflightResolutionBase):
    """Frozen evidence carrier {canonical_path, resolved_base,
    source_fingerprint}; exists only where a store RESOLVED. Consumed by mint
    as REASON-LABELING EVIDENCE ONLY (I18) — never authority-relevant."""
    __slots__ = ()

    def __new__(cls, canonical_path, resolved_base, source_fingerprint):
        problems = _resolution_scalar_problems(canonical_path, resolved_base,
                                               source_fingerprint)
        if problems:
            raise ValueError("invalid PreflightResolution: "
                             + "; ".join(problems))
        return super().__new__(cls, canonical_path, resolved_base,
                               source_fingerprint)


# --------------------------------------------------------------------------
# MigrationResult — the carrier over THE LITERAL §4e table (0018 §4e, I15)

class _MigrationResultBase(NamedTuple):
    outcome: str
    store_changed: object          # Optional[bool]
    transaction_committed: object  # Optional[bool]
    resulting_state: str
    resulting_version: object      # Optional[int]
    diagnostic: str


def _migration_result_problems(outcome, ch, co, state, ver,
                               diagnostic) -> list:
    p = []
    if type(outcome) is not str:
        return [f"outcome must be an exact str, is {type(outcome).__name__}"]
    if type(diagnostic) is not str:
        p.append(f"diagnostic must be an exact str, is "
                 f"{type(diagnostic).__name__}")
    if type(state) is not str:
        p.append(f"resulting_state must be an exact str, is "
                 f"{type(state).__name__}")
    for f, val in (("store_changed", ch), ("transaction_committed", co)):
        if val is not None and val is not True and val is not False:
            p.append(f"{f} must be True, False, or None")
    if not (ver is None or type(ver) is int):
        p.append("resulting_version must be an exact int or None")
    if p:
        return p
    if outcome == "unsupported-base":
        if not (ch is False and co is False and state == "source"
                and type(ver) is int and 1 <= ver <= _MAX_UNSUPPORTED):
            p.append(f"unsupported-base carries exactly (False, False, "
                     f"'source', 1..{_MAX_UNSUPPORTED})")
        return p
    if outcome == "mint-contention" or outcome in ("migration-audit-unavailable",
                                                   "migration-audit-state-unknown"):
        if not (ch is False and co is False and state == "unknown"
                and ver is None):
            p.append(f"{outcome} carries exactly (False, False, 'unknown', "
                     f"None)")
        return p
    if outcome not in OUTCOMES:
        p.append(f"outcome {outcome!r} is not in the returnable vocabulary")
        return p
    # The delegated DEFERENCE law (external R2-2): a carrier is valid iff its
    # seven-field TerminalFacts passes accepted 0013's problems() VERBATIM at
    # this release's endpoints — no 0018-added effect/state/version law.
    p += TerminalFacts.problems(TerminalFacts(outcome, _MINT_BASE, _HEAD, ch,
                                              co, state, ver))
    return p


class MigrationResult(_MigrationResultBase):
    """Frozen result carrier; the validating constructor REJECTS every carrier
    outside the literal §4e table (preflight fixed rows ∪ the four no-record
    rows ∪ the delegated deference domain). Facts are never inferred from the
    label (0013 r8-f3)."""
    __slots__ = ()

    def __new__(cls, outcome, store_changed, transaction_committed,
                resulting_state, resulting_version, diagnostic):
        problems = _migration_result_problems(
            outcome, store_changed, transaction_committed, resulting_state,
            resulting_version, diagnostic)
        if problems:
            raise ValueError("MigrationResult outside the 0018 §4e table: "
                             + "; ".join(problems))
        return super().__new__(cls, outcome, store_changed,
                               transaction_committed, resulting_state,
                               resulting_version, diagnostic)


# --------------------------------------------------------------------------
# MigrationAuthority + the mint API (0018 §4c)

class MigrationAuthority(NamedTuple):
    """The offline-boundary attestation, ported shape-for-shape from the
    instrument (~:642). Production consumption is the sidecar audit trail
    keyed by `operation_id` (documented narrowing in the module docstring)."""
    quiesced: bool
    backup_ref: str
    store_path: str
    from_version: int
    to_version: int
    source_digest: str
    migration_digest: str
    release_ref: str
    operation_id: str
    issued_at: str
    expires_at: str
    evidence_digest: str


_MINT_REASONS = ("source-missing", "source-unaccepted", "source-changed")
_AUTHORITY_VALIDITY = timedelta(minutes=15)


class MintError(Exception):
    """A mint refusal with the closed reason enum {source-missing,
    source-unaccepted, source-changed} (0018 §4c — the test-only
    `make_authority` and its undifferentiated ValueError are not this
    surface)."""

    def __init__(self, reason: str, diagnostic: str | None = None):
        if reason not in _MINT_REASONS:
            raise ValueError(f"{reason!r} is not a closed mint reason")
        self.reason, self.diagnostic = reason, diagnostic
        super().__init__(f"{reason}: {diagnostic or ''}")


class _Unobservable(Exception):
    def __init__(self, kind: str, diagnostic: str):
        self.kind, self.diagnostic = kind, diagnostic
        super().__init__(diagnostic)


def _observe(canonical: str):
    """Read (user_version, manifest) from the store, read-only: BEGIN
    IMMEDIATE, read, ROLLBACK — never create, adopt, or stamp (0018 §4h)."""
    try:
        conn = sqlite3.connect(canonical, timeout=_BUSY_TIMEOUT_S)
    except sqlite3.Error as exc:
        raise _Unobservable("store-unopenable",
                            f"cannot open: {_safe_repr(exc)}") from exc
    try:
        try:
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as exc:
            raise _Unobservable(
                "locked", "another connection holds the write lock; refused "
                          "loudly rather than hanging") from exc
        except sqlite3.DatabaseError as exc:
            raise _Unobservable("invalid-store",
                                f"not readable as a SQLite database: "
                                f"{_safe_repr(exc)}") from exc
        try:
            found = conn.execute("PRAGMA user_version").fetchone()[0]
            objs = sv.manifest(conn)
        except sqlite3.DatabaseError as exc:
            raise _Unobservable("invalid-store",
                                f"failed while being read: "
                                f"{_safe_repr(exc)}") from exc
        finally:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        return found, objs
    finally:
        conn.close()


def _release_ref() -> str:
    try:
        from importlib.metadata import version
        return f"veracium-{version('veracium')}"
    except Exception:
        return "veracium-unreleased"


def _declared_migration_digest() -> str:
    """The digest of this release's declared v7→v8 steps, over the
    instrument's canonical migration encoding (`canonical_migration_bytes`)."""
    payload = (b"veracium-migration-v1:"
               + json.dumps([_MINT_BASE, _HEAD, list(sv.ALTERS_V7_TO_V8)],
                            separators=(",", ":")).encode())
    return hashlib.sha256(payload).hexdigest()


def mint_release_authority(path, attestation, *,
                           resolved) -> MigrationAuthority:
    """The production mint API (0018 §4c). Re-resolves the path ITSELF and
    validates path + attestation against the REAL store on every attempt;
    `resolved` is reason-labeling evidence ONLY (I18) — no check is skipped
    or weakened because of it. At most callers' retry policy applies; this
    function performs exactly one resolve-and-mint."""
    ap = _attestation_problems(attestation)
    if ap:
        raise TypeError("invalid attestation: " + "; ".join(ap))
    if type(resolved) is not PreflightResolution:
        raise TypeError(f"resolved must be exactly a PreflightResolution, is "
                        f"{type(resolved).__name__}")
    rp = _resolution_scalar_problems(
        tuple.__getitem__(resolved, 0), tuple.__getitem__(resolved, 1),
        tuple.__getitem__(resolved, 2))
    if rp:
        raise TypeError("invalid resolution evidence: " + "; ".join(rp))
    if type(path) is not str or _store_path_problems(os.path.realpath(path)):
        raise TypeError(f"path {_safe_repr(path)} is not a usable store path")
    canonical = os.path.realpath(path)
    if not os.path.exists(canonical):
        raise MintError("source-missing", f"nothing at {canonical!r}")
    try:
        found, objs = _observe(canonical)
    except _Unobservable as exc:
        # An unreadable store cannot be confirmed to match the evidence —
        # honestly labeled `source-changed` (the label is the ONLY thing the
        # evidence could have improved; the refusal itself is check-driven).
        raise MintError("source-changed",
                        f"the store could not be re-observed ({exc.kind}): "
                        f"{exc.diagnostic}") from exc
    mintable = (found == _MINT_BASE
                and sv.digest(objs, _MINT_BASE) in sv.accepted_digests(_MINT_BASE))
    if mintable:
        now = datetime.now(timezone.utc)
        return MigrationAuthority(
            quiesced=True,
            backup_ref=tuple.__getitem__(attestation, 1),
            store_path=canonical,
            from_version=_MINT_BASE, to_version=_HEAD,
            source_digest=sv.digest(objs, _MINT_BASE),
            migration_digest=_declared_migration_digest(),
            release_ref=_release_ref(),
            operation_id="op-" + str(uuid.uuid4()),
            issued_at=canonical_timestamp(now),
            expires_at=canonical_timestamp(now + _AUTHORITY_VALIDITY),
            evidence_digest=hashlib.sha256(
                sv.VERSIONS.read_bytes()).hexdigest())
    # Failure labeling ONLY below (I18): the observation refused above; the
    # evidence merely names WHY honestly.
    if _fingerprint_of(found, objs) == tuple.__getitem__(resolved, 2):
        raise MintError(
            "source-unaccepted",
            f"the store at {canonical!r} matches the preflight observation "
            f"but is not an accepted v{_MINT_BASE} migration source "
            f"(user_version={found})")
    raise MintError(
        "source-changed",
        f"the store at {canonical!r} no longer matches the preflight "
        f"observation (user_version={found})")


# --------------------------------------------------------------------------
# the read-only preflight classification (0018 §4a/§4h)

def _intercept(outcome, ch, co, state, ver, diagnostic):
    return ("intercept",
            MigrationResult(outcome, ch, co, state, ver, diagnostic))


def _ladder_diagnostic(base: int) -> str:
    if base <= 5:
        return (f"store resolves to base v{base}, below this release's "
                f"supported migration source (v{_MINT_BASE}): migrate to v6 "
                f"on a ≤0.8.x release, then to v7 on a 0.9.x/0019-era "
                f"release, then run this release's migration")
    return (f"store resolves to base v6, below this release's supported "
            f"migration source (v{_MINT_BASE}): migrate to v7 on a 0019-era "
            f"release first")


def _preflight_classify(path: str):
    """The READ-ONLY resolution pass (0018 §4h): never creates, never adopts,
    never stamps. Returns ("intercept", MigrationResult) for every cell except
    resolved base 7 → ("mint", PreflightResolution) and current-with-drift →
    ("repair", canonical_path). Reuses 0007's own classification machinery
    (accepted digests, legacy-base resolution, the runtime gate)."""
    canonical = os.path.realpath(path)
    if not os.path.exists(canonical):
        return _intercept("migration-source-missing", False, False, "missing",
                          None, f"nothing at {canonical!r}")
    if not sv.runtime_supported():
        return _intercept("unsupported-sqlite", False, False, "unknown", None,
                          f"sqlite {sqlite3.sqlite_version} is not a "
                          f"qualified runtime build identity")
    try:
        found, objs = _observe(canonical)
    except _Unobservable as exc:
        return _intercept(exc.kind, False, False, "unknown", None,
                          exc.diagnostic)
    fingerprint = _fingerprint_of(found, objs)
    if found < 0:
        return _intercept("invalid-version", False, False, "unaccepted", None,
                          f"user_version {found} is invalid")
    if found > _HEAD:
        return _intercept("newer", False, False, "unaccepted", None,
                          f"store is stamped v{found}, this build is "
                          f"v{_HEAD}; install a build whose SCHEMA_VERSION "
                          f"covers the store")
    if found == _HEAD:
        if sv.digest(objs, _HEAD) not in sv.accepted_digests(_HEAD):
            return _intercept("stamped-shape-mismatch", False, False,
                              "unaccepted", None,
                              f"stamped v{_HEAD} but the shape is not in the "
                              f"accepted manifest set")
        if sv.drift(objs, _HEAD):
            return ("repair", canonical)
        return _intercept("current", False, False, "destination", _HEAD,
                          f"already at v{_HEAD}; nothing to migrate")
    if found == 0:
        if not objs:
            return _intercept(
                "migration-source-missing", False, False, "unaccepted", None,
                "a valid, empty, user_version=0 database with no objects is "
                "not a migration source (never created-into, never adopted)")
        base = sv.resolve(objs, sv.version_records(),
                          candidates=sv.legacy_base_versions())
        if base is None:
            return _intercept("foreign-shape", False, False, "unaccepted",
                              None, "unstamped store matches no evidenced "
                                    "legacy base")
        # a legitimate unstamped store resolves WITHOUT being stamped (§4h)
    else:
        # stamped 0 < found < head: accepted at its own version, or refused
        if sv.digest(objs, found) not in sv.accepted_digests(found):
            return _intercept("stamped-shape-mismatch", False, False,
                              "unaccepted", None,
                              f"stamped v{found} but the shape is not in "
                              f"v{found}'s accepted manifest set")
        base = found
    if base == _MINT_BASE:
        return ("mint", PreflightResolution(canonical, _MINT_BASE,
                                            fingerprint))
    return _intercept("unsupported-base", False, False, "source", base,
                      _ladder_diagnostic(base))


def _repair_current(canonical: str) -> MigrationResult:
    """The ONE preflight cell that commits (external R1-7): rebuildable drift
    at v8 is repaired through 0007's own repair-during-opening path — the one
    shared opener, never a second repairer — and reported honestly from the
    OpenResult's structured fields."""
    conn = sqlite3.connect(canonical, timeout=_BUSY_TIMEOUT_S)
    try:
        result = sv.open_versioned(conn, canonical)
    except sv.StoreVersionError as exc:
        return _reason_intercept(exc)
    finally:
        conn.close()
    return MigrationResult(
        "current", result.store_changed, result.transaction_committed,
        "destination", result.resulting_version,
        "already at the destination; rebuildable drift repaired during "
        "opening (0007 §4a-iii)" if result.store_changed
        else "already at the destination")


def _reason_intercept(exc: "sv.StoreVersionError") -> MigrationResult:
    state = ("unaccepted" if exc.reason in ("foreign-shape", "newer",
                                            "invalid-version",
                                            "stamped-shape-mismatch")
             else "unknown")
    return MigrationResult(exc.reason, False, False, state, None, str(exc))


# --------------------------------------------------------------------------
# the delegated path (0018 §4e/§4f)

class _AuditSinkWriteFailed(Exception):
    """The attempted-record write failed INSIDE the kernel transaction — the
    kernel rolls back; nothing is consumed (→ `migration-audit-unavailable`)."""


def _make_sink(apath: str, operation_id: str):
    def sink(event):
        if getattr(event, "event", None) == "migration_attempted":
            try:
                _write_attempted(apath, operation_id, event)
            except Exception as exc:
                raise _AuditSinkWriteFailed(_safe_repr(exc)) from exc
        else:
            # best-effort committed marker; the TERMINAL record (written by
            # the orchestrator from the kernel's actual outcome) is the
            # authoritative durable carrier — this marker must never convert
            # a committed migration into a post-commit escape.
            try:
                _write_committed_marker(apath, operation_id, event)
            except Exception:
                log.warning("committed-event marker write failed for %s",
                            operation_id)
    return sink


_NO_RECORD_DIAGNOSTICS = {
    "migration-audit-unavailable":
        "the attempted audit record is proven not written; the kernel "
        "transaction rolled back and nothing was consumed — safe to retry",
    "migration-audit-state-unknown":
        "the attempted-record write neither confirmed nor disproved — the "
        "authority MAY be consumed; query the durable operation_id before "
        "retrying (a retry is NOT safe until then)",
    "migration-quiescence-required":
        "refused before observation; no record exists for this operation",
    "migration-evidence-missing":
        "refused before observation; no record exists for this operation",
}


def _kernel_call(canonical: str, apath: str, operation_id: str):
    """Run the delegated kernel operation and derive (outcome, facts,
    diagnostic) from what ACTUALLY happened — never from a label alone.
    Returns facts=None only for the no-record outcomes."""
    from .migration import DuplicateOutcomeChainError, migrate_store
    try:
        r = migrate_store(canonical, audit_sink=_make_sink(apath,
                                                           operation_id))
    except _AuditSinkWriteFailed as exc:
        return ("migration-audit-unavailable", None,
                f"attempted-record write failed: {exc}")
    except sv.StoreVersionError as exc:
        state = ("unaccepted" if exc.reason in ("foreign-shape", "newer",
                                                "invalid-version",
                                                "stamped-shape-mismatch")
                 else "unknown")
        return (exc.reason,
                TerminalFacts(exc.reason, _MINT_BASE, _HEAD, False, False,
                              state, None),
                str(exc))
    except sv.PostCommitAuditError as exc:
        # the store IS migrated (committed=True by contract); the terminal
        # record below is the authoritative trail.
        return ("migrated",
                TerminalFacts("migrated", _MINT_BASE, _HEAD, True, True,
                              "destination", _HEAD),
                f"migrated; the committed-event marker failed afterwards "
                f"({_safe_repr(exc)})")
    except sv.PackageConsistencyError:
        raise                                     # §4f: the named escape
    except DuplicateOutcomeChainError as exc:
        return ("migration-failed",
                TerminalFacts("migration-failed", _MINT_BASE, _HEAD, None,
                              None, "unknown", None),
                _safe_repr(exc))
    except sqlite3.DatabaseError as exc:
        return ("migration-failed",
                TerminalFacts("migration-failed", _MINT_BASE, _HEAD, None,
                              None, "unknown", None),
                f"the kernel operation failed ({_safe_repr(exc)}); the "
                f"post-failure store state is unknown (rollback unconfirmed)")
    except Exception as exc:                      # noqa: BLE001 — total boundary
        return ("internal-error",
                TerminalFacts("internal-error", _MINT_BASE, _HEAD, None, None,
                              "unknown", None),
                f"library defect in the delegated operation: "
                f"{type(exc).__name__}: {_safe_repr(exc)}")
    # -- returned a result: exact-type and validate before trusting it -------
    if type(r) is not sv.OpenResult \
            or type(r.store_changed) is not bool \
            or type(r.transaction_committed) is not bool \
            or type(r.resulting_version) is not int:
        return ("internal-error",
                TerminalFacts("internal-error", _MINT_BASE, _HEAD, None, None,
                              "unknown", None),
                f"the kernel returned a malformed result: {_safe_repr(r)}")
    label = str.__str__(r)
    if label == "migrated" and r.store_changed is True \
            and r.transaction_committed is True \
            and r.resulting_version == _HEAD:
        return ("migrated",
                TerminalFacts("migrated", _MINT_BASE, _HEAD, True, True,
                              "destination", _HEAD),
                f"migrated v{_MINT_BASE} -> v{_HEAD}")
    if label == "current" and r.store_changed == r.transaction_committed \
            and r.resulting_version == _HEAD:
        return ("current",
                TerminalFacts("current", _MINT_BASE, _HEAD, r.store_changed,
                              r.transaction_committed, "destination", _HEAD),
                "the store was already at the destination when the delegated "
                "operation ran (a concurrent operation migrated it)")
    if label in ("created", "adopted") and r.store_changed is True \
            and r.transaction_committed is True \
            and r.resulting_version == _HEAD:
        # the kernel lacks 0013's new= seam (documented narrowing): a dedicated
        # migration must never create/adopt — recorded honestly as a defect
        # WITH the committed facts, never hidden.
        return ("internal-error",
                TerminalFacts("internal-error", _MINT_BASE, _HEAD, True, True,
                              "destination", _HEAD),
                f"the delegated operation returned {label!r} — a dedicated "
                f"migration must never {label} a store (0013 §5b); the "
                f"committed facts are recorded")
    return ("internal-error",
            TerminalFacts("internal-error", _MINT_BASE, _HEAD, None, None,
                          "unknown", None),
            f"the kernel returned an impossible cell: {label!r}/"
            f"{r.store_changed}/{r.transaction_committed}/"
            f"v{r.resulting_version}")


def _route_delegated(operation_id: str, kernel_outcome: str, apath: str,
                     diagnostic: str) -> MigrationResult:
    """§4f's routing, total over every delegated return. Facts come from the
    RECORD verbatim (the deference law) — never from the kernel label."""
    try:
        rb = read_terminal(operation_id, audit_path=apath)
    except BaseException as exc:  # noqa: BLE001 — read_terminal promises not to
        raise MigrationAuditReadError(operation_id, "malformed",
                                      kernel_outcome, cause=exc) from exc
    if type(rb) is not ReadbackResult:
        raise MigrationAuditReadError(operation_id, "malformed",
                                      kernel_outcome)
    if rb.kind == "record":
        facts = rb.facts
        if facts.outcome == kernel_outcome:
            return MigrationResult(
                kernel_outcome, facts.store_changed,
                facts.transaction_committed, facts.resulting_state,
                facts.resulting_version,
                f"{diagnostic} [facts from the terminal record for operation "
                f"{operation_id} (recorded)]")
        raise MigrationAuditReadError(operation_id, "mismatched",
                                      kernel_outcome)
    if rb.kind == "absent":
        if kernel_outcome in _NO_RECORD_OUTCOMES:
            return MigrationResult(
                kernel_outcome, False, False, "unknown", None,
                f"{diagnostic} [{_NO_RECORD_DIAGNOSTICS[kernel_outcome]}]")
        raise MigrationAuditReadError(operation_id, "missing", kernel_outcome)
    raise MigrationAuditReadError(operation_id, "malformed", kernel_outcome)


def _delegate(canonical: str, authority: MigrationAuthority) -> MigrationResult:
    operation_id = authority.operation_id
    apath = audit_trail_path(canonical)
    try:
        kernel_outcome, facts, diagnostic = _kernel_call(canonical, apath,
                                                         operation_id)
    except sv.PackageConsistencyError as exc:
        _package_escape_post_mint(exc, operation_id, apath)
        raise
    if facts is not None:
        try:
            _write_terminal(apath, operation_id, facts)
        except Exception as exc:
            raise MigrationAuditWriteError(operation_id, canonical, facts,
                                           audit_committed=False,
                                           cause=exc) from exc
    return _route_delegated(operation_id, kernel_outcome, apath, diagnostic)


def _package_escape_post_mint(exc, operation_id: str, apath: str) -> None:
    """The POST-MINT package route (external R3-5): terminal-record the
    consumed operation as `package-inconsistent` (best-effort — the escape
    must propagate regardless), run the escape-path readback, and attach the
    routing evidence to the exception (`readback_route`, `recorded_facts`).
    The record is accepted as a fact source ONLY when valid AND bound to
    `package-inconsistent`."""
    facts = TerminalFacts("package-inconsistent", _MINT_BASE, _HEAD, None,
                          None, "unknown", None)
    try:
        _write_terminal(apath, operation_id, facts)
    except Exception:
        pass
    try:
        rb = read_terminal(operation_id, audit_path=apath)
    except BaseException:  # noqa: BLE001
        rb = None
    exc.recorded_facts = None
    if rb is None or type(rb) is not ReadbackResult or rb.kind == "malformed":
        exc.readback_route = "malformed"
    elif rb.kind == "absent":
        exc.readback_route = "missing"
    elif rb.facts.outcome == "package-inconsistent":
        exc.readback_route = "recorded"
        exc.recorded_facts = rb.facts
    else:
        exc.readback_route = "mismatched"


# --------------------------------------------------------------------------
# run_release_migration — the orchestrator (0018 §4a)

def _invalid_request(diagnostic: str) -> MigrationResult:
    return MigrationResult("invalid-request", False, False, "unknown", None,
                           diagnostic)


def _classify_or_intercept(path: str):
    """One preflight classification, with the repair cell executed. Returns
    ("intercept", MigrationResult) or ("mint", PreflightResolution).
    PackageConsistencyError propagates (the PRE-MINT route: no operation
    minted, no readback attempted)."""
    kind, payload = _preflight_classify(path)
    if kind == "repair":
        return "intercept", _repair_current(payload)
    return kind, payload


def run_release_migration(path, *, host_attestation) -> MigrationResult:
    """The release-migration orchestrator (0018 §4): total over every input
    per the §4e matrix; every preflight interception zero-authority and
    zero-audit; resolved base 7 ALONE mints and delegates to the audited
    kernel operation."""
    ap = _attestation_problems(host_attestation)
    if ap:
        return _invalid_request("host_attestation refused: " + "; ".join(ap))
    if type(path) is not str or not path or "\x00" in path \
            or len(os.fsencode(path)) > 4096:
        return _invalid_request(f"path {_safe_repr(path)} is not a usable "
                                f"store path")
    try:
        kind, payload = _classify_or_intercept(path)
    except sv.PackageConsistencyError:
        raise                                     # pre-mint: propagates bare
    except (MigrationAuditWriteError, MigrationAuditReadError):
        raise
    except Exception as exc:                      # noqa: BLE001 — total boundary
        return MigrationResult("internal-error", None, None, "unknown", None,
                               f"preflight defect: {type(exc).__name__}: "
                               f"{_safe_repr(exc)}")
    if kind == "intercept":
        return payload
    resolved = payload
    canonical = resolved.canonical_path
    # -- the EXACT §4c retry: at most THREE mint calls, re-resolution after
    # -- failures one and two ONLY, the third error → mint-contention.
    reasons = []
    while True:
        try:
            authority = mint_release_authority(canonical, host_attestation,
                                               resolved=resolved)
            break
        except MintError as exc:
            reasons.append(exc.reason)
            if len(reasons) == 3:
                return MigrationResult(
                    "mint-contention", False, False, "unknown", None,
                    f"three mint attempts failed ({', '.join(reasons)}); a "
                    f"concurrent operation is racing this one and contention "
                    f"persisted three rounds — nothing was minted, nothing "
                    f"written; retry after the race settles")
        except Exception as exc:                  # noqa: BLE001
            return MigrationResult("internal-error", None, None, "unknown",
                                   None, f"mint defect: {type(exc).__name__}: "
                                         f"{_safe_repr(exc)}")
        try:
            kind, payload = _classify_or_intercept(canonical)
        except sv.PackageConsistencyError:
            raise
        except Exception as exc:                  # noqa: BLE001
            return MigrationResult("internal-error", None, None, "unknown",
                                   None, f"re-resolution defect: "
                                         f"{type(exc).__name__}: "
                                         f"{_safe_repr(exc)}")
        if kind == "intercept":
            return payload                        # the now-true outcome
        resolved = payload
    return _delegate(canonical, authority)
