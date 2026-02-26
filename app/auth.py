"""API key authentication utilities."""
import hashlib
import hmac
import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent import Agent


def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key. Format: sk_live_<64 hex chars>"""
    return f"sk_live_{secrets.token_hex(32)}"


def verify_api_key(db: Session, api_key: str) -> Agent | None:
    """Look up an agent by API key. Returns None if invalid."""
    key_hash = hash_api_key(api_key)
    return db.query(Agent).filter(Agent.api_key_hash == key_hash).first()


def verify_telnyx_webhook_signature(
    payload: bytes,
    signature: str,
    webhook_secret: Optional[str] = None,
) -> bool:
    """
    Verify Telnyx webhook signature using HMAC-SHA256.

    Telnyx sends a signature in the `Telnyx-Signature` header with the format:
        t=<timestamp>,v1=<signature>

    Args:
        payload: Raw request body as bytes
        signature: Signature header value from Telnyx
        webhook_secret: Telnyx webhook secret (defaults to TELNYX_WEBHOOK_SECRET env var)

    Returns:
        True if signature is valid, False otherwise
    """
    webhook_secret = webhook_secret or os.getenv("TELNYX_WEBHOOK_SECRET")
    if not webhook_secret:
        # No secret configured - skip verification (not recommended for production)
        return True

    if not signature:
        return False

    try:
        # Parse signature header (format: t=<timestamp>,v1=<signature>)
        parts = signature.split(",")
        signature_dict = {}
        for part in parts:
            key, value = part.split("=", 1)
            signature_dict[key] = value

        if "v1" not in signature_dict:
            return False

        expected_signature = signature_dict["v1"]

        # Compute HMAC-SHA256
        computed_hmac = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed_hmac, expected_signature)

    except (ValueError, KeyError):
        return False


async def verify_telnyx_webhook_request(request: Request) -> bool:
    """
    FastAPI dependency to verify Telnyx webhook signatures.

    Usage in endpoint:
        is_valid: bool = Depends(verify_telnyx_webhook_request)

    Raises HTTPException 401 if signature is invalid.
    """
    # Get signature from header
    signature = request.headers.get("Telnyx-Signature") or request.headers.get("telnyx-signature")

    # Get raw body
    body = await request.body()

    # Verify signature
    if not verify_telnyx_webhook_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    return True


# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_agent(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Agent:
    """
    FastAPI dependency to get the current authenticated agent from API key.

    Usage in endpoint:
        current_agent: Agent = Depends(get_current_agent)

    The API key should be provided via Authorization header:
        Authorization: Bearer sk_live_...
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. API key required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = credentials.credentials
    agent = verify_api_key(db, api_key)

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return agent


async def get_current_agent_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[Agent]:
    """
    Optional version of get_current_agent that returns None instead of raising 401.

    Useful for endpoints that have different behavior for authenticated vs anonymous users.
    """
    if credentials is None:
        return None

    api_key = credentials.credentials
    return verify_api_key(db, api_key)
