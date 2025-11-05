"""
Enterprise Banking Project - 100 Agent Collaboration Test (SDK Version)

Uses the official QMN Python SDK to demonstrate best practices for client integration.

This version shows how to properly use the SDK for:
- Nutrient broadcasting
- Hyphal memory storage
- Knowledge search
- Multi-agent coordination
"""

import asyncio
import sys
import os
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
sys.path.insert(0, str(sdk_path))

from qilbee_mycelial_network import MycelialClient, QMNSettings, Nutrient, Sensitivity
import hashlib
import math
import time
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


# Aicube Technology LLC Credentials
TENANT_ID = "4b374062-0494-4aad-8b3f-de40f820f1c4"
API_KEY = "qmn_4XY7KzcsajezHRsyisq_BNq1hcp-jHxsk4Lblns4dk0"
COMPANY_NAME = "Aicube Technology LLC"
CLIENT_NAME = "Global Trust Bank"


class AgentRole(Enum):
    """Agent specializations."""
    CHIEF_ARCHITECT = "Chief Architect"
    TECH_LEAD = "Technical Lead"
    BACKEND_SENIOR = "Senior Backend Engineer"
    FRONTEND_SENIOR = "Senior Frontend Engineer"
    QA_LEAD = "QA Lead"
    DEVOPS_LEAD = "DevOps Lead"


@dataclass
class Agent:
    """Agent in the development team."""
    id: str
    name: str
    role: AgentRole
    team: str
    specialization: List[str]


def generate_embedding(text: str, agent_id: str = "") -> List[float]:
    """Generate deterministic 1536-dim embedding."""
    combined = f"{agent_id}:{text}"
    hash_obj = hashlib.sha256(combined.encode())
    hash_bytes = hash_obj.digest()

    embedding = []
    for i in range(1536):
        byte_idx = i % len(hash_bytes)
        value = hash_bytes[byte_idx] / 255.0
        value = math.sin(value * math.pi * (i / 1536)) * 0.5 + 0.5
        embedding.append(value)

    magnitude = math.sqrt(sum(x**2 for x in embedding))
    return [x / magnitude for x in embedding]


async def run_sdk_simulation():
    """Run banking project simulation using QMN SDK."""
    print(f"\n{'='*80}")
    print(f"🏦 Banking Project Simulation (SDK Version)")
    print(f"{'='*80}\n")
    print(f"Company: {COMPANY_NAME}")
    print(f"Client: {CLIENT_NAME}")
    print(f"Using: QMN Python SDK")
    print()

    # Create SDK settings
    settings = QMNSettings(
        api_key=API_KEY,
        tenant_id=TENANT_ID,
        api_base_url="https://qmn.qube.aicube.ca",
        connect_timeout=15.0,
        read_timeout=30.0,
        max_retries=2,
    )

    metrics = {
        "broadcasts": 0,
        "stores": 0,
        "searches": 0,
        "errors": [],
        "start_time": time.time()
    }

    # Create specialized agents
    agents = [
        Agent("agent-001", "Chief Architect", AgentRole.CHIEF_ARCHITECT, "Architecture",
              ["system_design", "microservices", "scalability"]),
        Agent("agent-002", "Tech Lead", AgentRole.TECH_LEAD, "Architecture",
              ["code_review", "best_practices", "mentoring"]),
        Agent("agent-010", "Backend Lead", AgentRole.BACKEND_SENIOR, "Backend",
              ["java", "spring_boot", "api_design"]),
        Agent("agent-025", "Frontend Lead", AgentRole.FRONTEND_SENIOR, "Frontend",
              ["react", "typescript", "design_systems"]),
        Agent("agent-040", "QA Lead", AgentRole.QA_LEAD, "QA",
              ["test_automation", "quality_metrics", "ci_cd"]),
        Agent("agent-050", "DevOps Lead", AgentRole.DEVOPS_LEAD, "DevOps",
              ["kubernetes", "terraform", "monitoring"]),
    ]

    print(f"👥 Team: {len(agents)} key agents\n")

    # Use SDK with context manager
    client = MycelialClient(settings)
    async with client:
        print(f"✅ Connected to QMN")
        print()

        # Phase 1: Architecture
        print("📐 PHASE 1: Architecture Design")
        print("-" * 80)

        architect_knowledge = [
            {
                "agent": agents[0],
                "knowledge": "Designed microservices architecture: 50 services, event-driven, CQRS pattern with Istio service mesh.",
                "quality": 0.95
            },
            {
                "agent": agents[1],
                "knowledge": "Established coding standards: Java 17, Spring Boot 3.x, reactive programming with WebFlux. SonarQube quality gates enforced.",
                "quality": 0.92
            }
        ]

        for item in architect_knowledge:
            agent = item["agent"]
            knowledge = item["knowledge"]
            embedding = generate_embedding(knowledge, agent.id)

            try:
                # Broadcast using SDK
                nutrient = Nutrient(
                    summary=f"[{agent.team}] {agent.name}: {knowledge}",
                    embedding=embedding,
                    snippets=[knowledge[:500]],
                    tool_hints=agent.specialization[:3],
                    sensitivity=Sensitivity.INTERNAL,
                    ttl_sec=3600,
                    max_hops=5,
                    quota_cost=1
                )

                response = await client.broadcast(nutrient)
                metrics["broadcasts"] += 1
                print(f"   ✅ {agent.name}: Broadcast successful")

                # Store in hyphal memory using SDK
                store_response = await client.hyphal_store(
                    agent_id=agent.id,
                    kind="plan",
                    content={
                        "agent_name": agent.name,
                        "role": agent.role.value,
                        "team": agent.team,
                        "knowledge": knowledge
                    },
                    embedding=embedding,
                    quality=item["quality"],
                    sensitivity="internal"
                )
                metrics["stores"] += 1

            except Exception as e:
                metrics["errors"].append(f"Error for {agent.name}: {str(e)}")
                print(f"   ❌ {agent.name}: {str(e)}")

            await asyncio.sleep(0.3)

        print()

        # Phase 2: Development
        print("💻 PHASE 2: Development")
        print("-" * 80)

        dev_work = [
            {
                "agent": agents[2],
                "knowledge": "Implemented Payment Processing Service: handles 10k TPS with Redis caching, idempotency keys for duplicate prevention."
            },
            {
                "agent": agents[3],
                "knowledge": "Built responsive dashboard with real-time updates: WebSocket connection for live transactions, virtualized rendering for performance."
            }
        ]

        for item in dev_work:
            agent = item["agent"]
            knowledge = item["knowledge"]
            embedding = generate_embedding(knowledge, agent.id)

            try:
                nutrient = Nutrient(
                    summary=f"{agent.name}: {knowledge[:100]}...",
                    embedding=embedding,
                    snippets=[knowledge],
                    tool_hints=agent.specialization,
                    sensitivity=Sensitivity.INTERNAL,
                    ttl_sec=3600,
                    max_hops=5,
                    quota_cost=1
                )

                await client.broadcast(nutrient)
                metrics["broadcasts"] += 1
                print(f"   ✅ {agent.name}: Feature delivered")

                await client.hyphal_store(
                    agent_id=agent.id,
                    kind="snippet",
                    content={"knowledge": knowledge, "agent": agent.name},
                    embedding=embedding,
                    quality=0.88,
                    sensitivity="internal"
                )
                metrics["stores"] += 1

            except Exception as e:
                metrics["errors"].append(f"Dev error for {agent.name}: {str(e)}")

            await asyncio.sleep(0.3)

        print()

        # Phase 3: Testing
        print("🧪 PHASE 3: Quality Assurance")
        print("-" * 80)

        qa_knowledge = {
            "agent": agents[4],
            "knowledge": "Performance testing complete: System handles 50k concurrent users, 100k TPS. 99th percentile latency <500ms. Auto-scaling validated.",
            "quality": 0.90
        }

        try:
            embedding = generate_embedding(qa_knowledge["knowledge"], qa_knowledge["agent"].id)

            nutrient = Nutrient(
                summary=f"QA: {qa_knowledge['knowledge'][:100]}...",
                embedding=embedding,
                snippets=[qa_knowledge["knowledge"]],
                tool_hints=qa_knowledge["agent"].specialization,
                sensitivity=Sensitivity.INTERNAL,
                ttl_sec=3600,
                max_hops=5,
                quota_cost=1
            )

            await client.broadcast(nutrient)
            metrics["broadcasts"] += 1

            await client.hyphal_store(
                agent_id=qa_knowledge["agent"].id,
                kind="outcome",
                content={"test_results": qa_knowledge["knowledge"]},
                embedding=embedding,
                quality=qa_knowledge["quality"],
                sensitivity="internal"
            )
            metrics["stores"] += 1
            print(f"   ✅ {qa_knowledge['agent'].name}: Testing results shared")

        except Exception as e:
            metrics["errors"].append(f"QA error: {str(e)}")

        await asyncio.sleep(0.3)
        print()

        # Phase 4: Deployment
        print("🚀 PHASE 4: Deployment")
        print("-" * 80)

        devops_knowledge = {
            "agent": agents[5],
            "knowledge": "Deployed to production: Blue-green strategy, zero downtime. Kubernetes 500 nodes across 3 AZs. Monitoring with Prometheus/Grafana.",
            "quality": 0.93
        }

        try:
            embedding = generate_embedding(devops_knowledge["knowledge"], devops_knowledge["agent"].id)

            nutrient = Nutrient(
                summary=f"DevOps: {devops_knowledge['knowledge'][:100]}...",
                embedding=embedding,
                snippets=[devops_knowledge["knowledge"]],
                tool_hints=devops_knowledge["agent"].specialization,
                sensitivity=Sensitivity.INTERNAL,
                ttl_sec=3600,
                max_hops=5,
                quota_cost=1
            )

            await client.broadcast(nutrient)
            metrics["broadcasts"] += 1
            print(f"   ✅ {devops_knowledge['agent'].name}: Deployment complete")

        except Exception as e:
            metrics["errors"].append(f"DevOps error: {str(e)}")

        await asyncio.sleep(0.3)
        print()

        # Phase 5: Knowledge Search
        print("🔍 PHASE 5: Knowledge Search")
        print("-" * 80)

        search_queries = [
            "How do we handle database scaling?",
            "What security measures are in place?",
            "What's the deployment strategy?",
        ]

        for query in search_queries:
            try:
                query_embedding = generate_embedding(query, "searcher")
                results = await client.hyphal_search(
                    embedding=query_embedding,
                    top_k=5,
                    filters={"min_quality": 0.5}
                )
                metrics["searches"] += 1
                print(f"   🔍 '{query}' → Found {len(results)} results")

            except Exception as e:
                metrics["errors"].append(f"Search error: {str(e)}")
                print(f"   ⚠️  '{query}' → Error: {str(e)}")

            await asyncio.sleep(0.3)

    metrics["end_time"] = time.time()
    duration = metrics["end_time"] - metrics["start_time"]

    # Report
    print(f"\n{'='*80}")
    print(f"📊 SDK SIMULATION REPORT")
    print(f"{'='*80}\n")

    print(f"🔄 Operations:")
    print(f"   Nutrients Broadcast: {metrics['broadcasts']}")
    print(f"   Memories Stored: {metrics['stores']}")
    print(f"   Searches Performed: {metrics['searches']}")
    print(f"   Total: {metrics['broadcasts'] + metrics['stores'] + metrics['searches']}")
    print()

    print(f"⏱️  Performance:")
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Ops/Second: {(metrics['broadcasts'] + metrics['stores']) / duration:.2f}")
    print()

    if metrics["errors"]:
        print(f"⚠️  Errors: {len(metrics['errors'])}")
        for err in metrics["errors"][:5]:
            print(f"   • {err}")
    else:
        print(f"✅ No Errors - Perfect Execution")

    print()
    print(f"🎉 SDK Simulation Complete!")
    print(f"{'='*80}\n")

    return metrics


if __name__ == "__main__":
    asyncio.run(run_sdk_simulation())
