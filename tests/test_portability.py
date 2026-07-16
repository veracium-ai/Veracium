"""Portable export/import: lossless round-trip, idempotency, remap, versioning."""

import tempfile

import pytest

from veracium import Memory, MemoryConfig
from veracium.portability import export_memory, import_memory

from tests.test_compile_gate import RoleFake, EXTRACT, _prime


def test_export_import_round_trip_is_lossless():
    with tempfile.TemporaryDirectory() as d:
        mem, _ = _prime(d)   # grounded fact + quarantined claim + use_only inference
        src = mem.store
        r = export_memory(src, "u", f"{d}/u.jsonl")
        assert r["edges"] >= 3 and r["episodes"] == 2

        dst = Memory(llm=RoleFake(EXTRACT),
                     config=MemoryConfig(db_path=f"{d}/dst.db")).store
        imp = import_memory(dst, f"{d}/u.jsonl")
        assert imp["edges"] == r["edges"] and imp["episodes"] == r["episodes"]
        assert imp["skipped"] == 0

        # everything survives byte-for-byte: ids, provenance, disclosure
        src_edges = {e.id: e for e in src.edges("u", active_only=False)}
        dst_edges = {e.id: e for e in dst.edges("u", active_only=False)}
        assert src_edges.keys() == dst_edges.keys()
        for eid, se in src_edges.items():
            de = dst_edges[eid]
            assert (se.object, se.relation, se.quarantined, se.use_only,
                    se.assertable, se.provenance.disclosure,
                    se.provenance.author_of_evidence) == \
                   (de.object, de.relation, de.quarantined, de.use_only,
                    de.assertable, de.provenance.disclosure,
                    de.provenance.author_of_evidence)
        assert {ep.id for ep in src.episodes("u")} == {ep.id for ep in dst.episodes("u")}

        # idempotent: importing again changes nothing
        again = import_memory(dst, f"{d}/u.jsonl")
        assert again["edges"] == 0 and again["episodes"] == 0
        assert again["skipped"] == imp["edges"] + imp["episodes"]
        mem.close(); dst.close()


def test_import_remaps_user_and_rejects_bad_files():
    with tempfile.TemporaryDirectory() as d:
        mem, _ = _prime(d)
        export_memory(mem.store, "u", f"{d}/u.jsonl")
        imp = import_memory(mem.store, f"{d}/u.jsonl", user_id="u2")
        assert imp["user_id"] == "u2" and imp["edges"] > 0
        assert all(e.user_id == "u2" for e in mem.store.edges("u2", active_only=False))

        with open(f"{d}/bad.jsonl", "w") as f:
            f.write('{"kind": "something-else"}\n')
        with pytest.raises(ValueError, match="not a Veracium export"):
            import_memory(mem.store, f"{d}/bad.jsonl")

        with open(f"{d}/future.jsonl", "w") as f:
            f.write('{"kind": "veracium-export", "version": 99, "user_id": "u"}\n')
        with pytest.raises(ValueError, match="newer"):
            import_memory(mem.store, f"{d}/future.jsonl")
        mem.close()


def test_cli_export_import():
    from veracium.cli import main
    with tempfile.TemporaryDirectory() as d:
        mem, _ = _prime(d)
        n_edges = len(mem.store.edges("u", active_only=False))
        mem.close()
        assert main(["export", f"{d}/out.jsonl", "--user", "u", "--db", f"{d}/t.db"]) == 0
        assert main(["import", f"{d}/out.jsonl", "--user", "carol", "--db", f"{d}/t2.db"]) == 0
        from veracium.store.sqlite import SqliteStore
        s2 = SqliteStore(f"{d}/t2.db")
        assert len(s2.edges("carol", active_only=False)) == n_edges
        s2.close()
