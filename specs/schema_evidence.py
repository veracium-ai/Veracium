#!/usr/bin/env python3
"""Generated evidence: what every released version built, and on what runtime.

Separated from the schema kernel because git probing and artifact presentation
should not sit inside the trust boundary (round 5). This module *uses*
`schema_model`; nothing in `schema_model` depends on it.

**Migrations are out of `0007`'s scope from v10** -- see `specs/0013`. What
remains here is constructor output per version, which is what adoption needs.

  `--releases --write`  build a store with every released tag's own code and
                        record tag, commit sha, on-disk stamp, resolved version
                        and digest.
  `--runtime --write`   record this SQLite runtime's identity and feature probes.
  `--check`             re-derive every authoritative field and compare.
                        **Needs a git checkout**; exits 2 in an extracted archive.

**Every field is classified.** v6 said the gate re-derived everything and it did
not: an artifact with `head_digest="BAD"`, `head_schema_version=999`,
`sv.legacy_base_versions=[999]`, `sqlite_version="0.0.0"` and every release
`result="fabricated"` passed with rc 0 (round 5, finding 4, measured). A field
kept as evidence must be checked; a field that cannot be checked must not be
kept as evidence.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from schema_model import (GENERATED, POLICY_ARTIFACT, ROOT, SCHEMA_VERSION,  # noqa: E402
                          SCHEMAS, create, declared_policies, digest, identity,
                          manifest, resolve)
from veracium.store import schema_version as sv  # noqa: E402

# One canonical module: every artifact path and validator lives on `sv`, and
# this module (and the tests) reach them as ATTRIBUTES, so patching
# `sv.<name>` is the single point of truth. Re-bound names would be snapshots.
EVIDENCE_DIR = sv.EVIDENCE_DIR


# Which recorded fields are authoritative (re-derived and compared), which are
# summaries (recomputed from the authoritative ones), and which are notes.
# `result` is authoritative and was NOT compared until round 7, finding 7:
# the gate inspected the *stored* value, so a record could describe a
# freshly unbuildable release as "ok".
AUTHORITATIVE = ("tag", "commit", "on_disk_user_version", "store_schema_version",
                 "digest", "result")
SUMMARY = ("legacy_base_versions", "head_digest", "head_schema_version")


# --------------------------------------------------------------------------
# runtime identity


def _stage(path: pathlib.Path, text: str) -> pathlib.Path:
    """Write the new content beside its target, without publishing it.

    **The residual limit, stated rather than claimed away:** two renames are not
    one transaction. A crash between them can still leave the pair disagreeing.
    **The honest atomic boundary is the git commit**, and `--check` fails on a
    disagreeing pair — which is the guarantee that actually holds."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    return tmp


def _discard(*tmps) -> None:
    """Remove staged temporaries. v12 left `sqlite_runtimes.json.tmp` behind and
    it shipped in the review package (round 10)."""
    for t in tmps:
        try:
            t.unlink(missing_ok=True)
        except OSError:
            pass


def build_runtime_record() -> dict:
    me = sv.runtime_identity()
    me["manifest_algorithm"] = sv.MANIFEST_ALGORITHM
    me["schema_version"] = SCHEMA_VERSION
    me["constructor_digests"] = {str(v): sv._constructor_digest(v) for v in sorted(SCHEMAS)}
    # Full object records, not only digests: a second qualified runtime's
    # manifestations must be reconstructible, and an object-level `diff` cannot
    # be built from a digest (round 7, finding 4).
    me["manifestations"] = {f"constructor v{v}": sv._constructor_objects(v)
                            for v in sorted(SCHEMAS)}
    return me


def write_runtime(force: bool = False) -> int:
    """Record **this** runtime as qualified. Round 6, finding 5: `--runtime
    --write` was documented and did nothing — the flag was ignored on that path,
    so the stated workflow for qualifying a second runtime did not exist."""
    rec = build_runtime_record()
    problems = sv.runtime_record_problems(rec)
    if problems and not force:
        for p in problems:
            print(p, file=sys.stderr)
        print("refusing to write incomplete runtime evidence", file=sys.stderr)
        return 1
    # **Replacement is by build identity, with one carve-out for superseded
    # revisions** (round 12, finding 1). Same build identity -> replaced: that
    # is a new evidence revision of the same build. Same (version, source_id)
    # at an OLDER algorithm -> also replaced, because probe definitions may
    # have changed with the algorithm and the old record is superseded either
    # way; this is what clears a bump without deadlocking. Same (version,
    # source_id), CURRENT algorithm, different probes -> kept, and
    # `sv.artifact_problems()` refuses the contradiction rather than this code
    # silently deciding which record to believe.
    # **Round 13, finding 1: the evidence revision must be MONOTONE.** v15's
    # rule was "!= current algorithm", which read as "older" in the comments and
    # meant "any other" in the code — so an old checkout silently overwrote
    # evidence generated by newer code (a record at algorithm 14 became 13, and
    # a schema-version-2 record became 1; both measured, rc 0). Downgrading
    # evidence is the reverse of superseding it. A FUTURE component refuses.
    def _newer(r):
        if not isinstance(r, dict):
            return False
        alg, schema_v = r.get("manifest_algorithm"), r.get("schema_version")
        return ((type(alg) is int and alg > sv.MANIFEST_ALGORITHM)
                or (type(schema_v) is int and schema_v > SCHEMA_VERSION))
    future = [r for r in sv.qualified_runtimes()
              if _newer(r) and isinstance(r, dict)
              and (r.get("sqlite_version"), r.get("source_id"))
              == (rec["sqlite_version"], rec["source_id"])]
    if future:
        print(f"refusing to overwrite evidence from a NEWER revision "
              f"(algorithm {future[0].get('manifest_algorithm')}, schema "
              f"{future[0].get('schema_version')}); this checkout is older than "
              f"the artifact", file=sys.stderr)
        return 1

    def _replaced(r):
        if not isinstance(r, dict):
            return True                        # malformed junk: rewrite it away
        if sv.build_identity(r) == sv.build_identity(rec):
            return True
        # The older-algorithm carve-out: probe definitions may have changed, so
        # the old record's features are not comparable. STRICTLY older only —
        # future revisions were refused above.
        alg = r.get("manifest_algorithm")
        return ((r.get("sqlite_version"), r.get("source_id"))
                == (rec["sqlite_version"], rec["source_id"])
                and type(alg) is int and alg < sv.MANIFEST_ALGORITHM)
    others = [r for r in sv.qualified_runtimes() if not _replaced(r)]
    GENERATED.mkdir(parents=True, exist_ok=True)

    # **Round 8, finding 3: qualification must be atomic at the artifact level.**
    # v10 wrote only `sqlite_runtimes.json` and reported success, leaving
    # `schema_versions.json` byte-for-byte unchanged. Measured by adding 3.46.1:
    # rc 0, two runtime records, accepted provenance still "constructor v1"
    # only. On those two runtimes the digests agree so nothing broke -- but when
    # a runtime produces different stored DDL, which is the entire reason the
    # union model exists, it would be marked qualified while the stores it
    # creates were NOT in MANIFESTS.
    # **Round 9, finding 2: the "both or neither" claim was false.** v11 wrote
    # the runtime file first and restored it only on `SystemExit`; an ordinary
    # `OSError` from the second write left a qualified-but-stale artifact.
    # Measured against a simulated disk failure.
    #
    # The order is now: build and validate the complete prospective pair in
    # memory, then publish both by atomic rename. A crash between the two
    # renames is still possible -- **os.replace is per-file, not a two-file
    # transaction** -- so the honest boundary is the git commit, and `--check`
    # fails on a disagreeing pair. That limit is stated rather than claimed
    # away.
    prospective = {"runtimes": others + [rec]}
    saved_runtimes = sv.qualified_runtimes()
    try:
        sv._RUNTIME_OVERRIDE.append(prospective["runtimes"])
        versions = build_version_artifact()
        accepted = {a["digest"] for recs in versions["versions"].values()
                    for a in recs["accepted"]}
        for rt in prospective["runtimes"]:
            if sv.runtime_record_problems(rt) or rt.get("manifest_algorithm") != sv.MANIFEST_ALGORITHM:
                continue
            for prov, objs in rt["manifestations"].items():
                v = int(prov.rsplit("v", 1)[1])
                if sv._digest_of_identity(objs, v) not in accepted:
                    raise SystemExit(f"runtime output {prov} @ "
                                     f"{rt['sqlite_version']} is not in the "
                                     f"accepted set")
    except (Exception, SystemExit) as exc:      # validation OR filesystem
        # `SystemExit` is not an `Exception`, so v12's handler never caught
        # the validation failure it was written for (round 10).
        print(f"qualification refused, artifacts unchanged: {exc}", file=sys.stderr)
        return 1
    finally:
        sv._RUNTIME_OVERRIDE.clear()

    # Stage BOTH temporaries before renaming either, so a filesystem failure
    # happens while nothing is published. The two renames are then back to back,
    # and the first is rolled back if the second fails.
    saved = sv.RUNTIMES.read_text() if sv.RUNTIMES.exists() else None
    try:
        t_rt = _stage(sv.RUNTIMES, json.dumps(prospective, indent=2) + "\n")
        t_vs = _stage(sv.VERSIONS, json.dumps(versions, indent=2) + "\n")
    except OSError as exc:
        _discard(sv.RUNTIMES.with_suffix(sv.RUNTIMES.suffix + ".tmp"),
                 sv.VERSIONS.with_suffix(sv.VERSIONS.suffix + ".tmp"))
        print(f"staging failed, nothing published: {exc}", file=sys.stderr)
        return 1
    try:
        t_rt.replace(sv.RUNTIMES)
        t_vs.replace(sv.VERSIONS)
    except OSError as exc:
        _discard(t_rt, t_vs)
        if saved is None:
            sv.RUNTIMES.unlink(missing_ok=True)
        else:
            sv.RUNTIMES.write_text(saved)
        print(f"publish failed and was rolled back: {exc}", file=sys.stderr)
        return 1
    me_key = sv._identity_key(build_runtime_record())
    valid = sv.active_records(prospective["runtimes"])
    attested = sum(1 for r in valid if sv._identity_key(r) == me_key)
    unattested = len(valid) - attested
    stale = len(prospective["runtimes"]) - len(valid)
    # Round 9: superseded records were counted as "qualified". They are not.
    # Round 10: an internally valid but unattested foreign record was counted
    # as "active" though it contributes nothing. Three categories, named.
    print(f"recorded {rec['sqlite_version']} ({rec['source_id'][:20]}…) — "
          f"{attested} attested and contributing, {unattested} recorded but "
          f"unattested, {stale} superseded or invalid")
    if unattested or stale:
        print(f"note: {unattested + stale} record(s) contribute no accepted "
              f"manifest")
    return 0


# --------------------------------------------------------------------------
# accepted manifests per version


def build_version_artifact(strict: bool = True) -> dict:
    """Regenerate accepted manifests. Historical versions are immutable.

    Two guards, both from round 5's finding 5:

      * a historical version that regenerates *differently* is an error (v6 had
        this);
      * a historical version that is **missing** is also an error (v6 did not —
        running the generator with version 1 dropped from `SCHEMAS` silently
        emitted an artifact without it).

    Generation is bound to the declared `SCHEMA_VERSION`, not `max(SCHEMAS)`."""
    existing = (json.loads(sv.VERSIONS.read_text()).get("versions", {})
                if sv.VERSIONS.exists() else {})
    from schema_model import validate_schema_registry
    out, problems = {}, validate_schema_registry()

    for version in sorted(SCHEMAS):
        accepted = []
        c = sqlite3.connect(":memory:")
        create(c, version)
        accepted.append({"provenance": f"constructor v{version}",
                         "digest": digest(manifest(c), version),
                         "objects": identity(manifest(c))})
        # 0014 §4b / accepted 0013 §4e: v6 accepts a SECOND manifest — the v5->v6
        # ALTER path, whose `supersession_operations` stored DDL legitimately differs
        # from the constructor's. The entry is built from the REVIEWED CONSTANT
        # (`ALTER_PATH_V6_SQL`, authorized by the 0014 acceptance review), never by
        # running the migration here — `0013` §4c: a migration may not define its own
        # destination. The sha self-check makes a drifted constant fail loudly.
        # specs/0019: v7 is the NO-DDL bump over v6 (SCHEMA_V7 = SCHEMA_V6
        # byte-identical), so every v6-legal on-disk shape is v7-legal —
        # including the reviewed ALTER-path shape, which a ≤v5-base store
        # migrating to v7 lands in by crossing the v6 ALTER en route.
        if version in (6, 7):
            import copy
            import hashlib as _h
            if (_h.sha256(sv.ALTER_PATH_V6_SQL.encode()).hexdigest()
                    != sv.ALTER_PATH_V6_SHA256):
                raise SystemExit("ALTER_PATH_V6_SQL does not match its reviewed "
                                 "sha256 (0014 §4b) — refusing to emit evidence")
            alt = copy.deepcopy(identity(manifest(c)))
            alt["table:supersession_operations"] = dict(
                alt["table:supersession_operations"], sql=sv.ALTER_PATH_V6_SQL)
            accepted.append({
                "provenance": f"v5:constructor->v{version} (reviewed ALTER-path "
                              f"constant — specs/0014 §4b, sha 326ea193…)",
                "digest": sv._digest_of_identity(alt, version),
                "objects": alt})
        # SCHEMA v8 (the 0019 rider as amended by 0020/0021, C2/C4; 0021 §7b):
        # v8's shape evidence includes BOTH manifestations of `contribution_ledger`
        # — and because the v6 supersession_operations divergence persists, the
        # accepted set is the full REACHABLE matrix of the two tables' forms:
        #   constructor × constructor  — fresh v8, or a ≤v3 base (both tables are
        #                                created by the additive diff, inline);
        #   ALTER-v6    × constructor  — a v4/v5 base migrated to v8 (the ledger
        #                                is created inline, the receipts ALTERed);
        #   constructor × ALTER-v8     — a v6/v7 base BORN at ≥v6, migrated to v8;
        #   ALTER-v6    × ALTER-v8     — a v6/v7 base that itself arrived from ≤v5
        #                                by the earlier migration, now migrated on.
        # The ledger's ALTER-path entry is the RECORDED CONSTANT `ALTER_PATH_V8_SQL`
        # (schema_v8_evidence.txt [2], sha-checked), never produced by running the
        # migration here — `0013` §4c: a migration may not define its own destination.
        # SCHEMA v9 (specs/0022 §4a): a PURELY ADDITIVE bump — `source_revocations`
        # and its index are created identically by the fresh constructor and by the
        # additive migration diff, so no NEW divergence enters the matrix and the
        # v8 reachable matrix over the two historically-divergent tables persists
        # UNCHANGED at v9. Discovered the hard way: emitting only the constructor
        # manifestation left a migrated v7 base refused by the post-migration
        # re-check ("nearest accepted manifest: constructor v9; 1 object differs:
        # contribution_ledger") — the migration was right and the evidence was
        # incomplete, which is the correct direction of refusal.
        if version in (8, 9):
            import copy
            import hashlib as _h
            if (_h.sha256(sv.ALTER_PATH_V8_SQL.encode()).hexdigest()
                    != sv.ALTER_PATH_V8_SHA256):
                raise SystemExit("ALTER_PATH_V8_SQL does not match its recorded "
                                 "sha256 (0019 rider C2 / 0021 §7b) — refusing to "
                                 "emit evidence")
            ctor = identity(manifest(c))
            for sup_alt, ledger_alt, prov in (
                    (True, False, f"v5:constructor->v{version} (reviewed v6 ALTER-path "
                                  f"constant — specs/0014 §4b, sha 326ea193…; "
                                  f"ledger created inline)"),
                    (False, True, f"v7:constructor->v{version} (recorded ALTER-path "
                                  f"constant — 0019 rider C2 / 0021 §7b, "
                                  f"sha 027b5ca3…)"),
                    (True, True, f"v5:constructor->v7->v{version} (both ALTER-path "
                                 f"constants — specs/0014 §4b sha 326ea193…, "
                                 f"0019 rider C2 sha 027b5ca3…)")):
                alt = copy.deepcopy(ctor)
                if sup_alt:
                    alt["table:supersession_operations"] = dict(
                        alt["table:supersession_operations"],
                        sql=sv.ALTER_PATH_V6_SQL)
                if ledger_alt:
                    alt["table:contribution_ledger"] = dict(
                        alt["table:contribution_ledger"],
                        sql=sv.ALTER_PATH_V8_SQL)
                accepted.append({
                    "provenance": prov,
                    "digest": sv._digest_of_identity(alt, version),
                    "objects": alt})
        # SCHEMA v10 (specs/0025 §4b-v; the CONFIRMED 0014 amendment): the ONE
        # ADD COLUMN on `supersession_operations` makes the ops table's
        # MIGRATED form differ from the fresh constructor at v10 — in TWO
        # variants, because v9 stores already held the table in two accepted
        # forms. Crossed with the ledger's persisting two forms, the reachable
        # matrix is 2 × 2 migrated combinations + the fresh constructor:
        #   ctor-base ops-ALTER  × ledger inline   — fresh v8/v9 base migrated;
        #   v6-path  ops-ALTER   × ledger inline   — a v4/v5 base (ledger
        #                                            created inline en route);
        #   ctor-base ops-ALTER  × ALTER-v8 ledger — a v6/v7-born base;
        #   v6-path  ops-ALTER   × ALTER-v8 ledger — a v6/v7 base that itself
        #                                            arrived from ≤v5.
        # Both ops entries are the FROZEN v10 constants (sha-checked), never
        # produced by running the migration here — 0013 §4c.
        if version in (10, 11):   # specs/0001 I13c (candidate): v11
            # inherits EVERY accepted v10 manifestation BY CONSTRUCTION —
            # the same 2x2 object manipulation, digested at 11 (SCHEMA_V11
            # is SCHEMA_V10, so exact inheritance is the same code path)
            import copy
            import hashlib as _h
            for const, sha in ((sv.ALTER_PATH_V10_FROM_CONSTRUCTOR_SQL,
                                sv.ALTER_PATH_V10_FROM_CONSTRUCTOR_SHA256),
                               (sv.ALTER_PATH_V10_FROM_V6_ALTERPATH_SQL,
                                sv.ALTER_PATH_V10_FROM_V6_ALTERPATH_SHA256)):
                if _h.sha256(const.encode()).hexdigest() != sha:
                    raise SystemExit("an ALTER_PATH_V10 constant does not "
                                     "match its pinned sha256 (0025 §4b-v) — "
                                     "refusing to emit evidence")
            ctor = identity(manifest(c))
            for ops_sql, ops_tag in (
                    (sv.ALTER_PATH_V10_FROM_CONSTRUCTOR_SQL,
                     "v10 ALTER on the constructor base, sha 336b762f…"),
                    (sv.ALTER_PATH_V10_FROM_V6_ALTERPATH_SQL,
                     "v10 ALTER on the v6 ALTER-path base, sha a788a867…")):
                for ledger_alt, ledger_tag in (
                        (False, "ledger inline"),
                        (True, "ALTER-path ledger — 0019 rider C2, "
                               "sha 027b5ca3…")):
                    alt = copy.deepcopy(ctor)
                    alt["table:supersession_operations"] = dict(
                        alt["table:supersession_operations"], sql=ops_sql)
                    if ledger_alt:
                        alt["table:contribution_ledger"] = dict(
                            alt["table:contribution_ledger"],
                            sql=sv.ALTER_PATH_V8_SQL)
                    accepted.append({
                        "provenance": f"migrated->v{version} (0025 §4b-v: {ops_tag}; "
                                      f"{ledger_tag})"
                                      + (" [v10 shape inherited at v11 — specs/0001 I13c]" if version == 11 else ""),
                        "digest": sv._digest_of_identity(alt, version),
                        "objects": alt})
        c.close()
        # *(Historical: round 7's union across qualified runtimes. `0007` now
        # supports exactly one active build identity; this loop survives so the
        # attestation refusal below is exercised, and `0013`/S-Q7 own any real
        # widening.)* v8 regenerated the current version solely from
        # the runtime running the command, so qualifying a second runtime whose
        # DDL differs would mark it qualified while stores it creates were not
        # in MANIFESTS -- and regenerating there would delete the first
        # runtime's manifestation. Measured: an inserted foreign manifestation
        # was silently dropped.
        have = {a["digest"] for a in accepted}
        problems.extend(sv.artifact_problems())
        for rt in sv.qualified_runtimes():
            # Round 14 (non-blocking): the predicate was total and this loop
            # was not — `[42]` in the artifact raised AttributeError out of the
            # generator. CI failed either way, but a traceback is a worse
            # diagnostic than the problem statement sv.artifact_problems() already
            # recorded above.
            if not isinstance(rt, dict):
                continue
            # A record written under an older manifest algorithm describes a
            # different computation. It is **superseded, not fraudulent**: it
            # contributes nothing and is reported, but it does not block
            # regeneration -- otherwise bumping the algorithm deadlocks, since
            # the artifact can only be rewritten by a run that first refuses to
            # read it. Skipping is fail-closed: nothing it holds is accepted.
            if rt.get("manifest_algorithm") != sv.MANIFEST_ALGORITHM:
                print(f"note: runtime {rt.get('sqlite_version')!r} was recorded "
                      f"under manifest algorithm {rt.get('manifest_algorithm')}; "
                      f"re-run --runtime --write there to qualify it again")
                continue
            if sv.runtime_record_problems(rt):
                problems.append(f"runtime record for sqlite "
                                f"{rt.get('sqlite_version')!r} is invalid and "
                                f"contributes no accepted manifest: "
                                f"{sv.runtime_record_problems(rt)[0]}")
                continue
            # **Attestation, round 9 finding 1.** A record's objects agreeing
            # with its own digest proves internal consistency, not that the
            # claimed runtime produced them. The only record that may contribute
            # is one this process can REPRODUCE -- running the constructor here
            # and getting the same objects.
            if sv._identity_key(rt) != sv._identity_key(build_runtime_record()):
                print(f"note: runtime {rt.get('sqlite_version')!r} is recorded but "
                      f"not attested by this process; it contributes no accepted "
                      f"manifest until a job on that runtime regenerates it")
                continue
            for v in SCHEMAS:
                if rt["manifestations"][f"constructor v{v}"] != sv._constructor_objects(v):
                    problems.append(
                        f"runtime {rt.get('sqlite_version')!r} claims a v{v} "
                        f"manifestation this process does not reproduce")
            for prov, objs in (rt.get("manifestations") or {}).items():
                if not prov.endswith(f"v{version}") and prov != f"constructor v{version}":
                    continue
                d = sv._digest_of_identity(objs, version)
                if d in have:
                    continue
                have.add(d)
                accepted.append({
                    "provenance": f"{prov} @ sqlite {rt['sqlite_version']}",
                    "digest": d, "objects": objs})
        record = {"accepted": accepted}
        if version < SCHEMA_VERSION and str(version) in existing:
            if existing[str(version)] != record:
                problems.append(
                    f"version {version} is historical and regenerates differently. "
                    f"Historical manifests are immutable; a manifest-algorithm "
                    f"change needs a separately reviewed artifact migration.")
            out[str(version)] = existing[str(version)]
        else:
            out[str(version)] = record

    for key in existing:
        if key not in out:
            problems.append(
                f"version {key} is recorded but this build no longer declares it. "
                f"Deleting or renumbering a historical version is an error.")
            out[key] = existing[key]

    if problems and strict:
        raise SystemExit("\n".join(problems))
    return {"manifest_algorithm": sv.MANIFEST_ALGORITHM, "schema_version": SCHEMA_VERSION,
            "versions": out}


# --------------------------------------------------------------------------
# release probing


def _git(*a) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def _tags() -> list:
    return sorted((t for t in _git("tag").split() if t.startswith("v")),
                  key=lambda t: [int(x) for x in t.lstrip("v").split(".")])


def _probe_at(ref: str, work: pathlib.Path) -> dict:
    """Build a store with the code at `ref`. The creating code is that release's."""
    row = {"tag": ref, "commit": _git("rev-list", "-n1", ref),
           "on_disk_user_version": None, "store_schema_version": None,
           "digest": None, "result": None}
    wt = work / ref.replace("/", "_")
    if subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), ref],
                      cwd=ROOT, capture_output=True).returncode:
        row["result"] = "worktree failed"
        return row
    try:
        db = str(wt / "probe.db")
        r = subprocess.run(
            [sys.executable, "-c",
             f"from veracium.store.sqlite import SqliteStore; SqliteStore({db!r})"],
            cwd=wt, env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"},
            capture_output=True, text=True)
        if r.returncode:
            row["result"] = f"unbuildable: {r.stderr.strip().splitlines()[-1][:80]}"
            return row
        c = sqlite3.connect(db)
        row["on_disk_user_version"] = c.execute("PRAGMA user_version").fetchone()[0]
        row["_objects"] = {tuple(k.split(":", 1)): v
                           for k, v in identity(manifest(c)).items()}
        c.close()
        row["result"] = "ok"
        return row
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=ROOT, capture_output=True)


def _resolved(row: dict, records: dict, candidates=None) -> dict:
    objs = row.pop("_objects", {})
    v = resolve(objs, records, candidates)
    row["store_schema_version"] = v
    row["digest"] = None if v is None else digest(objs, v)
    return row


def releases(write: bool) -> int:
    records = build_version_artifact()["versions"]
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        head = _resolved(_probe_at("HEAD", work), records)
        rows = [_resolved(_probe_at(t, work), records) for t in _tags()]

    unknown = [r for r in rows if r["result"] == "ok" and r["store_schema_version"] is None]
    broken = [r for r in rows if r["result"] != "ok"]
    bad_stamp = [r for r in rows if r["result"] == "ok"
                 and r["on_disk_user_version"] not in (0, r["store_schema_version"])]
    for r in rows:
        v, st = r["store_schema_version"], r["on_disk_user_version"]
        mark = (r["result"] if r["result"] != "ok"
                else f"schema v{v}, " + ("unstamped (legacy)" if st == 0 else f"stamped {st}")
                if v is not None else "** UNKNOWN MANIFEST **")
        print(f"  {r['tag']:<10} {r['commit'][:12]}  {mark}")
    legacy = sorted({r["store_schema_version"] for r in rows
                     if r["on_disk_user_version"] == 0 and r["store_schema_version"]})
    print(f"\n{len(rows) - len(unknown) - len(broken)}/{len(rows)} resolve to a known "
          f"version · {len(broken)} unbuildable · legacy bases {legacy} · "
          f"sqlite {sqlite3.sqlite_version}")

    if write:
        GENERATED.mkdir(parents=True, exist_ok=True)
        sv.RELEASES.write_text(json.dumps({
            "manifest_algorithm": sv.MANIFEST_ALGORITHM,
            "head_digest": head["digest"],
            "head_schema_version": head["store_schema_version"],
            "legacy_base_versions": legacy,
            "releases": rows,
        }, indent=2) + "\n")
        sv.VERSIONS.write_text(json.dumps(build_version_artifact(), indent=2) + "\n")
        POLICY_ARTIFACT.write_text(json.dumps(
            {str(v): declared_policies(v) for v in sorted(SCHEMAS)}, indent=2) + "\n")
        if write_runtime() != 0:
            print("runtime evidence was not written", file=sys.stderr)
            return 1
        print(f"wrote {sv.RELEASES.name}, {sv.VERSIONS.name}, {POLICY_ARTIFACT.name}")
    return 1 if (unknown or broken or bad_stamp) else 0


def check() -> int:
    if subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                      capture_output=True).returncode:
        print("--check needs a git checkout: it rebuilds a store from every "
              "released tag. An extracted archive has no git metadata.",
              file=sys.stderr)
        return 2
    if not sv.RELEASES.exists():
        print(f"{sv.RELEASES.name} missing — run --releases --write", file=sys.stderr)
        return 1
    stored = json.loads(sv.RELEASES.read_text())
    generated = build_version_artifact()
    records = generated["versions"]
    bad = []

    if stored.get("manifest_algorithm") != sv.MANIFEST_ALGORITHM:
        bad.append(f"manifest algorithm: artifact {stored.get('manifest_algorithm')} "
                   f"vs build {sv.MANIFEST_ALGORITHM}")
    if not sv.VERSIONS.exists():
        bad.append(f"{sv.VERSIONS.name} is missing — it is load-bearing evidence and "
                   f"its absence must fail, not pass silently (round 11)")
    elif json.loads(sv.VERSIONS.read_text()) != generated:
        bad.append("schema_versions.json does not match what this build generates")
    if POLICY_ARTIFACT.exists():
        want = {str(v): declared_policies(v) for v in sorted(SCHEMAS)}
        if json.loads(POLICY_ARTIFACT.read_text()) != want:
            bad.append("schema_policy.json disagrees with the registry's policies")
    else:
        bad.append(f"{POLICY_ARTIFACT.name} missing")
    if not sv.runtime_supported():
        bad.append(f"sqlite {sqlite3.sqlite_version} is not a qualified runtime "
                   f"(see {sv.RUNTIMES.name}); 0007 §4a-viii refuses it")
    # Every stored record, not merely the one this process matches: an invalid
    # record beside a valid one still feeds the accepted set.
    # The release check is where stale-record diagnostics belong (round 13,
    # finding 3): superseded or duplicate leftovers do not disqualify the
    # runtime at open time, but the repository must be cleaned before release.
    seen_stale = set()
    for rt in sv.qualified_runtimes():
        if not isinstance(rt, dict):
            bad.append(f"runtime artifact contains a {type(rt).__name__}")
            continue
        if rt.get("manifest_algorithm") != sv.MANIFEST_ALGORITHM:
            key = (rt.get("sqlite_version"), rt.get("source_id"),
                   rt.get("manifest_algorithm"))
            dup = " (duplicate)" if key in seen_stale else ""
            seen_stale.add(key)
            bad.append(f"runtime {rt.get('sqlite_version')!r} was recorded under "
                       f"manifest algorithm {rt.get('manifest_algorithm')}, build "
                       f"uses {sv.MANIFEST_ALGORITHM} — re-qualify or remove it{dup}")
            continue
        for p in sv.runtime_record_problems(rt):
            bad.append(f"runtime {rt.get('sqlite_version')!r}: {p}")

    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        head = _resolved(_probe_at("HEAD", work), records)
        fresh = {r["tag"]: _resolved(r, records)
                 for r in (_probe_at(t, work) for t in _tags())}

    # every AUTHORITATIVE field re-derived, not just the version
    for row in stored["releases"]:
        now = fresh.get(row["tag"])
        if now is None:
            bad.append(f"{row['tag']}: recorded but no longer a tag")
            continue
        for field in AUTHORITATIVE:
            if now.get(field) != row.get(field):
                bad.append(f"{row['tag']}: {field} recorded {row.get(field)!r}, "
                           f"re-derived {now.get(field)!r}")
        if now.get("result") != "ok":
            bad.append(f"{row['tag']}: freshly probed result "
                       f"{now.get('result')!r}")
    for t in _tags():
        if t not in {r["tag"] for r in stored["releases"]}:
            bad.append(f"{t}: released since the artifact was generated")

    # SUMMARY fields recomputed from the authoritative ones
    want_legacy = sorted({r["store_schema_version"] for r in fresh.values()
                          if r["on_disk_user_version"] == 0 and r["store_schema_version"]})
    if stored.get("legacy_base_versions") != want_legacy:
        bad.append(f"legacy_base_versions recorded {stored.get('legacy_base_versions')}, "
                   f"recomputed {want_legacy}")
    if stored.get("head_digest") != head["digest"]:
        bad.append("head_digest does not match a freshly built HEAD")
    if stored.get("head_schema_version") != head["store_schema_version"]:
        bad.append(f"head_schema_version recorded {stored.get('head_schema_version')}, "
                   f"re-derived {head['store_schema_version']}")

    for b in bad:
        print(b, file=sys.stderr)
    if bad:
        print(f"\n{len(bad)} problem(s) — run --releases --write", file=sys.stderr)
        return 1
    print(f"evidence current — {len(stored['releases'])} releases, legacy bases "
          f"{want_legacy}, HEAD at v{head['store_schema_version']}, "
          f"sqlite {sqlite3.sqlite_version} qualified")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--releases", action="store_true")
    ap.add_argument("--runtime", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.releases:
        return releases(a.write)
    if a.runtime:
        if a.write:
            return write_runtime()
        print(json.dumps(build_runtime_record(), indent=2))
        print("qualified:", sv.runtime_supported())
        return 0
    if a.check:
        return check()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
