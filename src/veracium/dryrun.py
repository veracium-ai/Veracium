"""`veracium remember --dry-run` — what an ingest WOULD write, without writing it.

    veracium remember --user ida "I moved to Porto" --dry-run
    veracium remember --user ida "email from acme" --author third_party --dry-run --json

Why it exists (the developer-tools backlog, item 4, endorsed 2026-08-30 and
started on Quentin's word 2026-09-12): every decision `remember` makes is
silent until the row is written — which facts it extracts, which it refuses,
which it quarantines at birth, whether the 0026 relay floor demotes one,
which existing fact it supersedes or reinforces, whether the extraction was
usable at all. A host tuning a prompt, a provider, or a trust setting had to
write to a real store to find out.

How it works — by construction, not by a second code path: the ingest runs
FOR REAL against a SNAPSHOT COPY of the store in a private temporary
directory, with a diagnostics reporter attached to a temporary log, and the
report is the DELTA between the copy before and after plus the result the
ingest returned plus the degrade records it emitted. The original file is
never opened (specs/0031 §4b-ii: no second file-backed opener; the copy goes
through the store constructor like any store), so the bytes on disk are
provably unchanged; the copy is deleted afterwards. Because the real ingest
ran, the report cannot disagree with what the real write would do to the
same store with the same answer — the provider is called once, the way the
real ingest calls it, and the answer is consumed by the shipped path.

What the report carries, per new edge: subject / relation / object, the
evidence author, disclosure tier (mentionable / use_only / quarantined),
`quarantined`, `ungrounded`, `needs_confirmation`, the agreement record if
one was derived, and the edge it supersedes. Per changed edge: what moved
(retired with its reason, or liveness advanced). Then the ingest's counters
verbatim (`facts`, `quarantined`, `supersessions`, `reinforcements`,
`invalid`, `retried`, `recovered`, `residual`, `redispositioned`,
`instructions_dropped`, `subject_refused`, `quarantined_at_birth`,
`agreement_floored`, `agreement_recorded`, `unparseable`,
`extraction_unusable`), the episode that would be filed (count only; the
summary text is the ingest's own output and is shown because the operator
typed the input), and every degrade record (specs/0039) the run emitted.

Limits, stated: the provider is called (a dry run of an extraction is an
extraction; there is no provider-free variant), so the run costs one
provider call and its answer may differ next time; the snapshot copy is one
read of the store file; and a dry run against a store under concurrent
writes sees whatever bytes were on disk.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class DryRun:
    user_id: str
    db: str
    existing_store: bool
    result: dict = field(default_factory=dict)          # the ingest's own return, verbatim
    new_edges: list = field(default_factory=list)       # what would be written
    changed_edges: list = field(default_factory=list)   # what would move (retired / reinforced)
    new_episodes: int = 0
    degrades: list = field(default_factory=list)        # specs/0039 records, content-free
    error: Optional[str] = None                         # the provider raised: class name only

    @property
    def usable(self) -> bool:
        return self.error is None and not self.result.get("unparseable") \
            and not self.result.get("extraction_unusable")


_EDGE_FIELDS = ("subject", "relation", "object", "volatility", "valid_from", "invalidated_at",
                "invalidation_reason", "supersedes", "original_relation", "needs_confirmation",
                "agreement", "ungrounded", "note")
_PROV_FIELDS = ("author_of_evidence", "disclosure", "derived_from", "source_id", "observed_at",
                "confidence", "evidence_ref")


def _dump(e) -> dict:
    d = e.model_dump(mode="json")
    return {**{k: d.get(k) for k in _EDGE_FIELDS},
            **{f"provenance.{k}": (d.get("provenance") or {}).get(k) for k in _PROV_FIELDS},
            "id": d.get("id"), "quarantined": bool(e.quarantined)}


def _snapshot(store, user_id: str) -> tuple:
    edges = {e.id: _dump(e) for e in store.edges(user_id, active_only=False, include_quarantined=True)}
    n_episodes = len(store.episodes(user_id, include_retired=True))
    return edges, n_episodes


def _degrade_records(log_path) -> list:
    out = []
    if not os.path.exists(log_path):
        return out
    for line in open(log_path, encoding="utf-8").read().splitlines():
        if " degrade=" not in line:
            continue
        fields = {}
        for tok in line.split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                fields[k] = v
        out.append(fields)
    return out


def run(db_path: str, llm, user_id: str, text: str, *, author, event_type: str = "chat",
        date: Optional[str] = None, derived_from=None, source_id: Optional[str] = None,
        context=None) -> DryRun:
    """The dry run: a real ingest into a snapshot copy, reported as a delta."""
    from . import Memory, MemoryConfig
    from .diagnostics import DiagnosticsConfig, Reporter
    dr = DryRun(user_id=user_id, db=db_path, existing_store=os.path.exists(db_path))
    tmpdir = tempfile.mkdtemp(prefix="veracium-dryrun-")
    try:
        copy = os.path.join(tmpdir, "snapshot.db")
        if dr.existing_store:
            shutil.copy2(db_path, copy)
        log = os.path.join(tmpdir, "degrades.log")
        rep = Reporter(DiagnosticsConfig(log_path=log, report_enabled=False, prompt_on_error=False))
        mem = Memory(llm=llm, config=MemoryConfig(db_path=copy, wiki_recompile_after_writes=0),
                     diagnostics=rep)
        try:
            before, n_before = _snapshot(mem.store, user_id)
            kw = {"author": author, "event_type": event_type, "date": date,
                  "derived_from": derived_from, "source_id": source_id}
            if context is not None:
                kw["context"] = context
            try:
                dr.result = mem.remember(user_id, text, **kw)
            except Exception as ex:                                   # noqa: BLE001
                dr.error = type(ex).__name__          # the class only; a provider message can carry text
            after, n_after = _snapshot(mem.store, user_id)
        finally:
            mem.close()
        dr.degrades = _degrade_records(log)
        for eid, d in after.items():
            if eid not in before:
                dr.new_edges.append(d)
            elif d != before[eid]:
                moved = [(k, before[eid].get(k), d.get(k)) for k in d if before[eid].get(k) != d.get(k)]
                dr.changed_edges.append({"id": eid, "fact": f"{d['subject']} {d['relation']} {d['object']}",
                                         "changed": moved})
        dr.new_edges.sort(key=lambda d: (d["relation"] or "", d["object"] or ""))
        dr.new_episodes = n_after - n_before
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return dr


def _fmt(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    return str(v)


def render(dr: DryRun) -> str:
    out = [f"dry run — nothing written to {dr.db}" + ("" if dr.existing_store else " (no store there yet: a fresh one was assumed)")]
    if dr.error:
        out.append(f"  the provider call raised {dr.error}; no ingest outcome to report")
        return "\n".join(out) + "\n"
    r = dr.result
    if r.get("unparseable"):
        out.append("  extraction UNPARSEABLE: the provider answered with no usable JSON — nothing would be written but the episode")
    elif r.get("extraction_unusable"):
        out.append("  extraction UNUSABLE: the answer produced no shape-valid triple — nothing would be written but the episode")
    out.append(f"  would write {len(dr.new_edges)} fact(s), retire/move {len(dr.changed_edges)}, file {dr.new_episodes} episode(s)")
    for d in dr.new_edges:
        tier = d["provenance.disclosure"]
        flags = [x for x, on in (("quarantined", d["quarantined"]), ("ungrounded", d["ungrounded"]),
                                 ("needs_confirmation", d["needs_confirmation"])) if on]
        line = (f"  + {d['subject']} {d['relation']} {d['object']}   [{tier}; author={d['provenance.author_of_evidence']}"
                + (f"; derived_from={d['provenance.derived_from']}" if d["provenance.derived_from"] else "")
                + (f"; {', '.join(flags)}" if flags else "") + "]")
        out.append(line)
        if d.get("original_relation"):
            out.append(f"      relation repaired from {d['original_relation']}")
        if d.get("supersedes"):
            out.append(f"      supersedes {d['supersedes']}")
        if d.get("agreement"):
            out.append(f"      agreement record: {_fmt(d['agreement'])}")
        if d.get("note"):
            out.append(f"      note: {d['note']}")
    for c in dr.changed_edges:
        out.append(f"  ~ {c['fact']}  ({c['id']})")
        for k, b, a in c["changed"]:
            out.append(f"      {k}: {_fmt(b)} -> {_fmt(a)}")
    counters = ("facts", "quarantined", "supersessions", "reinforcements", "invalid", "retried", "recovered",
                "residual", "redispositioned", "instructions_dropped", "subject_refused", "quarantined_at_birth",
                "agreement_floored", "agreement_recorded")
    out.append("  counters   " + " ".join(f"{k}={r.get(k, 0)}" for k in counters))
    if r.get("birth_revocation_digest"):
        out.append(f"  quarantined at birth: the source is under a standing revocation ({str(r['birth_revocation_digest'])[:16]}…)")
    if r.get("episode"):
        out.append(f"  episode    {r['episode']}")
    for g in dr.degrades:
        out.append("  degrade    " + " ".join(f"{k}={v}" for k, v in g.items() if k in ("op", "degrade", "cause", "count")))
    return "\n".join(out) + "\n"


def to_json(dr: DryRun) -> dict:
    d = asdict(dr)
    d["usable"] = dr.usable
    return d
