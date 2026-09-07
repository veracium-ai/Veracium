"""specs/0028 §5 — the two-connection read-window cases as EXECUTABLE tests
(round-3 supplemental verdict, 2026-09-07: "the script records observations but
asserts none of them. Convert the cases into executable tests with timing-
tolerant assertions before using them as closure evidence").

The claim under test is §5's rule, written from the run and confirmed by the
reviewer's independent reproduction: under the store's DEFAULT journal mode
(rollback / `delete` — the store sets no journal_mode) a concurrent writer
cannot commit while a read window is open; it waits up to its `busy_timeout`,
commits after the window closes if the window closes first, otherwise raises
SQLite's `database is locked` from the commit and the write is LOST. Under WAL
the writer commits during the window and the reader keeps its snapshot. The
reader is never the one refused (the mirror). And the reader sees ONE snapshot
in every case.

Timing-tolerant by construction: no assertion compares a duration to a
constant. Each case records the window's open/close instants and the writer's
finish instant and asserts ORDER (finished before / after the window closed),
plus the outcome (committed / raised) and the store's final row count, which
are the facts the rule states. Windows and timeouts are reduced from the
transcript's 1s/7s/5000ms to keep the file under ten seconds; the rule is about
their relation, not their size.

The reader holds the SHIPPED window shape — `SqliteStore.current_state`'s
explicit BEGIN under the instance lock, reads inside, COMMIT — on its own
store's connection; the writer writes through its own `add_edge`
(`_write_txn`), so the recorded outcome is what a library caller sees.
"""
from __future__ import annotations

import sqlite3
import threading
import time

import pytest

from veracium.schema import Edge, EvidenceAuthor, Provenance
from veracium.store.sqlite import SqliteStore

U = "u-window"


def _edge(i):
    return Edge(id=f"e-{i}", user_id=U, subject="user", relation="uses_tool", object=f"tool-{i}",
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"w:{i}"))


def _stores(tmp_path, mode, *, writer_timeout_ms):
    path = str(tmp_path / "s.db")
    if mode == "wal":
        c = sqlite3.connect(path); c.execute("PRAGMA journal_mode=WAL"); c.close()
    reader = SqliteStore(path)
    writer = SqliteStore(path, busy_timeout_ms=writer_timeout_ms)
    assert reader._conn.execute("PRAGMA journal_mode").fetchone()[0] == mode
    return reader, writer


def _hold_window(store, seconds, out):
    """current_state's window shape, held open for `seconds`."""
    conn = store._conn
    with store._lock:
        assert not conn.in_transaction
        conn.execute("BEGIN")
        out["opened"] = time.perf_counter()
        out["count_at_open"] = conn.execute("SELECT count(*) FROM edges WHERE user_id=?", (U,)).fetchone()[0]
        time.sleep(seconds)
        out["count_before_commit"] = conn.execute("SELECT count(*) FROM edges WHERE user_id=?", (U,)).fetchone()[0]
        conn.execute("COMMIT")
        out["closed"] = time.perf_counter()


def _write_during_window(reader, writer, window_s, *, settle=0.2):
    res = {}
    th = threading.Thread(target=_hold_window, args=(reader, window_s, res))
    th.start()
    time.sleep(settle)                      # the window is open before the write starts
    started = time.perf_counter()
    err = None
    try:
        writer.add_edge(_edge("during"))
    except Exception as e:                  # noqa: BLE001 — the exception IS the observation
        err = e
    finished = time.perf_counter()
    th.join()
    assert started > res["opened"], "the write must start inside the window"
    return res, started, finished, err


def _count(writer):
    return len(writer.edges(U, active_only=False, include_quarantined=True))


# ---------------------------------------------------------------- the rule
def test_default_mode_writer_waits_and_commits_after_a_window_shorter_than_its_timeout(tmp_path):
    """DELETE journal, window < busy_timeout: the writer WAITS and commits
    AFTER the window closes; the store holds both rows; the reader saw one
    snapshot (both its counts equal)."""
    reader, writer = _stores(tmp_path, "delete", writer_timeout_ms=3000)
    writer.add_edge(_edge("seed"))
    res, started, finished, err = _write_during_window(reader, writer, window_s=0.8)
    assert err is None, err
    assert finished >= res["closed"], "the commit landed only after the window closed"
    assert res["count_at_open"] == res["count_before_commit"] == 1
    assert _count(writer) == 2
    reader.close(); writer.close()


def test_default_mode_writer_fails_and_loses_the_write_when_the_window_outlasts_its_timeout(tmp_path):
    """DELETE journal, window > busy_timeout: the writer's COMMIT fails after
    its busy_timeout, BEFORE the window closes; the write is LOST; the reader
    saw one snapshot. Since 0029 v10 (V-LOCK-REFUSAL-FORM) the refusal is the
    store's wrapped form naming the COMMIT site, with SQLite's bare
    `database is locked` kept as the cause — the 0028 §5 parenthetical that
    called the bare form a recorded product defect now reads as history."""
    reader, writer = _stores(tmp_path, "delete", writer_timeout_ms=500)
    writer.add_edge(_edge("seed"))
    res, started, finished, err = _write_during_window(reader, writer, window_s=2.0)
    assert isinstance(err, sqlite3.OperationalError), err
    assert "COMMIT" in str(err) and "V-LOCK-REFUSAL-FORM" in str(err), str(err)
    assert isinstance(err.__cause__, sqlite3.OperationalError) and "database is locked" in str(err.__cause__)
    assert finished < res["closed"], "the failure came while the window was still open"
    assert res["count_at_open"] == res["count_before_commit"] == 1
    assert _count(writer) == 1, "the write is lost — rolled back, not deferred"
    # the writer's connection is left CLEAN: the next write lands
    assert not writer._conn.in_transaction
    writer.add_edge(_edge("after"))
    assert _count(writer) == 2
    reader.close(); writer.close()


@pytest.mark.parametrize("window_s", [0.8, 2.0], ids=["short", "long"])
def test_wal_writer_commits_during_the_window_and_the_reader_keeps_its_snapshot(tmp_path, window_s):
    """WAL, either window length: the writer commits BEFORE the window closes;
    the reader's second read inside the window still shows the pre-write count
    (its snapshot held); the store holds both rows afterwards."""
    reader, writer = _stores(tmp_path, "wal", writer_timeout_ms=500)
    writer.add_edge(_edge("seed"))
    res, started, finished, err = _write_during_window(reader, writer, window_s=window_s)
    assert err is None, err
    assert finished < res["closed"], "the commit landed while the window was open"
    assert res["count_at_open"] == res["count_before_commit"] == 1, "the reader's snapshot held"
    assert _count(writer) == 2
    reader.close(); writer.close()


# --------------------------------------------------------------- the mirror
@pytest.mark.parametrize("mode", ["delete", "wal"])
def test_mirror_a_reserved_writer_never_refuses_the_reader_and_its_update_persists(tmp_path, mode):
    """The writer holds BEGIN IMMEDIATE with an uncommitted UPDATE; the reader
    opens its window and reads at once (RESERVED does not block SHARED) and
    sees the PRIOR state; the writer's COMMIT waits for the window (delete) or
    proceeds (wal). Persistence is checked on the SQL COLUMN the UPDATE wrote
    — the supplemental verdict's point: `edges()` rebuilds from the json
    payload, so the public read could not show this update."""
    reader, writer = _stores(tmp_path, mode, writer_timeout_ms=3000)
    writer.add_edge(_edge("seed"))
    wc = writer._conn
    wc.execute("BEGIN IMMEDIATE")
    wc.execute("UPDATE edges SET object='tool-uncommitted' WHERE id=?", ("e-seed",))
    res = {}
    th = threading.Thread(target=_hold_window, args=(reader, 0.8, res))
    th.start()
    time.sleep(0.2)
    assert "opened" in res, "the reader's window opened while the writer held RESERVED"
    wc.execute("COMMIT")
    c1 = time.perf_counter()
    th.join()
    if mode == "delete":
        assert c1 >= res["closed"], "delete: the commit waited for the window"
    else:
        assert c1 < res["closed"], "wal: the commit landed during the window"
    assert res["count_at_open"] == res["count_before_commit"] == 1
    # persistence, on the column the UPDATE wrote, from a THIRD connection
    third = sqlite3.connect(str(tmp_path / "s.db"))
    assert third.execute("SELECT object FROM edges WHERE id=?", ("e-seed",)).fetchone()[0] == "tool-uncommitted"
    third.close()
    reader.close(); writer.close()
