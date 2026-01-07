"""
Authentication utilities for QMN services.

Provides API key validation and tenant extraction.
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional, Tuple, List
from fastapi import HTTPException, Header, Depends, status

logger = logging.getLogger(__name__)


class APIKeyValidator:
    """Validates API keys against the database."""

    def __init__(self, postgres_manager):
        """
        Initialize validator with database connection.

        Args:
            postgres_manager: PostgresManager instance for database queries
        """
        self.db = postgres_manager

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key using SHA-256."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def validate(self, api_key: str) -> Tuple[bool, Optional[str], Optional[List[str]], Optional[int]]:
        """
        Validate an API key and return tenant info.

        Args:
            api_key: The API key to validate

        Returns:
            Tuple of (valid, tenant_id, scopes, rate_limit_per_minute)
        """
        if not api_key:
            return False, None, None, None

        key_hash = self.hash_api_key(api_key)

        try:
            result = await self.db.fetchrow(
                """
                SELECT k.tenant_id, k.scopes, k.rate_limit_per_minute, k.status, k.expires_at, k.id
                FROM api_keys k
                JOIN tenants t ON k.tenant_id = t.id
                WHERE k.key_hash = $1 AND t.status = 'active'
                """,
                key_hash,
            )

            if not result:
                logger.warning(f"API key not found: {api_key[:12]}...")
                return False, None, None, None

            # Check if expired
            if result["expires_at"] and result["expires_at"] < datetime.utcnow():
                logger.warning(f"API key expired: {api_key[:12]}...")
                return False, None, None, None

            # Check if revoked
            if result["status"] != "active":
                logger.warning(f"API key not active: {api_key[:12]}... (status: {result['status']})")
                return False, None, None, None

            # Update last_used_at
            await self.db.execute(
                "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1",
                result["id"],
            )

            # Parse scopes if needed
            scopes = result["scopes"]
            if isinstance(scopes, str):
                import json
                scopes = json.loads(scopes)

            logger.debug(f"API key validated for tenant: {result['tenant_id']}")
            return True, result["tenant_id"], scopes, result["rate_limit_per_minute"]

        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return False, None, None, None


# Global validator instance (set by each service on startup)
_validator: Optional[APIKeyValidator] = None


def init_api_key_validator(postgres_manager):
    """
    Initialize the global API key validator.

    Call this during service startup after database connection is established.

    Args:
        postgres_manager: PostgresManager instance
    """
    global _validator
    _validator = APIKeyValidator(postgres_manager)
    logger.info("API key validator initialized")


async def get_validated_tenant(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    """
    FastAPI dependency to validate API key and extract tenant_id.

    Usage:
        @app.post("/endpoint")
        async def endpoint(tenant_id: str = Depends(get_validated_tenant)):
            # tenant_id is now the validated tenant

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Validated tenant_id

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if _validator is None:
        logger.error("API key validator not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    valid, tenant_id, scopes, rate_limit = await _validator.validate(x_api_key)

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return tenant_id


async def get_optional_tenant(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[str]:
    """
    FastAPI dependency for optional API key validation.

    Returns tenant_id if valid key provided, None otherwise.
    Does not raise exceptions for missing/invalid keys.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Validated tenant_id or None
    """
    if _validator is None or not x_api_key:
        return None

    valid, tenant_id, _, _ = await _validator.validate(x_api_key)
    return tenant_id if valid else None
