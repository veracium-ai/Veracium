"""Embedded SQLite store — the zero-dependency default.

Everything (edges, episodes, compiled-view cache, per-user write counter) lives
in one SQLite file. Per-user graphs are small (the research saw ~120 edges at
9 weeks of history), so a single indexed table per kind is ample; a Neo4j/
Postgres `Store` can replace this for very large multi-tenant deployments.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from ..authority import DRAFTED_RULE_VERSIONS, RULE_VERSION, scope_fingerprint
from .. import redaction as _redaction
from ..attestation import declarative_grounding
from ..schema import (ConsolidationOp, ConsolidationOutputDraft, ConsolidationState,
                      Confirmation, ConfirmationActor, ConfirmationCallPath, REPLY_KINDS, Reply, ReplyActor,
                      reply_request_digest,
                      Disclosure, Edge, Episode, EvidenceAuthor, OutcomeJudgmentDraft, QUARANTINE_RELATION,
                      Provenance, RECOVERY_PENDING_STATES,
                      SupersessionPlan, SupersessionRefusal, SupersessionResult,
                      is_historical_id, to_historical_id,
                      DISPOSITIONED_REASONS, as_utc_required, assertion_view, wiki_drops_on)
from .base import (CutoffDomainError, EdgeEvent, PreEpochQuery, RawEdgeState, REINSTATEMENT_REASONS, ReplyRefused,
                   RequestRedacted, UnknownEdge,
                   DESTINATION_CHANGED, HEAD_MOVED, LEASE_MAX, NON_QUIESCENT,
                   PLAN_STALE, ReceiptSchemaBoundaryError, Store,
                   SupersessionIntegrityError)
from . import lifetime as _lifetime
from .edge_events import (append_event, mint_recorded_at, next_seq,  # noqa: F401
                          next_txn)
from .schema_version import (SCHEMA_V1, SCHEMA_VERSION, SCHEMAS,  # noqa: F401
                             PostCommitAuditError,
                             StoreVersionError, open_versioned)
from ..census import declare_site

# specs/0042 (tranche 5): the enforcement points of this module, each a declared site the
# decision is returned THROUGH — consult() brackets the decision, fire() wraps the value
_SITE_JOURNAL_REASON = declare_site("store.journal.reason-not-dispositioned")
# specs/0041 tranche 1: INV-11's MIRROR and the two closures the redaction spec found missing (§2d-v)
_SITE_UPSERT_MARKER = declare_site("store.upsert.marker-introduced")
_SITE_UPSERT_RELATION_ONLY_QUARANTINE = declare_site("store.upsert.relation-only-quarantine")
_SITE_EPISODE_MARKER = declare_site("store.episode.marker-introduced")
_SITE_EPISODE_KIND = declare_site("store.episode.kind-not-recognised")
_SITE_IMPORT_EPISODE_KIND = declare_site("store.import.episode-kind-not-recognised")
# specs/0041 tranche 3: the operation's refusals (INV-5 scope; the reason vocabulary; 0010 X21 on a claimed input;
# §4h(i)'s derived-disposition rule) and INV-11 keyed on the ATTESTATION record at the two whole-record writers
_SITE_REDACT_TARGET = declare_site("store.redact.target")
_SITE_REDACT_BOTH_OR_NEITHER = declare_site("store.redact.both-or-neither")   # §4a: exactly one target (its own id, 2026-09-20)
_SITE_REDACT_REASON = declare_site("store.redact.reason-not-registered")
_SITE_REDACT_CLAIMED = declare_site("store.redact.input-claimed")
_SITE_REDACT_DISPOSITION = declare_site("store.redact.disposition-changed")
_SITE_REDACT_NOTHING = declare_site("store.redact.nothing-to-redact")   # round 11: the owner's "Refuse: nothing to redact"
_SITE_UPSERT_ATTESTED = declare_site("store.upsert.attested-redaction")
_SITE_EPISODE_ATTESTED = declare_site("store.episode.attested-redaction")
_SITE_CONSOLIDATION_INPUT_REDACTED = declare_site("store.consolidation.input-redacted")
_SITE_IMPORT_NOTICE_CONFLICT = declare_site("store.import.notice-body-conflict")
# specs/0041 §11.6.6 (T4): a notice's state moves only through ONE writer, which validates the closed values (no DDL
# CHECK); and the host verb that applies a PENDING notice refuses an unknown id, a standing row, an absent target
_SITE_NOTICE_STATE = declare_site("store.notice.state-domain")
_SITE_CONFIRM_NOTICE_UNKNOWN = declare_site("store.confirm-notice.unknown")
_SITE_CONFIRM_NOTICE_STANDING = declare_site("store.confirm-notice.standing")
_SITE_CONFIRM_NOTICE_INERT = declare_site("store.confirm-notice.target-absent")
# ... and a file pairing a notice with its record UNREDACTED refuses whole (the owner's ruling): applying the notice could
# destroy the user's own fact (a hostile notice), skipping it would land content a source says it redacted (a stale copy)
_SITE_IMPORT_NOTICE_UNSHOWN = declare_site("store.import.notice-record-unredacted")
# specs/0041 §11.6.6 (T4): only an APPLIED row attests (a redaction this store made, or a notice it applied as its
# own total treatment); PENDING and STANDING rows hold a foreign body and attest nothing. Until v16 the state was
# derived (`event_ref IS NULL AND source_origin IS NOT NULL` read as standing); v16 stores it.
_APPLIED_SQL = "(state = 'applied')"
# `_attested_fields`'s by-ID key: add_episode's INV-11 refusal, whoever redacted the record (RII-R3-01, N1).
_ANY_OWNER = object()
_SITE_UPSERT_INVALIDATION_REASON = declare_site("store.upsert.invalidation-reason-not-registered")
_SITE_EPISODE_RETIRED_REASON = declare_site("store.episode.retired-reason-not-registered")
_SITE_IMPORT_REASON = declare_site("store.import.reason-not-registered")
_SITE_REDACTED_REASON = declare_site("store.redacted-reason.not-a-redaction")
_SITE_JOURNAL_REDACTION_REASON = declare_site("store.journal.redaction-reason")
_SITE_JOURNAL_REINSTATEMENT_REASON = declare_site("store.journal.reinstatement-reason")   # specs/0029 v12 §4b-i
_SITE_IMPORT_ATTESTED = declare_site("store.import.attested-redaction")     # tranche 4b: INV-11 at the import boundary
_SITE_READ_OUTPUT_NOT_VISIBLE = declare_site("store.read.output-not-visible", declines=False)
_SITE_READ_INPUT_CLAIMED = declare_site("store.read.input-claimed", declines=False)
_SITE_UPSERT_IMMUTABLE = declare_site("store.upsert.immutable")
_SITE_FLATTENING = declare_site("store.flattening")
_SITE_CONSOLIDATION_CONTRIBUTION = declare_site("store.consolidation-contribution")
_SITE_CONTRIBUTION = declare_site("store.contribution")
_SITE_TXN_LOCKED = declare_site("store.txn.locked")
_SITE_TXN_LOCKED_RETRY = declare_site("store.txn.locked-retry")
_SITE_ABANDON_LIVE_LEASE = declare_site("store.consolidation.abandon-live-lease")
_SITE_ADD_EPISODE = declare_site("store.add-episode")
_SITE_ADD_EPISODE_OWNER = declare_site("store.add-episode.owner")      # 0004 v3.5 §2c (i): the persisted owner
_SITE_OUTCOME_CONTEXT_REF = declare_site("store.outcome.context-ref")
_SITE_SUPERSESSION_INTEGRITY = declare_site("store.supersession.integrity")
_SITE_CORRECTION_AUTHORISATION = declare_site("store.correction.authorisation")
_SITE_SUPERSESSION_PLAN = declare_site("store.supersession.plan")
_SITE_IMPORT_PLAN = declare_site("store.import-plan")
_SITE_IMPORT_RESERVED = declare_site("store.import.reserved-id")      # 0010 X21 at the import (0004 v3.5 §2c (ii))
_SITE_CONFIRM_UNKNOWN_EDGE = declare_site("store.confirm.unknown-edge")
_SITE_CONFIRM_NOT_ASSERTABLE = declare_site("store.confirm.not-assertable")
_SITE_CONFIRM_REQUEST_DIGEST = declare_site("store.confirm.request-digest")
_SITE_CONFIRM_CORRELATION = declare_site("store.confirm.correlation")
_SITE_CONFIRM_SOURCE_REDACTED = declare_site("store.confirm.source-redacted")   # specs/0045 §4d, INV-G10
_SITE_CONFIRM_ACTIVE_CHALLENGE = declare_site("store.confirm.active-challenge")   # specs/0047 §4c, INV-R13
# specs/0047 §2c/§4b (T10a): the reply verb's refusals — the request's SHAPE (read no state), then the edge, then a
# resolve's target; and the registry's own-verb conflict (the shared terminal and verb rules are `_registry_held`'s)
_SITE_REPLY_KIND = declare_site("store.reply.kind")                      # INV-R8
_SITE_REPLY_ACTOR = declare_site("store.reply.actor")                    # §2c "who wrote it"
_SITE_REPLY_SHAPE = declare_site("store.reply.shape")                    # §4b's closed request; research's T10a F1
_SITE_REPLY_MARKER = declare_site("store.reply.marker")                  # INV-R7 / 0041 INV-RR1
_SITE_REPLY_UNKNOWN_EDGE = declare_site("store.reply.unknown-edge")      # INV-R9
_SITE_REPLY_REDACTED_EDGE = declare_site("store.reply.redacted-edge")    # §0, INV-R9
_SITE_REPLY_PROCEDURAL_EDGE = declare_site("store.reply.procedural-edge")    # §4d's ruling, INV-R19
_SITE_REPLY_RESOLVE_TARGET = declare_site("store.reply.resolve-target")  # INV-R14
_SITE_REPLY_RESOLVE_REPEAT = declare_site("store.reply.resolve-repeat")  # INV-R14
_SITE_REPLY_REQUEST_DIGEST = declare_site("store.reply.request-digest")  # INV-R15, R24
_SITE_REPLY_RESULT_MISSING = declare_site("store.reply.result-missing")  # 0008 §6c, reply's side
_SITE_SUPERSESSION_ABSORB_ACTED = declare_site("store.supersession.absorb-acted",
                                               declines=True)        # specs/0047 §4e, INV-R17
_SITE_REGISTRY_REDACTED = declare_site("store.registry.request-redacted")
_SITE_REGISTRY_VERB_HELD = declare_site("store.registry.verb-held")
_SITE_ACT_COUNTER = declare_site("store.act-counter.allocate")
_SITE_REGISTRY_RESULT_MISSING = declare_site("store.registry.result-missing")
_SITE_CONSOLIDATION_CONTENDED = declare_site("store.consolidation.contended")
_SITE_DELETE_NOT_CURRENT = declare_site("store.consolidation.delete-not-current")
_SITE_DELETE_EPISODE_OUTCOME = declare_site("store.delete-episode.outcome")
_SITE_DELETE_EPISODE_RESERVED = declare_site("store.delete-episode.reserved")
_SITE_JOURNAL_PRE_EPOCH = declare_site("store.journal.pre-epoch")
_SITE_EDGES_READ_FENCE = declare_site("store.edges.read-fence")
_SITE_EXPORT_NON_QUIESCENT = declare_site("store.export.non-quiescent", declines=NON_QUIESCENT)
_SITE_RENEW_REFUSED = declare_site("store.consolidation.renew-refused")
_SITE_TRANSITION = declare_site("store.consolidation.transition")
_SITE_EMBEDDING_DELAYED_WRITER = declare_site("store.embedding.delayed-writer")
_SITE_EMBEDDING_STALE_CONTENT = declare_site("store.embedding.stale-content")
_SITE_EMBEDDING_TXN_LOCKED = declare_site("store.embedding.txn-locked")   # specs/0041 §4e (tranche 5): the read-and-publish lock
_SITE_WRITE_NOT_CURRENT = declare_site("store.consolidation.write-not-current")

# The schema is DERIVED from the versioning registry — one declaration, which
# is 0007 §4a-vi's "honest end state": there is no second copy to drift, and
# `registry_conformance` compares this module against the registry it is built
# from. It tracks the CURRENT `SCHEMA_VERSION` (v2 adds `specs/0008`'s
# `confirmations` table), never a pinned v1. `IF NOT EXISTS` is gone with it:
# creation now happens exactly once, on the §4 "new" path, inside the open
# transaction.
_SCHEMA = ";\n".join(o.ddl for o in SCHEMAS[SCHEMA_VERSION]) + ";\n"

# specs/0029 §4b — EVERY function in this module that writes the `edges` table,
# with its event ruling. `tests/test_0029_carrier.py::
# test_every_edge_writing_site_carries_an_event_ruling` DERIVES the population
# (a regex over the raw UPDATE / INSERT ... INTO / DELETE FROM forms, literal
# and interpolated) and refuses a site absent here. KIND IS NOT A PROPERTY OF
# THE SITE — it is decided per WRITE by `_journal_edge_write` from prior
# presence × serialization delta (v4 F-A: no site→kind mapping can be total);
# the only site-determined kinds are the two `active` flips, passed as a hint.
_ERASE_TABLES = ("contribution_ledger",
                 "edges", "episodes", "wiki", "write_counter",
                 "confirmations", "consolidation_ops",
                 "supersession_refusals", "supersession_operations",
                 "edge_embedding", "edge_event", "policy_receipt",
                 "episode_event", "redactions",          # specs/0041 v15: the episode journal and the attestation record are erasable per user
                 "request_registry",                     # specs/0008 v7 §6g: replay ends at erasure; act_counter is NOT here (never reset)
                 "replies",                              # specs/0047 INV-R22: the user's replies, with their registry rows
                 # specs/0044 §4g-ii (the 0008 amendment's one erasure rule, §6g): everything 0044 records for the user.
                 # arity_era, plan_header, reclassification_plan and migration_op are store-level, never per-user, and
                 # never erased
                 "arity_inventory", "refusal_inventory", "migration_outcome", "migration_run",
                 # specs/0022 × 0008 §6g (the owner, 2026-10-29: "Erase it"): the user's revocation ledger. Append-only
                 # BETWEEN erasures; erasure ends it, so a recreated user id inherits no standing revocation
                 "source_revocations")
# specs/0044 §4f-ii: every ruling carries a LIFETIME disposition — `choke-point` (its lifetime transitions are derived
# at `_journal_edge_write` from the persisted prior and new row) or `erasure` (`forget_user`, under 0008 §6g's one
# erasure rule). tests/test_0029_carrier.py refuses a ruling without one.
EDGE_WRITE_SITE_RULINGS = {
    "_upsert_edge_row": {
        "ruling": "reads the persisted prior, upserts, journals through the choke "
                  "point (created / mutated / no event on unchanged bytes); a same-id upsert can write EITHER "
                  "lifetime state (specs/0044 §4f-ii: it reinstates and re-retires without the two methods below)",
        "lifetime": "choke-point"},
    "confirm_edge": {
        "ruling": "rewrites the edge json in place; journals (mutated, or no "
                  "event when the confirmation changed no byte)",
        "lifetime": "choke-point"},
    "_invalidate_edge_row": {
        "ruling": "the invalidate METHOD's active=0 write (not the only one: the same-id upsert writes it too, "
                  "specs/0044 §4f-ii); journals with the site hint "
                  "`invalidated`, reason validated against DISPOSITIONED_REASONS",
        "lifetime": "choke-point"},
    "_reinstate_edge_row": {
        "ruling": "the reinstate METHOD's active=1 write (not the only one: the same-id upsert writes it too, "
                  "specs/0044 §4f-ii); journals with the site "
                  "hint `reinstated`, reason `source_restored` (specs/0029 v12)",
        "lifetime": "choke-point"},
    "_recompute_edge_row": {
        "ruling": "the fourth site (R1-4): rewrites valid_from/observed_at/"
                  "confidence; journals on the FULL-STATE delta (mutated)",
        "lifetime": "choke-point"},
    "commit_outcome_import_plan": {
        "ruling": "imports edges through the choke point (created for new ids, "
                  "mutated for a changed same-id row, none when byte-identical)",
        "lifetime": "choke-point"},
    "_redact_in_txn": {
        "ruling": "specs/0041 §4c: the redaction's in-transaction body (`redact()` and, for an imported notice, the "
                  "import commit call it): rewrites the target's json and duplicated columns in place (the treatment "
                  "map), TOMBSTONES `state` on every prior event for the edge (the journal's one in-place "
                  "rewrite, amending 0029 V-APPEND) and journals a `redacted` event with the redaction reason through "
                  "the choke point",
        "lifetime": "choke-point"},
    "forget_user": {
        "ruling": "erasure: deletes the user's edges AND the user's events in "
                  "the same transaction (V-ERASE); journals nothing — the "
                  "journal is what is being erased",
        "tables": _ERASE_TABLES,
        "lifetime": "erasure"},
}


def _reply_shape_problem(kind: str, text, target) -> Optional[str]:
    """specs/0047 §4b's closed request shape, read from the request alone: a `resolve` names its challenge and carries
    no text; every other kind carries non-empty text and no target. Text must encode as strict UTF-8 (research's T10a
    F1: a lone surrogate otherwise raises `UnicodeEncodeError` at the INSERT, a `ValueError` with no reason). None:
    well formed."""
    if kind == "resolve":
        if not (isinstance(target, str) and target):
            return "a resolve names the challenge it withdraws (target)"
        if text is not None:
            return "a resolve carries no text"
        try:
            target.encode("utf-8")
        except UnicodeEncodeError:              # research's T10a S2-3: F1's check, on the target too
            return "the target does not encode as UTF-8 (a lone surrogate)"
        return None
    if target is not None:
        return f"only a resolve names a target ({kind!r} does not)"
    if not (isinstance(text, str) and text.strip()):
        return "a reply's text is empty"
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return "the text does not encode as UTF-8 (a lone surrogate)"
    return None


class SqliteStore(Store):
    def __init__(self, path: str | Path = "veracium.db", *,
                 allow_adopt: bool = True, audit_sink=None,
                 busy_timeout_ms: int = 5000, clock=None):
        self._path = str(path)
        # specs/0010 §4b-ii: the lease clock is the STORE's, not any worker's —
        # worker clocks disagree and a lease decided by the holder is not a lease.
        # Injectable so tests can drive lease expiry/renewal deterministically.
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        # 0007 §4e: audit strings are validated against a 4096-byte cap, never
        # truncated — and the path is checked before connecting, so the limit
        # is ours rather than whatever the OS happens to raise.
        if len(self._path.encode()) > 4096:
            raise ValueError("store path exceeds the 4096-byte audit limit")
        # check_same_thread=False + a lock: safe for the library's typical
        # single-writer, many-reader agent usage without a connection pool.
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        # 0007 §4c: `database is locked` waits this long, then refuses loudly
        # with reason="locked" — a startup failure that manifests as a hang is
        # worse than one that manifests as an error.
        self._conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        try:
            # The 0007 §4 decision table: refuse-unrecognised, stamp, adopt-v1.
            # Replaces the former unconditional `executescript(_SCHEMA)`, which
            # opened ANY store and silently added missing tables to foreign
            # ones. open_versioned() takes BEGIN IMMEDIATE before reading
            # anything and commits exactly once.
            open_versioned(self._conn, self._path,
                           allow_adopt=allow_adopt, audit_sink=audit_sink)
        except BaseException:
            self._conn.close()
            raise
        # RE-ENTRANT (0041 round 10): `atomic()` holds it across a caller's read-check-write, and the store's own
        # methods called inside take it again on the same thread. Across threads nothing changes.
        self._lock = threading.RLock()
        # specs/0028 §4b-o: the thread holding an open `read_window` — a
        # nested window on that thread JOINS instead of re-taking the
        # (non-reentrant) instance lock; any other thread waits on the lock.
        self._window_owner = None
        # specs/0029 §4a: the per-transaction allocation scope (txn per user,
        # one clock read per batch). None outside a journaled write.
        self._txn_alloc = None

    def _bump(self, user_id: str) -> None:
        self._conn.execute(
            "INSERT INTO write_counter(user_id, n) VALUES(?, 1) "
            "ON CONFLICT(user_id) DO UPDATE SET n = n + 1", (user_id,))

    # -- source identity (specs/0006) --------------------------------------
    def local_origin(self) -> str:
        """specs/0006 §4.2 — this store's durable, minted `origin` (the `store_identity`
        singleton). It is the value an absent local record-`origin` resolves to at read
        (§4 rule 6, `source_identity.resolve_origin`). Minted once at create/migrate and
        durable across reopen/backup (I11)."""
        row = self._conn.execute(
            "SELECT origin FROM store_identity WHERE id = 1").fetchone()
        if row is None:
            raise RuntimeError(
                "store_identity singleton is missing — a v5 store mints it at "
                "creation/migration (specs/0006 §4.2); this store did not")
        return row[0]

    # -- specs/0029: the journaled write transaction and its choke point ----
    @contextlib.contextmanager
    def _journal_scope(self):
        """The allocation scope of ONE event-emitting transaction: a fresh
        per-user txn map and one clock read. Re-entrant (an inner scope joins
        the outer's batch — V-BATCH). Opened by `_write_txn`, and by the
        revocation operation around its own `BEGIN IMMEDIATE`."""
        if self._txn_alloc is not None:
            yield
            return
        self._txn_alloc = {"clock": None, "users": {}}
        try:
            yield
        finally:
            self._txn_alloc = None

    @contextlib.contextmanager
    def _write_txn(self):
        """specs/0029 §4a: every edge-writing entry point runs inside this.
        Takes `BEGIN IMMEDIATE` BEFORE any allocation read (V-TXN-ALLOC —
        the DEFERRED schedule lets two connections read one maximum; the
        seam model keeps that reproduction as the negative control) and
        commits or rolls back the WHOLE batch. JOINS an already-open
        transaction (the caller owns commit) instead of nesting. The 0007
        §4c discipline at BOTH lock sites of the transaction this opened —
        its START (BEGIN IMMEDIATE) and its COMMIT: `busy_timeout` waits,
        then this refuses loudly in one form naming the site (specs/0029 v10
        §4a, V-LOCK-REFUSAL-FORM). The joined case commits elsewhere and is
        outside that guarantee (§4a-i)."""
        with self._journal_scope():
            if self._conn.in_transaction:
                yield
                return
            with _SITE_TXN_LOCKED.consult():
                try:
                    self._conn.execute("BEGIN IMMEDIATE")
                except sqlite3.OperationalError as e:
                    raise _SITE_TXN_LOCKED.fire(sqlite3.OperationalError(
                        f"could not take the write lock for a journaled edge write "
                        f"({e}) — refusing rather than allocating under a DEFERRED "
                        f"schedule (specs/0029 §4a; 0007 §4c)")) from e
            try:
                yield
            except BaseException:
                if self._conn.in_transaction:
                    self._conn.rollback()
                raise
            else:
                if self._conn.in_transaction:
                    with _SITE_TXN_LOCKED_RETRY.consult():
                        try:
                            self._conn.commit()
                        except sqlite3.OperationalError as e:
                            # specs/0029 v10 §4a, V-LOCK-REFUSAL-FORM: the COMMIT-time lock — a
                            # reader's SHARED lock outliving our busy_timeout under the default
                            # journal (0028 §5, measured 2026-09-07). SQLite has already rolled
                            # the batch back; refuse in the SAME form as the BEGIN, naming the
                            # site, same exception type (callers catching OperationalError are
                            # unchanged), the bare text kept as the cause. The explicit rollback
                            # is belt and braces for a state probed and not found.
                            if self._conn.in_transaction:
                                self._conn.rollback()
                            raise _SITE_TXN_LOCKED_RETRY.fire(sqlite3.OperationalError(
                                f"could not COMMIT a journaled edge write ({e}) — the write lock "
                                f"was lost at COMMIT after busy_timeout; no part of the batch is "
                                f"applied and the connection is reusable (specs/0029 §4a "
                                f"V-LOCK-REFUSAL-FORM; 0007 §4c)")) from e

    _SITE_KINDS = frozenset({"invalidated", "reinstated", "redacted"})   # specs/0041 §4c: the redaction is a write

    def _evict_wiki_on_view_change(self, user_id: str, model, prior_json: Optional[str],
                                   new_json: Optional[str]) -> None:
        """specs/0004 W1/W9 and 0047 §4d (R-II round 2's RII-R2-01), inside the caller's write transaction: drop the
        user's compiled wiki when a write REPLACES (or deletes: `new_json` None) a persisted record whose
        `schema.assertion_view` the write changes — a challenged record's twin key, a drawn record's value, its
        quarantine or use_only, its retirement by a revoking reason. A fresh record (no prior) never evicts: that is
        W3's staleness counter, and a retaining change (a counter, a note, decay, absorption) keeps the wiki by the
        view's own rule. Edges reach this from `_journal_edge_write`, the choke point every `edges` writer passes;
        every `episodes` writer calls it itself (tests/test_rii_r2_01_writer_inventory.py runs each one)."""
        if prior_json is None or prior_json == new_json:
            return
        try:
            new = model.model_validate_json(new_json) if new_json is not None else None
            moved = assertion_view(model.model_validate_json(prior_json)) != assertion_view(new)
        except ValidationError:
            # a row the model cannot read back (specs/0048's out-of-range write is one): its view is unknown, so the
            # wiki is dropped — and the WRITE is never refused here, so what a writer may store does not change
            moved = True
        if moved:
            self._conn.execute("DELETE FROM wiki WHERE user_id=?", (user_id,))

    def _journal_edge_write(self, user_id: str, edge_id: str, new_json: str,
                            prior_json: Optional[str], *, kind: Optional[str] = None,
                            reason: Optional[str] = None) -> Optional[str]:
        """THE emission choke point (specs/0029 §4b): called by every `edges`
        writer AFTER its row write, inside the same transaction. Decides the
        kind from the WRITE — prior absent → `created`; prior present and the
        serialization changed → `mutated`, or the site's `active`-flip hint;
        prior present and bytes unchanged → NO event (the full-state trigger
        basis, F4). `baseline` is the migration's kind and refused here.
        `reason` is non-NULL iff kind is invalidated (one of the seven
        DISPOSITIONED_REASONS), redacted (REDACTION_REASONS) or reinstated
        (REINSTATEMENT_REASONS, specs/0029 v12 — NULL included, refused); an
        unregistered reason refuses the WRITE (the exception unwinds the
        transaction). Returns the kind
        journaled, or None. specs/0041 §4c: a `redacted` write is journaled
        even when the bytes did not move (a record that arrived already
        carrying the marker, §4g) — the redaction is the write."""
        if self._txn_alloc is None or not self._conn.in_transaction:
            raise RuntimeError(
                "edge write outside a journaled write transaction — every "
                "edges writer runs inside _write_txn (specs/0029 §4a)")
        # specs/0044 §4f-ii: the LIFETIME HOOK, before the unchanged-bytes return below (an unchanged row is no
        # transition). Derived from the persisted prior and the new row — never from `kind`, which a changed same-id
        # upsert gives as `mutated` — so every writer that passes this point is bound alike.
        self._apply_lifetime_transition(user_id, edge_id, prior_json, new_json)
        if kind is not None and kind not in self._SITE_KINDS:
            raise ValueError(
                f"kind {kind!r} is not a site-determinable kind — only the two "
                f"active flips are; created/mutated derive from the write and "
                f"baseline is the migration's alone (specs/0029 §4b)")
        if prior_json is None:
            if kind is not None:
                raise ValueError(f"{kind!r} write with no prior row for {edge_id!r}")
            kind = "created"
        elif new_json == prior_json and kind != "redacted":
            return None                          # unchanged serialization: no event
        elif kind is None:
            kind = "mutated"
        if kind == "invalidated":
            with _SITE_JOURNAL_REASON.consult():
                if reason not in DISPOSITIONED_REASONS:
                    raise _SITE_JOURNAL_REASON.fire(ValueError(
                        f"invalidation reason {reason!r} is not registered in "
                        f"DISPOSITIONED_REASONS — the write is refused (specs/0029 V-KIND)"))
        elif kind == "redacted":
            # specs/0041 §4c / §11.2 (D1): the redacted event carries redaction's own closed vocabulary in
            # `reason` — the one kind beside `invalidated` whose reason is non-NULL; prose is refused here too
            with _SITE_JOURNAL_REDACTION_REASON.consult():
                if reason not in _redaction.REDACTION_REASONS:
                    raise _SITE_JOURNAL_REDACTION_REASON.fire(ValueError(
                        f"redaction reason {reason!r} is not one of {_redaction.REDACTION_REASONS} — "
                        f"the write is refused (specs/0041 §11.2, D1)"))
        elif kind == "reinstated":
            # specs/0029 v12 §4b-i (INV-J1): WHY the edge came back, from the closed vocabulary; NULL on a new write is
            # refused like any unregistered reason, and the raise unwinds the whole transaction — the row's
            # reinstatement with it
            with _SITE_JOURNAL_REINSTATEMENT_REASON.consult():
                if reason not in REINSTATEMENT_REASONS:
                    raise _SITE_JOURNAL_REINSTATEMENT_REASON.fire(ValueError(
                        f"reinstatement reason {reason!r} is not one of {REINSTATEMENT_REASONS} — the write is "
                        f"refused (specs/0029 v12 §4b-i)"))
        else:
            reason = None
        # specs/0004 W1/W9, 0047 §4d (RII-R2-01): the WIKI'S eviction, derived here as the lifetime hook's effects are —
        # from the persisted prior and the new row, so a same-ID replace that changes what the wiki may assert evicts
        # it on every `edges` writer, whichever method ran. After the kind and reason refusals (a refused write has no
        # effect to apply); an unchanged row returned above, and could not have evicted (an equal row has an equal view)
        self._evict_wiki_on_view_change(user_id, Edge, prior_json, new_json)
        alloc = self._txn_alloc
        if alloc["clock"] is None:
            alloc["clock"] = self._now()         # ONE clock read per batch (§4c)
        if user_id not in alloc["users"]:
            alloc["users"][user_id] = (
                next_txn(self._conn, user_id),
                mint_recorded_at(self._conn, user_id, alloc["clock"]))
        txn, recorded_at = alloc["users"][user_id]
        append_event(self._conn, user_id=user_id, seq=next_seq(self._conn, user_id),
                     txn=txn, edge_id=edge_id, kind=kind, reason=reason,
                     state=new_json, recorded_at=recorded_at)
        return kind

    def _apply_lifetime_transition(self, user_id: str, edge_id: str, prior_json: Optional[str],
                                   new_json: str) -> Optional[str]:
        """specs/0044 §4f-ii's effects, in the writer's transaction: a reinstatement ends the row's `arity_inventory`
        membership; a retirement, re-retirement or redaction clears `applicable` on its `migration_outcome` row. Both
        terminal. The derivation is `lifetime.transition` (§4f-ii's table, one implementation)."""
        t = _lifetime.transition(prior_json, new_json)
        if t in _lifetime.ENDS_MEMBERSHIP:
            self._conn.execute("DELETE FROM arity_inventory WHERE edge_id=?", (edge_id,))
        elif t in _lifetime.CLEARS_APPLICABLE:
            self._conn.execute("UPDATE migration_outcome SET applicable=0 "
                               "WHERE user_id=? AND edge_id=? AND applicable=1", (user_id, edge_id))
        return t

    # -- specs/0029 read surface --------------------------------------------
    def edge_events(self, user_id: str, *, edge_id: Optional[str] = None,
                    until_txn: Optional[int] = None) -> list[EdgeEvent]:
        q = ("SELECT user_id, seq, txn, edge_id, kind, reason, state, recorded_at "
             "FROM edge_event WHERE user_id=?")
        args: list = [user_id]
        if edge_id is not None:
            q += " AND edge_id=?"; args.append(edge_id)
        if until_txn is not None:
            q += " AND txn<=?"; args.append(self._cutoff(until_txn))
        q += " ORDER BY seq"
        return [EdgeEvent(*r) for r in self._conn.execute(q, args).fetchall()]

    @staticmethod
    def _cutoff(until_txn) -> int:
        if isinstance(until_txn, bool) or not isinstance(until_txn, int):
            raise CutoffDomainError(
                f"until_txn must be an int, got {type(until_txn).__name__}")
        return until_txn

    def edge_state_at(self, user_id: str, edge_id: str, until_txn: int):
        """specs/0029 §4b-ii: the RAW carrier — the `state` of the last event
        with txn ≤ until_txn, VERBATIM text, identity from the ROW COLUMNS;
        None before the edge's first event; a typed refusal below the user's
        epoch (V-EPOCH: a migrated store fabricates no pre-epoch knowledge)."""
        k = self._cutoff(until_txn)
        epoch = self.epoch_txn(user_id)
        with _SITE_JOURNAL_PRE_EPOCH.consult():
            if k < epoch:
                raise _SITE_JOURNAL_PRE_EPOCH.fire(PreEpochQuery(
                    f"until_txn {k} precedes user {user_id!r}'s journaling epoch "
                    f"(txn {epoch}) — no state is known before it (specs/0029 §4e)"))
        row = self._conn.execute(
            "SELECT edge_id, user_id, state, txn, seq, kind, recorded_at "
            "FROM edge_event WHERE user_id=? AND edge_id=? AND txn<=? "
            "ORDER BY seq DESC LIMIT 1", (user_id, edge_id, k)).fetchone()
        if row is None:
            return None
        return RawEdgeState(edge_id=row[0], user_id=row[1], state=row[2], txn=row[3],
                            seq=row[4], kind=row[5], recorded_at=row[6])

    def epoch_txn(self, user_id: str) -> int:
        """§4e: the txn of the user's migration baseline batch — DERIVED
        (MIN over the user's `baseline` events); 0 for a user journaled from
        the first write, which no cutoff can precede."""
        row = self._conn.execute(
            "SELECT MIN(txn) FROM edge_event WHERE user_id=? AND kind='baseline'",
            (user_id,)).fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    def current_state(self, user_id: str, edge_id: str, *, principal=None, policy=None):
        """specs/0030 §4a-i: `CurrentState` — the edge's current row VERBATIM,
        the three-valued source-restriction verdict from the STANDING source
        state, the per-user read token and (with a principal) the scope cell,
        ALL from ONE read window the store opens and closes here. The
        classifier consumes this; no caching (every call recomputes)."""


# ---- src/veracium/store/sqlite.py — beside epoch_txn -------------------------
    def current_state(self, user_id: str, edge_id: str, *, principal=None, policy=None):
        """specs/0030 §4a-i — ONE READ WINDOW, ONE WORLD. The store OWNS the
        window (the co-check's transaction-ownership contract): an explicit
        `BEGIN` on this connection under the instance lock, the derivation
        reads inside it and issues no BEGIN of its own, `COMMIT` closes it.
        The GUARANTEE is mode-neutral and the MECHANISM is not: under
        rollback-journal the window holds a SHARED lock and a concurrent
        writer is refused for its duration; under WAL the writer proceeds and
        this reader keeps its snapshot (V-WINDOW asserts the property in both
        modes). Joins an already-open transaction rather than nesting.

        specs/0028 §4b-o: the window shape is EXTRACTED to `read_window`;
        this call joins a resolution's window when one is open on this
        thread and opens its own otherwise — exactly the pre-0028 shape."""
        from .current_state import derive_current_state
        with self.read_window(user_id):
            return derive_current_state(self, user_id, edge_id,
                                        principal=principal, policy=policy)

    @contextlib.contextmanager
    def read_window(self, user_id: Optional[str] = None):
        """specs/0028 §4b-o — THE public read-only window: `BEGIN` under the
        instance lock, or JOIN an already-open transaction; `ROLLBACK` on
        error, `COMMIT` on exit. `current_state`'s shape (specs/0030 §4a-i),
        extracted so a resolution can open ONE outer window that every read
        joins — `edges(active_only=False)`, each `edges_superseding` hop and
        each `current_state` — and read one snapshot (V-ONE-SNAPSHOT). The
        join is keyed on the OWNER THREAD (the instance lock is re-entrant
        since 0041 round 10, and a window inside `atomic()` joins its open
        write transaction): a nested window on the holding thread yields at
        once; a window on another thread waits on the lock as any store
        operation does. What a concurrent WRITER sees is measured in
        specs/0028 §5 (never "refused for the duration"): under the default
        journal it waits, and commits or loses the write at its
        `busy_timeout`; under WAL it commits and this reader keeps its
        snapshot. `user_id` names the scope for the caller's record; the
        window itself is connection-wide."""
        # ASSUMPTION, stated for the next person adding an executor: a
        # resolution runs on ONE thread from BEGIN to COMMIT. The window's
        # identity is the owning thread, so a path that hops threads
        # mid-resolution (a pool, `to_thread`, `run_in_executor`) would open
        # a SECOND window on the other thread and V-ONE-SNAPSHOT would fail
        # looking like a data bug. No shipped path hops threads today
        # (measured 2026-09-08: no executor in mcp_server.py or the package).
        me = threading.get_ident()
        if self._window_owner == me:
            yield self                        # JOIN the window this thread holds
            return
        with self._lock:
            opened = not self._conn.in_transaction
            if opened:
                self._conn.execute("BEGIN")
            self._window_owner = me
            try:
                yield self
            except BaseException:
                # the window is READ-ONLY by contract, so COMMIT and ROLLBACK are
                # equivalent today — the rollback makes the contract explicit
                # rather than latent (research, post-merge Q2)
                if opened and self._conn.in_transaction:
                    self._conn.execute("ROLLBACK")
                raise
            finally:
                self._window_owner = None
            if opened and self._conn.in_transaction:
                self._conn.execute("COMMIT")

    def edges_superseding(self, user_id: str, edge_id: str, *, principal=None,
                          policy=None):
        """specs/0028 §5.1 — the DIRECT-successor accessor, SCAN-BACKED and
        stated as such: `supersedes` is a field inside the edge JSON with no
        column and no index, so it is scanned for, ONE read of the user's
        edges inside the window (a resolution's, joined, or this call's own).
        The queried edge is read through the SAME view as its successors
        (R5-1): an edge outside the caller's view asserts nothing TO THIS
        CALLER, exactly as a nonexistent id does — one code path. Every
        visibility decision runs INSIDE the window, because the shared
        `ScopeView` fires lazy contribution-ledger reads."""
        from ..asof.resolve import lookup_successors
        from ..scope_read import view_for
        with self.read_window(user_id):
            view = view_for(self, user_id, principal, policy)
            rows = self.edges(user_id, active_only=False, include_quarantined=True)
            visible = (lambda e: True) if view is None else view.visible
            return lookup_successors(rows, edge_id, visible)

    # -- edges -------------------------------------------------------------
    @staticmethod
    def _refuse_redacted_reason(reason, what: str, where: str) -> None:
        """specs/0041 §11.2 (round 10): `redacted` is written ONLY by a redaction — the treatment (`_redact_in_txn`)
        writes the treated row directly and passes through none of the writers that call this. Every other writer
        refuses it: an ordinary write that set it would make a record no redaction touched read, in `why` and in an
        export, as redacted — the marker's own problem one field over (INV-11's mirror, for the registry value)."""
        with _SITE_REDACTED_REASON.consult():
            if reason == _redaction.REDACTED_REASON_VALUE:
                raise _SITE_REDACTED_REASON.fire(ValueError(
                    f"refused: {what} would carry the reason {reason!r}, which only a redaction writes "
                    f"(specs/0041 §11.2)"), where)

    def _upsert_edge_row(self, edge: Edge) -> None:
        """INSERT OR REPLACE one edge with the specs/0008 §6d guards, WITHOUT taking the
        lock, bumping the write counter, or committing — the caller owns the transaction.
        `add_edge` and `apply_supersession_plan` (specs/0003 §4f) both use it, so the
        ownership + needs_confirmation guards hold on every persistence path, not only
        the single-edge one."""
        # specs/0041 §4b (INV-11's MIRROR): a NON-REDACTION write may not INTRODUCE the
        # marker — every persistence path runs through here (add_edge, the supersession
        # plan, correction), so the refusal is one line for all of them. Redaction itself
        # (tranche 3) writes under its own transaction, never through this method.
        with _SITE_UPSERT_MARKER.consult():
            hit = _redaction.marker_fields(edge.model_dump(mode="json"))
            if hit:
                raise _SITE_UPSERT_MARKER.fire(ValueError(
                    f"refused: edge {edge.id!r} would introduce the redaction marker in "
                    f"{hit} — only a redaction writes the marker (specs/0041 §4b, INV-11's mirror)"))
        # specs/0041 §4b-ii / INV-11 (v9, tranche 3): an ordinary write to a record whose redaction is
        # ATTESTED by a redaction record is REFUSED, not merged — keyed on the RECORD, never on the marker
        # bytes, so an unattested marker row stays writable (§4b's attestation rule; the test's control).
        with _SITE_UPSERT_ATTESTED.consult():
            attested = self._attested_fields(edge.user_id, "edge", edge.id, coverage=False)
            if attested:
                raise _SITE_UPSERT_ATTESTED.fire(ValueError(
                    f"refused: edge {edge.id!r} is redacted — a redaction record attests {sorted(attested)}; "
                    f"an ordinary write may not repopulate it (specs/0041 §4b-ii, INV-11)"))
        # specs/0041 §4h(i): a quarantine RELATION must carry the QUARANTINED disclosure —
        # the relation-only quarantine is held by one clause of `Edge.quarantined`, and a
        # later relation replacement would silently promote the claim. Ingest sets both;
        # this closes the model-and-store path that never did.
        # specs/0041 §11.2 / D1 (round 10, R9-02(c); found by sweep D): `Edge.invalidation_reason` CLOSES for future
        # writes on the registry the journal already enforces for `invalidate_edge`. Absent (None) stays valid; a
        # prose reason — accepted here on create and on a re-upsert to invalidated — refuses. Stored legacy prose
        # still loads (the closure binds writers and import, never the read path).
        self._refuse_redacted_reason(edge.invalidation_reason, f"edge {edge.id!r}", "edge-write")
        with _SITE_UPSERT_INVALIDATION_REASON.consult():
            if edge.invalidation_reason is not None and edge.invalidation_reason not in DISPOSITIONED_REASONS:
                raise _SITE_UPSERT_INVALIDATION_REASON.fire(ValueError(
                    f"refused: edge {edge.id!r} carries invalidation reason {edge.invalidation_reason!r}, which is not "
                    f"a registered reason {tuple(DISPOSITIONED_REASONS)} (specs/0041 §11.2, D1)"))
        with _SITE_UPSERT_RELATION_ONLY_QUARANTINE.consult():
            if edge.relation == QUARANTINE_RELATION and edge.provenance.disclosure != Disclosure.QUARANTINED:
                raise _SITE_UPSERT_RELATION_ONLY_QUARANTINE.fire(ValueError(
                    f"refused: edge {edge.id!r} carries the quarantine relation {QUARANTINE_RELATION!r} "
                    f"without the QUARANTINED disclosure — the disclosure is the durable discriminator "
                    f"(specs/0041 §4h(i))"))
        # specs/0008 §6d: may NOT clear `needs_confirmation` (True→False) when replacing
        # an edge of the same id — only `confirm_edge` may — and may NOT change an edge's
        # `user_id`. Compared against the PERSISTED prior state, so a reconstructed edge
        # cannot slip the transition past the write path (C1, C10).
        with _SITE_UPSERT_IMMUTABLE.consult():
            prior = self._conn.execute(
                "SELECT user_id, json FROM edges WHERE id=?", (edge.id,)).fetchone()
            if prior is not None:
                if prior[0] != edge.user_id:
                    raise _SITE_UPSERT_IMMUTABLE.fire(ValueError(
                        f"cannot change edge {edge.id!r}'s user_id "
                        f"({prior[0]!r} → {edge.user_id!r}) — ownership is not "
                        f"transferable through the upsert path (specs/0008 §6d)"), "user-id")
                prior_edge = Edge.model_validate_json(prior[1])
                if prior_edge.needs_confirmation and not edge.needs_confirmation:
                    raise _SITE_UPSERT_IMMUTABLE.fire(ValueError(
                        f"cannot clear needs_confirmation (True→False) on "
                        f"edge {edge.id!r} — only confirm_edge may (specs/0008 §6d, C1)"), "needs-confirmation")
                # specs/0019 §3b/§4d (R2-4, U4): a STORED row's `ungrounded` never
                # changes — the same-ID replace path refuses EVERY transition, in
                # BOTH directions, with no exception (absorption inserts a NEW
                # survivor whose flag is the N-ary OR computed pre-insert, so no
                # discriminator is needed here). Compared against the PERSISTED
                # prior state, the 0008 §6d guard shape.
                if prior_edge.ungrounded != edge.ungrounded:
                    raise _SITE_UPSERT_IMMUTABLE.fire(ValueError(
                        f"cannot change ungrounded "
                        f"({prior_edge.ungrounded} → {edge.ungrounded}) on edge "
                        f"{edge.id!r} — a stored flag is immutable in both "
                        f"directions (specs/0019 §4d, U4)"), "ungrounded")
                # specs/0037 §3 (V-BASIS-IMMUTABLE, the 0019 U4 shape): a STORED
                # basis and a STORED kind stamp never change on same-id replace,
                # in either direction — a promotion (observed → stated) is the
                # cap-only rule's mutant; a demotion or a stamp flip is a
                # laundering route in the other direction. Refused, nothing
                # written. Absorption inserts a NEW survivor carrying the
                # whole-set minimum, so no discriminator is needed here.
                if prior_edge.provenance.basis != edge.provenance.basis:
                    raise _SITE_UPSERT_IMMUTABLE.fire(ValueError(
                        f"cannot change basis ({prior_edge.provenance.basis!r} → "
                        f"{edge.provenance.basis!r}) on edge {edge.id!r} — a stored "
                        f"procedural marker is immutable in both directions "
                        f"(specs/0037 §3, V-BASIS-IMMUTABLE)"), "basis")
                if prior_edge.provenance.record_kind != edge.provenance.record_kind:
                    raise _SITE_UPSERT_IMMUTABLE.fire(ValueError(
                        f"cannot change record_kind ({prior_edge.provenance.record_kind!r} → "
                        f"{edge.provenance.record_kind!r}) on edge {edge.id!r} — a stored "
                        f"procedural marker is immutable in both directions "
                        f"(specs/0037 §3, V-BASIS-IMMUTABLE)"), "record-kind")
                # specs/0037 v23 (V-PRODUCER-IMMUTABLE): the producer stamp is a
                # write-time fact; a same-id replace that names a different
                # producer — or drops or adds one — is refused the same way.
                if prior_edge.provenance.producer != edge.provenance.producer:
                    raise _SITE_UPSERT_IMMUTABLE.fire(ValueError(
                        f"cannot change producer ({prior_edge.provenance.producer!r} → "
                        f"{edge.provenance.producer!r}) on edge {edge.id!r} — a stored "
                        f"producer stamp is immutable in both directions "
                        f"(specs/0037 v23 §4a-iii, V-PRODUCER-IMMUTABLE)"), "producer")
                # specs/0045 §2 (INV-G13: `attv` is never rewritten; `att` and `src` are written once at insert): the
                # declarative grounding axis is immutable in both directions, the 0019 U4 shape. Absorption inserts a
                # NEW survivor carrying its own values (§4e), so no discriminator is needed here.
                for axis, held, written in (("att", prior_edge.att, edge.att), ("src", prior_edge.src, edge.src),
                                             ("attv", prior_edge.attv, edge.attv)):
                    if held != written:
                        raise _SITE_UPSERT_IMMUTABLE.fire(ValueError(
                            f"cannot change {axis} ({held!r} → {written!r}) on edge {edge.id!r} — the grounding "
                            f"axis is written once at insert (specs/0045 §2)"), axis)
            # specs/0037 v19 (V-STAMP-INHERITED; research's red team, 2026-09-13): a
            # SUCCESSOR of a procedural record must itself be procedural. correct()
            # minted one without the stamp and the note rendered; correct() now refuses
            # a procedural prior, and this choke point refuses any path that would
            # drop the markers across a `supersedes` link — keyed on the PERSISTED
            # predecessor's own stamp/basis, never on the registry.
            if edge.supersedes:
                pred = self._conn.execute("SELECT json FROM edges WHERE id=?", (edge.supersedes,)).fetchone()
                if pred is not None:
                    pp = (json.loads(pred[0]).get("provenance") or {})
                    if (pp.get("record_kind") == "procedural" or pp.get("basis") is not None) and not (
                            edge.provenance.record_kind == "procedural" or edge.provenance.basis is not None):
                        raise _SITE_UPSERT_IMMUTABLE.fire(ValueError(
                            f"edge {edge.id!r} would supersede procedural record {edge.supersedes!r} without the "
                            f"procedural markers — a successor of a procedural record is procedural "
                            f"(specs/0037 §4a-iii, V-STAMP-INHERITED); nothing written"), "supersedes-procedural")
                    # specs/0037 v23 (V-PRODUCER-INHERITED): the successor of a
                    # producer-stamped record carries the SAME producer — the path
                    # that minted the predecessor is a fact about the lineage, and
                    # a successor naming another producer (or none) would let the
                    # doctor's split drift across a supersession.
                    if pp.get("producer") is not None and edge.provenance.producer != pp.get("producer"):
                        raise _SITE_UPSERT_IMMUTABLE.fire(ValueError(
                            f"edge {edge.id!r} would supersede procedural record {edge.supersedes!r} with a "
                            f"different producer ({pp.get('producer')!r} → {edge.provenance.producer!r}) — "
                            f"the producer stamp is inherited across a supersession "
                            f"(specs/0037 v23 §4a-iii, V-PRODUCER-INHERITED); nothing written"), "supersedes-producer")
            new_json = edge.model_dump_json()
            self._conn.execute(
                "INSERT OR REPLACE INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (edge.id, edge.user_id, edge.subject, edge.relation, edge.object,
                 int(edge.active), int(edge.quarantined), new_json))
            self._journal_edge_write(edge.user_id, edge.id, new_json,
                                     prior[1] if prior is not None else None)

    @contextlib.contextmanager
    def atomic(self):
        """specs/0041 round 10 (P-TXN, sweep A's dispute/record_outcome/correct): ONE write transaction — BEGIN
        IMMEDIATE on this connection, under the (re-entrant) instance lock — for a caller's read, decision and writes
        together. Every store writer called inside JOINS it (`_write_txn` joins an open transaction), so a record read
        here and the episode that quotes it commit together or not at all, and no other connection can redact the
        record in between."""
        with self._lock, self._write_txn():
            yield self

    def add_edge(self, edge: Edge) -> None:
        with self._lock, self._write_txn():
            self._upsert_edge_row(edge)
            self._bump(edge.user_id)

    @staticmethod
    def _confirmation_from_row(row) -> Confirmation:
        (cid, uid, eid, cat, actor, cpath, corr, dig) = row
        return Confirmation(
            id=cid, user_id=uid, edge_id=eid, confirmed_at=datetime.fromisoformat(cat),
            actor=ConfirmationActor(actor), call_path=ConfirmationCallPath(cpath),
            correlation_id=corr, request_digest=dig)

    def _registry_held(self, user_id, correlation_id, verb) -> Optional[tuple]:
        """specs/0008 v8 §6c/§6g — the REQUEST REGISTRY's two rules every verb shares, in ONE body (INV-Q1: one id
        space per user; T7, research's stage-1 Q4), read before any read of live edge state (INV-Q2). None: the id
        is free. A redacted row is TERMINAL for every verb and payload, BEFORE the verb check (v8), naming the verb
        that holds it; an id held by another verb is an integrity conflict naming that verb. Otherwise the held
        `(request_digest, result_ref)`, which the calling verb compares and resolves with its own sites."""
        held = self._conn.execute(
            "SELECT verb, request_digest, result_ref FROM request_registry WHERE user_id=? AND correlation_id=?",
            (user_id, correlation_id)).fetchone()
        if held is None:
            return None
        held_verb, digest, result_ref = held
        with _SITE_REGISTRY_REDACTED.consult():
            if digest == _redaction.MARKER:
                raise _SITE_REGISTRY_REDACTED.fire(RequestRedacted(user_id, correlation_id, held_verb))
        with _SITE_REGISTRY_VERB_HELD.consult():
            if held_verb != verb:
                raise _SITE_REGISTRY_VERB_HELD.fire(ValueError(
                    f"correlation_id {correlation_id!r} is held by a {held_verb!r} request — integrity conflict "
                    f"(specs/0008 §6c)"))
        return digest, result_ref

    def _confirm_replay(self, user_id, correlation_id, request_digest) -> Optional[Confirmation]:
        """specs/0008 v7 §6c/§6g — `confirm()`'s side of the REQUEST REGISTRY, read before any read of live edge
        state (INV-Q2), and the ONE lookup both the front path and the C8 race fallback use. None: the id is free.
        Otherwise, in the spec's precedence: the shared rules (`_registry_held`: terminal, then the verb); a
        different canonical request is an integrity conflict; else the original result, reconstructed from
        `result_ref` without reading the edge, so it replays after the edge retired."""
        _COLS = ("id, user_id, edge_id, confirmed_at, actor, call_path, "
                 "correlation_id, request_digest")
        held = self._registry_held(user_id, correlation_id, "confirm")
        if held is None:
            return None
        digest, result_ref = held
        with _SITE_CONFIRM_REQUEST_DIGEST.consult():
            if digest != request_digest:
                raise _SITE_CONFIRM_REQUEST_DIGEST.fire(ValueError(
                    f"correlation_id {correlation_id!r} was already used for a "
                    f"DIFFERENT request — integrity conflict (specs/0008 §6c)"))
        row = self._conn.execute(f"SELECT {_COLS} FROM confirmations WHERE id=? AND user_id=?",
                                 (result_ref, user_id)).fetchone()
        with _SITE_REGISTRY_RESULT_MISSING.consult():
            if row is None:
                raise _SITE_REGISTRY_RESULT_MISSING.fire(ValueError(
                    f"correlation_id {correlation_id!r}: the registry names confirmation {result_ref!r}, which "
                    f"does not exist — integrity conflict (specs/0008 §6c)"))
        return self._confirmation_from_row(row).model_copy(update={"replayed": True})

    def _allocate_act_seq(self) -> int:
        """specs/0008 v7 §6f — the next act position, inside the act verb's own BEGIN IMMEDIATE. The counter's row
        is minted only at creation and by the v16 migration; a writer never re-mints it, so an ABSENT row REFUSES
        (a fresh (1, 1) would reissue positions an earlier act already holds, and exported) and the increment must
        touch exactly that one row."""
        row = self._conn.execute("SELECT next_seq FROM act_counter WHERE id=1").fetchone()
        n = (self._conn.execute("UPDATE act_counter SET next_seq=next_seq+1 WHERE id=1 AND next_seq=?",
                                (row[0],)).rowcount if row is not None else 0)
        with _SITE_ACT_COUNTER.consult():
            if row is None or n != 1:
                raise _SITE_ACT_COUNTER.fire(RuntimeError(
                    "the store's act_counter row is absent or did not advance — refusing rather than restarting "
                    "act positions (specs/0008 §6f: the counter is never reset)"))
        return row[0]

    def confirm_edge(self, user_id, edge_id, *, actor, call_path, correlation_id,
                     request_digest, confirmed_at) -> Confirmation:
        _COLS = ("id, user_id, edge_id, confirmed_at, actor, call_path, "
                 "correlation_id, request_digest")
        with self._lock, self._write_txn():
            # Idempotency, checked BEFORE any read of live edge state (specs/0008 v7 §6c, INV-Q2): the registry
            # first, so a retry replays after the edge was invalidated, retired or changed. Before v16 this read
            # `confirmations` AFTER the edge's assertability check, and such a retry raised "not assertable".
            prior = self._confirm_replay(user_id, correlation_id, request_digest)
            if prior is not None:
                return prior
            row = self._conn.execute(
                "SELECT json FROM edges WHERE id=? AND user_id=?",
                (edge_id, user_id)).fetchone()
            with _SITE_CONFIRM_UNKNOWN_EDGE.consult():
                if row is None:
                    raise _SITE_CONFIRM_UNKNOWN_EDGE.fire(UnknownEdge(
                        f"edge {edge_id!r} not found for user {user_id!r}"))
            edge = Edge.model_validate_json(row[0])
            with _SITE_CONFIRM_NOT_ASSERTABLE.consult():
                if not edge.assertable:
                    raise _SITE_CONFIRM_NOT_ASSERTABLE.fire(ValueError(
                        f"edge {edge_id!r} is not assertable (quarantined/use_only/"
                        f"inactive) — a user affirming a claim is new evidence: ingest "
                        f"it via remember(author=USER) instead"))
            # specs/0047 §4c (INV-R13): no confirmation can post-date an unresolved challenge; a `resolve` is the way
            # back. Read in THIS transaction, and only after the registry (a completed confirmation still replays
            # after a later challenge: research's T10a F3)
            with _SITE_CONFIRM_ACTIVE_CHALLENGE.consult():
                if self._open_challenge_ids(user_id, edge_id):
                    raise _SITE_CONFIRM_ACTIVE_CHALLENGE.fire(ValueError(
                        f"edge {edge_id!r} has an active challenge by the subject — it cannot be confirmed until the "
                        f"challenge is resolved (specs/0047 §4c, store.confirm.active-challenge)"))
            # specs/0045 §4d (INV-G10; the owner's R1-04 ruling, "an erased source ends the upgrade path"): a
            # `not_attested` edge whose recorded source episode is redacted cannot be confirmed — state it anew. Scoped
            # by g(e) over this edge's confirmations, read in THIS transaction (research's T9 F2), so an edge already
            # confirmed locally is not refused a re-confirmation; an `attested` edge, a legacy row (`att` NULL) and an
            # edge with no `src` keep today's confirm(). Past consolidation the source episode is gone and its
            # redaction names the OUTPUT, so the output's lineage is read too, one hop (the owner, 2026-10-18, F1(a)).
            # A source deleted outright names no episode and no lineage: confirm is allowed, stated (F1(b)).
            with _SITE_CONFIRM_SOURCE_REDACTED.consult():
                if edge.src is not None and declarative_grounding(edge, [o for (o,) in self._conn.execute(
                        "SELECT origin FROM confirmations WHERE user_id=? AND edge_id=?", (user_id, edge_id))]
                        ) == "not_attested" and self._source_redacted(user_id, edge.src):
                    raise _SITE_CONFIRM_SOURCE_REDACTED.fire(ValueError(
                        f"edge {edge_id!r} cannot be confirmed: its source episode was redacted — state it anew "
                        f"(specs/0045 §4d, store.confirm.source-redacted)"))
            edge.needs_confirmation = False
            edge.provenance = edge.provenance.model_copy(update={      # frozen Provenance (0037 v23)
                "observed_at": max(edge.provenance.observed_at, confirmed_at),
                "confidence": max(edge.provenance.confidence, 0.9)})
            cid = f"c-{uuid.uuid4().hex[:12]}"
            # ONE id for the confirmation episode, derived from the confirmation's:
            # the row and the payload it stores must agree, because every read
            # surface returns the payload's id and every lookup is by the row's. Two
            # independently minted ids left a confirmation episode that could be
            # read but never deleted, retired or reinstated by the id a consumer
            # held — the attempt found no row and reported success (found by
            # `veracium doctor` on its first run, 2026-09-12; measured by both
            # seats; fixed on the owner's word "Fix it"). No accepted spec names
            # the id; 0008 pins the summary and the transaction, which stand.
            ep_id = f"ep-{cid}"
            actor_v = ConfirmationActor(actor).value
            call_v = ConfirmationCallPath(call_path).value
            try:
                new_json = edge.model_dump_json()
                self._conn.execute("UPDATE edges SET json=? WHERE id=?",
                                   (new_json, edge_id))
                self._journal_edge_write(user_id, edge_id, new_json, row[0])
                ep_json = Episode(id=ep_id, user_id=user_id,
                                  date=confirmed_at.date().isoformat(),
                                  summary=f"({actor_v}) confirmed "
                                          f"'{edge.relation}: {edge.object}' still holds",
                                  provenance=Provenance(
                                      author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"confirm:{edge_id}")
                                  ).model_dump_json()
                ep_prior = self._conn.execute("SELECT json FROM episodes WHERE id=?", (ep_id,)).fetchone()
                self._conn.execute(
                    "INSERT OR REPLACE INTO episodes(id,user_id,date,json) "
                    "VALUES(?,?,?,?)",
                    (ep_id, user_id, confirmed_at.date().isoformat(), ep_json))
                # RII-R2-01: the id is minted above, so no prior row is expected; the rule is applied, not assumed
                self._evict_wiki_on_view_change(user_id, Episode, ep_prior[0] if ep_prior else None, ep_json)
                # an act of THIS store: origin 'local', its position from the never-reset counter (§6f), its
                # portable identity NULL — derived at each export (0008 v7 §6e)
                self._conn.execute(
                    f"INSERT INTO confirmations({_COLS}, origin, act_seq) VALUES(?,?,?,?,?,?,?,?,'local',?)",
                    (cid, user_id, edge_id, confirmed_at.isoformat(), actor_v,
                     call_v, correlation_id, request_digest, self._allocate_act_seq()))
                # the request's registry row, in the verb's own transaction (§6c); written_at is the store's clock
                # at the write — a write time for every verb, never the caller's date
                self._conn.execute(
                    "INSERT INTO request_registry(user_id, correlation_id, verb, target_edge_id, request_digest, "
                    "result_ref, written_at) VALUES(?,?,'confirm',?,?,?,?)",
                    (user_id, correlation_id, edge_id, request_digest, cid, self._now().isoformat()))
                self._bump(user_id)
            except sqlite3.IntegrityError:
                # C8: a concurrent duplicate won the UNIQUE(user_id, correlation_id)
                # race. Roll back ours and answer from the committed original through the
                # SAME registry lookup as the front path (research's N2): one rule, not two.
                self._conn.rollback()
                prior = self._confirm_replay(user_id, correlation_id, request_digest)
                with _SITE_CONFIRM_CORRELATION.consult():
                    if prior is None:
                        raise _SITE_CONFIRM_CORRELATION.fire(ValueError(
                            f"correlation_id {correlation_id!r} conflict (specs/0008 §6c)"))
                return prior
            except BaseException:
                # C7: all-or-nothing — a failure anywhere (e.g. the mandatory record
                # cannot commit) rolls back EVERY edge field and the episode, so the
                # flag stays set and no partial confirmation is left on the wire.
                self._conn.rollback()
                raise
            return Confirmation(
                id=cid, user_id=user_id, edge_id=edge_id, confirmed_at=confirmed_at,
                actor=ConfirmationActor(actor), call_path=ConfirmationCallPath(call_path),
                correlation_id=correlation_id, request_digest=request_digest)

    def undo_restoration(self, user_id: str, edge_id: str, *, correlation_id: str) -> dict:
        """specs/0044 §4i — ONE write transaction (`BEGIN IMMEDIATE`) under the instance lock: the registry decision,
        the eligibility read, the per-field restore, the outcome row and the registry row commit together or not at
        all, and a concurrent duplicate waits for the lock, then replays. The body is
        `store/data_migration.undo_restoration`, beside the restoration it reverses."""
        from .data_migration import undo_restoration as _undo
        with self._lock, self._write_txn():
            return _undo(self, user_id, edge_id, correlation_id)

    _REPLY_COLS = "id, user_id, edge_id, kind, target, text, actor, correlation_id, request_digest, written_at"

    @staticmethod
    def _reply_from_row(row) -> Reply:
        (rid, uid, eid, kind, target, text, actor, corr, dig, at) = row
        return Reply(id=rid, user_id=uid, edge_id=eid, kind=kind, target=target, text=text, actor=ReplyActor(actor),
                     correlation_id=corr, request_digest=dig, written_at=datetime.fromisoformat(at))

    def _reply_replay(self, user_id, correlation_id, request_digest) -> Optional[Reply]:
        """specs/0008 §6c/§6g, `reply`'s side of the REQUEST REGISTRY (confirm's `_confirm_replay` shape): read before
        any read of live edge state (INV-Q2). None: the id is free. Otherwise the shared rules (`_registry_held`:
        terminal, then the verb), then this verb's digest, then the original reply rebuilt from `result_ref` without
        reading the edge, so it replays after the edge was retired or changed (INV-R24)."""
        held = self._registry_held(user_id, correlation_id, "reply")
        if held is None:
            return None
        digest, result_ref = held
        with _SITE_REPLY_REQUEST_DIGEST.consult():
            if digest != request_digest:
                raise _SITE_REPLY_REQUEST_DIGEST.fire(ValueError(
                    f"correlation_id {correlation_id!r} was already used for a DIFFERENT reply request — integrity "
                    f"conflict (specs/0008 §6c)"))
        row = self._conn.execute(f"SELECT {self._REPLY_COLS} FROM replies WHERE id=? AND user_id=?",
                                 (result_ref, user_id)).fetchone()
        with _SITE_REPLY_RESULT_MISSING.consult():
            if row is None:
                raise _SITE_REPLY_RESULT_MISSING.fire(ValueError(
                    f"correlation_id {correlation_id!r}: the registry names reply {result_ref!r}, which does not "
                    f"exist — integrity conflict (specs/0008 §6c)"))
        return self._reply_from_row(row).model_copy(update={"replayed": True})

    def add_reply(self, user_id: str, edge_id: str, *, kind: str, text: Optional[str], target: Optional[str],
                  actor: ReplyActor, correlation_id: str) -> Reply:
        """specs/0047 §4a–§4b (T10a): append ONE reply, in one `BEGIN IMMEDIATE` under the instance lock, in the order
        research's stage-1 read agreed:
          (a) the request's SHAPE, which reads no state (Q5; C9's precedent): `kind` closed (INV-R8), `actor` closed,
              a target iff `resolve` and non-empty strict-UTF-8 text iff not (§4b's closed request; F1: a lone
              surrogate refuses here, never at the INSERT), and no marker in the text (INV-R7, 0041 INV-RR1);
          (b) the REQUEST REGISTRY, through the one shared lookup — terminal, then the verb, then this verb's digest;
              the same request replays (INV-Q2, INV-R24);
          (c) the EDGE, read only now: absent for this user, redacted (its own carriers show the marker OR an applied
              attestation names it: Q7's union, the 0044 sweep's predicate), or procedural (INV-R9, INV-R19). An
              inactive, quarantined or use_only edge is admitted (§2c, §3; Q8);
          (d) a resolve's TARGET: a `challenge` of the same user and edge, not yet resolved (INV-R14). The actor may
              differ from the challenge's (Q9, the owner's 2026-10-19: labels are unauthenticated until 0050);
          (e) the WRITE: the row (`origin` local, `act_seq` from the never-reset counter, `act_uid` columns NULL —
              derived at export, as for `confirmations`), its registry row, and the version bump. No episode (§1c: a
              reply must never feed ingest), no edge write and no journal event (INV-R1)."""
        actor_v = actor.value if isinstance(actor, ReplyActor) else next(
            (a.value for a in ReplyActor if isinstance(actor, str) and actor == a.value), None)
        with _SITE_REPLY_KIND.consult():
            if not (isinstance(kind, str) and kind in REPLY_KINDS):
                raise _SITE_REPLY_KIND.fire(ReplyRefused(
                    "kind", user_id, edge_id, f"kind {kind!r} is outside the closed set {REPLY_KINDS}"))
        with _SITE_REPLY_ACTOR.consult():
            if actor_v is None:
                raise _SITE_REPLY_ACTOR.fire(ReplyRefused(
                    "actor", user_id, edge_id, f"actor {actor!r} is outside {[a.value for a in ReplyActor]} — a "
                    f"reply is the subject's (or the host's on their behalf), never the assistant's or the extractor's"))
        with _SITE_REPLY_SHAPE.consult():
            problem = _reply_shape_problem(kind, text, target)
            if problem:
                raise _SITE_REPLY_SHAPE.fire(ReplyRefused("shape", user_id, edge_id, problem))
        with _SITE_REPLY_MARKER.consult():
            if text is not None and _redaction.carries_marker(text):
                raise _SITE_REPLY_MARKER.fire(ReplyRefused(
                    "marker", user_id, edge_id, "the text carries the redaction marker — a reply may not introduce it "
                    "(0041 INV-11's mirror, INV-RR1)"))
        request_digest = reply_request_digest(user_id, edge_id, kind, target, text)
        with self._lock, self._write_txn():
            prior = self._reply_replay(user_id, correlation_id, request_digest)
            if prior is not None:
                return prior
            row = self._conn.execute("SELECT json FROM edges WHERE id=? AND user_id=?", (edge_id, user_id)).fetchone()
            with _SITE_REPLY_UNKNOWN_EDGE.consult():
                if row is None:
                    raise _SITE_REPLY_UNKNOWN_EDGE.fire(ReplyRefused(
                        "unknown-edge", user_id, edge_id, "no such edge for this user"))
            with _SITE_REPLY_REDACTED_EDGE.consult():
                if (_redaction.edge_carries_marker(json.loads(row[0]))
                        or self._attested_fields(user_id, "edge", edge_id, coverage=False)):
                    raise _SITE_REPLY_REDACTED_EDGE.fire(ReplyRefused(
                        "redacted-edge", user_id, edge_id, "the edge is redacted — a new reply to it is refused "
                        "(specs/0047 §0)"))
            with _SITE_REPLY_PROCEDURAL_EDGE.consult():
                if Edge.model_validate_json(row[0]).provenance.procedural:
                    raise _SITE_REPLY_PROCEDURAL_EDGE.fire(ReplyRefused(
                        "procedural-edge", user_id, edge_id, "a reply cannot attach to a procedural record (§4d's "
                        "ruling; a procedural right of reply is deferred, §10 R6)"))
            if kind == "resolve":
                challenge = self._conn.execute("SELECT edge_id, kind FROM replies WHERE id=? AND user_id=?",
                                               (target, user_id)).fetchone()
                with _SITE_REPLY_RESOLVE_TARGET.consult():
                    if challenge is None or challenge[0] != edge_id or challenge[1] != "challenge":
                        raise _SITE_REPLY_RESOLVE_TARGET.fire(ReplyRefused(
                            "resolve-target", user_id, edge_id, f"{target!r} is not a challenge of this edge"))
                with _SITE_REPLY_RESOLVE_REPEAT.consult():
                    if self._resolved(user_id, target):
                        raise _SITE_REPLY_RESOLVE_REPEAT.fire(ReplyRefused(
                            "resolve-repeat", user_id, edge_id, f"challenge {target!r} is already resolved"))
            rid = f"r-{uuid.uuid4().hex[:12]}"
            written_at = self._now()
            try:
                self._conn.execute(
                    f"INSERT INTO replies({self._REPLY_COLS}, origin, act_seq) VALUES(?,?,?,?,?,?,?,?,?,?,'local',?)",
                    (rid, user_id, edge_id, kind, target, text, actor_v, correlation_id, request_digest,
                     written_at.isoformat(), self._allocate_act_seq()))
                self._conn.execute(
                    "INSERT INTO request_registry(user_id, correlation_id, verb, target_edge_id, request_digest, "
                    "result_ref, written_at) VALUES(?,?,'reply',?,?,?,?)",
                    (user_id, correlation_id, edge_id, request_digest, rid, written_at.isoformat()))
                # specs/0047 §4d (INV-R18): a reply write evicts the user's compiled wiki in its own transaction, so
                # no cached body compiled before it is served after it; the bump fences an in-flight compile
                self._conn.execute("DELETE FROM wiki WHERE user_id=?", (user_id,))
                self._bump(user_id)
            except sqlite3.IntegrityError:
                # C8's shape (confirm's and undo's): roll back and answer through the SAME registry lookup. Under the
                # lock and BEGIN IMMEDIATE taken before (b) and (d), only a writer that skipped them reaches here; a
                # constraint that is not the correlation id's is never reported as one (research's T10a F2): a second
                # resolve of one challenge is `resolve-repeat`, anything else re-raises unchanged
                self._conn.rollback()
                prior = self._reply_replay(user_id, correlation_id, request_digest)
                if prior is not None:
                    return prior
                with _SITE_REPLY_RESOLVE_REPEAT.consult():
                    if kind == "resolve" and self._resolved(user_id, target):
                        raise _SITE_REPLY_RESOLVE_REPEAT.fire(ReplyRefused(
                            "resolve-repeat", user_id, edge_id, f"challenge {target!r} is already resolved"))
                raise
            except BaseException:
                self._conn.rollback()
                raise
            return Reply(id=rid, user_id=user_id, edge_id=edge_id, kind=kind, target=target, text=text,
                         actor=ReplyActor(actor_v), correlation_id=correlation_id, request_digest=request_digest,
                         written_at=written_at)

    def _resolved(self, user_id: str, challenge_id: str) -> bool:
        return self._conn.execute("SELECT 1 FROM replies WHERE user_id=? AND kind='resolve' AND target=? LIMIT 1",
                                  (user_id, challenge_id)).fetchone() is not None

    def _open_challenge_ids(self, user_id: str, edge_id: str) -> list:
        """specs/0047 §4b's predicate in ONE statement: the edge's challenges that no resolve names. Only a `resolve`
        clears a challenge, and only the one it names (INV-R14); `context` text never does."""
        return [r for (r,) in self._conn.execute(
            "SELECT c.id FROM replies c WHERE c.user_id=? AND c.edge_id=? AND c.kind='challenge' AND NOT EXISTS ("
            "SELECT 1 FROM replies r WHERE r.user_id=c.user_id AND r.kind='resolve' AND r.target=c.id)",
            (user_id, edge_id))]

    def replies_for(self, user_id: str, edge_id: str) -> list[Reply]:
        with self._lock:
            return [self._reply_from_row(r) for r in self._conn.execute(
                f"SELECT {self._REPLY_COLS} FROM replies WHERE user_id=? AND edge_id=? ORDER BY written_at, id",
                (user_id, edge_id))]

    def active_challenges(self, user_id: str, edge_id: str) -> list[Reply]:
        with self._lock:
            open_ids = set(self._open_challenge_ids(user_id, edge_id))
            return [self._reply_from_row(r) for r in self._conn.execute(
                f"SELECT {self._REPLY_COLS} FROM replies WHERE user_id=? AND edge_id=? AND kind='challenge' "
                f"ORDER BY written_at, id", (user_id, edge_id)) if r[0] in open_ids]

    _OUTCOME_COLUMNS = ("plan_id", "user_id", "edge_id", "outcome", "pre_invalidated_at", "pre_reason",
                        "successor_evidence", "applicable", "origin", "outcome_uid", "undone_at", "undo_request_ref",
                        "op_id")

    def arity_plan_state(self) -> dict:
        """specs/0044 §4e: the plan header's three durable states, with the plan's id and relations (T11a)."""
        with self._lock:
            row = self._conn.execute("SELECT plan_id FROM plan_header WHERE id=1").fetchone()
            if row is None:
                return {"state": "uninitialized", "plan_id": None, "relations": frozenset()}
            rels = frozenset(r[0] for r in self._conn.execute(
                "SELECT relation FROM reclassification_plan WHERE plan_id=?", (row[0],)))
            return {"state": "initialized" if rels else "initialized-empty", "plan_id": row[0], "relations": rels}

    def migration_outcomes(self, user_id: str) -> list:
        """specs/0044 §4g: the user's outcome rows, every plan, ordered (edge_id, plan_id) (T11a's export)."""
        cols = ", ".join(self._OUTCOME_COLUMNS)
        with self._lock:
            return [dict(zip(self._OUTCOME_COLUMNS, r)) for r in self._conn.execute(
                f"SELECT {cols} FROM migration_outcome WHERE user_id=? ORDER BY edge_id, plan_id", (user_id,))]

    def migration_outcomes_by_uid(self, uids) -> dict:
        """specs/0044 §4l: held outcome rows by `outcome_uid`, store-wide (T11a's replay comparison)."""
        ids = sorted(set(uids))
        if not ids:
            return {}
        cols = ", ".join(self._OUTCOME_COLUMNS)
        with self._lock:
            return {r[9]: dict(zip(self._OUTCOME_COLUMNS, r)) for r in self._conn.execute(
                f"SELECT {cols} FROM migration_outcome WHERE outcome_uid IN ({','.join('?' * len(ids))})", ids)}

    # specs/0008 §2a / 0047 §2 (T11b): every column of an act row, per table — what export carries and what an import's
    # staged union and its commit re-check compare
    _ACT_COLUMNS = {
        "confirmations": ("id", "user_id", "edge_id", "confirmed_at", "actor", "call_path", "correlation_id",
                          "request_digest", "origin", "recorded_correlation_id", "origin_store", "origin_user",
                          "origin_act_id", "act_seq"),
        "replies": ("id", "user_id", "edge_id", "kind", "target", "text", "actor", "correlation_id", "request_digest",
                    "origin", "recorded_correlation_id", "origin_store", "origin_user", "origin_act_id", "act_seq",
                    "written_at"),
    }

    def _act_rows_where(self, where: str, params: tuple) -> list:
        out = []
        for table, cols in self._ACT_COLUMNS.items():
            out += [{"table": table, **dict(zip(cols, r))} for r in self._conn.execute(
                f"SELECT {', '.join(cols)} FROM {table} WHERE {where} ORDER BY id", params)]
        return out

    def act_rows(self, user_id: str) -> list:
        """specs/0008 §6d / 0047 §4f (T11b): every act row of the user, both tables, every column (export)."""
        with self._lock:
            return self._act_rows_where("user_id=?", (user_id,))

    def act_state(self, user_id: str, uids, positions, edge_ids) -> dict:
        """specs/0008 §6e–§6f (T11b, build note D9): what an import decides acts by, read in one window — the held rows
        of every `act_uid` and every known position (STORE-WIDE: identity and the counter span users), and the user's
        rows on every touched edge. A LOCAL act's identity and position are DERIVED (its origin columns are NULL: this
        store's `local_origin()`, its own user and id, §6e v7), so they are matched in that form too. The import's
        preflight reads it, and its commit reads it again under the lock: any difference is a lost race."""
        local = self.local_origin()
        with self._lock:
            by_uid = {}
            for u in sorted(set(uids)):
                where, params = "(origin_store=? AND origin_user=? AND origin_act_id=?)", tuple(u)
                if u[0] == local:
                    where, params = where + " OR (origin_store IS NULL AND user_id=? AND id=?)", params + (u[1], u[2])
                by_uid[u] = self._act_rows_where(where, params)
            by_pos = {}
            for p in sorted(set(positions)):
                where, params = "act_seq=? AND (origin_store=?", (p[1], p[0])
                where += " OR origin_store IS NULL)" if p[0] == local else ")"
                by_pos[p] = self._act_rows_where(where, params)
            on_edges = {e: self._act_rows_where("user_id=? AND edge_id=?", (user_id, e)) for e in sorted(set(edge_ids))}
        return {"uids": by_uid, "positions": by_pos, "by_edge": on_edges}

    def acted_edge_ids(self, user_id: str, edge_ids) -> frozenset:
        """specs/0047 §4e: the edges among `edge_ids` that carry an act — a confirmation or a reply, any kind, any
        origin. Read by the absorption planner and, in the plan's own transaction, by the store's verifier."""
        ids = sorted(set(edge_ids))
        if not ids:
            return frozenset()
        q = ",".join("?" * len(ids))
        with self._lock:          # reentrant: the verifier calls it inside the plan's own transaction
            return frozenset(e for (e,) in self._conn.execute(
                f"SELECT edge_id FROM confirmations WHERE user_id=? AND edge_id IN ({q}) "
                f"UNION SELECT edge_id FROM replies WHERE user_id=? AND edge_id IN ({q})",
                (user_id, *ids, user_id, *ids)))

    def challenge_snapshot(self, user_id: str):
        """specs/0047 §4d's ONE snapshot, in one read window: every open challenge of the user (§4b's predicate) with its
        record, ordered `(written_at, id)`; which of those records are redacted, by the attestation record (0041
        §4b-iii, never the marker bytes: a redacted record twins nothing); every confirmation's origin (0045 §4c's
        g(e)); and the ids of every edge carrying an act (§4e's collapse row). A read surface reads it once per call."""
        from ..challenge import ChallengeSnapshot, ChallengedRecord, OpenChallenge
        from ..graph import _value_key
        with self.read_window(user_id):
            rows = self._conn.execute(
                "SELECT c.edge_id, c.id, c.text, c.written_at, e.json FROM replies c JOIN edges e "
                "ON e.user_id=c.user_id AND e.id=c.edge_id WHERE c.user_id=? AND c.kind='challenge' AND NOT EXISTS ("
                "SELECT 1 FROM replies r WHERE r.user_id=c.user_id AND r.kind='resolve' AND r.target=c.id) "
                "ORDER BY c.edge_id, c.written_at, c.id", (user_id,)).fetchall()
            redacted = self.redacted_targets(user_id, "edge")
            origins: dict = {}
            for eid, origin in self._conn.execute(
                    "SELECT edge_id, origin FROM confirmations WHERE user_id=? ORDER BY edge_id, id", (user_id,)):
                origins.setdefault(eid, []).append(origin)
            acted = frozenset(e for (e,) in self._conn.execute(
                "SELECT edge_id FROM confirmations WHERE user_id=? UNION SELECT edge_id FROM replies WHERE user_id=?",
                (user_id, user_id)))
        by_edge: dict = {}
        for eid, cid, text, wat, ejson in rows:
            by_edge.setdefault(eid, (ejson, []))[1].append(OpenChallenge(cid, text, datetime.fromisoformat(wat)))
        challenged = {}
        for eid, (ejson, chs) in by_edge.items():
            e = Edge.model_validate_json(ejson)
            challenged[eid] = ChallengedRecord(e, _value_key(e.object), tuple(chs), eid in redacted)
        return ChallengeSnapshot(challenged, {k: tuple(v) for k, v in origins.items()}, acted)

    def _absorbs_an_act(self, user_id: str, plan) -> bool:
        """specs/0047 §4e (INV-R17), the store's verifier: does this plan retire as `absorbed_duplicate` a prior that
        carries an act? Read in the plan's own transaction; True makes the plan STALE (research's T10a Q13)."""
        absorbed = sorted({eid for eid, _at, r in plan.prior_invalidations if r == "absorbed_duplicate"})
        with _SITE_SUPERSESSION_ABSORB_ACTED.consult():
            return _SITE_SUPERSESSION_ABSORB_ACTED.fire(bool(absorbed) and bool(self.acted_edge_ids(user_id, absorbed)),
                                                        "plan-stale")

    def _source_redacted(self, user_id: str, episode_id: str) -> bool:
        """specs/0045 §4d: is this episode redacted here, directly or as the input of a redacted consolidation output?
        APPLIED notices only (`redacted_targets`: a pending notice redacts nothing this store holds). The output's
        `lineage` carries the HISTORICAL form of each consumed input's id (X19), matched in that form, as the
        redaction receipt matches it; one hop, since an output's inputs are never outputs' outputs (X16)."""
        redacted = self.redacted_targets(user_id, "episode")
        if episode_id in redacted:
            return True
        hist = to_historical_id(episode_id)
        return any(hist in (json.loads(js).get("lineage") or [])
                   for (js,) in self._conn.execute(
                       f"SELECT json FROM episodes WHERE user_id=? AND id IN ({','.join('?' * len(redacted))})",
                       (user_id, *sorted(redacted)))) if redacted else False

    def confirmations_for(self, user_id, edge_id) -> list[Confirmation]:
        _COLS = ("id, user_id, edge_id, confirmed_at, actor, call_path, "
                 "correlation_id, request_digest")
        rows = self._conn.execute(
            f"SELECT {_COLS} FROM confirmations WHERE user_id=? AND edge_id=? "
            f"ORDER BY confirmed_at DESC", (user_id, edge_id)).fetchall()
        return [self._confirmation_from_row(r) for r in rows]

    def _invalidate_edge_row(self, edge_id: str, at, reason: str) -> Optional[str]:
        """Retire one edge WITHOUT lock/bump/commit; returns its user_id, or None if the
        edge does not exist. Shared by `invalidate_edge` and `apply_supersession_plan`."""
        row = self._conn.execute("SELECT json, user_id FROM edges WHERE id=?", (edge_id,)).fetchone()
        if not row:
            return None
        edge = Edge.model_validate_json(row[0])
        # The instant is NORMALIZED at the sole active=0 writer: the revocation
        # path hands `at` as the operation's ISO text and `Edge` has no
        # validate_assignment, so the live object used to carry a str where
        # the journal-reconstructed twin carried a datetime (bytes equal,
        # attributes differing; a serializer warning on every revocation-
        # retired edge, reproduced in shipped 0.19.0). `as_utc_required`
        # accepts a datetime or ISO text and REFUSES anything else, so garbage
        # refuses the write (the owner, 2026-09-06: fixed as a separate item).
        edge.invalidated_at = as_utc_required(at)
        self._refuse_redacted_reason(reason, f"edge {edge_id!r}", "edge-invalidate")
        edge.invalidation_reason = reason
        new_json = edge.model_dump_json()
        self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",
                           (new_json, edge_id))
        # specs/0029 §4b: the site-determined kind (the SOLE active=0 writer);
        # an unregistered reason refuses the whole write here (V-KIND)
        self._journal_edge_write(row[1], edge_id, new_json, row[0],
                                 kind="invalidated", reason=reason)
        # specs/0004 (W1/W2, internal R2): the wiki drop lives HERE, in the sole
        # active=0 writer, so every invalidation path — present and future —
        # inherits it by construction instead of having to remember it. The
        # RETAIN-set is consulted, never a drop-list: a registered reason
        # outside it drops (§2c, fail-closed). An UNREGISTERED reason never
        # reaches this line — specs/0029 V-KIND refused the write just above.
        # The refusal-contention drops in the callers are 0003's independent,
        # reason-blind condition and remain beside this.
        if wiki_drops_on(reason):          # specs/0004 W1, the rule W9's bind shares (schema.wiki_drops_on)
            self._conn.execute("DELETE FROM wiki WHERE user_id=?", (row[1],))
        return row[1]

    def standing_revocations(self, user_id: str) -> frozenset:
        """0022 §4a: latest action per identity digest, by seq alone."""
        from .revocation import standing_revocations as _standing
        with self._lock:
            return _standing(self._conn, user_id)

    def _retire_episode_row(self, episode_id: str, at, reason: str) -> Optional[str]:
        """Retire one episode WITHOUT lock/bump/commit; returns its user_id or
        None. THE SOLE episode-retirement writer (specs/0022 R18, mirroring
        _invalidate_edge_row) — every retirement path inherits this shape."""
        row = self._conn.execute("SELECT json, user_id FROM episodes WHERE id=?",
                                 (episode_id,)).fetchone()
        if not row:
            return None
        ep = Episode.model_validate_json(row[0])
        ep.retired_at = as_utc_required(at)      # the same normalization as the edge twin
        self._refuse_redacted_reason(reason, f"episode {episode_id!r}", "episode-retire")
        ep.retired_reason = reason
        new_json = ep.model_dump_json()
        self._conn.execute("UPDATE episodes SET json=? WHERE id=?", (new_json, episode_id))
        self._evict_wiki_on_view_change(row[1], Episode, row[0], new_json)      # RII-R2-01
        return row[1]

    def _reinstate_edge_row(self, edge_id: str, *, reason: str) -> None:
        """Make a retired edge active again, journaled `reinstated` with WHY (specs/0029 v12's closed vocabulary).
        TWO callers, each passing its own constant `reason` (REQUIRED, no default — V-REINSTATE-WRITERS censuses the
        callers, so a forwarded or defaulted reason cannot hide a site): 0022's lift (`source_restored`, reversing
        OUR OWN revoked_source retirement — the sweep only emits it for rows it retired) and 0044's restoration
        (`arity_reclassified`, store/data_migration.py, a row the old single-value rule retired). The wiki drops
        too: the derived view changed in the restoring direction as surely as in the retiring one, and a stale cache
        serving the pre-lift world is the same defect mirrored."""
        row = self._conn.execute("SELECT json, user_id FROM edges WHERE id=?",
                                 (edge_id,)).fetchone()
        if not row:
            return
        edge = Edge.model_validate_json(row[0])
        # `active` is DERIVED (invalidated_at is None) — clearing the fields
        # IS the reinstatement; the column mirrors it
        edge.invalidated_at = None
        edge.invalidation_reason = None
        new_json = edge.model_dump_json()
        self._conn.execute("UPDATE edges SET active=1, json=? WHERE id=?",
                           (new_json, edge_id))
        self._journal_edge_write(row[1], edge_id, new_json, row[0], kind="reinstated",
                                 reason=reason)   # specs/0029 v12: the caller's constant (censused per caller)
        self._conn.execute("DELETE FROM wiki WHERE user_id=?", (row[1],))

    def _reinstate_episode_row(self, episode_id: str) -> None:
        row = self._conn.execute("SELECT json, user_id FROM episodes WHERE id=?",
                                 (episode_id,)).fetchone()
        if not row:
            return
        ep = Episode.model_validate_json(row[0])
        ep.retired_at = None
        ep.retired_reason = None
        new_json = ep.model_dump_json()
        self._conn.execute("UPDATE episodes SET json=? WHERE id=?", (new_json, episode_id))
        self._evict_wiki_on_view_change(row[1], Episode, row[0], new_json)      # RII-R2-01

    def _recompute_edge_row(self, edge_id: str, values: dict) -> None:
        """0022's recompute verb: the three RECOMPUTED_FIELDS, nothing else."""
        from datetime import datetime

        def _parse(ts):
            # The THIRD retire-class writer normalizes like the other two
            # (research's sweep, 2026-09-06): the sweep's values carry the
            # corpus's canonical Z suffix, but a value without Z or offset used
            # to persist NAIVE — safe only because `as_utc` takes naive as UTC
            # at every comparison. `as_utc_required` makes the parse itself
            # aware (and refuses garbage), so the safety no longer rests on the
            # comparison convention. (3.10 floor: Z is replaced before parsing.)
            # WHAT KEEPS THIS CHANGE A NO-OP for stored bytes (research, before
            # it landed): a zoneless input WOULD now persist `…Z` where it used
            # to persist `…` — and this writer's only caller, the revocation
            # sweep's effect applier, REFUSES any recompute value that is not
            # the canonical Z-suffixed UTC form (revocation_sweep.py, "not the
            # writer's canonical Z-suffixed UTC json_datetime"). The guarantee
            # lives in that caller, not here: a caller added later without that
            # refusal persists a different byte form than before this change.
            return as_utc_required(ts)

        row = self._conn.execute("SELECT json, user_id FROM edges WHERE id=?",
                                 (edge_id,)).fetchone()
        if not row:
            return
        edge = Edge.model_validate_json(row[0])
        edge.valid_from = _parse(values["valid_from"])
        edge.provenance = edge.provenance.model_copy(update={          # frozen Provenance (0037 v23)
            "observed_at": _parse(values["observed_at"]),
            "confidence": float(values["confidence"])})
        new_json = edge.model_dump_json()
        self._conn.execute("UPDATE edges SET json=? WHERE id=?",
                           (new_json, edge_id))
        # the fourth site (0030 R1-4): digest-invisible, full-state-visible
        self._journal_edge_write(row[1], edge_id, new_json, row[0])
        self._conn.execute("DELETE FROM wiki WHERE user_id=?", (row[1],))

    def _edge_in_refusal(self, user_id: str, edge_id: str) -> bool:
        """True if `edge_id` participates (as prior or incoming) in any refusal record —
        i.e. it may be a member of a live refusal contention (specs/0003 §4c-ii)."""
        return self._conn.execute(
            "SELECT 1 FROM supersession_refusals WHERE user_id=? AND "
            "(prior_edge_id=? OR incoming_edge_id=?) LIMIT 1",
            (user_id, edge_id, edge_id)).fetchone() is not None

    def invalidate_edge(self, edge_id: str, at, reason: str) -> None:
        with self._lock, self._write_txn():
            uid = self._invalidate_edge_row(edge_id, at, reason)
            if uid is None:
                return
            self._bump(uid)
            # specs/0003 §4c-ii (round-10 blocker 1): deactivating an edge that
            # participates in a refusal contention is a derived-view RESOLUTION event —
            # `correct()`/`dispute`/lifecycle can end a `live_refusal_contention` while
            # the durable refusal is retained. Drop the wiki in the SAME mutation so the
            # invalidation rule is symmetric (formation AND resolution both recompile).
            if self._edge_in_refusal(uid, edge_id):
                self._conn.execute("DELETE FROM wiki WHERE user_id=?", (uid,))

    def edges(self, user_id, *, active_only=True, subject=None, relation=None,
              include_quarantined=True) -> list[Edge]:
        with _SITE_EDGES_READ_FENCE.consult():
            q = "SELECT json FROM edges WHERE user_id=?"
            args: list = [user_id]
            if active_only:
                q += " AND active=1"
            if subject is not None:
                q += " AND subject=?"; args.append(subject)
            if relation is not None:
                q += " AND relation=?"; args.append(relation)
            if not include_quarantined:
                q += " AND quarantined=0"
            rows = self._conn.execute(q, args).fetchall()
            return _SITE_EDGES_READ_FENCE.fire([Edge.model_validate_json(r[0]) for r in rows], "fence-applied", declined=not include_quarantined)

    # -- supersession (specs/0003) ----------------------------------------
    @staticmethod
    def _logical_request_digest(plan: SupersessionPlan) -> str:
        """A fingerprint of the plan's LOGICAL intent — what it does, NOT the
        `expected_state` it assumed (which changes on a CAS recompute). The same logical
        operation replayed produces the same digest (→ replay a committed receipt); a
        genuinely different operation that reuses an `operation_id` produces a different
        digest (→ integrity conflict). §4f processing order step 1."""
        # The digest binds the COMPLETE logical persistent outcome — every field the plan
        # would persist — not a hand-picked subset. The previous form bound only
        # [id, object, author, derived_from] + structural ids, so a resubmission of the
        # same operation_id with DIFFERENT provenance (another source_id, an inflated
        # confidence, a moved observed_at) digested identically and REPLAYED silently,
        # keeping the first submission's provenance while reporting success for the
        # second — exactly the "genuinely different operation" this docstring promises
        # an integrity conflict for (0012 round-1 external review, F4). Excluded, by the
        # docstring's own rule: `expected_state` (changes on CAS recompute) and
        # `operation_id` (it is the lookup key). A verbatim retry still replays: identical
        # plan → identical serialization; the reinforcement recompute stays stable because
        # max() is idempotent.
        # specs/0016 D2: the era-faithful recomputation (0019's strip of the
        # `ungrounded` field for pre-0019 receipts) is REMOVED — a receipt
        # stamped below version 4 refuses ON SIGHT before any digest is
        # computed (no comparison branch exists), so only the CURRENT dump
        # shape is ever digested here.
        def _dump(e):
            return json.loads(e.model_dump_json())
        payload = {
            "incoming": _dump(plan.incoming_edge),
            "insert_incoming": plan.insert_incoming,
            "upserts": sorted((_dump(e) for e in plan.prior_upserts),
                              key=lambda d: d["id"]),
            "invalidations": sorted([eid, at.isoformat(), reason]
                                    for eid, at, reason in plan.prior_invalidations),
            "refusals": sorted(
                (json.loads(r.model_dump_json()) for r in plan.refusals),
                key=lambda d: (d["prior_edge_id"], d["incoming_edge_id"])),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def _outcome_digest_v2(self, plan: SupersessionPlan) -> str:
        """specs/0014 R5-2/R6-1/R9-2: the EXTENDED outcome projection — everything
        the pre-split digest bound PLUS the contribution drafts and the absorption
        pre-image, so a store-level resubmission that mutates contribution fields
        is detected (the mutation check, reachable by construction because
        store-level callers submit plans). New receipts stamp version 4 (the
        0016 D2 `source_type`-less snapshot — the 0019 rider A1): the v4
        projection IS this v2 construction computed over the post-D2 field
        set (same wrapper, reduced basis). Stored versions 1–3 were digested
        over snapshots that carried the deleted field; neither historical
        projection is computable post-D2, so those receipts refuse ON SIGHT
        at the era boundary before this function is ever called — there is no
        era-faithful recomputation and no by-version selection."""
        payload = {
            "v1": None,   # structural marker: v2/v3/v4 wrap the v1 projection
            "pre_split": self._logical_request_digest(plan),
            "contributions": sorted(
                (json.loads(d.model_dump_json()) for d in plan.contribution_drafts),
                key=lambda d: (d["site"], d["contributor_type"], d["contributor_id"])),
            "absorption_pre_image": plan.absorption_pre_image,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def validate_receipt_state(request_digest, version, response) -> None:
        """specs/0014 R9-2/R10-4: the receipt-state triple is a CLOSED
        enumerated set — (NULL, 1, NULL) legacy; (NULL, ver, json) and
        (digest, ver, json) for ver in {2, 3, 4}. Any other combination is an
        integrity error at write AND at read; the response, when present,
        must deserialize into the exact effect fields. A LEGAL pre-D2 state
        (version < 4) is still a valid stored receipt — validation passes and
        the 0016 D2 era boundary then refuses it on sight; validation itself
        computes no digest."""
        if version == 1:
            if request_digest is not None or response is not None:
                raise ValueError(
                    f"illegal receipt state ({request_digest!r}, 1, "
                    f"{'json' if response else None}) — version-1 rows are the "
                    f"migrated legacy form (NULL, 1, NULL) only (0014 R10-4)")
            return
        if version in (2, 3, 4):
            # version 3 (specs/0019 rider): the ungrounded-bearing-snapshot
            # era; version 4 (specs/0016 D2, rider A1): the source_type-less
            # era — identical receipt-state SHAPE throughout; the era
            # difference lives in the digest projection, and versions < 4
            # refuse at the boundary before any projection is computed
            if response is None:
                raise ValueError(
                    f"illegal receipt state (…, {version}, NULL) — every "
                    f"version-{version} receipt persists its effect payload "
                    f"(0014 R9-1/R10-4)")
            try:
                effects = json.loads(response)
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f"receipt response is not valid JSON (0014 R10-4): {e}") from e
            if (not isinstance(effects, dict)
                    or set(effects) != {"inserted_incoming", "invalidated",
                                        "refused"}):
                raise ValueError(
                    "receipt response does not carry exactly the effect fields "
                    "{inserted_incoming, invalidated, refused} (0014 R10-1/R10-4)")
            return
        raise ValueError(
            f"illegal outcome_digest_version {version!r} — the closed set is "
            f"{{1, 2, 3, 4}} (0014 R9-2/R10-4; 3 per the 0019 rider; 4 per "
            f"0016 D2)")

    def supersession_receipt(self, user_id: str, operation_id: str):
        """specs/0014 §4b: the phase-1 lookup surface — the receipt's request
        identity, projection version, and persisted effects, or None."""
        row = self._conn.execute(
            "SELECT logical_request_digest, status, request_digest, response, "
            "outcome_digest_version, request_digest_domain "
            "FROM supersession_operations "
            "WHERE user_id=? AND operation_id=?",
            (user_id, operation_id)).fetchone()
        if row is None:
            return None
        self.validate_receipt_state(row[2], row[4], row[3])   # flagged at read
        # specs/0025 §4b-v read rule: a domain on a digest-less receipt is a
        # row no legal writer produces — surfaced by the matrix at the
        # comparison sites (ReceiptDomainError), carried through here.
        return {"logical_request_digest": row[0], "status": row[1],
                "request_digest": row[2], "response": row[3],
                "request_digest_domain": row[5],
                "outcome_digest_version": row[4]}

    @staticmethod
    def _replay_from_effects(response_json: str):
        """R10-1: replay CONSTRUCTS its result as the persisted effect fields +
        replayed=True — effect identity from the durable carrier, runtime
        provenance from the call. Never a reconstruction from the submitted
        (and discarded) plan."""
        effects = json.loads(response_json)
        return SupersessionResult(**effects, replayed=True)

    def apply_supersession_plan(self, plan: SupersessionPlan, *,
                                authorisation=None, acting_principal=None):
        from ..contribution import (CURRENT_DIGEST_DOMAIN, effect_payload,
                                    receipt_request_matches,
                                    request_digest_under,
                                    verify_snapshot_against_plan)
        from ..schema import CorrectionAuthorisation, correction_digest
        from .base import CorrectionAuthorisationError
        inc = plan.incoming_edge
        user_id = inc.user_id
        with _SITE_SUPERSESSION_INTEGRITY.consult():
            with _SITE_CORRECTION_AUTHORISATION.consult():
                with _SITE_SUPERSESSION_PLAN.consult():
                    with self._lock, self._write_txn():
                        # 1. receipt check — PRECEDES the CAS check, so a committed op REPLAYS rather
                        #    than tripping PlanStale on its own now-stale expected_state (§4f, r9 B3),
                        #    AND precedes EVERY digest computation: the 0016 D2 era boundary fires
                        #    ON SIGHT of a stored version < 4 — no digest is computed (not even the
                        #    plan's own request digest), no comparison branch exists; the
                        #    exploding-sentinel regressions pin exactly this ordering.
                        #    PHASE 2 is REQUEST-FIRST where request identity exists on both sides
                        #    (R8-1): matching raw_request → replay the PERSISTED effects, the
                        #    submitted plan's re-planned outcome DISCARDED unconsulted (the
                        #    concurrent-preflight loser lands here); differing → conflict. The
                        #    outcome digest governs ONLY receipts/plans WITHOUT request identity —
                        #    always the v4 projection: the era gate admits no other stored version.
                        row = self._conn.execute(
                            "SELECT logical_request_digest, request_digest, response, "
                            "outcome_digest_version, request_digest_domain "
                            "FROM supersession_operations "
                            "WHERE user_id=? AND operation_id=?", (user_id, plan.operation_id)).fetchone()
                        if row is not None:
                            stored_outcome, stored_rd, stored_resp, stored_ver, stored_dom = row
                            self.validate_receipt_state(stored_rd, stored_ver, stored_resp)
                            if stored_ver < 4:
                                raise _SITE_SUPERSESSION_INTEGRITY.fire(ReceiptSchemaBoundaryError(
                                    f"operation_id {plan.operation_id!r} for user {user_id!r} "
                                    f"committed under a pre-D2 receipt era (outcome_digest_"
                                    f"version {stored_ver}): its digest basis included the "
                                    f"deleted source_type field, so no historical projection "
                                    f"is computable and this resubmission is not replay-"
                                    f"verifiable across the removal — refused on sight, no "
                                    f"digest computed, a legitimate retry indistinguishable "
                                    f"from a different request (specs/0016 D2; 0003 §4f as "
                                    f"amended)"), "receipt-era")
                        # specs/0014 §4b: a present snapshot is verified against the plan under
                        # the exhaustive field partition BEFORE any use (forged/malformed →
                        # abort); the store derives the request digest ITSELF (R7-1).
                        plan_rd = None
                        if plan.raw_request is not None:
                            try:
                                verify_snapshot_against_plan(plan.raw_request, plan)
                            except ValueError as e:
                                raise _SITE_SUPERSESSION_INTEGRITY.fire(SupersessionIntegrityError(str(e)), "digest") from e
                            plan_rd = request_digest_under(CURRENT_DIGEST_DOMAIN,
                                                           plan.raw_request)
                        digest = self._outcome_digest_v2(plan)
                        if row is not None:
                            # specs/0025 §4b-v: the cross-era matrix at the STORE site —
                            # the stored domain selects the comparison (NULL = migrated →
                            # dual-domain; a valid domain → that domain only; the
                            # fail-closed cells raise from the matrix). The pre-D2
                            # boundary above PRECEDES this — no digest logic for < 4.
                            matches = receipt_request_matches(
                                stored_rd, stored_dom,
                                plan.raw_request if plan.raw_request is not None else None)
                            if matches is not None:
                                if matches:
                                    return self._replay_from_effects(stored_resp)
                                raise _SITE_SUPERSESSION_INTEGRITY.fire(SupersessionIntegrityError(
                                    f"operation_id {plan.operation_id!r} already committed a "
                                    f"DIFFERENT request for user {user_id!r} (specs/0014 §4b "
                                    f"phase 2, request-first)"), "different-request")
                            if stored_outcome != digest:
                                raise _SITE_SUPERSESSION_INTEGRITY.fire(SupersessionIntegrityError(
                                    f"operation_id {plan.operation_id!r} already committed a DIFFERENT "
                                    f"logical operation for user {user_id!r} — a reused id is a caller "
                                    f"integrity bug, not a race (specs/0003 §4f; projection "
                                    f"v{stored_ver})"), "different-outcome")
                            # every version-4 receipt persists its effects (validated above)
                            return self._replay_from_effects(stored_resp)
                        # 2/3. CAS: revalidate the COMPLETE scope fingerprint inside the txn; stale →
                        #      PlanStale, no write, receipt NOT consumed (the caller retries).
                        scope = self.edges(user_id, subject=inc.subject, relation=inc.relation,
                                           active_only=True, include_quarantined=True)
                        if scope_fingerprint(scope) != plan.expected_state:
                            return PLAN_STALE
                        # specs/0047 §4e (INV-R17): a contributor carrying an act is never absorbed. The fingerprint
                        # above does not see acts, so this read, in THIS transaction, is what closes the plan→commit
                        # race: an act written after planning makes the plan stale, and the re-plan declines to absorb
                        # (research's T10a Q13). A plan built to absorb an acted prior never commits.
                        if self._absorbs_an_act(user_id, plan):
                            return PLAN_STALE
                        # 4. apply all-or-nothing (one transaction). ANY failure mid-apply rolls the
                        #    WHOLE plan back — no incoming edge, no prior mutations, no refusal rows,
                        #    no receipt — so there is never a durable partial state (§4f failure rule).
                        # specs/0011 §4e (E5): in-transaction verification of the
                        # correction binding — the 0014 snapshot-verification shape,
                        # FAIL CLOSED in both directions. Every `corrected` retirement
                        # requires an authorisation whose five bound elements match
                        # what THIS plan actually does; a dangling authorisation (no
                        # corrected retirement to bind) is refused too. The replay
                        # branch above returns earlier by design: a receipt exists
                        # only for a commit that already passed this check.
                        _corrected = [eid for eid, _at, r in plan.prior_invalidations
                                      if r == "corrected"]
                        if _corrected and authorisation is None:
                            raise _SITE_CORRECTION_AUTHORISATION.fire(CorrectionAuthorisationError(
                                f"plan {plan.operation_id!r} retires "
                                f"{sorted(_corrected)} as 'corrected' with no "
                                f"CorrectionAuthorisation — corrections reach storage "
                                f"only through the verified binding (specs/0011 §4e)"), "missing")
                        if authorisation is not None:
                            if type(authorisation) is not CorrectionAuthorisation:
                                raise _SITE_CORRECTION_AUTHORISATION.fire(CorrectionAuthorisationError(
                                    f"authorisation must be a CorrectionAuthorisation; "
                                    f"got {type(authorisation).__name__}"), "type")
                            if len(_corrected) != 1:
                                raise _SITE_CORRECTION_AUTHORISATION.fire(CorrectionAuthorisationError(
                                    f"an authorisation binds exactly ONE 'corrected' "
                                    f"retirement; this plan carries {len(_corrected)}"), "cardinality")
                            if authorisation.kind != "corrected":
                                raise _SITE_CORRECTION_AUTHORISATION.fire(CorrectionAuthorisationError(
                                    f"authorisation.kind={authorisation.kind!r} does "
                                    f"not authorise a 'corrected' retirement"), "kind")
                            if authorisation.prior_edge_id != _corrected[0]:
                                raise _SITE_CORRECTION_AUTHORISATION.fire(CorrectionAuthorisationError(
                                    f"authorisation is bound to prior "
                                    f"{authorisation.prior_edge_id!r} but the plan "
                                    f"retires {_corrected[0]!r} — replay against a "
                                    f"different prior refused"), "prior")
                            if authorisation.origin != self.local_origin():
                                raise _SITE_CORRECTION_AUTHORISATION.fire(CorrectionAuthorisationError(
                                    "authorisation was minted for a different store "
                                    "origin — foreign or stale mint refused"), "origin")
                            if (authorisation.replacement_digest
                                    != correction_digest(inc.object)):
                                raise _SITE_CORRECTION_AUTHORISATION.fire(CorrectionAuthorisationError(
                                    "authorisation is bound to a different replacement "
                                    "value — rebinding refused"), "replacement")
                            if authorisation.principal != acting_principal:
                                raise _SITE_CORRECTION_AUTHORISATION.fire(CorrectionAuthorisationError(
                                    f"authorisation was minted under principal "
                                    f"{authorisation.principal!r} but is being applied "
                                    f"as {acting_principal!r} — cross-principal replay "
                                    f"refused"), "principal")
                        # specs/0014 §4b: EXACT SET EQUALITY between the plan's absorption
                        # drafts and its absorbed_duplicate invalidations (R5-1) — one draft
                        # per absorbed prior, no omissions, no duplicates, no extras. Checked
                        # and written BEFORE the contributor rows are invalidated, inside this
                        # same transaction (A7: rows atomic with the op).
                        absorbed_ids = [eid for eid, _at, r in plan.prior_invalidations
                                        if r == "absorbed_duplicate"]
                        draft_ids = [d.contributor_id for d in plan.contribution_drafts
                                     if d.site == "absorption"]
                        if (sorted(absorbed_ids) != sorted(set(absorbed_ids))
                                or sorted(draft_ids) != sorted(set(draft_ids))
                                or set(absorbed_ids) != set(draft_ids)):
                            raise _SITE_SUPERSESSION_PLAN.fire(SupersessionIntegrityError(
                                f"absorption drafts {sorted(draft_ids)} != absorbed priors "
                                f"{sorted(absorbed_ids)} — the draft set must equal the "
                                f"absorbed_duplicate set exactly (specs/0014 §4b, R5-1)"), "drafts")
                        contributor_flags = [self._write_contribution(user_id, d, plan)
                                             for d in plan.contribution_drafts]
                        # specs/0021 §4c — WRITE-TIME FLATTENING, in THIS transaction:
                        # the survivor's rows gain copies of every absorbed prior's
                        # TRANSITIVELY CLOSED set, so a post-0021 survivor's row set is
                        # its whole ancestry BY CONSTRUCTION (the A→B→C chain that
                        # defeated the single-level read cannot recur on rows we write).
                        self._write_absorption_flattening(user_id, plan)
                        # specs/0019 §4d / 0014 §2c as amended (U2b): the committed
                        # survivor's `ungrounded` must be EXACTLY the N-ary OR over
                        # {the raw incoming} ∪ {every absorbed contributor} —
                        # recomputed here from the plan's full contributor set against
                        # the AUTHORITATIVE rows just read. Any other flag difference
                        # aborts. Without a snapshot (phase-2 semantics) the raw
                        # incoming flag is unknowable; the laundering direction is
                        # still fully checkable: a flagged contributor forces a
                        # flagged survivor.
                        if any(contributor_flags) and inc.ungrounded is not True:
                            raise _SITE_SUPERSESSION_PLAN.fire(SupersessionIntegrityError(
                                "a flagged contributor was absorbed but the survivor "
                                "is unflagged — the N-ary OR never launders the "
                                "signal (specs/0019 §4d; 0014 §2c as amended)"), "flag-carrier")
                        if plan.raw_request is not None:
                            expected = (bool(plan.raw_request.get("ungrounded"))
                                        or any(contributor_flags))
                            if inc.ungrounded is not expected:
                                raise _SITE_SUPERSESSION_PLAN.fire(SupersessionIntegrityError(
                                    f"survivor ungrounded={inc.ungrounded!r} is not "
                                    f"the N-ary OR of the raw submission and its "
                                    f"absorbed contributors (={expected!r}) — the "
                                    f"verifier accepts exactly that transform "
                                    f"(specs/0019; 0014 §2c as amended)"), "ungrounded")
                        for e in plan.prior_upserts:
                            self._upsert_edge_row(e)
                        for eid, at, reason in plan.prior_invalidations:
                            self._invalidate_edge_row(eid, at, reason)
                        if plan.insert_incoming:
                            self._upsert_edge_row(inc)
                        now = self._now().isoformat()
                        for d in plan.refusals:
                            # BIND the refusal: it may only reference the plan's incoming edge and
                            # an existing edge of THIS user (round-6 correction C) — a caller cannot
                            # forge a refusal against an edge this commit does not write or another
                            # tenant's.
                            if d.incoming_edge_id != inc.id:
                                raise _SITE_SUPERSESSION_PLAN.fire(ValueError(
                                    "refusal.incoming_edge_id must equal the plan's incoming edge id"), "refusal-incoming")
                            prow = self._conn.execute(
                                "SELECT user_id FROM edges WHERE id=?", (d.prior_edge_id,)).fetchone()
                            if prow is None or prow[0] != user_id:
                                raise _SITE_SUPERSESSION_PLAN.fire(ValueError(
                                    "refusal.prior_edge_id must be an existing edge of this user"), "refusal-prior")
                            # specs/0003/within-episode §4c: a draft names its rule only from the CLOSED set;
                            # absent is the ladder's RULE_VERSION, stamped here as before
                            if d.rule_version is not None and d.rule_version not in DRAFTED_RULE_VERSIONS:
                                raise _SITE_SUPERSESSION_PLAN.fire(ValueError(
                                    f"refusal.rule_version {d.rule_version!r} is not one of {DRAFTED_RULE_VERSIONS}"),
                                    "refusal-rule-version")
                            self._conn.execute(
                                "INSERT INTO supersession_refusals(refusal_id,user_id,prior_edge_id,"
                                "incoming_edge_id,relation,prior_effective,incoming_effective,"
                                "rule_version,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                                (f"ref-{uuid.uuid4().hex[:12]}", user_id, d.prior_edge_id, inc.id,
                                 d.relation, d.prior_effective, d.incoming_effective,
                                 d.rule_version or RULE_VERSION, now))
                        # the durable receipt commits atomically with the effects (§4f
                        # idempotency; 0014 R9-1/R9-2/R10-1): the persisted EFFECT payload
                        # (result minus the runtime replayed flag), the store-computed
                        # request digest (NULL when no snapshot), and the projection
                        # version stamped EXPLICITLY — never relying on the DEFAULT.
                        result = SupersessionResult(
                            inserted_incoming=plan.insert_incoming,
                            invalidated=len(plan.prior_invalidations),
                            refused=len(plan.refusals))
                        resp_json = effect_payload(result)
                        # specs/0016 D2 (0019 rider A1): post-D2 writers stamp version
                        # 4 — the source_type-less snapshot era
                        self.validate_receipt_state(plan_rd, 4, resp_json)  # refused at write
                        self._conn.execute(
                            "INSERT INTO supersession_operations(user_id,operation_id,"
                            "logical_request_digest,status,request_digest,response,"
                            "outcome_digest_version,request_digest_domain) "
                            "VALUES(?,?,?,?,?,?,?,?)",
                            (user_id, plan.operation_id, digest, "applied",
                             plan_rd, resp_json, 4,
                             # specs/0025 §4b-v, the write rule: the domain is
                             # stamped iff the receipt carries a digest — a NEW
                             # digest-less receipt stores NULL/NULL (the writer
                             # invariant, NEW WRITES ONLY).
                             CURRENT_DIGEST_DOMAIN.decode() if plan_rd is not None
                             else None))
                        self._bump(user_id)                   # a recall-bearing edge changed
                        # A live_refusal_contention transition — INTO it (this plan records a
                        # refusal) OR OUT of it (this plan retires an edge that a refusal row
                        # references) — is a derived-view invalidation event, symmetric per
                        # round-10 blocker 1. Drop the wiki cache in the SAME commit (§4c-ii,
                        # immediate not batched). The refusal rows still reference a retired
                        # member (retention is "while either edge exists"), so the resolution
                        # check reads them post-invalidation.
                        touches_contention = bool(plan.refusals) or any(
                            self._edge_in_refusal(user_id, eid)
                            for eid, _at, _reason in plan.prior_invalidations)
                        if touches_contention:
                            self._conn.execute("DELETE FROM wiki WHERE user_id=?", (user_id,))
                        return result

    def refusal_inventory_ids(self, user_id: str) -> frozenset:
        """specs/0044 §4d: the user's refusal-inventory ids (written once, by the v16 schema step)."""
        return frozenset(r[0] for r in self._conn.execute(
            "SELECT refusal_id FROM refusal_inventory WHERE user_id=?", (user_id,)).fetchall())

    def refusals(self, user_id: str) -> list[SupersessionRefusal]:
        rows = self._conn.execute(
            "SELECT refusal_id,user_id,prior_edge_id,incoming_edge_id,relation,"
            "prior_effective,incoming_effective,rule_version,created_at "
            "FROM supersession_refusals WHERE user_id=? "
            "ORDER BY created_at DESC, refusal_id DESC", (user_id,)).fetchall()
        return [SupersessionRefusal(
            refusal_id=r[0], user_id=r[1], prior_edge_id=r[2], incoming_edge_id=r[3],
            relation=r[4], prior_effective=r[5], incoming_effective=r[6],
            rule_version=r[7], created_at=r[8]) for r in rows]

    # -- the contribution ledger (specs/0014 §4a/§4b/§4d) -------------------
    def _write_contribution(self, user_id: str, draft, plan) -> None:
        """Derive and INSERT one absorption ledger row from a reference-only
        draft (R2-1), inside the consuming transaction, BEFORE the contributor
        is invalidated. Everything is read from authoritative rows; the closed
        §4a schema is validated as a self-check (a failure aborts the op, A7)."""
        with _SITE_CONTRIBUTION.consult():
            from ..contribution import (canonical_payload, evidence_ref_digest,
                                        validate_payload)
            from ..source_identity import resolve_origin, source_identity_digest
            if draft.site != "absorption":
                raise _SITE_CONTRIBUTION.fire(SupersessionIntegrityError(
                    f"site {draft.site!r} cannot appear on the supersession path — "
                    f"consolidation rows are store-derived at the cutover (0014 §4b)"), "site")
            if plan.absorption_pre_image is None:
                raise _SITE_CONTRIBUTION.fire(SupersessionIntegrityError(
                    "an absorption draft requires the plan's absorption_pre_image "
                    "(specs/0014 §4b R3-1)"), "no-pre-image")
            row = self._conn.execute(
                "SELECT json FROM edges WHERE id=?", (draft.contributor_id,)).fetchone()
            if row is None:
                raise _SITE_CONTRIBUTION.fire(SupersessionIntegrityError(
                    f"draft contributor {draft.contributor_id!r} does not resolve to a "
                    f"row this transaction is consuming (0014 §4b)"), "contributor-unresolvable")
            contributor = Edge.model_validate_json(row[0])
            if contributor.user_id != user_id:
                raise _SITE_CONTRIBUTION.fire(SupersessionIntegrityError(
                    "draft contributor belongs to another tenant (0014 §4b)"), "other-tenant")
            local = self.local_origin()
            ident = source_identity_digest(
                resolve_origin(contributor.provenance.origin, local),
                contributor.provenance.source_id)
            ev = evidence_ref_digest(
                resolve_origin(contributor.provenance.origin, local),
                contributor.provenance.evidence_ref)
            from ..contribution import json_datetime
            side = {
                "observed_at": json_datetime(contributor.provenance.observed_at),
                "confidence": contributor.provenance.confidence,
                "valid_from": json_datetime(contributor.valid_from),
                "disclosure": contributor.provenance.disclosure.value,
            }
            if contributor.provenance.derived_from is not None:
                side["derived_from"] = contributor.provenance.derived_from.value
            payload = {"base": dict(plan.absorption_pre_image), "contributor": side}
            validate_payload("absorption", payload)
            # 0021 §7b (the 0014 amendment, clause 3) / the 0019 rider: the TYPED
            # CONTRIBUTOR LINK — persisted on every new native absorption row from
            # the fields the shipped draft ALREADY carries (draft `contributor_id`
            # -> column `contributor_ref`); legacy rows stay NULL. The accepted
            # {base, contributor} payload above is NOT amended.
            self._conn.execute(
                "INSERT INTO contribution_ledger(id,user_id,survivor_type,survivor_id,"
                "site,identity_digest,evidence_ref_digest,payload,op_key,created_at,"
                "contributor_type,contributor_ref) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"contrib-{uuid.uuid4().hex[:12]}", user_id, draft.survivor_type,
                 draft.survivor_id, "absorption", ident, ev,
                 canonical_payload(payload), None, self._now().isoformat(),
                 draft.contributor_type, draft.contributor_id))
            # specs/0019: the contributor's authoritative flag feeds the caller's
            # N-ary OR verification (U2b) — read from the row this transaction is
            # consuming, never from the draft.
            return contributor.ungrounded

    def _write_absorption_flattening(self, user_id: str, plan) -> None:
        """specs/0021 §4c / §7b SITE MATRIX row 2 — the NATIVE flattened
        copies, written by `apply_supersession_plan` inside the SAME atomic
        plan as the absorption itself.

        For every absorption draft: the prior's TRANSITIVELY CLOSED row set
        (never its direct rows — a legacy prior's direct rows may themselves
        be unclosed, and flattening an unclosed set would mint one that merely
        LOOKS closed) is copied onto the survivor at the `scope-attribution`
        site with payload EXACTLY `{"flattened": true}` and the NATIVE per-row
        key form (`native_row_op_key`: the shipped op id is `sup-{edge.id}`
        with an unrestricted suffix, so it is FRAMED INTO the digest rather
        than used as a prefix). The DIRECT contributor keeps its accepted
        native `absorption` row, `{base, contributor}` payload untouched.

        TWO store-side gates, because a rail that lives only in the planner is
        a rail the atomic primitive does not have (0014 A7's posture):

        1. the prior's closure must EXIST — a None closure is UNRESOLVED and
           §4c forbids absorbing it; the whole op aborts;
        2. the prior's membership evidence must EQUAL the survivor's own —
           the same-scope requirement, re-derived here from authoritative rows
           rather than trusted from the plan.

        Rows are DERIVED here, never carried in the plan: the plan's outcome
        digest (0014 R5-2, projection v4) binds caller-supplied fields, and a
        new plan member would either change that projection for every existing
        receipt or ride along unbound. The store derives and validates; the
        caller references (0014 §4b R2-1)."""
        with _SITE_FLATTENING.consult():
            drafts = [d for d in plan.contribution_drafts if d.site == "absorption"]
            if not drafts:
                return
            from ..contribution import canonical_payload
            from ..scope import (SITE_ATTRIBUTION, UNRESOLVED, ScopeError,
                                 construct_plan_row)
            from ..scope_read import MembershipResolver
            resolver = MembershipResolver(self, user_id)
            survivor = plan.incoming_edge
            own_evidence = resolver.evidence_of_unwritten(survivor)
            if own_evidence == UNRESOLVED:
                raise _SITE_FLATTENING.fire(SupersessionIntegrityError(
                    f"survivor {survivor.id!r} presents UNRESOLVED membership "
                    f"evidence — specs/0021 §4c: it absorbs nothing (fail closed)"), "survivor-unresolved")
            now = self._now().isoformat()
            written: set = set()
            for d in drafts:
                copies = resolver.flattening_plan(d.contributor_type,
                                                  d.contributor_id)
                if copies is None:
                    raise _SITE_FLATTENING.fire(SupersessionIntegrityError(
                        f"absorbed prior {d.contributor_id!r} has NO transitively "
                        f"closed absorption row set (UNRESOLVED) — specs/0021 §4c: "
                        f"such a prior never absorbs or is absorbed, and a survivor "
                        f"cannot flatten a set that does not close"), "no-closure")
                prow = self._conn.execute(
                    "SELECT json FROM edges WHERE id=?",
                    (d.contributor_id,)).fetchone()
                if prow is None:
                    raise _SITE_FLATTENING.fire(SupersessionIntegrityError(
                        f"absorbed prior {d.contributor_id!r} does not resolve to "
                        f"a row this transaction is consuming (0014 §4b)"), "prior-unresolvable")
                evidence = resolver.evidence(Edge.model_validate_json(prow[0]))
                if evidence == UNRESOLVED or evidence != own_evidence:
                    raise _SITE_FLATTENING.fire(SupersessionIntegrityError(
                        f"absorbed prior {d.contributor_id!r} presents membership "
                        f"evidence {evidence!r}, the survivor {own_evidence!r} — "
                        f"specs/0021 §4c/W2: absorption never crosses a scope "
                        f"boundary, and the atomic primitive refuses it "
                        f"independently of the planner"), "membership-differs")
                for c in copies:
                    ref = c["contributor_ref"]
                    if ref in written or ref == d.contributor_id:
                        continue          # one row per contributor: the direct
                                          # link is the native row, and a ref can
                                          # have only one absorber (the closure
                                          # refuses two), so this only ever
                                          # collapses a re-reached DAG node
                    written.add(ref)
                    try:
                        row = construct_plan_row(
                            "native", plan.operation_id, d.survivor_id,
                            site=SITE_ATTRIBUTION,
                            identity_digest=c["identity_digest"],
                            evidence_ref_digest=c["evidence_ref_digest"],
                            contributor_ref=ref, payload={"flattened": True})
                    except ScopeError as e:
                        raise _SITE_FLATTENING.fire(SupersessionIntegrityError(
                            f"the flattened attribution row for contributor "
                            f"{ref!r} does not satisfy the 0009 §4c writer "
                            f"contract: {e}"), "row-invalid") from e
                    self._conn.execute(
                        "INSERT INTO contribution_ledger(id,user_id,survivor_type,"
                        "survivor_id,site,identity_digest,evidence_ref_digest,"
                        "payload,op_key,created_at,contributor_type,"
                        "contributor_ref) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (f"contrib-{uuid.uuid4().hex[:12]}", user_id,
                         d.survivor_type, d.survivor_id, SITE_ATTRIBUTION,
                         row["identity_digest"], row["evidence_ref_digest"],
                         canonical_payload(row["payload"]), row["op_key"], now,
                         row["contributor_type"], ref))

    def _write_consolidation_contributions(self, op) -> None:
        """specs/0014 §4b/§4c: the N×M rows at the OUTPUTS_DURABLE cutover —
        every claimed input × every written output, derived wholly by the store
        (the claimed set and the bound outputs are both store-known, so the set
        is exact by construction). Runs INSIDE the cutover transaction, while
        the claimed inputs are still readable. Idempotent under recovery via the
        persisted op_key (R2-2): a key hit VERIFIES field-for-field (R3-3) —
        a true retry no-ops, any mismatch aborts."""
        from ..contribution import (canonical_payload, consolidation_op_key,
                                    evidence_ref_digest, validate_payload)
        from ..source_identity import resolve_origin, source_identity_digest
        bound = [ep for _, ep in
                 self._episodes_for_operation(op.user_id, op.operation_id)
                 if ep.lineage]
        outputs = list(enumerate(bound))   # index over OUTPUTS only, write order
        local = self.local_origin()
        now = self._now().isoformat()
        with _SITE_CONSOLIDATION_CONTRIBUTION.consult():
            for _, out_ep in outputs:
                idx = out_ep.consolidation_output_index
                if idx is None:
                    raise _SITE_CONSOLIDATION_CONTRIBUTION.fire(SupersessionIntegrityError(
                        f"output {out_ep.id!r} reached the cutover without a "
                        f"store-assigned index (0014 §4c)"), "no-index")
                for eid in op.claimed_ids:
                    row = self._conn.execute(
                        "SELECT json FROM episodes WHERE id=? AND user_id=?",
                        (eid, op.user_id)).fetchone()
                    if row is None:
                        raise _SITE_CONSOLIDATION_CONTRIBUTION.fire(SupersessionIntegrityError(
                            f"claimed input {eid!r} vanished before the cutover — the "
                            f"N×M contribution set cannot be complete (0014 §4b/A7)"), "input-vanished")
                    inp = Episode.model_validate_json(row[0])
                    ident = source_identity_digest(
                        resolve_origin(inp.provenance.origin, local),
                        inp.provenance.source_id)
                    ev = evidence_ref_digest(
                        resolve_origin(inp.provenance.origin, local),
                        inp.provenance.evidence_ref)
                    from ..contribution import json_datetime
                    side = {
                        "observed_at": json_datetime(inp.provenance.observed_at),
                        "confidence": inp.provenance.confidence,
                        "disclosure": inp.provenance.disclosure.value,
                        "author_of_evidence": inp.provenance.author_of_evidence.value,
                        "date": inp.date,
                    }
                    if inp.provenance.derived_from is not None:
                        side["derived_from"] = inp.provenance.derived_from.value
                    payload = {"input": side, "output_index": idx}
                    validate_payload("consolidation", payload)
                    key = consolidation_op_key(op.operation_id, idx, "episode", eid)
                    canon = canonical_payload(payload)
                    existing = self._conn.execute(
                        "SELECT user_id,survivor_type,survivor_id,site,identity_digest,"
                        "evidence_ref_digest,payload FROM contribution_ledger "
                        "WHERE op_key=?", (key,)).fetchone()
                    if existing is not None:
                        # R3-3: a conflict VERIFIES, never ignores — append-only (A8)
                        want = (op.user_id, "episode", out_ep.id, "consolidation",
                                ident, ev, canon)
                        if tuple(existing) != want:
                            raise _SITE_CONSOLIDATION_CONTRIBUTION.fire(SupersessionIntegrityError(
                                f"op_key {key!r} exists with DIFFERENT deterministic "
                                f"fields — a mis-keyed second output would lose its "
                                f"attribution invisibly (0014 §4a R3-3)"), "op-key-conflict")
                        continue
                    # The contributor columns stay NULL here: the 0021 §7b typed link
                    # is scoped to the draft-carried plan/absorption sites, and the
                    # R3-3 verify above compares the deterministic fields of PRE-v8
                    # rows — a recovered op resuming across the v7→v8 migration must
                    # keep matching its own legacy rows (NULL) field-for-field.
                    self._conn.execute(
                        "INSERT INTO contribution_ledger(id,user_id,survivor_type,"
                        "survivor_id,site,identity_digest,evidence_ref_digest,payload,"
                        "op_key,created_at,contributor_type,contributor_ref) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (f"contrib-{uuid.uuid4().hex[:12]}", op.user_id, "episode",
                         out_ep.id, "consolidation", ident, ev, canon, key, now,
                         None, None))

    @staticmethod
    def _contribution_record(r):
        import json as _json
        from ..schema import ContributionRecord
        return ContributionRecord(
            id=r[0], user_id=r[1], survivor_type=r[2], survivor_id=r[3],
            site=r[4], identity_digest=r[5], evidence_ref_digest=r[6],
            payload=_json.loads(r[7]), op_key=r[8], created_at=r[9],
            contributor_type=r[10], contributor_ref=r[11])

    _CONTRIB_COLS = ("id,user_id,survivor_type,survivor_id,site,identity_digest,"
                     "evidence_ref_digest,payload,op_key,created_at,"
                     "contributor_type,contributor_ref")

    def contributions(self, user_id: str, survivor_type: str,
                      survivor_id: str) -> list:
        """§4d: every contributor consumed into a survivor, newest first —
        type-keyed (R1-5: an Edge and an Episode sharing a raw id never merge)."""
        rows = self._conn.execute(
            f"SELECT {self._CONTRIB_COLS} FROM contribution_ledger "
            "WHERE user_id=? AND survivor_type=? AND survivor_id=? "
            "ORDER BY created_at DESC, id DESC",
            (user_id, survivor_type, survivor_id)).fetchall()
        return [self._contribution_record(r) for r in rows]

    def contributions_naming(self, user_id: str, contributor_ref: str) -> list:
        """specs/0021 §7b: every ledger row whose typed `contributor_ref`
        NAMES the given record — the export path's reverse join
        (`derive_absorbed_by`). Pre-v8 rows carry NULL `contributor_ref` and
        never match (the disclosed legacy class)."""
        # typed (round 10, sweep B): every caller names an EDGE, and edges and episodes are independent id
        # namespaces in this table — a raw-ref match could attribute another kind's row to the edge
        rows = self._conn.execute(
            "SELECT survivor_type,survivor_id,site,payload,contributor_ref "
            "FROM contribution_ledger WHERE user_id=? AND contributor_type='edge' AND contributor_ref=? "
            "ORDER BY created_at DESC, id DESC",
            (user_id, contributor_ref)).fetchall()
        return [{"survivor_type": r[0], "survivor_id": r[1], "site": r[2],
                 "payload": json.loads(r[3]), "contributor_ref": r[4]}
                for r in rows]

    def contributors_of_source(self, user_id: str, identity_digest: str) -> list:
        """§4d: every survivor a source contributed to — revoke_source's
        blast-radius join (A9). COMPLETE identities only: a NULL digest never
        joins (F1/I13), enforced by the NOT-NULL bind here."""
        if identity_digest is None:
            return []
        rows = self._conn.execute(
            f"SELECT {self._CONTRIB_COLS} FROM contribution_ledger "
            "WHERE user_id=? AND identity_digest=? "
            "ORDER BY created_at DESC, id DESC",
            (user_id, identity_digest)).fetchall()
        return [self._contribution_record(r) for r in rows]

    def _drop_contributions_for_survivor(self, user_id: str, survivor_type: str,
                                         survivor_id: str) -> None:
        """A10: a ledger row is kept while its survivor exists and dropped when
        the survivor is — type-keyed, so a same-raw-id Edge/Episode pair deletes
        independently (R1-5)."""
        self._conn.execute(
            "DELETE FROM contribution_ledger WHERE user_id=? AND survivor_type=? "
            "AND survivor_id=?", (user_id, survivor_type, survivor_id))

    # -- episodes ----------------------------------------------------------
    def add_episode(self, episode: Episode) -> None:
        # specs/0041 §4b (INV-11's mirror) and §2d-iv (the kind closure), at the WRITE
        # path only: a stored prose kind still loads (the read path never refuses).
        with _SITE_EPISODE_MARKER.consult():
            hit = _redaction.marker_fields(episode.model_dump(mode="json"))
            if hit:
                raise _SITE_EPISODE_MARKER.fire(ValueError(
                    f"refused: episode {episode.id!r} would introduce the redaction marker in "
                    f"{hit} — only a redaction writes the marker (specs/0041 §4b, INV-11's mirror)"))
        # specs/0041 §11.2 / D1 (round 10, R9-02(b)): a PRESENT `Episode.retired_reason` must be registered; None
        # (an active episode) stays valid
        self._refuse_redacted_reason(episode.retired_reason, f"episode {episode.id!r}", "episode-write")
        with _SITE_EPISODE_RETIRED_REASON.consult():
            if episode.retired_reason is not None and episode.retired_reason not in DISPOSITIONED_REASONS:
                raise _SITE_EPISODE_RETIRED_REASON.fire(ValueError(
                    f"refused: episode {episode.id!r} carries retired reason {episode.retired_reason!r}, which is not "
                    f"a registered reason {tuple(DISPOSITIONED_REASONS)} (specs/0041 §11.2, D1)"))
        with _SITE_EPISODE_KIND.consult():
            if episode.kind not in _redaction.RECOGNISED_EPISODE_KINDS:
                raise _SITE_EPISODE_KIND.fire(ValueError(
                    f"refused: episode {episode.id!r} kind {episode.kind!r} is not a recognised "
                    f"operational kind {_redaction.RECOGNISED_EPISODE_KINDS} — the set is closed at the "
                    f"write path (specs/0041 §2d-iv, §4h(ii))"))
        # specs/0014 §4c: store-assigned identity cannot be fabricated — a
        # caller-supplied consolidation_output_index on the generic path is
        # REFUSED; only write_consolidation_output_if_current assigns it.
        with _SITE_ADD_EPISODE.consult():
            if episode.consolidation_output_index is not None:
                raise _SITE_ADD_EPISODE.fire(ValueError(
                    f"add_episode refuses episode {episode.id!r} with a "
                    f"caller-supplied consolidation_output_index — the index is "
                    f"store-assigned by the consolidation primitive only "
                    f"(specs/0014 §4c)"), "output-index")
            # specs/0009 H14: outcome-chain rows carry append-only trust state (seq,
            # supersedes_episode, authorship) and may enter ONLY through the sanctioned
            # writers — `append_outcome_if_head` (runtime) or `commit_outcome_import_plan`
            # (import) — never the generic, replace-capable mutator. This refusal is the
            # fence: it closes caller-minted seqs, head-siblings, AND an INSERT-OR-REPLACE
            # of an existing outcome id (the unfenced-door class, cf. 0010 X21).
            if episode.kind == "outcome":
                raise _SITE_ADD_EPISODE.fire(ValueError(
                    f"add_episode refuses kind=='outcome' episode {episode.id!r} — "
                    f"outcome-chain links enter only via append_outcome_if_head or "
                    f"commit_outcome_import_plan (specs/0009 H14)"), "outcome-kind")
            # specs/0010 X18: the generic mutator cannot FABRICATE claimed/provisional/output
            # state — those fields are store-minted by the fenced consolidation primitives.
            if (episode.claimed_by is not None or episode.operation_id is not None
                    or episode.lineage):
                raise _SITE_ADD_EPISODE.fire(ValueError(
                    f"add_episode refuses episode {episode.id!r} carrying consolidation "
                    f"state (claimed_by/operation_id/lineage) — that state is minted only "
                    f"by the fenced consolidation primitives (specs/0010 X18)"), "consolidation-fields")
            # specs/0010 X19: a LIVE episode id can never inhabit the historical namespace
            # that finalized lineage ids live in, so the two can never collide.
            if is_historical_id(episode.id):
                raise _SITE_ADD_EPISODE.fire(ValueError(
                    f"add_episode refuses id {episode.id!r} — the '{episode.id[:5]}' "
                    f"namespace is reserved for historical lineage ids (specs/0010 X19)"), "historical-id")
            # specs/0041 round 9 R9-01: the decisions about the STORED state — the attestation (INV-11)
            # and the X21 reservation — are made under BEGIN IMMEDIATE on this connection, in the SAME
            # transaction as the write. Before, both were read before the write's transaction began (the
            # instance lock serialises only this connection), so a second connection's redaction or claim
            # committing in between was overwritten. The checks above read only the argument and stay outside.
            with self._lock, self._write_txn():
                # RII-R3-01 (the specs/0008 §6d ownership guard, the edge writer's shape): an episode's `user_id`
                # never changes through a same-ID replacement — the Store protocol's add_episode obligation, which
                # the assertion view's KEEP reason for `user_id` cites. Compared against the PERSISTED row, inside
                # the write's transaction: a replacement under another owner left the former owner's cached wiki
                # asserting an input it no longer held, and the eviction and bump below addressed only the newcomer.
                prior = self._conn.execute("SELECT user_id, json FROM episodes WHERE id=?", (episode.id,)).fetchone()
                with _SITE_ADD_EPISODE_OWNER.consult():
                    if prior is not None and prior[0] != episode.user_id:
                        raise _SITE_ADD_EPISODE_OWNER.fire(ValueError(
                            f"cannot change episode {episode.id!r}'s user_id "
                            f"({prior[0]!r} → {episode.user_id!r}) — ownership is not "
                            f"transferable through add_episode (specs/0008 §6d's guard)"), "user-id")
                # The two stored-state refusals below key on the ID, never on the incoming writer's user_id: ids are
                # unique across the store, and the state they consult can outlive the row it names (an owner's
                # deleted-but-redacted episode; an op's deleted-but-reserved input), where the guard above has no
                # row to compare. INV-11's WRITE refusal only — the readers stay per user (N1, RULED 2026-10-23).
                with _SITE_EPISODE_ATTESTED.consult():
                    attested = self._attested_fields(_ANY_OWNER, "episode", episode.id, coverage=False)
                    if attested:
                        raise _SITE_EPISODE_ATTESTED.fire(ValueError(
                            f"refused: episode {episode.id!r} is redacted — a redaction record attests "
                            f"{sorted(attested)}; an ordinary write may not repopulate it (specs/0041 §4b-ii, INV-11)"))
                # specs/0010 X21: an id RESERVED by a non-quiescent op is refused — the
                # reservation survives the input's physical deletion until the op finalizes
                # or cleanly abandons (so a deleted-but-reserved id cannot be recreated),
                # by ANY op, whoever owns it (research's B1: per owner, another user took it).
                if self._id_reserved(episode.id):
                    raise _SITE_ADD_EPISODE.fire(ValueError(
                        f"add_episode refuses reserved id {episode.id!r} — it is claimed by "
                        f"an in-flight consolidation (specs/0010 X21)"), "reserved-id")
                new_json = episode.model_dump_json()
                self._conn.execute(
                    "INSERT OR REPLACE INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                    (episode.id, episode.user_id, episode.date, new_json))
                self._evict_wiki_on_view_change(episode.user_id, Episode, prior[1] if prior else None, new_json)
                self._bump(episode.user_id)

    def episodes(self, user_id, *, limit=None,
                 include_retired=False) -> list[Episode]:
        # specs/0010 X9: every ordinary read sees EXACTLY ONE complete representation —
        # all relevant inputs, or all committed outputs, never both and never neither.
        # The episode rows and the op states are read in ONE snapshot (under the lock),
        # and provisional/hidden rows are filtered by the observed op state.
        with self._lock:
            op_state = {op.operation_id: op.state
                        for op in self._ops_for_user(user_id)}
            rows = self._conn.execute(
                "SELECT json FROM episodes WHERE user_id=? ORDER BY date",
                (user_id,)).fetchall()
        out = []
        for (blob,) in rows:
            ep = Episode.model_validate_json(blob)
            # specs/0022 R18: retired episodes are DEFAULT-EXCLUDED at the one
            # read seam, so all readers inherit the exclusion — the JSON-field
            # stand-in for the SQL guarantee a column would have given (§4b-ii)
            if ep.retired_reason is not None and not include_retired:
                continue
            if self._ordinary_read_visible(ep, op_state):
                out.append(ep)
                if limit and len(out) >= limit:
                    break
        return out

    @staticmethod
    def _ordinary_read_visible(ep: Episode, op_state: dict) -> bool:
        """specs/0010 §4c/X9. A provisional OUTPUT is hidden while its LOCAL op is
        pre-cutover (CLAIMED/GENERATING); a finalized/absent-op output is visible (X19).
        A claimed INPUT is hidden once its op reaches OUTPUTS_DURABLE (the cutover flips
        visibility); it is visible while CLAIMED/GENERATING. Everything else is visible."""
        S = ConsolidationState
        with _SITE_READ_OUTPUT_NOT_VISIBLE.consult():
            if ep.lineage:                                   # a consolidation OUTPUT
                return _SITE_READ_OUTPUT_NOT_VISIBLE.fire(op_state.get(ep.operation_id) not in (S.CLAIMED, S.GENERATING), "withhold")
        with _SITE_READ_INPUT_CLAIMED.consult():
            if ep.operation_id is not None:                  # a claimed INPUT
                return _SITE_READ_INPUT_CLAIMED.fire(op_state.get(ep.operation_id) is not S.OUTPUTS_DURABLE, "withhold")
        return True

    def delete_episode(self, episode_id) -> None:
        with self._lock:
            row = self._conn.execute(
                "SELECT user_id, json FROM episodes WHERE id=?",
                (episode_id,)).fetchone()
            # specs/0009 H14: an outcome-chain link leaves ONLY via forget_user
            # (wholesale erasure) — never a targeted delete, which would punch a
            # gap in append-only history or orphan a superseding child.
            with _SITE_DELETE_EPISODE_OUTCOME.consult():
                if row is not None and Episode.model_validate_json(row[1]).kind == "outcome":
                    raise _SITE_DELETE_EPISODE_OUTCOME.fire(ValueError(
                        f"delete_episode refuses outcome-chain link {episode_id!r} — "
                        f"outcome history is append-only and leaves only via forget_user "
                        f"(specs/0009 H14)"))
            # specs/0010 X21: a reserved (claimed) input leaves only via the fenced
            # batch-delete or forget_user — never a targeted generic delete.
            with _SITE_DELETE_EPISODE_RESERVED.consult():
                if row is not None and episode_id in self._reserved_ids(row[0]):
                    raise _SITE_DELETE_EPISODE_RESERVED.fire(ValueError(
                        f"delete_episode refuses reserved id {episode_id!r} — it is claimed "
                        f"by an in-flight consolidation; it is removed only by the fenced "
                        f"batch-delete or forget_user (specs/0010 X21)"))
            self._conn.execute("DELETE FROM episodes WHERE id=?", (episode_id,))
            if row:
                self._evict_wiki_on_view_change(row[0], Episode, row[1], None)      # RII-R2-01: a drawn input erased
                # specs/0014 A10: rows live while their survivor does — type-keyed
                self._drop_contributions_for_survivor(row[0], "episode", episode_id)
                self._bump(row[0])
            self._conn.commit()

    # -- outcome-authorship chain (specs/0009) ----------------------------------
    def _chain_head(self, user_id: str, edge_id: str, evidence_ref: str):
        """The head (max-`seq` episode) of the `(edge_id, evidence_ref)` outcome
        chain, or None. Derived — there is no materialised head pointer (H-Q2)."""
        head = None
        for r in self._conn.execute(
                "SELECT json FROM episodes WHERE user_id=?", (user_id,)):
            ep = Episode.model_validate_json(r[0])
            if (ep.kind == "outcome" and ep.edge_id == edge_id
                    and ep.provenance.evidence_ref == evidence_ref):
                if head is None or (ep.seq or 0) > (head.seq or 0):
                    head = ep
        return head

    def append_outcome_if_head(self, user_id, edge_id, evidence_ref,
                               expected_head_id, draft: OutcomeJudgmentDraft):
        """specs/0009 §4a. Atomic under `_lock` (which serialises every store
        mutation on the single connection), so the read-then-INSERT is a genuine
        compare-and-set: two concurrent callers cannot both extend one head (H3).
        INSERTs through its OWN statement, not `add_episode`, so it is a sanctioned
        outcome-chain writer even once the generic mutators refuse outcome rows (H14).

        0041 round 10 (found while fixing A3): the instance lock serialises ONE connection, so across two the head
        read and the INSERT were not one compare-and-set. Both now run under BEGIN IMMEDIATE on this connection (and
        join a caller's `atomic()` transaction when one is open)."""
        with self._lock, self._write_txn():
            head = self._chain_head(user_id, edge_id, evidence_ref)
            head_id = head.id if head is not None else None
            if head_id != expected_head_id:
                return HEAD_MOVED                       # CAS failed — caller retries
            if head is None:                            # a new chain: root
                seq, context_ref = 1, draft.context_ref
            else:
                seq = (head.seq or 0) + 1               # contiguous per-chain seq
                # context_ref: omitted → inherit; non-None must equal the chain's
                with _SITE_OUTCOME_CONTEXT_REF.consult():
                    if draft.context_ref is None:
                        context_ref = head.context_ref
                    elif draft.context_ref != head.context_ref:
                        raise _SITE_OUTCOME_CONTEXT_REF.fire(ValueError(
                            "context_ref may not change within an outcome chain "
                            f"({draft.context_ref!r} != {head.context_ref!r})"))
                    else:
                        context_ref = draft.context_ref
            ep = Episode(
                id=f"ep-{uuid.uuid4().hex[:12]}", user_id=user_id,
                date=draft.event_timestamp, summary=draft.summary, kind="outcome",
                edge_id=edge_id, outcome=draft.outcome, context_ref=context_ref,
                seq=seq, supersedes_episode=expected_head_id,
                judgment_time_known=True,
                provenance=Provenance(
                    author_of_evidence=draft.author, evidence_ref=evidence_ref))
            self._conn.execute(
                "INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                (ep.id, ep.user_id, ep.date, ep.model_dump_json()))
            self._bump(user_id)                          # H10
            return ep                                    # _write_txn commits (or the caller's atomic() does)

    def commit_outcome_import_plan(self, user_id, plan: dict,
                                   expected_destination_state: dict):
        """specs/0009 §4c. Atomic under `_lock` — the same single-connection
        serialisation that makes `append_outcome_if_head` a genuine CAS makes this
        whole-import commit LINEARIZE against concurrent appends: a head that moved
        between the caller's preflight and here is caught by the `chain_heads`
        re-check and the WHOLE import refuses (`DESTINATION_CHANGED`), never after a
        prefix. Installs outcome links through its OWN INSERT — a sanctioned writer
        even though the generic mutators now refuse outcome rows (H14).

        specs/0009 §4c AS AMENDED (0020/0021): `plan["contributions"]` rows —
        derived by the caller SOLELY from `reconstruct_absorption_rows`,
        pre-commit — are validated context-aware ("import" is the ONLY writer
        context this primitive owns), their op keys and row ids RE-DERIVED
        in-primitive (a caller-selected key or id refuses before any write),
        gated by `expected_destination_state["contribution_state"]`
        (absent → write; plan_row_id-set-equal → skip-as-existing; anything
        else → DESTINATION_CHANGED writing nothing), and installed in the SAME
        single atomic commit as the records."""
        with _SITE_IMPORT_PLAN.consult():
            from ..contribution import canonical_payload, validate_payload
            from ..scope_linkage import plan_row_id as _derive_row_id
            edges = plan.get("edges", [])
            episodes = plan.get("episodes", [])
            contributions = plan.get("contributions", [])
            # (0) validate the contribution row-plans — pure derivation checks,
            # before the lock and before ANY write. Presence first (R11-2), then
            # the ONE-minted-op rule, then the exact in-primitive derivation of
            # op_key AND row id (R13-1: keys are derived, never selected — the
            # validator inside plan_row_id consumes the op domain and requires
            # exact key equality; the id equality below closes the same door for
            # the PRIMARY-KEY-riding dedup identity).
            plan_edge_ids = {e.id for e in edges}
            contrib_by_surv: dict = {}
            import_op = None
            for row in contributions:
                missing = [f for f in ("id", "user_id", "survivor_type",
                                       "survivor_id", "op_key") if f not in row]
                if missing:
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"contribution row-plan is missing {missing} — the plan "
                        f"row is TOTAL over the stored field set (0009 §4c as "
                        f"amended, R11-2)"), "missing-rows")
                if row["user_id"] != user_id:
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        "contribution row-plan names another tenant — refused "
                        "(0009 §4c as amended)"), "other-tenant")
                if row["survivor_type"] != "edge":
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"contribution row-plan survivor_type "
                        f"{row['survivor_type']!r} — the import plan sites "
                        f"attribute EDGE survivors only (0020 §4a-iii)"), "survivor-type")
                op_key = row["op_key"]
                if not isinstance(op_key, str) or ":" not in op_key:
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"contribution row op_key {op_key!r} is not the "
                        f"injective {{op}}:{{site}}:{{digest}} form (R9-2)"), "op-key-shape")
                op = op_key.split(":", 1)[0]
                if import_op is None:
                    import_op = op
                elif op != import_op:
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"contribution rows carry TWO operation ids "
                        f"({import_op!r}, {op!r}) — the import mints ONE "
                        f"op-<12hex> id (0009 §4c as amended, R7-3)"), "two-operations")
                derived_id = _derive_row_id(user_id, "edge", row["survivor_id"],
                                            row, "import", op=op)
                if row["id"] != derived_id:
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"contribution row id {row['id']!r} is not the canonical "
                        f"plan_row_id projection — the id is DERIVED in-primitive, "
                        f"never selected (0009 §4c as amended, R9-3/R13-1)"), "row-id")
                validate_payload(row["site"], row["payload"])   # site registry
                contrib_by_surv.setdefault(row["survivor_id"], []).append(row)
            # specs/0041 §4g (tranche 4b): the import's redaction NOTICES — validated in full before the lock
            # (an invalid notice refuses the whole plan: the record-and-notice UNIT is never admitted
            # un-redacted), applied INSIDE the same transaction as the records below.
            notices = plan.get("redactions", [])
            # the MODE (specs/0041 §11.6.6's table): `notice_scope="any"` is a trusted restore (specs/0005: the operator's
            # own history), the only plan that may apply a notice to a record held BEFORE this import; anything else —
            # absent or unknown included — is the default import's narrow scope, where a held target's notice is PENDING.
            # (Shipped 0041 bound a notice to a bare target id, so an untrusted file carrying only a notice redacted the
            # user's own held fact; the 2026-10-13 hotfix narrowed it; §11.6.6 replaced the hotfix's rule.)
            notice_any = plan.get("notice_scope") == "any"
            notice_targets: set = set()
            for n in notices:
                missing = [f for f in ("target_kind", "target_id", "fields", "marker_version", "reason",
                                       "origin", "source_user", "source_event_ref") if f not in n]
                if missing:
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"redaction notice is missing {missing} — refused (specs/0041 §4g)"), "notice-missing-fields")
                # round 11 (R10-03): the source identity is three non-empty strings, as the parser requires — checked
                # here too (a plan reaches this primitive by other routes); any value is then held VERBATIM, framed
                if not all(isinstance(n[k], str) and n[k] for k in ("origin", "source_user", "source_event_ref")):
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"redaction notice for {n.get('target_id')!r} carries an empty or non-string source identity — "
                        f"refused (specs/0041 §4g)"), "notice-target")
                if n["target_kind"] not in ("edge", "episode") or not isinstance(n["target_id"], str) or not n["target_id"]:
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"redaction notice names an invalid target {n['target_kind']!r}/{n['target_id']!r} — refused (specs/0041 §4g)"), "notice-target")
                # round 10 (R9-08): the field NAMES are the declared kind's carrier paths — the domain DERIVED from
                # the treatment tables, checked here as well as at the parser (a plan reaches this primitive by
                # other routes); prose, a wrong-kind path, an empty or repeated list refuses the whole plan
                if (not isinstance(n["fields"], list) or not n["fields"] or len(set(n["fields"])) != len(n["fields"])
                        or not all(isinstance(f, str) for f in n["fields"])
                        or not set(n["fields"]) <= _redaction.attestation_paths(n["target_kind"])):
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"redaction notice for {n['target_id']!r} carries fields outside the {n['target_kind']} carrier "
                        f"paths — refused (specs/0041 §4b, §4g)"), "notice-fields")
                if not isinstance(n["marker_version"], int) or n["marker_version"] < 1 or n["marker_version"] > _redaction.MARKER_VERSION:
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"redaction notice for {n['target_id']!r} declares marker version {n['marker_version']!r}, which this "
                        f"build does not know (it knows up to {_redaction.MARKER_VERSION}) — refused (specs/0041 §4g)"), "notice-marker-version")
                if n["reason"] not in _redaction.ORIGINATING_REASONS:      # round 11 (R10-04): the SOURCE's own
                    raise _SITE_IMPORT_PLAN.fire(ValueError(
                        f"redaction notice for {n['target_id']!r} carries reason {n['reason']!r} outside the vocabulary — "
                        f"refused (specs/0041 §11.2)"), "notice-reason")
                for k in ("store_version_before", "store_version_after"):
                    v = n.get(k)
                    if v is not None and (isinstance(v, bool) or not isinstance(v, int) or v < 0):
                        raise _SITE_IMPORT_PLAN.fire(ValueError(
                            f"redaction notice for {n['target_id']!r} carries {k}={v!r} — refused (specs/0041 §4g)"), "notice-fields")
                # round 10 (R9-04): the row id binds the DESTINATION user and the typed (post-remap) target; the
                # foreign body is canonical, compared on every repeat and kept immutable
                n["_rid"] = self.notice_id(n["origin"], n["source_user"], n["source_event_ref"], user_id,
                                           n["target_kind"], n["target_id"])
                n["_body"] = self.notice_body(n)
                notice_targets.add((n["target_kind"], n["target_id"]))
            with self._lock, self._write_txn():
                # (1) Revalidate EVERY destination assumption the preflight reasoned
                # about (round-6 Correction B) — atomically, before any write.
                for eid, expect_present in expected_destination_state.get(
                        "edge_ids", {}).items():
                    row = self._conn.execute(
                        "SELECT user_id FROM edges WHERE id=?", (eid,)).fetchone()
                    # research's N2 (R-II round 3): an id ANOTHER user holds is never a lost race. The preflight reads
                    # per user and cannot see that row, so a retry re-plans the same collision; it used to exhaust the
                    # retries and refuse as "kept losing a race". The owner never changes (0008 §6d), so refuse it here
                    if row is not None and row[0] != user_id:
                        raise _SITE_IMPORT_PLAN.fire(ValueError(
                            f"edge {eid!r} is held by another user in this store — record ids are store-wide and an "
                            f"import never takes over another user's record; nothing imported (specs/0009 §4c, "
                            f"0008 §6d)"), "owner-conflict")
                    present = row is not None
                    if present != expect_present:
                        return DESTINATION_CHANGED       # created/removed under us
                for ep_id, expect_json in expected_destination_state.get(
                        "episode_records", {}).items():
                    row = self._conn.execute(
                        "SELECT json, user_id FROM episodes WHERE id=?", (ep_id,)).fetchone()
                    if row is not None and row[1] != user_id:     # N2, as for edges (0004 v3.5 §2c (i))
                        raise _SITE_IMPORT_PLAN.fire(ValueError(
                            f"episode {ep_id!r} is held by another user in this store — record ids are store-wide and "
                            f"an import never takes over another user's record; nothing imported (specs/0009 §4c, "
                            f"0004 §2c (i))"), "owner-conflict")
                    current = row[0] if row is not None else None
                    if current != expect_json:           # RECORD equality, not id
                        return DESTINATION_CHANGED
                for (edge_id, evidence_ref), expect_head in \
                        expected_destination_state.get("chain_heads", {}).items():
                    head = self._chain_head(user_id, edge_id, evidence_ref)
                    head_id = head.id if head is not None else None
                    if head_id != expect_head:           # linearize vs append_outcome_if_head
                        return DESTINATION_CHANGED
                # (1b) 0009 §4c as amended: the contribution gate — EVERY decision
                # is taken here, BEFORE any write, so DESTINATION_CHANGED writes
                # nothing (records included). Per survivor: the current row-id set
                # must equal the caller's expected `contribution_state` (drift is
                # a lost race); then ABSENT → write, plan_row_id-set-EQUAL → skip
                # as existing, anything else → a different recorded history,
                # refused whole.
                contribution_state = expected_destination_state.get(
                    "contribution_state", {})
                contrib_writes: list = []
                contrib_existing = 0
                for surv, rows in sorted(contrib_by_surv.items()):
                    if surv not in plan_edge_ids:
                        hit = self._conn.execute(
                            "SELECT user_id FROM edges WHERE id=?",
                            (surv,)).fetchone()
                        if hit is None or hit[0] != user_id:
                            raise _SITE_IMPORT_PLAN.fire(ValueError(
                                f"contribution rows attribute survivor {surv!r}, "
                                f"which is neither a plan record nor an "
                                f"already-present record of this user — the "
                                f"preflight refuses (0009 §4c as amended)"), "survivor-foreign")
                    current = {r[0] for r in self._conn.execute(
                        "SELECT id FROM contribution_ledger WHERE user_id=? AND "
                        "survivor_type='edge' AND survivor_id=?",
                        (user_id, surv)).fetchall()}
                    if current != set(contribution_state.get(surv, ())):
                        return DESTINATION_CHANGED       # rows moved under us
                    planned = {r["id"] for r in rows}
                    if current == planned:
                        contrib_existing += len(rows)    # idempotent re-import
                    elif not current:
                        contrib_writes.extend(rows)
                    else:
                        # different contributors or a different history SHAPE —
                        # a different history, refused whole, writing NOTHING
                        return DESTINATION_CHANGED
                # (1c) specs/0044 §4l (T11a, build note D9): the arity assumptions the preflight decided by — the plan
                # header's id, every outcome uid it compared, and every touched edge's outcome-uid set — re-checked here
                # under the lock, so a `run_data_migration`/plan-only call or a concurrent import between preflight and
                # commit is a lost race (DESTINATION_CHANGED, the preflight re-reads), never a stale decision.
                arity = expected_destination_state.get("arity")
                if arity is not None:
                    hdr = self._conn.execute("SELECT plan_id FROM plan_header WHERE id=1").fetchone()
                    if (hdr[0] if hdr is not None else None) != arity["plan_id"]:
                        return DESTINATION_CHANGED
                    for uid, expect in arity["outcome_uids"].items():
                        row = self._conn.execute(
                            f"SELECT {', '.join(self._OUTCOME_COLUMNS)} FROM migration_outcome WHERE outcome_uid=?",
                            (uid,)).fetchone()
                        if (dict(zip(self._OUTCOME_COLUMNS, row)) if row is not None else None) != expect:
                            return DESTINATION_CHANGED
                    for edge_id, expect in arity["edge_outcomes"].items():
                        cur = sorted(r[0] for r in self._conn.execute(
                            "SELECT outcome_uid FROM migration_outcome WHERE user_id=? AND edge_id=?", (user_id, edge_id)))
                        if cur != list(expect):
                            return DESTINATION_CHANGED
                # (1d) specs/0008 §6e–§6f (T11b, build note D9): the act rows the preflight decided by — every arriving
                # identity's and known position's held rows store-wide, and the user's rows on every touched edge —
                # read again under the lock: a local reply or confirm, or a concurrent import, between preflight and
                # commit is a lost race (the preflight re-reads and decides again), never a stale chronology
                acts_expected = expected_destination_state.get("acts")
                if acts_expected is not None:
                    if self.act_state(user_id, *acts_expected["args"]) != acts_expected["state"]:
                        return DESTINATION_CHANGED
                # (2) Install ALL records as one logical commit (edges before episodes so
                # an outcome link's edge_id always resolves; contribution rows ride
                # the SAME transaction — nothing is durable after a prefix).
                try:
                    created: set = set()             # (kind, id) of every record this commit INSERTS (the hotfix)
                    # R-A RA-02: each record's ARRIVING copy as the unit carries it (after remapping, BEFORE any treatment
                    # — `_treated_on_arrival` below, or a notice's), held as JSON TEXT so it is immutable by construction:
                    # the notice phase's predicates parse it afresh, and never read the row
                    arriving: dict = {}
                    for edge in edges:
                        arriving[("edge", edge.id)] = edge.model_dump_json()
                        # specs/0041 §11.2 / D1 at the IMPORT boundary (round 10, R9-02(c)): the reason closure binds
                        # import as it binds the writers
                        if ("edge", edge.id) not in notice_targets and not self._attested_fields(user_id, "edge", edge.id, coverage=True):
                            self._refuse_redacted_reason(edge.invalidation_reason, f"imported edge {edge.id!r}", "import-edge")
                        with _SITE_IMPORT_REASON.consult():
                            if edge.invalidation_reason is not None and edge.invalidation_reason not in DISPOSITIONED_REASONS:
                                raise _SITE_IMPORT_REASON.fire(ValueError(
                                    f"refused: imported edge {edge.id!r} carries invalidation reason "
                                    f"{edge.invalidation_reason!r}, not a registered reason (specs/0041 §11.2, D1)"), "edge")
                        # specs/0041 §4b-ii / INV-11 at the IMPORT boundary (tranche 4b): a record whose
                        # redaction this store already COMPLETED is not repopulated by an import with no notice
                        # for it. Round 11 (R10-02): WITH the notice, the record is written as the attestation's
                        # TREATED shape here, in this transaction — round 10's comment said it was "redacted again",
                        # but the notice was then counted existing and skipped, and the content arrived verbatim
                        with _SITE_IMPORT_ATTESTED.consult():
                            if self._completed_attestation(user_id, "edge", edge.id) and ("edge", edge.id) not in notice_targets:
                                raise _SITE_IMPORT_ATTESTED.fire(ValueError(
                                    f"refused: imported edge {edge.id!r} is redacted here (a redaction record attests it) "
                                    f"and the file carries no notice for it — an import may not repopulate it "
                                    f"(specs/0041 §4b-ii, INV-11; §4g)"))
                            if self._completed_attestation(user_id, "edge", edge.id):     # ONE consult per arrival
                                edge, uncovered = self._treated_on_arrival(user_id, "edge", edge.id, edge.model_dump(mode="json"))
                                if uncovered:
                                    raise _SITE_IMPORT_ATTESTED.fire(ValueError(
                                        f"refused: imported edge {edge.id!r} arrives under this store's completed redaction "
                                        f"record, but carries content in {uncovered}, which the record does not attest — "
                                        f"nothing imported (specs/0041 §4b-ii, INV-11; §4g)"), "arrival-outside-attestation")
                        prior = self._conn.execute(
                            "SELECT json FROM edges WHERE id=?", (edge.id,)).fetchone()
                        new_json = edge.model_dump_json()
                        self._conn.execute(
                            "INSERT OR REPLACE INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
                            "VALUES(?,?,?,?,?,?,?,?)",
                            (edge.id, edge.user_id, edge.subject, edge.relation, edge.object,
                             int(edge.active), int(edge.quarantined), new_json))
                        self._journal_edge_write(user_id, edge.id, new_json,
                                                 prior[0] if prior is not None else None)
                        if prior is None:
                            created.add(("edge", edge.id))
                    for ep in episodes:
                        # 0004 v3.5 §2c (ii)/(iii) at the import's episode admission (R-II round 3): the id's stored
                        # state is read by the ID. An id a non-quiescent op reserves is refused whoever owns the op, the
                        # destination included (0010 X21: its finalize deletes its claimed ids); an id ANOTHER owner's
                        # applied redaction attests is refused. The destination's own attestation keeps §4g's rule below.
                        with _SITE_IMPORT_ATTESTED.consult():
                            if self._attested_by_another_owner("episode", ep.id, user_id):
                                raise _SITE_IMPORT_ATTESTED.fire(ValueError(
                                    f"refused: imported episode {ep.id!r} is redacted in this store under another "
                                    f"owner — the redaction holds the id; nothing imported (specs/0041 INV-11; "
                                    f"0004 §2c (iii))"), "another-owners-redaction")
                        with _SITE_IMPORT_RESERVED.consult():
                            if self._id_reserved(ep.id):
                                raise _SITE_IMPORT_RESERVED.fire(ValueError(
                                    f"refused: imported episode {ep.id!r} is reserved by an in-flight consolidation — "
                                    f"nothing imported (specs/0010 X21; 0004 §2c (ii))"), "reserved-id")
                        arriving[("episode", ep.id)] = ep.model_dump_json()
                        if ("episode", ep.id) not in notice_targets and not self._attested_fields(user_id, "episode", ep.id, coverage=True):
                            self._refuse_redacted_reason(ep.retired_reason, f"imported episode {ep.id!r}", "import-episode")
                        with _SITE_IMPORT_REASON.consult():
                            if ep.retired_reason is not None and ep.retired_reason not in DISPOSITIONED_REASONS:
                                raise _SITE_IMPORT_REASON.fire(ValueError(
                                    f"refused: imported episode {ep.id!r} carries retired reason {ep.retired_reason!r}, "
                                    f"not a registered reason (specs/0041 §11.2, D1)"), "episode")
                        # specs/0041 §2d-iv / §4h(ii): the kind closure binds the IMPORT
                        # boundary as well; a marker-valued kind validates only under
                        # attestation (tranche 2) and is refused here until then
                        with _SITE_IMPORT_EPISODE_KIND.consult():
                            # round 10 (R9-06): a MARKER-valued kind is the treated value of a historical prose kind
                            # and is admitted ONLY when this same unit attests `kind` for this episode — a notice in
                            # this plan naming it, or one this store already holds (a standing notice included).
                            # A raw prose kind, or a marker kind nothing accounts for, keeps the closure's refusal.
                            if ep.kind not in _redaction.RECOGNISED_EPISODE_KINDS and not (
                                    ep.kind == _redaction.MARKER and (
                                        any(n["target_kind"] == "episode" and n["target_id"] == ep.id
                                            and "kind" in n["fields"] for n in notices)
                                        or "kind" in self._attested_fields(user_id, "episode", ep.id, coverage=True))):
                                raise _SITE_IMPORT_EPISODE_KIND.fire(ValueError(
                                    f"refused: imported episode {ep.id!r} kind {ep.kind!r} is not a "
                                    f"recognised operational kind — the closure binds the import "
                                    f"boundary (specs/0041 §2d-iv, §4h(ii))"))
                        with _SITE_IMPORT_ATTESTED.consult():
                            if self._completed_attestation(user_id, "episode", ep.id) and ("episode", ep.id) not in notice_targets:
                                raise _SITE_IMPORT_ATTESTED.fire(ValueError(
                                    f"refused: imported episode {ep.id!r} is redacted here (a redaction record attests it) "
                                    f"and the file carries no notice for it — an import may not repopulate it "
                                    f"(specs/0041 §4b-ii, INV-11; §4g)"))
                            # round 11 (R10-02): WITH the notice, the arrival is written in the attestation's treated
                            # shape — never the content (the notice below is `existing` and treats nothing)
                            if self._completed_attestation(user_id, "episode", ep.id):
                                ep, uncovered = self._treated_on_arrival(user_id, "episode", ep.id, ep.model_dump(mode="json"))
                                if uncovered:
                                    raise _SITE_IMPORT_ATTESTED.fire(ValueError(
                                        f"refused: imported episode {ep.id!r} arrives under this store's completed "
                                        f"redaction record, but carries content in {uncovered}, which the record does not "
                                        f"attest — nothing imported (specs/0041 §4b-ii, INV-11; §4g)"), "arrival-outside-attestation")
                        self._conn.execute(
                            "INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                            (ep.id, ep.user_id, ep.date, ep.model_dump_json()))
                        created.add(("episode", ep.id))
                    now = self._now().isoformat()
                    for row in contrib_writes:
                        self._conn.execute(
                            "INSERT INTO contribution_ledger(id,user_id,"
                            "survivor_type,survivor_id,site,identity_digest,"
                            "evidence_ref_digest,payload,op_key,created_at,"
                            "contributor_type,contributor_ref) "
                            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                            (row["id"], user_id, "edge", row["survivor_id"],
                             row["site"], row["identity_digest"],
                             row["evidence_ref_digest"],
                             canonical_payload(row["payload"]), row["op_key"],
                             now, row["contributor_type"],
                             row["contributor_ref"]))
                    # specs/0044 §4l (T11a): the unit's outcome rows — validated whole by the caller's preflight and
                    # re-checked above — and then import-time conversion through 0044 §4f's steps, both BEFORE the notice
                    # phase, so a notice in this unit ends an outcome's episode through the lifetime hook like any write
                    outcome_rows = plan.get("outcomes", [])
                    for o in outcome_rows:
                        self._conn.execute(
                            f"INSERT INTO migration_outcome({', '.join(self._OUTCOME_COLUMNS)}) "
                            f"VALUES({','.join('?' * len(self._OUTCOME_COLUMNS))})",
                            tuple(o[c] for c in self._OUTCOME_COLUMNS))
                    converted = ((), ())
                    conv = plan.get("arity_conversion")
                    if conv and conv["rows"]:
                        from .data_migration import convert_rows
                        self._conn.execute("INSERT INTO migration_op(op_id, mode, inputs_digest, admitted_at) "
                                           "VALUES(?, 'import-convert', ?, ?)", (conv["op_id"], conv["inputs_digest"], now))
                        converted = convert_rows(self, user_id, conv["plan_id"], conv["rows"], conv["op_id"])
                    # specs/0008 §6e rule 4 / 0047 §4f (T11b, build note D14–D15): the unit's admitted acts, after the
                    # records they name and BEFORE the notice phase, so a trusted restore's applied notice treats them with
                    # every held act (the total treatment) and a default import's pending notice touches none. An imported
                    # act writes NO registry row and takes NO position from this store's counter (Q4′, §6f); this
                    # primitive refuses a plan act labelled `local` or keyed in the caller's grammar (a plan reaches it by
                    # other routes than the preflight)
                    act_counts = {"confirmations": 0, "replies": 0}
                    for a in plan.get("acts", []):
                        if a["origin"] not in ("imported", "restored") or not a["correlation_id"].startswith("#act:"):
                            raise _SITE_IMPORT_PLAN.fire(ValueError(
                                f"imported act {a['id']!r} is labelled {a['origin']!r} or keyed {a['correlation_id']!r} — an "
                                f"import writes only `imported`/`restored` acts under an internal `#act:` key (specs/0008 "
                                f"§6e, INV-Q4′, INV-Q5)"), "act-label")
                        cols = self._ACT_COLUMNS[a["table"]]
                        self._conn.execute(f"INSERT INTO {a['table']}({', '.join(cols)}) VALUES({','.join('?' * len(cols))})",
                                           tuple(a[c] for c in cols))
                        act_counts[a["table"]] += 1
                    # specs/0041 §11.6.6 (T4; it REPLACES the 2026-10-13 notice-binding hotfix's rule): every notice in the
                    # unit is weighed by its TARGET's state at this import, the file's copy of the record, and the mode —
                    # and by nothing about its origin (the owner's ruling: origin is recorded as the notice's source
                    # identity and compared by no rule). APPLIED is this store's TOTAL treatment (`_redact_in_txn`);
                    # PENDING and STANDING rows keep the foreign body immutable and attest nothing. In the SAME
                    # transaction as the records: everything commits together or nothing does.
                    applied = standing = existing = 0
                    unbound: list = []               # the notices left PENDING by this import: [kind, id, reason]
                    unit_rids = {n["_rid"] for n in notices}
                    # R-A RA-02 (specs/0041 §11.6.6, INV-RR12): every `shows_redaction` decision of this phase is staged
                    # HERE, before any notice treatment, over ONE immutable snapshot — the arriving copy for a record
                    # this unit carries, the held row otherwise — so no notice's treatment can satisfy another's
                    # predicate and no decision depends on the order the notices are processed in. Treatments still act
                    # on the live row. The targets: every notice in the unit, and every STANDING notice held from an
                    # earlier import whose record this unit creates (the arrival loop below).
                    # The arrival loop's rows are read HERE, once, and the loop iterates this list: the notice loop below
                    # writes only the unit's own rows, so this is the set it would re-read, and staging and weighing are
                    # one set by construction (two queries kept in step by hand were not: a widened loop query met an
                    # unstaged target)
                    arrival_rows = [r_ for r_ in self._conn.execute(
                        "SELECT id, target_kind, target_id, fields FROM redactions WHERE user_id=? AND state='standing'",
                        (user_id,)).fetchall() if r_[0] not in unit_rids and (r_[1], r_[2]) in created]
                    staged = {(n["target_kind"], n["target_id"]) for n in notices} | {(r_[1], r_[2]) for r_ in arrival_rows}
                    pre: dict = {}
                    for k, t_ in staged:
                        if (k, t_) in arriving:
                            pre[(k, t_)] = arriving[(k, t_)]
                            continue
                        r_ = self._conn.execute(f"SELECT user_id, json FROM {'edges' if k == 'edge' else 'episodes'} "
                                                f"WHERE id=?", (t_,)).fetchone()
                        if r_ is not None and r_[0] == user_id:
                            pre[(k, t_)] = r_[1]
                    for n in notices:
                        held = self._conn.execute(
                            "SELECT state, pending_reason FROM redactions WHERE id=?", (n["_rid"],)).fetchone()
                        # round 10 (R9-04): a repeat is idempotent only for the SAME body; a contradictory body under
                        # one identity refuses the whole import, across calls as well as within one file
                        # round 10, stage 2 (S2-1): the body is compared on the SOURCE identity, not the bound row id —
                        # one source event has ONE body whichever destination user or remapped target it lands on. A
                        # user-remapping import mints a fresh target each time, so a bound-id lookup found nothing and
                        # compared nothing.
                        # round 11 (R10-03): the SOURCE identity compared EXACTLY — no prefix. Round 12 (R11-03): every
                        # candidate row — witnessed (its source columns) AND this store's own NATIVE rows (no source
                        # columns, so round 11's column query never saw them, and a contradictory notice of the store's
                        # own event was accepted) — is projected by `_canonical_source`, the one definition the export
                        # uses, and kept when its identity equals the notice's — that comparison DECIDES; the WHERE only
                        # narrows the scan (dropping its origin clause changes no outcome). A witnessed row holding no
                        # body is not compared: its body is unknown, and unknown never contradicts.
                        ident = (n["origin"], n["source_user"], n["source_event_ref"])
                        bodies, native_same_target = set(), False
                        for row in self._conn.execute(
                                f"SELECT user_id, target_kind, target_id, {self.RECORD_COLS} FROM redactions "
                                "WHERE source_origin=? AND source_user=? AND source_event_ref=? "
                                "OR source_origin IS NULL AND user_id=? AND ?=?",
                                ident + (n["source_user"], n["origin"], self.local_origin())).fetchall():
                            r_ident, rb = self._canonical_source(row[0], *row[4:])
                            if r_ident != ident or (row[12] is not None and row[11] is None):
                                continue                        # another event; or a witnessed row with no body
                            bodies.add(self.notice_body(rb))
                            if row[12] is None and (row[0], row[1], row[2]) == (user_id, n["target_kind"], n["target_id"]):
                                native_same_target = True
                        with _SITE_IMPORT_NOTICE_CONFLICT.consult():
                            if bodies - {n["_body"]}:
                                raise _SITE_IMPORT_NOTICE_CONFLICT.fire(ValueError(
                                    f"refused: a redaction notice for {n['target_kind']} {n['target_id']!r} carries a "
                                    f"different body from the one this store already holds under the same source "
                                    f"identity — a contradictory source, nothing imported (specs/0041 §4g)"))
                        if native_same_target:
                            existing += 1                       # the store's own event, already attested on that target
                            continue
                        kind, tid = n["target_kind"], n["target_id"]
                        tbl = "edges" if kind == "edge" else "episodes"
                        row = self._conn.execute(f"SELECT user_id, json FROM {tbl} WHERE id=?", (tid,)).fetchone()
                        present = row is not None and row[0] == user_id
                        state = held[0] if held is not None else None
                        if state == "applied":
                            existing += 1                       # applied before: the R10-02 `existing`
                            continue
                        created_here = (kind, tid) in created
                        # the CREATED row is weighed before the pending/standing shortcuts (research's T4 stage 2, T4-1):
                        # a pending notice whose target was deleted, re-arriving beside its UNREDACTED record in a unit
                        # that creates it, short-circuited to `existing` and the content landed (main-only). A pending
                        # notice stays pending across an import that re-creates its target only when the notice is NOT
                        # in that unit (the arrival loop below never weighs a pending row).
                        if state == "pending" and not created_here and (not notice_any or not present):
                            # IO-II-1: a repeat DEFAULT import of a pending notice is `existing`, its reason kept; a
                            # pending notice whose target is gone is inert in both modes (§11.6.6)
                            existing += 1
                            unbound.append((kind, tid, held[1]))
                            continue
                        if state == "standing" and not present:
                            existing += 1                       # still standing: its target is not held
                            continue
                        if created_here:
                            # CREATED by this import: the unit carries the record. It must SHOW the redaction, in both
                            # modes — admitting it would land content its source says it redacted, and redacting it
                            # would destroy a fact a poisoned export pairs with a notice (internal finding 0041-PA1).
                            # Whatever this store already held for the notice (none, standing, or pending with its
                            # target since deleted), a record this unit creates showing the redaction is APPLIED: the
                            # unit attests itself, and nothing the user holds is changed (dev's call on research's open
                            # "shown variant", 2026-10-15; research writes it into 0041)
                            shown = (n["_shown"] if "_shown" in n
                                     else _redaction.shows_redaction(kind, json.loads(pre[(kind, tid)]), n["fields"]))
                            with _SITE_IMPORT_NOTICE_UNSHOWN.consult():
                                if not shown:
                                    raise _SITE_IMPORT_NOTICE_UNSHOWN.fire(ValueError(
                                        f"refused: the file carries {kind} {tid!r} UNREDACTED beside a redaction notice "
                                        f"for it (origin {n['origin']!r}) — admitting it would land content its source "
                                        f"says it redacted, and applying the notice could destroy a record the file does "
                                        f"not show redacted; nothing imported (specs/0041 §11.6.6, INV-RR14)"))
                            self._redact_in_txn(user_id, kind, tid, "imported_notice", row_json=row[1], row_id=n["_rid"],
                                                fields_hint=n["fields"], source_body=n["_body"],
                                                source_identity=(n["origin"], n["source_user"], n["source_event_ref"]))
                            applied += 1
                            continue
                        if present:
                            # HELD before this import — a local fact, a copy of another store's record, or (research's
                            # B3) a record written locally under a STANDING notice: weighed like any held target
                            if not notice_any:
                                # a DEFAULT import never changes a held byte through a notice (INV-RR10): PENDING
                                self._set_notice_state(user_id, n, "pending", "held-target", prior=state, now=now)
                                unbound.append((kind, tid, held[1] if state == "pending" else "held-target"))
                                continue
                            # a TRUSTED RESTORE (own history, 0005): the file's copy decides
                            with _SITE_IMPORT_NOTICE_UNSHOWN.consult():
                                if n.get("_unshown") == "record-untreated":
                                    raise _SITE_IMPORT_NOTICE_UNSHOWN.fire(ValueError(
                                        f"refused: the file carries {kind} {tid!r} UNREDACTED beside a redaction notice "
                                        f"for it (origin {n['origin']!r}) — a restore may not land content its source "
                                        f"says it redacted, nor redact the held record on a copy that does not show it; "
                                        f"nothing imported (specs/0041 §11.6.6, INV-RR14)"))
                            if n.get("_shown") is True or _redaction.shows_redaction(kind, json.loads(pre[(kind, tid)]), n["fields"]):
                                # the file's copy shows it, or (no copy) the HELD record already does: applied, as this
                                # store's total treatment — held acts still carrying content are treated (§11.6.6)
                                self._redact_in_txn(user_id, kind, tid, "imported_notice", row_json=row[1],
                                                    row_id=n["_rid"], fields_hint=n["fields"], source_body=n["_body"],
                                                    source_identity=(n["origin"], n["source_user"], n["source_event_ref"]))
                                applied += 1
                                continue
                            self._set_notice_state(user_id, n, "pending", "record-not-in-file", prior=state, now=now)
                            unbound.append((kind, tid, held[1] if state == "pending" else "record-not-in-file"))
                            continue
                        # ABSENT, and not in the unit: STANDING — inert to local writes and readers (§11.6.6)
                        self._set_notice_state(user_id, n, "standing", None, prior=state, now=now)
                        standing += 1
                    # §11.6.6: a STANDING notice held from an EARLIER import, whose record THIS import created (and whose
                    # notice is not in this unit — the table above weighed those): an arrival that does not show the
                    # redaction refuses the whole import, in both modes; one that shows it is PENDING in a default import
                    # (reason `standing-arrival`, for the user's `confirm_notice`) and applied in a trusted restore. A
                    # record written LOCALLY is never completed here: it was not created by an import. No origin is read.
                    arrived = 0
                    for rid, kind, tid, fields in arrival_rows:
                        tbl = "edges" if kind == "edge" else "episodes"
                        row = self._conn.execute(f"SELECT user_id, json FROM {tbl} WHERE id=?", (tid,)).fetchone()
                        with _SITE_IMPORT_NOTICE_UNSHOWN.consult():
                            if not _redaction.shows_redaction(kind, json.loads(pre[(kind, tid)]), json.loads(fields)):
                                raise _SITE_IMPORT_NOTICE_UNSHOWN.fire(ValueError(
                                    f"refused: imported {kind} {tid!r} arrives UNREDACTED under a standing redaction "
                                    f"notice — admitting it would land content the notice says was redacted; nothing "
                                    f"imported (specs/0041 §11.6.6, INV-RR12)"))
                        if notice_any:
                            self._redact_in_txn(user_id, kind, tid, "imported_notice", row_json=row[1], row_id=rid,
                                                fields_hint=json.loads(fields))
                            arrived += 1
                        else:
                            self._set_notice_state(user_id, {"_rid": rid}, "pending", "standing-arrival",
                                                   prior="standing", now=now)
                            unbound.append((kind, tid, "standing-arrival"))
                    # specs/0047 §4d (INV-R18; R-II round 2, found answering research's B1): an import that admits a
                    # reply is a reply write, and evicts the user's compiled wiki in its own transaction as add_reply
                    # does — one bump alone leaves a cached body served for recompile_after writes. Every import
                    # evicts: an imported record changes what the body should say as surely as an imported act
                    self._conn.execute("DELETE FROM wiki WHERE user_id=?", (user_id,))
                    self._bump(user_id)
                except BaseException:
                    self._conn.rollback()                # ONE atomic commit —
                    raise                                # nothing after a prefix
            return {"edges": len(edges), "episodes": len(episodes),
                    "outcomes": len(outcome_rows), "arity_restored": list(converted[0]),
                    "confirmations": act_counts["confirmations"], "replies": act_counts["replies"],
                    "arity_withheld": list(converted[1]),
                    "contributions": len(contrib_writes),
                    "contributions_existing": contrib_existing,
                    "notices_applied": applied + arrived, "notices_standing": standing,
                    "notices_existing": existing, "notices_arrived": arrived,
                    "notices_not_applied": [list(t) for t in sorted(set(unbound))]}

    # -- crash-safe consolidation (specs/0010) --------------------------------
    _OP_COLS = ("operation_id", "user_id", "fence", "state", "owner",
                "lease_duration", "lease_expires_at", "claimed_ids")

    def _now(self) -> datetime:
        return self._clock()

    def _op_from_row(self, row) -> ConsolidationOp:
        return ConsolidationOp(
            operation_id=row[0], user_id=row[1], fence=row[2],
            state=ConsolidationState(row[3]), owner=row[4], lease_duration=row[5],
            lease_expires_at=row[6], claimed_ids=json.loads(row[7]))

    def _load_op(self, operation_id: str) -> Optional[ConsolidationOp]:
        row = self._conn.execute(
            f"SELECT {', '.join(self._OP_COLS)} FROM consolidation_ops "
            f"WHERE operation_id=?", (operation_id,)).fetchone()
        return self._op_from_row(row) if row is not None else None

    def _ops_for_user(self, user_id: str) -> list:
        return [self._op_from_row(r) for r in self._conn.execute(
            f"SELECT {', '.join(self._OP_COLS)} FROM consolidation_ops "
            f"WHERE user_id=?", (user_id,)).fetchall()]

    def _next_fence(self) -> int:
        return self._conn.execute(
            "SELECT COALESCE(MAX(fence), 0) + 1 FROM consolidation_ops").fetchone()[0]

    def _lease_live(self, op: ConsolidationOp) -> bool:
        return self._now() < datetime.fromisoformat(op.lease_expires_at)

    def _reserved_ids(self, user_id: str) -> set:
        """Every id claimed by a NON-QUIESCENT op (specs/0010 X21). Derived from
        `claimed_ids`, not physical presence, so the reservation survives the fenced
        batch-delete until the op reaches FINALIZED or clean ABANDONED."""
        reserved: set = set()
        for op in self._ops_for_user(user_id):
            if op.state in RECOVERY_PENDING_STATES:
                reserved.update(op.claimed_ids)
        return reserved

    def _id_reserved(self, episode_id: str) -> bool:
        """X21 for a WRITER: is `episode_id` claimed by ANY non-quiescent op, whoever owns it? Ids are unique across
        the store, so the reservation binds the id: read through the incoming writer's `_reserved_ids`, a
        deleted-but-reserved id was free to every other user (RII-R3-01, research's B1)."""
        for r in self._conn.execute(f"SELECT {', '.join(self._OP_COLS)} FROM consolidation_ops").fetchall():
            op = self._op_from_row(r)
            if op.state in RECOVERY_PENDING_STATES and episode_id in op.claimed_ids:
                return True
        return False

    def _write_op(self, op: ConsolidationOp) -> None:
        self._conn.execute(
            f"INSERT OR REPLACE INTO consolidation_ops({', '.join(self._OP_COLS)}) "
            f"VALUES(?,?,?,?,?,?,?,?)",
            (op.operation_id, op.user_id, op.fence, op.state.value, op.owner,
             op.lease_duration, op.lease_expires_at, json.dumps(op.claimed_ids)))

    def _episodes_for_operation(self, user_id: str, operation_id: str) -> list:
        """(episode_id, Episode) for every row physically tagged `operation_id` — both
        claimed INPUTS (claimed_by set, no lineage) and provisional OUTPUTS (lineage
        set). Parsed from the json blob, since operation_id is not a column."""
        out = []
        for eid, blob in self._conn.execute(
                "SELECT id, json FROM episodes WHERE user_id=?", (user_id,)):
            ep = Episode.model_validate_json(blob)
            if ep.operation_id == operation_id:
                out.append((eid, ep))
        return out

    def _claim_inputs(self, op: ConsolidationOp) -> None:
        """Tag each claimed input with `claimed_by`/`operation_id` (X4, atomic under the
        caller's lock+transaction). Every id must exist and belong to the op's user."""
        for eid in op.claimed_ids:
            row = self._conn.execute(
                "SELECT json FROM episodes WHERE id=? AND user_id=?",
                (eid, op.user_id)).fetchone()
            if row is None:
                raise ValueError(f"cannot claim {eid!r}: not an episode of "
                                 f"{op.user_id!r} (specs/0010 §4a)")
            ep = Episode.model_validate_json(row[0])
            bound = ep.model_copy(update={"claimed_by": op.operation_id,
                                          "operation_id": op.operation_id})
            self._conn.execute("UPDATE episodes SET json=? WHERE id=?",
                               (bound.model_dump_json(), eid))
            self._evict_wiki_on_view_change(op.user_id, Episode, row[0], bound.model_dump_json())   # RII-R2-01

    def _abandon(self, op: ConsolidationOp) -> None:
        """§4b-iii cleanup, under the caller's lock+transaction: delete every
        provisional OUTPUT row for the op, CLEAR the claim fields on every claimed INPUT
        row (never 'all rows' — inputs carry operation_id too), then mark ABANDONED."""
        for eid, ep in self._episodes_for_operation(op.user_id, op.operation_id):
            if ep.lineage:                                   # a provisional output
                self._conn.execute("DELETE FROM episodes WHERE id=?", (eid,))
                self._evict_wiki_on_view_change(op.user_id, Episode, ep.model_dump_json(), None)   # RII-R2-01
            else:                                            # a claimed input
                clean = ep.model_copy(update={"claimed_by": None, "operation_id": None})
                self._conn.execute("UPDATE episodes SET json=? WHERE id=?",
                                   (clean.model_dump_json(), eid))
                self._evict_wiki_on_view_change(op.user_id, Episode, ep.model_dump_json(),
                                                clean.model_dump_json())                         # RII-R2-01
        self._write_op(op.model_copy(update={"state": ConsolidationState.ABANDONED}))

    def create_or_takeover_consolidation(self, user_id, ids, owner, lease_duration):
        if not (0 < lease_duration <= LEASE_MAX):
            raise ValueError(f"lease_duration must be in (0, {LEASE_MAX}], "
                             f"not {lease_duration} (specs/0010 §4a-ii)")
        req = list(dict.fromkeys(ids))          # de-dup, preserve order
        req_set = set(req)
        # specs/0041 round 10 (found in sweep A): the claim is ONE transaction under BEGIN IMMEDIATE on this
        # connection, and refuses an ATTESTED input. The caller's candidate listing (and the LLM call made
        # from it) PRECEDES the claim, so a redaction committed by another connection in that gap would
        # otherwise be consumed: its content carried into the output, the redaction's target gone. Redact
        # already refuses a CLAIMED input (X21), so after this transaction commits no redaction can land on
        # the inputs; this check closes the window before it. The instance lock alone never serialised a
        # second connection.
        with self._lock, self._write_txn():
            with _SITE_CONSOLIDATION_INPUT_REDACTED.consult():
                redacted = sorted(req_set & self.redacted_targets(user_id, "episode"))
                if redacted:
                    raise _SITE_CONSOLIDATION_INPUT_REDACTED.fire(ValueError(
                        f"cannot claim: {len(redacted)} requested input(s) are attested-redacted — the candidate "
                        f"listing is stale; nothing is claimed (specs/0041 round 10, sweep A; specs/0010 §4a)"))
            # Recovery race rule (§4a-ii): abandon any EXPIRED pre-cutover op that
            # intersects the request BEFORE claiming, so a new fence issues only from a
            # clean ABANDONED state (X15). Re-evaluate until no expired intersection.
            while True:
                ops = self._ops_for_user(user_id)
                intersecting = [op for op in ops
                                if op.state in RECOVERY_PENDING_STATES
                                and req_set & set(op.claimed_ids)]
                live = [op for op in intersecting
                        if op.state == ConsolidationState.OUTPUTS_DURABLE
                        or self._lease_live(op)]
                with _SITE_CONSOLIDATION_CONTENDED.consult():
                    if live:
                        return _SITE_CONSOLIDATION_CONTENDED.fire(None, "contended")                  # contended (X7/X11 — no partial claim)
                if intersecting:                 # all expired pre-cutover → clean first
                    for op in intersecting:
                        self._abandon(op)
                    continue
                break
            # A CLEAN ABANDONED op covering EXACTLY these ids is revived under a NEW
            # fence; otherwise a fresh operation is created (X15).
            revivable = next(
                (op for op in ops if op.state == ConsolidationState.ABANDONED
                 and set(op.claimed_ids) == req_set), None)
            fence = self._next_fence()
            expires = (self._now() + timedelta(seconds=lease_duration)).isoformat()
            op = ConsolidationOp(
                operation_id=(revivable.operation_id if revivable
                              else f"op-{uuid.uuid4().hex[:12]}"),
                user_id=user_id, fence=fence, state=ConsolidationState.CLAIMED,
                owner=owner, lease_duration=lease_duration,
                lease_expires_at=expires, claimed_ids=req)
            self._claim_inputs(op)               # all-or-nothing under this transaction
            self._write_op(op)
            return op                            # _write_txn commits the claim as one transaction

    def renew_consolidation_lease(self, operation_id, fence, owner) -> bool:
        with self._lock:
            op = self._load_op(operation_id)
            with _SITE_RENEW_REFUSED.consult():
                if (op is None or op.fence != fence or op.owner != owner
                        or op.state not in (ConsolidationState.CLAIMED,
                                            ConsolidationState.GENERATING)
                        or not self._lease_live(op)):        # cannot resurrect an expired lease
                    return _SITE_RENEW_REFUSED.fire(False, "refuse")
            expires = (self._now() + timedelta(seconds=op.lease_duration)).isoformat()
            self._write_op(op.model_copy(update={"lease_expires_at": expires}))
            self._conn.commit()
            return True

    def write_consolidation_output_if_current(self, operation_id, fence, owner,
                                              draft: ConsolidationOutputDraft) -> bool:
        with self._lock:
            op = self._load_op(operation_id)
            with _SITE_WRITE_NOT_CURRENT.consult():
                if (op is None or op.fence != fence or op.owner != owner
                        or op.state != ConsolidationState.GENERATING
                        or not self._lease_live(op)):
                    return _SITE_WRITE_NOT_CURRENT.fire(False, "refuse")
            inputs = []
            for eid in op.claimed_ids:
                row = self._conn.execute(
                    "SELECT json FROM episodes WHERE id=? AND user_id=?",
                    (eid, op.user_id)).fetchone()
                if row is not None:
                    inputs.append(Episode.model_validate_json(row[0]))
            # X23: every derived field is STORE-computed from the claimed set, not the
            # draft/LLM — min trust across the whole set (N9b) and the true date range.
            prov, date_start, date_end = self._derive_output_metadata(inputs, operation_id)
            # specs/0014 §4c: the STORE assigns the output index — the count of
            # outputs already written for this operation (sequential from 0,
            # contiguous by construction; asserted below as the local-op
            # invariant). Only this primitive ever sets the field.
            existing = [e for _, e in
                        self._episodes_for_operation(op.user_id, operation_id)
                        if e.lineage]
            next_index = len(existing)
            assert sorted(
                e.consolidation_output_index for e in existing) == list(
                range(next_index)), "output indices must be contiguous 0..M-1"
            ep = Episode(
                id=f"epc-{uuid.uuid4().hex[:12]}", user_id=op.user_id,
                date=date_start, summary=draft.summary, date_start=date_start,
                date_end=date_end, operation_id=operation_id,
                lineage=[to_historical_id(i) for i in op.claimed_ids],
                consolidation_output_index=next_index,
                provenance=prov)
            # INSERT — never replace (X22): a minted-id collision is a store error.
            self._conn.execute(
                "INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                (ep.id, ep.user_id, ep.date, ep.model_dump_json()))
            self._conn.commit()                  # provisional + hidden until cutover
            return True

    def _derive_output_metadata(self, inputs, operation_id):
        """(Provenance, date_start, date_end) for a consolidation output, computed from
        the claimed inputs (specs/0010 §4d/§4d-ii/X23 — mirrors lifecycle's whole-set
        minimum-trust rule). Empty inputs cannot occur on the write path (a GENERATING
        op holds visible inputs), but guard defensively."""
        _RANK = {Disclosure.QUARANTINED: 0, Disclosure.USE_ONLY: 1,
                 Disclosure.MENTIONABLE: 2}
        base = inputs[0].provenance if inputs else Provenance(
            author_of_evidence=EvidenceAuthor.SYSTEM,
            evidence_ref=operation_id)
        influenced = any(e.provenance.third_party_influenced for e in inputs)
        weakest = (min(inputs, key=lambda e: _RANK[e.provenance.disclosure])
                   .provenance.disclosure if inputs else base.disclosure)
        prov = base.model_copy(update={
            "author_of_evidence": EvidenceAuthor.SYSTEM,
            "evidence_ref": operation_id,
            # specs/0021 §4a / W8 (external F1, the IMPLEMENTATION OBLIGATION):
            # a consolidation output CLEARS the inherited identity. `base` is
            # `inputs[0].provenance`, so before this the first input's
            # (origin, source_id) travelled onto every derivative — a mixed
            # A+B consolidation CLAIMED identity A, which is exactly the
            # laundering the scope machinery exists to stop. Store-authored
            # means store-identified: `origin=None` resolves to the LOCAL
            # singleton at read (0006 I9) and `source_id=None` is not
            # groupable (I13), so membership can only travel through the
            # 0014 ledger, never through a copied field.
            "origin": None,
            "source_id": None,
            "derived_from": (EvidenceAuthor.THIRD_PARTY if influenced
                             else base.derived_from),
            "disclosure": weakest,
            "confidence": (min(e.provenance.confidence for e in inputs)
                           if inputs else base.confidence),
            "observed_at": (max(e.provenance.observed_at for e in inputs)
                            if inputs else base.observed_at)})
        dates = sorted(e.date for e in inputs) if inputs else [""]
        return prov, dates[0], dates[-1]

    def transition_consolidation_if_current(self, operation_id, fence, owner,
                                            to_state) -> bool:
        to_state = ConsolidationState(to_state)
        with _SITE_TRANSITION.consult():
            with self._lock:
                op = self._load_op(operation_id)
                if op is None or op.fence != fence:
                    return _SITE_TRANSITION.fire(False, "fence")
                S = ConsolidationState
                if to_state is S.GENERATING:
                    if (op.state is not S.CLAIMED or op.owner != owner
                            or not self._lease_live(op)):
                        return _SITE_TRANSITION.fire(False, "generating-refused")
                    self._write_op(op.model_copy(update={"state": S.GENERATING}))
                elif to_state is S.OUTPUTS_DURABLE:
                    if (op.state is not S.GENERATING or op.owner != owner
                            or not self._lease_live(op)):
                        return _SITE_TRANSITION.fire(False, "cutover-refused")
                    # X22: refuse the cutover unless ≥1 correctly-bound output exists
                    bound = [ep for _, ep in
                             self._episodes_for_operation(op.user_id, operation_id)
                             if ep.lineage]
                    if not bound:
                        return _SITE_TRANSITION.fire(False, "no-bound-output")
                    # specs/0014 §4b/§4c: the N×M contribution rows are written AT
                    # the cutover, in this same transaction, while the claimed inputs
                    # are still readable (they are deleted only after OUTPUTS_DURABLE).
                    self._write_consolidation_contributions(op)
                    self._write_op(op.model_copy(update={"state": S.OUTPUTS_DURABLE}))
                    # RII-R2-01 (research's stage-1 addendum, (c)): the cutover hides every claimed input from every
                    # ordinary read and reveals the outputs, writing no episodes row — so no view moves, yet a wiki
                    # drawn on the inputs would be served beside an episodes block rendering the outputs, both
                    # representations in one call (0010 X9). It evicts here, in the cutover's own transaction; the
                    # inputs' deletion, which may be delayed by recovery, evicts again
                    self._conn.execute("DELETE FROM wiki WHERE user_id=?", (op.user_id,))
                    self._bump(op.user_id)           # X14: the visibility cutover bumps
                elif to_state is S.FINALIZED:
                    if op.state is not S.OUTPUTS_DURABLE:     # ownerless, recovery-safe
                        return _SITE_TRANSITION.fire(False, "not-durable")
                    # X20: unreachable until every claimed input is deleted
                    remaining = self._conn.execute(
                        "SELECT COUNT(*) FROM episodes WHERE user_id=? AND id IN ({})".format(
                            ",".join("?" * len(op.claimed_ids))),
                        (op.user_id, *op.claimed_ids)).fetchone()[0] if op.claimed_ids else 0
                    if remaining > 0:
                        return _SITE_TRANSITION.fire(False, "inputs-remaining")
                    self._write_op(op.model_copy(update={"state": S.FINALIZED}))
                else:
                    return _SITE_TRANSITION.fire(False, "unknown-transition")
                self._conn.commit()
                return True

    def delete_claimed_inputs_if_current(self, operation_id, fence) -> bool:
        with self._lock:
            op = self._load_op(operation_id)
            with _SITE_DELETE_NOT_CURRENT.consult():
                if (op is None or op.fence != fence
                        or op.state is not ConsolidationState.OUTPUTS_DURABLE):
                    return _SITE_DELETE_NOT_CURRENT.fire(False, "refuse")
            for eid in op.claimed_ids:           # idempotent all-or-nothing re-delete
                prior = self._conn.execute(
                    "SELECT json FROM episodes WHERE id=? AND user_id=?", (eid, op.user_id)).fetchone()
                self._conn.execute(
                    "DELETE FROM episodes WHERE id=? AND user_id=?", (eid, op.user_id))
                self._evict_wiki_on_view_change(op.user_id, Episode, prior[0] if prior else None, None)  # RII-R2-01
            self._conn.commit()
            return True

    def abandon_consolidation_if_current(self, operation_id, fence) -> bool:
        with self._lock:
            op = self._load_op(operation_id)
            with _SITE_ABANDON_LIVE_LEASE.consult():
                if (op is None or op.fence != fence
                        or op.state not in (ConsolidationState.CLAIMED,
                                            ConsolidationState.GENERATING)
                        or self._lease_live(op)):    # expired-lease only (X7)
                    return _SITE_ABANDON_LIVE_LEASE.fire(False, "refuse")
            self._abandon(op)
            self._conn.commit()
            return True

    def pending_consolidations(self, user_id) -> list:
        with self._lock:
            return [op for op in self._ops_for_user(user_id)
                    if op.state in RECOVERY_PENDING_STATES]

    def quiescent_episode_snapshot(self, user_id):
        # X17: ONE atomic observation — the quiescence check and the episode snapshot
        # under the same lock, linearizable against create_or_takeover_consolidation.
        with _SITE_EXPORT_NON_QUIESCENT.consult():
            with self._lock:
                if any(op.state in RECOVERY_PENDING_STATES
                       for op in self._ops_for_user(user_id)):
                    return _SITE_EXPORT_NON_QUIESCENT.fire(NON_QUIESCENT, "non-quiescent")
                return _SITE_EXPORT_NON_QUIESCENT.fire([Episode.model_validate_json(r[0]) for r in self._conn.execute(
                    "SELECT json FROM episodes WHERE user_id=? ORDER BY date", (user_id,))], "snapshot")

    # -- host/admin queries ---------------------------------------------------
    def list_users(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT user_id, SUM(e), SUM(p) FROM ("
            "  SELECT user_id, COUNT(*) AS e, 0 AS p FROM edges GROUP BY user_id"
            "  UNION ALL"
            "  SELECT user_id, 0, COUNT(*) FROM episodes GROUP BY user_id"
            ") GROUP BY user_id ORDER BY user_id").fetchall()
        return [{"user_id": u, "edges": int(e or 0), "episodes": int(p or 0)}
                for u, e, p in rows]

    # -- compliance erasure -------------------------------------------------
    # -- specs/0041 §4a: targeted redaction (tranche 3) ------------------------
    def _attested_fields(self, user_id: str, kind: str, target_id: str, *, coverage: bool = False) -> set:
        """§4b's attestation rule: the fields a redaction record names for this record — the ONLY thing that
        makes a marker mean 'redacted'. Empty when no record exists (an unattested marker confers nothing).
        Two readers (T4, research's B2); every call in src/ names which, held by
        tests/test_0041_notice_state.py::test_every_src_call_of_the_attested_fields_reader_names_it. The DEFAULT is the
        attestation reader (the tests and the committed 0041 evidence call it positionally, meaning "is it attested").
        For a caller that refuses on ABSENCE — the import's reason closures, the 0014 rider, R10-02's uncovered check —
        it is the fail-closed reader, counting less as covered; for the INV-11 writers applied-only is simply the
        correct reader, since a pending or standing notice redacts nothing they would repopulate:
        `coverage=False` — ATTESTATION, APPLIED rows only: what this store has redacted (the local writers' INV-11
        refusal, R10-02's treated arrival); `coverage=True` — COVERAGE, every row whatever its state (0041 §11.6.6:
        "Coverage counts every notice for the target, whatever its state"): what an ARRIVING row may be admitted as,
        which never writes held content.
        `user_id=_ANY_OWNER` keys the record by its ID alone, whoever redacted it: add_episode's INV-11 refusal
        (RII-R3-01, N1 RULED 2026-10-23: "the redaction holds the ID"). Never a reader's key: a per-id reader would
        apply one user's redaction to another's records."""
        out: set = set()
        owner_sql = "" if user_id is _ANY_OWNER else " AND user_id=?"
        args = (kind, target_id) if user_id is _ANY_OWNER else (kind, target_id, user_id)
        for (fields,) in self._conn.execute(
                "SELECT fields FROM redactions WHERE target_kind=? AND target_id=?" + owner_sql
                + ("" if coverage else f" AND {_APPLIED_SQL}"),
                args):
            out.update(json.loads(fields))
        return out

    def _attested_by_another_owner(self, kind: str, target_id: str, user_id: str) -> bool:
        """Does an APPLIED redaction under an owner other than `user_id` attest this id? The import's (iii): the
        destination's own attestation has §4g's notice rule; another owner's holds the id outright."""
        return self._conn.execute(
            f"SELECT 1 FROM redactions WHERE target_kind=? AND target_id=? AND user_id<>? AND {_APPLIED_SQL} LIMIT 1",
            (kind, target_id, user_id)).fetchone() is not None

    def redacted_targets(self, user_id: str, kind: str) -> frozenset:
        """specs/0041 §4b-iii (tranche 4a): the ids of this user's ATTESTED-redacted records of one kind — the
        set the readers exclude (recall, the wiki compile, describe_procedures). By the attestation record,
        never by marker bytes: an unattested marker row is not in it. Only APPLIED rows (0041 §11.6.6): a PENDING
        notice is not a redaction of anything this store holds, and a STANDING one names no record it holds."""
        return frozenset(r[0] for r in self._conn.execute(
            f"SELECT DISTINCT target_id FROM redactions WHERE user_id=? AND target_kind=? AND {_APPLIED_SQL}",
            (user_id, kind)))

    # specs/0041 §4g: a WITNESSED redaction (an imported notice) is attested by a row whose `reason` column is
    # `imported_notice` (the witness distinction: this store was TOLD the source redacted it); the source's own reason
    # travels in the notice body, never as this store's claim.
    # Round 11 (R10-03): the SOURCE identity — origin, source user, source event ref — is held in three structured
    # columns and compared EXACTLY. Round 10 joined it into the row id with U+001F and read it back by splitting
    # and by a substr prefix: two distinct triples whose separators fell differently encoded equal, a component
    # carrying the separator failed to decode (and the relay then re-labelled the row as LOCAL), and a NUL defeated
    # the prefix match. The row id is now a DIGEST over the six components, each length-framed (scope_linkage's
    # `_framed`, the same injective form 0021 adopted for its op keys), and nothing ever parses it.
    NOTICE_ID_DOMAIN = b"veracium.redaction-notice-id.v1"
    RECORD_COLS = ("id, fields, marker_version, reason, store_version_before, store_version_after, event_ref, "
                   "recorded_at, source_body, source_origin, source_user, source_event_ref")

    @classmethod
    def notice_id(cls, origin: str, source_user: str, source_event_ref: str, user_id: str, target_kind: str,
                  target_id: str) -> str:
        from ..scope_linkage import _framed
        h = hashlib.sha256(cls.NOTICE_ID_DOMAIN + b"".join(
            _framed(str(v).encode("utf-8")) for v in (origin, source_user, source_event_ref, user_id, target_kind,
                                                      target_id))).hexdigest()
        return "notice-" + h

    # the foreign notice BODY (round 10, R9-04/R9-05): the source's own facts, canonical, compared on every repeat
    # and re-exported unchanged — never this store's application facts
    NOTICE_BODY_KEYS = ("fields", "marker_version", "reason", "recorded_at", "store_version_before",
                        "store_version_after")

    @classmethod
    def notice_body(cls, n: dict) -> str:
        body = {k: n.get(k) for k in cls.NOTICE_BODY_KEYS}
        body["fields"] = sorted(body["fields"])
        return json.dumps(body, sort_keys=True, separators=(",", ":"))

    def _canonical_source(self, user_id: str, fields, mv, reason, vb, va, event_ref, recorded_at, source_body,
                          s_origin, s_user, s_event) -> tuple:
        """Round 12 (R11-03): a redaction row's SOURCE IDENTITY and canonical BODY, one definition for the export and
        the import's comparison. A witnessed row: its columns and its stored foreign body. A NATIVE row (no source
        columns): this store's origin, the row's user and event ref, and the body built from its own facts — never
        foreign columns written onto it."""
        if s_origin is not None:
            body = json.loads(source_body) if source_body is not None else {
                "fields": json.loads(fields), "marker_version": None, "reason": None, "recorded_at": None,
                "store_version_before": None, "store_version_after": None}
            return (s_origin, s_user, s_event), body
        body = {"fields": json.loads(fields), "marker_version": mv, "reason": reason, "recorded_at": recorded_at,
                "store_version_before": vb, "store_version_after": va}
        return (self.local_origin(), user_id, event_ref or ""), body

    def redaction_records(self, user_id: str) -> list:
        """specs/0041 D2 (tranche 4b): the user's redaction records as dicts, for export — every column, plus the
        SOURCE identity (`origin`, `source_user`, `source_event_ref`): this store's own for a local redaction,
        the original source's for a witnessed one. Never a content digest (the table holds none)."""
        out = []
        for row in self._conn.execute(
                "SELECT id, target_kind, target_id, fields, marker_version, reason, store_version_before, "
                "store_version_after, event_ref, recorded_at, source_body, source_origin, source_user, "
                "source_event_ref, state FROM redactions WHERE user_id=? ORDER BY recorded_at, id", (user_id,)):
            rid, kind, tid, fields, mv, reason, vb, va, event_ref, recorded_at, source_body = row[:11]
            (origin, s_user, s_event), body = self._canonical_source(user_id, fields, mv, reason, vb, va, event_ref,
                                                                     recorded_at, source_body, *row[11:14])
            # the NOTICE this record exports (round 10, R9-05): a local redaction's own facts; a witnessed one's
            # IMMUTABLE foreign body, unchanged — the ONE projection the import compares against (round 12, R11-03)
            out.append({"id": rid, "target_kind": kind, "target_id": tid, "fields": json.loads(fields),
                        "marker_version": mv, "reason": reason, "store_version_before": vb,
                        "store_version_after": va, "event_ref": event_ref, "recorded_at": recorded_at,
                        "origin": origin, "source_user": s_user, "source_event_ref": s_event, "notice_body": body,
                        "state": row[14]})
        return out

    def _completed_attestation(self, user_id: str, kind: str, target_id: str) -> bool:
        """An APPLIED redaction record — this store redacted the record (or applied a notice to it as its own
        total treatment). PENDING and STANDING rows are not (0041 §11.6.6)."""
        return self._conn.execute(
            f"SELECT 1 FROM redactions WHERE user_id=? AND target_kind=? AND target_id=? AND {_APPLIED_SQL} LIMIT 1",
            (user_id, kind, target_id)).fetchone() is not None

    def _set_notice_state(self, user_id: str, n: dict, state: str, reason, *, prior, now: str) -> None:
        """specs/0041 §11.6.6 (T4): the ONE writer of a notice's PENDING or STANDING state (APPLIED is written only by
        `_redact_in_txn`, as this store's total treatment). The closed values are validated HERE — the DDL holds no
        CHECK. `prior` is the row's state before this import (None: no row). A PENDING row keeps its reason (IO-II-1:
        only `confirm_notice` or its own re-arrival in a trusted restore moves it); a STANDING row may become PENDING
        (research's B3: its target was written locally, or arrived) and never the reverse. A new row is inserted with
        the notice's immutable foreign body and its source identity, as the standing insert always was."""
        with _SITE_NOTICE_STATE.consult():
            ok = (((state == "pending" and reason in _redaction.PENDING_REASONS)
                   or (state == "standing" and reason is None))
                  and prior in (None, "pending", "standing") and not (prior == "pending" and state == "standing"))
            if not ok:
                raise _SITE_NOTICE_STATE.fire(ValueError(
                    f"refused: a redaction notice may not move {prior!r} -> {state!r} (reason {reason!r}) — the "
                    f"states are {_redaction.NOTICE_STATES}, the pending reasons {_redaction.PENDING_REASONS} "
                    f"(specs/0041 §11.6.6)"))
        if prior == "pending" or prior == state:
            return
        if prior == "standing":
            self._conn.execute("UPDATE redactions SET state=?, pending_reason=? WHERE id=? AND state='standing'",
                               (state, reason, n["_rid"]))
            return
        ver = self.store_version(user_id)
        self._conn.execute(
            "INSERT INTO redactions(id, user_id, target_kind, target_id, fields, marker_version, reason, "
            "store_version_before, store_version_after, event_ref, recorded_at, source_body, "
            "source_origin, source_user, source_event_ref, state, pending_reason) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (n["_rid"], user_id, n["target_kind"], n["target_id"], json.dumps(n["fields"]), n["marker_version"],
             _redaction.WITNESS_REASON, ver, ver, None, now, n["_body"], n["origin"], n["source_user"],
             n["source_event_ref"], state, reason))

    def pending_notices(self, user_id: str) -> list:
        """specs/0041 §11.6.6 (T4): the user's PENDING notices, oldest first — the ids `confirm_notice` takes."""
        return [{"notice_id": rid, "target_kind": kind, "target_id": tid, "reason": reason, "origin": origin,
                 "source_user": s_user, "recorded_at": at}
                for rid, kind, tid, reason, origin, s_user, at in self._conn.execute(
                    "SELECT id, target_kind, target_id, pending_reason, source_origin, source_user, recorded_at "
                    "FROM redactions WHERE user_id=? AND state='pending' ORDER BY recorded_at, id", (user_id,))]

    def confirm_notice(self, user_id: str, notice_id: str):
        """specs/0041 §11.6.6 (T4): the user's CONFIRMATION of a PENDING notice — applied as a redaction BY THIS STORE,
        total over the target's carriers under this store's own treatment map (held acts included, even where the
        notice is older or partial and does not attest them), exactly as a local redaction is. The notice's foreign
        body is unchanged; the row becomes APPLIED and its fields are what this store treated. The only path by
        which a default-mode notice changes held content.
        An already APPLIED row is a repeat: its original receipt, `repeated=True` (redact()'s precedent). REFUSED,
        writing nothing: an unknown id and another user's id (ONE refusal for both — the existence of another
        user's notice is not disclosed by the shape of the error); a STANDING row (it is not pending); a pending
        notice whose target no longer exists (inert, §11.6.6)."""
        with self._lock, self._write_txn():
            row = self._conn.execute(
                "SELECT user_id, target_kind, target_id, fields, state FROM redactions WHERE id=?", (notice_id,)).fetchone()
            with _SITE_CONFIRM_NOTICE_UNKNOWN.consult():
                if row is None or row[0] != user_id:
                    raise _SITE_CONFIRM_NOTICE_UNKNOWN.fire(ValueError(
                        f"confirm_notice: no redaction notice {notice_id!r} for user {user_id!r} (specs/0041 §11.6.6)"))
            _uid, kind, tid, fields, state = row
            if state == "applied":
                record = self._conn.execute(f"SELECT {self.RECORD_COLS} FROM redactions WHERE id=?", (notice_id,)).fetchone()
                return self._receipt_from_record(user_id, kind, tid, record, repeated=True)
            with _SITE_CONFIRM_NOTICE_STANDING.consult():
                if state == "standing":
                    raise _SITE_CONFIRM_NOTICE_STANDING.fire(ValueError(
                        f"confirm_notice: notice {notice_id!r} is STANDING, not pending — it was recorded for a record this "
                        f"store did not hold, and only a pending notice is confirmed (specs/0041 §11.6.6)"))
            table = "edges" if kind == "edge" else "episodes"
            target = self._conn.execute(f"SELECT user_id, json FROM {table} WHERE id=?", (tid,)).fetchone()
            with _SITE_CONFIRM_NOTICE_INERT.consult():
                if target is None or target[0] != user_id:
                    raise _SITE_CONFIRM_NOTICE_INERT.fire(ValueError(
                        f"confirm_notice: notice {notice_id!r} is inert — its {kind} {tid!r} no longer exists here "
                        f"(specs/0041 §11.6.6)"))
            record = self._redact_in_txn(user_id, kind, tid, _redaction.WITNESS_REASON, row_json=target[1],
                                         row_id=notice_id, fields_hint=json.loads(fields))
            return self._receipt_from_record(user_id, kind, tid, record, repeated=False)

    def _treated_on_arrival(self, user_id: str, kind: str, target_id: str, dump: dict):
        """Round 11 (R10-02): the shape a record ARRIVING under a COMPLETED attestation is written in — the PURE
        treatment (`treat_edge` / `treat_episode`, the same functions the redaction ran), validated under the model.
        No event and no attestation row is written: the attestation is complete and stays the original, so the next
        receipt is `repeated=True` with the ORIGINAL facts. If the arriving record carries content in a carrier the
        attestation never named, the store cannot attest it and the arrival is REFUSED (fail-closed) — the
        attestation is the authority, and it does not cover that field. Pure: returns (the treated record, the carriers
        it would need treated that the attestation does not name)."""
        if kind == "edge":
            new, treated = _redaction.treat_edge(dump, reason_registry=DISPOSITIONED_REASONS)
            model = Edge
        else:
            new, treated = _redaction.treat_episode(dump, reason_registry=DISPOSITIONED_REASONS,
                                                    recognised_kinds=_redaction.RECOGNISED_EPISODE_KINDS)
            model = Episode
        uncovered = sorted(set(treated) - set(self._attested_fields(user_id, kind, target_id, coverage=False)))
        return model.model_validate(new), uncovered      # the CALLER refuses a non-empty `uncovered` (one census id,
                                                         # one function: the refusal stays at the insert it guards)

    def _redaction_record(self, user_id: str, kind: str, target_id: str):
        # APPLIED only (T4): `redact()`'s repeat check. A PENDING or STANDING row is no redaction of the held record, so
        # before v16 a user's own redact() of a record a standing notice named (after a local write of its id)
        # returned `repeated=True` and treated NOTHING; the user's redaction now writes its own applied row
        return self._conn.execute(
            f"SELECT {self.RECORD_COLS} FROM redactions WHERE user_id=? AND target_kind=? AND target_id=? "
            f"AND {_APPLIED_SQL} ORDER BY recorded_at, id",
            (user_id, kind, target_id)).fetchone()

    def _surviving_derived(self, user_id: str, kind: str, target_id: str) -> list:
        """§11.5(3) as WIDENED by the owner (2026-10-02, given in the dev session; 0041 round 10): the records that may
        still carry the target's content, FOUND BY AN IDENTIFIER JOIN IN EITHER DIRECTION — derived from the target,
        or its source — NAMED so the caller can redact them; never redacted here (§4d). Each carries its `via`.

          an EDGE      the SURVIVORS the ledger records it as a contributor to (an absorption carries its content);
                       its OUTCOME episodes (`edge_id`), whose summaries quote it; its SOURCE episode(s) — the
                       interaction it was extracted from — sharing its `provenance.evidence_ref`;
          an EPISODE   consolidation OUTPUTS whose lineage names it (in the historical form, X19); the EDGES extracted
                       from it, sharing its `provenance.evidence_ref`.

        Same user only. A record that is itself attested-redacted is left out: it no longer carries the content.
        `evidence_ref` is preserved by the treatment (row 53), so the join holds after the redaction and on a repeat
        receipt. A caller-supplied evidence_ref can OVER-name — the conservative direction for a "may still carry
        it" list (noise, never a false guarantee). Dispute/correct summaries have no structural link this round;
        they are the NAMED DOMAIN `_quoting_domain` reports, not a list."""
        redacted = {"edge": self.redacted_targets(user_id, "edge"), "episode": self.redacted_targets(user_id, "episode")}
        out, seen = [], set()

        def name(k, rid, via, note):
            if (k, rid) in seen or rid in redacted[k] or (k, rid) == (kind, target_id):
                return
            seen.add((k, rid))
            out.append({"kind": k, "id": rid, "via": via, "note": note})
        table = "edges" if kind == "edge" else "episodes"
        row = self._conn.execute(f"SELECT json FROM {table} WHERE id=? AND user_id=?", (target_id, user_id)).fetchone()
        ev = (json.loads(row[0]).get("provenance") or {}).get("evidence_ref") if row else None
        if kind == "edge":
            for st, sid, site in self._conn.execute(
                    "SELECT DISTINCT survivor_type, survivor_id, site FROM contribution_ledger "
                    "WHERE user_id=? AND contributor_type='edge' AND contributor_ref=?", (user_id, target_id)):
                name(st, sid, f"contribution_ledger:{site}",
                     "a survivor this record contributed to; its content may derive from the redacted record")
            for eid, js in self._conn.execute("SELECT id, json FROM episodes WHERE user_id=?", (user_id,)):
                d = json.loads(js)
                if d.get("kind") == "outcome" and d.get("edge_id") == target_id:
                    name("episode", eid, "edge_id", "an outcome judgment whose summary quotes the redacted record")
                elif ev and (d.get("provenance") or {}).get("evidence_ref") == ev:
                    name("episode", eid, "evidence_ref",
                         "the source episode the redacted record was extracted from (it may quote the content)")
        else:
            # lineage carries the HISTORICAL form of each consumed input's id (X19), so the target is matched in
            # that form — a raw-id comparison never matched (round 10, found in the R9-03 fix: reachable when a
            # store holds an input live beside a restored output that consumed it elsewhere)
            hist = to_historical_id(target_id)
            for eid, js in self._conn.execute("SELECT id, json FROM episodes WHERE user_id=? AND id<>?", (user_id, target_id)):
                if hist in (json.loads(js).get("lineage") or []):
                    name("episode", eid, "lineage", "a consolidation output whose lineage names the redacted episode")
            if ev:
                for eid, js in self._conn.execute("SELECT id, json FROM edges WHERE user_id=?", (user_id,)):
                    if (json.loads(js).get("provenance") or {}).get("evidence_ref") == ev:
                        name("edge", eid, "evidence_ref", "a fact extracted from the redacted episode")
        return out

    # the NAMED DOMAIN for summaries with no structural link this round (the owner's ruling (ii), 2026-10-02, given in
    # the dev session): an edge that was disputed or corrected — or that REPLACED a corrected prior — is quoted by an
    # episode the receipt cannot list exactly; the domain says so. A structural link is a later spec's.
    QUOTING_DOMAIN = ("episodes quoting the record (dispute/correct summaries) — no exact list this round: the record "
                      "was disputed or corrected, and the episode that says so quotes it")

    def _quoting_domain(self, user_id: str, kind: str, target_id: str) -> bool:
        """Sound over every writer of a quoting summary: dispute retires the target `disputed`, a correction retires
        the prior `corrected` (the reason survives redaction, and so does the journal event), and a correction's
        REPLACEMENT — quoted as "… to '<its value>'" — supersedes a `corrected` prior."""
        if kind != "edge":
            return False
        quoting = ("disputed", "corrected")
        row = self._conn.execute("SELECT json FROM edges WHERE id=? AND user_id=?", (target_id, user_id)).fetchone()
        if row is None:
            return False
        d = json.loads(row[0])
        if d.get("invalidation_reason") in quoting:
            return True
        if self._conn.execute("SELECT 1 FROM edge_event WHERE user_id=? AND edge_id=? AND kind='invalidated' AND "
                              "reason IN (?,?) LIMIT 1", (user_id, target_id, *quoting)).fetchone():
            return True
        prior = d.get("supersedes")
        if prior:
            p = self._conn.execute("SELECT json FROM edges WHERE id=? AND user_id=?", (prior, user_id)).fetchone()
            if p is not None and json.loads(p[0]).get("invalidation_reason") == "corrected":
                return True
        return False

    _RECEIPT_DOMAINS = (
        "confirmations.request_digest (replaced with the marker; the row kept)",
        "supersession receipts (counts only, unlinked — §4f: no exact tier; may retain a plan digest over the content)",
        "policy_receipt (deployment audit, unlinked by content — may retain a recall over the content)",
    )

    def redact(self, user_id: str, *, edge_id: Optional[str] = None, episode_id: Optional[str] = None,
               reason: str):
        """specs/0041 §4a — ONE transaction, every carrier in the per-candidate map (§2d-iii-bis) or none.

        The target's own carriers are treated by `redaction.treat_edge` / `treat_episode` (REPLACE the
        marker · CLEAR the empty shape · the three-case reason rule · the two-branch kind rule); the
        duplicated `edges.subject/relation/object` columns follow the json (INV-2); the side tables follow
        the map (`confirmations.request_digest` REPLACE, the ledger's two digests CLEAR, the refusal rows'
        copied `relation` REPLACE, the embedding rows DELETED — INV-7's oracle); the journal is TOMBSTONED
        on every prior event and a `redacted` event closes it (§4c, INV-4); the episode journal gets its
        row (§4b-ii); the wiki cache is dropped (a derivation of the content). §4h(i): a redaction may not
        change a DERIVED DISPOSITION — a quarantine relation's edge keeps `quarantined` through the
        disclosure it does not redact, and any other disposition change REFUSES with nothing written.
        Idempotent BY CONTENT (§4b-ii): a second call writes nothing and returns the original receipt
        with `repeated=True`. INV-5: an unknown target, a cross-user target, both or neither target, and an
        unregistered reason refuse loudly — never a silent no-op."""
        with _SITE_REDACT_BOTH_OR_NEITHER.consult():
            if (edge_id is None) == (episode_id is None):
                raise _SITE_REDACT_BOTH_OR_NEITHER.fire(ValueError(
                    "redact takes exactly one of edge_id / episode_id (specs/0041 §4a)"), "both-or-neither")
        with _SITE_REDACT_REASON.consult():
            # round 11 (R10-04): a caller's redaction ORIGINATES here, so its reason is an originating one; the
            # witness label `imported_notice` is the import path's alone (the owner's ruling, 2026-10-03)
            if reason not in _redaction.ORIGINATING_REASONS:
                raise _SITE_REDACT_REASON.fire(ValueError(
                    f"redaction reason {reason!r} is not one of {_redaction.ORIGINATING_REASONS} — "
                    f"`{_redaction.WITNESS_REASON}` is written only when another store's notice is imported "
                    f"(specs/0041 §11.2)"))
        kind = "edge" if edge_id is not None else "episode"
        target_id = edge_id if edge_id is not None else episode_id
        table = "edges" if kind == "edge" else "episodes"
        with self._lock, self._write_txn():
            row = self._conn.execute(f"SELECT user_id, json FROM {table} WHERE id=?", (target_id,)).fetchone()
            with _SITE_REDACT_TARGET.consult():
                if row is None or row[0] != user_id:
                    # INV-5: the same refusal for absent and cross-user — the existence of another user's
                    # record is not disclosed by the shape of the error
                    raise _SITE_REDACT_TARGET.fire(ValueError(
                        f"redact: no {kind} {target_id!r} for user {user_id!r} (specs/0041 INV-5)"), "unknown-or-cross-user")
            prior = self._redaction_record(user_id, kind, target_id)
            if prior is not None:
                return self._receipt_from_record(user_id, kind, target_id, prior, repeated=True)
            # specs/0010 X21: a claimed episode is refused by the treatment body itself (`_redact_in_txn`), so
            # every caller — this one, confirm_notice and the import's notice treatments — passes ONE guard (R-A RA-01)
            record = self._redact_in_txn(user_id, kind, target_id, reason, row_json=row[1])
            return self._receipt_from_record(user_id, kind, target_id, record, repeated=False)

    def _redact_in_txn(self, user_id: str, kind: str, target_id: str, reason: str, *, row_json: str,
                       row_id: Optional[str] = None, fields_hint: Optional[list] = None,
                       source_body: Optional[str] = None, source_identity: Optional[tuple] = None):
        """The treatment, inside an OPEN journaled transaction (the caller holds the lock and `_write_txn`):
        the record's carriers, the side tables, the journal, the attestation row. `row_id` names the
        attestation row to write (the import's deterministic notice id; a fresh id otherwise) — and when a
        STANDING notice row already exists under that id (specs/0041 §4g, the record arrived after its
        notice), that row is completed in place rather than duplicated. Returns the record tuple.

        specs/0010 X21 (R-A RA-01): an episode CLAIMED by an in-flight consolidation is refused HERE, before any
        write, so no caller of the treatment can bypass the reservation — `redact` carried this check alone, and
        T4's `confirm_notice` (and the import's notice treatments) reached the body without it. The refusal raises
        inside the caller's transaction, which unwinds it whole."""
        if kind == "episode":
            with _SITE_REDACT_CLAIMED.consult():
                if target_id in self._reserved_ids(user_id):
                    raise _SITE_REDACT_CLAIMED.fire(ValueError(
                        f"redaction refuses episode {target_id!r}: it is claimed by an in-flight consolidation "
                        f"(specs/0010 X21; specs/0041 tranche 3)"))
        table = "edges" if kind == "edge" else "episodes"
        before_json = row_json
        before = json.loads(before_json)
        version_before = self.store_version(user_id)
        if kind == "edge":
            # §4h(i)'s quarantine re-establishment is inside the pure treatment (round 12, R11-01)
            new, treated = _redaction.treat_edge(before, reason_registry=DISPOSITIONED_REASONS)
            model_before, model_after = Edge.model_validate(before), Edge.model_validate(new)
            # the derived dispositions, read EXPLICITLY (0031's census admits no dynamic attribute form)
            dispositions = {
                "active": (model_before.active, model_after.active),
                "quarantined": (model_before.quarantined, model_after.quarantined),
                "needs_confirmation": (model_before.needs_confirmation, model_after.needs_confirmation),
                "ungrounded": (model_before.ungrounded, model_after.ungrounded)}
        else:
            new, treated = _redaction.treat_episode(before, reason_registry=DISPOSITIONED_REASONS,
                                                    recognised_kinds=_redaction.RECOGNISED_EPISODE_KINDS)
            model_before, model_after = Episode.model_validate(before), Episode.model_validate(new)
            dispositions = {
                "active": (model_before.active, model_after.active),
                "quarantined": (model_before.quarantined, model_after.quarantined),
                "use_only": (model_before.use_only, model_after.use_only)}
        with _SITE_REDACT_DISPOSITION.consult():
            moved = [name for name, (b, a) in dispositions.items() if b != a]
            if moved:
                raise _SITE_REDACT_DISPOSITION.fire(ValueError(
                    f"redact refuses {kind} {target_id!r}: the treatment would change a derived disposition "
                    f"{moved} (specs/0041 §4h(i)) — nothing written"))
        new_json = model_after.model_dump_json()
        # an applied notice (§4g): the record arrives already carrying the marker, so this store's treatment
        # finds little to do — the attestation names the SOURCE's carriers too (the notice's fields), never fewer.
        # Round 11 (R10-04's class): it names EVERY carrier holding its treated value after the operation — what this
        # call treated AND what already held it (an unattested marker row is redacted precisely to attest it, v15
        # §4b-ii) — so a redaction never attests nothing, and never exports a notice its own importer refuses
        fields = sorted(set(treated) | set(_redaction.already_treated(kind, before)) | set(fields_hint or []))
        event_ref = None
        if kind == "edge":
            self._conn.execute(
                "UPDATE edges SET json=?, subject=?, relation=?, object=?, quarantined=? WHERE id=?",
                (new_json, model_after.subject, model_after.relation, model_after.object,
                 int(model_after.quarantined), target_id))
            # the side tables (rows 7, 21/23, 59/64) and the oracle (INV-7)
            n = self._conn.execute("UPDATE confirmations SET request_digest=? WHERE user_id=? AND edge_id=?",
                                   (_redaction.MARKER, user_id, target_id)).rowcount
            if n:
                fields.append("confirmations.request_digest")
            # specs/0008 v7 §6g / 0041 §2d-iii-bis: every verb's registry row whose target is the edge — after it, a
            # retry under that id is TERMINAL (`request_redacted`), never a replay
            n = self._conn.execute("UPDATE request_registry SET request_digest=? WHERE user_id=? AND target_edge_id=?",
                                   (_redaction.MARKER, user_id, target_id)).rowcount
            if n:
                fields.append("request_registry.request_digest")
            # specs/0041 §11.6.2 (amendment `0047/0041-replies`, INV-RR2/RR5): every reply's TEXT and every reply's
            # request DIGEST on the edge are REPLACED; the rows, kinds, targets, actors and positions are kept
            # (append-only). A resolve's NULL text stays NULL. A row already at the marker is this carrier at its
            # treated value, so it is attested too (the UPDATE counts matched rows, as for confirmations)
            n = self._conn.execute("UPDATE replies SET text=? WHERE user_id=? AND edge_id=? AND text IS NOT NULL",
                                   (_redaction.MARKER, user_id, target_id)).rowcount
            if n:
                fields.append("replies.text")
            n = self._conn.execute("UPDATE replies SET request_digest=? WHERE user_id=? AND edge_id=?",
                                   (_redaction.MARKER, user_id, target_id)).rowcount
            if n:
                fields.append("replies.request_digest")
            # rows 21/23, joined by user, KIND and id in both absorption directions (round-9 R9-03): edges and
            # episodes are independent id namespaces in this table, so a raw-id match cleared an unrelated
            # episode's digests when an edge shared its id
            n = self._conn.execute(
                "UPDATE contribution_ledger SET identity_digest=NULL, evidence_ref_digest=NULL "
                "WHERE user_id=? AND ((survivor_type='edge' AND survivor_id=?) "
                "OR (contributor_type='edge' AND contributor_ref=?)) "
                "AND (identity_digest IS NOT NULL OR evidence_ref_digest IS NOT NULL)",
                (user_id, target_id, target_id)).rowcount
            if n:
                fields.extend(["contribution_ledger.identity_digest", "contribution_ledger.evidence_ref_digest"])
            n = self._conn.execute(
                "UPDATE supersession_refusals SET relation=? WHERE user_id=? AND (prior_edge_id=? OR incoming_edge_id=?) "
                "AND relation<>?", (_redaction.MARKER, user_id, target_id, target_id, _redaction.MARKER)).rowcount
            # round 14 (N13-01): a refusal row links TWO edges — either end matches — so a row the OTHER edge's
            # redaction already marked never reached this union through the update's changed-row count. A row linked
            # to this edge at either end and already AT the marker is this carrier at its treated value: attested, as
            # the shared revocation row is (N12-02). `relation` is NOT NULL and REPLACE-treated, so the marker there is
            # distinguishable from content — unlike the ledger's CLEAR digests (round 14's measured limit)
            if n or self._conn.execute(
                    "SELECT 1 FROM supersession_refusals WHERE user_id=? AND (prior_edge_id=? OR incoming_edge_id=?) "
                    "AND relation=? LIMIT 1", (user_id, target_id, target_id, _redaction.MARKER)).fetchone():
                fields.append("supersession_refusals.relation")
            n = self._conn.execute("DELETE FROM edge_embedding WHERE user_id=? AND edge_id=?",
                                   (user_id, target_id)).rowcount
            if n:
                fields.append("edge_embedding")
            # §4c: tombstone every prior event, then the `redacted` event with the reason (INV-4); round 12 (R11-02):
            # a prior state that still held a value is a carrier this redaction treated — recorded as bookkeeping
            n = self._conn.execute("UPDATE edge_event SET state=? WHERE user_id=? AND edge_id=? AND state<>?",
                                   (_redaction.MARKER, user_id, target_id, _redaction.MARKER)).rowcount
            if n:
                fields.append("journal.state")
            self._journal_edge_write(user_id, target_id, new_json, before_json, kind="redacted", reason=reason)
            seq = self._conn.execute("SELECT MAX(seq) FROM edge_event WHERE user_id=? AND edge_id=?",
                                     (user_id, target_id)).fetchone()[0]
            event_ref = f"{user_id}:{seq}"
        else:
            self._conn.execute("UPDATE episodes SET json=? WHERE id=?", (new_json, target_id))
            # §4b-ii: the episode journal row — its own per-user seq/txn space, the store's clock
            seq = 1 + (self._conn.execute("SELECT COALESCE(MAX(seq), 0) FROM episode_event WHERE user_id=?",
                                          (user_id,)).fetchone()[0])
            txn = 1 + (self._conn.execute("SELECT COALESCE(MAX(txn), 0) FROM episode_event WHERE user_id=?",
                                          (user_id,)).fetchone()[0])
            self._conn.execute(
                "INSERT INTO episode_event(user_id, seq, txn, episode_id, kind, reason, state, recorded_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (user_id, seq, txn, target_id, "redacted", reason, new_json, self._now().isoformat()))
            event_ref = f"{user_id}:episode:{seq}"
            # rows 21/23 for an episode (round-9 R9-03: the treatment existed only in the edge branch): the rows
            # whose SURVIVOR is this episode — a consolidation output's ledger. An episode is never a recorded
            # CONTRIBUTOR (contributor_type is 'edge' or NULL: a consolidation row names its inputs only through
            # op_key), so the survivor direction is the whole of it.
            n = self._conn.execute(
                "UPDATE contribution_ledger SET identity_digest=NULL, evidence_ref_digest=NULL "
                "WHERE user_id=? AND survivor_type='episode' AND survivor_id=? "
                "AND (identity_digest IS NOT NULL OR evidence_ref_digest IS NOT NULL)",
                (user_id, target_id)).rowcount
            if n:
                fields.extend(["contribution_ledger.identity_digest", "contribution_ledger.evidence_ref_digest"])
        # §11.2 (round 10, R9-02(d)): the source-revocation rows linked to this record's SOURCE carry their stored
        # prose to the marker, through THE ONE UPDATER 0022 §4a now admits — inside this transaction, `reason` only,
        # so the standing state those rows derive cannot change. Both kinds: the identity is the record's source.
        from ..scope_linkage import identity_digest_of as _identity_digest_of
        from .revocation import redact_revocation_reasons as _redact_revocation_reasons
        from .revocation import revocation_reason_marked as _revocation_reason_marked
        _prov = before.get("provenance") or {}
        _digest = _identity_digest_of(_prov.get("origin"), _prov.get("source_id"), self.local_origin())
        # round 13 (N12-02): the revocation rows are SHARED by every record of the source, and the updater reports only
        # the rows IT changed — so a row another record's redaction already marked never entered this union, and an
        # empty record of a redacted source read "nothing to redact". A row already at the marker is this carrier at
        # its treated value: attested here like a record carrier already holding the marker (already_treated).
        if _digest is not None and (_redact_revocation_reasons(self._conn, user_id, _digest)
                                    or _revocation_reason_marked(self._conn, user_id, _digest)):
            fields.append("source_revocations.reason")
        # round 12 (R11-02): "nothing to redact" is decided HERE, over the whole surface the treatment reached — the
        # record, its side tables, its journal, the linked revocation prose — never from the live record alone (an
        # edge emptied by an ordinary write still carries its content in the journal and its side rows). The raise is
        # inside the caller's transaction: every statement above rolls back, so nothing is written. The owner's
        # ruling (2026-10-03) unchanged: a record with no covered content or marker ANYWHERE is refused.
        with _SITE_REDACT_NOTHING.consult():
            if not fields:
                raise _SITE_REDACT_NOTHING.fire(ValueError(
                    f"redact refuses {kind} {target_id!r}: nothing to redact — no carrier, side row or journal state "
                    f"holds content or the marker (specs/0041 §4b-ii; the owner's ruling, 2026-10-03) — nothing written"))
        # the attestation's fields as ONE canonical SET — side-table and journal paths are appended after the first
        # set-and-sort, so a store's own export listed them in another order than the canonical body a relay re-exports,
        # and an applied notice whose hint already named one listed it TWICE (round 12; the duplicate since round 10)
        fields = sorted(set(fields))
        self._conn.execute("DELETE FROM wiki WHERE user_id=?", (user_id,))     # a derivation of the content
        self._bump(user_id)
        version_after = self.store_version(user_id)
        recorded_at = self._now().isoformat()
        rid = row_id or ("rd-" + uuid.uuid4().hex)
        waiting = self._conn.execute("SELECT 1 FROM redactions WHERE id=? AND state IN ('pending', 'standing')",
                                     (rid,)).fetchone()
        if waiting is not None:
            # §4g / §11.6.6: a PENDING or STANDING notice becomes APPLIED in place, never duplicated — its foreign body
            # (source_body, the source identity) unchanged; its fields are THIS store's total treatment
            self._conn.execute(
                "UPDATE redactions SET fields=?, marker_version=?, store_version_before=?, store_version_after=?, "
                "event_ref=?, recorded_at=?, state='applied', pending_reason=NULL WHERE id=?",
                (json.dumps(fields), _redaction.MARKER_VERSION, version_before, version_after, event_ref, recorded_at, rid))
        else:
            self._conn.execute(
                "INSERT INTO redactions(id, user_id, target_kind, target_id, fields, marker_version, reason, "
                "store_version_before, store_version_after, event_ref, recorded_at, source_body, source_origin, "
                "source_user, source_event_ref) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rid, user_id, kind, target_id, json.dumps(fields), _redaction.MARKER_VERSION, reason,
                 version_before, version_after, event_ref, recorded_at, source_body,
                 *(source_identity or (None, None, None))))
        return self._conn.execute(f"SELECT {self.RECORD_COLS} FROM redactions WHERE id=?", (rid,)).fetchone()

    def _receipt_from_record(self, user_id, kind, target_id, record, *, repeated: bool):
        """The receipt IS the attestation record read back (§4b-ii): a repeat returns the ORIGINAL's fields,
        not an equal-looking new one. A WITNESSED redaction (an imported notice) holds no original receipt here:
        its original facts come from the notice's immutable foreign body — the SOURCE's reason, time, store
        versions and event — and are None where the body does not carry them (round 10, R9-05: never this
        store's counters standing in for an unknown); this store's own application facts are reported beside
        them under their own names."""
        rid, fields, mv, reason, vb, va, event_ref, recorded_at, source_body, _s_origin, _s_user, s_event = record
        common = dict(redacted_kind=kind, target_id=target_id, user_id=user_id, fields_cleared=json.loads(fields),
                      repeated=repeated, receipts_complete=False,
                      receipt_domains=(list(self._RECEIPT_DOMAINS)
                                       + ([self.QUOTING_DOMAIN] if self._quoting_domain(user_id, kind, target_id) else [])),
                      surviving_derived=self._surviving_derived(user_id, kind, target_id))
        if _s_origin is None:                     # round 11 (R10-04): a LOCAL redaction — by the record, never the reason
            return _redaction.RedactionReceipt(
                reason=reason, marker_version=mv, store_version_before=vb, store_version_after=va,
                recorded_at=recorded_at, event_ref=event_ref, reconstructed=False, **common)
        body = json.loads(source_body) if source_body is not None else {}      # this store's own canonical write
        return _redaction.RedactionReceipt(
            reason=body.get("reason", reason), marker_version=body.get("marker_version"),
            store_version_before=body.get("store_version_before"), store_version_after=body.get("store_version_after"),
            recorded_at=body.get("recorded_at"), event_ref=s_event, reconstructed=True,
            applied_at=recorded_at, applied_store_version_before=vb, applied_store_version_after=va,
            applied_event_ref=event_ref, **common)

    def forget_user(self, user_id) -> dict:
        with self._lock, self._write_txn():
            n_edges = self._conn.execute(
                "SELECT COUNT(*) FROM edges WHERE user_id=?", (user_id,)).fetchone()[0]
            n_eps = self._conn.execute(
                "SELECT COUNT(*) FROM episodes WHERE user_id=?", (user_id,)).fetchone()[0]
            # specs/0008 §6d: the data-subject erasure deletes the confirmations
            # too — they are removed with the edges they belong to — and COUNTS them.
            n_conf = self._conn.execute(
                "SELECT COUNT(*) FROM confirmations WHERE user_id=?",
                (user_id,)).fetchone()[0]
            # specs/0047 INV-R22: the replies go with them, and are counted beside them (research's T10a Q15)
            n_replies = self._conn.execute("SELECT COUNT(*) FROM replies WHERE user_id=?", (user_id,)).fetchone()[0]
            # specs/0010 X17: consolidation operation state is per-user erasable data —
            # forget_user removes it atomically with the rest of the user's memory.
            # specs/0003 §4f: the refusal inventory and the operation receipts are
            # user-linked Store-local metadata, so erasure covers them too.
            # specs/0027 §4f (V-ERASE): the user's embedding rows go in the
            # SAME transaction — erasure requires the bytes gone; V-FRESH
            # blocking recall of an orphan does not satisfy erasure.
            # specs/0029 §4f (V-ERASE): the user's events go in the SAME
            # transaction — the journal is erasable data, and this is the ONE
            # place that deletes from it (V-APPEND names this statement).
            self._conn.execute("DELETE FROM edge_event WHERE user_id=?", (user_id,))
            for table in _ERASE_TABLES:
                if table == "edge_event":
                    continue                      # deleted above, by name
                self._conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
        return {"edges": n_edges, "episodes": n_eps, "confirmations": n_conf, "replies": n_replies}

    # -- the durable policy receipt (specs/0027 §4g, v14) -------------------
    _RECEIPT_COLUMNS = ("recall_id", "policy_id", "policy_version", "recorded_at", "receipt")

    def write_policy_receipt(self, user_id, row) -> None:
        """One committed INSERT under the instance lock. Not an edge write:
        nothing is journaled and `_write_txn`'s allocation discipline does not
        apply; the 0007 §4c busy-timeout discipline does, and a lock that
        cannot be taken raises through `recall` (V-RECEIPT-DURABLE-OR-LOUD).
        The PK refuses a second row for a minted `recall_id` — a receipt is
        written once, never replaced."""
        missing = [c for c in self._RECEIPT_COLUMNS if c not in row]
        if missing:
            raise ValueError(f"write_policy_receipt: row lacks {missing}")
        with self._lock:
            self._conn.execute(
                "INSERT INTO policy_receipt(user_id,recall_id,policy_id,policy_version,"
                "recorded_at,receipt) VALUES(?,?,?,?,?,?)",
                (user_id, row["recall_id"], row["policy_id"], row["policy_version"],
                 row["recorded_at"], row["receipt"]))
            self._conn.commit()

    def policy_receipts(self, user_id, *, limit=None) -> list:
        sql = ("SELECT recall_id,policy_id,policy_version,recorded_at,receipt FROM policy_receipt "
               "WHERE user_id=? ORDER BY recorded_at DESC, recall_id DESC")
        params = [user_id]
        if limit is not None:
            if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
                raise ValueError(f"policy_receipts: limit must be a positive int, got {limit!r}")
            sql += " LIMIT ?"
            params.append(limit)
        return [dict(zip(self._RECEIPT_COLUMNS, r))
                for r in self._conn.execute(sql, params).fetchall()]

    def policy_receipt(self, user_id, recall_id):
        r = self._conn.execute(
            "SELECT recall_id,policy_id,policy_version,recorded_at,receipt FROM policy_receipt "
            "WHERE user_id=? AND recall_id=?", (user_id, recall_id)).fetchone()
        return None if r is None else dict(zip(self._RECEIPT_COLUMNS, r))

    # -- semantic lane (specs/0027 §4f) -------------------------------------
    def upsert_embedding(self, *, edge_id, user_id, embedder_id,
                         content_digest, dim, vec, built_at) -> bool:
        """specs/0027 §4f's delayed writer, made ONE transaction under the DATABASE lock (specs/0041 §4e,
        tranche 5): `BEGIN IMMEDIATE` BEFORE the read, so the row this worker checks its digest against is
        the row its vector is stored beside — a second connection's redaction cannot land between the SELECT
        and the INSERT (round-2 F1's two-connection race). An instance lock never serialised across
        connections. The lock refusal is the 0007 §4c form: busy_timeout, then refuse loudly naming the
        site — never a silent skip. Joins an already-open transaction rather than nesting."""
        from .. import semantic as _semantic
        with self._lock:
            opened = False
            if not self._conn.in_transaction:
                with _SITE_EMBEDDING_TXN_LOCKED.consult():
                    try:
                        self._conn.execute("BEGIN IMMEDIATE")
                    except sqlite3.OperationalError as e:
                        raise _SITE_EMBEDDING_TXN_LOCKED.fire(sqlite3.OperationalError(
                            f"could not take the write lock for the embedding upsert ({e}) — the read and the "
                            f"publish are one transaction, and a read outside it is the race (specs/0041 §4e; "
                            f"0007 §4c)")) from e
                opened = True
            try:
                return self._upsert_embedding_in_txn(edge_id, user_id, embedder_id, content_digest, dim, vec, built_at, _semantic)
            except BaseException:
                if opened and self._conn.in_transaction:
                    self._conn.rollback()
                raise

    def _upsert_embedding_in_txn(self, edge_id, user_id, embedder_id, content_digest, dim, vec, built_at, _semantic) -> bool:
        if True:
            row = self._conn.execute(
                "SELECT json FROM edges WHERE id=? AND user_id=?",
                (edge_id, user_id)).fetchone()
            with _SITE_EMBEDDING_DELAYED_WRITER.consult():
                if row is None:
                    # erase-vs-worker: after forget_user there is no live edge —
                    # the delayed worker writes nothing (0027 §4f)
                    self._conn.rollback()
                    return _SITE_EMBEDDING_DELAYED_WRITER.fire(False, "refuse")
            live = Edge.model_validate_json(row[0])
            with _SITE_EMBEDDING_STALE_CONTENT.consult():
                if _semantic.content_digest(live) != content_digest:
                    # update-vs-worker: the edge moved under the worker — drop it;
                    # the re-embed of the NEW content writes its own tuple
                    self._conn.rollback()
                    return _SITE_EMBEDDING_STALE_CONTENT.fire(False, "refuse")
            self._conn.execute(
                "INSERT INTO edge_embedding(edge_id, user_id, embedder_id, "
                "content_digest, dim, vec, built_at) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(edge_id, embedder_id, content_digest) DO NOTHING",
                (edge_id, user_id, embedder_id, content_digest, dim, vec,
                 built_at))
            self._conn.commit()
            return True

    def semantic_candidates(self, user_id, query_vec, *, embedder_id, dim,
                            k, min_cosine, visible_ids=None) -> list:
        from .. import semantic as _semantic
        rows = self._conn.execute(
            "SELECT ee.edge_id, ee.content_digest, ee.vec, e.json "
            "FROM edge_embedding ee "
            "JOIN edges e ON e.id = ee.edge_id AND e.user_id = ee.user_id "
            "WHERE ee.user_id=? AND ee.embedder_id=? AND ee.dim=?",
            (user_id, embedder_id, dim)).fetchall()
        out = []
        for eid, cdig, blob, ejson in rows:
            if visible_ids is not None and eid not in visible_ids:
                continue                       # scope BEFORE top-k (Stage 1)
            live = Edge.model_validate_json(ejson)
            if _semantic.content_digest(live) != cdig:
                continue                       # V-FRESH: stale vector excluded
            vec = _semantic.unpack_vec(blob, dim)
            if vec is None:
                continue                       # wrong-length blob refused (V5)
            c = _semantic.cosine(query_vec, vec)
            if c is None or c < min_cosine:
                continue
            out.append((eid, c))
        out.sort(key=lambda t: (-t[1], t[0]))  # cosine desc, edge_id asc
        return out[:k]

    def embedding_keys(self, user_id, embedder_id) -> set:
        rows = self._conn.execute(
            "SELECT edge_id, content_digest FROM edge_embedding "
            "WHERE user_id=? AND embedder_id=?",
            (user_id, embedder_id)).fetchall()
        return set(rows)

    # -- compiled-view cache ----------------------------------------------
    def get_wiki(self, user_id) -> Optional[tuple[str, int]]:
        row = self._conn.execute("SELECT text, store_version FROM wiki WHERE user_id=?",
                                 (user_id,)).fetchone()
        return (row[0], row[1]) if row else None

    def set_wiki(self, user_id, text, store_version) -> bool:
        """specs/0041 §4e (tranche 5): the wiki PUBLISH is ONE conditional statement — written only if the
        user's write counter still equals `store_version`, the value the compile read BEFORE its inputs. The
        check and the write are the same statement, so no second connection can move the store between them
        (a redaction bumps the counter, so a compile that read the content before it can never publish it).
        Returns whether the row was written; a stale compile publishes nothing and the next read recompiles."""
        with self._lock:
            n = self._conn.execute(
                "INSERT OR REPLACE INTO wiki(user_id,text,store_version) "
                "SELECT ?,?,? WHERE COALESCE((SELECT n FROM write_counter WHERE user_id=?), 0) = ?",
                (user_id, text, store_version, user_id, store_version)).rowcount
            self._conn.commit()
            return n == 1

    def discard_wiki(self, user_id, text, store_version) -> bool:
        """R-II round 2's RII-R2-01 (D2): delete the wiki row only if it is still `(text, store_version)` — one
        conditional statement, so a row a later compile published is never dropped."""
        with self._lock:
            n = self._conn.execute("DELETE FROM wiki WHERE user_id=? AND text=? AND store_version=?",
                                   (user_id, text, store_version)).rowcount
            self._conn.commit()
            return n == 1

    def store_version(self, user_id) -> int:
        row = self._conn.execute("SELECT n FROM write_counter WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else 0

    def close(self) -> None:
        self._conn.close()
