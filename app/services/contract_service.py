"""
Contract service — business logic extracted from the contracts router.
"""

import logging
from datetime import datetime
from typing import Optional, List

import httpx
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contact import Contact, ContactRole
from app.models.contract import Contract, ContractStatus, RequirementSource
from app.models.contract_submitter import ContractSubmitter, SubmitterStatus
from app.models.contract_template import ContractRequirement, ContractTemplate
from app.models.property import Property
from app.schemas.contract import (
    ContractCreate,
    ContractSendRequest,
    ContractSendToContactRequest,
    ContractSendVoiceRequest,
    ContractSmartSendRequest,
    ContractStatusResponse,
    ContractUpdate,
    ContractVoiceResponse,
    ContractSmartSendResponse,
)
from app.schemas.contract_submitter import (
    ContractSubmitterResponse,
    MultiPartyContractRequest,
    MultiPartyContractResponse,
    MultiPartyVoiceRequest,
    SubmitterInput,
)
from app.services.contract_ai_service import contract_ai_service
from app.services.contract_auto_attach import contract_auto_attach_service
from app.services.contract_smart_send import (
    build_submitters,
    find_contacts_for_roles,
    get_required_roles,
)
from app.services.conversation_context import get_context, persist_context_to_graph
from app.services.docuseal import docuseal_client
from app.services.memory_graph import memory_graph_service
from app.services.notification_service import notification_service
from app.services.resend_service import resend_service
from app.utils.websocket import get_ws_manager

logger = logging.getLogger(__name__)

# Role aliases shared between voice endpoints
ROLE_ALIASES = {
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

MULTI_PARTY_ROLE_ALIASES = {
    "owner": ContactRole.SELLER,
    "seller": ContactRole.SELLER,
    "buyer": ContactRole.BUYER,
    "lawyer": ContactRole.LAWYER,
    "attorney": ContactRole.ATTORNEY,
    "agent": None,  # Special handling
    "contractor": ContactRole.CONTRACTOR,
    "inspector": ContactRole.INSPECTOR,
}


def _format_signers_text(names: list[str]) -> str:
    """Build a natural-language list of signer names."""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


class ContractService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def list_all(
        self,
        status: Optional[ContractStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Contract]:
        limit = min(limit, 200)
        q = self.db.query(Contract)
        if status:
            q = q.filter(Contract.status == status)
        return q.order_by(Contract.created_at.desc()).offset(offset).limit(limit).all()

    def list_for_property(
        self,
        property_id: int,
        status: Optional[ContractStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Contract]:
        limit = min(limit, 200)
        prop = self.db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")

        q = self.db.query(Contract).filter(Contract.property_id == property_id)
        if status:
            q = q.filter(Contract.status == status)
        return q.order_by(Contract.created_at.desc()).offset(offset).limit(limit).all()

    def list_for_contact(
        self,
        contact_id: int,
        status: Optional[ContractStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Contract]:
        limit = min(limit, 200)
        contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        q = self.db.query(Contract).filter(Contract.contact_id == contact_id)
        if status:
            q = q.filter(Contract.status == status)
        return q.order_by(Contract.created_at.desc()).offset(offset).limit(limit).all()

    def get(self, contract_id: int) -> Contract:
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        return contract

    def create(self, data: ContractCreate) -> Contract:
        prop = self.db.query(Property).filter(Property.id == data.property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")

        if data.contact_id:
            contact = self.db.query(Contact).filter(Contact.id == data.contact_id).first()
            if not contact:
                raise HTTPException(status_code=404, detail="Contact not found")
            if contact.property_id != data.property_id:
                raise HTTPException(
                    status_code=400,
                    detail="Contact must belong to the same property as the contract",
                )

        new_contract = Contract(
            property_id=data.property_id,
            contact_id=data.contact_id,
            name=data.name,
            description=data.description,
            docuseal_template_id=data.docuseal_template_id,
            status=ContractStatus.DRAFT,
        )
        self.db.add(new_contract)
        self.db.commit()
        self.db.refresh(new_contract)
        return new_contract

    def update(self, contract_id: int, data: ContractUpdate) -> Contract:
        db_contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not db_contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        update_data = data.model_dump(exclude_unset=True)

        if "contact_id" in update_data and update_data["contact_id"]:
            contact = self.db.query(Contact).filter(Contact.id == update_data["contact_id"]).first()
            if not contact:
                raise HTTPException(status_code=404, detail="Contact not found")
            if contact.property_id != db_contract.property_id:
                raise HTTPException(
                    status_code=400,
                    detail="Contact must belong to the same property as the contract",
                )

        if "status" in update_data and update_data["status"] == ContractStatus.COMPLETED:
            if not db_contract.completed_at:
                update_data["completed_at"] = datetime.now()

        for field, value in update_data.items():
            setattr(db_contract, field, value)

        self.db.commit()
        self.db.refresh(db_contract)
        return db_contract

    def delete(self, contract_id: int) -> None:
        db_contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not db_contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        self.db.delete(db_contract)
        self.db.commit()

    # ------------------------------------------------------------------
    # DocuSeal sending
    # ------------------------------------------------------------------

    async def send(self, contract_id: int, send_request: ContractSendRequest) -> Contract:
        contract = self._get_contract_or_404(contract_id)
        self._require_docuseal_template(contract)

        try:
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

            contract.docuseal_submission_id = str(docuseal_response["id"])
            contract.docuseal_url = docuseal_response.get("submission_url")
            contract.status = ContractStatus.SENT
            contract.sent_at = datetime.now()

            self.db.commit()
            self.db.refresh(contract)
            return contract

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"DocuSeal API error: {e.response.text}",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send contract: {str(e)}")

    async def send_to_contact(
        self, contract_id: int, send_request: ContractSendToContactRequest
    ) -> Contract:
        contract = self._get_contract_or_404(contract_id)
        self._require_docuseal_template(contract)

        contact = self.db.query(Contact).filter(Contact.id == send_request.contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        if not contact.email:
            raise HTTPException(
                status_code=400,
                detail="Contact must have an email address to send contract",
            )
        if contact.property_id != contract.property_id:
            raise HTTPException(
                status_code=400,
                detail="Contact must belong to the same property as the contract",
            )

        try:
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

            contract.contact_id = contact.id
            contract.docuseal_submission_id = str(docuseal_response["id"])
            contract.docuseal_url = docuseal_response.get("submission_url")
            contract.status = ContractStatus.SENT
            contract.sent_at = datetime.now()

            self.db.commit()
            self.db.refresh(contract)
            return contract

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"DocuSeal API error: {e.response.text}",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send contract: {str(e)}")

    async def get_status(self, contract_id: int, refresh: bool = True) -> ContractStatusResponse:
        contract = self._get_contract_or_404(contract_id)

        if not contract.docuseal_submission_id:
            raise HTTPException(status_code=400, detail="Contract has not been sent yet")

        try:
            if refresh:
                docuseal_response = await docuseal_client.get_submission(
                    contract.docuseal_submission_id
                )

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

                self.db.commit()
                self.db.refresh(contract)

                # Notification on completion
                if old_status != ContractStatus.COMPLETED and contract.status == ContractStatus.COMPLETED:
                    manager = get_ws_manager()
                    prop = self.db.query(Property).filter(Property.id == contract.property_id).first()
                    property_address = prop.address if prop else "Unknown"

                    await notification_service.notify_contract_signed(
                        db=self.db,
                        manager=manager,
                        contract_id=contract.id,
                        contract_name=contract.name,
                        signer_name="All Parties",
                        property_address=property_address,
                        remaining_signers=0,
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
                detail=f"DocuSeal API error: {e.response.text}",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get contract status: {str(e)}")

    async def cancel(self, contract_id: int) -> Contract:
        contract = self._get_contract_or_404(contract_id)

        if not contract.docuseal_submission_id:
            contract.status = ContractStatus.CANCELLED
            self.db.commit()
            self.db.refresh(contract)
            return contract

        try:
            await docuseal_client.archive_submission(contract.docuseal_submission_id)
            contract.status = ContractStatus.CANCELLED
            self.db.commit()
            self.db.refresh(contract)
            return contract

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"DocuSeal API error: {e.response.text}",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to cancel contract: {str(e)}")

    # ------------------------------------------------------------------
    # Voice endpoints
    # ------------------------------------------------------------------

    async def send_voice(self, request: ContractSendVoiceRequest) -> ContractVoiceResponse:
        # 1. Find property
        query = request.address_query.lower()
        prop = self.db.query(Property).filter(Property.address.ilike(f"%{query}%")).first()
        if not prop:
            raise HTTPException(
                status_code=404,
                detail=f"No property found matching '{request.address_query}'. Please add the property first.",
            )

        # 2. Resolve contact role
        contact_role_input = request.contact_role.lower().strip()
        contact_role = ROLE_ALIASES.get(contact_role_input)
        if not contact_role:
            try:
                contact_role = ContactRole(contact_role_input)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown contact role: '{request.contact_role}'. Valid roles: lawyer, contractor, inspector, buyer, seller, etc.",
                )

        contact = (
            self.db.query(Contact)
            .filter(Contact.property_id == prop.id, Contact.role == contact_role)
            .first()
        )
        if not contact:
            raise HTTPException(
                status_code=404,
                detail=f"No {request.contact_role} found for {prop.address}. Please add a {request.contact_role} contact first.",
            )
        if not contact.email:
            raise HTTPException(
                status_code=400,
                detail=f"The {request.contact_role} contact ({contact.name}) doesn't have an email address. Please add one.",
            )

        # 3. Find or create contract
        contract_name_lower = request.contract_name.lower()
        contract = (
            self.db.query(Contract)
            .filter(
                Contract.property_id == prop.id,
                Contract.name.ilike(f"%{contract_name_lower}%"),
            )
            .first()
        )

        if not contract and request.create_if_missing:
            contract = Contract(
                property_id=prop.id,
                contact_id=contact.id,
                name=request.contract_name.title(),
                status=ContractStatus.DRAFT,
            )
            self.db.add(contract)
            self.db.commit()
            self.db.refresh(contract)

        if not contract:
            raise HTTPException(
                status_code=404,
                detail=f"No contract found with name '{request.contract_name}' for {prop.address}. Set create_if_missing=true to auto-create.",
            )

        # 4. DocuSeal template check
        if not contract.docuseal_template_id:
            raise HTTPException(
                status_code=400,
                detail=f"Contract '{contract.name}' doesn't have a DocuSeal template ID. Please set docuseal_template_id first.",
            )

        # 5. Send via DocuSeal
        try:
            submitters = [{
                "email": contact.email,
                "name": contact.name,
                "role": request.recipient_role,
            }]

            docuseal_response = await docuseal_client.create_submission(
                template_id=contract.docuseal_template_id,
                submitters=submitters,
                send_email=True,
                message=request.message,
            )

            contract.contact_id = contact.id
            contract.docuseal_submission_id = str(docuseal_response["id"])
            contract.docuseal_url = docuseal_response.get("submission_url")
            contract.status = ContractStatus.SENT
            contract.sent_at = datetime.now()

            self.db.commit()
            self.db.refresh(contract)

            # Persist conversational memory
            context = get_context(request.session_id)
            context.set_last_property(prop.id, prop.address)
            context.set_last_contact(contact.id, contact.name)
            context.set_last_contract(contract.id, contract.name)
            memory_graph_service.remember_property(
                db=self.db,
                session_id=request.session_id,
                property_id=prop.id,
                address=prop.address,
                city=prop.city,
                state=prop.state,
            )
            memory_graph_service.remember_contact(
                db=self.db,
                session_id=request.session_id,
                contact_id=contact.id,
                name=contact.name,
                role=contact.role.value if contact.role else None,
                property_id=prop.id,
            )
            memory_graph_service.remember_contract(
                db=self.db,
                session_id=request.session_id,
                contract_id=contract.id,
                name=contract.name,
                status=contract.status.value if contract.status else None,
                property_id=prop.id,
                contact_id=contact.id,
            )
            persist_context_to_graph(db=self.db, session_id=request.session_id)
            self.db.commit()

            voice_confirmation = (
                f"Done! I've sent the {contract.name} to {contact.name} "
                f"({request.contact_role}) at {contact.email} for {prop.address}."
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
            raise HTTPException(status_code=500, detail=f"Failed to send contract: {str(e)}")

    async def smart_send(self, request: ContractSmartSendRequest) -> ContractSmartSendResponse:
        # 1. Find property
        query = request.address_query.lower()
        prop = self.db.query(Property).filter(Property.address.ilike(f"%{query}%")).first()
        if not prop:
            raise HTTPException(
                status_code=404,
                detail=f"No property found matching '{request.address_query}'. Please add the property first.",
            )

        # 2. Find or create contract
        contract_name_lower = request.contract_name.lower()
        contract = (
            self.db.query(Contract)
            .filter(
                Contract.property_id == prop.id,
                Contract.name.ilike(f"%{contract_name_lower}%"),
            )
            .first()
        )

        if not contract and request.create_if_missing:
            template = self.db.query(ContractTemplate).filter(
                ContractTemplate.name.ilike(f"%{contract_name_lower}%"),
                ContractTemplate.is_active == True,
            ).first()

            contract = Contract(
                property_id=prop.id,
                name=request.contract_name.title(),
                description=f"Auto-created via smart send for {prop.address}",
                docuseal_template_id=template.docuseal_template_id if template else None,
                status=ContractStatus.DRAFT,
            )
            self.db.add(contract)
            self.db.commit()
            self.db.refresh(contract)

        if not contract:
            raise HTTPException(
                status_code=404,
                detail=f"No contract matching '{request.contract_name}' found for {prop.address}. Set create_if_missing=true to auto-create.",
            )

        # 3. Determine required signer roles
        roles = get_required_roles(contract, self.db)
        if not roles:
            raise HTTPException(
                status_code=400,
                detail=f"No signer roles configured for '{contract.name}'. "
                       f"Set required_signer_roles on the contract template, or specify contact roles manually with /voice/send-multi-party.",
            )

        # 4. Find contacts for those roles
        found_contacts, missing_roles = find_contacts_for_roles(self.db, prop.id, roles)

        if not found_contacts:
            missing_list = ", ".join(missing_roles)
            raise HTTPException(
                status_code=400,
                detail=f"Can't send {contract.name} - missing all required contacts: {missing_list}. Add them first.",
            )

        if missing_roles:
            missing_list = ", ".join(missing_roles)
            raise HTTPException(
                status_code=400,
                detail=f"Can't send {contract.name} - missing: {missing_list}. Add the missing contact(s) first.",
            )

        # 5. DocuSeal template check
        if not contract.docuseal_template_id:
            raise HTTPException(
                status_code=400,
                detail=f"Contract '{contract.name}' doesn't have a DocuSeal template ID. Please set one first.",
            )

        # 6. Build submitters and send via multi-party
        submitters = build_submitters(found_contacts)
        multi_party_request = MultiPartyContractRequest(
            submitters=submitters,
            order=request.order,
            message=request.message,
        )

        result = await self.send_multi_party(contract.id, multi_party_request)

        # 7. Voice response
        signer_parts = []
        for entry in found_contacts:
            c = entry["contact"]
            role = entry["role_str"]
            signer_parts.append(f"{c.name} ({role})")

        signers_text = _format_signers_text(signer_parts)
        voice_confirmation = f"Sent the {contract.name} to {signers_text} for {prop.address}."

        # Memory
        context = get_context(request.session_id)
        context.set_last_property(prop.id, prop.address)
        context.set_last_contract(contract.id, contract.name)
        memory_graph_service.remember_property(
            db=self.db,
            session_id=request.session_id,
            property_id=prop.id,
            address=prop.address,
            city=prop.city,
            state=prop.state,
        )
        memory_graph_service.remember_contract(
            db=self.db,
            session_id=request.session_id,
            contract_id=contract.id,
            name=contract.name,
            status=contract.status.value if contract.status else None,
            property_id=prop.id,
        )
        for entry in found_contacts:
            contact_entry = entry["contact"]
            memory_graph_service.remember_contact(
                db=self.db,
                session_id=request.session_id,
                contact_id=contact_entry.id,
                name=contact_entry.name,
                role=entry["role_str"],
                property_id=prop.id,
            )
        persist_context_to_graph(db=self.db, session_id=request.session_id)
        self.db.commit()

        return ContractSmartSendResponse(
            contract_id=contract.id,
            contract_name=contract.name,
            property_address=prop.address,
            submitters=[
                {"name": e["contact"].name, "email": e["contact"].email, "role": e["role_str"]}
                for e in found_contacts
            ],
            missing_roles=[],
            voice_confirmation=voice_confirmation,
            docuseal_url=result.docuseal_url,
        )

    async def send_multi_party_voice(
        self, request: MultiPartyVoiceRequest
    ) -> MultiPartyContractResponse:
        # 1. Find property
        query = request.address_query.lower()
        prop = self.db.query(Property).filter(Property.address.ilike(f"%{query}%")).first()
        if not prop:
            raise HTTPException(
                status_code=404,
                detail=f"No property found matching '{request.address_query}'",
            )

        # 2. Find contract
        contract_name_lower = request.contract_name.lower()
        contract = (
            self.db.query(Contract)
            .filter(
                Contract.property_id == prop.id,
                Contract.name.ilike(f"%{contract_name_lower}%"),
            )
            .first()
        )
        if not contract:
            raise HTTPException(
                status_code=404,
                detail=f"No contract found with name '{request.contract_name}' for {prop.address}",
            )
        if not contract.docuseal_template_id:
            raise HTTPException(
                status_code=400,
                detail=f"Contract '{contract.name}' doesn't have a DocuSeal template ID",
            )

        # 3. Resolve contacts for each role
        submitters = []
        for i, role_input in enumerate(request.contact_roles, 1):
            role_lower = role_input.lower().strip()

            if role_lower == "agent":
                agent = prop.agent
                submitters.append(SubmitterInput(
                    name=agent.name,
                    email=agent.email,
                    role="Agent",
                    signing_order=i,
                ))
                continue

            contact_role = MULTI_PARTY_ROLE_ALIASES.get(role_lower)
            if not contact_role:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown contact role: '{role_input}'",
                )

            contact = (
                self.db.query(Contact)
                .filter(Contact.property_id == prop.id, Contact.role == contact_role)
                .first()
            )
            if not contact:
                raise HTTPException(
                    status_code=404,
                    detail=f"No {role_input} found for {prop.address}",
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

        # 4. Send via multi-party
        multi_party_request = MultiPartyContractRequest(
            submitters=submitters,
            order=request.order,
            message=request.message,
        )

        result = await self.send_multi_party(contract.id, multi_party_request)

        # Memory
        context = get_context(request.session_id)
        context.set_last_property(prop.id, prop.address)
        context.set_last_contract(contract.id, contract.name)
        memory_graph_service.remember_property(
            db=self.db,
            session_id=request.session_id,
            property_id=prop.id,
            address=prop.address,
            city=prop.city,
            state=prop.state,
        )
        memory_graph_service.remember_contract(
            db=self.db,
            session_id=request.session_id,
            contract_id=contract.id,
            name=contract.name,
            status=contract.status.value if contract.status else None,
            property_id=prop.id,
        )
        for submitter in result.submitters:
            if submitter.contact_id is not None:
                memory_graph_service.remember_contact(
                    db=self.db,
                    session_id=request.session_id,
                    contact_id=submitter.contact_id,
                    name=submitter.name,
                    role=submitter.role,
                    property_id=prop.id,
                )
        persist_context_to_graph(db=self.db, session_id=request.session_id)
        self.db.commit()
        return result

    async def send_multi_party(
        self, contract_id: int, request: MultiPartyContractRequest
    ) -> MultiPartyContractResponse:
        contract = self._get_contract_or_404(contract_id)
        self._require_docuseal_template(contract)

        try:
            docuseal_submitters = []
            contract_submitters = []

            # Batch-load all referenced contacts to avoid N+1 queries
            contact_ids = [s.contact_id for s in request.submitters if s.contact_id]
            contacts_by_id = {}
            if contact_ids:
                contacts_list = self.db.query(Contact).filter(
                    Contact.id.in_(contact_ids)
                ).all()
                contacts_by_id = {c.id: c for c in contacts_list}

            for idx, submitter_input in enumerate(request.submitters, 1):
                if submitter_input.contact_id:
                    contact = contacts_by_id.get(submitter_input.contact_id)
                    if not contact:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Contact {submitter_input.contact_id} not found",
                        )
                    if not contact.email:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Contact {contact.name} doesn't have an email address",
                        )
                    name = contact.name
                    email = contact.email
                else:
                    name = submitter_input.name
                    email = submitter_input.email

                docuseal_submitters.append({
                    "name": name,
                    "email": email,
                    "role": submitter_input.role,
                })

                contract_submitter = ContractSubmitter(
                    contract_id=contract.id,
                    contact_id=submitter_input.contact_id,
                    name=name,
                    email=email,
                    role=submitter_input.role,
                    signing_order=submitter_input.signing_order,
                    status=SubmitterStatus.PENDING,
                )
                self.db.add(contract_submitter)
                contract_submitters.append(contract_submitter)

            docuseal_response = await docuseal_client.create_submission(
                template_id=contract.docuseal_template_id,
                submitters=docuseal_submitters,
                send_email=True,
                order=request.order,
                message=request.message,
            )

            contract.docuseal_submission_id = str(docuseal_response["id"])
            contract.docuseal_url = docuseal_response.get("submission_url")
            contract.status = ContractStatus.SENT
            contract.sent_at = datetime.now()

            docuseal_submitters_response = docuseal_response.get("submitters", [])
            for i, cs in enumerate(contract_submitters):
                if i < len(docuseal_submitters_response):
                    ds = docuseal_submitters_response[i]
                    cs.docuseal_submitter_id = str(ds.get("id"))
                    cs.docuseal_submitter_slug = ds.get("slug")
                    cs.sent_at = datetime.now()

            self.db.commit()

            for submitter in contract_submitters:
                self.db.refresh(submitter)

            # Resend notification emails
            resend_submitters = []
            for i, cs in enumerate(contract_submitters):
                ds = docuseal_submitters_response[i] if i < len(docuseal_submitters_response) else {}
                resend_submitters.append({
                    "name": cs.name,
                    "email": cs.email,
                    "role": cs.role,
                    "docuseal_url": ds.get("embed_src", contract.docuseal_url),
                    "signing_order": cs.signing_order,
                })

            await resend_service.send_multi_party_notification(
                submitters=resend_submitters,
                contract_name=contract.name,
                property_address=contract.property.address,
                is_sequential=(request.order == "preserved"),
                custom_message=request.message,
            )

            # Voice confirmation
            signer_names = [s.name for s in contract_submitters]
            signers_text = _format_signers_text(signer_names) if signer_names else "signers"
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
            raise HTTPException(status_code=500, detail=f"Failed to send contract: {str(e)}")

    # ------------------------------------------------------------------
    # Webhook handlers
    # ------------------------------------------------------------------

    async def handle_webhook(self, payload: dict) -> dict:
        try:
            event_type = payload.get("event_type", "")
            data = payload.get("data", payload)

            if event_type.startswith("form."):
                return await self._handle_form_event(event_type, data)
            elif event_type.startswith("submission."):
                return await self._handle_submission_event(event_type, data)
            else:
                return await self._handle_legacy_webhook(data)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _handle_form_event(self, event_type: str, data: dict) -> dict:
        submission_id = str(data.get("submission_id") or data.get("id", ""))
        submitter_id = str(data.get("submitter_id") or data.get("id", ""))

        contract = self.db.query(Contract).filter(
            Contract.docuseal_submission_id == submission_id
        ).first()
        if not contract:
            return {"status": "ignored", "message": "Contract not found"}

        contract_submitter = self.db.query(ContractSubmitter).filter(
            ContractSubmitter.contract_id == contract.id,
            ContractSubmitter.docuseal_submitter_id == submitter_id,
        ).first()
        if not contract_submitter:
            return {"status": "ignored", "message": "Submitter not found"}

        updated = False
        if event_type == "form.viewed":
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

            all_submitters = self.db.query(ContractSubmitter).filter(
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
            contract.status = ContractStatus.CANCELLED
            updated = True

        if updated:
            self.db.commit()

        return {
            "status": "success",
            "event": event_type,
            "contract_id": contract.id,
            "submitter": contract_submitter.name,
            "submitter_status": contract_submitter.status.value,
        }

    async def _handle_submission_event(self, event_type: str, data: dict) -> dict:
        submission_id = str(data.get("id", ""))

        contract = self.db.query(Contract).filter(
            Contract.docuseal_submission_id == submission_id
        ).first()
        if not contract:
            return {"status": "ignored", "message": "Contract not found"}

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

            submitters = self.db.query(ContractSubmitter).filter(
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
            self.db.commit()

        return {
            "status": "success",
            "event": event_type,
            "contract_id": contract.id,
            "contract_status": contract.status.value,
        }

    async def _handle_legacy_webhook(self, data: dict) -> dict:
        submission_id = str(data.get("id"))
        status = data.get("status", "").lower()
        submitters_data = data.get("submitters", [])

        contract = self.db.query(Contract).filter(
            Contract.docuseal_submission_id == submission_id
        ).first()
        if not contract:
            return {"status": "ignored", "message": "Contract not found"}

        # Batch-load all submitters for this contract to avoid N+1 queries
        all_contract_submitters = self.db.query(ContractSubmitter).filter(
            ContractSubmitter.contract_id == contract.id
        ).all()
        submitter_by_docuseal_id = {
            s.docuseal_submitter_id: s for s in all_contract_submitters
            if s.docuseal_submitter_id
        }

        updated_submitters = []
        for submitter_data in submitters_data:
            docuseal_submitter_id = str(submitter_data.get("id"))
            submitter_status = submitter_data.get("status", "").lower()

            contract_submitter = submitter_by_docuseal_id.get(docuseal_submitter_id)

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
                    "status": contract_submitter.status.value,
                })

        if status == "completed":
            contract.status = ContractStatus.COMPLETED
            if not contract.completed_at:
                contract.completed_at = datetime.now()
        elif status == "pending":
            contract.status = ContractStatus.IN_PROGRESS
        elif status == "archived":
            contract.status = ContractStatus.CANCELLED

        self.db.commit()

        return {
            "status": "success",
            "contract_id": contract.id,
            "contract_status": contract.status.value,
            "submitters_updated": updated_submitters,
        }

    # ------------------------------------------------------------------
    # Auto-attach & requirements
    # ------------------------------------------------------------------

    def auto_attach(self, property_id: int) -> dict:
        prop = self._get_property_or_404(property_id)
        attached_contracts = contract_auto_attach_service.auto_attach_contracts(self.db, prop)

        return {
            "property_id": property_id,
            "property_address": prop.address,
            "contracts_attached": len(attached_contracts),
            "contracts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "status": c.status.value,
                }
                for c in attached_contracts
            ],
        }

    def get_required_status(self, property_id: int) -> dict:
        prop = self._get_property_or_404(property_id)
        status = contract_auto_attach_service.get_required_contracts_status(self.db, prop)

        return {
            "property_id": property_id,
            "property_address": prop.address,
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
                    "category": t.category.value,
                }
                for t in status["missing_templates"]
            ],
            "incomplete_contracts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status.value,
                    "sent_at": c.sent_at,
                }
                for c in status["incomplete_contracts"]
            ],
        }

    def get_signing_status(self, property_id: int) -> dict:
        prop = self._get_property_or_404(property_id)

        contracts = self.db.query(Contract).filter(Contract.property_id == property_id).all()
        submitters = (
            self.db.query(ContractSubmitter)
            .filter(ContractSubmitter.contract_id.in_([c.id for c in contracts]))
            .all()
            if contracts
            else []
        )

        contract_signing = []
        total_signed = 0
        total_pending = 0
        pending_names = []

        for contract in contracts:
            contract_submitters = [s for s in submitters if s.contract_id == contract.id]
            signed = [s for s in contract_submitters if s.status.value == "completed"]
            waiting = [s for s in contract_submitters if s.status.value != "completed"]

            total_signed += len(signed)
            total_pending += len(waiting)

            for s in waiting:
                if s.name not in pending_names:
                    pending_names.append(s.name)

            contract_signing.append({
                "contract_id": contract.id,
                "contract_name": contract.name,
                "contract_status": contract.status.value,
                "signers": [
                    {
                        "name": s.name,
                        "role": s.role,
                        "email": s.email,
                        "status": s.status.value,
                        "signing_order": s.signing_order,
                        "sent_at": s.sent_at.isoformat() if s.sent_at else None,
                        "opened_at": s.opened_at.isoformat() if s.opened_at else None,
                        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    }
                    for s in contract_submitters
                ],
                "signed_count": len(signed),
                "pending_count": len(waiting),
            })

        # Voice summary
        if not submitters:
            voice_summary = f"No contracts have been sent for signing yet for {prop.address}."
        elif total_pending == 0:
            voice_summary = f"All {total_signed} signers have completed across {len(contracts)} contracts for {prop.address}."
        else:
            names_text = _format_signers_text(pending_names)
            voice_summary = (
                f"{total_signed} of {total_signed + total_pending} signers have completed "
                f"for {prop.address}. Still waiting on {names_text}."
            )

        return {
            "property_id": property_id,
            "property_address": prop.address,
            "total_signers": total_signed + total_pending,
            "signed": total_signed,
            "pending": total_pending,
            "pending_names": pending_names,
            "all_signed": total_pending == 0 and total_signed > 0,
            "contracts": contract_signing,
            "voice_summary": voice_summary,
        }

    def get_missing_contracts(
        self, property_id: int, required_only: bool = False
    ) -> dict:
        prop = self._get_property_or_404(property_id)
        requirement_filter = ContractRequirement.REQUIRED if required_only else None
        missing = contract_auto_attach_service.get_missing_contracts(
            self.db, prop, requirement=requirement_filter
        )

        return {
            "property_id": property_id,
            "property_address": prop.address,
            "missing_count": len(missing),
            "missing_contracts": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "category": t.category.value,
                    "requirement": t.requirement.value,
                    "docuseal_template_id": t.docuseal_template_id,
                }
                for t in missing
            ],
        }

    def check_contracts_voice(self, address_query: str) -> dict:
        query = address_query.lower()
        prop = self.db.query(Property).filter(Property.address.ilike(f"%{query}%")).first()
        if not prop:
            raise HTTPException(
                status_code=404,
                detail=f"No property found matching '{address_query}'",
            )

        status = contract_auto_attach_service.get_required_contracts_status(self.db, prop)

        if status["is_ready_to_close"]:
            voice_response = (
                f"Great news! {prop.address} has all {status['total_required']} "
                f"required contracts completed. The property is ready to close."
            )
        else:
            voice_response = f"Contract status for {prop.address}:\n"
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
            "property_address": prop.address,
            "is_ready_to_close": status["is_ready_to_close"],
            "total_required": status["total_required"],
            "completed": status["completed"],
            "in_progress": status["in_progress"],
            "missing": status["missing"],
            "voice_response": voice_response,
        }

    # ------------------------------------------------------------------
    # AI suggestions
    # ------------------------------------------------------------------

    async def ai_suggest(self, property_id: int) -> dict:
        prop = self._get_property_or_404(property_id)
        return await contract_ai_service.suggest_required_contracts(self.db, prop)

    async def ai_apply_suggestions(
        self, property_id: int, only_required: bool = True
    ) -> dict:
        prop = self._get_property_or_404(property_id)

        suggestions = await contract_ai_service.suggest_required_contracts(self.db, prop)

        existing_contracts = self.db.query(Contract).filter(
            Contract.property_id == property_id
        ).all()
        existing_names = {c.name.lower() for c in existing_contracts}

        created_contracts = []

        for suggestion in suggestions.get("required_contracts", []):
            template_id = suggestion.get("template_id")
            contract_name = suggestion.get("name")
            reason = suggestion.get("reason")

            if contract_name.lower() in existing_names:
                continue

            template = self.db.query(ContractTemplate).filter(
                ContractTemplate.id == template_id
            ).first()

            if template:
                contract = Contract(
                    property_id=property_id,
                    name=template.name,
                    description=template.description,
                    docuseal_template_id=template.docuseal_template_id,
                    is_required=True,
                    requirement_source=RequirementSource.AI_SUGGESTED,
                    requirement_reason=reason,
                    status=ContractStatus.DRAFT,
                )
                self.db.add(contract)
                created_contracts.append(contract)

        if not only_required:
            for suggestion in suggestions.get("optional_contracts", []):
                template_id = suggestion.get("template_id")
                contract_name = suggestion.get("name")
                reason = suggestion.get("reason")

                if contract_name.lower() in existing_names:
                    continue

                template = self.db.query(ContractTemplate).filter(
                    ContractTemplate.id == template_id
                ).first()

                if template:
                    contract = Contract(
                        property_id=property_id,
                        name=template.name,
                        description=template.description,
                        docuseal_template_id=template.docuseal_template_id,
                        is_required=False,
                        requirement_source=RequirementSource.AI_SUGGESTED,
                        requirement_reason=reason,
                        status=ContractStatus.DRAFT,
                    )
                    self.db.add(contract)
                    created_contracts.append(contract)

        self.db.commit()
        for contract in created_contracts:
            self.db.refresh(contract)

        return {
            "property_id": property_id,
            "property_address": prop.address,
            "contracts_created": len(created_contracts),
            "ai_summary": suggestions.get("summary"),
            "contracts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "is_required": c.is_required,
                    "requirement_reason": c.requirement_reason,
                }
                for c in created_contracts
            ],
        }

    async def ai_analyze_gaps(self, property_id: int) -> dict:
        prop = self._get_property_or_404(property_id)
        return await contract_ai_service.analyze_contract_gaps(self.db, prop)

    # ------------------------------------------------------------------
    # Manual requirement management
    # ------------------------------------------------------------------

    def mark_required(
        self,
        contract_id: int,
        is_required: bool = True,
        reason: Optional[str] = None,
        required_by_date: Optional[str] = None,
    ) -> dict:
        contract = self._get_contract_or_404(contract_id)

        contract.is_required = is_required
        contract.requirement_source = RequirementSource.MANUAL

        if reason:
            contract.requirement_reason = reason
        if required_by_date:
            contract.required_by_date = datetime.fromisoformat(required_by_date)

        self.db.commit()
        self.db.refresh(contract)

        return {
            "contract_id": contract.id,
            "name": contract.name,
            "is_required": contract.is_required,
            "requirement_source": contract.requirement_source.value,
            "requirement_reason": contract.requirement_reason,
            "required_by_date": contract.required_by_date,
        }

    def set_required_for_property(
        self,
        property_id: int,
        contract_ids: List[int],
        mark_all_others_optional: bool = False,
    ) -> dict:
        prop = self._get_property_or_404(property_id)

        all_contracts = self.db.query(Contract).filter(
            Contract.property_id == property_id
        ).all()

        updated_contracts = []
        for contract in all_contracts:
            if contract.id in contract_ids:
                contract.is_required = True
                contract.requirement_source = RequirementSource.MANUAL
                updated_contracts.append({"id": contract.id, "name": contract.name, "is_required": True})
            elif mark_all_others_optional:
                contract.is_required = False
                contract.requirement_source = RequirementSource.MANUAL
                updated_contracts.append({"id": contract.id, "name": contract.name, "is_required": False})

        self.db.commit()

        return {
            "property_id": property_id,
            "property_address": prop.address,
            "updated_count": len(updated_contracts),
            "contracts": updated_contracts,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_contract_or_404(self, contract_id: int) -> Contract:
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        return contract

    def _get_property_or_404(self, property_id: int) -> Property:
        prop = self.db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")
        return prop

    def _require_docuseal_template(self, contract: Contract) -> None:
        if not contract.docuseal_template_id:
            raise HTTPException(
                status_code=400,
                detail="Contract must have a DocuSeal template ID before sending",
            )


def get_contract_service(db: Session = Depends(get_db)) -> ContractService:
    return ContractService(db)
