"""
Voice Agent Service

Handles incoming voice calls via VAPI webhook, sends transcribed speech to
Claude API for tool-calling, and converts responses to speech via ElevenLabs TTS.
"""
import json
import logging
from datetime import datetime
from typing import Any, Optional

import anthropic
import httpx

from app.config import settings
from app.database import SessionLocal
from app.models.voice_agent_call import VoiceAgentCall

logger = logging.getLogger(__name__)

# Default ElevenLabs voice (Rachel)
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# System prompt for the voice agent
VOICE_AGENT_SYSTEM_PROMPT = """You are Ed Duran's AI real estate assistant, accessible by phone.
You help manage a real estate investment portfolio using available tools.
Keep responses concise and conversational since this is a voice call.
When the user asks you to do something, use the appropriate tool.
Always confirm actions before executing them.
Speak naturally as if on a phone call - avoid bullet points, markdown, or long lists.
Summarize results briefly and ask if they want more detail."""

# Tool definitions for Claude API - maps to RealtorClaw API actions
VOICE_TOOLS = [
    {
        "name": "research_property",
        "description": "Research a property by address. Gathers public records, ownership info, and market data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Full property address to research"
                }
            },
            "required": ["address"]
        }
    },
    {
        "name": "get_comps",
        "description": "Get comparable sales for a property. Returns recent sales of similar properties nearby.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID to get comps for"
                },
                "radius_miles": {
                    "type": "number",
                    "description": "Search radius in miles (default 1)"
                }
            },
            "required": ["property_id"]
        }
    },
    {
        "name": "score_property",
        "description": "Score a property for investment potential. Returns a 0-100 score with breakdown.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID to score"
                }
            },
            "required": ["property_id"]
        }
    },
    {
        "name": "send_report",
        "description": "Send a property report via email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID to generate report for"
                },
                "email": {
                    "type": "string",
                    "description": "Email address to send report to"
                }
            },
            "required": ["property_id"]
        }
    },
    {
        "name": "get_pipeline",
        "description": "Get the current deal pipeline summary. Shows properties by stage (lead, contacted, under contract, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "list_properties",
        "description": "List properties in the portfolio, optionally filtered by status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status: lead, contacted, under_contract, closed, dead"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of properties to return (default 10)"
                }
            }
        }
    },
    {
        "name": "get_property",
        "description": "Get details for a specific property by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID"
                }
            },
            "required": ["property_id"]
        }
    },
    {
        "name": "skip_trace",
        "description": "Skip trace a property to find owner contact information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID to skip trace"
                }
            },
            "required": ["property_id"]
        }
    },
    {
        "name": "send_mail",
        "description": "Send a direct mail piece (letter or postcard) to a property owner.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID to send mail to"
                },
                "mail_type": {
                    "type": "string",
                    "description": "Type of mail: letter or postcard"
                }
            },
            "required": ["property_id"]
        }
    },
    {
        "name": "get_daily_digest",
        "description": "Get today's daily digest with portfolio summary, action items, and market updates.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    }
]

# API base URL for internal calls
API_BASE = "http://localhost:8000"


class VoiceAgentService:
    """Service for handling voice agent calls with Claude tool-calling."""

    def __init__(self):
        self._call_contexts: dict[str, dict] = {}  # call_id -> context
        self._anthropic_client: Optional[anthropic.Anthropic] = None
        self._http_client: Optional[httpx.Client] = None

    @property
    def anthropic_client(self) -> anthropic.Anthropic:
        if self._anthropic_client is None:
            self._anthropic_client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key
            )
        return self._anthropic_client

    @property
    def http_client(self) -> httpx.Client:
        if self._http_client is None:
            self._http_client = httpx.Client(base_url=API_BASE, timeout=30.0)
        return self._http_client

    async def handle_call_start(self, call_data: dict) -> dict:
        """Handle a new incoming or outgoing voice call."""
        call_id = call_data.get("call_id", call_data.get("id", ""))
        phone_number = call_data.get("phone_number", call_data.get("customer", {}).get("number", ""))
        direction = call_data.get("direction", "inbound")

        logger.info(f"Voice agent call started: {call_id} ({direction}) from {phone_number}")

        # Initialize call context with conversation history
        self._call_contexts[call_id] = {
            "messages": [],
            "actions": [],
            "phone_number": phone_number,
            "direction": direction,
            "started_at": datetime.utcnow().isoformat(),
        }

        # Persist to database
        db = SessionLocal()
        try:
            call_record = VoiceAgentCall(
                call_id=call_id,
                phone_number=phone_number,
                direction=direction,
                status="started",
                started_at=datetime.utcnow(),
                transcript="",
                actions_taken="[]",
            )
            db.add(call_record)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to persist call start: {e}")
            db.rollback()
        finally:
            db.close()

        return {
            "status": "ok",
            "message": f"Voice agent ready for call {call_id}",
        }

    async def handle_speech(self, call_id: str, transcript: str) -> dict:
        """
        Process transcribed speech from the caller.
        Sends to Claude API with tool definitions, executes any tool calls,
        and returns the text response for TTS.
        """
        context = self._call_contexts.get(call_id)
        if not context:
            # Recover context if missing (e.g., server restart)
            context = {
                "messages": [],
                "actions": [],
                "phone_number": "",
                "direction": "inbound",
                "started_at": datetime.utcnow().isoformat(),
            }
            self._call_contexts[call_id] = context

        logger.info(f"Voice agent [{call_id}] user said: {transcript}")

        # Add user message to conversation history
        context["messages"].append({
            "role": "user",
            "content": transcript,
        })

        # Call Claude API with tools
        try:
            response_text = await self._process_with_claude(call_id, context)
        except Exception as e:
            logger.error(f"Claude API error for call {call_id}: {e}")
            response_text = "I'm sorry, I had trouble processing that. Could you try again?"

        # Add assistant response to history
        context["messages"].append({
            "role": "assistant",
            "content": response_text,
        })

        # Update database with transcript
        self._update_call_record(call_id, context)

        # Generate TTS audio URL via ElevenLabs
        audio_url = await self._text_to_speech(response_text)

        return {
            "response_text": response_text,
            "audio_url": audio_url,
            "call_id": call_id,
        }

    async def handle_function_call(self, call_id: str, function_name: str, arguments: dict) -> dict:
        """
        Handle a function call event from VAPI.
        VAPI may detect tool use and send it as a separate event.
        """
        logger.info(f"Voice agent [{call_id}] function call: {function_name}({arguments})")

        result = await self._execute_tool(function_name, arguments)

        context = self._call_contexts.get(call_id, {})
        actions = context.get("actions", [])
        actions.append({
            "tool": function_name,
            "arguments": arguments,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return {
            "result": result,
        }

    async def handle_call_end(self, call_data: dict) -> dict:
        """Handle call ended event."""
        call_id = call_data.get("call_id", call_data.get("id", ""))
        logger.info(f"Voice agent call ended: {call_id}")

        context = self._call_contexts.pop(call_id, {})

        # Update database
        db = SessionLocal()
        try:
            call_record = db.query(VoiceAgentCall).filter(
                VoiceAgentCall.call_id == call_id
            ).first()
            if call_record:
                call_record.status = "completed"
                call_record.ended_at = datetime.utcnow()
                # Build full transcript from messages
                if context.get("messages"):
                    transcript_lines = []
                    for msg in context["messages"]:
                        role = "User" if msg["role"] == "user" else "Agent"
                        transcript_lines.append(f"{role}: {msg['content']}")
                    call_record.transcript = "\n".join(transcript_lines)
                if context.get("actions"):
                    call_record.actions_taken = json.dumps(context["actions"])
                db.commit()
        except Exception as e:
            logger.error(f"Failed to persist call end: {e}")
            db.rollback()
        finally:
            db.close()

        return {"status": "ok", "call_id": call_id}

    async def _process_with_claude(self, call_id: str, context: dict) -> str:
        """Send conversation to Claude API with tool definitions and handle tool use."""
        messages = context["messages"]

        # Convert tool definitions to Claude format
        claude_tools = []
        for tool in VOICE_TOOLS:
            claude_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"],
            })

        # Call Claude
        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=VOICE_AGENT_SYSTEM_PROMPT,
            tools=claude_tools,
            messages=messages,
        )

        # Process response - handle tool use loop
        final_text = ""
        while response.stop_reason == "tool_use":
            # Extract tool use blocks
            tool_results = []
            assistant_content = response.content

            for block in assistant_content:
                if block.type == "text":
                    final_text += block.text
                elif block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_use_id = block.id

                    logger.info(f"Voice agent [{call_id}] calling tool: {tool_name}({tool_input})")

                    # Execute the tool
                    result = await self._execute_tool(tool_name, tool_input)

                    # Record action
                    context["actions"].append({
                        "tool": tool_name,
                        "arguments": tool_input,
                        "result": result,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result) if isinstance(result, dict) else str(result),
                    })

            # Add assistant response and tool results to messages
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            # Continue conversation with tool results
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=VOICE_AGENT_SYSTEM_PROMPT,
                tools=claude_tools,
                messages=messages,
            )

        # Extract final text response
        for block in response.content:
            if block.type == "text":
                final_text += block.text

        # Clean up messages - replace raw content blocks with text for storage
        # Keep the last assistant message as plain text
        if messages and messages[-1].get("role") == "user" and isinstance(messages[-1].get("content"), list):
            # Remove the tool_result messages from stored history to keep it clean
            # They were needed for the API call but we store the final response
            messages.pop()  # Remove tool_result
            if messages and messages[-1].get("role") == "assistant":
                messages.pop()  # Remove assistant tool_use

        return final_text

    async def _execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """Execute a tool by calling the internal API."""
        try:
            if tool_name == "research_property":
                address = arguments.get("address", "")
                resp = self.http_client.post(
                    "/agentic-research/research",
                    json={"address": address}
                )
                resp.raise_for_status()
                return resp.json()

            elif tool_name == "get_comps":
                property_id = arguments["property_id"]
                params = {}
                if arguments.get("radius_miles"):
                    params["radius_miles"] = arguments["radius_miles"]
                resp = self.http_client.get(
                    f"/comps/sales/{property_id}",
                    params=params,
                )
                resp.raise_for_status()
                return resp.json()

            elif tool_name == "score_property":
                property_id = arguments["property_id"]
                resp = self.http_client.post(
                    f"/property-scoring/{property_id}/score"
                )
                resp.raise_for_status()
                return resp.json()

            elif tool_name == "send_report":
                property_id = arguments["property_id"]
                email = arguments.get("email", settings.admin_email)
                resp = self.http_client.post(
                    f"/properties/{property_id}/report",
                    json={"email": email},
                )
                resp.raise_for_status()
                return resp.json()

            elif tool_name == "get_pipeline":
                resp = self.http_client.get("/pipeline/summary")
                resp.raise_for_status()
                return resp.json()

            elif tool_name == "list_properties":
                params = {}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("limit"):
                    params["limit"] = arguments["limit"]
                resp = self.http_client.get("/properties/", params=params)
                resp.raise_for_status()
                return resp.json()

            elif tool_name == "get_property":
                property_id = arguments["property_id"]
                resp = self.http_client.get(f"/properties/{property_id}")
                resp.raise_for_status()
                return resp.json()

            elif tool_name == "skip_trace":
                property_id = arguments["property_id"]
                resp = self.http_client.post(f"/skip-trace/{property_id}")
                resp.raise_for_status()
                return resp.json()

            elif tool_name == "send_mail":
                property_id = arguments["property_id"]
                mail_type = arguments.get("mail_type", "letter")
                endpoint = f"/direct-mail/send-{'letter' if mail_type == 'letter' else 'postcard'}"
                resp = self.http_client.post(
                    endpoint,
                    json={"property_id": property_id},
                )
                resp.raise_for_status()
                return resp.json()

            elif tool_name == "get_daily_digest":
                resp = self.http_client.post("/daily-digest/trigger")
                resp.raise_for_status()
                return resp.json()

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except httpx.HTTPStatusError as e:
            logger.error(f"Tool {tool_name} HTTP error: {e.response.status_code} {e.response.text}")
            return {"error": f"Tool {tool_name} failed with status {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Tool {tool_name} error: {e}")
            return {"error": f"Tool {tool_name} failed: {str(e)}"}

    async def _text_to_speech(self, text: str) -> Optional[str]:
        """Convert text to speech using ElevenLabs TTS API. Returns audio URL or None."""
        if not settings.elevenlabs_api_key:
            logger.warning("ElevenLabs API key not configured, skipping TTS")
            return None

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{DEFAULT_VOICE_ID}",
                    headers={
                        "xi-api-key": settings.elevenlabs_api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_turbo_v2",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                        },
                    },
                    timeout=15.0,
                )
                if resp.status_code == 200:
                    # For VAPI integration, we return the audio as base64
                    # VAPI handles playback directly
                    import base64
                    audio_b64 = base64.b64encode(resp.content).decode("utf-8")
                    return f"data:audio/mpeg;base64,{audio_b64}"
                else:
                    logger.error(f"ElevenLabs TTS failed: {resp.status_code} {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return None

    def _update_call_record(self, call_id: str, context: dict):
        """Update the database record with current transcript and actions."""
        db = SessionLocal()
        try:
            call_record = db.query(VoiceAgentCall).filter(
                VoiceAgentCall.call_id == call_id
            ).first()
            if call_record:
                call_record.status = "in_progress"
                # Build transcript
                transcript_lines = []
                for msg in context["messages"]:
                    if isinstance(msg.get("content"), str):
                        role = "User" if msg["role"] == "user" else "Agent"
                        transcript_lines.append(f"{role}: {msg['content']}")
                call_record.transcript = "\n".join(transcript_lines)
                if context.get("actions"):
                    call_record.actions_taken = json.dumps(context["actions"])
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update call record: {e}")
            db.rollback()
        finally:
            db.close()

    async def initiate_outbound_call(self, phone_number: str) -> dict:
        """Initiate an outbound call via VAPI."""
        if not settings.vapi_api_key:
            raise ValueError("VAPI API key not configured")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.vapi.ai/call/phone",
                headers={
                    "Authorization": f"Bearer {settings.vapi_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "phoneNumberId": settings.vapi_phone_number_id,
                    "customer": {
                        "number": phone_number,
                    },
                    "assistantOverrides": {
                        "firstMessage": "Hey, this is Ed's AI assistant. How can I help you today?",
                        "serverUrl": f"{API_BASE}/voice/agent/vapi/webhook",
                    },
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            result = resp.json()

        call_id = result.get("id", "")
        # Track the outbound call
        await self.handle_call_start({
            "call_id": call_id,
            "phone_number": phone_number,
            "direction": "outbound",
        })

        return {
            "call_id": call_id,
            "phone_number": phone_number,
            "status": "initiated",
        }

    def get_call_record(self, call_id: str) -> Optional[dict]:
        """Get a call record by call_id."""
        db = SessionLocal()
        try:
            record = db.query(VoiceAgentCall).filter(
                VoiceAgentCall.call_id == call_id
            ).first()
            if not record:
                return None
            return {
                "id": record.id,
                "call_id": record.call_id,
                "phone_number": record.phone_number,
                "direction": record.direction,
                "status": record.status,
                "transcript": record.transcript,
                "actions_taken": json.loads(record.actions_taken) if record.actions_taken else [],
                "started_at": record.started_at.isoformat() if record.started_at else None,
                "ended_at": record.ended_at.isoformat() if record.ended_at else None,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
        finally:
            db.close()

    def list_call_records(self, limit: int = 20) -> list[dict]:
        """List recent voice agent calls."""
        db = SessionLocal()
        try:
            records = (
                db.query(VoiceAgentCall)
                .order_by(VoiceAgentCall.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "call_id": r.call_id,
                    "phone_number": r.phone_number,
                    "direction": r.direction,
                    "status": r.status,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
        finally:
            db.close()


# Singleton
voice_agent_service = VoiceAgentService()
