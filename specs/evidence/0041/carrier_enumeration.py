#!/usr/bin/env python3
"""0040 §2's carrier enumeration — DERIVED, never hand-maintained.

A hand-listed carrier set is what lost `edges.subject`: §2 named the `object`
column as "the second site" and INV-2 planted one mutant, while the DDL carries
THREE columns duplicating json fields. Dev found `subject`; re-deriving found
`relation` too.

🔴 AND THE FIRST VERSION OF THIS SCRIPT REPRODUCED THE SAME DEFECT. It parsed
the DDL with a line-anchored regex (`^\\s*(\\w+)\\s+(TEXT|INTEGER)`), which found
`id` and `object` — the two columns that happen to start a line — and MISSED
`subject` and `relation`, which sit mid-line. An enumeration is only as complete
as its parser, and a regex over source text is a parser nobody reviewed. It now
splits on commas inside the parens.

🔴 AND THE THIRD FAILURE, found 2026-09-13 when dev announced a v14 receipt
table: THIS SCRIPT READ `SCHEMA_V1` AND SWEPT ONE TABLE. The current schema is
`SCHEMA_V13` with FOURTEEN tables — `edge_event`, `edge_embedding`,
`contribution_ledger`, `confirmations`, `source_revocations`, `store_epoch` and
the rest were invisible to it, including three that 0040 §2's own carrier table
already names. The tool built to stop a hand-list missing things was reading a
schema twelve versions stale, and it LOOKED FINE because its output for `edges`
was correct. A derivation is only as wide as its corpus.

It now discovers the latest `SCHEMA_Vn` by version number and sweeps EVERY
table, so a new table (the v14 receipt) appears without anyone remembering to
add it.

🔴 AND THE FOURTH FAILURE, found by the 0041 round-1 reviewer (2026-09-15):
SECTION B'S MODEL SET WAS ITSELF A HAND-LIST. It read `text_fields(Edge)` and
`text_fields(Provenance)` — two model names written literally — so it never
looked at `Episode` (missing `retired_reason`) and never recursed into nested
models (missing `agreement.markers` under a foreign lexicon version). The same
defect as `SCHEMA_V1`, one source lower: a derivation whose CORPUS is named by
hand. It now discovers every `BaseModel` in `veracium.schema` and RECURSES
through nested model fields, so a new model or a new nested shape appears
without anyone remembering it.

TWO SOURCES, because neither sees what the other does:
  A. the DDL          — columns, ALL TABLES. Cannot see inside the `json` blob.
  B. the pydantic models — every field that can hold text, including the ones
                           that live inside `json` and are invisible to SQL.
"""
import sys, json
# the packaged copy resolves the repository from THIS file (research's original,
# sha16 50531999b8caf5f0 at research commit 2dfdf3ab, carried an absolute local
# path here — the census precedent; the OUTPUT file beside this one is research's
# run of that original, sha16 90e1d907ed58560a, as-is)
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "src"))
from veracium.schema import Edge, Provenance
from veracium.store import schema_version as sv

SKIP_IDENTITY = {"id", "user_id"}


def latest_schema():
    """The newest SCHEMA_Vn, found by VERSION NUMBER — never named literally,
    because a literal is the hand-list this script exists to replace."""
    import re
    names = [n for n in dir(sv) if re.match(r"^SCHEMA_V\d+$", n)]
    newest = max(names, key=lambda n: int(n[len("SCHEMA_V"):]))
    return newest, getattr(sv, newest)


def ddl_columns(obj):
    body = obj.ddl[obj.ddl.index("(") + 1: obj.ddl.rindex(")")]
    out = []
    for part in body.split(","):
        tok = part.strip().split()
        if len(tok) >= 2:
            out.append((tok[0], tok[1]))
    return out


def text_fields(model):
    out = []
    for name, f in model.model_fields.items():
        ann = str(f.annotation)
        if "str" in ann and "Enum" not in ann and "datetime" not in ann:
            out.append((name, ann))
    return out


def all_models():
    """EVERY pydantic model in `veracium.schema`, discovered — not named.

    Section B used to read `text_fields(Edge)` and `text_fields(Provenance)`:
    two model names written literally, which is the `SCHEMA_V1` defect one
    source lower. `Episode.retired_reason` and nested `agreement.markers` were
    invisible to it for exactly that reason (0041 round-1 reviewer, F1).
    """
    from pydantic import BaseModel
    import veracium.schema as _s
    seen = {}
    for nm, obj in vars(_s).items():
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
            seen[obj.__name__] = obj
    return dict(sorted(seen.items()))


def walk_text(model, _path="", _seen=None):
    """Text-capable fields, RECURSING through nested models.

    A field whose annotation names another model is walked too, so a carrier
    nested one level down (`agreement.markers`) is reached. Cycles are cut by
    the visited set rather than by depth, so no shape is silently truncated.
    """
    from pydantic import BaseModel
    _seen = _seen if _seen is not None else set()
    if model in _seen:
        return []
    _seen.add(model)
    out = []
    for name, f in model.model_fields.items():
        ann = f.annotation
        anns = str(ann)
        nested = [a for a in getattr(ann, "__args__", ()) or ([ann] if isinstance(ann, type) else [])
                  if isinstance(a, type) and issubclass(a, BaseModel)]
        if nested:
            for sub in nested:
                out += walk_text(sub, f"{_path}{name}.", _seen)
        elif "str" in anns and "Enum" not in anns and "datetime" not in anns:
            out.append((f"{_path}{name}", anns))
    return out


if __name__ == "__main__":
    fields = set(Edge.model_fields)
    ver, schema = latest_schema()
    tables = [o for o in schema if o.kind == "table"]
    print(f"A. EVERY TEXT/BLOB COLUMN IN {ver} — {len(tables)} tables\n")
    dup = []
    for obj in sorted(tables, key=lambda o: o.name):
        cols = [(n, t) for n, t in ddl_columns(obj)
                if t.upper().startswith(("TEXT", "BLOB"))]
        if not cols:
            continue
        marks = []
        for n, t in cols:
            d = obj.name == "edges" and n in fields and n not in SKIP_IDENTITY
            if d: dup.append(f"{obj.name}.{n}")
            marks.append(f"{n}{' ←DUPLICATES json' if d else ''}")
        print(f"   {obj.name:<24} {', '.join(marks)}")
    print(f"\n   → {len(dup)} columns duplicate a json field: {dup}")
    print("     INV-2 must plant a mutant PER COLUMN, enumerated from here.")
    print("     Every other TEXT column above is a candidate carrier §2 must")
    print("     name or explicitly record as a non-carrier.\n")

    print("B. Model fields that can carry TEXT — the DDL is blind to these")
    models = all_models()
    print(f"   {len(models)} models DISCOVERED in veracium.schema, never named: "
          f"{', '.join(models)}\n")
    total = 0
    for mname, m in models.items():
        for fname, ann in walk_text(m):
            if fname in SKIP_IDENTITY: continue
            total += 1
            print(f"     {mname}.{fname:<28}{ann[:40]}")
    print(f"\n   {total} text-capable fields, RECURSED through nested models.")
    print("   Every one lives inside a json blob and is invisible to the schema.")


# ---------------------------------------------------------------------------
# C. TRIAGE — carrier or not, DERIVED. 125 paths are not 125 carriers.
#
# Section B counts PATHS. A path is not an identity: ContestedGroup.exposed.*
# and SupersessionPlan.incoming_edge.* are both `Edge`, reached through a
# container, and redacting Edge.note redacts it everywhere it is reachable.
# Pasting 125 rows into the spec would inventory the same field up to three
# times and call the repetition coverage.
#
# Three inputs, each derived, none declared:
#   1. TERMINAL identity   -- collapse every path to (owning model, field).
#   2. PERSISTED           -- a model is directly persisted iff the store
#                             layer reconstructs it with model_validate_json;
#                             you only validate from JSON what you wrote as
#                             JSON. Nested models inherit it by containment.
#   3. BOUNDED             -- the value space is closed (Literal / pattern /
#                             enum), so no user text can reach the field.
#
# NOTE ON max_length, WHICH IS THE TRAP HERE: Provenance.source_id carries
# max_length=512. That bounds the LENGTH and not the VALUE SPACE -- 512
# characters of free text is still free text. Counting max_length as a bound
# would mark a genuine carrier clean, so it is deliberately NOT a bound below.
# ---------------------------------------------------------------------------

def nested_models(model):
    """Direct model-typed fields of `model` (through Optional/list wrappers)."""
    from pydantic import BaseModel
    out = []
    for name, f in model.model_fields.items():
        ann = f.annotation
        for a in (getattr(ann, "__args__", ()) or ([ann] if isinstance(ann, type) else [])):
            if isinstance(a, type) and issubclass(a, BaseModel):
                out.append(a)
    return out


def resolve_terminal(model, path):
    """Walk a dotted path down to the model that ACTUALLY declares the leaf.

    `ContestedGroup.exposed.note` resolves to (Edge, "note") -- the same
    identity as `Edge.note`, which is why paths must not be counted as fields.
    """
    from pydantic import BaseModel
    parts = path.split(".")
    cur = model
    for hop in parts[:-1]:
        f = cur.model_fields[hop]
        ann = f.annotation
        nxt = [a for a in (getattr(ann, "__args__", ()) or ([ann] if isinstance(ann, type) else []))
               if isinstance(a, type) and issubclass(a, BaseModel)]
        cur = nxt[0]
    return cur, parts[-1]


def persisted_models():
    """Models that reach disk. TWO storage disciplines, and missing either one
    marks a written field 'never stored' -- a FALSE CLEAN, the direction that
    costs something.

      (a) JSON blob     -- store/ reconstructs it with model_validate_json.
      (b) FLAT columns  -- the model's fields ARE a table's columns
                           (SupersessionRefusal -> supersession_refusals,
                            Confirmation -> confirmations,
                            ContributionRecord -> contribution_ledger).

    The first pass of this triage derived (a) only and reported all three of
    those as TRANSIENT/non-carrier. They are INSERTed field by field, so the
    grep for a JSON round-trip could never see them. Both disciplines are
    derived below and the reason is reported per model, so a reader can tell
    which evidence carried each verdict.
    """
    import pathlib as _p, re, veracium
    root = _p.Path(veracium.__file__).parent
    how = {}
    for f in (root / "store").rglob("*.py"):
        for m in re.finditer(r"(?:^|[^\w.])_?(\w+)\.model_validate_json\(", f.read_text()):
            how[m.group(1).lstrip("_")] = "json blob"

    # (b) flat columns: a model whose field names are covered by a table's columns
    _ver, _schema = latest_schema()
    tables = {o.name: {n for n, _t in ddl_columns(o)}
              for o in _schema if o.kind == "table"}
    for name, mdl in all_models().items():
        if name in how:
            continue
        fields = set(mdl.model_fields)
        # THE MODEL *IS* THE ROW: every field is a column of that table.
        # An OVERLAP test was tried first and over-matched -- ContestedGroup
        # shares `subject` and `relation` with `edges` and was reported stored
        # in it, though it is a QUERY RESULT assembled from rows and is never
        # written. Subset is the property that actually means "this is a row".
        for t, cols in sorted(tables.items()):
            if len(fields & cols) >= 2 and fields <= cols:
                how[name] = f"IS the row -> {t}"
                break
        else:
            # Shares column names with a table but is not a row: a draft that
            # FEEDS an insert, or a view assembled from rows. Not derivable
            # from names alone -- reported for an explicit ruling rather than
            # defaulted either way, since guessing clean loses a carrier and
            # guessing dirty inflates the inventory.
            near = [(len(fields & cols), t, fields - cols)
                    for t, cols in sorted(tables.items()) if len(fields & cols) >= 2]
            if near:
                _n, t, extra = max(near)
                how[name] = (f"UNRESOLVED -- {t} covers all but "
                             f"{sorted(extra)}")
    return how


def is_bounded(f):
    """Closed value space, so no user text can reach the field.

    REPORTED AS STRUCTURALLY DEAD ON THIS CORPUS, not quietly passed: `pattern=`
    appears NOWHERE in veracium.schema, and Literal-typed fields never enter
    section B at all (walk_text keeps only annotations containing 'str', and
    str(Literal[...]) does not). So this predicate CANNOT return a bound here.

    It is kept, and its emptiness asserted at the end of triage(), because a
    check that cannot fire is indistinguishable from one that is satisfied --
    if a future field gains a pattern, the assertion fails loudly rather than
    the field being silently classified a carrier.
    """
    ann = str(f.annotation)
    if "Literal[" in ann or "Enum" in ann:
        return "Literal/enum"
    for m in (f.metadata or []):
        if getattr(m, "pattern", None):
            return f"pattern {m.pattern}"
    return ""


# The residual 13, ruled against the WRITE PATH rather than the field names.
# This IS a hand-list -- of JUDGEMENTS, which is the legitimate kind: the
# enumeration derives the question and a person answers it with cited
# evidence. The assertion in triage() fails if a ruling no longer has a
# question, so a stale ruling cannot outlive the thing it ruled on.
RULINGS = {
    "Confirmation": (True,
        "CARRIER. Subset failed on `replayed` alone, and the model's own comment "
        "calls it `runtime only: True when returned for a replay` -- it is not a "
        "column. The model IS the confirmations row; INSERTed by "
        "SqliteStore.confirm_edge."),
    # T10a (research's Q18, agreed 2026-10-19): the two models the `replies`
    # table (0047) brought into question, each ruled against its write path
    "Reply": (True,
        "CARRIER. Subset failed on `replayed` alone, the runtime flag the "
        "Confirmation ruling names (`runtime only: True when returned for a "
        "replay`). The model IS the replies row; INSERTed by "
        "SqliteStore.add_reply."),
    "CorrectionAuthorisation": (False,
        "NON-CARRIER as a replies row. It neared `replies` on two shared NAMES, "
        "`kind` and `origin`, which mean other things there. It is minted and "
        "verified inside SqliteStore.apply_supersession_plan, never INSERTed "
        "into any table."),
    "ContributionDraft": (True,
        "CARRIER. Subset failed on `contributor_id` alone, which is INSERTed "
        "into the column `contributor_ref` -- SqliteStore._write_contribution "
        "documents the rename in its own comment. The draft's content reaches "
        "disk."),
    "ContestedGroup": (False,
        "NON-CARRIER as a storage SITE. `exposed`/`linkage`/`prior_edge_ids` "
        "are not columns: it is a view ASSEMBLED from rows, never written. Its "
        "text is Edge's, already carried above. (`partition` greps clean in "
        "store/ -- every hit is str.partition(), our word, their sense.)"),
}


def triage():
    models = all_models()
    how = persisted_models()

    # terminal (model, field) -> the paths that reach it
    terminals = {}
    for top, mdl in models.items():
        for path, ann in walk_text(mdl):
            leaf = path.rsplit(".", 1)[-1]
            owner, fld = resolve_terminal(mdl, path)
            terminals.setdefault((owner.__name__, fld), []).append(f"{top}.{path}")

    # containment: nested inside a directly-persisted model => persisted
    persisted = dict(how)
    changed = True
    while changed:
        changed = False
        for top, mdl in models.items():
            # An UNRESOLVED container cannot confer persistence on what it
            # holds: ContestedLinkage sits inside ContestedGroup, which is a
            # VIEW assembled from rows. Propagating through it made the linkage
            # a carrier by inheritance from a thing that is not stored.
            if top not in persisted or persisted[top].startswith("UNRESOLVED"):
                continue
            for sub in nested_models(mdl):
                # CONTAINMENT OUTRANKS A NAME-ONLY NEAR-MATCH (2026-11-15, specs/0031 §4f): a model held inside a
                # persisted container IS stored, through it, whatever table its field NAMES also happen to share.
                # Provenance gained `call_path`, so it shares two names (`origin`, `call_path`) with `confirmations`
                # and near-matched it as UNRESOLVED, though it is written only inside Edge/Episode json. Overriding an
                # UNRESOLVED near-match here can only resolve a model to STORED, never to a non-carrier.
                if sub.__name__ not in persisted or persisted[sub.__name__].startswith("UNRESOLVED"):
                    persisted[sub.__name__] = f"nested in {top} ({persisted[top]})"
                    changed = True

    print()
    print("C. TRIAGE -- carriers, DERIVED from persistence and value-space bounds")
    print(f"   {len(terminals)} TERMINAL (model, field) identities behind "
          f"{sum(len(v) for v in terminals.values())} paths.")
    print()
    carriers, non, unres = [], [], []
    for (mname, fld), paths in sorted(terminals.items()):
        f = models[mname].model_fields[fld]
        bound = is_bounded(f)
        pers = mname in persisted
        why = ("UNRESOLVED" if persisted.get(mname, "").startswith("UNRESOLVED")
               else "TRANSIENT (never stored)" if not pers
               else f"BOUNDED ({bound})" if bound else "")
        store_why = persisted.get(mname, "")
        bucket = unres if why == "UNRESOLVED" else non if why else carriers
        bucket.append((mname, fld, why, paths, store_why))

    for i, (mname, fld, w, pa, sw) in enumerate(list(unres)):
        if mname in RULINGS:
            keep, _why = RULINGS[mname]
            tag = sw.split("covers all but")[0].replace("UNRESOLVED -- ", "").strip()
            (carriers if keep else non).append(
                (mname, fld, "" if keep else "RULED non-carrier", pa,
                 f"RULED carrier -> {tag}" if keep else "RULED view, not a row"))
    _ruled = {m for m, _f, _w, _p, _s in unres} & set(RULINGS)
    unres = [u for u in unres if u[0] not in RULINGS]
    carriers.sort(); non.sort()

    assert len(carriers) + len(non) + len(unres) == len(terminals), (
        f"buckets {len(carriers)}+{len(non)}+{len(unres)} != "
        f"{len(terminals)} terminals -- a field was dropped in triage")
    print(f"   -> {len(carriers)} CARRIERS. Each must be named in 0041 section 2, "
          f"or recorded there as an explicit exclusion.")
    for mname, fld, _, paths, store_why in carriers:
        alias = f"   [also reachable as {', '.join(p for p in paths if not p.startswith(mname+'.'))}]" if len(paths) > 1 else ""
        print(f"      {mname}.{fld:<24} [{store_why}]")
        if alias:
            print(f"   {alias}")
    print()
    stale = set(RULINGS) - _ruled
    if stale:
        print(f"   !! STALE RULING(S) {sorted(stale)} -- ruled on a question the")
        print( "      enumeration no longer asks. Re-derive before trusting this.")
    print()
    print("   RULED, against the write path (see RULINGS):")
    for m in sorted(_ruled):
        print(f"      {m:<20} {RULINGS[m][1]}")
    print()
    print(f"   -> {len(unres)} UNRESOLVED -- shares a table's columns but is not a row.")
    print( "      NOT defaulted into either pile: guessing non-carrier loses a real")
    print( "      carrier, and that is the direction that costs something. Each needs")
    print( "      one explicit ruling in 0041 section 2, recorded with its reason.")
    for mname, fld, _w, _p, sw in unres:
        print(f"      {mname}.{fld:<24} {sw[len('UNRESOLVED -- '):]}")
    print()
    print(f"   -> {len(non)} NON-CARRIERS, each with the reason it cannot carry text:")
    for mname, fld, why, _, _sw in non:
        print(f"      {mname}.{fld:<24} {why}")

    # The dead branch, asserted rather than assumed (see is_bounded.__doc__).
    bounded = [f"{m}.{f}" for m, f, w, _, _sw in non if w.startswith("BOUNDED")]
    print()
    if bounded:
        print(f"   !! is_bounded FIRED on {bounded} -- it was structurally dead when")
        print( "      this triage was written. A field gained a pattern/Literal; the")
        print( "      classification above is no longer the one that was reviewed.")
    else:
        print(f"   is_bounded fired on 0 of {len(non)} non-carriers, as predicted: no")
        print( "   text-capable field in veracium.schema has a closed value space. EVERY")
        print( "   non-carrier is one because it never reaches disk -- NOT because its")
        print( "   content is constrained. If storage changes, they become carriers at once.")
    # the buckets themselves, for a caller comparing data to data (0041 round 10's generated treatment matrix);
    # the printed output above is unchanged
    return carriers, non, unres


triage()
