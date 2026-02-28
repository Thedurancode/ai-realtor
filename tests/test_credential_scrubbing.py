"""Tests for the credential scrubbing service."""

from app.services.credential_scrubbing import CredentialScrubber, scrub_credentials


class TestCredentialScrubber:
    def setup_method(self):
        self.scrubber = CredentialScrubber()

    def test_scrub_empty_string(self):
        assert self.scrubber.scrub("") == ""

    def test_scrub_none(self):
        assert self.scrubber.scrub(None) is None

    def test_scrub_no_secrets(self):
        text = "Hello, this is a normal message."
        assert self.scrubber.scrub(text) == text

    # API Keys
    def test_scrub_anthropic_key(self):
        text = "API key: sk-ant-1234567890abcdef1234567890"
        result = self.scrubber.scrub(text)
        assert "sk-ant-1234567890abcdef1234567890" not in result
        assert "***REDACTED***" in result

    def test_scrub_openai_key(self):
        text = "Key is sk-proj1234567890abcdefghij1234567890"
        result = self.scrubber.scrub(text)
        assert "sk-proj1234567890abcdefghij1234567890" not in result

    def test_scrub_aws_key(self):
        text = "AWS key: AKIA1234567890ABCDEF"
        result = self.scrubber.scrub(text)
        assert "AKIA1234567890ABCDEF" not in result

    # Passwords
    def test_scrub_json_password(self):
        text = '{"password":"super_secret_123"}'
        result = self.scrubber.scrub(text)
        assert "super_secret_123" not in result

    def test_scrub_password_equals(self):
        text = 'password=mysecretpass'
        result = self.scrubber.scrub(text)
        assert "mysecretpass" not in result

    # Tokens
    def test_scrub_bearer_token(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI.payload.signature"
        result = self.scrubber.scrub(text)
        assert "eyJhbGciOiJIUzI" not in result

    def test_scrub_jwt(self):
        text = "token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = self.scrubber.scrub(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    # SSNs
    def test_scrub_ssn_dashes(self):
        text = "SSN: 123-45-6789"
        result = self.scrubber.scrub(text)
        assert "123-45-6789" not in result

    def test_scrub_ssn_spaces(self):
        text = "SSN: 123 45 6789"
        result = self.scrubber.scrub(text)
        assert "123 45 6789" not in result

    # Credit Cards
    def test_scrub_credit_card_spaces(self):
        text = "Card: 4111 1111 1111 1111"
        result = self.scrubber.scrub(text)
        assert "4111 1111 1111 1111" not in result

    def test_scrub_credit_card_dashes(self):
        text = "Card: 4111-1111-1111-1111"
        result = self.scrubber.scrub(text)
        assert "4111-1111-1111-1111" not in result

    # Emails
    def test_scrub_email(self):
        text = "Contact: user@example.com"
        result = self.scrubber.scrub(text)
        assert "user@example.com" not in result

    def test_email_scrubbing_disabled(self):
        scrubber = CredentialScrubber({"scrub_email": False})
        text = "Contact: user@example.com"
        assert "user@example.com" in scrubber.scrub(text)

    # IP Addresses
    def test_scrub_ip(self):
        text = "Server: 192.168.1.1"
        result = self.scrubber.scrub(text)
        assert "192.168.1.1" not in result

    def test_ip_scrubbing_disabled(self):
        scrubber = CredentialScrubber({"scrub_ip": False})
        text = "Server: 192.168.1.1"
        assert "192.168.1.1" in scrubber.scrub(text)

    # Keep chars
    def test_keep_chars(self):
        scrubber = CredentialScrubber({"keep_chars": 4})
        text = "SSN: 123-45-6789"
        result = scrubber.scrub(text)
        # Should keep some chars visible for debugging
        assert "***REDACTED***" in result

    # Custom redaction string
    def test_custom_redaction_string(self):
        scrubber = CredentialScrubber({"redaction_string": "[HIDDEN]"})
        text = "SSN: 123-45-6789"
        result = scrubber.scrub(text)
        assert "[HIDDEN]" in result


class TestScrubDict:
    def setup_method(self):
        self.scrubber = CredentialScrubber()

    def test_scrub_sensitive_keys(self):
        data = {
            "api_key": "sk-ant-secret123",
            "name": "Test",
            "password": "hidden",
        }
        result = self.scrubber.scrub_dict(data)
        assert result["api_key"] == "***REDACTED***"
        assert result["password"] == "***REDACTED***"
        assert result["name"] == "Test"

    def test_scrub_nested_dict(self):
        data = {
            "config": {
                "api_key": "secret123",
                "host": "localhost",
            },
            "name": "test",
        }
        result = self.scrubber.scrub_dict(data)
        assert result["config"]["api_key"] == "***REDACTED***"

    def test_scrub_non_dict(self):
        assert self.scrubber.scrub_dict("not a dict") == "not a dict"


class TestScrubList:
    def setup_method(self):
        self.scrubber = CredentialScrubber()

    def test_scrub_list_strings(self):
        data = ["normal text", "API key: sk-ant-1234567890abcdef1234567890"]
        result = self.scrubber.scrub_list(data)
        assert result[0] == "normal text"
        assert "sk-ant-1234567890abcdef1234567890" not in result[1]

    def test_scrub_list_mixed(self):
        data = [
            {"api_key": "secret"},
            "plain text",
            42,
        ]
        result = self.scrubber.scrub_list(data)
        assert result[0]["api_key"] == "***REDACTED***"
        assert result[1] == "plain text"
        assert result[2] == 42


class TestScrubJson:
    def setup_method(self):
        self.scrubber = CredentialScrubber()

    def test_scrub_json_string(self):
        import json
        data = json.dumps({"api_key": "secret123", "name": "test"})
        result = self.scrubber.scrub_json(data)
        parsed = json.loads(result)
        assert parsed["api_key"] == "***REDACTED***"
        assert parsed["name"] == "test"

    def test_scrub_invalid_json(self):
        import pytest
        import json
        with pytest.raises(json.JSONDecodeError):
            self.scrubber.scrub_json("not json")


class TestScrubLogEntry:
    def setup_method(self):
        self.scrubber = CredentialScrubber()

    def test_scrub_log_output_field(self):
        entry = {
            "timestamp": "2026-01-01T00:00:00Z",
            "output": "Result: sk-ant-1234567890abcdef1234567890",
            "level": "info",
        }
        result = self.scrubber.scrub_log_entry(entry)
        assert "sk-ant-1234567890abcdef1234567890" not in result["output"]
        assert result["timestamp"] == entry["timestamp"]
        assert result["level"] == "info"


class TestConvenienceFunction:
    def test_scrub_string(self):
        result = scrub_credentials("key: sk-ant-1234567890abcdef1234567890")
        assert "sk-ant-1234567890abcdef1234567890" not in result

    def test_scrub_dict(self):
        result = scrub_credentials({"api_key": "secret", "name": "test"})
        assert result["api_key"] == "***REDACTED***"
        assert result["name"] == "test"

    def test_scrub_list(self):
        result = scrub_credentials(["normal", "sk-ant-1234567890abcdef1234567890"])
        assert "sk-ant-1234567890abcdef1234567890" not in result[1]

    def test_scrub_other_type(self):
        assert scrub_credentials(42) == 42
        assert scrub_credentials(None) is None

    def test_scrub_with_custom_config(self):
        result = scrub_credentials(
            "SSN: 123-45-6789",
            config={"redaction_string": "[REMOVED]"},
        )
        assert "[REMOVED]" in result
