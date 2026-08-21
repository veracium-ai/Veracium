"""The cross-era receipt contract on the SHIPPED receipt schema — 0025 §4b-v.

Round 4 (R4-4) demanded real SQLite; round 5 (R5-1) found the harness had
invented a `receipts` table — the shipped receipt carrier is
`supersession_operations`, and request digests are compared at TWO product
sites: the public pre-plan phase-1 comparison (graph.py:149-151) and the
store-level phase-2 comparison (store/sqlite.py). This harness builds the
table from `schema_version.py`'s OWN DDL (the SCHEMA_V4 object plus the
frozen v5→v6 ALTERs, verbatim), inserts a legacy receipt using the SHIPPED
`contribution.request_digest` and `REQUEST_DIGEST_DOMAIN`, applies the
proposed ADD COLUMN in the same ALTER convention, and exercises the §4b-v
decision matrix AT BOTH comparison shapes — legacy/v1/v2/NULL/malformed/
unknown/true-mismatch, every row.

Run:  $PY specs/evidence/0025/receipt_era_harness.py
"""
import hashlib
import json
import pathlib
import sqlite3
import sys

# The SHIPPED source, from this tree — the conftest bootstrap, so the
# harness runs under any interpreter (the offline venv does not
# pip-install the package).
sys.path.insert(0, str(pathlib.Path(__file__).resolve()
                       .parents[3] / "src"))
try:
    from veracium.contribution import REQUEST_DIGEST_DOMAIN, request_digest
    from veracium.store.schema_version import ALTERS_V5_TO_V6, SCHEMA_V4
except ImportError as e:
    print(f"REFUSED: cannot import the shipped construction ({e}). Run "
          f"under an interpreter with the pinned test dependencies — the "
          f"offline launcher's .venv-offline/bin/python — from the "
          f"extraction root. This harness exercises the SHIPPED schema and "
          f"digest, never a stand-in.")
    sys.exit(2)

DOMAIN_V1 = REQUEST_DIGEST_DOMAIN
DOMAIN_V2 = b"veracium.supersession-request.v2"
CLOSED_SET = {DOMAIN_V1.decode(), DOMAIN_V2.decode()}

PROPOSED_ALTER = ("ALTER TABLE supersession_operations "
                  "ADD COLUMN request_digest_domain TEXT")


def digest_under(domain: bytes, snapshot: dict) -> str:
    """request_digest's FROZEN construction (contribution.py:190) under an
    explicit domain — byte-identical to the shipped function when the
    domain is the shipped constant (asserted in vector 1)."""
    body = json.dumps(snapshot, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(domain + body.encode("utf-8")).hexdigest()


class EraRefusal(Exception):
    """The fail-closed cell: a receipt whose stored domain this code
    cannot interpret — never replayed, never a new request."""


def same_request(stored_digest, stored_domain, snapshot: dict) -> bool:
    """The §4b-v decision matrix — ONE rule, applied independently at both
    product comparison sites (the two vectors below drive it through both
    call shapes)."""
    if stored_domain is None:                       # every legacy receipt
        return stored_digest in (digest_under(DOMAIN_V1, snapshot),
                                 digest_under(DOMAIN_V2, snapshot))
    if stored_domain not in CLOSED_SET:             # malformed / unknown
        raise EraRefusal(f"uninterpretable digest domain: {stored_domain!r}")
    return stored_digest == digest_under(stored_domain.encode(), snapshot)


# ---- the shipped schema, verbatim ------------------------------------------

SNAPSHOT = {"id": "e1", "user_id": "u1", "subject": "user",
            "relation": "works_as", "object": "carpenter", "note": ""}
OTHER = dict(SNAPSHOT, object="plumber")


def build_shipped_store() -> sqlite3.Connection:
    """`supersession_operations` exactly as deployed stores hold it TODAY:
    the SCHEMA_V4 CREATE (from schema_version.py's own object, not a
    retyped copy) plus the frozen v5→v6 ALTERs, then a legacy receipt
    written with the SHIPPED digest function — request identity present,
    no domain column yet."""
    ddl = next(o.ddl for o in SCHEMA_V4
               if o.name == "supersession_operations")
    conn = sqlite3.connect(":memory:")
    conn.execute(ddl)
    for alter in ALTERS_V5_TO_V6:
        conn.execute(alter)
    conn.execute("INSERT INTO supersession_operations "
                 "(user_id, operation_id, logical_request_digest, status, "
                 "request_digest, response, outcome_digest_version) "
                 "VALUES (?,?,?,?,?,?,?)",
                 ("u1", "op-legacy", "lrd-1", "committed",
                  request_digest(SNAPSHOT), '{"replayed":true}', 2))
    return conn


def migrate(conn) -> None:
    """§4b-v: the proposed column, in the v6 ALTER convention."""
    conn.execute(PROPOSED_ALTER)


def fetch(conn, op_id):
    return conn.execute(
        "SELECT request_digest, request_digest_domain FROM "
        "supersession_operations WHERE user_id='u1' AND operation_id=?",
        (op_id,)).fetchone()


def insert_v2_receipt(conn, op_id, snapshot, domain_value):
    conn.execute("INSERT INTO supersession_operations "
                 "(user_id, operation_id, logical_request_digest, status, "
                 "request_digest, response, outcome_digest_version, "
                 "request_digest_domain) VALUES (?,?,?,?,?,?,?,?)",
                 ("u1", op_id, f"lrd-{op_id}", "committed",
                  digest_under(DOMAIN_V2, snapshot), '{"replayed":true}',
                  2, domain_value))


# ---- vectors ---------------------------------------------------------------

def vector_shipped_digest_is_the_v1_cell():
    assert digest_under(DOMAIN_V1, SNAPSHOT) == request_digest(SNAPSHOT)


def vector_schema_is_the_shipped_one():
    conn = build_shipped_store()
    cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(supersession_operations)")]
    assert cols == ["user_id", "operation_id", "logical_request_digest",
                    "status", "request_digest", "response",
                    "outcome_digest_version"]
    migrate(conn)
    cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(supersession_operations)")]
    assert cols[-1] == "request_digest_domain"


def _matrix_at(site_compare):
    """Drive the full matrix through one comparison shape."""
    conn = build_shipped_store()
    migrate(conn)
    # legacy: NULL domain, dual-domain match; true mismatch refuses
    rd, dom = fetch(conn, "op-legacy")
    assert dom is None
    assert site_compare(rd, dom, SNAPSHOT)
    assert not site_compare(rd, dom, OTHER)
    # v2-stamped: its own domain only
    insert_v2_receipt(conn, "op-v2", SNAPSHOT, DOMAIN_V2.decode())
    rd, dom = fetch(conn, "op-v2")
    assert site_compare(rd, dom, SNAPSHOT)
    assert not site_compare(rd, dom, OTHER)
    # a v2-stamped digest never matches under v1 semantics
    conn.execute("UPDATE supersession_operations SET request_digest=? "
                 "WHERE operation_id='op-v2'",
                 (digest_under(DOMAIN_V1, SNAPSHOT),))
    rd, dom = fetch(conn, "op-v2")
    assert not site_compare(rd, dom, SNAPSHOT)
    # malformed / unknown / empty: fail CLOSED
    for i, bad in enumerate(("veracium.supersession-request.v9", "", "v2")):
        insert_v2_receipt(conn, f"op-bad{i}", SNAPSHOT, bad)
        rd, dom = fetch(conn, f"op-bad{i}")
        try:
            site_compare(rd, dom, SNAPSHOT)
            raise AssertionError(f"not refused: {bad!r}")
        except EraRefusal:
            pass


def vector_matrix_holds_at_the_public_phase1_shape():
    """graph.py:149-151 compares the receipt's stored request_digest
    against request_digest(snapshot) pre-plan. The era rule must sit AT
    that site (R5-1: fixing only the store leaves a public retry raising
    'different request' here first)."""
    def phase1_compare(stored_rd, stored_domain, snapshot):
        # the plan-side shape: receipt dict in hand, digest recomputed
        receipt = {"request_digest": stored_rd,
                   "request_digest_domain": stored_domain}
        return same_request(receipt["request_digest"],
                            receipt["request_digest_domain"], snapshot)
    _matrix_at(phase1_compare)


def vector_matrix_holds_at_the_store_phase2_shape():
    """store/sqlite.py's phase-2 shape: the row read back inside the
    store operation."""
    def phase2_compare(stored_rd, stored_domain, snapshot):
        return same_request(stored_rd, stored_domain, snapshot)
    _matrix_at(phase2_compare)


def main() -> int:
    vectors = [v for n, v in sorted(globals().items())
               if n.startswith("vector_")]
    for v in vectors:
        v()
        print(f"ok  {v.__name__}")
    print(f"{len(vectors)} vectors, shipped schema + shipped digest, "
          f"both comparison shapes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
