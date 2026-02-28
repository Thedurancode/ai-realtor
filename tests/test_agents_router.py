"""Tests for the agents router (CRUD operations)."""


class TestRegisterAgent:
    def test_register_success(self, client):
        response = client.post("/agents/register", json={
            "name": "New Agent",
            "email": "newagent@example.com",
            "phone": "555-9999",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Agent"
        assert data["email"] == "newagent@example.com"
        assert "api_key" in data
        assert data["api_key"].startswith("sk_live_")

    def test_register_duplicate_email(self, client, agent):
        response = client.post("/agents/register", json={
            "name": "Duplicate",
            "email": "test@example.com",  # same as agent fixture
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_with_license(self, client):
        response = client.post("/agents/register", json={
            "name": "Licensed Agent",
            "email": "licensed@example.com",
            "license_number": "LIC-999",
        })
        assert response.status_code == 201


class TestCreateAgent:
    def test_create_agent(self, client, agent, agent_headers):
        response = client.post("/agents/", json={
            "name": "Created Agent",
            "email": "created@example.com",
        }, headers=agent_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Created Agent"

    def test_create_duplicate_email(self, client, agent, agent_headers):
        response = client.post("/agents/", json={
            "name": "Dup",
            "email": "test@example.com",
        }, headers=agent_headers)
        assert response.status_code == 400


class TestListAgents:
    def test_list_empty(self, client, agent, agent_headers):
        # agent fixture creates one agent
        response = client.get("/agents/", headers=agent_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_list_pagination(self, client, agent, agent_headers):
        response = client.get("/agents/?skip=0&limit=1", headers=agent_headers)
        assert response.status_code == 200
        assert len(response.json()) <= 1


class TestGetAgent:
    def test_get_existing(self, client, agent, agent_headers):
        response = client.get(f"/agents/{agent.id}", headers=agent_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent.id
        assert data["name"] == agent.name

    def test_get_nonexistent(self, client, agent, agent_headers):
        response = client.get("/agents/99999", headers=agent_headers)
        assert response.status_code == 404


class TestUpdateAgent:
    def test_update_name(self, client, agent, agent_headers):
        response = client.patch(f"/agents/{agent.id}", json={
            "name": "Updated Name",
        }, headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_update_nonexistent(self, client, agent, agent_headers):
        response = client.patch("/agents/99999", json={
            "name": "Ghost",
        }, headers=agent_headers)
        assert response.status_code == 404

    def test_partial_update(self, client, agent, agent_headers):
        response = client.patch(f"/agents/{agent.id}", json={
            "phone": "555-UPDATED",
        }, headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["phone"] == "555-UPDATED"
        assert response.json()["name"] == agent.name  # unchanged


class TestDeleteAgent:
    def test_delete_existing(self, client, agent, agent_headers):
        response = client.delete(f"/agents/{agent.id}", headers=agent_headers)
        assert response.status_code == 204

    def test_delete_nonexistent(self, client, agent, agent_headers):
        response = client.delete("/agents/99999", headers=agent_headers)
        assert response.status_code == 404
