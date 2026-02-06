from app.services.agentic.utils import (
    build_evidence_hash,
    build_stable_property_key,
    normalize_address,
)


def test_normalize_address_deterministic():
    a = normalize_address("123 Main St.", city="Newark", state="nj", zip_code="07102")
    b = normalize_address(" 123 MAIN st ", city="newark", state="NJ", zip_code="07102")
    assert a == b


def test_stable_property_key_idempotent():
    k1 = build_stable_property_key("123 Main St", city="Newark", state="NJ", zip_code="07102", apn="001-ABC")
    k2 = build_stable_property_key("123 Main St", city="Newark", state="NJ", zip_code="07102", apn="001-ABC")
    assert k1 == k2


def test_evidence_hash_deterministic():
    h1 = build_evidence_hash(
        category="comps_sales",
        claim="Selected sales comp at 1 Main St",
        source_url="internal://properties/1",
        raw_excerpt="sale_price=500000",
    )
    h2 = build_evidence_hash(
        category="comps_sales",
        claim="Selected sales comp at 1 Main St",
        source_url="internal://properties/1",
        raw_excerpt="sale_price=500000",
    )
    assert h1 == h2
