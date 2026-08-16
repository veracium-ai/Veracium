"""specs/0016 D2 — the D1 deprecation surface, RESOLVED BY REMOVAL.

This file carried the D1 seven-row warning matrix (I2). D2 deletes the field
and the public name, so every D1 row now resolves the same way: the name is
GONE on every supported access path, the field is absent from the model, and
ordinary operation needs no deprecation machinery at all. The era boundary,
digest collapse, and FORMAT 7 tests live in test_0016_d2_deletion.py."""
import json
import warnings

import pytest

from veracium import Memory, MemoryConfig
from veracium.schema import Provenance


# -- the seven D1 access rows, each now a removal ------------------------------
def test_sourcetype_name_is_gone_on_every_access_path():
    import veracium
    import veracium.schema as schema

    # rows 1+3: package / schema attribute access → AttributeError
    with pytest.raises(AttributeError):
        veracium.SourceType
    with pytest.raises(AttributeError):
        schema.SourceType

    # rows 2+4: from-imports → ImportError
    with pytest.raises(ImportError):
        exec("from veracium import SourceType", {})
    with pytest.raises(ImportError):
        exec("from veracium.schema import SourceType", {})

    # row 5: star import — the pinned namespace no longer carries the name
    ns: dict = {}
    exec("from veracium.schema import *", ns)
    assert "SourceType" not in ns

    # rows 6+7: the field is gone from the model — attribute, model_fields,
    # and annotations alike
    assert "source_type" not in Provenance.model_fields
    prov = Provenance(author_of_evidence="user", evidence_ref="e-1")
    with pytest.raises(AttributeError):
        prov.source_type

    # and the D1 private alias + notice text were removed with the bridge
    assert not hasattr(schema, "_SourceType")
    assert not hasattr(schema, "_SOURCETYPE_DEPRECATION")


def test_star_import_namespace_is_the_post_deletion_pin():
    """The star-import pin, moved: 42 names at D1 (41 + the lazy enum) → 41
    at D2. __all__ remains the exact namespace; SourceType is not in it."""
    ns: dict = {}
    exec("from veracium.schema import *", ns)
    got = sorted(n for n in ns if not n.startswith("_"))
    import veracium.schema as schema
    assert got == sorted(schema.__all__)
    assert len(got) == 41
    assert "SourceType" not in got


def test_dir_surfaces_exclude_sourcetype():
    import veracium
    import veracium.schema as schema
    assert "SourceType" not in dir(schema)
    assert "SourceType" not in dir(veracium)


def test_construction_with_the_deleted_field_drops_it():
    """A caller still passing the historical kwarg (or validating stored JSON
    that carries the key) gets the key DROPPED — pydantic's extra=ignore, the
    §2c stored-value rule; it never lands as state."""
    p = Provenance(source_type="stated", author_of_evidence="user",
                   evidence_ref="e-1")
    assert "source_type" not in p.model_dump()
    q = Provenance.model_validate({"source_type": "observed",
                                   "author_of_evidence": "user",
                                   "evidence_ref": "e-1"})
    assert "source_type" not in q.model_dump()
    with pytest.raises(AttributeError):
        q.source_type


def test_ordinary_operation_emits_no_deprecation_warning(tmp_path):
    """Kept from D1 (still true, now trivially): a full operation cycle emits
    ZERO SourceType/source_type deprecation warnings — there is nothing left
    to warn about."""
    class Fake:
        def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
            if role == "distill":
                return json.dumps({"triples": [{"subject": "user",
                                                "relation": "works_as",
                                                "object": "chef"}],
                                   "episode": "User is a chef."})
            return "ok"

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        mem = Memory(llm=Fake(),
                     config=MemoryConfig(db_path=str(tmp_path / "d2.db"),
                                         wiki_recompile_after_writes=0))
        mem.remember("u", "USER: I'm a chef.", date="2026-06-01")
        mem.recall("u", "job?")
        mem.answer("u", "job?")
        mem.maintain("u")
        mem.introspect("u")
        mem.export_memory("u", str(tmp_path / "e.jsonl"))
        mem.close()
    deps = [x for x in w if issubclass(x.category, DeprecationWarning)
            and "source" in str(x.message).lower()]
    assert deps == [], [str(d.message)[:80] for d in deps]
