"""
Policy Engine - DLP/RBAC/ABAC Enforcement

Handles Data Loss Prevention, Role-Based Access Control,
and Attribute-Based Access Control policies.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import logging
import sys

sys.path.append("../..")
from shared.database import MongoManager
from shared.models import ServiceHealth, HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="QMN Policy Engine",
    description="DLP, RBAC, and ABAC policy enforcement",
    version="0.1.0",
)

mongo_db: Optional[MongoManager] = None


# Enums
class PolicyType(str, Enum):
    """Policy types."""

    DLP = "dlp"
    RBAC = "rbac"
    ABAC = "abac"
    RATE_LIMIT = "rate_limit"
    CONTENT_FILTER = "content_filter"


class PolicyAction(str, Enum):
    """Policy action outcomes."""

    ALLOW = "allow"
    DENY = "deny"
    LOG = "log"
    ALERT = "alert"


# Request/Response Models
class PolicyEvaluationRequest(BaseModel):
    """Request to evaluate policy."""

    tenant_id: str
    policy_type: PolicyType
    subject: Dict[str, Any]  # Agent, user, or entity
    resource: Dict[str, Any]  # Nutrient, memory, or data
    action: str  # broadcast, collect, search, etc.
    context: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResponse(BaseModel):
    """Response from policy evaluation."""

    allowed: bool
    action: PolicyAction
    policy_id: Optional[str] = None
    reason: Optional[str] = None
    checks_passed: List[str] = Field(default_factory=list)
    checks_failed: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreatePolicyRequest(BaseModel):
    """Request to create policy."""

    tenant_id: str
    policy_type: PolicyType
    name: str
    description: Optional[str] = None
    enabled: bool = True
    sensitivity_rules: Optional[Dict[str, Any]] = None
    rbac_roles: Optional[Dict[str, Any]] = None
    capability_matrix: Optional[Dict[str, Any]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    actions: Optional[Dict[str, Any]] = None


# Lifecycle
@app.on_event("startup")
async def startup():
    """Initialize database."""
    global mongo_db
    import os

    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")

    mongo_db = MongoManager(mongo_url, "qmn")
    await mongo_db.connect()

    logger.info("Policy Engine started")


@app.on_event("shutdown")
async def shutdown():
    """Close database."""
    if mongo_db:
        await mongo_db.disconnect()
    logger.info("Policy Engine stopped")


async def get_mongo() -> MongoManager:
    """Get MongoDB manager."""
    if mongo_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB not available",
        )
    return mongo_db


# Policy Evaluation Functions
async def evaluate_dlp_policy(
    policy: Dict[str, Any],
    resource: Dict[str, Any],
    subject: Dict[str, Any],
) -> PolicyEvaluationResponse:
    """
    Evaluate DLP (Data Loss Prevention) policy.

    Checks sensitivity labels and access permissions.
    """
    sensitivity = resource.get("sensitivity", "internal")
    rules = policy.get("sensitivity_rules", {})

    if sensitivity not in rules:
        return PolicyEvaluationResponse(
            allowed=True,
            action=PolicyAction.ALLOW,
            policy_id=policy["_id"],
            reason=f"No DLP rules for sensitivity level: {sensitivity}",
            checks_passed=["default_allow"],
        )

    sensitivity_rule = rules[sensitivity]

    # Check allowed agents
    allowed_agents = sensitivity_rule.get("allowed_agents", ["*"])
    subject_id = subject.get("id", "")

    checks_passed = []
    checks_failed = []

    # Wildcard allows all
    if "*" in allowed_agents:
        checks_passed.append("agent_wildcard")
    else:
        # Check if subject matches any pattern
        agent_allowed = any(
            subject_id.startswith(pattern.replace("*", ""))
            for pattern in allowed_agents
        )

        if agent_allowed:
            checks_passed.append("agent_authorized")
        else:
            checks_failed.append("agent_not_authorized")
            return PolicyEvaluationResponse(
                allowed=False,
                action=PolicyAction.DENY,
                policy_id=policy["_id"],
                reason=f"Agent {subject_id} not authorized for {sensitivity} data",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
            )

    # Check required capabilities
    required_capabilities = sensitivity_rule.get("required_capabilities", [])
    subject_capabilities = subject.get("capabilities", [])

    if required_capabilities:
        has_capabilities = all(
            cap in subject_capabilities for cap in required_capabilities
        )

        if has_capabilities:
            checks_passed.append("capabilities_verified")
        else:
            checks_failed.append("missing_capabilities")
            return PolicyEvaluationResponse(
                allowed=False,
                action=PolicyAction.DENY,
                policy_id=policy["_id"],
                reason="Missing required capabilities",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
            )

    # Check encryption requirement
    if sensitivity_rule.get("require_encryption", False):
        if not resource.get("encrypted", False):
            checks_failed.append("encryption_required")
            return PolicyEvaluationResponse(
                allowed=False,
                action=PolicyAction.DENY,
                policy_id=policy["_id"],
                reason="Encryption required for this sensitivity level",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
            )
        else:
            checks_passed.append("encryption_verified")

    # All checks passed
    return PolicyEvaluationResponse(
        allowed=True,
        action=PolicyAction.ALLOW,
        policy_id=policy["_id"],
        reason="All DLP checks passed",
        checks_passed=checks_passed,
        checks_failed=checks_failed,
    )


async def evaluate_rbac_policy(
    policy: Dict[str, Any],
    action: str,
    subject: Dict[str, Any],
) -> PolicyEvaluationResponse:
    """
    Evaluate RBAC (Role-Based Access Control) policy.

    Checks role permissions for requested action.
    """
    roles = policy.get("rbac_roles", {})
    subject_role = subject.get("role", "default")

    if subject_role not in roles:
        return PolicyEvaluationResponse(
            allowed=False,
            action=PolicyAction.DENY,
            policy_id=policy["_id"],
            reason=f"Role {subject_role} not defined in policy",
            checks_failed=["role_not_found"],
        )

    role_config = roles[subject_role]
    permissions = role_config.get("permissions", [])

    # Check if action is permitted
    if "*" in permissions or action in permissions:
        return PolicyEvaluationResponse(
            allowed=True,
            action=PolicyAction.ALLOW,
            policy_id=policy["_id"],
            reason=f"Role {subject_role} has permission for {action}",
            checks_passed=["role_authorized"],
        )
    else:
        return PolicyEvaluationResponse(
            allowed=False,
            action=PolicyAction.DENY,
            policy_id=policy["_id"],
            reason=f"Role {subject_role} lacks permission for {action}",
            checks_failed=["permission_denied"],
        )


async def evaluate_abac_policy(
    policy: Dict[str, Any],
    context: Dict[str, Any],
) -> PolicyEvaluationResponse:
    """
    Evaluate ABAC (Attribute-Based Access Control) policy.

    Checks attribute conditions from context.
    """
    conditions = policy.get("conditions", [])

    if not conditions:
        return PolicyEvaluationResponse(
            allowed=True,
            action=PolicyAction.ALLOW,
            policy_id=policy["_id"],
            reason="No ABAC conditions defined",
            checks_passed=["no_conditions"],
        )

    checks_passed = []
    checks_failed = []

    for condition in conditions:
        attribute = condition.get("attribute")
        operator = condition.get("operator")
        value = condition.get("value")

        context_value = context.get(attribute)

        # Evaluate condition
        passed = False

        if operator == "equals":
            passed = context_value == value
        elif operator == "not_equals":
            passed = context_value != value
        elif operator == "in":
            passed = context_value in value
        elif operator == "contains":
            passed = value in context_value if context_value else False
        elif operator == "greater_than":
            passed = context_value > value if context_value else False
        elif operator == "less_than":
            passed = context_value < value if context_value else False

        if passed:
            checks_passed.append(f"condition_{attribute}")
        else:
            checks_failed.append(f"condition_{attribute}")

    # All conditions must pass
    if checks_failed:
        return PolicyEvaluationResponse(
            allowed=False,
            action=PolicyAction.DENY,
            policy_id=policy["_id"],
            reason="ABAC conditions not met",
            checks_passed=checks_passed,
            checks_failed=checks_failed,
        )
    else:
        return PolicyEvaluationResponse(
            allowed=True,
            action=PolicyAction.ALLOW,
            policy_id=policy["_id"],
            reason="All ABAC conditions met",
            checks_passed=checks_passed,
        )


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check(mongo: MongoManager = Depends(get_mongo)):
    """Check service health."""
    mongo_healthy = await mongo.health_check()
    health_status = ServiceHealth.HEALTHY if mongo_healthy else ServiceHealth.UNHEALTHY

    return HealthResponse(
        status=health_status,
        service="policies",
        region="us-east-1",
        checks={"mongo": mongo_healthy},
    )


@app.post("/v1/policies:evaluate", response_model=PolicyEvaluationResponse)
async def evaluate_policy(
    request: PolicyEvaluationRequest,
    mongo: MongoManager = Depends(get_mongo),
):
    """
    Evaluate policy for given request.

    Checks DLP, RBAC, or ABAC policies based on request type.

    Args:
        request: Policy evaluation request

    Returns:
        Evaluation result with allow/deny decision
    """
    try:
        # Get policy from database
        policy = await mongo.find_one(
            "policies",
            {
                "tenant_id": request.tenant_id,
                "policy_type": request.policy_type.value,
                "enabled": True,
            },
        )

        if not policy:
            # No policy defined, default to allow with logging
            logger.warning(
                f"No {request.policy_type} policy found for tenant {request.tenant_id}"
            )
            return PolicyEvaluationResponse(
                allowed=True,
                action=PolicyAction.ALLOW,
                reason=f"No {request.policy_type} policy defined (default allow)",
                checks_passed=["no_policy"],
            )

        # Evaluate based on policy type
        if request.policy_type == PolicyType.DLP:
            result = await evaluate_dlp_policy(
                policy, request.resource, request.subject
            )
        elif request.policy_type == PolicyType.RBAC:
            result = await evaluate_rbac_policy(
                policy, request.action, request.subject
            )
        elif request.policy_type == PolicyType.ABAC:
            result = await evaluate_abac_policy(policy, request.context)
        else:
            result = PolicyEvaluationResponse(
                allowed=True,
                action=PolicyAction.ALLOW,
                reason=f"Policy type {request.policy_type} evaluation not implemented",
            )

        # Log evaluation
        log_action = policy.get("actions", {}).get("log", True)
        if log_action:
            await mongo.insert_one(
                "events",
                {
                    "tenant_id": request.tenant_id,
                    "trace_id": request.context.get("trace_id", "unknown"),
                    "type": "policy_checked",
                    "outcome": "allowed" if result.allowed else "denied",
                    "policy_type": request.policy_type.value,
                    "policy_id": result.policy_id,
                    "subject": request.subject.get("id"),
                    "action": request.action,
                    "policy_checks": {
                        "passed": result.checks_passed,
                        "failed": result.checks_failed,
                    },
                    "timestamp": datetime.utcnow(),
                },
            )

        return result

    except Exception as e:
        logger.error(f"Error evaluating policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate policy: {str(e)}",
        )


@app.post("/v1/policies", status_code=status.HTTP_201_CREATED)
async def create_policy(
    request: CreatePolicyRequest,
    mongo: MongoManager = Depends(get_mongo),
):
    """Create new policy."""
    policy_id = f"policy:{request.tenant_id}:{request.policy_type.value}"

    policy_doc = {
        "_id": policy_id,
        "tenant_id": request.tenant_id,
        "policy_type": request.policy_type.value,
        "name": request.name,
        "description": request.description,
        "enabled": request.enabled,
        "sensitivity_rules": request.sensitivity_rules,
        "rbac_roles": request.rbac_roles,
        "capability_matrix": request.capability_matrix,
        "conditions": request.conditions,
        "actions": request.actions,
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    await mongo.insert_one("policies", policy_doc)

    logger.info(f"Created policy {policy_id}")

    return {"id": policy_id, "status": "created"}


@app.get("/v1/policies/{tenant_id}")
async def list_policies(
    tenant_id: str,
    policy_type: Optional[PolicyType] = None,
    mongo: MongoManager = Depends(get_mongo),
):
    """List policies for tenant."""
    filter_dict = {"tenant_id": tenant_id}

    if policy_type:
        filter_dict["policy_type"] = policy_type.value

    policies = await mongo.find("policies", filter_dict, limit=100)

    return {"policies": policies, "total": len(policies)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8102)
