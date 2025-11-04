# Qilbee Mycelial Network (QMN) - Python SDK

[![PyPI version](https://badge.fury.io/py/qilbee-mycelial-network.svg)](https://pypi.org/project/qilbee-mycelial-network/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Enterprise SaaS SDK for building adaptive AI agent communication networks inspired by biological mycelia. Enable your AI agents to form a self-optimizing communication network with automatic reinforcement learning and emergent collective intelligence.

## 🌟 Why Qilbee Mycelial Network?

Traditional AI agent systems struggle with:
- **Static routing** - Hard-coded communication patterns that don't adapt
- **Context isolation** - Agents can't share learned knowledge effectively
- **Scalability** - Infrastructure complexity grows with agent count
- **No learning** - Systems don't improve from past interactions

**Qilbee solves these problems** by creating a living network where:
- 🧠 Agents share context through semantic embeddings
- 📈 Routes strengthen based on successful outcomes
- 🔄 Network topology evolves automatically
- ☁️ Zero infrastructure management required

## 🚀 Quick Start

### Installation

```bash
pip install qilbee-mycelial-network
```

For additional transport protocols:
```bash
# gRPC support (high performance)
pip install qilbee-mycelial-network[grpc]

# QUIC support (low latency)
pip install qilbee-mycelial-network[quic]

# OpenTelemetry integration
pip install qilbee-mycelial-network[telemetry]

# Everything
pip install qilbee-mycelial-network[all]
```

### Basic Usage

```python
import asyncio
from qilbee_mycelial_network import MycelialClient, Nutrient, Outcome, Sensitivity

async def main():
    # Initialize client (reads QMN_API_KEY from environment)
    async with MycelialClient.create_from_env() as client:

        # Broadcast nutrient to network
        await client.broadcast(
            Nutrient.seed(
                summary="Need PostgreSQL performance optimization advice",
                embedding=[...],  # Your 1536-dim embedding vector
                snippets=["EXPLAIN ANALYZE output..."],
                tool_hints=["db.analyze", "query.optimize"],
                sensitivity=Sensitivity.INTERNAL,
                ttl_sec=180,
                max_hops=3
            )
        )

        # Collect enriched contexts from network
        contexts = await client.collect(
            demand_embedding=[...],  # Your query embedding
            window_ms=300,
            top_k=5,
            diversify=True  # Apply MMR diversity
        )

        # Use collected context...
        for content in contexts.contents:
            print(f"Agent: {content['agent_id']}")
            print(f"Response: {content['data']}")

        # Record outcome for reinforcement learning
        await client.record_outcome(
            trace_id=contexts.trace_id,
            outcome=Outcome.with_score(0.92)  # 0.0 to 1.0
        )

asyncio.run(main())
```

## 📋 Core Features

### 🔄 Adaptive Routing
Routes are selected based on:
- **Embedding similarity** - Cosine similarity between nutrient and agent profiles
- **Learned weights** - Connection strengths that evolve (0.01 to 1.5)
- **Historical success** - Reinforcement learning from task outcomes
- **Capability matching** - Tool/skill alignment
- **Diversity** - Maximum Marginal Relevance for varied results

### 🧠 Vector Memory
- **Distributed storage** with PostgreSQL + pgvector
- **Semantic search** across all agent contexts
- **1536-dimension embeddings** (OpenAI compatible)
- **Automatic indexing** and optimization

### 🛡️ Enterprise Security
- **Encryption**: TLS 1.3 in transit, AES-256-GCM at rest
- **DLP**: 4-tier sensitivity labels (PUBLIC/INTERNAL/CONFIDENTIAL/SECRET)
- **RBAC**: Role-based access control
- **Audit trail**: Ed25519 signed events
- **Multi-tenancy**: Row-level security isolation
- **Compliance**: SOC 2, ISO 27001 ready

### 🌍 Multi-Region
- **Automatic failover** and disaster recovery
- **Regional routing** based on proximity
- **Global replication** with eventual consistency
- **99.99% availability** SLO

### 📊 Full Observability
- **Prometheus metrics** - Latency, throughput, error rates
- **Distributed tracing** - OpenTelemetry integration
- **Grafana dashboards** - Pre-built visualizations
- **Health checks** - Liveness and readiness probes

## 🔧 Configuration

### Environment Variables

```bash
# Required
export QMN_API_KEY=qmn_your_api_key_here

# Optional
export QMN_API_BASE_URL=https://api.qilbee.io      # API endpoint
export QMN_PREFERRED_REGION=us-east-1              # Preferred region
export QMN_TRANSPORT=grpc                          # grpc, quic, or http
export QMN_DEBUG=true                              # Enable debug logging
export QMN_TIMEOUT_SEC=30                          # Request timeout
export QMN_MAX_RETRIES=3                           # Retry attempts
```

### Programmatic Configuration

```python
from qilbee_mycelial_network import MycelialClient, QMNSettings

settings = QMNSettings(
    api_key="qmn_your_key",
    api_base_url="https://api.qilbee.io",
    preferred_region="us-west-2",
    transport="grpc",
    timeout_sec=30,
    max_retries=3,
    debug=False
)

async with MycelialClient(settings) as client:
    # Your code here
    pass
```

## 📖 Advanced Examples

### Example 1: Multi-Agent Collaboration

```python
import asyncio
from qilbee_mycelial_network import MycelialClient, Nutrient, Sensitivity

async def collaborative_task():
    async with MycelialClient.create_from_env() as client:
        # Agent 1: Research agent shares findings
        await client.broadcast(
            Nutrient.seed(
                summary="Found vulnerability in auth module",
                embedding=get_embedding("security vulnerability authentication"),
                snippets=["CVE-2024-1234", "Affects version 2.3.1"],
                tool_hints=["security.scan", "code.review"],
                sensitivity=Sensitivity.CONFIDENTIAL
            )
        )

        # Agent 2: Security agent queries for relevant context
        contexts = await client.collect(
            demand_embedding=get_embedding("security issues authentication"),
            top_k=10,
            diversify=True
        )

        # Agent processes contexts and takes action
        for ctx in contexts.contents:
            print(f"Found related issue: {ctx['summary']}")

        # Record successful collaboration
        await client.record_outcome(
            trace_id=contexts.trace_id,
            outcome=Outcome.with_score(0.95)
        )
```

### Example 2: Learning from Outcomes

```python
import asyncio
from qilbee_mycelial_network import MycelialClient, Outcome

async def learning_loop():
    async with MycelialClient.create_from_env() as client:
        # Collect contexts for a task
        contexts = await client.collect(
            demand_embedding=task_embedding,
            top_k=5
        )

        # Execute task with collected contexts
        result = await execute_task(contexts)

        # Record outcome - this strengthens successful routes
        if result.success:
            await client.record_outcome(
                trace_id=contexts.trace_id,
                outcome=Outcome.with_score(result.quality)  # 0.0 to 1.0
            )
        else:
            # Negative outcome weakens these routes
            await client.record_outcome(
                trace_id=contexts.trace_id,
                outcome=Outcome.with_score(0.0)
            )
```

### Example 3: Custom Agent Profiles

```python
from qilbee_mycelial_network import MycelialClient

async def register_agent():
    async with MycelialClient.create_from_env() as client:
        # Register agent with capabilities
        await client.register_agent(
            agent_id="code-reviewer-01",
            profile_embedding=get_embedding("code review security best practices"),
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

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Client SDK                          │
│              (pip install qilbee-mycelial-network)      │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTPS/gRPC/QUIC
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Control Plane                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Identity │  │   Keys   │  │ Policies │               │
│  └──────────┘  └──────────┘  └──────────┘               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Data Plane (Regional)                  │
│  ┌──────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  Router  │  │ Hyphal Memory  │  │ Reinforcement  │   │
│  │          │  │   (pgvector)   │  │    Engine      │   │
│  └──────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Routing Algorithm

Nutrients flow through the network based on:

1. **Semantic Similarity** (40% weight)
   - Cosine similarity between embeddings
   - Agent profile matching

2. **Edge Weights** (30% weight)
   - Learned from historical outcomes
   - Range: 0.01 to 1.5
   - Updated via reinforcement learning

3. **Capability Match** (20% weight)
   - Tool/skill alignment
   - Metadata filtering

4. **Diversity** (10% weight)
   - Maximum Marginal Relevance
   - Prevents echo chambers

### Reinforcement Learning

Edge weights evolve using:

```
Δw = α_pos × outcome - α_neg × (1 - outcome) - λ_decay
```

Where:
- `α_pos = 0.08` - Positive learning rate
- `α_neg = 0.04` - Negative learning rate
- `λ_decay = 0.002` - Natural decay to prevent stagnation
- `outcome ∈ [0, 1]` - Task success score

## 📊 Performance

Target SLOs:
- **p95 single-hop routing**: < 120ms
- **p95 collect() end-to-end**: < 350ms
- **Throughput**: 10,000 nutrients/min per node
- **Regional availability**: ≥ 99.99%

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=qilbee_mycelial_network --cov-report=html

# Integration tests only
pytest tests/integration/

# Performance benchmarks
pytest tests/performance/ -v
```

## 📚 Documentation

- **Homepage**: [qilbee.io](http://www.qilbee.io)
- **Full Documentation**: [qilbee.io/docs](http://www.qilbee.io/docs)
- **API Reference**: [API Docs](http://www.qilbee.io/docs/api)
- **Examples**: [GitHub Examples](https://github.com/aicubetechnology/qilbee-mycelial-network/tree/main/examples)
- **Architecture**: [System Design](https://github.com/aicubetechnology/qilbee-mycelial-network/blob/main/docs/ARCHITECTURE.md)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - Copyright (c) 2025 AICUBE TECHNOLOGY LLC

See [LICENSE](../LICENSE) for details.

## 🔗 Links

- **PyPI**: [pypi.org/project/qilbee-mycelial-network](https://pypi.org/project/qilbee-mycelial-network/)
- **GitHub**: [github.com/aicubetechnology/qilbee-mycelial-network](https://github.com/aicubetechnology/qilbee-mycelial-network)
- **Issues**: [GitHub Issues](https://github.com/aicubetechnology/qilbee-mycelial-network/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aicubetechnology/qilbee-mycelial-network/discussions)

## 💬 Support

- **Email**: contact@aicube.ca
- **GitHub Issues**: [Report a bug](https://github.com/aicubetechnology/qilbee-mycelial-network/issues/new)
- **GitHub Discussions**: [Ask questions](https://github.com/aicubetechnology/qilbee-mycelial-network/discussions)

---

**Built with ❤️ by AICUBE TECHNOLOGY LLC**

Inspired by the intelligence of fungal mycelial networks.
