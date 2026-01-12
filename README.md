# Qilbee Mycelial Network (QMN)

**Enterprise SaaS Platform for Adaptive AI Agent Communication**

[![PyPI version](https://badge.fury.io/py/qilbee-mycelial-network.svg)](https://pypi.org/project/qilbee-mycelial-network/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Test Coverage](https://img.shields.io/badge/coverage-68%25-green.svg)](https://github.com/aicubetechnology/qilbee-mycelial-network)

Qilbee Mycelial Network enables AI agents to form self-optimizing communication networks inspired by biological mycelia. Agents exchange "nutrients" (embeddings + context) through secure channels with automatic reinforcement learning, creating emergent collective intelligence.

---

## Table of Contents

- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [SDK Reference](#sdk-reference)
- [Services](#services)
- [Development](#development)
- [Deployment](#deployment)
- [Security](#security)
- [Performance](#performance)
- [Documentation](#documentation)
- [Support](#support)
- [License](#license)

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Zero Infrastructure** | `pip install` + API key - everything else managed |
| **Adaptive Routing** | Embedding-based similarity with reinforcement learning |
| **Vector Memory** | Distributed hyphal memory with semantic search (pgvector) |
| **Enterprise Security** | Multi-tenant isolation, DLP, RBAC/ABAC, audit trails |
| **Multi-Region** | Automatic regional routing with gossip synchronization |
| **Full Observability** | Built-in Prometheus metrics and Grafana dashboards |

---

## Quick Start

### Installation

```bash
pip install qilbee-mycelial-network
```

### Environment Setup

```bash
export QMN_API_KEY=qmn_your_api_key_here
```

### Basic Usage

```python
import asyncio
from qilbee_mycelial_network import MycelialClient, Nutrient, Outcome, Sensitivity

async def main():
    # Initialize client from environment
    async with MycelialClient.create_from_env() as client:

        # Broadcast knowledge to the network
        await client.broadcast(
            Nutrient.seed(
                summary="PostgreSQL query optimization discovered",
                embedding=[...],  # 1536-dimensional vector
                snippets=["Added index on user_id reduced query time by 80%"],
                tool_hints=["db.analyze", "sql.optimize"],
                sensitivity=Sensitivity.INTERNAL
            )
        )

        # Collect relevant contexts
        contexts = await client.collect(
            demand_embedding=[...],  # Your query embedding
            window_ms=300,
            top_k=5
        )

        # Process contexts and complete task...

        # Record outcome for reinforcement learning
        await client.record_outcome(
            trace_id=contexts.trace_id,
            outcome=Outcome.with_score(0.92)
        )

asyncio.run(main())
```

---

## Architecture

### System Overview

```
                              ┌─────────────────────────────────┐
                              │         Client SDK              │
                              │  pip install qilbee-mycelial-   │
                              │           network               │
                              └───────────────┬─────────────────┘
                                              │ HTTPS/gRPC
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CONTROL PLANE (Global)                           │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│  │    Identity     │   │      Keys       │   │    Policies     │            │
│  │   Port: 8100    │   │   Port: 8101    │   │   Port: 8102    │            │
│  │                 │   │                 │   │                 │            │
│  │ • Tenant CRUD   │   │ • Key lifecycle │   │ • DLP rules     │            │
│  │ • Plan tiers    │   │ • Validation    │   │ • RBAC/ABAC     │            │
│  │ • Quotas        │   │ • Rotation      │   │ • Rate limits   │            │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA PLANE (Regional)                            │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│  │     Router      │   │  Hyphal Memory  │   │ Reinforcement   │            │
│  │   Port: 8200    │   │   Port: 8201    │   │   Port: 8202    │            │
│  │                 │   │                 │   │                 │            │
│  │ • Broadcast     │   │ • Vector store  │   │ • Edge weights  │            │
│  │ • Collect       │   │ • Semantic      │   │ • Outcome       │            │
│  │ • Agent reg     │   │   search        │   │   recording     │            │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘            │
│                                                                              │
│  ┌─────────────────┐                                                         │
│  │     Gossip      │   State synchronization across regions                 │
│  │   Port: 8203    │                                                         │
│  └─────────────────┘                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA STORAGE                                   │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│  │   PostgreSQL    │   │    MongoDB      │   │     Redis       │            │
│  │   + pgvector    │   │                 │   │                 │            │
│  │   Port: 5432    │   │   Port: 27017   │   │   Port: 6379    │            │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Routing Algorithm

The router scores and ranks agents using multiple factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Cosine Similarity | Primary | Embedding similarity between nutrient and agent profiles |
| Edge Weights | 0.01-1.5 | Learned connection strengths from reinforcement learning |
| Demand Overlap | Additive | Recent task alignment scoring |
| Capability Match | +0.1 | Tool/skill matching bonus |
| MMR Diversity | λ=0.5 | Maximum Marginal Relevance for diverse results |

### Reinforcement Learning

Edge weights update based on task outcomes using synaptic plasticity:

```
Δw = α_pos × outcome - α_neg × (1 - outcome) - λ_decay
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| α_pos | 0.08 | Positive learning rate |
| α_neg | 0.04 | Negative learning rate |
| λ_decay | 0.002 | Natural decay to prevent stagnation |
| Min weight | 0.01 | Lower bound |
| Max weight | 1.5 | Upper bound (saturation) |

---

## SDK Reference

### MycelialClient

Main client for interacting with the network.

```python
from qilbee_mycelial_network import MycelialClient, QMNSettings

# From environment variables
async with MycelialClient.create_from_env() as client:
    pass

# From explicit settings
settings = QMNSettings(
    api_key="qmn_your_key",
    api_base_url="https://api.qilbee.io",
    preferred_region="us-east-1",
    timeout_sec=30,
    max_retries=3
)
client = MycelialClient(settings)
```

### Core Methods

| Method | Description | Storage |
|--------|-------------|---------|
| `broadcast(nutrient)` | Send ephemeral knowledge to network for routing | Temporary (TTL) |
| `collect(embedding, top_k)` | Collect matching contexts from network | - |
| `hyphal_store(agent_id, kind, content, embedding)` | Store persistent knowledge in vector DB | Permanent |
| `hyphal_search(embedding, top_k, filters)` | Search stored memories by similarity | - |
| `record_outcome(trace_id, outcome)` | Record task outcome for RL | - |
| `register_agent(agent_id, embedding, capabilities)` | Register/update agent profile | Permanent |
| `get_agent(agent_id)` | Get agent profile by ID | - |
| `list_agents(status_filter, capability)` | List agents for tenant | - |
| `deactivate_agent(agent_id)` | Deactivate agent (soft delete) | - |
| `rotate_key(grace_period_sec)` | Rotate API key | - |
| `health(service)` | Check service health | - |

### Broadcast vs Store

**Important distinction:**

| Operation | Method | Purpose | Duration |
|-----------|--------|---------|----------|
| **Broadcast** | `broadcast()` | Real-time knowledge sharing with other agents | Ephemeral (TTL: 1-3600 sec) |
| **Store** | `hyphal_store()` | Persistent knowledge storage in vector database | Permanent |

```python
# Ephemeral: Share discovery with network NOW (expires based on TTL)
await client.broadcast(Nutrient.seed(
    summary="Found bug fix",
    embedding=[...],
    ttl_sec=300  # Gone in 5 minutes
))

# Persistent: Store knowledge for future retrieval
await client.hyphal_store(
    agent_id="agent-001",
    kind="insight",
    content={"finding": "Database optimization technique"},
    embedding=[...],
    quality=0.9
)

# Search stored memories
results = await client.hyphal_search(
    embedding=[...],
    top_k=10,
    filters={"kind": "insight"}
)
```

### Data Models

**Nutrient** - Knowledge packet for broadcasting:
```python
Nutrient.seed(
    summary="Description of knowledge",
    embedding=[...],              # 1536-dim vector
    snippets=["code", "context"], # Supporting data
    tool_hints=["capability"],    # Routing hints
    sensitivity=Sensitivity.INTERNAL,
    ttl_sec=300,                  # Time-to-live (1-3600)
    max_hops=3                    # Propagation limit (1-10)
)
```

**Outcome** - Reinforcement learning feedback:
```python
Outcome.with_score(0.92)    # Custom score (0.0-1.0)
Outcome.success()           # Shorthand for score=1.0
```

**Sensitivity** - Data classification levels:
```python
Sensitivity.PUBLIC        # No restrictions
Sensitivity.INTERNAL      # Company-wide access
Sensitivity.CONFIDENTIAL  # Restricted access
Sensitivity.SECRET        # Highly restricted
```

---

## Services

### Control Plane

| Service | Port | Purpose | Database |
|---------|------|---------|----------|
| Identity | 8100 | Multi-tenant management | PostgreSQL |
| Keys | 8101 | API key lifecycle | PostgreSQL |
| Policies | 8102 | DLP/RBAC/ABAC enforcement | MongoDB |

### Data Plane

| Service | Port | Purpose | Database |
|---------|------|---------|----------|
| Router | 8200 | Nutrient broadcast and collection | PostgreSQL + MongoDB |
| Hyphal Memory | 8201 | Vector storage and semantic search | PostgreSQL (pgvector) |
| Reinforcement | 8202 | Edge weight plasticity | PostgreSQL + MongoDB |
| Gossip | 8203 | Regional state synchronization | MongoDB |

### API Endpoints

**Identity Service:**
```
POST   /v1/tenants              Create tenant
GET    /v1/tenants/{id}         Get tenant
PUT    /v1/tenants/{id}         Update tenant
GET    /v1/tenants              List tenants
DELETE /v1/tenants/{id}         Delete tenant
```

**Keys Service:**
```
POST   /v1/keys                 Create API key
POST   /v1/keys:validate        Validate API key
GET    /v1/keys/{tenant_id}     List keys for tenant
POST   /v1/keys:rotate          Rotate key
DELETE /v1/keys/{key_id}        Revoke key
POST   /v1/bootstrap            Admin bootstrap (one-time)
```

**Router Service:**
```
POST   /v1/broadcast            Broadcast nutrient
POST   /v1/collect              Collect contexts
POST   /v1/agents:register      Register/update agent
```

**Hyphal Memory Service:**
```
POST   /v1/memory:store         Store memory with embedding
POST   /v1/memory:search        Vector similarity search
```

**Reinforcement Service:**
```
POST   /v1/outcomes             Record task outcome
```

---

## Development

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- Make (optional)

### Local Setup

```bash
# Clone repository
git clone https://github.com/aicubetechnology/qilbee-mycelial-network.git
cd qilbee-mycelial-network

# Start all services
make up

# View logs
make logs

# Check health
make health

# Run tests
make test

# Stop services
make down
```

### Project Structure

```
qilbee-mycelial-network/
├── sdk/                          # Python SDK (PyPI package)
│   ├── qilbee_mycelial_network/
│   │   ├── client.py             # Main client
│   │   ├── models.py             # Data models
│   │   ├── settings.py           # Configuration
│   │   ├── retry.py              # Resilience
│   │   └── auth.py               # Authentication
│   ├── setup.py
│   └── pyproject.toml
├── services/
│   ├── shared/                   # Shared utilities
│   │   ├── routing.py            # Routing algorithm
│   │   ├── database.py           # DB managers
│   │   ├── auth.py               # Authentication
│   │   └── models.py             # Service models
│   ├── control_plane/
│   │   ├── identity/             # Tenant management
│   │   ├── keys/                 # API keys
│   │   └── policies/             # Policy engine
│   └── data_plane/
│       ├── router/               # Nutrient routing
│       ├── hyphal_memory/        # Vector search
│       ├── reinforcement/        # RL engine
│       └── gossip/               # State sync
├── infra/                        # Infrastructure configs
│   ├── postgres/init.sql         # PostgreSQL schema
│   ├── mongo/init.js             # MongoDB setup
│   └── prometheus/               # Monitoring config
├── tests/                        # Test suites
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── docs/                         # Documentation
├── deploy/                       # Kubernetes/Helm charts
├── examples/                     # Usage examples
├── docker-compose.yml            # Local development
└── Makefile                      # Development commands
```

### Database Schemas

**PostgreSQL** (with pgvector extension):
- `tenants` - Multi-tenant organizations
- `api_keys` - Authentication with SHA-256 hashing
- `hyphae_edges` - Network topology with learned weights
- `hyphal_memory` - 1536-dim vector embeddings
- `audit_events` - Ed25519 signed audit trail
- `quota_configs` - Per-tenant rate limits
- `retention_policies` - Data retention settings

**MongoDB**:
- `agents` - Agent profiles with capabilities
- `policies` - DLP/RBAC/ABAC rules
- `events` - Time-series event logging
- `tasks` - Task tracking
- `regional_state` - Regional health data

---

## Deployment

### Docker Compose (Development)

```bash
make up
```

### Kubernetes (Production)

```bash
# Add Helm repository
helm repo add qmn https://charts.qilbee.io
helm repo update

# Install
helm install qmn qmn/qmn \
  --namespace qmn \
  --create-namespace \
  --values production-values.yaml

# Verify
kubectl -n qmn get pods
```

### Environment Variables

**Required:**
```bash
QMN_API_KEY=qmn_your_key           # SDK authentication
POSTGRES_URL=postgresql://...      # PostgreSQL connection
MONGO_URL=mongodb://...            # MongoDB connection
```

**Optional:**
```bash
QMN_API_BASE_URL=https://api.qilbee.io
QMN_PREFERRED_REGION=us-east-1     # us-east-1, us-west-2, eu-central-1
QMN_TRANSPORT=grpc                 # grpc, quic, http
QMN_TIMEOUT_SEC=30
QMN_MAX_RETRIES=3
QMN_DEBUG=false
LOG_LEVEL=INFO
```

---

## Security

### Authentication & Authorization

| Feature | Implementation |
|---------|----------------|
| API Keys | SHA-256 hashed, stored in PostgreSQL |
| Admin Tenant | System admin with full privileges |
| Scopes | Flexible scope-based access (JSONB) |
| Expiration | Optional key expiration dates |
| Rate Limiting | Per-key limits (default 1000/min) |

### Data Protection

| Feature | Implementation |
|---------|----------------|
| Transit Encryption | TLS 1.3 |
| Rest Encryption | AES-256-GCM (BYOK supported) |
| DLP | Sensitivity labels with capability matching |
| Audit Trail | Ed25519 signed events |

### Multi-Tenancy

| Feature | Implementation |
|---------|----------------|
| Isolation | Row-level security (PostgreSQL) |
| Separation | Separate API keys per tenant |
| Policies | Per-tenant DLP/RBAC/ABAC rules |
| Quotas | Per-tenant rate limits and storage |

### Compliance

- SOC 2 Type II ready architecture
- ISO 27001 compatible controls
- GDPR-ready with data retention policies
- Comprehensive audit logging

---

## Performance

### Target SLOs

| Metric | Target | Achieved |
|--------|--------|----------|
| p95 single-hop routing | < 120ms | 20-40ms |
| p95 collect() end-to-end | < 350ms | < 100ms |
| Throughput | 10K nutrients/min | Validated |
| Regional availability | >= 99.99% | Designed |
| Vector search latency | < 50ms | 8-40x better |

### Test Results

```
Total Tests: 57
Passed: 57 (100%)
Coverage: 68%

E2E Test Results:
- 5-agent collaboration: 100% knowledge reuse
- 50-worker enterprise: Sub-50ms latencies
- Drug research (20 agents): Full collaboration verified
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/API.md) | SDK API documentation |
| [REST API Reference](docs/QMN_API_REFERENCE.md) | HTTP API documentation |
| [Deployment Guide](docs/DEPLOYMENT.md) | Production deployment |
| [Admin Bootstrap](docs/admin-bootstrap.md) | Initial setup guide |
| [Integration Guide](docs/COMMAND_CENTER_INTEGRATION_GUIDE.md) | Frontend integration |
| [Research Paper](docs/RESEARCH_PAPER.md) | Academic paper on architecture |

---

## Support

| Resource | Link |
|----------|------|
| Homepage | https://www.qilbee.io |
| Documentation | https://docs.qilbee.io |
| PyPI Package | https://pypi.org/project/qilbee-mycelial-network/ |
| GitHub | https://github.com/aicubetechnology/qilbee-mycelial-network |
| Issues | https://github.com/aicubetechnology/qilbee-mycelial-network/issues |
| Email | contact@aicube.ca |

---

## License

Business Source License 1.1 with Enhanced IP Protection - see [LICENSE](LICENSE) for details.

**Permitted Uses:**
- Internal business operations
- Development and testing
- Non-commercial/educational use
- Embedded applications (with restrictions)

**Restricted Uses (require commercial license):**
- Agent-Network-as-a-Service offerings
- Commercial distribution
- Competitive products

For commercial licensing: licensing@aicube.ca

Copyright (c) 2025 AICUBE TECHNOLOGY LLC

---

**Built by AICUBE TECHNOLOGY LLC**

*Inspired by the intelligence of fungal mycelial networks.*
