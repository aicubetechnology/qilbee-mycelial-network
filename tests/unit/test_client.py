"""
Unit tests for SDK MycelialClient.

Tests: initialization, HTTP methods, control plane, mocked API calls.
"""

import pytest
import sys
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../sdk'))

import httpx
from qilbee_mycelial_network.client import MycelialClient
from qilbee_mycelial_network.settings import QMNSettings
from qilbee_mycelial_network.models import Nutrient, Outcome, Context, Sensitivity


def make_settings(**overrides):
    """Create test settings."""
    defaults = {
        "api_key": "qmn_test_key_abc123def456ghi789jkl012mno",
        "api_base_url": "https://test.example.com",
        "tenant_id": "test-tenant",
    }
    defaults.update(overrides)
    return QMNSettings(**defaults)


def make_mock_response(status_code=200, json_data=None):
    """Create a mock httpx Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.raise_for_status = MagicMock()
    return response


class TestClientInit:
    """Test client initialization."""

    def test_init_with_settings(self):
        """Client initializes with settings."""
        settings = make_settings()
        client = MycelialClient(settings)
        assert client.settings == settings
        assert client._owned_client is True

    def test_init_with_custom_http_client(self):
        """Client accepts custom HTTP client."""
        settings = make_settings()
        mock_http = MagicMock()
        client = MycelialClient(settings, http_client=mock_http)
        assert client._http_client is mock_http
        assert client._owned_client is False

    @pytest.mark.asyncio
    async def test_create_from_env(self):
        """Create client from environment variables."""
        with patch.dict(os.environ, {
            "QMN_API_KEY": "qmn_test_key_abc123def456ghi789jkl012mno",
            "QMN_TENANT_ID": "env-tenant",
        }):
            client = await MycelialClient.create_from_env()
            assert client.settings.api_key == "qmn_test_key_abc123def456ghi789jkl012mno"

    @pytest.mark.asyncio
    async def test_create_with_settings(self):
        """Create client with explicit settings."""
        settings = make_settings()
        client = await MycelialClient.create(settings)
        assert client.settings is settings

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Client works as async context manager."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        client = MycelialClient(settings, http_client=mock_http)
        async with client as c:
            assert c is client

    @pytest.mark.asyncio
    async def test_close_owned_client(self):
        """Close disposes owned HTTP client."""
        settings = make_settings()
        client = MycelialClient(settings)
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        client._http_client = mock_http
        client._owned_client = True
        await client.close()
        mock_http.aclose.assert_awaited_once()
        assert client._http_client is None

    @pytest.mark.asyncio
    async def test_close_non_owned_client(self):
        """Close does not dispose non-owned HTTP client."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        client = MycelialClient(settings, http_client=mock_http)
        await client.close()
        mock_http.aclose.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ensure_client_creates_http_client(self):
        """_ensure_client creates httpx.AsyncClient if none exists."""
        settings = make_settings()
        client = MycelialClient(settings)
        assert client._http_client is None
        with patch('httpx.AsyncClient') as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value = mock_instance
            await client._ensure_client()
            assert client._http_client is mock_instance


class TestClientRequest:
    """Test _request method."""

    @pytest.mark.asyncio
    async def test_request_adds_auth_headers(self):
        """Request includes authentication headers."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"ok": True})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        response = await client._request("GET", "/test")

        call_kwargs = mock_http.request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert "X-API-Key" in headers

    @pytest.mark.asyncio
    async def test_request_with_retry(self):
        """Request uses retry when auto_retry is enabled."""
        settings = make_settings(auto_retry=True)
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"ok": True})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        response = await client._request("GET", "/test")
        assert response.json() == {"ok": True}

    @pytest.mark.asyncio
    async def test_request_without_retry(self):
        """Request skips retry when auto_retry is disabled."""
        settings = make_settings(auto_retry=False)
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"direct": True})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        response = await client._request("GET", "/test")
        assert response.json() == {"direct": True}


class TestClientBroadcast:
    """Test broadcast method."""

    @pytest.mark.asyncio
    async def test_broadcast_nutrient(self):
        """Broadcast sends nutrient and returns response."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"trace_id": "tr-123", "routed_to": 3})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        nutrient = Nutrient.seed(
            summary="test nutrient",
            embedding=[0.1] * 1536,
        )
        result = await client.broadcast(nutrient)
        assert result["trace_id"] == "tr-123"


class TestClientCollect:
    """Test collect method."""

    @pytest.mark.asyncio
    async def test_collect_contexts(self):
        """Collect returns Context object."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={
            "trace_id": "tr-456",
            "contents": [{"data": "result"}],
            "source_agents": ["agent-1"],
            "quality_scores": [0.9],
            "metadata": {},
        })
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        ctx = await client.collect(
            demand_embedding=[0.1] * 1536,
            window_ms=300,
            top_k=5,
        )
        assert isinstance(ctx, Context)
        assert ctx.trace_id == "tr-456"

    @pytest.mark.asyncio
    async def test_collect_with_trace_task_id(self):
        """Collect passes trace_task_id in payload."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={
            "trace_id": "tr-789",
            "contents": [],
            "source_agents": [],
            "quality_scores": [],
            "metadata": {},
        })
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        await client.collect(
            demand_embedding=[0.1] * 1536,
            trace_task_id="task-abc",
        )
        call_kwargs = mock_http.request.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["trace_task_id"] == "task-abc"

    @pytest.mark.asyncio
    async def test_collect_wrong_embedding_raises(self):
        """Collect rejects wrong embedding dimension."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        client = MycelialClient(settings, http_client=mock_http)
        with pytest.raises(ValueError, match="1536"):
            await client.collect(demand_embedding=[0.1] * 100)


class TestClientHyphalMemory:
    """Test hyphal memory methods."""

    @pytest.mark.asyncio
    async def test_hyphal_store(self):
        """Store in hyphal memory."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"id": "mem-123"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.hyphal_store(
            agent_id="agent-1",
            kind="insight",
            content={"knowledge": "test"},
            embedding=[0.1] * 1536,
        )
        assert result["id"] == "mem-123"

    @pytest.mark.asyncio
    async def test_hyphal_store_wrong_embedding(self):
        """Store rejects wrong embedding dimension."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        client = MycelialClient(settings, http_client=mock_http)
        with pytest.raises(ValueError, match="1536"):
            await client.hyphal_store(
                agent_id="agent-1",
                kind="insight",
                content={},
                embedding=[0.1] * 100,
            )

    @pytest.mark.asyncio
    async def test_hyphal_search(self):
        """Search hyphal memory returns results."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={
            "results": [
                {"id": "mem-1", "similarity": 0.95, "content": {"data": "test"},
                 "kind": "insight", "agent_id": "a1", "quality": 0.9,
                 "created_at": "2026-01-01T00:00:00"}
            ]
        })
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        results = await client.hyphal_search(embedding=[0.1] * 1536, top_k=5)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_hyphal_search_wrong_embedding(self):
        """Search rejects wrong embedding dimension."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        client = MycelialClient(settings, http_client=mock_http)
        with pytest.raises(ValueError, match="1536"):
            await client.hyphal_search(embedding=[0.1] * 100)


class TestClientOutcomes:
    """Test outcome recording."""

    @pytest.mark.asyncio
    async def test_record_outcome(self):
        """Record outcome sends score."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"status": "recorded"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.record_outcome(
            trace_id="tr-123",
            outcome=Outcome.with_score(0.85),
        )
        assert result["status"] == "recorded"

    @pytest.mark.asyncio
    async def test_record_outcome_with_hop_scores(self):
        """Record outcome passes hop_outcomes."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"status": "recorded"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        outcome = Outcome.with_hop_scores(
            score=0.8,
            hop_outcomes={"agent-1": 0.9, "agent-2": 0.6},
        )
        await client.record_outcome(trace_id="tr-456", outcome=outcome)

        call_kwargs = mock_http.request.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "hop_outcomes" in payload


class TestClientUsageAndHealth:
    """Test usage and health methods."""

    @pytest.mark.asyncio
    async def test_get_usage(self):
        """Get usage returns metrics."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={
            "nutrients_sent": 100,
            "quota_remaining": 900,
        })
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        usage = await client.get_usage()
        assert usage["nutrients_sent"] == 100

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Health check returns status."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"status": "healthy"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.health(service="router")
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_rotate_key(self):
        """Key rotation returns new key."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"new_api_key": "qmn_new_key"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.rotate_key(grace_period_sec=3600)
        assert result["new_api_key"] == "qmn_new_key"


class TestClientAgentManagement:
    """Test agent management methods."""

    @pytest.mark.asyncio
    async def test_register_agent(self):
        """Register agent sends profile."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"agent_id": "agent-1", "created": True})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.register_agent(
            agent_id="agent-1",
            profile_embedding=[0.1] * 1536,
            capabilities=["code_review"],
            tools=["git.diff"],
            name="Test Agent",
            skills=["python"],
            description="Test",
            region="us-east-1",
            metadata={"version": "1.0"},
        )
        assert result["agent_id"] == "agent-1"

    @pytest.mark.asyncio
    async def test_register_agent_wrong_embedding(self):
        """Register rejects wrong embedding dimension."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        client = MycelialClient(settings, http_client=mock_http)
        with pytest.raises(ValueError, match="1536"):
            await client.register_agent(
                agent_id="agent-1",
                profile_embedding=[0.1] * 100,
            )

    @pytest.mark.asyncio
    async def test_get_agent(self):
        """Get agent profile."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"agent_id": "agent-1", "name": "Test"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.get_agent("agent-1")
        assert result["agent_id"] == "agent-1"

    @pytest.mark.asyncio
    async def test_list_agents(self):
        """List agents with filters."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data=[{"agent_id": "a1"}, {"agent_id": "a2"}])
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.list_agents(status_filter="active", capability="review")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_deactivate_agent(self):
        """Deactivate agent."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response()
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        await client.deactivate_agent("agent-1")
        mock_http.request.assert_awaited_once()


class TestClientTenantManagement:
    """Test tenant management methods."""

    @pytest.mark.asyncio
    async def test_create_tenant(self):
        """Create tenant."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"id": "new-tenant"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.create_tenant(
            tenant_id="new-tenant",
            name="New Tenant",
            plan_tier="pro",
            kms_key_id="kms-123",
            region_preference="us-east-1",
            metadata={"org": "test"},
        )
        assert result["id"] == "new-tenant"

    @pytest.mark.asyncio
    async def test_get_tenant(self):
        """Get tenant by ID."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"id": "t1", "name": "Tenant 1"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.get_tenant("t1")
        assert result["name"] == "Tenant 1"

    @pytest.mark.asyncio
    async def test_list_tenants(self):
        """List tenants with filters."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data=[{"id": "t1"}, {"id": "t2"}])
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.list_tenants(status_filter="active", plan_tier="pro")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_tenant(self):
        """Update tenant fields."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"id": "t1", "name": "Updated"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.update_tenant(
            tenant_id="t1",
            name="Updated",
            plan_tier="enterprise",
            status="active",
            metadata={"updated": True},
        )
        assert result["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_delete_tenant(self):
        """Delete tenant."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response()
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        await client.delete_tenant("t1")
        mock_http.request.assert_awaited_once()


class TestClientKeyManagement:
    """Test API key management methods."""

    @pytest.mark.asyncio
    async def test_create_key(self):
        """Create API key."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"key": "qmn_new", "id": "k1"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.create_key(
            name="test-key",
            scopes=["*"],
            rate_limit_per_minute=500,
            expires_in_days=30,
        )
        assert result["id"] == "k1"

    @pytest.mark.asyncio
    async def test_validate_key(self):
        """Validate API key."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"valid": True, "tenant_id": "t1"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.validate_key("qmn_test_key")
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_list_keys(self):
        """List API keys."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data=[{"id": "k1"}, {"id": "k2"}])
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.list_keys()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_revoke_key(self):
        """Revoke API key."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"status": "revoked"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.revoke_key("k1")
        assert result["status"] == "revoked"


class TestClientPolicyManagement:
    """Test policy management methods."""

    @pytest.mark.asyncio
    async def test_evaluate_policy(self):
        """Evaluate policy."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"allowed": True})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.evaluate_policy(
            policy_type="rbac",
            context={"role": "admin", "action": "read"},
        )
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_create_policy(self):
        """Create policy."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data={"id": "p1", "name": "test-policy"})
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.create_policy(
            name="test-policy",
            policy_type="rbac",
            rules={"allow": ["read"]},
            description="Test policy",
        )
        assert result["name"] == "test-policy"

    @pytest.mark.asyncio
    async def test_list_policies(self):
        """List policies."""
        settings = make_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_response = make_mock_response(json_data=[{"id": "p1"}])
        mock_http.request = AsyncMock(return_value=mock_response)

        client = MycelialClient(settings, http_client=mock_http)
        result = await client.list_policies(policy_type="rbac")
        assert len(result) == 1
