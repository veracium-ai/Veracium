"""specs/0055 round 5: closure of R5-01..R5-06 and B, at the width of each finding's CLASS (research's stage-1 read,
additions 1-5). Each inventory row asserts the state it reached, with a positive control that the target operation
happened, so a row cannot pass by never reaching its branch (R5-03 got through round 5 because the all-tools check
fed `e-missing` and never reached a success).

The reviewer's own regressions are not copied here: they ship as the round-5 results' `test_round5_obligations.py`.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sqlite3
import sys
from enum import Enum

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


T = _load("r5c_invariants", "tests/test_0055_invariants.py")
R4 = _load("r5c_r4_closure", "tests/test_0055_r4_closure.py")

from veracium import Memory, MemoryConfig                       # noqa: E402
from veracium import credentials as C                           # noqa: E402
from veracium.portability import CredentialImportRefused        # noqa: E402

TOKEN = R4.TOKEN


def _shaped_enum(data: str):
    """A standard string-mixin enum member: its DATA is `data` (ordinary), its NAME is the token. It is a `str`, a
    scan of its data finds nothing, and an f-string prints its name (the reviewer's R5-06 construction)."""
    return Enum("Shaped", {TOKEN: data}, type=str)[TOKEN]


class _Shown(str):
    """A PLAIN `str` subclass, not an Enum: its data is ordinary and every formatting of it (`format`, `str`, `repr`)
    shows the token. §4b's class is an accepted `str` subclass, so the inventory drives this form beside the Enum one
    (research's stage 2 of round 5, S2-3: an `exact` that converted Enum members only passed every Enum cell)."""

    def __format__(self, spec):
        return TOKEN

    def __str__(self):
        return TOKEN

    def __repr__(self):
        return TOKEN


#: The accepted subclass forms each R5-06 cell drives, beside the ordinary data.
SUBCLASS_FORMS = {"enum": _shaped_enum, "plain": _Shown}


# ==== R5-06: every A5 row, driven with an accepted str subclass ======================================================

def _ordinary(param, base):
    return base if isinstance(base, str) and base else f"ordinary-{param}"


def _run_form(tmp_path, method, param, form):
    stub = T.Stub()
    sub = tmp_path / form
    sub.mkdir()
    mem = Memory(llm=stub, config=MemoryConfig(db_path=str(sub / "m.db"), wiki_recompile_after_writes=0))
    try:
        e = T._seed_edge(mem)
        if method == "unrevoke_source":
            from veracium.redaction import SOURCE_REVOCATION_REASONS
            mem.revoke_source("u", None, "chat", SOURCE_REVOCATION_REASONS[0])
        stub.prompts.clear()

        def value(base):
            data = _ordinary(param, base)
            return data if form == "data" else SUBCLASS_FORMS[form](data)
        result, exc = None, None
        try:
            result = R4._call(mem, sub, e, method, param, value)
        except Exception as ex:                                    # noqa: BLE001 - the outcome is recorded
            exc = ex
        shown = json.dumps(result, default=lambda x: x.model_dump(mode="json") if hasattr(x, "model_dump") else repr(x))
        return {"exc": exc, "leak": R4._leaks(str(sub / "m.db"), stub) | ({"result"} if TOKEN in shown else set())}
    finally:
        mem.close()


#: The screened rows whose ordinary value cannot reach success on a fresh store: `reply`'s target must name an existing
#: reply, and `undo_restoration` needs an edge the 0044 migration restored. Both still run both forms.
NO_SUCCESS_ON_A_FRESH_STORE = {("reply", "target"), ("undo_restoration", "correlation_id")}


@pytest.mark.parametrize("method,param", R4._a5_rows(), ids=[f"{m}.{p}" for m, p in R4._a5_rows()])
def test_r5_06_an_accepted_str_subclass_reaches_what_its_data_reaches(tmp_path, method, param):
    """Every A5 row, screened or not, driven with ordinary data and with each accepted subclass form holding the same
    data (SUBCLASS_FORMS: a str-Enum member under a shaped NAME, and a plain `str` subclass that formats as the token).
    Each form must end exactly as its data does (the same success, or the same exception class), and its shown text
    must reach no storage, provider prompt, result or exception text. A screened row's ordinary form must
    SUCCEED (the reachability control: the branch R5-06 lived on is a success branch), but for the two rows that
    cannot on a fresh store. RED against: round 5's R5-06 (`remember`'s fallback summary stored `event_type`'s name)
    and its unscreened siblings measured at the fix (`confirm`/`dispute` wrote an `edge_id`'s name into the record,
    `correct` derived `evidence_ref` from it, `answer` put a query's name in the gate's prompt). A parameter added
    later that formats its name fails here: this inventory is the guard, read by A5's rule from the signatures."""
    d = _run_form(tmp_path, method, param, "data")
    for form in SUBCLASS_FORMS:
        m = _run_form(tmp_path, method, param, form)
        assert type(m["exc"]) is type(d["exc"]), (method, param, form, repr(d["exc"]), repr(m["exc"]))
        assert not m["leak"], (method, param, form, m["leak"])
        if m["exc"] is not None:
            # the outward formatter (served, CLI, log) never carries it, on any row; a SCREENED row's library exception
            # does not either. An unscreened row's library exception may quote the caller's own argument (its repr):
            # E1's library scope, as the A5 census already records for the str form.
            assert TOKEN not in C.outward_text(m["exc"]), (method, param, form)
            if R4._screened_by(method, param) is not None:
                assert TOKEN not in str(m["exc"]), (method, param, form)
    if R4._screened_by(method, param) is not None and (method, param) not in NO_SUCCESS_ON_A_FRESH_STORE:
        assert d["exc"] is None, (method, param, repr(d["exc"]))


def test_r5_06_exact_returns_the_data_as_a_builtin_str():
    for make in SUBCLASS_FORMS.values():
        m = make("chat")
        assert f"{m}" != "chat" and str.__str__(m) == "chat"                  # the hazard, then its remedy
        out = C.exact(m)
        assert type(out) is str and out == "chat" and f"{out}" == "chat"
    assert C.exact("chat") == "chat" and C.exact(None) is None and C.exact(b"x") == b"x"


# ==== R5-01: every dict-typed field of the stored models, at admission and in the store guard =========================

def _dict_fields():
    """Every field of a stored record model whose annotation reaches `dict` (research's addition 4: not only
    `outcome_counts`), walked from the schema, never listed by hand."""
    import typing
    from pydantic import BaseModel
    from veracium import schema as S
    out = []
    for cls in (S.Edge, S.Episode):
        for name in typing.get_type_hints(cls):
            if name not in cls.model_fields:
                continue
            stack, seen = [typing.get_type_hints(cls)[name]], False
            while stack:
                t = stack.pop()
                if t is dict or typing.get_origin(t) is dict:
                    seen = True
                stack.extend(typing.get_args(t))
            if seen:
                out.append((cls.__name__, name))
    return out


def test_r5_01_the_dict_field_census_is_not_empty():
    fields = _dict_fields()
    assert ("Edge", "outcome_counts") in fields, fields


@pytest.mark.parametrize("model,field", _dict_fields())
@pytest.mark.parametrize("mode", ["plain", "restore", "restore_withhold"])
def test_r5_01_a_shaped_key_in_every_dict_field_is_refused_at_import(tmp_path, model, field, mode):
    """Each dict field, in each import mode: a shaped key refuses its record (a restore refuses whole), and an ordinary
    key in the same position imports (the positive control). Never renamed."""
    kind = "edge" if model == "Edge" else "episode"
    for key, expect_refused in ((TOKEN, True), ("ordinary_key", False)):
        sub = tmp_path / f"{mode}-{expect_refused}"
        sub.mkdir()
        path, _eid = T._export_with(sub)
        docs = [json.loads(line) for line in path.read_text().splitlines()]
        hit = 0
        for doc in docs:
            if doc.get("kind") == kind or (kind == "edge" and "relation" in doc and "subject" in doc):
                doc[field] = {key: 1}
                hit += 1
        assert hit, (model, field, "no record of that kind in the export")
        path.write_text("".join(json.dumps(d) + "\n" for d in docs))
        dest = T._mem(sub, "dest")
        try:
            kw = {} if mode == "plain" else {"restore": True, **({"withhold_credentials": True}
                                                              if mode == "restore_withhold" else {})}
            refused = False
            try:
                rep = dest.import_memory(str(path), **kw)
                refused = bool(rep.get("credential_refused_records")) if isinstance(rep, dict) else False
            except CredentialImportRefused:
                refused = True
            stored = T._dump(str(sub / "dest.db")) if (sub / "dest.db").exists() else ""
        finally:
            dest.close()
        assert refused is expect_refused, (model, field, mode, key)
        assert TOKEN not in stored
        if not expect_refused:
            assert "ordinary_key" in stored, (model, field, mode, "the ordinary key never reached the store")


def test_r5_01_the_store_guard_reads_new_keys_and_passes_unchanged_ones():
    """The guard's rule directly: a new shaped key is introduced (refused), the same key unchanged from the prior is
    not (a legacy key passes a transition), and an ordinary new key is not."""
    from veracium.store.sqlite import _cred_introduced
    assert _cred_introduced({"outcome_counts": {TOKEN: 1}}, {"outcome_counts": {}}) == ("outcome_counts.[key]",
                                                                                     C.first_class(TOKEN))
    assert _cred_introduced({"outcome_counts": {TOKEN: 2}}, {"outcome_counts": {TOKEN: 1}}) is None
    assert _cred_introduced({"outcome_counts": {"ordinary": 1}}, None) is None
    assert _cred_introduced({TOKEN: "x"}, None) == ("[key]", C.first_class(TOKEN))


# ==== R5-02: every path label is built from declared names =========================================================

@pytest.mark.parametrize("key", [TOKEN, "not_a_declared_name", "x" * 40, "relation"])
def test_r5_02_a_label_prints_a_declared_name_or_key(key):
    """The one segment rule both carriers use: a declared field name prints, anything else is `[key]`. `relation` is
    declared, so it prints (a fixed vocabulary is not input)."""
    seg = C.path_segment(key)
    assert seg == (key if key == "relation" else "[key]")
    from veracium.store.sqlite import _cred_introduced
    hit = _cred_introduced({key: {"inner": TOKEN}}, None)
    # a shaped key is itself the hit, at its parent's `[key]`; otherwise the value is, under the key's segment
    assert hit is not None and TOKEN not in hit[0], hit
    assert C.path_segment("inner") == "[key]"                              # `inner` is not a declared name either
    assert hit[0] == ("[key]" if C.first_class(key) else f"{seg}.[key]"), hit


def test_r5_02_an_import_refusal_and_its_audit_carry_no_input_key(tmp_path):
    """An unknown field whose NAME and value are shaped: the record is refused (reached), and neither the report nor
    the AuditLog carries the key."""
    from veracium.audit import AuditLog
    path, _eid = T._export_with(tmp_path)
    docs = [json.loads(line) for line in path.read_text().splitlines()]
    for d in docs:
        if "relation" in d and "subject" in d:
            d[TOKEN] = TOKEN
    path.write_text("".join(json.dumps(d) + "\n" for d in docs))
    log = tmp_path / "audit.jsonl"
    dest = T._mem(tmp_path, "dest", audit=AuditLog(str(log)))
    try:
        rep = dest.import_memory(str(path))
    finally:
        dest.close()
    assert rep["credential_refused_records"], "the record was not refused: the branch was not reached"
    assert TOKEN not in json.dumps(rep, default=str)
    assert log.exists() and "credential_refused" in log.read_text() and TOKEN not in log.read_text()


# ==== R5-03: every served tool's SUCCESS result over a store holding shaped ids and shaped text ========================

def test_r5_03_every_impl_is_served_through_the_projection():
    """By property: every module-level `*_impl` (what build_server's tools and the adapters' Binding call) is decorated
    with `_projected`, identified by its wrapper's code. A tool added later without it fails here."""
    import veracium.mcp_server as M
    impls = {n: f for n, f in vars(M).items() if n.endswith("_impl") and callable(f)}
    assert len(impls) >= 13, sorted(impls)
    bare = [n for n, f in impls.items() if getattr(f, "__code__", None) is None or f.__code__.co_name != "projected"
            or getattr(f, "__wrapped__", None) is None]
    assert not bare, bare


@pytest.mark.parametrize("key", ["confirmed", "disputed", "id", "edge_id", "corrected", "superseded_by"])
def test_r5_03_a_shaped_record_id_is_an_ordinal_and_stored_text_is_masked(key):
    import veracium.mcp_server as M
    out = M.served_result({"ok": True, key: TOKEN, "relation": f"likes {TOKEN}", "nested": [{"note": TOKEN}],
                           TOKEN: 1, "plain": "e-123"})
    shown = json.dumps(out)
    assert TOKEN not in shown
    assert out[key] == f"record 1 of this report ({key})"
    assert out["plain"] == "e-123" and out["ok"] is True                   # ordinary values untouched


def test_r5_03_the_minted_preview_token_is_kept():
    import veracium.mcp_server as M
    token = "tt1.eyJhbGciOiJub25lIn0.abcdefghijklmnopqrstuvwxyz"
    assert C.first_class(token) == "veracium_preview_token"
    out = M.served_result({"ok": True, "preview_token": token}, keep=frozenset({"preview_token"}))
    assert out["preview_token"] == token
    assert M.served_result({"ok": True, "other": token})["other"] != token


def _plant(m, *, shaped_id: bool, shaped_relation: bool) -> str:
    """The reviewer's construction: an ordinary fact whose current row and journal are rewritten coherently, with a
    shaped legacy id and/or shaped stored text in `relation`. Returns the id to act on."""
    edge = T._seed_edge(m)
    con = m.store._conn
    doc = json.loads(con.execute("SELECT json FROM edges WHERE id=?", (edge.id,)).fetchone()[0])
    rid = ("e-" + TOKEN) if shaped_id else edge.id
    doc["id"] = rid
    if shaped_relation:
        doc["relation"] = TOKEN
    con.execute("UPDATE edges SET id=?,relation=?,json=? WHERE id=?", (rid, doc["relation"], json.dumps(doc), edge.id))
    con.execute("UPDATE edge_event SET edge_id=?,state=? WHERE edge_id=?", (rid, json.dumps(doc), edge.id))
    con.commit()
    return rid


#: The cells whose declared outcome is a refusal, not a success: a shaped legacy id or identity cannot be copied into a
#: new record (the store guard on `supersedes`/`evidence_ref`; §4c-ii row 8's identity rule for `correct`). The
#: refusal names the field and class only. Every other cell must reach success.
EXPECT_REFUSED = {("remember", "shaped_id"), ("correct_fact", "shaped_id"), ("correct_fact", "shaped_relation")}


def _token_in(prev) -> str:
    """The preview token from either route's result (the binding's dict, or the MCP content's serialized form)."""
    import re
    m = re.search(r"tt1\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", json.dumps(prev, default=str))
    assert m, prev
    return m.group(0)


def _reached(name, out) -> bool:
    """The positive control per tool: the call reached its success state (not a refusal, and the payload a success
    carries is present)."""
    if isinstance(out, str):
        return bool(out.strip())
    if not isinstance(out, dict) or out.get("ok") is False or "refusal" in out:
        return False
    need = {"confirm_fact": "confirmed", "dispute_fact": "disputed", "correct_fact": "ok", "find_facts": "units",
            "forget_fact": "ok", "forget_everything_preview": "preview_token", "forget_everything_confirm": "ok"}
    return need.get(name, None) is None or need[name] in out


#: one success-reaching call per served tool; `{rid}` is the planted record. forget_everything_confirm takes the
#: preview's token from the same binding.
SWEEP = {
    "remember": {"text": "I drink tea in the morning"},
    "recall": {"query": "Denver"},
    "answer": {"query": "Where do I live?"},
    "maintain": {},
    "record_procedure": {"summary": "I run the tests first", "basis": "stated"},
    "describe_procedures": {"query": None},
    "find_facts": {"query": None},
    "correct_fact": {"edge_id": "{rid}", "corrected_value": "Boulder"},
    "dispute_fact": {"edge_id": "{rid}", "reason": "not true"},
    "confirm_fact": {"edge_id": "{rid}"},
    "forget_fact": {"edge_id": "{rid}"},
    "forget_everything_preview": {},
    "forget_everything_confirm": {"preview_token": "{token}"},
}


def test_r5_03_the_sweep_covers_every_served_tool(tmp_path):
    pytest.importorskip("mcp")                  # Binding builds the served server (the pydantic-floor lane has none)
    from veracium.adapters._surface import Binding
    m = T._mem(tmp_path)
    try:
        names = {t.name for t in Binding(m, user_id="u", capability="direct").tools()}
    finally:
        m.close()
    assert names == set(SWEEP), names ^ set(SWEEP)


@pytest.mark.parametrize("plant", ["shaped_id", "shaped_relation"])
@pytest.mark.parametrize("route", ["binding", "mcp"])
@pytest.mark.parametrize("name", sorted(SWEEP))
def test_r5_03_every_served_success_result_carries_no_shape(tmp_path, name, route, plant):
    """Research's addition 2: every served tool's SUCCESS result, over a store holding a shaped legacy id or shaped
    stored text, through the adapters' Binding and the real FastMCP `call_tool`. Each cell asserts it reached its
    success state; then no shape anywhere in the result. RED against: round 5's R5-03 (confirm/dispute returned the
    legacy id; dispute returned the stored relation)."""
    pytest.importorskip("mcp")                  # both routes build the served server (the pydantic-floor lane has none)
    import asyncio
    from veracium import mcp_server as MCP
    from veracium.adapters._surface import Binding
    m = T._mem(tmp_path)
    try:
        rid = _plant(m, shaped_id=plant == "shaped_id", shaped_relation=plant == "shaped_relation")
        b = Binding(m, user_id="u", capability="direct")
        server = MCP.build_server(m, default_user="u", capability="direct") if route == "mcp" else None

        def call(tool, args):
            if route == "binding":
                return b.call(tool, args)
            res = asyncio.run(server.call_tool(tool, args))
            if isinstance(res, tuple):                   # (content, structured): a str tool's {"result": ...}
                o = res[1].get("result", res[1]) if isinstance(res[1], dict) else res[0]
            else:
                o = res
            if isinstance(o, list) and o and hasattr(o[0], "text"):     # a dict tool: its JSON as TextContent
                try:
                    o = json.loads(o[0].text)
                except ValueError:
                    o = o[0].text
            return o
        token = ""
        if name == "forget_everything_confirm":          # the token from THIS route's own preview (its issuer)
            prev = call("forget_everything_preview", {})
            token = _token_in(prev)
        args = {k: (v.format(rid=rid, token=token) if isinstance(v, str) else v) for k, v in SWEEP[name].items()}
        out = call(name, args)
        shown = json.dumps(out, default=str)
        assert TOKEN not in shown, (name, route, plant, shown[:300])
        if (name, plant) in EXPECT_REFUSED:
            assert isinstance(out, dict) and out.get("refusal") == "credential_refused" and out.get("class"), \
                (name, route, plant, out)
        else:
            assert isinstance(out, (dict, str)), (name, route, type(out))   # both routes yield the tool's own value
            assert _reached(name, out), (name, route, plant, shown[:300])
    finally:
        m.close()


# ==== R5-04: multi-line grammars at every cut ==========================================================================

CHAINS = [
    ("aws\nsecret\naccess\nkey\nis\nnow\n", "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY"),
    ("access\nkey\nid\nis\nnow\n", "S3cr3t-Passw0rd-Value"),
    ("my\npin\ncode\nis\nnow\n", "8264"),
    ("Authorization\n:\nBearer\n", "abcdefghijklmnopqrstuvwxyz0123456789"),
    ("password\n=\n", '"quoted value 1234"'),
]


class _SeekRecorder:
    """The file object `log_tail` opens, with every `seek` recorded (its window's start is the first absolute seek
    after the seek to the end)."""
    def __init__(self, fh, seeks):
        self._fh, self._seeks = fh, seeks

    def seek(self, offset, whence=0):
        self._seeks.append((offset, whence))
        return self._fh.seek(offset, whence)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return self._fh.__exit__(*exc)

    def __getattr__(self, name):
        return getattr(self._fh, name)


def product_cut(call, log: pathlib.Path):
    """Run `call` with `log`'s file object recorded; return its result and the byte offset the product's window
    started at (research's stage 2, S2-D: the witness is read from the product, never recomputed beside it)."""
    seeks = []
    real_open = pathlib.Path.open
    target = log.resolve()

    def opened(self, *args, **kwargs):
        fh = real_open(self, *args, **kwargs)
        return _SeekRecorder(fh, seeks) if self.resolve() == target else fh
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(pathlib.Path, "open", opened)
        result = call()
    ends = [i for i, (off, whence) in enumerate(seeks) if whence == 2]
    assert ends, seeks                                                      # reached: the product opened this file
    absolute = [off for off, whence in seeks[ends[0] + 1:] if whence == 0]
    assert absolute, seeks
    return result, absolute[0]


def chain_cut_witnesses(chain: str, value: str, *, cap: int = 1024):
    """Round 6's R6-02A: the byte-placed files for the every-cut test, each with its WITNESS: where the window's real
    cut falls (`log_tail`'s `size - max(4 * cap, 1 << 20)`), where the chain is, and which chain line the cut opens.
    The chain's last line is followed by a run of blank lines a window long, then the value and twenty ordinary lines,
    so the value lies in the sent tail and the real cut lands at the START of each chain line in turn, then at the
    start of the value's line. (Up to round 6 the filler came BEFORE the chain, so every cut fell in the filler and the
    chain was always whole inside the window.) Blank lines do not count toward CHAIN_LINES on the recogniser's view
    (research's S2-2), so the value stays inside the context the window's start keeps."""
    window = max(4 * cap, 1 << 20)
    lead = "ordinary prefix\n"
    after = "".join(f"ordinary line {i}\n" for i in range(20))
    starts = [0] + [i + 1 for i, c in enumerate(chain) if c == "\n"]
    out = []
    for k, offset in enumerate(starts):
        target = len(lead.encode()) + offset
        bare = (lead + chain + value + "\n" + after).encode()
        padding = window + target - len(bare)
        if offset < len(chain):
            text = lead + chain + "\n" * padding + value + "\n" + after
        else:
            text = lead + chain + value + "\n" + "\n" * padding + after
        raw = text.encode()
        cut = len(raw) - window
        start = raw.index(chain.encode())
        out.append({"line": k, "cut": cut, "chain_start": start, "chain_end": start + len(chain.encode()),
                    "line_start": start + offset, "file_bytes": len(raw), "text": text,
                    "value_in_sent_region": value.strip('"') in raw[-cap:].decode()})
    return out


@pytest.mark.parametrize("chain,value", CHAINS, ids=[c.split()[0] for c, _ in CHAINS])
def test_r5_04_a_line_spanning_match_is_withheld_at_every_cut(tmp_path, chain, value):
    """Each white-space-joined grammar split one part per line, the window's REAL cut placed at the start of EVERY
    line of the chain in turn (`chain_cut_witnesses`, round 6's R6-02A). Each position asserts its geometry first (the
    cut's byte offset is that line's start, inside the chain, and the value lies in the sent region, so a failure to
    withhold would show), then the outcome: the sent tail never carries the value, and keeps the ordinary final line.
    Whole-input masking withholds the value (the precondition). The chain's part count stays below CHAIN_LINES."""
    from veracium.diagnostics import DiagnosticsConfig, Reporter
    assert value.strip('"') not in C.mask_text(chain + value + "\n"), "the grammar does not recognise this chain whole"
    assert chain.count("\n") <= C.CHAIN_LINES
    witnesses = chain_cut_witnesses(chain, value)
    assert len(witnesses) == chain.count("\n") + 1
    for w in witnesses:
        if w["cut"] < w["chain_end"]:
            assert w["value_in_sent_region"], w["line"]  # reached: unmasked, the value would be sent
        log = tmp_path / f"d{w['line']}.log"
        log.write_text(w["text"])
        reporter = Reporter(DiagnosticsConfig(log_path=str(log), max_report_bytes=1024, redact=False))
        # research's stage 2, S2-D: the witness is the PRODUCT's cut, the offset log_tail actually seeks its window to
        # (the test's own formula only places the file), asserted before the outcome
        tail, cut = product_cut(reporter.log_tail, log)
        assert cut == w["line_start"] and w["chain_start"] <= cut <= w["chain_end"], (w["line"], cut, w["line_start"])
        assert value.strip('"') not in tail, (w["line"], tail[-200:])
        assert "ordinary line 19" in tail, w["line"]


def test_r5_04_a_pem_block_with_no_end_longer_than_the_window_is_withheld(tmp_path):
    """The block rule runs to the end when there is no END; the window starts inside it. Read-back finds the BEGIN, so
    no body line is sent."""
    from veracium.diagnostics import DiagnosticsConfig, Reporter
    body = "".join("MIIEvQIBADANBgkqhkiG9w0BAQEFAASC" + f"{i:08d}" + "\n" for i in range(40000))
    log = tmp_path / "d.log"
    log.write_text("start\n-----BEGIN PRIVATE KEY-----\n" + body)
    assert len(log.read_bytes()) > (1 << 20)
    tail = Reporter(DiagnosticsConfig(log_path=str(log), max_report_bytes=1024, redact=False)).log_tail()
    assert "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC" not in tail, tail[-200:]


@pytest.mark.parametrize("chunk", [7, 64, 1 << 20])
def test_r5_04_pem_state_read_back_is_exact_across_chunk_edges(chunk):
    data = ("a\n-----BEGIN RSA PRIVATE KEY-----\nbody\n-----END RSA PRIVATE KEY-----\nb\n"
            "-----BEGIN PRIVATE KEY-----\nbody2\n").encode()

    def rb(lo, hi):
        return data[lo:hi]
    end1 = data.index(b"-----END RSA")
    assert C.pem_open_before(rb, data.index(b"body\n"), chunk) is True
    assert C.pem_open_before(rb, data.index(b"\nb\n") + 1, chunk) is False
    assert C.pem_open_before(rb, data.index(b"body2"), chunk) is True
    assert C.pem_open_before(rb, 2, chunk) is False
    assert end1 > 0


def test_r5_04_mask_from_omits_a_span_that_crosses_the_cut():
    text = "password: hunter2-very-secret\nnext line\n"
    cut = text.index("hunter2") + 3
    out = C.mask_from(text, cut)
    assert "ter2" not in out and out.startswith("\nnext line") or out.startswith("next")


# ---- research's stage 2 of round 5 (2026-11-27), S2-1 and S2-2: the window's state at its edges ------------------------

PEM_BEGIN_LINE = "-----BEGIN PRIVATE KEY-----\n"
PEM_END_LINE = "-----END PRIVATE KEY-----\n"
PEM_BODY = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC"


@pytest.mark.parametrize("k", [-1] + list(range(len(PEM_BEGIN_LINE) + 1)))
def test_s2_1_a_window_starting_anywhere_in_a_begin_line_withholds_the_body(tmp_path, k):
    """S2-1: the window starts `k` bytes into a PEM BEGIN line (-1: on the newline before it; 1..26: inside the marker,
    which neither the look-back nor the head line then holds whole; 27: after the marker; 28: the next line). The body
    is longer than the window's sent part and the block has an END, so ordinary lines follow it. The body must never
    be sent, and the lines after the END must be (the positive control: the state was judged, not refused, and the
    block was closed where it closes). RED at b85f67a7 for k in 1..26: the state was read before the cut."""
    from veracium.diagnostics import DiagnosticsConfig, Reporter
    window = 1 << 20
    head = "start\n"
    after = "".join(f"ordinary line {i}\n" for i in range(C.CHAIN_LINES + 4)) + "ordinary final line\n"
    assert PEM_BODY not in C.mask_text(head + PEM_BEGIN_LINE + f"{PEM_BODY}00000000\n" * 2 + PEM_END_LINE + after), \
        "the block rule does not withhold this body whole: not a test of the cut"
    need = window + k - len(PEM_BEGIN_LINE) - len(PEM_END_LINE) - len(after)      # body bytes that put the start at k

    def line(i):
        return f"{PEM_BODY}{i:08d}\n"                                              # 41 bytes
    n, r = divmod(need, 41)
    body = "".join(line(i) for i in range(n - 1)) + line(n - 1)[:-1] + "Q" * r + "\n"
    text = head + PEM_BEGIN_LINE + body + PEM_END_LINE + after
    raw = text.encode()
    start = len(raw) - window
    assert raw[len(head):len(head) + len(PEM_BEGIN_LINE)] == PEM_BEGIN_LINE.encode() and start == len(head) + k, \
        "the window does not start where this cell says"
    log = tmp_path / "d.log"
    log.write_bytes(raw)
    tail = Reporter(DiagnosticsConfig(log_path=str(log), max_report_bytes=1024, redact=False)).log_tail()
    assert PEM_BODY not in tail, (k, tail[:300])
    assert "ordinary final line" in tail, (k, tail[-300:])


@pytest.mark.parametrize("k", [-1] + list(range(len(PEM_END_LINE) + 1)))
def test_s2_1_a_window_starting_anywhere_in_an_end_line_sends_what_follows(tmp_path, k):
    """S2-1's other marker: the window starts `k` bytes into the END line of a block that began before it. Judged at the
    cut, the look-back saw only the BEGIN, so the block was re-opened and ran to the end of the text: every later line
    was withheld (safe, not honest). Judged at the head line's end, the END is read whole: the body is not in the window
    and the lines after the END are sent."""
    from veracium.diagnostics import DiagnosticsConfig, Reporter
    window = 1 << 20
    head = "start\n" + PEM_BEGIN_LINE + "".join(f"{PEM_BODY}{i:08d}\n" for i in range(4))
    final = "ordinary final line\n"
    need = window + k - len(PEM_END_LINE) - len(final)                             # filler bytes that put the start at k
    n, r = divmod(need, 81)
    filler = ("x" * 80 + "\n") * (n - 1) + "x" * (80 + r) + "\n"
    raw = (head + PEM_END_LINE + filler + final).encode()
    start = len(raw) - window
    assert raw[len(head):len(head) + len(PEM_END_LINE)] == PEM_END_LINE.encode() and start == len(head) + k, \
        "the window does not start where this cell says"
    log = tmp_path / "d.log"
    log.write_bytes(raw)
    tail = Reporter(DiagnosticsConfig(log_path=str(log), max_report_bytes=1024, redact=False)).log_tail()
    assert PEM_BODY not in tail and "ordinary final line" in tail, (k, tail[-300:])


#: A marker the block rule accepts (`(?:[A-Z0-9]+ )*` is unbounded) that is longer than the 4096-byte overlap the
#: read-back used to carry across a chunk edge.
LONG_WORDS = "AB " * 6000


@pytest.mark.parametrize("chunk", [7, 64, 4096, 1 << 20])
def test_s2_1_a_marker_longer_than_any_overlap_is_read_whole_across_chunk_edges(chunk):
    """Dev's find while fixing S2-1 (the same mechanism at the read-back's other boundary): a chunk edge that cuts a
    marker longer than the fixed overlap left it cut in every view, so the block read as closed. Each view now carries
    the previous one's partial first line. RED at b85f67a7 for chunks below the marker's length."""
    begin, end = f"-----BEGIN {LONG_WORDS}PRIVATE KEY-----", f"-----END {LONG_WORDS}PRIVATE KEY-----"
    assert "SECRETBODY" not in C.mask_text(f"{begin}\nSECRETBODY\n{end}\nafter\n"), "the block rule rejects it"
    assert len(begin) > 4096 and len(end) > 4096, "the markers do not exceed the old overlap"
    for text, at, want in [(f"a\n{begin}\nbody\n" + "x" * 80 + "\n", "body\n", True),
                           (f"a\n{begin}\nbody\n{end}\nb\n", "b\n", False),
                           (f"a\n-----BEGIN PRIVATE KEY-----\nbody\n{end}\nb\n", "b\n", False)]:
        data = text.encode()

        def rb(lo, hi):
            return data[lo:hi]
        pos = data.rindex(at.encode())
        assert C.pem_open_before(rb, pos, chunk) is want, (chunk, at, want)


def test_s2_1_a_long_begin_marker_cut_by_the_read_back_chunk_edge_withholds_the_body(tmp_path):
    """The same, end to end: the log window's look-back reads 1 MiB chunks, and a BEGIN marker longer than 4096 bytes
    straddles the first chunk edge with more than 4096 of its bytes after it. The body before the END must be withheld
    and the lines after it sent."""
    from veracium.diagnostics import DiagnosticsConfig, Reporter
    window = chunk = 1 << 20
    begin = f"-----BEGIN {LONG_WORDS}PRIVATE KEY-----\n"
    after = "".join(f"ordinary line {i}\n" for i in range(C.CHAIN_LINES + 4)) + "ordinary final line\n"
    lead = "start\n"
    target_edge = len(lead) + len(begin) // 2                          # where the first chunk edge should cut the marker
    body_len = target_edge + chunk + window - len(lead) - len(begin) - len(PEM_END_LINE) - len(after)
    n = body_len // 41
    body = "".join(f"{PEM_BODY}{i:08d}\n" for i in range(n))
    raw = (lead + begin + body + PEM_END_LINE + after).encode()
    start = len(raw) - window
    head_end = start + raw[start:].index(b"\n") + 1
    edge = head_end - chunk
    assert len(lead) < edge and len(lead) + len(begin) - 1 - edge > 4096, "the chunk edge does not cut the marker"
    log = tmp_path / "d.log"
    log.write_bytes(raw)
    tail = Reporter(DiagnosticsConfig(log_path=str(log), max_report_bytes=1024, redact=False)).log_tail()
    assert PEM_BODY not in tail, tail[:300]
    assert "ordinary final line" in tail, tail[-300:]


def test_s2_1_pem_state_is_judged_only_at_a_line_start():
    """`pem_open_before` refuses a position inside a line, where a marker can be cut in two (S2-1's mechanism), and
    answers at every line start; `log_tail` turns the refusal into an empty send (it never raises)."""
    data = b"a\n-----BEGIN PRIVATE KEY-----\nbody\n-----END PRIVATE KEY-----\nb\n"

    def rb(lo, hi):
        return data[lo:hi]
    answers = {}
    for pos in range(len(data) + 1):
        if pos == 0 or data[pos - 1:pos] == b"\n":
            answers[pos] = C.pem_open_before(rb, pos)
        else:
            with pytest.raises(ValueError):
                C.pem_open_before(rb, pos)
    assert answers == {0: False, 2: False, 30: True, 35: True, 61: False, 63: False}, answers


@pytest.mark.parametrize("sep_line", ["    \n", "\u200b\u200b\n"], ids=["blank-lines", "invisible-only-lines"])
def test_s2_2_a_many_line_run_between_a_label_and_its_value_counts_no_chain_line(tmp_path, sep_line):
    """S2-2: the chain bound counts NON-BLANK lines on the recogniser's view. A label ends a line before the window,
    then a run of MANY blank (or invisible-only) lines longer than the window, then the value. Counting the run's lines
    (or judging them raw, so an invisible-only line counts) would end the context inside the run and send the value.
    The value must be withheld, and the lines after the context must be sent."""
    from veracium.diagnostics import DiagnosticsConfig, Reporter
    value = "S3cr3t-Passw0rd-Value-0123456789abcdefABCDEF"
    window = 1 << 20
    n = window // len(sep_line.encode()) + 64
    text = ("password:\n" + sep_line * n + value + "\n" + "".join(f"ordinary line {i}\n" for i in range(20))
            + "ordinary final line\n")
    assert value not in C.mask_text(text), "the grammar does not recognise this across the run"
    start = len(text.encode()) - window
    assert len("password:\n") < start < len(("password:\n" + sep_line * n).encode()) - len(sep_line.encode()) * \
        (C.CHAIN_LINES + 2), "the window does not start inside the run, more than CHAIN_LINES lines before the value"
    log = tmp_path / "d.log"
    log.write_text(text)
    tail = Reporter(DiagnosticsConfig(log_path=str(log), max_report_bytes=1024, redact=False)).log_tail()
    assert value not in tail, tail[:300]
    assert "ordinary final line" in tail


@pytest.mark.parametrize("sep_line", ["    \n", "\u200b\u200b\n", "\n"], ids=["blank", "invisible-only", "empty"])
def test_s2_2_chain_safe_offset_counts_only_visible_lines(sep_line):
    """The bound itself: lines that are blank on the recogniser's view do not count toward CHAIN_LINES."""
    lines = [sep_line] * (C.CHAIN_LINES * 3) + [f"part {i}\n" for i in range(C.CHAIN_LINES)] + ["sent\n"]
    text = "".join(lines)
    assert C.chain_safe_offset(text) == text.index("sent\n")


# ==== R5-05: the final exception, constructors that add notes or a cause ==============================================

class _NoteInCtor(Exception):
    """Its display is its own `shown` attribute, set by its constructor (never `args`): rewriting `args` leaves the
    original showing the input, so only a FRESH instance can show the withheld message, and the replacement branch is
    reached (round 6's R6-02B: up to round 6 this class showed `args`, so the original itself was returned and the
    constructor never ran). The constructor then adds a note quoting the token: the final object's check is what
    removes it. `made` counts constructions."""
    made = 0

    def __init__(self, message):
        super().__init__(message)
        type(self).made += 1
        self.shown = message
        self.add_note(f"value was {TOKEN}")

    def __str__(self):
        return self.shown


class _CauseInCtor(Exception):
    """As `_NoteInCtor`, its constructor setting a cause that quotes the token."""
    made = 0

    def __init__(self, message):
        super().__init__(message)
        type(self).made += 1
        self.shown = message
        self.__cause__ = ValueError(TOKEN)

    def __str__(self):
        return self.shown


@pytest.mark.parametrize("cls", [_NoteInCtor, _CauseInCtor])
def test_r5_05_the_replacement_is_checked_after_construction(cls):
    """The witness first (round 6's R6-02B): the result is a NEW instance of the class, constructed exactly once by
    `withheld_defect`, so its constructor's note or cause was really added; then the final object shows nothing of it."""
    import traceback
    orig = cls(f"bad {TOKEN}")
    made = cls.made
    out = C.withheld_defect(orig)
    assert out is not orig and type(out) is cls, type(out)          # reached: the replacement branch
    assert cls.made == made + 1                                      # reached: its constructor ran, once
    text = "".join(traceback.format_exception(type(out), out, None))
    assert TOKEN not in text, text
    assert not getattr(out, "__notes__", None) and out.__cause__ is None


def test_r5_05_the_reviewers_round_5_constructor_case_is_in_the_gate(monkeypatch):
    """Round 6's R6-02B: the reviewer's round-5 regression, kept in the committed gate as it was written
    (`test_round5_obligations.py`'s `test_r5_05_cli_replacement_cannot_reintroduce_exception_notes`, the vectors
    module renamed to this file's): an exception whose display is an attribute its constructor sets, raised by a CLI
    verb; a fresh instance would add a note quoting the token."""
    import traceback
    from veracium import cli

    class NoteError(Exception):
        def __init__(self, message):
            super().__init__(message)
            self.display = message
            self.add_note(T.V.GH)

        def __str__(self):
            return self.display

    def defect(args, parser):
        raise NoteError(T.V.GH)

    monkeypatch.setitem(cli._VERBS, "selfcheck", defect)
    with pytest.raises(Exception) as caught:
        cli.main(["selfcheck"])
    assert caught.value.__suppress_context__
    safe = T.V.GH not in "".join(traceback.format_exception(caught.value))
    assert safe, "fresh exception constructor reintroduced an outward note"


# ==== B: the excluded BLOB column ====================================================================================

def test_b_the_finder_excludes_exactly_the_embedding_vector_and_its_contract_holds(tmp_path):
    """The finder skips declared BLOB columns. The set is exactly `edge_embedding.vec`; its one product writer passes
    `semantic.pack_vec` (dim x float32), and its reader refuses anything but 4*dim bytes, so no supported text carrier
    lives there. A new BLOB column fails here."""
    import ast
    from veracium import semantic
    from veracium.store.sqlite import SqliteStore
    s = SqliteStore(str(tmp_path / "m.db"))
    try:
        blobs = {(t, c[1]) for (t,) in s._conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name "
                                                        "NOT GLOB 'sqlite_*'")
                 for c in s._conn.execute("SELECT * FROM pragma_table_info(?)", (t,)) if (c[2] or "").upper() == "BLOB"}
    finally:
        s.close()
    assert blobs == {("edge_embedding", "vec")}, blobs
    writers = []
    for p in (ROOT / "src" / "veracium").rglob("*.py"):
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "upsert_embedding":
                vec = next(k.value for k in node.keywords if k.arg == "vec")
                writers.append((p.name, isinstance(vec, ast.Call) and getattr(vec.func, "attr", None) == "pack_vec"))
    assert writers and all(ok for _f, ok in writers), writers
    assert len(semantic.pack_vec([1.0, 2.0])) == 8
    assert semantic.unpack_vec(TOKEN, 2) is None and semantic.unpack_vec(b"\x00" * 7, 2) is None


# ==== R5-03's class in LIBRARY results (research's addition 2; dev's audit at the fix) =================================

def test_r5_03_library_dispute_masks_the_stored_relation(tmp_path):
    """`relation` is stored record text the caller did not pass: the library result masks it (the served one is
    projected again). `disputed` is the caller's own argument, E1's library scope."""
    m = T._mem(tmp_path)
    try:
        rid = _plant(m, shaped_id=False, shaped_relation=True)
        out = m.dispute("u", rid, reason="not true")
    finally:
        m.close()
    assert out["disputed"] == rid                                     # reached, and the caller's own id echoed
    assert TOKEN not in json.dumps(out) and out["relation"].startswith(C.PLACEHOLDER_PREFIX)


@pytest.mark.parametrize("mode", ["summary", "categories"])
def test_r5_03_introspect_carries_no_stored_shape_in_its_report_or_on_the_cli(tmp_path, mode, capsys):
    """`introspect` names stored relations as keys (`by_relation`, the categories) and stored reasons (`retired`), and
    `veracium introspect` prints them. Found by dev's library audit: the CLI printed a shaped relation."""
    from veracium import cli
    m = T._mem(tmp_path)
    try:
        _plant(m, shaped_id=False, shaped_relation=True)
        rep = m.introspect("u", mode=mode)
    finally:
        m.close()
    assert rep["facts"] >= 1                                           # reached: the planted fact is counted
    assert TOKEN not in json.dumps(rep, default=str)
    assert any(k.startswith(C.PLACEHOLDER_PREFIX) for k in rep["by_relation"]), rep["by_relation"]
    capsys.readouterr()
    cli.main(["introspect", "--db", str(tmp_path / "m.db"), "--user", "u"])
    assert TOKEN not in capsys.readouterr().out


#: Library results that echo the CALLER'S OWN argument (E1's library scope, research's addition 2): measured at the fix
#: with a shaped legacy id as the argument. A result naming a record the caller did not pass is not on this list.
CALLER_ECHO = {"confirm": "confirmed", "dispute": "disputed", "record_outcome": "edge_id", "reply": "edge_id"}


@pytest.mark.parametrize("method,key", sorted(CALLER_ECHO.items()))
def test_r5_03_a_library_result_echoes_only_the_callers_own_id(tmp_path, method, key):
    m = T._mem(tmp_path)
    try:
        rid = _plant(m, shaped_id=True, shaped_relation=False)

        class E:
            id = rid
        out = R4._call(m, tmp_path, E, method, "edge_id", rid)
    finally:
        m.close()
    shown = json.dumps(out, default=lambda x: x.model_dump(mode="json") if hasattr(x, "model_dump") else repr(x))
    assert out[key] == rid                                             # the caller's argument, as passed
    assert shown.count(TOKEN) == 1, shown                              # and nowhere else in the result


# ==== round 6's mutant measurement: the branches the inventories did not reach ========================================

def test_r5_06_remember_fallback_summary_uses_the_screened_event_type(tmp_path):
    """The reviewer's branch, in-tree: a provider answering non-JSON sends `remember` to the extractor fallback, whose
    summary formats `event_type`. An `event_type` of each accepted subclass form (data `chat`, shown as the token)
    must store and return `chat`. The inventory's stub answers structured output, so it never reaches this branch
    (measured: a mutant that kept the unconverted object survived every inventory cell)."""
    for form, make in SUBCLASS_FORMS.items():
        calls = []

        def llm(*args, **kwargs):
            calls.append(1)
            return "not structured output"
        sub = tmp_path / form
        sub.mkdir()
        m = T._mem(sub, llm=llm)
        try:
            out = m.remember("u", "I live in Denver", event_type=make("chat"))
            stored = T._dump(str(sub / "m.db"))
        finally:
            m.close()
        assert calls, (form, "the provider was never called: the fallback branch was not reached")
        assert TOKEN not in json.dumps(out, default=str) and TOKEN not in stored, form
        assert "chat" in stored, form                                  # the data, as the fallback formatted it


def test_r5_06_d3_returns_exact_strs():
    """D3's callee screen returns the exact str of each accepted subclass, so what is digested and refused is what was
    screened (the property its name promises; today's digest encodes the data either way, so this is asserted at
    the screen itself)."""
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp())
    m = T._mem(d)
    try:
        origin, source_id = m._d3_legacy_source_or_refuse("u", _shaped_enum("o1"), _shaped_enum("chat"), "revoke_source")
    finally:
        m.close()
    assert (type(origin), type(source_id)) == (str, str) and (origin, source_id) == ("o1", "chat")


def test_r5_02_an_ordinary_unknown_key_is_labelled_key_too(tmp_path):
    """I8: a label is built from declared names only; an unknown key is input even when it is not shaped. An ordinary
    unknown field whose VALUE is shaped refuses the record, and the label names `[key]`, not the field's own name."""
    path, _eid = T._export_with(tmp_path)
    docs = [json.loads(line) for line in path.read_text().splitlines()]
    for d in docs:
        if "relation" in d and "subject" in d:
            d["x_custom_field_7"] = TOKEN
    path.write_text("".join(json.dumps(d) + "\n" for d in docs))
    dest = T._mem(tmp_path, "dest")
    try:
        rep = dest.import_memory(str(path))
    finally:
        dest.close()
    recs = rep["credential_refused_records"]
    assert recs, "the record was not refused: the branch was not reached"
    shown = json.dumps(rep, default=str)
    assert "x_custom_field_7" not in shown and TOKEN not in shown
    assert any(r.get("field", "").endswith("[key]") for r in recs), recs


@pytest.mark.parametrize("before,after", [("password:", ""), ("aws secret", "access key is now"),
                                          ("Authorization:", "Bearer")], ids=["label", "split-label", "auth"])
def test_r5_04_a_label_before_a_window_long_blank_run_still_withholds_its_value(tmp_path, before, after):
    """The chain grammars join their parts by white space only, and white space can be longer than the window: a label
    ends a line, a blank run longer than the read window follows, then the value. The window starts inside the run, so
    the label is outside it; whole-input masking withholds the value (the precondition), and the sent tail must not
    carry it. The value is the window's first non-blank line, so it is context only, never sent."""
    from veracium.diagnostics import DiagnosticsConfig, Reporter
    value = "S3cr3t-Passw0rd-Value-0123456789abcdefABCDEF"
    window = 1 << 20
    text = (before + "\n" + " " * (window + 4096) + "\n" + (after + "\n" if after else "") + value + "\n"
            + "".join(f"ordinary line {i}\n" for i in range(C.CHAIN_LINES + 4)) + "ordinary final line\n")
    assert value not in C.mask_text(text), "the grammar does not recognise this across the blank run"
    log = tmp_path / "d.log"
    log.write_text(text)
    tail = Reporter(DiagnosticsConfig(log_path=str(log), max_report_bytes=1024, redact=False)).log_tail()
    assert value not in tail, tail[-300:]
    assert "ordinary final line" in tail


class _UndeletableNotes(Exception):
    """Its notes are a read-only property: `del exc.__notes__` raises, so only the final judgement can see them, and the
    traceback prints them (`traceback` reads `__notes__` by attribute)."""
    @property
    def __notes__(self):
        return [f"value was {TOKEN}"]


def test_r5_05_notes_that_cannot_be_deleted_refuse_the_object():
    import traceback
    orig = _UndeletableNotes("x")
    orig.args = (f"bad {TOKEN}",)
    assert TOKEN in "".join(traceback.format_exception(orig))              # the hazard: the notes print
    out = C.withheld_defect(orig)
    text = "".join(traceback.format_exception(type(out), out, None))
    assert out is not orig and TOKEN not in text, text


# ==== research's ruling on the host-only library results (2026-11-27): the RETURN census =================================
# Every public `Memory` method, classed by what its RETURN carries of a stored record, MEASURED over a store holding a
# legacy record with a credential-shaped id (and, separately, shaped stored text), the reviewer's construction
# (`_plant`). "Checked" is a test: a `host-record` row asserts its positive control (the raw shaped id IS in the host's
# return) and the outward check (no served tool, adapter, CLI verb or log line carries it); every other row asserts the
# complement. Classes:
#   host-record  a stored record (Edge / AsOfFact / Recall) or a record id the caller did NOT pass: the host's own read
#                of its store, or a host-only report naming records. v0.5.9 declares this class by that property.
#   caller-echo  only the caller's own argument (E1's library scope; `CALLER_ECHO` above pins the count).
#   none         no stored record's id or text, or a declared refusal (`CENSUS_REFUSED`).
# `export_memory` is `none` by its RETURN (counts); its FILE copies the store as it is, by design (§4e: a host backup).

RETURN_CENSUS = {
    # host-record: the host's own read of its store (record access)
    "edges_since": "host-record", "recall": "host-record", "facts_valid_at": "host-record",
    # host-record: host-only reports naming records (0022's revocation statement, 0027's PolicyReceipt, 0041's notices)
    "revoke_source": "host-record", "unrevoke_source": "host-record",
    "policy_receipt": "host-record", "policy_receipts": "host-record",
    "pending_notices": "host-record", "confirm_notice": "host-record",
    # host-record, and caller-echo too (round 6's R6-02C): 0041's RedactionReceipt echoes the target the caller passed
    # and can name a RELATED record in `surviving_derived` that it did not (measured over every plant: the only method
    # that moved); the receipt is 0041's declared host-only report
    "redact": "host-record",
    # caller-echo
    "confirm": "caller-echo", "dispute": "caller-echo", "record_outcome": "caller-echo", "reply": "caller-echo",
    "undo_restoration": "caller-echo",
    # none
    "answer": "none", "close": "none", "correct": "none", "describe_procedures": "none",
    "diagnostics_preview": "none", "embed_backfill": "none", "export_memory": "none", "flush_telemetry": "none",
    "forget": "none", "forget_everything_confirm": "none", "forget_everything_preview": "none",
    "import_memory": "none", "introspect": "none", "list_entities": "none", "maintain": "none",
    "record_procedure": "none", "record_procedure_report": "none", "remember": "none", "report_error": "none",
    "self_check": "none", "source_revocations": "none", "telemetry_preview": "none",
}
HOST_RECORD = sorted(k for k, v in RETURN_CENSUS.items() if v == "host-record")

#: `none` cells whose declared outcome is a refusal: a shaped legacy id or text cannot be copied into a new record
#: (`EXPECT_REFUSED`'s served twins).
CENSUS_REFUSED = {("correct", "id"), ("correct", "relation"), ("remember", "id")}

SHAPED_ID = "e-" + TOKEN


def _strings(x, seen=None):
    """Every str reachable from a return: containers, pydantic models, dataclasses, plain objects' attributes, Enum
    values. Typed objects are walked, not serialised, so a record object cannot hide a field from the census."""
    import dataclasses
    seen = set() if seen is None else seen
    if id(x) in seen:
        return
    seen.add(id(x))
    if isinstance(x, Enum):
        yield str(x.value)
    elif isinstance(x, (str, bytes)):
        yield x if isinstance(x, str) else x.decode("latin-1")
    elif isinstance(x, dict):
        for k, v in x.items():
            yield from _strings(k, seen)
            yield from _strings(v, seen)
    elif isinstance(x, (list, tuple, set, frozenset)):
        for v in x:
            yield from _strings(v, seen)
    elif hasattr(x, "model_dump"):
        yield from _strings(x.model_dump(mode="python"), seen)
    elif dataclasses.is_dataclass(x) and not isinstance(x, type):
        for f in dataclasses.fields(x):
            yield from _strings(getattr(x, f.name), seen)
    elif isinstance(getattr(x, "__dict__", None), dict):
        yield from _strings(vars(x), seen)


def _hits(x) -> int:
    return sum(s.count(TOKEN) for s in _strings(x))


def _public_methods() -> set:
    return {n for n, f in vars(Memory).items() if not n.startswith("_") and callable(f)}


def test_return_census_covers_every_public_method():
    """By property: the census is exactly Memory's public callables (a new method fails here until it is classed)."""
    assert set(RETURN_CENSUS) == _public_methods(), set(RETURN_CENSUS) ^ _public_methods()
    assert len(HOST_RECORD) == 10


def _host_record_call(tmp_path, name):
    """One success-reaching call per host-record method over a legacy shaped id. Returns the host's return."""
    import datetime
    from veracium.redaction import SOURCE_LIFT_REASONS, SOURCE_REVOCATION_REASONS
    if name in ("policy_receipt", "policy_receipts"):
        P27 = _load("r5c_p27", "tests/test_0027_policy_receipt.py")
        I19 = _load("r5c_i19", "tests/support_0055_i19.py")
        mem = P27._memory(tmp_path, "pol.db")
        first = mem.recall(P27.U, "boat topic", semantic=False, policy=P27.LANE).policy_receipt
        mem.close()
        I19.rename(str(tmp_path / "pol.db"), "edges", first.adjusted_order[0], SHAPED_ID)
        mem = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=str(tmp_path / "pol.db"),
                                                                  max_subgraph_edges=8, require_source_id=False))
        try:
            rid = mem.recall(P27.U, "boat topic", semantic=False, policy=P27.LANE).policy_receipt.recall_id
            return mem.policy_receipts(P27.U) if name == "policy_receipts" else mem.policy_receipt(P27.U, rid)
        finally:
            mem.close()
    if name in ("pending_notices", "confirm_notice"):
        N41 = _load("r5c_n41", "tests/test_0041_notice_state.py")
        I19 = _load("r5c_i19", "tests/support_0055_i19.py")
        _, notices, _ = N41._source(tmp_path, "src", eid="e-x")
        v = N41._holder(tmp_path, "hold.db", eid="e-x")
        v.import_memory(notices)
        assert [n["target_id"] for n in v.pending_notices(N41.U)] == ["e-x"]       # reached: a pending notice
        v.close()
        db = str(tmp_path / "hold.db")                     # a legacy store: the held record and its notice re-id'd
        I19.rename(db, "edges", "e-x", SHAPED_ID)
        con = sqlite3.connect(db)
        con.execute("UPDATE redactions SET target_id=? WHERE target_id='e-x'", (SHAPED_ID,))
        con.commit()
        con.close()
        v = N41._mem(tmp_path, "hold.db")
        try:
            pend = v.pending_notices(N41.U)
            return pend if name == "pending_notices" else v.confirm_notice(N41.U, pend[0]["notice_id"])
        finally:
            v.close()
    if name == "redact":
        m, target, related = _linked_shaped_episode(tmp_path)
        try:
            out = m.redact("u", edge_id=target, reason="operator_policy")
            assert not out.repeated and TOKEN not in target                       # reached: an ordinary target
            assert [d["id"] for d in out.surviving_derived] == [related], out    # reached: the related record
            return out
        finally:
            m.close()
    m = T._mem(tmp_path)
    try:
        rid = _plant(m, shaped_id=True, shaped_relation=False)
        assert rid == SHAPED_ID
        if name == "edges_since":
            return m.edges_since("u", "2000-01-01T00:00:00+00:00")
        if name == "recall":
            return m.recall("u", "Denver")
        if name == "facts_valid_at":
            return m.facts_valid_at("u", "user", "located_at", T=datetime.datetime.now(datetime.timezone.utc))
        m.revoke_source("u", origin=None, source_id="chat", reason=SOURCE_REVOCATION_REASONS[0])
        if name == "revoke_source":                        # the statement of a second revocation of a fresh source
            T._seed_edge(m)
            return m.revoke_source("u", origin=None, source_id="chat", reason=SOURCE_REVOCATION_REASONS[0])
        assert name == "unrevoke_source", name
        return m.unrevoke_source("u", origin=None, source_id="chat", reason=SOURCE_LIFT_REASONS[0])
    finally:
        m.close()


def _linked_shaped_episode(tmp_path):
    """Round 6's R6-02C, the reviewer's construction: an ordinary edge, and an episode sharing its provenance whose
    legacy id carries the shape. Redacting the ORDINARY edge names the related episode in `surviving_derived`.
    Returns `(memory, the ordinary target id, the shaped related id)`."""
    from veracium.schema import Episode
    m = T._mem(tmp_path)
    edge = T._seed_edge(m)
    ep = Episode(id="ep-ordinary", user_id="u", date="2026-11-26", summary="ordinary episode",
                 provenance=edge.provenance)
    m.store.add_episode(ep)
    doc = ep.model_dump(mode="json")
    rid = "ep-" + TOKEN
    doc["id"] = rid
    con = m.store._conn
    con.execute("UPDATE episodes SET id=?,json=? WHERE id=?", (rid, json.dumps(doc), ep.id))
    con.commit()
    return m, edge.id, rid


def test_the_served_forget_fact_projects_the_related_receipt_id(tmp_path):
    """R6-02C's outward half, served: `forget_fact` over the same plant succeeds, and its result carries no shape (the
    receipt passes `_locate_receipt` and the projection). The reviewer's control, committed."""
    pytest.importorskip("mcp")                  # Binding builds the served server (the pydantic-floor lane has none)
    from veracium.adapters._surface import Binding
    m, target, related = _linked_shaped_episode(tmp_path)
    try:
        out = Binding(m, user_id="u", capability="direct").call("forget_fact", {"edge_id": target})
    finally:
        m.close()
    assert out.get("ok") is True, out                                  # reached: the redaction happened
    assert TOKEN not in json.dumps(out), out


def test_the_credential_finders_act_prints_no_related_receipt_id(tmp_path):
    """R6-02C's outward half, the CLI: `credential_finder.act` redacts by the raw ids it holds and reads only
    `repeated` from the receipt, so its line carries nothing of the related record."""
    from veracium import credential_finder as CF
    m, target, related = _linked_shaped_episode(tmp_path)
    try:
        hit = CF.Hit(user_id="u", table="edges", carrier="edge.text", record_kind="edge", record_id=target,
                     parent_kind="edge", parent_id=target)
        assert CF.targets([hit]) == ([("u", "edge", target)], []), CF.targets([hit])   # reached: one redaction
        out = CF.act(m, [hit])
    finally:
        m.close()
    assert out and out[0]["outcome"] == "redacted", out                # reached: the redaction happened
    assert TOKEN not in json.dumps(out), out


@pytest.mark.parametrize("name", HOST_RECORD)
def test_a_host_record_return_carries_the_raw_id_and_no_log_line_does(tmp_path, name, caplog):
    """The positive control: the host's own return carries the legacy shaped id RAW (the declared class, not masked).
    The outward check's log half: nothing logged during the call carries it."""
    import logging
    caplog.set_level(logging.DEBUG)
    out = _host_record_call(tmp_path, name)
    assert _hits(out) >= 1, (name, out)
    assert not [r for r in caplog.records if TOKEN in r.getMessage()], name


def test_a_host_record_method_reaches_no_outward_surface_but_through_a_screened_caller():
    """The outward check's surface half, by `ast` over every src module: a host-record method is called from outside
    `Memory` only by (a) the served `*_impl` functions, whose results pass the projection
    (`test_r5_03_every_impl_is_served_through_the_projection`, the served sweep), or a helper only an `*_impl`
    calls; (b) the CLI's `recall` verb, which prints the masked `context` alone
    (`test_the_cli_recall_verb_prints_no_planted_shape`); (c) selfcheck, over its own throwaway store."""
    import ast
    callers, impl_only = set(), {}
    for f in sorted((ROOT / "src" / "veracium").rglob("*.py")):
        rel = f.relative_to(ROOT).as_posix()
        tree = ast.parse(f.read_text(encoding="utf-8"))
        top = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        for n in top:
            if rel == "src/veracium/__init__.py" and isinstance(n, ast.ClassDef) and n.name == "Memory":
                continue
            for c in ast.walk(n):
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr in HOST_RECORD:
                    callers.add((rel, n.name, c.func.attr))
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Name):
                    impl_only.setdefault((rel, c.func.id), set()).add(n.name)
    allowed = {("src/veracium/mcp_server.py", "recall_impl", "recall"),
               # round 6's R6-02C: `redact` is host-record; the served route locates its receipt and is projected
               # (test_the_served_forget_fact_projects_the_related_receipt_id), and the CLI's finder reads only
               # `repeated` (test_the_credential_finders_act_prints_no_related_receipt_id)
               ("src/veracium/mcp_server.py", "forget_fact_report", "redact"),
               ("src/veracium/credential_finder.py", "act", "redact"),
               ("src/veracium/mcp_server.py", "find_facts_report", "recall"),
               ("src/veracium/cli.py", "_memory_verbs", "recall"),
               ("src/veracium/selfcheck.py", "_check_injection", "recall"),
               ("src/veracium/selfcheck.py", "_check_revocation", "recall")}
    assert callers == allowed, callers ^ allowed
    for helper in ("find_facts_report", "forget_fact_report"):
        users = impl_only[("src/veracium/mcp_server.py", helper)]
        assert users and all(u.endswith("_impl") for u in users), (helper, users)


@pytest.mark.parametrize("plant", ["id", "relation"])
def test_the_cli_recall_verb_prints_no_planted_shape(tmp_path, plant, capsys):
    from veracium import cli
    m = T._mem(tmp_path)
    try:
        _plant(m, shaped_id=(plant == "id"), shaped_relation=(plant == "relation"))
        assert _hits(m.recall("u", "Denver")) >= 1                 # reached: the host's own recall holds the record
    finally:
        m.close()
    capsys.readouterr()
    assert cli.main(["recall", "--db", str(tmp_path / "m.db"), "--user", "u", "Denver"]) == 0
    out = capsys.readouterr()
    assert out.out.strip() and TOKEN not in out.out + out.err


_NOARG = {"close": {}, "flush_telemetry": {}, "telemetry_preview": {}, "report_error": {}, "diagnostics_preview": {},
          "list_entities": {}, "self_check": {"record": False}}
_BY_USER = {"embed_backfill": {}, "maintain": {}, "forget": {}, "source_revocations": {}}
#: the parameter `R4._call` is given (its value passes through unchanged): any of the method's own
_R4_PARAM = {"answer": "query", "describe_procedures": "query", "export_memory": "path", "import_memory": "path",
             "introspect": "mode", "record_procedure": "summary", "record_procedure_report": "summary",
             "remember": "event_text", "correct": "edge_id", "forget_everything_preview": "principal",
             "forget_everything_confirm": "principal"}


@pytest.mark.parametrize("plant", ["id", "relation"])
@pytest.mark.parametrize("name", sorted(k for k, v in RETURN_CENSUS.items() if v == "none"))
def test_a_none_return_carries_no_stored_shape(tmp_path, name, plant):
    """The complement: over a store holding the planted record, the call reaches its success (or its declared
    refusal) and the return carries no shape."""
    from veracium.credentials import CredentialRefused
    from veracium.redaction import SOURCE_REVOCATION_REASONS
    m = T._mem(tmp_path)
    try:
        rid = _plant(m, shaped_id=(plant == "id"), shaped_relation=(plant == "relation"))

        class E:
            id = rid
        if name == "source_revocations":                    # reached: one revocation to report
            m.revoke_source("u", origin=None, source_id="chat", reason=SOURCE_REVOCATION_REASONS[0])
        if (name, plant) in CENSUS_REFUSED:
            with pytest.raises(CredentialRefused) as ei:
                R4._call(m, tmp_path, E, name, _R4_PARAM[name], lambda v: v)
            assert TOKEN not in str(ei.value)
            return
        if name in _NOARG:
            out = getattr(m, name)(**_NOARG[name])
        elif name in _BY_USER:
            out = getattr(m, name)("u", **_BY_USER[name])
        else:
            out = R4._call(m, tmp_path, E, name, _R4_PARAM[name], lambda v: v)
        if name == "source_revocations":
            assert out["history"], out
    finally:
        m.close()
    assert _hits(out) == 0, (name, out)


def test_undo_restoration_echoes_only_the_callers_id(tmp_path):
    """`undo_restoration` (caller-echo) over a legacy shaped id: a restored store whose restored edge is re-id'd in
    every table that names it."""
    U44 = _load("r5c_u44", "tests/test_0044_t7_undo.py")
    I19 = _load("r5c_i19", "tests/support_0055_i19.py")
    db = U44._restored(tmp_path)
    I19.rename(db, "edges", U44.P, SHAPED_ID)
    con = sqlite3.connect(db)
    for t in ("edge_embedding", "redactions", "arity_inventory", "migration_outcome"):
        col = "target_id" if t == "redactions" else "edge_id"
        con.execute(f"UPDATE {t} SET {col}=? WHERE {col}=?", (SHAPED_ID, U44.P))
    con.commit()
    con.close()
    m = U44._mem(db)
    try:
        out = m.undo_restoration(U44.U, SHAPED_ID, correlation_id="c1")
    finally:
        m.close()
    assert out["undone"] == SHAPED_ID and not out["replayed"]           # reached: the restoration was undone
    assert _hits(out) == 1, out


def test_redact_echoes_only_the_callers_id(tmp_path):
    """The caller-echo half of `redact`'s return (round 6's R6-02C classes it host-record for its other half): over a
    shaped target with no related record, the receipt names the caller's id once."""
    m = T._mem(tmp_path)
    try:
        rid = _plant(m, shaped_id=True, shaped_relation=False)
        out = m.redact("u", edge_id=rid, reason="operator_policy")
    finally:
        m.close()
    assert not out.repeated and _hits(out) == 1, out                    # reached, and the caller's id once
