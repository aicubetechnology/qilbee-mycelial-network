"""
Unit tests for startup initialization module.

Tests: admin tenant creation, bootstrap key generation, idempotency.
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))

from shared.startup import (
    generate_api_key,
    initialize_admin_tenant,
    bootstrap_admin_key,
    ensure_admin_initialized,
)
from shared.auth import ADMIN_TENANT_ID


class TestGenerateAPIKey:
    """Test API key generation."""

    def test_key_has_prefix(self):
        """Generated key has qmn_ prefix."""
        key, key_hash = generate_api_key()
        assert key.startswith("qmn_")

    def test_key_length(self):
        """Generated key is 47 characters (4 prefix + 43 random)."""
        key, key_hash = generate_api_key()
        assert len(key) == 47

    def test_hash_is_sha256(self):
        """Hash is SHA-256 hex digest."""
        key, key_hash = generate_api_key()
        assert len(key_hash) == 64  # SHA-256 hex

    def test_unique_keys(self):
        """Each generation produces unique keys."""
        key1, _ = generate_api_key()
        key2, _ = generate_api_key()
        assert key1 != key2

    def test_hash_matches_key(self):
        """Hash is derived from the key."""
        import hashlib
        key, key_hash = generate_api_key()
        expected = hashlib.sha256(key.encode()).hexdigest()
        assert key_hash == expected


class TestInitializeAdminTenant:
    """Test admin tenant initialization."""

    @pytest.mark.asyncio
    async def test_creates_tenant_on_fresh_startup(self):
        """Creates admin tenant when it doesn't exist."""
        mock_pg = AsyncMock()
        mock_pg.fetchrow = AsyncMock(return_value=None)
        mock_pg.execute = AsyncMock()

        result = await initialize_admin_tenant(mock_pg)
        assert result is True
        mock_pg.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skips_if_already_exists(self):
        """Skips if admin tenant already exists."""
        mock_pg = AsyncMock()
        mock_pg.fetchrow = AsyncMock(return_value={"id": ADMIN_TENANT_ID})

        result = await initialize_admin_tenant(mock_pg)
        assert result is False
        mock_pg.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_raises_on_db_error(self):
        """Raises exception on database error."""
        mock_pg = AsyncMock()
        mock_pg.fetchrow = AsyncMock(side_effect=Exception("DB error"))

        with pytest.raises(Exception, match="DB error"):
            await initialize_admin_tenant(mock_pg)


class TestBootstrapAdminKey:
    """Test admin key bootstrap."""

    @pytest.mark.asyncio
    async def test_creates_key_on_fresh_bootstrap(self):
        """Creates admin key when none exist."""
        mock_pg = AsyncMock()
        mock_pg.fetchval = AsyncMock(return_value=0)
        mock_pg.fetchrow = AsyncMock(return_value={"id": ADMIN_TENANT_ID})
        mock_pg.execute = AsyncMock()

        result = await bootstrap_admin_key(mock_pg)
        assert result is not None
        assert result.startswith("qmn_")
        mock_pg.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_if_keys_exist(self):
        """Returns None if admin already has keys."""
        mock_pg = AsyncMock()
        mock_pg.fetchval = AsyncMock(return_value=1)

        result = await bootstrap_admin_key(mock_pg)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_if_no_tenant(self):
        """Returns None if admin tenant doesn't exist."""
        mock_pg = AsyncMock()
        mock_pg.fetchval = AsyncMock(return_value=0)
        mock_pg.fetchrow = AsyncMock(return_value=None)

        result = await bootstrap_admin_key(mock_pg)
        assert result is None

    @pytest.mark.asyncio
    async def test_raises_on_db_error(self):
        """Raises exception on database error."""
        mock_pg = AsyncMock()
        mock_pg.fetchval = AsyncMock(side_effect=Exception("DB error"))

        with pytest.raises(Exception, match="DB error"):
            await bootstrap_admin_key(mock_pg)


class TestEnsureAdminInitialized:
    """Test ensure_admin_initialized."""

    @pytest.mark.asyncio
    async def test_fresh_startup_logs_instructions(self):
        """Fresh startup logs bootstrap instructions."""
        mock_pg = AsyncMock()
        mock_pg.fetchrow = AsyncMock(return_value=None)
        mock_pg.execute = AsyncMock()

        # Should complete without error
        await ensure_admin_initialized(mock_pg)

    @pytest.mark.asyncio
    async def test_existing_tenant_no_instructions(self):
        """Existing tenant skips instructions."""
        mock_pg = AsyncMock()
        mock_pg.fetchrow = AsyncMock(return_value={"id": ADMIN_TENANT_ID})

        await ensure_admin_initialized(mock_pg)
        mock_pg.execute.assert_not_awaited()
