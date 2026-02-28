"""
Unit tests for database connection managers.

Tests: PostgresManager, MongoManager with mocked connections.
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))

from shared.database import DatabaseManager, PostgresManager, MongoManager


class TestDatabaseManagerInterface:
    """Test base DatabaseManager interface."""

    @pytest.mark.asyncio
    async def test_connect_not_implemented(self):
        """Base connect raises NotImplementedError."""
        mgr = DatabaseManager()
        with pytest.raises(NotImplementedError):
            await mgr.connect()

    @pytest.mark.asyncio
    async def test_disconnect_not_implemented(self):
        """Base disconnect raises NotImplementedError."""
        mgr = DatabaseManager()
        with pytest.raises(NotImplementedError):
            await mgr.disconnect()

    @pytest.mark.asyncio
    async def test_health_check_not_implemented(self):
        """Base health_check raises NotImplementedError."""
        mgr = DatabaseManager()
        with pytest.raises(NotImplementedError):
            await mgr.health_check()


class TestPostgresManager:
    """Test PostgresManager with mocked asyncpg."""

    def test_init(self):
        """Postgres manager initializes with URL and pool config."""
        mgr = PostgresManager("postgres://localhost/test", min_size=5, max_size=10)
        assert mgr.database_url == "postgres://localhost/test"
        assert mgr.min_size == 5
        assert mgr.max_size == 10
        assert mgr.pool is None

    @pytest.mark.asyncio
    async def test_connect(self):
        """Connect creates connection pool."""
        mgr = PostgresManager("postgres://localhost/test")
        mock_pool = AsyncMock()
        with patch('shared.database.asyncpg.create_pool', new_callable=AsyncMock, return_value=mock_pool):
            await mgr.connect()
            assert mgr.pool is mock_pool

    @pytest.mark.asyncio
    async def test_connect_already_connected(self):
        """Connect skips if pool exists."""
        mgr = PostgresManager("postgres://localhost/test")
        mgr.pool = MagicMock()
        # Should not raise, just log warning
        await mgr.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Disconnect closes pool."""
        mgr = PostgresManager("postgres://localhost/test")
        mock_pool = AsyncMock()
        mgr.pool = mock_pool
        await mgr.disconnect()
        mock_pool.close.assert_awaited_once()
        assert mgr.pool is None

    @pytest.mark.asyncio
    async def test_disconnect_no_pool(self):
        """Disconnect does nothing without pool."""
        mgr = PostgresManager("postgres://localhost/test")
        await mgr.disconnect()  # Should not raise

    @pytest.mark.asyncio
    async def test_health_check_no_pool(self):
        """Health check returns False without pool."""
        mgr = PostgresManager("postgres://localhost/test")
        assert await mgr.health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Health check returns True on valid connection."""
        mgr = PostgresManager("postgres://localhost/test")
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextManagerMock(mock_conn))
        mgr.pool = mock_pool

        result = await mgr.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Health check returns False on error."""
        mgr = PostgresManager("postgres://localhost/test")
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(side_effect=Exception("Connection refused"))
        mgr.pool = mock_pool

        result = await mgr.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_no_pool_raises(self):
        """Acquire raises RuntimeError without pool."""
        mgr = PostgresManager("postgres://localhost/test")
        with pytest.raises(RuntimeError, match="not initialized"):
            async with mgr.acquire():
                pass

    @pytest.mark.asyncio
    async def test_acquire_with_tenant(self):
        """Acquire sets tenant context for RLS."""
        mgr = PostgresManager("postgres://localhost/test")
        mock_conn = AsyncMock()

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextManagerMock(mock_conn))
        mgr.pool = mock_pool

        async with mgr.acquire(tenant_id="test-tenant") as conn:
            assert conn is mock_conn

        # Verify tenant context was set and reset
        mock_conn.execute.assert_any_await("SET app.tenant_id = 'test-tenant'")
        mock_conn.execute.assert_any_await("RESET app.tenant_id")

    @pytest.mark.asyncio
    async def test_execute(self):
        """Execute runs query through pool."""
        mgr = PostgresManager("postgres://localhost/test")
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="INSERT 0 1")

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextManagerMock(mock_conn))
        mgr.pool = mock_pool

        result = await mgr.execute("INSERT INTO test VALUES ($1)", "value")
        assert result == "INSERT 0 1"

    @pytest.mark.asyncio
    async def test_fetch(self):
        """Fetch returns multiple rows."""
        mgr = PostgresManager("postgres://localhost/test")
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{"id": 1}, {"id": 2}])

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextManagerMock(mock_conn))
        mgr.pool = mock_pool

        result = await mgr.fetch("SELECT * FROM test")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetchrow(self):
        """Fetchrow returns single row."""
        mgr = PostgresManager("postgres://localhost/test")
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"id": 1, "name": "test"})

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextManagerMock(mock_conn))
        mgr.pool = mock_pool

        result = await mgr.fetchrow("SELECT * FROM test WHERE id = $1", 1)
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_fetchval(self):
        """Fetchval returns single value."""
        mgr = PostgresManager("postgres://localhost/test")
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=42)

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncContextManagerMock(mock_conn))
        mgr.pool = mock_pool

        result = await mgr.fetchval("SELECT COUNT(*) FROM test")
        assert result == 42


class TestMongoManager:
    """Test MongoManager with mocked motor client."""

    def test_init(self):
        """Mongo manager initializes with URL."""
        mgr = MongoManager("mongodb://localhost:27017", database="test_db")
        assert mgr.mongo_url == "mongodb://localhost:27017"
        assert mgr.database_name == "test_db"
        assert mgr.client is None

    @pytest.mark.asyncio
    async def test_connect(self):
        """Connect creates motor client."""
        mgr = MongoManager("mongodb://localhost:27017")
        with patch('shared.database.AsyncIOMotorClient') as mock_cls:
            mock_client = MagicMock()
            mock_client.__getitem__ = MagicMock(return_value=MagicMock())
            mock_cls.return_value = mock_client
            await mgr.connect()
            assert mgr.client is mock_client
            assert mgr.db is not None

    @pytest.mark.asyncio
    async def test_connect_already_connected(self):
        """Connect skips if client exists."""
        mgr = MongoManager("mongodb://localhost:27017")
        mgr.client = MagicMock()
        await mgr.connect()  # Should not raise

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Disconnect closes client."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_client = MagicMock()
        mgr.client = mock_client
        mgr.db = MagicMock()
        await mgr.disconnect()
        mock_client.close.assert_called_once()
        assert mgr.client is None
        assert mgr.db is None

    @pytest.mark.asyncio
    async def test_disconnect_no_client(self):
        """Disconnect does nothing without client."""
        mgr = MongoManager("mongodb://localhost:27017")
        await mgr.disconnect()  # Should not raise

    @pytest.mark.asyncio
    async def test_health_check_no_client(self):
        """Health check returns False without client."""
        mgr = MongoManager("mongodb://localhost:27017")
        assert await mgr.health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Health check returns True on successful ping."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_client = MagicMock()
        mock_admin = AsyncMock()
        mock_client.admin = mock_admin
        mock_admin.command = AsyncMock(return_value={"ok": 1})
        mgr.client = mock_client
        assert await mgr.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Health check returns False on error."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_client = MagicMock()
        mock_admin = AsyncMock()
        mock_client.admin = mock_admin
        mock_admin.command = AsyncMock(side_effect=Exception("Connection refused"))
        mgr.client = mock_client
        assert await mgr.health_check() is False

    def test_get_collection_no_db(self):
        """Get collection raises without DB."""
        mgr = MongoManager("mongodb://localhost:27017")
        with pytest.raises(RuntimeError, match="not initialized"):
            mgr.get_collection("test")

    def test_get_collection(self):
        """Get collection returns collection."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value="test_collection")
        mgr.db = mock_db
        result = mgr.get_collection("test")
        assert result == "test_collection"

    @pytest.mark.asyncio
    async def test_find_one(self):
        """Find one document."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_coll = AsyncMock()
        mock_coll.find_one = AsyncMock(return_value={"_id": "1", "name": "test"})
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_coll)
        mgr.db = mock_db

        result = await mgr.find_one("agents", {"_id": "1"})
        assert result["name"] == "test"

    @pytest.mark.asyncio
    async def test_find_one_with_tenant(self):
        """Find one adds tenant_id to filter."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_coll = AsyncMock()
        mock_coll.find_one = AsyncMock(return_value=None)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_coll)
        mgr.db = mock_db

        await mgr.find_one("agents", {"_id": "1"}, tenant_id="t1")
        call_args = mock_coll.find_one.call_args
        assert call_args[0][0]["tenant_id"] == "t1"

    @pytest.mark.asyncio
    async def test_find(self):
        """Find multiple documents."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[{"_id": "1"}, {"_id": "2"}])

        mock_find_result = MagicMock()
        mock_find_result.limit = MagicMock(return_value=mock_cursor)

        mock_coll = MagicMock()
        mock_coll.find = MagicMock(return_value=mock_find_result)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_coll)
        mgr.db = mock_db

        result = await mgr.find("agents", {}, limit=10)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_find_with_tenant(self):
        """Find adds tenant_id to filter."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])

        mock_find_result = MagicMock()
        mock_find_result.limit = MagicMock(return_value=mock_cursor)

        mock_coll = MagicMock()
        mock_coll.find = MagicMock(return_value=mock_find_result)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_coll)
        mgr.db = mock_db

        await mgr.find("agents", {"status": "active"}, tenant_id="t1")
        call_args = mock_coll.find.call_args
        assert call_args[0][0]["tenant_id"] == "t1"

    @pytest.mark.asyncio
    async def test_insert_one(self):
        """Insert one document."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_result = MagicMock()
        mock_result.inserted_id = "new-id"
        mock_coll = AsyncMock()
        mock_coll.insert_one = AsyncMock(return_value=mock_result)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_coll)
        mgr.db = mock_db

        result = await mgr.insert_one("agents", {"name": "test"})
        assert result == "new-id"

    @pytest.mark.asyncio
    async def test_insert_one_with_tenant(self):
        """Insert adds tenant_id to document."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_result = MagicMock()
        mock_result.inserted_id = "new-id"
        mock_coll = AsyncMock()
        mock_coll.insert_one = AsyncMock(return_value=mock_result)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_coll)
        mgr.db = mock_db

        await mgr.insert_one("agents", {"name": "test"}, tenant_id="t1")
        call_args = mock_coll.insert_one.call_args
        assert call_args[0][0]["tenant_id"] == "t1"

    @pytest.mark.asyncio
    async def test_update_one(self):
        """Update one document."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_coll = AsyncMock()
        mock_coll.update_one = AsyncMock(return_value=mock_result)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_coll)
        mgr.db = mock_db

        result = await mgr.update_one("agents", {"_id": "1"}, {"name": "updated"})
        assert result == 1

    @pytest.mark.asyncio
    async def test_update_one_with_tenant(self):
        """Update adds tenant_id to filter."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_coll = AsyncMock()
        mock_coll.update_one = AsyncMock(return_value=mock_result)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_coll)
        mgr.db = mock_db

        await mgr.update_one("agents", {"_id": "1"}, {"name": "updated"}, tenant_id="t1")
        call_args = mock_coll.update_one.call_args
        assert call_args[0][0]["tenant_id"] == "t1"

    @pytest.mark.asyncio
    async def test_delete_one(self):
        """Delete one document."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_coll = AsyncMock()
        mock_coll.delete_one = AsyncMock(return_value=mock_result)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_coll)
        mgr.db = mock_db

        result = await mgr.delete_one("agents", {"_id": "1"})
        assert result == 1

    @pytest.mark.asyncio
    async def test_delete_one_with_tenant(self):
        """Delete adds tenant_id to filter."""
        mgr = MongoManager("mongodb://localhost:27017")
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_coll = AsyncMock()
        mock_coll.delete_one = AsyncMock(return_value=mock_result)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_coll)
        mgr.db = mock_db

        await mgr.delete_one("agents", {"_id": "1"}, tenant_id="t1")
        call_args = mock_coll.delete_one.call_args
        assert call_args[0][0]["tenant_id"] == "t1"


class AsyncContextManagerMock:
    """Helper to mock async context managers."""
    def __init__(self, return_value):
        self._return_value = return_value

    async def __aenter__(self):
        return self._return_value

    async def __aexit__(self, *args):
        pass
