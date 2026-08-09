"""Suite-wide fixtures.

VERACIUM_FORBID_NETWORK=1 arms a socket kill-switch for the whole run: any attempt to
create a network socket raises with a stack trace identifying the caller. The suite is
designed to pass fully offline (the network-capable modules — telemetry, diagnostics —
are exercised through injected poster stubs), and two isolated review-sandbox runs were
stopped by environment-level HTTPS attempts that could not be attributed. This makes the
no-network property EXECUTABLE rather than asserted: a reviewer runs with the variable
set, and either the suite passes (proving no test needs the network) or the raising
stack trace names the offender precisely.
"""
import os
import socket

import pytest


@pytest.fixture(autouse=True, scope="session")
def _forbid_network():
    if os.environ.get("VERACIUM_FORBID_NETWORK") != "1":
        yield
        return
    real_socket = socket.socket

    class _ForbiddenSocket(socket.socket):
        def __init__(self, family=socket.AF_INET, type=socket.SOCK_STREAM, *a, **kw):
            # AF_UNIX/AF_UNSPEC stay permitted: local IPC is not network egress.
            if family in (socket.AF_INET, socket.AF_INET6):
                raise RuntimeError(
                    "VERACIUM_FORBID_NETWORK=1: a test attempted to create a network "
                    "socket — the suite must pass fully offline; the stack trace above "
                    "this error names the caller")
            super().__init__(family, type, *a, **kw)

    socket.socket = _ForbiddenSocket
    try:
        yield
    finally:
        socket.socket = real_socket
