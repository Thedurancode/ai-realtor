#!/usr/bin/env python3
"""Test property enrichment with Google Places API"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import requests
import json

async def test_enrichment():
    print("="*70)
    print("  PROPERTY ENRICHMENT TEST")
    print("="*70)

    address = "312 Eisler Lane"

    print(f"\n1️⃣  Searching for: {address}")
    print("   Using Google Places Autocomplete API...")

    # Step 1: Autocomplete to get place_id
    autocomplete_resp = requests.post(
        "http://localhost:8000/address/autocomplete",
        json={"input": address, "country": "us"}
    )

    if autocomplete_resp.status_code == 200:
        result = autocomplete_resp.json()
        suggestions = result.get('suggestions', [])
        if suggestions:
            print(f"\n✅ Found {len(suggestions)} suggestion(s):")
            for i, s in enumerate(suggestions[:3], 1):
                print(f"   {i}. {s['description']}")

            # Use first suggestion
            place_id = suggestions[0]['place_id']
            description = suggestions[0]['description']

            print(f"\n2️⃣  Selected: {description}")
            print(f"   Place ID: {place_id[:30]}...")

            # Step 2: Create property with enrichment
            print("\n3️⃣  Creating property with voice endpoint (auto-enrichment)...")

            property_data = {
                "place_id": place_id,
                "price": 450000,
                "bedrooms": 3,
                "bathrooms": 2,
                "agent_id": 1,
                "status": "available",
                "property_type": "house"
            }

            create_resp = requests.post(
                "http://localhost:8000/properties/voice",
                json=property_data
            )

            if create_resp.status_code == 201:
                result = create_resp.json()
                prop = result['property']

                print("\n" + "="*70)
                print("  ✅ PROPERTY CREATED & ENRICHED!")
                print("="*70)

                print(f"\n📍 Full Address Details (from Google Places):")
                print(f"   Address: {prop['address']}")
                print(f"   City: {prop['city']}")
                print(f"   State: {prop['state']}")
                print(f"   Zip: {prop['zip_code']}")

                print(f"\n🏠 Property Details:")
                print(f"   ID: {prop['id']}")
                print(f"   Title: {prop['title']}")
                print(f"   Price: ${prop['price']:,}")
                print(f"   Bedrooms: {prop['bedrooms']}")
                print(f"   Bathrooms: {prop['bathrooms']}")
                print(f"   Status: {prop['status']}")

                print(f"\n🎤 Voice Confirmation:")
                print(f"   \"{result['voice_confirmation']}\"")

                print("\n" + "="*70)
                print("  WHAT HAPPENED")
                print("="*70)
                print("\n✅ Google Places Autocomplete found the address")
                print("✅ Got place_id from Google")
                print("✅ Fetched full address details (street, city, state, zip)")
                print("✅ Created property with all enriched data")
                print("✅ Saved to database with ID:", prop['id'])

                return prop
            else:
                error = create_resp.json()
                print(f"\n❌ Error creating property:")
                print(json.dumps(error, indent=2))

                # Check if Google API key is configured
                if "Invalid address" in str(error):
                    print("\n⚠️  Google Places API key might not be configured!")
                    print("   Update .env with:")
                    print("   GOOGLE_PLACES_API_KEY=your_actual_key")
        else:
            print("\n❌ No suggestions found for that address")
            print("   Google Places couldn't find '312 Eisler Lane'")
    else:
        print(f"\n❌ Autocomplete failed: {autocomplete_resp.status_code}")
        error = autocomplete_resp.json()
        print(json.dumps(error, indent=2))

        if autocomplete_resp.status_code == 500:
            print("\n⚠️  This usually means Google Places API key is not configured")
            print("   Check your .env file for GOOGLE_PLACES_API_KEY")

if __name__ == "__main__":
    asyncio.run(test_enrichment())
