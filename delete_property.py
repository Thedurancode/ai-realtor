#!/usr/bin/env python3
"""
Delete a specific property by ID
"""
import requests

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def main():
    property_id = 1  # Property ID for 141 Throop Ave

    print_section("🗑️  DELETING PROPERTY")

    print(f"Deleting Property ID: {property_id}")

    # Delete the property
    delete_resp = requests.delete(f"{BASE_URL}/properties/{property_id}")

    if delete_resp.status_code == 204:
        print("\n✅ PROPERTY DELETED SUCCESSFULLY!")
        print(f"   Property ID {property_id} has been removed from the database")
        print("   All related data (enrichments, skip traces, etc.) also deleted")

        print_section("🎉 DELETION COMPLETE!")
        print("The property has been removed from the TV display")
    else:
        print(f"\n❌ Deletion failed: {delete_resp.status_code}")
        if delete_resp.text:
            print(delete_resp.text)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
