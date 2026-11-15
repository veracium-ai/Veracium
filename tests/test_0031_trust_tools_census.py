"""specs/0031 §4f, round 2's TT-R2-02 at the implementation: the trust tools' write census
(specs/evidence/0031-trust-tools/census/write_census_tools.py) is CURRENT. Its committed output, census-tools.txt, is
regenerated here on fresh stores and compared line for line, so every claim the census makes (each refusal gate writes
nothing; find_facts' one conditional wiki row; correct's committed refusal bookkeeping; the erase's store_changed
refusal writing nothing) is re-measured at every commit, never a figure frozen at one."""
import contextlib
import importlib.util
import io
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CENSUS = ROOT / "specs" / "evidence" / "0031-trust-tools" / "census"


def _module():
    spec = importlib.util.spec_from_file_location("veracium_0031_tool_census", CENSUS / "write_census_tools.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_the_tool_census_is_current():
    m = _module()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print(f"write census of the seven trust tools through *_report; {len(m.CASES)} cases, each on a fresh store")
        for name, fn in m.CASES:
            r = fn()
            if isinstance(r[0], tuple):
                print(f"{name}\n    first:  {m.fmt(*r[0])}\n    second: {m.fmt(*r[1])}")
            else:
                print(f"{name}\n    {m.fmt(*r)}")
    committed = (CENSUS / "census-tools.txt").read_text(encoding="utf-8").splitlines()
    assert committed[0].startswith("src tree: ")
    assert buf.getvalue().splitlines() == committed[1:]


def test_no_tool_case_raised_and_every_refusal_gate_writes_nothing():
    lines = (CENSUS / "census-tools.txt").read_text(encoding="utf-8").splitlines()
    assert not [ln for ln in lines if "raised:" in ln]
    gate = [i for i, ln in enumerate(lines) if " / gate " in ln]
    assert len(gate) == 21                                  # 7 + 3 + 2 + 3 + 2 + 4: gates 1, 2, 3, 4, 5, 7
    for i in gate:
        assert lines[i + 1].strip().startswith("refused:") and lines[i + 1].rstrip().endswith("no writes"), lines[i:i + 2]
