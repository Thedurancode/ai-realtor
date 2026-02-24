"""
Setup Wizard API Router

Provides endpoints for first-time setup and configuration of AI Realtor platform.
Allows users to configure environment variables via a web interface instead of
manually editing .env files.
"""

import os
import json
import subprocess
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/setup", tags=["setup"])


# =============================================================================
# Models
# =============================================================================

class SetupStatusResponse(BaseModel):
    """Response model for setup status check"""
    configured: bool
    values: Dict[str, str]
    missing_required: List[str]
    missing_optional: List[str]


class ValidateRequest(BaseModel):
    """Request model for API key validation"""
    key: str
    value: str


class ValidateResponse(BaseModel):
    """Response model for API key validation"""
    valid: bool
    error: Optional[str] = None
    service: Optional[str] = None


class SaveRequest(BaseModel):
    """Request model for saving configuration"""
    values: Dict[str, str]


class SaveResponse(BaseModel):
    """Response model for save operation"""
    success: bool
    message: str
    restarted: bool = False


# =============================================================================
# Required and Optional Environment Variables
# =============================================================================

REQUIRED_ENV_VARS = [
    'GOOGLE_PLACES_API_KEY',
    'RAPIDAPI_KEY',
    'DOCUSEAL_API_KEY',
    'TELEGRAM_BOT_TOKEN',
    'ZHIPU_API_KEY',
]

OPTIONAL_ENV_VARS = [
    'ANTHROPIC_API_KEY',
    'VAPI_API_KEY',
    'ELEVENLABS_API_KEY',
    'RESEND_API_KEY',
    'EXA_API_KEY',
]

ALL_ENV_VARS = REQUIRED_ENV_VARS + OPTIONAL_ENV_VARS


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status():
    """
    Check if platform is configured and ready.

    Returns:
        - configured: True if all required vars are set
        - values: Current environment variable values (masked)
        - missing_required: List of missing required vars
        - missing_optional: List of missing optional vars
    """
    # Get current environment values
    values = {}
    for key in ALL_ENV_VARS:
        value = os.getenv(key, '')
        # Mask the value for security (show first 8 and last 4 chars)
        if value and len(value) > 12:
            values[key] = f"{value[:8]}...{value[-4:]}"
        elif value:
            values[key] = value
        else:
            values[key] = ''

    # Check which required vars are missing
    missing_required = [key for key in REQUIRED_ENV_VARS if not os.getenv(key)]
    missing_optional = [key for key in OPTIONAL_ENV_VARS if not os.getenv(key)]

    # Platform is configured if all required vars are set
    configured = len(missing_required) == 0

    return SetupStatusResponse(
        configured=configured,
        values=values,
        missing_required=missing_required,
        missing_optional=missing_optional
    )


@router.post("/validate", response_model=ValidateResponse)
async def validate_api_key(request: ValidateRequest):
    """
    Validate an API key by testing it against the respective service.

    Supports validation for:
    - Google Places API
    - RapidAPI (Zillow/Skip Trace)
    - DocuSeal
    - Telegram Bot
    - Zhipu AI
    - Anthropic Claude
    - VAPI
    - ElevenLabs
    - Resend
    - Exa AI

    Returns:
        - valid: True if key is valid
        - error: Error message if validation failed
        - service: Service name that was validated
    """
    key = request.key
    value = request.value.strip()

    if not value:
        return ValidateResponse(
            valid=False,
            error="API key is required",
            service=key
        )

    try:
        # Google Places API
        if key == 'GOOGLE_PLACES_API_KEY':
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/place/autocomplete/json",
                    params={
                        "input": "123 Main St",
                        "key": value
                    }
                )

                data = response.json()

                if "error_message" in data:
                    return ValidateResponse(
                        valid=False,
                        error=data.get("error_message", "Invalid API key"),
                        service="Google Places API"
                    )

                if data.get("status") == "OK" or data.get("status") == "ZERO_RESULTS":
                    return ValidateResponse(
                        valid=True,
                        service="Google Places API"
                    )

                return ValidateResponse(
                    valid=False,
                    error=f"Unexpected response: {data.get('status')}",
                    service="Google Places API"
                )

        # RapidAPI (Test with Zillow)
        elif key == 'RAPIDAPI_KEY':
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://private-zillow.p.rapidapi.com/listings",
                    params={"address": "123 Main St"},
                    headers={
                        "X-RapidAPI-Key": value,
                        "X-RapidAPI-Host": "private-zillow.p.rapidapi.com"
                    }
                )

                if response.status_code == 200:
                    return ValidateResponse(
                        valid=True,
                        service="RapidAPI (Zillow)"
                    )
                elif response.status_code == 401 or response.status_code == 403:
                    return ValidateResponse(
                        valid=False,
                        error="Invalid RapidAPI key or subscription expired",
                        service="RapidAPI"
                    )
                else:
                    return ValidateResponse(
                        valid=False,
                        error=f"HTTP {response.status_code}",
                        service="RapidAPI"
                    )

        # DocuSeal API
        elif key == 'DOCUSEAL_API_KEY':
            docuseal_url = os.getenv('DOCUSEAL_API_URL', 'https://api.docuseal.com')

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{docuseal_url}/templates",
                    headers={"X-Auth-Token": value}
                )

                if response.status_code == 200:
                    return ValidateResponse(
                        valid=True,
                        service="DocuSeal"
                    )
                elif response.status_code == 401:
                    return ValidateResponse(
                        valid=False,
                        error="Invalid DocuSeal API key",
                        service="DocuSeal"
                    )
                else:
                    return ValidateResponse(
                        valid=False,
                        error=f"HTTP {response.status_code}",
                        service="DocuSeal"
                    )

        # Telegram Bot Token
        elif key == 'TELEGRAM_BOT_TOKEN':
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://api.telegram.org/bot{value}/getMe"
                )

                data = response.json()

                if data.get("ok"):
                    return ValidateResponse(
                        valid=True,
                        service="Telegram Bot"
                    )
                else:
                    return ValidateResponse(
                        valid=False,
                        error="Invalid Telegram bot token",
                        service="Telegram"
                    )

        # Zhipu AI
        elif key == 'ZHIPU_API_KEY':
            # Test with a simple completion request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                    headers={
                        "Authorization": f"Bearer {value}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "glm-4-flash",
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 1
                    }
                )

                if response.status_code == 200:
                    return ValidateResponse(
                        valid=True,
                        service="Zhipu AI"
                    )
                elif response.status_code == 401:
                    return ValidateResponse(
                        valid=False,
                        error="Invalid Zhipu AI key",
                        service="Zhipu AI"
                    )
                else:
                    return ValidateResponse(
                        valid=False,
                        error=f"HTTP {response.status_code}",
                        service="Zhipu AI"
                    )

        # Anthropic Claude
        elif key == 'ANTHROPIC_API_KEY':
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": value,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "test"}]
                    }
                )

                if response.status_code == 200:
                    return ValidateResponse(
                        valid=True,
                        service="Anthropic Claude"
                    )
                elif response.status_code == 401:
                    return ValidateResponse(
                        valid=False,
                        error="Invalid Anthropic API key",
                        service="Anthropic"
                    )
                else:
                    return ValidateResponse(
                        valid=False,
                        error=f"HTTP {response.status_code}",
                        service="Anthropic"
                    )

        # VAPI
        elif key == 'VAPI_API_KEY':
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.vapi.run/assistant",
                    headers={"Authorization": f"Bearer {value}"}
                )

                if response.status_code == 200:
                    return ValidateResponse(
                        valid=True,
                        service="VAPI"
                    )
                elif response.status_code == 401:
                    return ValidateResponse(
                        valid=False,
                        error="Invalid VAPI API key",
                        service="VAPI"
                    )
                else:
                    return ValidateResponse(
                        valid=True,  # Accept other status codes as valid (may be permissions issue)
                        service="VAPI"
                    )

        # ElevenLabs
        elif key == 'ELEVENLABS_API_KEY':
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.elevenlabs.io/v1/user",
                    headers={"xi-api-key": value}
                )

                if response.status_code == 200:
                    return ValidateResponse(
                        valid=True,
                        service="ElevenLabs"
                    )
                elif response.status_code == 401:
                    return ValidateResponse(
                        valid=False,
                        error="Invalid ElevenLabs API key",
                        service="ElevenLabs"
                    )
                else:
                    return ValidateResponse(
                        valid=False,
                        error=f"HTTP {response.status_code}",
                        service="ElevenLabs"
                    )

        # Resend
        elif key == 'RESEND_API_KEY':
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {value}"}
                )

                if response.status_code == 200:
                    return ValidateResponse(
                        valid=True,
                        service="Resend"
                    )
                elif response.status_code == 401:
                    return ValidateResponse(
                        valid=False,
                        error="Invalid Resend API key",
                        service="Resend"
                    )
                else:
                    return ValidateResponse(
                        valid=True,  # Accept other status codes
                        service="Resend"
                    )

        # Exa AI
        elif key == 'EXA_API_KEY':
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.exa.ai/search",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": value
                    },
                    json={
                        "query": "test",
                        "numResults": 1
                    }
                )

                if response.status_code == 200:
                    return ValidateResponse(
                        valid=True,
                        service="Exa AI"
                    )
                elif response.status_code == 401:
                    return ValidateResponse(
                        valid=False,
                        error="Invalid Exa AI key",
                        service="Exa AI"
                    )
                else:
                    return ValidateResponse(
                        valid=False,
                        error=f"HTTP {response.status_code}",
                        service="Exa AI"
                    )

        else:
            return ValidateResponse(
                valid=False,
                error=f"Unknown environment variable: {key}",
                service=key
            )

    except httpx.TimeoutException:
        return ValidateResponse(
            valid=False,
            error="Request timed out. Service may be unavailable.",
            service=key
        )
    except Exception as e:
        return ValidateResponse(
            valid=False,
            error=f"Validation error: {str(e)}",
            service=key
        )


@router.post("/save", response_model=SaveResponse)
async def save_configuration(request: SaveRequest):
    """
    Save environment configuration and restart services.

    This endpoint:
    1. Validates all required keys are present
    2. Saves to .env file
    3. Optionally restarts Docker containers
    4. Returns success status

    Returns:
        - success: True if saved successfully
        - message: Status message
        - restarted: True if containers were restarted
    """
    values = request.values

    # Validate all required keys are present
    missing_required = [key for key in REQUIRED_ENV_VARS if not values.get(key)]

    if missing_required:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required keys: {', '.join(missing_required)}"
        )

    try:
        # Determine .env file path
        # In development, use local .env
        # In Docker, use /app/.env
        env_path = os.path.join(os.getcwd(), '.env')

        # If running in Docker, use app directory
        if os.path.exists('/app/.env'):
            env_path = '/app/.env'

        # Read existing .env file to preserve other variables
        existing_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_vars[key] = value

        # Merge new values with existing
        existing_vars.update(values)

        # Write back to .env file
        with open(env_path, 'w') as f:
            for key, value in existing_vars.items():
                f.write(f"{key}={value}\n")

        # Restart services if in Docker
        restarted = False
        if os.path.exists('/.dockerenv'):
            try:
                # Restart AI Realtor container
                subprocess.run(
                    ['docker', 'restart', 'ai-realtor-sqlite'],
                    capture_output=True,
                    timeout=30
                )
                # Restart Nanobot container
                subprocess.run(
                    ['docker', 'restart', 'nanobot-gateway'],
                    capture_output=True,
                    timeout=30
                )
                restarted = True
            except Exception as e:
                print(f"Failed to restart containers: {e}")

        return SaveResponse(
            success=True,
            message="Configuration saved successfully",
            restarted=restarted
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save configuration: {str(e)}"
        )


@router.post("/restart")
async def restart_services():
    """
    Restart all Docker services.

    Useful after configuration changes.
    """
    try:
        if os.path.exists('/.dockerenv'):
            # Restart AI Realtor
            result1 = subprocess.run(
                ['docker', 'restart', 'ai-realtor-sqlite'],
                capture_output=True,
                timeout=30
            )
            # Restart Nanobot
            result2 = subprocess.run(
                ['docker', 'restart', 'nanobot-gateway'],
                capture_output=True,
                timeout=30
            )

            return {
                "success": True,
                "message": "Services restarted successfully",
                "ai_realtor": result1.returncode == 0,
                "nanobot": result2.returncode == 0
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Not running in Docker environment"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart services: {str(e)}"
        )
