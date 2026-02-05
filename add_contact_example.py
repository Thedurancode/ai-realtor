#!/usr/bin/env python3
"""
Example: Add a contact to a property
"""
import requests

API_URL = "http://localhost:8000"

# Add a buyer
response = requests.post(
    f"{API_URL}/contacts/",
    json={
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "phone": "555-1234",
        "role": "buyer",
        "property_id": 1,  # Replace with your property ID
        "company": "Johnson Real Estate",
        "notes": "Looking for 3BR in Brooklyn, budget $500K"
    }
)

print(response.json())
