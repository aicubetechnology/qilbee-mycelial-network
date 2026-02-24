"""
Unit tests for SDK retry strategy and circuit breaker.
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../sdk'))

from qilbee_mycelial_network.retry import RetryStrategy, CircuitBreakerState
import httpx


class TestRetryStrategy:
    """Test retry strategy with exponential backoff."""

    def test_init_defaults(self):
        """Default initialization."""
        strategy = RetryStrategy()
        assert strategy.max_retries == 3
        assert strategy.backoff_factor == 2.0
        assert strategy.max_delay == 60.0

    def test_calculate_delay(self):
        """Delay increases exponentially."""
        strategy = RetryStrategy(backoff_factor=2.0, max_delay=60.0)
        assert strategy._calculate_delay(0) == 1.0  # 2^0
        assert strategy._calculate_delay(1) == 2.0  # 2^1
        assert strategy._calculate_delay(2) == 4.0  # 2^2
        assert strategy._calculate_delay(3) == 8.0  # 2^3

    def test_calculate_delay_capped(self):
        """Delay is capped at max_delay."""
        strategy = RetryStrategy(backoff_factor=2.0, max_delay=10.0)
        assert strategy._calculate_delay(10) == 10.0  # Capped

    def test_should_retry_network_error(self):
        """Network errors should be retried."""
        strategy = RetryStrategy(max_retries=3)
        error = httpx.NetworkError("connection refused")
        assert strategy._should_retry(error, 0) is True
        assert strategy._should_retry(error, 2) is True

    def test_should_retry_timeout(self):
        """Timeout errors should be retried."""
        strategy = RetryStrategy(max_retries=3)
        error = httpx.ReadTimeout("read timeout")
        assert strategy._should_retry(error, 0) is True

    def test_should_retry_max_attempts(self):
        """Should not retry beyond max attempts."""
        strategy = RetryStrategy(max_retries=2)
        error = httpx.NetworkError("error")
        assert strategy._should_retry(error, 2) is False

    def test_should_not_retry_client_error(self):
        """Client errors (4xx except 429) should not be retried."""
        strategy = RetryStrategy(max_retries=3)
        response = httpx.Response(400, request=httpx.Request("GET", "http://test"))
        error = httpx.HTTPStatusError("bad request", request=response.request, response=response)
        assert strategy._should_retry(error, 0) is False

    def test_should_retry_rate_limit(self):
        """429 rate limit should be retried."""
        strategy = RetryStrategy(max_retries=3)
        response = httpx.Response(429, request=httpx.Request("GET", "http://test"))
        error = httpx.HTTPStatusError("rate limited", request=response.request, response=response)
        assert strategy._should_retry(error, 0) is True

    def test_should_retry_server_error(self):
        """5xx server errors should be retried."""
        strategy = RetryStrategy(max_retries=3)
        response = httpx.Response(503, request=httpx.Request("GET", "http://test"))
        error = httpx.HTTPStatusError("unavailable", request=response.request, response=response)
        assert strategy._should_retry(error, 0) is True

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Successful execution returns result."""
        strategy = RetryStrategy(max_retries=3)
        call_count = 0

        async def success():
            nonlocal call_count
            call_count += 1
            return "result"

        result = await strategy.execute(success)
        assert result == "result"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_execute_raises_after_retries(self):
        """Raises exception after exhausting retries."""
        strategy = RetryStrategy(max_retries=1)

        async def always_fail():
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            await strategy.execute(always_fail)


class TestCircuitBreakerState:
    """Test circuit breaker state."""

    def test_initial_state(self):
        """Initial state is closed (not open)."""
        state = CircuitBreakerState()
        assert state.failure_count == 0
        assert state.is_open is False

    def test_record_failures_opens_circuit(self):
        """Multiple failures open the circuit breaker."""
        strategy = RetryStrategy(circuit_breaker_threshold=3)

        for _ in range(3):
            strategy._record_failure()

        assert strategy._circuit_state.is_open is True

    def test_record_success_resets(self):
        """Success resets the circuit breaker."""
        strategy = RetryStrategy(circuit_breaker_threshold=2)
        strategy._record_failure()
        strategy._record_failure()
        assert strategy._circuit_state.is_open is True

        strategy._record_success()
        assert strategy._circuit_state.is_open is False
        assert strategy._circuit_state.failure_count == 0
