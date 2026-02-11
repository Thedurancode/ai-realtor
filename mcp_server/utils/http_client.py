"""Shared HTTP client configuration."""
import os
import requests

API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://localhost:8000")


def api_get(path: str, **kwargs):
    """GET request to the backend API."""
    return requests.get(f"{API_BASE_URL}{path}", **kwargs)


def api_post(path: str, **kwargs):
    """POST request to the backend API."""
    return requests.post(f"{API_BASE_URL}{path}", **kwargs)


def api_patch(path: str, **kwargs):
    """PATCH request to the backend API."""
    return requests.patch(f"{API_BASE_URL}{path}", **kwargs)


def api_put(path: str, **kwargs):
    """PUT request to the backend API."""
    return requests.put(f"{API_BASE_URL}{path}", **kwargs)


def api_delete(path: str, **kwargs):
    """DELETE request to the backend API."""
    return requests.delete(f"{API_BASE_URL}{path}", **kwargs)
