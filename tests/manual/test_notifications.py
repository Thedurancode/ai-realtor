#!/usr/bin/env python3
"""
Test script for real-time notifications
Sends different types of notifications to the TV display
"""
import requests
import time
import json

API_URL = "http://localhost:8000"


def test_contract_signed():
    """Test contract signed notification"""
    print("📝 Sending contract signed notification...")
    response = requests.post(f"{API_URL}/notifications/demo/contract-signed")
    print(f"Response: {response.json()}\n")
    time.sleep(3)


def test_new_lead():
    """Test new lead notification"""
    print("🎯 Sending new lead notification...")
    response = requests.post(f"{API_URL}/notifications/demo/new-lead")
    print(f"Response: {response.json()}\n")
    time.sleep(3)


def test_price_change():
    """Test price change notification"""
    print("📉 Sending price change notification...")
    response = requests.post(f"{API_URL}/notifications/demo/price-change")
    print(f"Response: {response.json()}\n")
    time.sleep(3)


def test_appointment():
    """Test appointment reminder notification"""
    print("⏰ Sending appointment reminder notification...")
    response = requests.post(f"{API_URL}/notifications/demo/appointment")
    print(f"Response: {response.json()}\n")
    time.sleep(3)


def test_custom_notification(
    notification_type: str,
    title: str,
    message: str,
    priority: str = "medium",
    icon: str = "🔔"
):
    """Send custom notification"""
    print(f"{icon} Sending custom notification: {title}...")
    payload = {
        "type": notification_type,
        "priority": priority,
        "title": title,
        "message": message,
        "icon": icon,
        "auto_dismiss_seconds": 10
    }
    response = requests.post(f"{API_URL}/notifications/", json=payload)
    print(f"Response: {response.json()}\n")
    time.sleep(3)


def test_all_notifications():
    """Run all notification tests"""
    print("=" * 60)
    print("🚀 TESTING ALL NOTIFICATION TYPES")
    print("=" * 60)
    print()

    # Test built-in demos
    test_contract_signed()
    test_new_lead()
    test_price_change()
    test_appointment()

    # Test custom notifications
    test_custom_notification(
        "property_status_change",
        "🟢 Property Now Available",
        "141 Throop Ave is now on the market for $475,000",
        priority="high",
        icon="🟢"
    )

    test_custom_notification(
        "skip_trace_complete",
        "🔍 Owner Information Found",
        "Skip trace complete for 312 Eisler Ln. Found 2 phone numbers and 1 email address.",
        priority="medium",
        icon="🔍"
    )

    test_custom_notification(
        "enrichment_complete",
        "✨ Property Data Enriched",
        "123 Main St enriched with Zestimate ($425K), 15 photos, and school ratings.",
        priority="low",
        icon="✨"
    )

    test_custom_notification(
        "general",
        "🎉 Milestone Reached!",
        "Congratulations! You've closed 10 deals this month.",
        priority="high",
        icon="🎉"
    )

    test_custom_notification(
        "general",
        "⚠️ Action Required",
        "Contract for 456 Oak Ave expires in 24 hours. Get final signatures!",
        priority="urgent",
        icon="⚠️"
    )

    print("=" * 60)
    print("✅ ALL NOTIFICATION TESTS COMPLETE")
    print("=" * 60)


def test_notification_sequence():
    """Test realistic notification sequence"""
    print("\n" + "=" * 60)
    print("📋 TESTING REALISTIC NOTIFICATION SEQUENCE")
    print("=" * 60)
    print()

    print("Scenario: New lead comes in, views property, schedules showing, signs contract\n")

    # Step 1: New lead
    test_custom_notification(
        "new_lead",
        "🎯 New Lead: Michael Chen",
        "📧 michael.chen@email.com | 📱 555-9876 | 🏠 Interested in 789 Park Lane",
        priority="high",
        icon="🎯"
    )

    # Step 2: Appointment scheduled
    test_custom_notification(
        "appointment_reminder",
        "📅 New Showing Scheduled",
        "Property showing at 789 Park Lane with Michael Chen tomorrow at 2:00 PM",
        priority="medium",
        icon="📅"
    )

    time.sleep(5)

    # Step 3: Appointment reminder
    test_custom_notification(
        "appointment_reminder",
        "⏰ Showing in 15 Minutes",
        "Meeting with Michael Chen at 789 Park Lane at 2:00 PM",
        priority="urgent",
        icon="⏰"
    )

    # Step 4: Contract sent
    test_custom_notification(
        "general",
        "📄 Contract Sent",
        "Purchase Agreement sent to Michael Chen for 789 Park Lane ($825,000)",
        priority="medium",
        icon="📄"
    )

    time.sleep(5)

    # Step 5: Contract signed
    test_custom_notification(
        "contract_signed",
        "✅ Contract Fully Signed!",
        "All parties signed Purchase Agreement for 789 Park Lane",
        priority="high",
        icon="✅"
    )

    # Step 6: Property status change
    test_custom_notification(
        "property_status_change",
        "🟡 Property Status: Pending",
        "789 Park Lane status changed from 'available' to 'pending'",
        priority="high",
        icon="🟡"
    )

    print("\n" + "=" * 60)
    print("✅ SEQUENCE TEST COMPLETE")
    print("=" * 60)


def list_notifications():
    """List recent notifications"""
    print("\n" + "=" * 60)
    print("📋 RECENT NOTIFICATIONS")
    print("=" * 60)
    response = requests.get(f"{API_URL}/notifications/?limit=20")
    notifications = response.json()

    if not notifications:
        print("No notifications found.")
        return

    for notif in notifications:
        print(f"\n{notif.get('icon', '🔔')} {notif['title']}")
        print(f"   {notif['message']}")
        print(f"   Type: {notif['type']} | Priority: {notif['priority']}")
        print(f"   Created: {notif['created_at']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        action = sys.argv[1]

        if action == "all":
            test_all_notifications()
        elif action == "sequence":
            test_notification_sequence()
        elif action == "contract":
            test_contract_signed()
        elif action == "lead":
            test_new_lead()
        elif action == "price":
            test_price_change()
        elif action == "appointment":
            test_appointment()
        elif action == "list":
            list_notifications()
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)
    else:
        print("Usage:")
        print("  python3 test_notifications.py all          - Test all notification types")
        print("  python3 test_notifications.py sequence     - Test realistic sequence")
        print("  python3 test_notifications.py contract     - Test contract signed")
        print("  python3 test_notifications.py lead         - Test new lead")
        print("  python3 test_notifications.py price        - Test price change")
        print("  python3 test_notifications.py appointment  - Test appointment")
        print("  python3 test_notifications.py list         - List recent notifications")
        sys.exit(1)
