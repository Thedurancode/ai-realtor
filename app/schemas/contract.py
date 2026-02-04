from pydantic import BaseModel
from datetime import datetime

from app.models.contract import ContractStatus


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
