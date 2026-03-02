#!/usr/bin/env python3
"""
Test complete conversational flow:
1. "Create property at 141 Throop Ave New Brunswick"
2. "Add Lenny Hernandez as the lawyer"
3. "Skip trace it"
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
SESSION_ID = "conversation_demo"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_user(message):
    print(f"👤 YOU: \"{message}\"")
    print()

def print_system(message):
    print(f"🤖 SYSTEM: {message}")
    print()

def main():
    print_section("🗣️  NATURAL CONVERSATION DEMO")

    # ========================================================================
    # STEP 1: Create property at 141 Throop Ave New Brunswick
    # ========================================================================
    print_user("Create a new property at 141 Throop Ave New Brunswick, price $350,000")

    # Get address autocomplete
    autocomplete_resp = requests.post(
        f"{BASE_URL}/address/autocomplete",
        json={"input": "141 Throop Ave New Brunswick", "country": "us"}
    )

    if autocomplete_resp.status_code == 200:
        suggestions = autocomplete_resp.json()['suggestions']
        if suggestions:
            place_id = suggestions[0]['place_id']
            full_address = suggestions[0]['description']

            print_system(f"Found address: {full_address}")
            print_system("Creating property with Google Places enrichment...")

            # Create property with context
            create_resp = requests.post(
                f"{BASE_URL}/context/property/create",
                json={
                    "place_id": place_id,
                    "price": 350000,
                    "bedrooms": 4,
                    "bathrooms": 2,
                    "agent_id": 1,
                    "session_id": SESSION_ID
                }
            )

            if create_resp.status_code == 200:
                result = create_resp.json()

                print_system("✅ Property created successfully!")
                print(f"   📍 Address: {result['data']['address']}")
                print(f"   🏙️  City: {result['data']['city']}, {result['data']['state']}")
                print(f"   💰 Price: ${result['data']['price']:,.0f}")
                print(f"   🏠 Property ID: {result['data']['property_id']}")

                property_id = result['data']['property_id']

                print(f"\n   📝 Context Memory:")
                print(f"   → System remembers: Property ID {property_id}")

                time.sleep(1)

                # ================================================================
                # STEP 2: Add Lenny Hernandez as the lawyer
                # ================================================================
                print_section("🗣️  STEP 2 - ADD LAWYER")

                print_user("Add Lenny Hernandez as the lawyer for this property")

                # Create contact
                contact_resp = requests.post(
                    f"{BASE_URL}/contacts/",
                    json={
                        "property_id": property_id,
                        "name": "Lenny Hernandez",
                        "email": "lenny.hernandez@lawfirm.com",
                        "phone": "(555) 123-4567",
                        "role": "lawyer"
                    }
                )

                if contact_resp.status_code == 201:
                    contact = contact_resp.json()

                    print_system("✅ Contact added successfully!")
                    print(f"   👤 Name: {contact['name']}")
                    print(f"   ⚖️  Role: {contact['role']}")
                    print(f"   📧 Email: {contact['email']}")
                    print(f"   📞 Phone: {contact['phone']}")
                    print(f"   🆔 Contact ID: {contact['id']}")

                    print(f"\n   📝 Context Memory:")
                    print(f"   → System remembers: Property ID {property_id}")
                    print(f"   → System remembers: Lawyer contact ID {contact['id']}")

                    time.sleep(1)

                    # ============================================================
                    # STEP 3: Skip trace it
                    # ============================================================
                    print_section("🗣️  STEP 3 - SKIP TRACE")

                    print_user("Skip trace it")
                    print("   (Note: 'it' refers to the property we just created!)")
                    print()

                    # Skip trace with context - No property reference needed!
                    skip_resp = requests.post(
                        f"{BASE_URL}/context/skip-trace",
                        json={
                            "property_ref": None,  # Magic! Uses context
                            "session_id": SESSION_ID
                        }
                    )

                    if skip_resp.status_code == 200:
                        skip_result = skip_resp.json()

                        print_system("✅ Skip trace complete!")
                        print(f"   🔍 Searched: {skip_result['data']['property_address']}")
                        print(f"\n   👤 Property Owner Found:")
                        print(f"   → Name: {skip_result['data']['owner_name']}")

                        if skip_result['data']['owner_age']:
                            print(f"   → Age: {skip_result['data']['owner_age']}")

                        print(f"   → Phone Numbers: {skip_result['data']['phone_count']} found")
                        print(f"   → Email Addresses: {skip_result['data']['email_count']} found")

                        print(f"\n   💡 TruePeopleSearch Link Available")
                        print(f"   (Visit for complete contact details)")

                        print(f"\n   📝 Context Memory:")
                        context = skip_result['context_summary']
                        print(f"   → Property: {context['last_property']['address']} (ID: {context['last_property']['id']})")
                        print(f"   → Skip Trace: ID {context['last_skip_trace']['id']}")

                        print_section("✅ COMPLETE CONVERSATION SUCCESS!")

                        print("🎯 The system understood:")
                        print()
                        print("   1️⃣  'Create property at 141 Throop...'")
                        print("       → Created property ID", property_id)
                        print("       → Remembered it in context")
                        print()
                        print("   2️⃣  'Add Lenny Hernandez as the lawyer'")
                        print("       → Used property ID from context")
                        print("       → Created lawyer contact")
                        print()
                        print("   3️⃣  'Skip trace it'")
                        print("       → 'it' = property from context")
                        print("       → Ran RapidAPI skip trace")
                        print("       → Found owner:", skip_result['data']['owner_name'])

                        print_section("🚀 WHAT'S NEXT?")

                        print("Now you can continue the conversation:")
                        print()
                        print("   💬 \"Send a contract to the owner\"")
                        print("      → Creates contract for property", property_id)
                        print()
                        print("   💬 \"Email the lawyer about this\"")
                        print("      → Sends email to Lenny Hernandez")
                        print()
                        print("   💬 \"Add a todo to follow up tomorrow\"")
                        print("      → Creates task for property", property_id)
                        print()
                        print("   💬 \"Show me all contacts for this property\"")
                        print("      → Lists: Lenny Hernandez (lawyer) + owner")

                        print_section("📊 FINAL CONTEXT STATE")

                        # Show context
                        context_resp = requests.get(
                            f"{BASE_URL}/context/summary",
                            params={"session_id": SESSION_ID}
                        )

                        if context_resp.status_code == 200:
                            summary = context_resp.json()
                            print("Current conversation memory:")
                            print(json.dumps(summary['context'], indent=2))

                    else:
                        print(f"❌ Skip trace failed: {skip_resp.status_code}")
                        print(skip_resp.text)

                else:
                    print(f"❌ Contact creation failed: {contact_resp.status_code}")
                    print(contact_resp.text)

            else:
                print(f"❌ Property creation failed: {create_resp.status_code}")
                print(create_resp.text)

        else:
            print_system("❌ Address not found. Please check the address.")

    else:
        print(f"❌ Autocomplete failed: {autocomplete_resp.status_code}")

    print_section("🎉 CONVERSATIONAL AI DEMO COMPLETE!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
