from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.models.contract_submitter import SubmitterStatus


class SubmitterInput(BaseModel):
    """Input for a single submitter when sending a multi-party contract"""

    contact_id: int | None = None  # Optional - can specify contact ID
    name: str  # Required if no contact_id
    email: EmailStr  # Required if no contact_id
    role: str  # DocuSeal role: "Owner", "Lawyer", "Agent", "Buyer", "Seller", etc.
    signing_order: int = 1  # Order for sequential signing


class ContractSubmitterResponse(BaseModel):
    """Response for a contract submitter"""

    id: int
    contract_id: int
    contact_id: int | None
    name: str
    email: str
    role: str
    signing_order: int
    status: SubmitterStatus
    sent_at: datetime | None
    opened_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class MultiPartyContractRequest(BaseModel):
    """
    Send a contract to multiple parties (owner, lawyer, agent, etc.)

    Example: Purchase agreement that needs:
    - Owner to sign first (order 1)
    - Lawyer to review and sign second (order 2)
    - Agent to countersign third (order 3)
    """

    submitters: list[SubmitterInput]  # List of all parties that need to sign
    order: str = "preserved"  # "preserved" for sequential, "random" for parallel
    message: str | None = None  # Custom message for all recipients


class MultiPartyVoiceRequest(BaseModel):
    """
    Voice-optimized multi-party contract sending.

    Example: "send the purchase agreement to the owner, lawyer, and agent for 141 throop"
    """

    address_query: str  # Property address like "141 throop"
    contract_name: str  # Contract name like "purchase agreement"
    contact_roles: list[str]  # Roles like ["owner", "lawyer", "agent"]
    order: str = "preserved"  # "preserved" for sequential, "random" for parallel
    message: str | None = None


class MultiPartyContractResponse(BaseModel):
    """Response after sending multi-party contract"""

    contract_id: int
    submitters: list[ContractSubmitterResponse]
    voice_confirmation: str
    docuseal_url: str | None = None
