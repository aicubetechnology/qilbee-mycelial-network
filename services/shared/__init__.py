"""Shared utilities for QMN services."""

from .routing import RoutingAlgorithm, Neighbor, RoutingScore, QuotaChecker, TTLChecker
from .database import DatabaseManager, PostgresManager, MongoManager
from .models import ServiceConfig, ServiceHealth
from .auth import (
    APIKeyValidator,
    init_api_key_validator,
    get_validated_tenant,
    get_validated_admin,
    get_tenant_context,
    get_optional_tenant,
    TenantContext,
    ADMIN_TENANT_ID,
    ADMIN_TENANT_NAME,
    ADMIN_SCOPE,
)
from .startup import ensure_admin_initialized, initialize_admin_tenant, bootstrap_admin_key

__all__ = [
    "RoutingAlgorithm",
    "Neighbor",
    "RoutingScore",
    "QuotaChecker",
    "TTLChecker",
    "DatabaseManager",
    "PostgresManager",
    "MongoManager",
    "ServiceConfig",
    "ServiceHealth",
    "APIKeyValidator",
    "init_api_key_validator",
    "get_validated_tenant",
    "get_validated_admin",
    "get_tenant_context",
    "get_optional_tenant",
    "TenantContext",
    "ADMIN_TENANT_ID",
    "ADMIN_TENANT_NAME",
    "ADMIN_SCOPE",
    "ensure_admin_initialized",
    "initialize_admin_tenant",
    "bootstrap_admin_key",
]
