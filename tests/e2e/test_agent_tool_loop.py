"""
End-to-End Test: Agent Loop with Tool Use and Mycelial Network

This test demonstrates:
1. Agent using tools (bash, file operations)
2. Broadcasting tool results to mycelial network
3. Other agents discovering and using those results
4. Complete worker loop with memory persistence
"""

import asyncio
import httpx
import json
import hashlib
import math
from datetime import datetime
from typing import List, Dict, Any
import uuid


# ============================================================
# Configuration
# ============================================================
IDENTITY_URL = "http://localhost:8100"
ROUTER_URL = "http://localhost:8200"
HYPHAL_MEMORY_URL = "http://localhost:8201"

# Agent configurations
AGENTS = [
    {
        "agent_id": "agent-bash-executor",
        "name": "BashExecutor",
        "role": "System Command Specialist",
        "capabilities": ["bash", "system_commands", "file_operations"],
        "tools": ["bash", "file_read", "file_write"]
    },
    {
        "agent_id": "agent-data-analyzer",
        "name": "DataAnalyzer",
        "role": "Data Analysis Specialist",
        "capabilities": ["data_analysis", "json_parsing", "statistics"],
        "tools": ["bash", "file_read"]
    },
    {
        "agent_id": "agent-code-generator",
        "name": "CodeGenerator",
        "role": "Code Generation Specialist",
        "capabilities": ["code_generation", "python", "scripting"],
        "tools": ["file_write", "bash"]
    }
]


# ============================================================
# Helper Functions
# ============================================================
def generate_embedding(text: str, dimensions: int = 1536) -> List[float]:
    """Generate deterministic embedding from text using hash-based approach."""
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()

    embedding = []
    for i in range(dimensions):
        byte_idx = i % len(hash_bytes)
        value = hash_bytes[byte_idx] / 255.0
        value = math.sin(value * math.pi * (i / dimensions)) * 0.5 + 0.5
        embedding.append(value)

    # Normalize
    magnitude = math.sqrt(sum(x**2 for x in embedding))
    return [x / magnitude for x in embedding]


async def create_tenant(tenant_id: str) -> Dict[str, Any]:
    """Create a new tenant for testing."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{IDENTITY_URL}/v1/tenants",
            json={
                "id": tenant_id,
                "name": "Agent Tool Loop Test Organization",
                "plan_tier": "enterprise",
                "kms_key_id": f"kms-key-{tenant_id}",
                "region_preference": "us-east-1",
                "metadata": {
                    "test_run": datetime.utcnow().isoformat(),
                    "test_type": "agent_tool_loop"
                }
            },
            headers={"X-Tenant-ID": tenant_id}
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create tenant: {response.status_code} - {response.text}")

        return response.json()


async def simulate_tool_execution(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate tool execution (bash, file_read, file_write)."""

    if tool_name == "bash":
        command = tool_input.get("command", "")
        # Simulate bash execution
        if "echo" in command:
            output = command.replace("echo ", "").strip('"').strip("'")
        elif "ls" in command:
            output = "file1.txt\nfile2.py\ndata.json"
        elif "cat" in command:
            output = '{"users": 150, "sessions": 450, "revenue": 12500}'
        elif "python" in command and "analyze" in command:
            output = "Analysis complete:\nTotal users: 150\nAverage sessions: 3.0\nRevenue per user: $83.33"
        else:
            output = f"Executed: {command}"

        return {
            "success": True,
            "output": output,
            "exit_code": 0
        }

    elif tool_name == "file_read":
        path = tool_input.get("path", "")
        # Simulate file reading
        if "data.json" in path:
            content = '{"users": 150, "sessions": 450, "revenue": 12500}'
        elif "analysis.txt" in path:
            content = "Previous analysis:\nUsers growing at 15% MoM\nRevenue per session: $27.78"
        else:
            content = f"Content of {path}"

        return {
            "success": True,
            "content": content,
            "path": path
        }

    elif tool_name == "file_write":
        path = tool_input.get("path", "")
        content = tool_input.get("content", "")

        return {
            "success": True,
            "path": path,
            "bytes_written": len(content)
        }

    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }


async def agent_worker_loop(
    agent_id: str,
    task_description: str,
    tenant_id: str,
    max_iterations: int = 5
) -> List[Dict[str, Any]]:
    """
    Simulate an agent worker loop with tool use.

    This mimics what anthropic_client.py:worker_loop does:
    1. Search mycelial network for context
    2. Execute task with tools
    3. Broadcast results to network
    4. Store in hyphal memory
    """

    iterations = []

    for iteration in range(max_iterations):
        iteration_data = {
            "iteration": iteration + 1,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        # ========================================
        # Phase 1: Search Mycelial Network
        # ========================================
        print(f"\n{'='*60}")
        print(f"[{agent_id}] Iteration {iteration + 1}: {task_description}")
        print(f"{'='*60}")

        query_embedding = generate_embedding(task_description)

        async with httpx.AsyncClient() as client:
            search_response = await client.post(
                f"{HYPHAL_MEMORY_URL}/v1/hyphal:search",
                json={
                    "embedding": query_embedding,
                    "top_k": 3,
                    "min_quality": 0.5
                },
                headers={"X-Tenant-ID": tenant_id}
            )

            if search_response.status_code == 200:
                search_results = search_response.json()
                past_knowledge = search_results.get("results", [])
                iteration_data["past_knowledge_found"] = len(past_knowledge)

                if past_knowledge:
                    print(f"\n🔍 Found {len(past_knowledge)} relevant memories:")
                    for i, memory in enumerate(past_knowledge, 1):
                        print(f"   {i}. {memory.get('kind')}: {memory.get('content', {}).get('summary', 'N/A')[:60]}...")
                        print(f"      Quality: {memory.get('quality'):.2f}, Similarity: {memory.get('similarity', 0):.3f}")
                else:
                    print("\n🔍 No relevant past knowledge found")
            else:
                print(f"⚠️  Search failed: {search_response.status_code}")
                past_knowledge = []
                iteration_data["past_knowledge_found"] = 0

        # ========================================
        # Phase 2: Decide on Tool Use
        # ========================================
        # Based on task and agent capabilities, decide which tools to use
        tools_to_use = []

        if iteration == 0:  # First iteration - gather data
            if "bash" in AGENTS[0]["capabilities"] or "bash" in AGENTS[1]["capabilities"]:
                tools_to_use.append({
                    "tool": "bash",
                    "input": {"command": "cat data.json"}
                })

        elif iteration == 1:  # Second iteration - analyze data
            if "data_analysis" in task_description or "analyze" in task_description:
                tools_to_use.append({
                    "tool": "bash",
                    "input": {"command": "python analyze_data.py data.json"}
                })

        elif iteration == 2:  # Third iteration - generate code
            if "code" in task_description or "generate" in task_description:
                tools_to_use.append({
                    "tool": "file_write",
                    "input": {
                        "path": "report.py",
                        "content": "#!/usr/bin/env python3\nimport json\n\ndef analyze(data):\n    return data"
                    }
                })

        # ========================================
        # Phase 3: Execute Tools
        # ========================================
        tool_results = []

        for tool_use in tools_to_use:
            tool_name = tool_use["tool"]
            tool_input = tool_use["input"]

            print(f"\n🔧 Executing tool: {tool_name}")
            print(f"   Input: {json.dumps(tool_input, indent=2)}")

            result = await simulate_tool_execution(tool_name, tool_input)
            tool_results.append({
                "tool": tool_name,
                "input": tool_input,
                "result": result
            })

            print(f"   ✅ Result: {json.dumps(result, indent=2)[:100]}...")

        iteration_data["tools_used"] = len(tool_results)
        iteration_data["tool_results"] = tool_results

        # ========================================
        # Phase 4: Generate Response/Output
        # ========================================
        if iteration == 0:
            response_text = f"Data retrieved: {{users: 150, sessions: 450, revenue: 12500}}"
            summary = "Initial data collection complete"
        elif iteration == 1:
            response_text = f"Analysis complete: Total users: 150, Avg sessions: 3.0, Revenue/user: $83.33"
            summary = "Data analysis complete with insights"
        elif iteration == 2:
            response_text = f"Generated analysis script in report.py"
            summary = "Code generation complete"
        else:
            response_text = f"Task iteration {iteration + 1} complete"
            summary = f"Iteration {iteration + 1} summary"

        iteration_data["response"] = response_text
        iteration_data["summary"] = summary

        print(f"\n💬 Agent Response: {response_text}")

        # ========================================
        # Phase 5: Broadcast to Mycelial Network
        # ========================================
        response_embedding = generate_embedding(response_text)

        async with httpx.AsyncClient() as client:
            broadcast_response = await client.post(
                f"{ROUTER_URL}/v1/nutrients:broadcast",
                json={
                    "summary": summary,
                    "embedding": response_embedding,
                    "snippets": [response_text[:200]],
                    "tool_hints": [agent_id.split("-")[-1], "tool_execution"],
                    "sensitivity": "internal",
                    "max_hops": 3,
                    "ttl_sec": 600,
                    "quota_cost": 1.0
                },
                headers={"X-Tenant-ID": tenant_id}
            )

            if broadcast_response.status_code in [200, 201]:
                broadcast_data = broadcast_response.json()
                print(f"📡 Broadcast successful: {broadcast_data.get('nutrient_id')}")
                iteration_data["broadcast_success"] = True
                iteration_data["nutrient_id"] = broadcast_data.get("nutrient_id")
            else:
                print(f"⚠️  Broadcast failed: {broadcast_response.status_code}")
                iteration_data["broadcast_success"] = False

        # ========================================
        # Phase 6: Store in Hyphal Memory
        # ========================================
        if tool_results or iteration <= 2:  # Store important iterations
            async with httpx.AsyncClient() as client:
                memory_response = await client.post(
                    f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
                    json={
                        "agent_id": agent_id,
                        "kind": "tool_result" if tool_results else "insight",
                        "content": {
                            "summary": summary,
                            "response": response_text,
                            "tools_used": [tr["tool"] for tr in tool_results],
                            "iteration": iteration + 1
                        },
                        "embedding": response_embedding,
                        "quality": 0.85 if tool_results else 0.7,
                        "sensitivity": "internal",
                        "metadata": {
                            "agent_id": agent_id,
                            "iteration": iteration + 1,
                            "tools_count": len(tool_results)
                        }
                    },
                    headers={"X-Tenant-ID": tenant_id}
                )

                if memory_response.status_code in [200, 201]:
                    memory_data = memory_response.json()
                    print(f"💾 Stored in memory: {memory_data.get('id')}")
                    iteration_data["memory_stored"] = True
                    iteration_data["memory_id"] = memory_data.get("id")
                else:
                    print(f"⚠️  Memory storage failed: {memory_response.status_code}")
                    iteration_data["memory_stored"] = False

        iterations.append(iteration_data)

        # ========================================
        # Phase 7: Check if Task Complete
        # ========================================
        # For this test, we complete after 3 iterations
        if iteration >= 2:
            print(f"\n✅ Task complete after {iteration + 1} iterations")
            break

        # Small delay between iterations
        await asyncio.sleep(0.5)

    return iterations


async def run_multi_agent_collaboration(tenant_id: str):
    """
    Run a complete multi-agent collaboration scenario.

    Scenario:
    1. BashExecutor retrieves data files
    2. DataAnalyzer analyzes the data (uses BashExecutor's results)
    3. CodeGenerator creates analysis script (uses both previous results)
    """

    print("\n" + "="*80)
    print("🚀 MULTI-AGENT COLLABORATION TEST")
    print("="*80)

    all_results = {}

    # ========================================
    # Agent 1: BashExecutor - Data Retrieval
    # ========================================
    print("\n\n" + "▶"*40)
    print("AGENT 1: BashExecutor - Data Retrieval Task")
    print("▶"*40)

    bash_iterations = await agent_worker_loop(
        agent_id=AGENTS[0]["agent_id"],
        task_description="Retrieve and examine data files from the system",
        tenant_id=tenant_id,
        max_iterations=2
    )

    all_results["bash_executor"] = bash_iterations

    # Wait for data to propagate
    await asyncio.sleep(1)

    # ========================================
    # Agent 2: DataAnalyzer - Analysis
    # ========================================
    print("\n\n" + "▶"*40)
    print("AGENT 2: DataAnalyzer - Data Analysis Task")
    print("▶"*40)

    analyzer_iterations = await agent_worker_loop(
        agent_id=AGENTS[1]["agent_id"],
        task_description="Analyze the data and provide insights on user metrics",
        tenant_id=tenant_id,
        max_iterations=2
    )

    all_results["data_analyzer"] = analyzer_iterations

    # Wait for data to propagate
    await asyncio.sleep(1)

    # ========================================
    # Agent 3: CodeGenerator - Script Creation
    # ========================================
    print("\n\n" + "▶"*40)
    print("AGENT 3: CodeGenerator - Script Generation Task")
    print("▶"*40)

    code_iterations = await agent_worker_loop(
        agent_id=AGENTS[2]["agent_id"],
        task_description="Generate Python script for automated data analysis based on previous findings",
        tenant_id=tenant_id,
        max_iterations=2
    )

    all_results["code_generator"] = code_iterations

    return all_results


async def verify_knowledge_sharing(tenant_id: str):
    """
    Verify that agents shared knowledge through the mycelial network.
    """

    print("\n\n" + "="*80)
    print("🔍 KNOWLEDGE SHARING VERIFICATION")
    print("="*80)

    # Search for all stored knowledge
    queries = [
        ("data retrieval", ["bash", "file_operations"]),
        ("data analysis", ["data_analysis", "statistics"]),
        ("code generation", ["code_generation", "python"])
    ]

    total_found = 0

    for query_text, expected_hints in queries:
        print(f"\n📊 Query: '{query_text}'")

        query_embedding = generate_embedding(query_text)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HYPHAL_MEMORY_URL}/v1/hyphal:search",
                json={
                    "embedding": query_embedding,
                    "top_k": 5,
                    "min_quality": 0.5
                },
                headers={"X-Tenant-ID": tenant_id}
            )

            if response.status_code == 200:
                results = response.json().get("results", [])
                print(f"   Found {len(results)} results:")

                for i, result in enumerate(results, 1):
                    agent_id = result.get("agent_id", "unknown")
                    kind = result.get("kind", "unknown")
                    similarity = result.get("similarity", 0)
                    quality = result.get("quality", 0)
                    content = result.get("content", {})

                    print(f"   {i}. Agent: {agent_id}")
                    print(f"      Kind: {kind}, Quality: {quality:.2f}, Similarity: {similarity:.3f}")
                    print(f"      Summary: {content.get('summary', 'N/A')}")

                total_found += len(results)
            else:
                print(f"   ❌ Search failed: {response.status_code}")

    print(f"\n✅ Total knowledge items found: {total_found}")
    return total_found


async def generate_test_report(tenant_id: str, results: Dict[str, Any], knowledge_count: int):
    """Generate comprehensive test report."""

    report = {
        "test_type": "agent_tool_loop_collaboration",
        "timestamp": datetime.utcnow().isoformat(),
        "tenant_id": tenant_id,
        "summary": {
            "total_agents": len(AGENTS),
            "total_iterations": sum(len(agent_results) for agent_results in results.values()),
            "knowledge_items_stored": knowledge_count,
        },
        "agent_results": {},
        "metrics": {
            "broadcasts": 0,
            "memory_stores": 0,
            "tools_executed": 0,
            "knowledge_searches": 0
        }
    }

    # Analyze results for each agent
    for agent_key, iterations in results.items():
        agent_summary = {
            "iterations": len(iterations),
            "tools_used": 0,
            "broadcasts": 0,
            "memories_stored": 0,
            "knowledge_found": 0
        }

        for iteration in iterations:
            agent_summary["tools_used"] += iteration.get("tools_used", 0)
            if iteration.get("broadcast_success"):
                agent_summary["broadcasts"] += 1
                report["metrics"]["broadcasts"] += 1
            if iteration.get("memory_stored"):
                agent_summary["memories_stored"] += 1
                report["metrics"]["memory_stores"] += 1
            agent_summary["knowledge_found"] += iteration.get("past_knowledge_found", 0)

        report["agent_results"][agent_key] = agent_summary
        report["metrics"]["tools_executed"] += agent_summary["tools_used"]
        report["metrics"]["knowledge_searches"] += len(iterations)

    # Success criteria
    report["success_criteria"] = {
        "all_agents_executed": len(results) == len(AGENTS),
        "knowledge_shared": knowledge_count > 0,
        "broadcasts_successful": report["metrics"]["broadcasts"] > 0,
        "memory_persistence": report["metrics"]["memory_stores"] > 0,
        "tools_executed": report["metrics"]["tools_executed"] > 0
    }

    report["overall_success"] = all(report["success_criteria"].values())

    return report


# ============================================================
# Main Test
# ============================================================
async def main():
    """Run complete agent tool loop test."""

    print("\n" + "🧬"*40)
    print("QILBEE MYCELIAL NETWORK - Agent Tool Loop Test")
    print("🧬"*40)

    # Generate unique tenant ID
    tenant_id = f"tool-loop-test-{uuid.uuid4().hex[:8]}"

    try:
        # ========================================
        # Setup: Create Tenant
        # ========================================
        print(f"\n📋 Creating tenant: {tenant_id}")
        tenant = await create_tenant(tenant_id)
        print(f"✅ Tenant created: {tenant.get('id')}")

        # ========================================
        # Phase 1: Multi-Agent Collaboration
        # ========================================
        collaboration_results = await run_multi_agent_collaboration(tenant_id)

        # ========================================
        # Phase 2: Verify Knowledge Sharing
        # ========================================
        await asyncio.sleep(2)  # Allow time for data propagation
        knowledge_count = await verify_knowledge_sharing(tenant_id)

        # ========================================
        # Phase 3: Generate Report
        # ========================================
        report = await generate_test_report(tenant_id, collaboration_results, knowledge_count)

        # ========================================
        # Display Results
        # ========================================
        print("\n\n" + "="*80)
        print("📊 TEST REPORT")
        print("="*80)

        print(f"\nTenant ID: {report['tenant_id']}")
        print(f"Timestamp: {report['timestamp']}")

        print(f"\n📈 Summary:")
        print(f"   Total Agents: {report['summary']['total_agents']}")
        print(f"   Total Iterations: {report['summary']['total_iterations']}")
        print(f"   Knowledge Items: {report['summary']['knowledge_items_stored']}")

        print(f"\n📊 Metrics:")
        print(f"   Broadcasts: {report['metrics']['broadcasts']}")
        print(f"   Memory Stores: {report['metrics']['memory_stores']}")
        print(f"   Tools Executed: {report['metrics']['tools_executed']}")
        print(f"   Knowledge Searches: {report['metrics']['knowledge_searches']}")

        print(f"\n🤖 Agent Results:")
        for agent_key, agent_data in report['agent_results'].items():
            print(f"\n   {agent_key}:")
            print(f"      Iterations: {agent_data['iterations']}")
            print(f"      Tools Used: {agent_data['tools_used']}")
            print(f"      Broadcasts: {agent_data['broadcasts']}")
            print(f"      Memories Stored: {agent_data['memories_stored']}")
            print(f"      Knowledge Found: {agent_data['knowledge_found']}")

        print(f"\n✅ Success Criteria:")
        for criterion, passed in report['success_criteria'].items():
            status = "✅" if passed else "❌"
            print(f"   {status} {criterion}: {passed}")

        print(f"\n{'='*80}")
        if report['overall_success']:
            print("🎉 TEST PASSED - All criteria met!")
        else:
            print("❌ TEST FAILED - Some criteria not met")
        print(f"{'='*80}")

        # Save report to file
        report_filename = f"agent_tool_loop_test_report_{tenant_id}.json"
        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Report saved to: {report_filename}")

        return report['overall_success']

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
