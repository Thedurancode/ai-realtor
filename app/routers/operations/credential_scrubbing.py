"""Credential Scrubbing API router.

Provides endpoints for testing and using credential scrubbing functionality.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union

from app.services.credential_scrubbing import scrub_credentials, CredentialScrubber


router = APIRouter(prefix="/scrub", tags=["Credential Scrubbing"])


# Pydantic models
class ScrubTextRequest(BaseModel):
    """Request to scrub text."""
    text: str = Field(..., description="Text to scrub")
    keep_chars: int = Field(0, description="Number of leading/trailing chars to keep")
    scrub_email: bool = Field(True, description="Whether to scrub email addresses")
    scrub_phone: bool = Field(True, description="Whether to scrub phone numbers")
    scrub_ip: bool = Field(True, description="Whether to scrub IP addresses")


class ScrubJsonRequest(BaseModel):
    """Request to scrub JSON."""
    data: Dict[str, Any] = Field(..., description="JSON data to scrub")
    keep_chars: int = Field(0, description="Number of leading/trailing chars to keep")
    scrub_email: bool = Field(True, description="Whether to scrub email addresses")
    scrub_phone: bool = Field(True, description="Whether to scrub phone numbers")
    scrub_ip: bool = Field(True, description="Whether to scrub IP addresses")


class ScrubResponse(BaseModel):
    """Response from scrubbing operation."""
    original: str
    scrubbed: str
    patterns_found: int


@router.post("/text")
async def scrub_text(request: ScrubTextRequest):
    """Scrub sensitive information from text.

    Automatically detects and redacts:
    - API keys (Anthropic, OpenAI, AWS, Google)
    - Passwords
    - Tokens
    - SSNs
    - Credit cards
    - Email addresses (optional)
    - Phone numbers (optional)
    - IP addresses (optional)

    Returns the scrubbed text.
    """
    scrubber = CredentialScrubber(config={
        "keep_chars": request.keep_chars,
        "scrub_email": request.scrub_email,
        "scrub_phone": request.scrub_phone,
        "scrub_ip": request.scrub_ip
    })

    scrubbed = scrubber.scrub(request.text)

    # Count how many times redaction string appears
    patterns_found = scrubbed.count(scrubber.redaction_string)

    return {
        "original": request.text,
        "scrubbed": scrubbed,
        "patterns_found": patterns_found
    }


@router.post("/json")
async def scrub_json(request: ScrubJsonRequest):
    """Scrub sensitive information from JSON data.

    Automatically redacts sensitive values (passwords, API keys, tokens, etc.)
    while preserving JSON structure.
    """
    scrubber = CredentialScrubber(config={
        "keep_chars": request.keep_chars,
        "scrub_email": request.scrub_email,
        "scrub_phone": request.scrub_phone,
        "scrub_ip": request.scrub_ip
    })

    scrubbed = scrubber.scrub_dict(request.data)

    # Count redactions
    def count_redactions(data):
        if isinstance(data, str):
            return 1 if data == scrubber.redaction_string else 0
        elif isinstance(data, dict):
            return sum(count_redactions(v) for v in data.values())
        elif isinstance(data, list):
            return sum(count_redactions(item) for item in data)
        else:
            return 0

    patterns_found = count_redactions(scrubbed)

    return {
        "original": request.data,
        "scrubbed": scrubbed,
        "patterns_found": patterns_found
    }


@router.post("/test")
async def test_scrubbing():
    """Test credential scrubbing with sample data.

    Returns before/after examples for all supported patterns.
    """
    test_cases = [
        {
            "name": "Anthropic API Key",
            "input": "API key: sk-ant-api123-4567890abcdef",
            "expected": "API key: ***REDACTED***"
        },
        {
            "name": "OpenAI API Key",
            "input": "OpenAI key: sk-1234567890abcdefghijklmno",
            "expected": "OpenAI key: ***REDACTED***"
        },
        {
            "name": "AWS Access Key",
            "input": "AWS key: AKIA1234567890ABCDEFGHI",
            "expected": "AWS key: ***REDACTED***"
        },
        {
            "name": "Password (JSON)",
            "input": '{"password": "mySecretPass123"}',
            "expected": '{"password": "***REDACTED***"}'
        },
        {
            "name": "Bearer Token",
            "input": "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "expected": "Authorization: Bearer ***REDACTED***"
        },
        {
            "name": "SSN (with dashes)",
            "input": "SSN: 123-45-6789",
            "expected": "SSN: ***REDACTED***"
        },
        {
            "name": "Credit Card",
            "input": "Card: 1234 5678 9012 3456",
            "expected": "Card: ***REDACTED***"
        },
        {
            "name": "Email Address",
            "input": "Contact: agent@example.com",
            "expected": "Contact: age***REDACTED***"
        },
        {
            "name": "Phone Number",
            "input": "Phone: +1-415-555-1234",
            "expected": "Phone: ***REDACTED***"
        },
        {
            "name": "IP Address",
            "input": "Server: 192.168.1.1",
            "expected": "Server: ***REDACTED***"
        }
    ]

    results = []
    for test_case in test_cases:
        scrubbed = scrub_credentials(test_case["input"])
        results.append({
            "name": test_case["name"],
            "input": test_case["input"],
            "output": scrubbed,
            "expected": test_case["expected"],
            "passed": scrubbed == test_case["expected"]
        })

    return {
        "total_tests": len(test_cases),
        "passed": sum(1 for r in results if r["passed"]),
        "results": results
    }


@router.get("/patterns")
async def get_supported_patterns():
    """Get list of all supported credential patterns."""
    return {
        "api_keys": [
            "Anthropic Claude: sk-ant-api123-...",
            "OpenAI: sk-...",
            "AWS Access Key: AKIA...",
            "Google OAuth: ya29....",
            "Generic: api_key=..., key=..., secret=..."
        ],
        "passwords": [
            "JSON: password\":\"...\"",
            "Form: password=...",
            "Short: pass=..."
        ],
        "tokens": [
            "Bearer token: Bearer ...",
            "JSON token: token\":\"...\"",
            "JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        ],
        "ssns": [
            "With dashes: 123-45-6789",
            "With spaces: 123 45 6789",
            "Plain: 123456789"
        ],
        "credit_cards": [
            "With spaces: 1234 5678 9012 3456",
            "With dashes: 1234-5678-9012-3456",
            "Plain: 1234567890123456"
        ],
        "emails": [
            "Standard: user@example.com",
            "Subdomain: user@mail.example.com"
        ],
        "phones": [
            "International: +1-415-555-1234",
            "With parentheses: (415) 555-1234",
            "Standard: 415-555-1234"
        ],
        "ip_addresses": [
            "IPv4: 192.168.1.1",
            "Private: 10.0.0.1"
        ]
    }


@router.get("/config")
async def get_scrubber_config():
    """Get current scrubber configuration."""
    scrubber = CredentialScrubber()

    return {
        "redaction_string": scrubber.redaction_string,
        "keep_chars": scrubber.keep_chars,
        "scrub_email": scrubber.scrub_email,
        "scrub_phone": scrubber.scrub_phone,
        "scrub_ip": scrubber.scrub_ip,
        "custom_patterns": scrubber.custom_patterns
    }
