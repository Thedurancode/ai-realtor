"""
Property Resolver Helper - FastAPI dependency for resolving properties by address/ID
"""
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.utils.property_resolver import resolve_property, resolve_property_list, format_property_match


async def get_property_from_identifier(
    identifier: str,
    request: Request,
    require_single: bool = True
):
    """
    FastAPI dependency to resolve a property from any identifier (ID, address, city)

    Args:
        identifier: Property ID, address, or city
        request: FastAPI request (contains agent_id from auth middleware)
        require_single: If True, raises 404 if multiple matches found

    Returns:
        Property object

    Raises:
        404: Property not found
        400: Multiple matches found (when require_single=True)
    """
    db = SessionLocal()
    try:
        agent_id = request.state.agent_id

        # Try to find single match
        property = resolve_property(db, identifier, agent_id)

        if property:
            return property

        # No single match - check for multiple matches
        matches = resolve_property_list(db, identifier, agent_id)

        if require_single:
            if len(matches) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Property not found: '{identifier}'. Try being more specific or use the property ID."
                )
            elif len(matches) == 1:
                return matches[0]
            else:
                # Multiple matches - return formatted options
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "multiple_matches",
                        "message": f"Found {len(matches)} properties matching '{identifier}'. Please be more specific.",
                        "matches": [format_property_match(p) for p in matches[:5]]
                    }
                )
        else:
            # Return all matches (for list endpoints)
            return matches

    finally:
        db.close()


def get_agent_id_from_request(request: Request) -> int:
    """Extract agent_id from authenticated request"""
    agent_id = getattr(request.state, 'agent_id', None)
    if not agent_id:
        raise HTTPException(
            status_code=401,
            detail="Agent authentication required"
        )
    return agent_id
