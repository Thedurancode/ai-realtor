"""Offer & negotiation MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post
from ..utils.property_resolver import find_property_by_address


# ── Handlers ──

async def handle_create_offer(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id or address.")]

    payload = {"property_id": property_id, "offer_price": arguments["offer_price"]}
    for key in ["earnest_money", "financing_type", "closing_days", "contingencies", "notes", "is_our_offer"]:
        if arguments.get(key) is not None:
            payload[key] = arguments[key]

    response = api_post("/offers/", json=payload)
    response.raise_for_status()
    offer = response.json()

    terms = [f"${offer['offer_price']:,.0f}", offer.get('financing_type', 'cash')]
    if offer.get("closing_days"):
        terms.append(f"{offer['closing_days']}-day close")
    if offer.get("earnest_money"):
        terms.append(f"${offer['earnest_money']:,.0f} earnest")
    if offer.get("contingencies"):
        terms.append(f"{len(offer['contingencies'])} contingencies")

    text = f"Offer #{offer['id']} created on property #{offer['property_id']}: {', '.join(terms)}."
    if offer.get("mao_base"):
        text += f" MAO range: ${offer.get('mao_low', 0):,.0f}-${offer.get('mao_high', 0):,.0f}."
    if offer.get("expires_at_formatted"):
        text += f" Expires {offer['expires_at_formatted']}."
    return [TextContent(type="text", text=text)]


async def handle_counter_offer(arguments: dict) -> list[TextContent]:
    offer_id = arguments.get("offer_id")
    if not offer_id:
        property_id = arguments.get("property_id")
        address = arguments.get("address")
        if not property_id and address:
            property_id = find_property_by_address(address)
        if property_id:
            resp = api_get("/offers/", params={"property_id": property_id, "status": "submitted"})
            if resp.ok:
                offers = resp.json()
                if not offers:
                    resp2 = api_get("/offers/", params={"property_id": property_id, "status": "countered"})
                    if resp2.ok:
                        offers = resp2.json()
                if offers:
                    offer_id = offers[0]["id"]
        if not offer_id:
            return [TextContent(type="text", text="No active offer found to counter. Provide an offer_id or property address.")]

    payload = {"offer_price": arguments["offer_price"]}
    for key in ["earnest_money", "closing_days", "contingencies", "notes"]:
        if arguments.get(key) is not None:
            payload[key] = arguments[key]

    response = api_post(f"/offers/{offer_id}/counter", json=payload)
    response.raise_for_status()
    offer = response.json()

    text = f"Counter-offer #{offer['id']} sent at ${offer['offer_price']:,.0f} (countering offer #{offer.get('parent_offer_id')})."
    if offer.get("closing_days"):
        text += f" {offer['closing_days']}-day close."
    if offer.get("expires_at_formatted"):
        text += f" Expires {offer['expires_at_formatted']}."
    return [TextContent(type="text", text=text)]


async def handle_accept_offer(arguments: dict) -> list[TextContent]:
    offer_id = arguments.get("offer_id")
    if not offer_id:
        property_id = arguments.get("property_id")
        address = arguments.get("address")
        if not property_id and address:
            property_id = find_property_by_address(address)
        if property_id:
            resp = api_get("/offers/", params={"property_id": property_id})
            if resp.ok:
                offers = [o for o in resp.json() if o["status"] in ("submitted", "countered")]
                if offers:
                    offers.sort(key=lambda o: o["offer_price"], reverse=True)
                    offer_id = offers[0]["id"]
        if not offer_id:
            return [TextContent(type="text", text="No active offer found to accept.")]

    response = api_post(f"/offers/{offer_id}/accept")
    response.raise_for_status()
    offer = response.json()

    text = f"Offer #{offer['id']} accepted at ${offer['offer_price']:,.0f}. Property is now pending, competing offers auto-rejected, and purchase agreement contracts are queued."
    return [TextContent(type="text", text=text)]


async def handle_reject_offer(arguments: dict) -> list[TextContent]:
    offer_id = arguments.get("offer_id")
    if not offer_id:
        property_id = arguments.get("property_id")
        address = arguments.get("address")
        if not property_id and address:
            property_id = find_property_by_address(address)
        if property_id:
            resp = api_get("/offers/", params={"property_id": property_id})
            if resp.ok:
                offers = [o for o in resp.json() if o["status"] in ("submitted", "countered")]
                if offers:
                    offer_id = offers[0]["id"]
        if not offer_id:
            return [TextContent(type="text", text="No active offer found to reject.")]

    response = api_post(f"/offers/{offer_id}/reject")
    response.raise_for_status()
    offer = response.json()

    text = f"Offer #{offer['id']} rejected (was ${offer['offer_price']:,.0f})."
    return [TextContent(type="text", text=text)]


async def handle_withdraw_offer(arguments: dict) -> list[TextContent]:
    offer_id = arguments.get("offer_id")
    if not offer_id:
        property_id = arguments.get("property_id")
        address = arguments.get("address")
        if not property_id and address:
            property_id = find_property_by_address(address)
        if property_id:
            resp = api_get("/offers/", params={"property_id": property_id})
            if resp.ok:
                offers = [o for o in resp.json() if o["status"] in ("submitted", "countered", "draft") and o.get("is_our_offer")]
                if offers:
                    offer_id = offers[0]["id"]
        if not offer_id:
            return [TextContent(type="text", text="No active offer found to withdraw.")]

    response = api_post(f"/offers/{offer_id}/withdraw")
    response.raise_for_status()
    offer = response.json()

    text = f"Offer #{offer['id']} withdrawn (was ${offer['offer_price']:,.0f})."
    return [TextContent(type="text", text=text)]


async def handle_list_offers(arguments: dict) -> list[TextContent]:
    params = {}
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if property_id:
        params["property_id"] = property_id
    if arguments.get("status"):
        params["status"] = arguments["status"]

    response = api_get("/offers/", params=params)
    response.raise_for_status()
    offers = response.json()

    if not offers:
        return [TextContent(type="text", text="No offers found.")]

    text = f"You have {len(offers)} offer{'s' if len(offers) != 1 else ''}.\n\n"
    for o in offers[:15]:
        direction = "ours" if o.get("is_our_offer") else "received"
        text += f"#{o['id']} ${o['offer_price']:,.0f} ({o['status']}, {o.get('financing_type', 'cash')}, {direction})\n"
    return [TextContent(type="text", text=text.strip())]


async def handle_get_offer_details(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id or address.")]

    response = api_get(f"/offers/property/{property_id}/summary")
    response.raise_for_status()
    summary = response.json()

    text = summary.get("voice_summary", "No offer data available.")
    offers_list = summary.get("offers", [])
    if offers_list:
        text += "\n\n"
        for o in offers_list[:10]:
            direction = "ours" if o.get("is_our_offer") else "received"
            counter = f" (counter to #{o['parent_offer_id']})" if o.get("parent_offer_id") else ""
            text += f"#{o['id']} ${o['offer_price']:,.0f} — {o['status']}, {direction}{counter}\n"
    return [TextContent(type="text", text=text.strip())]


async def handle_calculate_mao(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id or address.")]

    response = api_post(f"/offers/property/{property_id}/mao")
    response.raise_for_status()
    mao = response.json()

    text = mao.get("voice_summary", "")
    details = []
    if mao.get("list_price"):
        details.append(f"list ${mao['list_price']:,.0f}")
    if mao.get("zestimate"):
        details.append(f"Zestimate ${mao['zestimate']:,.0f}")
    arv = mao.get("arv")
    if arv and arv.get("base"):
        details.append(f"ARV ${arv['base']:,.0f}")
    offer_rec = mao.get("offer_recommendation")
    if offer_rec and offer_rec.get("base"):
        details.append(f"max offer ${offer_rec['base']:,.0f} (range ${offer_rec.get('low', 0):,.0f}-${offer_rec.get('high', 0):,.0f})")
    if details:
        text += f"\n\n{mao.get('strategy', 'wholesale').title()} strategy: {', '.join(details)}."
    if mao.get('explanation'):
        text += f"\n{mao['explanation']}"
    return [TextContent(type="text", text=text.strip())]


# ── Tool Registration ──

register_tool(Tool(name="create_offer", description="Make an offer on a property. Supports property ID or address. Voice: 'Make an offer of $400K on 123 Main St with 30-day close'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID"}, "address": {"type": "string", "description": "Property address (alternative to property_id)"}, "offer_price": {"type": "number", "description": "Offer price in dollars (e.g., 400000)"}, "earnest_money": {"type": "number", "description": "Earnest money deposit in dollars"}, "financing_type": {"type": "string", "description": "Financing type: cash, conventional, fha, va, hard_money, seller_financing", "default": "cash"}, "closing_days": {"type": "number", "description": "Days to close from acceptance (default: 30)", "default": 30}, "contingencies": {"type": "array", "items": {"type": "string"}, "description": "List of contingencies: inspection, financing, appraisal, etc."}, "notes": {"type": "string", "description": "Additional terms or notes"}, "is_our_offer": {"type": "boolean", "description": "True if we're making the offer, false if we received it", "default": True}}, "required": ["offer_price"]}), handle_create_offer)

register_tool(Tool(name="counter_offer", description="Counter an existing offer with new terms. Voice: 'Counter at $380K with 45-day close'.", inputSchema={"type": "object", "properties": {"offer_id": {"type": "number", "description": "The offer ID to counter"}, "property_id": {"type": "number", "description": "Property ID (finds latest active offer)"}, "address": {"type": "string", "description": "Property address (finds latest active offer)"}, "offer_price": {"type": "number", "description": "Counter-offer price"}, "earnest_money": {"type": "number", "description": "Updated earnest money"}, "closing_days": {"type": "number", "description": "Updated days to close"}, "contingencies": {"type": "array", "items": {"type": "string"}, "description": "Updated contingencies"}, "notes": {"type": "string", "description": "Counter-offer notes"}}, "required": ["offer_price"]}), handle_counter_offer)

register_tool(Tool(name="accept_offer", description="Accept an offer on a property. Auto-sets property to pending, rejects competing offers, and attaches purchase agreement. Voice: 'Accept the offer on property 5'.", inputSchema={"type": "object", "properties": {"offer_id": {"type": "number", "description": "Offer ID to accept"}, "property_id": {"type": "number", "description": "Property ID (accepts highest active offer)"}, "address": {"type": "string", "description": "Property address (accepts highest active offer)"}}}), handle_accept_offer)

register_tool(Tool(name="reject_offer", description="Reject an offer on a property. Voice: 'Reject the offer on Ocean Drive'.", inputSchema={"type": "object", "properties": {"offer_id": {"type": "number", "description": "Offer ID to reject"}, "property_id": {"type": "number", "description": "Property ID (rejects latest active offer)"}, "address": {"type": "string", "description": "Property address (rejects latest active offer)"}}}), handle_reject_offer)

register_tool(Tool(name="withdraw_offer", description="Withdraw our offer on a property. Voice: 'Withdraw my offer on 123 Main'.", inputSchema={"type": "object", "properties": {"offer_id": {"type": "number", "description": "Offer ID to withdraw"}, "property_id": {"type": "number", "description": "Property ID (withdraws our latest active offer)"}, "address": {"type": "string", "description": "Property address"}}}), handle_withdraw_offer)

register_tool(Tool(name="list_offers", description="List all offers, optionally filtered by property or status. Voice: 'What offers do we have?' or 'Show offers on property 5'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Filter by property ID"}, "address": {"type": "string", "description": "Filter by property address"}, "status": {"type": "string", "description": "Filter by status: submitted, countered, accepted, rejected, withdrawn, expired"}}}), handle_list_offers)

register_tool(Tool(name="get_offer_details", description="Get detailed offer summary for a property including voice-friendly response. Voice: 'What's the offer status on 123 Main?'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID"}, "address": {"type": "string", "description": "Property address"}}}), handle_get_offer_details)

register_tool(Tool(name="calculate_mao", description="Calculate Maximum Allowable Offer based on underwriting data or Zestimate. Voice: 'What's the max I should offer on property 5?'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID"}, "address": {"type": "string", "description": "Property address"}}}), handle_calculate_mao)


async def handle_draft_offer_letter(arguments: dict) -> list[TextContent]:
    offer_id = arguments.get("offer_id")

    # If we have an offer_id, draft from the existing offer
    if offer_id:
        response = api_post(f"/offers/{int(offer_id)}/draft-letter")
        response.raise_for_status()
        data = response.json()
    else:
        # Standalone: resolve property
        property_id = arguments.get("property_id")
        address = arguments.get("address")
        if not property_id and address:
            property_id = find_property_by_address(address)
        if not property_id:
            return [TextContent(type="text", text="Please provide an offer_id, property_id, or address.")]

        offer_price = arguments.get("offer_price")
        if not offer_price:
            return [TextContent(type="text", text="Please provide an offer_price.")]

        payload = {"offer_price": offer_price}
        for key in ["financing_type", "closing_days", "contingencies", "earnest_money", "buyer_name", "buyer_email"]:
            if arguments.get(key) is not None:
                payload[key] = arguments[key]

        response = api_post(f"/offers/property/{int(property_id)}/draft-letter", json=payload)
        response.raise_for_status()
        data = response.json()

    text = data.get('voice_summary', f"Offer letter drafted (contract #{data['contract_id']}, ready for DocuSeal).")

    if data.get('negotiation_strategy'):
        text += f"\n\nNegotiation strategy: {data['negotiation_strategy']}"

    points = data.get("talking_points", [])
    if points:
        text += "\n\nTalking points: " + "; ".join(points[:5]) + "."

    if data.get("letter_text"):
        text += f"\n\nFull letter:\n{data['letter_text']}"

    return [TextContent(type="text", text=text.strip())]


register_tool(Tool(
    name="draft_offer_letter",
    description="Draft an AI-generated offer letter for a property. Creates a DRAFT contract ready for DocuSeal signing. Voice: 'Draft an offer letter for property 5 at $750,000'.",
    inputSchema={
        "type": "object",
        "properties": {
            "offer_id": {"type": "number", "description": "Existing offer ID to draft from"},
            "property_id": {"type": "number", "description": "Property ID (for standalone draft)"},
            "address": {"type": "string", "description": "Property address (alternative to property_id)"},
            "offer_price": {"type": "number", "description": "Offer price in dollars (required for standalone draft)"},
            "financing_type": {"type": "string", "description": "Financing: cash, conventional, fha, va, hard_money, seller_financing", "default": "cash"},
            "closing_days": {"type": "number", "description": "Days to close (default: 30)", "default": 30},
            "contingencies": {"type": "array", "items": {"type": "string"}, "description": "List of contingencies"},
            "earnest_money": {"type": "number", "description": "Earnest money deposit in dollars"},
            "buyer_name": {"type": "string", "description": "Buyer's full name"},
            "buyer_email": {"type": "string", "description": "Buyer's email address"},
        },
    },
), handle_draft_offer_letter)
