"""`veracium` command line — manage opt-in anonymous telemetry and run the
behavioral self-check.

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

from . import diagnostics, telemetry


def _status(cfg) -> None:
    print(json.dumps({"enabled": cfg.enabled, "install_id": cfg.install_id or None,
                      "endpoint": cfg.endpoint, "interval_days": cfg.interval_days,
                      "last_sent": cfg.last_sent}, indent=2))


def _build_llm():
    """The reference provider for CLI-driven checks. A host embedding veracium with
    its own model runs `Memory.self_check()` directly instead."""
    try:
        from .llm.anthropic import AnthropicComplete
    except Exception as e:
        raise SystemExit(
            "veracium selfcheck needs a model provider: pip install veracium[anthropic] "
            f"and set ANTHROPIC_API_KEY. ({e})")
    return AnthropicComplete()


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

    args = p.parse_args(argv)
    if args.cmd == "selfcheck":
        return _selfcheck(args)
    if args.cmd == "diagnostics":
        return _diagnostics(args, d)
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
        cfg = telemetry.set_enabled(True, endpoint=args.endpoint)
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
