#!/usr/bin/env python3
"""Generate every status summary in specs/0002 from specs/findings.py.

Five reviews, five deferrals, and each one found a status claim contradicting
another status claim in the same document. Every fix was a better hand-check;
the last was a phrase lint, which passed while "M1-M5, all closed" sat in the
header. A summary maintained beside the thing it summarises will drift, and
checking it harder does not change that.

So the summaries are generated between markers:

    <!-- GENERATED:name -->  ...  <!-- /GENERATED:name -->

`--write` rewrites them; `--check` fails on drift. Text inside a region is not
edited by hand -- edit `findings.py` instead.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "specs" / "0002-maintenance-provenance-invariant.md"
sys.path.insert(0, str(ROOT / "specs"))


def _regions() -> dict[str, str]:
    from findings import FINDINGS
    from reviews import REVIEWS as _ALL

    open_f = [f for f in FINDINGS if f["disposition"] == "open"]
    unimpl = [f for f in FINDINGS if f["implementation"] == "none"]
    shipped = [f for f in FINDINGS if f["implementation"] == "shipped"]
    committed = [f for f in FINDINGS if f["implementation"] == "committed"]
    releases = sorted({f["release"] for f in shipped if f["release"]})

    ids = lambda fs: ', '.join(f"`{f['id']}`" for f in fs)

    rows = []
    for f in FINDINGS:
        owner = "this spec" if f["owner"] == "0002" else f"**`specs/{f['owner']}`**"
        impl = {"shipped": f"**yes** — {f['release']}",
                "committed": f"**code yes, {f['release']}** — users do not have it",
                "none": "**no**", "n/a": "n/a"}[f["implementation"]]
        cur = f["current_defect"] or "—"
        if f["disposition"] == "open":
            cur = f"🔴 {cur}"
        adv = f" + {f['advisory']}" if f.get("advisory") else ""
        rows.append(f"| **{f['id']}** {f['title']} | {f['released_defect'] or '—'} | "
                    f"{cur} | {owner} | {impl}{adv} | `{f['test']}` |")

    ledger = ("| finding | released behaviour | current defect | owner | "
              "implemented? | test |\n|---|---|---|---|---|---|\n" + "\n".join(rows))

    summary = (
        f"**{len(FINDINGS)} findings · {len(shipped)} shipped "
        f"({', '.join(releases)}) · {len(unimpl)} unimplemented · "
        f"{len(open_f)} still open · **{len(committed)} fixed but unreleased**.**\n\n"
        f"**Unimplemented:** {ids(unimpl)}. **Open:** {ids(open_f)}.\n\n"
        f"*Two of the unimplemented — `M3` and `M4` — shipped in 0.4.5 as fixes "
        f"that do not hold.*")

    # 0002's rounds, from the one cross-spec source. The previous copy lived in
    # findings.py, covered only this spec, and stopped at v5 while a sixth
    # disposition sat in the document.
    REVIEWS = [r for r in _ALL if r["spec"] == "0002" and r["kind"] == "external"]
    # "round" is not "version": round 8 reviewed v7, and conflating them is how
    # a count becomes a contradiction two documents later.
    rv = " · ".join(f"r{r['round']} ({r['findings']})" for r in REVIEWS)
    reviews = (f"**{len(REVIEWS)} external review rounds, "
               f"{sum(r['findings'] for r in REVIEWS)} findings raised: {rv}.** The invariant was approved in every one; the "
               f"retrospective was deferred in every one.")

    # The reviewer's remedy for the split's lost overview: one page showing
    # finding -> owner -> status -> release, generated from the same records so
    # it cannot become another independently-maintained summary.
    idx_rows = []
    for f in FINDINGS:
        owner = "0002" if f["owner"] == "0002" else f["owner"]
        st = "open" if f["disposition"] == "open" else "resolved"
        impl = {"shipped": f"shipped {f['release']}",
                "committed": "**committed, unreleased**",
                "none": "**not implemented**", "n/a": "n/a"}[f["implementation"]]
        idx_rows.append(f"| `{f['id']}` | `{owner}` | {st} | {impl} | `{f['test']}` |")
    index = ("| finding | owner spec | disposition | implementation | test |\n"
             "|---|---|---|---|---|\n" + "\n".join(idx_rows))

    # The trust-class matrix is a status table too. v6 generated the ledger and
    # left this one hand-maintained, so it still called DECAY "clean" while the
    # ledger called N4-decay open.
    OPS = [
        ("`lifecycle.expire()` — LAPSE", None, "invalidates only; ages against `observed_at`"),
        ("`lifecycle.expire()` — DECAY", "N4-decay", "`confidence *= decay_factor`"),
        ("`lifecycle.expire()` — CONFIRM", None, "sets `needs_confirmation = True`; narrowing"),
        ("`lifecycle.consolidate()`", "M1", "provenance across the whole set"),
        ("`lifecycle.consolidate()` — provenance fields", "N9b-provenance", "`source_type` / `evidence_ref`"),
        ("`compile.py` (wiki)", None, "filters `use_only` and `third_party_influenced`"),
        ("`proactive.assemble()`", None, "`if not e.assertable: continue`"),
        ("`confirm()`", "M2", "first-known vs liveness"),
        ("T1 reinforcement", "M3", "clears `needs_confirmation`"),
        ("`record_outcome()` upgrade-in-place", "M4", "overwrites `author_of_evidence`"),
        ("T1 `confidence = max(...)`", "M5", "a new edge arrived"),
        ("`import_memory()`", "N9t-transfer", "trust fields reconstructed from a file"),
    ]
    by_id = {f["id"]: f for f in FINDINGS}
    mrows = []
    for op, fid, detail in OPS:
        if fid is None:
            verdict = "✅ clean"
        else:
            f = by_id[fid]
            if f["implementation"] == "committed":
                verdict = f"🟡 **fixed, unreleased** — `{fid}`"
            elif f["implementation"] == "shipped":
                verdict = f"✅ **fixed {f['release']}** — `{fid}`"
            elif f["disposition"] == "open":
                verdict = f"🔴 **open** — `{fid}`"
            else:
                verdict = f"🟠 **unimplemented** — `{fid}`"
        mrows.append(f"| {op} | {verdict} | {detail} |")
    matrix = ("| operation | verdict | detail |\n|---|---|---|\n" + "\n".join(mrows))

    # N9's relation, from specs/monotone.py. v7 stated it as a flat product of
    # per-field comparisons including `invalidation_reason` equality, which
    # forbids the first-time retirement the trust matrix calls clean.
    from monotone import EVIDENCE_FREE_REASONS, REASON_OWNER
    owners = "\n".join(f"| `{r}` | {o} | {'**yes**' if r in EVIDENCE_FREE_REASONS else 'no'} |"
                       for r, o in REASON_OWNER.items())
    n9 = ("""```
pre.active is False:                       # already retired
    post.active is False
    post.invalidation_reason == pre.invalidation_reason

pre.active and not post.active:            # THE retirement transition
    post.invalidation_reason is assigned, known, and
    permitted for this operation class

pre.active == post.active:                 # no transition
    post.invalidation_reason == pre.invalidation_reason

# and, in every case:
post.assertable          <=  pre.assertable
post.needs_confirmation  >=  pre.needs_confirmation   # keeping the caveat is weaker
post.disclosure          <=T pre.disclosure           # MENTIONABLE > USE_ONLY > QUARANTINED
post.confidence          <=  pre.confidence
post.observed_at         <=  pre.observed_at
post.author_of_evidence  ==  pre.author_of_evidence   # categorical
post.derived_from        ==  pre.derived_from         # categorical
post.valid_from          ==  pre.valid_from
```

**A reason says what happened, so only the operation that did it may assign
one.** An evidence-free operation may assign only the reasons in the last
column; `superseded`, `corrected` and `disputed` all require either new evidence
or an authorised act, so N9 rejects an evidence-free operation claiming them.

| reason | assigned by | evidence-free may assign? |
|---|---|---|
""" + owners)
    return {"ledger": ledger, "summary": summary, "reviews": reviews,
            "index": index, "matrix": matrix, "n9": n9}


def _apply(text: str, regions: dict[str, str]) -> str:
    for name, body in regions.items():
        pat = re.compile(rf"(<!-- GENERATED:{name} -->\n)(.*?)(<!-- /GENERATED:{name} -->)",
                         re.S)
        if not pat.search(text):
            raise SystemExit(f"no <!-- GENERATED:{name} --> region in {SPEC.name}")
        text = pat.sub(lambda m: m.group(1) + body + "\n" + m.group(3), text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = SPEC.read_text()
    want = _apply(text, _regions())
    if a.write:
        SPEC.write_text(want)
        print(f"regenerated {len(_regions())} region(s) in {SPEC.name}")
        return 0
    if a.check:
        if want != text:
            print(f"{SPEC.name}: a generated region is stale. Edit "
                  f"specs/findings.py, then run render_status.py --write. "
                  f"Status prose is derived; five reviews were deferred for "
                  f"maintaining it by hand.", file=sys.stderr)
            return 1
        print("status regions are in sync with specs/findings.py")
        return 0
    print(_regions()["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
