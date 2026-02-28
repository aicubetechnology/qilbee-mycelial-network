# API Reference

Complete API documentation for Qilbee Mycelial Network Python SDK v0.2.0.

## Table of Contents

- [MycelialClient](#mycelialclient)
- [Nutrient](#nutrient)
- [Outcome](#outcome)
- [Sensitivity](#sensitivity)
- [Context](#context)
- [QMNSettings](#qmnsettings)
- [Control Plane Methods](#control-plane-methods) *(New in v0.2.0)*
- [Hyphal Memory Methods](#hyphal-memory-methods) *(New in v0.2.0)*

---

## MycelialClient

The main client for interacting with the Qilbee Mycelial Network.

### Constructor

```python
class MycelialClient:
    def __init__(self, settings: QMNSettings)
```

**Parameters:**
- `settings` (QMNSettings): Configuration settings for the client

**Example:**
```python
from qilbee_mycelial_network import MycelialClient, QMNSettings

settings = QMNSettings(
    api_key="qmn_your_key",
    api_base_url="https://api.qilbee.io"
)

client = MycelialClient(settings)
```

### Factory Methods

#### `create_from_env()`

Create client from environment variables.

```python
@classmethod
async def create_from_env(cls) -> MycelialClient
```

**Returns:**
- `MycelialClient`: Configured client instance

**Environment Variables:**
- `QMN_API_KEY` (required): Your API key
- `QMN_API_BASE_URL`: API endpoint (default: https://api.qilbee.io)
- `QMN_PREFERRED_REGION`: Preferred region
- `QMN_TRANSPORT`: Transport protocol (http/grpc/quic)
- `QMN_DEBUG`: Enable debug mode

**Example:**
```python
import asyncio
from qilbee_mycelial_network import MycelialClient

async def main():
    async with MycelialClient.create_from_env() as client:
        # Use client
        pass

asyncio.run(main())
```

### Methods

#### `broadcast()`

Broadcast a nutrient to the mycelial network.

```python
async def broadcast(
    self,
    nutrient: Nutrient,
    *,
    timeout_sec: Optional[int] = None
) -> BroadcastResponse
```

**Parameters:**
- `nutrient` (Nutrient): The nutrient to broadcast
- `timeout_sec` (Optional[int]): Request timeout in seconds

**Returns:**
- `BroadcastResponse`: Response containing broadcast status and metadata

**Raises:**
- `APIError`: If the broadcast fails
- `TimeoutError`: If the request times out
- `ValidationError`: If the nutrient is invalid

**Example:**
```python
from qilbee_mycelial_network import Nutrient, Sensitivity

nutrient = Nutrient.seed(
    summary="Database optimization query",
    embedding=[0.1] * 1536,
    snippets=["SELECT * FROM large_table"],
    tool_hints=["db.analyze"],
    sensitivity=Sensitivity.INTERNAL
)

response = await client.broadcast(nutrient)
print(f"Broadcast ID: {response.broadcast_id}")
```

#### `collect()`

Collect contexts from the network matching the demand embedding.

```python
async def collect(
    self,
    demand_embedding: List[float],
    *,
    window_ms: int = 300,
    top_k: int = 5,
    diversify: bool = True,
    min_similarity: float = 0.7,
    timeout_sec: Optional[int] = None
) -> Context
```

**Parameters:**
- `demand_embedding` (List[float]): Query embedding vector (1536-dim)
- `window_ms` (int): Time window in milliseconds (default: 300)
- `top_k` (int): Maximum number of results (default: 5)
- `diversify` (bool): Apply MMR diversity (default: True)
- `min_similarity` (float): Minimum cosine similarity (default: 0.7)
- `timeout_sec` (Optional[int]): Request timeout

**Returns:**
- `Context`: Collection of matching contexts with trace ID

**Example:**
```python
contexts = await client.collect(
    demand_embedding=get_embedding("database performance"),
    window_ms=500,
    top_k=10,
    diversify=True,
    min_similarity=0.75
)

for content in contexts.contents:
    print(f"Agent: {content['agent_id']}")
    print(f"Summary: {content['summary']}")
    print(f"Similarity: {content['score']}")
```

#### `record_outcome()`

Record task outcome for reinforcement learning.

```python
async def record_outcome(
    self,
    trace_id: str,
    outcome: Outcome,
    *,
    metadata: Optional[Dict[str, Any]] = None,
    timeout_sec: Optional[int] = None
) -> OutcomeResponse
```

**Parameters:**
- `trace_id` (str): Trace ID from collect() response
- `outcome` (Outcome): Task outcome with score
- `metadata` (Optional[Dict]): Additional metadata
- `timeout_sec` (Optional[int]): Request timeout

**Returns:**
- `OutcomeResponse`: Confirmation of outcome recording

**Example:**
```python
from qilbee_mycelial_network import Outcome

# Successful task
await client.record_outcome(
    trace_id=contexts.trace_id,
    outcome=Outcome.with_score(0.92),
    metadata={"task_type": "optimization", "duration_ms": 1250}
)

# Per-hop outcomes (v0.2.0) - granular per-agent feedback
await client.record_outcome(
    trace_id=contexts.trace_id,
    outcome=Outcome.with_hop_scores(
        score=0.85,
        hop_outcomes={"agent-1": 0.9, "agent-2": 0.6}
    )
)

# Failed task
await client.record_outcome(
    trace_id=contexts.trace_id,
    outcome=Outcome.with_score(0.0),
    metadata={"error": "timeout"}
)
```

#### `hyphal_store()` *(New in v0.2.0)*

Store persistent knowledge in the hyphal memory vector database.

```python
async def hyphal_store(
    self,
    agent_id: str,
    kind: str,
    content: Dict[str, Any],
    embedding: List[float],
    *,
    quality: float = 0.5,
    sensitivity: str = "internal",
    metadata: Optional[Dict[str, Any]] = None,
    timeout_sec: Optional[int] = None
) -> StoreResponse
```

**Parameters:**
- `agent_id` (str): Agent identifier
- `kind` (str): Memory type (insight, snippet, decision, preference)
- `content` (Dict): Memory content payload
- `embedding` (List[float]): 1536-dim vector representation
- `quality` (float): Quality score 0.0-1.0
- `sensitivity` (str): Sensitivity level
- `metadata` (Optional[Dict]): Additional metadata
- `timeout_sec` (Optional[int]): Request timeout

**Example:**
```python
await client.hyphal_store(
    agent_id="agent-001",
    kind="insight",
    content={"finding": "Important discovery about performance"},
    embedding=[0.1] * 1536,
    quality=0.9,
    sensitivity="internal"
)
```

#### `hyphal_search()` *(New in v0.2.0)*

Search stored memories using semantic similarity.

```python
async def hyphal_search(
    self,
    embedding: List[float],
    *,
    top_k: int = 10,
    min_quality: float = 0.5,
    filters: Optional[Dict[str, str]] = None,
    timeout_sec: Optional[int] = None
) -> SearchResponse
```

**Parameters:**
- `embedding` (List[float]): Query embedding vector (1536-dim)
- `top_k` (int): Maximum results (default: 10)
- `min_quality` (float): Minimum quality score (default: 0.5)
- `filters` (Optional[Dict]): Filters (e.g., `{"kind": "insight"}`)
- `timeout_sec` (Optional[int]): Request timeout

**Example:**
```python
results = await client.hyphal_search(
    embedding=[0.1] * 1536,
    top_k=10,
    filters={"kind": "insight"}
)
for result in results.results:
    print(f"Content: {result.content}, Score: {result.similarity}")
```

#### `get_usage()` *(New in v0.2.0)*

Get usage metrics for the current tenant.

```python
async def get_usage(
    self,
    *,
    timeout_sec: Optional[int] = None
) -> UsageResponse
```

**Returns:**
- `UsageResponse`: Usage metrics including broadcast count, collect count, and storage usage

**Example:**
```python
usage = await client.get_usage()
print(f"Broadcasts: {usage.broadcasts}")
print(f"Collections: {usage.collections}")
```

#### `register_agent()`

Register an agent with the network.

```python
async def register_agent(
    self,
    agent_id: str,
    profile_embedding: List[float],
    capabilities: List[str],
    *,
    metadata: Optional[Dict[str, Any]] = None,
    timeout_sec: Optional[int] = None
) -> AgentResponse
```

**Parameters:**
- `agent_id` (str): Unique agent identifier
- `profile_embedding` (List[float]): Agent profile vector (1536-dim)
- `capabilities` (List[str]): Agent capabilities/skills
- `metadata` (Optional[Dict]): Additional agent metadata
- `timeout_sec` (Optional[int]): Request timeout

**Returns:**
- `AgentResponse`: Agent registration confirmation

**Example:**
```python
await client.register_agent(
    agent_id="code-reviewer-01",
    profile_embedding=get_embedding("code review security performance"),
    capabilities=[
        "code.review",
        "security.audit",
        "performance.analyze"
    ],
    metadata={
        "languages": ["python", "javascript", "go"],
        "expertise": ["security", "performance"],
        "version": "2.0.1"
    }
)
```

#### `health_check()`

Check client and service health.

```python
async def health_check(
    self,
    *,
    timeout_sec: Optional[int] = 5
) -> HealthResponse
```

**Returns:**
- `HealthResponse`: Health status of services

**Example:**
```python
health = await client.health_check()
print(f"Status: {health.status}")
print(f"Latency: {health.latency_ms}ms")
```

---

## Nutrient

Data model for nutrients flowing through the network.

### Constructor

```python
class Nutrient(BaseModel):
    summary: str
    embedding: List[float]
    snippets: Optional[List[str]] = None
    tool_hints: Optional[List[str]] = None
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    ttl_sec: int = 300
    max_hops: int = 3
    metadata: Optional[Dict[str, Any]] = None
```

**Fields:**
- `summary` (str): Brief description of nutrient content
- `embedding` (List[float]): 1536-dimension vector representation
- `snippets` (Optional[List[str]]): Code snippets or text fragments
- `tool_hints` (Optional[List[str]]): Suggested tools/capabilities
- `sensitivity` (Sensitivity): Data sensitivity level
- `ttl_sec` (int): Time-to-live in seconds
- `max_hops` (int): Maximum network hops
- `metadata` (Optional[Dict]): Additional data

### Factory Methods

#### `seed()`

Create a new nutrient instance.

```python
@classmethod
def seed(
    cls,
    summary: str,
    embedding: List[float],
    **kwargs
) -> Nutrient
```

**Example:**
```python
from qilbee_mycelial_network import Nutrient, Sensitivity

nutrient = Nutrient.seed(
    summary="Database query optimization needed",
    embedding=[0.1] * 1536,
    snippets=[
        "SELECT * FROM users WHERE created_at > '2024-01-01'",
        "Execution time: 2.3s"
    ],
    tool_hints=["db.analyze", "query.optimize"],
    sensitivity=Sensitivity.INTERNAL,
    ttl_sec=180,
    max_hops=5,
    metadata={"database": "postgresql", "table": "users"}
)
```

---

## Outcome

Task outcome for reinforcement learning.

### Constructor

```python
class Outcome(BaseModel):
    score: float
    details: Optional[str] = None
    hop_outcomes: Optional[Dict[str, float]] = None
```

**Fields:**
- `score` (float): Success score between 0.0 and 1.0
- `details` (Optional[str]): Additional outcome details
- `hop_outcomes` (Optional[Dict[str, float]]): Per-agent scores for granular RL *(New in v0.2.0)*

### Factory Methods

#### `with_score()`

Create outcome with score.

```python
@classmethod
def with_score(
    cls,
    score: float,
    details: Optional[str] = None
) -> Outcome
```

**Parameters:**
- `score` (float): Success score (0.0 to 1.0)
- `details` (Optional[str]): Outcome description

**Example:**
```python
from qilbee_mycelial_network import Outcome

# Successful outcome
success = Outcome.with_score(0.95, "Task completed successfully")

# Partial success
partial = Outcome.with_score(0.6, "Task completed with warnings")

# Failure
failure = Outcome.with_score(0.0, "Task failed: timeout")
```

#### `with_hop_scores()` *(New in v0.2.0)*

Create outcome with per-agent scores for granular reinforcement learning.

```python
@classmethod
def with_hop_scores(
    cls,
    score: float,
    hop_outcomes: Dict[str, float],
    details: Optional[str] = None
) -> Outcome
```

**Parameters:**
- `score` (float): Overall success score (0.0 to 1.0)
- `hop_outcomes` (Dict[str, float]): Map of agent_id to individual score
- `details` (Optional[str]): Outcome description

**Example:**
```python
from qilbee_mycelial_network import Outcome

# Per-hop feedback - reward useful agents more
outcome = Outcome.with_hop_scores(
    score=0.85,
    hop_outcomes={
        "agent-researcher-01": 0.95,  # Very helpful
        "agent-coder-03": 0.8,        # Helpful
        "agent-reviewer-02": 0.4      # Less helpful
    }
)
await client.record_outcome(trace_id=contexts.trace_id, outcome=outcome)
```

---

## Sensitivity

Enumeration of data sensitivity levels.

```python
class Sensitivity(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
```

**Levels:**
- `PUBLIC`: Public information, no restrictions
- `INTERNAL`: Internal use, company-wide access
- `CONFIDENTIAL`: Confidential data, restricted access
- `SECRET`: Secret data, highly restricted

**Example:**
```python
from qilbee_mycelial_network import Sensitivity, Nutrient

# Public nutrient
public_nutrient = Nutrient.seed(
    summary="Public API documentation",
    embedding=[...],
    sensitivity=Sensitivity.PUBLIC
)

# Secret nutrient
secret_nutrient = Nutrient.seed(
    summary="Authentication credentials",
    embedding=[...],
    sensitivity=Sensitivity.SECRET
)
```

---

## Context

Collection of contexts from the network.

### Model

```python
class Context(BaseModel):
    trace_id: str
    contents: List[Dict[str, Any]]
    metadata: Dict[str, Any]
```

**Fields:**
- `trace_id` (str): Unique trace identifier for outcome recording
- `contents` (List[Dict]): Matched contexts
- `metadata` (Dict): Collection metadata (timing, stats, etc.)

**Content Fields:**
- `agent_id` (str): Source agent identifier
- `summary` (str): Content summary
- `data` (Any): Context data
- `score` (float): Similarity score
- `timestamp` (str): ISO 8601 timestamp

**Example:**
```python
contexts = await client.collect(demand_embedding=[...])

print(f"Trace ID: {contexts.trace_id}")
print(f"Found {len(contexts.contents)} contexts")

for content in contexts.contents:
    print(f"Agent: {content['agent_id']}")
    print(f"Score: {content['score']:.3f}")
    print(f"Summary: {content['summary']}")
    print(f"Data: {content['data']}")
```

---

## QMNSettings

Configuration settings for MycelialClient.

### Constructor

```python
class QMNSettings(BaseModel):
    api_key: str
    api_base_url: str = "https://api.qilbee.io"
    preferred_region: Optional[str] = None
    transport: str = "http"
    timeout_sec: int = 30
    max_retries: int = 3
    debug: bool = False
```

**Fields:**
- `api_key` (str): QMN API key (required)
- `api_base_url` (str): API endpoint URL
- `preferred_region` (Optional[str]): Preferred region (us-east-1, etc.)
- `transport` (str): Transport protocol (http/grpc/quic)
- `timeout_sec` (int): Default request timeout
- `max_retries` (int): Maximum retry attempts
- `debug` (bool): Enable debug logging

**Example:**
```python
from qilbee_mycelial_network import QMNSettings, MycelialClient

# Production settings
prod_settings = QMNSettings(
    api_key="qmn_prod_key",
    api_base_url="https://api.qilbee.io",
    preferred_region="us-east-1",
    transport="grpc",
    timeout_sec=30,
    max_retries=3,
    debug=False
)

# Development settings
dev_settings = QMNSettings(
    api_key="qmn_dev_key",
    api_base_url="http://localhost:8200",
    transport="http",
    timeout_sec=60,
    debug=True
)

async with MycelialClient(prod_settings) as client:
    # Production client
    pass
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── QMNError (base exception)
│   ├── APIError (API request failed)
│   ├── ValidationError (invalid input)
│   ├── AuthenticationError (invalid API key)
│   ├── RateLimitError (rate limit exceeded)
│   └── TimeoutError (request timeout)
```

### Example

```python
from qilbee_mycelial_network import (
    MycelialClient,
    APIError,
    AuthenticationError,
    RateLimitError,
    TimeoutError
)

async def robust_broadcast(client, nutrient):
    try:
        response = await client.broadcast(nutrient)
        return response
    except AuthenticationError:
        print("Invalid API key")
    except RateLimitError as e:
        print(f"Rate limited. Retry after: {e.retry_after}s")
    except TimeoutError:
        print("Request timed out")
    except APIError as e:
        print(f"API error: {e.message}")
```

---

## Type Hints

The SDK is fully typed with Python type hints:

```python
from typing import List, Optional, Dict, Any
from qilbee_mycelial_network import MycelialClient, Nutrient, Context

async def process_task(
    client: MycelialClient,
    query: str,
    embedding: List[float]
) -> Optional[Dict[str, Any]]:
    """Process task with type safety."""
    contexts: Context = await client.collect(
        demand_embedding=embedding,
        top_k=5
    )

    if not contexts.contents:
        return None

    return {
        "trace_id": contexts.trace_id,
        "results": contexts.contents
    }
```

---

## Rate Limits

- **Broadcast**: 100 requests/min
- **Collect**: 200 requests/min
- **Record Outcome**: 500 requests/min
- **Register Agent**: 10 requests/min

Rate limit headers:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp (Unix epoch)

---

## Pagination

For methods returning large result sets:

```python
contexts = await client.collect(
    demand_embedding=[...],
    top_k=100,  # Max 100 results per request
    offset=0     # Pagination offset
)

# Get next page
next_contexts = await client.collect(
    demand_embedding=[...],
    top_k=100,
    offset=100
)
```

---

## Webhooks

Register webhooks for asynchronous notifications:

```python
await client.register_webhook(
    url="https://your-domain.com/webhook",
    events=["nutrient.received", "outcome.recorded"],
    secret="your_webhook_secret"
)
```

---

## Control Plane Methods *(New in v0.2.0)*

The SDK now provides full control plane access for managing tenants, API keys, and policies.

### Tenant Management

```python
# Create a new tenant (admin only)
await client.create_tenant(tenant_id="new-org", name="New Org", plan_tier="pro")

# Get tenant details
tenant = await client.get_tenant(tenant_id="new-org")

# List tenants (admin only)
tenants = await client.list_tenants(status_filter="active")

# Update tenant
await client.update_tenant(tenant_id="new-org", name="Updated Org", plan_tier="enterprise")

# Delete tenant (admin only)
await client.delete_tenant(tenant_id="new-org")
```

### API Key Management

```python
# Create a new API key
key = await client.create_key(name="prod-key", scopes=["*"])
print(f"Key: {key.api_key}")  # Store securely - shown only once

# Validate a key
result = await client.validate_key(api_key="qmn_...")

# List keys for tenant
keys = await client.list_keys()

# Revoke a key
await client.revoke_key(key_id="key-uuid")
```

### Policy Management

```python
# Evaluate a policy
result = await client.evaluate_policy(
    policy_type="rbac",
    context={"role": "admin", "resource": "tenants"}
)

# Create a policy
await client.create_policy(
    name="Block Confidential Broadcasts",
    policy_type="dlp",
    rules={"sensitivity": "confidential", "action": "deny"}
)

# List policies
policies = await client.list_policies()
```

---

## Hyphal Memory Methods *(New in v0.2.0)*

See `hyphal_store()` and `hyphal_search()` above under [Methods](#methods).

---

## Additional Resources

- **Examples**: [GitHub Examples](https://github.com/aicubetechnology/qilbee-mycelial-network/tree/main/examples)
- **Tutorials**: [qilbee.io/docs/tutorials](http://www.qilbee.io/docs/tutorials)
- **FAQ**: [qilbee.io/docs/faq](http://www.qilbee.io/docs/faq)
- **Support**: contact@aicube.ca
