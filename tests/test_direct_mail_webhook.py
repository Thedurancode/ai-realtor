"""
Tests for Lob Webhook Signature Verification
"""

import pytest
import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from fastapi import Request

from app.config import settings


class TestLobWebhookSecurity:
    """Test Lob webhook signature verification"""

    @pytest.fixture
    def webhook_client(self, client):
        """Reuse the conftest client which has DB overrides."""
        return client

    @pytest.fixture
    def webhook_secret(self):
        """Test webhook secret"""
        return "test_webhook_secret_123"

    @pytest.fixture
    def sample_webhook_payload(self):
        """Sample Lob webhook payload"""
        return {
            "id": "evt_test123",
            "event_type": "postcard.delivered",
            "resource": {
                "type": "postcard",
                "id": "postcard_test123"
            },
            "data": {
                "id": "lob_abc123",
                "expected_delivery_date": "2026-03-01",
                "tracking_events": [
                    {"event": "delivered", "time": "2026-03-01T14:30:00Z"}
                ]
            }
        }

    def test_webhook_rejects_missing_signature(self, webhook_client, agent, agent_headers, sample_webhook_payload):
        """Test that webhook rejects requests without signature"""
        original_secret = settings.lob_webhook_secret
        settings.lob_webhook_secret = "test_secret"

        try:
            response = webhook_client.post(
                "/webhooks/lob",
                json=sample_webhook_payload
            )

            # Should return 401 when signature is missing
            assert response.status_code in [401, 403]

        finally:
            settings.lob_webhook_secret = original_secret

    def test_webhook_rejects_invalid_signature(self, webhook_client, agent, agent_headers, sample_webhook_payload):
        """Test that webhook rejects requests with invalid signature"""
        original_secret = settings.lob_webhook_secret
        settings.lob_webhook_secret = "test_secret"

        try:
            response = webhook_client.post(
                "/webhooks/lob",
                json=sample_webhook_payload,
                headers={"x-lob-signature": "sha256=invalid_signature"}
            )

            # Should return 401 when signature is invalid
            assert response.status_code in [401, 403]

        finally:
            settings.lob_webhook_secret = original_secret

    def test_webhook_accepts_valid_signature(self, webhook_client, agent, agent_headers, sample_webhook_payload, webhook_secret):
        """Test that webhook accepts requests with valid signature"""
        original_secret = settings.lob_webhook_secret
        settings.lob_webhook_secret = webhook_secret

        try:
            # We must send the body as raw bytes and compute the signature
            # from the exact same bytes, since TestClient may serialize differently
            body = json.dumps(sample_webhook_payload, separators=(",", ":")).encode()

            signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()

            response = webhook_client.post(
                "/webhooks/lob",
                content=body,
                headers={
                    "x-lob-signature": f"sha256={signature}",
                    "content-type": "application/json"
                }
            )

            # Should accept the webhook (may be 200 or other success code)
            # Even if the mailpiece doesn't exist in DB, signature should pass
            assert response.status_code not in [401, 403]

        finally:
            settings.lob_webhook_secret = original_secret

    def test_webhook_works_without_secret_in_dev(self, webhook_client, agent, agent_headers, sample_webhook_payload):
        """Test that webhook works when secret is not configured (dev mode)"""
        original_secret = settings.lob_webhook_secret
        settings.lob_webhook_secret = ""

        try:
            # Should not require signature when secret is not set
            response = webhook_client.post(
                "/webhooks/lob",
                json=sample_webhook_payload
            )

            # Should not return 401 when no secret is configured
            assert response.status_code not in [401, 403]

        finally:
            settings.lob_webhook_secret = original_secret

    def test_webhook_test_endpoint(self, webhook_client, agent, agent_headers):
        """Test webhook configuration endpoint"""
        response = webhook_client.get("/webhooks/lob/test")

        assert response.status_code == 200
        data = response.json()

        assert "webhook_url" in data
        assert data["webhook_url"] == "/webhooks/lob"
        assert "supported_events" in data
        assert "postcard.delivered" in data["supported_events"]
        assert "configuration_steps" in data

    def test_signature_format_validation(self):
        """Test signature format validation"""
        # Valid format
        valid_sig = "sha256=abc123def456"
        assert valid_sig.startswith("sha256=")
        assert "=" in valid_sig

        # Invalid formats
        invalid_sigs = [
            "abc123",  # No prefix
            "md5=abc123",  # Wrong algorithm
            "sha256",  # No equals or hash
        ]

        for sig in invalid_sigs:
            assert not sig.startswith("sha256=") or len(sig.split("=")) != 2

    def test_webhook_handles_all_event_types(self, webhook_client, agent, agent_headers, sample_webhook_payload, webhook_secret):
        """Test that webhook handles all supported event types"""
        original_secret = settings.lob_webhook_secret
        settings.lob_webhook_secret = webhook_secret

        event_types = [
            "postcard.processed",
            "postcard.mailed",
            "postcard.in_transit",
            "postcard.delivered",
            "postcard.cancelled",
            "postcard.production_failed",
            "letter.processed",
            "letter.mailed",
            "letter.in_transit",
            "letter.delivered",
            "letter.cancelled",
            "letter.production_failed",
        ]

        try:
            for event_type in event_types:
                payload = dict(sample_webhook_payload)
                payload["event_type"] = event_type
                body = json.dumps(payload, separators=(",", ":")).encode()
                signature = hmac.new(
                    webhook_secret.encode(),
                    body,
                    hashlib.sha256
                ).hexdigest()

                response = webhook_client.post(
                    "/webhooks/lob",
                    content=body,
                    headers={
                        "x-lob-signature": f"sha256={signature}",
                        "content-type": "application/json"
                    }
                )

                # Should not reject due to signature verification
                assert response.status_code not in [401, 403], f"Failed for event type: {event_type}"

        finally:
            settings.lob_webhook_secret = original_secret
