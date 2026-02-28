"""Tests for application configuration."""

import os
from unittest.mock import patch


class TestSettings:
    def test_settings_defaults(self):
        from app.config import Settings
        s = Settings()
        assert s.google_places_api_key == ""
        assert s.docuseal_api_key == ""
        assert s.exa_base_url == "https://api.exa.ai"
        assert s.exa_search_type == "auto"
        assert s.exa_timeout_seconds == 20
        assert s.campaign_worker_enabled is True
        assert s.campaign_worker_interval_seconds == 15
        assert s.campaign_worker_max_calls_per_tick == 5
        assert s.daily_digest_enabled is True
        assert s.daily_digest_hour == 8
        assert s.redis_host == "localhost"
        assert s.redis_port == 6379
        assert s.aws_region == "us-east-1"
        assert s.lob_test_mode is False

    def test_settings_from_env(self):
        from app.config import Settings
        with patch.dict(os.environ, {
            "GOOGLE_PLACES_API_KEY": "test-key",
            "CAMPAIGN_WORKER_ENABLED": "false",
            "DAILY_DIGEST_HOUR": "10",
        }):
            s = Settings()
            assert s.google_places_api_key == "test-key"
            assert s.campaign_worker_enabled is False
            assert s.daily_digest_hour == 10

    def test_settings_extra_ignore(self):
        """Settings should ignore extra env vars."""
        from app.config import Settings
        with patch.dict(os.environ, {"UNKNOWN_SETTING": "value"}):
            s = Settings()
            assert not hasattr(s, "unknown_setting")


class TestDatabaseConfig:
    def test_database_url_default(self):
        """DATABASE_URL has a fallback default."""
        from app.database import Base
        assert Base is not None

    def test_get_db_yields_session(self):
        from app.database import get_db
        gen = get_db()
        session = next(gen)
        assert session is not None
        try:
            next(gen)
        except StopIteration:
            pass
