#!/usr/bin/env python3
"""
Add property at 141 Throop Ave, New Brunswick
"""
import requests
import json

BASE_URL = "http://localhost:8000"
SESSION_ID = "add_throop_session"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def main():
    print_section("🏠 ADDING PROPERTY: 141 Throop Ave, New Brunswick")

    # Step 1: Get place_id from address autocomplete
    print("📍 Looking up address...")
    autocomplete_resp = requests.post(
        f"{BASE_URL}/address/autocomplete",
        json={"input": "141 Throop Ave, New Brunswick, NJ", "country": "us"}
    )

    if autocomplete_resp.status_code != 200:
        print(f"❌ Address autocomplete error: {autocomplete_resp.status_code}")
        print(autocomplete_resp.text)
        return

    suggestions = autocomplete_resp.json()['suggestions']
    if not suggestions:
        print("❌ No address suggestions found")
        return

    print(f"✅ Found address: {suggestions[0]['description']}")
    place_id = suggestions[0]['place_id']

    # Step 2: Create property
    print("\n🏗️  Creating property...")
    create_resp = requests.post(
        f"{BASE_URL}/context/property/create",
        json={
            "place_id": place_id,
            "price": 350000,  # Default price - can be adjusted
            "bedrooms": 3,
            "bathrooms": 2,
            "agent_id": 1,
            "session_id": SESSION_ID
        }
    )

    if create_resp.status_code == 200:
        result = create_resp.json()

        print("\n✅ PROPERTY CREATED SUCCESSFULLY!")
        print(f"\n   📍 Property ID: {result['data']['property_id']}")
        print(f"   🏠 Address: {result['data']['address']}")
        print(f"   🏙️  City: {result['data']['city']}, {result['data']['state']}")
        print(f"   💰 Price: ${result['data']['price']:,.0f}")

        property_id = result['data']['property_id']

        # Step 3: Enrich with Zillow data
        print_section("📊 ENRICHING WITH ZILLOW DATA")

        enrich_resp = requests.post(
            f"{BASE_URL}/context/enrich",
            json={
                "property_ref": None,  # Uses context automatically
                "session_id": SESSION_ID
            }
        )

        if enrich_resp.status_code == 200:
            enrich_result = enrich_resp.json()

            print("✅ ZILLOW ENRICHMENT SUCCESSFUL!")
            data = enrich_result['data']
            print(f"\n   🏡 ZPID: {data['zpid']}")
            print(f"   💵 Zestimate: ${data['zestimate']:,.0f}" if data['zestimate'] else "   💵 Zestimate: N/A")
            print(f"   🏠 Rent Estimate: ${data['rent_zestimate']:,.0f}/mo" if data['rent_zestimate'] else "   🏠 Rent Estimate: N/A")
            print(f"   📐 Living Area: {data['living_area']:,} sqft" if data['living_area'] else "   📐 Living Area: N/A")
            print(f"   🌳 Lot Size: {data['lot_size']:,} sqft" if data['lot_size'] else "   🌳 Lot Size: N/A")
            print(f"   📅 Year Built: {data['year_built']}" if data['year_built'] else "   📅 Year Built: N/A")
            print(f"   🏘️  Type: {data['home_type']}" if data['home_type'] else "   🏘️  Type: N/A")
            print(f"   📸 Photos: {data['photo_count']} available")

            if data['zillow_url']:
                print(f"   🔗 View: {data['zillow_url']}")

        else:
            print(f"\n⚠️  Zillow enrichment failed: {enrich_resp.status_code}")
            print(enrich_resp.text)
            print("\n💡 Property created, but enrichment data unavailable")

        print_section("🎉 COMPLETE!")
        print(f"Property at 141 Throop Ave has been added to the database")
        print(f"Property ID: {property_id}")
        print(f"\nYou can now view it on the TV display at http://localhost:3025")

    else:
        print(f"\n❌ Property creation error: {create_resp.status_code}")
        print(create_resp.text)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
