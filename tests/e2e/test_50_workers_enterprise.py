"""
Enterprise Scenario: 50 Synthetic Workers Across Multiple Departments

This test simulates a real enterprise with 50 AI workers distributed across:
- Engineering (15 workers)
- Customer Support (10 workers)
- Sales & Marketing (8 workers)
- Finance & Operations (7 workers)
- HR & Legal (5 workers)
- Product & Design (5 workers)

Each worker solves problems in their domain and shares knowledge through
the mycelial network, creating a company-wide learning system.
"""

import asyncio
import httpx
import json
import hashlib
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid
from collections import defaultdict
import random


# ============================================================
# Configuration
# ============================================================
IDENTITY_URL = "http://localhost:8100"
ROUTER_URL = "http://localhost:8200"
HYPHAL_MEMORY_URL = "http://localhost:8201"

# ============================================================
# Department & Worker Definitions
# ============================================================

DEPARTMENTS = {
    "engineering": {
        "name": "Engineering",
        "workers": [
            {"id": "eng-backend-001", "name": "Backend API Developer", "focus": "REST APIs, databases, microservices"},
            {"id": "eng-backend-002", "name": "Backend Performance Engineer", "focus": "Query optimization, caching, scaling"},
            {"id": "eng-frontend-001", "name": "Frontend React Developer", "focus": "React, TypeScript, UI components"},
            {"id": "eng-frontend-002", "name": "Frontend Performance", "focus": "Bundle optimization, rendering, UX"},
            {"id": "eng-mobile-001", "name": "iOS Developer", "focus": "Swift, iOS SDK, mobile UX"},
            {"id": "eng-mobile-002", "name": "Android Developer", "focus": "Kotlin, Android SDK, mobile perf"},
            {"id": "eng-devops-001", "name": "DevOps Infrastructure", "focus": "Kubernetes, Docker, CI/CD"},
            {"id": "eng-devops-002", "name": "DevOps Monitoring", "focus": "Prometheus, Grafana, alerting"},
            {"id": "eng-data-001", "name": "Data Pipeline Engineer", "focus": "ETL, Airflow, data quality"},
            {"id": "eng-data-002", "name": "ML Engineer", "focus": "Model training, deployment, MLOps"},
            {"id": "eng-security-001", "name": "Security Engineer", "focus": "Penetration testing, vulnerabilities"},
            {"id": "eng-security-002", "name": "Security Compliance", "focus": "SOC2, GDPR, security audits"},
            {"id": "eng-qa-001", "name": "QA Automation", "focus": "Selenium, pytest, test automation"},
            {"id": "eng-qa-002", "name": "QA Performance Testing", "focus": "Load testing, JMeter, benchmarks"},
            {"id": "eng-architect-001", "name": "Solutions Architect", "focus": "System design, architecture review"},
        ],
        "common_tasks": [
            "Fix production bug in payment processing",
            "Optimize database queries for user dashboard",
            "Implement new REST API endpoint for mobile app",
            "Review and fix security vulnerability in authentication",
            "Set up CI/CD pipeline for new microservice",
            "Debug memory leak in backend service",
            "Optimize React component rendering performance",
            "Implement caching layer for frequently accessed data",
            "Write integration tests for checkout flow",
            "Review code for SQL injection vulnerabilities"
        ]
    },
    "customer_support": {
        "name": "Customer Support",
        "workers": [
            {"id": "cs-tier1-001", "name": "Support Agent L1", "focus": "Basic troubleshooting, FAQs"},
            {"id": "cs-tier1-002", "name": "Support Agent L1", "focus": "Account issues, billing questions"},
            {"id": "cs-tier2-001", "name": "Support Agent L2", "focus": "Technical issues, integrations"},
            {"id": "cs-tier2-002", "name": "Support Agent L2", "focus": "Complex troubleshooting, escalations"},
            {"id": "cs-specialist-001", "name": "Integration Specialist", "focus": "API support, third-party integrations"},
            {"id": "cs-specialist-002", "name": "Billing Specialist", "focus": "Invoicing, payment issues, refunds"},
            {"id": "cs-success-001", "name": "Customer Success Manager", "focus": "Onboarding, adoption, retention"},
            {"id": "cs-success-002", "name": "Customer Success Manager", "focus": "Enterprise customers, renewals"},
            {"id": "cs-quality-001", "name": "Quality Assurance", "focus": "Ticket review, CSAT analysis"},
            {"id": "cs-training-001", "name": "Training Coordinator", "focus": "Documentation, training materials"},
        ],
        "common_tasks": [
            "Customer unable to login after password reset",
            "Integration with Salesforce not syncing contacts",
            "Billing discrepancy for enterprise customer",
            "Customer requesting feature: bulk export data",
            "API rate limit exceeded - customer needs increase",
            "Mobile app crashes on iOS 17",
            "Customer onboarding: setup SSO with Okta",
            "Investigate slow dashboard loading for customer",
            "Customer data export request (GDPR compliance)",
            "Help customer migrate from competitor platform"
        ]
    },
    "sales_marketing": {
        "name": "Sales & Marketing",
        "workers": [
            {"id": "sales-ae-001", "name": "Account Executive", "focus": "Enterprise deals, demos"},
            {"id": "sales-ae-002", "name": "Account Executive", "focus": "Mid-market sales"},
            {"id": "sales-sdr-001", "name": "Sales Development Rep", "focus": "Lead qualification, outreach"},
            {"id": "sales-sdr-002", "name": "Sales Development Rep", "focus": "Inbound leads, demos"},
            {"id": "marketing-content-001", "name": "Content Marketing", "focus": "Blog posts, case studies, SEO"},
            {"id": "marketing-growth-001", "name": "Growth Marketing", "focus": "A/B testing, conversion optimization"},
            {"id": "marketing-social-001", "name": "Social Media Manager", "focus": "LinkedIn, Twitter, community"},
            {"id": "marketing-analytics-001", "name": "Marketing Analytics", "focus": "Campaign ROI, attribution"},
        ],
        "common_tasks": [
            "Prepare demo for Fortune 500 prospect",
            "Create case study for enterprise customer success",
            "Analyze why conversion rate dropped 15% this week",
            "Competitor analysis: new features announced",
            "Optimize landing page for Google Ads campaign",
            "Prepare ROI calculator for sales presentations",
            "Research target companies for outbound campaign",
            "Analyze which blog posts drive most signups",
            "Create content for product launch announcement",
            "Investigate spike in trial signups from organic search"
        ]
    },
    "finance_operations": {
        "name": "Finance & Operations",
        "workers": [
            {"id": "fin-accountant-001", "name": "Senior Accountant", "focus": "Financial reporting, reconciliation"},
            {"id": "fin-ar-001", "name": "Accounts Receivable", "focus": "Invoicing, collections, revenue"},
            {"id": "fin-ap-001", "name": "Accounts Payable", "focus": "Vendor payments, expense tracking"},
            {"id": "fin-fp&a-001", "name": "Financial Planning & Analysis", "focus": "Forecasting, budgets, metrics"},
            {"id": "ops-procurement-001", "name": "Procurement Specialist", "focus": "Vendor management, contracts"},
            {"id": "ops-facilities-001", "name": "Facilities Manager", "focus": "Office management, equipment"},
            {"id": "ops-it-001", "name": "IT Operations", "focus": "Employee laptops, software licenses"},
        ],
        "common_tasks": [
            "Reconcile Q3 revenue against Stripe payouts",
            "Investigate $50K variance in cloud infrastructure costs",
            "Prepare financial forecast for board meeting",
            "Analyze customer churn impact on ARR",
            "Review and approve vendor contracts for SaaS tools",
            "Calculate unit economics for new pricing tier",
            "Audit expense reports for policy compliance",
            "Optimize software license utilization",
            "Prepare cash flow projection for next quarter",
            "Analyze profitability by customer segment"
        ]
    },
    "hr_legal": {
        "name": "HR & Legal",
        "workers": [
            {"id": "hr-recruiter-001", "name": "Technical Recruiter", "focus": "Engineering hiring"},
            {"id": "hr-recruiter-002", "name": "Recruiter", "focus": "Sales, marketing hiring"},
            {"id": "hr-ops-001", "name": "HR Operations", "focus": "Benefits, onboarding, policies"},
            {"id": "legal-counsel-001", "name": "Legal Counsel", "focus": "Contracts, compliance, IP"},
            {"id": "legal-privacy-001", "name": "Privacy Officer", "focus": "GDPR, CCPA, data protection"},
        ],
        "common_tasks": [
            "Review employment contract for senior engineer offer",
            "Investigate GDPR data deletion request process",
            "Source candidates for Staff Backend Engineer role",
            "Review customer DPA (Data Processing Agreement)",
            "Analyze time-to-hire metrics and bottlenecks",
            "Prepare employee handbook policy updates",
            "Review terms of service changes for legal compliance",
            "Coordinate onboarding for 5 new engineering hires",
            "Analyze diversity metrics in hiring funnel",
            "Review vendor contract for compliance with privacy policy"
        ]
    },
    "product_design": {
        "name": "Product & Design",
        "workers": [
            {"id": "pm-core-001", "name": "Product Manager - Core", "focus": "Main product features, roadmap"},
            {"id": "pm-growth-001", "name": "Product Manager - Growth", "focus": "Onboarding, activation, retention"},
            {"id": "design-ui-001", "name": "UI/UX Designer", "focus": "User interface, visual design"},
            {"id": "design-ux-001", "name": "UX Researcher", "focus": "User research, usability testing"},
            {"id": "design-sys-001", "name": "Design Systems", "focus": "Component library, design tokens"},
        ],
        "common_tasks": [
            "Analyze user feedback on new dashboard redesign",
            "Design mobile app onboarding flow",
            "Conduct usability testing for checkout process",
            "Prioritize feature requests from enterprise customers",
            "Research competitor features and user sentiment",
            "Design component library for dark mode",
            "Analyze user drop-off in trial signup funnel",
            "Create wireframes for new reporting feature",
            "Review accessibility compliance (WCAG 2.1)",
            "Analyze feature adoption metrics post-launch"
        ]
    }
}


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
    """Create enterprise tenant."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{IDENTITY_URL}/v1/tenants",
            json={
                "id": tenant_id,
                "name": "Enterprise Corp - 50 Synthetic Workers",
                "plan_tier": "enterprise",
                "kms_key_id": f"kms-key-{tenant_id}",
                "region_preference": "us-east-1",
                "metadata": {
                    "test_run": datetime.utcnow().isoformat(),
                    "test_type": "50_workers_enterprise",
                    "total_workers": 50,
                    "departments": 6
                }
            },
            headers={"X-Tenant-ID": tenant_id}
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create tenant: {response.status_code} - {response.text}")

        return response.json()


async def worker_solve_problem(
    worker_id: str,
    worker_name: str,
    department: str,
    task_description: str,
    tenant_id: str,
    worker_focus: str
) -> Dict[str, Any]:
    """
    Simulate a synthetic worker solving a problem:
    1. Search mycelial network for related knowledge
    2. Solve the problem
    3. Broadcast solution to network
    4. Store in long-term memory
    """

    result = {
        "worker_id": worker_id,
        "worker_name": worker_name,
        "department": department,
        "task": task_description,
        "timestamp": datetime.utcnow().isoformat()
    }

    print(f"\n{'─'*80}")
    print(f"🤖 [{department}] {worker_name}")
    print(f"   Worker ID: {worker_id}")
    print(f"   Task: {task_description}")
    print(f"{'─'*80}")

    # ========================================
    # Phase 1: Search Mycelial Network
    # ========================================
    query_embedding = generate_embedding(task_description + " " + worker_focus)

    async with httpx.AsyncClient() as client:
        search_response = await client.post(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal:search",
            json={
                "embedding": query_embedding,
                "top_k": 5,
                "min_quality": 0.6
            },
            headers={"X-Tenant-ID": tenant_id},
            timeout=10.0
        )

        past_knowledge = []
        if search_response.status_code == 200:
            search_results = search_response.json()
            past_knowledge = search_results.get("results", [])

            if past_knowledge:
                print(f"\n🔍 Found {len(past_knowledge)} relevant memories from other workers:")
                for i, memory in enumerate(past_knowledge[:3], 1):  # Show top 3
                    source_agent = memory.get('agent_id', 'unknown')
                    source_dept = source_agent.split('-')[0] if '-' in source_agent else 'unknown'
                    memory_content = memory.get('content', {})
                    solution_summary = memory_content.get('solution_summary', 'N/A')
                    similarity = memory.get('similarity', 0)
                    quality = memory.get('quality', 0)

                    print(f"   {i}. From {source_dept}: {solution_summary[:70]}...")
                    print(f"      Similarity: {similarity:.3f}, Quality: {quality:.2f}")

                result["knowledge_found"] = len(past_knowledge)
                result["knowledge_sources"] = [
                    {
                        "from_agent": m.get("agent_id"),
                        "similarity": m.get("similarity"),
                        "summary": m.get("content", {}).get("solution_summary", "N/A")[:100]
                    }
                    for m in past_knowledge[:3]
                ]
            else:
                print(f"\n🔍 No relevant past knowledge found - solving from scratch")
                result["knowledge_found"] = 0

    # ========================================
    # Phase 2: Solve Problem
    # ========================================
    # Generate realistic solution based on department and task
    solution = generate_realistic_solution(department, task_description, past_knowledge)

    print(f"\n💡 Solution:")
    for line in solution["summary"].split('\n'):
        if line.strip():
            print(f"   {line}")

    result["solution"] = solution

    # ========================================
    # Phase 3: Broadcast to Network
    # ========================================
    broadcast_summary = f"[{department}] {solution['summary'].split('.')[0]}"
    broadcast_embedding = generate_embedding(broadcast_summary + " " + task_description)

    async with httpx.AsyncClient() as client:
        broadcast_response = await client.post(
            f"{ROUTER_URL}/v1/nutrients:broadcast",
            json={
                "summary": broadcast_summary,
                "embedding": broadcast_embedding,
                "snippets": [solution["summary"][:300]],
                "tool_hints": [department, solution.get("category", "general")],
                "sensitivity": "internal",
                "max_hops": 3,
                "ttl_sec": 3600,  # 1 hour
                "quota_cost": 1.0
            },
            headers={"X-Tenant-ID": tenant_id},
            timeout=10.0
        )

        if broadcast_response.status_code in [200, 201]:
            print(f"\n📡 Broadcast successful - knowledge now available to all workers")
            result["broadcast_success"] = True
        else:
            print(f"\n⚠️  Broadcast failed: {broadcast_response.status_code}")
            result["broadcast_success"] = False

    # ========================================
    # Phase 4: Store in Hyphal Memory
    # ========================================
    async with httpx.AsyncClient() as client:
        memory_response = await client.post(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
            json={
                "agent_id": worker_id,
                "kind": "solution",
                "content": {
                    "task": task_description,
                    "solution_summary": solution["summary"],
                    "department": department,
                    "worker_name": worker_name,
                    "category": solution.get("category"),
                    "leveraged_knowledge": len(past_knowledge) > 0
                },
                "embedding": broadcast_embedding,
                "quality": 0.8 if len(past_knowledge) > 0 else 0.7,
                "sensitivity": "internal",
                "metadata": {
                    "department": department,
                    "worker_id": worker_id,
                    "knowledge_reused": len(past_knowledge) > 0
                }
            },
            headers={"X-Tenant-ID": tenant_id},
            timeout=10.0
        )

        if memory_response.status_code in [200, 201]:
            memory_data = memory_response.json()
            print(f"💾 Stored in permanent memory: {memory_data.get('id')}")
            result["memory_stored"] = True
        else:
            print(f"⚠️  Memory storage failed: {memory_response.status_code}")
            result["memory_stored"] = False

    return result


def generate_realistic_solution(department: str, task: str, past_knowledge: List[Dict]) -> Dict[str, Any]:
    """Generate realistic solution based on department and task."""

    solutions = {
        "engineering": {
            "Fix production bug": {
                "summary": "Fixed bug by adding null check in payment processor. Added unit tests. Deployed to production with rollback plan.",
                "category": "bug_fix"
            },
            "Optimize": {
                "summary": "Optimized query by adding index on user_id column. Reduced response time from 2.5s to 180ms. Added query monitoring.",
                "category": "performance"
            },
            "Implement": {
                "summary": "Implemented new API endpoint with OpenAPI spec. Added request validation, rate limiting, and comprehensive tests.",
                "category": "feature"
            },
            "security": {
                "summary": "Fixed XSS vulnerability by sanitizing user input. Updated dependencies. Scheduled security audit.",
                "category": "security"
            }
        },
        "customer_support": {
            "unable to login": {
                "summary": "Resolved login issue caused by expired session cookies. Created KB article. Identified browser compatibility issue.",
                "category": "troubleshooting"
            },
            "Integration": {
                "summary": "Fixed Salesforce sync by refreshing OAuth token. Documented auth flow. Recommended webhook monitoring.",
                "category": "integration"
            },
            "Billing": {
                "summary": "Resolved billing discrepancy - found duplicate charge. Issued refund. Updated billing validation logic.",
                "category": "billing"
            }
        },
        "sales_marketing": {
            "demo": {
                "summary": "Prepared enterprise demo showcasing SSO, custom branding, and analytics. Created ROI calculator showing 40% time savings.",
                "category": "sales"
            },
            "conversion": {
                "summary": "Analyzed conversion drop - identified slow page load. Optimized images, reduced JS bundle size. A/B testing new CTA.",
                "category": "growth"
            },
            "case study": {
                "summary": "Created case study showing 10x ROI for enterprise customer. Highlighted team productivity gains and cost savings.",
                "category": "marketing"
            }
        },
        "finance_operations": {
            "Reconcile": {
                "summary": "Reconciled revenue - identified timing difference in Stripe webhooks. Automated reconciliation process going forward.",
                "category": "accounting"
            },
            "variance": {
                "summary": "Investigated cost variance - found auto-scaling issue in staging environment. Implemented cost monitoring alerts.",
                "category": "financial_analysis"
            },
            "forecast": {
                "summary": "Prepared forecast model with revenue projections based on pipeline and churn trends. 95% confidence intervals.",
                "category": "planning"
            }
        },
        "hr_legal": {
            "Review": {
                "summary": "Reviewed contract - negotiated IP ownership clause. Ensured compliance with employment laws. Approved for signature.",
                "category": "legal"
            },
            "GDPR": {
                "summary": "Implemented GDPR deletion workflow. Automated data export. Updated privacy policy and DPA templates.",
                "category": "compliance"
            },
            "hiring": {
                "summary": "Sourced 15 qualified candidates for engineering role. Scheduled technical screens. Average time-to-interview: 5 days.",
                "category": "recruiting"
            }
        },
        "product_design": {
            "Analyze user feedback": {
                "summary": "Analyzed 250 user feedback submissions. Top request: bulk export (mentioned 47 times). Created prioritized roadmap.",
                "category": "product_management"
            },
            "Design": {
                "summary": "Designed mobile onboarding with 3-step flow. Prototype tested with 8 users. Reduced time-to-value from 15min to 4min.",
                "category": "ux_design"
            },
            "usability": {
                "summary": "Conducted usability test with 12 users. Found 3 critical issues in checkout. Recommended 5 UX improvements.",
                "category": "user_research"
            }
        }
    }

    # Match task to solution template
    dept_solutions = solutions.get(department, {})
    for keyword, solution_template in dept_solutions.items():
        if keyword.lower() in task.lower():
            # If past knowledge exists, enhance the solution
            if past_knowledge:
                solution_template["summary"] += f" (Leveraged insights from {len(past_knowledge)} similar cases)"
            return solution_template

    # Default solution
    return {
        "summary": f"Completed task: {task[:50]}... Documented solution and shared findings with team.",
        "category": "general"
    }


async def analyze_knowledge_sharing(tenant_id: str, all_results: List[Dict]) -> Dict[str, Any]:
    """
    Analyze how knowledge was shared across workers and departments.
    """

    print(f"\n\n{'='*80}")
    print(f"📊 KNOWLEDGE SHARING ANALYSIS")
    print(f"{'='*80}")

    analysis = {
        "total_workers": len(all_results),
        "total_tasks": len(all_results),
        "knowledge_sharing": {
            "workers_found_knowledge": 0,
            "workers_solved_from_scratch": 0,
            "total_knowledge_reuse_instances": 0,
            "cross_department_sharing": []
        },
        "by_department": defaultdict(lambda: {
            "tasks_completed": 0,
            "knowledge_found": 0,
            "broadcasts_sent": 0,
            "memories_stored": 0
        })
    }

    # Analyze each worker's results
    for result in all_results:
        dept = result["department"]
        knowledge_found = result.get("knowledge_found", 0)

        analysis["by_department"][dept]["tasks_completed"] += 1

        if knowledge_found > 0:
            analysis["knowledge_sharing"]["workers_found_knowledge"] += 1
            analysis["knowledge_sharing"]["total_knowledge_reuse_instances"] += knowledge_found
            analysis["by_department"][dept]["knowledge_found"] += knowledge_found

            # Track cross-department sharing
            for source in result.get("knowledge_sources", []):
                source_agent = source.get("from_agent", "")
                source_dept = source_agent.split('-')[0] if '-' in source_agent else 'unknown'

                if source_dept != dept:
                    analysis["knowledge_sharing"]["cross_department_sharing"].append({
                        "from_dept": source_dept,
                        "to_dept": dept,
                        "to_worker": result["worker_id"],
                        "task": result["task"][:60],
                        "similarity": source.get("similarity", 0)
                    })
        else:
            analysis["knowledge_sharing"]["workers_solved_from_scratch"] += 1

        if result.get("broadcast_success"):
            analysis["by_department"][dept]["broadcasts_sent"] += 1

        if result.get("memory_stored"):
            analysis["by_department"][dept]["memories_stored"] += 1

    # Calculate knowledge reuse rate
    total_workers = len(all_results)
    if total_workers > 0:
        analysis["knowledge_sharing"]["reuse_rate"] = (
            analysis["knowledge_sharing"]["workers_found_knowledge"] / total_workers
        ) * 100

    # Print analysis
    print(f"\n📈 Overall Statistics:")
    print(f"   Total Workers: {analysis['total_workers']}")
    print(f"   Workers Who Found Relevant Knowledge: {analysis['knowledge_sharing']['workers_found_knowledge']}")
    print(f"   Workers Who Solved From Scratch: {analysis['knowledge_sharing']['workers_solved_from_scratch']}")
    print(f"   Knowledge Reuse Rate: {analysis['knowledge_sharing']['reuse_rate']:.1f}%")
    print(f"   Total Knowledge Reuse Instances: {analysis['knowledge_sharing']['total_knowledge_reuse_instances']}")

    print(f"\n🏢 By Department:")
    for dept, stats in sorted(analysis["by_department"].items()):
        print(f"\n   {DEPARTMENTS[dept]['name']}:")
        print(f"      Tasks Completed: {stats['tasks_completed']}")
        print(f"      Knowledge Found: {stats['knowledge_found']}")
        print(f"      Broadcasts Sent: {stats['broadcasts_sent']}")
        print(f"      Memories Stored: {stats['memories_stored']}")

    # Show cross-department knowledge sharing
    cross_dept = analysis["knowledge_sharing"]["cross_department_sharing"]
    if cross_dept:
        print(f"\n🔄 Cross-Department Knowledge Sharing ({len(cross_dept)} instances):")
        print(f"\n   Top Examples:")

        # Group by department pair
        dept_pairs = defaultdict(list)
        for sharing in cross_dept:
            key = f"{sharing['from_dept']} → {sharing['to_dept']}"
            dept_pairs[key].append(sharing)

        # Show top 10 examples
        shown = 0
        for pair, sharings in sorted(dept_pairs.items(), key=lambda x: len(x[1]), reverse=True):
            if shown >= 10:
                break

            example = sharings[0]
            count = len(sharings)

            print(f"\n   {pair} ({count} time{'s' if count > 1 else ''}):")
            print(f"      Task: {example['task']}")
            print(f"      Worker: {example['to_worker']}")
            print(f"      Similarity: {example['similarity']:.3f}")

            shown += 1

    return analysis


async def run_enterprise_simulation(tenant_id: str, num_workers_per_dept: Dict[str, int] = None):
    """
    Run enterprise simulation with 50 workers across 6 departments.

    Workers execute tasks in waves to simulate realistic knowledge accumulation.
    """

    print(f"\n{'='*80}")
    print(f"🏢 ENTERPRISE SIMULATION: 50 Synthetic Workers")
    print(f"{'='*80}")

    all_results = []

    # Execute in 3 waves to build up knowledge over time
    waves = [
        {"name": "Wave 1: Early Morning (20 workers)", "workers": 20},
        {"name": "Wave 2: Mid Morning (15 workers)", "workers": 15},
        {"name": "Wave 3: Afternoon (15 workers)", "workers": 15}
    ]

    worker_pool = []
    for dept_id, dept_data in DEPARTMENTS.items():
        for worker in dept_data["workers"]:
            tasks = dept_data["common_tasks"]
            worker_pool.append({
                "department": dept_id,
                "worker": worker,
                "task": random.choice(tasks)
            })

    # Shuffle for realistic distribution
    random.shuffle(worker_pool)

    worker_index = 0

    for wave in waves:
        print(f"\n\n{'▶'*40}")
        print(f"🌊 {wave['name']}")
        print(f"{'▶'*40}")

        wave_workers = []

        for _ in range(min(wave['workers'], len(worker_pool) - worker_index)):
            if worker_index >= len(worker_pool):
                break

            worker_data = worker_pool[worker_index]
            wave_workers.append(worker_data)
            worker_index += 1

        # Execute workers in parallel (batches of 5)
        batch_size = 5
        for i in range(0, len(wave_workers), batch_size):
            batch = wave_workers[i:i+batch_size]

            tasks = []
            for worker_data in batch:
                dept = worker_data["department"]
                worker = worker_data["worker"]
                task = worker_data["task"]

                task_coro = worker_solve_problem(
                    worker_id=worker["id"],
                    worker_name=worker["name"],
                    department=dept,
                    task_description=task,
                    tenant_id=tenant_id,
                    worker_focus=worker["focus"]
                )
                tasks.append(task_coro)

            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"⚠️  Worker error: {result}")
                else:
                    all_results.append(result)

            # Small delay between batches
            await asyncio.sleep(1)

        # Delay between waves to allow knowledge to propagate
        if wave != waves[-1]:
            print(f"\n⏳ Waiting for knowledge to propagate across network...")
            await asyncio.sleep(2)

    return all_results


# ============================================================
# Main Test
# ============================================================
async def main():
    """Run 50-worker enterprise simulation."""

    print(f"\n{'🧬'*40}")
    print(f"QILBEE MYCELIAL NETWORK - Enterprise Simulation")
    print(f"50 Synthetic Workers Across 6 Departments")
    print(f"{'🧬'*40}")

    tenant_id = f"enterprise-50workers-{uuid.uuid4().hex[:8]}"

    try:
        # ========================================
        # Setup
        # ========================================
        print(f"\n📋 Creating enterprise tenant: {tenant_id}")
        tenant = await create_tenant(tenant_id)
        print(f"✅ Tenant created: {tenant.get('id')}")

        # ========================================
        # Run Simulation
        # ========================================
        start_time = datetime.utcnow()
        all_results = await run_enterprise_simulation(tenant_id)
        end_time = datetime.utcnow()

        duration = (end_time - start_time).total_seconds()

        # ========================================
        # Analyze Results
        # ========================================
        await asyncio.sleep(2)  # Allow final propagation
        analysis = await analyze_knowledge_sharing(tenant_id, all_results)

        # ========================================
        # Generate Final Report
        # ========================================
        report = {
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": duration,
            "workers": {
                "total": len(all_results),
                "by_department": {
                    dept: len([r for r in all_results if r["department"] == dept])
                    for dept in DEPARTMENTS.keys()
                }
            },
            "knowledge_sharing": analysis["knowledge_sharing"],
            "by_department": dict(analysis["by_department"]),
            "success": len(all_results) == 50
        }

        # Save report
        report_filename = f"enterprise_50workers_report_{tenant_id}.json"
        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # ========================================
        # Final Summary
        # ========================================
        print(f"\n\n{'='*80}")
        print(f"🎉 SIMULATION COMPLETE")
        print(f"{'='*80}")

        print(f"\n⏱️  Duration: {duration:.1f} seconds")
        print(f"🤖 Workers Executed: {len(all_results)}/50")
        print(f"📊 Knowledge Reuse Rate: {analysis['knowledge_sharing']['reuse_rate']:.1f}%")
        print(f"🔄 Cross-Department Sharing: {len(analysis['knowledge_sharing']['cross_department_sharing'])} instances")

        print(f"\n💾 Report saved to: {report_filename}")

        print(f"\n{'='*80}")
        if report["success"]:
            print(f"✅ SUCCESS - All 50 workers completed their tasks!")
        else:
            print(f"⚠️  PARTIAL - {len(all_results)}/50 workers completed")
        print(f"{'='*80}\n")

        return report["success"]

    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
