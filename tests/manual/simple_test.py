#!/usr/bin/env python3
import requests
import json

# Test autocomplete
resp = requests.post(
    "http://localhost:8000/address/autocomplete",
    json={"input": "141 Throop Ave New Brunswick NJ", "country": "us"}
)

print("Status:", resp.status_code)
print("Response:")
print(json.dumps(resp.json(), indent=2))
