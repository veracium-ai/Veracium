#!/usr/bin/env python3
"""Tripwire: every commit touching the trust surface must reference a spec.

**What this establishes, precisely.** It requires that a guarded commit carries
a machine-readable reference to a specification that exists, or a declared
exception in a recognised category. **It does not establish compliance with the
specification process.** It does not check the trust matrix, the executable
invariants, internal or external review, the decision state, regime coverage,
or the accepted claim wording. Read a green result as "a reference is present
and well-formed", never as "this change followed the process".

That paragraph is load-bearing. The previous version's docstring claimed it
"turns the prose rule into a check", and an external reviewer then demonstrated
that `Spec: banana`, `Spec: none`, a reference to a nonexistent file, a rename
out of a guarded path, a brand-new trust module, and an unresolvable commit
range *all passed*. A gate that reports success it has not earned is worse than
no gate, because it manufactures assurance.

Accepted forms — real Git trailers, in the trailer block at the end of the
message:

    Spec: specs/0007-generated-content-trust-class.md

    Spec-Exception: docs-only
    Spec-Exception-Reason: corrected a stale comment in graph.py

    Spec-Exception: security-hotfix
    Spec-Exception-Reason: GHSA-r7j7-5jq9-3f5q, cross-trust identity merges
    Spec-Retrospective-Due: 2026-08-04

**These must be real trailers, not merely lines starting with "Spec:".** Git
requires the trailer block to be the last paragraph, and a wrapped value to be
indented on continuation lines. When this check was written, *all three* of our
existing `Spec:` lines failed that rule — the old regex accepted text Git itself
does not consider a trailer. If a value must wrap, indent the continuation.

Exit codes:  0 = ok · 1 = policy failure · 2 = could not run (fails closed)

Usage:  check_spec_reference.py [<commit-range>] [--allow-missing-base]
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
    "src/veracium/mcp_server.py",   # maps CALLER-SUPPLIED STRINGS onto trust
                                    # classes, and `remember` is an @server.tool
                                    # so the caller is the MODEL. Mapping
                                    # "system" here let a model declare its own
                                    # evidence class; the lookup then defaulted
                                    # unrecognised values to USER. A file that
                                    # decides what a string is allowed to mean,
                                    # for an untrusted caller, is the trust
                                    # surface — it was missing from this list
                                    # for the same reason the first three were.

    "src/veracium/compile.py",      # ADDED after M8. It was excluded on the
                                    # reasoning that the wiki is a derived view
                                    # whose inputs are guarded upstream — and
                                    # M8 falsified exactly that: the wiki CACHES
                                    # a trust decision and keeps serving it into
                                    # the GROUNDED block after the decision is
                                    # revoked. A derived view that outlives its
                                    # inputs is not downstream of them.
)

# --- how this list is derived, since recalling it kept failing ---------------
#
# A file is guarded if it DECIDES WHAT A CALLER-SUPPLIED VALUE IS PERMITTED TO
# MEAN, or if it WRITES, DERIVES, ROUTES ON, OR RENDERS a trust-bearing field.
# (research, 2026-08-01, after the fourth recalled-list failure in one session:
# consumers, store mutators, freeze content, and this.)
#
# Re-derive and diff rather than edit from memory:
#   trust fields: author_of_evidence · derived_from · disclosure · confidence ·
#                 valid_from · observed_at · needs_confirmation · quarantined ·
#                 assertable · active · invalidation_reason
#   forms that count: literal->enum maps · assignment · construction/validate ·
#                     `if ...<field>` routing · rendering into text
#
# Adjudicated exclusions from the last derivation, recorded so they are
# decisions rather than oversights:
#
#   cli.py       — offers `--author system`, which LOOKS like the mcp_server
#                  defect and is not: the CLI caller is a human operator, and a
#                  host attributing authorship is the trusted model. mcp_server
#                  was different because `remember` is @server.tool(), so the
#                  caller is the MODEL declaring its own class. Also cannot
#                  fail open — argparse `choices` constrains it. NOT guarded,
#                  but re-examine if the CLI is ever driven by an agent.
#   selfcheck.py — asserts guarantees against a throwaway store; it TESTS trust
#                  rather than deciding it. A defect there is claim-accuracy,
#                  not trust behaviour.
#   store/base.py — the interface declaration; the implementation
#                  (store/sqlite.py) is guarded and is where behaviour lives.

# The process controls themselves. A commit could otherwise weaken this script,
# or the workflow that runs it, and have the weakened version approve its own
# change. Requiring a declared `Process-Change:` does not *prevent* that — see
# the caveat printed below — but it removes "nobody noticed" as an explanation.
PROCESS_CONTROLS = (
    "specs/check_spec_reference.py",
    "specs/PROCESS.md",
    "specs/TEMPLATE.md",
    ".github/workflows/test.yml",
)

EXCEPTION_CATEGORIES = {
    "docs-only": "comments, docstrings, or prose in a guarded file",
    "test-only": "changes confined to test code",
    "behavior-preserving-refactor": "no observable change; say how that was established",
    "security-hotfix": "a live user-affecting defect; also needs Spec-Retrospective-Due",
    # Added 2026-08-01 while backing out a change that landed by accident. The
    # taxonomy had no way to say "this restores a guarded file to its last
    # approved state", so the only labels available were false ones — and a
    # false label is how the change got in: `git add -A` swept in held-back work
    # and a docs-only exception written for a different file waved it through.
    # A process with no exit is a process people mislabel their way out of.
    "revert": "restores a guarded file to its last approved state; name what is being backed out and why",
}

# A spec's state, as a machine-readable line INSIDE the spec file:
#
#     Spec-Status: accepted
#
# Only `accepted` authorises implementation. `accepted-with-amendments`
# deliberately does NOT — PROCESS.md says so in prose and this makes it true:
# amendments must be resolved and the amended version approved first.
#
# This exists because the gate could not previously tell an accepted spec from a
# blank draft. `Spec:` proved a file existed and nothing more, and 0.4.5 shipped
# citing a spec whose status line read "draft". Flagged by the checker's own
# external review ("its metadata has an acceptable status") and deferred to the
# pilot; the pilot happened and it bit.
SPEC_STATES = ("draft", "in review", "accepted", "accepted-with-amendments",
               "deferred", "rejected")
IMPLEMENTABLE = ("accepted",)
_SPEC_STATUS = re.compile(r"^Spec-Status:\s*(\S[^\n]*)$", re.M)
# Dev sets `accepted` once external-review comments are satisfied (PROCESS §4a).
# Dev has been wrong about "satisfied" three times, so the claim needs an
# artifact: one row per finding, each naming a command, test or commit.
_CLOSURE = re.compile(r"^##+\s*Review closure", re.M)

MIN_REASON_CHARS = 12
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class CannotRun(RuntimeError):
    """We could not determine what to check. Never silently a pass."""


def _git(*args: str) -> str:
    r = subprocess.run(("git", *args), capture_output=True, text=True)
    if r.returncode != 0:
        raise CannotRun(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def _trailer_values(sha: str, key: str) -> list[str]:
    """Real trailer parsing, via Git's own parser.

    The old regex matched any line beginning with `Spec:` anywhere in the
    message, so a sentence in a discussion paragraph satisfied the gate.
    """
    out = _git("log", "-1", f"--format=%(trailers:key={key},valueonly,separator=%x00)", sha)
    return [v.strip() for v in out.split("\0") if v.strip()]


def _touched(sha: str) -> set[str]:
    """Paths this commit touched, counting BOTH sides of a rename.

    `git show --name-only` reports only a rename's destination, so renaming
    `graph.py` to an unguarded name escaped the gate entirely. `-M` gives the
    status letter and both paths.
    """
    out = _git("diff-tree", "--name-status", "-M", "-r", "--no-commit-id", sha)
    paths: set[str] = set()
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        # R100/C75 carry <src> <dst>; both matter — moving code OUT of a
        # guarded file changes the guarded file just as much as editing it.
        paths.update(parts[1:] if status[0] in ("R", "C") else parts[1:2])
    return paths


def _is_merge(sha: str) -> bool:
    return len(_git("rev-list", "--parents", "-n", "1", sha).split()) > 2


def _validate_spec_ref(sha: str, value: str) -> list[str]:
    """A reference must point at a spec that exists in this commit's tree."""
    problems = []
    if not value.startswith("specs/"):
        problems.append(f"`Spec: {value}` — must be a path under `specs/`")
        return problems
    if not value.endswith(".md"):
        problems.append(f"`Spec: {value}` — must be a markdown file")
    if value in ("specs/TEMPLATE.md", "specs/PROCESS.md"):
        problems.append(f"`Spec: {value}` — that is the template/process itself, "
                        f"not a specification for this change")
        return problems
    try:
        body = _git("show", f"{sha}:{value}")
    except CannotRun:
        problems.append(f"`Spec: {value}` — does not exist in this commit's tree")
        return problems

    # --- status gate --------------------------------------------------------
    m = _SPEC_STATUS.search(body)
    if not m:
        problems.append(
            f"`{value}` has no `Spec-Status:` line. The gate cannot tell an "
            f"accepted spec from a blank draft without one, so it fails closed. "
            f"Add one of: {', '.join(SPEC_STATES)}")
        return problems
    state = m.group(1).strip().lower()
    if state not in SPEC_STATES:
        problems.append(f"`{value}` has `Spec-Status: {m.group(1).strip()}` — "
                        f"not one of {', '.join(SPEC_STATES)}")
    elif state not in IMPLEMENTABLE:
        extra = (" — amendments must be resolved and the amended version "
                 "approved before implementation"
                 if state == "accepted-with-amendments" else "")
        problems.append(
            f"`{value}` is `{state}`, which does not authorise implementation"
            f"{extra}. Land the spec first, or use `Spec-Exception:` if this "
            f"commit is docs/tests/a revert rather than implementing it.")
    elif not _CLOSURE.search(body):
        problems.append(
            f"`{value}` is `accepted` but carries no `## Review closure` "
            f"section. Dev sets `accepted` once external-review comments are "
            f"satisfied (PROCESS.md §4a) — so record one row per finding with "
            f"the command, test or commit that closes it. Three of dev's own "
            f"'this is fixed' claims were wrong this week; the artifact is what "
            f"removes the wrong answer.")
    return problems


def _validate_exception(sha: str, category: str) -> list[str]:
    problems = []
    if category not in EXCEPTION_CATEGORIES:
        problems.append(
            f"`Spec-Exception: {category}` — unrecognised. Use one of: "
            + ", ".join(sorted(EXCEPTION_CATEGORIES)))
        return problems
    reasons = _trailer_values(sha, "Spec-Exception-Reason")
    reason = reasons[0] if reasons else ""
    if len(reason) < MIN_REASON_CHARS:
        problems.append(
            f"`Spec-Exception: {category}` needs a `Spec-Exception-Reason:` "
            f"trailer of at least {MIN_REASON_CHARS} characters "
            f"({'none given' if not reason else 'too short: ' + reason!r})")
    if category == "security-hotfix":
        # The carve-out is correct — holding the 0.4.1 advisory fix for review
        # would have been the wrong call. A deadline is what keeps it a
        # carve-out rather than a door.
        due = _trailer_values(sha, "Spec-Retrospective-Due")
        if not due:
            problems.append("`security-hotfix` also needs "
                            "`Spec-Retrospective-Due: YYYY-MM-DD` — the date the "
                            "retrospective spec and external review are due")
        elif not _DATE.match(due[0]):
            problems.append(f"`Spec-Retrospective-Due: {due[0]}` — not YYYY-MM-DD")
    return problems


def _check_commit(sha: str) -> tuple[list[str], list[str]]:
    """Returns (problems, notes) for one commit."""
    problems: list[str] = []
    notes: list[str] = []
    touched = _touched(sha)
    guarded = sorted(t for t in touched if t in GUARDED)
    controls = sorted(t for t in touched if t in PROCESS_CONTROLS)

    if controls:
        if not _trailer_values(sha, "Process-Change"):
            problems.append(
                f"touches the process controls themselves ({', '.join(controls)}) "
                f"without a `Process-Change: <reason>` trailer")
        else:
            notes.append(f"  {sha[:8]} PROCESS CHANGE: {', '.join(controls)} "
                         f"-> requires independent approval (not verifiable here)")

    if not guarded:
        return problems, notes

    refs = _trailer_values(sha, "Spec")
    exceptions = _trailer_values(sha, "Spec-Exception")

    if refs and exceptions:
        problems.append("carries both `Spec:` and `Spec-Exception:` — pick one")
    elif refs:
        # Multiple specs are legitimate (one change implementing two accepted
        # specs). ALL must validate; the old code silently used the first.
        for value in refs:
            if value.lower() == "none":
                problems.append(
                    "`Spec: none` is no longer accepted — it carried no "
                    "category and any invented explanation passed. Use "
                    "`Spec-Exception: <category>` + `Spec-Exception-Reason:`")
            else:
                problems.extend(_validate_spec_ref(sha, value))
        if not problems:
            notes.append(f"  {sha[:8]} {', '.join(guarded)} -> {', '.join(refs)}")
    elif exceptions:
        if len(exceptions) > 1:
            problems.append("more than one `Spec-Exception:` — pick one category")
        else:
            problems.extend(_validate_exception(sha, exceptions[0]))
        if not problems:
            notes.append(f"  {sha[:8]} {', '.join(guarded)} -> "
                         f"EXCEPTION {exceptions[0]}")
    else:
        problems.append(f"touches the trust surface ({', '.join(guarded)}) with no "
                        f"`Spec:` or `Spec-Exception:` trailer")
    return problems, notes


def main(rng: str, *, allow_missing_base: bool = False) -> int:
    try:
        commits = _git("rev-list", rng).split()
    except CannotRun as e:
        if allow_missing_base:
            print(f"could not resolve range {rng!r}; --allow-missing-base given, "
                  f"skipping", file=sys.stderr)
            return 0
        # FAIL CLOSED. A shallow clone, a fork without `origin`, a renamed
        # default branch or a misconfigured job used to print "skipping" and
        # exit 0 — a green build that checked nothing, which is the worst
        # possible output because it is indistinguishable from a real pass.
        print(f"ERROR: cannot resolve commit range {rng!r}, so nothing was "
              f"checked.\n  {e}\n"
              f"  Refusing to report success for a check that did not run. "
              f"Fix the range (a full-depth checkout is usually the issue), or "
              f"pass --allow-missing-base for local use only.", file=sys.stderr)
        return 2

    failures, notes = [], []
    for sha in commits:
        try:
            if _is_merge(sha):
                # a merge introduces no changes of its own; its branch commits
                # are in the same range and are checked individually
                continue
            problems, commit_notes = _check_commit(sha)
        except CannotRun as e:
            print(f"ERROR inspecting {sha[:8]}: {e}", file=sys.stderr)
            return 2
        notes.extend(commit_notes)
        if problems:
            failures.append((sha[:8], problems))

    for n in notes:
        print(n)

    if failures:
        print("\nSpec-reference check FAILED:\n", file=sys.stderr)
        for sha, problems in failures:
            for p in problems:
                print(f"  {sha}  {p}", file=sys.stderr)
        print("\nAccepted forms (real Git trailers, last paragraph, "
              "continuations indented):\n"
              "  Spec: specs/<n>-<name>.md\n"
              "  Spec-Exception: <" + " | ".join(sorted(EXCEPTION_CATEGORIES))
              + ">\n  Spec-Exception-Reason: <why>\n"
              "  (security-hotfix also needs Spec-Retrospective-Due: YYYY-MM-DD)\n"
              "See specs/PROCESS.md.", file=sys.stderr)
        return 1

    print(f"spec-reference check: ok ({len(commits)} commit(s)) — reference "
          f"presence only; this does not establish process compliance")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--allow-missing-base"]
    raise SystemExit(main(args[0] if args else "origin/main..HEAD",
                          allow_missing_base="--allow-missing-base" in sys.argv))
