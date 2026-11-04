# 0018 amendment `0018-adjacent-rungs`: the probe re-run at the design package's pin
Research, 2026-11-03. **The pin** is veracium `67bbba69a8e463267f5533a161c3c6bd7c2991f3` (`origin/main`, as dev
named it for the package). **The subject** is the amendment `0018-adjacent-rungs`: the version the package ships, whose digest the package's
`PIN.txt` names (this README names no version's digest, so it cannot go stale when the text is re-versioned). It rides
outside the package's `tree/`, normative only on acceptance.

*Annotation, 2026-11-03.* This run was made at research `d459a6b2`, when the candidate was v0.2. v0.2.1 re-anchors
v0.2's citations at this pin after the 0.30.0 interim (dev `9e6c134`), and cites this run. No §2c-ii row's result
changes between the two: rows 2, 3 and 5 are identical, and rows 1 and 4 change only where the result was established
(this output, and "at the pin"). v0.2.2 adds the amendment's Number row and changes nothing else. The probe, its output and `run.sh` are the bytes committed at `d459a6b2`.

**The run** (`run.sh`; output `probe-rungs-67bbba6.out`):
- `probe_rungs.py` is the 2026-11-02 file unchanged (`../evidence-0018-adjacent-rungs-2026-11-02/`): both copies are
  sha256 `2f24580ff408cebe636ee1c7fb10e975d4bc31bb4371857e595ed6d9aba36d47`. `SHA256SUMS` covers this dir's files only, so
  it checks wherever the dir is shipped.
- A `git archive` of the pin, with `PYTHONPATH=src`. CPython 3.14.7 with no veracium of its own (`run.sh` refuses
  otherwise, and asserts the import comes from the export). nice 19, the stores on `/dev/shm`.
- **Result: 120 of 120 rungs ok, 15 of 15 direct jumps ok, and the four controls as expected**:
  - a v15 store judged as v16: False;
  - a walked v16 store: True;
  - the same store with a foreign table: False;
  - the same store with a column added to `edges`: False.
- The output is byte-identical to the run at `3bef432` (`diff`, no output). Between the two pins,
  `src/veracium/store/migration.py` is unchanged and `schema_version.py` changed in 14 lines (`git diff --stat`).

**Scope, as v0.2.1 §2c-ii states it (unchanged from v0.2):**
- the stores are EMPTY, so the data steps ran over zero rows;
- the in-process head patch stands in for the target parameter the draft specifies;
- I33 owes populated fixtures from each release's own code, through the implemented kernel.
