"""Property Photo Ordering MCP tools.

Voice-controlled interface for ordering professional property photography
through ProxyPics, BoxBrownie, and other providers.
"""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post
from ..utils.property_resolver import find_property_by_address


# ── Handlers ──

async def handle_order_photos(arguments: dict) -> list[TextContent]:
    """Order professional photography for a property."""
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id or address.")]

    # Build services list
    services = arguments.get("services", [])
    if not services and arguments.get("package"):
        # Pre-defined packages
        package = arguments["package"].lower()
        if package == "basic":
            services = [
                {"service_type": "hdr_interior", "quantity": 10, "service_name": "HDR Interior Photos"},
                {"service_type": "exterior_day", "quantity": 3, "service_name": "Exterior Day Photos"}
            ]
        elif package == "premium":
            services = [
                {"service_type": "hdr_interior", "quantity": 20, "service_name": "HDR Interior Photos"},
                {"service_type": "exterior_day", "quantity": 5, "service_name": "Exterior Day Photos"},
                {"service_type": "aerial_drone", "quantity": 5, "service_name": "Aerial Drone Photos"},
                {"service_type": "virtual_staging", "quantity": 3, "service_name": "Virtual Staging"}
            ]
        elif package == "full_marketing":
            services = [
                {"service_type": "hdr_interior", "quantity": 25, "service_name": "HDR Interior Photos"},
                {"service_type": "exterior_day", "quantity": 5, "service_name": "Exterior Day Photos"},
                {"service_type": "exterior_twilight", "quantity": 3, "service_name": "Twilight Exterior"},
                {"service_type": "aerial_drone", "quantity": 10, "service_name": "Aerial Drone Photos"},
                {"service_type": "walkthrough_video", "quantity": 1, "service_name": "Video Walkthrough"},
                {"service_type": "virtual_tour_3d", "quantity": 1, "service_name": "3D Virtual Tour"},
                {"service_type": "floor_plan", "quantity": 1, "service_name": "Floor Plan"}
            ]

    if not services:
        return [TextContent(type="text", text="Please specify services or a package (basic, premium, full_marketing).")]

    payload = {
        "property_id": property_id,
        "provider": arguments.get("provider", "proxypics"),
        "services": services,
        "special_instructions": arguments.get("instructions")
    }

    # Optional scheduling
    if arguments.get("requested_date"):
        payload["requested_date"] = arguments["requested_date"]
    if arguments.get("time_slot"):
        payload["time_slot_preference"] = arguments["time_slot"]

    # Contact info
    if arguments.get("contact_name"):
        payload["contact_name"] = arguments["contact_name"]
    if arguments.get("contact_phone"):
        payload["contact_phone"] = arguments["contact_phone"]

    response = api_post("/photo-orders/", json=payload)
    response.raise_for_status()
    order = response.json()

    # Build voice-friendly response
    service_count = len(services)
    estimated = order.get("estimated_cost_formatted", "N/A")

    text = f"Photo order #{order['id']} created for property #{order['property_id']} with {service_count} services. Estimated cost: {estimated}."

    if order.get("requested_at_formatted"):
        text += f" Requested for {order['requested_at_formatted']}."

    text += " Use 'submit_photo_order' to send to the provider."
    return [TextContent(type="text", text=text)]


async def handle_submit_photo_order(arguments: dict) -> list[TextContent]:
    """Submit a draft photo order to the provider."""
    order_id = arguments.get("order_id")
    if not order_id:
        property_id = arguments.get("property_id")
        address = arguments.get("address")
        if not property_id and address:
            property_id = find_property_by_address(address)
        if property_id:
            # Find draft order for this property
            resp = api_get("/photo-orders/", params={"property_id": property_id, "status": "draft", "limit": 1})
            if resp.ok:
                orders = resp.json()
                if orders:
                    order_id = orders[0]["id"]

        if not order_id:
            return [TextContent(type="text", text="No draft order found. Create an order first with 'order_photos'.")]

    response = api_post(f"/photo-orders/{order_id}/submit", json={"confirm_submit": True})
    response.raise_for_status()
    order = response.json()

    status = order.get("order_status", "pending")
    text = f"Photo order #{order['id']} submitted to {order.get('provider', 'provider')}. Status: {status}."

    if order.get("provider_order_id"):
        text += f" Provider order ID: {order['provider_order_id']}."

    if order.get("estimated_completion_formatted"):
        text += f" Expected completion: {order['estimated_completion_formatted']}."

    return [TextContent(type="text", text=text)]


async def handle_get_photo_order_status(arguments: dict) -> list[TextContent]:
    """Get status of a photo order with voice-friendly summary."""
    order_id = arguments.get("order_id")
    property_id = arguments.get("property_id")
    address = arguments.get("address")

    if not order_id and (property_id or address):
        if not property_id and address:
            property_id = find_property_by_address(address)
        if property_id:
            # Get most recent order for property
            resp = api_get("/photo-orders/", params={"property_id": property_id, "limit": 1})
            if resp.ok:
                orders = resp.json()
                if orders:
                    order_id = orders[0]["id"]

    if not order_id:
        return [TextContent(type="text", text="Please provide an order_id or property address.")]

    response = api_get(f"/photo-orders/{order_id}/voice-summary")
    response.raise_for_status()
    summary = response.json()

    return [TextContent(type="text", text=summary.get("voice_summary", f"Photo order {order_id}"))]


async def handle_list_photo_orders(arguments: dict) -> list[TextContent]:
    """List photo orders with optional filtering."""
    params = {}
    if arguments.get("property_id"):
        params["property_id"] = arguments["property_id"]
    if arguments.get("address"):
        property_id = find_property_by_address(arguments["address"])
        if property_id:
            params["property_id"] = property_id
    if arguments.get("status"):
        params["status"] = arguments["status"]
    if arguments.get("limit"):
        params["limit"] = arguments["limit"]

    response = api_get("/photo-orders/", params=params)
    response.raise_for_status()
    orders = response.json()

    if not orders:
        return [TextContent(type="text", text="No photo orders found.")]

    text = f"Found {len(orders)} photo order(s):\n\n"
    for order in orders[:10]:  # Limit to 10 for voice
        status_emoji = {
            "draft": "📝",
            "pending": "⏳",
            "confirmed": "✅",
            "in_progress": "📸",
            "completed": "🎉",
            "cancelled": "❌"
        }.get(order.get("order_status", ""), "")

        line = f"{status_emoji} Order #{order['id']}"
        if order.get("property_address"):
            line += f" - {order['property_address']}"
        line += f" ({order.get('order_status', 'unknown')})"
        if order.get("estimated_cost_formatted"):
            line += f" - {order['estimated_cost_formatted']}"
        if order.get("delivery_count", 0) > 0:
            line += f" - {order['delivery_count']} photos"

        text += line + "\n"

    if len(orders) > 10:
        text += f"\n... and {len(orders) - 10} more."

    return [TextContent(type="text", text=text.strip())]


async def handle_sync_photo_order(arguments: dict) -> list[TextContent]:
    """Sync photo order status with provider."""
    order_id = arguments.get("order_id")
    if not order_id:
        property_id = arguments.get("property_id")
        address = arguments.get("address")
        if not property_id and address:
            property_id = find_property_by_address(address)
        if property_id:
            resp = api_get("/photo-orders/", params={"property_id": property_id, "limit": 1})
            if resp.ok:
                orders = resp.json()
                if orders:
                    order_id = orders[0]["id"]

    if not order_id:
        return [TextContent(type="text", text="Please provide an order_id or property address.")]

    response = api_post(f"/photo-orders/{order_id}/sync")
    response.raise_for_status()
    order = response.json()

    text = f"Order #{order['id']} synced. Status: {order.get('order_status', 'unknown')}."

    if order.get("delivery_count", 0) > 0:
        text += f" {order['delivery_count']} photos delivered."

    if order.get("photographer_assigned"):
        text += f" Photographer: {order['photographer_assigned']}."

    return [TextContent(type="text", text=text)]


async def handle_cancel_photo_order(arguments: dict) -> list[TextContent]:
    """Cancel a photo order."""
    order_id = arguments.get("order_id")
    if not order_id:
        property_id = arguments.get("property_id")
        address = arguments.get("address")
        if not property_id and address:
            property_id = find_property_by_address(address)
        if property_id:
            resp = api_get("/photo-orders/", params={"property_id": property_id, "status": "draft", "limit": 1})
            if resp.ok:
                orders = resp.json()
                if not orders:
                    resp = api_get("/photo-orders/", params={"property_id": property_id, "status": "pending", "limit": 1})
                    if resp.ok:
                        orders = resp.json()
                if orders:
                    order_id = orders[0]["id"]

    if not order_id:
        return [TextContent(type="text", text="No cancellable order found.")]

    params = {"reason": arguments.get("reason")} if arguments.get("reason") else {}
    response = api_post(f"/photo-orders/{order_id}/cancel", params=params)
    response.raise_for_status()
    order = response.json()

    return [TextContent(type="text", text=f"Photo order #{order['id']} cancelled.")]


async def handle_check_photo_availability(arguments: dict) -> list[TextContent]:
    """Check photo service availability for a property."""
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id or address.")]

    response = api_get(f"/photo-orders/services/availability", params={"property_id": property_id})
    response.raise_for_status()
    availability = response.json()

    text = f"Property #{property_id} photo services:\n\n"
    text += f"Available services: {', '.join(availability.get('services_available', [])[:10])}\n"
    text += f"Current orders: {availability.get('current_orders', 0)}\n"

    if availability.get("recommended_package"):
        text += f"Recommended package: {availability['recommended_package']}\n"

    text += f"Can order: {'Yes' if availability.get('can_order') else 'No'}"

    if availability.get("reason"):
        text += f" ({availability['reason']})"

    # Show some sample pricing
    costs = availability.get("estimated_costs", {})
    if costs:
        text += "\n\nSample pricing:\n"
        for service, price in list(costs.items())[:5]:
            text += f"  {service}: ${price:.0f}\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_get_property_photo_summary(arguments: dict) -> list[TextContent]:
    """Get photo ordering summary for a property."""
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id or address.")]

    response = api_get(f"/photo-orders/property/{property_id}/summary")
    response.raise_for_status()
    summary = response.json()

    text = f"Photo summary for {summary.get('property_address', f'Property #{property_id}')}:\n\n"
    text += f"Total orders: {summary.get('total_orders', 0)}\n"
    text += f"Active orders: {summary.get('active_orders', 0)}\n"
    text += f"Completed orders: {summary.get('completed_orders', 0)}\n"
    text += f"Total spend: ${summary.get('total_spend', 0):,.2f}\n"
    text += f"Photos delivered: {summary.get('total_photos_delivered', 0)}\n"

    if summary.get("latest_order"):
        order = summary["latest_order"]
        text += f"\nLatest order: #{order['id']} ({order.get('order_status', 'unknown')})"
        if order.get("estimated_cost_formatted"):
            text += f" - {order['estimated_cost_formatted']}"

    return [TextContent(type="text", text=text.strip())]


async def handle_create_photo_template(arguments: dict) -> list[TextContent]:
    """Create a reusable photo order template."""
    agent_id = arguments.get("agent_id", 1)  # Default to agent 1
    services = arguments.get("services", [])
    if not services:
        return [TextContent(type="text", text="Please provide services for the template.")]

    payload = {
        "template_name": arguments.get("template_name", "My Template"),
        "description": arguments.get("description"),
        "services": services,
        "base_price": arguments.get("base_price"),
        "property_types": arguments.get("property_types"),
        "tags": arguments.get("tags"),
        "is_active": arguments.get("is_active", True)
    }

    response = api_post("/photo-orders/templates/", json=payload, params={"agent_id": agent_id})
    response.raise_for_status()
    template = response.json()

    return [TextContent(type="text", text=f"Template '{template['template_name']}' created (ID: {template['id']}) with {len(template['services'])} services.")]


async def handle_list_photo_templates(arguments: dict) -> list[TextContent]:
    """List photo order templates."""
    agent_id = arguments.get("agent_id", 1)
    response = api_get("/photo-orders/templates/", params={"agent_id": agent_id})
    response.raise_for_status()
    templates = response.json()

    if not templates:
        return [TextContent(type="text", text="No templates found.")]

    text = f"Found {len(templates)} template(s):\n\n"
    for template in templates:
        text += f"• {template['template_name']} (#{template['id']})"
        if template.get("base_price_formatted"):
            text += f" - {template['base_price_formatted']}"
        if template.get("tags"):
            text += f" [{', '.join(template['tags'])}]"
        text += "\n"

    return [TextContent(type="text", text=text.strip())]


# ── Tool Registration ──

register_tool(Tool(
    name="order_photos",
    description="Order professional photography for a property. Choose a package (basic, premium, full_marketing) or specify custom services. Voice: 'Order photos for property 5 with the premium package' or 'Order a basic photo shoot for 123 Main St'.",
    inputSchema={
        "type": "object",
        "properties": {
            "property_id": {"type": "number", "description": "Property ID"},
            "address": {"type": "string", "description": "Property address (alternative to property_id)"},
            "package": {"type": "string", "enum": ["basic", "premium", "full_marketing"], "description": "Pre-defined package"},
            "services": {"type": "array", "items": {"type": "object"}, "description": "Custom services list"},
            "provider": {"type": "string", "enum": ["proxypics", "boxbrownie", "photoup", "manual"], "default": "proxypics", "description": "Photo service provider"},
            "requested_date": {"type": "string", "description": "Preferred date (ISO format)"},
            "time_slot": {"type": "string", "enum": ["morning", "afternoon", "flexible"], "description": "Preferred time"},
            "instructions": {"type": "string", "description": "Special instructions for photographer"},
            "contact_name": {"type": "string", "description": "On-site contact name"},
            "contact_phone": {"type": "string", "description": "On-site contact phone"}
        }
    }
), handle_order_photos)

register_tool(Tool(
    name="submit_photo_order",
    description="Submit a draft photo order to the provider. Voice: 'Submit the photo order for property 5' or 'Send my photo order to ProxyPics'.",
    inputSchema={
        "type": "object",
        "properties": {
            "order_id": {"type": "number", "description": "Photo order ID"},
            "property_id": {"type": "number", "description": "Property ID (finds draft order)"},
            "address": {"type": "string", "description": "Property address (finds draft order)"}
        }
    }
), handle_submit_photo_order)

register_tool(Tool(
    name="get_photo_order_status",
    description="Get status of a photo order with voice-friendly summary. Voice: 'What's the status of my photo order?' or 'Check photo order for 123 Main St'.",
    inputSchema={
        "type": "object",
        "properties": {
            "order_id": {"type": "number", "description": "Photo order ID"},
            "property_id": {"type": "number", "description": "Property ID (finds latest order)"},
            "address": {"type": "string", "description": "Property address (finds latest order)"}
        }
    }
), handle_get_photo_order_status)

register_tool(Tool(
    name="list_photo_orders",
    description="List photo orders with optional filtering. Voice: 'Show my photo orders' or 'List pending photo orders'.",
    inputSchema={
        "type": "object",
        "properties": {
            "property_id": {"type": "number", "description": "Filter by property"},
            "address": {"type": "string", "description": "Filter by property address"},
            "status": {"type": "string", "description": "Filter by status (draft, pending, confirmed, etc.)"},
            "limit": {"type": "number", "description": "Max results (default: 50)"}
        }
    }
), handle_list_photo_orders)

register_tool(Tool(
    name="sync_photo_order",
    description="Sync photo order status with provider to check for updates. Voice: 'Sync my photo order' or 'Check for new photos on property 5'.",
    inputSchema={
        "type": "object",
        "properties": {
            "order_id": {"type": "number", "description": "Photo order ID"},
            "property_id": {"type": "number", "description": "Property ID"},
            "address": {"type": "string", "description": "Property address"}
        }
    }
), handle_sync_photo_order)

register_tool(Tool(
    name="cancel_photo_order",
    description="Cancel a photo order. Voice: 'Cancel my photo order for property 5'.",
    inputSchema={
        "type": "object",
        "properties": {
            "order_id": {"type": "number", "description": "Photo order ID"},
            "property_id": {"type": "number", "description": "Property ID"},
            "address": {"type": "string", "description": "Property address"},
            "reason": {"type": "string", "description": "Cancellation reason"}
        }
    }
), handle_cancel_photo_order)

register_tool(Tool(
    name="check_photo_availability",
    description="Check photo service availability and pricing for a property. Voice: 'What photo services are available for property 5?'",
    inputSchema={
        "type": "object",
        "properties": {
            "property_id": {"type": "number", "description": "Property ID"},
            "address": {"type": "string", "description": "Property address"},
            "provider": {"type": "string", "default": "proxypics", "description": "Photo service provider"}
        }
    }
), handle_check_photo_availability)

register_tool(Tool(
    name="get_property_photo_summary",
    description="Get complete photo ordering summary for a property. Voice: 'What's the photo history for property 5?' or 'Show photo summary for 123 Main St'.",
    inputSchema={
        "type": "object",
        "properties": {
            "property_id": {"type": "number", "description": "Property ID"},
            "address": {"type": "string", "description": "Property address"}
        }
    }
), handle_get_property_photo_summary)

register_tool(Tool(
    name="create_photo_template",
    description="Create a reusable photo order template. Voice: 'Create a premium listing photo template'.",
    inputSchema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "number", "default": 1, "description": "Agent ID"},
            "template_name": {"type": "string", "description": "Template name"},
            "description": {"type": "string", "description": "Template description"},
            "services": {"type": "array", "items": {"type": "object"}, "description": "Services included"},
            "base_price": {"type": "number", "description": "Base price"},
            "property_types": {"type": "array", "items": {"type": "string"}, "description": "Applicable property types"},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Template tags"},
            "is_active": {"type": "boolean", "default": True, "description": "Template active"}
        },
        "required": ["template_name", "services"]
    }
), handle_create_photo_template)

register_tool(Tool(
    name="list_photo_templates",
    description="List reusable photo order templates. Voice: 'Show my photo templates'.",
    inputSchema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "number", "default": 1, "description": "Agent ID"}
        }
    }
), handle_list_photo_templates)
