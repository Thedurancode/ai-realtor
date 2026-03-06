"""
ClaudeBot tools — thin wrapper over the AI Realtor REST API.
Claude calls these tools, we forward to the API and return results.
"""

import json
import httpx
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")
TIMEOUT = 30.0

# --- Tool definitions sent to Claude ---

TOOLS = [
    {
        "name": "list_properties",
        "description": "List all properties with optional filters (status, city, state, min/max price). Returns summary of each property.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status (available, under_contract, sold)"},
                "city": {"type": "string"},
                "state": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "get_property",
        "description": "Get detailed info about a specific property by ID.",
        "input_schema": {
            "type": "object",
            "properties": {"property_id": {"type": "integer"}},
            "required": ["property_id"],
        },
    },
    {
        "name": "create_property",
        "description": "Create a new property. Provide address, price, bedrooms, bathrooms, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {"type": "string"},
                "price": {"type": "number"},
                "bedrooms": {"type": "integer"},
                "bathrooms": {"type": "number"},
                "sqft": {"type": "integer"},
                "property_type": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["address"],
        },
    },
    {
        "name": "calculate_deal",
        "description": "Run deal analysis on a property. Returns wholesale, flip, rental, BRRRR scores and numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Property address"},
                "strategies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Strategies to analyze: wholesale, flip, rental, brrrr",
                },
            },
            "required": ["address"],
        },
    },
    {
        "name": "research_property",
        "description": "Run full AI research on a property — comps, neighborhood, environment, underwriting.",
        "input_schema": {
            "type": "object",
            "properties": {"property_id": {"type": "integer"}},
            "required": ["property_id"],
        },
    },
    {
        "name": "search_properties",
        "description": "Natural language search across properties. E.g. 'condos under 700k in Brooklyn'.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "create_offer",
        "description": "Submit an offer on a property.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "amount": {"type": "number"},
                "contingencies": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string"},
            },
            "required": ["property_id", "amount"],
        },
    },
    {
        "name": "list_offers",
        "description": "List all offers, optionally filtered by property.",
        "input_schema": {
            "type": "object",
            "properties": {"property_id": {"type": "integer"}},
        },
    },
    {
        "name": "list_contracts",
        "description": "List contracts, optionally filtered by property.",
        "input_schema": {
            "type": "object",
            "properties": {"property_id": {"type": "integer"}},
        },
    },
    {
        "name": "send_contract",
        "description": "Send a contract for e-signature via DocuSeal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "integer"},
                "signer_name": {"type": "string"},
                "signer_email": {"type": "string"},
            },
            "required": ["contract_id", "signer_email"],
        },
    },
    {
        "name": "get_daily_digest",
        "description": "Get today's digest — property updates, pending tasks, market alerts.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_pipeline_summary",
        "description": "Get pipeline overview — properties by stage, deals in progress, revenue projections.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "make_phone_call",
        "description": "Make an AI phone call to a contact about a property.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "phone_number": {"type": "string"},
                "purpose": {"type": "string", "description": "Why are we calling? E.g. 'ask if interested in selling'"},
            },
            "required": ["property_id", "phone_number"],
        },
    },
    {
        "name": "send_direct_mail",
        "description": "Send a postcard or letter to a property owner via Lob.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["postcard", "letter"]},
                "to_address": {"type": "string"},
                "message": {"type": "string"},
                "property_id": {"type": "integer"},
            },
            "required": ["type", "to_address", "message"],
        },
    },
    {
        "name": "api_request",
        "description": "Make any request to the AI Realtor API. Use for endpoints not covered by other tools. Specify method, path, and optional body.",
        "input_schema": {
            "type": "object",
            "properties": {
                "method": {"type": "string", "enum": ["GET", "POST", "PATCH", "DELETE"]},
                "path": {"type": "string", "description": "API path, e.g. /properties/5/enrich"},
                "body": {"type": "object", "description": "Request body for POST/PATCH"},
            },
            "required": ["method", "path"],
        },
    },
]

# --- Tool execution ---

ROUTE_MAP = {
    "list_properties": ("GET", "/properties/"),
    "get_property": ("GET", "/properties/{property_id}"),
    "create_property": ("POST", "/properties/voice"),
    "calculate_deal": ("POST", "/deal-calculator/voice"),
    "research_property": ("POST", "/agentic-research/property/{property_id}/run"),
    "search_properties": ("POST", "/search/properties"),
    "create_offer": ("POST", "/offers/"),
    "list_offers": ("GET", "/offers/"),
    "list_contracts": ("GET", "/contracts/"),
    "send_contract": ("POST", "/contracts/{contract_id}/send"),
    "get_daily_digest": ("GET", "/daily-digest/"),
    "get_pipeline_summary": ("GET", "/pipeline/summary"),
    "make_phone_call": ("POST", "/property-recap/property/{property_id}/call"),
    "send_direct_mail": ("POST", "/direct-mail/send"),
}


async def execute_tool(name: str, args: dict) -> str:
    """Execute a tool call and return the result as a string."""
    try:
        if name == "api_request":
            return await _raw_api_request(args["method"], args["path"], args.get("body"))

        if name not in ROUTE_MAP:
            return json.dumps({"error": f"Unknown tool: {name}"})

        method, path_template = ROUTE_MAP[name]

        # Substitute path params
        path = path_template
        query_params = {}
        body = {}
        for key, val in args.items():
            placeholder = "{" + key + "}"
            if placeholder in path:
                path = path.replace(placeholder, str(val))
            elif method == "GET":
                if val is not None:
                    query_params[key] = val
            else:
                body[key] = val

        return await _raw_api_request(method, path, body if method != "GET" else None, query_params)

    except Exception as e:
        return json.dumps({"error": str(e)})


async def _raw_api_request(
    method: str, path: str, body: dict | None = None, params: dict | None = None
) -> str:
    """Make an HTTP request to the AI Realtor API."""
    url = f"{API_BASE}{path}"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.request(method, url, headers=headers, json=body, params=params)

    try:
        data = resp.json()
    except Exception:
        data = {"status_code": resp.status_code, "text": resp.text[:1000]}

    # Truncate large responses for Claude's context
    result = json.dumps(data, default=str)
    if len(result) > 8000:
        result = result[:8000] + "\n... (truncated)"
    return result
