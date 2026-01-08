"""
Hyphal Memory Service - Vector Memory Storage & Search

Provides distributed vector memory storage and semantic search capabilities.
Stores insights, snippets, tool hints, and agent knowledge with embeddings.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import sys
import uuid

sys.path.append("../..")
from shared.database import PostgresManager
from shared.models import ServiceHealth, HealthResponse
from shared.auth import init_api_key_validator, get_validated_tenant, get_validated_admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="QMN Hyphal Memory Service",
    description="Vector memory storage and semantic search",
    version="0.1.0",
)

postgres_db: Optional[PostgresManager] = None


# Request/Response Models
# Valid memory kinds (extensible list)
VALID_KINDS = {"insight", "snippet", "tool_hint", "plan", "outcome", "result", "task", "context", "memory", "agent_result"}
VALID_SENSITIVITIES = {"public", "internal", "confidential", "secret"}


class StoreMemoryRequest(BaseModel):
    """Request to store memory.

    Accepts various memory kinds for flexibility.
    """

    agent_id: str
    kind: str
    content: Dict[str, Any]
    embedding: List[float]
    quality: float = Field(default=0.5, ge=0.0, le=1.0)
    sensitivity: str = Field(default="internal")
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    ttl_hours: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context):
        """Validate fields with better error messages."""
        # Validate embedding size
        if len(self.embedding) != 1536:
            raise ValueError(f"embedding must have exactly 1536 dimensions, got {len(self.embedding)}")

        # Normalize kind (lowercase)
        kind_lower = self.kind.lower()
        if kind_lower not in VALID_KINDS:
            logger.warning(f"Unknown memory kind '{self.kind}', allowing anyway")

        # Normalize sensitivity (lowercase)
        sensitivity_lower = self.sensitivity.lower()
        if sensitivity_lower not in VALID_SENSITIVITIES:
            raise ValueError(
                f"sensitivity must be one of {VALID_SENSITIVITIES}, got '{self.sensitivity}'"
            )


class MemoryResponse(BaseModel):
    """Memory record response."""

    id: str
    agent_id: str
    kind: str
    content: Dict[str, Any]
    quality: float
    sensitivity: str
    created_at: datetime
    expires_at: Optional[datetime]


class SearchRequest(BaseModel):
    """Request for vector similarity search.

    Supports two formats:
    1. Direct filters: {"kind_filter": "insight", "agent_filter": "agent-001"}
    2. SDK filters dict: {"filters": {"kind": "insight", "agent_id": "agent-001"}}
    """

    embedding: List[float]
    top_k: int = Field(default=10, ge=1, le=100)
    min_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    kind_filter: Optional[str] = None
    agent_filter: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None  # SDK format

    def model_post_init(self, __context):
        """Validate embedding and extract filters."""
        # Validate embedding size
        if len(self.embedding) != 1536:
            raise ValueError(f"embedding must have exactly 1536 dimensions, got {len(self.embedding)}")

        # Extract filters from SDK format if provided
        if self.filters:
            if not self.kind_filter and "kind" in self.filters:
                object.__setattr__(self, "kind_filter", self.filters["kind"])
            if not self.agent_filter and "agent_id" in self.filters:
                object.__setattr__(self, "agent_filter", self.filters["agent_id"])
            # Also check for quality filter
            if "quality" in self.filters and isinstance(self.filters["quality"], dict):
                if "$gt" in self.filters["quality"]:
                    object.__setattr__(self, "min_quality", self.filters["quality"]["$gt"])


class SearchResult(BaseModel):
    """Single search result."""

    id: str
    agent_id: str
    kind: str
    content: Dict[str, Any]
    similarity: float
    quality: float
    created_at: datetime


class SearchResponse(BaseModel):
    """Search results response."""

    results: List[SearchResult]
    total: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Lifecycle
@app.on_event("startup")
async def startup():
    """Initialize database."""
    global postgres_db
    import os

    postgres_url = os.getenv(
        "POSTGRES_URL", "postgresql://postgres:dev_password@localhost:5432/qmn"
    )
    postgres_db = PostgresManager(postgres_url)
    await postgres_db.connect()

    # Initialize API key validator
    init_api_key_validator(postgres_db)

    logger.info("Hyphal Memory service started")


@app.on_event("shutdown")
async def shutdown():
    """Close database."""
    if postgres_db:
        await postgres_db.disconnect()
    logger.info("Hyphal Memory service stopped")


async def get_postgres() -> PostgresManager:
    """Get PostgreSQL manager."""
    if postgres_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL not available",
        )
    return postgres_db


# Note: get_validated_tenant from shared.auth is used for API key validation


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check(postgres: PostgresManager = Depends(get_postgres)):
    """Check service health."""
    postgres_healthy = await postgres.health_check()
    health_status = ServiceHealth.HEALTHY if postgres_healthy else ServiceHealth.UNHEALTHY

    return HealthResponse(
        status=health_status,
        service="hyphal_memory",
        region="us-east-1",
        checks={"postgres": postgres_healthy},
    )


@app.post("/v1/hyphal:store", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def store_memory(
    request: StoreMemoryRequest,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    Store memory in hyphal network.

    Saves agent knowledge, insights, or context with vector embedding
    for future semantic search and retrieval.

    Requires valid API key in X-API-Key header.

    Args:
        request: Memory storage request
        tenant_id: Extracted from validated API key

    Returns:
        Stored memory information
    """
    try:

        # Calculate expiration if TTL provided
        expires_at = None
        if request.ttl_hours:
            expires_at = datetime.utcnow() + timedelta(hours=request.ttl_hours)

        # Insert memory
        # Convert types for PostgreSQL
        import json as json_lib
        embedding_str = "[" + ",".join(str(x) for x in request.embedding) + "]"
        content_json = json_lib.dumps(request.content)
        metadata_json = json_lib.dumps(request.metadata)

        result = await postgres.fetchrow(
            """
            INSERT INTO hyphal_memory (
                tenant_id, agent_id, task_id, trace_id, kind, content,
                embedding, quality, sensitivity, expires_at, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::vector, $8, $9, $10, $11::jsonb)
            RETURNING id, agent_id, kind, content, quality, sensitivity,
                      created_at, expires_at
            """,
            tenant_id,
            request.agent_id,
            request.task_id,
            request.trace_id,
            request.kind,
            content_json,
            embedding_str,
            request.quality,
            request.sensitivity,
            expires_at,
            metadata_json,
        )

        logger.info(
            f"Stored {request.kind} memory for agent {request.agent_id} "
            f"(id: {result['id']})"
        )

        # Parse JSON content back to dict for response
        content_dict = json_lib.loads(result["content"]) if isinstance(result["content"], str) else result["content"]

        return MemoryResponse(
            id=str(result["id"]),
            agent_id=result["agent_id"],
            kind=result["kind"],
            content=content_dict,
            quality=result["quality"],
            sensitivity=result["sensitivity"],
            created_at=result["created_at"],
            expires_at=result["expires_at"],
        )

    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store memory: {str(e)}",
        )


@app.post("/v1/hyphal:search", response_model=SearchResponse)
async def search_memory(
    request: SearchRequest,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    Search hyphal memory using vector similarity.

    Performs semantic search across stored memories to find relevant
    knowledge based on embedding similarity.

    Requires valid API key in X-API-Key header.

    Args:
        request: Search request with query embedding
        tenant_id: Extracted from validated API key

    Returns:
        Ranked search results with similarity scores
    """
    try:

        # Convert embedding to PostgreSQL vector format
        embedding_str = "[" + ",".join(str(x) for x in request.embedding) + "]"

        # Build query with filters
        query = """
            SELECT id, agent_id, kind, content, quality, created_at,
                   1 - (embedding <=> $1::vector) AS similarity
            FROM hyphal_memory
            WHERE tenant_id = $2
              AND quality >= $3
              AND (expires_at IS NULL OR expires_at > NOW())
        """
        params = [embedding_str, tenant_id, request.min_quality]
        param_count = 4

        # Add optional filters
        if request.kind_filter:
            query += f" AND kind = ${param_count}"
            params.append(request.kind_filter)
            param_count += 1

        if request.agent_filter:
            query += f" AND agent_id = ${param_count}"
            params.append(request.agent_filter)
            param_count += 1

        # Order by similarity and limit
        query += f" ORDER BY embedding <=> $1::vector LIMIT ${param_count}"
        params.append(request.top_k)

        # Execute search
        results = await postgres.fetch(query, *params)

        # Build response (parse JSON content back to dict)
        import json as json_lib
        search_results = [
            SearchResult(
                id=str(row["id"]),
                agent_id=row["agent_id"],
                kind=row["kind"],
                content=json_lib.loads(row["content"]) if isinstance(row["content"], str) else row["content"],
                similarity=float(row["similarity"]),
                quality=float(row["quality"]),
                created_at=row["created_at"],
            )
            for row in results
        ]

        logger.info(
            f"Vector search returned {len(search_results)} results "
            f"(quality >= {request.min_quality})"
        )

        return SearchResponse(
            results=search_results,
            total=len(search_results),
            metadata={
                "top_k": request.top_k,
                "min_quality": request.min_quality,
                "kind_filter": request.kind_filter,
                "agent_filter": request.agent_filter,
            },
        )

    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search memory: {str(e)}",
        )


@app.get("/v1/hyphal/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    Get specific memory by ID.

    Requires valid API key in X-API-Key header.

    Args:
        memory_id: Memory identifier
        tenant_id: Extracted from validated API key

    Returns:
        Memory record
    """

    result = await postgres.fetchrow(
        """
        SELECT id, agent_id, kind, content, quality, sensitivity,
               created_at, expires_at
        FROM hyphal_memory
        WHERE id = $1 AND tenant_id = $2
        """,
        memory_id,
        tenant_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory '{memory_id}' not found",
        )

    # Parse content JSON to dict
    import json as json_lib
    content_dict = json_lib.loads(result["content"]) if result["content"] else {}

    return MemoryResponse(
        id=str(result["id"]),
        agent_id=result["agent_id"],
        kind=result["kind"],
        content=content_dict,
        quality=result["quality"],
        sensitivity=result["sensitivity"],
        created_at=result["created_at"],
        expires_at=result["expires_at"],
    )


@app.delete("/v1/hyphal/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    Delete memory from hyphal network.

    Requires valid API key in X-API-Key header.

    Args:
        memory_id: Memory identifier
        tenant_id: Extracted from validated API key
    """

    result = await postgres.execute(
        "DELETE FROM hyphal_memory WHERE id = $1 AND tenant_id = $2",
        memory_id,
        tenant_id,
    )

    if result == "DELETE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory '{memory_id}' not found",
        )

    logger.info(f"Deleted memory: {memory_id}")
    return None


@app.get("/v1/hyphal/agent/{agent_id}", response_model=List[MemoryResponse])
async def list_agent_memories(
    agent_id: str,
    kind: Optional[str] = None,
    limit: int = 100,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    List memories for specific agent.

    Requires valid API key in X-API-Key header.

    Args:
        agent_id: Agent identifier
        kind: Optional kind filter
        limit: Maximum results
        tenant_id: Extracted from validated API key

    Returns:
        List of agent memories
    """

    query = """
        SELECT id, agent_id, kind, content, quality, sensitivity,
               created_at, expires_at
        FROM hyphal_memory
        WHERE tenant_id = $1 AND agent_id = $2
          AND (expires_at IS NULL OR expires_at > NOW())
    """
    params = [tenant_id, agent_id]

    if kind:
        query += " AND kind = $3 ORDER BY created_at DESC LIMIT $4"
        params.extend([kind, limit])
    else:
        query += " ORDER BY created_at DESC LIMIT $3"
        params.append(limit)

    results = await postgres.fetch(query, *params)

    # Parse content JSON to dict for each row
    import json as json_lib

    return [
        MemoryResponse(
            id=str(row["id"]),
            agent_id=row["agent_id"],
            kind=row["kind"],
            content=json_lib.loads(row["content"]) if row["content"] else {},
            quality=row["quality"],
            sensitivity=row["sensitivity"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )
        for row in results
    ]


@app.post("/v1/hyphal:cleanup")
async def cleanup_expired(
    admin_tenant: str = Depends(get_validated_admin),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    Cleanup expired memories.

    Removes memories past their TTL for maintenance.

    Requires admin API key (AIcube Technology LLC).

    Args:
        admin_tenant: Validated admin tenant ID

    Returns:
        Count of deleted memories
    """
    try:
        result = await postgres.fetchval(
            "SELECT cleanup_expired_memory()"
        )

        logger.info(f"Cleaned up {result} expired memories")

        return {"deleted_count": result}

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup memories: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8201)
