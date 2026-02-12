"""Shared HTTP client configuration."""
import os
import requests

API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("MCP_API_KEY", "")


def _default_headers() -> dict:
    """Build default headers including API key if set."""
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


def api_get(path: str, **kwargs):
    """GET request to the backend API."""
    headers = {**_default_headers(), **kwargs.pop("headers", {})}
    return requests.get(f"{API_BASE_URL}{path}", headers=headers, **kwargs)


def api_post(path: str, **kwargs):
    """POST request to the backend API."""
    headers = {**_default_headers(), **kwargs.pop("headers", {})}
    return requests.post(f"{API_BASE_URL}{path}", headers=headers, **kwargs)


def api_patch(path: str, **kwargs):
    """PATCH request to the backend API."""
    headers = {**_default_headers(), **kwargs.pop("headers", {})}
    return requests.patch(f"{API_BASE_URL}{path}", headers=headers, **kwargs)


def api_put(path: str, **kwargs):
    """PUT request to the backend API."""
    headers = {**_default_headers(), **kwargs.pop("headers", {})}
    return requests.put(f"{API_BASE_URL}{path}", headers=headers, **kwargs)


def api_delete(path: str, **kwargs):
    """DELETE request to the backend API."""
    headers = {**_default_headers(), **kwargs.pop("headers", {})}
    return requests.delete(f"{API_BASE_URL}{path}", headers=headers, **kwargs)
