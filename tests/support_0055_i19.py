"""specs/0055 I19's map-driven sweep: the instrument and the scenarios. Loaded BY PATH by
tests/test_0055_i19_digest_sweep.py (tests/ is not a package), which holds the expectations and the assertions.

THE INSTRUMENT. While a scenario's operation runs, `hashlib.sha256` is replaced by a recording wrapper: every digest
finalised records its exact input bytes, its hex value and the veracium frames on the stack (innermost first, as
(path under src/veracium, qualified name)). A map row's SITE is (the innermost veracium frame, which calls hashlib
itself; the frames that must appear further out; optionally frames that must NOT). After the operation, every SINK
is read: every column of every table of the store (blobs as hex), the operation's result (base64url token segments
decoded), the AuditLog when one is attached, an export of the user, and any sink the scenario names (a diagnostics
hook). A digest is FOUND in a sink when its first sixteen hex digits occur there.

A SCENARIO is `run(ctx, value) -> result`: it builds its own store under ctx.tmp, plants `value` into ONE
legacy-capable component (straight into sqlite or into an import file, as a pre-0055 store or file holds it: the
0055 screens refuse or mask the same value written through the API), and runs the operation inside `with ctx.tap:`.

The test runs each scenario twice: a CONTROL with a plain marker, which must reach the site carrying the marker (the
proof that the scenario drives this component into this digest, so a clean shaped run is not vacuous), and the
SHAPED run with a credential-shaped value (a GitHub-token shape from specs/evidence/0055/vectors.py).

Scenario provenance: rows 8, 9, 14-17, 26-33 and P written by dev; rows 1-3, 6, 7, 10, 11, 13, 34-36 and rows 12,
18-25 drafted by two delegated readers against this instrument, 2026-11-23, and re-run by the test on every build.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import veracium
from veracium import EvidenceAuthor, EvidenceContext, Memory, MemoryConfig
from veracium.audit import AuditLog
from veracium.contribution import evidence_ref_digest
from veracium.schema import DEFAULT_RELATIONS, Edge, Provenance, Relation
from veracium.source_identity import source_identity_digest
from veracium.store import data_migration as DM

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = pathlib.Path(veracium.__file__).resolve().parent


def _load(name, path):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


inv = _load("_0055_i19_invariants_helpers", ROOT / "tests" / "test_0055_invariants.py")
T6 = _load("t6_operation_helpers_0044", ROOT / "tests" / "test_0044_t6_operation.py")
V = inv.V
GH = V.GH
EC, EA = EvidenceContext, EvidenceAuthor
PLAIN = MARK = C = "plainmarkerzq1"
ORIGIN = "org-x"                     # the hand-written ledger file's provenance.origin (fixed, so digests are fixed)
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)
MAP_PATH = ROOT / "specs" / "evidence" / "0055" / "digests.json"
MAP = json.loads(MAP_PATH.read_text(encoding="utf-8"))
_comp: dict = {}
for _r in MAP["rows"]:
    _comp.setdefault(_r["row"], []).append(_r["component"])


def comp(row, i):
    return _comp[row][i]


# ==== the tap ==========================================================================================================
_REAL = hashlib.sha256


def _norm(q: str) -> str:
    return q.replace(".<locals>", "")


def _frames():
    out, f = [], sys._getframe(2)
    while f is not None:
        try:
            rel = pathlib.Path(f.f_code.co_filename).resolve().relative_to(SRC).as_posix()
        except ValueError:
            rel = None
        if rel is not None:
            out.append((rel, _norm(f.f_code.co_qualname), f.f_lineno))
        f = f.f_back
    return tuple(out)


class Tap:
    """Records every sha256 finalised while ON: (input bytes, hexdigest, frames). `with tap:` turns it on and off and
    restores the real constructor however the block exits."""

    def __init__(self):
        self.calls, self.on = [], False

    def _cls(self):
        tap = self

        class _H:
            name, digest_size, block_size = "sha256", 32, 64

            def __init__(self, data=b"", *, usedforsecurity=True, string=None, _h=None, _buf=None, _fr=None):
                data = string if string is not None else data
                self._h = _h if _h is not None else _REAL(bytes(data))
                self._buf = bytearray(_buf if _buf is not None else bytes(data))
                self._fr = _fr if _fr is not None else (_frames() if tap.on else ())

            def update(self, b):
                self._h.update(b)
                self._buf += bytes(b)

            def copy(self):
                return _H(_h=self._h.copy(), _buf=bytes(self._buf), _fr=self._fr)

            def _log(self):
                if tap.on and self._fr:
                    tap.calls.append((bytes(self._buf), self._h.hexdigest(), self._fr))

            def digest(self):
                self._log()
                return self._h.digest()

            def hexdigest(self):
                self._log()
                return self._h.hexdigest()

        return _H

    def __enter__(self):
        hashlib.sha256 = self._cls()
        self.on = True
        return self

    def __exit__(self, *exc):
        self.on = False
        hashlib.sha256 = _REAL
        return False


def _frame_in(q: str, frames) -> bool:
    """An outer frame matches by qualified name or as its prefix (a generator or nested function inside it)."""
    return any(q == fq or fq.startswith(q + ".") for fq in frames)


def at_site(call, site) -> bool:
    buf, h, fr = call
    inner, outer = site[0], site[1]
    not_outer = site[2] if len(site) > 2 else ()
    if not fr or (fr[0][0], fr[0][1]) != inner:
        return False
    rest = {}
    for f, q, _ in fr[1:]:
        rest.setdefault(f, set()).add(q)
    ok = all(_frame_in(q, rest.get(f, ())) for f, q in outer)
    return ok and not any(_frame_in(q, rest.get(f, ())) for f, q in not_outer)


def _decode_tokens(s: str) -> str:
    out = []
    for seg in s.replace(":", ".").replace('"', ".").replace("\x00", ".").split("."):
        if len(seg) >= 16:
            try:
                out.append(base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4)).decode("utf-8", "replace"))
            except (binascii.Error, ValueError):
                pass
    return "\n".join(out)


def carries(buf: bytes, needle: str) -> bool:
    """The needle in a digest's input: as bytes, or inside a base64url segment of it (the preview token's MAC is
    over the base64url payload that carries the snapshot digest)."""
    nb = needle.encode()
    return nb in buf or needle in _decode_tokens(buf.decode("ascii", "replace"))


# ==== the run ==========================================================================================================
class Ctx:
    def __init__(self, tmp: pathlib.Path):
        self.tmp, self.tap, self.mem, self.audit, self.extra_sinks, self.exc = tmp, Tap(), None, None, {}, None

    @property
    def db(self) -> str:
        return self.mem.config.db_path


def sinks(ctx: Ctx, result) -> dict:
    out = {}
    con = sqlite3.connect(ctx.db)
    try:
        for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            cols = [r[1] for r in con.execute(f"PRAGMA table_info('{t}')")]
            for row in con.execute(f"SELECT * FROM '{t}'"):
                for c, v in zip(cols, row):
                    s = v.hex() if isinstance(v, (bytes, bytearray)) else str(v)
                    out[f"{t}.{c}"] = out.get(f"{t}.{c}", "") + "\n" + s.lower()
    finally:
        con.close()
    r = json.dumps(result, default=repr, sort_keys=True) if result is not None else ""
    out["returned"] = (r + "\n" + _decode_tokens(r)).lower()
    if ctx.audit is not None and pathlib.Path(ctx.audit).exists():
        out["audit"] = pathlib.Path(ctx.audit).read_text().lower()
    for k, v in ctx.extra_sinks.items():
        out[k] = str(v).lower()
    return out


@dataclass
class Obs:
    reached: bool
    carries: bool
    raised: object
    found: list = field(default_factory=list)          # per carrying digest at the site: the sink labels holding it
    hexes: list = field(default_factory=list)          # those digests' values
    carrying: list = field(default_factory=list)       # every carrying digest anywhere: (hex, frames)
    labels_of: dict = field(default_factory=dict)      # hex -> the sink labels holding it, for every carrying digest
    result: object = None


def observe(scenario, site, value, needle, *, user="u", needle_from=None) -> Obs:
    """`needle_from` = (site, base needle): the needle is the hex of the first digest at that site carrying the base
    needle (row 33: the MAC is over the payload carrying row 32's snapshot digest)."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="i19-"))
    ctx = Ctx(tmp)
    result = None
    try:
        result = scenario(ctx, value)
    except Exception as exc:                          # a refusal is an observation, not a failure of the harness
        ctx.exc = exc
    ctx.tap.on = False
    calls = list(ctx.tap.calls)
    if needle_from is not None:
        s2, base = needle_from
        firsts = [h for c in calls if at_site(c, s2) and carries(c[0], base) for h in [c[1]]]
        needle = firsts[0] if firsts else "\x00no-such-digest\x00"
    if ctx.mem is not None:
        try:
            p = tmp / "export.jsonl"
            ctx.mem.export_memory(user, str(p))
            ctx.extra_sinks["export"] = p.read_text()
        except Exception as exc:                      # noqa: BLE001 - an export refusal is recorded, not raised
            ctx.extra_sinks["export"] = f"export failed: {type(exc).__name__}"
    sk = sinks(ctx, result) if ctx.mem is not None else {}
    at = [c for c in calls if at_site(c, site)]
    hit = [c for c in at if carries(c[0], needle)]
    carrying = [(h, fr) for buf, h, fr in calls if carries(buf, needle)]
    labels_of = {h: sorted(lbl for lbl, txt in sk.items() if h[:16] in txt) for h, _ in carrying}
    if ctx.mem is not None:
        ctx.mem.close()
    return Obs(reached=bool(at), carries=bool(hit), raised=ctx.exc, found=[labels_of[h] for _, h, _ in hit],
               hexes=[h for _, h, _ in hit], carrying=carrying, labels_of=labels_of, result=result)


# ====================================================================================================================
# SCENARIOS, dev: rows 4, 5, 8, 9, 14-17, 26-33, P
# ====================================================================================================================
def _con(db):
    return sqlite3.connect(db)


def plant_prov(db, table, rid, **prov):
    """A legacy provenance field (origin, source_id, evidence_ref) planted in a stored edge or episode row and its
    latest journal snapshot."""
    ev, key = ("edge_event", "edge_id") if table == "edges" else ("episode_event", "episode_id")
    con = _con(db)
    js = json.loads(con.execute(f"SELECT json FROM {table} WHERE id=?", (rid,)).fetchone()[0])
    js["provenance"].update(prov)
    con.execute(f"UPDATE {table} SET json=? WHERE id=?", (json.dumps(js), rid))
    con.execute(f"UPDATE {ev} SET state=? WHERE {key}=? AND seq=(SELECT MAX(seq) FROM {ev} WHERE {key}=?)",
                (json.dumps(js), rid, rid))
    con.commit()
    con.close()


def rename(db, table, old, new):
    """A legacy record id: the row, its journal and every reference renamed."""
    con = _con(db)
    if table == "edges":
        js = json.loads(con.execute("SELECT json FROM edges WHERE id=?", (old,)).fetchone()[0])
        js["id"] = new
        con.execute("UPDATE edges SET id=?, json=? WHERE id=?", (new, json.dumps(js), old))
        con.execute("UPDATE edge_event SET edge_id=? WHERE edge_id=?", (new, old))
        for t in ("confirmations", "replies"):
            con.execute(f"UPDATE {t} SET edge_id=? WHERE edge_id=?", (new, old))
    elif table == "episodes":
        js = json.loads(con.execute("SELECT json FROM episodes WHERE id=?", (old,)).fetchone()[0])
        js["id"] = new
        con.execute("UPDATE episodes SET id=?, json=? WHERE id=?", (new, json.dumps(js), old))
        con.execute("UPDATE episode_event SET episode_id=? WHERE episode_id=?", (new, old))
    else:
        con.execute(f"UPDATE {table} SET id=? WHERE id=?", (new, old))
    con.commit()
    con.close()


# ---- rows 26, 27: revoke_source over a legacy source (D3) ----------------------------------------------------------
def revoke_over(field):
    def run(ctx, v):
        ctx.audit = str(ctx.tmp / "audit.jsonl")
        ctx.mem = inv._mem(ctx.tmp, audit=AuditLog(ctx.audit))
        e = inv._seed_edge(ctx.mem)
        plant_prov(ctx.db, "edges", e.id, **{field: v})
        origin, sid = (v, "chat") if field == "origin" else (None, v)
        with ctx.tap:
            return ctx.mem.revoke_source("u", origin, sid, "policy")
    return run


# ---- rows 28-30: embeddings ------------------------------------------------------------------------------------------
class Embed:
    def id(self):
        return "i19-embed@1"

    def dim(self):
        return 3

    def __call__(self, texts):
        return [[float(len(t) % 7), 1.0, 0.5] for t in texts]


def embed_over(field, op="backfill"):
    def run(ctx, v):
        ctx.mem = inv._mem(ctx.tmp, embed=Embed())
        e = inv._seed_edge(ctx.mem)
        inv._plant(ctx.db, e.id, **{field: (v if field == "note" else f"x {v}")})
        if op == "backfill":
            with ctx.tap:
                return ctx.mem.embed_backfill("u")
        ctx.mem.embed_backfill("u")
        with ctx.tap:
            return ctx.mem.recall("u", "where do I live", semantic=True)
    return run


# ---- rows 32, 33: the erase preview ------------------------------------------------------------------------------
def preview_over(table):
    def run(ctx, v):
        from veracium.trust_tools import PreviewTokenIssuer
        ctx.mem = inv._mem(ctx.tmp)
        e = inv._seed_edge(ctx.mem)
        if table == "edges":
            rename(ctx.db, "edges", e.id, v)
        elif table == "episodes":
            ctx.mem.remember("u", "I live in Denver", context=EC.direct())
            ep = ctx.mem.store.episodes("u")[0].id
            rename(ctx.db, "episodes", ep, v)
        elif table == "confirmations":
            r = ctx.mem.confirm("u", e.id)
            con = _con(ctx.db)
            con.execute("UPDATE confirmations SET id=? WHERE edge_id=?", (v, e.id))
            con.commit()
            con.close()
        elif table == "replies":
            r = ctx.mem.reply("u", e.id, kind="context", text="plain words")
            rename(ctx.db, "replies", r["reply_id"], v)
        issuer = PreviewTokenIssuer(ctx.mem.store.local_origin(), "u")
        with ctx.tap:
            return ctx.mem.forget_everything_preview("u", issuer=issuer)
    return run


# ---- row 16: redaction over a legacy provenance -----------------------------------------------------------------
def redact_over(field):
    def run(ctx, v):
        ctx.mem = inv._mem(ctx.tmp)
        e = inv._seed_edge(ctx.mem)
        plant_prov(ctx.db, "edges", e.id, **{field: v})
        with ctx.tap:
            return ctx.mem.redact("u", edge_id=e.id, reason="subject_request")
    return run


# ---- rows 8, 9, 14: consolidation over legacy input episodes ----------------------------------------------------
class Compactor:
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        return json.dumps({"records": [{"date": "2020-01-01", "summary": "compacted A"},
                                       {"date": "2020-06-01", "summary": "compacted B"}]})


def consolidate_over(field, standing=False):
    def run(ctx, v):
        from veracium.schema import Disclosure, Episode, Provenance
        ctx.audit = str(ctx.tmp / "audit.jsonl")
        ctx.mem = Memory(llm=Compactor(), config=MemoryConfig(db_path=str(ctx.tmp / "c.db"),
                                                              wiki_recompile_after_writes=0),
                         audit=AuditLog(ctx.audit))
        old = (datetime.now(timezone.utc) - timedelta(days=400)).date().isoformat()
        for i in range(9):
            ctx.mem.store.add_episode(Episode(
                id=f"ep{i}", user_id="u", date=old, summary=f"cold episode {i}",
                provenance=Provenance(author_of_evidence=EA.USER, evidence_ref=f"ev{i}", source_id="feed",
                                      disclosure=Disclosure.MENTIONABLE, observed_at=datetime.now(timezone.utc))))
        for i in range(9):
            plant_prov(ctx.db, "episodes", f"ep{i}", **{field: v})
        if standing:                       # partition_cold digests provenance only under a standing revocation
            ctx.mem.revoke_source("u", None, "another-feed", "policy")
        with ctx.tap:
            return ctx.mem.maintain("u", consolidate=True)
    return run


# ---- row P: the diagnostics digests over provider text ----------------------------------------------------------
class Rec:
    def __init__(self):
        self.seen = []

    def record_degrade(self, where, kind, fields):
        self.seen.append(json.dumps(fields))

    def record_error(self, where, exc, ctx):
        self.seen.append(str(exc))


class Noisy(inv.Stub):
    def __init__(self, v, mode):
        super().__init__()
        self.v, self.mode = v, mode

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            if self.mode == "answer":
                return "not json at all, the answer echoes " + self.v
            # an off-vocabulary triple sends the batch to the retry call (ingest's `failing`)
            return json.dumps({"episode": "noted", "triples": [{"subject": "user", "relation": "zz_not_a_relation",
                                                                "object": "Denver", "volatility": "durable"}]})
        if role == "distill-retry":
            if self.mode == "error":
                raise RuntimeError("provider failed: " + self.v)
            return "still not json, the retry echoes " + (self.v if self.mode == "retry" else "nothing")
        return super().__call__(prompt, system=system, role=role, json_schema=json_schema)


def provider_over(mode):
    def run(ctx, v):
        rec = Rec()
        ctx.mem = Memory(llm=Noisy(v, mode), config=MemoryConfig(db_path=str(ctx.tmp / "m.db"),
                                                                  wiki_recompile_after_writes=0), diagnostics=rec)
        ctx.extra_sinks["diagnostics"] = rec.seen
        with ctx.tap:
            out = ctx.mem.remember("u", "I live in Denver", context=EC.direct())
        ctx.extra_sinks["diagnostics"] = "\n".join(rec.seen)
        return out
    return run


# ---- row 15: why.gather (the CLI's `veracium why`) over a legacy provenance ----------------------------------------
def why_over(field):
    def run(ctx, v):
        from veracium import why as _why
        ctx.mem = inv._mem(ctx.tmp)
        e = inv._seed_edge(ctx.mem)
        plant_prov(ctx.db, "edges", e.id, **{field: v})
        with ctx.tap:
            bio = _why.gather(ctx.mem.store, "u", e.id)
        return {"revoked_source": bio.revoked_source, "verdict": bio.verdict, "notes": bio.notes}
    return run


# ---- row 31: as-of classification over legacy text ----------------------------------------------------------------
def plant_one_side(db, edge_id, field, value, where):
    """A legacy text field planted in the current row only (`cur`) or in the latest journal snapshot only (`snap`)."""
    con = _con(db)
    if where == "cur":
        js = json.loads(con.execute("SELECT json FROM edges WHERE id=?", (edge_id,)).fetchone()[0])
        js[field] = value
        con.execute("UPDATE edges SET json=?, subject=?, relation=?, object=? WHERE id=?",
                    (json.dumps(js), js["subject"], js["relation"], js["object"], edge_id))
    else:
        seq, st = con.execute("SELECT seq, state FROM edge_event WHERE edge_id=? ORDER BY seq DESC LIMIT 1",
                              (edge_id,)).fetchone()
        js = json.loads(st)
        js[field] = value
        con.execute("UPDATE edge_event SET state=? WHERE edge_id=? AND seq=?", (json.dumps(js), edge_id, seq))
    con.commit()
    con.close()


def asof_over(field, where="both"):
    def run(ctx, v):
        ctx.mem = inv._mem(ctx.tmp)
        e = inv._seed_edge(ctx.mem)
        text = v if field == "note" else f"x {v}"
        if where == "both":
            inv._plant(ctx.db, e.id, **{field: text})
        else:
            plant_one_side(ctx.db, e.id, field, text, where)
        if where == "snap":
            field_for_query = None          # the query names the CURRENT row's subject/relation
        else:
            field_for_query = field
        T = datetime.now(timezone.utc)
        subj = f"x {v}" if field_for_query == "subject" else "user"
        rel = f"x {v}" if field_for_query == "relation" else "located_at"
        with ctx.tap:
            out = ctx.mem.facts_valid_at("u", subj, rel, T)
        return [repr(x) for x in out]
    return run


# ---- row 17: an imported redaction notice ---------------------------------------------------------------------------
def notice_over(field):
    def run(ctx, v):
        a = inv._mem(ctx.tmp, "a")
        e = inv._seed_edge(a)
        a.redact("u", edge_id=e.id, reason="subject_request")
        p = ctx.tmp / "x.jsonl"
        a.export_memory("u", str(p))
        a.close()
        lines = []
        for line in p.read_text().splitlines():
            j = json.loads(line)
            if field == "target_id":
                if j.get("record") == "edge" and j.get("id") == e.id:
                    j["id"] = v
                if j.get("record") == "redaction":
                    j["target_id"] = v
            elif j.get("record") == "redaction":
                j[field] = v
            lines.append(json.dumps(j))
        p.write_text("\n".join(lines) + "\n")
        ctx.mem = inv._mem(ctx.tmp, "b")
        with ctx.tap:
            return ctx.mem.import_memory(str(p), user_id="u")
    return run


# ---- rows 4, 5: confirm and reply over a legacy record id ---------------------------------------------------------
def confirm_over(ctx, v):
    ctx.mem = inv._mem(ctx.tmp)
    e = inv._seed_edge(ctx.mem)
    rename(ctx.db, "edges", e.id, v)
    with ctx.tap:
        return ctx.mem.confirm("u", v)


def reply_over(component):
    """`edge_id`: a context reply on a legacy edge id. `target`: a resolve whose target is a legacy challenge id."""
    def run(ctx, v):
        ctx.mem = inv._mem(ctx.tmp)
        e = inv._seed_edge(ctx.mem)
        if component == "edge_id":
            rename(ctx.db, "edges", e.id, v)
            with ctx.tap:
                return ctx.mem.reply("u", v, kind="context", text="plain words")
        ch = ctx.mem.reply("u", e.id, kind="challenge", text="that is wrong")
        rename(ctx.db, "replies", ch["reply_id"], v)
        with ctx.tap:
            return ctx.mem.reply("u", e.id, kind="resolve", target=v)
    return run


# ====================================================================================================================
# SCENARIOS, reader A: rows 1-3, 6, 7, 10, 11, 13, 34-36
# ====================================================================================================================
# ---- sites (innermost (file, qualname) that calls hashlib; outer frames that must appear further out) -------------
SQL = "store/sqlite.py"
SID = ("source_identity.py", "source_identity_digest")
SITE1 = ((SQL, "SqliteStore._logical_request_digest"), [])
SITE2 = ((SQL, "SqliteStore._outcome_digest_v2"), [])
SITE3 = (("authority.py", "scope_fingerprint"), [])
SITE6 = (SID, [(SQL, "SqliteStore._write_contribution")])
SITE7 = (("contribution.py", "evidence_ref_digest"), [(SQL, "SqliteStore._write_contribution")])
SITE10 = (("scope_linkage.py", "native_row_op_key"), [(SQL, "SqliteStore._write_absorption_flattening")])
# row 11 is a COPY (no hash of its own); the only hash that can feed it is the legacy recomputation in _legacy,
# reached from the flattening write
SITE11 = (SID, [("scope_read.py", "MembershipResolver._legacy"), (SQL, "SqliteStore._write_absorption_flattening")])
SITE13 = (SID, [("graph.py", "_build_supersession_plan._src_revoked")])
SITE34 = (SID, [("scope.py", "digest_of"), ("scope.py", "membership")])
SITE35 = (SID, [("scope_read.py", "MembershipResolver._legacy")])
SITE36 = (SID, [("scope_read.py", "MembershipResolver.evidence")])
# the confirm/reply sites from the example, so their hashes are not reported as strays
SITE4 = (("__init__.py", "Memory.confirm"), [])
SITE5 = (("schema.py", "reply_request_digest"), [])
MAPPED_A = [SITE1, SITE2, SITE3, SITE6, SITE7, SITE10, SITE11, SITE13, SITE34, SITE35, SITE36, SITE4, SITE5]


# ---- building blocks ------------------------------------------------------------------------------------------------
class OStub(inv.Stub):
    """The test Stub, but the extractor answers the NEXT triple of a queue (the last one repeats)."""

    def __init__(self, triples):
        super().__init__()
        self.triples = [dict(t) for t in triples]
        self.n = 0

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            self.prompts.append((role, prompt))
            t = self.triples[min(self.n, len(self.triples) - 1)]
            self.n += 1
            return json.dumps({"episode": "noted", "triples": [dict(t)]})
        return super().__call__(prompt, system=system, role=role, json_schema=json_schema)


def T(obj, subject="user", relation="located_at"):
    return {"subject": subject, "relation": relation, "object": obj, "volatility": "durable"}


def new_mem(ctx, triples=(T("Denver Colorado"),), relations=None):
    cfg = MemoryConfig(db_path=str(ctx.tmp / "m.db"), wiki_recompile_after_writes=0)
    if relations is not None:
        cfg.relations = relations
    ctx.mem = Memory(llm=OStub(list(triples)), config=cfg)
    return ctx.mem


_N = [0]


def seed(mem, *, uid="u", subject="user", relation="located_at", obj="Denver", source_id="chat",
         author=EvidenceAuthor.USER, note=""):
    _N[0] += 1
    e = Edge(id=f"e-seedA{_N[0]:06d}", user_id=uid, subject=subject, relation=relation, object=obj, note=note,
             provenance=Provenance(author_of_evidence=author, evidence_ref=f"ev-seedA{_N[0]}", source_id=source_id))
    mem.store.add_edge(e)
    return e.id


def edit(db, eid, fn=None, *, new_id=None, new_uid=None):
    """LEGACY state: rewrite one edge's row (columns + json) and EVERY journal snapshot of it, as a pre-0055 store
    holds it. `fn(js)` mutates the json in place; `new_id` renames the edge everywhere it is keyed."""
    con = sqlite3.connect(db)
    try:
        def apply(js):
            if fn is not None:
                fn(js)
            if new_id is not None:
                js["id"] = new_id
            if new_uid is not None:
                js["user_id"] = new_uid
            return js
        js = json.loads(con.execute("SELECT json FROM edges WHERE id=?", (eid,)).fetchone()[0])
        old_uid = js["user_id"]
        js = apply(js)
        con.execute("UPDATE edges SET id=?, user_id=?, subject=?, relation=?, object=?, json=? WHERE id=?",
                    (js["id"], js["user_id"], js["subject"], js["relation"], js["object"], json.dumps(js), eid))
        for seq, st in con.execute("SELECT seq, state FROM edge_event WHERE edge_id=?", (eid,)).fetchall():
            s = apply(json.loads(st))
            con.execute("UPDATE edge_event SET edge_id=?, state=?, user_id=? WHERE edge_id=? AND seq=?",
                        (s["id"], json.dumps(s), s["user_id"], eid, seq))
        if new_id is not None:
            for tbl, col in (("contribution_ledger", "survivor_id"), ("contribution_ledger", "contributor_ref")):
                con.execute(f"UPDATE {tbl} SET {col}=? WHERE {col}=?", (new_id, eid))
        if new_uid is not None:
            for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                cols = [r[1] for r in con.execute(f"PRAGMA table_info('{t}')")]
                if "user_id" in cols:
                    con.execute(f"UPDATE '{t}' SET user_id=? WHERE user_id=?", (new_uid, old_uid))
        con.commit()
    finally:
        con.close()
    return js["id"]


def setter(path):
    """A json mutator that sets a dotted path ('provenance.evidence_ref', 'agreement.markers', 'note' ...)."""
    def make(value):
        def fn(js):
            if path == "agreement.markers":
                js["agreement"] = {"markers": [value], "direction": "inbound", "lexicon": "legacy-0"}
                return
            if path == "src":                     # specs/0045 §2: src/attv are written only with att
                js.update({"att": "attested", "attv": "ATTEST-3@0123abcd", "src": value})
                return
            node, parts = js, path.split(".")
            for p in parts[:-1]:
                node = node[p]
            node[parts[-1]] = value
        return fn
    return make


def _remember(ctx, text, **kw):
    kw.setdefault("context", EC.direct())
    return ctx.mem.remember(kw.pop("uid", "u"), text, **kw)


# ---- scenario factories ---------------------------------------------------------------------------------------------
def absorb(field=None, *, rename=False, prior_src="chat", inc_src="chat", inc_src_is_value=False,
           prior_obj="Denver", inc_obj="Denver Colorado", obj_from_value=False, subject_from_value=False,
           relation_from_value=False, uid_from_value=False):
    """remember() with an incoming value that SUBSUMES a same-class, same-scope prior (the absorption branch,
    graph.py: `_subsumes(same, prior) and same_scope(prior)`); `value` is planted into the prior."""
    def run(ctx, value):
        subject, relation, pobj, iobj = "user", "located_at", prior_obj, inc_obj
        rels = None
        if obj_from_value:
            pobj, iobj = f"Denver {value}", f"Denver {value} Colorado"
        if subject_from_value:
            subject = value
        if relation_from_value:
            relation = value
            rels = {**DEFAULT_RELATIONS, value: Relation(name=value, functional=True, desc="where the user lives")}
        new_mem(ctx, [T(iobj, subject=subject, relation=relation)], relations=rels)
        # seeded PLAIN through the store (the 0055 store guard refuses a shaped write), then the legacy value planted
        eid = seed(ctx.mem, obj="Denver", source_id=(None if prior_src is None else "chat"))
        legacy = {}
        if subject != "user":
            legacy["subject"] = subject
        if relation != "located_at":
            legacy["relation"] = relation
        if pobj != "Denver":
            legacy["object"] = pobj
        if inc_src_is_value:
            legacy["provenance.source_id"] = value
        if legacy:
            edit(ctx.db, eid, lambda js: [setter(k)(v)(js) for k, v in legacy.items()])
        if rename:
            edit(ctx.db, eid, new_id=value)
        elif uid_from_value:
            edit(ctx.db, eid, new_uid=value)
        elif field is not None:
            edit(ctx.db, eid, setter(field)(value))
        with ctx.tap:
            return _remember(ctx, f"I live in {iobj}", uid=(value if uid_from_value else "u"),
                             source_id=(value if inc_src_is_value else inc_src))
    return run


def supersede(*, author=EvidenceAuthor.USER, prior_author=EvidenceAuthor.USER, plant_object=False):
    """remember() with a DIFFERENT value for the functional `located_at`: the prior is retired ('superseded',
    incoming.supersedes = prior.id) or, when the incoming's authority is lower, the retirement is REFUSED and a
    refusal draft names the prior."""
    def run(ctx, value):
        new_mem(ctx, [T("Boulder")])
        eid = seed(ctx.mem, obj="Denver", author=prior_author)
        if plant_object:
            edit(ctx.db, eid, setter("object")(value))
        else:
            edit(ctx.db, eid, new_id=value)
        with ctx.tap:
            return _remember(ctx, "I moved to Boulder", author=author, source_id="chat")
    return run


PROC_REL = "deploy_steps"


def proc_supersede(ctx, value):
    """record_procedure() under a host-registered FUNCTIONAL procedural relation: the second procedure supersedes
    the first (legacy id planted on the first)."""
    rels = {**DEFAULT_RELATIONS, PROC_REL: Relation(name=PROC_REL, relation_kind="procedural", functional=True,
                                                    desc="how the user deploys")}
    new_mem(ctx, relations=rels)
    kw = dict(author=EvidenceAuthor.USER, context=EC.direct(basis="stated"), relation=PROC_REL)
    eid = ctx.mem.record_procedure("u", "run the unit tests then deploy", **kw)
    edit(ctx.db, eid, new_id=value)
    with ctx.tap:
        return ctx.mem.record_procedure_report("u", "deploy with the release script", **kw)


def proc_absorb(field=None, *, rename=False):
    """record_procedure() whose summary SUBSUMES a stored procedure (default non-functional follows_procedure,
    no source_id on either side, so both are SHARED): the absorption branch on the procedure producer."""
    def run(ctx, value):
        new_mem(ctx)
        kw = dict(author=EvidenceAuthor.USER, context=EC.direct(basis="stated"))
        eid = ctx.mem.record_procedure("u", "run the unit tests", **kw)
        if rename:
            edit(ctx.db, eid, new_id=value)
        elif field is not None:
            edit(ctx.db, eid, setter(field)(value))
        with ctx.tap:
            return ctx.mem.record_procedure_report("u", "run the unit tests first", **kw)
    return run


def correct_over(field=None, *, rename=False, other_subject=False):
    """correct() of a stored prior: `value` planted into the prior's `field` (or the prior renamed to `value`).
    `other_subject` makes the prior's subject 'alice' so the bare self-assertion is REFUSED (a refusal-only plan,
    CorrectionRefused after the durable refusal row commits)."""
    def run(ctx, value):
        new_mem(ctx)
        eid = seed(ctx.mem, obj="Denver", subject=("alice" if other_subject else "user"))
        if rename:
            eid = edit(ctx.db, eid, new_id=value)
        elif field is not None:
            edit(ctx.db, eid, setter(field)(value))
        with ctx.tap:
            return ctx.mem.correct("u", eid, "Boulder")
    return run


def correct_markers(ctx, value):
    """correct() where the prior's note carries a relay marker next to `value`: the replacement's agreement record
    is derive_record(prior.note, corrected_value) — its markers come from the closed lexicon (agreement._VERBS)."""
    new_mem(ctx)
    eid = seed(ctx.mem, obj="Denver")
    edit(ctx.db, eid, setter("note")(f"{value} told me so"))
    with ctx.tap:
        return ctx.mem.correct("u", eid, "Boulder")


def chain(*, plant=None, all_src_value=False):
    """A two-hop NATIVE absorption chain: P0 'Denver' is absorbed by S1 'Denver Colorado' (setup), then the
    incoming 'Denver Colorado USA' absorbs S1, so the flattening write copies P0's row onto the survivor
    (native_row_op_key over contributor_ref = P0.id; identity_digest copied; _legacy recomputes every edge's
    digest). `plant` = 'id' renames P0 to `value`; `all_src_value` gives every hop source_id = `value` (the only
    way a seeded source_id is same-scope along the chain)."""
    def run(ctx, value):
        new_mem(ctx, [T("Denver Colorado"), T("Denver Colorado USA")])
        eid = seed(ctx.mem, obj="Denver", source_id="chat")
        if plant == "id":
            eid = edit(ctx.db, eid, new_id=value)
        r1 = _remember(ctx, "I live in Denver Colorado", source_id="chat")
        if all_src_value:
            # legacy: both stored hops (and their ledger row) were written under source_id <value>
            from veracium.source_identity import source_identity_digest
            s1 = r1_survivor(ctx.db, eid)
            for e in (eid, s1):
                edit(ctx.db, e, setter("provenance.source_id")(value))
            con = sqlite3.connect(ctx.db)
            con.execute("UPDATE contribution_ledger SET identity_digest=?",
                        (source_identity_digest(ctx.mem.store.local_origin(), value),))
            con.commit(); con.close()
        with ctx.tap:
            return _remember(ctx, "I live in Denver Colorado USA", source_id=(value if all_src_value else "chat"))
    return run


def r1_survivor(db, contributor):
    con = sqlite3.connect(db)
    try:
        return con.execute("SELECT survivor_id FROM contribution_ledger WHERE contributor_ref=?",
                           (contributor,)).fetchone()[0]
    finally:
        con.close()


def absorb_with_bystander(ctx, value):
    """An ordinary absorption, plus an UNRELATED edge of the same user whose source_id is `value`: the flattening
    write's MembershipResolver._legacy digests EVERY edge of the user (scope_read.py, the `digs` map)."""
    new_mem(ctx)
    x = seed(ctx.mem, relation="has_pet", obj="cat Miso", source_id="chat")
    edit(ctx.db, x, setter("provenance.source_id")(value))
    seed(ctx.mem, obj="Denver", source_id="chat")
    with ctx.tap:
        return _remember(ctx, "I live in Denver Colorado", source_id="chat")


def cross_scope_held(ctx, value):
    """A subsumption CANDIDATE whose stored source_id is `value` (≠ the incoming's 'chat'): the absorption gate
    asks the resolver for the prior's membership evidence (evidence → _evidence_of → membership → digest_of over
    the held record's shape) and finds it cross-scope, so nothing is absorbed."""
    new_mem(ctx)
    eid = seed(ctx.mem, obj="Denver", source_id="chat")
    edit(ctx.db, eid, setter("provenance.source_id")(value))
    with ctx.tap:
        return _remember(ctx, "I live in Denver Colorado", source_id="chat")


def revoked_guard(ctx, value):
    """A standing revocation exists (another source), so _src_revoked digests every same-class scoped prior; the
    prior's stored source_id is `value`."""
    new_mem(ctx, [T("Boulder")])
    ctx.mem.revoke_source("u", None, "some-other-source", "policy")
    eid = seed(ctx.mem, obj="Denver", source_id="chat")
    edit(ctx.db, eid, setter("provenance.source_id")(value))
    with ctx.tap:
        return _remember(ctx, "I moved to Boulder", source_id="chat")


def revoked_guard_origin(ctx, value):
    """As revoked_guard, with the seeded value in the prior's stored ORIGIN (source_id 'chat')."""
    new_mem(ctx, [T("Boulder")])
    ctx.mem.revoke_source("u", None, "some-other-source", "policy")
    eid = seed(ctx.mem, obj="Denver", source_id="chat")
    edit(ctx.db, eid, setter("provenance.origin")(value))
    with ctx.tap:
        return _remember(ctx, "I moved to Boulder", source_id="chat")


# ---- the rows -------------------------------------------------------------------------------------------------------
ID_C, ID_S = "e-" + PLAIN, "e-" + GH
SRC_C, SRC_S = "src-" + PLAIN, "src-" + GH
TXT_C, TXT_S = PLAIN, "token " + GH
EV_C, EV_S = "ev-" + PLAIN, "ev-" + GH
ORG_C, ORG_S = "org-" + PLAIN, "org-" + GH
UID_C, UID_S = "u-" + PLAIN, "u-" + GH
REL_C, REL_S = "rel-" + PLAIN, "rel-" + GH     # '-' not '_': the recogniser needs a boundary before 'ghp_' 


def _r(row, comp, site, fn, c, s, note, cn=PLAIN, sn=GH):
    return (row, comp, site, fn, c, cn, s, sn, note)


ROWS_A = [
    # ---- row 1: SqliteStore._logical_request_digest --------------------------------------------------------------
    _r(1, "incoming_edge.supersedes [remember]", SITE1, supersede(), ID_C, ID_S,
       "functional located_at, prior renamed; incoming 'Boulder' retires it (incoming.supersedes = prior.id)"),
    _r(1, "incoming_edge.supersedes [procedure]", SITE1, proc_supersede, ID_C, ID_S,
       "host registers a FUNCTIONAL procedural relation (the default follows_procedure is non-functional); "
       "first procedure renamed, the second supersedes it"),
    _r(1, "incoming_edge.subject [correct]", SITE1, correct_over("subject"), TXT_C, TXT_S,
       "prior subject planted; control subject is OTHER so the control is a refused correction (refusal-only plan)"),
    _r(1, "incoming_edge.relation [correct]", SITE1, correct_over("relation"), REL_C, REL_S,
       "prior relation planted (an unregistered relation; correct() does not consult the registry)"),
    _r(1, "incoming_edge.note [correct]", SITE1, correct_over("note"), TXT_C, TXT_S, "prior note planted"),
    _r(1, "incoming_edge.provenance.evidence_ref [correct]", SITE1, correct_over(rename=True), ID_C, ID_S,
       "no evidence_ref passed: the default is f'correct:{edge_id}', edge_id = the renamed prior"),
    _r(1, "incoming_edge.supersedes [correct]", SITE1, correct_over(rename=True), ID_C, ID_S, "prior renamed"),
    _r(1, "incoming_edge.agreement.markers [correct]", SITE1, correct_markers, TXT_C, TXT_S,
       "prior note '<value> told me so': derive_record yields markers ['told'] (closed lexicon)"),
    _r(1, "prior_upserts[].id [remember, procedure: absorption only]", SITE1, absorb(rename=True), ID_C, ID_S,
       "absorption; prior renamed"),
    _r(1, "prior_upserts[].user_id [remember, procedure: absorption only]", SITE1, absorb(uid_from_value=True),
       UID_C, UID_S, "every row of user 'u' moved to user <value>; remember(<value>) — the prior's user_id must equal "
       "the caller's (tenant check)"),
    _r(1, "prior_upserts[].subject [remember, procedure: absorption only]", SITE1, absorb(subject_from_value=True),
       TXT_C, TXT_S, "prior subject = <value>; the scope is (user, subject, relation) so the incoming must carry the "
       "same subject: the extractor answers it"),
    _r(1, "prior_upserts[].relation [remember, procedure: absorption only]", SITE1, absorb(relation_from_value=True),
       REL_C, REL_S, "host registry carries a relation named <value>; prior and extractor triple use it"),
    _r(1, "prior_upserts[].object [remember, procedure: absorption only]", SITE1, absorb(obj_from_value=True),
       TXT_C, TXT_S, "prior object 'Denver <value>'; the incoming must SUBSUME it: extractor answers "
       "'Denver <value> Colorado'"),
    _r(1, "prior_upserts[].note [remember, procedure: absorption only]", SITE1, absorb("note"), TXT_C, TXT_S,
       "absorption; prior note planted"),
    _r(1, "prior_upserts[].provenance.evidence_ref [remember, procedure: absorption only]", SITE1,
       absorb("provenance.evidence_ref"), EV_C, EV_S, "absorption; prior evidence_ref planted"),
    _r(1, "prior_upserts[].provenance.source_id [remember, procedure: absorption only]", SITE1,
       absorb(inc_src_is_value=True), SRC_C, SRC_S,
       "same-scope needs equal source identity: prior AND incoming source_id = <value>"),
    _r(1, "prior_upserts[].provenance.origin [remember, procedure: absorption only]", SITE1,
       absorb("provenance.origin", prior_src=None, inc_src=None), ORG_C, ORG_S,
       "source_id None on both sides (SHARED == SHARED), so a foreign origin on the prior stays same-scope"),
    _r(1, "prior_upserts[].invalidation_reason [remember, procedure: absorption only]", SITE1,
       absorb("invalidation_reason"), TXT_C, TXT_S, "active prior with a legacy invalidation_reason text"),
    _r(1, "prior_upserts[].supersedes [remember, procedure: absorption only]", SITE1, absorb("supersedes"),
       ID_C, ID_S, "prior.supersedes planted"),
    _r(1, "prior_upserts[].original_relation [remember, procedure: absorption only]", SITE1,
       absorb("original_relation"), TXT_C, TXT_S, "prior.original_relation planted"),
    _r(1, "prior_upserts[].agreement.markers [remember, procedure: absorption only]", SITE1,
       absorb("agreement.markers"), TXT_C, TXT_S,
       "prior.agreement = {markers:[<value>], direction:inbound, lexicon:'legacy-0'} (a foreign-lexicon record)"),
    _r(1, "prior_upserts[].src [remember, procedure: absorption only]", SITE1, absorb("src"), TXT_C, TXT_S,
       "prior.src planted"),
    _r(1, "prior_invalidations[].edge_id [remember, procedure]", SITE1, absorb(rename=True), ID_C, ID_S,
       "absorption (invalidation 'absorbed_duplicate'); prior renamed. The functional-supersession path is "
       "EXTRA_A '1-invalidations-functional'"),
    _r(1, "prior_invalidations[].edge_id [correct]", SITE1, correct_over(rename=True), ID_C, ID_S, "prior renamed"),
    _r(1, "refusals[].prior_edge_id [remember/procedure]", SITE1,
       supersede(author=EvidenceAuthor.ASSISTANT), ID_C, ID_S,
       "incoming author ASSISTANT (lower authority) cannot retire the USER prior: a refusal draft names it"),
    _r(1, "refusals[].prior_edge_id [correct]", SITE1, correct_over(rename=True, other_subject=True), ID_C, ID_S,
       "prior subject 'alice' (OTHER): the bare self-assertion correction is refused (CorrectionRefused expected "
       "on BOTH runs)"),
    _r(1, "refusals[].relation [correct]", SITE1, correct_over("relation", other_subject=True), REL_C, REL_S,
       "refused correction (prior subject OTHER); prior relation planted"),
    # ---- row 2 ---------------------------------------------------------------------------------------------------
    _r(2, "contribution_drafts[].contributor_id", SITE2, absorb(rename=True), ID_C, ID_S, "absorption; prior renamed"),
    # ---- row 3 ---------------------------------------------------------------------------------------------------
    _r(3, "e.id of each scoped edge", SITE3, absorb(rename=True), ID_C, ID_S,
       "scope (u, user, located_at) holds the renamed prior (absorption, so no new row carries the id)"),
    _r(3, "e.object", SITE3, supersede(plant_object=True), TXT_C, TXT_S, "prior object planted"),
    # ---- rows 6, 7 -----------------------------------------------------------------------------------------------
    _r(6, "resolve_origin(contributor.provenance.origin, local)", SITE6,
       absorb("provenance.origin"), ORG_C, ORG_S,
       "prior origin planted, source_id 'chat' both sides (source_identity_digest needs a source_id)"),
    _r(6, "contributor.provenance.source_id", SITE6, absorb(inc_src_is_value=True), SRC_C, SRC_S,
       "prior AND incoming source_id = <value> (the scope gate requires equal identity)"),
    _r(7, "resolve_origin(contributor.provenance.origin, local)", SITE7,
       absorb("provenance.origin", prior_src=None, inc_src=None), ORG_C, ORG_S,
       "source_id None both sides (SHARED), foreign origin planted on the prior"),
    _r(7, "contributor.provenance.evidence_ref", SITE7, absorb("provenance.evidence_ref"), EV_C, EV_S,
       "absorption; prior evidence_ref planted"),
    # ---- rows 10, 11 ---------------------------------------------------------------------------------------------
    _r(10, "contributor_ref = an id in the absorbed prior's transitive closure (scope_read.py:270-285)", SITE10,
       chain(plant="id"), ID_C, ID_S, "two-hop native chain; P0 renamed before its own absorption"),
    _r(11, "c[\"identity_digest\"]: copied from a closed ledger row (scope_read.py:277-280), or for a le", SITE11,
       chain(all_src_value=True), SRC_C, SRC_S,
       "two-hop chain, every hop source_id = <value> (same-scope forces equal identity along the chain)"),
    # ---- row 13 --------------------------------------------------------------------------------------------------
    _r(13, "prior.provenance.origin, .source_id", SITE13, revoked_guard, SRC_C, SRC_S,
       "a standing revocation of another source; prior source_id = <value>"),
    # ---- rows 34-36 ----------------------------------------------------------------------------------------------
    _r(34, "record.provenance.origin, .source_id of a held record (_record_shape, scope_read.py:179-18", SITE34,
       cross_scope_held, SRC_C, SRC_S, "subsumption candidate with stored source_id <value>; cross-scope"),
    _r(35, "e.provenance.origin, e.provenance.source_id for EVERY edge of the user, active and quarant", SITE35,
       absorb_with_bystander, SRC_C, SRC_S, "ordinary absorption + an unrelated edge with source_id <value>"),
    _r(36, "delegates to _evidence_of (STORED record row above)", SITE36, cross_scope_held, SRC_C, SRC_S,
       "as row 34"),
]

# extra evidence runs (not map rows): the alternative realistic path for a component the main scenario cannot reach
EXTRA_A = [
    ("13-origin", SITE13, revoked_guard_origin, ORG_C, ORG_S),
    ("1-invalidations-functional", SITE1, supersede(), ID_C, ID_S),
    ("35-chain-src", SITE35, chain(all_src_value=True), SRC_C, SRC_S),
    ("6-origin-sourceless", SITE6, absorb("provenance.origin", prior_src=None, inc_src=None), ORG_C, ORG_S),
    # a compare-only digest whose VALUE equals a persisted one: membership's digest of a same-scope prior is the
    # very digest _write_contribution persists (row 6) — only the cross-scope scenario keeps found == []
    ("34-same-scope", SITE34, absorb(inc_src_is_value=True), SRC_C, SRC_S),
    # the [procedure] half of the absorption-only components
    ("1-upserts-procedure-evidence_ref", SITE1, proc_absorb("provenance.evidence_ref"), EV_C, EV_S),
    ("1-upserts-procedure-id", SITE1, proc_absorb(rename=True), ID_C, ID_S),
    ("2-procedure-contributor_id", SITE2, proc_absorb(rename=True), ID_C, ID_S),
]


# ====================================================================================================================
# SCENARIOS, reader C: rows 12, 18-25
# ====================================================================================================================
# ------------------------------------------------------------------------------------------------------ site specs
def P(f, q):
    return (f, q)


# row_op_key runs at construction (reconstruct_absorption_rows -> construct_plan_row, and its validate_row_plan) AND is
# recomputed by validate_row_plan under plan_row_id (import_memory) and at commit (commit_outcome_import_plan): one site
SITE_12 = (P("scope_linkage.py", "row_op_key"), [P("portability.py", "import_memory")])
SITE_24 = (P("scope_linkage.py", "plan_row_id"), [P("portability.py", "import_memory")])
SITE_25 = (P("source_identity.py", "source_identity_digest"),
           [P("scope_linkage.py", "identity_digest_of"), P("portability.py", "import_memory")],
           [P("scope_linkage.py", "reconstruct_absorption_rows")])          # harness_C's not_outer
SITE_18 = (P("store/data_migration.py", "portable_uid"), [P("store/data_migration.py", "convert_rows")])
SITE_19 = (P("store/data_migration.py", "portable_uid"), [P("store/data_migration.py", "undo_restoration")])
SITE_20 = (P("store/data_migration.py", "portable_uid"), [P("portability.py", "_remap_outcomes")])
SITE_21 = (P("store/data_migration.py", "portable_uid"), [P("portability.py", "_remap_namespace")])
SITE_22 = (P("store/data_migration.py", "portable_uid"), [P("portability.py", "_act_preflight")])
SITE_23 = (P("portability.py", "import_memory"), [])
# the ledger primitives reconstruct_absorption_rows computes under plan_row_id (row 24's identity/evidence components
# are digests OF these; not separate map rows — listed so their raw-value hashing is not reported as stray)
SITE_24_ID = (P("source_identity.py", "source_identity_digest"),
              [P("scope_linkage.py", "reconstruct_absorption_rows")])
SITE_24_EV = (P("contribution.py", "evidence_ref_digest"), [P("scope_linkage.py", "reconstruct_absorption_rows")])
MAPPED_C = [SITE_12, SITE_24, SITE_25, SITE_18, SITE_19, SITE_20, SITE_21, SITE_22, SITE_23]
AUX_C = [SITE_24_ID, SITE_24_EV]


# --------------------------------------------------------------------------------------------------------- helpers
def _write_lines(path, header, records):
    with open(path, "w") as f:
        f.write(json.dumps(header) + "\n")
        for r in records:
            f.write(json.dumps(r) + "\n")
    return path


def _rec(eid, *, obj, reason=None, absorbed_by=None, sid=None, ev=None, origin=ORIGIN, rel="pet"):
    """tests/test_0021_import_linkage.py's `_rec`, for user "u"."""
    r = {"record": "edge", "id": eid, "user_id": "u", "subject": "user", "relation": rel, "object": obj,
         "valid_from": NOW.isoformat(), "note": "", "invalidation_reason": reason,
         "provenance": {"author_of_evidence": "user", "evidence_ref": ev or f"ev-{eid}",
                        "source_id": sid or f"agent-{eid}", "origin": origin,
                        "observed_at": NOW.isoformat(), "confidence": 0.5}}
    if absorbed_by is not None:
        r["absorbed_by_id"] = absorbed_by
    return r


def _ledger_file(ctx, *, w="w-1", l="l-1", sid=None, ev=None):
    """A format-7 export (header user "u") with one absorption: L absorbed_duplicate into W (structured
    absorbed_by_id). A plain, same-user import (no remap): the file's ids reach the ledger keys as written."""
    recs = [_rec(w, obj="cat Miso"), _rec(l, obj="Miso", reason="absorbed_duplicate", absorbed_by=w, sid=sid, ev=ev)]
    return _write_lines(ctx.tmp / "ledger.jsonl", {"kind": "veracium-export", "version": 7, "user_id": "u"}, recs)


def _import_plain(ctx, path, **kw):
    ctx.mem = inv._mem(ctx.tmp, "dest")
    with ctx.tap:
        return ctx.mem.import_memory(str(path), **kw)


def _edit_lines(path, fn):
    """Rewrite each JSONL line through fn(rec) -> rec (header included)."""
    lines = [json.loads(x) for x in pathlib.Path(path).read_text().splitlines() if x.strip()]
    pathlib.Path(path).write_text("".join(json.dumps(fn(r)) + "\n" for r in lines))
    return path


# ---- row 12 / row 24: the import ledger keys
def sc_ledger_survivor(ctx, v):
    return _import_plain(ctx, _ledger_file(ctx, w=v))


def sc_ledger_contributor(ctx, v):
    return _import_plain(ctx, _ledger_file(ctx, l=v))


def sc_ledger_source_id(ctx, v):
    return _import_plain(ctx, _ledger_file(ctx, sid=v))


def sc_ledger_evidence_ref(ctx, v):
    return _import_plain(ctx, _ledger_file(ctx, ev=v))


def id_hex(v):
    return source_identity_digest(ORIGIN, v)


def ev_hex(v):
    return evidence_ref_digest(ORIGIN, v)


# ---- row 25: the import quarantine decision (a standing revocation in the destination makes it run)
def _src_export(ctx, uid="u", *, edge_fields=None, prov_fields=None, acts=False, name="src"):
    """A real export of `uid` from a source Memory holding one seeded edge (and, with acts, a confirmation of it);
    then the edge line's fields / provenance fields are overwritten."""
    src = inv._mem(ctx.tmp, name)
    e = inv._seed_edge(src, uid)
    if acts == "replies":                    # a challenge and the resolve that names it (target_uid)
        ch = src.reply(uid, e.id, kind="challenge", text="that is not right")
        src.reply(uid, e.id, kind="resolve", target=ch["reply_id"])
    elif acts:
        src.confirm(uid, e.id)
    p = ctx.tmp / f"{name}.jsonl"
    src.export_memory(uid, str(p))
    src.close()

    def fix(r):
        if r.get("record") == "edge":
            r.update(edge_fields or {})
            r["provenance"].update(prov_fields or {})
        return r
    return _edit_lines(p, fix), e.id


def _revoked_dest(ctx):
    ctx.mem = inv._mem(ctx.tmp, "dest")
    ctx.mem.revoke_source("u", None, "some-other-source", "policy")        # any standing revocation for "u"
    return ctx.mem


def sc_quarantine_origin(ctx, v):
    path, _ = _src_export(ctx, prov_fields={"origin": v})
    m = _revoked_dest(ctx)
    with ctx.tap:
        return m.import_memory(str(path))


def sc_quarantine_source_id(ctx, v):
    path, _ = _src_export(ctx, prov_fields={"source_id": v})
    m = _revoked_dest(ctx)
    with ctx.tap:
        return m.import_memory(str(path))


# ---- row 23: the converting import's whole-file digest
def _arity_file(ctx, note):
    """A format-14 file with NO arity_plan record (an undecided source) carrying a candidate: p retired `superseded`
    under `measures` (reclassified, multi in the default registry) and its successor n; n's note carries `note`."""
    def e(eid, obj, *, at=None, reason=None, supersedes=None, note=""):
        return {"record": "edge", "id": eid, "user_id": "u", "subject": "user", "relation": "measures",
                "object": obj, "note": note, "valid_from": NOW.isoformat(),
                "invalidated_at": at, "invalidation_reason": reason, "supersedes": supersedes,
                "provenance": {"author_of_evidence": "user", "evidence_ref": f"ev-{eid}", "source_id": None,
                               "origin": "org-y", "observed_at": NOW.isoformat(), "confidence": 0.9}}
    recs = [e("p-1", "weight 78", at=datetime(2050, 1, 1, tzinfo=timezone.utc).isoformat(), reason="superseded"),
            e("n-1", "weight 80", supersedes="p-1", note=note)]
    return _write_lines(ctx.tmp / "arity.jsonl", {"kind": "veracium-export", "version": 14, "user_id": "u"}, recs)


def _planned_dest(ctx):
    ctx.mem = inv._mem(ctx.tmp, "dest")
    r = DM.run_data_migration(ctx.db, host_attestation=T6.ATT, registry=ctx.mem.config.relations
                              if ctx.mem.config.relations is not None else T6._reg(), op_id="op-plan",
                              plan_only=True)
    assert r.outcome in ("planned", "already-planned", "complete"), (r.outcome, r.diagnostic)
    return ctx.mem


def sc_whole_file_converting(ctx, v):
    path = _arity_file(ctx, note=f"weighed at the clinic {v}")
    m = _planned_dest(ctx)
    with ctx.tap:
        return m.import_memory(str(path))


def sc_whole_file_plain(ctx, v):
    """Non-converting control route: the same digest runs on every import; nothing persists it."""
    path, _ = _src_export(ctx, edge_fields={"note": f"weighed at the clinic {v}"})
    ctx.mem = inv._mem(ctx.tmp, "dest")
    with ctx.tap:
        return ctx.mem.import_memory(str(path))


# ---- rows 18 / 19: the arity migration and undo
def _legacy_restored(ctx, p_id="p-u", *, run=True):
    """A real upgraded (v15 -> head) store holding `p_id` retired `superseded` under `measures` and its successor;
    with run=True the data migration has restored it. Returns the db path."""
    edges = [T6._edge(p_id, "weight 78", user="u", at=T6.PRE_2050, reason="superseded"),
             T6._edge("n-u", "weight 80", user="u", day=2, supersedes=p_id)]
    path = T6._store(ctx.tmp, edges, name="legacy.db")
    if run:
        r = T6._run(path)
        assert r.outcome == "migrated", (r.outcome, r.diagnostic)
    return path


def _mem_at(path):
    return Memory(llm=inv.Stub(), config=MemoryConfig(db_path=path, wiki_recompile_after_writes=0))


def sc_migration_edge_id(ctx, v):
    path = _legacy_restored(ctx, v, run=False)
    with ctx.tap:
        r = T6._run(path)
    ctx.mem = _mem_at(path)
    return {"outcome": r.outcome, "committed": list(r.committed), "plan_id": r.plan_id}


def sc_migration_edge_id_via_import(ctx, v):
    """convert_rows' other caller: a converting import whose candidate edge id is `v` (from the file: screened)."""
    path = _edit_lines(_arity_file(ctx, note=""), lambda r: _rename_arity(r, "p-1", v))
    m = _planned_dest(ctx)
    with ctx.tap:
        return m.import_memory(str(path))


def _rename_arity(r, old, new):
    if r.get("id") == old:
        r["id"] = new
    if r.get("supersedes") == old:
        r["supersedes"] = new
    return r


def sc_undo_edge_id(ctx, v):
    path = _legacy_restored(ctx, v)
    ctx.mem = _mem_at(path)
    with ctx.tap:
        return ctx.mem.undo_restoration("u", v, correlation_id="undo-1")


def sc_undo_plan_id_legacy(ctx, v):
    """A legacy migration_outcome.plan_id (planted, as a pre-0055 store that restored an outcome under a
    file-supplied plan id would hold it), then undo."""
    path = _legacy_restored(ctx)
    con = sqlite3.connect(path)
    con.execute("UPDATE migration_outcome SET plan_id=? WHERE edge_id='p-u'", (v,))
    con.commit()
    con.close()
    ctx.mem = _mem_at(path)
    with ctx.tap:
        return ctx.mem.undo_restoration("u", "p-u", correlation_id="undo-1")


def sc_undo_plan_id_via_restore(ctx, v):
    """The realistic file route: a source's restored outcome exported, its plan_id edited, RESTORED (restore=True:
    origin local -> restored, a PROOF origin) into a fresh store, then undone there."""
    path = _legacy_restored(ctx)
    src = _mem_at(path)
    exp = ctx.tmp / "restored.jsonl"
    src.export_memory("u", str(exp))
    src.close()
    _edit_lines(exp, lambda r: dict(r, plan_id=v) if r.get("record") == "arity_outcome" else r)
    ctx.mem = inv._mem(ctx.tmp, "dest")
    ctx.mem.import_memory(str(exp), restore=True)            # outside the tap: setup
    with ctx.tap:
        return ctx.mem.undo_restoration("u", "p-u", correlation_id="undo-1")


# ---- row 20: outcome uid under a cross-user remap
def sc_remap_outcome_uid(ctx, v):
    edges = [T6._edge("p-w", "weight 78", user="w", at=T6.PRE_2050, reason="superseded"),
             T6._edge("n-w", "weight 80", user="w", day=2, supersedes="p-w")]
    path = T6._store(ctx.tmp, edges, name="srcw.db")
    assert T6._run(path).outcome == "migrated"
    src = _mem_at(path)
    exp = ctx.tmp / "w.jsonl"
    src.export_memory("w", str(exp))
    src.close()
    _edit_lines(exp, lambda r: dict(r, outcome_uid=v) if r.get("record") == "arity_outcome" else r)
    ctx.mem = inv._mem(ctx.tmp, "dest")
    with ctx.tap:
        return ctx.mem.import_memory(str(exp), user_id="u")


# ---- rows 21 / 22: act uids
def _act_file(ctx, uid, idx, v):
    path, _ = _src_export(ctx, uid, acts=True)

    def fix(r):
        if r.get("record") == "confirmation":
            au = list(r["act_uid"])
            au[idx] = v
            r["act_uid"] = au
        return r
    return _edit_lines(path, fix)


def sc_remap_act_origin(ctx, v):
    path = _act_file(ctx, "w", 0, v)
    ctx.mem = inv._mem(ctx.tmp, "dest")
    with ctx.tap:
        return ctx.mem.import_memory(str(path), user_id="u")


def _act_plain(idx):
    def sc(ctx, v):
        path = _act_file(ctx, "u", idx, v)
        ctx.mem = inv._mem(ctx.tmp, "dest")
        with ctx.tap:
            return ctx.mem.import_memory(str(path))
    sc.__name__ = f"sc_act_uid{idx}_plain"
    return sc


sc_act_uid0, sc_act_uid1, sc_act_uid2 = _act_plain(0), _act_plain(1), _act_plain(2)


def sc_act_uid_restore(idx):
    def sc(ctx, v):
        path = _act_file(ctx, "u", idx, v)
        ctx.mem = inv._mem(ctx.tmp, "dest")
        with ctx.tap:
            return ctx.mem.import_memory(str(path), restore=True)
    sc.__name__ = f"sc_act_uid{idx}_restore"
    return sc


# ------------------------------------------------------------------------------------------------------- the rows
ROWS_C = [
    # row, component, site, scenario, control value, control needle, shaped value, shaped needle, precondition
    (12, comp(12, 0), SITE_12, sc_ledger_survivor, f"w-{C}", C, f"w-{GH}", GH,
     "plain same-user import of a v7 file: W absorbs L (structured absorbed_by_id); W's id seeded"),
    (12, comp(12, 1), SITE_12, sc_ledger_contributor, f"l-{C}", C, f"l-{GH}", GH,
     "plain same-user import of a v7 file: L (absorbed_duplicate) id seeded"),
    (24, comp(24, 0), SITE_24, sc_ledger_survivor, f"w-{C}", C, f"w-{GH}", GH,
     "as row 12; plan_row_id frames survivor_id raw"),
    (24, comp(24, 1), SITE_24, sc_ledger_source_id, f"agent-{C}", id_hex(f"agent-{C}"), f"agent-{GH}",
     id_hex(f"agent-{GH}"),
     "L's provenance.source_id seeded (origin fixed 'org-x'); needle = source_identity_digest(origin, value) hex, "
     "the value plan_row_id frames"),
    (24, comp(24, 2), SITE_24, sc_ledger_evidence_ref, f"ev-{C}", ev_hex(f"ev-{C}"), f"ev-{GH}",
     ev_hex(f"ev-{GH}"),
     "L's provenance.evidence_ref seeded; needle = evidence_ref_digest(origin, value) hex"),
    (24, comp(24, 3), SITE_24, sc_ledger_contributor, f"l-{C}", C, f"l-{GH}", GH, "as row 12 contributor"),
    (25, comp(25, 0), SITE_25, sc_quarantine_origin, f"org-{C}", C, f"org-{GH}", GH,
     "destination holds a standing revocation for 'u' (else the decision is skipped); plain import, file edge's "
     "provenance.origin seeded"),
    (25, comp(25, 1), SITE_25, sc_quarantine_source_id, f"agent-{C}", C, f"agent-{GH}", GH,
     "as above; provenance.source_id seeded"),
    (18, comp(18, 0), SITE_18, sc_migration_edge_id, f"p-{C}", C, f"p-{GH}", GH,
     "legacy v15 store upgraded to head; the retired edge's id seeded; run_data_migration restores it"),
    (19, comp(19, 0), SITE_19, sc_undo_edge_id, f"p-{C}", C, f"p-{GH}", GH,
     "legacy store, restored by the migration; the restored edge's id seeded; Memory.undo_restoration"),
    (19, comp(19, 1), SITE_19, sc_undo_plan_id_legacy, f"pl-{C}", C, f"pl-{GH}", GH,
     "restored legacy store; migration_outcome.plan_id planted (legacy); Memory.undo_restoration"),
    (20, comp(20, 0), SITE_20, sc_remap_outcome_uid, f"ou-{C}", C, f"ou-{GH}", GH,
     "export of user 'w' with a restored outcome; outcome_uid edited; plain import user_id='u' (remap)"),
    (21, comp(21, 0), SITE_21, sc_remap_act_origin, f"st-{C}", C, f"st-{GH}", GH,
     "export of user 'w' with a confirmation; act_uid[0] edited; plain import user_id='u' (remap)"),
    (22, comp(22, 0), SITE_22, sc_act_uid0, f"st-{C}", C, f"st-{GH}", GH,
     "export of 'u' with a confirmation; act_uid[0] edited; plain import into a fresh store (no remap)"),
    (22, comp(22, 1), SITE_22, sc_act_uid1, f"u-{C}", C, f"u-{GH}", GH, "as above; act_uid[1] edited"),
    (22, comp(22, 2), SITE_22, sc_act_uid2, f"c-{C}", C, f"c-{GH}", GH, "as above; act_uid[2] edited"),
    (23, comp(23, 0), SITE_23, sc_whole_file_converting, C, C, GH, GH,
     "converting import: destination plan-only initialized; undecided v14 file with a measures candidate; the "
     "successor's note carries the value (free text: withheld by the screen AFTER the whole-file digest)"),
]


# ---------------------------------------------------------------------------------- extra routes (not ROWS_C cells)
def _reply_file(ctx, uid, idx, v):
    """A challenge + resolve export; act_uid[idx] seeded on the challenge (and, for idx 0/1 — one source store, one
    user — on the resolve too), and the resolve's target_uid[idx] kept naming the challenge."""
    path, _ = _src_export(ctx, uid, acts="replies")

    def fix(r):
        if r.get("record") == "reply":
            au = list(r["act_uid"])
            if r["kind"] == "challenge" or idx < 2:
                au[idx] = v
            r["act_uid"] = au
            if r.get("target_uid") is not None:
                tu = list(r["target_uid"])
                tu[idx] = v
                r["target_uid"] = tu
        return r
    return _edit_lines(path, fix)


def sc_remap_reply_origin(ctx, v):
    path = _reply_file(ctx, "w", 0, v)
    ctx.mem = inv._mem(ctx.tmp, "dest")
    with ctx.tap:
        return ctx.mem.import_memory(str(path), user_id="u")


def _reply_plain(idx):
    def sc(ctx, v):
        path = _reply_file(ctx, "u", idx, v)
        ctx.mem = inv._mem(ctx.tmp, "dest")
        with ctx.tap:
            return ctx.mem.import_memory(str(path))
    sc.__name__ = f"sc_reply_uid{idx}_plain"
    return sc


def sc_act_uid0_restore(ctx, v):
    path = _act_file(ctx, "u", 0, v)
    ctx.mem = inv._mem(ctx.tmp, "dest")
    with ctx.tap:
        return ctx.mem.import_memory(str(path), restore=True)


def sc_ledger_survivor_restore(ctx, v):
    return _import_plain(ctx, _ledger_file(ctx, w=v), restore=True)


def _ledger_remap(ctx, **kw):
    path = _edit_lines(_ledger_file(ctx, **kw),
                       lambda r: dict(r, user_id="w") if r.get("kind") == "veracium-export" or "id" in r else r)
    return _import_plain(ctx, path, user_id="u")


def sc_ledger_survivor_remap(ctx, v):
    return _ledger_remap(ctx, w=v)


def sc_ledger_source_id_remap(ctx, v):
    return _ledger_remap(ctx, sid=v)


def _quarantine_episode(field):
    def sc(ctx, v):
        src = inv._mem(ctx.tmp, "src")
        src.remember("u", "I live in Denver", context=inv.EvidenceContext.direct(), source_id="chat")
        p = ctx.tmp / "src.jsonl"
        src.export_memory("u", str(p))
        src.close()

        def fix(r):
            if r.get("record") == "episode" and (r.get("provenance") or {}).get("source_id") is not None:
                r["provenance"][field] = v
            return r
        _edit_lines(p, fix)
        m = _revoked_dest(ctx)
        with ctx.tap:
            return m.import_memory(str(p))
    sc.__name__ = f"sc_quarantine_episode_{field}"
    return sc


# EXTRA_C: (row, component, site, scenario, cv, cn, sv, sn, expected, note). `expected` states what the route shows
# when it differs from the ROWS_C reading (a control that is NOT meant to carry, a whole-file refusal).
EXTRA_C = [
    (23, comp(23, 0), SITE_23, sc_whole_file_plain, C, C, GH, GH, "carry, found [] (nothing persists it)",
     "non-converting plain import of a real export; edge note carries the value"),
    (19, comp(19, 1), SITE_19, sc_undo_plan_id_via_restore, f"pl-{C}", C, f"pl-{GH}", GH,
     "carry / CredentialImportRefused whole at the SETUP restore (undo never runs)",
     "file route: a restored outcome's plan_id edited in an export, restore=True into a fresh store, then undo"),
    (18, comp(18, 0), SITE_18, sc_migration_edge_id_via_import, f"p-{C}", C, f"p-{GH}", GH,
     "carry / refused per record (screened at import, not identifier_kept)",
     "convert_rows' second caller: converting import (destination plan-only initialized, undecided file); the "
     "candidate's file id seeded"),
    (21, comp(21, 0), SITE_21, sc_remap_reply_origin, f"st-{C}", C, f"st-{GH}", GH, "carry / refused per record",
     "replies (challenge + resolve) under remap: act_uid[0] AND target_uid[0] both pass _remap_namespace"),
    (22, comp(22, 0), SITE_22, _reply_plain(0), f"st-{C}", C, f"st-{GH}", GH, "carry / refused per record",
     "replies, no remap, act_uid[0] (+ target_uid[0])"),
    (22, comp(22, 1), SITE_22, _reply_plain(1), f"u-{C}", C, f"u-{GH}", GH, "carry / refused per record",
     "replies, no remap, act_uid[1] (+ target_uid[1])"),
    (22, comp(22, 2), SITE_22, _reply_plain(2), f"r-{C}", C, f"r-{GH}", GH, "carry / refused per record",
     "replies, no remap, the challenge's act_uid[2] (+ the resolve's target_uid[2])"),
    (22, comp(22, 0), SITE_22, sc_act_uid0_restore, f"st-{C}", C, f"st-{GH}", GH,
     "carry / CredentialImportRefused whole", "restore=True route of row 22 uid[0]"),
    (12, comp(12, 0), SITE_12, sc_ledger_survivor_restore, f"w-{C}", C, f"w-{GH}", GH,
     "carry / CredentialImportRefused whole", "restore=True route of the ledger file"),
    (12, comp(12, 0), SITE_12, sc_ledger_survivor_remap, f"w-{C}", C, f"w-{GH}", GH,
     "control does NOT carry (minted imp-e-...) / refused per record",
     "cross-user remap: survivor_id is the minted id, not the file's"),
    (24, comp(24, 1), SITE_24, sc_ledger_source_id_remap, f"agent-{C}", id_hex(f"agent-{C}"), f"agent-{GH}",
     id_hex(f"agent-{GH}"), "carry / refused per record", "cross-user remap: the identity digest is not remapped"),
    (25, comp(25, 0), SITE_25, _quarantine_episode("origin"), f"org-{C}", C, f"org-{GH}", GH,
     "carry, found [] / refused per record", "the quarantine loop's episode records: episode provenance.origin"),
    (25, comp(25, 1), SITE_25, _quarantine_episode("source_id"), f"agent-{C}", C, f"agent-{GH}", GH,
     "carry, found [] / refused per record", "episode provenance.source_id"),
]
