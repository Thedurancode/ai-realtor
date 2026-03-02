#!/usr/bin/env python3
"""
Test Zillow property enrichment with context awareness

Demonstrates:
"Add new property" → "Enrich THIS property with Zillow data"
"""
import requests
import json

BASE_URL = "http://localhost:8000"
SESSION_ID = "zillow_demo_session"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def main():
    print_section("🏠 ZILLOW ENRICHMENT DEMO")

    # Step 1: User says "Add a new property"
    print("👤 YOU: \"Add a property at 1875 AVONDALE Circle, Jacksonville, FL, price $4,250,000\"")
    print()

    # Get place_id first (this would happen automatically in voice interface)
    autocomplete_resp = requests.post(
        f"{BASE_URL}/address/autocomplete",
        json={"input": "1875 AVONDALE Circle, Jacksonville, FL 32205", "country": "us"}
    )

    if autocomplete_resp.status_code != 200:
        print(f"❌ Address autocomplete error: {autocomplete_resp.status_code}")
        print(autocomplete_resp.text)
        return

    suggestions = autocomplete_resp.json()['suggestions']
    if not suggestions:
        print("❌ No address suggestions found")
        return

    place_id = suggestions[0]['place_id']

    # Create property with context
    create_resp = requests.post(
        f"{BASE_URL}/context/property/create",
        json={
            "place_id": place_id,
            "price": 4250000,
            "bedrooms": 7,
            "bathrooms": 9,
            "agent_id": 1,
            "session_id": SESSION_ID
        }
    )

    if create_resp.status_code == 200:
        result = create_resp.json()

        print("🤖 SYSTEM:")
        print(f"   ✅ {result['message']}")
        print(f"   📍 Property ID: {result['data']['property_id']}")
        print(f"   🏠 Address: {result['data']['address']}")
        print(f"   💰 Price: ${result['data']['price']:,.0f}")

        print("\n   📝 Context Memory:")
        context = result['context_summary']
        print(f"   → Last Property: {context['last_property']['address']} (ID: {context['last_property']['id']})")

        print_section("📊 ZILLOW ENRICHMENT")

        # Step 2: User says "Enrich THIS property with Zillow data"
        print("👤 YOU: \"Enrich THIS property with Zillow data\"")
        print("         (Note: No property ID or address needed!)")
        print()

        # Enrich with context - No property reference needed!
        enrich_resp = requests.post(
            f"{BASE_URL}/context/enrich",
            json={
                "property_ref": None,  # Uses context automatically!
                "session_id": SESSION_ID
            }
        )

        if enrich_resp.status_code == 200:
            enrich_result = enrich_resp.json()

            print("🤖 SYSTEM:")
            print(f"   ✅ {enrich_result['message']}")
            print(f"\n   🏡 Zillow Property Information:")
            data = enrich_result['data']
            print(f"   → ZPID: {data['zpid']}")
            print(f"   → Zestimate: ${data['zestimate']:,.0f}" if data['zestimate'] else "   → Zestimate: N/A")
            print(f"   → Rent Zestimate: ${data['rent_zestimate']:,.0f}/mo" if data['rent_zestimate'] else "   → Rent Zestimate: N/A")
            print(f"   → Living Area: {data['living_area']:,} sqft" if data['living_area'] else "   → Living Area: N/A")
            print(f"   → Lot Size: {data['lot_size']:,} sqft" if data['lot_size'] else "   → Lot Size: N/A")
            print(f"   → Year Built: {data['year_built']}" if data['year_built'] else "   → Year Built: N/A")
            print(f"   → Home Type: {data['home_type']}" if data['home_type'] else "   → Home Type: N/A")
            print(f"   → Photos: {data['photo_count']} available")
            print(f"   → Zillow URL: {data['zillow_url']}" if data['zillow_url'] else "   → Zillow URL: N/A")

            print("\n   📝 Context Memory:")
            context = enrich_result['context_summary']
            print(f"   → Last Property: {context['last_property']['address']}")

            print_section("✅ SUCCESS - ZILLOW ENRICHMENT WORKS!")

            print("The system:")
            print("   1. ✅ Created property at 1875 AVONDALE Circle")
            print("   2. ✅ Remembered the property ID in context")
            print("   3. ✅ When you said 'enrich THIS property', it knew which one")
            print("   4. ✅ Called Zillow API and retrieved comprehensive property data")
            print("   5. ✅ Stored all enrichment data in the database")

            print_section("📊 ENRICHMENT DATA INCLUDES")

            print("Zillow provides comprehensive property information:")
            print()
            print("   • Valuation Data:")
            print("     - Zestimate (current home value)")
            print("     - Rent Zestimate (estimated rental value)")
            print("     - Price history")
            print()
            print("   • Property Details:")
            print("     - Living area, lot size")
            print("     - Year built, home type")
            print("     - Bedrooms, bathrooms")
            print()
            print("   • Market Info:")
            print("     - Days on Zillow")
            print("     - Page views")
            print("     - Favorite count")
            print()
            print("   • Additional Data:")
            print("     - High-resolution photos")
            print("     - Nearby schools with ratings")
            print("     - Tax history (last 5 years)")
            print("     - Property tax rate")

            print_section("🎯 OTHER ENRICHMENT EXAMPLES")

            print("You can also enrich by:")
            print()
            print("   \"Enrich THIS property\"")
            print("   → Uses last property from context")
            print()
            print("   \"Enrich property at 1875 AVONDALE\"")
            print("   → Searches by address")
            print()
            print("   \"Enrich property ID 2\"")
            print("   → Uses specific property ID")

        else:
            print(f"❌ Enrichment error: {enrich_resp.status_code}")
            print(enrich_resp.text)
            if enrich_resp.status_code == 500:
                print("\n💡 Note: Make sure RAPIDAPI_KEY and ZILLOW_API_HOST are set in .env")

    else:
        print(f"❌ Property creation error: {create_resp.status_code}")
        print(create_resp.text)

    print_section("🎉 ZILLOW ENRICHMENT DEMO COMPLETE!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
