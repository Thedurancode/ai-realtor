#!/usr/bin/env python3
"""
Enrich a property with Zillow data
"""
import requests
import json

BASE_URL = "http://localhost:8000"
SESSION_ID = "enrich_session"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def main():
    # Get property ID from user or use the last created one
    property_id = 1  # Default to property ID 1 (141 Throop Ave)

    print_section("📊 ENRICHING PROPERTY WITH ZILLOW DATA")

    print(f"🔍 Enriching Property ID: {property_id}")

    # Enrich with Zillow data
    enrich_resp = requests.post(
        f"{BASE_URL}/context/enrich",
        json={
            "property_ref": str(property_id),
            "session_id": SESSION_ID
        }
    )

    if enrich_resp.status_code == 200:
        enrich_result = enrich_resp.json()

        print("\n✅ ZILLOW ENRICHMENT SUCCESSFUL!")
        print(f"   {enrich_result['message']}")

        data = enrich_result['data']
        print(f"\n   🏡 Property Information:")
        print(f"   📍 Address: {data['property_address']}")
        print(f"   🆔 ZPID: {data['zpid']}")

        if data.get('zestimate'):
            print(f"   💵 Zestimate: ${data['zestimate']:,.0f}")

        if data.get('rent_zestimate'):
            print(f"   🏠 Rent Estimate: ${data['rent_zestimate']:,.0f}/mo")

        if data.get('living_area'):
            print(f"   📐 Living Area: {data['living_area']:,} sqft")

        if data.get('lot_size'):
            print(f"   🌳 Lot Size: {data['lot_size']:,} sqft")

        if data.get('year_built'):
            print(f"   📅 Year Built: {data['year_built']}")

        if data.get('home_type'):
            print(f"   🏘️  Type: {data['home_type']}")

        print(f"   📸 Photos: {data['photo_count']} available")

        if data.get('zillow_url'):
            print(f"   🔗 Zillow URL: {data['zillow_url']}")

        print_section("🎉 ENRICHMENT COMPLETE!")
        print("Property data has been enhanced with comprehensive Zillow information")
        print("View the property on the TV display to see photos and all details!")

    else:
        print(f"\n❌ Enrichment failed: {enrich_resp.status_code}")
        print(enrich_resp.text)

        # Try to parse error details
        try:
            error_detail = enrich_resp.json()
            print(f"\n💡 Error: {error_detail.get('detail', 'Unknown error')}")
        except:
            pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
