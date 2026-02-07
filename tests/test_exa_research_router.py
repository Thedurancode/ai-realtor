from fastapi.testclient import TestClient

import app.routers.exa_research as exa_router_module
from app.main import app


def test_property_dossier_endpoint_builds_and_submits_prompt(monkeypatch):
    captured: dict[str, str] = {}

    async def fake_create_research_task(instructions: str, model: str = "exa-research-fast"):
        captured["instructions"] = instructions
        captured["model"] = model
        return {
            "researchId": "r_test_123",
            "status": "running",
            "instructions": instructions,
            "model": model,
        }

    monkeypatch.setattr(
        exa_router_module.exa_research_service,
        "create_research_task",
        fake_create_research_task,
    )

    client = TestClient(app)
    response = client.post(
        "/exa/research/property-dossier",
        json={
            "address": "141 Throop Ave, New Brunswick, NJ 08901",
            "county": "Middlesex County",
            "strategy": "buy&hold",
            "model": "exa-research-fast",
        },
    )
    assert response.status_code == 200

    body = response.json()
    assert body["task_id"] == "r_test_123"
    assert body["status"] == "running"
    assert "141 Throop Ave, New Brunswick, NJ 08901, Middlesex County" in captured["instructions"]
    assert "underwriting model for buy&hold" in captured["instructions"]
    assert captured["model"] == "exa-research-fast"


def test_subdivision_dossier_endpoint_builds_and_submits_prompt(monkeypatch):
    captured: dict[str, str] = {}

    async def fake_create_research_task(instructions: str, model: str = "exa-research-fast"):
        captured["instructions"] = instructions
        captured["model"] = model
        return {
            "researchId": "r_subdivision_test_123",
            "status": "running",
            "instructions": instructions,
            "model": model,
        }

    monkeypatch.setattr(
        exa_router_module.exa_research_service,
        "create_research_task",
        fake_create_research_task,
    )

    client = TestClient(app)
    response = client.post(
        "/exa/research/subdivision-dossier",
        json={
            "address": "141 Throop Ave, New Brunswick, NJ 08901",
            "county": "Middlesex County",
            "target_strategy": "subdivide and build duplexes",
            "target_lot_count": 3,
            "model": "exa-research-fast",
        },
    )
    assert response.status_code == 200

    body = response.json()
    assert body["task_id"] == "r_subdivision_test_123"
    assert body["status"] == "running"
    assert "Target lot count goal: 3." in captured["instructions"]
    assert "Primary strategy: subdivide and build duplexes." in captured["instructions"]
    assert captured["model"] == "exa-research-fast"
