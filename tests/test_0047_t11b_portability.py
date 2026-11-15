"""specs/0008 §6d–§6f, 0047 §4f, 0041 §11.6.6 and 0045 §4e/§4f (T11b, format era 14 extended): act and attestation
portability — confirmation and reply lines travel with their origin, derived identity and position; import decides
each act over the staged union by 0008 §6e's precedence (rules 0–4) on the canonical TREATED projection, validates
chronology over the merged history H (§6f), and the edge's grounding axis travels, checked in both modes.

PRODUCT tests through the real `export_memory` / `import_memory`, acts written by the real `confirm` / `reply` verbs.
Build note d54b768f + addendum 1 (7a820236; research's stage-1 read 48750ecc): the owner's R-D6 (the act remap
namespace) and R-M1 (legacy order in a trusted restore), research's M2–M4 and P1–P4. Each §6 row T11b makes
product-true is named on its cell. Every product mutant is in the scratch campaign
`.claude/skills/pre-seal/impl-review/0044/t11b_mutant_defs.py` (classified by specs/evidence/mutation_kinds.py).
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

from veracium import EvidenceAuthor, EvidenceContext, Memory, MemoryConfig
from veracium import portability as P
from veracium import redaction as R
from veracium import why as W
from veracium.attestation import DEFAULT_IMPORT, PREDICATE_VERSION
from veracium.store.base import DESTINATION_CHANGED
from veracium.store.data_migration import portable_uid
from veracium.store.sqlite import SqliteStore

U, V = "u1", "u2"
DIRECT = EvidenceContext.direct()


class _Fake:
    """A scripted distiller; every other role answers nothing."""

    def __init__(self):
        self.s = []

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role != "distill":
            return ""
        return json.dumps(self.s.pop(0) if self.s else {"triples": [], "episode": "x"})


def _mem(tmp_path, name):
    return Memory(llm=_Fake(), config=MemoryConfig(db_path=str(tmp_path / name), wiki_recompile_after_writes=0))


def _ok(fn, *a, **k):
    """A call the cell expects to SUCCEED: any raise is the property failing, read as an assertion."""
    try:
        return fn(*a, **k)
    except Exception as exc:                                       # noqa: BLE001 — the cell's subject
        raise AssertionError(f"expected success; raised {type(exc).__name__}: {exc}") from exc


def _refused(mem, f, match, **kw):
    """An import the cell expects REFUSED with a ValueError matching `match`; anything else fails by assertion."""
    try:
        mem.import_memory(f, **kw)
    except Exception as x:                                         # noqa: BLE001
        assert isinstance(x, ValueError) and re.search(match, str(x)), f"{type(x).__name__}: {x}"
        return str(x)
    raise AssertionError("the import was admitted")


def _fact(mem, rel="lives_in", obj="Paris", user=U):
    mem.llm.s.append({"triples": [{"subject": "user", "relation": rel, "object": obj, "volatility": "durable"}],
                      "episode": "said"})
    before = {e.id for e in mem.store.edges(user, active_only=False, include_quarantined=True)}
    _ok(mem.remember, user, f"I {rel} {obj}", author=EvidenceAuthor.USER, context=DIRECT)
    new = [e for e in mem.store.edges(user, active_only=False, include_quarantined=True) if e.id not in before]
    assert len(new) == 1
    return new[0].id


def _edge(mem, eid, user=U):
    return _one(e for e in mem.store.edges(user, active_only=False, include_quarantined=True) if e.id == eid)


def _q(mem, sql, args=()):
    return mem.store._conn.execute(sql, args).fetchall()


def _acts(mem, user=U):
    """Every act row of the user, both tables, every column — the bytes a no-op must leave unchanged."""
    return mem.store.act_rows(user)


def _export(mem, tmp_path, name, user=U):
    f = tmp_path / name
    _ok(mem.export_memory, user, f)
    return f


def _lines(f):
    return [json.loads(x) for x in pathlib.Path(f).read_text().splitlines() if x.strip()]


def _write(f, recs, name=None):
    out = f if name is None else f.with_name(name)
    out.write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    return out


def _edit(f, name, fn):
    """A copy of file `f` with `fn` applied to its record list (the header is recs[0])."""
    recs = _lines(f)
    recs = fn(recs) or recs
    return _write(f, recs, name)


def _act_lines(recs, kind=None):
    return [r for r in recs if r.get("record") in ("confirmation", "reply") and (kind is None or
                                                                                 r.get("kind", "confirm") == kind)]


def _history(tmp_path, name="a.db"):
    """A source store: e1 confirmed; e2 challenged, resolved, then confirmed (§6f's legitimate history)."""
    a = _mem(tmp_path, name)
    e1 = _fact(a)
    e2 = _fact(a, "works_as", "dentist")
    _ok(a.confirm, U, e1, date="2026-10-01")
    c = _ok(a.reply, U, e2, kind="challenge", text="not any more")
    _ok(a.reply, U, e2, kind="resolve", target=c["reply_id"])
    _ok(a.confirm, U, e2, date="2026-10-02")
    return a, e1, e2, c["reply_id"]


def _origins(mem, user=U):
    return sorted((r["table"], r["origin"]) for r in _acts(mem, user))


# ================================================================================ C11 and the export (D1–D2)
def test_c11_export_carries_confirmations_with_origin_and_derived_identity(tmp_path):
    """0008 C11 (replacing `test_export_excludes_confirmations`): the export carries every confirmation and reply WITH
    its origin; a local act's identity is DERIVED (this store's origin, its user, its row id: §6e v7), its position
    as recorded, its original request id its own correlation id; no row id, no internal key, no registry travels."""
    a, e1, e2, cid = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    recs = _lines(f)
    assert recs[0]["version"] == 14 and P.FORMAT_VERSION == 15  # specs/0031 v23.1: 14->15, the call-path era, conditionally stamped the same way
    acts = _act_lines(recs)
    held = {r["id"]: r for r in _acts(a)}
    assert len(acts) == len(held) == 4
    local = a.store.local_origin()
    for r in acts:
        assert r["origin"] == "local" and r["act_uid"][0] == local and r["act_uid"][1] == U
        h = held[r["act_uid"][2]]
        assert r["act_seq"] == h["act_seq"] and r["recorded_correlation_id"] == h["correlation_id"]
        assert set(r) == {"record"} | set(P._ACT_KEYS[r["record"]])
    resolve = _one(r for r in acts if r.get("kind") == "resolve")
    assert resolve["target_uid"] == [local, U, cid]
    raw = f.read_text()
    assert "#act:" not in raw and "request_registry" not in raw
    assert not _q(a, "SELECT 1 FROM confirmations WHERE origin_store IS NOT NULL")      # export stays read-only


def test_g13_the_axis_travels_with_its_version_and_a_second_hop_keeps_it(tmp_path):
    """0045 INV-G13 (travel): the edge line carries `att`/`src`/`attv`; a trusted restore keeps them as recorded, and a
    second hop keeps `attv` (the mutant: drop `attv` on export, a second hop relabels)."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    held = {e.id: e for e in a.store.edges(U, active_only=False, include_quarantined=True)}
    for r in _lines(f):
        if r.get("record") == "edge":
            assert (r.get("att"), r.get("attv"), r.get("src")) == (held[r["id"]].att, held[r["id"]].attv,
                                                                   held[r["id"]].src)
            assert r["attv"] == PREDICATE_VERSION
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    g = _export(b, tmp_path, "b.jsonl")
    c = _mem(tmp_path, "c.db")
    _ok(c.import_memory, g, restore=True)
    for e in c.store.edges(U, active_only=False, include_quarantined=True):
        assert (e.att, e.attv, e.src) == (held[e.id].att, held[e.id].attv, held[e.id].src)


# ======================================================================= the origin matrix (INV-R21, INV-Q5)
def test_r21_restore_maps_local_to_restored_and_counts_toward_grounding(tmp_path):
    """INV-R21 / INV-Q5: a trusted restore writes a recorded `local` act `restored` (proof: `g(e) = confirmed`); a
    default import writes every act `imported` (testimony, not counted). Mutants: restore writes `local`; default
    keeps the file's origin; imported confirmations counted."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    r = _ok(b.import_memory, f, restore=True)
    assert (r["confirmations"], r["replies"], r["acts_existing"]) == (2, 2, 0)
    assert {o for _t, o in _origins(b)} == {"restored"}
    assert b.store.challenge_snapshot(U).inspect(_edge(b, e1)).grounding == "confirmed"
    d = _mem(tmp_path, "d.db")
    _ok(d.import_memory, f)
    assert {o for _t, o in _origins(d)} == {"imported"}
    assert d.store.challenge_snapshot(U).inspect(_edge(d, e1)).grounding == "not_attested"
    assert not _q(b, "SELECT 1 FROM request_registry") and not _q(d, "SELECT 1 FROM request_registry")   # INV-Q4′


def test_q5_the_testimony_chain_reads_imported_through_a_restore_with_a_legacy_row(tmp_path):
    """INV-Q5 (0008 §3a's chain): local → export → default import → export → trusted restore still reads `imported`;
    the chain carries a legacy confirmation (an UNKNOWN position, research's P4), which travels as unknown, never
    synthesised."""
    a = _mem(tmp_path, "a.db")
    e1 = _fact(a)
    _ok(a.confirm, U, e1, date="2026-10-01")
    _q(a, "UPDATE confirmations SET act_seq=NULL")             # recorded before the column existed (§6f)
    a.store._conn.commit()
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, _export(a, tmp_path, "a.jsonl"))
    c = _mem(tmp_path, "c.db")
    _ok(c.import_memory, _export(b, tmp_path, "b.jsonl"), restore=True)
    rows = _acts(c)
    assert [(r["origin"], r["act_seq"]) for r in rows] == [("imported", None)]


# =================================================================== precedence: rules 0–4 (INV-I1..I3, R16)
def test_i1_repeat_import_is_a_noop_in_both_modes_with_no_request_id(tmp_path):
    """INV-I1: the same file twice, either mode, leaves every act row byte-identical after the first; controls: an act
    recorded with NO request id (the internal key is never read as one) and a generated `auto-` id. Mutants: compare
    full rows; drop the exact-replay rule; read the internal key as the original id."""
    a, e1, e2, _c = _history(tmp_path)
    f = _edit(_export(a, tmp_path, "a.jsonl"), "f.jsonl",
              lambda recs: [dict(r, recorded_correlation_id=None) if r.get("kind") == "challenge" else r for r in recs])
    for mode in (False, True):
        m = _mem(tmp_path, f"m{mode}.db")
        _ok(m.import_memory, f, restore=mode)
        before = _acts(m)
        r = _ok(m.import_memory, f, restore=mode)
        assert (r["confirmations"], r["replies"], r["acts_existing"]) == (0, 0, 4)
        assert _acts(m) == before
        assert any(x["recorded_correlation_id"] is None for x in before)
        assert any((x["recorded_correlation_id"] or "").startswith("auto-") for x in before)


def test_rule0_a_default_file_claiming_this_stores_origin_is_refused_and_a_restore_admits_it(tmp_path):
    """0008 §6e rule 0 / INV-Q9: a DEFAULT file carrying this store's origin is refused whole (it could order an act
    before a local challenge); a trusted restore may carry it. Read on the act as ADMITTED (R-D6)."""
    a, e1, e2, _c = _history(tmp_path)
    d = _mem(tmp_path, "d.db")
    own = d.store.local_origin()
    f = _edit(_export(a, tmp_path, "a.jsonl"), "forged.jsonl",
              lambda recs: [dict(r, act_uid=[own] + r["act_uid"][1:], **({} if r["record"] == "confirmation" else {
                  "target_uid": None if r["target_uid"] is None else [own] + r["target_uid"][1:]}))
                  if r in _act_lines(recs) else r for r in recs])
    _refused(d, f, "THIS store's origin")
    assert not d.store.edges(U, active_only=False, include_quarantined=True)          # whole unit, nothing written
    r = _ok(d.import_memory, f, restore=True)
    assert r["confirmations"] == 2 and {o for _t, o in _origins(d)} == {"restored"}


_CONFLICT = "different projection"
@pytest.mark.parametrize("field,value,match", [
    ("actor", "host", _CONFLICT), ("confirmed_at", "2026-10-09T00:00:00+00:00", _CONFLICT), ("act_seq", 77, _CONFLICT),
    ("recorded_correlation_id", "other-id", _CONFLICT), ("request_digest", "0" * 64, _CONFLICT),
    ("edge_id", "SWAP", _CONFLICT),
    # `ConfirmationCallPath` has three values since specs/0031 §4f (host_api, mcp_direct, adapter_direct); "mcp" is
    # outside the enum, so it keeps the closed-shape refusal (0031 v23.2); a VALID changed call path is the next cell
    ("call_path", "mcp", "closed shape"),
])
def test_i2_a_structural_change_under_a_held_uid_refuses_the_whole_unit(tmp_path, field, value, match):
    """INV-I2 / IO-II-4 ("validate the full projection, including actor/call-path"): a confirmation re-arriving under
    its held `act_uid` with ANY projected field changed is a conflicting replay — the whole unit refused, nothing
    written. Mutant: the projection by uid only."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    before = _acts(b)

    def change(recs):
        k = _one(r for r in recs if r.get("record") == "confirmation" and r["edge_id"] == e1)
        k[field] = e2 if value == "SWAP" else value
    _refused(b, _edit(f, "g.jsonl", change), match, restore=True)
    assert _acts(b) == before


def test_i2_a_held_confirmation_re_arriving_with_an_agent_call_path_is_a_different_projection(tmp_path):
    """specs/0031 v23.2 (research's note on I2): a held-uid confirmation that re-arrives in a FORMAT-15 file with its
    `call_path` changed from `host_api` to `mcp_direct` is a valid value under its era, so it is a conflicting replay
    (`different projection`), not a shape refusal and not an era refusal; the whole unit refused, nothing written."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    before = _acts(b)

    def change(recs):
        recs[0]["version"] = 15
        k = _one(r for r in recs if r.get("record") == "confirmation" and r["edge_id"] == e1)
        k["call_path"] = "mcp_direct"
    _refused(b, _edit(f, "g15.jsonl", change), _CONFLICT, restore=True)
    assert _acts(b) == before


def test_i6_two_differing_copies_in_one_unit_refuse_and_two_equal_copies_are_one_act(tmp_path):
    """INV-I6 (the staged union): one `act_uid` twice in one file — equal: one act; different: the whole unit refused
    (rule 2 inside the unit; the wire carries no row id, so this is §6e's 'file row id naming two rows')."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    twice = _edit(f, "twice.jsonl", lambda recs: recs + [_seq(recs, "challenge")])
    b = _mem(tmp_path, "b.db")
    r = _ok(b.import_memory, twice, restore=True)
    assert r["replies"] == 2
    diff = _edit(f, "diff.jsonl", lambda recs: recs + [dict(_seq(recs, "challenge"), text="changed")])
    c = _mem(tmp_path, "c.db")
    _refused(c, diff, "appears twice")
    assert not _acts(c)


def test_r16_a_new_act_over_a_held_edge_is_refused_in_default_and_rule1_runs_first(tmp_path):
    """INV-R16 / 0008 §6e rule 3: a NEW act over an edge the destination already held, in a default import, refuses
    the whole file (the reviewer's mutant: trust every incoming side-row act). Rule 1 before rule 3: the unchanged file
    again is a no-op (INV-I3's control); and a replay grants NOTHING new on its target."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    bare = _edit(f, "bare.jsonl", lambda recs: [r for r in recs if r not in _act_lines(recs)])
    d = _mem(tmp_path, "d.db")
    _ok(d.import_memory, bare)
    _refused(d, f, "untrusted file cannot act as the subject")
    assert not _acts(d)
    d2 = _mem(tmp_path, "d2.db")
    _ok(d2.import_memory, f)
    assert _ok(d2.import_memory, f)["acts_existing"] == 4
    _ok(a.reply, U, e1, kind="context", text="since 2020")
    _refused(d2, _export(a, tmp_path, "a2.jsonl"), "untrusted file cannot act as the subject")


def test_r11_an_act_whose_edge_is_nowhere_refuses_the_whole_file_before_any_write(tmp_path):
    """INV-R11: an act naming an edge in neither the file nor the destination refuses the whole file, nothing written."""
    a, e1, e2, _c = _history(tmp_path)
    f = _edit(_export(a, tmp_path, "a.jsonl"), "orphan.jsonl",
              lambda recs: recs + [dict(_seq(recs, "challenge"), edge_id="e-nowhere",
                                        act_uid=[*_seq(recs, "challenge")["act_uid"][:2], "r-orphan"])])
    b = _mem(tmp_path, "b.db")
    _refused(b, f, "neither the file nor this store")
    assert not b.store.edges(U, active_only=False, include_quarantined=True) and not _acts(b)


# ==================================================================== the act shape (D13, P2) and identity
@pytest.mark.parametrize("mutate", [
    pytest.param(lambda r: r.pop("act_uid") and None, id="no-act-uid"),
    pytest.param(lambda r: r.update(act_uid=["x", "u"]), id="short-uid"),
    pytest.param(lambda r: r.update(act_seq=0), id="seq-zero"),
    pytest.param(lambda r: r.update(origin="mine"), id="origin"),
    pytest.param(lambda r: r.update(actor="assistant"), id="actor"),
    pytest.param(lambda r: r.update(kind="vote"), id="kind"),
    pytest.param(lambda r: r.update(recorded_correlation_id="#act:0123"), id="internal-key-as-original"),
    pytest.param(lambda r: r.update(request_digest="xyz"), id="digest"),
    pytest.param(lambda r: r.update(text=f"before {R.MARKER} after"), id="marker-mid-text"),
    pytest.param(lambda r: r.update(text="ok\ud800"), id="lone-surrogate"),
    pytest.param(lambda r: r.update(extra=1), id="extra-key"),
    pytest.param(lambda r: r.update(written_at="2026-10-01T10:00:00"), id="naive-time"),
])
def test_d13_an_act_outside_its_closed_shape_refuses_the_whole_file(tmp_path, mutate):
    """Build note D13 / IO-II-4 ("closed kind/shape rules … origin and UID grammar"; research's P2): a reply outside its
    closed shape refuses the whole file before any write — an absent `act_uid` (a store never mints one for an act it
    did not originate), an internal key offered as the original request id, a marker embedded mid-text on an
    unredacted target (add_reply's predicate), a naive time."""
    a, e1, e2, _c = _history(tmp_path)
    f = _edit(_export(a, tmp_path, "a.jsonl"), "bad.jsonl", lambda recs: mutate(_seq(recs, "challenge")))
    b = _mem(tmp_path, "b.db")
    _refused(b, f, "closed shape|timezone-aware")
    assert not b.store.edges(U, active_only=False, include_quarantined=True)


def test_q4prime_an_imported_act_writes_no_registry_row_and_never_takes_the_hosts_id(tmp_path):
    """INV-Q4′: an imported act's own key is `#act:` + its admitted identity's canonical hash (outside the caller
    grammar), it writes no registry row, and keeps the ORIGINAL id as evidence — so a later local confirm with the
    file's id as its caller id is ADMITTED (the verdict's sequence). INV-Q8: the key is a canonical-array hash, never a
    separator join (two separator-colliding identities give two keys)."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    for r in _acts(b):
        assert r["correlation_id"] == "#act:" + portable_uid(r["origin_store"], r["origin_user"], r["origin_act_id"])[:32]
    assert not _q(b, "SELECT 1 FROM request_registry")
    file_id = _one(r["recorded_correlation_id"] for r in _acts(b) if r["table"] == "confirmations")
    e3 = _fact(b, "likes", "tea")
    _ok(b.confirm, U, e3, correlation_id=file_id)
    assert portable_uid("a:b", "c", "d") != portable_uid("a", "b:c", "d")


def test_q9_the_counter_is_never_reset_by_erasure_and_never_moved_by_import(tmp_path):
    """INV-Q9 / IO-II-4 ("preserve the store-wide counter across erasure"): an import takes no position from this
    store's counter; after `forget`, a recreated user's act takes a position past every exported one."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    seqs = [r["act_seq"] for r in _act_lines(_lines(f))]
    assert seqs, "the export carries the acts"
    top = max(seqs)
    b = _mem(tmp_path, "b.db")
    seq0 = _q(b, "SELECT next_seq FROM act_counter")[0][0]
    _ok(b.import_memory, f, restore=True)
    assert _q(b, "SELECT next_seq FROM act_counter")[0][0] == seq0
    _ok(a.forget, U)
    e = _fact(a)
    _ok(a.confirm, U, e)
    assert [r["act_seq"] for r in _acts(a)] == [top + 1]


def test_p3_a_forged_identity_held_for_another_user_refuses_and_writes_nothing(tmp_path):
    """Research's P3 (no store-wide act UNIQUE: the refusal is the preflight's): an `act_uid` this store holds for user
    U, arriving in a file for user V, refuses the whole unit; the row count is unchanged."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    n = len(_q(b, "SELECT id FROM confirmations")) + len(_q(b, "SELECT id FROM replies"))
    forged = _edit(f, "v.jsonl", lambda recs: [dict(r, user_id=V) if r.get("kind") == "veracium-export" else r
                                              for r in recs])
    _refused(b, forged, "for another user")
    assert len(_q(b, "SELECT id FROM confirmations")) + len(_q(b, "SELECT id FROM replies")) == n


# ========================================================================= the remap namespace (R-D6, P1)
def test_rd6_a_remapped_copy_duplicates_as_its_edges_do_and_keeps_its_order(tmp_path):
    """The owner's R-D6: under a cross-user remap each act moves into this import's namespace — so one file twice into
    one user, and into two users, each ADMIT (acts duplicate exactly when their edges do), the internal key hashes the
    ADMITTED identity (P1: else the second copy hits UNIQUE(user_id, correlation_id)), a copy keeps its own order and its
    resolve's target, and rule 0 is read on the admitted act (a same-store copy of a user is testimony, not refused)."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    for tgt in (V, V, "u3"):
        r = _ok(a.import_memory, f, user_id=tgt)
        assert (r["confirmations"], r["replies"]) == (2, 2)
    rows = _acts(a, V)
    assert len(rows) == 8 and {r["origin"] for r in rows} == {"imported"}
    spaces = {r["origin_store"] for r in rows}
    assert len(spaces) == 2 and all(s.startswith("remap:") for s in spaces)
    for s in spaces:
        mine = [r for r in rows if r["origin_store"] == s]
        res = _one(r for r in mine if r.get("kind") == "resolve")
        ch = _one(r for r in mine if r.get("kind") == "challenge")
        assert res["target"] == ch["id"] and res["edge_id"] == ch["edge_id"] and ch["act_seq"] < res["act_seq"]


# =============================================================================== times (D3–D5, Q13, M3)
def test_d4_a_z_and_an_offset_copy_of_one_act_are_one_act(tmp_path):
    """Build note D4–D5 (IO-II-4 "normalized dates"; research's Q13): `confirmed_at` and `written_at` are re-rendered as
    canonical UTC before comparison and storage, so 'Z' and '+02:00' copies of an act are an exact replay; the stored
    text is the local writers' form. Mutant: compare the bytes."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    before = _acts(b)

    def shift(recs):
        for r in _act_lines(recs):
            if r["record"] == "confirmation":
                r["confirmed_at"] = r["confirmed_at"].replace("+00:00", "Z")
            else:
                from datetime import datetime, timedelta, timezone
                t = datetime.fromisoformat(r["written_at"]).astimezone(timezone(timedelta(hours=2)))
                r["written_at"] = t.isoformat()
    r = _ok(b.import_memory, _edit(f, "z.jsonl", shift), restore=True)
    assert r["acts_existing"] == 4 and _acts(b) == before
    c = _mem(tmp_path, "c.db")
    _ok(c.import_memory, _edit(f, "z2.jsonl", shift), restore=True)
    assert sorted(x["written_at"] for x in _acts(c) if x["table"] == "replies") == \
        sorted(x["written_at"] for x in before if x["table"] == "replies")


def test_m3_a_future_dated_imported_challenge_never_outranks_a_later_local_one(tmp_path):
    """Research's M3: an arriving `written_at` later than the import's clock read is clamped to it, in both modes, so a
    file cannot date a challenge ahead of every later local one (the latest challenge's text enters the recall unit).
    Mutant: no clamp."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    _ok(a.reply, U, e, kind="challenge", text="from the file")
    f = _edit(_export(a, tmp_path, "a.jsonl"), "future.jsonl",
              lambda recs: [dict(r, written_at="9999-01-01T00:00:00+00:00") if r.get("kind") == "challenge" else r
                            for r in recs])
    for mode in (True, False):
        b = _mem(tmp_path, f"b{mode}.db")
        _ok(b.import_memory, f, restore=mode)
        assert all(not x["written_at"].startswith("9999") for x in _acts(b))
        if mode:
            _ok(b.reply, U, e, kind="challenge", text="the local one")
            assert b.store.challenge_snapshot(U).inspect(_edge(b, e)).latest_challenge == "the local one"


# ============================================================================= chronology over H (§6f)
def _seq(recs, kind, edge=None):
    return _one(r for r in _act_lines(recs) if r.get("kind", "confirm") == kind and (edge is None or r["edge_id"] == edge))


def _one(rows):
    """The first row, ASSERTED present: a cell whose subject went missing fails by assertion, never by StopIteration."""
    rows = list(rows)
    assert rows, "the cell's subject row is absent"
    return rows[0]


def test_q10_a_confirmation_under_an_open_challenge_refuses_in_one_file_and_across_two(tmp_path):
    """INV-Q10 / INV-R23 (round 3's one-file witness): a history whose confirmation was made while a same-origin
    challenge was open (no resolve between) refuses, in one file and as two successive files. Mutants: check
    confirmations before installing the unit's challenges; judge only incoming confirmations. Its second half is also
    0008's INV-I3: the held challenge REPLAYS in the second file's unit, and the new confirmation beside it is still
    judged by §6f's chronology (research's T12 S2-M1: mutant I3-b skips the chronology for a unit holding a replay)."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    no_resolve = _edit(f, "nr.jsonl", lambda recs: [r for r in recs if r.get("kind") != "resolve"])
    b = _mem(tmp_path, "b.db")
    _refused(b, no_resolve, "made under challenge")
    assert not _acts(b)
    ch_only = _edit(f, "ch.jsonl", lambda recs: [r for r in recs if r.get("record") != "confirmation"
                                                 and r.get("kind") != "resolve"])
    c = _mem(tmp_path, "c.db")
    _ok(c.import_memory, ch_only, restore=True)
    _refused(c, no_resolve, "made under challenge", restore=True)


def test_q10_a_resolved_history_is_admitted_with_the_challenge_held_and_the_rest_arriving(tmp_path):
    """INV-R23 and INV-Q10 (round 3's valid resolved-history restore): the destination holds the challenge; the file brings the
    resolve and the confirmation; admitted. Mutant: judge held challenges before applying the unit's resolves."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    ch_only = _edit(f, "ch.jsonl", lambda recs: [r for r in recs if r.get("record") != "confirmation"
                                                 and r.get("kind") != "resolve"])
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, ch_only, restore=True)
    r = _ok(b.import_memory, f, restore=True)
    assert (r["confirmations"], r["replies"], r["acts_existing"]) == (2, 1, 1)


def test_q10_a_confirmation_before_the_challenge_is_consistent_and_an_incoming_challenge_meets_a_held_one(tmp_path):
    """INV-Q10 at §6f's first row: ordered k < c is consistent (confirm, then challenge: admitted). And an INCOMING challenge is
    judged against a HELD confirmation: a forged earlier challenge (c < k, unresolved) arriving over a held
    confirmation refuses. Mutant: judge only incoming confirmations."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    _ok(a.confirm, U, e, date="2026-10-01")
    _ok(a.reply, U, e, kind="challenge", text="changed my mind")
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    later = _edit(f, "later.jsonl", lambda recs: [dict(r, act_seq=5) if r.get("record") == "confirmation" else r
                                                  for r in recs])                 # k at 5, the challenge at 2: c < k
    conf_only = _edit(later, "k.jsonl", lambda recs: [r for r in recs if r.get("record") != "reply"])
    c = _mem(tmp_path, "c.db")
    _ok(c.import_memory, conf_only, restore=True)
    _refused(c, later, "made under challenge", restore=True)
    assert [r["table"] for r in _acts(c)] == ["confirmations"]


def test_q10_incomparable_or_unknown_positions_refuse_unless_the_challenge_is_resolved(tmp_path):
    """§6f's 'not ordered' rows (INV-Q10, INV-R23; IO-II-4: accepted only in the explicitly resolved-history case): a
    confirmation of another origin against an UNRESOLVED challenge refuses; against a RESOLVED one it is admitted.
    Mutant: an incomparable position read as earliest."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    _ok(a.reply, U, e, kind="challenge", text="wrong")
    f = _export(a, tmp_path, "a.jsonl")
    ch = _seq(_lines(f), "challenge")
    k = {"record": "confirmation", "act_uid": ["other-store", U, "c-x"], "act_seq": 9, "edge_id": e,
         "confirmed_at": "2026-10-03T00:00:00+00:00", "actor": "user", "call_path": "host_api",
         "recorded_correlation_id": "k1", "request_digest": "a" * 64, "origin": "local"}
    unresolved = _edit(f, "u.jsonl", lambda recs: recs + [k])
    _refused(_mem(tmp_path, "b.db"), unresolved, "cannot be ordered")
    res = {"record": "reply", "act_uid": ch["act_uid"][:2] + ["r-res"], "act_seq": ch["act_seq"] + 1, "edge_id": e,
           "kind": "resolve", "target_uid": ch["act_uid"], "text": None, "actor": "user",
           "recorded_correlation_id": "r1", "request_digest": "b" * 64, "origin": "local",
           "written_at": ch["written_at"]}
    _ok(_mem(tmp_path, "c.db").import_memory, _edit(f, "r.jsonl", lambda recs: recs + [k, res]), restore=True)


def test_rm1_a_legacy_position_restores_first_among_proof_acts_and_refuses_whole_in_default(tmp_path):
    """The owner's R-M1 (INV-Q10, INV-R23): in a TRUSTED RESTORE an unknown-position act of origin O precedes every known-position act of
    O, between PROOF acts — so a store's own backup holding a legacy confirmation and a LATER open challenge restores
    (O17). Testimony stays incomparable (a relayed `imported` legacy row refuses), and a DEFAULT import refuses WHOLE,
    at §6f L724's width: no edge is written. Mutants: R-M1 dropped; R-M1 in default mode; R-M1 for testimony."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    _ok(a.confirm, U, e, date="2026-10-01")
    _q(a, "UPDATE confirmations SET act_seq=NULL")
    a.store._conn.commit()
    _ok(a.reply, U, e, kind="challenge", text="later, I disagree")
    f = _export(a, tmp_path, "a.jsonl")
    r = _ok(_mem(tmp_path, "b.db").import_memory, f, restore=True)
    assert (r["confirmations"], r["replies"]) == (1, 1)
    d = _mem(tmp_path, "d.db")
    _refused(d, f, "cannot be ordered")
    assert not d.store.edges(U, active_only=False, include_quarantined=True)
    testimony = _edit(f, "t.jsonl", lambda recs: [dict(r, origin="imported") if r.get("record") == "confirmation"
                                                  else r for r in recs])
    _refused(_mem(tmp_path, "c.db"), testimony, "cannot be ordered", restore=True)


def test_q10_ties_a_second_resolve_and_a_resolve_before_its_challenge_each_refuse(tmp_path):
    """INV-Q10 at §6f: two different acts at one position (a forged or corrupted history); a challenge resolved twice in H; a
    resolve ordered before its own challenge — each refuses the unit. Mutant: a tie treated as ordered."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    recs = _lines(f)
    ch, res = _seq(recs, "challenge"), _seq(recs, "resolve")
    tie = dict(ch, act_uid=ch["act_uid"][:2] + ["r-tie"], text="another")
    _refused(_mem(tmp_path, "b.db"), _edit(f, "tie.jsonl", lambda rs: rs + [tie]), "one position", restore=True)
    second = dict(res, act_uid=res["act_uid"][:2] + ["r-res2"], act_seq=res["act_seq"] + 50)
    _refused(_mem(tmp_path, "c.db"), _edit(f, "two.jsonl", lambda rs: rs + [second]), "more than once", restore=True)
    before = _edit(f, "bef.jsonl", lambda rs: [dict(r, act_seq=30) if r.get("kind") == "resolve" else
                                               (dict(r, act_seq=40) if r.get("kind") == "challenge" else r) for r in rs])
    _refused(_mem(tmp_path, "d.db"), before, "before its own challenge", restore=True)      # unique positions: no tie


def test_i6_row_order_is_immaterial(tmp_path):
    """INV-I6: the result is the same under every row order (H is a set). Mutant: process rows in file order."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    rev = _edit(f, "rev.jsonl", lambda recs: [recs[0]] + list(reversed(recs[1:])))
    b, c = _mem(tmp_path, "b.db"), _mem(tmp_path, "c.db")
    _ok(b.import_memory, f, restore=True)
    _ok(c.import_memory, rev, restore=True)
    strip = lambda rows: sorted((r["table"], r["origin_act_id"], r["act_seq"], r["origin"]) for r in rows)  # noqa: E731
    assert strip(_acts(b)) == strip(_acts(c))


# =================================================================== coverage (RR3, RR6, RR8, RR9, I4, I7)
def _redacted_history(tmp_path):
    """A source whose edge carries a confirmation and a reply, then redacted (0041 §11.6: both content carriers treated,
    the attestation names them)."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    _ok(a.confirm, U, e, date="2026-10-01")
    _ok(a.reply, U, e, kind="context", text="the street was Rue Cler")
    clean = _export(a, tmp_path, "clean.jsonl")
    _ok(a.redact, U, edge_id=e, reason="subject_request")
    return a, e, clean, _export(a, tmp_path, "redacted.jsonl")


def test_rr3_a_redacted_round_trip_is_admitted_and_a_marker_reply_without_a_notice_refuses(tmp_path):
    """INV-RR3: a marker reply is admitted iff its unit attests `replies.text` for its edge (the redacted round trip,
    both modes); a marker reply with no notice is a fabricated tombstone — refused whole. Mutants: refuse every marker
    reply; admit one with no notice."""
    a, e, clean, red = _redacted_history(tmp_path)
    for mode in (True, False):
        b = _mem(tmp_path, f"b{mode}.db")
        _ok(b.import_memory, red, restore=mode)
        reply = _one(r for r in _acts(b) if r["table"] == "replies")
        assert reply["text"] == R.MARKER and reply["request_digest"] == R.MARKER
    fake = _edit(clean, "fake.jsonl", lambda recs: [dict(r, text=R.MARKER) if r.get("record") == "reply" else r
                                                    for r in recs])
    _refused(_mem(tmp_path, "c.db"), fake, "fabricated tombstone")


def test_rr6_rr9_an_old_or_partial_notice_refuses_an_arriving_act(tmp_path):
    """INV-RR6 (a notice that attests none of a row's content carriers: a pre-feature notice) and INV-RR9 (one that
    attests some but not all): coverage is all or nothing per row, and a foreign notice is never enlarged (0008's
    INV-I5's coverage clause). Mutants:
    an absent field read as permission; partial coverage admitted."""
    a, e, clean, red = _redacted_history(tmp_path)

    def fields(keep):
        def fn(recs):
            for r in recs:
                if r.get("record") == "redaction":
                    r["fields"] = [x for x in r["fields"] if keep(x)]
                if r.get("record") == "reply":
                    r["text"], r["request_digest"] = "the street was Rue Cler", "c" * 64
                if r.get("record") == "confirmation":
                    r["request_digest"] = "d" * 64
        return fn
    old = _edit(red, "old.jsonl", fields(lambda x: not x.startswith(("replies.", "confirmations."))))
    _refused(_mem(tmp_path, "b.db"), old, "coverage is all or nothing|fabricated|untreated|shows", restore=True)
    part = _edit(red, "part.jsonl", fields(lambda x: x != "replies.request_digest"))
    _refused(_mem(tmp_path, "c.db"), part, "coverage is all or nothing|fabricated|untreated|shows", restore=True)


def test_rr8_an_untreated_act_under_a_covering_notice_is_written_treated_and_reimports_as_a_noop(tmp_path):
    """INV-RR8 / INV-I4: an ordinary reply arriving onto its redacted target under a notice that covers it is written
    with BOTH `text` and `request_digest` treated, and the same file imported again is a no-op (the treated held row
    and the untreated arrival are one act under the coverage). Mutants: treat text only; compare untreated with
    treated."""
    a, e, clean, red = _redacted_history(tmp_path)
    untreated = {r["act_uid"][2]: r for r in _act_lines(_lines(clean))}
    mixed = _edit(red, "mixed.jsonl", lambda recs: [untreated[r["act_uid"][2]] if r in _act_lines(recs) else r
                                                    for r in recs])
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, mixed, restore=True)
    for r in _acts(b):
        assert r["request_digest"] == R.MARKER and (r["table"] == "confirmations" or r["text"] == R.MARKER)
    before = _acts(b)
    assert _ok(b.import_memory, mixed, restore=True)["acts_existing"] == 2 and _acts(b) == before


def test_rr8_rule4_writes_a_covered_act_treated_even_where_its_notice_stays_pending(tmp_path):
    """INV-RR8 and 0008's INV-I4 at 0008 §6e rule 4 ("written treated where the coverage attests its carriers"), apart from any notice's
    application: a trusted restore brings untreated acts onto a HELD, unredacted edge with their source's notice but no
    copy of the edge, so the notice stays PENDING (`record-not-in-file`) and treats nothing — yet the coverage counts it
    (every notice, whatever its state), so the acts are written with BOTH carriers treated. Mutant: treat the text and
    keep the digest (the cells where a notice is applied re-treat the row and hide it)."""
    a, e, clean, red = _redacted_history(tmp_path)
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, _edit(clean, "edges.jsonl", lambda recs: [r for r in recs if r not in _act_lines(recs)]),
        restore=True)
    untreated = {r["act_uid"][2]: r for r in _act_lines(_lines(clean))}
    unit = _edit(red, "unit.jsonl", lambda recs: [untreated[r["act_uid"][2]] if r in _act_lines(recs) else r
                                                  for r in recs if r.get("record") != "edge"])
    r = _ok(b.import_memory, unit, restore=True)
    assert [x[2] for x in r["notices_not_applied"]] == ["record-not-in-file"]
    assert _edge(b, e).object != R.MARKER                      # the held record is untouched: the notice is pending
    rows = _acts(b)
    assert len(rows) == 2
    for x in rows:
        assert x["request_digest"] == R.MARKER and (x["table"] == "confirmations" or x["text"] == R.MARKER)


def test_i7_a_default_replay_of_a_treated_copy_leaves_held_acts_byte_equal_until_confirm_notice(tmp_path):
    """INV-I7 / INV-RR10 (default mode): a held untreated act meeting its treated copy with the covering notice is an
    exact replay — every held act byte-equal, the notice PENDING; `confirm_notice` then treats the held acts (this
    store's total treatment). INV-I4's restore half: the restore applies the notice and the acts are treated. Mutant:
    the authorized transition in default mode."""
    a, e, clean, red = _redacted_history(tmp_path)
    d = _mem(tmp_path, "d.db")
    _ok(d.import_memory, clean)
    before = _acts(d)
    _ok(d.import_memory, red)
    assert _acts(d) == before
    pend = d.pending_notices(U)
    assert len(pend) == 1
    _ok(d.confirm_notice, U, pend[0]["notice_id"])
    assert all(r["request_digest"] == R.MARKER for r in _acts(d))
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, clean, restore=True)
    _ok(b.import_memory, red, restore=True)
    assert all(r["request_digest"] == R.MARKER for r in _acts(b))


# ========================================================================= the axis (D10, D11, M2, M4)
@pytest.mark.parametrize("axis,match", [
    ({"attv": "ATTEST-03@b1329a81"}, "attv"), ({"att": "proven"}, "att:"), ({"att": None}, "without-att"),
    ({"src": ""}, "src"),
])
def test_d10_an_axis_outside_its_rules_refuses_in_both_modes(tmp_path, axis, match):
    """Build note D10 (0045 §2c: "an `attv` outside its grammar → the unit refused", either mode; research's Q4): from
    era 14 the file's axis is checked BEFORE the default stamp — a default import used to overwrite a malformed
    `attv` silently. Mutant: check after the stamp."""
    a, e1, e2, _c = _history(tmp_path)
    f = _edit(_export(a, tmp_path, "a.jsonl"), "bad.jsonl",
              lambda recs: [dict(r, **axis) if r.get("record") == "edge" else r for r in recs])
    for mode in (False, True):
        m = _mem(tmp_path, f"m{mode}.db")
        _refused(m, f, f"grounding axis outside its rules \\({match}")
        assert not m.store.edges(U, active_only=False, include_quarantined=True)


def test_d10_both_predicate_versions_restore_as_recorded_and_a_dangling_src_is_admitted(tmp_path):
    """INV-G13 (versions coexist): ATTEST-3 and current-version rows restore with their own `attv`, and `why` names each.
    Research's M4 (the owner's F1(b)): a `src` naming no held or carried episode (a deleted or consumed source) is
    admitted in a restore, never refused. The default import still stamps (INV-G9's default half)."""
    a, e1, e2, _c = _history(tmp_path)
    f = _edit(_export(a, tmp_path, "a.jsonl"), "v3.jsonl",
              lambda recs: [dict(r, attv="ATTEST-3@b1329a81", src="ep-gone") if r.get("record") == "edge"
                            and r["id"] == e1 else r for r in recs])
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    got = {e.id: (e.attv, e.src) for e in b.store.edges(U, active_only=False, include_quarantined=True)}
    assert got[e1] == ("ATTEST-3@b1329a81", "ep-gone") and got[e2][0] == PREDICATE_VERSION
    assert "ATTEST-3@b1329a81" in W.render(W.gather(b.store, U, e1))
    d = _mem(tmp_path, "d.db")
    _ok(d.import_memory, f)
    assert {(e.att, e.attv, e.src) for e in d.store.edges(U, active_only=False, include_quarantined=True)} == \
        {("not_attested", DEFAULT_IMPORT, None)}


def test_d11_m2_a_restore_compares_the_axis_except_over_a_held_default_import(tmp_path):
    """Build note D11 with research's M2: a trusted restore over a held edge whose axis DIFFERS refuses (0009's
    differing record; INV-G13: never rewritten) — except where the held axis is `default-import`, this store's own
    judgement: kept, and listed in `axis_kept_default_import`. Mutants: exclude the axis in restore; refuse the M2 case."""
    a, e1, e2, _c = _history(tmp_path)
    f = _edit(_export(a, tmp_path, "a.jsonl"), "capped.jsonl",
              lambda recs: [r for r in recs if r not in _act_lines(recs)])
    capped = _edit(f, "capped2.jsonl", lambda recs: [dict(r, provenance=dict(
        r["provenance"], author_of_evidence="third_party", derived_from="third_party", disclosure="use_only"))
        if r.get("record") in ("edge", "episode") and "provenance" in r else r for r in recs])
    d = _mem(tmp_path, "d.db")
    _ok(d.import_memory, capped)
    r = _ok(d.import_memory, capped, restore=True)
    assert sorted(r["axis_kept_default_import"]) == sorted([e1, e2])
    assert {e.attv for e in d.store.edges(U, active_only=False, include_quarantined=True)} == {DEFAULT_IMPORT}
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    flipped = _edit(f, "flip.jsonl", lambda recs: [dict(r, att="attested") if r.get("record") == "edge" else r
                                                  for r in recs])
    msg = _refused(b, flipped, "already exists with different content", restore=True)
    assert "capped incoming form" not in msg                  # the restore's own comparison, not the default cap


def test_era_act_lines_below_14_refuse_and_the_axis_below_14_is_stripped(tmp_path):
    """Refuse-don't-drop below the era (build note D12): an act line in an envelope declaring 13 refuses; the axis in a
    ≤13 file is stripped (0006 I10), so a restore writes it NULL."""
    a, e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    old = _edit(f, "13.jsonl", lambda recs: [dict(recs[0], version=13)] + recs[1:])
    _refused(_mem(tmp_path, "b.db"), old, "declares format 13 but carries confirmation")
    bare = _edit(old, "13b.jsonl", lambda recs: [r for r in recs if r not in _act_lines(recs)])
    c = _mem(tmp_path, "c.db")
    _ok(c.import_memory, bare, restore=True)
    assert {(e.att, e.attv, e.src) for e in c.store.edges(U, active_only=False, include_quarantined=True)} == \
        {(None, None, None)}


# ================================================================= concurrency (IO-II-4, build note D9)
def test_d9_a_local_challenge_landing_before_the_commit_is_a_lost_race_and_the_retry_refuses(tmp_path, monkeypatch):
    """IO-II-4 ("cross-connection tests proving whole-unit refusal"): a challenge written by ANOTHER connection between
    this import's preflight and its commit changes H; the commit returns DESTINATION_CHANGED, and the retry refuses the
    incoming confirmation whole (another origin, unresolved). Mutant: the act re-check removed."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    f0 = _export(a, tmp_path, "a0.jsonl")
    _ok(a.confirm, U, e, date="2026-10-01")
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f0, restore=True)
    other = SqliteStore(str(tmp_path / "b.db"))
    real = SqliteStore.commit_outcome_import_plan
    calls = []

    def racing(self, user_id, plan, expected):
        if not calls:
            other.add_reply(U, e, kind="challenge", text="raced in", target=None, actor=__import__(
                "veracium.schema", fromlist=["ReplyActor"]).ReplyActor.USER, correlation_id="race-1")
        out = real(self, user_id, plan, expected)
        calls.append(out)
        return out
    monkeypatch.setattr(SqliteStore, "commit_outcome_import_plan", racing)
    _refused(b, f, "cannot be ordered", restore=True)
    # the first pass's preflight admitted the confirmation (no challenge yet); its commit saw the moved acts and
    # returned DESTINATION_CHANGED; the retry's preflight refused before any second commit
    assert calls == [DESTINATION_CHANGED]
    assert not [r for r in _acts(b) if r["table"] == "confirmations"]
    other.close()


def test_io_ii_4_confirming_only_after_resolution_across_connections(tmp_path):
    """IO-II-4 ("confirming only after resolution"): a restore installs an OPEN challenge; another connection's local
    confirm is then refused (INV-R13 reads the imported challenge); a later import of the resolve admits it."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    c = _ok(a.reply, U, e, kind="challenge", text="no")
    f0 = _export(a, tmp_path, "a0.jsonl")
    _ok(a.reply, U, e, kind="resolve", target=c["reply_id"])
    f1 = _export(a, tmp_path, "a1.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f0, restore=True)
    other = Memory(llm=_Fake(), config=MemoryConfig(db_path=str(tmp_path / "b.db"), wiki_recompile_after_writes=0))
    with pytest.raises(ValueError, match="active challenge"):
        other.confirm(U, e)
    _ok(b.import_memory, f1, restore=True)
    _ok(other.confirm, U, e)


# ====================================================================== why (D17) and the refused-record rule
def test_d17_why_shows_an_acts_origin_and_its_original_request_id(tmp_path):
    """0008 §3a ("testimony, shown in `why`"; build note D17): an imported act is shown with its origin, and with the
    ORIGINAL request id, never its internal `#act:` key."""
    a, e1, e2, _c = _history(tmp_path)
    d = _mem(tmp_path, "d.db")
    _ok(d.import_memory, _export(a, tmp_path, "a.jsonl"))
    bio = W.gather(d.store, U, e2)
    assert {c["origin"] for c in bio.confirmations} == {"imported"} and {r["origin"] for r in bio.replies} == {"imported"}
    assert all(not (c["correlation_id"] or "").startswith("#act:") for c in bio.confirmations)
    assert "[imported]" in W.render(bio) and "#act:" not in W.render(bio)


def test_d14_the_commit_primitive_refuses_an_act_labelled_local_or_keyed_in_the_callers_grammar(tmp_path):
    """Build note D14 at the primitive (a plan reaches it by other routes than the preflight): an imported act is only
    ever `imported` or `restored` (INV-Q5, 0047 INV-R21) under an internal `#act:` key (INV-Q4′); a plan carrying a `local` act, or
    one keyed in the caller's grammar, is refused and nothing is written."""
    a, e1, e2, _c = _history(tmp_path)
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, _export(a, tmp_path, "a.jsonl"), restore=True)
    row = dict(_one(r for r in _acts(b) if r["table"] == "confirmations"), id="c-forged", act_seq=99,
               origin_act_id="c-forged")
    for bad in ({"origin": "local", "correlation_id": "#act:" + "0" * 32}, {"origin": "imported", "correlation_id": "k-9"}):
        with pytest.raises(ValueError, match="an import writes only"):
            b.store.commit_outcome_import_plan(U, {"edges": [], "episodes": [], "acts": [dict(row, **bad)]}, {})
    assert not _q(b, "SELECT 1 FROM confirmations WHERE id='c-forged'")


def test_r14_a_resolve_naming_anything_but_a_challenge_of_its_edge_refuses(tmp_path):
    """0008 §6f / 0047 INV-R14 at import: a resolve names a CHALLENGE of its own edge in H, by identity; a resolve
    naming a context reply, or a challenge of another edge, refuses the whole unit."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    e2 = _fact(a, "works_as", "dentist")
    _ok(a.reply, U, e, kind="context", text="some context")
    c2 = _ok(a.reply, U, e2, kind="challenge", text="no")
    f = _export(a, tmp_path, "a.jsonl")
    recs = _lines(f)
    ctx, ch2 = _seq(recs, "context"), _seq(recs, "challenge")
    for name, tgt in (("ctx", ctx["act_uid"]), ("other-edge", ch2["act_uid"])):
        res = {"record": "reply", "act_uid": ctx["act_uid"][:2] + [f"r-{name}"], "act_seq": 90, "edge_id": e,
               "kind": "resolve", "target_uid": tgt, "text": None, "actor": "user",
               "recorded_correlation_id": f"k-{name}", "request_digest": "e" * 64, "origin": "local",
               "written_at": ctx["written_at"]}
        _refused(_mem(tmp_path, f"b-{name}.db"), _edit(f, f"{name}.jsonl", lambda rs: rs + [res]),
                 "names no challenge of its edge", restore=True)
    assert c2["reply_id"]


def test_acts_on_a_record_refused_per_record_go_with_it_and_are_counted(tmp_path):
    """Build note (stage-2 question): a default import refuses a procedural record PER RECORD (0037 §4e) and admits the
    rest; an act on that record goes with it — refused with it and counted (`acts_refused_with_edge`), never an orphan
    that would refuse the whole file. Mutant: keep the act (the file then refuses whole as an orphan)."""
    a, e1, e2, _c = _history(tmp_path)
    _ok(a.record_procedure, U, "I review invoices every Friday", author=EvidenceAuthor.USER,
        context=EvidenceContext.direct(basis="stated"))
    f = _export(a, tmp_path, "a.jsonl")
    proc = _one(r for r in _lines(f) if r.get("record") == "edge" and (r.get("provenance") or {}).get("record_kind"))
    k = dict(_seq(_lines(f), "confirm"), act_uid=[a.store.local_origin(), U, "c-proc"], act_seq=50, edge_id=proc["id"])
    d = _mem(tmp_path, "d.db")
    r = _ok(d.import_memory, _edit(f, "p.jsonl", lambda rs: rs + [k]))
    assert r["procedural_refused"] == 1 and r["acts_refused_with_edge"] == 1 and r["confirmations"] == 2


def test_d17_the_cli_names_the_acts_it_exported_and_imported(tmp_path, capsys):
    """Build note D17: the CLI's export and import lines name the confirmations and replies when the file carries any,
    and are otherwise unchanged."""
    from veracium.cli import main as cli_main
    a, e1, e2, _c = _history(tmp_path)
    f = tmp_path / "cli.jsonl"
    a.store.close()
    assert _ok(cli_main, ["export", str(f), "--user", U, "--db", str(tmp_path / "a.db")]) == 0
    assert "+ 2 confirmations + 2 replies ->" in capsys.readouterr().out
    assert _ok(cli_main, ["import", str(f), "--restore", "--db", str(tmp_path / "b.db")]) == 0
    assert "+ 2 confirmations + 2 replies into" in capsys.readouterr().out
    bare = _edit(f, "bare.jsonl", lambda recs: [r for r in recs if r not in _act_lines(recs)])
    assert _ok(cli_main, ["import", str(bare), "--db", str(tmp_path / "c.db")]) == 0
    assert "confirmations" not in capsys.readouterr().out


# ======================================== research's T11b stage-2 witnesses (READ-T11b-stage2.md, research 9fca4a7b)
# Adopted verbatim from proposals/evidence-t11b/stage2/test_research_t11b_witnesses.py (sha256 in its sha256.txt), the
# `test_w_` prefix renamed: each killed a research mutant that survived dev's cells (RM-A, I, Q, Y, E, H; the mutants are
# in t11b_mutant_defs.py's research group).
def _third_party(recs):
    """The edge and episode lines at third-party trust, so a default import's cap changes nothing but the axis."""
    return [dict(r, provenance=dict(r["provenance"], author_of_evidence="third_party", derived_from="third_party",
                                    disclosure="use_only"))
            if r.get("record") in ("edge", "episode") and "provenance" in r else r for r in recs]


def test_s2_research_rm_a_m2_keeps_only_the_axis_a_content_difference_still_refuses(tmp_path):
    """RM-A. M2 keeps a held `default-import` stamp only where the record is otherwise EQUAL: a restore whose copy of
    that edge differs in content refuses (0009's differing record), as before T11b."""
    a, e1, _e2, _c = _history(tmp_path)
    f = _edit(_export(a, tmp_path, "a.jsonl"), "tp.jsonl",
              lambda recs: _third_party([r for r in recs if r not in _act_lines(recs)]))
    d = _mem(tmp_path, "d.db")
    _ok(d.import_memory, f)
    changed = _edit(f, "chg.jsonl", lambda recs: [dict(r, object="Lyon") if r.get("id") == e1 else r for r in recs])
    _refused(d, changed, "already exists with different content", restore=True)


def test_s2_research_rm_i_r_m1_needs_both_labels_proof_a_testimony_challenge_stays_incomparable(tmp_path):
    """RM-I (INV-Q10, INV-R23). R-M1 orders an unknown position first only when BOTH acts are proof. A restored legacy confirmation
    (unknown position) against a same-origin `imported` challenge with a known position, unresolved: refused."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    _ok(a.confirm, U, e, date="2026-10-01")
    _q(a, "UPDATE confirmations SET act_seq=NULL")
    a.store._conn.commit()
    _ok(a.reply, U, e, kind="challenge", text="later, I disagree")
    f = _edit(_export(a, tmp_path, "a.jsonl"), "t.jsonl",
              lambda recs: [dict(r, origin="imported") if r.get("kind") == "challenge" else r for r in recs])
    _refused(_mem(tmp_path, "b.db"), f, "cannot be ordered", restore=True)


def test_s2_research_rm_q_a_new_act_at_a_held_acts_position_ties(tmp_path):
    """RM-Q (INV-Q10). Two different acts at one position refuse when one is HELD and the other arrives (not only within a
    unit): the destination holds the challenge; the file brings a different act at its position."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    _ok(a.reply, U, e, kind="challenge", text="wrong")
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    ch = _seq(_lines(f), "challenge")
    other = dict(ch, act_uid=ch["act_uid"][:2] + ["r-other"], kind="context", text="another act")
    g = _edit(f, "g.jsonl", lambda recs: [r for r in recs if r.get("record") != "reply"] + [other])
    _refused(b, g, "one position", restore=True)
    assert len(_acts(b)) == 1


def test_s2_research_rm_y_a_resolve_after_the_confirmation_does_not_clear_it(tmp_path):
    """RM-Y (INV-Q10, INV-R23). A confirmation made AFTER a challenge and BEFORE its resolve was made under an open challenge: refused,
    though the challenge is resolved later in the same history."""
    a, _e1, e2, _c = _history(tmp_path)
    f = _export(a, tmp_path, "a.jsonl")
    recs = _lines(f)
    ch, res = _seq(recs, "challenge"), _seq(recs, "resolve")
    k = _seq(recs, "confirm", e2)
    lo = ch["act_seq"]
    g = _edit(f, "g.jsonl", lambda rs: [dict(r, act_seq=lo + 1) if r is not None and r.get("act_uid") == k["act_uid"]
                                        else dict(r, act_seq=lo + 50) if r.get("act_uid") == res["act_uid"] else r
                                        for r in rs])
    _refused(_mem(tmp_path, "b.db"), g, "made under challenge", restore=True)


def test_s2_research_rm_e_rule0_reads_replies_too(tmp_path):
    """RM-E. Rule 0 is per arriving ACT: a default file whose only act claiming this store's origin is a REPLY is
    refused whole."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    _ok(a.reply, U, e, kind="challenge", text="wrong")
    d = _mem(tmp_path, "d.db")
    own = d.store.local_origin()
    f = _edit(_export(a, tmp_path, "a.jsonl"), "f.jsonl",
              lambda recs: [dict(r, act_uid=[own] + r["act_uid"][1:]) if r in _act_lines(recs) else r for r in recs])
    _refused(d, f, "THIS store's origin")
    assert not d.store.edges(U, active_only=False, include_quarantined=True)


def test_s2_research_rm_h_an_act_onto_an_edge_carrying_the_marker_with_no_notice(tmp_path):
    """RM-H. An arriving act onto an edge whose file copy carries the marker but no notice attests it. Observed: what
    refuses, and whether the act-level coverage rule is the one that does (if the edge-level rule refuses first, the
    marker arm of `redacted` is defence in depth)."""
    a, e1, _e2, _c = _history(tmp_path)
    f = _edit(_export(a, tmp_path, "a.jsonl"), "m.jsonl",
              lambda recs: [dict(r, object=R.MARKER) if r.get("id") == e1 else r for r in recs])
    msg = _refused(_mem(tmp_path, "b.db"), f, ".", restore=True)
    assert "coverage is all or nothing" in msg, msg


def test_s2_an_orphaned_act_is_exported_and_reported_and_its_import_refuses(tmp_path, capsys):
    """Research's T11b S2-2: an act whose edge this store no longer holds is corruption (no verb writes one). The export
    still writes it and REPORTS it (`acts_orphaned`; the CLI warns) instead of refusing the whole backup; an import of
    that file is refused whole (INV-R11). Mutant: count nothing."""
    from veracium.cli import main as cli_main
    a, e1, e2, _c = _history(tmp_path)
    _q(a, "DELETE FROM edges WHERE id=?", (e1,))                 # corruption: the edge gone, its act kept
    a.store._conn.commit()
    r = _ok(a.export_memory, U, tmp_path / "o.jsonl")
    assert r["acts_orphaned"] == 1 and r["confirmations"] == 2
    a.store.close()
    assert _ok(cli_main, ["export", str(tmp_path / "o2.jsonl"), "--user", U, "--db", str(tmp_path / "a.db")]) == 0
    assert "1 confirmation(s) or reply(ies) name a fact this store no longer holds" in capsys.readouterr().out
    _refused(_mem(tmp_path, "b.db"), tmp_path / "o.jsonl", "neither the file nor this store", restore=True)


def test_s2_why_names_an_act_without_an_original_request_id(tmp_path):
    """Research's T11b S2-6(c): an imported act recorded with NO original request id renders as such in `why`, never as
    "(correlation None)"."""
    a, e1, e2, _c = _history(tmp_path)
    f = _edit(_export(a, tmp_path, "a.jsonl"), "n.jsonl",
              lambda recs: [dict(r, recorded_correlation_id=None) if r.get("record") == "confirmation" else r
                            for r in recs])
    d = _mem(tmp_path, "d.db")
    _ok(d.import_memory, f)
    text = W.render(W.gather(d.store, U, e1))
    assert "no original request id" in text and "correlation None" not in text


def test_i3_a_replay_in_the_unit_does_not_exempt_a_tie(tmp_path):
    """0008 INV-I3's second clause: an exact replay never exempts another new act in the unit from validation, at
    §6f's position check. A trusted restore whose unit holds a REPLAYED act (the held confirmation, unchanged) and a
    NEW act at the held challenge's position refuses the unit as a tie, as RM-Q's unit with nothing replaying does
    (the control below). Research's T12 stage-2 repro (S2-M1), adopted: the position check skipped for a unit holding a
    replay (mutant I3-c) survived every cell before it. Mutant: skip §6f's position check for a unit that contains a
    replay."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    _ok(a.confirm, U, e, date="2026-10-01")
    _ok(a.reply, U, e, kind="challenge", text="wrong")
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    ch = _seq(_lines(f), "challenge")
    other = dict(ch, act_uid=ch["act_uid"][:2] + ["r-other"], kind="context", text="another act")
    # the unit: the held confirmation (an exact replay) and a new act at the held challenge's position
    g = _edit(f, "g.jsonl", lambda recs: [r for r in recs if r.get("record") != "reply"] + [other])
    assert any(r.get("record") == "confirmation" for r in _lines(g))
    _refused(b, g, "one position", restore=True)
    assert len(_acts(b)) == 2


def test_i3_control_the_same_tie_without_a_replay_refuses(tmp_path):
    """The control for the cell above: RM-Q's shape (no confirmation in the source, so nothing in the unit replays) is
    refused as a tie at the product and under the mutant alike."""
    a = _mem(tmp_path, "a.db")
    e = _fact(a)
    _ok(a.reply, U, e, kind="challenge", text="wrong")
    f = _export(a, tmp_path, "a.jsonl")
    b = _mem(tmp_path, "b.db")
    _ok(b.import_memory, f, restore=True)
    ch = _seq(_lines(f), "challenge")
    other = dict(ch, act_uid=ch["act_uid"][:2] + ["r-other"], kind="context", text="another act")
    g = _edit(f, "g.jsonl", lambda recs: [r for r in recs if r.get("record") != "reply"] + [other])
    _refused(b, g, "one position", restore=True)

