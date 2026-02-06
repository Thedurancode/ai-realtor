from typing import Any

import httpx

from app.config import settings


class ExaResearchService:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ):
        self.api_key = (api_key if api_key is not None else settings.exa_api_key).strip()
        self.base_url = (base_url if base_url is not None else settings.exa_base_url).rstrip("/")
        self.timeout_seconds = int(timeout_seconds if timeout_seconds is not None else settings.exa_timeout_seconds)

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("EXA_API_KEY is not configured")
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    @staticmethod
    def extract_task_id(payload: dict[str, Any]) -> str | None:
        for key in ("task_id", "taskId", "id", "research_id", "researchId"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def extract_status(payload: dict[str, Any]) -> str | None:
        value = payload.get("status")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @staticmethod
    def build_property_dossier_instructions(
        address: str,
        county: str | None = None,
        strategy: str = "buy&hold",
    ) -> str:
        location = address.strip()
        if county and county.strip():
            location = f"{location}, {county.strip()}"

        plan = strategy.strip() or "buy&hold"
        return (
            f"Create an investor-grade Property Intelligence Dossier for {location}: "
            "include parcel/APN + GIS, current & past owners (3-10 transfers), deed/mortgage "
            "history, liens/judgments/tax status & delinquencies, assessed values & tax trend, "
            "zoning code + plain-English allowed uses (ADU/duplex/multi/STR), "
            "overlays/setbacks/FAR/parking, permit history + open permits, code violations, "
            "flood/fire/other hazard risks, HOA info, neighborhood signals, 5-12 sold comps "
            "with adjustments + value range (low/base/high), 5-12 rent comps + rent range, "
            f"a simple underwriting model for {plan} with best/base/worst scenarios, key red "
            "flags, and a prioritized next-steps checklist; cite links for every major claim "
            "and clearly label unknowns/assumptions."
        )

    async def create_research_task(
        self,
        instructions: str,
        model: str = "exa-research-fast",
    ) -> dict[str, Any]:
        if not instructions.strip():
            raise ValueError("instructions cannot be empty")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/research/v1",
                headers=self._headers(),
                json={
                    "instructions": instructions,
                    "model": model,
                },
                timeout=float(self.timeout_seconds),
            )
            response.raise_for_status()
            return response.json()

    async def get_research_task(self, task_id: str) -> dict[str, Any]:
        if not task_id.strip():
            raise ValueError("task_id cannot be empty")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/research/v1/{task_id.strip()}",
                headers=self._headers(),
                timeout=float(self.timeout_seconds),
            )
            response.raise_for_status()
            return response.json()


exa_research_service = ExaResearchService()
