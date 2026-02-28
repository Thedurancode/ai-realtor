"""Tests for the contacts router (CRUD + voice + search)."""

from unittest.mock import patch, AsyncMock

from app.models.contact import ContactRole


class TestCreateContact:
    def test_create_basic(self, client, sample_property, agent_headers):
        with patch("app.routers.contacts.notification_service") as mock_notif, \
             patch("app.services.property_recap_service.regenerate_recap_background"):
            mock_notif.notify_new_lead = AsyncMock()
            response = client.post("/contacts/", json={
                "property_id": sample_property.id,
                "name": "Alice Smith",
                "role": "lawyer",
                "phone": "555-1234",
                "email": "alice@law.com",
                "company": "Smith Law",
            }, headers=agent_headers)
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Alice Smith"
            assert data["role"] == "lawyer"
            assert data["first_name"] == "Alice"
            assert data["last_name"] == "Smith"

    def test_create_buyer_triggers_notification(self, client, sample_property, agent_headers):
        with patch("app.routers.contacts.notification_service") as mock_notif, \
             patch("app.services.property_recap_service.regenerate_recap_background"):
            mock_notif.notify_new_lead = AsyncMock()
            response = client.post("/contacts/", json={
                "property_id": sample_property.id,
                "name": "Bob Buyer",
                "role": "buyer",
                "email": "bob@buy.com",
            }, headers=agent_headers)
            assert response.status_code == 201
            mock_notif.notify_new_lead.assert_called_once()

    def test_create_invalid_property(self, client, agent, agent_headers):
        response = client.post("/contacts/", json={
            "property_id": 99999,
            "name": "Ghost",
            "role": "other",
        }, headers=agent_headers)
        assert response.status_code == 404

    def test_create_with_single_name(self, client, sample_property, agent_headers):
        with patch("app.routers.contacts.notification_service") as mock_notif, \
             patch("app.services.property_recap_service.regenerate_recap_background"):
            mock_notif.notify_new_lead = AsyncMock()
            response = client.post("/contacts/", json={
                "property_id": sample_property.id,
                "name": "Madonna",
                "role": "stager",
            }, headers=agent_headers)
            assert response.status_code == 201
            data = response.json()
            assert data["first_name"] == "Madonna"
            assert data["last_name"] is None


class TestListContacts:
    def test_list_for_property(self, client, sample_contact, agent_headers):
        response = client.get(
            f"/contacts/property/{sample_contact.property_id}",
            headers=agent_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["contacts"]) >= 1
        assert "voice_summary" in data

    def test_list_for_nonexistent_property(self, client, agent, agent_headers):
        response = client.get("/contacts/property/99999", headers=agent_headers)
        assert response.status_code == 404

    def test_list_empty_property(self, client, second_property, agent_headers):
        response = client.get(
            f"/contacts/property/{second_property.id}",
            headers=agent_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["contacts"]) == 0
        assert "No contacts" in data["voice_summary"]


class TestGetContactsByRole:
    def test_get_by_role(self, client, sample_contact, agent_headers):
        response = client.get(
            f"/contacts/property/{sample_contact.property_id}/role/lawyer",
            headers=agent_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["contacts"]) >= 1
        for c in data["contacts"]:
            assert c["role"] == "lawyer"

    def test_get_role_alias(self, client, sample_contact, agent_headers):
        # "attorney" should map to "lawyer"
        response = client.get(
            f"/contacts/property/{sample_contact.property_id}/role/attorney",
            headers=agent_headers,
        )
        assert response.status_code == 200

    def test_get_empty_role(self, client, sample_property, agent_headers):
        response = client.get(
            f"/contacts/property/{sample_property.id}/role/plumber",
            headers=agent_headers,
        )
        assert response.status_code == 200
        assert len(response.json()["contacts"]) == 0


class TestGetContact:
    def test_get_existing(self, client, sample_contact, agent_headers):
        response = client.get(
            f"/contacts/{sample_contact.id}", headers=agent_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == sample_contact.id

    def test_get_nonexistent(self, client, agent, agent_headers):
        response = client.get("/contacts/99999", headers=agent_headers)
        assert response.status_code == 404


class TestUpdateContact:
    def test_update_phone(self, client, sample_contact, agent_headers):
        response = client.patch(f"/contacts/{sample_contact.id}", json={
            "phone": "555-UPDATED",
        }, headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["phone"] == "555-UPDATED"

    def test_update_name_reparses(self, client, sample_contact, agent_headers):
        response = client.patch(f"/contacts/{sample_contact.id}", json={
            "name": "Jane Marie Smith",
        }, headers=agent_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Marie Smith"

    def test_update_nonexistent(self, client, agent, agent_headers):
        response = client.patch("/contacts/99999", json={"phone": "x"}, headers=agent_headers)
        assert response.status_code == 404


class TestSearchContacts:
    def test_search_by_address(self, client, sample_contact, sample_property, agent_headers):
        response = client.get(
            f"/contacts/voice/search?address_query={sample_property.address[:8]}",
            headers=agent_headers,
        )
        assert response.status_code == 200
        assert len(response.json()["contacts"]) >= 1

    def test_search_by_address_with_role(self, client, sample_contact, sample_property, agent_headers):
        response = client.get(
            f"/contacts/voice/search?address_query={sample_property.address[:8]}&role=lawyer",
            headers=agent_headers,
        )
        assert response.status_code == 200

    def test_search_nonexistent_address(self, client, agent, agent_headers):
        response = client.get(
            "/contacts/voice/search?address_query=nonexistent_street_xyz",
            headers=agent_headers,
        )
        assert response.status_code == 404


class TestDeleteContact:
    def test_delete_existing(self, client, sample_contact, agent_headers):
        response = client.delete(
            f"/contacts/{sample_contact.id}", headers=agent_headers
        )
        assert response.status_code == 204

    def test_delete_nonexistent(self, client, agent, agent_headers):
        response = client.delete("/contacts/99999", headers=agent_headers)
        assert response.status_code == 404
