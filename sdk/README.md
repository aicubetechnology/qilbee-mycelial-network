# Qilbee Mycelial Network (QMN) - Python SDK

Enterprise SaaS SDK for building adaptive AI agent communication networks inspired by biological mycelia.

## 🚀 Quick Start

### Installation

```bash
pip install qilbee-mycelial-network
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

## 📋 Features

- **Zero Infrastructure**: Just `pip install` + API key, everything else is managed
- **Adaptive Routing**: Automatic learning and optimization based on outcomes
- **Enterprise Security**: SOC 2, ISO 27001 compliant with DLP/RBAC
- **Multi-Region**: Automatic regional routing and disaster recovery
- **Vector Memory**: Distributed hyphal memory with semantic search
- **Full Observability**: Built-in telemetry and tracing

## 🔧 Configuration

Set your API key:

```bash
export QMN_API_KEY=qmn_your_api_key_here
```

Optional environment variables:

```bash
export QMN_API_BASE_URL=https://api.qilbee.network  # Custom API endpoint
export QMN_PREFERRED_REGION=us-east-1               # Preferred region
export QMN_TRANSPORT=grpc                           # grpc or quic
export QMN_DEBUG=true                               # Enable debug mode
```

## 📚 Documentation

- [Full Documentation](https://docs.qilbee.network)
- [API Reference](https://docs.qilbee.network/api)
- [Examples](https://github.com/qilbee/mycelial-network/tree/main/examples)

## 🔐 Security

All data is encrypted in transit (TLS 1.3) and at rest (AES-256-GCM). See our [Security Policy](https://docs.qilbee.network/security) for details.

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Support

- [GitHub Issues](https://github.com/qilbee/mycelial-network/issues)
- [Documentation](https://docs.qilbee.network)
- [Email Support](mailto:support@qilbee.network)
