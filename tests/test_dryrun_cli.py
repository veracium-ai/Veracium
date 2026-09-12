"""`veracium remember --dry-run` (src/veracium/dryrun.py): a real ingest into a
snapshot copy, reported as a delta. Every assertion compares the dry run's report
against what the real write then does to the same store with the same answer —
the construction's own claim — and proves the original file is untouched."""

import hashlib
import json
import pathlib
import tempfile

from veracium import Memory, MemoryConfig, EvidenceAuthor
from veracium import dryrun
from veracium.cli import main as cli_main
from veracium.schema import EvidenceContext


class Fake:
    """A scripted provider: the same answer for every distill call, so a dry run
    and the real write that follows consume identical answers."""
    def __init__(self, answer):
        self.answer = answer
        self.calls = 0

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            self.calls += 1
            return self.answer if isinstance(self.answer, str) else json.dumps(self.answer)
        return "## USER MODEL\n- test wiki"


U = "ida"


def _seed(db):
    mem = Memory(llm=Fake({"triples": [{"subject": "user", "relation": "prefers", "object": "concise answers"}],
                           "episode": "User shared a preference."}),
                 config=MemoryConfig(db_path=db, wiki_recompile_after_writes=0))
    mem.remember(U, "I like concise answers", date="2026-09-01", context=EvidenceContext.direct())
    mem.close()
    return db


def _sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def test_a_supersession_is_reported_and_the_store_is_untouched():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        before = _sha(db)
        llm = Fake({"triples": [{"subject": "user", "relation": "prefers", "object": "detailed answers"}],
                    "episode": "User switched preference."})
        dr = dryrun.run(db, llm, U, "Actually, give me detailed answers", author=EvidenceAuthor.USER,
                        date="2026-09-02", context=EvidenceContext.direct())
        assert dr.usable and dr.error is None and llm.calls == 1
        assert _sha(db) == before and sorted(p.name for p in pathlib.Path(d).iterdir()) == ["t.db"]
        assert not [p for p in pathlib.Path(tempfile.gettempdir()).glob("veracium-dryrun-*")]
        assert [e["object"] for e in dr.new_edges] == ["detailed answers"]
        new = dr.new_edges[0]
        assert new["provenance.disclosure"] == "mentionable" and new["provenance.author_of_evidence"] == "user"
        assert new["supersedes"], "the new fact should name the fact it supersedes"
        assert [c["fact"] for c in dr.changed_edges] == ["user prefers concise answers"]
        moved = {k: (b, a) for k, b, a in dr.changed_edges[0]["changed"]}
        assert moved["invalidation_reason"] == (None, "superseded") and moved["invalidated_at"][1]
        assert dr.result["facts"] == 1 and dr.result["supersessions"] == 1 and dr.new_episodes == 1
        text = dryrun.render(dr)
        assert "nothing written" in text and "+ user prefers detailed answers" in text and "supersedes" in text
        assert "~ user prefers concise answers" in text and "invalidation_reason: — -> superseded" in text
        json.dumps(dryrun.to_json(dr), default=str)
        # THE CONSTRUCTION'S CLAIM: the real write does exactly what the dry run said
        mem = Memory(llm=Fake(llm.answer), config=MemoryConfig(db_path=db, wiki_recompile_after_writes=0))
        r = mem.remember(U, "Actually, give me detailed answers", date="2026-09-02", context=EvidenceContext.direct())
        assert {k: r[k] for k in ("facts", "quarantined", "supersessions")} == \
            {k: dr.result[k] for k in ("facts", "quarantined", "supersessions")}
        live = {e.object: e for e in mem.store.edges(U, active_only=False)}
        assert live["detailed answers"].supersedes == live["concise answers"].id
        assert live["concise answers"].invalidation_reason == "superseded"
        mem.close()


def test_third_party_quarantine_and_the_relay_floor_are_reported():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        llm = Fake({"triples": [{"subject": "org:quickclaim", "relation": "third_party_claim",
                                 "object": "user owes $2,400"}], "episode": "A collection email."})
        dr = dryrun.run(db, llm, U, "email from quickclaim", author=EvidenceAuthor.THIRD_PARTY,
                        event_type="email", source_id="quickclaim-inbox", date="2026-09-03")
        assert dr.usable and len(dr.new_edges) == 1
        e = dr.new_edges[0]
        assert e["quarantined"] and e["provenance.disclosure"] == "quarantined" and dr.result["quarantined"] == 1
        assert "[quarantined; author=third_party; derived_from=third_party; quarantined, ungrounded]" in dryrun.render(dr)
        # the 0026 relay floor: a user fact whose note says it was relayed is demoted
        # MENTIONABLE -> USE_ONLY and the counter says so
        llm2 = Fake({"triples": [{"subject": "user", "relation": "has_condition", "object": "needs rest",
                                  "note": "my doctor said to rest"}], "episode": "User relayed advice."})
        dr2 = dryrun.run(db, llm2, U, "my doctor said I need rest", author=EvidenceAuthor.USER,
                         date="2026-09-04", context=EvidenceContext.direct())
        assert dr2.usable and dr2.result["agreement_floored"] == 1
        assert dr2.new_edges[0]["provenance.disclosure"] == "use_only"
        assert "agreement_floored=1" in dryrun.render(dr2)


def test_an_unusable_extraction_is_reported_with_its_degrade_record():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        before = _sha(db)
        dr = dryrun.run(db, Fake("I cannot help with that."), U, "anything", author=EvidenceAuthor.USER,
                        date="2026-09-05")
        assert not dr.usable and dr.result["unparseable"] and dr.new_edges == []
        assert [g["degrade"] for g in dr.degrades] == ["unparseable"] and dr.degrades[0]["cause"] == "no_json"
        text = dryrun.render(dr)
        assert "UNPARSEABLE" in text and "degrade    op=" in text and "cause=no_json" in text
        assert _sha(db) == before
        # a shape failure: triples present but not a list — extraction_unusable, one record
        dr2 = dryrun.run(db, Fake({"triples": "user likes tea", "episode": "x"}), U, "anything",
                         author=EvidenceAuthor.USER, date="2026-09-05")
        assert not dr2.usable and dr2.result["extraction_unusable"] and not dr2.result.get("unparseable")
        assert [(g["degrade"], g["cause"]) for g in dr2.degrades] == [("primary_failed", "shape")]


def test_a_provider_that_raises_is_reported_by_class_only():
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        class Boom(Fake):
            def __call__(self, prompt, **kw):
                if kw.get("role") == "distill":
                    raise RuntimeError("the secret is s3cr3t")
                return "wiki"
        dr = dryrun.run(db, Boom(None), U, "anything", author=EvidenceAuthor.USER)
        assert not dr.usable and dr.error == "RuntimeError"
        assert "s3cr3t" not in dryrun.render(dr) and "s3cr3t" not in json.dumps(dryrun.to_json(dr), default=str)


def test_a_missing_store_is_dry_run_as_a_fresh_one_and_never_created():
    with tempfile.TemporaryDirectory() as d:
        db = f"{d}/new.db"
        dr = dryrun.run(db, Fake({"triples": [{"subject": "user", "relation": "lives_in", "object": "Porto"}],
                                  "episode": "Moved."}), U, "I moved to Porto", author=EvidenceAuthor.USER,
                        context=EvidenceContext.direct())
        assert dr.usable and not dr.existing_store and len(dr.new_edges) == 1
        assert not pathlib.Path(db).exists() and list(pathlib.Path(d).iterdir()) == []
        assert "no store there yet" in dryrun.render(dr)


def test_the_cli_flag_round_trips_and_exit_codes_follow_usability(capsys, monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        db = _seed(f"{d}/t.db")
        before = _sha(db)
        import veracium.cli as cli
        answer = {"triples": [{"subject": "user", "relation": "prefers", "object": "detailed answers"}],
                  "episode": "User switched preference."}
        monkeypatch.setattr(cli, "_build_llm", lambda *a, **k: Fake(answer))
        assert cli_main(["remember", "--user", U, "Actually, detailed answers", "--dry-run", "--db", db,
                         "--date", "2026-09-02"]) == 0
        out = capsys.readouterr().out
        assert out.startswith("dry run — nothing written") and "+ user prefers detailed answers" in out
        assert _sha(db) == before
        assert cli_main(["remember", "--user", U, "x", "--dry-run", "--json", "--db", db]) == 0
        doc = json.loads(capsys.readouterr().out)
        assert doc["usable"] and doc["new_edges"][0]["object"] == "detailed answers"
        monkeypatch.setattr(cli, "_build_llm", lambda *a, **k: Fake("prose, not json"))
        assert cli_main(["remember", "--user", U, "x", "--dry-run", "--db", db]) == 1
        assert "UNPARSEABLE" in capsys.readouterr().out
        assert _sha(db) == before
