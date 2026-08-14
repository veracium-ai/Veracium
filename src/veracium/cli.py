"""`veracium` command line — manage opt-in anonymous telemetry and run the
behavioral self-check.

    veracium recall --user X                 # proactive session-start briefing (store-only)
    veracium recall --user X "the query"     # query-matched recall (store-only, cached wiki)
    veracium remember --user X "event text"  # ingest one event ('-' reads stdin; needs provider)
    veracium introspect --user X             # transparency view: what is stored + where it came from

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
        mem = Memory(llm=llm, config=MemoryConfig(db_path=args.db))
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
                                     wiki_recompile_after_writes=10**9 if has_wiki else 0))
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
    """The operator-facing wrapper around the store's offline migration
    (specs/0013 §5b). Deliberately UNGUARDED: every behaviour — version
    resolution, the accepted-manifest gate, refusal reasons, audit events —
    lives in `migrate_store`; this verb only finds the file, calls it, and
    reports the structured result honestly (label + resulting version +
    whether anything changed), never inferring facts from the label."""
    import sys
    if not os.path.exists(args.db):
        print(f"no store at {args.db!r} — nothing to migrate", file=sys.stderr)
        return 2
    from .store.migration import migrate_store
    from .store.schema_version import StoreVersionError
    try:
        r = migrate_store(args.db)
    except StoreVersionError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    if r.store_changed:
        print(f"migrated {args.db} -> schema v{r.resulting_version} "
              f"(committed: {r.transaction_committed})")
    else:
        print(f"{args.db} is already current (schema v{r.resulting_version}) — "
              f"no change")
    return 0


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
        help="migrate a below-head store forward to the current schema version "
             "(OFFLINE — quiesce all other access first; safe to run on a "
             "current store, which is a no-op)")
    mg.add_argument("--db", default="veracium.db",
                    help="SQLite store path (default: veracium.db)")

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
    rm.add_argument("--author", default="user", choices=["user", "third_party", "system"],
                    help="who authored the evidence (third_party quarantines its claims)")
    rm.add_argument("--event-type", default="chat", help="event type (chat, email, document, ...)")
    rm.add_argument("--date", default=None, help="ISO date the event occurred (default: today)")
    rm.add_argument("--derived-from", default=None, choices=["user", "third_party", "system"],
                    help="lowest-trust party whose content the event embeds (caps trust)")
    rm.add_argument("--db", default="veracium.db", help="SQLite store path (default: veracium.db)")

    it = sub.add_parser("introspect", help="the transparency view: what is stored for a user "
                                           "and where it came from — store-only")
    it.add_argument("--user", required=True, help="user id to report on")
    it.add_argument("--categories", action="store_true",
                    help="include the facts themselves, grouped by relation")
    it.add_argument("--json", action="store_true", help="machine-readable report")
    it.add_argument("--db", default="veracium.db", help="SQLite store path (default: veracium.db)")

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
