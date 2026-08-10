"""R7-5 (0014 round 7): the retired-contract gate must BITE — each 0014 registry entry
is proven, adversarially, against the EXACT retired forms that motivated it (the forms
the reviewer quoted from submitted packages, verbatim). A pattern that fails to match
its own motivating text is a dead entry reading as coverage — the failure mode this
file exists to prevent, twice caught by review (v9's uncommitted script; v10's
too-narrow patterns)."""
import re
import sys
import pathlib

SPECS = pathlib.Path(__file__).resolve().parent.parent / "specs"
sys.path.insert(0, str(SPECS))


def _normalise(text):
    import importlib
    lw = importlib.import_module("lint_withdrawn")
    return lw._normalise(text)


def _matches(fixture: str) -> bool:
    from withdrawn_phrases import WITHDRAWN
    flat = _normalise(fixture)
    return any(re.search(pat, flat, re.IGNORECASE) for pat, _, _ in WITHDRAWN)


# the EXACT submitted forms each round's disposition quoted as still-live.
# Every string below is WITHDRAWN text quoted as adversarial FIXTURES — the
# linter's marker rule exempts this block by design (quoted history, not a
# live restatement).
MOTIVATING_FORMS = [
    # R6-5 / R7-4 — emptiness
    "`payload` MAY be `{}` — an empty payload still records the consumption",
    "`{}` is legal ONLY where no state is consulted-and-transferred",
    "{} only at absorption's no-transfer case",
    "the empty-payload consumption (a stale contributor",
    "a no-payload consumption. This is a",
    "every CONSUMED CONTRIBUTOR (payload empty or not)",
    "which may legitimately be empty",
    "or the no-transfer form at absorption only",
    # R6-5/R7-4 — the digest split
    "the pre-image ENTERS `0003`'s `_logical_request_digest`",
    "the drafts ENTER `0003`'s `_logical_request_digest`",
    # R6-5 — reversal
    "reversible — by direct restoration at absorption",
    "the record carries `prior_survivor_values` — direct restoration material",
    # R6-5 — format
    "**no `FORMAT_VERSION` change**",
    # R5-3 — the SQL column
    "a NEW nullable `episodes.consolidation_output_index INTEGER` column",
    # 0012
    "reinforcement never persists the incoming edge",
]


def test_every_registry_entry_catches_its_motivating_form():
    missed = [f for f in MOTIVATING_FORMS if not _matches(f)]
    assert not missed, (
        "retired forms the registry does NOT catch (dead coverage — R7-5):\n  "
        + "\n  ".join(repr(m) for m in missed))


def test_the_gate_is_clean_on_the_current_tree():
    """The registry bites (above) AND the current specs contain no live retired
    text — the two halves of the R6-6/R7-5 mechanism, asserted together."""
    import importlib
    lw = importlib.import_module("lint_withdrawn")
    v = lw.violations()
    assert not v, "live retired phrases in the tree:\n" + "\n".join(map(str, v))
