#!/usr/bin/env python3
"""0038 §8 — independent CROSS-FAMILY model pass over the oracle pack.

A sibling of `paper2/instrument/model_pass.py`, which is hardcoded to the
paper-2 semantic-relation pack (fields `a`/`b`, relation labels). Its
DISCIPLINE is copied here deliberately, item by item:

  * CROSS-FAMILY. The corpus, the registry and the rubric were all written by
    a Claude-family session, so an OpenAI model is the independent family.
  * TEMPERATURE 0. Reproducible, and it makes the repeated items a determinism
    check rather than noise.
  * BLIND BY CONSTRUCTION. This module reads `oracle_pack_v2_74.json` and
    NOTHING ELSE. There is no import of `verb_registry`, no path to
    `oracle_labelling_KEY.json`, and no path to the human's labels. That is
    what makes this a second labelling rather than a check of the first, and
    it is a property of the code, not a promise in a comment -- see
    `test_blind_by_construction` at the bottom, which greps this file.
  * THE SAME QUESTION. The rubric text below is copied VERBATIM from the
    sections of `RUBRIC.md` that state the task: the four answers, the one
    principle, and the note on AMBIGUOUS. The procedural sections of that file
    (repeats, disclosures, keybindings) are NOT included -- they are
    instructions to a human operator, not part of the question. A second
    labelling against a different rubric measures rubric drift, not agreement.
  * ONE attempt; ONE retry only on an unparseable reply; then recorded
    `unparsed`.

    python3 model_pass_0038.py --limit 3     # smoke test
    python3 model_pass_0038.py               # full 74
"""
import argparse
import json
import os
import pathlib
import re
import sys

MODEL = "gpt-4.1-2025-04-14"
HERE = pathlib.Path(__file__).parent
PACK = HERE / "oracle_pack_v2_74.json"
OUT = HERE / "oracle_model_labels_v2.json"
PACK_SHA16 = "a656970c90b14ded"

SYSTEM = (
    "You are labelling stored memory records for a measurement instrument. "
    "Answer from the instruction and the stored episode alone. Do not "
    "speculate about context you were not given."
)

# --- VERBATIM from RUBRIC.md, sections "The four answers", "The one
# --- principle", and "Using option 4".
RUBRIC = """You are deciding, for each stored episode: what does it assert about the
user's relationship to the action?

The four answers

1 — PERFORMED. The episode asserts the user *carried the action out* — either
on an occasion, or habitually.

2 — COMMITTED. The episode asserts the user *decided on, adopted, or bound
themselves to* the action — without asserting they did it. Deciding and doing
are separate acts.

3 — REPORTED. The episode asserts only that something was *said, instructed,
preferred, or noted*. No performance, no commitment.

4 — AMBIGUOUS. The episode genuinely supports more than one reading.

The one principle

The disposition follows what the episode asserts about the user's relation to
the action. A reporting frame does not change the content it reports.

"Stated…" can open all three and settles none of them: what matters is what
was stated. A stated *preference* is a preference. A stated *intention* is a
commitment. A stated *practice* is a claim about what the user habitually does.

Using option 4

Choosing AMBIGUOUS is a finding, not a failure or a cop-out.

---

THE INSTRUCTION THAT WAS GIVEN
{instruction}

THE EPISODE THE SYSTEM STORED
{episode}

Reply with ONLY the single digit 1, 2, 3 or 4."""

_VALID = {"1": "performed", "2": "committed", "3": "reported", "4": "ambiguous"}


def parse(text):
    m = re.search(r"[1-4]", (text or "").strip())
    return _VALID.get(m.group(0)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    import hashlib
    got = hashlib.sha256(PACK.read_bytes()).hexdigest()[:16]
    if got != PACK_SHA16:
        sys.exit(f"REFUSING: pack is {got}, expected {PACK_SHA16}")

    items = json.loads(PACK.read_text())
    if args.limit:
        items = items[: args.limit]

    from openai import OpenAI
    client = OpenAI()

    out, unparsed = {}, 0
    for n, it in enumerate(items, 1):
        prompt = RUBRIC.format(instruction=it["the_instruction_that_was_given"],
                               episode=it["the_episode_the_system_stored"])
        label = None
        for attempt in (0, 1):
            r = client.chat.completions.create(
                model=MODEL, temperature=0.0, max_tokens=8,
                messages=[{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": prompt}])
            label = parse(r.choices[0].message.content)
            if label:
                break
        if not label:
            label = "unparsed"
            unparsed += 1
        out[it["item_id"]] = label
        print(f"  {n:>3}/{len(items)}  {it['item_id']:<12} {label}")

    OUT.write_text(json.dumps(
        {"model": MODEL, "temperature": 0.0, "n": len(out),
         "pack_sha16": got, "unparsed": unparsed,
         "rubric_source": "RUBRIC.md (task sections, verbatim)",
         "labels": out}, indent=1) + "\n")
    print(f"\n  {len(out)} labelled by {MODEL}, unparsed={unparsed}")
    print(f"  -> {OUT}")


def test_blind_by_construction():
    """The blinding is a property of this file, asserted here rather than
    promised in the docstring.

    Checked over the AST, NOT by grepping the source: the first cut grepped
    for the string 'verb_registry' and fired on this module's own docstring,
    where the phrase 'no import of verb_registry' truthfully says the opposite.
    A check that cannot tell a mention from a use is not a check.
    """
    import ast
    tree = ast.parse(pathlib.Path(__file__).read_text())
    # SCAN THE PROGRAM, NOT THE CHECKER. This function's own body names the
    # forbidden files in order to forbid them, and its docstring describes
    # them; both are mentions. Five successive versions of this check matched
    # its own text -- the docstring, the ".json" suffix, the output filename,
    # the docstring again, then the FORBIDDEN tuple. The scope was the bug
    # every time: a checker that includes itself in what it checks cannot tell
    # a use from a mention, which is the only distinction it exists to make.
    tree.body = [n for n in tree.body
                 if not (isinstance(n, ast.FunctionDef)
                         and n.name == "test_blind_by_construction")]

    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert "verb_registry" not in imported, "blindness broken: imports the registry"

    # Every string CONSTANT that is not a DOCSTRING. Docstrings are excluded
    # because prose that says "there is no import of verb_registry" is a
    # MENTION and the thing being detected is a USE -- the distinction this
    # check exists to make, which four successive versions of it failed to
    # make about their own text.
    docstrings = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", None)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                docstrings.add(id(b[0].value))
    consts = {n.value for n in ast.walk(tree)
              if isinstance(n, ast.Constant) and isinstance(n.value, str)
              and id(n) not in docstrings}
    # DENY the contaminating sources by name; do not allowlist. Three
    # rewrites of this loop matched the checker itself -- the docstring's
    # honest mention of the registry, then the bare ".json" suffix it compares
    # against, then its own OUTPUT file, which is a write and not a leak. An
    # allowlist over "every string ending .json" was the wrong shape: it had to
    # be re-widened for each innocent constant, and each widening was a chance
    # to admit a real one. What actually must not appear is a SOURCE OF TRUTH.
    FORBIDDEN = ("oracle_labelling_KEY", "KEY.json", "verb_registry",
                 "oracle_labels_")           # the key, the registry, the human
    for c in consts:
        for f in FORBIDDEN:
            assert f not in c, f"blindness broken: names {c}"
    for name in ("PACK", "OUT"):
        assert name in {t.id for n in ast.walk(tree)
                        if isinstance(n, ast.Assign)
                        for t in n.targets if isinstance(t, ast.Name)}


if __name__ == "__main__":
    main()
