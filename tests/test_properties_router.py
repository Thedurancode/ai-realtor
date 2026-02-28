"""Tests for the properties router (CRUD + filtering)."""

from unittest.mock import patch, AsyncMock

from app.models.property import PropertyStatus, PropertyType


class TestCreateProperty:
    def test_create_basic(self, client, agent, agent_headers):
        with patch("app.routers.properties.contract_auto_attach_service") as mock_attach, \
             patch("app.routers.properties.run_auto_enrich_pipeline"), \
             patch("app.routers.properties.schedule_compliance_check", new_callable=AsyncMock), \
             patch("app.services.watchlist_service.watchlist_service"):
            mock_attach.auto_attach_contracts.return_value = []
            response = client.post("/properties/", json={
                "title": "New Home",
                "address": "789 Elm St",
                "city": "Testville",
                "state": "NJ",
                "zip_code": "07001",
                "price": 250000,
                "bedrooms": 2,
                "bathrooms": 1.5,
                "agent_id": agent.id,
            }, headers=agent_headers)
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "New Home"
            assert data["price"] == 250000
            assert data["status"] == "new_property"

    def test_create_invalid_agent(self, client, agent, agent_headers):
        response = client.post("/properties/", json={
            "title": "Bad Agent",
            "address": "999 Nowhere",
            "city": "X",
            "state": "XX",
            "zip_code": "00000",
            "price": 100000,
            "agent_id": 99999,
        }, headers=agent_headers)
        assert response.status_code == 404


class TestListProperties:
    def test_list_all(self, client, sample_property, agent_headers):
        response = client.get("/properties/?include_heartbeat=false", headers=agent_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_filter_by_city(self, client, sample_property, agent_headers):
        response = client.get(
            "/properties/?city=Testville&include_heartbeat=false",
            headers=agent_headers,
        )
        assert response.status_code == 200
        for p in response.json():
            assert "testville" in p["city"].lower()

    def test_filter_by_status(self, client, sample_property, agent_headers):
        response = client.get(
            "/properties/?status=new_property&include_heartbeat=false",
            headers=agent_headers,
        )
        assert response.status_code == 200
        for p in response.json():
            assert p["status"] == "new_property"

    def test_filter_by_price_range(self, client, sample_property, agent_headers):
        response = client.get(
            "/properties/?min_price=300000&max_price=400000&include_heartbeat=false",
            headers=agent_headers,
        )
        assert response.status_code == 200
        for p in response.json():
            assert 300000 <= p["price"] <= 400000

    def test_filter_by_bedrooms(self, client, sample_property, agent_headers):
        response = client.get(
            "/properties/?bedrooms=3&include_heartbeat=false",
            headers=agent_headers,
        )
        assert response.status_code == 200
        for p in response.json():
            assert p["bedrooms"] >= 3

    def test_filter_by_agent(self, client, sample_property, agent, agent_headers):
        response = client.get(
            f"/properties/?agent_id={agent.id}&include_heartbeat=false",
            headers=agent_headers,
        )
        assert response.status_code == 200
        for p in response.json():
            assert p["agent_id"] == agent.id

    def test_pagination(self, client, sample_property, agent_headers):
        response = client.get(
            "/properties/?skip=0&limit=1&include_heartbeat=false",
            headers=agent_headers,
        )
        assert response.status_code == 200
        assert len(response.json()) <= 1


class TestGetProperty:
    def test_get_existing(self, client, sample_property, agent_headers):
        response = client.get(
            f"/properties/{sample_property.id}?include_heartbeat=false",
            headers=agent_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_property.id
        assert data["address"] == "123 Test Street"

    def test_get_nonexistent(self, client, agent, agent_headers):
        response = client.get("/properties/99999?include_heartbeat=false", headers=agent_headers)
        assert response.status_code == 404


class TestUpdateProperty:
    def test_update_price(self, client, sample_property, agent_headers):
        with patch("app.services.notification_service.notification_service") as mock_notif, \
             patch("app.services.property_recap_service.regenerate_recap_background"):
            mock_notif.notify_property_price_change = AsyncMock()
            response = client.patch(f"/properties/{sample_property.id}", json={
                "price": 375000,
            }, headers=agent_headers)
            assert response.status_code == 200
            assert response.json()["price"] == 375000

    def test_update_status(self, client, sample_property, agent_headers):
        with patch("app.services.notification_service.notification_service") as mock_notif, \
             patch("app.services.property_recap_service.regenerate_recap_background"):
            mock_notif.notify_property_status_change = AsyncMock()
            response = client.patch(f"/properties/{sample_property.id}", json={
                "status": "enriched",
            }, headers=agent_headers)
            assert response.status_code == 200
            assert response.json()["status"] == "enriched"

    def test_update_nonexistent(self, client, agent, agent_headers):
        response = client.patch("/properties/99999", json={
            "price": 100,
        }, headers=agent_headers)
        assert response.status_code == 404

    def test_update_invalid_agent_id(self, client, sample_property, agent_headers):
        with patch("app.services.notification_service.notification_service"), \
             patch("app.services.property_recap_service.regenerate_recap_background"):
            response = client.patch(f"/properties/{sample_property.id}", json={
                "agent_id": 99999,
            }, headers=agent_headers)
            assert response.status_code == 404


class TestDeleteProperty:
    def test_delete_existing(self, client, sample_property, agent_headers):
        response = client.delete(
            f"/properties/{sample_property.id}", headers=agent_headers
        )
        assert response.status_code == 204

    def test_delete_nonexistent(self, client, agent, agent_headers):
        response = client.delete("/properties/99999", headers=agent_headers)
        assert response.status_code == 404


class TestPropertyDealType:
    def test_set_deal_type(self, client, sample_property, agent_headers):
        with patch("app.routers.properties.apply_deal_type") as mock_apply:
            mock_apply.return_value = {"success": True, "deal_type": "TRADITIONAL"}
            response = client.post(
                f"/properties/{sample_property.id}/set-deal-type?deal_type_name=TRADITIONAL",
                headers=agent_headers,
            )
            assert response.status_code == 200

    def test_set_deal_type_nonexistent_property(self, client, agent, agent_headers):
        response = client.post(
            "/properties/99999/set-deal-type?deal_type_name=TRADITIONAL",
            headers=agent_headers,
        )
        assert response.status_code == 404

    def test_get_deal_status(self, client, sample_property, agent_headers):
        with patch("app.routers.properties.get_deal_type_summary") as mock_summary:
            mock_summary.return_value = {"progress": 0.5}
            response = client.get(
                f"/properties/{sample_property.id}/deal-status",
                headers=agent_headers,
            )
            assert response.status_code == 200
