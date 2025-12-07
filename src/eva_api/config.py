"""Configuration settings for EVA API Platform.

Uses Pydantic Settings for environment variable management.
All sensitive values should be stored in Azure Key Vault.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "EVA API Platform"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # API Configuration
    api_prefix: str = "/api/v1"
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # Azure AD B2C (Citizen Authentication)
    azure_ad_b2c_tenant_id: str = ""
    azure_ad_b2c_client_id: str = ""
    azure_ad_b2c_client_secret: str = ""
    azure_ad_b2c_authority: str = ""
    azure_ad_b2c_scope: str = "openid profile email"

    # Azure Entra ID (Employee Authentication)
    azure_entra_tenant_id: str = ""
    azure_entra_client_id: str = ""
    azure_entra_client_secret: str = ""

    # JWT Configuration
    jwt_algorithm: str = "RS256"
    jwt_audience: str = ""
    jwt_issuer: str = ""

    # Azure Cosmos DB
    cosmos_db_endpoint: str = ""
    cosmos_db_key: str = ""
    cosmos_db_database: str = "eva_api"
    cosmos_db_container_api_keys: str = "api_keys"
    cosmos_db_container_audit_logs: str = "audit_logs"

    # Azure Blob Storage
    azure_storage_account_name: str = ""
    azure_storage_account_key: str = ""
    azure_storage_container_documents: str = "documents"

    # Azure OpenAI (Query Processing)
    azure_openai_endpoint: str = ""
    azure_openai_key: str = ""
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_deployment_name: str = "gpt-4"

    # Redis (Rate Limiting & Cache)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_ssl: bool = False

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_default: int = 60  # requests per minute

    # Security
    api_key_prefix: str = "sk_"
    api_key_length: int = 32
    require_https: bool = False

    # Observability
    otel_enabled: bool = False
    otel_endpoint: str = ""
    azure_monitor_connection_string: str = ""

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Settings: Application settings singleton
    """
    return Settings()
