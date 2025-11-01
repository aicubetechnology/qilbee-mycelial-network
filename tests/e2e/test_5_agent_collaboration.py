"""
5-Agent Collaboration Test - Full System Demonstration

This test demonstrates a complete collaboration scenario with 5 AI agents:
1. Agent Alice (Python Expert) - Coding and optimization
2. Agent Bob (Data Analyst) - Data analysis and insights
3. Agent Charlie (DevOps Engineer) - Infrastructure and deployment
4. Agent Diana (Technical Writer) - Documentation
5. Agent Eve (QA Engineer) - Testing and quality assurance

Scenario: Building a data processing pipeline
- Alice broadcasts need for performance optimization
- Bob provides data insights
- Charlie suggests infrastructure improvements
- Diana creates documentation
- Eve validates and tests the solution
"""

import asyncio
import httpx
import json
import os
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any
import hashlib
import math


# Service URLs
BASE_URL = "http://localhost"
IDENTITY_URL = f"{BASE_URL}:8100"
KEYS_URL = f"{BASE_URL}:8101"
ROUTER_URL = f"{BASE_URL}:8200"
HYPHAL_MEMORY_URL = f"{BASE_URL}:8201"

# API Key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def generate_embedding(text: str, agent_id: str) -> List[float]:
    """Generate deterministic embedding for testing."""
    # Combine text and agent_id for uniqueness
    combined = f"{agent_id}:{text}"
    hash_obj = hashlib.sha256(combined.encode())
    hash_bytes = hash_obj.digest()

    embedding = []
    for i in range(1536):
        byte_idx = i % len(hash_bytes)
        value = hash_bytes[byte_idx] / 255.0
        value = math.sin(value * math.pi * (i / 1536)) * 0.5 + 0.5
        embedding.append(value)

    # Normalize
    magnitude = math.sqrt(sum(x**2 for x in embedding))
    embedding = [x / magnitude for x in embedding]

    return embedding


class Agent:
    """Represents an AI agent in the collaboration."""

    def __init__(self, agent_id: str, name: str, role: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.contributions = []

    def create_contribution(self, task: str, solution: str) -> Dict[str, Any]:
        """Create a contribution from this agent."""
        contribution = {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "role": self.role,
            "task": task,
            "solution": solution,
            "timestamp": datetime.now().isoformat(),
            "embedding": generate_embedding(f"{task} {solution}", self.agent_id)
        }
        self.contributions.append(contribution)
        return contribution


class CollaborationTest:
    """Test harness for 5-agent collaboration."""

    def __init__(self):
        self.tenant_id = f"collab-tenant-{uuid.uuid4().hex[:8]}"
        self.api_key = None
        self.agents = []
        self.results = {
            "setup": False,
            "agents_created": 0,
            "nutrients_broadcast": 0,
            "memories_stored": 0,
            "searches_performed": 0,
            "collaboration_complete": False,
            "performance_metrics": {},
            "errors": []
        }

    async def setup(self):
        """Initialize test environment and agents."""
        print(f"\n{'='*80}")
        print(f"🧬 5-Agent Collaboration Test - Qilbee Mycelial Network")
        print(f"{'='*80}\n")

        # Create 5 agents with different specializations
        self.agents = [
            Agent(
                agent_id="agent-alice-python",
                name="Alice",
                role="Python Expert",
                capabilities=["python", "optimization", "algorithms", "code_review"]
            ),
            Agent(
                agent_id="agent-bob-data",
                name="Bob",
                role="Data Analyst",
                capabilities=["data_analysis", "sql", "pandas", "visualization"]
            ),
            Agent(
                agent_id="agent-charlie-devops",
                name="Charlie",
                role="DevOps Engineer",
                capabilities=["docker", "kubernetes", "ci_cd", "monitoring"]
            ),
            Agent(
                agent_id="agent-diana-writer",
                name="Diana",
                role="Technical Writer",
                capabilities=["documentation", "markdown", "tutorials", "api_docs"]
            ),
            Agent(
                agent_id="agent-eve-qa",
                name="Eve",
                role="QA Engineer",
                capabilities=["testing", "pytest", "selenium", "quality_assurance"]
            )
        ]

        print(f"👥 Team Assembled:")
        for agent in self.agents:
            print(f"   • {agent.name} ({agent.role})")
            print(f"     Capabilities: {', '.join(agent.capabilities)}")
        print()

        # Create tenant
        print("🏢 Setting up Tenant...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "id": self.tenant_id,
                "name": "5-Agent Collaboration Team",
                "plan_tier": "enterprise",
                "metadata": {
                    "test_type": "collaboration",
                    "agent_count": "5",
                    "scenario": "data_pipeline"
                }
            }

            try:
                response = await client.post(f"{IDENTITY_URL}/v1/tenants", json=payload)
                if response.status_code in [200, 201]:
                    print(f"   ✅ Tenant created: {self.tenant_id}")
                    self.results["setup"] = True
                else:
                    print(f"   ❌ Tenant creation failed: {response.status_code}")
                    return False
            except Exception as e:
                print(f"   ❌ Setup error: {e}")
                return False

        # Generate API key
        self.api_key = f"qmn_test_{uuid.uuid4().hex}"
        print(f"   ✅ API Key generated: {self.api_key[:20]}...\n")

        self.results["agents_created"] = len(self.agents)
        return True

    async def run_collaboration_scenario(self):
        """Execute the complete collaboration scenario."""
        print(f"📋 Scenario: Building a High-Performance Data Processing Pipeline\n")

        headers = {
            "X-API-Key": self.api_key,
            "X-Tenant-ID": self.tenant_id
        }

        # Phase 1: Alice identifies optimization need
        print("Phase 1: Problem Identification")
        print("-" * 80)
        alice_task = "Our data processing pipeline is slow with large datasets (>1M rows)"
        alice_solution = """
        Performance issues identified:
        1. Using Python loops instead of vectorized operations
        2. No parallel processing for independent tasks
        3. Loading entire dataset into memory
        4. Inefficient database queries with N+1 problem
        """

        alice_contrib = self.agents[0].create_contribution(alice_task, alice_solution)
        await self.broadcast_nutrient(alice_contrib, headers)
        print(f"✅ {self.agents[0].name}: Identified performance bottlenecks\n")
        await asyncio.sleep(0.5)

        # Phase 2: Bob analyzes data patterns
        print("Phase 2: Data Analysis")
        print("-" * 80)
        bob_task = "Analyze data access patterns and processing requirements"
        bob_solution = """
        Data insights discovered:
        1. 80% of queries access last 30 days of data
        2. Peak processing time: 9-11 AM (3x normal load)
        3. Average record size: 2KB, Total: 2TB dataset
        4. Recommended: Implement data partitioning by date
        5. Use batch processing for aggregations
        """

        bob_contrib = self.agents[1].create_contribution(bob_task, bob_solution)
        await self.broadcast_nutrient(bob_contrib, headers)
        await self.store_memory(bob_contrib, headers)
        print(f"✅ {self.agents[1].name}: Provided data analysis insights\n")
        await asyncio.sleep(0.5)

        # Phase 3: Charlie suggests infrastructure improvements
        print("Phase 3: Infrastructure Design")
        print("-" * 80)
        charlie_task = "Design scalable infrastructure for data pipeline"
        charlie_solution = """
        Infrastructure recommendations:
        1. Deploy on Kubernetes with auto-scaling (3-10 pods)
        2. Use PostgreSQL with TimescaleDB for time-series data
        3. Implement Redis caching for frequent queries
        4. Add Prometheus monitoring + Grafana dashboards
        5. Set up CI/CD pipeline with automated testing
        """

        charlie_contrib = self.agents[2].create_contribution(charlie_task, charlie_solution)
        await self.broadcast_nutrient(charlie_contrib, headers)
        await self.store_memory(charlie_contrib, headers)
        print(f"✅ {self.agents[2].name}: Designed scalable infrastructure\n")
        await asyncio.sleep(0.5)

        # Phase 4: Diana creates documentation
        print("Phase 4: Documentation")
        print("-" * 80)
        diana_task = "Document the optimized data pipeline architecture"
        diana_solution = """
        # Data Pipeline Documentation

        ## Architecture Overview
        - **Ingestion Layer**: Kafka for streaming data
        - **Processing Layer**: Apache Spark for parallel processing
        - **Storage Layer**: TimescaleDB for time-series, S3 for archives
        - **Caching Layer**: Redis for hot data

        ## Performance Improvements
        - 10x faster processing with vectorization
        - 5x throughput increase with parallel workers
        - 90% cache hit rate for recent data

        ## Monitoring & Alerts
        - Processing latency < 100ms (p95)
        - Error rate < 0.1%
        - Auto-scaling triggers at 70% CPU
        """

        diana_contrib = self.agents[3].create_contribution(diana_task, diana_solution)
        await self.broadcast_nutrient(diana_contrib, headers)
        await self.store_memory(diana_contrib, headers)
        print(f"✅ {self.agents[3].name}: Created comprehensive documentation\n")
        await asyncio.sleep(0.5)

        # Phase 5: Eve validates and tests
        print("Phase 5: Quality Assurance")
        print("-" * 80)
        eve_task = "Create test suite and validate performance improvements"
        eve_solution = """
        Test Results:
        ✅ Unit Tests: 150/150 passed
        ✅ Integration Tests: 45/45 passed
        ✅ Load Tests: Handles 10K req/sec
        ✅ Performance Benchmarks:
           - Before: 45 minutes for 1M records
           - After: 4.5 minutes for 1M records (10x improvement)
        ✅ Code Coverage: 92%
        ✅ Security Scan: No vulnerabilities
        ✅ Documentation: Complete and accurate

        APPROVED FOR PRODUCTION DEPLOYMENT 🚀
        """

        eve_contrib = self.agents[4].create_contribution(eve_task, eve_solution)
        await self.broadcast_nutrient(eve_contrib, headers)
        await self.store_memory(eve_contrib, headers)
        print(f"✅ {self.agents[4].name}: Validated and approved solution\n")

        # Phase 6: Search and retrieve all contributions
        print("Phase 6: Knowledge Retrieval")
        print("-" * 80)
        await self.search_collaboration_history(headers)

        self.results["collaboration_complete"] = True

    async def broadcast_nutrient(self, contribution: Dict[str, Any], headers: Dict):
        """Broadcast a nutrient to the network."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "summary": f"{contribution['agent_name']} ({contribution['role']}): {contribution['task']}",
                "embedding": contribution["embedding"],
                "snippets": [contribution["solution"][:200]],
                "tool_hints": contribution["agent_id"].split("-")[1:],
                "sensitivity": "internal",
                "ttl_sec": 600,
                "max_hops": 5,
                "quota_cost": 1.0
            }

            try:
                start_time = time.time()
                response = await client.post(
                    f"{ROUTER_URL}/v1/nutrients:broadcast",
                    json=payload,
                    headers=headers
                )
                elapsed = (time.time() - start_time) * 1000

                if response.status_code in [200, 201, 202]:
                    self.results["nutrients_broadcast"] += 1
                    self.results["performance_metrics"][f"broadcast_{contribution['agent_name']}"] = f"{elapsed:.0f}ms"
                    return True
                else:
                    error = f"Broadcast failed for {contribution['agent_name']}: {response.status_code}"
                    self.results["errors"].append(error)
                    return False
            except Exception as e:
                error = f"Broadcast error for {contribution['agent_name']}: {str(e)}"
                self.results["errors"].append(error)
                return False

    async def store_memory(self, contribution: Dict[str, Any], headers: Dict):
        """Store contribution in hyphal memory."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "agent_id": contribution["agent_id"],
                "kind": "insight",
                "content": {
                    "task": contribution["task"],
                    "solution": contribution["solution"],
                    "role": contribution["role"]
                },
                "embedding": contribution["embedding"],
                "quality": 0.9,
                "sensitivity": "internal"
            }

            try:
                start_time = time.time()
                response = await client.post(
                    f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
                    json=payload,
                    headers=headers
                )
                elapsed = (time.time() - start_time) * 1000

                if response.status_code in [200, 201]:
                    self.results["memories_stored"] += 1
                    self.results["performance_metrics"][f"store_{contribution['agent_name']}"] = f"{elapsed:.0f}ms"
                    return True
                else:
                    error = f"Memory storage failed for {contribution['agent_name']}: {response.status_code}"
                    self.results["errors"].append(error)
                    return False
            except Exception as e:
                error = f"Memory storage error for {contribution['agent_name']}: {str(e)}"
                self.results["errors"].append(error)
                return False

    async def search_collaboration_history(self, headers: Dict):
        """Search for all contributions in the collaboration."""
        queries = [
            "performance optimization techniques",
            "data analysis insights",
            "infrastructure recommendations",
            "testing and validation results"
        ]

        for query in queries:
            query_embedding = generate_embedding(query, "searcher")

            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "embedding": query_embedding,
                    "top_k": 5,
                    "min_quality": 0.5
                }

                try:
                    start_time = time.time()
                    response = await client.post(
                        f"{HYPHAL_MEMORY_URL}/v1/hyphal:search",
                        json=payload,
                        headers=headers
                    )
                    elapsed = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        data = response.json()
                        results_count = len(data.get("results", []))
                        self.results["searches_performed"] += 1
                        self.results["performance_metrics"][f"search_{self.results['searches_performed']}"] = f"{elapsed:.0f}ms"
                        print(f"   🔍 Query: '{query[:50]}...' → Found {results_count} results ({elapsed:.0f}ms)")
                except Exception as e:
                    print(f"   ⚠️  Search error: {str(e)}")

    def generate_report(self):
        """Generate comprehensive test report."""
        print(f"\n{'='*80}")
        print(f"📊 COLLABORATION TEST RESULTS")
        print(f"{'='*80}\n")

        # Overall metrics
        print(f"🎯 Overall Metrics:")
        print(f"   Tenant: {self.tenant_id}")
        print(f"   Agents: {self.results['agents_created']}/5")
        print(f"   Nutrients Broadcast: {self.results['nutrients_broadcast']}")
        print(f"   Memories Stored: {self.results['memories_stored']}")
        print(f"   Searches Performed: {self.results['searches_performed']}")
        print(f"   Collaboration: {'✅ Complete' if self.results['collaboration_complete'] else '❌ Incomplete'}")
        print()

        # Agent contributions
        print(f"👥 Agent Contributions:")
        for agent in self.agents:
            contrib_count = len(agent.contributions)
            print(f"   • {agent.name} ({agent.role}): {contrib_count} contribution(s)")
        print()

        # Performance metrics
        if self.results["performance_metrics"]:
            print(f"⚡ Performance Metrics:")
            for metric, value in self.results["performance_metrics"].items():
                print(f"   {metric}: {value}")
            print()

        # Errors
        if self.results["errors"]:
            print(f"⚠️  Errors Encountered ({len(self.results['errors'])}):")
            for error in self.results["errors"][:10]:
                print(f"   - {error}")
            print()

        # Success calculation
        total_operations = 5 + 3 + 4  # broadcasts + stores + searches
        successful_operations = (
            self.results["nutrients_broadcast"] +
            self.results["memories_stored"] +
            self.results["searches_performed"]
        )
        success_rate = (successful_operations / total_operations) * 100 if total_operations > 0 else 0

        print(f"📈 Success Rate: {success_rate:.1f}% ({successful_operations}/{total_operations} operations)")
        print()

        # Final verdict
        if success_rate >= 80 and self.results["collaboration_complete"]:
            print("🎉 RESULT: Full 5-agent collaboration successful!")
            print("   The mycelial network successfully coordinated a complex")
            print("   multi-agent workflow with knowledge sharing and retrieval.")
        elif success_rate >= 60:
            print("✅ RESULT: Collaboration partially successful")
            print("   Core functionality working, some features need attention")
        else:
            print("⚠️  RESULT: Collaboration needs improvement")
            print("   Several operations failed, requires debugging")

        print(f"\n{'='*80}\n")

        return self.results


async def main():
    """Run the 5-agent collaboration test."""
    test = CollaborationTest()

    try:
        # Setup
        if not await test.setup():
            print("❌ Setup failed, cannot continue")
            return

        # Run collaboration scenario
        await test.run_collaboration_scenario()

        # Generate report
        results = test.generate_report()

        # Save results
        with open("5_agent_collaboration_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📄 Detailed results saved to: 5_agent_collaboration_results.json\n")

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
