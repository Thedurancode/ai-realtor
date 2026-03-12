from typing import Optional, List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.rate_limit import limiter
from app.models.contract import ContractStatus
from app.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractSendRequest,
    ContractSendToContactRequest,
    ContractStatusResponse,
    ContractSendVoiceRequest,
    ContractVoiceResponse,
    ContractSmartSendRequest,
    ContractSmartSendResponse,
)
from app.schemas.contract_submitter import (
    MultiPartyContractRequest,
    MultiPartyVoiceRequest,
    MultiPartyContractResponse,
)
from app.services.contract_service import ContractService, get_contract_service

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("/", response_model=list[ContractResponse])
def list_all_contracts(
    status: ContractStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    svc: ContractService = Depends(get_contract_service),
):
    """List all contracts with optional status filter."""
    return svc.list_all(status=status, limit=limit, offset=offset)


@router.post("/", response_model=ContractResponse, status_code=201)
def create_contract(
    contract: ContractCreate,
    svc: ContractService = Depends(get_contract_service),
):
    """Create a contract for a property."""
    return svc.create(contract)


@router.get("/property/{property_id}", response_model=list[ContractResponse])
def list_contracts_for_property(
    property_id: int,
    status: ContractStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    svc: ContractService = Depends(get_contract_service),
):
    """List all contracts for a property with optional status filter."""
    return svc.list_for_property(property_id, status=status, limit=limit, offset=offset)


@router.get("/contact/{contact_id}", response_model=list[ContractResponse])
def list_contracts_for_contact(
    contact_id: int,
    status: ContractStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    svc: ContractService = Depends(get_contract_service),
):
    """List all contracts for a specific contact."""
    return svc.list_for_contact(contact_id, status=status, limit=limit, offset=offset)


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: int,
    svc: ContractService = Depends(get_contract_service),
):
    """Get a contract by ID."""
    return svc.get(contract_id)


@router.patch("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    contract: ContractUpdate,
    svc: ContractService = Depends(get_contract_service),
):
    """Update a contract."""
    return svc.update(contract_id, contract)


@router.delete("/{contract_id}", status_code=204)
def delete_contract(
    contract_id: int,
    svc: ContractService = Depends(get_contract_service),
):
    """Delete a contract."""
    svc.delete(contract_id)
    return None


@router.post("/{contract_id}/send", response_model=ContractResponse)
async def send_contract(
    contract_id: int,
    send_request: ContractSendRequest,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Send a contract via DocuSeal to a specific email address.
    Creates a DocuSeal submission and sends email to recipient.
    """
    return await svc.send(contract_id, send_request)


@router.post("/{contract_id}/send-to-contact", response_model=ContractResponse)
async def send_contract_to_contact(
    contract_id: int,
    send_request: ContractSendToContactRequest,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Send a contract to an existing contact.
    Links the contract to the contact and sends via DocuSeal.
    """
    return await svc.send_to_contact(contract_id, send_request)


@router.get("/{contract_id}/status", response_model=ContractStatusResponse)
async def get_contract_status(
    contract_id: int,
    refresh: bool = True,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Get contract status from DocuSeal.

    Args:
        contract_id: Contract ID
        refresh: If True, fetches latest status from DocuSeal API
    """
    return await svc.get_status(contract_id, refresh=refresh)


@router.post("/{contract_id}/cancel", response_model=ContractResponse)
async def cancel_contract(
    contract_id: int,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Cancel a contract (archive in DocuSeal).
    """
    return await svc.cancel(contract_id)


@router.post("/voice/send", response_model=ContractVoiceResponse)
async def send_contract_voice(
    request: ContractSendVoiceRequest,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Voice-optimized contract sending.
    Example: "send the property agreement to the lawyer on file for 141 throop"
    """
    return await svc.send_voice(request)


@router.post("/voice/smart-send", response_model=ContractSmartSendResponse)
async def smart_send_contract(
    request: ContractSmartSendRequest,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Smart contract sending - auto-determines who needs to sign.

    Example: "Send the purchase agreement for 123 contract lane"
    The system automatically knows Purchase Agreement needs buyer + seller,
    finds those contacts on the property, and sends to both.

    No need to specify contact roles - the template's required_signer_roles
    (or the default role map) handles it.
    """
    return await svc.smart_send(request)


@router.post("/voice/send-multi-party", response_model=MultiPartyContractResponse)
async def send_contract_multi_party_voice(
    request: MultiPartyVoiceRequest,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Voice-optimized multi-party contract sending.

    Example: "send the purchase agreement to the owner, lawyer, and agent for 141 throop"
    """
    return await svc.send_multi_party_voice(request)


@router.post("/{contract_id}/send-multi-party", response_model=MultiPartyContractResponse)
async def send_contract_multi_party(
    contract_id: int,
    request: MultiPartyContractRequest,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Send a contract to multiple parties (owner, lawyer, agent, etc.)

    Example: Purchase agreement that needs owner, lawyer, and agent to all sign.

    The contract will be sent in the order specified:
    - order="preserved": Sequential signing (owner -> lawyer -> agent)
    - order="random": Parallel signing (all at once)
    """
    return await svc.send_multi_party(contract_id, request)


@router.post("/webhook/docuseal", status_code=200)
async def docuseal_webhook(
    payload: dict,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Webhook endpoint for all DocuSeal events.
    Configure this URL in your DocuSeal settings: https://your-domain.com/contracts/webhook/docuseal

    Supported events:
    - form.viewed: Submitter viewed the form
    - form.started: Submitter started filling the form
    - form.completed: Submitter completed their signature
    - form.declined: Submitter declined to sign
    - submission.created: Submission was created
    - submission.completed: All submitters completed
    - submission.expired: Submission expired
    - submission.archived: Submission was cancelled/archived
    """
    return await svc.handle_webhook(payload)


# ========== AUTO-ATTACH CONTRACT ENDPOINTS ==========

@router.post("/property/{property_id}/auto-attach", response_model=dict)
def auto_attach_contracts_to_property(
    property_id: int,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Manually trigger auto-attach of required contracts to a property.

    This is useful if:
    1. Property was created before contract templates were configured
    2. New contract templates were added
    3. Property details changed (state, type, price)

    Returns list of contracts that were attached.
    """
    return svc.auto_attach(property_id)


@router.get("/property/{property_id}/required-status", response_model=dict)
def get_property_required_contracts_status(
    property_id: int,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Get status of all required contracts for a property.

    This shows:
    - How many required contracts exist
    - How many are completed
    - How many are in progress
    - What's missing
    - Whether property is ready to close

    Useful for checking if property can proceed to closing.
    """
    return svc.get_required_status(property_id)


@router.get("/property/{property_id}/signing-status", response_model=dict)
def get_property_signing_status(
    property_id: int,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Get signing status for all contracts on a property.
    Shows who signed, who hasn't, and what's still waiting -- across all contracts.
    Voice-optimized response included.
    """
    return svc.get_signing_status(property_id)


@router.get("/property/{property_id}/missing-contracts", response_model=dict)
def get_missing_contracts(
    property_id: int,
    required_only: bool = False,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Get list of contracts that should be attached to this property but aren't.

    Args:
        required_only: If true, only show REQUIRED contracts. Otherwise show all applicable.

    Useful for compliance checking and closing readiness.
    """
    return svc.get_missing_contracts(property_id, required_only=required_only)


@router.post("/voice/check-contracts", response_model=dict)
def check_contracts_voice(
    address_query: str,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Voice: "Check contract status for 141 throop"
    Returns voice-friendly summary of contract requirements.
    """
    return svc.check_contracts_voice(address_query)


# ========== AI-POWERED CONTRACT SUGGESTIONS ==========

@router.post("/property/{property_id}/ai-suggest", response_model=dict)
@limiter.limit("20/minute")
async def ai_suggest_contracts(
    request: Request,
    property_id: int,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Use AI to analyze property and suggest which contracts are required.

    Claude AI analyzes:
    - Property location, type, price
    - State/local regulations
    - Standard industry practices
    - Risk factors

    Returns detailed suggestions with reasoning for each contract.
    """
    return await svc.ai_suggest(property_id)


@router.post("/property/{property_id}/ai-apply-suggestions", response_model=dict)
@limiter.limit("20/minute")
async def apply_ai_suggestions(
    request: Request,
    property_id: int,
    only_required: bool = True,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Apply AI suggestions by creating contracts for the property.

    Args:
        only_required: If true, only create contracts AI marked as required.
                      If false, create all suggested contracts.

    Returns list of contracts created.
    """
    return await svc.ai_apply_suggestions(property_id, only_required=only_required)


@router.get("/property/{property_id}/ai-analyze-gaps", response_model=dict)
@limiter.limit("20/minute")
async def analyze_contract_gaps(
    request: Request,
    property_id: int,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Analyze what contracts are missing for a property.

    Uses AI to determine critical vs recommended missing contracts.
    """
    return await svc.ai_analyze_gaps(property_id)


# ========== MANUAL CONTRACT REQUIREMENT MANAGEMENT ==========

@router.patch("/contracts/{contract_id}/mark-required", response_model=dict)
def mark_contract_required(
    contract_id: int,
    is_required: bool = True,
    reason: Optional[str] = None,
    required_by_date: Optional[str] = None,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Manually mark a contract as required or optional.

    Use this to override AI suggestions or template defaults.

    Args:
        is_required: True = required, False = optional
        reason: Optional explanation for why
        required_by_date: Optional deadline (ISO format: 2026-03-15)
    """
    return svc.mark_required(contract_id, is_required=is_required, reason=reason, required_by_date=required_by_date)


@router.post("/property/{property_id}/set-required-contracts", response_model=dict)
def set_required_contracts_for_property(
    property_id: int,
    contract_ids: List[int],
    mark_all_others_optional: bool = False,
    svc: ContractService = Depends(get_contract_service),
):
    """
    Manually set which contracts are required for a property.

    Args:
        contract_ids: List of contract IDs to mark as required
        mark_all_others_optional: If true, mark all other contracts as optional

    This gives you full control over which contracts are required.
    """
    return svc.set_required_for_property(property_id, contract_ids, mark_all_others_optional=mark_all_others_optional)
