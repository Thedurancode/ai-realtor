"""Tests for the offers router (create, counter, accept, reject, withdraw)."""

from unittest.mock import patch


class TestCreateOffer:
    def test_create_basic(self, client, sample_property, agent_headers):
        response = client.post("/offers/", json={
            "property_id": sample_property.id,
            "offer_price": 300000,
            "financing_type": "cash",
            "closing_days": 30,
        }, headers=agent_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["offer_price"] == 300000
        assert data["status"] == "submitted"
        assert data["financing_type"] == "cash"

    def test_create_with_contingencies(self, client, sample_property, agent_headers):
        response = client.post("/offers/", json={
            "property_id": sample_property.id,
            "offer_price": 310000,
            "contingencies": ["inspection", "financing", "appraisal"],
            "earnest_money": 5000,
        }, headers=agent_headers)
        assert response.status_code == 201
        data = response.json()
        assert len(data["contingencies"]) == 3
        assert data["earnest_money"] == 5000

    def test_create_invalid_property(self, client, agent, agent_headers):
        response = client.post("/offers/", json={
            "property_id": 99999,
            "offer_price": 100000,
        }, headers=agent_headers)
        assert response.status_code == 400

    def test_create_with_buyer_contact(self, client, sample_property, buyer_contact, agent_headers):
        response = client.post("/offers/", json={
            "property_id": sample_property.id,
            "offer_price": 325000,
            "buyer_contact_id": buyer_contact.id,
        }, headers=agent_headers)
        assert response.status_code == 201
        assert response.json()["buyer_contact_id"] == buyer_contact.id


class TestListOffers:
    def test_list_all(self, client, sample_offer, agent_headers):
        response = client.get("/offers/", headers=agent_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_list_by_property(self, client, sample_offer, sample_property, agent_headers):
        response = client.get(
            f"/offers/?property_id={sample_property.id}",
            headers=agent_headers,
        )
        assert response.status_code == 200
        for o in response.json():
            assert o["property_id"] == sample_property.id

    def test_list_by_status(self, client, sample_offer, agent_headers):
        response = client.get("/offers/?status=submitted", headers=agent_headers)
        assert response.status_code == 200
        for o in response.json():
            assert o["status"] == "submitted"


class TestGetOffer:
    def test_get_existing(self, client, sample_offer, agent_headers):
        response = client.get(f"/offers/{sample_offer.id}", headers=agent_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_offer.id
        assert "offer_price_formatted" in data

    def test_get_nonexistent(self, client, agent, agent_headers):
        response = client.get("/offers/99999", headers=agent_headers)
        assert response.status_code == 404


class TestCounterOffer:
    def test_counter_submitted_offer(self, client, sample_offer, agent_headers):
        response = client.post(f"/offers/{sample_offer.id}/counter", json={
            "offer_price": 340000,
            "closing_days": 45,
        }, headers=agent_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["offer_price"] == 340000
        assert data["parent_offer_id"] == sample_offer.id
        assert data["status"] == "submitted"

    def test_counter_nonexistent(self, client, agent, agent_headers):
        response = client.post("/offers/99999/counter", json={
            "offer_price": 100000,
        }, headers=agent_headers)
        assert response.status_code == 400


class TestAcceptOffer:
    def test_accept(self, client, sample_offer, agent_headers):
        response = client.post(f"/offers/{sample_offer.id}/accept", headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    def test_accept_nonexistent(self, client, agent, agent_headers):
        response = client.post("/offers/99999/accept", headers=agent_headers)
        assert response.status_code == 400


class TestRejectOffer:
    def test_reject(self, client, sample_offer, agent_headers):
        response = client.post(f"/offers/{sample_offer.id}/reject", headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"

    def test_reject_nonexistent(self, client, agent, agent_headers):
        response = client.post("/offers/99999/reject", headers=agent_headers)
        assert response.status_code == 400


class TestWithdrawOffer:
    def test_withdraw(self, client, sample_offer, agent_headers):
        response = client.post(f"/offers/{sample_offer.id}/withdraw", headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "withdrawn"

    def test_withdraw_nonexistent(self, client, agent, agent_headers):
        response = client.post("/offers/99999/withdraw", headers=agent_headers)
        assert response.status_code == 400
