"""specs/0016 D1 — the SourceType deprecation surface (I2, the seven-row matrix).

D1 warns without behaviour change: every supported access path warns or is
enumerated in the notice; internal imports bind `_SourceType`, so ordinary
library import and operation are WARNING-FREE. D2 (removal, FORMAT 6,
SCHEMA v7) executes only through accepted 0018 in the next API-breaking
release."""
import json
import os
import pickle
import typing
import warnings

import pytest

from veracium import Memory, MemoryConfig
from veracium.schema import Provenance, _SourceType


def _caught(fn):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = fn()
    deps = [x for x in w if issubclass(x.category, DeprecationWarning)
            and "source" in str(x.message).lower()]
    return result, deps


# -- the seven-row access matrix ------------------------------------------------------
def test_sourcetype_import_warns_at_d1():
    import veracium
    import veracium.schema as schema

    # row 1: package attribute access
    st, deps = _caught(lambda: veracium.SourceType)
    assert st is _SourceType and len(deps) == 1

    # row 2: from veracium import SourceType — CPython's from-import probes
    # the attribute twice (_handle_fromlist hasattr + IMPORT_FROM getattr),
    # so the row asserts "warns" (>=1), not an interpreter-detail count
    def row2():
        from veracium import SourceType
        return SourceType
    st, deps = _caught(row2)
    assert st is _SourceType and len(deps) >= 1

    # row 3: schema attribute access
    st, deps = _caught(lambda: schema.SourceType)
    assert st is _SourceType and len(deps) == 1

    # row 4: from veracium.schema import SourceType (same from-import double)
    def row4():
        from veracium.schema import SourceType
        return SourceType
    st, deps = _caught(row4)
    assert st is _SourceType and len(deps) >= 1

    # row 5: star import — PEP 562 through the DEFINED __all__
    def row5():
        ns: dict = {}
        exec("from veracium.schema import *", ns)
        return ns
    ns, deps = _caught(row5)
    assert ns["SourceType"] is _SourceType and len(deps) == 1

    # row 6: field access warns (Field(deprecated=...), pydantic>=2.7 floor)
    prov = Provenance(source_type=_SourceType.STATED,
                      author_of_evidence="user", evidence_ref="e-1")
    _, deps = _caught(lambda: prov.source_type)
    assert len(deps) == 1

    # row 7: get_type_hints resolves to the IDENTICAL class, no NameError,
    # and cannot warn (annotation resolution bypasses module __getattr__) —
    # enumerated in the notice, not silent
    hints, deps = _caught(lambda: typing.get_type_hints(Provenance))
    assert hints["source_type"] is _SourceType
    assert deps == []
    assert "model_fields" in schema._SOURCETYPE_DEPRECATION or \
           "get_type_hints" in schema._SOURCETYPE_DEPRECATION


def test_construction_and_dump_do_not_warn():
    def build_and_dump():
        prov = Provenance(source_type=_SourceType.STATED,
                          author_of_evidence="user", evidence_ref="e-1")
        return prov.model_dump()
    dumped, deps = _caught(build_and_dump)
    assert dumped["source_type"] == "stated"
    assert deps == [], "construction and dump must not warn — access does"


def test_star_import_namespace_is_byte_identical():
    """The 42-name pre-D1 star-import namespace, preserved exactly."""
    ns: dict = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec("from veracium.schema import *", ns)
    got = sorted(n for n in ns if not n.startswith("_"))
    import veracium.schema as schema
    assert got == sorted(schema.__all__)
    assert len(got) == 42
    assert "SourceType" in got


def test_dir_surfaces_include_sourcetype():
    import veracium
    import veracium.schema as schema
    assert "SourceType" in dir(schema)
    assert "SourceType" in dir(veracium)


def test_pickle_roundtrip_emits_exactly_two_warnings():
    """Members pickle by module+public-name; dump and load EACH route
    through the lazy lookup — exactly TWO warnings per round-trip."""
    member = _SourceType.STATED

    def roundtrip():
        blob = pickle.dumps(member)
        return pickle.loads(blob)
    back, deps = _caught(roundtrip)
    assert back is _SourceType.STATED
    assert len(deps) == 2, [str(d.message)[:60] for d in deps]


def test_ordinary_operation_emits_no_deprecation_warning(tmp_path):
    """Internal imports bind the private name; internal comparisons use
    model dumps — a full operation cycle emits ZERO SourceType warnings."""
    class Fake:
        def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
            if role == "distill":
                return json.dumps({"triples": [{"subject": "user",
                                                "relation": "works_as",
                                                "object": "chef"}],
                                   "episode": "User is a chef."})
            return "ok"

    def cycle():
        mem = Memory(llm=Fake(),
                     config=MemoryConfig(db_path=str(tmp_path / "d1.db"),
                                         wiki_recompile_after_writes=0))
        mem.remember("u", "USER: I'm a chef.", date="2026-06-01")
        mem.recall("u", "job?")
        mem.answer("u", "job?")
        mem.maintain("u")
        mem.introspect("u")
        mem.export_memory("u", str(tmp_path / "e.jsonl"))
        mem.close()
    _, deps = _caught(cycle)
    assert deps == [], [str(d.message)[:80] for d in deps]


def test_behaviour_is_unchanged_at_d1(tmp_path):
    """D1 is warning-only: the field is still constructed, stored, exported,
    compared — the I1 narrowed sense."""
    prov = Provenance(source_type=_SourceType.STATED,
                      author_of_evidence="user", evidence_ref="e-1")
    assert prov.model_dump()["source_type"] == "stated"
    rt = Provenance.model_validate(prov.model_dump())
    assert rt.model_dump() == prov.model_dump()


def test_field_access_warns_at_pinned_floor():
    """R6-4: runs in the DEDICATED minimum-dependency CI job and asserts the
    installed version, so it cannot silently pass elsewhere."""
    if os.environ.get("VERACIUM_MIN_DEP_JOB") != "1":
        pytest.skip("VERACIUM_MIN_DEP_JOB not set — runs only in the "
                    "pydantic==2.7.0 minimum-dependency CI job")
    import pydantic
    assert pydantic.VERSION == "2.7.0", (
        f"the min-dep job must install the exact floor; got {pydantic.VERSION}")
    prov = Provenance(source_type=_SourceType.STATED,
                      author_of_evidence="user", evidence_ref="e-1")
    _, deps = _caught(lambda: prov.source_type)
    assert len(deps) == 1, "Field(deprecated=...) must warn at the pinned floor"
