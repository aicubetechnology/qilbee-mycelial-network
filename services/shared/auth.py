"""
Authentication utilities for QMN services.

Provides API key validation, tenant extraction, and admin access control.
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional, Tuple, List
from fastapi import HTTPException, Header, Depends, status

logger = logging.getLogger(__name__)

# AIcube Technology LLC - Global Admin Tenant
# This tenant has administrative privileges across the entire system
ADMIN_TENANT_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_TENANT_NAME = "AIcube Technology LLC"
ADMIN_SCOPE = "admin:*"


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

    async def validate(self, api_key: str) -> Tuple[bool, Optional[str], Optional[List[str]], Optional[int], bool]:
        """
        Validate an API key and return tenant info.

        Args:
            api_key: The API key to validate

        Returns:
            Tuple of (valid, tenant_id, scopes, rate_limit_per_minute, is_admin)
        """
        if not api_key:
            return False, None, None, None, False

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
                return False, None, None, None, False

            # Check if expired
            if result["expires_at"] and result["expires_at"] < datetime.utcnow():
                logger.warning(f"API key expired: {api_key[:12]}...")
                return False, None, None, None, False

            # Check if revoked
            if result["status"] != "active":
                logger.warning(f"API key not active: {api_key[:12]}... (status: {result['status']})")
                return False, None, None, None, False

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

            # Check if this is an admin key
            is_admin = (
                result["tenant_id"] == ADMIN_TENANT_ID or
                ADMIN_SCOPE in (scopes or [])
            )

            logger.debug(f"API key validated for tenant: {result['tenant_id']} (admin: {is_admin})")
            return True, result["tenant_id"], scopes, result["rate_limit_per_minute"], is_admin

        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return False, None, None, None, False


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


def get_validator() -> APIKeyValidator:
    """Get the global validator instance."""
    if _validator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available",
        )
    return _validator


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

    valid, tenant_id, scopes, rate_limit, is_admin = await _validator.validate(x_api_key)

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return tenant_id


async def get_validated_admin(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    """
    FastAPI dependency to validate API key and require admin privileges.

    Only AIcube Technology LLC API keys can access admin endpoints.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Validated admin tenant_id

    Raises:
        HTTPException: If API key is missing, invalid, or not admin
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

    valid, tenant_id, scopes, rate_limit, is_admin = await _validator.validate(x_api_key)

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not is_admin:
        logger.warning(f"Non-admin tenant {tenant_id} attempted admin access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required. Only AIcube Technology LLC keys can access this endpoint.",
        )

    return tenant_id


class TenantContext:
    """Context object containing tenant info and admin status."""
    def __init__(self, tenant_id: str, is_admin: bool, scopes: List[str]):
        self.tenant_id = tenant_id
        self.is_admin = is_admin
        self.scopes = scopes

    def can_access_tenant(self, target_tenant_id: str) -> bool:
        """Check if this context can access another tenant's data."""
        return self.is_admin or self.tenant_id == target_tenant_id


async def get_tenant_context(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> TenantContext:
    """
    FastAPI dependency to get full tenant context including admin status.

    Useful for endpoints where admin can access any tenant's data.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        TenantContext with tenant_id, is_admin, and scopes

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

    valid, tenant_id, scopes, rate_limit, is_admin = await _validator.validate(x_api_key)

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return TenantContext(tenant_id=tenant_id, is_admin=is_admin, scopes=scopes or [])


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

    valid, tenant_id, _, _, _ = await _validator.validate(x_api_key)
    return tenant_id if valid else None
