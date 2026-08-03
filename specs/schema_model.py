#!/usr/bin/env python3
"""The 0007 schema kernel — now a re-export of the PRODUCTION module.

The kernel moved to `veracium.store.schema_version` when `0007` was accepted
and implemented: the shared-production-boundary rule (rounds 6 and 8) says the
evidence generator must use the same declarations the store executes, and a
shipped package cannot import from `specs/`. What stays here is evidence-only:
the reviewed policy artifact and the registry-conformance check.

With the product schema now DERIVED from the registry (`sqlite.py`'s `_SCHEMA`
is generated from `SCHEMA_V1`), `registry_conformance` stops guarding a second
hand-written copy and instead proves the derivation and the policy artifact
still agree — the duplication rounds 5–9 kept flagging is gone.
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from veracium.store.schema_version import (  # noqa: E402,F401
    KINDS, POLICIES, REBUILDABLE, REBUILDABLE_KINDS, REQUIRED, SCHEMA_V1,
    SCHEMA_VERSION, SCHEMAS, SchemaObject, create, digest, drift, identity,
    manifest, rebuildable_keys, resolve, validate_schema_registry)

GENERATED = ROOT / "specs" / "generated"
POLICY_ARTIFACT = GENERATED / "schema_policy.json"
"""The independently reviewed policy record — still evidence-side. A policy
decides digest exclusion, drift repair and candidate matching; it cannot be
self-certifying (round 5), so changing it stays a reviewable diff here."""


def declared_policies(version: int = SCHEMA_VERSION) -> dict:
    return {f"{o.kind}:{o.name}": o.policy for o in SCHEMAS[version]}


def reviewed_policies(version: int = SCHEMA_VERSION) -> dict | None:
    if not POLICY_ARTIFACT.exists():
        return None
    return json.loads(POLICY_ARTIFACT.read_text()).get(str(version))


def registry_conformance(version: int = SCHEMA_VERSION) -> list:
    """Differences between the registry and the product schema. Empty = conformant.

    The product `_SCHEMA` is now DERIVED from this registry (`0007` accepted),
    so the hand-written second copy this check used to guard no longer exists.
    What it still proves: the derived text round-trips through SQLite to the
    same objects the registry constructs (a derivation bug would show here),
    and the reviewed policy artifact agrees with the registry — a policy
    decides digest exclusion, drift repair and candidate matching, so it stays
    a second, reviewable declaration (round 5)."""
    from veracium.store.sqlite import _SCHEMA
    pconn = sqlite3.connect(":memory:")
    pconn.executescript(_SCHEMA)
    rconn = sqlite3.connect(":memory:")
    create(rconn, version)
    prod, reg = identity(manifest(pconn)), identity(manifest(rconn))
    problems = [f"{k}: registry {reg.get(k)!r} != product {prod.get(k)!r}"
                for k in sorted(set(prod) | set(reg)) if prod.get(k) != reg.get(k)]
    if drift(manifest(rconn), version):
        problems.append(f"registry drifts against itself: "
                        f"{drift(manifest(rconn), version)}")
    reviewed = reviewed_policies(version)
    if reviewed is None:
        problems.append(f"{POLICY_ARTIFACT.name} has no record for version {version}")
    elif reviewed != declared_policies(version):
        for k in sorted(set(reviewed) | set(declared_policies(version))):
            if reviewed.get(k) != declared_policies(version).get(k):
                problems.append(f"policy {k}: registry says "
                                f"{declared_policies(version).get(k)!r}, reviewed "
                                f"artifact says {reviewed.get(k)!r}")
    pconn.close()
    rconn.close()
    return problems
