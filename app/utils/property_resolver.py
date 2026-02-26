"""
Property Resolver - Find properties by address, city, or natural language
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List

from app.models.property import Property
import re


def resolve_property(db: Session, identifier: str, agent_id: int) -> Optional[Property]:
    """
    Resolve a property from various identifier types:
    - Property ID (number)
    - Full address ("123 Main St, New York, NY")
    - Partial address ("123 Main St")
    - City/state ("Miami, FL")
    - Address + city ("Main St, Brooklyn")

    Args:
        db: Database session
        identifier: User input (ID, address, city, etc.)
        agent_id: Agent ID to scope search

    Returns:
        Property object or None
    """
    if not identifier:
        return None

    identifier = identifier.strip()

    # 1. Try direct ID match first
    if identifier.isdigit():
        property = db.query(Property).filter(
            Property.id == int(identifier),
            Property.agent_id == agent_id
        ).first()
        if property:
            return property

    # 2. Try full address match
    properties = db.query(Property).filter(Property.agent_id == agent_id).all()

    # Build searchable strings for each property
    for prop in properties:
        searchable_strings = [
            f"{prop.address}, {prop.city}, {prop.state}".lower(),
            f"{prop.address} {prop.city} {prop.state}".lower(),
            f"{prop.address}, {prop.city}".lower(),
            f"{prop.address}".lower(),
            f"{prop.city}, {prop.state}".lower(),
            f"{prop.city} {prop.state}".lower(),
            f"{prop.city}".lower(),
        ]

        # Check exact match
        for search_str in searchable_strings:
            if identifier.lower() == search_str:
                return prop

        # Check partial match (contains)
        for search_str in searchable_strings:
            if identifier.lower() in search_str and len(identifier) > 5:
                return prop

    # 3. Try fuzzy address match
    # Normalize identifier (remove extra spaces, commas, etc.)
    normalized = re.sub(r'\s+', ' ', identifier.lower().strip(','))

    for prop in properties:
        prop_address = re.sub(r'\s+', ' ', f"{prop.address} {prop.city} {prop.state}".lower())
        if normalized in prop_address or prop_address in normalized:
            return prop

    # 4. Try city/state match
    if ',' in identifier:
        parts = [p.strip().lower() for p in identifier.split(',')]
        for prop in properties:
            if prop.city.lower() in parts[0] and prop.state.lower() in parts[-1]:
                # Return the most recent match
                return prop

    return None


def resolve_property_list(db: Session, identifier: str, agent_id: int) -> List[Property]:
    """
    Resolve multiple properties matching an identifier (for ambiguous queries)
    Returns a list of potential matches
    """
    if not identifier:
        return []

    identifier = identifier.strip().lower()
    properties = db.query(Property).filter(Property.agent_id == agent_id).all()
    matches = []

    for prop in properties:
        searchable_strings = [
            f"{prop.address}, {prop.city}, {prop.state}".lower(),
            f"{prop.address} {prop.city} {prop.state}".lower(),
            f"{prop.address}, {prop.city}".lower(),
            f"{prop.address}".lower(),
            f"{prop.city}, {prop.state}".lower(),
            f"{prop.city} {prop.state}".lower(),
            f"{prop.city}".lower(),
        ]

        for search_str in searchable_strings:
            if identifier in search_str and len(identifier) > 3:
                matches.append(prop)
                break

    return matches


def get_property_identifier(property: Property) -> str:
    """
    Get a human-readable identifier for a property
    Returns the most specific unique identifier
    """
    if property.address:
        return f"{property.address}, {property.city}, {property.state}"
    return f"Property {property.id}"


def format_property_match(property: Property) -> dict:
    """
    Format a property for match confirmation
    """
    return {
        "id": property.id,
        "identifier": f"{property.address}, {property.city}, {property.state}",
        "title": property.title,
        "address": property.address,
        "city": property.city,
        "state": property.state,
        "price": property.price,
        "status": property.status.value if property.status else None
    }
