# Property Management MCP Server

This MCP (Model Context Protocol) server exposes the AI Realtor property database as a set of tools that can be used by Claude and other AI assistants.

## Installation

1. The MCP server is already configured in Claude Desktop at:
   ```
   ~/.config/Application Support/Claude/claude_desktop_config.json
   ```

2. **Restart Claude Desktop** to load the new MCP server.

## Available Tools

### 1. `list_properties`
List all properties in the database.

**Parameters:**
- `limit` (optional): Maximum number of properties to return (default: 10)
- `status` (optional): Filter by status - "new_property", "enriched", "researched", "waiting_for_contracts", "complete"

**Example:**
```
List all available properties
```

### 2. `get_property`
Get detailed information for a specific property including enrichment data.

**Parameters:**
- `property_id` (required): The ID of the property

**Returns:** Complete property data including:
- Basic property info (address, price, beds, baths)
- Zillow enrichment (photos, Zestimate, schools, tax history)
- Skip trace data (owner info, contact details)
- Contacts and contracts

**Example:**
```
Get details for property ID 1
```

### 3. `create_property`
Create a new property in the database.

**Parameters:**
- `address` (required): Property address (will be autocompleted)
- `price` (required): Property price in dollars
- `bedrooms` (optional): Number of bedrooms
- `bathrooms` (optional): Number of bathrooms
- `agent_id` (optional): Agent ID (default: 1)

**Example:**
```
Create a property at 123 Main Street, New York, NY for $500,000 with 3 bedrooms and 2 bathrooms
```

### 4. `delete_property`
Delete a property and all its related data.

**Parameters:**
- `property_id` (required): The ID of the property to delete

**Warning:** This permanently deletes the property and all related data (enrichments, skip traces, contacts, contracts).

**Example:**
```
Delete property ID 5
```

### 5. `enrich_property`
Enrich a property with comprehensive Zillow data.

**Parameters:**
- `property_id` (required): The ID of the property to enrich

**Returns:** Zillow data including:
- Photos and virtual tours
- Zestimate and rent estimate
- Tax history (5 years)
- Price history
- Nearby schools with ratings
- Property details (sqft, lot size, year built)
- Market statistics

**Triggers:** Shows enrichment animation on TV display

**Example:**
```
Enrich property ID 1 with Zillow data
```

### 6. `skip_trace_property`
Skip trace a property to find owner contact information.

**Parameters:**
- `property_id` (required): The ID of the property to skip trace

**Returns:** Owner information including:
- Owner name
- Phone numbers (with type: mobile, landline)
- Email addresses
- Mailing address

**Example:**
```
Skip trace property ID 1 to find the owner
```

### 7. `add_contact`
Add a contact to a property.

**Parameters:**
- `property_id` (required): The property ID
- `name` (required): Contact's full name
- `email` (optional): Contact's email
- `phone` (optional): Contact's phone number
- `role` (optional): "buyer", "seller", "agent", "other" (default: "buyer")

**Example:**
```
Add contact John Doe with email john@example.com and phone 555-1234 to property ID 1 as a buyer
```

## Usage Examples

### Complete Property Workflow

```
# 1. Create a property
Create a property at 141 Throop Ave, New Brunswick, NJ for $350,000

# 2. Enrich with Zillow data
Enrich property ID 1 with Zillow data

# 3. Skip trace for owner info
Skip trace property ID 1

# 4. Add interested buyer
Add contact Sarah Smith with email sarah@email.com to property ID 1 as a buyer

# 5. View complete property details
Get details for property ID 1
```

## Requirements

- Backend API must be running at `http://localhost:8000`
- Virtual environment activated with MCP SDK installed
- Valid API keys in `.env` file:
  - `GOOGLE_PLACES_API_KEY` - For address autocomplete
  - `RAPIDAPI_KEY` - For Zillow and skip trace APIs
  - `ZILLOW_API_HOST` - Zillow API endpoint
  - `SKIP_TRACE_API_HOST` - Skip trace API endpoint

## Troubleshooting

### MCP Server Not Loading
1. Check Claude Desktop config at `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Verify the Python path: `/Users/edduran/Documents/GitHub/ai-realtor/venv/bin/python`
3. Ensure MCP SDK is installed: `pip list | grep mcp`
4. Restart Claude Desktop

### Backend API Not Responding
1. Start the backend: `python -m uvicorn app.main:app --reload --port 8000`
2. Check if running: `curl http://localhost:8000/docs`
3. View logs: `tail -f backend.log`

### Enrichment Fails
1. Verify API keys in `.env` file
2. Check ZILLOW_API_HOST is set to `private-zillow.p.rapidapi.com`
3. Ensure property has valid address

## TV Display Integration

When you use MCP tools, they integrate with the TV display:
- **Create Property**: Property appears in live feed
- **Enrich Property**: Shows animated enrichment overlay
- **Delete Property**: Property disappears from feed
- **All Changes**: Reflected in real-time via WebSocket

View TV display at: `http://localhost:3025` or `http://localhost:3000`

## Architecture

```
┌─────────────┐
│   Claude    │
│  Desktop    │
└──────┬──────┘
       │ MCP Protocol
       ↓
┌─────────────┐
│  Property   │
│ MCP Server  │
└──────┬──────┘
       │ HTTP/SQLAlchemy
       ↓
┌─────────────┐      ┌──────────────┐
│  FastAPI    │ ←──→ │  PostgreSQL  │
│  Backend    │      │   Database   │
└──────┬──────┘      └──────────────┘
       │ WebSocket
       ↓
┌─────────────┐
│ TV Display  │
│  Frontend   │
└─────────────┘
```

## Development

To modify the MCP server:

1. Edit `/Users/edduran/Documents/GitHub/ai-realtor/mcp_server/property_mcp.py`
2. Restart Claude Desktop to reload changes
3. Test with simple commands in Claude

## Support

For issues or questions:
- Check backend logs: `tail -f backend.log`
- View API docs: `http://localhost:8000/docs`
- Test tools directly via Claude Desktop
