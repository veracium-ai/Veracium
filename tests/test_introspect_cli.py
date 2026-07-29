"""introspect() transparency view + the recall/remember/introspect CLI verbs."""

import json
import tempfile

from veracium import Memory, MemoryConfig, EvidenceAuthor
from veracium.cli import main as cli_main


class Fake:
    def __init__(self, scripts):
        self._scripts = list(scripts)

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill" and self._scripts:
            return json.dumps(self._scripts.pop(0))
        return "## USER MODEL\n- test wiki"


def _seeded_mem(db):
    mem = Memory(llm=Fake([
        {"triples": [
            {"subject": "user", "relation": "has_pet", "object": "cat Miso"},
            {"subject": "user", "relation": "prefers", "object": "concise answers"}],
         "episode": "User shared pet and preference."},
        {"triples": [
            {"subject": "user", "relation": "prefers", "object": "detailed answers"}],
         "episode": "User switched preference."},
        {"triples": [
            {"subject": "org:quickclaim", "relation": "third_party_claim",
             "object": "user owes $2,400"}],
         "episode": "Received a collection email."},
    ]), config=MemoryConfig(db_path=db, wiki_recompile_after_writes=0))
    mem.remember("ida", "I have a cat named Miso and I like concise answers")
    mem.remember("ida", "Actually, give me detailed answers")
    mem.remember("ida", "email from quickclaim", author=EvidenceAuthor.THIRD_PARTY,
                 event_type="email")
    return mem


def test_introspect_summary_counts():
    with tempfile.TemporaryDirectory() as d:
        mem = _seeded_mem(f"{d}/t.db")
        out = mem.introspect("ida")
        assert out["facts"] == 2
        assert out["unverified_claims"] == 1
        assert out["by_relation"] == {"has_pet": 1, "prefers": 1}
        assert out["by_author"] == {"third_party": 1, "user": 2}
        assert out["by_disclosure"]["quarantined"] == 1
        assert out["retired"] == {"superseded": 1}
        assert out["episodes"]["interaction"] == 3
        assert out["first_observed"] and out["last_observed"]
        json.dumps(out)  # JSON-able throughout
        mem.close()


def test_introspect_categories_render_provenance():
    with tempfile.TemporaryDirectory() as d:
        mem = _seeded_mem(f"{d}/t.db")
        out = mem.introspect("ida", mode="categories")
        assert set(out["categories"]) == {"has_pet", "prefers", "third_party_claim"}
        claim_line = out["categories"]["third_party_claim"][0]
        assert "UNVERIFIED third-party claim" in claim_line  # flagged exactly as recall shows it
        assert out["categories"]["prefers"] == [
            l for l in out["categories"]["prefers"] if "detailed" in l
        ]  # superseded value not listed among current facts
        mem.close()


def test_introspect_unknown_mode():
    with tempfile.TemporaryDirectory() as d:
        mem = _seeded_mem(f"{d}/t.db")
        try:
            mem.introspect("ida", mode="everything")
            raise AssertionError("expected ValueError")
        except ValueError:
            pass
        mem.close()


def test_cli_recall_and_introspect_are_store_only(capsys):
    """The store-only verbs must work with no provider configured at all."""
    with tempfile.TemporaryDirectory() as d:
        db = f"{d}/t.db"
        mem = _seeded_mem(db)
        mem.close()

        assert cli_main(["recall", "--user", "ida", "--db", db]) == 0
        briefing = capsys.readouterr().out
        assert briefing.strip()  # proactive briefing rendered

        assert cli_main(["recall", "--user", "ida", "--db", db, "detailed answers"]) == 0
        out = capsys.readouterr().out
        assert "detailed answers" in out
        assert "$2,400" not in out.split("UNVERIFIED")[0]  # claim only in flagged section

        assert cli_main(["introspect", "--user", "ida", "--db", db, "--json"]) == 0
        rep = json.loads(capsys.readouterr().out)
        assert rep["facts"] == 2

        assert cli_main(["introspect", "--user", "ida", "--db", db, "--categories"]) == 0
        assert "[has_pet]" in capsys.readouterr().out


def test_cli_remember_reads_stdin(capsys, monkeypatch):
    """`veracium remember - ` ingests stdin; patched builder supplies the fake LLM."""
    import io
    import veracium.cli as cli_mod
    with tempfile.TemporaryDirectory() as d:
        db = f"{d}/t.db"
        monkeypatch.setattr(cli_mod, "_build_llm", lambda *a, **k: Fake([
            {"triples": [{"subject": "user", "relation": "has_pet",
                          "object": "cat Miso"}],
             "episode": "User has a cat."}]))
        monkeypatch.setattr("sys.stdin", io.StringIO("I have a cat named Miso"))
        assert cli_main(["remember", "--user", "ida", "--db", db, "-"]) == 0
        assert "1 facts" in capsys.readouterr().out

        assert cli_main(["introspect", "--user", "ida", "--db", db, "--json"]) == 0
        assert json.loads(capsys.readouterr().out)["facts"] == 1
