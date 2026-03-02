#!/usr/bin/env python3
"""Diagnose DocuSeal API connectivity and authentication"""
import httpx
import sys

API_KEY = "21e1fa6f36ddff7350813d82fc41c5e0-96164d60-9750fbd5"

def test_endpoint(url, name):
    """Test a DocuSeal API endpoint"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*70)

    headers = {
        "X-Auth-Token": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = httpx.get(
            f"{url}/templates",
            headers=headers,
            params={"limit": 1},
            timeout=10.0
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")

        if response.status_code == 200:
            print("✅ SUCCESS! API key is valid for this endpoint")
            return True
        elif response.status_code == 401:
            print("❌ AUTHENTICATION FAILED")
            return False
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ CONNECTION ERROR: {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("  DOCUSEAL API DIAGNOSTIC TOOL")
    print("="*70)

    print(f"\n🔑 Testing API Key: {API_KEY[:20]}...")

    # Test standard endpoints
    endpoints = [
        ("https://api.docuseal.com", "Global Cloud Server"),
        ("https://api.docuseal.eu", "EU Cloud Server"),
    ]

    success = False
    for url, name in endpoints:
        if test_endpoint(url, name):
            success = True
            print(f"\n🎉 Found working endpoint: {url}")
            print(f"\nUpdate your .env file:")
            print(f"DOCUSEAL_API_URL={url}")
            break

    if not success:
        print("\n" + "="*70)
        print("  TROUBLESHOOTING GUIDE")
        print("="*70)

        print("\n❌ The API key is not valid for any DocuSeal cloud server.")
        print("\nPossible issues:")
        print("\n1. API Key is Incorrect")
        print("   • Double-check you copied the full API key")
        print("   • Make sure there are no extra spaces or characters")

        print("\n2. Using Self-Hosted DocuSeal")
        print("   • If you're running your own DocuSeal instance,")
        print("     you need to use your custom API URL")
        print("   • Example: https://your-docuseal-domain.com")
        print("   • Check your DocuSeal installation URL")

        print("\n3. Get API Key from Correct Location")
        print("   • For Cloud: https://console.docuseal.com")
        print("     - Log in to your account")
        print("     - Go to Settings → API")
        print("     - Copy the API key shown there")

        print("\n4. API Key Might Be Expired or Revoked")
        print("   • Generate a new API key from your DocuSeal console")

        print("\n" + "="*70)
        print("  NEXT STEPS")
        print("="*70)

        print("\n1. Log in to https://console.docuseal.com")
        print("2. Go to Settings → API")
        print("3. Copy your API key (should look like: sk_...)")
        print("4. Update .env file with the correct key")
        print("5. Run this script again to verify")

        print("\nOR")

        print("\nIf using self-hosted DocuSeal:")
        print("1. Find your DocuSeal installation URL")
        print("2. Go to YOUR_URL/settings/api")
        print("3. Copy your API key")
        print("4. Update .env with:")
        print("   DOCUSEAL_API_URL=YOUR_URL")
        print("   DOCUSEAL_API_KEY=YOUR_KEY")

if __name__ == "__main__":
    main()
