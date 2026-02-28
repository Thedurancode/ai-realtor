"""Tests for authentication and security utilities."""

import hashlib
import hmac

from app.auth import generate_api_key, hash_api_key, verify_api_key, verify_telnyx_webhook_signature


class TestGenerateApiKey:
    def test_format(self):
        key = generate_api_key()
        assert key.startswith("sk_live_")
        # 64 hex chars after prefix
        assert len(key) == len("sk_live_") + 64

    def test_uniqueness(self):
        keys = {generate_api_key() for _ in range(50)}
        assert len(keys) == 50


class TestHashApiKey:
    def test_deterministic(self):
        key = "sk_live_abc123"
        assert hash_api_key(key) == hash_api_key(key)

    def test_sha256(self):
        key = "sk_live_abc123"
        expected = hashlib.sha256(key.encode()).hexdigest()
        assert hash_api_key(key) == expected

    def test_different_keys_different_hashes(self):
        assert hash_api_key("key1") != hash_api_key("key2")


class TestVerifyApiKey:
    def test_valid_key(self, db, agent):
        from tests.conftest import TEST_API_KEY
        result = verify_api_key(db, TEST_API_KEY)
        assert result is not None
        assert result.id == agent.id

    def test_invalid_key(self, db, agent):
        result = verify_api_key(db, "sk_live_invalid_key_12345")
        assert result is None

    def test_empty_key(self, db):
        result = verify_api_key(db, "")
        assert result is None


class TestVerifyTelnyxWebhookSignature:
    def test_valid_signature(self):
        payload = b'{"event": "test"}'
        secret = "test_webhook_secret"
        computed = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        signature = f"t=1234567890,v1={computed}"

        assert verify_telnyx_webhook_signature(payload, signature, secret) is True

    def test_invalid_signature(self):
        payload = b'{"event": "test"}'
        secret = "test_webhook_secret"
        signature = "t=1234567890,v1=invalidsignature"

        assert verify_telnyx_webhook_signature(payload, signature, secret) is False

    def test_missing_v1(self):
        payload = b'{"event": "test"}'
        secret = "test_secret"
        signature = "t=1234567890"

        assert verify_telnyx_webhook_signature(payload, signature, secret) is False

    def test_empty_signature(self):
        payload = b'{"event": "test"}'
        assert verify_telnyx_webhook_signature(payload, "", "secret") is False

    def test_no_secret_configured(self):
        """When no secret is configured, verification is skipped (returns True)."""
        payload = b'{"event": "test"}'
        assert verify_telnyx_webhook_signature(payload, "any", None) is True

    def test_malformed_signature(self):
        payload = b'{"event": "test"}'
        assert verify_telnyx_webhook_signature(payload, "garbage", "secret") is False


class TestApiKeyMiddleware:
    def test_public_path_no_auth(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_docs_no_auth(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_health_no_auth(self, client):
        response = client.get("/health")
        assert response.status_code in (200, 503)  # depends on DB

    def test_protected_path_no_key(self, client):
        response = client.get("/agents/")
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    def test_protected_path_invalid_key(self, client):
        response = client.get("/agents/", headers={"x-api-key": "invalid"})
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_protected_path_valid_key(self, client, agent, agent_headers):
        response = client.get("/agents/", headers=agent_headers)
        assert response.status_code == 200
