#!/usr/bin/env python3
"""Send a real test contract with working signing links"""
import sys
sys.path.insert(0, '/Users/edduran/Documents/GitHub/ai-realtor')

import requests
import json

BASE_URL = "http://localhost:8000"
TEMPLATE_ID = "1"  # Your template ID

def main():
    print("="*70)
    print("  SENDING REAL CONTRACT WITH WORKING SIGNING LINKS")
    print("="*70)

    # Step 1: Create agent
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
        agent = {"id": 1, "name": "Test Agent", "email": "emprezarioinc@gmail.com"}
        print(f"⚠️  Using existing agent")

    # Step 2: Create property
    print("\n2. Creating property...")
    prop_resp = requests.post(
        f"{BASE_URL}/properties/",
        json={
            "address": "123 Main Street",
            "city": "Brooklyn",
            "state": "NY",
            "zip_code": "11201",
            "title": "Test Property for Real Contract",
            "price": 500000,
            "agent_id": agent['id']
        }
    )

    if prop_resp.status_code == 201:
        property_data = prop_resp.json()
        print(f"✅ Property: {property_data['address']} (ID: {property_data['id']})")
    else:
        print(f"❌ Error creating property: {prop_resp.text}")
        return

    # Step 3: Create contacts
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

    # Step 4: Create contract
    print("\n4. Creating contract...")
    contract_resp = requests.post(
        f"{BASE_URL}/contracts/",
        json={
            "property_id": property_data['id'],
            "name": "Short Sale Process Walkthrough",
            "description": "Real contract test with working signing links",
            "docuseal_template_id": TEMPLATE_ID
        }
    )

    if contract_resp.status_code == 201:
        contract = contract_resp.json()
        print(f"✅ Contract: {contract['name']} (ID: {contract['id']})")
        print(f"   Template ID: {contract['docuseal_template_id']}")
    else:
        print(f"❌ Error: {contract_resp.text}")
        return

    # Step 5: Send contract
    print("\n5. Sending contract via DocuSeal...")
    print("   This will create real signing links!")

    send_resp = requests.post(
        f"{BASE_URL}/contracts/{contract['id']}/send-multi-party",
        json={
            "submitters": [
                {
                    "contact_id": seller['id'],
                    "name": seller['name'],
                    "email": seller['email'],
                    "role": "First Party",
                    "signing_order": 1
                }
            ],
            "order": "preserved",
            "message": "Please review and sign this document. This is a test with real signing links."
        }
    )

    print(f"\n📊 Response Status: {send_resp.status_code}")

    if send_resp.status_code == 200:
        result = send_resp.json()
        print("\n✅ SUCCESS!")
        print(f"\n📢 {result['voice_confirmation']}")

        print(f"\n👥 Submitters:")
        for sub in result['submitters']:
            print(f"   • {sub['name']} ({sub['role']}) - {sub['status']}")

        if result.get('docuseal_url'):
            print(f"\n🔗 DocuSeal Submission URL:")
            print(f"   {result['docuseal_url']}")

        print("\n" + "="*70)
        print("  CHECK YOUR EMAIL NOW!")
        print("="*70)
        print(f"\n📬 Email: emprezarioinc@gmail.com")
        print("\nYou should receive:")
        print("   1. DocuSeal signing email (from DocuSeal)")
        print("   2. Beautiful Resend notification (from your system)")
        print("\n⚠️  Check SPAM folder if you don't see them!")
        print("\n✅ The signing links in these emails will WORK!")
        print("   Click them to actually sign the document.")

        # Get the signing URL
        if result.get('submitters'):
            for sub in result['submitters']:
                if sub.get('docuseal_url'):
                    print(f"\n🔗 Direct Signing Link:")
                    print(f"   {sub['docuseal_url']}")

        print("\n" + "="*70)

    else:
        error = send_resp.json()
        print(f"\n❌ Error: {error.get('detail', 'Unknown error')}")
        print("\nResponse:")
        print(json.dumps(error, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
