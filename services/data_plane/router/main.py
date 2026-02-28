"""
Router Service - Nutrient Routing & Collection

Core data plane service that handles:
- Nutrient broadcasting and routing
- Context collection from network
- Embedding-based similarity routing
- Quota enforcement
"""

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import numpy as np
import time as _time
import logging
import sys
import uuid

sys.path.append("../..")
from shared.database import PostgresManager, MongoManager
from shared.routing import RoutingAlgorithm, Neighbor, QuotaChecker, TTLChecker
from shared.models import ServiceHealth, HealthResponse, NutrientModel, ContextModel
from shared.auth import init_api_key_validator, get_validated_tenant
from shared.logging import configure_logging

logger = configure_logging("router")

app = FastAPI(
    title="QMN Router Service",
    description="Nutrient routing and context collection",
    version="0.1.0",
)

# Prometheus instrumentation
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    from shared.metrics import (
        nutrients_broadcast_total, contexts_collected_total,
        routing_latency, vector_search_latency,
    )
    Instrumentator().instrument(app).expose(app)
except ImportError:
    pass

postgres_db: Optional[PostgresManager] = None
mongo_db: Optional[MongoManager] = None


# Request/Response Models
class BroadcastRequest(BaseModel):
    """Request to broadcast nutrient."""

    summary: str
    embedding: List[float] = Field(..., min_items=1536, max_items=1536)
    snippets: List[str] = Field(default_factory=list)
    tool_hints: List[str] = Field(default_factory=list)
    sensitivity: str = "internal"
    ttl_sec: int = Field(default=180, ge=1, le=3600)
    max_hops: int = Field(default=3, ge=1, le=10)
    quota_cost: int = Field(default=1, ge=1, le=100)
    trace_task_id: Optional[str] = None
    source_agent_id: Optional[str] = None  # Agent ID broadcasting the nutrient


class BroadcastResponse(BaseModel):
    """Response from nutrient broadcast."""

    nutrient_id: str
    trace_id: str
    routed_to: List[str]
    routing_scores: Dict[str, float]
    created_at: datetime


class CollectRequest(BaseModel):
    """Request to collect contexts."""

    demand_embedding: List[float] = Field(..., min_items=1536, max_items=1536)
    window_ms: int = Field(default=300, ge=100, le=5000)
    top_k: int = Field(default=5, ge=1, le=50)
    diversify: bool = True
    trace_task_id: Optional[str] = None


# Agent Registration Models
class AgentProfile(BaseModel):
    """Agent profile with embedding and skills."""

    embedding: List[float] = Field(..., min_items=1536, max_items=1536)
    skills: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class RegisterAgentRequest(BaseModel):
    """Request to register/update an agent."""

    agent_id: str = Field(..., min_length=1, max_length=255)
    name: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    profile: AgentProfile
    region: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Agent registration response."""

    agent_id: str
    tenant_id: str
    name: Optional[str]
    capabilities: List[str]
    tools: List[str]
    status: str
    region: Optional[str]
    created_at: datetime
    updated_at: datetime


# Lifecycle
@app.on_event("startup")
async def startup():
    """Initialize databases."""
    global postgres_db, mongo_db
    import os

    postgres_url = os.getenv(
        "POSTGRES_URL", "postgresql://postgres:dev_password@localhost:5432/qmn"
    )
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")

    postgres_db = PostgresManager(postgres_url)
    await postgres_db.connect()

    mongo_db = MongoManager(mongo_url, "qmn")
    await mongo_db.connect()

    # Initialize API key validator
    init_api_key_validator(postgres_db)

    logger.info("Router service started")


@app.on_event("shutdown")
async def shutdown():
    """Close databases."""
    if postgres_db:
        await postgres_db.disconnect()
    if mongo_db:
        await mongo_db.disconnect()
    logger.info("Router service stopped")


async def get_postgres() -> PostgresManager:
    """Get PostgreSQL manager."""
    if postgres_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL not available",
        )
    return postgres_db


async def get_mongo() -> MongoManager:
    """Get MongoDB manager."""
    if mongo_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB not available",
        )
    return mongo_db


# Helper Functions
# Note: get_validated_tenant from shared.auth is used for API key validation


# Dynamic neighbor limit parameters
MIN_NEIGHBOR_LIMIT = 20
MAX_NEIGHBOR_LIMIT = 50
_cached_edge_count: Dict[str, Any] = {"count": 0, "updated_at": None}
EDGE_COUNT_CACHE_TTL_SEC = 300  # 5 minutes


async def _get_dynamic_limit(tenant_id: str, postgres: PostgresManager) -> int:
    """
    Calculate dynamic neighbor limit based on network size.

    Formula: min(50, max(20, total_edges / 10))
    Caches total edge count for 5 minutes.

    Returns:
        Dynamic neighbor limit
    """
    now = datetime.utcnow()
    cache_valid = (
        _cached_edge_count["updated_at"] is not None
        and (now - _cached_edge_count["updated_at"]).total_seconds() < EDGE_COUNT_CACHE_TTL_SEC
    )

    if not cache_valid:
        count = await postgres.fetchval(
            "SELECT COUNT(*) FROM hyphae_edges WHERE tenant_id = $1",
            tenant_id,
        )
        _cached_edge_count["count"] = count or 0
        _cached_edge_count["updated_at"] = now

    return min(MAX_NEIGHBOR_LIMIT, max(MIN_NEIGHBOR_LIMIT, _cached_edge_count["count"] // 10))


async def load_agent_neighbors(
    tenant_id: str,
    agent_id: str,
    mongo: MongoManager,
    postgres: PostgresManager,
) -> List[Neighbor]:
    """
    Load neighbor agents with edge weights.

    Uses dynamic neighbor limit based on network size and batch-loads
    all agent profiles in a single MongoDB query with projection.

    Args:
        tenant_id: Tenant identifier
        agent_id: Source agent ID
        mongo: MongoDB manager
        postgres: PostgreSQL manager

    Returns:
        List of Neighbor objects
    """
    # Dynamic neighbor limit based on network size
    neighbor_limit = await _get_dynamic_limit(tenant_id, postgres)

    # Get edges from PostgreSQL
    edges = await postgres.fetch(
        """
        SELECT dst, w, sim, last_update
        FROM hyphae_edges
        WHERE tenant_id = $1 AND src = $2
        ORDER BY w DESC
        LIMIT $3
        """,
        tenant_id,
        agent_id,
        neighbor_limit,
    )

    if not edges:
        return []

    # Batch load all neighbor agent profiles in a single MongoDB query
    # with projection to only fetch needed fields (fixes N+1 query)
    neighbor_ids = [edge["dst"] for edge in edges]
    edge_map = {edge["dst"]: edge for edge in edges}

    projection = {
        "_id": 1,
        "profile.embedding": 1,
        "metrics.recent_tasks": 1,
        "capabilities": 1,
    }

    cursor = mongo.get_collection("agents").find(
        {"_id": {"$in": neighbor_ids}, "tenant_id": tenant_id},
        projection=projection,
    )
    agents = await cursor.to_list(length=neighbor_limit)

    neighbors = []
    for agent in agents:
        edge = edge_map.get(agent["_id"])
        if not edge:
            continue

        neighbors.append(
            Neighbor(
                id=agent["_id"],
                profile_embedding=np.array(agent["profile"]["embedding"]),
                edge_weight=edge["w"],
                base_similarity=edge["sim"],
                recent_tasks=agent.get("metrics", {}).get("recent_tasks", []),
                capabilities=agent.get("capabilities", []),
                last_update=edge["last_update"],
            )
        )

    return neighbors


async def store_active_nutrient(
    tenant_id: str,
    nutrient_id: str,
    trace_id: str,
    request: BroadcastRequest,
    postgres: PostgresManager,
) -> None:
    """Store active nutrient in database."""
    import json as json_lib

    expires_at = datetime.utcnow() + timedelta(seconds=request.ttl_sec)

    # Convert arrays to proper PostgreSQL types
    embedding_str = "[" + ",".join(str(x) for x in request.embedding) + "]"
    snippets_json = json_lib.dumps(request.snippets)
    tool_hints_json = json_lib.dumps(request.tool_hints)

    await postgres.execute(
        """
        INSERT INTO nutrients_active (
            id, tenant_id, trace_id, summary, embedding, snippets, tool_hints,
            sensitivity, current_hop, max_hops, ttl_sec, quota_cost, expires_at
        )
        VALUES ($1, $2, $3, $4, $5::vector, $6::jsonb, $7::jsonb, $8, 0, $9, $10, $11, $12)
        """,
        nutrient_id,
        tenant_id,
        trace_id,
        request.summary,
        embedding_str,
        snippets_json,
        tool_hints_json,
        request.sensitivity,
        request.max_hops,
        request.ttl_sec,
        request.quota_cost,
        expires_at,
    )


async def record_routing_decision(
    tenant_id: str,
    nutrient_id: str,
    trace_id: str,
    src_agent: str,
    dst_agent: str,
    hop_number: int,
    routing_score: float,
    postgres: PostgresManager,
) -> None:
    """Record routing decision for reinforcement learning."""
    await postgres.execute(
        """
        INSERT INTO nutrient_routes (
            tenant_id, nutrient_id, trace_id, src_agent, dst_agent,
            hop_number, routing_score, routed_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        """,
        tenant_id,
        nutrient_id,
        trace_id,
        src_agent,
        dst_agent,
        hop_number,
        routing_score,
    )


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check(
    postgres: PostgresManager = Depends(get_postgres),
    mongo: MongoManager = Depends(get_mongo),
):
    """Check service health."""
    postgres_healthy = await postgres.health_check()
    mongo_healthy = await mongo.health_check()

    health_status = (
        ServiceHealth.HEALTHY
        if (postgres_healthy and mongo_healthy)
        else ServiceHealth.UNHEALTHY
    )

    return HealthResponse(
        status=health_status,
        service="router",
        region="us-east-1",
        checks={
            "postgres": postgres_healthy,
            "mongo": mongo_healthy,
        },
    )


@app.post("/v1/nutrients:broadcast", response_model=BroadcastResponse)
async def broadcast_nutrient(
    request: BroadcastRequest,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
    mongo: MongoManager = Depends(get_mongo),
):
    """
    Broadcast nutrient to mycelial network.

    Routes nutrient to relevant agents based on embedding similarity,
    capabilities, and learned edge weights.

    Requires valid API key in X-API-Key header.

    Args:
        request: Broadcast request with nutrient data
        tenant_id: Extracted from validated API key

    Returns:
        Routing information and trace ID
    """
    try:

        # TTL enforcement: validate nutrient is not expired before routing
        if not TTLChecker.can_forward(
            nutrient_created_at=datetime.utcnow(),
            nutrient_ttl_sec=request.ttl_sec,
            nutrient_max_hops=request.max_hops,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nutrient expired: TTL exceeded or no hops remaining",
            )

        # Generate IDs
        nutrient_id = f"nutr-{uuid.uuid4().hex[:12]}"
        trace_id = f"tr-{uuid.uuid4().hex[:16]}"

        # Use source_agent_id from request, or fallback to default
        source_agent = request.source_agent_id or "default-agent"

        # Load neighbor agents
        neighbors = await load_agent_neighbors(
            tenant_id=tenant_id,
            agent_id=source_agent,
            mongo=mongo,
            postgres=postgres,
        )

        # Store active nutrient first
        await store_active_nutrient(
            tenant_id, nutrient_id, trace_id, request, postgres
        )

        # Always record a self-route for reinforcement learning
        # This allows outcome recording even without neighbor routing
        await record_routing_decision(
            tenant_id=tenant_id,
            nutrient_id=nutrient_id,
            trace_id=trace_id,
            src_agent=source_agent,
            dst_agent=source_agent,  # Self-route
            hop_number=0,
            routing_score=1.0,
            postgres=postgres,
        )

        if not neighbors:
            # If no neighbors, return with just self-route
            return BroadcastResponse(
                nutrient_id=nutrient_id,
                trace_id=trace_id,
                routed_to=[source_agent],
                routing_scores={source_agent: 1.0},
                created_at=datetime.utcnow(),
            )

        # Route nutrient using algorithm (with latency tracking)
        nutrient_embedding = np.array(request.embedding)
        _start = _time.monotonic()

        selected = RoutingAlgorithm.route_nutrient(
            nutrient_embedding=nutrient_embedding,
            nutrient_tool_hints=request.tool_hints,
            neighbors=neighbors,
            top_k=3,
            diversify=True,
        )

        # Record metrics
        try:
            routing_latency.labels(tenant_id=tenant_id).observe(_time.monotonic() - _start)
            nutrients_broadcast_total.labels(tenant_id=tenant_id).inc()
        except Exception:
            pass

        # Record routing decisions
        routed_to = []
        routing_scores = {}

        for neighbor, score in selected:
            await record_routing_decision(
                tenant_id=tenant_id,
                nutrient_id=nutrient_id,
                trace_id=trace_id,
                src_agent=source_agent,
                dst_agent=neighbor.id,
                hop_number=0,
                routing_score=score.total_score,
                postgres=postgres,
            )

            routed_to.append(neighbor.id)
            routing_scores[neighbor.id] = score.total_score

        logger.info(
            f"Broadcasted nutrient {nutrient_id} to {len(routed_to)} agents "
            f"(trace: {trace_id})"
        )

        return BroadcastResponse(
            nutrient_id=nutrient_id,
            trace_id=trace_id,
            routed_to=routed_to,
            routing_scores=routing_scores,
            created_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Error broadcasting nutrient: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast nutrient: {str(e)}",
        )


@app.post("/v1/contexts:collect", response_model=ContextModel)
async def collect_contexts(
    request: CollectRequest,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
    mongo: MongoManager = Depends(get_mongo),
):
    """
    Collect enriched contexts from network.

    Gathers responses from agents based on demand embedding similarity.

    Requires valid API key in X-API-Key header.

    Args:
        request: Collection request with demand embedding
        tenant_id: Extracted from validated API key

    Returns:
        Aggregated contexts from network
    """
    try:

        # Generate trace ID
        trace_id = f"tr-{uuid.uuid4().hex[:16]}"
        _start = _time.monotonic()

        # Search hyphal memory for relevant contexts
        # Convert embedding list to PostgreSQL vector string format
        embedding_str = "[" + ",".join(str(x) for x in request.demand_embedding) + "]"

        # Use PostgreSQL vector search
        results = await postgres.fetch(
            """
            SELECT id, agent_id, kind, content, quality,
                   1 - (embedding <=> $1::vector) AS similarity
            FROM hyphal_memory
            WHERE tenant_id = $2
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY embedding <=> $1::vector
            LIMIT $3
            """,
            embedding_str,
            tenant_id,
            request.top_k * 2,  # Get more for diversity filtering
        )

        if not results:
            return ContextModel(
                trace_id=trace_id,
                contents=[],
                source_agents=[],
                quality_scores=[],
                metadata={"window_ms": request.window_ms, "top_k": request.top_k},
            )

        # Apply MMR diversity if requested
        if request.diversify and len(results) > request.top_k:
            # Simple diversity: select from different agents
            seen_agents = set()
            diverse_results = []

            for result in results:
                if result["agent_id"] not in seen_agents or len(diverse_results) < request.top_k:
                    diverse_results.append(result)
                    seen_agents.add(result["agent_id"])

                if len(diverse_results) >= request.top_k:
                    break

            results = diverse_results
        else:
            results = results[: request.top_k]

        # Build response
        contents = []
        source_agents = []
        quality_scores = []

        # Parse JSON content back to dict
        import json as json_lib

        for result in results:
            content_dict = json_lib.loads(result["content"]) if isinstance(result["content"], str) else result["content"]
            contents.append(
                {
                    "id": str(result["id"]),
                    "agent_id": result["agent_id"],
                    "kind": result["kind"],
                    "data": content_dict,
                    "similarity": float(result["similarity"]),
                }
            )
            source_agents.append(result["agent_id"])
            quality_scores.append(float(result["quality"]))

        # Record metrics
        try:
            vector_search_latency.labels(tenant_id=tenant_id).observe(_time.monotonic() - _start)
            contexts_collected_total.labels(tenant_id=tenant_id).inc()
        except Exception:
            pass

        logger.info(
            f"Collected {len(contents)} contexts from {len(set(source_agents))} agents "
            f"(trace: {trace_id})"
        )

        return ContextModel(
            trace_id=trace_id,
            contents=contents,
            source_agents=source_agents,
            quality_scores=quality_scores,
            metadata={
                "window_ms": request.window_ms,
                "top_k": request.top_k,
                "diversified": request.diversify,
            },
        )

    except Exception as e:
        logger.error(f"Error collecting contexts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect contexts: {str(e)}",
        )


# =============================================================================
# Agent Registration Endpoints
# =============================================================================


@app.post("/v1/agents:register", response_model=AgentResponse)
async def register_agent(
    request: RegisterAgentRequest,
    tenant_id: str = Depends(get_validated_tenant),
    mongo: MongoManager = Depends(get_mongo),
):
    """
    Register or update an agent in the network.

    Upserts agent profile in MongoDB with capabilities, profile embedding,
    and metadata. This enables the agent to participate in routing and
    reinforcement learning.

    Requires valid API key in X-API-Key header.

    Args:
        request: Agent registration request
        tenant_id: Extracted from validated API key

    Returns:
        Registered agent information
    """
    try:
        now = datetime.utcnow()

        # Build agent document
        agent_doc = {
            "_id": request.agent_id,
            "tenant_id": tenant_id,
            "name": request.name or request.agent_id,
            "capabilities": request.capabilities,
            "tools": request.tools,
            "profile": {
                "embedding": request.profile.embedding,
                "skills": request.profile.skills,
                "description": request.profile.description,
            },
            "metrics": {
                "tasks_completed_30d": 0,
                "tasks_completed_all_time": 0,
                "avg_success": 0.0,
                "last_active": now,
            },
            "neighbors": [],
            "quota": {
                "kb_hour": 2000,
                "msg_min": 10,
            },
            "status": "active",
            "metadata": request.metadata,
            "updated_at": now,
        }

        # Only include region if provided (MongoDB schema requires string, not null)
        if request.region:
            agent_doc["region"] = request.region

        # Check if agent exists
        existing = await mongo.find_one(
            "agents",
            {"_id": request.agent_id, "tenant_id": tenant_id},
            tenant_id=tenant_id,
        )

        if existing:
            # Update existing agent (preserve metrics and neighbors)
            update_fields = {
                "name": agent_doc["name"],
                "capabilities": agent_doc["capabilities"],
                "tools": agent_doc["tools"],
                "profile": agent_doc["profile"],
                "metadata": agent_doc["metadata"],
                "status": "active",
                "updated_at": now,
            }
            # Only update region if provided
            if request.region:
                update_fields["region"] = request.region

            update_doc = {"$set": update_fields}
            await mongo.get_collection("agents").update_one(
                {"_id": request.agent_id, "tenant_id": tenant_id},
                update_doc,
            )
            created_at = existing.get("created_at", now)
            logger.info(f"Updated agent: {request.agent_id} for tenant: {tenant_id}")
        else:
            # Insert new agent
            agent_doc["created_at"] = now
            await mongo.get_collection("agents").insert_one(agent_doc)
            created_at = now
            logger.info(f"Registered new agent: {request.agent_id} for tenant: {tenant_id}")

        return AgentResponse(
            agent_id=request.agent_id,
            tenant_id=tenant_id,
            name=agent_doc["name"],
            capabilities=agent_doc["capabilities"],
            tools=agent_doc["tools"],
            status="active",
            region=agent_doc["region"],
            created_at=created_at,
            updated_at=now,
        )

    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register agent: {str(e)}",
        )


@app.get("/v1/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    tenant_id: str = Depends(get_validated_tenant),
    mongo: MongoManager = Depends(get_mongo),
):
    """
    Get agent profile by ID.

    Requires valid API key in X-API-Key header.

    Args:
        agent_id: Agent identifier
        tenant_id: Extracted from validated API key

    Returns:
        Agent information
    """
    agent = await mongo.find_one(
        "agents",
        {"_id": agent_id, "tenant_id": tenant_id},
        tenant_id=tenant_id,
    )

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    return AgentResponse(
        agent_id=agent["_id"],
        tenant_id=agent["tenant_id"],
        name=agent.get("name"),
        capabilities=agent.get("capabilities", []),
        tools=agent.get("tools", []),
        status=agent.get("status", "unknown"),
        region=agent.get("region"),
        created_at=agent.get("created_at", datetime.utcnow()),
        updated_at=agent.get("updated_at", datetime.utcnow()),
    )


@app.get("/v1/agents", response_model=List[AgentResponse])
async def list_agents(
    status_filter: Optional[str] = None,
    capability: Optional[str] = None,
    limit: int = 100,
    tenant_id: str = Depends(get_validated_tenant),
    mongo: MongoManager = Depends(get_mongo),
):
    """
    List agents for the tenant.

    Requires valid API key in X-API-Key header.

    Args:
        status_filter: Filter by status (active, idle, suspended)
        capability: Filter by capability
        limit: Maximum number of results
        tenant_id: Extracted from validated API key

    Returns:
        List of agents
    """
    query = {"tenant_id": tenant_id}

    if status_filter:
        query["status"] = status_filter

    if capability:
        query["capabilities"] = capability

    agents = await mongo.find(
        "agents",
        query,
        tenant_id=tenant_id,
        limit=limit,
    )

    return [
        AgentResponse(
            agent_id=agent["_id"],
            tenant_id=agent["tenant_id"],
            name=agent.get("name"),
            capabilities=agent.get("capabilities", []),
            tools=agent.get("tools", []),
            status=agent.get("status", "unknown"),
            region=agent.get("region"),
            created_at=agent.get("created_at", datetime.utcnow()),
            updated_at=agent.get("updated_at", datetime.utcnow()),
        )
        for agent in agents
    ]


@app.delete("/v1/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_agent(
    agent_id: str,
    tenant_id: str = Depends(get_validated_tenant),
    mongo: MongoManager = Depends(get_mongo),
):
    """
    Deactivate an agent (soft delete).

    Sets agent status to 'suspended'. Does not delete data.

    Requires valid API key in X-API-Key header.

    Args:
        agent_id: Agent identifier
        tenant_id: Extracted from validated API key
    """
    result = await mongo.get_collection("agents").update_one(
        {"_id": agent_id, "tenant_id": tenant_id},
        {"$set": {"status": "suspended", "updated_at": datetime.utcnow()}},
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    logger.info(f"Deactivated agent: {agent_id}")
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8200)
