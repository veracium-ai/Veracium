"""0047 §4d (R5; the 0045-0047 round-1 reviewer's R1-05): the carrier inventory by COMPLEMENT.

A search for code that reads a new field finds only the code that already reads it — never a consumer that FORGOT it
(the reviewer's point about `grep .ungrounded`). So this census starts from where a fact's CONTENT leaves the store,
with three keys over the AST of src/:
  (a) every function that reads an edge's `.object`;
  (b) every function that serialises a model whole (`model_dump`, `model_dump_json`);
  (c) every function that CONSTRUCTS a fact-carrying result type. The types are DERIVED, never listed: a class with an
      annotated field whose type names `Edge` — or, transitively, names a class that does — quoted annotations parsed
      as expressions. Key (c) finds the sites that hand whole facts to a caller without ever reading `.object`.
A function is keyed by its QUALIFIED name within its module (`Memory.correct`, `assemble._obj`), so a new method that
shares a name with a classified one is a new site, not a silent member of the old classification.

Each censused function must carry a DISPOSITION from 0047 §4d (research's rules draft 3.3, sha16 5cefe166):
  RENDER       an assertion surface: a challenged fact is WITHHELD there, whatever its grounding value (0047 v1.8 §4d)
  CONTESTED    contested-group construction/render: an assertion surface, so a challenged member is withheld there too
  PROACTIVE    the proactive surface: an assertion surface, so a challenged fact is withheld wherever it renders facts
  WIKI         compiled-wiki input selection: challenged facts EXCLUDED; eviction + in-flight fence on a reply write
  ASOF         historical rendering: the unit from the CURRENT acts — T is valid time and selects facts, never acts
               (0047 INV-R20; the round-2 verdict's correction #1)
  COLLAPSE     render-time duplicate collapse: members whose acts differ are NOT collapsed (§4e)
  RAW          a structured return a caller may render: carries the open-challenge count and g(e)
  EXPORT       portability: §4f (rows carried in full; default import vs trusted restore)
  INTERNAL     not an output of a fact's content: planning, scoring, digests, store writes (reason given)
  RULING       needs research's ruling before adoption (reason given)
`python carrier_inventory.py` prints the derived carrier types and the census by disposition, and exits 1 if any
censused function is UNCLASSIFIED (a new render path cannot land undecided), if a classification is STALE (it names a
function that no longer exists or no longer carries content), or if any site is still awaiting a RULING.
`tests/test_0047_carrier_inventory.py` runs it on the tree in every suite run, and drives each refusal on a planted
source tree. NOT claimed (0047 §8): a carrier none of the three keys sees.
"""
# Mutation-Matrix: tests/test_0047_carrier_inventory.py::test_the_inventory_refuses_each_planted_defect
from __future__ import annotations

import ast
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "src" / "veracium"

CLASSIFIED = {
    ("graph.py", "render_edges"): ("RENDER", "the recall detail block — the primary fact line"),
    ("budgets.py", "clamp_edge_line"): ("RENDER", "clamps a rendered fact line; the unit clamps WITH the marker, never away"),
    ("__init__.py", "Memory._fit_to_budget"): ("RENDER", "recall's budget assembly — the count is computed BEFORE selection"),
    ("__init__.py", "Memory._fit_to_budget._rel"): ("RENDER", "recall's tier key — the variants tier (cf. 0044 P-2)"),
    ("__init__.py", "Memory._build_contested"): ("CONTESTED", "builds contested groups from the edges"),
    ("__init__.py", "Memory._contested_line"): ("CONTESTED", "renders one contested group's line"),
    ("__init__.py", "Memory._contested_line._member"): ("CONTESTED", "renders one member inside a contested line"),
    ("proactive.py", "assemble"): ("PROACTIVE", "assembles the proactive block"),
    ("proactive.py", "assemble._obj"): ("PROACTIVE", "a fact's object as rendered proactively"),
    ("proactive.py", "assemble._obj_counted"): ("PROACTIVE", "the counted proactive object"),
    ("proactive.py", "assemble._class_rank"): ("INTERNAL", "proactive ordering only — what it ranks still renders through assemble"),
    ("proactive.py", "assemble._due_key"): ("INTERNAL", "proactive due-date ordering only"),
    # 0044 T5-2 (research's F3): the content read moved from compile._live_refusal_contention_edge_ids into the ONE
    # live-contention predicate, which the compiler's exclusion set and recall's contested groups both call
    ("contention.py", "is_live_refusal"): ("WIKI", "the compiler's input exclusion set (and recall's contested groups) — challenged facts join it"),
    ("asof/resolve.py", "render_line"): ("ASOF", "the historical renderer (0019 U5's marker landed here 84b50c2)"),
    ("graph.py", "value_groups"): ("COLLAPSE", "groups values for render-time collapse"),
    ("graph.py", "_collapse_survivor_order"): ("COLLAPSE", "orders a collapse group's survivor"),
    ("graph.py", "within_episode_order"): ("INTERNAL", "write-path planning (0003/within-episode): groups and orders one episode's edges for supersession; returns no fact content to any renderer"),
    ("__init__.py", "Memory._recall"): ("RAW", "builds `Recall` — `Recall.edges` hands whole facts to the caller"),
    ("__init__.py", "Memory._proactive"): ("RAW", "builds the proactive `Recall`"),
    ("asof/recall.py", "recall_at"): ("RAW", "the as-of `Recall`; it renders the CURRENT acts, whatever T (0047 INV-R20)"),
    ("asof/resolve.py", "_resolve_as_of"): ("RAW", "builds `AsOfFact`s — facts_valid_at's return, through resolve_as_of; the call's snapshot travels BESIDE the answer (0047 T10b S2-1)"),
    ("graph.py", "plan_correction"): ("INTERNAL", "builds a `SupersessionPlan`; a plan, not an output"),
    ("why.py", "_edge_dict"): ("RAW", "`veracium why`'s per-edge record"),
    ("why.py", "gather"): ("RAW", "`veracium why`'s biography"),
    ("dryrun.py", "_dump"): ("RAW", "`remember --dry-run`'s report of facts that WOULD be written"),
    ("portability.py", "export_memory"): ("EXPORT", "§8: full confirmation and reply rows"),
    ("portability.py", "import_memory"): ("EXPORT", "§8: default import vs trusted restore"),
    ("portability.py", "_preflight_and_commit"): ("EXPORT", "§8: destination ∪ incoming preflight, one transaction"),
    ("portability.py", "_act_preflight"): ("EXPORT", "§8 / 0008 §6e–§6f: each arriving act over the staged union, chronology over H"),
    ("portability.py", "_outcome_structure"): ("EXPORT", "outcome-chain structure on the boundary"),
    ("portability.py", "source_identity_projection"): ("EXPORT", "source identity on the boundary"),
    ("graph.py", "_build_supersession_plan"): ("INTERNAL", "planning (0012/0044); no text leaves"),
    ("graph.py", "_permute_contention_groups"): ("INTERNAL", "contention planning"),
    ("graph.py", "_lexical_scored"): ("INTERNAL", "retrieval scoring"),
    ("graph.py", "semantic_duplicate_of"): ("INTERNAL", "duplicate detection for the write path"),
    ("authority.py", "scope_fingerprint"): ("INTERNAL", "the CAS fingerprint"),
    ("semantic.py", "content_digest"): ("INTERNAL", "an embedding cache key"),
    ("semantic.py", "embedded_text"): ("INTERNAL", "the text embedded for retrieval; never rendered"),
    ("procedures.py", "describe_procedures._rel"): ("INTERNAL", "a reply cannot attach to a procedural edge (0047 v1.4 ruling, INV-R19); these surfaces never meet a challenge"),
    ("procedures.py", "describe_outcome"): ("INTERNAL", "a reply cannot attach to a procedural edge (0047 v1.4 ruling, INV-R19); these surfaces never meet a challenge"),
    ("procedures.py", "describe_procedures"): ("INTERNAL", "a reply cannot attach to a procedural edge (0047 v1.4 ruling, INV-R19); these surfaces never meet a challenge"),
    ("__init__.py", "Memory.correct"): ("INTERNAL", "a WRITE of an act episode naming the value as the act's object, never asserting it (0047 v1.4 ruling); an episode naming a challenged value does not carry the challenge (0047 §8, NOT claimed)"),
    ("__init__.py", "Memory.dispute"): ("INTERNAL", "a WRITE of an act episode naming the value as the act's object, never asserting it (0047 v1.4 ruling); an episode naming a challenged value does not carry the challenge (0047 §8, NOT claimed)"),
    ("__init__.py", "Memory.record_outcome"): ("INTERNAL", "a write of an outcome act episode naming the value, never asserting it (0047 v1.4 ruling)"),
    ("store/sqlite.py", "SqliteStore._upsert_edge_row"): ("INTERNAL", "store write"),
    # R-II round 2's RII-R2-01: the ONE projection of what a compiled wiki may assert, compared, never rendered
    ("schema.py", "assertion_view"): ("INTERNAL", "the wiki's assertion view (RII-R2-01): compared by the store's eviction and recall's bind, never rendered"),
    ("store/sqlite.py", "SqliteStore.apply_supersession_plan"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore.confirm_edge"): ("INTERNAL", "store write (0008): its refusal message names the edge, not its content; its act episode names the confirmed value as the act's OBJECT (0047 v1.4's ruling for act episodes; §8 NOT claimed; confirm refuses under an open challenge, so the episode predates any challenge)"),
    ("ingest.py", "ingest_event"): ("INTERNAL", "the write path (0045 §2, T9): it re-validates the built edge with its grounding axis before storing it; no text leaves, and a challenge (0047) can only follow the write"),
    # T10b: the read half's two matchers. Neither renders: they decide WHICH facts the assertion surfaces withhold
    ("challenge.py", "_is_twin"): ("INTERNAL", "F7's same-value test (0047 T10b): compares value keys to decide withholding; never renders the object"),
    ("store/sqlite.py", "SqliteStore.challenge_snapshot"): ("INTERNAL", "0047 §4d's one snapshot: reads each challenged record to match its twins; the record is never handed to a caller"),
    ("store/sqlite.py", "SqliteStore._redact_in_txn"): ("INTERNAL", "redaction — the reply's text joins its treatment map (0041 amendment)"),
    ("store/sqlite.py", "SqliteStore.commit_outcome_import_plan"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore._logical_request_digest._dump"): ("INTERNAL", "serialises a plan for its replay digest; never rendered"),
    ("store/sqlite.py", "SqliteStore._abandon"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore._claim_inputs"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore._invalidate_edge_row"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore._logical_request_digest"): ("INTERNAL", "a digest"),
    ("store/sqlite.py", "SqliteStore._outcome_digest_v2"): ("INTERNAL", "a digest"),
    ("store/sqlite.py", "SqliteStore._recompute_edge_row"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore._reinstate_edge_row"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore._reinstate_episode_row"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore._retire_episode_row"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore.add_episode"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore.append_outcome_if_head"): ("INTERNAL", "store write"),
    ("store/sqlite.py", "SqliteStore.write_consolidation_output_if_current"): ("INTERNAL", "store write"),
    ("store/migration.py", "_migrate_outcome_chains"): ("INTERNAL", "schema migration"),
    ("contribution.py", "effect_payload"): ("INTERNAL", "a contribution digest payload"),
    ("contribution.py", "raw_request_snapshot"): ("INTERNAL", "a request snapshot for the CAS"),
    ("contribution.py", "verify_snapshot_against_plan"): ("INTERNAL", "a verifier"),
    ("selfcheck.py", "_check_revocation.snap"): ("INTERNAL", "selfcheck's own snapshot"),
}


def _annotation_names(ann) -> set:
    """Every name an annotation mentions, quoted forward references parsed as expressions."""
    out = set()
    for n in ast.walk(ann):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            try:
                out |= _annotation_names(ast.parse(n.value, mode="eval"))
            except SyntaxError:
                pass
    return out


def carrier_types(src: pathlib.Path = SRC) -> set:
    """Every class in src/ with an annotated field whose type names `Edge`, or names a class already found (to a fixed
    point) — a result type that hands whole facts to a caller WITHOUT reading `.object`. Derived, never listed."""
    fields = defaultdict(set)
    for f in sorted(src.rglob("*.py")):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ClassDef):
                for st in node.body:
                    if isinstance(st, ast.AnnAssign):
                        fields[node.name] |= _annotation_names(st.annotation)
    found = {"Edge"}
    while True:
        new = {c for c, names in fields.items() if c != "Edge" and names & found} - found
        if not new:
            return found - {"Edge"}
        found |= new


def _owners(tree) -> dict:
    """{id(node): qualified name of the innermost function enclosing it} — `Class.method`, `outer.inner`."""
    owner = {}

    def visit(n, prefix):
        for c in ast.iter_child_nodes(n):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = prefix + c.name
                for sub in ast.walk(c):
                    if sub is not c:
                        owner[id(sub)] = q        # an inner function, visited next, overwrites its own subtree
                visit(c, q + ".")
            elif isinstance(c, ast.ClassDef):
                visit(c, prefix + c.name + ".")
            else:
                visit(c, prefix)

    visit(tree, "")
    return owner


def census(src: pathlib.Path = SRC) -> dict:
    """{(module, qualified function): sorted lines} for every `.object` read, every whole-model serialisation, and every
    construction of a fact-carrying result type in src/."""
    out = defaultdict(set)
    carriers = carrier_types(src)
    for f in sorted(src.rglob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        owner = _owners(tree)
        mod = str(f.relative_to(src))
        for node in ast.walk(tree):
            hit = (isinstance(node, ast.Attribute) and node.attr == "object" and isinstance(node.ctx, ast.Load)) or (
                isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("model_dump", "model_dump_json")) or (
                isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute))
                and (node.func.id if isinstance(node.func, ast.Name) else node.func.attr) in carriers)
            if hit:
                out[(mod, owner.get(id(node), "<module>"))].add(node.lineno)
    return {k: sorted(v) for k, v in out.items()}


def main(src: pathlib.Path = SRC, classified: dict = CLASSIFIED) -> int:
    print("fact-carrying result types (derived):", ", ".join(sorted(carrier_types(src))) or "(none)")
    found = census(src)
    unclassified = sorted(set(found) - set(classified))
    stale = sorted(set(classified) - set(found))
    by = defaultdict(list)
    for k in sorted(found):
        by[classified.get(k, ("UNCLASSIFIED", ""))[0]].append(k)
    for disp in sorted(by):
        print(f"{disp} ({len(by[disp])})")
        for m, fn in by[disp]:
            print(f"    {m}:{fn}  L{found[(m, fn)][0]}  — {classified.get((m, fn), ('', ''))[1]}")
    for k in unclassified:
        print(f"UNCLASSIFIED: {k[0]}:{k[1]} — a new site; give it a disposition")
    for k in stale:
        print(f"STALE: {k[0]}:{k[1]} is classified but no longer reads a fact's content — remove it")
    ruling = by.get("RULING", [])
    for m, fn in ruling:
        print(f"RULING PENDING: {m}:{fn} — decide it before adoption")
    print(f"censused {len(found)} functions; unclassified {len(unclassified)}; stale {len(stale)}; RULING {len(ruling)}")
    return 1 if (unclassified or stale or ruling) else 0


if __name__ == "__main__":
    sys.exit(main())
