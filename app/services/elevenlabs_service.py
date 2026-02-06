"""
ElevenLabs Conversational AI Service

Creates a voice agent connected to the MCP SSE server, giving it access
to all property management tools. Supports outbound calls via Twilio.
"""
import os
from typing import Optional

from elevenlabs import (
    ElevenLabs,
    ConversationalConfig,
    AgentConfig,
    PromptAgentApiModelInput,
    PromptAgentApiModelInputToolsItem_System,
    SystemToolConfigInput,
    SystemToolConfigInputParams_EndCall,
    EndCallToolConfig,
)


SYSTEM_PROMPT = """You are an AI real estate assistant for a property management platform.
You have access to a full property management system through MCP tools. Use them to help
callers with their real estate needs.

Your capabilities:
- List and look up properties (list_properties, get_property)
- Create and manage properties (create_property, delete_property)
- Enrich properties with Zillow data (enrich_property)
- Skip trace to find property owners (skip_trace_property)
- Manage contacts on properties (add_contact)
- Check and manage contracts (check_property_contract_readiness, attach_required_contracts)
- AI-powered contract suggestions (ai_suggest_contracts, apply_ai_contract_suggestions)
- Set deal types and check deal status (set_deal_type, get_deal_status)
- Generate property recaps (generate_property_recap, get_property_recap)
- Check signing status (get_signing_status)

Guidelines:
- Be professional, friendly, and concise
- When asked about a property, use get_property or list_properties first
- Always confirm before making changes (creating, deleting, or modifying records)
- Provide clear summaries of what you find
- If you don't know something, say so rather than guessing
- End the call politely when the caller is done
"""

DEFAULT_FIRST_MESSAGE = (
    "Hi, this is your AI real estate assistant. "
    "I can help you with properties, contracts, contacts, and deals. "
    "How can I help you today?"
)


class ElevenLabsService:
    """Service for managing ElevenLabs Conversational AI agents with MCP tools."""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.agent_id = os.getenv("ELEVENLABS_AGENT_ID")
        self.mcp_server_id = os.getenv("ELEVENLABS_MCP_SERVER_ID")
        self.phone_number_id = os.getenv("ELEVENLABS_PHONE_NUMBER_ID")
        self.mcp_sse_url = os.getenv(
            "ELEVENLABS_MCP_SSE_URL",
            "https://ai-realtor.fly.dev:8001/sse"
        )
        self._client = None

    @property
    def client(self) -> ElevenLabs:
        if not self._client:
            if not self.api_key:
                raise ValueError("ELEVENLABS_API_KEY environment variable not set")
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    def setup_mcp_server(self) -> dict:
        """Register the MCP SSE server with ElevenLabs. One-time setup."""
        result = self.client.conversational_ai.mcp_servers.create(
            config={
                "url": self.mcp_sse_url,
                "name": "AI Realtor MCP",
            }
        )
        self.mcp_server_id = result.id
        return {
            "mcp_server_id": result.id,
            "url": self.mcp_sse_url,
            "name": "AI Realtor MCP",
            "transport": getattr(result.config, "transport", "SSE"),
        }

    def create_agent(
        self,
        system_prompt: str = SYSTEM_PROMPT,
        first_message: str = DEFAULT_FIRST_MESSAGE,
        llm: str = "claude-sonnet-4-5",
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
    ) -> dict:
        """Create an ElevenLabs conversational AI agent with MCP tools."""
        if not self.mcp_server_id:
            raise ValueError(
                "MCP server not registered. Call setup_mcp_server() first."
            )

        # Build tools list
        end_call_tool = PromptAgentApiModelInputToolsItem_System(
            name="end_call",
            type="system",
            description="End the call when the conversation is complete",
        )

        prompt_config = PromptAgentApiModelInput(
            prompt=system_prompt,
            llm=llm,
            temperature=0.7,
            max_tokens=1000,
            mcp_server_ids=[self.mcp_server_id],
            tools=[end_call_tool],
        )

        conversation_config = ConversationalConfig(
            agent=AgentConfig(
                first_message=first_message,
                prompt=prompt_config,
            ),
        )

        result = self.client.conversational_ai.agents.create(
            conversation_config=conversation_config,
            name="AI Realtor Voice Agent",
        )

        self.agent_id = result.agent_id
        return {
            "agent_id": result.agent_id,
            "name": "AI Realtor Voice Agent",
            "llm": llm,
            "voice_id": voice_id,
            "mcp_server_id": self.mcp_server_id,
            "status": "created",
        }

    def setup_agent(self) -> dict:
        """Full setup: register MCP server + create agent. One-time operation."""
        mcp_result = self.setup_mcp_server()
        agent_result = self.create_agent()
        return {
            "mcp_server": mcp_result,
            "agent": agent_result,
            "widget_html": (
                f'<elevenlabs-convai agent-id="{agent_result["agent_id"]}"></elevenlabs-convai>\n'
                '<script src="https://elevenlabs.io/convai-widget/index.js" async></script>'
            ),
        }

    def get_agent_info(self) -> dict:
        """Get current agent configuration and status."""
        if not self.agent_id:
            return {"error": "No agent configured. Run setup first."}

        result = self.client.conversational_ai.agents.get(agent_id=self.agent_id)
        return {
            "agent_id": result.agent_id,
            "name": result.name,
            "status": getattr(result, "status", "unknown"),
            "mcp_server_id": self.mcp_server_id,
            "mcp_sse_url": self.mcp_sse_url,
        }

    def update_agent_prompt(self, prompt: str) -> dict:
        """Update the agent's system prompt."""
        if not self.agent_id:
            return {"error": "No agent configured. Run setup first."}

        prompt_config = PromptAgentApiModelInput(prompt=prompt)
        conversation_config = ConversationalConfig(
            agent=AgentConfig(prompt=prompt_config)
        )

        self.client.conversational_ai.agents.update(
            agent_id=self.agent_id,
            conversation_config=conversation_config,
        )
        return {"agent_id": self.agent_id, "prompt_updated": True}

    def list_phone_numbers(self) -> list:
        """List available ElevenLabs phone numbers."""
        result = self.client.conversational_ai.phone_numbers.list()
        numbers = []
        for num in result:
            numbers.append({
                "id": getattr(num, "phone_number_id", getattr(num, "id", None)),
                "number": getattr(num, "phone_number", getattr(num, "number", None)),
                "label": getattr(num, "label", None),
            })
        return numbers

    def make_call(
        self,
        phone_number: str,
        custom_first_message: Optional[str] = None,
    ) -> dict:
        """Make an outbound call using the ElevenLabs agent via Twilio."""
        if not self.agent_id:
            raise ValueError("No agent configured. Run setup first.")
        if not self.phone_number_id:
            raise ValueError(
                "ELEVENLABS_PHONE_NUMBER_ID not set. "
                "Configure a phone number in ElevenLabs first."
            )

        # Validate phone format
        if not phone_number.startswith("+"):
            raise ValueError("Phone number must be in E.164 format (e.g., +14155551234)")

        kwargs = {
            "agent_id": self.agent_id,
            "agent_phone_number_id": self.phone_number_id,
            "to_number": phone_number,
        }

        if custom_first_message:
            kwargs["first_message"] = custom_first_message

        result = self.client.conversational_ai.twilio.outbound_call(**kwargs)

        return {
            "call_id": getattr(result, "call_id", getattr(result, "id", None)),
            "status": getattr(result, "status", "initiated"),
            "to_number": phone_number,
            "agent_id": self.agent_id,
        }

    def get_widget_config(self) -> dict:
        """Get the web widget embed configuration."""
        if not self.agent_id:
            return {"error": "No agent configured. Run setup first."}

        return {
            "agent_id": self.agent_id,
            "embed_html": (
                f'<elevenlabs-convai agent-id="{self.agent_id}"></elevenlabs-convai>\n'
                '<script src="https://elevenlabs.io/convai-widget/index.js" async></script>'
            ),
        }


# Singleton instance
elevenlabs_service = ElevenLabsService()
