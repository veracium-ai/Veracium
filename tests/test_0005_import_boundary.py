"""specs/0005 — the import trust boundary (P1–P16, the frozen acceptance surface).

Every default import caps all three trust levers (`author_of_evidence` and
`derived_from` to `THIRD_PARTY`, `disclosure` floored to `USE_ONLY`);
`restore=True` skips exactly the cap (trust-field-faithful over the shipped
identity canonicalization) and is a closed bool mutually exclusive with
`user_id`. This file also carries the §7b per-callsite disposition MANIFEST
(`test_import_memory_callsites_all_carry_a_disposition`) and the §7a audit /
CLI carriers.
"""
import ast
import json
import pathlib

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium.audit import AuditLog
from veracium.cli import main
from veracium.gate import partition_parts
from veracium.portability import _RESTORE_WARNING, export_memory, import_memory
from veracium.schema import Disclosure
from veracium.store.sqlite import SqliteStore

U = "alice"


class _Fake:
    """Scripted extraction: one grounded user fact + one third-party claim."""
    SCRIPTS = [
        {"triples": [{"subject": "user", "relation": "works_as", "object": "chef"}],
         "episode": "User is a chef."},
        {"triples": [{"subject": "org:quickclaim", "relation": "third_party_claim",
                      "object": "user owes $2,400"}],
         "episode": "Unverified billing notice: user owes $2,400."},
    ]

    def __init__(self, scripts=None):
        self._s = list(scripts if scripts is not None else self.SCRIPTS)

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill" and self._s:
            return json.dumps(self._s.pop(0))
        return ""


def _mem(db, scripts=None):
    return Memory(llm=_Fake(scripts),
                  config=MemoryConfig(require_source_id=False, db_path=db, wiki_recompile_after_writes=0))  # 0006 v8: opted out — measures records that exist (rule 8 / I3 / I13), not the ingest requirement


def _primed(tmp_path, db="src.db"):
    mem = _mem(str(tmp_path / db))
    mem.remember(U, "USER: I'm a chef.", date="2026-06-01")
    mem.remember(U, "From QuickClaim: you owe $2,400.", date="2026-06-04",
                 author=EvidenceAuthor.THIRD_PARTY, event_type="email")
    return mem


def _export(tmp_path, mem, name="e.jsonl", user=U):
    p = str(tmp_path / name)
    export_memory(mem.store, user, p)
    return p


def _lines(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def _write(p, header, recs):
    with open(p, "w") as f:
        f.write(json.dumps(header) + "\n")
        for r in recs:
            f.write(json.dumps(r) + "\n")


def _fresh(tmp_path, name="dst.db"):
    return SqliteStore(str(tmp_path / name))


# -- P1: a default import caps every record, and the reporting surfaces agree ---------
def test_default_import_caps_every_record(tmp_path):
    src = _primed(tmp_path)
    exp = _export(tmp_path, src)
    dst = _mem(str(tmp_path / "bob.db"))
    dst.import_memory(exp, user_id="bob")

    edges = dst.store.edges("bob", active_only=False, include_quarantined=True)
    assert edges, "fixture must import something"
    for e in edges:
        assert e.provenance.author_of_evidence == EvidenceAuthor.THIRD_PARTY
        assert e.provenance.derived_from == EvidenceAuthor.THIRD_PARTY
        assert not e.assertable
    for ep in dst.store.episodes("bob"):
        assert ep.provenance.third_party_influenced is True

    # the reporting surface (R1-1): nothing imported is attributed to the owner
    by_author = dst.introspect("bob")["by_author"]
    assert by_author.get("user", 0) == 0 and by_author.get("system", 0) == 0
    assert by_author.get("third_party", 0) == len(edges)
    src.close(); dst.close()


# -- P2: restore is trust-field-faithful over the four-cell matrix --------------------
_TRUST_FIELDS = ("author_of_evidence", "disclosure", "derived_from",
                 "confidence", "valid_from", "observed_at", "needs_confirmation")


def test_restore_preserves_trust_fields_exactly(tmp_path):
    src = _primed(tmp_path)
    exp = _export(tmp_path, src)
    file_recs = {r["id"]: r for r in _lines(exp)[1:] if r["record"] == "edge"}

    # cell 1: ordinary export -> FRESH destination (trust fields exactly as filed)
    dst = _fresh(tmp_path)
    import_memory(dst, exp, restore=True)
    for e in dst.edges(U, active_only=False, include_quarantined=True):
        filed = file_recs[e.id]
        got = json.loads(e.model_dump_json())
        for f in _TRUST_FIELDS:
            if f in ("author_of_evidence", "disclosure", "derived_from"):
                assert got["provenance"].get(f) == filed["provenance"].get(f), f
            else:
                assert got.get(f) == filed.get(f), f

    # cell 2: ordinary export -> SAME (source) store: record-equal skip
    r = import_memory(src.store, exp, restore=True)
    assert r["edges"] == 0 and r["episodes"] == 0 and r["skipped"] > 0
    src.close(); dst.close()


def test_restore_of_a_finalized_output_export(tmp_path):
    # cells 3+4: the finalized-consolidation-output shape, fresh + same-store.
    # Fresh destination: canonical identity transforms applied (hist: remap).
    hdr, base = _template(tmp_path)
    out = _indexed_output(base, op="op-live-1")
    exp = str(tmp_path / "cons.jsonl")
    _write(exp, hdr, [base["edge"], out])
    dst = _fresh(tmp_path)
    import_memory(dst, exp, restore=True)
    stored = [ep for ep in dst.episodes(U) if ep.lineage]
    assert len(stored) == 1
    assert stored[0].operation_id.startswith("hist:")   # canonicalized, not byte-kept
    # trust fields preserved exactly as filed
    assert stored[0].provenance.author_of_evidence.value == \
        out["provenance"]["author_of_evidence"]

    # same-store re-import of the SAME FILE: the remap is deterministic, so the
    # canonical form is stable and the re-import record-equal-skips.
    r = import_memory(dst, exp, restore=True)
    assert r["episodes"] == 0 and r["skipped"] >= 1
    dst.close()


# -- P3: the cap never raises (fixed points are byte-unchanged) -----------------------
def test_import_cap_never_raises(tmp_path):
    hdr, base = _template(tmp_path)
    for disc in ("use_only", "quarantined"):
        rec = json.loads(json.dumps(base["edge"]))
        rec["id"] = f"e-fp-{disc}"
        rec["provenance"]["author_of_evidence"] = "third_party"
        rec["provenance"]["derived_from"] = "third_party"
        rec["provenance"]["disclosure"] = disc
        exp = str(tmp_path / f"fp-{disc}.jsonl")
        _write(exp, hdr, [rec])
        dst = _fresh(tmp_path, f"fp-{disc}.db")
        r = import_memory(dst, exp)
        assert r["capped"] == 0, "a fixed-point record must not count as capped"
        [e] = dst.edges(U, active_only=False, include_quarantined=True)
        assert e.provenance.disclosure.value == disc          # never raised
        assert e.provenance.author_of_evidence == EvidenceAuthor.THIRD_PARTY
        dst.close()


# -- P4: hand-written files cannot evade the cap — the two reachable omission cells --
def test_handwritten_export_cannot_evade_the_cap(tmp_path):
    hdr, base = _template(tmp_path)
    adversarial = json.loads(json.dumps(base["edge"]))
    adversarial["id"] = "e-adv"
    adversarial["provenance"]["author_of_evidence"] = "user"
    adversarial["provenance"]["derived_from"] = None
    adversarial["provenance"]["disclosure"] = "mentionable"

    omitted = json.loads(json.dumps(base["edge"]))
    omitted["id"] = "e-omit"
    omitted["provenance"]["author_of_evidence"] = "user"   # required — cannot omit
    omitted["provenance"].pop("disclosure", None)          # -> MENTIONABLE default
    omitted["provenance"].pop("derived_from", None)        # -> None

    exp = str(tmp_path / "adv.jsonl")
    _write(exp, hdr, [adversarial, omitted])
    dst = _fresh(tmp_path)
    r = import_memory(dst, exp)
    assert r["capped"] == 2
    for e in dst.edges(U, active_only=False, include_quarantined=True):
        assert not e.assertable
        assert e.provenance.author_of_evidence == EvidenceAuthor.THIRD_PARTY
        assert e.provenance.derived_from == EvidenceAuthor.THIRD_PARTY
        assert e.provenance.disclosure == Disclosure.USE_ONLY
    dst.close()


# -- P5: restore and user_id are mutually exclusive ----------------------------------
def test_restore_with_remap_is_refused(tmp_path):
    dst = _fresh(tmp_path)
    with pytest.raises(ValueError, match="mutually exclusive"):
        import_memory(dst, str(tmp_path / "never-read.jsonl"),
                      user_id="bob", restore=True)
    # the CLI form exits non-zero via argparse mutual exclusion
    rc = None
    try:
        rc = main(["import", str(tmp_path / "x.jsonl"), "--restore", "--user", "bob",
                   "--db", str(tmp_path / "cli.db")])
    except SystemExit as e:
        rc = e.code
    assert rc not in (0, None)
    dst.close()


# -- P6: the cap is unconditional without restore ------------------------------------
def test_every_import_caps_by_default(tmp_path):
    src = _primed(tmp_path)
    exp = _export(tmp_path, src)

    # same-user import into a FRESH store still caps
    dst = _fresh(tmp_path, "same-user.db")
    import_memory(dst, exp)                     # header user kept — no remap
    for e in dst.edges(U, active_only=False, include_quarantined=True):
        assert e.provenance.author_of_evidence == EvidenceAuthor.THIRD_PARTY

    # a crafted header equal to the target caps identically (v1's suppression vector)
    ls = _lines(exp)
    ls[0]["user_id"] = "bob"
    for rec in ls[1:]:
        rec["user_id"] = "bob"
    crafted = str(tmp_path / "crafted.jsonl")
    _write(crafted, ls[0], ls[1:])
    dst2 = _fresh(tmp_path, "crafted.db")
    import_memory(dst2, crafted, user_id="bob")
    for e in dst2.edges("bob", active_only=False, include_quarantined=True):
        assert e.provenance.author_of_evidence == EvidenceAuthor.THIRD_PARTY
        assert not e.assertable
    src.close(); dst.close(); dst2.close()


# -- P7: the episode channel is closed -----------------------------------------------
def test_imported_episode_renders_unverified(tmp_path):
    src = _primed(tmp_path)
    exp = _export(tmp_path, src)
    dst = _mem(str(tmp_path / "bob.db"))
    dst.import_memory(exp, user_id="bob")
    edges = dst.store.edges("bob", active_only=True)
    eps = dst.store.episodes("bob")
    edge_lines, grounded_eps, claim_lines, tp_eps = partition_parts(edges, eps)
    grounded_joined = "\n".join(edge_lines + grounded_eps)
    unverified_joined = "\n".join(claim_lines + tp_eps)
    assert "chef" not in grounded_joined, "an imported author=user episode must not ground"
    assert "chef" in unverified_joined, "the material renders unverified, not lost"
    src.close(); dst.close()


# -- P8: import mutates nothing existing ---------------------------------------------
def test_import_never_mutates_existing_rows(tmp_path):
    dst_mem = _primed(tmp_path, db="dst.db")
    store = dst_mem.store

    def snapshot():
        return (sorted(e.model_dump_json() for e in
                       store.edges(U, active_only=False, include_quarantined=True)),
                sorted(ep.model_dump_json() for ep in store.episodes(U)))

    other = _primed(tmp_path, db="other.db")
    exp = _export(tmp_path, other, name="other.jsonl")

    before = snapshot()
    import_memory(store, exp, user_id="carol")          # success path (fresh user)
    assert snapshot() == before

    # refused path: own-store default re-import
    own = _export(tmp_path, dst_mem, name="own.jsonl")
    with pytest.raises(ValueError):
        import_memory(store, own)
    assert snapshot() == before

    # crafted supersedes-into-destination path: a new edge whose supersedes
    # names an existing destination edge — stored lineage only, active untouched
    target = store.edges(U, active_only=True)[0]
    hdr, base = _template(tmp_path)
    rec = json.loads(json.dumps(base["edge"]))
    rec["id"] = "e-super"
    rec["supersedes"] = target.id
    sup = str(tmp_path / "super.jsonl")
    _write(sup, hdr, [rec])
    import_memory(store, sup)
    # the new edge INSERTS (capped, supersedes stored as inert lineage); every
    # PRE-EXISTING row stays byte-identical and the target's active flag holds
    before_edge_rows, before_ep_rows = before
    before_ids = {json.loads(r)["id"] for r in before_edge_rows}
    after_existing = sorted(e.model_dump_json() for e in
                            store.edges(U, active_only=False, include_quarantined=True)
                            if e.id in before_ids)
    assert after_existing == before_edge_rows
    assert sorted(ep.model_dump_json() for ep in store.episodes(U)) == before_ep_rows
    refreshed = [e for e in store.edges(U, active_only=True) if e.id == target.id]
    assert refreshed and refreshed[0].active
    dst_mem.close(); other.close()


# -- P9: source-identity fields do not bypass the cap (0006 I7, discharged) ----------
def test_imported_source_id_does_not_bypass_the_remap_cap(tmp_path):
    hdr, base = _template(tmp_path)
    rec = json.loads(json.dumps(base["edge"]))
    rec["id"] = "e-foreign"
    foreign = "11111111-2222-4333-8444-555555555555"
    rec["provenance"]["origin"] = foreign
    rec["provenance"]["source_id"] = "their-mailbox"
    rec["provenance"]["author_of_evidence"] = "user"
    rec["provenance"]["disclosure"] = "mentionable"
    exp = str(tmp_path / "foreign.jsonl")
    _write(exp, hdr, [rec])
    dst = _fresh(tmp_path)
    import_memory(dst, exp, user_id="bob")
    [e] = dst.edges("bob", active_only=False, include_quarantined=True)
    # capped normally…
    assert e.provenance.author_of_evidence == EvidenceAuthor.THIRD_PARTY
    assert not e.assertable
    # …and grouping fields preserved (I2b), on the CAPPED record only
    assert e.provenance.origin == foreign
    assert e.provenance.source_id == "their-mailbox"
    dst.close()


# -- P10: the refusal carries the pinned warning -------------------------------------
def test_own_store_reimport_refusal_names_restore(tmp_path):
    mem = _primed(tmp_path)
    exp = _export(tmp_path, mem)
    with pytest.raises(ValueError) as exc:
        import_memory(mem.store, exp)
    msg = str(exc.value)
    assert "--restore" in msg
    assert "trusts every record" in msg
    assert "exported yourself or have independently verified" in msg
    mem.close()


# -- P11: `capped` is destination-blind, including through the projection-skip branch -
def test_capped_count_is_destination_blind(tmp_path):
    src = _primed(tmp_path)
    exp = _export(tmp_path, src)

    empty = _fresh(tmp_path, "empty.db")
    r1 = import_memory(empty, exp, user_id="bob")

    prepop = _fresh(tmp_path, "prepop.db")
    import_memory(prepop, exp, user_id="bob")           # pre-populate (all capped)
    r2 = import_memory(prepop, exp, user_id="bob")      # every ordinary rec re-imports fresh ids
    # NOTE: user_id remap mints fresh ids each call, so this destination holds
    # records; capped still reports the file's own count, not destination state.
    assert r1["capped"] == r2["capped"] > 0

    # the 0014 capped-projection skip branch: an indexed output that skips
    hdr, base = _template(tmp_path)
    out = _indexed_output(base, op="op-cap-1")
    out["provenance"]["author_of_evidence"] = "user"
    cons = str(tmp_path / "cons.jsonl")
    _write(cons, hdr, [out])
    d3 = _fresh(tmp_path, "d3.db")
    ra = import_memory(d3, cons)
    rb = import_memory(d3, cons)                        # projection-equal -> skip
    assert rb["episodes"] == 0
    assert ra["capped"] == rb["capped"] == 1
    src.close(); empty.close(); prepop.close(); d3.close()


# -- P12: imported corroboration cannot promote --------------------------------------
def test_imported_outcomes_cannot_promote_a_capped_edge(tmp_path):
    hdr, base = _template(tmp_path)
    edge = json.loads(json.dumps(base["edge"]))
    edge["id"] = "e-promo"
    edge["provenance"]["author_of_evidence"] = "user"
    edge["provenance"]["disclosure"] = "mentionable"
    outcomes = []
    prev = None
    for i in range(1, 4):                                # N fabricated judgments
        o = json.loads(json.dumps(base["episode"]))
        o.update({"id": f"ep-out-{i}", "kind": "outcome", "edge_id": "e-promo",
                  "seq": i, "supersedes_episode": prev,
                  "judgment_time_known": True, "outcome": "confirmed"})
        o["provenance"]["evidence_ref"] = "claim-1"
        outcomes.append(o)
        prev = o["id"]
    exp = str(tmp_path / "promo.jsonl")
    _write(exp, hdr, [edge] + outcomes)
    dst = _fresh(tmp_path)
    import_memory(dst, exp)
    [e] = dst.edges(U, active_only=False, include_quarantined=True)
    assert not e.assertable, "corroboration count must not promote a capped edge"
    assert e.provenance.author_of_evidence == EvidenceAuthor.THIRD_PARTY
    assert len([ep for ep in dst.episodes(U) if ep.kind == "outcome"]) == 3
    dst.close()


# -- P13: restore is a closed predicate ----------------------------------------------
def test_restore_rejects_non_bool_values(tmp_path):
    dst = _fresh(tmp_path)
    ghost = str(tmp_path / "does-not-exist.jsonl")       # nonexistent: nothing may be read
    for bad in ("false", "true", 1, 0, None, [], object()):
        with pytest.raises(TypeError, match="restore must be a bool"):
            import_memory(dst, ghost, restore=bad)
    # real bools behave per §4a (True reaches the file and fails on absence)
    with pytest.raises(FileNotFoundError):
        import_memory(dst, ghost, restore=True)
    dst.close()


# -- P14: the validate-then-cap sequence, all nine cells ------------------------------
@pytest.mark.parametrize("field,cell,payload_edit,expect", [
    ("author_of_evidence", "omitted", ("pop", None), "refuse"),
    ("author_of_evidence", "null", ("set", None), "refuse"),
    ("author_of_evidence", "malformed", ("set", "banana"), "refuse"),
    ("disclosure", "omitted", ("pop", None), "accept"),
    ("disclosure", "null", ("set", None), "refuse"),
    ("disclosure", "malformed", ("set", "banana"), "refuse"),
    ("derived_from", "omitted", ("pop", None), "accept"),
    ("derived_from", "null", ("set", None), "accept"),
    ("derived_from", "malformed", ("set", "banana"), "refuse"),
])
def test_malformed_trust_fields_raise_never_normalize(tmp_path, field, cell,
                                                      payload_edit, expect):
    hdr, base = _template(tmp_path)
    rec = json.loads(json.dumps(base["edge"]))
    rec["id"] = f"e-{field}-{cell}"
    op, value = payload_edit
    if op == "pop":
        rec["provenance"].pop(field, None)
    else:
        rec["provenance"][field] = value
    exp = str(tmp_path / f"m-{field}-{cell}.jsonl")
    _write(exp, hdr, [rec])
    dst = _fresh(tmp_path, f"m-{field}-{cell}.db")
    if expect == "refuse":
        with pytest.raises(Exception):
            import_memory(dst, exp)
        assert dst.edges(U, active_only=False, include_quarantined=True) == []
    else:
        import_memory(dst, exp)
        [e] = dst.edges(U, active_only=False, include_quarantined=True)
        assert e.provenance.derived_from == EvidenceAuthor.THIRD_PARTY   # capped
        assert e.provenance.disclosure == Disclosure.USE_ONLY
    dst.close()


# -- P15: the tampered-own-export mixed file -----------------------------------------
def test_tampered_own_export_refuses_with_warning(tmp_path):
    mem = _primed(tmp_path)
    exp = _export(tmp_path, mem)
    ls = _lines(exp)
    hdr, base = _template(tmp_path)
    attacker = json.loads(json.dumps(base["edge"]))
    attacker["id"] = "e-attacker"
    attacker["provenance"]["author_of_evidence"] = "user"
    attacker["provenance"]["disclosure"] = "mentionable"
    tampered = str(tmp_path / "tampered.jsonl")
    _write(tampered, ls[0], ls[1:] + [attacker])
    with pytest.raises(ValueError) as exc:
        import_memory(mem.store, tampered)               # default path refuses WHOLE
    assert "trusts every record" in str(exc.value)
    assert "e-attacker" not in {e.id for e in
                                mem.store.edges(U, active_only=False,
                                                include_quarantined=True)}
    # documented, not asserted-away: --restore on this file WOULD admit the
    # attacker edge — the pinned warning is the designed mitigation (§8 limit 1).
    mem.close()


# -- P16: the 0014 amendment — equivalence-class pairs and fixed points ---------------
def _identity_pair(tmp_path, field, val_a, val_b, op="op-p16"):
    hdr, base = _template(tmp_path)
    a = _indexed_output(base, op=op)
    b = json.loads(json.dumps(a))
    if val_a is _POP:
        a["provenance"].pop(field, None)
    else:
        a["provenance"][field] = val_a
    if val_b is _POP:
        b["provenance"].pop(field, None)
    else:
        b["provenance"][field] = val_b
    fa, fb = str(tmp_path / "a.jsonl"), str(tmp_path / "b.jsonl")
    _write(fa, hdr, [a]); _write(fb, hdr, [b])
    return fa, fb


_POP = object()


@pytest.mark.parametrize("field,val_a,val_b", [
    ("author_of_evidence", "user", "system"),
    ("author_of_evidence", "user", "third_party"),
    ("derived_from", "user", "system"),
    ("derived_from", "third_party", _POP),
    ("disclosure", "mentionable", "use_only"),
])
def test_capped_projection_identity_matrix_equivalent_pairs_skip(
        tmp_path, field, val_a, val_b):
    fa, fb = _identity_pair(tmp_path, field, val_a, val_b)
    dst = _fresh(tmp_path)
    import_memory(dst, fa)
    r = import_memory(dst, fb)                           # cap-equivalent -> skip
    assert r["episodes"] == 0
    assert len([ep for ep in dst.episodes(U) if ep.lineage]) == 1
    dst.close()


@pytest.mark.parametrize("field,val_a,val_b", [
    ("disclosure", "mentionable", "quarantined"),
    ("disclosure", "use_only", "quarantined"),
])
def test_capped_projection_identity_matrix_inequivalent_pairs_refuse(
        tmp_path, field, val_a, val_b):
    fa, fb = _identity_pair(tmp_path, field, val_a, val_b)
    dst = _fresh(tmp_path)
    import_memory(dst, fa)
    with pytest.raises(ValueError, match="DIFFERENT|different"):
        import_memory(dst, fb)
    dst.close()


def test_capped_projection_content_difference_refuses(tmp_path):
    hdr, base = _template(tmp_path)
    a = _indexed_output(base, op="op-content")
    b = json.loads(json.dumps(a))
    b["summary"] = "a DIFFERENT synthesized summary"
    fa, fb = str(tmp_path / "ca.jsonl"), str(tmp_path / "cb.jsonl")
    _write(fa, hdr, [a]); _write(fb, hdr, [b])
    dst = _fresh(tmp_path)
    import_memory(dst, fa)
    with pytest.raises(ValueError):
        import_memory(dst, fb)
    dst.close()


def test_mixed_path_refuses_where_the_cap_changes_a_field(tmp_path):
    hdr, base = _template(tmp_path)
    rec = _indexed_output(base, op="op-mixed")
    rec["provenance"]["author_of_evidence"] = "user"     # NOT a fixed point
    f = str(tmp_path / "mixed.jsonl")
    _write(f, hdr, [rec])

    d1 = _fresh(tmp_path, "d1.db")
    import_memory(d1, f)                                 # default: stored capped
    with pytest.raises(ValueError):
        import_memory(d1, f, restore=True)               # uncapped incoming differs

    d2 = _fresh(tmp_path, "d2.db")
    import_memory(d2, f, restore=True)                   # restore: stored uncapped
    with pytest.raises(ValueError):
        import_memory(d2, f)                             # capped incoming differs
    d1.close(); d2.close()


@pytest.mark.parametrize("disc", ["use_only", "quarantined"])
def test_fixed_point_records_are_path_invisible(tmp_path, disc):
    hdr, base = _template(tmp_path)
    rec = _indexed_output(base, op=f"op-fp-{disc}")
    rec["provenance"]["author_of_evidence"] = "third_party"
    rec["provenance"]["derived_from"] = "third_party"
    rec["provenance"]["disclosure"] = disc               # BOTH fixed-point families
    f = str(tmp_path / f"fp-{disc}.jsonl")
    _write(f, hdr, [rec])

    d1 = _fresh(tmp_path, f"fp1-{disc}.db")
    import_memory(d1, f)                                 # default first
    r = import_memory(d1, f, restore=True)               # then restore: SKIP
    assert r["episodes"] == 0
    assert len([ep for ep in d1.episodes(U) if ep.lineage]) == 1

    d2 = _fresh(tmp_path, f"fp2-{disc}.db")
    import_memory(d2, f, restore=True)                   # restore first
    r = import_memory(d2, f)                             # then default: SKIP
    assert r["episodes"] == 0
    assert len([ep for ep in d2.episodes(U) if ep.lineage]) == 1
    d1.close(); d2.close()


def test_restore_restore_uncapped_difference_refuses(tmp_path):
    # P16(iv): 0014's full-resolution alarm on the restore path, untouched
    fa, fb = _identity_pair(tmp_path, "disclosure", "mentionable", "use_only")
    dst = _fresh(tmp_path)
    import_memory(dst, fa, restore=True)
    with pytest.raises(ValueError):
        import_memory(dst, fb, restore=True)
    dst.close()


# -- §7a: the audit carrier keeps its shipped field set ------------------------------
def test_import_audit_payload_field_set_is_unchanged(tmp_path):
    src = _primed(tmp_path)
    exp = _export(tmp_path, src)
    log = AuditLog(str(tmp_path / "audit.jsonl"))
    dst = Memory(llm=_Fake([]), audit=log,
                 config=MemoryConfig(require_source_id=False, db_path=str(tmp_path / "bob.db"),  # 0006 v8: opted out — measures records that exist (rule 8 / I3 / I13), not the ingest requirement
                                     wiki_recompile_after_writes=0))
    r = dst.import_memory(exp, user_id="bob")
    assert r["capped"] > 0                                # the return DOES carry it
    [entry] = log.entries(op="import")
    payload_keys = set(entry.keys()) - {"op", "user_id", "ts"}
    assert payload_keys == {"edges", "episodes", "skipped"}, \
        "capped is deliberately NOT forwarded to the audit record (specs/0005 §7a)"
    src.close(); dst.close()


# -- §7a: the CLI printed line -------------------------------------------------------
def test_cli_import_line_carries_capped_only_on_the_default_path(tmp_path, capsys):
    src = _primed(tmp_path)
    exp = _export(tmp_path, src)
    src.close()

    assert main(["import", exp, "--user", "bob", "--db", str(tmp_path / "c1.db")]) == 0
    out = capsys.readouterr().out
    assert "capped to third-party trust" in out

    assert main(["import", exp, "--restore", "--db", str(tmp_path / "c2.db")]) == 0
    out = capsys.readouterr().out
    assert "capped" not in out


# -- §7b: the per-callsite disposition manifest --------------------------------------
# Every `import_memory` call under tests/ must carry a recorded disposition.
# A new, unmapped site FAILS this manifest until classified. Dispositions:
#   default  — stays on the default (capping) path: trust tests, fresh-store
#              imports, and refusal fixtures that assert their ORIGINAL reason.
#   restore  — relocated to restore=True per specs/0005 §7b (integrity
#              round-trip semantics: trust-field preservation, own-store
#              re-import, byte-level chain preservation).
#   both     — exercises the two paths deliberately (this file's own tests).
_CALLSITE_DISPOSITIONS = {
    # 0044 T11a (outcome portability): the module's one helper forwards `restore=` from each cell — both modes
    ("test_0044_t11a_portability.py", "_import"): "both",
    ("test_0044_t11a_portability.py", "_refuses"): "both",
    ("test_0047_t11b_portability.py", "_refused"): "both",
    # specs/0031 v23.1 (the call-path era): the round trip restores the store's own export; the old-reader and
    # planted-file cells are refusals before any record is admitted, the same in either mode, run as restores
    ("test_0031_trust_tools_library.py", "test_the_call_path_survives_export_import_and_a_redaction_of_the_audit_episode"): "restore",
    ("test_0031_trust_tools_library.py", "test_an_older_reader_refuses_a_15_file"): "restore",
    ("test_0031_trust_tools_library.py", "test_a_file_declaring_14_that_carries_an_agent_path_is_refused_whole"): "restore",
    # R-II round 2 (RII-01): an imported challenge evicts the cached wiki — both imports are restores of the user's own file
    ("test_0047_rii01_wiki_bind.py", "test_a_challenge_admitted_after_a_cached_wiki_is_never_asserted_by_it"): "restore",
    # R-II round 3 (RII-R3-01, 0004 v3.5 §2c (ii)/(iii)): the import's episode admission refuses by the id — the helper
    # forwards `restore=` from each cell; the replay cell restores a finalized op's outputs; the notice cell imports A's
    # notice-only cut and B's own plain file, both by default
    ("test_rii_r3_01_episode_owner.py", "_import"): "both",
    ("test_rii_r3_01_episode_owner.py", "test_a_restore_replaying_finalized_outputs_is_admitted_beside_an_in_flight_op"): "restore",
    ("test_rii_r3_01_episode_owner.py", "test_one_users_standing_notice_does_not_reach_another_users_import_of_the_id"): "default",
    ("test_rii_r3_01_episode_owner.py", "test_another_users_standing_notice_never_covers_a_forged_redacted_reason"): "both",
    # R-II round 3 NEXT-ROUND (research N2): an id another user holds is an owner conflict — the helper forwards
    # `restore=` from each cell
    ("test_rii_r3_n2_import_owner_conflict.py", "_import"): "both",
    # the kind closure held on its own: A restores its notice-only cut; B imports its forged arrival by default
    ("test_rii_r3_kind_closure_by_owner.py", "_a_holds_a_standing_notice_naming_kind"): "restore",
    ("test_rii_r3_kind_closure_by_owner.py", "test_another_users_standing_notice_never_admits_a_marker_kind"): "default",
    # R-II round 4: the reviewer's two files, byte-identical — each cell imports in both modes through its inner `run`
    # (the MARKER file restores its notice-only cut first)
    ("test_rii_r4_reviewer_import_boundary_atomicity.py", "run"): "both",
    ("test_rii_r4_reviewer_import_boundary_atomicity.py", "test_import_checks_durable_id_state_and_rolls_back_prefix"): "both",
    ("test_rii_r4_reviewer_marker_kind_owner.py", "run"): "both",
    ("test_rii_r4_reviewer_marker_kind_owner.py", "test_marker_kind_coverage_is_owned_by_the_destination"): "both",
    # R-A round 2 (RA-01, RA-02): the notice boundaries the external reviewer found, both modes where parametrised
    ("test_0041_ra2_notice_boundaries.py", "test_a_restore_that_would_treat_a_claimed_episode_refuses_the_whole_unit"): "restore",
    ("test_0041_ra2_notice_boundaries.py", "test_a_prior_standing_notice_is_judged_on_the_arriving_copy"): "both",
    ("test_0041_ra2_notice_boundaries.py", "test_the_standing_arrival_refusal_does_not_depend_on_the_order_of_the_units_notices"): "both",
    ("test_0041_ra2_notice_boundaries.py", "test_a_store_caller_without_the_staged_answer_is_judged_on_the_arriving_copy_too"): "both",
    ("test_0041_ra2_notice_boundaries.py", "test_an_arrival_under_a_completed_attestation_is_judged_on_the_copy_that_arrived"): "both",
    # the 2026-10-13 notice-binding hotfix: the untrusted path is its subject; one restore control
    ("test_0041_notice_binding_hotfix.py", "test_an_untrusted_notice_never_redacts_the_users_own_held_fact"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_an_untrusted_notice_never_redacts_a_held_episode"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_the_victims_exact_record_in_the_file_does_not_unlock_the_notice"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_a_held_different_version_under_an_untrusted_notice_is_kept_and_reported"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_an_untrusted_notice_for_an_absent_id_leaves_an_inert_standing_row"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_a_later_unredacted_record_of_that_id_is_refused_whole_and_nothing_is_redacted"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_a_redacted_record_arriving_new_is_still_redacted_in_the_same_transaction"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_a_trusted_restore_of_a_newer_backup_still_redacts_the_held_older_record"): "restore",
    ("test_0041_notice_binding_hotfix.py", "test_a_repeat_untrusted_import_stays_inert"): "default",
    ("test_0041_notice_binding_hotfix.py", "_legacy_standing"): "restore",   # writes a standing notice as the earlier code did
    ("test_0041_notice_binding_hotfix.py", "test_ii_a_default_REDACTED_arrival_from_another_origin_is_pending_origin_decides_nothing"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_ii_an_unredacted_arrival_under_a_standing_notice_refuses_even_on_restore"): "restore",
    ("test_0041_notice_binding_hotfix.py", "test_7a_a_poisoned_export_default_imported_refuses_and_redacts_nothing"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_7b_a_poisoned_export_restored_into_a_fresh_store_refuses_and_redacts_nothing"): "restore",
    ("test_0041_notice_binding_hotfix.py", "test_7c_a_poisoned_store_restoring_its_own_export_refuses_and_keeps_the_fact"): "restore",
    ("test_0041_notice_binding_hotfix.py", "test_a_notice_only_restore_onto_a_held_record_is_not_applied"): "restore",
    ("test_0041_notice_binding_hotfix.py", "test_7_the_default_path_reports_a_held_target_before_it_would_refuse"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_the_attest_only_branch_is_restore_only_on_a_default_import"): "default",
    ("test_0041_notice_binding_hotfix.py", "test_i_a_legacy_standing_notice_never_refuses_the_users_own_write"): "both",
    ("test_0041_notice_binding_hotfix.py", "test_i_a_legacy_standing_notice_never_refuses_the_users_own_episode_write"): "restore",
    ("test_0041_notice_binding_hotfix.py", "test_ii_an_unredacted_default_arrival_under_a_standing_notice_is_refused_whole"): "both",
    ("test_0041_notice_binding_hotfix.py", "test_ii_a_default_arrival_from_the_notices_own_origin_is_pending_not_applied"): "both",
    ("test_0041_notice_binding_hotfix.py", "test_ii_on_restore_completion_needs_an_inserted_shown_record_and_not_its_origin"): "restore",
    ("test_0041_notice_binding_hotfix.py", "test_ii_a_treated_default_arrival_under_a_standing_notice_is_admitted"): "both",
    # specs/0041 §11.6.6 (T4): the notice state machine — each test's mode is its subject, both where it is the table's
    # mode column (a parametrised restore flag, or a restore that writes the standing notice the default arrival meets)
    ("test_0041_notice_state.py", "_pending"): "default",
    ("test_0041_notice_state.py", "_store_holding"): "both",
    ("test_0041_notice_state.py", "test_a_created_record_must_show_its_notice_in_both_modes"): "both",
    ("test_0041_notice_state.py", "test_a_default_import_never_changes_a_held_record_through_a_notice"): "default",
    ("test_0041_notice_state.py", "test_a_pending_notice_is_no_attestation_and_refuses_no_local_write"): "default",
    ("test_0041_notice_state.py", "test_a_repeat_default_import_of_a_pending_notice_is_existing_and_keeps_its_reason"): "default",
    ("test_0041_notice_state.py", "test_a_restore_with_no_copy_applies_over_a_held_record_that_already_shows_it"): "both",
    ("test_0041_notice_state.py", "test_a_standing_notice_on_a_created_arrival_that_shows_it"): "both",
    ("test_0041_notice_state.py", "test_a_standing_notice_over_a_local_write_is_weighed_as_a_held_target"): "both",
    ("test_0041_notice_state.py", "test_a_standing_notice_refuses_an_unredacted_arrival_in_both_modes"): "both",
    ("test_0041_notice_state.py", "test_a_stores_own_export_round_trips_whatever_its_notices_hold"): "both",
    ("test_0041_notice_state.py", "test_a_trusted_restore_over_a_held_target_follows_the_files_copy"): "restore",
    ("test_0041_notice_state.py", "test_an_absent_target_leaves_an_inert_standing_notice"): "both",
    ("test_0041_notice_state.py", "test_an_episode_notice_pending_deleted_inert_recreated_then_confirmed"): "default",
    ("test_0041_notice_state.py", "test_confirm_notice_refuses_a_standing_row_as_standing"): "restore",
    ("test_0041_notice_state.py", "test_coverage_counts_a_standing_notice_for_a_treated_arrivals_reason"): "default",
    ("test_0041_notice_state.py", "test_forget_user_erases_pending_and_standing_rows"): "default",
    ("test_0041_notice_state.py", "test_origin_decides_nothing"): "default",
    ("test_0041_notice_state.py", "test_the_users_own_redact_of_a_record_a_standing_notice_names_redacts_it"): "restore",
    ("test_0041_notice_state.py", "test_io_ii_1_a_record_not_in_file_pending_notice_keeps_its_reason_on_a_default_replay"): "both",
    ("test_0041_notice_state.py", "test_io_ii_1_a_standing_arrival_pending_notice_keeps_its_reason_on_a_repeat_of_the_notice"): "default",
    ("test_0041_notice_state.py", "test_r11_a_pending_notice_keeps_its_reason_through_a_restore_that_leaves_it_pending"): "both",
    ("test_0041_notice_state.py", "test_io_ii_3_a_confirmation_on_one_connection_then_an_import_on_another"): "default",
    ("test_0041_notice_state.py", "test_io_ii_3_every_application_reaches_the_full_record_fixed_point"): "both",
    ("test_0041_notice_state.py", "test_io_ii_3_a_refused_import_rolls_back_every_notice_state_transition"): "both",
    ("test_0041_notice_state.py", "test_io_ii_3_a_remapped_import_binds_notice_rows_to_the_destination_user"): "default",
    ("test_0041_notice_state.py", "test_io_ii_3_a_notice_is_scoped_to_its_target_kind"): "default",
    ("test_0041_notice_state.py", "test_t4_1_a_pending_notice_beside_its_unredacted_re_created_record_refuses_the_unit"): "default",
    ("test_0041_notice_state.py", "test_r18_confirm_notice_never_treats_another_users_record_under_the_same_id"): "default",
    ("test_0041_notice_state.py", "test_r9_a_standing_episode_notice_over_a_local_episode_write_round_trips_the_own_export"): "restore",
    ("test_0041_notice_state.py", "test_r10_a_restore_weighs_a_held_pending_notice"): "both",
    ("test_0041_notice_state.py", "test_r5_coverage_counts_a_standing_notice_for_a_treated_episodes_reason"): "default",
    ("test_0041_notice_state.py", "test_r27_a_standing_notices_own_copy_with_its_created_record_takes_the_created_row"): "both",
    # specs/0037 §4e: the procedural boundary — the default path REFUSES a
    # record as procedural on any of three raw signals (the six §2c cells and
    # the format-10 8-cell matrix, through the `run` helper); `restore=True`
    # is the positive leg (a store's own procedures round-trip with their
    # basis; inconsistent markers refused per record); the old-reader test
    # imports on the default path under a reader held at format 10
    # specs/0027 v14 §4g (V-RECEIPT-NOT-EXPORTED): a default-path import of an
    # export taken after a firing recall — the destination holds no receipt
    ("test_0027_policy_receipt.py",
     "test_receipts_are_not_exported_and_an_import_carries_none"): "default",
    # specs/0041 §4g (tranche 4b, 2026-09-20): the import contract for redaction notices — restore round-trips
    # (a store's own redactions arrive attested); the remap test drives the default path on purpose (the
    # notice's subject moves with the record's); the invalid-notice, integrity and old-reader tests refuse
    # BEFORE the trust cap is reached, on the restore path
    ("test_0041_import_contract.py", "test_an_older_reader_refuses_a_file_that_carries_a_notice"): "restore",
    ("test_0041_import_contract.py", "test_a_held_record_and_its_notice_commit_together_and_the_destination_attests_it"): "restore",
    ("test_0041_import_contract.py", "test_repeat_imports_are_idempotent_by_source_identity"): "restore",
    ("test_0041_import_contract.py", "test_a_notice_before_its_record_is_a_standing_notice_and_the_record_is_redacted_on_arrival"): "restore",
    ("test_0041_import_contract.py", "test_the_two_orders_reach_the_same_destination_state"): "restore",
    # 0041 round 10: the generated matrix — an own-store before/after restore pair (the receipt's lineage case), and a
    # CROSS-USER import on the capping path whose minted imp-… survivor the ledger treatment must read
    ("test_0041_round10_matrix.py", "test_the_receipt_names_a_restored_output_whose_lineage_consumed_the_redacted_episode"): "restore",
    ("test_0041_round10_matrix.py", "test_an_imported_absorption_ledger_is_treated_under_its_minted_id"): "default",
    # 0041 round 10, the notice across the import boundary (R9-04/05/08 on the capping path; R9-06 restores the
    # frozen store's own treated history)
    ("test_0041_round11_provenance.py", "test_R10_04_every_admitted_local_reason_round_trips"): "restore",
    ("test_0041_round11_provenance.py", "test_control_a_genuine_imported_notice_keeps_the_sources_facts"): "restore",
    ("test_0041_round11_provenance.py", "test_R10_04_a_hand_built_notice_claiming_this_stores_own_identity_still_reads_as_witnessed"): "both",
    ("test_0041_round11_provenance.py", "test_R10_04_a_hand_built_notice_cannot_clear_its_own_provenance"): "both",
    ("test_0041_round11_provenance.py", "test_R10_04_a_notice_whose_own_reason_is_the_witness_label_is_refused"): "default",
    ("test_0041_round11_provenance.py", "test_the_doctor_calls_a_notice_standing_by_its_missing_event_and_never_a_local_row"): "restore",
    ("test_0041_round11_outcome.py", "test_R10_01_full_export_applies_notice_to_held_outcome"): "both",
    ("test_0041_round11_outcome.py", "test_the_treated_held_outcome_keeps_its_chain"): "both",
    ("test_0041_round11_outcome.py", "test_A2_an_already_treated_held_outcome_meeting_its_old_record_ends_existing_with_no_new_event"): "default",
    ("test_0041_round11_outcome.py", "test_outcome_and_interaction_give_the_same_result_for_the_same_difference"): "default",
    ("test_0041_round11_outcome.py", "test_control_a_changed_outcome_with_no_notice_still_refuses"): "default",
    ("test_0041_round11_outcome.py", "test_control_a_topology_conflict_refuses_notice_or_not"): "default",
    ("test_0041_round11_arrival.py", "_attested_from_new"): "both",   # the 2026-10-13 hotfix: `new` sets up; `combined` refuses
    ("test_0041_round11_arrival.py", "test_R10_02_public_import_cannot_repopulate_a_deleted_attested_episode"): "both",
    ("test_0041_round11_arrival.py", "test_a_backup_taken_after_the_redaction_restores_after_a_delete"): "both",
    ("test_0041_round11_arrival.py", "test_an_honest_full_backup_of_several_redacted_episodes_restores_after_one_is_deleted"): "restore",
    ("test_0041_round11_arrival.py", "test_control_re_arrival_without_a_notice_still_refuses"): "both",
    ("test_0041_round11_arrival.py", "test_notice_only_after_the_delete_inserts_nothing"): "default",
    ("test_0041_round11_arrival.py", "test_an_arrival_needing_treatment_in_a_carrier_the_attestation_never_named_is_refused"): "default",
    ("test_0041_round11_attestation.py", "_unattested_marker_episode"): "default",
    ("test_0041_round11_attestation.py", "test_its_export_round_trips"): "restore",
    ("test_0041_round11_attestation.py", "test_a_mixed_record_attests_both_the_treated_and_the_already_marker_carriers"): "default",
    ("test_0041_round12_quarantine.py", "_round_trip"): "both",
    ("test_0041_round12_quarantine.py", "test_the_notice_domain_stays_closed"): "default",
    ("test_0041_round12_quarantine.py", "test_R11_01_quarantine_redaction_export_applies_to_held_target"): "both",
    ("test_0041_round12_quarantine.py", "test_a_destination_holding_the_relation_only_shape_moves_and_attests_its_own_disclosure"): "both",
    ("test_0041_round12_surface.py", "test_a_history_only_redaction_exports_a_notice_another_store_applies"): "both",
    ("test_0041_round12_surface.py", "test_a_notice_WITHOUT_the_journal_path_still_treats_the_destinations_journal"): "both",
    ("test_0041_round12_surface.py", "test_an_applied_notice_attests_each_path_once"): "restore",
    # 0041 round 12 (R11-03): one projection for native and witnessed rows — every call on the default path
    ("test_0041_round12_native.py", "test_R11_03_contradiction_with_native_source_event_refuses_atomically"): "default",
    ("test_0041_round12_native.py", "test_the_stores_own_event_relayed_back_honestly_is_existing_not_a_second_row"): "both",
    ("test_0041_round12_native.py", "test_a_self_import_under_a_remap_attests_the_copy_as_a_witnessed_row"): "default",
    ("test_0041_round12_native.py", "test_control_the_stores_own_export_re_imported_is_existing"): "default",
    ("test_0041_round12_native.py", "test_control_a_witnessed_contradiction_still_refuses"): "default",
    ("test_0041_round12_native.py", "test_two_native_events_of_one_user_are_compared_each_against_its_own"): "default",
    ("test_0041_round12_native.py", "test_a_foreign_origin_never_compares_against_a_native_row"): "default",
    ("test_0041_round12_native.py", "test_a_witnessed_row_holding_no_body_is_a_stated_limit_not_a_contradiction"): "default",
    # 0041 round 13 (R12-01 / N12-01, the 0014 §2c rider): a held consolidation output reached by its redaction; the
    # rider's paired oracle cells live in the 0014 file. By AST, helpers included.
    ("test_0014_portability.py", "_rider_held"): "default",
    ("test_0014_portability.py", "test_rider_a_named_field_at_the_marker_WITH_the_notice_resolves_and_treats_the_held_output"): "both",
    ("test_0014_portability.py", "test_rider_the_same_difference_WITHOUT_the_notice_rejects"): "default",
    ("test_0014_portability.py", "test_rider_a_field_the_notice_does_NOT_name_rejects"): "default",
    ("test_0014_portability.py", "test_rider_a_named_field_at_a_NON_marker_value_rejects"): "default",
    ("test_0014_portability.py", "test_rider_a_lineage_difference_rejects_notice_or_not"): "default",
    ("test_0014_portability.py", "test_rider_a_treated_held_output_meeting_its_untreated_arrival_with_the_notice_is_existing"): "default",
    ("test_0041_round13_outputs.py", "test_R12_01_indexed_output_redaction_reaches_held_output"): "both",
    ("test_0041_round13_outputs.py", "test_r29_a_pending_notice_over_a_held_output_does_not_explain_a_differing_arrival"): "default",
    ("test_0041_round13_outputs.py", "test_the_held_output_keeps_every_field_the_notice_does_not_name"): "restore",
    ("test_0041_round13_outputs.py", "test_N12_01_a_repeated_remapped_import_binds_the_notice_to_the_existing_copy"): "default",
    ("test_0041_round13_outputs.py", "test_every_redaction_row_names_a_record_after_held_earlier_and_repeat"): "both",
    ("test_0041_round13_outputs.py", "test_a_notice_for_a_DIFFERENT_record_does_not_admit_the_output_difference"): "default",
    ("test_0041_round13_outputs.py", "test_a_contradictory_body_on_the_rebound_notice_still_refuses_whole_import"): "restore",
    ("test_0041_round13_outputs.py", "test_control_the_unchanged_first_export_still_reimports_idempotently"): "default",
    ("test_0041_round13_outputs.py", "test_control_the_redacted_export_without_its_notice_still_refuses"): "default",
    # 0041 round 13 (N12-02): the frozen store's redacted episode, isolated, into a fresh destination
    ("test_0041_round13_side.py", "test_N12_02_an_empty_episode_of_a_source_whose_revocation_row_is_marked_is_redacted"): "default",
    # 0041 round 14 (R13-02, the rider's marker condition the WHOLE value): every call takes the mode from a parameter
    ("test_0041_round14_marker.py", "_setup"): "both",
    ("test_0041_round14_marker.py", "test_R13_02_a_value_that_merely_CONTAINS_the_marker_refuses_whole_import"): "both",
    ("test_0041_round14_marker.py", "test_control_ordinary_text_in_a_named_field_refuses"): "both",
    ("test_0041_round14_marker.py", "test_control_the_exact_marker_with_the_notices_is_admitted_and_treats_both"): "both",
    # 0041 round 14 (R13-01, a notice for its own RESOLVED subject only): by AST, a helper included
    ("test_0041_round14_resolution.py", "_setup"): "both",
    ("test_0041_round14_resolution.py", "test_R13_01_permuted_ids_with_ONE_notice_refuse_the_whole_import"): "both",
    ("test_0041_round14_resolution.py", "test_R13_01_an_ordinary_arrival_reusing_a_held_id_does_not_lend_its_notice"): "both",
    ("test_0041_round14_resolution.py", "test_control_permuted_ids_with_BOTH_notices_treat_both_held_outputs"): "both",
    ("test_0041_round14_resolution.py", "test_control_a_notice_naming_a_held_target_with_no_arrival_applies_to_it"): "both",
    ("test_0041_round14_resolution.py", "test_control_a_repeated_user_remap_binds_both_notices_to_the_surviving_copies"): "default",
    # 0041 round 13 (the round-12 verdict's evidence-scope note): the generated edge matrix into a HELD destination
    ("test_0041_round12_quarantine.py", "test_every_writer_reachable_edge_state_reaches_a_destination_holding_it_earlier"): "both",
    ("test_0041_round11_identity.py", "test_R10_03_a_two_source_triples_that_encoded_equal_are_two_standing_notices"): "restore",
    ("test_0041_round11_identity.py", "test_R10_03_b_a_relay_preserves_the_native_source_triple"): "default",
    ("test_0041_round11_identity.py", "test_the_original_and_its_relay_are_held_as_one_source_identity"): "default",
    ("test_0041_round11_identity.py", "test_R10_03_c_a_changed_body_under_the_same_source_identity_refuses"): "default",
    ("test_0041_round11_identity.py", "test_R10_03_c_the_comparison_crosses_a_destination_remap_for_a_NUL_identity"): "default",
    ("test_0041_round11_identity.py", "test_control_an_equal_body_remapped_twice_is_not_a_contradiction"): "default",
    ("test_0041_round11_identity.py", "test_an_empty_source_component_is_refused_at_the_boundary"): "default",
    ("test_0041_round10_notices.py", "test_R9_04_one_notice_imported_for_two_destination_users_attests_each_users_own_record"): "default",
    ("test_0041_round10_notices.py", "test_R9_04_an_honest_repeat_is_idempotent_and_writes_nothing"): "default",
    ("test_0041_round10_notices.py", "test_R9_04_a_later_contradictory_body_under_the_same_identity_refuses_atomically"): "default",
    ("test_0041_round10_notices.py", "test_R9_04_two_bodies_under_one_identity_in_one_file_still_refuse"): "default",
    ("test_0041_round10_notices.py", "test_R9_05_a_witnessed_receipt_reports_the_sources_facts_and_this_stores_application_beside_them"): "default",
    ("test_0041_round10_notices.py", "test_R9_05_the_relay_re_exports_the_source_body_unchanged"): "default",
    ("test_0041_round10_notices.py", "test_R9_05_the_original_and_its_honest_relay_are_one_notice_together_or_in_sequence"): "default",
    ("test_0041_round10_notices.py", "test_R9_05_a_relay_that_alters_the_body_is_refused"): "default",
    ("test_0041_round10_notices.py", "test_R9_05_facts_the_notice_does_not_carry_are_None_and_serialise_as_null"): "default",
    ("test_0041_round10_notices.py", "test_R9_06_the_treated_historical_prose_kind_episode_round_trips_with_its_notice"): "restore",
    ("test_0041_round10_notices.py", "test_R9_06_a_standing_notice_admits_the_marker_kind_when_the_record_arrives_later"): "restore",
    ("test_0041_round10_notices.py", "test_R9_06_the_closure_still_refuses_what_no_attestation_accounts_for"): "restore",
    ("test_0041_round10_notices.py", "test_R9_08_notice_field_names_are_the_kinds_carrier_paths"): "default",
    # 0041 round 10 stage 2 (S2-1): the body compared on the SOURCE identity — remapping imports on the capping path, and
    # the non-remapping control over BOTH paths by parameter
    ("test_0041_round10_notices.py", "test_S2_1_a_remapping_import_with_a_contradictory_body_is_refused_atomically"): "default",
    ("test_0041_round10_notices.py", "test_S2_1_the_same_contradiction_across_two_destination_users_is_refused"): "default",
    ("test_0041_round10_notices.py", "test_S2_1_control_remapping_twice_with_an_equal_body_is_not_refused"): "default",
    ("test_0041_round10_notices.py", "test_S2_1_control_the_non_remapping_paths_still_refuse"): "both",
    # 0041 round 10, the D1 reason closure at the import boundary (an own-store restore of an edited export)
    ("test_0041_round10_reasons.py", "test_the_closure_binds_the_import_boundary"): "restore",
    # 0041 round 10: `redacted` admitted at import only with an attesting notice (own-store restores of edited exports)
    ("test_0041_round10_redacted_reason.py", "test_import_admits_redacted_only_with_an_attesting_notice"): "restore",
    ("test_0041_import_contract.py", "test_an_invalid_notice_refuses_the_record_and_notice_unit_with_nothing_written"): "restore",
    ("test_0041_import_contract.py", "test_two_notices_under_one_source_identity_with_different_bodies_are_an_integrity_refusal"): "restore",
    ("test_0041_import_contract.py", "test_a_held_different_version_is_redacted_anyway_and_flagged"): "restore",
    ("test_0041_import_contract.py", "test_a_tombstone_without_a_notice_is_admitted_as_an_unattested_marker_and_flagged"): "restore",
    ("test_0041_import_contract.py", "test_an_import_may_not_repopulate_a_record_the_destination_already_redacted_without_a_notice"): "restore",
    ("test_0041_import_contract.py", "test_the_user_remap_moves_the_notice_with_the_record"): "default",
    ("test_0037_procedural.py", "run"): "default",
    ("test_0037_procedural.py",
     "test_default_import_refuses_procedural_records_on_any_signal"): "default",
    ("test_0037_procedural.py",
     "test_restore_round_trips_procedural_records_with_basis"): "restore",
    ("test_0037_procedural.py",
     "test_old_reader_refuses_a_procedural_export"): "default",
    # specs/0037 v23 §4e: the producer era — each test drives BOTH paths on
    # purpose (an older reader refusing a 12 file on the default path and
    # restore round-tripping the producer; a raw producer as the fourth
    # default-path signal and the restore consistency rule on the same file)
    ("test_0037_producer_stamp.py",
     "test_the_export_stamps_12_only_for_a_producer_bearing_store_and_old_readers_refuse"): "both",
    ("test_0037_producer_stamp.py",
     "test_a_producer_in_a_pre_12_envelope_is_stripped_and_a_raw_producer_is_a_refusal_signal"): "both",
    # specs/0037 v24.1 §6 V-INHERITANCE-AT-IMPORT (round-5 finding 3): the restore
    # path applies the store's inheritance rules before committing (both file orders),
    # and the existing-predecessor test drives BOTH paths on purpose — restore for a
    # mismatched producer, default for a declarative successor of a procedural record
    ("test_0037_producer_stamp.py",
     "test_restore_applies_the_inheritance_rules_the_store_applies_to_a_write"): "restore",
    ("test_0037_producer_stamp.py",
     "test_inheritance_is_checked_against_an_existing_destination_predecessor_on_both_paths"): "both",
    # specs/0037 v24.2 (round-6 finding 2): the DEFAULT path's lookup sees a refused
    # procedural predecessor, so its marker-stripped successors are refused by lineage
    ("test_0037_producer_stamp.py",
     "test_the_default_path_keeps_a_refused_predecessor_for_its_successors_inheritance"): "default",
    # specs/0037 v24.3 (round-7 finding 2): the lineage helper's signals and the validated
    # inherited producer — the default path for the registry-only and producer-only
    # lineages, restore for the changed-producer chain and the intact control
    ("test_0037_producer_stamp.py",
     "test_lineage_reads_every_import_signal_and_carries_validated_inheritance"): "both",
    # specs/0037 v24.4 (round-8 finding 1): the id-conflict regression drives BOTH
    # paths on purpose — restore for the stored-predecessor forms and the re-import
    # control, default for the duplicate-id forms; both file orders
    ("test_0037_producer_stamp.py",
     "test_conflicting_ids_are_resolved_before_lineage_in_both_orders"): "both",
    # specs/0037 v24.4 (research's pre-seal red team, A and C): the registry-only
    # predecessor by custody and the shadowed chain, default path, both orders
    ("test_0037_producer_stamp.py",
     "test_stored_and_incoming_custody_read_one_procedural_signal_set"): "default",
    # specs/0037 v24.5 (round-9 F1): the persisted-producer regression, restore path,
    # Q stored and incoming, both orders
    ("test_0037_producer_stamp.py",
     "test_a_persisted_producer_is_never_replaced_by_claimed_ancestry"): "restore",
    ("test_0037_producer_stamp.py", "run"): "both",          # that test's helper: default for the lineages, restore for the chains
    # specs/0042: the census runtime leg executes one DECLINING import per site — the helper
    # carries whatever path the entry names (restore for the agreement-record and the
    # restore-with-user refusals, default otherwise); the preflight conflict is a restore
    ("test_0042_sites.py", "_import"): "both",
    ("test_0042_sites.py", "_preflight_conflict"): "restore",
    # specs/0026 V6a: the accepted import decision table driven over
    # BOTH modes deliberately — default-recompute (forged discarded,
    # counted) and restore (verbatim-valid, foreign-opaque,
    # malformed-raises); plus the old-format row over the frozen
    # pre-agreement oracle
    ("test_0026_relay_lexicon.py",
     "test_agreement_import_recomputes"): "both",
    # specs/0011 §4c (E3): the portability cell of the contested sweep runs
    # restore=True DELIBERATELY — the test's subject is that a refusal record
    # is STORE-LOCAL (the imported pair arrives uncontested) even on the
    # maximum-fidelity path where every trust field round-trips verbatim;
    # showing it on the capping default path would prove less
    ("test_0011_entitlement.py",
     "test_contested_is_derived_and_total_over_readers"): "restore",
    # specs/0023 N8: the export→revoke→reimport sequence runs restore=True
    # DELIBERATELY — the test's subject is that the destination-standing cap
    # applies even when the operator asserts file-trust fidelity, because the
    # cap is about THIS STORE's standing state, not the file's trust (§3b)
    ("test_0023_inventory.py", "test_import_round_trip_requarantines"): "restore",
    # specs/0022 R18: the retired-episode round-trip imports into a FRESH
    # store on the default path — the test's subject is retirement state
    # surviving portability, and the default path is the one a host actually
    # runs; nothing here touches restore-only semantics
    ("test_0022_revoke_source.py", "test_retired_episode_round_trips"): "default",
    # specs/0029 §6a (corpus V08 cell a): the acceptance runner imports a
    # SECOND store's export into a fresh store on the DEFAULT path — the cell's
    # subject is the journal (one `created` event, none of the exporter's
    # events crossing), not trust fidelity; the default path is the one a
    # host runs, and the cap does not change the event kind
    ("corpus_runner.py", "v08_import"): "default",
    # specs/0019 U7: the forging matrix exercises BOTH paths deliberately
    # (default-path composition immunity; restore-path flag-keyed
    # eligibility grants — the documented §8 limit 6); the strip test is a
    # restore of a downgraded pre-v6 envelope
    ("test_0019_ungrounded.py", "test_import_strictbool_and_forging_matrix"): "both",
    ("test_0019_ungrounded.py", "test_pre_v6_envelope_strips_the_field"): "restore",
    # specs/0016 D2: the FORMAT-7 boundary tests — the ≤6 source_type strip
    # and the round-trip run on the restore path so the trust cap does not
    # mask the strip; the too-new refusal fires before any path choice
    ("test_0016_d2_deletion.py", "test_v6_import_drops_the_key_and_keeps_the_record"): "restore",
    ("test_0016_d2_deletion.py", "test_a_7_file_round_trips"): "restore",
    ("test_0016_d2_deletion.py", "test_a_newer_file_is_refused_by_the_version_gate"): "default",
    # specs/0001 §2d.2: the downgrade test exercises BOTH paths on purpose —
    # the DEFAULT import must flatten an ASSISTANT record to THIRD_PARTY
    # (authority 1 -> 0, the ratified 0005 cap: an imported file cannot
    # carry its own trust), and the RESTORE path must preserve the author
    # exactly, which is what makes the cap a deliberate choice rather than
    # a lossy round-trip. Asserting only one path would leave the other
    # free to be wrong.
    ("test_0001_generated_content_trust.py",
     "test_downgrade_export_fails_cleanly"): "both",
    ("test_0005_import_boundary.py", "test_default_import_caps_every_record"): "default",
    ("test_0005_import_boundary.py", "test_restore_preserves_trust_fields_exactly"): "restore",
    ("test_0005_import_boundary.py", "test_restore_of_a_finalized_output_export"): "restore",
    ("test_0005_import_boundary.py", "test_import_cap_never_raises"): "default",
    ("test_0005_import_boundary.py", "test_handwritten_export_cannot_evade_the_cap"): "default",
    ("test_0005_import_boundary.py", "test_restore_with_remap_is_refused"): "both",
    ("test_0005_import_boundary.py", "test_every_import_caps_by_default"): "default",
    ("test_0005_import_boundary.py", "test_imported_episode_renders_unverified"): "default",
    ("test_0005_import_boundary.py", "test_import_never_mutates_existing_rows"): "default",
    ("test_0005_import_boundary.py", "test_imported_source_id_does_not_bypass_the_remap_cap"): "default",
    ("test_0005_import_boundary.py", "test_own_store_reimport_refusal_names_restore"): "default",
    ("test_0005_import_boundary.py", "test_capped_count_is_destination_blind"): "default",
    ("test_0005_import_boundary.py", "test_imported_outcomes_cannot_promote_a_capped_edge"): "default",
    ("test_0005_import_boundary.py", "test_restore_rejects_non_bool_values"): "both",
    ("test_0005_import_boundary.py", "test_malformed_trust_fields_raise_never_normalize"): "default",
    ("test_0005_import_boundary.py", "test_tampered_own_export_refuses_with_warning"): "default",
    ("test_0005_import_boundary.py", "test_capped_projection_identity_matrix_equivalent_pairs_skip"): "default",
    ("test_0005_import_boundary.py", "test_capped_projection_identity_matrix_inequivalent_pairs_refuse"): "default",
    ("test_0005_import_boundary.py", "test_capped_projection_content_difference_refuses"): "default",
    ("test_0005_import_boundary.py", "test_mixed_path_refuses_where_the_cap_changes_a_field"): "both",
    ("test_0005_import_boundary.py", "test_fixed_point_records_are_path_invisible"): "both",
    ("test_0005_import_boundary.py", "test_restore_restore_uncapped_difference_refuses"): "restore",
    ("test_0005_import_boundary.py", "test_import_audit_payload_field_set_is_unchanged"): "default",
    ("test_0006_source_identity.py", "test_export_materialises_and_import_roundtrips_source_id_and_origin"): "default",
    ("test_0006_source_identity.py", "test_local_source_survives_a_roundtrip_into_the_same_store"): "restore",
    ("test_0006_source_identity.py", "test_a_v4_import_missing_origin_is_rejected"): "default",
    ("test_0006_source_identity.py", "test_a_foreign_origin_is_preserved_not_localised"): "default",
    ("test_0006_source_identity.py", "test_a_pre_v4_envelope_carrying_source_id_is_stripped"): "default",
    ("test_0009_import_migration.py", "test_import_preserves_the_outcome_chain"): "restore",
    ("test_0009_import_migration.py", "test_cross_user_import_remaps_supersedes_episode"): "default",
    ("test_0009_import_migration.py", "test_two_valid_chains_same_identity_refuses"): "default",
    ("test_0009_import_migration.py", "test_import_refuses_missing_or_foreign_edge"): "default",
    ("test_0009_import_migration.py", "test_same_id_different_author_refuses_whole_import"): "default",
    ("test_0009_import_migration.py", "test_same_id_different_outcome_refuses"): "default",
    ("test_0009_import_migration.py", "test_same_user_reimport_is_idempotent"): "restore",
    ("test_0009_import_migration.py", "test_import_extends_the_destination_head"): "default",
    ("test_0009_import_migration.py", "_src_from_prefix"): "default",
    ("test_0009_import_migration.py", "test_malformed_import_refuses_atomically"): "default",
    ("test_0009_import_migration.py", "test_competing_destination_root_refuses"): "default",
    ("test_0009_import_migration.py", "test_divergent_suffix_refuses"): "default",
    ("test_0009_import_migration.py", "test_import_racing_a_concurrent_append_never_branches"): "default",
    ("test_0009_import_migration.py", "test_legacy_portable_outcome_import"): "default",
    ("test_0009_import_migration.py", "test_v2_duplicate_identity_import_refuses"): "default",
    ("test_0009_import_migration.py", "test_v3_import_requires_explicit_judgment_time_known"): "default",
    ("test_0009_runtime_invariants.py", "test_v3_outcome_omitting_judgment_time_known_is_refused"): "default",
    ("test_0009_runtime_invariants.py", "test_non_root_with_unknown_time_is_refused"): "default",
    ("test_0010_consolidate_recovery.py", "test_export_then_import_round_trips_a_finalized_output"): "default",
    ("test_0010_consolidate_recovery.py", "test_import_refuses_claimed_input_shape"): "default",
    ("test_0010_consolidate_recovery.py", "test_malformed_lineage_shape_is_refused"): "default",
    ("test_0010_consolidate_recovery.py", "test_imported_operation_id_cannot_collide_with_a_live_local_op"): "default",
    ("test_0010_consolidate_recovery.py", "test_partial_then_retried_import_keeps_one_producer_group"): "default",
    # specs/0021 §7b / 0020 §4a-iii: the linkage tests — restore-path where
    # the fixture is the store's own export re-imported (the trust cap is
    # orthogonal to linkage reconstruction, which reads only non-trust
    # fields: id/note/invalidation_reason/identity); default-path where the
    # file is hand-crafted (the refusal cells, the v6 strip) or remapped
    # specs/0021 W15's durability cell: a restore, so the reconstructed
    # membership read back after reopen is the SAME evidence, not a capped
    # projection of it
    ("test_0021_maintain_scope.py", "test_import_contribution_primitive_membership_after_reopen"): "restore",
    ("test_0021_import_linkage.py", "test_import_persists_direct_and_transitive_rows_and_reads_back"): "restore",
    ("test_0021_import_linkage.py", "test_reimport_is_idempotent_rows_skip_counted_existing"): "restore",
    ("test_0021_import_linkage.py", "test_remapped_import_keys_rows_to_postremap_ids"): "default",
    ("test_0021_import_linkage.py", "test_conflicting_history_primitive_returns_destination_changed"): "restore",
    # specs/0041 (draft) — the executable transition table: the ruled quarantine
    # shape round-trips on the DEFAULT path (the cap is irrelevant to a
    # disposition carried by the disclosure); the prose-kind import is the
    # import-boundary closure's strict xfail, also on the default path
    ("test_0041_transition_table.py", "test_A_the_ruled_shape_survives_export_and_import"): "default",
    ("test_0041_transition_table.py", "test_B_an_import_carrying_a_prose_kind_is_refused"): "default",
    ("test_0021_import_linkage.py", "test_conflicting_history_reimport_refuses_whole_writing_nothing"): "restore",
    ("test_0021_import_linkage.py", "test_refusal_cell_leaves_destination_unchanged"): "default",
    ("test_0021_import_linkage.py", "test_legacy_file_without_field_takes_the_note_rule"): "restore",
    ("test_0021_import_linkage.py", "test_pre_v7_envelope_absorbed_by_id_is_stripped_never_trusted"): "default",
    ("test_0014_portability.py", "test_an_older_importer_refuses_a_v5_export"): "default",
    ("test_0014_portability.py", "test_v5_round_trip_is_lossless_and_v4_stays_accepted"): "default",
    ("test_0014_portability.py", "test_a_v5_output_without_an_index_is_the_legacy_shape"): "default",
    ("test_0014_portability.py", "test_an_explicit_null_index_is_malformed"): "default",
    ("test_0014_portability.py", "test_type_gates_reject_bool_string_negative"): "default",
    ("test_0014_portability.py", "test_an_index_on_a_plain_episode_is_fabricated_identity"): "default",
    ("test_0014_portability.py", "test_duplicate_output_index_within_an_imported_operation_is_rejected"): "default",
    ("test_0014_portability.py", "test_duplicate_output_index_across_sequential_imports_is_rejected"): "default",
    ("test_0014_portability.py", "test_repeated_remapped_import_resolves_the_indexed_output_idempotently"): "default",
    ("test_0014_portability.py", "test_every_projection_field_binds_source_identity"): "default",
    ("test_audit.py", "test_audit_records_every_operation_content_free"): "default",
    ("test_portability.py", "test_export_import_round_trip_is_lossless"): "restore",
    ("test_portability.py", "test_import_remaps_user_and_rejects_bad_files"): "default",
}


def test_import_memory_callsites_all_carry_a_disposition():
    tests_dir = pathlib.Path(__file__).resolve().parent
    found = set()
    for p in sorted(tests_dir.rglob("*.py")):
        tree = ast.parse(p.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for n in ast.walk(node):
                if isinstance(n, ast.Call):
                    f = n.func
                    name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
                    if name == "import_memory":
                        found.add((p.name, node.name))
    mapped = set(_CALLSITE_DISPOSITIONS)
    unmapped = found - mapped
    stale = mapped - found
    assert not unmapped, (f"import_memory call sites with NO recorded disposition "
                          f"(classify them in _CALLSITE_DISPOSITIONS): {sorted(unmapped)}")
    assert not stale, f"stale manifest entries (site gone): {sorted(stale)}"
    assert set(_CALLSITE_DISPOSITIONS.values()) <= {"default", "restore", "both"}


# -- shared hand-crafted record templates --------------------------------------------
_TEMPLATE_CACHE = {}


def _template(tmp_path):
    """A valid v5 header + one edge/one episode record template, derived from a
    REAL export (so required fields track the shipped model, never a guess).
    Trust fields on the template edge: author=user, disclosure=mentionable."""
    key = str(tmp_path)
    if key in _TEMPLATE_CACHE:
        hdr, base = _TEMPLATE_CACHE[key]
        return json.loads(json.dumps(hdr)), json.loads(json.dumps(base))
    mem = _mem(str(tmp_path / "__template.db"))
    mem.remember(U, "USER: I'm a chef.", date="2026-06-01")
    p = str(tmp_path / "__template.jsonl")
    export_memory(mem.store, U, p)
    ls = _lines(p)
    hdr = ls[0]
    edge = next(r for r in ls[1:] if r["record"] == "edge")
    episode = next(r for r in ls[1:] if r["record"] == "episode")
    mem.close()
    base = {"edge": edge, "episode": episode}
    _TEMPLATE_CACHE[key] = (hdr, base)
    return json.loads(json.dumps(hdr)), json.loads(json.dumps(base))


def _indexed_output(base, *, op):
    """A finalized-consolidation-output episode record: lineage (historical),
    an operation reference, and the store-assigned output index."""
    rec = json.loads(json.dumps(base["episode"]))
    rec.update({
        "id": f"ep-{op}",
        "kind": "interaction",          # the kind consolidation outputs actually carry; "consolidated" was an invented value the
                                        # product never writes, refused by 0041 tranche 1's import-boundary kind closure (2026-09-19)
        "lineage": ["hist:ep-src-1", "hist:ep-src-2"],
        "operation_id": op,
        "consolidation_output_index": 0,
    })
    return rec
