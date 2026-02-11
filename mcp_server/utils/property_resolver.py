"""Property resolution utilities for voice-friendly tool arguments."""
from .voice import normalize_voice_query


def find_property_by_address(address_query: str) -> int:
    """Find a single property by address, city, or state. Raises ValueError with options if multiple matches."""
    from app.database import SessionLocal
    from app.models.property import Property
    from sqlalchemy import func, or_

    db = SessionLocal()
    try:
        query_variations = normalize_voice_query(address_query)
        # Build search terms: full variations + individual words (3+ chars)
        search_terms = set(query_variations)
        for var in query_variations:
            for word in var.split():
                if len(word) >= 3:
                    search_terms.add(word)

        # Remove overly generic terms that match everything
        generic_terms = {'the', 'property', 'house', 'home', 'this', 'that', 'for', 'and'}
        search_terms = search_terms - generic_terms

        if not search_terms:
            raise ValueError(f"No searchable terms in: {address_query}")

        filters = []
        for term in search_terms:
            filters.append(func.lower(Property.address).contains(term))
            filters.append(func.lower(Property.city).contains(term))
            filters.append(func.lower(Property.state).contains(term))
        properties = db.query(Property).filter(or_(*filters)).all()

        if not properties:
            from difflib import get_close_matches
            all_props = db.query(Property).limit(100).all()
            all_labels = [
                f"{p.address}, {p.city or ''}, {p.state or ''}".lower().strip(", ")
                for p in all_props
            ]
            matches = get_close_matches(query_variations[0], all_labels, n=3, cutoff=0.4)
            if matches:
                raise ValueError(f"No exact match for '{address_query}'. Did you mean: {', '.join(matches)}?")
            raise ValueError(f"No property found matching: {address_query}")

        if len(properties) > 1:
            # Score each property by how many search terms match
            scored = []
            for p in properties:
                full_text = f"{(p.address or '').lower()} {(p.city or '').lower()} {(p.state or '').lower()}"
                score = sum(1 for term in search_terms if term in full_text)
                # Bonus for address match (more specific than state)
                addr_score = sum(1 for term in search_terms if term in (p.address or '').lower())
                city_score = sum(1 for term in search_terms if term in (p.city or '').lower())
                scored.append((p, score * 10 + addr_score * 5 + city_score * 3))

            scored.sort(key=lambda x: x[1], reverse=True)

            # If top result has a clearly higher score, use it
            if scored[0][1] > scored[1][1]:
                return scored[0][0].id

            # Still ambiguous - list options
            listing = "\n".join(
                f"  - Property {p.id}: {p.address}, {p.city or ''}, {p.state or ''}"
                + (f" (${p.price:,.0f})" if p.price else "")
                for p, _ in scored
            )
            raise ValueError(
                f"Found {len(properties)} properties matching '{address_query}'. "
                f"Please specify which one:\n{listing}\n\n"
                f"Try again with the city, state, or property ID to narrow it down."
            )

        return properties[0].id
    finally:
        db.close()


def resolve_property_id(arguments: dict) -> int:
    """Resolve property_id from arguments - supports both ID and address lookup."""
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        raise ValueError("Please provide either a property ID or a property address.")
    return int(property_id)
