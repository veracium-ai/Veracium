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
