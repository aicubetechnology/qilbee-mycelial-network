"""
Reinforcement Learning Engine - Edge Weight Plasticity

Updates edge weights based on task outcomes using synaptic plasticity principles.
Implements the formula: Δw = α_pos × outcome - α_neg × (1 - outcome) - λ_decay
"""

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import sys

sys.path.append("../..")
from shared.database import PostgresManager, MongoManager
from shared.models import ServiceHealth, HealthResponse
from shared.auth import init_api_key_validator, get_validated_tenant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="QMN Reinforcement Engine",
    description="Edge weight plasticity and reinforcement learning",
    version="0.1.0",
)

postgres_db: Optional[PostgresManager] = None
mongo_db: Optional[MongoManager] = None

# Reinforcement Learning Parameters
ALPHA_POS = 0.08  # Positive learning rate
ALPHA_NEG = 0.04  # Negative learning rate
LAMBDA_DECAY = 0.002  # Natural decay rate
MIN_WEIGHT = 0.01  # Minimum edge weight
MAX_WEIGHT = 1.5  # Maximum edge weight


# Request/Response Models
class OutcomeObject(BaseModel):
    """Nested outcome object from SDK."""

    score: float = Field(..., ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OutcomeRequest(BaseModel):
    """Request to record outcome.

    Supports two formats:
    1. Direct: {"trace_id": "...", "outcome_score": 0.85}
    2. SDK format: {"trace_id": "...", "outcome": {"score": 0.85}}
    """

    trace_id: str
    outcome_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    outcome: Optional[OutcomeObject] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def score(self) -> float:
        """Get outcome score from either format."""
        if self.outcome_score is not None:
            return self.outcome_score
        if self.outcome is not None:
            return self.outcome.score
        raise ValueError("Either outcome_score or outcome.score must be provided")

    def model_post_init(self, __context):
        """Validate that at least one score format is provided."""
        if self.outcome_score is None and self.outcome is None:
            raise ValueError("Either outcome_score or outcome object must be provided")


class OutcomeResponse(BaseModel):
    """Response from outcome recording."""

    trace_id: str
    edges_updated: int
    weight_changes: List[Dict[str, Any]]
    success: bool


class EdgeUpdate(BaseModel):
    """Edge weight update details."""

    src: str
    dst: str
    old_weight: float
    new_weight: float
    delta: float


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

    logger.info("Reinforcement Engine started")


@app.on_event("shutdown")
async def shutdown():
    """Close databases."""
    if postgres_db:
        await postgres_db.disconnect()
    if mongo_db:
        await mongo_db.disconnect()
    logger.info("Reinforcement Engine stopped")


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


# Note: get_validated_tenant from shared.auth is used for API key validation


# Reinforcement Learning Functions
def calculate_weight_delta(outcome_score: float, current_weight: float) -> float:
    """
    Calculate weight change using synaptic plasticity formula.

    Δw = α_pos × outcome - α_neg × (1 - outcome) - λ_decay

    Args:
        outcome_score: Task success score (0.0 to 1.0)
        current_weight: Current edge weight

    Returns:
        Weight delta (change amount)
    """
    delta = (
        ALPHA_POS * outcome_score
        - ALPHA_NEG * (1 - outcome_score)
        - LAMBDA_DECAY
    )

    return delta


def clamp_weight(weight: float) -> float:
    """Clamp weight to valid range."""
    return max(MIN_WEIGHT, min(MAX_WEIGHT, weight))


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
        service="reinforcement",
        region="us-east-1",
        checks={
            "postgres": postgres_healthy,
            "mongo": mongo_healthy,
        },
    )


@app.post("/v1/outcomes:record", response_model=OutcomeResponse)
async def record_outcome(
    request: OutcomeRequest,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    Record task outcome and update edge weights.

    Uses reinforcement learning to strengthen or weaken connections
    based on task success/failure.

    Requires valid API key in X-API-Key header.

    Args:
        request: Outcome request with trace ID and score
        tenant_id: Extracted from validated API key

    Returns:
        Updated edge information
    """
    try:

        # Get all routes for this trace
        routes = await postgres.fetch(
            """
            SELECT tenant_id, src_agent, dst_agent, routing_score, hop_number
            FROM nutrient_routes
            WHERE trace_id = $1
            ORDER BY hop_number ASC
            """,
            request.trace_id,
        )

        if not routes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No routes found for trace {request.trace_id}",
            )

        # Update each edge in the path
        weight_changes = []
        edges_updated = 0

        for route in routes:
            # Get current edge weight
            edge = await postgres.fetchrow(
                """
                SELECT w, r_success, r_decay
                FROM hyphae_edges
                WHERE tenant_id = $1 AND src = $2 AND dst = $3
                """,
                tenant_id,
                route["src_agent"],
                route["dst_agent"],
            )

            if not edge:
                # Edge doesn't exist yet, create it
                await postgres.execute(
                    """
                    INSERT INTO hyphae_edges (tenant_id, src, dst, w, sim, r_success, r_decay)
                    VALUES ($1, $2, $3, 0.1, 0.0, 0.0, 0.0)
                    """,
                    tenant_id,
                    route["src_agent"],
                    route["dst_agent"],
                )
                edge = {"w": 0.1, "r_success": 0.0, "r_decay": 0.0}

            old_weight = float(edge["w"])

            # Calculate weight delta
            delta = calculate_weight_delta(request.score, old_weight)
            new_weight = clamp_weight(old_weight + delta)

            # Update reinforcement counters
            new_r_success = float(edge["r_success"]) + request.score
            new_r_decay = float(edge["r_decay"]) + (1 - request.score)

            # Update edge in database
            await postgres.execute(
                """
                UPDATE hyphae_edges
                SET w = $1,
                    r_success = $2,
                    r_decay = $3,
                    last_update = NOW()
                WHERE tenant_id = $4 AND src = $5 AND dst = $6
                """,
                new_weight,
                new_r_success,
                new_r_decay,
                tenant_id,
                route["src_agent"],
                route["dst_agent"],
            )

            # Update outcome score in route record
            await postgres.execute(
                """
                UPDATE nutrient_routes
                SET outcome_score = $1
                WHERE trace_id = $2 AND src_agent = $3 AND dst_agent = $4
                """,
                request.score,
                request.trace_id,
                route["src_agent"],
                route["dst_agent"],
            )

            weight_changes.append({
                "src": route["src_agent"],
                "dst": route["dst_agent"],
                "old_weight": old_weight,
                "new_weight": new_weight,
                "delta": delta,
                "hop": route["hop_number"],
            })

            edges_updated += 1

        logger.info(
            f"Updated {edges_updated} edges for trace {request.trace_id} "
            f"with outcome {request.score:.2f}"
        )

        return OutcomeResponse(
            trace_id=request.trace_id,
            edges_updated=edges_updated,
            weight_changes=weight_changes,
            success=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording outcome: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record outcome: {str(e)}",
        )


@app.get("/v1/edges/stats")
async def get_edge_stats(
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    Get edge weight statistics.

    Requires valid API key in X-API-Key header.

    Args:
        tenant_id: Extracted from validated API key

    Returns:
        Statistical summary of edge weights
    """

    stats = await postgres.fetchrow(
        """
        SELECT
            COUNT(*) as total_edges,
            AVG(w) as avg_weight,
            MIN(w) as min_weight,
            MAX(w) as max_weight,
            STDDEV(w) as stddev_weight,
            AVG(r_success) as avg_success,
            AVG(r_decay) as avg_decay
        FROM hyphae_edges
        WHERE tenant_id = $1
        """,
        tenant_id,
    )

    return {
        "total_edges": stats["total_edges"],
        "avg_weight": float(stats["avg_weight"] or 0),
        "min_weight": float(stats["min_weight"] or 0),
        "max_weight": float(stats["max_weight"] or 0),
        "stddev_weight": float(stats["stddev_weight"] or 0),
        "avg_success": float(stats["avg_success"] or 0),
        "avg_decay": float(stats["avg_decay"] or 0),
    }


@app.get("/v1/edges/{agent_id}")
async def get_agent_edges(
    agent_id: str,
    min_weight: float = 0.0,
    limit: int = 50,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    Get edges for a specific agent.

    Returns edges where the agent is either source or destination.

    Requires valid API key in X-API-Key header.

    Args:
        agent_id: Agent identifier
        min_weight: Minimum edge weight filter
        limit: Maximum edges to return
        tenant_id: Extracted from validated API key

    Returns:
        List of edges for the agent
    """
    edges = await postgres.fetch(
        """
        SELECT src, dst, w, sim, r_success, r_decay, last_update
        FROM hyphae_edges
        WHERE tenant_id = $1
          AND (src = $2 OR dst = $2)
          AND w >= $3
        ORDER BY w DESC
        LIMIT $4
        """,
        tenant_id,
        agent_id,
        min_weight,
        limit,
    )

    edge_list = [
        {
            "src": edge["src"],
            "dst": edge["dst"],
            "target_id": edge["dst"],  # Alias for client compatibility
            "weight": float(edge["w"]),
            "similarity": float(edge["sim"]),
            "success": float(edge["r_success"]),
            "decay": float(edge["r_decay"]),
            "last_update": edge["last_update"].isoformat() if edge["last_update"] else None,
        }
        for edge in edges
    ]

    return {"edges": edge_list}


@app.get("/v1/edges/top")
async def get_top_edges(
    limit: int = 10,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    Get top edges by weight.

    Requires valid API key in X-API-Key header.

    Args:
        limit: Number of edges to return
        tenant_id: Extracted from validated API key

    Returns:
        List of strongest edges
    """

    edges = await postgres.fetch(
        """
        SELECT src, dst, w, sim, r_success, r_decay, last_update
        FROM hyphae_edges
        WHERE tenant_id = $1
        ORDER BY w DESC
        LIMIT $2
        """,
        tenant_id,
        limit,
    )

    return [
        {
            "src": edge["src"],
            "dst": edge["dst"],
            "weight": float(edge["w"]),
            "similarity": float(edge["sim"]),
            "success": float(edge["r_success"]),
            "decay": float(edge["r_decay"]),
            "last_update": edge["last_update"].isoformat(),
        }
        for edge in edges
    ]


@app.post("/v1/edges:prune")
async def prune_weak_edges(
    threshold: float = 0.05,
    tenant_id: str = Depends(get_validated_tenant),
    postgres: PostgresManager = Depends(get_postgres),
):
    """
    Prune weak edges below threshold.

    Requires valid API key in X-API-Key header.

    Args:
        threshold: Minimum weight threshold
        tenant_id: Extracted from validated API key

    Returns:
        Number of edges pruned
    """

    result = await postgres.fetchval(
        """
        DELETE FROM hyphae_edges
        WHERE tenant_id = $1 AND w < $2
        RETURNING COUNT(*)
        """,
        tenant_id,
        threshold,
    )

    pruned_count = result or 0

    logger.info(f"Pruned {pruned_count} weak edges below threshold {threshold}")

    return {
        "pruned": pruned_count,
        "threshold": threshold,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8202)
