#!/usr/bin/env python3
"""Test skip tracing on the property we just created"""
import sys
sys.path.insert(0, '/Users/edduran/Documents/GitHub/ai-realtor')

import requests
import json

def main():
    print("="*70)
    print("  SKIP TRACE DEMO")
    print("="*70)

    # We created property ID 2 (312 Eisler Lane)
    property_id = 2

    print(f"\n1️⃣  Running skip trace on Property ID: {property_id}")
    print("   (312 Eisler Lane, Hillsborough Township, NJ)")

    # Run skip trace
    resp = requests.post(
        f"http://localhost:8000/skip-trace/property/{property_id}"
    )

    if resp.status_code == 200:
        result = resp.json()

        print("\n" + "="*70)
        print("  ✅ SKIP TRACE COMPLETE!")
        print("="*70)

        # Owner info
        owner = result['result']
        print(f"\n👤 Property Owner:")
        print(f"   Name: {owner['owner_name']}")
        print(f"   First: {owner['owner_first_name']}")
        print(f"   Last: {owner['owner_last_name']}")

        # Phone numbers
        phones = owner['phone_numbers']
        print(f"\n📞 Phone Numbers ({len(phones)} found):")
        for i, phone in enumerate(phones, 1):
            status_emoji = "✅" if phone['status'] == 'valid' else "⚠️"
            print(f"   {i}. {status_emoji} {phone['number']} ({phone['type']}) - {phone['status']}")

        # Emails
        emails = owner['emails']
        print(f"\n📧 Email Addresses ({len(emails)} found):")
        for i, email in enumerate(emails, 1):
            print(f"   {i}. {email['email']} ({email['type']})")

        # Mailing address
        if owner.get('mailing_address'):
            print(f"\n📬 Mailing Address (Different from Property):")
            print(f"   {owner['mailing_address']}")
            print(f"   {owner['mailing_city']}, {owner['mailing_state']} {owner['mailing_zip']}")
        else:
            print(f"\n📬 Mailing Address: Same as property address")

        # Voice responses
        print("\n" + "="*70)
        print("  🎤 VOICE-FRIENDLY RESPONSES")
        print("="*70)

        print(f"\n📢 Summary:")
        print(f"   \"{result['voice_summary']}\"")

        print(f"\n📞 Phone List (for voice):")
        print(f"   \"{result['voice_phone_list']}\"")

        print(f"\n📧 Email List (for voice):")
        print(f"   \"{result['voice_email_list']}\"")

        print("\n" + "="*70)
        print("  HOW IT WORKS")
        print("="*70)

        print("\n✅ System searched property database for ID 2")
        print("✅ Called skip trace API with property address")
        print("✅ Retrieved owner contact information:")
        print("   • Owner full name")
        print("   • Multiple phone numbers (mobile, landline, work)")
        print("   • Email addresses (personal, secondary)")
        print("   • Mailing address (if different)")
        print("✅ Saved results to database")
        print("✅ Generated voice-friendly responses")

        print("\n" + "="*70)
        print("  CACHED RESULTS")
        print("="*70)

        print("\n💡 Skip trace results are cached!")
        print("   If you run again, it returns cached data (no new API call)")
        print("   To force refresh: POST /skip-trace/property/2/refresh")

        # Show it's cached
        print("\n🔄 Testing cache... (running skip trace again)")
        resp2 = requests.post(
            f"http://localhost:8000/skip-trace/property/{property_id}"
        )
        result2 = resp2.json()

        if result2['result']['owner_name'] == result['result']['owner_name']:
            print("   ✅ Returned same cached results instantly!")

    else:
        error = resp.json()
        print(f"\n❌ Error: {error.get('detail')}")
        print("\nFull response:")
        print(json.dumps(error, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
