"""
Test Compliance Engine

This script demonstrates the compliance engine functionality.
Run after deploying the backend.
"""
import requests
import json
from datetime import datetime

# API base URL
API_URL = "https://ai-realtor.fly.dev"
# For local testing: API_URL = "http://localhost:8000"


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_run_compliance_check():
    """Test running a compliance check on a property"""
    print_section("1. Run Compliance Check")

    # First, get a property to check
    response = requests.get(f"{API_URL}/properties/")
    properties = response.json()

    if not properties:
        print("❌ No properties found. Please add a property first.")
        return

    property_id = properties[0]['id']
    address = properties[0]['address']

    print(f"\n📋 Running compliance check on property {property_id}: {address}")

    # Run compliance check
    response = requests.post(
        f"{API_URL}/compliance/properties/{property_id}/check",
        params={"check_type": "full"}
    )

    if response.status_code == 200:
        check = response.json()
        print(f"\n✅ Compliance check completed!")
        print(f"   Check ID: {check['id']}")
        print(f"   Status: {check['status']}")
        print(f"   Rules checked: {check['total_rules_checked']}")
        print(f"   Passed: {check['passed_count']}")
        print(f"   Failed: {check['failed_count']}")
        print(f"   Warnings: {check['warning_count']}")
        print(f"\n📝 Summary:")
        print(f"   {check['ai_summary']}")

        if check.get('violations'):
            print(f"\n⚠️  Found {len(check['violations'])} violations:")
            for i, v in enumerate(check['violations'][:5], 1):
                print(f"\n   {i}. {v['violation_message']}")
                print(f"      Severity: {v['severity']}")
                print(f"      Explanation: {v['ai_explanation']}")
                if v.get('recommendation'):
                    print(f"      Fix: {v['recommendation']}")

        return check['id']
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None


def test_get_compliance_report(property_id):
    """Test getting a compliance report"""
    print_section("2. Get Compliance Report")

    response = requests.get(f"{API_URL}/compliance/properties/{property_id}/report")

    if response.status_code == 200:
        report = response.json()
        print(f"\n📊 Compliance Report for {report['property_address']}")
        print(f"   State: {report['property_state']}")
        print(f"   Overall Status: {report['overall_status']}")
        print(f"   Ready to List: {'✅ Yes' if report['is_ready_to_list'] else '❌ No'}")

        stats = report['statistics']
        print(f"\n   Statistics:")
        print(f"   • Total rules checked: {stats['total_rules_checked']}")
        print(f"   • Passed: {stats['passed']}")
        print(f"   • Failed: {stats['failed']}")
        print(f"   • Warnings: {stats['warnings']}")

        violations = report['violations_by_severity']
        if any(violations.values()):
            print(f"\n   Violations by Severity:")
            for severity, vlist in violations.items():
                if vlist:
                    print(f"   • {severity.upper()}: {len(vlist)}")

        if report.get('estimated_total_fix_cost'):
            print(f"\n   💰 Estimated fix cost: ${report['estimated_total_fix_cost']:,.2f}")
        if report.get('estimated_total_fix_time_days'):
            print(f"   ⏱️  Estimated fix time: {report['estimated_total_fix_time_days']} days")
    else:
        print(f"❌ Error: {response.status_code}")


def test_voice_compliance_check():
    """Test voice-optimized compliance check"""
    print_section("3. Voice Compliance Check")

    # Get a property
    response = requests.get(f"{API_URL}/properties/")
    properties = response.json()

    if not properties:
        print("❌ No properties found.")
        return

    # Use part of the address
    address = properties[0]['address']
    search_term = address.split()[0]  # Use first word

    print(f"\n🎤 Voice command: 'Run compliance check on {search_term}'")

    response = requests.post(
        f"{API_URL}/compliance/voice/check",
        json={
            "address_query": search_term,
            "check_type": "full"
        }
    )

    if response.status_code == 200:
        result = response.json()
        print(f"\n🤖 Voice Response:")
        print(f"   {result['voice_confirmation']}")
        print(f"\n   {result['voice_summary']}")
    else:
        print(f"❌ Error: {response.status_code}")


def test_voice_compliance_status():
    """Test voice compliance status check"""
    print_section("4. Voice Compliance Status")

    # Get a property
    response = requests.get(f"{API_URL}/properties/")
    properties = response.json()

    if not properties:
        print("❌ No properties found.")
        return

    address = properties[0]['address']
    search_term = address.split()[0]

    print(f"\n🎤 Voice command: 'Is {search_term} ready to list?'")

    response = requests.get(
        f"{API_URL}/compliance/voice/status",
        params={"address_query": search_term}
    )

    if response.status_code == 200:
        result = response.json()
        print(f"\n🤖 Voice Response:")
        print(f"   {result['voice_response']}")
    else:
        print(f"❌ Error: {response.status_code}")


def test_quick_check():
    """Test quick compliance check"""
    print_section("5. Quick Compliance Check")

    response = requests.get(f"{API_URL}/properties/")
    properties = response.json()

    if not properties:
        print("❌ No properties found.")
        return

    property_id = properties[0]['id']
    address = properties[0]['address']

    print(f"\n⚡ Running quick check on {address}...")

    response = requests.post(
        f"{API_URL}/compliance/properties/{property_id}/quick-check"
    )

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Quick Check Result:")
        print(f"   Status: {result['status']}")
        print(f"   Ready to list: {'✅ Yes' if result['is_ready_to_list'] else '❌ No'}")
        print(f"   Passed: {result['passed']}/{result['total_rules_checked']}")
        print(f"   Failed: {result['failed']}")
        print(f"   Warnings: {result['warnings']}")
    else:
        print(f"❌ Error: {response.status_code}")


def test_compliance_history():
    """Test getting compliance history"""
    print_section("6. Compliance Check History")

    response = requests.get(f"{API_URL}/properties/")
    properties = response.json()

    if not properties:
        print("❌ No properties found.")
        return

    property_id = properties[0]['id']
    address = properties[0]['address']

    print(f"\n📜 Compliance history for {address}:")

    response = requests.get(f"{API_URL}/compliance/properties/{property_id}/checks")

    if response.status_code == 200:
        checks = response.json()
        if checks:
            for i, check in enumerate(checks, 1):
                print(f"\n   {i}. Check #{check['id']}")
                print(f"      Date: {check['created_at']}")
                print(f"      Status: {check['status']}")
                print(f"      Failed: {check['failed_count']}, Warnings: {check['warning_count']}")
        else:
            print("   No compliance checks found.")
    else:
        print(f"❌ Error: {response.status_code}")


def run_all_tests():
    """Run all compliance engine tests"""
    print("\n" + "=" * 60)
    print("  COMPLIANCE ENGINE TEST SUITE")
    print("  Testing: " + API_URL)
    print("=" * 60)

    try:
        # Test 1: Run compliance check
        check_id = test_run_compliance_check()

        # Test 2: Get first property for remaining tests
        response = requests.get(f"{API_URL}/properties/")
        properties = response.json()

        if properties:
            property_id = properties[0]['id']

            # Test 2: Get compliance report
            test_get_compliance_report(property_id)

            # Test 3: Voice compliance check
            test_voice_compliance_check()

            # Test 4: Voice status check
            test_voice_compliance_status()

            # Test 5: Quick check
            test_quick_check()

            # Test 6: Compliance history
            test_compliance_history()

        print("\n" + "=" * 60)
        print("  ✅ ALL TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error running tests: {str(e)}")


if __name__ == "__main__":
    print("\n🧪 Compliance Engine Test Script")
    print("=" * 60)
    print("\nOptions:")
    print("1. Run all tests")
    print("2. Test individual property")
    print("3. Test voice commands")

    choice = input("\nEnter choice (1-3) or press Enter for all tests: ").strip()

    if choice == "2":
        # Test individual property
        prop_id = input("Enter property ID: ").strip()
        if prop_id.isdigit():
            test_get_compliance_report(int(prop_id))
    elif choice == "3":
        # Test voice commands
        test_voice_compliance_check()
        test_voice_compliance_status()
    else:
        # Run all tests
        run_all_tests()

    print("\n✅ Testing complete!\n")
