"""API key authentication utilities."""
import hashlib
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
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
