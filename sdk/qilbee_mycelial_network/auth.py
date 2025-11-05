"""
Authentication handler for QMN API.

Manages API key authentication and header generation.
"""

from typing import Dict, Optional


class AuthHandler:
    """
    Handles API key authentication for QMN requests.

    Generates appropriate headers for authenticated requests.
    """

    def __init__(self, api_key: str, tenant_id: Optional[str] = None):
        """
        Initialize auth handler.

        Args:
            api_key: QMN API key
            tenant_id: Optional tenant ID for multi-tenant environments
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        self.api_key = api_key
        self.tenant_id = tenant_id

    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.

        Returns:
            Dictionary of HTTP headers for authentication
        """
        headers = {
            "X-API-Key": self.api_key,
            "X-QMN-Client": "qmn-sdk-python/0.1.0",
        }

        if self.tenant_id:
            headers["X-Tenant-ID"] = self.tenant_id

        return headers

    def validate_key_format(self) -> bool:
        """
        Validate API key format.

        Returns:
            True if key format is valid

        Note:
            QMN API keys should start with 'qmn_' prefix
        """
        return self.api_key.startswith("qmn_") and len(self.api_key) >= 32
