"""Test script for Resend email integration.

Run this to verify your Resend setup is working correctly:

    python3 tests/test_email_service.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal
from app.services.email_service import email_service
from app.services.analytics_alert_service import AnalyticsAlertService


def test_email_service():
    """Test email service initialization."""
    print("=" * 60)
    print("RESEND EMAIL SERVICE TEST")
    print("=" * 60)

    # Check environment
    print("\n1. Checking environment configuration...")
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL")

    if api_key:
        print(f"   ✓ RESEND_API_KEY: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("   ⚠ RESEND_API_KEY: Not set")

    if from_email:
        print(f"   ✓ RESEND_FROM_EMAIL: {from_email}")
    else:
        print("   ⚠ RESEND_FROM_EMAIL: Not set (using default)")

    # Check service status
    print("\n2. Checking email service status...")
    print(f"   Email service enabled: {email_service.enabled}")

    if not email_service.enabled:
        print("\n❌ Email service is disabled!")
        print("   Set RESEND_API_KEY in your .env file")
        return False

    # Test alert email
    print("\n3. Testing alert email...")
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    print(f"   Sending test alert to: {test_email}")

    result = email_service.send_alert_notification(
        to=test_email,
        alert_name="Test Alert",
        alert_message="This is a test alert from AI Realtor platform",
        metric_name="property_views",
        metric_value=1234,
        severity="medium",
        additional_context={"test": True, "source": "email_service_test"}
    )

    if result:
        print("   ✓ Alert email sent successfully!")
    else:
        print("   ❌ Alert email failed (check domain verification)")

    # Test daily summary email
    print("\n4. Testing daily summary email...")
    db = SessionLocal()
    try:
        alert_service = AnalyticsAlertService(db)
        result = alert_service.send_daily_summary_email(
            agent_id=1,
            recipient_email=test_email
        )

        if result:
            print("   ✓ Daily summary email sent successfully!")
        else:
            print("   ❌ Daily summary email failed")
    except Exception as e:
        print(f"   ⚠ Daily summary test skipped: {e}")
    finally:
        db.close()

    # Check recent alert triggers
    print("\n5. Checking recent alert triggers...")
    db = SessionLocal()
    try:
        from app.models.analytics_alert import AnalyticsAlertTrigger

        triggers = db.query(AnalyticsAlertTrigger).order_by(
            AnalyticsAlertTrigger.created_at.desc()
        ).limit(5).all()

        print(f"   Found {len(triggers)} recent triggers:")

        for trigger in triggers:
            status_icon = "✓" if trigger.notifications_sent.get("email") else "✗"
            print(f"   {status_icon} {trigger.message[:60]}...")
            if trigger.notifications_sent.get("email"):
                print(f"      → Email sent at {trigger.notification_sent_at}")
    except Exception as e:
        print(f"   ⚠ Could not fetch triggers: {e}")
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nTroubleshooting:")
    print("• Domain not verified? → https://resend.com/domains")
    print("• API key invalid? → Check RESEND_API_KEY in .env")
    print("• Email not received? → Check https://resend.com/logs")
    print("• Setup guide: → RESEND_SETUP.md")
    print()

    return True


if __name__ == "__main__":
    test_email_service()
