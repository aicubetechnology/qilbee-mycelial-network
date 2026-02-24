"""
Identity Service - Tenant Management

Handles tenant creation, updates, and multi-tenant identity management.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import sys

sys.path.append("../..")
from shared.database import PostgresManager
from shared.models import ServiceHealth, HealthResponse, TenantInfo
from shared.auth import init_api_key_validator, get_validated_admin
from shared.startup import ensure_admin_initialized

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="QMN Identity Service",
    description="Multi-tenant identity and organization management",
    version="0.1.0",
)

# Database manager
db: Optional[PostgresManager] = None


# Request/Response Models
class CreateTenantRequest(BaseModel):
    """Request to create new tenant."""

    id: str = Field(..., min_length=3, max_length=64, pattern="^[a-z0-9-]+$")
    name: str = Field(..., min_length=1, max_length=255)
    plan_tier: str = Field(default="free", pattern="^(free|pro|enterprise)$")
    kms_key_id: Optional[str] = None
    region_preference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateTenantRequest(BaseModel):
    """Request to update tenant."""

    name: Optional[str] = None
    plan_tier: Optional[str] = None
    kms_key_id: Optional[str] = None
    region_preference: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    """Tenant response."""

    id: str
    name: str
    plan_tier: str
    status: str
    kms_key_id: Optional[str]
    region_preference: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


# Lifecycle Events
@app.on_event("startup")
async def startup():
    """Initialize database connections and admin tenant."""
    global db
    import os

    postgres_url = os.getenv(
        "POSTGRES_URL", "postgresql://postgres:dev_password@localhost:5432/qmn"
    )

    db = PostgresManager(postgres_url)
    await db.connect()

    # Initialize API key validator
    init_api_key_validator(db)

    # Ensure admin tenant exists (creates AIcube Technology LLC on fresh startup)
    await ensure_admin_initialized(db)

    logger.info("Identity service started")


@app.on_event("shutdown")
async def shutdown():
    """Close database connections."""
    if db:
        await db.disconnect()
    logger.info("Identity service stopped")


# Dependency Injection
async def get_db() -> PostgresManager:
    """Get database manager."""
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    return db


# Health Check
@app.get("/health", response_model=HealthResponse)
async def health_check(database: PostgresManager = Depends(get_db)):
    """Check service health."""
    postgres_healthy = await database.health_check()

    health_status = ServiceHealth.HEALTHY if postgres_healthy else ServiceHealth.UNHEALTHY

    return HealthResponse(
        status=health_status,
        service="identity",
        region="us-east-1",
        checks={"postgres": postgres_healthy},
    )


# Tenant Management Endpoints
@app.post("/v1/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: CreateTenantRequest,
    admin_tenant: str = Depends(get_validated_admin),
    database: PostgresManager = Depends(get_db),
):
    """
    Create new tenant organization.

    Requires admin API key (AIcube Technology LLC).

    Args:
        request: Tenant creation request
        admin_tenant: Validated admin tenant ID

    Returns:
        Created tenant information
    """
    try:
        # Check if tenant already exists
        existing = await database.fetchrow(
            "SELECT id FROM tenants WHERE id = $1",
            request.id,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tenant '{request.id}' already exists",
            )

        # Insert tenant (convert metadata dict to JSON)
        import json as json_lib
        metadata_json = json_lib.dumps(request.metadata) if request.metadata else "{}"

        result = await database.fetchrow(
            """
            INSERT INTO tenants (id, name, plan_tier, status, kms_key_id, region_preference, metadata)
            VALUES ($1, $2, $3, 'active', $4, $5, $6::jsonb)
            RETURNING id, name, plan_tier, status, kms_key_id, region_preference,
                      created_at, updated_at, metadata
            """,
            request.id,
            request.name,
            request.plan_tier,
            request.kms_key_id,
            request.region_preference,
            metadata_json,
        )

        # Create default quota config
        await database.execute(
            "INSERT INTO quota_configs (tenant_id) VALUES ($1) ON CONFLICT DO NOTHING",
            request.id,
        )

        # Create default retention policy
        await database.execute(
            "INSERT INTO retention_policies (tenant_id) VALUES ($1) ON CONFLICT DO NOTHING",
            request.id,
        )

        logger.info(f"Created tenant: {request.id}")

        # Parse metadata JSON back to dict
        metadata_dict = json_lib.loads(result["metadata"]) if result["metadata"] else {}

        return TenantResponse(
            id=result["id"],
            name=result["name"],
            plan_tier=result["plan_tier"],
            status=result["status"],
            kms_key_id=result["kms_key_id"],
            region_preference=result["region_preference"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            metadata=metadata_dict,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}",
        )


@app.get("/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    admin_tenant: str = Depends(get_validated_admin),
    database: PostgresManager = Depends(get_db),
):
    """
    Get tenant by ID.

    Requires admin API key (AIcube Technology LLC).

    Args:
        tenant_id: Tenant identifier
        admin_tenant: Validated admin tenant ID

    Returns:
        Tenant information
    """
    result = await database.fetchrow(
        """
        SELECT id, name, plan_tier, status, kms_key_id, region_preference,
               created_at, updated_at, metadata
        FROM tenants
        WHERE id = $1
        """,
        tenant_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found",
        )

    # Parse metadata JSON to dict
    import json as json_lib
    metadata_dict = json_lib.loads(result["metadata"]) if result["metadata"] else {}

    return TenantResponse(
        id=result["id"],
        name=result["name"],
        plan_tier=result["plan_tier"],
        status=result["status"],
        kms_key_id=result["kms_key_id"],
        region_preference=result["region_preference"],
        created_at=result["created_at"],
        updated_at=result["updated_at"],
        metadata=metadata_dict,
    )


@app.put("/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    request: UpdateTenantRequest,
    admin_tenant: str = Depends(get_validated_admin),
    database: PostgresManager = Depends(get_db),
):
    """
    Update tenant information.

    Requires admin API key (AIcube Technology LLC).

    Args:
        tenant_id: Tenant identifier
        request: Update request
        admin_tenant: Validated admin tenant ID

    Returns:
        Updated tenant information
    """
    # Check if tenant exists
    existing = await database.fetchrow("SELECT id FROM tenants WHERE id = $1", tenant_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found",
        )

    import json as json_lib

    # Explicit parameterized update using only known columns
    # Each field maps to a fixed column name (no user input in column names)
    ALLOWED_FIELDS = {
        "name": "name",
        "plan_tier": "plan_tier",
        "kms_key_id": "kms_key_id",
        "region_preference": "region_preference",
        "status": "status",
        "metadata": "metadata",
    }

    updates = []
    values = []
    param_count = 1

    for field_name, column_name in ALLOWED_FIELDS.items():
        value = getattr(request, field_name, None)
        if value is not None:
            if field_name == "metadata":
                # Serialize metadata dict to JSON string for JSONB column
                updates.append(f"{column_name} = ${param_count}::jsonb")
                values.append(json_lib.dumps(value))
            else:
                updates.append(f"{column_name} = ${param_count}")
                values.append(value)
            param_count += 1

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    # Add tenant_id as last parameter
    values.append(tenant_id)

    query = f"""
        UPDATE tenants
        SET {', '.join(updates)}, updated_at = NOW()
        WHERE id = ${param_count}
        RETURNING id, name, plan_tier, status, kms_key_id, region_preference,
                  created_at, updated_at, metadata
    """

    result = await database.fetchrow(query, *values)

    logger.info(f"Updated tenant: {tenant_id}")

    # Parse metadata JSON to dict
    import json as json_lib
    metadata_dict = json_lib.loads(result["metadata"]) if result["metadata"] else {}

    return TenantResponse(
        id=result["id"],
        name=result["name"],
        plan_tier=result["plan_tier"],
        status=result["status"],
        kms_key_id=result["kms_key_id"],
        region_preference=result["region_preference"],
        created_at=result["created_at"],
        updated_at=result["updated_at"],
        metadata=metadata_dict,
    )


@app.get("/v1/tenants", response_model=List[TenantResponse])
async def list_tenants(
    status_filter: Optional[str] = None,
    plan_tier: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    admin_tenant: str = Depends(get_validated_admin),
    database: PostgresManager = Depends(get_db),
):
    """
    List tenants with optional filters.

    Requires admin API key (AIcube Technology LLC).

    Args:
        status_filter: Filter by status
        plan_tier: Filter by plan tier
        limit: Maximum results
        offset: Pagination offset
        admin_tenant: Validated admin tenant ID

    Returns:
        List of tenants
    """
    query = """
        SELECT id, name, plan_tier, status, kms_key_id, region_preference,
               created_at, updated_at, metadata
        FROM tenants
        WHERE 1=1
    """
    params = []
    param_count = 1

    if status_filter:
        query += f" AND status = ${param_count}"
        params.append(status_filter)
        param_count += 1

    if plan_tier:
        query += f" AND plan_tier = ${param_count}"
        params.append(plan_tier)
        param_count += 1

    query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
    params.extend([limit, offset])

    results = await database.fetch(query, *params)

    # Parse metadata JSON to dict for each row
    import json as json_lib

    return [
        TenantResponse(
            id=row["id"],
            name=row["name"],
            plan_tier=row["plan_tier"],
            status=row["status"],
            kms_key_id=row["kms_key_id"],
            region_preference=row["region_preference"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json_lib.loads(row["metadata"]) if row["metadata"] else {},
        )
        for row in results
    ]


@app.delete("/v1/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    admin_tenant: str = Depends(get_validated_admin),
    database: PostgresManager = Depends(get_db),
):
    """
    Delete tenant (soft delete by setting status to 'deleted').

    Requires admin API key (AIcube Technology LLC).

    Args:
        tenant_id: Tenant identifier
        admin_tenant: Validated admin tenant ID
    """
    result = await database.execute(
        "UPDATE tenants SET status = 'deleted', updated_at = NOW() WHERE id = $1",
        tenant_id,
    )

    if result == "UPDATE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found",
        )

    logger.info(f"Deleted tenant: {tenant_id}")
    return None


@app.get("/v1/tenants/{tenant_id}/usage")
async def get_tenant_usage(
    tenant_id: str,
    admin_tenant: str = Depends(get_validated_admin),
    database: PostgresManager = Depends(get_db),
):
    """
    Get usage metrics and quota status for a tenant.

    Requires admin API key.

    Args:
        tenant_id: Tenant identifier
        admin_tenant: Validated admin tenant ID

    Returns:
        Usage metrics and quota information
    """
    # Get quota config
    quota = await database.fetchrow(
        "SELECT * FROM quota_configs WHERE tenant_id = $1",
        tenant_id,
    )

    # Get recent usage metrics
    usage_rows = await database.fetch(
        """
        SELECT metric_type, SUM(value) as total_value
        FROM usage_metrics
        WHERE tenant_id = $1
          AND window_start >= NOW() - INTERVAL '1 hour'
        GROUP BY metric_type
        """,
        tenant_id,
    )

    usage = {row["metric_type"]: int(row["total_value"]) for row in usage_rows}

    quota_info = {}
    if quota:
        quota_info = {
            "nutrients_per_hour": quota["nutrients_per_hour"],
            "contexts_per_hour": quota["contexts_per_hour"],
            "memory_searches_per_hour": quota["memory_searches_per_hour"],
            "storage_mb": quota["storage_mb"],
            "max_agents": quota["max_agents"],
        }

    return {
        "tenant_id": tenant_id,
        "current_usage": usage,
        "quota": quota_info,
        "nutrients_sent": usage.get("nutrients_sent", 0),
        "contexts_collected": usage.get("contexts_collected", 0),
        "quota_remaining": {
            "nutrients_per_hour": quota_info.get("nutrients_per_hour", 10000)
            - usage.get("nutrients_sent", 0),
            "contexts_per_hour": quota_info.get("contexts_per_hour", 5000)
            - usage.get("contexts_collected", 0),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
