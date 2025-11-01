"""
Drug Research Collaboration: AI Agents in Pharmaceutical Research

This test simulates a realistic pharmaceutical research environment where
multiple AI research assistants across different labs and specializations
collaborate on drug discovery and development through the mycelial network.

Departments:
- Computational Chemistry (molecular modeling, docking, QSAR)
- Biological Screening (in vitro, in vivo, toxicology)
- Clinical Research (trial design, patient recruitment, data analysis)
- Regulatory Affairs (FDA submissions, compliance, documentation)
- Bioinformatics (genomics, proteomics, pathway analysis)
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
# Research Labs & Scientists (AI Agents)
# ============================================================

RESEARCH_LABS = {
    "computational_chemistry": {
        "name": "Computational Chemistry Lab",
        "researchers": [
            {"id": "chem-molmod-001", "name": "Dr. Sarah Chen", "focus": "Molecular modeling, protein-ligand docking"},
            {"id": "chem-molmod-002", "name": "Dr. James Kumar", "focus": "QSAR analysis, pharmacophore modeling"},
            {"id": "chem-synthesis-001", "name": "Dr. Maria Rodriguez", "focus": "Synthetic chemistry, compound libraries"},
            {"id": "chem-qsar-001", "name": "Dr. Robert Li", "focus": "Machine learning QSAR, property prediction"},
        ],
        "research_tasks": [
            "Identify novel kinase inhibitors for cancer therapy",
            "Optimize lead compound ADME properties",
            "Predict binding affinity for target protein",
            "Design compound library for HTS screening",
            "Analyze structure-activity relationships for series",
            "Perform molecular docking against PDB structure 6XYZ",
            "Predict toxicity profile for lead compound",
            "Optimize lipophilicity without losing potency"
        ]
    },
    "biological_screening": {
        "name": "Biological Screening Lab",
        "researchers": [
            {"id": "bio-invitro-001", "name": "Dr. Emily Watson", "focus": "Cell-based assays, IC50 determination"},
            {"id": "bio-invitro-002", "name": "Dr. Michael Zhang", "focus": "Enzyme assays, kinetic analysis"},
            {"id": "bio-invivo-001", "name": "Dr. Linda Martinez", "focus": "Animal models, pharmacokinetics"},
            {"id": "bio-tox-001", "name": "Dr. David Johnson", "focus": "Toxicology, safety assessment"},
        ],
        "research_tasks": [
            "Screen compound library against cancer cell lines",
            "Determine IC50 for lead compounds in HeLa cells",
            "Assess PK profile in mouse xenograft model",
            "Evaluate hepatotoxicity in rat liver microsomes",
            "Measure target engagement in cells using CETSA",
            "Perform selectivity screen against kinome panel",
            "Analyze metabolic stability in liver microsomes",
            "Test compounds for hERG channel inhibition"
        ]
    },
    "clinical_research": {
        "name": "Clinical Research",
        "researchers": [
            {"id": "clin-design-001", "name": "Dr. Patricia O'Brien", "focus": "Clinical trial design, biostatistics"},
            {"id": "clin-recruit-001", "name": "Dr. Thomas Anderson", "focus": "Patient recruitment, inclusion criteria"},
            {"id": "clin-data-001", "name": "Dr. Jennifer Lee", "focus": "Clinical data analysis, endpoints"},
        ],
        "research_tasks": [
            "Design Phase II trial for kinase inhibitor",
            "Analyze interim efficacy data from ongoing trial",
            "Identify optimal patient population for trial",
            "Calculate sample size for Phase III study",
            "Review adverse events from Phase I trial",
            "Design adaptive trial protocol",
            "Analyze biomarker stratification strategy"
        ]
    },
    "regulatory_affairs": {
        "name": "Regulatory Affairs",
        "researchers": [
            {"id": "reg-fda-001", "name": "Dr. Richard Brown", "focus": "FDA submissions, IND applications"},
            {"id": "reg-compliance-001", "name": "Dr. Susan Miller", "focus": "GxP compliance, quality documentation"},
        ],
        "research_tasks": [
            "Prepare IND application for new compound",
            "Review CMC section for regulatory submission",
            "Address FDA clinical hold concerns",
            "Prepare briefing document for FDA meeting",
            "Ensure GMP compliance for manufacturing",
            "Review nonclinical safety data package"
        ]
    },
    "bioinformatics": {
        "name": "Bioinformatics Lab",
        "researchers": [
            {"id": "bioinfo-genomics-001", "name": "Dr. Kevin Park", "focus": "Genomics, target identification"},
            {"id": "bioinfo-proteomics-001", "name": "Dr. Rachel Green", "focus": "Proteomics, pathway analysis"},
            {"id": "bioinfo-ai-001", "name": "Dr. Alex Thompson", "focus": "AI/ML for drug discovery"},
        ],
        "research_tasks": [
            "Identify genetic biomarkers for patient stratification",
            "Analyze RNA-seq data from treated cells",
            "Perform pathway enrichment analysis",
            "Build ML model to predict clinical response",
            "Identify novel drug targets from GWAS data",
            "Analyze proteomics data for mechanism of action"
        ]
    }
}


# ============================================================
# Drug Candidates Being Researched
# ============================================================

DRUG_CANDIDATES = [
    {
        "id": "QMN-101",
        "name": "Kinase Inhibitor Alpha",
        "target": "EGFR",
        "indication": "Non-small cell lung cancer",
        "stage": "Lead Optimization"
    },
    {
        "id": "QMN-201",
        "name": "Kinase Inhibitor Beta",
        "target": "ALK",
        "indication": "ALK+ lung cancer",
        "stage": "Preclinical"
    },
    {
        "id": "QMN-301",
        "name": "Immunotherapy Candidate",
        "target": "PD-L1",
        "indication": "Melanoma",
        "stage": "Phase I"
    }
]


# ============================================================
# Helper Functions
# ============================================================

def generate_embedding(text: str, dimensions: int = 1536) -> List[float]:
    """Generate deterministic embedding from text."""
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()

    embedding = []
    for i in range(dimensions):
        byte_idx = i % len(hash_bytes)
        value = hash_bytes[byte_idx] / 255.0
        value = math.sin(value * math.pi * (i / dimensions)) * 0.5 + 0.5
        embedding.append(value)

    magnitude = math.sqrt(sum(x**2 for x in embedding))
    return [x / magnitude for x in embedding]


async def create_tenant(tenant_id: str) -> Dict[str, Any]:
    """Create pharmaceutical research tenant."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{IDENTITY_URL}/v1/tenants",
            json={
                "id": tenant_id,
                "name": "Global Pharma Research - Drug Discovery Collaboration",
                "plan_tier": "enterprise",
                "kms_key_id": f"kms-key-{tenant_id}",
                "region_preference": "us-east-1",
                "metadata": {
                    "test_run": datetime.utcnow().isoformat(),
                    "test_type": "drug_research_collaboration",
                    "research_focus": "oncology_drug_discovery",
                    "total_researchers": sum(len(lab["researchers"]) for lab in RESEARCH_LABS.values())
                }
            },
            headers={"X-Tenant-ID": tenant_id}
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create tenant: {response.status_code}")

        return response.json()


async def researcher_conduct_study(
    researcher_id: str,
    researcher_name: str,
    lab: str,
    research_task: str,
    drug_candidate: Dict[str, Any],
    tenant_id: str,
    focus: str
) -> Dict[str, Any]:
    """
    Simulate a pharmaceutical researcher conducting a study:
    1. Search mycelial network for related research
    2. Conduct the study
    3. Broadcast findings to network
    4. Store in research database (hyphal memory)
    """

    result = {
        "researcher_id": researcher_id,
        "researcher_name": researcher_name,
        "lab": lab,
        "research_task": research_task,
        "drug_candidate": drug_candidate["id"],
        "timestamp": datetime.utcnow().isoformat()
    }

    print(f"\n{'━'*80}")
    print(f"🔬 [{lab}] {researcher_name}")
    print(f"   Researcher ID: {researcher_id}")
    print(f"   Drug Candidate: {drug_candidate['name']} ({drug_candidate['id']})")
    print(f"   Target: {drug_candidate['target']} - {drug_candidate['indication']}")
    print(f"   Task: {research_task}")
    print(f"{'━'*80}")

    # ========================================
    # Phase 1: Search Mycelial Network for Related Research
    # ========================================
    search_query = f"{research_task} {drug_candidate['target']} {drug_candidate['indication']}"
    query_embedding = generate_embedding(search_query + " " + focus)

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

        past_research = []
        if search_response.status_code == 200:
            search_results = search_response.json()
            past_research = search_results.get("results", [])

            if past_research:
                print(f"\n📚 Found {len(past_research)} related research findings:")
                for i, research in enumerate(past_research[:3], 1):
                    source_researcher = research.get('agent_id', 'unknown')
                    source_lab = source_researcher.split('-')[0] if '-' in source_researcher else 'unknown'
                    research_content = research.get('content', {})
                    finding = research_content.get('key_finding', 'N/A')
                    similarity = research.get('similarity', 0)
                    quality = research.get('quality', 0)

                    print(f"   {i}. From {source_lab} lab: {finding[:80]}...")
                    print(f"      Similarity: {similarity:.3f}, Quality: {quality:.2f}")

                result["prior_research_found"] = len(past_research)
                result["prior_research_sources"] = [
                    {
                        "from_researcher": r.get("agent_id"),
                        "similarity": r.get("similarity"),
                        "finding": r.get("content", {}).get("key_finding", "N/A")[:100]
                    }
                    for r in past_research[:3]
                ]
            else:
                print(f"\n📚 No prior research found - conducting novel study")
                result["prior_research_found"] = 0

    # ========================================
    # Phase 2: Conduct Research
    # ========================================
    findings = generate_research_findings(
        lab, research_task, drug_candidate, past_research
    )

    print(f"\n🧪 Research Findings:")
    print(f"   {findings['key_finding']}")
    if findings.get("data"):
        for key, value in findings["data"].items():
            print(f"   • {key}: {value}")

    result["findings"] = findings

    # ========================================
    # Phase 3: Broadcast to Research Network
    # ========================================
    broadcast_summary = f"[{lab}] {findings['key_finding']}"
    broadcast_embedding = generate_embedding(broadcast_summary + " " + research_task)

    async with httpx.AsyncClient() as client:
        broadcast_response = await client.post(
            f"{ROUTER_URL}/v1/nutrients:broadcast",
            json={
                "summary": broadcast_summary,
                "embedding": broadcast_embedding,
                "snippets": [findings["key_finding"][:300]],
                "tool_hints": [
                    lab,
                    drug_candidate["target"],
                    drug_candidate["indication"],
                    "pharmaceutical_research"
                ],
                "sensitivity": "confidential",  # Research data is confidential
                "max_hops": 5,
                "ttl_sec": 86400,  # 24 hours
                "quota_cost": 1.0
            },
            headers={"X-Tenant-ID": tenant_id},
            timeout=10.0
        )

        if broadcast_response.status_code in [200, 201]:
            print(f"\n📡 Research findings broadcast to network")
            result["broadcast_success"] = True
        else:
            print(f"\n⚠️  Broadcast failed: {broadcast_response.status_code}")
            result["broadcast_success"] = False

    # ========================================
    # Phase 4: Store in Research Database
    # ========================================
    async with httpx.AsyncClient() as client:
        memory_response = await client.post(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
            json={
                "agent_id": researcher_id,
                "kind": "research_finding",
                "content": {
                    "research_task": research_task,
                    "drug_candidate": drug_candidate["id"],
                    "target": drug_candidate["target"],
                    "indication": drug_candidate["indication"],
                    "key_finding": findings["key_finding"],
                    "data": findings.get("data", {}),
                    "researcher_name": researcher_name,
                    "lab": lab,
                    "built_on_prior_research": len(past_research) > 0
                },
                "embedding": broadcast_embedding,
                "quality": 0.9 if len(past_research) > 0 else 0.75,
                "sensitivity": "confidential",
                "metadata": {
                    "lab": lab,
                    "researcher_id": researcher_id,
                    "drug_candidate": drug_candidate["id"],
                    "research_stage": drug_candidate["stage"]
                }
            },
            headers={"X-Tenant-ID": tenant_id},
            timeout=10.0
        )

        if memory_response.status_code in [200, 201]:
            memory_data = memory_response.json()
            print(f"💾 Stored in research database: {memory_data.get('id')}")
            result["stored_in_database"] = True
        else:
            print(f"⚠️  Storage failed: {memory_response.status_code}")
            result["stored_in_database"] = False

    return result


def generate_research_findings(
    lab: str,
    task: str,
    drug_candidate: Dict[str, Any],
    past_research: List[Dict]
) -> Dict[str, Any]:
    """Generate realistic research findings based on lab and task."""

    findings_templates = {
        "computational_chemistry": {
            "docking": {
                "key_finding": f"Molecular docking shows {drug_candidate['id']} binds {drug_candidate['target']} with -9.2 kcal/mol binding energy",
                "data": {
                    "binding_energy": "-9.2 kcal/mol",
                    "key_interactions": "H-bonds with Asp855, Met793",
                    "docking_score": "8.7"
                }
            },
            "QSAR": {
                "key_finding": f"QSAR model predicts IC50 = 12 nM for {drug_candidate['id']} against {drug_candidate['target']}",
                "data": {
                    "predicted_IC50": "12 nM",
                    "model_R2": "0.87",
                    "confidence_interval": "8-18 nM"
                }
            },
            "ADME": {
                "key_finding": f"Lead optimization improved oral bioavailability to 45% while maintaining potency",
                "data": {
                    "oral_bioavailability": "45%",
                    "half_life": "6.2 hours",
                    "CYP_inhibition": "Minimal"
                }
            }
        },
        "biological_screening": {
            "IC50": {
                "key_finding": f"{drug_candidate['id']} shows IC50 = 8.5 nM in {drug_candidate['indication']} cells",
                "data": {
                    "IC50": "8.5 nM",
                    "cell_line": "H1975 (EGFR mutant)",
                    "selectivity": "100x vs wild-type"
                }
            },
            "PK": {
                "key_finding": f"Pharmacokinetic study shows excellent exposure with Cmax = 1.2 μM at 50 mg/kg",
                "data": {
                    "Cmax": "1.2 μM",
                    "AUC": "8.5 μM·h",
                    "half_life": "5.8 hours",
                    "tumor_penetration": "Good"
                }
            },
            "toxicity": {
                "key_finding": f"Toxicity assessment shows no hepatotoxicity up to 500 mg/kg in rats",
                "data": {
                    "MTD": ">500 mg/kg",
                    "liver_enzymes": "Normal",
                    "histopathology": "No adverse findings"
                }
            }
        },
        "clinical_research": {
            "trial_design": {
                "key_finding": f"Phase II trial designed: 120 patients, primary endpoint ORR, enriched for {drug_candidate['target']}+ population",
                "data": {
                    "sample_size": "120 patients",
                    "primary_endpoint": "Objective Response Rate",
                    "enrichment": f"{drug_candidate['target']}+ biomarker",
                    "expected_ORR": "35%"
                }
            },
            "efficacy": {
                "key_finding": f"Interim analysis shows ORR = 38% (95% CI: 28-48%) in biomarker+ patients",
                "data": {
                    "ORR": "38%",
                    "CI_95": "28-48%",
                    "median_PFS": "8.2 months",
                    "patients_enrolled": "85"
                }
            }
        },
        "regulatory_affairs": {
            "IND": {
                "key_finding": f"IND application prepared with complete nonclinical package for {drug_candidate['id']}",
                "data": {
                    "status": "Ready for submission",
                    "nonclinical_studies": "Complete",
                    "CMC_documentation": "GMP-compliant"
                }
            },
            "FDA_response": {
                "key_finding": f"FDA cleared clinical hold after addressing manufacturing concerns",
                "data": {
                    "hold_reason": "CMC clarification",
                    "resolution": "Additional stability data provided",
                    "clearance_date": "2025-10-15"
                }
            }
        },
        "bioinformatics": {
            "biomarker": {
                "key_finding": f"Identified {drug_candidate['target']} mutation signature predicting 2.5x better response",
                "data": {
                    "biomarker": f"{drug_candidate['target']} L858R/T790M",
                    "HR_PFS": "0.42 (p<0.001)",
                    "predictive_accuracy": "78%"
                }
            },
            "mechanism": {
                "key_finding": f"Proteomics reveals {drug_candidate['id']} inhibits downstream MAPK/ERK signaling",
                "data": {
                    "pathways_affected": "MAPK/ERK, PI3K/AKT",
                    "phospho_ERK_reduction": "85%",
                    "validation": "Western blot confirmed"
                }
            }
        }
    }

    # Select appropriate finding based on lab and task
    lab_findings = findings_templates.get(lab, {})

    for keyword, template in lab_findings.items():
        if keyword.lower() in task.lower():
            finding = template.copy()
            if past_research:
                finding["key_finding"] += f" (Validated with {len(past_research)} prior studies)"
            return finding

    # Default finding
    return {
        "key_finding": f"Completed {task} for {drug_candidate['id']} - positive results",
        "data": {"status": "completed", "outcome": "positive"}
    }


async def analyze_research_collaboration(
    tenant_id: str,
    all_results: List[Dict]
) -> Dict[str, Any]:
    """Analyze how research knowledge was shared across labs."""

    print(f"\n\n{'='*80}")
    print(f"📊 RESEARCH COLLABORATION ANALYSIS")
    print(f"{'='*80}")

    analysis = {
        "total_researchers": len(all_results),
        "total_studies": len(all_results),
        "knowledge_sharing": {
            "researchers_found_prior_work": 0,
            "researchers_conducted_novel_studies": 0,
            "total_knowledge_reuse": 0,
            "cross_lab_collaboration": []
        },
        "by_lab": defaultdict(lambda: {
            "studies_completed": 0,
            "prior_research_found": 0,
            "broadcasts_sent": 0,
            "stored_in_database": 0
        }),
        "by_drug_candidate": defaultdict(lambda: {
            "studies_completed": 0,
            "labs_involved": set(),
            "researchers_involved": set()
        })
    }

    # Analyze results
    for result in all_results:
        lab = result["lab"]
        drug_id = result["drug_candidate"]
        prior_research = result.get("prior_research_found", 0)

        analysis["by_lab"][lab]["studies_completed"] += 1

        if prior_research > 0:
            analysis["knowledge_sharing"]["researchers_found_prior_work"] += 1
            analysis["knowledge_sharing"]["total_knowledge_reuse"] += prior_research
            analysis["by_lab"][lab]["prior_research_found"] += prior_research

            # Track cross-lab collaboration
            for source in result.get("prior_research_sources", []):
                source_researcher = source.get("from_researcher", "")
                source_lab = source_researcher.split('-')[0] if '-' in source_researcher else 'unknown'

                if source_lab != lab:
                    analysis["knowledge_sharing"]["cross_lab_collaboration"].append({
                        "from_lab": source_lab,
                        "to_lab": lab,
                        "to_researcher": result["researcher_id"],
                        "drug_candidate": drug_id,
                        "research_task": result["research_task"][:60],
                        "similarity": source.get("similarity", 0)
                    })
        else:
            analysis["knowledge_sharing"]["researchers_conducted_novel_studies"] += 1

        if result.get("broadcast_success"):
            analysis["by_lab"][lab]["broadcasts_sent"] += 1

        if result.get("stored_in_database"):
            analysis["by_lab"][lab]["stored_in_database"] += 1

        # Track by drug candidate
        analysis["by_drug_candidate"][drug_id]["studies_completed"] += 1
        analysis["by_drug_candidate"][drug_id]["labs_involved"].add(lab)
        analysis["by_drug_candidate"][drug_id]["researchers_involved"].add(result["researcher_id"])

    # Calculate reuse rate
    total = len(all_results)
    if total > 0:
        analysis["knowledge_sharing"]["reuse_rate"] = (
            analysis["knowledge_sharing"]["researchers_found_prior_work"] / total
        ) * 100

    # Print analysis
    print(f"\n📈 Overall Statistics:")
    print(f"   Total Researchers: {analysis['total_researchers']}")
    print(f"   Researchers Who Found Prior Work: {analysis['knowledge_sharing']['researchers_found_prior_work']}")
    print(f"   Researchers Conducting Novel Studies: {analysis['knowledge_sharing']['researchers_conducted_novel_studies']}")
    print(f"   Knowledge Reuse Rate: {analysis['knowledge_sharing']['reuse_rate']:.1f}%")
    print(f"   Total Prior Research References: {analysis['knowledge_sharing']['total_knowledge_reuse']}")

    print(f"\n🔬 By Research Lab:")
    for lab, stats in sorted(analysis["by_lab"].items()):
        lab_name = RESEARCH_LABS[lab]["name"]
        print(f"\n   {lab_name}:")
        print(f"      Studies Completed: {stats['studies_completed']}")
        print(f"      Prior Research Found: {stats['prior_research_found']}")
        print(f"      Findings Broadcast: {stats['broadcasts_sent']}")
        print(f"      Stored in Database: {stats['stored_in_database']}")

    print(f"\n💊 By Drug Candidate:")
    for drug_id, stats in sorted(analysis["by_drug_candidate"].items()):
        drug = next((d for d in DRUG_CANDIDATES if d["id"] == drug_id), None)
        if drug:
            print(f"\n   {drug['name']} ({drug_id}):")
            print(f"      Target: {drug['target']} - {drug['indication']}")
            print(f"      Stage: {drug['stage']}")
            print(f"      Studies Completed: {stats['studies_completed']}")
            print(f"      Labs Involved: {len(stats['labs_involved'])}")
            print(f"      Researchers Involved: {len(stats['researchers_involved'])}")

    # Cross-lab collaboration
    cross_lab = analysis["knowledge_sharing"]["cross_lab_collaboration"]
    if cross_lab:
        print(f"\n🔄 Cross-Lab Collaboration ({len(cross_lab)} instances):")
        print(f"\n   Key Examples:")

        # Group by lab pair
        lab_pairs = defaultdict(list)
        for collab in cross_lab:
            key = f"{collab['from_lab']} → {collab['to_lab']}"
            lab_pairs[key].append(collab)

        # Show examples
        for pair, collabs in sorted(lab_pairs.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            example = collabs[0]
            count = len(collabs)

            from_lab_name = RESEARCH_LABS.get(example['from_lab'], {}).get('name', example['from_lab'])
            to_lab_name = RESEARCH_LABS.get(example['to_lab'], {}).get('name', example['to_lab'])

            print(f"\n   {from_lab_name} → {to_lab_name} ({count} time{'s' if count > 1 else ''}):")
            print(f"      Drug: {example['drug_candidate']}")
            print(f"      Task: {example['research_task']}")
            print(f"      Researcher: {example['to_researcher']}")
            print(f"      Relevance: {example['similarity']:.3f}")

    return analysis


async def run_drug_research_simulation(tenant_id: str):
    """Run pharmaceutical research simulation."""

    print(f"\n{'='*80}")
    print(f"💊 PHARMACEUTICAL RESEARCH SIMULATION")
    print(f"{'='*80}")

    all_results = []

    # Select subset of researchers and assign drug candidates
    research_assignments = []

    for drug in DRUG_CANDIDATES[:2]:  # Focus on 2 drug candidates
        for lab_id, lab_data in RESEARCH_LABS.items():
            # Select 1-2 researchers per lab per drug
            researchers = random.sample(lab_data["researchers"], min(2, len(lab_data["researchers"])))
            tasks = random.sample(lab_data["research_tasks"], len(researchers))

            for researcher, task in zip(researchers, tasks):
                research_assignments.append({
                    "lab": lab_id,
                    "researcher": researcher,
                    "task": task,
                    "drug": drug
                })

    # Shuffle for realistic distribution
    random.shuffle(research_assignments)

    print(f"\n📋 Research Plan:")
    print(f"   Total Studies: {len(research_assignments)}")
    print(f"   Drug Candidates: {len(DRUG_CANDIDATES[:2])}")
    print(f"   Labs Involved: {len(RESEARCH_LABS)}")

    # Execute studies in batches
    batch_size = 3
    for i in range(0, len(research_assignments), batch_size):
        batch = research_assignments[i:i+batch_size]

        tasks = []
        for assignment in batch:
            task_coro = researcher_conduct_study(
                researcher_id=assignment["researcher"]["id"],
                researcher_name=assignment["researcher"]["name"],
                lab=assignment["lab"],
                research_task=assignment["task"],
                drug_candidate=assignment["drug"],
                tenant_id=tenant_id,
                focus=assignment["researcher"]["focus"]
            )
            tasks.append(task_coro)

        # Execute batch
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in batch_results:
            if isinstance(result, Exception):
                print(f"⚠️  Study error: {result}")
            else:
                all_results.append(result)

        # Delay between batches
        await asyncio.sleep(1.5)

    return all_results


# ============================================================
# Main Test
# ============================================================

async def main():
    """Run drug research collaboration test."""

    print(f"\n{'🧬'*40}")
    print(f"QILBEE MYCELIAL NETWORK - Drug Research Collaboration")
    print(f"Pharmaceutical AI Research Assistants")
    print(f"{'🧬'*40}")

    tenant_id = f"pharma-research-{uuid.uuid4().hex[:8]}"

    try:
        # Setup
        print(f"\n📋 Creating pharmaceutical research tenant: {tenant_id}")
        tenant = await create_tenant(tenant_id)
        print(f"✅ Tenant created: {tenant.get('id')}")

        # Run simulation
        start_time = datetime.utcnow()
        all_results = await run_drug_research_simulation(tenant_id)
        end_time = datetime.utcnow()

        duration = (end_time - start_time).total_seconds()

        # Analyze
        await asyncio.sleep(2)
        analysis = await analyze_research_collaboration(tenant_id, all_results)

        # Generate report
        report = {
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": duration,
            "researchers": {
                "total": len(all_results),
                "by_lab": {
                    lab: len([r for r in all_results if r["lab"] == lab])
                    for lab in RESEARCH_LABS.keys()
                }
            },
            "knowledge_sharing": analysis["knowledge_sharing"],
            "by_lab": {k: dict(v) for k, v in analysis["by_lab"].items()},
            "by_drug_candidate": {
                k: {
                    "studies_completed": v["studies_completed"],
                    "labs_involved": len(v["labs_involved"]),
                    "researchers_involved": len(v["researchers_involved"])
                }
                for k, v in analysis["by_drug_candidate"].items()
            },
            "success": len(all_results) > 0
        }

        # Save report
        report_filename = f"drug_research_collaboration_report_{tenant_id}.json"
        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Final summary
        print(f"\n\n{'='*80}")
        print(f"🎉 RESEARCH SIMULATION COMPLETE")
        print(f"{'='*80}")

        print(f"\n⏱️  Duration: {duration:.1f} seconds")
        print(f"🔬 Studies Completed: {len(all_results)}")
        print(f"📊 Knowledge Reuse Rate: {analysis['knowledge_sharing']['reuse_rate']:.1f}%")
        print(f"🔄 Cross-Lab Collaboration: {len(analysis['knowledge_sharing']['cross_lab_collaboration'])} instances")

        print(f"\n💾 Report saved to: {report_filename}")

        print(f"\n{'='*80}")
        if report["success"]:
            print(f"✅ SUCCESS - Research collaboration demonstrated!")
        else:
            print(f"⚠️  PARTIAL - Some studies incomplete")
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
