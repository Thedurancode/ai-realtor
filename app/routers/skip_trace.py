from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.rate_limit import limiter
from app.models.property import Property
from app.models.skip_trace import SkipTrace
from app.schemas.skip_trace import (
    SkipTraceRequest,
    SkipTraceByPropertyRequest,
    SkipTraceResult,
    SkipTraceVoiceResponse,
    PhoneNumber,
    Email,
)
from app.services.skip_trace import skip_trace_service

router = APIRouter(prefix="/skip-trace", tags=["skip-trace"])


def format_phone_for_voice(phone: str) -> str:
    """Format phone number for voice readability."""
    # Remove formatting and read digit by digit with pauses
    digits = "".join(filter(str.isdigit, phone))
    if len(digits) == 10:
        return f"{digits[:3]}, {digits[3:6]}, {digits[6:]}"
    return phone


def build_voice_response(result: SkipTrace, property: Property) -> SkipTraceVoiceResponse:
    """Build voice-friendly response from skip trace result."""
    phone_numbers = [PhoneNumber(**p) for p in (result.phone_numbers or [])]
    emails = [Email(**e) for e in (result.emails or [])]

    # Build voice summary
    voice_summary = f"Skip trace complete for {property.address}, {property.city}. "
    voice_summary += f"The owner is {result.owner_name}. "

    valid_phones = [p for p in phone_numbers if p.status == "valid"]
    if valid_phones:
        voice_summary += f"I found {len(valid_phones)} phone number{'s' if len(valid_phones) > 1 else ''}. "
    if emails:
        voice_summary += f"I found {len(emails)} email address{'es' if len(emails) > 1 else ''}. "

    voice_summary += "Would you like me to read the contact information?"

    # Build readable phone list
    phone_parts = []
    for i, phone in enumerate(valid_phones[:3], 1):  # Limit to 3 for voice
        formatted = format_phone_for_voice(phone.number)
        phone_parts.append(f"Phone {i}, {phone.type}: {formatted}")
    voice_phone_list = ". ".join(phone_parts) if phone_parts else "No valid phone numbers found."

    # Build readable email list
    email_parts = []
    for i, email in enumerate(emails[:2], 1):  # Limit to 2 for voice
        # Spell out email for clarity
        email_parts.append(f"Email {i}: {email.email}")
    voice_email_list = ". ".join(email_parts) if email_parts else "No email addresses found."

    return SkipTraceVoiceResponse(
        result=SkipTraceResult(
            id=result.id,
            property_id=result.property_id,
            owner_name=result.owner_name,
            owner_first_name=result.owner_first_name,
            owner_last_name=result.owner_last_name,
            phone_numbers=phone_numbers,
            emails=emails,
            mailing_address=result.mailing_address,
            mailing_city=result.mailing_city,
            mailing_state=result.mailing_state,
            mailing_zip=result.mailing_zip,
            created_at=result.created_at,
        ),
        voice_summary=voice_summary,
        voice_phone_list=voice_phone_list,
        voice_email_list=voice_email_list,
    )


@router.post("/voice", response_model=SkipTraceVoiceResponse)
@limiter.limit("5/minute")
async def skip_trace_by_address_voice(
    request: Request, body: SkipTraceRequest, db: Session = Depends(get_db)
):
    """
    Voice-optimized skip trace by address.
    User says: "skip trace 141 throop ave"
    Searches for matching property and runs skip trace.
    """
    # Search for property matching the address query
    query = body.address_query.lower()
    property = (
        db.query(Property)
        .filter(Property.address.ilike(f"%{query}%"))
        .first()
    )

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{body.address_query}'. Please add the property first.",
        )

    # Check if we already have a recent skip trace
    existing = (
        db.query(SkipTrace)
        .filter(SkipTrace.property_id == property.id)
        .order_by(SkipTrace.created_at.desc())
        .first()
    )

    if existing:
        return build_voice_response(existing, property)

    # Run skip trace
    result = await skip_trace_service.skip_trace(
        address=property.address,
        city=property.city,
        state=property.state,
        zip_code=property.zip_code,
    )

    # Save result
    skip_trace = SkipTrace(
        property_id=property.id,
        owner_name=result["owner_name"],
        owner_first_name=result["owner_first_name"],
        owner_last_name=result["owner_last_name"],
        phone_numbers=result["phone_numbers"],
        emails=result["emails"],
        mailing_address=result["mailing_address"],
        mailing_city=result["mailing_city"],
        mailing_state=result["mailing_state"],
        mailing_zip=result["mailing_zip"],
        raw_response=result["raw_response"],
    )
    db.add(skip_trace)
    db.commit()
    db.refresh(skip_trace)

    return build_voice_response(skip_trace, property)


@router.post("/property/{property_id}", response_model=SkipTraceVoiceResponse)
@limiter.limit("5/minute")
async def skip_trace_by_property_id(
    request: Request, property_id: int, db: Session = Depends(get_db)
):
    """
    Run skip trace on a property by ID.
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check for existing skip trace
    existing = (
        db.query(SkipTrace)
        .filter(SkipTrace.property_id == property.id)
        .order_by(SkipTrace.created_at.desc())
        .first()
    )

    if existing:
        return build_voice_response(existing, property)

    # Run skip trace
    result = await skip_trace_service.skip_trace(
        address=property.address,
        city=property.city,
        state=property.state,
        zip_code=property.zip_code,
    )

    # Save result
    skip_trace = SkipTrace(
        property_id=property.id,
        owner_name=result["owner_name"],
        owner_first_name=result["owner_first_name"],
        owner_last_name=result["owner_last_name"],
        phone_numbers=result["phone_numbers"],
        emails=result["emails"],
        mailing_address=result["mailing_address"],
        mailing_city=result["mailing_city"],
        mailing_state=result["mailing_state"],
        mailing_zip=result["mailing_zip"],
        raw_response=result["raw_response"],
    )
    db.add(skip_trace)
    db.commit()
    db.refresh(skip_trace)

    return build_voice_response(skip_trace, property)


@router.get("/property/{property_id}", response_model=SkipTraceVoiceResponse)
def get_skip_trace_for_property(property_id: int, db: Session = Depends(get_db)):
    """
    Get existing skip trace results for a property.
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    skip_trace = (
        db.query(SkipTrace)
        .filter(SkipTrace.property_id == property_id)
        .order_by(SkipTrace.created_at.desc())
        .first()
    )

    if not skip_trace:
        raise HTTPException(
            status_code=404,
            detail="No skip trace found for this property. Run a skip trace first.",
        )

    return build_voice_response(skip_trace, property)


@router.post("/property/{property_id}/refresh", response_model=SkipTraceVoiceResponse)
@limiter.limit("5/minute")
async def refresh_skip_trace(request: Request, property_id: int, db: Session = Depends(get_db)):
    """
    Force a new skip trace, even if one already exists.
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Run new skip trace
    result = await skip_trace_service.skip_trace(
        address=property.address,
        city=property.city,
        state=property.state,
        zip_code=property.zip_code,
    )

    # Save new result
    skip_trace = SkipTrace(
        property_id=property.id,
        owner_name=result["owner_name"],
        owner_first_name=result["owner_first_name"],
        owner_last_name=result["owner_last_name"],
        phone_numbers=result["phone_numbers"],
        emails=result["emails"],
        mailing_address=result["mailing_address"],
        mailing_city=result["mailing_city"],
        mailing_state=result["mailing_state"],
        mailing_zip=result["mailing_zip"],
        raw_response=result["raw_response"],
    )
    db.add(skip_trace)
    db.commit()
    db.refresh(skip_trace)

    return build_voice_response(skip_trace, property)
