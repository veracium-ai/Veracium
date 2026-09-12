"""`veracium doctor` — a no-LLM, read-only static linter for a store file.

    veracium doctor --db veracium.db              # every user
    veracium doctor --db veracium.db --user ida   # one user's rows
    veracium doctor --db veracium.db --json       # machine-readable

Why it exists (the developer-tools backlog, item 5, endorsed 2026-08-30 and
started on Quentin's word 2026-09-12): the selfcheck needs a provider, so a
host's first touch of a store had nothing to run; and the store's own
invariants — the version stamp, the singleton identity, the journal, the
supersession links, the ledger's references, the revocation sweep's
completeness — were checked at write time by the code that wrote them and
never again by anything that only READS.

What it does: copies the file into a private temporary directory and opens
THE COPY through the store's own constructor — never the original, and never
a connection of its own. Both halves are deliberate. The original is not
touched (not even the lock or journal the constructor's `BEGIN IMMEDIATE`
would take), so the report is a snapshot and the bytes on disk are provably
the same before and after. And specs/0031 §4b-ii pins every file-backed
`sqlite3.connect` site under src/ to an inventory whose criterion allows no
third class — a linter with its own opener would be a new site owed the
factory — so the doctor goes through the one blessed door and lets its typed
refusals (below head, above head, unstamped, not a database) BECOME the
findings. Then SQLite's own `quick_check`, then every table it knows. It
repairs nothing and never will: `veracium migrate` is the version path, and a
dangling reference is a fact an operator must see before anyone rewrites a
row (specs/0009: outcome history is append-only; specs/0022: retirement is a
recorded action, never a silent edit).

The copy costs one read of the file. A store under concurrent writes yields a
snapshot of whatever bytes were on disk; `quick_check` says whether that
snapshot is consistent. Run it against a quiesced store to lint the store
rather than a moment of it.

The checks, each named in the output:

  file          the path exists, its copy is a database the constructor can
                read, quick_check ok
  version       the constructor's own verdict on the copy — below head
                (migrate offline), above head (this build cannot read it),
                unstamped/foreign (a legacy base; adoption is disabled here)
                — reported verbatim; at head, `store_epoch` and the
                `store_identity` singleton present exactly once
  objects       every REQUIRED object of the stated version present on the
                snapshot. REBUILDABLE drift (a dropped or altered index) is
                NOT observable here: the constructor rebuilds it on open, by
                specs/0007's policy, so the copy the doctor reads is already
                repaired — and the original is untouched
  rows          every `edges`/`episodes` JSON parses; its `id`/`user_id`
                equal the row columns; the `active` column agrees with the
                payload's `invalidated_at`; `quarantined` agrees with the
                payload's disclosure; a retired edge carries a reason from the
                dispositioned vocabulary
  refs          `supersedes` names an existing edge of the same user; the
                chain has no cycle; a superseded predecessor is retired;
                outcome episodes, confirmations, ledger survivors and typed
                contributors, embeddings and journal events all name rows
                that exist
  journal       every edge has at least one journal event (specs/0029: a row
                with no `created`/`baseline` event was written outside the
                journal)
  revocation    for every standing revocation (specs/0022), the reference
                sweep over the store AS IT IS has no pending effect — the
                sweep is the same pure function the commit path runs, called
                with no proposed action (its `complete` flag, the §4c blind-
                spot count that over-reports by design, is not a finding here)
  runtime       this interpreter's SQLite is a qualified runtime for the
                store (specs/0007's predicate); informational

Exit codes: 0 clean, 1 findings, 2 the file could not be read at all.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import tempfile
from dataclasses import asdict, dataclass, field
from typing import Optional

from .store import schema_version as sv

MAX_IDS = 20   # ids listed per finding in the text form; the JSON form carries all


@dataclass
class Finding:
    check: str
    level: str            # "error" | "warn" | "info"
    message: str
    ids: list = field(default_factory=list)


@dataclass
class Report:
    db: str
    readable: bool
    user_version: Optional[int] = None
    head_version: int = sv.SCHEMA_VERSION
    users: list = field(default_factory=list)
    counts: dict = field(default_factory=dict)
    checks_run: list = field(default_factory=list)
    findings: list = field(default_factory=list)

    def add(self, check: str, level: str, message: str, ids=()) -> None:
        self.findings.append(Finding(check, level, message, sorted(set(ids))))

    @property
    def exit_code(self) -> int:
        if not self.readable:
            return 2
        return 1 if any(f.level in ("error", "warn") for f in self.findings) else 0


# ----------------------------------------------------------------- opening --
_FOUND = re.compile(r"found=(\d+)|stamped v(\d+)")


def _open_snapshot(rep: Report, path: str, tmpdir: str):
    """Copy the file and open the copy through the store's constructor with
    adoption disabled. Returns the store, or None with the refusal recorded:
    a version refusal is a READABLE outcome (exit 1, the operator's next step
    is named); a file that is not a database is not (exit 2)."""
    rep.checks_run.append("file")
    if not os.path.exists(path):
        rep.add("file", "error", f"no such file: {path}")
        return None
    copy = os.path.join(tmpdir, "snapshot.db")
    shutil.copy2(path, copy)
    from .store.sqlite import SqliteStore
    try:
        store = SqliteStore(copy, allow_adopt=False)
    except sv.StoreVersionError as ex:                 # unstamped/foreign, or above head
        rep.readable = True
        rep.checks_run.append("version")
        m = _FOUND.search(str(ex))
        rep.user_version = int(m.group(1) or m.group(2)) if m else None
        rep.add("version", "error", f"the store constructor refuses this file: {ex}")
        return None
    except sv.PackageConsistencyError as ex:           # stamped below head
        rep.readable = True
        rep.checks_run.append("version")
        m = _FOUND.search(str(ex))
        rep.user_version = int(m.group(1) or m.group(2)) if m else None
        rep.add("version", "error", f"below this build's head — migrate offline first "
                f"(`veracium migrate --db X --i-have-quiesced --backup REF`): {ex}")
        return None
    except sqlite3.DatabaseError as ex:
        rep.add("file", "error", f"not a readable SQLite database: {ex}")
        return None
    conn = store._conn                                 # the package's own convention (revocation.project_store)
    conn.row_factory = sqlite3.Row
    qc = conn.execute("PRAGMA quick_check").fetchone()[0]
    if qc != "ok":
        rep.add("file", "error", f"SQLite quick_check on the snapshot: {qc}")
        store.close()
        return None
    rep.readable = True
    return store


def _tables(conn) -> set:
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


# ------------------------------------------------------------------ checks --
def _check_version(rep: Report, conn) -> Optional[int]:
    """At head by construction (the constructor accepted the copy); the
    singleton and the epoch are the checks that remain."""
    rep.checks_run.append("version")
    v = conn.execute("PRAGMA user_version").fetchone()[0]
    rep.user_version = v
    tables = _tables(conn)
    if "store_identity" in tables:
        rows = conn.execute("SELECT id, origin FROM store_identity").fetchall()
        if len(rows) != 1 or not rows[0]["origin"]:
            rep.add("version", "error", f"store_identity singleton: {len(rows)} row(s) "
                    "(specs/0006 §4.2 requires exactly one, with a minted origin)")
    elif v >= 5:
        rep.add("version", "error", "store_identity table missing at a version that requires it")
    if "store_epoch" in tables:
        rows = conn.execute("SELECT id, started_at, schema_at FROM store_epoch").fetchall()
        if len(rows) != 1:
            rep.add("version", "error", f"store_epoch: {len(rows)} row(s) (exactly one expected)")
        elif rows[0]["schema_at"] > v:
            rep.add("version", "error", f"store_epoch.schema_at {rows[0]['schema_at']} is above "
                    f"the stamped version {v}")
    elif v >= 13:
        rep.add("version", "error", "store_epoch table missing at a version that requires it")
    return v


def _check_objects(rep: Report, conn, v: int) -> None:
    rep.checks_run.append("objects")
    if v not in sv.SCHEMAS:
        rep.add("objects", "info", f"v{v} is not a version this build declares; object check skipped")
        return
    objs = sv.manifest(conn)
    declared = sv.SCHEMAS[v]
    missing_required = [o.key for o in declared if o.policy == sv.REQUIRED and o.key not in objs]
    if missing_required:
        rep.add("objects", "error", f"{len(missing_required)} REQUIRED object(s) of v{v} missing "
                "(specs/0007: absence is damage, not drift)", [f"{k[0]}:{k[1]}" for k in missing_required])
    # REBUILDABLE drift is not checked: the constructor already rebuilt it on the
    # copy (specs/0007: a rebuildable object is restored at open, never reported),
    # so `sv.drift` here would only ever measure the repair, not the store.


def _load_rows(rep: Report, conn, user: Optional[str]) -> tuple:
    """Parse every edge and episode once; report the parse-level findings."""
    rep.checks_run.append("rows")
    from .schema import DISPOSITIONED_REASONS
    where, args = ("WHERE user_id=?", (user,)) if user else ("", ())
    edges, bad = {}, []
    for r in conn.execute(f"SELECT id, user_id, active, quarantined, json FROM edges {where}", args):
        try:
            d = json.loads(r["json"])
        except ValueError:
            bad.append(r["id"]); continue
        edges[(r["user_id"], r["id"])] = (dict(r), d)
    if bad:
        rep.add("rows", "error", f"{len(bad)} edge row(s) whose JSON does not parse", bad)
    mism, active_m, quar_m, reason_m = [], [], [], []
    for (uid, eid), (row, d) in edges.items():
        if d.get("id") != eid or d.get("user_id") != uid:
            mism.append(eid)
        retired = d.get("invalidated_at") is not None
        if bool(row["active"]) == retired:
            active_m.append(eid)
        disc = (d.get("provenance") or {}).get("disclosure")
        if bool(row["quarantined"]) != (disc == "quarantined"):
            quar_m.append(eid)
        if retired and d.get("invalidation_reason") not in DISPOSITIONED_REASONS:
            reason_m.append(eid)
    if mism:
        rep.add("rows", "error", f"{len(mism)} edge payload(s) whose id/user_id differ from the row columns", mism)
    if active_m:
        rep.add("rows", "error", f"{len(active_m)} edge row(s) whose `active` column disagrees with the "
                "payload's `invalidated_at`", active_m)
    if quar_m:
        rep.add("rows", "error", f"{len(quar_m)} edge row(s) whose `quarantined` column disagrees with the "
                "payload's disclosure", quar_m)
    if reason_m:
        rep.add("rows", "error", f"{len(reason_m)} retired edge(s) whose invalidation_reason is outside "
                "the dispositioned vocabulary", reason_m)
    episodes, bad = {}, []
    for r in conn.execute(f"SELECT id, user_id, json FROM episodes {where}", args):
        try:
            d = json.loads(r["json"])
        except ValueError:
            bad.append(r["id"]); continue
        if d.get("id") != r["id"] or d.get("user_id") != r["user_id"]:
            bad.append(r["id"]); continue
        episodes[(r["user_id"], r["id"])] = d
    if bad:
        rep.add("rows", "error", f"{len(bad)} episode row(s) whose JSON does not parse or whose "
                "id/user_id differ from the row columns", bad)
    return edges, episodes


def _check_refs(rep: Report, conn, user: Optional[str], edges: dict, episodes: dict) -> None:
    rep.checks_run.append("refs")
    where, args = ("WHERE user_id=?", (user,)) if user else ("", ())
    # supersedes: the target exists for the same user; no cycles; predecessor retired
    dangling, unretired = [], []
    for (uid, eid), (row, d) in edges.items():
        pred = d.get("supersedes")
        if not pred:
            continue
        if (uid, pred) not in edges:
            dangling.append(eid)
        elif edges[(uid, pred)][1].get("invalidated_at") is None and d.get("invalidated_at") is None:
            unretired.append(eid)
    if dangling:
        rep.add("refs", "error", f"{len(dangling)} edge(s) whose `supersedes` names an edge that does "
                "not exist for that user (dangling supersession link)", dangling)
    if unretired:
        rep.add("refs", "warn", f"{len(unretired)} active edge(s) whose predecessor is still active "
                "(a supersession that did not retire what it superseded)", unretired)
    cycles = []
    for (uid, eid), (row, d) in edges.items():
        seen, cur = {eid}, d.get("supersedes")
        while cur and (uid, cur) in edges:
            if cur in seen:
                cycles.append(eid); break
            seen.add(cur); cur = edges[(uid, cur)][1].get("supersedes")
    if cycles:
        rep.add("refs", "error", f"{len(cycles)} edge(s) on a supersession CYCLE", cycles)
    # outcome episodes name an edge
    orphan_out = [eid_ for (uid, eid_), d in episodes.items()
                  if d.get("kind") == "outcome" and (uid, d.get("edge_id")) not in edges]
    if orphan_out:
        rep.add("refs", "error", f"{len(orphan_out)} outcome episode(s) naming an edge that does not "
                "exist (specs/0009 history without its subject)", orphan_out)
    # confirmations
    ids = [r["id"] for r in conn.execute(f"SELECT id, user_id, edge_id FROM confirmations {where}", args)
           if (r["user_id"], r["edge_id"]) not in edges]
    if ids:
        rep.add("refs", "error", f"{len(ids)} confirmation(s) naming an edge that does not exist", ids)
    # contribution ledger: survivors and typed contributors
    bad_surv, bad_contrib = [], []
    for r in conn.execute(f"SELECT id, user_id, survivor_type, survivor_id, contributor_type, "
                          f"contributor_ref FROM contribution_ledger {where}", args):
        pool = edges if r["survivor_type"] == "edge" else episodes
        if (r["user_id"], r["survivor_id"]) not in pool:
            bad_surv.append(r["id"])
        if r["contributor_type"] and r["contributor_ref"]:
            cpool = edges if r["contributor_type"] == "edge" else episodes
            if (r["user_id"], r["contributor_ref"]) not in cpool:
                bad_contrib.append(r["id"])
    if bad_surv:
        rep.add("refs", "error", f"{len(bad_surv)} ledger row(s) whose survivor does not exist", bad_surv)
    if bad_contrib:
        rep.add("refs", "error", f"{len(bad_contrib)} ledger row(s) whose typed contributor does not "
                "exist", bad_contrib)
    # embeddings
    ids = [r["edge_id"] for r in conn.execute(f"SELECT DISTINCT edge_id, user_id FROM edge_embedding {where}", args)
           if (r["user_id"], r["edge_id"]) not in edges]
    if ids:
        rep.add("refs", "warn", f"{len(ids)} embedding(s) for an edge that does not exist", ids)
    # journal events name an edge
    ids = [r["edge_id"] for r in conn.execute(f"SELECT DISTINCT edge_id, user_id FROM edge_event {where}", args)
           if (r["user_id"], r["edge_id"]) not in edges]
    if ids:
        rep.add("refs", "error", f"{len(ids)} journaled edge id(s) with no row (specs/0029: the journal "
                "outlived its subject, or a row was deleted outside `forget`)", ids)


def _check_journal(rep: Report, conn, user: Optional[str], edges: dict) -> None:
    rep.checks_run.append("journal")
    where, args = ("WHERE user_id=?", (user,)) if user else ("", ())
    journaled = {(r["user_id"], r["edge_id"]) for r in
                 conn.execute(f"SELECT DISTINCT user_id, edge_id FROM edge_event {where}", args)}
    silent = [eid for key, (row, d) in edges.items() if key not in journaled for eid in [key[1]]]
    if silent:
        rep.add("journal", "warn", f"{len(silent)} edge(s) with no journal event (specs/0029: written "
                "outside the journal, or a pre-epoch row the migration did not baseline)", silent)


def _check_revocation(rep: Report, store, users: list) -> None:
    """The reference sweep, called with NO proposed action, over each user's
    standing revocations: its effect list is the delta between the store as it
    is and the state the standing set requires. Non-empty = not applied."""
    rep.checks_run.append("revocation")
    from .store import revocation as rv
    from .store import revocation_sweep as sw
    if True:
        for uid in users:
            standing = store.standing_revocations(uid)
            if not standing:
                continue
            projection = rv.project_store(store, uid)
            for digest in sorted(standing):
                st = sw.sweep(projection, digest)
                effects = st.get("effects") or []
                if effects:
                    rep.add("revocation", "error",
                            f"user {uid!r}: revocation {digest[:16]}… is NOT APPLIED — the sweep still "
                            f"has {len(effects)} pending effect(s) against the store as it is "
                            f"(specs/0022 §4e)", [str(e.get("id")) for e in effects][:200])
                # the statement's `complete` flag is NOT read here: it is the sweep's
                # blind-spot signal about the contributor graph (0022 §4c class (c)),
                # which over-reports BY DESIGN — every plain fact that never combined
                # with anything counts — so it is false on almost every store and says
                # nothing about whether the revocation was applied. `effects` does.


def _check_runtime(rep: Report) -> None:
    rep.checks_run.append("runtime")
    try:
        ok = sv.runtime_supported()
    except Exception as ex:                                   # noqa: BLE001
        ok, why = False, type(ex).__name__
    else:
        why = None
    if not ok:
        rep.add("runtime", "info", "this interpreter's SQLite is not a qualified runtime for the store "
                "(specs/0007's recorded-runtime predicate)" + (f": {why}" if why else ""))


# ------------------------------------------------------------------- driver --
def diagnose(path: str, *, user: Optional[str] = None) -> Report:
    rep = Report(db=path, readable=False)
    tmpdir = tempfile.mkdtemp(prefix="veracium-doctor-")
    try:
        store = _open_snapshot(rep, path, tmpdir)
        if store is None:
            if rep.readable:
                rep.add("revocation", "info", "row-level checks and revocation completeness skipped: "
                        "the constructor refused the snapshot (see the version finding)")
            return rep
        try:
            conn = store._conn
            v = _check_version(rep, conn)
            _check_objects(rep, conn, v)
            users = [r[0] for r in conn.execute("SELECT DISTINCT user_id FROM edges UNION "
                                                "SELECT DISTINCT user_id FROM episodes")]
            rep.users = [user] if user else sorted(users)
            edges, episodes = _load_rows(rep, conn, user)
            rep.counts = {"edges": len(edges), "episodes": len(episodes),
                          "active_edges": sum(1 for (_r, d) in edges.values()
                                              if d.get("invalidated_at") is None)}
            _check_refs(rep, conn, user, edges, episodes)
            _check_journal(rep, conn, user, edges)
            try:
                _check_revocation(rep, store, rep.users)
            except Exception as ex:                           # noqa: BLE001
                rep.add("revocation", "error", f"the revocation sweep could not be evaluated: "
                        f"{type(ex).__name__}: {ex}")
        finally:
            store.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    _check_runtime(rep)
    return rep


def render(rep: Report) -> str:
    out = [f"veracium doctor — {rep.db}"]
    if not rep.readable:
        for f in rep.findings:
            out.append(f"  ✘ {f.check:11s} {f.message}")
        out.append("  UNREADABLE")
        return "\n".join(out) + "\n"
    out.append(f"  schema v{rep.user_version} (head v{rep.head_version})   users {len(rep.users)}   "
               f"edges {rep.counts.get('edges', 0)} ({rep.counts.get('active_edges', 0)} active)   "
               f"episodes {rep.counts.get('episodes', 0)}")
    by_check = {}
    for f in rep.findings:
        by_check.setdefault(f.check, []).append(f)
    mark = {"error": "✘", "warn": "!", "info": "·"}
    run = rep.checks_run
    # checks that ran, then any check that only left a finding (the refused-snapshot
    # path adds an info under "revocation" without running it)
    for check in run + [c for c in by_check if c not in run]:
        fs = by_check.get(check, [])
        if not fs:
            out.append(f"  ✓ {check:11s} ok")
        for f in fs:
            out.append(f"  {mark[f.level]} {check:11s} {f.message}")
            if f.ids:
                shown = ", ".join(f.ids[:MAX_IDS])
                more = f" … and {len(f.ids) - MAX_IDS} more" if len(f.ids) > MAX_IDS else ""
                out.append(f"      {shown}{more}")
    n_err = sum(1 for f in rep.findings if f.level == "error")
    n_warn = sum(1 for f in rep.findings if f.level == "warn")
    out.append(f"  {'CLEAN' if rep.exit_code == 0 else 'FINDINGS'}: {n_err} error(s), {n_warn} warning(s); "
               f"nothing was changed")
    return "\n".join(out) + "\n"


def to_json(rep: Report) -> dict:
    d = asdict(rep)
    d["exit_code"] = rep.exit_code
    return d
