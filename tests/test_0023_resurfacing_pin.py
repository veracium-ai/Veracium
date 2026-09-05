"""The resurfacing cells' manifest pin (specs/evidence/0023/resurfacing_cells_pin.json)
is REGENERATED from the shipped surface and compared for equality — the
registered expectations of research's R1-R4 draft cannot drift silently.
Each cell's registered expectation is also asserted by name, so a pin that
was regenerated to a WRONG surface fails on the expectation, not only on
the diff."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs" / "evidence" / "0023"))
PIN = ROOT / "specs" / "evidence" / "0023" / "resurfacing_cells_pin.json"


def test_the_pin_equals_the_regenerated_observation():
    import resurfacing_cells
    fresh = json.loads(json.dumps(resurfacing_cells.observe(), sort_keys=True))
    pinned = json.loads(PIN.read_text())
    assert fresh == pinned, "the shipped surface drifted from the pinned observations — regenerate deliberately and say so"


def test_the_registered_expectations_hold():
    c = json.loads(PIN.read_text())["cells"]
    r1 = c["R1"]["stored"]
    assert all(e["disclosure"] == "quarantined" and not e["assertable"] for e in r1["edges"] + r1["episodes"])
    assert r1["report"]["quarantined_at_birth"] >= 1 and c["R1"]["digest_matches_source"]
    assert not c["R1"]["consequence"]["value_in_grounded"]
    r2 = c["R2"]["stored"]
    # the invariant, not the exact disclosure: never mentionable, never
    # assertable (a live extractor may route the text to third_party_claim,
    # which the relation leg quarantines — still inside the invariant)
    assert all(e["disclosure"] in ("use_only", "quarantined") and not e["assertable"]
               for e in r2["edges"] + r2["episodes"])
    assert all(e["disclosure"] != "mentionable" for e in r2["edges"] + r2["episodes"])
    assert r2["report"]["quarantined_at_birth"] == 0 and not r2["report"]["birth_revocation_digest_present"]
    assert not c["R2"]["consequence"]["value_in_grounded"] and c["R2"]["consequence"]["value_in_unverified"]
    assert c["R2"]["statement"]["counts"]["class-c-unattributed"] == 2 and c["R2"]["statement"]["complete"] is False
    r3 = c["R3"]
    by_obj = {e["object"]: e for e in r3["stored"]["edges"]}
    assert by_obj["Braga"]["disclosure"] == "quarantined"          # identified half: the birth floor
    assert by_obj["carpenter"]["disclosure"] in ("use_only", "quarantined")  # stripped half: never mentionable
    assert not by_obj["carpenter"]["assertable"]
    assert r3["report_identified"]["quarantined_at_birth"] == 1 and r3["report_identified"]["digest_matches_source"]
    assert r3["statement"]["counts"]["class-c-unattributed"] == 2 and r3["statement"]["complete"] is False
    assert not r3["consequence"]["Braga"]["value_in_grounded"] and not r3["consequence"]["carpenter"]["value_in_grounded"]
    r4 = c["R4"]["stored_after_lift"]
    assert all(e["disclosure"] == "quarantined" and not e["assertable"] for e in r4["edges"] + r4["episodes"])
    assert not c["R4"]["consequence_after_lift"]["value_in_grounded"]
