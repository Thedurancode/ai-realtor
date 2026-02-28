"""Tests for the contracts router (CRUD + status)."""

from app.models.contract import ContractStatus


class TestCreateContract:
    def test_create_basic(self, client, sample_property, agent_headers):
        response = client.post("/contracts/", json={
            "property_id": sample_property.id,
            "name": "Inspection Agreement",
            "description": "Standard inspection agreement",
        }, headers=agent_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Inspection Agreement"
        assert data["status"] == "draft"

    def test_create_invalid_property(self, client, agent, agent_headers):
        response = client.post("/contracts/", json={
            "property_id": 99999,
            "name": "Ghost Contract",
        }, headers=agent_headers)
        assert response.status_code == 404

    def test_create_with_contact(self, client, sample_property, sample_contact, agent_headers):
        response = client.post("/contracts/", json={
            "property_id": sample_property.id,
            "name": "Lawyer Contract",
            "contact_id": sample_contact.id,
        }, headers=agent_headers)
        assert response.status_code == 201
        assert response.json()["contact_id"] == sample_contact.id


class TestListContracts:
    def test_list_all(self, client, sample_contract, agent_headers):
        response = client.get("/contracts/", headers=agent_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_list_by_status(self, client, sample_contract, agent_headers):
        response = client.get("/contracts/?status=draft", headers=agent_headers)
        assert response.status_code == 200
        for c in response.json():
            assert c["status"] == "draft"

    def test_list_pagination(self, client, sample_contract, agent_headers):
        response = client.get("/contracts/?limit=1&offset=0", headers=agent_headers)
        assert response.status_code == 200
        assert len(response.json()) <= 1


class TestListContractsForProperty:
    def test_list_property_contracts(self, client, sample_contract, sample_property, agent_headers):
        response = client.get(
            f"/contracts/property/{sample_property.id}",
            headers=agent_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_nonexistent_property(self, client, agent, agent_headers):
        response = client.get("/contracts/property/99999", headers=agent_headers)
        assert response.status_code == 404


class TestGetContract:
    def test_get_existing(self, client, sample_contract, agent_headers):
        response = client.get(
            f"/contracts/{sample_contract.id}", headers=agent_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == sample_contract.id

    def test_get_nonexistent(self, client, agent, agent_headers):
        response = client.get("/contracts/99999", headers=agent_headers)
        assert response.status_code == 404


class TestUpdateContract:
    def test_update_name(self, client, sample_contract, agent_headers):
        response = client.patch(f"/contracts/{sample_contract.id}", json={
            "name": "Updated Contract Name",
        }, headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Contract Name"

    def test_update_status(self, client, sample_contract, agent_headers):
        response = client.patch(f"/contracts/{sample_contract.id}", json={
            "status": "sent",
        }, headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "sent"

    def test_update_nonexistent(self, client, agent, agent_headers):
        response = client.patch("/contracts/99999", json={
            "name": "Ghost",
        }, headers=agent_headers)
        assert response.status_code == 404


class TestDeleteContract:
    def test_delete_existing(self, client, sample_contract, agent_headers):
        response = client.delete(
            f"/contracts/{sample_contract.id}", headers=agent_headers
        )
        assert response.status_code == 204

    def test_delete_nonexistent(self, client, agent, agent_headers):
        response = client.delete("/contracts/99999", headers=agent_headers)
        assert response.status_code == 404
