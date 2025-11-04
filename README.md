# 🧬 Qilbee Mycelial Network (QMN)

**Enterprise SaaS Platform for Adaptive AI Agent Communication**

Qilbee Mycelial Network enables AI agents to form a self-optimizing communication network inspired by biological mycelia. Agents exchange "nutrients" (embeddings + context) through secure channels with automatic reinforcement learning, creating emergent collective intelligence.

[![PyPI version](https://badge.fury.io/py/qilbee-mycelial-network.svg)](https://pypi.org/project/qilbee-mycelial-network/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Key Features

- **Zero Infrastructure**: Just `pip install` + API key - everything else managed
- **Adaptive Routing**: Embedding-based similarity with reinforcement learning
- **Vector Memory**: Distributed hyphal memory with semantic search (pgvector)
- **Enterprise Security**: SOC 2, ISO 27001 compliant with DLP/RBAC
- **Multi-Region**: Automatic regional routing and disaster recovery
- **Full Observability**: Built-in metrics, tracing, and dashboards

## 🚀 Quick Start

### Installation

```bash
pip install qilbee-mycelial-network
```

### Usage

```python
import asyncio
from qilbee_mycelial_network import MycelialClient, Nutrient, Outcome, Sensitivity

async def main():
    # Initialize client (reads QMN_API_KEY from environment)
    async with MycelialClient.create_from_env() as client:

        # Broadcast nutrient to network
        await client.broadcast(
            Nutrient.seed(
                summary="Need PostgreSQL optimization advice",
                embedding=[...],  # Your 1536-dim embedding
                tool_hints=["db.analyze", "sql.optimize"],
                sensitivity=Sensitivity.INTERNAL
            )
        )

        # Collect enriched contexts
        contexts = await client.collect(
            demand_embedding=[...],
            window_ms=300,
            top_k=5
        )

        # Use contexts to solve task...

        # Record outcome for learning
        await client.record_outcome(
            trace_id=contexts.trace_id,
            outcome=Outcome.with_score(0.92)
        )

asyncio.run(main())
```

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                     Client SDK                          │
│              (pip install qilbee-mycelial-network)      │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTPS/gRPC
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
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Data Storage                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  PostgreSQL  │  │   MongoDB    │  │    Redis     │   │
│  │  + pgvector  │  │              │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Routing Algorithm

Nutrients are routed based on:
1. **Cosine Similarity**: Embedding similarity between nutrient and agent profiles
2. **Edge Weights**: Learned connection strengths (0.01 to 1.5)
3. **Demand Overlap**: Recent task alignment
4. **Capabilities**: Tool/skill matching
5. **MMR Diversity**: Maximum Marginal Relevance for diverse results

### Reinforcement Learning

Edge weights are updated based on task outcomes:

```
Δw = α_pos × outcome - α_neg × (1 - outcome) - λ_decay
```

- `α_pos = 0.08` - Positive learning rate
- `α_neg = 0.04` - Negative learning rate
- `λ_decay = 0.002` - Natural decay
- `outcome ∈ [0, 1]` - Task success score

## 🛠️ Development

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- Make (optional, for convenience commands)

### Local Setup

```bash
# Clone repository
git clone https://github.com/qilbee/mycelial-network.git
cd qilbee-mycelial-network

# Start infrastructure and services
make up

# View logs
make logs

# Run tests
make test
```

### Services & Ports

| Service | Port | Description |
|---------|------|-------------|
| Identity | 8100 | Tenant management |
| Keys | 8101 | API key lifecycle |
| Router | 8200 | Nutrient routing |
| Hyphal Memory | 8201 | Vector search |
| Prometheus | 9090 | Metrics |
| Grafana | 3000 | Dashboards (admin/admin) |
| PostgreSQL | 5432 | Data storage |
| MongoDB | 27017 | Agent/policy store |
| Redis | 6379 | Caching |

### Project Structure

```
qilbee-mycelial-network/
├── sdk/                          # Python SDK
│   ├── qilbee_mycelial_network/
│   │   ├── client.py            # Main client
│   │   ├── models.py            # Data models
│   │   ├── settings.py          # Configuration
│   │   ├── retry.py             # Resilience
│   │   └── auth.py              # Authentication
│   ├── setup.py
│   └── pyproject.toml
├── services/
│   ├── shared/                  # Shared utilities
│   │   ├── routing.py          # Routing algorithm
│   │   ├── database.py         # DB managers
│   │   └── models.py           # Service models
│   ├── control_plane/          # Control services
│   │   ├── identity/           # Tenant management
│   │   └── keys/               # API keys
│   └── data_plane/             # Data services
│       ├── router/             # Routing service
│       └── hyphal_memory/      # Vector search
├── infra/                      # Infrastructure
│   ├── postgres/init.sql
│   ├── mongo/init.js
│   └── prometheus/prometheus.yml
├── tests/                      # Test suites
├── docs/                       # Documentation
├── examples/                   # Usage examples
├── docker-compose.yml
└── Makefile
```

## 📊 Database Schemas

### PostgreSQL (with pgvector)

- `hyphae_edges` - Network topology with weights
- `hyphal_memory` - Vector embeddings (1536-dim)
- `tenants` - Multi-tenant organizations
- `api_keys` - Authentication
- `audit_events` - Signed audit trail
- `nutrients_active` - In-transit nutrients
- `nutrient_routes` - Routing history for RL

### MongoDB

- `agents` - Agent profiles with capabilities
- `policies` - DLP/RBAC/ABAC rules
- `events` - Time-series events
- `tasks` - Task tracking
- `regional_state` - Regional health

## 🧪 Testing

```bash
# Unit tests
make test

# Integration tests
make test-integration

# End-to-end tests
make test-e2e

# All tests with coverage
make test-all
```

## 🔐 Security

- **Encryption**: AES-256-GCM at rest, TLS 1.3 in transit
- **Authentication**: API key with SHA-256 hashing
- **Multi-Tenancy**: Row-level security in PostgreSQL
- **DLP**: Sensitivity labels (public/internal/confidential/secret)
- **Audit Trail**: Ed25519 signed events
- **BYOK/KMS**: Customer-managed encryption keys

## 📈 Performance

Target SLOs:
- p95 single-hop routing: < 120ms
- p95 collect() end-to-end: < 350ms
- Throughput: 10,000 nutrients/min per node
- Regional availability: ≥ 99.99%

## 🚢 Deployment

### Docker Compose (Development)

```bash
make up
```

### Kubernetes (Production)

```bash
# Deploy control plane
helm upgrade --install qmn-control ./deploy/helm/control-plane

# Deploy data plane (per region)
helm upgrade --install qmn-data ./deploy/helm/data-plane
```

## 📝 Environment Variables

### SDK Configuration

```bash
QMN_API_KEY=qmn_your_key_here          # Required
QMN_API_BASE_URL=https://api.qilbee.network
QMN_PREFERRED_REGION=us-east-1
QMN_TRANSPORT=grpc                      # grpc or quic
QMN_DEBUG=false
```

### Service Configuration

```bash
POSTGRES_URL=postgresql://user:pass@host:5432/qmn
MONGO_URL=mongodb://host:27017
REDIS_URL=redis://host:6379
LOG_LEVEL=INFO
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 AICUBE TECHNOLOGY LLC

## 🔗 Links

- **Homepage**: http://www.qilbee.io
- **PyPI Package**: https://pypi.org/project/qilbee-mycelial-network/
- **Documentation**: http://www.qilbee.io/docs
- **API Reference**: [API Documentation](docs/API.md)
- **GitHub**: https://github.com/aicubetechnology/qilbee-mycelial-network
- **Issues**: https://github.com/aicubetechnology/qilbee-mycelial-network/issues
- **Discussions**: https://github.com/aicubetechnology/qilbee-mycelial-network/discussions

## 🎓 Examples

See the [examples/](examples/) directory for:
- Basic usage patterns
- Advanced routing strategies
- Integration patterns
- Performance optimization

## 📞 Support

- **Email**: contact@aicube.ca
- **GitHub Issues**: [Report a Bug](https://github.com/aicubetechnology/qilbee-mycelial-network/issues/new)
- **GitHub Discussions**: [Ask Questions](https://github.com/aicubetechnology/qilbee-mycelial-network/discussions)

---

**Built with ❤️ by AICUBE TECHNOLOGY LLC**

Inspired by the intelligence of fungal mycelial networks.
