"""
Seed compliance rules for different states

Run this script to populate the database with example compliance rules:
python seed_compliance_rules.py
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.compliance_rule import ComplianceRule
from datetime import date


def seed_compliance_rules():
    """Seed database with example compliance rules"""

    db = SessionLocal()

    # Check if rules already exist
    existing = db.query(ComplianceRule).first()
    if existing:
        print("⚠️  Compliance rules already exist in database. Skipping seed.")
        print("   Delete existing rules first if you want to re-seed.")
        db.close()
        return

    rules = [
        # ========== NEW YORK RULES ==========
        ComplianceRule(
            state="NY",
            rule_code="NY-LEAD-001",
            category="disclosure",
            title="Lead-Based Paint Disclosure Required",
            description="Properties built before 1978 must have lead paint disclosure form signed by buyer and seller",
            legal_citation="42 U.S.C. § 4852d",
            rule_type="threshold",
            field_to_check="year_built",
            condition="< 1978",
            severity="critical",
            requires_document=True,
            document_type="lead_paint_disclosure",
            ai_prompt="If this property was built before 1978, it MUST have a lead paint disclosure form. Check if year_built < 1978.",
            how_to_fix="Obtain and complete EPA Lead-Based Paint Disclosure Form before listing",
            penalty_description="Up to $10,000 fine per violation",
            fine_amount_min=1000.0,
            fine_amount_max=10000.0,
            tags=["lead", "pre-1978", "disclosure", "epa"],
            is_active=True
        ),

        ComplianceRule(
            state="NY",
            rule_code="NY-SMOKE-001",
            category="safety",
            title="Smoke Detector Requirement",
            description="All residential properties must have working smoke detectors in every bedroom and hallway",
            legal_citation="NYS Property Maintenance Code § 704",
            rule_type="ai_review",
            severity="high",
            ai_prompt="Verify that property has smoke detectors documented. For multi-bedroom properties, there must be one per bedroom plus hallways.",
            how_to_fix="Install and test smoke detectors in all required locations",
            penalty_description="Code violation notice, must fix before closing",
            tags=["safety", "smoke_detector", "code"],
            is_active=True
        ),

        ComplianceRule(
            state="NY",
            rule_code="NY-PROP-001",
            category="disclosure",
            title="Property Condition Disclosure Statement",
            description="Sellers must provide Property Condition Disclosure Statement for 1-4 family residences",
            legal_citation="NY RPL § 462",
            rule_type="document",
            severity="high",
            property_type_filter=["house", "townhouse", "condo", "apartment"],
            requires_document=True,
            document_type="property_condition_disclosure",
            ai_prompt="Check if property has completed Property Condition Disclosure Statement on file",
            how_to_fix="Complete NY Property Condition Disclosure Statement form",
            tags=["disclosure", "property_condition"],
            is_active=True
        ),

        # ========== CALIFORNIA RULES ==========
        ComplianceRule(
            state="CA",
            rule_code="CA-EARTH-001",
            category="disclosure",
            title="Natural Hazard Disclosure Statement",
            description="Properties must disclose location in earthquake, flood, fire, or other natural hazard zones",
            legal_citation="CA Civil Code § 1103",
            rule_type="document",
            severity="critical",
            requires_document=True,
            document_type="natural_hazard_disclosure",
            ai_prompt="Check if property has Natural Hazard Disclosure Statement (NHD) including earthquake, flood, and fire hazard zones",
            how_to_fix="Obtain Natural Hazard Disclosure Report from qualified third-party",
            penalty_description="Buyer may rescind contract if not provided",
            tags=["earthquake", "natural_hazard", "disclosure", "nhd"],
            is_active=True
        ),

        ComplianceRule(
            state="CA",
            rule_code="CA-RETRO-001",
            category="safety",
            title="Earthquake Retrofit Disclosure",
            description="Properties built before 1960 must disclose whether earthquake retrofit has been performed",
            legal_citation="CA Civil Code § 1102.6",
            rule_type="threshold",
            field_to_check="year_built",
            condition="< 1960",
            severity="high",
            ai_prompt="For properties built before 1960, check if earthquake retrofit disclosure has been provided",
            how_to_fix="Provide disclosure about earthquake retrofit status",
            tags=["earthquake", "retrofit", "pre-1960"],
            min_year_built=None,
            max_year_built=1960,
            is_active=True
        ),

        ComplianceRule(
            state="CA",
            rule_code="CA-WATER-001",
            category="environmental",
            title="Water-Conserving Plumbing Fixtures",
            description="Properties must have water-conserving plumbing fixtures installed before transfer of title",
            legal_citation="CA Civil Code § 1101.1-1101.9",
            rule_type="ai_review",
            severity="high",
            ai_prompt="Check if property has water-conserving toilets (1.6 gallons per flush or less) and low-flow showerheads",
            how_to_fix="Replace old fixtures with water-conserving models",
            penalty_description="Must install before close of escrow",
            estimated_fix_cost=500.0,
            estimated_fix_time_days=2,
            tags=["water", "conservation", "plumbing"],
            is_active=True
        ),

        ComplianceRule(
            state="CA",
            rule_code="CA-LEAD-001",
            category="disclosure",
            title="Lead-Based Paint Disclosure (CA)",
            description="Properties built before 1978 require lead paint disclosure per federal and state law",
            legal_citation="42 U.S.C. § 4852d; CA Health & Safety Code § 105250",
            rule_type="threshold",
            field_to_check="year_built",
            condition="< 1978",
            severity="critical",
            requires_document=True,
            document_type="lead_paint_disclosure",
            ai_prompt="Properties built before 1978 must have lead paint disclosure",
            how_to_fix="Complete lead paint disclosure form",
            tags=["lead", "pre-1978", "disclosure"],
            max_year_built=1978,
            is_active=True
        ),

        # ========== FLORIDA RULES ==========
        ComplianceRule(
            state="FL",
            rule_code="FL-RADON-001",
            category="disclosure",
            title="Radon Gas Disclosure",
            description="Sellers must provide radon gas notification to buyers",
            legal_citation="FL Statute § 404.056",
            rule_type="document",
            severity="medium",
            requires_document=True,
            document_type="radon_disclosure",
            ai_prompt="Check if property has radon gas disclosure notice provided to buyer",
            how_to_fix="Provide Florida Radon Gas Disclosure Statement",
            tags=["radon", "disclosure", "gas"],
            is_active=True
        ),

        ComplianceRule(
            state="FL",
            rule_code="FL-PROP-001",
            category="disclosure",
            title="Property Tax Disclosure",
            description="Sellers must disclose property tax information to buyers",
            legal_citation="FL Statute § 689.261",
            rule_type="document",
            severity="medium",
            requires_document=True,
            document_type="property_tax_disclosure",
            ai_prompt="Check if property tax disclosure has been provided",
            how_to_fix="Provide property tax disclosure statement",
            tags=["property_tax", "disclosure"],
            is_active=True
        ),

        ComplianceRule(
            state="FL",
            rule_code="FL-HOA-001",
            category="hoa",
            title="HOA/Condo Association Disclosure",
            description="For condos and properties with HOAs, must provide association documents and financial statements",
            legal_citation="FL Statute § 718.503, § 720.401",
            rule_type="document",
            severity="high",
            property_type_filter=["condo", "townhouse"],
            requires_document=True,
            document_type="hoa_documents",
            ai_prompt="For properties in HOA or condo associations, check if governing documents and financial statements have been provided",
            how_to_fix="Obtain and provide HOA/condo association documents, bylaws, and financial statements",
            tags=["hoa", "condo", "association"],
            is_active=True
        ),

        # ========== TEXAS RULES ==========
        ComplianceRule(
            state="TX",
            rule_code="TX-SELLER-001",
            category="disclosure",
            title="Seller's Disclosure Notice",
            description="Sellers must provide Seller's Disclosure Notice for residential property",
            legal_citation="TX Property Code § 5.008",
            rule_type="document",
            severity="critical",
            requires_document=True,
            document_type="sellers_disclosure",
            ai_prompt="Check if Texas Seller's Disclosure Notice has been completed and provided",
            how_to_fix="Complete and sign Texas Seller's Disclosure Notice form",
            penalty_description="Buyer may terminate contract if not provided",
            tags=["sellers_disclosure", "disclosure"],
            is_active=True
        ),

        ComplianceRule(
            state="TX",
            rule_code="TX-LEAD-001",
            category="disclosure",
            title="Lead-Based Paint Disclosure (TX)",
            description="Properties built before 1978 require lead paint disclosure",
            legal_citation="42 U.S.C. § 4852d",
            rule_type="threshold",
            field_to_check="year_built",
            condition="< 1978",
            severity="critical",
            requires_document=True,
            document_type="lead_paint_disclosure",
            ai_prompt="Properties built before 1978 must have lead paint disclosure",
            how_to_fix="Complete federal lead paint disclosure form",
            tags=["lead", "pre-1978", "disclosure"],
            max_year_built=1978,
            is_active=True
        ),

        ComplianceRule(
            state="TX",
            rule_code="TX-FLOOD-001",
            category="environmental",
            title="Flood Zone Disclosure",
            description="Properties in flood zones must disclose flood hazard status",
            legal_citation="TX Property Code § 5.008",
            rule_type="ai_review",
            severity="high",
            ai_prompt="Check if property is in a flood zone and if flood hazard disclosure has been provided",
            how_to_fix="Obtain flood zone determination and provide disclosure if in flood zone",
            tags=["flood", "environmental", "disclosure"],
            is_active=True
        ),

        # ========== GENERAL RULES (examples that apply broadly) ==========
        ComplianceRule(
            state="NY",
            rule_code="NY-PRICE-001",
            category="licensing",
            title="High-Value Property Additional Documentation",
            description="Properties over $5M may require additional documentation and review",
            rule_type="threshold",
            field_to_check="price",
            condition=">= 5000000",
            severity="medium",
            ai_prompt="For properties valued at $5M or more, verify additional documentation requirements are met",
            how_to_fix="Consult with real estate attorney for high-value transaction requirements",
            min_price=5000000.0,
            tags=["high_value", "luxury"],
            is_active=True
        ),
    ]

    # Add all rules to database
    for rule in rules:
        db.add(rule)

    db.commit()

    print(f"✅ Successfully seeded {len(rules)} compliance rules!")
    print("\nBreakdown by state:")

    from collections import Counter
    state_counts = Counter([r.state for r in rules])
    for state, count in state_counts.items():
        print(f"   {state}: {count} rules")

    db.close()


if __name__ == "__main__":
    print("🌱 Seeding compliance rules...")
    seed_compliance_rules()
    print("\n✅ Done! Compliance knowledge base is ready.")
    print("\n📚 You can now:")
    print("   - View rules: GET /compliance/knowledge/rules")
    print("   - Add rules: POST /compliance/knowledge/rules")
    print("   - Use AI to generate rules: POST /compliance/knowledge/rules/ai-generate")
    print("   - Run compliance checks on properties")
