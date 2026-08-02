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

from schema_migrations import MIGRATIONS, apply_migration, chain, validate_registry
from schema_model import (GENERATED, POLICY_ARTIFACT, ROOT, SCHEMA_VERSION, SCHEMAS,
                          create, declared_policies, digest, identity, manifest,
                          resolve)

RELEASES = GENERATED / "legacy_stores.json"
VERSIONS = GENERATED / "schema_versions.json"
RUNTIMES = GENERATED / "sqlite_runtimes.json"

MANIFEST_ALGORITHM = 5

# Which recorded fields are authoritative (re-derived and compared), which are
# summaries (recomputed from the authoritative ones), and which are notes.
AUTHORITATIVE = ("tag", "commit", "on_disk_user_version", "store_schema_version",
                 "digest")
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
    try:
        c.execute("CREATE TABLE s (a) STRICT")
        out["strict_tables"] = True
    except sqlite3.DatabaseError:
        out["strict_tables"] = False
    out["stores_ddl_verbatim"] = bool(
        c.execute("SELECT sql FROM sqlite_master WHERE name='t'").fetchone())
    c.close()
    return out


def runtime_identity() -> dict:
    return {"sqlite_version": sqlite3.sqlite_version,
            "source_id": sqlite3.connect(":memory:").execute(
                "SELECT sqlite_source_id()").fetchone()[0],
            "features": _feature_probes()}


def qualified_runtimes() -> list:
    return json.loads(RUNTIMES.read_text())["runtimes"] if RUNTIMES.exists() else []


def runtime_supported() -> bool:
    """**Derived from the evidence artifact, never from a hand-edited tuple.**

    v6's `TESTED_SQLITE` was editable in place: adding `"3.99.0"` made an
    untested runtime supported with no manifest, probe or CI result behind it
    (round 5, measured). Qualification now means *a recorded runtime whose
    source id and feature probes match, and whose recorded constructor digests
    reproduce here*."""
    me = runtime_identity()
    for r in qualified_runtimes():
        if (r["sqlite_version"] == me["sqlite_version"]
                and r["source_id"] == me["source_id"]
                and r["features"] == me["features"]):
            return all(_constructor_digest(int(v)) == d
                       for v, d in r["constructor_digests"].items())
    return False


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
    out, problems = {}, list(validate_registry())

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
            accepted.append({"provenance": f"migration v{base}->v{version}",
                             "digest": digest(manifest(mc), version),
                             "objects": identity(manifest(mc))})
            mc.close()
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
        return frozenset({SCHEMA_VERSION})
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
        me = runtime_identity()
        me["constructor_digests"] = {str(v): _constructor_digest(v) for v in sorted(SCHEMAS)}
        others = [r for r in qualified_runtimes()
                  if r["source_id"] != me["source_id"]]
        RUNTIMES.write_text(json.dumps({"runtimes": others + [me]}, indent=2) + "\n")
        print(f"wrote {RELEASES.name}, {VERSIONS.name}, {POLICY_ARTIFACT.name}, "
              f"{RUNTIMES.name}")
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
        if row.get("result") != "ok":
            bad.append(f"{row['tag']}: recorded result {row.get('result')!r}")
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
        print(json.dumps(runtime_identity(), indent=2))
        print("qualified:", runtime_supported())
        return 0
    if a.check:
        return check()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
