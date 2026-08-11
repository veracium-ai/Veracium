"""specs/0015 I8, I12–I13, I15–I17: the consent lifecycle."""

import json
import os

import pytest

import veracium.telemetry as T


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    yield


def _cfgfile():
    return T.TelemetryConfig.path()


def _write(d):
    p = _cfgfile()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d))


def _enabled_cfg(version=1, epoch=1, endpoint="https://x/c"):
    _write({"enabled": True, "install_id": "i", "endpoint": endpoint,
            "schema_version": version, "consent_epoch": epoch})
    return T.TelemetryConfig.load()


# ---- I12 / I13: stamping -------------------------------------------------

def test_set_enabled_never_stamps_consent_version():
    _enabled_cfg(version=1, epoch=1)
    for flag in (False, True, True, False):
        cfg = T.set_enabled(flag)
        assert cfg.schema_version == 1


def test_only_affirmative_consent_stamps_current(monkeypatch):
    # non-interactive, EOF, and "no" all end at 1
    cfg = T.prompt_consent(interactive=False)
    assert (cfg.enabled, cfg.schema_version) == (False, 1)
    os.remove(_cfgfile())
    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(EOFError()))
    cfg = T.prompt_consent(interactive=True)
    assert (cfg.enabled, cfg.schema_version) == (False, 1)
    os.remove(_cfgfile())
    monkeypatch.setattr("builtins.input", lambda *_: "no")
    cfg = T.prompt_consent(interactive=True)
    assert (cfg.enabled, cfg.schema_version) == (False, 1)
    os.remove(_cfgfile())
    monkeypatch.setattr("builtins.input", lambda *_: "y")
    cfg = T.prompt_consent(interactive=True)
    assert (cfg.enabled, cfg.schema_version) == (True, T.SCHEMA_VERSION)
    # existing config: idempotent no-op, no re-stamp (R3-4)
    monkeypatch.setattr("builtins.input", lambda *_: "y")
    before = T.TelemetryConfig.load().consent_epoch
    cfg = T.prompt_consent(interactive=True)
    assert cfg.consent_epoch == before


def test_config_default_schema_version_is_1():
    assert T.TelemetryConfig().schema_version == 1


def test_fresh_programmatic_enable_stays_v1():
    cfg = T.set_enabled(True)
    assert (cfg.enabled, cfg.schema_version) == (True, 1)


def test_epoch_bumps_iff_pair_changed():
    a = T.set_enabled(True)
    b = T.set_enabled(True)     # idempotent: no bump
    c = T.set_enabled(False)    # change: bump
    assert a.consent_epoch == b.consent_epoch and c.consent_epoch == a.consent_epoch + 1
    d = T.accept_current_consent()   # enable+stamp = ONE transition
    assert d.consent_epoch == c.consent_epoch + 1
    e = T.accept_current_consent()   # idempotent acceptance: no bump
    assert e.consent_epoch == d.consent_epoch


# ---- I16: validity -------------------------------------------------------

@pytest.mark.parametrize("bad", [None, "2", True, 2.0, [2], 0, -1, 99])
def test_invalid_schema_version_reads_as_v1(bad):
    _write({"enabled": True, "install_id": "i", "schema_version": bad,
            "consent_epoch": 1})
    assert T.TelemetryConfig.load().schema_version == 1


@pytest.mark.parametrize("bad", [None, "1", True, 1.0, [1], 0, -3])
def test_invalid_consent_epoch_normalizes_nonzero(bad):
    _write({"enabled": True, "install_id": "i", "schema_version": 1,
            "consent_epoch": bad})
    assert T.TelemetryConfig.load().consent_epoch == 0  # the invalid marker
    coll = T.load_collector_if_enabled()
    assert coll is not None and coll.consent_epoch >= 1  # normalized under lock
    assert T.TelemetryConfig.load().consent_epoch >= 1


def test_adoption_time_invalid_epoch_normalizes_and_discards():
    cfg = _enabled_cfg(version=2, epoch=3)
    coll = T.Collector(consent_epoch=3, schema_version=2)
    coll.record("ingest", {"facts": 1, "supersessions": 1})
    _write({"enabled": True, "install_id": "i", "endpoint": "https://x/c",
            "schema_version": 2, "consent_epoch": "corrupt"})
    assert T.preview(T.TelemetryConfig.load(), coll) is not None or True
    # after the locked normalization the epoch differs from 3 → discarded
    assert coll._counts["ingest"] == 0


def test_unknown_config_key_fails_closed_whole_config():
    _write({"enabled": True, "install_id": "i", "schema_version": 1,
            "consent_epoch": 1, "mystery": 1})
    cfg = T.TelemetryConfig.load()
    assert cfg.enabled is False


# ---- I8: record-time gating + transitions --------------------------------

def test_gated_fields_never_accumulate_pre_consent():
    coll = T.Collector(consent_epoch=1, schema_version=1)
    coll.record("ingest", {"facts": 2, "supersessions": 5, "reinforcements": 3})
    sums = coll.snapshot()["events"]["ingest"]["sums"]
    assert sums == {"facts": 2.0}


def test_v1_consent_strips_new_fields():
    cfg = _enabled_cfg(version=1, epoch=1)
    coll = T.Collector(consent_epoch=1, schema_version=1)
    coll.record("ingest", {"facts": 1, "supersessions": 4})
    p = T.preview(cfg, coll)
    assert "supersessions" not in p["events"]["ingest"]["sums"]


def test_v1_to_v2_transition_through_a_live_memory_carrier(tmp_path):
    """I8: record under v1 → accept v2 (display flow) → flush adopts → record
    → only post-acceptance values sent."""
    from veracium import Memory, MemoryConfig, SqliteStore
    _enabled_cfg(version=1, epoch=1)

    values = ["A", "B", "C", "D"]
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            v = values.pop(0)
            return json.dumps({"triples": [{"subject": "user",
                                            "relation": "located_at",
                                            "object": v}],
                               "episode": v})
        return "ok"
    db = str(tmp_path / "m.db")
    m = Memory(llm=llm, store=SqliteStore(db), config=MemoryConfig(db_path=db))
    m.telemetry = T.load_collector_if_enabled()
    m.remember("u", "USER: move A"); m.remember("u", "USER: move B")  # 1 supersession, v1: dropped
    T.accept_current_consent(endpoint="https://x/c")                  # v2, epoch bump
    sent = []
    T.flush_if_due(T.TelemetryConfig.load(), m.telemetry,
                   poster=lambda u, p: sent.append(p))                # adopts: discard, no due data
    m.remember("u", "USER: move C"); m.remember("u", "USER: move D")  # 2 supersessions under v2
    cfg = T.TelemetryConfig.load(); cfg.last_sent = None; cfg.save()
    T.flush_if_due(cfg, m.telemetry, poster=lambda u, p: sent.append(p))
    assert sent, "the second flush must send"
    sums = sent[-1]["events"]["ingest"]["sums"]
    assert sums["supersessions"] == 2.0  # ONLY post-acceptance values


def test_downgrade_adoption_discards_gated_fields():
    coll = T.Collector(consent_epoch=2, schema_version=2)
    coll.record("ingest", {"supersessions": 3, "facts": 1})
    cfg = _enabled_cfg(version=1, epoch=5)
    coll.adopt_consent(cfg)
    assert coll.snapshot()["events"] == {}


def test_disabled_period_records_are_never_sent(tmp_path):
    """I17: enabled → disabled → record → re-enabled → flush sends nothing
    from the disabled period (the epoch discard)."""
    _enabled_cfg(version=2, epoch=1)
    coll = T.load_collector_if_enabled()
    coll.record("ingest", {"facts": 1})
    T.set_enabled(False)                       # epoch bump
    coll.record("ingest", {"facts": 7})        # the disabled-period record
    T.set_enabled(True, endpoint="https://x/c")  # epoch bump again (ABA-proof)
    sent = []
    T.flush_if_due(T.TelemetryConfig.load(), coll,
                   poster=lambda u, p: sent.append(p))
    assert not sent or "ingest" not in sent[0].get("events", {})


def test_disabled_start_activates_only_at_restart(tmp_path):
    """I8/R3-2: a disabled start yields no collector; later acceptance takes
    effect at the next construction (the restart boundary)."""
    _write({"enabled": False, "install_id": "i", "schema_version": 1,
            "consent_epoch": 1})
    assert T.load_collector_if_enabled() is None
    T.accept_current_consent()
    # the running process still has None — nothing was collected or sent;
    # a NEW construction (the restart) gets a collector
    assert T.load_collector_if_enabled() is not None


def test_preview_is_what_flush_posts():
    cfg = _enabled_cfg(version=2, epoch=1)
    coll = T.Collector(consent_epoch=1, schema_version=2)
    coll.record("ingest", {"facts": 1, "supersessions": 2})
    p = T.preview(cfg, coll)
    sent = []
    cfg2 = T.TelemetryConfig.load()
    T.flush_if_due(cfg2, coll, poster=lambda u, x: sent.append(x))
    assert sent and sent[0]["events"] == p["events"]


# ---- I15: reset ----------------------------------------------------------

def test_reset_preserves_adopted_consent_two_periods():
    cfg = _enabled_cfg(version=2, epoch=1)
    coll = T.Collector(consent_epoch=1, schema_version=2)
    sent = []
    for _ in range(2):
        coll.record("ingest", {"supersessions": 1, "facts": 1})
        c = T.TelemetryConfig.load(); c.last_sent = None; c.save()
        assert T.flush_if_due(c, coll, poster=lambda u, p: sent.append(p))
    assert len(sent) == 2
    for p in sent:
        assert p["events"]["ingest"]["sums"]["supersessions"] == 1.0


# ---- I17: lock + tombstone + flush/preview -------------------------------

def test_racing_transitions_mint_distinct_epochs():
    _enabled_cfg(version=1, epoch=1)
    import threading
    epochs = []
    def toggle(flag):
        epochs.append(T.set_enabled(flag).consent_epoch)
    a = threading.Thread(target=toggle, args=(False,))
    b = threading.Thread(target=toggle, args=(True,))
    a.start(); b.start(); a.join(); b.join()
    assert len(set(epochs)) == len([e for e in epochs])  # distinct


def test_paused_live_holder_is_never_broken():
    """R8-1: a held lock is NEVER entered by a second acquirer, however long
    the holder pauses — the second acquisition times out fail-closed."""
    fd = T._acquire_lock()
    assert fd is not None
    try:
        assert T._acquire_lock(deadline_s=0.3) is None
    finally:
        T._release_lock(fd)


def test_posix_live_holder_exclusion_across_processes(tmp_path):
    """I17a: kernel-mediated exclusion, independent processes."""
    if os.name != "posix":
        pytest.skip("POSIX adapter test (specs/0015 I17)")
    import subprocess, sys, textwrap
    fd = T._acquire_lock()
    try:
        code = textwrap.dedent(f"""
            import os; os.environ['XDG_CONFIG_HOME'] = {str(_cfgfile().parent.parent)!r}
            import veracium.telemetry as T
            print("GOT" if T._acquire_lock(deadline_s=0.3) is not None else "BLOCKED")
        """)
        out = subprocess.run([sys.executable, "-c", code], capture_output=True,
                             text=True, env={**os.environ, "PYTHONPATH": "src"})
        assert "BLOCKED" in out.stdout
    finally:
        T._release_lock(fd)


def test_posix_death_releases_lock_across_processes(tmp_path):
    """I17a: a crashed holder's lock is released by the OS."""
    if os.name != "posix":
        pytest.skip("POSIX adapter test (specs/0015 I17)")
    import subprocess, sys, textwrap
    code = textwrap.dedent(f"""
        import os; os.environ['XDG_CONFIG_HOME'] = {str(_cfgfile().parent.parent)!r}
        import veracium.telemetry as T
        fd = T._acquire_lock(); assert fd is not None
        os._exit(1)  # die holding it
    """)
    subprocess.run([sys.executable, "-c", code],
                   env={**os.environ, "PYTHONPATH": "src"})
    fd = T._acquire_lock(deadline_s=0.5)
    assert fd is not None
    T._release_lock(fd)


def test_preauth_lock_failure_returns_false_no_adoption(monkeypatch):
    cfg = _enabled_cfg(version=2, epoch=1)
    coll = T.Collector(consent_epoch=1, schema_version=1)  # stale consent
    monkeypatch.setattr(T, "_acquire_lock", lambda *a, **k: None)
    assert T.flush_if_due(cfg, coll, poster=lambda u, p: None) is False
    assert coll.schema_version == 1  # no adoption happened


def test_postsend_lock_failure_returns_true_last_sent_unwritten(monkeypatch):
    cfg = _enabled_cfg(version=2, epoch=1)
    coll = T.Collector(consent_epoch=1, schema_version=2)
    coll.record("ingest", {"facts": 1})
    real = T._acquire_lock
    calls = {"n": 0}
    def failing_second(*a, **k):
        calls["n"] += 1
        return real(*a, **k) if calls["n"] == 1 else None
    monkeypatch.setattr(T, "_acquire_lock", failing_second)
    assert T.flush_if_due(T.TelemetryConfig.load(), coll,
                          poster=lambda u, p: None) is True
    assert T.TelemetryConfig.load().last_sent is None  # unwritten


def test_collector_load_lock_failure_returns_none(monkeypatch):
    _enabled_cfg()
    monkeypatch.setattr(T, "_acquire_lock", lambda *a, **k: None)
    assert T.load_collector_if_enabled() is None


def test_preview_lock_failure_returns_none(monkeypatch):
    cfg = _enabled_cfg()
    coll = T.Collector(consent_epoch=1, schema_version=1)
    monkeypatch.setattr(T, "_acquire_lock", lambda *a, **k: None)
    assert T.preview(cfg, coll) is None


def test_explicit_transition_raises_on_lock_failure(monkeypatch):
    monkeypatch.setattr(T, "_acquire_lock", lambda *a, **k: None)
    with pytest.raises(T.TelemetryLockError):
        T.set_enabled(True)
    with pytest.raises(T.TelemetryLockError):
        T.accept_current_consent()


def test_tombstone_after_deletion_drops_records_pre_and_post_post():
    cfg = _enabled_cfg(version=2, epoch=1)
    coll = T.Collector(consent_epoch=1, schema_version=2)
    os.remove(_cfgfile())
    assert T.flush_if_due(cfg, coll, poster=lambda u, p: None) is False
    coll.record("ingest", {"facts": 9})
    assert coll.snapshot()["events"] == {}  # tombstoned: dropped
    assert not _cfgfile().exists()          # NEVER recreated


def test_same_epoch_recreation_never_sends_post_erasure_records():
    """R10-1: delete → record → recreate at the SAME epoch → nothing from the
    erased period is sent."""
    cfg = _enabled_cfg(version=2, epoch=4)
    coll = T.Collector(consent_epoch=4, schema_version=2)
    os.remove(_cfgfile())
    T.flush_if_due(cfg, coll, poster=lambda u, p: None)  # observes absence → tombstone
    coll.record("ingest", {"facts": 5, "supersessions": 5})  # post-erasure
    _enabled_cfg(version=2, epoch=4)                     # SAME-epoch recreation
    sent = []
    T.flush_if_due(T.TelemetryConfig.load(), coll,
                   poster=lambda u, p: sent.append(p))
    assert not sent or "ingest" not in sent[0].get("events", {})


def test_malformed_config_never_rewritten():
    cfg = _enabled_cfg(version=2, epoch=1)
    coll = T.Collector(consent_epoch=1, schema_version=2)
    _cfgfile().write_text("{not json")
    before = _cfgfile().read_text()
    assert T.flush_if_due(cfg, coll, poster=lambda u, p: None) is False
    coll.record("ingest", {"facts": 1})
    assert coll.snapshot()["events"] == {}  # tombstoned
    assert _cfgfile().read_text() == before  # untouched


def test_read_config_status_three_states():
    assert T._read_config_status()[0] == "absent"
    _write({"enabled": True, "install_id": "i", "schema_version": 1,
            "consent_epoch": 1})
    assert T._read_config_status()[0] == "valid"
    _cfgfile().write_text("{broken")
    assert T._read_config_status()[0] == "malformed"


def test_not_due_flush_still_adopts():
    """R8-2: an accepted v2 + a not-yet-due flush still adopts."""
    import time as _t
    cfg = _enabled_cfg(version=2, epoch=7)
    cfg.last_sent = _t.time(); cfg.save()
    coll = T.Collector(consent_epoch=1, schema_version=1)
    assert T.flush_if_due(T.TelemetryConfig.load(), coll,
                          poster=lambda u, p: None) is False
    assert (coll.consent_epoch, coll.schema_version) == (7, 2)  # adopted


def test_delete_during_post_never_recreates():
    cfg = _enabled_cfg(version=2, epoch=1)
    coll = T.Collector(consent_epoch=1, schema_version=2)
    coll.record("ingest", {"facts": 1})
    def poster(u, p):
        os.remove(_cfgfile())  # deleted mid-POST
    assert T.flush_if_due(T.TelemetryConfig.load(), coll, poster=poster) is True
    assert not _cfgfile().exists()  # the terminal matrix: NEVER recreated


def test_blocked_poster_disable_survives_post_resume():
    """R5-1: POST stalls → disable persists → POST resumes → the disable is
    durable and last_sent lands on the CURRENT (disabled) file."""
    cfg = _enabled_cfg(version=2, epoch=1)
    coll = T.Collector(consent_epoch=1, schema_version=2)
    coll.record("ingest", {"facts": 1})
    def poster(u, p):
        T.set_enabled(False)  # the disable lands while the POST is in flight
    assert T.flush_if_due(T.TelemetryConfig.load(), coll, poster=poster) is True
    after = T.TelemetryConfig.load()
    assert after.enabled is False  # durable — never overwritten by stale save


def test_preview_matrix_total(monkeypatch):
    """R9-3: every preview status × enabled cell."""
    coll = T.Collector(consent_epoch=1, schema_version=2)
    # absent
    assert T.preview(T.TelemetryConfig(), coll) is None
    # malformed
    _cfgfile().parent.mkdir(parents=True, exist_ok=True)
    _cfgfile().write_text("{bad")
    assert T.preview(T.TelemetryConfig(), T.Collector(1, 2)) is None
    # disabled
    _write({"enabled": False, "install_id": "i", "schema_version": 2,
            "consent_epoch": 1})
    assert T.preview(T.TelemetryConfig.load(), T.Collector(1, 2)) is None
    # valid+enabled, NOT due, NO endpoint → still a payload; never POSTs
    import time as _t
    _write({"enabled": True, "install_id": "i", "schema_version": 2,
            "consent_epoch": 1, "last_sent": _t.time(), "endpoint": None})
    c = T.Collector(consent_epoch=1, schema_version=2)
    c.record("ingest", {"facts": 1})
    p = T.preview(T.TelemetryConfig.load(), c)
    assert p is not None and p["events"]["ingest"]["sums"]["facts"] == 1.0
    # lock failure
    monkeypatch.setattr(T, "_acquire_lock", lambda *a, **k: None)
    assert T.preview(T.TelemetryConfig.load(), c) is None
