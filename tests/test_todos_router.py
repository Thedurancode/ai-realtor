"""Tests for the todos router (CRUD + voice + search)."""

from app.models.todo import TodoStatus, TodoPriority


class TestCreateTodo:
    def test_create_basic(self, client, sample_property, agent_headers):
        response = client.post("/todos/", json={
            "property_id": sample_property.id,
            "title": "Call inspector",
            "priority": "high",
        }, headers=agent_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Call inspector"
        assert data["priority"] == "high"
        assert data["status"] == "pending"

    def test_create_with_contact(self, client, sample_property, sample_contact, agent_headers):
        response = client.post("/todos/", json={
            "property_id": sample_property.id,
            "title": "Follow up with lawyer",
            "contact_id": sample_contact.id,
        }, headers=agent_headers)
        assert response.status_code == 201
        assert response.json()["contact_id"] == sample_contact.id

    def test_create_invalid_property(self, client, agent, agent_headers):
        response = client.post("/todos/", json={
            "property_id": 99999,
            "title": "Ghost todo",
        }, headers=agent_headers)
        assert response.status_code == 404

    def test_create_invalid_contact(self, client, sample_property, agent_headers):
        response = client.post("/todos/", json={
            "property_id": sample_property.id,
            "title": "Bad contact",
            "contact_id": 99999,
        }, headers=agent_headers)
        assert response.status_code == 404

    def test_create_contact_wrong_property(self, client, second_property, sample_contact, agent_headers):
        """Contact from one property can't be used on another property's todo."""
        response = client.post("/todos/", json={
            "property_id": second_property.id,
            "title": "Wrong property contact",
            "contact_id": sample_contact.id,
        }, headers=agent_headers)
        assert response.status_code == 400


class TestCreateTodoFromVoice:
    def test_voice_create(self, client, sample_property, agent_headers):
        response = client.post("/todos/voice", json={
            "address_query": sample_property.address[:8],
            "title": "Schedule appraisal",
            "priority": "urgent",
        }, headers=agent_headers)
        assert response.status_code == 201
        data = response.json()
        assert "voice_confirmation" in data
        assert "urgent" in data["voice_confirmation"]

    def test_voice_create_with_due_date(self, client, sample_property, agent_headers):
        response = client.post("/todos/voice", json={
            "address_query": sample_property.address[:8],
            "title": "File paperwork",
            "due_date": "tomorrow",
        }, headers=agent_headers)
        assert response.status_code == 201
        assert response.json()["todo"]["due_date"] is not None

    def test_voice_create_nonexistent_property(self, client, agent, agent_headers):
        response = client.post("/todos/voice", json={
            "address_query": "nonexistent_xyz",
            "title": "Ghost todo",
        }, headers=agent_headers)
        assert response.status_code == 404


class TestListTodosForProperty:
    def test_list_all(self, client, sample_todo, agent_headers):
        response = client.get(
            f"/todos/property/{sample_todo.property_id}",
            headers=agent_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["todos"]) >= 1
        assert "voice_summary" in data

    def test_list_by_status(self, client, sample_todo, agent_headers):
        response = client.get(
            f"/todos/property/{sample_todo.property_id}?status=pending",
            headers=agent_headers,
        )
        assert response.status_code == 200
        for t in response.json()["todos"]:
            assert t["status"] == "pending"

    def test_list_nonexistent_property(self, client, agent, agent_headers):
        response = client.get("/todos/property/99999", headers=agent_headers)
        assert response.status_code == 404


class TestSearchTodosVoice:
    def test_search_by_address(self, client, sample_todo, sample_property, agent_headers):
        response = client.get(
            f"/todos/voice/search?address_query={sample_property.address[:8]}",
            headers=agent_headers,
        )
        assert response.status_code == 200
        assert len(response.json()["todos"]) >= 1

    def test_search_with_status_filter(self, client, sample_todo, sample_property, agent_headers):
        response = client.get(
            f"/todos/voice/search?address_query={sample_property.address[:8]}&status=pending",
            headers=agent_headers,
        )
        assert response.status_code == 200

    def test_search_nonexistent(self, client, agent, agent_headers):
        response = client.get(
            "/todos/voice/search?address_query=nonexistent_xyz",
            headers=agent_headers,
        )
        assert response.status_code == 404


class TestGetTodo:
    def test_get_existing(self, client, sample_todo, agent_headers):
        response = client.get(f"/todos/{sample_todo.id}", headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["id"] == sample_todo.id

    def test_get_nonexistent(self, client, agent, agent_headers):
        response = client.get("/todos/99999", headers=agent_headers)
        assert response.status_code == 404


class TestUpdateTodo:
    def test_update_status(self, client, sample_todo, agent_headers):
        response = client.patch(f"/todos/{sample_todo.id}", json={
            "status": "in_progress",
        }, headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

    def test_mark_completed(self, client, sample_todo, agent_headers):
        response = client.patch(f"/todos/{sample_todo.id}", json={
            "status": "completed",
        }, headers=agent_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_update_priority(self, client, sample_todo, agent_headers):
        response = client.patch(f"/todos/{sample_todo.id}", json={
            "priority": "low",
        }, headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["priority"] == "low"

    def test_update_nonexistent(self, client, agent, agent_headers):
        response = client.patch("/todos/99999", json={"status": "completed"}, headers=agent_headers)
        assert response.status_code == 404


class TestUpdateTodoFromVoice:
    def test_voice_mark_completed(self, client, sample_todo, agent_headers):
        response = client.patch("/todos/voice", json={
            "todo_id": sample_todo.id,
            "status": "done",
        }, headers=agent_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["todo"]["status"] == "completed"
        assert "voice_confirmation" in data

    def test_voice_update_nonexistent(self, client, agent, agent_headers):
        response = client.patch("/todos/voice", json={
            "todo_id": 99999,
            "status": "done",
        }, headers=agent_headers)
        assert response.status_code == 404


class TestDeleteTodo:
    def test_delete_existing(self, client, sample_todo, agent_headers):
        response = client.delete(f"/todos/{sample_todo.id}", headers=agent_headers)
        assert response.status_code == 204

    def test_delete_nonexistent(self, client, agent, agent_headers):
        response = client.delete("/todos/99999", headers=agent_headers)
        assert response.status_code == 404
