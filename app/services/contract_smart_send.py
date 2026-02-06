"""
Smart Contract Send Service

Automatically determines which contacts need to sign a contract
based on the contract template's required_signer_roles or a default role map.

Example: "Send the purchase agreement for 123 Main St"
  -> System knows Purchase Agreement needs buyer + seller
  -> Finds those contacts on the property
  -> Sends to both with correct signing order
"""
from difflib import get_close_matches
from sqlalchemy.orm import Session

from app.models.contact import Contact, ContactRole
from app.models.contract import Contract, ContractStatus
from app.models.contract_template import ContractTemplate
from app.schemas.contract_submitter import SubmitterInput


# Default role mapping - fallback when template doesn't specify roles
DEFAULT_ROLE_MAP = {
    "Purchase Agreement": ["buyer", "seller"],
    "Inspection Report": ["inspector"],
    "Disclosure Form": ["seller"],
    "Title Insurance": ["title_company"],
    "Loan Documents": ["buyer", "lender"],
    "Lease Agreement": ["tenant", "landlord"],
    "Property Condition Disclosure": ["seller"],
    "Lead Paint Disclosure": ["seller", "buyer"],
    "Seller Disclosure": ["seller"],
    "Buyer Agency Agreement": ["buyer"],
    "Listing Agreement": ["seller"],
}

# Map role strings to ContactRole enum values
ROLE_STRING_TO_ENUM = {
    "buyer": ContactRole.BUYER,
    "seller": ContactRole.SELLER,
    "lawyer": ContactRole.LAWYER,
    "attorney": ContactRole.ATTORNEY,
    "contractor": ContactRole.CONTRACTOR,
    "inspector": ContactRole.INSPECTOR,
    "appraiser": ContactRole.APPRAISER,
    "lender": ContactRole.LENDER,
    "mortgage_broker": ContactRole.MORTGAGE_BROKER,
    "title_company": ContactRole.TITLE_COMPANY,
    "tenant": ContactRole.TENANT,
    "landlord": ContactRole.LANDLORD,
}


def get_required_roles(contract: Contract, db: Session) -> list[str] | None:
    """
    Determine which roles need to sign this contract.

    Priority:
    1. Template's required_signer_roles (if contract has a matching template)
    2. DEFAULT_ROLE_MAP fuzzy match on contract name
    3. None (no roles configured)
    """
    # 1. Check if there's a matching template with required_signer_roles
    if contract.docuseal_template_id:
        template = db.query(ContractTemplate).filter(
            ContractTemplate.docuseal_template_id == contract.docuseal_template_id,
            ContractTemplate.is_active == True,
        ).first()
        if template and template.required_signer_roles:
            return template.required_signer_roles

    # Also try matching by name
    template = db.query(ContractTemplate).filter(
        ContractTemplate.name.ilike(f"%{contract.name}%"),
        ContractTemplate.is_active == True,
    ).first()
    if template and template.required_signer_roles:
        return template.required_signer_roles

    # 2. Fallback to DEFAULT_ROLE_MAP with fuzzy matching
    contract_name = contract.name.strip()

    # Exact match first (case-insensitive)
    for map_name, roles in DEFAULT_ROLE_MAP.items():
        if map_name.lower() == contract_name.lower():
            return roles

    # Fuzzy match
    map_names = list(DEFAULT_ROLE_MAP.keys())
    matches = get_close_matches(contract_name, map_names, n=1, cutoff=0.6)
    if matches:
        return DEFAULT_ROLE_MAP[matches[0]]

    # 3. No roles found
    return None


def find_contacts_for_roles(
    db: Session, property_id: int, roles: list[str]
) -> tuple[list[dict], list[str]]:
    """
    Find contacts for the given roles on a property.

    Returns:
        (found_contacts, missing_roles)
        found_contacts: [{contact: Contact, role_str: str}]
        missing_roles: ["seller", "inspector"] - roles with no matching contact
    """
    found = []
    missing = []

    for role_str in roles:
        role_enum = ROLE_STRING_TO_ENUM.get(role_str.lower())
        if not role_enum:
            missing.append(role_str)
            continue

        # Find the most recent contact with this role for the property
        contact = (
            db.query(Contact)
            .filter(
                Contact.property_id == property_id,
                Contact.role == role_enum,
            )
            .order_by(Contact.created_at.desc())
            .first()
        )

        if not contact:
            missing.append(role_str)
        elif not contact.email:
            missing.append(f"{role_str} (no email for {contact.name})")
        else:
            found.append({"contact": contact, "role_str": role_str})

    return found, missing


def build_submitters(contacts: list[dict]) -> list[SubmitterInput]:
    """
    Build SubmitterInput list from found contacts with signing order.

    Args:
        contacts: [{contact: Contact, role_str: str}]

    Returns:
        List of SubmitterInput with sequential signing order
    """
    submitters = []
    for i, entry in enumerate(contacts, 1):
        contact = entry["contact"]
        submitters.append(
            SubmitterInput(
                contact_id=contact.id,
                name=contact.name,
                email=contact.email,
                role=entry["role_str"].replace("_", " ").title(),
                signing_order=i,
            )
        )
    return submitters
