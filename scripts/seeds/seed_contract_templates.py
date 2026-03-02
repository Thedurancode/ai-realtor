"""
Seed Contract Templates

This script seeds the database with common contract templates
that should be auto-attached to properties.

Run this after deploying your application:
python3 scripts/seeds/seed_contract_templates.py
"""
import requests
import json

# API base URL
API_URL = "https://ai-realtor.fly.dev"
# For local testing: API_URL = "http://localhost:8000"


def create_template(template_data):
    """Create a contract template"""
    response = requests.post(
        f"{API_URL}/contract-templates/",
        json=template_data
    )
    if response.status_code == 201:
        template = response.json()
        print(f"✅ Created: {template['name']} (ID: {template['id']})")
        return template
    else:
        print(f"❌ Failed to create {template_data['name']}: {response.text}")
        return None


def seed_templates():
    """Seed all contract templates"""
    print("=" * 60)
    print("  Seeding Contract Templates")
    print("=" * 60)

    templates = [
        # ========== NEW YORK TEMPLATES ==========
        {
            "name": "NY Property Condition Disclosure Statement",
            "description": "Required disclosure form for all NY residential property sales",
            "category": "disclosure",
            "requirement": "required",
            "state": "NY",
            "property_type_filter": ["house", "condo", "townhouse"],
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "seller",
            "message_template": "Please complete the NY Property Condition Disclosure Statement for this property.",
            "is_active": True,
            "priority": 10,
            # Note: Set docuseal_template_id after creating template in DocuSeal
        },
        {
            "name": "NY Lead-Based Paint Disclosure",
            "description": "Federal requirement for properties built before 1978",
            "category": "disclosure",
            "requirement": "required",
            "state": "NY",
            "max_price": None,  # All properties
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "seller",
            "is_active": True,
            "priority": 9,
        },
        {
            "name": "NY Purchase and Sale Agreement",
            "description": "Standard NY real estate purchase contract",
            "category": "purchase",
            "requirement": "required",
            "state": "NY",
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "buyer",
            "is_active": True,
            "priority": 10,
        },

        # ========== CALIFORNIA TEMPLATES ==========
        {
            "name": "CA Transfer Disclosure Statement (TDS)",
            "description": "Required for 1-4 unit residential properties in California",
            "category": "disclosure",
            "requirement": "required",
            "state": "CA",
            "property_type_filter": ["house", "condo", "townhouse"],
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "seller",
            "is_active": True,
            "priority": 10,
        },
        {
            "name": "CA Natural Hazard Disclosure Statement",
            "description": "Required disclosure for properties in hazard zones",
            "category": "disclosure",
            "requirement": "required",
            "state": "CA",
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "seller",
            "is_active": True,
            "priority": 9,
        },
        {
            "name": "CA Residential Purchase Agreement",
            "description": "Standard California real estate purchase contract",
            "category": "purchase",
            "requirement": "required",
            "state": "CA",
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "buyer",
            "is_active": True,
            "priority": 10,
        },

        # ========== FLORIDA TEMPLATES ==========
        {
            "name": "FL Seller's Property Disclosure",
            "description": "Voluntary but recommended seller disclosure form",
            "category": "disclosure",
            "requirement": "recommended",
            "state": "FL",
            "property_type_filter": ["house", "condo", "townhouse"],
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "seller",
            "is_active": True,
            "priority": 8,
        },
        {
            "name": "FL Homeowners Association Disclosure",
            "description": "Required for properties with HOA",
            "category": "disclosure",
            "requirement": "required",
            "state": "FL",
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "seller",
            "is_active": True,
            "priority": 9,
        },
        {
            "name": "FL Residential Purchase Agreement",
            "description": "Standard Florida real estate purchase contract",
            "category": "purchase",
            "requirement": "required",
            "state": "FL",
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "buyer",
            "is_active": True,
            "priority": 10,
        },

        # ========== TEXAS TEMPLATES ==========
        {
            "name": "TX Seller's Disclosure Notice",
            "description": "Required disclosure for all TX residential properties",
            "category": "disclosure",
            "requirement": "required",
            "state": "TX",
            "property_type_filter": ["house", "condo", "townhouse"],
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "seller",
            "is_active": True,
            "priority": 10,
        },
        {
            "name": "TX Residential Purchase Contract",
            "description": "Standard Texas real estate purchase contract",
            "category": "purchase",
            "requirement": "required",
            "state": "TX",
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "buyer",
            "is_active": True,
            "priority": 10,
        },

        # ========== UNIVERSAL TEMPLATES ==========
        {
            "name": "Home Inspection Contingency Addendum",
            "description": "Standard inspection contingency for purchase agreements",
            "category": "addendum",
            "requirement": "recommended",
            "state": None,  # Applies to all states
            "auto_attach_on_create": False,
            "auto_send": False,
            "default_recipient_role": "buyer",
            "is_active": True,
            "priority": 5,
        },
        {
            "name": "Financing Contingency Addendum",
            "description": "Financing contingency for purchase agreements",
            "category": "addendum",
            "requirement": "recommended",
            "state": None,  # Applies to all states
            "auto_attach_on_create": False,
            "auto_send": False,
            "default_recipient_role": "buyer",
            "is_active": True,
            "priority": 5,
        },
        {
            "name": "Lead-Based Paint Disclosure (Federal)",
            "description": "Federal requirement for all properties built before 1978",
            "category": "disclosure",
            "requirement": "required",
            "state": None,  # Applies to all states
            "auto_attach_on_create": True,
            "auto_send": False,
            "default_recipient_role": "seller",
            "is_active": True,
            "priority": 10,
        },
    ]

    created_count = 0
    for template_data in templates:
        if create_template(template_data):
            created_count += 1

    print("\n" + "=" * 60)
    print(f"  ✅ Created {created_count}/{len(templates)} contract templates")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Go to DocuSeal and create templates for these contracts")
    print("2. Update each contract template with its docuseal_template_id")
    print("3. Test by creating a new property - contracts will auto-attach!")
    print("\nExample: Update template with DocuSeal ID:")
    print("curl -X PATCH 'https://ai-realtor.fly.dev/contract-templates/1' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"docuseal_template_id\": \"your_docuseal_template_id\"}'")


if __name__ == "__main__":
    seed_templates()
