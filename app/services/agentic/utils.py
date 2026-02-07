import hashlib
import re
import uuid
from datetime import datetime, timezone

US_STATE_NAME_TO_CODE = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
    "american samoa": "AS",
    "guam": "GU",
    "northern mariana islands": "MP",
    "puerto rico": "PR",
    "us virgin islands": "VI",
    "u s virgin islands": "VI",
    "virgin islands": "VI",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_us_state_code(state: str | None) -> str | None:
    if not state:
        return None

    cleaned = re.sub(r"[^a-zA-Z\s]", " ", state).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return None

    if re.fullmatch(r"[A-Za-z]{2}", cleaned):
        return cleaned.upper()

    return US_STATE_NAME_TO_CODE.get(cleaned.lower())


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
    state_part = normalize_us_state_code(state) or _clean(state or "").upper()
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
