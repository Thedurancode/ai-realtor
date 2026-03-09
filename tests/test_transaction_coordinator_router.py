"""Tests for Transaction Coordinator router — endpoint-level integration tests.

Covers every endpoint in app/routers/transaction_coordinator.py:
- POST   /transactions/
- GET    /transactions/
- GET    /transactions/active
- GET    /transactions/pipeline
- GET    /transactions/check-deadlines
- GET    /transactions/{txn_id}
- GET    /transactions/{txn_id}/summary
- PUT    /transactions/{txn_id}/status
- POST   /transactions/{txn_id}/party
- POST   /transactions/{txn_id}/risk-flag
- POST   /transactions/{txn_id}/milestones
- PUT    /transactions/milestones/{milestone_id}
"""

import pytest
from datetime import datetime, timedelta, timezone


# ── Create ──────────────────────────────────────────────────────


def test_create_transaction(client, agent, agent_headers, sample_property):
    resp = client.post(
        "/transactions/",
        json={
            "property_id": sample_property.id,
            "title": "Test Deal",
            "sale_price": 350000,
            "earnest_money": 5000,
            "financing_type": "conventional",
        },
        headers=agent_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Deal"
    assert data["sale_price"] == 350000
    assert data["status"] == "initiated"
    assert len(data["milestones"]) == 9  # 9 default milestones


def test_create_transaction_minimal(client, agent, agent_headers, sample_property):
    resp = client.post(
        "/transactions/",
        json={"property_id": sample_property.id},
        headers=agent_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["property_id"] == sample_property.id
    assert "Transaction — Property" in data["title"]


def test_create_transaction_invalid_property(client, agent, agent_headers):
    resp = client.post(
        "/transactions/",
        json={"property_id": 99999},
        headers=agent_headers,
    )
    # Should fail due to FK constraint (500 or 422)
    assert resp.status_code in (422, 500)


# ── List / Read ─────────────────────────────────────────────────


def test_list_transactions(client, agent, agent_headers, sample_property):
    # Create two
    client.post("/transactions/", json={"property_id": sample_property.id}, headers=agent_headers)
    client.post("/transactions/", json={"property_id": sample_property.id, "title": "Second"}, headers=agent_headers)

    resp = client.get("/transactions/", headers=agent_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_transactions_filter_status(client, agent, agent_headers, sample_property):
    client.post("/transactions/", json={"property_id": sample_property.id}, headers=agent_headers)

    resp = client.get("/transactions/?status=initiated", headers=agent_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get("/transactions/?status=closed", headers=agent_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_list_active_transactions(client, agent, agent_headers, sample_property):
    client.post("/transactions/", json={"property_id": sample_property.id}, headers=agent_headers)

    resp = client.get("/transactions/active", headers=agent_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_transaction(client, agent, agent_headers, sample_property):
    create_resp = client.post(
        "/transactions/",
        json={"property_id": sample_property.id, "title": "Lookup Test"},
        headers=agent_headers,
    )
    txn_id = create_resp.json()["id"]

    resp = client.get(f"/transactions/{txn_id}", headers=agent_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Lookup Test"


def test_get_transaction_not_found(client, agent, agent_headers):
    resp = client.get("/transactions/99999", headers=agent_headers)
    assert resp.status_code == 404


def test_get_transaction_summary(client, agent, agent_headers, sample_property):
    create_resp = client.post(
        "/transactions/",
        json={"property_id": sample_property.id, "sale_price": 400000},
        headers=agent_headers,
    )
    txn_id = create_resp.json()["id"]

    resp = client.get(f"/transactions/{txn_id}/summary", headers=agent_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sale_price"] == 400000
    assert data["milestones_total"] == 9
    assert "days_to_close" in data


def test_get_transaction_summary_not_found(client, agent, agent_headers):
    resp = client.get("/transactions/99999/summary", headers=agent_headers)
    assert resp.status_code == 404


# ── Pipeline ────────────────────────────────────────────────────


def test_pipeline_empty(client, agent, agent_headers):
    resp = client.get("/transactions/pipeline", headers=agent_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_count"] == 0


def test_pipeline_with_data(client, agent, agent_headers, sample_property):
    client.post(
        "/transactions/",
        json={"property_id": sample_property.id, "sale_price": 500000},
        headers=agent_headers,
    )

    resp = client.get("/transactions/pipeline", headers=agent_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_count"] == 1
    assert data["total_pipeline_value"] == 500000


# ── Check Deadlines ────────────────────────────────────────────


def test_check_deadlines_endpoint(client, agent, agent_headers, sample_property):
    # Create a transaction with past dates so milestones are overdue
    past = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    client.post(
        "/transactions/",
        json={
            "property_id": sample_property.id,
            "accepted_date": past,
            "closing_date": future,
        },
        headers=agent_headers,
    )

    resp = client.get("/transactions/check-deadlines", headers=agent_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] > 0
    assert len(data["alerts"]) > 0


# ── Status Updates ──────────────────────────────────────────────


def test_advance_status(client, agent, agent_headers, sample_property):
    create_resp = client.post(
        "/transactions/",
        json={"property_id": sample_property.id},
        headers=agent_headers,
    )
    txn_id = create_resp.json()["id"]

    resp = client.put(
        f"/transactions/{txn_id}/status?new_status=inspections&notes=Ready",
        headers=agent_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "inspections"


def test_advance_status_not_found(client, agent, agent_headers):
    resp = client.put(
        "/transactions/99999/status?new_status=closed",
        headers=agent_headers,
    )
    assert resp.status_code == 404


# ── Parties ─────────────────────────────────────────────────────


def test_add_party(client, agent, agent_headers, sample_property):
    create_resp = client.post(
        "/transactions/",
        json={"property_id": sample_property.id},
        headers=agent_headers,
    )
    txn_id = create_resp.json()["id"]

    resp = client.post(
        f"/transactions/{txn_id}/party?name=Bob+Attorney&role=attorney&email=bob@law.com",
        headers=agent_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()["parties"]) == 1


def test_add_party_not_found(client, agent, agent_headers):
    resp = client.post(
        "/transactions/99999/party?name=Bob&role=attorney",
        headers=agent_headers,
    )
    assert resp.status_code == 404


# ── Risk Flags ──────────────────────────────────────────────────


def test_add_risk_flag(client, agent, agent_headers, sample_property):
    create_resp = client.post(
        "/transactions/",
        json={"property_id": sample_property.id},
        headers=agent_headers,
    )
    txn_id = create_resp.json()["id"]

    resp = client.post(
        f"/transactions/{txn_id}/risk-flag?flag=appraisal_gap",
        headers=agent_headers,
    )
    assert resp.status_code == 200
    assert "appraisal_gap" in resp.json()["risk_flags"]


def test_add_risk_flag_not_found(client, agent, agent_headers):
    resp = client.post(
        "/transactions/99999/risk-flag?flag=test",
        headers=agent_headers,
    )
    assert resp.status_code == 404


# ── Milestones ──────────────────────────────────────────────────


def test_add_custom_milestone(client, agent, agent_headers, sample_property):
    create_resp = client.post(
        "/transactions/",
        json={"property_id": sample_property.id},
        headers=agent_headers,
    )
    txn_id = create_resp.json()["id"]

    resp = client.post(
        f"/transactions/{txn_id}/milestones",
        json={
            "name": "Radon Test",
            "assigned_role": "inspector",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        },
        headers=agent_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Radon Test"
    assert resp.json()["status"] == "pending"


def test_add_milestone_to_nonexistent_transaction(client, agent, agent_headers):
    resp = client.post(
        "/transactions/99999/milestones",
        json={"name": "Test"},
        headers=agent_headers,
    )
    assert resp.status_code == 404


def test_update_milestone(client, agent, agent_headers, sample_property):
    create_resp = client.post(
        "/transactions/",
        json={"property_id": sample_property.id},
        headers=agent_headers,
    )
    milestone_id = create_resp.json()["milestones"][0]["id"]

    resp = client.put(
        f"/transactions/milestones/{milestone_id}",
        json={"status": "completed", "outcome_notes": "Passed review"},
        headers=agent_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["outcome_notes"] == "Passed review"
    assert data["completed_at"] is not None


def test_update_milestone_not_found(client, agent, agent_headers):
    resp = client.put(
        "/transactions/milestones/99999",
        json={"status": "completed"},
        headers=agent_headers,
    )
    assert resp.status_code == 404
