"""
Webhook Listener Service — processes incoming webhook events in real time.

Replaces polling-based workflows with instant event-driven reactions.
Supports: new_lead, property_update, offer_received, contract_signed,
          email_received, mls_listing.
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://localhost:8000")


async def send_telegram(message: str) -> bool:
    """Send a message via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info("Telegram notification sent successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False


async def _api_call(method: str, path: str, **kwargs) -> Optional[dict]:
    """Make an internal API call to the FastAPI backend."""
    url = f"{API_BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if method == "GET":
                resp = await client.get(url, **kwargs)
            else:
                resp = await client.post(url, **kwargs)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"Internal API call failed: {method} {path} — {e}")
        return None


async def _handle_new_lead(payload: dict) -> dict:
    """
    New lead received — auto-research, score, and alert.

    Expected payload keys: address, price, source, contact_name, contact_phone
    """
    address = payload.get("address", "Unknown address")
    price = payload.get("price")
    source = payload.get("source", "Unknown")
    contact_name = payload.get("contact_name", "Unknown")

    results = {"event": "new_lead", "address": address, "actions": []}

    # Step 1: Try to create or find the property
    property_data = await _api_call("POST", "/context/property/create", json={
        "address": address,
        "price": price,
        "agent_id": 1,
        "session_id": "webhook_listener",
    })
    if property_data:
        property_id = property_data.get("property_id") or property_data.get("id")
        results["property_id"] = property_id
        results["actions"].append("property_created")

        # Step 2: Research the property
        research = await _api_call("POST", f"/research/property/{property_id}/research")
        if research:
            results["actions"].append("research_started")

        # Step 3: Score the property
        score_data = await _api_call("POST", f"/properties/{property_id}/score")
        if score_data:
            results["score"] = score_data.get("score")
            results["actions"].append("scored")

    # Step 4: Send Telegram alert
    price_str = f"${price:,.0f}" if price else "N/A"
    score_str = f"Score: {results.get('score', 'pending')}"
    msg = (
        f"<b>New Lead</b>\n"
        f"Address: {address}\n"
        f"Price: {price_str}\n"
        f"Contact: {contact_name}\n"
        f"Source: {source}\n"
        f"{score_str}"
    )
    await send_telegram(msg)
    results["actions"].append("telegram_sent")

    return results


async def _handle_property_update(payload: dict) -> dict:
    """
    Property data updated — notify if significant changes.

    Expected payload keys: property_id, changes (dict of field: new_value)
    """
    property_id = payload.get("property_id")
    changes = payload.get("changes", {})

    results = {"event": "property_update", "property_id": property_id, "actions": []}

    significant_fields = {"price", "status", "deal_type", "arv", "repair_cost"}
    significant_changes = {k: v for k, v in changes.items() if k in significant_fields}

    if significant_changes:
        changes_str = "\n".join(f"  {k}: {v}" for k, v in significant_changes.items())
        msg = (
            f"<b>Property Updated</b>\n"
            f"Property #{property_id}\n"
            f"Changes:\n{changes_str}"
        )
        await send_telegram(msg)
        results["actions"].append("telegram_sent")
    else:
        results["actions"].append("minor_update_skipped")

    return results


async def _handle_offer_received(payload: dict) -> dict:
    """
    New offer received — analyze and alert with recommendation.

    Expected payload keys: property_id, offer_price, buyer_name, financing_type,
                          contingencies, closing_date
    """
    property_id = payload.get("property_id")
    offer_price = payload.get("offer_price", 0)
    buyer_name = payload.get("buyer_name", "Unknown")
    financing_type = payload.get("financing_type", "Unknown")
    contingencies = payload.get("contingencies", [])
    closing_date = payload.get("closing_date", "TBD")

    results = {"event": "offer_received", "property_id": property_id, "actions": []}

    # Get property details to compare
    property_data = await _api_call("GET", f"/properties/{property_id}")
    asking_price = None
    address = f"Property #{property_id}"

    recommendation = "Review needed"
    if property_data:
        asking_price = property_data.get("price")
        address = property_data.get("address", address)

        if asking_price and offer_price:
            pct = (offer_price / asking_price) * 100
            if pct >= 98:
                recommendation = "STRONG — at or above asking"
            elif pct >= 93:
                recommendation = "REASONABLE — close to asking"
            elif pct >= 85:
                recommendation = "LOW — counter recommended"
            else:
                recommendation = "VERY LOW — likely reject or counter aggressively"
            results["offer_pct_of_asking"] = round(pct, 1)

    results["recommendation"] = recommendation
    results["actions"].append("analyzed")

    # Build contingency summary
    cont_str = ", ".join(contingencies) if contingencies else "None"

    asking_str = f"${asking_price:,.0f}" if asking_price else "N/A"
    offer_str = f"${offer_price:,.0f}" if offer_price else "N/A"

    msg = (
        f"<b>Offer Received</b>\n"
        f"Property: {address}\n"
        f"Buyer: {buyer_name}\n"
        f"Offer: {offer_str} (Asking: {asking_str})\n"
        f"Financing: {financing_type}\n"
        f"Contingencies: {cont_str}\n"
        f"Closing: {closing_date}\n"
        f"\n<b>Recommendation:</b> {recommendation}"
    )
    await send_telegram(msg)
    results["actions"].append("telegram_sent")

    return results


async def _handle_contract_signed(payload: dict) -> dict:
    """
    Contract signed — send notification.

    Expected payload keys: property_id, contract_name, signer_name, signed_at
    """
    property_id = payload.get("property_id")
    contract_name = payload.get("contract_name", "Unknown contract")
    signer_name = payload.get("signer_name", "Unknown")
    signed_at = payload.get("signed_at", "just now")

    results = {"event": "contract_signed", "property_id": property_id, "actions": []}

    address = f"Property #{property_id}"
    if property_id:
        property_data = await _api_call("GET", f"/properties/{property_id}")
        if property_data:
            address = property_data.get("address", address)

    msg = (
        f"<b>Contract Signed</b>\n"
        f"Property: {address}\n"
        f"Contract: {contract_name}\n"
        f"Signed by: {signer_name}\n"
        f"Time: {signed_at}"
    )
    await send_telegram(msg)
    results["actions"].append("telegram_sent")

    return results


async def _handle_email_received(payload: dict) -> dict:
    """
    Email received — notify if relevant.

    Expected payload keys: from_email, subject, snippet, property_id (optional)
    """
    from_email = payload.get("from_email", "Unknown")
    subject = payload.get("subject", "No subject")
    snippet = payload.get("snippet", "")

    results = {"event": "email_received", "actions": []}

    msg = (
        f"<b>Email Received</b>\n"
        f"From: {from_email}\n"
        f"Subject: {subject}\n"
        f"{snippet[:200]}"
    )
    await send_telegram(msg)
    results["actions"].append("telegram_sent")

    return results


async def _handle_mls_listing(payload: dict) -> dict:
    """
    New MLS listing detected — score, check watchlists, alert if match.

    Expected payload keys: address, price, bedrooms, bathrooms, sqft,
                          property_type, city, state, mls_id
    """
    address = payload.get("address", "Unknown")
    price = payload.get("price")
    city = payload.get("city", "")
    state = payload.get("state", "")
    mls_id = payload.get("mls_id", "")

    results = {"event": "mls_listing", "address": address, "actions": []}

    # Create property in system
    property_data = await _api_call("POST", "/context/property/create", json={
        "address": address,
        "price": price,
        "agent_id": 1,
        "session_id": "webhook_mls",
    })

    property_id = None
    if property_data:
        property_id = property_data.get("property_id") or property_data.get("id")
        results["property_id"] = property_id
        results["actions"].append("property_created")

        # Score it
        score_data = await _api_call("POST", f"/properties/{property_id}/score")
        if score_data:
            results["score"] = score_data.get("score")
            results["actions"].append("scored")

        # Check against watchlists
        match_data = await _api_call("GET", f"/watchlists/check/{property_id}")
        if match_data:
            matches = match_data.get("matches", [])
            results["watchlist_matches"] = len(matches)
            results["actions"].append("watchlists_checked")

            if matches:
                watchlist_names = ", ".join(m.get("name", "?") for m in matches)
                price_str = f"${price:,.0f}" if price else "N/A"
                score_str = results.get("score", "N/A")
                msg = (
                    f"<b>MLS Match Found</b>\n"
                    f"Address: {address}\n"
                    f"Price: {price_str}\n"
                    f"Location: {city}, {state}\n"
                    f"MLS: {mls_id}\n"
                    f"Score: {score_str}\n"
                    f"Matched watchlists: {watchlist_names}"
                )
                await send_telegram(msg)
                results["actions"].append("telegram_sent")

    return results


# Event type to handler mapping
_EVENT_HANDLERS = {
    "new_lead": _handle_new_lead,
    "property_update": _handle_property_update,
    "offer_received": _handle_offer_received,
    "contract_signed": _handle_contract_signed,
    "email_received": _handle_email_received,
    "mls_listing": _handle_mls_listing,
}

SUPPORTED_EVENT_TYPES = list(_EVENT_HANDLERS.keys())


async def process_webhook(event_type: str, payload: dict) -> dict:
    """
    Process an incoming webhook event.

    Args:
        event_type: One of the supported event types.
        payload: Event-specific data.

    Returns:
        dict with processing results and actions taken.
    """
    handler = _EVENT_HANDLERS.get(event_type)
    if not handler:
        logger.warning(f"Unknown webhook event type: {event_type}")
        return {
            "error": f"Unknown event type: {event_type}",
            "supported_types": SUPPORTED_EVENT_TYPES,
        }

    logger.info(f"Processing webhook event: {event_type}")
    try:
        result = await handler(payload)
        logger.info(f"Webhook event {event_type} processed: {result.get('actions', [])}")
        return result
    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {e}", exc_info=True)
        return {"event": event_type, "error": str(e)}
