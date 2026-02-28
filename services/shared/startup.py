"""
Startup initialization for QMN services.

Handles fresh startup initialization including:
- Creating AIcube Technology LLC admin tenant
- Admin API key must be generated via bootstrap endpoint (not logged)
"""

import hashlib
import secrets
import string
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple

from .auth import ADMIN_TENANT_ID, ADMIN_TENANT_NAME, ADMIN_SCOPE

logger = logging.getLogger(__name__)


def generate_api_key() -> Tuple[str, str]:
    """
    Generate a new API key with prefix.

    Returns:
        Tuple of (full_api_key, key_hash)
    """
    alphabet = string.ascii_letters + string.digits + "-_"
    random_part = ''.join(secrets.choice(alphabet) for _ in range(43))
    api_key = f"qmn_{random_part}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key, key_hash


async def initialize_admin_tenant(postgres_manager) -> bool:
    """
    Initialize AIcube Technology LLC admin tenant on fresh startup.

    This function is idempotent - it only creates the tenant if it doesn't exist.

    SECURITY: This does NOT create an API key automatically.
    Use the bootstrap endpoint to generate the first admin key.

    Args:
        postgres_manager: PostgresManager instance

    Returns:
        True if tenant was created (fresh startup), False if already exists
    """
    try:
        # Check if admin tenant already exists
        existing = await postgres_manager.fetchrow(
            "SELECT id FROM tenants WHERE id = $1",
            ADMIN_TENANT_ID
        )

        if existing:
            logger.info(f"Admin tenant '{ADMIN_TENANT_NAME}' already exists")
            return False

        # Create admin tenant
        logger.info(f"Creating admin tenant: {ADMIN_TENANT_NAME}")

        await postgres_manager.execute(
            """
            INSERT INTO tenants (id, name, plan_tier, status, created_at, updated_at, metadata)
            VALUES ($1, $2, 'enterprise', 'active', NOW(), NOW(), $3::jsonb)
            """,
            ADMIN_TENANT_ID,
            ADMIN_TENANT_NAME,
            json.dumps({
                "is_admin": True,
                "description": "Global administrator tenant with full system access",
                "contact": "admin@aicubetechnology.com"
            })
        )

        logger.info(f"Admin tenant created: {ADMIN_TENANT_ID}")
        logger.info(">>> Run bootstrap endpoint to generate admin API key <<<")
        return True

    except Exception as e:
        logger.error(f"Error initializing admin tenant: {e}")
        raise


async def bootstrap_admin_key(postgres_manager) -> Optional[str]:
    """
    Generate the first admin API key (one-time bootstrap).

    SECURITY: This only works if NO admin keys exist yet.
    After the first key is created, this function returns None.

    Args:
        postgres_manager: PostgresManager instance

    Returns:
        API key if created, None if keys already exist
    """
    try:
        # Check if admin has any API keys
        key_count = await postgres_manager.fetchval(
            "SELECT COUNT(*) FROM api_keys WHERE tenant_id = $1 AND status = 'active'",
            ADMIN_TENANT_ID
        )

        if key_count > 0:
            logger.warning("Bootstrap rejected: Admin already has active API keys")
            return None

        # Check if admin tenant exists
        existing = await postgres_manager.fetchrow(
            "SELECT id FROM tenants WHERE id = $1",
            ADMIN_TENANT_ID
        )

        if not existing:
            logger.error("Bootstrap failed: Admin tenant does not exist")
            return None

        # Generate and create admin API key
        import uuid
        api_key, key_hash = generate_api_key()
        key_id = str(uuid.uuid4())
        key_prefix = api_key[:12]

        # Admin key never expires (10 years)
        expires_at = datetime.utcnow() + timedelta(days=3650)

        await postgres_manager.execute(
            """
            INSERT INTO api_keys (id, tenant_id, name, key_hash, key_prefix, scopes,
                                  rate_limit_per_minute, status, expires_at, created_at)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, 'active', $8, NOW())
            """,
            key_id,
            ADMIN_TENANT_ID,
            "admin-master-key",
            key_hash,
            key_prefix,
            json.dumps([ADMIN_SCOPE, "*"]),
            10000,
            expires_at
        )

        # Log only the prefix, never the full key
        logger.info(f"Admin API key created: {key_prefix}...")

        return api_key

    except Exception as e:
        logger.error(f"Error bootstrapping admin key: {e}")
        raise


async def ensure_admin_initialized(postgres_manager) -> None:
    """
    Ensure admin tenant is initialized during service startup.

    Call this from each service's startup event.

    NOTE: This only creates the tenant, NOT the API key.
    Use POST /v1/bootstrap to generate the admin key.

    Args:
        postgres_manager: PostgresManager instance
    """
    is_fresh = await initialize_admin_tenant(postgres_manager)

    if is_fresh:
        # Log instructions (no sensitive data)
        logger.info("=" * 50)
        logger.info("FRESH STARTUP DETECTED")
        logger.info("To generate admin API key, run:")
        logger.info("  curl -X POST http://localhost:8022/keys/v1/bootstrap")
        logger.info("=" * 50)
