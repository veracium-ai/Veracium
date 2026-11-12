#!/usr/bin/env python3
"""The container image's checks (specs/0054 §6, I1–I8), and their RED matrix.

    check_image.py build --wheel W --tag T                 build container/Dockerfile with wheel W (context: a temp dir)
    check_image.py check --image T --version V [--only I3,I4] [--key-env NAME]
    check_image.py red   --wheel W                         every RED variant: built, and refused where §6 says

`check` prints one PASS/FAIL line per invariant and exits 1 on any FAIL. `--key-env NAME` (the release step) also scans
the image for the exact bytes of $NAME, the key in use (I8b). `red` first builds the GREEN baseline and requires I1–I8 to
pass on it, then builds each deliberately wrong image of §6's RED column and requires the build to refuse with the
named reason, or the named check to FAIL. An edit whose anchor is not in the Dockerfile exactly once refuses the whole
run: a variant that changes nothing would read as a refusal that never happened.

Needs docker, and the `mcp` SDK in the running interpreter (the handshake is the SDK's own client). Nothing is written
under the repository: every build context is assembled in a temporary directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

HERE = pathlib.Path(__file__).resolve().parent
DOCKERFILE = HERE / "Dockerfile"
LOCK = HERE / "requirements.lock"
SIX = ["answer", "describe_procedures", "maintain", "recall", "record_procedure", "remember"]
TRUST_VARS = ("ANTHROPIC_API_KEY", "VERACIUM_MCP_CAPABILITY", "VERACIUM_MCP_SOURCE_ID", "VERACIUM_USER")
# I8a, two tiers (0054 v0.5): the first refused anywhere outside the base, whatever any RECORD says (a RECORD is the
# package's own claim, and the 0.1.2–0.15.0 leak was the project's own file); the second unless a distribution OTHER
# than veracium lists the path in its RECORD (certifi ships its own tests/).
NEVER = ("CLAUDE.md", ".claude", "COORDINATION.md", ".git")
UNLESS_OTHERS_OWN = ("specs", "tests")
DATA_ALLOWED = {"veracium.db", "veracium.db-wal", "veracium.db-shm", "veracium.db-journal", "config", "state"}
KEY_SHAPE = r"sk-ant-[A-Za-z0-9_-]{20,}"                                             # I8b
ALLOWLIST = HERE / "secret_scan_allowlist.json"                                      # path + sha256; empty


def sh(*a, check=False, **kw):
    return subprocess.run(list(a), capture_output=True, text=True, check=check, **kw)


# ---------------------------------------------------------------------------------------------------- build ----------
def build(wheel: pathlib.Path, tag: str, dockerfile_text: str | None = None, extra: dict | None = None,
          wheel_bytes: bytes | None = None, sha_of: bytes | None = None) -> subprocess.CompletedProcess:
    """Build an image from container/Dockerfile (or `dockerfile_text`) in a temp context: the Dockerfile, the lock and
    the wheel. `wheel_bytes` replaces the wheel's bytes; `sha_of` is the bytes WHEEL_SHA256 is computed from (the real
    wheel's, so a changed wheel is refused); `extra` adds files (path -> bytes) to the context."""
    real = wheel.read_bytes()
    with tempfile.TemporaryDirectory(prefix="veracium-image-") as d:
        ctx = pathlib.Path(d)
        (ctx / "Dockerfile").write_text(dockerfile_text if dockerfile_text is not None else DOCKERFILE.read_text())
        shutil.copy(LOCK, ctx / "requirements.lock")
        (ctx / wheel.name).write_bytes(wheel_bytes if wheel_bytes is not None else real)
        shutil.copy(HERE / ".dockerignore", ctx / ".dockerignore")
        for rel, data in (extra or {}).items():
            p = ctx / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        if extra:   # a RED variant that copies extra files must be able to see them
            (ctx / ".dockerignore").write_text("")
        sha = hashlib.sha256(sha_of if sha_of is not None else real).hexdigest()
        return sh("docker", "build", "--progress=plain", "-t", tag, "--build-arg", f"WHEEL={wheel.name}",
                  "--build-arg", f"WHEEL_SHA256={sha}", str(ctx))


# ---------------------------------------------------------------------------------------------------- check ----------
def _run(img, *a, entry=None, vol=None, net="none"):
    cmd = ["docker", "run", "--rm", "--network", net]
    if vol:
        cmd += ["-v", f"{vol}:/data"]
    if entry:
        cmd += ["--entrypoint", entry]
    return sh(*cmd, img, *a)


def _volume():
    v = f"veracium-0054-{uuid.uuid4().hex[:10]}"
    sh("docker", "volume", "create", v, check=True)
    return v


def _handshake(img, vol, errpath=None):
    """MCP initialize then tools/list over stdio, under --network none and with NO provider key (0054 §2c-ii)."""
    import anyio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command="docker", args=["run", "-i", "--rm", "--network", "none", "-v", f"{vol}:/data",
                                                          img], env={"PATH": os.environ["PATH"]})

    async def go():
        with anyio.fail_after(120):
            with open(errpath or os.devnull, "w") as err:
                async with stdio_client(params, errlog=err) as (r, w):
                    async with ClientSession(r, w) as s:
                        await s.initialize()
                        return sorted(t.name for t in (await s.list_tools()).tools)
    try:
        return anyio.run(go)
    except BaseException as e:   # noqa: BLE001 — the SDK raises an ExceptionGroup from its task group
        return f"handshake failed: {type(e).__name__}: {str(e)[:160]}"


def _pinned_base() -> str:
    return DOCKERFILE.read_text().split("ARG BASE=", 1)[1].split("\n", 1)[0].strip()


def _diff_ids(ref: str) -> list:
    return json.loads(sh("docker", "image", "inspect", ref, check=True).stdout)[0]["RootFS"]["Layers"]


def _base_clause(img: str) -> tuple:
    """I2's base clause (0054 v0.6): the image's RootFS.Layers begin with exactly the pinned base's, for this platform."""
    base = _pinned_base()
    if sh("docker", "image", "inspect", base).returncode:
        sh("docker", "pull", "-q", base, check=True)
    mine, theirs = _diff_ids(img), _diff_ids(base)
    return mine[:len(theirs)] == theirs, len(theirs), len(mine)


def _added_layers(img: str, nbase: int):
    """Every layer the image adds over the pinned base, as (index, tarfile.TarFile), read from `docker save`; each
    layer's bytes must hash to its RootFS diff_id, so the tars read are the image's own."""
    import io
    import tarfile
    mine = _diff_ids(img)
    saved = subprocess.run(["docker", "save", img], capture_output=True, check=True).stdout
    outer = tarfile.open(fileobj=io.BytesIO(saved))
    paths = json.loads(outer.extractfile("manifest.json").read())[0]["Layers"]
    if len(paths) != len(mine):
        raise SystemExit(f"REFUSED: docker save lists {len(paths)} layers, docker inspect {len(mine)}")
    out = []
    for i, path in enumerate(paths[nbase:], start=nbase):
        raw = outer.extractfile(path).read()
        if "sha256:" + hashlib.sha256(raw).hexdigest() != mine[i]:
            raise SystemExit(f"REFUSED: layer {i}'s bytes do not hash to its diff_id {mine[i][:19]}")
        out.append((i, tarfile.open(fileobj=io.BytesIO(raw))))
    return out


def check(img: str, version: str, only=None, key_env=None) -> list:
    results = []

    def record(inv, ok, detail):
        results.append((inv, ok, detail))
        print(f"{'PASS' if ok else 'FAIL'} {inv}: {detail}", flush=True)

    def want(inv):
        return only is None or inv in only

    vols = []
    try:
        cfg = json.loads(sh("docker", "image", "inspect", img, check=True).stdout)[0]["Config"]
        if want("I1"):
            got = _run(img, "-c", "import importlib.metadata as m; print(m.version('veracium'))", entry="python").stdout.strip()
            record("I1", got == version, f"installed veracium {got!r}, expected {version!r} "
                                         "(the wheel's sha256 is the build's own refusal)")
        if want("I2"):
            r = _run(img, "-c", "from veracium.store.schema_version import runtime_status as s; print(s().status)",
                     entry="python")
            st = r.stdout.strip() or r.stderr.strip()[-160:]
            line = next((l.strip() for l in _run(img, "doctor", entry="veracium").stdout.splitlines() if "runtime" in l),
                        "(no runtime line)")
            base_ok, nb, nm = _base_clause(img)
            record("I2", st == "attested" and base_ok, f"runtime_status {st!r}; the pinned base's {nb} layers "
                                                      f"{'begin' if base_ok else 'DO NOT begin'} the image's {nm}; doctor: {line}")
        if want("I3"):
            bad = [e for e in (cfg.get("Env") or []) if e.split("=", 1)[0] in TRUST_VARS]
            record("I3", not bad, f"Config.Env trust-bearing: {bad or 'none'}")
        if want("I4") or want("I5") or want("I6"):
            v = _volume(); vols.append(v)
            names = _handshake(img, v)
            if want("I5"):
                record("I5", names == SIX, f"--network none, no key: {names}")
            if want("I4"):
                u = cfg.get("User") or "(unset)"
                st = _run(img, "-c", "stat -c '%u %n' /data/veracium.db 2>&1", entry="sh", vol=v).stdout.strip()
                record("I4", u == "10001" and st == "10001 /data/veracium.db", f"Config.User {u!r}; store: {st!r}")
            if want("I6"):
                _run(img, "telemetry", "status", entry="veracium", vol=v)          # one CLI call (§6)
                top = sorted(pathlib.PurePosixPath(l.strip()).name for l in
                             _run(img, "-c", "find /data -mindepth 1 -maxdepth 1", entry="sh", vol=v).stdout.split()
                             if l.strip())
                extra = [x for x in top if x not in DATA_ALLOWED]
                record("I6", "veracium.db" in top and not extra, f"/data holds {top}; outside §4c: {extra or 'none'}")
        if want("I7"):
            v = _volume(); vols.append(v)
            _run(img, "-c", "from veracium import Memory, MemoryConfig; "
                            "Memory(llm=lambda *a, **k: '', config=MemoryConfig(db_path='/data/veracium.db')).close()",
                 entry="python", vol=v)
            ctl = _handshake(img, v)
            stamp = _run(img, "-c", "import sqlite3; c = sqlite3.connect('/data/veracium.db'); "
                                    "n = c.execute('PRAGMA user_version').fetchone()[0]; "
                                    "c.execute(f'PRAGMA user_version = {n + 1}'); c.commit(); print(n, n + 1)",
                         entry="python", vol=v).stdout.split()
            before = _run(img, "-c", "sha256sum /data/veracium.db", entry="sh", vol=v).stdout.split()[:1]
            with tempfile.NamedTemporaryFile("r", suffix=".err") as ef:
                refused = _handshake(img, v, ef.name)
                errtext = open(ef.name).read()
            after = _run(img, "-c", "sha256sum /data/veracium.db", entry="sh", vol=v).stdout.split()[:1]
            named = "newer" in errtext and "SCHEMA_VERSION" in errtext            # the refusal's own words
            ok = ctl == SIX and isinstance(refused, str) and named and before == after and len(stamp) == 2
            tail = errtext.strip().splitlines()[0][:160] if errtext.strip() else "(empty)"
            record("I7", ok, f"control at {stamp[:1]}: {'opens' if ctl == SIX else ctl}; stamped {stamp[1:]}: "
                             f"{'refused' if isinstance(refused, str) else 'OPENED'}, in its own words: {named}; "
                             f"bytes unchanged: {before == after}; stderr: {tail}")
        if want("I8"):
            # every layer the image adds over the pinned base, member by member, whatever the mode (0054 v0.6): a file
            # written in one layer and removed in a later one is still in the image, and in its own layer here.
            key = os.environ.get(key_env, "").encode() if key_env else b""
            if key_env and not key:
                record("I8", False, f"--key-env {key_env}: the variable is empty, so the exact-key scan cannot run")
                return results
            base_ok, nbase, _nm = _base_clause(img)
            if not base_ok:
                record("I8", False, "the image does not begin with the pinned base's layers, so 'added' is undefined")
                return results
            # paths listed in the RECORD of a distribution other than veracium; veracium's own are never exempt
            listing = _run(img, "-c", "import importlib.metadata as m\nfor d in m.distributions():\n"
                                      "    for f in d.files or []:\n"
                                      "        print(d.metadata['Name'], str(d.locate_file(f)).lstrip('/'), sep='\\t')",
                           entry="python").stdout.split("\n")
            owned = {l.split("\t", 1)[1] for l in listing if "\t" in l and l.split("\t", 1)[0].lower() != "veracium"}
            owned_dirs = {str(q) for o in owned for q in pathlib.PurePosixPath(o).parents}

            def _owned(f):
                return f in owned or f in owned_dirs or (f.endswith(".pyc") and "__pycache__" in f
                                                         and str(pathlib.PurePosixPath(f).parent.parent) in owned_dirs)
            shape = re.compile(KEY_SHAPE.encode())
            allow = {(e["path"], e["sha256"]) for e in json.loads(ALLOWLIST.read_text())["allowed"]}
            hits, keys, members, layers = [], [], 0, 0
            for i, tf in _added_layers(img, nbase):
                layers += 1
                for m in tf.getmembers():
                    members += 1
                    name = m.name.lstrip("./").rstrip("/")
                    pp = pathlib.PurePosixPath(name)
                    target = str(pp.parent / pp.name[len(".wh."):]) if pp.name.startswith(".wh.") else name
                    parts = set(pathlib.PurePosixPath(target).parts)
                    if parts & set(NEVER) or (parts & set(UNLESS_OTHERS_OWN) and not _owned(target)):
                        hits.append(f"layer {i}: {name}")
                    if m.isfile():
                        data = tf.extractfile(m).read()
                        if (shape.search(data) or (key and key in data)) and \
                                (name, hashlib.sha256(data).hexdigest()) not in allow:
                            keys.append(f"layer {i}: {name} (mode {m.mode:o})")
            record("I8", not hits and not keys,
                   f"{members} members in {layers} added layers; repository paths: {hits[:5] or 'none'}; "
                   f"key-shaped{' or exact-key' if key else ''} matches: {keys[:5] or 'none'}")
    finally:
        for v in vols:
            sh("docker", "volume", "rm", "-f", v)
    return results


# ------------------------------------------------------------------------------------------------------ red ----------
def _edit(text: str, edits) -> str:
    for a, b in edits:
        n = text.count(a)
        if n != 1:
            raise SystemExit(f"REFUSED: a RED edit's anchor occurs {n} times in container/Dockerfile, not once: {a[:70]!r}")
        text = text.replace(a, b)
    return text


def _wheel_with(raw: bytes, rel: str, data: bytes) -> bytes:
    """`raw` (a wheel) with one more file, listed in its own RECORD with a correct hash: the package's own claim."""
    import base64, io, zipfile
    src = zipfile.ZipFile(io.BytesIO(raw)); out = io.BytesIO()
    record = next(n for n in src.namelist() if n.endswith(".dist-info/RECORD"))
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for n in src.namelist():
            body = src.read(n)
            if n == record:
                body = body.rstrip(b"\n") + f"\n{rel},sha256={digest},{len(data)}\n".encode()
            dst.writestr(n, body)
        dst.writestr(rel, data)
    return out.getvalue()


_SITE = "/usr/local/lib/python3.14/site-packages"
_FLATBASE = "veracium-0054-flatbase:red"


def _make_flatbase() -> None:
    """I2's RED case (0054 v0.6): the pinned base's own filesystem re-imported as ONE layer. Its SQLite is the same
    attested build, so the status passes; only the base clause can refuse it."""
    base = _pinned_base()
    if sh("docker", "image", "inspect", base).returncode:
        sh("docker", "pull", "-q", base, check=True)
    cid = sh("docker", "create", base, check=True).stdout.strip()
    try:
        tar = subprocess.run(["docker", "export", cid], capture_output=True, check=True).stdout
    finally:
        sh("docker", "rm", cid)
    env = json.loads(sh("docker", "image", "inspect", base, check=True).stdout)[0]["Config"]["Env"]
    changes = [x for e in env for x in ("--change", f"ENV {e.split('=', 1)[0]}={e.split('=', 1)[1]}")]
    subprocess.run(["docker", "import", *changes, "-", _FLATBASE], input=tar, capture_output=True, check=True)
_USERADD = "&& useradd --system --uid 10001 --home-dir /home/veracium --no-create-home --shell /usr/sbin/nologin veracium"
_FAKE_KEY = ("sk-ant-" + "api03-" + "PLANTED0054REDCASE" * 2).encode()   # FAKE and key-shaped; never a real key

# (name, the invariant, the Dockerfile edits, build kwargs, how it must fail: ("build", text in the build log) or
# ("check", invariant)). §6's RED column, one row each; I4 has two.
RED = [
    ("I1-wheel-one-byte", "I1", [], {"mutate_wheel": True}, ("build", "FAILED")),
    ("I2-unattested-base", "I2", [("ARG BASE=python@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f",
                                   "ARG BASE=python:3.14-alpine3.21"),
                                  (_USERADD, "&& adduser -S -u 10001 -h /home/veracium -s /sbin/nologin veracium")],
     {}, ("build", "runtime status: verified")),
    ("I3-capability-default", "I3", [("ENTRYPOINT [", "ENV VERACIUM_MCP_CAPABILITY=direct\nENTRYPOINT [")], {},
     ("check", "I3")),
    ("I4-no-user", "I4", [("USER 10001\n", "")], {}, ("check", "I4")),
    ("I4-wrong-store-variable", "I4", [("ENV VERACIUM_DB_PATH=/data/veracium.db", "ENV VERACIUM_DB=/data/veracium.db")],
     {}, ("check", "I4")),
    ("I5-cli-entrypoint", "I5", [('ENTRYPOINT ["veracium-mcp"]', 'ENTRYPOINT ["veracium"]')], {}, ("check", "I5")),
    ("I6-home-on-the-volume", "I6", [("HOME=/home/veracium", "HOME=/data"),
                                     ("USER 10001\n", "RUN cp -r /etc/skel/. /data/ && chown -R 10001 /data\nUSER 10001\n")],
     {}, ("check", "I6")),
    ("I8-repository-copied", "I8", [("ENTRYPOINT [", "COPY repo /src\nENTRYPOINT [")],
     {"extra": {"repo/COORDINATION.md": b"planted\n", "repo/specs/x.md": b"planted\n", "repo/tests/test_x.py": b"x = 1\n"}},
     ("check", "I8")),
    ("I8-veracium-ships-claude-md", "I8", [], {"wheel_adds": ("veracium/CLAUDE.md", b"# planted\n")}, ("check", "I8")),
    ("I8-unowned-tests-in-site-packages", "I8",
     [("USER 10001\n", f"RUN mkdir -p {_SITE}/tests && echo 'x = 1' > {_SITE}/tests/planted.py\nUSER 10001\n")], {},
     ("check", "I8")),
    ("I8-written-then-removed", "I8", [("ENTRYPOINT [", "RUN echo 'ANTHROPIC_API_KEY=" + _FAKE_KEY.decode()
                                        + "' > /home/veracium/.env\nRUN rm /home/veracium/.env\nENTRYPOINT [")], {},
     ("check", "I8")),
    ("I8-mode-000", "I8", [("ENTRYPOINT [", "RUN echo 'ANTHROPIC_API_KEY=" + _FAKE_KEY.decode()
                            + "' > /home/veracium/.k && chmod 000 /home/veracium/.k\nENTRYPOINT [")], {}, ("check", "I8")),
    ("I8-repository-copied-then-removed", "I8", [("ENTRYPOINT [", "COPY --chown=10001 repo /src\nRUN rm -rf /src/*\nENTRYPOINT [")],
     {"extra": {"repo/COORDINATION.md": b"planted\n", "repo/specs/x.md": b"planted\n"}}, ("check", "I8")),
    ("I2-flattened-base", "I2", [("ARG BASE=python@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f",
                                  "ARG BASE=" + _FLATBASE)], {"prep": "flatbase"}, ("check", "I2")),
    ("I8-planted-key", "I8", [("ENTRYPOINT [", "RUN echo 'ANTHROPIC_API_KEY=" + _FAKE_KEY.decode()
                               + "' > /home/veracium/.env\nENTRYPOINT [")], {}, ("check", "I8")),
]


def red(wheel: pathlib.Path) -> int:
    version = wheel.name.split("-")[1]
    green = f"veracium-0054-green:{uuid.uuid4().hex[:8]}"
    b = build(wheel, green)
    if b.returncode:
        print(b.stdout[-2000:] + b.stderr[-2000:]); print("REFUSED: the GREEN baseline does not build"); return 1
    base = check(green, version)
    if not all(ok for _i, ok, _d in base) or len(base) != 8:
        print("REFUSED: the GREEN baseline does not pass I1–I8, so no RED case can mean anything"); return 1
    text = DOCKERFILE.read_text(); bad = []
    for name, inv, edits, kw, (how, what) in RED:
        tag = f"veracium-0054-red:{name.lower()}"
        wb = sha_of = None
        if kw.get("mutate_wheel"):
            raw = wheel.read_bytes(); wb = raw[:-1] + bytes([raw[-1] ^ 1])
        if kw.get("prep") == "flatbase":
            _make_flatbase()
        if kw.get("wheel_adds"):     # I1 is bypassed on purpose (its sha256 is the rebuilt wheel's): this tests I8 alone
            wb = sha_of = _wheel_with(wheel.read_bytes(), *kw["wheel_adds"])
        r = build(wheel, tag, _edit(text, edits), extra=kw.get("extra"), wheel_bytes=wb, sha_of=sha_of)
        if how == "build":
            log = r.stdout + r.stderr
            ok = r.returncode != 0 and what in log
            print(f"{'RED ' if ok else 'MISS'} {name}: build exit {r.returncode}; refusal names {what!r}: {what in log}",
                  flush=True)
        else:
            if r.returncode:
                print(f"MISS {name}: the variant did not build (exit {r.returncode}), so its check never ran"); bad.append(name)
                continue
            res = check(tag, version, only={what})
            ok = len(res) == 1 and res[0][1] is False
            print(f"{'RED ' if ok else 'MISS'} {name}: {what} {'FAILED, as it must' if ok else 'did not fail'}", flush=True)
            sh("docker", "image", "rm", "-f", tag)
        if not ok:
            bad.append(name)
    sh("docker", "image", "rm", "-f", green, _FLATBASE)
    print(f"RED matrix: {len(RED) - len(bad)} of {len(RED)} refused as §6 names" + (f"; MISSED: {bad}" if bad else ""))
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--wheel", required=True, type=pathlib.Path); b.add_argument("--tag", required=True)
    c = sub.add_parser("check"); c.add_argument("--image", required=True); c.add_argument("--version", required=True)
    c.add_argument("--only"); c.add_argument("--key-env")
    r = sub.add_parser("red"); r.add_argument("--wheel", required=True, type=pathlib.Path)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        res = build(a.wheel, a.tag)
        print((res.stdout + res.stderr)[-3000:])
        return res.returncode
    if a.cmd == "check":
        res = check(a.image, a.version, set(a.only.split(",")) if a.only else None, a.key_env)
        return 0 if res and all(ok for _i, ok, _d in res) else 1
    return red(a.wheel)


if __name__ == "__main__":
    sys.exit(main())
