#!/usr/bin/env python3
"""
Quick test of API authentication using generated API keys.

Usage:
    python scripts/test_auth.py
    python scripts/test_auth.py --key sk_live_abc123...
"""

import argparse
import csv
import sys
from pathlib import Path

import httpx


def test_authentication(api_key: str, base_url: str = "http://localhost:8000"):
    """Test API authentication."""

    print("=" * 80)
    print("🔐 Testing API Authentication")
    print("=" * 80)
    print()

    # Test 1: Public endpoint (no auth needed)
    print("Test 1: Public endpoint (no auth)")
    print("-" * 80)

    response = httpx.get(f"{base_url}/health", follow_redirects=True)
    print(f"GET {base_url}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Test 2: Protected endpoint without API key (should fail)
    print("Test 2: Protected endpoint WITHOUT API key (should fail)")
    print("-" * 80)

    response = httpx.get(f"{base_url}/properties", follow_redirects=True)
    print(f"GET {base_url}/properties")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Test 3: Protected endpoint with X-API-Key header
    print("Test 3: Protected endpoint WITH X-API-Key header")
    print("-" * 80)

    response = httpx.get(
        f"{base_url}/properties",
        headers={"X-API-Key": api_key},
        follow_redirects=True
    )
    print(f"GET {base_url}/properties")
    print(f"Header: X-API-Key: {api_key[:20]}...")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: Found {len(data)} properties")
    else:
        print(f"Response: {response.json()}")
    print()

    # Test 4: Protected endpoint with Authorization Bearer header
    print("Test 4: Protected endpoint WITH Authorization Bearer header")
    print("-" * 80)

    response = httpx.get(
        f"{base_url}/properties",
        headers={"Authorization": f"Bearer {api_key}"},
        follow_redirects=True
    )
    print(f"GET {base_url}/properties")
    print(f"Header: Authorization: Bearer {api_key[:20]}...")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: Found {len(data)} properties")
    else:
        print(f"Response: {response.json()}")
    print()

    # Test 5: Check rate limit status
    print("Test 5: Rate limit status (always public)")
    print("-" * 80)

    response = httpx.get(f"{base_url}/rate-limit", follow_redirects=True)
    print(f"GET {base_url}/rate-limit")
    print(f"Status: {response.status_code}")
    print(f"Response:")
    config = response.json()
    print(f"  Enabled: {config['rate_limiting']['enabled']}")
    print(f"  Default: {config['limits']['default']}")
    print(f"  Tiers: {config['tiers']}")
    print()

    print("=" * 80)
    print("✅ Authentication test complete!")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Test API authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--key", "-k",
        type=str,
        help="API key to use (default: first key from api_keys.csv)",
    )
    parser.add_argument(
        "--url", "-u",
        type=str,
        default="http://localhost:8000",
        help="API base URL",
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.key
    if not api_key:
        # Try to read from api_keys.csv
        csv_path = Path("api_keys.csv")
        if csv_path.exists():
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                first_row = next(reader, None)
                if first_row:
                    api_key = first_row["api_key"]
                    print(f"📁 Using first API key from api_keys.csv")
                    print(f"   Agent: {first_row['name']} ({first_row['email']})")
                    print()

    if not api_key:
        print("❌ No API key provided. Use --key or ensure api_keys.csv exists")
        print()
        print("Get an API key by registering:")
        print('  curl -X POST http://localhost:8000/agents/register \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"email":"test@example.com","name":"Test"}\'')
        sys.exit(1)

    test_authentication(api_key, args.url)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
