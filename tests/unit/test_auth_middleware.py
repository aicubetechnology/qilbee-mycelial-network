"""
Unit tests for authentication middleware and FastAPI dependencies.

Tests: get_validated_tenant, get_validated_admin, get_tenant_context, get_optional_tenant.
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))

from fastapi import HTTPException
from shared.auth import (
    get_validated_tenant,
    get_validated_admin,
    get_tenant_context,
    get_optional_tenant,
    require_scope,
    TenantContext,
    ADMIN_TENANT_ID,
)
import shared.auth as auth_module


class TestGetValidatedTenant:
    """Test get_validated_tenant dependency."""

    @pytest.mark.asyncio
    async def test_no_validator_raises_503(self):
        """Raises 503 if validator not initialized."""
        old_val = auth_module._validator
        auth_module._validator = None
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_validated_tenant(x_api_key="test-key")
            assert exc_info.value.status_code == 503
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_missing_key_raises_401(self):
        """Raises 401 if no API key provided."""
        mock_validator = MagicMock()
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_validated_tenant(x_api_key=None)
            assert exc_info.value.status_code == 401
            assert "Missing" in exc_info.value.detail
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_invalid_key_raises_401(self):
        """Raises 401 for invalid API key."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(return_value=(False, None, None, None, False))
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_validated_tenant(x_api_key="bad-key")
            assert exc_info.value.status_code == 401
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_valid_key_returns_tenant_id(self):
        """Returns tenant_id for valid API key."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(
            return_value=(True, "my-tenant", ["*"], 1000, False)
        )
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            tenant_id = await get_validated_tenant(x_api_key="valid-key")
            assert tenant_id == "my-tenant"
        finally:
            auth_module._validator = old_val


class TestGetValidatedAdmin:
    """Test get_validated_admin dependency."""

    @pytest.mark.asyncio
    async def test_no_validator_raises_503(self):
        """Raises 503 if validator not initialized."""
        old_val = auth_module._validator
        auth_module._validator = None
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_validated_admin(x_api_key="test-key")
            assert exc_info.value.status_code == 503
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_missing_key_raises_401(self):
        """Raises 401 if no API key provided."""
        mock_validator = MagicMock()
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_validated_admin(x_api_key=None)
            assert exc_info.value.status_code == 401
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_invalid_key_raises_401(self):
        """Raises 401 for invalid key."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(return_value=(False, None, None, None, False))
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_validated_admin(x_api_key="bad-key")
            assert exc_info.value.status_code == 401
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_non_admin_raises_403(self):
        """Raises 403 for non-admin key."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(
            return_value=(True, "regular-tenant", ["*"], 1000, False)
        )
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_validated_admin(x_api_key="regular-key")
            assert exc_info.value.status_code == 403
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_admin_key_returns_tenant_id(self):
        """Returns admin tenant_id for admin key."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(
            return_value=(True, ADMIN_TENANT_ID, ["*"], 10000, True)
        )
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            tenant_id = await get_validated_admin(x_api_key="admin-key")
            assert tenant_id == ADMIN_TENANT_ID
        finally:
            auth_module._validator = old_val


class TestGetTenantContext:
    """Test get_tenant_context dependency."""

    @pytest.mark.asyncio
    async def test_no_validator_raises_503(self):
        """Raises 503 if validator not initialized."""
        old_val = auth_module._validator
        auth_module._validator = None
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_tenant_context(x_api_key="test-key")
            assert exc_info.value.status_code == 503
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_missing_key_raises_401(self):
        """Raises 401 if no API key."""
        mock_validator = MagicMock()
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_tenant_context(x_api_key=None)
            assert exc_info.value.status_code == 401
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_invalid_key_raises_401(self):
        """Raises 401 for invalid key."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(return_value=(False, None, None, None, False))
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_tenant_context(x_api_key="bad-key")
            assert exc_info.value.status_code == 401
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_valid_key_returns_context(self):
        """Returns TenantContext for valid key."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(
            return_value=(True, "my-tenant", ["read", "write"], 1000, False)
        )
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            ctx = await get_tenant_context(x_api_key="valid-key")
            assert isinstance(ctx, TenantContext)
            assert ctx.tenant_id == "my-tenant"
            assert ctx.is_admin is False
            assert ctx.scopes == ["read", "write"]
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_admin_context(self):
        """Returns admin TenantContext for admin key."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(
            return_value=(True, ADMIN_TENANT_ID, ["*"], 10000, True)
        )
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            ctx = await get_tenant_context(x_api_key="admin-key")
            assert ctx.is_admin is True
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_null_scopes_default_to_empty(self):
        """Null scopes default to empty list."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(
            return_value=(True, "my-tenant", None, 1000, False)
        )
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            ctx = await get_tenant_context(x_api_key="valid-key")
            assert ctx.scopes == []
        finally:
            auth_module._validator = old_val


class TestRequireScope:
    """
    Test require_scope() dependency factory.

    Declarative scope gating (FastAPI's Depends()-based equivalent of
    Spring's @Scopes("a") annotation) - see /projects/guard_rails_protocol
    memory for the full design discussion.
    """

    def _ctx(self, scopes, is_admin=False, tenant_id="t1"):
        return TenantContext(tenant_id=tenant_id, is_admin=is_admin, scopes=scopes)

    def test_invalid_mode_raises_value_error(self):
        """mode must be 'any' or 'all' - fails fast, not at request time."""
        with pytest.raises(ValueError):
            require_scope("a", mode="bogus")

    @pytest.mark.asyncio
    async def test_single_scope_present_passes(self):
        checker = require_scope("memory:write:privileged")
        ctx = self._ctx(["memory:write:privileged", "other"])
        result = await checker(ctx=ctx)
        assert result is ctx

    @pytest.mark.asyncio
    async def test_single_scope_missing_raises_403(self):
        checker = require_scope("memory:write:privileged")
        ctx = self._ctx(["other"])
        with pytest.raises(HTTPException) as exc_info:
            await checker(ctx=ctx)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_any_mode_passes_with_one_of_many(self):
        """mode='any' (default): passes if ctx has AT LEAST ONE required scope."""
        checker = require_scope("a", "b", "c")  # default mode="any"
        ctx = self._ctx(["b"])  # only has "b", not "a" or "c"
        result = await checker(ctx=ctx)
        assert result is ctx

    @pytest.mark.asyncio
    async def test_any_mode_fails_with_none_matching(self):
        checker = require_scope("a", "b", "c", mode="any")
        ctx = self._ctx(["z"])
        with pytest.raises(HTTPException) as exc_info:
            await checker(ctx=ctx)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_all_mode_passes_only_with_every_scope(self):
        """mode='all': passes only if ctx has EVERY required scope."""
        checker = require_scope("a", "b", mode="all")
        ctx = self._ctx(["a", "b", "extra"])
        result = await checker(ctx=ctx)
        assert result is ctx

    @pytest.mark.asyncio
    async def test_all_mode_fails_if_missing_any_one(self):
        checker = require_scope("a", "b", mode="all")
        ctx = self._ctx(["a"])  # missing "b"
        with pytest.raises(HTTPException) as exc_info:
            await checker(ctx=ctx)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_bypasses_any_mode(self):
        checker = require_scope("a", "b", "c", mode="any")
        ctx = self._ctx([], is_admin=True)
        result = await checker(ctx=ctx)
        assert result is ctx

    @pytest.mark.asyncio
    async def test_admin_bypasses_all_mode(self):
        checker = require_scope("a", "b", "c", mode="all")
        ctx = self._ctx([], is_admin=True)
        result = await checker(ctx=ctx)
        assert result is ctx

    @pytest.mark.asyncio
    async def test_wildcard_scope_bypasses_all_mode(self):
        checker = require_scope("a", "b", "c", mode="all")
        ctx = self._ctx(["*"])
        result = await checker(ctx=ctx)
        assert result is ctx


class TestGetOptionalTenant:
    """Test get_optional_tenant dependency."""

    @pytest.mark.asyncio
    async def test_no_validator_returns_none(self):
        """Returns None if validator not initialized."""
        old_val = auth_module._validator
        auth_module._validator = None
        try:
            result = await get_optional_tenant(x_api_key="test-key")
            assert result is None
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_no_key_returns_none(self):
        """Returns None if no API key provided."""
        mock_validator = MagicMock()
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            result = await get_optional_tenant(x_api_key=None)
            assert result is None
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_valid_key_returns_tenant_id(self):
        """Returns tenant_id for valid key."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(
            return_value=(True, "my-tenant", ["*"], 1000, False)
        )
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            result = await get_optional_tenant(x_api_key="valid-key")
            assert result == "my-tenant"
        finally:
            auth_module._validator = old_val

    @pytest.mark.asyncio
    async def test_invalid_key_returns_none(self):
        """Returns None for invalid key."""
        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(
            return_value=(False, None, None, None, False)
        )
        old_val = auth_module._validator
        auth_module._validator = mock_validator
        try:
            result = await get_optional_tenant(x_api_key="bad-key")
            assert result is None
        finally:
            auth_module._validator = old_val
