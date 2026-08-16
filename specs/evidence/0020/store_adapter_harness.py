"""specs/0020 — the REAL-STORE adapter harness (v9 — external round 7
rebuilt the import half). Exercises the SHIPPED store — actual absorption
through `apply_supersession`, actual `SqliteStore.contributions()` rows,
actual `export_memory` files — projects the real rows into the normative
resolver's input shape, and asserts the expected memberships.

EXECUTION-MODE LABELS (the round-7 archive ask — COLLECTED must not
overstate): every check line is prefixed with its mode —
  [import-path]  the check DROVE the real export file / real import
                 machinery through the spec's pre-commit order;
  [store]        the check drove real store mutations (apply_supersession,
                 contributions, reopen) with no import involved;
  [helper]       the check called a normative helper on synthetic input
                 (used ONLY where the input is deliberately corrupt in a
                 way real machinery refuses to produce);
  [impl-gated]   stated obligations that need the 0021 implementation
                 (the amended 0009 primitive) — recorded, NOT executed.

Regression groups:
(1) [store] the round-3 single-hop leak (cross-identity absorption →
    UNRESOLVED from real ledger rows); same-identity → own digest.
(2) [store] THE ROUND-7 THREE-HOP CHAIN, NATIVE: A(scope-a) absorbed by
    B(scope-b) absorbed by C(scope-b) via real apply_supersession. The
    single-level read over C's direct rows returns C's OWN digest — the
    demonstrated leak — and the normative CLOSURE returns UNRESOLVED.
    Links are derived from the REAL records via the decidable linkage
    rule. Same-identity chain → own digest (the contrast cell).
(3) [import-path] the restored three-hop: real export → PRE-COMMIT
    transitive reconstruction (minted op key) → the destination survivor
    is UNRESOLVED via born-closed rows; under user_id remap; stable
    across close/reopen; re-running reconstruction is idempotent.
(4) [import-path] the PRE-COMMIT GATE (`scoped_import`, the spec's
    normative order around the shipped importer): a REAL native export
    whose winner id embeds the note framing RESOLVES (v8's regex refused
    it — the round-7 headline); a REAL pre-existing `absorbed_by:ghost`
    note followed by the genuine appended tag RESOLVES (last tag
    governs); a genuinely AMBIGUOUS id universe REFUSES before any
    write; [helper] hand-corrupted files (missing tag / unresolvable
    tag) REFUSE before any write — and after every refusal the
    destination's logical state is asserted UNCHANGED.
(5) [store] host records with no rows: own digest / SHARED floor.
(6) [impl-gated] ledger-row rollback on mid-plan failure, concurrent
    same-file imports, durable `imported-absorption` rows after reopen,
    consolidation-output and recovery-state cases — the amended 0009
    primitive's obligations (0021 §7b exact text; W15), stated so the
    gap is a statement, not an omission.

Run: `<venv>/python specs/evidence/0020/store_adapter_harness.py`
(builds temp stores; ~2s; the seal runs it and records the result in
`store_adapter_result.txt`).
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from veracium.graph import DEFAULT_RELATIONS, apply_supersession  # noqa: E402
from veracium.schema import Edge, EvidenceAuthor, Provenance  # noqa: E402
from veracium import portability  # noqa: E402
from veracium.store.sqlite import SqliteStore  # noqa: E402
from reference_scope import (SHARED, UNRESOLVED, digest_of, Identity,  # noqa: E402
                             ImportLinkageError, close_absorption_rows,
                             membership, reconstruct_absorption_rows)

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _mint_op():
    return f"op-{uuid.uuid4().hex[:12]}"


def _edge(obj, *, eid, sid, conf=0.9, observed=NOW, note="", rel="pet"):
    return Edge(id=eid, user_id="u1", subject="user", relation=rel,
                object=obj, valid_from=observed, note=note,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{eid}",
                                      source_id=sid,
                                      observed_at=observed, confidence=conf))


def _project(store, user_id, survivor_type, survivor_id):
    """REAL `ContributionRecord`s → the resolver's row shape."""
    return [{"site": r.site, "identity_digest": r.identity_digest,
             "op_key": r.op_key}
            for r in store.contributions(user_id, survivor_type, survivor_id)]


def _record_shape(edge):
    return {"author": edge.provenance.author_of_evidence.value,
            "origin": edge.provenance.origin,
            "source_id": edge.provenance.source_id,
            "evidence_ref": edge.provenance.evidence_ref,
            "lineage": False}


def _links_from_real_records(store, user_id):
    """Derive absorbed-prior links AND digests from the REAL records via
    the decidable linkage rule (the same candidate matching the import
    path uses). READ-SIDE assembly is TOLERANT (unlike the import gate): a
    record whose winner cannot resolve contributes NO link — the closure
    then fails closed on the unaccounted row rather than crashing the
    read (R8-1: this is exactly the post-prune shape)."""
    from reference_scope import _resolve_winner
    recs = [{"id": e.id, "invalidation_reason": e.invalidation_reason,
             "note": e.note, "origin": e.provenance.origin,
             "source_id": e.provenance.source_id}
            for e in store.edges(user_id, active_only=False)]
    ids = {r["id"] for r in recs}
    links: dict = {}
    digests: dict = {}
    for r in recs:
        digests[r["id"]] = digest_of(
            Identity(r["origin"], r["source_id"]), store.local_origin())
        if r["invalidation_reason"] == "absorbed_duplicate":
            try:
                links.setdefault(_resolve_winner(r, ids), []).append(r["id"])
            except ImportLinkageError:
                pass                       # unresolvable — no link; closure
                                           # fails closed downstream
    return {k: tuple(v) for k, v in links.items()}, digests


def _parse_export(path):
    out = []
    for line in pathlib.Path(path).read_text().splitlines():
        d = json.loads(line)
        if d.get("record") != "edge":
            continue
        prov = d.get("provenance") or {}
        out.append({"id": d.get("id"),
                    "invalidation_reason": d.get("invalidation_reason"),
                    "note": d.get("note"),
                    "origin": prov.get("origin"),
                    "source_id": prov.get("source_id"),
                    "evidence_ref": prov.get("evidence_ref"),
                    "object": d.get("object"),
                    "absorbed_by_id": d.get("absorbed_by_id")})
    return out


def _logical_state(store, user_id):
    """The destination-unchanged fingerprint: the full logical edge state
    plus the (always-empty-until-implemented) contribution projection."""
    return sorted((e.id, e.object, e.invalidation_reason or "", e.note or "")
                  for e in store.edges(user_id, active_only=False,
                                       include_quarantined=True))


def scoped_import(dest_store, export_path, *, user_id=None):
    """The spec's NORMATIVE pre-commit order (0020 §4a-iii v9 / R7-2):
    parse the export FILE → reconstruct linkage (refusal raises HERE,
    before any destination write) → only then hand the file to the
    shipped importer. Returns (import_counts, reconstructed_rows keyed by
    post-remap id). The shipped `import_memory` adding these rows through
    the amended 0009 primitive is the implementation obligation."""
    records = _parse_export(export_path)
    op = _mint_op()
    local = dest_store.local_origin()
    rebuilt_old = reconstruct_absorption_rows(records, local, import_op=op)
    counts = portability.import_memory(dest_store, export_path,
                                       user_id=user_id,
                                       restore=(user_id is None))
    if user_id is None:
        return counts, rebuilt_old
    # the shipped importer remints ids under a user remap without touching
    # notes; rebuild THROUGH the id table derived from the committed store
    # (content-matched here; the importer's own table is the impl carrier)
    imported = [{"id": e.id, "object": e.object}
                for e in dest_store.edges(user_id, active_only=False)]
    by_obj = {e["object"]: e["id"] for e in imported}
    old_by_obj = {r["object"]: r["id"] for r in records}
    remap = {old: by_obj.get(obj) for obj, old in old_by_obj.items()}
    rebuilt = reconstruct_absorption_rows(records, local, id_remap=remap,
                                          import_op=op)
    return counts, rebuilt


def run():
    checks = []
    with tempfile.TemporaryDirectory() as d:
        store = SqliteStore(f"{d}/s.db")
        local = store.local_origin()

        # ---- (1) [store] the round-3 single-hop cells ------------------
        prior_b = _edge("Miso", eid="e-b", sid="agent-b", conf=0.99)
        apply_supersession(store, prior_b, DEFAULT_RELATIONS)
        incoming_a = _edge("cat Miso", eid="e-a", sid="agent-a", conf=0.10,
                           observed=NOW - timedelta(days=30))
        apply_supersession(store, incoming_a, DEFAULT_RELATIONS)
        rows = _project(store, "u1", "edge", "e-a")
        assert rows, "no real ledger rows written for the absorption"
        surv = [e for e in store.edges("u1", active_only=True)
                if e.id == "e-a"][0]
        got = membership(_record_shape(surv), rows, "none", local)
        assert got == UNRESOLVED, f"cross-identity absorption: {got!r}"
        checks.append("[store] single-hop cross-identity absorption -> "
                      f"UNRESOLVED ({len(rows)} real ledger row(s))")
        p2 = _edge("Rex", eid="e-p2", sid="agent-c", conf=0.5, rel="dog")
        apply_supersession(store, p2, DEFAULT_RELATIONS)
        w2 = _edge("dog Rex", eid="e-w2", sid="agent-c", conf=0.9, rel="dog")
        apply_supersession(store, w2, DEFAULT_RELATIONS)
        surv2 = [e for e in store.edges("u1", active_only=True)
                 if e.id == "e-w2"][0]
        got2 = membership(_record_shape(surv2),
                          _project(store, "u1", "edge", "e-w2"),
                          "none", local)
        assert got2 == digest_of(Identity(None, "agent-c"), local), \
            f"same-identity absorption: {got2!r}"
        checks.append("[store] same-identity absorption -> own digest")
        store.close()

        # ---- (2) [store] THE ROUND-7 THREE-HOP CHAIN, NATIVE -----------
        chain = SqliteStore(f"{d}/chain.db")
        clocal = chain.local_origin()
        e1 = _edge("Miso", eid="c-1", sid="agent-a", conf=0.2)
        apply_supersession(chain, e1, DEFAULT_RELATIONS)
        e2 = _edge("cat Miso", eid="c-2", sid="agent-b", conf=0.5)
        apply_supersession(chain, e2, DEFAULT_RELATIONS)      # B absorbs A
        e3 = _edge("small cat Miso", eid="c-3", sid="agent-b", conf=0.9)
        apply_supersession(chain, e3, DEFAULT_RELATIONS)      # C absorbs B
        direct3 = _project(chain, "u1", "edge", "c-3")
        assert direct3, "no rows on the chain survivor"
        surv3 = [e for e in chain.edges("u1", active_only=True)
                 if e.id == "c-3"][0]
        # the DEMONSTRATED leak: single-level read = own scope
        leak = membership(_record_shape(surv3), direct3, "none", clocal)
        own3 = digest_of(Identity(None, "agent-b"), clocal)
        assert leak == own3, (
            f"expected the single-level read to demonstrate the R7-1 leak "
            f"(own digest), got {leak!r}")
        # the NORMATIVE closure: UNRESOLVED (A's foreign digest, one hop down)
        links, digests = _links_from_real_records(chain, "u1")
        direct_rows = {e.id: _project(chain, "u1", "edge", e.id)
                       for e in chain.edges("u1", active_only=False)}
        closed = close_absorption_rows("c-3", direct_rows, links, digests)
        assert closed is not None, "closure unwalkable on a complete store"
        got3 = membership(_record_shape(surv3), closed, "none", clocal)
        assert got3 == UNRESOLVED, f"three-hop native closure: {got3!r}"
        checks.append("[store] THREE-HOP native chain: single-level read "
                      "reproduces the R7-1 leak; the CLOSURE -> UNRESOLVED "
                      f"({len(closed)} closed row(s), links from real "
                      "records via the decidable rule)")
        # the contrast: an all-same-identity chain closes to own digest
        s1 = _edge("Rex", eid="s-1", sid="agent-z", conf=0.2, rel="dog")
        apply_supersession(chain, s1, DEFAULT_RELATIONS)
        s2 = _edge("dog Rex", eid="s-2", sid="agent-z", conf=0.5, rel="dog")
        apply_supersession(chain, s2, DEFAULT_RELATIONS)
        s3 = _edge("small dog Rex", eid="s-3", sid="agent-z", conf=0.9,
                   rel="dog")
        apply_supersession(chain, s3, DEFAULT_RELATIONS)
        linksz, digz = _links_from_real_records(chain, "u1")
        drz = {e.id: _project(chain, "u1", "edge", e.id)
               for e in chain.edges("u1", active_only=False)}
        closedz = close_absorption_rows("s-3", drz, linksz, digz)
        sv3 = [e for e in chain.edges("u1", active_only=True)
               if e.id == "s-3"][0]
        gz = membership(_record_shape(sv3), closedz, "none", clocal)
        assert gz == digest_of(Identity(None, "agent-z"), clocal), repr(gz)
        checks.append("[store] three-hop SAME-identity chain closes to own "
                      "digest (the contrast cell)")

        # ---- (2b) [store] THE ROUND-8 PRUNE REGRESSION (R8-1) ----------
        # No shipped path physically prunes an absorbed edge (mechanically
        # asserted in 0021 §2c-ii: expiry invalidates, consolidation
        # deletes EPISODES, erasure removes whole users) — so the prune is
        # SIMULATED by direct SQL, labeled, standing in for the future
        # retention capability the spec's retention contract governs.
        # v9's harness deleted B's ROWS but kept its LINK — the reviewer
        # called that artificial; THIS deletes the RECORD, which takes the
        # note-link with it, exactly the executed break.
        chain.close()                    # settle the file, then fork a copy
        import shutil
        shutil.copyfile(f"{d}/chain.db", f"{d}/chain-pruned.db")
        chain = SqliteStore(f"{d}/chain.db")        # groups (3)+ keep the
        pruned = SqliteStore(f"{d}/chain-pruned.db")  # unpruned original
        pruned._conn.execute("DELETE FROM edges WHERE id='c-2'")
        pruned._conn.commit()
        pruned.close()
        re_chain = SqliteStore(f"{d}/chain-pruned.db")  # close/reopen, real
        rl = re_chain.local_origin()
        linksp, digp = _links_from_real_records(re_chain, "u1")
        drp = {e.id: _project(re_chain, "u1", "edge", e.id)
               for e in re_chain.edges("u1", active_only=False)}
        # B's ledger rows happen to survive HERE because the raw SQL prune
        # bypassed A10's row-drop (the API-level prune would drop them —
        # accepted 0014 _drop_contributions_for_survivor); include them so
        # the closure sees the WORST honest case: rows present, link gone
        drp["c-2"] = _project(re_chain, "u1", "edge", "c-2")
        surv_p = [e for e in re_chain.edges("u1", active_only=True)
                  if e.id == "c-3"][0]
        closed_p = close_absorption_rows("c-3", drp, linksp, digp)
        got_p = (UNRESOLVED if closed_p is None
                 else membership(_record_shape(surv_p), closed_p, "none", rl))
        assert closed_p is None and got_p == UNRESOLVED, (
            f"pruned legacy chain must close to None -> UNRESOLVED, got "
            f"closure={'set' if closed_p is not None else 'None'}, "
            f"{got_p!r}")
        checks.append("[store] R8-1 PRUNE regression: B's RECORD physically "
                      "deleted (simulated retention; no shipped API — "
                      "reach-asserted), close/REOPEN, links re-derived from "
                      "what survives -> the survivor's row is unattributed "
                      "with no link -> closure None -> UNRESOLVED (v9 read "
                      "this cell own-scope; typed contributor_ref rows are "
                      "the durable fix, proven in ledger_plan_harness)")
        re_chain.close()

        # ---- (3) [import-path] the RESTORED three-hop ------------------
        exp = pathlib.Path(d) / "chain.jsonl"
        portability.export_memory(chain, "u1", exp)
        dest = SqliteStore(f"{d}/dest.db")
        _counts, rebuilt = scoped_import(dest, exp)
        assert _project(dest, "u1", "edge", "c-3") == [], \
            "the ledger travelled?! (0014 locality broken)"
        r3 = rebuilt.get("c-3", [])
        digs3 = {r["identity_digest"] for r in r3}
        assert digest_of(Identity(clocal, "agent-a"), dest.local_origin()) \
            in digs3 and len(r3) >= 2, (
            f"transitive reconstruction missed the ancestor: {r3!r}")
        assert all(r["op_key"]
                   and r["site"] in ("imported-absorption",
                                     "scope-attribution")
                   and r["contributor_ref"] and r["evidence_ref_digest"]
                   for r in r3), "rows not fully populated (R7-3/R8-3: " \
            "per-row key, typed contributor binding, evidence digest)"
        assert any(r["site"] == "scope-attribution" for r in r3), \
            "the transitive copy should land at the derived-row site (R10-1)"
        dsurv = [e for e in dest.edges("u1", active_only=False)
                 if e.id == "c-3"][0]
        dgot = membership(_record_shape(dsurv), r3, "none",
                          dest.local_origin())
        assert dgot == UNRESOLVED, f"restored three-hop: {dgot!r}"
        checks.append("[import-path] RESTORED three-hop: pre-commit "
                      "transitive reconstruction (minted op key) -> the "
                      "destination survivor UNRESOLVED via born-closed "
                      f"rows ({len(r3)} row(s) incl. the ancestor digest)")
        # idempotent re-run of reconstruction over the same file
        again = reconstruct_absorption_rows(
            _parse_export(exp), dest.local_origin(), import_op="op-aaaaaaaaaaaa")
        assert {k: sorted((r["identity_digest"] or "") for r in v)
                for k, v in again.items()} == \
               {k: sorted((r["identity_digest"] or "") for r in v)
                for k, v in rebuilt.items()}
        checks.append("[import-path] reconstruction is deterministic across "
                      "re-runs (idempotent re-import's precondition)")
        dest.close()
        # reopen: records + reconstruction stable
        re_dest = SqliteStore(f"{d}/dest.db")
        r3r = reconstruct_absorption_rows(
            _parse_export(exp), re_dest.local_origin(),
            import_op="op-bbbbbbbbbbbb").get("c-3", [])
        rsurv = [e for e in re_dest.edges("u1", active_only=False)
                 if e.id == "c-3"][0]
        assert membership(_record_shape(rsurv), r3r, "none",
                          re_dest.local_origin()) == UNRESOLVED
        checks.append("[import-path] after CLOSE/REOPEN the restored "
                      "three-hop survivor is still UNRESOLVED")
        re_dest.close()
        # under user_id remap
        dest2 = SqliteStore(f"{d}/dest2.db")
        _c2, rebuilt2 = scoped_import(dest2, exp, user_id="u2")
        new_surv = {e.object: e.id
                    for e in dest2.edges("u2", active_only=False)}[
                        "small cat Miso"]
        rr = rebuilt2.get(new_surv, [])
        assert rr and len(rr) >= 2, f"remap lost the transitive rows: {rr!r}"
        checks.append("[import-path] REMAPPED import keys the transitive "
                      f"rows to post-remap ids ({new_surv})")
        dest2.close()
        chain.close()

        # ---- (4) [import-path] the PRE-COMMIT GATE ---------------------
        # (4a) a REAL export whose winner id embeds the framing — v8's
        # regex refused this valid file; the decidable rule resolves it
        punct = SqliteStore(f"{d}/punct.db")
        pw = _edge("Miso", eid="loser-p", sid="agent-a", conf=0.2)
        apply_supersession(punct, pw, DEFAULT_RELATIONS)
        pv = _edge("cat Miso", eid="winner (restated as x", sid="agent-b",
                   conf=0.9)
        apply_supersession(punct, pv, DEFAULT_RELATIONS)
        exp_p = pathlib.Path(d) / "punct.jsonl"
        portability.export_memory(punct, "u1", exp_p)
        punct.close()
        dp = SqliteStore(f"{d}/dp.db")
        _cp, rb_p = scoped_import(dp, exp_p)
        assert rb_p.get("winner (restated as x"), \
            "the punctuation-id native export failed to reconstruct (R7-2)"
        checks.append("[import-path] REAL export with a framing-embedded "
                      "winner id RESOLVES via the decidable rule (v8's "
                      "regex refused this valid file)")
        dp.close()
        # (4b) a REAL pre-existing absorbed_by:ghost note + the genuine
        # appended tag — the LAST tag governs
        ghost = SqliteStore(f"{d}/ghost.db")
        gp = _edge("Rex", eid="loser-g", sid="agent-a", conf=0.2, rel="dog",
                   note="user pasted: absorbed_by:ghost")
        apply_supersession(ghost, gp, DEFAULT_RELATIONS)
        gv = _edge("dog Rex", eid="winner-g", sid="agent-b", conf=0.9,
                   rel="dog")
        apply_supersession(ghost, gv, DEFAULT_RELATIONS)
        exp_g = pathlib.Path(d) / "ghost.jsonl"
        portability.export_memory(ghost, "u1", exp_g)
        ghost.close()
        dg = SqliteStore(f"{d}/dg.db")
        _cg, rb_g = scoped_import(dg, exp_g)
        assert rb_g.get("winner-g"), \
            "the incidental-ghost note broke resolution (last tag governs)"
        checks.append("[import-path] REAL pre-existing 'absorbed_by:ghost' "
                      "note + the genuine appended tag RESOLVES — the LAST "
                      "tag governs and is the only one that must (v8 "
                      "demanded the ghost resolve too)")
        dg.close()
        # (4c) refusal cases — each drives scoped_import on a FILE and
        # asserts the destination's logical state UNCHANGED
        ref_cases = []
        # genuinely ambiguous id universe (both "winner" and the framing-
        # embedded id exist): REAL store construction
        amb = SqliteStore(f"{d}/amb.db")
        a0 = _edge("plain", eid="winner", sid="agent-c", conf=0.9,
                   rel="bird")
        amb.add_edge(a0)
        ap = _edge("Miso", eid="loser-a", sid="agent-a", conf=0.2)
        apply_supersession(amb, ap, DEFAULT_RELATIONS)
        av = _edge("cat Miso", eid="winner (restated as x", sid="agent-b",
                   conf=0.9)
        apply_supersession(amb, av, DEFAULT_RELATIONS)
        exp_a = pathlib.Path(d) / "amb.jsonl"
        portability.export_memory(amb, "u1", exp_a)
        amb.close()
        ref_cases.append(("[import-path] AMBIGUOUS id universe (real "
                          "store: 'winner' + the framing-embedded id)",
                          exp_a))
        # hand-corrupted files (real machinery refuses to produce these —
        # [helper]-authored FILES, still driven through the import path)
        def _corrupt(name, note):
            p = pathlib.Path(d) / name
            with p.open("w") as f:
                f.write(json.dumps({"kind": "veracium-export", "version": 6,
                                    "user_id": "u1"}) + "\n")
                f.write(json.dumps(
                    {"record": "edge", "id": "w1", "user_id": "u1",
                     "subject": "user", "relation": "pet", "object": "x",
                     "valid_from": NOW.isoformat(), "note": None,
                     "invalidation_reason": None,
                     "provenance": {"author_of_evidence": "user",
                                    "evidence_ref": "ev-1",
                                    "source_id": "agent-1",
                                    "origin": "org-x",
                                    "observed_at": NOW.isoformat(),
                                    "confidence": 0.9}}) + "\n")
                f.write(json.dumps(
                    {"record": "edge", "id": "l1", "user_id": "u1",
                     "subject": "user", "relation": "pet", "object": "y",
                     "valid_from": NOW.isoformat(), "note": note,
                     "invalidation_reason": "absorbed_duplicate",
                     "provenance": {"author_of_evidence": "user",
                                    "evidence_ref": "ev-2",
                                    "source_id": "agent-2",
                                    "origin": "org-x",
                                    "observed_at": NOW.isoformat(),
                                    "confidence": 0.5}}) + "\n")
            return p
        ref_cases.append(("[helper-file/import-path] MISSING tag",
                          _corrupt("missing.jsonl", "retired")))
        ref_cases.append(("[helper-file/import-path] UNRESOLVABLE tag",
                          _corrupt("unres.jsonl", "absorbed_by:ghost-id")))
        for label, path in ref_cases:
            dref = SqliteStore(f"{d}/ref-{path.stem}.db")
            pre = _edge("sentinel", eid="pre-existing", sid="agent-s",
                        rel="fish")
            dref.add_edge(pre)
            before = _logical_state(dref, "u1")
            try:
                scoped_import(dref, path)
                raise AssertionError(f"{label} did not refuse")
            except ImportLinkageError:
                pass
            after = _logical_state(dref, "u1")
            assert before == after, f"{label}: destination state CHANGED"
            assert _project(dref, "u1", "edge", "pre-existing") == []
            dref.close()
            checks.append(f"{label} -> PRE-COMMIT whole-import refusal; "
                          "destination logical state byte-for-byte "
                          "unchanged (pre-populated sentinel intact)")

        # ---- (5) [store] host records, no rows -------------------------
        floor = SqliteStore(f"{d}/floor.db")
        flocal = floor.local_origin()
        h = _edge("Tortoise", eid="e-h", sid="agent-z", rel="tortoise")
        floor.add_edge(h)
        assert membership(_record_shape(h), [], "none", flocal) == \
            digest_of(Identity(None, "agent-z"), flocal)
        nid = _edge("Sparrow", eid="e-n", sid=None, rel="bird2")
        nid2 = nid.model_copy(update={"provenance": nid.provenance.model_copy(
            update={"source_id": None})})
        assert membership(_record_shape(nid2), [], "none", flocal) == SHARED
        floor.close()
        checks.append("[store] host records: own digest / SHARED floor")

        # ---- (6) [impl-gated] the amended-primitive obligations --------
        checks.append("[impl-gated] ledger-row ROLLBACK on mid-plan "
                      "failure, CONCURRENT same-file imports, durable "
                      "imported-absorption rows after reopen, idempotent "
                      "re-import ROW-SKIP counts, consolidation-output and "
                      "recovery-state adapter cases — the amended 0009 "
                      "primitive's obligations (0021 §7b exact text; W15); "
                      "stated, awaiting the 0021 implementation")
    return checks


if __name__ == "__main__":
    results = run()                      # once (round-5 F4's note)
    for line in results:
        print("PASS", line)
    executed = sum(1 for r in results if not r.startswith("[impl-gated]"))
    print(f"store adapter harness: {executed} executed regression checks "
          f"pass against the SHIPPED store "
          f"(+{len(results) - executed} impl-gated obligation(s) stated)")
