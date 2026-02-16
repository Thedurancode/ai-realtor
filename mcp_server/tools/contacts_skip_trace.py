"""Contact and skip trace MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post, API_BASE_URL
from ..utils.property_resolver import resolve_property_id
import requests


# ── Helpers ──

async def skip_trace_property(property_id: int) -> dict:
    response = api_post("/context/skip-trace", json={"property_ref": str(property_id), "session_id": "mcp_session"})
    response.raise_for_status()
    return response.json()


async def add_contact_to_property(property_id, name, email=None, phone=None, role="buyer") -> dict:
    response = api_post("/contacts/", json={"name": name, "email": email, "phone": phone, "role": role, "property_id": property_id})
    response.raise_for_status()
    return response.json()


async def get_property(property_id: int) -> dict:
    response = api_get(f"/properties/{property_id}")
    response.raise_for_status()
    return response.json()


# ── Handlers ──

async def handle_skip_trace_property(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    result = await skip_trace_property(property_id)

    trace = result.get("data", result.get("skip_trace", result))
    address = trace.get("property_address", f"property {property_id}")

    # Try to get detailed info from property endpoint
    owner = trace.get('owner_name')
    phones = []
    emails = []
    mailing = None
    try:
        full = await get_property(property_id)
        skip_traces = full.get('skip_traces', [])
        if skip_traces:
            st = skip_traces[0]
            if st.get('owner_name') and st['owner_name'] != 'Unknown Owner':
                owner = st['owner_name']
            phones = st.get('phone_numbers', []) or []
            emails = st.get('emails', []) or []
            if st.get('mailing_address'):
                mailing = st['mailing_address']
                if st.get('mailing_city'):
                    mailing += f", {st['mailing_city']}"
                if st.get('mailing_state'):
                    mailing += f", {st['mailing_state']}"
    except Exception:
        pass

    text = f"Skip trace completed for {address}."
    if owner and owner != 'Unknown Owner':
        text += f" Owner: {owner}."
    else:
        text += " Owner information was not available."
    if phones:
        text += f" Phone: {', '.join(phones)}."
    if emails:
        text += f" Email: {', '.join(emails)}."
    if mailing:
        text += f" Mailing address: {mailing}."

    return [TextContent(type="text", text=text)]


async def handle_add_contact(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    result = await add_contact_to_property(
        property_id=property_id, name=arguments["name"],
        email=arguments.get("email"), phone=arguments.get("phone"),
        role=arguments.get("role", "buyer")
    )

    contact_name = result.get("name", arguments["name"])
    contact_role = result.get("role", arguments.get("role", "buyer")).replace("_", " ")
    output = f"Added {contact_name} as {contact_role} for property {property_id}.\n"

    if arguments.get("send_contracts"):
        contact_id = result.get("id")
        if contact_id:
            try:
                send_response = requests.post(f"{API_BASE_URL}/contacts/{contact_id}/send-pending-contracts")
                send_response.raise_for_status()
                send_result = send_response.json()

                matched = send_result.get("matched_contracts", [])
                if matched:
                    output += f"\nContract matching:\n"
                    for m in matched:
                        status = "Ready to send" if m["ready_to_send"] else f"Missing: {', '.join(m['missing_roles'])}"
                        signers = ", ".join(s["name"] for s in m["found_signers"])
                        output += f"  - {m['contract_name']}: {status}\n"
                        if m["found_signers"]:
                            output += f"    Signers: {signers}\n"
                else:
                    output += f"\nNo draft contracts need a {contact_role}'s signature on this property."

                output += f"\n{send_result.get('voice_summary', '')}"
            except Exception as e:
                output += f"\nCouldn't check contracts: {str(e)}"
        else:
            output += "\nCouldn't check contracts: contact ID not returned."

    return [TextContent(type="text", text=output)]


# ── Tool Registration ──

register_tool(
    Tool(name="skip_trace_property", description="Skip trace a property to find owner contact information including name, phone numbers, email addresses, and mailing address. Voice-friendly: say the address instead of the ID.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "The ID of the property to skip trace (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')"}}}),
    handle_skip_trace_property
)

register_tool(
    Tool(name="add_contact", description="Add a contact to a property. Set send_contracts=true to automatically find and send any draft contracts that need this contact's role signature. Voice-friendly: say the address instead of the ID. Example: 'Add Daffy Duck as the lawyer for 123 Main Street'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "The property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street')"}, "name": {"type": "string", "description": "Contact's full name"}, "email": {"type": "string", "description": "Contact's email address (required if send_contracts is true)"}, "phone": {"type": "string", "description": "Contact's phone number"}, "role": {"type": "string", "description": "Contact's role", "enum": ["buyer", "seller", "lawyer", "attorney", "contractor", "inspector", "appraiser", "lender", "mortgage_broker", "title_company", "tenant", "landlord", "property_manager", "handyman", "plumber", "electrician", "photographer", "stager", "other"], "default": "buyer"}, "send_contracts": {"type": "boolean", "description": "If true, automatically find draft contracts needing this role's signature and report which are ready to send", "default": False}}, "required": ["name"]}),
    handle_add_contact
)
