#!/usr/bin/env python3
import requests
import json

addresses = [
    "1600 Pennsylvania Avenue Washington DC",
    "350 Fifth Avenue New York",
    "312 Eisler Lane"
]

for addr in addresses:
    print(f"\n{'='*70}")
    print(f"Testing: {addr}")
    print('='*70)

    resp = requests.post(
        "http://localhost:8000/address/autocomplete",
        json={"input": addr, "country": "us"}
    )

    result = resp.json()
    suggestions = result.get('suggestions', [])

    if suggestions:
        print(f"✅ Found {len(suggestions)} results:")
        for i, s in enumerate(suggestions[:3], 1):
            print(f"   {i}. {s['description']}")
    else:
        print(f"❌ No results: {result.get('voice_prompt')}")
