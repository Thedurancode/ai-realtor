"""Telnyx Voice Service - Direct telephony API integration."""
import os
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class TelnyxService:
    """Service for making phone calls using Telnyx API."""

    BASE_URL = "https://api.telnyx.com/v2"

    def __init__(self):
        self.api_key = os.getenv("TELNYX_API_KEY")
        self.connection_id = os.getenv("TELNYX_CONNECTION_ID")
        self.telnyx_number = os.getenv("TELNYX_PHONE_NUMBER")
        self.webhook_url = os.getenv("TELNYX_WEBHOOK_URL")

    async def create_call(
        self,
        to: str,
        script: str,
        from_number: Optional[str] = None,
        property_id: Optional[int] = None,
        questions: Optional[List[str]] = None,
        detect_machine: bool = True,
        record_call: bool = True,
        webhook_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call using Telnyx API.

        Args:
            to: Destination phone number (E.164 format, e.g., "+15551234567")
            script: Text script for the call (will be converted to speech via TTS)
            from_number: Caller ID number (defaults to TELNYX_PHONE_NUMBER)
            property_id: Property ID for context tracking
            questions: List of questions to ask (for AI agent)
            detect_machine: Enable answering machine detection
            record_call: Enable call recording
            webhook_url: Webhook URL for call events

        Returns:
            Dict with call_id, status, and call_control_id
        """
        if not self.api_key:
            raise ValueError("TELNYX_API_KEY not configured")
        if not self.connection_id:
            raise ValueError("TELNYX_CONNECTION_ID not configured")

        # Use provided number or default
        from_num = from_number or self.telnyx_number
        if not from_num:
            raise ValueError("No from_number provided and TELNYX_PHONE_NUMBER not configured")

        # Build the request
        url = f"{self.BASE_URL}/calls"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Build call payload
        payload = {
            "to": to,
            "from": from_num,
            "connection_id": self.connection_id,
            "webhook_url": webhook_url or self.webhook_url,
            "webhook_url_method": "POST",
            "timeout_secs": 60,
            "timeout_limit_secs": 600,  # 10 minutes max
        }

        # Enable answering machine detection
        if detect_machine:
            payload["answering_machine_detection"] = "detect"
            payload["answering_machine_detection_config"] = {
                "total_analysis_time_millis": 5000,
                "after_greeting_silence_millis": 1000,
                "between_words_silence_millis": 100,
                "greeting_duration_millis": 1500,
                "initial_silence_millis": 1800,
                "maximum_number_of_words": 3,
                "maximum_word_length_millis": 2000,
                "silence_threshold": 512,
                "greeting_total_analysis_time_millis": 7500,
                "greeting_silence_duration_millis": 2000,
            }

        # Add client state for tracking
        client_state = {
            "script": script,
            "property_id": property_id,
            "questions": questions or [],
            "recording_enabled": record_call,
        }
        import base64
        payload["client_state"] = base64.b64encode(
            json.dumps(client_state).encode()
        ).decode()

        # Make the request
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # Extract call IDs
        call_data = data.get("data", {})
        return {
            "call_id": call_data.get("call_control_id"),
            "call_session_id": call_data.get("call_session_id"),
            "call_leg_id": call_data.get("call_leg_id"),
            "status": "initiated",
            "provider": "telnyx",
            "to": to,
            "from": from_num,
        }

    async def get_call_status(self, call_control_id: str) -> Dict[str, Any]:
        """
        Get the status of a call using its call_control_id.

        Args:
            call_control_id: The call control ID from create_call

        Returns:
            Dict with status, duration, recording_url, transcript
        """
        if not self.api_key:
            raise ValueError("TELNYX_API_KEY not configured")

        url = f"{self.BASE_URL}/calls/{call_control_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        call_data = data.get("data", {})

        # Map Telnyx states to our status
        state = call_data.get("state", "unknown")
        is_alive = call_data.get("is_alive", False)

        if is_alive:
            status = "in_progress"
        elif state in ["completed", "hung_up"]:
            status = "completed"
        elif state in ["failed", "error"]:
            status = "failed"
        elif state == "no_answer":
            status = "no_answer"
        else:
            status = state

        return {
            "call_id": call_control_id,
            "status": status,
            "state": state,
            "is_alive": is_alive,
            "duration_seconds": call_data.get("call_duration", 0),
            "start_time": call_data.get("start_time"),
            "end_time": call_data.get("end_time"),
            "recording_id": call_data.get("recording_id"),
            "recording_enabled": call_data.get("recording_enabled", False),
            "client_state": call_data.get("client_state"),
        }

    async def hangup_call(self, call_control_id: str) -> Dict[str, Any]:
        """
        Hang up an active call.

        Args:
            call_control_id: The call control ID

        Returns:
            Dict with result
        """
        if not self.api_key:
            raise ValueError("TELNYX_API_KEY not configured")

        url = f"{self.BASE_URL}/calls/{call_control_id}/actions/hangup"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json={})
            response.raise_for_status()
            data = response.json()

        return {
            "call_id": call_control_id,
            "action": "hangup",
            "result": data.get("result", "success"),
        }

    async def speak_text(
        self,
        call_control_id: str,
        text: str,
        language: str = "en-US",
        voice: str = "female",
    ) -> Dict[str, Any]:
        """
        Speak text to the call using text-to-speech.

        Args:
            call_control_id: The call control ID
            text: Text to speak
            language: Language code (e.g., "en-US", "es-US")
            voice: Voice type ("male", "female")

        Returns:
            Dict with result
        """
        if not self.api_key:
            raise ValueError("TELNYX_API_KEY not configured")

        url = f"{self.BASE_URL}/calls/{call_control_id}/actions/speak"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "text": text,
            "language": language,
            "voice": voice,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        return {
            "call_id": call_control_id,
            "action": "speak",
            "result": data.get("result", "success"),
        }

    async def gather_audio(
        self,
        call_control_id: str,
        prompt: str,
        max_digits: int = 10,
        timeout_secs: int = 30,
    ) -> Dict[str, Any]:
        """
        Gather audio input (DTMF or speech) from the call.

        Args:
            call_control_id: The call control ID
            prompt: Prompt text to speak before gathering
            max_digits: Maximum number of DTMF digits to collect
            timeout_secs: Timeout in seconds

        Returns:
            Dict with result and collected digits/text
        """
        if not self.api_key:
            raise ValueError("TELNYX_API_KEY not configured")

        url = f"{self.BASE_URL}/calls/{call_control_id}/actions/gather"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "audio_url": None,  # Use TTS instead
            "prompt": prompt,
            "maximum_digits": max_digits,
            "timeout_secs": timeout_secs,
            "inter_digit_timeout_secs": 5,
            "terminator": "#",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        return {
            "call_id": call_control_id,
            "action": "gather",
            "result": data.get("result", "success"),
        }

    async def get_recording(self, recording_id: str) -> Dict[str, Any]:
        """
        Get a call recording by ID.

        Args:
            recording_id: The recording ID

        Returns:
            Dict with download URL and metadata
        """
        if not self.api_key:
            raise ValueError("TELNYX_API_KEY not configured")

        url = f"{self.BASE_URL}/recordings/{recording_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        recording_data = data.get("data", {})
        return {
            "recording_id": recording_id,
            "download_url": recording_data.get("download_url"),
            "content_type": recording_data.get("content_type"),
            "size_bytes": recording_data.get("size_bytes"),
            "created_at": recording_data.get("created_at"),
        }

    async def list_phone_numbers(
        self,
        limit: int = 20,
        status: str = "active",
    ) -> List[Dict[str, Any]]:
        """
        List available phone numbers in the Telnyx account.

        Args:
            limit: Maximum number of results
            status: Filter by status ("active", "reserved", etc.)

        Returns:
            List of phone number objects
        """
        if not self.api_key:
            raise ValueError("TELNYX_API_KEY not configured")

        url = f"{self.BASE_URL}/phone_numbers"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        params = {
            "page[size]": limit,
            "filter[status]": status,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        numbers = []
        for item in data.get("data", []):
            numbers.append({
                "phone_number": item.get("phone_number"),
                "status": item.get("status"),
                "country_code": item.get("country_code"),
                "type": item.get("type"),
            })

        return numbers


# Singleton instance
_telnyx_service = None


def get_telnyx_service() -> TelnyxService:
    """Get or create the Telnyx service singleton."""
    global _telnyx_service
    if _telnyx_service is None:
        _telnyx_service = TelnyxService()
    return _telnyx_service
