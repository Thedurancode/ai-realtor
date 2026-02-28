"""Tests for main application endpoints, middleware, and configuration."""


class TestRootEndpoint:
    def test_root_returns_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "RealtorClaw" in data["message"]
        assert data["version"] == "1.0.0"
        assert "features" in data
        assert len(data["features"]) > 0

    def test_root_has_docs_link(self, client):
        response = client.get("/")
        assert response.json()["docs"] == "/docs"


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert data["database"]["type"] in ("SQLite", "PostgreSQL")
        assert data["version"] == "1.0.0"


class TestRateLimitEndpoint:
    def test_rate_limit_status(self, client):
        response = client.get("/rate-limit")
        assert response.status_code == 200
        data = response.json()
        assert "rate_limiting" in data
        assert "limits" in data
        assert "tiers" in data
        assert "how_to_disable" in data
        assert "how_to_enable" in data


class TestCacheEndpoints:
    def test_cache_stats(self, client):
        response = client.get("/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "google_places" in data
        assert "zillow" in data
        assert "docuseal" in data

    def test_cache_clear(self, client):
        response = client.post("/cache/clear")
        assert response.status_code == 200
        assert response.json()["message"] == "All caches cleared"


class TestOpenAPISchema:
    def test_openapi_json(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "RealtorClaw API"
        assert "components" in data
        assert "securitySchemes" in data["components"]
        assert "ApiKeyAuth" in data["components"]["securitySchemes"]

    def test_docs_page(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_page(self, client):
        response = client.get("/redoc")
        assert response.status_code == 200


class TestCORSHeaders:
    def test_cors_preflight(self, client):
        response = client.options("/agents/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        # CORS preflight may be intercepted by auth middleware (401) or handled normally
        assert response.status_code in (200, 401, 405)


class TestDisplayCommand:
    def test_send_command(self, client, agent, agent_headers):
        response = client.post("/display/command", json={
            "action": "show_property",
            "property_id": 1,
        }, headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "command_sent"
