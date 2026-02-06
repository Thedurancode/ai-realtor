from app.config import settings
from app.services.agentic.providers import (
    ExaSearchProvider,
    StubSearchProvider,
    build_search_provider_from_settings,
)


def test_provider_falls_back_to_stub_when_no_key():
    previous = settings.exa_api_key
    try:
        settings.exa_api_key = ""
        provider = build_search_provider_from_settings()
        assert isinstance(provider, StubSearchProvider)
    finally:
        settings.exa_api_key = previous


def test_provider_uses_exa_when_key_present():
    previous = settings.exa_api_key
    try:
        settings.exa_api_key = "test-key"
        provider = build_search_provider_from_settings()
        assert isinstance(provider, ExaSearchProvider)
    finally:
        settings.exa_api_key = previous
