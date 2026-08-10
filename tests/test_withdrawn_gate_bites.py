"""R7-5/R8-5 (0014 rounds 7-8): the retired-contract gate must BITE — and each entry
must be proven INDIVIDUALLY. Round 7 proved fixtures against the registry; round 8
found the proof too weak: matching *any* entry lets an overlapping broad pattern mask
a dead one (dead coverage with extra steps). Every motivating fixture below therefore
names the SPECIFIC rule_id that owns it, and the test asserts THAT entry matches —
an entry whose own fixture no longer fires it fails loudly, no neighbour can cover
for it."""
import re
import sys
import pathlib

SPECS = pathlib.Path(__file__).resolve().parent.parent / "specs"
sys.path.insert(0, str(SPECS))


def _normalise(text):
    import importlib
    lw = importlib.import_module("lint_withdrawn")
    return lw._normalise(text)


def _rule(rule_id):
    from withdrawn_phrases import WITHDRAWN
    matches = [e for e in WITHDRAWN if e[0] == rule_id]
    assert len(matches) == 1, f"rule_id {rule_id!r} must exist exactly once in the registry"
    return matches[0]


# (rule_id, fixture): the EXACT submitted form each round's disposition quoted as
# still-live, mapped to the ONE registry entry that owns it (R8-5). Every string
# below is WITHDRAWN text quoted as adversarial FIXTURES — the linter's marker rule
# exempts this block by design (quoted history, not a live restatement).
MOTIVATING_FORMS = [
    # R6-5 / R7-4 — emptiness
    ("0014-payload-empty-legal", "`payload` MAY be `{}` — an empty payload still records the consumption"),
    ("0014-payload-empty-legal", "`{}` is legal ONLY where no state is consulted-and-transferred"),
    ("0014-payload-empty-legal", "{} only at absorption's no-transfer case"),
    ("0014-empty-consumption", "the empty-payload consumption (a stale contributor"),
    ("0014-empty-consumption", "a no-payload consumption. This is a"),
    ("0014-empty-consumption", "every CONSUMED CONTRIBUTOR (payload empty or not)"),
    ("0014-legitimately-empty", "which may legitimately be empty"),
    ("0014-no-transfer-form", "or the no-transfer form at absorption only"),
    # R8-5 — the evasion FRAMING (empty payloads abort; the evasion is no-transfer)
    ("0014-empty-payload-evasion", "The adversary's cheapest evasion is the empty payload"),
    ("0014-empty-payload-evasion", "and the empty-payload evasion is closed with it"),
    # R8-1 — the concurrent-preflight loser must REPLAY, never conflict
    ("0014-loser-may-conflict", "one commits, the other replays-or-conflicts per its receipt"),
    ("0014-loser-may-conflict", "one commits, the other replays or conflicts per its receipt"),
    # R6-5/R7-4 — the digest split
    ("0014-preimage-into-request-digest", "the pre-image ENTERS `0003`'s `_logical_request_digest`"),
    ("0014-preimage-into-request-digest", "the drafts ENTER `0003`'s `_logical_request_digest`"),
    # R6-5 — reversal
    ("0014-direct-restoration", "reversible — by direct restoration at absorption"),
    ("0014-direct-restoration", "the record carries `prior_survivor_values` — direct restoration material"),
    # R6-5 — format
    ("0014-no-format-bump", "**no `FORMAT_VERSION` change**"),
    # R5-3 — the SQL column
    ("0014-sql-column", "a NEW nullable `episodes.consolidation_output_index INTEGER` column"),
    # R4-6 — valid_from in the consolidation payload
    ("0014-validfrom-consolidation", "valid_from is in the consolidation payload set"),
    # 0012
    ("0012-reinforcement-never-persists", "reinforcement never persists the incoming edge"),
]


def test_every_registry_entry_catches_its_motivating_form_individually():
    """R8-5: the NAMED entry must match its fixture — matching any other entry
    does not count, so a dead entry cannot hide behind a broad neighbour."""
    missed = []
    for rule_id, fixture in MOTIVATING_FORMS:
        rid, pat, _, _ = _rule(rule_id)
        if not re.search(pat, _normalise(fixture), re.IGNORECASE):
            missed.append((rule_id, fixture))
    assert not missed, (
        "registry entries that do NOT catch their own motivating form "
        "(dead coverage — R7-5/R8-5):\n  "
        + "\n  ".join(f"{r}: {f!r}" for r, f in missed))


def test_every_0014_entry_has_a_motivating_fixture():
    """The inverse direction: a 0014-era entry with NO fixture is unproven —
    exactly the dead-entry shape R8-5 names. Every 0014/0012 entry must appear
    at least once above."""
    from withdrawn_phrases import WITHDRAWN
    covered = {rule_id for rule_id, _ in MOTIVATING_FORMS}
    modern = [e[0] for e in WITHDRAWN if e[0].startswith(("0014-", "0012-"))]
    unproven = [rid for rid in modern if rid not in covered]
    assert not unproven, (
        "registry entries with no motivating fixture (unproven — R8-5):\n  "
        + "\n  ".join(unproven))


def test_the_gate_is_clean_on_the_current_tree():
    """The registry bites (above) AND the current specs contain no live retired
    text — the two halves of the R6-6/R7-5 mechanism, asserted together."""
    import importlib
    lw = importlib.import_module("lint_withdrawn")
    v = lw.violations()
    assert not v, "live retired phrases in the tree:\n" + "\n".join(map(str, v))
