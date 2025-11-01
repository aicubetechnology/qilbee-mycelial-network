"""
Shared models for QMN services.

Common data models used across control and data plane services.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ServiceHealth(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceConfig(BaseModel):
    """Base configuration for QMN services."""

    service_name: str
    region: str = "us-east-1"
    postgres_url: str
    mongo_url: str
    redis_url: Optional[str] = None
    log_level: str = "INFO"
    debug: bool = False


class HealthResponse(BaseModel):
    """Health check response."""

    status: ServiceHealth
    service: str
    region: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, bool] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TenantInfo(BaseModel):
    """Tenant information."""

    id: str
    name: str
    plan_tier: str = "free"
    status: str = "active"
    kms_key_id: Optional[str] = None
    region_preference: Optional[str] = None
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class APIKeyInfo(BaseModel):
    """API key information (without actual key)."""

    id: str
    tenant_id: str
    key_prefix: str
    name: Optional[str] = None
    scopes: List[str] = Field(default_factory=lambda: ["*"])
    rate_limit_per_minute: int = 1000
    status: str = "active"
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime


class QuotaConfig(BaseModel):
    """Quota configuration for tenant."""

    tenant_id: str
    nutrients_per_hour: int = 10000
    contexts_per_hour: int = 5000
    memory_searches_per_hour: int = 20000
    storage_mb: int = 10240
    max_agents: int = 100
    custom_limits: Dict[str, Any] = Field(default_factory=dict)


class UsageMetrics(BaseModel):
    """Usage metrics for tenant."""

    tenant_id: str
    nutrients_sent: int = 0
    contexts_collected: int = 0
    memory_searches: int = 0
    storage_used_mb: float = 0.0
    window_start: datetime
    window_end: datetime
    region: Optional[str] = None


class AgentProfile(BaseModel):
    """Agent profile from MongoDB."""

    id: str = Field(alias="_id")
    tenant_id: str
    name: str
    capabilities: List[str]
    tools: List[str]
    profile: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    neighbors: List[Dict[str, Any]] = Field(default_factory=list)
    quota: Optional[Dict[str, int]] = None
    status: str = "active"
    region: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class PolicyDocument(BaseModel):
    """Policy document from MongoDB."""

    id: str = Field(alias="_id")
    tenant_id: str
    policy_type: str
    name: str
    description: Optional[str] = None
    enabled: bool = True
    sensitivity_rules: Optional[Dict[str, Any]] = None
    rbac_roles: Optional[Dict[str, Any]] = None
    capability_matrix: Optional[Dict[str, Any]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    actions: Optional[Dict[str, Any]] = None
    version: int = 1
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class NutrientModel(BaseModel):
    """Nutrient model for API."""

    id: str
    trace_id: str
    summary: str
    embedding: List[float]
    snippets: List[str] = Field(default_factory=list)
    tool_hints: List[str] = Field(default_factory=list)
    sensitivity: str = "internal"
    current_hop: int = 0
    max_hops: int = 3
    ttl_sec: int = 180
    quota_cost: int = 1
    trace_task_id: Optional[str] = None
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextModel(BaseModel):
    """Context response model."""

    trace_id: str
    contents: List[Dict[str, Any]]
    source_agents: List[str]
    quality_scores: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OutcomeModel(BaseModel):
    """Outcome record model."""

    score: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
