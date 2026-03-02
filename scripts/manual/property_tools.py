#!/usr/bin/env python3
"""
Property Management Tools - MCP-style CRUD operations for properties
"""
import requests
import json
import sys
from typing import Optional


API_URL = "http://localhost:8000"


def create_property(
    address: str,
    city: str,
    state: str,
    zip_code: str,
    price: float,
    title: Optional[str] = None,
    description: Optional[str] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,
    square_feet: Optional[int] = None,
    property_type: str = "house",
    status: str = "available",
    agent_id: int = 1
):
    """Create a new property"""
    property_data = {
        "address": address,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "price": price,
        "property_type": property_type,
        "status": status,
        "agent_id": agent_id,
        "title": title if title else f"Property at {address}"
    }
    if description:
        property_data["description"] = description
    if bedrooms:
        property_data["bedrooms"] = bedrooms
    if bathrooms:
        property_data["bathrooms"] = bathrooms
    if square_feet:
        property_data["square_feet"] = square_feet

    response = requests.post(f"{API_URL}/properties/", json=property_data)
    return response.json()


def get_properties():
    """Get all properties"""
    response = requests.get(f"{API_URL}/properties/")
    return response.json()


def get_property(property_id: int):
    """Get a specific property by ID"""
    response = requests.get(f"{API_URL}/properties/{property_id}")
    return response.json()


def update_property(property_id: int, **updates):
    """Update a property"""
    response = requests.put(f"{API_URL}/properties/{property_id}", json=updates)
    return response.json()


def delete_property(property_id: int):
    """Delete a property"""
    response = requests.delete(f"{API_URL}/properties/{property_id}")
    return {"status": "deleted", "property_id": property_id}


def search_properties(address: Optional[str] = None, city: Optional[str] = None,
                      min_price: Optional[float] = None, max_price: Optional[float] = None):
    """Search properties with filters"""
    params = {}
    if address:
        params["address"] = address
    if city:
        params["city"] = city
    if min_price:
        params["min_price"] = min_price
    if max_price:
        params["max_price"] = max_price

    response = requests.get(f"{API_URL}/properties/", params=params)
    return response.json()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Property Management Tools - CRUD Operations")
        print("\nUsage:")
        print("  python3 scripts/manual/property_tools.py create <address> <city> <state> <zip> <price> [options]")
        print("  python3 scripts/manual/property_tools.py list")
        print("  python3 scripts/manual/property_tools.py get <property_id>")
        print("  python3 scripts/manual/property_tools.py update <property_id> <field> <value>")
        print("  python3 scripts/manual/property_tools.py delete <property_id>")
        print("  python3 scripts/manual/property_tools.py search <query>")
        print("\nExamples:")
        print('  python3 scripts/manual/property_tools.py create "123 Main St" "New York" "NY" "10001" 500000')
        print('  python3 scripts/manual/property_tools.py list')
        print('  python3 scripts/manual/property_tools.py get 1')
        print('  python3 scripts/manual/property_tools.py update 1 price 550000')
        print('  python3 scripts/manual/property_tools.py delete 1')
        print('  python3 scripts/manual/property_tools.py search "broadway"')
        sys.exit(1)

    action = sys.argv[1]

    if action == "create" and len(sys.argv) >= 7:
        address = sys.argv[2]
        city = sys.argv[3]
        state = sys.argv[4]
        zip_code = sys.argv[5]
        price = float(sys.argv[6])

        result = create_property(address, city, state, zip_code, price)
        print(json.dumps(result, indent=2))

    elif action == "list":
        result = get_properties()
        print(json.dumps(result, indent=2))

    elif action == "get" and len(sys.argv) >= 3:
        property_id = int(sys.argv[2])
        result = get_property(property_id)
        print(json.dumps(result, indent=2))

    elif action == "update" and len(sys.argv) >= 5:
        property_id = int(sys.argv[2])
        field = sys.argv[3]
        value = sys.argv[4]

        # Try to convert to appropriate type
        try:
            value = float(value) if '.' in value else int(value)
        except ValueError:
            pass  # Keep as string

        updates = {field: value}
        result = update_property(property_id, **updates)
        print(json.dumps(result, indent=2))

    elif action == "delete" and len(sys.argv) >= 3:
        property_id = int(sys.argv[2])
        result = delete_property(property_id)
        print(json.dumps(result, indent=2))

    elif action == "search" and len(sys.argv) >= 3:
        query = sys.argv[2]
        result = search_properties(address=query)
        print(json.dumps(result, indent=2))

    else:
        print("Invalid command")
        sys.exit(1)
