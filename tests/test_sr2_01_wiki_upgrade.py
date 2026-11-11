"""SR2-01 (shipped-changes round 2, a patch-release blocker): a wiki cached before 0012-v2 kept serving its code-owned
empty-input body after upgrade, above a verified fact in the same response.

The reviewer's reproduction: under round 1's code, remember one third-party claim and recall (the compiler caches
"(no verified facts yet)" without a model call); reopen under the new code, remember "I live in Berlin." and recall:
the old header was served, `needs_recompile` false, policy digest db45cc67acf9f302 before and after. Research's stage 1
(S1): the class is older than round 1. 2f3899be (v0.28.0) replaced a MODEL-written empty body with the literal without
a bump, so a 0.27.x cache survived too. Both legacy bodies are frozen stores written by the released code itself
(specs/evidence/sr2-01/build_legacy_wiki_stores.py); the cells copy them and never open the frozen files in place.

Found in the fix: a FRESH store had the same contradiction. The empty body cached at one read survived a grounded write
below `wiki_recompile_after_writes`, since the threshold lets a model summary lag. The code-owned empty body is a
statement that the view held no verified fact, so any write since makes it stale (compile.needs_recompile).
"""
import ast
import json
import pathlib
import shutil
import sqlite3

import pytest

from veracium import EvidenceAuthor, EvidenceContext, Memory, MemoryConfig
from veracium import compile as _compile
from veracium import budgets as _budgets

EVIDENCE = pathlib.Path(__file__).resolve().parent.parent / "specs" / "evidence" / "sr2-01"
OLD_DIGEST = "db45cc67acf9f302"          # the default-config digest at every release v0.27.1 … v0.31.0 (0012-v1)
TAGS = ("v0.31.0", "v0.27.1")
LEGACY_BODY = {"v0.31.0": "(no verified facts yet)", "v0.27.1": "Document is empty pending user information"}


class Stub:
    """A direct user statement extracts Berlin; a compile is counted and answers with the fact."""
    def __init__(self):
        self.compile_calls = 0

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            return json.dumps({"triples": [{"subject": "user", "relation": "located_at", "object": "Berlin",
                                            "volatility": "durable"}], "episode": "The user lives in Berlin.",
                               "instructions": []})
        self.compile_calls += 1
        return "The user lives in Berlin."


def _row(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return c.execute("SELECT text, store_version FROM wiki WHERE user_id='u'").fetchone()
    finally:
        c.close()


def _legacy(tmp_path, tag):
    """A writable copy of the frozen store, its legacy row asserted from the bytes before anything opens it."""
    dst = tmp_path / f"{tag}.sqlite"
    shutil.copy2(EVIDENCE / f"legacy-empty-wiki-{tag}.sqlite", dst)
    text, _ = _row(dst)
    assert text.startswith(f"{_compile._ENVELOPE}{OLD_DIGEST}\n{LEGACY_BODY[tag]}\n"), text[:80]
    return dst


def _mem(db, llm):
    return Memory(llm=llm, config=MemoryConfig(db_path=str(db), require_source_id=False))


def _berlin(m):
    m.remember("u", "I live in Berlin.", date="2026-11-02", context=EvidenceContext.direct())
    assert any(e.assertable and e.object == "Berlin" for e in m.store.edges("u"))


@pytest.mark.parametrize("tag", TAGS)
def test_sr2_01_the_frozen_stores_are_the_released_codes_empty_compile(tag):
    """The fixtures' recorded facts, re-read from their bytes: each holds one wiki row under the OLD default digest with
    its legacy body, written by the tag named, and the current digest is not that one (the bump re-keys it)."""
    rec = json.loads((EVIDENCE / "legacy-empty-wiki.json").read_text())[tag]
    text, at = _row(EVIDENCE / f"legacy-empty-wiki-{tag}.sqlite")
    assert rec["tag"] == tag and rec["policy_digest"] == OLD_DIGEST and rec["body_first_line"] == LEGACY_BODY[tag]
    assert text == f"{_compile._ENVELOPE}{OLD_DIGEST}\n{rec['body']}" and at == rec["version_at_compile"]
    assert _compile._policy_digest(MemoryConfig().relations) != OLD_DIGEST


@pytest.mark.parametrize("tag", TAGS)
def test_sr2_01_the_reviewers_sequence_does_not_serve_the_legacy_body(tmp_path, tag):
    """The reviewer's sequence: open the old store under this code, remember a direct statement (one write, below the
    recompilation threshold), recall. The legacy body is gone and the verified fact is compiled."""
    llm = Stub()
    m = _mem(_legacy(tmp_path, tag), llm)
    _berlin(m)
    ctx = m.recall("u", "where does the user live", semantic=False).context
    m.close()
    assert LEGACY_BODY[tag] not in ctx, ctx[:200]
    assert _compile.EMPTY_GROUNDED_BODY not in ctx, ctx[:200]
    assert ctx.startswith("The user lives in Berlin.") and "located_at: Berlin" in ctx, ctx[:200]
    assert llm.compile_calls == 1


@pytest.mark.parametrize("tag", TAGS)
def test_sr2_01_a_read_between_the_upgrade_and_the_grounded_write(tmp_path, tag):
    """A read FIRST: the re-keyed empty input compiles to the current empty body WITHOUT a model call; then the
    grounded write (below the threshold) makes that body stale, and the next read compiles the fact."""
    llm = Stub()
    m = _mem(_legacy(tmp_path, tag), llm)
    first = m.recall("u", "where does the user live", semantic=False).context
    assert first.startswith(_compile.EMPTY_GROUNDED_BODY) and LEGACY_BODY[tag] not in first, first[:200]
    assert llm.compile_calls == 0, "the empty-input recompile must not call the model"
    _berlin(m)
    second = m.recall("u", "where does the user live", semantic=False).context
    m.close()
    assert _compile.EMPTY_GROUNDED_BODY not in second and second.startswith("The user lives in Berlin."), second[:200]
    assert llm.compile_calls == 1


def _no_llm(*a, **k):
    raise AssertionError("a provider-free reader must not call a model")


_no_llm._veracium_no_llm = True


@pytest.mark.parametrize("tag", TAGS)
def test_sr2_01_a_provider_free_reader_of_a_legacy_row_gets_the_stale_notice(tmp_path, tag):
    """The provider-free path (I10l) over a legacy row: the stale notice, never the legacy body, never a model."""
    db = _legacy(tmp_path, tag)
    m = _mem(db, Stub())
    body = _compile.ensure_wiki(m.store, _no_llm, "u", m.config.wiki_recompile_after_writes, m.config.relations)
    m.close()
    assert body == _budgets.STALE_WIKI_NOTICE, body


def test_sr2_01_a_fresh_cached_empty_body_is_stale_after_any_write(tmp_path):
    """Found in the fix, on a fresh store with no upgrade: a third-party claim and a read cache the empty body; one
    grounded write later the next read must not serve it above the verified fact."""
    llm = Stub()
    m = _mem(tmp_path / "fresh.db", llm)
    m.remember("u", "The user lives in Berlin.", date="2026-11-01", author=EvidenceAuthor.THIRD_PARTY)
    assert m.recall("u", "where does the user live", semantic=False).context.startswith(_compile.EMPTY_GROUNDED_BODY)
    assert llm.compile_calls == 0
    _berlin(m)
    ctx = m.recall("u", "where does the user live", semantic=False).context
    m.close()
    assert _compile.EMPTY_GROUNDED_BODY not in ctx and ctx.startswith("The user lives in Berlin."), ctx[:200]
    assert llm.compile_calls == 1


def test_sr2_01_a_model_written_body_below_the_threshold_is_still_served(tmp_path):
    """The honest probe: a MODEL summary keeps its threshold. A grounded store compiles once; one more write, below the
    threshold, and the next read is served from the cache with no second compile (no spurious recompiles)."""
    llm = Stub()
    m = _mem(tmp_path / "model.db", llm)
    _berlin(m)
    assert m.recall("u", "where does the user live", semantic=False).context.startswith("The user lives in Berlin.")
    assert llm.compile_calls == 1
    m.remember("u", "I live in Berlin.", date="2026-11-03", context=EvidenceContext.direct())
    m.recall("u", "where does the user live", semantic=False)
    m.close()
    assert llm.compile_calls == 1


# The pairing gate. (policy version) -> (the code-owned empty body, the branch that selects it). The empty body and its
# selection changed twice without a bump (2f3899be; SR1-03), so this cell refuses BY NAME when either moves while the
# version stays. Change either: bump compile._CONTENTION_POLICY_VERSION, add its row here, add an upgrade fixture.
# Limit: the gate reads compile_wiki's ONE `raw = <body> if <condition> else <model>` selection; a second code-owned
# body written by another statement would need its own row (research's stage-1 census: there is one, 2026-11-11).
PAIRED = {"0012-v2": {"body": "(no verified facts in this view)", "condition": "not edges and not episodes",
                      "selected": "EMPTY_GROUNDED_BODY"}}


def _selection():
    tree = ast.parse(pathlib.Path(_compile.__file__).read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "compile_wiki")
    found = [n.value for n in ast.walk(fn) if isinstance(n, ast.Assign) and len(n.targets) == 1
             and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "raw" and isinstance(n.value, ast.IfExp)]
    assert len(found) == 1, f"compile_wiki must hold exactly one `raw = … if … else …` selection, found {len(found)}"
    return found[0].test, found[0].body


def _same(node, source):
    """The recorded SOURCE parsed by this interpreter, compared node for node: ast.dump's field set differs across
    3.10-3.14, so both sides are dumped by the same interpreter and the difference cancels."""
    return ast.dump(node) == ast.dump(ast.parse(source, mode="eval").body)


def test_sr2_01_the_policy_version_is_paired_with_the_empty_body_and_its_branch():
    version = _compile._CONTENTION_POLICY_VERSION
    assert version in PAIRED, (f"_CONTENTION_POLICY_VERSION is {version!r}, which has no recorded row: record its "
                               f"empty body and selection here, with an upgrade fixture")
    want = PAIRED[version]
    test, body = _selection()
    assert _compile.EMPTY_GROUNDED_BODY == want["body"], (
        f"EMPTY_GROUNDED_BODY changed under policy {version}: bump _CONTENTION_POLICY_VERSION and re-record, or a "
        f"cached wiki keeps serving the old body (SR2-01)")
    assert _same(test, want["condition"]) and _same(body, want["selected"]), (
        f"the empty-input selection changed under policy {version} ({ast.unparse(test)!r} -> {ast.unparse(body)!r}): "
        f"bump _CONTENTION_POLICY_VERSION and re-record (2f3899be changed the branch, not only the words)")
