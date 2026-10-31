"""`veracium doctor` — a no-LLM, read-only static linter for a store file.

    veracium doctor --db veracium.db              # every user
    veracium doctor --db veracium.db --user ida   # one user's rows
    veracium doctor --db veracium.db --json       # machine-readable

Why it exists (the developer-tools backlog, item 5, endorsed 2026-08-30 and
started on the owner's word 2026-09-12): the selfcheck needs a provider, so a
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
                outcome episodes, confirmations, replies, ledger survivors and
                typed contributors, embeddings and journal events all name rows
                that exist; a resolve reply names a challenge of its own edge
  journal       every edge has at least one journal event (specs/0029: a row
                with no `created`/`baseline` event was written outside the
                journal)
  sources       every record whose evidence is THIRD-PARTY AUTHORED carries a
                `source_id` (specs/0006): without one it has no source identity,
                no digest, and cannot be revoked by source (specs/0022 R12) —
                the only remedy left is per-user erasure. Keyed on the AUTHOR
                only: a record whose content was merely DERIVED from a third
                party is not checked, because the stored payload cannot tell a
                declared derivation from the 0011 §4d floor every undeclared
                ingest receives (the owner's staged ruling, option C, 2026-09-12)
  procedural    numbers never merged (research's census, the owner's word
                2026-09-12; the producer split, specs/0037 v23):
                `procedural_declared` — procedural records whose producer
                stamp is `host` (record_procedure), `procedural_captured` —
                producer `extractor` (the quote-gated capture),
                `procedural_unstamped` — procedural records with no
                producer: written before the stamp existed, or after it
                through a path other than `Memory`, or restored from an
                older export or a sub-12 envelope (the field stripped) — the
                producer is UNKNOWN and the count does not say why — each EXACT, the record's
                own stamps — and `procedural_shaped` — DECLARATIVE records whose `note`
                matches the census marker SCREEN, a TRIPWIRE and never a
                count of procedures (specs/0037 §4a: kind is the stamp, never
                the text). Notes only: `summary` is never read (specs/0022
                §7a); this is the doctor's one read of `note`, for a shape
                screen — counts and ids only, the text itself never reported.
                Informational: it cannot fail the build. What it is for:
                noticing an extractor that starts producing procedure-shaped
                notes, or hosts feeding procedures down the declarative path
  revocation    for every standing revocation (specs/0022), the reference
                sweep over the store AS IT IS has no pending effect — the
                sweep is the same pure function the commit path runs, called
                with no proposed action (its `complete` flag, the §4c blind-
                spot count that over-reports by design, is not a finding here)
  data-migration  specs/0044 / the 0018 amendment §4e, the PRE-PLAN phase (no
                plan header): members of the v16 step's arity inventory whose
                current retirement still equals the inventoried one warn,
                judged by relation NAME only and stated as such — never a
                claim of eligibility, which is the plan's. The planned phases
                are the data-migration operation's (not yet implemented)
  runtime       this interpreter's SQLite build, measured before any store
                is opened (specs/0007 §4g), whether or not a store exists:
                attested or verified (info), or refused (error, naming the
                failing step), naming any unreadable key field; then the
                list of attested builds, each with its machine, system and libc

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
from .store.data_migration import PROOF_ORIGINS

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
    attested_builds: list = field(default_factory=list)   # 0007 §4g.6 (v0.12): every current, unpoisoned record

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


def _live_restoration_origins(conn, user: Optional[str]) -> dict:
    """specs/0044 §4k: (user_id, edge_id) → the origins of its LIVE restoration outcomes (`restored`, not undone,
    `applicable`). Joined on the user AND the edge in every run, scoped or not. The refs check runs only on a store
    at this build's version, so the table is there; a store without outcome rows exempts nothing and reads as
    before."""
    out: dict = {}
    for r in conn.execute("SELECT user_id, edge_id, origin FROM migration_outcome WHERE outcome='restored' "
                          "AND undone_at IS NULL AND applicable=1" + (" AND user_id=?" if user else ""),
                          (user,) if user else ()):
        out.setdefault((r[0], r[1]), set()).add(r[2])
    return out


def _check_refs(rep: Report, conn, user: Optional[str], edges: dict, episodes: dict) -> None:
    rep.checks_run.append("refs")
    where, args = ("WHERE user_id=?", (user,)) if user else ("", ())
    # supersedes: the target exists for the same user; no cycles; predecessor retired
    dangling, unretired, restored, testimony = [], [], [], []
    origins = _live_restoration_origins(conn, user)
    for (uid, eid), (row, d) in edges.items():
        pred = d.get("supersedes")
        if not pred:
            continue
        if (uid, pred) not in edges:
            dangling.append(eid)
        elif edges[(uid, pred)][1].get("invalidated_at") is None and d.get("invalidated_at") is None:
            # specs/0044 §4k: the PREDECESSOR's live restoration outcome decides — PROOF (this store restored it:
            # `local`/`restored`, not undone, applicable) is `info`; `imported` testimony keeps the warning and names
            # it; anything else is the old warning, unchanged
            o = origins.get((uid, pred), ())
            (restored if any(x in PROOF_ORIGINS for x in o) else
             testimony if "imported" in o else unretired).append(eid)
    if dangling:
        rep.add("refs", "error", f"{len(dangling)} edge(s) whose `supersedes` names an edge that does "
                "not exist for that user (dangling supersession link)", dangling)
    if unretired:
        rep.add("refs", "warn", f"{len(unretired)} active edge(s) whose predecessor is still active "
                "(a supersession that did not retire what it superseded)", unretired)
    if testimony:
        rep.add("refs", "warn", f"{len(testimony)} active edge(s) whose predecessor is still active and was "
                "restored only by IMPORTED testimony — another store's data-migration outcome, which this store "
                "cannot verify (specs/0044 §4k)", testimony)
    if restored:
        rep.add("refs", "info", f"{len(restored)} active edge(s) whose predecessor is active because this store's "
                "data migration restored it (specs/0044 §4k: its own outcome row is the proof)", restored)
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
    # replies (specs/0047 INV-R5): joined on the user AND the edge, as confirmations are, so a reply naming another
    # user's edge id is an orphan too. A resolve must name a challenge of its own edge (§4b): the writer and the
    # partial unique index hold that, but no CHECK can cross rows, so a row that breaks it is reported (research's
    # T10a Q14). A store from before the table has none to check.
    if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='replies'").fetchone():
        ids = [r["id"] for r in conn.execute(f"SELECT id, user_id, edge_id FROM replies {where}", args)
               if (r["user_id"], r["edge_id"]) not in edges]
        if ids:
            rep.add("refs", "error", f"{len(ids)} reply(ies) naming an edge that does not exist "
                    "(specs/0047 INV-R5)", ids)
        rwhere = where.replace("user_id", "r.user_id")
        ids = [r["id"] for r in conn.execute(
            f"SELECT r.id FROM replies r LEFT JOIN replies c ON c.user_id = r.user_id AND c.id = r.target "
            f"AND c.edge_id = r.edge_id AND c.kind = 'challenge' {rwhere} {'AND' if rwhere else 'WHERE'} "
            f"r.kind = 'resolve' AND c.id IS NULL", args)]
        if ids:
            rep.add("refs", "error", f"{len(ids)} resolve reply(ies) naming no challenge of their own edge "
                    "(specs/0047 §4b)", ids)
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
    # specs/0041 v15: redaction records name a target; episode events name an episode
    if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='redactions'").fetchone():
        # specs/0041 §11.6.6 (T4): a redaction row's NOTICE STATE is stored — `applied` (an attestation), `pending`
        # (a witnessed notice over a held record, awaiting the user's `confirm_notice`), `standing` (a witnessed notice
        # whose record this store does not hold). The DDL holds no CHECK, so a value outside the closed sets is damage.
        from . import redaction as _red
        rows = list(conn.execute("SELECT id, user_id, target_kind, target_id, reason, event_ref, source_origin, "
                                 f"source_user, state, pending_reason FROM redactions {where}", args))
        bad = [r["id"] for r in rows
               if r["state"] not in _red.NOTICE_STATES
               or (r["state"] == "pending") != (r["pending_reason"] is not None)
               or (r["state"] == "pending" and r["pending_reason"] not in _red.PENDING_REASONS)]
        if bad:
            rep.add("refs", "error", f"{len(bad)} redaction record(s) whose notice state or pending reason is outside "
                    f"{_red.NOTICE_STATES} / {_red.PENDING_REASONS}, or a pending reason on a row that is not pending "
                    f"(specs/0041 §11.6.6)", bad)
        held = lambda r: (r["user_id"], r["target_id"]) in (edges if r["target_kind"] == "edge" else episodes)   # noqa: E731
        pending = [f"{r['id']} ({r['target_kind']} {r['target_id']}; {r['pending_reason']}; claimed source "
                   f"{r['source_origin']}/{r['source_user']})" for r in rows if r["state"] == "pending" and held(r)]
        if pending:
            rep.add("refs", "info", f"{len(pending)} PENDING redaction notice(s) awaiting the user's confirmation "
                    f"(`confirm_notice`): another store's unauthenticated testimony that it redacted a record held here; "
                    f"nothing is redacted until confirmed (specs/0041 §11.6.6)", pending)
        inert = [r["id"] for r in rows if r["state"] == "pending" and not held(r)]
        if inert:
            rep.add("refs", "info", f"{len(inert)} pending redaction notice(s) whose record no longer exists — inert: "
                    f"confirming one is refused (specs/0041 §11.6.6)", inert)
        standing = [r["id"] for r in rows if r["state"] == "standing"]
        if standing:
            rep.add("refs", "info", f"{len(standing)} standing redaction notice(s) naming no record this store held when "
                    f"they arrived — they refuse no write and redact nothing; a later import that creates the record "
                    f"refuses it unredacted, and otherwise leaves the notice pending or (a trusted restore) applies it "
                    f"(specs/0041 §11.6.6)", standing)
        absent = [r for r in rows if r["state"] == "applied" and not held(r)]
        # round 11 (R10-02): an APPLIED attestation whose EPISODE is gone is a state the store makes legitimately —
        # the supported `delete_episode`, after which a re-arriving record is written in its treated shape (§4g).
        # Only episodes: no supported remover deletes a single edge, so an absent edge stays an error. The doctor
        # cannot tell "deleted" from "never existed"; planting the latter needs raw SQL, outside what it serves.
        is_deleted_episode = lambda r: r["target_kind"] == "episode"   # noqa: E731
        deleted = [r["id"] for r in absent if is_deleted_episode(r)]
        ids = [r["id"] for r in absent if not is_deleted_episode(r)]
        if deleted:
            rep.add("refs", "info", f"{len(deleted)} redaction record(s) for an episode since deleted — the record stays "
                    f"attested (its journal events stay too), and a re-arriving copy with its notice is written treated "
                    f"(specs/0041 §4g); not damage",
                    deleted)
        if ids:
            rep.add("refs", "error", f"{len(ids)} redaction record(s) naming a target that does not exist", ids)
        # round 11 (R10-02): the episode journal is append-only, so a deleted ATTESTED episode keeps its events — the
        # same legitimate state as its redaction record above, reported there; events of any OTHER absent episode stay
        # an error
        gone_attested = {(r["user_id"], r["target_id"]) for r in absent if is_deleted_episode(r)}
        ids = [r["episode_id"] for r in conn.execute(f"SELECT DISTINCT episode_id, user_id FROM episode_event {where}", args)
               if (r["user_id"], r["episode_id"]) not in episodes and (r["user_id"], r["episode_id"]) not in gone_attested]
        if ids:
            rep.add("refs", "error", f"{len(ids)} episode event(s) naming an episode that does not exist", ids)
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


def _check_sources(rep: Report, edges: dict, episodes: dict) -> None:
    """specs/0006 I13 / specs/0022 R12, read the other way round: a third-party-
    AUTHORED record with no `source_id` is one no revocation can ever reach."""
    rep.checks_run.append("sources")
    def unsourced(d):
        prov = d.get("provenance") or {}
        return prov.get("author_of_evidence") == "third_party" and not prov.get("source_id")
    live = [eid for (_u, eid), (_row, d) in edges.items() if unsourced(d) and d.get("invalidated_at") is None]
    gone = [eid for (_u, eid), (_row, d) in edges.items() if unsourced(d) and d.get("invalidated_at") is not None]
    eps = [eid for (_u, eid), d in episodes.items() if unsourced(d) and not d.get("retired_reason")]
    if live or eps:
        rep.add("sources", "warn",
                f"{len(live)} active fact(s) and {len(eps)} episode(s) with third-party-authored evidence "
                f"carry no source_id: no source identity, no digest, not revocable by source (specs/0006 "
                f"I13, specs/0022 R12) — only per-user erasure reaches them"
                + (f"; {len(gone)} retired fact(s) likewise" if gone else ""),
                live + eps)


# research's census marker SCREEN (section8-labelling, 2026-09-12), VERBATIM as
# research re-ran and sent it (Python `re`, compiled with re.I and nothing else;
# the TRAILING SPACES after `before`, `after`, `then` and `first` are load-bearing
# — without them the screen matches inside words and the count changes). It is
# the instrument behind the census's 13 of 312 and the 1-in-20 control (a 20-item
# read of non-candidates: 1 arguably habitual), chosen over the unvalidated
# detector. NOT the wider summaries screen (36/100), which is never shipped:
# summaries are meta-narrations and specs/0022 §7a forbids reading them anyway.
# Baseline, stated the only honest way: 13 SCREEN HITS in 312 notes, 0 GENUINE
# ON READING (every hit temporal — "purchased two weeks before 2023-05-27" — not
# sequential); production mailbox (0.13.0) 5,436 notes, 2 genuine of 12
# detector positives read completely. The tripwire's meaning is a CHANGE IN THE
# HIT RATE, never the hit count read as a quantity of procedures (specs/0037
# §4a: kind is the stamp, never the text) — which is why the two numbers the
# check reports are never merged. Measured before 0037 v16; a captured procedure
# now carries its quote in `note`, but stamped records are never screened here.
PROCEDURAL_MARKERS = re.compile(
    r"every \d|each (week|month|day|morning)|routine|always|usually|before |after |then |"
    r"by \w+ing|prefers to|steps?\b|first ", re.I)


def _check_procedural(rep: Report, edges: dict) -> None:
    """Research's census as a standing check (the owner's word, 2026-09-12).
    Numbers deliberately separated and never added: what hosts DECLARED and
    what the extractor CAPTURED (the producer stamp, exact — specs/0037 v23;
    a procedural record from before that stamp is reported as UNSTAMPED, not
    guessed into either), and what declarative notes LOOK like (the screen, a
    tripwire). Notes only — specs/0022 §7a forbids reading `summary`; this is
    the doctor's one read of `note`, for the screen, and it reports counts
    and ids, never the text. Informational on every outcome."""
    rep.checks_run.append("procedural")
    # specs/0037 v23 §4a-iii: the kind stamp says WHAT a record is; the
    # PRODUCER stamp says WHICH product path wrote it. Until v23 the two
    # producers wrote byte-identical stamps, so the "declared" count here
    # merged host-declared and extractor-captured records (research's
    # finding, 2026-09-14). Now three numbers by the record's own stamps,
    # never added: declared (producer host), captured (producer extractor),
    # unstamped (a procedural record with NO producer — the producer is
    # UNKNOWN: written before the producer stamp existed; restored from an
    # older export or from an envelope below format 12, where 0006 I10 strips
    # the field; or written through a path other than Memory — a hand-minted
    # record at Store.add_edge, the boundary 0006 v10 rule 10 states rather
    # than gates. The count establishes that the producer is unknown, not why:
    # v23.1's "on a store created after the stamp existed a non-zero count is
    # the live reading of a write past the Memory boundary" was WITHDRAWN at
    # v24.1 — the round-5 reviewer restored a format-11 record into a new
    # database and got unstamped=1 through an ordinary supported path).
    declared, captured, unstamped, shaped = [], [], [], []
    for (_u, eid), (_row, d) in edges.items():
        prov = d.get("provenance") or {}
        if prov.get("record_kind") == "procedural":
            producer = prov.get("producer")
            (declared if producer == "host" else captured if producer == "extractor"
             else unstamped).append(eid)
        elif PROCEDURAL_MARKERS.search(str(d.get("note") or "")):
            shaped.append(eid)
    rep.counts["procedural_declared"] = len(declared)
    rep.counts["procedural_captured"] = len(captured)
    rep.counts["procedural_unstamped"] = len(unstamped)
    rep.counts["procedural_shaped"] = len(shaped)
    rep.add("procedural", "info",
            f"procedural_declared {len(declared)} (host-declared through record_procedure — exact, the record's "
            f"own producer stamp) · procedural_captured {len(captured)} (extractor-captured behind the quote gate "
            f"— exact, the producer stamp) · procedural_unstamped {len(unstamped)} (stamped procedural with NO producer — "
            f"the producer is UNKNOWN: written before the producer stamp existed, restored from an older export or from "
            f"an envelope below format 12 (the field stripped at import), or written through a path other than Memory; "
            f"the count says the producer is unknown, not why, and declared and captured cannot be told apart there) · "
            f"procedural_shaped "
            f"{len(shaped)} (declarative records whose note matches the census "
            f"marker screen — a SCREEN RESULT, never a count of procedures; the baseline is 13 screen hits "
            f"in 312 notes with 0 genuine on reading, so only a CHANGE in the hit rate means anything; the "
            f"numbers are never merged)",
            shaped)


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


# 0018 amendment §4e, the uninitialized phase's finding, verbatim
PRE_PLAN_WARNING = ("may have values to restore (judged by relation name): run run_data_migration(path, "
                    "host_attestation=…, registry=…) — see 0044. A host whose registry keeps a custom single-value "
                    "declaration for these relations will find none eligible.")


# 0018 amendment §4e, the initialized-EMPTY phase's finding, verbatim
PLAN_EMPTY_INFO = ("data migration planned: no relation was reclassified (this host's own declarations keep them "
                   "single-valued); nothing to restore")


def _check_data_migration(rep: Report, conn, user: Optional[str], edges: dict) -> None:
    """specs/0044 §4k / 0018 §4i.6 §4e — the four phases, read from the plan HEADER (an empty plan is a state of its
    own):
      uninitialized         an arity-inventory member, under a reclassified default NAME, still holds exactly its
                            inventoried retirement (0044 §4f's equality test, through `lifetime.retirement`: no time
                            is compared) → warn, name-only and stated as such;
      initialized-empty     → info, §4e's text;
      initialized-nonempty  users of the operation's universe (those holding an `arity_inventory` row — 0018 §4i's
                            research annotation) without a run row → warn, naming the count and the operation;
                            none → nothing."""
    rep.checks_run.append("data-migration")
    from .store.lifetime import RECLASSIFIED_RELATIONS, retirement, same_retirement
    # research's T6 S2 F5, in every phase: an inventory row naming no edge of its own user is damage, and the
    # operation fails that user until it is repaired
    q = ("SELECT i.edge_id FROM arity_inventory i LEFT JOIN edges e ON e.id = i.edge_id "
         "WHERE (e.id IS NULL OR e.user_id != i.user_id)")
    damaged = [r[0] for r in conn.execute(q + (" AND i.user_id=?" if user else "") + " ORDER BY i.edge_id",
                                          (user,) if user else ())]
    if damaged:
        rep.add("data-migration", "warn",
                f"{len(damaged)} arity_inventory row(s) name no edge of their own user — the store is damaged, and "
                f"run_data_migration fails that user until it is repaired", damaged)
    header = conn.execute("SELECT plan_id FROM plan_header WHERE id=1").fetchone()
    if header is not None:
        plan_id = header[0]
        if conn.execute("SELECT 1 FROM reclassification_plan WHERE plan_id=? LIMIT 1", (plan_id,)).fetchone() is None:
            rep.add("data-migration", "info", PLAN_EMPTY_INFO)
            return
        q = ("SELECT DISTINCT i.user_id FROM arity_inventory i WHERE NOT EXISTS (SELECT 1 FROM migration_run r "
             "WHERE r.plan_id=? AND r.user_id=i.user_id)")
        missing = [r[0] for r in conn.execute(q + (" AND i.user_id=?" if user else "") + " ORDER BY i.user_id",
                                              (plan_id, user) if user else (plan_id,))]
        if missing:
            rep.add("data-migration", "warn",
                    f"{len(missing)} user(s) have not completed the per-user phase of plan {plan_id}: re-run "
                    f"run_data_migration(path, host_attestation=…, registry=…) — see 0044", missing)
        return
    q = "SELECT user_id, edge_id, pre_invalidated_at, pre_reason FROM arity_inventory"
    rows = conn.execute(q + (" WHERE user_id=?" if user else ""), (user,) if user else ()).fetchall()
    ids = []
    for uid, eid, at, reason in rows:
        held = edges.get((uid, eid))
        if held is None:
            continue
        d = held[1]
        if d.get("relation") in RECLASSIFIED_RELATIONS and same_retirement(retirement(d), (at, reason)):
            ids.append(eid)
    if ids:
        rep.add("data-migration", "warn", f"{len(ids)} retired value(s) {PRE_PLAN_WARNING}", ids)


def _attested_builds() -> list:
    """Each attested build, `SQLite <version> on <machine> <system> <libc> (<route> <image>, …)`, one per CURRENT record of an
    UNPOISONED artifact: attested_key's rule, so a poisoned or unreadable artifact lists nothing (it attests nothing).
    Total: an escape lists nothing rather than failing the report."""
    try:
        records = sv.attestations()
        if sv.attestation_artifact_problems(records):
            return []
        out = []
        for r in records:
            if sv.attestation_revision(r) != "current":
                continue
            routes = ", ".join(sorted({f"{p['route']} {p['runner_image']}" for p in r["provenance"]}))
            out.append((tuple(int(x) for x in r["sqlite_version"].split(".")),
                        f"SQLite {r['sqlite_version']} on {r['machine']} {r['system']} {r['libc']} ({routes})"))
        return [s for _, s in sorted(out)]
    except Exception:  # noqa: BLE001 - a listing never fails the report
        return []


def _check_runtime(rep: Report) -> None:
    """0007 §4g.6 4e (INV-SA9): the SQLite status, measured BEFORE any store is opened, so it runs exactly when a
    refused build needs it, and always leaves its one finding (a store-less run reports the build too). `attested`
    and `verified` are `info` (doctor exits 1 on any warning, and an unattested but verified build is not a store
    problem); `refused` is `error`, with the failing step. Each names any unreadable field of the build's key (such a
    build matches no record), and the report carries the attested builds (v0.12)."""
    rep.checks_run.append("runtime")
    st = sv.runtime_status()                                  # total: never raises
    build = (f"SQLite {st.sqlite_version or '(version unreadable)'} on "
             + " ".join(v if v else "(unreadable)" for v in st.platform))
    gaps = (f"; unreadable key field(s): {', '.join(st.unreadable)}, so it matches no attestation record"
            if st.unreadable else "")
    rep.attested_builds = _attested_builds()
    if st.status == "refused":
        rep.add("runtime", "error", f"this interpreter's SQLite cannot be verified for the store: {st.reason}{gaps}")
    elif st.status == "verified":
        rep.add("runtime", "info", f"this interpreter's {build} is not an attested build; it was verified on this run "
                "(it reproduces every schema version and tells apart every near-miss)"
                + (f"; the attestation records were not used: {st.reason}" if st.reason else "") + gaps)
    else:
        rep.add("runtime", "info", f"this interpreter's {build} is an attested build" + gaps)


# ------------------------------------------------------------------- driver --
def diagnose(path: str, *, user: Optional[str] = None) -> Report:
    rep = Report(db=path, readable=False)
    _check_runtime(rep)                                       # before any store is opened (INV-SA9)
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
            _check_sources(rep, edges, episodes)
            _check_procedural(rep, edges)
            _check_data_migration(rep, conn, user, edges)
            try:
                _check_revocation(rep, store, rep.users)
            except Exception as ex:                           # noqa: BLE001
                rep.add("revocation", "error", f"the revocation sweep could not be evaluated: "
                        f"{type(ex).__name__}: {ex}")
        finally:
            store.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return rep


def _attested_lines(rep: Report) -> list:
    """The attested builds under the runtime line, every one (never MAX_IDS-truncated: the list is the remedy a
    refusal names)."""
    if not rep.attested_builds:
        return ["      no build is attested by this package"]
    return [f"      attested builds ({len(rep.attested_builds)}):"] + [f"        {b}" for b in rep.attested_builds]


def render(rep: Report) -> str:
    out = [f"veracium doctor — {rep.db}"]
    mark = {"error": "✘", "warn": "!", "info": "·"}
    if not rep.readable:
        for f in rep.findings:
            out.append(f"  {mark[f.level]} {f.check:11s} {f.message}")
            if f.check == "runtime":
                out += _attested_lines(rep)
        out.append("  UNREADABLE")
        return "\n".join(out) + "\n"
    out.append(f"  schema v{rep.user_version} (head v{rep.head_version})   users {len(rep.users)}   "
               f"edges {rep.counts.get('edges', 0)} ({rep.counts.get('active_edges', 0)} active)   "
               f"episodes {rep.counts.get('episodes', 0)}")
    by_check = {}
    for f in rep.findings:
        by_check.setdefault(f.check, []).append(f)
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
            if check == "runtime":
                out += _attested_lines(rep)
    n_err = sum(1 for f in rep.findings if f.level == "error")
    n_warn = sum(1 for f in rep.findings if f.level == "warn")
    out.append(f"  {'CLEAN' if rep.exit_code == 0 else 'FINDINGS'}: {n_err} error(s), {n_warn} warning(s); "
               f"nothing was changed")
    return "\n".join(out) + "\n"


def to_json(rep: Report) -> dict:
    d = asdict(rep)
    d["exit_code"] = rep.exit_code
    return d
