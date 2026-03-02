#!/usr/bin/env python3
"""
Delete all properties from the database
WARNING: This is a destructive operation!
"""
from app.database import SessionLocal
from app.models.property import Property
from app.models.skip_trace import SkipTrace
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.contact import Contact
from app.models.contract import Contract

def main():
    print("\n" + "="*70)
    print("  ⚠️  DELETE ALL PROPERTIES FROM DATABASE")
    print("="*70 + "\n")

    # Ask for confirmation
    confirmation = input("Are you sure you want to delete ALL properties? (yes/no): ")

    if confirmation.lower() != "yes":
        print("\n❌ Operation cancelled.")
        return

    # Double confirmation
    double_confirm = input("\nThis will delete ALL properties and related data. Type 'DELETE ALL' to confirm: ")

    if double_confirm != "DELETE ALL":
        print("\n❌ Operation cancelled.")
        return

    print("\n🗑️  Deleting all properties and related data...")

    db = SessionLocal()
    try:
        # Delete related data first (due to foreign key constraints)

        # Delete contracts
        contracts_deleted = db.query(Contract).delete()
        print(f"   ✅ Deleted {contracts_deleted} contracts")

        # Delete contacts
        contacts_deleted = db.query(Contact).delete()
        print(f"   ✅ Deleted {contacts_deleted} contacts")

        # Delete Zillow enrichments
        enrichments_deleted = db.query(ZillowEnrichment).delete()
        print(f"   ✅ Deleted {enrichments_deleted} Zillow enrichments")

        # Delete skip traces
        skip_traces_deleted = db.query(SkipTrace).delete()
        print(f"   ✅ Deleted {skip_traces_deleted} skip traces")

        # Finally, delete properties
        properties_deleted = db.query(Property).delete()
        print(f"   ✅ Deleted {properties_deleted} properties")

        # Commit the transaction
        db.commit()

        print("\n" + "="*70)
        print(f"  ✅ SUCCESS - All properties and related data deleted")
        print("="*70)
        print(f"\nTotal records deleted:")
        print(f"  - Properties: {properties_deleted}")
        print(f"  - Skip Traces: {skip_traces_deleted}")
        print(f"  - Zillow Enrichments: {enrichments_deleted}")
        print(f"  - Contacts: {contacts_deleted}")
        print(f"  - Contracts: {contracts_deleted}")
        print(f"\nDatabase is now clean!\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error deleting properties: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
