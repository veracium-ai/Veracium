"""The cross-era receipt contract on a REAL SQLite store — 0025 §4b-v.

External round 4, R4-4: the v5 reference vector used invented domains, a
different digest construction, and a Python dict for storage — a lossy
stand-in that cannot establish a durable contract. This harness uses the
SHIPPED digest construction and domain constant (`veracium.contribution`),
a real receipts table, a legacy row inserted under the PRE-migration
schema, the actual `ALTER TABLE ... ADD COLUMN` migration, and the total
§4b-v decision matrix — including the fail-closed malformed/unknown cell.

Run:  $PY specs/evidence/0025/receipt_era_harness.py
      (requires the product importable — it IS the point; refuses with a
       named message otherwise)
"""
import json
import sqlite3
import sys

try:
    from veracium.contribution import REQUEST_DIGEST_DOMAIN, request_digest
except ImportError:
    print("REFUSED: veracium not importable — this harness exists to "
          "exercise the SHIPPED digest construction, not a stand-in")
    sys.exit(2)

# the v2 domain: same construction, the None-omission serialization era.
# §4b-v pins the closed set; the v1 member must BE the shipped constant.
DOMAIN_V1 = REQUEST_DIGEST_DOMAIN
DOMAIN_V2 = b"veracium.supersession-request.v2"
CLOSED_SET = {DOMAIN_V1.decode(), DOMAIN_V2.decode()}

import hashlib


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


def same_request(row: tuple, snapshot: dict) -> bool:
    """The §4b-v decision matrix over a (request_digest,
    request_digest_domain) receipt row."""
    stored_digest, stored_domain = row
    if stored_domain is None:                       # every legacy receipt
        return stored_digest in (digest_under(DOMAIN_V1, snapshot),
                                 digest_under(DOMAIN_V2, snapshot))
    if stored_domain not in CLOSED_SET:             # malformed / unknown
        raise EraRefusal(f"uninterpretable digest domain: {stored_domain!r}")
    return stored_digest == digest_under(stored_domain.encode(), snapshot)


# ---------------------------------------------------------------------------

SNAPSHOT = {"id": "e1", "user_id": "u1", "subject": "user",
            "relation": "works_as", "object": "carpenter", "note": ""}
OTHER = dict(SNAPSHOT, object="plumber")


def build_legacy_store() -> sqlite3.Connection:
    """The PRE-amendment schema: request_digest only, no domain column —
    exactly what every deployed store holds today."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE receipts (correlation_id TEXT NOT NULL, "
                 "request_digest TEXT NOT NULL)")
    conn.execute("INSERT INTO receipts VALUES (?, ?)",
                 ("corr-1", request_digest(SNAPSHOT)))   # the SHIPPED fn
    return conn


def migrate(conn) -> None:
    """§4b-v: the migration IS the DDL line — nullable, no rewrite."""
    conn.execute("ALTER TABLE receipts ADD COLUMN request_digest_domain "
                 "TEXT NULL")


def fetch(conn, corr):
    return conn.execute("SELECT request_digest, request_digest_domain "
                        "FROM receipts WHERE correlation_id=?",
                        (corr,)).fetchone()


def vector_shipped_digest_is_the_v1_cell():
    assert digest_under(DOMAIN_V1, SNAPSHOT) == request_digest(SNAPSHOT)


def vector_legacy_receipt_replays_across_the_era():
    conn = build_legacy_store()
    migrate(conn)
    row = fetch(conn, "corr-1")
    assert row[1] is None                       # migration invented nothing
    assert same_request(row, SNAPSHOT)          # the lost-response retry
    assert not same_request(row, OTHER)         # true mismatch still refuses


def vector_new_receipts_stamp_and_compare_their_own_domain():
    conn = build_legacy_store()
    migrate(conn)
    conn.execute("INSERT INTO receipts VALUES (?, ?, ?)",
                 ("corr-2", digest_under(DOMAIN_V2, SNAPSHOT),
                  DOMAIN_V2.decode()))
    row = fetch(conn, "corr-2")
    assert same_request(row, SNAPSHOT)
    assert not same_request(row, OTHER)
    # a v2-stamped receipt is NOT matched under v1 semantics: the stored
    # domain picks exactly one comparison
    conn.execute("INSERT INTO receipts VALUES (?, ?, ?)",
                 ("corr-3", digest_under(DOMAIN_V1, SNAPSHOT),
                  DOMAIN_V2.decode()))
    assert not same_request(fetch(conn, "corr-3"), SNAPSHOT)


def vector_unknown_or_malformed_domain_fails_closed():
    conn = build_legacy_store()
    migrate(conn)
    for bad in ("veracium.supersession-request.v9", "", "garbage"):
        conn.execute("INSERT INTO receipts VALUES (?, ?, ?)",
                     (f"corr-{bad or 'empty'}",
                      digest_under(DOMAIN_V2, SNAPSHOT), bad))
        try:
            same_request(fetch(conn, f"corr-{bad or 'empty'}"), SNAPSHOT)
            raise AssertionError(f"not refused: {bad!r}")
        except EraRefusal:
            pass                                # named refusal, no guess


def main() -> int:
    vectors = [v for n, v in sorted(globals().items())
               if n.startswith("vector_")]
    for v in vectors:
        v()
        print(f"ok  {v.__name__}")
    print(f"{len(vectors)} vectors, real SQLite, shipped digest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
