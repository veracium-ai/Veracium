#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0018_rungs_t5.py::test_each_rung_s_digest_is_its_vector
"""I36's digest vectors: each rung's entry list, preimage (hex) and digest, in digest_vectors.json. `--write` regenerates the file from the
tree; `--check` compares. The file FREEZES the preimages: 0013 §5g.1's grammar is frozen, so moving one is a reviewed event."""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "src"))
import veracium.store.migration as mig  # noqa: E402
import veracium.store.schema_version as sv  # noqa: E402


DIRECT_BASES = (1, 4, 13)


def vectors() -> dict:
    rungs = {}
    for b in range(sv.FIRST_MIGRATABLE, sv.SCHEMA_VERSION):
        pre = mig.plan_preimage(b, b + 1)
        rungs[str(b)] = {"to": b + 1, "digest": hashlib.sha256(pre).hexdigest(), "preimage": pre.hex(),
                         "entries": [[e.kind, *map(str, mig.preimage_fields(e))] for e in mig.plan(b, b + 1)]}
    # 0013 §5g.1: a guard decides membership, so steps of two different rungs meet only in a direct plan, and no rung's digest orders them
    direct = {str(b): [[e.kind, *map(str, mig.preimage_fields(e))] for e in mig.plan(b, sv.SCHEMA_VERSION)] for b in DIRECT_BASES}
    return {"grammar": "0018-rung-steps-v1", "rungs": rungs, "direct": direct}


def main(argv) -> int:
    path = HERE / "digest_vectors.json"
    text = json.dumps(vectors(), indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        path.write_text(text)
        print(f"wrote {path.name}")
        return 0
    same = path.read_text() == text
    print("vectors current" if same else "vectors STALE")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
