"""
Keys Service - API Key Management

Handles API key creation, validation, rotation, and revocation.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import hashlib
import secrets
import logging
import sys

sys.path.append("../..")
from shared.database import PostgresManager
from shared.models import ServiceHealth, HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="QMN Keys Service",
    description="API key lifecycle management",
    version="0.1.0",
)

db: Optional[PostgresManager] = None


# Models
class CreateKeyRequest(BaseModel):
    """Request to create API key."""

    tenant_id: str
    name: Optional[str] = None
    scopes: List[str] = Field(default_factory=lambda: ["*"])
    rate_limit_per_minute: int = 1000
    expires_in_days: Optional[int] = None


class CreateKeyResponse(BaseModel):
    """Response with new API key."""

    id: str
    api_key: str  # Only returned on creation
    key_prefix: str
    tenant_id: str
    name: Optional[str]
    scopes: List[str]
    rate_limit_per_minute: int
    expires_at: Optional[datetime]
    created_at: datetime


class KeyInfo(BaseModel):
    """API key information (without secret)."""

    id: str
    key_prefix: str
    tenant_id: str
    name: Optional[str]
    scopes: List[str]
    rate_limit_per_minute: int
    status: str
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime


class ValidateKeyRequest(BaseModel):
    """Request to validate API key."""

    api_key: str


class ValidateKeyResponse(BaseModel):
    """Response from key validation."""

    valid: bool
    tenant_id: Optional[str] = None
    scopes: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = None


class RotateKeyRequest(BaseModel):
    """Request to rotate API key."""

    key_id: str
    grace_period_sec: int = 3600


# Lifecycle
@app.on_event("startup")
async def startup():
    """Initialize database."""
    global db
    import os

    postgres_url = os.getenv(
        "POSTGRES_URL", "postgresql://postgres:dev_password@localhost:5432/qmn"
    )
    db = PostgresManager(postgres_url)
    await db.connect()
    logger.info("Keys service started")


@app.on_event("shutdown")
async def shutdown():
    """Close database."""
    if db:
        await db.disconnect()
    logger.info("Keys service stopped")


async def get_db() -> PostgresManager:
    """Get database manager."""
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    return db


# Helper Functions
def generate_api_key() -> str:
    """Generate secure API key."""
    random_bytes = secrets.token_bytes(32)
    return f"qmn_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_key_prefix(api_key: str) -> str:
    """Extract key prefix for identification."""
    return api_key[:12] if len(api_key) >= 12 else api_key


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check(database: PostgresManager = Depends(get_db)):
    """Check service health."""
    postgres_healthy = await database.health_check()
    health_status = ServiceHealth.HEALTHY if postgres_healthy else ServiceHealth.UNHEALTHY

    return HealthResponse(
        status=health_status,
        service="keys",
        region="us-east-1",
        checks={"postgres": postgres_healthy},
    )


@app.post("/v1/keys", response_model=CreateKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    request: CreateKeyRequest,
    database: PostgresManager = Depends(get_db),
):
    """
    Create new API key for tenant.

    Args:
        request: Key creation request

    Returns:
        API key information including the secret key
    """
    try:
        # Verify tenant exists
        tenant = await database.fetchrow(
            "SELECT id FROM tenants WHERE id = $1 AND status = 'active'",
            request.tenant_id,
        )

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active tenant '{request.tenant_id}' not found",
            )

        # Generate API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        key_prefix = get_key_prefix(api_key)

        # Calculate expiration
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

        # Insert key
        result = await database.fetchrow(
            """
            INSERT INTO api_keys (
                tenant_id, key_hash, key_prefix, name, scopes,
                rate_limit_per_minute, expires_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, tenant_id, key_prefix, name, scopes,
                      rate_limit_per_minute, expires_at, created_at
            """,
            request.tenant_id,
            key_hash,
            key_prefix,
            request.name,
            request.scopes,
            request.rate_limit_per_minute,
            expires_at,
        )

        logger.info(f"Created API key for tenant: {request.tenant_id}")

        return CreateKeyResponse(
            id=str(result["id"]),
            api_key=api_key,  # Only returned here
            key_prefix=result["key_prefix"],
            tenant_id=result["tenant_id"],
            name=result["name"],
            scopes=result["scopes"],
            rate_limit_per_minute=result["rate_limit_per_minute"],
            expires_at=result["expires_at"],
            created_at=result["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}",
        )


@app.post("/v1/keys:validate", response_model=ValidateKeyResponse)
async def validate_key(
    request: ValidateKeyRequest,
    database: PostgresManager = Depends(get_db),
):
    """
    Validate API key and return tenant info.

    Args:
        request: Validation request with API key

    Returns:
        Validation result with tenant information
    """
    try:
        key_hash = hash_api_key(request.api_key)

        result = await database.fetchrow(
            """
            SELECT k.tenant_id, k.scopes, k.rate_limit_per_minute, k.status, k.expires_at, k.id
            FROM api_keys k
            JOIN tenants t ON k.tenant_id = t.id
            WHERE k.key_hash = $1 AND t.status = 'active'
            """,
            key_hash,
        )

        if not result:
            return ValidateKeyResponse(valid=False)

        # Check if expired
        if result["expires_at"] and result["expires_at"] < datetime.utcnow():
            return ValidateKeyResponse(valid=False)

        # Check if revoked
        if result["status"] != "active":
            return ValidateKeyResponse(valid=False)

        # Update last_used_at
        await database.execute(
            "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1",
            result["id"],
        )

        return ValidateKeyResponse(
            valid=True,
            tenant_id=result["tenant_id"],
            scopes=result["scopes"],
            rate_limit_per_minute=result["rate_limit_per_minute"],
        )

    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return ValidateKeyResponse(valid=False)


@app.get("/v1/keys/{tenant_id}", response_model=List[KeyInfo])
async def list_keys(
    tenant_id: str,
    database: PostgresManager = Depends(get_db),
):
    """
    List API keys for tenant.

    Args:
        tenant_id: Tenant identifier

    Returns:
        List of API keys (without secrets)
    """
    results = await database.fetch(
        """
        SELECT id, key_prefix, tenant_id, name, scopes, rate_limit_per_minute,
               status, expires_at, last_used_at, created_at
        FROM api_keys
        WHERE tenant_id = $1
        ORDER BY created_at DESC
        """,
        tenant_id,
    )

    return [
        KeyInfo(
            id=str(row["id"]),
            key_prefix=row["key_prefix"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            scopes=row["scopes"],
            rate_limit_per_minute=row["rate_limit_per_minute"],
            status=row["status"],
            expires_at=row["expires_at"],
            last_used_at=row["last_used_at"],
            created_at=row["created_at"],
        )
        for row in results
    ]


@app.post("/v1/keys:rotate", response_model=CreateKeyResponse)
async def rotate_key(
    request: RotateKeyRequest,
    database: PostgresManager = Depends(get_db),
):
    """
    Rotate API key with grace period.

    Creates new key and marks old key for expiration after grace period.

    Args:
        request: Rotation request with grace period

    Returns:
        New API key information
    """
    try:
        # Get old key info
        old_key = await database.fetchrow(
            """
            SELECT tenant_id, name, scopes, rate_limit_per_minute
            FROM api_keys
            WHERE id = $1 AND status = 'active'
            """,
            request.key_id,
        )

        if not old_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key '{request.key_id}' not found or inactive",
            )

        # Generate new API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        key_prefix = get_key_prefix(api_key)

        # Insert new key
        new_key = await database.fetchrow(
            """
            INSERT INTO api_keys (
                tenant_id, key_hash, key_prefix, name, scopes, rate_limit_per_minute
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, tenant_id, key_prefix, name, scopes,
                      rate_limit_per_minute, expires_at, created_at
            """,
            old_key["tenant_id"],
            key_hash,
            key_prefix,
            old_key["name"],
            old_key["scopes"],
            old_key["rate_limit_per_minute"],
        )

        # Mark old key for expiration after grace period
        grace_expiration = datetime.utcnow() + timedelta(seconds=request.grace_period_sec)
        await database.execute(
            "UPDATE api_keys SET expires_at = $1 WHERE id = $2",
            grace_expiration,
            request.key_id,
        )

        logger.info(
            f"Rotated API key {request.key_id} for tenant {old_key['tenant_id']} "
            f"with {request.grace_period_sec}s grace period"
        )

        return CreateKeyResponse(
            id=str(new_key["id"]),
            api_key=api_key,
            key_prefix=new_key["key_prefix"],
            tenant_id=new_key["tenant_id"],
            name=new_key["name"],
            scopes=new_key["scopes"],
            rate_limit_per_minute=new_key["rate_limit_per_minute"],
            expires_at=new_key["expires_at"],
            created_at=new_key["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rotating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate API key: {str(e)}",
        )


@app.delete("/v1/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: str,
    database: PostgresManager = Depends(get_db),
):
    """
    Revoke API key immediately.

    Args:
        key_id: Key identifier
    """
    result = await database.execute(
        "UPDATE api_keys SET status = 'revoked' WHERE id = $1",
        key_id,
    )

    if result == "UPDATE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key '{key_id}' not found",
        )

    logger.info(f"Revoked API key: {key_id}")
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8101)
