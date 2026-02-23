"""ServiceContext — lightweight bag of config shared across all workers."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.agentic.providers import PortalFetcher, SearchProvider


@dataclass
class ServiceContext:
    search_provider: SearchProvider
    portal_fetcher: PortalFetcher
    urban_radius_cities: set[str]
    high_trust_domains: set[str]
    medium_trust_domains: set[str]
