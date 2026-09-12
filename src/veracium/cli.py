"""`veracium` command line — manage opt-in anonymous telemetry and run the
behavioral self-check.

    veracium recall --user X                 # proactive session-start briefing (store-only)
    veracium recall --user X "the query"     # query-matched recall (store-only, cached wiki)
    veracium remember --user X "event text"  # ingest one event ('-' reads stdin; needs provider)
    veracium remember --user X "text" --dry-run   # what WOULD be written, against a snapshot copy; nothing written
    veracium introspect --user X             # transparency view: what is stored + where it came from
    veracium why --user X <edge-id>          # one fact's biography: provenance, journal, lineage (store-only)
    veracium why --user X --find "text"      # find edge ids by subject/relation/object text
    veracium doctor [--db X] [--user U]      # read-only store linter: version, objects, rows, refs, journal, revocation

    veracium export / import / forget        # portability + compliance erasure

    veracium telemetry status        # show current setting
    veracium telemetry prompt        # run the consent question (first-run)
    veracium telemetry enable [--endpoint URL]
    veracium telemetry disable
    veracium telemetry preview       # show the (content-free) payload schema

    veracium selfcheck               # run the load-bearing guarantees, print a scorecard
    veracium selfcheck --json        # machine-readable result
    veracium selfcheck --push        # also record + flush the content-free scores (if opted in)

    veracium diagnostics status      # show error-reporting setting + log path
    veracium diagnostics prompt      # advance-permission consent for auto-send
    veracium diagnostics enable [--endpoint URL]   # grant advance permission to send logs
    veracium diagnostics disable
    veracium diagnostics preview     # show exactly what a report would send (redacted)
    veracium diagnostics report      # send the current log now (asks first)
    veracium diagnostics path        # print the local log file location
"""

from __future__ import annotations

import argparse
import json
import os

from . import diagnostics, telemetry


def _status(cfg) -> None:
    print(json.dumps({"enabled": cfg.enabled, "install_id": cfg.install_id or None,
                      "endpoint": cfg.endpoint, "interval_days": cfg.interval_days,
                      "last_sent": cfg.last_sent}, indent=2))


def _provider_help(verb: str, alternative: str) -> str:
    return (f"veracium {verb} needs an LLM provider:\n"
            "  pip install 'veracium[anthropic]'   # the reference provider\n"
            "  export ANTHROPIC_API_KEY=sk-...     # its credentials\n"
            f"or {alternative} — see https://docs.veracium.ai/api/")


_PROVIDER_HELP = _provider_help(
    "selfcheck", "run Memory.self_check() with your own Complete callable")


def _build_llm(help_text: str = _PROVIDER_HELP):
    """The reference provider for CLI-driven checks, preflighted so a missing
    SDK or key exits with one clear line instead of a traceback — or worse,
    a garbage FAIL scorecard that looks like the guarantees failing (the
    2026-07-20 launch-prep finding). A host embedding veracium with its own
    model runs `Memory.self_check()` directly instead."""
    try:
        from .llm.anthropic import AnthropicComplete
        llm = AnthropicComplete()   # constructor may lazily import the SDK
    except SystemExit:
        raise
    except Exception:
        raise SystemExit(help_text)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(help_text)
    return llm


def _no_llm(prompt, *, system=None, role="compile", json_schema=None):
    """Stub provider for store-only verbs. `_veracium_no_llm` marks it so ensure_wiki
    serves the deterministic stale-cache notice instead of recompiling when the cache is
    identity-stale (specs/0012 I10l) — this stub can then never fire; raising loudly
    beats silently degrading if a future path regresses that."""
    raise SystemExit("internal: this veracium verb should never invoke the LLM "
                     "— please report this at github.com/veracium-ai/Veracium/issues")


_no_llm._veracium_no_llm = True


def _selfcheck(args) -> int:
    from . import selfcheck
    result = selfcheck.run(_build_llm())
    if args.push:
        # record the content-free scores and push them (own ephemeral collector, so
        # a weekly `veracium selfcheck --push` cron folds self-check into telemetry).
        cfg = telemetry.TelemetryConfig.load()
        if cfg.enabled:
            coll = telemetry.Collector()
            coll.record("selfcheck", result)  # non-scalar keys dropped by the collector
            telemetry.flush_if_due(cfg, coll)
    if args.json:
        print(json.dumps({k: v for k, v in result.items()}, indent=2))
    else:
        print(selfcheck.format_scorecard(result))
    if not result.get("ran", True):
        return 2   # environment problem — neither PASS nor FAIL
    return 0 if result["passed"] else 1


def _diagnostics(args, parser) -> int:
    cfg = diagnostics.DiagnosticsConfig.load()
    if args.dcmd == "status":
        print(json.dumps({"log_enabled": cfg.log_enabled,
                          "report_enabled (auto-send)": cfg.report_enabled,
                          "prompt_on_error": cfg.prompt_on_error,
                          "redact": cfg.redact, "endpoint": cfg.endpoint,
                          "install_id": cfg.install_id or None,
                          "log_path": str(cfg.resolved_log_path()),
                          "last_report": cfg.last_report}, indent=2))
    elif args.dcmd == "prompt":
        cfg = diagnostics.prompt_consent(interactive=True)
        print("\nAuto-send enabled." if cfg.report_enabled else "\nAuto-send left disabled.")
    elif args.dcmd == "enable":
        cfg = diagnostics.set_report_enabled(True, endpoint=args.endpoint)
        note = "" if cfg.endpoint else "  (no --endpoint set → nothing sends until one is configured)"
        print("Error-log auto-send enabled." + note)
    elif args.dcmd == "disable":
        diagnostics.set_report_enabled(False)
        print("Error-log auto-send disabled. (Local logging is unaffected.)")
    elif args.dcmd == "preview":
        print(json.dumps(diagnostics.Reporter(cfg).preview(), indent=2))
        print("\n(This is the actual log content that would be sent. Redaction is "
              f"{'on' if cfg.redact else 'OFF'}. Nothing is sent by `preview`.)")
    elif args.dcmd == "report":
        if not cfg.endpoint:
            print("No endpoint configured — set one with `veracium diagnostics enable --endpoint URL`.")
            return 1
        sent = diagnostics.Reporter(cfg).send(interactive=True, reason="manual")
        print("Sent." if sent else "Not sent.")
        return 0 if sent else 1
    elif args.dcmd == "path":
        print(cfg.resolved_log_path())
    else:
        parser.print_help()
    return 0


def _portability(args) -> int:
    from .portability import export_memory, import_memory
    from .store.sqlite import SqliteStore
    store = SqliteStore(args.db)
    try:
        if args.cmd == "export":
            r = export_memory(store, args.user, args.path)
            print(f"exported {r['edges']} edges + {r['episodes']} episodes -> {r['path']}")
        else:
            r = import_memory(store, args.path, user_id=args.user,
                              restore=args.restore)
            # specs/0005 §7a — the default-path line carries the capped count
            # (the one surface built for the operator); the restore-path line
            # says nothing about capping (capped is 0 by construction there).
            tail = "" if args.restore else f"; {r['capped']} capped to third-party trust"
            print(f"imported {r['edges']} edges + {r['episodes']} episodes into "
                  f"'{r['user_id']}' ({r['skipped']} already present, skipped{tail})")
        return 0
    finally:
        store.close()


def _memory_verbs(args) -> int:
    """recall / remember / introspect — the working verbs that make hook and
    script integrations one-liners (see examples/claude_code_hooks/).

    `recall` and `introspect` are store-only: no provider, no network. Recall
    with no QUERY is the proactive session-start briefing (LLM-free by
    design); with a QUERY it serves the *cached* wiki plus the entity-matched
    subgraph — it never recompiles the wiki (that happens on the write path).
    `remember` runs extraction, so it needs the provider."""
    from . import Memory, MemoryConfig
    if args.cmd == "remember":
        text = args.text
        if text == "-":
            import sys
            text = sys.stdin.read()
        if not text.strip():
            print("nothing to remember (empty input)")
            return 1
        from .schema import EvidenceAuthor
        llm = _build_llm(_provider_help(
            "remember", "use Memory.remember() with your own Complete callable"))
        if args.dry_run:
            from . import dryrun as _dr
            dr = _dr.run(args.db, llm, args.user, text, author=EvidenceAuthor(args.author),
                         event_type=args.event_type, date=args.date,
                         derived_from=(EvidenceAuthor(args.derived_from) if args.derived_from else None))
            if args.json:
                print(json.dumps(_dr.to_json(dr), indent=2, default=str))
            else:
                print(_dr.render(dr), end="")
            return 0 if dr.usable else 1
        # specs/0039 §2d: the CLI attaches a reporter as the MCP entry point does —
        # a Reporter iff log_enabled, so a degrade during `remember` leaves a record
        mem = Memory(llm=llm, config=MemoryConfig(db_path=args.db),
                     diagnostics=diagnostics.load_reporter())
        try:
            r = mem.remember(args.user, text, author=EvidenceAuthor(args.author),
                             event_type=args.event_type, date=args.date,
                             derived_from=(EvidenceAuthor(args.derived_from)
                                           if args.derived_from else None))
            print(f"remembered: {r['facts']} facts, {r['quarantined']} quarantined "
                  f"claims for '{args.user}'")
            return 0
        finally:
            mem.close()

    # store-only verbs: serve the cached wiki if one was ever compiled (the
    # huge threshold makes it never-stale), disable the layer otherwise —
    # either way the stub provider can never fire
    from .store.sqlite import SqliteStore
    store = SqliteStore(args.db)
    has_wiki = store.get_wiki(args.user) is not None
    mem = Memory(llm=_no_llm, store=store,
                 config=MemoryConfig(db_path=args.db,
                                     wiki_recompile_after_writes=10**9 if has_wiki else 0),
                 # specs/0039 §2d: one rule for both constructions (this one can
                 # emit no degrade record — its provider never extracts — but
                 # its errors reach the same log)
                 diagnostics=diagnostics.load_reporter())
    try:
        if args.cmd == "recall":
            r = mem.recall(args.user, args.query, token_budget=args.budget)
            print(r.context)
            return 0
        out = mem.introspect(args.user,
                             mode="categories" if args.categories else "summary")
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(f"memory for '{out['user_id']}': {out['facts']} facts, "
                  f"{out['unverified_claims']} unverified claims, "
                  f"{out['episodes']['interaction']} episodes "
                  f"({out['first_known'] or 'n/a'} → {out['last_recorded'] or 'n/a'})")
            rec = out.get("wiki_compile_record") or {}
            if rec.get("status") == "ok":
                print(f"wiki compile: +{rec['facts_dropped']} facts / "
                      f"+{rec['episodes_dropped']} episodes not compiled")
            else:
                print(f"wiki compile: no compile record "
                      f"({rec.get('status', 'absent')} cache)")
            for section in ("by_relation", "by_author", "by_disclosure", "retired"):
                if out[section]:
                    print(f"  {section.replace('_', ' ')}: "
                          + ", ".join(f"{k}={v}" for k, v in out[section].items()))
            if out["needs_confirmation"]:
                print(f"  needs confirmation: {out['needs_confirmation']}")
            for rel, lines in out.get("categories", {}).items():
                print(f"\n[{rel}]")
                for line in lines:
                    print(f"  {line}")
        return 0
    finally:
        mem.close()


def _why(args) -> int:
    """`why` — a fact's biography (src/veracium/why.py). Store-only and read-only:
    no provider, no Memory, no write. Exit 0 when the edge (or a --find hit) is
    found, 1 when not, 2 on a usage error."""
    from .store.sqlite import SqliteStore
    from . import why as _w
    if bool(args.edge) == bool(args.find):
        print("usage: veracium why --user X <edge-id>  |  veracium why --user X --find TEXT")
        return 2
    store = SqliteStore(args.db)
    try:
        if args.find:
            hits = _w.find(store, args.user, args.find)
            if args.json:
                print(json.dumps(hits, indent=2))
            else:
                print(_w.render_find(args.user, args.find, hits), end="")
            return 0 if hits else 1
        bio = _w.gather(store, args.user, args.edge)
        if args.json:
            print(json.dumps(_w.to_json(bio), indent=2, default=str))
        else:
            print(_w.render(bio), end="")
        return 0 if bio.found else 1
    finally:
        store.close()


def _doctor(args) -> int:
    """`doctor` — the read-only store linter (src/veracium/doctor.py). Opens the
    file with a mode=ro connection, never the store class, so a below-head or
    foreign file is reported rather than refused. Exit 0 clean, 1 findings,
    2 unreadable. Changes nothing."""
    from . import doctor as _d
    rep = _d.diagnose(args.db, user=args.user)
    if args.json:
        print(json.dumps(_d.to_json(rep), indent=2, default=str))
    else:
        print(_d.render(rep), end="")
    return rep.exit_code


def _forget(args) -> int:
    from .store.sqlite import SqliteStore
    if not args.yes:
        reply = input(f"Irreversibly erase ALL memory for '{args.user}' in {args.db}? "
                      f"There is no undo (export first if unsure). [y/N] ")
        if reply.strip().lower() not in ("y", "yes"):
            print("aborted")
            return 1
    store = SqliteStore(args.db)
    try:
        r = store.forget_user(args.user)
        print(f"erased {r['edges']} edges + {r['episodes']} episodes for '{args.user}'")
        return 0
    finally:
        store.close()


def _migrate(args) -> int:
    """The operator-facing release-migration verb (specs/0018 §4g) —
    re-dispositioned from the direct-`migrate_store` contract to the
    orchestrator. Flags, never prompts: `--i-have-quiesced` and `--backup REF`
    are the operator's explicit assertions, both required on the migration
    path. Exit codes: 0 = migrated/current · 1 = every refusal outcome ·
    2 = usage / invalid attestation · 3 = a named loud escape
    (MigrationAuditWriteError / MigrationAuditReadError /
    PackageConsistencyError). Reporting stays on the STRUCTURED result fields
    (facts are never inferred from the label, 0013 r8-f3), and every printed
    state on the escape paths is labeled recorded, derived, or unavailable."""
    import sys
    from .store import release_migration as rm
    from .store.schema_version import PackageConsistencyError
    if not args.i_have_quiesced or args.backup is None:
        print("usage: veracium migrate --db X --i-have-quiesced --backup REF\n"
              "the migration path requires BOTH flags: --i-have-quiesced (the "
              "host's explicit\nassertion that all other access to the store "
              "is stopped) and --backup REF\n(the pre-migration backup token "
              "this operation made)", file=sys.stderr)
        return 2
    if not rm.backup_token_ok(args.backup):
        print(f"invalid --backup token {args.backup!r}: must match "
              f"[A-Za-z0-9][A-Za-z0-9._+:/-]{{0,127}} "
              f"(1-128 ASCII, no whitespace)", file=sys.stderr)
        return 2
    attestation = rm.MigrationAttestation(quiesced=True, backup_ref=args.backup)
    try:
        r = rm.run_release_migration(args.db, host_attestation=attestation)
    except rm.MigrationAuditWriteError as e:
        print(f"MigrationAuditWriteError: {e}", file=sys.stderr)
        print(f"operation_id: {e.operation_id}", file=sys.stderr)
        print(f"resulting_state: {e.resulting_state} (recorded)",
              file=sys.stderr)
        print(f"store_changed: {e.store_changed}  transaction_committed: "
              f"{e.committed}  resulting_version: {e.resulting_version}  "
              f"audit_committed: {e.audit_committed}", file=sys.stderr)
        return 3
    except rm.MigrationAuditReadError as e:
        print(f"MigrationAuditReadError: {e}", file=sys.stderr)
        print(f"operation_id: {e.operation_id}", file=sys.stderr)
        print(f"resulting_state: {e.derived_resulting_state} "
              f"(derived-from-outcome)", file=sys.stderr)
        return 3
    except PackageConsistencyError as e:
        # the accepted package exception itself carries no facts and the CLI
        # never invents them (0018 §4g, external R2-6/R3-5): the five routes.
        route = getattr(e, "readback_route", "pre-mint")
        print(f"PackageConsistencyError: {e}", file=sys.stderr)
        if route == "pre-mint":
            print("resulting_state: unavailable (pre-mint: no operation "
                  "minted)", file=sys.stderr)
        elif route == "recorded":
            f = e.recorded_facts
            print(f"resulting_state: {f.resulting_state} (recorded)",
                  file=sys.stderr)
            print(f"store_changed: {f.store_changed}  transaction_committed: "
                  f"{f.transaction_committed}  resulting_version: "
                  f"{f.resulting_version}", file=sys.stderr)
        else:
            print(f"resulting_state: unavailable (readback: {route})",
                  file=sys.stderr)
        return 3
    print(f"outcome: {r.outcome}")
    print(f"store_changed: {r.store_changed}  transaction_committed: "
          f"{r.transaction_committed}")
    print(f"resulting_state: {r.resulting_state}  resulting_version: "
          f"{r.resulting_version}")
    if r.diagnostic:
        print(r.diagnostic)
    return 0 if r.outcome in ("migrated", "current") else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="veracium")
    sub = p.add_subparsers(dest="cmd")
    t = sub.add_parser("telemetry", help="manage anonymous, content-free usage statistics (opt-in, default off)")
    ts = t.add_subparsers(dest="tcmd")
    ts.add_parser("status", help="show the current telemetry setting")
    ts.add_parser("prompt", help="run the first-run consent question")
    en = ts.add_parser("enable", help="opt in")
    en.add_argument("--endpoint", help="where aggregates are sent (required for sending)")
    ts.add_parser("disable", help="opt out")
    ts.add_parser("preview", help="show exactly what would be sent")

    sc = sub.add_parser("selfcheck", help="run veracium's load-bearing guarantees and score them")
    sc.add_argument("--json", action="store_true", help="print the machine-readable result")
    sc.add_argument("--push", action="store_true",
                    help="record the content-free scores and flush if telemetry is enabled and due")

    d = sub.add_parser("diagnostics", help="opt-in error reporting: local error log + consented send")
    dsub = d.add_subparsers(dest="dcmd")
    dsub.add_parser("status", help="show the current error-reporting setting")
    dsub.add_parser("prompt", help="advance-permission consent for auto-send")
    de = dsub.add_parser("enable", help="grant advance permission to auto-send logs on error")
    de.add_argument("--endpoint", help="where logs are sent (required for sending)")
    dsub.add_parser("disable", help="revoke advance permission to send")
    dsub.add_parser("preview", help="show exactly what a report would send (redacted)")
    dsub.add_parser("report", help="send the current local log now (asks first)")
    dsub.add_parser("path", help="print the local log file location")

    ex = sub.add_parser("export", help="export a user's memory to portable JSONL (full provenance)")
    ex.add_argument("path", help="output .jsonl file")
    ex.add_argument("--user", required=True, help="user id to export")
    ex.add_argument("--db", default="veracium.db", help="SQLite store path (default: veracium.db)")

    im = sub.add_parser("import", help="import a Veracium JSONL export (idempotent; never overwrites; "
                                       "DEFAULT imports cap trust — specs/0005)")
    im.add_argument("path", help="input .jsonl file")
    im_mode = im.add_mutually_exclusive_group()
    im_mode.add_argument("--user", help="remap the records into this user id (records import capped)")
    im_mode.add_argument("--restore", action="store_true",
                         help="trust the file's provenance exactly as written — ONLY for a file "
                              "you exported yourself or have independently verified; a restore "
                              "is this store's own history and never remaps (specs/0005 §4a)")
    im.add_argument("--db", default="veracium.db", help="SQLite store path (default: veracium.db)")

    mg = sub.add_parser(
        "migrate",
        help="run this release's migration on a store (OFFLINE — quiesce all "
             "other access first; safe on a current store, which is a no-op). "
             "Requires --i-have-quiesced and --backup REF. Exits 0 "
             "migrated/current, 1 refused, 2 usage, 3 audit failure (loud)")
    mg.add_argument("--db", default="veracium.db",
                    help="SQLite store path (default: veracium.db)")
    mg.add_argument("--i-have-quiesced", action="store_true",
                    help="the operator's explicit assertion that every other "
                         "process/connection using the store is stopped "
                         "(specs/0013 §5b; asserted, never prompted for)")
    mg.add_argument("--backup", metavar="REF", default=None,
                    help="reference token of the pre-migration backup this "
                         "operation made (1-128 ASCII, no whitespace)")

    fg = sub.add_parser("forget", help="irreversibly erase EVERYTHING stored for a user (compliance erasure)")
    fg.add_argument("--user", required=True, help="user id to erase")
    fg.add_argument("--db", default="veracium.db", help="SQLite store path (default: veracium.db)")
    fg.add_argument("--yes", action="store_true", help="skip the confirmation prompt")

    rc = sub.add_parser("recall", help="print memory context: session-start briefing (no QUERY) "
                                       "or query-matched recall — store-only, no provider needed")
    rc.add_argument("query", nargs="?", default=None,
                    help="what to recall; omit for the proactive briefing")
    rc.add_argument("--user", required=True, help="user id to recall for")
    rc.add_argument("--budget", type=int, default=None, help="approximate token budget for the context")
    rc.add_argument("--db", default="veracium.db", help="SQLite store path (default: veracium.db)")

    rm = sub.add_parser("remember", help="ingest one event into a user's memory (needs the provider)")
    rm.add_argument("text", help="the event text, or '-' to read stdin")
    rm.add_argument("--user", required=True, help="user id to remember for")
    rm.add_argument("--author", default="user", choices=["user", "third_party", "system", "assistant"],
                    help="who authored the evidence (third_party quarantines its claims)")
    rm.add_argument("--event-type", default="chat", help="event type (chat, email, document, ...)")
    rm.add_argument("--date", default=None, help="ISO date the event occurred (default: today)")
    rm.add_argument("--derived-from", default=None, choices=["user", "third_party", "system", "assistant"],
                    help="lowest-trust party whose content the event embeds (caps trust)")
    rm.add_argument("--dry-run", action="store_true",
                    help="run the ingest against a snapshot copy of the store and report what would be "
                         "written — facts, tiers, quarantine, supersession, degrade records; the store is "
                         "not touched (the provider is still called)")
    rm.add_argument("--json", action="store_true", help="with --dry-run: machine-readable report")
    rm.add_argument("--db", default="veracium.db", help="SQLite store path (default: veracium.db)")

    it = sub.add_parser("introspect", help="the transparency view: what is stored for a user "
                                           "and where it came from — store-only")
    it.add_argument("--user", required=True, help="user id to report on")
    it.add_argument("--categories", action="store_true",
                    help="include the facts themselves, grouped by relation")
    it.add_argument("--json", action="store_true", help="machine-readable report")
    it.add_argument("--db", default="veracium.db", help="SQLite store path (default: veracium.db)")
    wy = sub.add_parser("why", help="one fact's biography: where it came from, every recorded "
                                    "change with its reason, what superseded or absorbed it, its "
                                    "confirmations and outcomes — store-only, read-only")
    wy.add_argument("--user", required=True, help="user id the edge belongs to")
    wy.add_argument("edge", nargs="?", help="edge id (as printed by `why --find` or `export`)")
    wy.add_argument("--find", metavar="TEXT",
                    help="instead of an id: list edges whose subject, relation or object contains TEXT")
    wy.add_argument("--json", action="store_true", help="machine-readable biography")
    wy.add_argument("--db", default="veracium.db", help="SQLite store path (default: veracium.db)")
    dr = sub.add_parser("doctor", help="read-only static linter for a store file: schema version, "
                                        "required/rebuildable objects, row consistency, dangling "
                                        "references and supersession chains, unjournaled edges, "
                                        "revocation completeness — no provider, nothing changed")
    dr.add_argument("--user", help="restrict the row-level checks to one user id")
    dr.add_argument("--json", action="store_true", help="machine-readable report")
    dr.add_argument("--db", default="veracium.db", help="SQLite store path (default: veracium.db)")

    args = p.parse_args(argv)
    if args.cmd == "selfcheck":
        return _selfcheck(args)
    if args.cmd == "diagnostics":
        return _diagnostics(args, d)
    if args.cmd in ("export", "import"):
        return _portability(args)
    if args.cmd == "forget":
        return _forget(args)
    if args.cmd == "migrate":
        return _migrate(args)
    if args.cmd == "why":
        return _why(args)
    if args.cmd == "doctor":
        return _doctor(args)
    if args.cmd in ("recall", "remember", "introspect"):
        return _memory_verbs(args)
    if args.cmd != "telemetry":
        p.print_help()
        return 0

    cfg = telemetry.TelemetryConfig.load()
    if args.tcmd == "status":
        _status(cfg)
    elif args.tcmd == "prompt":
        cfg = telemetry.prompt_consent(interactive=True)
        print("\nEnabled." if cfg.enabled else "\nLeft disabled.")
        _status(cfg)
    elif args.tcmd == "enable":
        # specs/0015 I13: the CLI enable IS a display flow — the text is shown
        # and acceptance stamps the current consent version.
        print(telemetry.CONSENT_TEXT.rsplit("\n\n", 1)[0])
        cfg = telemetry.accept_current_consent(endpoint=args.endpoint)
        note = "" if cfg.endpoint else "  (no --endpoint set → nothing sends until one is configured)"
        print("Telemetry enabled." + note)
    elif args.tcmd == "disable":
        telemetry.set_enabled(False)
        print("Telemetry disabled.")
    elif args.tcmd == "preview":
        print(json.dumps(telemetry.preview(cfg, telemetry.Collector()), indent=2))
        print("\n(Live counters accumulate inside the running app; this shows the "
              "envelope + content-free schema. Nothing here is your memory content.)")
    else:
        t.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
