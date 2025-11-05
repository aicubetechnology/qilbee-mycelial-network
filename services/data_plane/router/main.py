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
import logging
import sys
import uuid

sys.path.append("../..")
from shared.database import PostgresManager, MongoManager
from shared.routing import RoutingAlgorithm, Neighbor, QuotaChecker, TTLChecker
from shared.models import ServiceHealth, HealthResponse, NutrientModel, ContextModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="QMN Router Service",
    description="Nutrient routing and context collection",
    version="0.1.0",
)

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
async def get_tenant_from_context(tenant_id: str = "dev-tenant") -> str:
    """
    Extract tenant ID from request context.

    In production, this would be extracted from validated JWT/API key.
    For now, using default dev-tenant.
    """
    return tenant_id


async def load_agent_neighbors(
    tenant_id: str,
    agent_id: str,
    mongo: MongoManager,
    postgres: PostgresManager,
) -> List[Neighbor]:
    """
    Load neighbor agents with edge weights.

    Args:
        tenant_id: Tenant identifier
        agent_id: Source agent ID
        mongo: MongoDB manager
        postgres: PostgreSQL manager

    Returns:
        List of Neighbor objects
    """
    # Get edges from PostgreSQL
    edges = await postgres.fetch(
        """
        SELECT dst, w, sim, last_update
        FROM hyphae_edges
        WHERE tenant_id = $1 AND src = $2
        ORDER BY w DESC
        LIMIT 20
        """,
        tenant_id,
        agent_id,
    )

    if not edges:
        return []

    # Get neighbor agent profiles from MongoDB
    neighbor_ids = [edge["dst"] for edge in edges]
    edge_map = {edge["dst"]: edge for edge in edges}

    agents = await mongo.find(
        "agents",
        {"_id": {"$in": neighbor_ids}},
        tenant_id=tenant_id,
    )

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
    postgres: PostgresManager = Depends(get_postgres),
    mongo: MongoManager = Depends(get_mongo),
):
    """
    Broadcast nutrient to mycelial network.

    Routes nutrient to relevant agents based on embedding similarity,
    capabilities, and learned edge weights.

    Args:
        request: Broadcast request with nutrient data

    Returns:
        Routing information and trace ID
    """
    try:
        tenant_id = await get_tenant_from_context()

        # Generate IDs
        nutrient_id = f"nutr-{uuid.uuid4().hex[:12]}"
        trace_id = f"tr-{uuid.uuid4().hex[:16]}"

        # For demo, use a default source agent
        # In production, this would be from authenticated context
        source_agent = "agent:dev-1"

        # Load neighbor agents
        neighbors = await load_agent_neighbors(
            tenant_id=tenant_id,
            agent_id=source_agent,
            mongo=mongo,
            postgres=postgres,
        )

        if not neighbors:
            # If no neighbors, store nutrient but don't route
            await store_active_nutrient(
                tenant_id, nutrient_id, trace_id, request, postgres
            )

            return BroadcastResponse(
                nutrient_id=nutrient_id,
                trace_id=trace_id,
                routed_to=[],
                routing_scores={},
                created_at=datetime.utcnow(),
            )

        # Route nutrient using algorithm
        nutrient_embedding = np.array(request.embedding)

        selected = RoutingAlgorithm.route_nutrient(
            nutrient_embedding=nutrient_embedding,
            nutrient_tool_hints=request.tool_hints,
            neighbors=neighbors,
            top_k=3,
            diversify=True,
        )

        # Store active nutrient
        await store_active_nutrient(
            tenant_id, nutrient_id, trace_id, request, postgres
        )

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
    postgres: PostgresManager = Depends(get_postgres),
    mongo: MongoManager = Depends(get_mongo),
):
    """
    Collect enriched contexts from network.

    Gathers responses from agents based on demand embedding similarity.

    Args:
        request: Collection request with demand embedding

    Returns:
        Aggregated contexts from network
    """
    try:
        tenant_id = await get_tenant_from_context()

        # Generate trace ID
        trace_id = f"tr-{uuid.uuid4().hex[:16]}"

        # Search hyphal memory for relevant contexts
        # This is a simplified version - full implementation would query active agents
        query_embedding = request.demand_embedding

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
            query_embedding,
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8200)
