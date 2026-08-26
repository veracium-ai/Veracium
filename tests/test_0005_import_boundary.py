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
                  config=MemoryConfig(db_path=db, wiki_recompile_after_writes=0))


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
                 config=MemoryConfig(db_path=str(tmp_path / "bob.db"),
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
        "kind": "consolidated",
        "lineage": ["hist:ep-src-1", "hist:ep-src-2"],
        "operation_id": op,
        "consolidation_output_index": 0,
    })
    return rec
