#!/usr/bin/env python3
"""Test Resend email integration"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.resend_service import resend_service

def test_single_email():
    """Test sending a single email notification"""
    print("Testing Resend Email Integration")
    print("=" * 60)

    print("\n📧 Sending test email...")

    result = resend_service.send_contract_notification(
        to_email="emprezarioinc@gmail.com",  # Your email
        to_name="Test Recipient",
        contract_name="Purchase Agreement",
        property_address="789 Broadway, New York, NY 10003",
        docuseal_url="https://docuseal.com/s/test123",
        role="Owner",
        signing_order=1,
        is_sequential=True,
        custom_message="This is a test email from your Real Estate Contract system. Please review and sign when ready."
    )

    print("\n✅ Result:")
    print(f"   Success: {result['success']}")
    print(f"   To: {result['to']}")

    if result['success']:
        print(f"   Email ID: {result['email_id']}")
        print("\n🎉 Email sent successfully!")
        print(f"\n📬 Check your inbox at: {result['to']}")
        print("   (Check spam folder if you don't see it)")
    else:
        print(f"   Error: {result['error']}")

    return result['success']


def test_multi_party_email():
    """Test sending multi-party email notifications"""
    print("\n" + "=" * 60)
    print("Testing Multi-Party Email Notifications")
    print("=" * 60)

    submitters = [
        {
            "name": "John Smith",
            "email": "emprezarioinc@gmail.com",
            "role": "Owner",
            "docuseal_url": "https://docuseal.com/s/owner123",
            "signing_order": 1
        },
        {
            "name": "Emily Chen",
            "email": "emprezarioinc@gmail.com",
            "role": "Lawyer",
            "docuseal_url": "https://docuseal.com/s/lawyer456",
            "signing_order": 2
        },
        {
            "name": "Sarah Johnson",
            "email": "emprezarioinc@gmail.com",
            "role": "Agent",
            "docuseal_url": "https://docuseal.com/s/agent789",
            "signing_order": 3
        }
    ]

    print("\n📧 Sending multi-party notifications...")

    results = resend_service.send_multi_party_notification(
        submitters=submitters,
        contract_name="Purchase Agreement",
        property_address="789 Broadway, New York, NY",
        is_sequential=True,
        custom_message="Please review and sign in order. You'll be notified when it's your turn."
    )

    print("\n✅ Results:")
    success_count = 0
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['to']}: ", end="")
        if result['success']:
            print(f"Sent (ID: {result['email_id']})")
            success_count += 1
        else:
            print(f"Failed ({result['error']})")

    print(f"\n📊 Summary: {success_count}/{len(results)} emails sent successfully")

    if success_count > 0:
        print(f"\n📬 Check your inbox at: emprezarioinc@gmail.com")
        print("   You should see 3 emails with different signing orders!")

    return success_count == len(results)


if __name__ == "__main__":
    print("\n🚀 Starting Resend Email Tests...\n")

    try:
        # Test 1: Single email
        test1_passed = test_single_email()

        # Test 2: Multi-party emails
        test2_passed = test_multi_party_email()

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"   Single Email Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"   Multi-Party Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")

        if test1_passed and test2_passed:
            print("\n🎉 All tests passed!")
            print("\n📧 Email integration is working!")
            print("   Check emprezarioinc@gmail.com for test emails")
        else:
            print("\n⚠️  Some tests failed. Check your Resend API key.")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
