#!/usr/bin/env python3
"""SR2-01 (shipped-changes round 2): two stores whose wiki was cached by RELEASED code before 0012-v2, frozen as
files so the upgrade regression runs from a git-less export.

The reviewer: "an existing wiki cache keeps serving the former globally worded empty header after upgrade", and its
standing request: "future changes to code-owned cached prose should include a persistent-store upgrade fixture, not
only fresh-store tests". Each store is WRITTEN BY THE TAG'S OWN src (git archive of the tag, imported in a child
process with the import origin asserted), never forged through today's store:

    legacy-empty-wiki-v0.31.0.sqlite   round 1's pin: the cached body is "(no verified facts yet)" plus its marker
    legacy-empty-wiki-v0.27.1.sqlite   before 2f3899be: the compiler was CALLED on an empty input; a stub reply
                                       stands in for the model ("Document is empty pending user information", the
                                       body research's adoption probe 3 recorded, 2026-10-29)

Both: one third-party claim ("The user lives in Berlin.") and one recall at the default wiki configuration, so the
wiki row is the empty-input compile under the default policy digest db45cc67acf9f302 (the same at every release
from v0.27.1 to v0.31.0). The FACTS the cells read from each store are written to legacy-empty-wiki.json; a rebuild
must reproduce the facts, not the bytes (sqlite pages are not a contract).

    .venv/bin/python specs/evidence/sr2-01/build_legacy_wiki_stores.py --write
        # needs git, the two tags, and an interpreter with veracium's dependencies (the child imports the TAG's src)
"""
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FACTS = HERE / "legacy-empty-wiki.json"
LEGACY = {
    "v0.31.0": {"body": "(no verified facts yet)", "compile_reply": None},
    "v0.27.1": {"body": "Document is empty pending user information",
                "compile_reply": "Document is empty pending user information"},
}

CHILD = r'''
import json, sys
src, db, reply = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
sys.path.insert(0, src)
import veracium
assert veracium.__file__.startswith(src), veracium.__file__
from veracium import Memory, MemoryConfig, EvidenceAuthor
class Stub:
    def __init__(self):
        self.compile_calls = 0
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            return json.dumps({"triples": [{"subject": "user", "relation": "located_at", "object": "Berlin",
                                            "volatility": "durable"}], "episode": "The user lives in Berlin.",
                               "instructions": []})
        self.compile_calls += 1
        assert reply is not None, "this release must not call the model on an empty input"
        return reply
llm = Stub()
m = Memory(llm=llm, config=MemoryConfig(db_path=db, require_source_id=False))
m.remember("u", "The user lives in Berlin.", date="2026-11-01", author=EvidenceAuthor.THIRD_PARTY)
m.recall("u", "where does the user live", semantic=False)
m.close()
print(json.dumps({"veracium": veracium.__file__, "compile_calls": llm.compile_calls}))
'''


def _strict_pairs(pairs):
    """0026-EVIDENCE-R8-1: a duplicate member refuses at parse (json.loads keeps the LAST duplicate)."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON member {k!r}")
        out[k] = v
    return out


def facts(db: pathlib.Path) -> dict:
    """What a cell asserts about a frozen store, read from the store itself."""
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        user_version = c.execute("PRAGMA user_version").fetchone()[0]
        rows = c.execute("SELECT user_id, text, store_version FROM wiki").fetchall()
    finally:
        c.close()
    assert len(rows) == 1, rows
    uid, wiki, at = rows[0]
    assert wiki.startswith("\x00policy:"), wiki[:40]
    head, _, body = wiki.partition("\n")
    return {"user_id": uid, "policy_digest": head[len("\x00policy:"):], "body_first_line": body.split("\n", 1)[0],
            "body": body, "version_at_compile": at, "user_version": user_version}


def build(tag: str, out: pathlib.Path) -> dict:
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", f"{tag}^{{commit}}"], capture_output=True,
                            text=True, check=True).stdout.strip()
    with tempfile.TemporaryDirectory() as td:
        arc = subprocess.run(["git", "-C", str(ROOT), "archive", commit, "src"], capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", td], input=arc.stdout, check=True)
        db = pathlib.Path(td) / "store.sqlite"
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", VERACIUM_FORBID_NETWORK="1")
        r = subprocess.run([sys.executable, "-I", "-c", CHILD, str(pathlib.Path(td) / "src"), str(db),
                            json.dumps(LEGACY[tag]["compile_reply"])], capture_output=True, text=True, env=env)
        if r.returncode:
            raise SystemExit(f"{tag}: the child failed:\n{r.stdout}{r.stderr}")
        child = json.loads(r.stdout.strip().splitlines()[-1], object_pairs_hook=_strict_pairs)
        for side in ("-wal", "-shm"):
            assert not (db.parent / (db.name + side)).exists(), f"{tag}: {side} left beside the store"
        f = facts(db)
        assert f["body_first_line"] == LEGACY[tag]["body"], (tag, f["body_first_line"])
        out.write_bytes(db.read_bytes())
    return {"tag": tag, "commit": commit, "compile_calls_at_write": child["compile_calls"], **f}


def main() -> int:
    if "--write" not in sys.argv:
        print(__doc__)
        return 2
    record = {}
    for tag in LEGACY:
        record[tag] = build(tag, HERE / f"legacy-empty-wiki-{tag}.sqlite")
        print(f"{tag}: {record[tag]['commit'][:12]} digest {record[tag]['policy_digest']} "
              f"body {record[tag]['body_first_line']!r} compile calls {record[tag]['compile_calls_at_write']}")
    FACTS.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
