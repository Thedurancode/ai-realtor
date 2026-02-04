from pydantic import BaseModel


class AddressAutocompleteRequest(BaseModel):
    """Request for address autocomplete - voice agent sends partial address"""

    input: str
    country: str = "us"


class AddressSuggestion(BaseModel):
    """A single address suggestion from autocomplete"""

    place_id: str
    description: str
    main_text: str
    secondary_text: str


class AddressAutocompleteResponse(BaseModel):
    """Response with address suggestions for voice agent to read back"""

    suggestions: list[AddressSuggestion]
    voice_prompt: str  # Text for voice agent to speak


class AddressDetailsRequest(BaseModel):
    """Request to get full address details from a place_id"""

    place_id: str


class AddressDetails(BaseModel):
    """Full parsed address details"""

    formatted_address: str
    street_number: str
    street: str
    city: str
    state: str
    zip_code: str
    country: str
    lat: float | None = None
    lng: float | None = None


class AddressDetailsResponse(BaseModel):
    """Response with full address for voice confirmation"""

    address: AddressDetails
    voice_confirmation: str  # Text for voice agent to speak back
