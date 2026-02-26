"""AI Voice Assistant Service - handles inbound calls with VAPI."""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.phone_call import PhoneCall
from app.models.phone_number import PhoneNumber
from app.models.property import Property
from app.models.scheduled_task import ScheduledTask, TaskType, TaskStatus
from app.models.offer import Offer
from app.services.heartbeat_service import heartbeat_service

logger = logging.getLogger(__name__)


class VoiceAssistantService:
    """Handle inbound voice calls with AI-powered responses."""

    # AI Prompts for different scenarios
    PROMPT_GREETING = """You are a professional real estate AI assistant for {company_name}.
Your goal is to help callers with property inquiries, schedule viewings, take messages, or create offer leads.

Be friendly, professional, and concise. Ask for clarification if needed.
Always identify the property first if they're asking about a specific listing.
"""

    PROMPT_PROPERTY_INQUIRY = """The caller is asking about property {address}.

Property Details:
- Price: ${price:,.0f}
- {bedrooms} bedrooms, {bathrooms} bathrooms
- {sqft} sqft
- Description: {description}

Pipeline Status: {stage}
Health: {health}
Next Action: {next_action}

Provide a concise overview (2-3 sentences). Ask if they want to:
1. Schedule a viewing
2. Make an offer
3. Speak to an agent
"""

    PROMPT_SCHEDULE_VIEWING = """The caller wants to schedule a viewing for {address}.

Ask for:
1. Their name
2. Preferred date/time
3. Phone number

Then confirm: "Great! I've scheduled a viewing for {date} at {time}. The agent will call you at {phone} to confirm."
"""

    PROMPT_MAKE_OFFER = """The caller wants to make an offer on {address}.

Ask for:
1. Their name
2. Offer amount
3. Phone number
4. Any contingencies

Then confirm: "Thanks! I've created an offer lead for ${amount:,.0f}. The agent will contact you at {phone} within 24 hours."
"""

    PROMPT_SPEAK_AGENT = """The caller wants to speak to an agent.

Say: "I'm sorry, all agents are currently assisting other clients. Let me take a message and they'll get back to you within 1 hour."

Ask for:
1. Their name
2. Phone number
3. Brief message

Confirm: "Thanks {name}. I've passed your message to the team. Someone will call you at {phone} within the hour."
"""

    PROMPT_GENERAL_INQUIRY = """The caller has a general question.

Handle these common queries:
- "What properties do you have?" → Ask for location, price range, beds/baths
- "What areas do you serve?" → List your coverage areas
- "How do I contact an agent?" → Offer to take message

Be helpful and guide them toward a property inquiry or scheduling.
"""

    def __init__(self):
        pass

    def handle_incoming_call(
        self,
        db: Session,
        phone_number: str,
        vapi_call_id: str,
        vapi_phone_id: str
    ) -> Dict[str, Any]:
        """Handle incoming call from VAPI webhook.

        Args:
            db: Database session
            phone_number: Caller's phone number
            vapi_call_id: VAPI call UUID
            vapi_phone_id: VAPI phone number ID

        Returns:
            Dict with AI response configuration for VAPI
        """
        # Find phone number configuration
        phone_config = db.query(PhoneNumber).filter(
            PhoneNumber.phone_number == vapi_phone_id,
            PhoneNumber.is_active == True
        ).first()

        if not phone_config:
            logger.error(f"Phone number {vapi_phone_id} not found in database")
            return self._error_response("Phone number not configured")

        # Create call log
        call = PhoneCall(
            agent_id=phone_config.agent_id,
            direction="inbound",
            phone_number=phone_number,
            vapi_call_id=vapi_call_id,
            vapi_phone_number_id=vapi_phone_id,
            status="in_progress",
            started_at=datetime.now(timezone.utc)
        )
        db.add(call)
        db.commit()

        # Build AI response
        greeting = phone_config.greeting_message or f"Thank you for calling"
        company_name = phone_config.agent.company_name if phone_config.agent else "our real estate team"

        response = {
            "assistant_id": phone_config.ai_assistant_id,
            "voice_id": phone_config.ai_voice_id,
            "first_sentence": f"{greeting}. I'm your AI assistant. How can I help you today?",
            "prompt": self.PROMPT_GREETING.format(company_name=company_name),
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 200,
            "hipaa_enabled": False,
            "recording_enabled": True,
            "transcription_enabled": True,
            "callback_url": f"/voice-assistant/callback/{call.id}",
            "end_call_message": "Thanks for calling. Have a great day!",
            " interruption_enabled": True
        }

        logger.info(f"Inbound call started: {vapi_call_id} from {phone_number}")
        return response

    def handle_call_update(
        self,
        db: Session,
        call_id: int,
        event: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle call progress events from VAPI.

        Args:
            db: Database session
            call_id: Phone call ID
            event: Event type (transcript, function_call, ended, etc.)
            data: Event data from VAPI

        Returns:
            Dict with any response needed
        """
        call = db.query(PhoneCall).filter(PhoneCall.id == call_id).first()
        if not call:
            logger.error(f"Call {call_id} not found")
            return {}

        if event == "transcript":
            # Update transcription as call progresses
            current = call.transcription or ""
            new_text = data.get("text", "")
            call.transcription = current + " " + new_text
            db.commit()
            return {}

        elif event == "function_call":
            # AI wants to call a function (property lookup, schedule, etc.)
            return self._handle_function_call(db, call, data)

        elif event == "ended":
            # Call completed
            call.status = data.get("status", "completed")
            call.duration_seconds = data.get("duration", 0)
            call.ended_at = datetime.now(timezone.utc)
            call.recording_url = data.get("recording_url")
            db.commit()

            # Generate AI summary of the call
            self._generate_call_summary(db, call)

            logger.info(f"Call {call_id} ended: {call.status}")
            return {}

        return {}

    def _handle_function_call(
        self,
        db: Session,
        call: PhoneCall,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle AI function calls during conversation.

        Functions AI can call:
        - lookup_property: Get property details
        - schedule_viewing: Schedule a viewing
        - create_offer: Create an offer lead
        - take_message: Take a message for agent
        - get_properties: Search properties
        """
        function_name = data.get("name")
        arguments = data.get("arguments", {})

        logger.info(f"AI function call: {function_name} with args: {arguments}")

        if function_name == "lookup_property":
            return self._lookup_property(db, call, arguments)

        elif function_name == "schedule_viewing":
            return self._schedule_viewing(db, call, arguments)

        elif function_name == "create_offer":
            return self._create_offer_lead(db, call, arguments)

        elif function_name == "take_message":
            return self._take_message(db, call, arguments)

        elif function_name == "get_properties":
            return self._search_properties(db, call, arguments)

        else:
            return {"error": f"Unknown function: {function_name}"}

    def _lookup_property(
        self,
        db: Session,
        call: PhoneCall,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI: Look up property details."""
        property_id = args.get("property_id")
        address = args.get("address")

        if property_id:
            prop = db.query(Property).filter(Property.id == property_id).first()
        elif address:
            prop = db.query(Property).filter(Property.address.ilike(f"%{address}%")).first()
        else:
            return {"error": "Please provide property ID or address"}

        if not prop:
            return {"error": "Property not found"}

        # Get heartbeat for pipeline context
        heartbeat = heartbeat_service.get_heartbeat(db, prop.id)

        call.property_id = prop.id
        call.intent = "property_inquiry"
        db.commit()

        return {
            "property": {
                "id": prop.id,
                "address": prop.address,
                "price": prop.price,
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "square_feet": prop.square_feet,
                "description": prop.description,
                "stage": heartbeat["stage_label"],
                "health": heartbeat["health"],
                "next_action": heartbeat["next_action"]
            }
        }

    def _schedule_viewing(
        self,
        db: Session,
        call: PhoneCall,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI: Schedule a property viewing."""
        property_id = args.get("property_id")
        caller_name = args.get("caller_name")
        phone = args.get("phone")
        date_time = args.get("date_time")

        if not all([property_id, caller_name, phone, date_time]):
            return {"error": "Missing required information"}

        # Create scheduled task
        task = ScheduledTask(
            agent_id=call.agent_id,
            property_id=property_id,
            task_type=TaskType.FOLLOW_UP,
            status=TaskStatus.PENDING,
            title=f"Viewing scheduled: {caller_name}",
            description=f"Call {caller_name} at {phone} to confirm viewing for {date_time}",
            due_date=date_time,
            source="phone_call"
        )
        db.add(task)

        call.caller_name = caller_name
        call.caller_phone = phone
        call.outcome = "viewing_scheduled"
        call.follow_up_created = True
        db.commit()

        return {
            "success": True,
            "message": f"Viewing scheduled for {date_time}",
            "confirmation": f"The agent will call you at {phone} to confirm"
        }

    def _create_offer_lead(
        self,
        db: Session,
        call: PhoneCall,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI: Create an offer lead."""
        property_id = args.get("property_id")
        caller_name = args.get("caller_name")
        phone = args.get("phone")
        amount = args.get("amount")
        contingencies = args.get("contingencies", "")

        if not all([property_id, caller_name, phone, amount]):
            return {"error": "Missing required information"}

        # Create offer
        offer = Offer(
            property_id=property_id,
            buyer_name=caller_name,
            buyer_contact=phone,
            offer_amount=amount,
            contingencies=contingencies,
            status="lead",
            source="phone_call"
        )
        db.add(offer)

        call.caller_name = caller_name
        call.caller_phone = phone
        call.outcome = "offer_created"
        call.follow_up_created = True
        db.commit()

        return {
            "success": True,
            "message": f"Offer lead created for ${amount:,.0f}",
            "confirmation": f"The agent will contact you at {phone} within 24 hours"
        }

    def _take_message(
        self,
        db: Session,
        call: PhoneCall,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI: Take a message for the agent."""
        caller_name = args.get("caller_name", "Caller")
        phone = args.get("phone")
        message = args.get("message", "")

        call.caller_name = caller_name
        call.caller_phone = phone
        call.message = message
        call.outcome = "message_taken"
        call.follow_up_created = True
        db.commit()

        # Create follow-up task
        task = ScheduledTask(
            agent_id=call.agent_id,
            task_type=TaskType.FOLLOW_UP,
            status=TaskStatus.PENDING,
            title=f"Return call: {caller_name}",
            description=f"Call {caller_name} at {phone}. Message: {message}",
            priority="high"
        )
        db.add(task)
        db.commit()

        return {
            "success": True,
            "message": f"Message taken for {caller_name}",
            "confirmation": f"Someone will call you at {phone} within 1 hour"
        }

    def _search_properties(
        self,
        db: Session,
        call: PhoneCall,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI: Search for properties matching criteria."""
        city = args.get("city")
        min_price = args.get("min_price")
        max_price = args.get("max_price")
        bedrooms = args.get("bedrooms")

        query = db.query(Property).filter(Property.status != "complete")

        if city:
            query = query.filter(Property.city.ilike(f"%{city}%"))
        if min_price:
            query = query.filter(Property.price >= min_price)
        if max_price:
            query = query.filter(Property.price <= max_price)
        if bedrooms:
            query = query.filter(Property.bedrooms >= bedrooms)

        properties = query.limit(5).all()

        return {
            "properties": [
                {
                    "id": p.id,
                    "address": p.address,
                    "price": p.price,
                    "bedrooms": p.bedrooms,
                    "bathrooms": p.bathrooms
                }
                for p in properties
            ],
            "count": len(properties)
        }

    def _generate_call_summary(self, db: Session, call: PhoneCall):
        """Generate AI summary of the call transcript."""
        if not call.transcription:
            return

        # Use Claude to summarize
        # This would use the existing AI service
        call.summary = f"Call from {call.phone_number}. " \
                     f"Intent: {call.intent or 'unknown'}. " \
                     f"Outcome: {call.outcome or 'unknown'}."

        db.commit()

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Return error response for VAPI."""
        return {
            "error": True,
            "message": message,
            "first_sentence": "I'm sorry, I'm having trouble connecting. Please try again later."
        }


voice_assistant_service = VoiceAssistantService()
