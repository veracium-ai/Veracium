"""`engram` command line — manage opt-in anonymous telemetry.

    engram telemetry status        # show current setting
    engram telemetry prompt        # run the consent question (first-run)
    engram telemetry enable [--endpoint URL]
    engram telemetry disable
    engram telemetry preview       # show the (content-free) payload schema
"""

from __future__ import annotations

import argparse
import json

from . import telemetry


def _status(cfg) -> None:
    print(json.dumps({"enabled": cfg.enabled, "install_id": cfg.install_id or None,
                      "endpoint": cfg.endpoint, "interval_days": cfg.interval_days,
                      "last_sent": cfg.last_sent}, indent=2))


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

    args = p.parse_args(argv)
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
