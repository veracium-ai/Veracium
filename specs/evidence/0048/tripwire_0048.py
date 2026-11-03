"""0048 round 2: the token tripwire, the second instrument beside census_0048 (it does not share the census's scope).

    python tripwire_0048.py <tree-root>            # JSON {file: {trigger: count}}, the shape the snapshot compares
    python tripwire_0048.py <tree-root> --sites    # one line per hit, for hand classification (the full line text: the snapshot keys on it)

The census RESOLVES forms, and every form it was not written for passes it (stage 2: v1 missed 20; the widened census
missed 11 more, dev's campaign). This tool resolves nothing. It counts every TOKEN that any unvalidated write of
`confidence`, or any write of the edges table, must contain, per (file, trigger), and a committed hand-classified
snapshot is compared with it: a new occurrence fails until someone classifies it. A moved line does not.

Triggers, from Python's own tokenizer (comments and docstrings excluded; they cannot write):
  NAME   confidence model_copy model_construct construct copy __dict__ vars setattr __setattr__ __replace__ partial
         getattr exec eval pickle copyreg shelve marshal deepcopy __setstate__ __getstate__ __reduce__ __reduce_ex__
  STRING any non-docstring string (f-string literal parts included) containing `confidence` or `edges` as a word,
         or a SQL write verb (`update`, `insert`, `replace`, any case) as a word: a new edge writer can reuse a
         table name already held in a classified variable (`f"UPDATE {table} SET json=?"` beside sqlite.py's
         `table = "edges" if kind == "edge" else "episodes"`) and carry no `edges` token, so the VERB is the trigger
         (stage 2b, research: that plant passed the census, the tripwire's counts and the snapshot compare)

Residual, by construction, and named rather than hidden: a write that contains none of these tokens. For a Python
write, the field name must be built from parts (`'confi' + 'dence'`) AND reach an unvalidated path through none of the
NAMEs above (a memory-level route such as ctypes, or a C extension). For SQL, the write VERB must be built from parts
(`'UP' + 'DATE …'`), or the statement read from outside src/veracium/*.py (a .sql resource). A computed `getattr`
name or exec/eval still fires: the NAME is the trigger. Reusing an already-declared writer (a new call to one of the
census's writers) is not a new writer. Durable protection is §4C's validating serialiser at the store, not this tool.
"""
# Mutation-Matrix: tests/test_0048_evidence.py::test_tripwire_0048_fires_on_every_planted_attack
import ast
import io
import json
import pathlib
import re
import sys
import tokenize

NAMES = {"confidence", "model_copy", "model_construct", "construct", "copy", "__dict__", "vars", "setattr",
         "__setattr__", "__replace__", "partial", "getattr", "exec", "eval",
         # serialisation round trips restore state without validation (stage 2b: a pickle round trip with the
         # float's bytes swapped stores 2.0, and carries none of the names above)
         "pickle", "copyreg", "shelve", "marshal", "deepcopy", "__setstate__", "__getstate__", "__reduce__",
         "__reduce_ex__",
         # 0048 round 4 (research's stage 2, S2-04): a code object swapped onto a guarded function
         "__code__"}
WORDS = re.compile(r"\b(confidence|edges)\b")
VERBS = re.compile(r"\b(update|insert|replace)\b", re.I)

root = pathlib.Path(sys.argv[1]).resolve()
src = root / "src" / "veracium"
counts, sites = {}, []
for f in sorted(src.rglob("*.py")):
    rel = f.relative_to(root).as_posix()
    text = f.read_text()
    doc = set()                                          # start lines of docstrings
    for n in ast.walk(ast.parse(text)):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) \
                and isinstance(n.body[0].value.value, str):
            doc.add(n.body[0].lineno)
    for t in tokenize.generate_tokens(io.StringIO(text).readline):
        hits = []
        if t.type == tokenize.NAME and t.string in NAMES:
            hits = [t.string]
        elif t.type in (tokenize.STRING, tokenize.FSTRING_MIDDLE) and t.start[0] not in doc:
            hits = [f"str:{w}" for w in sorted(set(WORDS.findall(t.string)))]
            hits += ["str:sql-write"] if VERBS.search(t.string) else []
        for h in hits:
            counts.setdefault(rel, {}).setdefault(h, 0)
            counts[rel][h] += 1
            sites.append(f"{rel}:{t.start[0]} {h} {' '.join(t.line.split())}")

if "--sites" in sys.argv:
    print("\n".join(sites))
else:
    print(json.dumps(counts, indent=1, sort_keys=True))
print(f"# {sum(sum(v.values()) for v in counts.values())} hits in {len(counts)} files", file=sys.stderr)
