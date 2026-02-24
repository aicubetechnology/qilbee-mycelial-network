"""
Redis-based rate limiting middleware for QMN services.

Implements sliding window rate limiting using Redis sorted sets.
"""

import os
import time
import logging
from typing import Optional

import redis.asyncio as redis
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Default rate limit if not specified per-key
DEFAULT_RATE_LIMIT = 1000  # requests per minute


class RateLimiter:
    """
    Redis-based sliding window rate limiter.

    Uses sorted sets keyed by tenant_id with timestamps as scores
    to implement a sliding window counter.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL (default from REDIS_URL env)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis: Optional[redis.Redis] = None

    async def connect(self):
        """Establish Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            logger.info("Rate limiter Redis connected")

    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def check_rate_limit(
        self,
        tenant_id: str,
        limit_per_minute: int = DEFAULT_RATE_LIMIT,
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Uses Redis sorted set sliding window: removes entries older than
        60 seconds, then counts remaining entries.

        Args:
            tenant_id: Tenant identifier
            limit_per_minute: Maximum requests per minute

        Returns:
            Tuple of (allowed, remaining, retry_after_seconds)
        """
        if self._redis is None:
            # If Redis is unavailable, allow the request (fail open)
            return True, limit_per_minute, 0

        now = time.time()
        window_start = now - 60.0
        key = f"rate:{tenant_id}:{int(now // 60)}"

        try:
            pipe = self._redis.pipeline()
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            # Count current entries
            pipe.zcard(key)
            # Add current request
            pipe.zadd(key, {f"{now}:{id(pipe)}": now})
            # Set expiry on the key
            pipe.expire(key, 120)  # 2 min TTL for cleanup
            results = await pipe.execute()

            current_count = results[1]

            if current_count >= limit_per_minute:
                retry_after = int(60 - (now - window_start))
                return False, 0, max(retry_after, 1)

            remaining = limit_per_minute - current_count - 1
            return True, max(remaining, 0), 0

        except Exception as e:
            logger.warning(f"Rate limiter error (failing open): {e}")
            return True, limit_per_minute, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Extracts tenant_id from request state (set by auth middleware)
    and enforces rate limits using Redis sliding window.
    """

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing request."""
        # Skip health checks and metrics
        if request.url.path in ("/health", "/metrics"):
            return await call_next(request)

        # Get tenant_id from request state (set by auth dependency)
        tenant_id = getattr(request.state, "tenant_id", None)

        if tenant_id:
            # Get per-key rate limit (stored during auth validation)
            limit = getattr(request.state, "rate_limit_per_minute", DEFAULT_RATE_LIMIT)

            allowed, remaining, retry_after = await self.rate_limiter.check_rate_limit(
                tenant_id, limit
            )

            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": retry_after,
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )

        response = await call_next(request)

        # Add rate limit headers
        if tenant_id:
            limit = getattr(request.state, "rate_limit_per_minute", DEFAULT_RATE_LIMIT)
            response.headers["X-RateLimit-Limit"] = str(limit)

        return response
