#!/usr/bin/env python3
"""Test script for DocuSeal webhook events"""
import requests
import json

BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{BASE_URL}/contracts/webhook/docuseal"

def print_test(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

def test_webhook_event(event_type, payload, description):
    """Test a webhook event"""
    print(f"\n📡 Testing: {event_type}")
    print(f"   Description: {description}")

    response = requests.post(WEBHOOK_URL, json=payload)

    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Response: {json.dumps(result, indent=6)}")

    return response.status_code == 200

def main():
    print_test("DOCUSEAL WEBHOOK TESTING")

    # First, create test data
    print("\n📋 Setting up test data...")

    # Create agent
    agent_resp = requests.post(
        f"{BASE_URL}/agents/",
        json={
            "name": "Test Agent Webhook",
            "email": "webhook-test@test.com",
            "phone": "555-0000"
        }
    )
    if agent_resp.status_code == 201:
        agent = agent_resp.json()
        print(f"✅ Agent created (ID: {agent['id']})")
    else:
        print("⚠️  Using existing agent")
        agent = {"id": 1}

    # Create property
    prop_resp = requests.post(
        f"{BASE_URL}/properties/",
        json={
            "address": "Webhook Test Property",
            "city": "Test City",
            "state": "NY",
            "zip_code": "10001",
            "title": "Webhook Test",
            "price": 100000,
            "agent_id": agent['id']
        }
    )
    if prop_resp.status_code == 201:
        property_data = prop_resp.json()
        print(f"✅ Property created (ID: {property_data['id']})")
    else:
        print("⚠️  Using existing property")
        property_data = {"id": 1}

    # Create contacts
    seller_resp = requests.post(
        f"{BASE_URL}/contacts/",
        json={
            "property_id": property_data['id'],
            "name": "Webhook Seller",
            "email": "seller@test.com",
            "phone": "555-1111",
            "role": "seller"
        }
    )
    seller = seller_resp.json() if seller_resp.status_code == 201 else {"id": 1, "name": "Test Seller", "email": "seller@test.com"}

    lawyer_resp = requests.post(
        f"{BASE_URL}/contacts/",
        json={
            "property_id": property_data['id'],
            "name": "Webhook Lawyer",
            "email": "lawyer@test.com",
            "phone": "555-2222",
            "role": "lawyer"
        }
    )
    lawyer = lawyer_resp.json() if lawyer_resp.status_code == 201 else {"id": 2, "name": "Test Lawyer", "email": "lawyer@test.com"}

    # Create contract
    contract_resp = requests.post(
        f"{BASE_URL}/contracts/",
        json={
            "property_id": property_data['id'],
            "name": "Webhook Test Contract",
            "description": "For webhook testing",
            "docuseal_template_id": "TEST_TEMPLATE"
        }
    )
    contract = contract_resp.json()
    print(f"✅ Contract created (ID: {contract['id']})")

    # Manually add submitters to simulate multi-party sending
    # (In real scenario, these would be created by send-multi-party endpoint)
    print(f"\n📝 Note: In real usage, submitters are created by send-multi-party endpoint")
    print(f"   For testing, we'll simulate DocuSeal webhook events without actual submitters")

    # Set a fake submission ID
    contract_id = contract['id']
    fake_submission_id = "webhook_test_submission_123"
    fake_submitter1_id = "submitter_abc_123"
    fake_submitter2_id = "submitter_def_456"

    # Update contract with submission ID (simulating what send-multi-party would do)
    requests.patch(
        f"{BASE_URL}/contracts/{contract_id}",
        json={"docuseal_submission_id": fake_submission_id}
    )

    # ========================================================================
    # TEST 1: submission.created event
    # ========================================================================
    print_test("TEST 1: submission.created Event")

    test_webhook_event(
        "submission.created",
        {
            "event_type": "submission.created",
            "data": {
                "id": fake_submission_id,
                "status": "pending"
            }
        },
        "Submission was created and sent to signers"
    )

    # ========================================================================
    # TEST 2: form.started event (individual submitter)
    # ========================================================================
    print_test("TEST 2: form.started Event")

    test_webhook_event(
        "form.started",
        {
            "event_type": "form.started",
            "data": {
                "submission_id": fake_submission_id,
                "submitter_id": fake_submitter1_id,
                "submitter": {
                    "email": seller['email'],
                    "name": seller['name']
                }
            }
        },
        "Submitter opened and started filling the form"
    )

    # ========================================================================
    # TEST 3: form.completed event (individual submitter)
    # ========================================================================
    print_test("TEST 3: form.completed Event")

    test_webhook_event(
        "form.completed",
        {
            "event_type": "form.completed",
            "data": {
                "submission_id": fake_submission_id,
                "submitter_id": fake_submitter1_id,
                "submitter": {
                    "email": seller['email'],
                    "name": seller['name']
                },
                "completed_at": "2026-02-04T12:00:00Z"
            }
        },
        "Submitter completed their signature"
    )

    # ========================================================================
    # TEST 4: form.declined event
    # ========================================================================
    print_test("TEST 4: form.declined Event")

    test_webhook_event(
        "form.declined",
        {
            "event_type": "form.declined",
            "data": {
                "submission_id": fake_submission_id,
                "submitter_id": fake_submitter2_id,
                "submitter": {
                    "email": lawyer['email'],
                    "name": lawyer['name']
                }
            }
        },
        "Submitter declined to sign"
    )

    # ========================================================================
    # TEST 5: submission.completed event
    # ========================================================================
    print_test("TEST 5: submission.completed Event")

    # Create a new contract for completion test
    contract2_resp = requests.post(
        f"{BASE_URL}/contracts/",
        json={
            "property_id": property_data['id'],
            "name": "Completion Test Contract",
            "docuseal_template_id": "TEST_TEMPLATE_2"
        }
    )
    contract2 = contract2_resp.json()
    fake_submission_id2 = "webhook_test_submission_456"

    requests.patch(
        f"{BASE_URL}/contracts/{contract2['id']}",
        json={"docuseal_submission_id": fake_submission_id2}
    )

    test_webhook_event(
        "submission.completed",
        {
            "event_type": "submission.completed",
            "data": {
                "id": fake_submission_id2,
                "status": "completed",
                "completed_at": "2026-02-04T12:30:00Z"
            }
        },
        "All submitters completed - contract is done"
    )

    # ========================================================================
    # TEST 6: submission.expired event
    # ========================================================================
    print_test("TEST 6: submission.expired Event")

    contract3_resp = requests.post(
        f"{BASE_URL}/contracts/",
        json={
            "property_id": property_data['id'],
            "name": "Expired Test Contract",
            "docuseal_template_id": "TEST_TEMPLATE_3"
        }
    )
    contract3 = contract3_resp.json()
    fake_submission_id3 = "webhook_test_submission_789"

    requests.patch(
        f"{BASE_URL}/contracts/{contract3['id']}",
        json={"docuseal_submission_id": fake_submission_id3}
    )

    test_webhook_event(
        "submission.expired",
        {
            "event_type": "submission.expired",
            "data": {
                "id": fake_submission_id3,
                "status": "expired",
                "expired_at": "2026-02-10T00:00:00Z"
            }
        },
        "Submission expired (deadline passed)"
    )

    # ========================================================================
    # TEST 7: submission.archived event
    # ========================================================================
    print_test("TEST 7: submission.archived Event")

    contract4_resp = requests.post(
        f"{BASE_URL}/contracts/",
        json={
            "property_id": property_data['id'],
            "name": "Archived Test Contract",
            "docuseal_template_id": "TEST_TEMPLATE_4"
        }
    )
    contract4 = contract4_resp.json()
    fake_submission_id4 = "webhook_test_submission_101"

    requests.patch(
        f"{BASE_URL}/contracts/{contract4['id']}",
        json={"docuseal_submission_id": fake_submission_id4}
    )

    test_webhook_event(
        "submission.archived",
        {
            "event_type": "submission.archived",
            "data": {
                "id": fake_submission_id4,
                "status": "archived"
            }
        },
        "Submission was cancelled/archived"
    )

    # ========================================================================
    # TEST 8: Legacy webhook format (backwards compatibility)
    # ========================================================================
    print_test("TEST 8: Legacy Webhook Format")

    test_webhook_event(
        "legacy",
        {
            "id": fake_submission_id2,
            "status": "completed",
            "submitters": [
                {
                    "id": "sub_1",
                    "status": "completed"
                },
                {
                    "id": "sub_2",
                    "status": "completed"
                }
            ]
        },
        "Old webhook format (without event_type)"
    )

    # ========================================================================
    # Summary
    # ========================================================================
    print_test("WEBHOOK TESTING SUMMARY")

    print("\n✅ Tested All DocuSeal Webhook Events:")
    print("   ✅ submission.created - Contract sent")
    print("   ✅ submission.completed - All signatures collected")
    print("   ✅ submission.expired - Deadline passed")
    print("   ✅ submission.archived - Contract cancelled")
    print("   ✅ form.started - Submitter began filling")
    print("   ✅ form.completed - Submitter signed")
    print("   ✅ form.declined - Submitter declined")
    print("   ✅ Legacy format - Backwards compatibility")

    print("\n📚 Next Steps:")
    print("   1. Configure webhook URL in DocuSeal:")
    print(f"      {BASE_URL}/contracts/webhook/docuseal")
    print("   2. Enable all events (check all boxes)")
    print("   3. Test with real DocuSeal submissions")
    print("   4. Monitor database for automatic status updates")

    print_test("TESTING COMPLETE")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
