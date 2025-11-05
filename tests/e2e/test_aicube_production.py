"""
Production Test for Aicube Technology LLC

This test uses the actual Aicube Technology LLC tenant and API key
to validate the production QMN system.
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import List
import hashlib
import math

# Service URLs
BASE_URL = "https://qmn.qube.aicube.ca"
IDENTITY_URL = f"{BASE_URL}/identity"
KEYS_URL = f"{BASE_URL}/keys"
ROUTER_URL = f"{BASE_URL}/router"
HYPHAL_MEMORY_URL = f"{BASE_URL}/memory"

# Aicube Technology LLC Credentials
TENANT_ID = "4b374062-0494-4aad-8b3f-de40f820f1c4"
API_KEY = "qmn_4XY7KzcsajezHRsyisq_BNq1hcp-jHxsk4Lblns4dk0"
COMPANY_NAME = "Aicube Technology LLC"


def generate_embedding(text: str) -> List[float]:
    """Generate deterministic embedding for testing."""
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()

    embedding = []
    for i in range(1536):
        byte_idx = i % len(hash_bytes)
        value = hash_bytes[byte_idx] / 255.0
        value = math.sin(value * math.pi * (i / 1536)) * 0.5 + 0.5
        embedding.append(value)

    # Normalize to unit vector
    magnitude = math.sqrt(sum(x**2 for x in embedding))
    embedding = [x / magnitude for x in embedding]

    return embedding


async def test_tenant_info():
    """Test 1: Verify tenant information."""
    print(f"\n{'='*80}")
    print(f"Test 1: Verifying Tenant Information")
    print(f"{'='*80}\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{IDENTITY_URL}/v1/tenants/{TENANT_ID}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Tenant Found:")
                print(f"   Company: {data.get('name')}")
                print(f"   ID: {data.get('id')}")
                print(f"   Plan: {data.get('plan_tier')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Created: {data.get('created_at')}")
                return True
            else:
                print(f"❌ Failed to fetch tenant: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_nutrient_broadcast():
    """Test 2: Broadcast knowledge to the network."""
    print(f"\n{'='*80}")
    print(f"Test 2: Broadcasting Nutrient")
    print(f"{'='*80}\n")

    headers = {
        "X-API-Key": API_KEY,
        "X-Tenant-ID": TENANT_ID
    }

    knowledge = "Aicube Technology LLC: Testing production QMN deployment with real-world scenario"
    embedding = generate_embedding(knowledge)

    payload = {
        "summary": knowledge,
        "embedding": embedding,
        "snippets": [
            "Production deployment validation",
            "Real-world knowledge sharing test",
            "Enterprise mycelial network testing"
        ],
        "tool_hints": ["production", "validation", "enterprise"],
        "sensitivity": "internal",
        "ttl_sec": 3600,
        "max_hops": 5,
        "metadata": {
            "company": COMPANY_NAME,
            "test_type": "production_validation",
            "timestamp": datetime.now().isoformat()
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{ROUTER_URL}/v1/nutrients:broadcast",
                json=payload,
                headers=headers
            )

            if response.status_code in [200, 201, 202]:
                data = response.json()
                print(f"✅ Broadcast Successful")
                print(f"   Nutrient ID: {data.get('nutrient_id', 'N/A')}")
                print(f"   Summary: {knowledge[:60]}...")
                return True
            else:
                print(f"❌ Broadcast Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_memory_storage():
    """Test 3: Store knowledge in hyphal memory."""
    print(f"\n{'='*80}")
    print(f"Test 3: Storing Knowledge in Hyphal Memory")
    print(f"{'='*80}\n")

    headers = {
        "X-API-Key": API_KEY,
        "X-Tenant-ID": TENANT_ID
    }

    content = {
        "title": "QMN Production Validation",
        "description": "Validating Qilbee Mycelial Network for Aicube Technology LLC",
        "findings": [
            "System is operational",
            "Tenant creation successful",
            "Knowledge broadcasting functional"
        ],
        "timestamp": datetime.now().isoformat()
    }

    embedding = generate_embedding(json.dumps(content))

    payload = {
        "agent_id": "aicube-validator-001",
        "kind": "insight",
        "content": content,
        "embedding": embedding,
        "quality": 0.95,
        "sensitivity": "internal"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
                json=payload,
                headers=headers
            )

            if response.status_code in [200, 201]:
                data = response.json()
                print(f"✅ Memory Stored Successfully")
                print(f"   Memory ID: {data.get('id', 'N/A')}")
                print(f"   Quality: {payload['quality']}")
                return True
            else:
                print(f"❌ Storage Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_memory_search():
    """Test 4: Search stored memories."""
    print(f"\n{'='*80}")
    print(f"Test 4: Searching Hyphal Memory")
    print(f"{'='*80}\n")

    headers = {
        "X-API-Key": API_KEY,
        "X-Tenant-ID": TENANT_ID
    }

    query = "QMN production validation for Aicube"
    query_embedding = generate_embedding(query)

    payload = {
        "embedding": query_embedding,
        "top_k": 5,
        "min_quality": 0.5
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{HYPHAL_MEMORY_URL}/v1/hyphal:search",
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"✅ Search Completed")
                print(f"   Query: '{query}'")
                print(f"   Results Found: {len(results)}")

                if results:
                    print(f"\n   Top Results:")
                    for idx, result in enumerate(results[:3], 1):
                        print(f"   {idx}. Quality: {result.get('quality', 0):.2f}, "
                              f"Similarity: {result.get('similarity', 0):.2f}")

                return True
            else:
                print(f"❌ Search Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def main():
    """Run all production tests."""
    print(f"\n{'='*80}")
    print(f"🏢 AICUBE TECHNOLOGY LLC - QMN PRODUCTION TEST")
    print(f"{'='*80}\n")
    print(f"Company: {COMPANY_NAME}")
    print(f"Tenant ID: {TENANT_ID}")
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Environment: Production (https://qmn.qube.aicube.ca)")

    results = {
        "tenant_verification": False,
        "nutrient_broadcast": False,
        "memory_storage": False,
        "memory_search": False
    }

    # Run tests
    results["tenant_verification"] = await test_tenant_info()
    await asyncio.sleep(1)

    results["nutrient_broadcast"] = await test_nutrient_broadcast()
    await asyncio.sleep(1)

    results["memory_storage"] = await test_memory_storage()
    await asyncio.sleep(1)

    results["memory_search"] = await test_memory_search()

    # Generate report
    print(f"\n{'='*80}")
    print(f"📊 TEST RESULTS SUMMARY")
    print(f"{'='*80}\n")

    passed = sum(results.values())
    total = len(results)
    success_rate = (passed / total) * 100

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")

    print(f"\nSuccess Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")

    if success_rate >= 80:
        print(f"\n🎉 RESULT: Production system operational for Aicube Technology LLC!")
    else:
        print(f"\n⚠️  RESULT: Some issues detected, please review failures.")

    print(f"\n{'='*80}\n")

    # Save results
    with open("aicube_test_results.json", "w") as f:
        json.dump({
            "company": COMPANY_NAME,
            "tenant_id": TENANT_ID,
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "success_rate": success_rate
        }, f, indent=2)

    print(f"📄 Results saved to: aicube_test_results.json\n")


if __name__ == "__main__":
    asyncio.run(main())
