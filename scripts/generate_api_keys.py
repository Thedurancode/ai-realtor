#!/usr/bin/env python3
"""
Generate multiple API keys by hitting the /register endpoint.

Usage:
    python scripts/generate_api_keys.py --count 109 --output api_keys.csv

This will:
1. Register N agents via POST /register
2. Collect all API keys
3. Save to CSV with: id, name, email, api_key, created_at
"""

import argparse
import asyncio
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import httpx
from pydantic import ValidationError


class APIKeyGenerator:
    """Generate API keys via registration endpoint."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        count: int = 109,
        output: str = "api_keys.csv",
        concurrent: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.count = count
        self.output_path = Path(output)
        self.concurrent = concurrent
        self.results: List[Dict] = []
        self.errors: List[Dict] = []

    def generate_agent_data(self, index: int) -> Dict:
        """Generate unique agent registration data."""
        return {
            "email": f"agent_{index:03d}@api-generation.example.com",
            "name": f"API Agent {index:03d}",
            "phone": f"+1555{index:04d}",
            "license_number": f"LICENSE{index:06d}" if index % 2 == 0 else None,
        }

    async def register_agent(self, client: httpx.AsyncClient, index: int) -> Dict | None:
        """Register a single agent and return the result."""
        data = self.generate_agent_data(index)

        try:
            response = await client.post(
                f"{self.base_url}/agents/register",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30.0,
            )

            if response.status_code == 201:
                result = response.json()
                print(f"✅ Agent {index:03d}: {result['email']} -> {result['api_key'][:20]}...")
                return result
            else:
                error_detail = response.text
                self.errors.append({
                    "index": index,
                    "email": data["email"],
                    "status": response.status_code,
                    "error": error_detail,
                })
                print(f"❌ Agent {index:03d}: HTTP {response.status_code} - {error_detail}")
                return None

        except httpx.TimeoutException:
            self.errors.append({
                "index": index,
                "email": data["email"],
                "status": "timeout",
                "error": "Request timed out",
            })
            print(f"⏱️  Agent {index:03d}: Timeout")
            return None
        except Exception as e:
            self.errors.append({
                "index": index,
                "email": data["email"],
                "status": "exception",
                "error": str(e),
            })
            print(f"💥 Agent {index:03d}: {e}")
            return None

    async def generate_all(self):
        """Generate all API keys with concurrent requests."""
        print(f"🚀 Generating {self.count} API keys...")
        print(f"📡 Target: {self.base_url}/agents/register")
        print(f"⚡ Concurrency: {self.concurrent}")
        print("-" * 60)

        # Use a semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.concurrent)

        async def bounded_register(client: httpx.AsyncClient, index: int):
            async with semaphore:
                return await self.register_agent(client, index)

        async with httpx.AsyncClient(limits=httpx.Limits(max_connections=self.concurrent)) as client:
            tasks = [bounded_register(client, i) for i in range(1, self.count + 1)]
            results = await asyncio.gather(*tasks)

        # Filter out None results (failed registrations)
        self.results = [r for r in results if r is not None]

    def save_to_csv(self):
        """Save all results to CSV file."""
        if not self.results:
            print("❌ No successful registrations to save!")
            return

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "email", "api_key", "created_at"])
            writer.writeheader()

            for result in self.results:
                writer.writerow({
                    "id": result.get("id"),
                    "name": result.get("name"),
                    "email": result.get("email"),
                    "api_key": result.get("api_key"),
                    "created_at": result.get("created_at"),
                })

        print("-" * 60)
        print(f"✅ Saved {len(self.results)} API keys to: {self.output_path.absolute()}")

    def print_summary(self):
        """Print generation summary."""
        print("\n📊 SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {len(self.results)}/{self.count}")
        print(f"❌ Failed:     {len(self.errors)}/{self.count}")
        print(f"📁 Output:     {self.output_path.absolute()}")

        if self.errors:
            print(f"\n⚠️  Errors ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  - Agent {error['index']}: {error['error']}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")

    def save_errors_to_csv(self):
        """Save errors to a separate CSV file."""
        if not self.errors:
            return

        error_path = self.output_path.parent / f"{self.output_path.stem}_errors{self.output_path.suffix}"

        with open(error_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["index", "email", "status", "error"])
            writer.writeheader()

            for error in self.errors:
                writer.writerow(error)

        print(f"📄 Saved errors to: {error_path.absolute()}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate API keys via registration endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 109 keys (default)
  python scripts/generate_api_keys.py

  # Generate 50 keys
  python scripts/generate_api_keys.py --count 50

  # Custom output file
  python scripts/generate_api_keys.py --count 109 --output keys/production.csv

  # Target production server
  python scripts/generate_api_keys.py --url https://ai-realtor.fly.dev
        """,
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=109,
        help="Number of API keys to generate (default: 109)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="api_keys.csv",
        help="Output CSV file path (default: api_keys.csv)",
    )
    parser.add_argument(
        "--url", "-u",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--concurrent", "-j",
        type=int,
        default=10,
        help="Max concurrent requests (default: 10)",
    )

    args = parser.parse_args()

    # Confirm
    print(f"🎯 About to generate {args.count} API keys")
    print(f"📡 Target: {args.url}/agents/register")
    print(f"📁 Output: {Path(args.output).absolute()}")
    confirm = input("\nProceed? (y/N): ")

    if confirm.lower() != "y":
        print("❌ Aborted")
        sys.exit(0)

    # Generate
    generator = APIKeyGenerator(
        base_url=args.url,
        count=args.count,
        output=args.output,
        concurrent=args.concurrent,
    )

    await generator.generate_all()
    generator.save_to_csv()
    generator.save_errors_to_csv()
    generator.print_summary()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
