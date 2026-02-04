#!/usr/bin/env python3
"""Test DocuSeal API directly to see response format"""
import httpx
import json

API_KEY = "jnTC1bKhVToZZFekCcr8BZjbZznC7KGjD14qhujcUMj"
API_URL = "http://docuseal-p8oc4sw8scksocoo80occw8c.44.203.101.160.sslip.io/api"

async def test_submission():
    payload = {
        "template_id": 1,
        "send_email": False,
        "order": "preserved",
        "submitters": [
            {
                "name": "Test User",
                "email": "emprezarioinc@gmail.com",
                "role": "First Party"
            }
        ]
    }

    headers = {
        "X-Auth-Token": API_KEY,
        "Content-Type": "application/json"
    }

    print("Sending request to DocuSeal...")
    print(f"URL: {API_URL}/submissions")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/submissions",
            json=payload,
            headers=headers,
            timeout=30.0
        )

        print(f"Status Code: {response.status_code}")
        print(f"\nResponse:")
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_submission())
