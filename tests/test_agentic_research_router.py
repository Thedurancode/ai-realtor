import app.routers.research.agentic_research as agentic_router_module


def test_get_agentic_property_enrichment_status_success(client, agent, agent_headers, monkeypatch):
    def fake_get_property_enrichment_status(db, property_id: int, max_age_hours: int | None = None):
        assert property_id == 42
        assert max_age_hours == 168
        return {
            "has_crm_property_match": True,
            "has_skip_trace_owner": True,
            "has_zillow_enrichment": True,
            "is_enriched": True,
            "is_fresh": True,
            "age_hours": 2.0,
            "max_age_hours": 168,
            "matched_property_id": 7,
            "skip_trace_id": 11,
            "zillow_enrichment_id": 13,
            "missing": [],
            "last_enriched_at": "2026-02-06T19:00:00+00:00",
        }

    monkeypatch.setattr(
        agentic_router_module.agentic_research_service,
        "get_property_enrichment_status",
        fake_get_property_enrichment_status,
    )

    response = client.get("/agentic/properties/42/enrichment-status?max_age_hours=168", headers=agent_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["property_id"] == 42
    assert body["enrichment_status"]["is_enriched"] is True
    assert body["enrichment_status"]["is_fresh"] is True
    assert body["enrichment_status"]["max_age_hours"] == 168


def test_get_agentic_property_enrichment_status_not_found(client, agent, agent_headers, monkeypatch):
    def fake_get_property_enrichment_status(db, property_id: int, max_age_hours: int | None = None):
        return None

    monkeypatch.setattr(
        agentic_router_module.agentic_research_service,
        "get_property_enrichment_status",
        fake_get_property_enrichment_status,
    )

    response = client.get("/agentic/properties/999999/enrichment-status", headers=agent_headers)
    assert response.status_code == 404
    body = response.json()
    assert "not found" in body.get("message", body.get("detail", "")).lower()
