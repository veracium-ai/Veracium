"""Dev's executable model of the 0018 adjacent-rungs v0.3 contract tables (research 1af75b1e, revision 3; run 2 was
against revision 2, 84e70bb8).

A MODEL, NOT THE PRODUCT. It implements the tables' A1 (target argument), A2 (one rung's transaction), A3 (the mint),
B (recovery classes), C1 (RungReport + binding) and C2 (the walk) ON TOP OF the pin's real kernel: `open_versioned`,
`_apply_forward`, the pin's audit writers and the pin's `TerminalFacts` validator. A rung's target replaces the head by
a process-local patch of `schema_version.SCHEMA_VERSION` and `migration.SCHEMA_VERSION` (the round-1 probe's
technique, widened to the opening path because A1 says the target replaces SCHEMA_VERSION "throughout the decision
table"). No product file is edited. Fixtures are synthetic (sv.create + one legacy outcome row), not I33's
release-authored fixtures.

Every cell prints one JSON line: {"cell", "expect", "got", "ok"}. The run ends with a summary; exit 1 if any cell is
not ok. Cells the model cannot express are printed as {"cell", "inexpressible": why} and are NOT counted as ok.

Usage, from the pin's tree/: PYTHONPATH=src python -B model_v03.py <new empty work dir>
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import sqlite3
import sys
import urllib.parse
import uuid
from contextlib import contextmanager
from typing import NamedTuple, Optional

from veracium.store import migration as m
from veracium.store import release_migration as rm
from veracium.store import schema_version as sv

ROOT = pathlib.Path(sys.argv[1]).resolve()
ROOT.mkdir(parents=True, exist_ok=False)
HEAD = sv.SCHEMA_VERSION
FIRST = 1                                   # FIRST_MIGRATABLE at this head
ATT = rm.MigrationAttestation(quiesced=True, backup_ref="dev-v03-model")
RESULTS = []


def emit(rec):
    """Deterministic output: the work directory prints as <work> and every operation id as op-<id>, so a re-run is
    byte-comparable and no local path is printed."""
    s = json.dumps(rec, sort_keys=True, default=str).replace(str(ROOT), "<work>")
    print(re.sub(r"op-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "op-<id>", s))


def local(s):
    """Normalise BEFORE any truncation, so a note's length never depends on the work directory's path."""
    return str(s).replace(str(ROOT), "<work>")


def cell(name, expect, got, note=None):
    ok = expect == got
    RESULTS.append(ok)
    rec = {"cell": name, "expect": expect, "got": got, "ok": ok}
    if note:
        rec["note"] = note
    emit(rec)


def inexpressible(name, why):
    RESULTS.append(None)
    emit({"cell": name, "inexpressible": why})


# ---------------------------------------------------------------- fixtures --------------------------------------------
def legacy_row():
    return {"id": "episode-1", "user_id": "model-user", "date": "2026-05-05", "summary": "legacy observation",
            "kind": "outcome", "edge_id": "edge-1", "outcome": "concurred",
            "provenance": {"author_of_evidence": "system", "evidence_ref": "model-event"}}


# ---- round 3 (E2-01, E2-02): the preflight's predicate, 0013's rung absence rule, and observers that never create ---
def nothing_at(path):
    """The PREFLIGHT's predicate (0018; release_migration.py at the pin, L903-905 and L1002-1004):
    `os.path.exists(os.path.realpath(path))` is False. Used by this model's preflight and its observers. The RUNG
    is the dedicated operation and uses accepted 0013's own rule instead (`absent_lstat`): two accepted rules, which
    differ on a dangling symlink (research, correcting its stage-1 P1)."""
    return not os.path.exists(os.path.realpath(path))


def absent_lstat(path):
    """Accepted 0013's absence rule for the dedicated operation (specs/0013-store-migrations.md L662 at the pin):
    "Absence is proven by an `lstat` ENOENT, NEVER by `os.path.lexists` (round 13 f3)", re-run FRESH on a mode=rw open
    failure (round 16, finding 5)."""
    try:
        os.lstat(path)
    except FileNotFoundError:
        return True
    return False


RECHECK = {"on": True}                    # round 3 mutant switch: 0013's fresh re-check after a failed open
URI_RAW = {"on": False}                    # round 3 counter-control: round 2's unencoded URI, put back


def rw_uri(path):
    """E2-01: the canonical path's FILESYSTEM BYTES, percent-encoded, so `?`, `#`, `%`, a space or a non-UTF-8 name
    names exactly that file (round 2's model interpolated the path and migrated a sibling). `mode=rw` opens without
    creating (row 11a)."""
    if URI_RAW["on"]:
        return f"file:{path}?mode=rw"
    return "file:" + urllib.parse.quote(os.fsencode(os.path.realpath(path))) + "?mode=rw"


def ro_uri(path):
    return "file:" + urllib.parse.quote(os.fsencode(os.path.realpath(path))) + "?mode=ro"


def make(path, v, *, stamped=True, populated=False, foreign=False):
    path = str(path)
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path, isolation_level=None)
    c.execute("BEGIN")
    sv.create(c, v)
    if stamped:
        c.execute(f"PRAGMA user_version={v}")
    if populated and v <= 2:
        r = legacy_row()
        c.execute("INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                  (r["id"], r["user_id"], r["date"], json.dumps(r)))
    if foreign:
        c.execute("CREATE TABLE model_foreign(x)")
    c.execute("COMMIT")
    c.close()
    return path


def stamp_of(path):
    if nothing_at(path):                       # round 3: an observer never creates (E2-02's class)
        return None
    c = sqlite3.connect(ro_uri(path), uri=True)
    try:
        return c.execute("PRAGMA user_version").fetchone()[0]
    finally:
        c.close()


def file_sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() if os.path.exists(path) else None


def content(path):
    if nothing_at(path):                       # round 3: an observer never creates (E2-02's class)
        return None
    c = sqlite3.connect(ro_uri(path), uri=True)
    try:
        rows = {}
        for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
            rows[name] = sorted(map(repr, c.execute(f'SELECT * FROM "{name}"').fetchall()))
        return c.execute("PRAGMA user_version").fetchone()[0], rows
    finally:
        c.close()


@contextmanager
def head(t):
    saved = (sv.SCHEMA_VERSION, m.SCHEMA_VERSION)
    sv.SCHEMA_VERSION = m.SCHEMA_VERSION = t
    try:
        yield
    finally:
        sv.SCHEMA_VERSION, m.SCHEMA_VERSION = saved


# ---------------------------------------------------------------- A1: the target argument ----------------------------
def open_target(conn, path, *, migrate_to=None, older=None, new=None, allow_adopt=True):
    """A1, checked BEFORE the runtime gate and before any store access."""
    if migrate_to is None:
        return sv.open_versioned(conn, path, older=older, new=new, allow_adopt=allow_adopt)
    if type(migrate_to) is not int:
        raise TypeError(f"migrate_to must be exactly int, not {type(migrate_to).__name__}")
    if not FIRST + 1 <= migrate_to <= HEAD:
        raise ValueError(f"migrate_to {migrate_to} is outside {FIRST + 1}..{HEAD}")
    if migrate_to == HEAD:
        return sv.open_versioned(conn, path, older=older, new=new, allow_adopt=allow_adopt)
    if older is None:
        raise ValueError("a migration target below head requires the migration hook")
    # MODEL FINDING (run 1): the runtime gate is NOT target-relative. verify_build() and attestation_revision() read
    # the module's SCHEMA_VERSION, so moving the head to t refuses every below-head rung as unsupported-sqlite. The
    # model measures the build's status ONCE at the production head and holds it for the rung: A1 must say that only
    # the version/shape decision table takes t, and the runtime gate stays at the build's own revision.
    status = sv.runtime_status()
    saved = sv.runtime_status
    sv.runtime_status = lambda: status
    try:
        with head(migrate_to):
            return sv.open_versioned(conn, path, older=older, new=new, allow_adopt=allow_adopt)
    finally:
        sv.runtime_status = saved


# ---------------------------------------------------------------- A3: the mint ----------------------------------------
class Authority(NamedTuple):
    operation_id: str
    from_version: int
    to_version: int
    source_digest: str
    source_stamp: int


class ModelMintError(Exception):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


MINTS = []                                  # every mint call, for "stops before the next mint"


def mint(path, att, *, resolved=None):
    """A3: by the mint's OWN observation; `resolved` labels a failure and decides nothing (I18)."""
    MINTS.append(path)
    if rm._attestation_problems(att):
        raise ModelMintError("attestation-refused")
    try:
        found, objs = rm._observe(path)
    except rm._Unobservable as exc:
        raise ModelMintError(exc.kind)
    if 1 <= found <= HEAD - 1 and sv.digest(objs, found) in sv.accepted_digests(found):
        b = found
    elif found == 0 and objs:
        b = sv.resolve(objs, sv.version_records(), candidates=sv.legacy_base_versions())
        if b is None or not 1 <= b <= HEAD - 1:
            raise ModelMintError("source-unaccepted")
    else:
        raise ModelMintError("source-unaccepted")
    return Authority(f"op-{uuid.uuid4()}", b, b + 1, sv.digest(objs, b), found)


# ---------------------------------------------------------------- A2: one rung's transaction ---------------------------
class SourceMissing(Exception):
    def __init__(self, found, base):
        self.found, self.base = found, base
        super().__init__(f"no accepted v{{t-1}} source where the authority attests one; observed v{found}")


class AuditUnknown(Exception):
    """Model of the attempted write neither confirmed nor disproved (B row 6)."""


SWAP = {"fn": None}                         # a fault: applied between the mint and the transaction
FAULT = {}                                  # in-rung faults keyed by name


def rung_txn(path, auth, apath):
    """A2 inside one rung's transaction, authority b -> t. Returns (outcome, facts, diagnostic, attempted_written)."""
    b, t = auth.from_version, auth.to_version
    if SWAP["fn"] is not None:
        SWAP["fn"](path, b, t)
    state = {"attempted": False}

    def older(c, spath, found, objs, base, *, runtime):
        if base != t - 1:
            raise SourceMissing(found, base)
        m._apply_forward(c, base)
        if "postcondition" in FAULT:
            raise m.MigrationPostconditionError(base, FAULT["postcondition"], ["model forced failure"])
        if "dberror" in FAULT:
            raise sqlite3.OperationalError("model: disk I/O error inside the rung")
        ev = m._mig_event("migration_attempted", auth.operation_id, spath, base, t, m.migration_runtime(runtime))
        if "attempted-unavailable" in FAULT:
            raise rm._AuditSinkWriteFailed("model: attempted write proven not written")
        if "attempted-unknown" in FAULT:
            raise AuditUnknown("model: attempted write neither confirmed nor disproved")
        rm._write_attempted(apath, auth.operation_id, ev)
        state["attempted"] = True

    def new(c, spath, found, objs):
        raise SourceMissing(found, None)

    # revision 3, row 11a: open WITHOUT creating. Round 3 (E2-01): the URI carries the path's bytes, encoded; and an
    # open that FAILS is not absence: only nothing at the path (the preflight's predicate) is `missing`, and an
    # existing path that cannot be opened is row 11b's existing rule, `store-unopenable` (release_migration._observe).
    # Absence is 0013's: an lstat ENOENT, checked before the open and re-run fresh after a failed one.
    if absent_lstat(path):
        return ("migration-source-missing", rm.TerminalFacts("migration-source-missing", b, t, False, False,
                                                             "missing", None),
                "nothing at the path (opened without creating)", False)
    try:
        conn = sqlite3.connect(rw_uri(path), uri=True)
    except sqlite3.OperationalError as exc:
        if RECHECK["on"] and absent_lstat(path):   # 0013 round 16 f5: removed between the check and the open
            return ("migration-source-missing", rm.TerminalFacts("migration-source-missing", b, t, False, False,
                                                                 "missing", None),
                    "nothing at the path (opened without creating)", False)
        return ("store-unopenable", rm.TerminalFacts("store-unopenable", b, t, False, False, "unknown", None),
                f"cannot open: {exc!r}", False)
    try:
        try:
            r = open_target(conn, path, migrate_to=t, older=older, new=new, allow_adopt=False)
        except SourceMissing as exc:
            return ("migration-source-missing", rm.TerminalFacts("migration-source-missing", b, t, False, False,
                                                                 "unaccepted", None),
                    f"no accepted v{t - 1} source where the authority attests one; observed v{exc.found}", False)
        except rm._AuditSinkWriteFailed:
            return ("migration-audit-unavailable", None, "attempted-record write failed", False)
        except AuditUnknown:
            return ("migration-audit-state-unknown", None, rm._NO_RECORD_DIAGNOSTICS["migration-audit-state-unknown"],
                    False)
        except sv.StoreVersionError as exc:
            st = ("unaccepted" if exc.reason in ("foreign-shape", "newer", "invalid-version", "stamped-shape-mismatch")
                  else "unknown")
            diag = str(exc)
            if exc.reason == "newer":
                diag = f"v{exc.found} is newer than this rung's target v{t}"
            return (exc.reason, rm.TerminalFacts(exc.reason, b, t, False, False, st, None), diag, state["attempted"])
        except sqlite3.DatabaseError as exc:
            return ("migration-failed", rm.TerminalFacts("migration-failed", b, t, None, None, "unknown", None),
                    f"the rung failed ({exc}); the post-failure store state is unknown", state["attempted"])
        label = str.__str__(r)
        if label == "migrated" and r.resulting_version == t:
            return ("migrated", rm.TerminalFacts("migrated", b, t, True, True, "destination", t),
                    f"migrated v{b} -> v{t}", state["attempted"])
        if label == "current" and r.resulting_version == t:
            return ("current", rm.TerminalFacts("current", b, t, r.store_changed, r.transaction_committed,
                                                "destination", t), "the store was already at this rung's target",
                    state["attempted"])
        return ("internal-error", rm.TerminalFacts("internal-error", b, t, None, None, "unknown", None),
                f"impossible cell {label!r}/v{r.resulting_version}", state["attempted"])
    finally:
        conn.close()


# ---------------------------------------------------------------- C1: the carrier --------------------------------------
NO_RECORD = ("migration-audit-unavailable", "migration-audit-state-unknown", "migration-quiescence-required",
             "migration-evidence-missing")


class ModelResult(NamedTuple):
    outcome: str
    store_changed: Optional[bool]
    transaction_committed: Optional[bool]
    resulting_state: str
    resulting_version: Optional[int]
    diagnostic: str


def result_lawful_somewhere(r):
    """C1: MigrationResult's widened domain — lawful at SOME adjacent rung (or a no-record / preflight row)."""
    if r.outcome in NO_RECORD:
        return (r.store_changed, r.transaction_committed, r.resulting_state, r.resulting_version) == \
               (False, False, "unknown", None)
    return any(rm.TerminalFacts(r.outcome, b, b + 1, r.store_changed, r.transaction_committed, r.resulting_state,
                                r.resulting_version).problems() == [] for b in range(FIRST, HEAD))


class RungReport(NamedTuple):
    kind: str
    result: Optional[ModelResult]
    preflight_base: Optional[int]
    source_stamp: Optional[int]
    operation_id: Optional[str]
    from_version: Optional[int]
    to_version: Optional[int]
    expected_base: Optional[int]

    @classmethod
    def make(cls, **kw):
        r = cls(**kw)
        p = r.problems()
        if p:
            raise ValueError("invalid RungReport: " + "; ".join(p))
        return r

    def problems(self):
        out = []
        if type(self.kind) is not str or self.kind not in ("preflight", "delegated", "unexpected-base"):
            return [f"kind {self.kind!r}"]
        if self.kind == "unexpected-base":
            if self.result is not None:
                out.append("unexpected-base carries a result")
            if self.expected_base == self.preflight_base:
                out.append("unexpected-base where the bases agree")
        else:
            if type(self.result) is not ModelResult:
                out.append("result is not exactly a ModelResult")
        if self.kind == "delegated":
            if not (type(self.from_version) is int and type(self.to_version) is int
                    and self.to_version == self.from_version + 1 and FIRST <= self.from_version < HEAD):
                out.append(f"endpoints {self.from_version}->{self.to_version} are not an adjacent rung")
            elif type(self.result) is ModelResult and self.result.outcome not in NO_RECORD:
                f = rm.TerminalFacts(self.result.outcome, self.from_version, self.to_version,
                                     self.result.store_changed, self.result.transaction_committed,
                                     self.result.resulting_state, self.result.resulting_version)
                out += [f"binding: {x}" for x in f.problems()]
            if not (type(self.operation_id) is str and rm._OPERATION_RE.fullmatch(self.operation_id)):
                out.append("operation_id")
        else:
            if self.operation_id is not None or self.from_version is not None or self.to_version is not None:
                out.append("a non-delegated report carries operation context")
        return out


class ModelAuditWriteError(Exception):
    def __init__(self, rung_context, facts):
        self.rung_context, self.facts = rung_context, facts
        super().__init__(f"terminal record not published for {rung_context}")


class ModelPackageEscape(Exception):
    def __init__(self, rung_context):
        self.rung_context = rung_context
        super().__init__(f"package consistency escape (rung_context={rung_context})")


# ---------------------------------------------------------------- the rung entry ---------------------------------------
def preflight(path):
    if "pre-mint-escape" in FAULT:
        raise ModelPackageEscape(None)
    if nothing_at(path):                       # 0018's preflight rule (realpath + exists), the pin's own
        return ("refusal", "missing", None, None)
    try:
        found, objs = rm._observe(path)
    except rm._Unobservable as exc:
        return ("refusal", exc.kind, None, None)
    if found == HEAD:
        return ("current", None, HEAD, found)
    if found > HEAD:
        return ("refusal", "newer", None, found)
    if found < 0:
        return ("refusal", "invalid-version", None, found)
    if found > 0:
        if sv.digest(objs, found) in sv.accepted_digests(found):
            return ("base", None, found, found)
        return ("refusal", "stamped-shape-mismatch", None, found)
    if not objs:
        return ("refusal", "migration-source-missing", None, 0)
    b = sv.resolve(objs, sv.version_records(), candidates=sv.legacy_base_versions())
    if b is None:
        return ("refusal", "foreign-shape", None, 0)
    return ("base", None, b, 0)


def run_release_rung(path, *, host_attestation, expect_base=None):
    kind, label, base, stamp = preflight(path)
    if kind == "current":
        return RungReport.make(kind="preflight", result=ModelResult("current", False, False, "destination", HEAD,
                                                                    "current at head"),
                               preflight_base=base, source_stamp=stamp, operation_id=None, from_version=None,
                               to_version=None, expected_base=expect_base)
    if kind == "refusal":
        return RungReport.make(kind="preflight", result=ModelResult(label, False, False, "unknown", None,
                                                                    f"preflight refusal {label}"),
                               preflight_base=None, source_stamp=stamp, operation_id=None, from_version=None,
                               to_version=None, expected_base=expect_base)

    def unexpected(b, st):
        return RungReport.make(kind="unexpected-base", result=None, preflight_base=b, source_stamp=st,
                               operation_id=None, from_version=None, to_version=None, expected_base=expect_base)
    if expect_base is not None and base != expect_base:          # C2 check 1
        return unexpected(base, stamp)
    reasons = []
    while True:
        try:
            auth = mint(path, host_attestation)
            break
        except ModelMintError as exc:
            reasons.append(exc.reason)
            if len(reasons) == 3:
                return RungReport.make(kind="preflight", result=ModelResult("mint-contention", False, False,
                                                                            "unknown", None, ", ".join(reasons)),
                                       preflight_base=base, source_stamp=stamp, operation_id=None,
                                       from_version=None, to_version=None, expected_base=expect_base)
        kind, label, base, stamp = preflight(path)
        if kind != "base":
            return run_release_rung(path, host_attestation=host_attestation, expect_base=expect_base)
        if expect_base is not None and base != expect_base:      # C2 check 2
            return unexpected(base, stamp)
    if expect_base is not None and auth.from_version != expect_base:   # C2 check 3: discard, nothing consumed
        return unexpected(auth.from_version, auth.source_stamp)
    apath = rm.audit_trail_path(path)
    ctx = (auth.operation_id, auth.from_version, auth.to_version)
    if "post-mint-escape" in FAULT:
        raise ModelPackageEscape(ctx)
    outcome, facts, diag, _ = rung_txn(path, auth, apath)
    if facts is not None:
        try:
            if "terminal-write" in FAULT:
                raise OSError("model: terminal write unavailable")
            pub = facts                          # round-3 closure: a fixture may publish a chosen RECORD; the
            if "terminal-facts" in FAULT:          # rung's own report keeps the transaction's real facts
                pub = FAULT["terminal-facts"](facts, auth)
            rm._write_terminal(apath, auth.operation_id, pub)
        except Exception:
            if "terminal-facts" in FAULT:
                facts = FAULT["terminal-facts"](facts, auth)
            raise ModelAuditWriteError(ctx, facts)
        res = ModelResult(outcome, facts.store_changed, facts.transaction_committed, facts.resulting_state,
                          facts.resulting_version, diag)
    else:
        res = ModelResult(outcome, False, False, "unknown", None, diag)
    return RungReport.make(kind="delegated", result=res, preflight_base=base, source_stamp=auth.source_stamp,
                           operation_id=auth.operation_id, from_version=auth.from_version,
                           to_version=auth.to_version, expected_base=expect_base)


# ---------------------------------------------------------------- B and C2: the walk -----------------------------------
def klass(changed, committed):
    if changed is False and committed is False:
        return "unchanged"
    if changed is True and committed is True:
        return "committed"
    if changed is None and committed is None:
        return "unknown"
    return f"impossible({changed},{committed})"


def walk(path):
    """C2. Returns (exit, committed rung ids, lines, stop)."""
    expect, committed, lines, reports = None, [], [], []
    while True:
        try:
            rep = run_release_rung(path, host_attestation=ATT, expect_base=expect)
        except ModelAuditWriteError as exc:
            f = exc.facts
            k = klass(f.store_changed, f.transaction_committed)
            if k == "committed":
                committed.append(exc.rung_context[0])
                lines.append(f"rung v{exc.rung_context[1]} -> v{exc.rung_context[2]}: committed; its terminal record "
                             f"was NOT published (operation {exc.rung_context[0]}); store v{f.resulting_version} "
                             f"(from the error's carried facts)")
                return 3, committed, lines, {"stop": "audit-write", "class": k, "version": f.resulting_version,
                                             "rerun": "resumes the store; does not write the missing record",
                                             "ctx": exc.rung_context}
            return 3, committed, lines, {"stop": "audit-write", "class": k, "version": "unknown", "ctx": exc.rung_context}
        except ModelPackageEscape as exc:
            return 3, committed, lines, {"stop": "package", "ctx": exc.rung_context,
                                         "version": "unavailable (pre-mint: no operation minted)"
                                         if exc.rung_context is None else "readback"}
        reports.append(rep)
        if rep.kind == "preflight" and rep.result.outcome == "current":
            lines.append(f"store current at v{HEAD}")
            return 0, committed, lines, {"stop": "current", "version": HEAD, "reports": reports}
        if rep.kind == "preflight":
            return 1, committed, lines, {"stop": rep.result.outcome, "class": "unchanged",
                                         "version": "unknown", "rerun": True}
        if rep.kind == "unexpected-base":
            return 1, committed, lines, {"stop": "unexpected-base", "class": "no operation",
                                         "diag": f"observed v{rep.preflight_base} where v{rep.expected_base} was "
                                                 f"expected (the store changed between rungs)"}
        r = rep.result
        if r.outcome in ("migrated", "current") and r.resulting_version == rep.to_version:
            lines.append(f"rung v{rep.from_version} -> v{rep.to_version}: {r.outcome} (operation {rep.operation_id})")
            if klass(r.store_changed, r.transaction_committed) == "committed":
                committed.append(rep.operation_id)
            expect = rep.to_version
            continue
        k = klass(r.store_changed, r.transaction_committed) if r.outcome not in NO_RECORD else (
            "unchanged; authority MAY be consumed" if r.outcome == "migration-audit-state-unknown" else "unchanged")
        version = r.resulting_version if r.resulting_version is not None else "unknown"
        rerun = {"migration-audit-state-unknown": "NO: query the operation id first"}.get(
            r.outcome, "not automatically: inspect first" if k == "unknown" else "yes")
        return 1, committed, lines, {"stop": r.outcome, "class": k, "version": version, "rerun": rerun,
                                     "op": rep.operation_id, "endpoints": (rep.from_version, rep.to_version)}


# ======================================================================================================================
# CELLS
# ======================================================================================================================
def p(name):
    return str(ROOT / f"{name}.db")


emit({"model": "0018 adjacent-rungs v0.5.1 (research 7a2e150f): v0.3's tables (research 1af75b1e), round 3's controls and the round-3 closure", "head": HEAD,
      "runtime": sv.runtime_status().status, "legacy_base_versions": sorted(sv.legacy_base_versions()),
      "source": os.path.relpath(m.__file__)})

# ---- A1 ---------------------------------------------------------------------------------------------------------------
class IntSub(int):
    pass


for label, arg, hook, want in [("None", None, None, "opened"), ("True", True, "hook", "TypeError"),
                               ("False", False, "hook", "TypeError"), ("float", 15.0, "hook", "TypeError"),
                               ("str", "15", "hook", "TypeError"), ("int-subclass", IntSub(15), "hook", "TypeError"),
                               ("1", 1, "hook", "ValueError"), ("0", 0, "hook", "ValueError"),
                               ("17", HEAD + 1, "hook", "ValueError"), ("15-no-hook", 15, None, "ValueError"),
                               ("HEAD-no-hook", HEAD, None, "opened"), ("HEAD-hook", HEAD, "hook", "opened")]:
    path = make(p(f"a1-{label}"), HEAD)
    before = file_sha(path)
    conn = sqlite3.connect(path)
    try:
        open_target(conn, path, migrate_to=arg, older=(lambda *a, **k: None) if hook else None)
        got = "opened"
    except (TypeError, ValueError) as exc:
        got = type(exc).__name__
    finally:
        conn.close()
    cell(f"A1 migrate_to={label}", {"outcome": want, "untouched": True},
         {"outcome": got, "untouched": file_sha(path) == before or got == "opened"})

# I37: migrate_to=HEAD identical to None, byte-for-byte, on a below-head fixture with and without the hook
for hook in (False, True):
    outs = []
    for arg in (None, HEAD):
        path = make(p(f"i37-{hook}-{arg}"), HEAD - 1)
        conn = sqlite3.connect(path)
        try:
            open_target(conn, path, migrate_to=arg,
                        older=(lambda c, s, f, o, b, *, runtime: m._apply_forward(c, b)) if hook else None)
            outs.append(("ok", stamp_of(path)))
        except Exception as exc:
            outs.append((type(exc).__name__, getattr(exc, "reason", None), stamp_of(path)))
        finally:
            conn.close()
    cell(f"I37 migrate_to=HEAD == None (hook={hook})", True, outs[0] == outs[1], note=str(outs))


# ---- A2: one rung, swaps between the mint and the transaction ---------------------------------------------------------
def swap_to(kind):
    def fn(path, b, t):
        if kind == "none":
            return
        if kind == "absent":
            os.remove(path)
            return
        if kind == "empty":
            os.remove(path)
            sqlite3.connect(path).close()
            return
        v, stamped, foreign = {"t": (t, True, False), "head": (HEAD, True, False), "above": (t + 1, True, False),
                               "below": (t - 2, True, False), "src-foreign": (t - 1, True, True),
                               "legacy-unstamped": (1, False, False), "t-unstamped": (t, False, False),
                               "foreign": (1, False, True)}[kind]
        make(path, v, stamped=stamped, foreign=foreign)
        if kind == "t-drift":
            pass
    return fn


def drift_t(path, b, t):
    make(path, t)
    c = sqlite3.connect(path, isolation_level=None)
    idx = [n for (n,) in c.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")]
    if idx:
        c.execute(f'DROP INDEX "{idx[0]}"')
    c.close()
    drift_t.dropped = idx[:1]


A2_EXPECT = {  # (row, outcome, (changed, committed, state, version-or-'t'))
    "none": ("1", "migrated", (True, True, "destination", "t")),
    "t": ("4", "current", (False, False, "destination", "t")),
    "t-drift": ("5", "current", (True, True, "destination", "t")),
    "src-foreign": ("3", "stamped-shape-mismatch", (False, False, "unaccepted", None)),
    "below": ("7a", "migration-source-missing", (False, False, "unaccepted", None)),
    "above": ("7b", "newer", (False, False, "unaccepted", None)),
    "head": ("7b", "newer", (False, False, "unaccepted", None)),
    "legacy-unstamped": ("8a", "migration-source-missing", (False, False, "unaccepted", None)),
    "t-unstamped": ("8b (unreachable at this head -> row 9)", "foreign-shape", (False, False, "unaccepted", None)),
    "foreign": ("9", "foreign-shape", (False, False, "unaccepted", None)),
    "empty": ("10", "migration-source-missing", (False, False, "unaccepted", None)),
    "absent": ("11a", "migration-source-missing", (False, False, "missing", None)),
}

for b in (1, 13, 15):
    t = b + 1
    for kind, (row, want, facts) in A2_EXPECT.items():
        if kind in ("above", "head") and t >= HEAD:
            continue                                    # 7b only when t < HEAD
        if kind == "head" and t + 1 == HEAD:
            continue                                    # same store as "above"
        if kind == "below" and t - 2 < 1:
            continue
        if kind == "legacy-unstamped" and t - 1 == 1:
            continue                                    # that is row 2, below
        path = make(p(f"a2-{b}-{kind}"), b)
        SWAP["fn"] = drift_t if kind == "t-drift" else swap_to(kind)
        try:
            auth = mint(path, ATT)
            outcome, f, diag, attempted = rung_txn(path, auth, rm.audit_trail_path(path))
        except Exception as exc:
            outcome, f, diag, attempted = f"escape:{type(exc).__name__}", None, local(exc)[:160], None
        finally:
            SWAP["fn"] = None
        exp_facts = None if facts is None else tuple(t if x == "t" else x for x in facts)
        got_facts = None if f is None else (f.store_changed, f.transaction_committed, f.resulting_state,
                                            f.resulting_version)
        lawful = None if f is None else f.problems() == []
        note = local(diag)[:140]
        if kind == "t-drift":
            note = f"dropped index {drift_t.dropped}; {note}"
        if kind == "absent":
            note += f"; file exists after: {os.path.exists(path)}"
        cell(f"A2 row {row} rung {b}->{t} swap={kind}",
             {"outcome": want, "facts": exp_facts, "lawful": True, "file_after": kind != "absent"},
             {"outcome": outcome, "facts": got_facts, "lawful": lawful, "file_after": os.path.exists(path)},
             note=note)

# A2 row 2: the unstamped legacy store at rung 1->2; bytes unchanged before delegation; forced failure restores it
path = make(p("a2-row2"), 1, stamped=False, populated=True)
before = (file_sha(path), content(path))
pf = preflight(path)
auth = mint(path, ATT)
after_mint = (file_sha(path), content(path))
cell("A2 row 2 preflight+mint leave bytes and stamp unchanged", True, before == after_mint,
     note=f"preflight={pf[0]} base={pf[2]} stamp={pf[3]}; authority {auth.from_version}->{auth.to_version} "
          f"source_stamp={auth.source_stamp}")
FAULT["postcondition"] = m.STEP_STAMP
outcome, f, diag, _ = rung_txn(path, auth, rm.audit_trail_path(path))
FAULT.clear()
cell("A2 row 12 forced first-rung failure on the unstamped store", {"outcome": "unsupported-migration",
                                                                     "restored": True},
     {"outcome": outcome, "restored": content(path) == before[1]}, note=f"stamp after {stamp_of(path)}")
auth = mint(path, ATT)
outcome, f, diag, attempted = rung_txn(path, auth, rm.audit_trail_path(path))
cell("A2 row 2 unstamped legacy migrates 1->2 and is stamped 2",
     {"outcome": "migrated", "stamp": 2, "facts_lawful": True, "record_from": 1},
     {"outcome": outcome, "stamp": stamp_of(path), "facts_lawful": f.problems() == [],
      "record_from": json.load(open(rm.audit_trail_path(path)))[auth.operation_id]["attempted"]["from_version"]})

# A2 row 12 at a stamped rung (13->14): unsupported-migration, stamp stays t-1
path = make(p("a2-row12-13"), 13)
auth = mint(path, ATT)
FAULT["postcondition"] = "model-step"
outcome, f, diag, _ = rung_txn(path, auth, rm.audit_trail_path(path))
FAULT.clear()
cell("A2 row 12 postcondition failure at rung 13->14", {"outcome": "unsupported-migration", "stamp": 13,
                                                         "facts": (False, False, "unknown", None)},
     {"outcome": outcome, "stamp": stamp_of(path), "facts": (f.store_changed, f.transaction_committed,
                                                              f.resulting_state, f.resulting_version)})

# A3 / I18: a forged resolution cannot alter the mint's outcome, under either real-store condition
for label, v, stamped, want in (("eligible-stamped-13", 13, True, (13, 14)), ("refusing-foreign", 1, False, "refused")):
    path = make(p(f"a3-{label}"), v, stamped=stamped, foreign=(label == "refusing-foreign"))
    forged_list, built = [None], []
    for fb in (7, 15, 2):
        try:
            forged_list.append(rm.PreflightResolution(path, fb, "0" * 64))
            built.append(fb)
        except Exception as exc:                       # the pin's constructor may refuse a forged shape
            built.append(f"{fb}:{type(exc).__name__}")
    outs = set()
    for forged in forged_list:
        try:
            a = mint(path, ATT, resolved=forged)
            outs.add(str((a.from_version, a.to_version)))
        except ModelMintError:
            outs.add("refused")
    cell(f"A3 forged resolution decides nothing ({label})", [str(want)], sorted(outs),
         note=f"forged resolutions tried: {built}")

# ---- C1: binding ------------------------------------------------------------------------------------------------------
lawful = ModelResult("migrated", True, True, "destination", 14, "x")
op = f"op-{uuid.uuid4()}"
for (fr, to), want in (((13, 14), []), ((14, 15), "fails")):
    try:
        RungReport.make(kind="delegated", result=lawful, preflight_base=fr, source_stamp=fr, operation_id=op,
                        from_version=fr, to_version=to, expected_base=None)
        got = []
    except ValueError:
        got = "fails"
    cell(f"C1 binding (13,14,migrated) under authority {fr}->{to}", want, got)
cell("C1 widened MigrationResult admits a lawful v14 commit", True, result_lawful_somewhere(lawful))
cell("C1 widened MigrationResult refuses a commit at v14 labelled current-with-None",
     False, result_lawful_somewhere(ModelResult("migrated", True, True, "destination", None, "x")))

# ---- C2 + B: walks ----------------------------------------------------------------------------------------------------
for b in (13, 1):
    path = make(p(f"walk-{b}"), b, populated=(b == 1))
    MINTS.clear()
    code, ids, lines, stop = walk(path)
    cell(f"C2 walk from v{b}: exactly HEAD-b0 rungs, then the head-level check, exit 0",
         {"exit": 0, "rungs": HEAD - b, "mints": HEAD - b, "stamp": HEAD, "distinct_ids": HEAD - b},
         {"exit": code, "rungs": len(ids), "mints": len(MINTS), "stamp": stamp_of(path),
          "distinct_ids": len(set(ids))})

path = make(p("walk-legacy"), 1, stamped=False, populated=True)
code, ids, lines, stop = walk(path)
cell("C2 walk from an unstamped legacy v1 store", {"exit": 0, "rungs": HEAD - 1, "stamp": HEAD},
     {"exit": code, "rungs": len(ids), "stamp": stamp_of(path)})

path = make(p("walk-head"), HEAD)
code, ids, lines, stop = walk(path)
cell("C2 walk at HEAD: zero rungs, exit 0", {"exit": 0, "rungs": 0}, {"exit": code, "rungs": len(ids)})

# the store changes between rungs: stops BEFORE the next mint
path = make(p("walk-changed"), 13)
orig_rung = rung_txn
state = {"n": 0}


def rung_then_swap(path_, auth, apath):
    out = orig_rung(path_, auth, apath)
    state["n"] += 1
    if state["n"] == 1:
        make(path_, 12)                                # another writer moves it down after rung 1 commits
    return out


rung_txn = rung_then_swap
MINTS.clear()
code, ids, lines, stop = walk(path)
rung_txn = orig_rung
cell("C2 a store changed between rungs stops with unexpected-base before the next mint",
     {"exit": 1, "stop": "unexpected-base", "rungs": 1, "mints": 1},
     {"exit": code, "stop": stop["stop"], "rungs": len(ids), "mints": len(MINTS)}, note=stop.get("diag"))

# a row-4 current (another operation reached the target) continues the walk, uncounted
path = make(p("walk-row4"), 13)
state = {"n": 0}


def swap_on_second(path_, b, t):
    state["n"] += 1
    if state["n"] == 2:
        make(path_, t)


SWAP["fn"] = swap_on_second
code, ids, lines, stop = walk(path)
SWAP["fn"] = None
cell("C2 a row-4 current continues the walk and is not counted as committed",
     {"exit": 0, "committed": HEAD - 13 - 1, "printed": HEAD - 13},
     {"exit": code, "committed": len(ids), "printed": len(lines) - 1}, note=" | ".join(lines))

# B rows 5, 6, 7, 8 at rung 2 of a v13 walk (the first rung commits)
for row, fault, want in (("5", "attempted-unavailable", {"stop": "migration-audit-unavailable", "class": "unchanged",
                                                         "version": "unknown", "rerun": "yes"}),
                         ("6", "attempted-unknown", {"stop": "migration-audit-state-unknown",
                                                     "class": "unchanged; authority MAY be consumed",
                                                     "version": "unknown", "rerun": "NO: query the operation id first"}),
                         ("7", "dberror", {"stop": "migration-failed", "class": "unknown", "version": "unknown",
                                           "rerun": "not automatically: inspect first"})):
    path = make(p(f"b-row{row}"), 13)
    state = {"n": 0}

    def fault_on_second(path_, b, t, fault=fault):
        state["n"] += 1
        if state["n"] == 2:
            FAULT[fault] = True
    SWAP["fn"] = fault_on_second
    code, ids, lines, stop = walk(path)
    SWAP["fn"] = None
    FAULT.clear()
    cell(f"B row {row} at rung 2 of a v13 walk", {**want, "committed_before": 1, "stamp": 14},
         {k: stop.get(k) for k in want} | {"committed_before": len(ids), "stamp": stamp_of(path)},
         note=f"previous rung reached v14; printed version must not be 14: printed {stop.get('version')}")

path = make(p("b-row8"), 13)
state = {"n": 0}


def term_fault_on_second(path_, b, t):
    state["n"] += 1
    if state["n"] == 2:
        FAULT["terminal-write"] = True


SWAP["fn"] = term_fault_on_second
code, ids, lines, stop = walk(path)
SWAP["fn"] = None
FAULT.clear()
missing_op = stop["ctx"][0]
cell("B row 8 terminal write fails after rung 2 commits", {"exit": 3, "class": "committed", "version": 15,
                                                           "stamp": 15, "committed": 2},
     {"exit": code, "class": stop["class"], "version": stop["version"], "stamp": stamp_of(path),
      "committed": len(ids)})
code2, ids2, lines2, stop2 = walk(path)
cell("B row 8 rerun resumes the store but does not write the missing terminal record",
     {"exit": 0, "rungs": 1, "stamp": HEAD, "missing_record": "absent"},
     {"exit": code2, "rungs": len(ids2), "stamp": stamp_of(path),
      "missing_record": rm.read_terminal(missing_op, audit_path=rm.audit_trail_path(path)).kind})

# C1: a pre-mint escape after two committed rungs does not reuse an id
path = make(p("c1-premint"), 13)
state = {"n": 0}
orig_preflight = preflight


def preflight_third(path_):
    state["n"] += 1
    if state["n"] == 3:
        FAULT["pre-mint-escape"] = True
    try:
        return orig_preflight(path_)
    finally:
        FAULT.pop("pre-mint-escape", None)


preflight = preflight_third
code, ids, lines, stop = walk(path)
preflight = orig_preflight
cell("C1 a pre-mint escape after two committed rungs carries no id",
     {"exit": 3, "committed": 2, "ctx": None, "version": "unavailable (pre-mint: no operation minted)"},
     {"exit": code, "committed": len(ids), "ctx": stop["ctx"], "version": stop["version"]})

# ---- M1 closed by the hook binding: a swap to v13 under authority 15->16 refuses, no attempted event ------------------
path = make(p("m1-closed"), 15)
auth = mint(path, ATT)
SWAP["fn"] = swap_to("below")
outcome, f, diag, attempted = rung_txn(path, auth, rm.audit_trail_path(path))
SWAP["fn"] = None
cell("M1 closed: a swap to v14-2 under 15->16 refuses with no store change and no attempted event",
     {"outcome": "migration-source-missing", "stamp": 14, "attempted": False},
     {"outcome": outcome, "stamp": stamp_of(path), "attempted": attempted})

# ---- E2: the check sequence, recorded at runtime, on a populated fixture ----------------------------------------------
orig_refuse = m._refuse_unless
seq = []


def recording(base, step, problems):
    seq.append(step)
    return orig_refuse(base, step, problems)


def rung_checks(path, b):
    seq.clear()
    m._refuse_unless = recording
    try:
        c = sqlite3.connect(path, isolation_level=None)
        with head(b + 1):
            c.execute("BEGIN IMMEDIATE")
            m._apply_forward(c, b)
            c.execute("COMMIT")
        c.close()
    finally:
        m._refuse_unless = orig_refuse
    return list(seq)


path = make(p("e2-populated"), 2, populated=True)
declared = {}
for b in range(2, HEAD):
    declared[b + 1] = rung_checks(path, b)
emit({"E2 check sequences at the pin (populated synthetic v2 walk)": declared})
cell("E2 rung 2->3 check sequence contains the helper-carried STEP_CHAINS", True, m.STEP_CHAINS in declared[3])
repeats = {t: sorted(s for s in set(v) if v.count(s) > 1) for t, v in declared.items()}
cell("E2 the v16 rung records a repeated check", True, bool(repeats.get(16)), note=str(repeats.get(16)))
stamp_check_seen = any(m.STEP_STAMP in v for v in declared.values())
cell("E2 a stamp verification is recorded through _refuse_unless", True, stamp_check_seen,
     note="if False: the final stamp check is not a _refuse_unless call at the pin, and sequence 2 needs a second hook")

# control: the helper-carried check dropped from EXECUTION must fail sequence 2
path = make(p("e2-control"), 2, populated=True)
orig_chains = m._check_outcome_chains
m._check_outcome_chains = lambda *a, **k: None
try:
    got = rung_checks(path, 2)
finally:
    m._check_outcome_chains = orig_chains
cell("E2 control: _check_outcome_chains made a no-op fails the 2->3 check sequence", True, got != declared[3],
     note=f"executed {got} vs declared {declared[3]}")

inexpressible("E2 sequence 1 (writes = add/alter/data entries in order) and the 'two data steps swapped' control",
              "needs the §5f.1 census run at an intermediate target, which is E1's own change (the pin's gate is "
              "head-bound: gate_paths() covers HEAD-1 only). Expressible once E1 lands, not before.")
inexpressible("E2 the repeated _edges_unchanged dropped control",
              "_edges_unchanged is a nested definition inside _apply_forward's v16 block; dropping ONE of its calls "
              "needs an edit to the kernel's source, which this model does not make. The declaration form makes it a "
              "one-entry edit at implementation.")


# ======================================================================================================================
# ROUND 3 (0018 amendment v0.4.1; round 2's verdict E2-01, R2-01, R2-02; research's stage-1 P1, P4, P5)
# ======================================================================================================================
import ast as _ast
import itertools as _it

emit({"round 3": "focused controls for E2-01, R2-01 and R2-02 (0018 adjacent rungs v0.4.1)"})


# ---- E2-01: the URI preserves the path's filesystem bytes; an open failure is not absence ----------------------------
def rung_once(path):
    """one rung from a fresh mint, through the model's own transaction (A2)"""
    auth = mint(path, ATT)
    return rung_txn(path, auth, rm.audit_trail_path(path))


E201 = {"question": "name?suffix.db", "hash": "name#suffix.db", "percent": "name%41.db", "space": "name suffix.db"}
SIBLING = {"question": "name", "hash": "name", "percent": "nameA.db", "space": None}
for label, nm in list(E201.items()) + [("non-utf8", os.fsdecode(b"name\xffsuffix.db"))]:
    for raw in (False, True):
        d = ROOT / f"e201-{label}-{'raw' if raw else 'encoded'}"
        d.mkdir()
        sib = SIBLING.get(label)
        sib_path = make(d / sib, 13) if sib else None
        target = str(d / nm)
        try:
            make(target, 13)
        except Exception as exc:                       # the platform or sqlite3 refuses the name: not a model claim
            inexpressible(f"E2-01 {label} ({'raw' if raw else 'encoded'})", f"cannot create the fixture: {local(exc)[:120]}")
            continue
        sib_before = file_sha(sib_path) if sib_path else None
        URI_RAW["on"] = raw
        try:
            outcome, f, diag, _ = rung_once(target)
        except Exception as exc:
            outcome, f, diag = f"escape:{type(exc).__name__}", None, local(exc)[:120]
        finally:
            URI_RAW["on"] = False
        got = {"outcome": outcome, "target_stamp": stamp_of(target),
               "sibling_unchanged": (file_sha(sib_path) == sib_before) if sib_path else None}
        want = {"outcome": "migrated", "target_stamp": 14, "sibling_unchanged": True if sib_path else None}
        if not raw:
            cell(f"E2-01 {label}: the rung migrates exactly the named file, the sibling untouched", want, got,
                 note=local(diag)[:120] if got != want else None)
        elif label in ("question", "hash", "percent"):  # the counter-control: round 2's unencoded URI, put back
            cell(f"E2-01 counter-control {label}: the UNENCODED URI does not migrate the named file", True,
                 got != want, note=str(got))
        else:
            emit({"E2-01 unencoded, recorded only": label, "got": got})

# an existing directory at the path is unopenable (row 11b), never missing; a dangling symlink swapped in after the mint
# is lstat-present, so unopenable too (0013); at preflight time it is `missing` (0018). Two accepted rules, stated.
def swap_dir(path, b, t):
    os.remove(path)
    os.mkdir(path)


def swap_dangling(path, b, t):
    os.remove(path)
    os.symlink(path + ".gone", path)


for kind, fn, want in (("directory", swap_dir, ("store-unopenable", (False, False, "unknown", None))),
                       ("dangling-symlink", swap_dangling, ("store-unopenable", (False, False, "unknown", None)))):
    path = make(p(f"e201-{kind}"), 13)
    SWAP["fn"] = fn
    try:
        outcome, f, diag, _ = rung_once(path)
    finally:
        SWAP["fn"] = None
    got = (outcome, None if f is None else (f.store_changed, f.transaction_committed, f.resulting_state, f.resulting_version))
    cell(f"E2-01 a {kind} at the path, swapped in after the mint", want, got,
         note=f"lawful={f.problems() == [] if f else None}; created: {os.path.lexists(path + '.gone')}")
# 0013 round 16 f5: the source vanishes BETWEEN the pre-open lstat and the open; the fresh re-check says missing
def vanish_at_open(recheck):
    path = make(p(f"e201-vanish-at-open-{recheck}"), 13)
    auth = mint(path, ATT)
    real = sqlite3.connect

    def vanish(*a, **k):
        sqlite3.connect = real
        os.remove(path)
        raise sqlite3.OperationalError("model: unable to open database file")
    sqlite3.connect, RECHECK["on"] = vanish, recheck
    try:
        outcome, f, _, _ = rung_txn(path, auth, rm.audit_trail_path(path))
    finally:
        sqlite3.connect, RECHECK["on"] = real, True
    return (outcome, None if f is None else (f.store_changed, f.transaction_committed, f.resulting_state, f.resulting_version))


cell("0013 round 16 f5: a source vanishing between the lstat and the open is re-checked fresh: missing, not unopenable",
     ("migration-source-missing", (False, False, "missing", None)), vanish_at_open(True))
cell("0013 round 16 f5 mutant: without the fresh re-check the same race reads store-unopenable (the cell above kills it)",
     True, vanish_at_open(False)[0] == "store-unopenable")
link = str(ROOT / "p1-dangling.db")
os.symlink(link + ".gone", link)
cell("a dangling symlink at PREFLIGHT time is `missing` there (0018's realpath + exists), so nothing is minted; "
     "swapped in after the mint, the rung finds it lstat-present and unopenable (0013's lstat rule): store-unopenable",
     ("refusal", "missing"), preflight(link)[:2])
cell("neither rule created the symlink's target", False, os.path.lexists(link + ".gone"))


# ---- R2-01: count by facts BEFORE continuation; the §7 mapping is total ------------------------------------------------
def row_matches(outcome, ch, co, state, ver, t):
    """v0.4.1 §7 for a DELEGATED record (no-record outcomes are rows 5/6, handled before). Every row whose predicate
    holds; the totality cell requires exactly one."""
    k, ok_out = klass(ch, co), outcome in ("migrated", "current") and ver == t
    rows = []
    if k == "committed" and ok_out:
        rows.append("continue")
    if k == "committed" and not ok_out:
        rows.append("4b")
    if k == "unchanged" and outcome == "current" and ver == t:
        rows.append("continue-uncounted")
    if k == "unchanged" and not (outcome == "current" and ver == t):
        rows.append("4")
    if k == "unknown":
        rows.append("7")
    return rows


VERSIONS = lambda b, t: (None, b, t, b - 1, t + 1, HEAD + 1)
TRI = (True, False, None)


class ModelAuditReadError(Exception):
    def __init__(self, rung_context, outcome):
        self.rung_context, self.outcome = rung_context, outcome
        # the pin's own class derives the state from the frozen outcome->states map, never from the record
        self.derived_state = rm.MigrationAuditReadError(rung_context[0], "missing", outcome).derived_resulting_state
        super().__init__(f"terminal readback failed for {rung_context}")


R3 = {"at": None, "kind": None, "facts": None, "n": 0}


def run_rung_r3(path, expect):
    """the rung entry, with ONE injected event at delegated rung number R3['at']"""
    nxt = R3["n"] + 1
    armed = R3["at"] == nxt
    if armed and R3["kind"] == "write-error":
        FAULT["terminal-write"] = True
    if armed and R3["kind"] == "write-error-facts":     # R3-02: a write error CARRYING chosen facts
        FAULT["terminal-write"] = True
        FAULT["terminal-facts"] = lambda f, a: rm.TerminalFacts(R3["facts"][0], a.from_version, a.to_version, *R3["facts"][1:])
    if armed and R3["kind"] == "pi-escape":             # R3-03: publish a chosen record, then the post-mint escape
        FAULT["terminal-facts"] = R3["facts"]
    if armed and R3["kind"] == "postcondition":
        FAULT["postcondition"] = m.STEP_STAMP
    try:
        rep = run_release_rung(path, host_attestation=ATT, expect_base=expect)
    finally:
        FAULT.pop("terminal-write", None)
        FAULT.pop("postcondition", None)
        FAULT.pop("terminal-facts", None)
    if rep.kind != "delegated":
        return rep
    R3["n"] = nxt
    ctx = (rep.operation_id, rep.from_version, rep.to_version)
    if armed and R3["kind"] == "override":
        o, ch, co, st, ver = R3["facts"]
        return rep._replace(result=ModelResult(o, ch, co, st, ver, "model: injected lawful carrier"))
    if armed and R3["kind"] in ("post-commit-escape", "pi-escape"):
        raise ModelPackageEscape(ctx)
    if armed and R3["kind"] == "read-error":
        raise ModelAuditReadError(ctx, rep.result.outcome)
    return rep


def walk4(path, mutant=None):
    """SUPERSEDED (round 3 R3-01): v0.4.1's walk and its row_matches, kept only as the superseded implementation. v0.4.1 §4g: an id enters `committed` iff its validated facts are (True, True), BEFORE continuation is decided.
    `mutant` names one superseded or broken rule (the cells' kill list)."""
    expect, committed, lines = None, [], []
    R3["n"] = 0
    while True:
        try:
            rep = run_rung_r3(path, expect)
        except ModelAuditWriteError as exc:
            f = exc.facts
            k = klass(f.store_changed, f.transaction_committed)
            if k == "committed":
                committed.append(exc.rung_context[0])
                return 3, committed, lines, {"row": "8", "version": f"v{f.resulting_version} (carried)",
                                             "rerun": "resumes the store; does not write the missing record"}
            return 3, committed, lines, {"row": "9", "version": "unknown", "rerun": "as row 4 or 7"}
        except ModelAuditReadError as exc:
            ver = exc.derived_state if mutant == "row10-state-as-version" else "unknown"
            return 3, committed, lines, {"row": "10", "version": ver, "derived_state": f"{exc.derived_state} (derived-from-outcome)",
                                         "rerun": "not until the record is inspected"}
        except ModelPackageEscape as exc:
            if exc.rung_context is None:
                return 3, committed, lines, {"row": "11", "version": "unavailable (pre-mint: no operation minted)",
                                             "rerun": "no: repair or reinstall the build"}
            rb = rm.read_terminal(exc.rung_context[0], audit_path=rm.audit_trail_path(path))
            rec = rb.kind == "record"
            if rec and klass(rb.facts.store_changed, rb.facts.transaction_committed) == "committed" \
                    and mutant != "readback-not-counted":
                committed.append(exc.rung_context[0])
            ver = f"v{rb.facts.resulting_version} (recorded)" if rec and rb.facts.resulting_version is not None \
                else f"unavailable (readback: {rb.kind})"
            rerun = "yes" if (mutant == "rerun-if-version-known" and rec) else "no: repair or reinstall the build"
            return 3, committed, lines, {"row": "12", "version": ver, "rerun": rerun}
        if rep.kind == "preflight" and rep.result.outcome == "current":
            lines.append(f"store current at v{HEAD}")
            return 0, committed, lines, {"row": "current", "version": HEAD}
        if rep.kind == "preflight":
            return 1, committed, lines, {"row": "1-3", "stop": rep.result.outcome, "version": "unknown", "rerun": "yes"}
        if rep.kind == "unexpected-base":
            return 1, committed, lines, {"row": "unexpected-base", "version": "unknown"}
        r = rep.result
        if r.outcome in NO_RECORD:
            row = "6" if r.outcome == "migration-audit-state-unknown" else "5"
            return 1, committed, lines, {"row": row, "stop": r.outcome, "version": "unknown",
                                         "rerun": "NO: query the operation id first" if row == "6" else "yes"}
        k = klass(r.store_changed, r.transaction_committed)
        if k == "committed" and mutant != "r2-algorithm":
            committed.append(rep.operation_id)                       # FIRST, whatever the outcome
        rows = row_matches(r.outcome, r.store_changed, r.transaction_committed, r.resulting_state,
                           r.resulting_version, rep.to_version)
        row = rows[0] if len(rows) == 1 else f"IMPOSSIBLE{rows}"
        if row in ("continue", "continue-uncounted"):
            if k == "committed" and mutant in ("r2-algorithm", "count-twice"):
                committed.append(rep.operation_id)                   # round 2's place (and, doubled, both places)
            lines.append(f"rung v{rep.from_version} -> v{rep.to_version}: {r.outcome} (operation {rep.operation_id})")
            expect = rep.to_version
            continue
        rerun = {"4": "yes", "4b": "not automatically: inspect first", "7": "not automatically: inspect first"}.get(row, "?")
        if mutant == "rerun-if-version-known" and r.resulting_version is not None:
            rerun = "yes"
        version = (f"v{r.resulting_version}, labelled recorded: committed at v{r.resulting_version} with {r.outcome}"
                   if row == "4b" else (f"v{r.resulting_version}" if r.resulting_version is not None else "unknown"))
        return 1, committed, lines, {"row": row, "stop": r.outcome, "version": version, "rerun": rerun}


# ======================================================================================================================
# ROUND-3 CLOSURE (0018 v0.5.1; round 3's verdict R3-01, R3-02, R3-03): one executable recovery classifier
# ======================================================================================================================
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import recovery_v05 as RC                                    # noqa: E402

RC.load(pathlib.Path(__file__).resolve().parent / "recovery-table-v051.json")
emit({"round-3 closure": "recovery by §7a-7c of v0.5.1, its table EXTRACTED (recovery-table-v051.json)",
      "rows": sorted(RC.TABLE)})
CLOSURE = []                                                 # (cell, expect, got) of every closure check, for the mutants
SEQ = _it.count()                                            # a unique fixture name per store


def ccell(name, expect, got, note=None, asserts=None):
    """a closure cell: also recorded for the mutant runs; `asserts` names the §7 row and ids it pins (the row map)"""
    CLOSURE.append(name)
    rec_note = note
    cell(name, expect, got, note=rec_note)
    if asserts:
        emit({"asserts": {"cell": name, "row": asserts[0], "actions": list(asserts[1])}})


def expected_ids(row):
    """the ids a row's decision must carry, from the extracted table and §7's two composite rules; None for a row the
    table does not have (a mutant's invented row reads as a failure, never a crash)"""
    base = row.split(">", 1)[-1]
    if base not in RC.TABLE:
        return None
    if row.startswith("P4>"):
        u = row[3:]
        return ("no-rerun-this-build",) if u == "U4" else tuple(RC.TABLE[u]["actions"])
    if row.startswith("E1>"):
        u = row[3:]
        store = (RC.TABLE["E1"]["resume"],) if u in ("C1", "U0") else tuple(RC.TABLE[u]["actions"])
        return store + (RC.TABLE["E1"]["disclosure"],)
    return tuple(RC.TABLE[row]["actions"])


DELEG = sorted(rm.TERMINAL_OUTCOMES - {"package-inconsistent"} - set(RC.NO_RECORD))
# admission is separate from validity (I15'): the RECORD route admits the terminal outcomes minus package-inconsistent
# (E4's alone) and minus the four no-record outcomes, which are refused before observation and enter only with no facts
RUNGS = ((1, 2), (13, 14), (15, 16))


def lawful(o, b, t, f):
    try:
        return rm.TerminalFacts(o, b, t, *f).problems() == []
    except Exception:
        return False


# B1: the preflight domain, DERIVED from the pin's own code (never a free enumeration)
def preflight_domain():
    src = pathlib.Path(rm.__file__).read_text()
    tree = _ast.parse(src)
    fn = {n.name: n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)}
    out = []
    for c in _ast.walk(fn["_preflight_classify"]):
        if isinstance(c, _ast.Call) and isinstance(c.func, _ast.Name) and c.func.id == "_intercept":
            o, st = c.args[0], c.args[3]
            if isinstance(o, _ast.Constant):
                out.append((o.value, st.value, f"_preflight_classify L{c.lineno}"))
            else:                                            # `exc.kind`: every kind _observe raises
                for r in _ast.walk(fn["_observe"]):
                    if isinstance(r, _ast.Call) and getattr(r.func, "id", "") == "_Unobservable":
                        out.append((r.args[0].value, st.value, f"_preflight_classify L{c.lineno} via _observe L{r.lineno}"))
    for name in ("_invalid_request", "run_release_migration"):
        for c in _ast.walk(fn[name]):
            if isinstance(c, _ast.Call) and getattr(c.func, "id", "") == "MigrationResult" and c.args \
                    and isinstance(c.args[0], _ast.Constant) and c.args[0].value in ("invalid-request", "mint-contention"):
                out.append((c.args[0].value, c.args[3].value, f"{name} L{c.lineno}"))
    return sorted(set(out))


PRE = preflight_domain()
emit({"B1 the preflight domain, derived from the pin's release_migration.py": [list(x) for x in PRE]})


def names_input(row, o, f, t):
    """the chosen row's own input cell names this input (independent of the classifier's code path)"""
    T = RC.TABLE
    if row[0] == "N":
        return o in T[row]["outcomes"]
    if row == "C1":
        return klass(f[0], f[1]) == "committed" and o in T["C1"]["outcomes"] and f[3] == t
    if row == "C2":
        return klass(f[0], f[1]) == "committed" and not (o in T["C1"]["outcomes"] and f[3] == t)
    if row == "K":
        return klass(f[0], f[1]) == "unknown"
    if row == "U0":
        return klass(f[0], f[1]) == "unchanged" and o == "current" and f[2] == "destination" and f[3] == t
    named = [u for u in ("U1", "U2", "U3", "U4", "U5", "U6") if o in T[u]["outcomes"] and T[u]["state"] in (None, f[2])]
    if row == "U7":
        return klass(f[0], f[1]) == "unchanged" and not named
    return klass(f[0], f[1]) == "unchanged" and named[:1] == [row]


def oracle(cls):
    """every admitted input on every route gets exactly one row and that row's ids; returns (problems, stats)"""
    bad, stats = [], {}
    for b, t in RUNGS:
        rows, adm, ref = {}, 0, 0
        for o in DELEG + list(RC.NO_RECORD):
            for f in ([None] if o in RC.NO_RECORD else
                      _it.product(TRI, TRI, sorted(rm._RESULTING_STATES), VERSIONS(b, t))):
                if f is not None and not lawful(o, b, t, f):
                    ref += 1
                    continue
                adm += 1
                d = cls("delegated", o, f, t)
                if d.row not in RC.TABLE or tuple(d.actions) != expected_ids(d.row) or not d.actions \
                        or not names_input(d.row, o, f, t):
                    bad.append(("delegated", b, t, o, f, d))
                rows[d.row] = rows.get(d.row, 0) + 1
                if d.row not in RC.TABLE:
                    continue
                if f is not None:                            # the same facts, carried by the write error (E1)
                    e = cls("write-error", o, f, t)
                    if not e.row.startswith("E1>") or tuple(e.actions) != expected_ids("E1>" + d.row) \
                            or e.counted != (klass(f[0], f[1]) == "committed"):
                        bad.append(("write-error", b, t, o, f, e))
        stats[f"{b}->{t}"] = {"admitted": adm, "refused": ref, "rows": dict(sorted(rows.items()))}
    prow = {}
    for o, st, _ in PRE:
        d = cls("preflight", o, (False, False, st, None))
        if not (d.row in ("P0", "P1", "P2") or d.row.startswith("P4>")) or tuple(d.actions) != expected_ids(d.row):
            bad.append(("preflight", o, st, d))
        prow[d.row] = prow.get(d.row, 0) + 1
    stats["preflight"] = dict(sorted(prow.items()))
    return bad, stats


bad, stats = oracle(RC.classify)
ccell("R3-01 the exhaustive oracle: every admitted input on every route has exactly one row and that row's ids", [], bad[:5],
      note=f"domain: outcome in TERMINAL_OUTCOMES ({len(rm.TERMINAL_OUTCOMES)}) minus package-inconsistent and minus the "
           f"{len(rm.TERMINAL_OUTCOMES & set(RC.NO_RECORD))} no-record outcomes it contains, so {len(DELEG)} on the record route; "
           f"plus the {len(RC.NO_RECORD)} no-record outcomes, with no facts; (changed, committed) in {{T, F, None}}^2, state in _RESULTING_STATES, version in "
           f"{{None, b, t, b-1, t+1, HEAD+1}}, as an ordinary record and as a write error; the {len(PRE)} derived "
           f"preflight inputs. Per rung: {stats}")

# the oracle's reach, made visible to the row map: one representative input per row it selected (the first, in domain
# order), asserted with that row's ids
def representatives():
    seen = {}
    for b, t in RUNGS:
        for o in DELEG + list(RC.NO_RECORD):
            for f in ([None] if o in RC.NO_RECORD else _it.product(TRI, TRI, sorted(rm._RESULTING_STATES), VERSIONS(b, t))):
                if f is not None and not lawful(o, b, t, f):
                    continue
                d = RC.classify("delegated", o, f, t)
                seen.setdefault(d.row, (f"delegated {o} {f} at {b}->{t}", d))
                if f is not None:
                    e = RC.classify("write-error", o, f, t)
                    seen.setdefault(e.row, (f"write error carrying {o} {f} at {b}->{t}", e))
    for o, st, src in PRE:
        d = RC.classify("preflight", o, (False, False, st, None))
        seen.setdefault(d.row, (f"preflight {o}/{st} ({src})", d))
    seen.setdefault("P3", ("unexpected-base", RC.classify("unexpected-base")))
    seen.setdefault("E2", ("a terminal read error", RC.classify("read-error")))
    seen.setdefault("E3", ("a pre-mint package escape", RC.classify("package-pre-mint")))
    return seen


for row, (what, d) in sorted(representatives().items()):
    emit({"asserts": {"cell": f"oracle reach: {what}", "row": d.row, "actions": list(d.actions)}})


# the reviewer's four carriers at 13->14, and a later head's outcome (research N1)
for o, f, want in (("internal-error", (False, False, "source", 13), "U7"), ("migration-failed", (False, False, "source", 13), "U7"),
                   ("migration-result-mismatch", (False, False, "source", 13), "U7"), ("invalid-store", (False, False, "unknown", None), "U1")):
    d = RC.classify("delegated", o, f, 14)
    ccell(f"R3-01 the reviewer's carrier {o}/{f[0]}/{f[1]}/{f[2]}/{f[3]} at 13->14 is {want}", (want, lawful(o, 13, 14, f)),
          (d.row, True), asserts=(d.row, d.actions))
d = RC.classify("delegated", "future-outcome", (False, False, "unknown", None), 14)
ccell("R3-01 an outcome a later head adds, unchanged, is the fallback U7", "U7", d.row, asserts=(d.row, d.actions))


# R3-01: the reviewer's two equal-input pairs, through the model's real rung (one v13 preflight and mint, then a swap)
def swap_v17(path, b, t):
    os.remove(path)
    make(path, HEAD)
    c = sqlite3.connect(path)
    c.execute(f"PRAGMA user_version={HEAD + 1}")
    c.close()


def through_rung(fn):
    path = make(p(f"r301-pair-{next(SEQ)}"), 13)
    SWAP["fn"] = fn
    try:
        outcome, f, diag, _ = rung_once(path)
    finally:
        SWAP["fn"] = None
    return outcome, (f.store_changed, f.transaction_committed, f.resulting_state, f.resulting_version), diag


PAIRS = {"source-missing/unaccepted (an accepted v12 vs an empty replacement)": (swap_to("below"), swap_to("empty"), "U3"),
         "newer (an accepted v15 vs a v17 store)": (swap_to("above"), swap_v17, "U4")}
PAIR_IN = {}
for label, (fa, fb, want) in PAIRS.items():
    a, b_ = through_rung(fa), through_rung(fb)
    PAIR_IN[label] = (a, b_, want)
    ccell(f"R3-01 pair {label}: identical structured inputs", True, a[:2] == b_[:2], note=f"{a[:2]} / {b_[:2]}")
    ccell(f"R3-01 pair {label}: the diagnostics DIFFER (the pair is real; research B2)", True, a[2] != b_[2],
          note=f"{local(a[2])[:90]} | {local(b_[2])[:90]}")
    da, db = RC.classify("delegated", a[0], a[1], 14), RC.classify("delegated", b_[0], b_[1], 14)
    ccell(f"R3-01 pair {label}: one conservative action for both, {want}", (want, want), (da.row, db.row),
          asserts=(da.row, da.actions))


# the walk, deciding by the classifier
COUNT = {"mode": "honest"}    # R2-01's counting closure, kept as mutants: "r2" (round 2's algorithm), "twice"


def walk5(path, cls=None, count_before_binding=False):
    cls = cls or RC.classify
    expect, committed, decisions = None, [], []
    R3["n"] = 0
    while True:
        try:
            rep = run_rung_r3(path, expect)
        except ModelAuditWriteError as exc:
            f = exc.facts
            d = cls("write-error", f.outcome, (f.store_changed, f.transaction_committed, f.resulting_state,
                                                f.resulting_version), exc.rung_context[2])
            if d.counted:
                committed.append(exc.rung_context[0])
            return 3, committed, decisions + [d]
        except ModelAuditReadError:
            return 3, committed, decisions + [cls("read-error")]
        except ModelPackageEscape as exc:
            if exc.rung_context is None:
                return 3, committed, decisions + [cls("package-pre-mint")]
            rb = rm.read_terminal(exc.rung_context[0], audit_path=rm.audit_trail_path(path))
            d = cls("package-post-mint", ctx=exc.rung_context[1:], readback=rb)
            if count_before_binding:                         # THE DEFECT R3-03 named: any record's committed facts count
                d = d._replace(counted=rb.kind == "record" and klass(rb.facts.store_changed, rb.facts.transaction_committed) == "committed")
            if d.counted:
                committed.append(exc.rung_context[0])
            return 3, committed, decisions + [d]
        if rep.kind == "preflight":
            r = rep.result
            d = cls("preflight", r.outcome, (r.store_changed, r.transaction_committed, r.resulting_state, r.resulting_version))
            return (0 if d.row == "P0" else 1), committed, decisions + [d]
        if rep.kind == "unexpected-base":
            return 1, committed, decisions + [cls("unexpected-base")]
        r = rep.result
        f = None if r.outcome in RC.NO_RECORD else (r.store_changed, r.transaction_committed, r.resulting_state,
                                                    r.resulting_version)
        d = cls("delegated", r.outcome, f, rep.to_version)
        decisions.append(d)
        if (d.counted if COUNT["mode"] == "honest" else d.row == "C1"):   # "r2": counted only where the walk continues
            committed.append(rep.operation_id)
            if COUNT["mode"] == "twice":
                committed.append(rep.operation_id)
        if d.row in ("C1", "U0"):
            expect = rep.to_version
            continue
        return 1, committed, decisions


def walk_case(kind=None, facts=None, cls=None, cbb=False, base=13, tag=""):
    path = make(p(f"r3c-{kind}-{next(SEQ)}"), base)
    R3.update(at=2 if kind else None, kind=kind, facts=facts)
    try:
        code, ids_, ds = walk5(path, cls, cbb)
    finally:
        R3.update(at=None, kind=None, facts=None)
    last = ds[-1]
    return {"exit": code, "ids": len(ids_), "distinct": len(set(ids_)), "row": last.row, "actions": list(last.actions),
            "stamp": stamp_of(path)}, path


CI_FACTS = ("internal-error", True, True, "destination", 15)
WALK = {
    "an honest v13 walk": ((None, None), {"exit": 0, "ids": 3, "row": "P0", "stamp": 16}),
    "a committed error at rung 2 stops, counted once (C2)": (("override", CI_FACTS), {"exit": 1, "ids": 2, "distinct": 2, "row": "C2", "stamp": 15}),
    "a write error with committed success facts (E1, C1: resume the store)": (("write-error", None), {"exit": 3, "ids": 2, "distinct": 2, "row": "E1>C1", "stamp": 15}),
    "a terminal read error (E2), uncounted although the store is at t": (("read-error", None), {"exit": 3, "ids": 1, "row": "E2", "stamp": 15}),
    "a postcondition failure (U5): not with the same build": (("postcondition", None), {"exit": 1, "ids": 1, "row": "U5", "stamp": 14}),
}
for name, ((kind, fx), want) in WALK.items():
    got, _ = walk_case(kind, fx)
    ccell(f"R3-01 walk: {name}", want, {k: got[k] for k in want}, asserts=(got["row"], got["actions"]))

# I35 (iv): the postcondition example clears its fault BEFORE the rerun; the same-build rerun fails again
got, path = walk_case("postcondition", None, tag="i35")
R3.update(at=1, kind="postcondition", facts=None)
try:
    same = walk5(path)
finally:
    R3.update(at=None, kind=None, facts=None)
ccell("I35 (iv) the same-build rerun after a postcondition failure fails the same way (U5 again, stamp unchanged)",
      ("U5", 14), (same[2][-1].row, stamp_of(path)))
again = walk5(path)
ccell("I35 (iv) with the fault cleared (the build repaired), the rerun resumes to head", (0, 16), (again[0], stamp_of(path)))

# R3-02: four transport pairs, an ordinary record vs a MigrationAuditWriteError carrying the SAME facts
for label, row7b, fx in (("committed migrated", "C1", ("migrated", True, True, "destination", 15)), ("committed internal-error", "C2", CI_FACTS),
                         ("unchanged unsupported-migration", "U5", ("unsupported-migration", False, False, "unknown", None)),
                         ("unknown migration-failed", "K", ("migration-failed", None, None, "unknown", None))):
    ok_lawful = lawful(fx[0], 14, 15, fx[1:])
    ordi, _ = walk_case("override", fx, tag=f"ord-{label}")
    esc, _ = walk_case("write-error-facts", fx, tag=f"esc-{label}")
    o_ids = ordi["actions"] if ordi["row"] not in ("P0",) else ["continue"]
    want_store = [RC.TABLE["E1"]["resume"]] if fx[1] is True and fx[0] == "migrated" else o_ids
    ccell(f"R3-02 pair {label} ({row7b}): the escape's store-side ids equal the ordinary record's"
          f"{' (C1: the resume id)' if row7b == 'C1' else ''}, plus the disclosure",
          {"lawful": True, "store": want_store, "disclosure": RC.TABLE["E1"]["disclosure"], "esc_exit": 3, "counted_equal": True},
          {"lawful": ok_lawful, "store": esc["actions"][:-1], "disclosure": esc["actions"][-1], "esc_exit": esc["exit"],
           "counted_equal": (esc["ids"] == 2) == (fx[1] is True)}, note=f"ordinary {ordi} | escape {esc}",
          asserts=(esc["row"], esc["actions"]))

# R3-03: the package escape binds BEFORE it counts
PI_UNCOMMITTED = next((f for f in _it.product(TRI, TRI, sorted(rm._RESULTING_STATES), VERSIONS(14, 15))
                       if f[1] is not True and lawful("package-inconsistent", 14, 15, f)), None)
ccell("R3-03 a lawful package-inconsistent carrier that did not commit exists at 14->15 (the zero-count fixture)", True,
      PI_UNCOMMITTED is not None, note=str(PI_UNCOMMITTED))
PKG = {
    "a lawful package-inconsistent record at the minted rung, committed (bound, counted)":
        (lambda f, a: rm.TerminalFacts("package-inconsistent", a.from_version, a.to_version, True, True, "destination", a.to_version),
         {"ids": 2, "row": "E4", "actions": ["repair-build", "stop-inspect-committed"]}),
    "a record with another outcome (migrated: round 3's defective positive): unbound, not counted":
        (lambda f, a: f, {"ids": 1, "row": "E4", "actions": ["repair-build"]}),
    "a lawful package-inconsistent record at ANOTHER rung: unbound, not counted":
        (lambda f, a: rm.TerminalFacts("package-inconsistent", a.from_version + 1, a.to_version + 1, True, True, "destination", a.to_version + 1),
         {"ids": 1, "row": "E4", "actions": ["repair-build"]}),
    f"a bound package-inconsistent record that did not commit ({PI_UNCOMMITTED}): counts nothing":
        (lambda f, a: rm.TerminalFacts("package-inconsistent", a.from_version, a.to_version, *PI_UNCOMMITTED),
         {"ids": 1, "row": "E4", "actions": ["repair-build"]}),
}
for name, (pub, want) in PKG.items():
    got, _ = walk_case("pi-escape", pub, tag=f"pkg-{len(CLOSURE)}")
    ccell(f"R3-03 {name}", want, {k: got[k] for k in want}, asserts=(got["row"], got["actions"]))


# ---- the kill list: each rule must make at least one closure check fail ---------------------------------------------
def variant(base, **over):
    def cls(route, outcome=None, facts=None, t=None, ctx=None, readback=None):
        d = base(route, outcome, facts, t, ctx, readback)
        for key, fn in over.items():
            d = fn(route, outcome, facts, t, d) or d
        return d
    return cls


R = RC.classify
DIAG = {"now": ""}                                          # the prose a mutant may (wrongly) read


def cause_from_prose(rt, o, f, t, d):
    """THE FORBIDDEN READING (I35's mutant): a U3/U4 cause parsed out of the diagnostic text"""
    m = re.search(r"observed v(\d+)", DIAG["now"]) if d.row == "U3" else re.search(r"v(\d+) is newer", DIAG["now"]) if d.row == "U4" else None
    if not m:
        return None
    v = int(m.group(1))
    if d.row == "U3":
        return d._replace(row="U2", actions=("fix-path-then-rerun",)) if v == 0 else d._replace(row="P3", actions=("rerun-when-quiescent",))
    return d._replace(row="U5", actions=("no-rerun-this-build",)) if v > HEAD else d._replace(row="P3", actions=("rerun-when-quiescent",))


MUT = {
    "a U3/U4 cause read from the diagnostic prose (I35's mutant)": variant(R, x=cause_from_prose),
    "the blanket unchanged retry (v0.4.1's row 4, THE SUPERSEDED RULE)":
        variant(R, x=lambda rt, o, f, t, d: d._replace(row="4", actions=("rerun",)) if d.row in ("U1", "U3", "U4", "U5", "U7") else None),
    "the same-build postcondition retry (U5 -> rerun)":
        variant(R, x=lambda rt, o, f, t, d: d._replace(actions=("rerun",)) if d.row == "U5" else None),
    "an escape weaker than its facts (E1 with a committed error -> resume the store)":
        variant(R, x=lambda rt, o, f, t, d: d._replace(actions=(RC.TABLE["E1"]["resume"], RC.TABLE["E1"]["disclosure"])) if d.row == "E1>C2" else None),
    "zero ids for one input (U7)": variant(R, x=lambda rt, o, f, t, d: d._replace(actions=()) if d.row == "U7" else None),
    "two rows' ids for one input (U3 and U4)":
        variant(R, x=lambda rt, o, f, t, d: d._replace(actions=d.actions + tuple(RC.TABLE["U4"]["actions"])) if d.row == "U3" else None),
    "round 2's no-record routing (every no-record outcome but audit-state-unknown -> rerun; research B2)":
        variant(R, x=lambda rt, o, f, t, d: d._replace(row="N1", actions=("rerun",)) if d.row in ("N3", "N4") else None),
    "a committed error continuing (C2 -> continue; research B2)":
        variant(R, x=lambda rt, o, f, t, d: d._replace(row="C1", actions=("continue",)) if d.row == "C2" else None),
}


def failures(cls, cbb=False):
    """re-run every closure check under a classifier (and the count-before-binding walk); the names that differ"""
    out = []
    b_, _ = oracle(cls)
    if b_:
        out.append("oracle")
    for o, f, want in (("internal-error", (False, False, "source", 13), "U7"), ("invalid-store", (False, False, "unknown", None), "U1")):
        if cls("delegated", o, f, 14).row != want:
            out.append(f"carrier {o}")
    for label, (a, b2, want) in PAIR_IN.items():
        DIAG["now"] = a[2]
        da = cls("delegated", a[0], a[1], 14)
        DIAG["now"] = b2[2]
        db = cls("delegated", b2[0], b2[1], 14)
        DIAG["now"] = ""
        if (da.row, db.row) != (want, want) or tuple(da.actions) != expected_ids(want) or tuple(db.actions) != expected_ids(want):
            out.append(f"pair {label}")
    for name, ((kind, fx), want) in WALK.items():
        got, _ = walk_case(kind, fx, cls, tag="mut")
        if {k: got[k] for k in want} != want or tuple(got["actions"]) != expected_ids(got["row"]):
            out.append(f"walk {name}")
    for name, (pub, want) in PKG.items():
        got, _ = walk_case("pi-escape", pub, cls, cbb, tag="mut")
        if {k: got[k] for k in want} != want:
            out.append(f"pkg {name}")
    return out


ccell("the honest classifier passes every closure check (the kill list's baseline)", [], failures(R))
for name, cls in MUT.items():
    f = failures(cls)
    ccell(f"mutant killed: {name}", True, bool(f), note=f"fails: {f[:4]}")
f = failures(R, cbb=True)
ccell("mutant killed: count before binding (R3-03's defect: any record's committed facts count)", True, bool(f), note=f"fails: {f[:4]}")
# R2-01's counting closure (closed by round 3), kept as regression mutants on the new walk
for mode, what in (("r2", "round 2's walk, counting only where the walk continues (R2-01's SUPERSEDED IMPLEMENTATION)"),
                   ("twice", "an id counted twice")):
    COUNT["mode"] = mode
    try:
        f = failures(R)
    finally:
        COUNT["mode"] = "honest"
    ccell(f"mutant killed: {what}", True, bool(f), note=f"fails: {f[:4]}")
ccell("mutant killed: rerun keyed on 'a version is known', not on the stopping row", True,
     bool(failures(variant(R, x=lambda rt, o, f, t, d: d._replace(actions=("rerun",)) if f and f[3] is not None and d.row not in ("C1", "U0") and not d.row.startswith("P") else None))))
inexpressible("R2-01 mutant: row 10 printing the derived state in the version column",
              "a decision carries ids, not a printed version: E2 (`inspect-audit-trail`) prints `unknown` by its row, and no "
              "classifier path can put a state there; the printing is the CLI's, owed at implementation (I35)")


# ---- R2-02: one guarded table, plan(b, t) for both routes, the trace and kind attribution -----------------------------
SRC = pathlib.Path(m.__file__).read_text()
AF = next(n for n in _ast.parse(SRC).body if isinstance(n, _ast.FunctionDef) and n.name == "_apply_forward")


def parse_guard(test):
    """`[lo <=] base < v <= SCHEMA_VERSION` -> (lo, v); `base >= k` -> ('nested', k); else None"""
    if isinstance(test, _ast.Compare):
        names = [test.left] + test.comparators
        txt = [_ast.unparse(x) for x in names]
        ops = [type(o).__name__ for o in test.ops]
        if txt[-2:] and txt[-1] == "SCHEMA_VERSION" and "base" in txt:
            i = txt.index("base")
            lo = int(txt[0]) if i == 1 and ops[0] == "LtE" else 0
            v = int(txt[i + 1])
            if ops[i] == "Lt" and ops[-1] == "LtE" and len(txt) == i + 3:
                return (lo, v)
        if txt[0] == "base" and ops == ["GtE"] and len(txt) == 2:
            return ("nested", int(txt[1]))
    return None


def entries_of(body, guard, out):
    for st in body:
        if isinstance(st, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            continue
        if isinstance(st, _ast.Expr) and isinstance(st.value, _ast.Constant) and isinstance(st.value.value, str):
            continue                                    # a docstring: never dispatched
        if isinstance(st, _ast.With):                   # the site wrapper (_SITE_MIGRATION_VERSION.consult()) holds the body
            entries_of(st.body, guard, out)
            continue
        g = parse_guard(st.test) if isinstance(st, _ast.If) and not st.orelse else None
        if g and g[0] == "nested" and guard is not None:
            entries_of(st.body, (max(guard[0], g[1]), guard[1]), out)
        elif g and g[0] != "nested" and guard is None:
            entries_of(st.body, g, out)
        else:
            out.append({"line": st.lineno, "guard": guard, "src": _ast.unparse(st).splitlines()[0][:80]})
    return out


ENTRIES = entries_of(AF.body, None, [])
GUARDS = sorted({tuple(e["guard"]) for e in ENTRIES if e["guard"]})
emit({"R2-02 the guard table's guards, from the pin's AST": [list(g) for g in GUARDS]})
cell("R2-02 the eight step guards and the two nested bounds are (lo, v) guards",
     [[0, 3], [0, 4], [0, 5], [0, 13], [0, 16], [2, 16], [4, 6], [4, 10], [6, 8], [15, 16]], [list(g) for g in GUARDS])


def plan(b, t, entries=None):
    return [e["line"] for e in (entries or ENTRIES) if e["guard"] is None or (e["guard"][0] <= b < e["guard"][1] <= t)]


WRITE_CLASS = {sqlite3.SQLITE_INSERT: "data", sqlite3.SQLITE_UPDATE: "data", sqlite3.SQLITE_DELETE: "data",
               sqlite3.SQLITE_ALTER_TABLE: "alter", sqlite3.SQLITE_PRAGMA: "pragma"}
for _n in dir(sqlite3):
    if _n.startswith("SQLITE_CREATE_") or _n.startswith("SQLITE_DROP_"):
        WRITE_CLASS[getattr(sqlite3, _n)] = "add" if _n.startswith("SQLITE_CREATE_") else "drop"


def observe(b, t, fn=None, *, populated=0, direct_concat=False):
    """run the kernel's forward step b -> t under a patched head on a fresh store; return (trace of entry lines, writes
    [(entry line, class, sql)], clock reads, stamps). statement caching is OFF so every statement is prepared (and so
    classified) where it runs (0048 round 4's lesson)."""
    path = make(p(f"r202-{b}-{t}-{populated}-{id(fn)}-{direct_concat}"), b)
    if populated:
        c = sqlite3.connect(path, isolation_level=None)
        c.execute("DELETE FROM episodes")
        for i in range(populated):
            r = legacy_row() | {"id": f"episode-{i + 1}", "edge_id": f"edge-{i + 1}"}
            c.execute("INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                      (r["id"], r["user_id"], r["date"], json.dumps(r)))
        c.close()
    lines_ = {e["line"] for e in ENTRIES}
    trace, writes, pending, clocks = [], [], [], [0]
    target = fn or m._apply_forward

    def tracer(frame, event, arg):
        if frame.f_code.co_name != "_apply_forward":
            return None
        def local_(fr, ev, a):
            if ev == "line" and fr.f_lineno in lines_ and (not trace or trace[-1] != fr.f_lineno):
                trace.append(fr.f_lineno)
            return local_
        return local_

    def auth(action, a1, a2, db, src):
        if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE) and \
                a1 in ("sqlite_master", "sqlite_temp_master", "sqlite_schema"):
            return sqlite3.SQLITE_OK                  # SQLite's own schema bookkeeping for a CREATE or an ALTER
        cls = WRITE_CLASS.get(action)
        if cls == "pragma":
            cls = "stamp" if (a1 == "user_version" and a2 is not None) else None
        if cls:
            pending.append(cls)
        return sqlite3.SQLITE_OK

    def tcb(sql):
        if pending:
            writes.append((trace[-1] if trace else None, sorted(set(pending)), " ".join(sql.split())))
            pending.clear()

    orig_clock = m._clock
    m._clock = lambda: (clocks.__setitem__(0, clocks[0] + 1), orig_clock())[1]
    c = sqlite3.connect(path, isolation_level=None, cached_statements=0)
    c.set_authorizer(auth)
    c.set_trace_callback(tcb)
    sys.settrace(tracer)
    try:
        c.execute("BEGIN IMMEDIATE")
        if direct_concat:
            for bb in range(b, t):
                with head(bb + 1):
                    target(c, bb)
        else:
            with head(t):
                target(c, b)
        c.execute("COMMIT")
    finally:
        sys.settrace(None)
        m._clock = orig_clock
        c.close()
    stamps = [w for w in writes if w[1] == ["stamp"]]
    return trace, writes, clocks[0], [s[2] for s in stamps]


# the frozen table's kinds: observed at the pin across every route; one kind per entry, or the entry is MIXED
KIND = {e["line"]: set() for e in ENTRIES}
runs = [(b, b + 1) for b in range(FIRST, HEAD)] + [(b, HEAD) for b in range(FIRST, HEAD - 1)]
OBS = {}
for b, t in runs:
    OBS[(b, t)] = observe(b, t)
POP = {n: observe(2, 3, populated=n) for n in (0, 1, 2)}      # the populated v2 fixtures (legacy outcome rows)
for obs in list(OBS.values()) + list(POP.values()):
    for ln, cls, _ in obs[1]:
        if ln in KIND:
            KIND[ln].update(cls)
emit({"R2-02 the kinds' bound": "each entry's kind is the write class OBSERVED on the model's fixtures (every route on "
      "empty stores, plus 2->3 on 0/1/2 legacy rows); an entry that writes only on data these fixtures lack reads as "
      "zero-write here. The implementation's table DECLARES kinds; this model checks them on its fixtures only."})
mixed = {ln: sorted(k) for ln, k in KIND.items() if len(k) > 1}
cell("R2-02 every entry of the table is single-kind at the pin (a mixed block is split by statement)", {}, mixed)
for e in ENTRIES:
    e["kind"] = (sorted(KIND[e["line"]]) or ["none"])[0]
emit({"R2-02 FORWARD_ENTRIES (derived at the pin)": [{k: e[k] for k in ("line", "guard", "kind", "src")} for e in ENTRIES]})


def violations(obs, b, t, entries=None):
    ents = entries or ENTRIES
    kind = {e["line"]: e["kind"] for e in ents}
    trace, writes = obs[0], obs[1]
    v = []
    if trace != plan(b, t, ents):
        v.append("trace != plan")
    for ln, cls, sql in writes:
        if ln is None or ln not in kind:
            v.append(f"write with no active entry: {sql}")
        elif any(c != kind[ln] for c in cls):
            v.append(f"entry L{ln} ({kind[ln]}) issued {cls}: {sql}")
    return v


bad = {f"{b}->{t}": violations(OBS[(b, t)], b, t) for b, t in runs}
bad = {k: x for k, x in bad.items() if x}
cell(f"R2-02 the step-invocation trace equals plan(b, t), and every write is admitted by its entry's kind, on all "
     f"{len(runs)} routes (every rung, and the direct route from every base)", {}, bad)

# 0/1/2 legacy outcome rows: 0, 1, 2 writes under ONE data entry (the reviewer's data-step-write-cardinality)
counts = []
for n_rows in (0, 1, 2):
    tr, wr, _, _ = POP[n_rows]
    per = {}
    for ln, cls, sql in wr:
        if cls == ["data"] and sql.startswith("UPDATE episodes"):
            per[ln] = per.get(ln, 0) + 1
    counts.append((n_rows, sorted(per.items()), violations((tr, wr), 2, 3)))
cell("R2-02 0, 1 and 2 legacy rows give 0, 1 and 2 UPDATE episodes writes under one data entry, each admitted",
     {"writes": [0, 1, 2], "entries": [[], [1], [1]], "violations": [[], [], []]},
     {"writes": [sum(c for _, c in x[1]) for x in counts], "entries": [[1] * len(x[1]) for x in counts],
      "violations": [x[2] for x in counts]}, note=local(counts)[:300])

# the reviewer's direct-versus-adjacent witness, under the table
d_tr, d_wr, d_clock, d_stamps = OBS[(1, HEAD)]
a_alter = a_clock = 0
a_stamps = []
for b in range(1, HEAD):
    tr, wr, ck, st = OBS[(b, b + 1)]
    a_alter += sum(1 for _, cls, _ in wr if cls == ["alter"]); a_clock += ck; a_stamps += st
d_alter = sum(1 for _, cls, _ in d_wr if cls == ["alter"])
def conf(wr):
    return [s for _, c, s in wr if c == ["add"] and s.startswith("CREATE TABLE") and " confirmations" in s.split("(")[0]]
ddl = lambda v: [" ".join(o.ddl.split()) for o in sv.SCHEMAS[v] if o.key == ("table", "confirmations")]
a_conf = []
for b in range(1, HEAD):
    a_conf += conf(OBS[(b, b + 1)][1])
cell("R2-02 the direct route uses the DESTINATION constructor of confirmations; the adjacent walk the v2 one",
     {"direct": ddl(HEAD), "adjacent": ddl(2)}, {"direct": conf(d_wr), "adjacent": a_conf})
cell("R2-02 direct base 1 -> 16: 0 ALTERs, one clock read, one stamp (the pin's contract, under plan(1, 16))",
     {"alter": 0, "clock": 1, "stamps": 1}, {"alter": d_alter, "clock": d_clock, "stamps": len(d_stamps)})
cell("R2-02 adjacent 1 -> 16: 14 ALTERs, 15 clock reads, 15 stamps",
     {"alter": 14, "clock": 15, "stamps": 15}, {"alter": a_alter, "clock": a_clock, "stamps": len(a_stamps)})


# I36's closure mutants, each on an edited COPY of the pin's _apply_forward (no source file is touched); each must
# produce a violation against the frozen table
def mutated(edit):
    tree = _ast.parse(SRC)
    fn = next(n for n in tree.body if isinstance(n, _ast.FunctionDef) and n.name == "_apply_forward")
    edit(fn)
    _ast.fix_missing_locations(tree)
    # compiled into the module's OWN namespace, so the head patch reaches it; the original is restored at once
    orig = m._apply_forward
    exec(compile(_ast.Module(body=[fn], type_ignores=[]), m.__file__, "exec"), m.__dict__)
    mutant, m._apply_forward = m._apply_forward, orig
    return mutant


def find_stmt(fn, line):
    for node in _ast.walk(fn):
        for field in ("body", "orelse"):
            seq = getattr(node, field, None)
            if isinstance(seq, list):
                for i, st in enumerate(seq):
                    if getattr(st, "lineno", None) == line:
                        return seq, i
    raise KeyError(line)


def stmt(src, line):
    s = _ast.parse(src).body[0]
    for n in _ast.walk(s):
        if hasattr(n, "lineno"):
            n.lineno = n.end_lineno = line
    return s


checks = [e for e in ENTRIES if e["kind"] == "none" and "_edges_unchanged" in e["src"]]
datas = [e for e in ENTRIES if e["kind"] == "data"]
first_check = next(e for e in ENTRIES if e["kind"] == "none" and e["guard"] == (0, 3))
adj = next(((x, y) for x, y in zip(ENTRIES, ENTRIES[1:]) if x["guard"] is not None and x["guard"] == y["guard"]
            and "data" in (x["kind"], y["kind"])), None)

def ins_after(line, src):
    def ed(fn):
        seq, i = find_stmt(fn, line); seq.insert(i + 1, stmt(src, 9000 + line))
    return ed

def delete(line):
    def ed(fn):
        seq, i = find_stmt(fn, line); seq[i] = stmt("pass", 9500 + line)
    return ed

def widen(v_from, v_to):
    def ed(fn):
        hits = [st for st in _ast.walk(fn) if isinstance(st, _ast.If) and parse_guard(st.test)
                and parse_guard(st.test)[0] != "nested" and parse_guard(st.test)[1] == v_from]
        assert len(hits) == 1, f"widen: {len(hits)} guards with v={v_from}"   # a mutator asserts its anchor
        cs = [c for c in hits[0].test.comparators if isinstance(c, _ast.Constant) and c.value == v_from]
        assert len(cs) == 1
        cs[0].value = v_to
    return ed

def swap(l1, l2):
    def ed(fn):
        s1, i = find_stmt(fn, l1); s2, j = find_stmt(fn, l2); s1[i], s2[j] = s2[j], s1[i]
    return ed

MUT = [("an undeclared write (after a check entry)", ins_after(first_check["line"], 'conn.execute("UPDATE episodes SET json = json WHERE 0")'), (2, 3)),
       ("an undeclared dispatch (the v4 block's guard widened to base < 5)", widen(4, 5), (4, 5)),
       ("a nested check deleted (the first _edges_unchanged)", delete(checks[0]["line"]), (15, 16)),
       ("one repeated v16 check deleted (the last _edges_unchanged)", delete(checks[-1]["line"]), (15, 16)),
       ("a data entry issuing DDL", ins_after(datas[0]["line"], 'conn.execute("CREATE TABLE model_plant(x)")'),
        (datas[0]["guard"][1] - 1, datas[0]["guard"][1]))]
if adj:
    MUT.append((f"a data step swapped with its neighbour (L{adj[0]['line']} <-> L{adj[1]['line']})", swap(adj[0]["line"], adj[1]["line"]),
                (adj[0]["guard"][1] - 1, adj[0]["guard"][1])))
else:
    inexpressible("R2-02 mutant: two adjacent data steps swapped",
                  "no two data entries are adjacent under one guard at the pin; a swap across guards is the dispatch mutant")
for label, edit, (b, t) in MUT:
    try:
        obs = observe(b, t, mutated(edit))
        v = violations(obs, b, t)
    except Exception as exc:                            # a mutant the kernel itself refuses also fails the operation
        v = [f"refused: {type(exc).__name__}"]
    cell(f"R2-02 mutant detected: {label}", True, bool(v), note=str(v[:2]))
obs = observe(1, HEAD, direct_concat=True)
cell("R2-02 mutant detected: the direct route rebuilt as the concatenation of adjacent plans", True,
     bool(violations(obs, 1, HEAD)), note=f"ALTERs {sum(1 for _, c, _ in obs[1] if c == ['alter'])}, clock reads {obs[2]}")
# a mis-split entry (a table mutant): the first ALTER loop filed under a data entry's kind
alt = next(e for e in ENTRIES if e["kind"] == "alter")
merged = [dict(e, kind="data") if e is alt else e for e in ENTRIES]
b, t = alt["guard"][1] - 1, alt["guard"][1]
cell(f"R2-02 table mutant detected: the ALTER loop at L{alt['line']} filed under the data kind", True,
     bool(violations(OBS[(b, t)], b, t, merged)))
n_ok = sum(1 for r in RESULTS if r is True)
n_bad = sum(1 for r in RESULTS if r is False)
n_inx = sum(1 for r in RESULTS if r is None)
emit({"summary": {"ok": n_ok, "not_ok": n_bad, "inexpressible": n_inx}})
sys.exit(1 if n_bad else 0)
