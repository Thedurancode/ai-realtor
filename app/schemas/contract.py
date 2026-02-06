from pydantic import BaseModel, computed_field
from datetime import datetime

from app.models.contract import ContractStatus


def format_datetime(dt: datetime | None) -> str | None:
    """Format datetime to human-readable string"""
    if not dt:
        return None
    return dt.strftime("%b %d, %Y at %I:%M %p")


class ContractBase(BaseModel):
    name: str
    description: str | None = None
    docuseal_template_id: str | None = None


class ContractCreate(ContractBase):
    property_id: int
    contact_id: int | None = None


class ContractUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    contact_id: int | None = None
    docuseal_template_id: str | None = None
    docuseal_submission_id: str | None = None
    docuseal_url: str | None = None
    status: ContractStatus | None = None
    sent_at: datetime | None = None
    completed_at: datetime | None = None


class ContractResponse(ContractBase):
    id: int
    property_id: int
    contact_id: int | None = None
    docuseal_submission_id: str | None = None
    docuseal_url: str | None = None
    status: ContractStatus
    sent_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @computed_field
    @property
    def sent_at_formatted(self) -> str | None:
        return format_datetime(self.sent_at)

    @computed_field
    @property
    def completed_at_formatted(self) -> str | None:
        return format_datetime(self.completed_at)

    @computed_field
    @property
    def created_at_formatted(self) -> str:
        return format_datetime(self.created_at)

    @computed_field
    @property
    def updated_at_formatted(self) -> str | None:
        return format_datetime(self.updated_at)

    class Config:
        from_attributes = True


class ContractSendRequest(BaseModel):
    """Request to send a contract via DocuSeal"""

    recipient_email: str
    recipient_name: str | None = None
    recipient_role: str = "Signer"
    message: str | None = None


class ContractSendToContactRequest(BaseModel):
    """Send contract to an existing contact"""

    contact_id: int
    recipient_role: str = "Signer"
    message: str | None = None


class ContractStatusResponse(BaseModel):
    """DocuSeal submission status response"""

    contract_id: int
    status: ContractStatus
    docuseal_status: str
    submission_id: str
    submitters: list[dict]  # List of submitters with their status
    created_at: datetime
    completed_at: datetime | None = None

    @computed_field
    @property
    def created_at_formatted(self) -> str:
        return format_datetime(self.created_at)

    @computed_field
    @property
    def completed_at_formatted(self) -> str | None:
        return format_datetime(self.completed_at)


class ContractSendVoiceRequest(BaseModel):
    """
    Voice-optimized contract sending.
    Example: "send the property agreement to the lawyer on file for 141 throop"
    """

    address_query: str  # Partial address like "141 throop"
    contract_name: str  # Contract name like "property agreement", "purchase agreement"
    contact_role: str  # Role like "lawyer", "buyer", "seller", "inspector"
    recipient_role: str = "Signer"  # DocuSeal role
    message: str | None = None
    create_if_missing: bool = True  # Create contract if it doesn't exist


class ContractVoiceResponse(BaseModel):
    """Voice-optimized response after sending contract"""

    contract: ContractResponse
    voice_confirmation: str


class ContractSmartSendRequest(BaseModel):
    """
    Smart contract sending - auto-determines signers from template role mapping.
    Example: "send the purchase agreement for 123 contract lane"
    No need to specify who - the system knows Purchase Agreement needs buyer + seller.
    """

    address_query: str  # Partial address like "123 contract lane"
    contract_name: str  # Contract name like "Purchase Agreement"
    order: str = "preserved"  # "preserved" for sequential, "random" for parallel
    message: str | None = None
    create_if_missing: bool = True  # Create contract if it doesn't exist


class ContractSmartSendResponse(BaseModel):
    """Response after smart-sending a contract"""

    contract_id: int
    contract_name: str
    property_address: str
    submitters: list[dict]  # [{name, email, role}]
    missing_roles: list[str]  # Roles that couldn't be filled
    voice_confirmation: str
    docuseal_url: str | None = None
