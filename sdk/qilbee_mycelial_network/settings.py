"""
Configuration settings for QMN SDK.

Provides QMNSettings for configuring API endpoints, authentication,
timeouts, and SDK behavior.
"""

import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class QMNSettings:
    """
    Configuration settings for Mycelial Client.

    All settings can be configured via environment variables or constructor args.
    """

    # Authentication
    api_key: str
    tenant_id: Optional[str] = None

    # API Endpoints
    api_base_url: str = "https://qmn.qube.aicube.ca"
    api_version: str = "v1"

    # Timeouts (in seconds)
    connect_timeout: float = 10.0
    read_timeout: float = 30.0

    # Retry configuration
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    retry_max_delay: float = 60.0

    # Circuit breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0

    # Transport
    transport_protocol: str = "grpc"  # "grpc" or "quic"

    # Telemetry
    telemetry_enabled: bool = True
    telemetry_endpoint: Optional[str] = None

    # Regional preferences
    preferred_region: Optional[str] = None

    # SDK behavior
    auto_retry: bool = True
    verify_ssl: bool = True

    # Development
    debug: bool = False

    @classmethod
    def from_env(cls) -> "QMNSettings":
        """
        Create settings from environment variables.

        Required:
            QMN_API_KEY: API key for authentication

        Optional:
            QMN_API_BASE_URL: API base URL
            QMN_API_VERSION: API version
            QMN_CONNECT_TIMEOUT: Connection timeout in seconds
            QMN_READ_TIMEOUT: Read timeout in seconds
            QMN_MAX_RETRIES: Maximum retry attempts
            QMN_TRANSPORT: Transport protocol (grpc/quic)
            QMN_TELEMETRY_ENABLED: Enable telemetry (true/false)
            QMN_PREFERRED_REGION: Preferred region for routing
            QMN_DEBUG: Enable debug mode (true/false)
        """
        api_key = os.getenv("QMN_API_KEY")
        if not api_key:
            raise ValueError(
                "QMN_API_KEY environment variable is required. "
                "Get your API key from https://console.qilbee.network"
            )

        return cls(
            api_key=api_key,
            tenant_id=os.getenv("QMN_TENANT_ID"),
            api_base_url=os.getenv("QMN_API_BASE_URL", "https://qmn.qube.aicube.ca"),
            api_version=os.getenv("QMN_API_VERSION", "v1"),
            connect_timeout=float(os.getenv("QMN_CONNECT_TIMEOUT", "10.0")),
            read_timeout=float(os.getenv("QMN_READ_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("QMN_MAX_RETRIES", "3")),
            transport_protocol=os.getenv("QMN_TRANSPORT", "grpc"),
            telemetry_enabled=os.getenv("QMN_TELEMETRY_ENABLED", "true").lower() == "true",
            telemetry_endpoint=os.getenv("QMN_TELEMETRY_ENDPOINT"),
            preferred_region=os.getenv("QMN_PREFERRED_REGION"),
            debug=os.getenv("QMN_DEBUG", "false").lower() == "true",
        )

    @property
    def api_url(self) -> str:
        """Get full API URL."""
        return self.api_base_url

    def validate(self) -> None:
        """Validate settings."""
        if not self.api_key:
            raise ValueError("API key is required")

        if self.transport_protocol not in ("grpc", "quic"):
            raise ValueError(f"Invalid transport protocol: {self.transport_protocol}")

        if self.connect_timeout <= 0:
            raise ValueError("Connect timeout must be positive")

        if self.read_timeout <= 0:
            raise ValueError("Read timeout must be positive")

        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
