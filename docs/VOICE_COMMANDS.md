# Voice Command Examples for Contract Sending

## 🎤 Natural Language Contract Sending

You can now say: **"Send the property agreement to the lawyer on file for 141 throop"**

## How It Works

### Single API Call Does Everything:

```bash
POST /contracts/voice/send
{
  "address_query": "141 throop",
  "contract_name": "property agreement",
  "contact_role": "lawyer"
}
```

### What Happens Automatically:

1. ✅ **Finds Property** - Searches for "141 throop" in addresses
2. ✅ **Finds Contact** - Looks up the "lawyer" for that property
3. ✅ **Finds/Creates Contract** - Looks for "property agreement" or creates it
4. ✅ **Sends via DocuSeal** - Emails contract to lawyer's email
5. ✅ **Returns Confirmation** - "Done! I've sent the Property Agreement to John Lawyer..."

## Real-World Voice Commands

### Send to Lawyer
```json
{
  "address_query": "141 throop",
  "contract_name": "property agreement",
  "contact_role": "lawyer"
}
```
**Voice:** "Send the property agreement to the lawyer for 141 throop"

### Send to Buyer
```json
{
  "address_query": "main street",
  "contract_name": "purchase agreement",
  "contact_role": "buyer"
}
```
**Voice:** "Send the purchase agreement to the buyer for main street"

### Send to Inspector
```json
{
  "address_query": "oak avenue",
  "contract_name": "inspection waiver",
  "contact_role": "inspector"
}
```
**Voice:** "Send the inspection waiver to the inspector for oak avenue"

### Send to Seller
```json
{
  "address_query": "elm",
  "contract_name": "listing agreement",
  "contact_role": "seller"
}
```
**Voice:** "Send the listing agreement to the seller for elm"

### Send to Contractor
```json
{
  "address_query": "brooklyn",
  "contract_name": "repair agreement",
  "contact_role": "contractor"
}
```
**Voice:** "Send the repair agreement to the contractor for brooklyn property"

## Supported Contact Roles

- `lawyer` / `attorney`
- `buyer`
- `seller`
- `contractor`
- `inspector`
- `appraiser`
- `lender` / `mortgage broker`
- `tenant`
- `landlord`
- `property manager`
- `handyman`
- `plumber`
- `electrician`

## Features

### Fuzzy Address Matching
- "141 throop" matches "141 Throop Avenue, Brooklyn, NY"
- "main street" matches "123 Main Street"
- "oak" matches "456 Oak Avenue"

### Auto-Create Contracts
By default, if the contract doesn't exist, it will be created automatically.

```json
{
  "create_if_missing": true  // Default
}
```

Set to `false` if you want an error when contract doesn't exist.

### Custom Message
Add a personalized message:

```json
{
  "address_query": "throop",
  "contract_name": "purchase agreement",
  "contact_role": "buyer",
  "message": "Please review and sign by Friday"
}
```

## Prerequisites

For this to work, you need:

1. ✅ **Property exists** - Property must be in database
2. ✅ **Contact exists** - Contact with specified role must exist for property
3. ✅ **Contact has email** - Contact record must have an email address
4. ✅ **Contract has template** - Contract must have `docuseal_template_id` set

## Response

```json
{
  "contract": {
    "id": 1,
    "property_id": 1,
    "contact_id": 3,
    "name": "Property Agreement",
    "status": "sent",
    "docuseal_submission_id": "12345",
    "docuseal_url": "https://docuseal.co/s/12345",
    "sent_at": "2026-02-04T14:30:00"
  },
  "voice_confirmation": "Done! I've sent the Property Agreement to John Lawyer (lawyer) at john@lawfirm.com for 123 Main Street."
}
```

## Error Messages (Voice-Friendly)

### Property Not Found
```
"No property found matching '141 throop'. Please add the property first."
```

### Contact Not Found
```
"No lawyer found for 123 Main Street. Please add a lawyer contact first."
```

### Contact Missing Email
```
"The lawyer contact (John Lawyer) doesn't have an email address. Please add one."
```

### Contract Missing Template
```
"Contract 'Property Agreement' doesn't have a DocuSeal template ID. Please set docuseal_template_id first."
```

## Example Workflow

### 1. Setup Data
```bash
# Add property
POST /properties/
{
  "title": "Brooklyn Apartment",
  "address": "141 Throop Avenue",
  "city": "Brooklyn",
  "state": "NY",
  "zip_code": "11206",
  "price": 500000,
  "agent_id": 1
}

# Add lawyer contact
POST /contacts/
{
  "property_id": 1,
  "name": "John Lawyer",
  "role": "lawyer",
  "email": "john@lawfirm.com",
  "phone": "555-1234"
}

# Create contract with template
POST /contracts/
{
  "property_id": 1,
  "name": "Property Agreement",
  "docuseal_template_id": "template_abc123"
}
```

### 2. Send with Voice Command
```bash
POST /contracts/voice/send
{
  "address_query": "141 throop",
  "contract_name": "property agreement",
  "contact_role": "lawyer"
}
```

### 3. Check Status
```bash
GET /contracts/1/status?refresh=true
```

## Integration with Voice AI

This endpoint is designed to work with voice AI assistants. The AI can:

1. Parse user speech: "send the property agreement to the lawyer for 141 throop"
2. Extract parameters:
   - `address_query`: "141 throop"
   - `contract_name`: "property agreement"
   - `contact_role`: "lawyer"
3. Call the API
4. Read the `voice_confirmation` back to the user

## Comparison: Traditional vs Voice

### Traditional Way (4 API calls)
```bash
# 1. Find property ID
GET /properties/?address=141%20throop

# 2. Find lawyer contact ID
GET /contacts/property/1?role=lawyer

# 3. Find contract ID
GET /contracts/property/1?name=property%20agreement

# 4. Send contract
POST /contracts/3/send-to-contact
{
  "contact_id": 5
}
```

### Voice Way (1 API call)
```bash
POST /contracts/voice/send
{
  "address_query": "141 throop",
  "contract_name": "property agreement",
  "contact_role": "lawyer"
}
```

## Tips

- **Be specific with property addresses** if you have multiple similar ones
- **Use common role names** - "lawyer" is easier than "attorney"
- **Contract names are fuzzy** - "property agreement" matches "Property Agreement Contract"
- **Set up templates first** - Make sure contracts have `docuseal_template_id` before sending

## Next Steps

See `DOCUSEAL_INTEGRATION.md` for full DocuSeal setup and configuration.
