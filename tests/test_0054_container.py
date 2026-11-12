"""specs/0054: the container image's static contract, checked without docker.

The image's behaviour (I1–I8) is container/check_image.py's, run in the `container` workflow on a built image. These
cells hold the files that workflow builds from to the spec, so a change to them fails here on every run, docker or not:
the base pinned by digest; no trust-bearing default; non-root; the working directory off the volume (C1); the store
variable the server actually reads; every locked dependency hashed; and a RED matrix whose every edit still applies.
"""
import importlib.util
import json
import pathlib
import re
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
C = ROOT / "container"
DOCKERFILE = (C / "Dockerfile").read_text()


def _check_image():
    spec = importlib.util.spec_from_file_location("veracium_check_image", C / "check_image.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _instructions():
    """(INSTRUCTION, argument) pairs, continuation lines joined and comments dropped."""
    out, cur = [], ""
    for line in DOCKERFILE.splitlines():
        if not cur and (not line.strip() or line.lstrip().startswith("#")):
            continue
        cur += line.rstrip("\\").strip() + " "
        if not line.rstrip().endswith("\\"):
            word, _, rest = cur.strip().partition(" ")
            out.append((word.upper(), rest.strip()))
            cur = ""
    return out


def test_the_base_is_pinned_by_digest():
    bases = [a for i, a in _instructions() if i == "ARG" and a.startswith("BASE=")]
    assert len(bases) == 1 and re.fullmatch(r"BASE=python@sha256:[0-9a-f]{64}", bases[0]), bases
    assert ("FROM", "${BASE}") in _instructions()


def test_the_image_sets_no_trust_bearing_variable():
    """I3, statically: none of the host's four variables is an ENV or ARG default of the image."""
    ci = _check_image()
    declared = []
    for inst, arg in _instructions():
        if inst in ("ENV", "ARG"):
            declared += [m.group(1) for m in re.finditer(r"(?:^|\s)([A-Z_][A-Z0-9_]*)=", arg)]
    assert declared, "no ENV parsed: the parser, not the image, is wrong"
    assert not set(declared) & set(ci.TRUST_VARS), set(declared) & set(ci.TRUST_VARS)


def test_non_root_the_working_directory_off_the_volume_and_the_server_as_entrypoint():
    ins = _instructions()
    assert [a for i, a in ins if i == "USER"] == ["10001"]
    workdirs = [a for i, a in ins if i == "WORKDIR"]
    assert workdirs == ["/home/veracium"], workdirs        # never /data (0054 §4b, C1)
    assert [a for i, a in ins if i == "ENTRYPOINT"] == ['["veracium-mcp"]']
    assert [a for i, a in ins if i == "VOLUME"] == ['["/data"]']


def test_the_attested_gate_reads_the_status_not_doctors_prose():
    """0054 §4b, C2: the build gate tests runtime_status().status == "attested", the value I2 reads."""
    runs = [a for i, a in _instructions() if i == "RUN" and "runtime_status" in a]
    assert len(runs) == 1 and "s.status == 'attested'" in runs[0] and "sys.exit(" in runs[0], runs
    assert "grep" not in runs[0], "the gate must not match doctor's text"


def test_the_store_variable_is_the_one_the_server_reads():
    """dev's prototype first wrote VERACIUM_DB; the image's name must be the one mcp_server.build_memory reads."""
    env = " ".join(a for i, a in _instructions() if i == "ENV")
    assert "VERACIUM_DB_PATH=/data/veracium.db" in env, env
    src = (ROOT / "src" / "veracium" / "mcp_server.py").read_text()
    assert 'os.environ.get("VERACIUM_DB_PATH"' in src


def test_every_locked_dependency_is_hashed_and_the_lock_covers_the_install():
    lock = (C / "requirements.lock").read_text()
    reqs = re.findall(r"^([A-Za-z0-9_.-]+)==[^\n]*\\\n((?:\s+--hash=sha256:[0-9a-f]{64}(?: \\)?\n)+)", lock, re.M)
    names = {n.lower().replace("_", "-") for n, _h in reqs}
    pinned_lines = [l for l in lock.splitlines() if re.match(r"^[A-Za-z0-9]", l)]
    assert len(reqs) == len(pinned_lines) > 0, "a pinned requirement without hashes"
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    wanted = project["dependencies"] + project["optional-dependencies"]["mcp"] + project["optional-dependencies"]["anthropic"]
    for req in wanted:
        name = re.match(r"[A-Za-z0-9_.-]+", req).group(0).lower().replace("_", "-")
        assert name in names, f"{req} (pyproject) is not in container/requirements.lock: regenerate the lock"


def test_every_red_edit_still_applies_and_the_matrix_names_its_invariants():
    """A RED variant whose anchor no longer occurs would build the GREEN image and read as a refusal never made."""
    ci = _check_image()
    for name, _inv, edits, _kw, _how in ci.RED:
        ci._edit(DOCKERFILE, edits)                           # raises SystemExit unless each anchor occurs once
    covered = {inv for _n, inv, *_ in ci.RED}
    assert covered == {"I1", "I2", "I3", "I4", "I5", "I6", "I8"}, covered     # I7's RED is its own control, in check()
    assert {n for n, *_ in ci.RED} >= {"I4-no-user", "I4-wrong-store-variable", "I8-repository-copied", "I8-planted-key",
                                       "I8-veracium-ships-claude-md", "I8-unowned-tests-in-site-packages"}
    assert "CLAUDE.md" in ci.NEVER and "tests" in ci.UNLESS_OTHERS_OWN        # 0054 v0.5's two tiers


def test_a_wheel_rebuilt_with_one_more_file_lists_it_in_its_own_record():
    """The I8 RED case's wheel must carry the file AND claim it in RECORD, or it would test nothing about RECORD."""
    import base64, hashlib, io, zipfile
    ci = _check_image()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("veracium/__init__.py", b"")
        z.writestr("veracium-0.0.0.dist-info/RECORD", b"veracium/__init__.py,,\n")
    out = zipfile.ZipFile(io.BytesIO(ci._wheel_with(buf.getvalue(), "veracium/CLAUDE.md", b"x\n")))
    digest = base64.urlsafe_b64encode(hashlib.sha256(b"x\n").digest()).rstrip(b"=").decode()
    assert out.read("veracium/CLAUDE.md") == b"x\n"
    assert f"veracium/CLAUDE.md,sha256={digest},2" in out.read("veracium-0.0.0.dist-info/RECORD").decode()


def test_the_secret_scan_allowlist_is_well_formed():
    data = json.loads((C / "secret_scan_allowlist.json").read_text())
    for e in data["allowed"]:
        assert set(e) == {"path", "sha256"} and re.fullmatch(r"[0-9a-f]{64}", e["sha256"]), e


def _top_level_block(text: str, key: str) -> list:
    """The keys directly under a top-level `key:` of a workflow file (two-space indent), read from the text."""
    lines = text.splitlines()
    start = lines.index(f"{key}:")
    out = []
    for line in lines[start + 1:]:
        if line and not line.startswith(" "):
            break
        if line.startswith("  ") and not line.startswith("   ") and line.strip().endswith(":"):
            out.append(line.strip()[:-1])
    return out


def test_only_the_hand_run_release_workflow_can_push_an_image():
    """0054 §4a: an image is pushed only on the owner's release word. The per-push workflow has no packages
    permission and no push; the release workflow runs on workflow_dispatch alone and refuses a re-pushed version."""
    wf = ROOT / ".github" / "workflows"
    text = (wf / "container.yml").read_text()
    assert "packages:" not in text and "docker push" not in text and "docker login" not in text
    assert set(_top_level_block(text, "on")) == {"push", "pull_request", "workflow_dispatch"}
    rtext = (wf / "container-release.yml").read_text()
    assert _top_level_block(rtext, "on") == ["workflow_dispatch"], _top_level_block(rtext, "on")
    assert "already exists; a fix is a new version" in rtext            # §4a.3, never re-pushed
    assert rtext.index("check_image.py check") < rtext.index("docker push")   # gated before pushed
    assert 'test "$gated" = "$pulled"' in rtext                        # the pushed image is the gated one
