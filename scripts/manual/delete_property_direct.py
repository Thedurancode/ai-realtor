#!/usr/bin/env python3
"""
Delete a specific property directly from database
"""
from app.database import SessionLocal
from app.models.property import Property
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.skip_trace import SkipTrace
from app.models.contact import Contact
from app.models.contract import Contract

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def main():
    property_id = 1  # Property ID for 141 Throop Ave

    print_section("🗑️  DELETING PROPERTY FROM DATABASE")

    db = SessionLocal()
    try:
        # Get the property first
        property = db.query(Property).filter(Property.id == property_id).first()

        if not property:
            print(f"❌ Property ID {property_id} not found")
            return

        print(f"Found property: {property.address}, {property.city}, {property.state}")
        print(f"\n🗑️  Deleting related data and property...")

        # Delete related data (due to foreign key constraints)

        # Delete contracts
        contracts_deleted = db.query(Contract).filter(Contract.property_id == property_id).delete()
        print(f"   ✅ Deleted {contracts_deleted} contracts")

        # Delete contacts
        contacts_deleted = db.query(Contact).filter(Contact.property_id == property_id).delete()
        print(f"   ✅ Deleted {contacts_deleted} contacts")

        # Delete Zillow enrichments
        enrichments_deleted = db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == property_id).delete()
        print(f"   ✅ Deleted {enrichments_deleted} Zillow enrichments")

        # Delete skip traces
        skip_traces_deleted = db.query(SkipTrace).filter(SkipTrace.property_id == property_id).delete()
        print(f"   ✅ Deleted {skip_traces_deleted} skip traces")

        # Delete the property
        db.delete(property)

        # Commit the transaction
        db.commit()

        print_section("✅ SUCCESS - PROPERTY DELETED")
        print(f"Property ID {property_id} ({property.address}) has been removed")
        print("The property will disappear from the TV display")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error deleting property: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
