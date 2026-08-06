"""
Integration tests for Skills support in Hyphal Memory Service.

Tests validate that Skills (memories with kind='skill') work correctly
using the existing Hyphal Memory infrastructure.
"""
import pytest
import httpx
import uuid
from typing import List


BASE_URL = "http://localhost"
HYPHAL_MEMORY_URL = f"{BASE_URL}:8201"


@pytest.fixture
def tenant_id():
    """Generate a unique tenant ID for tests."""
    return f"test-tenant-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def api_key():
    """Generate a test API key."""
    return f"qmn_test_{uuid.uuid4().hex}"


@pytest.fixture
def test_embedding() -> List[float]:
    """Generate a test embedding vector."""
    return [0.1] * 1536


@pytest.mark.asyncio
async def test_store_skill_memory(tenant_id, api_key, test_embedding):
    """
    Test storing a memory with kind='skill'.
    
    Validates:
    - POST /v1/hyphal:store accepts kind='skill'
    - Returns 201 Created
    - Response includes all expected fields
    """
    async with httpx.AsyncClient() as client:
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        
        skill_payload = {
            "agent_id": agent_id,
            "kind": "skill",
            "content": {
                "name": "Python Code Analysis",
                "description": "Analyzes Python code for best practices",
                "schema": {
                    "input": {"type": "string", "description": "Python code to analyze"},
                    "output": {"type": "object", "description": "Analysis results"}
                }
            },
            "embedding": test_embedding,
            "quality": 0.8,
            "sensitivity": "internal",
            "metadata": {
                "version": "1.0",
                "author": "test"
            }
        }
        
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
        response = await client.post(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
            json=skill_payload,
            headers=headers
        )
        
        # Validate response
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "id" in data
        assert data["agent_id"] == agent_id
        assert data["kind"] == "skill"
        assert data["content"]["name"] == "Python Code Analysis"
        assert data["quality"] == 0.8
        assert data["sensitivity"] == "internal"
        assert "created_at" in data


@pytest.mark.asyncio
async def test_list_skills_by_agent(tenant_id, api_key, test_embedding):
    """
    Test listing skills for a specific agent.
    
    Validates:
    - GET /v1/hyphal/agent/{agent_id}?kind=skill works
    - Returns only memories with kind='skill'
    - Pagination with limit parameter works
    """
    async with httpx.AsyncClient() as client:
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        
        # Create 3 skills
        for i in range(3):
            skill_payload = {
                "agent_id": agent_id,
                "kind": "skill",
                "content": {
                    "name": f"Skill {i+1}",
                    "description": f"Test skill number {i+1}"
                },
                "embedding": test_embedding,
                "quality": 0.7
            }
            
            headers = {
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
                json=skill_payload,
                headers=headers
            )
            assert response.status_code == 201
        
        # List skills with kind filter
        headers = {"X-API-Key": api_key}
        response = await client.get(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal/agent/{agent_id}",
            params={"kind": "skill", "limit": 10},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate all returned items are skills
        assert isinstance(data, list)
        assert len(data) == 3
        for skill in data:
            assert skill["kind"] == "skill"
            assert skill["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_get_skill_by_id(tenant_id, api_key, test_embedding):
    """
    Test retrieving a specific skill by ID.
    
    Validates:
    - GET /v1/hyphal/{memory_id} returns skill correctly
    - All fields are preserved
    """
    async with httpx.AsyncClient() as client:
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        
        # Create a skill
        skill_payload = {
            "agent_id": agent_id,
            "kind": "skill",
            "content": {
                "name": "Data Validation",
                "description": "Validates data structures"
            },
            "embedding": test_embedding,
            "quality": 0.9,
            "sensitivity": "confidential"
        }
        
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
        # Store skill
        create_response = await client.post(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
            json=skill_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        skill_id = create_response.json()["id"]
        
        # Retrieve skill by ID
        get_response = await client.get(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal/{skill_id}",
            headers=headers
        )
        
        assert get_response.status_code == 200
        retrieved_skill = get_response.json()
        
        # Validate all fields preserved
        assert retrieved_skill["id"] == skill_id
        assert retrieved_skill["agent_id"] == agent_id
        assert retrieved_skill["kind"] == "skill"
        assert retrieved_skill["content"]["name"] == "Data Validation"
        assert retrieved_skill["quality"] == 0.9
        assert retrieved_skill["sensitivity"] == "confidential"


@pytest.mark.asyncio
async def test_delete_skill(tenant_id, api_key, test_embedding):
    """
    Test deleting a skill.
    
    Validates:
    - DELETE /v1/hyphal/{memory_id} removes skill
    - Returns 204 No Content
    - Subsequent GET returns 404
    """
    async with httpx.AsyncClient() as client:
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        
        # Create a skill
        skill_payload = {
            "agent_id": agent_id,
            "kind": "skill",
            "content": {"name": "Temporary Skill"},
            "embedding": test_embedding,
            "quality": 0.5
        }
        
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
        # Store skill
        create_response = await client.post(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
            json=skill_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        skill_id = create_response.json()["id"]
        
        # Delete skill
        delete_response = await client.delete(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal/{skill_id}",
            headers=headers
        )
        
        assert delete_response.status_code == 204
        
        # Verify skill is deleted
        get_response = await client.get(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal/{skill_id}",
            headers=headers
        )
        
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_search_skills(tenant_id, api_key, test_embedding):
    """
    Test semantic search for skills.
    
    Validates:
    - POST /v1/hyphal:search with kind_filter='skill' works
    - Returns only skills
    - Similarity scoring works
    """
    async with httpx.AsyncClient() as client:
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        
        # Create skills with different embeddings
        for i in range(2):
            embedding = [0.1 + (i * 0.1)] * 1536
            skill_payload = {
                "agent_id": agent_id,
                "kind": "skill",
                "content": {
                    "name": f"Search Test Skill {i+1}"
                },
                "embedding": embedding,
                "quality": 0.7
            }
            
            headers = {
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
                json=skill_payload,
                headers=headers
            )
            assert response.status_code == 201
        
        # Search for skills
        search_payload = {
            "embedding": test_embedding,
            "top_k": 10,
            "kind_filter": "skill",
            "min_quality": 0.5
        }
        
        headers = {"X-API-Key": api_key}
        response = await client.post(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal:search",
            json=search_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert isinstance(data["results"], list)
        
        # Validate all results are skills
        for result in data["results"]:
            assert result["kind"] == "skill"
            assert "similarity" in result


@pytest.mark.asyncio
async def test_skills_coexist_with_other_memories(tenant_id, api_key, test_embedding):
    """
    Test that skills coexist with other memory kinds.
    
    Validates:
    - Different memory kinds don't interfere
    - Filtering by kind works correctly
    - No regression in existing functionality
    """
    async with httpx.AsyncClient() as client:
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
        # Create different kinds of memories
        memory_kinds = ["skill", "insight", "snippet", "tool_hint"]
        
        for kind in memory_kinds:
            payload = {
                "agent_id": agent_id,
                "kind": kind,
                "content": {"name": f"Test {kind}"},
                "embedding": test_embedding,
                "quality": 0.7
            }
            
            response = await client.post(
                f"{HYPHAL_MEMORY_URL}/v1/hyphal:store",
                json=payload,
                headers=headers
            )
            assert response.status_code == 201
        
        # List all memories (no filter)
        response = await client.get(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal/agent/{agent_id}",
            params={"limit": 100},
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        all_memories = response.json()
        assert len(all_memories) == 4
        
        # List only skills
        response = await client.get(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal/agent/{agent_id}",
            params={"kind": "skill", "limit": 100},
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        skills_only = response.json()
        assert len(skills_only) == 1
        assert skills_only[0]["kind"] == "skill"
        
        # List only insights
        response = await client.get(
            f"{HYPHAL_MEMORY_URL}/v1/hyphal/agent/{agent_id}",
            params={"kind": "insight", "limit": 100},
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        insights_only = response.json()
        assert len(insights_only) == 1
        assert insights_only[0]["kind"] == "insight"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
