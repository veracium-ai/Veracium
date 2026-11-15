"""specs/0031 §4f §4e: the whole-user erase in two steps, at the library (`Memory.forget_everything_preview` /
`forget_everything_confirm`, `trust_tools`). INV-TT8, TT9, TT10, TT14, TT17 (library half), TT20 and TT21; the tool
surfaces are tested with the tools. Every mutating case runs on its own fresh store, and the clock and the key are
injected (§6's oracle discipline): nothing here normalizes a MAC, a digest or a refusal away.
"""
import base64
import hashlib
import hmac
import json
import sqlite3

import pytest

from veracium import Memory, MemoryConfig
from veracium import trust_tools as T
from veracium.schema import Edge, EvidenceAuthor, Provenance
from veracium.scope import Identity
from veracium.trust_tools import PreviewTokenIssuer, TrustRefused

U = "u"
T0 = 1_800_000_000
KEY = bytes(range(32))


def _mem(tmp_path, name="v.db"):
    tmp_path.mkdir(parents=True, exist_ok=True)
    return Memory(llm=lambda *a, **k: "x",
                  config=MemoryConfig(db_path=str(tmp_path / name), require_source_id=False,
                                      wiki_recompile_after_writes=0))


def _edge(m, eid, user=U):
    m.store.add_edge(Edge(id=eid, user_id=user, subject="user", relation="likes", object=f"o-{eid}",
                          provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"ev-{eid}")))


def _issuer(m, clock, user=U, key=None):
    return PreviewTokenIssuer(m.store.local_origin(), user, clock=lambda: clock["t"], key=key)


def _digest(m) -> str:
    return hashlib.sha256("\n".join(m.store._conn.iterdump()).encode()).hexdigest()


def _count(m, table, user=U):
    return m.store._conn.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id=?", (user,)).fetchone()[0]


# ------------------------------------------------------------------ INV-TT21: the construction, byte for byte
def _oracle_token(user, keys, issued_at, key):
    """An INDEPENDENT construction of §4e from the spec's words, with no import from veracium."""
    snap = json.dumps({"v": 1, "user": user, "tables": [[t, keys[t]] for t in
                                                        ("edges", "episodes", "confirmations", "replies")]},
                      separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(snap).hexdigest()
    payload = json.dumps({"u": user, "d": digest, "t": issued_at}, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    wire = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    mac = hmac.new(key, b"veracium/0031-tt/preview/v1\x00" + wire.encode("ascii"), hashlib.sha256).digest()
    return snap, digest, payload, wire, mac, f"tt1.{wire}.{base64.urlsafe_b64encode(mac).decode().rstrip('=')}"


#: THE PUBLISHED VECTOR (INV-TT21): key = bytes 0..31, user "u", t = 1800000000, and these key lists
VECTOR_KEYS = {"edges": ["e-1", "e-2"], "episodes": ["ep-1"], "confirmations": [], "replies": ["rp-1"]}
VECTOR_DIGEST = "44c53d519ff540105acca8a13f925add92317406f08494482068f2d45e4e0da7"
VECTOR_MAC_HEX = "27286d62dc401ac8931227170bdece7a96cc3f8ba11385b1e93e878eeec1d7d7"
VECTOR_TOKEN = ("tt1.eyJ1IjoidSIsImQiOiI0NGM1M2Q1MTlmZjU0MDEwNWFjY2E4YTEzZjkyNWFkZDkyMzE3NDA2ZjA4NDk0NDgyMDY4ZjJk"
                "NDVlNGUwZGE3IiwidCI6MTgwMDAwMDAwMH0.JyhtYtxAGsiTEicXC97OepbMP4uhE4Wx6T6Hju7B19c")


def test_the_token_matches_an_independent_construction_byte_for_byte():
    """Mutants: a delimiter-joined digest; a MAC over the decoded JSON instead of the wire segment."""
    snap, digest, payload, wire, mac, token = _oracle_token(U, VECTOR_KEYS, T0, KEY)
    assert T.snapshot_digest(U, VECTOR_KEYS) == digest
    iss = PreviewTokenIssuer("origin-x", U, clock=lambda: T0, key=KEY)
    assert iss.issue(digest, T0) == token
    assert iss._mac(wire) == mac
    # the vector, pinned: a change to any construction step moves these bytes
    assert snap == (b'{"v":1,"user":"u","tables":[["edges",["e-1","e-2"]],["episodes",["ep-1"]],'
                    b'["confirmations",[]],["replies",["rp-1"]]]}')
    assert payload == ('{"u":"u","d":"' + digest + '","t":1800000000}').encode()
    assert (digest, mac.hex(), token) == (VECTOR_DIGEST, VECTOR_MAC_HEX, VECTOR_TOKEN)


def test_the_same_key_in_another_table_is_a_different_set():
    a = {"edges": ["x"], "episodes": [], "confirmations": [], "replies": []}
    b = {"edges": [], "episodes": ["x"], "confirmations": [], "replies": []}
    assert T.snapshot_digest(U, a) != T.snapshot_digest(U, b)


def test_keys_sort_as_utf8_bytes():
    assert T._sorted_keys(["é", "z", "a"]) == ["a", "z", "é"]
    assert T._sorted_keys(["￿", "\U0001f600"]) == ["￿", "\U0001f600"]   # bytes order; code points agree here


def _valid():
    iss = PreviewTokenIssuer("origin-x", U, clock=lambda: T0, key=KEY)
    d = T.snapshot_digest(U, VECTOR_KEYS)
    return iss, d, iss.issue(d, T0)


def _seg(obj_bytes):
    return base64.urlsafe_b64encode(obj_bytes).decode().rstrip("=")


def _forge(payload_bytes, key=KEY):
    wire = _seg(payload_bytes)
    mac = hmac.new(key, b"veracium/0031-tt/preview/v1\x00" + wire.encode(), hashlib.sha256).digest()
    return f"tt1.{wire}.{_seg(mac)}"


def _malformed():
    iss, d, tok = _valid()
    pre, wire, mac = tok.split(".")
    yield "padding", f"{pre}.{wire}==.{mac}"
    # non-zero pad bits: flip the low bits of the last character of a segment whose length leaves pad bits
    last = mac[-1]
    alt = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    yield "non-zero pad bits", f"{pre}.{wire}.{mac[:-1]}{alt[(alt.index(last) + 1) % 64]}"
    yield "wrong alphabet", f"{pre}.{wire.replace(wire[3], '+', 1)}.{mac}"
    yield "four parts", f"{tok}.x"
    yield "wrong prefix", f"tt2.{wire}.{mac}"
    yield "extra key", _forge(json.dumps({"u": U, "d": d, "t": T0, "x": 1}, separators=(",", ":")).encode())
    yield "missing key", _forge(json.dumps({"u": U, "d": d}, separators=(",", ":")).encode())
    yield "duplicate key", _forge(('{"u":"u","d":"' + d + '","t":1800000000,"t":1800000000}').encode())
    yield "nested object", _forge(json.dumps({"u": {"x": 1}, "d": d, "t": T0}).encode())
    yield "non-integer t", _forge(json.dumps({"u": U, "d": d, "t": float(T0)}).encode())
    yield "boolean t", _forge(json.dumps({"u": U, "d": d, "t": True}).encode())
    yield "uppercase hex", _forge(json.dumps({"u": U, "d": d.upper(), "t": T0}).encode())
    yield "malformed utf-8", _forge(b'{"u":"\xff","d":"' + d.encode() + b'","t":1800000000}')
    yield "short mac", f"{pre}.{wire}.{_seg(b'0' * 31)}"
    yield "not a string", 12345


@pytest.mark.parametrize("case, token", list(_malformed()), ids=[c for c, _ in _malformed()])
def test_every_malformed_token_is_refused_alike(case, token):
    """Mutant: a non-strict parser (each of these would parse under a lenient one); an isinstance timestamp check."""
    iss, _d, _t = _valid()
    with pytest.raises(TrustRefused) as ei:
        iss.verify(token, store_identity="origin-x", user_id=U)
    assert (ei.value.reason, ei.value.detail) == ("preview_unknown", T.PREVIEW_UNKNOWN_DETAIL), case


def test_the_valid_token_itself_verifies():
    iss, d, tok = _valid()
    assert iss.verify(tok, store_identity="origin-x", user_id=U) == d


@pytest.mark.parametrize("offset, outcome", [(-1, "preview_unknown"), (0, "ok"), (599, "ok"),
                                             (600, "preview_expired")])
def test_the_expiry_boundaries(offset, outcome):
    """valid iff t <= now < t + 600; a future t is preview_unknown."""
    clock = {"t": T0 + offset}
    iss = PreviewTokenIssuer("origin-x", U, clock=lambda: clock["t"], key=KEY)
    tok = iss.issue(T.snapshot_digest(U, VECTOR_KEYS), T0)
    if outcome == "ok":
        iss.verify(tok, store_identity="origin-x", user_id=U)
    else:
        with pytest.raises(TrustRefused) as ei:
            iss.verify(tok, store_identity="origin-x", user_id=U)
        assert ei.value.reason == outcome


def test_another_key_instance_and_another_context_refuse():
    """Mutants: a process-global key (another instance would verify); no issuer-context check (an issuer for another
    store, with the same key, would verify)."""
    iss, _d, tok = _valid()
    fresh = PreviewTokenIssuer("origin-x", U, clock=lambda: T0)          # a reconstructed issuer: a new key
    with pytest.raises(TrustRefused, match="preview_unknown"):
        fresh.verify(tok, store_identity="origin-x", user_id=U)
    with pytest.raises(TrustRefused, match="preview_unknown"):
        iss.verify(tok, store_identity="origin-y", user_id=U)            # the receiving store is not the issuer's
    with pytest.raises(TrustRefused, match="preview_unknown"):
        iss.verify(tok, store_identity="origin-x", user_id="v")          # nor the receiving user


def test_no_issuer_holds_a_shared_key():
    assert PreviewTokenIssuer("o", U)._key != PreviewTokenIssuer("o", U)._key


# ------------------------------------------------------------------ the two steps on a store
def test_the_preview_reveals_counts_only_and_writes_nothing(tmp_path):
    """INV-TT10. Mutant: adding an object list."""
    m = _mem(tmp_path)
    _edge(m, "e-1"); _edge(m, "e-2")
    before = _digest(m)
    p = m.forget_everything_preview(U, issuer=_issuer(m, {"t": T0}))
    assert set(p) == {"counts", "expires_at", "preview_token", "warning"}
    assert p["counts"] == {"edges": 2, "episodes": 0, "confirmations": 0, "replies": 0}
    assert "o-e-1" not in json.dumps(p) and _digest(m) == before


def test_confirm_erases_the_previewed_user_and_only_that_user(tmp_path):
    m = _mem(tmp_path)
    _edge(m, "e-1"); _edge(m, "e-other", user="v")
    clock = {"t": T0}
    iss = _issuer(m, clock)
    r = m.forget_everything_confirm(U, m.forget_everything_preview(U, issuer=iss)["preview_token"], issuer=iss)
    assert r["edges"] == 1 and _count(m, "edges") == 0 and _count(m, "edges", "v") == 1


@pytest.mark.parametrize("case", ["forged", "another_user", "another_issuer", "expired", "future", "write_after"])
def test_each_refusal_erases_nothing(tmp_path, case):
    """INV-TT8: one case per reason. Mutant: each refusal branch removed in turn."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    clock = {"t": T0}
    iss = _issuer(m, clock)
    tok = m.forget_everything_preview(U, issuer=iss)["preview_token"]
    expected = "preview_unknown"
    if case == "forged":
        tok = tok[:-2] + ("AA" if tok[-2:] != "AA" else "BA")
    elif case == "another_user":
        _edge(m, "e-v", user="v")
        other = _issuer(m, clock, user="v")
        tok = m.forget_everything_preview("v", issuer=other)["preview_token"]
    elif case == "another_issuer":
        iss = _issuer(m, clock)
    elif case == "expired":
        clock["t"] += 600
        expected = "preview_expired"
    elif case == "future":
        clock["t"] -= 1
    elif case == "write_after":
        _edge(m, "e-2")
        expected = "store_changed"
    before = _digest(m)
    with pytest.raises(TrustRefused) as ei:
        m.forget_everything_confirm(U, tok, issuer=iss)
    assert ei.value.reason == expected and _digest(m) == before


def test_replay_is_key_set_equality_not_one_use(tmp_path):
    """INV-TT8 (TT-R2-04): after a successful erase of non-empty sets a replay is store_changed; with the same ids
    restored it erases again; with empty bound sets it erases again. Mutant: a replay that ignores key-set equality."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    clock = {"t": T0}
    iss = _issuer(m, clock)
    tok = m.forget_everything_preview(U, issuer=iss)["preview_token"]
    m.forget_everything_confirm(U, tok, issuer=iss)
    with pytest.raises(TrustRefused, match="store_changed"):
        m.forget_everything_confirm(U, tok, issuer=iss)
    _edge(m, "e-1")                                             # the same id restored
    assert m.forget_everything_confirm(U, tok, issuer=iss)["edges"] == 1
    empty = m.forget_everything_preview(U, issuer=iss)["preview_token"]
    assert m.forget_everything_confirm(U, empty, issuer=iss)["edges"] == 0
    assert m.forget_everything_confirm(U, empty, issuer=iss)["edges"] == 0     # empty sets: erases again


def test_an_in_place_update_does_not_void_the_token_and_an_insert_or_delete_does(tmp_path):
    """INV-TT14's per-table cases on edges (the digest binds key sets, not contents)."""
    for case, expect in [("update", "ok"), ("insert", "store_changed"), ("delete", "store_changed")]:
        m = _mem(tmp_path / case)
        _edge(m, "e-1"); _edge(m, "e-2")
        clock = {"t": T0}
        iss = _issuer(m, clock)
        tok = m.forget_everything_preview(U, issuer=iss)["preview_token"]
        if case == "update":
            m.store._conn.execute("UPDATE edges SET object='changed' WHERE id='e-1'")
            m.store._conn.commit()
        elif case == "insert":
            _edge(m, "e-3")
        else:
            m.store._conn.execute("DELETE FROM edges WHERE id='e-2'")
            m.store._conn.commit()
        if expect == "ok":
            assert m.forget_everything_confirm(U, tok, issuer=iss)["edges"] == 2
        else:
            with pytest.raises(TrustRefused, match=expect):
                m.forget_everything_confirm(U, tok, issuer=iss)


@pytest.mark.parametrize("table", ["episodes", "confirmations", "replies"])
def test_an_insert_in_each_other_previewed_table_voids_the_token(tmp_path, table):
    """INV-TT14: the digest spans all four tables. Mutant: the digest omitting any one of them."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    clock = {"t": T0}
    iss = _issuer(m, clock)
    tok = m.forget_everything_preview(U, issuer=iss)["preview_token"]
    if table == "episodes":
        from veracium.schema import Episode
        m.store.add_episode(Episode(id="ep-n", user_id=U, date="2026-11-01", summary="s",
                                    provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="r")))
    elif table == "confirmations":
        m.confirm(U, "e-1")
    else:
        m.reply(U, "e-1", kind="context", text="a note")
    with pytest.raises(TrustRefused, match="store_changed"):
        m.forget_everything_confirm(U, tok, issuer=iss)


def test_a_policy_receipt_written_between_the_steps_does_not_void_the_token(tmp_path):
    """INV-TT14: a row in a table the preview does not bind (a policy_receipt that really appears). Mutant: the
    digest spanning every erased table."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    clock = {"t": T0}
    iss = _issuer(m, clock)
    tok = m.forget_everything_preview(U, issuer=iss)["preview_token"]
    n = m.store._conn.execute("SELECT COUNT(*) FROM policy_receipt").fetchone()[0]
    m.store.write_policy_receipt(U, {"recall_id": "r-1", "policy_id": "p", "policy_version": 1,
                                     "recorded_at": "2026-11-15T00:00:00+00:00", "receipt": "{}"})
    assert m.store._conn.execute("SELECT COUNT(*) FROM policy_receipt").fetchone()[0] == n + 1
    assert m.forget_everything_confirm(U, tok, issuer=iss)["edges"] == 1
    assert _count(m, "policy_receipt") == 0                       # erased with the user, uncounted


def test_the_check_and_the_erase_are_one_write_transaction(tmp_path, monkeypatch):
    """INV-TT9: a failure injected mid-erase leaves every table unchanged; a second connection cannot write between
    the digest check and the deletes. Mutants: the check moved outside the transaction; a second committing erase."""
    m = _mem(tmp_path)
    _edge(m, "e-1"); _edge(m, "e-2")
    clock = {"t": T0}
    iss = _issuer(m, clock)
    tok = m.forget_everything_preview(U, issuer=iss)["preview_token"]
    from veracium.store import sqlite as S
    real = S._ERASE_TABLES
    monkeypatch.setattr(S, "_ERASE_TABLES", real[:3] + ("no_such_table",) + real[3:])
    before = _digest(m)
    with pytest.raises(sqlite3.OperationalError):
        m.forget_everything_confirm(U, tok, issuer=iss)
    assert _digest(m) == before
    monkeypatch.setattr(S, "_ERASE_TABLES", real)
    # inside the erase's transaction another connection's write is refused (BEGIN IMMEDIATE holds the write lock)
    seen = {}
    orig = m.store._erase_preview_keys

    def probe(user_id):
        other = sqlite3.connect(str(tmp_path / "v.db"), timeout=0.05)
        try:
            other.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
                          "VALUES('e-x','u','user','r','o',1,0,'{}')")
            other.commit()
            seen["wrote"] = True
        except sqlite3.OperationalError:
            seen["wrote"] = False
        finally:
            other.close()
        return orig(user_id)
    monkeypatch.setattr(m.store, "_erase_preview_keys", probe)
    m.forget_everything_confirm(U, tok, issuer=iss)
    assert seen == {"wrote": False} and _count(m, "edges") == 0


def test_the_preview_counts_and_digest_come_from_one_snapshot(tmp_path):
    """INV-TT20: a second connection's insert BETWEEN the preview's table reads cannot land, so the four lists, the
    counts and the digest are one snapshot (the store's rollback journal: an open read transaction holds the lock a
    writer's commit needs). The confirm then erases exactly the previewed set. Mutant: the reads taken outside one
    transaction (the insert would land between them)."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    from veracium.store import sqlite as S
    calls = {"n": 0}
    real = S.SqliteStore._erase_preview_keys

    def interleaved(self, user_id):
        out = {}
        from veracium.trust_tools import ERASE_PREVIEW_TABLES, _sorted_keys
        for t in ERASE_PREVIEW_TABLES:
            out[t] = _sorted_keys(r[0] for r in self._conn.execute(f"SELECT id FROM {t} WHERE user_id=?", (user_id,)))
            if t == "edges" and calls["n"] == 0:
                calls["n"] += 1
                other = sqlite3.connect(str(tmp_path / "v.db"), timeout=0.05)
                try:
                    other.execute("INSERT INTO episodes(id,user_id,date,json) VALUES('ep-x','u','2026-11-01','{}')")
                    other.commit()
                    calls["landed"] = True
                except sqlite3.OperationalError:
                    calls["landed"] = False
                finally:
                    other.close()
        return out
    S.SqliteStore._erase_preview_keys = interleaved
    try:
        clock = {"t": T0}
        iss = _issuer(m, clock)
        p = m.forget_everything_preview(U, issuer=iss)
    finally:
        S.SqliteStore._erase_preview_keys = real
    assert calls == {"n": 1, "landed": False} and p["counts"]["episodes"] == 0
    assert m.forget_everything_confirm(U, p["preview_token"], issuer=iss)["edges"] == 1


def test_both_steps_refuse_any_principal_and_write_nothing(tmp_path):
    """INV-TT17's library half: a token issued with no principal, then confirmed under one."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    clock = {"t": T0}
    iss = _issuer(m, clock)
    P = Identity(None, "src-a")
    before = _digest(m)
    with pytest.raises(TrustRefused, match="principal_scoped"):
        m.forget_everything_preview(U, issuer=iss, principal=P)
    tok = m.forget_everything_preview(U, issuer=iss)["preview_token"]
    with pytest.raises(TrustRefused, match="principal_scoped"):
        m.forget_everything_confirm(U, tok, issuer=iss, principal=P)
    assert _digest(m) == before


def test_a_refused_confirm_is_counted_by_reason_with_no_content(tmp_path):
    """§4f: the operator's discard counter, through `_record`."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    seen = []
    m._record = lambda kind, data, user_id: seen.append((kind, data, user_id))
    iss = _issuer(m, {"t": T0})
    with pytest.raises(TrustRefused):
        m.forget_everything_confirm(U, "tt1.x.y", issuer=iss)
    assert seen == [("erase_refused", {"reason": "preview_unknown"}, U)]
