from fastapi import APIRouter, HTTPException

from app.services.google_places import google_places_service
from app.schemas.address import (
    AddressAutocompleteRequest,
    AddressAutocompleteResponse,
    AddressSuggestion,
    AddressDetailsRequest,
    AddressDetailsResponse,
    AddressDetails,
)

router = APIRouter(prefix="/address", tags=["address"])


@router.post("/autocomplete", response_model=AddressAutocompleteResponse)
async def autocomplete_address(request: AddressAutocompleteRequest):
    """
    Get address suggestions from partial input.
    Voice agent says: "141 throop ave new brunswick"
    Returns suggestions with voice-friendly prompts.
    """
    suggestions = await google_places_service.autocomplete(
        input_text=request.input,
        country=request.country,
    )

    if not suggestions:
        return AddressAutocompleteResponse(
            suggestions=[],
            voice_prompt="I couldn't find any addresses matching that. Could you please repeat the address?",
        )

    suggestion_list = [AddressSuggestion(**s) for s in suggestions]

    if len(suggestion_list) == 1:
        voice_prompt = f"I found one address: {suggestion_list[0].description}. Is this correct?"
    else:
        options = ". ".join(
            [f"Option {i+1}: {s.description}" for i, s in enumerate(suggestion_list[:3])]
        )
        voice_prompt = f"I found {len(suggestion_list)} addresses. {options}. Which one is correct?"

    return AddressAutocompleteResponse(
        suggestions=suggestion_list,
        voice_prompt=voice_prompt,
    )


@router.post("/details", response_model=AddressDetailsResponse)
async def get_address_details(request: AddressDetailsRequest):
    """
    Get full address details from a place_id.
    Called after user confirms an autocomplete suggestion.
    Returns parsed address components for property creation.
    """
    details = await google_places_service.get_place_details(request.place_id)

    if not details:
        raise HTTPException(status_code=404, detail="Address not found")

    address = AddressDetails(**details)

    street_address = f"{address.street_number} {address.street}".strip()
    voice_confirmation = (
        f"Got it. The property address is {street_address}, "
        f"{address.city}, {address.state} {address.zip_code}."
    )

    return AddressDetailsResponse(
        address=address,
        voice_confirmation=voice_confirmation,
    )
