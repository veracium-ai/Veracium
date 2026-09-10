"""specs/0039 §6a — the MANUAL CLI exercise, driven: `veracium remember` through the
real CLI entry point (cli.main), with the reference provider replaced AT THE CLI'S
OWN SEAM (`cli._build_llm`) by a scripted provider — the CLI has no other way to be
given a provider — and XDG dirs pointed at a scratch directory so the log the CLI
writes is the one printed below. Everything else is the shipped CLI."""
# Mutation-Matrix: tests/test_0039_degradation_visibility.py::test_the_manual_cli_transcript_reproduces
import json, os, sys, pathlib
sys.path.insert(0, "specs/evidence/0039")
from answer_shapes import Stub, GOOD, OFF
from veracium import cli
state = pathlib.Path(os.environ["XDG_STATE_HOME"]) / "veracium" / "veracium.log"
def run(label, llm):
    cli._build_llm = lambda *a, **k: llm
    print(f"$ veracium remember --db {os.environ['DB']} --user alice 'I use Vim for editing.'     # provider: {label}")
    try:
        rc = cli.main(["remember", "--db", os.environ["DB"], "--user", "alice", "I use Vim for editing."])
        print(f"  (exit {rc})")
    except SystemExit as e:
        print(f"  (exit {e.code})")
run("fails the retry (raises)", Stub(json.dumps({"triples": [OFF]}), retry_raises=RuntimeError("provider unavailable")))
run("volatility vocabulary drifted", Stub(json.dumps({"triples": [dict(GOOD, volatility="long-term"), dict(GOOD, object="Emacs", volatility="sticky")]}), retry_raw="{}"))
print(f"$ cat {state}")
for line in state.read_text().splitlines():
    print("  " + line)
