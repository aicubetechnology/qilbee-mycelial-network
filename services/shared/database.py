"""
Database connection managers for PostgreSQL and MongoDB.

Provides connection pooling, health checks, and tenant isolation.
"""

import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any, List
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Base database manager interface."""

    async def connect(self) -> None:
        """Establish database connection."""
        raise NotImplementedError

    async def disconnect(self) -> None:
        """Close database connection."""
        raise NotImplementedError

    async def health_check(self) -> bool:
        """Check database health."""
        raise NotImplementedError


class PostgresManager(DatabaseManager):
    """
    PostgreSQL connection manager with pgvector support.

    Manages connection pooling and provides helper methods for
    common operations with tenant isolation.
    """

    def __init__(self, database_url: str, min_size: int = 10, max_size: int = 20):
        """
        Initialize Postgres manager.

        Args:
            database_url: PostgreSQL connection URL
            min_size: Minimum pool size
            max_size: Maximum pool size
        """
        self.database_url = database_url
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Establish connection pool."""
        if self.pool is not None:
            logger.warning("PostgreSQL pool already exists")
            return

        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=60,
        )
        logger.info(f"PostgreSQL pool created: {self.min_size}-{self.max_size} connections")

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL pool closed")

    async def health_check(self) -> bool:
        """Check database connectivity."""
        if self.pool is None:
            return False

        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False

    @asynccontextmanager
    async def acquire(self, tenant_id: Optional[str] = None):
        """
        Acquire connection with optional tenant context.

        Args:
            tenant_id: Tenant ID for row-level security

        Yields:
            Database connection
        """
        if self.pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")

        async with self.pool.acquire() as conn:
            # Set tenant context for RLS if provided
            if tenant_id:
                await conn.execute(f"SET app.tenant_id = '{tenant_id}'")

            try:
                yield conn
            finally:
                # Reset tenant context
                if tenant_id:
                    await conn.execute("RESET app.tenant_id")

    async def execute(
        self,
        query: str,
        *args,
        tenant_id: Optional[str] = None,
    ) -> str:
        """Execute query with optional tenant context."""
        async with self.acquire(tenant_id) as conn:
            return await conn.execute(query, *args)

    async def fetch(
        self,
        query: str,
        *args,
        tenant_id: Optional[str] = None,
    ) -> List[asyncpg.Record]:
        """Fetch multiple rows."""
        async with self.acquire(tenant_id) as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(
        self,
        query: str,
        *args,
        tenant_id: Optional[str] = None,
    ) -> Optional[asyncpg.Record]:
        """Fetch single row."""
        async with self.acquire(tenant_id) as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(
        self,
        query: str,
        *args,
        tenant_id: Optional[str] = None,
    ) -> Any:
        """Fetch single value."""
        async with self.acquire(tenant_id) as conn:
            return await conn.fetchval(query, *args)


class MongoManager(DatabaseManager):
    """
    MongoDB connection manager.

    Manages connection to MongoDB for agents, policies, and events.
    """

    def __init__(self, mongo_url: str, database: str = "qmn"):
        """
        Initialize MongoDB manager.

        Args:
            mongo_url: MongoDB connection URL
            database: Database name
        """
        self.mongo_url = mongo_url
        self.database_name = database
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self) -> None:
        """Establish MongoDB connection."""
        if self.client is not None:
            logger.warning("MongoDB client already exists")
            return

        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.database_name]
        logger.info(f"MongoDB connected to database: {self.database_name}")

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client is not None:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB connection closed")

    async def health_check(self) -> bool:
        """Check MongoDB connectivity."""
        if self.client is None:
            return False

        try:
            await self.client.admin.command("ping")
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False

    def get_collection(self, name: str):
        """Get collection by name."""
        if self.db is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self.db[name]

    async def find_one(
        self,
        collection: str,
        filter_dict: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find single document with tenant isolation."""
        if tenant_id:
            filter_dict["tenant_id"] = tenant_id

        coll = self.get_collection(collection)
        return await coll.find_one(filter_dict)

    async def find(
        self,
        collection: str,
        filter_dict: Dict[str, Any],
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Find multiple documents with tenant isolation."""
        if tenant_id:
            filter_dict["tenant_id"] = tenant_id

        coll = self.get_collection(collection)
        cursor = coll.find(filter_dict).limit(limit)
        return await cursor.to_list(length=limit)

    async def insert_one(
        self,
        collection: str,
        document: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> str:
        """Insert single document."""
        if tenant_id:
            document["tenant_id"] = tenant_id

        coll = self.get_collection(collection)
        result = await coll.insert_one(document)
        return str(result.inserted_id)

    async def update_one(
        self,
        collection: str,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> int:
        """Update single document."""
        if tenant_id:
            filter_dict["tenant_id"] = tenant_id

        coll = self.get_collection(collection)
        result = await coll.update_one(filter_dict, {"$set": update_dict})
        return result.modified_count

    async def delete_one(
        self,
        collection: str,
        filter_dict: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> int:
        """Delete single document."""
        if tenant_id:
            filter_dict["tenant_id"] = tenant_id

        coll = self.get_collection(collection)
        result = await coll.delete_one(filter_dict)
        return result.deleted_count
