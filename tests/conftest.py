"""Suite-wide test configuration.

VERACIUM_FORBID_NETWORK=1 arms a socket kill-switch: any attempt to create an
AF_INET/AF_INET6 socket raises with a stack trace identifying the caller. The suite is
designed to pass fully offline (network-capable modules — telemetry, diagnostics — are
exercised through injected poster stubs).

The guard installs AT CONFTEST IMPORT TIME (round-8 external R8-5 corrected the earlier
session-fixture placement, which armed only after plugin startup and collection): conftest
import precedes test-module imports and every test, so those are covered; pytest's own
startup and third-party plugin initialization run BEFORE conftest import and are outside
the guard's window — the proof claim is scoped accordingly. For coverage of the pytest
startup itself, run under an OS-level egress denial; the suite passes there too.
"""
import os
import socket

if os.environ.get("VERACIUM_FORBID_NETWORK") == "1":
    _real_socket = socket.socket

    class _ForbiddenSocket(socket.socket):
        def __init__(self, family=socket.AF_INET, type=socket.SOCK_STREAM, *a, **kw):
            # AF_UNIX/AF_UNSPEC stay permitted: local IPC is not network egress.
            if family in (socket.AF_INET, socket.AF_INET6):
                raise RuntimeError(
                    "VERACIUM_FORBID_NETWORK=1: a network socket was requested — the "
                    "suite must pass fully offline; the stack trace above this error "
                    "names the caller")
            super().__init__(family, type, *a, **kw)

    socket.socket = _ForbiddenSocket


import tempfile

import pytest


@pytest.fixture(scope="session", autouse=True)
def _suite_tempdir(tmp_path_factory):
    """Every temporary name the suite mints lands under pytest's own basetemp, which pytest prunes (it keeps the last
    three runs), never in the system temp directory, which nothing prunes. Measured 2026-10-14 with the suite run under
    a private TMPDIR: one full run left 694 entries (97 MB) outside pytest's directory — test stores, exports, package
    copies, mutant files from bare `mkdtemp`/`mkstemp` calls in some sixty sites — about 12,000 a day across the
    seats' runs. b6fa646 (2026-09-16) redirected seven files one by one and recorded the rest as remaining; this is the
    whole-suite form. Both carriers are set: `tempfile.tempdir` for this process, and `TMPDIR` for the evidence scripts
    and child interpreters the tests launch (a child resolves its own temp directory from the environment). The
    per-file redirects (`tempfile.tempdir = tmp_path`, restored to the previous value) still nest inside this one.
    Each xdist worker gets its own directory under its own basetemp."""
    d = tmp_path_factory.mktemp("systemp", numbered=False)
    prev_dir, prev_env = tempfile.tempdir, os.environ.get("TMPDIR")
    tempfile.tempdir = str(d)
    os.environ["TMPDIR"] = str(d)
    try:
        yield d
    finally:
        tempfile.tempdir = prev_dir
        if prev_env is None:
            os.environ.pop("TMPDIR", None)
        else:
            os.environ["TMPDIR"] = prev_env


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    """Anchor the seam model's RUNTIME execution gate LAST — after
    pytest-randomly's shuffle (trylast runs after its hook), so every
    control-invoking test has executed before the gate compares the
    discovered control set against the runtime registry (0029/0030
    external round 14: AST call identity credits dead branches; the
    execution claim rides runtime evidence recorded by assert_control)."""
    gate = [i for i in items
            if i.name == "test_every_control_was_executed_and_asserted"]
    for g in gate:
        items.remove(g)
        items.append(g)


def pytest_deselected(items):
    """0042 round 6 (2026-09-20): the runtime leg's collection guard (tests/test_0042_sites.py) must know whether
    ITS module was collected whole. It observes the EFFECT — which nodes were deselected — rather than enumerating
    the causes: -k, -m, --deselect, --lf and --sw all deselect through this hook, and so will a plugin nobody has
    named yet. (A hand list of five flags missed --sw, which deselects a random prefix under pytest-randomly and
    made the guard accuse a correct tree; found by research running the skip branch under every mechanism.)"""
    if items:
        cfg = items[0].config
        cfg.veracium_deselected = cfg.veracium_deselected | frozenset(i.nodeid for i in items)


def pytest_configure(config):
    """The recorder's PRESENCE is a fact the guard can read: an empty set means 'the recorder ran and nothing
    was deselected'; an ABSENT attribute means the recorder is not installed (this conftest not loaded, the
    hook renamed), and the guard refuses by name rather than enforcing over a domain it cannot see."""
    config.veracium_deselected = frozenset()
    hold_basetemp(config)


def hold_basetemp(config):
    """R-I/R-II round 2, V1 (c): pytest REMOVES an explicit `--basetemp` when a session first uses it
    (`_pytest/tmpdir.py`, `getbasetemp`: `rm_rf(basetemp)`), so a second session given the same path deletes a running
    session's stores under it, and SQLite's next write to one of them reads "attempt to write a readonly database"
    (SQLITE_READONLY_DBMOVED; research's stage-1 read). The reviewer's run used one such path for an interrupted suite
    and the full suite after it. The controller takes an exclusive, non-blocking lock on a sibling file, OUTSIDE the
    directory pytest removes, before anything touches it, and holds it for the process's life; a second session given
    a held path refuses by name, never silently picks another (the operator chose the path). xdist workers run under
    their controller's lock. Without `fcntl` (Windows) nothing is held, and nothing is claimed. Returns the lock path,
    or None when no explicit basetemp was given."""
    basetemp = getattr(config.option, "basetemp", None)
    if not basetemp or hasattr(config, "workerinput"):
        return None
    try:
        import fcntl
    except ImportError:
        return None
    import pathlib
    target = pathlib.Path(basetemp).resolve()
    lock = target.parent / f".{target.name}.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        holder = os.pread(fd, 32, 0).decode("ascii", "replace").strip() or "unknown"
        os.close(fd)
        raise pytest.UsageError(
            f"--basetemp {target} is held by a live pytest session (pid {holder}): pytest removes an explicit "
            f"--basetemp when a session starts, which would delete that session's files under it (R-II V1); give "
            f"this session another path") from None
    os.ftruncate(fd, 0)
    os.pwrite(fd, str(os.getpid()).encode("ascii"), 0)
    config.veracium_basetemp_lock = fd
    return lock


def sqlite_error_names(exc):
    """Every sqlite3 error in an exception's chain, as `(type, sqlite_errorname or None, message)` (R-I/R-II round 2,
    V1 (d)). The reviewer's trace kept only the message, and "attempt to write a readonly database" is the message of
    both SQLITE_READONLY (8: a chmod, a read-only remount) and SQLITE_READONLY_DBMOVED (1032: the open file or its
    directory removed or replaced), so the message alone cannot say which. `sqlite_errorname` exists from Python 3.11;
    on 3.10 the name is None and says so."""
    import sqlite3
    out, seen = [], set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        if isinstance(exc, sqlite3.Error):
            out.append((type(exc).__name__, getattr(exc, "sqlite_errorname", None), str(exc)))
        exc = exc.__cause__ or exc.__context__
    return out


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """V1 (d): a failure whose chain holds a sqlite3 error records each error's extended name on the report, as a
    JUnit property (`sqlite_error`) and a report section, so the next readonly-database failure says which one it is."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        # 0048 round 4: the edges-write tripwire's teardown checks a cell's stores only when the cell itself PASSED —
        # a failed cell has already detected its defect, and a second report would turn a kill into an error
        item._0048_call_failed = rep.failed
    if call.excinfo is not None:
        for name, errname, msg in sqlite_error_names(call.excinfo.value):
            rep.user_properties.append(("sqlite_error", f"{name} {errname} {msg}"))
            rep.sections.append(("sqlite error", f"{name}: sqlite_errorname={errname}: {msg}"))


@pytest.fixture(autouse=True)
def _unattested_warning_once_per_test():
    """0007 §4e emits the unattested-build warning once per PROCESS (INV-SA7). Under pytest-randomly whichever test
    opened the first store in a worker would see it and no other, so each test starts with the once-flag clear: a
    test's warnings depend on what it does, never on the order it ran in (research's stage-1 read, item 14 D2)."""
    import sys
    sv = sys.modules.get("veracium.store.schema_version")
    if sv is not None:
        sv._WARNED.clear()
    yield
