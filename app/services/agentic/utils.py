import hashlib
import re
import uuid
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_address(
    address: str,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
) -> str:
    def _clean(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9\s#-]", " ", value or "")
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
        return cleaned

    address_part = _clean(address)
    city_part = _clean(city or "")
    state_part = _clean(state or "").upper()
    zip_part = _clean(zip_code or "")

    segments = [segment for segment in [address_part, city_part, state_part, zip_part] if segment]
    return ", ".join(segments)


def build_stable_property_key(
    address: str,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    apn: str | None = None,
) -> str:
    normalized = normalize_address(address=address, city=city, state=state, zip_code=zip_code)
    material = f"{normalized}|{(apn or '').strip().lower()}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_evidence_hash(
    category: str,
    claim: str,
    source_url: str,
    raw_excerpt: str | None,
) -> str:
    material = "|".join(
        [
            category.strip().lower(),
            claim.strip().lower(),
            source_url.strip().lower(),
            (raw_excerpt or "").strip().lower(),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def new_trace_id() -> str:
    return uuid.uuid4().hex[:16]
