"""0018 adjacent-rungs v0.3 tables draft, A2: every row's terminal facts, run through the
pin's TerminalFacts.problems() at three rungs; plus the C1 binding examples and controls."""
from veracium.store.release_migration import TerminalFacts, MigrationResult

ROWS = [
    ("1 migrated", "migrated", True, True, "destination", "t"),
    ("2 migrated (unstamped)", "migrated", True, True, "destination", "t"),
    ("3 stamped-shape-mismatch", "stamped-shape-mismatch", False, False, "unaccepted", None),
    ("4 current at t", "current", False, False, "destination", "t"),
    ("5 current at t, repaired", "current", True, True, "destination", "t"),
    ("6 stamped-shape-mismatch", "stamped-shape-mismatch", False, False, "unaccepted", None),
    ("7a migration-source-missing", "migration-source-missing", False, False, "unaccepted", None),
    ("7b newer", "newer", False, False, "unaccepted", None),
    ("8a migration-source-missing", "migration-source-missing", False, False, "unaccepted", None),
    ("8b adoption-refused", "adoption-refused", False, False, "unknown", None),
    ("9 foreign-shape", "foreign-shape", False, False, "unaccepted", None),
    ("10 migration-source-missing", "migration-source-missing", False, False, "unaccepted", None),
    ("11a migration-source-missing (nothing at the path)", "migration-source-missing", False, False, "missing", None),
    ("12 unsupported-migration", "unsupported-migration", False, False, "unknown", None),
]
bad = 0
RUNGS = (1, 13, 14, 15)
for b in RUNGS:
    t = b + 1
    for label, out, ch, co, st, v in ROWS:
        p = TerminalFacts(out, b, t, ch, co, st, t if v == "t" else v).problems()
        if p:
            bad += 1
            print(f"FAIL b={b} row {label}: {p}")
print(f"A2 rows x rungs {RUNGS}: {len(ROWS) * len(RUNGS)} checked, {bad} with problems")
# C1 binding: a lawful (13,14,migrated) record validates at 13->14, fails at 14->15
ok = TerminalFacts("migrated", 13, 14, True, True, "destination", 14).problems()
wrong = TerminalFacts("migrated", 14, 15, True, True, "destination", 14).problems()
print(f"C1 (13,14) at 13->14: {ok or 'no problems'}")
print(f"C1 (13,14) at 14->15: {wrong or 'no problems'}")
# controls: problems() must be able to refuse
ctl = [TerminalFacts("current", 13, 14, False, False, "destination", 16).problems(),
       TerminalFacts("migration-source-missing", 13, 14, False, False, "destination", 14).problems(),
       TerminalFacts("migrated", 13, 15, True, True, "destination", 15).problems(),
       TerminalFacts("adoption-refused", 13, 14, False, False, "unaccepted", None).problems(),
       TerminalFacts("migration-source-missing", 13, 14, False, False, "missing", 14).problems()]
print("controls refused:", [bool(c) for c in ctl])
# the pin's MigrationResult refuses the lawful (13,14) projection (R1-03)
try:
    MigrationResult("migrated", True, True, "destination", 14, "x")
    print("pin MigrationResult (migrated, v14): accepted")
except ValueError as e:
    print(f"pin MigrationResult (migrated, v14): refused: {e}")
