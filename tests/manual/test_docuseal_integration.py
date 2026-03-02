#!/usr/bin/env python3
"""Test complete DocuSeal integration with real API"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

def main():
    print_section("COMPLETE DOCUSEAL INTEGRATION TEST")

    print("\n📋 Prerequisites Check:")
    print("   1. DocuSeal API key configured in .env")
    print("   2. At least one template created in DocuSeal")
    print("   3. Resend API key configured")
    print("   4. Server running on port 8000")

    input("\n✅ Press Enter when ready to continue...")

    # Step 1: Create test data
    print_section("STEP 1: Creating Test Data")

    # Create agent
    print("\n1. Creating agent...")
    agent_resp = requests.post(
        f"{BASE_URL}/agents/",
        json={
            "name": "Test Agent",
            "email": "emprezarioinc@gmail.com",
            "phone": "555-1000"
        }
    )

    if agent_resp.status_code == 201:
        agent = agent_resp.json()
        print(f"✅ Agent: {agent['name']} (ID: {agent['id']})")
    else:
        print(f"⚠️  Using existing agent (ID: 1)")
        agent = {"id": 1, "name": "Test Agent", "email": "emprezarioinc@gmail.com"}

    # Create property
    print("\n2. Creating property...")
    prop_resp = requests.post(
        f"{BASE_URL}/properties/",
        json={
            "address": "123 Test Street",
            "city": "Brooklyn",
            "state": "NY",
            "zip_code": "11201",
            "title": "Test Property for DocuSeal",
            "price": 500000,
            "agent_id": agent['id']
        }
    )

    if prop_resp.status_code == 201:
        property_data = prop_resp.json()
        print(f"✅ Property: {property_data['address']} (ID: {property_data['id']})")
    else:
        print(f"⚠️  Error: {prop_resp.text}")
        return

    # Create contacts
    print("\n3. Creating contacts...")

    seller_resp = requests.post(
        f"{BASE_URL}/contacts/",
        json={
            "property_id": property_data['id'],
            "name": "John Seller",
            "email": "emprezarioinc@gmail.com",
            "phone": "555-2000",
            "role": "seller"
        }
    )
    seller = seller_resp.json()
    print(f"✅ Seller: {seller['name']}")

    lawyer_resp = requests.post(
        f"{BASE_URL}/contacts/",
        json={
            "property_id": property_data['id'],
            "name": "Lisa Lawyer",
            "email": "emprezarioinc@gmail.com",
            "phone": "555-3000",
            "role": "lawyer"
        }
    )
    lawyer = lawyer_resp.json()
    print(f"✅ Lawyer: {lawyer['name']}")

    # Step 2: Get DocuSeal templates
    print_section("STEP 2: Checking DocuSeal Templates")

    print("\n🔍 Fetching your DocuSeal templates...")
    print("\nYou need to:")
    print("   1. Go to https://docuseal.com/templates")
    print("   2. Create a template (or use existing)")
    print("   3. Copy the Template ID")

    template_id = input("\n📝 Enter your DocuSeal Template ID: ").strip()

    if not template_id:
        print("❌ Template ID required. Exiting.")
        return

    # Step 3: Create contract
    print_section("STEP 3: Creating Contract")

    print("\n📄 Creating contract with DocuSeal template...")
    contract_resp = requests.post(
        f"{BASE_URL}/contracts/",
        json={
            "property_id": property_data['id'],
            "name": "Test Purchase Agreement",
            "description": "Testing full DocuSeal integration",
            "docuseal_template_id": template_id
        }
    )

    if contract_resp.status_code == 201:
        contract = contract_resp.json()
        print(f"✅ Contract created: {contract['name']} (ID: {contract['id']})")
        print(f"   Template ID: {contract['docuseal_template_id']}")
        print(f"   Status: {contract['status']}")
    else:
        print(f"❌ Error: {contract_resp.text}")
        return

    # Step 4: Send multi-party contract
    print_section("STEP 4: Sending Multi-Party Contract via DocuSeal")

    print("\n📧 This will:")
    print("   1. Create a DocuSeal submission")
    print("   2. Send DocuSeal emails to signers")
    print("   3. Send Resend notification emails")
    print("   4. Track each signer in the database")

    input("\n✅ Press Enter to send the contract...")

    multi_party_request = {
        "submitters": [
            {
                "contact_id": seller['id'],
                "name": seller['name'],
                "email": seller['email'],
                "role": "Seller",
                "signing_order": 1
            },
            {
                "contact_id": lawyer['id'],
                "name": lawyer['name'],
                "email": lawyer['email'],
                "role": "Lawyer",
                "signing_order": 2
            },
            {
                "name": agent['name'],
                "email": agent['email'],
                "role": "Agent",
                "signing_order": 3
            }
        ],
        "order": "preserved",
        "message": "This is a test contract. Please review and sign in order."
    }

    print("\n🚀 Sending contract...")
    send_resp = requests.post(
        f"{BASE_URL}/contracts/{contract['id']}/send-multi-party",
        json=multi_party_request
    )

    print(f"\n📊 Response Status: {send_resp.status_code}")

    if send_resp.status_code == 200:
        result = send_resp.json()
        print("\n✅ SUCCESS! Contract sent!")
        print(f"\n📢 Voice Confirmation:")
        print(f"   {result['voice_confirmation']}")

        print(f"\n👥 Submitters Created:")
        for sub in result['submitters']:
            print(f"   {sub['signing_order']}. {sub['name']} ({sub['role']}) - {sub['status']}")

        if result.get('docuseal_url'):
            print(f"\n🔗 DocuSeal URL: {result['docuseal_url']}")

        print("\n📬 CHECK YOUR EMAIL:")
        print("   emprezarioinc@gmail.com")
        print("\n   You should receive:")
        print("   • DocuSeal signing emails (from DocuSeal)")
        print("   • Beautiful Resend notification emails (from your system)")

        # Step 5: Check status
        print_section("STEP 5: Checking Contract Status")

        input("\n✅ Press Enter to check contract status...")

        status_resp = requests.get(f"{BASE_URL}/contracts/{contract['id']}/status?refresh=true")

        if status_resp.status_code == 200:
            status_data = status_resp.json()
            print(f"\n📊 Contract Status:")
            print(f"   ID: {status_data['contract_id']}")
            print(f"   Status: {status_data['status']}")
            print(f"   DocuSeal Status: {status_data['docuseal_status']}")

            if status_data.get('submitters'):
                print(f"\n   👥 Submitters:")
                for sub in status_data['submitters']:
                    status_icon = {
                        'pending': '⏳',
                        'opened': '👁️',
                        'completed': '✅',
                        'declined': '❌'
                    }.get(sub.get('status', '').lower(), '❓')

                    print(f"      {status_icon} {sub.get('name', 'Unknown')} - {sub.get('status', 'unknown')}")

        # Step 6: Test voice endpoint
        print_section("STEP 6: Testing Voice Command")

        print("\n🎤 Testing voice-optimized endpoint...")
        print(f"   Command: 'Send the test purchase agreement to seller, lawyer, and agent for 123 test street'")

        # Optional - uncomment to test voice
        # voice_resp = requests.post(
        #     f"{BASE_URL}/contracts/voice/send-multi-party",
        #     json={
        #         "address_query": "123 test",
        #         "contract_name": "test purchase",
        #         "contact_roles": ["seller", "lawyer", "agent"],
        #         "order": "preserved"
        #     }
        # )
        # print(f"\n   Status: {voice_resp.status_code}")

        # Step 7: Webhook info
        print_section("STEP 7: Webhook Configuration")

        print("\n🔗 To receive real-time status updates:")
        print("\n   1. For local testing, use ngrok:")
        print("      ngrok http 8000")
        print("\n   2. In DocuSeal Settings → Webhooks, set:")
        print("      https://your-ngrok-url.ngrok.io/contracts/webhook/docuseal")
        print("\n   3. Check all 8 event boxes")
        print("\n   4. When signers take action, your database updates automatically!")

        # Summary
        print_section("TEST COMPLETE - WHAT TO DO NEXT")

        print("\n✅ Integration Working!")
        print("\n📧 Check Your Email:")
        print("   • You should see signing requests")
        print("   • Both DocuSeal and Resend emails")
        print("   • Click the signing links to test")

        print("\n🔍 Monitor Status:")
        print(f"   GET {BASE_URL}/contracts/{contract['id']}/status")

        print("\n📊 View in Database:")
        print("   • contracts table - overall status")
        print("   • contract_submitters table - individual signers")

        print("\n🎉 Your real estate contract system is LIVE!")

    else:
        error = send_resp.json()
        print(f"\n❌ Error: {error.get('detail', 'Unknown error')}")
        print("\nCommon issues:")
        print("   • DOCUSEAL_API_KEY not set in .env")
        print("   • Invalid template ID")
        print("   • Template roles don't match (Seller, Lawyer, Agent)")
        print("\nCheck your .env file and DocuSeal template settings.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
