"""specs/0028 §5 — the two-connection read-window TRANSCRIPT RECORDER (round-4
evidence; the reviewer reproduced its four cases independently, 2026-09-07).

    python3 specs/evidence/0028/window_transcript.py [--out LOG]

Records — asserts nothing. The ASSERTIONS live in
`tests/test_0028_window_transcript.py` (timing-tolerant ORDER assertions per
the supplemental verdict's ask); this file exists so a package can regenerate
the human-readable log at its pin with the exact interpreter and SQLite named.

What it does: two `SqliteStore` instances on one file; the WRITER writes
through its own `add_edge` (`_write_txn`: BEGIN IMMEDIATE … COMMIT, the
default 5000ms `busy_timeout`) so the recorded outcome is what a library
caller sees; the READER holds `SqliteStore.current_state`'s window shape —
an explicit BEGIN under the instance lock, a count read, a hold, a second
count read, COMMIT — for 1s and for 7s, in rollback-journal (the store's
default: it sets no journal_mode) and in WAL. Then the MIRROR: the writer
holds BEGIN IMMEDIATE with an uncommitted UPDATE while the reader opens its
window; the writer commits with the window open.

Supplemental-verdict fix (mirror): the UPDATE writes the relational `object`
column while `SqliteStore.edges()` rebuilds edges from the json payload, so
the earlier recorder's "after: seed object = …" line could not show the
update. Persistence is now read from the SQL COLUMN the UPDATE wrote, from a
THIRD connection, and the line says which representation it read.
"""
from __future__ import annotations

import argparse
import pathlib
import sqlite3
import sys
import tempfile
import threading
import time

from veracium.schema import Edge, EvidenceAuthor, Provenance
from veracium.store.sqlite import SqliteStore

U = "u-transcript"
OUT = []


def log(s):
    line = f"{time.strftime('%H:%M:%S')} {s}"
    OUT.append(line)
    print(line, flush=True)


def edge(i):
    return Edge(id=f"e-{i}", user_id=U, subject="user", relation="uses_tool", object=f"tool-{i}",
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"transcript:{i}"))


def hold_window(store, D, result):
    """The shipped window shape (sqlite.py current_state), held for D seconds."""
    conn = store._conn
    with store._lock:
        opened = not conn.in_transaction
        if opened:
            conn.execute("BEGIN")
        result["opened_at"] = time.perf_counter()
        result["count_at_open"] = conn.execute("SELECT count(*) FROM edges WHERE user_id=?", (U,)).fetchone()[0]
        time.sleep(D)
        result["count_before_commit"] = conn.execute("SELECT count(*) FROM edges WHERE user_id=?", (U,)).fetchone()[0]
        conn.execute("COMMIT")
        result["closed_at"] = time.perf_counter()


def _open(mode, workdir, tag):
    d = tempfile.mkdtemp(prefix=f"asof-{tag}-{mode}-", dir=str(workdir))
    path = str(pathlib.Path(d) / "s.db")
    if mode == "WAL":
        c = sqlite3.connect(path); c.execute("PRAGMA journal_mode=WAL"); c.close()
    reader = SqliteStore(path); writer = SqliteStore(path)
    return path, reader, writer


def run_case(mode, D, seq, workdir):
    path, reader, writer = _open(mode, workdir, "case")
    jm = reader._conn.execute("PRAGMA journal_mode").fetchone()[0]
    bt = writer._conn.execute("PRAGMA busy_timeout").fetchone()[0]
    writer.add_edge(edge(f"{seq}-seed"))
    log(f"--- CASE mode={jm} window={D}s writer busy_timeout={bt}ms ---")
    res = {}
    th = threading.Thread(target=hold_window, args=(reader, D, res)); th.start()
    time.sleep(0.3)
    t0 = time.perf_counter()
    try:
        writer.add_edge(edge(f"{seq}-during")); outcome, err = "COMMITTED", ""
    except Exception as e:  # noqa: BLE001 — the exception IS the observation
        outcome, err = f"RAISED {type(e).__name__}", str(e).replace("\n", " ")
    t1 = time.perf_counter()
    th.join()
    log(f"writer: add_edge during the window -> {outcome} after {t1 - t0:.2f}s {('| ' + err) if err else ''}")
    log(f"reader: count at open={res['count_at_open']} count before COMMIT={res['count_before_commit']} "
        f"(window held {res['closed_at'] - res['opened_at']:.2f}s; writer finished "
        f"{'BEFORE' if t1 < res['closed_at'] else 'AFTER'} the window closed)")
    final = writer.edges(U, active_only=False, include_quarantined=True)
    log(f"after: {len(final)} edge(s) in the store: {sorted(e.id for e in final)}")
    log(f"writer connection after the case: in_transaction={writer._conn.in_transaction}")
    reader.close(); writer.close()


def run_mirror(mode, seq, workdir):
    path, reader, writer = _open(mode, workdir, "mirror")
    jm = reader._conn.execute("PRAGMA journal_mode").fetchone()[0]
    writer.add_edge(edge(f"{seq}-seed"))
    log(f"--- MIRROR mode={jm}: writer holds BEGIN IMMEDIATE with an uncommitted UPDATE; reader opens its window ---")
    wc = writer._conn
    wc.execute("BEGIN IMMEDIATE")
    wc.execute("UPDATE edges SET object='tool-uncommitted' WHERE id=?", (f"e-{seq}-seed",))
    res = {}
    t0 = time.perf_counter()
    th = threading.Thread(target=hold_window, args=(reader, 2.0, res)); th.start()
    time.sleep(0.5)
    tc0 = time.perf_counter()
    try:
        wc.execute("COMMIT"); c_out = "COMMITTED"
    except Exception as e:  # noqa: BLE001
        c_out = f"RAISED {type(e).__name__} | {e}"
        try:
            wc.execute("ROLLBACK")
        except Exception:  # noqa: BLE001
            pass
    tc1 = time.perf_counter()
    th.join()
    log(f"reader: window opened {res['opened_at'] - t0:.2f}s after the writer's BEGIN IMMEDIATE; "
        f"count at open={res['count_at_open']} before COMMIT={res['count_before_commit']}")
    log(f"writer: COMMIT issued with the reader's window open -> {c_out} after {tc1 - tc0:.2f}s "
        f"({'BEFORE' if tc1 < res['closed_at'] else 'AFTER'} the window closed)")
    third = sqlite3.connect(path)
    col = third.execute("SELECT object FROM edges WHERE id=?", (f"e-{seq}-seed",)).fetchone()[0]
    third.close()
    log(f"after (SQL column `object`, read by a THIRD connection — the representation the UPDATE wrote; "
        f"edges() rebuilds from the json payload and would not show it): {col!r}")
    reader.close(); writer.close()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="asof-window-transcript.log")
    a = ap.parse_args(argv)
    workdir = tempfile.mkdtemp(prefix="asof-window-transcript-")
    log(f"python {sys.version.split()[0]} sqlite {sqlite3.sqlite_version} (throwaway stores under {workdir})")
    seq = 0
    for mode in ("DELETE", "WAL"):
        for D in (1.0, 7.0):
            seq += 1; run_case(mode, D, seq, workdir)
    for mode in ("DELETE", "WAL"):
        seq += 1; run_mirror(mode, seq, workdir)
    pathlib.Path(a.out).write_text("\n".join(OUT) + "\n")
    log(f"transcript written: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
