# Joint test groups — the tests that must share ONE pytest process

The suite is designed to run as one process (`python -m pytest -q`). Where it is
split, the groups below stay whole: CI's five shards assign a group to one shard
(`.github/ci_shard.py`), and the offline launcher's default two phases run G1 in
its own single-process phase 2 (`two_phase.py files` refuses unless its list equals
G1's members below; `VERACIUM_OFFLINE_MODE=single` runs one process). A reviewer
who splits it across processes some other way — by
module, by directory, in parallel — can split a GROUP whose gate reads state
the OTHER members record in that same process. Split, such a gate does not
"fail on a defect"; it fails because the evidence it checks was produced in a
process it cannot see. The 0041 round-9 review hit exactly this (its four
module processes separated the seam model's two drivers; rejoined, both drivers
passed 286 of 286) and asked for the groups to be documented.

There are TWO groups. Each is listed with the mechanism that makes it joint,
what happens when it is split, and the command that runs it whole.

## G1 — the seam model's runtime execution gate (0029/0030)

| | |
|---|---|
| members | `tests/test_seam_model_0029_0030.py` AND `tests/test_seam_model_0029_0030_store.py`, in one process |
| the gate | `tests/test_seam_model_0029_0030_store.py::test_every_control_was_executed_and_asserted` |
| the mechanism | every `control_*` callable in the seam-model modules is an obligation captured at import (`_EXPECTED_CONTROLS`); `assert_control` records each one in the process-local registry `EXECUTED` (`specs/evidence/0029-0030/seam_model/binding_census.py`) at the moment its assertion passes; the gate, anchored LAST by `tests/conftest.py`'s `pytest_collection_modifyitems`, requires every obligation executed in THIS process. Both drivers invoke controls, and they are the registry's only two importers |
| split | the store driver alone: the gate FAILS, naming the controls only the other driver executes (by design — "an unexecuted control is unexecuted, and the gate refuses to guess why") |
| run whole | `python -m pytest -q tests/test_seam_model_0029_0030.py tests/test_seam_model_0029_0030_store.py` |

## G2 — the 0042 runtime leg's collection guard

| | |
|---|---|
| members | `tests/test_0042_sites.py`, collected WHOLE (no `-k`, `-m`, `--deselect`, `--lf`, `--sw`, and no node id on the command line) |
| the guard | `tests/test_0042_sites.py::test_the_collected_parametrisations_cover_every_declared_id` |
| the mechanism | the guard reads `request.session.items` — what pytest collected in THIS process — and requires the `site_id`s of the two parametrised tests to equal the declared census sites (a collection that fell short, 143 of 157, is visible only from this side). It knows whether the module was collected whole from `tests/conftest.py`'s `pytest_deselected` recorder, initialised in `pytest_configure` |
| narrowed | the guard SKIPS with the reason named ("selection narrowed …"): a skip, not pass credit. Run WITHOUT `tests/conftest.py` (another rootdir, the hook renamed) it FAILS by name — "the pytest_deselected recorder … did not run" — rather than enforce over a collection it cannot see. A per-MODULE split keeps this group whole: the module is its own group |
| run whole | `python -m pytest -q tests/test_0042_sites.py` |

## How the list was made, and its limit

By MECHANISM, not by sampling failures, in two sweeps over `tests/*.py`:

1. **Session or collection state.** A text search for `session.items`, `request.session`,
   `pytest_collection_modifyitems`, `pytest_deselected` and `config.getoption` found twelve
   files. Two are the groups above (and `tests/conftest.py`, which serves them). The other
   nine matched because they test a narrowed DOMAIN (an enum, a scope, a DDL claim), not
   because they depend on their collection.
2. **A registry another test file writes.** An AST sweep listed every non-product module
   imported by two or more test files (fifteen). In each, it looked for a module-level
   dict, list or set that the module's own functions mutate. There were two:
   `binding_census.EXECUTED` (G1), and `migrations_0013._DRAFT`, a context manager's
   re-entrancy state restored on exit, which carries nothing between tests. The
   `tests.eval` / `tests.robustness` imports are fixtures.

The limit, stated rather than absorbed: a search finds the mechanisms it names.
A test that reads a FILE another test writes would be a third kind; the suite's
one known instance (an evidence transcript, 2026-08-19) was removed and the
tests that read artifacts read committed ones. The executed check below runs the
two named groups; it does not prove there is no third.

## Verified by execution (2026-10-02, at 9e9e035, CPython 3.14.7, pytest-randomly shuffling)

| run | result |
|---|---|
| G1 joined: both drivers in one process | 286 passed (the round-9 reviewer's corrected figure) |
| G1 split: the store driver alone | 1 failed, 113 passed: the gate, naming 17 controls "NEVER EXECUTED-AND-ASSERTED this session" |
| G1 split: the other driver alone | 172 passed. The gate lives in the store driver, so this half has nothing to fail; it is not evidence for the controls the other half asserts |
| G2 whole | 179 passed, the guard enforcing |
| G2 narrowed (`-k` deselecting one parametrised test) | 12 passed, 1 skipped, 166 deselected; the skip is the guard's, "selection narrowed … 166 of its nodes deselected" |
