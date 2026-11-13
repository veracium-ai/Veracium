"""specs/0003 §4c-ii v18.7, I6d (C3-01): the code-owned empty body is bound to the response by the user's store_version.

The round-3 review reproduced one recall serving "(no verified facts in this view)" above a fact a second connection
committed during that recall. v18.7 binds the empty body: its basis is the version at which its emptiness was
established, and `compile.empty_body_unbound` re-reads store_version after the recall's last store read whose result
can reach a response carrying the body. On a difference the body is left out of that one response.

Every write here is a public `remember()` on a second `Memory` connection to the same file, placed by instrumentation
that only orders the two connections (no product source altered, no edge written directly). Built on the reviewer's
probe_round3.py and research's prototype probe (research 0951206a).
"""
import inspect
import json

import pytest

import veracium
from veracium import EvidenceAuthor, EvidenceContext, Memory, MemoryConfig
from veracium import compile as C

E = C.EMPTY_GROUNDED_BODY
Q = "where does the user live"


def _body(text: str) -> bool:
    """The code-owned empty BODY is served: its exact text, marker line included. The empty-view placeholder recall
    computes itself carries the same first line and no marker, so the first line alone cannot tell them apart."""
    return C._empty_input_body() in text


class _Stub:
    """distill: one fact; compile: the model's summary of a grounded view (an empty view compiles with no model)."""

    def __init__(self, body="The user lives in Berlin.", fact=("located_at", "Berlin")):
        self.calls, self.body, self.fact = 0, body, fact

    def __call__(self, prompt, *, role="compile", **kw):
        if role == "distill":
            rel, obj = self.fact
            return json.dumps({"triples": [{"subject": "user", "relation": rel, "object": obj, "volatility": "durable"}],
                               "episode": f"The user said {obj}.", "instructions": []})
        self.calls += 1
        return self.body


def _no_provider(*a, **k):
    raise AssertionError("a provider-free reader called a model")


_no_provider._veracium_no_llm = True


def _mem(path, llm):
    return Memory(llm=llm, config=MemoryConfig(db_path=str(path), require_source_id=False))


def _remember(m, direct, user="u", text=None):
    kw = {"context": EvidenceContext.direct()} if direct else {"author": EvidenceAuthor.THIRD_PARTY}
    m.remember(user, text or ("I live in Berlin." if direct else "The user lives in Berlin."), date="2026-11-12", **kw)


def _caller():
    """The name of the function that called the hook calling this (the hook's caller)."""
    return inspect.currentframe().f_back.f_back.f_code.co_name


def _run(tmp_path, monkeypatch, placement, *, seed="third_party", reader="llm", writer_user="u", bind=True):
    """Seed a store whose cached wiki is the code-owned empty body (or a model summary), open a reader, and run ONE
    recall with a second connection's grounded write placed at `placement`; then a plain next recall."""
    db = tmp_path / f"{placement}-{seed}-{reader}-{writer_user}-{bind}.db"
    seeder = _mem(db, _Stub())
    if seed == "third_party":
        _remember(seeder, False)                       # a third-party claim: the verified view stays empty
    else:                                              # a model summary of a grounded fact
        seeder.close()
        seeder = _mem(db, _Stub(body="The user likes tea.", fact=("likes", "tea")))
        _remember(seeder, True, text="I like tea.")
    seeder.recall("u", Q, semantic=False)              # publishes the cached row
    m = _mem(db, _no_provider if reader == "provider-free" else seeder.llm)
    first = m.recall("u", Q, semantic=False).grounded
    writer = _mem(db, _Stub())
    fired = []

    def write():
        assert not fired
        fired.append(1)
        _remember(writer, True, user=writer_user)

    o_snap, o_inputs, o_eps, o_unbound = (m.store.challenge_snapshot, C._grounded_inputs, m.store.episodes,
                                          C.empty_body_unbound)

    def snap(*a, **k):
        if not fired and _caller() == "bound_wiki":
            write()
        return o_snap(*a, **k)

    def inputs(*a, **k):
        r = o_inputs(*a, **k)
        if not fired:
            write()
        return r

    o_select = veracium.subgraph_for_query

    def select(*a, **k):
        if not fired:
            write()                                    # bound_wiki has returned to recall; detail selection begins
        return o_select(*a, **k)

    def eps(*a, **k):
        if not fired and _caller() == "_recall":
            write()
        return o_eps(*a, **k)

    def unbound(*a, **k):
        r = o_unbound(*a, **k)
        if not fired:
            write()                                    # the boundary: the write after the bind read
        return r

    if placement == "cached-body-before-snapshot":
        monkeypatch.setattr(m.store, "challenge_snapshot", snap)
    elif placement == "compile-inputs-before-publication":
        monkeypatch.setattr(C, "_grounded_inputs", inputs)
        row = m.store.get_wiki("u")
        if row:                                        # force this call to compile
            m.store.discard_wiki("u", *row)
    elif placement == "after-bound-wiki-before-detail":
        monkeypatch.setattr(veracium, "subgraph_for_query", select)
    elif placement == "after-selection-before-episodes":
        monkeypatch.setattr(m.store, "episodes", eps)
    elif placement == "after-the-bind-read":
        monkeypatch.setattr(C, "empty_body_unbound", unbound)
    if not bind:                                       # v18.6's behaviour: the superseded rule, as the oracle
        monkeypatch.setattr(C, "empty_body_unbound", lambda *a, **k: False)
    this = m.recall("u", Q, semantic=False)
    monkeypatch.undo()
    nxt = m.recall("u", Q, semantic=False).grounded
    for x in (m, writer, seeder):
        x.close()
    return {"fired": bool(fired), "first": first, "this": this, "next": nxt}


REGRESSION = ["cached-body-before-snapshot", "compile-inputs-before-publication", "after-bound-wiki-before-detail",
              "after-selection-before-episodes"]


@pytest.mark.parametrize("placement", REGRESSION)
def test_a_write_during_the_recall_leaves_the_empty_body_out_of_that_response(tmp_path, monkeypatch, placement):
    """The review's three interleavings and research's fourth: the response leaves the empty body out and includes
    the fact; the next response includes the fact with no empty body."""
    r = _run(tmp_path, monkeypatch, placement)
    assert r["fired"] and _body(r["first"]), r
    assert not _body(r["this"].grounded) and E not in r["this"].grounded and "Berlin" in r["this"].grounded, \
        r["this"].grounded
    assert "Berlin" in r["next"] and E not in r["next"], r["next"]


def test_the_boundary_a_write_after_the_bind_read_is_not_in_that_response(tmp_path, monkeypatch):
    r = _run(tmp_path, monkeypatch, "after-the-bind-read")
    assert r["fired"]
    assert _body(r["this"].grounded) and "Berlin" not in r["this"].grounded, r["this"].grounded
    assert "Berlin" in r["next"] and E not in r["next"], r["next"]


def test_with_no_write_the_response_is_byte_identical_to_v18_6(tmp_path, monkeypatch):
    """The superseded rule (no bind) is the oracle: with no write during the call, the two responses are equal."""
    a = _run(tmp_path, monkeypatch, "none")
    b = _run(tmp_path, monkeypatch, "none", bind=False)
    assert not a["fired"] and a["this"].context == b["this"].context and _body(a["this"].grounded)


def test_a_model_summary_is_served_across_a_concurrent_write(tmp_path, monkeypatch):
    """No broadening: only the code-owned empty body is bound; a model summary keeps 0012's lag."""
    r = _run(tmp_path, monkeypatch, "after-bound-wiki-before-detail", seed="model_summary")
    assert r["fired"] and "likes tea" in r["this"].grounded and "Berlin" in r["this"].grounded, r["this"].grounded


def test_a_provider_free_reader_leaves_the_body_out_and_calls_no_model(tmp_path, monkeypatch):
    r = _run(tmp_path, monkeypatch, "after-bound-wiki-before-detail", reader="provider-free")
    assert r["fired"] and not _body(r["this"].grounded) and "Berlin" in r["this"].grounded, r["this"].grounded


def test_another_users_write_leaves_the_body_served(tmp_path, monkeypatch):
    r = _run(tmp_path, monkeypatch, "after-bound-wiki-before-detail", writer_user="other")
    assert r["fired"] and _body(r["this"].grounded) and "Berlin" not in r["this"].grounded, r["this"].grounded


def test_a_principal_bearing_recall_is_unchanged(tmp_path, monkeypatch):
    """A principal-bearing recall has no wiki (0020), so the bind never applies: its response equals v18.6's."""
    from veracium.scope import Identity
    out = []
    for bind in (True, False):
        db = tmp_path / f"principal-{bind}.db"
        m = Memory(llm=_Stub(), config=MemoryConfig(db_path=str(db), require_source_id=False, scope_groups={}))
        _remember(m, True)
        if not bind:
            monkeypatch.setattr(C, "empty_body_unbound", lambda *a, **k: False)
        out.append(m.recall("u", Q, semantic=False, principal=Identity(origin=None, source_id="s")).context)
        monkeypatch.undo()
        m.close()
    assert out[0] == out[1]


def test_a_served_empty_body_never_runs_the_placeholder_reads(tmp_path, monkeypatch):
    """research's stage 1 on dev's B2: a response carrying the body never computes an empty-view placeholder, so no
    store read there can reach it. A later change that renders a placeholder beside the body fails here."""
    db = tmp_path / "placeholder.db"
    m = _mem(db, _Stub())
    _remember(m, False)
    m.recall("u", Q, semantic=False)
    seen = []
    o_eps, o_edges = m.store.episodes, m.store.edges

    def eps(*a, **k):
        if k.get("limit") == 1 and k.get("include_retired"):
            seen.append("episodes")
        return o_eps(*a, **k)

    def edges(*a, **k):
        if k.get("include_quarantined") and k.get("active_only") is False and _caller() == "_recall":
            seen.append("edges")
        return o_edges(*a, **k)
    monkeypatch.setattr(m.store, "episodes", eps)
    monkeypatch.setattr(m.store, "edges", edges)
    r = m.recall("u", Q, semantic=False)
    assert _body(r.grounded) and seen == [], (seen, r.grounded)
    m.close()


def test_the_stated_limit_an_erasure_and_writes_back_to_the_basis_pass_the_bind(tmp_path, monkeypatch):
    """specs/0003 §4c-ii v18.8, the bind's limit: forget_user deletes the user's write_counter row (0008 §6g), so an
    erasure followed by writes back to exactly the basis B, all inside one recall, passes the bind, and that response
    carries the empty body above the recreated user's fact. Asserted AS the limit; inverted when the store-wide floor
    lands (0003 §10 Q8, at the next schema-version change)."""
    db = tmp_path / "aba.db"
    seeder = _mem(db, _Stub())
    _remember(seeder, False)
    seeder.recall("u", Q, semantic=False)               # the cached code-owned empty row
    m = _mem(db, seeder.llm)
    writer = _mem(db, _Stub())
    basis = m.store.store_version("u")
    fired = []
    o_bound = C.bound_wiki

    def bound(*a, **k):
        r = o_bound(*a, **k)
        if not fired:
            fired.append(1)
            writer.forget("u")
            while writer.store.store_version("u") < basis:     # one remember advances it by 2: stop AT the basis
                _remember(writer, True)
        return r
    monkeypatch.setattr(C, "bound_wiki", bound)
    this = m.recall("u", Q, semantic=False).grounded
    monkeypatch.undo()
    assert fired and m.store.store_version("u") == basis, (basis, m.store.store_version("u"))
    assert _body(this) and "Berlin" in this, this                  # THE LIMIT: the bind passed across the erasure
    for x in (m, writer, seeder):
        x.close()
