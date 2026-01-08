"""
Main Mycelial Client for QMN SDK.

Provides the primary interface for broadcasting nutrients, collecting contexts,
searching hyphal memory, and recording outcomes.
"""

import asyncio
import httpx
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from .models import Nutrient, Context, Outcome, SearchRequest, SearchResult
from .settings import QMNSettings
from .retry import RetryStrategy
from .auth import AuthHandler


class MycelialClient:
    """
    Main client for interacting with Qilbee Mycelial Network.

    This client handles all communication with the QMN platform, including:
    - Broadcasting nutrients to the network
    - Collecting enriched contexts
    - Searching hyphal memory
    - Recording task outcomes for reinforcement learning

    Example:
        ```python
        async with MycelialClient.create_from_env() as client:
            # Broadcast nutrient
            await client.broadcast(
                Nutrient.seed(
                    summary="Need database optimization advice",
                    embedding=[...],  # 1536-dim vector
                    tool_hints=["db.analyze", "perf.profile"]
                )
            )

            # Collect contexts
            contexts = await client.collect(
                demand_embedding=[...],
                window_ms=300,
                top_k=5
            )

            # Record outcome
            await client.record_outcome(
                trace_id=contexts.trace_id,
                outcome=Outcome.success()
            )
        ```
    """

    def __init__(
        self,
        settings: QMNSettings,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize Mycelial Client.

        Args:
            settings: Configuration settings
            http_client: Optional custom HTTP client
        """
        self.settings = settings
        self.settings.validate()

        self._http_client = http_client
        self._owned_client = http_client is None

        self._auth = AuthHandler(settings.api_key, settings.tenant_id)
        self._retry = RetryStrategy(
            max_retries=settings.max_retries,
            backoff_factor=settings.retry_backoff_factor,
            max_delay=settings.retry_max_delay,
        )

    @classmethod
    async def create_from_env(cls) -> "MycelialClient":
        """
        Create client from environment variables.

        Requires QMN_API_KEY to be set.

        Returns:
            Initialized MycelialClient

        Raises:
            ValueError: If QMN_API_KEY is not set
        """
        settings = QMNSettings.from_env()
        return cls(settings)

    @classmethod
    async def create(cls, settings: QMNSettings) -> "MycelialClient":
        """
        Create client with explicit settings.

        Args:
            settings: Configuration settings

        Returns:
            Initialized MycelialClient
        """
        return cls(settings)

    async def __aenter__(self) -> "MycelialClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.settings.api_url,
                timeout=httpx.Timeout(
                    connect=self.settings.connect_timeout,
                    read=self.settings.read_timeout,
                    write=self.settings.read_timeout,
                    pool=self.settings.connect_timeout,
                ),
                verify=self.settings.verify_ssl,
            )

    async def close(self):
        """Close HTTP client if owned by this instance."""
        if self._owned_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> httpx.Response:
        """
        Make authenticated HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: On request failure
        """
        await self._ensure_client()

        headers = kwargs.pop("headers", {})
        headers.update(self._auth.get_headers())

        async def _make_request():
            response = await self._http_client.request(
                method=method,
                url=endpoint,
                headers=headers,
                **kwargs,
            )
            response.raise_for_status()
            return response

        if self.settings.auto_retry:
            return await self._retry.execute(_make_request)
        else:
            return await _make_request()

    async def broadcast(
        self,
        nutrient: Nutrient,
    ) -> Dict[str, Any]:
        """
        Broadcast a nutrient to the mycelial network.

        The nutrient will be routed to relevant agents based on embedding similarity,
        agent capabilities, and learned edge weights.

        Args:
            nutrient: Nutrient to broadcast

        Returns:
            Response containing trace_id and routing metadata

        Raises:
            httpx.HTTPError: On API error

        Example:
            ```python
            response = await client.broadcast(
                Nutrient.seed(
                    summary="Need code review for authentication module",
                    embedding=embedding_vector,
                    snippets=["auth.py code..."],
                    tool_hints=["code_review.run", "security.scan"],
                    sensitivity=Sensitivity.INTERNAL,
                )
            )
            print(f"Broadcasted with trace: {response['trace_id']}")
            ```
        """
        response = await self._request(
            "POST",
            "/router/v1/nutrients:broadcast",
            json=nutrient.to_dict(),
        )
        return response.json()

    async def collect(
        self,
        demand_embedding: List[float],
        window_ms: int = 300,
        top_k: int = 5,
        diversify: bool = True,
        trace_task_id: Optional[str] = None,
    ) -> Context:
        """
        Collect enriched contexts from the network.

        Gathers responses from agents that received relevant nutrients and can
        provide useful context for the current demand.

        Args:
            demand_embedding: Embedding vector representing current need (1536-dim)
            window_ms: Time window to wait for responses (milliseconds)
            top_k: Maximum number of contexts to collect
            diversify: Apply MMR diversity to results
            trace_task_id: Optional task ID for tracing

        Returns:
            Context object with aggregated responses

        Raises:
            httpx.HTTPError: On API error

        Example:
            ```python
            contexts = await client.collect(
                demand_embedding=task_embedding,
                window_ms=500,
                top_k=10,
                diversify=True
            )

            for content in contexts.contents:
                print(f"Source: {content['agent_id']}")
                print(f"Content: {content['data']}")
            ```
        """
        if len(demand_embedding) != 1536:
            raise ValueError(f"Embedding must be 1536-dimensional, got {len(demand_embedding)}")

        payload = {
            "demand_embedding": demand_embedding,
            "window_ms": window_ms,
            "top_k": top_k,
            "diversify": diversify,
        }
        if trace_task_id:
            payload["trace_task_id"] = trace_task_id

        response = await self._request(
            "POST",
            "/router/v1/contexts:collect",
            json=payload,
        )
        return Context.from_dict(response.json())

    async def hyphal_store(
        self,
        agent_id: str,
        kind: str,
        content: Dict[str, Any],
        embedding: List[float],
        quality: float = 0.8,
        sensitivity: str = "internal",
    ) -> Dict[str, Any]:
        """
        Store knowledge in hyphal memory.

        Args:
            agent_id: Agent identifier
            kind: Memory kind (insight, snippet, tool_hint, plan, outcome)
            content: Memory content dictionary
            embedding: Memory embedding vector (1536-dim)
            quality: Memory quality score (0.0-1.0)
            sensitivity: Data sensitivity level

        Returns:
            Response with memory ID

        Example:
            ```python
            result = await client.hyphal_store(
                agent_id="agent-001",
                kind="insight",
                content={"knowledge": "Best practice for ..."},
                embedding=embedding_vector,
                quality=0.95
            )
            ```
        """
        if len(embedding) != 1536:
            raise ValueError(f"Embedding must be 1536-dimensional, got {len(embedding)}")

        payload = {
            "agent_id": agent_id,
            "kind": kind,
            "content": content,
            "embedding": embedding,
            "quality": quality,
            "sensitivity": sensitivity,
        }

        response = await self._request(
            "POST",
            "/memory/v1/hyphal:store",
            json=payload,
        )
        return response.json()

    async def hyphal_search(
        self,
        embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search hyphal memory using vector similarity.

        Queries the distributed memory store for relevant past experiences,
        insights, and knowledge based on semantic similarity.

        Args:
            embedding: Query embedding vector (1536-dim)
            top_k: Number of results to return
            filters: Optional filters (e.g., {"kind": "insight", "agent_id": "..."})

        Returns:
            List of search results with similarity scores

        Raises:
            httpx.HTTPError: On API error

        Example:
            ```python
            results = await client.hyphal_search(
                embedding=query_vector,
                top_k=15,
                filters={"kind": "tool_hint", "quality": {"$gt": 0.8}}
            )

            for result in results:
                print(f"Similarity: {result.similarity:.3f}")
                print(f"Content: {result.content}")
            ```
        """
        if len(embedding) != 1536:
            raise ValueError(f"Embedding must be 1536-dimensional, got {len(embedding)}")

        request = SearchRequest(
            embedding=embedding,
            top_k=top_k,
            filters=filters,
        )

        response = await self._request(
            "POST",
            "/memory/v1/hyphal:search",
            json=request.to_dict(),
        )
        data = response.json()
        return [SearchResult.from_dict(item) for item in data["results"]]

    async def record_outcome(
        self,
        trace_id: str,
        outcome: Outcome,
    ) -> Dict[str, Any]:
        """
        Record task outcome for reinforcement learning.

        Reports whether a collected context successfully helped complete a task.
        This updates edge weights between agents to improve future routing.

        Args:
            trace_id: Trace ID from broadcast/collect operation
            outcome: Outcome with score (0.0=failure to 1.0=success)

        Returns:
            Response confirming outcome recorded

        Raises:
            httpx.HTTPError: On API error

        Example:
            ```python
            # After using collected context to complete task
            await client.record_outcome(
                trace_id=contexts.trace_id,
                outcome=Outcome.with_score(0.85)  # 85% success
            )
            ```
        """
        payload = {
            "trace_id": trace_id,
            "outcome": outcome.to_dict(),
        }

        response = await self._request(
            "POST",
            "/reinforcement/v1/outcomes:record",
            json=payload,
        )
        return response.json()

    async def get_usage(self) -> Dict[str, Any]:
        """
        Get current usage metrics and quota status.

        Note: This endpoint is not yet available in production.

        Returns:
            Usage data including quota limits and consumption

        Raises:
            NotImplementedError: This feature is not yet available

        Example:
            ```python
            usage = await client.get_usage()
            print(f"Nutrients sent: {usage['nutrients_sent']}")
            print(f"Quota remaining: {usage['quota_remaining']}")
            ```
        """
        raise NotImplementedError(
            "Usage endpoint is not yet available. "
            "This feature will be added in a future release."
        )

    async def rotate_key(self, grace_period_sec: int = 3600) -> Dict[str, Any]:
        """
        Rotate API key with grace period.

        Args:
            grace_period_sec: Grace period before old key expires (seconds)

        Returns:
            New API key and metadata

        Example:
            ```python
            result = await client.rotate_key(grace_period_sec=7200)  # 2 hours
            new_key = result['new_api_key']
            # Update QMN_API_KEY environment variable
            ```
        """
        response = await self._request(
            "POST",
            "/keys/v1/keys:rotate",
            json={"grace_period_sec": grace_period_sec},
        )
        return response.json()

    async def health(self, service: str = "router") -> Dict[str, Any]:
        """
        Check service health.

        Args:
            service: Service to check (router, memory, identity, keys)

        Returns:
            Health status and metadata

        Example:
            ```python
            health = await client.health()
            print(f"Status: {health['status']}")
            print(f"Region: {health['region']}")
            ```
        """
        response = await self._request("GET", f"/{service}/health")
        return response.json()

    async def register_agent(
        self,
        agent_id: str,
        profile_embedding: List[float],
        capabilities: Optional[List[str]] = None,
        tools: Optional[List[str]] = None,
        name: Optional[str] = None,
        skills: Optional[List[str]] = None,
        description: Optional[str] = None,
        region: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Register or update an agent in the mycelial network.

        Registers the agent with its profile embedding, capabilities, and metadata.
        This enables the agent to participate in routing and reinforcement learning.
        If the agent already exists, it will be updated (preserving metrics/neighbors).

        Args:
            agent_id: Unique agent identifier
            profile_embedding: Agent profile embedding vector (1536-dim)
            capabilities: List of agent capabilities (e.g., ["code_review", "testing"])
            tools: List of available tools (e.g., ["git.analyze", "test.run"])
            name: Human-readable agent name
            skills: Agent skill keywords
            description: Agent description
            region: Deployment region
            metadata: Additional agent metadata

        Returns:
            Agent registration response with created/updated timestamps

        Raises:
            httpx.HTTPError: On API error
            ValueError: If embedding is not 1536-dimensional

        Example:
            ```python
            await client.register_agent(
                agent_id="code-reviewer-01",
                profile_embedding=get_embedding("code review security best practices"),
                capabilities=["code_review", "security_audit"],
                tools=["git.diff", "security.scan"],
                name="Code Reviewer Agent",
                skills=["python", "security", "code-quality"],
                description="Reviews code for security and best practices"
            )
            ```
        """
        if len(profile_embedding) != 1536:
            raise ValueError(f"Embedding must be 1536-dimensional, got {len(profile_embedding)}")

        payload = {
            "agent_id": agent_id,
            "name": name,
            "capabilities": capabilities or [],
            "tools": tools or [],
            "profile": {
                "embedding": profile_embedding,
                "skills": skills or [],
                "description": description,
            },
            "region": region,
            "metadata": metadata or {},
        }

        response = await self._request(
            "POST",
            "/router/v1/agents:register",
            json=payload,
        )
        return response.json()

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent profile by ID.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent profile and metadata

        Raises:
            httpx.HTTPError: On API error (404 if not found)

        Example:
            ```python
            agent = await client.get_agent("code-reviewer-01")
            print(f"Agent: {agent['name']}")
            print(f"Capabilities: {agent['capabilities']}")
            ```
        """
        response = await self._request("GET", f"/router/v1/agents/{agent_id}")
        return response.json()

    async def list_agents(
        self,
        status_filter: Optional[str] = None,
        capability: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List agents for the current tenant.

        Args:
            status_filter: Filter by status (active, idle, suspended)
            capability: Filter by capability
            limit: Maximum number of results

        Returns:
            List of agent profiles

        Example:
            ```python
            agents = await client.list_agents(status_filter="active")
            for agent in agents:
                print(f"{agent['agent_id']}: {agent['capabilities']}")
            ```
        """
        params = {"limit": limit}
        if status_filter:
            params["status_filter"] = status_filter
        if capability:
            params["capability"] = capability

        response = await self._request("GET", "/router/v1/agents", params=params)
        return response.json()

    async def deactivate_agent(self, agent_id: str) -> None:
        """
        Deactivate an agent (soft delete).

        Sets agent status to 'suspended'. Does not delete data.

        Args:
            agent_id: Agent identifier

        Raises:
            httpx.HTTPError: On API error (404 if not found)

        Example:
            ```python
            await client.deactivate_agent("old-agent-01")
            ```
        """
        await self._request("DELETE", f"/router/v1/agents/{agent_id}")
