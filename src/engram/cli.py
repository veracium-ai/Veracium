"""`engram` command line — manage opt-in anonymous telemetry and run the
behavioral self-check.

    engram telemetry status        # show current setting
    engram telemetry prompt        # run the consent question (first-run)
    engram telemetry enable [--endpoint URL]
    engram telemetry disable
    engram telemetry preview       # show the (content-free) payload schema

    engram selfcheck               # run the load-bearing guarantees, print a scorecard
    engram selfcheck --json        # machine-readable result
    engram selfcheck --push        # also record + flush the content-free scores (if opted in)
"""

from __future__ import annotations

import argparse
import json

from . import telemetry


def _status(cfg) -> None:
    print(json.dumps({"enabled": cfg.enabled, "install_id": cfg.install_id or None,
                      "endpoint": cfg.endpoint, "interval_days": cfg.interval_days,
                      "last_sent": cfg.last_sent}, indent=2))


def _build_llm():
    """The reference provider for CLI-driven checks. A host embedding engram with
    its own model runs `Memory.self_check()` directly instead."""
    try:
        from .llm.anthropic import AnthropicComplete
    except Exception as e:
        raise SystemExit(
            "engram selfcheck needs a model provider: pip install engram[anthropic] "
            f"and set ANTHROPIC_API_KEY. ({e})")
    return AnthropicComplete()


def _selfcheck(args) -> int:
    from . import selfcheck
    result = selfcheck.run(_build_llm())
    if args.push:
        # record the content-free scores and push them (own ephemeral collector, so
        # a weekly `engram selfcheck --push` cron folds self-check into telemetry).
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


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="engram")
    sub = p.add_subparsers(dest="cmd")
    t = sub.add_parser("telemetry", help="manage anonymous, content-free usage statistics (opt-in, default off)")
    ts = t.add_subparsers(dest="tcmd")
    ts.add_parser("status", help="show the current telemetry setting")
    ts.add_parser("prompt", help="run the first-run consent question")
    en = ts.add_parser("enable", help="opt in")
    en.add_argument("--endpoint", help="where aggregates are sent (required for sending)")
    ts.add_parser("disable", help="opt out")
    ts.add_parser("preview", help="show exactly what would be sent")

    sc = sub.add_parser("selfcheck", help="run engram's load-bearing guarantees and score them")
    sc.add_argument("--json", action="store_true", help="print the machine-readable result")
    sc.add_argument("--push", action="store_true",
                    help="record the content-free scores and flush if telemetry is enabled and due")

    args = p.parse_args(argv)
    if args.cmd == "selfcheck":
        return _selfcheck(args)
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
