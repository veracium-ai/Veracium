"""specs/0022 §4b — the NORMATIVE reference for source revocation: the
standing-state derivation, the completeness classifier, and the sweep (v1,
draft).

PORTABLE AND PURE: no I/O, no store dependency, no clock. A conforming
implementation must agree with this module on every pinned vector; the
vectors live beside it in `vectors.json`, the SELF-EXECUTING HARNESS
(`vector_harness.py`) runs them, and 0022 R11 binds implementations to
both. The pattern is `specs/evidence/0020/reference_scope.py`, which is
what let the scope surface survive fourteen review rounds: the decidable
core lives in one executable place, so a disagreement between two
implementations is a failing vector rather than an argument.

THE DECIDABLE CORE, stated once:

  Given a user's records, that user's 0014 contribution rows, that user's
  APPEND-ONLY `source_revocations` rows, and an optional PROPOSED action
  (revoke / lift a resolved identity), compute:

    (1) the STANDING revocation set   — derived, never stored;
    (2) each affected survivor's COMPLETENESS CLASS and BASIS;
    (3) the effect list (retire / recompute / reinstate);
    (4) the COMPLETENESS STATEMENT — the blast radius AND the blind spot.

FOUR PROPERTIES THIS MODULE EXISTS TO MAKE FALSIFIABLE:

  * ONE COMPUTATION, FOUR CALLERS (0022 §4e). `sweep()` is a pure function
    of (store, proposed action). Dry-run revoke, committed revoke, dry-run
    lift and committed lift differ ONLY in whether the caller then applies
    the returned effects. A preview that can diverge from the commit is
    the classic defect in this shape of feature, so preview and commit are
    not two code paths here — they are one call and a boolean the callee
    never sees.

  * DESIRED-STATE, NOT UNDO (0022 §4f). A lift does not replay an effect
    log backwards. Both directions re-derive the desired state from the
    STANDING set, which is the only construction that gets the overlapping
    case right: a record whose basis is revoked by TWO sources must stay
    retired when one of them is lifted. An undo log gets that cell wrong.

  * RESTRICT-ONLY, INCLUDING THE RECOMPUTE (0022 §4d). The recompute is
    the SHIPPED absorption transform — min(valid_from), max(observed_at),
    max(confidence) over the surviving sides — which is monotone under
    contributor REMOVAL, and it is additionally CLAMPED against the
    survivor's current values so that a non-monotone aggregator could
    still never grant. `ungrounded` is RATCHETED and never recomputed:
    it is an N-ary OR, so re-deriving it over a SMALLER set can flip it
    True→False, which is a promotion wearing a recompute's clothes.

  * SUPERSEDE-NEVER-ERASE (0022 §4f). `apply_effects` returns a NEW store,
    never mutates its input, never removes a record, and appends every
    superseded value to `history`.

WHAT THIS MODULE DELIBERATELY DOES NOT DEFINE (one definition, one
carrier — the carrier-completeness rule):

  * the identity RESOLUTION and DIGEST construction beyond mirroring the
    shipped `veracium.source-id.v1` primitive byte-for-byte (0006 owns it);
  * whether a derivative is store-authored (0020 §4a-ii's normative
    predicate owns it) — this module reads the SITE of the ledger rows,
    which is a present field, not a re-derived judgement;
  * anything about ingest, maintenance or import behaviour under a
    standing revocation — that is 0023, and this reference is silent on it
    on purpose.
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional

# ---- the shipped digest construction, mirrored EXACTLY (0006 §4 rules 6-7) --

_DOMAIN = b"veracium.source-id.v1"
IDENTITY_MAX = 512                      # the shipped Provenance field bounds

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")

# ---- the closed vocabularies ----------------------------------------------

ACTIONS = ("revoke", "lift")

#: the completeness classes — BY CAPABILITY, never by era (0022 §4c)
CLASS_LINKED = "class-a-linked"            # typed link present: the graph walks
CLASS_LINKLESS = "class-b-linkless"        # survivor named, graph does not walk
CLASS_UNATTRIBUTED = "class-c-unattributed"  # no rows at all: unreachable

BASIS_SOLE = "sole-basis"
BASIS_CORROBORATED = "corroborated"

#: what a survivor IS, read from the SITE of its rows — a synthesized record's
#: content was written by the LLM over its contributor set; a restatement's
#: content is its own testimony and the contributors only moved its maxima.
KIND_SYNTHESIZED = "synthesized"
KIND_RESTATEMENT = "restatement"

SITE_CONSOLIDATION = "consolidation"
SITE_ABSORPTION = "absorption"

#: the CLOSED effect vocabulary. There is no `delete` and no `edit` verb, and
#: their absence is asserted by a vector: C3 (supersede-never-erase) is a
#: property of the vocabulary before it is a property of any implementation.
EFFECT_VERBS = frozenset({"retire", "recompute", "reinstate"})

RETIREMENT_REASON = "revoked_source"

#: the three fields the shipped absorption transform recomputes (graph.py's
#: inheritance, verified against contribution.py's replay check). `ungrounded`,
#: `disclosure` and `derived_from` are NOT in this set, by the ratchet rule.
RECOMPUTED_FIELDS = ("valid_from", "observed_at", "confidence")


class RevocationError(ValueError):
    """A malformed or undecidable input. Every refusal in this module is this
    class or a subclass: fail closed, never a best-effort partial sweep."""


class RevocationLinkageError(RevocationError):
    """Corrupt attribution linkage — a self-naming contribution row. The 0020
    post-acceptance defect (a self-absorbing record looping a walker) is the
    reason this is a REFUSAL and not a `continue`."""


# ---- identity --------------------------------------------------------------

def _framed(b: bytes) -> bytes:
    return len(b).to_bytes(4, "big") + b


def resolve_origin(stored_origin: Optional[str], local_origin: str) -> str:
    """0006's resolve-at-read chokepoint, mirrored: an absent origin is the
    local store's singleton BEFORE any comparison, grouping or digest."""
    if not isinstance(local_origin, str) or not local_origin:
        raise RevocationError("local_origin must be a non-empty str")
    return local_origin if stored_origin is None else stored_origin


def _bounded(value, name):
    if value is None:
        return None
    if not isinstance(value, str) or not (1 <= len(value) <= IDENTITY_MAX):
        raise RevocationError(
            f"{name} must be absent or a str of 1..{IDENTITY_MAX} chars "
            f"(the shipped Provenance bounds) — got {value!r}")
    return value


def digest_of(origin: Optional[str], source_id: Optional[str],
              local_origin: str) -> Optional[str]:
    """The shipped `source_identity_digest` over the RESOLVED pair.

    None when `source_id` is absent: an absent source_id yields NO groupable
    identity and therefore NO digest, so such a record is NOT REVOCABLE BY
    SOURCE at all (0006's absence rule, whose own acceptance test already
    asserts that a revocation matches neither of two source_id-less records).
    That is inherited, not invented here."""
    origin = _bounded(origin, "origin")
    source_id = _bounded(source_id, "source_id")
    if source_id is None:
        return None
    resolved = resolve_origin(origin, local_origin)
    payload = (_DOMAIN + _framed(resolved.encode("utf-8"))
               + _framed(source_id.encode("utf-8")))
    return hashlib.sha256(payload).hexdigest()


# ---- the append-only table and the DERIVED standing state ------------------

_REVOCATION_FIELDS = ("user_id", "identity_digest", "action", "at", "seq",
                      "reason")


def validate_revocation_row(row) -> dict:
    """One row of the APPEND-ONLY `source_revocations` table.

    Presence is required SEPARATELY from value validity: `None` is a value and
    absence is not, and a validator built on `.get()` accepts a deleted key as
    a default (the defect class 0021's row validator was returned for twice)."""
    if not isinstance(row, dict):
        raise RevocationError(f"revocation row must be a dict — got {row!r}")
    missing = [f for f in _REVOCATION_FIELDS if f not in row]
    extra = [f for f in row if f not in _REVOCATION_FIELDS]
    if missing or extra:
        raise RevocationError(
            f"revocation row field set is CLOSED: missing={missing} "
            f"unknown={extra}")
    if not isinstance(row["user_id"], str) or not row["user_id"]:
        raise RevocationError("user_id must be a non-empty str")
    d = row["identity_digest"]
    if not isinstance(d, str) or not _DIGEST_RE.fullmatch(d):
        # A NULL digest must never reach this table: it would be a
        # `(resolved_origin, NULL)` pseudo-source, which 0006 forbids, and it
        # would revoke every unknown-source record in one row.
        raise RevocationError(
            f"identity_digest must be 64 lowercase hex — got {d!r}; an absent "
            f"source_id has NO digest and is not revocable by source")
    if row["action"] not in ACTIONS:
        raise RevocationError(
            f"action must be one of {ACTIONS} — got {row['action']!r}")
    if not isinstance(row["at"], str) or not _TS_RE.fullmatch(row["at"]):
        raise RevocationError(f"at must be an ISO-8601 Z timestamp — "
                              f"got {row['at']!r}")
    if not isinstance(row["seq"], int) or isinstance(row["seq"], bool) \
            or row["seq"] < 0:
        raise RevocationError(f"seq must be a non-negative int (a real int: "
                              f"bools refuse) — got {row['seq']!r}")
    if not isinstance(row["reason"], str) or not row["reason"].strip():
        raise RevocationError("reason must be a non-empty str — a revocation "
                              "with no recorded reason is not auditable")
    return row


def standing_revocations(rows, user_id: str) -> frozenset:
    """THE STANDING STATE IS DERIVED, NEVER STORED (0022 §4a).

    `source_revocations` is APPEND-ONLY — a revoke row and, later, a lifting
    row. The standing set is the LATEST row per (user, identity digest) by
    (at, seq); there is no UPDATE, no `active` column and no row that is
    edited in place. This resolves the mutable-state-vs-insert-only seam the
    ledger already settled (0014's insert-only discipline) rather than leaving
    a second, contradictory answer in the store.

    `seq` is the per-user append ordinal and is UNIQUE: two rows sharing one
    ordinal make the latest-row rule undecidable, so they REFUSE rather than
    resolve by dict order."""
    if not isinstance(user_id, str) or not user_id:
        raise RevocationError("user_id must be a non-empty str")
    latest: dict = {}
    seen_seq: dict = {}
    for row in rows:
        validate_revocation_row(row)
        if row["user_id"] != user_id:
            continue
        key = row["seq"]
        if key in seen_seq and seen_seq[key] != row:
            raise RevocationError(
                f"two DIFFERENT rows share append ordinal seq={key} — the "
                f"latest-row rule is undecidable; the table is append-only "
                f"with a unique per-user ordinal")
        seen_seq[key] = row
        d = row["identity_digest"]
        prev = latest.get(d)
        if prev is None or (row["at"], row["seq"]) > (prev["at"], prev["seq"]):
            latest[d] = row
    return frozenset(d for d, row in latest.items()
                     if row["action"] == "revoke")


def with_proposed(rows, user_id: str, action: Optional[dict]):
    """The rows a PROPOSED action would produce, WITHOUT writing anything.

    This is the single place the preview and the commit diverge, and they
    diverge before the computation rather than inside it: both callers run the
    identical `sweep()` over the identical row list."""
    rows = list(rows)
    if action is None:
        return rows
    if set(action) != {"identity_digest", "action", "at", "reason"}:
        raise RevocationError(
            "a proposed action carries exactly identity_digest, action, at, "
            f"reason — got {sorted(action)}")
    nxt = 1 + max([r["seq"] for r in rows
                   if validate_revocation_row(r)["user_id"] == user_id],
                  default=-1)
    rows.append({"user_id": user_id, "seq": nxt, **action})
    validate_revocation_row(rows[-1])
    return rows


# ---- the 0014 contribution rows -------------------------------------------

_ROW_FIELDS = ("user_id", "survivor_type", "survivor_id", "site",
               "identity_digest", "evidence_ref_digest", "payload", "op_key",
               "contributor_type", "contributor_ref")


def validate_contribution_row(row) -> dict:
    """The SHIPPED ten-field stored row (0014, as amended by 0021's typed
    link). Presence required separately from value validity, as above."""
    if not isinstance(row, dict):
        raise RevocationError(f"contribution row must be a dict — got {row!r}")
    missing = [f for f in _ROW_FIELDS if f not in row]
    if missing:
        raise RevocationError(f"contribution row missing fields: {missing}")
    if not isinstance(row["survivor_type"], str) or not row["survivor_type"]:
        raise RevocationError("survivor_type must be a non-empty str")
    if not isinstance(row["survivor_id"], str) or not row["survivor_id"]:
        raise RevocationError("survivor_id must be a non-empty str")
    if not isinstance(row["site"], str) or not row["site"]:
        raise RevocationError("site must be a non-empty str")
    d = row["identity_digest"]
    if d is not None and (not isinstance(d, str) or not _DIGEST_RE.fullmatch(d)):
        raise RevocationError(f"identity_digest must be 64 hex or None — {d!r}")
    ref, ctype = row["contributor_ref"], row["contributor_type"]
    if ref is not None and (not isinstance(ref, str) or not ref):
        raise RevocationError(f"contributor_ref must be a non-empty str or "
                              f"None — got {ref!r}")
    if (ref is None) != (ctype is None):
        # A half-typed link is corrupt, not legacy: legacy rows carry BOTH
        # columns NULL. Fail closed rather than guessing which half is right.
        raise RevocationError(
            f"contributor_type and contributor_ref must be present together "
            f"or absent together — got {ctype!r} / {ref!r}")
    if row["contributor_ref"] is not None \
            and row["contributor_ref"] == row["survivor_id"] \
            and row["contributor_type"] == row["survivor_type"]:
        raise RevocationLinkageError(
            f"contribution row names its own survivor "
            f"({row['survivor_type']}:{row['survivor_id']}) as its "
            f"contributor — corrupt linkage REFUSES; a walker that treated "
            f"this as data would not terminate")
    return row


def row_class(row) -> str:
    """The row's CAPABILITY, which is what the class is about.

    (a) a typed link — `contributor_ref` present — lets the sweep walk the
        contributor graph transitively;
    (b) a LINKLESS row — `identity_digest` present, `contributor_ref` NULL —
        identifies the SURVIVOR completely (that join is indexed) and carries
        the contributor's own side values inline, but the CONTRIBUTOR GRAPH
        does not walk, so the survivor's own descendants are unreachable.

    Class (b) is NOT a legacy class: consolidation writes NULL contributor
    columns TODAY, by a documented decision, so a store created tomorrow still
    produces class-(b) rows at the consolidation site."""
    validate_contribution_row(row)
    return CLASS_LINKED if row["contributor_ref"] is not None else CLASS_LINKLESS


def _key(row):
    return (row["survivor_type"], row["survivor_id"])


def rows_by_survivor(ledger, user_id: str) -> dict:
    out: dict = {}
    for row in ledger:
        validate_contribution_row(row)
        if row["user_id"] != user_id:
            continue
        out.setdefault(_key(row), []).append(row)
    return out


def survivor_kind(rows) -> str:
    """Read from the SITE, which is a present field — never a re-derived
    judgement about what a record 'looks like'. A survivor carrying rows at
    BOTH sites takes the stricter treatment."""
    return (KIND_SYNTHESIZED
            if any(r["site"] == SITE_CONSOLIDATION for r in rows)
            else KIND_RESTATEMENT)


def survivor_class(rows) -> str:
    """A survivor is class (a) only if EVERY one of its rows walks. One
    linkless row makes its contributor graph incomplete, and an incomplete
    graph reported as complete is the failure this whole section exists to
    prevent."""
    return (CLASS_LINKED if rows and all(row_class(r) == CLASS_LINKED
                                         for r in rows)
            else CLASS_LINKLESS)


def basis(rows, standing, retired=frozenset()) -> str:
    """THE SOLE-BASIS TEST (0022 §4c, resolving research's Q1).

    Surviving independent evidence requires a DIFFERENT RESOLVED IDENTITY.
    Two consequences, both deliberate:

      * same-source self-corroboration does NOT save a record from its own
        source's revocation — a source that restated a claim five times has
        given one source's testimony five times, which is 0012's independence
        condition applied to revocation;
      * an UNIDENTIFIED contributor (NULL digest) is not a different resolved
        identity and cannot corroborate either. Otherwise omitting a source_id
        would immunise content against revocation, which is the adversarial
        cell in reverse.

    The STANDING SET is the whole authority here — the revoked source is in
    it — so the test needs no separate `target` argument, and a LIFT restores
    the lifted source's rows as corroborating evidence by the same rule.

    THE PROPERTY RECURSES (0022 §4c). A contributor that is ITSELF being
    retired by this sweep is not surviving evidence either: independence has
    to hold transitively, or a revoked source launders its testimony one hop
    down and the record one level up reads as corroborated. `retired` is the
    set of (type, id) contributor keys already condemned; the sweep iterates
    to a fixpoint, so a chain of any depth settles."""
    for r in rows:
        d = r["identity_digest"]
        if d is not None and d in standing:
            continue
        if r["contributor_ref"] is not None \
                and (r["contributor_type"], r["contributor_ref"]) in retired:
            continue
        if d is not None:
            return BASIS_CORROBORATED
    return BASIS_SOLE


def dead_rows(rows, standing, retired=frozenset()) -> list:
    """The rows whose evidence this sweep removes: the source stands revoked,
    or the typed contributor is itself condemned."""
    out = []
    for r in rows:
        d = r["identity_digest"]
        if (d is not None and d in standing) or (
                r["contributor_ref"] is not None
                and (r["contributor_type"], r["contributor_ref"]) in retired):
            out.append(r)
    return out


# ---- the recompute ---------------------------------------------------------

def _side(payload, which):
    if not isinstance(payload, dict) or which not in payload:
        raise RevocationError(
            f"absorption payload must carry {which!r} — the shipped "
            f"{{base, contributor}} schema is what makes RECOMPUTE possible "
            f"without a prior_values column")
    side = payload[which]
    if not isinstance(side, dict):
        raise RevocationError(f"payload[{which!r}] must be a dict")
    return side


def _fold(base, sides) -> dict:
    """The SHIPPED absorption inheritance: min(valid_from), max(observed_at),
    max(confidence). Folding over the FULL side set reproduces exactly the
    value the store committed at write — which is what makes the clamp below
    a guard rather than a ratchet."""
    out = {"valid_from": base["valid_from"],
           "observed_at": base["observed_at"],
           "confidence": base["confidence"]}
    for s in sides:
        out["valid_from"] = min(out["valid_from"], s["valid_from"])
        out["observed_at"] = max(out["observed_at"], s["observed_at"])
        out["confidence"] = max(out["confidence"], s["confidence"])
    return out


def recompute(rows, standing, retired=frozenset()) -> dict:
    """RECOMPUTE-NOT-RESTORE, over the SURVIVING evidence only — and a PURE
    FUNCTION OF THE STANDING SET, which is what makes it reversible without a
    `prior_values` column in either direction.

    The transform is the SHIPPED absorption inheritance folded over the
    survivor's own pre-absorption `base` (which every absorption row already
    carries) plus the `contributor` side of every row whose source still
    stands. No new column is needed anywhere: 0012 persists every contributor
    edge and 0014 records every side, so the surviving evidence set is already
    on disk. Lifting a revocation puts the sides back and the SAME fold
    returns the SAME value the store committed at write.

    Restrict-only is enforced TWICE, on purpose. The transform is monotone
    under contributor removal (min/max over a subset of the same sides), and
    the result is then CLAMPED against the FULL-evidence fold, so an
    implementation that someday changes the aggregator still cannot turn a
    revocation into a promotion. The clamp is a no-op under today's transform
    and a guard under tomorrow's — and a vector proves it bites.

    `ungrounded` is absent from the output BY CONSTRUCTION. It is an N-ary OR
    over the contributor set, so re-deriving it over a smaller set can flip it
    True→False — a promotion wearing a recompute's clothes. Once flagged, a
    surviving representation stays flagged."""
    base = None
    all_sides, live_sides = [], []
    for r in rows:
        if r["site"] != SITE_ABSORPTION:
            continue
        b = _side(r["payload"], "base")
        if base is None:
            base = b
        elif b != base:
            raise RevocationError(
                "absorption rows for one survivor disagree about its base "
                "pre-image — the recompute has no floor; refusing")
        side = _side(r["payload"], "contributor")
        all_sides.append(side)
        if r not in dead_rows([r], standing, retired):
            live_sides.append(side)
    if base is None:
        raise RevocationError("recompute requires at least one absorption row")

    full = _fold(base, all_sides)
    out = _fold(base, live_sides)
    # the clamp, against the FULL-evidence fold (= the committed value): never
    # an earlier start, never later currency, never higher confidence
    out["valid_from"] = max(out["valid_from"], full["valid_from"])
    out["observed_at"] = min(out["observed_at"], full["observed_at"])
    out["confidence"] = min(out["confidence"], full["confidence"])
    return out


# ---- the sweep -------------------------------------------------------------

_RECORD_FIELDS = ("type", "id", "origin", "source_id", "active",
                  "retired_reason", "system_authored", "valid_from",
                  "observed_at", "confidence", "ungrounded")


def validate_record(rec) -> dict:
    if not isinstance(rec, dict):
        raise RevocationError(f"record must be a dict — got {rec!r}")
    missing = [f for f in _RECORD_FIELDS if f not in rec]
    if missing:
        raise RevocationError(f"record missing fields: {missing}")
    if rec["type"] not in ("edge", "episode"):
        raise RevocationError(f"record type must be edge|episode — "
                              f"got {rec['type']!r}")
    for f in ("active", "system_authored", "ungrounded"):
        if not isinstance(rec[f], bool):
            raise RevocationError(f"{f} must be a real bool — got {rec[f]!r}")
    rr = rec["retired_reason"]
    if rr is not None and (not isinstance(rr, str) or not rr):
        raise RevocationError(f"retired_reason must be a non-empty str or "
                              f"None — got {rr!r}")
    if rec["active"] and rr is not None:
        raise RevocationError("an active record carries no retired_reason")
    return rec


def sweep(store: dict, target_digest: str, *, proposed=None) -> dict:
    """THE ONE COMPUTATION (0022 §4e, resolving Q3).

    Pure: (store, target, proposed action) → the COMPLETENESS STATEMENT plus
    the effect list. It writes nothing and applies nothing. `revoke_source`
    with `dry_run=True` returns this statement and stops; with `dry_run=False`
    it appends the proposed row and applies `effects`. Both callers run THIS
    function, so a preview cannot disagree with its commit — and 0022 R6
    executes exactly that comparison over a shared store.

    The statement is derived from the STANDING SET, never from an effect log,
    so a lift of one of two overlapping revocations correctly leaves a record
    retired (0022 §4f)."""
    user_id = store["user_id"]
    local = store["local_origin"]
    if not isinstance(target_digest, str) \
            or not _DIGEST_RE.fullmatch(target_digest):
        raise RevocationError(
            f"target must be a 64-hex identity digest — got "
            f"{target_digest!r}; an absent source_id has no digest and no "
            f"revocation reaches it")

    rows = with_proposed(store.get("revocations", ()), user_id, proposed)
    standing = standing_revocations(rows, user_id)
    revoked_now = target_digest in standing

    records = {(r["type"], r["id"]): validate_record(r)
               for r in store["records"]}
    by_survivor = rows_by_survivor(store["ledger"], user_id)

    # (1) DIRECTLY-SOURCED records: their OWN resolved identity is revoked.
    direct = sorted(
        k for k, r in records.items()
        if digest_of(r["origin"], r["source_id"], local) in standing)

    # (2) CONTRIBUTIONS. `affected` is scoped to THE TARGET — it answers "what
    # did this source contribute to", which is what a completeness statement
    # about this source means. `retire`/`recompute` below are the DESIRED
    # STATE under the whole standing set, and `effects` is the DELTA against
    # the store as it is; the three are deliberately different questions and
    # the statement carries all three rather than conflating them.
    affected = sorted(k for k, rws in by_survivor.items()
                      if any(r["identity_digest"] == target_digest
                             for r in rws))

    classes = {k: survivor_class(rws) for k, rws in by_survivor.items()}
    kinds = {k: survivor_kind(rws) for k, rws in by_survivor.items()}

    # (3) THE FIXPOINT. Consumption is TRANSITIVELY CLOSED (a single-level
    # sweep is a defect by accepted rule), and the closure is the RECURSION OF
    # THE PROPERTY rather than a blanket retirement of every descendant: at
    # each pass a condemned contributor stops counting as evidence, which can
    # turn a survivor that read as corroborated into a sole-basis one. The
    # retire set only grows, over a finite survivor set, so this terminates;
    # a self-naming row REFUSED in the validator, so no cycle reaches here.
    retired = set(direct)
    recompute_to: dict = {}
    while True:
        grew = False
        recompute_to = {}
        for key in sorted(by_survivor):
            if key in retired:
                continue
            rws = by_survivor[key]
            if not dead_rows(rws, standing, retired):
                continue                     # nothing this sweep removes
            if kinds[key] == KIND_SYNTHESIZED:
                # The survivor's CONTENT was written over its contributor set,
                # so corroboration by another source does not make the
                # synthesized text safe: the revoked material may be IN it.
                # Retire. Re-deriving from the surviving inputs is a
                # maintenance operation the operator can run — never something
                # a revocation does silently.
                retired.add(key)
                grew = True
            elif basis(rws, standing, retired) == BASIS_SOLE:
                retired.add(key)
                grew = True
            elif any(r["site"] == SITE_ABSORPTION for r in rws):
                recompute_to[key] = recompute(rws, standing, retired)
        if not grew:
            break

    # (3b) THE RESTORING PASS. Desired state is a function of the standing set
    # in BOTH directions, so a lift must put back the maxima the revocation
    # took — by RECOMPUTATION over the restored evidence, never from a stored
    # prior value. The restore is bounded structurally: the target is the fold
    # over the surviving sides, clamped by the FULL-evidence fold, which is
    # exactly the value the store committed at write, so nothing can be raised
    # past it. It is planned only when every field moves in the restoring
    # direction, so this pass can never manufacture a promotion out of a
    # difference some other mechanism introduced.
    for key in sorted(by_survivor):
        if key in retired or key in recompute_to or key not in records:
            continue
        rws = by_survivor[key]
        if not any(r["site"] == SITE_ABSORPTION for r in rws):
            continue
        want = recompute(rws, standing, retired)
        cur = records[key]
        if all(want[f] == cur[f] for f in RECOMPUTED_FIELDS):
            continue
        if (want["confidence"] >= cur["confidence"]
                and want["observed_at"] >= cur["observed_at"]
                and want["valid_from"] <= cur["valid_from"]):
            recompute_to[key] = want

    retire = sorted(retired)
    reach = sorted(k for k in retired
                   if k not in set(direct) and k not in set(affected))
    walkable = not any(
        row_class(r) == CLASS_LINKLESS
        for k in set(affected) | retired
        for r in by_survivor.get(k, ()))

    # (4) CLASS (c): system-authored records with NO attribution rows at all.
    # An UPPER BOUND on the unreachable population, and deliberately so: the
    # correct direction of error for a blind-spot count is over-reporting.
    unattributed = sorted(k for k, r in records.items()
                          if r["system_authored"] and k not in by_survivor)

    # (5) THE EFFECTS ARE A DIFF AGAINST THE DESIRED STATE, in ONE direction-
    # free construction: a record's desired state is a function of the
    # STANDING set alone, so revoke and lift are the same computation and an
    # overlapping revocation holds a record retired until the last lift.
    retire_set = set(retire)
    effects = []
    for key in sorted(records):
        r = records[key]
        want_active = key not in retire_set
        if r["active"] and not want_active:
            effects.append({"verb": "retire", "type": key[0], "id": key[1],
                            "reason": RETIREMENT_REASON})
        elif want_active and not r["active"] \
                and r["retired_reason"] == RETIREMENT_REASON:
            # Only OUR OWN retirements reverse. A record retired as superseded
            # or lapsed is not this operation's to reinstate.
            effects.append({"verb": "reinstate", "type": key[0], "id": key[1],
                            "via": "supersession"})
        values = recompute_to.get(key)
        if values and any(values[f] != r[f] for f in RECOMPUTED_FIELDS):
            effects.append({"verb": "recompute", "type": key[0], "id": key[1],
                            "values": values})
    effects.sort(key=lambda e: (e["verb"], e["type"], e["id"]))
    for e in effects:
        assert e["verb"] in EFFECT_VERBS, e            # the closed vocabulary

    complete = walkable and not unattributed
    return {
        "target": target_digest,
        "standing": revoked_now,
        "direct": direct,
        "affected": affected,
        "classes": {f"{t}:{i}": classes[(t, i)] for t, i in affected},
        "kinds": {f"{t}:{i}": kinds[(t, i)] for t, i in affected},
        "retire": retire,
        "recompute": sorted(recompute_to),
        "descendants": reach,
        "counts": {
            CLASS_LINKED: sum(1 for k in affected
                              if classes[k] == CLASS_LINKED),
            CLASS_LINKLESS: sum(1 for k in affected
                                if classes[k] == CLASS_LINKLESS),
            CLASS_UNATTRIBUTED: len(unattributed),
        },
        "graph_walkable": walkable,
        "complete": complete,
        "effects": effects,
    }


# ---- applying effects: supersede-never-erase, provably --------------------

def apply_effects(store: dict, statement: dict) -> dict:
    """Return a NEW store. Never mutates the input, never removes a record,
    and appends every superseded value to `history`.

    This is the executable form of C3: the reversal of a retirement is a new
    superseding event, never an edit and never an undelete. 0022 R9 asserts
    that the input store is byte-identical afterwards and that `history` only
    grows."""
    records = {(r["type"], r["id"]): dict(r) for r in store["records"]}
    history = list(store.get("history", ()))
    for e in statement["effects"]:
        key = (e["type"], e["id"])
        if key not in records:
            raise RevocationError(f"effect names an absent record: {key}")
        before = dict(records[key])
        after = dict(before)
        if e["verb"] == "retire":
            after["active"] = False
            after["retired_reason"] = e["reason"]
        elif e["verb"] == "reinstate":
            after["active"] = True
            after.pop("retired_reason", None)
        elif e["verb"] == "recompute":
            for f in RECOMPUTED_FIELDS:
                after[f] = e["values"][f]
        else:                                    # unreachable: closed above
            raise RevocationError(f"unknown effect verb {e['verb']!r}")
        history.append({"superseded": before, "by": e["verb"]})
        records[key] = after
    out = dict(store)
    out["records"] = [records[(r["type"], r["id"])] for r in store["records"]]
    out["history"] = history
    if statement["standing"] and statement.get("row"):
        out["revocations"] = list(store.get("revocations", ())) \
            + [statement["row"]]
    return out
