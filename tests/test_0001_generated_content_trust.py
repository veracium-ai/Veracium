"""specs/0001 — the generated-content trust class, with REAL `ASSISTANT`
records (no stand-ins).

ACCEPTED at external round 18 (2026-08-25) and implemented here. This
file spent eighteen rounds as the reviewer's executable evidence branch,
where it was named for the candidate patch that carried it; it is
ordinary product coverage now and is named for what it tests.

Covers: I1, I5 (partition + render + marker), I6 (the exact 1,000+1
fixture at BOTH coverage shares), I11 (the full author×derived product),
I12 (pair-keyed labels), I13a-c (the five-manifestation matrix with
derived counts) and the I13 refusal exactness.
"""
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from veracium.gate import partition_parts
from veracium.graph import (apply_supersession, collapse_for_render,
                            subgraph_for_query)
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge,
                             EvidenceAuthor, Provenance, Volatility)
from veracium.store import schema_version as sv
from veracium.store.migration import migrate_store
from veracium.store.sqlite import SqliteStore

U = "u-cand"
NOW = datetime.now(timezone.utc)


def _edge(obj, *, author, derived=None, rel="works_as", subject="user",
          days_ago=1, disclosure=None):
    t = NOW - timedelta(days=days_ago)
    prov = Provenance(author_of_evidence=author, derived_from=derived,
                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                      confidence=0.7, observed_at=t,
                      **({"disclosure": disclosure} if disclosure else {}))
    return Edge(id=f"e-{uuid.uuid4().hex[:8]}", user_id=U, subject=subject,
                relation=rel, object=obj, volatility=Volatility.SLOW,
                valid_from=t, provenance=prov)


def _assistant_edge(obj, **kw):
    from veracium.ingest import _disclosure_for
    d = _disclosure_for(EvidenceAuthor.ASSISTANT, kw.get("rel", "works_as"))
    return _edge(obj, author=EvidenceAuthor.ASSISTANT, disclosure=d, **kw)


# ---- I1 + I11: disclosure, the full product --------------------------------

def test_i1_assistant_is_use_only_for_every_subject():
    for subject in ("user", "server", "assistant"):
        e = _assistant_edge("the deploy failed", subject=subject)
        assert e.provenance.disclosure == Disclosure.USE_ONLY, subject
        assert not e.assertable, subject


def test_i11_never_mentionable_over_the_full_product():
    from veracium.ingest import _disclosure_for
    members = list(EvidenceAuthor)
    assert EvidenceAuthor.ASSISTANT in members
    for author in members:
        for derived in [None, *members]:
            d = _disclosure_for(author, "works_as", derived)
            if (author == EvidenceAuthor.ASSISTANT
                    or derived == EvidenceAuthor.ASSISTANT):
                assert d != Disclosure.MENTIONABLE, (author, derived)


# ---- I5: affirmation, at the REAL surfaces ---------------------------------

def test_i5_affirmation_grounds_and_partitions_and_confirm_refuses():
    s = SqliteStore(":memory:")
    prior = _assistant_edge("carpenter")
    apply_supersession(s, prior, DEFAULT_RELATIONS)
    affirmation = _edge("carpenter", author=EvidenceAuthor.USER)
    apply_supersession(s, affirmation, DEFAULT_RELATIONS)
    edges = s.edges(U)
    by_id = {e.id: e for e in edges}
    assert by_id[affirmation.id].assertable
    assert not by_id[prior.id].assertable
    # no cross-class collapse (the upstream assertion, retained)
    surfaced, _ = collapse_for_render(edges)
    assert len(surfaced) == 2
    # THE RENDERED PARTITIONS (R5-3/R6-3): grounded-only / unverified-only /
    # the assistant marker present / no leakage
    edge_lines, _eps, claim_lines, _tps = partition_parts(surfaced, [])
    grounded = "\n".join(edge_lines)
    unverified = "\n".join(claim_lines)
    assert "carpenter" in grounded
    assert "carpenter" in unverified
    assert "assistant-generated" in unverified, (
        "the I12 bare-assistant label must reach the rendered block")
    assert "assistant-generated" not in grounded
    assert not (set(edge_lines) & set(claim_lines))
    # 0008 PRESERVED: confirm_edge refuses the assistant edge
    with pytest.raises(ValueError, match="not assertable"):
        s.confirm_edge(U, prior.id, actor="user", call_path="t",
                       correlation_id="c", request_digest=None,
                       confirmed_at="2026-08-23T00:00:00Z")
    # different value: the ladder retires the prior (rung 3 > rung 1)
    s2 = SqliteStore(":memory:")
    p2 = _assistant_edge("carpenter")
    apply_supersession(s2, p2, DEFAULT_RELATIONS)
    apply_supersession(s2, _edge("plumber", author=EvidenceAuthor.USER),
                       DEFAULT_RELATIONS)
    assert not next(e for e in s2.edges(U, active_only=False)
                    if e.id == p2.id).active


# ---- I12: pair-keyed origin labels -----------------------------------------

def test_i12_the_complete_label_matrix():
    """R7-1: the §4b decision order verbatim, over the COMPLETE
    author x derived-from product — no author class inherits another's
    label, and the fail-safe holds for every unlabellable cell."""
    from veracium.graph import _origin_label
    A = EvidenceAuthor
    for author in A:
        for derived in [None, *A]:
            e = _edge("x", author=author, derived=derived,
                      disclosure=Disclosure.USE_ONLY)
            got = _origin_label(e)
            if derived == A.THIRD_PARTY:
                want = "third-party-derived"
            elif author == A.THIRD_PARTY:
                want = "third-party-reported"
            elif author == A.ASSISTANT:
                want = "assistant-generated"
            else:
                want = "unverified-origin"
            assert got == want, (author, derived, got)


# ---- I6: the exact fixture, BOTH shares ------------------------------------

@pytest.mark.parametrize("share", [0.0, 0.25])
def test_i6_reserve_guarantees_the_user_edge(share):
    s = SqliteStore(":memory:")
    user_edge = _edge("the user's own fact", author=EvidenceAuthor.USER,
                      days_ago=400)
    s.add_edge(user_edge)
    for i in range(1000):
        s.add_edge(_assistant_edge(f"assistant fact {i}", days_ago=1))
    picked = subgraph_for_query(s, U, "works fact", max_edges=40,
                                coverage_share=share,
                                relations=DEFAULT_RELATIONS)
    ids = {e.id for e in picked}
    assert len(picked) == 40
    assert user_edge.id in ids, (
        f"the reserve must guarantee the assertable edge at share={share}")


# ---- I13: the migration matrix ---------------------------------------------

def test_i13a_schema_v11_is_byte_identical_to_v10():
    assert sv.SCHEMA_V11 == sv.SCHEMA_V10
    assert sv.SCHEMA_VERSION == 11


def _accepted_v10_records():
    """The EXACT five accepted v10 manifestations, from the executable
    authority's own records (objects included) — never a route proxy
    (R7-2)."""
    rec = sv.version_records()["10"]["accepted"]
    assert all("objects" in a for a in rec)
    return rec


def _store_from_objects(path, objects, version):
    conn = sqlite3.connect(path)
    # tables before the indexes/triggers that reference them
    for _name, obj in sorted(objects.items(),
                             key=lambda kv: (0 if kv[0].startswith("table")
                                             else 1, kv[0])):
        conn.execute(obj["sql"] if isinstance(obj, dict) else obj.sql)
    conn.execute(f"PRAGMA user_version = {version}")
    conn.commit()
    conn.close()


@pytest.mark.parametrize("idx", range(5))
def test_i13b_stamp_only_across_every_accepted_v10_shape(idx, tmp_path):
    """R7-2: the FIVE-manifestation matrix, exact — each accepted v10
    shape is constructed FROM the authority's own object record, dumped
    AT v10, migrated, and the v10-vs-v11 dumps compared (not v11-vs-v11);
    the landing digest must be v11-accepted."""
    recs = _accepted_v10_records()
    assert idx < len(recs)
    objects = recs[idx]["objects"]
    db = str(tmp_path / f"shape{idx}.db")
    _store_from_objects(db, objects, 10)
    conn = sqlite3.connect(db)
    dump_v10 = sorted(r[0] or "" for r in conn.execute(
        "SELECT sql FROM sqlite_master").fetchall())
    conn.close()
    migrate_store(db)
    conn = sqlite3.connect(db)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 11
    dump_v11 = sorted(r[0] or "" for r in conn.execute(
        "SELECT sql FROM sqlite_master").fetchall())
    conn.close()
    assert dump_v11 == dump_v10, (
        f"shape {idx} ({recs[idx]['provenance'][:40]}…): the v10->v11 "
        f"edge changed SQL — the stamp-only promise broke")
    s = SqliteStore(db)      # opens accepted at 11
    s.close()


def test_i13c_v11_inherits_by_digest_not_count():
    """R7-2: inheritance asserted at DIGEST level — five unrelated v11
    records must NOT pass. The count is derived, never typed; and the
    five inherited shapes INCLUDE the constructor (five total, not
    five-plus-one)."""
    recs = _accepted_v10_records()
    inherited = {sv._digest_of_identity(r["objects"], 11) for r in recs}
    v11 = sv.accepted_digests(11)
    assert inherited == v11, (
        "accepted_digests(11) must be EXACTLY the v10 shapes re-digested "
        "at 11")
    assert len(v11) == len(sv.accepted_digests(10))


def test_i13_pre_assistant_reader_refuses_a_v11_store(tmp_path,
                                                      monkeypatch):
    """R7-2: the REAL boundary — a reader whose head is 10 (pre-ASSISTANT)
    opening a v11 store that CONTAINS assistant data refuses at open with
    exactly reason='newer', before any edge validates."""
    import veracium.store.sqlite as sq
    db = str(tmp_path / "v11.db")
    s = SqliteStore(db)
    s.add_edge(_assistant_edge("model claim"))
    s.close()
    monkeypatch.setattr(sv, "SCHEMA_VERSION", 10)
    monkeypatch.setattr(sq, "SCHEMA_VERSION", 10, raising=False)
    # the simulated old reader carries a VALID runtime record for ITS OWN
    # head (a real pre-ASSISTANT tree does); only the version boundary is
    # under test here — the reviewer's two-tree probe measured the same
    # refusal with no simulation at all
    monkeypatch.setattr(sv, "runtime_supported", lambda: True)
    with pytest.raises(sv.StoreVersionError) as ei:
        SqliteStore(db)
    assert ei.value.reason == "newer"


# ---- I7: the export era ----------------------------------------------------

def test_downgrade_export_fails_cleanly(tmp_path, monkeypatch):
    """R7-3: the spec-named test, REAL — an export carrying an assistant
    record round-trips at 9, and an OLDER importer (head 8) refuses with
    our message, never a pydantic traceback."""
    import veracium.portability as port
    # the 0001 era stamped 9; 0026 moved the reader to 10 with a
    # CONDITIONAL write stamp — this assistant-record store is
    # marker-free, so its export still stamps the pre-agreement 9 and
    # every assertion below holds unchanged
    assert port.FORMAT_VERSION == 10
    assert port._PRE_AGREEMENT_VERSION == 9
    s = SqliteStore(str(tmp_path / "a.db"))
    e = _assistant_edge("model claim")
    s.add_edge(e)
    out = tmp_path / "export.jsonl"
    port.export_memory(s, U, out)
    # same-era round trip: the DEFAULT import applies the ratified 0005
    # cap (§2d.2) — the assistant record arrives THIRD_PARTY, authority
    # 1 -> 0, conservative; restore=True is the faithful mode
    s2 = SqliteStore(str(tmp_path / "b.db"))
    port.import_memory(s2, out)
    assert any(x.provenance.author_of_evidence == EvidenceAuthor.THIRD_PARTY
               for x in s2.edges(U, active_only=False)), (
        "the 0005 cap must flatten the imported author (ratified, §2d.2)")
    s2.close()
    s2r = SqliteStore(str(tmp_path / "br.db"))
    port.import_memory(s2r, out, restore=True)
    assert any(x.provenance.author_of_evidence == EvidenceAuthor.ASSISTANT
               for x in s2r.edges(U, active_only=False)), (
        "restore=True must carry ASSISTANT faithfully")
    s2r.close()
    # the OLD importer refuses cleanly — WITH the parse sentinel (R8-2):
    # the refusal must fire BEFORE any record validates, or a real old
    # enum would hit pydantic instead of our message. The prior form let
    # a version-check-after-parsing regression pass silently.
    monkeypatch.setattr(port, "FORMAT_VERSION", 8)
    from veracium import schema as _schema
    parses = []
    for cls_name in ("Edge", "Episode"):
        cls = getattr(_schema, cls_name)
        real = cls.model_validate
        def boom(*a, _n=cls_name, **k):
            parses.append(_n)
            raise AssertionError(
                f"{_n} validated BEFORE the newer-format refusal (R8-2)")
        monkeypatch.setattr(cls, "model_validate", classmethod(
            lambda c, *a, _b=boom, **k: _b(*a, **k)))
    s3 = SqliteStore(str(tmp_path / "c.db"))
    with pytest.raises(ValueError, match="newer"):
        port.import_memory(s3, out)
    assert parses == [], "records parsed before the version refusal"
    s3.close()
    s.close()


# ---- I6 composition (R7-4): the four named branches, exact IDs -------------

def _mk(s, obj, *, assertable, day, rank_boost=0):
    """A controlled-rank edge: `obj` carries the query token; rank_boost
    adds extra matching tokens; `day` fixes valid_from's date."""
    author = EvidenceAuthor.USER if assertable else EvidenceAuthor.THIRD_PARTY
    disc = None if assertable else Disclosure.USE_ONLY
    e = _edge(f"topic {'topic ' * rank_boost}{obj}", author=author,
              disclosure=disc, days_ago=day)
    s.add_edge(e)
    return e


def _pick(s, share, max_edges=8):
    return [e.id for e in subgraph_for_query(
        s, U, "topic", max_edges=max_edges, coverage_share=share,
        relations=DEFAULT_RELATIONS)]


def test_i6_composition_reserved_day_overlap():
    """(a) reserved records share their day with the top-ranked rest:
    the seeded covered-day state makes the coverage tail spend on OTHER
    days — asserted by exact selection."""
    s = SqliteStore(":memory:")
    a1 = _mk(s, "a1", assertable=True, day=10, rank_boost=5)
    a2 = _mk(s, "a2", assertable=True, day=10, rank_boost=5)
    highs = [_mk(s, f"h{i}", assertable=False, day=10, rank_boost=3)
             for i in range(6)]
    d_other = [_mk(s, f"d{i}", assertable=False, day=20 + i, rank_boost=0)
               for i in range(3)]
    picked = _pick(s, share=0.25)
    # R8-1: the EXACT ORDERED expectation, computed by construction —
    # reserve (a1, a2 by rank) first in rank order, then the head by rank,
    # then the coverage tail on unseen days by rank. Rest budget 6, cover
    # reserve int(6*0.25)=1 -> head 5 = h0..h4, tail 1 = d0 (day 20,
    # highest-ranked unseen-day candidate).
    expected = [a1.id, a2.id] + [h.id for h in highs[:5]] + [d_other[0].id]
    assert picked == expected, (picked, expected)


def test_i6_composition_distinct_reserved_days():
    """(b) reserved records on DISTINCT days both seed coverage; the tail
    then only spends on genuinely new days."""
    s = SqliteStore(":memory:")
    a1 = _mk(s, "a1", assertable=True, day=10, rank_boost=5)
    a2 = _mk(s, "a2", assertable=True, day=11, rank_boost=5)
    highs = [_mk(s, f"h{i}", assertable=False, day=10, rank_boost=3)
             for i in range(5)]
    same_day_low = _mk(s, "sd", assertable=False, day=11, rank_boost=0)
    new_day_low = _mk(s, "nd", assertable=False, day=30, rank_boost=0)
    picked = _pick(s, share=0.25)
    # R8-1 exact order: reserve a1,a2; head 5 = highs h0..h4; the single
    # coverage slot takes the NEW-day candidate (day 30) over the
    # seeded-day one (day 11), by construction
    expected = [a1.id, a2.id] + [h.id for h in highs[:5]] + [new_day_low.id]
    assert picked == expected, (picked, expected)
    assert same_day_low.id not in picked


def test_i6_composition_dedup_across_reserve_and_coverage():
    """(c) strictly-redundant duplicates collapse BEFORE the reserve, so
    neither the reserve nor coverage can select a suppressed twin."""
    s = SqliteStore(":memory:")
    a1 = _mk(s, "a1", assertable=True, day=10, rank_boost=5)
    twin_a = _edge("topic twin", author=EvidenceAuthor.THIRD_PARTY,
                   disclosure=Disclosure.USE_ONLY, days_ago=15)
    twin_b = _edge("topic twin", author=EvidenceAuthor.THIRD_PARTY,
                   disclosure=Disclosure.USE_ONLY, days_ago=15)
    s.add_edge(twin_a)
    s.add_edge(twin_b)
    fs = [_mk(s, f"f{i}", assertable=False, day=40 + i)
          for i in range(8)]
    picked = _pick(s, share=0.25)
    # R8-1: the PRECISE dedup survivor — collapse_for_render's survivor
    # order decides; assert which twin lives and that the loser is absent
    surfaced, _ = collapse_for_render([twin_a, twin_b])
    assert len(surfaced) == 1
    survivor, loser = surfaced[0].id, (
        twin_b.id if surfaced[0].id == twin_a.id else twin_a.id)
    assert loser not in picked, "the suppressed twin must never surface"
    # R9-1: the COMPLETE ordered output, not survivor membership — §20
    # claims every vector asserts the full order, so this one does too:
    # reserved [a1] first, then the rank-ordered head (survivor, f0..f4),
    # then the one coverage slot (f5, the highest-ranked unseen day)
    expected = [a1.id, survivor] + [f.id for f in fs[:5]] + [fs[5].id]
    assert picked == expected, (picked, expected)


def test_i6_reserved_low_rank_is_placed_first_nonfunctional():
    """(e) R9-1, the reviewer's construction: the ONE assertable record
    ranks LAST globally and sits under a NON-functional relation
    (has_pet), so no authority permutation can mask output order. The
    contract is CONSTRUCTION — reserved + remainder — and the complete
    ordered output is asserted: the reserved record is FIRST despite
    being the store's worst-ranked candidate. The pre-fix filter over
    the globally scored list returned it fourth of four."""
    s = SqliteStore(":memory:")
    highs = []
    for i in range(4):
        e = _edge(f"topic h{i}", author=EvidenceAuthor.THIRD_PARTY,
                  disclosure=Disclosure.USE_ONLY, rel="has_diet",
                  days_ago=10 + i)
        s.add_edge(e)
        highs.append(e)
    low = _edge("topic", author=EvidenceAuthor.USER, rel="has_pet",
                days_ago=30)          # assertable; oldest -> globally last
    s.add_edge(low)
    picked = _pick(s, share=0.25, max_edges=4)
    # reserve ceil(4/4)=1 -> [low]; rest budget 3, coverage int(3*0.25)=0
    # -> head = the three newest highs by recency tiebreak
    expected = [low.id] + [h.id for h in highs[:3]]
    assert picked == expected, (picked, expected)


def test_i6_no_relevant_assertable_reserves_nothing():
    """(f) R10-1, the reviewer's executed counterexample: the spec
    reserves count_RELEVANT_assertable, but eligibility is not relevance
    — a user-subject assertable edge with ZERO query overlap sits in
    `scored` at baseline score, and the pre-fix reserve protected it
    FIRST, dropping a relevant fact. Query 'topic', max_edges=4,
    coverage_share=0.0: four relevant unverified facts + one unrelated
    assertable ('bananas'). The reserve must engage for NO record; the
    output is exactly the four relevant facts by rank. Pre-fix output:
    bananas, topic h0, topic h1, topic h2."""
    s = SqliteStore(":memory:")
    highs = []
    for i in range(4):
        e = _edge(f"topic h{i}", author=EvidenceAuthor.THIRD_PARTY,
                  disclosure=Disclosure.USE_ONLY, rel="has_diet",
                  days_ago=10 + i)
        s.add_edge(e)
        highs.append(e)
    bananas = _edge("bananas", author=EvidenceAuthor.USER, rel="has_pet",
                    days_ago=5)   # assertable, zero overlap with 'topic'
    s.add_edge(bananas)
    picked = [e.id for e in subgraph_for_query(
        s, U, "topic", max_edges=4, coverage_share=0.0,
        relations=DEFAULT_RELATIONS)]
    expected = [h.id for h in highs]
    assert picked == expected, (picked, expected)
    assert bananas.id not in picked, (
        "an eligibility-only assertable edge was reserved over a "
        "relevant fact (R10-1)")


def test_i6_composition_underfill_backfills_by_rank_deterministically():
    """(d) when every remaining candidate shares the seeded day, coverage
    UNDERFILLS and the tail backfills BY RANK — asserted on the exact
    ordered selection, twice (determinism)."""
    s = SqliteStore(":memory:")
    a1 = _mk(s, "a1", assertable=True, day=10, rank_boost=5)
    a2 = _mk(s, "a2", assertable=True, day=10, rank_boost=5)
    rest = [_mk(s, f"r{i}", assertable=False, day=10, rank_boost=6 - i)
            for i in range(7)]
    picked1 = _pick(s, share=0.25)
    picked2 = _pick(s, share=0.25)
    assert picked1 == picked2, "backfill must be deterministic"
    # R8-1: the EXACT ORDERED list — reserve, then the rank-ordered head,
    # then the rank-ordered backfill (no new day existed to cover)
    expected = [a1.id, a2.id] + [r.id for r in rest[:6]]
    assert picked1 == expected, (picked1, expected)
