"""specs/0031 §4b-ii — the proposal carrier's DDL, executed from the SPEC.

Round-2 F6 asked for runnable evidence rather than transcripts; this file is
it. The DDL is EXTRACTED FROM THE SPEC at test time — the spec's own fenced
`CREATE TABLE` blocks are what executes — so a spec edit that breaks the
contract fails here, and the committed evidence can never drift from the
normative text (the propagation discipline, applied to DDL).

Round-2's findings live here as permanent cells: the reviewer's six original
rows (R1-R6), the NULL-blind claim CHECK (C1 — SQL three-valued logic: NULL
never fails a naive CHECK), the non-hex digest (N1), the FK to a nonexistent
proposal (N3), and the resolver attribution (N4). RULE ZERO: the FK cells run
under `PRAGMA foreign_keys=ON` exactly as the store must open connections,
and the pragma-OFF negative control proves the FK is INERT without it — an
unenforced FK is a comment wearing a constraint's clothes.
"""
import re
import sqlite3
from pathlib import Path

import pytest

SPEC = Path(__file__).resolve().parents[1] / "specs" / "0031-agent-facing-trust-surface.md"


def _ddl():
    text = SPEC.read_text()
    blocks = re.findall(r"CREATE TABLE mcp_proposal.*?\n\);", text, re.S)
    assert len(blocks) == 2, (
        f"expected exactly the two pinned tables in the spec, found {len(blocks)}")
    return "\n".join(blocks)


@pytest.fixture()
def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")   # the pinned store obligation
    conn.executescript(_ddl())
    yield conn
    conn.close()


BASE = dict(user_id="u", id="p1", kind="correction", proposer="model",
            target_edge_id="e1", target_state_digest="a" * 64,
            correction_payload='{"new":"x"}', claim="error",
            evidence_ref="ev", note=None, created_at="T", expires_at="T2",
            state="open", resolved_at=None, applied_txn=None)
RBASE = dict(user_id="u", proposal_id="p1", seq=1, action="accept", at="T",
             resolver="host-admin", applied_txn=7, reversal_txn=None)


def _insert(conn, table, base, **over):
    row = {**base, **over}
    cols, ph = ",".join(row), ",".join("?" * len(row))
    conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({ph})",
                 list(row.values()))


PROPOSAL_CELLS = [
    # (cell, overrides, refused?)
    ("R1-kind-confirm", dict(kind="confirm"), True),
    ("R2-proposer-user", dict(proposer="user"), True),
    ("R3-unknown-kind", dict(kind="zzz"), True),
    ("R4-dispute-with-payload",
     dict(kind="dispute", correction_payload='{"x":1}', claim=None), True),
    ("R5-terminal-missing-resolution", dict(state="accepted"), True),
    ("R6-open-with-resolution", dict(resolved_at="T3", applied_txn=7), True),
    ("C1-correction-claim-NULL", dict(claim=None), True),
    ("C2-claim-outside-domain", dict(claim="oops"), True),
    ("C3-dispute-with-claim",
     dict(kind="dispute", correction_payload=None, claim="error"), True),
    ("C4-oversize-payload", dict(correction_payload="x" * 5000), True),
    ("N1-non-hex-digest", dict(target_state_digest="Z" * 64), True),
    ("N2-short-digest", dict(target_state_digest="ab"), True),
    ("P1-valid-correction", dict(), False),
    ("P2-valid-dispute",
     dict(kind="dispute", correction_payload=None, claim=None), False),
    ("P3-valid-accepted",
     dict(state="accepted", resolved_at="T3", applied_txn=7), False),
    ("P4-valid-refused", dict(state="refused", resolved_at="T3"), False),
]


@pytest.mark.parametrize("cell,over,refused",
                         PROPOSAL_CELLS, ids=[c[0] for c in PROPOSAL_CELLS])
def test_proposal_cell(db, cell, over, refused):
    if refused:
        with pytest.raises(sqlite3.IntegrityError):
            _insert(db, "mcp_proposal", BASE, **over)
    else:
        _insert(db, "mcp_proposal", BASE, **over)


RESOLUTION_CELLS = [
    ("N3-fk-nonexistent-proposal", dict(proposal_id="p-missing"), True),
    ("N4-resolver-empty", dict(resolver=""), True),
    ("accept-valid", dict(), False),
    ("accept-without-txn", dict(applied_txn=None), True),
    ("reverse-valid", dict(action="reverse", applied_txn=None, reversal_txn=9),
     False),
    ("refuse-valid", dict(action="refuse", applied_txn=None), False),
]


@pytest.mark.parametrize("cell,over,refused",
                         RESOLUTION_CELLS, ids=[c[0] for c in RESOLUTION_CELLS])
def test_resolution_cell(db, cell, over, refused):
    _insert(db, "mcp_proposal", BASE)          # the referenced proposal
    if refused:
        with pytest.raises(sqlite3.IntegrityError):
            _insert(db, "mcp_proposal_resolution", RBASE, **over)
    else:
        _insert(db, "mcp_proposal_resolution", RBASE, **over)


def test_fk_is_inert_without_the_pragma__control():
    """V-FK-ENFORCED's negative control: the SAME DDL on a connection opened
    WITHOUT the pragma ACCEPTS a resolution for a nonexistent proposal — so
    the pragma is load-bearing, and a store that forgets it ships the
    round-1 comments-not-constraints defect in a new costume."""
    conn = sqlite3.connect(":memory:")       # no PRAGMA — the wrong opening
    conn.executescript(_ddl())
    _insert(conn, "mcp_proposal_resolution", RBASE, proposal_id="p-missing")
    conn.close()  # accepted: the control proves the pragma discriminates


def test_null_claim_would_pass_a_naive_check__control():
    """C1's mechanism, kept executable: NULL IN (...) is NULL, and a CHECK
    refuses only FALSE — proven on a minimal naive table so the spec's
    IS-NOT-NULL clause is demonstrably load-bearing."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""CREATE TABLE naive (
        kind TEXT NOT NULL,
        claim TEXT CHECK ((kind = 'dispute' AND claim IS NULL) OR
                          (kind = 'correction' AND claim IN ('error','change'))))""")
    conn.execute("INSERT INTO naive VALUES ('correction', NULL)")  # accepted!
    conn.close()
