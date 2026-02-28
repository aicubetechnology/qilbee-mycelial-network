# Qilbee Mycelial Network Documentation

**Version**: 0.2.0
**Last Updated**: February 2026

---

## Documentation Overview

This documentation provides comprehensive guides for developers, operators, and architects working with the Qilbee Mycelial Network (QMN) platform.

---

## Quick Navigation

| Getting Started | For Developers | For Operators |
|----------------|----------------|---------------|
| [Quick Start](../README.md#quick-start) | [SDK API Reference](API.md) | [Deployment Guide](DEPLOYMENT.md) |
| [Installation](../README.md#installation) | [REST API Reference](QMN_API_REFERENCE.md) | [Admin Bootstrap](admin-bootstrap.md) |
| [Architecture](../README.md#architecture) | [Integration Guide](COMMAND_CENTER_INTEGRATION_GUIDE.md) | [Security](../README.md#security) |

---

## Documentation Index

### 1. Getting Started

| Document | Description | Audience |
|----------|-------------|----------|
| [README](../README.md) | Project overview, quick start, architecture | All |
| [Admin Bootstrap](admin-bootstrap.md) | Initial setup and API key generation | Operators |

### 2. API Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| [SDK API Reference](API.md) | Python SDK classes, methods, and examples | Developers |
| [REST API Reference](QMN_API_REFERENCE.md) | HTTP endpoints, request/response formats | Developers |

### 3. Integration Guides

| Document | Description | Audience |
|----------|-------------|----------|
| [Command Center Integration](COMMAND_CENTER_INTEGRATION_GUIDE.md) | React/TypeScript frontend integration | Frontend Developers |
| [Integration Guides Index](INTEGRATION_GUIDES_INDEX.md) | Overview of all integration options | Architects |

### 4. Operations & Deployment

| Document | Description | Audience |
|----------|-------------|----------|
| [Deployment Guide](DEPLOYMENT.md) | Docker, Kubernetes, and production deployment | DevOps |
| [Final Summary](FINAL_SUMMARY.md) | Implementation status and production readiness | Project Managers |

### 5. Research & Analysis

| Document | Description | Audience |
|----------|-------------|----------|
| [Research Paper](RESEARCH_PAPER.md) | Academic paper on bio-inspired architecture | Researchers |
| [Enterprise 50 Workers Analysis](ENTERPRISE_50_WORKERS_KNOW_HOW_SHARING.md) | Enterprise-scale test results | Architects |
| [Drug Research Analysis](DRUG_RESEARCH_KNOW_HOW_SHARING.md) | Pharmaceutical research collaboration | Domain Experts |

### 6. Test Results

| Document | Description | Audience |
|----------|-------------|----------|
| [Deployment Test Results](DEPLOYMENT_TEST_RESULTS.md) | Production deployment validation | QA Engineers |
| [Final Test Report](FINAL_TEST_REPORT.md) | Comprehensive test summary | QA Engineers |

---

## Document Descriptions

### API.md - SDK API Reference

Complete Python SDK documentation including:
- `MycelialClient` class and all methods
- `Nutrient`, `Outcome`, `Context` data models
- `QMNSettings` configuration options
- Error handling and exception types
- Rate limits and pagination
- Code examples for all operations

### QMN_API_REFERENCE.md - REST API Reference

HTTP API documentation covering:
- Authentication and tenant-based access
- Identity Service endpoints (tenant CRUD)
- Router Service endpoints (broadcast, collect)
- Hyphal Memory Service endpoints (store, search)
- Policies Service endpoints (policy management)
- Error codes and rate limiting
- TypeScript and Python client examples

### DEPLOYMENT.md - Deployment Guide

Production deployment instructions:
- Docker Compose for development
- Kubernetes/Helm for production
- Environment variable configuration
- Secrets management
- Monitoring setup (Prometheus/Grafana)
- Scaling strategies
- Backup and recovery procedures

### admin-bootstrap.md - Admin Bootstrap Guide

Initial system setup:
- Security design principles
- Fresh startup process
- Admin API key generation
- Admin-only endpoints
- Troubleshooting guide
- Best practices

### COMMAND_CENTER_INTEGRATION_GUIDE.md - Integration Guide

Frontend integration tutorial:
- Architecture integration patterns
- Service module creation
- API client implementation
- React hooks for QMN
- UI component examples
- Testing strategies

### RESEARCH_PAPER.md - Academic Research Paper

15,000+ word academic paper:
- Bio-inspired architecture design
- Multi-agent system coordination
- Empirical validation studies
- Performance analysis
- Comparative analysis
- Future research directions

---

## Architecture Diagrams

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client SDK                              │
│              pip install qilbee-mycelial-network            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Control Plane                            │
│   Identity (8100)  │  Keys (8101)  │  Policies (8102)       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Plane                              │
│  Router (8200) │ Hyphal Memory (8201) │ Reinforcement (8202)│
│                │                      │ Gossip (8203)       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Storage                             │
│    PostgreSQL + pgvector  │  MongoDB  │  Redis              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Agent A                           Agent B
   │                                 │
   │ 1. broadcast(nutrient)          │
   ├──────────────────────────────▶  │
   │                                 │
   │     Router Service              │
   │     - Score agents              │
   │     - Apply policies            │
   │     - Route nutrient            │
   │                                 │
   │                                 │ 2. collect(embedding)
   │  ◀──────────────────────────────┤
   │                                 │
   │ 3. record_outcome(trace_id)     │
   ├──────────────────────────────▶  │
   │                                 │
   │     Reinforcement Service       │
   │     - Update edge weights       │
   │     - Improve future routing    │
   │                                 │
```

---

## Service Reference

| Service | Port | Database | Key Responsibilities |
|---------|------|----------|---------------------|
| Identity | 8100 | PostgreSQL | Tenant management, plan tiers, quotas |
| Keys | 8101 | PostgreSQL | API key lifecycle, validation, rotation |
| Policies | 8102 | MongoDB | DLP, RBAC, ABAC policy enforcement |
| Router | 8200 | PostgreSQL + MongoDB | Nutrient broadcast, context collection |
| Hyphal Memory | 8201 | PostgreSQL (pgvector) | Vector storage, semantic search |
| Reinforcement | 8202 | PostgreSQL + MongoDB | Edge weight plasticity, outcome recording |
| Gossip | 8203 | MongoDB | Regional state synchronization |

---

## SDK Quick Reference

```python
from qilbee_mycelial_network import (
    MycelialClient,
    Nutrient,
    Outcome,
    Sensitivity,
    QMNSettings
)

# Initialize
async with MycelialClient.create_from_env() as client:

    # EPHEMERAL: Broadcast knowledge to network (TTL-based)
    await client.broadcast(Nutrient.seed(
        summary="...",
        embedding=[...],  # 1536-dim
        sensitivity=Sensitivity.INTERNAL,
        ttl_sec=300  # Expires in 5 minutes
    ))

    # Collect contexts from network
    contexts = await client.collect(
        demand_embedding=[...],
        top_k=5
    )

    # Record outcome for reinforcement learning
    await client.record_outcome(
        trace_id=contexts.trace_id,
        outcome=Outcome.with_score(0.9)
    )

    # Record per-hop outcomes for granular feedback (v0.2.0)
    await client.record_outcome(
        trace_id=contexts.trace_id,
        outcome=Outcome.with_hop_scores(
            score=0.85,
            hop_outcomes={"agent-1": 0.9, "agent-2": 0.6}
        )
    )

    # PERSISTENT: Store knowledge in vector database
    await client.hyphal_store(
        agent_id="agent-001",
        kind="insight",
        content={"finding": "Important discovery"},
        embedding=[...],
        quality=0.9
    )

    # Search stored memories
    results = await client.hyphal_search(
        embedding=[...],
        top_k=10,
        filters={"kind": "insight"}
    )

    # Control plane: Tenant management (v0.2.0, admin only)
    await client.create_tenant(tenant_id="new-org", name="New Org", plan_tier="pro")
    tenants = await client.list_tenants(status_filter="active")
    usage = await client.get_usage()

    # Control plane: API key management (v0.2.0)
    key = await client.create_key(name="prod-key", scopes=["*"])
    await client.revoke_key(key_id="key-uuid")

    # Control plane: Policy management (v0.2.0)
    await client.evaluate_policy(policy_type="rbac", context={"role": "admin"})
```

### Broadcast vs Store

| Operation | Method | Storage | Use Case |
|-----------|--------|---------|----------|
| Broadcast | `broadcast()` | Ephemeral (TTL) | Real-time agent-to-agent sharing |
| Store | `hyphal_store()` | Permanent | Long-term knowledge retention |

---

## What's New in v0.2.0

### Routing Intelligence
- **Epsilon-greedy exploration**: Prevents local optima with configurable exploration rate
- **Semantic demand overlap**: Fuzzy string matching replaces exact set intersection
- **Proportional capability boost**: Scaled by match count (0.05 per match, max 4)
- **Time-based edge decay**: Background task decays stale edges exponentially
- **TTL enforcement**: Expired nutrients rejected before routing (409)
- **Per-hop outcome support**: Granular per-agent feedback for RL

### Production Hardening
- **Real AES-256-GCM encryption**: PBKDF2 key derivation, proper nonce/salt
- **Real Ed25519 audit signing**: Deterministic signatures with key export
- **Redis rate limiting**: Sliding window with per-tenant limits
- **SQL injection hardening**: Explicit allowed-fields mapping

### Performance at Scale
- **Batch edge loading**: Single SQL query replaces N+1 pattern
- **Dynamic neighbor limit**: Scales with network size (20-50)
- **MMR similarity cache**: Pre-computed pairwise matrix
- **Composite database index**: `(tenant_id, src, w DESC)` on hyphae_edges

### Observability
- **Prometheus metrics**: Custom counters, histograms, and gauges
- **Structured logging**: JSON output with structlog, tenant/trace context
- **Alerting rules**: Error rate, latency, service down, business metrics

### SDK Completeness
- **Control plane methods**: Full tenant, key, and policy management
- **get_usage()**: Real implementation (was NotImplementedError)
- **Per-hop outcomes**: `Outcome.with_hop_scores()` for granular RL
- **User filters**: `SearchRequest.user_filter` support

### Test Coverage
- **312 tests passing** (up from 57)
- **98% code coverage** (up from 68%)
- 8 new test files covering all major modules

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `QMN_API_KEY` | Yes | - | API key for authentication |
| `QMN_API_BASE_URL` | No | https://api.qilbee.io | API endpoint |
| `QMN_PREFERRED_REGION` | No | - | Preferred region |
| `QMN_TRANSPORT` | No | http | Transport (http/grpc/quic) |
| `QMN_TIMEOUT_SEC` | No | 30 | Request timeout |
| `QMN_MAX_RETRIES` | No | 3 | Max retry attempts |
| `QMN_DEBUG` | No | false | Enable debug logging |

---

## Support Resources

| Resource | URL |
|----------|-----|
| Homepage | https://www.qilbee.io |
| Documentation | https://docs.qilbee.io |
| PyPI Package | https://pypi.org/project/qilbee-mycelial-network/ |
| GitHub | https://github.com/aicubetechnology/qilbee-mycelial-network |
| Issues | https://github.com/aicubetechnology/qilbee-mycelial-network/issues |
| Email | contact@aicube.ca |

---

**Copyright (c) 2025-2026 AICUBE TECHNOLOGY LLC**
