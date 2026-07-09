"""Tests for configuration loading."""

import os
from pathlib import Path


class TestSettings:
    def test_base_dir_exists(self):
        from config.settings import BASE_DIR
        assert BASE_DIR.exists()
        assert (BASE_DIR / "config").exists()

    def test_default_lms_url(self):
        from config.settings import LMS_URL
        assert LMS_URL == "https://lms.ssn.edu.in"

    def test_default_ai_provider(self):
        from config.settings import AI_PROVIDER
        assert AI_PROVIDER == "google"

    def test_default_host(self):
        from config.settings import MCP_SERVER_HOST
        assert MCP_SERVER_HOST == "127.0.0.1"

    def test_default_port(self):
        from config.settings import MCP_SERVER_PORT
        assert MCP_SERVER_PORT == 8080

    def test_default_poll_interval(self):
        from config.settings import POLL_INTERVAL_MINUTES
        assert POLL_INTERVAL_MINUTES == 30

    def test_database_path_default_contains_data_dir(self):
        import config.settings as cs
        assert "data" in str(cs.DATABASE_PATH)
        assert cs.DATABASE_PATH.name == "lms_mcp.db"

    def test_generated_dir_default_exists(self):
        import config.settings as cs
        assert isinstance(cs.GENERATED_DIR, Path)
        assert cs.GENERATED_DIR.exists()

    def test_env_vars_override_defaults(self, monkeypatch):
        monkeypatch.setenv("LMS_URL", "https://custom-lms.example.com")
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        import importlib
        import config.settings
        importlib.reload(config.settings)
        assert config.settings.LMS_URL == "https://custom-lms.example.com"
        assert config.settings.AI_PROVIDER == "anthropic"
        monkeypatch.delenv("LMS_URL")
        monkeypatch.delenv("AI_PROVIDER")
        importlib.reload(config.settings)
