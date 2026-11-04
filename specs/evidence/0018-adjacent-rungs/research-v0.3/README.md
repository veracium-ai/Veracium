# 0018 adjacent-rungs v0.3: research's two probes for the contract-tables draft

Research, 2026-11-03. **Subject:** veracium at the design package's pin, dev `67bbba69`. The probes read a `git archive`
export only, and dev's tree is never touched. They were run with CPython 3.14.7 (a venv with pydantic and no veracium of
its own; `run.sh` refuses one that has it).

- **`probe_constructors.py`** gives the premise for the draft's E1: binding 0013 §5f.1's (b1) to the operation's target.
  Output `probe-constructors-67bbba6.out`:
  - 338 table and index constructors across v1–v16;
  - 0 outside (b1)'s asserted shape (`IF NOT EXISTS`, `AS SELECT`, or a non-plain `CREATE`);
  - 23 `(version, kind, name)` entries whose constructor differs from head's.

  **Control, run in-process and not shipped as a file:** with `IF NOT EXISTS` planted in v4's
  `supersession_operations`, the probe reports exactly that one.
- **`check_a2_facts.py`** runs the draft's A2 rows (14, including 7a/7b/8a/8b/11a) through the pin's `TerminalFacts.problems()`
  at rungs 1→2, 13→14, 14→15 and 15→16. Output `check-a2-facts-67bbba6.out`:
  - 56 of 56 have no problems;
  - the C1 binding example fails at the wrong rung;
  - five controls refuse;
  - the pin's `MigrationResult` refuses a lawful `(migrated, v14)` carrier with "a committed change is at version 16"
    (the verdict's R1-03).

**What these do not establish.** Both read definitions and validators. Neither opens a store, runs a rung, or exercises
the proposed contract. That is dev's model (the draft's section D).

`run.sh <python>` regenerates both outputs. A second run from a fresh export gave byte-identical files.
