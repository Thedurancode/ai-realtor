#!/usr/bin/env python3
"""
Test rate limiting by making requests until hitting the limit.

Usage:
    # Use first API key from CSV
    python scripts/test_rate_limit.py

    # Use specific API key
    python scripts/test_rate_limit.py --key sk_live_abc123...

    # Test with custom limit
    python scripts/test_rate_limit.py --limit 25
"""

import argparse
import asyncio
import csv
import sys
import time
from pathlib import Path

import httpx


async def test_rate_limit(api_key: str, base_url: str = "http://localhost:8000", max_requests: int = 25):
    """Test rate limiting by making requests until limit is hit."""

    print(f"🧪 Testing Rate Limiting")
    print(f"📡 Target: {base_url}")
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"📊 Max Requests: {max_requests}")
    print("-" * 60)

    success_count = 0
    rate_limited = False
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {api_key}"}

        for i in range(1, max_requests + 1):
            try:
                response = await client.get(
                    f"{base_url}/properties",
                    headers=headers,
                    timeout=10.0,
                )

                # Check if rate limited
                if response.status_code == 429:
                    print(f"⚠️  Request {i}: RATE LIMITED (429)")
                    print(f"   Response: {response.json()}")
                    rate_limited = True
                    break
                elif response.status_code == 200:
                    success_count += 1
                    remaining = response.headers.get("X-RateLimit-Remaining", "N/A")
                    print(f"✅ Request {i}: Success (Remaining: {remaining})")
                else:
                    print(f"❌ Request {i}: HTTP {response.status_code}")

                # Small delay between requests
                await asyncio.sleep(0.2)

            except Exception as e:
                print(f"💥 Request {i}: Error - {e}")
                break

    elapsed = time.time() - start_time

    print("-" * 60)
    print(f"📊 RESULTS")
    print(f"✅ Successful: {success_count}")
    print(f"⚠️  Rate Limited: {'Yes' if rate_limited else 'No'}")
    print(f"⏱️  Elapsed: {elapsed:.2f}s")
    print(f"📈 Avg: {elapsed/max_requests:.2f}s per request")


async def check_rate_limit_status(base_url: str = "http://localhost:8000"):
    """Check current rate limit configuration."""
    print("\n🔍 Current Rate Limit Configuration:")
    print("-" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/rate-limit")
        if response.status_code == 200:
            config = response.json()

            print(f"Enabled: {config['rate_limiting']['enabled']}")
            print(f"Message: {config['rate_limiting']['message']}")
            print(f"\nLimits:")
            print(f"  Default: {config['limits']['default']}")
            print(f"  Burst: {config['limits']['burst']}")
            print(f"\nTiers:")
            for tier, limit in config['tiers'].items():
                print(f"  {tier}: {limit}")
        else:
            print("❌ Could not fetch rate limit status")


async def main():
    parser = argparse.ArgumentParser(
        description="Test rate limiting",
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
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=25,
        help="Maximum number of requests to make",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check rate limit status, don't test",
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
                    print(f"📁 Using first API key from api_keys.csv\n")

    if not api_key:
        print("❌ No API key provided. Use --key or ensure api_keys.csv exists")
        sys.exit(1)

    # Check rate limit status
    await check_rate_limit_status(args.url)

    if not args.check_only:
        print("\n")
        await test_rate_limit(api_key, args.url, args.limit)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(1)
