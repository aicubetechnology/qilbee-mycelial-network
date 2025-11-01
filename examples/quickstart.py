"""
Qilbee Mycelial Network - Quick Start Example

Demonstrates basic SDK usage:
1. Broadcasting nutrients
2. Collecting contexts
3. Recording outcomes
"""

import asyncio
import os
import numpy as np
from qilbee_mycelial_network import (
    MycelialClient,
    Nutrient,
    Outcome,
    Sensitivity,
    QMNSettings,
)


async def main():
    """
    Main example demonstrating QMN SDK usage.
    """
    print("=" * 60)
    print("Qilbee Mycelial Network - Quick Start Example")
    print("=" * 60)
    print()

    # Method 1: Create client from environment (recommended)
    # Requires: export QMN_API_KEY=your_key_here
    # For development, using direct settings

    settings = QMNSettings(
        api_key=os.getenv("QMN_API_KEY", "qmn_dev_key_12345678901234567890"),
        api_base_url=os.getenv("QMN_API_BASE_URL", "http://localhost:8200"),
        debug=True,
    )

    async with MycelialClient.create(settings) as client:

        print("Step 1: Broadcasting Nutrient")
        print("-" * 60)

        # Generate a sample embedding (in production, use actual embeddings)
        sample_embedding = np.random.rand(1536).tolist()

        # Broadcast nutrient to network
        nutrient = Nutrient.seed(
            summary="Need help optimizing PostgreSQL query performance",
            embedding=sample_embedding,
            snippets=[
                "SELECT * FROM orders WHERE customer_id = ?",
                "EXPLAIN ANALYZE shows seq scan on 10M rows"
            ],
            tool_hints=["db.analyze", "sql.explain", "index.suggest"],
            sensitivity=Sensitivity.INTERNAL,
            ttl_sec=300,  # 5 minutes
            max_hops=3,
        )

        print(f"  Nutrient ID: {nutrient.id}")
        print(f"  Summary: {nutrient.summary}")
        print(f"  Tool hints: {', '.join(nutrient.tool_hints)}")
        print(f"  Sensitivity: {nutrient.sensitivity.value}")
        print()

        try:
            broadcast_result = await client.broadcast(nutrient)
            print(f"  ✓ Broadcast successful!")
            print(f"  Trace ID: {broadcast_result.get('trace_id', 'N/A')}")
        except Exception as e:
            print(f"  ✗ Broadcast failed: {e}")
            print("  Note: Make sure services are running (make up)")
            return

        print()

        print("Step 2: Collecting Contexts")
        print("-" * 60)

        # Wait a moment for propagation
        await asyncio.sleep(1)

        # Generate demand embedding (what we're looking for)
        demand_embedding = np.random.rand(1536).tolist()

        try:
            contexts = await client.collect(
                demand_embedding=demand_embedding,
                window_ms=500,  # Wait 500ms for responses
                top_k=5,
                diversify=True,
            )

            print(f"  ✓ Collected {len(contexts.contents)} contexts")
            print(f"  Trace ID: {contexts.trace_id}")
            print(f"  Source agents: {len(set(contexts.source_agents))}")

            for i, content in enumerate(contexts.contents[:3], 1):
                print(f"\n  Context {i}:")
                print(f"    Agent: {content.get('agent_id', 'Unknown')}")
                print(f"    Type: {content.get('kind', 'Unknown')}")
                print(f"    Similarity: {content.get('similarity', 0):.3f}")

        except Exception as e:
            print(f"  ✗ Collection failed: {e}")
            contexts = None

        print()

        print("Step 3: Recording Outcome")
        print("-" * 60)

        if contexts:
            # Simulate using the contexts to complete task
            # In real usage, you'd actually use the collected knowledge
            task_success_score = 0.85  # 85% successful

            try:
                outcome_result = await client.record_outcome(
                    trace_id=contexts.trace_id,
                    outcome=Outcome.with_score(
                        task_success_score,
                        task_type="database_optimization",
                        execution_time_ms=1234,
                    )
                )

                print(f"  ✓ Outcome recorded successfully!")
                print(f"  Success score: {task_success_score:.2f}")
                print(f"  This updates edge weights for reinforcement learning")

            except Exception as e:
                print(f"  ✗ Outcome recording failed: {e}")
        else:
            print("  Skipped (no contexts to associate with)")

        print()

        print("Step 4: Hyphal Memory Search")
        print("-" * 60)

        # Search hyphal memory for relevant past knowledge
        query_embedding = np.random.rand(1536).tolist()

        try:
            search_results = await client.hyphal_search(
                embedding=query_embedding,
                top_k=10,
                filters={"kind": "insight"}
            )

            print(f"  ✓ Found {len(search_results)} memories")

            for i, result in enumerate(search_results[:3], 1):
                print(f"\n  Memory {i}:")
                print(f"    ID: {result.id}")
                print(f"    Agent: {result.agent_id}")
                print(f"    Kind: {result.kind}")
                print(f"    Similarity: {result.similarity:.3f}")
                print(f"    Quality: {result.quality:.3f}")

        except Exception as e:
            print(f"  ✗ Search failed: {e}")

        print()

        print("Step 5: Check Usage")
        print("-" * 60)

        try:
            usage = await client.get_usage()
            print(f"  ✓ Usage retrieved")
            print(f"  Details: {usage}")
        except Exception as e:
            print(f"  Note: Usage endpoint may not be implemented yet")

    print()
    print("=" * 60)
    print("Example completed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  - View service logs: make logs")
    print("  - Check Grafana dashboards: http://localhost:3000")
    print("  - Explore API docs: http://localhost:8200/docs")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
