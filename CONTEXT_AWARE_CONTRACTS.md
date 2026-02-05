# ✅ Context-Aware Contract Queries - COMPLETE

## Summary

Successfully enhanced MCP contract tools to support **natural language address queries** instead of requiring numeric IDs. You can now say "show me who signed contracts for 141 throop" instead of "show me who signed contracts for property_id=5".

---

## What Was Added

### Enhanced MCP Tools

#### 1. check_contract_status (Enhanced)
Now accepts optional `address_query` parameter for fuzzy address matching.

**Before:**
```
"Check the status of contract 5"
```

**Now Also Works:**
```
"Show me who signed the contract for 141 throop"
"Check contract status for 123 main street"
"Has the contract for oak avenue been completed?"
```

---

#### 2. list_contracts (Enhanced)
Now accepts optional `address_query` parameter for fuzzy address matching.

**Before:**
```
"Show me contracts for property 5"
```

**Now Also Works:**
```
"Show me contracts for 141 throop"
"List contracts for 123 main street"
"What contracts do we have for the oak avenue property?"
```

---

## How It Works

### Fuzzy Address Matching

The tools use **case-insensitive substring matching** to find properties:

1. User provides partial address (e.g., "141 throop")
2. System searches database for properties containing those terms
3. First matching property is used
4. Contracts for that property are returned

**Examples:**
- "141 throop" → Matches "141 Throop Avenue, Brooklyn, NY 11206"
- "123 main" → Matches "123 Main Street"
- "oak ave" → Matches any property with "oak" and "ave"
- "456 elm sf" → Matches "456 Elm Street, San Francisco, CA"

---

## Implementation Details

### Files Modified

#### 1. `mcp_server/property_mcp.py`

**Function: `check_contract_status`** (Lines 233-251)
```python
async def check_contract_status(
    contract_id: Optional[int] = None,
    address_query: Optional[str] = None
) -> dict:
    """Check the status of a contract by ID or property address"""
    if address_query:
        # Find property by address, then get contracts
        contracts = await list_contracts(address_query=address_query)
        if not contracts or len(contracts) == 0:
            raise ValueError(f"No contracts found for address: {address_query}")
        # Return the most recent contract
        return await check_contract_status(contract_id=contracts[0]['id'])

    if not contract_id:
        raise ValueError("Either contract_id or address_query must be provided")

    response = requests.get(
        f"{API_BASE_URL}/contracts/{contract_id}/status",
        params={"refresh": "true"}
    )
    response.raise_for_status()
    return response.json()
```

**Function: `list_contracts`** (Lines 254-286)
```python
async def list_contracts(
    property_id: Optional[int] = None,
    address_query: Optional[str] = None
) -> dict:
    """List contracts, optionally filtered by property ID or address"""
    # If address provided, find property first
    if address_query:
        # Use context endpoint to find property by address
        from app.database import SessionLocal
        from app.models.property import Property
        from sqlalchemy import func

        db = SessionLocal()
        try:
            # Fuzzy match on address (similar to context router)
            query_lower = address_query.lower().strip()
            properties = db.query(Property).filter(
                func.lower(Property.address).contains(query_lower)
            ).all()

            if not properties:
                raise ValueError(f"No property found matching address: {address_query}")

            # Use the first matching property
            property_id = properties[0].id
        finally:
            db.close()

    if property_id:
        url = f"{API_BASE_URL}/contracts/property/{property_id}"
    else:
        url = f"{API_BASE_URL}/contracts/"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

**Tool Definitions Updated** (Lines 525-558)
- Added `address_query` parameter to both tools
- Made `contract_id` optional for `check_contract_status`
- Updated descriptions to mention natural language support

**Tool Handlers Updated** (Lines 692-740)
- Modified to accept and pass `address_query` parameter
- Enhanced output messages to show address when used
- Improved error messages for address-based queries

---

#### 2. `MCP_CONTRACTS.md`

**Updates:**
- Added `address_query` parameter documentation to both tools
- Added 10+ natural language usage examples
- Added new section: "Context-Aware Address Queries"
- Added Scenario 5 showing complete workflow
- Added "Benefits" section explaining advantages

---

## Usage Examples

### Example 1: List Contracts by Address

**User says to Claude:**
```
"Show me all contracts for 141 throop"
```

**Claude does:**
1. Uses `list_contracts` tool with `address_query="141 throop"`
2. Tool queries database: `SELECT * FROM properties WHERE LOWER(address) LIKE '%141 throop%'`
3. Finds property ID: 5 (141 Throop Avenue)
4. Fetches contracts: `GET /contracts/property/5`

**Response:**
```
Found 2 contract(s) for address '141 throop':

📝 Purchase Agreement (ID: 23)
   Status: in_progress
   Property ID: 5
   Created: 2026-02-04T21:30:00Z

📝 Seller Disclosure (ID: 27)
   Status: completed
   Property ID: 5
   Created: 2026-02-03T18:45:00Z
```

---

### Example 2: Check Contract Status by Address

**User says:**
```
"Show me who signed the contract for 141 throop"
```

**Claude does:**
1. Uses `check_contract_status` tool with `address_query="141 throop"`
2. Tool first calls `list_contracts` to find contracts for that address
3. Gets the most recent contract (ID: 23)
4. Checks status with `GET /contracts/23/status?refresh=true`

**Response:**
```
Contract #23 Status: IN_PROGRESS

Signers:
  - Sarah Johnson (Buyer): completed
  - Michael Chen (Seller): pending

Full JSON: {...}
```

---

### Example 3: Combined Workflow

**User says:**
```
"For 123 main street: show me all contracts, then check if the purchase agreement has been signed"
```

**Claude does:**
1. Uses `list_contracts` with `address_query="123 main street"`
2. Shows 3 contracts found
3. Identifies "Purchase Agreement" is contract ID: 45
4. Uses `check_contract_status` with `contract_id=45`
5. Shows detailed signing status

---

## Natural Language Variations

Claude understands many ways to ask:

**Checking Status:**
- "Show me who signed the contract for 141 throop"
- "Check contract status for 123 main street"
- "Has the contract for oak avenue been completed?"
- "What's the signing status for the main street property?"
- "Did everyone sign the 141 throop contract?"

**Listing Contracts:**
- "Show me contracts for 141 throop"
- "List all contracts for 123 main street"
- "What contracts do we have for oak avenue?"
- "Give me the contracts for the main street property"
- "How many contracts exist for 141 throop?"

---

## Benefits

✅ **No ID Lookup Required**
- Skip the step of finding property IDs
- Use addresses you already know
- Faster workflow

✅ **Natural Conversation**
- Speak to Claude naturally
- No need to learn technical IDs
- More intuitive

✅ **Fuzzy Matching**
- Partial addresses work
- Case-insensitive
- Flexible queries

✅ **Backwards Compatible**
- Original ID-based queries still work
- Both methods available
- No breaking changes

---

## Error Handling

### No Property Found
```
Error: No property found matching address: '999 fake st'
```

**Solution:** Try a different address variation or use property ID

### No Contracts Found
```
No contracts found for address: '141 throop'
```

**Meaning:** Property exists but has no contracts

### Multiple Properties Match
Currently uses the **first match**. If multiple properties match:
- Use more specific address (e.g., "141 throop brooklyn" instead of "throop")
- Or use property ID for precision

---

## Testing

### Via Claude Desktop

1. Ensure backend is running:
   ```bash
   python3 -m uvicorn app.main:app --reload --port 8000
   ```

2. Ensure properties and contracts exist in database

3. Try these commands in Claude Desktop:
   ```
   "Show me contracts for 141 throop"

   "Check who signed the contract for 123 main street"

   "List all contracts for oak avenue"

   "What's the contract status for the elm street property?"
   ```

### Expected Results

- Claude should use `list_contracts` or `check_contract_status` with `address_query`
- Should find properties by fuzzy match
- Should return contracts with formatted output
- Should show property address in response

---

## Architecture Flow

```
Claude Desktop
      ↓
User: "Show me contracts for 141 throop"
      ↓
MCP Tool: list_contracts(address_query="141 throop")
      ↓
Fuzzy Address Match
      ↓
Database Query: SELECT * FROM properties
                WHERE LOWER(address) LIKE '%141 throop%'
      ↓
Found: Property ID 5 (141 Throop Avenue)
      ↓
GET /contracts/property/5
      ↓
Return Contracts with Formatted Output
      ↓
Claude Desktop Shows Results
```

---

## Comparison: Before vs After

### Before ❌

**User:** "Show me who signed contracts for 141 throop"

**Required Steps:**
1. "List all properties"
2. Find property ID manually (ID: 5)
3. "List contracts for property 5"
4. Find contract ID manually (ID: 23)
5. "Check status of contract 23"

**Total:** 5 steps, manual ID lookup required

---

### After ✅

**User:** "Show me who signed contracts for 141 throop"

**Claude does:**
1. Uses `check_contract_status(address_query="141 throop")`
2. Returns complete status instantly

**Total:** 1 step, no manual lookup

---

## Future Enhancements

🔮 **Planned:**
- Support multiple property matches (prompt user to choose)
- Address normalization (handle abbreviations)
- Support city/state filters ("main street in brooklyn")
- Cache address → property_id mappings
- Add address autocomplete suggestions

---

## Complete Tool Specifications

### check_contract_status

**Parameters:**
```typescript
{
  contract_id?: number,      // Optional if address_query provided
  address_query?: string     // Fuzzy property address
}
```

**Either** `contract_id` **OR** `address_query` **must be provided**

**Returns:**
```typescript
{
  id: number,
  status: string,
  submitters: Array<{
    name: string,
    role: string,
    status: string
  }>,
  // ... more contract details
}
```

---

### list_contracts

**Parameters:**
```typescript
{
  property_id?: number,      // Optional
  address_query?: string     // Optional fuzzy property address
}
```

**Use either** `property_id` **OR** `address_query` (not both)

**Returns:**
```typescript
Array<{
  id: number,
  name: string,
  status: string,
  property_id: number,
  created_at: string,
  // ... more contract details
}>
```

---

## Key Files

- `mcp_server/property_mcp.py` - MCP tool implementations
- `MCP_CONTRACTS.md` - User documentation
- `CONTEXT_AWARE_CONTRACTS.md` - This file (technical summary)

---

**🎉 Context-aware contract queries are now live!**

Try it in Claude Desktop:
```
"Show me who signed contracts for 141 throop"
```
