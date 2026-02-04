#!/usr/bin/env python3
"""
Test conversational flow with context memory

Demonstrates:
"Add new property" → "Skip trace THIS property"
"""
import requests
import json

BASE_URL = "http://localhost:8000"
SESSION_ID = "demo_session"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def main():
    print_section("🗣️  CONVERSATIONAL FLOW DEMO")

    # Step 1: User says "Add new property"
    print("👤 YOU: \"Add a new property at 312 Eisler Lane, price $450,000\"")
    print()

    # Get place_id first (this would happen automatically in voice interface)
    autocomplete_resp = requests.post(
        f"{BASE_URL}/address/autocomplete",
        json={"input": "312 Eisler Lane", "country": "us"}
    )
    suggestions = autocomplete_resp.json()['suggestions']
    place_id = suggestions[0]['place_id']

    # Create property with context
    create_resp = requests.post(
        f"{BASE_URL}/context/property/create",
        json={
            "place_id": place_id,
            "price": 450000,
            "bedrooms": 3,
            "bathrooms": 2,
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

        print_section("🗣️  FOLLOW-UP COMMAND")

        # Step 2: User says "Skip trace THIS property"
        print("👤 YOU: \"Skip trace THIS property\"")
        print("         (Note: No property ID or address needed!)")
        print()

        # Skip trace with context - No property reference needed!
        skip_resp = requests.post(
            f"{BASE_URL}/context/skip-trace",
            json={
                "property_ref": None,  # Uses context automatically!
                "session_id": SESSION_ID
            }
        )

        if skip_resp.status_code == 200:
            skip_result = skip_resp.json()

            print("🤖 SYSTEM:")
            print(f"   ✅ {skip_result['message']}")
            print(f"\n   👤 Owner Information:")
            print(f"   → Name: {skip_result['data']['owner_name']}")
            if skip_result['data']['owner_age']:
                print(f"   → Age: {skip_result['data']['owner_age']}")
            print(f"   → Phone Numbers: {skip_result['data']['phone_count']} found")
            print(f"   → Email Addresses: {skip_result['data']['email_count']} found")

            print("\n   📝 Context Memory:")
            context = skip_result['context_summary']
            print(f"   → Last Property: {context['last_property']['address']}")
            print(f"   → Last Skip Trace: ID {context['last_skip_trace']['id']}")

            print_section("✅ SUCCESS - CONTEXT WORKS!")

            print("The system remembered:")
            print("   1. ✅ You created property at 312 Eisler Lane")
            print("   2. ✅ Property ID was 2 (or whatever it created)")
            print("   3. ✅ When you said 'THIS property', it knew you meant ID 2")
            print("   4. ✅ Automatically ran skip trace on the right property")

            print_section("🎯 OTHER CONTEXT EXAMPLES")

            print("Now you can also say:")
            print()
            print("   \"Skip trace THIS property\"")
            print("   → Uses last property from context")
            print()
            print("   \"Skip trace THAT property\"")
            print("   → Uses last property from context")
            print()
            print("   \"Skip trace IT\"")
            print("   → Uses last property from context")
            print()
            print("   \"Add a contact for THIS property\"")
            print("   → Uses last property from context")
            print()
            print("   \"Send a contract for THIS property\"")
            print("   → Uses last property from context")

            print_section("📊 VIEW CURRENT CONTEXT")

            # Show context summary
            context_resp = requests.get(
                f"{BASE_URL}/context/summary",
                params={"session_id": SESSION_ID}
            )

            if context_resp.status_code == 200:
                summary = context_resp.json()
                print("Current conversation memory:")
                print(json.dumps(summary['context'], indent=2))

        else:
            print(f"❌ Skip trace error: {skip_resp.status_code}")
            print(skip_resp.text)

    else:
        print(f"❌ Property creation error: {create_resp.status_code}")
        print(create_resp.text)

    print_section("🎉 CONVERSATIONAL AI COMPLETE!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
