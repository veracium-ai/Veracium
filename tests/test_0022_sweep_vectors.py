"""specs/0022 — the DIFFERENTIAL vector corpus: product vs reference.

Every sweep-bearing vector in the acceptance corpus is materialised into a
REAL SqliteStore, driven through the product surface (`revoke_source`), and
its statement compared FIELD-FOR-FIELD against the normative reference run on
the vector's own dict-store. Commit-path vectors additionally compare the
POST-STATE record-by-record against the reference's `apply_effects`.

This is what makes the verbatim port's adapter honest: the pure core is the
same code by construction, so any disagreement here is a projection or
effect-application defect — exactly the seam where the fidelity risk lives.
"""

import copy
import json
import pathlib
import sys
import uuid
from datetime import datetime

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs" / "evidence" / "0022"))

import vector_harness as VH                                   # noqa: E402
from reference_revocation import (RevocationError as RefError,  # noqa: E402
                                  apply_effects as ref_apply,
                                  sweep as ref_sweep)

from veracium import EvidenceAuthor, SqliteStore              # noqa: E402
from veracium.schema import Edge, Episode, Provenance          # noqa: E402
from veracium.store import revocation as rv                    # noqa: E402
from veracium.store import revocation_sweep as psw             # noqa: E402

_VECTORS = json.loads(
    (ROOT / "specs" / "evidence" / "0022" / "vectors.json").read_text())
_SWEEPS = [v for v in _VECTORS if "store" in v]


def _dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _materialise(tmp_path, store_dict):
    """A REAL SqliteStore holding exactly the vector's store."""
    s = SqliteStore(str(tmp_path / f"v-{uuid.uuid4().hex[:8]}.db"))
    uid = store_dict["user_id"]
    s._conn.execute("UPDATE store_identity SET origin=?",
                    (store_dict["local_origin"],))
    for r in store_dict["records"]:
        prov = Provenance(
            author_of_evidence=(EvidenceAuthor.SYSTEM if r["system_authored"]
                                else EvidenceAuthor.USER),
            evidence_ref=f"ev-{r['id']}",
            source_id=r["source_id"], origin=r["origin"],
            observed_at=_dt(r["observed_at"]),
            confidence=r["confidence"])
        if r["type"] == "edge":
            e = Edge(id=r["id"], user_id=uid, subject="user",
                     relation="related_to", object=r["id"],
                     provenance=prov, valid_from=_dt(r["valid_from"]),
                     ungrounded=r["ungrounded"])
            if not r["active"]:
                e.invalidated_at = _dt(r["observed_at"])
                e.invalidation_reason = r["retired_reason"]
            s._conn.execute(
                "INSERT INTO edges(id, user_id, subject, relation, active,"
                " quarantined, json) VALUES(?,?,?,?,?,0,?)",
                (e.id, uid, e.subject, e.relation, int(r["active"]),
                 e.model_dump_json()))
        else:
            ep = Episode(id=r["id"], user_id=uid,
                         date=r["valid_from"][:10], summary=f"s-{r['id']}",
                         provenance=prov,
                         retired_reason=r["retired_reason"],
                         retired_at=(None if r["active"]
                                     else _dt(r["observed_at"])))
            s._conn.execute(
                "INSERT INTO episodes(id, user_id, date, json) "
                "VALUES(?,?,?,?)", (ep.id, uid, ep.date, ep.model_dump_json()))
    for row in store_dict["ledger"]:
        s._conn.execute(
            "INSERT INTO contribution_ledger(id, user_id, survivor_type,"
            " survivor_id, site, identity_digest, evidence_ref_digest,"
            " payload, op_key, contributor_type, contributor_ref, created_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"c-{uuid.uuid4().hex[:10]}", row["user_id"],
             row["survivor_type"], row["survivor_id"], row["site"],
             row["identity_digest"], row["evidence_ref_digest"],
             json.dumps(row["payload"]), row["op_key"],
             row["contributor_type"], row["contributor_ref"],
             "2026-08-01T00:00:00+00:00"))
    for row in store_dict["revocations"]:
        s._conn.execute(
            "INSERT INTO source_revocations(user_id, seq, identity_digest,"
            " action, at, reason) VALUES(?,?,?,?,?,?)",
            (row["user_id"], row["seq"], row["identity_digest"],
             row["action"], row["at"], row["reason"]))
    s._conn.commit()
    return s


def _canon(stmt):
    """Field-for-field comparable form (tuple keys vs list keys unified)."""
    out = copy.deepcopy(stmt)
    for f in ("direct", "affected", "retire", "recompute", "descendants"):
        out[f] = [list(k) for k in out[f]]
    return out


@pytest.mark.parametrize(
    "v", _SWEEPS, ids=[v["name"] for v in _SWEEPS])
def test_product_agrees_with_the_reference(v, tmp_path):
    store_dict = VH._sub(copy.deepcopy(v["store"]))
    target = VH.D(v["target"])
    proposed = VH._sub(copy.deepcopy(v.get("proposed")))

    if VH._is_error(v.get("expect")):
        # the ERROR half (the harness's OWN membership check — a blanket
        # "any string" test misrouted 'append-only' and 'identical', which is
        # the exact mistake _is_error's docstring warns about)
        with pytest.raises(RefError):
            ref_sweep(copy.deepcopy(store_dict), target, proposed=proposed)
        import sqlite3
        try:
            s = _materialise(tmp_path, store_dict)
        except sqlite3.IntegrityError:
            # the duplicate-record-key vector: the reference refuses in the
            # sweep; the PRODUCT refuses one layer LOWER, at the primary key —
            # the same property ("refuse instead of last-one-wins"), enforced
            # by the store's own shape before a sweep could ever see it
            assert "duplicate_record_keys" in v["name"]
            return
        with pytest.raises(psw.RevocationError):
            if proposed is not None:
                rv.revoke_source(s, store_dict["user_id"], target,
                                 proposed["action"], proposed["reason"],
                                 proposed["at"], dry_run=True)
            else:
                psw.sweep(rv.project_store(s, store_dict["user_id"]), target)
        return

    ref_stmt = ref_sweep(copy.deepcopy(store_dict), target, proposed=proposed)

    # (1) THE STATEMENT, through the product surface
    s = _materialise(tmp_path, store_dict)
    uid = store_dict["user_id"]
    if proposed is not None:
        got = rv.revoke_source(s, uid, target, proposed["action"],
                               proposed["reason"], proposed["at"],
                               dry_run=True)
    else:
        got = psw.sweep(rv.project_store(s, uid), target)
    assert _canon(got) == _canon(ref_stmt), v["name"]

    # (2) THE POST-STATE, when there is a commit to make
    if proposed is None:
        return
    committed = rv.revoke_source(s, uid, target, proposed["action"],
                                 proposed["reason"], proposed["at"])
    assert _canon(committed) == _canon(ref_stmt), (
        f"{v['name']}: preview and commit statements diverge at the product "
        f"surface — the one-computation rule")
    ref_after = ref_apply(copy.deepcopy(store_dict), ref_stmt)
    product_after = {(r["type"], r["id"]): r
                     for r in rv.project_store(s, uid)["records"]}
    for r in ref_after["records"]:
        key = (r["type"], r["id"])
        p = product_after[key]
        for f in ("active", "retired_reason", "valid_from", "observed_at",
                  "confidence"):
            # reference reinstate POPs retired_reason; absent means None
            assert p.get(f) == r.get(f), (
                f"{v['name']}: {key} field {f!r}: product {p.get(f)!r} != "
                f"reference {r.get(f)!r}")
