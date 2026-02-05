from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.models.property import Property
from app.models.contact import Contact, ContactRole
from app.models.contract import Contract, ContractStatus
from app.models.contract_submitter import ContractSubmitter, SubmitterStatus
from app.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractSendRequest,
    ContractSendToContactRequest,
    ContractStatusResponse,
    ContractSendVoiceRequest,
    ContractVoiceResponse,
)
from app.schemas.contract_submitter import (
    MultiPartyContractRequest,
    MultiPartyVoiceRequest,
    MultiPartyContractResponse,
    SubmitterInput,
    ContractSubmitterResponse,
)
from app.services.docuseal import docuseal_client
from app.services.resend_service import resend_service
from app.services.notification_service import notification_service
from app.services.contract_auto_attach import contract_auto_attach_service
from app.models.contract_template import ContractRequirement

router = APIRouter(prefix="/contracts", tags=["contracts"])


# Helper function to get WebSocket manager
def get_ws_manager():
    """Get WebSocket manager from main module"""
    try:
        import sys
        if 'app.main' in sys.modules:
            return sys.modules['app.main'].manager
    except:
        pass
    return None


@router.get("/", response_model=list[ContractResponse])
def list_all_contracts(
    status: ContractStatus | None = None,
    db: Session = Depends(get_db),
):
    """List all contracts with optional status filter."""
    contracts_query = db.query(Contract)

    if status:
        contracts_query = contracts_query.filter(Contract.status == status)

    contracts = contracts_query.order_by(Contract.created_at.desc()).all()
    return contracts


@router.post("/", response_model=ContractResponse, status_code=201)
def create_contract(contract: ContractCreate, db: Session = Depends(get_db)):
    """Create a contract for a property."""
    property = db.query(Property).filter(Property.id == contract.property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Validate contact if provided
    if contract.contact_id:
        contact = db.query(Contact).filter(Contact.id == contract.contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        if contact.property_id != contract.property_id:
            raise HTTPException(
                status_code=400,
                detail="Contact must belong to the same property as the contract"
            )

    new_contract = Contract(
        property_id=contract.property_id,
        contact_id=contract.contact_id,
        name=contract.name,
        description=contract.description,
        docuseal_template_id=contract.docuseal_template_id,
        status=ContractStatus.DRAFT,
    )
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)
    return new_contract


@router.get("/property/{property_id}", response_model=list[ContractResponse])
def list_contracts_for_property(
    property_id: int,
    status: ContractStatus | None = None,
    db: Session = Depends(get_db),
):
    """List all contracts for a property with optional status filter."""
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    contracts_query = db.query(Contract).filter(Contract.property_id == property_id)

    if status:
        contracts_query = contracts_query.filter(Contract.status == status)

    contracts = contracts_query.order_by(Contract.created_at.desc()).all()
    return contracts


@router.get("/contact/{contact_id}", response_model=list[ContractResponse])
def list_contracts_for_contact(
    contact_id: int,
    status: ContractStatus | None = None,
    db: Session = Depends(get_db),
):
    """List all contracts for a specific contact."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contracts_query = db.query(Contract).filter(Contract.contact_id == contact_id)

    if status:
        contracts_query = contracts_query.filter(Contract.status == status)

    contracts = contracts_query.order_by(Contract.created_at.desc()).all()
    return contracts


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    """Get a contract by ID."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.patch("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int, contract: ContractUpdate, db: Session = Depends(get_db)
):
    """Update a contract."""
    db_contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    update_data = contract.model_dump(exclude_unset=True)

    # Validate contact if being updated
    if "contact_id" in update_data and update_data["contact_id"]:
        contact = db.query(Contact).filter(Contact.id == update_data["contact_id"]).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        if contact.property_id != db_contract.property_id:
            raise HTTPException(
                status_code=400,
                detail="Contact must belong to the same property as the contract"
            )

    # Set completed_at if marking as completed
    if "status" in update_data and update_data["status"] == ContractStatus.COMPLETED:
        if not db_contract.completed_at:
            update_data["completed_at"] = datetime.now()

    for field, value in update_data.items():
        setattr(db_contract, field, value)

    db.commit()
    db.refresh(db_contract)
    return db_contract


@router.delete("/{contract_id}", status_code=204)
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    """Delete a contract."""
    db_contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    db.delete(db_contract)
    db.commit()
    return None


@router.post("/{contract_id}/send", response_model=ContractResponse)
async def send_contract(
    contract_id: int,
    send_request: ContractSendRequest,
    db: Session = Depends(get_db),
):
    """
    Send a contract via DocuSeal to a specific email address.
    Creates a DocuSeal submission and sends email to recipient.
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.docuseal_template_id:
        raise HTTPException(
            status_code=400,
            detail="Contract must have a DocuSeal template ID before sending",
        )

    try:
        # Create submission in DocuSeal
        submitters = [{
            "email": send_request.recipient_email,
            "role": send_request.recipient_role,
        }]

        if send_request.recipient_name:
            submitters[0]["name"] = send_request.recipient_name

        docuseal_response = await docuseal_client.create_submission(
            template_id=contract.docuseal_template_id,
            submitters=submitters,
            send_email=True,
            message=send_request.message,
        )

        # Update contract with DocuSeal info
        contract.docuseal_submission_id = str(docuseal_response["id"])
        contract.docuseal_url = docuseal_response.get("submission_url")
        contract.status = ContractStatus.SENT
        contract.sent_at = datetime.now()

        db.commit()
        db.refresh(contract)
        return contract

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"DocuSeal API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send contract: {str(e)}"
        )


@router.post("/{contract_id}/send-to-contact", response_model=ContractResponse)
async def send_contract_to_contact(
    contract_id: int,
    send_request: ContractSendToContactRequest,
    db: Session = Depends(get_db),
):
    """
    Send a contract to an existing contact.
    Links the contract to the contact and sends via DocuSeal.
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.docuseal_template_id:
        raise HTTPException(
            status_code=400,
            detail="Contract must have a DocuSeal template ID before sending",
        )

    # Get contact
    contact = db.query(Contact).filter(Contact.id == send_request.contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if not contact.email:
        raise HTTPException(
            status_code=400,
            detail="Contact must have an email address to send contract"
        )

    # Validate contact belongs to same property
    if contact.property_id != contract.property_id:
        raise HTTPException(
            status_code=400,
            detail="Contact must belong to the same property as the contract"
        )

    try:
        # Create submission in DocuSeal
        submitters = [{
            "email": contact.email,
            "name": contact.name,
            "role": send_request.recipient_role,
        }]

        docuseal_response = await docuseal_client.create_submission(
            template_id=contract.docuseal_template_id,
            submitters=submitters,
            send_email=True,
            message=send_request.message,
        )

        # Update contract with DocuSeal info and link to contact
        contract.contact_id = contact.id
        contract.docuseal_submission_id = str(docuseal_response["id"])
        contract.docuseal_url = docuseal_response.get("submission_url")
        contract.status = ContractStatus.SENT
        contract.sent_at = datetime.now()

        db.commit()
        db.refresh(contract)
        return contract

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"DocuSeal API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send contract: {str(e)}"
        )


@router.get("/{contract_id}/status", response_model=ContractStatusResponse)
async def get_contract_status(
    contract_id: int,
    refresh: bool = True,
    db: Session = Depends(get_db),
):
    """
    Get contract status from DocuSeal.

    Args:
        contract_id: Contract ID
        refresh: If True, fetches latest status from DocuSeal API
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.docuseal_submission_id:
        raise HTTPException(
            status_code=400,
            detail="Contract has not been sent yet"
        )

    try:
        if refresh:
            # Fetch latest status from DocuSeal
            docuseal_response = await docuseal_client.get_submission(
                contract.docuseal_submission_id
            )

            # Update contract status based on DocuSeal response
            docuseal_status = docuseal_response.get("status", "").lower()
            old_status = contract.status

            if docuseal_status == "completed":
                contract.status = ContractStatus.COMPLETED
                if not contract.completed_at:
                    contract.completed_at = datetime.now()
            elif docuseal_status == "pending":
                contract.status = ContractStatus.IN_PROGRESS
            elif docuseal_status == "archived":
                contract.status = ContractStatus.CANCELLED

            db.commit()
            db.refresh(contract)

            # Send notification if status changed to completed
            if old_status != ContractStatus.COMPLETED and contract.status == ContractStatus.COMPLETED:
                manager = get_ws_manager()
                property = db.query(Property).filter(Property.id == contract.property_id).first()
                property_address = property.address if property else "Unknown"

                await notification_service.notify_contract_signed(
                    db=db,
                    manager=manager,
                    contract_id=contract.id,
                    contract_name=contract.name,
                    signer_name="All Parties",
                    property_address=property_address,
                    remaining_signers=0
                )

            return ContractStatusResponse(
                contract_id=contract.id,
                status=contract.status,
                docuseal_status=docuseal_response.get("status", "unknown"),
                submission_id=contract.docuseal_submission_id,
                submitters=docuseal_response.get("submitters", []),
                created_at=contract.created_at,
                completed_at=contract.completed_at,
            )
        else:
            # Return cached status
            return ContractStatusResponse(
                contract_id=contract.id,
                status=contract.status,
                docuseal_status="cached",
                submission_id=contract.docuseal_submission_id,
                submitters=[],
                created_at=contract.created_at,
                completed_at=contract.completed_at,
            )

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"DocuSeal API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contract status: {str(e)}"
        )


@router.post("/{contract_id}/cancel", response_model=ContractResponse)
async def cancel_contract(
    contract_id: int,
    db: Session = Depends(get_db),
):
    """
    Cancel a contract (archive in DocuSeal).
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.docuseal_submission_id:
        # Contract not sent yet, just mark as cancelled
        contract.status = ContractStatus.CANCELLED
        db.commit()
        db.refresh(contract)
        return contract

    try:
        # Archive in DocuSeal
        await docuseal_client.archive_submission(contract.docuseal_submission_id)

        contract.status = ContractStatus.CANCELLED
        db.commit()
        db.refresh(contract)
        return contract

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"DocuSeal API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel contract: {str(e)}"
        )


@router.post("/voice/send", response_model=ContractVoiceResponse)
async def send_contract_voice(
    request: ContractSendVoiceRequest,
    db: Session = Depends(get_db),
):
    """
    Voice-optimized contract sending.
    Example: "send the property agreement to the lawyer on file for 141 throop"
    """
    # 1. Find property by partial address
    query = request.address_query.lower()
    property = db.query(Property).filter(Property.address.ilike(f"%{query}%")).first()

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{request.address_query}'. Please add the property first.",
        )

    # 2. Find contact by role
    # Parse role aliases
    role_aliases = {
        "lawyer": ContactRole.LAWYER,
        "attorney": ContactRole.ATTORNEY,
        "contractor": ContactRole.CONTRACTOR,
        "inspector": ContactRole.INSPECTOR,
        "appraiser": ContactRole.APPRAISER,
        "lender": ContactRole.LENDER,
        "mortgage broker": ContactRole.MORTGAGE_BROKER,
        "buyer": ContactRole.BUYER,
        "seller": ContactRole.SELLER,
        "tenant": ContactRole.TENANT,
        "landlord": ContactRole.LANDLORD,
    }

    contact_role_input = request.contact_role.lower().strip()
    contact_role = role_aliases.get(contact_role_input)

    if not contact_role:
        # Try direct enum match
        try:
            contact_role = ContactRole(contact_role_input)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown contact role: '{request.contact_role}'. Valid roles: lawyer, contractor, inspector, buyer, seller, etc.",
            )

    contact = (
        db.query(Contact)
        .filter(Contact.property_id == property.id, Contact.role == contact_role)
        .first()
    )

    if not contact:
        raise HTTPException(
            status_code=404,
            detail=f"No {request.contact_role} found for {property.address}. Please add a {request.contact_role} contact first.",
        )

    if not contact.email:
        raise HTTPException(
            status_code=400,
            detail=f"The {request.contact_role} contact ({contact.name}) doesn't have an email address. Please add one.",
        )

    # 3. Find or create contract
    contract_name_lower = request.contract_name.lower()
    contract = (
        db.query(Contract)
        .filter(
            Contract.property_id == property.id,
            Contract.name.ilike(f"%{contract_name_lower}%"),
        )
        .first()
    )

    if not contract and request.create_if_missing:
        # Create new contract
        contract = Contract(
            property_id=property.id,
            contact_id=contact.id,
            name=request.contract_name.title(),
            status=ContractStatus.DRAFT,
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)

    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"No contract found with name '{request.contract_name}' for {property.address}. Set create_if_missing=true to auto-create.",
        )

    # 4. Check if contract has DocuSeal template
    if not contract.docuseal_template_id:
        raise HTTPException(
            status_code=400,
            detail=f"Contract '{contract.name}' doesn't have a DocuSeal template ID. Please set docuseal_template_id first.",
        )

    # 5. Send contract via DocuSeal
    try:
        submitters = [
            {
                "email": contact.email,
                "name": contact.name,
                "role": request.recipient_role,
            }
        ]

        docuseal_response = await docuseal_client.create_submission(
            template_id=contract.docuseal_template_id,
            submitters=submitters,
            send_email=True,
            message=request.message,
        )

        # Update contract
        contract.contact_id = contact.id
        contract.docuseal_submission_id = str(docuseal_response["id"])
        contract.docuseal_url = docuseal_response.get("submission_url")
        contract.status = ContractStatus.SENT
        contract.sent_at = datetime.now()

        db.commit()
        db.refresh(contract)

        # Build voice confirmation
        voice_confirmation = (
            f"Done! I've sent the {contract.name} to {contact.name} "
            f"({request.contact_role}) at {contact.email} for {property.address}."
        )

        return ContractVoiceResponse(
            contract=contract,
            voice_confirmation=voice_confirmation,
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"DocuSeal API error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send contract: {str(e)}"
        )

@router.post("/voice/send-multi-party", response_model=MultiPartyContractResponse)
async def send_contract_multi_party_voice(
    request: MultiPartyVoiceRequest,
    db: Session = Depends(get_db),
):
    """
    Voice-optimized multi-party contract sending.

    Example: "send the purchase agreement to the owner, lawyer, and agent for 141 throop"
    """
    # 1. Find property
    query = request.address_query.lower()
    property = db.query(Property).filter(Property.address.ilike(f"%{query}%")).first()

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{request.address_query}'",
        )

    # 2. Find contract
    contract_name_lower = request.contract_name.lower()
    contract = (
        db.query(Contract)
        .filter(
            Contract.property_id == property.id,
            Contract.name.ilike(f"%{contract_name_lower}%"),
        )
        .first()
    )

    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"No contract found with name '{request.contract_name}' for {property.address}",
        )

    if not contract.docuseal_template_id:
        raise HTTPException(
            status_code=400,
            detail=f"Contract '{contract.name}' doesn't have a DocuSeal template ID",
        )

    # 3. Find contacts for each role
    role_aliases = {
        "owner": ContactRole.SELLER,
        "seller": ContactRole.SELLER,
        "buyer": ContactRole.BUYER,
        "lawyer": ContactRole.LAWYER,
        "attorney": ContactRole.ATTORNEY,
        "agent": None,  # Special handling for agent
        "contractor": ContactRole.CONTRACTOR,
        "inspector": ContactRole.INSPECTOR,
    }

    submitters = []
    for i, role_input in enumerate(request.contact_roles, 1):
        role_lower = role_input.lower().strip()

        # Special handling for "agent" - use property's agent
        if role_lower == "agent":
            agent = property.agent
            submitters.append(SubmitterInput(
                name=agent.name,
                email=agent.email,
                role="Agent",
                signing_order=i,
            ))
            continue

        # Find contact by role
        contact_role = role_aliases.get(role_lower)
        if not contact_role:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown contact role: '{role_input}'",
            )

        contact = (
            db.query(Contact)
            .filter(Contact.property_id == property.id, Contact.role == contact_role)
            .first()
        )

        if not contact:
            raise HTTPException(
                status_code=404,
                detail=f"No {role_input} found for {property.address}",
            )

        if not contact.email:
            raise HTTPException(
                status_code=400,
                detail=f"The {role_input} contact ({contact.name}) doesn't have an email",
            )

        submitters.append(SubmitterInput(
            contact_id=contact.id,
            name=contact.name,
            email=contact.email,
            role=role_input.title(),
            signing_order=i,
        ))

    # 4. Send via multi-party endpoint
    multi_party_request = MultiPartyContractRequest(
        submitters=submitters,
        order=request.order,
        message=request.message,
    )

    return await send_contract_multi_party(contract.id, multi_party_request, db)

@router.post("/{contract_id}/send-multi-party", response_model=MultiPartyContractResponse)
async def send_contract_multi_party(
    contract_id: int,
    request: MultiPartyContractRequest,
    db: Session = Depends(get_db),
):
    """
    Send a contract to multiple parties (owner, lawyer, agent, etc.)

    Example: Purchase agreement that needs owner, lawyer, and agent to all sign.

    The contract will be sent in the order specified:
    - order="preserved": Sequential signing (owner → lawyer → agent)
    - order="random": Parallel signing (all at once)
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.docuseal_template_id:
        raise HTTPException(
            status_code=400,
            detail="Contract must have a DocuSeal template ID before sending",
        )

    try:
        # Build submitters list for DocuSeal
        docuseal_submitters = []
        contract_submitters = []

        for idx, submitter_input in enumerate(request.submitters, 1):
            # Get contact details if contact_id provided
            if submitter_input.contact_id:
                contact = db.query(Contact).filter(
                    Contact.id == submitter_input.contact_id
                ).first()
                if not contact:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Contact {submitter_input.contact_id} not found"
                    )
                if not contact.email:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Contact {contact.name} doesn't have an email address"
                    )

                name = contact.name
                email = contact.email
            else:
                name = submitter_input.name
                email = submitter_input.email

            # Add to DocuSeal submitters list
            docuseal_submitters.append({
                "name": name,
                "email": email,
                "role": submitter_input.role,
            })

            # Create ContractSubmitter record
            contract_submitter = ContractSubmitter(
                contract_id=contract.id,
                contact_id=submitter_input.contact_id,
                name=name,
                email=email,
                role=submitter_input.role,
                signing_order=submitter_input.signing_order,
                status=SubmitterStatus.PENDING,
            )
            db.add(contract_submitter)
            contract_submitters.append(contract_submitter)

        # Send via DocuSeal
        docuseal_response = await docuseal_client.create_submission(
            template_id=contract.docuseal_template_id,
            submitters=docuseal_submitters,
            send_email=True,
            order=request.order,
            message=request.message,
        )

        # Update contract
        contract.docuseal_submission_id = str(docuseal_response["id"])
        contract.docuseal_url = docuseal_response.get("submission_url")
        contract.status = ContractStatus.SENT
        contract.sent_at = datetime.now()

        # Update submitters with DocuSeal IDs
        docuseal_submitters_response = docuseal_response.get("submitters", [])
        for i, contract_submitter in enumerate(contract_submitters):
            if i < len(docuseal_submitters_response):
                docuseal_submitter = docuseal_submitters_response[i]
                contract_submitter.docuseal_submitter_id = str(docuseal_submitter.get("id"))
                contract_submitter.docuseal_submitter_slug = docuseal_submitter.get("slug")
                contract_submitter.sent_at = datetime.now()

        db.commit()

        # Refresh all submitters
        for submitter in contract_submitters:
            db.refresh(submitter)

        # Send Resend notification emails
        resend_submitters = []
        for i, contract_submitter in enumerate(contract_submitters):
            docuseal_submitter = docuseal_submitters_response[i] if i < len(docuseal_submitters_response) else {}
            resend_submitters.append({
                "name": contract_submitter.name,
                "email": contract_submitter.email,
                "role": contract_submitter.role,
                "docuseal_url": docuseal_submitter.get("embed_src", contract.docuseal_url),
                "signing_order": contract_submitter.signing_order,
            })

        # Send multi-party notification emails
        resend_service.send_multi_party_notification(
            submitters=resend_submitters,
            contract_name=contract.name,
            property_address=contract.property.address,
            is_sequential=(request.order == "preserved"),
            custom_message=request.message,
        )

        # Build voice confirmation
        signer_names = [s.name for s in contract_submitters]
        if len(signer_names) == 2:
            signers_text = f"{signer_names[0]} and {signer_names[1]}"
        elif len(signer_names) > 2:
            signers_text = f"{', '.join(signer_names[:-1])}, and {signer_names[-1]}"
        else:
            signers_text = signer_names[0] if signer_names else "signers"

        order_text = "sequentially" if request.order == "preserved" else "simultaneously"

        voice_confirmation = (
            f"Done! I've sent the {contract.name} to {signers_text} "
            f"for {contract.property.address}. They will sign {order_text}."
        )

        return MultiPartyContractResponse(
            contract_id=contract.id,
            submitters=[ContractSubmitterResponse.from_orm(s) for s in contract_submitters],
            voice_confirmation=voice_confirmation,
            docuseal_url=contract.docuseal_url,
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"DocuSeal API error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send contract: {str(e)}"
        )




@router.post("/webhook/docuseal", status_code=200)
async def docuseal_webhook(
    payload: dict,
    db: Session = Depends(get_db),
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
    - submission.archived: Submission was archived
    """
    try:
        event_type = payload.get("event_type", "")
        data = payload.get("data", payload)  # Some webhooks nest data, some don't

        # Extract IDs based on event type
        if event_type.startswith("form."):
            # Form events: individual submitter updates
            return await _handle_form_event(event_type, data, db)
        elif event_type.startswith("submission."):
            # Submission events: overall contract updates
            return await _handle_submission_event(event_type, data, db)
        else:
            # Legacy support: handle payloads without event_type
            return await _handle_legacy_webhook(data, db)

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


async def _handle_form_event(event_type: str, data: dict, db: Session):
    """
    Handle form-level events (individual submitter actions).

    Events:
    - form.viewed: Submitter opened the document
    - form.started: Submitter began filling fields
    - form.completed: Submitter finished signing
    - form.declined: Submitter declined to sign
    """
    submission_id = str(data.get("submission_id") or data.get("id", ""))
    submitter_id = str(data.get("submitter_id") or data.get("id", ""))

    # Find contract
    contract = db.query(Contract).filter(
        Contract.docuseal_submission_id == submission_id
    ).first()

    if not contract:
        return {"status": "ignored", "message": "Contract not found"}

    # Find specific submitter
    contract_submitter = db.query(ContractSubmitter).filter(
        ContractSubmitter.contract_id == contract.id,
        ContractSubmitter.docuseal_submitter_id == submitter_id
    ).first()

    if not contract_submitter:
        return {"status": "ignored", "message": "Submitter not found"}

    # Update submitter status based on event
    updated = False
    if event_type == "form.viewed":
        # Don't change status for viewed, but could log it
        pass

    elif event_type == "form.started":
        if contract_submitter.status == SubmitterStatus.PENDING:
            contract_submitter.status = SubmitterStatus.OPENED
            if not contract_submitter.opened_at:
                contract_submitter.opened_at = datetime.now()
            updated = True

    elif event_type == "form.completed":
        contract_submitter.status = SubmitterStatus.COMPLETED
        if not contract_submitter.completed_at:
            contract_submitter.completed_at = datetime.now()
        updated = True

        # Update contract status if all submitters completed
        all_submitters = db.query(ContractSubmitter).filter(
            ContractSubmitter.contract_id == contract.id
        ).all()

        if all(s.status == SubmitterStatus.COMPLETED for s in all_submitters):
            contract.status = ContractStatus.COMPLETED
            if not contract.completed_at:
                contract.completed_at = datetime.now()
        else:
            contract.status = ContractStatus.IN_PROGRESS

    elif event_type == "form.declined":
        contract_submitter.status = SubmitterStatus.DECLINED
        # Mark contract as cancelled if anyone declines
        contract.status = ContractStatus.CANCELLED
        updated = True

    if updated:
        db.commit()

    return {
        "status": "success",
        "event": event_type,
        "contract_id": contract.id,
        "submitter": contract_submitter.name,
        "submitter_status": contract_submitter.status.value
    }


async def _handle_submission_event(event_type: str, data: dict, db: Session):
    """
    Handle submission-level events (overall contract status).

    Events:
    - submission.created: Contract sent to signers
    - submission.completed: All signatures collected
    - submission.expired: Submission deadline passed
    - submission.archived: Submission was cancelled/archived
    """
    submission_id = str(data.get("id", ""))

    # Find contract
    contract = db.query(Contract).filter(
        Contract.docuseal_submission_id == submission_id
    ).first()

    if not contract:
        return {"status": "ignored", "message": "Contract not found"}

    # Update contract status based on event
    updated = False
    if event_type == "submission.created":
        if contract.status == ContractStatus.DRAFT:
            contract.status = ContractStatus.SENT
            if not contract.sent_at:
                contract.sent_at = datetime.now()
            updated = True

    elif event_type == "submission.completed":
        contract.status = ContractStatus.COMPLETED
        if not contract.completed_at:
            contract.completed_at = datetime.now()

        # Mark all submitters as completed
        submitters = db.query(ContractSubmitter).filter(
            ContractSubmitter.contract_id == contract.id
        ).all()
        for submitter in submitters:
            if submitter.status != SubmitterStatus.COMPLETED:
                submitter.status = SubmitterStatus.COMPLETED
                if not submitter.completed_at:
                    submitter.completed_at = datetime.now()

        updated = True

    elif event_type == "submission.expired":
        contract.status = ContractStatus.EXPIRED
        updated = True

    elif event_type == "submission.archived":
        contract.status = ContractStatus.CANCELLED
        updated = True

    if updated:
        db.commit()

    return {
        "status": "success",
        "event": event_type,
        "contract_id": contract.id,
        "contract_status": contract.status.value
    }


async def _handle_legacy_webhook(data: dict, db: Session):
    """
    Handle legacy webhook format (without event_type field).
    Kept for backwards compatibility.
    """
    submission_id = str(data.get("id"))
    status = data.get("status", "").lower()
    submitters_data = data.get("submitters", [])

    # Find contract
    contract = db.query(Contract).filter(
        Contract.docuseal_submission_id == submission_id
    ).first()

    if not contract:
        return {"status": "ignored", "message": "Contract not found"}

    # Update individual submitters
    updated_submitters = []
    for submitter_data in submitters_data:
        docuseal_submitter_id = str(submitter_data.get("id"))
        submitter_status = submitter_data.get("status", "").lower()

        contract_submitter = db.query(ContractSubmitter).filter(
            ContractSubmitter.contract_id == contract.id,
            ContractSubmitter.docuseal_submitter_id == docuseal_submitter_id
        ).first()

        if contract_submitter:
            if submitter_status == "completed":
                contract_submitter.status = SubmitterStatus.COMPLETED
                if not contract_submitter.completed_at:
                    contract_submitter.completed_at = datetime.now()
            elif submitter_status == "opened":
                contract_submitter.status = SubmitterStatus.OPENED
                if not contract_submitter.opened_at:
                    contract_submitter.opened_at = datetime.now()
            elif submitter_status == "declined":
                contract_submitter.status = SubmitterStatus.DECLINED

            updated_submitters.append({
                "name": contract_submitter.name,
                "status": contract_submitter.status.value
            })

    # Update overall contract status
    if status == "completed":
        contract.status = ContractStatus.COMPLETED
        if not contract.completed_at:
            contract.completed_at = datetime.now()
    elif status == "pending":
        contract.status = ContractStatus.IN_PROGRESS
    elif status == "archived":
        contract.status = ContractStatus.CANCELLED

    db.commit()

    return {
        "status": "success",
        "contract_id": contract.id,
        "contract_status": contract.status.value,
        "submitters_updated": updated_submitters
    }


# ========== AUTO-ATTACH CONTRACT ENDPOINTS ==========

@router.post("/property/{property_id}/auto-attach", response_model=dict)
def auto_attach_contracts_to_property(
    property_id: int,
    db: Session = Depends(get_db)
):
    """
    Manually trigger auto-attach of required contracts to a property.

    This is useful if:
    1. Property was created before contract templates were configured
    2. New contract templates were added
    3. Property details changed (state, type, price)

    Returns list of contracts that were attached.
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    attached_contracts = contract_auto_attach_service.auto_attach_contracts(db, property)

    return {
        "property_id": property_id,
        "property_address": property.address,
        "contracts_attached": len(attached_contracts),
        "contracts": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "status": c.status.value
            }
            for c in attached_contracts
        ]
    }


@router.get("/property/{property_id}/required-status", response_model=dict)
def get_property_required_contracts_status(
    property_id: int,
    db: Session = Depends(get_db)
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
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    status = contract_auto_attach_service.get_required_contracts_status(db, property)

    # Format for response
    return {
        "property_id": property_id,
        "property_address": property.address,
        "total_required": status["total_required"],
        "completed": status["completed"],
        "in_progress": status["in_progress"],
        "missing": status["missing"],
        "is_ready_to_close": status["is_ready_to_close"],
        "missing_templates": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category.value
            }
            for t in status["missing_templates"]
        ],
        "incomplete_contracts": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status.value,
                "sent_at": c.sent_at
            }
            for c in status["incomplete_contracts"]
        ]
    }


@router.get("/property/{property_id}/missing-contracts", response_model=dict)
def get_missing_contracts(
    property_id: int,
    required_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get list of contracts that should be attached to this property but aren't.

    Args:
        required_only: If true, only show REQUIRED contracts. Otherwise show all applicable.

    Useful for compliance checking and closing readiness.
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    requirement_filter = ContractRequirement.REQUIRED if required_only else None
    missing = contract_auto_attach_service.get_missing_contracts(
        db, property, requirement=requirement_filter
    )

    return {
        "property_id": property_id,
        "property_address": property.address,
        "missing_count": len(missing),
        "missing_contracts": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category.value,
                "requirement": t.requirement.value,
                "docuseal_template_id": t.docuseal_template_id
            }
            for t in missing
        ]
    }


@router.post("/voice/check-contracts", response_model=dict)
def check_contracts_voice(
    address_query: str,
    db: Session = Depends(get_db)
):
    """
    Voice: "Check contract status for 141 throop"
    Returns voice-friendly summary of contract requirements.
    """
    # Find property
    query = address_query.lower()
    property = db.query(Property).filter(Property.address.ilike(f"%{query}%")).first()

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{address_query}'"
        )

    # Get status
    status = contract_auto_attach_service.get_required_contracts_status(db, property)

    # Build voice response
    if status["is_ready_to_close"]:
        voice_response = (
            f"Great news! {property.address} has all {status['total_required']} "
            f"required contracts completed. The property is ready to close."
        )
    else:
        voice_response = f"Contract status for {property.address}:\n"

        if status["completed"] > 0:
            voice_response += f"✅ {status['completed']} contracts completed\n"

        if status["in_progress"] > 0:
            voice_response += f"⏳ {status['in_progress']} contracts in progress\n"

        if status["missing"] > 0:
            voice_response += f"❌ {status['missing']} contracts not yet created\n"
            voice_response += "\nMissing contracts:\n"
            for t in status["missing_templates"][:3]:
                voice_response += f"• {t.name}\n"

        voice_response += f"\nThe property is not ready to close yet."

    return {
        "property_address": property.address,
        "is_ready_to_close": status["is_ready_to_close"],
        "total_required": status["total_required"],
        "completed": status["completed"],
        "in_progress": status["in_progress"],
        "missing": status["missing"],
        "voice_response": voice_response
    }
