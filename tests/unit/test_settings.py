"""
Unit tests for settings.
"""

import pytest
import os
from qilbee_mycelial_network.settings import QMNSettings


class TestQMNSettings:
    """Test QMN settings."""

    def test_settings_creation(self):
        """Test creating settings."""
        settings = QMNSettings(api_key="test_key_123")

        assert settings.api_key == "test_key_123"
        assert settings.api_base_url == "https://api.qilbee.network"
        assert settings.api_version == "v1"
        assert settings.transport_protocol == "grpc"

    def test_settings_api_url(self):
        """Test API URL property."""
        settings = QMNSettings(
            api_key="test",
            api_base_url="https://test.example.com",
            api_version="v2",
        )

        assert settings.api_url == "https://test.example.com/v2"

    def test_settings_from_env(self, monkeypatch):
        """Test creating settings from environment."""
        monkeypatch.setenv("QMN_API_KEY", "env_key_123")
        monkeypatch.setenv("QMN_API_BASE_URL", "https://custom.api.com")
        monkeypatch.setenv("QMN_PREFERRED_REGION", "eu-west-1")
        monkeypatch.setenv("QMN_DEBUG", "true")

        settings = QMNSettings.from_env()

        assert settings.api_key == "env_key_123"
        assert settings.api_base_url == "https://custom.api.com"
        assert settings.preferred_region == "eu-west-1"
        assert settings.debug is True

    def test_settings_from_env_missing_key(self, monkeypatch):
        """Test that missing API key raises error."""
        monkeypatch.delenv("QMN_API_KEY", raising=False)

        with pytest.raises(ValueError, match="QMN_API_KEY environment variable is required"):
            QMNSettings.from_env()

    def test_settings_validation(self):
        """Test settings validation."""
        settings = QMNSettings(api_key="test_key")

        # Should not raise
        settings.validate()

    def test_settings_invalid_transport(self):
        """Test invalid transport protocol."""
        settings = QMNSettings(
            api_key="test",
            transport_protocol="invalid",
        )

        with pytest.raises(ValueError, match="Invalid transport protocol"):
            settings.validate()

    def test_settings_invalid_timeout(self):
        """Test invalid timeout values."""
        settings = QMNSettings(
            api_key="test",
            connect_timeout=-1,
        )

        with pytest.raises(ValueError, match="Connect timeout must be positive"):
            settings.validate()
