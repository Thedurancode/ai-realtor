# How to Add Contacts

## Overview

Contacts can be added to properties in **3 ways**:
1. **API** - Direct HTTP requests
2. **MCP/Claude Desktop** - Natural language commands
3. **Voice API** - Voice-optimized endpoints

When you add a **buyer** or **seller**, the system automatically sends a **🎯 New Lead notification** to the TV display!

---

## Contact Roles

The system supports **13+ contact roles**:

| Role | Description | Auto-Notification? |
|------|-------------|-------------------|
| buyer | Property buyer | ✅ Yes |
| seller | Property seller | ✅ Yes |
| agent | Real estate agent | ❌ No |
| lawyer | Attorney | ❌ No |
| contractor | General contractor | ❌ No |
| inspector | Home inspector | ❌ No |
| appraiser | Property appraiser | ❌ No |
| mortgage_broker | Mortgage broker | ❌ No |
| lender | Bank/lender | ❌ No |
| title_company | Title company | ❌ No |
| tenant | Renter | ❌ No |
| landlord | Property owner | ❌ No |
| property_manager | Property manager | ❌ No |
| handyman | Handyman | ❌ No |
| plumber | Plumber | ❌ No |
| electrician | Electrician | ❌ No |
| photographer | Property photographer | ❌ No |
| stager | Home stager | ❌ No |
| other | Other role | ❌ No |

---

## Method 1: API (Python Script)

### Basic Example
```python
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
        "property_id": 1
    }
)

print(response.json())
```

### With All Fields
```python
response = requests.post(
    f"{API_URL}/contacts/",
    json={
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "phone": "555-1234",
        "role": "buyer",
        "property_id": 1,
        "company": "Johnson Real Estate",
        "notes": "Looking for 3BR in Brooklyn, budget $500K"
    }
)
```

### Multiple Contacts for Same Property
```python
# Add buyer
buyer = requests.post(f"{API_URL}/contacts/", json={
    "name": "Michael Chen",
    "email": "michael@email.com",
    "phone": "555-5678",
    "role": "buyer",
    "property_id": 1
})

# Add lawyer
lawyer = requests.post(f"{API_URL}/contacts/", json={
    "name": "Jennifer Martinez",
    "email": "jmartinez@lawfirm.com",
    "phone": "555-9999",
    "role": "lawyer",
    "property_id": 1,
    "company": "Martinez & Associates"
})

# Add inspector
inspector = requests.post(f"{API_URL}/contacts/", json={
    "name": "David Brown",
    "email": "david@inspections.com",
    "phone": "555-7777",
    "role": "inspector",
    "property_id": 1,
    "company": "Brown Inspections"
})
```

---

## Method 2: MCP/Claude Desktop

### Simple Add
```
"Add Sarah Johnson as a buyer for property 1. Her email is sarah@email.com and phone is 555-1234"
```

Claude will:
- Use `add_contact` MCP tool
- Create the contact
- **Auto-send notification** (since role is "buyer")
- TV shows: "🎯 New Lead: Sarah Johnson"

### Multiple Contacts
```
"For property 5, add Michael Chen as a buyer (michael@email.com, 555-5678) and Jennifer Martinez as the lawyer (jmartinez@lawfirm.com, 555-9999)"
```

Claude will:
- Add both contacts
- Send notification for the buyer
- No notification for lawyer

### With Company Info
```
"Add a contractor named David Brown to property 8. He's from Brown Construction, phone 555-7777"
```

---

## Method 3: Voice-Optimized API

For voice assistants and natural language parsing.

### Endpoint
```http
POST /contacts/voice
```

### Voice-Friendly Request
```python
response = requests.post(
    f"{API_URL}/contacts/voice",
    json={
        "address_query": "141 throop",  # Fuzzy address match
        "name": "Sarah Johnson",
        "role_input": "buyer",  # Natural language role
        "email": "sarah@email.com",
        "phone": "555-1234"
    }
)
```

### Role Aliases (Voice-Friendly)
The voice API understands natural language:

```python
"lawyer" → ContactRole.LAWYER
"attorney" → ContactRole.LAWYER
"contractor" → ContactRole.CONTRACTOR
"home inspector" → ContactRole.INSPECTOR
"mortgage" → ContactRole.MORTGAGE_BROKER
"mortgage broker" → ContactRole.MORTGAGE_BROKER
"bank" → ContactRole.LENDER
"title" → ContactRole.TITLE_COMPANY
"title company" → ContactRole.TITLE_COMPANY
"pm" → ContactRole.PROPERTY_MANAGER
"property manager" → ContactRole.PROPERTY_MANAGER
```

### Voice Example
```python
# User says: "Add a lawyer to 141 throop, his name is Ed Duran, 201-335-5555"

response = requests.post(
    f"{API_URL}/contacts/voice",
    json={
        "address_query": "141 throop",
        "name": "Ed Duran",
        "role_input": "lawyer",
        "phone": "201-335-5555"
    }
)

# Voice-friendly response
{
    "message": "Done! I've added Ed Duran as the lawyer for 141 Throop Avenue. Their phone is 2 0 1, 3 3 5, 5 5 5 5.",
    "contact": { ... }
}
```

---

## Complete Example Script

Save as `add_contacts.py`:

```python
#!/usr/bin/env python3
"""
Add contacts to properties
"""
import requests
import sys

API_URL = "http://localhost:8000"


def add_contact(property_id, name, email=None, phone=None, role="buyer", company=None, notes=None):
    """Add a contact to a property"""
    payload = {
        "name": name,
        "role": role,
        "property_id": property_id
    }

    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone
    if company:
        payload["company"] = company
    if notes:
        payload["notes"] = notes

    response = requests.post(f"{API_URL}/contacts/", json=payload)
    response.raise_for_status()
    return response.json()


def list_contacts_for_property(property_id):
    """List all contacts for a property"""
    response = requests.get(f"{API_URL}/contacts/property/{property_id}")
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Example: Add a buyer
    print("Adding buyer...")
    buyer = add_contact(
        property_id=1,
        name="Sarah Johnson",
        email="sarah@example.com",
        phone="555-1234",
        role="buyer",
        notes="First-time buyer, pre-approved for $500K"
    )
    print(f"✅ Added: {buyer['name']} (ID: {buyer['id']})")

    # Example: Add a lawyer
    print("\nAdding lawyer...")
    lawyer = add_contact(
        property_id=1,
        name="Jennifer Martinez",
        email="jmartinez@lawfirm.com",
        phone="555-9999",
        role="lawyer",
        company="Martinez & Associates"
    )
    print(f"✅ Added: {lawyer['name']} (ID: {lawyer['id']})")

    # List all contacts for the property
    print("\nAll contacts for property 1:")
    contacts = list_contacts_for_property(1)
    for contact in contacts:
        print(f"  - {contact['name']} ({contact['role']})")
```

Run it:
```bash
python3 add_contacts.py
```

---

## API Response

### Successful Response
```json
{
  "id": 23,
  "name": "Sarah Johnson",
  "first_name": "Sarah",
  "last_name": "Johnson",
  "email": "sarah@example.com",
  "phone": "555-1234",
  "role": "buyer",
  "property_id": 1,
  "company": null,
  "notes": "First-time buyer",
  "created_at": "2026-02-04T21:00:00.123456",
  "updated_at": "2026-02-04T21:00:00.123456"
}
```

### With Notification (Buyer/Seller)
If role is `buyer` or `seller`, you'll also see a notification on the TV display:

```
🎯 New Lead: Sarah Johnson
📧 sarah@example.com | 📱 555-1234 | 🏠 Interested in 123 Main Street
```

---

## Listing Contacts

### List All Contacts for a Property
```python
response = requests.get(f"{API_URL}/contacts/property/1")
contacts = response.json()

for contact in contacts:
    print(f"{contact['name']} - {contact['role']}")
```

### List All Contacts (Any Property)
```python
response = requests.get(f"{API_URL}/contacts/")
contacts = response.json()
```

### Filter by Role
```python
response = requests.get(f"{API_URL}/contacts/?role=buyer")
buyers = response.json()
```

---

## Updating Contacts

```python
response = requests.patch(
    f"{API_URL}/contacts/23",
    json={
        "phone": "555-9999",  # Update phone
        "notes": "Updated: Budget increased to $600K"
    }
)
```

---

## Deleting Contacts

```python
response = requests.delete(f"{API_URL}/contacts/23")
# Returns 204 No Content
```

---

## curl Examples

### Add Buyer
```bash
curl -X POST http://localhost:8000/contacts/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Johnson",
    "email": "sarah@example.com",
    "phone": "555-1234",
    "role": "buyer",
    "property_id": 1
  }'
```

### Add Lawyer
```bash
curl -X POST http://localhost:8000/contacts/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jennifer Martinez",
    "email": "jmartinez@lawfirm.com",
    "phone": "555-9999",
    "role": "lawyer",
    "property_id": 1,
    "company": "Martinez & Associates"
  }'
```

### List Contacts
```bash
# All contacts for property 1
curl http://localhost:8000/contacts/property/1

# All contacts
curl http://localhost:8000/contacts/

# Filter by role
curl http://localhost:8000/contacts/?role=buyer
```

---

## Testing with the Script

I've created `add_contact_example.py` for you:

```bash
# Edit the script first (change property_id and details)
nano add_contact_example.py

# Run it
python3 add_contact_example.py
```

---

## Real-World Workflow

### Scenario: New Property Deal

```python
# 1. Create property
property = requests.post(f"{API_URL}/properties/", json={
    "address": "123 Main Street",
    "city": "Brooklyn",
    "state": "NY",
    "zip_code": "11201",
    "price": 500000,
    "bedrooms": 3,
    "bathrooms": 2,
    "square_feet": 1500,
    "agent_id": 1
}).json()

property_id = property["id"]

# 2. Add buyer (triggers notification)
buyer = requests.post(f"{API_URL}/contacts/", json={
    "name": "Sarah Johnson",
    "email": "sarah@example.com",
    "phone": "555-1234",
    "role": "buyer",
    "property_id": property_id
}).json()

# 3. Add seller
seller = requests.post(f"{API_URL}/contacts/", json={
    "name": "Robert Smith",
    "email": "robert@example.com",
    "phone": "555-5678",
    "role": "seller",
    "property_id": property_id
}).json()

# 4. Add lawyer
lawyer = requests.post(f"{API_URL}/contacts/", json={
    "name": "Jennifer Martinez",
    "email": "jmartinez@lawfirm.com",
    "phone": "555-9999",
    "role": "lawyer",
    "property_id": property_id,
    "company": "Martinez & Associates"
}).json()

# 5. Add inspector
inspector = requests.post(f"{API_URL}/contacts/", json={
    "name": "David Brown",
    "email": "david@inspections.com",
    "phone": "555-7777",
    "role": "inspector",
    "property_id": property_id,
    "company": "Brown Inspections"
}).json()

print("✅ All contacts added!")
print(f"   Buyer: {buyer['name']}")
print(f"   Seller: {seller['name']}")
print(f"   Lawyer: {lawyer['name']}")
print(f"   Inspector: {inspector['name']}")
```

**TV Display will show:**
- 🎯 New Lead notification for Sarah Johnson (buyer)
- 🎯 New Lead notification for Robert Smith (seller)
- No notifications for lawyer/inspector (not leads)

---

## API Documentation

View full API documentation at:
```
http://localhost:8000/docs
```

Look for the **contacts** section with all endpoints.

---

**Need help?** Check:
- API Docs: http://localhost:8000/docs
- Voice Commands: VOICE_COMMANDS.md
- MCP Guide: MCP_INTEGRATION_GUIDE.md
