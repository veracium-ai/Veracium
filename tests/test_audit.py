"""Opt-in operation audit log: every op leaves a line; no memory content leaks."""

import json
import tempfile

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium.audit import AuditLog


def _fake(prompt, *, system=None, role="compile", json_schema=None):
    if role == "distill":
        return json.dumps({"triples": [{"subject": "user", "relation": "has_diet",
                                        "object": "vegetarian", "volatility": "permanent"}],
                           "episode": "User said they are vegetarian."})
    return "ok"


def test_audit_records_every_operation_content_free():
    with tempfile.TemporaryDirectory() as d:
        log = AuditLog(f"{d}/audit.jsonl")
        mem = Memory(llm=_fake, audit=log,
                     config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
        mem.remember("alice", "USER: I'm vegetarian.", date="2026-07-01")
        mem.recall("alice", "lunch?")
        mem.answer("alice", "diet?")
        mem.maintain("alice")
        fact = mem.store.edges("alice")[0]
        mem.confirm("alice", fact.id)
        mem.dispute("alice", fact.id, reason="changed my mind")
        mem.export_memory("alice", f"{d}/a.jsonl")
        mem.import_memory(f"{d}/a.jsonl", user_id="bob")
        mem.forget("alice")

        ops = [e["op"] for e in log.entries()]
        # answer() recalls internally — the audit records that honestly
        assert ops == ["ingest", "recall", "recall", "answer", "maintain",
                       "feedback", "feedback", "export", "import", "forget"]
        assert all(e["user_id"] == "alice" for e in log.entries()
                   if e["op"] not in ("import",))
        assert log.entries(user_id="bob", op="import")[0]["edges"] == 1
        assert all("ts" in e for e in log.entries())

        # content-free: no memory text in the log, ever
        raw = open(f"{d}/audit.jsonl").read()
        assert "vegetarian" not in raw and "lunch" not in raw

        # an audit sink must never break memory
        class Broken:
            def record(self, *a, **k):
                raise RuntimeError("disk full")
        mem.audit = Broken()
        try:
            mem.remember("alice", "USER: still vegetarian.", date="2026-07-02")
        except RuntimeError as e:
            raise AssertionError("audit failure broke remember()") from e
        mem.close()
