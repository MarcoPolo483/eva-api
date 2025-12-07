"""Tests for configuration settings."""

import pytest

from eva_api.config import Settings, get_settings


def test_default_settings() -> None:
    """Test that default settings are loaded correctly."""
    settings = Settings()
    
    assert settings.app_name == "EVA API Platform"
    assert settings.app_version == "1.0.0"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.log_level == "INFO"


def test_settings_environment_variables(monkeypatch) -> None:
    """Test that environment variables override defaults."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    
    settings = Settings()
    
    assert settings.environment == "production"
    assert settings.debug is True
    assert settings.log_level == "ERROR"


def test_settings_is_development() -> None:
    """Test is_development property."""
    settings = Settings(environment="development")
    assert settings.is_development is True
    
    settings = Settings(environment="production")
    assert settings.is_development is False


def test_settings_is_production() -> None:
    """Test is_production property."""
    settings = Settings(environment="production")
    assert settings.is_production is True
    
    settings = Settings(environment="development")
    assert settings.is_production is False


def test_settings_cors_origins_from_string() -> None:
    """Test parsing CORS origins from comma-separated string."""
    settings = Settings(allowed_origins="http://localhost:3000,http://localhost:8000,https://app.eva.ai")
    
    assert len(settings.allowed_origins) == 3
    assert "http://localhost:3000" in settings.allowed_origins
    assert "http://localhost:8000" in settings.allowed_origins
    assert "https://app.eva.ai" in settings.allowed_origins


def test_settings_cors_origins_from_list() -> None:
    """Test CORS origins as list."""
    origins = ["http://localhost:3000", "http://localhost:8000"]
    settings = Settings(allowed_origins=origins)
    
    assert settings.allowed_origins == origins


def test_get_settings_cached() -> None:
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    
    assert settings1 is settings2


def test_settings_api_key_defaults() -> None:
    """Test API key configuration defaults."""
    settings = Settings()
    
    assert settings.api_key_prefix == "sk_"
    assert settings.api_key_length == 32


def test_settings_rate_limiting_defaults() -> None:
    """Test rate limiting configuration defaults."""
    settings = Settings()
    
    assert settings.rate_limit_enabled is True
    assert settings.rate_limit_default == 60


def test_settings_redis_defaults() -> None:
    """Test Redis configuration defaults."""
    settings = Settings()
    
    assert settings.redis_host == "localhost"
    assert settings.redis_port == 6379
    assert settings.redis_db == 0
    assert settings.redis_ssl is False
