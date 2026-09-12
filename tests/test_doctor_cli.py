"""`veracium doctor` — the read-only store linter (src/veracium/doctor.py) and its
CLI verb. A linter is tested by what it CATCHES: every check has a planted defect
that must be named, and a clean store that must not be. Defects are planted with
raw SQL on a copy, because that is exactly what the linter exists to detect —
rows the product did not write."""

import hashlib
import json
import pathlib
import shutil
import sqlite3
import tempfile

import pytest

from veracium import Memory, MemoryConfig, EvidenceAuthor
from veracium import doctor
from veracium.cli import main as cli_main
from veracium.schema import EvidenceContext
from veracium.store import revocation as rv
from veracium.store import schema_version as sv


class Fake:
    def __init__(self, scripts):
        self._scripts = list(scripts)

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill" and self._scripts:
            return json.dumps(self._scripts.pop(0))
        return "## USER MODEL\n- test wiki"


U = "ida"


def _seed(db, *, confirm=False):
    """Three remembers (one supersession, one third-party claim with a source id).
    `confirm=True` adds a confirmation and an outcome on the pet fact — which the
    doctor reports (see test_the_doctor_found_the_confirmation_episode_id_mismatch)."""
    mem = Memory(llm=Fake([
        {"triples": [{"subject": "user", "relation": "has_pet", "object": "cat Miso"},
                     {"subject": "user", "relation": "prefers", "object": "concise answers"}],
         "episode": "User shared pet and preference."},
        {"triples": [{"subject": "user", "relation": "prefers", "object": "detailed answers"}],
         "episode": "User switched preference."},
        {"triples": [{"subject": "org:quickclaim", "relation": "third_party_claim",
                      "object": "user owes $2,400"}],
         "episode": "Received a collection email."},
    ]), config=MemoryConfig(db_path=db, wiki_recompile_after_writes=0))
    mem.remember(U, "I have a cat named Miso and I like concise answers", date="2026-09-01",
                 context=EvidenceContext.direct())
    mem.remember(U, "Actually, give me detailed answers", date="2026-09-02",
                 context=EvidenceContext.direct())
    mem.remember(U, "email from quickclaim", author=EvidenceAuthor.THIRD_PARTY,
                 event_type="email", source_id="quickclaim-inbox", date="2026-09-03")
    if confirm:
        pet = next(e for e in mem.store.edges(U) if e.relation == "has_pet")
        mem.confirm(U, pet.id, date="2026-09-04")
        mem.record_outcome(U, pet.id, outcome="confirmed", actor="user", evidence_ref="r1", date="2026-09-05")
    mem.close()
    return db


def test_the_doctor_found_the_confirmation_episode_id_mismatch():
    """FOUND ON THE DOCTOR'S FIRST RUN (2026-09-12), a product defect in guarded code:
    `SqliteStore.confirm_edge` inserts the confirmation episode's ROW under one minted
    id (`ep-<hex>`) while the Episode payload it stores carries another (`ep-c-<hex>`),
    so the row and its JSON disagree about the episode's identity. Surfaced to the
    owner; the fix lives under specs/0008 and is not this tool's to make. This test
    pins the finding so the defect cannot be forgotten, and FAILS the day it is fixed
    (delete it then)."""
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db", confirm=True)
        rep = doctor.diagnose(db)
        f = [x for x in rep.findings if x.check == "rows" and "episode row(s)" in x.message]
        assert len(f) == 1 and len(f[0].ids) == 1, _messages(rep, "rows")
        c = sqlite3.connect(db)
        row_id, payload_id = c.execute("SELECT id, json_extract(json,'$.id') FROM episodes WHERE id=?",
                                       (f[0].ids[0],)).fetchone()
        c.close()
        assert payload_id.startswith("ep-c-") and row_id != payload_id
        # and nothing ELSE on a store with a confirmation and an outcome
        assert [x.message for x in rep.findings if x.level in ("error", "warn")] == [f[0].message]


def _messages(rep, check=None):
    return [f.message for f in rep.findings if check is None or f.check == check]


def _plant(db, sql, *args):
    c = sqlite3.connect(db)
    c.execute(sql, args); c.commit(); c.close()


def test_a_clean_store_is_clean_and_every_check_ran():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        rep = doctor.diagnose(db)
        assert rep.readable and rep.user_version == sv.SCHEMA_VERSION
        assert [f for f in rep.findings if f.level in ("error", "warn")] == [], _messages(rep)
        assert set(rep.checks_run) >= {"file", "version", "objects", "rows", "refs", "journal", "revocation", "runtime"}
        assert rep.users == [U] and rep.counts["edges"] == 4 and rep.counts["active_edges"] == 3
        assert rep.exit_code == 0
        text = doctor.render(rep)
        assert "CLEAN" in text and "nothing was changed" in text
        json.dumps(doctor.to_json(rep), default=str)


def test_doctor_writes_nothing_and_opens_read_only():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        before = hashlib.sha256(pathlib.Path(db).read_bytes()).hexdigest()
        doctor.diagnose(db); doctor.diagnose(db, user=U)
        assert hashlib.sha256(pathlib.Path(db).read_bytes()).hexdigest() == before
        # the original is never opened: no journal/WAL side file appears beside it
        assert sorted(p.name for p in pathlib.Path(d).iterdir()) == ["t.db"]
        # the snapshot copy is removed
        assert not [p for p in pathlib.Path(tempfile.gettempdir()).glob("veracium-doctor-*")]
        # and it never creates a file: a missing path is a finding, not a new store
        rep = doctor.diagnose(f"{d}/nope.db")
        assert not rep.readable and rep.exit_code == 2 and not pathlib.Path(f"{d}/nope.db").exists()


def test_a_non_database_file_is_reported_not_crashed():
    with tempfile.TemporaryDirectory() as d:
        p = f"{d}/text.db"; pathlib.Path(p).write_text("this is not sqlite\n" * 100)
        rep = doctor.diagnose(p)
        assert not rep.readable and rep.exit_code == 2
        assert any("not a readable SQLite database" in m or "quick_check" in m for m in _messages(rep, "file"))


def test_a_below_head_store_is_reported_without_opening_the_store_class():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        _plant(db, f"PRAGMA user_version = {sv.SCHEMA_VERSION - 1}")
        rep = doctor.diagnose(db)
        assert rep.readable and rep.user_version == sv.SCHEMA_VERSION - 1 and rep.exit_code == 1
        assert any("below this build's head" in m and "migrating forward is specs/0013's contract" in m
                   for m in _messages(rep, "version"))
        assert any("skipped: the constructor refused the snapshot" in m for m in _messages(rep, "revocation"))
        # the two other refusals the constructor can give, reported the same way
        for pragma, needle, version in (("PRAGMA user_version = 0", "foreign-shape (found=0", 0),
                                        ("PRAGMA user_version = 99", "newer (found=99", 99)):
            db2 = _seed(f"{d}/v{version}.db"); _plant(db2, pragma)
            r2 = doctor.diagnose(db2)
            assert r2.readable and r2.exit_code == 1 and r2.user_version == version
            assert any(needle in m for m in _messages(r2, "version")), _messages(r2, "version")
        # no sqlite3.connect of its own: specs/0031 §4b-ii's inventory stays as it is
        import re
        assert not re.search(r"sqlite3\.connect\s*\(", pathlib.Path(doctor.__file__).read_text())


def test_the_singleton_and_the_epoch_are_checked():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        _plant(db, "DELETE FROM store_identity")
        rep = doctor.diagnose(db)
        assert any("store_identity singleton: 0 row(s)" in m for m in _messages(rep, "version"))
        db2 = _seed(f"{d}/u.db")
        _plant(db2, "UPDATE store_epoch SET schema_at = 99")
        assert any("schema_at 99 is above" in m for m in _messages(doctor.diagnose(db2), "version"))


def test_a_dropped_index_is_repaired_on_open_not_reported_and_a_dropped_table_is_damage():
    """The doctor reads through the store constructor (specs/0031 §4b-ii allows no
    second opener), and the constructor rebuilds REBUILDABLE objects on open
    (specs/0007) — so a dropped index is invisible to the doctor, by design, and the
    original file is still untouched. A dropped REQUIRED table is damage and is named."""
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        _plant(db, "DROP INDEX ix_edges_subj_rel")
        before = hashlib.sha256(pathlib.Path(db).read_bytes()).hexdigest()
        rep = doctor.diagnose(db)
        assert not [x for x in rep.findings if x.check == "objects"], _messages(rep, "objects")
        assert hashlib.sha256(pathlib.Path(db).read_bytes()).hexdigest() == before   # repaired on the COPY only
        c = sqlite3.connect(db)
        assert c.execute("SELECT count(*) FROM sqlite_master WHERE name='ix_edges_subj_rel'").fetchone()[0] == 0
        c.close()
        db2 = _seed(f"{d}/u.db")
        _plant(db2, "DROP TABLE supersession_refusals")
        rep2 = doctor.diagnose(db2)
        # a missing REQUIRED table is a stamped-shape mismatch the constructor refuses,
        # naming the objects that differ — the doctor carries that refusal as the finding
        f2 = [x for x in rep2.findings if x.check == "version" and x.level == "error"]
        assert f2 and "table:supersession_refusals" in f2[0].message and rep2.exit_code == 1


def test_row_level_inconsistencies_are_named():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        c = sqlite3.connect(db)
        ids = [r[0] for r in c.execute("SELECT id FROM edges WHERE active=1 AND quarantined=0 ORDER BY id")]
        ids.append(c.execute("SELECT id FROM edges WHERE quarantined=1").fetchone()[0])   # ids[2]: the claim
        retired = c.execute("SELECT id FROM edges WHERE active=0").fetchone()[0]
        # (a) active column contradicts the payload; (b) quarantined column contradicts disclosure;
        # (c) a retired edge with a reason outside the vocabulary; (d) payload id differs; (e) bad JSON
        c.execute("UPDATE edges SET active=0 WHERE id=?", (ids[0],))
        c.execute("UPDATE edges SET quarantined=1 WHERE id=?", (ids[1],))
        c.execute("UPDATE edges SET json = json_set(json, '$.invalidation_reason', 'vibes') WHERE id=?", (retired,))
        c.execute("UPDATE edges SET json = json_set(json, '$.id', 'e-elsewhere') WHERE id=?", (ids[2],))
        c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
                  "VALUES('e-broken','ida','s','r','o',1,0,'{not json')")
        c.execute("UPDATE episodes SET json = '{oops' WHERE id = (SELECT id FROM episodes LIMIT 1)")
        c.commit(); c.close()
        rep = doctor.diagnose(db)
        msgs = _messages(rep, "rows")
        assert any("`active` column disagrees" in m for m in msgs)
        assert any("`quarantined` column disagrees" in m for m in msgs)
        assert any("outside the dispositioned vocabulary" in m for m in msgs)
        assert any("id/user_id differ from the row columns" in m for m in msgs)
        assert any("edge row(s) whose JSON does not parse" in m for m in msgs)
        assert any("episode row(s) whose JSON does not parse" in m for m in msgs)
        by = {f.message: f.ids for f in rep.findings if f.check == "rows"}
        assert any("e-broken" in v for v in by.values())
        assert rep.exit_code == 1


def test_dangling_and_cyclic_supersession_and_an_unretired_predecessor():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        c = sqlite3.connect(db)
        old = c.execute("SELECT id FROM edges WHERE active=0").fetchone()[0]
        new = c.execute("SELECT id FROM edges WHERE json_extract(json,'$.supersedes') = ?", (old,)).fetchone()[0]
        pet = c.execute("SELECT id FROM edges WHERE relation='has_pet'").fetchone()[0]
        claim = c.execute("SELECT id FROM edges WHERE relation='third_party_claim'").fetchone()[0]
        # dangling: the pet edge points at a ghost
        c.execute("UPDATE edges SET json = json_set(json, '$.supersedes', 'e-ghost') WHERE id=?", (pet,))
        # cycle: old -> new -> old
        c.execute("UPDATE edges SET json = json_set(json, '$.supersedes', ?) WHERE id=?", (new, old))
        # unretired predecessor: the claim supersedes the (active) new edge while both stay active
        c.execute("UPDATE edges SET json = json_set(json, '$.supersedes', ?) WHERE id=?", (new, claim))
        c.commit(); c.close()
        rep = doctor.diagnose(db)
        msgs = _messages(rep, "refs")
        assert any("dangling supersession link" in m for m in msgs)
        assert any("supersession CYCLE" in m for m in msgs)
        assert any("predecessor is still active" in m for m in msgs)
        ids = {i for x in rep.findings if x.check == "refs" for i in x.ids}
        assert {pet, claim} <= ids and (old in ids or new in ids)


def test_orphaned_references_in_every_side_table_are_named():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db", confirm=True)
        c = sqlite3.connect(db)
        pet = c.execute("SELECT id FROM edges WHERE relation='has_pet'").fetchone()[0]
        ep = c.execute("SELECT id FROM episodes WHERE json_extract(json,'$.kind')='outcome'").fetchone()[0]
        # the outcome's edge vanishes; the confirmation, an embedding and the journal now point at nothing
        c.execute("INSERT INTO edge_embedding(edge_id,user_id,embedder_id,content_digest,dim,vec,built_at) "
                  "VALUES(?, 'ida', 'emb', 'd', 2, x'0000', '2026-09-05T00:00:00Z')", (pet,))
        c.execute("INSERT INTO contribution_ledger(id,user_id,survivor_type,survivor_id,site,payload,created_at,"
                  "contributor_type,contributor_ref) VALUES('cl-1','ida','edge','e-ghost','site','{}','2026-09-05T00:00:00Z','edge','e-ghost2')")
        c.execute("DELETE FROM edges WHERE id=?", (pet,))
        c.commit(); c.close()
        rep = doctor.diagnose(db)
        msgs = _messages(rep, "refs")
        for needle in ("outcome episode(s) naming an edge that does not exist",
                       "confirmation(s) naming an edge that does not exist",
                       "ledger row(s) whose survivor does not exist",
                       "ledger row(s) whose typed contributor does not exist",
                       "embedding(s) for an edge that does not exist",
                       "journaled edge id(s) with no row"):
            assert any(needle in m for m in msgs), needle
        ids = {i for x in rep.findings if x.check == "refs" for i in x.ids}
        assert {pet, ep, "cl-1"} <= ids


def test_an_edge_written_outside_the_journal_is_a_warning():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        _plant(db, "INSERT INTO edges(id,user_id,subject,relation,object,active,quarantined,json) VALUES("
               "'e-silent','ida','user','likes','tea',1,0,"
               "json_object('id','e-silent','user_id','ida','subject','user','relation','likes','object','tea',"
               "'volatility','durable','valid_from','2026-09-01T00:00:00Z','provenance',json_object('author_of_evidence','user','disclosure','mentionable')))")
        rep = doctor.diagnose(db)
        f = [x for x in rep.findings if x.check == "journal"]
        assert f and f[0].level == "warn" and f[0].ids == ["e-silent"]


def test_revocation_completeness_holds_after_a_real_revocation_and_fails_after_a_hand_reinstatement():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        from veracium.store.sqlite import SqliteStore
        from veracium.source_identity import resolve_origin, source_identity_digest
        store = SqliteStore(db)
        claim = next(e for e in store.edges(U, include_quarantined=True) if e.relation == "third_party_claim")
        digest = source_identity_digest(resolve_origin(claim.provenance.origin, store.local_origin()),
                                        claim.provenance.source_id)
        rv.revoke_source(store, U, digest, "revoke", "operator", "2026-09-07T00:00:00Z")
        store.close()
        rep = doctor.diagnose(db)
        assert not [x for x in rep.findings if x.check == "revocation"], _messages(rep, "revocation")
        # a hand reinstatement of the retired claim: the standing set still revokes it
        _plant(db, "UPDATE edges SET active=1, json = json_remove(json_set(json, '$.invalidated_at', NULL), "
                   "'$.invalidation_reason') WHERE id=?", claim.id)
        rep2 = doctor.diagnose(db)
        f = [x for x in rep2.findings if x.check == "revocation"]
        assert f and f[0].level == "error" and "NOT APPLIED" in f[0].message and claim.id in f[0].ids


def test_forget_leaves_no_orphan_the_doctor_can_see():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        mem = Memory(llm=lambda p, **k: "{}", config=MemoryConfig(db_path=db)); mem.forget(U); mem.close()
        rep = doctor.diagnose(db)
        assert rep.users == [] and rep.counts["edges"] == 0
        assert not [x for x in rep.findings if x.level in ("error", "warn")], _messages(rep)


def test_the_cli_round_trips_with_exit_codes(capsys):
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        assert cli_main(["doctor", "--db", db]) == 0
        out = capsys.readouterr().out
        assert out.startswith("veracium doctor") and "CLEAN" in out and "✓ refs" in out
        assert cli_main(["doctor", "--db", db, "--user", U, "--json"]) == 0
        doc = json.loads(capsys.readouterr().out)
        assert doc["readable"] and doc["exit_code"] == 0 and doc["users"] == [U]
        _plant(db, "UPDATE edges SET json = json_set(json, '$.supersedes', 'e-ghost') WHERE relation='has_pet'")
        assert cli_main(["doctor", "--db", db]) == 1
        assert "dangling supersession link" in capsys.readouterr().out
        assert cli_main(["doctor", "--db", f"{d}/missing.db"]) == 2
        assert "UNREADABLE" in capsys.readouterr().out
