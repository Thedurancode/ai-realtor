"""
Direct Mail MCP Tools

Voice-controlled tools for sending physical mail via Lob.com
Integrates with AI Realtor's direct mail system
"""

import os
import httpx
from typing import Any, Dict, List
from mcp_server.types import TextContent

from app.database import SessionLocal
from app.models.direct_mail import DirectMail, DirectMailTemplate, MailType, MailStatus
from app.models import Property, Contact, Agent
from app.schemas.direct_mail import PostcardSize, LetterSize


# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def find_property_by_address(db: SessionLocal, address_query: str) -> Property:
    """
    Find a property by address with flexible matching.

    Supports:
    - Full address: "123 Main St, New York, NY 10001"
    - Street + City: "123 Main St, New York"
    - Street name: "Main St"
    - City only: "New York"
    - ZIP code: "10001"

    Returns the best matching property or None.
    """
    if not address_query:
        return None

    query = address_query.strip().lower()

    # Try exact full address match first
    property = db.query(Property).filter(
        Property.address.ilike(f"%{query}%")
    ).first()
    if property:
        return property

    # Try city + state match
    if "," in address_query:
        parts = [p.strip() for p in address_query.split(",")]
        if len(parts) >= 2:
            city = parts[0].strip()
            rest = " ".join(parts[1:]).strip()

            # Match city and state
            property = db.query(Property).filter(
                Property.city.ilike(f"%{city}%")
            ).first()
            if property:
                return property

    # Try city only
    property = db.query(Property).filter(
        Property.city.ilike(f"%{query}%")
    ).first()
    if property:
        return property

    # Try ZIP code
    if len(query) >= 5 and query.replace(" ", "").replace("-", "").isdigit():
        zip_code = query.replace(" ", "").replace("- "")[:5]
        property = db.query(Property).filter(
            Property.zip_code == zip_code
        ).first()
        if property:
            return property

    # Try street name (remove numbers)
    words = query.split()
    if words:
        # Filter out numbers and common words
        street_words = [w for w in words if not w.isdigit() and w not in ['st', 'street', 'ave', 'avenue', 'rd', 'road', 'dr', 'drive', 'blvd', 'boulevard']]
        if street_words:
            street_query = " ".join(street_words[:3])  # Use first 3 words
            property = db.query(Property).filter(
                Property.address.ilike(f"%{street_query}%")
            ).first()
            if property:
                return property

    return None


async def handle_send_postcard(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Send a postcard via Lob.com

    Voice: "Send a just sold postcard for property 5"
    Voice: "Mail a postcard to 123 Main St in New York"
    Voice: "Send an open house postcard to the Miami property"
    Voice: "Mail a just sold card to the owner of 123 Main St"
    """
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    contact_id = arguments.get("contact_id")
    template = arguments.get("template", "just_sold")
    size = arguments.get("size", "4x6")
    color = arguments.get("color", False)

    db = SessionLocal()
    try:
        # Get property (by ID or address lookup)
        if property_id:
            property = db.query(Property).filter(Property.id == property_id).first()
            if not property:
                return [TextContent(
                    type="text",
                    text=f"Property {property_id} not found."
                )]
        elif address:
            property = find_property_by_address(db, address)
            if not property:
                return [TextContent(
                    type="text",
                    text=f"No property found matching address '{address}'. "
                         f"Try saying the full address, city, or property ID."
                )]
            # Provide feedback about which property was found
            address_desc = f"{property.address}, {property.city}, {property.state} {property.zip_code}"
        else:
            property = None

        # Get contact
        if contact_id:
            contact = db.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                return [TextContent(
                    type="text",
                    text=f"Contact {contact_id} not found."
                )]

            # Build address from contact
            to_address = {
                "name": contact.name or "Property Owner",
                "address_line1": contact.address or "123 Main St",
                "address_city": contact.city or "Anytown",
                "address_state": contact.state or "CA",
                "address_zip": contact.zip_code or "90210",
                "address_country": "US"
            }
        else:
            # Use property address
            if property:
                to_address = {
                    "name": "Property Owner",
                    "address_line1": property.address or "123 Main St",
                    "address_city": property.city or "Anytown",
                    "address_state": property.state or "CA",
                    "address_zip": property.zip_code or "90210",
                    "address_country": "US"
                }
            else:
                return [TextContent(
                    type="text",
                    text="Please provide a contact ID or property with address."
                )]

        # Get agent for return address
        agent = db.query(Agent).first()  # Get first agent (default)
        from_address = {
            "name": agent.full_name or "Real Estate Agent" if agent else "Agent",
            "company": agent.brokerage or "" if agent else "",
            "address_line1": agent.office_address or "123 Main St" if agent else "123 Main St",
            "address_city": agent.office_city or "Anytown" if agent else "Anytown",
            "address_state": agent.office_state or "CA" if agent else "CA",
            "address_zip": agent.office_zip or "90210" if agent else "90210",
            "address_country": "US"
        }

        # Prepare API request
        payload = {
            "mail_type": "postcard",
            "to_address": to_address,
            "from_address": from_address,
            "template_name": template,
            "size": size,
            "color": color,
            "property_id": property_id,
            "contact_id": contact_id
        }

        # Send via API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/direct-mail/postcards?agent_id={agent.id if agent else 1}",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        # Build success message with property details
        property_info = ""
        if address and property:
            property_info = f" to {property.address}, {property.city}, {property.state}"
        elif property:
            property_info = f" to property {property.id} ({property.address}, {property.city})"

        return [TextContent(
            type="text",
            text=f"Postcard sent successfully{property_info}! Mailpiece ID: {result['id']}. "
                 f"It should arrive in 2-5 business days. "
                 f"Estimated cost: ${result.get('estimated_cost', 0):.2f}"
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to send postcard: {str(e)}"
        )]
    finally:
        db.close()


async def handle_send_letter(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Send a letter via Lob.com

    Voice: "Send a letter to contact 5"
    Voice: "Mail the offer letter to the property owner"
    """
    contact_id = arguments.get("contact_id")
    file_url = arguments.get("file_url")
    certified = arguments.get("certified", False)

    if not contact_id:
        return [TextContent(
            type="text",
            text="Please provide a contact ID to send the letter to."
        )]

    if not file_url:
        return [TextContent(
            type="text",
            text="Please provide a PDF file URL for the letter content."
        )]

    db = SessionLocal()
    try:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return [TextContent(
                type="text",
                text=f"Contact {contact_id} not found."
            )]

        to_address = {
            "name": contact.name or "Recipient",
            "address_line1": contact.address or "123 Main St",
            "address_city": contact.city or "Anytown",
            "address_state": contact.state or "CA",
            "address_zip": contact.zip_code or "90210",
            "address_country": "US"
        }

        # Get agent return address
        agent = db.query(Agent).first()
        from_address = {
            "name": agent.full_name or "Agent" if agent else "Agent",
            "address_line1": agent.office_address or "123 Main St" if agent else "123 Main St",
            "address_city": agent.office_city or "Anytown" if agent else "Anytown",
            "address_state": agent.office_state or "CA" if agent else "CA",
            "address_zip": agent.office_zip or "90210" if agent else "90210",
            "address_country": "US"
        }

        payload = {
            "mail_type": "letter",
            "to_address": to_address,
            "from_address": from_address,
            "file_url": file_url,
            "certified_mail": certified,
            "contact_id": contact_id
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/direct-mail/letters?agent_id={agent.id if agent else 1}",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        mail_type = "certified letter" if certified else "letter"

        return [TextContent(
            type="text",
            text=f"{mail_type.capitalize()} sent to {contact.name}! "
                 f"Mailpiece ID: {result['id']}. "
                 f"Expected delivery in 2-5 business days."
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to send letter: {str(e)}"
        )]
    finally:
        db.close()


async def handle_check_mail_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Check the status of a mailpiece

    Voice: "What's the status of mailpiece 5?"
    Voice: "Has the postcard been delivered yet?"
    """
    mailpiece_id = arguments.get("mailpiece_id")

    if not mailpiece_id:
        return [TextContent(
            type="text",
            text="Please provide a mailpiece ID to check."
        )]

    db = SessionLocal()
    try:
        mailpiece = db.query(DirectMail).filter(
            DirectMail.id == mailpiece_id
        ).first()

        if not mailpiece:
            return [TextContent(
                type="text",
                text=f"Mailpiece {mailpiece_id} not found."
            )]

        status = mailpiece.mail_status.value.replace("_", " ")
        mail_type = mailpiece.mail_type.value

        # Get tracking info
        tracking_info = ""
        if mailpiece.tracking_events and len(mailpiece.tracking_events) > 0:
            latest = mailpiece.tracking_events[-1]
            tracking_info = f" Latest update: {latest.get('status', 'unknown')} on {latest.get('timestamp', '')}"

        delivery_info = ""
        if mailpiece.delivered_at:
            delivery_info = f" Delivered on {mailpiece.delivered_at.strftime('%B %d, %Y')}"
        elif mailpiece.expected_delivery_date:
            delivery_info = f" Expected delivery by {mailpiece.expected_delivery_date.strftime('%B %d, %Y')}"

        return [TextContent(
            type="text",
            text=f"Your {mail_type} status is: {status.title()}.{delivery_info}{tracking_info}"
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to check status: {str(e)}"
        )]
    finally:
        db.close()


async def handle_list_mailpieces(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    List all sent mailpieces

    Voice: "Show me all my postcards"
    Voice: "What mail have I sent recently?"
    """
    status = arguments.get("status")
    mail_type = arguments.get("mail_type")
    limit = arguments.get("limit", 10)

    db = SessionLocal()
    try:
        query = db.query(DirectMail)

        if status:
            try:
                mail_status = MailStatus[status.upper()]
                query = query.filter(DirectMail.mail_status == mail_status)
            except KeyError:
                pass

        if mail_type:
            try:
                mail_t = MailType[mail_type.lower()]
                query = query.filter(DirectMail.mail_type == mail_t)
            except KeyError:
                pass

        mailpieces = query.order_by(DirectMail.created_at.desc()).limit(limit).all()

        if not mailpieces:
            return [TextContent(
                type="text",
                text="No mailpieces found."
            )]

        # Build summary
        summary_lines = [f"You have {len(mailpieces)} mailpiece{ 's' if len(mailpieces) != 1 else ''}:"]
        for mp in mailpieces:
            recipient = mp.to_address.get("name", "Unknown")
            m_type = mp.mail_type.value
            m_status = mp.mail_status.value.replace("_", " ")
            created = mp.created_at.strftime("%B %d") if mp.created_at else "Unknown"

            summary_lines.append(f"  • {m_type} to {recipient} - {m_status} (sent {created})")

        return [TextContent(
            type="text",
            text="\n".join(summary_lines)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to list mailpieces: {str(e)}"
        )]
    finally:
        db.close()


async def handle_create_campaign(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Create a bulk direct mail campaign

    Voice: "Create a just sold campaign for all properties in Miami"
    Voice: "Start a postcard campaign for contacts 1, 2, and 3"
    Voice: "Create a campaign for the Brooklyn properties"
    """
    name = arguments.get("name", "Bulk Campaign")
    template = arguments.get("template", "just_sold")
    property_ids = arguments.get("property_ids", [])
    contact_ids = arguments.get("contact_ids", [])
    city = arguments.get("city")  # New: city-based targeting
    send_immediately = arguments.get("send_immediately", False)

    db = SessionLocal()
    try:
        # If city is provided, look up all properties in that city
        if city and not property_ids:
            properties = db.query(Property).filter(
                Property.city.ilike(f"%{city}%")
            ).all()
            if properties:
                property_ids = [p.id for p in properties]
                if len(property_ids) > 10:
                    return [TextContent(
                        type="text",
                        text=f"Found {len(property_ids)} properties in {city}. "
                             f"That's a lot! Please specify a smaller area or use specific property IDs."
                    )]

        if not property_ids and not contact_ids:
            return [TextContent(
                type="text",
                text="Please provide property_ids, contact_ids, or a city name for the campaign."
            )]

        payload = {
            "name": name,
            "campaign_type": template,
            "mail_type": "postcard",
            "target_property_ids": property_ids,
            "target_contact_ids": contact_ids,
            "send_immediately": send_immediately
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/direct-mail/campaigns",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        total_recipients = len(property_ids) + len(contact_ids)

        # Build success message with targeting details
        targeting = ""
        if city:
            targeting = f" for {len(property_ids)} properties in {city}"
        elif property_ids:
            targeting = f" for {len(property_ids)} properties"
        elif contact_ids:
            targeting = f" for {len(contact_ids)} contacts"

        return [TextContent(
            type="text",
            text=f"Campaign '{name}' created{targeting}. "
                 f"Campaign ID: {result['id']}. "
                 f"{'Sending immediately!' if send_immediately else 'Scheduled for later.'}"
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to create campaign: {str(e)}"
        )]
    finally:
        db.close()


async def handle_get_templates(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    List available direct mail templates

    Voice: "What postcard templates are available?"
    Voice: "Show me all mail templates"
    """
    template_type = arguments.get("type", "postcard")

    db = SessionLocal()
    try:
        templates = db.query(DirectMailTemplate).filter(
            DirectMailTemplate.template_type == template_type,
            DirectMailTemplate.is_active == True
        ).all()

        if not templates:
            return [TextContent(
                type="text",
                text=f"No {template_type} templates found. You can create custom templates or use the built-in ones."
            )]

        summary_lines = [f"Available {template_type} templates:"]
        for tmpl in templates:
            summary_lines.append(f"  • {tmpl.name} - {tmpl.description or 'No description'}")
            if tmpl.campaign_type:
                summary_lines.append(f"    Type: {tmpl.campaign_type}")

        return [TextContent(
            type="text",
            text="\n".join(summary_lines)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to get templates: {str(e)}"
        )]
    finally:
        db.close()


async def handle_verify_address(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Verify a postal address before sending

    Voice: "Verify the address 123 Main St, Anytown, CA 90210"
    Voice: "Check if this address is valid"
    """
    address_line1 = arguments.get("address_line1")
    city = arguments.get("city")
    state = arguments.get("state")
    zip_code = arguments.get("zip_code")

    if not all([address_line1, city, state, zip_code]):
        return [TextContent(
            type="text",
            text="Please provide the full address: address, city, state, and ZIP code."
        )]

    address = {
        "address_line1": address_line1,
        "address_city": city,
        "address_state": state,
        "address_zip": zip_code
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/direct-mail/verify-address",
                json=address,
                timeout=30.0
            )
            result = response.json()

        if result.get("is_valid"):
            verified = result.get("verified_address", {})
            return [TextContent(
                type="text",
                text=f"Address is valid! Standardized format: "
                     f"{verified.get('name', '')}, {verified.get('address_line1', '')}, "
                     f"{verified.get('address_city', '')}, {verified.get('address_state', '')} "
                     f"{verified.get('address_zip', '')}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Address verification failed: {result.get('deliverability', 'unknown')}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to verify address: {str(e)}"
        )]


async def handle_cancel_mailpiece(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Cancel a mailpiece before it's sent

    Voice: "Cancel mailpiece 5"
    Voice: "Stop the postcard from being mailed"
    """
    mailpiece_id = arguments.get("mailpiece_id")

    if not mailpiece_id:
        return [TextContent(
            type="text",
            text="Please provide a mailpiece ID to cancel."
        )]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/direct-mail/postcards/{mailpiece_id}/cancel",
                timeout=30.0
            )
            response.raise_for_status()

        return [TextContent(
            type="text",
            text=f"Mailpiece {mailpiece_id} has been cancelled successfully."
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to cancel mailpiece: {str(e)}"
        )]


# Register all tools
from mcp.types import Tool
from ..server import register_tool

__all__ = [
    "handle_send_postcard",
    "handle_send_letter",
    "handle_check_mail_status",
    "handle_list_mailpieces",
    "handle_create_campaign",
    "handle_get_templates",
    "handle_verify_address",
    "handle_cancel_mailpiece"
]

# Tool registrations with schemas
register_tool(
    Tool(
        name="send_postcard",
        description="Send a postcard via Lob.com direct mail. Can send to a property address, specific contact, or property ID. Voice: 'Send a just sold postcard to 123 Main St' or 'Mail an open house card to the Miami property'.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "number", "description": "Property ID (optional if address provided)"},
                "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main St' or 'the Miami property')"},
                "contact_id": {"type": "number", "description": "Contact ID to send to (optional)"},
                "template": {"type": "string", "description": "Template name", "enum": ["just_sold", "open_house", "market_update", "new_listing", "price_reduction", "hello", "interested_in_selling"], "default": "just_sold"},
                "size": {"type": "string", "description": "Postcard size", "enum": ["4x6", "6x9", "6x11"], "default": "4x6"},
                "color": {"type": "boolean", "description": "Color printing", "default": False}
            }
        }
    ),
    handle_send_postcard
)

register_tool(
    Tool(
        name="send_letter",
        description="Send a letter via Lob.com with a PDF attachment. Voice: 'Send a letter to contact 5' or 'Mail the offer letter'.",
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {"type": "number", "description": "Contact ID to send to"},
                "file_url": {"type": "string", "description": "PDF file URL for letter content"},
                "certified": {"type": "boolean", "description": "Send as certified mail", "default": False}
            },
            "required": ["contact_id", "file_url"]
        }
    ),
    handle_send_letter
)

register_tool(
    Tool(
        name="check_mail_status",
        description="Check the delivery status of a mailpiece. Voice: 'Check the status of mailpiece 5' or 'Where's my postcard?'.",
        inputSchema={
            "type": "object",
            "properties": {
                "mailpiece_id": {"type": "number", "description": "Mailpiece ID to check"}
            },
            "required": ["mailpiece_id"]
        }
    ),
    handle_check_mail_status
)

register_tool(
    Tool(
        name="list_mailpieces",
        description="List all sent mailpieces with their delivery status. Voice: 'Show me all my mailpieces' or 'List my direct mail'.",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status", "enum": ["draft", "scheduled", "processing", "mailed", "in_transit", "delivered", "cancelled", "failed"]}
            }
        }
    ),
    handle_list_mailpieces
)

register_tool(
    Tool(
        name="create_direct_mail_campaign",
        description="Create a bulk direct mail campaign for multiple properties or contacts. Voice: 'Create a just sold campaign for all properties in Miami' or 'Start a postcard campaign for Brooklyn'.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Campaign name"},
                "template": {"type": "string", "description": "Template name", "enum": ["just_sold", "open_house", "market_update", "new_listing", "price_reduction", "hello", "interested_in_selling"], "default": "just_sold"},
                "property_ids": {"type": "array", "items": {"type": "number"}, "description": "List of property IDs"},
                "contact_ids": {"type": "array", "items": {"type": "number"}, "description": "List of contact IDs"},
                "city": {"type": "string", "description": "Target all properties in a city (voice-friendly)"},
                "send_immediately": {"type": "boolean", "description": "Send immediately or schedule for later", "default": False}
            }
        }
    ),
    handle_create_campaign
)

register_tool(
    Tool(
        name="get_direct_mail_templates",
        description="List available direct mail templates. Voice: 'Show me available templates' or 'What templates can I use?'.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    handle_get_templates
)

register_tool(
    Tool(
        name="verify_address",
        description="Verify a postal address with USPS before sending mail. Voice: 'Verify the address 123 Main St, Anytown, CA 90210'.",
        inputSchema={
            "type": "object",
            "properties": {
                "address_line1": {"type": "string", "description": "Street address"},
                "city": {"type": "string", "description": "City"},
                "state": {"type": "string", "description": "State (2-letter code)"},
                "zip_code": {"type": "string", "description": "ZIP code"}
            },
            "required": ["address_line1", "city", "state", "zip_code"]
        }
    ),
    handle_verify_address
)

register_tool(
    Tool(
        name="cancel_mailpiece",
        description="Cancel a mailpiece before it's sent. Voice: 'Cancel mailpiece 5' or 'Stop that postcard'.",
        inputSchema={
            "type": "object",
            "properties": {
                "mailpiece_id": {"type": "number", "description": "Mailpiece ID to cancel"}
            },
            "required": ["mailpiece_id"]
        }
    ),
    handle_cancel_mailpiece
)
