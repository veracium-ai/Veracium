#!/usr/bin/env python3
"""Generated evidence: what every released version built, and on what runtime.

Separated from the schema kernel because git probing and artifact presentation
should not sit inside the trust boundary (round 5). This module *uses*
`schema_model`; nothing in `schema_model` depends on it.

  `--releases --write`  build a store with every released tag's own code and
                        record tag, commit sha, on-disk stamp, resolved version
                        and digest.
  `--runtime --write`   record this SQLite runtime's identity and feature probes.
  `--check`             re-derive every authoritative field and compare.
                        **Needs a git checkout**; exits 2 in an extracted archive.

**Every field is classified.** v6 said the gate re-derived everything and it did
not: an artifact with `head_digest="BAD"`, `head_schema_version=999`,
`legacy_base_versions=[999]`, `sqlite_version="0.0.0"` and every release
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

from schema_migrations import (MIGRATIONS, apply_migration, chain,
                               destination_problems, validate_registry)
from schema_model import (GENERATED, POLICY_ARTIFACT, ROOT, SCHEMA_VERSION, SCHEMAS,
                          create, declared_policies, digest, identity, manifest,
                          resolve)

RELEASES = GENERATED / "legacy_stores.json"
VERSIONS = GENERATED / "schema_versions.json"
RUNTIMES = GENERATED / "sqlite_runtimes.json"

MANIFEST_ALGORITHM = 7

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


def _feature_probes() -> dict:
    """Behaviours the manifest actually depends on.

    A version number names a release, not a build. Two builds of `3.45.1` can
    differ in compile options, authorizer availability and DDL support — all of
    which the exact-match model leans on (round 5, finding 6)."""
    c = sqlite3.connect(":memory:")
    out = {}
    try:
        c.execute("CREATE TABLE t (a TEXT, b TEXT GENERATED ALWAYS AS (a) VIRTUAL)")
        out["generated_columns"] = True
    except sqlite3.DatabaseError:
        out["generated_columns"] = False
    try:
        c.set_authorizer(lambda *a: sqlite3.SQLITE_OK)
        c.set_authorizer(None)
        out["authorizer"] = True
    except Exception:
        out["authorizer"] = False
    # Round 7, finding 5: this probe used `CREATE TABLE s (a) STRICT`, which is
    # invalid -- a strict table's column must declare a datatype. It therefore
    # recorded `strict_tables: False` on a runtime that fully supports them.
    # Measured on 3.46.1. A probe that fails for the wrong reason is worse than
    # no probe: it records a false property as evidence.
    try:
        c.execute("CREATE TABLE s (a TEXT) STRICT")
        out["strict_tables"] = True
    except sqlite3.DatabaseError:
        out["strict_tables"] = False
    # ...and this one only checked that a row existed, which cannot establish
    # that DDL is stored verbatim. Submit distinctive text and compare it.
    # Writing this probe found that "verbatim" was too strong a word for what
    # the manifest actually needs. SQLite normalises the whitespace *before* the
    # object name -- `CREATE TABLE  vp` is stored as `CREATE TABLE vp` -- while
    # preserving the body exactly. The property §4a depends on is body
    # preservation, which is why two-space and one-space CHECK literals produce
    # different digests. Probe the property, not the slogan.
    marker = ("CREATE TABLE verbatim_probe ( a   TEXT ,\n"
              "  b TEXT DEFAULT 'x  y' , c TEXT CHECK(c <> 'p  q') )")
    c.execute(marker)
    stored = c.execute(
        "SELECT sql FROM sqlite_master WHERE name='verbatim_probe'").fetchone()[0]
    out["preserves_ddl_body"] = stored[stored.index("("):] == marker[marker.index("("):]
    # The authorizer probe checked only that `set_authorizer` was callable. What
    # migration confinement actually relies on is that these specific actions
    # are denied, so exercise them.
    from schema_migrations import Migration, apply_migration
    c.execute("BEGIN IMMEDIATE")
    denied = []
    for stmt in ("COMMIT", "END", "RELEASE s", "PRAGMA writable_schema=ON",
                 "CREATE TEMP TABLE tmp_probe (x)"):
        try:
            apply_migration(c, Migration(0, 0, (stmt,)))
        except Exception:
            denied.append(stmt)
    out["authorizer_denies_all"] = len(denied) == 5
    try:
        c.execute("ROLLBACK")
    except sqlite3.DatabaseError:
        pass
    # `table_xinfo` must expose a generated column with a nonzero hidden flag --
    # the property §4a-ii depends on.
    out["xinfo_exposes_generated"] = any(
        r[1] == "b" and int(r[6]) != 0
        for r in c.execute("SELECT * FROM pragma_table_xinfo('t')"))
    c.close()
    return out


def runtime_identity() -> dict:
    return {"sqlite_version": sqlite3.sqlite_version,
            "source_id": sqlite3.connect(":memory:").execute(
                "SELECT sqlite_source_id()").fetchone()[0],
            "features": _feature_probes()}


def qualified_runtimes() -> list:
    return json.loads(RUNTIMES.read_text())["runtimes"] if RUNTIMES.exists() else []


def runtime_record_problems(r: dict) -> list:
    """Whether a recorded runtime is complete enough to qualify anything.

    **Round 6, finding 4: an empty `constructor_digests` qualified vacuously**,
    because `all(...)` over an empty mapping is `True`. Measured. Completeness
    is now a precondition, and the key set must *equal* the declared schema
    versions rather than being whatever happened to be recorded."""
    problems = []
    for field in ("sqlite_version", "source_id", "features", "constructor_digests",
                  "migration_digests", "manifest_algorithm", "schema_version"):
        if field not in r:
            problems.append(f"runtime record is missing {field!r}")
    if problems:
        return problems
    if r["manifest_algorithm"] != MANIFEST_ALGORITHM:
        problems.append(f"runtime record uses manifest algorithm "
                        f"{r['manifest_algorithm']}, build uses {MANIFEST_ALGORITHM}")
    if r["schema_version"] != SCHEMA_VERSION:
        problems.append(f"runtime record is for schema version {r['schema_version']}, "
                        f"build declares {SCHEMA_VERSION}")
    want = {str(v) for v in SCHEMAS}
    if set(r["constructor_digests"]) != want:
        problems.append(f"runtime record covers versions "
                        f"{sorted(r['constructor_digests'])}, build declares "
                        f"{sorted(want)}")
    if not r["constructor_digests"]:
        problems.append("runtime record has no constructor digests")
    if not r["features"]:
        problems.append("runtime record has no feature probes")
    # Round 7, finding 2: the constructor key set was validated and the
    # migration key set was not, so `{}` and `{"999": "bad"}` both passed and
    # `runtime_supported()` then checked whichever entries happened to exist.
    want_paths = set(migration_paths())
    if set(r["migration_digests"]) != want_paths:
        problems.append(f"runtime record covers migration paths "
                        f"{sorted(r['migration_digests'])}, build declares "
                        f"{sorted(want_paths)}")
    for name, must in (("authorizer_denies_all", True),
                       ("preserves_ddl_body", True),
                       ("xinfo_exposes_generated", True)):
        if r["features"].get(name) is not must:
            problems.append(f"runtime fails a required behaviour: {name}")
    return problems


def runtime_supported() -> bool:
    """**Derived from the evidence artifact, never from a hand-edited tuple.**

    Qualification means: a *complete* recorded runtime whose version, source id
    and feature probes match this process, and whose recorded constructor **and
    migration-path** digests all reproduce here. Migration digests are included
    because DDL rewriting is the reason a version has multiple accepted
    manifests in the first place — a runtime that agrees on constructors could
    still disagree on an `ALTER` path."""
    me = runtime_identity()
    for r in qualified_runtimes():
        if runtime_record_problems(r):
            continue
        if not (r["sqlite_version"] == me["sqlite_version"]
                and r["source_id"] == me["source_id"]
                and r["features"] == me["features"]):
            continue
        if any(_constructor_digest(int(v)) != d
               for v, d in r["constructor_digests"].items()):
            return False
        here = migration_paths()
        return all(here[k]["digest"] == d for k, d in r["migration_digests"].items())
    return False


def migration_paths() -> dict:
    """Every declared path, keyed individually.

    **Round 7, finding 3: v8 keyed by destination version and returned after the
    first viable base**, so only one path per destination could ever be
    recorded — while the whole reason migration digests exist is that different
    bases can produce different exact output at the same destination."""
    out = {}
    for to_version in sorted(SCHEMAS):
        for base in sorted(v for v in SCHEMAS if v < to_version):
            try:
                steps = chain(base, to_version)
            except KeyError:
                continue
            c = sqlite3.connect(":memory:")
            create(c, base)
            for mig in steps:
                apply_migration(c, mig)
            out[f"v{base}:constructor->v{to_version}"] = {
                "digest": digest(manifest(c), to_version),
                "objects": identity(manifest(c)),
                "to_version": to_version}
            c.close()
    return out


def build_runtime_record() -> dict:
    me = runtime_identity()
    me["manifest_algorithm"] = MANIFEST_ALGORITHM
    me["schema_version"] = SCHEMA_VERSION
    me["constructor_digests"] = {str(v): _constructor_digest(v) for v in sorted(SCHEMAS)}
    paths = migration_paths()
    me["migration_digests"] = {k: v["digest"] for k, v in paths.items()}
    # Full object records, not only digests: round 7, finding 4 -- a second
    # qualified runtime's manifestations must be reconstructible, and an
    # object-level `diff` cannot be built from a digest.
    me["manifestations"] = {
        **{f"constructor v{v}": _constructor_objects(v) for v in sorted(SCHEMAS)},
        **{k: v["objects"] for k, v in paths.items()}}
    return me


def _digest_of_identity(objs: dict, version: int) -> str:
    """Digest a recorded identity mapping without rebuilding the database."""
    from schema_model import rebuildable_keys
    import hashlib as _h
    skip = rebuildable_keys(version)
    scoped = {k: v for k, v in objs.items() if tuple(k.split(":", 1)) not in skip}
    return _h.sha256(
        json.dumps(scoped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _constructor_objects(version: int) -> dict:
    c = sqlite3.connect(":memory:")
    create(c, version)
    o = identity(manifest(c))
    c.close()
    return o


def write_runtime(force: bool = False) -> int:
    """Record **this** runtime as qualified. Round 6, finding 5: `--runtime
    --write` was documented and did nothing — the flag was ignored on that path,
    so the stated workflow for qualifying a second runtime did not exist."""
    rec = build_runtime_record()
    problems = runtime_record_problems(rec)
    if problems and not force:
        for p in problems:
            print(p, file=sys.stderr)
        print("refusing to write incomplete runtime evidence", file=sys.stderr)
        return 1
    others = [r for r in qualified_runtimes()
              if (r.get("source_id"), r.get("sqlite_version")) !=
                 (rec["source_id"], rec["sqlite_version"])]
    GENERATED.mkdir(parents=True, exist_ok=True)
    RUNTIMES.write_text(json.dumps({"runtimes": others + [rec]}, indent=2) + "\n")
    print(f"recorded {rec['sqlite_version']} ({rec['source_id'][:20]}…) — "
          f"{len(others) + 1} qualified runtime(s)")
    return 0


def _constructor_digest(version: int) -> str:
    c = sqlite3.connect(":memory:")
    create(c, version)
    d = digest(manifest(c), version)
    c.close()
    return d


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
    existing = (json.loads(VERSIONS.read_text()).get("versions", {})
                if VERSIONS.exists() else {})
    from schema_model import validate_schema_registry
    out, problems = {}, validate_schema_registry() + list(validate_registry())

    for version in sorted(SCHEMAS):
        accepted = []
        c = sqlite3.connect(":memory:")
        create(c, version)
        accepted.append({"provenance": f"constructor v{version}",
                         "digest": digest(manifest(c), version),
                         "objects": identity(manifest(c))})
        c.close()
        # Single-step model: every accepted manifest of the source version must
        # migrate, so paths are generated per accepted source rather than once.
        for base in sorted(v for v in SCHEMAS if v < version):
            try:
                steps = chain(base, version)
            except KeyError:
                continue
            mc = sqlite3.connect(":memory:")
            create(mc, base)
            for mig in steps:
                apply_migration(mc, mig)
            # **The destination contract is independent of what the migration
            # produced** (round 6, finding 1). Without this an empty migration
            # authorises its own broken output as a valid destination.
            dp = destination_problems(manifest(mc), version)
            if dp:
                problems.extend(f"migration v{base}->v{version}: {p}" for p in dp)
            else:
                accepted.append({"provenance": f"migration v{base}->v{version}",
                                 "digest": digest(manifest(mc), version),
                                 "objects": identity(manifest(mc))})
            mc.close()
        # **Round 7, finding 4: accepted manifests are the union across every
        # qualified runtime.** v8 regenerated the current version solely from
        # the runtime running the command, so qualifying a second runtime whose
        # DDL differs would mark it qualified while stores it creates were not
        # in MANIFESTS -- and regenerating there would delete the first
        # runtime's manifestation. Measured: an inserted foreign manifestation
        # was silently dropped.
        have = {a["digest"] for a in accepted}
        for rt in qualified_runtimes():
            for prov, objs in (rt.get("manifestations") or {}).items():
                if not prov.endswith(f"v{version}") and prov != f"constructor v{version}":
                    continue
                d = _digest_of_identity(objs, version)
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
    return {"manifest_algorithm": MANIFEST_ALGORITHM, "schema_version": SCHEMA_VERSION,
            "versions": out}


def legacy_base_versions() -> frozenset:
    """Versions whose release evidence shows a genuinely **unstamped** store.

    The only candidates version-zero resolution may try (round 5, finding 3)."""
    if not RELEASES.exists():
        # **Fails closed** (round 6, finding 7). v7 returned {SCHEMA_VERSION},
        # which silently authorised adoption using the very evidence that was
        # missing. No verified legacy artifact means no adoption candidates.
        return frozenset()
    return frozenset(
        r["store_schema_version"] for r in json.loads(RELEASES.read_text())["releases"]
        if r.get("on_disk_user_version") == 0 and r.get("store_schema_version"))


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
        RELEASES.write_text(json.dumps({
            "manifest_algorithm": MANIFEST_ALGORITHM,
            "head_digest": head["digest"],
            "head_schema_version": head["store_schema_version"],
            "legacy_base_versions": legacy,
            "releases": rows,
        }, indent=2) + "\n")
        VERSIONS.write_text(json.dumps(build_version_artifact(), indent=2) + "\n")
        POLICY_ARTIFACT.write_text(json.dumps(
            {str(v): declared_policies(v) for v in sorted(SCHEMAS)}, indent=2) + "\n")
        if write_runtime() != 0:
            print("runtime evidence was not written", file=sys.stderr)
            return 1
        print(f"wrote {RELEASES.name}, {VERSIONS.name}, {POLICY_ARTIFACT.name}")
    return 1 if (unknown or broken or bad_stamp) else 0


def check() -> int:
    if subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                      capture_output=True).returncode:
        print("--check needs a git checkout: it rebuilds a store from every "
              "released tag. An extracted archive has no git metadata.",
              file=sys.stderr)
        return 2
    if not RELEASES.exists():
        print(f"{RELEASES.name} missing — run --releases --write", file=sys.stderr)
        return 1
    stored = json.loads(RELEASES.read_text())
    generated = build_version_artifact()
    records = generated["versions"]
    bad = []

    if stored.get("manifest_algorithm") != MANIFEST_ALGORITHM:
        bad.append(f"manifest algorithm: artifact {stored.get('manifest_algorithm')} "
                   f"vs build {MANIFEST_ALGORITHM}")
    if VERSIONS.exists() and json.loads(VERSIONS.read_text()) != generated:
        bad.append("schema_versions.json does not match what this build generates")
    if POLICY_ARTIFACT.exists():
        want = {str(v): declared_policies(v) for v in sorted(SCHEMAS)}
        if json.loads(POLICY_ARTIFACT.read_text()) != want:
            bad.append("schema_policy.json disagrees with the registry's policies")
    else:
        bad.append(f"{POLICY_ARTIFACT.name} missing")
    if not runtime_supported():
        bad.append(f"sqlite {sqlite3.sqlite_version} is not a qualified runtime "
                   f"(see {RUNTIMES.name}); 0007 §4a-viii refuses it")

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
        print("qualified:", runtime_supported())
        return 0
    if a.check:
        return check()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
