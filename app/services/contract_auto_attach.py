"""
Contract Auto-Attach Service

Automatically attaches required contracts to properties based on
configured templates.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.models.property import Property
from app.models.contract import Contract, ContractStatus
from app.models.contract_template import ContractTemplate, ContractRequirement

logger = logging.getLogger(__name__)


class ContractAutoAttachService:
    """Service for automatically attaching contracts to properties"""

    def get_applicable_templates(
        self,
        db: Session,
        property: Property
    ) -> List[ContractTemplate]:
        """
        Get all contract templates that apply to a property.

        Returns templates sorted by priority (highest first).
        """
        # Get all active templates
        all_templates = db.query(ContractTemplate).filter(
            ContractTemplate.is_active == True
        ).all()

        # Filter to applicable templates
        applicable = []
        for template in all_templates:
            if template.applies_to_property(property):
                applicable.append(template)

        # Sort by priority (highest first)
        applicable.sort(key=lambda t: t.priority, reverse=True)

        return applicable

    def auto_attach_contracts(
        self,
        db: Session,
        property: Property
    ) -> List[Contract]:
        """
        Automatically attach applicable contracts to a property.

        Called when:
        1. Property is created
        2. Property is updated (state/price/type changed)
        3. Manually triggered by user

        Returns list of created contracts.
        """
        templates = self.get_applicable_templates(db, property)

        # Filter to templates with auto_attach enabled
        auto_attach_templates = [
            t for t in templates
            if t.auto_attach_on_create
        ]

        created_contracts = []

        for template in auto_attach_templates:
            # Check if contract already exists for this template
            existing = db.query(Contract).filter(
                Contract.property_id == property.id,
                Contract.name == template.name
            ).first()

            if existing:
                logger.info(
                    f"Contract '{template.name}' already exists for property {property.id}, skipping"
                )
                continue

            # Create contract
            contract = Contract(
                property_id=property.id,
                name=template.name,
                description=template.description,
                docuseal_template_id=template.docuseal_template_id,
                status=ContractStatus.DRAFT
            )

            db.add(contract)
            created_contracts.append(contract)

            logger.info(
                f"Auto-attached contract '{template.name}' to property {property.id}"
            )

        if created_contracts:
            db.commit()

            # Refresh all contracts
            for contract in created_contracts:
                db.refresh(contract)

        return created_contracts

    def get_missing_contracts(
        self,
        db: Session,
        property: Property,
        requirement: Optional[ContractRequirement] = None
    ) -> List[ContractTemplate]:
        """
        Get list of contract templates that should be attached
        to this property but aren't yet.

        Args:
            property: Property to check
            requirement: Filter by requirement level (e.g., only REQUIRED)

        Returns list of missing templates.
        """
        # Get all applicable templates
        applicable = self.get_applicable_templates(db, property)

        # Filter by requirement if specified
        if requirement:
            applicable = [t for t in applicable if t.requirement == requirement]

        # Get existing contracts for property
        existing_contracts = db.query(Contract).filter(
            Contract.property_id == property.id
        ).all()

        existing_names = {c.name.lower() for c in existing_contracts}

        # Find missing templates
        missing = []
        for template in applicable:
            if template.name.lower() not in existing_names:
                missing.append(template)

        return missing

    def get_required_contracts_status(
        self,
        db: Session,
        property: Property
    ) -> dict:
        """
        Get status of all required contracts for a property.

        Returns:
        {
            "total_required": 5,
            "completed": 3,
            "in_progress": 1,
            "missing": 1,
            "is_ready_to_close": False,
            "missing_templates": [...],
            "incomplete_contracts": [...]
        }
        """
        # Get all required templates
        required_templates = self.get_applicable_templates(db, property)
        required_templates = [
            t for t in required_templates
            if t.requirement == ContractRequirement.REQUIRED
        ]

        # Get existing contracts
        existing_contracts = db.query(Contract).filter(
            Contract.property_id == property.id
        ).all()

        # Map contracts by name
        contract_map = {c.name.lower(): c for c in existing_contracts}

        completed = []
        in_progress = []
        missing_templates = []

        for template in required_templates:
            contract = contract_map.get(template.name.lower())

            if not contract:
                # Missing contract
                missing_templates.append(template)
            elif contract.status == ContractStatus.COMPLETED:
                completed.append(contract)
            else:
                in_progress.append(contract)

        is_ready_to_close = (
            len(missing_templates) == 0 and
            len(in_progress) == 0 and
            len(completed) == len(required_templates)
        )

        return {
            "total_required": len(required_templates),
            "completed": len(completed),
            "in_progress": len(in_progress),
            "missing": len(missing_templates),
            "is_ready_to_close": is_ready_to_close,
            "missing_templates": missing_templates,
            "incomplete_contracts": in_progress,
            "completed_contracts": completed
        }


# Singleton instance
contract_auto_attach_service = ContractAutoAttachService()
