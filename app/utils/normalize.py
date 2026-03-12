"""Data normalization utilities for scraped real estate data.

Scraped data from Zillow, Redfin, etc. is inherently messy — None values,
inconsistent types, missing fields. This module provides utilities to clean
data at the boundary between scraping and storage.
"""
from typing import Any, Optional, TypeVar
from decimal import Decimal, InvalidOperation

T = TypeVar("T")


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Convert any value to float, returning default on failure."""
    if value is None:
        return default
    try:
        result = float(str(value).replace(",", "").replace("$", "").strip())
        return result
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Convert any value to int, returning default on failure."""
    if value is None:
        return default
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """Convert any value to stripped string."""
    if value is None:
        return default
    return str(value).strip()


def safe_decimal(value: Any, default: Optional[Decimal] = None) -> Optional[Decimal]:
    """Convert any value to Decimal."""
    if value is None:
        return default
    try:
        cleaned = str(value).replace(",", "").replace("$", "").strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError, TypeError):
        return default


def safe_format(template: str, **kwargs: Any) -> str:
    """Format a string template, replacing None values with 'N/A'.

    Prevents format string errors when scraped data contains None values.
    """
    cleaned = {k: (v if v is not None else "N/A") for k, v in kwargs.items()}
    return template.format(**cleaned)


def normalize_price(value: Any) -> Optional[float]:
    """Normalize a price value from various formats ($1,234,567 or 1234567)."""
    return safe_float(value)


def normalize_sqft(value: Any) -> Optional[int]:
    """Normalize square footage from various formats."""
    return safe_int(value)


def normalize_address(
    street: Any = None,
    city: Any = None,
    state: Any = None,
    zipcode: Any = None,
) -> dict[str, str]:
    """Normalize address components."""
    return {
        "street": safe_str(street),
        "city": safe_str(city),
        "state": safe_str(state).upper()[:2] if state else "",
        "zipcode": safe_str(zipcode)[:10],
    }
