# QMN API Reference Guide
## Complete API Documentation for Developers

**Version**: 1.0
**Last Updated**: November 1, 2025
**Base URL**: `http://localhost:8000` (Development)

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Identity Service API](#identity-service-api)
3. [Router Service API](#router-service-api)
4. [Hyphal Memory Service API](#hyphal-memory-service-api)
5. [Policies Service API](#policies-service-api)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Code Examples](#code-examples)

---

## Authentication

### Overview

QMN uses tenant-based authentication. Each request must include the tenant ID in the URL path.

### Headers

```http
Content-Type: application/json
X-Trace-ID: optional-trace-id-for-debugging
```

### Tenant ID

Obtain your tenant ID by creating a tenant via the Identity Service (see below).

---

## Identity Service API

**Base URL**: `http://localhost:8001`

### Create Tenant

Create a new tenant in the QMN system.

**Endpoint**: `POST /v1/tenants`

**Request Body**:
```json
{
  "id": "string (required, unique)",
  "name": "string (required)",
  "plan_tier": "free|pro|enterprise (required)",
  "kms_key_id": "string (required)",
  "region_preference": "string (optional)",
  "metadata": {
    "key": "value"
  }
}
```

**Response** (201 Created):
```json
{
  "id": "my-company",
  "name": "My Company",
  "plan_tier": "pro",
  "status": "active",
  "kms_key_id": "kms-abc123",
  "region_preference": "us-east-1",
  "created_at": "2025-11-01T12:00:00Z",
  "updated_at": "2025-11-01T12:00:00Z",
  "metadata": {
    "industry": "technology"
  }
}
```

**Example**:
```typescript
const response = await fetch('http://localhost:8001/v1/tenants', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    id: 'acme-corp',
    name: 'Acme Corporation',
    plan_tier: 'enterprise',
    kms_key_id: 'kms-acme-001',
    region_preference: 'us-west-2',
    metadata: {
      industry: 'manufacturing',
      employee_count: 500
    }
  })
});
const tenant = await response.json();
console.log('Tenant created:', tenant.id);
```

---

### Get Tenant

Retrieve tenant information.

**Endpoint**: `GET /v1/tenants/{tenant_id}`

**Path Parameters**:
- `tenant_id` (string, required): Tenant ID

**Response** (200 OK):
```json
{
  "id": "my-company",
  "name": "My Company",
  "plan_tier": "pro",
  "status": "active",
  "kms_key_id": "kms-abc123",
  "region_preference": "us-east-1",
  "created_at": "2025-11-01T12:00:00Z",
  "updated_at": "2025-11-01T12:00:00Z",
  "metadata": {}
}
```

**Example**:
```typescript
const response = await fetch('http://localhost:8001/v1/tenants/acme-corp');
const tenant = await response.json();
console.log('Tenant plan:', tenant.plan_tier);
```

---

### Update Tenant

Update tenant information.

**Endpoint**: `PATCH /v1/tenants/{tenant_id}`

**Request Body**:
```json
{
  "name": "string (optional)",
  "plan_tier": "free|pro|enterprise (optional)",
  "status": "active|suspended (optional)",
  "metadata": {}
}
```

**Response** (200 OK):
```json
{
  "id": "my-company",
  "name": "Updated Name",
  "plan_tier": "enterprise",
  "status": "active",
  ...
}
```

---

## Router Service API

**Base URL**: `http://localhost:8003`

### Broadcast Nutrient

Broadcast ephemeral knowledge to the mycelial network.

**Endpoint**: `POST /v1/broadcast/{tenant_id}/{trace_id}`

**Path Parameters**:
- `tenant_id` (string, required): Tenant ID
- `trace_id` (string, required): Unique trace ID for this broadcast

**Request Body**:
```json
{
  "summary": "string (required, max 1000 chars)",
  "embedding": [0.1, 0.2, ...] (required, 1536 floats),
  "snippets": ["string"] (required, array of strings),
  "tool_hints": ["string"] (optional, array of strings),
  "sensitivity": "public|internal|confidential (required)",
  "max_hops": number (required, 1-10),
  "ttl_sec": number (required, 60-86400),
  "quota_cost": number (required, 1-10000)
}
```

**Response** (200 OK):
```json
{
  "nutrient_id": "uuid",
  "status": "broadcast_initiated",
  "timestamp": "2025-11-01T12:00:00Z"
}
```

**Example**:
```typescript
// Generate embedding (use real embedding API in production)
const embedding = new Array(1536).fill(0).map(() => Math.random());

const response = await fetch(
  `http://localhost:8003/v1/broadcast/acme-corp/trace-${Date.now()}`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      summary: 'Discovered performance optimization in checkout flow',
      embedding,
      snippets: [
        'Reduced checkout time by 40%',
        'Implemented lazy loading for payment forms',
        'Added caching for shipping calculations'
      ],
      tool_hints: ['performance', 'optimization', 'frontend'],
      sensitivity: 'internal',
      max_hops: 3,
      ttl_sec: 3600,
      quota_cost: 100
    })
  }
);
const result = await response.json();
console.log('Broadcast ID:', result.nutrient_id);
```

**Field Descriptions**:
- `summary`: Brief description of the knowledge being shared
- `embedding`: 1536-dimensional vector representation (use OpenAI, Cohere, etc.)
- `snippets`: Key pieces of information or code snippets
- `tool_hints`: Tags for categorization and routing
- `sensitivity`: Access level for this knowledge
- `max_hops`: How many network hops before expiration (1-10)
- `ttl_sec`: Time to live in seconds (60-86400 = 1 min to 24 hours)
- `quota_cost`: Cost in quota units (your internal billing metric)

---

## Hyphal Memory Service API

**Base URL**: `http://localhost:8004`

### Store Memory

Store persistent knowledge in the mycelial memory.

**Endpoint**: `POST /v1/hyphal/{tenant_id}`

**Path Parameters**:
- `tenant_id` (string, required): Tenant ID

**Request Body**:
```json
{
  "agent_id": "string (required)",
  "kind": "insight|snippet|decision|preference (required)",
  "content": {} (required, JSON object),
  "quality": number (required, 0.0-1.0),
  "sensitivity": "public|internal|confidential (required)",
  "metadata": {} (optional, JSON object),
  "embedding": [0.1, 0.2, ...] (required, 1536 floats),
  "expires_at": "ISO 8601 datetime (optional)"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "agent_id": "agent-001",
  "kind": "insight",
  "content": {
    "discovery": "..."
  },
  "quality": 0.85,
  "sensitivity": "internal",
  "created_at": "2025-11-01T12:00:00Z",
  "expires_at": null
}
```

**Example**:
```typescript
const embedding = new Array(1536).fill(0).map(() => Math.random());

const response = await fetch('http://localhost:8004/v1/hyphal/acme-corp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent_id: 'agent-analytics-01',
    kind: 'insight',
    content: {
      finding: 'Users are 3x more likely to convert on mobile',
      data_points: 15000,
      confidence: 0.95,
      recommendation: 'Optimize mobile checkout flow'
    },
    quality: 0.9,
    sensitivity: 'internal',
    metadata: {
      department: 'product',
      campaign: 'mobile-optimization-q4'
    },
    embedding
  })
});
const memory = await response.json();
console.log('Memory stored:', memory.id);
```

**Kind Types**:
- `insight`: High-level discoveries or learnings
- `snippet`: Code snippets, configurations, or specific solutions
- `decision`: Past decisions and their rationale
- `preference`: User or system preferences

**Quality Score**: 0.0 to 1.0
- `0.0-0.3`: Low quality, experimental
- `0.4-0.6`: Medium quality, useful
- `0.7-0.8`: High quality, validated
- `0.9-1.0`: Exceptional quality, mission-critical

---

### Search Memories

Search for relevant memories using semantic similarity.

**Endpoint**: `POST /v1/hyphal:search/{tenant_id}`

**Path Parameters**:
- `tenant_id` (string, required): Tenant ID

**Request Body**:
```json
{
  "embedding": [0.1, 0.2, ...] (required, 1536 floats),
  "min_quality": number (optional, default 0.5),
  "limit": number (optional, default 10, max 100),
  "kind_filter": "string (optional)"
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "id": "uuid",
      "agent_id": "agent-001",
      "kind": "insight",
      "content": {},
      "quality": 0.85,
      "created_at": "2025-11-01T12:00:00Z",
      "similarity": 0.92
    }
  ],
  "total": 5
}
```

**Example**:
```typescript
// User asks: "How can we improve mobile conversions?"
const query = "improve mobile conversions";
const embedding = generateEmbedding(query); // Use your embedding API

const response = await fetch(
  'http://localhost:8004/v1/hyphal:search/acme-corp',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      embedding,
      min_quality: 0.7,  // Only high-quality memories
      limit: 10,
      kind_filter: 'insight'  // Only insights
    })
  }
);

const { results } = await response.json();
results.forEach(memory => {
  console.log(`Found: ${memory.content.finding}`);
  console.log(`Similarity: ${(memory.similarity * 100).toFixed(1)}%`);
  console.log(`Quality: ${(memory.quality * 100).toFixed(0)}%`);
});
```

**Similarity Score**: Cosine similarity between query and memory embeddings
- `0.9-1.0`: Extremely relevant
- `0.8-0.9`: Highly relevant
- `0.7-0.8`: Moderately relevant
- `0.6-0.7`: Somewhat relevant
- `<0.6`: Low relevance

---

## Policies Service API

**Base URL**: `http://localhost:8005`

### Create Policy

Create a knowledge sharing policy.

**Endpoint**: `POST /v1/policies/{tenant_id}`

**Request Body**:
```json
{
  "name": "string (required)",
  "pattern": "string (required, glob pattern)",
  "action": "allow|deny|require_approval (required)",
  "sensitivity_level": "public|internal|confidential (required)",
  "priority": number (required, 1-100)
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "tenant_id": "my-company",
  "name": "Block Confidential Broadcasts",
  "pattern": "confidential/*",
  "action": "deny",
  "sensitivity_level": "confidential",
  "priority": 90,
  "created_at": "2025-11-01T12:00:00Z"
}
```

---

### List Policies

List all policies for a tenant.

**Endpoint**: `GET /v1/policies/{tenant_id}`

**Query Parameters**:
- `active` (boolean, optional): Filter by active status
- `limit` (number, optional): Max results (default 100)

**Response** (200 OK):
```json
{
  "policies": [
    {
      "id": "uuid",
      "name": "Policy Name",
      "pattern": "pattern",
      "action": "allow",
      ...
    }
  ],
  "total": 5
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request body",
    "details": {
      "field": "embedding",
      "issue": "must be array of 1536 floats"
    }
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `TENANT_NOT_FOUND` | Tenant ID not found |
| `QUOTA_EXCEEDED` | Tenant quota exceeded |
| `INVALID_EMBEDDING` | Embedding format or dimension incorrect |
| `POLICY_VIOLATION` | Request blocked by policy |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## Rate Limiting

### Limits by Plan Tier

| Plan | Broadcasts/min | Searches/min | Stores/min |
|------|----------------|--------------|------------|
| Free | 10 | 30 | 10 |
| Pro | 100 | 300 | 100 |
| Enterprise | 1000 | 3000 | 1000 |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1698765432
```

### Handling Rate Limits

```typescript
async function broadcastWithRetry(data: BroadcastRequest, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const response = await fetch(url, { method: 'POST', body: JSON.stringify(data) });

    if (response.status === 429) {
      const resetTime = parseInt(response.headers.get('X-RateLimit-Reset') || '0');
      const waitMs = (resetTime * 1000) - Date.now();

      console.log(`Rate limited. Waiting ${waitMs}ms...`);
      await new Promise(resolve => setTimeout(resolve, waitMs));
      continue;
    }

    return response.json();
  }

  throw new Error('Max retries exceeded');
}
```

---

## Code Examples

### Complete TypeScript Client

```typescript
class QMNClient {
  constructor(
    private baseUrl: string,
    private tenantId: string
  ) {}

  async broadcast(traceId: string, data: BroadcastRequest): Promise<BroadcastResponse> {
    const response = await fetch(
      `${this.baseUrl}/v1/broadcast/${this.tenantId}/${traceId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error.message);
    }

    return response.json();
  }

  async storeMemory(data: MemoryStoreRequest): Promise<MemoryResponse> {
    const response = await fetch(
      `${this.baseUrl}/v1/hyphal/${this.tenantId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }
    );

    if (!response.ok) {
      throw new Error('Failed to store memory');
    }

    return response.json();
  }

  async searchMemories(query: MemorySearchRequest): Promise<SearchResponse> {
    const response = await fetch(
      `${this.baseUrl}/v1/hyphal:search/${this.tenantId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(query)
      }
    );

    return response.json();
  }
}

// Usage
const client = new QMNClient('http://localhost:8000', 'my-tenant');

// Broadcast
await client.broadcast('trace-123', {
  summary: 'Discovery',
  embedding: [...],
  snippets: ['snippet1'],
  tool_hints: [],
  sensitivity: 'internal',
  max_hops: 3,
  ttl_sec: 3600,
  quota_cost: 100
});

// Store
await client.storeMemory({
  agent_id: 'agent-01',
  kind: 'insight',
  content: { finding: 'Important discovery' },
  quality: 0.85,
  sensitivity: 'internal',
  embedding: [...]
});

// Search
const results = await client.searchMemories({
  embedding: [...],
  min_quality: 0.7,
  limit: 10
});
```

---

### Python Client Example

```python
import requests
from typing import List, Dict, Any

class QMNClient:
    def __init__(self, base_url: str, tenant_id: str):
        self.base_url = base_url
        self.tenant_id = tenant_id

    def broadcast(self, trace_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/broadcast/{self.tenant_id}/{trace_id}"
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def store_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/hyphal/{self.tenant_id}"
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def search_memories(self, query: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/hyphal:search/{self.tenant_id}"
        response = requests.post(url, json=query)
        response.raise_for_status()
        return response.json()

# Usage
client = QMNClient("http://localhost:8000", "my-tenant")

# Broadcast
client.broadcast("trace-123", {
    "summary": "Discovery",
    "embedding": [0.1] * 1536,
    "snippets": ["snippet1"],
    "tool_hints": [],
    "sensitivity": "internal",
    "max_hops": 3,
    "ttl_sec": 3600,
    "quota_cost": 100
})

# Search
results = client.search_memories({
    "embedding": [0.1] * 1536,
    "min_quality": 0.7,
    "limit": 10
})

print(f"Found {len(results['results'])} memories")
```

---

## Best Practices

### 1. Embedding Generation

**Don't** use random or hash-based embeddings in production:
```typescript
// ❌ Bad for production
const embedding = new Array(1536).fill(0).map(() => Math.random());
```

**Do** use proper embedding APIs:
```typescript
// ✅ Good for production
import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: text
  });
  return response.data[0].embedding;
}
```

### 2. Error Handling

Always handle errors gracefully:

```typescript
try {
  await qmnClient.broadcast(traceId, data);
} catch (error) {
  if (error.status === 429) {
    // Rate limited - wait and retry
    await sleep(1000);
    return retry();
  } else if (error.status === 422) {
    // Validation error - fix data
    console.error('Invalid data:', error.details);
  } else {
    // Unknown error - log and alert
    logger.error('QMN broadcast failed', error);
  }
}
```

### 3. Quality Scoring

Use consistent quality scoring:

```typescript
function calculateQuality(data: any): number {
  let score = 0.5; // Base score

  // Increase for validation
  if (data.validated) score += 0.2;

  // Increase for usage
  if (data.usageCount > 10) score += 0.1;

  // Increase for freshness
  const ageMs = Date.now() - new Date(data.created_at).getTime();
  if (ageMs < 86400000) score += 0.1; // Less than 1 day

  // Increase for user feedback
  if (data.positive_feedback > data.negative_feedback) score += 0.1;

  return Math.min(1.0, score);
}
```

---

**Next**: See [Command Center Integration Guide](./COMMAND_CENTER_INTEGRATION_GUIDE.md) for complete integration tutorial.
