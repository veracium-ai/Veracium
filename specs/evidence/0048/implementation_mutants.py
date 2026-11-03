#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0048_implementation_mutants.py::test_the_table_check_refuses_each_tampered_table
"""0048 §6's planned mechanism mutants, against the IMPLEMENTATION (§4 A–D): every row demonstrated red.

Each row is a code edit run by the shared protocol (specs/evidence/mutation_protocol.py) on a copy of the tracked
tree, killed by assertion (or DID NOT RAISE) in ITS named cells, with an HONEST probe that still passes under it.
Beside them, per mutated file, a NO-OP control whose named cells must all pass, and one classifier negative control.
Row ids carry the invariant each demonstrates; the rows past §6's table are dev's own campaign (the next mutant of
each new check: the fallback, the swallow, the copied lifetimes, F2's table, the redaction check's place).

One §6 row is a DOUBLE mutant and is run by hand, stated rather than dropped: "decay write back to unvalidated
model_copy, entry check also removed" edits lifecycle.py (the entry check) AND store/sqlite.py (the stamp). The
protocol edits one file per mutant, and each half alone is equivalent by construction (a validated factor makes the
unvalidated copy write a valid value; a validated stamp catches an unvalidated factor at C). Its kill (N4d's cells,
by assertion) is recorded in the implementation commit.

The three conditional-write rows (N4h) carry the LISTING's copy into the transition through the store's own `edges()`
read, so each is one file: a stale read taken INSIDE the transition would see B's commit and be no defect at all.

    $PY specs/evidence/0048/implementation_mutants.py --check     # fast: definitions, anchors, digests, every row good
    TMPDIR=/dev/shm $PY specs/evidence/0048/implementation_mutants.py --write
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

TABLE = HERE / "implementation" / "mutation-table.json"
SELF = "specs/evidence/0048/implementation_mutants.py"
CFG = "src/veracium/config.py"
LC = "src/veracium/lifecycle.py"
SQ = "src/veracium/store/sqlite.py"
G = "src/veracium/graph.py"
T = "tests/test_0048_decay_bounds.py"
EVT = "tests/test_0048_evidence.py"
SUBJECT = "implementation"
DIGESTED = (CFG, LC, SQ, G, "src/veracium/store/base.py", T, EVT, "specs/evidence/0048/census_0048.py",
            "specs/evidence/0048/tripwire_0048.py", "specs/evidence/0048/tripwire_0048_classified.tsv",
            "specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)

C = lambda name: f"{T}::{name}"                                                       # noqa: E731
VALIDATED = lambda v, f: C(f"test_config_bounds_are_validated[{v}-{f}]")             # noqa: E731
BOUNDARY = lambda v, f: C(f"test_boundary_configs_are_still_valid[{v}-{f}]")         # noqa: E731
ASSIGN = lambda v, f: C(f"test_config_bounds_hold_on_assignment[{v}-{f}]")           # noqa: E731
REFUSAL = lambda fa, fl: C(f"test_decay_config_refusal_writes_nothing[{fa}-{fl}]")   # noqa: E731
FACTOR = lambda fa, c: C(f"test_factor_is_validated_whatever_the_confidence[{fa}-{c}]")  # noqa: E731
N4I = lambda case: C(f"test_decay_keeps_the_shipped_result[{case}]")                 # noqa: E731
N4H = lambda case: C(f"test_expiry_is_decided_from_the_current_row[{case}]")         # noqa: E731
OTHER = C("test_other_fields_still_assign")
SHIPPED = C("test_lapse_and_confirm_keep_their_shipped_counts")
OUT_OF_BOUND = C("test_the_store_refuses_an_out_of_bound_edge")
GATE = C("test_every_edge_write_goes_through_the_validating_serialiser")
DECLARED = C("test_declared_bounds_hold_on_every_write_path")
TRIPWIRE = f"{EVT}::test_every_tripwire_hit_on_this_tree_is_classified"
REFUSAL_FX = lambda case, role: C(f"test_a_transition_of_an_edge_in_a_refusal_has_the_shipped_side_effects"  # noqa: E731
                                  f"[{case}-{role}]")
DUE_AT = lambda age: C(f"test_the_transition_itself_decides_due_ness_at_the_lifetime_boundary[{age}]")  # noqa: E731

_SET = "        if name in DECAY_BOUNDS:\n            validate_decay_bound(name, value)\n"
_V = '    decay_factor = validate_decay_bound("decay_factor", config.decay_factor)\n'
_F = '    confidence_floor = validate_decay_bound("confidence_floor", config.confidence_floor)\n'
_CALL = ("        outcome = store.expiry_transition(user_id, e.id, now=now, lifetimes=lifetimes, behaviors=behaviors,\n"
         "                                          decay_factor=decay_factor, confidence_floor=confidence_floor)\n")
_LOOP_HEAD = ('    for e in store.edges(user_id, active_only=True):\n'
              '        lifetime = lifetimes.get(e.volatility)\n'
              '        # the LISTING picks candidates; the transition decides on the row as committed when it runs\n'
              '        if lifetime is None or (now - e.provenance.observed_at).days <= lifetime:\n'
              '            continue\n' + _CALL)
_SHIPPED_LOOP = '''    from .schema import ExpiryBehavior as _B
    for e in store.edges(user_id, active_only=True):
        lifetime = lifetimes.get(e.volatility)
        if lifetime is None or (now - e.provenance.observed_at).days <= lifetime:
            continue
        b = behaviors[e.volatility]
        outcome = None
        if b == _B.LAPSE:
            store.invalidate_edge(e.id, now, "lapsed"); outcome = "lapsed"
        elif b == _B.DECAY:
            e.provenance = e.provenance.model_copy(update={"confidence": e.provenance.confidence * decay_factor})
            if e.provenance.confidence < confidence_floor:
                store.invalidate_edge(e.id, now, "decayed"); outcome = "decayed"
            else:
                store.add_edge(e)
        elif not e.needs_confirmation:
            e.needs_confirmation = True; store.add_edge(e); outcome = "flagged"
'''
_EDGES_RET = ('            return _SITE_EDGES_READ_FENCE.fire([Edge.model_validate_json(r[0]) for r in rows], '
              '"fence-applied", declined=not include_quarantined)\n')
_STASH = ('            setattr(self, "_listed", {**getattr(self, "_listed", {}), **{r[0][7:r[0].index(\'"\', 7)]: r[0] for r in rows}})\n'
          + _EDGES_RET)
_READ = ('            row = self._conn.execute("SELECT json, active FROM edges WHERE id=? AND user_id=?",\n'
         '                                     (edge_id, user_id)).fetchone()\n')
_STALE = '            _stale = (getattr(self, "_listed", {}).get(edge_id), 1)\n'
_DECAY_RETIRE = '                    self._invalidate_edge_row(edge_id, now, "decayed")     # stored confidence unchanged (N4i)\n'
_INV_WRITER = ('        self._write_edge_row("UPDATE edges SET active=0, json=? WHERE id=?", (), edge, (edge_id,),\n'
               '                             user_id=row[1], edge_id=edge_id, prior=row[0], kind="invalidated", reason=reason)\n')
_INV_DIRECT = ('        self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?", ({dump}, edge_id))\n'
               '        self._journal_edge_write(row[1], edge_id, {dump}, row[0], kind="invalidated", reason=reason)\n')
_HELPER = "    captured = edge.model_dump_json()\n    Edge.model_validate_json(captured)\n    return captured\n"
_INT_FIRST = "    if (isinstance(value, int) and not 0 <= value <= 1) or not math.isfinite(value)"
_EXIT_RAISE = "        if exc_type is None and state != \"emitted\":\n"
_NEW_IMPORT = "\nimport re\n"
_WIKI = '            if outcome in ("lapsed", "decayed") and self._edge_in_refusal(user_id, edge_id):\n'
_DUE = ("            if lifetime is None or (now - e.provenance.observed_at).days <= lifetime:\n"
        "                return None\n")

# (id, kind, file, [(anchor, replacement)], named cells, honest nodes, reason or None, what)
MUTANTS = [
    ("N4b-construction-check-removed", "product", CFG,
     [(_SET, "        if name in DECAY_BOUNDS and name in self.__dict__:\n            validate_decay_bound(name, value)\n")],
     [VALIDATED("1.5", "decay_factor"), VALIDATED("nan", "confidence_floor")], [OTHER], None,
     "the bounds validated on assignment only: construction accepts 2.0"),
    ("N4b-assign-check-removed", "product", CFG,
     [(_SET, "        if name in DECAY_BOUNDS and name not in self.__dict__:\n            validate_decay_bound(name, value)\n")],
     [ASSIGN("1.5", "decay_factor"), ASSIGN("nan", "confidence_floor")], [VALIDATED("1.5", "decay_factor")], None,
     "the bounds validated at construction only: `c.decay_factor = 2.0` is accepted"),
    ("N4b-assign-sets-before-validating", "product", CFG,
     [(_SET + "        object.__setattr__(self, name, value)\n",
       "        object.__setattr__(self, name, value)\n" + _SET)],
     [ASSIGN("1.5", "decay_factor")], [BOUNDARY("0.0", "decay_factor")], None,
     "the value set before it is validated: a refused assignment loses the old value"),
    ("N4b-prime-exclusive-bound", "product", CFG,
     [("not 0.0 <= value <= 1.0", "not 0.0 < value < 1.0")],
     [BOUNDARY("0.0", "decay_factor"), BOUNDARY("1", "confidence_floor")], [VALIDATED("1.5", "decay_factor")], None,
     "an exclusive bound: the endpoints 0 and 1 are refused"),
    ("N4b-nan-blind-comparison", "product", CFG,
     [("    if (isinstance(value, int) and not 0 <= value <= 1) or not math.isfinite(value) or not 0.0 <= value <= 1.0:",
       "    if (isinstance(value, int) and not 0 <= value <= 1) or value < 0.0 or value > 1.0:")],
     [VALIDATED("nan", "decay_factor"), VALIDATED("nan", "confidence_floor")], [VALIDATED("1.5", "decay_factor")],
     None, "a NaN-blind comparison: nan is accepted"),
    ("R3-03-float-first", "product", CFG,
     [(_INT_FIRST, "    if not math.isfinite(value) or (isinstance(value, int) and not 0 <= value <= 1)")],
     [VALIDATED("+10**400", "decay_factor"), VALIDATED("-10**400", "confidence_floor"),
      ASSIGN("+10**400", "confidence_floor"), REFUSAL("+10**400", "0.3")], [VALIDATED("1.5", "decay_factor")], None,
     "the float conversion first again: 10**400 raises OverflowError, not the ValueError naming the field (R3-03)"),
    ("N4b-bool-accepted", "product", CFG,
     [("if isinstance(value, bool) or not isinstance(value, (int, float)):", "if not isinstance(value, (int, float)):")],
     [VALIDATED("True", "decay_factor"), VALIDATED("False", "confidence_floor")], [VALIDATED("1.5", "decay_factor")],
     None, "no explicit refusal of a bool: True reads as 1"),
    ("N4g-entry-validation-removed", "product", LC,
     [(_V, "    decay_factor = config.decay_factor\n")],
     [FACTOR("2.0", "0.3"), FACTOR("2.0", "0.0")], [SHIPPED], None,
     "the factor not validated at entry, A and C intact: 0.3 × 2.0 → 0.6 is written (in range)"),
    ("N4d-floor-unvalidated-at-entry", "product", LC,
     [(_F, "    confidence_floor = config.confidence_floor\n")],
     [REFUSAL("0.5", "2.0"), REFUSAL("0.5", "-0.5")], [FACTOR("2.0", "0.3")], None,
     "the floor left unvalidated at entry"),
    ("N4d-validation-inside-the-decay-branch", "product", LC,
     [(_V, "    decay_factor = config.decay_factor\n"), (_F, "    confidence_floor = config.confidence_floor\n"),
      (_CALL, '        if behaviors[e.volatility].value == "decay":\n'
              '            validate_decay_bound("decay_factor", decay_factor)\n'
              '            validate_decay_bound("confidence_floor", confidence_floor)\n' + _CALL)],
     [REFUSAL("2.0", "0.3"), REFUSAL("0.5", "2.0")], [SHIPPED], None,
     "the validation moved back inside the DECAY branch: the TRANSIENT edge listed first is lapsed before the refusal"),
    ("N4i-retained-decay-counted", "product", LC,
     [('        elif outcome == "decayed":\n', '        elif outcome in ("decayed", "decay-retained"):\n')],
     [N4I("retained"), N4I("exactly at the floor")], [N4I("below the floor")], None,
     "a retained decay counted as `decayed` (R2-02)"),
    ("ruling-falls-back-without-the-transition", "product", LC,
     [("    if impl is None or getattr(impl, \"__func__\", None) is Store.expiry_transition:\n",
       "    if impl is None:\n")],
     [C("test_a_store_without_the_transition_refuses_at_entry")], [SHIPPED], None,
     "a store without `expiry_transition` is not refused at entry (the owner's ruling, \"Refuse, name it\")"),
    ("ruling-a-delegating-wrapper-refused", "product", LC,
     [('    impl = getattr(store, "expiry_transition", None)\n',
       '    impl = getattr(type(store), "expiry_transition", None)\n')],
     [C("test_a_delegating_wrapper_store_is_not_refused")], [SHIPPED], None,
     "the capability read on the CLASS alone: a delegating wrapper (its __getattr__ reaches the inner store's "
     "transition) is refused (found by 0021's fault matrix, 2026-11-02)"),
    ("ruling-the-wrappers-class-asked", "product", LC,
     [("    if impl is None or getattr(impl, \"__func__\", None) is Store.expiry_transition:\n",
       "    if impl is None or getattr(type(store), \"expiry_transition\", None) is Store.expiry_transition:\n")],
     [C("test_a_wrapper_around_a_store_without_the_transition_refuses_at_entry")], [SHIPPED], None,
     "the capability read asks the wrapper's class, not the resolved method: Wrapper(a non-overriding subclass) "
     "escapes the refusal at entry (research, 2026-11-02)"),
    ("N4-write-refusal-swallowed", "product", LC,
     [(_CALL, "        try:\n" + "\n".join("    " + ln for ln in _CALL.splitlines()) + "\n"
              "        except ValueError:\n            continue\n")],
     [C("test_an_unrelated_write_refusal_inside_the_transition_still_raises")], [SHIPPED], None,
     "a ValueError from the transition swallowed (the shipped `except ValueError` shape)"),
    ("N3-lifetimes-read-live", "product", LC,
     [("    lifetimes = dict(config.volatility_lifetime_days)", "    lifetimes = config.volatility_lifetime_days")],
     [C("test_the_lifetimes_are_copied_at_entry")], [SHIPPED], None,
     "the lifetimes dict read live: a host's mid-run edit changes the run"),
    ("N4h-decided-from-the-listing", "product", LC,
     [(_LOOP_HEAD, _SHIPPED_LOOP)],
     [N4H("confirm"), N4H("lapse"), N4H("decay")], [SHIPPED], None,
     "THE SUPERSEDED IMPLEMENTATION: the shipped expire() body, deciding from its listing and writing the copy back"),
    ("F2-the-store-modules-table", "product", SQ,
     [("            behavior = behaviors[e.volatility]\n",
       "            from ..schema import DEFAULT_EXPIRY as _T\n            behavior = _T[e.volatility]\n")],
     [C("test_a_host_that_rebinds_lifecycles_table_is_honoured")], [N4I("retained")], None,
     "the transition reads the store module's import of the table, not expire()'s copy (research's F2)"),
    ("N4f-helper-does-not-validate", "product", SQ,
     [(_HELPER, "    return edge.model_dump_json()\n")],
     [OUT_OF_BOUND], [SHIPPED], None, "the store helper serialises without validating"),
    ("N4f-helper-trusts-the-instance", "product", SQ,
     [("    Edge.model_validate_json(captured)\n", "    Edge.model_validate(edge)\n")],
     [OUT_OF_BOUND], [SHIPPED], None, "the helper accepts an instance without revalidating its nested data"),
    ("N4f-a-writer-bypasses-the-helper", "product", SQ,
     [(_INV_WRITER, _INV_DIRECT.format(dump="edge.model_dump_json()"))],
     [GATE], [OUT_OF_BOUND], None, "the sole active=0 writer binds its own dump, not the helper's"),
    ("N4f-the-helpers-return-ignored", "product", SQ,
     [(_INV_WRITER, "        _validated_edge_json(edge)\n" + _INV_DIRECT.format(dump="edge.model_dump_json()"))],
     [GATE], [OUT_OF_BOUND], None, "a writer calls the helper and ignores its return value"),
    ("R3-01-two-observations", "product", SQ,
     [(_HELPER, "    Edge.model_validate(edge.model_dump())\n    return edge.model_dump_json()\n")],
     [C("test_the_store_binds_the_bytes_it_validated")], [OUT_OF_BOUND], None,
     "THE SUPERSEDED IMPLEMENTATION (round 3's body): one observation validated, another serialised (R3-01)"),
    ("R3-01-validate-the-capture-return-a-fresh-dump", "product", SQ,
     [(_HELPER, "    captured = edge.model_dump_json()\n    Edge.model_validate_json(captured)\n"
                "    return edge.model_dump_json()\n")],
     [C("test_the_store_binds_the_bytes_it_validated")], [OUT_OF_BOUND], None,
     "the capture validated, a second dump returned: the bytes bound are not the bytes checked"),
    ("N4f-deferred-journal-swallows-an-exception", "product", SQ,
     [("            raise RuntimeError(f\"the edge row {self._edge_id!r} was written and its journal never emitted — refusing, \"\n"
       "                               f\"so the write transaction rolls back (specs/0048 §4C; specs/0029 §4b)\")\n"
       "        return False\n",
       "            raise RuntimeError(f\"the edge row {self._edge_id!r} was written and its journal never emitted — refusing, \"\n"
       "                               f\"so the write transaction rolls back (specs/0048 §4C; specs/0029 §4b)\")\n"
       "        return True\n")],
     [C("test_a_deferred_journal_never_swallows_an_exception"), GATE], [OUT_OF_BOUND], None,
     "the deferred journal's __exit__ suppresses: a failed side-table write commits a row with no journal"),
    ("N4f-deferred-journal-unemitted-allowed", "product", SQ,
     [(_EXIT_RAISE, "        if False:\n")],
     [C("test_a_deferred_journal_left_unemitted_rolls_the_write_back"), GATE], [OUT_OF_BOUND], None,
     "leaving the deferred block without emit is allowed: a row commits with no journal"),
    ("N4h-conditional-on-confidence-and-activity", "product", SQ,
     [(_EDGES_RET, _STASH),
      (_READ, _READ + _STALE + "            if row is not None and _stale[0] is not None:\n"
              "                _c, _s = Edge.model_validate_json(row[0]), Edge.model_validate_json(_stale[0])\n"
              "                if (_c.provenance.confidence, row[1]) == (_s.provenance.confidence, _stale[1]):\n"
              "                    row = _stale\n")],
     [N4H("confirm95")], [N4I("retained")], None,
     "a write conditional on (confidence, activity) as read: confirm() on 0.95 changes neither, and is reverted"),
    ("N4h-conditional-on-the-read-model-re-serialised", "product", SQ,
     [(_EDGES_RET, _STASH),
      (_READ, _READ + _STALE + "            if row is None or _stale[0] is None or row[0] != "
              "Edge.model_validate_json(_stale[0]).model_dump_json():\n                return None\n")],
     [C("test_a_legacy_serialisation_is_processed_not_skipped")], [N4H("confirm")], None,
     "a predicate binding the read model re-serialised: a legacy row's bytes never match and it is skipped"),
    ("N4h-conditional-on-the-row-as-read", "product", SQ,
     [(_EDGES_RET, _STASH),
      (_READ, _READ + _STALE + "            if row is None or _stale[0] is None or row[0] != _stale[0]:\n"
              "                return None\n")],
     [N4H("decay")], [N4H("confirm")], None,
     "a write conditional on the row as read in place of the in-transaction read (H-01: a due transition dropped)"),
    ("N4i-below-the-floor-the-decayed-value-stored", "product", SQ,
     [(_DECAY_RETIRE, '                    e.provenance = Provenance.model_validate({**e.provenance.model_dump(), '
                      '"confidence": decayed})\n                    self._upsert_edge_row(e)\n'
                      '                    self._invalidate_edge_row(edge_id, now, "decayed")\n')],
     [N4I("below the floor"), N4I("factor 0, floor 0.3")], [N4I("retained")], None,
     "below the floor, the decayed confidence stored before the retirement (R2-02)"),
    ("N4i-floor-comparison-inclusive", "product", SQ,
     [("                if decayed < confidence_floor:\n", "                if decayed <= confidence_floor:\n")],
     [N4I("exactly at the floor")], [N4I("retained")], None, "the floor comparison inclusive: a decay at the floor retires"),
    ("D1-the-redaction-check-outside-the-transaction", "product", SQ,
     [('            if edge_id in self.redacted_targets(user_id, "edge"):\n                return None\n', "")],
     [C("test_a_redaction_after_the_listing_is_seen_inside_the_transition")], [SHIPPED], None,
     "the 0041 skip not inside the transaction: a redaction after the listing makes the write path refuse"),
    ("D-an-inactive-row-transitioned", "product", SQ,
     [("            if row is None or not row[1]:\n                return None\n            # specs/0041 round 10's skip",
       "            if row is None:\n                return None\n            # specs/0041 round 10's skip")],
     [C("test_a_change_between_listing_and_transition_is_decided_on_the_current_row[invalidated]")],
     [C("test_a_change_between_listing_and_transition_is_decided_on_the_current_row[made transient]")], None,
     "an INACTIVE current row is transitioned (an invalidation committed after the listing is flagged)"),
    ("D-the-bump-skipped", "product", SQ,
     [("            self._bump(user_id)\n            # invalidate_edge's 0003 §4c-ii drop",
       "            # invalidate_edge's 0003 §4c-ii drop")],
     [C("test_a_transitions_side_effects_equal_the_shipped_paths[flag]"),
      C("test_a_transitions_side_effects_equal_the_shipped_paths[decay retained]")],
     [C("test_a_transitions_side_effects_equal_the_shipped_paths[not due]")], None,
     "a transition that writes does not bump the user's store version (the shipped writers bump)"),
    ("D-a-bump-on-a-no-op", "product", SQ,
     [("            e = Edge.model_validate_json(row[0])\n            lifetime = lifetimes.get(e.volatility)\n",
       "            self._bump(user_id)\n            e = Edge.model_validate_json(row[0])\n            lifetime = lifetimes.get(e.volatility)\n")],
     [C("test_a_change_between_listing_and_transition_is_decided_on_the_current_row[made permanent]")],
     [C("test_a_transitions_side_effects_equal_the_shipped_paths[not due]")], None,
     "the store version bumped before the transition knows it writes: a transition that writes nothing moves it"),
    ("D-wiki-drop-on-lapse-only", "product", SQ,
     [(_WIKI, '            if outcome == "lapsed" and self._edge_in_refusal(user_id, edge_id):\n')],
     [REFUSAL_FX("decay below the floor", "prior"), REFUSAL_FX("decay below the floor", "incoming")],
     [REFUSAL_FX("lapse", "prior")], None,
     "a decay that retires an edge in a refusal keeps the wiki: 0003 §4c-ii's resolution event missed (research's "
     "stage-2 mark on 574f130)"),
    ("D-wiki-drop-removed", "product", SQ,
     [(_WIKI, "            if False and self._edge_in_refusal(user_id, edge_id):\n")],
     [REFUSAL_FX("lapse", "prior"), REFUSAL_FX("lapse", "incoming"), REFUSAL_FX("decay below the floor", "prior")],
     [REFUSAL_FX("not due", "prior")], None,
     "no retiring transition drops the wiki (research's stage-2 mark on 574f130)"),
    ("D-wiki-drop-outcome-blind", "product", SQ,
     [(_WIKI, "            if self._edge_in_refusal(user_id, edge_id):\n")],
     [REFUSAL_FX("flag", "prior"), REFUSAL_FX("decay retained", "incoming")], [REFUSAL_FX("lapse", "prior")], None,
     "the drop applied to every writing outcome: a flag or a retained decay of an edge in a refusal drops the wiki "
     "(the next mutant of the drop's guard)"),
    ("D-due-boundary-exclusive", "product", SQ,
     [(_DUE, _DUE.replace("<= lifetime", "< lifetime"))],
     [DUE_AT("exactly the lifetime")], [DUE_AT("one day past it")], None,
     "the transition's due-ness exclusive: an edge exactly `lifetime` days old on its current row is transitioned "
     "(equivalent through expire(), whose listing skips it; research's stage-2 survivor)"),
    ("N4c-iii-a-copy-site-not-declared", "product", G,
     [(_NEW_IMPORT, "\ndef _planted_raise(p):\n    return p.model_copy(update={\"confidence\": p.confidence * 2.0})\n"
                    + _NEW_IMPORT)],
     [DECLARED], [GATE], None, "a new copy site writing confidence, absent from the declared table"),
    ("N4c-iv-a-form-the-census-does-not-see", "product", G,
     [(_NEW_IMPORT, "\ndef _planted_vars(p):\n    vars(p)[\"confidence\"] = 2.0\n" + _NEW_IMPORT)],
     [TRIPWIRE], [GATE], None, "a writer of a form the census does not see, its trigger tokens unclassified"),
]


def _noop(rel, anchor, cells):
    return (f"NOOP-{pathlib.Path(rel).stem}", rel, [(anchor, "# no-op control: a comment, no behaviour\n" + anchor)],
            sorted(set(cells)), f"a comment edit in {rel}: its mutants' cells must all pass", "SURVIVED")


def _cells_of(rel):
    return [c for m in MUTANTS if m[2] == rel for c in m[4]]


# (id, file, [(anchor, replacement)], named cells, what, the outcome the classifier must give)
CONTROLS = [
    _noop(CFG, "def validate_decay_bound(", _cells_of(CFG)),
    _noop(LC, "def expire(", _cells_of(LC)),
    _noop(SQ, "def _validated_edge_json(", _cells_of(SQ)),
    _noop(G, "def subject_class(", _cells_of(G)),
    ("CTRL-unrelated-TypeError", LC,
     [(_V, '    raise TypeError("an unrelated execution failure (classifier negative control)")\n' + _V)],
     [SHIPPED], "an UNRELATED TypeError at expire()'s entry: every cell fails for no reason a row names",
     "UNCLASSIFIED"),
]

SUBJECT_P = _protocol.Subject(
    spec="0048", finding=SUBJECT, table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium.config", "veracium.lifecycle", "veracium.store.sqlite", "veracium.graph"),
    import_specs=(), cells_files=(T, EVT), kinds=("product",))

definition_sha = _protocol.definition_sha
canonical = _protocol.canonical
render = _protocol.render
_digests = SUBJECT_P.digests


def problems(path: pathlib.Path = TABLE, root: pathlib.Path = ROOT) -> list:
    return SUBJECT_P.problems(path, root)


def main() -> int:
    if "--check" in sys.argv or len(sys.argv) == 1:
        probs = problems()
        for b in probs:
            print(f"STALE: {b}")
        return 1 if probs else 0
    return SUBJECT_P.main(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
