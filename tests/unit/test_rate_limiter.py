"""
Unit tests for rate limiter module.

Tests: RateLimiter with mocked Redis, RateLimitMiddleware.
"""

import pytest
import sys
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))

from shared.rate_limiter import RateLimiter, RateLimitMiddleware, DEFAULT_RATE_LIMIT


class TestRateLimiterInit:
    """Test rate limiter initialization."""

    def test_default_redis_url(self):
        """Uses default Redis URL."""
        limiter = RateLimiter()
        assert "redis" in limiter.redis_url
        assert limiter._redis is None

    def test_custom_redis_url(self):
        """Accepts custom Redis URL."""
        limiter = RateLimiter(redis_url="redis://custom:6380")
        assert limiter.redis_url == "redis://custom:6380"


class TestRateLimiterConnect:
    """Test rate limiter connection management."""

    @pytest.mark.asyncio
    async def test_connect(self):
        """Connect creates Redis client."""
        limiter = RateLimiter(redis_url="redis://localhost:6379")
        with patch('shared.rate_limiter.redis.from_url') as mock_from_url:
            mock_redis = MagicMock()
            mock_from_url.return_value = mock_redis
            await limiter.connect()
            assert limiter._redis is mock_redis

    @pytest.mark.asyncio
    async def test_connect_already_connected(self):
        """Connect skips if already connected."""
        limiter = RateLimiter()
        limiter._redis = MagicMock()
        existing = limiter._redis
        with patch('shared.rate_limiter.redis.from_url') as mock_from_url:
            await limiter.connect()
            mock_from_url.assert_not_called()
            assert limiter._redis is existing

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Disconnect closes Redis client."""
        limiter = RateLimiter()
        mock_redis = AsyncMock()
        limiter._redis = mock_redis
        await limiter.disconnect()
        mock_redis.aclose.assert_awaited_once()
        assert limiter._redis is None

    @pytest.mark.asyncio
    async def test_disconnect_no_client(self):
        """Disconnect does nothing without client."""
        limiter = RateLimiter()
        await limiter.disconnect()  # Should not raise


class TestRateLimiterCheck:
    """Test rate limit checking."""

    @pytest.mark.asyncio
    async def test_no_redis_allows_request(self):
        """Fails open: allows requests when Redis unavailable."""
        limiter = RateLimiter()
        allowed, remaining, retry_after = await limiter.check_rate_limit("tenant-1")
        assert allowed is True
        assert remaining == DEFAULT_RATE_LIMIT
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_within_limit(self):
        """Allows requests within rate limit."""
        limiter = RateLimiter()
        mock_pipe = AsyncMock()
        mock_pipe.execute = AsyncMock(return_value=[
            0,     # zremrangebyscore result
            5,     # zcard: 5 current requests
            True,  # zadd result
            True,  # expire result
        ])
        mock_redis = MagicMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        limiter._redis = mock_redis

        allowed, remaining, retry_after = await limiter.check_rate_limit("tenant-1", 1000)
        assert allowed is True
        assert remaining == 994  # 1000 - 5 - 1
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_exceeds_limit(self):
        """Denies requests exceeding rate limit."""
        limiter = RateLimiter()
        mock_pipe = AsyncMock()
        mock_pipe.execute = AsyncMock(return_value=[
            0,      # zremrangebyscore
            1000,   # zcard: at limit
            True,   # zadd
            True,   # expire
        ])
        mock_redis = MagicMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        limiter._redis = mock_redis

        allowed, remaining, retry_after = await limiter.check_rate_limit("tenant-1", 1000)
        assert allowed is False
        assert remaining == 0
        assert retry_after >= 1

    @pytest.mark.asyncio
    async def test_redis_error_fails_open(self):
        """Redis errors fail open (allow requests)."""
        limiter = RateLimiter()
        mock_pipe = AsyncMock()
        mock_pipe.execute = AsyncMock(side_effect=Exception("Redis connection error"))
        mock_redis = MagicMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        limiter._redis = mock_redis

        allowed, remaining, retry_after = await limiter.check_rate_limit("tenant-1")
        assert allowed is True
        assert remaining == DEFAULT_RATE_LIMIT


class TestRateLimitMiddleware:
    """Test FastAPI rate limit middleware."""

    @pytest.mark.asyncio
    async def test_skips_health_endpoint(self):
        """Skips rate limiting for /health."""
        mock_limiter = AsyncMock(spec=RateLimiter)
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, mock_limiter)

        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(mock_request, mock_call_next)
        mock_call_next.assert_awaited_once()
        mock_limiter.check_rate_limit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_metrics_endpoint(self):
        """Skips rate limiting for /metrics."""
        mock_limiter = AsyncMock(spec=RateLimiter)
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, mock_limiter)

        mock_request = MagicMock()
        mock_request.url.path = "/metrics"
        mock_call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(mock_request, mock_call_next)
        mock_call_next.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_tenant_passes_through(self):
        """Requests without tenant_id pass through."""
        mock_limiter = AsyncMock(spec=RateLimiter)
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, mock_limiter)

        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.state = MagicMock(spec=[])  # No tenant_id attribute

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, mock_call_next)
        mock_call_next.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rate_limited_returns_429(self):
        """Returns 429 when rate limited."""
        mock_limiter = AsyncMock(spec=RateLimiter)
        mock_limiter.check_rate_limit = AsyncMock(return_value=(False, 0, 30))
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, mock_limiter)

        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.state.tenant_id = "test-tenant"
        mock_request.state.rate_limit_per_minute = 100

        mock_call_next = AsyncMock()
        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 429
        mock_call_next.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_allowed_request_adds_headers(self):
        """Allowed requests get rate limit headers."""
        mock_limiter = AsyncMock(spec=RateLimiter)
        mock_limiter.check_rate_limit = AsyncMock(return_value=(True, 95, 0))
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, mock_limiter)

        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.state.tenant_id = "test-tenant"
        mock_request.state.rate_limit_per_minute = 100

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, mock_call_next)
        mock_call_next.assert_awaited_once()
        assert response.headers["X-RateLimit-Limit"] == "100"
