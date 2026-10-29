"""specs/0047 §4d, INV-R18 — R-II round 2's RII-01: the wiki body a recall serves and the call's challenge snapshot
come from ONE state (compile.bound_wiki), so a body never asserts a fact the same call reports as challenged.

The reviewer's counterexample was the cached path; research's stage-1 read (READ-RII-phase0-stage1.md B1) showed the
window open on all three ensure_wiki paths, and answering its question showed a fourth, sequential instance: an
IMPORTED challenge left the cached wiki in place. Each cell interleaves at bound_wiki's own snapshot read and asserts
that it did (research's trap: compile_wiki reads the snapshot itself, and a probe that interleaves there measures the
compile's fence, not this window), and asserts the path the call took.

The census below holds the bind's precondition: every write of a reply evicts the user's wiki in its own function.
Confirmations are out of its scope by the withheld rule itself: ChallengeSnapshot.withheld reads only the open
challenges (`challenged`), never `confirmation_origins`, so a confirmation cannot make a cached body assert anything
the snapshot withholds.
"""
import ast
import pathlib
import re
import sys
from datetime import datetime, timezone

import pytest

from veracium import Memory, MemoryConfig, budgets
from veracium import compile as compile_mod
from veracium.schema import DISPOSITIONED_REASONS, Disclosure, Edge, Episode, EvidenceAuthor, Provenance, wiki_drops_on

U = "bind-user"
FACT = "Toronto"
WIKI_LINE = "User has a fact about Toronto."   # the provider's body: the wiki, not an edge line, asserts it
SRC = pathlib.Path(compile_mod.__file__).resolve().parent


def _edge(eid, obj, rel="located_at"):
    return Edge(id=eid, user_id=U, subject="user", relation=rel, object=obj, provenance=Provenance(
        author_of_evidence=EvidenceAuthor.USER, evidence_ref="bind", disclosure=Disclosure.MENTIONABLE))


def _cfg(path, after=1):
    return MemoryConfig(db_path=str(path), wiki_recompile_after_writes=after, require_source_id=False, scope_groups={})


def _bind_site_hook(monkeypatch, store, before=None, after=None):
    """Wrap the store's snapshot read; run `before`/`after` around it ONLY when bound_wiki is the caller. Returns the
    list of callers seen, so a cell can assert the interleave happened at the window under test."""
    real, callers = store.challenge_snapshot, []

    def hooked(user_id):
        f = sys._getframe(1).f_code
        site = f"{pathlib.Path(f.co_filename).name}:{f.co_name}"
        callers.append(site)
        bind = site == "compile.py:bound_wiki"
        if bind and before is not None:
            before(len([c for c in callers if c == site]))
        snap = real(user_id)
        if bind and after is not None:
            after(len([c for c in callers if c == site]))
        return snap
    monkeypatch.setattr(store, "challenge_snapshot", hooked)
    return callers


def _record_publishes(monkeypatch, store):
    real, published = store.set_wiki, []

    def rec(*a, **k):
        ok = real(*a, **k)
        published.append(bool(ok))
        return ok
    monkeypatch.setattr(store, "set_wiki", rec)
    return published


def _provider(state):
    def provider(prompt, *, role="compile", **kw):
        if role != "compile":
            return "ok"
        state["compiles"] = state.get("compiles", 0) + 1
        if state.get("during_compile") and not state.get("done"):
            state["done"] = True
            state["during_compile"]()
        facts = [f for f in ("Toronto", "Lisbon", "Kittiwake", "Puffinry") if f in prompt]
        return " ".join(f"User has a fact about {f}." for f in facts) or "No current location fact."
    return provider


# ================================================================================ INV-R18: the window, on every path
@pytest.mark.parametrize("path", ["cached", "compiled_published", "compiled_unpublished"])
def test_a_challenge_before_the_bound_snapshot_is_never_asserted_by_the_body(tmp_path, monkeypatch, path):
    """A challenge committed after the body is read and before the call's snapshot: the inspection reports it and the
    body does not assert it, on the cached, the published-compile and the unpublished-compile paths.
    Mutant (07df8f8's recall): the body read before the snapshot is served as is — all three fail."""
    state = {}
    reader, writer = (Memory(llm=_provider(state), config=_cfg(tmp_path / "m.db")) for _ in range(2))
    try:
        reader.store.add_edge(_edge("location", FACT))
        if path == "cached":
            assert WIKI_LINE in reader.recall(U, FACT, semantic=False).grounded and reader.store.get_wiki(U) is not None
        if path == "compiled_unpublished":                 # a plain concurrent write during the compile
            state["during_compile"] = lambda: writer.store.add_edge(_edge("other", "tea", rel="prefers"))
        compiles = state.get("compiles", 0)
        published = _record_publishes(monkeypatch, reader.store)
        challenged, first = [], []

        def challenge(n):
            if not challenged:
                # the path the call's FIRST ensure_wiki took, read at the bound snapshot it precedes
                first.append((state.get("compiles", 0) - compiles, list(published)))
                challenged.append(writer.reply(U, "location", kind="challenge", text="Please withhold this."))
        callers = _bind_site_hook(monkeypatch, reader.store, before=challenge)
        r = reader.recall(U, FACT, semantic=False)
        assert challenged and "compile.py:bound_wiki" in callers, callers
        # the path really is the one named: the first ensure_wiki served the cache, published, or could not publish
        assert first == [{"cached": (0, []), "compiled_published": (1, [True]),
                          "compiled_unpublished": (1, [False])}[path]], first
        assert not r.inspection["location"].challenge_clear
        assert FACT not in r.grounded, r.grounded
    finally:
        reader.close()
        writer.close()


@pytest.mark.parametrize("path", ["cached", "compiled_published"])
def test_a_challenge_after_the_bound_snapshot_leaves_the_call_coherent(tmp_path, monkeypatch, path):
    """The control: a challenge committed right after the call's snapshot (same thread: no read window is held, so the
    writer never waits on this call). A compiled body is bound by its inputs against the call's snapshot, which
    predates the challenge: this call is clear and the body asserts the fact. A cached body's row is evicted before
    the bind re-reads it: the call recomputes, and its fresh snapshot withholds the fact both ways. Either way the
    body and the inspection agree, and the next call withholds."""
    state = {}
    reader, writer = (Memory(llm=_provider(state), config=_cfg(tmp_path / "m.db")) for _ in range(2))
    try:
        reader.store.add_edge(_edge("location", FACT))
        if path == "cached":
            reader.recall(U, FACT, semantic=False)
            assert reader.store.get_wiki(U) is not None
        done = []

        def challenge(n):
            if not done:
                done.append(writer.reply(U, "location", kind="challenge", text="Please withhold this."))
        callers = _bind_site_hook(monkeypatch, reader.store, after=challenge)
        r1 = reader.recall(U, FACT, semantic=False)
        assert done and "compile.py:bound_wiki" in callers
        clear = r1.inspection["location"].challenge_clear
        assert clear == (WIKI_LINE in r1.grounded), r1.grounded            # coherent, whichever state it read
        assert clear == {"compiled_published": True, "cached": False}[path]
        assert callers.count("compile.py:bound_wiki") == {"compiled_published": 1, "cached": 2}[path], callers
        monkeypatch.undo()
        r2 = reader.recall(U, FACT, semantic=False)
        assert not r2.inspection["location"].challenge_clear and FACT not in r2.grounded, r2.grounded
    finally:
        reader.close()
        writer.close()


def test_a_resolve_before_the_bound_snapshot_is_served_from_a_fresh_body(tmp_path, monkeypatch):
    """The resolve direction: a body compiled while the fact was challenged OMITS it (it asserts nothing false); a
    resolve committed before the call's snapshot evicts that body, so the call serves one that carries the fact, and
    the inspection agrees (clear)."""
    state = {}
    reader, writer = (Memory(llm=_provider(state), config=_cfg(tmp_path / "m.db", after=10**6)) for _ in range(2))
    try:
        reader.store.add_edge(_edge("location", FACT))
        cid = reader.reply(U, "location", kind="challenge", text="Please withhold this.")["reply_id"]
        omitted = reader.recall(U, FACT, semantic=False)
        assert WIKI_LINE not in omitted.grounded and reader.store.get_wiki(U) is not None
        done = []

        def resolve(n):
            if not done:
                done.append(writer.reply(U, "location", kind="resolve", target=cid))
        callers = _bind_site_hook(monkeypatch, reader.store, before=resolve)
        r = reader.recall(U, FACT, semantic=False)
        assert done and "compile.py:bound_wiki" in callers
        assert r.inspection["location"].challenge_clear and WIKI_LINE in r.grounded, r.grounded
    finally:
        reader.close()
        writer.close()


def test_a_body_that_fails_its_bind_twice_is_the_disputed_notice(tmp_path, monkeypatch):
    """The retry is bounded: a challenge before each of the call's two bound snapshots (Toronto, then Lisbon, each a fact
    the body then drew on) leaves the disputed notice, never a body asserting either fact, and never a third compile."""
    state = {}
    reader, writer = (Memory(llm=_provider(state), config=_cfg(tmp_path / "m.db")) for _ in range(2))
    try:
        reader.store.add_edge(_edge("location", FACT))
        reader.store.add_edge(_edge("trip", "Lisbon", rel="visited"))
        targets = {1: "location", 2: "trip"}

        def challenge(n):
            if n in targets:
                writer.reply(U, targets.pop(n), kind="challenge", text="Please withhold this.")
        callers = _bind_site_hook(monkeypatch, reader.store, before=challenge)
        r = reader.recall(U, "Toronto Lisbon", semantic=False)
        assert callers.count("compile.py:bound_wiki") == 2 and not targets
        assert budgets.DISPUTED_DURING_COMPILE_NOTICE in r.grounded
        assert FACT not in r.grounded and "Lisbon" not in r.grounded, r.grounded
    finally:
        reader.close()
        writer.close()


# ================================================================================ INV-R18: redaction and erasure in the window
@pytest.mark.parametrize("path", ["compiled", "cached"])
@pytest.mark.parametrize("target", ["edge", "episode"])
def test_a_redaction_before_the_bound_snapshot_is_never_in_the_body(tmp_path, monkeypatch, path, target):
    """Research's R-II round 2 stage-2 probe: a redaction committed after the body is read and before the call's
    snapshot. A bind that reads only `withheld` passes it (a redacted, unchallenged record withholds nothing), and the
    body carries the redacted record — what 0041 round 10's fence forbids inside the compile, just after it. The
    compiled body is bound by its inputs' redaction too, edges and episodes; the cached body by its row (a redaction
    evicts). Mutant: the redaction clause dropped from the compiled bind."""
    state = {}
    reader, writer = (Memory(llm=_provider(state), config=_cfg(tmp_path / "m.db")) for _ in range(2))
    try:
        reader.store.add_edge(_edge("location", "Kittiwake"))
        reader.store.add_episode(Episode(id="ep-1", user_id=U, date="2026-10-21", summary="a trip to Puffinry",
                                         provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                               evidence_ref="bind")))
        token = {"edge": "Kittiwake", "episode": "Puffinry"}[target]
        if path == "cached":
            assert f"User has a fact about {token}." in reader.recall(U, token, semantic=False).grounded
            assert reader.store.get_wiki(U) is not None
        done = []

        def redact(n):
            if not done:
                done.append(writer.redact(U, reason="subject_request",
                                          **({"edge_id": "location"} if target == "edge" else {"episode_id": "ep-1"})))
        callers = _bind_site_hook(monkeypatch, reader.store, before=redact)
        r = reader.recall(U, token, semantic=False)
        assert done and "compile.py:bound_wiki" in callers, callers
        assert token not in r.grounded, r.grounded
    finally:
        reader.close()
        writer.close()


@pytest.mark.parametrize("path", ["compiled", "cached"])
def test_an_erasure_before_the_bound_snapshot_is_never_in_the_body(tmp_path, monkeypatch, path):
    """forget_user in the same window: the compiled body is bound by its inputs' presence (an erased edge is gone), the
    cached one by its row (erasure deletes it); either way the call answers. Mutant: the presence clause dropped from
    the compiled bind (the W9 clause then meets the erased edge: a crash, reported here as the cell's failure)."""
    state = {}
    reader, writer = (Memory(llm=_provider(state), config=_cfg(tmp_path / "m.db")) for _ in range(2))
    try:
        reader.store.add_edge(_edge("location", FACT))
        if path == "cached":
            assert WIKI_LINE in reader.recall(U, FACT, semantic=False).grounded
        done = []

        def erase(n):
            if not done:
                done.append(writer.forget(U))
        callers = _bind_site_hook(monkeypatch, reader.store, before=erase)
        try:
            r = reader.recall(U, FACT, semantic=False)
        except Exception as e:                       # the call must answer: an erased input is withheld, never a crash
            raise AssertionError(f"the erasure in the window crashed the call: {e!r}") from e
        assert done and "compile.py:bound_wiki" in callers, callers
        assert FACT not in r.grounded, r.grounded
    finally:
        reader.close()
        writer.close()


def test_an_erasure_before_the_bound_snapshot_withholds_an_episodes_only_body(tmp_path, monkeypatch):
    """Research's R-II round 2 landing read (L1): a body compiled in the call from EPISODES alone, then forget_user in
    the window. An edge-presence test holds vacuously over no edges; the bind reads the episodes' presence too.
    Mutant: the episode-presence clause dropped (L1's state at 6611c9b)."""
    state = {}
    reader, writer = (Memory(llm=_provider(state), config=_cfg(tmp_path / "m.db")) for _ in range(2))
    try:
        reader.store.add_episode(Episode(id="ep-1", user_id=U, date="2026-10-21", summary="a trip to Puffinry",
                                         provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                               evidence_ref="bind")))
        assert reader.store.edges(U, active_only=False, include_quarantined=True) == []
        done = []

        def erase(n):
            if not done:
                done.append(writer.forget(U))
        callers = _bind_site_hook(monkeypatch, reader.store, before=erase)
        r = reader.recall(U, "Puffinry", semantic=False)
        assert done and "compile.py:bound_wiki" in callers, callers
        assert "Puffinry" not in r.grounded, r.grounded
    finally:
        reader.close()
        writer.close()


def test_an_erasure_followed_by_writes_still_withholds_an_episodes_only_body(tmp_path, monkeypatch):
    """forget_user, then writes in the same window (the user's write counter climbs back): a bind keyed on the
    counter would pass this; presence does not. Mutant: the episode-presence clause dropped."""
    state = {}
    reader, writer = (Memory(llm=_provider(state), config=_cfg(tmp_path / "m.db", after=10**6)) for _ in range(2))
    try:
        reader.store.add_episode(Episode(id="ep-1", user_id=U, date="2026-10-21", summary="a trip to Puffinry",
                                         provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                               evidence_ref="bind")))
        done = []

        def erase_then_write(n):
            if not done:
                done.append(writer.forget(U))
                for i in range(5):
                    writer.store.add_edge(_edge(f"after-{i}", f"thing {i}", rel="likes"))
        callers = _bind_site_hook(monkeypatch, reader.store, before=erase_then_write)
        r = reader.recall(U, "Puffinry", semantic=False)
        assert done and "compile.py:bound_wiki" in callers, callers
        assert reader.store.store_version(U) >= 1
        assert "Puffinry" not in r.grounded, r.grounded
    finally:
        reader.close()
        writer.close()


# ================================================================================ 0004 W9 (INV-R18's window): invalidation
# "redacted" is the one key no invalidation writes (only a redaction does, 0041 §11.2): its window is
# test_a_redaction_before_the_bound_snapshot_is_never_in_the_body's, and the cell below holds the exclusion to that one key
INVALIDATION_REASONS = sorted(set(DISPOSITIONED_REASONS) - {"redacted"})


def test_w9_every_dispositioned_reason_but_redacted_is_an_invalidation_reason(tmp_path):
    s = Memory(llm=_provider({}), config=_cfg(tmp_path / "m.db")).store
    s.add_edge(_edge("location", FACT))
    with pytest.raises(ValueError, match="only a redaction writes"):
        s.invalidate_edge("location", datetime.now(timezone.utc), "redacted")
    assert set(DISPOSITIONED_REASONS) - set(INVALIDATION_REASONS) == {"redacted"} and wiki_drops_on("redacted")


@pytest.mark.parametrize("path", ["compiled_at_snapshot", "compiled_during_compile", "cached"])
@pytest.mark.parametrize("reason", INVALIDATION_REASONS)
def test_w9_a_revoking_invalidation_withholds_the_body_and_a_retaining_one_keeps_it(tmp_path, monkeypatch, path,
                                                                                    reason):
    """specs/0004 W9 (the owner's D10 ruling): a fact the body drew on, invalidated in the window — at the call's
    snapshot, or during the compile itself — withholds the body iff the reason drops the wiki by W1's rule
    (schema.wiki_drops_on, the function the store's eviction calls); W3's staleness and W8's absorption keep it. The
    cached path is the control: a dropping reason evicts the row (W1), a retaining one keeps row and body. Every key of
    DISPOSITIONED_REASONS, both sides. Mutants: the clause dropped (the drop cells fail); "any reason drops" (the
    retain cells fail); the store's eviction and the bind each switched to their own predicate (one side's cells
    fail)."""
    state = {}
    reader, writer = (Memory(llm=_provider(state), config=_cfg(tmp_path / "m.db")) for _ in range(2))
    try:
        reader.store.add_edge(_edge("location", FACT))
        invalidate = lambda: writer.store.invalidate_edge("location", datetime.now(timezone.utc), reason)
        done = []
        if path == "cached":
            assert WIKI_LINE in reader.recall(U, FACT, semantic=False).grounded and reader.store.get_wiki(U) is not None
        if path == "compiled_during_compile":
            state["during_compile"] = lambda: done.append(invalidate())
            callers = _bind_site_hook(monkeypatch, reader.store)
        else:
            def at_snapshot(n):
                if not done:
                    done.append(invalidate())
            callers = _bind_site_hook(monkeypatch, reader.store, before=at_snapshot)
        r = reader.recall(U, FACT, semantic=False)
        assert done and "compile.py:bound_wiki" in callers, callers
        drops = DISPOSITIONED_REASONS[reason] == "drop"
        assert drops == wiki_drops_on(reason), reason              # the registry and the rule agree, both sides
        assert (WIKI_LINE in r.grounded) is (not drops), (reason, path, r.grounded)
    finally:
        reader.close()
        writer.close()


# ================================================================================ INV-R18: the imported challenge (sequential)
@pytest.mark.parametrize("route", ["import", "local_reply"])
def test_a_challenge_admitted_after_a_cached_wiki_is_never_asserted_by_it(tmp_path, route):
    """No concurrency: a wiki cached on a fact, then a challenge of it admitted by an IMPORT (the file's record is
    skipped, its challenge act admitted) or written locally, under the default recompile threshold. Mutant (07df8f8's
    import): one bump and no eviction, so the cached body grounds the fact beside the withheld notice."""
    src = Memory(llm=_provider({}), config=_cfg(tmp_path / "a.db", after=8))
    src.store.add_edge(_edge("location", FACT))
    src.export_memory(U, tmp_path / "f0.jsonl")
    src.reply(U, "location", kind="challenge", text="Please withhold this.")
    src.export_memory(U, tmp_path / "f1.jsonl")
    src.close()
    dst = Memory(llm=_provider({}), config=_cfg(tmp_path / "b.db", after=8))
    try:
        dst.import_memory(tmp_path / "f0.jsonl", restore=True)
        assert WIKI_LINE in dst.recall(U, FACT, semantic=False).grounded and dst.store.get_wiki(U) is not None
        if route == "import":
            r1 = dst.import_memory(tmp_path / "f1.jsonl", restore=True)
            assert (r1["edges"], r1["skipped"], r1["replies"]) == (0, 1, 1), r1
        else:
            dst.reply(U, "location", kind="challenge", text="Please withhold this.")
        assert dst.store.get_wiki(U) is None              # evicted in the writer's own transaction
        r = dst.recall(U, FACT, semantic=False)
        assert not r.inspection["location"].challenge_clear and FACT not in r.grounded, r.grounded
    finally:
        dst.close()


# ================================================================================ INV-R18: the precondition, as a census
_WRITE = re.compile(r"\b(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|REPLACE\s+INTO|UPDATE|DELETE\s+FROM)\s+(\w+|\{\w*\})", re.I)
_EVICT = re.compile(r"DELETE\s+FROM\s+(?:wiki|\{wiki\})\s+WHERE\s+user_id\s*=\s*\?", re.I)


def _module_tuples(tree):
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) \
                and isinstance(n.value, ast.Tuple) and all(isinstance(e, ast.Constant) for e in n.value.elts):
            out[n.targets[0].id] = [e.value for e in n.value.elts]
    return out


def _sql_texts(fn, arg, loops, tuples):
    """Every SQL text `arg` can be, or None when the function's own source cannot resolve it. A placeholder bound by a
    `for` over a module-level tuple of names expands to each name (forget_user's erasure loop); any other placeholder
    stays `{}`, which the census treats as ANY table — the import's act loop writes `INSERT INTO {a['table']}`, and
    research's trap is that a literal match never sees it."""
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return [arg.value]
    if isinstance(arg, ast.JoinedStr):
        outs = [""]
        for v in arg.values:
            if isinstance(v, ast.Constant):
                outs = [o + v.value for o in outs]
            elif isinstance(v.value, ast.Name) and v.value.id in loops and loops[v.value.id] in tuples:
                outs = [o + "{" + t + "}" for o in outs for t in tuples[loops[v.value.id]]]
            else:
                outs = [o + "{}" for o in outs]
        return outs
    if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
        a, b = _sql_texts(fn, arg.left, loops, tuples), _sql_texts(fn, arg.right, loops, tuples)
        return None if a is None or b is None else [x + y for x in a for y in b]
    if isinstance(arg, ast.IfExp):
        a, b = _sql_texts(fn, arg.body, loops, tuples), _sql_texts(fn, arg.orelse, loops, tuples)
        return None if a is None or b is None else a + b
    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == "format":
        base = _sql_texts(fn, arg.func.value, loops, tuples)
        return None if base is None else [re.sub(r"\{[^}]*\}", "{}", b) for b in base]
    if isinstance(arg, ast.Name):
        parts = []
        for n in ast.walk(fn):
            tgt = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AugAssign) else []
            if any(isinstance(t, ast.Name) and t.id == arg.id for t in tgt):
                v = _sql_texts(fn, n.value, loops, tuples)
                if v is None:
                    return None
                parts += v
        return [" ".join(parts)] if parts else None
    return None


def reply_writer_census(source: str):
    """{function: (evicts, [(line, write)])} for every function whose SQL can write `replies`, and the (function,
    line) of every execute whose SQL the census cannot resolve (each refuses). Scope: one function is the unit; the
    shipped writers run their statements in one transaction per function, which the behaviour cells above exercise."""
    tree = ast.parse(source)
    tuples = _module_tuples(tree)
    writers, unresolved = {}, []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        loops = {f.target.id: f.iter.id for f in ast.walk(fn) if isinstance(f, ast.For)
                 and isinstance(f.target, ast.Name) and isinstance(f.iter, ast.Name)}
        evicts, writes = False, []
        for c in ast.walk(fn):
            if not (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                    and c.func.attr in ("execute", "executemany") and c.args):
                continue
            texts = _sql_texts(fn, c.args[0], loops, tuples)
            if texts is None:
                unresolved.append((fn.name, c.lineno))
                continue
            for t in texts:
                evicts = evicts or bool(_EVICT.search(t))
                writes += [(c.lineno, m.group(0)) for m in _WRITE.finditer(t)
                           if m.group(1).lower() in ("replies", "{replies}", "{}")]
        if writes:
            writers[fn.name] = (evicts, writes)
    return writers, unresolved


def _sqlite_source():
    return (SRC / "store" / "sqlite.py").read_text(encoding="utf-8")


def test_every_reply_writer_evicts_the_wiki_in_its_own_function():
    writers, unresolved = reply_writer_census(_sqlite_source())
    assert not unresolved, unresolved
    # anchor: the census sees the literal writers, the redaction's updates, the import's NON-literal act loop and the
    # erasure loop (a census blind to the import would pass at 07df8f8)
    assert {"add_reply", "_redact_in_txn", "commit_outcome_import_plan", "forget_user"} <= set(writers), writers
    assert [k for k, (ev, _w) in writers.items() if not ev] == [], writers


def _span(source, fn_name):
    tree = ast.parse(source)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == fn_name)
    lines = source.splitlines(keepends=True)
    return sum(map(len, lines[:fn.lineno - 1])), sum(map(len, lines[:fn.end_lineno]))


def _without_eviction(source, fn_name):
    a, b = _span(source, fn_name)
    body = source[a:b]
    stmt = 'self._conn.execute("DELETE FROM wiki WHERE user_id=?", '
    assert body.count(stmt) >= 1, (fn_name, "anchor absent")
    return source[:a] + body.replace(stmt, 'self._conn.execute("SELECT 1 FROM wiki WHERE user_id=?", ') + source[b:]


@pytest.mark.parametrize("fn_name", ["add_reply", "_redact_in_txn", "commit_outcome_import_plan"])
def test_the_census_flags_a_reply_writer_without_its_eviction(fn_name):
    """The census's mutants: each writer's eviction removed in turn is FLAGGED (the import's is 07df8f8's state)."""
    writers, unresolved = reply_writer_census(_without_eviction(_sqlite_source(), fn_name))
    assert not unresolved and writers[fn_name][0] is False, writers.get(fn_name)


def test_the_census_flags_an_erasure_loop_without_the_wiki_and_refuses_unresolved_sql():
    src = _sqlite_source()
    anchor = '"edges", "episodes", "wiki", "write_counter",'
    assert src.count(anchor) == 1
    writers, _u = reply_writer_census(src.replace(anchor, '"edges", "episodes", "write_counter",'))
    assert writers["forget_user"][0] is False
    probe = "def probe(self, q):\n    self._conn.execute(q)\n"
    assert reply_writer_census(probe)[1] == [("probe", 2)]


# every function in store/sqlite.py that evicts the wiki, and the bind clause that makes a body served across it honest
# (compile.bound_wiki): the cached path's row bind covers every one of them; for a COMPILED body, each names what it
# can change that the body may not carry. A new evicting writer refuses here until it is classed. This census reads
# SQL; it cannot show that every NECESSARY eviction exists (the reviewer's RII-R2-01) — that is
# tests/test_rii_r2_01_writer_inventory.py, which runs every store mutator against a cached wiki.
EVICTING_WRITERS = {
    "add_reply": "a challenge or a resolve: the withheld clause",
    "_redact_in_txn": "a redaction (edge or episode): the redacted clause",
    "forget_user": "an erasure: the presence clause",
    "commit_outcome_import_plan": "admitted acts (withheld clause) and imported notices, applied through "
                                  "_redact_in_txn (redacted clause); imported records are new facts, not in the body",
    "_invalidate_edge_row": "a content change: one that changes schema.assertion_view withholds the body by the view clause "
                            "(RII-R2-01); any other is kept for the call, as a write during the compile is (0041 §4e)",
    "_reinstate_edge_row": "a content change: one that changes schema.assertion_view withholds the body by the view clause "
                            "(RII-R2-01); any other is kept for the call, as a write during the compile is (0041 §4e)",
    "_recompute_edge_row": "a content change: one that changes schema.assertion_view withholds the body by the view clause "
                            "(RII-R2-01); any other is kept for the call, as a write during the compile is (0041 §4e)",
    "invalidate_edge": "a content change: one that changes schema.assertion_view withholds the body by the view clause "
                            "(RII-R2-01); any other is kept for the call, as a write during the compile is (0041 §4e)",
    "apply_supersession_plan": "a content change: one that changes schema.assertion_view withholds the body by the "
                               "view clause (RII-R2-01); any other is kept for the call (0041 §4e)",
    "_evict_wiki_on_view_change": "RII-R2-01: every edge write (via _journal_edge_write) and every episode write that "
                                  "changes a persisted record's schema.assertion_view: the view clause (the drawn "
                                  "record's CURRENT view against its drawn one) and snap.withheld on the current row",
    "transition_consolidation_if_current": "RII-R2-01: the consolidation cutover hides the claimed inputs and reveals "
                                           "the outputs (0010 X9); the presence clause reads a hidden input as absent",
    "discard_wiki": "RII-R2-01 (D2): the bind's own discard of the row a withheld compiled body published; no record "
                    "changes, so no clause is owed",
}


def wiki_evictors(source: str):
    """Every function whose SQL can delete the user's wiki row, by the census's own resolution of each execute."""
    tree = ast.parse(source)
    tuples = _module_tuples(tree)
    out = set()
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        loops = {f.target.id: f.iter.id for f in ast.walk(fn) if isinstance(f, ast.For)
                 and isinstance(f.target, ast.Name) and isinstance(f.iter, ast.Name)}
        for c in ast.walk(fn):
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr in ("execute",
                                                                                                  "executemany") \
                    and c.args and any(_EVICT.search(x) for x in (_sql_texts(fn, c.args[0], loops, tuples) or [])):
                out.add(fn.name)
    return out


def test_every_wiki_evicting_writer_is_classed_against_the_bind():
    assert wiki_evictors(_sqlite_source()) == set(EVICTING_WRITERS), \
        sorted(wiki_evictors(_sqlite_source()) ^ set(EVICTING_WRITERS))


def test_no_other_module_writes_replies():
    """The census reads store/sqlite.py; no other module of the package carries SQL that writes `replies`."""
    hits = []
    for p in sorted(SRC.rglob("*.py")):
        if p.name == "sqlite.py" and p.parent.name == "store":
            continue
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                hits += [(p.name, n.lineno) for m in _WRITE.finditer(n.value) if m.group(1).lower() == "replies"]
    assert hits == [], hits


def test_a_row_evicted_between_the_staleness_check_and_the_read_recompiles(tmp_path, monkeypatch):
    """ensure_wiki reads the row twice (needs_recompile, then the body): a reply between the two leaves None. The body
    read recompiles, as a stale cache does, rather than index None. Mutant (07df8f8): `get_wiki(user_id)[0]` raises
    TypeError."""
    state = {}
    reader, writer = (Memory(llm=_provider(state), config=_cfg(tmp_path / "m.db", after=10**6)) for _ in range(2))
    try:
        reader.store.add_edge(_edge("location", FACT))
        reader.recall(U, FACT, semantic=False)
        real, reads = reader.store.get_wiki, []

        def evict_after_first(user_id):
            reads.append(1)
            row = real(user_id)
            if len(reads) == 1:
                writer.reply(U, "location", kind="challenge", text="Please withhold this.")
            return row
        monkeypatch.setattr(reader.store, "get_wiki", evict_after_first)
        # "recompiles" is counted at the compiler, not the provider: after the challenge the only fact is withheld,
        # and an empty grounded input compiles to the fixed body without a model call (adoption probe 3)
        real_compile, compiles = compile_mod.compile_wiki, []
        monkeypatch.setattr(compile_mod, "compile_wiki", lambda *a, **k: (compiles.append(1), real_compile(*a, **k))[1])
        try:
            r = reader.recall(U, FACT, semantic=False)
        except TypeError as e:                       # the defect's own shape, reported as the cell's failure
            raise AssertionError(f"the evicted row was indexed: {e}") from e
        assert len(reads) >= 2 and compiles, (reads, compiles)
        assert not r.inspection["location"].challenge_clear and FACT not in r.grounded, r.grounded
    finally:
        reader.close()
        writer.close()
