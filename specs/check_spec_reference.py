#!/usr/bin/env python3
"""Require a spec reference on commits that touch the trust surface.

`PROCESS.md` says a change to stored state, its semantics, its trust or
disclosure classes, its lifecycle, or how it is selected for recall needs a
spec. That is a rule in prose, and this week taught us repeatedly that a rule
which is only prose is a rule that gets skipped under time pressure — so this
turns it into a check.

A commit touching those files must carry a trailer:

    Spec: specs/0007-generated-content-trust-class.md
    Spec: none (docs-only change to a guarded file)
    Spec: none (hotfix — GHSA-xxxx, retrospective review per PROCESS.md)

The escape hatch is deliberate and deliberately *visible*: the security-hotfix
carve-out exists because holding the 0.4.1 advisory fix for review would have
been the wrong call, and a process that cannot say so is one people route
around. Making the exemption a greppable line in history is the difference
between an exception and an erosion.

Usage:  check_spec_reference.py [<commit-range>]     (default: origin/main..HEAD)
"""

from __future__ import annotations

import re
import subprocess
import sys

# Files whose semantics the process governs. Deliberately narrow: this is the
# trust surface, not "important files". Widening it costs nothing but noise,
# and a noisy gate is one people learn to bypass.
GUARDED = (
    "src/veracium/schema.py",       # trust classes, field contracts
    "src/veracium/graph.py",        # supersession, absorption, recall selection
    "src/veracium/ingest.py",       # disclosure routing at write time
    "src/veracium/lifecycle.py",    # expiry, staleness, liveness
    "src/veracium/gate.py",         # what may be asserted
    "src/veracium/portability.py",  # what stored state means across a boundary
    # Added after review found the first list missed three surfaces that change
    # trust behaviour without touching the obvious files:
    "src/veracium/__init__.py",     # confirm() sets valid_from and is the
                                    # sanctioned exit from needs_confirmation;
                                    # correct() writes a superseding edge
    "src/veracium/store/sqlite.py", # edges() defaults to active_only=True, and
                                    # that default is load-bearing for every
                                    # caller — it is what keeps T1 absorption
                                    # from re-touching an invalidated prior
    "src/veracium/proactive.py",    # disclosure-gated, and injects text into
                                    # model context with NO user turn: a
                                    # regression here volunteers use_only
                                    # material nobody asked for
    "src/veracium/introspect.py",   # the transparency surface — we already
                                    # shipped a provenance misreport here
                                    # (first_observed read a max()ed field)
)

# Deliberately NOT guarded, so the exclusions are a decision rather than an
# oversight: compile.py builds the wiki, which is a derived view and never the
# source of truth, and its inputs are already guarded via graph and gate. The
# list covers what changes "what may be asserted, what is visible, or what
# reaches model context" — not "important files". A noisy gate gets bypassed.

TRAILER = re.compile(r"^Spec:\s*(\S.*)$", re.M)


def _run(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def main(rng: str) -> int:
    try:
        commits = _run("git", "rev-list", rng).split()
    except subprocess.CalledProcessError:
        print(f"could not resolve range {rng!r}; skipping", file=sys.stderr)
        return 0

    failures = []
    for sha in commits:
        files = _run("git", "show", "--name-only", "--format=", sha).split()
        touched = sorted(f for f in files if f in GUARDED)
        if not touched:
            continue
        message = _run("git", "log", "-1", "--format=%B", sha)
        m = TRAILER.search(message)
        if not m:
            failures.append((sha[:8], touched))
            continue
        print(f"  {sha[:8]} touches {', '.join(touched)} -> Spec: {m.group(1).strip()}")

    if failures:
        print("\nMissing `Spec:` trailer on commits touching the trust surface:\n",
              file=sys.stderr)
        for sha, touched in failures:
            print(f"  {sha}  {', '.join(touched)}", file=sys.stderr)
        print("\nAdd one of:\n"
              "  Spec: specs/<n>-<name>.md\n"
              "  Spec: none (<why this needs no spec>)\n"
              "See specs/PROCESS.md for what needs a spec and the hotfix carve-out.",
              file=sys.stderr)
        return 1
    print("spec-reference check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "origin/main..HEAD"))
