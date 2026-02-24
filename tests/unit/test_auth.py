"""
Unit tests for authentication modules (both SDK and service-side).
"""

import pytest
import hashlib
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../sdk'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))

from qilbee_mycelial_network.auth import AuthHandler
from shared.auth import (
    APIKeyValidator,
    ADMIN_TENANT_ID,
    ADMIN_SCOPE,
    TenantContext,
    init_api_key_validator,
    get_validator,
)


class TestSDKAuthHandler:
    """Test SDK AuthHandler."""

    def test_init_with_valid_key(self):
        """Create auth handler with valid key."""
        handler = AuthHandler("qmn_test_key_abc123", tenant_id="test-tenant")
        assert handler.api_key == "qmn_test_key_abc123"
        assert handler.tenant_id == "test-tenant"

    def test_init_empty_key_raises(self):
        """Empty API key raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            AuthHandler("")

    def test_get_headers(self):
        """Get authentication headers."""
        handler = AuthHandler("qmn_key_abc", tenant_id="my-tenant")
        headers = handler.get_headers()

        assert headers["X-API-Key"] == "qmn_key_abc"
        assert headers["X-QMN-Client"] == "qmn-sdk-python/0.1.0"
        assert headers["X-Tenant-ID"] == "my-tenant"

    def test_get_headers_no_tenant(self):
        """Headers without tenant_id."""
        handler = AuthHandler("qmn_key_abc")
        headers = handler.get_headers()

        assert "X-API-Key" in headers
        assert "X-Tenant-ID" not in headers

    def test_validate_key_format_valid(self):
        """Valid key format passes."""
        handler = AuthHandler("qmn_" + "a" * 28)
        assert handler.validate_key_format() is True

    def test_validate_key_format_invalid_prefix(self):
        """Invalid prefix fails."""
        handler = AuthHandler("xxx_" + "a" * 28)
        assert handler.validate_key_format() is False

    def test_validate_key_format_too_short(self):
        """Too short key fails."""
        handler = AuthHandler("qmn_short")
        assert handler.validate_key_format() is False


class TestAPIKeyValidator:
    """Test service-side API key validator."""

    def test_hash_api_key(self):
        """Hash API key with SHA-256."""
        key = "test_api_key"
        expected = hashlib.sha256(key.encode()).hexdigest()
        assert APIKeyValidator.hash_api_key(key) == expected

    @pytest.mark.asyncio
    async def test_validate_empty_key(self):
        """Empty key returns invalid."""
        mock_db = MagicMock()
        validator = APIKeyValidator(mock_db)
        valid, tid, scopes, rl, admin = await validator.validate("")
        assert valid is False

    @pytest.mark.asyncio
    async def test_validate_key_not_found(self):
        """Non-existent key returns invalid."""
        mock_db = MagicMock()
        mock_db.fetchrow = AsyncMock(return_value=None)
        validator = APIKeyValidator(mock_db)
        valid, tid, scopes, rl, admin = await validator.validate("test_key")
        assert valid is False

    @pytest.mark.asyncio
    async def test_validate_expired_key(self):
        """Expired key returns invalid."""
        mock_db = MagicMock()
        mock_db.fetchrow = AsyncMock(return_value={
            "tenant_id": "test-tenant",
            "scopes": '["*"]',
            "rate_limit_per_minute": 1000,
            "status": "active",
            "expires_at": datetime.utcnow() - timedelta(hours=1),
            "id": "key-id",
        })
        validator = APIKeyValidator(mock_db)
        valid, tid, scopes, rl, admin = await validator.validate("test_key")
        assert valid is False

    @pytest.mark.asyncio
    async def test_validate_revoked_key(self):
        """Revoked key returns invalid."""
        mock_db = MagicMock()
        mock_db.fetchrow = AsyncMock(return_value={
            "tenant_id": "test-tenant",
            "scopes": '["*"]',
            "rate_limit_per_minute": 1000,
            "status": "revoked",
            "expires_at": None,
            "id": "key-id",
        })
        validator = APIKeyValidator(mock_db)
        valid, tid, scopes, rl, admin = await validator.validate("test_key")
        assert valid is False

    @pytest.mark.asyncio
    async def test_validate_active_key(self):
        """Active key returns valid with tenant info."""
        mock_db = MagicMock()
        mock_db.fetchrow = AsyncMock(return_value={
            "tenant_id": "test-tenant",
            "scopes": ["*"],
            "rate_limit_per_minute": 1000,
            "status": "active",
            "expires_at": None,
            "id": "key-id",
        })
        mock_db.execute = AsyncMock()
        validator = APIKeyValidator(mock_db)
        valid, tid, scopes, rl, admin = await validator.validate("test_key")
        assert valid is True
        assert tid == "test-tenant"
        assert rl == 1000

    @pytest.mark.asyncio
    async def test_validate_admin_key(self):
        """Admin tenant key is identified."""
        mock_db = MagicMock()
        mock_db.fetchrow = AsyncMock(return_value={
            "tenant_id": ADMIN_TENANT_ID,
            "scopes": ["*"],
            "rate_limit_per_minute": 10000,
            "status": "active",
            "expires_at": None,
            "id": "admin-key-id",
        })
        mock_db.execute = AsyncMock()
        validator = APIKeyValidator(mock_db)
        valid, tid, scopes, rl, admin = await validator.validate("admin_key")
        assert valid is True
        assert admin is True

    @pytest.mark.asyncio
    async def test_validate_db_error(self):
        """Database error returns invalid."""
        mock_db = MagicMock()
        mock_db.fetchrow = AsyncMock(side_effect=Exception("DB error"))
        validator = APIKeyValidator(mock_db)
        valid, tid, scopes, rl, admin = await validator.validate("test_key")
        assert valid is False


class TestTenantContext:
    """Test TenantContext."""

    def test_admin_can_access_any_tenant(self):
        """Admin can access any tenant's data."""
        ctx = TenantContext("admin-id", is_admin=True, scopes=["*"])
        assert ctx.can_access_tenant("other-tenant") is True

    def test_non_admin_can_access_own_tenant(self):
        """Non-admin can access own tenant."""
        ctx = TenantContext("my-tenant", is_admin=False, scopes=["*"])
        assert ctx.can_access_tenant("my-tenant") is True

    def test_non_admin_cannot_access_other_tenant(self):
        """Non-admin cannot access other tenant."""
        ctx = TenantContext("my-tenant", is_admin=False, scopes=["*"])
        assert ctx.can_access_tenant("other-tenant") is False


class TestValidatorInit:
    """Test validator initialization."""

    def test_init_validator(self):
        """Can initialize validator."""
        mock_db = MagicMock()
        init_api_key_validator(mock_db)
        validator = get_validator()
        assert validator is not None

    def test_get_validator_before_init(self):
        """Getting validator before init raises 503."""
        from shared import auth
        old_val = auth._validator
        auth._validator = None
        try:
            from fastapi import HTTPException
            with pytest.raises(HTTPException):
                get_validator()
        finally:
            auth._validator = old_val
