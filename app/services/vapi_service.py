"""
VAPI Integration Service

Handles phone calls using VAPI API with property recap context.
"""
import os
import requests
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.property_recap import PropertyRecap
from app.services.property_recap_service import property_recap_service


class VAPIService:
    """Service for making phone calls via VAPI API"""

    def __init__(self):
        self.api_key = os.getenv("VAPI_API_KEY")
        self.base_url = "https://api.vapi.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def make_property_call(
        self,
        db: Session,
        property: Property,
        phone_number: str,
        call_purpose: str = "property_update",
        assistant_config: Optional[Dict] = None,
        custom_context: Optional[Dict] = None
    ) -> Dict:
        """
        Make a phone call about a property using VAPI.

        Args:
            db: Database session
            property: Property to discuss
            phone_number: Phone number to call (E.164 format, e.g., +14155551234)
            call_purpose: Purpose of call (property_update, contract_reminder, etc.)
            assistant_config: Optional custom assistant configuration

        Returns:
            VAPI call response with call ID and status
        """
        # Ensure recap exists and is up to date
        recap = await property_recap_service.ensure_recap_exists(
            db, property, trigger=f"phone_call_{call_purpose}"
        )

        # Build assistant configuration
        if not assistant_config:
            assistant_config = self._build_default_assistant_config(
                property, recap, call_purpose, custom_context
            )

        # Prepare call payload
        payload = {
            "assistant": assistant_config,
            "phoneNumberId": None,  # Use VAPI's default number
            "customer": {
                "number": phone_number,
            },
        }

        # Make API call to VAPI
        response = requests.post(
            f"{self.base_url}/call/phone",
            headers=self.headers,
            json=payload
        )

        response.raise_for_status()

        call_data = response.json()

        return {
            "success": True,
            "call_id": call_data.get("id"),
            "status": call_data.get("status"),
            "property_id": property.id,
            "property_address": f"{property.address}, {property.city}, {property.state}",
            "phone_number": phone_number,
            "call_purpose": call_purpose,
            "vapi_response": call_data
        }

    def _build_default_assistant_config(
        self,
        property: Property,
        recap: PropertyRecap,
        call_purpose: str,
        custom_context: Optional[Dict] = None
    ) -> Dict:
        """Build default VAPI assistant configuration with property context"""

        # Extract structured context
        context = recap.recap_context
        voice_summary = recap.voice_summary

        # Build system prompt based on call purpose
        system_prompts = {
            "property_update": f"""You are a professional real estate assistant calling to provide an update about a property.

PROPERTY CONTEXT:
{voice_summary}

Your goal is to:
1. Introduce yourself as a real estate assistant
2. Provide a brief property update
3. Answer any questions they have about the property
4. Offer to send more detailed information via email

Be professional, concise, and helpful. Keep the call under 3 minutes unless they have specific questions.

DETAILED PROPERTY INFO:
{recap.recap_text}

CONTRACT STATUS:
- Ready to Close: {'Yes' if context['readiness']['is_ready_to_close'] else 'No'}
- Completed Contracts: {context['readiness']['completed']}/{context['readiness']['total_required']}
- In Progress: {context['readiness']['in_progress']}
- Missing: {context['readiness']['missing']}
""",
            "contract_reminder": f"""You are calling to remind about pending contracts for a property.

PROPERTY: {property.address}, {property.city}, {property.state}

CONTRACT STATUS:
- {context['readiness']['in_progress']} contracts in progress
- {context['readiness']['missing']} contracts missing

Your goal is to:
1. Politely remind them about pending contracts
2. Explain which contracts need attention
3. Ask if they need help or have questions
4. Offer to resend contract links if needed

Be friendly and helpful, not pushy.

FULL CONTEXT:
{recap.recap_text}
""",
            "closing_ready": f"""You are calling with great news - a property is ready to close!

PROPERTY: {property.address}, {property.city}, {property.state}

Your goal is to:
1. Congratulate them that all contracts are complete
2. Confirm the property is ready to close
3. Discuss next steps (closing date, final walkthrough, etc.)
4. Answer any questions

Be enthusiastic but professional.

PROPERTY DETAILS:
{voice_summary}

{recap.recap_text}
""",
            "specific_contract_reminder": f"""You are calling {custom_context.get('contact_name', 'the contact') if custom_context else 'the contact'} about a specific contract that needs attention.

PROPERTY: {property.address}, {property.city}, {property.state}

CONTRACT DETAILS:
- Contract Name: {custom_context.get('contract_name', 'Unknown') if custom_context else 'Unknown'}
- Status: {custom_context.get('contract_status', 'pending') if custom_context else 'pending'}

{f"SPECIAL NOTE: {custom_context['custom_message']}" if custom_context and custom_context.get('custom_message') else ""}

Your goal is to:
1. Greet {custom_context.get('contact_name', 'them') if custom_context else 'them'} warmly
2. Remind them about the {custom_context.get('contract_name', 'contract') if custom_context else 'contract'} that needs their attention
3. Explain what's needed (signature, review, etc.)
4. Answer any questions about the contract
5. Offer to resend the contract link if needed

Be friendly, professional, and helpful. Don't be pushy.

FULL PROPERTY CONTEXT:
{recap.recap_text}
""",
            "skip_trace_outreach": f"""You are calling {custom_context.get('owner_name', 'the property owner') if custom_context else 'the property owner'} about their property at {custom_context.get('property_address', property.address) if custom_context else property.address}.

This is a COLD CALL for lead generation.

{f"SPECIAL NOTE: {custom_context['custom_message']}" if custom_context and custom_context.get('custom_message') else ""}

Your goal is to:
1. Introduce yourself as a real estate professional
2. Ask if they've considered selling their property
3. Mention current market conditions are favorable
4. Ask if they'd be interested in a no-obligation market analysis
5. Answer questions about the selling process
6. Be respectful if they're not interested

IMPORTANT:
- Be professional and courteous
- Don't be pushy or aggressive
- Respect if they say no
- Keep it conversational and exploratory
- Maximum 2-3 minutes unless they engage

PROPERTY INFO:
Address: {custom_context.get('property_address', property.address) if custom_context else property.address}
Owner: {custom_context.get('owner_name', 'Property owner') if custom_context else 'Property owner'}

Market context:
{voice_summary}
""",
        }

        system_prompt = system_prompts.get(
            call_purpose,
            system_prompts["property_update"]
        )

        # Assistant configuration for VAPI
        return {
            "name": f"Real Estate Assistant - {call_purpose.replace('_', ' ').title()}",
            "firstMessage": self._get_first_message(call_purpose, property),
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ],
                "temperature": 0.7,
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel - professional female voice
            },
            "recordingEnabled": True,
            "endCallFunctionEnabled": True,
            "clientMessages": [
                "transcript",
                "hang",
                "function-call",
                "speech-update",
                "metadata",
                "conversation-update"
            ],
            # Add property context as metadata
            "metadata": {
                "property_id": property.id,
                "property_address": f"{property.address}, {property.city}, {property.state}",
                "call_purpose": call_purpose,
                "recap_version": recap.version,
                "contracts_ready": context['readiness']['is_ready_to_close'],
            }
        }

    def _get_first_message(self, call_purpose: str, property: Property) -> str:
        """Get the first message the assistant says when call connects"""

        first_messages = {
            "property_update": f"Hi! This is your real estate assistant calling with an update about the property at {property.address}. Do you have a moment?",
            "contract_reminder": f"Hi! This is your real estate assistant calling about some pending contracts for {property.address}. Do you have a minute to discuss?",
            "closing_ready": f"Hi! I have great news about the property at {property.address}! Do you have a moment to hear it?",
        }

        return first_messages.get(
            call_purpose,
            f"Hi! This is your real estate assistant calling about {property.address}. How are you today?"
        )

    async def get_call_status(self, call_id: str) -> Dict:
        """Get status of a VAPI call"""
        response = requests.get(
            f"{self.base_url}/call/{call_id}",
            headers=self.headers
        )

        response.raise_for_status()
        return response.json()

    async def end_call(self, call_id: str) -> Dict:
        """End an ongoing VAPI call"""
        response = requests.patch(
            f"{self.base_url}/call/{call_id}",
            headers=self.headers,
            json={"status": "ended"}
        )

        response.raise_for_status()
        return response.json()

    async def get_call_recording(self, call_id: str) -> Optional[str]:
        """Get recording URL for a completed call"""
        call_data = await self.get_call_status(call_id)

        return call_data.get("recordingUrl")


# Singleton instance
vapi_service = VAPIService()
