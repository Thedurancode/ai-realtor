"""API key authentication utilities."""
import hashlib
import secrets

from sqlalchemy.orm import Session

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
