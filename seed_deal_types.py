#!/usr/bin/env python3
"""
Seed built-in deal type configs.
Run: python seed_deal_types.py
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.deal_type_config import DealTypeConfig

BUILTIN_CONFIGS = [
    {
        "name": "traditional",
        "display_name": "Traditional",
        "description": "Standard purchase/sale transaction",
        "contract_templates": [
            "Purchase Agreement",
            "Property Disclosure",
            "Lead Paint Disclosure",
        ],
        "required_contact_roles": ["buyer", "seller"],
        "checklist": [
            {"title": "Schedule home inspection", "description": "Arrange professional home inspection", "priority": "high", "due_days": 10},
            {"title": "Order appraisal", "description": "Lender orders property appraisal", "priority": "high", "due_days": 14},
            {"title": "Review title report", "description": "Review title search for liens or issues", "priority": "medium", "due_days": 21},
            {"title": "Final walkthrough", "description": "Buyer does final walkthrough before closing", "priority": "high", "due_days": 28},
        ],
        "compliance_tags": ["title_search", "disclosure_required"],
    },
    {
        "name": "short_sale",
        "display_name": "Short Sale",
        "description": "Bank-approved sale below market value — requires lender approval",
        "contract_templates": [
            "Purchase Agreement",
            "Short Sale Addendum",
            "Property Disclosure",
        ],
        "required_contact_roles": ["buyer", "seller", "lender"],
        "checklist": [
            {"title": "Obtain hardship letter", "description": "Seller provides hardship letter to lender", "priority": "high", "due_days": 7},
            {"title": "Submit offer to bank", "description": "Send purchase offer package to seller's lender", "priority": "high", "due_days": 10},
            {"title": "Follow up with bank weekly", "description": "Call bank weekly for status updates", "priority": "medium", "due_days": 14},
            {"title": "Request BPO", "description": "Bank orders Broker Price Opinion", "priority": "medium", "due_days": 21},
        ],
        "compliance_tags": ["bank_approval", "title_search", "disclosure_required"],
    },
    {
        "name": "reo",
        "display_name": "REO (Bank-Owned)",
        "description": "Bank-owned foreclosure property",
        "contract_templates": [
            "Purchase Agreement",
            "As-Is Addendum",
            "Lead Paint Disclosure",
        ],
        "required_contact_roles": ["buyer", "seller"],
        "checklist": [
            {"title": "Request property disclosure", "description": "Request any available disclosures from bank/asset manager", "priority": "high", "due_days": 7},
            {"title": "Order title report", "description": "Title search to check for liens from foreclosure", "priority": "high", "due_days": 10},
            {"title": "Verify occupancy status", "description": "Confirm property is vacant or arrange eviction", "priority": "high", "due_days": 5},
            {"title": "Submit offer to asset manager", "description": "Submit offer through bank's asset manager or portal", "priority": "high", "due_days": 3},
        ],
        "compliance_tags": ["title_search", "foreclosure_compliance", "as_is"],
    },
    {
        "name": "fsbo",
        "display_name": "For Sale By Owner (FSBO)",
        "description": "Seller is not represented by a listing agent",
        "contract_templates": [
            "Buyer Agency Agreement",
            "Purchase Agreement",
            "Property Disclosure",
        ],
        "required_contact_roles": ["buyer", "seller"],
        "checklist": [
            {"title": "Verify seller ownership", "description": "Confirm seller is the actual property owner via title search", "priority": "high", "due_days": 5},
            {"title": "Discuss commission structure", "description": "Clarify buyer agent commission with seller", "priority": "high", "due_days": 3},
            {"title": "Explain contract process", "description": "Walk seller through purchase agreement terms since no listing agent", "priority": "medium", "due_days": 7},
        ],
        "compliance_tags": ["title_search", "disclosure_required", "agency_disclosure"],
    },
    {
        "name": "new_construction",
        "display_name": "New Construction",
        "description": "Buying a newly built property from a builder/developer",
        "contract_templates": [
            "Purchase Agreement",
            "Builder Warranty",
        ],
        "required_contact_roles": ["buyer", "seller"],
        "checklist": [
            {"title": "Review builder contract", "description": "Have attorney review builder's purchase agreement", "priority": "high", "due_days": 7},
            {"title": "Schedule pre-drywall inspection", "description": "Inspect framing, plumbing, electrical before drywall", "priority": "high", "due_days": 14},
            {"title": "Final punch list walkthrough", "description": "Create punch list of items for builder to fix before closing", "priority": "high", "due_days": 28},
            {"title": "Verify builder warranty terms", "description": "Review structural and systems warranty coverage", "priority": "medium", "due_days": 21},
        ],
        "compliance_tags": ["builder_warranty", "new_construction_inspection"],
    },
    {
        "name": "wholesale",
        "display_name": "Wholesale",
        "description": "Assignment of contract — investor finds deal and assigns to end buyer",
        "contract_templates": [
            "Purchase Agreement",
            "Assignment of Contract",
        ],
        "required_contact_roles": ["buyer", "seller"],
        "checklist": [
            {"title": "Get property under contract", "description": "Execute purchase agreement with seller", "priority": "urgent", "due_days": 3},
            {"title": "Find end buyer", "description": "Market deal to investor buyers list", "priority": "high", "due_days": 7},
            {"title": "Execute assignment", "description": "Complete assignment of contract with end buyer", "priority": "high", "due_days": 14},
            {"title": "Coordinate double close", "description": "If not assigning, set up simultaneous closings", "priority": "medium", "due_days": 21},
        ],
        "compliance_tags": ["assignment_disclosure", "title_search"],
    },
    {
        "name": "rental",
        "display_name": "Rental",
        "description": "Lease transaction between landlord and tenant",
        "contract_templates": [
            "Lease Agreement",
        ],
        "required_contact_roles": ["tenant", "landlord"],
        "checklist": [
            {"title": "Run credit check", "description": "Run tenant credit and background check", "priority": "high", "due_days": 3},
            {"title": "Verify employment", "description": "Verify tenant employment and income", "priority": "high", "due_days": 5},
            {"title": "Collect security deposit", "description": "Collect first month rent and security deposit", "priority": "high", "due_days": 7},
            {"title": "Key handoff", "description": "Schedule move-in date and key handoff", "priority": "medium", "due_days": 10},
        ],
        "compliance_tags": ["fair_housing", "tenant_screening", "security_deposit_law"],
    },
    {
        "name": "commercial",
        "display_name": "Commercial",
        "description": "Commercial real estate transaction",
        "contract_templates": [
            "Purchase Agreement",
            "Property Disclosure",
        ],
        "required_contact_roles": ["buyer", "seller"],
        "checklist": [
            {"title": "Environmental assessment", "description": "Order Phase I environmental site assessment", "priority": "high", "due_days": 14},
            {"title": "Review zoning", "description": "Verify zoning allows intended use", "priority": "high", "due_days": 7},
            {"title": "Commercial inspection", "description": "Hire commercial property inspector", "priority": "high", "due_days": 14},
            {"title": "Review financials", "description": "Analyze rent rolls, operating expenses, NOI", "priority": "high", "due_days": 10},
        ],
        "compliance_tags": ["environmental_compliance", "zoning_verification", "commercial_disclosure"],
    },
]


def seed():
    db = SessionLocal()
    try:
        created = 0
        skipped = 0
        for config_data in BUILTIN_CONFIGS:
            existing = db.query(DealTypeConfig).filter(
                DealTypeConfig.name == config_data["name"]
            ).first()
            if existing:
                print(f"  Skipping '{config_data['name']}' (already exists)")
                skipped += 1
                continue

            config = DealTypeConfig(
                name=config_data["name"],
                display_name=config_data["display_name"],
                description=config_data["description"],
                is_builtin=True,
                is_active=True,
                contract_templates=config_data["contract_templates"],
                required_contact_roles=config_data["required_contact_roles"],
                checklist=config_data["checklist"],
                compliance_tags=config_data["compliance_tags"],
            )
            db.add(config)
            created += 1
            print(f"  Created '{config_data['name']}' ({config_data['display_name']})")

        db.commit()
        print(f"\nDone! Created {created}, skipped {skipped} (already existed).")
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding deal type configs...")
    seed()
