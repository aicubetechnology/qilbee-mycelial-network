"""
Integration tests for QMN services.
Run these tests with services deployed (docker-compose up).
"""
import asyncio
import pytest
import httpx
import uuid
from datetime import datetime


BASE_URL = "http://localhost"
IDENTITY_URL = f"{BASE_URL}:8100"
KEYS_URL = f"{BASE_URL}:8101"
ROUTER_URL = f"{BASE_URL}:8200"
HYPHAL_MEMORY_URL = f"{BASE_URL}:8201"
REINFORCEMENT_URL = f"{BASE_URL}:8202"


@pytest.fixture
def tenant_id():
    """Generate a unique tenant ID for tests."""
    return f"test-tenant-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def api_key():
    """Generate a test API key."""
    return f"qmn_test_{uuid.uuid4().hex}"


@pytest.mark.asyncio
async def test_identity_service_health():
    """Test Identity service health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{IDENTITY_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "identity"


@pytest.mark.asyncio
async def test_keys_service_health():
    """Test Keys service health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{KEYS_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "keys"


@pytest.mark.asyncio
async def test_router_service_health():
    """Test Router service health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ROUTER_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "router"


@pytest.mark.asyncio
async def test_hyphal_memory_service_health():
    """Test Hyphal Memory service health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{HYPHAL_MEMORY_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "hyphal-memory"


@pytest.mark.asyncio
async def test_reinforcement_service_health():
    """Test Reinforcement service health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REINFORCEMENT_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "reinforcement"


@pytest.mark.asyncio
async def test_create_tenant(tenant_id):
    """Test tenant creation via Identity service."""
    async with httpx.AsyncClient() as client:
        payload = {
            "tenant_id": tenant_id,
            "name": "Test Tenant",
            "contact_email": "test@example.com",
            "tier": "enterprise"
        }
        response = await client.post(f"{IDENTITY_URL}/v1/tenants", json=payload)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["tenant_id"] == tenant_id
        assert data["name"] == "Test Tenant"


@pytest.mark.asyncio
async def test_generate_api_key(tenant_id, api_key):
    """Test API key generation via Keys service."""
    # First create tenant
    async with httpx.AsyncClient() as client:
        tenant_payload = {
            "tenant_id": tenant_id,
            "name": "Test Tenant",
            "contact_email": "test@example.com"
        }
        await client.post(f"{IDENTITY_URL}/v1/tenants", json=tenant_payload)

        # Generate API key
        key_payload = {
            "tenant_id": tenant_id,
            "description": "Test API Key"
        }
        response = await client.post(f"{KEYS_URL}/v1/keys", json=key_payload)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("qmn_")
        assert data["tenant_id"] == tenant_id


@pytest.mark.asyncio
async def test_broadcast_nutrient(tenant_id, api_key):
    """Test nutrient broadcasting via Router service."""
    async with httpx.AsyncClient() as client:
        # Setup tenant
        tenant_payload = {
            "tenant_id": tenant_id,
            "name": "Test Tenant",
            "contact_email": "test@example.com"
        }
        await client.post(f"{IDENTITY_URL}/v1/tenants", json=tenant_payload)

        # Broadcast nutrient
        nutrient_payload = {
            "summary": "Test nutrient for integration testing",
            "embedding": [0.1] * 1536,  # 1536-dim vector
            "snippets": ["test snippet"],
            "tool_hints": ["test.tool"],
            "sensitivity": "internal",
            "ttl_sec": 180,
            "max_hops": 3
        }

        headers = {
            "X-API-Key": api_key,
            "X-Tenant-ID": tenant_id
        }

        response = await client.post(
            f"{ROUTER_URL}/v1/nutrients:broadcast",
            json=nutrient_payload,
            headers=headers
        )
        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert "nutrient_id" in data or "status" in data


@pytest.mark.asyncio
async def test_hyphal_memory_search(tenant_id, api_key):
    """Test vector search via Hyphal Memory service."""
    async with httpx.AsyncClient() as client:
        # Setup tenant
        tenant_payload = {
            "tenant_id": tenant_id,
            "name": "Test Tenant",
            "contact_email": "test@example.com"
        }
        await client.post(f"{IDENTITY_URL}/v1/tenants", json=tenant_payload)

        # Search memories
        search_payload = {
            "embedding": [0.1] * 1536,
            "top_k": 5,
            "kind_filter": ["insight", "snippet"]
        }

        headers = {
            "X-API-Key": api_key,
            "X-Tenant-ID": tenant_id
        }

        response = await client.post(
            f"{HYPHAL_MEMORY_URL}/v1/memories:search",
            json=search_payload,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_record_outcome(tenant_id, api_key):
    """Test outcome recording via Reinforcement service."""
    async with httpx.AsyncClient() as client:
        # Setup tenant
        tenant_payload = {
            "tenant_id": tenant_id,
            "name": "Test Tenant",
            "contact_email": "test@example.com"
        }
        await client.post(f"{IDENTITY_URL}/v1/tenants", json=tenant_payload)

        # Record outcome
        outcome_payload = {
            "interaction_id": str(uuid.uuid4()),
            "nutrient_id": str(uuid.uuid4()),
            "agent_id": "test-agent",
            "outcome": "success",
            "score": 0.85,
            "metadata": {
                "test": True
            }
        }

        headers = {
            "X-API-Key": api_key,
            "X-Tenant-ID": tenant_id
        }

        response = await client.post(
            f"{REINFORCEMENT_URL}/v1/outcomes",
            json=outcome_payload,
            headers=headers
        )
        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert "status" in data or "outcome_id" in data


@pytest.mark.asyncio
async def test_end_to_end_workflow(tenant_id):
    """Test complete workflow: broadcast → collect → record outcome."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Create tenant
        tenant_payload = {
            "tenant_id": tenant_id,
            "name": "E2E Test Tenant",
            "contact_email": "e2e@example.com"
        }
        response = await client.post(f"{IDENTITY_URL}/v1/tenants", json=tenant_payload)
        assert response.status_code in [200, 201]

        # 2. Generate API key
        key_payload = {
            "tenant_id": tenant_id,
            "description": "E2E Test Key"
        }
        response = await client.post(f"{KEYS_URL}/v1/keys", json=key_payload)
        assert response.status_code in [200, 201]
        test_api_key = response.json()["api_key"]

        headers = {
            "X-API-Key": test_api_key,
            "X-Tenant-ID": tenant_id
        }

        # 3. Broadcast nutrient
        nutrient_payload = {
            "summary": "E2E test: Need database optimization help",
            "embedding": [0.1 + i * 0.0001 for i in range(1536)],
            "snippets": ["SELECT * FROM large_table", "Performance issue"],
            "tool_hints": ["db.analyze", "db.optimize"],
            "sensitivity": "internal",
            "ttl_sec": 180,
            "max_hops": 3
        }

        response = await client.post(
            f"{ROUTER_URL}/v1/nutrients:broadcast",
            json=nutrient_payload,
            headers=headers
        )
        assert response.status_code in [200, 201, 202]
        broadcast_result = response.json()

        # 4. Search hyphal memory
        search_payload = {
            "embedding": nutrient_payload["embedding"],
            "top_k": 5
        }

        response = await client.post(
            f"{HYPHAL_MEMORY_URL}/v1/memories:search",
            json=search_payload,
            headers=headers
        )
        assert response.status_code == 200
        search_results = response.json()
        assert "results" in search_results

        # 5. Record outcome
        outcome_payload = {
            "interaction_id": str(uuid.uuid4()),
            "nutrient_id": broadcast_result.get("nutrient_id", str(uuid.uuid4())),
            "agent_id": "e2e-test-agent",
            "outcome": "success",
            "score": 0.92,
            "metadata": {
                "test": "e2e",
                "workflow": "complete"
            }
        }

        response = await client.post(
            f"{REINFORCEMENT_URL}/v1/outcomes",
            json=outcome_payload,
            headers=headers
        )
        assert response.status_code in [200, 201, 202]

        print("✅ End-to-end workflow completed successfully!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
